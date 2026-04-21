---
name: clean-agents-cli
description: "CLI reference for the CLean-agents Python package. Use when the user is running `clean-agents` commands (init, design, blueprint, shield, cost, eval, observe, scaffold, export, serve, plugin, harness, benchmark, marketplace, history, knowledge, telemetry) or writing Python code against the clean_agents SDK. Documents command flags, SDK classes (Blueprint, Recommender, Config), plugin types (AnalysisPlugin, TransformPlugin, ScaffoldPlugin), and install extras."
---

# CLean-agents CLI — Command & SDK Reference

## Overview

CLean-agents is a Python CLI + SDK that acts as an architecture consultant for building production-grade agentic AI systems. It takes a natural-language description and produces evidence-backed blueprints, security analyses, cost projections, scaffolded code, and deployment infrastructure.

## When to Use This Skill

Use when the user asks about:
- Designing or planning an agentic AI system
- Multi-agent architecture decisions
- Security hardening for AI agents (prompt injection, data exfiltration, etc.)
- Choosing frameworks (LangGraph, CrewAI, AutoGen, Semantic Kernel, LlamaIndex)
- Cost estimation for agent systems
- Scaffolding agent code
- Generating deployment infrastructure (Docker, K8s, Terraform, CloudFormation)

## How to Use

CLean-agents is installed as a CLI tool. All commands follow the pattern `clean-agents <command>`.

If `clean-agents` is not on PATH, use: `python -m clean_agents.cli.main <command>`

### Core Workflow

```bash
# 1. Initialize a project
clean-agents init

# 2. Design an architecture (interactive)
clean-agents design

# 3. Design with AI enhancement (requires ANTHROPIC_API_KEY)
clean-agents design --ai

# 4. Design non-interactively
clean-agents design --desc "A legal document review system with 3 agents that handles HIPAA compliance" --no-interactive
```

### Viewing and Comparing Blueprints

```bash
# View current blueprint
clean-agents blueprint

# Export as YAML/JSON
clean-agents blueprint --format yaml
clean-agents blueprint --format json

# Export to file
clean-agents blueprint --format yaml --export my-blueprint.yaml

# Generate HTML report
clean-agents blueprint --html --export report.html

# Compare two blueprints
clean-agents diff blueprint-v1.yaml blueprint-v2.yaml
clean-agents diff blueprint-v1.yaml blueprint-v2.yaml --format yaml
```

### Security Analysis (CLean-shield)

```bash
# Run security analysis
clean-agents shield

# With AI-enhanced deep analysis
clean-agents shield --ai
```

CLean-shield analyzes 7 attack categories:
1. **Prompt Injection** — direct injection, indirect via tool outputs
2. **Data Exfiltration** — PII leakage, context smuggling
3. **Privilege Escalation** — tool misuse, scope creep
4. **Denial of Service** — token flooding, recursive loops
5. **Model Manipulation** — jailbreaking, role confusion
6. **Supply Chain** — malicious plugins, dependency attacks
7. **Social Engineering** — authority impersonation, urgency exploitation

### On-Demand Modules

```bash
clean-agents cost          # Cost simulator — per-request and monthly projections
clean-agents models        # Model selection — benchmark-based recommendations
clean-agents prompts       # Prompt Lab — optimized templates per agent role
clean-agents prompts --ai  # AI-generated prompts
clean-agents eval          # Evaluation suite — test cases and metrics
clean-agents observe       # Observability — monitoring, tracing, alerting
clean-agents comply        # Compliance — regulation-to-component mapping
clean-agents load          # Load testing — performance scenarios
clean-agents migrate       # Migration advisor — framework migration paths
```

### Code Scaffolding

```bash
# Generate framework-specific starter code
clean-agents scaffold                          # Default: LangGraph
clean-agents scaffold --framework crewai
clean-agents scaffold --framework autogen
clean-agents scaffold --framework semantic-kernel
clean-agents scaffold --framework llamaindex

# Add infrastructure
clean-agents scaffold --docker                 # Dockerfile + docker-compose
clean-agents scaffold --terraform              # Terraform AWS configuration

# Combined
clean-agents scaffold --framework crewai --docker --terraform
```

### Infrastructure Export

