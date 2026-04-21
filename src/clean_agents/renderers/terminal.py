"""Rich terminal renderer for CLean-agents output."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from clean_agents.core.blueprint import Blueprint


def render_blueprint_summary(console: Console, blueprint: Blueprint) -> None:
    """Render a blueprint summary panel."""
    summary = blueprint.summary()

    content = (
        f"[bold]Name:[/]        {summary['name']}\n"
        f"[bold]Type:[/]        {summary['type']}\n"
        f"[bold]Pattern:[/]     {summary['pattern']}\n"
        f"[bold]Framework:[/]   {summary['framework']}\n"
        f"[bold]Domain:[/]      {summary['domain']}\n"
        f"[bold]Agents:[/]      {summary['agents']}\n"
        f"[bold]GraphRAG:[/]    {'✓' if summary['has_graphrag'] else '✗'}\n"
        f"[bold]HITL:[/]        {'✓' if summary['has_hitl'] else '✗'}\n"
        f"[bold]Compliance:[/]  {', '.join(summary['compliance']) or 'None'}\n"
        f"[bold]Est. cost:[/]   {summary['est_cost_per_request']}/request\n"
        f"[bold]Iteration:[/]   {summary['iteration']}"
    )

    console.print(Panel(
        content,
        title="[bold cyan]Architecture Blueprint[/]",
        border_style="cyan",
    ))


def render_agents_table(console: Console, blueprint: Blueprint) -> None:
    """Render a table of all agents."""
    table = Table(
        title="Agent Specifications",
        show_header=True,
        header_style="bold",
        show_lines=True,
    )
    table.add_column("Agent", style="cyan", no_wrap=True)
    table.add_column("Type")
    table.add_column("Model")
    table.add_column("Reasoning")
    table.add_column("HITL")
    table.add_column("Memory")
    table.add_column("Guardrails")
    table.add_column("Tokens", justify="right")

    for agent in blueprint.agents:
        memory_flags = []
        if agent.memory.short_term:
            memory_flags.append("ST")
        if agent.memory.episodic:
            memory_flags.append("EP")
        if agent.memory.semantic:
            memory_flags.append("SM")
        if agent.memory.procedural:
            memory_flags.append("PR")
        if agent.memory.graphrag:
            memory_flags.append("GR")

        guardrail_count = len(agent.guardrails.input) + len(agent.guardrails.output)

        table.add_row(
            agent.name,
            agent.agent_type,
            agent.model.primary.replace("claude-", "c-").replace("gpt-", "g-"),
            agent.reasoning.value,
            agent.hitl.value,
            " ".join(memory_flags),
            f"{guardrail_count} rules",
            str(agent.token_budget),
        )

    console.print(table)


def render_design_decisions(console: Console, blueprint: Blueprint) -> None:
    """Render design decisions as a tree."""
    if not blueprint.decisions:
        return

    tree = Tree("[bold]Design Decisions[/]")

    for decision in blueprint.decisions:
        node = tree.add(f"[bold cyan]{decision.dimension}[/]: {decision.decision}")
        node.add(f"[dim]Justification:[/] {decision.justification}")

        if decision.research:
            research_node = node.add("[dim]Research:[/]")
            for r in decision.research:
                year = f" ({r.year})" if r.year else ""
                research_node.add(f"{r.source}{year}: {r.finding}")

        if decision.alternatives_considered:
            alts = ", ".join(decision.alternatives_considered)
            node.add(f"[dim]Alternatives:[/] {alts}")

    console.print(tree)


def render_architecture_diagram(console: Console, blueprint: Blueprint) -> None:
    """Render an ASCII architecture diagram."""
    orchestrator = blueprint.get_orchestrator()
    specialists = [a for a in blueprint.agents if a.agent_type == "specialist"]
    guardians = [a for a in blueprint.agents if a.agent_type == "guardian"]
    classifiers = [a for a in blueprint.agents if a.agent_type == "classifier"]

    tree = Tree(f"[bold cyan]{blueprint.name}[/] ({blueprint.pattern.value})")

    if orchestrator:
        orch_node = tree.add(f"[bold yellow]⚙ {orchestrator.name}[/] (orchestrator)")
        for s in specialists:
            orch_node.add(f"[green]◆ {s.name}[/] — {s.role[:50]}")
        for c in classifiers:
            orch_node.add(f"[blue]◇ {c.name}[/] — {c.role[:50]}")
        for g in guardians:
            tree.add(f"[red]🛡 {g.name}[/] — {g.role[:50]}")
    else:
        for agent in blueprint.agents:
            icon = {"specialist": "◆", "classifier": "◇", "guardian": "🛡"}.get(agent.agent_type, "●")
            tree.add(f"{icon} {agent.name} — {agent.role[:50]}")

    console.print(tree)
