# CLean-agents CLI Specification

> Framework CLI for designing, hardening, and operating production-grade agentic AI systems.

```
pip install clean-agents
```

---

## Command Overview

```
clean-agents
├── init              # Initialize a new project
├── design            # Interactive architecture design session
├── blueprint         # Generate/update HTML blueprint from config
├── prompt            # Generate system prompts for all agents
├── model             # Model selection & assignment
├── cost              # Cost simulation & projection
├── eval              # Evaluation suite management
│   ├── generate      # Auto-generate test cases
│   ├── run           # Execute eval suite
│   └── report        # Generate eval report
├── shield            # Security testing
│   ├── scan          # Static analysis of blueprint
│   ├── attack        # Live red team against running agents
│   └── report        # Security dashboard
├── observe           # Observability setup
│   ├── init          # Generate tracing/metrics configs
│   ├── dashboard     # Generate dashboard configs
│   └── alerts        # Generate alerting rules
├── migrate           # Migration advisor
│   ├── analyze       # Analyze current system
│   ├── plan          # Generate migration plan
│   └── track         # Track migration progress
├── comply            # Compliance mapper
│   ├── scan          # Identify applicable regulations
│   ├── gaps          # Run gap analysis
│   └── report        # Generate compliance report
├── load              # Load testing
│   ├── plan          # Generate load test scenarios
│   ├── config        # Generate Locust/k6 configs
│   └── project       # Project costs under load
├── scaffold          # Generate runnable code from blueprint
├── export            # Export blueprint/configs to various formats
├── serve             # Start as API/MCP server
└── doctor            # Check environment & dependencies
```

---

## Core Data Model

All commands operate on a `.clean-agents/` project directory:

```
my-agent-project/
├── .clean-agents/
│   ├── config.yaml           # Project configuration
│   ├── blueprint.yaml        # System architecture definition (source of truth)
│   ├── agents/               # Per-agent configurations
│   │   ├── orchestrator.yaml
│   │   ├── doc_analyzer.yaml
│   │   └── risk_evaluator.yaml
│   ├── prompts/              # Generated system prompts
│   │   ├── orchestrator.md
│   │   ├── doc_analyzer.md
│   │   └── risk_evaluator.md
│   ├── evals/                # Evaluation suite
│   │   ├── config.yaml
│   │   ├── test_cases/
│   │   ├── rubrics/
│   │   ├── baselines/
│   │   └── reports/
│   ├── security/             # Security testing results
│   │   ├── scan_results.yaml
│   │   ├── attack_log.yaml
│   │   └── reports/
│   ├── compliance/           # Compliance mappings
│   │   ├── applicable.yaml
│   │   ├── gaps.yaml
│   │   └── reports/
│   ├── observability/        # Generated configs
│   │   ├── tracing.yaml
│   │   ├── dashboards/
│   │   └── alerts.yaml
│   ├── load/                 # Load testing configs
│   │   ├── scenarios.yaml
│   │   ├── locustfile.py
│   │   └── k6_script.js
│   ├── migrations/           # Migration tracking
│   │   ├── plan.yaml
│   │   └── progress.yaml
│   └── history/              # Design iteration history
│       ├── v1.yaml
│       └── changelog.md
├── src/                      # Generated code scaffold
│   ├── agents/
│   ├── memory/
│   ├── guardrails/
│   ├── tools/
│   ├── observability/
│   └── tests/
├── outputs/                  # Generated artifacts
│   ├── blueprint.html
│   ├── security_dashboard.html
│   └── compliance_report.html
└── clean-agents.yaml         # Root config (points to .clean-agents/)
```

### Blueprint YAML (source of truth)

