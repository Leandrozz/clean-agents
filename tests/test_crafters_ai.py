"""Tests for the Skill-crafter AI helpers on ClaudeArchitect."""

from __future__ import annotations

from unittest.mock import MagicMock

from clean_agents.integrations.anthropic import ClaudeArchitect


def test_detect_contradictions_returns_list():
    client_mock = MagicMock()
    client_mock.messages.create.return_value = MagicMock(
        content=[MagicMock(text='["claim A contradicts claim B"]')],
    )
    arch = ClaudeArchitect(client=client_mock)
    result = arch.detect_contradictions("some body text")
    assert isinstance(result, list)
    assert "contradicts" in result[0]


def test_suggest_triggers_returns_list():
    client_mock = MagicMock()
    client_mock.messages.create.return_value = MagicMock(
        content=[MagicMock(text='["pdf table", "markdown grid", "csv parse"]')],
    )
    arch = ClaudeArchitect(client=client_mock)
    triggers = arch.suggest_triggers("detect tables in markdown")
    assert len(triggers) == 3
