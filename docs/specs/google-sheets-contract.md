# Google Sheets Contract (V1)

## Role of Sheets

Google Sheets is an export and review surface. It is not the system of record.

Local SQLite remains canonical for entries, mappings, fingerprints, and audit events.

## Tabs

- `raw_imports`
- `normalized_entries`
- `review_queue`
- `mapping_rules`
- `monthly_summary`

## normalized_entries Columns

- `entry_id`
- `source_type`
- `document_id`
- `merchant_name`
- `transaction_date`
- `posting_date`
- `amount`
- `currency`
- `base_currency_amount`
- `suggested_category`
- `final_category`
- `confidence`
- `duplicate_status`
- `status`
- `review_reasons`
- `export_timestamp`

Export rule:

- only `approved` entries sync
- entries with `exact_duplicate_import` do not sync as active rows
- upsert key is `entry_id`

## review_queue Columns

- `entry_id`
- `issue_type`
- `merchant`
- `amount`
- `currency`
- `suggested_category`
- `rationale`
- `duplicate_signals`
- `reviewer_status`

Export rule:

- only `needs_review` entries sync
- upsert key is `entry_id`

## monthly_summary Columns

- `month`
- `metric_type`
- `metric_key`
- `metric_value`

Export rule:

- summary values derive from approved entries only
- upsert key is `metric_key`

## Idempotency

All sheet writes must use idempotent upsert behavior keyed by stable internal IDs.
