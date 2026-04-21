"""clean-agents init — project initialization command."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from clean_agents.core.config import Config, LLMConfig

console = Console()


def init_cmd(
    name: str = typer.Option("", "--name", "-n", help="Project name"),
    directory: str = typer.Option(".", "--dir", "-d", help="Project directory"),
    provider: str = typer.Option("anthropic", "--provider", "-p", help="LLM provider"),
    model: str = typer.Option("claude-sonnet-4-6", "--model", "-m", help="Default model"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing project"),
) -> None:
    """Initialize a new CLean-agents project.

    Creates the .clean-agents/ directory with config, blueprints, and scaffolding.
    """
    console.print()
    console.print(Panel.fit(
        "[bold cyan]CLean-agents[/] — Project Initialization",
        border_style="cyan",
    ))

    base = Path(directory).resolve()

    # Interactive name if not provided
    if not name:
        name = Prompt.ask(
            "[bold]Project name[/]",
            default=base.name,
        )

    project_dir = base / ".clean-agents"

    if project_dir.exists() and not force:
        if not Confirm.ask(f"[yellow]Project already exists at {project_dir}. Overwrite?[/]"):
            console.print("[dim]Cancelled.[/]")
            raise typer.Exit()

    # Create directory structure
    dirs = [
        project_dir,
        project_dir / "agents",
        project_dir / "prompts",
        project_dir / "evals",
        project_dir / "security",
        project_dir / "compliance",
        project_dir / "history",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Create config
    config = Config(
        project_name=name,
        project_dir=str(project_dir),
        llm=LLMConfig(provider=provider, model=model),
    )
    config.save()

    # Summary
    console.print()
    console.print("[green]✓[/] Project initialized successfully!")
    console.print()
    console.print(f"  [bold]Name:[/]      {name}")
    console.print(f"  [bold]Location:[/]  {project_dir}")
    console.print(f"  [bold]Provider:[/]  {provider}")
    console.print(f"  [bold]Model:[/]     {model}")
    console.print()
    console.print("[dim]Next steps:[/]")
    console.print("  1. Run [bold cyan]clean-agents design[/] to start an architecture session")
    console.print("  2. Run [bold cyan]clean-agents blueprint[/] to view your blueprint")
    console.print("  3. Run [bold cyan]clean-agents shield[/] to harden security")
    console.print()
