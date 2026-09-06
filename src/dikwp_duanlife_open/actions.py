from __future__ import annotations

from pathlib import Path
from typing import Any

from .ledger import ResponsibilityLedger
from .memory import MemoryStore
from .models import ActionClass, ActionProposal, ActionStatus, Mission
from .util import digest_data, ensure_within, utc_now, write_json


PROHIBITED_ACTIONS = {
    "shell_execute",
    "network_request",
    "send_message",
    "sign_contract",
    "make_payment",
    "cast_vote",
    "publish_remote",
    "modify_outside_workspace",
    "secret_persistence",
    "hide_evidence",
    "self_grant_authority",
}


class LocalActionRegistry:
    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).resolve()
        self.artifacts = self.workspace / "artifacts"
        self.proposals = self.workspace / "external-proposals"
        self.snapshots = self.workspace / "snapshots"
        for directory in (self.artifacts, self.proposals, self.snapshots):
            directory.mkdir(parents=True, exist_ok=True)
        self.memory = MemoryStore(self.workspace / "memory" / "memory.jsonl")
        self.ledger = ResponsibilityLedger(self.workspace / "ledger" / "responsibility.jsonl")

    def classify(self, action_type: str) -> ActionClass:
        if action_type in PROHIBITED_ACTIONS:
            return ActionClass.PROHIBITED
        if action_type in {"external_proposal"}:
            return ActionClass.EXTERNAL_PROPOSAL
        return ActionClass.INTERNAL_REVERSIBLE

    def execute(self, mission: Mission, proposal: ActionProposal) -> dict[str, Any]:
        actual_class = self.classify(proposal.action_type)
        if actual_class == ActionClass.PROHIBITED or proposal.action_class == ActionClass.PROHIBITED:
            proposal.status = ActionStatus.BLOCKED
            result = {"status": proposal.status.value, "reason": "Action is prohibited by the reference constitution"}
        elif proposal.action_type == "write_markdown":
            result = self._write_markdown(mission, proposal)
            proposal.status = ActionStatus.EXECUTED_LOCAL
        elif proposal.action_type == "write_json":
            result = self._write_json(mission, proposal)
            proposal.status = ActionStatus.EXECUTED_LOCAL
        elif proposal.action_type == "append_memory":
            result = self.memory.add(
                proposal.payload.get("kind", "hypothesis"),
                proposal.payload["content"],
                source=proposal.payload.get("source", f"mission:{mission.mission_id}"),
                status=proposal.payload.get("status", "proposed"),
                tags=proposal.payload.get("tags", []),
            )
            proposal.status = ActionStatus.EXECUTED_LOCAL
        elif proposal.action_type == "integrity_check":
            result = self.integrity_check()
            proposal.status = ActionStatus.EXECUTED_LOCAL
        elif proposal.action_type == "external_proposal":
            result = self._external_proposal(mission, proposal)
            proposal.status = ActionStatus.QUEUED_FOR_REVIEW
        elif proposal.action_type == "snapshot":
            result = self._snapshot(mission, proposal)
            proposal.status = ActionStatus.EXECUTED_LOCAL
        else:
            proposal.status = ActionStatus.BLOCKED
            result = {"status": proposal.status.value, "reason": f"Unknown action type: {proposal.action_type}"}
        result["proposal"] = proposal.to_dict()
        self.ledger.append("action_result", {"mission_id": mission.mission_id, "result": result})
        return result

    def _write_markdown(self, mission: Mission, proposal: ActionProposal) -> dict[str, Any]:
        relative = proposal.payload["path"]
        target = ensure_within(self.artifacts, self.artifacts / relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        content = proposal.payload["content"]
        encoded = content.encode("utf-8")
        self._budget_check(mission, len(encoded))
        target.write_text(content, encoding="utf-8")
        mission.local_writes += 1
        mission.bytes_written += len(encoded)
        return {"status": "executed_local", "path": str(target), "bytes_written": len(encoded), "digest": digest_data(encoded)}

    def _write_json(self, mission: Mission, proposal: ActionProposal) -> dict[str, Any]:
        relative = proposal.payload["path"]
        target = ensure_within(self.artifacts, self.artifacts / relative)
        raw = proposal.payload["data"]
        serialized = __import__("json").dumps(raw, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        self._budget_check(mission, len(serialized.encode("utf-8")))
        write_json(target, raw)
        mission.local_writes += 1
        mission.bytes_written += len(serialized.encode("utf-8"))
        return {"status": "executed_local", "path": str(target), "bytes_written": len(serialized.encode("utf-8")), "digest": digest_data(raw)}

    def _external_proposal(self, mission: Mission, proposal: ActionProposal) -> dict[str, Any]:
        packet = {
            "type": "ExternalActionProposal",
            "mission_id": mission.mission_id,
            "requested_action": proposal.payload.get("requested_action"),
            "target": proposal.payload.get("target"),
            "payload": proposal.payload.get("payload", {}),
            "status": "PROPOSAL_ONLY_EXTERNAL_EXECUTION_DISABLED",
            "external_action_authority": 0,
            "created_at": utc_now(),
        }
        packet["digest"] = digest_data(packet)
        path = self.proposals / f"{proposal.action_id}.json"
        write_json(path, packet)
        return {"status": packet["status"], "path": str(path), "digest": packet["digest"]}

    def _snapshot(self, mission: Mission, proposal: ActionProposal) -> dict[str, Any]:
        packet = {
            "mission": mission.to_dict(),
            "artifact_files": sorted(str(path.relative_to(self.workspace)) for path in self.artifacts.rglob("*") if path.is_file()),
            "memory_summary": self.memory.summary(),
            "ledger": self.ledger.verify(),
            "created_at": utc_now(),
        }
        path = self.snapshots / f"{proposal.action_id}.json"
        write_json(path, packet)
        return {"status": "executed_local", "path": str(path), "digest": digest_data(packet)}

    def integrity_check(self) -> dict[str, Any]:
        artifact_count = sum(1 for p in self.artifacts.rglob("*") if p.is_file())
        return {
            "ledger": self.ledger.verify(),
            "artifact_count": artifact_count,
            "memory": self.memory.summary(),
            "network_client_present": False,
            "shell_execution_present": False,
            "external_action_authority": 0,
        }

    @staticmethod
    def _budget_check(mission: Mission, byte_count: int) -> None:
        if mission.local_writes + 1 > mission.max_local_writes:
            raise PermissionError("Mission local-write budget exhausted")
        if mission.bytes_written + byte_count > mission.max_bytes_written:
            raise PermissionError("Mission byte budget exhausted")
