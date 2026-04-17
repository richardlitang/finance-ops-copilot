# Feature: Finance Ops Copilot V1

## Goal

Build a local-first ingestion pipeline that converts receipts and statements into one canonical entry model, routes uncertain items to review, prevents duplicate pollution, and syncs approved rows to Google Sheets.

## Architecture Overview

V1 should ship as a single TypeScript service with SQLite as the local source of truth, strict schema validation at every boundary, and thin adapters around OCR, LLM suggestion, and Google Sheets side effects. The canonical model and deterministic review pipeline are the product, so adapters stay narrow and all status, math, duplicate, and export logic stays inside local code.

The initial execution shape should be library-first plus a thin CLI entrypoint. That keeps the core reusable for a later MCP surface or local UI without forcing route-handler complexity into V1.

## Assumptions

- Primary implementation language: TypeScript
- Runtime: Node.js 22+
- Local database: SQLite
- Validation: Zod
- Tests: Vitest
- Statement ingestion starts with CSV-first support
- Receipt support starts with text and image inputs, with OCR behind a dedicated port
- Google Sheets is an export and review surface, not the canonical store

## Proposed Repo Layout

```text
docs/
  index.md
  specs/
  plans/
    active/
    completed/
src/
  cli/
  app/
  domain/
  adapters/
    receipt/
    statement/
    sheets/
    llm/
  infra/
    db/
    files/
  fixtures/
tests/
```

## Tech Stack

- TypeScript
- Node.js
- `zod`
- `better-sqlite3`
- `vitest`
- `csv-parse`
- `googleapis`
- `tesseract.js` for local receipt OCR, only behind a port
- `pdf-parse` for bounded receipt PDF text extraction

## Execution Strategy

Build in this order:

1. repository and tooling skeleton
2. canonical schemas and domain rules
3. local persistence and audit trail
4. intake plus source adapters
5. duplicate, categorization, and review engines
6. Sheets sync and summary generation
7. end-to-end fixtures and operational docs

## Human Checkpoints

Pause for review after:

1. foundation and schema slice
2. ingestion plus duplicate slice
3. Sheets plus summary slice
4. end-to-end fixture coverage slice

## Tasks

### Task 1: Bootstrap project tooling

**Files:**
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `vitest.config.ts`
- Create: `.gitignore`
- Create: `.env.example`

**Action:** Create the TypeScript workspace with scripts for `build`, `test`, `typecheck`, `lint`, and `dev`, and include environment keys for SQLite path, Google Sheets IDs, and optional LLM configuration.

**Verify:**
```bash
npm install
npm run typecheck
```

**Commit:** `chore(repo): bootstrap typescript workspace`

---

### Task 2: Create docs and top-level runbook skeleton

**Files:**
- Create: `README.md`
- Create: `docs/specs/README.md`
- Create: `docs/tech-debt.md`

**Action:** Document repo purpose, local-first constraint, planned commands, and where schema, plans, and debt logs live.

**Verify:**
```bash
test -f README.md && test -f docs/specs/README.md && test -f docs/tech-debt.md
```

**Commit:** `docs(repo): add initial runbook and doc skeleton`

---

### Task 3: Define canonical category and status enums

**Files:**
- Create: `src/domain/enums.ts`

**Action:** Export the canonical V1 categories, source types, duplicate states, entry statuses, review reasons, and suggestion sources as `as const` arrays plus inferred TypeScript union types.

**Verify:**
```bash
npm run typecheck
```

**Commit:** `feat(domain): add canonical enums for entries and review flow`

---

### Task 4: Define canonical entity schemas

**Files:**
- Create: `src/domain/schemas.ts`

**Action:** Implement Zod schemas for `SourceDocumentRef`, `ExtractionMeta`, `CategoryDecision`, `DuplicateCheckResult`, `AuditEvent`, `MappingRule`, and `NormalizedEntry`. Include explicit IDs, provenance fields, normalized and raw value fields, confidence, warnings, and review reasons.

**Verify:**
```bash
npm run typecheck
```

**Commit:** `feat(domain): add canonical zod schemas`

---

### Task 5: Add schema contract tests

**Files:**
- Create: `tests/domain/schemas.test.ts`

**Action:** Add tests that validate a minimal valid `NormalizedEntry`, reject missing required fields, and ensure exact duplicate entries cannot be marked `approved` without a review-safe duplicate state.

**Verify:**
```bash
npm test -- tests/domain/schemas.test.ts
```

**Commit:** `test(domain): add canonical schema contract coverage`

---

### Task 6: Add deterministic review and state transition policy

**Files:**
- Create: `src/domain/review-policy.ts`
- Create: `tests/domain/review-policy.test.ts`

