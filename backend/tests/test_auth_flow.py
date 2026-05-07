"""Signup -> login -> /auth/me round-trip against an in-process FastAPI app
backed by an in-memory SQLite DB."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# `tests/conftest.py` sets the env vars before app modules are loaded.
from app.api.deps import get_db
from app.db import Base
from app.main import app


@pytest.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
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


async def test_signup_login_me_roundtrip(client: AsyncClient) -> None:
    # 1. Signup
    resp = await client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "supersecret",
            "dob": str(date(1995, 6, 15)),
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["age_bucket"] in ("25-29", "30-34")
    assert body["username"].count("-") == 2  # adjective-animal-NNNN

    signup_token = body["access_token"]
    handle = body["username"]

    # 2. Login with the same credentials returns a token + same handle.
    resp = await client.post(
        "/auth/login",
        json={"email": "TEST@EXAMPLE.com", "password": "supersecret"},
    )
    assert resp.status_code == 200, resp.text
    login_body = resp.json()
    assert login_body["username"] == handle
    assert login_body["access_token"]

    # 3. /auth/me requires the bearer header and reflects state.
    resp = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {signup_token}"},
    )
    assert resp.status_code == 200, resp.text
    me = resp.json()
    assert me["username"] == handle
    assert me["age_bucket"] == body["age_bucket"]
    assert me["has_bank_linked"] is False


async def test_me_requires_token(client: AsyncClient) -> None:
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_login_bad_password(client: AsyncClient) -> None:
    await client.post(
        "/auth/signup",
        json={
            "email": "alice@example.com",
            "password": "supersecret",
            "dob": str(date(1990, 1, 1)),
        },
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


async def test_signup_underage_rejected(client: AsyncClient) -> None:
    resp = await client.post(
        "/auth/signup",
        json={
            "email": "kid@example.com",
            "password": "supersecret",
            "dob": str(date(2015, 1, 1)),
        },
    )
    assert resp.status_code == 400
    assert "18" in resp.json()["detail"]


async def test_duplicate_email_rejected(client: AsyncClient) -> None:
    payload = {
        "email": "dupe@example.com",
        "password": "supersecret",
        "dob": str(date(1990, 1, 1)),
    }
    first = await client.post("/auth/signup", json=payload)
    assert first.status_code == 201
    second = await client.post("/auth/signup", json=payload)
    assert second.status_code == 409
