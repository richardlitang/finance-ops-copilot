from datetime import datetime, timezone
from dataclasses import replace

from app.db import create_db_engine, create_session_factory
from app.domain import (
    ConfirmationStatus,
    Direction,
    EvidenceRecord,
    EvidenceType,
    LifecycleStatus,
    ReviewStatus,
    SourceQuality,
    SpendingEvent,
)
from app.repositories import SqlAlchemyFinanceRepository


NOW = datetime(2026, 4, 17, tzinfo=timezone.utc)


def repository() -> SqlAlchemyFinanceRepository:
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    repo = SqlAlchemyFinanceRepository(create_session_factory(engine))
    repo.create_schema()
    return repo


def test_sqlalchemy_repository_dedupes_evidence_by_fingerprint():
    repo = repository()
    evidence = EvidenceRecord(
        id="ev_1",
        source_document_id="src_1",
        evidence_type=EvidenceType.RECEIPT,
        extraction_confidence=1.0,
        fingerprint="same",
        created_at=NOW,
    )

    repo.save_evidence_record(evidence)
    saved = repo.save_evidence_record(replace(evidence, id="ev_2"))

    assert saved.id == "ev_1"


def test_sqlalchemy_repository_saves_and_lists_spending_events():
    repo = repository()
    event = SpendingEvent(
        id="evt_1",
        occurred_at=NOW,
        merchant_normalized="Aldi",
        amount_minor=4297,
        currency="EUR",
        direction=Direction.EXPENSE,
        confirmation_status=ConfirmationStatus.PROVISIONAL,
        review_status=ReviewStatus.CLEAR,
        lifecycle_status=LifecycleStatus.ACTIVE,
        source_quality=SourceQuality.RECEIPT_ONLY,
        created_at=NOW,
        updated_at=NOW,
    )

    repo.save_spending_event(event)

    assert repo.list_spending_events() == [event]
