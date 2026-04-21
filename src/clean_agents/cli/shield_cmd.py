"""clean-agents shield — CLean-shield security hardening analysis."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from clean_agents.core.blueprint import Blueprint
from clean_agents.core.config import Config

console = Console()

# Attack categories from CLean-shield
ATTACK_CATEGORIES = [
    {
        "id": "ATK-1",
        "name": "Prompt Injection",
        "description": "Direct/indirect manipulation of system prompts",
        "checks": ["system_prompt_isolation", "input_sanitization", "instruction_hierarchy"],
    },
    {
        "id": "ATK-2",
        "name": "Jailbreaking",
        "description": "Techniques to bypass safety constraints",
        "checks": ["role_boundary_enforcement", "output_monitoring", "multi_turn_tracking"],
    },
    {
        "id": "ATK-3",
        "name": "Data Extraction",
        "description": "Attempts to extract training data or system prompts",
        "checks": ["output_filtering", "system_prompt_protection", "rag_access_control"],
    },
    {
        "id": "ATK-4",
        "name": "Agent Manipulation",
        "description": "Exploiting agent-to-agent trust boundaries",
        "checks": ["inter_agent_auth", "message_validation", "privilege_boundaries"],
    },
    {
        "id": "ATK-5",
        "name": "Tool Abuse",
        "description": "Unauthorized tool execution or parameter injection",
        "checks": ["tool_permission_model", "parameter_validation", "execution_sandboxing"],
    },
    {
        "id": "ATK-6",
        "name": "Denial of Service",
        "description": "Resource exhaustion through recursive/expensive operations",
        "checks": ["rate_limiting", "token_budgets", "recursion_depth_limits"],
    },
    {
        "id": "ATK-7",
        "name": "Privacy Violation",
        "description": "PII leakage through context or output",
        "checks": ["pii_detection", "output_sanitization", "context_isolation"],
    },
]


def shield_cmd(
    path: str = typer.Option("", "--path", "-p", help="Blueprint file path"),
    attack: str = typer.Option("all", "--attack", "-a", help="Specific attack category (ATK-1..ATK-7 or all)"),
    output: str = typer.Option("", "--output", "-o", help="Save report to file"),
    ai: bool = typer.Option(False, "--ai", help="Enable AI-enhanced deep analysis (requires ANTHROPIC_API_KEY)"),
) -> None:
    """Run CLean-shield security hardening analysis.

    Analyzes the blueprint for security vulnerabilities across 7 attack categories
    and generates hardening recommendations.

    Use --ai for deep security analysis powered by Claude.
    """
    import os

    config = Config.discover()
    bp_path = Path(path) if path else config.blueprint_path()

    if not bp_path.exists():
        console.print("[red]Error:[/] No blueprint found. Run [bold]clean-agents design[/] first.")
        raise typer.Exit(1)

    blueprint = Blueprint.load(bp_path)

    console.print()
    console.print(Panel.fit(
        "[bold red]CLean-shield[/] — Security Hardening Analysis",
        border_style="red",
    ))
    console.print()

    # Filter attack categories
    if attack == "all":
        categories = ATTACK_CATEGORIES
    else:
        categories = [c for c in ATTACK_CATEGORIES if c["id"].lower() == attack.lower()]
        if not categories:
            console.print(f"[red]Unknown attack category: {attack}[/]")
            raise typer.Exit(1)

    total_issues = 0
    results = []

    for cat in categories:
        findings = _analyze_category(blueprint, cat)
        results.append((cat, findings))
        total_issues += len([f for f in findings if f["status"] == "FAIL"])

    # Render results
    for cat, findings in results:
        _render_category(console, cat, findings)

    # Summary
    console.print()
    total_checks = sum(len(cat["checks"]) * len(blueprint.agents) for cat in categories)
    passed = total_checks - total_issues
    color = "green" if total_issues == 0 else "yellow" if total_issues < 5 else "red"
    console.print(Panel(
        f"[{color}]{passed}/{total_checks} checks passed[/] — {total_issues} issues found",
        title="[bold]Security Score[/]",
        border_style=color,
    ))

    # AI-enhanced deep analysis
    if ai or os.environ.get("CLEAN_AGENTS_AI", ""):
        _ai_security_analysis(console, blueprint)

    if output:
        _export_report(Path(output), blueprint, results)
        console.print(f"\n[green]✓[/] Report saved to {output}")


def _ai_security_analysis(console: Console, blueprint: Blueprint) -> None:
    """Run AI-enhanced deep security analysis via ClaudeArchitect."""
    import os

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[yellow]⚠ ANTHROPIC_API_KEY not set — skipping AI analysis[/]")
        return

    try:
        from clean_agents.integrations.anthropic import ClaudeArchitect
    except ImportError:
        console.print("[yellow]⚠ anthropic package not installed — skipping AI analysis[/]")
        return

    console.print()
    console.print("[bold]AI-enhanced deep analysis...[/]", end="")

    try:
        architect = ClaudeArchitect(api_key=api_key)
        analysis = architect.analyze_security(blueprint)
        console.print(" [green]✓[/]")
        console.print()

        # Overall score
        score = analysis.get("overall_score", 0)
        score_color = "green" if score >= 80 else "yellow" if score >= 50 else "red"
        console.print(Panel(
            f"[{score_color}]AI Security Score: {score}/100[/{score_color}]",
            border_style=score_color,
        ))

        # Critical findings
        findings = analysis.get("critical_findings", [])
        if findings:
            console.print()
            console.print("[bold]AI-identified vulnerabilities:[/]")
            for f in findings:
                sev = f.get("severity", "medium")
                sev_c = {"critical": "red", "high": "red", "medium": "yellow", "low": "green"}.get(sev, "white")
                console.print(
                    f"  [{sev_c}]{sev.upper():>8}[/{sev_c}] "
                    f"[cyan]{f.get('agent', '?')}[/cyan]: {f.get('vulnerability', '')}"
                )
                if f.get("remediation"):
                    console.print(f"           [dim]→ {f['remediation']}[/]")

        # Attack scenarios
        scenarios = analysis.get("attack_scenarios", [])
        if scenarios:
            console.print()
            console.print("[bold]Attack scenarios identified:[/]")
            for s in scenarios:
                console.print(f"  [red]⚡[/] [bold]{s.get('name', '')}[/]")
                console.print(f"    Impact: {s.get('impact', '?')}")
                console.print(f"    Mitigation: {s.get('mitigation', '?')}")

        # Hardening checklist
        checklist = analysis.get("hardening_checklist", [])
        if checklist:
            console.print()
            console.print("[bold]Hardening checklist:[/]")
            for item in checklist:
                console.print(f"  [dim]☐[/] {item}")

        console.print()

    except Exception as exc:
        console.print(f" [red]✗[/] ({exc})")
        console.print()


def _analyze_category(blueprint: Blueprint, category: dict) -> list[dict]:
    """Analyze a single attack category against the blueprint."""
    findings = []
    for agent in blueprint.agents:
        for check in category["checks"]:
            status, detail = _run_check(agent, check)
            findings.append({
                "agent": agent.name,
                "check": check,
                "status": status,
                "detail": detail,
            })
    return findings


def _run_check(agent, check: str) -> tuple[str, str]:
    """Run a single security check against an agent."""
    # Input guardrails checks
    if check in ("injection_detection", "input_sanitization", "system_prompt_isolation"):
        if "injection_detection" in agent.guardrails.input:
            return "PASS", "Injection detection enabled"
        return "FAIL", f"Agent '{agent.name}' missing input injection detection"

    if check == "encoding_detection":
        if "encoding_detection" in agent.guardrails.input:
            return "PASS", "Encoding detection enabled"
        return "WARN", f"Agent '{agent.name}' has no encoding detection (recommended for multi-agent)"

    if check == "pii_detection":
        if "pii_detection" in agent.guardrails.input:
            return "PASS", "PII detection enabled on input"
        return "WARN", f"Agent '{agent.name}' has no PII detection on input"

    # Output checks
    if check in ("output_filtering", "output_sanitization", "output_monitoring"):
        if agent.guardrails.output:
            return "PASS", f"Output guardrails active: {', '.join(agent.guardrails.output)}"
        return "FAIL", f"Agent '{agent.name}' has no output guardrails"

    if check == "pii_masking":
        if "pii_masking" in agent.guardrails.output:
            return "PASS", "PII masking enabled on output"
        return "WARN", "No PII masking on output"

    # Token/resource checks
    if check in ("token_budgets", "rate_limiting"):
        if agent.token_budget and agent.token_budget <= 16000:
            return "PASS", f"Token budget set: {agent.token_budget}"
        return "WARN", f"Token budget is high ({agent.token_budget}) — consider tightening"

    if check == "recursion_depth_limits":
        return "WARN", "Recursion limits should be configured at framework level"

    # Tool checks
    if check == "tool_permission_model":
        high_risk = [t for t in agent.tools if t.risk_level.value in ("high", "critical")]
        if not high_risk:
            return "PASS", "No high-risk tools without approval"
        unapproved = [t for t in high_risk if not t.requires_approval]
        if unapproved:
            return "FAIL", f"High-risk tools without approval: {[t.name for t in unapproved]}"
        return "PASS", "All high-risk tools require approval"

    if check in ("parameter_validation", "execution_sandboxing"):
        return "PASS", "Framework-level control (verify in implementation)"

    # Agent-level checks
    if check == "inter_agent_auth":
        if agent.agent_type == "orchestrator":
            return "PASS", "Orchestrator manages agent trust boundaries"
        return "WARN", "Verify agent-to-agent auth at framework level"

    if check in ("message_validation", "privilege_boundaries"):
        if agent.guardrails.input:
            return "PASS", "Input validation active"
        return "WARN", "Add input validation for inter-agent messages"

    # HITL checks
    if check in ("role_boundary_enforcement", "instruction_hierarchy", "multi_turn_tracking"):
        if agent.hitl != "none":
            return "PASS", f"HITL mode: {agent.hitl}"
        return "WARN", "Consider HITL for sensitive operations"

    # RAG checks
    if check == "rag_access_control":
        if agent.memory.graphrag or agent.memory.episodic:
            return "WARN", "RAG enabled — ensure access control on retrieval"
        return "PASS", "No RAG/retrieval to secure"

    if check == "context_isolation":
        return "WARN", "Verify context isolation between users at runtime"

    if check == "system_prompt_protection":
        return "WARN", "Ensure system prompts are not exposed in tool outputs"

    if check == "schema_validation":
        if "schema_validation" in agent.guardrails.output:
            return "PASS", "Schema validation on output"
        return "WARN", "Add schema validation to enforce structured output"

    if check == "confidence_threshold":
        if "confidence_threshold" in agent.guardrails.output:
            return "PASS", "Confidence threshold active"
        return "WARN", "No confidence threshold — agent may return low-confidence answers"

    return "INFO", f"Check '{check}' — manual review required"


def _render_category(console: Console, category: dict, findings: list[dict]) -> None:
    """Render findings for a single attack category."""
    fails = [f for f in findings if f["status"] == "FAIL"]
    warns = [f for f in findings if f["status"] == "WARN"]
    passes = [f for f in findings if f["status"] == "PASS"]

    color = "red" if fails else "yellow" if warns else "green"
    console.print(Panel(
        f"[bold]{category['name']}[/]: {category['description']}",
        title=f"[bold]{category['id']}[/]",
        border_style=color,
    ))

    table = Table(show_header=True, header_style="bold", show_lines=False)
    table.add_column("Status", width=6)
    table.add_column("Agent", style="cyan")
    table.add_column("Check")
    table.add_column("Detail")

    status_icons = {"PASS": "[green]✓[/]", "FAIL": "[red]✗[/]", "WARN": "[yellow]![/]", "INFO": "[dim]i[/]"}

    for f in findings:
        if f["status"] in ("FAIL", "WARN"):
            table.add_row(
                status_icons[f["status"]],
                f["agent"],
                f["check"],
                f["detail"],
            )

    if not fails and not warns:
        console.print("  [green]All checks passed[/]")
    else:
        console.print(table)

    console.print()


def _export_report(path: Path, blueprint: Blueprint, results: list) -> None:
    """Export security report to file."""
    lines = [
        f"# CLean-shield Security Report",
        f"## Blueprint: {blueprint.name}",
        f"## Agents: {blueprint.total_agents()}",
        "",
    ]
    for cat, findings in results:
        fails = [f for f in findings if f["status"] == "FAIL"]
        warns = [f for f in findings if f["status"] == "WARN"]
        lines.append(f"### {cat['id']}: {cat['name']}")
        lines.append(f"Fails: {len(fails)} | Warnings: {len(warns)}")
        for f in findings:
            if f["status"] in ("FAIL", "WARN"):
                lines.append(f"  [{f['status']}] {f['agent']}: {f['detail']}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
