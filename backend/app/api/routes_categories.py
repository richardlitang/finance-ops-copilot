from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.domain import Category
from app.repositories import InMemoryFinanceRepository
from app.schemas.categories import CategoryCreateRequest, CategoryResponse

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

