from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from functools import wraps
from dotenv import load_dotenv
import os
import secrets
import database
from scraper import run_scraper, import_csv
from enricher import run_enricher
from emailer import (
    save_smtp_credentials, SMTP_PROVIDERS, process_email_queue,
    send_outreach_email, preview_outreach_email
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

# Initialize database
database.init_db()


def apply_env_defaults():
    """Seed database settings from environment variables on first run."""
    env_map = {
        'SMTP_EMAIL': 'smtp_email',
        'SMTP_SERVER': 'smtp_server',
        'SMTP_PORT': 'smtp_port',
        'SMTP_SECURITY': 'smtp_security',
        'EMAIL_FROM_NAME': 'email_from_name',
        'SITE_URL': 'site_url',
    }
    for env_key, db_key in env_map.items():
        val = os.environ.get(env_key)
        if val and not database.get_setting(db_key):
            database.set_setting(db_key, val)

    # Handle SMTP password via the secure credential path
    smtp_email = os.environ.get('SMTP_EMAIL')
    smtp_pass = os.environ.get('SMTP_PASSWORD')
    if smtp_email and smtp_pass:
        existing_email, existing_pass = None, None
        try:
            from emailer import get_smtp_credentials
            existing_email, existing_pass = get_smtp_credentials()
        except Exception:
            pass
        if not existing_pass:
            save_smtp_credentials(smtp_email, smtp_pass)

    # Set provider to protonmail if server is 127.0.0.1
    if os.environ.get('SMTP_SERVER') == '127.0.0.1' and not database.get_setting('smtp_provider'):
        database.set_setting('smtp_provider', 'protonmail')


apply_env_defaults()

# Allowed settings keys (prevent injection)
ALLOWED_SETTINGS = {
    'scrape_lookback_days', 'scrape_frequency_hours', 'scrape_times',
    'max_scrape_pages', 'enricher_rate_limit', 'auto_skip_has_website',
    'smtp_email', 'smtp_provider', 'smtp_server', 'smtp_port', 'smtp_security',
    'email_from_name', 'site_url', 'auto_send_enabled',
    'daily_email_limit', 'email_rate_limit_seconds',
}


# --- Auth ---

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        expected_key = os.environ.get('LLCSCRAPER_API_KEY')

        if request.remote_addr in ('127.0.0.1', 'localhost', '::1'):
            return f(*args, **kwargs)

        if not expected_key or api_key != expected_key:
            return jsonify({'error': 'Unauthorized'}), 401

        return f(*args, **kwargs)
    return decorated_function


# --- Scheduler ---

scheduler = BackgroundScheduler()
scheduler.start()


def schedule_scraper():
    """Schedule the scraper based on settings."""
    # Remove existing scraper jobs
    for job in scheduler.get_jobs():
        if job.id.startswith('scraper_job'):
            scheduler.remove_job(job.id)

    scrape_times = database.get_setting('scrape_times', '')

    if scrape_times:
        times = [t.strip() for t in scrape_times.split(',') if t.strip()]
        if times:
            try:
                for i, time_str in enumerate(times):
                    hour, minute = map(int, time_str.split(':'))
                    scheduler.add_job(
                        run_scraper,
                        'cron',
                        hour=hour,
                        minute=minute,
                        id=f'scraper_job_{i}',
                        name=f'LLC Scraper ({time_str})',
                        replace_existing=True
                    )
                database.add_log(f"Scheduled scraper for: {', '.join(times)}", "info")
                return
            except Exception as e:
                database.add_log(f"Invalid scrape_times format: {str(e)}", "warning")

    # Fallback to interval
    interval = int(database.get_setting('scrape_frequency_hours', 12))
    if interval > 0:
        scheduler.add_job(
            run_scraper,
            'interval',
            hours=interval,
            id='scraper_job',
            name='LLC Scraper'
        )
        database.add_log(f"Scheduled scraper to run every {interval} hours", "info")


# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/settings', methods=['GET'])
@require_api_key
def get_settings():
    settings = database.get_all_settings()
    return jsonify(settings)


@app.route('/api/settings', methods=['POST'])
@require_api_key
def update_settings():
    data = request.json
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    # Handle SMTP credentials separately
    if 'smtp_email' in data and 'smtp_password' in data:
        if data['smtp_password']:
            save_smtp_credentials(data['smtp_email'], data['smtp_password'])
        data.pop('smtp_password')

    for key, value in data.items():
        if key in ALLOWED_SETTINGS:
            database.set_setting(key, value)
        else:
            database.add_log(f"Attempted to set disallowed key: {key}", "warning")

    if 'scrape_frequency_hours' in data or 'scrape_times' in data:
        schedule_scraper()

    database.add_log("Settings updated", "info")
    return jsonify({'success': True})


@app.route('/api/smtp-providers', methods=['GET'])
@require_api_key
def get_smtp_providers():
    return jsonify(SMTP_PROVIDERS)


@app.route('/api/run-scraper', methods=['POST'])
@require_api_key
def run_scraper_endpoint():
    try:
        new_llcs = run_scraper()
        count = len(new_llcs) if new_llcs else 0
        return jsonify({'success': True, 'message': f'{count} new LLC(s) found'})
    except Exception as e:
        database.add_log(f"Scraper error: {type(e).__name__}", "error")
        return jsonify({'success': False, 'message': 'Scraper execution failed'}), 500


@app.route('/api/run-enricher', methods=['POST'])
@require_api_key
def run_enricher_endpoint():
    try:
        count = run_enricher()
        return jsonify({'success': True, 'message': f'{count} LLC(s) enriched'})
    except Exception as e:
        database.add_log(f"Enricher error: {type(e).__name__}", "error")
        return jsonify({'success': False, 'message': 'Enricher execution failed'}), 500


@app.route('/api/import-csv', methods=['POST'])
@require_api_key
def import_csv_endpoint():
    """Import LLCs from CSV data."""
    data = request.json
    csv_content = data.get('csv', '') if data else ''
    if not csv_content:
        return jsonify({'error': 'No CSV data provided'}), 400

    try:
        count = import_csv(csv_content)
        return jsonify({'success': True, 'message': f'{count} LLC(s) imported'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# --- LLC routes ---

@app.route('/api/llcs', methods=['GET'])
@require_api_key
def get_llcs():
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    outreach_status = request.args.get('outreach_status')
    enrichment_status = request.args.get('enrichment_status')
    has_email = request.args.get('has_email')
    search = request.args.get('search')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    if has_email is not None:
        has_email = has_email.lower() == 'true'

    llcs = database.get_llcs(
        limit=limit, offset=offset,
        outreach_status=outreach_status,
        enrichment_status=enrichment_status,
        has_email=has_email,
        search=search,
        date_from=date_from,
        date_to=date_to
    )
    return jsonify(llcs)


@app.route('/api/llcs/<int:llc_id>', methods=['GET'])
@require_api_key
def get_llc(llc_id):
    llc = database.get_llc(llc_id)
    if not llc:
        return jsonify({'error': 'LLC not found'}), 404
    return jsonify(llc)


@app.route('/api/llcs/<int:llc_id>/approve', methods=['POST'])
@require_api_key
def approve_llc(llc_id):
    llc = database.get_llc(llc_id)
    if not llc:
        return jsonify({'error': 'LLC not found'}), 404
    database.update_llc_outreach_status(llc_id, 'approved')
    database.add_log(f"Approved for outreach: {llc['business_name']}", "info")
    return jsonify({'success': True})


@app.route('/api/llcs/<int:llc_id>/skip', methods=['POST'])
@require_api_key
def skip_llc(llc_id):
    llc = database.get_llc(llc_id)
    if not llc:
        return jsonify({'error': 'LLC not found'}), 404
    data = request.json or {}
    reason = data.get('reason', 'manually skipped')
    database.update_llc_outreach_status(llc_id, 'skipped', skip_reason=reason)
    database.add_log(f"Skipped: {llc['business_name']} ({reason})", "info")
    return jsonify({'success': True})


@app.route('/api/llcs/<int:llc_id>/send', methods=['POST'])
@require_api_key
def send_single_email(llc_id):
    llc = database.get_llc(llc_id)
    if not llc:
        return jsonify({'error': 'LLC not found'}), 404
    if not llc.get('email_address'):
        return jsonify({'error': 'No email address for this LLC'}), 400

    success = send_outreach_email(llc)
    return jsonify({'success': success})


@app.route('/api/email-preview/<int:llc_id>', methods=['GET'])
@require_api_key
def email_preview(llc_id):
    llc = database.get_llc(llc_id)
    if not llc:
        return jsonify({'error': 'LLC not found'}), 404
    preview = preview_outreach_email(llc)
    return jsonify(preview)


@app.route('/api/send-emails', methods=['POST'])
@require_api_key
def send_emails_endpoint():
    try:
        count = process_email_queue()
        return jsonify({'success': True, 'message': f'{count} email(s) sent'})
    except Exception as e:
        database.add_log(f"Email queue error: {str(e)}", "error")
        return jsonify({'success': False, 'message': 'Email processing failed'}), 500


@app.route('/api/email-history', methods=['GET'])
@require_api_key
def get_email_history():
    history = database.get_email_history(50)
    return jsonify(history)


@app.route('/api/stats', methods=['GET'])
@require_api_key
def get_stats():
    stats = database.get_stats()
    return jsonify(stats)


@app.route('/api/logs', methods=['GET'])
@require_api_key
def get_logs():
    logs = database.get_logs(50)
    formatted = []
    for log in logs:
        formatted.append({
            'timestamp': log[0],
            'message': log[1],
            'status': log[2]
        })
    return jsonify(formatted)


@app.route('/api/scheduler-status', methods=['GET'])
@require_api_key
def scheduler_status():
    jobs = []
    for job in scheduler.get_jobs():
        if job.id.startswith('scraper_job'):
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            })

    return jsonify({
        'running': len(jobs) > 0,
        'jobs': jobs,
        'frequency': database.get_setting('scrape_frequency_hours', 12)
    })


if __name__ == '__main__':
    schedule_scraper()

    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    api_key = os.environ.get('LLCSCRAPER_API_KEY')

    print("\n" + "=" * 50)
    print("CT LLC Scraper - Hammer & Pixels Lead Gen")
    print("=" * 50)
    print("\nDashboard running at http://localhost:5075")
    if api_key:
        print("API authentication enabled")
    else:
        print("Localhost access allowed without API key")
    print(f"Debug mode: {'ON' if debug_mode else 'OFF'}\n")

    app.run(debug=debug_mode, use_reloader=False, port=5075)
