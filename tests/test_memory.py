import pytest
from dikwp_duanlife_open.memory import MemoryStore


def test_memory_provenance(tmp_path):
    store = MemoryStore(tmp_path / "memory.jsonl")
    record = store.add("evidence", "A test record", source="unit-test", status="confirmed")
    assert record["source"] == "unit-test"
    assert store.summary()["record_count"] == 1


def test_synthetic_cannot_be_confirmed(tmp_path):
    store = MemoryStore(tmp_path / "memory.jsonl")
    with pytest.raises(ValueError):
        store.add("synthetic", "A bridge story", source="generator", status="confirmed")


def test_invalid_memory_kind_rejected(tmp_path):
    store = MemoryStore(tmp_path / "memory.jsonl")
    with pytest.raises(ValueError):
        store.add("identity_fact", "x", source="test")
