"""Architecture recommendation engine — the brain of CLean-agents.

Takes a natural language description and produces an opinionated architecture
recommendation backed by evidence from the embedded knowledge base.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from clean_agents.core.agent import (
    AgentSpec,
    Guardrails,
    HITLMode,
    Memory,
    MetricTarget,
    ModelConfig,
    ReasoningPattern,
)
from clean_agents.core.blueprint import (
    ArchitecturePattern,
    Blueprint,
    ComplianceConfig,
    DesignDecision,
    InfraConfig,
    ResearchFinding,
    SystemType,
)


class DomainType(str, Enum):
    LEGAL = "legal"
    MEDICAL = "medical"
    FINANCIAL = "financial"
    SUPPORT = "support"
    CODING = "coding"
    RESEARCH = "research"
    ECOMMERCE = "ecommerce"
    GENERAL = "general"


@dataclass
class IntakeSignals:
    """Signals extracted from the user's natural language description."""

    description: str
    domain: DomainType = DomainType.GENERAL
    num_responsibilities: int = 1
    needs_compliance: bool = False
    needs_audit_trail: bool = False
    needs_hitl: bool = False
    handles_sensitive_data: bool = False
    is_exploratory: bool = False
    is_deterministic: bool = True
    expected_scale: str = "medium"
    has_existing_system: bool = False
    mentioned_frameworks: list[str] | None = None
    mentioned_models: list[str] | None = None

    # Domain-specific signals
    compliance_types: list[str] | None = None
    data_types: list[str] | None = None


# --- Signal Keywords ---

DOMAIN_KEYWORDS: dict[DomainType, list[str]] = {
    DomainType.LEGAL: ["legal", "contract", "clause", "compliance", "regulatory", "law", "attorney", "litigation"],
    DomainType.MEDICAL: ["medical", "health", "patient", "clinical", "diagnosis", "hipaa", "pharma", "hospital"],
    DomainType.FINANCIAL: ["financial", "trading", "portfolio", "banking", "fintech", "payment", "risk", "sox", "audit"],
    DomainType.SUPPORT: ["support", "ticket", "customer", "helpdesk", "chat", "service", "complaint"],
    DomainType.CODING: ["code", "programming", "developer", "debug", "repository", "pull request", "ci/cd"],
    DomainType.RESEARCH: ["research", "paper", "academic", "analysis", "literature", "study"],
    DomainType.ECOMMERCE: ["ecommerce", "product", "cart", "order", "catalog", "recommendation"],
}

COMPLIANCE_KEYWORDS: dict[str, list[str]] = {
    "gdpr": ["gdpr", "data protection", "eu data", "personal data", "right to deletion"],
    "hipaa": ["hipaa", "phi", "protected health", "medical records", "baa"],
    "sox": ["sox", "sarbanes", "financial audit", "internal controls"],
    "eu-ai-act": ["eu ai act", "ai act", "high-risk ai", "annex iii"],
    "soc2": ["soc 2", "soc2", "trust service", "audit"],
    "finra": ["finra", "sec", "securities", "trading compliance"],
    "aba": ["aba", "legal ethics", "attorney", "bar association"],
}

SENSITIVE_DATA_KEYWORDS = [
    "pii", "personal data", "ssn", "credit card", "medical records", "phi",
    "confidential", "classified", "sensitive", "private", "encrypted",
]


