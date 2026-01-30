from __future__ import annotations

from dataclasses import asdict

from pydantic import BaseModel

from app.services.google_sheets import GoogleSheetsSyncResult
from app.services.summary import MonthlySummary


class MonthlySummaryResponse(BaseModel):
    month: str
    mode: str
    total_expense_minor: int
    event_count: int
    category_totals_minor: dict[str, int]
    provisional_count: int

    @classmethod
    def from_domain(cls, summary: MonthlySummary) -> MonthlySummaryResponse:
        return cls(
            month=summary.month,
            mode=summary.mode.value,
            total_expense_minor=summary.total_expense_minor,
            event_count=summary.event_count,
            category_totals_minor=summary.category_totals_minor,
            provisional_count=summary.provisional_count,
        )


class GoogleSheetsExportResponse(BaseModel):
    normalized_entries: int
    review_queue: int
    mapping_rules: int
    monthly_summary: int

    @classmethod
    def from_domain(cls, result: GoogleSheetsSyncResult) -> "GoogleSheetsExportResponse":
        return cls(**asdict(result))
