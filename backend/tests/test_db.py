from sqlalchemy import text

from app.db import create_db_engine, create_session_factory


def test_create_session_factory_executes_sqlite_query():
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        result = session.execute(text("select 1")).scalar_one()

    assert result == 1
