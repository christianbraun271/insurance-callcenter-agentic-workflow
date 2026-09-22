============================= test session starts ==============================
platform darwin -- Python 3.13.3, pytest-9.1.1, pluggy-1.6.0 --
cachedir: .pytest_cache
plugins: langsmith-0.7.38, anyio-4.15.1
collecting ... collected 25 items

tests/test_agent_loop.py::test_calls_tool_then_returns_the_typed_answer PASSED [  4%]
tests/test_agent_loop.py::test_skips_tools_entirely_when_the_model_answers_immediately PASSED [  8%]
tests/test_agent_loop.py::test_raises_if_the_model_never_calls_anything PASSED [ 12%]
tests/test_agent_loop.py::test_raises_if_the_model_never_stops_calling_tools PASSED [ 16%]
tests/test_graph.py::test_route_after_verification_unverified_goes_to_escalate PASSED [ 20%]
tests/test_graph.py::test_route_after_verification_claim_goes_to_triage PASSED [ 24%]
tests/test_graph.py::test_route_after_verification_question_goes_to_inquiry PASSED [ 28%]
tests/test_graph.py::test_route_after_verification_unrecognized_intent_escalates PASSED [ 32%]
tests/test_graph.py::test_route_after_triage_risk_flags_go_to_escalate PASSED [ 36%]
tests/test_graph.py::test_route_after_triage_clean_claim_resolves PASSED [ 40%]
tests/test_graph.py::test_clean_claim_gets_auto_resolved PASSED          [ 44%]
tests/test_graph.py::test_claim_with_risk_flags_gets_escalated PASSED    [ 48%]
tests/test_graph.py::test_coverage_question_resolves_without_ever_reaching_triage PASSED [ 52%]
tests/test_graph.py::test_unverifiable_caller_escalates_before_ever_reaching_triage PASSED [ 56%]
tests/test_nodes.py::test_verified_when_name_matches PASSED              [ 60%]
tests/test_nodes.py::test_not_verified_on_name_mismatch_but_record_is_still_returned PASSED [ 64%]
tests/test_nodes.py::test_not_verified_on_unknown_policy_number PASSED   [ 68%]
tests/test_nodes.py::test_not_verified_when_no_policy_number_was_captured PASSED [ 72%]
tests/test_nodes.py::test_appends_to_rather_than_replaces_the_existing_log PASSED [ 76%]
tests/test_tools.py::test_lookup_policy_found PASSED                     [ 80%]
tests/test_tools.py::test_lookup_policy_is_case_and_whitespace_insensitive PASSED [ 84%]
tests/test_tools.py::test_lookup_policy_not_found PASSED                 [ 88%]
tests/test_tools.py::test_check_claim_history_matches_the_policy_record PASSED [ 92%]
tests/test_tools.py::test_check_claim_history_not_found PASSED           [ 96%]
tests/test_tools.py::test_create_claim_ticket_ids_are_unique_and_increasing PASSED [100%]

============================== 25 passed in 0.09s ==============================
