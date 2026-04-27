from fastapi import APIRouter, Depends

from app.repositories import InMemoryFinanceRepository
from app.schemas.events import SpendingEventResponse

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

