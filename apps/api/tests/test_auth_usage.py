import pytest

from httpx import ASGITransport, AsyncClient
from types import SimpleNamespace

from app.main import app
from app.db import get_session


class DummySession:
    pass


async def _override_get_session():
    yield DummySession()


@pytest.mark.asyncio
async def test_register_login_and_usage_flow(monkeypatch):
    users: dict[str, SimpleNamespace] = {}
    api_keys: dict[str, SimpleNamespace] = {}

    async def fake_get_user_by_email(session, email):
        return users.get(email)

    async def fake_create_user(session, email, password):
        user = SimpleNamespace(id="user-1", email=email, hashed_password="hashed")
        users[email] = user
        return user

    async def fake_get_user_by_id(session, user_id):
        for user in users.values():
            if user.id == user_id:
                return user
        return None

    async def fake_create_api_key(session, user_id, key, label=None):
        record = SimpleNamespace(key=key, label=label, user_id=user_id, revoked=False)
        api_keys[key] = record
        return record

    async def fake_get_api_key_by_value(session, key):
        return api_keys.get(key)

    class FakeResult:
        def scalars(self):
            return self

        def all(self):
            return []

    async def fake_execute(self, *args, **kwargs):
        return FakeResult()

    monkeypatch.setattr("app.crud.auth.get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr("app.crud.auth.create_user", fake_create_user)
    monkeypatch.setattr("app.crud.auth.get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr("app.crud.auth.create_api_key", fake_create_api_key)
    monkeypatch.setattr("app.crud.auth.get_api_key_by_value", fake_get_api_key_by_value)
    monkeypatch.setattr(DummySession, "execute", fake_execute, raising=False)

    app.dependency_overrides[get_session] = _override_get_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            r = await ac.post("/api/v1/auth/register", json={"email": "testuser@example.com", "password": "secret"})
            assert r.status_code == 200
            data = r.json()
            assert "access_token" in data
            token = data["access_token"]

            headers = {"Authorization": f"Bearer {token}"}
            r2 = await ac.post("/api/v1/auth/apikey", headers=headers, json={"label": "devkey"})
            assert r2.status_code == 200
            key_data = r2.json()
            assert "key" in key_data
            api_key = key_data["key"]

            r3 = await ac.get("/api/v1/auth/usage", headers=headers)
            assert r3.status_code == 200
            usage = r3.json()
            assert isinstance(usage, list)

            r4 = await ac.get("/api/v1/auth/usage", headers={"x-api-key": api_key})
            assert r4.status_code in (200, 401)
    finally:
        app.dependency_overrides.clear()
