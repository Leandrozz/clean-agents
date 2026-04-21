"""Knowledge base interface for crafter artifacts.

v1 ships `FlatYAMLKnowledge`. Future GraphRAG impl slots in without touching consumers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel, Field

from clean_agents.crafters.base import ArtifactRef


class BestPractice(BaseModel):
    id: str
    title: str
    body: str
    applies_to: list[str] = Field(default_factory=list)  # "skill", "mcp", "tool", "plugin"
    source: str | None = None


class AntiPattern(BaseModel):
    id: str
    title: str
    body: str
    rule_id: str | None = None                 # optional back-link to validator rule
    applies_to: list[str] = Field(default_factory=list)
    source: str | None = None


class JinjaTemplate(BaseModel):
    name: str
    path: Path


class KnowledgeBase(ABC):
    """Read-only interface consumed by DesignSession + validators + renderer."""

    @abstractmethod
    def get_best_practices(self, artifact_type: str | None = None) -> list[BestPractice]: ...

    @abstractmethod
    def get_anti_patterns(self, artifact_type: str | None = None) -> list[AntiPattern]: ...

    @abstractmethod
    def get_similar(self, description: str, k: int = 5) -> list[ArtifactRef]: ...

    @abstractmethod
    def get_template(self, name: str) -> JinjaTemplate: ...
