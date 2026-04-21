"""Tests for the recommendation engine."""

from clean_agents.core.blueprint import ArchitecturePattern, SystemType
from clean_agents.engine.recommender import (
    DomainType,
    Recommender,
    classify_system,
    extract_signals,
    select_framework,
    select_pattern,
)


# ── Signal Extraction ─────────────────────────────────────────────────────────


def test_extract_domain_legal():
    signals = extract_signals("Build a contract review system for legal compliance")
    assert signals.domain == DomainType.LEGAL


def test_extract_domain_medical():
    signals = extract_signals("Create a patient diagnosis assistant for the hospital")
    assert signals.domain == DomainType.MEDICAL


def test_extract_domain_financial():
    signals = extract_signals("Build a trading risk assessment platform")
    assert signals.domain == DomainType.FINANCIAL


def test_extract_compliance_gdpr():
    signals = extract_signals("System must handle personal data under GDPR")
    assert signals.needs_compliance
    assert "gdpr" in signals.compliance_types


def test_extract_compliance_hipaa():
    signals = extract_signals("Medical records system compliant with HIPAA")
    assert signals.needs_compliance
    assert "hipaa" in signals.compliance_types


def test_extract_sensitive_data():
    signals = extract_signals("Must handle PII and credit card information securely")
    assert signals.handles_sensitive_data


def test_extract_hitl():
    signals = extract_signals("Requires human approval before executing trades")
    assert signals.needs_hitl


def test_extract_scale_enterprise():
    signals = extract_signals("Enterprise system handling millions of requests")
    assert signals.expected_scale == "enterprise"


def test_extract_scale_small():
    signals = extract_signals("Simple prototype for personal use")
    assert signals.expected_scale == "small"


def test_extract_exploratory():
    signals = extract_signals("Creative brainstorming and research exploration tool")
    assert signals.is_exploratory
    assert not signals.is_deterministic


# ── System Classification ─────────────────────────────────────────────────────


def test_classify_single_agent():
    signals = extract_signals("Summarize documents")
    st = classify_system(signals)
    assert st == SystemType.SINGLE_AGENT


def test_classify_multi_agent():
    signals = extract_signals("Analyze, classify, generate, and evaluate customer tickets")
    st = classify_system(signals)
    assert st in (SystemType.MULTI_AGENT, SystemType.COMPLEX_SYSTEM)


# ── Pattern Selection ─────────────────────────────────────────────────────────


def test_pattern_single():
    signals = extract_signals("Simple chatbot")
    st = classify_system(signals)
    pattern = select_pattern(signals, st)
    assert pattern == ArchitecturePattern.SINGLE


def test_pattern_exploratory_swarm():
    signals = extract_signals("Creative research exploration tool for brainstorming")
    signals.num_responsibilities = 4
    st = SystemType.MULTI_AGENT
    pattern = select_pattern(signals, st)
    assert pattern == ArchitecturePattern.BLACKBOARD_SWARM


def test_pattern_compliance_hierarchical():
    signals = extract_signals("GDPR compliant document analysis with audit trail")
    signals.num_responsibilities = 4
    st = SystemType.MULTI_AGENT
    pattern = select_pattern(signals, st)
    assert pattern == ArchitecturePattern.SUPERVISOR_HIERARCHICAL


# ── Framework Selection ───────────────────────────────────────────────────────


def test_framework_single_sensitive():
    signals = extract_signals("Handle PII data securely")
    pattern = ArchitecturePattern.SINGLE
    fw = select_framework(signals, pattern)
    assert fw == "claude-agent-sdk"


def test_framework_pipeline():
    pattern = ArchitecturePattern.PIPELINE
    signals = extract_signals("Process documents sequentially")
    fw = select_framework(signals, pattern)
    assert fw == "crewai"


def test_framework_hierarchical():
    pattern = ArchitecturePattern.SUPERVISOR_HIERARCHICAL
    signals = extract_signals("Multi-agent customer support")
    fw = select_framework(signals, pattern)
    assert fw == "langgraph"


# ── Full Recommendation ──────────────────────────────────────────────────────


def test_full_recommendation_legal():
    r = Recommender()
    bp = r.recommend("Build a contract review system with clause extraction and risk scoring for legal compliance under GDPR")
    assert bp.domain == "legal"
    assert bp.name
    assert len(bp.agents) >= 2
    assert bp.compliance.regulations
    assert any(a.name == "doc_analyzer" for a in bp.agents)


def test_full_recommendation_simple():
    r = Recommender()
    bp = r.recommend("A simple chatbot for answering FAQ questions")
    assert bp.system_type == SystemType.SINGLE_AGENT
    assert bp.pattern == ArchitecturePattern.SINGLE
    assert len(bp.agents) == 1


def test_full_recommendation_enterprise():
    r = Recommender()
    bp = r.recommend(
        "Enterprise customer support system that classifies, routes, resolves, "
        "monitors, evaluates, and generates reports for millions of tickets with SOX compliance"
    )
    assert bp.system_type in (SystemType.MULTI_AGENT, SystemType.COMPLEX_SYSTEM)
    assert len(bp.agents) >= 3
    assert bp.compliance.audit_trail
