"""Focused tests for loop-supervisor helper logic inside agent_loop.py."""

import sys
from unittest.mock import MagicMock

import pytest

# Avoid importing heavy app stack for this helper-focused test module.
for mod in [
    "sqlalchemy", "sqlalchemy.orm", "sqlalchemy.ext", "sqlalchemy.ext.declarative",
    "sqlalchemy.ext.hybrid", "sqlalchemy.sql", "sqlalchemy.sql.expression",
    "src.database",
    "src.agent_tools",
    "core.models", "core.database",
]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

from src.agent_loop import (
    _dedupe_candidates,
    _resolve_supervisor_candidates,
    _tool_result_failed,
)


def _patch_settings(monkeypatch: pytest.MonkeyPatch, values: dict):
    import src.settings as settings_mod
    monkeypatch.setattr(settings_mod, "load_settings", lambda: dict(values))
    monkeypatch.setattr(
        settings_mod,
        "get_user_setting",
        lambda key, owner="", default=None: values.get(key, default),
    )


def test_dedupe_candidates_keeps_primary_first():
    primary = ("https://a/chat/completions", "m1", {"h": "1"})
    extras = [
        ("https://a/chat/completions", "m1", {"h": "1"}),
        ("https://b/chat/completions", "m2", {"h": "2"}),
    ]
    out = _dedupe_candidates(primary, extras)
    assert out == [
        ("https://a/chat/completions", "m1", {"h": "1"}),
        ("https://b/chat/completions", "m2", {"h": "2"}),
    ]


def test_tool_result_failed_matrix():
    assert _tool_result_failed({"error": "boom"}) is True
    assert _tool_result_failed({"success": False}) is True
    assert _tool_result_failed({"exit_code": 1}) is True
    assert _tool_result_failed({"exit_code": 0}) is False
    assert _tool_result_failed({"success": True}) is False


def test_resolve_supervisor_prefers_explicit_loop_settings(monkeypatch: pytest.MonkeyPatch):
    _patch_settings(monkeypatch, {
        "loop_supervisor_endpoint_id": "sup_ep",
        "loop_supervisor_model": "sup-model",
    })
    import src.endpoint_resolver as resolver_mod
    monkeypatch.setattr(
        resolver_mod,
        "resolve_endpoint_by_id",
        lambda ep_id, model=None: ("https://sup/chat/completions", model or "sup-model", {"Authorization": "Bearer sup"})
        if ep_id == "sup_ep" else None,
    )
    monkeypatch.setattr(
        resolver_mod,
        "resolve_endpoint",
        lambda *args, **kwargs: (None, None, None),
    )

    out = _resolve_supervisor_candidates(
        worker_endpoint_url="https://worker/chat/completions",
        worker_model="worker-model",
        worker_headers={"Authorization": "Bearer w"},
        owner="alice",
    )
    assert out[0][1] == "sup-model"
    assert out[-1][1] == "worker-model"


def test_resolve_supervisor_uses_utility_if_configured(monkeypatch: pytest.MonkeyPatch):
    _patch_settings(monkeypatch, {
        "utility_endpoint_id": "util_ep",
        "utility_model": "util-model",
    })
    import src.endpoint_resolver as resolver_mod
    monkeypatch.setattr(resolver_mod, "resolve_endpoint_by_id", lambda ep_id, model=None: None)
    monkeypatch.setattr(
        resolver_mod,
        "resolve_endpoint",
        lambda prefix, owner=None: ("https://util/chat/completions", "util-model", {"Authorization": "Bearer u"})
        if prefix == "utility" else (None, None, None),
    )

    out = _resolve_supervisor_candidates(
        worker_endpoint_url="https://worker/chat/completions",
        worker_model="worker-model",
        worker_headers={"Authorization": "Bearer w"},
        owner="alice",
    )
    assert out[0][1] == "util-model"
    assert out[-1][1] == "worker-model"


def test_resolve_supervisor_falls_back_to_worker(monkeypatch: pytest.MonkeyPatch):
    _patch_settings(monkeypatch, {})
    import src.endpoint_resolver as resolver_mod
    monkeypatch.setattr(resolver_mod, "resolve_endpoint_by_id", lambda ep_id, model=None: None)
    monkeypatch.setattr(resolver_mod, "resolve_endpoint", lambda *args, **kwargs: (None, None, None))

    out = _resolve_supervisor_candidates(
        worker_endpoint_url="https://worker/chat/completions",
        worker_model="worker-model",
        worker_headers={"Authorization": "Bearer w"},
        owner="alice",
    )
    assert out == [("https://worker/chat/completions", "worker-model", {"Authorization": "Bearer w"})]

