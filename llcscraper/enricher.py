import re
import time
import requests
from html import escape as html_escape
from database import (
    get_pending_enrichment, update_llc_enrichment,
    update_llc_outreach_status, add_log, get_setting
)

# Domains that are directories/social, not the business's own website
DIRECTORY_DOMAINS = {
    'facebook.com', 'yelp.com', 'yellowpages.com', 'bbb.org',
    'linkedin.com', 'instagram.com', 'twitter.com', 'x.com',
    'mapquest.com', 'google.com', 'manta.com', 'dandb.com',
    'bizapedia.com', 'opencorporates.com', 'buzzfile.com',
    'chamberofcommerce.com', 'ct.gov', 'service.ct.gov',
    'secretary.state.ct.us', 'indeed.com', 'glassdoor.com',
    'tiktok.com', 'pinterest.com', 'nextdoor.com', 'angi.com',
    'thumbtack.com', 'homeadvisor.com',
}

# Common parked/placeholder page indicators
PARKED_INDICATORS = [
    'this domain is for sale',
    'domain is parked',
    'buy this domain',
    'under construction',
    'coming soon',
    'website coming soon',
    'godaddy',
    'squarespace - claim this domain',
    'this site can\'t be reached',
    'page not found',
]

# Request timeout (seconds)
REQUEST_TIMEOUT = 10

# Delay between Google searches (seconds) - be respectful of rate limits
SEARCH_DELAY = 12


def run_enricher():
    """Enrich all pending LLCs with contact information."""
    pending = get_pending_enrichment(limit=20)
    rate_limit = float(get_setting('enricher_rate_limit', SEARCH_DELAY))

    if not pending:
        add_log("No LLCs pending enrichment", "info")
        return 0

    add_log(f"Starting enrichment for {len(pending)} LLC(s)", "info")
    enriched_count = 0

    for llc in pending:
        try:
            result = enrich_llc(llc)
            if result:
                enriched_count += 1
            time.sleep(rate_limit)
        except Exception as e:
            add_log(f"Error enriching {llc['business_name']}: {str(e)}", "error")
            update_llc_enrichment(
                llc['id'],
                enrichment_status='failed',
                enrichment_notes=str(e)
            )

    add_log(f"Enrichment complete: {enriched_count}/{len(pending)} enriched", "success")
    return enriched_count


def enrich_llc(llc):
    """Enrich a single LLC with website and email information."""
    business_name = llc['business_name']
    llc_id = llc['id']

    add_log(f"Enriching: {business_name}", "info")

    # Clean the business name for searching (remove LLC suffix)
    search_name = _clean_business_name(business_name)

    # Step 1: Google search for the business
    search_results = search_google(search_name, 'Connecticut')

    website_url = None
    has_website = -1  # -1 = no website found
    email_address = None
    phone = None
    notes = []

    # Step 2: Check search results for a website
    if search_results:
        for url in search_results:
            domain = _extract_domain(url)

            # Skip directory/social sites
            if any(d in domain for d in DIRECTORY_DOMAINS):
                continue

            # This might be their own website
            if check_website(url):
                website_url = url
                has_website = 1
                notes.append(f"Website found: {url}")

                # Step 3: Try to find email on the website
                found_email = find_email_on_page(url)
                if found_email:
                    email_address = found_email
                    notes.append(f"Email found: {found_email}")

                # Try to find phone on the website
                found_phone = find_phone_on_page(url)
                if found_phone:
                    phone = found_phone

                break

    if not website_url:
        notes.append("No website found")

    # Step 4: If no email from website, try common email patterns
    if not email_address and website_url:
        domain = _extract_domain(website_url)
        guessed = _guess_email(domain)
        if guessed:
            notes.append(f"Guessed email pattern: {guessed}")
            # Don't set as confirmed email, just note it

    # Update the LLC record
    enrichment_notes = '; '.join(notes) if notes else None

    update_llc_enrichment(
        llc_id,
        website_url=website_url,
        has_website=has_website,
        email_address=email_address,
        phone=phone,
        enrichment_status='enriched',
        enrichment_notes=enrichment_notes
    )

    # Auto-skip if they already have a professional website
    auto_skip = get_setting('auto_skip_has_website', True)
    if has_website == 1 and auto_skip:
        update_llc_outreach_status(llc_id, 'skipped', skip_reason='has_existing_website')
        add_log(f"Auto-skipped {business_name} (has website)", "info")

    return True


