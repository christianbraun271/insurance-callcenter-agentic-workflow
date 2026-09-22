# Insurance Call Center Agentic Workflow

**Remark: This is an anonymized excerpt, which is based on a real-world prototype
that served as foundation for a production-grade project. The production-grade project
is under NDA and cannot be shared.**

A LangGraph multi-agent workflow that takes a raw call transcript from an
insurance call center and carries it end to end: understand what the caller
wants, verify who they are, triage a claim if there is one, and either
resolve the call automatically or hand it to a human agent with a written
briefing.

**Technical Stack: LangGraph as Agentic Workflow, Snowflake as LLM provider, 
claude-sonnet-5 as LLM, tool calling implemented via structured JSON-parsing**

## The idea

A call center handles a few repeatable shapes of call: file a claim, ask a
coverage question, ask a billing question. Each one still needs a
person to verify the caller, pull up the right record, and judge whether
anything about it needs a closer look. This project automates that judgment
as a graph of small, focused steps, each backed by a real LLM call or a real
tool call, with a human agent only brought in for the calls that actually
need one.

```
intake  -->  verify_identity
                 |
                 +-- not verified ------------------------> escalate --> END
                 |
                 +-- coverage / billing question --> handle_inquiry --> END
                 |
                 +-- claim --> triage_claim
                                   |
                                   +-- risk flags found --> escalate --> END
                                   |
                                   +-- clean --------------> resolve_claim --> END
```

Every branch ends one of two ways: **auto-resolved** (the caller gets an
answer or a filed claim, no human involved) or **escalated** (a human agent
gets a written handoff brief explaining why). See
[`src/graph.py`](src/graph.py) for the actual routing logic.

## How it works

- **Intake**: the model reads the raw transcript and extracts intent,
  caller name, and policy number as a typed (Pydantic) result via
  `with_structured_output`. No tools involved; this is a pure extraction
  step.
- **Verify identity**: a deterministic step (no LLM judgment call needed
  here). Look up the policy by number, compare the caller's stated name
  against the name on file. Unverifiable calls go straight to a human.
- **Triage claim** *(claims only)*: the model is given the policy on file
  and the transcript, and is expected to call a `check_claim_history` tool
  before producing its final assessment (claim type, severity, and any risk
  flags). This step uses a small hand-rolled agentic loop
  ([`src/agent_loop.py`](src/agent_loop.py)): the model can call tools freely,
  but must eventually call a schema-shaped "final answer" tool to end the
  turn. That's the same idea behind LangGraph's `ToolNode` / `tools_condition`
  pattern, adapted for a step that has to end in a typed result rather than
  free text.
- **Resolve or escalate**: a clean claim gets filed (`create_claim_ticket`)
  and a short confirmation message is generated for the caller. A claim
  with risk flags, a coverage/billing question, or a call that couldn't be
  verified all end at the same `escalate` node, which writes a short brief
  for the human agent picking it up.

## Repository structure

```
src/
  state.py          Shared state (TypedDict) passed between every node
  llm.py             Snowflake Cortex client setup
  tools.py            lookup_policy / check_claim_history / create_claim_ticket
  agent_loop.py        The reusable tool-calling-to-typed-answer loop
  prompts.py            System prompts for each node
  nodes.py                The node functions themselves
  graph.py                 Wires the nodes into a LangGraph StateGraph
data/
  policies.json      A small synthetic book of business (4 fictional policies)
sample_calls/
  *.txt              Four transcripts, one per branch through the graph
tests/
  test_tools.py      lookup_policy / check_claim_history / create_claim_ticket
  test_agent_loop.py The tool-calling loop, including its two failure modes
  test_nodes.py      verify_identity_node's branches (the one node with no LLM call)
  test_graph.py      Routing functions, plus a full graph run for each of the four branches
docs/
  sample_run.md      A real run's output, captured with `python run_demo.py`
run_demo.py          Runs the sample calls and prints each one's trace
```

## Running it

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your Snowflake account details
python run_demo.py
```

Pass one or more filenames to run just those calls, e.g.
`python run_demo.py call_3_suspicious_claim.txt`.

## Testing

```bash
pytest
```

The test suite doesn't need a Snowflake connection: `test_agent_loop.py` and
`test_graph.py` swap in a small scripted stand-in for `ChatSnowflake` (see
`ScriptedLLM` / `GraphFakeLLM` in those files), while `test_tools.py` and
`test_nodes.py` run for real against the synthetic `data/policies.json`,
since those have no LLM call to fake in the first place.
`test_graph.py` builds the actual compiled graph from `src/graph.py` and
runs it end to end for each of the four branches described above, so it's
exercising the real routing logic, not a re-implementation of it.

### What you need

- A Snowflake account with **Cortex** enabled, and a warehouse to run on.
- A programmatic access token (PAT): `create_session_from_pat()` in
  `src/llm.py` authenticates with the `SNOWFLAKE_PAT` env var, the same
  pattern as this repo's LangGraph learning exercises.
- **The model matters here, but only for one step.** Cortex's `llama3.1-70b`
  does not support tool calling (it rejects tool-bound requests outright),
  so `triage_claim_node` (the one step that binds a real tool via
  `bind_tools`) needs a model that does. This project runs on
  `claude-sonnet-5` everywhere, for simplicity, even though `intake_node`'s
  `with_structured_output` call doesn't actually need that:
  `langchain_snowflake` implements it as a JSON-schema instruction injected
  into the prompt and parsed back out of the response text, not real
  function calling.

### The four sample calls

| File | What happens |
|---|---|
| `call_1_simple_auto_claim.txt` | Verified caller, clean history → claim filed, call auto-resolved |
| `call_2_coverage_question.txt` | Verified caller, no claim → answered from the policy record |
| `call_3_suspicious_claim.txt` | Verified caller, but claim history shows prior claims and a fraud flag → escalated with a handoff brief |
| `call_4_unverifiable_caller.txt` | Caller can't give a valid policy number → escalated, identity unverified |

## Scope

All policy data is synthetic: four fictional policyholders, invented policy
numbers, no real insurer's data or systems. This is a demonstration of the
workflow pattern (detect intent → verify → triage → route to automation or a
human), not a production call-handling system: there's no telephony
integration, no persistence beyond the in-memory mock policy store, and no
retry/observability layer.

## Future work

This is an initial prototype covering the reasoning core of a call-handling
agent, not a deployable call center system. It currently runs on written
transcripts as input. The natural next step is closing that gap with real
voice, on both ends of the call:

- **Speech-to-text**, to turn a live caller's audio into the transcript this
  graph already consumes.
- **Text-to-speech**, to turn `resolution_message` back into audio the
  caller actually hears.
- **A telephony API** (e.g. Twilio), to put the whole thing on an actual
  phone line instead of reading `.txt` files from disk.

None of that changes the graph itself. `state.py`'s `call_transcript` field
is exactly what a speech-to-text transcript would look like, and
`resolution_message` is exactly what a text-to-speech step would read
aloud, so the orchestration layer built here should carry over largely
unchanged.

## License

No license is included, which means all rights are reserved. This
repository is shared to demonstrate the approach and the code, not as
something to be copied, modified, or reused.
