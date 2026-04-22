# Taxonomy of Parametrized Questions

The 12 dimensions CLean-agents uses to understand a system. NOT all dimensions apply to every case.
After Phase 0 (intake), determine which dimensions are relevant based on the system classification.

**Rule**: A simple chatbot might need 4 dimensions. An enterprise multi-agent system might need all 12.
Only ask about dimensions that will change your recommendation.

---

## Dimension Relevance Matrix

| Dimension | Single Agent | Pipeline | Multi-Agent | Complex System |
|-----------|:---:|:---:|:---:|:---:|
| D1: Purpose | Always | Always | Always | Always |
| D2: Scale | Sometimes | Always | Always | Always |
| D3: Autonomy | Sometimes | Sometimes | Always | Always |
| D4: Domain & Data | Always | Always | Always | Always |
| D5: Memory | Sometimes | Sometimes | Always | Always |
| D6: Tools | Always | Always | Always | Always |
| D7: Reasoning | Sometimes | Sometimes | Always | Always |
| D8: Safety | Always | Always | Always | Always |
| D9: Observability | Sometimes | Sometimes | Always | Always |
| D10: Testing | Sometimes | Sometimes | Always | Always |
| D11: Costs | Sometimes | Always | Always | Always |
| D12: Team & Timeline | Always | Always | Always | Always |

---

## The 12 Dimensions

### D1: System Purpose
**Root question**: "What real-world problem does this system solve?"
**Phase**: 0-1 (usually answered in the intake)

Sub-questions:
- Who is the end user? (human, another system, API consumer)
- What triggers execution? (event, schedule, user request, webhook)
- What happens if the system fails? (critical impact vs tolerable degradation)
- Does something do this today? (replacement vs greenfield)
- What does "success" look like? (metric, outcome, user reaction)

**What this affects**: Everything — this is the foundation of all recommendations.

### D2: Complexity & Scale
**Root question**: "How many operations per day and how complex are they?"
**Phase**: 1

Sub-questions:
- Expected volume: 1-10, 10-100, 100-1K, 1K+ operations/day
- Acceptable latency: real-time (<1s), seconds, minutes, hours
- Concurrency: sequential vs parallel processing
- Expected growth in 6 months
- Peak vs average load ratio

**What this affects**: Architecture pattern (simple patterns for low scale, hybrid for high),
framework choice (OpenAI SDK for small, LangGraph/custom for large), infrastructure needs.

### D3: Autonomy Level
**Root question**: "How much human supervision does this need?"
**Phase**: 1

Scale:
- **L1 Full auto** — no human in the loop
- **L2 Passive supervision** — human monitors dashboards, intervenes on alerts
- **L3 Active approval** — human approves critical actions before execution
- **L4 Co-pilot** — human decides, agent executes

**What this affects**: HITL integration points, guardrail strictness, fallback chain design,
approval queue architecture, confidence threshold tuning.

### D4: Domain & Data
**Root question**: "What type of data does the system operate on?"
**Phase**: 2

Sub-questions:
- Data types: text, images, audio, structured data, code, PDFs
- Sources: APIs, databases, documents, web scraping, user input
- Sensitivity: PII, PHI, financial, classified, public
- Domain: legal, medical, financial, e-commerce, general
- Data volume per operation: small (<10KB), medium, large (>1MB)

**What this affects**: Memory type (GraphRAG for relationship-heavy, vector for document retrieval),
guardrail requirements (PII filtering for sensitive data), model selection (multimodal if images/audio),
compliance requirements.

### D5: Memory & Knowledge
**Root question**: "Does it need to remember things between sessions?"
**Phase**: 2

Decision matrix:
- Only session context → **Short-term memory** (context window management)
- Remember past events → **+ Episodic** (vector DB with timestamps)
- Accumulate domain knowledge → **+ Semantic** (structured facts/rules)
- Improve with usage → **+ Procedural** (learned skills/preferences)
- Reason about entity relationships → **+ GraphRAG** (knowledge graph + RAG)

Sub-questions:
- Retention policy: how long should memories persist?
- Scope: per-user, per-organization, global?
- Update frequency: real-time, batch, manual?
- Storage backend preference: existing infrastructure?

**What this affects**: Infrastructure (vector DB, graph DB, cache), cost (storage + retrieval calls),
agent architecture (memory-sharing patterns between agents), retrieval strategy.

