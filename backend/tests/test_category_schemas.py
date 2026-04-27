from datetime import datetime, timezone

from app.domain import Category
from app.schemas.categories import CategoryResponse


def test_category_response_serializes_category_domain_entity():
    category = Category(
        id="cat_groceries",
        name="Groceries",
        created_at=datetime(2026, 4, 27, tzinfo=timezone.utc),
    )

    response = CategoryResponse.from_domain(category)

    assert response.id == "cat_groceries"
    assert response.name == "Groceries"
