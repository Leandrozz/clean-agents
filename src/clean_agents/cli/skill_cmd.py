"""CLI for the Skills vertical of crafters (M1 stubs; filled in M6)."""

from __future__ import annotations

import json as _json
import sys as _sys
from pathlib import Path as _Path

import typer
import yaml as _yaml
from rich.console import Console
from rich.table import Table

from clean_agents.crafters.base import ArtifactType
from clean_agents.crafters.skill.spec import SkillSpec
from clean_agents.crafters.validators.base import (
    Level,
    Severity,
    ValidationContext,
    ValidationReport,
    get_registry,
)
from clean_agents.crafters.validators.collision import default_installed_roots

console = Console()


def _load_spec(path: _Path) -> tuple[SkillSpec, _Path | None]:
    """Accept either a bundle directory (with .skill-spec.yaml) or a YAML file."""
    if path.is_dir():
        yaml_path = path / ".skill-spec.yaml"
        bundle_root: _Path | None = path
    else:
        yaml_path = path
        bundle_root = path.parent if path.parent.exists() else None
    data = _yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    return SkillSpec.model_validate(data), bundle_root


def _run_validators(
    spec: SkillSpec,
    ctx: ValidationContext,
    levels: set[Level],
) -> ValidationReport:
    report = ValidationReport()
    for v in get_registry().for_artifact(ArtifactType.SKILL):
        if v.level not in levels:
            continue
        try:
            report.findings.extend(v.check(spec, ctx))
        except Exception as e:
            report.findings.append(
                # Surface validator bugs instead of swallowing (no silent failures)
                _finding_for_exception(v.rule_id, e),
            )
    return report


def _finding_for_exception(rule_id: str, err: Exception):
    from clean_agents.crafters.validators.base import (
        Severity as _S,
        ValidationFinding as _VF,
    )

    return _VF(
        rule_id=rule_id,
        severity=_S.INFO,
        message=f"validator {rule_id} raised {type(err).__name__}: {err}",
        fix_hint="File an issue at github.com/Leandrozz/clean-agents with the full traceback.",
    )


def design_cmd(
    description: str = typer.Argument("", help="Natural-language description"),
    ai: bool = typer.Option(False, "--ai", help="Use Anthropic SDK for richer recommendations"),
    for_agent: str = typer.Option("", "--for-agent", help="Link this skill to a specific agent"),
    blueprint: str = typer.Option("", "--blueprint", help="Blueprint YAML to pre-load context"),
    spec: str = typer.Option("", "--spec", help="Structured YAML input"),
    no_interactive: bool = typer.Option(
        False, "--no-interactive", help="One-shot from --spec / description"
    ),
    lang: str = typer.Option("en", "--lang", help="Output language (en, es, pt)"),
    output: str = typer.Option(".", "--output", "-o", help="Output bundle directory"),
) -> None:
    from clean_agents.crafters.session import DesignConfig, DesignSession

    if spec:
        spec_data = _yaml.safe_load(_Path(spec).read_text(encoding="utf-8"))
        skill_spec = SkillSpec.model_validate(spec_data)
    elif description:
        # Minimal heuristic draft from NL description
        desc = description.strip()
        if len(desc) < 50:
            desc = (desc + " — designed via clean-agents skill design --no-interactive.").strip()
        if len(desc) > 500:
            desc = desc[:497] + "..."
        # Derive a kebab-case name
        name = "-".join(
            tok.lower() for tok in desc.split()[:3] if tok.isalnum()
        ) or "unnamed-skill"
        skill_spec = SkillSpec(
            name=name,
            description=desc,
            language=lang,
            triggers=[tok.lower() for tok in desc.split()[:5] if tok.isalnum()],
            references=[],
            body_outline=[],
        )
    else:
        console.print("[red]Provide either --spec or a description argument.[/]")
        raise typer.Exit(code=2)

    session = DesignSession[SkillSpec](
        spec=skill_spec,
        config=DesignConfig(enable_ai=ai, language=lang, interactive=not no_interactive),
    )
    session.intake(skill_spec)

    if not no_interactive:
        console.print("[yellow]Interactive design loop coming in M7; running one-shot for now.[/]")

    bundle = session.render(_Path(output))
    console.print(f"[green]Bundle written:[/] {bundle.output_dir}")


