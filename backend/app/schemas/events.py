from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.domain import EvidenceLink, EvidenceRecord, SpendingEvent
from app.domain.models import MatchCandidate


class SpendingEventResponse(BaseModel):
    id: str
    occurred_at: datetime
    posted_at: datetime | None
    merchant_normalized: str
    amount_minor: int
    currency: str
    direction: str
    category_id: str | None
    confirmation_status: str
    review_status: str
    lifecycle_status: str
    source_quality: str
    canonical_source_evidence_id: str | None

    @classmethod
    def from_domain(cls, event: SpendingEvent) -> SpendingEventResponse:
        return cls(
            id=event.id,
            occurred_at=event.occurred_at,
            posted_at=event.posted_at,
            merchant_normalized=event.merchant_normalized,
            amount_minor=event.amount_minor,
            currency=event.currency,
            direction=event.direction.value,
            category_id=event.category_id,
            confirmation_status=event.confirmation_status.value,
            review_status=event.review_status.value,
            lifecycle_status=event.lifecycle_status.value,
            source_quality=event.source_quality.value,
            canonical_source_evidence_id=event.canonical_source_evidence_id,
        )


class EvidenceRecordResponse(BaseModel):
    id: str
    source_document_id: str
    evidence_type: str
    merchant_raw: str | None
    merchant_normalized: str | None
    occurred_at: datetime | None
    posted_at: datetime | None
    amount_minor: int | None
    currency: str | None
    description_raw: str | None
    extraction_confidence: float
    warnings: list[str]
    created_at: datetime

    @classmethod
    def from_domain(cls, evidence: EvidenceRecord) -> "EvidenceRecordResponse":
        return cls(
            id=evidence.id,
            source_document_id=evidence.source_document_id,
            evidence_type=evidence.evidence_type.value,
            merchant_raw=evidence.merchant_raw,
            merchant_normalized=evidence.merchant_normalized,
            occurred_at=evidence.occurred_at,
            posted_at=evidence.posted_at,
            amount_minor=evidence.amount_minor,
            currency=evidence.currency,
            description_raw=evidence.description_raw,
            extraction_confidence=evidence.extraction_confidence,
            warnings=list(evidence.warnings),
            created_at=evidence.created_at,
        )


class EventEvidenceLinkResponse(BaseModel):
    id: str
    link_type: str
    status: str
    match_score: int | None
    created_at: datetime
    evidence: EvidenceRecordResponse

    @classmethod
    def from_domain(
        cls,
        link: EvidenceLink,
        evidence: EvidenceRecord,
    ) -> "EventEvidenceLinkResponse":
        return cls(
            id=link.id,
            link_type=link.link_type.value,
            status=link.status.value,
            match_score=link.match_score,
            created_at=link.created_at,
            evidence=EvidenceRecordResponse.from_domain(evidence),
        )


class EventMatchCandidateResponse(BaseModel):
    id: str
    statement_evidence_record_id: str
    score: int
    decision: str
    reasons: list[str]
    created_at: datetime

    @classmethod
    def from_domain(cls, candidate: MatchCandidate) -> "EventMatchCandidateResponse":
        return cls(
            id=candidate.id,
            statement_evidence_record_id=candidate.statement_evidence_record_id,
            score=candidate.score,
            decision=candidate.decision,
            reasons=list(candidate.reasons),
            created_at=candidate.created_at,
        )


class EventEvidenceResponse(BaseModel):
    event: SpendingEventResponse
    linked_evidence: list[EventEvidenceLinkResponse]
    match_candidates: list[EventMatchCandidateResponse]
