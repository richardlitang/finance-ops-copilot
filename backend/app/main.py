from fastapi import FastAPI

from app.api.routes_events import router as events_router
from app.api.routes_imports import router as imports_router
from app.api.routes_health import router as health_router
from app.api.routes_summary import router as summary_router
from app.repositories import InMemoryFinanceRepository


def create_app() -> FastAPI:
    app = FastAPI(title="Receipt-First Finance API")
    app.state.repository = InMemoryFinanceRepository()
    app.include_router(health_router)
    app.include_router(events_router)
    app.include_router(imports_router)
    app.include_router(summary_router)
    return app


app = create_app()