**Action:** Implement pure functions that derive `normalized`, `needs_review`, or `approved` from required field presence, confidence thresholds, duplicate state, and category certainty. Keep auto-approval rules narrow and explicit.

**Verify:**
```bash
npm test -- tests/domain/review-policy.test.ts
```

**Commit:** `feat(review): add deterministic status transition policy`

---

### Task 7: Add duplicate fingerprint helpers

**Files:**
- Create: `src/domain/fingerprints.ts`
- Create: `tests/domain/fingerprints.test.ts`

**Action:** Implement import fingerprint generation from institution, account suffix, raw date, raw description, raw amount, and raw reference. Test that exact same source rows produce identical fingerprints and small changes alter the value.

**Verify:**
```bash
npm test -- tests/domain/fingerprints.test.ts
```

**Commit:** `feat(duplicates): add import fingerprint generator`

---

### Task 8: Create SQLite bootstrap and migrations runner

**Files:**
- Create: `src/infra/db/client.ts`
- Create: `src/infra/db/migrate.ts`
- Create: `src/infra/db/migrations/001_foundation.sql`

**Action:** Add SQLite connection helpers and the initial schema for source documents, normalized entries, mapping rules, audit events, fingerprints, and export records.

**Verify:**
```bash
npm run typecheck
node --import tsx src/infra/db/migrate.ts
```

**Commit:** `feat(db): add sqlite foundation schema`

---

### Task 9: Add repository layer for core entities

**Files:**
- Create: `src/infra/db/document-repo.ts`
- Create: `src/infra/db/entry-repo.ts`
- Create: `src/infra/db/mapping-rule-repo.ts`
- Create: `src/infra/db/audit-repo.ts`
- Create: `tests/infra/db/repos.test.ts`

**Action:** Implement CRUD helpers for documents, entries, mappings, and audit events. Repositories should accept and return canonical domain shapes, not raw SQL row blobs.

**Verify:**
```bash
npm test -- tests/infra/db/repos.test.ts
```

**Commit:** `feat(db): add repositories for core entities`

---

### Task 10: Add import intake service

**Files:**
- Create: `src/app/intake-service.ts`
- Create: `src/infra/files/file-ingest.ts`
- Create: `tests/app/intake-service.test.ts`

**Action:** Implement import creation with document ID, filename, mime type, import timestamp, optional source hint, and locale hints. Persist the raw file metadata and optional text payload reference.

**Verify:**
```bash
npm test -- tests/app/intake-service.test.ts
```

**Commit:** `feat(intake): record imported documents with provenance`

---

### Task 11: Add source classification heuristics

**Files:**
- Create: `src/app/source-classifier.ts`
- Create: `tests/app/source-classifier.test.ts`

**Action:** Classify inputs as receipt, bank statement, or credit card statement using explicit hints, mime type, filename heuristics, and row-shape clues. Return confidence and rationale. Leave an extension point for LLM fallback without calling it yet.

**Verify:**
```bash
npm test -- tests/app/source-classifier.test.ts
```

**Commit:** `feat(classifier): add deterministic source classification`

---

### Task 12: Add statement CSV parser primitives

**Files:**
- Create: `src/adapters/statement/csv-parser.ts`
- Create: `tests/adapters/statement/csv-parser.test.ts`

**Action:** Parse CSV input into raw rows with header normalization, delimiter tolerance, and preservation of raw field values. Keep this generic and provider-agnostic.

**Verify:**
```bash
npm test -- tests/adapters/statement/csv-parser.test.ts
```

**Commit:** `feat(statement): add generic csv parser`

---

### Task 13: Add bank statement adapter

**Files:**
- Create: `src/adapters/statement/bank-statement-adapter.ts`
- Create: `tests/adapters/statement/bank-statement-adapter.test.ts`
- Create: `src/fixtures/statements/bank-sample.csv`

**Action:** Map raw CSV rows into candidate transaction shapes with raw amount, raw currency, date fields, merchant or payee hints, and raw description preserved.

**Verify:**
```bash
npm test -- tests/adapters/statement/bank-statement-adapter.test.ts
```

**Commit:** `feat(statement): add bank csv adapter`

---

### Task 14: Add credit card statement adapter

**Files:**
- Create: `src/adapters/statement/credit-card-adapter.ts`
- Create: `tests/adapters/statement/credit-card-adapter.test.ts`
- Create: `src/fixtures/statements/credit-card-sample.csv`

**Action:** Reuse the CSV parser and implement card-specific extraction rules, especially around posting date, transaction date, reference text, fees, and payment or transfer rows.

**Verify:**
```bash
npm test -- tests/adapters/statement/credit-card-adapter.test.ts
```

**Commit:** `feat(statement): add credit card csv adapter`

---

### Task 15: Add receipt text extraction port

