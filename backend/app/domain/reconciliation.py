from __future__ import annotations

from datetime import datetime
from difflib import SequenceMatcher

from .enums import (
    ConfirmationStatus,
    EvidenceLinkStatus,
    EvidenceLinkType,
    EvidenceType,
    LifecycleStatus,
    ReviewStatus,
    SourceQuality,
)
from .models import EvidenceLink, EvidenceRecord, MatchCandidate, SpendingEvent


class ReconciliationError(ValueError):
    pass


def score_statement_match(event: SpendingEvent, statement: EvidenceRecord) -> tuple[int, tuple[str, ...]]:
    score = 0
    reasons: list[str] = []

    if statement.amount_minor == event.amount_minor:
        score += 50
        reasons.append("exact_amount")
    else:
        score -= 30
        reasons.append("amount_mismatch")

    if statement.currency == event.currency:
        score += 10
        reasons.append("same_currency")

    if statement.occurred_at and statement.occurred_at.date() == event.occurred_at.date():
        score += 20
        reasons.append("same_date")
    elif statement.occurred_at:
        day_gap = abs((statement.occurred_at.date() - event.occurred_at.date()).days)
        if day_gap <= 3:
            score += 10
            reasons.append("nearby_date")

    merchant_similarity = _similarity(event.merchant_normalized, statement.merchant_normalized or "")
    if merchant_similarity >= 0.8:
        score += 20
        reasons.append("high_merchant_similarity")

    if event.confirmation_status is ConfirmationStatus.CONFIRMED:
        score -= 40
        reasons.append("already_statement_confirmed")

    return score, tuple(reasons)


def build_match_candidate(
    *,
    candidate_id: str,
    event: SpendingEvent,
    statement: EvidenceRecord,
    created_at: datetime,
) -> MatchCandidate:
    score, reasons = score_statement_match(event, statement)
    if score >= 80:
        decision = "auto_confirm"
    elif score >= 50:
        decision = "needs_review"
    else:
        decision = "no_match"
    return MatchCandidate(
        id=candidate_id,
        spending_event_id=event.id,
        statement_evidence_record_id=statement.id,
        score=score,
        decision=decision,
        reasons=reasons,
        created_at=created_at,
    )


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


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left.lower(), right.lower()).ratio()
