import hmac
import math
import threading
import time
from collections import deque

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from src.api.deps import get_app_settings
from src.core.config import Settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    api_key: str | None = Security(api_key_header),
    settings: Settings = Depends(get_app_settings),
) -> None:
    """Require a configured API key in production and validate it without timing leaks."""
    configured_key = settings.API_KEY
    if not configured_key:
        if settings.ENVIRONMENT.casefold() == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API authentication is not configured.",
            )
        return
    if not api_key or not hmac.compare_digest(
        api_key.encode("utf-8"), configured_key.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )


class InMemoryIPRateLimiter:
    """Per-process sliding-window rate limiter for the single-instance demo deployment."""

    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, client_ip: str, limit: int, window_seconds: int) -> int | None:
        now = time.monotonic()
        with self._lock:
            timestamps = self._requests.setdefault(client_ip, deque())
            while timestamps and timestamps[0] <= now - window_seconds:
                timestamps.popleft()
            if len(self._requests) >= 10_000:
                expired_clients = [
                    ip
                    for ip, requests in self._requests.items()
                    if not requests or requests[-1] <= now - window_seconds
                ]
                for ip in expired_clients:
                    self._requests.pop(ip, None)
                if len(self._requests) >= 10_000:
                    victim = next(ip for ip in self._requests if ip != client_ip)
                    self._requests.pop(victim)
            if len(timestamps) >= limit:
                return max(1, math.ceil(timestamps[0] + window_seconds - now))
            timestamps.append(now)
            return None


rate_limiter = InMemoryIPRateLimiter()


async def enforce_rate_limit(
    request: Request,
    settings: Settings = Depends(get_app_settings),
) -> None:
    """Limit query and feedback requests to the configured per-IP budget."""
    client_ip = request.client.host if request.client else "unknown"
    retry_after = rate_limiter.check(
        client_ip,
        settings.RATE_LIMIT_REQUESTS,
        settings.RATE_LIMIT_WINDOW_SECONDS,
    )
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Request limit exceeded. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