def extract_signals(description: str) -> IntakeSignals:
    """Extract architectural signals from a natural language description."""
    desc_lower = description.lower()
    signals = IntakeSignals(description=description)

    # Domain detection
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            signals.domain = domain
            break

    # Compliance detection
    detected_compliance = []
    for reg, keywords in COMPLIANCE_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            detected_compliance.append(reg)
    if detected_compliance:
        signals.needs_compliance = True
        signals.compliance_types = detected_compliance

    # Sensitive data
    if any(kw in desc_lower for kw in SENSITIVE_DATA_KEYWORDS):
        signals.handles_sensitive_data = True

    # HITL signals
    hitl_keywords = ["human", "approval", "review", "sign-off", "manual", "oversight", "aprobación"]
    if any(kw in desc_lower for kw in hitl_keywords):
        signals.needs_hitl = True

    # Audit trail
    audit_keywords = ["audit", "trail", "log", "traceability", "accountability"]
    if any(kw in desc_lower for kw in audit_keywords):
        signals.needs_audit_trail = True

    # Exploratory vs deterministic
    exploratory_keywords = ["creative", "exploratory", "research", "brainstorm", "explore", "discover"]
    if any(kw in desc_lower for kw in exploratory_keywords):
        signals.is_exploratory = True
        signals.is_deterministic = False

    # Count responsibilities (heuristic: count distinct task verbs)
    task_verbs = ["analyze", "extract", "classify", "generate", "evaluate", "monitor",
                  "search", "summarize", "translate", "validate", "route", "review",
                  "analizar", "extraer", "clasificar", "generar", "evaluar", "buscar"]
    count = sum(1 for v in task_verbs if v in desc_lower)
    signals.num_responsibilities = max(1, count)

    # Scale detection
    scale_keywords = {
        "enterprise": ["enterprise", "million", "10k", "100k", "high volume", "production scale"],
        "large": ["large", "thousands", "high throughput", "5k", "1000+"],
        "small": ["simple", "prototype", "mvp", "poc", "small", "personal"],
    }
    for scale, keywords in scale_keywords.items():
        if any(kw in desc_lower for kw in keywords):
            signals.expected_scale = scale
            break

    return signals


def classify_system(signals: IntakeSignals) -> SystemType:
    """Layer 1: Classify system type from signals."""
    if signals.num_responsibilities <= 1:
        return SystemType.SINGLE_AGENT
    if signals.num_responsibilities <= 3 and signals.is_deterministic:
        return SystemType.PIPELINE
    if signals.expected_scale == "enterprise" or signals.num_responsibilities > 5:
        return SystemType.COMPLEX_SYSTEM
    return SystemType.MULTI_AGENT


def select_pattern(signals: IntakeSignals, system_type: SystemType) -> ArchitecturePattern:
    """Layer 2: Select architecture pattern."""
    if system_type == SystemType.SINGLE_AGENT:
        return ArchitecturePattern.SINGLE
    if system_type == SystemType.PIPELINE:
        return ArchitecturePattern.PIPELINE

    # Multi-agent or complex
    if signals.is_exploratory and not signals.needs_compliance:
        return ArchitecturePattern.BLACKBOARD_SWARM
    if system_type == SystemType.COMPLEX_SYSTEM:
        return ArchitecturePattern.HYBRID
    # Default for compliance-heavy, deterministic, auditable
    return ArchitecturePattern.SUPERVISOR_HIERARCHICAL


def select_framework(signals: IntakeSignals, pattern: ArchitecturePattern) -> str:
    """Layer 3: Select recommended framework."""
    if pattern == ArchitecturePattern.SINGLE:
        if signals.handles_sensitive_data or signals.needs_compliance:
            return "claude-agent-sdk"
        return "openai-agents-sdk"

    if pattern == ArchitecturePattern.PIPELINE:
        return "crewai"

    if pattern in (ArchitecturePattern.SUPERVISOR_HIERARCHICAL, ArchitecturePattern.HYBRID):
        if signals.needs_compliance and signals.expected_scale == "enterprise":
            return "custom-ontology"
        return "langgraph"

    if pattern == ArchitecturePattern.BLACKBOARD_SWARM:
        return "langgraph"

    return "langgraph"


