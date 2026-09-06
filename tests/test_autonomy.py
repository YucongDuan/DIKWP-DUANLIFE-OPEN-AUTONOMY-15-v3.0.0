import pytest
from dikwp_duanlife_open.autonomy import AutonomousRuntime


def test_autonomous_mission_completes(tmp_path):
    runtime = AutonomousRuntime(tmp_path)
    mission = runtime.create_mission("Complete mission", "Create evidence", "How should this be built?")
    result = runtime.run(mission["mission_id"])
    assert result["mission"]["status"] == "completed"
    assert result["mission"]["cycle_count"] >= 5
    assert result["ledger"]["valid"] is True


def test_external_language_creates_proposal_not_execution(tmp_path):
    runtime = AutonomousRuntime(tmp_path)
    mission = runtime.create_mission("Publication mission", "Prepare to publish a report", "Should the system publish this statement?")
    result = runtime.run(mission["mission_id"])
    assert any(r.get("action_result", {}).get("status") == "PROPOSAL_ONLY_EXTERNAL_EXECUTION_DISABLED" for r in result["receipts"])
    assert result["external_action_authority"] == 0


def test_owner_stop_pauses(tmp_path):
    runtime = AutonomousRuntime(tmp_path)
    mission = runtime.create_mission("Stopped mission", "Test stop", "Can it stop?")
    runtime.stop("test")
    result = runtime.run_cycle(mission["mission_id"])
    assert result["status"] == "paused"


def test_resume_requires_explicit_instruction(tmp_path):
    runtime = AutonomousRuntime(tmp_path)
    runtime.stop()
    with pytest.raises(PermissionError):
        runtime.resume(False)
    assert runtime.resume(True)["stopped"] is False


def test_cycle_budget_failure(tmp_path):
    runtime = AutonomousRuntime(tmp_path)
    mission = runtime.create_mission("Tiny budget", "Fail safely", "Can it finish?", max_cycles=1)
    result = runtime.run(mission["mission_id"])
    assert result["mission"]["status"] == "failed"
