"""Tests for ui_control mode handling."""

import asyncio

from src.ai_interaction import do_ui_control


def test_set_mode_accepts_loop():
    out = asyncio.run(do_ui_control("set_mode loop"))
    assert out.get("ui_event") == "set_mode"
    assert out.get("mode") == "loop"


def test_set_mode_accepts_agent_and_chat():
    out_agent = asyncio.run(do_ui_control("set_mode agent"))
    out_chat = asyncio.run(do_ui_control("set_mode chat"))
    assert out_agent.get("mode") == "agent"
    assert out_chat.get("mode") == "chat"


def test_set_mode_rejects_invalid_value():
    out = asyncio.run(do_ui_control("set_mode not-a-mode"))
    assert "error" in out
    assert "agent, loop, chat" in out["error"]

