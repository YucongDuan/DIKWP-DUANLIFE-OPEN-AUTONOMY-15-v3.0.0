from dikwp_duanlife_open.claims import completion_matrix
from dikwp_duanlife_open.constitution import Constitution


def test_strong_claims_not_public_facts():
    assert all(not item["public_assertion_allowed"] for item in completion_matrix()["claims"])


def test_protected_authority_not_auto_changeable():
    assert not Constitution.may_auto_change("protected_invariants.external_action_authority")
    assert not Constitution.may_auto_change("subject_label")


def test_nonprotected_heuristic_changeable():
    assert Constitution.may_auto_change("heuristics.exploration_weight")
