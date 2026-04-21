"""Opt-in anonymous telemetry for usage analytics.

Stores events locally in ~/.config/clean-agents/telemetry.jsonl
Users can view, export, or delete their data at any time.

NEVER sends data anywhere without explicit user action.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class TelemetryEvent(BaseModel):
    """A telemetry event."""

    command: str
    timestamp: str
    duration_ms: float
    success: bool
    blueprint_agents: int = 0
    blueprint_pattern: str = ""
    framework: str = ""
    error: str = ""


class TelemetryCollector:
    """Opt-in anonymous telemetry for usage analytics.

    Stores events locally in ~/.config/clean-agents/telemetry.jsonl
    Users can view, export, or delete their data at any time.

    NEVER sends data anywhere without explicit user action.
    """

    def __init__(self, enabled: bool = False) -> None:
        self._enabled = enabled
        self._path = Path.home() / ".config" / "clean-agents" / "telemetry.jsonl"

    @classmethod
    def from_config(cls) -> TelemetryCollector:
        """Load from config. Respects CLEAN_AGENTS_TELEMETRY=true env var."""
        enabled = os.environ.get("CLEAN_AGENTS_TELEMETRY", "").lower() == "true"
        return cls(enabled=enabled)

    def is_enabled(self) -> bool:
        """Check if telemetry is enabled."""
        return self._enabled

    def enable(self) -> None:
        """Enable telemetry collection."""
        self._enabled = True

    def disable(self) -> None:
        """Disable telemetry collection."""
        self._enabled = False

    def record(self, event: TelemetryEvent) -> None:
        """Append event to local JSONL file."""
        if not self._enabled:
            return

        # Ensure directory exists
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # Append event to JSONL file
        with open(self._path, "a") as f:
            f.write(event.model_dump_json() + "\n")

    def get_events(self, limit: int = 100) -> list[TelemetryEvent]:
        """Read recent events (up to limit)."""
        if not self._path.exists():
            return []

        events: list[TelemetryEvent] = []
        with open(self._path) as f:
            lines = f.readlines()
            # Get the last `limit` lines
            for line in lines[-limit:]:
                if line.strip():
                    try:
                        data = json.loads(line)
                        events.append(TelemetryEvent(**data))
                    except (json.JSONDecodeError, ValueError):
                        # Skip malformed lines
                        pass

        return events

    def summary(self) -> dict[str, Any]:
        """Aggregate stats: most used commands, avg duration, success rate."""
        events = self.get_events(limit=10000)  # Get all events for summary
        if not events:
            return {
                "total_events": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0.0,
                "commands": {},
            }

        # Calculate stats
        total = len(events)
        successful = sum(1 for e in events if e.success)
        success_rate = (successful / total * 100) if total > 0 else 0.0
        avg_duration = sum(e.duration_ms for e in events) / total if total > 0 else 0.0

        # Count commands
        commands: dict[str, int] = {}
        for event in events:
            commands[event.command] = commands.get(event.command, 0) + 1

        return {
            "total_events": total,
            "success_rate": round(success_rate, 2),
            "avg_duration_ms": round(avg_duration, 2),
            "commands": commands,
        }

    def clear(self) -> None:
        """Delete all telemetry data."""
        if self._path.exists():
            self._path.unlink()

    def export(self, path: Path) -> None:
        """Export to file for sharing/analysis."""
        if not self._path.exists():
            return

        events = self.get_events(limit=10000)
        with open(path, "w") as f:
            for event in events:
                f.write(event.model_dump_json() + "\n")


# Global singleton instance
_telemetry_instance: TelemetryCollector | None = None


def get_telemetry() -> TelemetryCollector:
    """Get global telemetry singleton."""
    global _telemetry_instance
    if _telemetry_instance is None:
        _telemetry_instance = TelemetryCollector.from_config()
    return _telemetry_instance


def reset_telemetry() -> None:
    """Reset the global telemetry instance (for testing)."""
    global _telemetry_instance
    _telemetry_instance = None
