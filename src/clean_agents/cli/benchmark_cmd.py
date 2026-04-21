"""CLI commands for benchmark and comparison operations."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from clean_agents.core.blueprint import Blueprint
from clean_agents.harness.benchmark import BenchmarkRunner, BenchmarkSuite

console = Console()


def benchmark_run_cmd(
    path: str = typer.Argument(
        ...,
        help="Path to blueprint YAML file",
    ),
    suite: str = typer.Option(
        "",
        help="Path to benchmark suite YAML (default: built-in suite)",
    ),
    provider: str = typer.Option(
        "mock",
        help="LLM provider: mock, anthropic, openai",
    ),
    output: str = typer.Option(
        "",
        help="Save results to file (JSON/YAML)",
    ),
) -> None:
    """Run benchmarks against a single blueprint."""
    try:
        # Load blueprint
        blueprint_path = Path(path)
        if not blueprint_path.exists():
            console.print(f"[red]Error:[/] Blueprint file not found: {path}")
            raise typer.Exit(1)

        blueprint = Blueprint.load(blueprint_path)
        console.print(f"[cyan]Loaded blueprint:[/] {blueprint.name}")

        # Load or create suite
        if suite:
            suite_path = Path(suite)
            if not suite_path.exists():
                console.print(f"[red]Error:[/] Suite file not found: {suite}")
                raise typer.Exit(1)
            benchmark_suite = BenchmarkSuite.from_yaml(suite_path)
            console.print(f"[cyan]Loaded suite:[/] {benchmark_suite.name}")
        else:
            benchmark_suite = BenchmarkSuite.default_suite()
            console.print("[cyan]Using:[/] default benchmark suite")

        # Create runner and execute
        console.print(f"[cyan]Provider:[/] {provider}")
        console.print(f"[cyan]Running {len(benchmark_suite.tasks)} tasks...[/]")

        runner = BenchmarkRunner()
        score = asyncio.run(runner.run_suite(blueprint, benchmark_suite))

        # Display results
        console.print("\n[bold]Benchmark Results[/]")
        console.print(f"Blueprint: {score.blueprint_name}")
        console.print(f"Pass rate: {score.pass_rate:.1%} ({score.tasks_passed}/{score.tasks_total})")
        console.print(f"Average score: {score.avg_score:.3f}")
        console.print(f"Average latency: {score.avg_latency_ms:.0f}ms")
        console.print(f"Total cost: ${score.total_cost:.4f}")
        console.print(f"Total tokens: {score.total_tokens.total}")

        if score.category_scores:
            console.print("\n[bold]Category Scores[/]")
            for category, cat_score in sorted(score.category_scores.items()):
                console.print(f"  {category}: {cat_score:.3f}")

        # Save results if requested
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if output.endswith(".json"):
                import json

                with open(output_path, "w") as f:
                    json.dump(score.model_dump(), f, indent=2, default=str)
            else:
                import yaml

                with open(output_path, "w") as f:
                    yaml.dump(score.model_dump(), f, default_flow_style=False)
            console.print(f"[green]Results saved to:[/] {output}")

    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)


def benchmark_compare_cmd(
    paths: str = typer.Argument(
        ...,
        help="Comma-separated paths to blueprint YAML files",
    ),
    suite: str = typer.Option(
        "",
        help="Path to benchmark suite YAML (default: built-in suite)",
    ),
    output: str = typer.Option(
        "",
        help="Save results to file (JSON/YAML)",
    ),
) -> None:
    """Compare multiple blueprints side-by-side."""
    try:
        # Parse blueprint paths
        blueprint_paths = [p.strip() for p in paths.split(",")]
        blueprints = []

        for bp_path in blueprint_paths:
            path = Path(bp_path)
            if not path.exists():
                console.print(f"[red]Error:[/] Blueprint file not found: {bp_path}")
                raise typer.Exit(1)
            blueprints.append(Blueprint.load(path))
            console.print(f"[cyan]Loaded:[/] {blueprints[-1].name}")

        # Load or create suite
        if suite:
            suite_path = Path(suite)
            if not suite_path.exists():
                console.print(f"[red]Error:[/] Suite file not found: {suite}")
                raise typer.Exit(1)
            benchmark_suite = BenchmarkSuite.from_yaml(suite_path)
            console.print(f"[cyan]Using suite:[/] {benchmark_suite.name}")
        else:
            benchmark_suite = BenchmarkSuite.default_suite()
            console.print("[cyan]Using:[/] default benchmark suite")

        # Run comparison
        console.print(f"[cyan]Comparing {len(blueprints)} blueprints...[/]")
        runner = BenchmarkRunner()
        comparison = asyncio.run(runner.compare(blueprints, benchmark_suite))

        # Display results
        console.print("\n" + comparison.to_table())
        console.print("\n" + comparison.summary)

        # Save results if requested
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if output.endswith(".json"):
                import json

                with open(output_path, "w") as f:
                    json.dump(comparison.model_dump(), f, indent=2, default=str)
            else:
                import yaml

                with open(output_path, "w") as f:
                    yaml.dump(comparison.model_dump(), f, default_flow_style=False)
            console.print(f"[green]Results saved to:[/] {output}")

    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)


def benchmark_suite_cmd(
    output: str = typer.Option(
        "benchmark_suite.yaml",
        help="Output file for benchmark suite",
    ),
) -> None:
    """Generate a default benchmark suite YAML for customization."""
    try:
        suite = BenchmarkSuite.default_suite()
        output_path = Path(output)
        suite.save(output_path)
        console.print(f"[green]Benchmark suite generated:[/] {output_path}")
        console.print(f"[cyan]Tasks:[/] {len(suite.tasks)}")
        for task in suite.tasks:
            console.print(f"  - {task.name} ({task.category})")
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)
