"""A BEHAVIORAL guard: a test touching the role-gated lifecycle verbs must DECLARE its role
(plan `e4lkv5` E-07).

THE DEFECT CLASS THIS CATCHES. `ipd_lifecycle.run_begin`/`run_finalize` read the AMBIENT process
environment (`worker_role_active(os.environ)`), and both runners export `AW_EXECUTION_ROLE=worker`
into an isolated execute turn. A test that drives those verbs without declaring a role therefore
measures WHOEVER LAUNCHED PYTEST: it passes in a human's shell and fails with the
`AW-LIFECYCLE-ROLE-001` refusal inside a managed lane. The mirror case is silent and worse: a test
ASSERTING the refusal while inheriting the marking passes VACUOUSLY, so a safety guard stops testing
anything and no run goes red to say so.

WHY THIS IS BEHAVIORAL AND NOT A GREP, which is the whole design constraint. The real failure mode is
INHERITANCE, i.e. the ABSENCE of a declaration, and no source-text search can see an absence: a file
that merely MENTIONS `AW_EXECUTION_ROLE` in a comment satisfies a grep while still inheriting. This
repository has already paid for that lesson once - the previous guard of that kind "was measurably
satisfiable by a COMMENT, and on oc a comment is what satisfied it"
(`agent_workflows/runner_shared.py:14310`), which is why it was replaced by an assertion on actual
behavior. So this guard RUNS the protected files under BOTH role values and asserts the results are
identical. A test whose outcome depends on the ambient role is exactly what that comparison exposes,
and a comment cannot change an outcome.

WHY THE COMPARISON NEEDS A RE-ASSERTING PLUGIN. The root `conftest.py` pops `AW_EXECUTION_ROLE` at
import time (added in `f1a6e94c`), so an ordinary subprocess CANNOT observe the marked condition no
matter what env it is handed: the scrub runs before collection. That scrub keeps a lane's baseline
green, but it MASKS this defect class rather than fixing it - measured at `2815aa56`, re-asserting the
marking after the scrub still reddened 31 tests. This guard therefore injects a `-p` plugin that sets
the marking back in `pytest_configure`, i.e. AFTER the scrub and BEFORE collection, which is the only
place the underlying condition is observable. That makes the guard independent of the scrub: it keeps
working if the scrub is ever removed, and it keeps failing if a new test starts inheriting while the
scrub hides it.

HONEST LIMITS, stated because a guard whose reach is oversold is worse than none.
1. It protects an ENUMERATED file list (`PROTECTED_FILES`), not the whole suite. A brand-new test
   file that inherits is not covered until it is added here. Enumeration is deliberate: running the
   whole suite twice costs ~6 minutes, while these files cost ~17s per condition.
2. It proves OUTCOME INVARIANCE under the role, not that any particular mechanism was used. A test
   that hard-codes its role by hand rather than through `support.declare_execution_role` passes, and
   that is correct: declaring the role is the requirement, the helper is just the convenient way.
3. It cannot detect a test that inherits some OTHER ambient variable. `tests/test_turn_bounds.py`'s
   `OPENCODE_CONFIG_CONTENT` failure is that same defect class in a different variable and is out of
   this plan's scope (already filed many times over).
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from tests import support

# MARKED `slow`, following this repo's own convention for subprocess-heavy files. This guard runs the
# protected files TWICE in child pytest sessions, measured at 4m26s, so leaving it in the default
# fast subset would roughly double a bare `python3 -m pytest`. It runs in `make test-all`, in
# release-review and in CI, which is where a role-inheritance regression needs to be caught. Honest
# cost of that choice: a newly added inheriting test is caught at the full-suite gate rather than in
# a lane's own bare run.
pytestmark = pytest.mark.slow

_REPO_ROOT = support.REPO_ROOT

# The files whose role-independence is guarded. These are the five that plan `e4lkv5` made declare
# their role, i.e. every file measured to hold a role-inheriting failure except the one owned by
# plan `8b9ufm` (see `_KNOWN_AMBIENT_ASSERTING`).
PROTECTED_FILES = (
    "tests/test_oc_runipd.py",
    "tests/test_agy_runipd_cli.py",
    "tests/test_runner_backlog_close_in_lane.py",
    "tests/test_ipd_lifecycle_cli.py",
    "tests/test_novalnomerge_integration.py",
)

# Deliberately NOT protected: this test asserts about the AMBIENT environment by design, so it is
# role-dependent on purpose. APPROVED plan `8b9ufm` owns the file and explicitly forbids "fixing" it.
_KNOWN_AMBIENT_ASSERTING = "tests/test_worker_role_refusal.py"

_REASSERT_PLUGIN = '''"""Set the managed-lane role marking AFTER the root conftest scrubs it.