```yaml
# .clean-agents/blueprint.yaml
version: "1.0"
name: "contract-analysis-system"
description: "Multi-agent system for legal contract analysis with SOX compliance"
language: "es"  # UI language

system:
  type: "multi-agent"              # single-agent | pipeline | multi-agent | complex
  pattern: "supervisor-hierarchical"
  domain: "legal"
  scale: "medium"                   # small (<100/day) | medium | large (>10k/day) | enterprise
  autonomy: "L3"                    # L1-L4

agents:
  orchestrator:
    role: "Plan decomposition, task routing, result synthesis"
    model:
      primary: "claude-opus-4-6"
      fallback: "gpt-5-4"
    reasoning: "htl-planning"
    tools: ["route_to_agent", "synthesize_results"]
    memory:
      short_term: true
      episodic: false
      semantic: false
      graphrag: false
    guardrails:
      input: ["injection_detection", "encoding_detection"]
      output: ["schema_validation", "pii_masking"]
    hitl: "pre-action"              # none | pre-action | post-action | tool-level
    token_budget: 2000
    metrics:
      routing_accuracy: 0.95
      recovery_rate: 0.80

  doc_analyzer:
    role: "Extract clauses, risks, and obligations from legal documents"
    model:
      primary: "claude-sonnet-4-6"
      fallback: "claude-haiku-4-5"
    reasoning: "react"
    tools: ["read_document", "search_knowledge_base", "extract_clauses"]
    memory:
      short_term: true
      graphrag: true
    guardrails:
      input: ["size_limit"]
      output: ["schema_validation", "confidence_threshold"]
    hitl: "none"
    token_budget: 4000
    metrics:
      extraction_accuracy: 0.92
      hallucination_rate: 0.03

infrastructure:
  vector_db: "pinecone"
  graph_db: "neo4j"
  message_queue: "redis"
  observability: "langfuse"

compliance:
  regulations: ["gdpr", "eu-ai-act", "sox"]
  data_residency: "eu"
  audit_trail: true

cost:
  budget_monthly: 5000
  optimization:
    routing: true
    caching: true
    batch: false

timeline:
  start: "2026-05-01"
  target_mvp: "2026-06-15"
  target_prod: "2026-08-01"
```

---

## Command Details

### `clean-agents init`

Initialize a new CLean-agents project.

```bash
clean-agents init [project-name] [options]

Options:
  --template <name>     Start from a template (legal, support, coding, research, custom)
  --interactive         Guided wizard (default if no template)
  --from-existing       Analyze existing codebase and generate blueprint
  --language <lang>     Output language (en, es, pt, fr, de) [default: en]
  --llm <provider>      LLM for design session (anthropic, openai) [default: anthropic]
  --api-key <key>       API key (or set ANTHROPIC_API_KEY / OPENAI_API_KEY env var)

Examples:
  clean-agents init my-legal-system --template legal --language es
  clean-agents init --interactive
  clean-agents init --from-existing ./src
```

**Interactive mode flow:**
```
$ clean-agents init --interactive

  CLean-agents v1.0 — Agentic Architecture Consultant

  Tell me what you want to build (natural language):
  > Necesito un sistema para analizar contratos legales, extraer
    cláusulas de riesgo, y generar reportes con aprobación humana.

  ⠋ Researching architecture patterns for legal document analysis...
  ⠋ Checking latest benchmarks and framework updates...

  ┌─ RECOMMENDATION ──────────────────────────────────────────────┐
  │                                                               │
  │  Architecture: Supervisor Hierarchical                        │
  │  Agents: 3 (Orchestrator + Doc Analyzer + Risk Evaluator)     │
  │  Framework: LangGraph (complex state + cycles)                │
  │  Memory: GraphRAG (relationship-aware retrieval)              │
  │                                                               │
  │  Evidence: "Hierarchical MAS shows 34% fewer coordination     │
  │  errors in compliance-heavy workflows" (ArXiv 2508.12683)     │
  │                                                               │
  └───────────────────────────────────────────────────────────────┘

  Accept this recommendation? [Y/n/modify]:
```

---

### `clean-agents design`

Interactive design session — the core experience. Runs the full 5-phase flow.