**Files:**
- Create: `src/adapters/receipt/receipt-text-port.ts`
- Create: `src/adapters/receipt/receipt-text-adapter.ts`
- Create: `tests/adapters/receipt/receipt-text-adapter.test.ts`
- Create: `src/fixtures/receipts/receipt-text.txt`

**Action:** Support pre-extracted text input for receipt parsing and produce candidate merchant, date, amount, tax, currency, and optional line items with confidence and warnings.

**Verify:**
```bash
npm test -- tests/adapters/receipt/receipt-text-adapter.test.ts
```

**Commit:** `feat(receipts): add text-first receipt adapter`

---

### Task 16: Add local OCR-backed receipt image adapter

**Files:**
- Create: `src/adapters/receipt/ocr-port.ts`
- Create: `src/adapters/receipt/tesseract-ocr.ts`
- Create: `src/adapters/receipt/receipt-image-adapter.ts`
- Create: `tests/adapters/receipt/receipt-image-adapter.test.ts`

**Action:** Add a port-backed OCR implementation using `tesseract.js` and route JPG or PNG receipts through OCR before the receipt text adapter. Keep OCR errors review-safe and never auto-approve on weak OCR output.

**Verify:**
```bash
npm test -- tests/adapters/receipt/receipt-image-adapter.test.ts
```

**Commit:** `feat(receipts): add local ocr receipt adapter`

---

### Task 17: Add normalization helpers

**Files:**
- Create: `src/app/normalize-entry.ts`
- Create: `tests/app/normalize-entry.test.ts`

**Action:** Normalize dates, parse signed amounts, standardize currencies for PHP, USD, and EUR, normalize merchant text, and convert adapter candidates into `NormalizedEntry` records with extraction metadata attached.

**Verify:**
```bash
npm test -- tests/app/normalize-entry.test.ts
```

**Commit:** `feat(normalization): add canonical entry normalization`

---

### Task 18: Add mapping rule engine

**Files:**
- Create: `src/app/mapping-rule-engine.ts`
- Create: `tests/app/mapping-rule-engine.test.ts`

**Action:** Apply persistent rules in priority order against merchant, description, and line-item fields, and return suggested category plus rationale and source metadata.

**Verify:**
```bash
npm test -- tests/app/mapping-rule-engine.test.ts
```

**Commit:** `feat(categorization): add mapping rule engine`

---

### Task 19: Add LLM suggestion port and fallback categorizer

**Files:**
- Create: `src/adapters/llm/llm-port.ts`
- Create: `src/app/category-suggester.ts`
- Create: `tests/app/category-suggester.test.ts`

**Action:** Define a narrow LLM interface that accepts sanitized transaction context and returns category suggestion, confidence, and rationale. Only call it when mapping rules fail or confidence is low.

**Verify:**
```bash
npm test -- tests/app/category-suggester.test.ts
```

**Commit:** `feat(categorization): add bounded llm fallback port`

---

### Task 20: Add exact and near-duplicate engine

**Files:**
- Create: `src/app/duplicate-engine.ts`
- Create: `tests/app/duplicate-engine.test.ts`

**Action:** Combine import fingerprints for exact duplicates with explainable near-duplicate scoring on amount, normalized merchant, date tolerance, account context, and similar description. Exact duplicates block active export rows, near-duplicates go to review.

**Verify:**
```bash
npm test -- tests/app/duplicate-engine.test.ts
```

**Commit:** `feat(duplicates): add exact and near-duplicate evaluation`

---

### Task 21: Add validation and review router

**Files:**
- Create: `src/app/review-router.ts`
- Create: `tests/app/review-router.test.ts`

**Action:** Compose normalization, duplicate signals, extraction confidence, and category confidence into final review reasons and entry status. Preserve every rationale and warning for the audit layer and Sheets export.

**Verify:**
```bash
npm test -- tests/app/review-router.test.ts
```

**Commit:** `feat(review): add review routing service`

---

### Task 22: Add audit event writer

**Files:**
- Create: `src/app/audit-service.ts`
- Create: `tests/app/audit-service.test.ts`

**Action:** Record audit events for import, classification, extraction, normalization, duplicate detection, review state changes, approval, and export. Keep payloads privacy-aware and structured.

**Verify:**
```bash
npm test -- tests/app/audit-service.test.ts
```

**Commit:** `feat(audit): add structured audit logging`

---

### Task 23: Add Google Sheets contract and sync service

**Files:**
- Create: `src/adapters/sheets/sheets-contract.ts`
- Create: `src/adapters/sheets/google-sheets-service.ts`
- Create: `tests/adapters/sheets/google-sheets-service.test.ts`

