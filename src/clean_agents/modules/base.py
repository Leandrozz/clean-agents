"""Plugin system for CLean-agents — base classes and registry.

Plugins extend CLean-agents with custom modules that can:
  - Add new analysis passes (post-blueprint hooks)
  - Add new CLI commands
  - Add new scaffold targets
  - Override default behavior (model selection, cost estimation, etc.)

Plugin lifecycle:
  1. Discovery: scan entry points + plugin directories
  2. Registration: validate manifest, register hooks
  3. Execution: run on blueprint via CLI or API

Plugin types:
  - AnalysisPlugin: runs analysis on a blueprint, returns findings
  - ScaffoldPlugin: generates code for a new framework target
  - TransformPlugin: modifies a blueprint in-place (e.g., optimizer)
"""

from __future__ import annotations

import importlib
import importlib.metadata
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from clean_agents.core.blueprint import Blueprint


class PluginType(str, Enum):
    ANALYSIS = "analysis"
    SCAFFOLD = "scaffold"
    TRANSFORM = "transform"


@dataclass
class PluginManifest:
    """Metadata describing a plugin."""

    name: str
    version: str
    description: str
    author: str = ""
    plugin_type: PluginType = PluginType.ANALYSIS
    cli_command: str | None = None         # CLI subcommand name (e.g., "my-check")
    requires: list[str] = field(default_factory=list)  # pip dependencies
    config_schema: dict[str, Any] = field(default_factory=dict)  # JSON Schema for plugin config


class PluginResult:
    """Standardized result from a plugin execution."""

    def __init__(
        self,
        plugin_name: str,
        success: bool = True,
        findings: list[dict[str, Any]] | None = None,
        data: dict[str, Any] | None = None,
        modified_blueprint: Blueprint | None = None,
        files_generated: list[str] | None = None,
        summary: str = "",
    ) -> None:
        self.plugin_name = plugin_name
        self.success = success
        self.findings = findings or []
        self.data = data or {}
        self.modified_blueprint = modified_blueprint
        self.files_generated = files_generated or []
        self.summary = summary

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin": self.plugin_name,
            "success": self.success,
            "findings": self.findings,
            "data": self.data,
            "files_generated": self.files_generated,
            "summary": self.summary,
        }


# ── Base plugin classes ───────────────────────────────────────────────────────


