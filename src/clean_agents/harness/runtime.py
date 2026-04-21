"""Runtime harness for executing multi-agent systems defined by blueprints."""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field

from clean_agents.core.blueprint import Blueprint
from clean_agents.harness.providers import LLMProvider, MockProvider, ProviderResponse


class TokenUsage(BaseModel):
    """Token usage statistics."""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens

    def add(self, other: TokenUsage) -> None:
        """Add another TokenUsage to this one."""
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens


class AgentResponse(BaseModel):
    """Response from a single agent invocation."""

    agent_name: str
    content: str
    tokens_used: TokenUsage = Field(default_factory=TokenUsage)
    latency_ms: float = 0.0
    cost: float = 0.0
    model: str = ""
    error: str | None = None


class HarnessResult(BaseModel):
    """Result from running a blueprint against an input."""

    final_output: str = ""
    total_tokens: TokenUsage = Field(default_factory=TokenUsage)
    total_cost: float = 0.0
    total_latency_ms: float = 0.0
    agent_traces: list[AgentResponse] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    rounds_executed: int = 0


class AgentRuntime:
    """Runtime for a single agent within a multi-agent system."""

    def __init__(
        self,
        agent_name: str,
        model: str,
        max_tokens: int,
        temperature: float,
        provider: LLMProvider,
    ) -> None:
        """Initialize agent runtime.

        Args:
            agent_name: Name of the agent.
            model: Model identifier.
            max_tokens: Maximum output tokens.
            temperature: Sampling temperature.
            provider: LLM provider to use.
        """
        self.agent_name = agent_name
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.provider = provider

    async def run(self, messages: list[dict[str, str]]) -> AgentResponse:
        """Run the agent.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.

        Returns:
            AgentResponse with output, tokens, latency, and cost.
        """
        start_time = time.time()

        try:
            response = await self.provider.complete(
                messages=messages,
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            latency_ms = (time.time() - start_time) * 1000

            # Calculate cost (rough estimate)
            cost = self._estimate_cost(response)

            return AgentResponse(
                agent_name=self.agent_name,
                content=response.content,
                tokens_used=TokenUsage(
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                ),
                latency_ms=latency_ms,
                cost=cost,
                model=self.model,
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return AgentResponse(
                agent_name=self.agent_name,
                content="",
                tokens_used=TokenUsage(),
                latency_ms=latency_ms,
                cost=0.0,
                model=self.model,
                error=str(e),
            )

    def _estimate_cost(self, response: ProviderResponse) -> float:
        """Estimate cost for a response.

        Args:
            response: Provider response.

        Returns:
            Estimated cost in USD.
        """
        # Pricing per 1M tokens (approximate)
        pricing = {
            "claude-opus-4-6": (5.0, 25.0),
            "claude-sonnet-4-6": (3.0, 15.0),
            "claude-haiku-4-5": (1.0, 5.0),
            "gpt-4o": (2.5, 10.0),
            "gpt-4o-mini": (0.15, 0.60),
            "gemini-2.5-pro": (4.0, 20.0),
            "gemini-2.5-flash": (0.30, 2.50),
        }

        input_price, output_price = pricing.get(self.model, (3.0, 15.0))
        cost = (response.input_tokens / 1_000_000 * input_price) + (
            response.output_tokens / 1_000_000 * output_price
        )
        return round(cost, 6)


class RuntimeHarness:
    """Harness for running a blueprint against inputs."""

    def __init__(
        self,
        blueprint: Blueprint,
        provider: LLMProvider | None = None,
    ) -> None:
        """Initialize runtime harness.

        Args:
            blueprint: Blueprint defining the multi-agent system.
            provider: LLM provider. Defaults to MockProvider if not provided.
        """
        self.blueprint = blueprint
        self.provider = provider or MockProvider()
        self.agent_runtimes: dict[str, AgentRuntime] = {}

        # Initialize agent runtimes
        for agent_spec in blueprint.agents:
            self.agent_runtimes[agent_spec.name] = AgentRuntime(
                agent_name=agent_spec.name,
                model=agent_spec.model.primary,
                max_tokens=agent_spec.token_budget,
                temperature=agent_spec.model.temperature,
                provider=self.provider,
            )

    async def run(
        self,
        input_message: str,
        max_rounds: int = 10,
    ) -> HarnessResult:
        """Run the blueprint against an input message.

        Args:
            input_message: The input message to process.
            max_rounds: Maximum number of rounds to execute.

        Returns:
            HarnessResult with final output, token usage, cost, and agent traces.
        """
        result = HarnessResult()
        messages: list[dict[str, str]] = [
            {"role": "user", "content": input_message},
        ]

        # For now, simple single-pass execution
        # In a real implementation, this would handle multi-agent coordination
        orchestrator = self.blueprint.get_orchestrator()

        if orchestrator:
            # If there's an orchestrator, route through it
            runtime = self.agent_runtimes.get(orchestrator.name)
            if runtime:
                agent_response = await runtime.run(messages)
                result.agent_traces.append(agent_response)
                if agent_response.error:
                    result.errors.append(agent_response.error)
                else:
                    result.final_output = agent_response.content
                    result.total_tokens.add(agent_response.tokens_used)
                    result.total_cost += agent_response.cost
                    result.total_latency_ms += agent_response.latency_ms
                result.rounds_executed = 1
        else:
            # If no orchestrator, call first agent
            if self.blueprint.agents:
                first_agent = self.blueprint.agents[0]
                runtime = self.agent_runtimes.get(first_agent.name)
                if runtime:
                    agent_response = await runtime.run(messages)
                    result.agent_traces.append(agent_response)
                    if agent_response.error:
                        result.errors.append(agent_response.error)
                    else:
                        result.final_output = agent_response.content
                        result.total_tokens.add(agent_response.tokens_used)
                        result.total_cost += agent_response.cost
                        result.total_latency_ms += agent_response.latency_ms
                    result.rounds_executed = 1

        return result
