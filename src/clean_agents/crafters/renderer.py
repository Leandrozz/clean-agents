"""Generic Jinja2-based bundle renderer. Verticals wrap this with their templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined


class BundleRenderer:
    def __init__(self, template_dir: Path) -> None:
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            undefined=StrictUndefined,
            keep_trailing_newline=True,
        )

    def render(self, template_name: str, ctx: dict[str, Any]) -> str:
        return self.env.get_template(template_name).render(**ctx)
