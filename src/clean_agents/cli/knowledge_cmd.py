"""CLean-agents knowledge — manage the dynamic knowledge base."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from clean_agents.knowledge.base import FrameworkProfile, ModelBenchmark
from clean_agents.knowledge.updater import KnowledgeStore

console = Console()


def knowledge_list_cmd(
    category: str = typer.Argument(
        "models", help="Category: models | frameworks | compliance | attack_vectors"
    ),
) -> None:
    """List knowledge base entries."""
    store = KnowledgeStore()

    console.print()

    if category == "models":
        models = store.get_models()
        console.print(Panel.fit("[bold cyan]Model Benchmarks[/]", border_style="cyan"))
        console.print()

        if not models:
            console.print("[dim]No models found.[/]")
            return

        table = Table(show_header=True, header_style="bold", show_lines=False)
        table.add_column("Name", style="cyan")
        table.add_column("Provider", style="green")
        table.add_column("GPQA", justify="right")
        table.add_column("SWE-Bench", justify="right")
        table.add_column("BFCL", justify="right")
        table.add_column("Input Price", justify="right")
        table.add_column("Context", justify="right")

        for _name, model in sorted(models.items()):
            table.add_row(
                model.name,
                model.provider,
                f"{model.gpqa:.1f}%",
                f"{model.swe_bench:.1f}%",
                f"{model.bfcl:.1f}%",
                f"${model.input_price:.2f}",
                f"{model.context_window:,}",
            )

        console.print(table)
        console.print()
        console.print(f"[dim]{len(models)} model(s) available[/]")
        console.print()

    elif category == "frameworks":
        frameworks = store.get_frameworks()
        console.print(
            Panel.fit("[bold cyan]Framework Profiles[/]", border_style="cyan")
        )
        console.print()

        if not frameworks:
            console.print("[dim]No frameworks found.[/]")
            return

        table = Table(show_header=True, header_style="bold", show_lines=False)
        table.add_column("Name", style="cyan")
        table.add_column("Multi-Agent")
        table.add_column("State Mgmt")
        table.add_column("HITL")
        table.add_column("Streaming")
        table.add_column("Persistence")

        for _name, fw in sorted(frameworks.items()):
            table.add_row(
                fw.name,
                "✓" if fw.multi_agent else "✗",
                "✓" if fw.state_management else "✗",
                "✓" if fw.built_in_hitl else "✗",
                "✓" if fw.streaming else "✗",
                "✓" if fw.persistence else "✗",
            )

        console.print(table)
        console.print()
        console.print(f"[dim]{len(frameworks)} framework(s) available[/]")
        console.print()

    elif category == "compliance":
        requirements = store.get_compliance()
        console.print(
            Panel.fit("[bold cyan]Compliance Requirements[/]", border_style="cyan")
        )
        console.print()

        if not requirements:
            console.print("[dim]No compliance requirements found.[/]")
            return

        # Group by regulation
        by_reg = {}
        for req in requirements:
            if req.regulation not in by_reg:
                by_reg[req.regulation] = []
            by_reg[req.regulation].append(req)

        for regulation in sorted(by_reg.keys()):
            reqs = by_reg[regulation]
            console.print(f"[bold green]{regulation}[/] ({len(reqs)} requirements)")
            for req in reqs:
                console.print(f"  {req.article}: {req.requirement[:60]}")
            console.print()

    elif category == "attack_vectors":
        vectors = store.get_attack_vectors()
        console.print(
            Panel.fit("[bold cyan]Attack Vectors[/]", border_style="cyan")
        )
        console.print()

        if not vectors:
            console.print("[dim]No attack vectors found.[/]")
            return

        table = Table(show_header=True, header_style="bold", show_lines=False)
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Description")
        table.add_column("Mitigations", justify="right")

        for vec in sorted(vectors, key=lambda v: v.id):
            table.add_row(
                vec.id,
                vec.name,
                vec.description[:50],
                str(len(vec.mitigations)),
            )

        console.print(table)
        console.print()
        console.print(f"[dim]{len(vectors)} attack vector(s) defined[/]")
        console.print()

    else:
        console.print(
            f"[red]Unknown category: {category}[/]"
        )
        raise typer.Exit(code=1)


def knowledge_add_cmd(
    category: str = typer.Argument(..., help="Category: models | frameworks"),
    name: str = typer.Argument(..., help="Entry name"),
    scope: str = typer.Option("global", help="Scope: global | project"),
) -> None:
    """Add or update a knowledge base entry interactively."""
    store = KnowledgeStore()

    if category == "models":
        console.print("[bold cyan]Add Model Benchmark[/]")
        console.print()

        provider = typer.prompt("Provider (anthropic/openai/google)")
        gpqa = float(typer.prompt("GPQA score (0-100)"))
        swe_bench = float(typer.prompt("SWE-Bench score (0-100)"))
        bfcl = float(typer.prompt("BFCL score (0-100)"))
        input_price = float(typer.prompt("Input price (USD per 1M tokens)"))
        output_price = float(typer.prompt("Output price (USD per 1M tokens)"))
        context_window = int(typer.prompt("Context window (tokens)"))
        max_output = int(typer.prompt("Max output (tokens)"))

        model = ModelBenchmark(
            name=name,
            provider=provider,
            gpqa=gpqa,
            swe_bench=swe_bench,
            bfcl=bfcl,
            input_price=input_price,
            output_price=output_price,
            context_window=context_window,
            max_output=max_output,
        )

        store.add_model(model, scope=scope)
        console.print(f"[green]✓[/] Model '{name}' added to [bold]{scope}[/] knowledge base")

    elif category == "frameworks":
        console.print("[bold cyan]Add Framework Profile[/]")
        console.print()

        strengths_str = typer.prompt("Strengths (comma-separated)")
        strengths = [s.strip() for s in strengths_str.split(",")]

        weaknesses_str = typer.prompt("Weaknesses (comma-separated)")
        weaknesses = [w.strip() for w in weaknesses_str.split(",")]

        best_for_str = typer.prompt("Best for (comma-separated)")
        best_for = [b.strip() for b in best_for_str.split(",")]

        multi_agent = typer.confirm("Multi-agent support?", default=True)
        state_mgmt = typer.confirm("State management?", default=False)
        hitl = typer.confirm("Built-in HITL?", default=False)
        streaming = typer.confirm("Streaming support?", default=True)
        persistence = typer.confirm("Persistence?", default=False)

        framework = FrameworkProfile(
            name=name,
            strengths=strengths,
            weaknesses=weaknesses,
            best_for=best_for,
            multi_agent=multi_agent,
            state_management=state_mgmt,
            built_in_hitl=hitl,
            streaming=streaming,
            persistence=persistence,
        )

        store.add_framework(framework, scope=scope)
        console.print(
            f"[green]✓[/] Framework '{name}' added to [bold]{scope}[/] knowledge base"
        )

    else:
        console.print(f"[red]Cannot add category: {category}[/]")
        console.print("[dim]Use 'knowledge add models' or 'knowledge add frameworks'[/]")
        raise typer.Exit(code=1)


def knowledge_import_cmd(
    file: str = typer.Argument(..., help="YAML file to import"),
) -> None:
    """Import knowledge updates from YAML."""
    path = Path(file)
    if not path.exists():
        console.print(f"[red]File not found: {file}[/]")
        raise typer.Exit(code=1)

    try:
        store = KnowledgeStore()
        count = store.import_from_yaml(path)
        console.print(f"[green]✓[/] Imported {count} knowledge update(s)")
    except ImportError as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(code=1) from e


def knowledge_export_cmd(
    output: str = typer.Option(
        "knowledge_export.yaml", "--output", "-o", help="Output YAML file"
    ),
) -> None:
    """Export knowledge base to YAML."""
    path = Path(output)

    try:
        store = KnowledgeStore()
        store.export_to_yaml(path)
        console.print(f"[green]✓[/] Exported knowledge base to [cyan]{path}[/]")
    except ImportError as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(code=1) from e
