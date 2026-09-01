"""Worker-role lifecycle verbs refuse deterministically (wtiso-03 `rchpms` E-04..E-06).

x03wgn Section 2 "Receipt ownership does not mean agent tool compliance" + Section 3
`AW-LIFECYCLE-ROLE-001`. The driver already wraps begin/finalize, but receipt OWNERSHIP alone does not
stop an in-lane agent from running `aw ipd begin`/`aw ipd finalize` ITSELF, which forks a second
receipt and a second lifecycle transaction the driver cannot see (and the in-lane receipt copy then
hides the split). So a process marked `AW_EXECUTION_ROLE=worker` refuses both verbs outright.

ADVERSARIAL SHAPE: the refusal tests drive the REAL CLI in a subprocess with the env var set - not the
predicate - and assert (a) the documented exit code, (b) the `AW-LIFECYCLE-ROLE-001` token on stderr,
and (c) that NO receipt file was created. (c) is the assertion that matters: a refusal that still wrote
a receipt would leave exactly the forked authority this guard exists to prevent.

HONEST LIMIT (asserted nowhere because it is not enforceable here): the env selector is the
operational-default guidance layer, not a hardened boundary. A same-user worker with shell access can
unset it; hard enforcement is an OS sandbox / separate principal (x03wgn Phase 6, `1o4eif`).
"""

from __future__ import annotations

import inspect
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd
from agent_workflows import ipd_authoring as A
from agent_workflows import ipd_lifecycle as LC
from agent_workflows import oc_runipd

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")


def _commit_all(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)


def _ready_plan_text(*, plan_id: str = "abc123") -> str:
    txt = A.build_skeleton(
        kind="child",
        title="demo",
        author="tester",
        when="2026-08-24",
        set_name="demo",
        order=1,
        plan_id=plan_id,
    )
    out = []
    in_meta = True
    for ln in txt.splitlines():
        if ln.startswith("## "):
            in_meta = False
        if in_meta and ln.startswith("- Status:"):
            out.append("- Status: approved")
            continue
        if in_meta and ln.startswith("- Scope-Paths:"):
            out.append("- Scope-Paths: agent_workflows/demo.py, tests/test_demo.py")
            continue
        if in_meta and ln.startswith("- Item-Dependencies:"):
            out.append("- Item-Dependencies: none")
            continue
        out.append(ln)
        if in_meta and ln.startswith("- Author:"):
            out.append("- Approval: 2026-08-24, human: approved")
    return "\n".join(out) + "\n"


class WorkerRolePredicateTests(unittest.TestCase):
    """E-04: the pure predicate and the deterministic error token."""

    def test_worker_role_predicate(self):
        self.assertIs(LC.worker_role_active({"AW_EXECUTION_ROLE": "worker"}), True)
        self.assertIs(LC.worker_role_active({}), False)
        self.assertIs(
            LC.worker_role_active({"AW_EXECUTION_ROLE": "coordinator"}), False
        )
        # An empty/whitespace value is not a worker either (fail OPEN for the role check is correct:
        # only an explicit `worker` marking removes authority).
        self.assertIs(LC.worker_role_active({"AW_EXECUTION_ROLE": ""}), False)
        self.assertIs(LC.worker_role_active({"AW_EXECUTION_ROLE": "  worker  "}), True)
        self.assertTrue(LC.LIFECYCLE_ROLE_ERROR.startswith("AW-LIFECYCLE-ROLE-001"))


