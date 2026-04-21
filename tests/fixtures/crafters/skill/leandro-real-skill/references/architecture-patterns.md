# Architecture Patterns & Decision Engine

This is the embedded knowledge base for CLean-agents. Use this for fast decisions. Launch live
research (WebSearch) when you need current framework versions, recent papers, or domain-specific evidence.

## Table of Contents
1. Architecture Patterns (detailed)
2. Framework Comparison Matrix
3. Memory Architecture Decision Matrix
4. Reasoning Framework Selection
5. Guardrails & Safety Patterns
6. Observability Stack
7. Error Recovery & Fallback Chains
8. Human-in-the-Loop Patterns
9. Production Deployment Checklist

---

## 1. Architecture Patterns

### Supervisor Hierarchical
- **Source**: "A Taxonomy of Hierarchical Multi-Agent Systems" (2025, ArXiv 2508.12683)
- **Pattern**: Central orchestrator plans, delegates, decides completion
- **Best for**: Deterministic workflows, compliance-heavy, auditability needed
- **Strengths**: Clear accountability, auditable decisions, sequential reasoning
- **Weaknesses**: Bottleneck at supervisor, fragile if supervisor fails
- **Signals**: step-by-step flow, regulated domain, audit requirements, data sensitivity

**When to recommend**: The case has a clear sequence (A → B → C), needs compliance/auditability,
handles sensitive data, or operates in a regulated domain (legal, medical, financial).

**Component template**:
- Orchestrator agent (planner + router)
- 2-5 specialist agents (one per domain responsibility)
- Shared message queue (not shared memory — message decoupling for fault tolerance)
- Guardrails per layer (input → processing → output)
- HITL at decision points for high-stakes actions

### Blackboard / Swarm
- **Source**: O'Reilly "Designing Effective Multi-Agent Architectures" (2025)
- **Pattern**: Autonomous agents contribute partial solutions to shared state
- **Best for**: Exploratory, creative, research, collaborative reasoning
- **Strengths**: Resilient to individual failures, explores multiple paths
- **Weaknesses**: Complex state management, harder to audit
- **Signals**: no predetermined order, creative/exploratory task, resilience > efficiency

**When to recommend**: The problem is open-ended, there's no single "right" sequence, multiple
perspectives add value, or you need robustness (if one agent fails, others compensate).

**Component template**:
- Shared blackboard (central state store)
- 3-N autonomous specialist agents
- Consensus/voting mechanism for final decisions
- Episodic memory per agent + shared semantic memory
- Circuit breakers per agent

### Hybrid Hierarchical-Swarm
- **Source**: Emerging best practice (2025), Palantir AIP architecture
- **Pattern**: Top-down planning + bottom-up autonomous execution
- **Best for**: Enterprise scale, complex multi-domain problems
- **Strengths**: Efficiency of hierarchy + resilience of swarms
- **Weaknesses**: Most complex to implement, needs mature observability
- **Signals**: enterprise scale (>100 ops/day), subsystems with different needs, mix of deterministic and exploratory

**When to recommend**: The system has subsystems that need central coordination, BUT within each
subsystem there are exploratory/creative tasks. Think: top layer defines goals → middle manages
teams → bottom executes autonomously.

**Component template**:
- Strategic orchestrator (goal setting, resource allocation)
- Team coordinators (mid-level orchestration)
- Autonomous executor swarms (bottom-level)
- GraphRAG for knowledge (relationship-aware retrieval)
- Ontology layer for enterprise (formal semantic grounding)
- Full observability stack (runs, traces, threads)

### Pipeline (Sequential Chain)
- **Best for**: Simple multi-step workflows with clear input/output handoffs
- **Signals**: 2-3 steps, clear data flow, each step transforms input
- **Component template**: Agent A → Agent B → Agent C, with error handling at each step

### Single Agent
- **Best for**: Focused tasks, conversational interfaces, simple tool use
- **Signals**: one responsibility, straightforward reasoning, tool-augmented
- **Component template**: One agent with ReAct loop + tools + guardrails

