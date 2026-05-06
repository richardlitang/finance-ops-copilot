from datetime import datetime, timezone

from app.domain import AuditActor, AuditEventType
from app.repositories import InMemoryFinanceRepository
from app.services.audit_service import AuditService


NOW = datetime(2026, 4, 17, tzinfo=timezone.utc)


def test_audit_service_records_structured_event():
    repository = InMemoryFinanceRepository()
    service = AuditService(repository)

    event = service.record(
        entity_type="spending_event",
        entity_id="evt_1",
        event_type=AuditEventType.IMPORT_CREATED,
        payload={"source_document_id": "src_1"},
        actor=AuditActor.SYSTEM,
        created_at=NOW,
    )

    assert event.id == "audit_1"
    assert repository.list_audit_events(entity_id="evt_1") == [event]
