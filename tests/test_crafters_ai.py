"""Tests for the Skill-crafter AI helpers on ClaudeArchitect."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from typer.testing import CliRunner

from clean_agents.cli.main import app
from clean_agents.integrations.anthropic import ClaudeArchitect

runner = CliRunner()


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


def test_ai_flag_enables_contradiction_check(monkeypatch, tmp_path: Path):
    from clean_agents.integrations import anthropic as ant

    fake_client = MagicMock()
    fake_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text='["A says X and not-X"]')],
    )
    monkeypatch.setattr(
        ant, "get_architect", lambda: ant.ClaudeArchitect(client=fake_client)
    )

    fixture = Path("tests/fixtures/crafters/skill/good-skill")
    result = runner.invoke(
        app, ["skill", "validate", str(fixture), "--level", "L2", "--ai"]
    )
    assert result.exit_code in (0, 1)  # may or may not block depending on severity
    assert fake_client.messages.create.called, (
        "AI client should be invoked when --ai is passed with L2 enabled"
    )
