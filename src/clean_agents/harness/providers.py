"""LLM provider abstraction and implementations."""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ProviderResponse(BaseModel):
    """Response from an LLM provider call."""

    content: str
    input_tokens: int
    output_tokens: int
    model: str
    latency_ms: float


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> ProviderResponse:
        """Complete a message sequence with the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Model identifier.
            max_tokens: Maximum output tokens.
            temperature: Sampling temperature (0.0-2.0).

        Returns:
            ProviderResponse with content, token counts, and latency.
        """
        ...


class AnthropicProvider(LLMProvider):
    """Real Anthropic API provider."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key. Defaults to ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create Anthropic client."""
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> ProviderResponse:
        """Complete a message sequence using Anthropic API."""
        client = self._get_client()
        start_time = time.time()

        # Extract system message if present
        system_message = ""
        request_messages = messages
        if messages and messages[0].get("role") == "system":
            system_message = messages[0]["content"]
            request_messages = messages[1:]

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_message if system_message else None,
            messages=request_messages,
        )

        latency_ms = (time.time() - start_time) * 1000
        content = response.content[0].text if response.content else ""

        return ProviderResponse(
            content=content,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=model,
            latency_ms=latency_ms,
        )


class OpenAIProvider(LLMProvider):
    """Real OpenAI API provider."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key. Defaults to OPENAI_API_KEY env var.
        """
        self.api_key = api_key
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create OpenAI client."""
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key)
        return self._client

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> ProviderResponse:
        """Complete a message sequence using OpenAI API."""
        client = self._get_client()
        start_time = time.time()

        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,
        )

        latency_ms = (time.time() - start_time) * 1000
        content = response.choices[0].message.content or ""

        return ProviderResponse(
            content=content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            model=model,
            latency_ms=latency_ms,
        )


class MockProvider(LLMProvider):
    """Mock provider for testing — returns configurable responses."""

    def __init__(
        self,
        responses: dict[str, str] | None = None,
        default_response: str = "Mock response",
    ) -> None:
        """Initialize mock provider.

        Args:
            responses: Mapping of agent_name or model to specific responses.
            default_response: Default response to return if no match found.
        """
        self.responses = responses or {}
        self.default_response = default_response
        self.call_count = 0

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> ProviderResponse:
        """Return a mock response."""
        self.call_count += 1

        # Try to find a matching response by model or fall back to default
        content = self.responses.get(model, self.default_response)

        # Simulate some latency
        await asyncio.sleep(0.01)

        # Estimate tokens based on content length
        input_tokens = sum(
            len(str(msg.get("content", "")).split()) for msg in messages
        )
        output_tokens = len(content.split())

        return ProviderResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            latency_ms=10.0,
        )
