"""Validator base classes and types for the crafter pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from clean_agents.crafters.base import ArtifactSpec, ArtifactType

T = TypeVar("T", bound=ArtifactSpec)


class Severity(str, Enum):
    """Severity levels for validation findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    def rank(self) -> int:
        """Return numeric rank for comparison. Higher = more severe."""
        return {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}[self.value]


class Level(str, Enum):
    """Validation level hierarchy."""

    L1 = "L1"  # structural
    L2 = "L2"  # semantic
    L3 = "L3"  # cross-artifact collision
    L4 = "L4"  # runtime eval (opt-in)


class ValidationFinding(BaseModel):
    """A single finding from a validator."""

    rule_id: str
    severity: Severity
    message: str
    location: str | None = None
    fix_hint: str | None = None
    auto_fixable: bool = False


class ValidationReport(BaseModel):
    """Aggregated results from one or more validators."""

    findings: list[ValidationFinding] = Field(default_factory=list)

    def has_critical(self) -> bool:
        """Check if any finding is CRITICAL."""
        return any(f.severity is Severity.CRITICAL for f in self.findings)

    def has_blocking(self) -> bool:
        """Check if any finding is CRITICAL or HIGH."""
        return any(f.severity in (Severity.CRITICAL, Severity.HIGH) for f in self.findings)

    def by_severity(self, severity: Severity) -> list[ValidationFinding]:
        """Return all findings matching a severity level."""
        return [f for f in self.findings if f.severity is severity]

    def by_rule(self, rule_id: str) -> list[ValidationFinding]:
        """Return all findings with a specific rule_id."""
        return [f for f in self.findings if f.rule_id == rule_id]

    def extend(self, other: ValidationReport) -> None:
        """Merge findings from another report into this one."""
        self.findings.extend(other.findings)


class ValidationContext(BaseModel):
    """Context passed to every validator. Holds filesystem roots, installed artifact index, etc."""

    bundle_root: Path | None = None
    installed_roots: list[Path] = Field(default_factory=list)
    marketplace_index: dict[str, list[str]] = Field(default_factory=dict)
    enable_ai: bool = False


class ValidatorBase(ABC, Generic[T]):
    """Base class for all validators. Subclasses declare level, artifact_type, rule_id."""

    level: Level
    artifact_type: ArtifactType
    rule_id: str
    severity_default: Severity = Severity.MEDIUM

    @abstractmethod
    def check(self, spec: T, ctx: ValidationContext) -> list[ValidationFinding]:
        """Run validation logic. Return a list of findings (empty = pass)."""
