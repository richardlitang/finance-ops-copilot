from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.domain import AuditActor, AuditEventType, ConfirmationStatus, LifecycleStatus, ReviewStatus
from app.repositories import InMemoryFinanceRepository
from app.schemas.summary import GoogleSheetsExportResponse, MonthlySummaryResponse
from app.services.audit_service import AuditService
from app.services.export_service import export_events_csv
from app.services.google_sheets import GoogleSheetsService
from app.services.summary import AnalysisMode, summarize_month

from .dependencies import get_repository


router = APIRouter(tags=["summary"])


@router.get("/api/summary", response_model=MonthlySummaryResponse)
def monthly_summary(
    month: str,
    mode: AnalysisMode = AnalysisMode.FAST,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> MonthlySummaryResponse:
    summary = summarize_month(repository.list_spending_events(), month=month, mode=mode)
    return MonthlySummaryResponse.from_domain(summary)


@router.post("/api/export/csv")
def export_csv(
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> Response:
    csv_text = export_events_csv(repository.list_spending_events())
    return Response(content=csv_text, media_type="text/csv")


@router.post("/api/export/google-sheets", response_model=GoogleSheetsExportResponse)
def export_google_sheets(
    request: Request,
    month: str,
    mode: AnalysisMode = AnalysisMode.FAST,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> GoogleSheetsExportResponse:
    gateway = getattr(request.app.state, "sheets_gateway", None)
    if gateway is None:
        raise HTTPException(status_code=503, detail="google sheets gateway is not configured")
    service = GoogleSheetsService(gateway)
    result = service.sync_all(repository=repository, month=month, mode=mode)
    audit = AuditService(repository)
    for event in repository.list_spending_events():
        if event.occurred_at.strftime("%Y-%m") != month:
            continue
        if event.lifecycle_status is not LifecycleStatus.ACTIVE:
            continue
        if event.review_status is ReviewStatus.NEEDS_REVIEW:
            continue
        if event.confirmation_status not in {
            ConfirmationStatus.CONFIRMED,
            ConfirmationStatus.MANUAL_CONFIRMED,
        }:
            continue
        audit.record(
            entity_type="spending_event",
            entity_id=event.id,
            event_type=AuditEventType.GOOGLE_SHEETS_EXPORTED,
            payload={
                "month": month,
                "mode": mode.value,
                "normalized_entries": result.normalized_entries,
                "review_queue": result.review_queue,
                "mapping_rules": result.mapping_rules,
                "monthly_summary": result.monthly_summary,
            },
            actor=AuditActor.USER,
        )
    return GoogleSheetsExportResponse.from_domain(result)
