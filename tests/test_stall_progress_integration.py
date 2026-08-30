#!/usr/bin/env python3
"""End-to-end stall behavior: progress-aware survival AND the preserved true-hang kill.

Both halves matter and are tested here together on purpose:

- THE BUG (E-03/V-03): a turn whose stdout has gone quiet while an attributable SUBAGENT is
  still working must SURVIVE. This is the regression that used to kill healthy turns.
- THE GUARANTEE (E-06/V-06): a turn making NO agent-loop progress must STILL be killed at
  the timeout, in BOTH the silent variant and the realistic NOISY variant where a
  permission-deadlocked child keeps emitting housekeeping log lines (backlog ``qyaime``).

The noisy variant is the load-bearing one. If attribution were too permissive (counting any
log line for our process), a deadlocked run would become IMMORTAL, which is strictly worse
than the original bug: a killed turn is recoverable, an immortal one is not.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from agent_workflows import oc_runipd as driver
from agent_workflows import stall_progress as sp
from tests.support import REPO_ROOT

_DRIVER_CMD = [sys.executable, "-m", "agent_workflows.oc_runipd"]

_PARENT = "ses_<redacted>parent"
_CHILD = "ses_<redacted>child"


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)


def _write_plan(repo: Path, id6: str) -> Path:
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True, exist_ok=True)
    plan = pending / f"20260829-demo-01-{id6}-test.ipd.md"
    plan.write_text(
        f"- Id: {id6}\n- Set: demo\n- Status: approved\n# Plan {id6}\n",
        encoding="utf-8",
    )
    return plan


def _run_driver(repo: Path, id6: str, child: Path, stall: str, env_extra=None):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [
            *_DRIVER_CMD,
            "start",
            id6,
            "--no-self-finalize",
            "--repo",
            os.fspath(repo),
            "--stall-timeout",
            stall,
            "--opencode",
            os.fspath(child),
        ],
        cwd=repo,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _state_of(result, repo: Path) -> dict:
    run_id = next(
        line.split(": ", 1)[1]
        for line in result.stdout.splitlines()
        if line.startswith("Run ID:")
    )
    path = repo / ".aw" / "records" / "runs" / run_id / "state.json"
    return json.loads(path.read_text(encoding="utf-8")), run_id


def _events_of(repo: Path, run_id: str) -> list[dict]:
    path = repo / ".aw" / "records" / "runs" / run_id / "events.jsonl"
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class SubagentProgressSurvivalTests(unittest.TestCase):
    """THE BUG: stdout silent + attributable subagent active => turn must SURVIVE."""

    def test_turn_with_quiet_stdout_but_active_subagent_is_not_killed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            _init_repo(repo)
            _write_plan(repo, "prog01")

            # Must be the path the observer resolves from XDG_DATA_HOME, so the driver's
            # observer and this fake child are talking about the SAME file.
            logdir = root / "opencode" / "log"
            logdir.mkdir(parents=True)
            log = logdir / "opencode.log"
            log.write_text("", encoding="utf-8")

            # A child that emits a few stdout events (so the driver learns the parent
            # session id), then goes SILENT on stdout for well past the stall timeout while
            # writing attributable agent-loop progress into opencode's log, exactly like a
            # real Task/subagent delegation.
            child = root / "subagent_opencode"
            child.write_text(
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import json, pathlib, re, sys, time
                    args = sys.argv[1:]
                    prompt = args[args.index('--') + 1] if '--' in args else ""
                    outcome = pathlib.Path(re.search(r'Required JSON outcome: (.+)', prompt).group(1).strip())
                    plan = pathlib.Path(re.search(r'Plan file at launch: (.+)', prompt).group(1).strip())
                    log = pathlib.Path({str(os.fspath(log))!r})

                    # Parent stdout: carries our session id, then falls silent.
                    print(json.dumps({{'type':'step_start','sessionID':{_PARENT!r}}}), flush=True)
                    print(json.dumps({{'type':'text','sessionID':{_PARENT!r},'part':{{'text':'delegating'}}}}), flush=True)

                    # Announce the subagent, then work inside it, emitting NO parent stdout.
                    with log.open('a') as fh:
                        fh.write('timestamp=T level=INFO run=abc message=created id={_CHILD} parentID={_PARENT} title="x (@explore subagent)"\\n')
                        fh.flush()
                    for step in range(24):
                        with log.open('a') as fh:
                            fh.write('timestamp=T level=INFO run=abc message=loop session.id={_CHILD} step=%d\\n' % step)
                            fh.write('timestamp=T level=INFO run=abc message=process session.id={_CHILD} messageID=msg_x\\n')
                            fh.flush()
                        time.sleep(0.1)

                    executed = pathlib.Path(str(plan).replace('/pending/', '/executed/'))
                    executed.parent.mkdir(parents=True, exist_ok=True)
                    plan.rename(executed)
                    outcome.write_text(json.dumps({{'schema_version':1,'id6':'prog01','disposition':'executed','pushed':False}}))
                    print(json.dumps({{'type':'text','sessionID':{_PARENT!r},'part':{{'text':'done'}}}}), flush=True)
                    """
                ),
                encoding="utf-8",
            )
            child.chmod(0o755)

            # Stall timeout (0.7s) is MUCH shorter than the stdout silence (~2.4s), so
            # without the observer the watchdog would certainly fire.
            result = _run_driver(
                repo,
                "prog01",
                child,
                "0.7",
                env_extra={"XDG_DATA_HOME": os.fspath(root)},
            )
            state, run_id = _state_of(result, repo)
            item = state["queue"][0]

            stalled = [
                e for e in _events_of(repo, run_id) if e.get("event") == "ipd-stalled"
            ]
            self.assertEqual(
                stalled,
                [],
                "a PROGRESSING turn was killed: subagent progress did not reach the watchdog",
            )
            self.assertEqual(item["status"], "executed")
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_observer_is_wired_with_the_log_from_xdg_data_home(self):
        # Guards the resolution path the integration test depends on.
        prev = os.environ.get("XDG_DATA_HOME")
        os.environ["XDG_DATA_HOME"] = "/tmp/xdg-probe"
        try:
            obs = sp.SubagentProgressObserver()
            self.assertEqual(
                obs.log_path, Path("/tmp/xdg-probe/opencode/log/opencode.log")
            )
        finally:
            if prev is None:
                del os.environ["XDG_DATA_HOME"]
            else:
                os.environ["XDG_DATA_HOME"] = prev


