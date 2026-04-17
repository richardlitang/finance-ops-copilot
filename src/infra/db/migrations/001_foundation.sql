CREATE TABLE IF NOT EXISTS source_documents (
  document_id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  filename TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  imported_at TEXT NOT NULL,
  locale_hint TEXT,
  country_hint TEXT,
  source_hint TEXT,
  raw_text TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS normalized_entries (
  entry_id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL,
  merchant_raw TEXT,
  merchant_normalized TEXT,
  description TEXT,
  reference TEXT,
  transaction_date TEXT,
  posting_date TEXT,
  amount REAL NOT NULL,
  currency TEXT NOT NULL,
  base_amount REAL,
  base_currency TEXT,
  tax_amount REAL,
  line_items_json TEXT NOT NULL,
  category_decision_json TEXT NOT NULL,
  duplicate_check_json TEXT NOT NULL,
  status TEXT NOT NULL,
  review_reasons_json TEXT NOT NULL,
  extraction_meta_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (document_id) REFERENCES source_documents (document_id)
);

CREATE TABLE IF NOT EXISTS mapping_rules (
  rule_id TEXT PRIMARY KEY,
  field TEXT NOT NULL,
  pattern TEXT NOT NULL,
  target_category TEXT NOT NULL,
  priority INTEGER NOT NULL,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
  event_id TEXT PRIMARY KEY,
  entry_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_at TEXT NOT NULL,
  actor TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS import_fingerprints (
  fingerprint TEXT PRIMARY KEY,
  entry_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS export_records (
  export_id TEXT PRIMARY KEY,
  entry_id TEXT NOT NULL,
  destination TEXT NOT NULL,
  exported_at TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_entries_document_id ON normalized_entries (document_id);
CREATE INDEX IF NOT EXISTS idx_entries_status ON normalized_entries (status);
CREATE INDEX IF NOT EXISTS idx_audit_events_entry_id ON audit_events (entry_id);
