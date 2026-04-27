from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain import ConfirmationStatus, LifecycleStatus, SpendingEvent


class AnalysisMode(StrEnum):
    FAST = "fast"
    CONSERVATIVE = "conservative"


@dataclass(frozen=True, slots=True)
class MonthlySummary:
    month: str
    mode: AnalysisMode
    total_expense_minor: int
    event_count: int
    category_totals_minor: dict[str, int]
    provisional_count: int


def summarize_month(events: list[SpendingEvent], *, month: str, mode: AnalysisMode) -> MonthlySummary:
    included = [event for event in events if _event_in_month(event, month) and _include_event(event, mode)]
    category_totals: dict[str, int] = {}
    for event in included:
        category = event.category_id or "uncategorized"
        category_totals[category] = category_totals.get(category, 0) + event.amount_minor

    return MonthlySummary(
        month=month,
        mode=mode,
        total_expense_minor=sum(event.amount_minor for event in included),
        event_count=len(included),
        category_totals_minor=category_totals,
        provisional_count=sum(
            event.confirmation_status is ConfirmationStatus.PROVISIONAL for event in included
        ),
    )


def _event_in_month(event: SpendingEvent, month: str) -> bool:
    return event.occurred_at.strftime("%Y-%m") == month


def _include_event(event: SpendingEvent, mode: AnalysisMode) -> bool:
    if event.lifecycle_status is not LifecycleStatus.ACTIVE:
        return False
    if mode is AnalysisMode.FAST:
        return True
    return event.confirmation_status in {
        ConfirmationStatus.CONFIRMED,
        ConfirmationStatus.MANUAL_CONFIRMED,
    }
