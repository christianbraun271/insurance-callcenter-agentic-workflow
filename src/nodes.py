"""The graph's nodes. Each takes the current CallState and returns a partial
update to it, the standard LangGraph node shape. Nodes that need the LLM take
it as a keyword argument, bound in graph.py via functools.partial; nodes
that don't (verify_identity_node) take only the state.
"""

from __future__ import annotations

import json
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from .agent_loop import run_agentic_step
from .prompts import (
    ESCALATION_SYSTEM_PROMPT,
    INQUIRY_SYSTEM_PROMPT,
    INTAKE_SYSTEM_PROMPT,
    RESOLUTION_SYSTEM_PROMPT,
    TRIAGE_SYSTEM_PROMPT,
)
from .state import CallState
from .tools import check_claim_history, create_claim_ticket, lookup_policy


class IntakeExtraction(BaseModel):
    """What the intake step pulls out of the raw call transcript."""

    intent: Literal["claim", "coverage_question", "billing_question", "unknown"]
    caller_name: str | None = Field(default=None)
    policy_number: str | None = Field(default=None)
    summary: str


class TriageAssessment(BaseModel):
    """The claims-triage step's final, structured assessment."""

    claim_type: str = Field(description="e.g. collision, water damage, theft, fire, liability")
    claim_description: str
    claim_severity: Literal["low", "medium", "high"]
    risk_flags: list[str] = Field(
        default_factory=list,
        description="Reasons this claim needs human review before it's filed. Empty if none.",
    )
    reasoning: str


def intake_node(state: CallState, *, llm) -> dict:
    """Extracts intent, caller name, and policy number from the raw
    transcript. Pure extraction: no tools, just a structured-output call."""
    extraction = llm.with_structured_output(IntakeExtraction).invoke(
        [
            SystemMessage(content=INTAKE_SYSTEM_PROMPT),
            HumanMessage(content=state["call_transcript"]),
        ]
    )
    log = list(state.get("agent_log", [])) + [
        f"[intake] intent={extraction.intent!r} caller_name={extraction.caller_name!r} "
        f"policy_number={extraction.policy_number!r}"
    ]
    return {
        "intent": extraction.intent,
        "caller_name": extraction.caller_name,
        "policy_number": extraction.policy_number,
        "agent_log": log,
    }


def verify_identity_node(state: CallState) -> dict:
    """Looks up the policy intake found and checks the caller's stated name
    against the name on file. No LLM call: this is a plain lookup and string
    match, not a judgment call."""
    log = list(state.get("agent_log", []))
    policy_number = state.get("policy_number")

    if not policy_number:
        log.append("[verify_identity] no policy number captured -- cannot verify")
        return {"identity_verified": False, "policy_record": None, "agent_log": log}

    result = lookup_policy.invoke({"policy_number": policy_number})
    if "error" in result:
        log.append(f"[verify_identity] {result['error']}")
        return {"identity_verified": False, "policy_record": None, "agent_log": log}

    caller_name = (state.get("caller_name") or "").strip().lower()
    holder_name = result["policyholder_name"].strip().lower()
    verified = bool(caller_name) and (caller_name in holder_name or holder_name in caller_name)

    log.append(
        f"[verify_identity] policy {policy_number} on file for "
        f"{result['policyholder_name']!r}; caller gave {state.get('caller_name')!r} "
        f"-> verified={verified}"
    )
    return {"identity_verified": verified, "policy_record": result, "agent_log": log}


def triage_claim_node(state: CallState, *, llm) -> dict:
    """Runs the agentic loop for claims: the model checks claim history
    before deciding on claim type, severity, and any risk flags."""
    policy_record = state["policy_record"]
    assessment, trace = run_agentic_step(
        llm,
        system_prompt=TRIAGE_SYSTEM_PROMPT,
        user_prompt=(
            f"Policy on file: {json.dumps(policy_record)}\n\n"
            f"Call transcript:\n{state['call_transcript']}"
        ),
        tools=[check_claim_history],
        output_schema=TriageAssessment,
    )
    log = (
        list(state.get("agent_log", []))
        + [f"[triage_claim] {line}" for line in trace]
        + [
            f"[triage_claim] type={assessment.claim_type!r} "
            f"severity={assessment.claim_severity!r} risk_flags={assessment.risk_flags!r}"
        ]
    )
    return {
        "claim_type": assessment.claim_type,
        "claim_description": assessment.claim_description,
        "claim_severity": assessment.claim_severity,
        "risk_flags": assessment.risk_flags,
        "agent_log": log,
    }


def resolve_claim_node(state: CallState, *, llm) -> dict:
    """Files the claim that triage cleared, then asks the model for a short
    closing message confirming the ticket to the caller."""
    ticket = create_claim_ticket.invoke(
        {
            "policy_number": state["policy_number"],
            "claim_type": state["claim_type"],
            "description": state["claim_description"],
            "severity": state["claim_severity"],
        }
    )
    message = llm.invoke(
        [
            SystemMessage(content=RESOLUTION_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Ticket {ticket['ticket_id']} has been filed for a "
                    f"{state['claim_type']} claim. Write the closing message."
                )
            ),
        ]
    ).content
    log = list(state.get("agent_log", [])) + [f"[resolve_claim] filed {ticket['ticket_id']}"]
    return {"decision": "auto_resolved", "resolution_message": message, "agent_log": log}


def handle_inquiry_node(state: CallState, *, llm) -> dict:
    """Answers a coverage or billing question directly from the policy
    record already fetched by verify_identity_node."""
    message = llm.invoke(
        [
            SystemMessage(content=INQUIRY_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Policy on file: {json.dumps(state['policy_record'])}\n\n"
                    f"Caller's question:\n{state['call_transcript']}"
                )
            ),
        ]
    ).content
    log = list(state.get("agent_log", [])) + ["[handle_inquiry] answered from policy record"]
    return {"decision": "auto_resolved", "resolution_message": message, "agent_log": log}


def escalate_node(state: CallState, *, llm) -> dict:
    """Terminal node for anything not auto-resolved: works out why the call
    is being escalated, then asks the model to write a handoff brief for
    whichever human agent picks it up next."""
    if not state.get("identity_verified"):
        reason = "identity could not be verified"
    elif state.get("risk_flags"):
        reason = f"risk flags from triage: {', '.join(state['risk_flags'])}"
    else:
        reason = "intent unclear from the transcript"

    context = {
        k: v
        for k, v in state.items()
        if k not in ("call_transcript", "agent_log") and v is not None
    }
    brief = llm.invoke(
        [
            SystemMessage(content=ESCALATION_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Reason for escalation: {reason}\n\n"
                    f"Call transcript:\n{state['call_transcript']}\n\n"
                    f"State so far: {json.dumps(context, default=str)}"
                )
            ),
        ]
    ).content
    log = list(state.get("agent_log", [])) + [f"[escalate] reason={reason!r}"]
    return {"decision": "escalated", "escalation_brief": brief, "agent_log": log}
