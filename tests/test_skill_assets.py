"""Confirm the skill_assets bundle is shipped with the package and readable via importlib."""

from __future__ import annotations

from importlib.resources import files


def test_skill_md_resource_is_accessible():
    skill_md = files("clean_agents.skill_assets").joinpath("SKILL.md")
    assert skill_md.is_file(), "skill_assets/SKILL.md missing — not packaged with the wheel"
    content = skill_md.read_text(encoding="utf-8")
    assert "CLean-agents" in content
    assert "## Crafters:" in content, "Crafters section not present in canonical SKILL.md"


def test_crafters_reference_is_accessible():
    ref = files("clean_agents.skill_assets.references").joinpath("crafters.md")
    assert ref.is_file()
    content = ref.read_text(encoding="utf-8")
    assert "SKILL-L1-NAME-DIR" in content
    assert "`.skill-spec.yaml`" in content


def test_all_twelve_original_references_are_bundled():
    expected = {
        "architecture-patterns.md", "compliance-mapper.md", "cost-simulator.md",
        "eval-suite.md", "load-testing.md", "migration-advisor.md",
        "model-choosing.md", "observability.md", "output-templates.md",
        "prompt-engineering.md", "security-testing.md", "taxonomy.md",
    }
    refs_dir = files("clean_agents.skill_assets.references")
    names = {p.name for p in refs_dir.iterdir() if p.name.endswith(".md")}
    missing = expected - names
    assert not missing, f"missing references in bundle: {missing}"
