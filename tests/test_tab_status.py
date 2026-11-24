"""Behavioral tests for Zellij tab status glyphs, OSC 2 titles, config, CLI, and runner hooks."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
from pathlib import Path
from typing import Any, Sequence

import pytest

from agent_workflows import (
    agy_runipd,
    cli,
    config,
    oc_runipd,
    runner_shared,
    runner_stop,
    tab_status,
)

pytestmark = pytest.mark.core


class _FakeTTY(io.StringIO):
    """In-memory text stream claiming to be an interactive TTY."""

    def isatty(self) -> bool:
        return True


def _make_zellij_mock(
    panes: list[dict[str, Any]], tabs: list[dict[str, Any]] | None = None
):
    """Build a fake Zellij subprocess runner that records rename-tab calls and updates state."""
    calls: list[list[str]] = []
    tab_list = (
        list(tabs)
        if tabs is not None
        else [
            {
                "tab_id": p["tab_id"],
                "name": p["tab_name"],
                "active": bool(p.get("is_focused", False)),
            }
            for p in panes
            if not p.get("is_plugin")
        ]
    )

    def _run(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        cmd = list(argv)
        calls.append(cmd)
        if cmd[:4] == ["zellij", "action", "list-panes", "--tab"]:
            return subprocess.CompletedProcess(
                cmd, 0, stdout=json.dumps(panes), stderr=""
            )
        if cmd[:4] == ["zellij", "action", "list-tabs", "--all"]:
            return subprocess.CompletedProcess(
                cmd, 0, stdout=json.dumps(tab_list), stderr=""
            )
        if cmd[:4] == ["zellij", "action", "rename-tab", "--tab-id"]:
            tid = int(cmd[4])
            new_name = cmd[5]
            for p in panes:
                if p.get("tab_id") == tid:
                    p["tab_name"] = new_name
            for t in tab_list:
                if t.get("tab_id") == tid:
                    t["name"] = new_name
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="unknown")

    return _run, calls, tab_list


def test_glyph_mapping_and_stripping_idempotence() -> None:
    assert tab_status.STATE_GLYPHS == {
        "executing": "\u25b6\ufe0f",
        "rerunning": "🔄",
        "graduating": "📝",
        "reviewing": "🔍",
        "validating": "🔬",
        "waiting-deps": "⏳",
        "waiting-lock": "🔒",
        "integrating": "🧩",
        "asking": "❓",
        "paused": "\u23f8\ufe0f",
        "finished": "✅",
        "killed": "❌",
    }
    assert tab_status.ATTENTION_BADGE == "\u26a0\ufe0f"
    assert tab_status.FAILURE_BADGE == "\u26a0\ufe0f"

    # Retired legacy glyphs still strip cleanly
    assert tab_status.strip_runner_glyphs("⇄agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("🆁agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("⌕agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("▶agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("▶ agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("▶🚨agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("⏹🚨agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("⏹🚨 agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("⛒agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("▶ ⏹ agy1") == "agy1"

    # Current emoji glyphs (including variation selectors and combining attention badge) strip cleanly
    assert tab_status.strip_runner_glyphs("agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("\u25b6\ufe0f agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("\u25b6\ufe0f\u26a0\ufe0f agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("✅\u26a0\ufe0f agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("❌agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("⏳ agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("🔒 agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("🧩 agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("\u23f8\ufe0f agy1") == "agy1"
    assert tab_status.strip_runner_glyphs("  keep spaces") == "  keep spaces"

    assert (
        tab_status.format_tab_name("⏹🚨agy1", tab_status.STATE_EXECUTING)
        == "\u25b6\ufe0f agy1"
    )
    assert (
        tab_status.format_tab_name(
            "✅ agy1", tab_status.STATE_VALIDATING, has_failure=True
        )
        == "🔬\u26a0\ufe0f agy1"
    )


def test_window_title_styles() -> None:
    assert (
        tab_status.format_window_title(
            tab_status.STATE_EXECUTING, style="short", host="oc", repo_name="pubrun"
        )
        == "\u25b6\ufe0f aw"
    )
    assert (
        tab_status.format_window_title(
            tab_status.STATE_EXECUTING, style="medium", host="oc", repo_name="pubrun"
        )
        == "\u25b6\ufe0f aw pubrun"
    )
    assert (
        tab_status.format_window_title(
            tab_status.STATE_EXECUTING, style="long", host="oc", repo_name="pubrun"
        )
        == "\u25b6\ufe0f aw oc run pubrun"
    )
    assert (
        tab_status.format_window_title(
            tab_status.STATE_FINISHED,
            style="medium",
            host="agy",
            repo_name="pubrun",
            has_failure=True,
        )
        == "✅\u26a0\ufe0f aw pubrun"
    )
    assert (
        tab_status.format_window_title(
            tab_status.STATE_EXECUTING, style="none", host="oc", repo_name="pubrun"
        )
        is None
    )


def test_needs_attention_predicate_covers_failures_blocked_partial_and_questions() -> (
    None
):
    assert tab_status.queue_needs_attention({"queue": []}) is False
    assert (
        tab_status.queue_needs_attention(
            {"queue": [{"id6": "a1b2c3", "status": "executed"}]}
        )
        is False
    )
    assert (
        tab_status.queue_needs_attention(
            {"queue": [{"id6": "a1b2c3", "status": "partial"}]}
        )
        is True
    )
    assert (
        tab_status.queue_needs_attention(
            {"queue": [{"id6": "a1b2c3", "status": "blocked"}]}
        )
        is True
    )
    assert (
        tab_status.queue_needs_attention(
            {"queue": [{"id6": "a1b2c3", "status": "awaiting-human"}]}
        )
        is True
    )
    assert (
        tab_status.queue_needs_attention(
            {"queue": [{"id6": "a1b2c3", "status": "not-run", "needs_input": True}]}
        )
        is True
    )
    assert (
        tab_status.queue_needs_attention(
            {
                "queue": [
                    {
                        "id6": "a1b2c3",
                        "status": "executed",
                        "questions": [{"id": "Q1", "unanswered": True}],
                    }
                ]
            }
        )
        is True
    )
    assert (
        tab_status.queue_needs_attention(
            {
                "queue": [
                    {
                        "id6": "a1b2c3",
                        "status": "executed",
                        "questions": [{"id": "Q1", "blocking": True, "answered": True}],
                    }
                ]
            }
        )
        is False
    )
    # Multiple attention items append the badge only once
    assert (
        tab_status.format_tab_name(
            "agy1",
            tab_status.STATE_FINISHED,
            has_failure=tab_status.queue_needs_attention(
                {
                    "queue": [
                        {"id6": "a1b2c3", "status": "failed"},
                        {"id6": "d4e5f6", "status": "awaiting-human"},
                    ]
                }
            ),
        )
        == "✅\u26a0\ufe0f agy1"
    )


def test_zellij_targets_only_own_tab_strips_prior_glyphs_and_combines_failure() -> None:
    panes = [
        {"id": 0, "is_plugin": True, "tab_id": 99, "tab_name": "wrong-plugin-tab"},
        {
            "id": 0,
            "is_plugin": False,
            "tab_id": 4,
            "tab_name": "⏹🚨pubrun-work",
            "is_focused": False,
        },
        {
            "id": 1,
            "is_plugin": False,
            "tab_id": 7,
            "tab_name": "other-focused-tab",
            "is_focused": True,
        },
    ]
    mock_run, calls, tab_list = _make_zellij_mock(panes)
    tty = _FakeTTY()
    env = {"ZELLIJ_SESSION_NAME": "aw", "ZELLIJ_PANE_ID": "0"}

    ctrl = tab_status.RunnerTabStatus(
        host="agy",
        repo=Path("/tmp/pubrun"),
        title_style="medium",
        stream=tty,
        env=env,
        zellij_runner=mock_run,
    )

    assert ctrl.set_state(tab_status.STATE_EXECUTING) is True
    assert tab_list[0]["name"] == "\u25b6\ufe0f pubrun-work"
    assert tab_list[1]["name"] == "other-focused-tab"
    # Duplicate set_state is a no-op (no extra rename-tab call)
    before_calls = len(calls)
    assert ctrl.set_state(tab_status.STATE_EXECUTING) is False
    assert len(calls) == before_calls

    with ctrl.temporary(tab_status.STATE_VALIDATING):
        assert tab_list[0]["name"] == "🔬 pubrun-work"
    assert tab_list[0]["name"] == "\u25b6\ufe0f pubrun-work"

    # Attention badge combines with active state and persists through finish
    ctrl.refresh_failure({"queue": [{"id6": "a1b2c3", "status": "fail-verify"}]})
    assert tab_list[0]["name"] == "\u25b6\ufe0f\u26a0\ufe0f pubrun-work"

    with ctrl.temporary(tab_status.STATE_ASKING):
        assert tab_list[0]["name"] == "❓\u26a0\ufe0f pubrun-work"
    assert tab_list[0]["name"] == "\u25b6\ufe0f\u26a0\ufe0f pubrun-work"

    ctrl.mark_finished({"queue": [{"id6": "a1b2c3", "status": "fail-verify"}]})
    assert tab_list[0]["name"] == "✅\u26a0\ufe0f pubrun-work"
    # Never emitted OSC 2 while in Zellij
    assert tty.getvalue() == ""


def test_non_zellij_emits_osc2_and_respects_tty_and_none_style() -> None:
    tty = _FakeTTY()
    ctrl = tab_status.RunnerTabStatus(
        host="oc",
        repo=Path("/tmp/pubrun"),
        title_style="long",
        stream=tty,
        env={},
    )
    assert ctrl.set_state(tab_status.STATE_GRADUATING) is True
    assert ctrl.mark_killed(only_if_activated=True) is True
    assert (
        tty.getvalue()
        == "\x1b]2;📝 aw oc run pubrun\x1b\\\x1b]2;❌ aw oc run pubrun\x1b\\"
    )

    # Non-TTY stream emits nothing
    pipe = io.StringIO()
    ctrl_pipe = tab_status.RunnerTabStatus(
        host="oc", repo=Path("/tmp/pubrun"), title_style="medium", stream=pipe, env={}
    )
    assert ctrl_pipe.set_state(tab_status.STATE_EXECUTING) is False
    assert pipe.getvalue() == ""

    # title_style='none' suppresses both Zellij and OSC 2
    tty_none = _FakeTTY()
    ctrl_none = tab_status.RunnerTabStatus(
        host="oc", repo=Path("/tmp/pubrun"), title_style="none", stream=tty_none, env={}
    )
    assert ctrl_none.set_state(tab_status.STATE_EXECUTING) is False
    assert tty_none.getvalue() == ""


def test_config_and_cli_title_style_precedence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(config.CONFIG_DIR_ENV, str(tmp_path / "cfg"))
    tab_status.set_title_style_override(None)

    assert tuple(config.TITLE_STYLE_VALUES) == tuple(tab_status.TITLE_STYLE_VALUES)
    assert config.get_title_style() is None
    assert tab_status.resolve_title_style() == "medium"

    assert cli.main(["config", "set", "title_style", "short"]) == 0
    assert config.get_title_style() == "short"
    assert tab_status.resolve_title_style() == "short"

    # CLI override beats config
    tab_status.set_title_style_override("long")
    assert tab_status.resolve_title_style() == "long"
    tab_status.set_title_style_override(None)

    # Unset reverts to default medium
    assert cli.main(["config", "set", "title_style", "-"]) == 0
    assert config.get_title_style() is None
    assert tab_status.resolve_title_style() == "medium"

    # Invalid value rejected by config and early CLI flag
    assert cli.main(["config", "set", "title_style", "bogus"]) != 0
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rc_bad = cli.main(["--title-style", "bogus", "status"])
    assert rc_bad == 2
    assert "--title-style" in err.getvalue()


def test_reset_title_verb_and_aliases_zellij_and_terminal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 1. Under Zellij: single tab reset and --all reset
    panes = [
        {
            "id": 2,
            "is_plugin": False,
            "tab_id": 10,
            "tab_name": "⏹🚨 agy1",
            "is_focused": True,
        },
        {
            "id": 3,
            "is_plugin": False,
            "tab_id": 11,
            "tab_name": "⛒ pubrun",
            "is_focused": False,
        },
        {
            "id": 4,
            "is_plugin": False,
            "tab_id": 12,
            "tab_name": "clean-tab",
            "is_focused": False,
        },
    ]
    mock_run, _calls, tab_list = _make_zellij_mock(panes)
    monkeypatch.setenv("ZELLIJ_SESSION_NAME", "aw")
    monkeypatch.setenv("ZELLIJ_PANE_ID", "2")
    monkeypatch.setattr(tab_status, "_default_zellij_runner", mock_run)

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = cli.main(["reset-title", "--agent"])
    assert rc == 0
    rec = json.loads(out.getvalue().strip())
    assert rec["schema"] == "aw.agent/v1"
    assert rec["cmd"] == "reset-title"
    assert rec["changed"] is True
    assert tab_list[0]["name"] == "agy1"
    assert tab_list[1]["name"] == "⛒ pubrun"

    # --all clears remaining tabs with glyphs via alias clear-title
    out_all = io.StringIO()
    with contextlib.redirect_stdout(out_all):
        rc_all = cli.main(["clear-title", "--all", "--json"])
    assert rc_all == 0
    payload = json.loads(out_all.getvalue())
    assert payload["changed"] is True
    assert tab_list[1]["name"] == "pubrun"
    assert tab_list[2]["name"] == "clean-tab"

    # 2. Outside Zellij: emits OSC 2 clear to TTY
    monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
    monkeypatch.delenv("ZELLIJ_PANE_ID", raising=False)
    tty = _FakeTTY()
    res = tab_status.reset_title(stream=tty, env={})
    assert res["environment"] == "terminal"
    assert res["changed"] is True
    assert tty.getvalue() == "\x1b]2;\x1b\\"


def test_item_active_state_and_shared_hooks() -> None:
    assert (
        tab_status.item_active_state({"action": "execute"})
        == tab_status.STATE_EXECUTING
    )
    assert (
        tab_status.item_active_state({"action": "review"}) == tab_status.STATE_REVIEWING
    )
    assert (
        tab_status.item_active_state({"action": "plan"}) == tab_status.STATE_GRADUATING
    )
    assert (
        tab_status.item_active_state({"action": "execute"}, attempt_no=2)
        == tab_status.STATE_RERUNNING
    )
    assert (
        tab_status.item_active_state({"action": "review"}, recovery=True)
        == tab_status.STATE_RERUNNING
    )
    assert (
        tab_status.item_active_state(
            {"action": "execute", "requeue_from_status": "failed"}
        )
        == tab_status.STATE_RERUNNING
    )

    # resume_via_launcher temporarily switches active controller to 🔄 (rerunning)
    tty = _FakeTTY()
    observed: list[str | None] = []
    with tab_status.runner_status_session(
        host="oc", repo=Path("/tmp/demo"), title_style="short", stream=tty, env={}
    ) as ctrl:
        ctrl.set_state(tab_status.STATE_EXECUTING)
        runner_shared.resume_via_launcher(
            lambda: observed.append(ctrl.current_state), (), {}
        )
        observed.append(ctrl.current_state)
    assert observed == [tab_status.STATE_RERUNNING, tab_status.STATE_EXECUTING]
    assert (
        "\x1b]2;\u25b6\ufe0f aw\x1b\\\x1b]2;🔄 aw\x1b\\\x1b]2;\u25b6\ufe0f aw\x1b\\"
        == tty.getvalue()
    )

    # handle_interactive_interrupt temporarily switches active controller to ⏸️ (paused)
    tty_pause = _FakeTTY()
    pause_observed: list[str | None] = []
    with tab_status.runner_status_session(
        host="agy",
        repo=Path("/tmp/demo"),
        title_style="short",
        stream=tty_pause,
        env={},
    ) as ctrl:
        ctrl.set_state(tab_status.STATE_EXECUTING)
        orig_prompt = runner_stop.prompt_interrupt_action
        try:

            def _fake_prompt(*_a: Any, **_kw: Any) -> int:
                pause_observed.append(ctrl.current_state)
                return runner_stop.INTERRUPT_ACTION_RESUME

            runner_stop.prompt_interrupt_action = _fake_prompt  # type: ignore[assignment]
            res = runner_stop.handle_interactive_interrupt(stream=io.StringIO())
        finally:
            runner_stop.prompt_interrupt_action = orig_prompt  # type: ignore[assignment]
        pause_observed.append(ctrl.current_state)
    assert res == runner_stop.INTERRUPT_ACTION_RESUME
    assert pause_observed == [tab_status.STATE_PAUSED, tab_status.STATE_EXECUTING]

    # integrate_under_repository_lock with concurrent consent switches directly to 🧩 (integrating)
    tty_int = _FakeTTY()
    int_observed: list[str | None] = []
    with tab_status.runner_status_session(
        host="agy", repo=Path("/tmp/demo"), title_style="short", stream=tty_int, env={}
    ) as ctrl:
        ctrl.set_state(tab_status.STATE_EXECUTING)
        item_dict: dict[str, Any] = {"id6": "abc123"}
        ok, _msg, _kind = runner_shared.integrate_under_repository_lock(
            Path("/tmp/demo"),
            item_dict,
            None,
            state={"options": {"allow_concurrent_driver": "test"}},
            holder_label="test",
            integrate=lambda _it, _h: (
                int_observed.append(ctrl.current_state) is None,
                "ok",
                "",
            ),
        )
        assert ok is True
        int_observed.append(ctrl.current_state)
    assert int_observed == [tab_status.STATE_INTEGRATING, tab_status.STATE_EXECUTING]
    assert (
        "\x1b]2;\u25b6\ufe0f aw\x1b\\\x1b]2;🧩 aw\x1b\\\x1b]2;\u25b6\ufe0f aw\x1b\\"
        == tty_int.getvalue()
    )


def test_integration_lock_wait_and_acquire_transitions_lock_to_integrating(
    tmp_path: Path,
) -> None:
    tty_lock = _FakeTTY()
    lock_states: list[str | None] = []
    (tmp_path / ".aw" / "records" / "runs").mkdir(parents=True, exist_ok=True)
    with tab_status.runner_status_session(
        host="oc", repo=tmp_path, title_style="short", stream=tty_lock, env={}
    ) as ctrl:
        ctrl.set_state(tab_status.STATE_EXECUTING)
        item_dict: dict[str, Any] = {"id6": "abc123"}

        @contextlib.contextmanager
        def _fake_lock(*_a: Any, **_kw: Any):
            lock_states.append(ctrl.current_state)
            yield runner_shared.IntegrationLockOutcome(
                acquired=True,
                handle=None,
                holder=None,
                waited_seconds=0.0,
                detail="acquired",
            )

        orig_lock = runner_shared.integration_lock
        orig_tip = runner_shared._resolved_main_tip
        try:
            runner_shared.integration_lock = _fake_lock  # type: ignore[assignment]
            runner_shared._resolved_main_tip = lambda *_a, **_kw: "deadbeef"  # type: ignore[assignment]
            ok, _msg, _kind = runner_shared.integrate_under_repository_lock(
                tmp_path,
                item_dict,
                None,
                state={"options": {}},
                holder_label="test",
                integrate=lambda _it, _h: (
                    lock_states.append(ctrl.current_state) is None,
                    "ok",
                    "",
                ),
            )
        finally:
            runner_shared.integration_lock = orig_lock  # type: ignore[assignment]
            runner_shared._resolved_main_tip = orig_tip  # type: ignore[assignment]
        assert ok is True
        lock_states.append(ctrl.current_state)

    assert lock_states == [
        tab_status.STATE_WAITING_LOCK,
        tab_status.STATE_INTEGRATING,
        tab_status.STATE_EXECUTING,
    ]
    assert (
        "\x1b]2;\u25b6\ufe0f aw\x1b\\\x1b]2;🔒 aw\x1b\\\x1b]2;🧩 aw\x1b\\\x1b]2;\u25b6\ufe0f aw\x1b\\"
        == tty_lock.getvalue()
    )


def test_poll_for_deps_emits_waiting_deps_glyph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import argparse

    tty_poll = _FakeTTY()
    observed: list[str | None] = []
    calls = {"n": 0}

    def _fake_once(*_a: Any, **_kw: Any) -> Path:
        calls["n"] += 1
        if calls["n"] == 1:
            raise runner_shared.WaitableExternalDependencies(
                [("a1b2c3", "executed:d4e5f6", "d4e5f6", "approved")],
                "waiting",
            )
        return Path("/tmp/run-done")

    monkeypatch.setattr(runner_shared, "_initialize_run_core_once", _fake_once)

    with tab_status.runner_status_session(
        host="oc", repo=Path("/tmp/demo"), title_style="short", stream=tty_poll, env={}
    ) as ctrl:

        def _fake_sleep(_secs: float) -> None:
            observed.append(ctrl.current_state)

        ns = argparse.Namespace(poll_for_deps="5m")
        out = runner_shared.initialize_run_core(
            ns,
            host="oc",
            driver_path=None,
            host_options={},
            labels=None,
            poll_sleep_fn=_fake_sleep,
        )
        assert out == Path("/tmp/run-done")

    assert observed == [tab_status.STATE_WAITING_DEPS]
    assert "\x1b]2;⏳ aw\x1b\\" in tty_poll.getvalue()


def test_runners_expose_title_style_flag() -> None:
    import argparse

    for mod in (agy_runipd, oc_runipd):
        parser = mod.build_parser()
        sub = next(
            a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
        )
        for cmd in ("start", "resume"):
            ns = sub.choices[cmd].parse_args(
                ["--title-style", "short", "abc123"]
                if cmd == "start"
                else ["--title-style", "short", "run-123"]
            )
            assert ns.title_style == "short"


def test_transient_list_panes_timeout_retries_and_reset_title_falls_back_to_active_tab() -> (
    None
):
    assert tab_status.ZELLIJ_CMD_TIMEOUT_SECONDS >= 10.0

    panes = [
        {
            "id": 5,
            "is_plugin": False,
            "tab_id": 20,
            "tab_name": "▶ag4",
            "is_focused": True,
        }
    ]
    tabs = [{"tab_id": 20, "name": "▶ag4", "active": True}]
    mock_run, _calls, tab_list = _make_zellij_mock(panes, tabs)

    # 1. Transient failure on first list-panes call does not permanently disable RunnerTabStatus
    attempts = {"list_panes": 0}

    def _flaky_run(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        if list(argv)[:3] == ["zellij", "action", "list-panes"]:
            attempts["list_panes"] += 1
            if attempts["list_panes"] == 1:
                raise subprocess.TimeoutExpired(list(argv), 10.0)
        return mock_run(argv)

    tty = _FakeTTY()
    env = {"ZELLIJ_SESSION_NAME": "aw", "ZELLIJ_PANE_ID": "5"}
    ctrl = tab_status.RunnerTabStatus(
        host="agy",
        repo=Path("/tmp/demo"),
        title_style="medium",
        stream=tty,
        env=env,
        zellij_runner=_flaky_run,
    )
    assert ctrl.set_state(tab_status.STATE_EXECUTING) is False
    assert ctrl.set_state(tab_status.STATE_REVIEWING) is True
    assert tab_list[0]["name"] == "🔍 ag4"

    # 2. Interactive reset_title falls back to active tab when list-panes times out
    def _timeout_panes(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        if list(argv)[:3] == ["zellij", "action", "list-panes"]:
            raise subprocess.TimeoutExpired(list(argv), 10.0)
        return mock_run(argv)

    res = tab_status.reset_title(env=env, zellij_runner=_timeout_panes)
    assert res["changed"] is True
    assert res["tab_id"] == 20
    assert tab_list[0]["name"] == "ag4"

    # 3. Background RunnerTabStatus NEVER falls back to active tab when ZELLIJ_PANE_ID is missing
    ctrl_no_pane = tab_status.RunnerTabStatus(
        host="agy",
        repo=Path("/tmp/demo"),
        title_style="medium",
        stream=_FakeTTY(),
        env={"ZELLIJ_SESSION_NAME": "aw"},
        zellij_runner=mock_run,
    )
    assert ctrl_no_pane.set_state(tab_status.STATE_EXECUTING) is False
    assert tab_list[0]["name"] == "ag4"
