"""Tests for telemetry collection."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from clean_agents.telemetry import TelemetryCollector, TelemetryEvent, get_telemetry, reset_telemetry


def test_record_event():
    """Test recording a telemetry event."""
    with TemporaryDirectory() as tmpdir:
        collector = TelemetryCollector(enabled=True)
        # Override the path for testing
        collector._path = Path(tmpdir) / "telemetry.jsonl"

        event = TelemetryEvent(
            command="design",
            timestamp="2026-04-20T14:00:00Z",
            duration_ms=1500.0,
            success=True,
            blueprint_agents=3,
            blueprint_pattern="supervisor_hierarchical",
        )

        collector.record(event)

        # Check file exists
        assert collector._path.exists()

        # Check event was recorded
        events = collector.get_events()
        assert len(events) == 1
        assert events[0].command == "design"
        assert events[0].success is True


def test_summary():
    """Test aggregating telemetry summary."""
    with TemporaryDirectory() as tmpdir:
        collector = TelemetryCollector(enabled=True)
        collector._path = Path(tmpdir) / "telemetry.jsonl"

        # Record multiple events
        collector.record(
            TelemetryEvent(
                command="design",
                timestamp="2026-04-20T14:00:00Z",
                duration_ms=1000.0,
                success=True,
            )
        )
        collector.record(
            TelemetryEvent(
                command="shield",
                timestamp="2026-04-20T14:01:00Z",
                duration_ms=2000.0,
                success=True,
            )
        )
        collector.record(
            TelemetryEvent(
                command="design",
                timestamp="2026-04-20T14:02:00Z",
                duration_ms=1500.0,
                success=False,
                error="User interrupted",
            )
        )

        summary = collector.summary()

        assert summary["total_events"] == 3
        assert summary["success_rate"] == 66.67  # 2/3 = 66.67%
        assert summary["avg_duration_ms"] == 1500.0  # (1000 + 2000 + 1500) / 3
        assert summary["commands"]["design"] == 2
        assert summary["commands"]["shield"] == 1


def test_clear():
    """Test clearing telemetry data."""
    with TemporaryDirectory() as tmpdir:
        collector = TelemetryCollector(enabled=True)
        collector._path = Path(tmpdir) / "telemetry.jsonl"

        # Record an event
        collector.record(
            TelemetryEvent(
                command="design",
                timestamp="2026-04-20T14:00:00Z",
                duration_ms=1000.0,
                success=True,
            )
        )

        assert collector._path.exists()
        assert len(collector.get_events()) == 1

        # Clear
        collector.clear()

        assert not collector._path.exists()
        assert len(collector.get_events()) == 0


def test_disabled_does_not_record():
    """Test that disabled telemetry does not record events."""
    with TemporaryDirectory() as tmpdir:
        collector = TelemetryCollector(enabled=False)
        collector._path = Path(tmpdir) / "telemetry.jsonl"

        # Try to record an event
        collector.record(
            TelemetryEvent(
                command="design",
                timestamp="2026-04-20T14:00:00Z",
                duration_ms=1000.0,
                success=True,
            )
        )

        # File should not be created
        assert not collector._path.exists()


def test_export():
    """Test exporting telemetry data."""
    with TemporaryDirectory() as tmpdir:
        collector = TelemetryCollector(enabled=True)
        collector._path = Path(tmpdir) / "telemetry.jsonl"

        # Record events
        collector.record(
            TelemetryEvent(
                command="design",
                timestamp="2026-04-20T14:00:00Z",
                duration_ms=1000.0,
                success=True,
            )
        )
        collector.record(
            TelemetryEvent(
                command="shield",
                timestamp="2026-04-20T14:01:00Z",
                duration_ms=2000.0,
                success=False,
                error="Invalid blueprint",
            )
        )

        # Export
        export_path = Path(tmpdir) / "exported.jsonl"
        collector.export(export_path)

        # Check exported file
        assert export_path.exists()
        exported_events = []
        with open(export_path) as f:
            for line in f:
                if line.strip():
                    import json
                    exported_events.append(json.loads(line))

        assert len(exported_events) == 2
        assert exported_events[0]["command"] == "design"
        assert exported_events[1]["error"] == "Invalid blueprint"


def test_enable_disable():
    """Test enabling and disabling telemetry."""
    collector = TelemetryCollector(enabled=False)
    assert not collector.is_enabled()

    collector.enable()
    assert collector.is_enabled()

    collector.disable()
    assert not collector.is_enabled()


def test_from_config_default():
    """Test loading from config without env var."""
    # Make sure env var is not set
    os.environ.pop("CLEAN_AGENTS_TELEMETRY", None)

    collector = TelemetryCollector.from_config()
    assert not collector.is_enabled()


def test_from_config_with_env():
    """Test loading from config with env var."""
    os.environ["CLEAN_AGENTS_TELEMETRY"] = "true"
    try:
        collector = TelemetryCollector.from_config()
        assert collector.is_enabled()
    finally:
        os.environ.pop("CLEAN_AGENTS_TELEMETRY", None)


def test_empty_summary():
    """Test summary when no events exist."""
    with TemporaryDirectory() as tmpdir:
        collector = TelemetryCollector(enabled=True)
        collector._path = Path(tmpdir) / "telemetry.jsonl"

        summary = collector.summary()

        assert summary["total_events"] == 0
        assert summary["success_rate"] == 0.0
        assert summary["avg_duration_ms"] == 0.0
        assert summary["commands"] == {}


def test_get_telemetry_singleton():
    """Test the global singleton instance."""
    reset_telemetry()

    t1 = get_telemetry()
    t2 = get_telemetry()

    assert t1 is t2

    reset_telemetry()
