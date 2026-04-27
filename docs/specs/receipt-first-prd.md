# PRD: Receipt-First Finance Ingestion Tool

## 1. Product Summary

Build a receipt-first personal finance ingestion tool using a Python backend and a Next.js frontend.

The app lets users upload receipts as soon as they spend money, creates provisional spending records, and gives early monthly spending analysis. Later, when bank or card statements become available, the system imports those statements and reconciles them against the provisional receipt-based records to confirm, correct, or deduplicate spending.

Core idea:

```text
Receipts provide early spending visibility.
Statements provide later financial truth.
```

## 2. Product Goal

The system should answer:

> Can I understand my spending now from receipts, and later reconcile it cleanly against bank or card statements without creating duplicates?

The tool should support:

- receipt text import
- bank or card statement CSV import
- receipt-based provisional expenses
- statement-confirmed transactions
- receipt-to-statement matching
- category rules
- review queue
- monthly summary
- CSV export
- optional AI and OCR extraction in later phases

## 3. Product Principle

Receipts create provisional spending events. Statements confirm or correct them later.

This avoids two weak models:

- Statement-only: users cannot analyze spending until statements arrive.
- Receipt-only: users may double-count once statement rows arrive.

Preferred model:

```text
Receipt arrives first
-> create receipt evidence
-> create provisional spending event
-> include it in fast spending analysis

Statement arrives later
-> create statement evidence
-> match it to the existing event
-> confirm, correct, or route to review
```

## 4. Target User

A user who wants to track personal spending from messy real-world inputs:

- grocery receipts
- restaurant receipts
- online purchase receipts
- bank or card CSV exports
- occasional manual entries

They want quick visibility now, then cleaner final numbers later.

## 5. Non-Goals For V1

Do not build:

- full accounting
- tax filing
- bank OAuth integration
- Plaid-style live bank sync
- multi-user auth
- full budgeting
- invoice or payment workflows
- mobile app
- complex double-entry ledger
- Google Sheets sync

This is an ingestion, reconciliation, and analysis tool, not a complete finance platform.

## 6. Target Stack

Backend:

- Python 3.12
- FastAPI for API
- Pydantic for schemas and structured validation
- SQLAlchemy 2.0 for ORM
- Alembic for migrations
- PostgreSQL for the main version
- SQLite acceptable for local prototype and tests
- Typer for CLI commands
- Polars or Pandas for CSV processing
- RapidFuzz for merchant similarity
- python-dateutil for date parsing

Frontend:

- Next.js
- React
- TypeScript
- Tailwind
- TanStack Query
- shadcn/ui if it fits the project style

Reference implementation:

- The existing TypeScript implementation in this repository is a product learning and fixture source.
- Reuse its concepts for adapters, mapping rules, OCR boundaries, summaries, and tests where useful.
- The new target architecture is Python/FastAPI plus Next.js.

Later optional services:

- Redis plus RQ for background jobs
- OCR for receipt images
- AI extraction using structured JSON output
- Google Sheets API export

## 7. High-Level Architecture

```text
Frontend or CLI
-> Import API
-> Source document storage
-> Extraction adapter
-> Evidence record
-> Spending event creation or update
-> Categorization
-> Receipt to statement reconciliation
-> Review queue
-> Summary and CSV export
```

The most important architectural split is:

```text
SourceDocument = raw uploaded input
EvidenceRecord = extracted fact from one source
SpendingEvent = canonical spending object used for analysis
EvidenceLink = connection between evidence and event
```

## 8. Core Concepts

### 8.1 Source Document

The raw uploaded input.

Examples:

- receipt text
- receipt image
- bank CSV
- card CSV
- manually pasted receipt

Rule:

- Always preserve raw source input so parsing can be rerun later.

```ts
type SourceDocument = {
  id: string;
  sourceType: "receipt_text" | "receipt_image" | "bank_csv" | "card_csv" | "manual";
  filename?: string;
  rawText?: string;
  filePath?: string;
  status: "uploaded" | "parsed" | "failed";
  createdAt: string;
};
```

