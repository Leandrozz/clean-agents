# Output Templates for CLean-agents

Templates for the HTML artifacts, Mermaid diagrams, agent specs, and project plans
that CLean-agents generates.

## HTML Template

Use this base template for all HTML outputs. Save to the outputs directory.
The template uses a dark theme with Mermaid.js for diagrams.

### Base HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CLean-agents Blueprint — [PROJECT NAME]</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.6.1/mermaid.min.js"></script>
<style>
  :root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --surface2: #1a1a2e;
    --border: #2a2a3e;
    --accent: #6366f1;
    --accent2: #8b5cf6;
    --accent3: #06b6d4;
    --green: #10b981;
    --amber: #f59e0b;
    --red: #ef4444;
    --text: #e2e8f0;
    --text-dim: #94a3b8;
    --text-bright: #f8fafc;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Inter', -apple-system, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
  /* ... (see the blueprint HTML for the full CSS) ... */
</style>
</head>
```

### Mermaid Configuration

Always use this config for dark theme compatibility:

```javascript
mermaid.initialize({
  startOnLoad: true,
  theme: 'dark',
  themeVariables: {
    primaryColor: '#6366f1',
    primaryTextColor: '#e2e8f0',
    primaryBorderColor: '#4f46e5',
    lineColor: '#94a3b8',
    secondaryColor: '#1a1a2e',
    tertiaryColor: '#12121a',
    background: '#12121a',
    mainBkg: '#1a1a2e',
    nodeBorder: '#6366f1',
    fontSize: '14px'
  },
  flowchart: { curve: 'basis', padding: 20 },
  sequence: { mirrorActors: false, messageMargin: 40 },
  gantt: { fontSize: 12 }
});
```

### Tab Navigation Pattern

```html
<div class="tabs">
  <div class="tab active" onclick="showSection('overview')">System Overview</div>
  <div class="tab" onclick="showSection('agents')">Agent Specs</div>
  <div class="tab" onclick="showSection('flow')">Data Flow</div>
  <div class="tab" onclick="showSection('plan')">Project Plan</div>
  <div class="tab" onclick="showSection('security')">Security</div>
</div>
```

---

## Mermaid Diagram Templates

### Critical Mermaid Syntax Rules

These rules prevent the most common rendering failures:
- Node IDs: alphanumeric only (A1, ORCH, DOC_ANALYZER). No hyphens, dots, or spaces.
- Labels with spaces: wrap in double quotes — `A1["My Agent"]`
- Line breaks in labels: use `<br/>` inside quotes — `A1["Line One<br/>Line Two"]`
- Forbidden in labels: parentheses (), ampersands &, angle brackets <>, raw quotes
- Max 15 nodes per diagram. Split complex systems into multiple diagrams.
- Max 2 levels of subgraph nesting.
- Sequence diagram participant names: 1-2 words, no special characters.
- Always validate: every opening bracket/quote has a matching close.

### System Overview (Phase 1)
Use `graph TB` or `graph LR` to show agents and their connections.
Color-code by role:
- Orchestrator: `fill:#f59e0b` (amber)
- Specialist agents: `fill:#06b6d4` (cyan)
- Memory/knowledge: `fill:#8b5cf6` (purple)
- Input/output: `fill:#6366f1` (indigo)
- Human: `fill:#10b981` (green)

### Agent Detail (Phase 2)
Use `subgraph` blocks for each agent showing internal components:
model, reasoning pattern, tools, memory, guardrails.

### Sequence Diagram (Phase 3)
Use `sequenceDiagram` to show the complete data flow including:
- User interaction
- Agent-to-agent communication
- Tool calls
- Memory reads/writes
- HITL approval points (use `alt` blocks)

### Gantt Chart (Phase 3)
Use `gantt` for the project plan with sections per sprint.

---

## Agent Spec Template (Markdown)

Generate one section per agent in this format:

```markdown
## Agent: [Name]

**Role**: [One sentence describing what this agent does]
**Model**: [Primary model] (fallback: [fallback model])
**Reasoning**: [Pattern — ReAct, ToT, HTN, Reflection, etc.]

### Tools
| Tool | Purpose | Risk Level |
|------|---------|-----------|
| [name] | [what it does] | Low/Medium/High |

### Memory
- **Short-term**: [context window management approach]
- **Long-term**: [episodic/semantic/procedural/GraphRAG — whichever apply]

### Guardrails
- **Input**: [specific filters]
- **Output**: [specific validators]
- **HITL**: [when human approval is required, or "Not required"]

### Metrics
- [metric 1]: [target]
- [metric 2]: [target]

### Budget
- **Token ceiling**: [max tokens per operation]
- **Estimated cost**: [$ per operation]
- **Circuit breaker**: [failure condition → action]
```

---

## Project Plan Template

### Sprint Table

| Sprint | Task | Dependency | Estimate | Risk |
|--------|------|-----------|----------|------|
| S1 | [task description] | — | [X days] | Low/Medium/High |

### Risk Levels
- **Low**: Well-understood, standard implementation
- **Medium**: Some uncertainty, may need iteration
- **High**: Significant unknowns, may require architecture changes

### Estimation Guidelines
- Setup + infra: 2-3 days
- Simple agent (ReAct + tools): 2-3 days
- Complex agent (ToT/Reflection + memory): 4-5 days
- Orchestrator + routing: 2-4 days
- GraphRAG setup: 3-5 days
- Guardrails + circuit breakers: 2-3 days
- Observability stack: 2-3 days
- Testing suite (with 50-run E2E): 3-5 days
- Red teaming: 2-3 days

---

## Code Scaffold Template

Generate this directory structure adapted to the specific project:

```
project-name/
├── agents/
│   ├── orchestrator.py      # Supervisor/routing logic
│   ├── [agent_name].py      # One file per agent
│   └── ...
├── memory/
│   ├── short_term.py        # Context window management
│   ├── episodic.py          # Vector DB interface (if needed)
│   ├── semantic.py          # Facts/rules store (if needed)
│   └── graphrag.py          # Knowledge graph + RAG (if needed)
├── guardrails/
│   ├── input_filters.py     # PII, injection, encoding, size
│   ├── output_validators.py # Schema, confidence, safety
│   └── circuit_breaker.py   # Failure tracking + fast-fail
├── tools/
│   ├── mcp_server.py        # MCP tool definitions
│   └── tool_registry.py     # Dynamic tool selection (if needed)
├── observability/
│   ├── tracer.py            # Runs, traces, threads
│   └── metrics.py           # Performance dashboards
├── tests/
│   ├── unit/                # Per-agent mocked tests
│   ├── integration/         # Agent interaction tests
│   └── e2e/                 # Full system (N runs)
├── config.yaml              # System configuration
└── README.md                # Auto-generated documentation
```

Only include directories relevant to the specific project. A simple single-agent system
doesn't need the full structure.
