from datetime import datetime, timezone
import unittest

from app.domain import (
    ConfirmationStatus,
    Direction,
    EvidenceLinkStatus,
    LifecycleStatus,
    ReviewStatus,
    SourceQuality,
)
from app.domain.models import MatchCandidate, SpendingEvent
from app.services.review_service import (
    confirm_receipt_as_manual,
    ignore_event,
    mark_event_duplicate,
    reject_match_candidate,
)


NOW = datetime(2026, 4, 20, tzinfo=timezone.utc)


def provisional_event() -> SpendingEvent:
    return SpendingEvent(
        id="evt_1",
        occurred_at=NOW,
        merchant_normalized="Cash Cafe",
        amount_minor=1200,
        currency="EUR",
        direction=Direction.EXPENSE,
        confirmation_status=ConfirmationStatus.PROVISIONAL,
        review_status=ReviewStatus.NEEDS_REVIEW,
        lifecycle_status=LifecycleStatus.ACTIVE,
        source_quality=SourceQuality.RECEIPT_ONLY,
        created_at=NOW,
        updated_at=NOW,
    )


class ReviewServiceTests(unittest.TestCase):
    def test_confirm_receipt_as_manual_sets_manual_confirmed_and_manual_source(self):
        event = confirm_receipt_as_manual(provisional_event(), reviewed_at=NOW)

        self.assertEqual(event.confirmation_status, ConfirmationStatus.MANUAL_CONFIRMED)
        self.assertEqual(event.review_status, ReviewStatus.RESOLVED)
        self.assertEqual(event.review_reasons, ())
        self.assertEqual(event.source_quality, SourceQuality.MANUAL)

    def test_mark_duplicate_and_ignore_update_lifecycle_status(self):
        duplicate = mark_event_duplicate(provisional_event(), reviewed_at=NOW)
        ignored = ignore_event(provisional_event(), reviewed_at=NOW)

        self.assertEqual(duplicate.lifecycle_status, LifecycleStatus.DUPLICATE)
        self.assertEqual(ignored.lifecycle_status, LifecycleStatus.IGNORED)

    def test_reject_match_candidate_creates_rejected_link(self):
        link = reject_match_candidate(
            MatchCandidate(
                id="match_1",
                spending_event_id="evt_1",
                statement_evidence_record_id="ev_statement_1",
                score=72,
                decision="needs_review",
                reasons=("exact_amount",),
                created_at=NOW,
            ),
            reviewed_at=NOW,
        )

        self.assertEqual(link.status, EvidenceLinkStatus.REJECTED)
        self.assertEqual(link.match_score, 72)


if __name__ == "__main__":
    unittest.main()
