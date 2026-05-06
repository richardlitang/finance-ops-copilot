from __future__ import annotations

from datetime import datetime, timezone
import json

from app.domain import (
    AuditActor,
    AuditEvent,
    AuditEventType,
    ConfirmationStatus,
    Category,
    Direction,
    EvidenceLink,
    EvidenceLinkStatus,
    EvidenceLinkType,
    EvidenceRecord,
    EvidenceType,
    LifecycleStatus,
    ReviewReason,
    ReviewStatus,
    SourceDocument,
    SourceDocumentStatus,
    SourceQuality,
    SourceType,
    SpendingEvent,
)
from app.domain.models import MatchCandidate
from app.services.categorization import MappingRule, PatternType

from .models import (
    AuditEventRow,
    CategoryRow,
    EvidenceLinkRow,
    EvidenceRecordRow,
    MappingRuleRow,
    MatchCandidateRow,
    SourceDocumentRow,
    SpendingEventRow,
)


def source_document_to_row(value: SourceDocument) -> SourceDocumentRow:
    return SourceDocumentRow(
        id=value.id,
        source_type=value.source_type.value,
        status=value.status.value,
        filename=value.filename,
        raw_text=value.raw_text,
        file_path=value.file_path,
        fingerprint=value.fingerprint,
        created_at=value.created_at,
    )


def source_document_from_row(row: SourceDocumentRow) -> SourceDocument:
    return SourceDocument(
        id=row.id,
        source_type=SourceType(row.source_type),
        status=SourceDocumentStatus(row.status),
        filename=row.filename,
        raw_text=row.raw_text,
        file_path=row.file_path,
        fingerprint=row.fingerprint,
        created_at=_utc(row.created_at),
    )


def evidence_record_to_row(value: EvidenceRecord) -> EvidenceRecordRow:
    return EvidenceRecordRow(
        id=value.id,
        source_document_id=value.source_document_id,
        evidence_type=value.evidence_type.value,
        merchant_raw=value.merchant_raw,
        merchant_normalized=value.merchant_normalized,
        occurred_at=value.occurred_at,
        posted_at=value.posted_at,
        amount_minor=value.amount_minor,
        currency=value.currency,
        description_raw=value.description_raw,
        extraction_confidence=int(value.extraction_confidence * 100),
        fingerprint=value.fingerprint,
        raw_payload_json=value.raw_payload_json,
        warnings="\n".join(value.warnings),
        created_at=value.created_at,
    )


def evidence_record_from_row(row: EvidenceRecordRow) -> EvidenceRecord:
    return EvidenceRecord(
        id=row.id,
        source_document_id=row.source_document_id,
        evidence_type=EvidenceType(row.evidence_type),
        merchant_raw=row.merchant_raw,
        merchant_normalized=row.merchant_normalized,
        occurred_at=_utc(row.occurred_at),
        posted_at=_utc(row.posted_at),
        amount_minor=row.amount_minor,
        currency=row.currency,
        description_raw=row.description_raw,
        extraction_confidence=row.extraction_confidence / 100,
        fingerprint=row.fingerprint,
        raw_payload_json=row.raw_payload_json,
        warnings=tuple(item for item in row.warnings.splitlines() if item),
        created_at=_utc(row.created_at),
    )


def spending_event_to_row(value: SpendingEvent) -> SpendingEventRow:
    return SpendingEventRow(
        id=value.id,
        occurred_at=value.occurred_at,
        posted_at=value.posted_at,
        merchant_normalized=value.merchant_normalized,
        amount_minor=value.amount_minor,
        currency=value.currency,
        direction=value.direction.value,
        category_id=value.category_id,
        confirmation_status=value.confirmation_status.value,
        review_status=value.review_status.value,
        review_reasons="\n".join(reason.value for reason in value.review_reasons),
        lifecycle_status=value.lifecycle_status.value,
        source_quality=value.source_quality.value,
        canonical_source_evidence_id=value.canonical_source_evidence_id,
        created_at=value.created_at,
        updated_at=value.updated_at,
    )