`pytest_configure` runs after conftest import and before collection, which is the only window in
which the marked condition is observable. See tests/test_role_declaration_guard.py.
"""
import os


def pytest_configure(config):
    os.environ["AW_EXECUTION_ROLE"] = "worker"
'''


def _run_protected(
    files, *, reassert_worker: bool, extra_args=()
) -> subprocess.CompletedProcess:
    """Run `files` in a subprocess, optionally re-asserting the worker marking after the scrub.

    `-o addopts=""` is used deliberately: the configured `addopts` carry `-q`, which would suppress
    the per-test counts this guard compares, and `-n auto`, whose worker startup dominates a run this
    small.
    """

    with tempfile.TemporaryDirectory() as tmp:
        plugin_dir = Path(tmp)
        (plugin_dir / "_aw_reassert_role.py").write_text(
            _REASSERT_PLUGIN, encoding="utf-8"
        )

        env = {**os.environ}
        env.pop(support.EXECUTION_ROLE_ENV, None)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(plugin_dir), str(_REPO_ROOT), env.get("PYTHONPATH", "")]
        ).rstrip(os.pathsep)

        argv = [sys.executable, "-m", "pytest", "-o", 'addopts=""', *extra_args]
        if reassert_worker:
            argv += ["-p", "_aw_reassert_role"]
        argv += list(files)

        return subprocess.run(
            argv,
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            env=env,
        )


def _summary(proc: subprocess.CompletedProcess) -> str:
    """The last non-empty stdout line, i.e. pytest's own summary line."""

    lines = [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip()]
    return lines[-1] if lines else "<no output>"


def _failed_ids(proc: subprocess.CompletedProcess) -> set[str]:
    return {
        ln.split(" ", 1)[1].split(" ")[0]
        for ln in (proc.stdout or "").splitlines()
        if ln.startswith("FAILED ")
    }


class TheReassertProbeActuallyReachesTheTests(unittest.TestCase):
    """The guard's own instrument must work, or every assertion below passes vacuously.

    This is the meta-check that stops this file becoming the thing it polices. If the plugin failed
    to set the marking (or the conftest scrub moved and re-scrubbed after it), the two conditions
    would be identical for the WRONG reason and the guard would report green forever.
    """

    def test_the_probe_makes_the_marked_condition_observable(self):
        """`test_worker_role_refusal.py`'s ambient assertion is the litmus: it MUST fail under the
        probe and pass without it. If that flips, the probe is broken, not the tree."""

        marked = _run_protected(
            [f"{_KNOWN_AMBIENT_ASSERTING}::ChildEnvWorkerRoleTests"],
            reassert_worker=True,
        )
        clean = _run_protected(
            [f"{_KNOWN_AMBIENT_ASSERTING}::ChildEnvWorkerRoleTests"],
            reassert_worker=False,
        )

        self.assertNotEqual(
            marked.returncode,
            0,
            "the probe did not reach the test session: the ambient-asserting test passed with the "
            f"marking re-asserted, so this guard would be vacuous.\nstdout:\n{marked.stdout}",
        )
        self.assertEqual(
            clean.returncode,
            0,
            f"without the probe the same test must pass.\nstdout:\n{clean.stdout}",
        )


class ProtectedTestsDoNotDependOnTheAmbientRole(unittest.TestCase):
    """THE GUARD: the protected files must behave IDENTICALLY under either ambient role."""

    def test_protected_files_pass_with_the_worker_marking_reasserted(self):
        """A role-inheriting test reddens here with `AW-LIFECYCLE-ROLE-001` while an ordinary run
        stays green, which is precisely the condition a lane agent hits."""

        proc = _run_protected(PROTECTED_FILES, reassert_worker=True)
        self.assertEqual(
            proc.returncode,
            0,
            "a protected test INHERITED the ambient execution role instead of declaring it. "
            "Declare it in the test's `setUp` with `support.declare_execution_role(self)` (or pass "
            "an explicit `env=`/`role=` to the code under test); do NOT relax "
            "`AW-LIFECYCLE-ROLE-001` and do NOT scrub the variable to make this pass.\n"
            f"summary: {_summary(proc)}\nfailed: {sorted(_failed_ids(proc))}",
        )

    def test_the_outcome_is_the_same_under_both_ambient_roles(self):
        """Invariance is the real property, and it catches the direction the check above cannot: a
        test that passes only WITH the marking (a refusal test relying on the ambient value) is just
        as broken as one that fails with it."""

        marked = _run_protected(PROTECTED_FILES, reassert_worker=True)
        clean = _run_protected(PROTECTED_FILES, reassert_worker=False)

        self.assertEqual(
            _failed_ids(marked),
            _failed_ids(clean),
            "the protected files produced a DIFFERENT failure set under the two ambient roles, so "
            "at least one test reads the role instead of declaring it.\n"
            f"marked: {_summary(marked)}\nclean:  {_summary(clean)}",
        )
        self.assertEqual(
            marked.returncode,
            clean.returncode,
            f"exit status differed by ambient role.\nmarked: {_summary(marked)}\n"
            f"clean:  {_summary(clean)}",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
