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
.venv/bin/fastapi dev app/main.py
```

For SQLite persistence:

```bash
cd backend
FINANCE_DATABASE_URL=sqlite+pysqlite:///./finance.sqlite .venv/bin/alembic upgrade head
FINANCE_DATABASE_URL=sqlite+pysqlite:///./finance.sqlite .venv/bin/fastapi dev app/main.py
```

Available V1 endpoints:

- `GET /health`
- `POST /api/imports/receipt-text`
- `POST /api/imports/statement-csv`
- `GET /api/events?month=2026-04`
- `GET /api/summary?month=2026-04&mode=fast`
- `POST /api/export/csv`

Current persistence is intentionally in-memory. It proves the receipt-first reconciliation model before adding SQLAlchemy persistence.
Without `FINANCE_DATABASE_URL`, the API uses in-memory storage. With `FINANCE_DATABASE_URL`, it uses the SQLAlchemy repository.
