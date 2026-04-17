CREATE TABLE IF NOT EXISTS extracted_candidates (
  candidate_id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL,
  source_type TEXT NOT NULL,
  entry_id TEXT,
  merchant_raw TEXT,
  description_raw TEXT,
  reference_raw TEXT,
  transaction_date_raw TEXT,
  posting_date_raw TEXT,
  amount_raw TEXT,
  currency_raw TEXT,
  tax_amount_raw TEXT,
  line_items_json TEXT NOT NULL DEFAULT '[]',
  confidence REAL NOT NULL,
  warnings_json TEXT NOT NULL DEFAULT '[]',
  raw_text TEXT,
  raw_row_json TEXT,
  extractor_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(document_id) REFERENCES source_documents(document_id),
  FOREIGN KEY(entry_id) REFERENCES normalized_entries(entry_id)
);

CREATE INDEX IF NOT EXISTS idx_extracted_candidates_document_id
  ON extracted_candidates(document_id);

CREATE INDEX IF NOT EXISTS idx_extracted_candidates_entry_id
  ON extracted_candidates(entry_id);
