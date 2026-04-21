from pathlib import Path

from clean_agents.core.agent import AgentSpec
from clean_agents.crafters.base import ArtifactRef, ArtifactType


def test_agent_spec_has_recommended_artifacts_default_empty():
    a = AgentSpec(name="a", role="classifier")
    assert a.recommended_artifacts == []


def test_agent_spec_accepts_artifact_refs():
    ref = ArtifactRef(
        artifact_type=ArtifactType.SKILL,
        name="legal-patterns",
        rationale="agent works with legal jargon",
        spec_path=Path(".clean-agents/skills/legal-patterns/.skill-spec.yaml"),
        status="needed",
    )
    a = AgentSpec(
        name="risk_evaluator",
        role="legal risk assessor",
        recommended_artifacts=[ref],
    )
    assert a.recommended_artifacts[0].name == "legal-patterns"
    assert a.recommended_artifacts[0].artifact_type is ArtifactType.SKILL


def test_existing_blueprint_yaml_still_loads():
    """Regression: Blueprints from v0.1 without recommended_artifacts must still load."""
    from clean_agents.core.blueprint import Blueprint

    data = {
        "name": "legacy",
        "agents": [{"name": "a", "role": "classifier"}],
    }
    bp = Blueprint.model_validate(data)
    assert bp.agents[0].recommended_artifacts == []
