"""Tests for runstale Order 01 (ssk6nf): read-time liveness projection in `aw runs`.

The defect: `oc_runipd.reconcile_interrupted` is reached ONLY from `run_queue` (a resume), so a run
killed without a chance to write (SIGKILL, OOM, crash, suspend) keeps claiming `running` forever and
every read path trusts it.

These tests hold a REAL flock from a live subprocess rather than mocking it, because the property under
test is OS behavior: the kernel releases an flock when its holder dies, which is why acquirability (not
the recorded `pid=`) is the trustworthy liveness signal.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import run_viewer as rv

STATE = {
    "run_id": "run-20260101T000000Z-1",
    "repo": "",
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-01-01T00:00:00+00:00",
    "queue": [
        {
            "position": 1,
            "id6": "aaa111",
            "setid": "tst",
            "action": "execute",
            "status": "running",
            "configured_file": "x/20260101-tst-01-aaa111-a.ipd.md",
            "attempts": [{"number": 1, "log": None}],
        },
        {
            "position": 2,
            "id6": "bbb222",
            "setid": "tst",
            "action": "execute",
            "status": "queued",
            "configured_file": "x/20260101-tst-02-bbb222-b.ipd.md",
        },
    ],
}

# Holds an exclusive flock on argv[1] until stdin closes, so the parent controls liveness precisely.
_HOLDER = """
import fcntl, sys
with open(sys.argv[1], "a+") as h:
    fcntl.flock(h.fileno(), fcntl.LOCK_EX)
    sys.stdout.write("locked\\n")
    sys.stdout.flush()
    sys.stdin.read()
