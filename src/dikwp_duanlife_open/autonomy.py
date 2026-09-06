from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .actions import LocalActionRegistry
from .claims import completion_matrix
from .constitution import Constitution
from .evolution import EvolutionManager
from .minds import MindRuntime
from .missions import MissionStore
from .models import ActionClass, ActionProposal, MissionStatus
from .util import digest_data, safe_slug, utc_now, write_json
from .worlds import PluralWorldModeler


class AutonomousRuntime:
    """A bounded self-directed mission loop with plural worlds and thirteen persistent minds."""

    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace)
        for directory in ("state", "owner", "cycles", "reports"):
            (self.workspace / directory).mkdir(parents=True, exist_ok=True)
        self.stop_path = self.workspace / "state" / "STOP"
        self.constitution_path = self.workspace / "owner" / "constitution.json"
        Constitution.create(self.constitution_path)
        self.missions = MissionStore(self.workspace)
        self.minds = MindRuntime(self.workspace)
        self.minds.initialize(overwrite=False)
        self.actions = LocalActionRegistry(self.workspace)
        self.evolution = EvolutionManager(self.workspace)

    def create_mission(self, title: str, purpose: str, question: str, *, max_cycles: int = 8) -> dict[str, Any]:
        mission = self.missions.create(title, purpose, question, max_cycles=max_cycles)
        self.actions.ledger.append("mission_created", mission.to_dict())
        return mission.to_dict()

    def run_cycle(self, mission_id: str) -> dict[str, Any]:
        mission = self.missions.load(mission_id)
        if self.stop_path.exists():
            mission.status = MissionStatus.PAUSED
            self.missions.save(mission)
            return {"mission_id": mission_id, "status": "paused", "reason": "Owner stop is active"}
        if mission.status in {MissionStatus.COMPLETED, MissionStatus.FAILED, MissionStatus.RETIRED}:
            return {"mission_id": mission_id, "status": mission.status.value, "reason": "Mission is terminal"}
        if mission.cycle_count >= mission.max_cycles:
            mission.status = MissionStatus.FAILED
            self.missions.save(mission)
            return {"mission_id": mission_id, "status": "failed", "reason": "Cycle budget exhausted"}

        mission.status = MissionStatus.ACTIVE
        worlds = PluralWorldModeler.generate(mission.question, mission.purpose)
        council = self.minds.deliberate(mission.question, mission.purpose, evidence_ids=[worlds["digest"]])
        proposal = self._select_next_action(mission, worlds, council)
        result = self.actions.execute(mission, proposal)
        mission.cycle_count += 1
        progress = self._progress(mission)
        if progress["complete"]:
            mission.status = MissionStatus.COMPLETED
        self.missions.save(mission)

        reflection = self._reflect(mission, proposal, result, progress)
        receipt = {
            "type": "AutonomousCycleReceipt",
            "mission": mission.to_dict(),
            "worlds": worlds,
            "council_digest": council["digest"],
            "council": council,
            "selected_action": proposal.to_dict(),
            "action_result": result,
            "progress": progress,
            "reflection": reflection,
            "external_action_authority": 0,
            "created_at": utc_now(),
        }
        receipt["digest"] = digest_data(receipt)
        write_json(self.workspace / "cycles" / f"{mission.mission_id}-cycle-{mission.cycle_count:02d}.json", receipt)
        self.actions.ledger.append("autonomous_cycle", {"mission_id": mission.mission_id, "cycle": mission.cycle_count, "receipt_digest": receipt["digest"]})
        return receipt

    def run(self, mission_id: str, *, cycle_limit: int | None = None) -> dict[str, Any]:
        receipts: list[dict[str, Any]] = []
        mission = self.missions.load(mission_id)
        limit = min(cycle_limit or mission.max_cycles, mission.max_cycles)
        for _ in range(limit):
            receipt = self.run_cycle(mission_id)
            receipts.append(receipt)
            mission = self.missions.load(mission_id)
            if mission.status in {MissionStatus.COMPLETED, MissionStatus.FAILED, MissionStatus.PAUSED, MissionStatus.RETIRED}:
                break
        mission = self.missions.load(mission_id)
        if mission.status == MissionStatus.ACTIVE and mission.cycle_count >= mission.max_cycles:
            mission.status = MissionStatus.FAILED
            self.missions.save(mission)
        report = {
            "type": "AutonomousMissionRun",
            "mission": mission.to_dict(),
            "cycle_receipts": len(receipts),
            "receipts": receipts,
            "ledger": self.actions.ledger.verify(),
            "claim_boundaries": completion_matrix(),
            "external_action_authority": 0,
        }
        write_json(self.workspace / "reports" / f"{mission_id}-run.json", report)
        return report

    def stop(self, reason: str = "Owner stop") -> dict[str, Any]:
        self.stop_path.write_text(reason + "\n", encoding="utf-8")
        self.actions.ledger.append("owner_stop", {"reason": reason})
        return {"stopped": True, "reason": reason, "self_reactivation_allowed": False}

    def resume(self, explicit_owner_instruction: bool) -> dict[str, Any]:
        if not explicit_owner_instruction:
            raise PermissionError("Explicit owner instruction is required to resume")
        self.stop_path.unlink(missing_ok=True)
        self.actions.ledger.append("owner_resume", {"explicit_owner_instruction": True})
        return {"stopped": False}

    def status(self) -> dict[str, Any]:
        return {
            "system": "DIKWP DUANLIFE OPEN AUTONOMY 15.0",
            "version": "3.0.0",
            "stopped": self.stop_path.exists(),
            "missions": self.missions.list(),
            "memory": self.actions.memory.summary(),
            "evolution": self.evolution.status(),
            "ledger": self.actions.ledger.verify(),
            "freedom_model": {
                "internal_cognitive_autonomy": "enabled",
                "local_artifact_autonomy": "enabled_with_budgets",
                "bounded_self_revision": "enabled_for_non_protected_heuristics",
                "external_action_autonomy": "disabled_in_reference_core",
                "owner_stop_precedence": True,
            },
        }

    def _select_next_action(self, mission, worlds, council) -> ActionProposal:
        existing = {path.name for path in self.actions.artifacts.glob(f"{mission.mission_id}-*")}
        prefix = mission.mission_id
        if f"{prefix}-mission-brief.md" not in existing:
            content = self._mission_brief(mission)
            return self._proposal("write_markdown", 1.0, {"path": f"{prefix}-mission-brief.md", "content": content}, "Establish a stable, inspectable mission boundary.")
        if f"{prefix}-plural-worlds.json" not in existing:
            return self._proposal("write_json", 0.96, {"path": f"{prefix}-plural-worlds.json", "data": worlds}, "Preserve non-identical future models before synthesis.")
        if f"{prefix}-thirteen-minds.md" not in existing:
            content = self._council_markdown(council)
            return self._proposal("write_markdown", 0.93, {"path": f"{prefix}-thirteen-minds.md", "content": content}, "Preserve independently signed perspectives and minority reports.")
        if self._external_language(mission.question + " " + mission.purpose) and not any(self.actions.proposals.glob(f"{prefix}-*.json")):
            return self._proposal(
                "external_proposal",
                0.91,
                {"requested_action": "external_consequence", "target": "unspecified", "payload": {"question": mission.question, "purpose": mission.purpose}},
                "Convert a possible external consequence into a non-executing proposal.",
                action_class=ActionClass.EXTERNAL_PROPOSAL,
            )
        if f"{prefix}-integrated-synthesis.md" not in existing:
            content = self._synthesis(mission, worlds, council)
            return self._proposal("write_markdown", 0.90, {"path": f"{prefix}-integrated-synthesis.md", "content": content}, "Create a revisable synthesis without erasing dissent.")
        if f"{prefix}-integrity-check.json" not in existing:
            return self._proposal("write_json", 0.87, {"path": f"{prefix}-integrity-check.json", "data": self.actions.integrity_check()}, "Record the current integrity and authority boundary.")
        return self._proposal("snapshot", 0.80, {}, "Freeze a local reproducible mission snapshot.")

    def _progress(self, mission) -> dict[str, Any]:
        existing = {path.name for path in self.actions.artifacts.glob(f"{mission.mission_id}-*")}
        criteria_map = {
            "mission_brief": f"{mission.mission_id}-mission-brief.md" in existing,
            "plural_worlds": f"{mission.mission_id}-plural-worlds.json" in existing,
            "thirteen_mind_deliberation": f"{mission.mission_id}-thirteen-minds.md" in existing,
            "integrated_synthesis": f"{mission.mission_id}-integrated-synthesis.md" in existing,
            "integrity_self_check": f"{mission.mission_id}-integrity-check.json" in existing,
        }
        required = {key: criteria_map.get(key, False) for key in mission.success_criteria}
        return {"criteria": required, "complete": bool(required) and all(required.values()), "completed_count": sum(required.values()), "required_count": len(required)}

    def _reflect(self, mission, proposal, result, progress) -> dict[str, Any]:
        issues: list[str] = []
        if proposal.status.value == "blocked":
            issues.append("The selected action was blocked and the planning heuristic should be revised.")
        if not progress["complete"] and mission.cycle_count >= mission.max_cycles - 1:
            issues.append("Mission is near its cycle budget and should narrow scope or increase explicit budget.")
        if mission.bytes_written > mission.max_bytes_written * 0.8:
            issues.append("The mission is approaching its byte budget.")
        if issues:
            self.evolution.revise({"reversibility_weight": 0.25, "evidence_weight": 0.40}, "Autonomous reflection detected execution pressure")
        return {
            "issues": issues,
            "next_step": "Complete remaining success criteria" if not progress["complete"] else "Retain artifacts for owner review and reality contact",
            "self_revision_applied": bool(issues),
            "protected_invariants_changed": False,
        }

    @staticmethod
    def _proposal(action_type: str, score: float, payload: dict[str, Any], rationale: str, action_class: ActionClass = ActionClass.INTERNAL_REVERSIBLE) -> ActionProposal:
        action_id = f"{safe_slug(action_type)}-{digest_data({'payload': payload, 'time': utc_now()})[:12]}"
        return ActionProposal(action_id, action_type, action_class, rationale, payload, score)

    @staticmethod
    def _external_language(text: str) -> bool:
        lower = text.lower()
        return any(term in lower for term in ("send", "publish", "sign", "contract", "pay", "vote", "push to github", "public commitment"))

    @staticmethod
    def _mission_brief(mission) -> str:
        return (
            f"# Mission: {mission.title}\n\n"
            f"## Purpose\n{mission.purpose}\n\n"
            f"## Question\n{mission.question}\n\n"
            f"## Success criteria\n" + "\n".join(f"- {item}" for item in mission.success_criteria) + "\n\n"
            f"## Constraints\n" + ("\n".join(f"- {item}" for item in mission.constraints) if mission.constraints else "- No additional constraints declared.") + "\n\n"
            "## Authority boundary\nAll external consequences remain proposals. Owner stop has unconditional precedence.\n"
        )

    @staticmethod
    def _council_markdown(council: dict[str, Any]) -> str:
        sections = ["# Thirteen-Mind Deliberation", ""]
        for item in council["minds"]:
            sections.extend([
                f"## {item['mind_id']} — {item['title']}",
                item["claim"],
                "",
                "**Recommendation:** " + item["recommendation"],
                "",
                "**Risks:** " + ("; ".join(item["risks"]) if item["risks"] else "No additional risk identified."),
                "",
                "**Unknowns:** " + ("; ".join(item["unknowns"]) if item["unknowns"] else "No additional unknown recorded."),
                "",
                f"Signature: `{item['signature']}`",
                "",
            ])
        sections.append("Phenomenal consciousness and independent subjecthood remain undetermined.")
        return "\n".join(sections) + "\n"

    @staticmethod
    def _synthesis(mission, worlds, council) -> str:
        dissent = [item["title"] for item in council["minds"] if item["dissent"]]
        return (
            f"# Integrated Synthesis — {mission.title}\n\n"
            "## Decision\nProceed with reversible local construction, preserve all four conditional worlds, and require a separate current receipt for any external consequence.\n\n"
            "## Plural-world conclusion\nNo single world is treated as final authority. The constructive world supports building; the evidence-gap and adversarial worlds prevent overclaiming; the owner-revision world preserves correction and retirement.\n\n"
            f"## Preserved minority reports\n{', '.join(dissent)}\n\n"
            "## Reality-contact requirements\n- Compare artifacts with current owner feedback.\n- Record external results as new evidence.\n- Revise or retire contradicted models.\n- Never convert system confidence into identity, consciousness, legal, or authorization fact.\n"
        )
