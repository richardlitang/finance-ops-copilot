# Finance Ops Copilot

Finance Ops Copilot is a local-first ingestion pipeline that normalizes receipts and statement inputs into a canonical model, routes uncertainty to review, and syncs approved entries to Google Sheets.

## Repository Goals

- Preserve provenance and auditability from import to export
- Keep duplicate handling deterministic and explainable
- Use LLMs only as bounded suggestion helpers
- Keep local storage as the source of truth

## Quickstart

```bash
npm install
npm run typecheck
npm test
```

## Full Verify

Run:

```bash
npm run verify
```

What it does:

- runs `typecheck`
- runs the full test suite
- runs the production build
- runs the local smoke flow

Use this as the primary local regression check before committing.

## Smoke Flow

Run:

```bash
npm run smoke
```

What it does:

- migrates a dedicated local smoke database
- loads stable smoke mapping rules and fixtures
- imports one PH receipt, one US receipt, one bank CSV, one credit card CSV, and one duplicate bank re-import
- prints a concise review queue summary
- auto-approves only `normalized` non-review entries for smoke validation
- exports approved rows through the configured Sheets gateway
- prints monthly summary row count

Expected output shape:

```text
migrate ok db=...
fixtures loaded rules=... imports=5
import ph-receipt entries=1
...
review_queue=... exact_duplicates=... ...
export approved=... review_queue=... auto_approved=...
summary rows=...
smoke ok fixtures=5 entries=... review_queue=... approved_exported=... summary_rows=...
```

## Mapping Rules

Bootstrap the default checked-in rules:

```bash
node --import tsx src/cli/index.ts rules bootstrap
```

Import a custom rules CSV:

```bash
node --import tsx src/cli/index.ts rules import ./path/to/rules.csv
```

List the current local rules:

```bash
node --import tsx src/cli/index.ts rules list
```

CSV columns:

- `rule_id` (optional, deterministic ID is generated if omitted)
- `field` (`merchant`, `description`, or `line_item`)
- `pattern`
- `target_category`
- `priority` (optional, defaults to `50`)
- `created_by` (optional)

## Extracted Candidates

Inspect raw extracted candidate fields linked to a normalized entry or source document:

```bash
node --import tsx src/cli/index.ts candidates entry <entry-id>
node --import tsx src/cli/index.ts candidates document <document-id>
```

This is the quickest way to compare what an adapter extracted versus what the normalized entry ended up storing.

Inspect the normalized record directly:

```bash
node --import tsx src/cli/index.ts entry show <entry-id>
```

Use `entry show` and `candidates entry` together when validating receipt parsing.

## Key Docs

- [Docs Index](./docs/index.md)
- [V1 Plan](./docs/plans/active/2026-04-17-finance-ops-copilot-v1.md)