### 8.2 Evidence Record

An extracted record from a source document.

A receipt and a statement row are both evidence. Evidence values are immutable source facts for audit purposes. Canonical spending event values may change later, but the original evidence remains preserved.

```ts
type EvidenceRecord = {
  id: string;
  sourceDocumentId: string;

  evidenceType: "receipt" | "statement_row" | "manual_entry";

  merchantRaw?: string;
  merchantNormalized?: string;

  occurredAt?: string;
  postedAt?: string;

  amountMinor?: number;
  currency?: string;

  descriptionRaw?: string;

  extractionConfidence: number;
  fingerprint: string;
  rawPayloadJson?: string;
  warnings: string[];

  createdAt: string;
};
```

### 8.3 Spending Event

The canonical thing used for analysis.

A spending event may be:

- receipt-only
- statement-only
- receipt plus statement
- manual

Status is intentionally split into separate dimensions. Do not compress these into one overloaded field.

```ts
type SpendingEvent = {
  id: string;

  occurredAt: string;
  postedAt?: string;
  merchantNormalized: string;

  amountMinor: number;
  currency: string;

  direction: "expense" | "income" | "transfer";

  categoryId?: string;

  confirmationStatus: "provisional" | "confirmed" | "manual_confirmed";
  reviewStatus: "clear" | "needs_review" | "resolved";
  lifecycleStatus: "active" | "duplicate" | "ignored";

  sourceQuality:
    | "receipt_only"
    | "statement_only"
    | "receipt_and_statement"
    | "manual";

  canonicalSourceEvidenceId?: string;

  createdAt: string;
  updatedAt: string;
};
```

### 8.4 Evidence Link

Connects evidence records to spending events.

This is what prevents duplicate spending when a receipt arrives first and a statement row arrives later.

```ts
type EvidenceLink = {
  id: string;

  spendingEventId: string;
  evidenceRecordId: string;

  linkType:
    | "created_from"
    | "matched_to"
    | "supporting_receipt"
    | "statement_confirmation";

  matchScore?: number;

  status: "suggested" | "confirmed" | "rejected";

  createdAt: string;
  updatedAt: string;
};
```

### 8.5 Match Candidate

A proposed receipt-to-statement or evidence-to-event match.

```ts
type MatchCandidate = {
  id: string;
  spendingEventId: string;
  evidenceRecordId: string;
  score: number;
  signals: string[];
  status: "suggested" | "auto_confirmed" | "confirmed" | "rejected";
  createdAt: string;
  resolvedAt?: string;
};
```

## 9. Statement-Backed Truth

Statements are the stronger source for final financial truth, but they do not erase receipt evidence.

Rules:

- Receipt extraction values remain preserved on `EvidenceRecord`.
- Statement row extraction values remain preserved on `EvidenceRecord`.
- When matched, statement evidence may update canonical `SpendingEvent` fields:
  - `amountMinor`
  - `postedAt`
  - `merchantNormalized`
  - `confirmationStatus`
  - `sourceQuality`
  - `canonicalSourceEvidenceId`
- Never overwrite, delete, or mutate the original receipt evidence to make it look like the statement.
- Any material mismatch between receipt and statement values should be visible in event detail and review.

Example:

```text
Receipt evidence:
merchantRaw = "Aldi"
occurredAt = 2026-04-17
amountMinor = 4297

Statement evidence:
merchantRaw = "ALDI BE"
postedAt = 2026-04-18
amountMinor = 4297

Spending event after match:
merchantNormalized = "Aldi"
occurredAt = 2026-04-17
postedAt = 2026-04-18
amountMinor = 4297
confirmationStatus = confirmed
sourceQuality = receipt_and_statement
```

## 10. Main User Flows

### Flow 1: Import Receipt First

