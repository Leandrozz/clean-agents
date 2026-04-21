"""clean-agents blueprint — view, export, or diff the current blueprint."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel

from clean_agents.core.blueprint import Blueprint
from clean_agents.core.config import Config
from clean_agents.renderers.terminal import render_blueprint_summary, render_agents_table

console = Console()


def _render_diff(console: Console, blueprint: Blueprint, other: Blueprint) -> None:
    """Render a side-by-side diff of two blueprints."""
    console.print()
    console.print("[bold cyan]Blueprint Diff[/]")
    console.print()

    # Metadata changes
    metadata_changes = []
    if blueprint.name != other.name:
        metadata_changes.append(("name", blueprint.name, other.name))
    if blueprint.system_type != other.system_type:
        metadata_changes.append(("system_type", blueprint.system_type.value, other.system_type.value))
    if blueprint.pattern != other.pattern:
        metadata_changes.append(("pattern", blueprint.pattern.value, other.pattern.value))
    if blueprint.framework != other.framework:
        metadata_changes.append(("framework", blueprint.framework, other.framework))
    if blueprint.domain != other.domain:
        metadata_changes.append(("domain", blueprint.domain, other.domain))
    if blueprint.scale != other.scale:
        metadata_changes.append(("scale", blueprint.scale, other.scale))

    if metadata_changes:
        console.print("[bold]Metadata Changes:[/]")
        for field, old_val, new_val in metadata_changes:
            console.print(f"  {field}: [red]{old_val}[/] → [green]{new_val}[/]")
        console.print()

    # Agent changes
    old_agents = {a.name: a for a in blueprint.agents}
    new_agents = {a.name: a for a in other.agents}

    added = set(new_agents.keys()) - set(old_agents.keys())
    removed = set(old_agents.keys()) - set(new_agents.keys())
    changed = set(old_agents.keys()) & set(new_agents.keys())

    # Agents added
    if added:
        console.print("[bold green]Agents Added:[/]")
        for name in sorted(added):
            agent = new_agents[name]
            console.print(f"  [green]+ {name}[/] ({agent.agent_type}, {agent.model.primary}, tokens: {agent.token_budget})")
        console.print()

    # Agents removed
    if removed:
        console.print("[bold red]Agents Removed:[/]")
        for name in sorted(removed):
            agent = old_agents[name]
            console.print(f"  [red]- {name}[/] ({agent.agent_type}, {agent.model.primary}, tokens: {agent.token_budget})")
        console.print()

    # Agents changed
    agent_changes = []
    for name in sorted(changed):
        old_agent = old_agents[name]
        new_agent = new_agents[name]
        changes = []

        if old_agent.model.primary != new_agent.model.primary:
            changes.append(("model.primary", old_agent.model.primary, new_agent.model.primary))
        if old_agent.reasoning != new_agent.reasoning:
            changes.append(("reasoning", old_agent.reasoning.value, new_agent.reasoning.value))
        if old_agent.token_budget != new_agent.token_budget:
            changes.append(("token_budget", str(old_agent.token_budget), str(new_agent.token_budget)))
        if old_agent.hitl != new_agent.hitl:
            changes.append(("hitl", old_agent.hitl.value, new_agent.hitl.value))

        # Check guardrails
        old_gr = len(old_agent.guardrails.input) + len(old_agent.guardrails.output)
        new_gr = len(new_agent.guardrails.input) + len(new_agent.guardrails.output)
        if old_gr != new_gr:
            changes.append(("guardrails", str(old_gr), str(new_gr)))

        if changes:
            agent_changes.append((name, changes))

    if agent_changes:
        console.print("[bold yellow]Agents Changed:[/]")
        for name, changes in agent_changes:
            console.print(f"  [yellow]~ {name}[/]")
            for field, old_val, new_val in changes:
                console.print(f"    {field}: [red]{old_val}[/] → [green]{new_val}[/]")
        console.print()

    # Cost difference
    old_cost = blueprint.estimated_cost_per_request()
    new_cost = other.estimated_cost_per_request()
    cost_delta = new_cost - old_cost
    percent_change = (cost_delta / old_cost * 100) if old_cost > 0 else 0

    console.print("[bold]Cost per Request:[/]")
    if cost_delta == 0:
        console.print(f"  [cyan]No change:[/] ${old_cost:.6f}")
    else:
        direction = "[green]↓[/]" if cost_delta < 0 else "[red]↑[/]"
        console.print(f"  {direction} ${old_cost:.6f} → ${new_cost:.6f} (Δ {cost_delta:+.6f}, {percent_change:+.1f}%)")
    console.print()

    # Summary
    if not any([metadata_changes, added, removed, agent_changes]):
        console.print("[cyan]No differences found.[/]")
    else:
        total_agents_old = len(old_agents)
        total_agents_new = len(new_agents)
        console.print(f"[cyan]Summary:[/] {total_agents_old} → {total_agents_new} agents | "
                      f"Cost: ${old_cost:.6f} → ${new_cost:.6f}")


def blueprint_cmd(
    path: str = typer.Option("", "--path", "-p", help="Blueprint file path"),
    fmt: str = typer.Option("summary", "--format", "-f", help="Output format: summary | yaml | json"),
    export: str = typer.Option("", "--export", "-e", help="Export to file"),
    html: bool = typer.Option(False, "--html", help="Export as HTML report"),
    diff: str = typer.Option("", "--diff", help="Path to second blueprint to compare against"),
) -> None:
    """View, export, or inspect the current blueprint."""
    config = Config.discover()
    bp_path = Path(path) if path else config.blueprint_path()

    if not bp_path.exists():
        console.print("[red]Error:[/] No blueprint found.")
        console.print("[dim]Run [bold]clean-agents design[/] first to create one.[/]")
        raise typer.Exit(1)

    blueprint = Blueprint.load(bp_path)

    # Handle diff mode
    if diff:
        diff_path = Path(diff)
        if not diff_path.exists():
            console.print(f"[red]Error:[/] Diff blueprint not found at {diff}")
            raise typer.Exit(1)
        other_blueprint = Blueprint.load(diff_path)
        _render_diff(console, blueprint, other_blueprint)
        return

    if fmt == "yaml":
        yaml_str = blueprint.to_yaml()
        if export:
            Path(export).write_text(yaml_str, encoding="utf-8")
            console.print(f"[green]✓[/] Exported YAML to {export}")
        else:
            console.print(Syntax(yaml_str, "yaml", theme="monokai"))

    elif fmt == "json":
        import json
        json_str = json.dumps(blueprint.model_dump(mode="json", exclude_none=True), indent=2)
        if export:
            Path(export).write_text(json_str, encoding="utf-8")
            console.print(f"[green]✓[/] Exported JSON to {export}")
        else:
            console.print(Syntax(json_str, "json", theme="monokai"))

    elif html:
        from clean_agents.renderers.html import render_html_report
        html_content = render_html_report(blueprint)
        out_path = Path(export) if export else config.outputs_path() / f"{blueprint.name}.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html_content, encoding="utf-8")
        console.print(f"[green]✓[/] HTML report saved to [bold]{out_path}[/]")

    else:
        # summary (default)
        console.print()
        render_blueprint_summary(console, blueprint)
        console.print()
        render_agents_table(console, blueprint)
        console.print()
