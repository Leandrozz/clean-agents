"""Tests for the plugin system."""

from clean_agents.core.agent import AgentSpec, Guardrails, HITLMode, Memory, ModelConfig, ReasoningPattern
from clean_agents.core.blueprint import ArchitecturePattern, Blueprint, SystemType
from clean_agents.modules.base import (
    AnalysisPlugin,
    PluginManifest,
    PluginRegistry,
    PluginResult,
    PluginType,
    TransformPlugin,
    get_registry,
)
from clean_agents.modules.examples import CostOptimizer, RedundancyDetector, TokenBudgetAuditor


def _test_blueprint() -> Blueprint:
    return Blueprint(
        name="test-system",
        description="Test",
        system_type=SystemType.MULTI_AGENT,
        pattern=ArchitecturePattern.SUPERVISOR_HIERARCHICAL,
        agents=[
            AgentSpec(
                name="orchestrator", role="Route tasks", agent_type="orchestrator",
                model=ModelConfig(primary="claude-opus-4-6"), token_budget=6000,
            ),
            AgentSpec(
                name="classifier", role="Classify tickets", agent_type="classifier",
                model=ModelConfig(primary="claude-sonnet-4-6"), token_budget=2000,
            ),
            AgentSpec(
                name="analyst", role="Analyze data", agent_type="specialist",
                model=ModelConfig(primary="claude-sonnet-4-6"),
                reasoning=ReasoningPattern.REFLECTION, token_budget=3000,
            ),
            AgentSpec(
                name="guardian", role="Safety filter", agent_type="guardian",
                model=ModelConfig(primary="claude-haiku-4-5"), token_budget=1500,
            ),
        ],
    )


# ── Registry ──────────────────────────────────────────────────────────────────


def test_registry_register_and_list():
    registry = PluginRegistry()
    plugin = TokenBudgetAuditor()
    registry.register(plugin)
    manifests = registry.list_plugins()
    assert len(manifests) == 1
    assert manifests[0].name == "token-budget-auditor"


def test_registry_unregister():
    registry = PluginRegistry()
    registry.register(TokenBudgetAuditor())
    registry.unregister("token-budget-auditor")
    assert len(registry.list_plugins()) == 0


def test_registry_get():
    registry = PluginRegistry()
    registry.register(TokenBudgetAuditor())
    assert registry.get("token-budget-auditor") is not None
    assert registry.get("nonexistent") is None


def test_registry_run_analysis():
    registry = PluginRegistry()
    registry.register(TokenBudgetAuditor())
    bp = _test_blueprint()
    result = registry.run_analysis("token-budget-auditor", bp)
    assert result.success
    assert result.plugin_name == "token-budget-auditor"


def test_registry_run_nonexistent():
    registry = PluginRegistry()
    result = registry.run_analysis("nonexistent", _test_blueprint())
    assert not result.success


def test_registry_run_all_analysis():
    registry = PluginRegistry()
    registry.register(TokenBudgetAuditor())
    registry.register(RedundancyDetector())
    results = registry.run_all_analysis(_test_blueprint())
    assert len(results) == 2


# ── Token Budget Auditor ──────────────────────────────────────────────────────


def test_token_auditor_flags_orchestrator():
    bp = _test_blueprint()
    auditor = TokenBudgetAuditor()
    result = auditor.analyze(bp)
    # Orchestrator has 6000 tokens (> 4000 threshold)
    orch_findings = [f for f in result.findings if f["agent"] == "orchestrator"]
    assert len(orch_findings) >= 1


def test_token_auditor_flags_classifier():
    bp = _test_blueprint()
    auditor = TokenBudgetAuditor()
    result = auditor.analyze(bp)
    # Classifier has 2000 tokens (> 1000 threshold)
    cls_findings = [f for f in result.findings if f["agent"] == "classifier"]
    assert len(cls_findings) >= 1


