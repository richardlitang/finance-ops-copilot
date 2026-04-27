from __future__ import annotations

import csv
from io import StringIO

from app.domain import LifecycleStatus, SpendingEvent


def export_events_csv(events: list[SpendingEvent]) -> str:
    buffer = StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "id",
            "occurred_at",
            "posted_at",
            "merchant",
            "amount_minor",
            "currency",
            "category_id",
            "confirmation_status",
            "source_quality",
        ],
    )
    writer.writeheader()
    for event in events:
        if event.lifecycle_status is not LifecycleStatus.ACTIVE:
            continue
        writer.writerow(
            {
                "id": event.id,
                "occurred_at": event.occurred_at.date().isoformat(),
                "posted_at": event.posted_at.date().isoformat() if event.posted_at else "",
                "merchant": event.merchant_normalized,
                "amount_minor": event.amount_minor,
                "currency": event.currency,
                "category_id": event.category_id or "",
                "confirmation_status": event.confirmation_status.value,
                "source_quality": event.source_quality.value,
            }
        )
    return buffer.getvalue()