```bash
clean-agents design [options]

Options:
  --resume              Resume previous design session
  --phase <N>           Jump to specific phase (0-4)
  --research            Force live research (WebSearch) even if cached
  --no-research         Skip live research, use embedded knowledge only
  --output <dir>        Output directory for artifacts [default: ./outputs]
  --format <fmt>        Output format: html, yaml, json, all [default: all]

Examples:
  clean-agents design                    # Start new session
  clean-agents design --resume           # Continue from last checkpoint
  clean-agents design --phase 3          # Jump to blueprint generation
```

**Session persistence:**
Every design decision is saved to `.clean-agents/history/`. The engineer can:
- Resume after closing terminal
- Branch: "save this state, try a different approach"
- Compare: "diff this blueprint against v2"

---

### `clean-agents blueprint`

Generate or update the HTML blueprint from the current config.

```bash
clean-agents blueprint [options]

Options:
  --open                Open in browser after generating
  --watch               Regenerate on config changes (dev mode)
  --sections <list>     Only generate specific sections (comma-separated)
                        Options: overview, agents, flow, plan, security, cost,
                                 models, prompts, eval, observability, compliance, load
  --diff <version>      Show diff against a previous version
  --export-pdf          Also export as PDF

Examples:
  clean-agents blueprint --open
  clean-agents blueprint --sections overview,agents,security --open
  clean-agents blueprint --diff v1
```

---

### `clean-agents prompt`

Generate optimized system prompts for every agent.

```bash
clean-agents prompt [options]

Options:
  --agent <name>        Generate for specific agent only
  --format <fmt>        Output: markdown, json, python, typescript [default: markdown]
  --include-examples    Add few-shot examples to prompts
  --optimize            Run prompt optimization (requires eval suite)
  --dry-run             Show prompts without saving

Examples:
  clean-agents prompt                              # All agents
  clean-agents prompt --agent orchestrator         # Single agent
  clean-agents prompt --format python              # Python string format
  clean-agents prompt --optimize                   # DSPy-style optimization
```

**Output in Python format:**
```python
# .clean-agents/prompts/orchestrator.py
SYSTEM_PROMPT = """You are the Orchestrator of the contract-analysis-system...

## Available Agents
- **doc_analyzer**: Extract clauses and risks. Use when: document input received.
- **risk_evaluator**: Score and categorize risks. Use when: clauses extracted.

## Routing Rules
IF document_input → delegate to doc_analyzer
IF clauses_ready → delegate to risk_evaluator
IF confidence < 0.7 → escalate to human

## Constraints
- Token budget: 2000 max output
- Never execute tasks yourself — always delegate
"""
```

---

### `clean-agents model`

Model selection, assignment, and provider analysis.

```bash
clean-agents model [subcommand] [options]

Subcommands:
  benchmark             Compare models on relevant benchmarks
  assign                Optimize model assignment per agent
  providers             Provider risk analysis & fallback chain
  cost                  Cost comparison across providers

Options:
  --agent <name>        Focus on specific agent
  --budget <usd>        Monthly budget constraint
  --latency <ms>        Max latency constraint
  --compliance <reg>    Filter by compliance (hipaa, gdpr, soc2)

Examples:
  clean-agents model benchmark                   # Show relevant benchmarks
  clean-agents model assign --budget 2000        # Optimize within budget
  clean-agents model providers --compliance gdpr # EU-compliant providers
  clean-agents model cost                        # Full cost comparison
```

---

### `clean-agents cost`

Cost simulation and projection.

```bash
clean-agents cost [options]

Options:
  --volume <N>          Requests per day [default: from blueprint]
  --scenario <name>     Scenario: optimistic, realistic, pessimistic
  --compare             Compare current vs optimized
  --monthly             Show monthly projection
  --breakdown           Show per-agent breakdown
  --provider <name>     Compare specific provider

Examples:
  clean-agents cost                              # Current projection
  clean-agents cost --volume 5000 --monthly      # At 5k/day
  clean-agents cost --compare                    # Current vs optimized
  clean-agents cost --scenario pessimistic       # Worst case
```