def search_google(business_name, state='Connecticut'):
    """Search Google for a business and return top result URLs."""
    try:
        from googlesearch import search
    except ImportError:
        add_log("googlesearch-python not installed. Run: pip install googlesearch-python", "error")
        return []

    query = f'"{business_name}" {state}'
    results = []

    try:
        for url in search(query, num_results=5, sleep_interval=2):
            results.append(url)
    except Exception as e:
        add_log(f"Google search error for '{business_name}': {str(e)}", "warning")

    return results


def check_website(url):
    """Check if a URL is a real, active website (not parked or placeholder)."""
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; HammerPixelsBot/1.0)'},
            allow_redirects=True
        )

        if response.status_code != 200:
            return False

        content_lower = response.text.lower()

        # Check for parked/placeholder indicators
        for indicator in PARKED_INDICATORS:
            if indicator in content_lower:
                return False

        # Check that the page has meaningful content (not just a shell)
        # A real website typically has more than 500 chars of visible text
        text_content = re.sub(r'<[^>]+>', '', response.text)
        text_content = re.sub(r'\s+', ' ', text_content).strip()

        if len(text_content) < 500:
            return False

        return True

    except requests.RequestException:
        return False


def find_email_on_page(url):
    """Scrape a webpage for email addresses."""
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; HammerPixelsBot/1.0)'},
            allow_redirects=True
        )

        if response.status_code != 200:
            return None

        # Find mailto: links
        mailto_pattern = re.compile(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})')
        mailto_matches = mailto_pattern.findall(response.text)

        if mailto_matches:
            return mailto_matches[0]

        # Find email patterns in text
        email_pattern = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
        all_emails = email_pattern.findall(response.text)

        # Filter out common non-business emails
        skip_patterns = ['example.com', 'sentry.io', 'wixpress', 'wordpress',
                         'w3.org', 'schema.org', 'googleapis.com', 'gravatar.com']

        for email in all_emails:
            email_lower = email.lower()
            if not any(skip in email_lower for skip in skip_patterns):
                return email

        # Also check common contact/about pages
        for page_path in ['/contact', '/about', '/contact-us', '/about-us']:
            try:
                contact_url = url.rstrip('/') + page_path
                resp = requests.get(
                    contact_url,
                    timeout=REQUEST_TIMEOUT,
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; HammerPixelsBot/1.0)'},
                    allow_redirects=True
                )
                if resp.status_code == 200:
                    for email in email_pattern.findall(resp.text):
                        email_lower = email.lower()
                        if not any(skip in email_lower for skip in skip_patterns):
                            return email
            except requests.RequestException:
                continue

    except requests.RequestException:
        pass

    return None


def find_phone_on_page(url):
    """Scrape a webpage for phone numbers."""
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; HammerPixelsBot/1.0)'},
            allow_redirects=True
        )

        if response.status_code != 200:
            return None

        # Common US phone patterns
        phone_pattern = re.compile(
            r'(?:tel:|phone:?\s*)?(?:\+?1[-.\s]?)?'
            r'\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})'
        )

        matches = phone_pattern.findall(response.text)
        if matches:
            area, prefix, line = matches[0]
            return f"({area}) {prefix}-{line}"

    except requests.RequestException:
        pass

    return None


def _clean_business_name(name):
    """Clean business name for searching (remove LLC suffixes, punctuation)."""
    # Remove common suffixes
    suffixes = [
        r',?\s*LLC\.?$', r',?\s*L\.L\.C\.?$', r',?\s*Limited Liability Company$',
        r',?\s*Inc\.?$', r',?\s*Corp\.?$', r',?\s*Corporation$',
    ]
    cleaned = name
    for suffix in suffixes:
        cleaned = re.sub(suffix, '', cleaned, flags=re.IGNORECASE)

    return cleaned.strip()


def _extract_domain(url):
    """Extract the domain from a URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return ''


def _guess_email(domain):
    """Guess common email patterns for a domain."""
    common_prefixes = ['info', 'contact', 'hello', 'admin']
    return [f"{prefix}@{domain}" for prefix in common_prefixes]
