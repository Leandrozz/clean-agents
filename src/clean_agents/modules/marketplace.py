"""Plugin marketplace and index system for CLean-agents.

Provides browsing and discovery of community plugins. Plugins can be indexed
and installed from PyPI packages, GitHub repositories, or local YAML files.
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class PluginEntry(BaseModel):
    """A plugin entry in the marketplace index."""

    name: str
    version: str
    description: str
    author: str
    plugin_type: str = Field(..., description="Plugin type: analysis | transform | scaffold")
    tags: list[str] = Field(default_factory=list)
    pip_package: str = Field(default="", description="PyPI package name, if published")
    source_url: str = Field(default="", description="GitHub or repository URL")
    install_cmd: str = Field(default="", description="Installation command (e.g., pip install ...)")
    downloads: int = Field(default=0, description="Download count from PyPI")
    rating: float = Field(default=0.0, description="Community rating (0-5)")

    def __str__(self) -> str:
        return f"{self.name} v{self.version} ({self.plugin_type})"


class PluginIndex(BaseModel):
    """Index of available community plugins."""

    plugins: list[PluginEntry] = Field(default_factory=list)
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    @classmethod
    def load_builtin(cls) -> PluginIndex:
        """Load the built-in plugin index with example community plugins."""
        builtin_plugins = [
            PluginEntry(
                name="security-scanner",
                version="1.2.0",
                description="Deep security scanning for agent vulnerabilities and injection risks",
                author="CLean-agents Security Team",
                plugin_type="analysis",
                tags=["security", "analysis", "compliance"],
                pip_package="clean-agents-security-scanner",
                source_url="https://github.com/clean-agents/security-scanner",
                install_cmd="pip install clean-agents-security-scanner",
                downloads=5420,
                rating=4.8,
            ),
            PluginEntry(
                name="latency-optimizer",
                version="1.0.5",
                description="Optimize agent responses for low-latency scenarios",
                author="Community Contributors",
                plugin_type="transform",
                tags=["performance", "optimization"],
                pip_package="clean-agents-latency-optimizer",
                source_url="https://github.com/clean-agents/latency-optimizer",
                install_cmd="pip install clean-agents-latency-optimizer",
                downloads=3210,
                rating=4.6,
            ),
            PluginEntry(
                name="cost-reporter",
                version="2.1.0",
                description="Generate detailed cost breakdown by agent and token usage",
                author="CLean-agents Team",
                plugin_type="analysis",
                tags=["cost", "reporting", "analysis"],
                pip_package="clean-agents-cost-reporter",
                source_url="https://github.com/clean-agents/cost-reporter",
                install_cmd="pip install clean-agents-cost-reporter",
                downloads=8920,
                rating=4.9,
            ),
            PluginEntry(
                name="graphrag-validator",
                version="1.3.2",
                description="Validate GraphRAG configuration and knowledge graph setup",
                author="RAG Community",
                plugin_type="analysis",
                tags=["rag", "validation", "knowledge-graph"],
                pip_package="clean-agents-graphrag-validator",
                source_url="https://github.com/clean-agents/graphrag-validator",
                install_cmd="pip install clean-agents-graphrag-validator",
                downloads=2150,
                rating=4.5,
            ),
            PluginEntry(
                name="aws-scaffold",
                version="1.4.1",
                description="Generate AWS deployment scaffold with Lambda, API Gateway, and DynamoDB",
                author="AWS Community",
                plugin_type="scaffold",
                tags=["aws", "deployment", "infrastructure"],
                pip_package="clean-agents-aws-scaffold",
                source_url="https://github.com/clean-agents/aws-scaffold",
                install_cmd="pip install clean-agents-aws-scaffold",
                downloads=6840,
                rating=4.7,
            ),
            PluginEntry(
                name="gcp-scaffold",
                version="1.2.0",
                description="Generate Google Cloud deployment scaffold with Cloud Run and Firestore",
                author="GCP Community",
                plugin_type="scaffold",
                tags=["gcp", "google-cloud", "deployment"],
                pip_package="clean-agents-gcp-scaffold",
                source_url="https://github.com/clean-agents/gcp-scaffold",
                install_cmd="pip install clean-agents-gcp-scaffold",
                downloads=4120,
                rating=4.6,
            ),
            PluginEntry(
                name="azure-scaffold",
                version="1.1.3",
                description="Generate Azure deployment scaffold with Azure Functions and Cosmos DB",
                author="Azure Community",
                plugin_type="scaffold",
                tags=["azure", "deployment", "microsoft"],
                pip_package="clean-agents-azure-scaffold",
                source_url="https://github.com/clean-agents/azure-scaffold",
                install_cmd="pip install clean-agents-azure-scaffold",
                downloads=3450,
                rating=4.5,
            ),
            PluginEntry(
                name="compliance-auditor",
                version="2.0.1",
                description="Extended compliance audit for SOC2, HIPAA, and GDPR requirements",
                author="Compliance Team",
                plugin_type="analysis",
                tags=["compliance", "audit", "security"],
                pip_package="clean-agents-compliance-auditor",
                source_url="https://github.com/clean-agents/compliance-auditor",
                install_cmd="pip install clean-agents-compliance-auditor",
                downloads=4670,
                rating=4.8,
            ),
            PluginEntry(
                name="model-benchmark",
                version="1.5.0",
                description="Run model benchmarks to measure latency, cost, and accuracy",
                author="Benchmarking Team",
                plugin_type="analysis",
                tags=["benchmarking", "performance", "evaluation"],
                pip_package="clean-agents-model-benchmark",
                source_url="https://github.com/clean-agents/model-benchmark",
                install_cmd="pip install clean-agents-model-benchmark",
                downloads=5980,
                rating=4.7,
            ),
            PluginEntry(
                name="prompt-optimizer",
                version="1.3.1",
                description="Optimize system prompts for clarity, conciseness, and performance",
                author="NLP Community",
                plugin_type="transform",
                tags=["prompts", "optimization", "nlp"],
                pip_package="clean-agents-prompt-optimizer",
                source_url="https://github.com/clean-agents/prompt-optimizer",
                install_cmd="pip install clean-agents-prompt-optimizer",
                downloads=3850,
                rating=4.6,
            ),
        ]
        return cls(
            plugins=builtin_plugins,
            updated_at=datetime.utcnow().isoformat(),
        )

    @classmethod
    def from_url(cls, url: str) -> PluginIndex:
        """Fetch plugin index from a URL (future: community registry).

        Args:
            url: URL to remote plugin index

        Returns:
            PluginIndex loaded from the URL
        """
        import httpx

        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        return cls(**data)

    @classmethod
    def from_file(cls, path: Path | str) -> PluginIndex:
        """Load index from local YAML or JSON file.

        Args:
            path: Path to YAML or JSON index file

        Returns:
            PluginIndex loaded from file
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Index file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            if path.suffix.lower() == ".yaml" or path.suffix.lower() == ".yml":
                data = yaml.safe_load(f)
            else:
                import json
                data = json.load(f)

        return cls(**data)

    def to_yaml(self, path: Path | str) -> None:
        """Save index to YAML file.

        Args:
            path: Path where to save the YAML file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)

    def search(self, query: str) -> list[PluginEntry]:
        """Search plugins by name, description, or tags.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching plugins, sorted by relevance
        """
        query_lower = query.lower()
        results = []

        for plugin in self.plugins:
            # Name match (highest priority)
            if query_lower in plugin.name.lower():
                results.append((plugin, 3))
            # Tag match
            elif any(query_lower in tag.lower() for tag in plugin.tags):
                results.append((plugin, 2))
            # Description match
            elif query_lower in plugin.description.lower():
                results.append((plugin, 1))

        # Sort by relevance (descending), then by downloads
        results.sort(key=lambda x: (x[1], x[0].downloads), reverse=True)
        return [r[0] for r in results]

    def filter_by_type(self, plugin_type: str) -> list[PluginEntry]:
        """Filter plugins by type.

        Args:
            plugin_type: Type filter (analysis | transform | scaffold)

        Returns:
            List of plugins matching the type
        """
        return [p for p in self.plugins if p.plugin_type == plugin_type]

    def filter_by_tag(self, tag: str) -> list[PluginEntry]:
        """Filter plugins by tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of plugins with the tag
        """
        return [p for p in self.plugins if tag in p.tags]

    def filter_by_type_and_tag(self, plugin_type: str, tag: str) -> list[PluginEntry]:
        """Filter plugins by type and tag.

        Args:
            plugin_type: Type filter (analysis | transform | scaffold)
            tag: Tag to filter by

        Returns:
            List of plugins matching both criteria
        """
        return [
            p
            for p in self.plugins
            if p.plugin_type == plugin_type and tag in p.tags
        ]

    def get(self, name: str) -> PluginEntry | None:
        """Get a specific plugin by name.

        Args:
            name: Plugin name

        Returns:
            PluginEntry if found, None otherwise
        """
        return next((p for p in self.plugins if p.name.lower() == name.lower()), None)

    def sort_by_rating(self, descending: bool = True) -> list[PluginEntry]:
        """Get plugins sorted by rating.

        Args:
            descending: If True, sort highest rating first

        Returns:
            Sorted list of plugins
        """
        return sorted(self.plugins, key=lambda p: p.rating, reverse=descending)

    def sort_by_downloads(self, descending: bool = True) -> list[PluginEntry]:
        """Get plugins sorted by download count.

        Args:
            descending: If True, sort most downloaded first

        Returns:
            Sorted list of plugins
        """
        return sorted(self.plugins, key=lambda p: p.downloads, reverse=descending)

    def top_rated(self, limit: int = 5) -> list[PluginEntry]:
        """Get top-rated plugins.

        Args:
            limit: Maximum number of plugins to return

        Returns:
            List of top-rated plugins
        """
        return self.sort_by_rating(descending=True)[:limit]

    def most_popular(self, limit: int = 5) -> list[PluginEntry]:
        """Get most popular plugins by download count.

        Args:
            limit: Maximum number of plugins to return

        Returns:
            List of most popular plugins
        """
        return self.sort_by_downloads(descending=True)[:limit]


def install_plugin(entry: PluginEntry) -> bool:
    """Install a plugin from the marketplace.

    Args:
        entry: PluginEntry to install

    Returns:
        True if installation succeeded, False otherwise
    """
    if not entry.pip_package and not entry.source_url:
        return False

    install_cmd = entry.install_cmd
    if not install_cmd:
        if entry.pip_package:
            install_cmd = f"pip install {entry.pip_package}"
        elif entry.source_url:
            install_cmd = f"pip install git+{entry.source_url}"
        else:
            return False

    try:
        subprocess.run(install_cmd, shell=True, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False
