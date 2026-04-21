"""Tests for core data models."""

from pathlib import Path
from tempfile import TemporaryDirectory

from clean_agents.core.agent import (
    AgentSpec,
    Guardrails,
    HITLMode,
    Memory,
    MetricTarget,
    ModelConfig,
    ReasoningPattern,
)
from clean_agents.core.blueprint import (
    ArchitecturePattern,
    Blueprint,
    ComplianceConfig,
    InfraConfig,
    SystemType,
)
from clean_agents.core.config import Config


# ── AgentSpec ─────────────────────────────────────────────────────────────────


def test_agent_spec_defaults():
    agent = AgentSpec(name="test", role="Test agent")
    assert agent.agent_type == "specialist"
    assert agent.model.primary == "claude-sonnet-4-6"
    assert agent.reasoning == ReasoningPattern.REACT
    assert agent.hitl == HITLMode.NONE
    assert agent.token_budget == 4096


def test_agent_is_orchestrator():
    agent = AgentSpec(name="orch", role="Route tasks", agent_type="orchestrator")
    assert agent.is_orchestrator()

    specialist = AgentSpec(name="spec", role="Analyze")
    assert not specialist.is_orchestrator()


def test_agent_input_token_estimate():
    orch = AgentSpec(name="o", role="Route", agent_type="orchestrator")
    assert orch.total_input_tokens_estimate() == 3500

    spec = AgentSpec(name="s", role="Work", agent_type="specialist")
    assert spec.total_input_tokens_estimate() == 3000

    classifier = AgentSpec(name="c", role="Classify", agent_type="classifier")
    assert classifier.total_input_tokens_estimate() == 800


# ── Blueprint ─────────────────────────────────────────────────────────────────


def _make_blueprint() -> Blueprint:
    return Blueprint(
        name="test-system",
        description="Test system",
        system_type=SystemType.MULTI_AGENT,
        pattern=ArchitecturePattern.SUPERVISOR_HIERARCHICAL,
        agents=[
            AgentSpec(name="orchestrator", role="Route", agent_type="orchestrator",
                      model=ModelConfig(primary="claude-sonnet-4-6")),
            AgentSpec(name="analyst", role="Analyze data", agent_type="specialist",
                      model=ModelConfig(primary="claude-sonnet-4-6"),
                      memory=Memory(short_term=True, graphrag=True),
                      hitl=HITLMode.PRE_ACTION),
            AgentSpec(name="guardian", role="Filter", agent_type="guardian",
                      model=ModelConfig(primary="claude-haiku-4-5")),
        ],
        compliance=ComplianceConfig(regulations=["gdpr", "sox"], audit_trail=True),
        infrastructure=InfraConfig(vector_db="pinecone", observability="langfuse"),
    )


def test_blueprint_agent_names():
    bp = _make_blueprint()
    assert bp.agent_names() == ["orchestrator", "analyst", "guardian"]


def test_blueprint_get_orchestrator():
    bp = _make_blueprint()
    orch = bp.get_orchestrator()
    assert orch is not None
    assert orch.name == "orchestrator"


def test_blueprint_has_graphrag():
    bp = _make_blueprint()
    assert bp.has_graphrag()


def test_blueprint_has_hitl():
    bp = _make_blueprint()
    assert bp.has_hitl()


def test_blueprint_cost_estimation():
    bp = _make_blueprint()
    cost = bp.estimated_cost_per_request()
    assert cost > 0
    assert isinstance(cost, float)


def test_blueprint_summary():
    bp = _make_blueprint()
    summary = bp.summary()
    assert summary["name"] == "test-system"
    assert summary["agents"] == 3
    assert summary["has_graphrag"] is True
    assert summary["has_hitl"] is True


def test_blueprint_yaml_roundtrip():
    bp = _make_blueprint()
    yaml_str = bp.to_yaml()
    assert "test-system" in yaml_str
    assert "orchestrator" in yaml_str


def test_blueprint_save_load():
    bp = _make_blueprint()
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "blueprint.yaml"
        bp.save(path)
        assert path.exists()

        loaded = Blueprint.load(path)
        assert loaded.name == bp.name
        assert loaded.total_agents() == bp.total_agents()
        assert loaded.agent_names() == bp.agent_names()


# ── Config ────────────────────────────────────────────────────────────────────


def test_config_defaults():
    cfg = Config()
    assert cfg.project_name == "my-agent-system"
    assert cfg.llm.provider == "anthropic"
    assert cfg.llm.model == "claude-opus-4-6"


def test_config_save_load():
    with TemporaryDirectory() as tmpdir:
        cfg = Config(project_name="test-proj", project_dir=tmpdir)
        path = Path(tmpdir) / "config.yaml"
        cfg.save(path)
        assert path.exists()

        loaded = Config.load(path)
        assert loaded.project_name == "test-proj"
