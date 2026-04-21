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


import pytest
from pydantic import ValidationError

from clean_agents.crafters.base import ArtifactSpec


def test_artifact_ref_full_roundtrip():
    """Serialize + deserialize must produce an equal object."""
    ref = ArtifactRef(
        artifact_type=ArtifactType.SKILL,
        name="legal-risk-patterns",
        rationale="risk_evaluator uses domain-specific jargon",
        spec_path=Path(".clean-agents/skills/legal-risk-patterns/.skill-spec.yaml"),
        status="needed",
        priority="recommended",
    )
    dumped = ref.model_dump(mode="json")
    restored = ArtifactRef.model_validate(dumped)
    assert restored == ref


def test_artifact_spec_instantiates():
    """Base ArtifactSpec must be instantiable with minimum required fields."""
    spec = ArtifactSpec(
        name="example-spec",
        description="Example description for base spec test.",
        artifact_type=ArtifactType.SKILL,
    )
    assert spec.name == "example-spec"
    assert spec.version == "0.1.0"
    assert spec.language == "en"
    assert spec.license == "MIT"
    assert spec.source == "human"


@pytest.mark.parametrize(
    "bad_name",
    [
        "-leading",     # leading hyphen
        "trailing-",    # trailing hyphen
        "double--hyphen",  # consecutive hyphens
        "UPPER",        # uppercase
        "has_underscore",  # underscore
        "has space",    # space
        "",             # empty
    ],
)
def test_artifact_spec_rejects_bad_kebab(bad_name):
    with pytest.raises(ValidationError):
        ArtifactSpec(
            name=bad_name,
            description="desc",
            artifact_type=ArtifactType.SKILL,
        )


def test_artifact_spec_accepts_valid_kebab():
    """Valid kebab-case strings pass."""
    for good in ["a", "abc", "a1", "foo-bar", "foo-bar-baz", "v1-alpha2"]:
        ArtifactSpec(name=good, description="desc", artifact_type=ArtifactType.SKILL)


@pytest.mark.parametrize("bad_lang", ["eng", "e", "EN1", "e1", "zz1", "12"])
def test_artifact_spec_rejects_bad_language(bad_lang):
    with pytest.raises(ValidationError):
        ArtifactSpec(
            name="ok",
            description="desc",
            artifact_type=ArtifactType.SKILL,
            language=bad_lang,
        )


from clean_agents.crafters.validators.base import (
    Level,
    Severity,
    ValidationContext,
    ValidationFinding,
    ValidationReport,
)


def test_validation_report_aggregation():
    findings = [
        ValidationFinding(rule_id="R1", severity=Severity.CRITICAL, message="x"),
        ValidationFinding(rule_id="R2", severity=Severity.HIGH, message="y"),
        ValidationFinding(rule_id="R3", severity=Severity.LOW, message="z"),
    ]
    report = ValidationReport(findings=findings)
    assert report.has_critical() is True
    assert report.has_blocking() is True  # critical OR high
    assert len(report.by_severity(Severity.LOW)) == 1


def test_severity_ordering():
    assert Severity.CRITICAL.rank() > Severity.HIGH.rank() > Severity.MEDIUM.rank()
    assert Severity.MEDIUM.rank() > Severity.LOW.rank() > Severity.INFO.rank()


def test_validation_context_defaults():
    ctx = ValidationContext(bundle_root=None, installed_roots=[])
    assert ctx.bundle_root is None
    assert ctx.installed_roots == []


def test_has_critical_false_when_no_critical():
    report = ValidationReport(findings=[
        ValidationFinding(rule_id="R1", severity=Severity.HIGH, message="high only"),
        ValidationFinding(rule_id="R2", severity=Severity.LOW, message="low only"),
    ])
    assert report.has_critical() is False
    # has_blocking() should still be True because HIGH is blocking
    assert report.has_blocking() is True


def test_by_rule_filters_findings():
    findings = [
        ValidationFinding(rule_id="R1", severity=Severity.CRITICAL, message="x"),
        ValidationFinding(rule_id="R2", severity=Severity.HIGH, message="y"),
        ValidationFinding(rule_id="R1", severity=Severity.LOW, message="z"),
    ]
    report = ValidationReport(findings=findings)
    r1 = report.by_rule("R1")
    assert len(r1) == 2
    assert all(f.rule_id == "R1" for f in r1)
    assert report.by_rule("UNKNOWN") == []


def test_extend_merges_findings_in_place():
    a = ValidationReport(findings=[
        ValidationFinding(rule_id="R1", severity=Severity.HIGH, message="first"),
    ])
    b = ValidationReport(findings=[
        ValidationFinding(rule_id="R2", severity=Severity.LOW, message="second"),
        ValidationFinding(rule_id="R3", severity=Severity.INFO, message="third"),
    ])
    a.extend(b)
    assert len(a.findings) == 3
    # b must not be mutated by extend
    assert len(b.findings) == 2
