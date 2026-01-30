import os

from sqlalchemy.orm import sessionmaker

from fastapi import FastAPI

from app.api.routes_events import router as events_router
from app.api.routes_categories import router as categories_router
from app.api.routes_imports import router as imports_router
from app.api.routes_health import router as health_router
from app.api.routes_review import router as review_router
from app.api.routes_summary import router as summary_router
from app.db import create_db_engine, create_session_factory
from app.repositories import InMemoryFinanceRepository, SqlAlchemyFinanceRepository
from app.services.google_sheets import build_google_sheets_gateway_from_env


def create_app(database_url: str | None = None) -> FastAPI:
    app = FastAPI(title="Receipt-First Finance API")
    app.state.sheets_gateway = build_google_sheets_gateway_from_env(os.environ)
    if database_url:
        engine = create_db_engine(database_url)
        session_factory: sessionmaker = create_session_factory(engine)
        repository = SqlAlchemyFinanceRepository(session_factory)
        repository.create_schema()
        app.state.repository = repository
    else:
        app.state.repository = InMemoryFinanceRepository()
    app.include_router(health_router)
    app.include_router(categories_router)
    app.include_router(events_router)
    app.include_router(imports_router)
    app.include_router(review_router)
    app.include_router(summary_router)
    return app


app = create_app(os.environ.get("FINANCE_DATABASE_URL"))
