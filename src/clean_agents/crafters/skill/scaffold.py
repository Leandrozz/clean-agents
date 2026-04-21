"""Write a Skill bundle to disk using the Jinja2 templates in templates/."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from clean_agents.crafters.renderer import BundleRenderer
from clean_agents.crafters.session import Bundle
from clean_agents.crafters.skill.spec import SkillSpec

_TEMPLATES = Path(__file__).parent / "templates"
_PROJECT_URL = "https://github.com/Leandrozz/clean-agents"


def render_skill_bundle(spec: SkillSpec, output_dir: Path) -> Bundle:
    """Render a Skill bundle directory. Returns Bundle pointing at output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    r = BundleRenderer(_TEMPLATES)

    # SKILL.md
    skill_md = r.render("SKILL.md.j2", {"spec": spec})
    (output_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    # README.md
    readme = r.render("README.md.j2", {"spec": spec, "project_url": _PROJECT_URL})
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    # References scaffolds
    refs_dir = output_dir / "references"
    refs_dir.mkdir(exist_ok=True)
    out_resolved = output_dir.resolve()
    for ref in spec.references:
        target = output_dir / ref.path
        if not target.resolve().is_relative_to(out_resolved):
            raise ValueError(
                f"reference path {ref.path!r} escapes the output directory"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text(r.render("reference.md.j2", {"ref": ref}), encoding="utf-8")

    # Evals
    if spec.evals is not None:
        evals_dir = output_dir / "evals"
        evals_dir.mkdir(exist_ok=True)
        rendered = r.render("evals.json.j2", {"spec": spec})
        # Normalize via json.loads/dumps to guarantee valid JSON
        (evals_dir / "evals.json").write_text(
            json.dumps(json.loads(rendered), indent=2), encoding="utf-8"
        )

    # Source-of-truth YAML
    data = spec.model_dump(mode="json", exclude_none=True)
    (output_dir / ".skill-spec.yaml").write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    files = [p for p in output_dir.rglob("*") if p.is_file()]
    return Bundle(output_dir=output_dir, files=files)
