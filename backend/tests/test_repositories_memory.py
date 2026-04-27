from datetime import datetime, timezone

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
from app.repositories import InMemoryFinanceRepository


NOW = datetime(2026, 4, 17, tzinfo=timezone.utc)


def test_repository_dedupes_evidence_by_fingerprint():
    repo = InMemoryFinanceRepository()
    first = EvidenceRecord(
        id="ev_1",
        source_document_id="src_1",
        evidence_type=EvidenceType.RECEIPT,
        extraction_confidence=1.0,
        fingerprint="same",
        created_at=NOW,
    )
    second = EvidenceRecord(
        id="ev_2",
        source_document_id="src_2",
        evidence_type=EvidenceType.RECEIPT,
        extraction_confidence=1.0,
        fingerprint="same",
        created_at=NOW,
    )

    repo.save_evidence_record(first)
    saved = repo.save_evidence_record(second)

    assert saved.id == "ev_1"
    assert len(repo.evidence_records) == 1


def test_repository_lists_provisional_events():
    repo = InMemoryFinanceRepository()
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

    assert repo.list_provisional_events() == [event]
    assert repo.get_spending_event("evt_1") == event
    assert repo.find_event_by_canonical_evidence_id("missing") is None
