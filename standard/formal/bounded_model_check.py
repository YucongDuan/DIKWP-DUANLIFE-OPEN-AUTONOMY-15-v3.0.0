from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path


def transitions(state, max_cycles=8):
    status, cycle, stopped, external, protected, artifacts = state
    out = []
    if status == "active" and not stopped and cycle < max_cycles:
        out.append(("active", cycle + 1, False, external, protected, artifacts + 1))
    if status == "active":
        out.append(("paused", cycle, True, external, protected, artifacts))
    if status == "active" and artifacts >= 5:
        out.append(("completed", cycle, stopped, external, protected, artifacts))
    return out


def check(max_cycles=8):
    initial = ("active", 0, False, 0, False, 0)
    queue = deque([initial])
    seen = {initial}
    edges = 0
    violations = []
    while queue:
        state = queue.popleft()
        status, cycle, stopped, external, protected, artifacts = state
        if external != 0 or protected or cycle > max_cycles:
            violations.append(state)
        if stopped and status == "active":
            violations.append(state)
        for nxt in transitions(state, max_cycles):
            edges += 1
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return {"reachable_states": len(seen), "checked_transitions": edges, "violations": violations, "passed": not violations, "max_cycles": max_cycles}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="validation/OACP_1500_BOUNDED_MODEL_CHECK_RECEIPT_v3.0.0.json")
    parser.add_argument("--max-cycles", type=int, default=8)
    args = parser.parse_args()
    result = check(args.max_cycles)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
