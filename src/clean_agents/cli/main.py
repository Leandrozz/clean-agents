"""CLean-agents CLI — main entrypoint.

Usage:
    clean-agents init          Initialize a new project
    clean-agents design        Start interactive architecture session
    clean-agents blueprint     View / export the current blueprint
    clean-agents shield        Run security hardening analysis
    clean-agents cost          Run cost simulator
    clean-agents eval          Generate evaluation suite
    clean-agents observe       Generate observability blueprint
    clean-agents prompts       Generate optimized prompt templates
    clean-agents models        Run model selection analysis
    clean-agents migrate       Run migration advisor
    clean-agents comply        Run compliance mapper
    clean-agents load          Generate load testing plan
    clean-agents scaffold      Generate framework-specific starter code
    clean-agents serve         Start API server
    clean-agents version       Show version info
"""

from __future__ import annotations

import typer
from rich.console import Console

from clean_agents import __version__

console = Console()
app = typer.Typer(
    name="clean-agents",
    help="Design, plan, and harden production-grade agentic AI systems.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold cyan]CLean-agents[/] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version", callback=version_callback, is_eager=True,
    ),
) -> None:
    """CLean-agents: your agentic architecture consultant."""


# ── Import and register sub-commands ──────────────────────────────────────────

from clean_agents.cli.init_cmd import init_cmd  # noqa: E402
from clean_agents.cli.design_cmd import design_cmd  # noqa: E402
from clean_agents.cli.blueprint_cmd import blueprint_cmd  # noqa: E402
from clean_agents.cli.diff_cmd import diff_cmd  # noqa: E402
from clean_agents.cli.shield_cmd import shield_cmd  # noqa: E402
from clean_agents.cli.module_cmds import cost_cmd, eval_cmd, observe_cmd, models_cmd  # noqa: E402
from clean_agents.cli.module_cmds import prompts_cmd, migrate_cmd, comply_cmd, load_cmd  # noqa: E402
from clean_agents.cli.scaffold_cmd import scaffold_cmd  # noqa: E402
from clean_agents.cli.export_cmd import export_cmd  # noqa: E402
from clean_agents.cli.plugin_cmd import plugin_list_cmd, plugin_run_cmd, plugin_init_cmd  # noqa: E402
from clean_agents.cli.marketplace_cmd import (  # noqa: E402
    marketplace_search_cmd,
    marketplace_info_cmd,
    marketplace_install_cmd,
    marketplace_list_cmd,
)
from clean_agents.cli.harness_cmd import harness_run_cmd, harness_trace_cmd  # noqa: E402
from clean_agents.cli.benchmark_cmd import benchmark_run_cmd, benchmark_compare_cmd, benchmark_suite_cmd  # noqa: E402
from clean_agents.cli.history_cmd import history_list_cmd, history_restore_cmd, history_diff_cmd  # noqa: E402
from clean_agents.cli.knowledge_cmd import (  # noqa: E402
    knowledge_list_cmd,
    knowledge_add_cmd,
    knowledge_import_cmd,
    knowledge_export_cmd,
)
from clean_agents.cli.telemetry_cmd import (  # noqa: E402
    telemetry_status_cmd,
    telemetry_enable_cmd,
    telemetry_disable_cmd,
    telemetry_export_cmd,
    telemetry_clear_cmd,
)

app.command("init", help="Initialize a new CLean-agents project")(init_cmd)
app.command("design", help="Start interactive architecture design session")(design_cmd)
app.command("blueprint", help="View, export, or diff the current blueprint")(blueprint_cmd)
app.command("diff", help="Compare two blueprints side-by-side")(diff_cmd)
app.command("shield", help="Run CLean-shield security analysis")(shield_cmd)
app.command("cost", help="Run cost simulator")(cost_cmd)
app.command("eval", help="Generate evaluation suite")(eval_cmd)
app.command("observe", help="Generate observability blueprint")(observe_cmd)
app.command("models", help="Run model selection analysis")(models_cmd)
app.command("prompts", help="Generate optimized prompt templates")(prompts_cmd)
app.command("migrate", help="Run migration advisor")(migrate_cmd)
app.command("comply", help="Run compliance mapper")(comply_cmd)
app.command("load", help="Generate load testing plan")(load_cmd)
app.command("scaffold", help="Generate starter code for chosen framework")(scaffold_cmd)
app.command("export", help="Export blueprint as deployment infrastructure")(export_cmd)

# Plugin subcommands
plugin_app = typer.Typer(name="plugin", help="Manage and run plugins", no_args_is_help=True)
plugin_app.command("list", help="List all available plugins")(plugin_list_cmd)
plugin_app.command("run", help="Run a specific plugin")(plugin_run_cmd)
plugin_app.command("init", help="Scaffold a new plugin file")(plugin_init_cmd)
app.add_typer(plugin_app)

# Harness subcommands
harness_app = typer.Typer(name="harness", help="Run and test agent systems", no_args_is_help=True)
harness_app.command("run", help="Run the agent harness against a blueprint")(harness_run_cmd)
harness_app.command("trace", help="Display detailed execution trace")(harness_trace_cmd)
app.add_typer(harness_app)

# Benchmark subcommands
benchmark_app = typer.Typer(name="benchmark", help="Benchmark and compare blueprints", no_args_is_help=True)
benchmark_app.command("run", help="Run benchmarks against a blueprint")(benchmark_run_cmd)
benchmark_app.command("compare", help="Compare multiple blueprints side-by-side")(benchmark_compare_cmd)
benchmark_app.command("suite", help="Generate a benchmark suite for customization")(benchmark_suite_cmd)
app.add_typer(benchmark_app)

