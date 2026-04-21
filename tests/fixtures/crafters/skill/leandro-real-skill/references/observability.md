# Observability Blueprint Module

Generate production-ready observability configurations for the designed agentic system:
tracing, metrics, dashboards, and alerting.

---

## 1. Observability Primitives

### Three Core Primitives (Source: LangChain 2025)

| Primitive | Definition | Granularity |
|-----------|-----------|-------------|
| **Run** | Single execution step (1 LLM call + I/O) | Finest — one model invocation |
| **Trace** | Complete agent execution (all runs + relationships) | Medium — one user request |
| **Thread** | Multi-turn session (multiple traces over time) | Coarsest — conversation/session |

### Relationships

```
Thread (session)
  └── Trace 1 (first request)
  │     ├── Run: Orchestrator LLM call
  │     ├── Run: Tool call (search_db)
  │     ├── Run: Specialist A LLM call
  │     ├── Run: Tool call (analyze_doc)
  │     └── Run: Orchestrator LLM call (synthesis)
  └── Trace 2 (follow-up request)
        ├── Run: Orchestrator LLM call
        └── Run: Specialist B LLM call
```

---

## 2. Key Metrics Dashboard

### Latency Metrics

| Metric | Definition | Target | Alert |
|--------|-----------|--------|-------|
| TTFT (Time to First Token) | Request → first streamed token | <500ms | >2s |
| ITL (Inter-Token Latency) | Time between tokens in stream | <50ms | >200ms |
| E2E Latency p50 | Median full request time | <2s | >5s |
| E2E Latency p95 | 95th percentile | <5s | >15s |
| E2E Latency p99 | 99th percentile | <10s | >30s |
| Agent Handoff Latency | Time between agents in pipeline | <200ms | >1s |

### Quality Metrics

| Metric | Definition | Target | Alert |
|--------|-----------|--------|-------|
| Task Completion Rate | Successful / total requests | >95% | <90% |
| Error Rate | Failed / total requests | <2% | >5% |
| Retry Rate | Retried / total requests | <5% | >15% |
| Hallucination Rate | Flagged by judge / total | <3% | >5% |
| Tool Call Success Rate | Successful tool calls / total | >98% | <95% |
| HITL Escalation Rate | Human review / total | Baseline | >2x baseline |

### Cost Metrics

| Metric | Definition | Target | Alert |
|--------|-----------|--------|-------|
| Cost per Request | Total tokens * price | Baseline | >150% baseline |
| Cost per Successful Task | Cost / completed tasks | Baseline | >200% baseline |
| Token Usage (input) | Input tokens per request | Baseline | >2x baseline |
| Token Usage (output) | Output tokens per request | Baseline | >2x baseline |
| Daily Spend | Total API cost per day | Budget | >80% budget |
| Monthly Projected | Daily * 30 extrapolation | Budget | >90% budget |

### Agent-Specific Metrics

| Metric | Applies To | Definition |
|--------|-----------|-----------|
| Routing Accuracy | Orchestrator | Correct agent selected / total |
| Delegation Depth | Orchestrator | Avg delegation chain length |
| Tool Usage Distribution | All | Which tools used, how often |
| Reasoning Steps | Specialists | Avg CoT steps per request |
| Context Window Usage | All | % of max context consumed |
| Cache Hit Rate | All | Cached / total prompts |

---

## 3. Platform Comparison

### Decision Matrix

| Feature | LangSmith | Langfuse | Phoenix (Arize) | Helicone |
|---------|-----------|----------|-----------------|----------|
| **Pricing** | $39-499/mo | $59+/mo or self-host | Open source | $30-150/mo |
| **Free Tier** | 5k traces | 50k observations | Unlimited (self-host) | 10k requests |
| **LangChain Integration** | Native (best) | Good | Good | Moderate |
| **Framework Agnostic** | Moderate | Excellent | Excellent | Excellent |
| **Self-Hosting** | No | Yes (Docker) | Yes | No |
| **Distributed Tracing** | Good | Good | Excellent (OTEL) | Basic |
| **Multi-Agent Support** | Good | Good | Excellent | Basic |
| **Evaluation Built-in** | Yes | Yes | Yes | No |
| **Cost Tracking** | Yes | Yes | Yes | Yes (focus) |
| **Real-time Alerting** | Yes | Basic | Yes | Yes |
| **Data Export** | API | API + DB access | Full access | API |

### Selection Decision Tree

```
IF using LangChain/LangGraph → LangSmith (tightest integration)
IF self-hosting required (compliance) → Langfuse (Docker)
IF OpenTelemetry ecosystem → Phoenix/Arize (OTEL native)
IF cost tracking is priority → Helicone (focused on cost)
IF maximum flexibility → Phoenix + custom dashboards
IF budget constrained → Langfuse self-hosted or Phoenix
DEFAULT → Langfuse (best balance of features, open source)
```

---

## 4. OpenTelemetry Integration

### Why OTEL for Multi-Agent

