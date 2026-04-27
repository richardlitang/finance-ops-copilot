from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.domain import SpendingEvent


class SpendingEventResponse(BaseModel):
    id: str
    occurred_at: datetime
    posted_at: datetime | None
    merchant_normalized: str
    amount_minor: int
    currency: str
    direction: str
    category_id: str | None
    confirmation_status: str
    review_status: str
    lifecycle_status: str
    source_quality: str
    canonical_source_evidence_id: str | None

    @classmethod
    def from_domain(cls, event: SpendingEvent) -> SpendingEventResponse:
        return cls(
            id=event.id,
            occurred_at=event.occurred_at,
            posted_at=event.posted_at,
            merchant_normalized=event.merchant_normalized,
            amount_minor=event.amount_minor,
            currency=event.currency,
            direction=event.direction.value,
            category_id=event.category_id,
            confirmation_status=event.confirmation_status.value,
            review_status=event.review_status.value,
            lifecycle_status=event.lifecycle_status.value,
            source_quality=event.source_quality.value,
            canonical_source_evidence_id=event.canonical_source_evidence_id,
        )

