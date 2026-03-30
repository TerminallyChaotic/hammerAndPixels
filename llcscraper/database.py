import sqlite3
import json
import os
from pathlib import Path

DB_PATH = Path('config/llcscraper.db')


def init_db():
    """Initialize the SQLite database."""
    os.makedirs('config', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Settings table (key/value store)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    # LLC records
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS llcs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filing_number TEXT UNIQUE NOT NULL,
            business_name TEXT NOT NULL,
            business_type TEXT DEFAULT 'LLC',
            filing_date TEXT,
            principal_address TEXT,
            mailing_address TEXT,
            registered_agent TEXT,
            agent_address TEXT,
            status TEXT DEFAULT 'active',
            source TEXT DEFAULT 'ct_sots',
            discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            website_url TEXT,
            has_website INTEGER DEFAULT 0,
            email_address TEXT,
            phone TEXT,
            enrichment_status TEXT DEFAULT 'pending',
            enriched_at DATETIME,
            enrichment_notes TEXT,
            outreach_status TEXT DEFAULT 'pending',
            approved_at DATETIME,
            emailed_at DATETIME,
            skip_reason TEXT
        )
    ''')

    # Email send log (audit trail)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            llc_id INTEGER NOT NULL,
            to_address TEXT NOT NULL,
            subject TEXT,
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'sent',
            error_message TEXT,
            FOREIGN KEY (llc_id) REFERENCES llcs(id)
        )
    ''')

    # Activity logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            message TEXT,
            status TEXT
        )
    ''')

    conn.commit()
    conn.close()


# --- Settings ---

def get_setting(key, default=None):
    """Get a setting from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    result = cursor.fetchone()
    conn.close()

    if result:
        try:
            return json.loads(result[0])
        except (json.JSONDecodeError, TypeError):
            return result[0]
    return default


def set_setting(key, value):
    """Save a setting to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if isinstance(value, (dict, list)):
        value = json.dumps(value)

    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()


def get_all_settings():
    """Get all settings."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM settings')
    results = cursor.fetchall()
    conn.close()

    settings = {}
    for key, value in results:
        try:
            settings[key] = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            settings[key] = value
    return settings


# --- LLC Records ---

def is_llc_seen(filing_number):
    """Check if an LLC has already been recorded."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM llcs WHERE filing_number = ?', (filing_number,))
    result = cursor.fetchone() is not None
    conn.close()
    return result


def save_llc(filing_number, business_name, filing_date=None, principal_address=None,
             mailing_address=None, registered_agent=None, agent_address=None,
             status='active', source='ct_sots', business_type='LLC',
             email_address=None, naics_code=None):
    """Save a new LLC record. Returns the new row id or None if duplicate."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO llcs
            (filing_number, business_name, business_type, filing_date, principal_address,
             mailing_address, registered_agent, agent_address, status, source,
             email_address, enrichment_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (filing_number, business_name, business_type, filing_date, principal_address,
              mailing_address, registered_agent, agent_address, status, source,
              email_address, naics_code))
        conn.commit()
        row_id = cursor.lastrowid if cursor.rowcount > 0 else None
        # If we got an email from the API, mark enrichment accordingly
        if row_id and email_address:
            cursor.execute('''
                UPDATE llcs SET enrichment_status = 'enriched', enriched_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (row_id,))
            conn.commit()
    finally:
        conn.close()
    return row_id


