"""Tests for the runtime harness."""

from __future__ import annotations

import pytest

from clean_agents.core.agent import AgentSpec, ModelConfig
from clean_agents.core.blueprint import Blueprint, ArchitecturePattern, SystemType
from clean_agents.harness import (
    RuntimeHarness,
    MockProvider,
    AgentResponse,
    TokenUsage,
    HarnessResult,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_provider() -> MockProvider:
    """Create a mock provider for testing."""
    responses = {
        "claude-sonnet-4-6": "Sonnet response",
        "claude-haiku-4-5": "Haiku response",
    }
    return MockProvider(responses=responses, default_response="Default mock response")


def _make_simple_blueprint() -> Blueprint:
    """Create a simple single-agent blueprint."""
    return Blueprint(
        name="simple-system",
        system_type=SystemType.SINGLE_AGENT,
        pattern=ArchitecturePattern.SINGLE,
        agents=[
            AgentSpec(
                name="classifier",
                role="Classify input",
                agent_type="classifier",
                model=ModelConfig(primary="claude-haiku-4-5"),
            ),
        ],
    )


def _make_orchestrator_blueprint() -> Blueprint:
    """Create a blueprint with an orchestrator."""
    return Blueprint(
        name="orchestrator-system",
        system_type=SystemType.MULTI_AGENT,
        pattern=ArchitecturePattern.SUPERVISOR_HIERARCHICAL,
        agents=[
            AgentSpec(
                name="orchestrator",
                role="Route tasks",
                agent_type="orchestrator",
                model=ModelConfig(primary="claude-sonnet-4-6"),
            ),
            AgentSpec(
                name="specialist",
                role="Handle tasks",
                agent_type="specialist",
                model=ModelConfig(primary="claude-sonnet-4-6"),
            ),
        ],
    )


# ── Token Usage Tests ─────────────────────────────────────────────────────────


def test_token_usage_initialization():
    """Test TokenUsage creation."""
    tokens = TokenUsage(input_tokens=100, output_tokens=50)
    assert tokens.input_tokens == 100
    assert tokens.output_tokens == 50
    assert tokens.total == 150


def test_token_usage_add_method():
    """Test TokenUsage add method."""
    tokens1 = TokenUsage(input_tokens=100, output_tokens=50)
    tokens2 = TokenUsage(input_tokens=200, output_tokens=75)
    tokens1.add(tokens2)
    assert tokens1.input_tokens == 300
    assert tokens1.output_tokens == 125


# ── Agent Response Tests ──────────────────────────────────────────────────────


def test_agent_response_creation():
    """Test AgentResponse creation."""
    response = AgentResponse(
        agent_name="test_agent",
        content="Test output",
        tokens_used=TokenUsage(input_tokens=100, output_tokens=50),
        latency_ms=150.0,
        cost=0.001,
    )
    assert response.agent_name == "test_agent"
    assert response.content == "Test output"
    assert response.tokens_used.total == 150
    assert response.latency_ms == 150.0


def test_agent_response_with_error():
    """Test AgentResponse with error."""
    response = AgentResponse(
        agent_name="test_agent",
        content="",
        tokens_used=TokenUsage(),
        error="Test error",
    )
    assert response.error == "Test error"
    assert response.content == ""


# ── Basic Harness Tests ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_harness_with_simple_agent(mock_provider):
    """Test harness with a simple agent."""
    blueprint = _make_simple_blueprint()
    harness = RuntimeHarness(blueprint, provider=mock_provider)

    result = await harness.run("Classify this text")

    assert result.final_output == "Haiku response"
    assert result.rounds_executed == 1
    assert len(result.agent_traces) == 1
    assert result.agent_traces[0].agent_name == "classifier"
    assert result.total_cost > 0


@pytest.mark.asyncio
async def test_harness_with_orchestrator(mock_provider):
    """Test harness with orchestrator agent."""
    blueprint = _make_orchestrator_blueprint()
    harness = RuntimeHarness(blueprint, provider=mock_provider)

    result = await harness.run("Route this task")

    assert result.final_output == "Sonnet response"
    assert result.rounds_executed >= 1
    assert len(result.agent_traces) > 0
    assert result.agent_traces[0].agent_name == "orchestrator"


@pytest.mark.asyncio
async def test_harness_with_empty_blueprint(mock_provider):
    """Test harness with no agents."""
    blueprint = Blueprint(
        name="empty-system",
        system_type=SystemType.SINGLE_AGENT,
        pattern=ArchitecturePattern.SINGLE,
        agents=[],
    )
    harness = RuntimeHarness(blueprint, provider=mock_provider)

    result = await harness.run("Process")

    assert result.final_output == ""
    assert result.rounds_executed == 0


# ── Mock Provider Tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mock_provider_basic():
    """Test mock provider basic functionality."""
    provider = MockProvider(default_response="Test response")

    response = await provider.complete(
        messages=[{"role": "user", "content": "Hello"}],
        model="test-model",
        max_tokens=100,
        temperature=0.7,
    )

    assert response.content == "Test response"
    assert response.input_tokens > 0
    assert response.output_tokens > 0
    assert response.latency_ms > 0


@pytest.mark.asyncio
async def test_mock_provider_custom_responses():
    """Test mock provider with custom responses."""
    provider = MockProvider(
        responses={
            "model-a": "Response A",
            "model-b": "Response B",
        },
        default_response="Default response",
    )

    response_a = await provider.complete(
        messages=[{"role": "user", "content": "Test"}],
        model="model-a",
        max_tokens=100,
        temperature=0.7,
    )
    assert response_a.content == "Response A"

    response_b = await provider.complete(
        messages=[{"role": "user", "content": "Test"}],
        model="model-b",
        max_tokens=100,
        temperature=0.7,
    )
    assert response_b.content == "Response B"

    response_default = await provider.complete(
        messages=[{"role": "user", "content": "Test"}],
        model="unknown-model",
        max_tokens=100,
        temperature=0.7,
    )
    assert response_default.content == "Default response"


@pytest.mark.asyncio
async def test_mock_provider_call_counting():
    """Test that mock provider counts calls."""
    provider = MockProvider()

    assert provider.call_count == 0

    await provider.complete(
        messages=[{"role": "user", "content": "Test"}],
        model="test",
        max_tokens=100,
        temperature=0.7,
    )
    assert provider.call_count == 1

    await provider.complete(
        messages=[{"role": "user", "content": "Test"}],
        model="test",
        max_tokens=100,
        temperature=0.7,
    )
    assert provider.call_count == 2


# ── Harness Result Tests ──────────────────────────────────────────────────────


def test_harness_result_initialization():
    """Test HarnessResult initialization."""
    result = HarnessResult()
    assert result.final_output == ""
    assert result.total_tokens.total == 0
    assert result.total_cost == 0.0
    assert result.total_latency_ms == 0.0
    assert len(result.agent_traces) == 0
    assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_harness_result_metrics(mock_provider):
    """Test that HarnessResult properly aggregates metrics."""
    blueprint = _make_simple_blueprint()
    harness = RuntimeHarness(blueprint, provider=mock_provider)

    result = await harness.run("Test input")

    # Verify metrics are populated
    assert result.total_tokens.total > 0
    assert result.total_cost > 0
    assert result.total_latency_ms > 0

    # Verify aggregation from traces
    total_tokens_from_traces = sum(t.tokens_used.total for t in result.agent_traces)
    assert result.total_tokens.total == total_tokens_from_traces

    total_cost_from_traces = sum(t.cost for t in result.agent_traces)
    assert result.total_cost == total_cost_from_traces


# ── Edge Cases ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_harness_default_provider():
    """Test that harness uses MockProvider by default."""
    blueprint = _make_simple_blueprint()
    # Don't pass provider, should default to MockProvider
    harness = RuntimeHarness(blueprint)

    result = await harness.run("Test")

    assert len(result.agent_traces) > 0
    assert result.final_output is not None


@pytest.mark.asyncio
async def test_agent_runtime_error_handling(mock_provider):
    """Test error handling in agent execution."""
    # Create a blueprint with an agent that has a very low token budget
    blueprint = Blueprint(
        name="low-budget",
        system_type=SystemType.SINGLE_AGENT,
        pattern=ArchitecturePattern.SINGLE,
        agents=[
            AgentSpec(
                name="agent",
                role="Test",
                agent_type="specialist",
                model=ModelConfig(primary="claude-sonnet-4-6"),
                token_budget=1,  # Very low to potentially cause issues
            ),
        ],
    )
    harness = RuntimeHarness(blueprint, provider=mock_provider)

    result = await harness.run("Test")

    # Should still complete even with odd config
    assert result.rounds_executed >= 0


@pytest.mark.asyncio
async def test_multiple_blueprint_executions(mock_provider):
    """Test running same harness multiple times."""
    blueprint = _make_simple_blueprint()
    harness = RuntimeHarness(blueprint, provider=mock_provider)

    result1 = await harness.run("First")
    result2 = await harness.run("Second")

    assert result1.final_output == result2.final_output
    assert mock_provider.call_count == 2
