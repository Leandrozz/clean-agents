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
