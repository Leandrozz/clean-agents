from uuid import UUID

from clean_agents.crafters.base import ArtifactSpec, ArtifactType
from clean_agents.crafters.session import (
    DesignConfig,
    DesignSession,
    Phase,
)


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
