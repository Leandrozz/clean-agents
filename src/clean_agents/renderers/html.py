"""HTML + Mermaid + Chart.js renderer for interactive blueprint reports.

Generates a single self-contained HTML file with:
  - Executive summary with KPI cards
  - Interactive tabbed sections (Architecture, Agents, Security, Cost, Decisions)
  - Mermaid architecture diagram
  - Chart.js cost breakdown and security score visualizations
  - Agent detail cards with expand/collapse
  - Dark theme with responsive layout
  - Print-friendly styles
"""

from __future__ import annotations

from clean_agents.core.blueprint import Blueprint
from clean_agents.cli.shield_cmd import ATTACK_CATEGORIES, _analyze_category


def render_html_report(blueprint: Blueprint) -> str:
    """Generate a complete interactive HTML report."""
    mermaid = _mermaid_diagram(blueprint)
    agents_html = _agents_section(blueprint)
    decisions_html = _decisions_section(blueprint)
    cost_data = _cost_data(blueprint)
    security_data = _security_data(blueprint)
    summary = blueprint.summary()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CLean-agents | {blueprint.name}</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
:root {{
  --bg: #0d1117; --bg2: #161b22; --bg3: #1c2333;
  --border: #30363d; --border-light: #3d444d;
  --text: #e6edf3; --text-dim: #8b949e; --text-muted: #656d76;
  --accent: #58a6ff; --accent-hover: #79c0ff;
  --green: #3fb950; --green-bg: rgba(63,185,80,0.15);
  --yellow: #d29922; --yellow-bg: rgba(210,153,34,0.15);
  --red: #f85149; --red-bg: rgba(248,81,73,0.15);
  --blue-bg: rgba(88,166,255,0.15);
  --purple: #bc8cff; --purple-bg: rgba(188,140,255,0.15);
  --radius: 8px; --shadow: 0 1px 3px rgba(0,0,0,0.4);
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.6;
}}
.container {{ max-width: 1280px; margin: 0 auto; padding: 2rem; }}
a {{ color: var(--accent); text-decoration: none; }}
a:hover {{ color: var(--accent-hover); }}

/* Header */
.header {{ margin-bottom: 2rem; }}
.header h1 {{ font-size: 2rem; color: var(--text); font-weight: 700; }}
.header h1 span {{ color: var(--accent); }}
.header p {{ color: var(--text-dim); margin-top: 0.25rem; max-width: 800px; }}
.meta {{ display: flex; gap: 1.5rem; margin-top: 0.75rem; color: var(--text-muted); font-size: 0.85rem; }}

/* KPI Grid */
.kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
.kpi {{
  background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 1.25rem; text-align: center; box-shadow: var(--shadow);
  transition: border-color 0.2s;
}}
.kpi:hover {{ border-color: var(--accent); }}
.kpi-value {{ font-size: 1.75rem; font-weight: 700; color: var(--accent); line-height: 1.2; }}
.kpi-label {{ color: var(--text-dim); font-size: 0.8rem; margin-top: 0.25rem; text-transform: uppercase; letter-spacing: 0.05em; }}

/* Tabs */
.tabs {{ display: flex; gap: 0; border-bottom: 1px solid var(--border); margin-bottom: 1.5rem; overflow-x: auto; }}
.tab {{
  padding: 0.75rem 1.25rem; cursor: pointer; color: var(--text-dim); font-size: 0.9rem;
  font-weight: 500; border-bottom: 2px solid transparent; white-space: nowrap;
  transition: color 0.2s, border-color 0.2s;
}}
.tab:hover {{ color: var(--text); }}
.tab.active {{ color: var(--accent); border-bottom-color: var(--accent); }}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; animation: fadeIn 0.3s ease; }}
@keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}

/* Cards */
.card {{
  background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 1.5rem; margin-bottom: 1rem; box-shadow: var(--shadow);
}}
.card h3 {{ color: var(--accent); margin-bottom: 0.75rem; font-size: 1.1rem; }}

