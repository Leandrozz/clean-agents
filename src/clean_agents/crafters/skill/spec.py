"""Skill-vertical artifact spec (v1 of crafters)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from clean_agents.crafters.base import ArtifactSpec, ArtifactType


class SkillSection(BaseModel):
    heading: str
    body: str = ""
    anchor: str | None = None                  # slug for cross-reference


class ReferenceFile(BaseModel):
    path: Path                                 # relative to bundle root
    topic: str
    outline: list[str] = Field(default_factory=list)
    mentioned_in: list[str] = Field(default_factory=list)   # anchors in SKILL.md


class EvalCase(BaseModel):
    prompt: str
    expected: Literal["activate", "ignore"]
    note: str = ""


class EvalThresholds(BaseModel):
    tpr_min: float = 0.8
    fpr_max: float = 0.2


class EvalsManifest(BaseModel):
    positive_cases: list[EvalCase] = Field(default_factory=list)
    negative_cases: list[EvalCase] = Field(default_factory=list)
    thresholds: EvalThresholds = Field(default_factory=EvalThresholds)


class SkillSpec(ArtifactSpec):
    """Skill (Claude Code / Anthropic Skills) artifact spec."""

    artifact_type: Literal[ArtifactType.SKILL] = ArtifactType.SKILL
    triggers: list[str] = Field(default_factory=list)
    references: list[ReferenceFile] = Field(default_factory=list)
    evals: EvalsManifest | None = None
    body_outline: list[SkillSection] = Field(default_factory=list)
    bundle_format: Literal["dir", "zip"] = "dir"
