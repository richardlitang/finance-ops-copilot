from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.domain import AuditEventType, ReviewReason, ReviewStatus
from app.repositories import InMemoryFinanceRepository
from app.schemas.imports import ImportResponse, ReceiptTextImportRequest, StatementCsvImportRequest
from app.services.audit_service import AuditService
from app.services.categorization import categorize_event
from app.services.import_service import import_receipt_text, import_statement_csv

from .dependencies import get_repository


router = APIRouter(prefix="/api/imports", tags=["imports"])


@router.post("/receipt-text", response_model=ImportResponse)
def import_receipt_text_endpoint(
    request: ReceiptTextImportRequest,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> ImportResponse:
    audit = AuditService(repository)
    result = import_receipt_text(
        raw_text=request.raw_text,
        filename=request.filename,
        now=datetime.now(timezone.utc),
        source_document_id=repository.next_id("source_document"),
        evidence_record_id=repository.next_id("evidence_record"),
        spending_event_id=repository.next_id("spending_event"),
        evidence_link_id=repository.next_id("evidence_link"),
    )
    source_document = repository.save_source_document(result.source_document)
    evidence_record = repository.save_evidence_record(result.evidence_record)
    existing_event = repository.find_event_by_canonical_evidence_id(evidence_record.id)
    if existing_event:
        audit.record(
            entity_type="spending_event",
            entity_id=existing_event.id,
            event_type=AuditEventType.IMPORT_CREATED,
            payload={
                "source_document_id": source_document.id,
                "evidence_record_id": evidence_record.id,
                "deduplicated": True,
            },
        )
        return ImportResponse(
            source_document_id=source_document.id,
            evidence_record_ids=[evidence_record.id],
            spending_event_ids=[existing_event.id],
            evidence_link_ids=[],
        )
    category_decision = categorize_event(
        result.spending_event,
        evidence_record,
        repository.list_mapping_rules(),
    )
    event_to_save = result.spending_event
    if category_decision.category_id:
        event_to_save = event_to_save.with_updates(category_id=category_decision.category_id)
    elif category_decision.needs_review:
        review_reasons = list(event_to_save.review_reasons)
        if ReviewReason.UNCERTAIN_CATEGORY not in review_reasons:
            review_reasons.append(ReviewReason.UNCERTAIN_CATEGORY)
        event_to_save = event_to_save.with_updates(
            review_status=ReviewStatus.NEEDS_REVIEW,
            review_reasons=tuple(review_reasons),
        )

    spending_event = repository.save_spending_event(event_to_save)
    evidence_link = repository.save_evidence_link(result.evidence_link)
    audit.record(
        entity_type="spending_event",
        entity_id=spending_event.id,
        event_type=AuditEventType.IMPORT_CREATED,
        payload={
            "source_document_id": source_document.id,
            "evidence_record_id": evidence_record.id,
            "source_type": result.source_document.source_type.value,
            "review_reasons": [reason.value for reason in spending_event.review_reasons],
        },
    )
    if spending_event.review_reasons:
        audit.record(
            entity_type="spending_event",
            entity_id=spending_event.id,
            event_type=AuditEventType.REVIEW_ROUTED,
            payload={"review_reasons": [reason.value for reason in spending_event.review_reasons]},
        )
    return ImportResponse(
        source_document_id=source_document.id,
        evidence_record_ids=[evidence_record.id],
        spending_event_ids=[spending_event.id],
        evidence_link_ids=[evidence_link.id],
    )


@router.post("/statement-csv", response_model=ImportResponse)
def import_statement_csv_endpoint(
    request: StatementCsvImportRequest,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> ImportResponse:
    audit = AuditService(repository)
    try:
        result = import_statement_csv(
            raw_csv=request.raw_csv,
            filename=request.filename,
            existing_events=repository.list_spending_events(),
            now=datetime.now(timezone.utc),
            source_document_id=repository.next_id("source_document"),
            evidence_record_id_start=_id_number(repository.next_id("evidence_record")),
            spending_event_id_start=_id_number(repository.next_id("spending_event")),
            evidence_link_id_start=_id_number(repository.next_id("evidence_link")),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    source_document = repository.save_source_document(result.source_document)
    new_evidence_ids: set[str] = set()
    evidence_records = []
    for record in result.evidence_records:
        existing_evidence = repository.find_evidence_by_fingerprint(record.fingerprint)
        evidence_record = repository.save_evidence_record(record)
        evidence_records.append(evidence_record)
        if existing_evidence is None:
            new_evidence_ids.add(evidence_record.id)

    spending_events = []
    for event in result.spending_events:
        if event.canonical_source_evidence_id in new_evidence_ids:
            spending_events.append(repository.save_spending_event(event))

    evidence_links = [
        repository.save_evidence_link(link)
        for link in result.evidence_links
        if link.evidence_record_id in new_evidence_ids
    ]
    match_candidates = [
        repository.save_match_candidate(candidate)
        for candidate in result.match_candidates
        if candidate.statement_evidence_record_id in new_evidence_ids
    ]
    for event in spending_events:
        audit.record(
            entity_type="spending_event",
            entity_id=event.id,
            event_type=AuditEventType.IMPORT_CREATED,
            payload={
                "source_document_id": source_document.id,
                "source_type": result.source_document.source_type.value,
                "canonical_source_evidence_id": event.canonical_source_evidence_id,
                "review_reasons": [reason.value for reason in event.review_reasons],
            },
        )
        if event.review_reasons:
            audit.record(
                entity_type="spending_event",
                entity_id=event.id,
                event_type=AuditEventType.REVIEW_ROUTED,
                payload={"review_reasons": [reason.value for reason in event.review_reasons]},
            )
    for candidate in match_candidates:
        audit.record(
            entity_type="spending_event",
            entity_id=candidate.spending_event_id,
            event_type=AuditEventType.REVIEW_ROUTED,
            payload={
                "review_reasons": _candidate_review_reasons(candidate.reasons),
                "match_candidate_id": candidate.id,
                "score": candidate.score,
            },
        )
    return ImportResponse(
        source_document_id=source_document.id,
        evidence_record_ids=[record.id for record in evidence_records],
        spending_event_ids=[event.id for event in spending_events],
        evidence_link_ids=[link.id for link in evidence_links],
        match_candidate_ids=[candidate.id for candidate in match_candidates],
    )


def _id_number(value: str) -> int:
    return int(value.rsplit("_", 1)[1])


def _candidate_review_reasons(reasons: tuple[str, ...]) -> list[str]:
    values = ["possible_receipt_statement_match"]
    if "amount_mismatch" in reasons:
        values.append("amount_mismatch")
    return values
