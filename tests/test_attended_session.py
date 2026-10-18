#!/usr/bin/env python3
"""Attended plans open an interactive agent session instead of four manual steps (backlog `rfofos`).

Behavioral: drives `aw work begin`, the runners' queue freeze (`start --prepare-only`), the resume
re-mark, and a full attended turn through each host's real `execute_item`, using a fake agent binary
that records how it was launched. A terminal is simulated by patching `term.is_interactive`, the one
predicate both entry points consult.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from agent_workflows import (
    agy_runipd,
    attended_session,
    cli,
    oc_runipd,
    runner_shared,
    term,
)
from tests import support
from tests.support import coordinator_role


def _fake_agent(tmp_path: Path) -> Path:
    """A fake interactive agent: records argv, cwd and env, and acts on a runner prompt if given."""

    return support.make_fake_executable(
        tmp_path / "fake_agent",
        """#!/usr/bin/env python3
import json, os, re, sys
from pathlib import Path
rec = {"argv": sys.argv[1:], "cwd": os.getcwd(),
       "run_id": os.environ.get("AW_RUN_ID"), "id6": os.environ.get("AW_ITEM_ID6")}
Path(os.environ["FAKE_RECORD"]).write_text(json.dumps(rec), encoding="utf-8")
text = " ".join(sys.argv[1:])
m = re.search(r"The full runner prompt is in (\\S+?)\\.?$", text)
if m and Path(m.group(1)).is_file():
    prompt = Path(m.group(1)).read_text(encoding="utf-8")
    out = re.search(r"Required JSON outcome: (\\S+)", prompt)
    if out:
        p = Path(out.group(1)); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(os.environ.get("FAKE_PAYLOAD_JSON", "{}"), encoding="utf-8")
    plan = re.search(r"Plan file at launch: (\\S+)", prompt)
    payload = json.loads(os.environ.get("FAKE_PAYLOAD_JSON", "{}"))
    if plan and payload.get("disposition") == "executed":
        pf = Path(plan.group(1))
        if pf.is_file() and "pending" in pf.parts:
            dest = pf.parent.parent / "executed"; dest.mkdir(parents=True, exist_ok=True)
            pf.rename(dest / pf.name)