/* Agent cards */
.agent-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 1rem; }}
.agent-card {{
  background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius);
  overflow: hidden; box-shadow: var(--shadow); transition: border-color 0.2s;
}}
.agent-card:hover {{ border-color: var(--accent); }}
.agent-header {{
  padding: 1rem 1.25rem; display: flex; justify-content: space-between;
  align-items: center; cursor: pointer; user-select: none;
}}
.agent-header h4 {{ margin: 0; font-size: 1rem; }}
.agent-header .toggle {{ color: var(--text-dim); transition: transform 0.3s; }}
.agent-header .toggle.open {{ transform: rotate(180deg); }}
.agent-body {{ padding: 0 1.25rem 1.25rem; display: none; }}
.agent-body.open {{ display: block; }}
.agent-row {{ display: flex; justify-content: space-between; padding: 0.35rem 0; border-bottom: 1px solid var(--border); font-size: 0.9rem; }}
.agent-row:last-child {{ border-bottom: none; }}
.agent-row .label {{ color: var(--text-dim); }}

/* Badges */
.badge {{
  display: inline-block; padding: 0.15rem 0.6rem; border-radius: 12px;
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.02em;
}}
.badge-green {{ background: var(--green-bg); color: var(--green); }}
.badge-yellow {{ background: var(--yellow-bg); color: var(--yellow); }}
.badge-red {{ background: var(--red-bg); color: var(--red); }}
.badge-blue {{ background: var(--blue-bg); color: var(--accent); }}
.badge-purple {{ background: var(--purple-bg); color: var(--purple); }}

/* Tables */
table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
th, td {{ padding: 0.65rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }}
th {{ color: var(--accent); font-weight: 600; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }}
tr:hover td {{ background: var(--bg3); }}

/* Charts */
.chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem; }}
.chart-box {{ background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.25rem; }}
.chart-box h4 {{ color: var(--text-dim); margin-bottom: 1rem; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }}
canvas {{ max-height: 280px; }}

/* Mermaid */
.mermaid-container {{
  background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 2rem; text-align: center; overflow-x: auto;
}}

/* Security score */
.score-ring {{ position: relative; width: 160px; height: 160px; margin: 0 auto 1rem; }}
.score-ring svg {{ transform: rotate(-90deg); }}
.score-value {{
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  font-size: 2.5rem; font-weight: 700;
}}

/* Decision timeline */
.decision {{ position: relative; padding-left: 2rem; margin-bottom: 1.5rem; }}
.decision::before {{
  content: ''; position: absolute; left: 0.5rem; top: 0; bottom: -1.5rem;
  width: 2px; background: var(--border);
}}
.decision:last-child::before {{ display: none; }}
.decision::after {{
  content: ''; position: absolute; left: 0.15rem; top: 0.5rem;
  width: 12px; height: 12px; border-radius: 50%;
  background: var(--accent); border: 2px solid var(--bg2);
}}
.decision h4 {{ color: var(--accent); font-size: 0.95rem; }}
.decision p {{ color: var(--text-dim); font-size: 0.9rem; margin-top: 0.25rem; }}
.decision .research {{ font-size: 0.8rem; color: var(--text-muted); margin-top: 0.35rem; font-style: italic; }}

/* Footer */
.footer {{ text-align: center; color: var(--text-muted); padding: 2rem 0; font-size: 0.8rem; border-top: 1px solid var(--border); margin-top: 2rem; }}