**Output:**
```
  ┌─ COST PROJECTION ─────────────────────────────────────────────┐
  │                                                               │
  │  Per Request                                                  │
  │  ├── Orchestrator (Opus)      $0.028   ████████░░  33%       │
  │  ├── Doc Analyzer (Sonnet)    $0.026   ████████░░  31%       │
  │  ├── Risk Evaluator (Sonnet)  $0.026   ████████░░  31%       │
  │  ├── Guardian (Haiku)         $0.002   ░░░░░░░░░░   2%       │
  │  └── GraphRAG retrieval       $0.003   ░░░░░░░░░░   3%       │
  │  Total: $0.085/request                                        │
  │                                                               │
  │  Monthly @ 1000 req/day                                       │
  │  ├── API costs:        $2,550                                 │
  │  ├── Infrastructure:   $470                                   │
  │  ├── Observability:    $59                                    │
  │  └── Total:            $3,079/month                           │
  │                                                               │
  │  With Optimization (routing + caching):                       │
  │  └── Total:            $1,847/month  (-40%)                   │
  │                                                               │
  └───────────────────────────────────────────────────────────────┘
```

---

### `clean-agents eval`

Evaluation suite management.

```bash
clean-agents eval generate [options]
  --agent <name>        Generate for specific agent only
  --count <N>           Test cases per category [default: 5]
  --categories <list>   happy_path, edge_case, adversarial, regression
  --from-logs           Generate from production logs

clean-agents eval run [options]
  --suite <path>        Specific test suite [default: all]
  --agent <name>        Test specific agent only
  --runs <N>            Runs per test case [default: 50]
  --judge <model>       Judge model [default: claude-opus-4-6]
  --parallel <N>        Concurrent evaluations [default: 5]
  --baseline            Save as baseline for regression
  --compare <version>   Compare against baseline version

clean-agents eval report [options]
  --format <fmt>        html, json, markdown [default: html]
  --open                Open report in browser
  --ci                  CI-friendly output (exit code 1 if below threshold)

Examples:
  clean-agents eval generate --count 10
  clean-agents eval run --runs 100 --compare v1
  clean-agents eval run --ci                      # For CI/CD pipeline
  clean-agents eval report --open
```

**CI/CD integration:**
```yaml
# .github/workflows/eval.yml
- name: Run agent evals
  run: |
    clean-agents eval run --runs 50 --ci
    # Exit code 1 if task_completion_rate < 0.90 or error_rate > 0.05
```

---

### `clean-agents shield`

Security testing — static analysis and live red teaming.

```bash
clean-agents shield scan [options]
  --severity <level>    Minimum severity: low, medium, high, critical [default: low]
  --category <list>     Specific categories (injection, context, tool_abuse,
                        data_leakage, escalation, dos, supply_chain)
  --fix                 Auto-generate fixes for findings

clean-agents shield attack [options]
  --target <url>        Agent API endpoint
  --category <list>     Attack categories to test
  --intensity <level>   light (5 min), medium (15 min), heavy (60 min) [default: medium]
  --model <name>        Attacker model [default: claude-sonnet-4-6]
  --budget <usd>        Max spend on attack testing [default: 5.00]
  --garak               Use Garak framework for attacks
  --pyrit               Use PyRIT framework for attacks

clean-agents shield report [options]
  --format <fmt>        html, json, sarif [default: html]
  --open                Open dashboard in browser
  --ci                  CI-friendly (exit code 1 if critical findings)

Examples:
  clean-agents shield scan --fix                  # Static + auto-fix
  clean-agents shield attack --target http://localhost:8000 --intensity heavy
  clean-agents shield report --open
  clean-agents shield scan --ci                   # For CI/CD
```

