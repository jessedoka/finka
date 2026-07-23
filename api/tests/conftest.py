import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import main
from database import get_db
from models import Base
from models.user import User
from services.auth import get_current_user

# Integration-test harness: the real FastAPI app + service + ORM stack, but on an
# in-memory SQLite DB with a stubbed current-user, so create->earmark->split flows
# run end to end without Postgres, dev-data pollution, or Cognito. StaticPool keeps
# the one in-memory connection alive so every session sees the same schema + rows.


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
def sessionmaker(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def user(sessionmaker) -> User:
    async with sessionmaker() as s:
        u = User(cognito_sub="test-user-001", email="test@example.com", display_name="Test")
        s.add(u)
        await s.commit()
        await s.refresh(u)
        return u


@pytest_asyncio.fixture
async def session(sessionmaker):
    """A session tests use to seed rows (accounts, snapshots) directly."""
    async with sessionmaker() as s:
        yield s


@pytest_asyncio.fixture
async def client(sessionmaker, user):
    async def override_get_db():
        async with sessionmaker() as s:
            yield s

    async def override_get_current_user():
        return user

    main.app.dependency_overrides[get_db] = override_get_db
    main.app.dependency_overrides[get_current_user] = override_get_current_user
    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    main.app.dependency_overrides.clear()