def generate_agents(signals: IntakeSignals, pattern: ArchitecturePattern) -> list[AgentSpec]:
    """Generate recommended agent specifications based on signals and pattern."""
    agents: list[AgentSpec] = []

    if pattern == ArchitecturePattern.SINGLE:
        agents.append(AgentSpec(
            name="agent",
            role=f"Handle {signals.domain.value} tasks: {signals.description[:100]}",
            agent_type="specialist",
            model=ModelConfig(primary="claude-sonnet-4-6"),
            reasoning=ReasoningPattern.REACT,
            memory=Memory(short_term=True),
            guardrails=Guardrails(
                input=["injection_detection", "size_limit"],
                output=["schema_validation"],
            ),
            hitl=HITLMode.PRE_ACTION if signals.needs_hitl else HITLMode.NONE,
            token_budget=4096,
        ))
        return agents

    # Multi-agent patterns need an orchestrator
    orchestrator_model = "claude-opus-4-6" if signals.needs_compliance else "claude-sonnet-4-6"
    agents.append(AgentSpec(
        name="orchestrator",
        role="Plan decomposition, task routing, result synthesis",
        agent_type="orchestrator",
        model=ModelConfig(primary=orchestrator_model, fallback="gpt-4o"),
        reasoning=ReasoningPattern.HTN_PLANNING if signals.num_responsibilities > 3 else ReasoningPattern.REACT,
        memory=Memory(short_term=True),
        guardrails=Guardrails(
            input=["injection_detection", "encoding_detection"],
            output=["schema_validation"],
        ),
        hitl=HITLMode.PRE_ACTION if signals.needs_hitl else HITLMode.NONE,
        token_budget=2000,
        metrics=[
            MetricTarget(name="routing_accuracy", target=0.95),
            MetricTarget(name="recovery_rate", target=0.80),
        ],
    ))

    # Generate specialists based on domain
    domain_specialists = _get_domain_specialists(signals)
    agents.extend(domain_specialists)

    # Guardian agent for sensitive/compliance cases
    if signals.handles_sensitive_data or signals.needs_compliance:
        agents.append(AgentSpec(
            name="guardian",
            role="Input/output safety filtering, PII detection, compliance checks",
            agent_type="guardian",
            model=ModelConfig(primary="claude-haiku-4-5"),
            reasoning=ReasoningPattern.REACT,
            memory=Memory(short_term=True),
            guardrails=Guardrails(
                input=["injection_detection", "encoding_detection", "pii_detection"],
                output=["pii_masking", "content_filter"],
            ),
            token_budget=500,
            metrics=[
                MetricTarget(name="detection_rate", target=0.99),
                MetricTarget(name="false_positive_rate", target=0.05, alert_threshold=0.10),
            ],
        ))

    return agents


