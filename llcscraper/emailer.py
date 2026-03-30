import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from html import escape as html_escape
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from database import (
    get_setting, set_setting, add_log, get_approved_for_email,
    update_llc_outreach_status, log_email_sent, get_emails_sent_today
)

# Try to import keyring; fall back to env vars in Docker/headless environments
try:
    import keyring
    # Test if a usable backend is available
    keyring.get_password("llcscraper", "__test__")
    _USE_KEYRING = True
except Exception:
    _USE_KEYRING = False

SMTP_PROVIDERS = {
    'gmail': {
        'label': 'Gmail',
        'server': 'smtp.gmail.com',
        'port': 587,
        'security': 'starttls',
        'help': 'Use an App Password from myaccount.google.com > Security > App Passwords'
    },
    'outlook': {
        'label': 'Outlook / Hotmail',
        'server': 'smtp.office365.com',
        'port': 587,
        'security': 'starttls',
        'help': 'Use your Microsoft account password or app password'
    },
    'yahoo': {
        'label': 'Yahoo Mail',
        'server': 'smtp.mail.yahoo.com',
        'port': 587,
        'security': 'starttls',
        'help': 'Generate an app password at login.yahoo.com > Account Security'
    },
    'protonmail': {
        'label': 'Proton Mail (Bridge)',
        'server': '127.0.0.1',
        'port': 1025,
        'security': 'starttls',
        'help': 'Requires Proton Mail Bridge running on localhost:1025'
    },
    'sendgrid': {
        'label': 'SendGrid',
        'server': 'smtp.sendgrid.net',
        'port': 587,
        'security': 'starttls',
        'help': 'Use "apikey" as username and your SendGrid API key as password'
    },
    'custom': {
        'label': 'Custom SMTP',
        'server': '',
        'port': 587,
        'security': 'starttls',
        'help': 'Enter your SMTP server details manually'
    }
}

# Jinja2 template environment
_template_dir = Path(__file__).parent / 'templates'
_jinja_env = Environment(
    loader=FileSystemLoader(str(_template_dir)),
    autoescape=select_autoescape(['html'])
)


def get_smtp_credentials():
    """Retrieve SMTP credentials securely.

    Uses OS keyring when available (local dev), falls back to env var
    SMTP_PASSWORD or database storage in Docker/headless environments.
    """
    email = get_setting('smtp_email')

    # Try keyring first (local dev with OS keyring)
    password = None
    if _USE_KEYRING:
        password = keyring.get_password("llcscraper", "smtp_password")

    # Fall back to environment variable (Docker)
    if not password:
        password = os.environ.get('SMTP_PASSWORD')

    # Last resort: check database (less secure, but functional)
    if not password:
        password = get_setting('_smtp_password_fallback')

    return email, password


def save_smtp_credentials(email, password):
    """Save SMTP credentials securely.

    Uses OS keyring when available, falls back to database storage
    in Docker/headless environments.
    """
    set_setting('smtp_email', email)

    if _USE_KEYRING:
        keyring.set_password("llcscraper", "smtp_password", password)
    else:
        # In Docker: store in DB (the DB file is on a mounted volume)
        set_setting('_smtp_password_fallback', password)


def send_email(to_address, subject, html_content, from_name=None):
    """Send an email via SMTP."""
    try:
        email, password = get_smtp_credentials()

        if not email or not password:
            add_log("SMTP credentials not configured", "error")
            return False

        server_host = get_setting('smtp_server', 'smtp.gmail.com')
        server_port = int(get_setting('smtp_port', 587))
        security = get_setting('smtp_security', 'starttls')

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        if from_name:
            msg['From'] = f"{from_name} <{email}>"
        else:
            msg['From'] = email
        msg['To'] = to_address

        msg.attach(MIMEText(html_content, 'html'))

        if security == 'ssl':
            with smtplib.SMTP_SSL(server_host, server_port) as server:
                server.login(email, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(server_host, server_port) as server:
                server.starttls()
                server.login(email, password)
                server.send_message(msg)

        return True

    except Exception as e:
        add_log(f"Email send failed: {str(e)}", "error")
        return False


def render_outreach_email(llc):
    """Render the outreach email template for an LLC."""
    template = _jinja_env.get_template('email_outreach.html')

    from_email = get_setting('smtp_email', '')
    from_name = get_setting('email_from_name', 'Jesse')
    site_url = get_setting('site_url', 'https://hammerandpixels.com')

    return template.render(
        business_name=html_escape(llc.get('business_name', '')),
        from_name=from_name,
        from_email=from_email,
        site_url=site_url,
        llc=llc
    )


def send_outreach_email(llc):
    """Send an outreach email to a specific LLC."""
    email_to = llc.get('email_address')
    if not email_to:
        add_log(f"No email address for {llc['business_name']}", "warning")
        return False

    business_name = llc.get('business_name', 'your new business')
    from_name = get_setting('email_from_name', 'Jesse')

    subject = f"Congrats on {business_name} - a quick hello from a fellow CT small biz"
    html_content = render_outreach_email(llc)

    success = send_email(email_to, subject, html_content, from_name=from_name)

    if success:
        update_llc_outreach_status(llc['id'], 'sent')
        log_email_sent(llc['id'], email_to, subject, status='sent')
        add_log(f"Outreach email sent to {email_to} ({business_name})", "success")
    else:
        log_email_sent(llc['id'], email_to, subject, status='failed',
                       error_message='SMTP send failed')

    return success


def process_email_queue():
    """Send outreach emails to all approved LLCs, respecting daily limit."""
    daily_limit = int(get_setting('daily_email_limit', 10))
    sent_today = get_emails_sent_today()
    remaining = daily_limit - sent_today

    if remaining <= 0:
        add_log(f"Daily email limit reached ({daily_limit})", "warning")
        return 0

    approved = get_approved_for_email(limit=remaining)

    if not approved:
        add_log("No approved LLCs in email queue", "info")
        return 0

    add_log(f"Processing email queue: {len(approved)} to send ({sent_today}/{daily_limit} sent today)", "info")

    sent_count = 0
    rate_limit = float(get_setting('email_rate_limit_seconds', 5))

    for llc in approved:
        if not llc.get('email_address'):
            update_llc_outreach_status(llc['id'], 'skipped', skip_reason='no_email_address')
            continue

        success = send_outreach_email(llc)
        if success:
            sent_count += 1

        # Rate limit between sends
        if sent_count < len(approved):
            import time
            time.sleep(rate_limit)

    add_log(f"Email queue processed: {sent_count} sent", "success")
    return sent_count


def preview_outreach_email(llc):
    """Generate a preview of the outreach email for an LLC."""
    html_content = render_outreach_email(llc)
    business_name = llc.get('business_name', 'your new business')
    subject = f"Congrats on {business_name} - a quick hello from a fellow CT small biz"

    return {
        'subject': subject,
        'html': html_content,
        'to': llc.get('email_address', '(no email found)'),
        'business_name': business_name
    }