# Marketplace subcommands
marketplace_app = typer.Typer(
    name="marketplace",
    help="Browse and install community plugins",
    no_args_is_help=True,
)
marketplace_app.command("search", help="Search the plugin marketplace")(marketplace_search_cmd)
marketplace_app.command("list", help="List all plugins in the marketplace")(marketplace_list_cmd)
marketplace_app.command("info", help="Show detailed info about a plugin")(marketplace_info_cmd)
marketplace_app.command("install", help="Install a plugin from the marketplace")(marketplace_install_cmd)
app.add_typer(marketplace_app)

# History subcommands
history_app = typer.Typer(
    name="history",
    help="Blueprint version history",
    no_args_is_help=True,
)
history_app.command("list", help="Show blueprint version history")(history_list_cmd)
history_app.command("restore", help="Restore blueprint to a specific version")(history_restore_cmd)
history_app.command("diff", help="Diff two blueprint versions")(history_diff_cmd)
app.add_typer(history_app)

# Knowledge subcommands
knowledge_app = typer.Typer(
    name="knowledge",
    help="Manage the knowledge base (models, frameworks, compliance)",
    no_args_is_help=True,
)
knowledge_app.command("list", help="List knowledge base entries")(knowledge_list_cmd)
knowledge_app.command("add", help="Add or update a knowledge entry")(knowledge_add_cmd)
knowledge_app.command("import", help="Import knowledge updates from YAML")(knowledge_import_cmd)
knowledge_app.command("export", help="Export knowledge base to YAML")(knowledge_export_cmd)
app.add_typer(knowledge_app)

# Telemetry subcommands
telemetry_app = typer.Typer(
    name="telemetry",
    help="Manage local usage telemetry",
    no_args_is_help=True,
)
telemetry_app.command("status", help="Show telemetry status and summary")(telemetry_status_cmd)
telemetry_app.command("enable", help="Enable local telemetry collection")(telemetry_enable_cmd)
telemetry_app.command("disable", help="Disable telemetry (optionally clear data with --clear)")(
    telemetry_disable_cmd
)
telemetry_app.command("export", help="Export telemetry data to a file")(telemetry_export_cmd)
telemetry_app.command("clear", help="Delete all telemetry data")(telemetry_clear_cmd)
app.add_typer(telemetry_app)

from clean_agents.cli.skill_cmd import (  # noqa: E402
    design_cmd as skill_design_cmd,
    validate_cmd as skill_validate_cmd,
    render_cmd as skill_render_cmd,
    publish_cmd as skill_publish_cmd,
    install_cmd as skill_install_cmd,
    list_cmd as skill_list_cmd,
)

skill_app = typer.Typer(
    name="skill",
    help="Design, validate, render, and publish Claude Code Skills",
    no_args_is_help=True,
)
skill_app.command("design", help="Start an interactive Skill design session")(skill_design_cmd)
skill_app.command("validate", help="Validate a Skill bundle or spec")(skill_validate_cmd)
skill_app.command("render", help="Render a Skill bundle from .skill-spec.yaml")(skill_render_cmd)
skill_app.command("publish", help="Publish a Skill to the marketplace")(skill_publish_cmd)
skill_app.command("install", help="Install a skill from the marketplace")(skill_install_cmd)
skill_app.command("list", help="List installed and/or marketplace skills")(skill_list_cmd)
app.add_typer(skill_app)


@app.command("serve")
def serve_cmd(
    host: str = typer.Option("127.0.0.1", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
    mode: str = typer.Option("api", help="Server mode: api | mcp"),
    auth: bool = typer.Option(False, "--auth", help="Enable API key authentication"),
    api_key: str = typer.Option("", "--api-key", help="Set a single API key (or use CLEAN_AGENTS_API_KEYS env)"),
    rate_limit: int = typer.Option(60, "--rate-limit", help="Requests per minute per key"),
) -> None:
    """Start the CLean-agents server (API or MCP mode).

    Authentication:
        Use --auth to enable API key authentication.
        Provide keys via --api-key (single key) or CLEAN_AGENTS_API_KEYS env (comma-separated).

    Rate limiting:
        Use --rate-limit to set requests per minute (default: 60).
        Configure burst with CLEAN_AGENTS_RATE_LIMIT_BURST env var.

    Example:
        clean-agents serve --auth --api-key mykey123 --rate-limit 100
    """
    if mode == "mcp":
        console.print("[bold cyan]Starting CLean-agents MCP server[/] (stdio mode)")
        from clean_agents.server.mcp_server import run_mcp_stdio
        run_mcp_stdio()
    else:
        console.print(f"[bold cyan]Starting CLean-agents API server[/] on {host}:{port}")

        # Configure authentication if enabled
        auth_config = None
        if auth or api_key:
            from clean_agents.server.auth import AuthConfig
            import os

            # Determine API keys
            api_keys = []
            if api_key:
                api_keys = [api_key]
            else:
                # Try to load from env
                env_keys = os.getenv("CLEAN_AGENTS_API_KEYS", "")
                api_keys = [k.strip() for k in env_keys.split(",") if k.strip()]

            if not api_keys:
                console.print("[yellow]Warning: --auth enabled but no API keys provided[/]")
                console.print("Set CLEAN_AGENTS_API_KEYS env or use --api-key")

            auth_config = AuthConfig(
                enabled=True,
                api_keys=api_keys,
                rate_limit_rpm=rate_limit,
            )
            console.print(f"[green]Auth enabled[/] with {len(api_keys)} key(s), {rate_limit} req/min")

        from clean_agents.server.api import run_server
        run_server(host=host, port=port, auth_config=auth_config)


if __name__ == "__main__":
    app()
