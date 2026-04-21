# Cost Simulator Module

Estimate total cost of ownership for the designed agentic system:
API costs, infrastructure, and operational overhead.

---

## 1. Cost Model Structure

### Per-Request Cost Formula

```
Cost_per_request = SUM over all agents:
  (input_tokens / 1M * input_price) +
  (output_tokens / 1M * output_price) +
  (cached_tokens / 1M * cached_price)

Plus:
  + infrastructure_cost_per_request (vector DB, compute, storage)
  + observability_cost_per_request (logging, tracing)
```

### Monthly Cost Formula

```
Monthly_cost =
  Cost_per_request * requests_per_day * 30
  + fixed_infra_monthly (hosting, DBs, monitoring)
  + human_review_cost (HITL operations * hourly_rate)
```

---

## 2. Token Estimation by Agent Role

### Typical Token Usage Patterns

| Agent Role | System Prompt | Avg Input | Avg Output | Calls/Request |
|-----------|--------------|-----------|------------|---------------|
| Orchestrator | 1500-2500 | 500-2000 | 200-800 | 1-3 |
| Specialist (ReAct) | 1000-2000 | 1000-5000 | 500-2000 | 1-5 |
| Specialist (ToT) | 1500-2500 | 2000-8000 | 1000-4000 | 2-4 |
| Classifier | 300-800 | 100-500 | 50-200 | 1 |
| Extractor | 500-1500 | 1000-10000 | 200-1000 | 1-2 |
| Guardian | 500-1000 | 100-2000 | 50-200 | 1-2 |
| Summarizer | 800-1500 | 2000-50000 | 500-2000 | 1 |

### Multiplier by Architecture Pattern

| Pattern | Token Multiplier vs Single Agent | Reason |
|---------|--------------------------------|--------|
| Single Agent | 1x | Baseline |
| Pipeline (2-3 steps) | 2-3x | Sequential processing |
| Supervisor Hierarchical | 3-5x | Orchestration overhead + specialists |
| Blackboard/Swarm | 4-7x | Multiple agents + consensus |
| Hybrid Hierarchical-Swarm | 5-10x | Most complex architecture |

### RAG/GraphRAG Additional Costs

| Component | Token Impact | Infrastructure |
|-----------|-------------|---------------|
| Vanilla RAG retrieval | +500-2000 tokens/query (context) | Vector DB hosting |
| GraphRAG retrieval | +1000-5000 tokens/query (richer context) | Graph DB + Vector DB |
| Document embedding | One-time: ~1 token per word of corpus | Embedding API calls |
| Re-ranking | +100-500 tokens/query | Re-ranker model calls |

---

## 3. Cost Calculation Templates

### Template A: Simple Agent (single agent + tools)

```
Per request:
  System prompt: ~1500 tokens (cached after first request)
  User input: ~500 tokens
  Tool calls: 2 avg * 300 tokens each = 600 tokens
  Response: ~800 tokens

  First request: (1500+500+600)/1M * input_price + 800/1M * output_price
  Cached request: (1500*0.1+500+600)/1M * input_price + 800/1M * output_price

  With Sonnet 4.6: $0.0048 first / $0.0036 cached
  With Haiku 4.5: $0.0016 first / $0.0010 cached
```

### Template B: Multi-Agent System (supervisor + 3 specialists)

```
Per request:
  Orchestrator (Opus): 2000+1000 in, 500 out = $0.0275
  Specialist 1 (Sonnet): 1500+2000 in, 1000 out = $0.0255
  Specialist 2 (Sonnet): 1500+2000 in, 1000 out = $0.0255
  Specialist 3 (Haiku): 800+1000 in, 500 out = $0.0043
  Guardian (Haiku): 500+500 in, 100 out = $0.0015

  Total per request: ~$0.084
  With caching (after warmup): ~$0.058 (31% savings)
  With model routing (70% skip orchestrator): ~$0.042 (50% savings)

  At 1000 requests/day: ~$1,260/month (optimized)
```

### Template C: Enterprise Complex System

