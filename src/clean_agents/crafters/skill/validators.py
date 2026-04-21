"""Skill-vertical validator rules (L1-L4)."""

from __future__ import annotations

import re

from clean_agents.crafters.base import ArtifactType
from clean_agents.crafters.skill.spec import SkillSpec
from clean_agents.crafters.validators.base import (
    Level,
    Severity,
    ValidationContext,
    ValidationFinding,
    ValidatorBase,
    ValidatorRegistry,
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


class SkillL1DescLength(ValidatorBase[SkillSpec]):
    level = Level.L1
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L1-DESC-LENGTH"
    MIN = 50
    MAX = 500

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        n = len(spec.description)
        if self.MIN <= n <= self.MAX:
            return []
        return [
            ValidationFinding(
                rule_id=self.rule_id,
                severity=Severity.CRITICAL,
                message=f"description length {n} outside [{self.MIN}, {self.MAX}]",
                location="spec.description",
                fix_hint=(
                    "Shorten to ≤500 chars while preserving distinctive triggers"
                    if n > self.MAX else "Expand to ≥50 chars with concrete activation cues"
                ),
                auto_fixable=False,
            )
        ]


class SkillL1RefsExist(ValidatorBase[SkillSpec]):
    level = Level.L1
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L1-REFS-EXIST"

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        if ctx.bundle_root is None:
            return []
        out: list[ValidationFinding] = []
        for ref in spec.references:
            path = ctx.bundle_root / ref.path
            if not path.exists():
                out.append(ValidationFinding(
                    rule_id=self.rule_id,
                    severity=Severity.HIGH,
                    message=f"reference declared but missing on disk: {ref.path}",
                    location=str(ref.path),
                    fix_hint=f"Create {ref.path} or remove it from spec.references.",
                    auto_fixable=True,
                ))
        return out


class SkillL1RefsOrphan(ValidatorBase[SkillSpec]):
    level = Level.L1
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L1-REFS-ORPHAN"

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        if ctx.bundle_root is None:
            return []
        refs_dir = ctx.bundle_root / "references"
        if not refs_dir.exists():
            return []
        declared = {ref.path.name for ref in spec.references}
        out: list[ValidationFinding] = []
        for path in refs_dir.glob("*.md"):
            if path.name not in declared:
                out.append(ValidationFinding(
                    rule_id=self.rule_id,
                    severity=Severity.MEDIUM,
                    message=f"file in references/ not referenced from spec: {path.name}",
                    location=str(path.relative_to(ctx.bundle_root)),
                    fix_hint=(
                        f"Add {path.name} to spec.references or delete it."
                    ),
                    auto_fixable=False,
                ))
        return out


_PCT_RE = re.compile(r"\b\d+\.\d+\s?%")
_CVE_RE = re.compile(r"\bCVE-\d{4}-\d+\b", re.IGNORECASE)
_PAPER_RE = re.compile(r"\bpaper de \d{4}\b", re.IGNORECASE)
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def _iter_body_text(spec: SkillSpec) -> list[tuple[str, str]]:
    """Yield (location, text) per section."""
    return [(f"body_outline[{i}]", s.body) for i, s in enumerate(spec.body_outline)]


class SkillL2HardcodedStats(ValidatorBase[SkillSpec]):
    level = Level.L2
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L2-HARDCODED-STATS"

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        out: list[ValidationFinding] = []
        patterns = [
            (_PCT_RE, "percentage"),
            (_CVE_RE, "CVE id"),
            (_PAPER_RE, "paper year"),
        ]
        for loc, text in _iter_body_text(spec):
            for pat, kind in patterns:
                for m in pat.finditer(text):
                    out.append(ValidationFinding(
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        message=f"hard-coded {kind} ages poorly: {m.group(0)!r}",
                        location=loc,
                        fix_hint=(
                            f"Move {m.group(0)!r} to references/ "
                            "so it can be updated independently."
                        ),
                    ))
        return out


class SkillL2HardcodedDates(ValidatorBase[SkillSpec]):
    level = Level.L2
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L2-HARDCODED-DATES"

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        out: list[ValidationFinding] = []
        for loc, text in _iter_body_text(spec):
            for m in _YEAR_RE.finditer(text):
                out.append(ValidationFinding(
                    rule_id=self.rule_id,
                    severity=Severity.MEDIUM,
                    message=f"hard-coded year {m.group(0)!r} ages poorly",
                    location=loc,
                    fix_hint="Replace with a relative reference or move to references/.",
                ))
        return out


def register_builtin(registry: ValidatorRegistry) -> None:
    """Called from crafters package init to register L1 validators."""
    registry.register(SkillL1NameDir())
    registry.register(SkillL1DescLength())
    registry.register(SkillL1RefsExist())
    registry.register(SkillL1RefsOrphan())
