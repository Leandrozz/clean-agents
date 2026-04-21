# tests/test_crafters_runtime.py
from unittest.mock import MagicMock

from clean_agents.crafters.skill.spec import EvalCase, EvalsManifest, SkillSpec
from clean_agents.crafters.skill.validators import SkillL4ActivationPrecision
from clean_agents.crafters.validators.base import Severity, ValidationContext


def _spec_with_evals(cases_pos: list[str], cases_neg: list[str]) -> SkillSpec:
    return SkillSpec(
        name="eval-skill",
        description="A fixture used to exercise the L4 eval harness with mocked activation.",
        triggers=["eval"],
        references=[],
        body_outline=[],
        evals=EvalsManifest(
            positive_cases=[EvalCase(prompt=p, expected="activate") for p in cases_pos],
            negative_cases=[EvalCase(prompt=p, expected="ignore") for p in cases_neg],
        ),
    )


def test_l4_passes_when_tpr_and_fpr_within_thresholds():
    # activate returns True for positives, False for negatives → perfect
    fake = MagicMock(side_effect=lambda prompt: "positive" in prompt)
    v = SkillL4ActivationPrecision(activate_fn=fake)
    spec = _spec_with_evals(["positive A", "positive B"], ["decoy one", "decoy two"])
    findings = v.check(spec, ValidationContext(enable_ai=True))
    assert findings == []


def test_l4_fires_when_tpr_too_low():
    # Never activates on positives → TPR=0
    fake = MagicMock(return_value=False)
    v = SkillL4ActivationPrecision(activate_fn=fake)
    spec = _spec_with_evals(["p1", "p2"], ["n1", "n2"])
    findings = v.check(spec, ValidationContext(enable_ai=True))
    assert findings
    assert findings[0].severity in (Severity.HIGH, Severity.MEDIUM)
    assert "TPR" in findings[0].message
