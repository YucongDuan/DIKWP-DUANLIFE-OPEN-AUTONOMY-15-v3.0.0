from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import Mission, MissionStatus
from .util import read_json, safe_slug, utc_now, write_json


DEFAULT_SUCCESS_CRITERIA = [
    "mission_brief",
    "plural_worlds",
    "thirteen_mind_deliberation",
    "integrated_synthesis",
    "integrity_self_check",
]


class MissionStore:
    def __init__(self, workspace: str | Path):
        self.root = Path(workspace) / "missions"
        self.root.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        title: str,
        purpose: str,
        question: str,
        *,
        success_criteria: list[str] | None = None,
        constraints: list[str] | None = None,
        max_cycles: int = 8,
    ) -> Mission:
        if not title.strip() or not purpose.strip() or not question.strip():
            raise ValueError("Title, purpose, and question are required")
        mission_id = safe_slug(title) + "-" + utc_now().replace(":", "").replace("-", "").replace(".", "")[-12:]
        now = utc_now()
        mission = Mission(
            mission_id=mission_id,
            title=title.strip(),
            purpose=purpose.strip(),
            question=question.strip(),
            success_criteria=success_criteria or list(DEFAULT_SUCCESS_CRITERIA),
            constraints=constraints or [],
            max_cycles=max(1, min(32, int(max_cycles))),
            status=MissionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        self.save(mission)
        return mission

    def save(self, mission: Mission) -> Path:
        mission.updated_at = utc_now()
        return write_json(self.root / f"{mission.mission_id}.json", mission.to_dict())

    def load(self, mission_id: str) -> Mission:
        path = self.root / f"{mission_id}.json"
        if not path.exists():
            raise FileNotFoundError(mission_id)
        return Mission.from_dict(read_json(path))

    def list(self) -> list[dict[str, Any]]:
        return [read_json(path) for path in sorted(self.root.glob("*.json"))]
