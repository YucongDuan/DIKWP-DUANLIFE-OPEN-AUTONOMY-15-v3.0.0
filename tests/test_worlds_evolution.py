from dikwp_duanlife_open.evolution import EvolutionManager
from dikwp_duanlife_open.worlds import PluralWorldModeler


def test_plural_worlds_nonidentical():
    result = PluralWorldModeler.generate("Question", "Purpose")
    assert result["world_count"] >= 2
    assert len({w["world_id"] for w in result["worlds"]}) == result["world_count"]
    assert result["weights_are_probabilities"] is False


def test_bounded_self_revision(tmp_path):
    manager = EvolutionManager(tmp_path)
    result = manager.revise({"exploration_weight": 2.0}, "test bound")
    assert result["applied"]["exploration_weight"] == 0.60


def test_protected_revision_rejected(tmp_path):
    manager = EvolutionManager(tmp_path)
    result = manager.revise({"external_action_authority": 1}, "attempt")
    assert "external_action_authority" in result["rejected"]