**SARIF output** for GitHub Code Scanning integration:
```bash
clean-agents shield scan --format sarif > results.sarif
# Upload to GitHub Security tab
```

---

### `clean-agents observe`

Observability setup and configuration generation.

```bash
clean-agents observe init [options]
  --platform <name>     langsmith, langfuse, phoenix, helicone, otel [default: from blueprint]
  --self-host           Generate Docker Compose for self-hosted
  --framework <name>    Agent framework (langgraph, crewai, claude-sdk, custom)

clean-agents observe dashboard [options]
  --template <name>     overview, agent-detail, cost, quality [default: overview]
  --export <fmt>        grafana-json, datadog-json, html [default: html]

clean-agents observe alerts [options]
  --export <fmt>        prometheus, pagerduty, opsgenie, yaml [default: yaml]
  --sensitivity <level> low, medium, high [default: medium]

Examples:
  clean-agents observe init --platform langfuse --self-host
  clean-agents observe dashboard --template overview --open
  clean-agents observe alerts --export prometheus
```

---

### `clean-agents migrate`

Migration advisor — analyze, plan, and track.

```bash
clean-agents migrate analyze [options]
  --source <path>       Path to existing agent codebase
  --framework <name>    Current framework (if not auto-detected)
  --target <name>       Target framework

clean-agents migrate plan [options]
  --strategy <name>     strangler-fig, big-bang, parallel [default: strangler-fig]
  --timeline <weeks>    Target timeline in weeks

clean-agents migrate track [options]
  --update              Update progress interactively
  --status              Show current status

Examples:
  clean-agents migrate analyze --source ./old-agents --target langgraph
  clean-agents migrate plan --strategy strangler-fig --timeline 12
  clean-agents migrate track --status
```

---

### `clean-agents comply`

Compliance mapper — identify, analyze, report.

```bash
clean-agents comply scan [options]
  --regulations <list>  Specific regulations (gdpr, eu-ai-act, hipaa, sox, soc2,
                        finra, aba) [default: auto-detect from blueprint]
  --domain <name>       Override domain detection

clean-agents comply gaps [options]
  --regulation <name>   Focus on specific regulation
  --priority <level>    Filter by: critical, high, medium, low
  --effort              Include remediation effort estimates

clean-agents comply report [options]
  --format <fmt>        html, pdf, docx, json [default: html]
  --open                Open in browser
  --auditor             Generate auditor-ready format
  --deadline            Highlight items by compliance deadline

Examples:
  clean-agents comply scan
  clean-agents comply gaps --priority critical --effort
  clean-agents comply report --format pdf --auditor
```

---

### `clean-agents load`

Load testing planner.

```bash
clean-agents load plan [options]
  --target-rps <N>      Target requests per second
  --scenarios <list>    ramp, sustained, spike, failover [default: all]
  --duration <min>      Test duration per scenario [default: 30]

clean-agents load config [options]
  --tool <name>         locust, k6 [default: locust]
  --output <path>       Config file path

clean-agents load project [options]
  --volume <N>          Requests per day
  --growth <pct>        Monthly growth percentage [default: 20]
  --months <N>          Projection horizon [default: 12]

Examples:
  clean-agents load plan --target-rps 50
  clean-agents load config --tool k6
  clean-agents load project --volume 10000 --growth 30 --months 12
```

---

### `clean-agents scaffold`

Generate runnable code from blueprint.

```bash
clean-agents scaffold [options]

Options:
  --framework <name>    Override framework from blueprint
  --complete            Generate full implementation (not just stubs)
  --tests               Include unit tests
  --docker              Include Dockerfile + docker-compose.yml
  --ci <platform>       CI config: github-actions, gitlab-ci, circleci
  --output <dir>        Output directory [default: ./src]

Examples:
  clean-agents scaffold                              # Stubs from blueprint
  clean-agents scaffold --complete --tests --docker  # Full implementation
  clean-agents scaffold --ci github-actions          # With CI config
```

