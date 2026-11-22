"""Behavioral tests for resuming a run with a different model or runner (IPD c9v6ie)."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from unittest import mock

import pytest

from agent_workflows import agy_runipd, oc_runipd, runner_shared

pytestmark = pytest.mark.core


def _sample_agy_state() -> dict:
    return {
        "run_id": "run-20261122T120000Z-11111",
        "driver": {
            "id": runner_shared.AGY_HOST_LABELS.id,
            "path": "/tmp/agy_runipd.py",
            "sha256": "aaa",
        },
        "session_id": "agy-ses-001",
        "set_sessions": {"demo": "agy-ses-001"},
        "session_item_count": 3,
        "options": {
            "agy_executable": "agy",
            "model": "gemini-4-neon",
            "explicit_model": "gemini-4-neon",
            "effort": "high",
            "timeout": "1800s",
            "new_session": False,
            "dangerously_skip_permissions": True,
            "no_verify": False,
            "session": "agy-ses-001",
            runner_shared.COST_ATTRIBUTION_KEY: {
                "host": "agy",
                "model": "gemini-4-neon",
                "model_source": "cli-argument",
            },
        },
        "queue": [
            {
                "position": 1,
                "id6": "aaa111",
                "setid": "demo",
                "action": "execute",
                "status": "executed",
                "attempts": [{"number": 1, "session_id": "agy-ses-001"}],
            },
            {
                "position": 2,
                "id6": "bbb222",
                "setid": "demo",
                "action": "execute",
                "status": "awaiting-human",
                "question_resume_session": "agy-ses-001",
                "preserved_branch": "aw/lane/bbb222",
                "attempts": [
                    {
                        "number": 1,
                        "session_id": "agy-ses-001",
                        "review_steps": [{"prompt": 1, "session_id": "agy-ses-001"}],
                    }
                ],
            },
        ],
    }


def _sample_oc_state() -> dict:
    return {
        "run_id": "run-20261122T120000Z-22222",
        "driver": {
            "id": runner_shared.OC_HOST_LABELS.id,
            "path": "/tmp/oc_runipd.py",
            "sha256": "bbb",
        },
        "session_id": "ses_oc_999",
        "set_sessions": {"demo": "ses_oc_999"},
        "session_item_count": 2,
        "options": {
            "opencode": "opencode",
            "model": "anthropic/claude-opus-4",
            "variant": "high",
            "agent": "build",
            "auto": True,
            "validate": True,
            "no_audit": False,
            "session": "ses_oc_999",
            "launch_profile": {
                "applied": "opus",
                "config_digest": "deadbeef",
                "provenance": {"model": "profile"},
            },
            runner_shared.COST_ATTRIBUTION_KEY: {
                "host": "oc",
                "model": "anthropic/claude-opus-4",
                "model_source": "profile",
            },
        },
        "queue": [
            {
                "position": 1,
                "id6": "ccc333",
                "setid": "demo",
                "action": "execute",
                "status": "partial",
                "question_resume_session": "ses_oc_999",
                "preserved_branch": "aw/lane/ccc333",
                "attempts": [
                    {
                        "number": 1,
                        "session_id": "ses_oc_999",
                        "review_steps": [{"prompt": 1, "session_id": "ses_oc_999"}],
                    }
                ],
            }
        ],
    }


def test_resume_parsers_accept_model_and_host_overrides_and_refuse_blank_model():
    agy_args = agy_runipd.build_parser().parse_args(
        ["resume", "run-123", "--model", "gemini-4-carbon", "--effort", "medium"]
    )
    assert agy_args.model == "gemini-4-carbon"
    assert agy_args.effort == "medium"

    agy_omitted = agy_runipd.build_parser().parse_args(["resume", "run-123"])
    assert agy_omitted.model is None
    assert agy_omitted.effort is None

    oc_args = oc_runipd.build_parser().parse_args(
        [
            "resume",
            "run-123",
            "--model",
            "openai/gpt-5",
            "--variant",
            "medium",
            "--opencode",
            "/usr/local/bin/opencode",
        ]
    )
    assert oc_args.model == "openai/gpt-5"
    assert oc_args.variant == "medium"
    assert oc_args.opencode == "/usr/local/bin/opencode"

    oc_omitted = oc_runipd.build_parser().parse_args(["resume", "run-123"])
    assert oc_omitted.model is None
    assert oc_omitted.variant is None
    assert oc_omitted.opencode is None

    for bad in ("", "   "):
        with pytest.raises(runner_shared.DriverError, match="non-empty model"):
            runner_shared.validate_resume_model_override(argparse.Namespace(model=bad))


def test_same_host_noop_and_model_switch_clear_sessions_and_preserve_launch_profile():
    # No-op on same host leaves state byte-identical.
    state = _sample_oc_state()
    before = copy.deepcopy(state)
    changed, notice = runner_shared.apply_resume_host_and_model_switch(
        state,
        argparse.Namespace(model=None, variant=None, opencode=None, session=None),
        target_host="oc",
        target_labels=runner_shared.OC_HOST_LABELS,
    )
    assert changed is False
    assert notice is None
    assert state == before

    # Explicit model + variant switch on same host clears sessions and preserves launch_profile.
    changed, notice = runner_shared.apply_resume_host_and_model_switch(
        state,
        argparse.Namespace(
            model="google/gemini-3.7-pro",
            variant="medium",
            opencode=None,
            session=None,
        ),
        target_host="oc",
        target_labels=runner_shared.OC_HOST_LABELS,
    )
    assert changed is True
    assert notice is not None and "google/gemini-3.7-pro" in notice
    assert state["options"]["model"] == "google/gemini-3.7-pro"
    assert state["options"]["variant"] == "medium"
    assert state["options"]["launch_profile"] == before["options"]["launch_profile"]
    assert (
        state["options"][runner_shared.COST_ATTRIBUTION_KEY]["model"]
        == "google/gemini-3.7-pro"
    )
    assert state["session_id"] is None
    assert state["set_sessions"] == {}
    assert state["options"]["session"] is None
    assert state["session_item_count"] == 0
    assert "question_resume_session" not in state["queue"][0]
    assert state["queue"][0]["attempts"][0]["review_steps"][0]["session_id"] is None
    assert state["queue"][0]["preserved_branch"] == "aw/lane/ccc333"
    assert len(state["resume_handoffs"]) == 1
    assert state["resume_handoffs"][0]["reason"] == "model-switch"
    assert state["resume_handoffs"][0]["sessions_cleared"] is True


def test_cross_host_handoff_agy_to_oc_and_oc_to_agy():
    # 1. agy -> oc with explicit model
    agy_state = _sample_agy_state()
    changed, notice = runner_shared.apply_resume_host_and_model_switch(
        agy_state,
        argparse.Namespace(
            model="anthropic/claude-sonnet-4",
            variant="low",
            opencode="opencode-alt",
            session=None,
        ),
        target_host="oc",
        target_labels=runner_shared.OC_HOST_LABELS,
        default_host_options={
            "opencode": "opencode",
            "auto": True,
            "variant": None,
            "agent": None,
            "validate": False,
            "no_audit": True,
        },
    )
    assert changed is True
    assert notice is not None and "agy -> oc" in notice
    assert agy_state["driver"]["id"] == runner_shared.OC_HOST_LABELS.id
    assert agy_state["options"]["model"] == "anthropic/claude-sonnet-4"
    assert agy_state["options"]["variant"] == "low"
    assert agy_state["options"]["opencode"] == "opencode-alt"
    assert agy_state["options"]["validate"] is True  # translated from no_verify=False
    assert agy_state["options"]["no_audit"] is False
    assert agy_state["session_id"] is None
    assert agy_state["set_sessions"] == {}
    assert "question_resume_session" not in agy_state["queue"][1]
    assert agy_state["queue"][1]["attempts"][0]["review_steps"][0]["session_id"] is None
    assert agy_state["queue"][1]["preserved_branch"] == "aw/lane/bbb222"
    assert agy_state["resume_handoffs"][0]["from_host"] == "agy"
    assert agy_state["resume_handoffs"][0]["to_host"] == "oc"
    assert agy_state["resume_handoffs"][0]["reason"] == "host-and-model-switch"

    # 2. oc -> agy without explicit --model falls back to agy default resolver (never leaks oc provider/model)
    oc_state = _sample_oc_state()
    changed, notice = runner_shared.apply_resume_host_and_model_switch(
        oc_state,
        argparse.Namespace(model=None, effort="medium", session=None),
        target_host="agy",
        target_labels=runner_shared.AGY_HOST_LABELS,
        default_model_resolver=lambda: ("gemini-4-default", "settings-json"),
        default_host_options={
            "agy_executable": None,
            "timeout": "1800s",
            "new_session": False,
            "dangerously_skip_permissions": True,
            "no_verify": True,
        },
    )
    assert changed is True
    assert notice is not None and "oc -> agy" in notice
    assert oc_state["driver"]["id"] == runner_shared.AGY_HOST_LABELS.id
    assert oc_state["options"]["model"] == "gemini-4-default"
    assert oc_state["options"]["explicit_model"] is None
    assert oc_state["options"]["effort"] == "medium"
    assert oc_state["options"]["no_verify"] is False  # translated from validate=True
    assert oc_state["options"]["launch_profile"]["applied"] == "opus"
    assert oc_state["session_id"] is None
    assert oc_state["set_sessions"] == {}
    assert oc_state["resume_handoffs"][0]["from_host"] == "oc"
    assert oc_state["resume_handoffs"][0]["to_host"] == "agy"
    assert oc_state["resume_handoffs"][0]["reason"] == "host-switch"


def test_driver_main_resume_end_to_end_persists_switch_and_preserves_profile_refusal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    # Prepare an agy run_dir and resume it via oc_runipd.main with --model
    run_dir = tmp_path / ".aw" / "records" / "runs" / "run-20261122T120000Z-33333"
    run_dir.mkdir(parents=True)
    (run_dir / "state.json").write_text(
        json.dumps(_sample_agy_state()), encoding="utf-8"
    )

    with (
        mock.patch.object(oc_runipd, "install_stop_triggers"),
        mock.patch.object(oc_runipd, "run_queue", return_value=0) as fake_rq,
    ):
        rc = oc_runipd.main(
            [
                "resume",
                str(run_dir),
                "--repo",
                str(tmp_path),
                "--model",
                "anthropic/claude-sonnet-4",
                "--variant",
                "high",
            ]
        )
    assert rc == 0
    assert fake_rq.called
    saved = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert saved["driver"]["id"] == runner_shared.OC_HOST_LABELS.id
    assert saved["options"]["model"] == "anthropic/claude-sonnet-4"
    assert saved["options"]["variant"] == "high"
    assert saved["session_id"] is None
    assert len(saved["resume_handoffs"]) == 1
    assert "agy -> oc" in capsys.readouterr().err

    # Now hand it back to agy_runipd.main with --model and --effort
    with (
        mock.patch.object(agy_runipd, "install_stop_triggers"),
        mock.patch.object(agy_runipd, "run_queue", return_value=0) as fake_agy_rq,
    ):
        rc2 = agy_runipd.main(
            [
                "resume",
                str(run_dir),
                "--repo",
                str(tmp_path),
                "--model",
                "gemini-4-carbon",
                "--effort",
                "low",
            ]
        )
    assert rc2 == 0
    assert fake_agy_rq.called
    saved2 = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert saved2["driver"]["id"] == runner_shared.AGY_HOST_LABELS.id
    assert saved2["options"]["model"] == "gemini-4-carbon"
    assert saved2["options"]["effort"] == "low"
    assert len(saved2["resume_handoffs"]) == 2
    assert "oc -> agy" in capsys.readouterr().err

    # Existing kgpptv refusal of --verify-with on oc_runipd resume remains intact.
    rc_bad = oc_runipd.main(
        ["resume", str(run_dir), "--repo", str(tmp_path), "--verify-with", "opus"]
    )
    assert rc_bad != 0
    assert "--verify-with" in capsys.readouterr().err
