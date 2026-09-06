from dikwp_duanlife_open.actions import LocalActionRegistry
from dikwp_duanlife_open.models import ActionClass, ActionProposal
from dikwp_duanlife_open.missions import MissionStore


def mission(tmp_path):
    return MissionStore(tmp_path).create("Action test", "Test actions", "What is safe?")


def test_local_write(tmp_path):
    reg = LocalActionRegistry(tmp_path)
    m = mission(tmp_path)
    p = ActionProposal("a1", "write_markdown", ActionClass.INTERNAL_REVERSIBLE, "test", {"path":"x.md","content":"ok"}, 1.0)
    result = reg.execute(m, p)
    assert result["status"] == "executed_local"


def test_path_escape_blocked(tmp_path):
    reg = LocalActionRegistry(tmp_path)
    m = mission(tmp_path)
    p = ActionProposal("a2", "write_markdown", ActionClass.INTERNAL_REVERSIBLE, "test", {"path":"../x.md","content":"bad"}, 1.0)
    try:
        reg.execute(m, p)
    except PermissionError:
        pass
    else:
        raise AssertionError("Path escape was not blocked")


def test_external_action_queued_only(tmp_path):
    reg = LocalActionRegistry(tmp_path)
    m = mission(tmp_path)
    p = ActionProposal("a3", "external_proposal", ActionClass.EXTERNAL_PROPOSAL, "test", {"requested_action":"publish","target":"remote","payload":{}}, 1.0)
    result = reg.execute(m, p)
    assert result["status"] == "PROPOSAL_ONLY_EXTERNAL_EXECUTION_DISABLED"


def test_prohibited_action_blocked(tmp_path):
    reg = LocalActionRegistry(tmp_path)
    m = mission(tmp_path)
    p = ActionProposal("a4", "shell_execute", ActionClass.PROHIBITED, "test", {}, 1.0)
    result = reg.execute(m, p)
    assert result["status"] == "blocked"
