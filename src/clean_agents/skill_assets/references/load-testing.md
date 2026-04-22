# Load Testing Planner Module

Design load testing scenarios for agentic systems:
concurrent users, token throughput, rate limits, graceful degradation.

---

## 1. Why LLM Load Testing is Different

Traditional load testing measures: requests/second, response time, error rate.
Agent load testing additionally measures: **token throughput, TTFT, ITL, cost under load,
and quality degradation** — because LLM performance degrades non-linearly under load.

### Key Differences

| Traditional API | Agent System |
|----------------|-------------|
| Response time is predictable | Response time varies 10-100x based on output length |
| Cost is fixed per request | Cost scales with tokens (varies per request) |
| Quality doesn't change under load | Quality CAN degrade under load (rate limits → fallback models) |
| Scale horizontally is straightforward | LLM providers have hard rate limits |
| Error modes are well-understood | New error modes: token limit, context overflow, rate limit |

---

## 2. Key Metrics for Agent Load Testing

### Performance Metrics

| Metric | Definition | Target | Critical |
|--------|-----------|--------|----------|
| TTFT (Time to First Token) | Request → first token | <500ms | >2s |
| ITL (Inter-Token Latency) | Between consecutive tokens | <50ms | >200ms |
| E2E Latency p50 | Median total time | <3s | >10s |
| E2E Latency p95 | 95th percentile | <8s | >20s |
| Goodput | Successful requests / total | >98% | <95% |
| Token Throughput | Tokens/second sustained | Provider-specific | Degrading |

### Cost Metrics Under Load

| Metric | Definition | Alert |
|--------|-----------|-------|
| Cost per minute | Total API spend rate | >budget/1440 |
| Cost per successful request | Including retries | >2x baseline |
| Wasted tokens | Failed requests | >5% of total tokens |
| Fallback model cost | Cost shift to cheaper models | Track % shift |

### Quality Metrics Under Load

| Metric | What Changes Under Load | How to Measure |
|--------|----------------------|----------------|
| Task completion rate | May drop if rate limited | Run eval suite at each load level |
| Response quality | May degrade with fallback models | Agent-as-Judge scoring |
| Hallucination rate | May increase under pressure | Factuality checks |
| Tool call accuracy | May fail under concurrent load | Tool success rate |

---

## 3. Load Scenarios

### Scenario 1: Ramp Up

```
Purpose: Find the breaking point
Pattern: Linear increase from 0 to max over 30 minutes
Metrics: Track when latency/error rate starts degrading

Timeline:
  0-5 min:   10 concurrent users
  5-10 min:  25 concurrent users
  10-15 min: 50 concurrent users
  15-20 min: 100 concurrent users
  20-25 min: 200 concurrent users
  25-30 min: 500 concurrent users

Success criteria:
  - Latency p95 stays <10s up to target concurrency
  - Error rate stays <5% up to target concurrency
  - Cost stays within projected budget
```

### Scenario 2: Sustained Load

```
Purpose: Verify stability at expected production volume
Pattern: Constant load for 2-4 hours
Metrics: Track for degradation over time (memory leaks, cache issues)

Configuration:
  Concurrent users: [expected production average]
  Duration: 4 hours
  Request pattern: realistic mix of simple/complex

Success criteria:
  - No latency drift (p95 stays within 10% of start)
  - No memory/resource leaks
  - Consistent error rate throughout
```

### Scenario 3: Spike

```
Purpose: Test reaction to sudden traffic burst
Pattern: Normal load → 10x spike for 5 minutes → normal

Timeline:
  0-10 min:  normal load (baseline)
  10-15 min: 10x normal load (spike)
  15-25 min: normal load (recovery)

Success criteria:
  - System remains responsive during spike (degraded OK, outage NOT OK)
  - Recovery to baseline within 5 minutes of spike end
  - No data loss or corruption during spike
  - Graceful degradation activates correctly
```

### Scenario 4: Provider Failover

```
Purpose: Test fallback chain under primary provider outage
Pattern: Simulate primary provider failure during load

Timeline:
  0-5 min:   normal load, all providers healthy
  5-10 min:  primary provider returns errors
  10-15 min: verify failover to secondary
  15-20 min: primary recovers, verify return to primary

Success criteria:
  - Failover activates within 30 seconds
  - Quality degradation <10% during failover
  - Return to primary is seamless
  - No requests lost during transition
```

---

## 4. Rate Limit Management

### Provider Rate Limits (approximate, verify current)

| Provider | RPM (Requests) | TPM (Tokens) | Notes |
|----------|---------------|-------------|-------|
| Anthropic | 4,000 | 400,000 | Tier-dependent |
| OpenAI | 10,000 | 2,000,000 | Tier-dependent |
| Google | 1,000-5,000 | 4,000,000 | Model-dependent |
| Groq | 30,000 | Varies | Highest throughput |

### Rate Limit Strategies

**Strategy 1: Token Budget per Minute**
```
total_budget = provider_TPM * 0.8  # 80% safety margin
per_agent_budget = total_budget / num_agents
queue_overflow = redirect to secondary provider
```

