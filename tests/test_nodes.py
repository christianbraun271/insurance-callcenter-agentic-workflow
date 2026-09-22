"""Tests for verify_identity_node, the one node with no LLM call, so it's
plain deterministic logic over the real synthetic data/policies.json.
"""

from src.nodes import verify_identity_node


def test_verified_when_name_matches():
    result = verify_identity_node(
        {"policy_number": "AUTO-10234", "caller_name": "Maria Chen", "agent_log": []}
    )
    assert result["identity_verified"] is True
    assert result["policy_record"]["policyholder_name"] == "Maria Chen"


def test_not_verified_on_name_mismatch_but_record_is_still_returned():
    result = verify_identity_node(
        {"policy_number": "AUTO-10234", "caller_name": "Someone Else", "agent_log": []}
    )
    assert result["identity_verified"] is False
    # The record stays attached even on a failed match, so a human picking
    # up the escalation isn't starting from nothing.
    assert result["policy_record"] is not None


def test_not_verified_on_unknown_policy_number():
    result = verify_identity_node(
        {"policy_number": "ZZZ-000", "caller_name": "Robert Smith", "agent_log": []}
    )
    assert result["identity_verified"] is False
    assert result["policy_record"] is None


def test_not_verified_when_no_policy_number_was_captured():
    result = verify_identity_node({"agent_log": []})
    assert result["identity_verified"] is False
    assert result["policy_record"] is None


def test_appends_to_rather_than_replaces_the_existing_log():
    result = verify_identity_node(
        {
            "policy_number": "AUTO-10234",
            "caller_name": "Maria Chen",
            "agent_log": ["[intake] intent='claim'"],
        }
    )
    assert len(result["agent_log"]) == 2
