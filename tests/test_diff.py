"""Tests for blueprint diff functionality."""

from pathlib import Path
from tempfile import TemporaryDirectory

from clean_agents.cli.diff_cmd import _build_diff_structure
from clean_agents.core.agent import (
    AgentSpec,
    Guardrails,
    HITLMode,
    Memory,
    ModelConfig,
    ReasoningPattern,
)
from clean_agents.core.blueprint import (
    ArchitecturePattern,
    Blueprint,
    ComplianceConfig,
    SystemType,
)


def _make_base_blueprint() -> Blueprint:
    """Create a base blueprint for testing."""
    return Blueprint(
        name="test-system",
        description="Test system",
        system_type=SystemType.MULTI_AGENT,
        pattern=ArchitecturePattern.SUPERVISOR_HIERARCHICAL,
        framework="langgraph",
        domain="general",
        scale="medium",
        agents=[
            AgentSpec(
                name="orchestrator",
                role="Route tasks",
                agent_type="orchestrator",
                model=ModelConfig(primary="claude-sonnet-4-6"),
                token_budget=4096,
            ),
            AgentSpec(
                name="analyst",
                role="Analyze data",
                agent_type="specialist",
                model=ModelConfig(primary="claude-sonnet-4-6"),
                token_budget=2048,
                reasoning=ReasoningPattern.REACT,
                hitl=HITLMode.NONE,
            ),
        ],
    )


# ── Test Identical Blueprints ─────────────────────────────────────────────────


def test_diff_identical_blueprints():
    """Test that identical blueprints show no changes."""
    bp1 = _make_base_blueprint()
    bp2 = _make_base_blueprint()

    diff = _build_diff_structure(bp1, bp2)

    assert diff["metadata_changes"] == []
    assert diff["agents_added"] == []
    assert diff["agents_removed"] == []
    assert diff["agents_changed"] == []
    assert diff["cost_delta"]["delta"] == 0.0


# ── Test Agent Added ──────────────────────────────────────────────────────────


def test_diff_agent_added():
    """Test that added agents are detected."""
    bp1 = _make_base_blueprint()
    bp2 = _make_base_blueprint()

    # Add new agent to bp2
    bp2.agents.append(
        AgentSpec(
            name="classifier",
            role="Classify input",
            agent_type="classifier",
            model=ModelConfig(primary="claude-haiku-4-5"),
            token_budget=1024,
        )
    )

    diff = _build_diff_structure(bp1, bp2)

    assert len(diff["agents_added"]) == 1
    assert diff["agents_added"][0]["name"] == "classifier"
    assert diff["agents_added"][0]["agent_type"] == "classifier"
    assert diff["agents_added"][0]["model"] == "claude-haiku-4-5"
    assert diff["agents_added"][0]["token_budget"] == 1024

    assert diff["agents_removed"] == []
    assert diff["agents_changed"] == []


# ── Test Agent Removed ────────────────────────────────────────────────────────


def test_diff_agent_removed():
    """Test that removed agents are detected."""
    bp1 = _make_base_blueprint()
    bp2 = _make_base_blueprint()

    # Remove analyst from bp2
    bp2.agents = [a for a in bp2.agents if a.name != "analyst"]

    diff = _build_diff_structure(bp1, bp2)

    assert len(diff["agents_removed"]) == 1
    assert diff["agents_removed"][0]["name"] == "analyst"
    assert diff["agents_removed"][0]["agent_type"] == "specialist"
    assert diff["agents_removed"][0]["model"] == "claude-sonnet-4-6"
    assert diff["agents_removed"][0]["token_budget"] == 2048

    assert diff["agents_added"] == []
    assert diff["agents_changed"] == []


# ── Test Agent Model Changed ──────────────────────────────────────────────────


def test_diff_agent_model_changed():
    """Test that changed agent models are detected."""
    bp1 = _make_base_blueprint()
    bp2 = _make_base_blueprint()

    # Change model for analyst
    analyst = bp2.get_agent("analyst")
    assert analyst is not None
    analyst.model.primary = "claude-opus-4-6"

    diff = _build_diff_structure(bp1, bp2)

    assert len(diff["agents_changed"]) == 1
    assert diff["agents_changed"][0]["name"] == "analyst"

    changes = diff["agents_changed"][0]["changes"]
    model_change = next((c for c in changes if c["field"] == "model.primary"), None)
    assert model_change is not None
    assert model_change["old"] == "claude-sonnet-4-6"
    assert model_change["new"] == "claude-opus-4-6"


# ── Test Agent Token Budget Changed ───────────────────────────────────────────


def test_diff_agent_token_budget_changed():
    """Test that changed token budgets are detected."""
    bp1 = _make_base_blueprint()
    bp2 = _make_base_blueprint()

    # Change token budget for analyst
    analyst = bp2.get_agent("analyst")
    assert analyst is not None
    analyst.token_budget = 4096

    diff = _build_diff_structure(bp1, bp2)

    assert len(diff["agents_changed"]) == 1
    assert diff["agents_changed"][0]["name"] == "analyst"

    changes = diff["agents_changed"][0]["changes"]
    token_change = next((c for c in changes if c["field"] == "token_budget"), None)
    assert token_change is not None
    assert token_change["old"] == 2048
    assert token_change["new"] == 4096


# ── Test Agent HITL Changed ───────────────────────────────────────────────────


