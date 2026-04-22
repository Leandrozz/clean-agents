"""`clean-agents skill-sync` — install the versioned Claude Code skill bundle."""

from __future__ import annotations

import hashlib
from importlib.resources import as_file, files
from importlib.resources.abc import Traversable
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()

DEFAULT_TARGET = Path.home() / ".claude" / "skills" / "clean-agents"
ASSETS_PACKAGE = "clean_agents.skill_assets"


def _walk_assets(root: Traversable, prefix: str = "") -> list[tuple[str, Traversable]]:
    """Yield (relative_posix_path, traversable) for every file under root."""
    out: list[tuple[str, Traversable]] = []
    for entry in root.iterdir():
        rel = f"{prefix}/{entry.name}" if prefix else entry.name
        if entry.is_dir():
            out.extend(_walk_assets(entry, rel))
        elif entry.is_file():
            out.append((rel, entry))
    return out


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _classify(source_bytes: bytes, target_path: Path) -> str:
    """Return one of: NEW, UPDATE, UNCHANGED."""
    if not target_path.exists():
        return "NEW"
    current = target_path.read_bytes()
    if _sha256(current) == _sha256(source_bytes):
        return "UNCHANGED"
    return "UPDATE"


def skill_sync_cmd(
    target: str = typer.Option(
        "",
        "--target",
        "-t",
        help=f"Install path for the skill bundle (default: {DEFAULT_TARGET})",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite locally modified files without prompting",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show which files would change; write nothing",
    ),
) -> None:
    """Install or update the canonical CLean-agents Claude Code skill at the target path."""
    target_dir = Path(target).expanduser() if target else DEFAULT_TARGET

    assets_root = files(ASSETS_PACKAGE)
    assets = _walk_assets(assets_root)
    if not assets:
        console.print(
            "[red]No skill_assets found in installed package — was the wheel built correctly?[/]"
        )
        raise typer.Exit(code=2)

    plan: list[tuple[str, str, Path, bytes]] = []  # (rel_path, action, target_path, source_bytes)
    for rel, resource in assets:
        # Read resource bytes via as_file for cross-platform safety (zip wheels, etc.)
        with as_file(resource) as src_path:
            src_bytes = Path(src_path).read_bytes()
        dst = target_dir / rel
        action = _classify(src_bytes, dst)
        plan.append((rel, action, dst, src_bytes))

    table = Table(title=f"skill-sync -> {target_dir}")
    table.add_column("Action")
    table.add_column("File")
    for rel, action, _, _ in plan:
        color = {"NEW": "green", "UPDATE": "yellow", "UNCHANGED": "dim"}.get(action, "")
        table.add_row(f"[{color}]{action}[/]" if color else action, rel)
    console.print(table)

    updates = [p for p in plan if p[1] == "UPDATE"]
    new_count = sum(1 for p in plan if p[1] == "NEW")

    if dry_run:
        console.print("[dim]--dry-run: no files written.[/]")
        return

    if updates and not force:
        console.print(
            f"[red]{len(updates)} file(s) would overwrite local edits. "
            f"Re-run with --force to proceed.[/]"
        )
        raise typer.Exit(code=1)

    if not updates and new_count == 0:
        console.print("[green]Already up to date — no changes.[/]")
        return

    # Apply
    for _, action, dst, src_bytes in plan:
        if action == "UNCHANGED":
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src_bytes)

    console.print(
        f"[green]Installed:[/] {new_count} new, {len(updates)} updated, "
        f"{len(plan) - new_count - len(updates)} unchanged."
    )
