"""Tests for blueprint versioning system."""

from pathlib import Path
from tempfile import TemporaryDirectory
import time

from clean_agents.core.agent import AgentSpec, ModelConfig, Memory, AutonomyLevel
from clean_agents.core.blueprint import Blueprint, SystemType, ArchitecturePattern, ComplianceConfig
from clean_agents.core.versioning import BlueprintVersion, BlueprintHistory, VersionManager


def _make_test_blueprint(name: str = "test-system", agents: int = 2) -> Blueprint:
    """Create a test blueprint."""
    return Blueprint(
        name=name,
        description=f"Test system with {agents} agents",
        system_type=SystemType.MULTI_AGENT,
        pattern=ArchitecturePattern.SUPERVISOR_HIERARCHICAL,
        agents=[
            AgentSpec(
                name=f"agent-{i}",
                role=f"Agent {i}",
                agent_type="specialist",
                model=ModelConfig(primary="claude-sonnet-4-6"),
            )
            for i in range(agents)
        ],
        compliance=ComplianceConfig(regulations=["gdpr"], audit_trail=True),
    )


# ── BlueprintVersion ──────────────────────────────────────────────────────────


def test_blueprint_version_defaults():
    """Test BlueprintVersion creation with defaults."""
    version = BlueprintVersion()
    assert version.version_id  # Should have auto-generated ID
    assert version.timestamp  # Should have auto-generated timestamp
    assert version.author == "clean-agents"
    assert version.description == ""
    assert version.changes == []


def test_blueprint_version_custom():
    """Test BlueprintVersion with custom values."""
    version = BlueprintVersion(
        version_id="v1",
        description="Initial blueprint",
        blueprint_hash="abc123",
        changes=["Added agent X", "Removed agent Y"],
    )
    assert version.version_id == "v1"
    assert version.description == "Initial blueprint"
    assert version.blueprint_hash == "abc123"
    assert len(version.changes) == 2


# ── BlueprintHistory ─────────────────────────────────────────────────────────


def test_blueprint_history_empty():
    """Test BlueprintHistory starts empty."""
    history = BlueprintHistory(blueprint_name="test")
    assert history.blueprint_name == "test"
    assert len(history.versions) == 0
    assert history.latest() is None


def test_blueprint_history_add_version():
    """Test adding a version to history."""
    history = BlueprintHistory(blueprint_name="test-system")
    bp = _make_test_blueprint()

    version = history.add_version(bp, "Initial version")

    assert len(history.versions) == 1
    assert history.versions[0].description == "Initial version"
    assert history.latest() == version
    assert version.blueprint_hash  # Should have computed hash


def test_blueprint_history_multiple_snapshots():
    """Test multiple snapshots with different blueprints."""
    history = BlueprintHistory(blueprint_name="evolving-system")

    # First version
    bp1 = _make_test_blueprint(agents=2)
    v1 = history.add_version(bp1, "Version 1: 2 agents")

    # Second version
    bp2 = _make_test_blueprint(agents=3)
    v2 = history.add_version(bp2, "Version 2: 3 agents")

    assert len(history.versions) == 2
    assert history.latest().version_id == v2.version_id
    assert v1.blueprint_hash != v2.blueprint_hash


def test_blueprint_history_get_version():
    """Test retrieving a specific version."""
    history = BlueprintHistory(blueprint_name="test")
    bp = _make_test_blueprint()
    v1 = history.add_version(bp, "Version 1")
    v2 = history.add_version(bp, "Version 2")

    retrieved = history.get_version(v1.version_id)
    assert retrieved is not None
    assert retrieved.version_id == v1.version_id
    assert retrieved.description == "Version 1"

    not_found = history.get_version("nonexistent")
    assert not_found is None


def test_blueprint_history_diff():
    """Test diff between two versions."""
    history = BlueprintHistory(blueprint_name="test")
    bp = _make_test_blueprint()

    v1 = history.add_version(bp, "Version 1")
    v2 = history.add_version(bp, "Version 2")

    diff = history.diff(v1.version_id, v2.version_id)

    assert diff["v1_id"] == v1.version_id
    assert diff["v2_id"] == v2.version_id
    assert "v1_timestamp" in diff
    assert "v2_timestamp" in diff


def test_blueprint_history_diff_nonexistent():
    """Test diff with nonexistent versions."""
    history = BlueprintHistory(blueprint_name="test")
    diff = history.diff("fake1", "fake2")
    assert "error" in diff


# ── VersionManager ────────────────────────────────────────────────────────────


def test_version_manager_snapshot():
    """Test taking a snapshot with VersionManager."""
    with TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        vm = VersionManager(project_dir)
        bp = _make_test_blueprint()

        version = vm.snapshot(bp, "First snapshot")

        assert version.version_id
        assert version.description == "First snapshot"

        # Check files were created
        assert vm._history_path.exists()
        snapshot_file = vm._snapshots_dir / f"{version.version_id}.yaml"
        assert snapshot_file.exists()


def test_version_manager_list_versions():
    """Test listing versions."""
    with TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        vm = VersionManager(project_dir)

        bp = _make_test_blueprint()
        v1 = vm.snapshot(bp, "Version 1")
        v2 = vm.snapshot(bp, "Version 2")

        versions = vm.list_versions()

        assert len(versions) == 2
        assert versions[0].version_id == v1.version_id
        assert versions[1].version_id == v2.version_id


def test_version_manager_restore():
    """Test restoring a blueprint from a version."""
    with TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        vm = VersionManager(project_dir)

        original = _make_test_blueprint(agents=3)
        version = vm.snapshot(original, "Original with 3 agents")

        restored = vm.restore(version.version_id)

        assert restored is not None
        assert restored.name == original.name
        assert restored.total_agents() == 3


