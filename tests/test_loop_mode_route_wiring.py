"""Regression checks for loop-mode wiring in chat routes."""

from pathlib import Path


def _chat_routes_source() -> str:
    return Path("routes/chat_routes.py").read_text(encoding="utf-8")


def test_chat_stream_persists_loop_mode():
    src = _chat_routes_source()
    assert "_effective_mode in ('agent', 'research', 'chat', 'loop')" in src


def test_chat_context_treats_loop_as_agentic():
    src = _chat_routes_source()
    assert 'agent_mode=(chat_mode in ("agent", "loop"))' in src


def test_agent_loop_receives_supervisor_flag_in_loop_mode():
    src = _chat_routes_source()
    assert 'supervisor_enabled=(chat_mode == "loop")' in src

