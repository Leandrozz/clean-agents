"""clean-agents diff — compare two blueprints side-by-side."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from clean_agents.core.blueprint import Blueprint

console = Console()


def _build_diff_structure(blueprint: Blueprint, other: Blueprint) -> dict[str, Any]:
    """Build a structured diff output comparing two blueprints."""
    diff = {
        "metadata_changes": [],
        "agents_added": [],
        "agents_removed": [],
        "agents_changed": [],
        "cost_delta": {},
    }

    # Metadata changes
    metadata_fields = [
        ("name", "name"),
        ("system_type", "system_type"),
        ("pattern", "pattern"),
        ("framework", "framework"),
        ("domain", "domain"),
        ("scale", "scale"),
    ]

    for field_name, attr_name in metadata_fields:
        old_val = getattr(blueprint, attr_name)
        new_val = getattr(other, attr_name)

        # Handle enum values
        if hasattr(old_val, "value"):
            old_val = old_val.value
        if hasattr(new_val, "value"):
            new_val = new_val.value

        if old_val != new_val:
            diff["metadata_changes"].append({
                "field": field_name,
                "old": old_val,
                "new": new_val,
            })

    # Agent changes
    old_agents = {a.name: a for a in blueprint.agents}
    new_agents = {a.name: a for a in other.agents}

    added = set(new_agents.keys()) - set(old_agents.keys())
    removed = set(old_agents.keys()) - set(new_agents.keys())
    changed = set(old_agents.keys()) & set(new_agents.keys())

    # Agents added
    for name in sorted(added):
        agent = new_agents[name]
        diff["agents_added"].append({
            "name": name,
            "agent_type": agent.agent_type,
            "model": agent.model.primary,
            "token_budget": agent.token_budget,
        })

    # Agents removed
    for name in sorted(removed):
        agent = old_agents[name]
        diff["agents_removed"].append({
            "name": name,
            "agent_type": agent.agent_type,
            "model": agent.model.primary,
            "token_budget": agent.token_budget,
        })

    # Agents changed
    for name in sorted(changed):
        old_agent = old_agents[name]
        new_agent = new_agents[name]
        changes = []

        if old_agent.model.primary != new_agent.model.primary:
            changes.append({
                "field": "model.primary",
                "old": old_agent.model.primary,
                "new": new_agent.model.primary,
            })
        if old_agent.reasoning != new_agent.reasoning:
            changes.append({
                "field": "reasoning",
                "old": old_agent.reasoning.value,
                "new": new_agent.reasoning.value,
            })
        if old_agent.token_budget != new_agent.token_budget:
            changes.append({
                "field": "token_budget",
                "old": old_agent.token_budget,
                "new": new_agent.token_budget,
            })
        if old_agent.hitl != new_agent.hitl:
            changes.append({
                "field": "hitl",
                "old": old_agent.hitl.value,
                "new": new_agent.hitl.value,
            })

        # Check guardrails
        old_gr = len(old_agent.guardrails.input) + len(old_agent.guardrails.output)
        new_gr = len(new_agent.guardrails.input) + len(new_agent.guardrails.output)
        if old_gr != new_gr:
            changes.append({
                "field": "guardrails",
                "old": old_gr,
                "new": new_gr,
            })

        if changes:
            diff["agents_changed"].append({
                "name": name,
                "changes": changes,
            })

    # Cost delta
    old_cost = blueprint.estimated_cost_per_request()
    new_cost = other.estimated_cost_per_request()
    cost_delta = new_cost - old_cost
    percent_change = (cost_delta / old_cost * 100) if old_cost > 0 else 0.0

    diff["cost_delta"] = {
        "old": round(old_cost, 6),
        "new": round(new_cost, 6),
        "delta": round(cost_delta, 6),
        "percent": round(percent_change, 1),
    }

    return diff


def _render_diff_rich(console: Console, diff: dict[str, Any]) -> None:
    """Render diff as Rich output."""
    console.print()
    console.print("[bold cyan]Blueprint Diff[/]")
    console.print()

    # Metadata changes
    if diff["metadata_changes"]:
        console.print("[bold]Metadata Changes:[/]")
        for change in diff["metadata_changes"]:
            console.print(f"  {change['field']}: [red]{change['old']}[/] → [green]{change['new']}[/]")
        console.print()

    # Agents added
    if diff["agents_added"]:
        console.print("[bold green]Agents Added:[/]")
        for agent in diff["agents_added"]:
            console.print(f"  [green]+ {agent['name']}[/] ({agent['agent_type']}, {agent['model']}, "
                         f"tokens: {agent['token_budget']})")
        console.print()

    # Agents removed
    if diff["agents_removed"]:
        console.print("[bold red]Agents Removed:[/]")
        for agent in diff["agents_removed"]:
            console.print(f"  [red]- {agent['name']}[/] ({agent['agent_type']}, {agent['model']}, "
                         f"tokens: {agent['token_budget']})")
        console.print()

    # Agents changed
    if diff["agents_changed"]:
        console.print("[bold yellow]Agents Changed:[/]")
        for agent_change in diff["agents_changed"]:
            console.print(f"  [yellow]~ {agent_change['name']}[/]")
            for change in agent_change["changes"]:
                console.print(f"    {change['field']}: [red]{change['old']}[/] → [green]{change['new']}[/]")
        console.print()

    # Cost difference
    cost = diff["cost_delta"]
    console.print("[bold]Cost per Request:[/]")
    if cost["delta"] == 0:
        console.print(f"  [cyan]No change:[/] ${cost['old']:.6f}")
    else:
        direction = "[green]↓[/]" if cost["delta"] < 0 else "[red]↑[/]"
        console.print(f"  {direction} ${cost['old']:.6f} → ${cost['new']:.6f} "
                     f"(Δ {cost['delta']:+.6f}, {cost['percent']:+.1f}%)")
    console.print()

    # Summary
    if not any([diff["metadata_changes"], diff["agents_added"], diff["agents_removed"], diff["agents_changed"]]):
        console.print("[cyan]No differences found.[/]")


def _render_diff_yaml(console: Console, diff: dict[str, Any]) -> None:
    """Render diff as YAML."""
    import yaml
    yaml_str = yaml.dump(diff, default_flow_style=False, allow_unicode=True, sort_keys=False)
    console.print(Syntax(yaml_str, "yaml", theme="monokai"))


def _render_diff_json(console: Console, diff: dict[str, Any]) -> None:
    """Render diff as JSON."""
    json_str = json.dumps(diff, indent=2)
    console.print(Syntax(json_str, "json", theme="monokai"))


def diff_cmd(
    file_a: str = typer.Argument(..., help="First blueprint path"),
    file_b: str = typer.Argument(..., help="Second blueprint path"),
    output: str = typer.Option("", "--output", "-o", help="Save diff to file"),
    format: str = typer.Option("rich", "--format", "-f", help="Output format: rich | yaml | json"),
) -> None:
    """Compare two blueprints side-by-side."""
    path_a = Path(file_a)
    path_b = Path(file_b)

    if not path_a.exists():
        console.print(f"[red]Error:[/] First blueprint not found at {file_a}")
        raise typer.Exit(1)

    if not path_b.exists():
        console.print(f"[red]Error:[/] Second blueprint not found at {file_b}")
        raise typer.Exit(1)

    blueprint_a = Blueprint.load(path_a)
    blueprint_b = Blueprint.load(path_b)

    diff = _build_diff_structure(blueprint_a, blueprint_b)

    # Render based on format
    if format == "yaml":
        import yaml
        yaml_str = yaml.dump(diff, default_flow_style=False, allow_unicode=True, sort_keys=False)
        output_str = yaml_str
    elif format == "json":
        output_str = json.dumps(diff, indent=2)
    else:  # rich
        # For rich format, we render to console and optionally save
        _render_diff_rich(console, diff)
        if output:
            with open(output, "w", encoding="utf-8") as f:
                # Save as JSON for rich format
                f.write(json.dumps(diff, indent=2))
            console.print(f"[green]✓[/] Diff saved to {output}")
        return

    # For yaml and json formats
    if format == "yaml":
        _render_diff_yaml(console, diff)
    else:
        _render_diff_json(console, diff)

    # Save to file if requested
    if output:
        Path(output).write_text(output_str, encoding="utf-8")
        console.print(f"[green]✓[/] Diff saved to {output}")
