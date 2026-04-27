from __future__ import annotations

from datetime import datetime

from .enums import (
    ConfirmationStatus,
    EvidenceLinkStatus,
    EvidenceLinkType,
    EvidenceType,
    LifecycleStatus,
    ReviewStatus,
    SourceQuality,
)
from .models import EvidenceLink, EvidenceRecord, SpendingEvent


class ReconciliationError(ValueError):
    pass


def apply_statement_confirmation(
    event: SpendingEvent,
    statement: EvidenceRecord,
    *,
    link_id: str,
    matched_at: datetime,
    match_score: int,
) -> tuple[SpendingEvent, EvidenceLink]:
    """Return a confirmed event and link without mutating source evidence."""
    if statement.evidence_type is not EvidenceType.STATEMENT_ROW:
        raise ReconciliationError("statement confirmation requires statement row evidence")
    if event.lifecycle_status is not LifecycleStatus.ACTIVE:
        raise ReconciliationError("only active events can be statement-confirmed")
    if statement.amount_minor is None:
        raise ReconciliationError("statement evidence must include amount_minor")
    if statement.currency is None:
        raise ReconciliationError("statement evidence must include currency")

    confirmed_event = event.with_updates(
        amount_minor=statement.amount_minor,
        currency=statement.currency,
        merchant_normalized=statement.merchant_normalized or event.merchant_normalized,
        posted_at=statement.posted_at or event.posted_at,
        confirmation_status=ConfirmationStatus.CONFIRMED,
        review_status=ReviewStatus.CLEAR,
        source_quality=SourceQuality.RECEIPT_AND_STATEMENT,
        canonical_source_evidence_id=statement.id,
        updated_at=matched_at,
    )
    link = EvidenceLink(
        id=link_id,
        spending_event_id=event.id,
        evidence_record_id=statement.id,
        link_type=EvidenceLinkType.STATEMENT_CONFIRMATION,
        status=EvidenceLinkStatus.CONFIRMED,
        match_score=match_score,
        created_at=matched_at,
    )
    return confirmed_event, link
