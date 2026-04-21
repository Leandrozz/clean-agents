"""Tests for the dynamic knowledge store."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from clean_agents.knowledge.updater import KnowledgeStore
from clean_agents.knowledge.base import ModelBenchmark, FrameworkProfile


class TestKnowledgeStore:
    """Tests for KnowledgeStore."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def store(self, temp_project_dir, monkeypatch):
        """Create a KnowledgeStore instance with isolated directories."""
        # Monkeypatch Path.home to return a temp directory instead
        temp_home = Path(tempfile.gettempdir()) / f"clean_agents_test_{id(self)}"
        temp_home.mkdir(exist_ok=True)

        def mock_home():
            return temp_home

        monkeypatch.setattr(Path, "home", mock_home)
        return KnowledgeStore(project_dir=temp_project_dir)

    def test_builtin_models_loaded(self, store):
        """Test that built-in models are loaded."""
        models = store.get_models()
        assert len(models) >= 7
        assert "Claude Opus 4.6" in models
        assert "GPT-4o" in models

    def test_get_model(self, store):
        """Test retrieving a specific model."""
        model = store.get_model("Claude Opus 4.6")
        assert model is not None
        assert model.provider == "anthropic"
        assert model.gpqa > 0

    def test_get_model_missing(self, store):
        """Test retrieving a non-existent model."""
        model = store.get_model("nonexistent-model")
        assert model is None

    def test_builtin_frameworks_loaded(self, store):
        """Test that built-in frameworks are loaded."""
        frameworks = store.get_frameworks()
        assert len(frameworks) >= 4
        assert "LangGraph" in frameworks

    def test_get_framework(self, store):
        """Test retrieving a specific framework."""
        fw = store.get_framework("LangGraph")
        assert fw is not None
        assert fw.state_management is True
        assert fw.multi_agent is True

    def test_builtin_compliance_loaded(self, store):
        """Test that built-in compliance requirements are loaded."""
        compliance = store.get_compliance()
        assert len(compliance) > 0
        regulations = {c.regulation for c in compliance}
        assert "GDPR" in regulations

    def test_builtin_attack_vectors_loaded(self, store):
        """Test that built-in attack vectors are loaded."""
        vectors = store.get_attack_vectors()
        assert len(vectors) == 7
        ids = {v.id for v in vectors}
        assert "ATK-1" in ids

    def test_add_model_global(self, store):
        """Test adding a model to global scope."""
        new_model = ModelBenchmark(
            name="Test Model",
            provider="test",
            gpqa=50.0,
            swe_bench=50.0,
            bfcl=50.0,
            input_price=1.0,
            output_price=5.0,
            context_window=100_000,
            max_output=4_096,
        )

        store.add_model(new_model, scope="global")
        retrieved = store.get_model("Test Model")
        assert retrieved is not None
        assert retrieved.provider == "test"

    def test_add_model_project(self, store, temp_project_dir):
        """Test adding a model to project scope."""
        new_model = ModelBenchmark(
            name="Project Model",
            provider="test",
            gpqa=60.0,
            swe_bench=60.0,
            bfcl=60.0,
            input_price=2.0,
            output_price=10.0,
            context_window=200_000,
            max_output=8_192,
        )

        store.add_model(new_model, scope="project")
        retrieved = store.get_model("Project Model")
        assert retrieved is not None
        assert retrieved.gpqa == 60.0

    def test_override_builtin_model(self, store):
        """Test overriding a built-in model."""
        # Get original
        original = store.get_model("Claude Opus 4.6")
        original_gpqa = original.gpqa

        # Create override
        override = ModelBenchmark(
            name="Claude Opus 4.6",
            provider="anthropic",
            gpqa=99.0,  # Different value
            swe_bench=original.swe_bench,
            bfcl=original.bfcl,
            input_price=original.input_price,
            output_price=original.output_price,
            context_window=original.context_window,
            max_output=original.max_output,
        )

        store.add_model(override, scope="global")

        # Verify override
        updated = store.get_model("Claude Opus 4.6")
        assert updated.gpqa == 99.0

    def test_remove_model(self, store):
        """Test removing a model."""
        # Add a model first
        new_model = ModelBenchmark(
            name="Removable Model",
            provider="test",
            gpqa=50.0,
            swe_bench=50.0,
            bfcl=50.0,
            input_price=1.0,
            output_price=5.0,
            context_window=100_000,
            max_output=4_096,
        )
        store.add_model(new_model, scope="global")

        # Verify it exists
        assert store.get_model("Removable Model") is not None

        # Remove it
        store.remove_model("Removable Model", scope="global")

        # Verify it's gone
        assert store.get_model("Removable Model") is None

    def test_add_framework(self, store):
        """Test adding a framework."""
        new_fw = FrameworkProfile(
            name="Test Framework",
            strengths=["strength1", "strength2"],
            weaknesses=["weakness1"],
            best_for=["use_case1"],
            multi_agent=True,
            state_management=True,
        )

        store.add_framework(new_fw, scope="global")
        retrieved = store.get_framework("Test Framework")
        assert retrieved is not None
        assert retrieved.state_management is True

    def test_remove_framework(self, store):
        """Test removing a framework."""
        # Add a framework first
        new_fw = FrameworkProfile(
            name="Removable Framework",
            strengths=["s1"],
            weaknesses=["w1"],
            best_for=["use_case"],
        )
        store.add_framework(new_fw, scope="global")

        # Verify it exists
        assert store.get_framework("Removable Framework") is not None

        # Remove it
        store.remove_framework("Removable Framework", scope="global")

        # Verify it's gone
        assert store.get_framework("Removable Framework") is None

    def test_project_overrides_global(self, store):
        """Test that project overrides take precedence over global."""
        # Add to global
        global_model = ModelBenchmark(
            name="Override Test",
            provider="global",
            gpqa=50.0,
            swe_bench=50.0,
            bfcl=50.0,
            input_price=1.0,
            output_price=5.0,
            context_window=100_000,
            max_output=4_096,
        )
        store.add_model(global_model, scope="global")

        # Add to project (should override)
        project_model = ModelBenchmark(
            name="Override Test",
            provider="project",
            gpqa=75.0,
            swe_bench=75.0,
            bfcl=75.0,
            input_price=2.0,
            output_price=10.0,
            context_window=200_000,
            max_output=8_192,
        )
        store.add_model(project_model, scope="project")

        # Verify project version wins
        result = store.get_model("Override Test")
        assert result.provider == "project"
        assert result.gpqa == 75.0

    def test_get_merged_models(self, store):
        """Test that get_models returns merged built-in and overrides."""
        initial_count = len(store.get_models())

        # Add a new model
        new_model = ModelBenchmark(
            name="Merged Test",
            provider="test",
            gpqa=50.0,
            swe_bench=50.0,
            bfcl=50.0,
            input_price=1.0,
            output_price=5.0,
            context_window=100_000,
            max_output=4_096,
        )
        store.add_model(new_model, scope="global")

        # Verify count increased
        updated_count = len(store.get_models())
        assert updated_count == initial_count + 1

        # Verify new model is in the dict
        assert "Merged Test" in store.get_models()

    def test_cache_invalidation(self, store):
        """Test that caches are invalidated on updates."""
        # Get initial models
        models1 = store.get_models()
        count1 = len(models1)

        # Add a model
        new_model = ModelBenchmark(
            name="Cache Test",
            provider="test",
            gpqa=50.0,
            swe_bench=50.0,
            bfcl=50.0,
            input_price=1.0,
            output_price=5.0,
            context_window=100_000,
            max_output=4_096,
        )
        store.add_model(new_model, scope="global")

        # Get models again (should be cached, but invalidated)
        models2 = store.get_models()
        count2 = len(models2)

        # Verify cache was invalidated
        assert count2 == count1 + 1
        assert "Cache Test" in models2