"""


def _make_run(root: Path, name: str = "run-20260101T000000Z-1") -> Path:
    d = root / ".aw" / "records" / "runs" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "state.json").write_text(json.dumps(STATE), encoding="utf-8")
    (d / "driver.lock").write_text(
        "pid=999999 started=2026-01-01T00:00:00+00:00\n", encoding="utf-8"
    )
    return d


class HolderStateTests(unittest.TestCase):
    """E-01: flock acquirability is the liveness signal; the probe never writes."""

    def test_no_lock_file_means_no_holder(self):
        with TemporaryDirectory() as td:
            d = _make_run(Path(td))
            (d / "driver.lock").unlink()
            self.assertEqual(rv.driver_holder_state(d), rv.HOLDER_NONE)

    def test_released_lock_means_no_holder(self):
        with TemporaryDirectory() as td:
            d = _make_run(Path(td))
            self.assertEqual(rv.driver_holder_state(d), rv.HOLDER_NONE)

    def test_live_holder_is_detected(self):
        """A REAL flock held by a live subprocess must read as HOLDER_LIVE."""
        with TemporaryDirectory() as td:
            d = _make_run(Path(td))
            proc = subprocess.Popen(
                [sys.executable, "-c", _HOLDER, str(d / "driver.lock")],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
            )
            try:
                assert proc.stdout is not None
                self.assertEqual(proc.stdout.readline().strip(), "locked")
                self.assertEqual(rv.driver_holder_state(d), rv.HOLDER_LIVE)
            finally:
                proc.stdin.close()  # type: ignore[union-attr]
                proc.wait(timeout=10)

    def test_lock_released_when_holder_dies(self):
        """The OS releases an flock on death, which is why a recorded PID is not needed."""
        with TemporaryDirectory() as td:
            d = _make_run(Path(td))
            proc = subprocess.Popen(
                [sys.executable, "-c", _HOLDER, str(d / "driver.lock")],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
            )
            assert proc.stdout is not None
            proc.stdout.readline()
            self.assertEqual(rv.driver_holder_state(d), rv.HOLDER_LIVE)
            proc.kill()
            proc.wait(timeout=10)
            for _ in range(50):
                if rv.driver_holder_state(d) == rv.HOLDER_NONE:
                    break
                time.sleep(0.05)
            self.assertEqual(rv.driver_holder_state(d), rv.HOLDER_NONE)

    def test_missing_fcntl_is_unknown_not_dead(self):
        """Failing to prove a driver is alive is NOT proof it is dead."""
        import builtins

        real_import = builtins.__import__

        def no_fcntl(name, *a, **k):
            if name == "fcntl":
                raise ImportError("no fcntl")
            return real_import(name, *a, **k)

        with TemporaryDirectory() as td:
            d = _make_run(Path(td))
            builtins.__import__ = no_fcntl
            try:
                self.assertEqual(rv.driver_holder_state(d), rv.HOLDER_UNKNOWN)
            finally:
                builtins.__import__ = real_import

    def test_probe_does_not_modify_the_lock(self):
        with TemporaryDirectory() as td:
            d = _make_run(Path(td))
            lock = d / "driver.lock"
            before = lock.read_bytes()
            for _ in range(3):
                rv.driver_holder_state(d)
            self.assertTrue(lock.is_file(), "the probe must not unlink the lock")
            self.assertEqual(lock.read_bytes(), before)


class ProjectionTests(unittest.TestCase):
    """E-02/E-03: honest counts and lines, display-only, visibly attributed."""

    def test_running_with_no_holder_projects(self):
        with TemporaryDirectory() as td:
            d = _make_run(Path(td))
            s = rv.load_run_summary(d, Path(td))
            assert s is not None
            self.assertEqual(s.counts.get("running", 0), 0)
            self.assertEqual(s.counts.get(rv.ABANDONED), 1)

    def test_projection_preserves_the_persisted_value(self):
        with TemporaryDirectory() as td:
            d = _make_run(Path(td))
            s = rv.load_run_summary(d, Path(td))
            assert s is not None
            step = next(x for x in s.steps if x.id6 == "aaa111")
            self.assertTrue(step.is_projected)
            self.assertEqual(step.persisted_status, "running")
            self.assertEqual(step.status, rv.ABANDONED)

    def test_counts_and_steps_agree(self):
        with TemporaryDirectory() as td:
            d = _make_run(Path(td))
            s = rv.load_run_summary(d, Path(td))
            assert s is not None
            from collections import Counter

            self.assertEqual(Counter(x.status for x in s.steps), Counter(s.counts))

    def test_live_run_still_reports_running(self):
        with TemporaryDirectory() as td:
            d = _make_run(Path(td))
            proc = subprocess.Popen(
                [sys.executable, "-c", _HOLDER, str(d / "driver.lock")],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
            )
            try:
                assert proc.stdout is not None
                proc.stdout.readline()
                s = rv.load_run_summary(d, Path(td))
                assert s is not None
                self.assertEqual(s.counts.get("running"), 1)
                self.assertEqual(s.counts.get(rv.ABANDONED, 0), 0)
                step = next(x for x in s.steps if x.id6 == "aaa111")
                self.assertFalse(step.is_projected)
            finally:
                proc.stdin.close()  # type: ignore[union-attr]
                proc.wait(timeout=10)

    def test_read_is_side_effect_free(self):
        with TemporaryDirectory() as td:
            d = _make_run(Path(td))
            before = (d / "state.json").read_bytes()
            for _ in range(3):
                rv.load_run_summary(d, Path(td))
            self.assertEqual((d / "state.json").read_bytes(), before)

    def test_projection_never_yields_executed_or_verified(self):
        with TemporaryDirectory() as td:
            d = _make_run(Path(td))
            s = rv.load_run_summary(d, Path(td))
            assert s is not None
            for step in s.steps:
                if step.is_projected:
                    self.assertNotIn(step.status, ("executed", "verified"))

    def test_projected_line_is_distinguishable(self):
        from agent_workflows.term import Term

        term = Term(color=False)
        with TemporaryDirectory() as td:
            d = _make_run(Path(td))
            s = rv.load_run_summary(d, Path(td))
            assert s is not None
            step = next(x for x in s.steps if x.is_projected)
            line = rv.format_step_line(step, term)
            self.assertIn("no live driver", line)
            self.assertIn("recorded running", line)

    def test_persisted_interrupted_is_not_labelled_projected(self):
        """A real reconciled `interrupted` must not be confused with an inference."""
        from agent_workflows.term import Term

        with TemporaryDirectory() as td:
            root = Path(td)
            d = _make_run(root)
            state = json.loads((d / "state.json").read_text())
            state["queue"][0]["status"] = "interrupted"
            (d / "state.json").write_text(json.dumps(state), encoding="utf-8")
            s = rv.load_run_summary(d, root)
            assert s is not None
            step = next(x for x in s.steps if x.id6 == "aaa111")
            self.assertFalse(step.is_projected)
            self.assertNotIn(
                "no live driver", rv.format_step_line(step, Term(color=False))
            )


class RepairTests(unittest.TestCase):
    """E-04: the durable fix delegates to the single reconciler and refuses on a live run."""

    def test_repair_reconciles_and_is_idempotent(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            d = _make_run(root)
            state = json.loads((d / "state.json").read_text())
            state["repo"] = str(root)
            (d / "state.json").write_text(json.dumps(state), encoding="utf-8")

            code, msg = rv.repair_run(d, root)
            self.assertEqual(code, 0, msg)
            self.assertIn("reconciled 1 step", msg)
            after = json.loads((d / "state.json").read_text())
            self.assertEqual(after["queue"][0]["status"], "interrupted")

            code2, msg2 = rv.repair_run(d, root)
            self.assertEqual(code2, 0)
            self.assertIn("nothing to repair", msg2)

    def test_repair_refuses_while_a_driver_is_live(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            d = _make_run(root)
            proc = subprocess.Popen(
                [sys.executable, "-c", _HOLDER, str(d / "driver.lock")],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
            )
            try:
                assert proc.stdout is not None
                proc.stdout.readline()
                before = (d / "state.json").read_bytes()
                code, msg = rv.repair_run(d, root)
                self.assertEqual(code, 1)
                self.assertIn("refusing to repair", msg)
                self.assertEqual((d / "state.json").read_bytes(), before)
            finally:
                proc.stdin.close()  # type: ignore[union-attr]
                proc.wait(timeout=10)

    def test_repair_rejects_a_non_run_directory(self):
        with TemporaryDirectory() as td:
            code, msg = rv.repair_run(Path(td), Path(td))
            self.assertEqual(code, 2)
            self.assertIn("not a run directory", msg)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
