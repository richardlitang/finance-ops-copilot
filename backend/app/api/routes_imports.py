from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.repositories import InMemoryFinanceRepository
from app.schemas.imports import ImportResponse, ReceiptTextImportRequest, StatementCsvImportRequest
from app.services.categorization import categorize_event
from app.services.import_service import import_receipt_text, import_statement_csv

from .dependencies import get_repository


router = APIRouter(prefix="/api/imports", tags=["imports"])


@router.post("/receipt-text", response_model=ImportResponse)
def import_receipt_text_endpoint(
    request: ReceiptTextImportRequest,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> ImportResponse:
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

    spending_event = repository.save_spending_event(event_to_save)
    evidence_link = repository.save_evidence_link(result.evidence_link)
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
    return ImportResponse(
        source_document_id=source_document.id,
        evidence_record_ids=[record.id for record in evidence_records],
        spending_event_ids=[event.id for event in spending_events],
        evidence_link_ids=[link.id for link in evidence_links],
        match_candidate_ids=[candidate.id for candidate in match_candidates],
    )


def _id_number(value: str) -> int:
    return int(value.rsplit("_", 1)[1])
