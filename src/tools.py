"""Tools that stand in for the call center's backend systems: a policy
administration system and a claims system. Backed by data/policies.json --
a small synthetic book of business, not a real insurer's data.
"""

from __future__ import annotations

import json
from itertools import count
from pathlib import Path

from langchain_core.tools import tool

_POLICIES_PATH = Path(__file__).resolve().parent.parent / "data" / "policies.json"


def _load_policies() -> dict[str, dict]:
    with open(_POLICIES_PATH) as f:
        return {p["policy_number"]: p for p in json.load(f)}


_POLICIES = _load_policies()
_ticket_ids = count(1000)


@tool
def lookup_policy(policy_number: str) -> dict:
    """Look up a policy by its policy number in the policy administration
    system. Returns the policy record (holder name, type, coverage limit,
    deductible, active status), or an error dict if no such policy exists.
    """
    record = _POLICIES.get(policy_number.strip().upper())
    if record is None:
        return {"error": f"No policy found with number {policy_number!r}."}
    return record


@tool
def check_claim_history(policy_number: str) -> dict:
    """Return the claim history summary for a policy: how many prior claims
    it has and whether any were flagged for fraud review. Use this before
    deciding whether a new claim needs a risk flag.
    """
    record = _POLICIES.get(policy_number.strip().upper())
    if record is None:
        return {"error": f"No policy found with number {policy_number!r}."}
    return {
        "policy_number": policy_number,
        "prior_claims_count": record.get("prior_claims_count", 0),
        "prior_fraud_flags": record.get("prior_fraud_flags", 0),
        "policy_start_date": record.get("policy_start_date"),
    }


@tool
def create_claim_ticket(
    policy_number: str, claim_type: str, description: str, severity: str
) -> dict:
    """File a new claim ticket in the claims system and return its ticket ID
    and status. Only call this for claims that are ready to be filed, not
    ones that still need a human's review.
    """
    return {
        "ticket_id": f"CLM-{next(_ticket_ids)}",
        "policy_number": policy_number,
        "claim_type": claim_type,
        "description": description,
        "severity": severity,
        "status": "filed",
    }
