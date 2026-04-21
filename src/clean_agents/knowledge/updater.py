"""Dynamic knowledge store — manage and override built-in knowledge with external updates.

Supports three layers:
1. Built-in (from base.py) — never modified
2. Global overrides (~/.config/clean-agents/knowledge/)
3. Project overrides (.clean-agents/knowledge/)

Higher layers override lower ones.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from clean_agents.knowledge.base import (
    ATTACK_VECTORS,
    COMPLIANCE_REQUIREMENTS,
    FRAMEWORK_PROFILES,
    MODEL_BENCHMARKS,
    AttackVector,
    ComplianceRequirement,
    FrameworkProfile,
    ModelBenchmark,
)


class KnowledgeUpdate(BaseModel):
    """A single knowledge update entry."""

    type: str  # "model", "framework", "compliance", "attack_vector"
    action: str  # "add", "update", "remove"
    key: str  # e.g., model name or attack vector ID
    data: dict[str, Any] = {}  # New data
    source: str = ""  # Where this info came from
    timestamp: str = ""


class KnowledgeStore:
    """Manages a persistent, updatable knowledge base.

    Layers:
    1. Built-in (from base.py) — always available, never modified
    2. Global overrides (~/.config/clean-agents/knowledge/)
    3. Project overrides (.clean-agents/knowledge/)

    Higher layers override lower ones.
    """

    def __init__(self, project_dir: Path | None = None):
        """Initialize the knowledge store.

        Args:
            project_dir: Path to project root. If None, uses current directory.
        """
        self._builtin = _load_builtin()
        self._global_dir = Path.home() / ".config" / "clean-agents" / "knowledge"
        self._project_dir = project_dir or Path.cwd()
        self._project_knowledge_dir = self._project_dir / ".clean-agents" / "knowledge"

        # Merged caches (built-in + overrides)
        self._models_cache: dict[str, ModelBenchmark] | None = None
        self._frameworks_cache: dict[str, FrameworkProfile] | None = None
        self._compliance_cache: list[ComplianceRequirement] | None = None
        self._attack_vectors_cache: list[AttackVector] | None = None

    def get_models(self) -> dict[str, ModelBenchmark]:
        """Get all models (built-in + overrides merged)."""
        if self._models_cache is not None:
            return self._models_cache

        models = dict(self._builtin["models"])  # Start with built-in
        global_overrides = self._load_overrides(self._global_dir, "models")
        project_overrides = self._load_overrides(self._project_knowledge_dir, "models")

        # Apply global overrides
        for key, data in global_overrides.items():
            if data.get("action") == "remove":
                models.pop(key, None)
            else:
                models[key] = _dict_to_model_benchmark(data)

        # Apply project overrides (highest priority)
        for key, data in project_overrides.items():
            if data.get("action") == "remove":
                models.pop(key, None)
            else:
                models[key] = _dict_to_model_benchmark(data)

        self._models_cache = models
        return models

    def get_model(self, name: str) -> ModelBenchmark | None:
        """Get a specific model by name."""
        models = self.get_models()
        return models.get(name)

    def get_frameworks(self) -> dict[str, FrameworkProfile]:
        """Get all frameworks (built-in + overrides merged)."""
        if self._frameworks_cache is not None:
            return self._frameworks_cache

        frameworks = dict(self._builtin["frameworks"])
        global_overrides = self._load_overrides(self._global_dir, "frameworks")
        project_overrides = self._load_overrides(self._project_knowledge_dir, "frameworks")

        # Apply global overrides
        for key, data in global_overrides.items():
            if data.get("action") == "remove":
                frameworks.pop(key, None)
            else:
                frameworks[key] = _dict_to_framework_profile(data)

        # Apply project overrides
        for key, data in project_overrides.items():
            if data.get("action") == "remove":
                frameworks.pop(key, None)
            else:
                frameworks[key] = _dict_to_framework_profile(data)

        self._frameworks_cache = frameworks
        return frameworks

    def get_framework(self, name: str) -> FrameworkProfile | None:
        """Get a specific framework by name."""
        frameworks = self.get_frameworks()
        return frameworks.get(name)

    def get_compliance(self) -> list[ComplianceRequirement]:
        """Get all compliance requirements (built-in + overrides merged)."""
        if self._compliance_cache is not None:
            return self._compliance_cache

        compliance = list(self._builtin["compliance"])
        global_overrides = self._load_overrides(self._global_dir, "compliance")
        project_overrides = self._load_overrides(self._project_knowledge_dir, "compliance")

        # Apply overrides (remove and add)
        to_remove = set()
        for key, data in {**global_overrides, **project_overrides}.items():
            if data.get("action") == "remove":
                to_remove.add(key)

        compliance = [c for c in compliance if c.regulation != to_remove]

        # Add new entries
        for _key, data in {**global_overrides, **project_overrides}.items():
            if data.get("action") in ("add", "update"):
                compliance.append(_dict_to_compliance_requirement(data))

        self._compliance_cache = compliance
        return compliance

    def get_attack_vectors(self) -> list[AttackVector]:
        """Get all attack vectors (built-in + overrides merged)."""
        if self._attack_vectors_cache is not None:
            return self._attack_vectors_cache

        vectors = list(self._builtin["attack_vectors"])
        global_overrides = self._load_overrides(self._global_dir, "attack_vectors")
        project_overrides = self._load_overrides(self._project_knowledge_dir, "attack_vectors")

        # Apply overrides
        to_remove = set()
        for key, data in {**global_overrides, **project_overrides}.items():
            if data.get("action") == "remove":
                to_remove.add(key)

        vectors = [v for v in vectors if v.id not in to_remove]

        # Add new entries
        for _key, data in {**global_overrides, **project_overrides}.items():
            if data.get("action") in ("add", "update"):
                vectors.append(_dict_to_attack_vector(data))

        self._attack_vectors_cache = vectors
        return vectors

    def add_model(self, model: ModelBenchmark, scope: str = "global") -> None:
        """Add or update a model in the knowledge base.

        Args:
            model: ModelBenchmark to add
            scope: "global" or "project"
        """
        data = {
            "action": "add",
            "data": {
                "name": model.name,
                "provider": model.provider,
                "gpqa": model.gpqa,
                "swe_bench": model.swe_bench,
                "bfcl": model.bfcl,
                "input_price": model.input_price,
                "output_price": model.output_price,
                "context_window": model.context_window,
                "max_output": model.max_output,
                "supports_vision": model.supports_vision,
                "supports_tools": model.supports_tools,
            },
            "timestamp": datetime.now().isoformat(),
        }

        target_dir = (
            self._project_knowledge_dir if scope == "project" else self._global_dir
        )
        self._save_override(target_dir, "models", model.name, data)
        self._models_cache = None  # Invalidate cache

    def remove_model(self, name: str, scope: str = "global") -> None:
        """Remove a model from the knowledge base.

        Args:
            name: Model name to remove
            scope: "global" or "project"
        """
        data = {"action": "remove", "timestamp": datetime.now().isoformat()}
        target_dir = (
            self._project_knowledge_dir if scope == "project" else self._global_dir
        )
        self._save_override(target_dir, "models", name, data)
        self._models_cache = None  # Invalidate cache

    def add_framework(
        self, framework: FrameworkProfile, scope: str = "global"
    ) -> None:
        """Add or update a framework in the knowledge base.

        Args:
            framework: FrameworkProfile to add
            scope: "global" or "project"
        """
        data = {
            "action": "add",
            "data": {
                "name": framework.name,
                "strengths": framework.strengths,
                "weaknesses": framework.weaknesses,
                "best_for": framework.best_for,
                "multi_agent": framework.multi_agent,
                "state_management": framework.state_management,
                "built_in_hitl": framework.built_in_hitl,
                "streaming": framework.streaming,
                "persistence": framework.persistence,
            },
            "timestamp": datetime.now().isoformat(),
        }

        target_dir = (
            self._project_knowledge_dir if scope == "project" else self._global_dir
        )
        self._save_override(target_dir, "frameworks", framework.name, data)
        self._frameworks_cache = None  # Invalidate cache

    def remove_framework(self, name: str, scope: str = "global") -> None:
        """Remove a framework from the knowledge base.

        Args:
            name: Framework name to remove
            scope: "global" or "project"
        """
        data = {"action": "remove", "timestamp": datetime.now().isoformat()}
        target_dir = (
            self._project_knowledge_dir if scope == "project" else self._global_dir
        )
        self._save_override(target_dir, "frameworks", name, data)
        self._frameworks_cache = None  # Invalidate cache

    def import_from_yaml(self, path: Path) -> int:
        """Import knowledge updates from a YAML file.

        Args:
            path: Path to YAML file

        Returns:
            Number of updates imported
        """
        try:
            import yaml  # noqa: F401
        except ImportError as e:
            msg = (
                "PyYAML required for import_from_yaml. "
                "Install with: pip install pyyaml"
            )
            raise ImportError(msg) from e

        with open(path) as f:
            data = yaml.safe_load(f)

        if not data:
            return 0

        count = 0
        for update_dict in data.get("updates", []):
            update = KnowledgeUpdate(**update_dict)

            if update.type == "model":
                model = _dict_to_model_benchmark(update.data)
                self.add_model(model, scope="global")
                count += 1
            elif update.type == "framework":
                framework = _dict_to_framework_profile(update.data)
                self.add_framework(framework, scope="global")
                count += 1

        return count

    def export_to_yaml(self, path: Path) -> None:
        """Export current knowledge (including overrides) to YAML.

        Args:
            path: Path to write YAML file
        """
        try:
            import yaml  # noqa: F401
        except ImportError as e:
            msg = (
                "PyYAML required for export_to_yaml. "
                "Install with: pip install pyyaml"
            )
            raise ImportError(msg) from e

        updates = []

        # Export models
        for name, model in self.get_models().items():
            if name not in self._builtin["models"]:
                # Only export overrides
                updates.append({
                    "type": "model",
                    "action": "add",
                    "key": name,
                    "data": {
                        "name": model.name,
                        "provider": model.provider,
                        "gpqa": model.gpqa,
                        "swe_bench": model.swe_bench,
                        "bfcl": model.bfcl,
                        "input_price": model.input_price,
                        "output_price": model.output_price,
                        "context_window": model.context_window,
                        "max_output": model.max_output,
                        "supports_vision": model.supports_vision,
                        "supports_tools": model.supports_tools,
                    },
                })

        # Export frameworks
        for name, framework in self.get_frameworks().items():
            if name not in self._builtin["frameworks"]:
                updates.append({
                    "type": "framework",
                    "action": "add",
                    "key": name,
                    "data": {
                        "name": framework.name,
                        "strengths": framework.strengths,
                        "weaknesses": framework.weaknesses,
                        "best_for": framework.best_for,
                        "multi_agent": framework.multi_agent,
                        "state_management": framework.state_management,
                        "built_in_hitl": framework.built_in_hitl,
                        "streaming": framework.streaming,
                        "persistence": framework.persistence,
                    },
                })

        output = {"updates": updates}
        with open(path, "w") as f:
            yaml.dump(output, f, default_flow_style=False)

    def _load_overrides(
        self, directory: Path, category: str
    ) -> dict[str, dict[str, Any]]:
        """Load override files from a directory.

        Args:
            directory: Directory to search for overrides
            category: Category name ("models", "frameworks", etc.)

        Returns:
            Dict of key -> override data (with nested "data" field)
        """
        if not directory.exists():
            return {}

        overrides = {}
        category_dir = directory / category
        if not category_dir.exists():
            return {}

        for json_file in category_dir.glob("*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    key = json_file.stem
                    overrides[key] = data
            except (json.JSONDecodeError, OSError):
                pass

        return overrides

    def _save_override(
        self, directory: Path, category: str, key: str, data: dict[str, Any]
    ) -> None:
        """Save an override file to disk.

        Args:
            directory: Base directory
            category: Category name
            key: Unique key for the override
            data: Data to save
        """
        category_dir = directory / category
        category_dir.mkdir(parents=True, exist_ok=True)

        file_path = category_dir / f"{key}.json"
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)


# ── Helper functions ────────────────────────────────────────────────────────


def _load_builtin() -> dict:
    """Load the built-in knowledge from base.py."""
    return {
        "models": {m.name: m for m in MODEL_BENCHMARKS.values()},
        "frameworks": {f.name: f for f in FRAMEWORK_PROFILES.values()},
        "compliance": list(COMPLIANCE_REQUIREMENTS),
        "attack_vectors": list(ATTACK_VECTORS),
    }


def _dict_to_model_benchmark(data: dict[str, Any]) -> ModelBenchmark:
    """Convert a dict to ModelBenchmark.

    Handles both direct data and nested data structure.
    """
    # Extract the actual model data (handle both nested and flat structures)
    model_data = data.get("data", data)

    return ModelBenchmark(
        name=model_data["name"],
        provider=model_data["provider"],
        gpqa=model_data["gpqa"],
        swe_bench=model_data["swe_bench"],
        bfcl=model_data["bfcl"],
        input_price=model_data["input_price"],
        output_price=model_data["output_price"],
        context_window=model_data["context_window"],
        max_output=model_data["max_output"],
        supports_vision=model_data.get("supports_vision", True),
        supports_tools=model_data.get("supports_tools", True),
    )


def _dict_to_framework_profile(data: dict[str, Any]) -> FrameworkProfile:
    """Convert a dict to FrameworkProfile.

    Handles both direct data and nested data structure.
    """
    # Extract the actual framework data (handle both nested and flat structures)
    fw_data = data.get("data", data)

    return FrameworkProfile(
        name=fw_data["name"],
        strengths=fw_data["strengths"],
        weaknesses=fw_data["weaknesses"],
        best_for=fw_data["best_for"],
        multi_agent=fw_data.get("multi_agent", True),
        state_management=fw_data.get("state_management", False),
        built_in_hitl=fw_data.get("built_in_hitl", False),
        streaming=fw_data.get("streaming", True),
        persistence=fw_data.get("persistence", False),
    )


def _dict_to_compliance_requirement(
    data: dict[str, Any],
) -> ComplianceRequirement:
    """Convert a dict to ComplianceRequirement.

    Handles both direct data and nested data structure.
    """
    # Extract the actual compliance data (handle both nested and flat structures)
    comp_data = data.get("data", data)

    return ComplianceRequirement(
        regulation=comp_data["regulation"],
        article=comp_data["article"],
        requirement=comp_data["requirement"],
        components=comp_data["components"],
        evidence_needed=comp_data["evidence_needed"],
    )


def _dict_to_attack_vector(data: dict[str, Any]) -> AttackVector:
    """Convert a dict to AttackVector.

    Handles both direct data and nested data structure.
    """
    # Extract the actual attack vector data (handle both nested and flat structures)
    vec_data = data.get("data", data)

    return AttackVector(
        id=vec_data["id"],
        name=vec_data["name"],
        description=vec_data["description"],
        detection_methods=vec_data["detection_methods"],
        mitigations=vec_data["mitigations"],
        affected_components=vec_data["affected_components"],
    )
