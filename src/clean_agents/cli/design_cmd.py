"""clean-agents design — interactive architecture design session.

Supports two modes:
  - Heuristic-only (default): fast, offline, no API key needed
  - AI-enhanced (--ai flag or ANTHROPIC_API_KEY present): multi-turn
    design conversation powered by ClaudeArchitect
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import typer
import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from clean_agents.core.config import Config
from clean_agents.engine.recommender import Recommender
from clean_agents.renderers.terminal import (
    render_agents_table,
    render_blueprint_summary,
    render_design_decisions,
)

if TYPE_CHECKING:
    from clean_agents.core.blueprint import Blueprint
    from clean_agents.integrations.anthropic import ClaudeArchitect

console = Console()

# ── Helpers ──────────────────────────────────────────────────────────────────


def _try_create_architect(
    model: str = "claude-sonnet-4-6",
) -> ClaudeArchitect | None:
    """Return a ClaudeArchitect if the SDK + key are available, else None."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        from clean_agents.integrations.anthropic import ClaudeArchitect

        return ClaudeArchitect(api_key=api_key, model=model)
    except ImportError:
        return None


def _module_suggest_artifacts(blueprint: Blueprint) -> None:
    """Phase-5 module: print per-agent artifact suggestions as a Rich table."""
    from clean_agents.crafters.base import ArtifactRef, ArtifactType

    table = Table(title="Suggested artifacts")
    table.add_column("Agent")
    table.add_column("Type")
    table.add_column("Name")
    table.add_column("Rationale")
    table.add_column("Priority")

    for agent in blueprint.agents:
        suggestions: list[ArtifactRef] = []
        role_lc = agent.role.lower()
        if any(w in role_lc for w in ("legal", "risk", "jargon", "medical", "financial")):
            suggestions.append(
                ArtifactRef(
                    artifact_type=ArtifactType.SKILL,
                    name=f"{agent.name.replace('_', '-')}-domain-patterns",
                    rationale="domain-specific jargon indicates a dedicated Skill",
                    priority="recommended",
                )
            )
        if agent.memory.graphrag:
            suggestions.append(
                ArtifactRef(
                    artifact_type=ArtifactType.MCP,
                    name=f"{agent.name.replace('_', '-')}-graph-mcp",
                    rationale="graphrag memory benefits from a typed MCP wrapper",
                    priority="recommended",
                )
            )
        for s in suggestions:
            table.add_row(
                agent.name,
                s.artifact_type.value,
                s.name,
                s.rationale,
                s.priority,
            )
            console.print(
                f"  run: clean-agents skill design --for-agent {agent.name} "
                f"--blueprint <blueprint.yaml>"
            )

    console.print(table)


def _ai_enhance_phase(
    console: Console,
    architect: ClaudeArchitect,
    blueprint: Blueprint,
) -> None:
    """Phase 2 — ask Claude to review the heuristic blueprint."""
    console.print("[bold]Phase 2:[/] AI-enhanced analysis...", end="")
    try:
        analysis = architect.enhance_blueprint(blueprint)
        console.print(" [green]✓[/]")
        console.print()

        # Suggestions
        suggestions = analysis.get("suggestions", [])
        if suggestions:
            console.print(Panel("[bold]AI Improvement Suggestions[/]", border_style="magenta"))
            for _i, s in enumerate(suggestions, 1):
                prio = s.get("priority", "medium")
                prio_color = {"high": "red", "medium": "yellow", "low": "green"}.get(prio, "white")
                console.print(
                    f"  [{prio_color}]{prio.upper()}[/{prio_color}]  "
                    f"[bold]{s.get('title', '')}[/] — {s.get('description', '')}"
                )
            console.print()

        # Risk assessment
        risk = analysis.get("risk_assessment", {})
        if risk:
            console.print("[bold]Risk assessment:[/]")
            for axis in ("security", "reliability", "cost"):
                detail = risk.get(axis, {})
                if isinstance(detail, dict):
                    lvl = detail.get("level", "?")
                    lvl_c = {"high": "red", "medium": "yellow", "low": "green"}.get(
                        lvl, "white"
                    )
                    console.print(
                        f"  [{lvl_c}]{lvl.upper():>6}[/{lvl_c}]  {axis}: "
                        f"{detail.get('details', '')}"
                    )
            console.print()

        # Missing components
        missing = analysis.get("missing_components", [])
        if missing:
            console.print("[bold]Missing components:[/]")
            for m in missing:
                console.print(f"  [yellow]→[/] {m}")
            console.print()

    except Exception as exc:
        console.print(f" [red]✗[/] ({exc})")
        console.print("[dim]Continuing with heuristic results.[/]")
        console.print()


