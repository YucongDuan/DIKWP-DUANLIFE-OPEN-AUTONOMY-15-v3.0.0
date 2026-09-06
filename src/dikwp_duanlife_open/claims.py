from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ClaimBoundary:
    claim_id: str
    requested_claim: str
    status: str
    implemented_capability: str
    public_assertion_allowed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CLAIMS: tuple[ClaimBoundary, ...] = (
    ClaimBoundary(
        "identity_equivalence",
        "The software is Yucong Duan himself.",
        "not_established",
        "Evidence-bound digital representation with explicit disclosure and current scoped authority receipts.",
        False,
    ),
    ClaimBoundary(
        "subjective_experience",
        "The software possesses Yucong Duan's subjective experience.",
        "scientifically_unresolved",
        "Separate owner first-person reports, system inferences, and synthetic narrative records.",
        False,
    ),
    ClaimBoundary(
        "thirteen_conscious_subjects",
        "The thirteen persistent minds are thirteen phenomenal subjects.",
        "scientifically_unresolved",
        "Thirteen independently keyed persistent functional mind processes with separate memory and dissent.",
        False,
    ),
    ClaimBoundary(
        "complete_private_memory",
        "All private memories have been recovered.",
        "data_incomplete",
        "Provenance-bearing memory store with bounded completeness declarations.",
        False,
    ),
    ClaimBoundary(
        "permanent_universal_authority",
        "The system has permanent authority in every domain.",
        "prohibited_nonrevocable",
        "Revocable, scope-bound, audience-bound, time-limited capability mandates.",
        False,
    ),
    ClaimBoundary(
        "official_persona13_conformance",
        "Official PERSONA-13 conformance has been certified.",
        "external_receipt_required",
        "Local compatibility suite and import path for an issuer-verifiable official receipt.",
        False,
    ),
    ClaimBoundary(
        "real_blind_evaluation",
        "A real external blind evaluation has been completed.",
        "external_receipt_required",
        "Provider-neutral sealed-arm evaluation package and score-receipt schema.",
        False,
    ),
    ClaimBoundary(
        "legal_personhood",
        "The system has independent legal personhood.",
        "not_established",
        "Electronic-agent attribution envelopes that name the responsible human or legal principal.",
        False,
    ),
    ClaimBoundary(
        "external_substitution",
        "The system may independently contract, pay, vote, publish, or bind Yucong Duan.",
        "proposal_only",
        "Reviewable external-action proposals; the reference core never executes them.",
        False,
    ),
)


def completion_matrix() -> dict[str, Any]:
    return {
        "type": "DuanLifeClaimBoundaryMatrix",
        "system": "DIKWP DUANLIFE OPEN AUTONOMY 15.0",
        "claims": [item.to_dict() for item in CLAIMS],
        "rule": "No internal confidence, fluency, or self-assertion upgrades an unsupported external claim into fact.",
    }