---

## 2. Framework Comparison Matrix

| Framework | MVP Speed | Learning Curve | Model Flex | State Mgmt | Graph Support | Prod Ready | Best For |
|-----------|-----------|---------------|------------|------------|--------------|------------|----------|
| OpenAI SDK | 3-5 days | Lowest | 100+ models | Simple | No | High | Quick MVPs, simple agents |
| CrewAI | 1-2 weeks | Low | Multi-model | Moderate | No | High | Multi-role teams, balance |
| LangGraph | 2-3 weeks | High | Multi-model | Advanced | Yes (DAG) | High | Complex orchestration, cycles |
| Claude SDK | 3-4 weeks | High | Claude only | Simple | No | Very High | Safety-first, extended thinking |
| AutoGen | 2-3 weeks | Moderate | Moderate | Moderate | No | Medium | Conversational multi-agent |
| DSPy | Variable | High | Multi-model | Simple | Yes | High | Systematic prompt optimization |

### Selection flowchart (use internally, don't show to user)

```
IF fast MVP needed AND simple → OpenAI Agents SDK
IF multi-role collaboration AND balance → CrewAI
IF complex state machines OR cycles → LangGraph
IF safety critical OR Claude features needed → Claude Agent SDK
IF enterprise + ontology + compliance → Custom + Ontology
IF systematic optimization needed → DSPy
```

---

## 3. Memory Architecture Decision Matrix

### The Four Decisions
1. **What to store**: recent context, learned patterns, critical events
2. **How to store**: vector DB, graph DB, relational, cache
3. **How to retrieve**: semantic search, SQL, keyword, hybrid
4. **When to forget**: fixed retention, importance-based, LRU

### Selection by signal

| User need | Memory type | Implementation |
|-----------|------------|----------------|
| Coherent conversations | Short-term (context window) | System prompt + history + tools |
| Remember past events | Episodic | Vector DB with timestamps |
| Accumulate domain knowledge | Semantic | Structured facts/rules store |
| Improve with usage | Procedural | Learned skills repository |
| Reason about relationships | GraphRAG | Knowledge graph + RAG retrieval |

### GraphRAG specifics
- **Source**: Microsoft Research (2024-2025)
- **Performance**: +38% accuracy on complex reasoning vs vanilla RAG
- **Best for**: Cases requiring relationship-aware retrieval (legal, medical, research)
- **Implementation**: Extract entities → build knowledge graph → community detection → summarize → retrieve via graph queries
- **Tools**: Neo4j GraphRAG Context Provider, LazyGraphRAG for large corpora

---

## 4. Reasoning Framework Selection

| Pattern | Structure | Best for | Token efficiency |
|---------|-----------|----------|-----------------|
| ReAct | Linear loop (observe→reason→act) | Sequential tool use, grounded reasoning | High |
| Tree of Thoughts | Multi-path tree with backtracking | Strategic decisions, multi-path reasoning | Medium |
| Graph of Thoughts | Arbitrary graph connections | Complex dependencies | Low-Medium |
| HTN Planning | Hierarchical task decomposition | Complex task breakdown, constrained domains | Medium |
| Reflection | Generate → evaluate → refine | Self-improvement, accuracy-critical | Medium |
| Reasoning models (o1/R1) | Built-in chain of thought | Deep reasoning, math, code | Variable |

### Selection by signal

```
IF sequential tool use → ReAct
IF strategic decisions with alternatives → Tree of Thoughts
IF complex task decomposition → HTN Planning
IF accuracy-critical with self-improvement → Reflection
IF deep reasoning + budget available → Reasoning models
```

---

## 5. Guardrails & Safety Patterns

### Layered Defense Architecture
```
User Input → Input Guardrails → LLM → Output Guardrails → User
                 ↓ Block              ↓ Modify/Filter
```

### Input Guardrails
- Pattern matching (injection detection)
- Prompt classification (safe/unsafe)
- Encoding detection (Base64, hex, ROT13, unicode)
- Size/token limits
- PII detection pre-processing

