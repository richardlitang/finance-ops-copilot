from app.main import create_app
from app.repositories import InMemoryFinanceRepository, SqlAlchemyFinanceRepository


def test_create_app_defaults_to_in_memory_repository():
    app = create_app()

    assert isinstance(app.state.repository, InMemoryFinanceRepository)


def test_create_app_uses_sqlalchemy_repository_when_database_url_is_provided():
    app = create_app("sqlite+pysqlite:///:memory:")

    assert isinstance(app.state.repository, SqlAlchemyFinanceRepository)
