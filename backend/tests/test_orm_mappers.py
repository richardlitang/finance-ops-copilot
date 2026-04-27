from datetime import datetime, timezone

from app.domain import (
    ConfirmationStatus,
    Direction,
    EvidenceType,
    LifecycleStatus,
    ReviewStatus,
    SourceQuality,
)
from app.domain.models import EvidenceRecord, SpendingEvent
from app.orm.mappers import (
    evidence_record_from_row,
    evidence_record_to_row,
    spending_event_from_row,
    spending_event_to_row,
)


NOW = datetime(2026, 4, 17, tzinfo=timezone.utc)


def test_evidence_record_round_trips_warnings_and_confidence():
    evidence = EvidenceRecord(
        id="ev_1",
        source_document_id="src_1",
        evidence_type=EvidenceType.RECEIPT,
        extraction_confidence=0.74,
        fingerprint="fp",
        warnings=("missing_total", "missing_date"),
        created_at=NOW,
    )

    restored = evidence_record_from_row(evidence_record_to_row(evidence))

    assert restored.extraction_confidence == 0.74
    assert restored.warnings == ("missing_total", "missing_date")


def test_spending_event_round_trips_status_dimensions():
    event = SpendingEvent(
        id="evt_1",
        occurred_at=NOW,
        merchant_normalized="Aldi",
        amount_minor=4297,
        currency="EUR",
        direction=Direction.EXPENSE,
        confirmation_status=ConfirmationStatus.PROVISIONAL,
        review_status=ReviewStatus.NEEDS_REVIEW,
        lifecycle_status=LifecycleStatus.ACTIVE,
        source_quality=SourceQuality.RECEIPT_ONLY,
        created_at=NOW,
        updated_at=NOW,
    )

    restored = spending_event_from_row(spending_event_to_row(event))

    assert restored.confirmation_status is ConfirmationStatus.PROVISIONAL
    assert restored.review_status is ReviewStatus.NEEDS_REVIEW
    assert restored.lifecycle_status is LifecycleStatus.ACTIVE
