# Model Choosing Module

Comprehensive model selection engine for agentic systems. Three sub-modules:
Benchmark Comparator, Model-per-Agent Optimizer, and Provider Risk Analysis.

---

## 1. Benchmark Comparator

### Agent-Specific Benchmarks (2025-2026)

| Benchmark | Focus | Top Performers | Status |
|-----------|-------|---------------|--------|
| BFCL V4 Agentic | Tool use, function calling | Top LLMs >85% single-turn | De facto standard |
| SWE-Bench Verified | Software engineering | Claude Opus 4.6: 80.8%, Gemini 3.1 Pro: 80.6% | Production benchmark |
| WebArena | Autonomous web agents | ~60% success rate (up from 14% in 2023) | Active development |
| TAU-Bench | Long-horizon workflows | Sierra benchmark | Tool-enabled conversations |
| Context-Bench | Long-running context | Letta (Oct 2025) | File ops, decision consistency |
| AgentBench | Multi-domain agent tasks | Varies by domain | 8 distinct environments |
| GAIA | General AI assistants | Multi-step reasoning + tools | Real-world question answering |

### Reasoning Benchmarks

| Benchmark | Content | Saturation Level | Best For |
|-----------|---------|------------------|----------|
| MMLU | 15,908 multi-choice (57 subjects) | Saturated (>90%) | Baseline capability |
| GPQA Diamond | 448 expert questions | Active (Gemini 3.1 Pro: 94.3%) | Deep domain reasoning |
| ARC-AGI-2 | Abstract reasoning | Active (77.1% best) | Novel problem solving |
| HLE | 2,500 expert questions (100+ subjects) | Active | Frontier knowledge |

### Coding Benchmarks

| Benchmark | Scope | 2025 Status | Notes |
|-----------|-------|-------------|-------|
| HumanEval | 164 problems | Saturated (>95%) | Single-function |
| SWE-Bench | Real GitHub issues | 71.7% solved | End-to-end codebase |
| RE-Bench | Complex agentic tasks | Active | Rigorous evaluation |

### How to Use This Module

When an engineer describes their use case, identify the PRIMARY capability needed:

```
IF agent needs tool use → prioritize BFCL scores
IF agent does code generation → prioritize SWE-Bench scores
IF agent needs deep reasoning → prioritize GPQA/ARC scores
IF agent is long-running autonomous → prioritize WebArena/Context-Bench
IF agent needs multi-step planning → prioritize GAIA/AgentBench
```

Always verify with WebSearch for the latest scores — benchmarks update monthly.

---

## 2. Model-per-Agent Optimizer

### Role-Based Model Assignment Matrix

| Agent Role | Complexity | Recommended Model | Latency SLA | Volume |
|------------|-----------|-------------------|-------------|--------|
| Strategic Orchestrator | High | Claude Opus 4.6 / GPT-5.4 | <5s | Low (1-3% of calls) |
| Domain Supervisor | Medium-High | Claude Sonnet 4.6 / GPT-4o | <3s | Medium (10-20%) |
| Specialist Executor | Medium | Claude Sonnet 4.6 / Gemini Flash | <2s | Medium (30-40%) |
| Classifier/Router | Low | Claude Haiku 4.5 / GPT-4o-mini | <500ms | High (20-30%) |
| Data Extractor | Low-Medium | Claude Haiku 4.5 | <1s | High (15-25%) |
| Code Generator | High | Claude Opus 4.6 (80.8% SWE-bench) | <10s | Low |
| Summarizer | Medium | Claude Sonnet 4.6 | <2s | Medium |

### Architecture Template: Hierarchical Cost Optimization

```
Strategic Coordinator (Opus 4.6) — 5% of calls
  |
  +-- Domain Supervisor A (Sonnet 4.6) — 15% of calls
  |     +-- Worker A1 (Haiku 4.5) — 25% of calls
  |     +-- Worker A2 (Haiku 4.5) — 25% of calls
  |
  +-- Domain Supervisor B (Sonnet 4.6) — 10% of calls
        +-- Worker B1 (Haiku 4.5) — 20% of calls
```

**Result**: 40% cost savings vs all-Opus baseline with <2% quality degradation.

### Model Assignment Decision Tree

```
FOR each agent in the system:
  1. Classify task complexity: Low / Medium / High
  2. Check latency requirement: <500ms / <2s / <5s / relaxed
  3. Check volume: High (>1000/day) / Medium / Low
  4. Check accuracy requirement: Critical (>99%) / Standard (>95%) / Flexible

  IF complexity=High AND accuracy=Critical → Opus/GPT-5.4
  IF complexity=Medium AND volume=High → Sonnet with batch processing
  IF complexity=Low AND volume=High → Haiku/GPT-4o-mini
  IF latency<500ms → Haiku or Groq-hosted Llama
  IF budget constrained → Route 70% Haiku, 25% Sonnet, 5% Opus
```

### Intelligent Model Routing

**30% Cost Reduction Blueprint:**
- Route 60-70% of requests to Haiku 4.5
- Route 25-35% to Sonnet 4.6
- Reserve 5-10% for Opus 4.6 (complex escalations)
- Routing overhead: 1-2% latency, ~$0.001 per routing decision
- Accuracy: 95%+ routing precision achievable with simple classifier

