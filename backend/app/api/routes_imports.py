from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.repositories import InMemoryFinanceRepository
from app.schemas.imports import ImportResponse, ReceiptTextImportRequest, StatementCsvImportRequest
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
    spending_event = repository.save_spending_event(result.spending_event)
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
    result = import_statement_csv(
        raw_csv=request.raw_csv,
        filename=request.filename,
        existing_events=repository.list_spending_events(),
        now=datetime.now(timezone.utc),
        source_document_id=repository.next_id("source_document"),
    )
    source_document = repository.save_source_document(result.source_document)
    evidence_records = [repository.save_evidence_record(record) for record in result.evidence_records]
    spending_events = [repository.save_spending_event(event) for event in result.spending_events]
    evidence_links = [repository.save_evidence_link(link) for link in result.evidence_links]
    match_candidates = [
        repository.save_match_candidate(candidate) for candidate in result.match_candidates
    ]
    return ImportResponse(
        source_document_id=source_document.id,
        evidence_record_ids=[record.id for record in evidence_records],
        spending_event_ids=[event.id for event in spending_events],
        evidence_link_ids=[link.id for link in evidence_links],
        match_candidate_ids=[candidate.id for candidate in match_candidates],
    )
