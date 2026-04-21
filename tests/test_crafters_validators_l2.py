from __future__ import annotations

from clean_agents.crafters.skill.spec import SkillSection, SkillSpec
from clean_agents.crafters.skill.validators import (
    SkillL2HardcodedDates,
    SkillL2HardcodedStats,
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
