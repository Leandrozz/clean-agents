"""CLean-agents marketplace — browse and install community plugins."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from clean_agents.modules.marketplace import PluginIndex, install_plugin

console = Console()


def marketplace_search_cmd(
    query: str = typer.Argument("", help="Search query (name, description, or tag)"),
    type_filter: str = typer.Option("", "--type", "-t", help="Filter by type: analysis | transform | scaffold"),
    tag: str = typer.Option("", "--tag", help="Filter by tag"),
    sort_by: str = typer.Option("relevance", "--sort", help="Sort by: relevance | rating | downloads"),
) -> None:
    """Search the plugin marketplace.

    Examples:
        clean-agents marketplace search security
        clean-agents marketplace search --type analysis
        clean-agents marketplace search --tag rag --sort rating
    """
    index = PluginIndex.load_builtin()
    results = []

    # Apply filters
    if query:
        results = index.search(query)
    else:
        results = index.plugins.copy()

    if type_filter:
        results = [p for p in results if p.plugin_type == type_filter]

    if tag:
        results = [p for p in results if tag in p.tags]

    # Apply sorting
    if sort_by == "rating":
        results.sort(key=lambda p: p.rating, reverse=True)
    elif sort_by == "downloads":
        results.sort(key=lambda p: p.downloads, reverse=True)
    # else: keep relevance order from search

    if not results:
        console.print("[dim]No plugins found.[/]")
        return

    console.print()
    console.print(Panel.fit("[bold cyan]Plugin Marketplace[/]", border_style="cyan"))
    console.print()

    table = Table(show_header=True, header_style="bold", show_lines=False)
    table.add_column("Name", style="cyan")
    table.add_column("Version")
    table.add_column("Type")
    table.add_column("Rating")
    table.add_column("Downloads")
    table.add_column("Description")

    type_colors = {
        "analysis": "green",
        "scaffold": "blue",
        "transform": "yellow",
    }

    for plugin in results:
        type_color = type_colors.get(plugin.plugin_type, "white")
        rating_str = f"[yellow]★[/] {plugin.rating:.1f}" if plugin.rating > 0 else "[dim]—[/]"
        table.add_row(
            plugin.name,
            plugin.version,
            f"[{type_color}]{plugin.plugin_type}[/]",
            rating_str,
            str(plugin.downloads),
            plugin.description[:50],
        )

    console.print(table)
    console.print()
    console.print(f"[dim]Use [bold]marketplace info <name>[/] for details[/]")
    console.print()


def marketplace_info_cmd(
    name: str = typer.Argument(..., help="Plugin name"),
) -> None:
    """Show detailed info about a plugin.

    Example:
        clean-agents marketplace info security-scanner
    """
    index = PluginIndex.load_builtin()
    plugin = index.get(name)

    if not plugin:
        console.print(f"[red]Error:[/] Plugin '[bold]{name}[/]' not found in marketplace.")
        console.print("[dim]Run [bold]marketplace search[/] to find available plugins.[/]")
        raise typer.Exit(1)

    console.print()
    console.print(Panel.fit(f"[bold cyan]{plugin.name}[/] v{plugin.version}", border_style="cyan"))
    console.print()

    # Basic info
    table = Table(show_header=False, box=None)
    table.add_column("", style="bold", width=15)
    table.add_column("", width=60)

    table.add_row("Type", f"[yellow]{plugin.plugin_type}[/]")
    table.add_row("Author", plugin.author)
    table.add_row("Description", plugin.description)
    table.add_row("Rating", f"[yellow]★[/] {plugin.rating:.1f} / 5.0" if plugin.rating > 0 else "[dim]N/A[/]")
    table.add_row("Downloads", str(plugin.downloads))

    if plugin.tags:
        table.add_row("Tags", ", ".join(f"[dim]{tag}[/]" for tag in plugin.tags))

    if plugin.source_url:
        table.add_row("Repository", f"[link]{plugin.source_url}[/link]")

    console.print(table)
    console.print()

    # Installation
    if plugin.pip_package or plugin.source_url:
        console.print("[bold]Installation:[/]")
        if plugin.install_cmd:
            console.print(f"  [green]$[/] {plugin.install_cmd}")
        else:
            if plugin.pip_package:
                console.print(f"  [green]$[/] pip install {plugin.pip_package}")
            elif plugin.source_url:
                console.print(f"  [green]$[/] pip install git+{plugin.source_url}")
        console.print()
        console.print("[dim]Or use:[/] [bold]marketplace install {name}[/]")
    else:
        console.print("[yellow]Note:[/] This plugin is not available for installation.")

    console.print()


def marketplace_install_cmd(
    name: str = typer.Argument(..., help="Plugin name to install"),
    confirm: bool = typer.Option(False, "--confirm", "-y", help="Skip confirmation prompt"),
) -> None:
    """Install a plugin from the marketplace.

    Example:
        clean-agents marketplace install security-scanner
        clean-agents marketplace install security-scanner --confirm
    """
    index = PluginIndex.load_builtin()
    plugin = index.get(name)

    if not plugin:
        console.print(f"[red]Error:[/] Plugin '[bold]{name}[/]' not found in marketplace.")
        raise typer.Exit(1)

    if not plugin.pip_package and not plugin.source_url:
        console.print(f"[red]Error:[/] Plugin '[bold]{name}[/]' is not available for installation.")
        raise typer.Exit(1)

    # Show install info
    console.print()
    console.print(f"[bold]Installing:[/] {plugin.name} v{plugin.version}")
    console.print(f"[dim]Author:[/] {plugin.author}")
    console.print(f"[dim]Type:[/] {plugin.plugin_type}")
    console.print()

    if not confirm:
        if not typer.confirm("Continue with installation?"):
            console.print("[dim]Cancelled.[/]")
            raise typer.Exit(0)

    console.print()
    console.print("[cyan]Installing...[/]")

    if install_plugin(plugin):
        console.print(f"[green]✓[/] Successfully installed [bold]{plugin.name}[/]")
        console.print()
        console.print("[dim]The plugin is now available. Use:[/]")
        console.print(f"  [bold]clean-agents plugin list[/]     # See all plugins")
        console.print(f"  [bold]clean-agents plugin run {name}[/]  # Run the plugin")
        console.print()
    else:
        console.print(f"[red]✗[/] Failed to install [bold]{plugin.name}[/]")
        console.print("[yellow]Tip:[/] Install manually using:")
        if plugin.install_cmd:
            console.print(f"  {plugin.install_cmd}")
        elif plugin.pip_package:
            console.print(f"  pip install {plugin.pip_package}")
        raise typer.Exit(1)


def marketplace_list_cmd(
    sort_by: str = typer.Option("downloads", "--sort", help="Sort by: rating | downloads | name"),
) -> None:
    """List all plugins in the marketplace.

    Example:
        clean-agents marketplace list
        clean-agents marketplace list --sort rating
    """
    index = PluginIndex.load_builtin()
    plugins = index.plugins.copy()

    # Sort
    if sort_by == "rating":
        plugins.sort(key=lambda p: p.rating, reverse=True)
    elif sort_by == "downloads":
        plugins.sort(key=lambda p: p.downloads, reverse=True)
    elif sort_by == "name":
        plugins.sort(key=lambda p: p.name)

    console.print()
    console.print(Panel.fit("[bold cyan]Plugin Marketplace[/]", border_style="cyan"))
    console.print()

    table = Table(show_header=True, header_style="bold", show_lines=False)
    table.add_column("Name", style="cyan")
    table.add_column("Type")
    table.add_column("Rating")
    table.add_column("Downloads")
    table.add_column("Author")

    type_colors = {
        "analysis": "green",
        "scaffold": "blue",
        "transform": "yellow",
    }

    for plugin in plugins:
        type_color = type_colors.get(plugin.plugin_type, "white")
        rating_str = f"[yellow]★[/] {plugin.rating:.1f}" if plugin.rating > 0 else "[dim]—[/]"
        table.add_row(
            plugin.name,
            f"[{type_color}]{plugin.plugin_type}[/]",
            rating_str,
            str(plugin.downloads),
            plugin.author,
        )

    console.print(table)
    console.print()
    console.print(f"[dim]{len(plugins)} plugin(s) available[/]")
    console.print("[dim]Use [bold]marketplace info <name>[/] for details, or [bold]marketplace search[/] to search[/]")
    console.print()
