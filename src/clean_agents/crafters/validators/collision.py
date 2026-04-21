"""Cross-artifact collision scanner (L3)."""

from __future__ import annotations

from pathlib import Path


def installed_skill_names(roots: list[Path]) -> dict[str, Path]:
    """Return name → path for every subdir in any root (shallow scan)."""
    out: dict[str, Path] = {}
    for root in roots:
        if not root.exists():
            continue
        for p in root.iterdir():
            if p.is_dir() and not p.name.startswith("."):
                out.setdefault(p.name, p)
    return out


def default_installed_roots() -> list[Path]:
    home = Path.home()
    return [
        home / ".claude" / "skills",
        home / ".claude" / "plugins",
        Path(".claude") / "skills",
    ]