def test_diff_agent_hitl_changed():
    """Test that changed HITL settings are detected."""
    bp1 = _make_base_blueprint()
    bp2 = _make_base_blueprint()

    # Change HITL for analyst
    analyst = bp2.get_agent("analyst")
    assert analyst is not None
    analyst.hitl = HITLMode.PRE_ACTION

    diff = _build_diff_structure(bp1, bp2)

    assert len(diff["agents_changed"]) == 1
    assert diff["agents_changed"][0]["name"] == "analyst"

    changes = diff["agents_changed"][0]["changes"]
    hitl_change = next((c for c in changes if c["field"] == "hitl"), None)
    assert hitl_change is not None
    assert hitl_change["old"] == "none"
    assert hitl_change["new"] == "pre-action"


# ── Test Guardrails Changed ───────────────────────────────────────────────────


def test_diff_agent_guardrails_changed():
    """Test that changed guardrails are detected."""
    bp1 = _make_base_blueprint()
    bp2 = _make_base_blueprint()

    # Add guardrails to analyst
    analyst = bp2.get_agent("analyst")
    assert analyst is not None
    analyst.guardrails = Guardrails(
        input=["injection_detection", "pii_detection"],
        output=["schema_validation"],
    )

    diff = _build_diff_structure(bp1, bp2)

    assert len(diff["agents_changed"]) == 1
    assert diff["agents_changed"][0]["name"] == "analyst"

    changes = diff["agents_changed"][0]["changes"]
    gr_change = next((c for c in changes if c["field"] == "guardrails"), None)
    assert gr_change is not None
    assert gr_change["old"] == 0
    assert gr_change["new"] == 3


# ── Test Framework Changed ────────────────────────────────────────────────────


def test_diff_framework_changed():
    """Test that changed framework is detected."""
    bp1 = _make_base_blueprint()
    bp2 = _make_base_blueprint()

    bp2.framework = "autogen"

    diff = _build_diff_structure(bp1, bp2)

    assert len(diff["metadata_changes"]) == 1
    assert diff["metadata_changes"][0]["field"] == "framework"
    assert diff["metadata_changes"][0]["old"] == "langgraph"
    assert diff["metadata_changes"][0]["new"] == "autogen"


# ── Test Domain Changed ───────────────────────────────────────────────────────


def test_diff_domain_changed():
    """Test that changed domain is detected."""
    bp1 = _make_base_blueprint()
    bp2 = _make_base_blueprint()

    bp2.domain = "medical"

    diff = _build_diff_structure(bp1, bp2)

    metadata_changes = [c for c in diff["metadata_changes"] if c["field"] == "domain"]
    assert len(metadata_changes) == 1
    assert metadata_changes[0]["old"] == "general"
    assert metadata_changes[0]["new"] == "medical"


# ── Test Cost Delta ───────────────────────────────────────────────────────────


def test_diff_cost_delta():
    """Test that cost delta is calculated correctly."""
    bp1 = _make_base_blueprint()
    bp2 = _make_base_blueprint()

    # Make analyst more expensive
    analyst = bp2.get_agent("analyst")
    assert analyst is not None
    analyst.model.primary = "claude-opus-4-6"

    diff = _build_diff_structure(bp1, bp2)

    assert "cost_delta" in diff
    assert diff["cost_delta"]["old"] > 0
    assert diff["cost_delta"]["new"] > diff["cost_delta"]["old"]
    assert diff["cost_delta"]["delta"] > 0
    assert diff["cost_delta"]["percent"] > 0


# ── Test Cost Delta Zero ──────────────────────────────────────────────────────


def test_diff_cost_delta_zero():
    """Test that cost delta is zero for identical blueprints."""
    bp1 = _make_base_blueprint()
    bp2 = _make_base_blueprint()

    diff = _build_diff_structure(bp1, bp2)

    assert diff["cost_delta"]["delta"] == 0.0
    assert diff["cost_delta"]["percent"] == 0.0


# ── Test Multiple Changes ─────────────────────────────────────────────────────


def test_diff_multiple_changes():
    """Test that multiple changes are detected together."""
    bp1 = _make_base_blueprint()
    bp2 = _make_base_blueprint()

    # Remove analyst
    bp2.agents = [a for a in bp2.agents if a.name != "analyst"]

    # Add new agent
    bp2.agents.append(
        AgentSpec(
            name="classifier",
            role="Classify",
            agent_type="classifier",
            model=ModelConfig(primary="claude-haiku-4-5"),
        )
    )

    # Change orchestrator model
    orch = bp2.get_agent("orchestrator")
    assert orch is not None
    orch.model.primary = "claude-opus-4-6"

    # Change framework
    bp2.framework = "crewai"

    diff = _build_diff_structure(bp1, bp2)

    assert len(diff["agents_removed"]) == 1
    assert len(diff["agents_added"]) == 1
    assert len(diff["agents_changed"]) == 1
    assert len(diff["metadata_changes"]) == 1


# ── Test Diff with Save/Load ─────────────────────────────────────────────────


def test_diff_blueprint_files():
    """Test diff with actual blueprint files."""
    bp1 = _make_base_blueprint()
    bp2 = _make_base_blueprint()

    # Modify bp2
    analyst = bp2.get_agent("analyst")
    assert analyst is not None
    analyst.token_budget = 8192

    with TemporaryDirectory() as tmpdir:
        path1 = Path(tmpdir) / "blueprint1.yaml"
        path2 = Path(tmpdir) / "blueprint2.yaml"

        bp1.save(path1)
        bp2.save(path2)

        loaded_bp1 = Blueprint.load(path1)
        loaded_bp2 = Blueprint.load(path2)

        diff = _build_diff_structure(loaded_bp1, loaded_bp2)

        assert len(diff["agents_changed"]) == 1
        assert diff["agents_changed"][0]["name"] == "analyst"
