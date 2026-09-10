"""Tests for the orchestrator settings."""

import os
from unittest.mock import patch

from settings import Settings, settings


def test_default_settings() -> None:
    """Default settings should have sensible defaults."""
    s = Settings()
    assert s.OPENROUTER_BASE_URL == "https://openrouter.ai/api/v1"
    assert s.MODEL == "openai/gpt-4o-mini"
    assert s.TEMPERATURE == 0.7
    assert s.MAX_TOKENS == 4096
    assert s.SMTP_PORT == 587
    assert s.MAX_TOOL_ITERATIONS == 10


def test_settings_singleton() -> None:
    """The module-level `settings` instance should be a Settings."""
    assert isinstance(settings, Settings)


def test_env_override() -> None:
    """Environment variables should override defaults."""
    with patch.dict(
        os.environ,
        {
            "OPENROUTER_API_KEY": "test-key",
            "MODEL": "anthropic/claude-3.5-sonnet",
            "TEMPERATURE": "0.2",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "465",
            "MAX_TOOL_ITERATIONS": "5",
        },
    ):
        s = Settings()
        assert s.OPENROUTER_API_KEY == "test-key"
        assert s.MODEL == "anthropic/claude-3.5-sonnet"
        assert s.TEMPERATURE == 0.2
        assert s.SMTP_HOST == "smtp.example.com"
        assert s.SMTP_PORT == 465
        assert s.MAX_TOOL_ITERATIONS == 5


def test_extra_env_vars_ignored() -> None:
    """Unknown env vars should not raise (extra='ignore')."""
    with patch.dict(os.environ, {"SOME_UNKNOWN_VAR": "value"}, clear=False):
        s = Settings()
        assert s.OPENROUTER_BASE_URL == "https://openrouter.ai/api/v1"
