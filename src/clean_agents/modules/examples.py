"""Example plugins that ship with CLean-agents.

These serve as both useful defaults and reference implementations
for building custom plugins.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from clean_agents.core.blueprint import Blueprint
from clean_agents.modules.base import (
    AnalysisPlugin,
    PluginManifest,
    PluginResult,
    PluginType,
    TransformPlugin,
)


# ── Analysis Plugin: Token Budget Auditor ─────────────────────────────────────


class TokenBudgetAuditor(AnalysisPlugin):
    """Checks if agent token budgets are aligned with their roles.

    Flags agents that are over- or under-budgeted based on heuristics:
      - Orchestrators shouldn't need >4K output tokens
      - Classifiers shouldn't need >1K output tokens
      - Agents with reflection reasoning need more tokens
      - GraphRAG agents need larger context windows
    """

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="token-budget-auditor",
            version="0.1.0",
            description="Audit agent token budgets for over/under-allocation",
            author="CLean-agents",
            plugin_type=PluginType.ANALYSIS,
            cli_command="audit-tokens",
        )

    def analyze(self, blueprint: Blueprint, config: dict[str, Any] | None = None) -> PluginResult:
        findings = []

        for agent in blueprint.agents:
            # Orchestrator budget check
            if agent.agent_type == "orchestrator" and agent.token_budget > 4000:
                findings.append({
                    "agent": agent.name,
                    "severity": "warning",
                    "message": f"Orchestrator has {agent.token_budget} token budget — typically needs ≤4K for routing decisions",
                    "suggestion": "Reduce to 2000-4000 to save ~40% on orchestrator cost",
                })

            # Classifier budget check
            if agent.agent_type == "classifier" and agent.token_budget > 1000:
                findings.append({
                    "agent": agent.name,
                    "severity": "warning",
                    "message": f"Classifier has {agent.token_budget} token budget — classification outputs are typically short",
                    "suggestion": "Reduce to 500-1000 for cost optimization",
                })

            # Guardian budget check
            if agent.agent_type == "guardian" and agent.token_budget > 1000:
                findings.append({
                    "agent": agent.name,
                    "severity": "info",
                    "message": f"Guardian has {agent.token_budget} token budget — safety checks produce short outputs",
                    "suggestion": "Consider reducing to 500 unless detailed explanations are needed",
                })

            # Reflection agents need more tokens
            if agent.reasoning.value == "reflection" and agent.token_budget < 4000:
                findings.append({
                    "agent": agent.name,
                    "severity": "warning",
                    "message": f"Reflection agent has only {agent.token_budget} tokens — reflection requires room for self-critique",
                    "suggestion": "Increase to ≥4000 for effective reflection loops",
                })

            # Tree-of-thoughts needs even more
            if agent.reasoning.value == "tree-of-thoughts" and agent.token_budget < 6000:
                findings.append({
                    "agent": agent.name,
                    "severity": "warning",
                    "message": f"Tree-of-thoughts agent has only {agent.token_budget} tokens — needs room for multiple reasoning paths",
                    "suggestion": "Increase to ≥6000 for effective branch exploration",
                })

        status = "optimal" if not findings else f"{len(findings)} issues found"
        return PluginResult(
            plugin_name="token-budget-auditor",
            success=True,
            findings=findings,
            summary=f"Token budget audit: {status}",
        )


# ── Analysis Plugin: Redundancy Detector ──────────────────────────────────────


class RedundancyDetector(AnalysisPlugin):
    """Detects redundant agents that could be merged.

    Checks for:
      - Agents with identical models and similar roles
      - Overlapping tool sets
      - Agents that could be a single agent with multiple tools
    """

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="redundancy-detector",
            version="0.1.0",
            description="Detect potentially redundant agents that could be merged",
            author="CLean-agents",
            plugin_type=PluginType.ANALYSIS,
            cli_command="detect-redundancy",
        )

    def analyze(self, blueprint: Blueprint, config: dict[str, Any] | None = None) -> PluginResult:
        findings = []
        agents = blueprint.agents

        for i, a1 in enumerate(agents):
            for a2 in agents[i + 1:]:
                if a1.agent_type != a2.agent_type:
                    continue
                if a1.model.primary != a2.model.primary:
                    continue

                # Same type + same model = potential redundancy
                score = self._similarity_score(a1, a2)
                if score > 0.6:
                    findings.append({
                        "agents": [a1.name, a2.name],
                        "severity": "info" if score < 0.8 else "warning",
                        "similarity": round(score, 2),
                        "message": f"Agents '{a1.name}' and '{a2.name}' are {int(score * 100)}% similar — consider merging",
                        "suggestion": f"Merge into a single agent with combined capabilities to reduce latency and cost",
                    })

        return PluginResult(
            plugin_name="redundancy-detector",
            success=True,
            findings=findings,
            summary=f"Redundancy check: {len(findings)} potential merges found" if findings else "No redundancies detected",
        )

    def _similarity_score(self, a1, a2) -> float:
        """Compute a rough similarity score between two agents."""
        score = 0.0
        weights = 0.0

        # Same model = +0.3
        if a1.model.primary == a2.model.primary:
            score += 0.3
        weights += 0.3

        # Same reasoning = +0.2
        if a1.reasoning == a2.reasoning:
            score += 0.2
        weights += 0.2

        # Similar memory config = +0.2
        mem_match = sum([
            a1.memory.short_term == a2.memory.short_term,
            a1.memory.episodic == a2.memory.episodic,
            a1.memory.semantic == a2.memory.semantic,
            a1.memory.graphrag == a2.memory.graphrag,
        ])
        score += 0.2 * (mem_match / 4)
        weights += 0.2

        # Similar token budget = +0.15
        budget_ratio = min(a1.token_budget, a2.token_budget) / max(a1.token_budget, a2.token_budget)
        score += 0.15 * budget_ratio
        weights += 0.15

        # Same HITL = +0.15
        if a1.hitl == a2.hitl:
            score += 0.15
        weights += 0.15

        return score / weights if weights > 0 else 0


# ── Transform Plugin: Cost Optimizer ──────────────────────────────────────────


class CostOptimizer(TransformPlugin):
    """Automatically downgrades models where possible to reduce cost.

    Rules:
      - Classifiers → cheapest model meeting BFCL threshold
      - Guardians → cheapest model
      - Orchestrators → best tool-use model (BFCL optimized)
      - Specialists with reflection → keep premium
      - Others → try downgrading one tier
    """

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="cost-optimizer",
            version="0.1.0",
            description="Automatically optimize model assignments for cost",
            author="CLean-agents",
            plugin_type=PluginType.TRANSFORM,
            cli_command="optimize-cost",
        )

    def transform(self, blueprint: Blueprint, config: dict[str, Any] | None = None) -> PluginResult:
        findings = []
        original_cost = blueprint.estimated_cost_per_request()

        for agent in blueprint.agents:
            old_model = agent.model.primary
            new_model = self._optimize_model(agent)

            if new_model != old_model:
                agent.model.primary = new_model
                findings.append({
                    "agent": agent.name,
                    "old_model": old_model,
                    "new_model": new_model,
                    "severity": "info",
                    "message": f"Downgraded {agent.name}: {old_model} → {new_model}",
                })

        new_cost = blueprint.estimated_cost_per_request()
        savings = original_cost - new_cost
        savings_pct = (savings / original_cost * 100) if original_cost > 0 else 0

        return PluginResult(
            plugin_name="cost-optimizer",
            success=True,
            findings=findings,
            data={
                "original_cost": round(original_cost, 5),
                "optimized_cost": round(new_cost, 5),
                "savings_per_request": round(savings, 5),
                "savings_percent": round(savings_pct, 1),
            },
            modified_blueprint=blueprint,
            summary=f"Optimized: ${original_cost:.5f} → ${new_cost:.5f} ({savings_pct:.1f}% savings)",
        )

    def _optimize_model(self, agent) -> str:
        """Select optimal model for an agent based on role."""
        if agent.agent_type == "classifier":
            return "claude-haiku-4-5"
        if agent.agent_type == "guardian":
            return "claude-haiku-4-5"
        if agent.agent_type == "orchestrator":
            return "claude-sonnet-4-6"  # Best BFCL + reasonable cost
        if agent.reasoning.value in ("reflection", "tree-of-thoughts"):
            return agent.model.primary  # Keep premium for reasoning
        if agent.agent_type == "specialist":
            # Downgrade one tier if on opus
            if agent.model.primary == "claude-opus-4-6":
                return "claude-sonnet-4-6"
        return agent.model.primary


# ── Built-in plugins registration ─────────────────────────────────────────────

BUILTIN_PLUGINS: list[type] = [
    TokenBudgetAuditor,
    RedundancyDetector,
    CostOptimizer,
]
