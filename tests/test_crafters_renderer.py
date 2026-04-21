from pathlib import Path

import yaml

from clean_agents.crafters.skill.scaffold import render_skill_bundle
from clean_agents.crafters.skill.spec import (
    EvalCase,
    EvalsManifest,
    ReferenceFile,
    SkillSection,
    SkillSpec,
)


def test_render_bundle_produces_expected_files(tmp_path: Path):
    spec = SkillSpec(
        name="demo-skill",
        description="Fixture skill for BundleRenderer unit testing.",
        triggers=["demo", "fixture"],
        references=[
            ReferenceFile(
                path=Path("references/taxonomy.md"),
                topic="Taxonomy",
                outline=["Intro"],
            )
        ],
        body_outline=[
            SkillSection(
                heading="Overview",
                body="See references/taxonomy.md.",
                anchor="overview",
            )
        ],
        evals=EvalsManifest(
            positive_cases=[
                EvalCase(prompt="demo prompt", expected="activate")
            ],
            negative_cases=[EvalCase(prompt="unrelated", expected="ignore")],
        ),
    )
    bundle = render_skill_bundle(spec, output_dir=tmp_path / "out")
    assert (bundle.output_dir / "SKILL.md").exists()
    assert (bundle.output_dir / "README.md").exists()
    assert (bundle.output_dir / "references" / "taxonomy.md").exists()
    assert (bundle.output_dir / "evals" / "evals.json").exists()
    assert (bundle.output_dir / ".skill-spec.yaml").exists()


def test_roundtrip_spec_yaml(tmp_path: Path):
    spec = SkillSpec(
        name="roundtrip",
        description="Fixture for round-trip YAML; survives save + load.",
        triggers=["roundtrip"],
        references=[],
        body_outline=[],
    )
    bundle = render_skill_bundle(spec, output_dir=tmp_path / "rt")
    loaded = yaml.safe_load((bundle.output_dir / ".skill-spec.yaml").read_text(encoding="utf-8"))
    assert loaded["name"] == "roundtrip"
    restored = SkillSpec.model_validate(loaded)
    assert restored.description == spec.description


def test_rerender_preserves_existing_reference_file(tmp_path: Path):
    """Re-rendering a bundle must NOT overwrite a human-edited reference file."""
    spec = SkillSpec(
        name="preserve-test",
        description="Verify reference files are not re-written on re-render.",
        triggers=["preserve"],
        references=[
            ReferenceFile(
                path=Path("references/notes.md"),
                topic="Notes",
                outline=["Intro"],
            )
        ],
        body_outline=[],
    )
    bundle = render_skill_bundle(spec, output_dir=tmp_path / "out")
    ref_file = bundle.output_dir / "references" / "notes.md"
    # Human edits the reference file after the first render.
    edited = "# Notes\n\nUser hand-written content.\n"
    ref_file.write_text(edited, encoding="utf-8")
    # Re-render the bundle — the user's edits must be preserved.
    render_skill_bundle(spec, output_dir=bundle.output_dir)
    assert ref_file.read_text(encoding="utf-8") == edited


def test_reference_path_escaping_is_rejected(tmp_path: Path):
    """A ReferenceFile whose path escapes the output directory must be rejected."""
    import pytest

    spec = SkillSpec(
        name="path-escape",
        description="Verify path traversal is rejected for reference files.",
        triggers=["escape"],
        references=[
            ReferenceFile(path=Path("../evil.md"), topic="Evil", outline=[])
        ],
        body_outline=[],
    )
    with pytest.raises(ValueError, match="escapes the output directory"):
        render_skill_bundle(spec, output_dir=tmp_path / "safe")
