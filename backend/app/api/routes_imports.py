from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.repositories import InMemoryFinanceRepository
from app.schemas.imports import ImportResponse, ReceiptTextImportRequest
from app.services.import_service import import_receipt_text

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
        source_document_id=f"src_{len(repository.source_documents) + 1}",
        evidence_record_id=f"ev_{len(repository.evidence_records) + 1}",
        spending_event_id=f"evt_{len(repository.spending_events) + 1}",
        evidence_link_id=f"link_{len(repository.evidence_links) + 1}",
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

