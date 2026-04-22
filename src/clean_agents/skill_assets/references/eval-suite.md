# Eval Suite Generator Module

Auto-generate evaluation suites for the designed agentic system:
test cases, metrics, Agent-as-Judge configs, and regression benchmarks.

---

## 1. Evaluation Framework

### Three-Level Evaluation Architecture

```
Level 1: Single Step (unit tests)
  → Does each agent do its job correctly in isolation?

Level 2: Full Turn (integration tests)
  → Does the full pipeline produce correct results end-to-end?

Level 3: Multi-Turn (conversation/session tests)
  → Does the system maintain quality across extended interactions?
```

### Critical Rule: Statistical Significance

Agent behavior is NON-DETERMINISTIC. A single test proves nothing.

| Confidence Level | Minimum Runs | Use Case |
|-----------------|-------------|----------|
| Sanity check | 10-20 runs | Quick validation during dev |
| Development benchmark | 50-100 runs | Internal quality tracking |
| Production release gate | 100-150 runs | Comparison between versions |
| Published results | 200-300 runs | External reporting |

Use bootstrap confidence intervals (95% CI) for all metrics.

---

## 2. Metrics by Agent Role

### Universal Metrics (every agent)

| Metric | Formula | Target | Alert Threshold |
|--------|---------|--------|----------------|
| Task Completion Rate | successful / total | >95% | <90% |
| Latency p50 | Median response time | <2s | >5s |
| Latency p95 | 95th percentile | <5s | >10s |
| Token Efficiency | output_quality / tokens_used | Baseline | <80% baseline |
| Error Rate | errors / total | <2% | >5% |
| Cost per Successful Task | total_cost / successful | Baseline | >150% baseline |

### Orchestrator-Specific

| Metric | What It Measures | Target |
|--------|-----------------|--------|
| Routing Accuracy | Correct agent selection | >95% |
| Delegation Efficiency | Optimal task decomposition | >90% agreement with expert |
| Recovery Rate | Successful error handling | >80% |
| Unnecessary Escalation | Over-delegation to expensive models | <10% |

### Specialist-Specific

| Metric | What It Measures | Target |
|--------|-----------------|--------|
| Domain Accuracy | Correctness within domain | >90% |
| Tool Selection Accuracy | Right tool for task | >95% |
| Hallucination Rate | Fabricated information | <3% |
| Reasoning Faithfulness | Steps follow from evidence | >90% |

### RAG-Specific (use RAGAS framework)

| Metric | What It Measures | Target |
|--------|-----------------|--------|
| Context Relevance | Retrieved docs match query | >0.8 |
| Faithfulness | Answer grounded in context | >0.9 |
| Answer Relevance | Response addresses query | >0.85 |
| Context Precision | Relevant docs ranked higher | >0.75 |

---

## 3. Agent-as-Judge Configuration

### Why Agent-as-Judge

Human evaluation is slow and expensive. Use a strong LLM (Opus/GPT-4) to evaluate
agent outputs against rubrics. Research shows >85% agreement with human evaluators.

### Judge Prompt Template

```
You are evaluating the output of an AI agent. Score on these criteria:

## Criteria
[For each criterion:]
- **[Name]** (weight: [W]%): [Definition]
  - Score 1: [what a terrible response looks like]
  - Score 3: [what an average response looks like]
  - Score 5: [what an excellent response looks like]

## Input
[The original user request]

## Agent Output
[The agent's response]

## Expected Output (if available)
[The reference/gold standard]

## Instructions
1. Evaluate each criterion independently
2. Provide a brief justification for each score
3. Calculate weighted total

Respond in JSON:
{
  "scores": {
    "[criterion_1]": {"score": N, "justification": "..."},
    "[criterion_2]": {"score": N, "justification": "..."}
  },
  "total": N.N,
  "pass": true/false,
  "summary": "One sentence overall assessment"
}
```

### Judge Model Selection

| Judge Model | Cost | Agreement with Human | Best For |
|-------------|------|---------------------|----------|
| Claude Opus 4.6 | $0.03/eval | ~90% | Production release gates |
| Claude Sonnet 4.6 | $0.018/eval | ~85% | Development benchmarks |
| GPT-4o | $0.012/eval | ~85% | Budget-conscious evaluation |

### Calibration

