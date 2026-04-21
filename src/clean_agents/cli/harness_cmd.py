"""CLI commands for the runtime harness."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from clean_agents.core.blueprint import Blueprint
from clean_agents.harness import (
    RuntimeHarness,
    MockProvider,
    AnthropicProvider,
)

console = Console()


def harness_run_cmd(
    path: str = typer.Option(
        "blueprint.yaml",
        "--blueprint",
        "-b",
        help="Path to blueprint YAML file",
    ),
    input_msg: str = typer.Option(
        "What should I do?",
        "--input",
        "-i",
        help="Input message to process",
    ),
    provider: str = typer.Option(
        "mock",
        "--provider",
        "-p",
        help="LLM provider: mock, anthropic, openai",
    ),
    max_rounds: int = typer.Option(
        10,
        "--max-rounds",
        help="Maximum rounds for multi-step patterns",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose logging",
    ),
) -> None:
    """Run the agent harness against a blueprint.

    Example:
        clean-agents harness run --blueprint my-blueprint.yaml --input "Analyze this"
    """
    # Load blueprint
    blueprint_path = Path(path)
    if not blueprint_path.exists():
        console.print(f"[red]Error: Blueprint not found at {path}[/]")
        raise typer.Exit(1)

    try:
        blueprint = Blueprint.load(blueprint_path)
    except Exception as e:
        console.print(f"[red]Error loading blueprint: {e}[/]")
        raise typer.Exit(1)

    # Create provider
    if provider == "anthropic":
        llm_provider = AnthropicProvider()
    elif provider == "openai":
        from clean_agents.harness import OpenAIProvider

        llm_provider = OpenAIProvider()
    else:  # Default to mock
        llm_provider = MockProvider()

    # Create and run harness
    harness = RuntimeHarness(blueprint, provider=llm_provider)

    try:
        console.print(f"[cyan]Running {blueprint.name} ({blueprint.pattern.value})...[/]\n")
        result = asyncio.run(harness.run(input_msg, max_rounds=max_rounds))

        # Display results
        _display_harness_result(result)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"[red]Error running harness: {e}[/]")
        if verbose:
            import traceback

            traceback.print_exc()
        raise typer.Exit(1)


def harness_trace_cmd(
    output_file: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Save trace to JSON file (optional)",
    ),
) -> None:
    """Display detailed execution trace from last harness run."""
    # This is a placeholder for storing/retrieving the last run
    console.print("[yellow]Trace command — stores last harness result in session[/]")
    if output_file:
        console.print(f"[green]Trace would be saved to {output_file}[/]")


def _display_harness_result(result) -> None:
    """Display harness result in a formatted table."""
    # Summary table
    console.print("[bold cyan]═══ HARNESS EXECUTION RESULT ═══[/]\n")

    summary_table = Table(title="Execution Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Blueprint", result.blueprint_name)
    summary_table.add_row("Pattern", result.pattern)
    summary_table.add_row("Rounds", str(result.rounds))
    summary_table.add_row("Total Latency", f"{result.total_latency_ms:.1f}ms")
    summary_table.add_row("Total Cost", f"${result.total_cost:.4f}")
    summary_table.add_row("Total Tokens", f"{result.total_tokens.total():,}")

    console.print(summary_table)

    # Final output
    console.print("\n[bold cyan]Final Output:[/]")
    console.print(f"[white]{result.final_output}[/]")

    # Agent traces
    if result.agent_traces:
        console.print("\n[bold cyan]Agent Traces:[/]")
        traces_table = Table(title="Agent Execution Details")
        traces_table.add_column("Agent", style="cyan")
        traces_table.add_column("Latency (ms)", style="yellow")
        traces_table.add_column("Tokens", style="green")
        traces_table.add_column("Cost", style="magenta")

        for trace in result.agent_traces:
            tokens = f"{trace.tokens_used.input_tokens}↓/{trace.tokens_used.output_tokens}↑"
            traces_table.add_row(
                trace.agent_name,
                f"{trace.latency_ms:.1f}",
                tokens,
                f"${trace.cost:.6f}",
            )

        console.print(traces_table)

    # Errors
    if result.errors:
        console.print("\n[bold red]Errors:[/]")
        for error in result.errors:
            console.print(f"  • {error}")
