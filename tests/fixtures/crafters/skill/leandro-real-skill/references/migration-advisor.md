# Migration Advisor Module

Analyze existing agentic systems and recommend migration paths:
framework migration, model migration, and architecture migration.

---

## 1. Migration Types

### Type A: Framework Migration

Moving between orchestration frameworks (e.g., CrewAI → LangGraph).

### Type B: Model Migration

Switching LLM providers (e.g., GPT-4 → Claude, proprietary → open source).

### Type C: Architecture Migration

Evolving system structure (e.g., single agent → multi-agent, monolith → microservices).

---

## 2. Framework Migration

### Compatibility Matrix

| From → To | Effort | Rewrite % | Timeline | Risk |
|-----------|--------|-----------|----------|------|
| CrewAI → LangGraph | High | 50-80% | 3-6 months | Medium |
| OpenAI SDK → Claude SDK | Medium | 30-50% | 2-4 months | Low |
| LangChain → LangGraph | Low | 20-30% | 1-2 months | Low |
| AutoGen → CrewAI | Medium | 40-60% | 2-4 months | Medium |
| Custom → LangGraph | High | 60-90% | 4-8 months | High |
| Any → Custom | High | 80-100% | 4-8 months | High |

### Key Migration Challenges

| Challenge | Impact | Mitigation |
|-----------|--------|-----------|
| State management differences | Data loss, bugs | Map state schemas before migrating |
| Tool interface changes | Broken integrations | Abstract tools behind interface layer |
| Memory format incompatibility | Lost context | Export/import memory with schema mapping |
| Prompt format differences | Quality regression | A/B test prompts in both frameworks |
| Testing infrastructure | Coverage gaps | Port test suites first, then code |

### Strangler Fig Pattern for Frameworks

Recommended approach: gradual replacement, not big-bang rewrite.

```
Phase 1 (Week 1-4): Shadow Mode
  → New framework runs alongside old
  → Both process same inputs
  → Compare outputs, log discrepancies
  → No production traffic to new system

Phase 2 (Week 5-8): Canary (10%)
  → Route 10% of traffic to new framework
  → Monitor quality metrics closely
  → Compare against baseline: latency, accuracy, cost
  → Rollback trigger: any metric >5% worse

Phase 3 (Week 9-12): Ramp (10% → 25% → 50%)
  → Gradually increase traffic
  → Each ramp-up requires 1 week of stable metrics
  → Document all edge cases found

Phase 4 (Week 13-16): Full Migration (50% → 100%)
  → Complete cutover
  → Keep old system warm for 2 weeks (instant rollback)
  → Decommission old system after 30 days stable
```

---

## 3. Model Migration

### Decision Triggers

| Trigger | Action |
|---------|--------|
| Cost reduction needed | Evaluate cheaper models on your eval suite |
| Quality improvement needed | Benchmark newer models on your specific tasks |
| Provider reliability issues | Add fallback provider, consider primary switch |
| Compliance requirement | Switch to compliant provider (EU → Mistral, HIPAA → BAA provider) |
| New model release | Run eval suite against new model before switching |

### Migration Process

```
Step 1: Baseline
  → Run full eval suite on current model (N=100+ runs)
  → Record: accuracy, latency, cost, edge case behavior
  → This is your comparison benchmark

Step 2: Candidate Evaluation
  → Run same eval suite on candidate model
  → Compare: accuracy within 2%, latency within 20%, cost change
  → Pay special attention to: tool use accuracy, structured output, edge cases

Step 3: Prompt Adaptation
  → Models respond differently to same prompts
  → Adjust system prompts for new model's strengths
  → Re-run eval suite after prompt changes

Step 4: Shadow Testing
  → Run new model in shadow mode (no production impact)
  → Compare outputs on live traffic for 1-2 weeks
  → Flag and investigate all discrepancies

Step 5: Canary Deployment
  → Route 10% → 25% → 50% → 100%
  → Each step requires 3-5 days of stable metrics
  → Automated rollback if quality drops >5%
```

### Cost Break-Even Analysis

