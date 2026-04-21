"""Skill-vertical validator rules (L1-L4)."""

from __future__ import annotations

from clean_agents.crafters.base import ArtifactType
from clean_agents.crafters.skill.spec import SkillSpec
from clean_agents.crafters.validators.base import (
    Level,
    Severity,
    ValidationContext,
    ValidationFinding,
    ValidatorBase,
)


class SkillL1NameDir(ValidatorBase[SkillSpec]):
    level = Level.L1
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L1-NAME-DIR"

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        if ctx.bundle_root is None:
            return []
        if ctx.bundle_root.name != spec.name:
            return [
                ValidationFinding(
                    rule_id=self.rule_id,
                    severity=Severity.HIGH,
                    message=(
                        f"spec.name={spec.name!r} does not match bundle directory "
                        f"{ctx.bundle_root.name!r}"
                    ),
                    location=str(ctx.bundle_root),
                    fix_hint=f"Rename the directory to {spec.name!r} or update spec.name.",
                    auto_fixable=False,
                )
            ]
        return []
