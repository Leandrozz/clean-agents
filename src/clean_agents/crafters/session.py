"""DesignSession[T] — reusable engine for every crafter vertical."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

import yaml
from pydantic import BaseModel, Field

from clean_agents.crafters.base import ArtifactSpec
from clean_agents.crafters.validators.base import ValidationReport

T = TypeVar("T", bound=ArtifactSpec)


class Phase(str, Enum):
    INTAKE = "intake"
    RECOMMEND = "recommend"
    DEEP_DIVE = "deep_dive"
    BUNDLE = "bundle"
    ITERATE = "iterate"
    MODULES = "modules"


class DesignConfig(BaseModel):
    enable_ai: bool = False
    language: str = "en"
    interactive: bool = True
    knowledge_root: Path | None = None


class Turn(BaseModel):
    phase: Phase
    role: str                              # "user" | "assistant" | "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Recommendation(BaseModel):
    summary: str
    proposed_spec: dict[str, Any]
    evidence: list[str] = Field(default_factory=list)


class Delta(BaseModel):
    field_path: str
    old_value: Any = None
    new_value: Any = None
    cascaded_fields: list[str] = Field(default_factory=list)


class CascadeReport(BaseModel):
    deltas: list[Delta] = Field(default_factory=list)
    invalidated_validators: list[str] = Field(default_factory=list)


class ModuleResult(BaseModel):
    name: str
    ok: bool
    data: dict[str, Any] = Field(default_factory=dict)
    message: str = ""


class Bundle(BaseModel):
    output_dir: Path
    files: list[Path] = Field(default_factory=list)
    validation: ValidationReport | None = None


class DesignSession(BaseModel, Generic[T]):
    """Generic 5-phase engine. Typed on the artifact spec subclass."""

    session_id: UUID = Field(default_factory=uuid4)
    phase: Phase = Phase.INTAKE
    spec: T
    history: list[Turn] = Field(default_factory=list)
    validation_state: ValidationReport | None = None
    config: DesignConfig = Field(default_factory=DesignConfig)

    model_config = {"arbitrary_types_allowed": True}

    def intake(self, input: str | T) -> Recommendation:  # noqa: A002
        raise NotImplementedError("Implemented in M5")

    def answer(self, question_id: str, answer: Any) -> Delta:
        raise NotImplementedError("Implemented in M5")

    def render(self, output_dir: Path) -> Bundle:
        raise NotImplementedError("Implemented in M5")

    def iterate(self, edits: dict[str, Any]) -> CascadeReport:
        raise NotImplementedError("Implemented in M5")

    def module(self, name: str, **kwargs: Any) -> ModuleResult:
        raise NotImplementedError("Implemented in M5")

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(mode="json")
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    @classmethod
    def load(cls, path: Path) -> DesignSession[T]:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)
