import pytest
from httpx import AsyncClient
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.main import app
from shared.db.connection import AsyncSessionLocal, engine
from shared.db.base import Base

@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    # Create tables before tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Drop all tables first
        await conn.run_sync(Base.metadata.create_all)  # Create fresh tables

    yield  # Run tests

    # Clean up after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def session() -> AsyncSession:
    async with AsyncSessionLocal() as s:
        yield s

@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
