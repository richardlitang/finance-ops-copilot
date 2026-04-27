from fastapi import Request

from app.repositories import InMemoryFinanceRepository


def get_repository(request: Request) -> InMemoryFinanceRepository:
    return request.app.state.repository

