import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.api.security import InMemoryIPRateLimiter, require_api_key


def test_api_key_is_required_and_compared_in_constant_time():
    settings = SimpleNamespace(API_KEY="configured-secret", ENVIRONMENT="production")

    with pytest.raises(HTTPException) as missing:
        asyncio.run(require_api_key(None, settings))
    assert missing.value.status_code == 401

    with pytest.raises(HTTPException) as invalid:
        asyncio.run(require_api_key("wrong", settings))
    assert invalid.value.status_code == 401

    assert asyncio.run(require_api_key("configured-secret", settings)) is None


def test_production_fails_closed_when_api_key_is_unconfigured():
    settings = SimpleNamespace(API_KEY=None, ENVIRONMENT="production")

    with pytest.raises(HTTPException) as error:
        asyncio.run(require_api_key(None, settings))

    assert error.value.status_code == 503


def test_rate_limiter_enforces_and_expires_sliding_window(monkeypatch):
    now = [100.0]
    monkeypatch.setattr("src.api.security.time.monotonic", lambda: now[0])
    limiter = InMemoryIPRateLimiter()

    assert limiter.check("192.0.2.1", limit=2, window_seconds=60) is None
    assert limiter.check("192.0.2.1", limit=2, window_seconds=60) is None
    assert limiter.check("192.0.2.1", limit=2, window_seconds=60) == 60

    now[0] = 161.0
    assert limiter.check("192.0.2.1", limit=2, window_seconds=60) is None
