from __future__ import annotations

from datetime import datetime, timezone

from app.domain import AuditActor, AuditEvent, AuditEventType


class AuditService:
    def __init__(self, repository: object) -> None:
        self.repository = repository

    def record(
        self,
        *,
        entity_type: str,
        entity_id: str,
        event_type: AuditEventType,
        payload: dict[str, object] | None = None,
        actor: AuditActor = AuditActor.SYSTEM,
        created_at: datetime | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            id=self.repository.next_id("audit_event"),
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            actor=actor,
            payload=payload or {},
            created_at=created_at or datetime.now(timezone.utc),
        )
        return self.repository.save_audit_event(event)