class TestKnowledgeStoreYAML:
    """Tests for YAML import/export (requires pyyaml)."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def store(self, temp_project_dir, monkeypatch):
        """Create a KnowledgeStore instance with isolated directories."""
        # Monkeypatch Path.home to return a temp directory instead
        temp_home = Path(tempfile.gettempdir()) / f"clean_agents_test_yaml_{id(self)}"
        temp_home.mkdir(exist_ok=True)

        def mock_home():
            return temp_home

        monkeypatch.setattr(Path, "home", mock_home)
        return KnowledgeStore(project_dir=temp_project_dir)

    @pytest.fixture
    def yaml_file(self, temp_project_dir):
        """Create a temporary YAML file."""
        return temp_project_dir / "knowledge.yaml"

    def test_export_import_roundtrip(self, store, yaml_file):
        """Test that export/import roundtrip works."""
        pytest.importorskip("yaml")

        # Add a custom model
        new_model = ModelBenchmark(
            name="Export Test",
            provider="test",
            gpqa=55.0,
            swe_bench=55.0,
            bfcl=55.0,
            input_price=1.5,
            output_price=7.5,
            context_window=150_000,
            max_output=6_144,
        )
        store.add_model(new_model, scope="global")

        # Export
        store.export_to_yaml(yaml_file)
        assert yaml_file.exists()

        # Import into new store
        new_store = KnowledgeStore()
        count = new_store.import_from_yaml(yaml_file)
        assert count > 0

        # Verify model was imported
        imported = new_store.get_model("Export Test")
        assert imported is not None
        assert imported.provider == "test"
        assert imported.gpqa == 55.0

    def test_export_only_includes_overrides(self, store, yaml_file):
        """Test that export only includes overrides, not built-in."""
        pytest.importorskip("yaml")

        # Export without adding anything
        store.export_to_yaml(yaml_file)

        # Read the file
        import yaml

        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        # Should be empty or minimal
        updates = data.get("updates", [])
        # Only custom entries should be exported
        builtin_names = {"Claude Opus 4.6", "GPT-4o", "LangGraph"}
        for update in updates:
            key = update.get("key", update.get("data", {}).get("name"))
            assert key not in builtin_names
