"""Unit tests for src/loop_supervisor.py."""

from src.loop_supervisor import (
    should_intervene,
    build_supervisor_prompt,
    parse_supervisor_decision,
)


class TestShouldIntervene:
    def test_tool_failure_streak_triggers(self):
        yes, reason = should_intervene({"tool_failure_streak": 2})
        assert yes is True
        assert reason == "tool_failure_streak"

    def test_no_progress_streak_triggers(self):
        yes, reason = should_intervene({"no_progress_streak": 3})
        assert yes is True
        assert reason == "no_progress_streak"

    def test_stream_error_without_output_triggers(self):
        yes, reason = should_intervene({"stream_error_no_output": True})
        assert yes is True
        assert reason == "stream_error_no_output"

    def test_normal_progress_does_not_trigger(self):
        yes, reason = should_intervene({
            "tool_failure_streak": 0,
            "no_progress_streak": 0,
            "loop_breaker_proximity": False,
            "stream_error_no_output": False,
        })
        assert yes is False
        assert reason == ""


class TestParseSupervisorDecision:
    def test_parses_inject_instruction(self):
        d = parse_supervisor_decision('{"action":"inject_instruction","reason":"stuck","instruction":"Use manage_notes"}')
        assert d["action"] == "inject_instruction"
        assert d["instruction"] == "Use manage_notes"
        assert d["reason"] == "stuck"

    def test_parses_switch_candidate_index(self):
        d = parse_supervisor_decision('{"action":"switch_candidate","candidate_index":1,"reason":"fallback"}')
        assert d["action"] == "switch_candidate"
        assert d["candidate_index"] == 1

    def test_malformed_json_falls_back_to_none(self):
        d = parse_supervisor_decision("{not-json")
        assert d["action"] == "none"
        assert d["candidate_index"] is None

    def test_extracts_json_inside_think_tags(self):
        raw = "<think>internal</think>\n{\"action\":\"switch_candidate\",\"candidate_index\":\"2\"}"
        d = parse_supervisor_decision(raw)
        assert d["action"] == "switch_candidate"
        assert d["candidate_index"] == 2

    def test_missing_required_fields_downgrades_to_none(self):
        d = parse_supervisor_decision('{"action":"switch_candidate"}')
        assert d["action"] == "none"


def test_build_prompt_contains_snapshot_and_candidates():
    prompt = build_supervisor_prompt(
        {"round": 2, "tool_failure_streak": 2},
        [{"index": 0, "model": "m1", "endpoint": "u1"}],
    )
    assert "tool_failure_streak" in prompt
    assert "m1" in prompt
    assert "JSON schema" in prompt