| Migration Type | Break-Even Point | Example |
|---------------|-----------------|---------|
| Opus → Sonnet | Immediate (60% cheaper) | If quality acceptable |
| GPT-4 → Claude Sonnet | 1-2 weeks (prompt tuning) | Similar capability, different pricing |
| Proprietary → Open Source | 2-4 months (infra setup) | Savings >$2k/mo at 2M+ tokens/day |
| Single model → Routed | 2-4 weeks (router dev) | 30% savings at scale |

---

## 4. Architecture Migration

### Single Agent → Multi-Agent

**When to migrate:**
- Single agent exceeding context window regularly
- Response quality degrading on complex tasks
- Need for specialized domain knowledge
- Latency too high (can parallelize)

**Migration path:**
```
Phase 1: Identify Responsibilities
  → Map all tasks the single agent handles
  → Group by domain/capability
  → Identify parallelizable vs sequential

Phase 2: Extract First Specialist
  → Pick the clearest, most independent responsibility
  → Create specialist agent with its own prompt + tools
  → Orchestrator routes to specialist for that domain
  → Keep everything else in "general" agent

Phase 3: Iterate
  → Extract next specialist
  → Refine orchestrator routing
  → Repeat until "general" agent only orchestrates

Phase 4: Optimize
  → Assign optimal models per agent (model-choosing.md)
  → Add caching and routing optimization
  → Implement parallel execution where possible
```

### Monolith → Microservices (for Agent Systems)

**Decomposition strategy:**
```
1. Identify agent boundaries (one responsibility per service)
2. Define communication protocol (message queue vs direct call)
3. Implement shared state management (if needed)
4. Add observability at service boundaries
5. Deploy incrementally (one service at a time)
```

---

## 5. Risk Assessment Framework

### Migration Risk Scorecard

| Dimension | Weight | Low (1) | Medium (3) | High (5) |
|-----------|--------|---------|------------|----------|
| Scope | 25% | 1 component | 3-5 components | >5 components |
| Data | 20% | No data migration | Schema mapping | Complex data transform |
| Quality | 20% | Tests pass | Some quality gaps | Significant rework |
| Timeline | 15% | Flexible | Fixed milestone | Hard deadline |
| Team | 10% | Experienced | Some gaps | New technology |
| Rollback | 10% | Instant | Hours | Days/impossible |

**Score interpretation:**
- 1.0-2.0: Low risk — proceed with standard process
- 2.1-3.5: Medium risk — add monitoring, extend timeline 25%
- 3.6-5.0: High risk — consider phased approach, add contingency

### Rollback Plan Template

```
Trigger Conditions:
  - Quality metric drops >5% for >1 hour
  - Error rate exceeds 10% for >15 minutes
  - P95 latency exceeds 3x baseline
  - Cost exceeds 2x baseline for >4 hours

Rollback Process:
  1. Route 100% traffic to old system (< 1 minute)
  2. Verify old system healthy (metrics normal)
  3. Investigate root cause in new system
  4. Document findings, update migration plan
  5. Re-attempt after fixing issues
```

---

## 6. Output in HTML Blueprint

Add a "Migration Advisor" tab showing:

1. **Current State** — what the engineer has now (if applicable)
2. **Target State** — the recommended architecture
3. **Migration Path** — phased plan with timeline
4. **Risk Scorecard** — scored assessment with mitigations
5. **Rollback Plan** — trigger conditions and process
6. **Cost of Migration** — effort hours + infrastructure changes

### Mermaid: Migration Timeline

```
gantt
    title Migration Plan
    dateFormat YYYY-MM-DD
    section Phase 1 Shadow
    Setup new framework    :a1, 2026-01-01, 14d
    Shadow testing         :a2, after a1, 14d
    section Phase 2 Canary
    10 percent traffic     :b1, after a2, 7d
    25 percent traffic     :b2, after b1, 7d
    section Phase 3 Ramp
    50 percent traffic     :c1, after b2, 7d
    100 percent traffic    :c2, after c1, 7d
    section Phase 4 Cleanup
    Decommission old       :d1, after c2, 14d
```
