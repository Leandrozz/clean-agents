from pathlib import Path

from clean_agents.crafters.base import ArtifactType
from clean_agents.crafters.skill.spec import SkillSpec
from clean_agents.crafters.skill.validators import SkillL1NameDir
from clean_agents.crafters.validators.base import Severity, ValidationContext


def _spec(name: str) -> SkillSpec:
    return SkillSpec(
        name=name,
        description="Fixture description longer than fifty chars to pass L1-DESC-LENGTH.",
        triggers=[name],
        references=[],
        body_outline=[],
    )


def test_name_dir_match_passes(tmp_path: Path):
    bundle = tmp_path / "my-skill"
    bundle.mkdir()
    ctx = ValidationContext(bundle_root=bundle)
    result = SkillL1NameDir().check(_spec("my-skill"), ctx)
    assert result == []


def test_name_dir_mismatch_fires(tmp_path: Path):
    bundle = tmp_path / "other-name"
    bundle.mkdir()
    ctx = ValidationContext(bundle_root=bundle)
    findings = SkillL1NameDir().check(_spec("my-skill"), ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "SKILL-L1-NAME-DIR"
    assert findings[0].severity is Severity.HIGH
