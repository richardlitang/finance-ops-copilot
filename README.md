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

## Key Docs

- [Docs Index](./docs/index.md)
- [V1 Plan](./docs/plans/active/2026-04-17-finance-ops-copilot-v1.md)
