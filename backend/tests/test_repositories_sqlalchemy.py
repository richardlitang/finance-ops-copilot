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
from app.services.import_service import import_receipt_text


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
    assert repo.find_event_by_canonical_evidence_id("missing") is None


def test_sqlalchemy_repository_persists_receipt_import_result():
    repo = repository()
    result = import_receipt_text(
        raw_text="ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR",
        now=NOW,
    )

    repo.save_source_document(result.source_document)
    repo.save_evidence_record(result.evidence_record)
    repo.save_spending_event(result.spending_event)
    repo.save_evidence_link(result.evidence_link)

    events = repo.list_spending_events()
    links = repo.list_evidence_links()

    assert len(events) == 1
    assert events[0].merchant_normalized == "Aldi"
    assert events[0].amount_minor == 4297
    assert len(links) == 1
    assert links[0].evidence_record_id == result.evidence_record.id
