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

### Task 4: Add Idempotency Fingerprints

**Files:**

- `backend/app/domain/fingerprints.py`
- `backend/tests/test_domain_fingerprints.py`
- `backend/app/domain/__init__.py`

**Action:** Add deterministic fingerprint helpers for document and evidence idempotency.

**Verify:**

```bash
python3 -B -m unittest discover -s tests
```

**Commit:** `feat(backend): add idempotency fingerprint helpers`

### Task 5: Next Slice, Backend API Skeleton

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

## Batch Checkpoint, 2026-04-27

Completed backend core slices:

- `389b892` added deterministic money, date, currency, and merchant normalization.
- `4353a94` added deterministic receipt text parsing.
- `002e2e9` creates source documents, receipt evidence, provisional events, and evidence links from receipt text.
- `70e7d35` added priority-ordered mapping rules for categorization.
- `9cabce6` added the narrow V1 statement CSV profile.
- `63789bd` added match scoring and match candidates.
- `9a6445f` imports statement rows, auto-confirms high-confidence matches, and creates statement-only events.
- `634b439` added review actions for manual cash confirmation, duplicate, ignored, and rejected matches.
- `f96852d` added fast and conservative monthly summaries plus CSV export.

Current blocker for Task 5:

- FastAPI is declared in `backend/pyproject.toml`, but it is not installed in the local Python environment yet.
- Continue with the FastAPI health endpoint after installing backend dependencies in a virtual environment.

## Batch Checkpoint, Idempotency

Completed import idempotency slices:

- `0264e35` stabilizes receipt and statement evidence fingerprints across generated IDs.
- `d18889b` adds repository lookups from evidence to canonical spending events.
- `0e891e2` makes duplicate receipt imports return the existing event without creating links.
- `477f27d` verifies duplicate receipt imports on SQLite-backed API storage.
- `9c10226` skips duplicate statement-row evidence before creating events, links, or match candidates.
- `8716966` verifies duplicate statement CSV imports on both in-memory and SQLite API paths.

Current import idempotency behavior:

- Duplicate receipt text imports do not create duplicate evidence, events, or links.
- Duplicate statement CSV imports do not create duplicate evidence, events, links, or matches.
- Reconciliation updates the existing receipt-created event when a new matching statement row arrives.

## Batch Checkpoint, Review API

Completed review workflow slices:

- `23a7dbf` adds repository lookup methods needed by review actions.
- `722c31f` adds review response schemas.
- `43ab65e` exposes manual cash confirmation for unmatched receipts.
- `4cfe626` exposes duplicate and ignored lifecycle review actions.
- `8727873` exposes medium-confidence match listing.
- `b14475f` records rejected match links.
- `6156093` confirms suggested matches and updates canonical spending events from statement evidence.
- `c886d72` verifies review actions against SQLite-backed API storage.

Current review behavior:

- Review actions update status fields, they do not delete raw evidence.
- Confirming a match uses the deterministic statement-confirmation service.
- Rejecting a match creates a rejected evidence link so the decision remains auditable.
