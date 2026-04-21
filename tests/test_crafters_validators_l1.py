from pathlib import Path

from clean_agents.crafters.base import ArtifactType
from clean_agents.crafters.skill.spec import ReferenceFile, SkillSpec
from clean_agents.crafters.skill.validators import (
    SkillL1DescLength,
    SkillL1NameDir,
    SkillL1RefsExist,
    SkillL1RefsOrphan,
)
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


def test_name_dir_skips_when_no_bundle_root():
    ctx = ValidationContext()
    result = SkillL1NameDir().check(_spec("my-skill"), ctx)
    assert result == []


def test_desc_length_short_fires():
    spec = SkillSpec(
        name="x", description="too short",
        triggers=["x"], references=[], body_outline=[],
    )
    findings = SkillL1DescLength().check(spec, ValidationContext())
    assert len(findings) == 1
    assert findings[0].severity is Severity.CRITICAL


def test_desc_length_long_fires():
    spec = SkillSpec(
        name="x", description="a" * 501,
        triggers=["x"], references=[], body_outline=[],
    )
    findings = SkillL1DescLength().check(spec, ValidationContext())
    assert len(findings) == 1
    assert findings[0].rule_id == "SKILL-L1-DESC-LENGTH"


def test_refs_exist_fires_for_missing_file(tmp_path: Path):
    bundle = tmp_path / "s"
    bundle.mkdir()
    spec = SkillSpec(
        name="s",
        description="A fixture description longer than fifty chars to pass length check.",
        triggers=["s"],
        references=[ReferenceFile(path=Path("references/missing.md"), topic="", outline=[])],
        body_outline=[],
    )
    findings = SkillL1RefsExist().check(spec, ValidationContext(bundle_root=bundle))
    assert len(findings) == 1
    assert findings[0].rule_id == "SKILL-L1-REFS-EXIST"


def test_refs_orphan_fires_for_unmentioned_file(tmp_path: Path):
    bundle = tmp_path / "s"
    (bundle / "references").mkdir(parents=True)
    (bundle / "references" / "orphan.md").write_text("# orphan\n")
    spec = SkillSpec(
        name="s",
        description="A fixture description longer than fifty chars to pass length check.",
        triggers=["s"], references=[], body_outline=[],
    )
    findings = SkillL1RefsOrphan().check(spec, ValidationContext(bundle_root=bundle))
    assert any(f.rule_id == "SKILL-L1-REFS-ORPHAN" for f in findings)
