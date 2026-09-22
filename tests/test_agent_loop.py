"""Tests for run_agentic_step, the hand-rolled tool-calling-to-typed-answer
loop in src/agent_loop.py. Uses a scripted fake in place of ChatSnowflake,
so these run with no network access and no Snowflake credentials.
"""

import pytest
from langchain_core.messages import AIMessage

from src.agent_loop import run_agentic_step
from src.nodes import TriageAssessment
from src.tools import check_claim_history


class ScriptedLLM:
    """Stands in for ChatSnowflake: bind_tools() returns self, and each
    invoke() call returns the next message off a pre-scripted list."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        self.calls.append(messages)
        return self._responses.pop(0)


def test_calls_tool_then_returns_the_typed_answer():
    llm = ScriptedLLM(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "check_claim_history",
                        "args": {"policy_number": "AUTO-77410"},
                        "id": "call_1",
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "TriageAssessment",
                        "args": {
                            "claim_type": "fire",
                            "claim_description": "garage fire, total loss",
                            "claim_severity": "high",
                            "risk_flags": ["3 prior claims", "1 prior fraud flag"],
                            "reasoning": "history shows a pattern",
                        },
                        "id": "call_2",
                    }
                ],
            ),
        ]
    )

    assessment, trace = run_agentic_step(
        llm,
        system_prompt="sys",
        user_prompt="user",
        tools=[check_claim_history],
        output_schema=TriageAssessment,
    )

    assert assessment.claim_severity == "high"
    assert len(llm.calls) == 2
    assert len(trace) == 1
    assert "check_claim_history" in trace[0]


def test_skips_tools_entirely_when_the_model_answers_immediately():
    llm = ScriptedLLM(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "TriageAssessment",
                        "args": {
                            "claim_type": "collision",
                            "claim_description": "minor bumper damage",
                            "claim_severity": "low",
                            "risk_flags": [],
                            "reasoning": "clean history",
                        },
                        "id": "call_1",
                    }
                ],
            ),
        ]
    )

    assessment, trace = run_agentic_step(
        llm,
        system_prompt="sys",
        user_prompt="user",
        tools=[check_claim_history],
        output_schema=TriageAssessment,
    )

    assert assessment.claim_severity == "low"
    assert trace == []


def test_raises_if_the_model_never_calls_anything():
    llm = ScriptedLLM([AIMessage(content="I'm not sure what to do.", tool_calls=[])])

    with pytest.raises(RuntimeError, match="without calling"):
        run_agentic_step(
            llm,
            system_prompt="sys",
            user_prompt="user",
            tools=[check_claim_history],
            output_schema=TriageAssessment,
        )


def test_raises_if_the_model_never_stops_calling_tools():
    responses = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "check_claim_history",
                    "args": {"policy_number": "AUTO-77410"},
                    "id": f"call_{i}",
                }
            ],
        )
        for i in range(10)
    ]
    llm = ScriptedLLM(responses)

    with pytest.raises(RuntimeError, match="Exceeded max_tool_calls"):
        run_agentic_step(
            llm,
            system_prompt="sys",
            user_prompt="user",
            tools=[check_claim_history],
            output_schema=TriageAssessment,
            max_tool_calls=2,
        )
