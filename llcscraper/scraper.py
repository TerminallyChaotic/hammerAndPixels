import csv
import io
import requests
from datetime import datetime, timedelta
from database import is_llc_seen, save_llc, add_log, get_setting

# CT Open Data (Socrata) API - Business Master dataset
CT_DATA_API = "https://data.ct.gov/resource/n7gp-d28j.json"


def run_scraper():
    """Run the CT LLC scraper via the open data API."""
    try:
        add_log("LLC scraper started", "info")

        lookback_days = int(get_setting('scrape_lookback_days', 7))
        add_log(f"Searching for LLCs filed in last {lookback_days} days", "info")

        new_llcs = fetch_new_llcs(lookback_days)

        if new_llcs:
            add_log(f"Scraper complete: {len(new_llcs)} new LLC(s) found", "success")
        else:
            add_log("Scraper complete: no new LLCs found", "info")

        return new_llcs

    except Exception as e:
        add_log(f"Scraper error: {str(e)}", "error")
        return []


def fetch_new_llcs(lookback_days=7):
    """Fetch newly registered LLCs from the CT Open Data API."""
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

            row_id = save_llc(
                filing_number=filing_number,
                business_name=business_name,
                filing_date=filing_date,
                principal_address=principal_address or None,
                mailing_address=rec.get('mailing_address') or None,
                business_type='LLC',
                source='ct_data_api',
                email_address=rec.get('business_email_address') or None,
                naics_code=rec.get('naics_code') or None,
            )

            if row_id:
                new_llcs.append({
                    'filing_number': filing_number,
                    'business_name': business_name,
                    'filing_date': filing_date,
                    'principal_address': principal_address,
                    'email_address': rec.get('business_email_address'),
                    'naics_code': rec.get('naics_code'),
                })
                add_log(f"New LLC: {business_name} (#{filing_number})", "success")

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
