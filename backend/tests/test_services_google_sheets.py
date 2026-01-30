from datetime import datetime, timezone

from app.domain import (
    Category,
    ConfirmationStatus,
    Direction,
    EvidenceRecord,
    EvidenceType,
    LifecycleStatus,
    ReviewStatus,
    SourceDocument,
    SourceDocumentStatus,
    SourceQuality,
    SourceType,
    SpendingEvent,
)
from app.repositories import InMemoryFinanceRepository
from app.services.categorization import MappingRule, PatternType
from app.services.google_sheets import GoogleSheetsService
from app.services.summary import AnalysisMode


NOW = datetime(2026, 4, 17, tzinfo=timezone.utc)


class InMemorySheetsGateway:
    def __init__(self) -> None:
        self.writes: list[tuple[str, list[dict[str, object]], str]] = []

    def upsert_rows(self, tab: str, rows: list[dict[str, object]], key_field: str) -> None:
        self.writes.append((tab, rows, key_field))


def build_repository() -> InMemoryFinanceRepository:
    repository = InMemoryFinanceRepository()
    repository.save_category(Category(id="cat_groceries", name="Groceries", created_at=NOW))
    repository.save_mapping_rule(
        MappingRule(
            id="rule_1",
            pattern="Aldi",
            pattern_type=PatternType.MERCHANT,
            category_id="cat_groceries",
            priority=100,
            created_from_review=False,
            created_at=NOW,
        )
    )
    repository.save_source_document(
        SourceDocument(
            id="src_1",
            source_type=SourceType.RECEIPT_TEXT,
            status=SourceDocumentStatus.PARSED,
            created_at=NOW,
            raw_text="receipt",
            fingerprint="src-fingerprint",
        )
    )
    repository.save_evidence_record(
        EvidenceRecord(
            id="ev_1",
            source_document_id="src_1",
            evidence_type=EvidenceType.RECEIPT,
            merchant_normalized="Aldi",
            occurred_at=NOW,
            amount_minor=4297,
            currency="EUR",
            extraction_confidence=1.0,
            fingerprint="ev-fingerprint",
            created_at=NOW,
        )
    )
    repository.save_spending_event(
        SpendingEvent(
            id="evt_approved",
            occurred_at=NOW,
            merchant_normalized="Aldi",
            amount_minor=4297,
            currency="EUR",
            direction=Direction.EXPENSE,
            confirmation_status=ConfirmationStatus.CONFIRMED,
            review_status=ReviewStatus.CLEAR,
            lifecycle_status=LifecycleStatus.ACTIVE,
            source_quality=SourceQuality.RECEIPT_AND_STATEMENT,
            created_at=NOW,
            updated_at=NOW,
            category_id="cat_groceries",
            canonical_source_evidence_id="ev_1",
        )
    )
    repository.save_spending_event(
        SpendingEvent(
            id="evt_review",
            occurred_at=NOW,
            merchant_normalized="Unknown Merchant",
            amount_minor=1599,
            currency="EUR",
            direction=Direction.EXPENSE,
            confirmation_status=ConfirmationStatus.PROVISIONAL,
            review_status=ReviewStatus.NEEDS_REVIEW,
            lifecycle_status=LifecycleStatus.ACTIVE,
            source_quality=SourceQuality.RECEIPT_ONLY,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    return repository


def test_google_sheets_service_syncs_exportable_events_review_queue_rules_and_summary():
    gateway = InMemorySheetsGateway()
    service = GoogleSheetsService(gateway)
    repository = build_repository()

    result = service.sync_all(repository=repository, month="2026-04", mode=AnalysisMode.FAST, exported_at=NOW)

    assert result.normalized_entries == 1
    assert result.review_queue == 1
    assert result.mapping_rules == 1
    assert result.monthly_summary >= 3

    writes = {tab: rows for tab, rows, _ in gateway.writes}
    assert writes["normalized_entries"][0]["entry_id"] == "evt_approved"
    assert writes["normalized_entries"][0]["source_type"] == "receipt_text"
    assert writes["review_queue"][0]["entry_id"] == "evt_review"
    assert writes["review_queue"][0]["issue_type"] == "unmatched_receipt"
    assert writes["mapping_rules"][0]["rule_id"] == "rule_1"
    summary_keys = {row["metric_key"] for row in writes["monthly_summary"]}
    assert "2026-04:Groceries" in summary_keys
    assert "2026-04:Aldi" in summary_keys
    assert "2026-04:EUR" in summary_keys
