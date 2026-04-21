"""Tests for AI-enhanced features (ClaudeArchitect integration)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from clean_agents.core.agent import AgentSpec, ModelConfig
from clean_agents.core.blueprint import ArchitecturePattern, Blueprint, SystemType


def _test_blueprint() -> Blueprint:
    return Blueprint(
        name="test-system",
        description="Test system",
        system_type=SystemType.MULTI_AGENT,
        pattern=ArchitecturePattern.SUPERVISOR_HIERARCHICAL,
        agents=[
            AgentSpec(
                name="orchestrator", role="Route tasks", agent_type="orchestrator",
                model=ModelConfig(primary="claude-opus-4-6"), token_budget=6000,
            ),
            AgentSpec(
                name="worker", role="Do work", agent_type="specialist",
                model=ModelConfig(primary="claude-sonnet-4-6"), token_budget=4000,
            ),
        ],
    )


class _FakeResponse:
    """Fake Anthropic API response."""

    def __init__(self, text: str):
        self.content = [MagicMock(text=text)]


@pytest.fixture
def mock_anthropic():
    """Patch the anthropic import inside ClaudeArchitect."""
    mock_module = MagicMock()
    mock_client = MagicMock()
    mock_module.Anthropic.return_value = mock_client
    with patch.dict("sys.modules", {"anthropic": mock_module}):
        yield mock_client


# ── enhance_blueprint ────────────────────────────────────────────────────────


def test_enhance_blueprint_parses_json(mock_anthropic):
    from clean_agents.integrations.anthropic import ClaudeArchitect

    response_data = {
        "suggestions": [{"title": "Add fallback", "description": "Use fallback model", "priority": "high", "impact": "resilience"}],
        "risk_assessment": {"security": {"level": "medium", "details": "OK"}, "reliability": {"level": "low", "details": "Good"}, "cost": {"level": "low", "details": "Cheap"}},
        "missing_components": ["rate limiting"],
    }
    mock_anthropic.messages.create.return_value = _FakeResponse(json.dumps(response_data))

    architect = ClaudeArchitect(api_key="test-key")
    result = architect.enhance_blueprint(_test_blueprint())

    assert len(result["suggestions"]) == 1
    assert result["suggestions"][0]["title"] == "Add fallback"
    assert result["missing_components"] == ["rate limiting"]


def test_enhance_blueprint_handles_markdown_json(mock_anthropic):
    from clean_agents.integrations.anthropic import ClaudeArchitect

    data = {"suggestions": [], "risk_assessment": {}, "missing_components": []}
    text = f"Here's my analysis:\n```json\n{json.dumps(data)}\n```"
    mock_anthropic.messages.create.return_value = _FakeResponse(text)

    architect = ClaudeArchitect(api_key="test-key")
    result = architect.enhance_blueprint(_test_blueprint())
    assert result["suggestions"] == []


def test_enhance_blueprint_handles_unparseable(mock_anthropic):
    from clean_agents.integrations.anthropic import ClaudeArchitect

    mock_anthropic.messages.create.return_value = _FakeResponse("Not valid JSON at all")

    architect = ClaudeArchitect(api_key="test-key")
    result = architect.enhance_blueprint(_test_blueprint())
    assert "raw_response" in result


# ── generate_agent_prompt ────────────────────────────────────────────────────


def test_generate_agent_prompt(mock_anthropic):
    from clean_agents.integrations.anthropic import ClaudeArchitect

    mock_anthropic.messages.create.return_value = _FakeResponse("You are an expert orchestrator...")

    architect = ClaudeArchitect(api_key="test-key")
    prompt = architect.generate_agent_prompt(
        agent_name="orchestrator",
        agent_role="Route tasks",
        domain="customer-support",
        constraints=["Max 6000 tokens"],
        tools=["search", "classify"],
    )
    assert "orchestrator" in prompt.lower() or "expert" in prompt.lower()


# ── analyze_security ─────────────────────────────────────────────────────────


def test_analyze_security_parses(mock_anthropic):
    from clean_agents.integrations.anthropic import ClaudeArchitect

    data = {
        "overall_score": 72,
        "critical_findings": [{"agent": "worker", "vulnerability": "No input filtering", "severity": "high", "remediation": "Add guards"}],
        "attack_scenarios": [],
        "hardening_checklist": ["Enable PII detection"],
    }
    mock_anthropic.messages.create.return_value = _FakeResponse(json.dumps(data))

    architect = ClaudeArchitect(api_key="test-key")
    result = architect.analyze_security(_test_blueprint())
    assert result["overall_score"] == 72
    assert len(result["critical_findings"]) == 1


# ── iterate_design ───────────────────────────────────────────────────────────


def test_iterate_design_returns_text(mock_anthropic):
    from clean_agents.integrations.anthropic import ClaudeArchitect

    mock_anthropic.messages.create.return_value = _FakeResponse(
        "## Changes\n1. Switch orchestrator to sonnet\n\n```yaml\nagents:\n  - name: orchestrator\n    model: claude-sonnet-4-6\n```"
    )

    architect = ClaudeArchitect(api_key="test-key")
    result = architect.iterate_design(
        _test_blueprint(),
        "Make it cheaper",
        conversation_history=[],
    )
    assert "orchestrator" in result
    assert "sonnet" in result


def test_iterate_design_with_history(mock_anthropic):
    from clean_agents.integrations.anthropic import ClaudeArchitect

    mock_anthropic.messages.create.return_value = _FakeResponse("Done")

    architect = ClaudeArchitect(api_key="test-key")
    history = [
        {"role": "user", "content": "Add a QA agent"},
        {"role": "assistant", "content": "Added qa-reviewer agent"},
    ]
    result = architect.iterate_design(_test_blueprint(), "Now make it faster", history)
    assert result == "Done"

    # Verify history was passed correctly
    call_kwargs = mock_anthropic.messages.create.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages", [])
    assert len(messages) == 3  # 2 history + 1 new


# ── design_cmd helpers ───────────────────────────────────────────────────────


def test_try_create_architect_no_key():
    """Without ANTHROPIC_API_KEY, should return None."""
    import os
    from clean_agents.cli.design_cmd import _try_create_architect

    old = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        assert _try_create_architect() is None
    finally:
        if old:
            os.environ["ANTHROPIC_API_KEY"] = old