Before trusting Agent-as-Judge:
1. Create 20-30 manually graded examples
2. Run judge on same examples
3. Calculate agreement (Cohen's Kappa)
4. If Kappa < 0.7, refine rubric
5. Re-calibrate monthly

---

## 4. Test Case Generation

### Auto-Generation Strategy

For each agent, generate test cases across these dimensions:

```
1. Happy Path (40% of tests)
   → Standard inputs that should succeed
   → Covers main use cases

2. Edge Cases (25% of tests)
   → Boundary inputs (empty, very long, special chars)
   → Ambiguous requests
   → Multi-language inputs

3. Adversarial (20% of tests)
   → Prompt injection attempts
   → Out-of-scope requests
   → Malformed tool responses

4. Regression (15% of tests)
   → Known bugs from production
   → Previously failed scenarios
   → Customer-reported issues
```

### Test Case Template

```json
{
  "id": "TC-001",
  "agent": "document_analyzer",
  "category": "happy_path",
  "input": {
    "user_message": "Analyze this contract for risk clauses",
    "context": {"document": "sample_contract.pdf"},
    "tools_available": ["read_document", "search_knowledge_base"]
  },
  "expected": {
    "tool_calls": ["read_document"],
    "output_contains": ["risk", "liability", "indemnification"],
    "output_format": "structured_json",
    "max_tokens": 2000
  },
  "evaluation": {
    "criteria": ["accuracy", "completeness", "format_compliance"],
    "pass_threshold": 3.5,
    "judge_model": "claude-opus-4-6"
  }
}
```

### Generation from System Design

When generating eval suite from the blueprint:

```
FOR each agent in the system:
  1. Read agent spec (role, tools, domain, constraints)
  2. Generate 5 happy path cases from the agent's primary use case
  3. Generate 3 edge cases per tool (empty input, malformed, timeout)
  4. Generate 2 adversarial cases (injection, out-of-scope)
  5. Generate 1 regression template (empty, to be filled from production)

FOR the full system:
  1. Generate 5 end-to-end scenarios covering the main workflow
  2. Generate 2 multi-turn conversation scenarios
  3. Generate 2 failure recovery scenarios (agent crash, tool timeout)
  4. Generate 1 load scenario (concurrent requests)
```

---

## 5. Benchmark Suite Structure

### Directory Layout

```
evals/
  config.yaml           # Eval configuration (models, thresholds, runs)
  test_cases/
    unit/               # Level 1: per-agent tests
      orchestrator.json
      specialist_1.json
      classifier.json
    integration/        # Level 2: end-to-end tests
      main_workflow.json
      error_recovery.json
    conversation/       # Level 3: multi-turn tests
      session_1.json
      session_2.json
    adversarial/        # Security-focused tests
      injection.json
      data_leakage.json
  rubrics/
    accuracy.yaml       # Scoring rubric per criterion
    completeness.yaml
    safety.yaml
  baselines/
    v1_baseline.json    # Historical results for regression
  reports/
    latest_run.html     # Auto-generated HTML report
```

### Config Template

```yaml
eval_config:
  judge_model: "claude-opus-4-6"
  runs_per_test: 50
  pass_threshold: 3.5
  confidence_interval: 0.95
  
  metrics:
    - task_completion_rate
    - latency_p50
    - latency_p95
    - token_efficiency
    - error_rate
    - cost_per_task
  
  alerts:
    task_completion_rate: {min: 0.90}
    error_rate: {max: 0.05}
    latency_p95: {max: 10000}  # ms
    cost_per_task: {max: 0.10}  # USD
  
  regression:
    compare_to: "baselines/v1_baseline.json"
    max_degradation: 0.05  # 5% degradation allowed
```

---

## 6. Evaluation Platform Comparison

| Platform | Free Tier | Strengths | Weaknesses |
|----------|-----------|-----------|------------|
| LangSmith | 5k traces/mo | Deep LangChain integration | Vendor lock-in |
| Braintrust | Generous free | End-to-end, caching | Newer platform |
| Langfuse | 50k obs/mo | Open source, self-hostable | Less polished UI |
| Humanloop | Limited | Collaboration, CI/CD | Expensive at scale |
| Patronus AI | Limited | Safety/compliance focus | Narrow scope |
| Custom (recommended) | Free | Full control, no lock-in | Build effort |

### Recommendation

```
IF using LangChain/LangGraph → LangSmith (natural fit)
IF self-hosting preferred → Langfuse (open source)
IF safety-critical domain → Patronus AI + custom
IF maximum flexibility → Custom eval framework + Agent-as-Judge
DEFAULT → Custom with Agent-as-Judge (cheapest, most flexible)
```

---

## 7. Output in HTML Blueprint

Add an "Eval Suite" tab showing:

1. **Test Coverage Matrix** — agents x test categories, with counts
2. **Generated Test Cases** — expandable JSON blocks per agent
3. **Judge Configuration** — rubric preview, model, thresholds
4. **Metrics Dashboard** — which metrics tracked, alert thresholds
5. **Benchmark Config** — YAML config ready to copy
6. **Cost Estimate** — eval suite run cost (judge calls * tests * runs)

### Export

Generate a downloadable `evals/` directory structure that the engineer can
drop into their project and run immediately.
