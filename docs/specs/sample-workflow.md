# Sample Local Workflow (V1)

## Prerequisites

- Node.js 22+
- dependencies installed with `npm install`
- local DB path configured via `DB_PATH` in `.env` (optional)
- to enable real Sheets writes, set:
  - `GOOGLE_SHEETS_ENABLED=true`
  - `GOOGLE_SHEETS_SPREADSHEET_ID=<sheet-id>`
  - `GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON=<json-or-path>`
- to enable OCR for image receipts, set:
  - `OCR_PROVIDER=tesseract`
  - `OCR_LANGUAGE=eng` (or preferred Tesseract language code)

## Typical Flow

1. Run migration bootstrap:
```bash
node --import tsx src/infra/db/migrate.ts
```

2. Import a statement or receipt text file:
```bash
node --import tsx src/cli/index.ts import src/fixtures/statements/bank-sample.csv bank_statement
node --import tsx src/cli/index.ts import src/fixtures/receipts/receipt-text.txt receipt_text
```

3. View current review queue:
```bash
node --import tsx src/cli/index.ts review list
```

4. Approve or adjust entries:
```bash
node --import tsx src/cli/index.ts review approve <entry-id>
node --import tsx src/cli/index.ts review edit-category <entry-id> groceries
node --import tsx src/cli/index.ts review mark-duplicate <entry-id> <related-entry-id>
```

5. Sync exports:
```bash
node --import tsx src/cli/index.ts export
node --import tsx src/cli/index.ts summary
```

## Expected V1 Behavior

- uncertain records route to review instead of silent approval
- exact duplicate imports are detected through fingerprint matching
- near-duplicates are flagged for review, not auto-merged
- recurring patterns are tracked for summary, not auto-marked as duplicates

## Current V1 Limits

- OCR for low-quality images can still produce uncertain extraction and review routing
- Google Sheets writes require explicit env configuration and service account access
- CSV parsing is generic but not yet bank-provider specific
