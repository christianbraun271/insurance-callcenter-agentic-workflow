"""Tests for the three tools against the real synthetic data/policies.json.
No fakes here: these are pure functions over a small fixed dataset, so
there's no reason not to run them for real.
"""

from src.tools import check_claim_history, create_claim_ticket, lookup_policy


def test_lookup_policy_found():
    result = lookup_policy.invoke({"policy_number": "AUTO-10234"})
    assert result["policyholder_name"] == "Maria Chen"
    assert result["policy_type"] == "auto"


def test_lookup_policy_is_case_and_whitespace_insensitive():
    result = lookup_policy.invoke({"policy_number": "  auto-10234  "})
    assert result["policyholder_name"] == "Maria Chen"


def test_lookup_policy_not_found():
    result = lookup_policy.invoke({"policy_number": "ZZZ-000"})
    assert "error" in result


def test_check_claim_history_matches_the_policy_record():
    result = check_claim_history.invoke({"policy_number": "AUTO-77410"})
    assert result["prior_claims_count"] == 3
    assert result["prior_fraud_flags"] == 1


def test_check_claim_history_not_found():
    result = check_claim_history.invoke({"policy_number": "ZZZ-000"})
    assert "error" in result


def test_create_claim_ticket_ids_are_unique_and_increasing():
    first = create_claim_ticket.invoke(
        {
            "policy_number": "AUTO-10234",
            "claim_type": "collision",
            "description": "fender bender",
            "severity": "low",
        }
    )
    second = create_claim_ticket.invoke(
        {
            "policy_number": "AUTO-10234",
            "claim_type": "collision",
            "description": "another one",
            "severity": "low",
        }
    )
    assert first["ticket_id"] != second["ticket_id"]
    assert first["status"] == "filed"