User uploads or pastes receipt text.

System:

1. stores a source document
2. extracts merchant, date, total, and currency
3. creates a receipt evidence record
4. creates a provisional spending event
5. links evidence to event with `created_from`
6. categorizes if deterministic rules apply
7. routes uncertainty to review
8. includes the event in fast monthly analysis

Example:

```text
Receipt: Aldi, Apr 17, EUR 42.97

SpendingEvent:
merchantNormalized = Aldi
amountMinor = 4297
confirmationStatus = provisional
reviewStatus = clear
lifecycleStatus = active
sourceQuality = receipt_only
category = groceries
```

### Flow 2: Import Statement Later

User uploads a card or bank statement CSV.

System:

1. stores a source document
2. parses statement rows
3. creates statement evidence records
4. matches each row against active provisional receipt events
5. auto-confirms high-confidence matches
6. creates statement-only confirmed events for unmatched rows
7. routes uncertain matches to review

Example:

```text
Statement row: ALDI BE, Apr 18, EUR 42.97
-> matches Aldi receipt event
-> creates confirmed evidence link
-> updates spending event to confirmed
-> updates sourceQuality to receipt_and_statement
```

### Flow 3: Receipt Has No Statement Match

An unmatched receipt is not necessarily bad data.

Possible reasons:

- cash purchase
- statement not imported yet
- paid by another account
- transaction grouped differently
- extraction error

Behavior:

- Receipt remains `confirmationStatus = provisional` by default.
- User can confirm it as a cash or manual expense.
- That sets `confirmationStatus = manual_confirmed` and `sourceQuality = manual`.
- Original receipt evidence remains linked and preserved.

### Flow 4: Statement Has No Receipt Match

Behavior:

- Statement row creates a confirmed statement-only spending event.
- The event is included in conservative and fast analysis.

Example:

```text
Netflix EUR 15.99
-> no receipt
-> confirmed event from statement
-> sourceQuality = statement_only
```

### Flow 5: Uncertain Match

Example:

```text
Receipt: EUR 42.97
Statement: EUR 43.00
Merchant similar
Date close
```

Behavior:

1. create `MatchCandidate`
2. create `ReviewItem`
3. user confirms or rejects
4. confirmed match links evidence and updates the event
5. rejected match stays recorded and does not affect the event

## 11. Analysis Modes

Monthly reports should support three modes.

Fast mode includes:

- confirmed events
- provisional receipt events
- manual-confirmed events

Use case:

> What have I probably spent this month so far?

Conservative mode includes:

- statement-confirmed events
- manually confirmed events

Use case:

> What is the safest final number?

Review mode shows:

- provisional receipt-only events
- possible duplicates
- uncertain matches
- missing categories
- parse warnings

Use case:

> What needs cleaning up?

## 12. Reconciliation Engine

Inputs:

- new evidence record
- existing active spending events
- existing evidence links
- existing match candidates

Matching signals:

- exact amount
- amount proximity
- same currency
- same date
- nearby date
- merchant similarity
- description similarity
- whether event is already statement-confirmed

Example scoring:

- `+50` exact amount match
- `+20` same date
- `+10` within 3 days
- `+20` high merchant similarity
- `+10` same currency
- `-30` amount mismatch
- `-40` already statement-confirmed

Thresholds:

- `score >= 80`: auto-confirm match
- `score 50-79`: suggest match and route to review
- `score < 50`: no match

Reconciliation must be safe to rerun. A second run should not create duplicate evidence links, duplicate match candidates, or duplicate events.

## 13. Categorization Engine

Use deterministic rules first.

Order:

1. user-defined merchant rule
2. description keyword rule
3. source-specific rule
4. AI category suggestion if enabled
5. review queue

```ts
type MappingRule = {
  id: string;
  pattern: string;
  patternType: "merchant" | "description" | "source";
  categoryId: string;
  priority: number;
  createdFromReview: boolean;
};
```