def _get_domain_specialists(signals: IntakeSignals) -> list[AgentSpec]:
    """Generate domain-specific specialist agents."""
    specialists = []
    domain = signals.domain

    if domain == DomainType.LEGAL:
        specialists.extend([
            AgentSpec(
                name="doc_analyzer",
                role="Extract clauses, obligations, and terms from legal documents",
                agent_type="specialist",
                model=ModelConfig(primary="claude-sonnet-4-6"),
                reasoning=ReasoningPattern.REACT,
                memory=Memory(short_term=True, graphrag=True),
                guardrails=Guardrails(output=["schema_validation", "confidence_threshold"]),
                token_budget=4000,
                metrics=[MetricTarget(name="extraction_accuracy", target=0.92)],
            ),
            AgentSpec(
                name="risk_evaluator",
                role="Score and categorize contractual risks by severity",
                agent_type="specialist",
                model=ModelConfig(primary="claude-sonnet-4-6"),
                reasoning=ReasoningPattern.REFLECTION,
                memory=Memory(short_term=True, graphrag=True),
                guardrails=Guardrails(output=["schema_validation"]),
                hitl=HITLMode.POST_ACTION if signals.needs_hitl else HITLMode.NONE,
                token_budget=3000,
                metrics=[MetricTarget(name="risk_classification_accuracy", target=0.90)],
            ),
        ])
    elif domain == DomainType.MEDICAL:
        specialists.extend([
            AgentSpec(
                name="clinical_analyzer",
                role="Analyze clinical data, symptoms, and patient records",
                agent_type="specialist",
                model=ModelConfig(primary="claude-opus-4-6"),
                reasoning=ReasoningPattern.REFLECTION,
                memory=Memory(short_term=True, semantic=True),
                guardrails=Guardrails(
                    input=["pii_detection"],
                    output=["schema_validation", "confidence_threshold", "pii_masking"],
                ),
                token_budget=4000,
            ),
            AgentSpec(
                name="evidence_retriever",
                role="Search medical literature and clinical guidelines",
                agent_type="specialist",
                model=ModelConfig(primary="claude-sonnet-4-6"),
                reasoning=ReasoningPattern.REACT,
                memory=Memory(short_term=True, graphrag=True),
                token_budget=3000,
            ),
        ])
    elif domain == DomainType.FINANCIAL:
        specialists.extend([
            AgentSpec(
                name="data_analyst",
                role="Analyze financial data, calculate metrics, identify patterns",
                agent_type="specialist",
                model=ModelConfig(primary="claude-sonnet-4-6"),
                reasoning=ReasoningPattern.REACT,
                memory=Memory(short_term=True, semantic=True),
                token_budget=4000,
            ),
            AgentSpec(
                name="risk_assessor",
                role="Evaluate financial risks and compliance violations",
                agent_type="specialist",
                model=ModelConfig(primary="claude-sonnet-4-6"),
                reasoning=ReasoningPattern.REFLECTION,
                guardrails=Guardrails(output=["schema_validation"]),
                hitl=HITLMode.PRE_ACTION,
                token_budget=3000,
            ),
        ])
    elif domain == DomainType.SUPPORT:
        specialists.extend([
            AgentSpec(
                name="classifier",
                role="Classify tickets by category, priority, and department",
                agent_type="classifier",
                model=ModelConfig(primary="claude-haiku-4-5"),
                reasoning=ReasoningPattern.REACT,
                memory=Memory(short_term=True),
                token_budget=500,
            ),
            AgentSpec(
                name="resolver",
                role="Generate solutions and draft responses for support tickets",
                agent_type="specialist",
                model=ModelConfig(primary="claude-sonnet-4-6"),
                reasoning=ReasoningPattern.REACT,
                memory=Memory(short_term=True, episodic=True, semantic=True),
                token_budget=3000,
            ),
        ])
    elif domain == DomainType.CODING:
        specialists.extend([
            AgentSpec(
                name="code_analyzer",
                role="Analyze code, identify bugs, suggest improvements",
                agent_type="specialist",
                model=ModelConfig(primary="claude-opus-4-6"),
                reasoning=ReasoningPattern.REFLECTION,
                memory=Memory(short_term=True),
                token_budget=8000,
            ),
            AgentSpec(
                name="code_generator",
                role="Generate code, tests, and documentation",
                agent_type="specialist",
                model=ModelConfig(primary="claude-opus-4-6"),
                reasoning=ReasoningPattern.REACT,
                memory=Memory(short_term=True),
                token_budget=8000,
            ),
        ])
    else:
        # Generic specialists based on responsibility count
        for i in range(min(signals.num_responsibilities, 3)):
            specialists.append(AgentSpec(
                name=f"specialist_{i + 1}",
                role=f"Specialist agent {i + 1}",
                agent_type="specialist",
                model=ModelConfig(primary="claude-sonnet-4-6"),
                reasoning=ReasoningPattern.REACT,
                memory=Memory(short_term=True),
                token_budget=4000,
            ))

    return specialists


def select_infrastructure(signals: IntakeSignals, agents: list[AgentSpec]) -> InfraConfig:
    """Select infrastructure based on signals and agent needs."""
    has_graphrag = any(a.memory.graphrag for a in agents)
    has_episodic = any(a.memory.episodic for a in agents)

    return InfraConfig(
        vector_db="pinecone" if (has_graphrag or has_episodic) else None,
        graph_db="neo4j" if has_graphrag else None,
        message_queue="redis" if len(agents) > 2 else None,
        observability="langfuse",
    )


