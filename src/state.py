"""Shared state that flows through every node in the call-handling graph.

A plain TypedDict, not an Annotated/reducer-based one: every node that writes
a list field (agent_log, risk_flags) recomputes the full value itself before
returning it, so LangGraph's default "last write wins" per-key merge is all
that's needed here.
"""

from __future__ import annotations

from typing import Literal, Optional, TypedDict


class PolicyRecord(TypedDict, total=False):
    """One row from data/policies.json, as returned by lookup_policy."""

    policy_number: str
    policyholder_name: str
    policy_type: Literal["auto", "home", "health"]
    coverage_limit: float
    deductible: float
    active: bool
    policy_start_date: str
    prior_claims_count: int
    prior_fraud_flags: int


class CallState(TypedDict, total=False):
    """The state object passed between every node. Fields are grouped below
    by which node sets them first."""

    call_transcript: str

    # Set by intake_node
    caller_name: Optional[str]
    policy_number: Optional[str]
    intent: Literal["claim", "coverage_question", "billing_question", "unknown"]

    # Set by verify_identity_node
    policy_record: Optional[PolicyRecord]
    identity_verified: bool

    # Set by triage_claim_node (claims only)
    claim_type: Optional[str]
    claim_description: Optional[str]
    claim_severity: Optional[Literal["low", "medium", "high"]]
    risk_flags: list[str]

    # Set by whichever terminal node runs
    decision: Literal["auto_resolved", "escalated"]
    resolution_message: Optional[str]
    escalation_brief: Optional[str]

    # Appended to by every node, for the demo trace printed by run_demo.py
    agent_log: list[str]
