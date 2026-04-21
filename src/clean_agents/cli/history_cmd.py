"""Blueprint version history CLI commands."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from clean_agents.core.blueprint import Blueprint
from clean_agents.core.config import Config
from clean_agents.core.versioning import VersionManager

console = Console()


def history_list_cmd(
    path: str = typer.Option(
        None,
        help="Path to project directory (auto-discovered if not provided)",
    ),
) -> None:
    """Show blueprint version history."""
    try:
        if path:
            project_dir = Path(path)
        else:
            config = Config.discover()
            project_dir = config.project_path()

        if not project_dir.exists():
            console.print(f"[red]Project directory not found: {project_dir}[/red]")
            raise typer.Exit(1)

        vm = VersionManager(project_dir)
        versions = vm.list_versions()

        if not versions:
            console.print("[yellow]No version history found.[/yellow]")
            raise typer.Exit(0)

        table = Table(title="Blueprint Version History", show_header=True, header_style="bold cyan")
        table.add_column("Version ID", style="magenta")
        table.add_column("Timestamp", style="green")
        table.add_column("Description")
        table.add_column("Hash", style="dim")

        for v in versions:
            table.add_row(v.version_id, v.timestamp, v.description, v.blueprint_hash)

        console.print(table)
        console.print(f"\n[cyan]Total versions:[/cyan] {len(versions)}")

    except Exception as e:
        console.print(f"[red]Error listing versions: {e}[/red]")
        raise typer.Exit(1)


def history_restore_cmd(
    version_id: str = typer.Option(
        ...,
        help="Version ID to restore",
    ),
    path: str = typer.Option(
        None,
        help="Path to project directory (auto-discovered if not provided)",
    ),
    output: str = typer.Option(
        None,
        help="Output path for restored blueprint (defaults to blueprint.yaml in project)",
    ),
) -> None:
    """Restore blueprint to a specific version."""
    try:
        if path:
            project_dir = Path(path)
        else:
            config = Config.discover()
            project_dir = config.project_path()

        if not project_dir.exists():
            console.print(f"[red]Project directory not found: {project_dir}[/red]")
            raise typer.Exit(1)

        vm = VersionManager(project_dir)
        blueprint = vm.restore(version_id)

        if blueprint is None:
            console.print(f"[red]Version not found: {version_id}[/red]")
            raise typer.Exit(1)

        output_path = Path(output) if output else project_dir / "blueprint.yaml"
        blueprint.save(output_path, f"Restored from version {version_id}")

        console.print(f"[green]✓[/green] Blueprint restored to [cyan]{output_path}[/cyan]")

    except Exception as e:
        console.print(f"[red]Error restoring version: {e}[/red]")
        raise typer.Exit(1)


def history_diff_cmd(
    v1: str = typer.Option(
        ...,
        help="First version ID",
    ),
    v2: str = typer.Option(
        ...,
        help="Second version ID",
    ),
    path: str = typer.Option(
        None,
        help="Path to project directory (auto-discovered if not provided)",
    ),
) -> None:
    """Diff two blueprint versions."""
    try:
        if path:
            project_dir = Path(path)
        else:
            config = Config.discover()
            project_dir = config.project_path()

        if not project_dir.exists():
            console.print(f"[red]Project directory not found: {project_dir}[/red]")
            raise typer.Exit(1)

        vm = VersionManager(project_dir)
        diff_result = vm.get_diff(v1, v2)

        if "error" in diff_result:
            console.print(f"[red]Error: {diff_result['error']}[/red]")
            raise typer.Exit(1)

        # Display diff information
        console.print("\n[bold cyan]Version Comparison[/bold cyan]")
        console.print(f"[bold]Version 1:[/bold] {diff_result['v1_id']}")
        console.print(f"  Timestamp: {diff_result['v1_timestamp']}")
        console.print(f"  Description: {diff_result['v1_description']}")
        console.print(f"  Hash: {diff_result['v1_hash']}")

        console.print(f"\n[bold]Version 2:[/bold] {diff_result['v2_id']}")
        console.print(f"  Timestamp: {diff_result['v2_timestamp']}")
        console.print(f"  Description: {diff_result['v2_description']}")
        console.print(f"  Hash: {diff_result['v2_hash']}")

        if diff_result["hashes_match"]:
            console.print("\n[green]✓ No content changes between versions[/green]")
        else:
            console.print("\n[yellow]⚠ Content differs between versions[/yellow]")

        if diff_result["v1_changes"]:
            console.print(f"\n[bold cyan]Changes in Version 1:[/bold cyan]")
            for change in diff_result["v1_changes"]:
                console.print(f"  - {change}")

        if diff_result["v2_changes"]:
            console.print(f"\n[bold cyan]Changes in Version 2:[/bold cyan]")
            for change in diff_result["v2_changes"]:
                console.print(f"  - {change}")

    except Exception as e:
        console.print(f"[red]Error comparing versions: {e}[/red]")
        raise typer.Exit(1)
