from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.repositories import InMemoryFinanceRepository
from app.schemas.events import SpendingEventResponse
from app.schemas.review import ReviewActionResponse
from app.services.review_service import confirm_receipt_as_manual, ignore_event, mark_event_duplicate

from .dependencies import get_repository


router = APIRouter(prefix="/api/review", tags=["review"])


@router.post("/events/{event_id}/confirm-manual", response_model=ReviewActionResponse)
def confirm_manual_event(
    event_id: str,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> ReviewActionResponse:
    event = _get_event_or_404(repository, event_id)

    updated = confirm_receipt_as_manual(event, reviewed_at=datetime.now(timezone.utc))
    repository.save_spending_event(updated)
    return ReviewActionResponse(spending_event=SpendingEventResponse.from_domain(updated))


@router.post("/events/{event_id}/duplicate", response_model=ReviewActionResponse)
def mark_duplicate_event(
    event_id: str,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> ReviewActionResponse:
    event = _get_event_or_404(repository, event_id)
    updated = mark_event_duplicate(event, reviewed_at=datetime.now(timezone.utc))
    repository.save_spending_event(updated)
    return ReviewActionResponse(spending_event=SpendingEventResponse.from_domain(updated))


@router.post("/events/{event_id}/ignore", response_model=ReviewActionResponse)
def ignore_review_event(
    event_id: str,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> ReviewActionResponse:
    event = _get_event_or_404(repository, event_id)
    updated = ignore_event(event, reviewed_at=datetime.now(timezone.utc))
    repository.save_spending_event(updated)
    return ReviewActionResponse(spending_event=SpendingEventResponse.from_domain(updated))


def _get_event_or_404(repository: InMemoryFinanceRepository, event_id: str):
    event = repository.get_spending_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="spending event not found")
    return event