**Implementation Pattern:**
```python
# Routing classifier (runs on Haiku)
def route_request(request):
    complexity = classify_complexity(request)  # Haiku call
    if complexity > 0.8:
        return "opus"
    elif complexity > 0.4:
        return "sonnet"
    else:
        return "haiku"
```

---

## 3. Provider Risk Analysis

### Current API Pricing (2026, verify with WebSearch)

#### Proprietary Models per 1M Tokens

| Provider | Model | Input | Output | Context | Batch Discount |
|----------|-------|-------|--------|---------|---------------|
| Anthropic | Opus 4.6 | $5.00 | $25.00 | 1M | 50% off |
| Anthropic | Sonnet 4.6 | $3.00 | $15.00 | 1M | 50% off |
| Anthropic | Haiku 4.5 | $1.00 | $5.00 | 200k | 50% off |
| OpenAI | GPT-4o | $2.50 | $10.00 | 128k | 50% off |
| OpenAI | GPT-4o-mini | $0.15 | $0.60 | 128k | 50% off |
| OpenAI | o1 | $10.00 | $70.00 | 128k | — |
| OpenAI | o3-mini | $0.55 | $2.20 | 128k | 50% off |
| Google | Gemini 2.5 Pro | $4.00 | $20.00 | 2M | — |
| Google | Gemini 2.5 Flash | $0.30 | $2.50 | 1M | — |

#### Prompt Caching (90% discount on cached input)

| Provider | Model | Cached Input | Break-even |
|----------|-------|-------------|------------|
| Anthropic | Opus 4.6 | $0.50/M | 2-3 requests |
| Anthropic | Sonnet 4.6 | $0.30/M | 2-3 requests |
| Anthropic | Haiku 4.5 | $0.10/M | 2-3 requests |

#### Open Source Providers

| Provider | Speed | Pricing | Best For |
|----------|-------|---------|----------|
| Groq | 2.6x faster | $0.29-0.59/M | Real-time agents, low latency |
| Fireworks | Standard | $0.20-0.60/M | Predictable workloads |
| Together AI | Flexible | $0.20-0.80/M | Multi-model strategies |
| Self-hosted | Variable | GPU cost only | Full control, compliance |

### Provider Capability Matrix

| Capability | Anthropic | OpenAI | Google | Groq | Together |
|-----------|-----------|--------|--------|------|----------|
| Native Tool Use | Yes | Yes | Yes | Compatible | Compatible |
| Parallel Tool Calls | Yes | Yes | Yes | Yes | Yes |
| Structured Output | Yes | Yes (JSON mode) | Yes | Supported | Supported |
| MCP Support | Native | — | Planned | — | — |
| Streaming | SSE | SSE | SSE | SSE | SSE |
| TTFT Latency | 150-250ms | 100-150ms | 200-300ms | 50-100ms | 100-200ms |
| EU Data Residency | Available | Available | Available | — | — |
| SOC 2 Type II | Yes | Yes | Yes | Yes | — |
| HIPAA Eligible | Yes | Yes | Yes (FedRAMP) | — | — |

### Vendor Lock-in Risk Assessment

| Risk Level | Pattern | Mitigation |
|-----------|---------|------------|
| HIGH | Single-provider, proprietary formats, fine-tuned models | Avoid for critical paths |
| MEDIUM | Multi-provider with standardized interfaces | Acceptable with fallbacks |
| LOW | MCP-based tool abstraction + open source fallback | Recommended |

### Multi-Provider Fallback Chain (99.95% Uptime)

```
Primary: Claude Opus 4.6
  | timeout >5s OR rate limit OR downtime
  v
Secondary: GPT-4o (different provider)
  | timeout >5s OR rate limit OR downtime
  v
Tertiary: Gemini 2.5 Pro (third provider)
  | timeout >5s OR rate limit OR downtime
  v
Emergency: Self-hosted Llama 70B (no external dependency)
```

### Provider Selection Decision Tree

```
IF compliance critical (HIPAA/SOC2) → Anthropic or OpenAI (with BAA)
IF EU data residency required → Anthropic EU or Mistral
IF lowest latency needed → Groq
IF largest context window → Google Gemini (2M tokens)
IF full control needed → Self-hosted open source
IF MCP ecosystem → Anthropic (native support)
IF cost minimized → Haiku + Groq routing
IF multi-provider resilience → 3+ provider fallback chain
```

---

## Output Format

When generating Model Choosing analysis, include in the HTML blueprint:

### Tab: Model Selection
1. **Benchmark Match** — which benchmarks matter for this case and current leaders
2. **Agent-Model Map** — table showing each agent → assigned model with justification
3. **Cost Projection** — monthly estimate at stated volume (see cost-simulator.md)
4. **Provider Strategy** — primary + fallback chain with risk analysis
5. **Optimization Tips** — batch processing, caching, routing opportunities

### Mermaid Diagram: Model Assignment

```
graph LR
    USER["User Request"] --> ROUTER["Model Router<br/>Haiku 4.5"]
    ROUTER -->|complex| OPUS["Orchestrator<br/>Opus 4.6"]
    ROUTER -->|standard| SONNET["Specialist<br/>Sonnet 4.6"]
    ROUTER -->|simple| HAIKU["Classifier<br/>Haiku 4.5"]
    
    style ROUTER fill:#f59e0b,color:#000
    style OPUS fill:#6366f1,color:#fff
    style SONNET fill:#06b6d4,color:#000
    style HAIKU fill:#10b981,color:#000
```