class WorkerRoleCliRefusalTests(unittest.TestCase):
    """E-05: the CLI verbs refuse, with no receipt and no transition."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        d = self.root / ".aw" / "records" / "plans" / "pending"
        d.mkdir(parents=True, exist_ok=True)
        self.plan = d / "20260824-demo-01-abc123-demo.ipd.md"
        self.plan.write_text(_ready_plan_text(), encoding="utf-8")
        _commit_all(self.root, "init")
        self.receipt = LC.receipt_path_for(self.root, "abc123")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run_cli(self, *argv: str, role: str | None) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(_REPO_ROOT)
        env.pop("AW_EXECUTION_ROLE", None)
        if role is not None:
            env["AW_EXECUTION_ROLE"] = role
        return subprocess.run(
            [sys.executable, "-m", "agent_workflows", *argv],
            cwd=self.root,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_worker_role_begin_refuses_with_role_error(self):
        proc = self._run_cli(
            "ipd", "begin", str(self.plan), "--actor", "x", role="worker"
        )
        self.assertEqual(
            proc.returncode,
            LC.EXIT_CANNOT_RUN,
            f"stdout={proc.stdout!r} stderr={proc.stderr!r}",
        )
        self.assertIn("AW-LIFECYCLE-ROLE-001", proc.stderr)
        # THE POINT: no execution authority was created.
        self.assertFalse(
            self.receipt.exists(),
            "a refused worker-role begin must write NO receipt",
        )

    def test_worker_role_finalize_refuses_and_writes_no_receipt(self):
        proc = self._run_cli(
            "ipd",
            "finalize",
            str(self.plan),
            "--actor",
            "x",
            "--message",
            "m",
            "--apply",
            role="worker",
        )
        self.assertEqual(
            proc.returncode,
            LC.EXIT_CANNOT_RUN,
            f"stdout={proc.stdout!r} stderr={proc.stderr!r}",
        )
        self.assertIn("AW-LIFECYCLE-ROLE-001", proc.stderr)
        self.assertFalse(self.receipt.exists())
        # And no terminal transition happened: the plan is still where it was.
        self.assertTrue(self.plan.is_file(), "the plan must not have been moved")

    def test_coordinator_role_begin_runs_normally(self):
        """The guard must not break the normal path: with no role marking, the gate runs."""
        proc = self._run_cli("ipd", "begin", str(self.plan), "--actor", "x", role=None)
        self.assertEqual(
            proc.returncode,
            LC.EXIT_OK,
            f"stdout={proc.stdout!r} stderr={proc.stderr!r}",
        )
        self.assertNotIn("AW-LIFECYCLE-ROLE-001", proc.stderr)
        self.assertTrue(
            self.receipt.is_file(),
            "a coordinator-role begin must write the receipt (normal gate ran)",
        )


class ChildEnvWorkerRoleTests(unittest.TestCase):
    """E-06: the drivers mark only the WORKER child, never their own process."""

    def test_both_drivers_mark_only_an_isolated_turn(self):
        """The marking is WIRED into both turn functions, keyed on the lane, and strips a stale value.

        Asserted against the driver SOURCE rather than a helper, because the thing that must be true
        is that the running turn marks the child. `rchpms` originally carried this through a
        `build_child_env` helper introduced by its Phase-1 prerequisite (`qcqhj7`); that phase is NOT
        landed here (its prompt-isolation design collides with main's own), so the same behavior is
        wired directly onto the shared `pinned_child_env`. This test pins the BEHAVIOR so a later
        refactor cannot quietly drop the marking or the strip.
        """
        for module, func in (
            (oc_runipd, "run_opencode"),
            (agy_runipd, "run_agy_turn"),
        ):
            src = inspect.getsource(getattr(module, func))
            with self.subTest(driver=module.__name__):
                # The child env is built EXPLICITLY and handed to Popen (it used to be inherited
                # implicitly, so there was nowhere to put the marking at all).
                self.assertIn("pinned_child_env()", src)
                self.assertIn('popen_kwargs["env"] = child_env', src)
                # Marked only when the turn runs in a lane...
                self.assertIn("if work_dir:", src)
                self.assertIn("ipd_lifecycle.ROLE_WORKER", src)
                # ...and a stale inherited marking is STRIPPED otherwise, so a coordinator turn can
                # never accidentally refuse its own lifecycle verbs.
                self.assertIn(
                    "child_env.pop(ipd_lifecycle.EXECUTION_ROLE_ENV, None)", src
                )

    def test_the_marking_predicate_round_trips(self):
        """The value the drivers write is exactly the value the refusal predicate recognizes."""
        marked = {"PATH": "/usr/bin"}
        marked[LC.EXECUTION_ROLE_ENV] = LC.ROLE_WORKER
        self.assertTrue(LC.worker_role_active(marked))

        stripped = dict(marked)
        stripped.pop(LC.EXECUTION_ROLE_ENV, None)
        self.assertFalse(LC.worker_role_active(stripped))
        # Everything else survives: the env is explicit, not minimal.
        self.assertEqual(stripped["PATH"], "/usr/bin")

    def test_driver_own_process_is_not_worker_role(self):
        """The DRIVER's own environment must never be worker-marked, or `driver_begin` would refuse."""
        self.assertNotEqual(os.environ.get("AW_EXECUTION_ROLE"), "worker")
        self.assertFalse(LC.worker_role_active(os.environ))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