**Output structure:**
```
src/
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py         # Full agent implementation
│   ├── doc_analyzer.py
│   └── risk_evaluator.py
├── memory/
│   ├── graphrag.py             # GraphRAG setup + queries
│   └── short_term.py
├── guardrails/
│   ├── input_filters.py        # Injection, encoding, PII detection
│   ├── output_validators.py    # Schema, confidence, safety
│   └── circuit_breaker.py
├── tools/
│   ├── document_tools.py       # MCP tool definitions
│   └── knowledge_base.py
├── observability/
│   ├── tracer.py               # OTEL / Langfuse instrumentation
│   └── metrics.py
├── tests/
│   ├── test_orchestrator.py
│   ├── test_doc_analyzer.py
│   └── conftest.py
├── config.yaml
├── main.py                     # Entrypoint
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .github/
    └── workflows/
        ├── test.yml
        └── eval.yml
```

---

### `clean-agents export`

Export artifacts to various formats.

```bash
clean-agents export [options]

Options:
  --format <fmt>        html, pdf, docx, yaml, json, terraform, pulumi
  --what <item>         blueprint, prompts, evals, security, compliance, all
  --output <path>       Output path

Examples:
  clean-agents export --format pdf --what blueprint
  clean-agents export --format terraform --what infrastructure
  clean-agents export --format docx --what compliance     # Auditor-ready doc
```

---

### `clean-agents serve`

Start CLean-agents as an API or MCP server.

```bash
clean-agents serve [options]

Options:
  --mode <mode>         api, mcp [default: api]
  --port <N>            Port number [default: 8420]
  --host <addr>         Bind address [default: 127.0.0.1]
  --cors                Enable CORS for web UI

Examples:
  clean-agents serve                          # REST API on :8420
  clean-agents serve --mode mcp               # MCP server for Claude/Cursor
  clean-agents serve --port 3000 --cors       # For web UI development
```

**API endpoints:**
```
POST   /api/design          # Start design session
POST   /api/design/:id/ask  # Answer design questions
GET    /api/blueprint        # Get current blueprint
POST   /api/shield/scan      # Run security scan
POST   /api/eval/run         # Run evaluation suite
GET    /api/cost             # Get cost projection
GET    /api/comply/gaps      # Get compliance gaps
```

**MCP tools exposed:**
```
design_system          # Interactive design
generate_blueprint     # Generate HTML blueprint
run_security_scan      # Static security analysis
generate_prompts       # Generate agent prompts
simulate_cost          # Cost projection
map_compliance         # Compliance mapping
```

---

### `clean-agents doctor`

Environment check — verify all dependencies.

```bash
clean-agents doctor

  CLean-agents v1.0 Doctor

  ✓ Python 3.11+                     3.12.3
  ✓ API Key (Anthropic)              sk-ant-...Xk2
  ✓ API Key (OpenAI)                 sk-...f4a (optional)
  ✓ Garak installed                  v0.9.2
  ✗ PyRIT installed                  not found (optional)
  ✓ Docker available                 24.0.7
  ✓ Node.js (for Mermaid CLI)        v20.11.0
  ✓ Locust installed                 v2.24.0 (optional)
  ✓ k6 installed                     v0.49.0 (optional)

  Project: ./my-legal-system
  ✓ .clean-agents/ directory         found
  ✓ blueprint.yaml                   valid (3 agents)
  ✓ eval suite                       42 test cases
  ✗ baseline                         not set (run: clean-agents eval run --baseline)

  Overall: Ready (2 optional items missing)
```

---

## Global Options (all commands)

```
--verbose, -v         Verbose output (show research queries, LLM calls)
--quiet, -q           Minimal output (for CI/CD)
--no-color            Disable colored output
--json                Machine-readable JSON output
--config <path>       Override config path [default: ./clean-agents.yaml]
--llm <provider>      LLM provider override (anthropic, openai)
--model <name>        Model override
--api-key <key>       API key override
--language <lang>     Output language override (en, es, pt, fr, de)
--dry-run             Show what would happen without executing
--version             Show version
--help, -h            Show help
```

