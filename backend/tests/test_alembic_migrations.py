from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_initial_migration_creates_core_tables(tmp_path):
    database_path = tmp_path / "finance.sqlite"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite+pysqlite:///{database_path}")

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite+pysqlite:///{database_path}")
    table_names = set(inspect(engine).get_table_names())
    assert "source_documents" in table_names
    assert "evidence_records" in table_names
    assert "spending_events" in table_names
    assert "categories" in table_names
    assert "mapping_rules" in table_names