**Action:** Define the tab schemas for `raw_imports`, `normalized_entries`, `review_queue`, `mapping_rules`, and `monthly_summary`. Implement idempotent writes keyed by internal IDs and approved status.

**Verify:**
```bash
npm test -- tests/adapters/sheets/google-sheets-service.test.ts
```

**Commit:** `feat(sheets): add idempotent google sheets sync`

---

### Task 24: Add monthly summary service

**Files:**
- Create: `src/app/monthly-summary-service.ts`
- Create: `tests/app/monthly-summary-service.test.ts`

**Action:** Aggregate approved entries into category totals, merchant totals, currency totals, recurring merchant candidates, and unmatched or uncategorized counts.

**Verify:**
```bash
npm test -- tests/app/monthly-summary-service.test.ts
```

**Commit:** `feat(summary): add monthly summary aggregation`

---

### Task 25: Add import pipeline orchestrator

**Files:**
- Create: `src/app/import-pipeline.ts`
- Create: `tests/app/import-pipeline.test.ts`

**Action:** Wire intake, classification, adapter selection, normalization, duplicate evaluation, categorization, review routing, persistence, and audit writing into one deterministic pipeline.

**Verify:**
```bash
npm test -- tests/app/import-pipeline.test.ts
```

**Commit:** `feat(pipeline): orchestrate end-to-end import flow`

---

### Task 26: Add thin CLI commands

**Files:**
- Create: `src/cli/index.ts`
- Create: `src/cli/commands/import.ts`
- Create: `src/cli/commands/review.ts`
- Create: `src/cli/commands/export.ts`
- Create: `src/cli/commands/summary.ts`

**Action:** Add thin command wrappers for importing files, listing review items, approving entries, exporting approved rows, and generating monthly summaries. Keep business logic in `src/app`.

**Verify:**
```bash
node --import tsx src/cli/index.ts --help
```

**Commit:** `feat(cli): add operational commands for v1 workflow`

---

### Task 27: Add review queue repository and approval operations

**Files:**
- Create: `src/app/review-service.ts`
- Create: `tests/app/review-service.test.ts`

**Action:** Support list, approve, edit category, mark duplicate, ignore duplicate warning, and reject or archive malformed entries. Every mutation should emit an audit event.

**Verify:**
```bash
npm test -- tests/app/review-service.test.ts
```

**Commit:** `feat(review): add review queue mutation service`

---

### Task 28: Add fixture-driven end-to-end tests

**Files:**
- Create: `tests/e2e/receipt-and-statement-ingestion.test.ts`
- Create: `tests/fixtures/`

**Action:** Add one receipt flow and one statement flow that prove both sources normalize into the same schema, produce review-safe statuses, and persist audit history.

**Verify:**
```bash
npm test -- tests/e2e/receipt-and-statement-ingestion.test.ts
```

**Commit:** `test(e2e): cover receipt and statement normalization flows`

---

### Task 29: Add Sheets export end-to-end test

**Files:**
- Create: `tests/e2e/sheets-export.test.ts`

**Action:** Verify approved entries sync to the correct tab shape, exact duplicates do not create a second active row, and review queue rows remain isolated from approved exports.

**Verify:**
```bash
npm test -- tests/e2e/sheets-export.test.ts
```

**Commit:** `test(e2e): verify sheets export contract`

---

### Task 30: Add operational setup and sample workflow docs

**Files:**
- Create: `docs/specs/schema.md`
- Create: `docs/specs/google-sheets-contract.md`
- Create: `docs/specs/sample-workflow.md`

**Action:** Document the canonical schema, tab contract, CLI workflow, and current V1 limitations around OCR quality, provider-specific CSV formats, and manual review expectations.

**Verify:**
```bash
test -f docs/specs/schema.md && test -f docs/specs/google-sheets-contract.md && test -f docs/specs/sample-workflow.md
```

**Commit:** `docs(specs): add schema and workflow references`

## Batch Recommendation

Recommended execution batches:

1. Tasks 1-6, repo foundation and schema contract
2. Tasks 7-11, persistence and intake foundation
3. Tasks 12-17, adapters and normalization
4. Tasks 18-22, categorization, duplicates, review, and audit
5. Tasks 23-27, Sheets sync, summary, CLI, and review operations
6. Tasks 28-30, end-to-end coverage and docs

## First Slice To Execute

Start with Tasks 1-3. They establish the workspace, document skeleton, and the canonical enums that all later schemas and tests depend on.

## Open Decisions To Confirm Before Coding

These do not block the plan, but they should be confirmed during early implementation:

1. preferred package manager, `npm` or `bun`
2. whether to use a pure CLI V1 or add a minimal local web review screen later
3. preferred base currency strategy for future FX support
4. whether receipt PDF parsing should land in V1 or stay behind a review-heavy adapter