class TrueHangPreservationTests(unittest.TestCase):
    """THE GUARANTEE: no agent-loop progress => still killed, in BOTH hang variants."""

    def _assert_killed(self, result, repo, id6):
        state, run_id = _state_of(result, repo)
        item = state["queue"][0]
        self.assertEqual(item["status"], "interrupted")
        attempt = item["attempts"][0]
        self.assertEqual(attempt.get("interrupt_reason"), "stall_timeout")
        stalled = [
            e for e in _events_of(repo, run_id) if e.get("event") == "ipd-stalled"
        ]
        self.assertTrue(
            stalled,
            f"{id6}: a true hang was NOT killed; ipd-stalled was never recorded",
        )
        self.assertEqual(result.returncode, 1, result.stderr)

    def test_silent_hang_is_still_killed(self):
        # Variant (a): no stdout at all, and no log activity whatsoever.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            _init_repo(repo)
            _write_plan(repo, "hang01")
            (root / "opencode" / "log").mkdir(parents=True)
            (root / "opencode" / "log" / "opencode.log").write_text(
                "", encoding="utf-8"
            )

            child = root / "silent_opencode"
            child.write_text(
                "#!/usr/bin/env python3\nimport time\ntime.sleep(60)\n",
                encoding="utf-8",
            )
            child.chmod(0o755)

            result = _run_driver(
                repo,
                "hang01",
                child,
                "0.4",
                env_extra={"XDG_DATA_HOME": os.fspath(root)},
            )
            self._assert_killed(result, repo, "hang01")

    def test_noisy_permission_deadlock_is_still_killed(self):
        # Variant (b), THE LOAD-BEARING ONE (backlog qyaime): the child is stuck on an
        # unanswerable permission prompt. It emits NO stdout and NO agent-loop progress, but
        # its process KEEPS writing housekeeping lines to opencode's log. A too-permissive
        # observer would read that chatter as "progress" and make the hang immortal.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            _init_repo(repo)
            _write_plan(repo, "hang02")
            logdir = root / "opencode" / "log"
            logdir.mkdir(parents=True)
            log = logdir / "opencode.log"
            log.write_text("", encoding="utf-8")

            child = root / "noisy_opencode"
            child.write_text(
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import pathlib, time
                    log = pathlib.Path({str(os.fspath(log))!r})
                    # A real deadlocked child DOES announce a child session and then chatters.
                    with log.open('a') as fh:
                        fh.write('timestamp=T level=INFO run=abc message=created id={_CHILD} parentID={_PARENT}\\n')
                    for _ in range(200):
                        with log.open('a') as fh:
                            fh.write('timestamp=T level=INFO run=abc message=asking id=per_1 permission=external_directory patterns=["/tmp/x/*"]\\n')
                            fh.write('timestamp=T level=INFO run=abc message=evaluated permission=bash pattern="x" action.action=allow\\n')
                            fh.write('timestamp=T level=INFO run=abc message="llm runtime selected" runtime=node\\n')
                            fh.write('timestamp=T level=INFO run=abc message=tracking hash=0\\n')
                            fh.write('timestamp=T level=INFO run=abc message="resolved path" path=/tmp/x\\n')
                            fh.flush()
                        time.sleep(0.05)
                    """
                ),
                encoding="utf-8",
            )
            child.chmod(0o755)

            result = _run_driver(
                repo,
                "hang02",
                child,
                "0.5",
                env_extra={"XDG_DATA_HOME": os.fspath(root)},
            )
            self._assert_killed(result, repo, "hang02")

    def test_noisy_hang_kill_is_not_achieved_by_ignoring_the_log(self):
        # The noisy-hang test must pass for the RIGHT reason. Prove the observer really was
        # reading a log receiving that noise, and still reported no progress. If this
        # asserted nothing, variant (b) could pass merely because the observer was inert.
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "opencode.log"
            log.write_text(
                f"message=created id={_CHILD} parentID={_PARENT}\n", encoding="utf-8"
            )
            obs = sp.SubagentProgressObserver(
                parent_session_id=_PARENT, log_path=log, start_at_end=False
            )
            self.assertTrue(obs.poll() is False)
            self.assertIn(_CHILD, obs.known_children())  # the log WAS read
            with log.open("a", encoding="utf-8") as fh:
                for _ in range(50):
                    fh.write("message=asking id=per_1 permission=external_directory\n")
                    fh.write('message=evaluated permission=bash pattern="x"\n')
                    fh.write('message="llm runtime selected" runtime=node\n')
            self.assertFalse(obs.poll(), "housekeeping noise counted as progress")
            self.assertEqual(obs.progress_count, 0)
            # And a single genuine agent-loop line DOES register, proving the observer is live.
            with log.open("a", encoding="utf-8") as fh:
                fh.write(f"message=loop session.id={_CHILD} step=0\n")
            self.assertTrue(obs.poll())


class WatchdogRemainingTests(unittest.TestCase):
    """The countdown authority: `remaining()` is the watchdog's own clock."""

    class _FakeProc:
        def poll(self):
            return None

    def test_remaining_counts_down_from_the_timeout(self):
        wd = driver.StallWatchdog(self._FakeProc(), timeout=100.0)
        wd.touch()
        first = wd.remaining()
        self.assertIsNotNone(first)
        self.assertLessEqual(first, 100.0)
        import time as _t

        _t.sleep(0.05)
        second = wd.remaining()
        self.assertLess(second, first, "remaining() did not decrease")

    def test_touch_resets_remaining(self):
        wd = driver.StallWatchdog(self._FakeProc(), timeout=10.0)
        import time as _t

        _t.sleep(0.05)
        before = wd.remaining()
        wd.touch()
        self.assertGreater(wd.remaining(), before)

    def test_remaining_is_none_when_disabled(self):
        wd = driver.StallWatchdog(self._FakeProc(), timeout=0)
        self.assertFalse(wd.enabled)
        self.assertIsNone(wd.remaining())

    def test_remaining_never_negative(self):
        wd = driver.StallWatchdog(self._FakeProc(), timeout=0.01)
        import time as _t

        _t.sleep(0.05)
        self.assertGreaterEqual(wd.remaining(), 0.0)

    def test_agy_watchdog_has_the_same_accessor(self):
        from agent_workflows import agy_runipd as agy

        wd = agy.StallWatchdog(self._FakeProc(), timeout=50.0)
        self.assertIsNotNone(wd.remaining())
        self.assertIsNone(agy.StallWatchdog(self._FakeProc(), timeout=0).remaining())


if __name__ == "__main__":
    unittest.main()
