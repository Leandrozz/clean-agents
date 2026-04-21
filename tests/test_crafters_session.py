from pathlib import Path
from uuid import UUID

from clean_agents.crafters.base import ArtifactSpec, ArtifactType
from clean_agents.crafters.session import (
    DesignConfig,
    DesignSession,
    Phase,
)
from clean_agents.crafters.skill.spec import SkillSpec


class _Spec(ArtifactSpec):
    artifact_type: ArtifactType = ArtifactType.SKILL


def _skeleton_spec() -> _Spec:
    return _Spec(
        name="test-skill",
        description="A fixture skill used for session state-machine unit tests.",
        artifact_type=ArtifactType.SKILL,
    )


def test_session_initial_phase_is_intake():
    s = DesignSession[_Spec](spec=_skeleton_spec(), config=DesignConfig())
    assert s.phase is Phase.INTAKE
    assert isinstance(s.session_id, UUID)


def test_phase_enum_has_six_values():
    assert {p.value for p in Phase} == {
        "intake", "recommend", "deep_dive", "bundle", "iterate", "modules",
    }


def _skill() -> SkillSpec:
    return SkillSpec(
        name="session-skill",
        description="A fixture used to test DesignSession state transitions end-to-end.",
        triggers=["session", "fixture"],
        references=[], body_outline=[],
    )


def test_intake_transitions_to_recommend():
    s = DesignSession[SkillSpec](spec=_skill(), config=DesignConfig())
    s.intake(_skill())
    assert s.phase is Phase.RECOMMEND


def test_render_transitions_to_bundle(tmp_path: Path):
    s = DesignSession[SkillSpec](spec=_skill(), config=DesignConfig())
    s.intake(_skill())
    bundle = s.render(tmp_path / "out")
    assert s.phase is Phase.BUNDLE
    assert bundle.output_dir.exists()


def test_iterate_records_delta_and_reenters_recommend():
    s = DesignSession[SkillSpec](spec=_skill(), config=DesignConfig())
    s.intake(_skill())
    desc = "Shorter description, still over fifty characters in length."
    report = s.iterate({"description": desc})
    assert report.deltas
    assert s.phase is Phase.ITERATE


def test_session_save_load_roundtrip(tmp_path: Path):
    s1 = DesignSession[SkillSpec](spec=_skill(), config=DesignConfig())
    s1.intake(_skill())
    s1.save(tmp_path / "session.yaml")
    s2 = DesignSession[SkillSpec].load(tmp_path / "session.yaml")
    assert s2.spec.name == s1.spec.name
    assert s2.phase is s1.phase
