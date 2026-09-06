import json
from dikwp_duanlife_open.ledger import ResponsibilityLedger


def test_ledger_valid_and_tamper_detected(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger = ResponsibilityLedger(path)
    ledger.append("x", {"a":1})
    ledger.append("y", {"b":2})
    assert ledger.verify()["valid"] is True
    lines = path.read_text(encoding="utf-8").splitlines()
    record = json.loads(lines[0])
    record["payload"]["a"] = 9
    lines[0] = json.dumps(record)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert ledger.verify()["valid"] is False
