"""Integration tests: run the whole compiled graph through each of its four
branches with a scripted LLM standing in for Cortex, plus direct tests of
the two routing functions. No network access or Snowflake credentials
needed: verify_identity_node and the tools still run for real against
data/policies.json, only the LLM itself is faked.
"""

from langchain_core.messages import AIMessage

from src.graph import build_graph, route_after_triage, route_after_verification
from src.nodes import IntakeExtraction, TriageAssessment


def test_route_after_verification_unverified_goes_to_escalate():
    assert route_after_verification({"identity_verified": False}) == "escalate"


def test_route_after_verification_claim_goes_to_triage():
    state = {"identity_verified": True, "intent": "claim"}
    assert route_after_verification(state) == "triage_claim"


def test_route_after_verification_question_goes_to_inquiry():
    state = {"identity_verified": True, "intent": "billing_question"}
    assert route_after_verification(state) == "handle_inquiry"


def test_route_after_verification_unrecognized_intent_escalates():
    state = {"identity_verified": True, "intent": "unknown"}
    assert route_after_verification(state) == "escalate"


def test_route_after_triage_risk_flags_go_to_escalate():
    assert route_after_triage({"risk_flags": ["looks off"]}) == "escalate"


def test_route_after_triage_clean_claim_resolves():
    assert route_after_triage({"risk_flags": []}) == "resolve_claim"


class _Const:
    """A structured-output runnable that always returns the same value."""

    def __init__(self, value):
        self._value = value

    def invoke(self, messages):
        return self._value


class _TriageToolCaller:
    """Stands in for the bound (tools + TriageAssessment) model inside
    run_agentic_step: calls check_claim_history for real once, then returns
    the configured TriageAssessment."""

    def __init__(self, triage, policy_number):
        self._triage = triage
        self._policy_number = policy_number
        self._called_tool = False

    def invoke(self, messages):
        if not self._called_tool:
            self._called_tool = True
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "check_claim_history",
                        "args": {"policy_number": self._policy_number},
                        "id": "call_1",
                    }
                ],
            )
        return AIMessage(
            content="",
            tool_calls=[
                {"name": "TriageAssessment", "args": self._triage.model_dump(), "id": "call_2"}
            ],
        )


class GraphFakeLLM:
    """Stands in for ChatSnowflake across a full graph run: one scripted
    intake extraction, an optional scripted triage assessment (only needed
    for calls that reach triage_claim_node), and a fixed reply for every
    plain call (the closing message, the inquiry answer, the escalation
    brief)."""

    def __init__(self, intake: IntakeExtraction, triage: TriageAssessment | None = None, reply="Okay."):
        self._intake = intake
        self._triage = triage
        self._reply = reply

    def with_structured_output(self, schema):
        assert schema is IntakeExtraction
        return _Const(self._intake)

    def bind_tools(self, tools):
        return _TriageToolCaller(self._triage, self._intake.policy_number)

    def invoke(self, messages):
        return AIMessage(content=self._reply)


def _run(llm, transcript="a caller transcript"):
    app = build_graph(llm)
    return app.invoke({"call_transcript": transcript, "agent_log": [], "risk_flags": []})


def test_clean_claim_gets_auto_resolved():
    llm = GraphFakeLLM(
        intake=IntakeExtraction(
            intent="claim", caller_name="Maria Chen", policy_number="AUTO-10234", summary="a claim"
        ),
        triage=TriageAssessment(
            claim_type="collision",
            claim_description="fender bender",
            claim_severity="low",
            risk_flags=[],
            reasoning="clean history",
        ),
    )
    result = _run(llm)
    assert result["decision"] == "auto_resolved"
    assert result["resolution_message"] == "Okay."


def test_claim_with_risk_flags_gets_escalated():
    llm = GraphFakeLLM(
        intake=IntakeExtraction(
            intent="claim", caller_name="Priya Natarajan", policy_number="AUTO-77410", summary="a claim"
        ),
        triage=TriageAssessment(
            claim_type="fire",
            claim_description="garage fire, total loss",
            claim_severity="high",
            risk_flags=["3 prior claims", "1 prior fraud flag"],
            reasoning="risky history",
        ),
    )
    result = _run(llm)
    assert result["decision"] == "escalated"
    assert result["escalation_brief"] == "Okay."


def test_coverage_question_resolves_without_ever_reaching_triage():
    llm = GraphFakeLLM(
        intake=IntakeExtraction(
            intent="coverage_question",
            caller_name="David Okafor",
            policy_number="HOME-58821",
            summary="a coverage question",
        )
    )
    result = _run(llm)
    assert result["decision"] == "auto_resolved"
    assert "claim_type" not in result


def test_unverifiable_caller_escalates_before_ever_reaching_triage():
    llm = GraphFakeLLM(
        intake=IntakeExtraction(
            intent="claim", caller_name="Robert Smith", policy_number=None, summary="a claim, unverified"
        )
    )
    result = _run(llm)
    assert result["decision"] == "escalated"
    assert "claim_type" not in result