def test_token_auditor_flags_guardian():
    bp = _test_blueprint()
    auditor = TokenBudgetAuditor()
    result = auditor.analyze(bp)
    guardian_findings = [f for f in result.findings if f["agent"] == "guardian"]
    assert len(guardian_findings) >= 1


def test_token_auditor_flags_low_reflection():
    bp = Blueprint(
        name="test", description="Test",
        system_type=SystemType.SINGLE_AGENT,
        pattern=ArchitecturePattern.SINGLE,
        agents=[AgentSpec(
            name="thinker", role="Think deeply",
            reasoning=ReasoningPattern.REFLECTION, token_budget=2000,
        )],
    )
    result = TokenBudgetAuditor().analyze(bp)
    assert any(f["agent"] == "thinker" for f in result.findings)


# ── Redundancy Detector ───────────────────────────────────────────────────────


def test_redundancy_no_false_positives():
    bp = _test_blueprint()
    result = RedundancyDetector().analyze(bp)
    # Different types shouldn't be flagged
    assert result.success


def test_redundancy_detects_similar():
    bp = Blueprint(
        name="test", description="Test",
        system_type=SystemType.MULTI_AGENT,
        pattern=ArchitecturePattern.SUPERVISOR_HIERARCHICAL,
        agents=[
            AgentSpec(name="agent_a", role="Analyze docs", agent_type="specialist",
                      model=ModelConfig(primary="claude-sonnet-4-6"), token_budget=4000),
            AgentSpec(name="agent_b", role="Review docs", agent_type="specialist",
                      model=ModelConfig(primary="claude-sonnet-4-6"), token_budget=4000),
        ],
    )
    result = RedundancyDetector().analyze(bp)
    assert len(result.findings) >= 1
    assert "agent_a" in str(result.findings[0])


# ── Cost Optimizer ────────────────────────────────────────────────────────────


def test_cost_optimizer_downgrades():
    bp = _test_blueprint()
    original_cost = bp.estimated_cost_per_request()
    optimizer = CostOptimizer()
    result = optimizer.transform(bp)
    assert result.success
    assert result.modified_blueprint is not None
    # Should downgrade orchestrator from opus to sonnet
    orch = result.modified_blueprint.get_agent("orchestrator")
    assert orch.model.primary == "claude-sonnet-4-6"
    # Classifier should go to haiku
    cls = result.modified_blueprint.get_agent("classifier")
    assert cls.model.primary == "claude-haiku-4-5"
    # Guardian should stay haiku
    guard = result.modified_blueprint.get_agent("guardian")
    assert guard.model.primary == "claude-haiku-4-5"
    # Should have savings
    assert result.data["savings_percent"] > 0


def test_cost_optimizer_keeps_reflection():
    bp = _test_blueprint()
    optimizer = CostOptimizer()
    result = optimizer.transform(bp)
    analyst = result.modified_blueprint.get_agent("analyst")
    # Reflection specialist should keep its model
    assert analyst.model.primary == "claude-sonnet-4-6"


# ── Plugin Result ─────────────────────────────────────────────────────────────


def test_plugin_result_to_dict():
    result = PluginResult("test", success=True, summary="All good", findings=[{"a": 1}])
    d = result.to_dict()
    assert d["plugin"] == "test"
    assert d["success"] is True
    assert len(d["findings"]) == 1


# ── Custom Plugin ─────────────────────────────────────────────────────────────


class _TestPlugin(AnalysisPlugin):
    def manifest(self):
        return PluginManifest(name="test-plugin", version="1.0", description="Test", plugin_type=PluginType.ANALYSIS)
    def analyze(self, blueprint, config=None):
        return PluginResult("test-plugin", success=True, summary="OK")


def test_custom_plugin():
    registry = PluginRegistry()
    registry.register(_TestPlugin())
    result = registry.run_analysis("test-plugin", _test_blueprint())
    assert result.success
    assert result.summary == "OK"
