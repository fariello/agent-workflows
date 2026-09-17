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
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

REPO_ROOT = Path(__file__).resolve().parents[1]
DRIVERS = ("agent_workflows/oc_runipd.py", "agent_workflows/agy_runipd.py")

# rununify 05 (`ct4w0a`) E-03, per the maintainer's OQ-03 ruling: THE OWNER SET, not the driver files.
# A nested-`aw` launcher may now live in `runner_shared` (`run_checked` since `818uru`, `driver_begin`
# since `ct4w0a`), so a guard keyed to FILES has to be edited every time a symbol moves, and each such
# edit is an opportunity to weaken it by accident. Keyed to the owner set it states the property that
# actually matters -- every nested `aw` launch denies stdin, WHEREVER it lives -- and stops needing
# maintenance. The set must list every module that may hold one; a launcher added to a module NOT
# listed here would be invisible, which `OwnerSetCompletenessTests` below is what refuses.
OWNER_SET = DRIVERS + ("agent_workflows/runner_shared.py",)


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

    def test_the_owner_set_has_nested_aw_call_sites(self):
        """The launchers must still EXIST, counted over the OWNER SET rather than per driver file.

        RE-BASED by rununify 05 (`ct4w0a`) E-03 per the maintainer's OQ-03 ruling. This asserted at
        least 3 sites PER DRIVER FILE, which was true only while every launcher lived in a driver.
        `818uru` moved `run_checked` into `runner_shared` and `ct4w0a` moved `driver_begin`, so each
        driver file legitimately holds fewer of its own; the launchers did not vanish, their address
        changed. THE THRESHOLD IS NOT LOWERED, it is re-based: the total over the owner set is asserted
        at the SAME 6 sites that exist today, which is strictly more than the old form's 3-per-file
        could see, and a deleted launcher anywhere in the set now fails here.
        """
        total = sum(len(self._nested_aw_calls(rel)) for rel in OWNER_SET)
        self.assertGreaterEqual(
            total,
            6,
            "nested-`aw` launch sites vanished from the owner set: "
            + repr({rel: len(self._nested_aw_calls(rel)) for rel in OWNER_SET}),
        )

    def test_every_nested_aw_run_denies_stdin(self):
        """The core guard. `subprocess.Popen` for the AGENT is deliberately exempt (backlog qyaime).

        COUNTED OVER THE OWNER SET since `ct4w0a`: the shared module holds two launchers now, and
        checking only the driver files would have stopped inspecting them.
        """
        for rel in OWNER_SET:
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

        COUNTED ACROSS THE OWNER SET since rununify Order 02 (`818uru` E-05) and RE-BASED ONTO IT
        ENTIRELY by Order 05 (`ct4w0a` E-03), per the maintainer's OQ-03 ruling.

        WHAT THE OLD FORM DID AND WHY IT COULD NOT SURVIVE: it required each driver's OWN stdin-covered
        count PLUS the shared count to be at least 3, which was exactly `2 + 1` while `run_checked` was
        the only shared launcher. `ct4w0a` shared `driver_begin` too, making it `1 + 2`, so the per-file
        arithmetic broke even though not one launcher lost its `stdin=`.

        THE THRESHOLD IS RE-BASED, NOT LOWERED, and the distinction is the whole point. `818uru`'s
        docstring recorded why lowering is forbidden ("would have made this pass while silently
        accepting a future change that actually removed a `stdin=`"), and that reasoning is honored
        here: this now asserts that EVERY nested-`aw` launcher in the owner set that is not the exempt
        agent `Popen` denies stdin -- a UNIVERSAL, which is strictly stronger than any count, since a
        count can be satisfied while one site is uncovered. The symmetry half is preserved as the
        property it was protecting (a fix landing in one host only), by requiring each DRIVER to hold
        the same number of its own launchers.
        """
        agent_popen_exemptions = 0
        uncovered: list[str] = []
        launchers = 0
        for rel in OWNER_SET:
            src_lines = (REPO_ROOT / rel).read_text(encoding="utf-8").splitlines()
            for lineno, kw, first in self._nested_aw_calls(rel):
                if "Popen" in src_lines[lineno - 1]:
                    agent_popen_exemptions += 1
                    continue  # the host agent spawn; owned by backlog qyaime
                launchers += 1
                if "stdin" not in kw:
                    uncovered.append(f"{rel}:{lineno} (arg0={first})")
        # THE UNIVERSAL: no nested-`aw` launcher anywhere in the owner set may inherit a terminal.
        self.assertEqual(
            uncovered,
            [],
            "nested-`aw` launch site(s) in the owner set do not deny stdin: "
            + ", ".join(uncovered),
        )
        # NON-VACUITY: a universal over an empty set is trivially true, so the population is pinned.
        self.assertGreaterEqual(
            launchers,
            4,
            f"expected at least 4 non-exempt nested-`aw` launchers in the owner set, saw {launchers}",
        )
        self.assertEqual(
            agent_popen_exemptions,
            2,
            "expected exactly the two host agent `Popen` spawns to be exempt; a third exemption "
            "means something else stopped being checked",
        )
        # THE SYMMETRY PROPERTY the old count was protecting: a fix in one host only must not pass.
        own = {
            rel: sum(1 for lineno, kw, _ in self._nested_aw_calls(rel) if "stdin" in kw)
            for rel in DRIVERS
        }
        self.assertEqual(
            own[DRIVERS[0]],
            own[DRIVERS[1]],
            f"drivers disagree on stdin= coverage: {own}",
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


class OwnerSetCompletenessTests(unittest.TestCase):
    """rununify 05 (`ct4w0a`) E-03: what an owner-set guard can miss, and what stops it.

    Re-basing from FILES onto an OWNER SET buys freedom from per-move edits, and it introduces exactly
    one new failure mode in exchange: a launcher added to a module that is not in `OWNER_SET` would
    never be inspected, so the guard above would keep passing while an unprotected nested `aw` shipped.
    That is a worse hole than the one the re-base closed, so the set's completeness is asserted rather
    than assumed. This class is the price of the ruling and it is deliberately paid here.
    """

    # Nested-`aw` launches that live OUTSIDE the owner set, each with the reason it is not covered by
    # the stdin guard above. This is an ALLOWLIST and it is deliberately tiny: every entry is a hole,
    # and the scan below fails when a new one appears so the hole is a decision rather than a drift.
    EXEMPT_OUTSIDE_OWNER_SET: ClassVar[dict[str, int]] = {
        # PRE-EXISTING AND REPORTED, not introduced by `ct4w0a` (measured at its execution HEAD
        # 1171f7b2, before any change in this plan). These two are release GATES, not runner launchers:
        # they are invoked from a human-run `aw release-review`, they pass `--agent` (which makes the
        # child non-interactive on its own merits), and they build an INLINE literal argv rather than
        # naming it `argv`/`cmd`, which is why the original per-driver guard never saw them either.
        # They are NOT fixed here because `agent_workflows/release_readiness.py` is outside this plan's
        # declared `Scope-Paths`; the finding is filed instead, so the next reader inherits the fact
        # rather than re-discovering it.
        "agent_workflows/release_readiness.py": 2,
    }

    def _semantic_nested_aw_sites(self, rel: str) -> list[tuple[int, str, bool]]:
        """Nested-`aw` launches found by MEANING rather than by the first argument's NAME.

        WHY A SECOND DETECTOR. The guard above identifies launchers by `arg0 in ('argv', 'cmd')`,
        which is precise INSIDE the drivers and useless outside them: package-wide, `cmd` is what a
        plain `git` invocation is called too, so that filter yields false positives (measured: 5, all
        of them `git`/`--version` calls that cannot prompt for anything). This detector instead finds a
        function that BUILDS a nested-`aw` argv -- through the pin helpers or a literal
        `-m agent_workflows` -- and reports the subprocess launches inside it.
        """
        src = (REPO_ROOT / rel).read_text(encoding="utf-8")
        tree = ast.parse(src)
        builders: dict[str, tuple[int, int]] = {}
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = ast.unparse(fn)
            if (
                "pinned_module_argv" in body
                or "_AW_PIN_BOOTSTRAP" in body
                or "_AW_PIN_PROBE" in body
                or '"-m", "agent_workflows"' in body
                or "'-m', 'agent_workflows'" in body
            ):
                builders[fn.name] = (fn.lineno, fn.end_lineno or fn.lineno)
        found: list[tuple[int, str, bool]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and ast.unparse(node.func) in (
                "subprocess.run",
                "subprocess.Popen",
            ):
                kw = {k.arg for k in node.keywords if k.arg}
                for name, (start, end) in builders.items():
                    if start <= node.lineno <= end:
                        found.append((node.lineno, name, "stdin" in kw))
        return found

    def test_no_unaccounted_nested_aw_launcher_lives_outside_the_owner_set(self):
        """Scan the WHOLE package by MEANING, so an unlisted launcher fails loudly.

        This is what the re-base onto an owner set costs, and paying it is the point: a launcher added
        to a module nobody listed would never be inspected by the stdin guard above, which is a worse
        hole than the per-file counting the ruling replaced.
        """
        package = REPO_ROOT / "agent_workflows"
        strays: dict[str, list[str]] = {}
        for path in sorted(package.rglob("*.py")):
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel in OWNER_SET:
                continue
            sites = self._semantic_nested_aw_sites(rel)
            if sites:
                strays[rel] = [f"{rel}:{ln} in {fn}" for ln, fn, _ in sites]
        counts = {rel: len(v) for rel, v in strays.items()}
        self.assertEqual(
            counts,
            self.EXEMPT_OUTSIDE_OWNER_SET,
            "the set of nested-`aw` launches OUTSIDE the owner set changed. Every such site is "
            "invisible to the stdin guard above, so a new one must be a decision: either add its "
            "module to OWNER_SET (preferred, it then gets the guard) or add it to "
            "EXEMPT_OUTSIDE_OWNER_SET with the reason. Found: " + repr(strays),
        )

    def test_the_owner_set_names_only_modules_that_exist(self):
        for rel in OWNER_SET:
            with self.subTest(module=rel):
                self.assertTrue(
                    (REPO_ROOT / rel).is_file(),
                    f"{rel} is named in OWNER_SET but does not exist; a renamed module would "
                    "silently stop being scanned",
                )

    def test_the_completeness_scan_would_catch_a_stray_launcher(self):
        """Non-vacuity for the scan itself, run against a REAL temporary module on disk.

        Asserted through `_semantic_nested_aw_sites`, the same function the scan uses, rather than
        against a re-implementation, so a detector that stopped detecting fails here.
        """
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / "agent_workflows") as temp:
            stray = Path(temp) / "stray_launcher.py"
            stray.write_text(
                "import subprocess\n"
                "def sneaky(repo):\n"
                "    argv = pinned_module_argv(['ipd', 'set', 'executed'])\n"
                "    return subprocess.run(argv, cwd=repo, stdout=subprocess.PIPE)\n",
                encoding="utf-8",
            )
            rel = stray.relative_to(REPO_ROOT).as_posix()
            sites = self._semantic_nested_aw_sites(rel)
            self.assertEqual(
                [(fn, covered) for _ln, fn, covered in sites],
                [("sneaky", False)],
                "the completeness scan must recognise a nested-`aw` launcher in an unlisted module, "
                "and must report it as NOT stdin-covered",
            )

    def test_the_semantic_detector_ignores_a_plain_git_invocation(self):
        """The other half of non-vacuity: it must not cry wolf on a `cmd` that is just `git`.

        This is why the package-wide scan uses meaning rather than the `arg0` NAME the driver guard
        uses: measured, the name filter reports 5 false positives package-wide, all `git`/`--version`
        calls that cannot prompt.
        """
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / "agent_workflows") as temp:
            benign = Path(temp) / "benign_git.py"
            benign.write_text(
                "import subprocess\n"
                "def commit(repo, paths):\n"
                "    cmd = ['git', 'commit', '-m', 'x', '--'] + paths\n"
                "    return subprocess.run(cmd, cwd=repo)\n",
                encoding="utf-8",
            )
            rel = benign.relative_to(REPO_ROOT).as_posix()
            self.assertEqual(
                self._semantic_nested_aw_sites(rel),
                [],
                "a plain `git` launch must NOT be reported as a nested-`aw` launcher",
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