def _try_auto_apply(
    console: Console,
    blueprint: Blueprint,
    response_text: str,
) -> Blueprint:
    """Try to extract YAML from Claude response and apply updates to the blueprint.

    Attempts to:
    1. Extract YAML blocks (```yaml ... ```) from the response
    2. Parse the YAML
    3. Apply partial updates to the blueprint
    4. Track iteration and changelog

    Falls back gracefully if YAML is malformed.
    """
    # Try to extract YAML block
    yaml_pattern = r"```yaml\s*(.*?)\s*```"
    matches = re.findall(yaml_pattern, response_text, re.DOTALL)

    if not matches:
        console.print("[dim]No YAML changes found in response.[/]")
        return blueprint

    yaml_text = matches[0]

    # Try to parse YAML
    try:
        changes = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        console.print(f"[yellow]Could not parse YAML changes:[/] {e}")
        console.print("[dim]Skipping auto-apply. Describe the change and I'll regenerate.[/]")
        return blueprint

    if not isinstance(changes, dict):
        console.print("[yellow]YAML must be a dictionary (object).[/]")
        return blueprint

    # Track what we'll change
    changes_made = []

    try:
        # 1. Update agents (merge matching agents by name)
        if "agents" in changes and isinstance(changes["agents"], list):
            for agent_update in changes["agents"]:
                if not isinstance(agent_update, dict) or "name" not in agent_update:
                    continue
                agent_name = agent_update["name"]
                existing_agent = blueprint.get_agent(agent_name)
                if existing_agent:
                    # Merge fields from update into existing agent
                    for key, value in agent_update.items():
                        if key != "name" and value is not None:
                            try:
                                setattr(existing_agent, key, value)
                                changes_made.append(f"Updated agent '{agent_name}': {key}")
                            except Exception as e:
                                console.print(f"[dim]Skipped setting {agent_name}.{key}: {e}[/]")
                else:
                    console.print(f"[dim]Agent '{agent_name}' not found, skipping.[/]")

        # 2. Update framework
        if "framework" in changes and isinstance(changes["framework"], str):
            old_fw = blueprint.framework
            blueprint.framework = changes["framework"]
            changes_made.append(f"Framework: {old_fw} → {blueprint.framework}")

        # 3. Update pattern
        if "pattern" in changes and isinstance(changes["pattern"], str):
            old_pat = blueprint.pattern
            blueprint.pattern = changes["pattern"]  # type: ignore
            changes_made.append(f"Pattern: {old_pat} → {blueprint.pattern}")

        # 4. Merge infrastructure
        if "infrastructure" in changes and isinstance(changes["infrastructure"], dict):
            for key, value in changes["infrastructure"].items():
                if value is not None:
                    try:
                        setattr(blueprint.infrastructure, key, value)
                        changes_made.append(f"Infrastructure: {key} = {value}")
                    except Exception as e:
                        console.print(f"[dim]Skipped infra.{key}: {e}[/]")

        # 5. Merge compliance
        if "compliance" in changes and isinstance(changes["compliance"], dict):
            for key, value in changes["compliance"].items():
                if value is not None:
                    try:
                        setattr(blueprint.compliance, key, value)
                        changes_made.append(f"Compliance: {key} = {value}")
                    except Exception as e:
                        console.print(f"[dim]Skipped compliance.{key}: {e}[/]")

    except Exception as e:
        console.print(f"[yellow]Error applying changes:[/] {e}")
        console.print("[dim]Returning original blueprint.[/]")
        return blueprint

    # If we made changes, update iteration and changelog
    if changes_made:
        blueprint.iteration += 1
        timestamp = datetime.now().isoformat()
        changelog_entry = f"Iteration {blueprint.iteration} ({timestamp}): " + "; ".join(
            changes_made[:3]
        )
        if len(changes_made) > 3:
            changelog_entry += f" (and {len(changes_made) - 3} more)"
        blueprint.changelog.append(changelog_entry)
        blueprint.updated_at = timestamp

        console.print("[green]✓[/] Applied changes:")
        for change in changes_made[:5]:  # Show first 5 changes
            console.print(f"  • {change}")
        if len(changes_made) > 5:
            console.print(f"  ... and {len(changes_made) - 5} more")
    else:
        console.print("[dim]No valid changes found to apply.[/]")

    return blueprint


