from fastapi import APIRouter, Depends, Response

from app.repositories import InMemoryFinanceRepository
from app.schemas.summary import MonthlySummaryResponse
from app.services.export_service import export_events_csv
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