```
Per request (hybrid hierarchical-swarm):
  Strategic Orchestrator (Opus): $0.035
  2x Domain Supervisors (Sonnet): $0.05
  4x Workers (Haiku): $0.008
  2x Guardians (Haiku): $0.003
  GraphRAG retrieval: $0.005
  Observability overhead: $0.002

  Total per request: ~$0.103
  Optimized (caching + routing): ~$0.065

  At 10,000 requests/day: ~$19,500/month
  Infrastructure add-on: ~$3,000-5,000/month
  HITL (5% of requests): ~$2,000-5,000/month (at $25/hr)
```

---

## 4. Infrastructure Cost Components

### Vector Database

| Service | Free Tier | Production | Notes |
|---------|-----------|------------|-------|
| Pinecone | 100k vectors | $70-350/month | Managed, serverless |
| Weaviate Cloud | 1M objects | $100-500/month | Hybrid search |
| Qdrant Cloud | 1GB | $50-200/month | Open source option |
| Supabase pgvector | 500MB | $25-100/month | Integrated with Postgres |
| Self-hosted | — | $50-200/month (compute) | Full control |

### Graph Database (for GraphRAG)

| Service | Free Tier | Production | Notes |
|---------|-----------|------------|-------|
| Neo4j AuraDB | 50k nodes | $200-1000/month | Enterprise features |
| Amazon Neptune | — | $300-1500/month | AWS integrated |
| Self-hosted Neo4j | — | $100-400/month (compute) | Community edition free |

### Compute & Hosting

| Component | Cost Range | Notes |
|-----------|-----------|-------|
| Agent API server | $50-200/month | Serverless or container |
| Redis (caching) | $15-100/month | Session state, rate limiting |
| Message queue | $20-100/month | Agent communication |
| Logging/storage | $10-50/month | Trace data retention |

### Observability

| Platform | Free Tier | Production |
|----------|-----------|------------|
| LangSmith | 5k traces/month | $39-499/month |
| Langfuse | 50k observations | Self-hosted or $59+/month |
| Helicone | 10k requests | $30-150/month |
| Phoenix (Arize) | Open source | Self-hosted cost only |

---

## 5. Cost Optimization Strategies

### Strategy 1: Model Routing (30-50% savings)
Route simple requests to cheap models, complex to expensive.
See model-choosing.md for implementation details.

### Strategy 2: Prompt Caching (20-40% savings)
Cache system prompts across requests. Break-even at 2-3 reuses.
Most effective for: long system prompts, repeated context, code repos.

### Strategy 3: Batch Processing (50% savings on eligible work)
Batch API available on all major providers. 24-hour latency.
Best for: document processing, bulk extraction, non-real-time analysis.

### Strategy 4: Token Budget Enforcement
Set max_tokens per agent. Prevents runaway costs.
```
Orchestrator: 1000 max output
Specialist: 2000 max output
Classifier: 200 max output
```

### Strategy 5: Early Exit
If classifier routes to "simple" path, skip expensive agents.
Saves 40-60% on requests that don't need full pipeline.

---

## 6. Output Format

### Cost Dashboard in HTML Blueprint

Add a "Cost Simulator" tab showing:

1. **Per-Request Breakdown** — table with each agent, model, tokens, cost
2. **Monthly Projection** — at stated volume, with 3 scenarios:
   - Pessimistic (no optimization): raw costs
   - Realistic (caching + routing): 30% reduction
   - Optimistic (full optimization): 50% reduction
3. **Provider Comparison** — same system on different providers
4. **Cost-Quality Tradeoff** — what you lose at each optimization level
5. **Infrastructure Total** — fixed monthly costs breakdown

### Mermaid Diagram: Cost Flow

```
graph LR
    REQ["1000 req/day"] --> ROUTE["Router<br/>$0.001/req"]
    ROUTE -->|70%| CHEAP["Haiku Path<br/>$0.002/req"]
    ROUTE -->|25%| MID["Sonnet Path<br/>$0.025/req"]
    ROUTE -->|5%| FULL["Opus Path<br/>$0.084/req"]
    CHEAP --> TOTAL["Monthly Total<br/>$1,260"]
    MID --> TOTAL
    FULL --> TOTAL

    style TOTAL fill:#10b981,color:#000
    style CHEAP fill:#06b6d4,color:#000
    style FULL fill:#ef4444,color:#fff
```
