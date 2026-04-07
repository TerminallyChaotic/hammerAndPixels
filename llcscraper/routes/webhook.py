from flask import Blueprint, request, jsonify
import database
import traceback
from functools import wraps
import os

webhook_bp = Blueprint('webhook', __name__, url_prefix='/api/llc')


def require_api_key(f):
    """Decorator to require X-API-Key header for webhook access."""
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


@webhook_bp.route('/webhook', methods=['POST'])
@require_api_key
def receive_llcs():
    """Receive batch of LLCs from scraper, store with pending_review status."""
    try:
        payload = request.get_json()

        if not payload or 'llcs' not in payload:
            return jsonify({'error': 'Invalid payload, missing "llcs" key'}), 400

        llcs = payload['llcs']
        if not isinstance(llcs, list) or len(llcs) == 0:
            return jsonify({'error': 'llcs must be non-empty list'}), 400

        saved_count = 0
        for llc_data in llcs:
            # Validate required fields
            required = ['filing_number', 'business_name', 'filing_date', 'address', 'registered_agent']
            missing_fields = [f for f in required if f not in llc_data]
            if missing_fields:
                log_msg = f"Skipped LLC: missing fields {missing_fields}"
                if 'business_name' in llc_data:
                    log_msg += f" (business: {llc_data['business_name']})"
                if 'filing_number' in llc_data:
                    log_msg += f" (filing: {llc_data['filing_number']})"
                database.add_log(log_msg, "warn")
                continue

            # Save with pending_review status
            row_id = database.save_llc(
                filing_number=llc_data['filing_number'],
                business_name=llc_data['business_name'],
                filing_date=llc_data['filing_date'],
                principal_address=llc_data.get('address'),
                mailing_address=llc_data.get('mailing_address'),
                registered_agent=llc_data.get('registered_agent'),
                agent_address=llc_data.get('agent_address'),
                status='pending_review',
                source='webhook',
                email_address=llc_data.get('email_address'),
                naics_code=llc_data.get('naics_code')
            )

            if row_id:
                # Set openclaw_reviewed to false (0 in SQLite)
                database.mark_openclaw_unreviewed(row_id)
                saved_count += 1

        database.add_log(f"Webhook received: {saved_count} new LLC(s) in pending_review", "info")
        return jsonify({'success': True, 'count': saved_count}), 200

    except Exception as e:
        # Log full traceback for debugging, but don't expose it to caller
        database.add_log(f"Webhook error: {traceback.format_exc()}", "error")
        return jsonify({'error': 'Internal server error'}), 500
