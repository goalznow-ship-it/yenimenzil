import pytest

from app.core.security import REFRESH_TOKEN_COOKIE, hash_password
from app.models.user import User

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
ME_URL = "/api/v1/auth/me"


def _register_payload(**overrides):
    payload = {
        "email": "newuser@test.az",
        "password": "supersecret1",
        "full_name": "Test User",
        "phone": "+994501234567",
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_register_creates_user_and_sets_cookies(client):
    response = await client.post(REGISTER_URL, json=_register_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "newuser@test.az"
    assert body["user"]["role"] == "user"
    assert body["user"]["is_verified"] is False
    assert body["user"]["profile"]["preferred_language"] == "az"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_register_duplicate_email_conflict(client):
    await client.post(REGISTER_URL, json=_register_payload())
    response = await client.post(REGISTER_URL, json=_register_payload())
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_phone_rejected(client):
    response = await client.post(
        REGISTER_URL, json=_register_payload(phone="12345")
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success_sets_cookies(client, db):
    user = User(
        email="login@test.az",
        password_hash=hash_password("supersecret1"),
        full_name="Login User",
    )
    db.add(user)
    await db.commit()

    response = await client.post(
        LOGIN_URL, json={"email": "login@test.az", "password": "supersecret1"}
    )
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "login@test.az"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password_rejected(client, db):
    user = User(
        email="login@test.az",
        password_hash=hash_password("supersecret1"),
        full_name="Login User",
    )
    db.add(user)
    await db.commit()

    response = await client.post(
        LOGIN_URL, json={"email": "login@test.az", "password": "wrongpassword"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user_rejected(client, db):
    user = User(
        email="inactive@test.az",
        password_hash=hash_password("supersecret1"),
        full_name="Inactive",
        is_active=False,
    )
    db.add(user)
    await db.commit()

    response = await client.post(
        LOGIN_URL, json={"email": "inactive@test.az", "password": "supersecret1"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    response = await client.get(ME_URL)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user(client, db):
    await client.post(REGISTER_URL, json=_register_payload(email="me@test.az"))
    response = await client.get(ME_URL)
    assert response.status_code == 200
    assert response.json()["email"] == "me@test.az"


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client, db):
    await client.post(REGISTER_URL, json=_register_payload(email="out@test.az"))
    refresh_cookie = client.cookies.get(REFRESH_TOKEN_COOKIE)

    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 204
    assert client.cookies.get("access_token") is None or response.cookies.get(
        "access_token"
    ) is None

    client.cookies.set(REFRESH_TOKEN_COOKIE, refresh_cookie)
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rotates_tokens(client, db):
    await client.post(REGISTER_URL, json=_register_payload(email="rot@test.az"))
    first_refresh = client.cookies.get(REFRESH_TOKEN_COOKIE)

    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 200
    new_refresh = response.cookies.get(REFRESH_TOKEN_COOKIE)
    assert new_refresh != first_refresh

    # Old token is revoked.
    client.cookies.set(REFRESH_TOKEN_COOKIE, first_refresh)
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_missing_token_rejected(client):
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_me(client, db):
    await client.post(REGISTER_URL, json=_register_payload(email="upd@test.az"))
    response = await client.patch(
        "/api/v1/users/me",
        json={"full_name": "New Name", "bio": "Hello", "city": "Bakı"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "New Name"
    assert body["profile"]["bio"] == "Hello"
    assert body["profile"]["city"] == "Bakı"


@pytest.mark.asyncio
async def test_update_me_requires_auth(client):
    response = await client.patch(
        "/api/v1/users/me", json={"full_name": "Hacker"}
    )
    assert response.status_code == 401
