"""Snowflake Cortex LLM client, shared by every node that needs one.

Cortex's llama3.1-70b does not support tool calling (Snowflake rejects
tool-bound requests for it outright), so anything in this project that binds
tools or asks for structured output -- which is implemented as tool calling
under the hood -- runs on claude-3-5-sonnet instead, which Snowflake
documents as tool-calling capable.
"""

from __future__ import annotations

import os

from langchain_snowflake import ChatSnowflake, create_session_from_pat

MODEL_NAME = "claude-sonnet-5"


def get_llm(temperature: float = 0.0) -> ChatSnowflake:
    session = create_session_from_pat()
    session.use_warehouse(os.environ["SNOWFLAKE_WAREHOUSE"])
    return ChatSnowflake(model=MODEL_NAME, temperature=temperature, session=session)
