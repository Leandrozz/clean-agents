"""Shared base types for crafter artifacts (Skills, MCPs, Tools, Plugins)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ArtifactType(str, Enum):
    SKILL = "skill"
    MCP = "mcp"
    TOOL = "tool"
    PLUGIN = "plugin"


class ArtifactRef(BaseModel):
    """A reference from one artifact to another (used by AgentSpec + cross-artifact links)."""

    artifact_type: ArtifactType
    name: str
    rationale: str = ""
    spec_path: Path | None = None
    status: Literal["needed", "designed", "installed"] = "needed"
    priority: Literal["critical", "recommended", "nice-to-have"] = "recommended"


class ArtifactSpec(BaseModel):
    """Shared base for every crafter artifact. Verticals subclass to add fields."""

    name: str = Field(description="kebab-case artifact identifier")
    version: str = "0.1.0"
    description: str = Field(description="one-paragraph description; see per-vertical length rules")
    artifact_type: ArtifactType
    author: str | None = None
    language: str = Field(default="en", description="ISO 639-1 code")
    license: str = "MIT"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Traceability for future meta-agent
    source: Literal["human", "agent", "blueprint"] = "human"
    blueprint_ref: Path | None = None

    @field_validator("language")
    @classmethod
    def _validate_lang(cls, v: str) -> str:
        if len(v) != 2 or not v.isalpha():
            raise ValueError(f"language must be ISO 639-1 (2 letters), got: {v!r}")
        return v.lower()

    @field_validator("name")
    @classmethod
    def _validate_kebab(cls, v: str) -> str:
        if not v or not all(c.islower() or c.isdigit() or c == "-" for c in v):
            raise ValueError(f"name must be kebab-case (lowercase, digits, hyphens): {v!r}")
        return v