def spending_event_from_row(row: SpendingEventRow) -> SpendingEvent:
    return SpendingEvent(
        id=row.id,
        occurred_at=_utc(row.occurred_at),
        posted_at=_utc(row.posted_at),
        merchant_normalized=row.merchant_normalized,
        amount_minor=row.amount_minor,
        currency=row.currency,
        direction=Direction(row.direction),
        category_id=row.category_id,
        confirmation_status=ConfirmationStatus(row.confirmation_status),
        review_status=ReviewStatus(row.review_status),
        review_reasons=tuple(ReviewReason(item) for item in row.review_reasons.splitlines() if item),
        lifecycle_status=LifecycleStatus(row.lifecycle_status),
        source_quality=SourceQuality(row.source_quality),
        canonical_source_evidence_id=row.canonical_source_evidence_id,
        created_at=_utc(row.created_at),
        updated_at=_utc(row.updated_at),
    )


def evidence_link_to_row(value: EvidenceLink) -> EvidenceLinkRow:
    return EvidenceLinkRow(
        id=value.id,
        spending_event_id=value.spending_event_id,
        evidence_record_id=value.evidence_record_id,
        link_type=value.link_type.value,
        status=value.status.value,
        match_score=value.match_score,
        created_at=value.created_at,
    )


def evidence_link_from_row(row: EvidenceLinkRow) -> EvidenceLink:
    return EvidenceLink(
        id=row.id,
        spending_event_id=row.spending_event_id,
        evidence_record_id=row.evidence_record_id,
        link_type=EvidenceLinkType(row.link_type),
        status=EvidenceLinkStatus(row.status),
        match_score=row.match_score,
        created_at=_utc(row.created_at),
    )


def match_candidate_to_row(value: MatchCandidate) -> MatchCandidateRow:
    return MatchCandidateRow(
        id=value.id,
        spending_event_id=value.spending_event_id,
        statement_evidence_record_id=value.statement_evidence_record_id,
        score=value.score,
        decision=value.decision,
        reasons="\n".join(value.reasons),
        created_at=value.created_at,
    )


def match_candidate_from_row(row: MatchCandidateRow) -> MatchCandidate:
    return MatchCandidate(
        id=row.id,
        spending_event_id=row.spending_event_id,
        statement_evidence_record_id=row.statement_evidence_record_id,
        score=row.score,
        decision=row.decision,
        reasons=tuple(item for item in row.reasons.splitlines() if item),
        created_at=_utc(row.created_at),
    )


def category_to_row(value: Category) -> CategoryRow:
    return CategoryRow(id=value.id, name=value.name, created_at=value.created_at)


def category_from_row(row: CategoryRow) -> Category:
    return Category(id=row.id, name=row.name, created_at=_utc(row.created_at))


def mapping_rule_to_row(value: MappingRule) -> MappingRuleRow:
    return MappingRuleRow(
        id=value.id,
        pattern=value.pattern,
        pattern_type=value.pattern_type.value,
        category_id=value.category_id,
        priority=value.priority,
        created_from_review=1 if value.created_from_review else 0,
        created_at=value.created_at,
    )


def mapping_rule_from_row(row: MappingRuleRow) -> MappingRule:
    return MappingRule(
        id=row.id,
        pattern=row.pattern,
        pattern_type=PatternType(row.pattern_type),
        category_id=row.category_id,
        priority=row.priority,
        created_from_review=bool(row.created_from_review),
        created_at=_utc(row.created_at),
    )


def audit_event_to_row(value: AuditEvent) -> AuditEventRow:
    return AuditEventRow(
        id=value.id,
        entity_type=value.entity_type,
        entity_id=value.entity_id,
        event_type=value.event_type.value,
        actor=value.actor.value,
        payload_json=json.dumps(value.payload, sort_keys=True),
        created_at=value.created_at,
    )


def audit_event_from_row(row: AuditEventRow) -> AuditEvent:
    return AuditEvent(
        id=row.id,
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        event_type=AuditEventType(row.event_type),
        actor=AuditActor(row.actor),
        payload=json.loads(row.payload_json),
        created_at=_utc(row.created_at),
    )


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
