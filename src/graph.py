"""Builds the LangGraph StateGraph that orchestrates one call end to end:

    START -> intake -> verify_identity -+-> triage_claim -+-> resolve_claim -> END
                                         |                 +-> escalate -> END
                                         +-> handle_inquiry -> END
                                         +-> escalate -> END

Every branch ends at either resolve_claim/handle_inquiry (auto-resolved) or
escalate (handed to a human). See README.md for what routes each call down
which path.
"""

from __future__ import annotations

from functools import partial

from langgraph.graph import END, START, StateGraph

from .nodes import (
    escalate_node,
    handle_inquiry_node,
    intake_node,
    resolve_claim_node,
    triage_claim_node,
    verify_identity_node,
)
from .state import CallState


def route_after_verification(state: CallState) -> str:
    """Where verify_identity sends the call next: escalate if the caller
    couldn't be verified, otherwise branch on intent."""
    if not state.get("identity_verified"):
        return "escalate"
    if state["intent"] == "claim":
        return "triage_claim"
    if state["intent"] in ("coverage_question", "billing_question"):
        return "handle_inquiry"
    return "escalate"


def route_after_triage(state: CallState) -> str:
    """Where triage_claim sends the call next: any risk flag means a human
    looks at it before it's filed, otherwise it's ready to resolve."""
    return "escalate" if state.get("risk_flags") else "resolve_claim"


def build_graph(llm):
    """Assembles and compiles the StateGraph described in this module's
    docstring, with every LLM-backed node bound to `llm`."""
    workflow = StateGraph(CallState)

    workflow.add_node("intake", partial(intake_node, llm=llm))
    workflow.add_node("verify_identity", verify_identity_node)
    workflow.add_node("triage_claim", partial(triage_claim_node, llm=llm))
    workflow.add_node("resolve_claim", partial(resolve_claim_node, llm=llm))
    workflow.add_node("handle_inquiry", partial(handle_inquiry_node, llm=llm))
    workflow.add_node("escalate", partial(escalate_node, llm=llm))

    workflow.add_edge(START, "intake")
    workflow.add_edge("intake", "verify_identity")
    workflow.add_conditional_edges(
        "verify_identity",
        route_after_verification,
        {
            "triage_claim": "triage_claim",
            "handle_inquiry": "handle_inquiry",
            "escalate": "escalate",
        },
    )
    workflow.add_conditional_edges(
        "triage_claim",
        route_after_triage,
        {"resolve_claim": "resolve_claim", "escalate": "escalate"},
    )
    workflow.add_edge("resolve_claim", END)
    workflow.add_edge("handle_inquiry", END)
    workflow.add_edge("escalate", END)

    return workflow.compile()
