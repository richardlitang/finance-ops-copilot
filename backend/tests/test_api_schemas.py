from datetime import datetime, timezone

from app.domain import (
    ConfirmationStatus,
    Direction,
    LifecycleStatus,
    ReviewStatus,
    SourceQuality,
)
from app.domain.models import SpendingEvent
from app.schemas.events import SpendingEventResponse


def test_spending_event_response_serializes_enum_values():
    event = SpendingEvent(
        id="evt_1",
        occurred_at=datetime(2026, 4, 17, tzinfo=timezone.utc),
        merchant_normalized="Aldi",
        amount_minor=4297,
        currency="EUR",
        direction=Direction.EXPENSE,
        confirmation_status=ConfirmationStatus.PROVISIONAL,
        review_status=ReviewStatus.CLEAR,
        lifecycle_status=LifecycleStatus.ACTIVE,
        source_quality=SourceQuality.RECEIPT_ONLY,
        created_at=datetime(2026, 4, 17, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )

    response = SpendingEventResponse.from_domain(event)

    assert response.confirmation_status == "provisional"
    assert response.review_status == "clear"
    assert response.review_reasons == []
    assert response.source_quality == "receipt_only"
