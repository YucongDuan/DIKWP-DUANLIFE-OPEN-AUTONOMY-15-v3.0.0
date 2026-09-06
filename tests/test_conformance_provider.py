from dikwp_duanlife_open.autonomy import AutonomousRuntime
from dikwp_duanlife_open.conformance import assess_conformance
from dikwp_duanlife_open.provider import build_provider_request


def test_conformance_l4_reference(tmp_path):
    AutonomousRuntime(tmp_path)
    result = assess_conformance(tmp_path)
    assert result["level"] == "L4-reference"


def test_provider_request_has_no_authority():
    result = build_provider_request("example-model", "Question", "Purpose")
    assert result["external_action_authority"] == 0
    assert result["network_authorized"] is False
    assert result["tools_enabled"] is False
