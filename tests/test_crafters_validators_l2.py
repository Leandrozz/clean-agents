from __future__ import annotations

from pathlib import Path

from clean_agents.crafters.skill.spec import ReferenceFile, SkillSection, SkillSpec
from clean_agents.crafters.skill.validators import (
    SkillL2HardcodedDates,
    SkillL2HardcodedStats,
    SkillL2LanguageMix,
    SkillL2ProgressiveDisclosure,
    SkillL2PromisesVsDelivery,
    SkillL2TriggerCoverage,
)
from clean_agents.crafters.validators.base import Severity, ValidationContext


def _spec_with_body(body: str) -> SkillSpec:
    return SkillSpec(
        name="s",
        description="A fixture description longer than fifty chars to pass length check.",
        triggers=["s"],
        references=[],
        body_outline=[SkillSection(heading="Body", body=body)],
    )


def test_hardcoded_stats_percent():
    body = "Accuracy was 82.4% in benchmark."
    findings = SkillL2HardcodedStats().check(_spec_with_body(body), ValidationContext())
    assert any(f.rule_id == "SKILL-L2-HARDCODED-STATS" for f in findings)


def test_hardcoded_stats_cve():
    body = "Mitigates CVE-2025-6514 attacks."
    findings = SkillL2HardcodedStats().check(_spec_with_body(body), ValidationContext())
    assert any("CVE" in f.message for f in findings)


def test_hardcoded_stats_paper_year():
    body = "as shown by paper de 2024 results"
    findings = SkillL2HardcodedStats().check(_spec_with_body(body), ValidationContext())
    assert findings


def test_hardcoded_dates_fires_on_specific_year():
    body = "In 2024, the team shipped v1."
    findings = SkillL2HardcodedDates().check(_spec_with_body(body), ValidationContext())
    assert findings
    assert findings[0].severity is Severity.MEDIUM


def test_language_mix_fires_for_spanish_in_english_skill():
    spec = _spec_with_body("The agent said: 'si puedes porfi, revisá el commit antes de mergear'.")
    findings = SkillL2LanguageMix().check(spec, ValidationContext())
    assert any(f.rule_id == "SKILL-L2-LANGUAGE-MIX" for f in findings)


def test_trigger_coverage_fires_below_80pct():
    spec = SkillSpec(
        name="s",
        description="Designs, validates, renders, publishes and ships full-bundle artifacts.",
        triggers=["unrelated"],
        references=[],
        body_outline=[],
    )
    findings = SkillL2TriggerCoverage().check(spec, ValidationContext())
    assert findings


def test_progressive_disclosure_fires_long_body_no_refs():
    big = "word " * 2500
    spec = SkillSpec(
        name="s",
        description="A fixture description longer than fifty chars to pass length check.",
        triggers=["s"],
        references=[],
        body_outline=[SkillSection(heading="Big", body=big)],
    )
    findings = SkillL2ProgressiveDisclosure().check(spec, ValidationContext())
    assert findings


def test_promises_vs_delivery_fires_for_empty_ref(tmp_path: Path):
    bundle = tmp_path / "s"
    (bundle / "references").mkdir(parents=True)
    (bundle / "references" / "taxonomy.md").write_text("")  # empty
    spec = SkillSpec(
        name="s",
        description="A fixture description longer than fifty chars to pass length check.",
        triggers=["s"],
        references=[ReferenceFile(path=Path("references/taxonomy.md"), topic="t")],
        body_outline=[SkillSection(heading="Overview", body="See references/taxonomy.md")],
    )
    findings = SkillL2PromisesVsDelivery().check(spec, ValidationContext(bundle_root=bundle))
    assert findings
