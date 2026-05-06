from datetime import datetime, timezone

from app.domain import (
    AuditActor,
    AuditEvent,
    AuditEventType,
    ConfirmationStatus,
    Direction,
    EvidenceType,
    LifecycleStatus,
    ReviewReason,
    ReviewStatus,
    SourceQuality,
)
from app.domain.models import EvidenceRecord, SpendingEvent
from app.orm.mappers import (
    evidence_record_from_row,
    evidence_record_to_row,
    spending_event_from_row,
    spending_event_to_row,
    audit_event_from_row,
    audit_event_to_row,
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
        review_reasons=(ReviewReason.PARSE_WARNING,),
    )

    restored = spending_event_from_row(spending_event_to_row(event))

    assert restored.confirmation_status is ConfirmationStatus.PROVISIONAL
    assert restored.review_status is ReviewStatus.NEEDS_REVIEW
    assert restored.lifecycle_status is LifecycleStatus.ACTIVE
    assert restored.review_reasons == (ReviewReason.PARSE_WARNING,)


def test_audit_event_round_trips_payload_json():
    event = AuditEvent(
        id="audit_1",
        entity_type="spending_event",
        entity_id="evt_1",
        event_type=AuditEventType.IMPORT_CREATED,
        actor=AuditActor.SYSTEM,
        payload={"source_document_id": "src_1"},
        created_at=NOW,
    )

    restored = audit_event_from_row(audit_event_to_row(event))

    assert restored.event_type is AuditEventType.IMPORT_CREATED
    assert restored.actor is AuditActor.SYSTEM
    assert restored.payload == {"source_document_id": "src_1"}
