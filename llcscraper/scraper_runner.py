"""CLI runner for the LLC scraper.

Usage:
    python scraper_runner.py              # Run scraper only
    python scraper_runner.py --enrich     # Run scraper + enricher
    python scraper_runner.py --send       # Run scraper + enricher + send emails
"""
import sys
import database
from scraper import run_scraper
from enricher import run_enricher
from emailer import process_email_queue

if __name__ == '__main__':
    database.init_db()

    print("CT LLC Scraper - CLI Runner")
    print("=" * 40)

    # Run scraper
    print("\n[1/3] Running scraper...")
    new_llcs = run_scraper()
    print(f"  Found {len(new_llcs) if new_llcs else 0} new LLC(s)")

    # Optionally run enricher
    if '--enrich' in sys.argv or '--send' in sys.argv:
        print("\n[2/3] Running enricher...")
        enriched = run_enricher()
        print(f"  Enriched {enriched} LLC(s)")
    else:
        print("\n[2/3] Skipping enricher (use --enrich to run)")

    # Optionally send emails
    if '--send' in sys.argv:
        print("\n[3/3] Processing email queue...")
        sent = process_email_queue()
        print(f"  Sent {sent} email(s)")
    else:
        print("\n[3/3] Skipping email send (use --send to run)")

    print("\nDone.")