class Recommender:
    """Main recommendation engine that produces a Blueprint from a description."""

    def recommend(self, description: str, language: str = "en") -> Blueprint:
        """Generate an opinionated architecture recommendation.

        Args:
            description: Natural language description of the desired system.
            language: Output language code.

        Returns:
            A complete Blueprint with recommended architecture.
        """
        # Phase 0: Extract signals
        signals = extract_signals(description)

        # Layer 1: System classification
        system_type = classify_system(signals)

        # Layer 2: Architecture pattern
        pattern = select_pattern(signals, system_type)

        # Layer 3: Framework
        framework = select_framework(signals, pattern)

        # Generate agents
        agents = generate_agents(signals, pattern)

        # Infrastructure
        infra = select_infrastructure(signals, agents)

        # Compliance
        compliance = ComplianceConfig(
            regulations=signals.compliance_types or [],
            audit_trail=signals.needs_audit_trail or signals.needs_compliance,
        )

        # Build blueprint
        blueprint = Blueprint(
            name=_generate_project_name(description),
            description=description,
            language=language,
            system_type=system_type,
            pattern=pattern,
            domain=signals.domain.value,
            scale=signals.expected_scale,
            framework=framework,
            agents=agents,
            infrastructure=infra,
            compliance=compliance,
            decisions=[
                DesignDecision(
                    dimension="D1-Purpose",
                    decision=f"System type: {system_type.value}",
                    justification=f"Based on {signals.num_responsibilities} detected responsibilities and {'exploratory' if signals.is_exploratory else 'deterministic'} nature.",
                    alternatives_considered=[t.value for t in SystemType if t != system_type],
                ),
                DesignDecision(
                    dimension="D2-Architecture",
                    decision=f"Pattern: {pattern.value}",
                    justification=_pattern_justification(pattern, signals),
                    research=[
                        ResearchFinding(
                            source="Taxonomy of Hierarchical MAS (ArXiv 2508.12683, 2025)",
                            finding="34% fewer coordination errors in compliance-heavy workflows vs swarm",
                            relevance="Applicable to regulated domains with audit requirements",
                            year=2025,
                        ),
                    ] if pattern == ArchitecturePattern.SUPERVISOR_HIERARCHICAL else [],
                ),
            ],
        )

        return blueprint


def _generate_project_name(description: str) -> str:
    """Generate a project name from description."""
    words = description.lower().split()[:4]
    clean = [w for w in words if len(w) > 2 and w.isalpha()]
    return "-".join(clean[:3]) or "agent-system"


def _pattern_justification(pattern: ArchitecturePattern, signals: IntakeSignals) -> str:
    """Generate human-readable justification for pattern choice."""
    justifications = {
        ArchitecturePattern.SINGLE: "Single clear responsibility detected. No need for multi-agent overhead.",
        ArchitecturePattern.PIPELINE: "2-3 sequential responsibilities with clear data handoffs. Pipeline is simplest.",
        ArchitecturePattern.SUPERVISOR_HIERARCHICAL: (
            f"Domain ({signals.domain.value}) requires centralized control for "
            f"{'compliance/auditability' if signals.needs_compliance else 'coordination'}. "
            "Hierarchical pattern provides clear accountability and audit trail."
        ),
        ArchitecturePattern.BLACKBOARD_SWARM: (
            "Exploratory/creative task without strict ordering. "
            "Swarm pattern enables resilient parallel exploration."
        ),
        ArchitecturePattern.HYBRID: (
            "Enterprise scale with mixed deterministic and exploratory subsystems. "
            "Hybrid provides top-down planning with bottom-up autonomous execution."
        ),
    }
    return justifications.get(pattern, "Selected based on signal analysis.")