sys.exit(int(os.environ.get("FAKE_EXIT", "0")))
""",
    )


def _attended_repo(tmp_path: Path, *, with_dependent: bool = False) -> Path:
    from tests.test_freeze_time_refusal import _init_repo, _write_plan

    repo = _init_repo(tmp_path)
    att = _write_plan(repo, "att004", order=1)
    att.write_text(
        att.read_text(encoding="utf-8").replace(
            "- Id: att004\n", "- Id: att004\n- Attended: required\n"
        ),
        encoding="utf-8",
    )
    if with_dependent:
        _write_plan(repo, "dep005", order=2, dependencies=["executed:att004"])
    else:
        _write_plan(repo, "pln005", order=2)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "plans"], cwd=repo, check=True)
    return repo


# --- the argv builder --------------------------------------------------------------------------------


def test_interactive_argv_per_host(tmp_path: Path) -> None:
    wd = tmp_path
    assert attended_session.build_interactive_argv(
        "opencode", workdir=wd, prompt="go", model="m/x", agent="build"
    ) == ["opencode", str(wd), "--prompt", "go", "--model", "m/x", "--agent", "build"]
    assert attended_session.build_interactive_argv(
        "claude", workdir=wd, prompt="go", model="opus"
    ) == ["claude", "--model", "opus", "go"]
    assert attended_session.build_interactive_argv(
        "agy", workdir=wd, prompt="go", model="Gemini", variant="high"
    ) == ["agy", "--prompt-interactive", "go", "--model", "Gemini", "--effort", "high"]
    # Runner ids map to their host.
    assert (
        attended_session.build_interactive_argv("oc", workdir=wd, prompt="go")[0]
        == "opencode"
    )
    with pytest.raises(ValueError):
        attended_session.build_interactive_argv("nope", workdir=wd, prompt="go")


def test_execute_prompt_names_plan_and_outcome() -> None:
    p = attended_session.execute_prompt("abc123")
    assert "Execute plan abc123" in p and "/askme" in p
    r = attended_session.execute_prompt("abc123", outcome_path="/x/out.json")
    assert "/x/out.json" in r and "run continues" in r


# --- aw work begin ------------------------------------------------------------------------------------


def _work_begin(
    repo: Path, extra: list[str], *, interactive: bool, record: Path
) -> tuple[int, str]:
    buf = io.StringIO()
    with mock.patch.object(
        term, "is_interactive", return_value=interactive
    ), mock.patch.dict(os.environ, {"FAKE_RECORD": str(record)}), redirect_stdout(buf):
        rc = cli.main(["work", "begin", "att004", "--dir", str(repo), *extra])
    return rc, buf.getvalue()


def test_work_begin_opens_the_session_in_the_worktree(tmp_path: Path) -> None:
    repo = _attended_repo(tmp_path)
    fake = _fake_agent(tmp_path)
    record = tmp_path / "rec.json"
    rc, out = _work_begin(
        repo,
        ["--host", "opencode", "--host-bin", str(fake)],
        interactive=True,
        record=record,
    )
    assert rc == 0, out
    rec = json.loads(record.read_text(encoding="utf-8"))
    worktree = repo / ".aw" / "worktrees" / "att004"
    assert Path(rec["cwd"]).resolve() == worktree.resolve()
    assert Path(rec["argv"][0]).resolve() == worktree.resolve()
    assert rec["argv"][1] == "--prompt" and "Execute plan att004" in rec["argv"][2]
    assert "session ended (exit 0)" in out


def test_work_begin_without_a_terminal_prints_the_command(tmp_path: Path) -> None:
    repo = _attended_repo(tmp_path)
    fake = _fake_agent(tmp_path)
    record = tmp_path / "rec.json"
    rc, out = _work_begin(
        repo,
        ["--host", "claude", "--host-bin", str(fake)],
        interactive=False,
        record=record,
    )
    assert rc == 0
    assert not record.exists()
    assert "to execute it, run: cd " in out and "Execute plan att004" in out


def test_work_begin_no_session_opens_nothing(tmp_path: Path) -> None:
    repo = _attended_repo(tmp_path)
    fake = _fake_agent(tmp_path)
    record = tmp_path / "rec.json"
    rc, out = _work_begin(
        repo, ["--no-session", "--host-bin", str(fake)], interactive=True, record=record
    )
    assert rc == 0 and not record.exists()
    assert "allocated worktree" in out


# --- the runners: queue freeze ------------------------------------------------------------------------


def _freeze(
    module: Any, repo: Path, ids: list[str], *, interactive: bool, extra: list[str] = ()
) -> dict:
    args = module.build_parser().parse_args(
        ["start", *ids, "--prepare-only", "--repo", str(repo), *extra]
    )
    with mock.patch.object(term, "is_interactive", return_value=interactive):
        run_dir = Path(module.initialize_run(args))
    return json.loads((run_dir / "state.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("module", [oc_runipd, agy_runipd], ids=["oc", "agy"])
def test_at_a_terminal_the_attended_plan_stays_queued_and_marked(
    tmp_path: Path, module: Any
) -> None:
    repo = _attended_repo(tmp_path, with_dependent=True)
    # A dependent of the attended plan no longer refuses the whole run at a terminal.
    state = _freeze(module, repo, ["att004", "dep005"], interactive=True)
    by = {e["id6"]: e for e in state["queue"]}
    assert by["att004"]["status"] == "queued"
    assert by["att004"][runner_shared.ATTENDED_KEY] is True
    assert not by["att004"].get(runner_shared.NEEDS_INPUT_KEY)
    assert by["dep005"]["status"] == "queued"


@pytest.mark.parametrize("module", [oc_runipd, agy_runipd], ids=["oc", "agy"])
def test_unattended_still_holds_it_without_spending_a_turn(
    tmp_path: Path, module: Any
) -> None:
    repo = _attended_repo(tmp_path)
    for interactive, extra in ((False, []), (True, ["--unattended"])):
        state = _freeze(
            module, repo, ["att004", "pln005"], interactive=interactive, extra=extra
        )
        by = {e["id6"]: e for e in state["queue"]}
        assert by["att004"]["status"] == "not-run", extra
        assert by["att004"]["refusal"]["code"] == runner_shared.ATTENDED_REQUIRED_CODE
        assert "interactive session" in by["att004"]["refusal"]["remedy"]


def test_dispatch_time_check_holds_when_the_terminal_is_gone(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    item: dict[str, Any] = {
        "id6": "att004",
        "action": "execute",
        "status": "queued",
        runner_shared.ATTENDED_KEY: True,
    }
    state: dict[str, Any] = {"options": {}, "queue": [item]}
    with mock.patch.object(term, "is_interactive", return_value=False):
        held = runner_shared.hold_attended_if_unattended(
            run_dir,
            state,
            item,
            save_state=lambda *a: None,
            append_jsonl=runner_shared.append_jsonl,
        )
    assert held and item["status"] == "not-run"
    assert item["refusal"]["code"] == runner_shared.ATTENDED_REQUIRED_CODE
    assert "attended-held" in (run_dir / "events.jsonl").read_text(encoding="utf-8")
    # At a terminal it is left for the interactive session.
    item2: dict[str, Any] = {
        "id6": "x",
        "action": "execute",
        "status": "queued",
        runner_shared.ATTENDED_KEY: True,
    }
    with mock.patch.object(term, "is_interactive", return_value=True):
        assert not runner_shared.hold_attended_if_unattended(
            run_dir,
            state,
            item2,
            save_state=lambda *a: None,
            append_jsonl=runner_shared.append_jsonl,
        )


def test_resume_requeue_re_marks_a_held_attended_item() -> None:
    item: dict[str, Any] = {"id6": "a", "status": "not-run"}
    runner_shared._freeze_attended_hold(item)
    runner_shared.remark_attended_on_requeue(item)
    assert item[runner_shared.ATTENDED_KEY] is True
    other: dict[str, Any] = {"id6": "b", "status": "not-run"}
    runner_shared.remark_attended_on_requeue(other)
    assert runner_shared.ATTENDED_KEY not in other


# --- the runners: the attended turn itself -----------------------------------------------------------


@pytest.mark.parametrize("runner_name", ["oc", "agy"])
def test_attended_turn_runs_interactively_and_is_scored_normally(
    tmp_path: Path, runner_name: str
) -> None:
    from tests.test_run_proposal_channel import _create_plan_file, _create_test_repo

    repo = _create_test_repo(tmp_path)
    plan_file = _create_plan_file(repo, "att009")
    fake = _fake_agent(tmp_path)
    record = tmp_path / "rec.json"
    run_dir = repo / ".aw" / "records" / "runs" / f"run-attended-{runner_name}"
    for sub in ("outcomes", "prompts"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    item: dict[str, Any] = {
        "id6": "att009",
        "setid": "testset",
        "position": 1,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_file),
        "attempts": [],
        runner_shared.ATTENDED_KEY: True,
    }
    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": f"run-attended-{runner_name}",
        "queue": [item],
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": False,
            "output_mode": "quiet",
        },
    }
    module = oc_runipd if runner_name == "oc" else agy_runipd
    state["options"]["opencode" if runner_name == "oc" else "agy"] = str(fake)
    payload = {
        "disposition": "executed",
        "defect_report": {"state": "none-found", "findings": []},
        "pushed": False,
    }
    with mock.patch.dict(
        os.environ,
        {"FAKE_RECORD": str(record), "FAKE_PAYLOAD_JSON": json.dumps(payload)},
    ), coordinator_role():
        module.execute_item(run_dir, state, item, recovery=False)

    rec = json.loads(record.read_text(encoding="utf-8"))
    # Launched in its INTERACTIVE form, not the headless one.
    if runner_name == "oc":
        assert rec["argv"][1] == "--prompt" and "run" not in rec["argv"][:1]
    else:
        assert rec["argv"][0] == "--prompt-interactive" and "-p" not in rec["argv"]
    assert "Execute plan att009" in " ".join(rec["argv"])
    assert rec["id6"] == "att009"
    # Scored by the normal post-turn path from the outcome the session wrote.
    assert item["status"] == "executed", item.get("refusal")
    events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
    assert "attended-session-start" in events and "attended-session-end" in events
