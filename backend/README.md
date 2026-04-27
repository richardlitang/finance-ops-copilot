# Receipt-First Finance Backend

Python/FastAPI backend for the receipt-first ingestion and reconciliation model.

## Setup

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

## Test

```bash
cd backend
.venv/bin/python -m pytest tests
```

## Run API

FastAPI is exposed as `app.main:app`.

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --reload
```

For SQLite persistence:

```bash
cd backend
FINANCE_DATABASE_URL=sqlite+pysqlite:///./finance.sqlite .venv/bin/alembic upgrade head
FINANCE_DATABASE_URL=sqlite+pysqlite:///./finance.sqlite .venv/bin/python -m uvicorn app.main:app --reload
```

Available V1 endpoints:

- `GET /health`
- `POST /api/imports/receipt-text`
- `POST /api/imports/statement-csv`
- `GET /api/categories`
- `POST /api/categories`
- `GET /api/categories/rules`
- `POST /api/categories/rules`
- `GET /api/events?month=2026-04`
- `GET /api/review/matches`
- `POST /api/review/events/{event_id}/confirm-manual`
- `POST /api/review/events/{event_id}/duplicate`
- `POST /api/review/events/{event_id}/ignore`
- `POST /api/review/events/{event_id}/category`
- `POST /api/review/matches/{match_id}/confirm`
- `POST /api/review/matches/{match_id}/reject`
- `GET /api/summary?month=2026-04&mode=fast`
- `POST /api/export/csv`

Without `FINANCE_DATABASE_URL`, the API uses in-memory storage. With `FINANCE_DATABASE_URL`, it uses the SQLAlchemy repository.

## Idempotency

Receipt and statement imports are keyed by stable source and evidence fingerprints.

- Re-importing the same receipt text returns the existing evidence and spending event.
- Re-importing the same statement CSV returns existing evidence and does not create extra events, links, or match candidates.
- Receipt-to-statement reconciliation can be rerun without duplicating the canonical spending event.

## Review Actions

The review API keeps uncertainty explicit:

- Manual confirmation turns an unmatched receipt into `manual_confirmed` spending with `source_quality = manual`.
- Duplicate and ignored actions update `lifecycle_status` without deleting evidence.
- Match confirmation updates the canonical spending event from statement evidence and records a confirmed evidence link.
- Match rejection records a rejected evidence link for auditability.
- Category correction can optionally create a merchant mapping rule for future imports.

## Categorization

Mapping rules are deterministic and priority-ordered. Receipt imports apply the current rules before saving the spending event.

Supported rule pattern types:

- `merchant`
- `description`
- `source`
