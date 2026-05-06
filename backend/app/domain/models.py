from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any

from .enums import (
    AuditActor,
    AuditEventType,
    ConfirmationStatus,
    Direction,
    EvidenceLinkStatus,
    EvidenceLinkType,
    EvidenceType,
    LifecycleStatus,
    ReviewReason,
    ReviewStatus,
    SourceDocumentStatus,
    SourceQuality,
    SourceType,
)


@dataclass(frozen=True, slots=True)
class SourceDocument:
    id: str
    source_type: SourceType
    status: SourceDocumentStatus
    created_at: datetime
    filename: str | None = None
    raw_text: str | None = None
    file_path: str | None = None
    fingerprint: str | None = None


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    id: str
    source_document_id: str
    evidence_type: EvidenceType
    extraction_confidence: float
    fingerprint: str
    created_at: datetime
    merchant_raw: str | None = None
    merchant_normalized: str | None = None
    occurred_at: datetime | None = None
    posted_at: datetime | None = None
    amount_minor: int | None = None
    currency: str | None = None
    description_raw: str | None = None
    raw_payload_json: str | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class SpendingEvent:
    id: str
    occurred_at: datetime
    merchant_normalized: str
    amount_minor: int
    currency: str
    direction: Direction
    confirmation_status: ConfirmationStatus
    review_status: ReviewStatus
    lifecycle_status: LifecycleStatus
    source_quality: SourceQuality
    created_at: datetime
    updated_at: datetime
    posted_at: datetime | None = None
    category_id: str | None = None
    canonical_source_evidence_id: str | None = None
    review_reasons: tuple[ReviewReason, ...] = field(default_factory=tuple)

    def with_updates(self, **changes: object) -> SpendingEvent:
        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class EvidenceLink:
    id: str
    spending_event_id: str
    evidence_record_id: str
    link_type: EvidenceLinkType
    status: EvidenceLinkStatus
    created_at: datetime
    match_score: int | None = None


@dataclass(frozen=True, slots=True)
class MatchCandidate:
    id: str
    spending_event_id: str
    statement_evidence_record_id: str
    score: int
    decision: str
    reasons: tuple[str, ...]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Category:
    id: str
    name: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AuditEvent:
    id: str
    entity_type: str
    entity_id: str
    event_type: AuditEventType
    actor: AuditActor
    payload: dict[str, Any]
    created_at: datetime
