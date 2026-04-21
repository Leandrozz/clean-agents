def test_crafters_package_importable():
    import clean_agents.crafters
    import clean_agents.crafters.validators
    import clean_agents.crafters.skill
    assert clean_agents.crafters is not None


from pathlib import Path

from clean_agents.crafters.base import ArtifactRef, ArtifactType


def test_artifact_type_values():
    assert ArtifactType.SKILL.value == "skill"
    assert ArtifactType.MCP.value == "mcp"
    assert ArtifactType.TOOL.value == "tool"
    assert ArtifactType.PLUGIN.value == "plugin"


def test_artifact_ref_roundtrip():
    ref = ArtifactRef(
        artifact_type=ArtifactType.SKILL,
        name="legal-risk-patterns",
        rationale="risk_evaluator uses domain-specific jargon",
        spec_path=Path(".clean-agents/skills/legal-risk-patterns/.skill-spec.yaml"),
        status="needed",
        priority="recommended",
    )
    dumped = ref.model_dump(mode="json")
    assert dumped["artifact_type"] == "skill"
    assert dumped["status"] == "needed"
