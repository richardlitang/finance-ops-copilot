from datetime import datetime, timezone

from app.domain import Category


def test_category_is_first_class_domain_entity():
    category = Category(
        id="cat_groceries",
        name="Groceries",
        created_at=datetime(2026, 4, 27, tzinfo=timezone.utc),
    )

    assert category.id == "cat_groceries"
    assert category.name == "Groceries"
