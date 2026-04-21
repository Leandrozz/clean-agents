"""Blueprint: the central data model representing an entire agentic system design."""

from __future__ import annotations

from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from clean_agents.core.agent import AgentSpec, AutonomyLevel


class SystemType(str, Enum):
    SINGLE_AGENT = "single-agent"
    PIPELINE = "pipeline"
    MULTI_AGENT = "multi-agent"
    COMPLEX_SYSTEM = "complex-system"


class ArchitecturePattern(str, Enum):
    SINGLE = "single"
    PIPELINE = "pipeline"
    SUPERVISOR_HIERARCHICAL = "supervisor-hierarchical"
    BLACKBOARD_SWARM = "blackboard-swarm"
    HYBRID = "hybrid-hierarchical-swarm"


class InfraConfig(BaseModel):
    """Infrastructure configuration."""

    vector_db: str | None = None
    graph_db: str | None = None
    message_queue: str | None = None
    observability: str | None = None
    hosting: str | None = None


class ComplianceConfig(BaseModel):
    """Compliance requirements."""

    regulations: list[str] = Field(default_factory=list)
    data_residency: str | None = None
    audit_trail: bool = True


class CostConfig(BaseModel):
    """Cost constraints and optimization settings."""

    budget_monthly: float | None = None
    optimization: dict[str, bool] = Field(
        default_factory=lambda: {"routing": True, "caching": True, "batch": False}
    )


class TimelineConfig(BaseModel):
    """Project timeline."""

    start: date | None = None
    target_mvp: date | None = None
    target_prod: date | None = None


class ResearchFinding(BaseModel):
    """A research finding backing an architectural decision."""

    source: str = Field(description="Paper title, URL, or reference")
    finding: str = Field(description="Key finding or metric")
    relevance: str = Field(description="How this applies to the current design")
    year: int | None = None


class DesignDecision(BaseModel):
    """A recorded design decision with justification."""

    dimension: str = Field(description="Which dimension this decision affects (D1-D12)")
    decision: str = Field(description="What was decided")
    justification: str = Field(description="Why, with evidence")
    research: list[ResearchFinding] = Field(default_factory=list)
    alternatives_considered: list[str] = Field(default_factory=list)
    cascading_effects: list[str] = Field(default_factory=list)


class Blueprint(BaseModel):
    """Complete system architecture blueprint — source of truth for CLean-agents."""

    # Metadata
    version: str = "1.0"
    name: str = Field(description="Project name (kebab-case)")
    description: str = Field(default="", description="System description")
    language: str = Field(default="en", description="Output language (en, es, pt, fr, de)")
    created_at: str | None = None
    updated_at: str | None = None

    # System classification
    system_type: SystemType = SystemType.MULTI_AGENT
    pattern: ArchitecturePattern = ArchitecturePattern.SUPERVISOR_HIERARCHICAL
    domain: str = Field(default="general", description="Domain (legal, medical, financial, etc.)")
    scale: str = Field(default="medium", description="small, medium, large, enterprise")
    autonomy: AutonomyLevel = AutonomyLevel.L3_ACTIVE_APPROVAL
    framework: str = Field(default="langgraph", description="Recommended framework")

    # Agents
    agents: list[AgentSpec] = Field(default_factory=list)

    # Infrastructure
    infrastructure: InfraConfig = Field(default_factory=InfraConfig)

    # Compliance
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig)

    # Cost
    cost: CostConfig = Field(default_factory=CostConfig)

    # Timeline
    timeline: TimelineConfig = Field(default_factory=TimelineConfig)

    # Design history
    decisions: list[DesignDecision] = Field(default_factory=list)
    research_findings: list[ResearchFinding] = Field(default_factory=list)

    # Iteration tracking
    iteration: int = Field(default=1, description="Current design iteration")
    changelog: list[str] = Field(default_factory=list)

    # --- Methods ---

    def get_agent(self, name: str) -> AgentSpec | None:
        """Get agent by name."""
        return next((a for a in self.agents if a.name == name), None)

    def get_orchestrator(self) -> AgentSpec | None:
        """Get the orchestrator agent (if any)."""
        return next((a for a in self.agents if a.is_orchestrator()), None)

    def agent_names(self) -> list[str]:
        """List all agent names."""
        return [a.name for a in self.agents]

    def total_agents(self) -> int:
        return len(self.agents)

    def has_graphrag(self) -> bool:
        return any(a.memory.graphrag for a in self.agents)

    def has_hitl(self) -> bool:
        return any(a.hitl != "none" for a in self.agents)

    def applicable_regulations(self) -> list[str]:
        return self.compliance.regulations

    def estimated_cost_per_request(self) -> float:
        """Rough cost estimate based on agent models and token budgets."""
        pricing = {
            "claude-opus-4-6": (5.0, 25.0),
            "claude-sonnet-4-6": (3.0, 15.0),
            "claude-haiku-4-5": (1.0, 5.0),
            "gpt-4o": (2.5, 10.0),
            "gpt-4o-mini": (0.15, 0.60),
            "gemini-2.5-pro": (4.0, 20.0),
            "gemini-2.5-flash": (0.30, 2.50),
        }
        total = 0.0
        for agent in self.agents:
            input_price, output_price = pricing.get(agent.model.primary, (3.0, 15.0))
            input_tokens = agent.total_input_tokens_estimate()
            output_tokens = agent.token_budget
            cost = (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)
            total += cost
        return round(total, 4)

    def save(self, path: Path, version_description: str = "") -> None:
        """Save blueprint to YAML file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(mode="json", exclude_none=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        # Auto-snapshot if inside a .clean-agents project
        try:
            project_dir = path.parent
            if (project_dir / "config.yaml").exists() or project_dir.name == ".clean-agents":
                from clean_agents.core.versioning import VersionManager
                vm = VersionManager(project_dir)
                vm.snapshot(self, version_description or f"Saved at {path.name}")
        except Exception:
            pass  # Never fail the save due to versioning

    @classmethod
    def load(cls, path: Path) -> Blueprint:
        """Load blueprint from YAML file."""
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)

    def to_yaml(self) -> str:
        """Serialize to YAML string."""
        data = self.model_dump(mode="json", exclude_none=True)
        return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def summary(self) -> dict[str, Any]:
        """Quick summary for display."""
        return {
            "name": self.name,
            "type": self.system_type.value,
            "pattern": self.pattern.value,
            "agents": self.total_agents(),
            "framework": self.framework,
            "domain": self.domain,
            "has_graphrag": self.has_graphrag(),
            "has_hitl": self.has_hitl(),
            "compliance": self.applicable_regulations(),
            "est_cost_per_request": f"${self.estimated_cost_per_request():.4f}",
            "iteration": self.iteration,
        }
