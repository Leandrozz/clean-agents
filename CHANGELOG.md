# Changelog

## [0.2.0] - 2026-04-21

### Added
- `src/clean_agents/crafters/` module — design Skills / MCPs / Tools / Plugins (Skills v1).
- CLI: `clean-agents skill {design,validate,render,publish,install,list}`.
- 15 validator rules for Skills (L1/L2/L3/L4) with Pydantic findings.
- Bidirectional Blueprint integration: `AgentSpec.recommended_artifacts`,
  `--for-agent`, and `design --module suggest-artifacts`.
- Optional `crafters` extra (`sentence-transformers>=2.7`). TF-IDF fallback
  preserves offline-first invariant.
- New entry-point group `clean_agents.validators` for third-party rules.

### Changed
- `AgentSpec` now has `recommended_artifacts: list[ArtifactRef]` (default `[]`).
  Blueprints from v0.1 continue to load unchanged.

## [0.1.0] — 2026-04-17

### Added
- 4-layer architecture recommendation engine (system classification → pattern → framework → transversal)
- Interactive CLI with 16 commands via Typer + Rich
- CLean-shield security analysis across 7 attack categories
- AI-enhanced design sessions with multi-turn iteration (`--ai` flag)
- AI-enhanced prompt generation and security analysis
- Plugin system with 3 types: Analysis, Transform, Scaffold
- 3 built-in plugins: Token Budget Auditor, Redundancy Detector, Cost Optimizer
- Plugin discovery: Python entry points, global dir, project dir
- Interactive HTML report with Mermaid diagrams and Chart.js
- Code scaffolding for LangGraph, CrewAI, Claude SDK, OpenAI SDK
- REST API server (FastAPI) with 7 endpoints
- MCP server for IDE integration (JSON-RPC over stdio)
- Embedded knowledge base: 7 models, 5 frameworks, 18 compliance requirements
- Cost simulator with per-agent breakdown and monthly projections
- Eval suite generator with test cases per agent
- Observability blueprint with metrics, traces, and alert rules
- Model chooser with benchmark-based recommendations
- Prompt Lab with role-specific template generation
- Migration advisor with framework compatibility matrix
- Compliance mapper for GDPR, HIPAA, EU AI Act, SOX, SOC2
- Load testing planner with 4 scenarios
- Blueprint save/load in YAML and JSON formats
- 68 tests covering core, engine, knowledge, server, and plugins
