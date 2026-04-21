"""Validator base classes and registry for the crafter pipeline."""

from __future__ import annotations

import importlib.metadata
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


class ValidatorRegistry:
    """Central registry for validators.

    Discovery sources (in order):
      1. Built-in validators registered programmatically
      2. Python entry points (group: "clean_agents.validators")
      3. User-provided validator objects via register()
    """

    ENTRY_POINT_GROUP = "clean_agents.validators"

    def __init__(self) -> None:
        self._validators: list[ValidatorBase] = []
        self._loaded: bool = False

    def register(self, validator: ValidatorBase) -> None:
        self._validators.append(validator)

    def for_artifact(
        self,
        artifact_type: ArtifactType,
        level: Level | None = None,
    ) -> list[ValidatorBase]:
        if not self._loaded:
            self.discover()
        result = [v for v in self._validators if v.artifact_type is artifact_type]
        if level is not None:
            result = [v for v in result if v.level is level]
        return result

    def discover(self) -> None:
        self._loaded = True
        try:
            eps = importlib.metadata.entry_points()
            if hasattr(eps, "select"):
                group_eps = eps.select(group=self.ENTRY_POINT_GROUP)
            elif isinstance(eps, dict):
                group_eps = eps.get(self.ENTRY_POINT_GROUP, [])
            else:
                group_eps = [ep for ep in eps if ep.group == self.ENTRY_POINT_GROUP]
            for ep in group_eps:
                try:
                    cls = ep.load()
                    if isinstance(cls, type) and issubclass(cls, ValidatorBase):
                        self._validators.append(cls())
                except Exception:
                    pass
        except Exception:
            pass


_registry: ValidatorRegistry | None = None


def get_registry() -> ValidatorRegistry:
    global _registry
    if _registry is None:
        _registry = ValidatorRegistry()
    return _registry
