"""Refresh token rotation and logout."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.db import Base
from app.main import app


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield factory
    await engine.dispose()


@pytest.fixture
async def client(session_factory) -> AsyncIterator[AsyncClient]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def test_refresh_rotates_and_old_token_invalid(client: AsyncClient) -> None:
    r = await client.post(
        "/auth/signup",
        json={
            "email": "refresh@example.com",
            "password": "supersecret",
            "dob": str(date(1990, 1, 1)),
        },
    )
    assert r.status_code == 201, r.text
    first = r.json()
    rt1 = first["refresh_token"]

    r2 = await client.post("/auth/refresh", json={"refresh_token": rt1})
    assert r2.status_code == 200, r2.text
    second = r2.json()
    assert second["refresh_token"] != rt1
    assert second["access_token"]

    r3 = await client.post("/auth/refresh", json={"refresh_token": rt1})
    assert r3.status_code == 401

    r4 = await client.post("/auth/refresh", json={"refresh_token": second["refresh_token"]})
    assert r4.status_code == 200, r4.text


async def test_logout_without_body_invalidates_access(client: AsyncClient) -> None:
    r = await client.post(
        "/auth/signup",
        json={
            "email": "logout@example.com",
            "password": "supersecret",
            "dob": str(date(1990, 1, 1)),
        },
    )
    assert r.status_code == 201, r.text
    access = r.json()["access_token"]

    out = await client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert out.status_code == 204, out.text

    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 401
