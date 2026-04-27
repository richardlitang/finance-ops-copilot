from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.domain import Category
from app.services.categorization import MappingRule


class CategoryCreateRequest(BaseModel):
    name: str


class CategoryResponse(BaseModel):
    id: str
    name: str
    created_at: datetime

    @classmethod
    def from_domain(cls, category: Category) -> CategoryResponse:
        return cls(id=category.id, name=category.name, created_at=category.created_at)


class MappingRuleCreateRequest(BaseModel):
    pattern: str
    pattern_type: str
    category_id: str
    priority: int = 100
    created_from_review: bool = False


class MappingRuleResponse(BaseModel):
    id: str
    pattern: str
    pattern_type: str
    category_id: str
    priority: int
    created_from_review: bool
    created_at: datetime | None

    @classmethod
    def from_domain(cls, rule: MappingRule) -> MappingRuleResponse:
        return cls(
            id=rule.id,
            pattern=rule.pattern,
            pattern_type=rule.pattern_type.value,
            category_id=rule.category_id,
            priority=rule.priority,
            created_from_review=rule.created_from_review,
            created_at=rule.created_at,
        )

