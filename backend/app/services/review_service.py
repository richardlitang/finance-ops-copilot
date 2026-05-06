from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain import (
    ConfirmationStatus,
    Direction,
    EvidenceLink,
    EvidenceLinkStatus,
    EvidenceLinkType,
    LifecycleStatus,
    ReviewReason,
    ReviewStatus,
    SourceQuality,
    SpendingEvent,
)
from app.domain.models import EvidenceRecord, MatchCandidate


@dataclass(frozen=True, slots=True)
class ReviewActionResult:
    spending_event: SpendingEvent
    evidence_link: EvidenceLink | None = None


def confirm_receipt_as_manual(event: SpendingEvent, *, reviewed_at: datetime) -> SpendingEvent:
    if event.lifecycle_status is not LifecycleStatus.ACTIVE:
        raise ValueError("only active events can be manually confirmed")
    return event.with_updates(
        confirmation_status=ConfirmationStatus.MANUAL_CONFIRMED,
        review_status=ReviewStatus.RESOLVED,
        review_reasons=(),
        source_quality=SourceQuality.MANUAL,
        updated_at=reviewed_at,
    )


def mark_event_duplicate(event: SpendingEvent, *, reviewed_at: datetime) -> SpendingEvent:
    return event.with_updates(
        lifecycle_status=LifecycleStatus.DUPLICATE,
        review_status=ReviewStatus.RESOLVED,
        review_reasons=(),
        updated_at=reviewed_at,
    )


def ignore_event(event: SpendingEvent, *, reviewed_at: datetime) -> SpendingEvent:
    return event.with_updates(
        lifecycle_status=LifecycleStatus.IGNORED,
        review_status=ReviewStatus.RESOLVED,
        review_reasons=(),
        updated_at=reviewed_at,
    )


def reject_match_candidate(candidate: MatchCandidate, *, reviewed_at: datetime) -> EvidenceLink:
    return EvidenceLink(
        id=f"rejected_{candidate.id}",
        spending_event_id=candidate.spending_event_id,
        evidence_record_id=candidate.statement_evidence_record_id,
        link_type=EvidenceLinkType.MATCHED_TO,
        status=EvidenceLinkStatus.REJECTED,
        match_score=candidate.score,
        created_at=reviewed_at,
    )


def create_statement_only_event_from_evidence(
    evidence: EvidenceRecord,
    *,
    event_id: str,
    reviewed_at: datetime,
) -> SpendingEvent:
    if evidence.amount_minor is None:
        raise ValueError("statement evidence must include amount_minor")
    if evidence.currency is None:
        raise ValueError("statement evidence must include currency")
    return SpendingEvent(
        id=event_id,
        occurred_at=evidence.occurred_at or reviewed_at,
        posted_at=evidence.posted_at,
        merchant_normalized=evidence.merchant_normalized or evidence.merchant_raw or "Unknown Merchant",
        amount_minor=evidence.amount_minor,
        currency=evidence.currency,
        direction=Direction.EXPENSE if evidence.amount_minor >= 0 else Direction.INCOME,
        confirmation_status=ConfirmationStatus.CONFIRMED,
        review_status=ReviewStatus.CLEAR if not evidence.warnings else ReviewStatus.NEEDS_REVIEW,
        lifecycle_status=LifecycleStatus.ACTIVE,
        source_quality=SourceQuality.STATEMENT_ONLY,
        created_at=reviewed_at,
        updated_at=reviewed_at,
        canonical_source_evidence_id=evidence.id,
        review_reasons=_review_reasons_for_evidence(evidence),
    )


def _review_reasons_for_evidence(evidence: EvidenceRecord) -> tuple[ReviewReason, ...]:
    reasons: list[ReviewReason] = []
    if evidence.warnings:
        reasons.append(ReviewReason.PARSE_WARNING)
        if any("missing" in warning.lower() for warning in evidence.warnings):
            reasons.append(ReviewReason.MISSING_REQUIRED_FIELD)
    return tuple(reasons)