def validate_cmd(
    path: str = typer.Argument(..., help="Path to skill bundle or .skill-spec.yaml"),
    level: str = typer.Option("L1,L2,L3", "--level", help="Comma-separated levels"),
    eval_: bool = typer.Option(
        False, "--eval", help="Include L4 runtime eval (requires ANTHROPIC_API_KEY)"
    ),
    fmt: str = typer.Option("table", "--format", help="table | json | md"),
) -> None:
    """Validate a Skill against L1/L2/L3 rules (stub — wired in M6)."""
    p = _Path(path)
    if not p.exists():
        console.print(f"[red]path not found:[/] {p}")
        raise typer.Exit(code=2)
    spec, bundle_root = _load_spec(p)

    levels = {Level(tok.strip()) for tok in level.split(",")}
    if eval_:
        levels.add(Level.L4)

    ctx = ValidationContext(
        bundle_root=bundle_root,
        installed_roots=default_installed_roots(),
    )
    report = _run_validators(spec, ctx, levels)

    if fmt == "json":
        # Write straight to stdout so CliRunner captures the JSON verbatim
        # (Rich's Console would otherwise wrap/highlight multi-line JSON).
        _sys.stdout.write(_json.dumps(report.model_dump(mode="json"), indent=2))
        _sys.stdout.write("\n")
    elif fmt == "md":
        for f in report.findings:
            console.print(
                f"- **{f.severity.value.upper()}** `{f.rule_id}` — {f.message}"
            )
    else:
        if not report.findings:
            console.print("[green]No findings — skill passes validation.[/]")
        else:
            table = Table(title=f"Validation findings for {spec.name}")
            table.add_column("Severity")
            table.add_column("Rule")
            table.add_column("Message")
            table.add_column("Location")
            for f in report.findings:
                table.add_row(f.severity.value, f.rule_id, f.message, f.location or "—")
            console.print(table)

    if report.has_critical() or report.has_blocking():
        raise typer.Exit(code=1)


def render_cmd(
    spec: str = typer.Argument(..., help="Path to .skill-spec.yaml"),
    output: str = typer.Option(..., "--output", "-o", help="Output bundle directory"),
    zip_: bool = typer.Option(False, "--zip", help="Package as .skill zip"),
    force: bool = typer.Option(False, "--force", help="Ignore HIGH/CRITICAL findings"),
) -> None:
    p = _Path(spec)
    if not p.exists():
        console.print(f"[red]spec not found:[/] {p}")
        raise typer.Exit(code=2)

    skill_spec = SkillSpec.model_validate(_yaml.safe_load(p.read_text(encoding="utf-8")))
    out_dir = _Path(output)

    ctx = ValidationContext(bundle_root=out_dir, installed_roots=default_installed_roots())
    report = _run_validators(skill_spec, ctx, {Level.L1, Level.L2, Level.L3})

    if report.has_critical() and not force:
        console.print("[red]Render blocked — critical findings present.[/]")
        for f in report.findings:
            if f.severity is Severity.CRITICAL:
                console.print(f"  CRITICAL {f.rule_id}: {f.message}")
        raise typer.Exit(code=1)

    from clean_agents.crafters.skill.scaffold import render_skill_bundle
    bundle = render_skill_bundle(skill_spec, out_dir)
    console.print(f"[green]Bundle rendered:[/] {bundle.output_dir}")

    if zip_:
        import shutil
        shutil.make_archive(str(out_dir), "zip", out_dir)
        console.print(f"[green]Zipped:[/] {out_dir}.zip")


def publish_cmd(
    spec: str = typer.Argument(..., help="Path to .skill-spec.yaml"),
) -> None:
    """Publish a Skill to the marketplace (stub — wired in M6)."""
    console.print(f"[yellow]skill publish {spec}: coming in M6[/]")