```bash
clean-agents export --target docker            # Dockerfile + docker-compose.yml
clean-agents export --target kubernetes        # K8s manifests
clean-agents export --target terraform-aws     # ECS Fargate + Secrets Manager
clean-agents export --target terraform-gcp     # Cloud Run + Secret Manager
clean-agents export --target cloudformation    # CloudFormation ECS stack
```

### Plugin System

```bash
clean-agents plugin list                       # List available plugins
clean-agents plugin run <plugin-name>          # Run a specific plugin
clean-agents plugin init                       # Scaffold a new plugin

# Marketplace
clean-agents marketplace list                  # Browse all plugins
clean-agents marketplace search "security"     # Search plugins
clean-agents marketplace info <plugin-name>    # Plugin details
clean-agents marketplace install <plugin-name> # Install a plugin
```

### Runtime Harness

```bash
# Execute agent system against a blueprint
clean-agents harness run
clean-agents harness run --provider mock       # Use mock LLM (for testing)
clean-agents harness run --provider anthropic   # Use real Anthropic API
clean-agents harness run --input "Analyze this contract"
clean-agents harness trace                     # Show detailed execution trace

# Benchmark blueprints
clean-agents benchmark run                     # Benchmark current blueprint
clean-agents benchmark compare bp1.yaml bp2.yaml  # Compare two blueprints
clean-agents benchmark suite --export tasks.yaml   # Export benchmark suite
```

### Blueprint Versioning

```bash
clean-agents history list                      # Show version history
clean-agents history restore <version-id>      # Restore to a version
clean-agents history diff <v1> <v2>            # Diff two versions
```

### Knowledge Base

```bash
clean-agents knowledge list                    # List all entries
clean-agents knowledge list --category models  # Filter by category
clean-agents knowledge add                     # Add an entry interactively
clean-agents knowledge import updates.yaml     # Import from YAML
clean-agents knowledge export --output kb.yaml # Export to YAML
```

### API Server

```bash
# Start REST API
clean-agents serve
clean-agents serve --host 0.0.0.0 --port 8080

# With authentication
clean-agents serve --auth --api-key mykey123 --rate-limit 100

# Start MCP server (for LLM tool integration)
clean-agents serve --mode mcp
```

### Telemetry & i18n

```bash
# Telemetry (opt-in, local-only)
clean-agents telemetry status
clean-agents telemetry enable
clean-agents telemetry disable
clean-agents telemetry export --output stats.json

# Language
clean-agents design --lang es    # Spanish
clean-agents design --lang pt    # Portuguese
```

## SDK Usage (Python)

```python
from clean_agents.engine.recommender import Recommender
from clean_agents.core.blueprint import Blueprint

# Generate a blueprint programmatically
recommender = Recommender()
blueprint = recommender.recommend("A customer support system with 4 specialized agents")

# Access blueprint data
print(blueprint.name)
print(blueprint.pattern)  # e.g., "supervisor-hierarchical"
print(blueprint.estimated_cost_per_request())

for agent in blueprint.agents:
    print(f"{agent.name}: {agent.model.primary}, {agent.token_budget} tokens")

# Save/load
blueprint.save(Path("my-blueprint.yaml"))
loaded = Blueprint.load(Path("my-blueprint.yaml"))
```

## Architecture Patterns

| Pattern | Best For |
|---------|----------|
| `single` | Simple, single-responsibility tasks |
| `pipeline` | Sequential processing (ETL, document pipelines) |
| `supervisor-hierarchical` | Complex multi-agent with orchestration |
| `blackboard-swarm` | Exploratory/creative/research tasks |
| `hybrid-hierarchical-swarm` | Enterprise-scale mixed workloads |

## Agent Autonomy Levels

| Level | Name | Description |
|-------|------|-------------|
| L1 | Informational | Read-only, no actions |
| L2 | Approval Required | Every action needs human approval |
| L3 | Active Approval | Most actions auto, high-risk flagged |
| L4 | Supervisory | Autonomous with periodic review |
| L5 | Fully Autonomous | No human-in-the-loop |

## Important Notes

- The core CLI works **without any API key** (heuristic-only mode)
- Use `--ai` flag + `ANTHROPIC_API_KEY` env var for AI-enhanced mode
- Blueprints are saved as YAML in `.clean-agents/blueprint.yaml`
- All telemetry is local-only (no network calls)
- The project is MIT licensed and published on PyPI as `clean-agents`
