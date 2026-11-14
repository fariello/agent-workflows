"""Operator-facing wording of three end-of-run lines (host error, integration lock, AW_HOME discard).

Each test drives the real renderer or the real lock/report function and asserts on the text an
operator reads, including the case measured on run-20261114T011406Z-590956.
"""

from __future__ import annotations

import io
import subprocess
from pathlib import Path

from agent_workflows import render_stream, runner_shared

_503 = {
    "name": "ERROR",
    "message": "API error (attempt 1): UNAVAILABLE (code 503): The service is currently unavailable.",
}


def _summary(item: dict) -> str:
    return render_stream.render_run_summary_table(
        {"run_id": "run-t", "queue": [item]}, "test"
    )


def test_host_error_after_a_merged_review_says_no_action_needed():
    item = {
        "id6": "z8hu7r",
        "action": "review",
        "status": "reviewed",
        "position": 1,
        "review_integrated": True,
        "host_error": dict(_503),
        "attempts": [
            {"exit_code": 0, "disposition": "reviewed", "host_error": dict(_503)}
        ],
    }
    summary = _summary(item)
    assert (
        "• z8hu7r: reviewed and merged. The AI service reported an error at the end of the "
        "turn, after the work was complete (API error (attempt 1): UNAVAILABLE (code 503): "
        "The service is currently unavailable.). No action needed."
    ) in summary
    assert "(host ERROR" not in summary
    assert "remedy" not in summary


def test_host_error_on_a_failed_item_says_it_failed_and_what_to_do():
    item = {
        "id6": "abc123",
        "action": "review",
        "status": "fail-gate",
        "position": 1,
        "host_error": dict(_503),
        "attempts": [{"exit_code": 1, "host_error": dict(_503)}],
    }
    summary = _summary(item)
    assert (
        "• abc123: fail-gate. The turn failed with an AI service error (API error"
        in summary
    )
    assert "→ remedy: read the session log for abc123" in summary
    assert "No action needed" not in summary


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "t@example.com"], cwd=path, check=True
    )
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True)
    (path / "f.txt").write_text("x\n")
    subprocess.run(["git", "add", "f.txt"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=path, check=True)
    (path / ".aw" / "records" / "runs").mkdir(parents=True, exist_ok=True)
    return path


def _head(repo: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def test_main_tip_is_recorded_even_when_the_injected_runner_cannot_be_called(tmp_path):
    """The measured cause of 'an unresolvable tip': the injected callable raised every time."""

    repo = _init_repo(tmp_path / "repo")
    item: dict = {}
    runner_shared.integrate_under_repository_lock(
        repo,
        item,
        object(),
        state={"run_id": "run-a"},
        holder_label="run=run-a",
        integrate=lambda _i, _h: (True, "ok", "integrated"),
        # The module-level shared function, exactly as the drivers pass it.
        run_checked=runner_shared.run_checked,
    )
    assert item["integration_serialization"]["main_tip_in_lock"] == _head(repo)


def test_waited_lock_message_is_plain_and_names_no_unresolvable_tip(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    clock = [0.0]
    messages: list[str] = []
    item: dict = {}

    def _sleep(seconds: float) -> None:
        clock[0] += seconds
        # Release the blocker partway through the wait by clearing its sidecar and lock.
        if clock[0] >= 3.0 and blocker_ctx[0] is not None:
            blocker_ctx[0].__exit__(None, None, None)
            blocker_ctx[0] = None

    blocker = runner_shared.integration_lock(repo, holder_label="blocker")
    blocker.__enter__()
    # A holder that wrote no sidecar line, as observed in the run.
    runner_shared.integration_lock_holder_path(repo).unlink()
    blocker_ctx = [blocker]
    runner_shared.integrate_under_repository_lock(
        repo,
        item,
        object(),
        state={"run_id": "run-w"},
        holder_label="run=run-w",
        integrate=lambda _i, _h: (True, "ok", "integrated"),
        progress=messages.append,
        sleep=_sleep,
        now=lambda: clock[0],
    )
    text = "\n".join(messages)
    assert "unresolvable" not in text
    assert "(bound" not in text
    assert (
        "waiting for the repository integration lock held by another process that did not "
        "record who it is (will give up after 30m and retry the merge later)"
    ) in text
    acquired = [m for m in messages if m.startswith("acquired")]
    assert len(acquired) == 1
    assert acquired[0].startswith(
        "acquired the repository integration lock after waiting "
    )
    assert "(the previous holder did not record who it was)" in acquired[0]
    assert f"merging onto main at {_head(repo)[:12]}" in acquired[0]


def test_acquired_message_omits_the_tip_when_it_could_not_be_read():
    msg = runner_shared.format_integration_lock_acquired_message(
        3.2, "run=run-x pid=1 started=now", ""
    )
    assert msg == (
        "acquired the repository integration lock after waiting 3s for run=run-x pid=1 started=now"
    )


def test_aw_home_discard_of_scratch_project_state_says_no_action_needed(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    runner_shared.append_jsonl(
        run_dir / "events.jsonl",
        {
            "event": "agent-aw-home-discarded",
            "id6": "j6o96i",
            "attempt": 1,
            "file": "projects/tmpabs9euj3-045c1a",
            "change": "added",
            "keys": ["records"],
        },
    )
    buf = io.StringIO()
    runner_shared.report_discarded_aw_home(run_dir, stream=buf)
    out = buf.getvalue()
    assert out == (
        "Discarded 1 change agents made to their private per-run AW_HOME copy (your real "
        "AW_HOME was not touched): j6o96i added projects/tmpabs9euj3-045c1a (records).\n"
        "  This is usually scratch state from tests the agent ran. No action needed.\n"
    )
