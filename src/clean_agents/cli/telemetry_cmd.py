"""CLean-agents telemetry commands.

Manage local usage telemetry collection.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from clean_agents.telemetry import get_telemetry

console = Console()


def telemetry_status_cmd() -> None:
    """Show telemetry status and summary."""
    telemetry = get_telemetry()

    status = "enabled" if telemetry.is_enabled() else "disabled"
    console.print(f"\n[bold cyan]Telemetry Status:[/] {status}")

    summary = telemetry.summary()

    if summary["total_events"] == 0:
        console.print("[dim]No telemetry data collected yet.[/]")
        return

    console.print(f"[bold]Total events:[/] {summary['total_events']}")
    console.print(f"[bold]Success rate:[/] {summary['success_rate']}%")
    console.print(f"[bold]Avg duration:[/] {summary['avg_duration_ms']}ms")

    if summary["commands"]:
        console.print("\n[bold]Commands used:[/]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Command")
        table.add_column("Count", justify="right")

        for cmd, count in sorted(summary["commands"].items(), key=lambda x: x[1], reverse=True):
            table.add_row(cmd, str(count))

        console.print(table)

    console.print()


def telemetry_enable_cmd() -> None:
    """Enable local telemetry collection."""
    telemetry = get_telemetry()
    telemetry.enable()

    console.print(
        "[bold green]✓[/] Telemetry enabled. "
        "Data is stored locally in [cyan]~/.config/clean-agents/telemetry.jsonl[/]"
    )
    console.print(
        "[dim]You can view, export, or delete your data at any time with "
        "'clean-agents telemetry' commands.[/]\n"
    )


def telemetry_disable_cmd(
    clear: bool = typer.Option(False, "--clear", help="Also delete all telemetry data"),
) -> None:
    """Disable telemetry collection."""
    telemetry = get_telemetry()
    telemetry.disable()

    console.print("[bold green]✓[/] Telemetry disabled.")

    if clear:
        telemetry.clear()
        console.print("[bold green]✓[/] All telemetry data deleted.")
    else:
        console.print(
            "[dim]Existing telemetry data is preserved. "
            "Use --clear to also delete all data.[/]"
        )

    console.print()


def telemetry_export_cmd(
    output: str = typer.Option(
        "clean-agents-telemetry.jsonl",
        "--output",
        "-o",
        help="Output file path",
    ),
) -> None:
    """Export telemetry data to a file."""
    telemetry = get_telemetry()

    try:
        output_path = Path(output)
        telemetry.export(output_path)
        console.print(f"[bold green]✓[/] Telemetry exported to [cyan]{output_path.absolute()}[/]")
        console.print()
    except Exception as e:
        console.print(f"[bold red]✗[/] Failed to export telemetry: {e}")
        raise typer.Exit(code=1) from e


def telemetry_clear_cmd() -> None:
    """Delete all telemetry data."""
    telemetry = get_telemetry()

    if typer.confirm("Are you sure you want to delete all telemetry data?"):
        telemetry.clear()
        console.print("[bold green]✓[/] All telemetry data deleted.\n")
    else:
        console.print("[dim]Cancelled.[/]\n")
