from datetime import datetime, timezone

from app.db import create_db_engine, create_session_factory
from app.domain import Category
from app.repositories import InMemoryFinanceRepository, SqlAlchemyFinanceRepository
from app.services.categorization import MappingRule, PatternType


NOW = datetime(2026, 4, 27, tzinfo=timezone.utc)


def sql_repository() -> SqlAlchemyFinanceRepository:
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    repo = SqlAlchemyFinanceRepository(create_session_factory(engine))
    repo.create_schema()
    return repo


def assert_category_rule_repository(repo):
    category = Category(id="cat_groceries", name="Groceries", created_at=NOW)
    rule = MappingRule(
        id="rule_aldi",
        pattern="Aldi",
        pattern_type=PatternType.MERCHANT,
        category_id=category.id,
        priority=100,
        created_from_review=True,
        created_at=NOW,
    )

    repo.save_category(category)
    repo.save_mapping_rule(rule)

    assert repo.list_categories() == [category]
    assert repo.list_mapping_rules() == [rule]


def test_memory_repository_persists_categories_and_mapping_rules():
    assert_category_rule_repository(InMemoryFinanceRepository())


def test_sql_repository_persists_categories_and_mapping_rules():
    assert_category_rule_repository(sql_repository())