### D6: Tools & Integrations
**Root question**: "What external systems does it interact with?"
**Phase**: 2

Sub-questions:
- External APIs: which ones, rate limits, authentication methods
- Databases: read/write/both, query complexity
- Cloud services: AWS, GCP, Azure, specific services
- MCP servers: available? custom needed?
- Dynamic tool selection: should the agent choose tools adaptively? (AutoTool pattern)
- Tool count: <5 (simple), 5-15 (moderate), 15+ (needs dynamic selection)

**What this affects**: MCP server design, tool registry architecture, AutoTool integration,
rate limiting strategy, authentication management, cost per operation.

### D7: Reasoning Pattern
**Root question**: "What type of thinking does this require?"
**Phase**: 2

Decision matrix:
- Step-by-step with tools → **ReAct** (linear observe-reason-act loop)
- Explore alternatives before deciding → **Tree of Thoughts** (multi-path with backtracking)
- Complex task decomposition → **HTN Planning** (hierarchical task network)
- Self-improvement needed → **Reflection** (generate-evaluate-refine cycle)
- Deep analytical reasoning → **Reasoning models** (o1/R1 with test-time compute)
- Combination → **Hybrid** (ReAct for routine, ToT for hard decisions)

**What this affects**: Token budget (ToT uses 3-5x more than ReAct), latency, model selection
(reasoning models for deep analysis), cost per operation.

### D8: Safety & Guardrails
**Root question**: "What happens if the agent does something wrong?"
**Phase**: 2

Sub-questions:
- Which actions are irreversible? (critical for HITL placement)
- What data must never be exposed? (PII categories, secrets)
- Compliance requirements: SOX, HIPAA, GDPR, EU AI Act, industry-specific
- Token budget ceiling per operation
- Fallback model chain: which models in which order?
- Red teaming requirements: how adversarial should testing be?

**What this affects**: Guardrail layers (input + output + tool-level), HITL design,
compliance documentation, fallback chain, testing strategy, security audit scope.

### D9: Observability
**Root question**: "How will you know if it's working correctly?"
**Phase**: 2

Sub-questions:
- Success metrics: accuracy, latency, cost, user satisfaction, task completion rate
- Tracing level: runs only, full traces, multi-turn threads
- Agent-as-Judge: should agents evaluate their own outputs?
- Alerting conditions: what triggers an alarm?
- Dashboard requirements: real-time vs batch, audience (eng vs exec)

**What this affects**: Logging infrastructure, storage costs, debugging capability,
alert routing, dashboard design, ongoing maintenance burden.

### D10: Testing & Evaluation
**Root question**: "How do you test a non-deterministic system?"
**Phase**: 2

Recommended levels:
- **Unit tests**: Per-agent with mocked tools (deterministic, fast)
- **Integration tests**: Real agents, mocked external dependencies
- **E2E tests**: Full system, repeated N times (N=50+) for pattern detection
- **Benchmarks**: Standard (AgentBench, GAIA, SWE-bench) or custom
- **Red teaming**: Adversarial inputs (CLean-shield handles this)

Sub-questions:
- Existing test infrastructure? CI/CD pipeline?
- Acceptable flakiness threshold?
- Benchmark selection: standard vs custom vs both?

**What this affects**: CI/CD integration, test infrastructure, development velocity,
confidence in deployments.

### D11: Costs & Budget
**Root question**: "What's the budget per operation?"
**Phase**: 2

Sub-questions:
- Cost ceiling per operation (hard limit vs soft target)
- Primary model vs fallback (quality vs cost trade-off)
- Token optimization: caching? prompt compression? output pruning?
- Self-hosted vs API-based models
- Scaling economics: cost projection at 10x current volume

**What this affects**: Model selection, caching strategy, fallback chain ordering,
token budget per agent, architecture simplicity (cheaper = simpler).

### D12: Team & Timeline
**Root question**: "Who's building this and by when?"
**Phase**: 2

Sub-questions:
- Team size: solo, 2-3, 4+
- Agent development experience: first time, intermediate, expert
- Timeline: 1 week, 1 month, 3 months, 6+ months
- Existing tech stack: Python, TypeScript, other
- CI/CD and deployment infrastructure: exists? needs setup?

**What this affects**: Framework recommendation (CrewAI for small/fast, LangGraph for experienced),
scope of initial blueprint (MVP vs full system), phasing of the project plan.
