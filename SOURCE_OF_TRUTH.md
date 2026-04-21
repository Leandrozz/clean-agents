# CLean-agents — Source of Truth

> Last updated: 2026-04-20 | Version: 0.1.0 | Status: Alpha (published on PyPI)

## 1. Project Overview

**CLean-agents** is a Python CLI + SDK framework for designing, planning, and hardening production-grade agentic AI systems. It acts as an "architecture consultant" that takes a natural-language description of an agentic system and produces evidence-backed blueprints, security analyses, cost projections, scaffolded code, and deployment infrastructure.

- **PyPI**: `pip install clean-agents`
- **Repository**: [github.com/Leandrozz/clean-agents](https://github.com/Leandrozz/clean-agents)
- **License**: MIT
- **Author**: Leandro (leansroasas@gmail.com)

## 2. Architecture

### 2.1 Core Data Flow

```
User description → Recommender (heuristic engine) → Blueprint (Pydantic model)
                                                       ↓
                                           ┌───────────┼────────────┐
                                           ▼           ▼            ▼
                                      Modules     Scaffold      Export
                                    (cost, eval,  (LangGraph,   (Docker,
                                     shield...)   CrewAI...)    K8s, TF)
```

### 2.2 System Layers

| Layer | Purpose | Key Files |
|-------|---------|-----------|
| **CLI** | Typer + Rich terminal interface (25+ commands) | `cli/main.py`, `cli/*_cmd.py` |
| **Core** | Pydantic v2 data models (Blueprint, AgentSpec, Config) | `core/blueprint.py`, `core/agent.py`, `core/config.py` |
| **Engine** | Heuristic recommender + AI-enhanced design | `engine/recommender.py`, `integrations/anthropic.py` |
| **Harness** | Runtime execution + benchmarking of agent systems | `harness/runtime.py`, `harness/benchmark.py` |
| **Modules** | On-demand analysis plugins (cost, eval, shield, etc.) | `modules/base.py`, `modules/examples.py` |
| **Knowledge** | Three-layer knowledge base (built-in → global → project) | `knowledge/updater.py`, `knowledge/base.py` |
| **Server** | FastAPI REST API + MCP stdio server | `server/api.py`, `server/mcp_server.py` |
| **Renderers** | Terminal (Rich) and HTML output | `renderers/terminal.py`, `renderers/html.py` |
| **Infrastructure** | Versioning, telemetry, i18n, auth | `core/versioning.py`, `telemetry.py`, `i18n.py`, `server/auth.py` |

### 2.3 Design Principles

1. **Heuristic-first**: every command works offline without API keys; AI enhancement is opt-in via `--ai` flag.
2. **Blueprint as source of truth**: all commands read/write a single `blueprint.yaml` file.
3. **Plugin-extensible**: three plugin types (Analysis, Scaffold, Transform) with three discovery sources (entry points, directory, registry).
4. **Evidence-backed**: design decisions reference research findings (paper titles, metrics, years).
5. **Framework-agnostic**: generates code for LangGraph, CrewAI, AutoGen, Semantic Kernel, LlamaIndex.

## 3. CLI Commands

### 3.1 Top-level Commands

| Command | Description |
|---------|-------------|
| `clean-agents init` | Initialize a `.clean-agents/` project directory |
| `clean-agents design` | Interactive architecture design session (heuristic + optional AI) |
| `clean-agents blueprint` | View/export the current blueprint (summary, YAML, JSON, HTML) |
| `clean-agents diff` | Compare two blueprints side-by-side |
| `clean-agents shield` | Run CLean-shield security hardening analysis |
| `clean-agents cost` | Run cost simulator |
| `clean-agents eval` | Generate evaluation suite |
| `clean-agents observe` | Generate observability blueprint |
| `clean-agents models` | Run model selection analysis |
| `clean-agents prompts` | Generate optimized prompt templates |
| `clean-agents migrate` | Run migration advisor |
| `clean-agents comply` | Run compliance mapper |
| `clean-agents load` | Generate load testing plan |
| `clean-agents scaffold` | Generate framework-specific starter code |
| `clean-agents export` | Export blueprint as deployment infrastructure |
| `clean-agents serve` | Start API server (REST or MCP mode) |

### 3.2 Subcommand Groups

| Group | Commands | Description |
|-------|----------|-------------|
| `plugin` | `list`, `run`, `init` | Manage and run analysis plugins |
| `harness` | `run`, `trace` | Execute agent systems against blueprints |
| `benchmark` | `run`, `compare`, `suite` | Benchmark and compare blueprints |
| `marketplace` | `search`, `list`, `info`, `install` | Browse/install community plugins |
| `history` | `list`, `restore`, `diff` | Blueprint version history |
| `knowledge` | `list`, `add`, `import`, `export` | Manage the knowledge base |
| `telemetry` | `status`, `enable`, `disable`, `export`, `clear` | Local usage telemetry |

## 4. Key Technical Decisions

### 4.1 Architecture Pattern Classification

The recommender maps descriptions to one of five architecture patterns:

| Pattern | When Used |
|---------|-----------|
| `single` | Simple tasks, single responsibility |
| `pipeline` | Sequential processing, ETL-like flows |
| `supervisor-hierarchical` | Complex multi-agent with orchestration (default) |
| `blackboard-swarm` | Exploratory/creative tasks, research |
| `hybrid-hierarchical-swarm` | Enterprise-scale, mixed workloads |

### 4.2 Agent Autonomy Levels (L1–L5)

| Level | Name | Description |
|-------|------|-------------|
| L1 | Informational | Read-only, no actions |
| L2 | Approval Required | Every action needs human approval |
| L3 | Active Approval | Most actions auto-approved, high-risk flagged |
| L4 | Supervisory | Autonomous with periodic human review |
| L5 | Fully Autonomous | No human-in-the-loop |

### 4.3 Security (CLean-shield)

Seven attack categories analyzed:

| Category | Examples |
|----------|----------|
| Prompt Injection | Direct injection, indirect via tool outputs |
| Data Exfiltration | PII leakage, context smuggling |
| Privilege Escalation | Tool misuse, scope creep |
| Denial of Service | Token flooding, recursive loops |
| Model Manipulation | Jailbreaking, role confusion |
| Supply Chain | Malicious plugins, dependency attacks |
| Social Engineering | Authority impersonation, urgency exploitation |

### 4.4 Framework Scaffolding

| Framework | Output |
|-----------|--------|
| LangGraph | `graph.py` with StateGraph, nodes, edges |
| CrewAI | `crew.py` with Crew, Agent, Task definitions |
| AutoGen | `agents.py` with ConversableAgent, GroupChat |
| Semantic Kernel | `agents.py` with Kernel, ChatCompletionAgent |
| LlamaIndex | `workflow.py` with Workflow, steps, events |

### 4.5 Infrastructure Export

| Target | Output Files |
|--------|-------------|
| Docker | `Dockerfile`, `docker-compose.yml`, `.env.example`, `.dockerignore` |
| Kubernetes | `deployment.yaml`, `service.yaml`, `configmap.yaml`, `hpa.yaml` |
| Terraform AWS | `main.tf`, `variables.tf`, `outputs.tf` (ECS Fargate + Secrets Manager) |
| Terraform GCP | `main.tf`, `variables.tf`, `outputs.tf` (Cloud Run + Secret Manager) |
| CloudFormation | `template.yaml` (ECS Fargate stack) |

## 5. Data Models

### 5.1 Blueprint (central model)

```
Blueprint
├── Metadata: name, description, version, language, created_at, updated_at
├── Classification: system_type, pattern, domain, scale, autonomy, framework
├── agents: list[AgentSpec]
│   ├── name, role, agent_type, model (ModelConfig)
│   ├── tools, reasoning, token_budget, hitl
│   ├── guardrails (GuardrailConfig: input/output rules)
│   └── memory (MemoryConfig: short/long/graphrag)
├── infrastructure: InfraConfig (vector_db, graph_db, message_queue, etc.)
├── compliance: ComplianceConfig (regulations, data_residency, audit_trail)
├── cost: CostConfig (budget_monthly, optimization flags)
├── timeline: TimelineConfig (start, target_mvp, target_prod)
├── decisions: list[DesignDecision] (dimension, justification, research)
├── research_findings: list[ResearchFinding]
└── Iteration: iteration count, changelog
```

### 5.2 AgentSpec

Each agent has: name, role, agent_type (orchestrator/worker/specialist/evaluator), model config (primary + fallback), reasoning level, token budget, HITL level, guardrails (input/output rules), memory config, and a tools list.

## 6. Harness System

### 6.1 Runtime Harness

Executes multi-agent systems with support for four architecture patterns:

- **Single**: Direct agent execution
- **Pipeline**: Sequential agent chain, output → input
- **Supervisor**: Orchestrator delegates to workers, aggregates results
- **Swarm**: Parallel execution, shared blackboard state

Components: `AgentRuntime`, `RuntimeHarness`, `LLMProvider` (Anthropic/OpenAI/Mock), Interceptors (logging, guardrails, fault injection, cost tracking).

### 6.2 Benchmark Harness

Compares blueprints across 10 default tasks with scoring:
- 0.5 base completion score
- 0.25 exact match bonus
- 0.25 keyword overlap bonus

Outputs: per-task results, aggregate scores, comparative analysis, winner determination.

## 7. Plugin System

### 7.1 Plugin Types

| Type | Purpose | Method |
|------|---------|--------|
| `AnalysisPlugin` | Read-only analysis of blueprints | `analyze(blueprint) → dict` |
| `ScaffoldPlugin` | Generate files from blueprints | `scaffold(blueprint, output_dir)` |
| `TransformPlugin` | Modify blueprints in-place | `transform(blueprint) → Blueprint` |

### 7.2 Discovery Sources

1. **Entry points**: `pyproject.toml` `[project.entry-points."clean_agents.plugins"]`
2. **Plugin directory**: `.clean-agents/plugins/*.py`
3. **Marketplace**: curated registry with search/install

### 7.3 Built-in Plugins

- `TokenBudgetAuditor` — flags agents with budget <500 or >50k tokens
- `RedundancyDetector` — finds agents with overlapping roles
- `CostOptimizer` — suggests model downgrades to reduce cost

## 8. Server

### 8.1 REST API (`clean-agents serve`)

FastAPI server with endpoints:
- `POST /design` — run design session
- `GET /blueprint` — get current blueprint
- `POST /shield` — run security analysis
- `POST /cost` — run cost simulator

Optional auth via `--auth` flag with API key authentication and token bucket rate limiting.

### 8.2 MCP Server (`clean-agents serve --mode mcp`)

Stdio-based MCP server exposing the same capabilities as tools for LLM integration.

## 9. Knowledge Base

Three-layer override system:

```
Built-in (packaged) → Global (~/.clean-agents/knowledge/) → Project (.clean-agents/knowledge/)
```

Categories: `models`, `frameworks`, `compliance`, `security`, `patterns`, `tools`.

Each entry: key, value, metadata (source, updated_at, version), tags.

CLI: `knowledge list|add|import|export`.

## 10. Infrastructure Features

### 10.1 Blueprint Versioning

- SHA256 content hashing for change detection
- Snapshot/restore with descriptions
- Version history with diff between any two versions
- Auto-snapshot on `blueprint.save()` inside project directories

### 10.2 Telemetry (opt-in, local-only)

- JSONL storage at `~/.clean-agents/telemetry/events.jsonl`
- Events: command usage, duration, blueprint stats
- No network calls — purely local analytics
- CLI: `telemetry status|enable|disable|export|clear`

### 10.3 Internationalization (i18n)

- Supported languages: English (en), Spanish (es), Portuguese (pt)
- 21+ translation keys covering all user-facing messages
- Fallback chain: requested language → English
- Set via `--lang` flag or `CLEAN_AGENTS_LANG` env var

### 10.4 API Authentication

- API key authentication via `--auth` + `--api-key` or `CLEAN_AGENTS_API_KEYS` env
- Token bucket rate limiting (configurable RPM, burst capacity)
- Per-key tracking with automatic refill

## 11. Project Stats

| Metric | Value |
|--------|-------|
| Source files | 48 |
| Source lines | ~12,100 |
| Test files | 19 |
| Test lines | ~5,000 |
| Tests passing | 303 |
| CLI commands | 25+ (including subcommands) |
| Supported frameworks | 5 (LangGraph, CrewAI, AutoGen, Semantic Kernel, LlamaIndex) |
| Export targets | 5 (Docker, K8s, Terraform AWS/GCP, CloudFormation) |
| Attack categories | 7 (CLean-shield) |
| Languages | 3 (en, es, pt) |

## 12. File Structure

```
clean-agents/
├── src/clean_agents/
│   ├── __init__.py              # Package version
│   ├── i18n.py                  # Internationalization (en/es/pt)
│   ├── telemetry.py             # Opt-in local telemetry
│   ├── py.typed                 # PEP 561 marker
│   ├── cli/
│   │   ├── main.py              # Typer app, all command registration
│   │   ├── init_cmd.py          # Project initialization
│   │   ├── design_cmd.py        # Interactive design + AI iteration
│   │   ├── blueprint_cmd.py     # View/export blueprint
│   │   ├── diff_cmd.py          # Blueprint comparison
│   │   ├── shield_cmd.py        # Security analysis
│   │   ├── module_cmds.py       # Cost, eval, observe, models, prompts, migrate, comply, load
│   │   ├── scaffold_cmd.py      # Code generation (5 frameworks + Docker + Terraform)
│   │   ├── export_cmd.py        # Infrastructure export (Docker, K8s, TF, CF)
│   │   ├── plugin_cmd.py        # Plugin management
│   │   ├── harness_cmd.py       # Agent runtime execution
│   │   ├── benchmark_cmd.py     # Blueprint benchmarking
│   │   ├── marketplace_cmd.py   # Community plugin marketplace
│   │   ├── history_cmd.py       # Blueprint versioning
│   │   ├── knowledge_cmd.py     # Knowledge base management
│   │   └── telemetry_cmd.py     # Telemetry management
│   ├── core/
│   │   ├── agent.py             # AgentSpec, ModelConfig, GuardrailConfig, MemoryConfig
│   │   ├── blueprint.py         # Blueprint, SystemType, ArchitecturePattern, InfraConfig
│   │   ├── config.py            # Config discovery and project settings
│   │   └── versioning.py        # BlueprintVersion, VersionManager, SHA256 hashing
│   ├── engine/
│   │   └── recommender.py       # Heuristic recommendation engine (12 dimensions)
│   ├── harness/
│   │   ├── runtime.py           # AgentRuntime, RuntimeHarness, 4 architecture patterns
│   │   ├── providers.py         # LLMProvider ABC, Anthropic/OpenAI/Mock providers
│   │   ├── interceptors.py      # Logging, guardrails, fault injection, cost tracking
│   │   └── benchmark.py         # BenchmarkSuite, BenchmarkRunner, scoring system
│   ├── integrations/
│   │   └── anthropic.py         # ClaudeArchitect (AI-enhanced design)
│   ├── knowledge/
│   │   ├── base.py              # Base knowledge data
│   │   └── updater.py           # KnowledgeStore with 3-layer overrides
│   ├── modules/
│   │   ├── base.py              # Plugin ABC (Analysis, Scaffold, Transform)
│   │   ├── examples.py          # 3 built-in plugins
│   │   └── marketplace.py       # Plugin registry, search, install
│   ├── renderers/
│   │   ├── terminal.py          # Rich console output
│   │   └── html.py              # HTML report generation
│   └── server/
│       ├── api.py               # FastAPI REST server + auth middleware
│       ├── auth.py              # AuthConfig, RateLimiter, AuthManager
│       └── mcp_server.py        # MCP stdio server
├── tests/                       # 19 test files, 303 tests
├── .github/workflows/ci.yml     # GitHub Actions CI (Python 3.10/3.11/3.12)
├── pyproject.toml               # Build config, dependencies, entry points
├── README.md                    # PyPI-facing documentation
├── CHANGELOG.md                 # Version history
├── LICENSE                      # MIT
└── SOURCE_OF_TRUTH.md           # This file
```

## 13. Dependencies

### Required
- `typer[all]>=0.12.0` — CLI framework
- `rich>=13.0` — Terminal formatting
- `pydantic>=2.0` — Data validation
- `pyyaml>=6.0` — YAML serialization
- `jinja2>=3.1` — Template rendering
- `httpx>=0.27` — HTTP client

### Optional Extras
- `[ai]` — `anthropic>=0.40.0` (AI-enhanced design)
- `[api]` — `fastapi>=0.115`, `uvicorn>=0.30` (REST server)
- `[openai]` — `openai>=1.50` (OpenAI provider)
- `[security]` — `garak>=0.9` (adversarial testing)
- `[eval]` — `ragas>=0.2` (evaluation)
- `[observe]` — `opentelemetry-api/sdk>=1.25`
- `[load]` — `locust>=2.24` (load testing)
- `[all]` — everything above
- `[dev]` — pytest, ruff, mypy

## 14. Development

### Setup
```bash
git clone https://github.com/Leandrozz/clean-agents.git
cd clean-agents
pip install -e ".[dev]"
```

### Testing
```bash
pytest tests/ -v          # Full suite (303 tests)
pytest tests/test_core.py # Single module
ruff check src/           # Linting
```

### CI/CD
- GitHub Actions runs on push/PR to `main`
- Matrix: Python 3.10, 3.11, 3.12
- Steps: checkout → setup Python → install deps → ruff check → pytest

## 15. Roadmap

### Completed (v0.1.0)
- [x] Core CLI with 25+ commands
- [x] Heuristic recommender engine (12 design dimensions)
- [x] AI-enhanced design with ClaudeArchitect (multi-turn iteration)
- [x] CLean-shield security analysis (7 attack categories)
- [x] 8 on-demand modules (cost, eval, observe, models, prompts, migrate, comply, load)
- [x] Code scaffolding (5 frameworks: LangGraph, CrewAI, AutoGen, Semantic Kernel, LlamaIndex)
- [x] Infrastructure export (Docker, K8s, Terraform AWS/GCP, CloudFormation)
- [x] Plugin system with marketplace
- [x] Runtime harness (4 architecture patterns)
- [x] Benchmark harness with scoring
- [x] Blueprint versioning with history
- [x] API server with auth + rate limiting
- [x] MCP server (stdio mode)
- [x] Dynamic knowledge base (3-layer overrides)
- [x] Opt-in local telemetry
- [x] i18n (en/es/pt)
- [x] GitHub Actions CI
- [x] Published on PyPI

### Planned (v0.2.0+)
- [ ] Real LLM provider integration tests (with mocked billing)
- [ ] Web dashboard for blueprint visualization
- [ ] `clean-agents watch` — file watcher for live blueprint updates
- [ ] Additional framework scaffolds (DSPy, Haystack)
- [ ] Plugin SDK documentation + community contribution guide
- [ ] More export targets (Azure ARM, Pulumi)
- [ ] Advanced benchmark tasks (multi-turn, tool-use, retrieval)
- [ ] Blueprint sharing/import from URL
- [ ] VS Code extension
- [ ] Performance profiling module
