"""Middleware interceptors for the runtime harness."""

from __future__ import annotations

import asyncio
import random
import time
from abc import ABC, abstractmethod

from rich.console import Console

from clean_agents.harness.runtime import AgentResponse

console = Console()


class Interceptor(ABC):
    """Middleware that can inspect/modify messages between agents."""

    @abstractmethod
    async def before_call(
        self,
        agent_name: str,
        message: str,
        context: dict,
    ) -> str:
        """Hook called before agent invocation.

        Args:
            agent_name: Name of the agent being called.
            message: Input message to the agent.
            context: Execution context.

        Returns:
            Modified message, or original if unchanged.
        """
        ...

    @abstractmethod
    async def after_call(
        self,
        agent_name: str,
        response: AgentResponse,
    ) -> AgentResponse:
        """Hook called after agent invocation.

        Args:
            agent_name: Name of the agent that was called.
            response: Agent response object.

        Returns:
            Modified response, or original if unchanged.
        """
        ...


class LoggingInterceptor(Interceptor):
    """Logs all agent interactions."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize logging interceptor.

        Args:
            verbose: If True, logs full content. Otherwise logs summaries.
        """
        self.verbose = verbose

    async def before_call(
        self,
        agent_name: str,
        message: str,
        context: dict,
    ) -> str:
        """Log before agent call."""
        if self.verbose:
            console.print(f"[cyan]→ {agent_name}[/] input: {message[:100]}...")
        else:
            console.print(f"[cyan]→ {agent_name}[/]")
        return message

    async def after_call(
        self,
        agent_name: str,
        response: AgentResponse,
    ) -> AgentResponse:
        """Log after agent call."""
        tokens = response.tokens_used
        console.print(
            f"[green]← {agent_name}[/] "
            f"({response.latency_ms:.0f}ms, "
            f"in={tokens.input_tokens} out={tokens.output_tokens})"
        )
        return response


class GuardrailInterceptor(Interceptor):
    """Applies guardrail checks based on AgentSpec config."""

    async def before_call(
        self,
        agent_name: str,
        message: str,
        context: dict,
    ) -> str:
        """Apply input guardrails."""
        # Placeholder: actual guardrail logic would be implemented here
        # based on the agent's guardrails config
        return message

    async def after_call(
        self,
        agent_name: str,
        response: AgentResponse,
    ) -> AgentResponse:
        """Apply output guardrails."""
        # Placeholder: actual guardrail validation would be implemented here
        return response


class FaultInjector(Interceptor):
    """Injects failures for resilience testing."""

    class FaultInjectionError(Exception):
        """Raised when fault injection is triggered."""

        pass

    def __init__(
        self,
        failure_rate: float = 0.1,
        target_agents: list[str] | None = None,
    ) -> None:
        """Initialize fault injector.

        Args:
            failure_rate: Probability of failure (0.0-1.0).
            target_agents: If specified, only inject failures for these agents.
        """
        self.failure_rate = max(0.0, min(1.0, failure_rate))
        self.target_agents = target_agents or []

    async def before_call(
        self,
        agent_name: str,
        message: str,
        context: dict,
    ) -> str:
        """Inject faults before agent call."""
        should_fail = (
            (not self.target_agents or agent_name in self.target_agents)
            and random.random() < self.failure_rate
        )
        if should_fail:
            raise self.FaultInjectionError(f"Injected failure for {agent_name}")
        return message

    async def after_call(
        self,
        agent_name: str,
        response: AgentResponse,
    ) -> AgentResponse:
        """No-op for after call."""
        return response


class LatencyInjector(Interceptor):
    """Adds artificial latency for testing timeout handling."""

    def __init__(
        self,
        latency_ms: int = 1000,
        target_agents: list[str] | None = None,
    ) -> None:
        """Initialize latency injector.

        Args:
            latency_ms: Latency to inject in milliseconds.
            target_agents: If specified, only inject latency for these agents.
        """
        self.latency_ms = latency_ms
        self.target_agents = target_agents or []

    async def before_call(
        self,
        agent_name: str,
        message: str,
        context: dict,
    ) -> str:
        """Inject latency before agent call."""
        should_delay = not self.target_agents or agent_name in self.target_agents
        if should_delay:
            await asyncio.sleep(self.latency_ms / 1000.0)
        return message

    async def after_call(
        self,
        agent_name: str,
        response: AgentResponse,
    ) -> AgentResponse:
        """No-op for after call."""
        return response


class CostTracker(Interceptor):
    """Tracks cumulative cost and can enforce budget limits."""

    class BudgetExceeded(Exception):
        """Raised when cost budget is exceeded."""

        pass

    def __init__(self, budget_limit: float | None = None) -> None:
        """Initialize cost tracker.

        Args:
            budget_limit: Maximum allowed cost in USD. None = unlimited.
        """
        self.budget_limit = budget_limit
        self.total_cost = 0.0
        self.call_count = 0

    async def before_call(
        self,
        agent_name: str,
        message: str,
        context: dict,
    ) -> str:
        """Check budget before call."""
        if self.budget_limit and self.total_cost >= self.budget_limit:
            raise self.BudgetExceeded(
                f"Budget limit ${self.budget_limit:.2f} exceeded. "
                f"Current cost: ${self.total_cost:.2f}"
            )
        return message

    async def after_call(
        self,
        agent_name: str,
        response: AgentResponse,
    ) -> AgentResponse:
        """Track cost after call."""
        self.total_cost += response.cost
        self.call_count += 1
        return response

    def get_summary(self) -> dict:
        """Get cost tracking summary."""
        return {
            "total_cost": round(self.total_cost, 4),
            "call_count": self.call_count,
            "avg_cost_per_call": round(self.total_cost / self.call_count, 4)
            if self.call_count > 0
            else 0.0,
            "budget_limit": self.budget_limit,
            "remaining_budget": (
                round(self.budget_limit - self.total_cost, 4)
                if self.budget_limit
                else None
            ),
        }
