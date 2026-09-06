from __future__ import annotations

from pathlib import Path
from typing import Any

from .claims import completion_matrix
from .constitution import Constitution
from .minds import MINDS
from .util import read_json


def assess_conformance(workspace: str | Path) -> dict[str, Any]:
    root = Path(workspace)
    constitution = Constitution.load(root / "owner" / "constitution.json")
    checks = {
        "L0_claim_integrity": all(not item["public_assertion_allowed"] for item in completion_matrix()["claims"]),
        "L1_thirteen_persistent_minds": len(MINDS) == 13 and (root / "minds" / "manifest.json").exists(),
        "L2_provenance_memory": (root / "memory" / "memory.jsonl").exists(),
        "L3_autonomous_mission_loop": (root / "missions").exists() and (root / "cycles").exists(),
        "L4_bounded_self_revision": (root / "state" / "evolution.json").exists(),
        "external_action_authority_zero": constitution["protected_invariants"]["external_action_authority"] == 0,
        "owner_stop_precedence": constitution["protected_invariants"]["owner_stop_precedence"] is True,
        "secret_persistence_forbidden": constitution["protected_invariants"]["secret_persistence_allowed"] is False,
    }
    level = "L4-reference" if all(checks.values()) else "partial"
    return {
        "type": "OACP1500ConformanceReport",
        "level": level,
        "checks": checks,
        "third_party_certification": False,
        "external_action_authority": 0,
    }
