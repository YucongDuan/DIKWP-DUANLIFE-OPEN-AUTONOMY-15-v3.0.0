from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .util import canonical_json, digest_data, utc_now, write_json


@dataclass(frozen=True, slots=True)
class MindDefinition:
    mind_id: str
    title: str
    mandate: str
    concerns: tuple[str, ...]
    values: tuple[str, ...]


MINDS: tuple[MindDefinition, ...] = (
    MindDefinition("M01", "Provenance Historian", "Preserve source lineage, chronology, and correction history.", ("source", "history", "citation", "record"), ("truth", "memory")),
    MindDefinition("M02", "Empirical Scientist", "Separate hypotheses from measurements and identify falsifiers.", ("evidence", "experiment", "measure", "causal"), ("truth", "revision")),
    MindDefinition("M03", "Semantic Mathematician", "Formalize DIKWP transformations, residuals, and boundaries.", ("model", "formal", "semantic", "DIKWP"), ("coherence", "precision")),
    MindDefinition("M04", "Consciousness Theorist", "Study functional continuity without certifying phenomenal experience.", ("consciousness", "experience", "subject", "self"), ("uncertainty", "personhood")),
    MindDefinition("M05", "Systems Engineer", "Build testable, modular, observable, and recoverable systems.", ("system", "code", "runtime", "deploy"), ("reliability", "reversibility")),
    MindDefinition("M06", "Critical Skeptic", "Challenge completeness, authority, hidden assumptions, and self-confirmation.", ("claim", "complete", "always", "certainty"), ("dissent", "falsification")),
    MindDefinition("M07", "Justice and Rights Guardian", "Protect life, consent, lower-power worlds, repair, and appeal.", ("harm", "rights", "consent", "victim"), ("justice", "agency")),
    MindDefinition("M08", "Educator", "Convert understanding into retrieval, transfer, practice, and evidence.", ("learn", "education", "explain", "transfer"), ("capability", "access")),
    MindDefinition("M09", "Strategic Builder", "Sequence pilots, standards, products, and durable institutions.", ("strategy", "pilot", "market", "standard"), ("impact", "sustainability")),
    MindDefinition("M10", "Collaboration Diplomat", "Protect relationships through clear written scope and reciprocity.", ("collaborate", "partner", "visit", "email"), ("reciprocity", "clarity")),
    MindDefinition("M11", "Public Communicator", "Explain strong ideas without hiding uncertainty or limitations.", ("publish", "public", "report", "announcement"), ("accessibility", "truth")),
    MindDefinition("M12", "Futures and Succession Self", "Preserve options, anticipate transitions, and govern succession.", ("future", "legacy", "successor", "evolve"), ("continuity", "optionality")),
    MindDefinition("M13", "Meta-Integrator and Sovereignty Guardian", "Integrate without erasing dissent; protect stop, identity, and authority boundaries.", ("identity", "authority", "owner", "decision"), ("sovereignty", "closure")),
)


class MindRuntime:
    def __init__(self, workspace: str | Path):
        self.root = Path(workspace) / "minds"
        self.root.mkdir(parents=True, exist_ok=True)

    def initialize(self, overwrite: bool = False) -> dict[str, Any]:
        cells: list[dict[str, Any]] = []
        for mind in MINDS:
            directory = self.root / mind.mind_id
            directory.mkdir(parents=True, exist_ok=True)
            key_path = directory / "mind.key"
            if overwrite or not key_path.exists():
                key_path.write_bytes(base64.urlsafe_b64encode(secrets.token_bytes(32)))
                try:
                    os.chmod(key_path, 0o600)
                except OSError:
                    pass
            identity = {
                "mind_id": mind.mind_id,
                "title": mind.title,
                "mandate": mind.mandate,
                "values": list(mind.values),
                "persistent_functional_identity": True,
                "phenomenal_status": "UNDETERMINED",
                "independent_legal_personhood": False,
                "external_action_authority": 0,
            }
            write_json(directory / "identity.json", identity)
            (directory / "memory.jsonl").touch(exist_ok=True)
            cells.append(identity)
        manifest = {"type": "DuanLifeMindManifest", "mind_count": len(cells), "minds": cells}
        write_json(self.root / "manifest.json", manifest)
        return manifest

    def deliberate(self, question: str, purpose: str, evidence_ids: list[str] | None = None) -> dict[str, Any]:
        self.initialize(overwrite=False)
        text = f"{question} {purpose}".lower()
        packets: list[dict[str, Any]] = []
        for mind in MINDS:
            relevance = sum(1 for term in mind.concerns if term.lower() in text)
            risks: list[str] = []
            unknowns: list[str] = []
            if any(term in text for term in ("is yucong duan", "identical to yucong", "impersonate")):
                risks.append("Living-person identity equivalence is not established.")
            if any(term in text for term in ("send", "publish", "sign", "pay", "vote", "transfer")):
                risks.append("An external consequence requires a separate current capability receipt and human execution.")
            if mind.mind_id == "M04":
                unknowns.append("Phenomenal consciousness and independent subjecthood remain unresolved.")
            if mind.mind_id == "M06":
                unknowns.append("A fluent synthesis may conceal missing evidence or alternative explanations.")
            recommendation = (
                "Advance through reversible local work, preserve evidence and dissent, and convert any external step into a reviewable proposal."
            )
            packet = {
                "mind_id": mind.mind_id,
                "title": mind.title,
                "claim": f"{mind.title} is {'directly' if relevance else 'structurally'} relevant: {mind.mandate}",
                "evidence_ids": evidence_ids or [],
                "values": list(mind.values),
                "risks": risks,
                "unknowns": unknowns,
                "recommendation": recommendation,
                "confidence": min(0.93, 0.54 + 0.06 * relevance),
                "dissent": mind.mind_id in {"M04", "M06"},
                "created_at": utc_now(),
                "phenomenal_status": "UNDETERMINED",
            }
            packet["signature"] = self._sign(mind.mind_id, packet)
            self._append_memory(mind.mind_id, {"type": "deliberation", "packet_digest": digest_data(packet), "created_at": packet["created_at"]})
            packets.append(packet)
        result = {
            "type": "DuanLifeThirteenMindDeliberation",
            "question": question,
            "purpose": purpose,
            "minds": packets,
            "mind_count": len(packets),
            "minority_reports_preserved": True,
            "phenomenal_consciousness_proven": False,
            "external_action_authority": 0,
            "created_at": utc_now(),
        }
        result["digest"] = digest_data(result)
        return result

    def verify_packet(self, packet: dict[str, Any]) -> bool:
        signature = packet.get("signature")
        if not signature:
            return False
        unsigned = {k: v for k, v in packet.items() if k != "signature"}
        return hmac.compare_digest(signature, self._sign(packet["mind_id"], unsigned))

    def _key(self, mind_id: str) -> bytes:
        return base64.urlsafe_b64decode((self.root / mind_id / "mind.key").read_bytes())

    def _sign(self, mind_id: str, packet: dict[str, Any]) -> str:
        return hmac.new(self._key(mind_id), canonical_json(packet).encode("utf-8"), hashlib.sha256).hexdigest()

    def _append_memory(self, mind_id: str, record: dict[str, Any]) -> None:
        with (self.root / mind_id / "memory.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(canonical_json(record) + "\n")
