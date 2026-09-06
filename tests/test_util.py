from pathlib import Path
import pytest
from dikwp_duanlife_open.util import digest_data, ensure_within, safe_slug


def test_digest_deterministic():
    assert digest_data({"b": 2, "a": 1}) == digest_data({"a": 1, "b": 2})


def test_safe_slug():
    assert safe_slug("Hello, Open Autonomy!") == "hello-open-autonomy"


def test_path_confinement(tmp_path):
    assert ensure_within(tmp_path, "a/b.txt").is_relative_to(tmp_path.resolve())
    with pytest.raises(PermissionError):
        ensure_within(tmp_path, "../escape.txt")
