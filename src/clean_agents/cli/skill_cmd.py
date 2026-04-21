"""CLI for the Skills vertical of crafters (M1 stubs; filled in M6)."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def design_cmd(
    description: str = typer.Argument("", help="Natural-language description"),
) -> None:
    """Start an interactive Skill design session (stub — wired in M6)."""
    console.print("[yellow]skill design: coming in M6[/]")


def validate_cmd(
    path: str = typer.Argument(..., help="Path to skill bundle or .skill-spec.yaml"),
) -> None:
    """Validate a Skill against L1/L2/L3 rules (stub — wired in M6)."""
    console.print(f"[yellow]skill validate {path}: coming in M6[/]")


def render_cmd(
    spec: str = typer.Argument(..., help="Path to .skill-spec.yaml"),
) -> None:
    """Render a Skill bundle from a spec (stub — wired in M6)."""
    console.print(f"[yellow]skill render {spec}: coming in M6[/]")


def publish_cmd(
    spec: str = typer.Argument(..., help="Path to .skill-spec.yaml"),
) -> None:
    """Publish a Skill to the marketplace (stub — wired in M6)."""
    console.print(f"[yellow]skill publish {spec}: coming in M6[/]")
