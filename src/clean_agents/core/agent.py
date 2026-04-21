"""Agent specification data models."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ReasoningPattern(str, Enum):
    REACT = "react"
    TREE_OF_THOUGHTS = "tree-of-thoughts"
    GRAPH_OF_THOUGHTS = "graph-of-thoughts"
    HTN_PLANNING = "htn-planning"
    REFLECTION = "reflection"
    REASONING_MODEL = "reasoning-model"


class HITLMode(str, Enum):
    NONE = "none"
    PRE_ACTION = "pre-action"
    POST_ACTION = "post-action"
    TOOL_LEVEL = "tool-level"


class AutonomyLevel(str, Enum):
    L1_FULL_AUTO = "L1"
    L2_PASSIVE = "L2"
    L3_ACTIVE_APPROVAL = "L3"
    L4_COPILOT = "L4"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModelConfig(BaseModel):
    """LLM model configuration for an agent."""

    primary: str = Field(description="Primary model identifier (e.g., 'claude-opus-4-6')")
    fallback: str | None = Field(default=None, description="Fallback model if primary fails")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, gt=0)


class Memory(BaseModel):
    """Memory configuration for an agent."""

    short_term: bool = Field(default=True, description="Context window management")
    episodic: bool = Field(default=False, description="Vector DB with timestamps")
    semantic: bool = Field(default=False, description="Structured facts/rules store")
    procedural: bool = Field(default=False, description="Learned skills repository")
    graphrag: bool = Field(default=False, description="Knowledge graph + RAG retrieval")


class Guardrails(BaseModel):
    """Input/output safety filters for an agent."""

    input: list[str] = Field(
        default_factory=list,
        description="Input filters (e.g., injection_detection, encoding_detection, pii_detection, size_limit)",
    )
    output: list[str] = Field(
        default_factory=list,
        description="Output validators (e.g., schema_validation, pii_masking, confidence_threshold, content_filter)",
    )


class ToolSpec(BaseModel):
    """Tool available to an agent."""

    name: str
    description: str
    risk_level: RiskLevel = RiskLevel.LOW
    parameters: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False


class MetricTarget(BaseModel):
    """Performance metric target for an agent."""

    name: str
    target: float
    alert_threshold: float | None = None
    unit: str = ""


class AgentSpec(BaseModel):
    """Complete specification for a single agent in the system."""

    name: str = Field(description="Agent identifier (snake_case)")
    role: str = Field(description="One sentence describing what this agent does")
    agent_type: str = Field(
        default="specialist",
        description="Agent type: orchestrator, specialist, classifier, extractor, guardian",
    )
    model: ModelConfig = Field(default_factory=lambda: ModelConfig(primary="claude-sonnet-4-6"))
    reasoning: ReasoningPattern = ReasoningPattern.REACT
    tools: list[ToolSpec] = Field(default_factory=list)
    memory: Memory = Field(default_factory=Memory)
    guardrails: Guardrails = Field(default_factory=Guardrails)
    hitl: HITLMode = HITLMode.NONE
    token_budget: int = Field(default=4096, description="Max output tokens per operation")
    metrics: list[MetricTarget] = Field(default_factory=list)
    dependencies: list[str] = Field(
        default_factory=list,
        description="Names of agents this agent depends on",
    )
    estimated_cost_per_call: float | None = Field(
        default=None, description="Estimated cost in USD per invocation"
    )

    def is_orchestrator(self) -> bool:
        return self.agent_type == "orchestrator"

    def total_input_tokens_estimate(self) -> int:
        """Estimate total input tokens (system prompt + avg user input)."""
        base = {"orchestrator": 3500, "specialist": 3000, "classifier": 800, "extractor": 2000, "guardian": 1000}
        return base.get(self.agent_type, 2000)