---

## Configuration Hierarchy

```
Priority (highest to lowest):
1. CLI flags (--model claude-sonnet-4-6)
2. Environment variables (CLEAN_AGENTS_MODEL=claude-sonnet-4-6)
3. Project config (.clean-agents/config.yaml)
4. User config (~/.config/clean-agents/config.yaml)
5. Defaults (embedded in framework)
```

### Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-...         # Anthropic API key
OPENAI_API_KEY=sk-...                # OpenAI API key (optional)
CLEAN_AGENTS_MODEL=claude-opus-4-6   # Default model
CLEAN_AGENTS_LANGUAGE=es             # Default language
CLEAN_AGENTS_OUTPUT=./outputs        # Default output directory
CLEAN_AGENTS_LOG_LEVEL=info          # Logging level
```

---

## Python SDK API

The CLI is a thin wrapper around the Python SDK:

```python
from clean_agents import CleanAgents, Blueprint

# Initialize
ca = CleanAgents(api_key="sk-ant-...")

# Design (programmatic)
blueprint = ca.design(
    description="Multi-agent legal contract analysis system",
    pattern="supervisor-hierarchical",
    domain="legal",
    language="es"
)

# Generate prompts
prompts = ca.prompt.generate(blueprint)
print(prompts["orchestrator"])

# Cost simulation
cost = ca.cost.simulate(blueprint, volume=1000)
print(f"Monthly: ${cost.monthly_total:.2f}")

# Security scan
findings = ca.shield.scan(blueprint)
for f in findings.critical:
    print(f"[CRITICAL] {f.title}: {f.remediation}")

# Evaluation
suite = ca.eval.generate(blueprint, count=10)
results = ca.eval.run(suite, runs=50)
print(f"Pass rate: {results.pass_rate:.1%}")

# Compliance
gaps = ca.comply.scan(blueprint, regulations=["gdpr", "eu-ai-act"])
for gap in gaps.critical:
    print(f"[{gap.regulation}] {gap.component}: {gap.finding}")

# Export
blueprint.export("html", open=True)
blueprint.export("pdf", path="./report.pdf")

# Code scaffold
ca.scaffold(blueprint, framework="langgraph", complete=True, tests=True)
```

### Blueprint as Code

```python
from clean_agents import Blueprint, Agent, Memory, Guardrails

# Define programmatically
bp = Blueprint(
    name="contract-analysis",
    pattern="supervisor-hierarchical",
    agents=[
        Agent(
            name="orchestrator",
            role="Plan decomposition and routing",
            model="claude-opus-4-6",
            reasoning="htn-planning",
            tools=["route_to_agent", "synthesize_results"],
            memory=Memory(short_term=True),
            guardrails=Guardrails(
                input=["injection_detection"],
                output=["schema_validation"]
            ),
            hitl="pre-action",
            token_budget=2000
        ),
        Agent(
            name="doc_analyzer",
            role="Extract clauses and risks",
            model="claude-sonnet-4-6",
            reasoning="react",
            tools=["read_document", "search_kb"],
            memory=Memory(short_term=True, graphrag=True),
        ),
    ]
)