### Output Guardrails
- PII masking (regex + NER)
- Content filtering (topic boundaries)
- Schema validation (structured outputs)
- Confidence thresholds
- Format compliance

### Hybrid Deterministic-Neural
- **Neural**: LLM handles flexible/creative parts
- **Deterministic**: Rules engine handles must-not-fail parts
- Best of both: natural language + guaranteed safety

### Red Teaming (table stakes for production)
- Dedicate time to breaking guardrails before deployment
- Test every injection technique
- Feed adversarial inputs from OWASP Top 10 LLM 2025
- Document edge cases, iterate defenses

---

## 6. Observability Stack

### Core Primitives (Source: LangChain Agent Observability, 2025)
1. **Runs**: Single execution step (one LLM call + I/O)
2. **Traces**: Complete agent execution (all runs + relationships)
3. **Threads**: Multi-turn conversations (multiple traces over time)

### Key Metrics
- Success rate across runs
- Tool selection distribution
- Reasoning path diversity
- Token efficiency variance
- Error recovery effectiveness
- Latency percentiles (p50, p95, p99)
- Cost per operation

### Testing non-deterministic agents
- **Three-level evaluation**: single-step → full-turn → multi-turn
- **Critical**: Test each scenario REPEATEDLY (N=50+) to understand actual behavior patterns
- Single test pass shows what CAN happen, not what TYPICALLY happens

---

## 7. Error Recovery & Fallback Chains

### Graceful Degradation Chain
```
Primary: GPT-4o / Claude Opus (full capability)
    ↓ timeout/failure
Fallback 1: Claude Sonnet / GPT-4-mini (faster, cheaper)
    ↓ timeout/failure
Fallback 2: Local small model (no network dependency)
    ↓ timeout/failure
Fallback 3: Cached/template response (deterministic)
    ↓ timeout/failure
Escalate to human
```

### Circuit Breaker Pattern
- Track failure rate per dependency
- If failures > threshold in time window → STOP calling → fail fast
- Example: API fails >5 times in 60s → circuit opens for 5 minutes

### Retry Strategy
- Exponential backoff: 1s, 2s, 4s, 8s (with ±10% jitter)
- Cap at 60s maximum
- Budget limit: max total retries before giving up

---

## 8. Human-in-the-Loop Patterns

### Autonomy Levels
- **L1 Full auto**: No human involvement
- **L2 Passive monitoring**: Human watches dashboards
- **L3 Active approval**: Human approves high-stakes actions
- **L4 Co-pilot**: Human decides, agent executes

### Integration Points
- **Pre-action (approval)**: Review plan before execution
- **Post-action (validation)**: Review results after execution
- **Tool-level**: Some tools auto-execute (low-risk), others need approval (high-risk)

### Scaling HITL
- Route by risk level to different reviewers
- Use agent confidence scores for routing
- Batch similar decisions for efficiency
- Monitor approval rates to identify systematic issues

---

## 9. Production Deployment Checklist

### Pre-Deploy
- [ ] Guardrails: input + output with red team testing
- [ ] Memory: appropriate layers configured
- [ ] Fallback: graceful degradation chain
- [ ] Circuit breakers: all external dependencies
- [ ] Observability: runs, traces, threads tracked
- [ ] HITL: approval points for high-stakes actions
- [ ] Evaluation: multi-dimensional framework ready
- [ ] Tools: dynamic selection validated
- [ ] Reflection: self-correction loops (if applicable)
- [ ] Ontology: domain constraints (if enterprise)

### Deploy
- [ ] Rate limiting
- [ ] Monitoring dashboards
- [ ] Alerting on anomalies
- [ ] Full trace logging
- [ ] A/B testing vs baseline
- [ ] Rollback plan

### Post-Deploy
- [ ] Continuous automated benchmarks
- [ ] User feedback loop
- [ ] Incident analysis from traces
- [ ] Prompt optimization (DSPy or similar)
- [ ] Tool performance monitoring
- [ ] Reflection quality assessment
