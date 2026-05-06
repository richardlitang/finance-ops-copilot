from fastapi import APIRouter, Depends, HTTPException

from app.repositories import InMemoryFinanceRepository
from app.schemas.events import (
    AuditEventResponse,
    EventEvidenceLinkResponse,
    EventEvidenceResponse,
    EventMatchCandidateResponse,
    SpendingEventResponse,
)

from .dependencies import get_repository


router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=list[SpendingEventResponse])
def list_events(
    month: str | None = None,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> list[SpendingEventResponse]:
    events = repository.list_spending_events()
    if month:
        events = [event for event in events if event.occurred_at.strftime("%Y-%m") == month]
    return [SpendingEventResponse.from_domain(event) for event in events]


@router.get("/{event_id}", response_model=SpendingEventResponse)
def get_event(
    event_id: str,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> SpendingEventResponse:
    event = repository.get_spending_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="spending event not found")
    return SpendingEventResponse.from_domain(event)


@router.get("/{event_id}/evidence", response_model=EventEvidenceResponse)
def get_event_evidence(
    event_id: str,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> EventEvidenceResponse:
    event = repository.get_spending_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="spending event not found")

    linked_evidence = []
    for link in repository.list_evidence_links():
        if link.spending_event_id != event_id:
            continue
        evidence = repository.get_evidence_record(link.evidence_record_id)
        if evidence is None:
            continue
        linked_evidence.append(EventEvidenceLinkResponse.from_domain(link, evidence))

    match_candidates = [
        EventMatchCandidateResponse.from_domain(candidate)
        for candidate in repository.list_match_candidates()
        if candidate.spending_event_id == event_id
    ]
    audit_events = [
        AuditEventResponse.from_domain(audit_event)
        for audit_event in repository.list_audit_events(entity_id=event_id)
    ]

    return EventEvidenceResponse(
        event=SpendingEventResponse.from_domain(event),
        linked_evidence=linked_evidence,
        match_candidates=match_candidates,
        audit_events=audit_events,
    )


@router.get("/{event_id}/audit", response_model=list[AuditEventResponse])
def list_event_audit(
    event_id: str,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> list[AuditEventResponse]:
    event = repository.get_spending_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="spending event not found")
    return [
        AuditEventResponse.from_domain(audit_event)
        for audit_event in repository.list_audit_events(entity_id=event_id)
    ]
