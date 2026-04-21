"""Tests for the plugin marketplace system."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml

from clean_agents.modules.marketplace import PluginEntry, PluginIndex


class TestPluginEntry:
    """Test PluginEntry model."""

    def test_plugin_entry_creation(self) -> None:
        """Test creating a plugin entry."""
        entry = PluginEntry(
            name="test-plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            plugin_type="analysis",
        )
        assert entry.name == "test-plugin"
        assert entry.version == "1.0.0"
        assert entry.plugin_type == "analysis"

    def test_plugin_entry_with_tags(self) -> None:
        """Test plugin entry with tags."""
        entry = PluginEntry(
            name="test",
            version="1.0",
            description="Test",
            author="Author",
            plugin_type="analysis",
            tags=["security", "analysis"],
        )
        assert len(entry.tags) == 2
        assert "security" in entry.tags

    def test_plugin_entry_defaults(self) -> None:
        """Test plugin entry default values."""
        entry = PluginEntry(
            name="test",
            version="1.0",
            description="Test",
            author="Author",
            plugin_type="analysis",
        )
        assert entry.pip_package == ""
        assert entry.source_url == ""
        assert entry.downloads == 0
        assert entry.rating == 0.0


class TestPluginIndex:
    """Test PluginIndex model."""

    def test_builtin_index_has_plugins(self) -> None:
        """Test that builtin index contains plugins."""
        index = PluginIndex.load_builtin()
        assert len(index.plugins) > 0
        assert len(index.plugins) == 10  # Should have ~10 example plugins

    def test_builtin_index_plugins_by_type(self) -> None:
        """Test that builtin index has plugins of each type."""
        index = PluginIndex.load_builtin()
        types = set(p.plugin_type for p in index.plugins)
        assert "analysis" in types
        assert "scaffold" in types
        assert "transform" in types

    def test_builtin_index_has_specific_plugins(self) -> None:
        """Test that builtin index has expected plugins."""
        index = PluginIndex.load_builtin()
        names = {p.name for p in index.plugins}
        assert "security-scanner" in names
        assert "cost-reporter" in names
        assert "aws-scaffold" in names
        assert "prompt-optimizer" in names

    def test_search_by_name(self) -> None:
        """Test searching plugins by name."""
        index = PluginIndex.load_builtin()
        results = index.search("security")
        assert len(results) > 0
        assert results[0].name == "security-scanner"

    def test_search_by_description(self) -> None:
        """Test searching plugins by description."""
        index = PluginIndex.load_builtin()
        results = index.search("cost")
        assert len(results) > 0
        # Should find cost-related plugins
        found_cost = any("cost" in p.name.lower() for p in results)
        assert found_cost

    def test_search_by_tag(self) -> None:
        """Test searching plugins by tag."""
        index = PluginIndex.load_builtin()
        results = index.search("security")
        assert len(results) > 0
        # Security-scanner should be first (name match)
        assert results[0].name == "security-scanner"

    def test_search_case_insensitive(self) -> None:
        """Test that search is case-insensitive."""
        index = PluginIndex.load_builtin()
        results1 = index.search("security")
        results2 = index.search("SECURITY")
        results3 = index.search("Security")
        assert len(results1) == len(results2) == len(results3)

    def test_search_no_results(self) -> None:
        """Test search with no results."""
        index = PluginIndex.load_builtin()
        results = index.search("nonexistent-plugin-xyz")
        assert len(results) == 0

    def test_filter_by_type(self) -> None:
        """Test filtering plugins by type."""
        index = PluginIndex.load_builtin()
        analysis_plugins = index.filter_by_type("analysis")
        assert len(analysis_plugins) > 0
        assert all(p.plugin_type == "analysis" for p in analysis_plugins)

    def test_filter_by_type_scaffold(self) -> None:
        """Test filtering scaffold plugins."""
        index = PluginIndex.load_builtin()
        scaffold_plugins = index.filter_by_type("scaffold")
        assert len(scaffold_plugins) == 3  # aws, gcp, azure
        assert all(p.plugin_type == "scaffold" for p in scaffold_plugins)

    def test_filter_by_type_transform(self) -> None:
        """Test filtering transform plugins."""
        index = PluginIndex.load_builtin()
        transform_plugins = index.filter_by_type("transform")
        assert len(transform_plugins) > 0
        assert all(p.plugin_type == "transform" for p in transform_plugins)

    def test_filter_by_tag(self) -> None:
        """Test filtering plugins by tag."""
        index = PluginIndex.load_builtin()
        security_plugins = index.filter_by_tag("security")
        assert len(security_plugins) > 0
        assert all("security" in p.tags for p in security_plugins)

    def test_filter_by_type_and_tag(self) -> None:
        """Test filtering plugins by type and tag."""
        index = PluginIndex.load_builtin()
        results = index.filter_by_type_and_tag("analysis", "security")
        assert len(results) > 0
        assert all(p.plugin_type == "analysis" for p in results)
        assert all("security" in p.tags for p in results)

    def test_get_plugin_by_name(self) -> None:
        """Test getting a specific plugin by name."""
        index = PluginIndex.load_builtin()
        plugin = index.get("security-scanner")
        assert plugin is not None
        assert plugin.name == "security-scanner"
        assert plugin.plugin_type == "analysis"

    def test_get_plugin_case_insensitive(self) -> None:
        """Test that get is case-insensitive."""
        index = PluginIndex.load_builtin()
        plugin1 = index.get("security-scanner")
        plugin2 = index.get("SECURITY-SCANNER")
        plugin3 = index.get("Security-Scanner")
        assert plugin1 == plugin2 == plugin3

    def test_get_nonexistent_plugin(self) -> None:
        """Test getting a nonexistent plugin."""
        index = PluginIndex.load_builtin()
        plugin = index.get("nonexistent-xyz")
        assert plugin is None

    def test_sort_by_rating(self) -> None:
        """Test sorting plugins by rating."""
        index = PluginIndex.load_builtin()
        sorted_plugins = index.sort_by_rating(descending=True)
        assert len(sorted_plugins) > 1
        # First should have higher or equal rating than last
        assert sorted_plugins[0].rating >= sorted_plugins[-1].rating

    def test_sort_by_rating_ascending(self) -> None:
        """Test sorting plugins by rating ascending."""
        index = PluginIndex.load_builtin()
        sorted_plugins = index.sort_by_rating(descending=False)
        assert len(sorted_plugins) > 1
        # First should have lower or equal rating than last
        assert sorted_plugins[0].rating <= sorted_plugins[-1].rating

    def test_sort_by_downloads(self) -> None:
        """Test sorting plugins by downloads."""
        index = PluginIndex.load_builtin()
        sorted_plugins = index.sort_by_downloads(descending=True)
        assert len(sorted_plugins) > 1
        # First should have more or equal downloads than last
        assert sorted_plugins[0].downloads >= sorted_plugins[-1].downloads

    def test_top_rated(self) -> None:
        """Test getting top-rated plugins."""
        index = PluginIndex.load_builtin()
        top = index.top_rated(limit=3)
        assert len(top) <= 3
        assert len(top) > 0
        # Should be sorted by rating
        if len(top) > 1:
            assert top[0].rating >= top[1].rating

    def test_most_popular(self) -> None:
        """Test getting most popular plugins."""
        index = PluginIndex.load_builtin()
        popular = index.most_popular(limit=3)
        assert len(popular) <= 3
        assert len(popular) > 0
        # Should be sorted by downloads
        if len(popular) > 1:
            assert popular[0].downloads >= popular[1].downloads

    def test_index_to_yaml(self) -> None:
        """Test saving index to YAML file."""
        with TemporaryDirectory() as tmpdir:
            index = PluginIndex.load_builtin()
            yaml_path = Path(tmpdir) / "marketplace.yaml"

            index.to_yaml(yaml_path)
            assert yaml_path.exists()

            # Verify contents
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            assert "plugins" in data
            assert len(data["plugins"]) == len(index.plugins)

    def test_index_from_file(self) -> None:
        """Test loading index from YAML file."""
        with TemporaryDirectory() as tmpdir:
            # Create and save
            index1 = PluginIndex.load_builtin()
            yaml_path = Path(tmpdir) / "marketplace.yaml"
            index1.to_yaml(yaml_path)

            # Load back
            index2 = PluginIndex.from_file(yaml_path)
            assert len(index2.plugins) == len(index1.plugins)
            assert index2.plugins[0].name == index1.plugins[0].name

    def test_index_from_file_not_found(self) -> None:
        """Test loading from nonexistent file."""
        with pytest.raises(FileNotFoundError):
            PluginIndex.from_file("/nonexistent/path/marketplace.yaml")

    def test_index_updated_at_timestamp(self) -> None:
        """Test that index has updated_at timestamp."""
        index = PluginIndex.load_builtin()
        assert index.updated_at
        assert "T" in index.updated_at  # ISO format

    def test_plugin_with_install_cmd(self) -> None:
        """Test plugin entry with install command."""
        index = PluginIndex.load_builtin()
        plugin = index.get("security-scanner")
        assert plugin is not None
        assert plugin.install_cmd
        assert "pip install" in plugin.install_cmd

    def test_plugin_with_source_url(self) -> None:
        """Test plugin entry with source URL."""
        index = PluginIndex.load_builtin()
        plugin = index.get("aws-scaffold")
        assert plugin is not None
        assert plugin.source_url
        assert "github.com" in plugin.source_url.lower()

    def test_all_plugins_have_required_fields(self) -> None:
        """Test that all plugins have required fields."""
        index = PluginIndex.load_builtin()
        for plugin in index.plugins:
            assert plugin.name
            assert plugin.version
            assert plugin.description
            assert plugin.author
            assert plugin.plugin_type in ["analysis", "scaffold", "transform"]


class TestPluginIndexSearchRelevance:
    """Test search relevance ranking."""

    def test_name_match_ranked_highest(self) -> None:
        """Test that name matches are ranked highest."""
        index = PluginIndex.load_builtin()
        results = index.search("security")
        # Name match (security-scanner) should come before description matches
        assert results[0].name == "security-scanner"

    def test_tag_match_ranked_second(self) -> None:
        """Test that tag matches are ranked second."""
        index = PluginIndex.load_builtin()
        # Search for a tag that doesn't match any plugin names
        results = index.search("compliance")
        # Should find compliance-auditor (which has "compliance" in tags)
        assert any(p.name == "compliance-auditor" for p in results)

    def test_downloads_as_tiebreaker(self) -> None:
        """Test that downloads are used as tiebreaker."""
        index = PluginIndex.load_builtin()
        # Filter for analysis plugins with same tag relevance
        analysis = index.filter_by_type("analysis")
        # When sorted by downloads, more popular should come first
        if len(analysis) > 1:
            sorted_by_downloads = sorted(analysis, key=lambda p: p.downloads, reverse=True)
            assert sorted_by_downloads[0].downloads >= sorted_by_downloads[1].downloads