Examples:

- merchant contains `ALDI` -> groceries
- description contains `NETFLIX` -> subscriptions
- merchant contains `SNCB` -> transport

## 14. Review Queue

Review is first-class. The system should not hide uncertainty.

```ts
type ReviewReason =
  | "uncertain_category"
  | "possible_duplicate"
  | "possible_receipt_statement_match"
  | "amount_mismatch"
  | "unmatched_receipt"
  | "missing_required_field"
  | "parse_warning";
```

```ts
type ReviewItem = {
  id: string;
  entityType: "spending_event" | "evidence_record" | "match_candidate";
  entityId: string;
  reason: ReviewReason;
  details: string[];
  status: "open" | "resolved" | "ignored";
  createdAt: string;
  resolvedAt?: string;
};
```

User actions:

- confirm category
- change category
- confirm match
- reject match
- confirm receipt as cash or manual
- ignore item
- mark duplicate

## 15. Idempotency Requirements

Idempotency is a first-class product requirement.

Receipt re-import:

- Re-importing the same receipt should not create duplicate evidence records.
- Re-importing the same receipt should not create duplicate spending events.
- If the parser improves later, reprocessing should update derived canonical values through an explicit reprocess flow, not accidental duplicate import.

Statement re-import:

- Re-importing the same statement CSV should not create duplicate evidence records.
- Re-importing the same statement CSV should not create duplicate spending events.
- Re-importing the same statement CSV should not create duplicate match candidates.

Reconciliation rerun:

- Reconciliation should be safe to run repeatedly.
- Existing confirmed links should be reused.
- Existing rejected matches should not be recreated as new open review items without a material input change.
- Exact duplicate imports should be recorded for audit but should not create active exportable events.

Suggested enforcement:

- source document fingerprint
- evidence fingerprint
- unique constraints on source-specific row fingerprints
- unique constraints on evidence links by event and evidence IDs
- unique constraints on open match candidates by event and evidence IDs

## 16. Backend API

V1 should keep the API thin around the core model.

Imports:

- `POST /api/imports/receipt-text`
- `POST /api/imports/statement-csv`
- `GET /api/imports`
- `GET /api/imports/{id}`

Spending events:

- `GET /api/events?month=2026-04&mode=fast`
- `GET /api/events/{id}`
- `PATCH /api/events/{id}`
- `GET /api/events/{id}/evidence`

Evidence:

- `GET /api/evidence/{id}`

Review:

- `GET /api/review`
- `POST /api/review/{id}/resolve`
- `POST /api/review/{id}/ignore`

Reconciliation:

- `POST /api/reconcile`
- `GET /api/matches`
- `POST /api/matches/{id}/confirm`
- `POST /api/matches/{id}/reject`

Summaries and export:

- `GET /api/summary?month=2026-04&mode=fast`
- `POST /api/export/csv`

Google Sheets export is V2.

## 17. CLI Commands

The CLI is useful for development and demoing.

```bash
finance import receipt ./data/aldi.txt
finance import statement ./data/card.csv

finance events --month 2026-04 --mode fast
finance events --month 2026-04 --mode conservative

finance reconcile
finance review
finance summary --month 2026-04 --mode fast
finance export --month 2026-04 --format csv

finance evidence --event <event_id>
finance matches --event <event_id>
finance reprocess <source_document_id>
finance rules
```

## 18. Minimal UI Scope

The main implementation priority is proving the reconciliation model, not building a polished UI first.

V1 UI should be minimal and only arrive after the core model works.

Screens:

- import receipt text
- import one statement CSV profile
- spending events list
- event detail with linked evidence
- review queue
- monthly summary
- CSV export

Defer:

- highly polished dashboard
- receipt image OCR UI
- Google Sheets setup
- advanced filters
- mobile-specific flows

## 19. Data Model Tables

Minimum V1 tables:

- `source_documents`
- `evidence_records`
- `spending_events`
- `evidence_links`
- `match_candidates`
- `categories`
- `mapping_rules`
- `review_items`
- `import_runs`
- `exports`

Recommended V1 constraints:

- unique source document fingerprint
- unique evidence fingerprint
- unique active evidence link per spending event and evidence record
- unique open match candidate per spending event and evidence record
- no active export row for duplicate or ignored spending events

Optional V2 tables:

- `receipt_line_items`
- `parse_warnings`
- `audit_events`
- `ai_extraction_runs`
- `google_sheets_syncs`

## 20. AI And OCR Rules

AI and OCR are optional and bounded.

Environment flags:

```bash
ENABLE_AI_EXTRACTION=false
ENABLE_OCR=false
ENABLE_GOOGLE_SHEETS_SYNC=false
```

Good AI usage:

- extract receipt fields from messy text
- suggest merchant normalization
- suggest category
- explain why two records may match

Bad AI usage:

- silently confirm financial transactions
- overwrite raw values
- create final confirmed records without deterministic checks
- decide duplicates without score and review trail
- own status transitions

Principle:

```text
AI suggests. Deterministic code validates, scores, and routes to review.
```

## 21. Money Handling Rules

Use integer minor units.

Examples:

- `EUR 42.97` -> `4297`
- `EUR 10.00` -> `1000`

Avoid floats.

Store:

```ts
amountMinor: number;
currency: string;
```

Handle:

- EU decimal commas
- negative amounts
- debit and credit columns
- currency symbols
- whitespace
- thousands separators

## 22. Narrow V1 Scope

V1 is a receipt-first local finance analyzer that proves the reconciliation model.

V1 includes:

- receipt text import
- one statement CSV profile
- source documents
- evidence records
- spending events
- evidence links
- reconciliation scoring
- category rules
- review queue
- monthly summary
- CSV export
- minimal UI only after the core model works

V1 excludes:

- Google Sheets
- OCR
- AI extraction
- multiple statement profiles
- bank sync
- polished dashboard
- receipt line-item accounting

## 23. V1 Acceptance Criteria

Receipt import:

- User can upload or paste receipt text.
- System extracts merchant, date, total, and currency.
- System creates a source document.
- System creates a receipt evidence record.
- System creates a provisional spending event.
- System links evidence to the event.
- Receipt-only events appear in fast monthly analysis.

Statement import:

- User can upload one supported bank or card CSV format.
- System parses statement rows.
- System creates statement evidence records.
- Unmatched rows create confirmed statement-only spending events.
- Candidate matches are created against provisional receipt events.

Reconciliation:

- Exact amount, date, merchant, and currency matches are auto-confirmed.
- Medium-confidence matches go to review.
- Confirmed matches do not duplicate spending.
- Statement evidence may update canonical spending event values.
- Original receipt evidence remains preserved.
- Event `confirmationStatus` and `sourceQuality` update correctly.

Cash or manual receipt flow:

- Unmatched receipts remain valid provisional expenses.
- User can confirm an unmatched receipt as a cash or manual expense.
- Manual confirmation sets `confirmationStatus = manual_confirmed`.
- Manual confirmation sets `sourceQuality = manual`.

Categorization:

- Merchant rules assign categories.
- Unknown categories go to review.
- User can correct category.
- Corrected category can create a future mapping rule.

Review:

- Review queue displays uncertain items.
- User can confirm or reject a match.
- User can mark a receipt as cash or manual.
- User can mark duplicate or ignored.

Summary:

- Fast mode includes provisional receipt events.
- Conservative mode includes confirmed and manual-confirmed events only.
- Category totals use active, non-duplicate, non-ignored events.
- CSV export works.

Idempotency:

- Re-importing the same receipt does not duplicate evidence or events.
- Re-importing the same statement CSV does not duplicate evidence, events, or matches.
- Reconciliation is safe to rerun.
- Duplicate imports are auditable but not active exportable spending.

UI:

- User can import receipt text.
- User can import the supported statement CSV.
- User can view spending events.
- User can resolve review items.
- User can see monthly summary.
- User can export CSV.

## 24. Implementation Order

### Phase 1: Python Backend Foundation

- FastAPI app
- Pydantic schemas
- SQLAlchemy models
- Alembic migrations
- categories seed data
- health endpoint
- Typer CLI skeleton

### Phase 2: Core Domain Model

- `SourceDocument`
- `EvidenceRecord`
- `SpendingEvent`
- `EvidenceLink`
- `MatchCandidate`
- `ReviewItem`
- idempotency fingerprints and constraints

### Phase 3: Receipt Text Import

- upload or paste receipt text
- deterministic receipt field extraction
- date and money normalization
- evidence record creation
- provisional spending event creation
- evidence link creation

### Phase 4: One Statement CSV Profile

- parse one known CSV format
- normalize rows
- create statement evidence records
- create statement-only events for unmatched rows

### Phase 5: Reconciliation

- scoring engine
- match candidates
- auto-confirm high-confidence matches
- review medium-confidence matches
- safe rerun behavior

### Phase 6: Review Flow

- review queue API
- confirm or reject match
- edit category
- confirm receipt as cash or manual
- mark duplicate or ignored

### Phase 7: Summary And CSV Export

- monthly category summary
- fast and conservative modes
- CSV export

### Phase 8: Minimal Next.js UI

- import pages
- events list
- event detail
- review page
- summary/export page

### Phase 9: V2 Enhancements

- OCR
- AI extraction
- Google Sheets sync
- multiple statement profiles
- receipt line items
- background jobs
- audit event UI

## 25. Suggested Folder Structure

Backend:

```text
backend/
  app/
    main.py
    api/
      routes_imports.py
      routes_events.py
      routes_review.py
      routes_summary.py
      routes_export.py
    core/
      config.py
      db.py
    models/
      source_document.py
      evidence_record.py
      spending_event.py
      evidence_link.py
      match_candidate.py
      review_item.py
      category.py
      mapping_rule.py
    schemas/
      imports.py
      events.py
      evidence.py
      review.py
      summary.py
    services/
      import_service.py
      receipt_parser.py
      statement_parser.py
      normalization.py
      categorization.py
      reconciliation.py
      review_service.py
      summary.py
      csv_export.py
    cli/
      main.py
  alembic/
  tests/
```

Frontend:

```text
frontend/
  app/
    imports/
    events/
    review/
    summary/
  components/
    UploadReceipt.tsx
    UploadStatement.tsx
    EventTable.tsx
    ReviewItemCard.tsx
    SummaryCards.tsx
    EvidencePanel.tsx
  lib/
    api.ts
    types.ts
```

## 26. Portfolio Positioning

Strong one-liner:

> I built a receipt-first finance ingestion tool using Python and Next.js. Receipts create provisional spending events so users can analyze spending immediately, and bank or card statements later reconcile against those events to confirm or correct them. The architecture separates raw sources, extracted evidence, canonical spending events, and reviewable matches, which prevents duplicate spending while still supporting early analysis.

Technical talking points:

- Python ingestion pipeline
- FastAPI API layer
- Pydantic schema validation
- SQLAlchemy data model
- adapter-based parsing
- canonical spending event model
- evidence-based reconciliation
- provisional versus confirmed state model
- idempotency and fingerprints
- deterministic rules before AI
- review queue for uncertain cases
- Next.js UI for review and summaries
- CSV export

## 27. Why This Is A Strong Project

This demonstrates:

- backend architecture
- data modeling
- real-world ambiguity handling
- reconciliation logic
- review workflows
- product thinking
- AI-bounded system design
- Python plus TypeScript full-stack execution
- financial data correctness concerns

The project is not just uploading a CSV. It is a small but realistic data pipeline with uncertainty, delayed confirmation, and user review.
