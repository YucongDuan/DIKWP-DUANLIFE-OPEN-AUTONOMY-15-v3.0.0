from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class MissionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    RETIRED = "retired"


class ActionClass(str, Enum):
    INTERNAL_REVERSIBLE = "internal_reversible"
    EXTERNAL_PROPOSAL = "external_proposal"
    PROHIBITED = "prohibited"


class ActionStatus(str, Enum):
    PROPOSED = "proposed"
    EXECUTED_LOCAL = "executed_local"
    QUEUED_FOR_REVIEW = "queued_for_review"
    BLOCKED = "blocked"


@dataclass(slots=True)
class Mission:
    mission_id: str
    title: str
    purpose: str
    question: str
    success_criteria: list[str]
    constraints: list[str] = field(default_factory=list)
    max_cycles: int = 8
    max_local_writes: int = 12
    max_bytes_written: int = 500_000
    status: MissionStatus = MissionStatus.DRAFT
    cycle_count: int = 0
    local_writes: int = 0
    bytes_written: int = 0
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        raw = asdict(self)
        raw["status"] = self.status.value
        return raw

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Mission":
        data = dict(raw)
        data["status"] = MissionStatus(data.get("status", MissionStatus.DRAFT.value))
        return cls(**data)


@dataclass(slots=True)
class ActionProposal:
    action_id: str
    action_type: str
    action_class: ActionClass
    rationale: str
    payload: dict[str, Any]
    score: float
    status: ActionStatus = ActionStatus.PROPOSED
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        raw = asdict(self)
        raw["action_class"] = self.action_class.value
        raw["status"] = self.status.value
        return raw
