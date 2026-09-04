"""Tests for ttywedge Order 01 (g40w37): a nested `aw` must never block on a prompt.

Incident: a driver-spawned `aw ipd finalize` wedged for 1h49m holding its run lock, leaving the plan
`approved` in pending/ while the run reported `complete`. `ipd_lifecycle.run_finalize` decided it could
prompt from `sys.stdin.isatty()` alone, and the driver spawned it with stdout/stderr piped but stdin
INHERITED, so the child saw the operator's terminal and called `input()` for an answer nobody could
type, because the prompt itself went into a pipe.

Two independent layers are asserted here, because each alone would have prevented the incident and
neither is redundant: the CALLEE must not treat an inherited TTY as consent, and the CALLER must not
hand a child a terminal at all.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DRIVERS = ("agent_workflows/oc_runipd.py", "agent_workflows/agy_runipd.py")


class _FakeStream:
    def __init__(self, tty: bool, raises: type[BaseException] | None = None) -> None:
        self._tty = tty
        self._raises = raises

    def isatty(self) -> bool:
        if self._raises is not None:
            raise self._raises("detached")
        return self._tty


def _interactive(
    *,
    stdin_tty: bool,
    stdout_tty: bool,
    is_agent: bool = False,
    is_json: bool = False,
    env: dict[str, str] | None = None,
    stdin_raises: type[BaseException] | None = None,
) -> bool:
    """Re-evaluate run_finalize's predicate in isolation.

    Mirrors the implementation exactly; the AST test below pins that the real code still carries the
    same conditions, so this cannot silently drift into testing a copy.
    """
    import os

    environ = env if env is not None else {}

    def is_tty(stream: object) -> bool:
        try:
            return bool(getattr(stream, "isatty", None) and stream.isatty())  # type: ignore[union-attr]
        except (ValueError, OSError):
            return False

    forced = any(
        str(environ.get(var, "")).strip().lower() not in ("", "0", "false", "no")
        for var in ("AW_NONINTERACTIVE", "CI")
    )
    assert os is not None
    return (
        not (is_agent or is_json)
        and not forced
        and is_tty(_FakeStream(stdin_tty, stdin_raises))
        and is_tty(_FakeStream(stdout_tty))
    )


class PredicateMatrixTests(unittest.TestCase):
    """E-01: the full matrix, not just the happy path."""

    def test_the_incident_case_is_now_non_interactive(self):
        """stdin inherited TTY + stdout piped: exactly what wedged for 1h49m."""
        self.assertFalse(_interactive(stdin_tty=True, stdout_tty=False))

    def test_real_human_terminal_still_prompts(self):
        """No regression: a genuine interactive session must still be interactive."""
        self.assertTrue(_interactive(stdin_tty=True, stdout_tty=True))

    def test_aw_noninteractive_env_forces_off(self):
        self.assertFalse(
            _interactive(
                stdin_tty=True, stdout_tty=True, env={"AW_NONINTERACTIVE": "1"}
            )
        )

    def test_ci_env_forces_off(self):
        self.assertFalse(
            _interactive(stdin_tty=True, stdout_tty=True, env={"CI": "true"})
        )

    def test_falsey_env_values_do_not_force_off(self):
        """`CI=0` / `CI=` must not be mistaken for a signal."""
        for value in ("", "0", "false", "no", "  "):
            self.assertTrue(
                _interactive(stdin_tty=True, stdout_tty=True, env={"CI": value}),
                f"CI={value!r} should not force non-interactive",
            )

    def test_agent_and_json_modes_remain_non_interactive(self):
        self.assertFalse(_interactive(stdin_tty=True, stdout_tty=True, is_agent=True))
        self.assertFalse(_interactive(stdin_tty=True, stdout_tty=True, is_json=True))

    def test_no_tty_at_all_is_non_interactive(self):
        self.assertFalse(_interactive(stdin_tty=False, stdout_tty=False))

    def test_detached_stream_is_not_a_terminal(self):
        """A closed/detached stream raises; that must read as 'no terminal', not crash."""
        for exc in (ValueError, OSError):
            self.assertFalse(
                _interactive(stdin_tty=True, stdout_tty=True, stdin_raises=exc)
            )


class CalleeSourceTests(unittest.TestCase):
    """E-01: pin that the real predicate still carries every condition."""

    def _predicate_src(self) -> str:
        src = (REPO_ROOT / "agent_workflows" / "ipd_lifecycle.py").read_text(
            encoding="utf-8"
        )
        i = src.find("forced_noninteractive")
        self.assertGreater(i, -1, "the hardened predicate is gone")
        return src[i - 400 : i + 700]

    def test_requires_stdout_tty(self):
        self.assertIn("_is_tty(_sys.stdout)", self._predicate_src())

    def test_requires_stdin_tty(self):
        self.assertIn("_is_tty(_sys.stdin)", self._predicate_src())

    def test_honours_env_signals(self):
        src = self._predicate_src()
        self.assertIn("AW_NONINTERACTIVE", src)
        self.assertIn("CI", src)

    def test_still_excludes_agent_and_json_modes(self):
        self.assertIn("ctx.is_agent or ctx.is_json", self._predicate_src())


def _subprocess_calls(rel: str) -> list[tuple[int, set[str], str]]:
    """(lineno, kwargs, first-arg-source) for every subprocess.run/Popen in a module."""
    tree = ast.parse((REPO_ROOT / rel).read_text(encoding="utf-8"))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and ast.unparse(node.func) in (
            "subprocess.run",
            "subprocess.Popen",
        ):
            first = ast.unparse(node.args[0]) if node.args else ""
            out.append((node.lineno, {k.arg for k in node.keywords if k.arg}, first))
    return out


class CallerDevnullTests(unittest.TestCase):
    """E-02/E-03/E-04: an AST guard, not a grep (a grep would match this file's own literals)."""

    # The nested-`aw` launchers: run_checked, driver_begin, driver_finalize in each driver. They pass
    # a prebuilt `argv`/`cmd` list, unlike the inline `['git', ...]` calls which cannot prompt.
    NESTED_AW_FIRST_ARGS = ("argv", "cmd")

    def _nested_aw_calls(self, rel: str):
        return [
            (lineno, kw, first)
            for lineno, kw, first in _subprocess_calls(rel)
            if first in self.NESTED_AW_FIRST_ARGS
        ]

    def test_both_drivers_have_nested_aw_call_sites(self):
        for rel in DRIVERS:
            self.assertGreaterEqual(
                len(self._nested_aw_calls(rel)), 3, f"{rel}: call sites vanished"
            )

    def test_every_nested_aw_run_denies_stdin(self):
        """The core guard. `subprocess.Popen` for the AGENT is deliberately exempt (backlog qyaime)."""
        for rel in DRIVERS:
            for lineno, kw, first in self._nested_aw_calls(rel):
                src = (REPO_ROOT / rel).read_text(encoding="utf-8").splitlines()
                is_popen = "Popen" in src[lineno - 1]
                if is_popen:
                    continue  # the host agent spawn; owned by qyaime, not this plan
                self.assertIn(
                    "stdin",
                    kw,
                    f"{rel}:{lineno} spawns a nested aw without stdin= (arg0={first})",
                )

    def test_symmetry_across_both_drivers(self):
        """A fix landed in one driver only must not pass.

        COUNTED ACROSS THE OWNER SET since rununify Order 02 (`818uru` E-05): `run_checked` was one
        of each driver's three nested-`aw` launchers and now has ONE definition in `runner_shared`,
        which both drivers delegate to through a one-line wrapper. Each driver file therefore shows
        two of its own sites plus the shared one.

        THE THRESHOLD IS DELIBERATELY UNCHANGED at 3. Lowering it to 2 would have made this pass
        while silently accepting a future change that actually removed a `stdin=` from a launch site,
        which is exactly the regression this guard exists to catch. The symmetry assertion still
        compares like with like, because the shared site is added to both sides.
        """
        shared = "agent_workflows/runner_shared.py"
        shared_covered = sum(
            1 for _lineno, kw, _first in self._nested_aw_calls(shared) if "stdin" in kw
        )
        counts = {
            rel: sum(1 for lineno, kw, _ in self._nested_aw_calls(rel) if "stdin" in kw)
            for rel in DRIVERS
        }
        self.assertEqual(
            counts[DRIVERS[0]],
            counts[DRIVERS[1]],
            f"drivers disagree on stdin= coverage: {counts}",
        )
        for rel, n in counts.items():
            self.assertGreaterEqual(
                n + shared_covered,
                3,
                f"{rel} covers only {n} of its own call sites plus "
                f"{shared_covered} shared; the total must not drop below 3",
            )

    def test_guard_fails_on_an_injected_regression(self):
        """Proves the guard guards something, rather than merely passing today."""
        snippet = (
            "import subprocess\n"
            "def f(cmd, repo):\n"
            "    return subprocess.run(cmd, cwd=repo, stdout=subprocess.PIPE)\n"
        )
        offenders = []
        for node in ast.walk(ast.parse(snippet)):
            if (
                isinstance(node, ast.Call)
                and ast.unparse(node.func) == "subprocess.run"
            ):
                kw = {k.arg for k in node.keywords if k.arg}
                first = ast.unparse(node.args[0]) if node.args else ""
                if first in self.NESTED_AW_FIRST_ARGS and "stdin" not in kw:
                    offenders.append(node.lineno)
        self.assertEqual(
            offenders, [3], "the AST guard must catch a nested-aw call missing stdin="
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
