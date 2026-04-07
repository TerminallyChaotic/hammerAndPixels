from flask import Blueprint, request, jsonify
import database

webhook_bp = Blueprint('webhook', __name__, url_prefix='/api/llc')


@webhook_bp.route('/webhook', methods=['POST'])
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
            if not all(field in llc_data for field in required):
                database.add_log(f"Skipped LLC: missing required fields", "warn")
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
        database.add_log(f"Webhook error: {str(e)}", "error")
        return jsonify({'error': str(e)}), 500
