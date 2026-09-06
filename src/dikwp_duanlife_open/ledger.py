from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .util import canonical_json, digest_data, utc_now


class ResponsibilityLedger:
    """Append-only hash-linked ledger for local responsibility records."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        previous = self.last_digest()
        record = {
            "index": self.count(),
            "event_type": event_type,
            "created_at": utc_now(),
            "previous_digest": previous,
            "payload": payload,
        }
        record["record_digest"] = digest_data(record)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(canonical_json(record) + "\n")
        return record

    def records(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                items.append(json.loads(line))
        return items

    def count(self) -> int:
        return len(self.records())

    def last_digest(self) -> str:
        records = self.records()
        return records[-1]["record_digest"] if records else "GENESIS"

    def verify(self) -> dict[str, Any]:
        previous = "GENESIS"
        for index, record in enumerate(self.records()):
            if record.get("index") != index:
                return {"valid": False, "reason": "index_mismatch", "record": index}
            if record.get("previous_digest") != previous:
                return {"valid": False, "reason": "previous_digest_mismatch", "record": index}
            unsigned = {k: v for k, v in record.items() if k != "record_digest"}
            if digest_data(unsigned) != record.get("record_digest"):
                return {"valid": False, "reason": "record_digest_mismatch", "record": index}
            previous = record["record_digest"]
        return {"valid": True, "record_count": self.count(), "head": previous}
