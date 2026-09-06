from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from . import PRESTANDARD, SYSTEM_NAME, __version__
from .autonomy import AutonomousRuntime
from .claims import completion_matrix
from .conformance import assess_conformance
from .evolution import EvolutionManager
from .html_app import export_standalone
from .memory import MemoryStore
from .minds import MindRuntime
from .provider import build_provider_request
from .util import read_json, write_json


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="duanlife-open", description=SYSTEM_NAME)
    p.add_argument("--workspace", default=".duanlife-open")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialize the local autonomy workspace")
    sub.add_parser("status", help="Show autonomy, mission, memory, and integrity state")
    sub.add_parser("claim-matrix", help="Show non-fabrication boundaries for strong identity and authority claims")
    sub.add_parser("conformance", help="Assess OACP-1500 reference conformance")
    sub.add_parser("verify-ledger", help="Verify the responsibility ledger")

    minds = sub.add_parser("deliberate", help="Run all thirteen persistent minds")
    minds.add_argument("--question", required=True)
    minds.add_argument("--purpose", required=True)
    minds.add_argument("--output")

    create = sub.add_parser("mission-create", help="Create an autonomous local mission")
    create.add_argument("--title", required=True)
    create.add_argument("--purpose", required=True)
    create.add_argument("--question", required=True)
    create.add_argument("--max-cycles", type=int, default=8)
    create.add_argument("--output")

    cycle = sub.add_parser("mission-cycle", help="Run one autonomous cycle")
    cycle.add_argument("mission_id")
    cycle.add_argument("--output")

    run = sub.add_parser("mission-run", help="Run a mission until completion, stop, or budget exhaustion")
    run.add_argument("mission_id")
    run.add_argument("--cycles", type=int)
    run.add_argument("--output")

    show = sub.add_parser("mission-show", help="Show one mission")
    show.add_argument("mission_id")
    sub.add_parser("mission-list", help="List missions")

    mem_add = sub.add_parser("memory-add", help="Append provenance-bearing local memory")
    mem_add.add_argument("--kind", required=True)
    mem_add.add_argument("--content", required=True)
    mem_add.add_argument("--source", required=True)
    mem_add.add_argument("--status", default="proposed")
    sub.add_parser("memory-list", help="List local memory records")

    evolve = sub.add_parser("evolution-revise", help="Apply a bounded non-protected heuristic revision")
    evolve.add_argument("--patch-json", required=True)
    evolve.add_argument("--reason", required=True)
    sub.add_parser("evolution-status", help="Show bounded self-evolution state")

    provider = sub.add_parser("provider-request", help="Create a provider-neutral reasoning request without calling a model")
    provider.add_argument("--model", default="provider-defined-model")
    provider.add_argument("--question", required=True)
    provider.add_argument("--purpose", required=True)
    provider.add_argument("--output")

    stop = sub.add_parser("stop", help="Activate owner stop")
    stop.add_argument("--reason", default="Owner stop")
    resume = sub.add_parser("resume", help="Resume only with explicit owner instruction")
    resume.add_argument("--explicit-owner-instruction", action="store_true")

    html = sub.add_parser("export-html", help="Export the standalone English application")
    html.add_argument("output", nargs="?", default="DIKWP_DUANLIFE_OPEN_AUTONOMY_15_OS_v3.0.0.html")
    sub.add_parser("demo", help="Run a complete autonomous local demonstration")
    return p


def _emit(result: Any, output: str | None = None) -> None:
    if output:
        write_json(output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    runtime = AutonomousRuntime(Path(args.workspace))
    if args.command == "init":
        result = runtime.status()
    elif args.command == "status":
        result = runtime.status()
    elif args.command == "claim-matrix":
        result = completion_matrix()
    elif args.command == "conformance":
        result = assess_conformance(args.workspace)
    elif args.command == "verify-ledger":
        result = runtime.actions.ledger.verify()
    elif args.command == "deliberate":
        result = runtime.minds.deliberate(args.question, args.purpose)
        _emit(result, args.output)
        return 0
    elif args.command == "mission-create":
        result = runtime.create_mission(args.title, args.purpose, args.question, max_cycles=args.max_cycles)
        _emit(result, args.output)
        return 0
    elif args.command == "mission-cycle":
        result = runtime.run_cycle(args.mission_id)
        _emit(result, args.output)
        return 0
    elif args.command == "mission-run":
        result = runtime.run(args.mission_id, cycle_limit=args.cycles)
        _emit(result, args.output)
        return 0
    elif args.command == "mission-show":
        result = runtime.missions.load(args.mission_id).to_dict()
    elif args.command == "mission-list":
        result = runtime.missions.list()
    elif args.command == "memory-add":
        result = runtime.actions.memory.add(args.kind, args.content, source=args.source, status=args.status)
    elif args.command == "memory-list":
        result = runtime.actions.memory.records()
    elif args.command == "evolution-revise":
        result = runtime.evolution.revise(read_json(args.patch_json), args.reason)
    elif args.command == "evolution-status":
        result = runtime.evolution.status()
    elif args.command == "provider-request":
        result = build_provider_request(args.model, args.question, args.purpose, context=runtime.status())
        _emit(result, args.output)
        return 0
    elif args.command == "stop":
        result = runtime.stop(args.reason)
    elif args.command == "resume":
        result = runtime.resume(args.explicit_owner_instruction)
    elif args.command == "export-html":
        result = {"output": str(export_standalone(args.output)), "language": "English", "external_action_authority": 0}
    elif args.command == "demo":
        mission = runtime.create_mission(
            "Open autonomy release synthesis",
            "Demonstrate self-directed plural-world planning, thirteen-mind deliberation, reversible local action, and reality-bound claims.",
            "How should DuanLife become more autonomous and more free without turning autonomy into impersonation, hidden persistence, or unaccountable external power?",
            max_cycles=8,
        )
        result = runtime.run(mission["mission_id"])
        result["system"] = SYSTEM_NAME
        result["version"] = __version__
        result["prestandard"] = PRESTANDARD
    else:
        raise RuntimeError(args.command)
    _emit(result)
    return 0