def _iterate_loop(
    console: Console,
    architect: ClaudeArchitect,
    blueprint: Blueprint,
    config: Config,
    save_path: Path | None,
) -> Blueprint:
    """Multi-turn design iteration powered by Claude."""
    history: list[dict] = []

    console.print(
        Panel(
            "[bold cyan]Design Iteration Mode[/]\n\n"
            "Chat with Claude to refine your architecture.\n"
            "Examples:\n"
            '  • "Change the framework to CrewAI"\n'
            '  • "Add a QA agent that reviews outputs"\n'
            '  • "Make it cheaper — I have a $50/mo budget"\n'
            '  • "Add HIPAA compliance"\n\n'
            "Type [bold]done[/] to finish, [bold]show[/] to redisplay the blueprint.",
            border_style="cyan",
        )
    )
    console.print()

    while True:
        feedback = Prompt.ask("[bold magenta]iterate ›[/]")
        if not feedback.strip():
            continue

        cmd = feedback.strip().lower()
        if cmd in ("done", "exit", "quit", "q"):
            break

        if cmd == "show":
            render_blueprint_summary(console, blueprint)
            console.print()
            render_agents_table(console, blueprint)
            console.print()
            continue

        if cmd == "save":
            if save_path:
                blueprint.save(save_path)
                console.print(f"[green]✓[/] Saved to {save_path}")
            else:
                sp = config.blueprint_path()
                blueprint.save(sp)
                console.print(f"[green]✓[/] Saved to {sp}")
            continue

        if cmd == "cost":
            cost = blueprint.estimated_cost_per_request()
            console.print(f"[bold]Current cost/request:[/] ${cost:.4f}")
            continue

        # Send to Claude
        console.print("[dim]Thinking…[/]", end="")
        try:
            response_text = architect.iterate_design(blueprint, feedback, history)

            # Update conversation history
            history.append({"role": "user", "content": feedback})
            history.append({"role": "assistant", "content": response_text})

            console.print("\r", end="")
            console.print(Panel(Markdown(response_text), border_style="magenta", title="Claude"))
            console.print()

            # Offer to apply
            if Confirm.ask("[bold]Apply suggested changes automatically?[/]", default=False):
                blueprint = _try_auto_apply(console, blueprint, response_text)
                console.print()

        except Exception as exc:
            console.print(f"\r[red]Error:[/] {exc}")
            console.print()

    return blueprint


# ── Main command ─────────────────────────────────────────────────────────────


