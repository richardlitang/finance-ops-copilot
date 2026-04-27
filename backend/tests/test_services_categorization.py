from datetime import datetime, timezone
import unittest

from app.domain import (
    ConfirmationStatus,
    Direction,
    EvidenceType,
    LifecycleStatus,
    ReviewStatus,
    SourceQuality,
)
from app.domain.models import EvidenceRecord, SpendingEvent
from app.services.categorization import MappingRule, PatternType, categorize_event


NOW = datetime(2026, 4, 17, tzinfo=timezone.utc)


class CategorizationTests(unittest.TestCase):
    def test_categorize_event_applies_highest_priority_matching_rule(self):
        event = SpendingEvent(
            id="evt_1",
            occurred_at=NOW,
            merchant_normalized="Aldi Be",
            amount_minor=4297,
            currency="EUR",
            direction=Direction.EXPENSE,
            confirmation_status=ConfirmationStatus.PROVISIONAL,
            review_status=ReviewStatus.CLEAR,
            lifecycle_status=LifecycleStatus.ACTIVE,
            source_quality=SourceQuality.RECEIPT_ONLY,
            created_at=NOW,
            updated_at=NOW,
        )
        evidence = EvidenceRecord(
            id="ev_1",
            source_document_id="src_1",
            evidence_type=EvidenceType.RECEIPT,
            extraction_confidence=1.0,
            fingerprint="fp",
            created_at=NOW,
        )
        rules = [
            MappingRule("rule_low", "Aldi", PatternType.MERCHANT, "shopping", priority=10),
            MappingRule("rule_high", "Aldi", PatternType.MERCHANT, "groceries", priority=100),
        ]

        decision = categorize_event(event, evidence, rules)

        self.assertEqual(decision.category_id, "groceries")
        self.assertEqual(decision.rule_id, "rule_high")
        self.assertFalse(decision.needs_review)

    def test_categorize_event_routes_unknown_category_to_review(self):
        event = SpendingEvent(
            id="evt_1",
            occurred_at=NOW,
            merchant_normalized="Unknown Shop",
            amount_minor=4297,
            currency="EUR",
            direction=Direction.EXPENSE,
            confirmation_status=ConfirmationStatus.PROVISIONAL,
            review_status=ReviewStatus.CLEAR,
            lifecycle_status=LifecycleStatus.ACTIVE,
            source_quality=SourceQuality.RECEIPT_ONLY,
            created_at=NOW,
            updated_at=NOW,
        )
        evidence = EvidenceRecord(
            id="ev_1",
            source_document_id="src_1",
            evidence_type=EvidenceType.RECEIPT,
            extraction_confidence=1.0,
            fingerprint="fp",
            created_at=NOW,
        )

        decision = categorize_event(event, evidence, [])

        self.assertIsNone(decision.category_id)
        self.assertTrue(decision.needs_review)


if __name__ == "__main__":
    unittest.main()
