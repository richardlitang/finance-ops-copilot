from sqlalchemy import inspect

from app.db import Base, create_db_engine
from app.orm import CategoryRow, EvidenceRecordRow, SourceDocumentRow, SpendingEventRow


def test_core_tables_are_registered_on_metadata():
    table_names = set(Base.metadata.tables.keys())

    assert "source_documents" in table_names
    assert "evidence_records" in table_names
    assert "spending_events" in table_names


def test_core_tables_create_in_sqlite():
    engine = create_db_engine("sqlite+pysqlite:///:memory:")

    Base.metadata.create_all(engine)

    table_names = set(inspect(engine).get_table_names())
    assert SourceDocumentRow.__tablename__ in table_names
    assert EvidenceRecordRow.__tablename__ in table_names
    assert SpendingEventRow.__tablename__ in table_names
    assert CategoryRow.__tablename__ in table_names
