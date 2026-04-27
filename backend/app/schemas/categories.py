from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.domain import Category
from app.services.categorization import MappingRule, PatternType


class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("category name is required")
        return normalized


class CategoryResponse(BaseModel):
    id: str
    name: str
    created_at: datetime

    @classmethod
    def from_domain(cls, category: Category) -> CategoryResponse:
        return cls(id=category.id, name=category.name, created_at=category.created_at)


class MappingRuleCreateRequest(BaseModel):
    pattern: str = Field(min_length=1, max_length=240)
    pattern_type: PatternType
    category_id: str = Field(min_length=1)
    priority: int = Field(default=100, ge=0, le=1000)
    created_from_review: bool = False

    @field_validator("pattern", "category_id")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value is required")
        return normalized


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
