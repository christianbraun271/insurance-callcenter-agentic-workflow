"""A small reusable tool-calling loop for steps that need to reason with
tools *and* end in a typed result, not free text.

langgraph.prebuilt's ToolNode + tools_condition (see the arithmetic-agent
examples this project's sibling folder, langgraph-learning, builds up) is the
right fit for an open-ended chat loop. It doesn't fit here, because each of
these steps has to end with one specific, structured answer. So the "final
answer" is modeled as one more tool the model can call, and the loop stops
the moment that one is called.
"""

from __future__ import annotations

from typing import Type, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def run_agentic_step(
    llm,
    *,
    system_prompt: str,
    user_prompt: str,
    tools: list[BaseTool],
    output_schema: Type[T],
    max_tool_calls: int = 4,
) -> tuple[T, list[str]]:
    """Runs `llm` in a loop: on each turn it may call any of `tools`, and
    must eventually call `output_schema` to produce its final, typed answer.

    Returns (parsed_answer, trace). trace is a list of human-readable
    strings describing each tool call made, for the demo's printed log.
    """
    bound_llm = llm.bind_tools([*tools, output_schema])
    tools_by_name = {t.name: t for t in tools}
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    trace: list[str] = []

    for _ in range(max_tool_calls + 1):
        response = bound_llm.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            raise RuntimeError(
                f"Model responded without calling {output_schema.__name__} or a "
                f"tool. Got: {response.content!r}"
            )

        final_call = next(
            (c for c in response.tool_calls if c["name"] == output_schema.__name__),
            None,
        )
        if final_call is not None:
            return output_schema(**final_call["args"]), trace

        for call in response.tool_calls:
            called_tool = tools_by_name.get(call["name"])
            if called_tool is None:
                result = {"error": f"Unknown tool {call['name']!r}"}
            else:
                result = called_tool.invoke(call["args"])
                trace.append(f"called {call['name']}({call['args']}) -> {result}")
            messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))

    raise RuntimeError(
        f"Exceeded max_tool_calls={max_tool_calls} without a final "
        f"{output_schema.__name__} answer."
    )