def test_version_manager_restore_nonexistent():
    """Test restoring a nonexistent version."""
    with TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        vm = VersionManager(project_dir)

        restored = vm.restore("nonexistent-version-id")
        assert restored is None


def test_version_manager_rollback():
    """Test rollback functionality."""
    with TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        vm = VersionManager(project_dir)

        bp1 = _make_test_blueprint(agents=1)
        v1 = vm.snapshot(bp1, "Version 1")

        bp2 = _make_test_blueprint(agents=2)
        v2 = vm.snapshot(bp2, "Version 2")

        # Rollback to v1
        rolled_back = vm.rollback(v1.version_id)

        assert rolled_back is not None
        assert rolled_back.total_agents() == 1


def test_version_manager_history_save_load():
    """Test saving and loading history."""
    with TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # Create and save versions
        vm1 = VersionManager(project_dir)
        bp = _make_test_blueprint()
        v1 = vm1.snapshot(bp, "Version 1")
        v2 = vm1.snapshot(bp, "Version 2")

        # Load in new manager instance
        vm2 = VersionManager(project_dir)
        versions = vm2.list_versions()

        assert len(versions) == 2
        assert versions[0].version_id == v1.version_id
        assert versions[1].version_id == v2.version_id


def test_version_manager_get_history():
    """Test getting the full history object."""
    with TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        vm = VersionManager(project_dir)

        bp = _make_test_blueprint()
        vm.snapshot(bp, "Snapshot 1")
        vm.snapshot(bp, "Snapshot 2")

        history = vm.get_history()

        assert history.blueprint_name == "test-system"
        assert len(history.versions) == 2


def test_version_manager_get_diff():
    """Test getting diff through manager."""
    with TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        vm = VersionManager(project_dir)

        bp = _make_test_blueprint()
        v1 = vm.snapshot(bp, "Version 1")
        v2 = vm.snapshot(bp, "Version 2")

        diff = vm.get_diff(v1.version_id, v2.version_id)

        assert diff["v1_id"] == v1.version_id
        assert diff["v2_id"] == v2.version_id


# ── Auto-snapshot on Blueprint.save() ──────────────────────────────────────────


def test_auto_snapshot_on_save():
    """Test that Blueprint.save() auto-snapshots when in a project."""
    with TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / ".clean-agents"
        project_dir.mkdir()

        # Create config.yaml to mark it as a project
        (project_dir / "config.yaml").write_text("project_name: test\n")

        bp = _make_test_blueprint()
        blueprint_path = project_dir / "blueprint.yaml"

        # Save blueprint (should auto-snapshot)
        bp.save(blueprint_path, "Auto-saved blueprint")

        # Check that history was created
        vm = VersionManager(project_dir)
        versions = vm.list_versions()

        assert len(versions) > 0
        assert versions[0].description == "Auto-saved blueprint"


def test_save_without_project_no_error():
    """Test that save doesn't fail even without a project."""
    with TemporaryDirectory() as tmpdir:
        # Not a project directory (no config.yaml)
        bp = _make_test_blueprint()
        blueprint_path = Path(tmpdir) / "blueprint.yaml"

        # Should not raise an error
        bp.save(blueprint_path)
        assert blueprint_path.exists()


# ── Integration tests ─────────────────────────────────────────────────────────


def test_version_workflow():
    """Test a complete versioning workflow."""
    with TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        vm = VersionManager(project_dir)

        # Create initial blueprint
        bp1 = Blueprint(
            name="workflow-test",
            system_type=SystemType.SINGLE_AGENT,
            agents=[
                AgentSpec(name="agent-1", role="Worker", model=ModelConfig(primary="claude-haiku-4-5"))
            ],
        )

        v1 = vm.snapshot(bp1, "Initial: Single agent system")
        assert v1.version_id

        # Evolve blueprint
        bp2 = Blueprint(
            name="workflow-test",
            system_type=SystemType.MULTI_AGENT,
            agents=[
                AgentSpec(name="orchestrator", role="Coordinator", agent_type="orchestrator"),
                AgentSpec(name="worker-1", role="Process tasks"),
                AgentSpec(name="worker-2", role="Validate results"),
            ],
        )

        v2 = vm.snapshot(
            bp2,
            "Evolution: Multi-agent with orchestrator",
            changes=[
                "Added orchestrator agent",
                "Split worker into 2 specialized agents",
                "Changed system type to multi-agent",
            ],
        )

        # Verify history
        versions = vm.list_versions()
        assert len(versions) == 2
        assert versions[0].description == "Initial: Single agent system"
        assert versions[1].description == "Evolution: Multi-agent with orchestrator"

        # Restore v1
        restored = vm.restore(v1.version_id)
        assert restored.total_agents() == 1

        # Check diff
        diff = vm.get_diff(v1.version_id, v2.version_id)
        assert not diff["hashes_match"]


def test_concurrent_snapshots():
    """Test multiple rapid snapshots."""
    with TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        vm = VersionManager(project_dir)

        bp = _make_test_blueprint()

        for i in range(5):
            vm.snapshot(bp, f"Snapshot {i + 1}")
            # Small delay to ensure different timestamps
            time.sleep(0.01)

        versions = vm.list_versions()
        assert len(versions) == 5

        # Verify timestamps are unique or increasing
        timestamps = [v.timestamp for v in versions]
        assert len(timestamps) == len(set(timestamps)) or all(
            timestamps[i] <= timestamps[i + 1] for i in range(len(timestamps) - 1)
        )
