from flask import Blueprint, request, jsonify
import database
import traceback
from functools import wraps
import os
from datetime import datetime, timedelta
import sqlite3

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


@webhook_bp.route('/pending-review', methods=['GET'])
@require_api_key
def get_pending_review():
    """Return LLCs with status='pending_review' for OpenClaw curation.

    Query parameters:
    - last_hours: Get LLCs created in last N hours (e.g., ?last_hours=24)
    - date_from: ISO format datetime for range start
    - date_to: ISO format datetime for range end

    Returns: {llcs: [...], count: N}
    """
    try:
        conn = sqlite3.connect(database.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query with optional date filtering
        query = """
            SELECT id, filing_number, business_name, filing_date, principal_address,
                   registered_agent, status, openclaw_reviewed, discovered_at
            FROM llcs
            WHERE status = 'pending_review'
        """
        params = []

        # Handle last_hours filter
        last_hours = request.args.get('last_hours')
        if last_hours:
            try:
                hours = int(last_hours)
                cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                # Convert to SQLite format (space instead of T)
                cutoff_str = cutoff_time.isoformat().replace('T', ' ')
                query += " AND discovered_at >= ?"
                params.append(cutoff_str)
            except ValueError:
                return jsonify({'error': 'last_hours must be an integer'}), 400

        # Handle date_from / date_to range
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        if date_from:
            try:
                datetime.fromisoformat(date_from)  # Validate format
                # Convert ISO format to SQLite format (space instead of T)
                date_from_str = date_from.replace('T', ' ')
                query += " AND discovered_at >= ?"
                params.append(date_from_str)
            except ValueError:
                return jsonify({'error': 'date_from must be ISO format (e.g., 2026-04-07T00:00:00)'}), 400

        if date_to:
            try:
                datetime.fromisoformat(date_to)  # Validate format
                # Convert ISO format to SQLite format (space instead of T)
                date_to_str = date_to.replace('T', ' ')
                query += " AND discovered_at <= ?"
                params.append(date_to_str)
            except ValueError:
                return jsonify({'error': 'date_to must be ISO format (e.g., 2026-04-07T23:59:59)'}), 400

        # Note: If both date_from/to and last_hours provided, both filters are applied (AND logic)

        # Order by creation date ascending (FIFO for OpenClaw)
        query += " ORDER BY discovered_at ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        llcs = [dict(row) for row in rows]
        database.add_log(f"Pending-review query returned {len(llcs)} LLC(s)", "info")
        return jsonify({'llcs': llcs, 'count': len(llcs)}), 200

    except Exception as e:
        database.add_log(f"Pending-review query error: {traceback.format_exc()}", "error")
        return jsonify({'error': 'Internal server error'}), 500


def _update_llc_review_status(llc_id_int, action, notes):
    """Mark an LLC as approved or rejected, creating audit trail entry.

    Args:
        llc_id_int (int): The LLC ID to update
        action (str): "approved" or "rejected"
        notes (str): Optional notes for audit trail

    Returns:
        Tuple[dict, int]: (response_dict, status_code)
    """
    conn = None
    cursor = None

    try:
        conn = sqlite3.connect(database.DB_PATH)
        cursor = conn.cursor()

        # Check LLC exists
        existing_llc = database.get_llc(llc_id_int)
        if not existing_llc:
            return {'error': 'LLC not found'}, 404

        # Begin transaction
        cursor.execute('BEGIN')

        # Update status and approval fields (both approve and reject mark as user-decided)
        cursor.execute('''
            UPDATE llcs
            SET status = ?, approved_by_user = 1, user_approved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (action, llc_id_int))

        # Create audit trail entry
        cursor.execute('''
            INSERT INTO openclaw_review_log (llc_id, action, notes, timestamp)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (llc_id_int, action, notes or ''))

        conn.commit()
        return {'success': True, 'status': action}, 200

    except Exception:
        if conn:
            conn.rollback()
        database.add_log(traceback.format_exc(), "error")
        return {'error': 'Internal server error'}, 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@webhook_bp.route('/<llc_id>/approve', methods=['POST'])
@require_api_key
def approve_llc(llc_id):
    """Approve an LLC by user, marking it as approved in the system.

    Request body: {action: "approve", notes?: "optional notes"}
    Returns: {success: true, status: "approved"}
    """
    # Validate llc_id is a valid integer
    try:
        llc_id_int = int(llc_id)
    except ValueError:
        return jsonify({'error': 'LLC ID must be a valid integer'}), 400

    # Parse optional notes from request
    try:
        payload = request.get_json() or {}
    except Exception:
        payload = {}

    notes = payload.get('notes', '')

    # Update LLC and log action
    response_dict, status_code = _update_llc_review_status(llc_id_int, 'approved', notes)

    if status_code == 200:
        database.add_log(f"LLC {llc_id_int} approved by user", "info")

    return jsonify(response_dict), status_code


@webhook_bp.route('/<llc_id>/reject', methods=['POST'])
@require_api_key
def reject_llc(llc_id):
    """Reject an LLC, marking it as rejected in the system.

    Request body: {action: "reject", notes?: "optional notes"}
    Returns: {success: true, status: "rejected"}
    """
    # Validate llc_id is a valid integer
    try:
        llc_id_int = int(llc_id)
    except ValueError:
        return jsonify({'error': 'LLC ID must be a valid integer'}), 400

    # Parse optional notes from request
    try:
        payload = request.get_json() or {}
    except Exception:
        payload = {}

    notes = payload.get('notes', '')

    # Update LLC and log action
    response_dict, status_code = _update_llc_review_status(llc_id_int, 'rejected', notes)

    if status_code == 200:
        database.add_log(f"LLC {llc_id_int} rejected by user", "info")

    return jsonify(response_dict), status_code
