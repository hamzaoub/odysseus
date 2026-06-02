"""Supervisor helpers for loop mode.

Pure, side-effect-light logic used by agent_loop's optional loop supervisor.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple


_ACTIONS = {"none", "inject_instruction", "switch_candidate"}


def should_intervene(snapshot: Dict[str, Any]) -> Tuple[bool, str]:
    """Return (should_intervene, reason) from a lightweight round snapshot."""
    if snapshot.get("stream_error_no_output"):
        return True, "stream_error_no_output"
    if int(snapshot.get("tool_failure_streak") or 0) >= 2:
        return True, "tool_failure_streak"
    if int(snapshot.get("no_progress_streak") or 0) >= 3:
        return True, "no_progress_streak"
    if snapshot.get("loop_breaker_proximity"):
        return True, "loop_breaker_proximity"
    return False, ""


def build_supervisor_prompt(snapshot: Dict[str, Any], candidates: List[Dict[str, Any]]) -> str:
    """Build the supervisor prompt with strict JSON response requirements."""
    return (
        "You are the loop supervisor for a worker agent.\n"
        "Intervene only when needed. Choose exactly one action.\n\n"
        f"Round snapshot:\n{json.dumps(snapshot, ensure_ascii=True)}\n\n"
        f"Runtime candidates:\n{json.dumps(candidates, ensure_ascii=True)}\n\n"
        "Rules:\n"
        "- Prefer action=none unless intervention is clearly needed.\n"
        "- inject_instruction: short, concrete steering instruction for next round.\n"
        "- switch_candidate: choose candidate_index from the provided list only.\n"
        "- Never ask for human input.\n"
        "- Output JSON only.\n\n"
        "JSON schema:\n"
        "{"
        "\"action\":\"none|inject_instruction|switch_candidate\","
        "\"reason\":\"short reason\","
        "\"instruction\":\"string (required only for inject_instruction)\","
        "\"candidate_index\":0"
        "}"
    )


def parse_supervisor_decision(json_text: str) -> Dict[str, Any]:
    """Parse supervisor JSON robustly and normalize into a safe decision dict."""
    raw = (json_text or "").strip()
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL | re.IGNORECASE).strip()

    data: Dict[str, Any] = {}
    if raw:
        try:
            data = json.loads(raw)
        except Exception:
            m = re.search(r"\{[\s\S]*\}", raw)
            if m:
                try:
                    data = json.loads(m.group(0))
                except Exception:
                    data = {}

    action = str(data.get("action") or "none").strip().lower()
    if action not in _ACTIONS:
        action = "none"

    reason = str(data.get("reason") or "").strip()
    instruction = str(data.get("instruction") or "").strip()

    candidate_index = data.get("candidate_index")
    if isinstance(candidate_index, bool):  # bool is an int subclass in python
        candidate_index = None
    if isinstance(candidate_index, (int, float)):
        candidate_index = int(candidate_index)
    else:
        try:
            candidate_index = int(str(candidate_index).strip())
        except Exception:
            candidate_index = None
    if candidate_index is not None and candidate_index < 0:
        candidate_index = None

    if action == "inject_instruction" and not instruction:
        action = "none"
    if action == "switch_candidate" and candidate_index is None:
        action = "none"

    return {
        "action": action,
        "reason": reason,
        "instruction": instruction,
        "candidate_index": candidate_index,
    }