/* Responsive */
@media (max-width: 768px) {{
  .chart-row {{ grid-template-columns: 1fr; }}
  .agent-grid {{ grid-template-columns: 1fr; }}
  .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}

/* Print */
@media print {{
  body {{ background: #fff; color: #000; }}
  .tabs {{ display: none; }}
  .tab-content {{ display: block !important; }}
  .agent-body {{ display: block !important; }}
}}
</style>
</head>
<body>
<div class="container">

<!-- Header -->
<div class="header">
  <h1><span>&#9881;&#65039;</span> {blueprint.name}</h1>
  <p>{blueprint.description[:300]}</p>
  <div class="meta">
    <span>v{blueprint.version}</span>
    <span>Iteration {blueprint.iteration}</span>
    <span>{blueprint.created_at or 'Generated'}</span>
    <span>{blueprint.domain} domain</span>
  </div>
</div>

<!-- KPIs -->
<div class="kpi-grid">
  <div class="kpi">
    <div class="kpi-value">{summary['agents']}</div>
    <div class="kpi-label">Agents</div>
  </div>
  <div class="kpi">
    <div class="kpi-value" style="font-size:1.3rem;">{summary['pattern']}</div>
    <div class="kpi-label">Pattern</div>
  </div>
  <div class="kpi">
    <div class="kpi-value" style="font-size:1.3rem;">{summary['framework']}</div>
    <div class="kpi-label">Framework</div>
  </div>
  <div class="kpi">
    <div class="kpi-value">{summary['est_cost_per_request']}</div>
    <div class="kpi-label">Cost / Request</div>
  </div>
  <div class="kpi">
    <div class="kpi-value" style="color:{'var(--green)' if security_data['score'] >= 80 else 'var(--yellow)' if security_data['score'] >= 60 else 'var(--red)'};">{security_data['score']}%</div>
    <div class="kpi-label">Security Score</div>
  </div>
  <div class="kpi">
    <div class="kpi-value">{'&#10003;' if summary['has_hitl'] else '&#10007;'}</div>
    <div class="kpi-label">Human-in-Loop</div>
  </div>
</div>

<!-- Tabs -->
<div class="tabs">
  <div class="tab active" onclick="switchTab('arch')">Architecture</div>
  <div class="tab" onclick="switchTab('agents')">Agents</div>
  <div class="tab" onclick="switchTab('security')">Security</div>
  <div class="tab" onclick="switchTab('cost')">Cost Analysis</div>
  <div class="tab" onclick="switchTab('decisions')">Decisions</div>
  <div class="tab" onclick="switchTab('compliance')">Compliance</div>
</div>

<!-- Tab: Architecture -->
<div id="tab-arch" class="tab-content active">
  <div class="mermaid-container">
    <div class="mermaid">
{mermaid}
    </div>
  </div>
  <div class="card" style="margin-top:1rem;">
    <h3>Architecture Summary</h3>
    <table>
      <tr><td style="width:200px; color:var(--text-dim);">System Type</td><td>{blueprint.system_type.value}</td></tr>
      <tr><td style="color:var(--text-dim);">Pattern</td><td>{blueprint.pattern.value}</td></tr>
      <tr><td style="color:var(--text-dim);">Framework</td><td>{blueprint.framework}</td></tr>
      <tr><td style="color:var(--text-dim);">Scale</td><td>{blueprint.scale}</td></tr>
      <tr><td style="color:var(--text-dim);">Autonomy Level</td><td>{blueprint.autonomy.value}</td></tr>
      <tr><td style="color:var(--text-dim);">Infrastructure</td><td>{_infra_summary(blueprint)}</td></tr>
    </table>
  </div>
</div>

<!-- Tab: Agents -->
<div id="tab-agents" class="tab-content">
  <div class="agent-grid">
{agents_html}
  </div>
</div>

<!-- Tab: Security -->
<div id="tab-security" class="tab-content">
  <div class="chart-row">
    <div class="chart-box">
      <h4>Security Score</h4>
      <div class="score-ring">
        <svg width="160" height="160" viewBox="0 0 160 160">
          <circle cx="80" cy="80" r="70" fill="none" stroke="var(--border)" stroke-width="12"/>
          <circle cx="80" cy="80" r="70" fill="none"
            stroke="{'var(--green)' if security_data['score'] >= 80 else 'var(--yellow)' if security_data['score'] >= 60 else 'var(--red)'}"
            stroke-width="12" stroke-linecap="round"
            stroke-dasharray="{security_data['score'] / 100 * 440} 440"/>
        </svg>
        <div class="score-value" style="color:{'var(--green)' if security_data['score'] >= 80 else 'var(--yellow)' if security_data['score'] >= 60 else 'var(--red)'};">{security_data['score']}</div>
      </div>
      <p style="text-align:center; color:var(--text-dim); font-size:0.85rem;">
        {security_data['passed']}/{security_data['total']} checks passed
      </p>
    </div>
    <div class="chart-box">
      <h4>Findings by Category</h4>
      <canvas id="securityChart"></canvas>
    </div>
  </div>
  {security_data['table_html']}
</div>

<!-- Tab: Cost -->
<div id="tab-cost" class="tab-content">
  <div class="chart-row">
    <div class="chart-box">
      <h4>Cost per Agent (per request)</h4>
      <canvas id="costChart"></canvas>
    </div>
    <div class="chart-box">
      <h4>Monthly Projection (10K requests)</h4>
      <table>
        <tr><td style="color:var(--text-dim);">LLM Cost</td><td style="text-align:right; font-weight:700;">${cost_data['monthly_llm']:.2f}</td></tr>
        <tr><td style="color:var(--text-dim);">Infrastructure</td><td style="text-align:right;">${cost_data['infra']:.0f}</td></tr>
        <tr style="border-top:2px solid var(--accent);"><td style="color:var(--accent); font-weight:700;">Total</td><td style="text-align:right; font-weight:700; color:var(--accent);">${cost_data['monthly_llm'] + cost_data['infra']:.2f}/mo</td></tr>
      </table>
      <div style="margin-top:1.5rem;">
        <h4 style="color:var(--text-dim); font-size:0.85rem; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.5rem;">Optimization Tips</h4>
        {cost_data['tips_html']}
      </div>
    </div>
  </div>
</div>

<!-- Tab: Decisions -->
<div id="tab-decisions" class="tab-content">
  <div class="card">
{decisions_html}
  </div>
</div>

<!-- Tab: Compliance -->
<div id="tab-compliance" class="tab-content">
  {_compliance_section(blueprint)}
</div>

<!-- Footer -->
<div class="footer">
  Generated by <strong>CLean-agents</strong> v{blueprint.version} &middot;
  {blueprint.total_agents()} agents &middot;
  {blueprint.domain} domain &middot;
  {len(blueprint.decisions)} design decisions
</div>

</div>

<script>
mermaid.initialize({{
  startOnLoad: true, theme: 'dark',
  themeVariables: {{
    primaryColor: '#161b22', primaryTextColor: '#e6edf3',
    primaryBorderColor: '#58a6ff', lineColor: '#30363d',
    secondaryColor: '#1f2937', tertiaryColor: '#0d1117',
  }}
}});

function switchTab(id) {{
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + id).classList.add('active');
  event.target.classList.add('active');
}}

function toggleAgent(el) {{
  const body = el.nextElementSibling;
  const icon = el.querySelector('.toggle');
  body.classList.toggle('open');
  icon.classList.toggle('open');
}}

// Cost chart
const costCtx = document.getElementById('costChart');
if (costCtx) {{
  new Chart(costCtx, {{
    type: 'doughnut',
    data: {{
      labels: {cost_data['labels_json']},
      datasets: [{{ data: {cost_data['values_json']}, backgroundColor: ['#58a6ff','#3fb950','#d29922','#f85149','#bc8cff','#f778ba','#79c0ff'], borderColor: '#161b22', borderWidth: 2 }}]
    }},
    options: {{
      responsive: true, plugins: {{
        legend: {{ position: 'bottom', labels: {{ color: '#8b949e', padding: 12 }} }}
      }}
    }}
  }});
}}

// Security chart
const secCtx = document.getElementById('securityChart');
if (secCtx) {{
  new Chart(secCtx, {{
    type: 'bar',
    data: {{
      labels: {security_data['cat_labels_json']},
      datasets: [
        {{ label: 'Pass', data: {security_data['pass_json']}, backgroundColor: 'rgba(63,185,80,0.7)' }},
        {{ label: 'Warn', data: {security_data['warn_json']}, backgroundColor: 'rgba(210,153,34,0.7)' }},
        {{ label: 'Fail', data: {security_data['fail_json']}, backgroundColor: 'rgba(248,81,73,0.7)' }}
      ]
    }},
    options: {{
      responsive: true, scales: {{
        x: {{ stacked: true, ticks: {{ color: '#8b949e' }}, grid: {{ display: false }} }},
        y: {{ stacked: true, ticks: {{ color: '#8b949e' }}, grid: {{ color: '#30363d' }} }}
      }},
      plugins: {{ legend: {{ labels: {{ color: '#8b949e' }} }} }}
    }}
  }});
}}
</script>
</body>
</html>"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mermaid_diagram(bp: Blueprint) -> str:
    lines = ["graph TD"]
    orch = bp.get_orchestrator()
    specialists = [a for a in bp.agents if a.agent_type == "specialist"]
    guardians = [a for a in bp.agents if a.agent_type == "guardian"]
    classifiers = [a for a in bp.agents if a.agent_type == "classifier"]

    lines.append('    INPUT(["User Input"])')
    if orch:
        lines.append(f'    {orch.name}{{"⚙ {orch.name}"}}')
        lines.append(f'    INPUT --> {orch.name}')
        for a in specialists + classifiers:
            shape = f'["{a.name}"]' if a.agent_type == "specialist" else f'{{{{"{a.name}"}}}}'
            lines.append(f'    {a.name}{shape}')
            lines.append(f'    {orch.name} --> {a.name}')
        for g in guardians:
            lines.append(f'    {g.name}[/"🛡 {g.name}"/]')
            lines.append(f'    INPUT -.->|filter| {g.name}')
            lines.append(f'    {g.name} -.-> {orch.name}')
        lines.append('    OUTPUT(["Response"])')
        lines.append(f'    {orch.name} --> OUTPUT')
    else:
        prev = "INPUT"
        for a in bp.agents:
            lines.append(f'    {a.name}["{a.name}"]')
            lines.append(f'    {prev} --> {a.name}')
            prev = a.name
        lines.append('    OUTPUT(["Response"])')
        lines.append(f'    {prev} --> OUTPUT')

    lines.append('    style INPUT fill:#1f6feb,stroke:#58a6ff,color:#fff')
    lines.append('    style OUTPUT fill:#1f6feb,stroke:#58a6ff,color:#fff')
    if orch:
        lines.append(f'    style {orch.name} fill:#d29922,stroke:#e3b341,color:#000')
    for g in guardians:
        lines.append(f'    style {g.name} fill:#f85149,stroke:#f85149,color:#fff')
    return "\n".join(lines)


def _agents_section(bp: Blueprint) -> str:
    html = ""
    for a in bp.agents:
        type_class = {"orchestrator":"badge-yellow","specialist":"badge-blue","guardian":"badge-red","classifier":"badge-green","extractor":"badge-purple"}.get(a.agent_type, "badge-blue")
        mem = []
        if a.memory.short_term: mem.append("Short-term")
        if a.memory.episodic: mem.append("Episodic")
        if a.memory.semantic: mem.append("Semantic")
        if a.memory.procedural: mem.append("Procedural")
        if a.memory.graphrag: mem.append("GraphRAG")
        guard_in = ", ".join(a.guardrails.input) if a.guardrails.input else "None"
        guard_out = ", ".join(a.guardrails.output) if a.guardrails.output else "None"
        metrics_html = ", ".join(f"{m.name}: {m.target}" for m in a.metrics) if a.metrics else "None defined"

        html += f"""    <div class="agent-card">
      <div class="agent-header" onclick="toggleAgent(this)">
        <h4>{a.name} <span class="badge {type_class}">{a.agent_type}</span></h4>
        <span class="toggle">&#9660;</span>
      </div>
      <div class="agent-body">
        <div class="agent-row"><span class="label">Role</span><span>{a.role}</span></div>
        <div class="agent-row"><span class="label">Model</span><span>{a.model.primary}</span></div>
        <div class="agent-row"><span class="label">Reasoning</span><span>{a.reasoning.value}</span></div>
        <div class="agent-row"><span class="label">HITL</span><span>{a.hitl.value}</span></div>
        <div class="agent-row"><span class="label">Token Budget</span><span>{a.token_budget:,}</span></div>
        <div class="agent-row"><span class="label">Memory</span><span>{', '.join(mem) or 'Short-term only'}</span></div>
        <div class="agent-row"><span class="label">Input Guards</span><span>{guard_in}</span></div>
        <div class="agent-row"><span class="label">Output Guards</span><span>{guard_out}</span></div>
        <div class="agent-row"><span class="label">Metrics</span><span>{metrics_html}</span></div>
      </div>
    </div>
"""
    return html


def _decisions_section(bp: Blueprint) -> str:
    if not bp.decisions:
        return '<p style="color:var(--text-dim);">No design decisions recorded.</p>'
    html = ""
    for d in bp.decisions:
        research_html = ""
        if d.research:
            for r in d.research:
                year = f" ({r.year})" if r.year else ""
                research_html += f'<div class="research">{r.source}{year}: {r.finding}</div>'
        alts = ""
        if d.alternatives_considered:
            alts = f'<div style="font-size:0.8rem; color:var(--text-muted); margin-top:0.25rem;">Alternatives: {", ".join(d.alternatives_considered)}</div>'
        html += f"""    <div class="decision">
      <h4>{d.dimension}: {d.decision}</h4>
      <p>{d.justification}</p>
      {research_html}{alts}
    </div>
"""
    return html


def _cost_data(bp: Blueprint) -> dict:
    pricing = {
        "claude-opus-4-6": (5.0, 25.0), "claude-sonnet-4-6": (3.0, 15.0),
        "claude-haiku-4-5": (1.0, 5.0), "gpt-4o": (2.5, 10.0),
        "gpt-4o-mini": (0.15, 0.60), "gemini-2.5-pro": (4.0, 20.0), "gemini-2.5-flash": (0.30, 2.50),
    }
    labels, values, tips = [], [], []
    total = 0.0
    for a in bp.agents:
        ip, op = pricing.get(a.model.primary, (3.0, 15.0))
        cost = (a.total_input_tokens_estimate() / 1e6 * ip) + (a.token_budget / 1e6 * op)
        labels.append(a.name)
        values.append(round(cost, 5))
        total += cost
        if a.model.primary == "claude-opus-4-6" and a.agent_type != "orchestrator":
            tips.append(f'<div style="color:var(--yellow); font-size:0.85rem; margin-bottom:0.35rem;">&#8226; {a.name}: downgrade to Sonnet (save ~40%)</div>')
        if a.token_budget > 8000:
            tips.append(f'<div style="color:var(--yellow); font-size:0.85rem; margin-bottom:0.35rem;">&#8226; {a.name}: review {a.token_budget} token budget</div>')

    infra = 0.0
    if bp.infrastructure.vector_db: infra += 50
    if bp.infrastructure.graph_db: infra += 100
    if bp.infrastructure.message_queue: infra += 20
    if bp.infrastructure.observability: infra += 30

    if not tips:
        tips.append('<div style="color:var(--green); font-size:0.85rem;">&#10003; No obvious optimizations needed</div>')

    import json
    return {
        "labels_json": json.dumps(labels), "values_json": json.dumps(values),
        "total": total, "monthly_llm": total * 10000, "infra": infra,
        "tips_html": "\n      ".join(tips),
    }


def _security_data(bp: Blueprint) -> dict:
    import json
    cat_labels, pass_counts, warn_counts, fail_counts = [], [], [], []
    all_findings = []
    total_checks = 0
    total_fails = 0

    for cat in ATTACK_CATEGORIES:
        findings = _analyze_category(bp, cat)
        passes = len([f for f in findings if f["status"] == "PASS"])
        warns = len([f for f in findings if f["status"] == "WARN"])
        fails = len([f for f in findings if f["status"] == "FAIL"])
        total_checks += len(findings)
        total_fails += fails
        cat_labels.append(cat["id"])
        pass_counts.append(passes)
        warn_counts.append(warns)
        fail_counts.append(fails)
        for f in findings:
            if f["status"] in ("FAIL", "WARN"):
                all_findings.append({**f, "category": cat["id"], "cat_name": cat["name"]})

    score = round((total_checks - total_fails) / total_checks * 100) if total_checks else 100

    # Build findings table
    table_html = '<div class="card"><h3>Security Findings</h3>'
    if all_findings:
        table_html += '<table><thead><tr><th>Status</th><th>Category</th><th>Agent</th><th>Check</th><th>Detail</th></tr></thead><tbody>'
        for f in all_findings:
            icon = '<span style="color:var(--red);">&#10007;</span>' if f["status"] == "FAIL" else '<span style="color:var(--yellow);">&#9888;</span>'
            table_html += f'<tr><td>{icon}</td><td>{f["category"]}</td><td>{f["agent"]}</td><td>{f["check"]}</td><td style="color:var(--text-dim);">{f["detail"]}</td></tr>'
        table_html += '</tbody></table>'
    else:
        table_html += '<p style="color:var(--green);">All security checks passed.</p>'
    table_html += '</div>'

    return {
        "score": score, "total": total_checks, "passed": total_checks - total_fails,
        "cat_labels_json": json.dumps(cat_labels),
        "pass_json": json.dumps(pass_counts),
        "warn_json": json.dumps(warn_counts),
        "fail_json": json.dumps(fail_counts),
        "table_html": table_html,
    }


def _infra_summary(bp: Blueprint) -> str:
    parts = []
    if bp.infrastructure.vector_db: parts.append(f"Vector DB: {bp.infrastructure.vector_db}")
    if bp.infrastructure.graph_db: parts.append(f"Graph DB: {bp.infrastructure.graph_db}")
    if bp.infrastructure.message_queue: parts.append(f"Queue: {bp.infrastructure.message_queue}")
    if bp.infrastructure.observability: parts.append(f"Observability: {bp.infrastructure.observability}")
    return " | ".join(parts) if parts else "Minimal (no external services)"


def _compliance_section(bp: Blueprint) -> str:
    if not bp.compliance.regulations:
        return '<div class="card"><p style="color:var(--text-dim);">No compliance requirements configured. Add regulations during <code>clean-agents design</code>.</p></div>'

    from clean_agents.cli.module_cmds import _check_compliance_status

    mappings = {
        "GDPR": [("Art. 13-14 Transparency", "guardrails.output → explainability"), ("Art. 15 Right of access", "audit_trail → logging"), ("Art. 17 Right to erasure", "memory → deletion endpoint"), ("Art. 25 Data protection by design", "guardrails.input → pii_detection"), ("Art. 35 DPIA", "blueprint.decisions")],
        "HIPAA": [("§164.312(a) Access control", "agent auth + tool permissions"), ("§164.312(e) Transmission security", "TLS + encrypted queue"), ("§164.530(j) Audit trail", "immutable logging (6yr)")],
        "EU-AI-ACT": [("Art. 6 Risk classification", "blueprint.domain + scale"), ("Art. 11 Technical documentation", "blueprint.to_yaml()"), ("Art. 13 Transparency", "HITL + explainable outputs"), ("Art. 50 AI-generated content", "output watermarking")],
        "SOX": [("§302 Management cert", "HITL + approval workflows"), ("§404 Internal controls", "guardrails + audit trail"), ("§802 Record retention", "immutable logging (7yr)")],
        "SOC2": [("CC6.1 Logical access", "agent auth + RBAC"), ("CC7.2 System monitoring", "observability → alerting"), ("CC8.1 Change management", "blueprint versioning")],
    }

    html = ""
    for reg in bp.compliance.regulations:
        reg_upper = reg.upper().replace("-", "_").replace(" ", "_")
        reqs = mappings.get(reg.upper(), mappings.get(reg.upper().replace("_","-"), []))
        if not reqs:
            html += f'<div class="card"><h3>{reg.upper()}</h3><p style="color:var(--text-dim);">Detailed mapping available in v0.2</p></div>'
            continue

        html += f'<div class="card"><h3>{reg.upper()}</h3><table><thead><tr><th>Requirement</th><th>Component</th><th>Status</th></tr></thead><tbody>'
        for req_name, component in reqs:
            status = _check_compliance_status(component, bp)
            # Strip Rich markup for HTML
            if "Configured" in status:
                status_html = '<span class="badge badge-green">Configured</span>'
            elif "Missing" in status:
                status_html = '<span class="badge badge-red">Missing</span>'
            else:
                status_html = '<span class="badge badge-yellow">Review</span>'
            html += f'<tr><td>{req_name}</td><td style="color:var(--text-dim);">{component}</td><td>{status_html}</td></tr>'
        html += '</tbody></table></div>'

    return html
