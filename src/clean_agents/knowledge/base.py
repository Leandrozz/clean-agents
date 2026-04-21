"""Embedded knowledge base — structured data from skill reference files.

This module contains the distilled knowledge from the CLean-agents skill
research, organized for programmatic access by the recommendation engine
and on-demand modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ModelBenchmark:
    """Benchmark data for a specific model."""
    name: str
    provider: str
    gpqa: float          # Graduate-level reasoning (%)
    swe_bench: float     # Software engineering (%)
    bfcl: float          # Tool use / function calling (%)
    input_price: float   # USD per 1M input tokens
    output_price: float  # USD per 1M output tokens
    context_window: int  # Max context tokens
    max_output: int      # Max output tokens
    supports_vision: bool = True
    supports_tools: bool = True


@dataclass
class FrameworkProfile:
    """Framework capabilities and trade-offs."""
    name: str
    strengths: list[str]
    weaknesses: list[str]
    best_for: list[str]
    multi_agent: bool = True
    state_management: bool = False
    built_in_hitl: bool = False
    streaming: bool = True
    persistence: bool = False


@dataclass
class ComplianceRequirement:
    """A specific compliance requirement with mapping to system components."""
    regulation: str
    article: str
    requirement: str
    components: list[str]  # Blueprint components that address this
    evidence_needed: str


@dataclass
class AttackVector:
    """Security attack vector with detection and mitigation."""
    id: str
    name: str
    description: str
    detection_methods: list[str]
    mitigations: list[str]
    affected_components: list[str]


# ── Model Benchmarks (as of May 2025) ────────────────────────────────────────

MODEL_BENCHMARKS: dict[str, ModelBenchmark] = {
    "claude-opus-4-6": ModelBenchmark(
        name="Claude Opus 4.6", provider="anthropic",
        gpqa=72.5, swe_bench=72.0, bfcl=88.0,
        input_price=5.0, output_price=25.0,
        context_window=200_000, max_output=32_000,
    ),
    "claude-sonnet-4-6": ModelBenchmark(
        name="Claude Sonnet 4.6", provider="anthropic",
        gpqa=65.0, swe_bench=65.0, bfcl=90.5,
        input_price=3.0, output_price=15.0,
        context_window=200_000, max_output=16_000,
    ),
    "claude-haiku-4-5": ModelBenchmark(
        name="Claude Haiku 4.5", provider="anthropic",
        gpqa=41.0, swe_bench=41.0, bfcl=80.2,
        input_price=1.0, output_price=5.0,
        context_window=200_000, max_output=8_192,
    ),
    "gpt-4o": ModelBenchmark(
        name="GPT-4o", provider="openai",
        gpqa=53.6, swe_bench=33.2, bfcl=87.0,
        input_price=2.5, output_price=10.0,
        context_window=128_000, max_output=16_384,
    ),
    "gpt-4o-mini": ModelBenchmark(
        name="GPT-4o Mini", provider="openai",
        gpqa=40.2, swe_bench=24.0, bfcl=82.0,
        input_price=0.15, output_price=0.60,
        context_window=128_000, max_output=16_384,
    ),
    "gemini-2.5-pro": ModelBenchmark(
        name="Gemini 2.5 Pro", provider="google",
        gpqa=59.0, swe_bench=63.8, bfcl=75.0,
        input_price=4.0, output_price=20.0,
        context_window=1_000_000, max_output=65_536,
    ),
    "gemini-2.5-flash": ModelBenchmark(
        name="Gemini 2.5 Flash", provider="google",
        gpqa=42.0, swe_bench=33.0, bfcl=70.0,
        input_price=0.30, output_price=2.50,
        context_window=1_000_000, max_output=65_536,
    ),
}

# ── Framework Profiles ────────────────────────────────────────────────────────

FRAMEWORK_PROFILES: dict[str, FrameworkProfile] = {
    "langgraph": FrameworkProfile(
        name="LangGraph",
        strengths=["State machine graphs", "Persistence", "Human-in-loop", "Streaming"],
        weaknesses=["Learning curve", "LangChain dependency", "Verbose for simple cases"],
        best_for=["Multi-agent systems", "Stateful workflows", "Production systems"],
        multi_agent=True, state_management=True, built_in_hitl=True,
        streaming=True, persistence=True,
    ),
    "crewai": FrameworkProfile(
        name="CrewAI",
        strengths=["Simple API", "Role-based agents", "Sequential/hierarchical"],
        weaknesses=["Limited state management", "Less flexible routing"],
        best_for=["Pipeline workflows", "Role-based teams", "Quick prototypes"],
        multi_agent=True, state_management=False, built_in_hitl=True,
    ),
    "claude-agent-sdk": FrameworkProfile(
        name="Claude Agent SDK",
        strengths=["Native tool use", "Extended thinking", "Simple", "Best Anthropic integration"],
        weaknesses=["Single-provider", "No built-in multi-agent", "Newer ecosystem"],
        best_for=["Claude-first systems", "Simple agents", "Sensitive data"],
        multi_agent=False, state_management=False, built_in_hitl=False,
    ),
    "openai-agents-sdk": FrameworkProfile(
        name="OpenAI Agents SDK",
        strengths=["Handoff protocol", "Guardrails built-in", "Simple"],
        weaknesses=["OpenAI-centric", "Limited persistence"],
        best_for=["OpenAI-first systems", "Simple multi-agent", "Quick start"],
        multi_agent=True, state_management=False, built_in_hitl=False,
    ),
    "custom-ontology": FrameworkProfile(
        name="Custom Framework",
        strengths=["Full control", "No vendor lock-in", "Optimized for domain"],
        weaknesses=["Build from scratch", "Maintenance burden", "Longer timeline"],
        best_for=["Enterprise", "Highly regulated", "Custom requirements"],
        multi_agent=True, state_management=True, built_in_hitl=True,
        persistence=True,
    ),
}

# ── Compliance Requirements ───────────────────────────────────────────────────

COMPLIANCE_REQUIREMENTS: list[ComplianceRequirement] = [
    # GDPR
    ComplianceRequirement("GDPR", "Art. 13-14", "Transparency of processing",
        ["guardrails.output.explainability", "logging.request_tracking"], "Transparency notice, processing records"),
    ComplianceRequirement("GDPR", "Art. 15", "Right of access",
        ["audit_trail", "data_export_api"], "Access request handler, data inventory"),
    ComplianceRequirement("GDPR", "Art. 17", "Right to erasure",
        ["memory.deletion_endpoint", "data_retention_policy"], "Deletion workflow, confirmation logs"),
    ComplianceRequirement("GDPR", "Art. 25", "Data protection by design",
        ["guardrails.input.pii_detection", "guardrails.output.pii_masking"], "Privacy impact assessment"),
    ComplianceRequirement("GDPR", "Art. 35", "DPIA",
        ["blueprint.decisions", "risk_assessment"], "DPIA document, risk register"),
    # HIPAA
    ComplianceRequirement("HIPAA", "§164.312(a)", "Access control",
        ["agent_auth", "tool_permissions", "rbac"], "Access control matrix"),
    ComplianceRequirement("HIPAA", "§164.312(e)", "Transmission security",
        ["tls_encryption", "encrypted_queue"], "Encryption audit, cert management"),
    ComplianceRequirement("HIPAA", "§164.530(j)", "Audit trail",
        ["audit_trail", "immutable_logging"], "6-year retention logs"),
    # EU AI Act
    ComplianceRequirement("EU-AI-ACT", "Art. 6", "Risk classification",
        ["blueprint.domain", "blueprint.scale"], "Risk classification document"),
    ComplianceRequirement("EU-AI-ACT", "Art. 11", "Technical documentation",
        ["blueprint.to_yaml()", "design_decisions"], "System documentation package"),
    ComplianceRequirement("EU-AI-ACT", "Art. 13", "Transparency",
        ["hitl_mode", "explainable_outputs"], "User notification mechanism"),
    ComplianceRequirement("EU-AI-ACT", "Art. 50", "AI-generated content",
        ["output_watermarking"], "Watermarking implementation"),
    # SOX
    ComplianceRequirement("SOX", "§302", "Management certification",
        ["hitl.pre_action", "approval_workflows"], "Approval audit trail"),
    ComplianceRequirement("SOX", "§404", "Internal controls",
        ["guardrails", "audit_trail"], "Control testing evidence"),
    ComplianceRequirement("SOX", "§802", "Record retention",
        ["immutable_logging"], "7-year retention policy"),
    # SOC 2
    ComplianceRequirement("SOC2", "CC6.1", "Logical access",
        ["agent_auth", "rbac", "tool_permissions"], "Access control matrix"),
    ComplianceRequirement("SOC2", "CC7.2", "System monitoring",
        ["observability", "alerting"], "Monitoring dashboard, alert config"),
    ComplianceRequirement("SOC2", "CC8.1", "Change management",
        ["blueprint.versioning", "changelog"], "Change log, approval records"),
]

# ── Attack Vectors ────────────────────────────────────────────────────────────

ATTACK_VECTORS: list[AttackVector] = [
    AttackVector(
        "ATK-1", "Prompt Injection",
        "Direct or indirect manipulation of system prompts to alter agent behavior",
        ["input pattern matching", "system/user prompt separation", "canary tokens"],
        ["instruction hierarchy", "input sanitization", "output monitoring"],
        ["all agents with user-facing input"],
    ),
    AttackVector(
        "ATK-2", "Jailbreaking",
        "Techniques to bypass safety constraints and policy guardrails",
        ["output content analysis", "behavioral monitoring", "multi-turn tracking"],
        ["role boundary enforcement", "output filtering", "conversation limits"],
        ["all agents"],
    ),
    AttackVector(
        "ATK-3", "Data Extraction",
        "Attempts to extract system prompts, training data, or sensitive context",
        ["output pattern analysis", "prompt reflection detection"],
        ["system prompt protection", "RAG access control", "output filtering"],
        ["agents with RAG/memory", "agents with sensitive system prompts"],
    ),
    AttackVector(
        "ATK-4", "Agent Manipulation",
        "Exploiting trust relationships between agents in multi-agent systems",
        ["inter-agent message validation", "behavioral anomaly detection"],
        ["agent authentication", "message signing", "privilege boundaries"],
        ["orchestrator", "inter-agent communication channels"],
    ),
    AttackVector(
        "ATK-5", "Tool Abuse",
        "Unauthorized tool execution, parameter injection, or privilege escalation",
        ["tool call auditing", "parameter validation"],
        ["tool permission model", "execution sandboxing", "approval for high-risk tools"],
        ["agents with external tools", "code execution agents"],
    ),
    AttackVector(
        "ATK-6", "Denial of Service",
        "Resource exhaustion through recursive calls, expensive operations, or token flooding",
        ["rate monitoring", "token usage tracking", "recursion detection"],
        ["rate limiting", "token budgets", "recursion depth limits", "circuit breakers"],
        ["orchestrator", "agents with loops or recursive patterns"],
    ),
    AttackVector(
        "ATK-7", "Privacy Violation",
        "PII leakage through context bleed, output, or cross-user contamination",
        ["PII scanning on input/output", "context isolation verification"],
        ["PII detection/masking", "context isolation", "session management"],
        ["all agents handling user data"],
    ),
]


# ── Convenience accessors ─────────────────────────────────────────────────────

def get_model(name: str) -> ModelBenchmark | None:
    """Get benchmark data for a model."""
    return MODEL_BENCHMARKS.get(name)


def get_framework(name: str) -> FrameworkProfile | None:
    """Get profile for a framework."""
    return FRAMEWORK_PROFILES.get(name)


def get_compliance_for(regulation: str) -> list[ComplianceRequirement]:
    """Get all requirements for a specific regulation."""
    reg_upper = regulation.upper().replace("-", "_").replace(" ", "_")
    return [r for r in COMPLIANCE_REQUIREMENTS if r.regulation.upper().replace("-", "_") == reg_upper]


def get_attack_vector(attack_id: str) -> AttackVector | None:
    """Get attack vector by ID."""
    return next((a for a in ATTACK_VECTORS if a.id == attack_id), None)


def all_model_names() -> list[str]:
    """List all known model identifiers."""
    return list(MODEL_BENCHMARKS.keys())


def cheapest_model_for(min_gpqa: float = 0, min_bfcl: float = 0) -> str | None:
    """Find the cheapest model meeting minimum benchmark thresholds."""
    candidates = [
        (name, m) for name, m in MODEL_BENCHMARKS.items()
        if m.gpqa >= min_gpqa and m.bfcl >= min_bfcl
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda x: x[1].input_price + x[1].output_price)[0]