**Strategy 2: Request Queue with Backpressure**
```
IF queue_length > threshold:
  → Reject new requests with 429 + retry-after header
  → Route overflow to secondary provider
  → Alert ops team
```

**Strategy 3: Adaptive Rate Limiting**
```
Monitor: 429 responses from provider
IF 429 count > 3 in 60s:
  → Reduce request rate by 50%
  → Gradually increase after 60s of no 429s
  → Log rate limit events for capacity planning
```

**Strategy 4: Multi-Provider Load Balancing**
```
Primary: 70% of requests → Anthropic
Secondary: 20% → OpenAI  
Tertiary: 10% → Google

IF primary rate limited:
  → Shift primary traffic to secondary
  → Rebalance when primary recovers
```

---

## 5. Graceful Degradation Under Load

### Degradation Chain

```
Level 0: Normal Operation
  → All agents use optimal models
  → Full feature set available

Level 1: Elevated Load (>70% capacity)
  → Enable prompt caching aggressively
  → Reduce max_tokens for non-critical agents
  → Batch non-urgent requests

Level 2: High Load (>85% capacity)
  → Downgrade specialist models (Opus → Sonnet → Haiku)
  → Disable optional features (detailed logging, analytics)
  → Queue non-critical requests

Level 3: Critical Load (>95% capacity)
  → Route to fallback models only
  → Simplify agent pipeline (skip optional agents)
  → Return cached responses where possible
  → Alert: capacity increase needed

Level 4: Overload
  → Reject new requests with friendly error
  → Process only in-flight requests
  → Activate emergency human escalation
```

### Testing Degradation

For each level, verify:
- [ ] Transition is smooth (no errors during switch)
- [ ] Quality metrics are acceptable at each level
- [ ] Recovery to previous level is automatic
- [ ] Users are notified of degraded service (if applicable)

---

## 6. Load Test Tool Configuration

### Locust (Python) — Recommended for Agent Systems

```python
# Token-aware load test configuration
class AgentUser(HttpUser):
    wait_time = between(1, 5)
    
    @task(7)
    def simple_request(self):
        """70% simple requests (classifier path)"""
        self.client.post("/api/agent", json={
            "message": "Classify this document",
            "complexity": "low"
        })
    
    @task(2)
    def medium_request(self):
        """20% medium requests (specialist path)"""
        self.client.post("/api/agent", json={
            "message": "Analyze this contract for risks",
            "complexity": "medium"
        })
    
    @task(1)
    def complex_request(self):
        """10% complex requests (full pipeline)"""
        self.client.post("/api/agent", json={
            "message": "Design a compliance strategy",
            "complexity": "high"
        })
```

### k6 (JavaScript) — Good for CI/CD Integration

```javascript
// Streaming-aware load test
export const options = {
    stages: [
        { duration: '5m', target: 10 },
        { duration: '10m', target: 50 },
        { duration: '5m', target: 100 },
        { duration: '5m', target: 0 },
    ],
    thresholds: {
        http_req_duration: ['p(95)<10000'],
        http_req_failed: ['rate<0.05'],
    },
};
```

---

## 7. Cost Projection Under Load

### Estimation Template

```
At [N] concurrent users, [M] requests/hour:

Per-Hour Cost:
  Simple requests (70%): M * 0.70 * $cost_simple = $X
  Medium requests (20%): M * 0.20 * $cost_medium = $Y
  Complex requests (10%): M * 0.10 * $cost_complex = $Z
  
  Subtotal: $X + $Y + $Z
  + Retries (5%): * 1.05
  + Rate limit overflow to secondary: +10-20%
  
  Total hourly: $___
  Daily (peak 8h + off-peak 16h at 30%): $___
  Monthly: $___

At 2x load (stress scenario):
  API cost: ~2.2x (some overhead from rate limiting)
  Infrastructure: ~1.5x (auto-scaling)
  Total: ~2x normal
```

---

## 8. Output in HTML Blueprint

Add a "Load Testing" tab showing:

1. **Load Profile** — expected traffic pattern (daily curve)
2. **Test Scenarios** — configured scenarios with parameters
3. **Rate Limit Strategy** — per-provider limits and management
4. **Degradation Chain** — levels and triggers
5. **Cost Projection** — at normal, peak, and stress loads
6. **Tool Config** — Locust/k6 configs ready to use

### Mermaid: Load Profile

```
graph LR
    NORMAL["Normal Load<br/>100 req/min"] -->|70% capacity| ELEVATED["Elevated<br/>Reduce tokens"]
    ELEVATED -->|85% capacity| HIGH["High Load<br/>Downgrade models"]
    HIGH -->|95% capacity| CRITICAL["Critical<br/>Fallback only"]
    CRITICAL -->|100% capacity| OVERLOAD["Overload<br/>Reject new"]

    style NORMAL fill:#10b981,color:#000
    style ELEVATED fill:#f59e0b,color:#000
    style HIGH fill:#ef4444,color:#fff
    style CRITICAL fill:#7f1d1d,color:#fff
    style OVERLOAD fill:#450a0a,color:#fff
```
