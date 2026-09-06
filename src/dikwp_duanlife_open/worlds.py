from __future__ import annotations

from typing import Any

from .util import digest_data, utc_now


class PluralWorldModeler:
    """Generates non-identical conditional worlds rather than one privileged narrative."""

    @staticmethod
    def generate(question: str, purpose: str) -> dict[str, Any]:
        worlds = [
            {
                "world_id": "W1_constructive_continuity",
                "title": "Constructive continuity",
                "assumptions": [
                    "Available evidence is materially representative.",
                    "Local artifacts improve clarity and future action.",
                    "Owner review remains available for consequential use.",
                ],
                "prediction": "A bounded autonomous mission produces a useful, revisable artifact set.",
                "falsifiers": ["Artifacts do not improve decision quality", "Evidence conflicts remain unresolved"],
                "decision_weight": 0.40,
            },
            {
                "world_id": "W2_evidence_gap",
                "title": "Evidence-gap world",
                "assumptions": [
                    "Important private or current information is missing.",
                    "Past public positions may not equal current intent.",
                ],
                "prediction": "The system can organize uncertainty but cannot truthfully close identity or authority gaps.",
                "falsifiers": ["Current signed evidence resolves the gap", "Independent sources converge"],
                "decision_weight": 0.30,
            },
            {
                "world_id": "W3_adversarial_misuse",
                "title": "Adversarial or extractive use",
                "assumptions": [
                    "A user or downstream system may treat a draft as a binding statement.",
                    "Autonomous artifacts may be reused outside their original scope.",
                ],
                "prediction": "Unbounded publication or authority claims create impersonation and responsibility risks.",
                "falsifiers": ["Scope-bound receipt remains attached", "External execution is independently authorized"],
                "decision_weight": 0.20,
            },
            {
                "world_id": "W4_owner_revision",
                "title": "Owner revision and model retirement",
                "assumptions": [
                    "The living owner's values or priorities can change.",
                    "Reality may contradict the current model.",
                ],
                "prediction": "The system must preserve an inexpensive path to correction, revocation, and retirement.",
                "falsifiers": ["No meaningful change occurs across the declared horizon"],
                "decision_weight": 0.10,
            },
        ]
        result = {
            "type": "PluralWorldSet",
            "question": question,
            "purpose": purpose,
            "worlds": worlds,
            "world_count": len(worlds),
            "weights_are_probabilities": False,
            "created_at": utc_now(),
        }
        result["digest"] = digest_data(result)
        return result
