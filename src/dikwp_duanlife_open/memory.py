from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .util import canonical_json, digest_data, utc_now


class MemoryStore:
    """Provenance-bearing local memory. It never labels synthetic content as factual memory."""

    VALID_KINDS = {"observation", "evidence", "hypothesis", "decision", "outcome", "owner_report", "synthetic"}
    VALID_STATUSES = {"proposed", "confirmed", "contested", "superseded", "revoked", "expired", "synthetic"}

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def add(
        self,
        kind: str,
        content: str,
        *,
        source: str,
        status: str = "proposed",
        tags: list[str] | None = None,
        expires_at: str | None = None,
    ) -> dict[str, Any]:
        if kind not in self.VALID_KINDS:
            raise ValueError(f"Unsupported memory kind: {kind}")
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Unsupported memory status: {status}")
        if kind == "synthetic" and status != "synthetic":
            raise ValueError("Synthetic memory must retain synthetic status")
        record = {
            "memory_id": digest_data({"kind": kind, "content": content, "source": source, "created_at": utc_now()})[:20],
            "kind": kind,
            "content": content,
            "source": source,
            "status": status,
            "tags": tags or [],
            "expires_at": expires_at,
            "created_at": utc_now(),
        }
        record["digest"] = digest_data(record)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(canonical_json(record) + "\n")
        return record

    def records(self) -> list[dict[str, Any]]:
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def summary(self) -> dict[str, Any]:
        items = self.records()
        by_kind: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for item in items:
            by_kind[item["kind"]] = by_kind.get(item["kind"], 0) + 1
            by_status[item["status"]] = by_status.get(item["status"], 0) + 1
        return {"record_count": len(items), "by_kind": by_kind, "by_status": by_status}
