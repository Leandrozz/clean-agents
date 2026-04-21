"""Tests for the embedded knowledge base."""

from clean_agents.knowledge.base import (
    MODEL_BENCHMARKS,
    FRAMEWORK_PROFILES,
    COMPLIANCE_REQUIREMENTS,
    ATTACK_VECTORS,
    get_model,
    get_framework,
    get_compliance_for,
    get_attack_vector,
    all_model_names,
    cheapest_model_for,
)


def test_model_benchmarks_populated():
    assert len(MODEL_BENCHMARKS) >= 7
    assert "claude-opus-4-6" in MODEL_BENCHMARKS
    assert "claude-sonnet-4-6" in MODEL_BENCHMARKS
    assert "gpt-4o" in MODEL_BENCHMARKS


def test_get_model():
    m = get_model("claude-sonnet-4-6")
    assert m is not None
    assert m.provider == "anthropic"
    assert m.gpqa > 0
    assert m.input_price > 0


def test_get_model_missing():
    assert get_model("nonexistent-model") is None


def test_framework_profiles():
    assert len(FRAMEWORK_PROFILES) >= 4
    lg = get_framework("langgraph")
    assert lg is not None
    assert lg.state_management is True
    assert lg.multi_agent is True


def test_compliance_gdpr():
    reqs = get_compliance_for("GDPR")
    assert len(reqs) >= 4
    articles = [r.article for r in reqs]
    assert "Art. 25" in articles


def test_compliance_hipaa():
    reqs = get_compliance_for("HIPAA")
    assert len(reqs) >= 3


def test_compliance_eu_ai_act():
    reqs = get_compliance_for("EU-AI-ACT")
    assert len(reqs) >= 3


def test_attack_vectors():
    assert len(ATTACK_VECTORS) == 7
    atk1 = get_attack_vector("ATK-1")
    assert atk1 is not None
    assert atk1.name == "Prompt Injection"
    assert len(atk1.mitigations) > 0


def test_all_model_names():
    names = all_model_names()
    assert len(names) >= 7
    assert "claude-sonnet-4-6" in names


def test_cheapest_model_basic():
    # Should return the cheapest model with no constraints
    cheapest = cheapest_model_for(min_gpqa=0, min_bfcl=0)
    assert cheapest is not None
    # gpt-4o-mini should be cheapest overall
    assert cheapest == "gpt-4o-mini"


def test_cheapest_model_high_quality():
    # With high GPQA requirement, should filter to premium models
    cheapest = cheapest_model_for(min_gpqa=60, min_bfcl=85)
    assert cheapest is not None
    # Only claude-opus and claude-sonnet meet both thresholds
    assert "claude" in cheapest
