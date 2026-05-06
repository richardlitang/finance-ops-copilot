from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain import (
    ConfirmationStatus,
    EvidenceLink,
    EvidenceLinkStatus,
    EvidenceLinkType,
    LifecycleStatus,
    ReviewStatus,
    SourceQuality,
    SpendingEvent,
)
from app.domain.models import MatchCandidate


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
