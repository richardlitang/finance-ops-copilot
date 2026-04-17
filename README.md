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

## Key Docs

- [Docs Index](./docs/index.md)
- [V1 Plan](./docs/plans/active/2026-04-17-finance-ops-copilot-v1.md)
