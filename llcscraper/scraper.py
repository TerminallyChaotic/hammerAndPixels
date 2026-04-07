import csv
import io
import requests
import time
import os
from datetime import datetime, timedelta
from database import is_llc_seen, save_llc, add_log, get_setting

# CT Open Data (Socrata) API - Business Master dataset
CT_DATA_API = "https://data.ct.gov/resource/n7gp-d28j.json"

# Webhook configuration
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s

# Default webhook settings (can be overridden via environment)
DEFAULT_WEBHOOK_URL = 'http://localhost:5001/api/llc/webhook'


def post_llcs_to_webhook(llcs, webhook_url=None, api_key=None):
    """Post a batch of LLCs to the webhook endpoint with retry logic.

    Args:
        llcs (list): List of LLC dicts with filing_number, business_name, filing_date, address, etc.
        webhook_url (str): The webhook endpoint URL (defaults to WEBHOOK_URL env or DEFAULT_WEBHOOK_URL)
        api_key (str): API key for authentication (defaults to LLCSCRAPER_API_KEY env)

    Returns:
        bool: True if successful, False if all retries failed
    """
    if not llcs:
        return True  # Nothing to post

    # Resolve webhook URL
    if webhook_url is None:
        webhook_url = os.environ.get('WEBHOOK_URL', DEFAULT_WEBHOOK_URL)

    # Resolve API key
    if api_key is None:
        api_key = os.environ.get('LLCSCRAPER_API_KEY', '')

    payload = {'llcs': llcs}
    headers = {'Content-Type': 'application/json'}

    # Add API key if available
    if api_key:
        headers['X-API-Key'] = api_key

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            add_log(f"Posting {len(llcs)} LLC(s) to webhook (attempt {attempt}/{MAX_RETRIES})", "info")

            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            # Check response indicates success
            resp_data = response.json()
            if resp_data.get('success'):
                count = resp_data.get('count', len(llcs))
                add_log(f"Webhook accepted {count} LLC(s)", "success")
                return True
            else:
                error_msg = resp_data.get('error', 'Unknown error')
                add_log(f"Webhook returned error: {error_msg}", "error")
                return False

        except Exception as e:
            # Catch all exceptions: requests.RequestException, connection errors, etc.
            if attempt < MAX_RETRIES:
                backoff_seconds = RETRY_BACKOFF[attempt - 1]
                add_log(f"Webhook POST failed (attempt {attempt}): {str(e)}. Retrying in {backoff_seconds}s...", "warn")
                time.sleep(backoff_seconds)
            else:
                add_log(f"Webhook POST failed after {MAX_RETRIES} attempts: {str(e)}", "error")
                return False

    return False


def run_scraper():
    """Run the CT LLC scraper via the open data API.

    Flow:
    1. Fetch new LLCs from CT Open Data API
    2. POST all LLCs to webhook endpoint in a single batch
    3. Webhook stores them with pending_review status
    4. Return the list of LLCs that were sent (success only, not the full final list)
    """
    try:
        add_log("LLC scraper started", "info")

        lookback_days = int(get_setting('scrape_lookback_days', 7))
        add_log(f"Searching for LLCs filed in last {lookback_days} days", "info")

        new_llcs = fetch_new_llcs(lookback_days)

        if not new_llcs:
            add_log("Scraper complete: no new LLCs found", "info")
            return []

        add_log(f"Found {len(new_llcs)} new LLC(s), posting to webhook...", "info")

        # POST all LLCs to webhook in a single batch
        # webhook_url and api_key will be read from environment if not explicitly passed
        success = post_llcs_to_webhook(new_llcs)

        if success:
            add_log(f"Scraper complete: {len(new_llcs)} new LLC(s) posted to webhook", "success")
            return new_llcs
        else:
            add_log(f"Scraper found {len(new_llcs)} new LLCs but webhook posting failed", "error")
            return []

    except Exception as e:
        add_log(f"Scraper error: {str(e)}", "error")
        return []


def fetch_new_llcs(lookback_days=7):
    """Fetch newly registered LLCs from the CT Open Data API.

    Returns a list of LLC dicts ready to POST to the webhook.
    Note: This function builds the list but does NOT save or POST to webhook—
    that happens in run_scraper() after all LLCs are fetched.
    """
    cutoff = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%dT00:00:00')
    new_llcs = []
    offset = 0
    page_size = 500
    max_pages = int(get_setting('max_scrape_pages', 10))

    for page_num in range(max_pages):
        params = {
            "$where": f"business_type='LLC' AND date_registration>'{cutoff}' AND status='Active'",
            "$order": "date_registration DESC",
            "$limit": page_size,
            "$offset": offset,
        }

        try:
            resp = requests.get(CT_DATA_API, params=params, timeout=30)
            resp.raise_for_status()
            records = resp.json()
        except requests.RequestException as e:
            add_log(f"API request failed: {str(e)}", "error")
            break

        if not records:
            break

        add_log(f"API page {page_num + 1}: {len(records)} records", "info")

        for rec in records:
            filing_number = rec.get('accountnumber', '')
            business_name = rec.get('name', '')

            if not filing_number or not business_name:
                continue

            if is_llc_seen(filing_number):
                continue

            # Build address from billing fields
            address_parts = [
                rec.get('billingstreet', ''),
                rec.get('billing_unit', ''),
            ]
            city_state_zip = ', '.join(filter(None, [
                rec.get('billingcity', ''),
                rec.get('billingstate', ''),
                rec.get('billingpostalcode', ''),
            ]))
            principal_address = ' '.join(filter(None, address_parts)).strip()
            if city_state_zip:
                principal_address = f"{principal_address}, {city_state_zip}" if principal_address else city_state_zip

            # Parse registration date
            filing_date = rec.get('date_registration', '')
            if filing_date and 'T' in filing_date:
                filing_date = filing_date.split('T')[0]

            # Build LLC dict for webhook (includes both required and optional fields)
            # Webhook requires: filing_number, business_name, filing_date, address, registered_agent
            llc_dict = {
                'filing_number': filing_number,
                'business_name': business_name,
                'filing_date': filing_date,
                'address': principal_address or '',  # Required by webhook
                'registered_agent': '',  # Required by webhook, but not in CT API
                'email_address': rec.get('business_email_address'),
                'naics_code': rec.get('naics_code'),
                'mailing_address': rec.get('mailing_address'),
            }

            new_llcs.append(llc_dict)
            add_log(f"New LLC found: {business_name} (#{filing_number})", "info")

        if len(records) < page_size:
            break
        offset += page_size

    return new_llcs


def import_csv(csv_content):
    """Import LLC records from CSV content (manual fallback).

    Expected CSV columns: filing_number, business_name, filing_date,
    principal_address, registered_agent
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    imported = 0

    for row in reader:
        filing_number = row.get('filing_number', '').strip()
        business_name = row.get('business_name', '').strip()

        if not filing_number or not business_name:
            continue

        if is_llc_seen(filing_number):
            continue

        save_llc(
            filing_number=filing_number,
            business_name=business_name,
            filing_date=row.get('filing_date', '').strip() or None,
            principal_address=row.get('principal_address', '').strip() or None,
            registered_agent=row.get('registered_agent', '').strip() or None,
            agent_address=row.get('agent_address', '').strip() or None,
            source='csv_import'
        )
        imported += 1

    add_log(f"CSV import: {imported} new LLC(s) imported", "success")
    return imported
