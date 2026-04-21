"""clean-agents plugin — manage and run plugins."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from clean_agents.core.blueprint import Blueprint
from clean_agents.core.config import Config
from clean_agents.modules.base import (
    AnalysisPlugin,
    PluginType,
    ScaffoldPlugin,
    TransformPlugin,
    get_registry,
)
from clean_agents.modules.examples import BUILTIN_PLUGINS

console = Console()


def _ensure_builtins() -> None:
    """Register built-in plugins if not already loaded."""
    registry = get_registry()
    for cls in BUILTIN_PLUGINS:
        instance = cls()
        manifest = instance.manifest()
        if manifest.name not in registry.plugins:
            registry.register(instance)


def plugin_list_cmd() -> None:
    """List all available plugins."""
    _ensure_builtins()
    registry = get_registry()
    manifests = registry.list_plugins()

    console.print()
    console.print(Panel.fit("[bold cyan]CLean-agents Plugins[/]", border_style="cyan"))
    console.print()

    if not manifests:
        console.print("[dim]No plugins installed.[/]")
        console.print("[dim]Place .py files in ~/.config/clean-agents/plugins/ or .clean-agents/plugins/[/]")
        return

    table = Table(show_header=True, header_style="bold", show_lines=False)
    table.add_column("Name", style="cyan")
    table.add_column("Version")
    table.add_column("Type")
    table.add_column("Command")
    table.add_column("Description")

    for m in manifests:
        type_color = {"analysis": "green", "scaffold": "blue", "transform": "yellow"}.get(m.plugin_type.value, "white")
        table.add_row(
            m.name,
            m.version,
            f"[{type_color}]{m.plugin_type.value}[/]",
            m.cli_command or "—",
            m.description[:60],
        )

    console.print(table)
    console.print()
    console.print(f"[dim]{len(manifests)} plugin(s) loaded[/]")
    console.print()


def plugin_run_cmd(
    name: str = typer.Argument(..., help="Plugin name to run"),
    path: str = typer.Option("", "--path", "-p", help="Blueprint file path"),
    output: str = typer.Option("", "--output", "-o", help="Output directory (for scaffold plugins)"),
) -> None:
    """Run a specific plugin against the current blueprint."""
    _ensure_builtins()
    registry = get_registry()
    config = Config.discover()

    bp_path = Path(path) if path else config.blueprint_path()
    if not bp_path.exists():
        console.print("[red]Error:[/] No blueprint found. Run [bold]clean-agents design[/] first.")
        raise typer.Exit(1)

    blueprint = Blueprint.load(bp_path)
    plugin = registry.get(name)

    if not plugin:
        console.print(f"[red]Error:[/] Plugin '{name}' not found.")
        console.print("[dim]Run [bold]clean-agents plugin list[/] to see available plugins.[/]")
        raise typer.Exit(1)

    manifest = plugin.manifest()
    console.print()
    console.print(Panel.fit(
        f"[bold]{manifest.name}[/] v{manifest.version} — {manifest.description}",
        border_style="cyan",
    ))
    console.print()

    # Execute based on type
    if isinstance(plugin, AnalysisPlugin):
        result = plugin.analyze(blueprint)
    elif isinstance(plugin, TransformPlugin):
        result = plugin.transform(blueprint)
        if result.modified_blueprint:
            result.modified_blueprint.save(bp_path)
            console.print(f"[green]✓[/] Blueprint updated at {bp_path}")
    elif isinstance(plugin, ScaffoldPlugin):
        out_dir = Path(output) if output else Path("./generated")
        result = plugin.scaffold(blueprint, out_dir)
    else:
        console.print("[red]Unknown plugin type[/]")
        raise typer.Exit(1)

    # Render results
    console.print(f"[bold]Summary:[/] {result.summary}")
    console.print()

    if result.findings:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Severity", width=10)
        table.add_column("Agent", style="cyan")
        table.add_column("Finding")
        table.add_column("Suggestion")

        severity_icons = {
            "critical": "[red]✗ CRIT[/]",
            "warning": "[yellow]! WARN[/]",
            "info": "[blue]i INFO[/]",
        }

        for f in result.findings:
            severity = f.get("severity", "info")
            agent = f.get("agent", f.get("agents", ["—"]))
            if isinstance(agent, list):
                agent = ", ".join(agent)
            table.add_row(
                severity_icons.get(severity, severity),
                agent,
                f.get("message", ""),
                f.get("suggestion", ""),
            )

        console.print(table)

    if result.data:
        console.print()
        for key, value in result.data.items():
            console.print(f"  [bold]{key}:[/] {value}")

    if result.files_generated:
        console.print()
        console.print("[bold]Files generated:[/]")
        for f in result.files_generated:
            console.print(f"  [green]✓[/] {f}")

    console.print()


def plugin_init_cmd(
    name: str = typer.Argument(..., help="Plugin name (kebab-case)"),
    plugin_type: str = typer.Option("analysis", "--type", "-t", help="Plugin type: analysis | scaffold | transform"),
    directory: str = typer.Option(".", "--dir", "-d", help="Directory to create plugin file"),
) -> None:
    """Scaffold a new plugin file with boilerplate."""
    ptype_map = {"analysis": "AnalysisPlugin", "scaffold": "ScaffoldPlugin", "transform": "TransformPlugin"}
    base_class = ptype_map.get(plugin_type)
    if not base_class:
        console.print(f"[red]Unknown plugin type: {plugin_type}[/]")
        raise typer.Exit(1)

    class_name = name.replace("-", "_").title().replace("_", "")

    template = f'''"""CLean-agents plugin: {name}"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from clean_agents.core.blueprint import Blueprint
