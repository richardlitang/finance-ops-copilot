from dataclasses import replace
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.domain import AuditActor, AuditEventType, ReviewStatus
from app.domain.reconciliation import apply_statement_confirmation
from app.repositories import InMemoryFinanceRepository
from app.schemas.events import SpendingEventResponse
from app.schemas.review import (
    CategoryCorrectionRequest,
    EvidenceLinkResponse,
    MatchCandidateResponse,
    ReviewActionResponse,
)
from app.services.categorization import MappingRule, PatternType
from app.services.audit_service import AuditService
from app.services.review_service import (
    confirm_receipt_as_manual,
    create_statement_only_event_from_evidence,
    ignore_event,
    mark_event_duplicate,
    reject_match_candidate,
)

from .dependencies import get_repository


router = APIRouter(prefix="/api/review", tags=["review"])


@router.get("/matches", response_model=list[MatchCandidateResponse])
def list_review_matches(
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> list[MatchCandidateResponse]:
    return [
        MatchCandidateResponse.from_domain(candidate)
        for candidate in repository.list_match_candidates()
        if candidate.decision == "needs_review"
    ]


@router.post("/events/{event_id}/confirm-manual", response_model=ReviewActionResponse)
def confirm_manual_event(
    event_id: str,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> ReviewActionResponse:
    event = _get_event_or_404(repository, event_id)
    audit = AuditService(repository)

    updated = confirm_receipt_as_manual(event, reviewed_at=datetime.now(timezone.utc))
    repository.save_spending_event(updated)
    audit.record(
        entity_type="spending_event",
        entity_id=updated.id,
        event_type=AuditEventType.EVENT_MANUAL_CONFIRMED,
        payload={"previous_confirmation_status": event.confirmation_status.value},
        actor=AuditActor.USER,
    )
    return ReviewActionResponse(spending_event=SpendingEventResponse.from_domain(updated))


@router.post("/events/{event_id}/duplicate", response_model=ReviewActionResponse)
def mark_duplicate_event(
    event_id: str,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> ReviewActionResponse:
    event = _get_event_or_404(repository, event_id)
    audit = AuditService(repository)
    updated = mark_event_duplicate(event, reviewed_at=datetime.now(timezone.utc))
    repository.save_spending_event(updated)
    audit.record(
        entity_type="spending_event",
        entity_id=updated.id,
        event_type=AuditEventType.EVENT_MARKED_DUPLICATE,
        payload={"previous_lifecycle_status": event.lifecycle_status.value},
        actor=AuditActor.USER,
    )
    return ReviewActionResponse(spending_event=SpendingEventResponse.from_domain(updated))


@router.post("/events/{event_id}/ignore", response_model=ReviewActionResponse)
def ignore_review_event(
    event_id: str,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> ReviewActionResponse:
    event = _get_event_or_404(repository, event_id)
    audit = AuditService(repository)
    updated = ignore_event(event, reviewed_at=datetime.now(timezone.utc))
    repository.save_spending_event(updated)
    audit.record(
        entity_type="spending_event",
        entity_id=updated.id,
        event_type=AuditEventType.EVENT_IGNORED,
        payload={"previous_lifecycle_status": event.lifecycle_status.value},
        actor=AuditActor.USER,
    )
    return ReviewActionResponse(spending_event=SpendingEventResponse.from_domain(updated))


@router.post("/events/{event_id}/category", response_model=ReviewActionResponse)
def correct_event_category(
    event_id: str,
    request: CategoryCorrectionRequest,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> ReviewActionResponse:
    event = _get_event_or_404(repository, event_id)
    _get_category_or_404(repository, request.category_id)
    audit = AuditService(repository)
    updated = event.with_updates(
        category_id=request.category_id,
        review_status=ReviewStatus.RESOLVED,
        review_reasons=(),
        updated_at=datetime.now(timezone.utc),
    )
    repository.save_spending_event(updated)
    audit.record(
        entity_type="spending_event",
        entity_id=updated.id,
        event_type=AuditEventType.CATEGORY_CORRECTED,
        payload={
            "previous_category_id": event.category_id,
            "category_id": request.category_id,
        },
        actor=AuditActor.USER,
    )
    if request.create_mapping_rule:
        mapping_rule = repository.save_mapping_rule(
            MappingRule(
                id=repository.next_id("mapping_rule"),
                pattern=event.merchant_normalized,
                pattern_type=PatternType.MERCHANT,
                category_id=request.category_id,
                priority=100,
                created_from_review=True,
                created_at=datetime.now(timezone.utc),
            )
        )
        audit.record(
            entity_type="spending_event",
            entity_id=updated.id,
            event_type=AuditEventType.MAPPING_RULE_CREATED,
            payload={
                "mapping_rule_id": mapping_rule.id,
                "category_id": mapping_rule.category_id,
                "pattern": mapping_rule.pattern,
            },
            actor=AuditActor.USER,
        )
    return ReviewActionResponse(spending_event=SpendingEventResponse.from_domain(updated))


@router.post("/matches/{match_id}/reject", response_model=EvidenceLinkResponse)
def reject_match(
    match_id: str,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> EvidenceLinkResponse:
    candidate = repository.get_match_candidate(match_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="match candidate not found")
    audit = AuditService(repository)
    evidence = repository.get_evidence_record(candidate.statement_evidence_record_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="match target not found")
    link = reject_match_candidate(candidate, reviewed_at=datetime.now(timezone.utc))
    repository.save_evidence_link(link)
    repository.save_spending_event(
        create_statement_only_event_from_evidence(
            evidence,
            event_id=repository.next_id("spending_event"),
            reviewed_at=datetime.now(timezone.utc),
        )
    )
    repository.save_match_candidate(replace(candidate, decision="rejected"))
    audit.record(
        entity_type="spending_event",
        entity_id=candidate.spending_event_id,
        event_type=AuditEventType.MATCH_REJECTED,
        payload={"match_candidate_id": candidate.id, "score": candidate.score},
        actor=AuditActor.USER,
    )
    return EvidenceLinkResponse.from_domain(link)


@router.post("/matches/{match_id}/confirm", response_model=ReviewActionResponse)
def confirm_match(
    match_id: str,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> ReviewActionResponse:
    candidate = repository.get_match_candidate(match_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="match candidate not found")
    audit = AuditService(repository)
    event = repository.get_spending_event(candidate.spending_event_id)
    evidence = repository.get_evidence_record(candidate.statement_evidence_record_id)
    if event is None or evidence is None:
        raise HTTPException(status_code=404, detail="match target not found")

    confirmed, link = apply_statement_confirmation(
        event,
        evidence,
        link_id=repository.next_id("evidence_link"),
        matched_at=datetime.now(timezone.utc),
        match_score=candidate.score,
    )
    repository.save_spending_event(confirmed)
    repository.save_evidence_link(link)
    repository.save_match_candidate(replace(candidate, decision="confirmed"))
    audit.record(
        entity_type="spending_event",
        entity_id=confirmed.id,
        event_type=AuditEventType.MATCH_CONFIRMED,
        payload={
            "match_candidate_id": candidate.id,
            "statement_evidence_record_id": candidate.statement_evidence_record_id,
            "score": candidate.score,
        },
        actor=AuditActor.USER,
    )
    return ReviewActionResponse(
        spending_event=SpendingEventResponse.from_domain(confirmed),
        evidence_link=EvidenceLinkResponse.from_domain(link),
    )


def _get_event_or_404(repository: InMemoryFinanceRepository, event_id: str):
    event = repository.get_spending_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="spending event not found")
    return event


def _get_category_or_404(repository: InMemoryFinanceRepository, category_id: str):
    for category in repository.list_categories():
        if category.id == category_id:
            return category
    raise HTTPException(status_code=404, detail="category not found")
