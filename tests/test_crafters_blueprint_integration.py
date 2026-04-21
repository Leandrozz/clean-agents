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


import yaml
from typer.testing import CliRunner

from clean_agents.cli.main import app

runner = CliRunner()


def test_skill_design_for_agent_loads_blueprint(tmp_path: Path):
    bp = {
        "name": "demo",
        "agents": [
            {"name": "risk_evaluator", "role": "legal risk assessor"},
            {"name": "classifier", "role": "intent router"},
        ],
    }
    bp_path = tmp_path / "blueprint.yaml"
    bp_path.write_text(yaml.safe_dump(bp), encoding="utf-8")

    out = tmp_path / "skill-out"
    result = runner.invoke(
        app,
        [
            "skill", "design",
            "--for-agent", "risk_evaluator",
            "--blueprint", str(bp_path),
            "--no-interactive",
            "--output", str(out),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert (out / ".skill-spec.yaml").exists()
    spec_data = yaml.safe_load((out / ".skill-spec.yaml").read_text(encoding="utf-8"))
    assert "risk_evaluator" in spec_data["description"]
