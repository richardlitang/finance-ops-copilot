from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.models import EvidenceRecord, SpendingEvent


class PatternType(StrEnum):
    MERCHANT = "merchant"
    DESCRIPTION = "description"
    SOURCE = "source"


@dataclass(frozen=True, slots=True)
class MappingRule:
    id: str
    pattern: str
    pattern_type: PatternType
    category_id: str
    priority: int
    created_from_review: bool = False
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class CategoryDecision:
    category_id: str | None
    rule_id: str | None
    needs_review: bool


def categorize_event(
    event: SpendingEvent,
    evidence: EvidenceRecord,
    rules: list[MappingRule],
) -> CategoryDecision:
    ordered = sorted(rules, key=lambda rule: rule.priority, reverse=True)
    for rule in ordered:
        haystack = _value_for_rule(rule.pattern_type, event, evidence)
        if rule.pattern.lower() in haystack.lower():
            return CategoryDecision(
                category_id=rule.category_id,
                rule_id=rule.id,
                needs_review=False,
            )
    return CategoryDecision(category_id=None, rule_id=None, needs_review=True)


def _value_for_rule(
    pattern_type: PatternType,
    event: SpendingEvent,
    evidence: EvidenceRecord,
) -> str:
    if pattern_type is PatternType.MERCHANT:
        return event.merchant_normalized
    if pattern_type is PatternType.DESCRIPTION:
        return evidence.description_raw or ""
    if pattern_type is PatternType.SOURCE:
        return evidence.source_document_id
    raise ValueError(f"unsupported pattern type: {pattern_type}")