def get_llc(llc_id):
    """Get a single LLC by id."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM llcs WHERE id = ?', (llc_id,))
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None


def get_llcs(limit=50, offset=0, outreach_status=None, enrichment_status=None,
             has_email=None, search=None, date_from=None, date_to=None):
    """Get LLC records with optional filters."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = 'SELECT * FROM llcs WHERE 1=1'
    params = []

    if outreach_status:
        query += ' AND outreach_status = ?'
        params.append(outreach_status)

    if enrichment_status:
        query += ' AND enrichment_status = ?'
        params.append(enrichment_status)

    if has_email is not None:
        if has_email:
            query += ' AND email_address IS NOT NULL AND email_address != ""'
        else:
            query += ' AND (email_address IS NULL OR email_address = "")'

    if search:
        query += ' AND business_name LIKE ?'
        params.append(f'%{search}%')

    if date_from:
        query += ' AND filing_date >= ?'
        params.append(date_from)

    if date_to:
        query += ' AND filing_date <= ?'
        params.append(date_to)

    query += ' ORDER BY discovered_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_llc_count(outreach_status=None, enrichment_status=None, has_email=None):
    """Get count of LLCs matching filters."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = 'SELECT COUNT(*) FROM llcs WHERE 1=1'
    params = []

    if outreach_status:
        query += ' AND outreach_status = ?'
        params.append(outreach_status)

    if enrichment_status:
        query += ' AND enrichment_status = ?'
        params.append(enrichment_status)

    if has_email is not None:
        if has_email:
            query += ' AND email_address IS NOT NULL AND email_address != ""'
        else:
            query += ' AND (email_address IS NULL OR email_address = "")'

    cursor.execute(query, params)
    result = cursor.fetchone()[0]
    conn.close()
    return result


def update_llc_enrichment(llc_id, website_url=None, has_website=0,
                          email_address=None, phone=None, enrichment_status='enriched',
                          enrichment_notes=None):
    """Update enrichment fields for an LLC."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE llcs SET
            website_url = ?, has_website = ?, email_address = ?, phone = ?,
            enrichment_status = ?, enriched_at = CURRENT_TIMESTAMP, enrichment_notes = ?
        WHERE id = ?
    ''', (website_url, has_website, email_address, phone, enrichment_status,
          enrichment_notes, llc_id))
    conn.commit()
    conn.close()


def update_llc_outreach_status(llc_id, status, skip_reason=None):
    """Update outreach status for an LLC."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if status == 'approved':
        cursor.execute('''
            UPDATE llcs SET outreach_status = ?, approved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, llc_id))
    elif status == 'sent':
        cursor.execute('''
            UPDATE llcs SET outreach_status = ?, emailed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, llc_id))
    elif status == 'skipped':
        cursor.execute('''
            UPDATE llcs SET outreach_status = ?, skip_reason = ?
            WHERE id = ?
        ''', (status, skip_reason, llc_id))
    else:
        cursor.execute('UPDATE llcs SET outreach_status = ? WHERE id = ?', (status, llc_id))

    conn.commit()
    conn.close()


def get_pending_enrichment(limit=20):
    """Get LLCs pending enrichment."""
    return get_llcs(limit=limit, enrichment_status='pending')


def get_approved_for_email(limit=20):
    """Get LLCs approved for outreach that haven't been emailed."""
    return get_llcs(limit=limit, outreach_status='approved')


# --- Email Log ---

def log_email_sent(llc_id, to_address, subject, status='sent', error_message=None):
    """Log an email send attempt."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO email_log (llc_id, to_address, subject, status, error_message)
        VALUES (?, ?, ?, ?, ?)
    ''', (llc_id, to_address, subject, status, error_message))
    conn.commit()
    conn.close()


def get_email_history(limit=50):
    """Get email send history with LLC info."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.*, l.business_name, l.filing_number
        FROM email_log e
        JOIN llcs l ON e.llc_id = l.id
        ORDER BY e.sent_at DESC
        LIMIT ?
    ''', (limit,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_emails_sent_today():
    """Count emails sent today (for daily limit enforcement)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM email_log
        WHERE DATE(sent_at) = DATE('now') AND status = 'sent'
    ''')
    result = cursor.fetchone()[0]
    conn.close()
    return result


# --- Logs ---

def add_log(message, status='info'):
    """Add a log entry."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO logs (message, status) VALUES (?, ?)', (message, status))
    conn.commit()
    conn.close()


def get_logs(limit=50):
    """Get recent logs."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, message, status
        FROM logs
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    results = cursor.fetchall()
    conn.close()
    return results


# --- Stats ---

def get_stats():
    """Get dashboard statistics."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    stats = {}
    cursor.execute('SELECT COUNT(*) FROM llcs')
    stats['total_llcs'] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM llcs WHERE enrichment_status = 'pending'")
    stats['pending_enrichment'] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM llcs WHERE enrichment_status = 'enriched'")
    stats['enriched'] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM llcs WHERE outreach_status = 'pending'")
    stats['pending_outreach'] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM llcs WHERE outreach_status = 'approved'")
    stats['approved'] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM llcs WHERE outreach_status = 'sent'")
    stats['emails_sent'] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM llcs WHERE outreach_status = 'skipped'")
    stats['skipped'] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM llcs WHERE has_website = 1")
    stats['have_website'] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM llcs WHERE email_address IS NOT NULL AND email_address != ''")
    stats['have_email'] = cursor.fetchone()[0]

    cursor.execute('''
        SELECT COUNT(*) FROM email_log
        WHERE DATE(sent_at) = DATE('now') AND status = 'sent'
    ''')
    stats['emails_today'] = cursor.fetchone()[0]

    conn.close()
    return stats
