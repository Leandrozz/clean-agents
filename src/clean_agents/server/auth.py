"""API authentication and rate limiting for CLean-agents server.

Provides:
    - AuthConfig: Configuration for API key authentication
    - RateLimiter: Token bucket rate limiter implementation
    - AuthManager: Unified authentication and rate limit checking
"""

from __future__ import annotations

import os
import time
from typing import Optional

from pydantic import BaseModel


class AuthConfig(BaseModel):
    """API authentication configuration."""

    enabled: bool = False
    api_keys: list[str] = []  # Valid API keys
    rate_limit_rpm: int = 60  # Requests per minute per key
    rate_limit_burst: int = 10  # Max burst requests


class RateLimiter:
    """Simple in-memory rate limiter using token bucket algorithm.

    Maintains per-key token buckets that refill at rate_rpm/60 tokens per second.
    Each request consumes 1 token. Burst capacity limits max instantaneous requests.
    """

    def __init__(self, rpm: int = 60, burst: int = 10) -> None:
        """Initialize rate limiter.

        Args:
            rpm: Requests per minute allowed
            burst: Maximum burst capacity
        """
        self.rpm = rpm
        self.burst = burst
        self.rate_per_second = rpm / 60.0
        # Key: API key, Value: (tokens_available, last_refill_time)
        self._buckets: dict[str, tuple[float, float]] = {}

    def check(self, key: str) -> bool:
        """Check if request is allowed for the given key.

        Args:
            key: API key or identifier

        Returns:
            True if request is allowed, False if rate limited
        """
        self._refill(key)
        tokens, _ = self._buckets.get(key, (self.burst, time.time()))

        if tokens >= 1.0:
            self._buckets[key] = (tokens - 1.0, time.time())
            return True

        return False

    def _refill(self, key: str) -> None:
        """Refill tokens for a key based on elapsed time.

        Args:
            key: API key to refill
        """
        now = time.time()

        if key not in self._buckets:
            self._buckets[key] = (self.burst, now)
            return

        tokens, last_refill = self._buckets[key]
        elapsed = now - last_refill
        refill_amount = elapsed * self.rate_per_second
        tokens = min(self.burst, tokens + refill_amount)
        self._buckets[key] = (tokens, now)


class AuthManager:
    """Manages API key validation and rate limiting."""

    def __init__(self, config: Optional[AuthConfig] = None) -> None:
        """Initialize auth manager.

        Args:
            config: AuthConfig instance. If None, defaults to disabled.
        """
        self.config = config or AuthConfig()
        self.rate_limiter = RateLimiter(
            rpm=self.config.rate_limit_rpm,
            burst=self.config.rate_limit_burst,
        )

    @classmethod
    def from_env(cls) -> AuthManager:
        """Load configuration from environment variables.

        Environment variables:
            CLEAN_AGENTS_AUTH_ENABLED: "true" to enable authentication
            CLEAN_AGENTS_API_KEYS: Comma-separated list of valid API keys
            CLEAN_AGENTS_RATE_LIMIT: Requests per minute (default: 60)
            CLEAN_AGENTS_RATE_LIMIT_BURST: Burst capacity (default: 10)

        Returns:
            AuthManager configured from environment
        """
        enabled = os.getenv("CLEAN_AGENTS_AUTH_ENABLED", "false").lower() == "true"
        api_keys_str = os.getenv("CLEAN_AGENTS_API_KEYS", "")
        api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()] if api_keys_str else []
        rate_limit = int(os.getenv("CLEAN_AGENTS_RATE_LIMIT", "60"))
        burst = int(os.getenv("CLEAN_AGENTS_RATE_LIMIT_BURST", "10"))

        config = AuthConfig(
            enabled=enabled,
            api_keys=api_keys,
            rate_limit_rpm=rate_limit,
            rate_limit_burst=burst,
        )
        return cls(config)

    def validate_key(self, key: Optional[str]) -> bool:
        """Validate an API key.

        Args:
            key: API key to validate (can be None)

        Returns:
            True if key is valid or auth is disabled, False otherwise
        """
        if not self.config.enabled:
            return True

        if not key:
            return False

        return key in self.config.api_keys

    def check_rate_limit(self, key: str) -> bool:
        """Check if request is allowed under rate limit.

        Args:
            key: API key or identifier

        Returns:
            True if request is allowed, False if rate limited
        """
        if not self.config.enabled:
            return True

        return self.rate_limiter.check(key)