OpenTelemetry provides vendor-independent distributed tracing across agents.
Critical for: multi-agent systems where requests traverse multiple services.

### Setup Pattern

```python
# OTEL instrumentation for agent system
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure exporter (Jaeger, OTLP, or Langfuse)
provider = TracerProvider()
processor = BatchSpanProcessor(exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("agent-system")

# Instrument agent calls
with tracer.start_as_current_span("orchestrator") as span:
    span.set_attribute("agent.role", "orchestrator")
    span.set_attribute("model", "claude-opus-4-6")
    span.set_attribute("tokens.input", input_tokens)
    span.set_attribute("tokens.output", output_tokens)
    
    # Nested span for specialist
    with tracer.start_as_current_span("specialist_a") as child:
        child.set_attribute("agent.role", "specialist")
        child.set_attribute("tool_calls", tool_count)
```

### Semantic Conventions for LLM (emerging standard)

| Attribute | Type | Description |
|-----------|------|-------------|
| `gen_ai.system` | string | Provider (anthropic, openai) |
| `gen_ai.request.model` | string | Model name |
| `gen_ai.request.max_tokens` | int | Max tokens requested |
| `gen_ai.response.finish_reason` | string | stop, max_tokens, error |
| `gen_ai.usage.input_tokens` | int | Input token count |
| `gen_ai.usage.output_tokens` | int | Output token count |
| `gen_ai.agent.name` | string | Agent identifier |
| `gen_ai.agent.role` | string | orchestrator, specialist, etc |

---

## 5. Alerting Rules

### Critical Alerts (page immediately)

```yaml
alerts:
  - name: high_error_rate
    condition: error_rate > 0.10 for 5m
    severity: critical
    action: page_oncall

  - name: cost_runaway
    condition: hourly_cost > 3x avg_hourly for 15m
    severity: critical
    action: page_oncall + auto_rate_limit

  - name: complete_outage
    condition: success_rate < 0.50 for 2m
    severity: critical
    action: page_oncall + activate_fallback
```

### Warning Alerts (notify, don't page)

```yaml
  - name: elevated_latency
    condition: p95_latency > 2x baseline for 15m
    severity: warning
    action: notify_slack

  - name: quality_degradation
    condition: task_completion_rate < 0.92 for 1h
    severity: warning
    action: notify_slack + trigger_eval_suite

  - name: token_inflation
    condition: avg_tokens_per_request > 1.5x baseline for 1h
    severity: warning
    action: notify_slack

  - name: budget_approaching
    condition: daily_spend > 0.80 * daily_budget
    severity: warning
    action: notify_slack
```

### Anomaly Detection

```yaml
  - name: behavior_drift
    condition: tool_usage_distribution differs >20% from baseline over 24h
    severity: info
    action: log + weekly_report

  - name: new_error_pattern
    condition: new_error_type not seen in last 30 days
    severity: info
    action: log + notify_slack
```

---

## 6. Production Debugging Workflow

### When an Agent Fails

```
1. IDENTIFY: Which trace failed? Which run within the trace?
   → Check trace viewer (LangSmith/Langfuse)

2. ISOLATE: Was it the LLM, a tool, or the orchestrator?
   → LLM: Check input/output, token usage, finish reason
   → Tool: Check tool input, response, latency
   → Orchestrator: Check routing decision, delegation

3. REPRODUCE: Can you replay the exact same input?
   → Use trace replay feature
   → Run N=10 times to check if deterministic or stochastic

4. ROOT CAUSE:
   → Model degradation: Compare to baseline eval suite
   → Tool failure: Check external service status
   → Context overflow: Check token usage vs limit
   → Prompt regression: Diff system prompt versions

5. FIX:
   → Quick: Adjust guardrails, add edge case handling
   → Medium: Refine prompt, adjust routing rules
   → Deep: Architecture change, model switch
```

---

## 7. Output in HTML Blueprint

Add an "Observability" tab showing:

1. **Architecture Diagram** — Mermaid showing trace flow across agents
2. **Metrics Table** — all tracked metrics with targets and alerts
3. **Platform Recommendation** — which observability tool and why
4. **Alert Configuration** — YAML configs ready to deploy
5. **Dashboard Layout** — which charts/panels to create
6. **Cost of Observability** — platform pricing + storage costs

### Mermaid: Trace Flow

```
graph LR
    USER["User Request"] --> TRACE["Trace Start"]
    TRACE --> R1["Run: Router<br/>50ms"]
    R1 --> R2["Run: Orchestrator<br/>800ms"]
    R2 --> R3["Run: Specialist A<br/>1200ms"]
    R2 --> R4["Run: Specialist B<br/>900ms"]
    R3 --> R5["Run: Tool Call<br/>200ms"]
    R4 --> R6["Run: Synthesis<br/>600ms"]
    R6 --> END["Trace End<br/>Total: 3.2s"]

    style TRACE fill:#6366f1,color:#fff
    style END fill:#10b981,color:#000
    style R5 fill:#f59e0b,color:#000
```
