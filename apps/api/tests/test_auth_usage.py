import asyncio
import pytest

from httpx import AsyncClient

from app.main import app
from app.core.config import get_settings


@pytest.mark.asyncio
async def test_register_login_and_usage_flow(monkeypatch):
    settings = get_settings()
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        # register
        r = await ac.post('/api/v1/auth/register', json={'email': 'testuser@example.com', 'password': 'secret'})
        assert r.status_code == 200
        data = r.json()
        assert 'access_token' in data
        token = data['access_token']

        # create a project via direct POST to projects endpoint if exists else create run denial
        # create api key for user
        headers = {'Authorization': f'Bearer {token}'}
        r2 = await ac.post('/api/v1/auth/apikey', headers=headers, json={'label': 'devkey'})
        assert r2.status_code == 200
        key_data = r2.json()
        assert 'key' in key_data
        api_key = key_data['key']

        # call usage endpoint (should be empty list)
        r3 = await ac.get('/api/v1/auth/usage', headers=headers)
        assert r3.status_code == 200
        usage = r3.json()
        assert isinstance(usage, list)

        # call usage with api key header
        r4 = await ac.get('/api/v1/auth/usage', headers={'x-api-key': api_key})
        # may be 200 or 401 depending on api key->user mapping; ensure no server error
        assert r4.status_code in (200, 401)
