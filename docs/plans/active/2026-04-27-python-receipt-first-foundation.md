# Feature: Python Receipt-First Foundation

## Goal

Create the Python backend foundation for receipt-first ingestion, starting with the canonical domain model and reconciliation-safe state transitions.

## Architecture Overview

The first implementation slice lives under `backend/` and does not replace the existing TypeScript reference implementation. It introduces Python domain objects for source documents, evidence records, spending events, and evidence links, then verifies the most important V1 invariant: statement evidence may correct canonical spending event fields without mutating receipt evidence.

## Tech Stack

- Python 3.12 target
- Standard-library dataclasses and `StrEnum` for the first domain slice
- `unittest` for zero-install verification
- FastAPI, Pydantic, SQLAlchemy, and Alembic follow after the core model is proven

## Tasks

### Task 1: Commit PRD Update

**Files:**

- `docs/specs/receipt-first-prd.md`
- `docs/specs/README.md`
- `docs/index.md`

**Action:** Completed.

**Verify:**

```bash
git show --stat --oneline HEAD
```

**Commit:** `docs(prd): define receipt-first finance ingestion`

### Task 2: Add Python Domain Model

**Files:**

- `backend/app/domain/enums.py`
- `backend/app/domain/models.py`
- `backend/app/domain/reconciliation.py`
- `backend/tests/test_domain_reconciliation.py`

**Action:** Create the state enums, dataclass entities, and a deterministic statement-confirmation transition.

**Verify:**

```bash
python3 -m unittest discover -s backend/tests
```

**Commit:** `feat(backend): add receipt-first domain model`

### Task 3: Add Backend Package Metadata

**Files:**

- `backend/pyproject.toml`
- `backend/app/__init__.py`
- `backend/app/domain/__init__.py`

**Action:** Declare the Python package metadata and export domain symbols.

**Verify:**

```bash
python3 -m unittest discover -s backend/tests
```

**Commit:** `chore(backend): add python package metadata`

### Task 4: Next Slice, Backend API Skeleton

**Files:**

- `backend/app/main.py`
- `backend/app/api/routes_health.py`
- `backend/tests/test_health_app.py`

**Action:** Add the FastAPI health endpoint once dependencies are installed or available.

**Verify:**

```bash
python3 -m pytest backend/tests
```

**Commit:** `feat(backend): add fastapi health endpoint`