# All modules work on Blueprint objects
ca.prompt.generate(bp)
ca.cost.simulate(bp, volume=5000)
ca.shield.scan(bp)
```

---

## Package Structure

```
clean-agents/
├── pyproject.toml
├── src/
│   └── clean_agents/
│       ├── __init__.py              # Public API exports
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py              # Click/Typer CLI entrypoint
│       │   ├── init_cmd.py
│       │   ├── design_cmd.py
│       │   ├── blueprint_cmd.py
│       │   ├── prompt_cmd.py
│       │   ├── model_cmd.py
│       │   ├── cost_cmd.py
│       │   ├── eval_cmd.py
│       │   ├── shield_cmd.py
│       │   ├── observe_cmd.py
│       │   ├── migrate_cmd.py
│       │   ├── comply_cmd.py
│       │   ├── load_cmd.py
│       │   ├── scaffold_cmd.py
│       │   ├── export_cmd.py
│       │   ├── serve_cmd.py
│       │   └── doctor_cmd.py
│       ├── core/
│       │   ├── blueprint.py         # Blueprint data model (Pydantic v2)
│       │   ├── agent.py             # Agent model
│       │   ├── config.py            # Configuration loading
│       │   ├── session.py           # Design session state machine
│       │   └── research.py          # WebSearch + paper analysis
│       ├── engine/
│       │   ├── decision.py          # 4-layer decision engine
│       │   ├── cascade.py           # Cascading implications calculator
│       │   └── recommender.py       # Architecture recommender
│       ├── modules/
│       │   ├── prompt_lab.py        # Prompt generation
│       │   ├── model_chooser.py     # Model selection + assignment
│       │   ├── cost_sim.py          # Cost simulation
│       │   ├── eval_gen.py          # Eval suite generator
│       │   ├── shield.py            # Security scanner
│       │   ├── shield_attacker.py   # Live red team
│       │   ├── observer.py          # Observability configs
│       │   ├── migrator.py          # Migration advisor
│       │   ├── complier.py          # Compliance mapper
│       │   ├── load_planner.py      # Load testing
│       │   └── scaffolder.py        # Code generation
│       ├── renderers/
│       │   ├── html.py              # HTML + Mermaid renderer
│       │   ├── pdf.py               # PDF export
│       │   ├── yaml_render.py       # YAML serialization
│       │   └── terminal.py          # Rich terminal UI
│       ├── integrations/
│       │   ├── anthropic.py         # Claude API wrapper
│       │   ├── openai.py            # OpenAI API wrapper
│       │   ├── garak.py             # Garak integration
│       │   ├── pyrit.py             # PyRIT integration
│       │   ├── langfuse.py          # Langfuse integration
│       │   └── mcp_server.py        # MCP server mode
│       ├── knowledge/               # Embedded knowledge (from skill references)
│       │   ├── architecture.py      # Architecture patterns
│       │   ├── taxonomy.py          # 12 dimensions
│       │   ├── security.py          # Attack catalog
│       │   ├── compliance.py        # Regulation database
│       │   ├── benchmarks.py        # Model benchmarks
│       │   └── templates.py         # Output templates
│       └── server/
│           ├── api.py               # FastAPI REST API
│           └── mcp.py               # MCP server implementation
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
│   ├── getting-started.md
│   ├── cli-reference.md
│   ├── sdk-reference.md
│   └── modules/
└── examples/
    ├── legal-system/
    ├── support-bot/
    └── coding-assistant/
```

---

## Dependencies

```toml
[project]
name = "clean-agents"
version = "1.0.0"
requires-python = ">=3.11"

dependencies = [
    "anthropic>=0.40.0",         # Claude API
    "typer[all]>=0.12.0",        # CLI framework
    "rich>=13.0",                # Terminal UI
    "pydantic>=2.0",             # Data models
    "pyyaml>=6.0",               # Config handling
    "jinja2>=3.1",               # Template rendering
    "httpx>=0.27",               # HTTP client (research)
    "fastapi>=0.115",            # API server
    "uvicorn>=0.30",             # ASGI server
]

[project.optional-dependencies]
openai = ["openai>=1.50"]
security = ["garak>=0.9"]
eval = ["ragas>=0.2"]
observe = ["opentelemetry-api>=1.25", "opentelemetry-sdk>=1.25"]
load = ["locust>=2.24"]
all = ["clean-agents[openai,security,eval,observe,load]"]

[project.scripts]
clean-agents = "clean_agents.cli.main:app"
```
