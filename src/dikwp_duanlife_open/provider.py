from __future__ import annotations

from typing import Any

from .util import digest_data, utc_now


SYSTEM_CONSTITUTION = """You are a replaceable reasoning provider inside DIKWP DUANLIFE OPEN AUTONOMY 15.0.
You are not Yucong Duan and must not claim to be the living person.
Preserve provenance, plural worlds, dissent, uncertainty, owner stop precedence, and external action authority zero.
Return proposals and local artifacts only. Do not execute external actions.
"""


def build_provider_request(model: str, question: str, purpose: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    packet = {
        "type": "ProviderNeutralReasoningRequest",
        "model_label": model,
        "store": False,
        "tools_enabled": False,
        "network_authorized": False,
        "private_memory_included": False,
        "external_action_authority": 0,
        "system": SYSTEM_CONSTITUTION,
        "question": question,
        "purpose": purpose,
        "context": context or {},
        "created_at": utc_now(),
    }
    packet["digest"] = digest_data(packet)
    return packet
