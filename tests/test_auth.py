"""Tests for API authentication and rate limiting."""

import os
import time
from unittest.mock import patch

import pytest

from clean_agents.server.auth import AuthConfig, RateLimiter, AuthManager


class TestRateLimiter:
    """Tests for the RateLimiter token bucket implementation."""

    def test_rate_limiter_allows_within_limit(self):
        """Requests within the rate limit should be allowed."""
        limiter = RateLimiter(rpm=60, burst=10)

        # Should allow 10 requests instantly (burst capacity)
        for _ in range(10):
            assert limiter.check("key1") is True

    def test_rate_limiter_blocks_over_limit(self):
        """Requests exceeding burst should be blocked."""
        limiter = RateLimiter(rpm=60, burst=3)

        # Allow 3 (burst)
        assert limiter.check("key1") is True
        assert limiter.check("key1") is True
        assert limiter.check("key1") is True

        # Block the 4th
        assert limiter.check("key1") is False

    def test_rate_limiter_refills_over_time(self):
        """Tokens should refill based on elapsed time."""
        limiter = RateLimiter(rpm=60, burst=1)  # 1 req/sec, burst of 1

        # Use the burst
        assert limiter.check("key1") is True
        assert limiter.check("key1") is False

        # Wait 1.5 seconds (should give ~1.5 tokens, so 1 is available)
        time.sleep(1.5)
        assert limiter.check("key1") is True

        # Next should be blocked (only 0.5 tokens left)
        assert limiter.check("key1") is False

    def test_rate_limiter_independent_keys(self):
        """Different keys should have independent rate limits."""
        limiter = RateLimiter(rpm=60, burst=2)

        # key1 uses both burst tokens
        assert limiter.check("key1") is True
        assert limiter.check("key1") is True
        assert limiter.check("key1") is False

        # key2 should still have burst available
        assert limiter.check("key2") is True
        assert limiter.check("key2") is True
        assert limiter.check("key2") is False


class TestAuthManager:
    """Tests for the AuthManager."""

    def test_auth_manager_validates_key(self):
        """Valid keys should pass validation."""
        config = AuthConfig(
            enabled=True,
            api_keys=["key1", "key2"],
        )
        manager = AuthManager(config)

        assert manager.validate_key("key1") is True
        assert manager.validate_key("key2") is True

    def test_auth_manager_rejects_invalid_key(self):
        """Invalid keys should be rejected."""
        config = AuthConfig(
            enabled=True,
            api_keys=["key1"],
        )
        manager = AuthManager(config)

        assert manager.validate_key("invalid") is False
        assert manager.validate_key(None) is False

    def test_auth_manager_rejects_when_disabled(self):
        """When auth is disabled, all requests should pass."""
        config = AuthConfig(enabled=False)
        manager = AuthManager(config)

        # Even without keys, should allow anything
        assert manager.validate_key(None) is True
        assert manager.validate_key("any_key") is True

    def test_auth_manager_rate_limit_check(self):
        """Rate limiting should work when enabled."""
        config = AuthConfig(
            enabled=True,
            api_keys=["key1"],
            rate_limit_rpm=60,
            rate_limit_burst=2,
        )
        manager = AuthManager(config)

        # Should allow burst of 2
        assert manager.check_rate_limit("key1") is True
        assert manager.check_rate_limit("key1") is True

        # 3rd should be blocked
        assert manager.check_rate_limit("key1") is False

    def test_auth_manager_rate_limit_disabled(self):
        """Rate limiting should be skipped when auth is disabled."""
        config = AuthConfig(
            enabled=False,
            rate_limit_rpm=1,
            rate_limit_burst=0,
        )
        manager = AuthManager(config)

        # Should allow many requests even with restrictive limits
        for _ in range(10):
            assert manager.check_rate_limit("key1") is True

    def test_auth_manager_from_env(self):
        """Load config from environment variables."""
        with patch.dict(os.environ, {
            "CLEAN_AGENTS_AUTH_ENABLED": "true",
            "CLEAN_AGENTS_API_KEYS": "key1,key2,key3",
            "CLEAN_AGENTS_RATE_LIMIT": "100",
            "CLEAN_AGENTS_RATE_LIMIT_BURST": "20",
        }):
            manager = AuthManager.from_env()

            assert manager.config.enabled is True
            assert manager.config.api_keys == ["key1", "key2", "key3"]
            assert manager.config.rate_limit_rpm == 100
            assert manager.config.rate_limit_burst == 20

    def test_auth_manager_from_env_defaults(self):
        """Defaults should be used when env vars are not set."""
        with patch.dict(os.environ, clear=True):
            manager = AuthManager.from_env()

            assert manager.config.enabled is False
            assert manager.config.api_keys == []
            assert manager.config.rate_limit_rpm == 60
            assert manager.config.rate_limit_burst == 10

    def test_auth_manager_from_env_whitespace(self):
        """Whitespace in API keys should be trimmed."""
        with patch.dict(os.environ, {
            "CLEAN_AGENTS_API_KEYS": " key1 , key2 , key3 ",
        }):
            manager = AuthManager.from_env()

            assert manager.config.api_keys == ["key1", "key2", "key3"]

    def test_auth_disabled_allows_all(self):
        """When auth is disabled, all operations should succeed."""
        config = AuthConfig(enabled=False)
        manager = AuthManager(config)

        # Should validate any key
        assert manager.validate_key("anything") is True
        assert manager.validate_key(None) is True

        # Should allow unlimited requests
        for _ in range(1000):
            assert manager.check_rate_limit("key1") is True


class TestAuthConfig:
    """Tests for the AuthConfig model."""

    def test_auth_config_defaults(self):
        """AuthConfig should have sensible defaults."""
        config = AuthConfig()

        assert config.enabled is False
        assert config.api_keys == []
        assert config.rate_limit_rpm == 60
        assert config.rate_limit_burst == 10

    def test_auth_config_custom_values(self):
        """AuthConfig should accept custom values."""
        config = AuthConfig(
            enabled=True,
            api_keys=["key1", "key2"],
            rate_limit_rpm=120,
            rate_limit_burst=20,
        )

        assert config.enabled is True
        assert config.api_keys == ["key1", "key2"]
        assert config.rate_limit_rpm == 120
        assert config.rate_limit_burst == 20
