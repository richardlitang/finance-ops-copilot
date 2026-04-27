from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.domain import EvidenceLink
from app.domain.models import MatchCandidate
from app.schemas.events import SpendingEventResponse


class EvidenceLinkResponse(BaseModel):
    id: str
    spending_event_id: str
    evidence_record_id: str
    link_type: str
    status: str
    match_score: int | None
    created_at: datetime

    @classmethod
    def from_domain(cls, link: EvidenceLink) -> EvidenceLinkResponse:
        return cls(
            id=link.id,
            spending_event_id=link.spending_event_id,
            evidence_record_id=link.evidence_record_id,
            link_type=link.link_type.value,
            status=link.status.value,
            match_score=link.match_score,
            created_at=link.created_at,
        )


class MatchCandidateResponse(BaseModel):
    id: str
    spending_event_id: str
    statement_evidence_record_id: str
    score: int
    decision: str
    reasons: list[str]
    created_at: datetime

    @classmethod
    def from_domain(cls, candidate: MatchCandidate) -> MatchCandidateResponse:
        return cls(
            id=candidate.id,
            spending_event_id=candidate.spending_event_id,
            statement_evidence_record_id=candidate.statement_evidence_record_id,
            score=candidate.score,
            decision=candidate.decision,
            reasons=list(candidate.reasons),
            created_at=candidate.created_at,
        )


class ReviewActionResponse(BaseModel):
    spending_event: SpendingEventResponse
    evidence_link: EvidenceLinkResponse | None = None


class CategoryCorrectionRequest(BaseModel):
    category_id: str = Field(min_length=1)
    create_mapping_rule: bool = False

    @field_validator("category_id")
    @classmethod
    def normalize_category_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("category id is required")
        return normalized
