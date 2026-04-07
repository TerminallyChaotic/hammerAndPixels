-- NOTE: SQLite doesn't support IF NOT EXISTS for ALTER TABLE ADD COLUMN.
-- Idempotency is handled by the migration runner catching "already exists" errors.
-- Running this file twice is safe because the runner skips columns that exist.
--
-- Add columns to existing llcs table for OpenClaw workflow
-- Note: Using SQLite syntax (INTEGER, DATETIME, DEFAULT) to match actual database
ALTER TABLE llcs ADD COLUMN status VARCHAR(50) DEFAULT 'new';
ALTER TABLE llcs ADD COLUMN openclaw_reviewed INTEGER DEFAULT 0;
ALTER TABLE llcs ADD COLUMN openclaw_approved_at DATETIME NULL;
ALTER TABLE llcs ADD COLUMN approved_by_user INTEGER DEFAULT 0;
ALTER TABLE llcs ADD COLUMN user_approved_at DATETIME NULL;
ALTER TABLE llcs ADD COLUMN sent INTEGER DEFAULT 0;
ALTER TABLE llcs ADD COLUMN sent_at DATETIME NULL;

-- Create review log table for audit trail
CREATE TABLE IF NOT EXISTS openclaw_review_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    llc_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    notes TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (llc_id) REFERENCES llcs(id) ON DELETE CASCADE
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_llcs_status ON llcs(status);
CREATE INDEX IF NOT EXISTS idx_llcs_openclaw_reviewed ON llcs(openclaw_reviewed);
CREATE INDEX IF NOT EXISTS idx_review_log_llc ON openclaw_review_log(llc_id);
CREATE INDEX IF NOT EXISTS idx_review_log_timestamp ON openclaw_review_log(timestamp);
