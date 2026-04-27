from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.domain import Category
from app.repositories import InMemoryFinanceRepository
from app.schemas.categories import (
    CategoryCreateRequest,
    CategoryResponse,
    MappingRuleCreateRequest,
    MappingRuleResponse,
)
from app.services.categorization import MappingRule, PatternType

from .dependencies import get_repository


router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> list[CategoryResponse]:
    return [CategoryResponse.from_domain(category) for category in repository.list_categories()]


@router.post("", response_model=CategoryResponse)
def create_category(
    request: CategoryCreateRequest,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> CategoryResponse:
    category = Category(
        id=repository.next_id("category"),
        name=request.name,
        created_at=datetime.now(timezone.utc),
    )
    saved = repository.save_category(category)
    return CategoryResponse.from_domain(saved)


@router.get("/rules", response_model=list[MappingRuleResponse])
def list_mapping_rules(
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> list[MappingRuleResponse]:
    return [MappingRuleResponse.from_domain(rule) for rule in repository.list_mapping_rules()]


@router.post("/rules", response_model=MappingRuleResponse)
def create_mapping_rule(
    request: MappingRuleCreateRequest,
    repository: InMemoryFinanceRepository = Depends(get_repository),
) -> MappingRuleResponse:
    rule = MappingRule(
        id=repository.next_id("mapping_rule"),
        pattern=request.pattern,
        pattern_type=PatternType(request.pattern_type),
        category_id=request.category_id,
        priority=request.priority,
        created_from_review=request.created_from_review,
        created_at=datetime.now(timezone.utc),
    )
    saved = repository.save_mapping_rule(rule)
    return MappingRuleResponse.from_domain(saved)
