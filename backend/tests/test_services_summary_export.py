from datetime import datetime, timezone
import unittest

from app.domain import (
    ConfirmationStatus,
    Direction,
    LifecycleStatus,
    ReviewStatus,
    SourceQuality,
)
from app.domain.models import SpendingEvent
from app.services.export_service import export_events_csv
from app.services.summary import AnalysisMode, summarize_month


def event(
    event_id: str,
    amount_minor: int,
    confirmation_status: ConfirmationStatus,
    *,
    category_id: str | None = None,
    lifecycle_status: LifecycleStatus = LifecycleStatus.ACTIVE,
) -> SpendingEvent:
    return SpendingEvent(
        id=event_id,
        occurred_at=datetime(2026, 4, 17, tzinfo=timezone.utc),
        merchant_normalized="Aldi",
        amount_minor=amount_minor,
        currency="EUR",
        direction=Direction.EXPENSE,
        category_id=category_id,
        confirmation_status=confirmation_status,
        review_status=ReviewStatus.CLEAR,
        lifecycle_status=lifecycle_status,
        source_quality=SourceQuality.RECEIPT_ONLY,
        created_at=datetime(2026, 4, 17, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )


class SummaryExportTests(unittest.TestCase):
    def test_fast_summary_includes_provisional_and_confirmed_events(self):
        summary = summarize_month(
            [
                event("evt_1", 4297, ConfirmationStatus.PROVISIONAL, category_id="groceries"),
                event("evt_2", 1599, ConfirmationStatus.CONFIRMED, category_id="subscriptions"),
            ],
            month="2026-04",
            mode=AnalysisMode.FAST,
        )

        self.assertEqual(summary.total_expense_minor, 5896)
        self.assertEqual(summary.provisional_count, 1)
        self.assertEqual(summary.category_totals_minor["groceries"], 4297)

    def test_conservative_summary_excludes_provisional_events(self):
        summary = summarize_month(
            [
                event("evt_1", 4297, ConfirmationStatus.PROVISIONAL),
                event("evt_2", 1599, ConfirmationStatus.CONFIRMED),
            ],
            month="2026-04",
            mode=AnalysisMode.CONSERVATIVE,
        )

        self.assertEqual(summary.total_expense_minor, 1599)
        self.assertEqual(summary.event_count, 1)

    def test_csv_export_skips_ignored_or_duplicate_events(self):
        csv_text = export_events_csv(
            [
                event("evt_1", 4297, ConfirmationStatus.CONFIRMED),
                event("evt_2", 1599, ConfirmationStatus.CONFIRMED, lifecycle_status=LifecycleStatus.IGNORED),
            ]
        )

        self.assertIn("evt_1", csv_text)
        self.assertNotIn("evt_2", csv_text)
        self.assertIn("confirmation_status", csv_text)


if __name__ == "__main__":
    unittest.main()
