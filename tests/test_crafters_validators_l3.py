from pathlib import Path

from clean_agents.crafters.skill.spec import SkillSpec
from clean_agents.crafters.skill.validators import SkillL3NameCollision
from clean_agents.crafters.validators.base import Severity, ValidationContext


def _spec(name: str) -> SkillSpec:
    return SkillSpec(
        name=name,
        description="A fixture description longer than fifty chars to pass length check.",
        triggers=[name],
        references=[], body_outline=[],
    )


def test_name_collision_fires(tmp_path: Path):
    installed = tmp_path / "installed"
    (installed / "clean-agents").mkdir(parents=True)
    ctx = ValidationContext(installed_roots=[installed])
    findings = SkillL3NameCollision().check(_spec("clean-agents"), ctx)
    assert findings
    assert findings[0].rule_id == "SKILL-L3-NAME-COLLISION"
    assert findings[0].severity is Severity.CRITICAL


def test_name_collision_no_match(tmp_path: Path):
    installed = tmp_path / "installed"
    installed.mkdir()
    ctx = ValidationContext(installed_roots=[installed])
    assert SkillL3NameCollision().check(_spec("brand-new-skill"), ctx) == []
