# CLean-agents — Project Instructions for Claude Code

## Project

CLean-agents is a Python CLI + SDK for designing, planning, and hardening production-grade agentic AI systems. It acts as an architecture consultant.

- **PyPI**: `pip install clean-agents`
- **Repo**: github.com/Leandrozz/clean-agents
- **License**: MIT
- **Author**: Leandro (leansroasas@gmail.com)

## Stack

- Python 3.10+, Typer + Rich (CLI), Pydantic v2 (models), PyYAML, Jinja2
- FastAPI + Uvicorn (optional API server)
- Anthropic SDK (optional AI enhancement)
- pytest, ruff, mypy (dev tools)

## Structure

```
src/clean_agents/
├── cli/           # Typer commands (main.py = entrypoint)
├── core/          # Blueprint, AgentSpec, Config, Versioning
├── engine/        # Heuristic recommender
├── harness/       # Runtime + Benchmark harness
├── integrations/  # ClaudeArchitect (Anthropic SDK)
├── knowledge/     # Three-layer knowledge base
├── modules/       # Plugin system (base, examples, marketplace)
├── renderers/     # Terminal (Rich) + HTML output
└── server/        # FastAPI API + MCP server + Auth
```

## Key Conventions

- All data models use Pydantic v2 `BaseModel`
- Blueprint is the central model — every command reads/writes `blueprint.yaml`
- AI features are always optional (--ai flag), core works offline
- Plugin types: AnalysisPlugin, ScaffoldPlugin, TransformPlugin
- Entry point: `clean-agents` CLI or `python -m clean_agents.cli.main`
- Tests: `pytest tests/ -v` (303 tests, all passing)

## Testing

```bash
pytest tests/ -v                    # Full suite
pytest tests/test_core.py           # Single file
ruff check src/                     # Linting
```

## CLI Commands

Main: init, design, blueprint, diff, shield, cost, eval, observe, models, prompts, migrate, comply, load, scaffold, export, serve

Subgroups: plugin (list/run/init), harness (run/trace), benchmark (run/compare/suite), marketplace (search/list/info/install), history (list/restore/diff), knowledge (list/add/import/export), telemetry (status/enable/disable/export/clear)

## Do NOT

- Break the existing 303 tests
- Add required dependencies (new deps should be optional extras)
- Hardcode API keys or secrets
- Change the Blueprint schema without updating all consumers