from clean_agents.modules.base import (
    {base_class},
    PluginManifest,
    PluginResult,
    PluginType,
)


class {class_name}({base_class}):
    """TODO: Describe what this plugin does."""

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="{name}",
            version="0.1.0",
            description="TODO: One-line description",
            author="Your Name",
            plugin_type=PluginType.{plugin_type.upper()},
            cli_command="{name}",
        )
'''

    if plugin_type == "analysis":
        template += f'''
    def analyze(self, blueprint: Blueprint, config: dict[str, Any] | None = None) -> PluginResult:
        findings = []

        for agent in blueprint.agents:
            # TODO: Add your analysis logic here
            pass

        return PluginResult(
            plugin_name="{name}",
            success=True,
            findings=findings,
            summary=f"{{len(findings)}} findings",
        )
'''
    elif plugin_type == "transform":
        template += f'''
    def transform(self, blueprint: Blueprint, config: dict[str, Any] | None = None) -> PluginResult:
        # TODO: Modify the blueprint
        return PluginResult(
            plugin_name="{name}",
            success=True,
            modified_blueprint=blueprint,
            summary="Blueprint transformed",
        )
'''
    elif plugin_type == "scaffold":
        template += f'''
    def scaffold(
        self, blueprint: Blueprint, output_dir: Path, config: dict[str, Any] | None = None,
    ) -> PluginResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        # TODO: Generate files
        files = []
        return PluginResult(
            plugin_name="{name}",
            success=True,
            files_generated=files,
            summary=f"Generated {{len(files)}} files",
        )
'''

    out_file = Path(directory) / f"{name.replace('-', '_')}.py"
    out_file.write_text(template, encoding="utf-8")

    console.print(f"[green]✓[/] Plugin scaffolded at [bold]{out_file}[/]")
    console.print()
    console.print("[dim]To use:[/]")
    console.print(f"  1. Edit {out_file} and implement your logic")
    console.print(f"  2. Copy to ~/.config/clean-agents/plugins/ or .clean-agents/plugins/")
    console.print(f"  3. Run: clean-agents plugin run {name}")
    console.print()