def design_cmd(
    description: str = typer.Option(
        "", "--desc", "-d", help="System description (skip interactive prompt)"
    ),
    language: str = typer.Option("en", "--lang", "-l", help="Output language (en, es, pt, fr, de)"),
    output: str = typer.Option("", "--output", "-o", help="Save blueprint to file"),
    no_interactive: bool = typer.Option(False, "--no-interactive", help="Non-interactive mode"),
    ai: bool = typer.Option(
        False, "--ai", help="Enable AI-enhanced mode (requires ANTHROPIC_API_KEY)"
    ),
    ai_model: str = typer.Option(
        "claude-sonnet-4-6", "--ai-model", help="Model for AI-enhanced analysis"
    ),
    blueprint_path: str = typer.Option(
        "", "--blueprint", help="Path to an existing blueprint.yaml (used by --module)"
    ),
    module: str = typer.Option(
        "", "--module", help="Run a Phase-5 module (e.g., 'suggest-artifacts')"
    ),
) -> None:
    """Start an interactive architecture design session.

    Describe your system and get an evidence-backed architecture recommendation.
    Use --ai to enable multi-turn design iteration powered by Claude.
    """
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]CLean-agents[/] — Architecture Design Session",
            border_style="cyan",
        )
    )
    console.print()

    # Phase-5 module short-circuit (no heuristic run needed)
    if module:
        if not blueprint_path:
            console.print("[red]Error:[/] --module requires --blueprint")
            raise typer.Exit(2)
        from clean_agents.core.blueprint import Blueprint

        bp = Blueprint.load(Path(blueprint_path))
        if module == "suggest-artifacts":
            _module_suggest_artifacts(bp)
            return
        console.print(f"[red]Error:[/] unknown --module value {module!r}")
        raise typer.Exit(2)

    # Load config
    config = Config.discover()

    # Resolve AI mode
    architect: ClaudeArchitect | None = None
    if ai or os.environ.get("CLEAN_AGENTS_AI", ""):
        architect = _try_create_architect(model=ai_model)
        if architect:
            console.print("[green]✓[/] AI-enhanced mode active")
        else:
            console.print(
                "[yellow]⚠ AI mode requested but ANTHROPIC_API_KEY not set or "
                "anthropic package not installed.[/]"
            )
            console.print("[dim]Falling back to heuristic mode.[/]")
        console.print()

    # Get description
    if not description:
        if no_interactive:
            console.print("[red]Error:[/] --desc required in non-interactive mode")
            raise typer.Exit(1)

        console.print("[bold]Describe the agentic system you want to build.[/]")
        console.print("[dim]Include: domain, responsibilities, scale, compliance needs, etc.[/]")
        console.print()
        description = Prompt.ask("[bold cyan]›[/]")
        console.print()

    if not description.strip():
        console.print("[red]Error:[/] Description cannot be empty")
        raise typer.Exit(1)

    # Phase 1: Heuristic recommendation (always runs — fast, free)
    console.print("[bold]Phase 1:[/] Analyzing requirements...", end="")
    recommender = Recommender()
    blueprint = recommender.recommend(description, language=language)
    blueprint.created_at = datetime.now().isoformat()
    console.print(" [green]✓[/]")
    console.print()

    # Display heuristic results
    render_blueprint_summary(console, blueprint)
    console.print()
    render_agents_table(console, blueprint)
    console.print()
    render_design_decisions(console, blueprint)
    console.print()

    # Cost estimate
    cost = blueprint.estimated_cost_per_request()
    console.print(f"[bold]Estimated cost per request:[/] ${cost:.4f}")
    console.print()

    # Phase 2: AI enhancement (optional)
    if architect:
        _ai_enhance_phase(console, architect, blueprint)

    # Save blueprint
    save_path: Path | None = None
    if output:
        save_path = Path(output)
    elif not no_interactive:
        if Confirm.ask("[bold]Save blueprint?[/]", default=True):
            save_path = config.blueprint_path()
    else:
        save_path = config.blueprint_path()

    if save_path:
        blueprint.save(save_path)
        console.print(f"[green]✓[/] Blueprint saved to [bold]{save_path}[/]")
        console.print()

    # Phase 3: Multi-turn iteration (AI mode + interactive)
    if architect and not no_interactive:
        if Confirm.ask("[bold]Enter design iteration mode?[/]", default=True):
            blueprint = _iterate_loop(console, architect, blueprint, config, save_path)
            # Re-save after iteration
            if save_path:
                blueprint.save(save_path)
                console.print(f"[green]✓[/] Final blueprint saved to [bold]{save_path}[/]")
                console.print()

    # Offer on-demand modules
    if not no_interactive:
        _offer_modules(console, blueprint)


def _offer_modules(console: Console, blueprint: Blueprint) -> None:
    """Offer on-demand modules after initial design."""
    console.print("[bold]Available modules:[/]")
    console.print()

    modules = [
        ("cost", "Cost Simulator", "Detailed per-request and monthly cost projections"),
        ("models", "Model Chooser", "Benchmark-based model selection per agent"),
        ("prompts", "Prompt Lab", "Optimized prompt templates per agent role"),
        ("eval", "Eval Suite", "Evaluation framework with test cases"),
        ("observe", "Observability", "Monitoring, tracing, and alerting blueprint"),
        ("shield", "CLean-shield", "Security hardening + adversarial testing"),
        ("comply", "Compliance", "Regulation-to-component mapping"),
        ("load", "Load Testing", "Performance testing scenarios and configs"),
    ]

    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=3)
    table.add_column("Command", style="cyan")
    table.add_column("Module", style="bold")
    table.add_column("Description")

    for i, (cmd, name, desc) in enumerate(modules, 1):
        table.add_row(str(i), f"clean-agents {cmd}", name, desc)

    console.print(table)
    console.print()
    console.print("[dim]Run any module command to activate it against the current blueprint.[/]")
    console.print()
