from __future__ import annotations

from importlib import resources
from pathlib import Path


def export_standalone(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = resources.files("dikwp_duanlife_open").joinpath("resources", "DIKWP_DUANLIFE_OPEN_AUTONOMY_15_OS_v3.0.0.html").read_bytes()
    target.write_bytes(data)
    return target
