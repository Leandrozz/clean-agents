"""L4 runtime eval harness — simulated skill activation against generated prompts."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path


def compute_tpr_fpr(
    results: list[tuple[str, str, bool]],  # (prompt, expected, activated)
) -> tuple[float, float]:
    pos = [r for r in results if r[1] == "activate"]
    neg = [r for r in results if r[1] == "ignore"]
    tpr = (sum(1 for _, _, a in pos if a) / len(pos)) if pos else 0.0
    fpr = (sum(1 for _, _, a in neg if a) / len(neg)) if neg else 0.0
    return tpr, fpr


def write_results(output: Path, results: list[dict]) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"results-{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.json"
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return path


ActivationFn = Callable[[str], bool]
