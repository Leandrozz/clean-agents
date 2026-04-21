from pathlib import Path

from clean_agents.crafters.skill.spec import SkillSpec
from clean_agents.crafters.skill.validators import (
    SkillL3MarketplaceDedupe,
    SkillL3NameCollision,
    SkillL3TriggerOverlap,
)
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


def test_trigger_overlap_fires_above_60pct(tmp_path: Path):
    # installed skill "legal-risk" with triggers we overlap with
    installed = tmp_path / "installed"
    skill_dir = installed / "legal-risk"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: legal-risk\ndescription: legal risk patterns\n---\n"
        "# Triggers\n- legal\n- risk\n- contract\n- liability\n- indemnify\n"
    )
    spec = _spec("my-skill")
    spec.triggers = ["legal", "risk", "contract", "liability"]
    ctx = ValidationContext(installed_roots=[installed])
    findings = SkillL3TriggerOverlap().check(spec, ctx)
    assert findings
    assert findings[0].rule_id == "SKILL-L3-TRIGGER-OVERLAP"


def test_marketplace_dedupe_noop_without_index():
    assert (
        SkillL3MarketplaceDedupe().check(_spec("x"), ValidationContext(marketplace_index={}))
        == []
    )


def test_marketplace_dedupe_fires_when_name_in_index():
    ctx = ValidationContext(
        marketplace_index={"legal-risk-patterns": ["triggers", "mentioned"]},
    )
    findings = SkillL3MarketplaceDedupe().check(_spec("legal-risk-patterns"), ctx)
    assert findings


def test_leandro_real_skill_regression(tmp_path: Path):
    from clean_agents.crafters.base import ArtifactType
    from clean_agents.crafters.skill.spec import SkillSection, SkillSpec
    from clean_agents.crafters.validators.base import get_registry

    # Construct a spec that mirrors the known issues found in the real skill
    spec = SkillSpec(
        name="clean-agents",   # collides on purpose
        description="x" * 850, # over 500 on purpose
        triggers=["agent"],
        references=[],
        body_outline=[
            SkillSection(
                heading="Phase 5",
                body="si puedes porfi, revisá el commit. 82.4% accuracy vs CVE-2025-6514.",
            )
        ],
    )
    reg = get_registry()
    ctx = ValidationContext(installed_roots=[tmp_path])
    rule_ids = set()
    for v in reg.for_artifact(ArtifactType.SKILL):
        for f in v.check(spec, ctx):
            rule_ids.add(f.rule_id)
    # The 5 documented findings (excluding NAME-DIR which needs a real dir)
    assert "SKILL-L1-DESC-LENGTH" in rule_ids
    assert "SKILL-L2-HARDCODED-STATS" in rule_ids
    assert "SKILL-L2-LANGUAGE-MIX" in rule_ids
