# CLean-agents

**Design, plan, and harden production-grade agentic AI systems.**

CLean-agents is an interactive architect skill for Claude that recommends optimal architectures backed by scientific papers and real-time research — from single agents to multi-agent swarms with GraphRAG and enterprise guardrails.

> **Clean** (well-designed, no unnecessary complexity) + **Lean** (efficient, no over-engineering) = **CLean-agents**

---

## What It Does

Give CLean-agents a natural language description of what you want to build, and it will:

1. **Analyze & Research** — classifies your system, searches for the latest papers and benchmarks
2. **Recommend** — proposes an opinionated architecture with evidence (not a menu of equal options)
3. **Deep Dive** — asks targeted questions that affect the design, updating the blueprint progressively
4. **Generate Blueprint** — interactive HTML with Mermaid diagrams, agent specs, project plan, and code scaffold
5. **Iterate** — change any parameter and it recalculates cascading implications across the system

## CLean-shield: Security Testing

Built-in adversarial security module with 7 attack categories:

| Category | Description |
|----------|-------------|
| Prompt Injection & Jailbreaks | Direct, indirect, multi-turn, encoding attacks |
| Context Contamination | RAG poisoning, memory injection, cross-agent contamination |
| Tool Abuse | Confused deputy, exfiltration, parameter manipulation |
| Data Leakage | PII extraction, system prompt extraction, cross-session |
| Multi-Agent Escalation | Privilege escalation, agent impersonation |
| DoS & Resource Exhaustion | Token flooding, infinite loops, recursive tool calls |
| Supply Chain | Malicious MCP servers, tool shadowing, dependency poisoning |

Two modes: **Static Analysis** (automatic after blueprint) and **Live Red Team** (on-demand against deployed agents).

## 8 On-Demand Modules

After the main blueprint, activate any combination of:

| Module | What It Does |
|--------|-------------|
| **Model Choosing** | Benchmark comparison (BFCL, SWE-Bench, GPQA), model-per-agent assignment, provider risk analysis, multi-provider fallback chains |
| **Prompt Engineering Lab** | Generates optimized system prompts per agent role (orchestrator, specialist, classifier, guardian) with anti-pattern catalog |
| **Cost Simulator** | Per-request and monthly cost projections, optimization strategies (routing 30-50% savings, caching 20-40%, batch 50%) |
| **Eval Suite Generator** | Auto-generates test cases, Agent-as-Judge configs, RAGAS metrics for RAG, statistical significance guidance |
| **Observability Blueprint** | Platform comparison (LangSmith/Langfuse/Phoenix/Helicone), OTEL tracing, alerting rules, debugging workflows |
| **Migration Advisor** | Framework/model/architecture migration paths, Strangler Fig pattern, risk scorecards, rollback plans |
| **Compliance Mapper** | EU AI Act, GDPR, SOC 2, HIPAA, SEC/FINRA, ABA — regulation-to-component mapping matrix with gap analysis |
| **Load Testing Planner** | 4 scenarios (ramp/sustained/spike/failover), rate limit strategies, graceful degradation chains, Locust/k6 configs |

## Installation

### As a Claude Code Skill

Copy the `clean-agents/` directory into your `.claude/skills/` folder:

```bash
cp -r clean-agents/ ~/.claude/skills/clean-agents/
```

### As a `.skill` Package

Install the pre-packaged `clean-agents.skill` file through Claude's skill installation interface.

## Repository Structure

```
clean-agents-repo/
├── SKILL.md                              # Main skill definition (16KB)
├── clean-agents.skill                    # Pre-packaged skill file (57KB)
├── references/
│   ├── architecture-patterns.md          # Architecture patterns & decision engine
│   ├── taxonomy.md                       # 12 parametrized dimensions (D1-D12)
│   ├── security-testing.md               # 7 attack categories & defense patterns
│   ├── output-templates.md               # HTML/Mermaid templates & syntax rules
│   ├── model-choosing.md                 # Benchmarks, pricing, provider analysis
│   ├── prompt-engineering.md             # Prompt templates by agent role
│   ├── cost-simulator.md                 # Cost formulas & optimization strategies
│   ├── eval-suite.md                     # Evaluation framework & Agent-as-Judge
│   ├── observability.md                  # Tracing, metrics, alerting configs
│   ├── migration-advisor.md              # Migration paths & risk assessment
│   ├── compliance-mapper.md              # Regulatory mapping (EU AI Act, GDPR, etc.)
│   └── load-testing.md                   # Load scenarios & degradation chains
├── evals/
│   └── evals.json                        # Test cases for skill evaluation
├── LICENSE
└── README.md
```

## Architecture Decision Engine

CLean-agents uses a 4-layer decision engine:

**Layer 1 — System Classification**: Single Agent → Pipeline → Multi-Agent → Complex System

**Layer 2 — Architecture Pattern**: Supervisor Hierarchical, Blackboard/Swarm, Hybrid, Pipeline

**Layer 3 — Framework Selection**: OpenAI SDK (3-5 days), CrewAI (1-2 weeks), LangGraph (2-3 weeks), Claude SDK (3-4 weeks)

**Layer 4 — Transversal Components**: Memory, reasoning, safety, observability, testing

Every recommendation is backed by papers with concrete metrics ("+38% accuracy" not "significant improvement").

## Example Usage

```
User: Necesito un sistema multi-agente para análisis de contratos legales
      con compliance SOX y aprobaciones humanas para decisiones de riesgo.

CLean-agents: Para tu caso recomiendo una arquitectura Supervisor Hierarchical
con 3 agentes especializados. El dominio legal + compliance hacen que el control
centralizado sea esencial — un paper de 2025 sobre MAS jerárquicos muestra 34%
menos errores de coordinación vs swarm en workflows regulados...

[Generates interactive HTML blueprint with Mermaid diagrams]
[Offers on-demand modules: "¿Querés que active el Compliance Mapper para GDPR + SOX?"]
```

## Key Research Sources

- Berkeley Function Calling Leaderboard (BFCL V4)
- Microsoft Research GraphRAG (+38% accuracy vs vanilla RAG)
- OWASP Top 10 for LLM Applications 2025
- Palantir AIP ontology-driven architecture
- NVIDIA Garak & Microsoft PyRIT adversarial testing
- EU AI Act Articles 6, 11, 13, 50 (deadline: August 2, 2026)
- NIST AI Risk Management Framework

## License

MIT License — see [LICENSE](LICENSE) for details.

---

Built with Claude by [@leansroasas](https://github.com/leansroasas)
