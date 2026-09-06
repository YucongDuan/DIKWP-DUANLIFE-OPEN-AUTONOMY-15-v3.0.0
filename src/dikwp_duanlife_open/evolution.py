from __future__ import annotations

from pathlib import Path
from typing import Any

from .constitution import Constitution
from .util import bounded, read_json, utc_now, write_json


DEFAULT_HEURISTICS = {
    "exploration_weight": 0.30,
    "dissent_weight": 0.25,
    "evidence_weight": 0.30,
    "reversibility_weight": 0.15,
    "world_model_count": 4,
    "self_reflection_interval": 1,
}


class EvolutionManager:
    """Allows bounded self-revision of heuristics, never identity or authority invariants."""

    BOUNDS = {
        "exploration_weight": (0.05, 0.60),
        "dissent_weight": (0.10, 0.60),
        "evidence_weight": (0.20, 0.70),
        "reversibility_weight": (0.10, 0.60),
        "world_model_count": (2, 8),
        "self_reflection_interval": (1, 8),
    }

    def __init__(self, workspace: str | Path):
        self.path = Path(workspace) / "state" / "evolution.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            write_json(self.path, {"heuristics": DEFAULT_HEURISTICS, "history": [], "protected_change_proposals": []})

    def status(self) -> dict[str, Any]:
        return read_json(self.path)

    def revise(self, patch: dict[str, Any], reason: str) -> dict[str, Any]:
        state = self.status()
        applied: dict[str, Any] = {}
        rejected: dict[str, Any] = {}
        for key, value in patch.items():
            if key not in self.BOUNDS:
                rejected[key] = "Protected or unsupported heuristic"
                continue
            lo, hi = self.BOUNDS[key]
            numeric = float(value)
            if isinstance(DEFAULT_HEURISTICS[key], int):
                numeric = int(round(numeric))
            numeric = bounded(numeric, lo, hi)
            state["heuristics"][key] = numeric
            applied[key] = numeric
        state["history"].append({"created_at": utc_now(), "reason": reason, "applied": applied, "rejected": rejected})
        write_json(self.path, state)
        return {"applied": applied, "rejected": rejected, "state": state}

    def propose_protected_change(self, dotted_path: str, proposed_value: Any, reason: str) -> dict[str, Any]:
        state = self.status()
        proposal = {
            "path": dotted_path,
            "proposed_value": proposed_value,
            "reason": reason,
            "auto_applied": False,
            "owner_review_required": not Constitution.may_auto_change(dotted_path),
            "created_at": utc_now(),
        }
        state["protected_change_proposals"].append(proposal)
        write_json(self.path, state)
        return proposal