class BasePlugin(ABC):
    """Abstract base for all CLean-agents plugins."""

    @abstractmethod
    def manifest(self) -> PluginManifest:
        """Return plugin metadata."""

    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate plugin-specific configuration. Override to add checks."""
        return True

    def on_load(self) -> None:
        """Called when the plugin is first loaded. Override for setup."""

    def on_unload(self) -> None:
        """Called when the plugin is unloaded. Override for cleanup."""


class AnalysisPlugin(BasePlugin):
    """Plugin that analyzes a blueprint and returns findings."""

    @abstractmethod
    def analyze(self, blueprint: Blueprint, config: dict[str, Any] | None = None) -> PluginResult:
        """Run analysis on the blueprint."""

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name=self.__class__.__name__,
            version="0.0.0",
            description="",
            plugin_type=PluginType.ANALYSIS,
        )


class ScaffoldPlugin(BasePlugin):
    """Plugin that generates starter code for a framework."""

    @abstractmethod
    def scaffold(
        self, blueprint: Blueprint, output_dir: Path, config: dict[str, Any] | None = None,
    ) -> PluginResult:
        """Generate scaffold files."""

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name=self.__class__.__name__,
            version="0.0.0",
            description="",
            plugin_type=PluginType.SCAFFOLD,
        )


class TransformPlugin(BasePlugin):
    """Plugin that modifies a blueprint (optimizer, migration, etc.)."""

    @abstractmethod
    def transform(self, blueprint: Blueprint, config: dict[str, Any] | None = None) -> PluginResult:
        """Transform the blueprint. Return result with modified_blueprint."""

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name=self.__class__.__name__,
            version="0.0.0",
            description="",
            plugin_type=PluginType.TRANSFORM,
        )


# ── Plugin Registry ──────────────────────────────────────────────────────────


class PluginRegistry:
    """Central registry for discovering, loading, and running plugins.

    Discovery sources (in order):
      1. Python entry points (group: "clean_agents.plugins")
      2. Plugin directory (~/.config/clean-agents/plugins/)
      3. Project-local plugins (.clean-agents/plugins/)
      4. Programmatic registration via register()
    """

    ENTRY_POINT_GROUP = "clean_agents.plugins"

    def __init__(self) -> None:
        self._plugins: dict[str, BasePlugin] = {}
        self._loaded: bool = False

    @property
    def plugins(self) -> dict[str, BasePlugin]:
        if not self._loaded:
            self.discover()
        return self._plugins

    def register(self, plugin: BasePlugin) -> None:
        """Manually register a plugin instance."""
        manifest = plugin.manifest()
        self._plugins[manifest.name] = plugin
        plugin.on_load()

    def unregister(self, name: str) -> None:
        """Unregister a plugin by name."""
        plugin = self._plugins.pop(name, None)
        if plugin:
            plugin.on_unload()

    def get(self, name: str) -> BasePlugin | None:
        """Get a plugin by name."""
        return self.plugins.get(name)

    def list_plugins(self) -> list[PluginManifest]:
        """List all registered plugin manifests."""
        return [p.manifest() for p in self.plugins.values()]

    def discover(self) -> None:
        """Discover plugins from all sources."""
        self._loaded = True
        self._discover_entry_points()
        self._discover_directory(Path.home() / ".config" / "clean-agents" / "plugins")
        self._discover_directory(Path(".clean-agents") / "plugins")

    def _discover_entry_points(self) -> None:
        """Load plugins from Python package entry points."""
        try:
            eps = importlib.metadata.entry_points()
            # Python 3.12+ returns a SelectableGroups, older returns dict
            if hasattr(eps, "select"):
                group_eps = eps.select(group=self.ENTRY_POINT_GROUP)
            elif isinstance(eps, dict):
                group_eps = eps.get(self.ENTRY_POINT_GROUP, [])
            else:
                group_eps = [ep for ep in eps if ep.group == self.ENTRY_POINT_GROUP]

            for ep in group_eps:
                try:
                    plugin_cls = ep.load()
                    if isinstance(plugin_cls, type) and issubclass(plugin_cls, BasePlugin):
                        instance = plugin_cls()
                        self.register(instance)
                except Exception:
                    pass  # Skip broken plugins
        except Exception:
            pass

    def _discover_directory(self, plugin_dir: Path) -> None:
        """Load plugins from a directory of .py files."""
        if not plugin_dir.exists():
            return

        import importlib.util

        for py_file in plugin_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(
                    f"clean_agents_plugin_{py_file.stem}", py_file,
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Find all BasePlugin subclasses in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, BasePlugin)
                            and attr not in (BasePlugin, AnalysisPlugin, ScaffoldPlugin, TransformPlugin)
                        ):
                            instance = attr()
                            self.register(instance)
            except Exception:
                pass  # Skip broken plugin files

    # ── Execution helpers ─────────────────────────────────────────────────

    def run_analysis(
        self, name: str, blueprint: Blueprint, config: dict[str, Any] | None = None,
    ) -> PluginResult:
        """Run a specific analysis plugin."""
        plugin = self.get(name)
        if not plugin:
            return PluginResult(name, success=False, summary=f"Plugin '{name}' not found")
        if not isinstance(plugin, AnalysisPlugin):
            return PluginResult(name, success=False, summary=f"Plugin '{name}' is not an analysis plugin")
        return plugin.analyze(blueprint, config)

    def run_transform(
        self, name: str, blueprint: Blueprint, config: dict[str, Any] | None = None,
    ) -> PluginResult:
        """Run a specific transform plugin."""
        plugin = self.get(name)
        if not plugin:
            return PluginResult(name, success=False, summary=f"Plugin '{name}' not found")
        if not isinstance(plugin, TransformPlugin):
            return PluginResult(name, success=False, summary=f"Plugin '{name}' is not a transform plugin")
        return plugin.transform(blueprint, config)

    def run_scaffold(
        self, name: str, blueprint: Blueprint, output_dir: Path, config: dict[str, Any] | None = None,
    ) -> PluginResult:
        """Run a specific scaffold plugin."""
        plugin = self.get(name)
        if not plugin:
            return PluginResult(name, success=False, summary=f"Plugin '{name}' not found")
        if not isinstance(plugin, ScaffoldPlugin):
            return PluginResult(name, success=False, summary=f"Plugin '{name}' is not a scaffold plugin")
        return plugin.scaffold(blueprint, output_dir, config)

    def run_all_analysis(self, blueprint: Blueprint) -> list[PluginResult]:
        """Run all registered analysis plugins."""
        results = []
        for name, plugin in self.plugins.items():
            if isinstance(plugin, AnalysisPlugin):
                results.append(plugin.analyze(blueprint))
        return results


# ── Global registry singleton ─────────────────────────────────────────────────

_registry: PluginRegistry | None = None


def get_registry() -> PluginRegistry:
    """Get the global plugin registry (lazy singleton)."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry
