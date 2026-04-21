"""Blueprint versioning — track history of changes with timestamps and diffs."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field

from clean_agents.core.blueprint import Blueprint


class BlueprintVersion(BaseModel):
    """A single version snapshot of a blueprint."""

    version_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds") + "Z"
    )
    description: str = ""
    blueprint_hash: str = ""
    changes: list[str] = Field(default_factory=list)
    author: str = "clean-agents"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return self.model_dump(mode="json", exclude_none=True)


class BlueprintHistory(BaseModel):
    """Full version history for a blueprint."""

    blueprint_name: str
    versions: list[BlueprintVersion] = Field(default_factory=list)

    def add_version(
        self, blueprint: Blueprint, description: str = "", changes: list[str] | None = None
    ) -> BlueprintVersion:
        """Snapshot the current blueprint state."""
        yaml_str = blueprint.to_yaml()
        blueprint_hash = hashlib.sha256(yaml_str.encode()).hexdigest()[:16]

        version = BlueprintVersion(
            version_id=str(uuid4())[:8],
            description=description or f"Auto-snapshot of {blueprint.name}",
            blueprint_hash=blueprint_hash,
            changes=changes or [],
            author="clean-agents",
        )
        self.versions.append(version)
        return version

    def get_version(self, version_id: str) -> BlueprintVersion | None:
        """Get a version by ID."""
        return next((v for v in self.versions if v.version_id == version_id), None)

    def latest(self) -> BlueprintVersion | None:
        """Get the most recent version."""
        return self.versions[-1] if self.versions else None

    def diff(self, v1_id: str, v2_id: str) -> dict[str, Any]:
        """Generate a diff between two versions (requires snapshot files)."""
        v1 = self.get_version(v1_id)
        v2 = self.get_version(v2_id)

        if not v1 or not v2:
            return {"error": "Version not found"}

        return {
            "v1_id": v1_id,
            "v1_timestamp": v1.timestamp,
            "v1_description": v1.description,
            "v2_id": v2_id,
            "v2_timestamp": v2.timestamp,
            "v2_description": v2.description,
            "v1_hash": v1.blueprint_hash,
            "v2_hash": v2.blueprint_hash,
            "v1_changes": v1.changes,
            "v2_changes": v2.changes,
            "hashes_match": v1.blueprint_hash == v2.blueprint_hash,
        }

    def save(self, path: Path) -> None:
        """Save history to YAML file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(mode="json", exclude_none=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    @classmethod
    def load(cls, path: Path) -> BlueprintHistory:
        """Load history from file."""
        if not path.exists():
            raise FileNotFoundError(f"History file not found: {path}")
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls.model_validate(data)


class VersionManager:
    """Manages blueprint versioning lifecycle."""

    def __init__(self, project_dir: Path):
        """Initialize version manager for a project."""
        self.project_dir = Path(project_dir)
        self._history_path = self.project_dir / "history" / "blueprint_history.yaml"
        self._snapshots_dir = self.project_dir / "history" / "snapshots"
        self._history: BlueprintHistory | None = None

    def _ensure_history_loaded(self) -> BlueprintHistory:
        """Load or initialize history."""
        if self._history is None:
            if self._history_path.exists():
                self._history = BlueprintHistory.load(self._history_path)
            else:
                self._history = BlueprintHistory(blueprint_name="default")
        return self._history

    def snapshot(
        self, blueprint: Blueprint, description: str = "", changes: list[str] | None = None
    ) -> BlueprintVersion:
        """Take a snapshot, save the full blueprint YAML, and update history."""
        history = self._ensure_history_loaded()
        history.blueprint_name = blueprint.name

        # Create version entry
        version = history.add_version(blueprint, description, changes)

        # Save snapshot file
        self._snapshots_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = self._snapshots_dir / f"{version.version_id}.yaml"
        with open(snapshot_path, "w", encoding="utf-8") as f:
            f.write(blueprint.to_yaml())

        # Save updated history
        history.save(self._history_path)
        self._history = history

        return version

    def restore(self, version_id: str) -> Blueprint | None:
        """Restore a blueprint from a specific version snapshot."""
        snapshot_path = self._snapshots_dir / f"{version_id}.yaml"
        if not snapshot_path.exists():
            return None
        return Blueprint.load(snapshot_path)

    def list_versions(self) -> list[BlueprintVersion]:
        """List all versions in history."""
        history = self._ensure_history_loaded()
        return history.versions

    def rollback(self, version_id: str) -> Blueprint | None:
        """Restore and return a blueprint from a specific version."""
        return self.restore(version_id)

    def get_history(self) -> BlueprintHistory:
        """Get the full history object."""
        return self._ensure_history_loaded()

    def get_diff(self, v1_id: str, v2_id: str) -> dict[str, Any]:
        """Get diff between two versions."""
        history = self._ensure_history_loaded()
        return history.diff(v1_id, v2_id)
