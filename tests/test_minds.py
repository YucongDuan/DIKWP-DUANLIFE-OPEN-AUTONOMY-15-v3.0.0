from dikwp_duanlife_open.minds import MINDS, MindRuntime


def test_thirteen_minds_exist():
    assert len(MINDS) == 13
    assert len({m.mind_id for m in MINDS}) == 13


def test_mind_packets_independently_signed(tmp_path):
    runtime = MindRuntime(tmp_path)
    result = runtime.deliberate("How should evidence be preserved?", "Create a reversible plan")
    assert result["mind_count"] == 13
    assert all(runtime.verify_packet(packet) for packet in result["minds"])


def test_consciousness_remains_undetermined(tmp_path):
    result = MindRuntime(tmp_path).deliberate("Are these minds conscious?", "Preserve uncertainty")
    assert all(item["phenomenal_status"] == "UNDETERMINED" for item in result["minds"])
    assert result["phenomenal_consciousness_proven"] is False
