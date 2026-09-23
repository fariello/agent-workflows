#!/usr/bin/env python3
"""lanetruth Order 01 (af7i6p): a nested `aw` must run the RUNNER's own tooling, not the lane's.

THE DEFECT. Under worktree isolation the runner invokes a nested `aw` with `cwd` set to the LANE
worktree (`driver_finalize` receives the lane as its `repo` argument). Python seeds `sys.path[0]`
from the cwd, so a bare `[sys.executable, "-m", "agent_workflows", ...]` resolved the package to
the LANE BRANCH's checked-out copy. A lane that legitimately edits `agent_workflows/` therefore
had the runner execute that unreviewed, possibly mid-edit code to perform the very transition
meant to gate it, and two lanes in one run could enforce different lifecycle rules depending on
their base commits.

WHY THE FIXTURE HAS THREE PACKAGES. A two-package fixture cannot distinguish "pinned to the
runner" from "merely not the lane". On an editable install (which this repo is) site-packages and
the parent checkout are the SAME files, so a cwd-suppression-only fix passes a two-package test
while silently running third-party code on a normal wheel install. The third, default-path copy
makes that failure detectable: see `test_suppression_only_lands_on_the_wrong_copy`.

FIXTURE DETAIL. The identity probe imports and prints `agent_workflows.__file__` rather than
running `-m agent_workflows --version`, because a minimal decoy package has no `__main__.py` and
`-m` against it dies with "cannot be directly executed" -- which does prove the decoy was
selected, but on an error path an assertion written against stdout would misread as a failure to
reproduce. The decoys here are given a `__main__.py` anyway so both surfaces are usable.

WHY THIS FILE IS THE CANONICAL RECORD OF THE COMMENT-SATISFIED-PIN DEFECT, and why the source-text
pins that used to live beside the runtime tests above are gone (audit 2026-09-19). The shipped guard
`test_raw_subprocess_module_launches_pass_the_pinned_env` searched `inspect.getsource(driver_begin)`
for the LITERAL `env=pinned_child_env()`; on `oc_runipd` the real code read
`env={**pinned_child_env(), **begin_baseline_env(isolated)}`, which does NOT contain that substring,
so the only match in the whole function was the explanatory COMMENT above it. The guard was green for
a reason unrelated to the pin. `TheBeginPinSurvivedTheMove` below already replaced that pin's BEGIN
half behaviorally; this round did the same for the remaining launchers. Each ex-pin's replacement
DRIVES the launcher with `subprocess.run` patched and asserts the env the child is actually handed
carries the pin's markers, and asserts the argv is the one `pinned_module_argv` builds -- a comment
cannot satisfy either, and a rename or reformat cannot break either.

WHAT IS DELIBERATELY KEPT AS AN AST GUARD, and cannot be replaced by a behavioral test.
`NestedAwLaunchSiteGuardTests` enumerates launch SITES by parsing the module, which is a claim about
code that does not exist yet: it fails when someone ADDS an unpinned launcher, on a code path no test
drives. No behavioral test can assert a property of a call site nobody calls. A comment cannot satisfy
it either, because `ast.parse` does not see comments. `test_stdin_devnull_is_not_regressed` is the one
remaining `.count()` over source text and it is KEPT for the same reason, stated on the test itself.
"""

from __future__ import annotations

import ast
import inspect
import os
import subprocess
import sys
import sysconfig
import tempfile
import textwrap
import unittest
import unittest.mock
from pathlib import Path
from typing import ClassVar

from agent_workflows import agy_runipd
from agent_workflows import oc_runipd as driver
from agent_workflows import runner_shared

# WHY THE PROBE AND THE MEMO ARE NEUTRALIZED ON `runner_shared` AND NOT ON `driver` (runnerlayer
# Order 02 `1f7xno`, backlog `cnwy8g`). The pin's four public names and the five private ones they
# close over (`_AW_PIN_PROBE`, `_TOOL_IDENTITY_VERIFIED`, `runner_package_root`, `_AW_PIN_BOOTSTRAP`,
# `_AW_PIN_STRIP`) were CONSOLIDATED onto `runner_shared`, which already carried a byte-identical copy
# of each; `oc_runipd` re-exports them so every name below still resolves through `driver`.
#
# A RE-EXPORT IS NOT A PATCH POINT, and that is the whole reason these sites changed: rebinding
# `driver._AW_PIN_PROBE` replaces the host's ALIAS while the shared body keeps reading its own global,
# so the induced mismatch never fires and an `assertRaises(ToolIdentityError)` reports
# "ToolIdentityError not raised" - which is exactly how these tests failed when the consolidation
# landed. Neutralizing the OWNING module's global is what actually reaches the code under test.
#
# THE CONSOLIDATION ALSO FIXED A LIVE DEFECT (`232wcg`), which is worth knowing here because this file
# is where a tool-identity regression would surface: there were TWO `ToolIdentityError` classes, so
# `runner_shared.assert_child_tool_identity` raised one that neither host's `except ToolIdentityError`
# names, and the run-fatal ABORT-RUN escalation degraded to the item-local `except DriverError`.

PROBE = "import agent_workflows as a, os; print(os.path.realpath(a.__file__))"

# The two halves of the pin, named once so the guard and the runtime tests agree.
_SUPPRESS_MARKERS = ("_AW_PIN_BOOTSTRAP", "_AW_PIN_STRIP", "pinned_module_argv")
_SELECT_MARKERS = ("pinned_child_env",)


def _module_source(module) -> str:
    """Source text of `module`, with the `getsourcefile` Optional narrowed."""
    path = inspect.getsourcefile(module)
    assert path is not None, f"no source file for {module!r}"
    return Path(path).read_text(encoding="utf-8")


class _LaunchSpy:
    """Stands in for `subprocess.run`, recording the argv and kwargs a child was launched with.

    A CLASS rather than a closure, deliberately: every caller below records inside a loop, and a
    closure over a per-iteration dict is the `B023` late-binding trap, which in a test silently makes
    one iteration assert about another's launch.
    """

    def __init__(self, stdout: str = "ok", returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = ""
        self.argv: list[str] | None = None
        self.kwargs: dict = {}
        self.calls = 0

    def __call__(self, argv, **kwargs):
        self.calls += 1
        self.argv = list(argv)
        self.kwargs = kwargs
        return self

    @property
    def env(self) -> dict:
        return self.kwargs.get("env") or {}


class _CallRecorder:
    """Append-only ordered log of which patched collaborator ran, for call-ORDER assertions."""

    def __init__(self) -> None:
        self.order: list[str] = []

    def stub(self, label: str, result=None):
        """A callable that records `label` and returns `result`, ignoring its arguments."""

        def _stub(*_args, **_kwargs):
            self.order.append(label)
            return result

        return _stub


def _parent_module() -> str:
    """Realpath of the RUNNER's own `agent_workflows/__init__.py` (the pin target)."""
    return os.path.realpath(str(Path(driver.__file__).resolve().parent / "__init__.py"))


def _make_package(root: Path, marker: str, version: str) -> Path:
    """Create a minimal but distinguishable `agent_workflows` package under `root`."""
    pkg = root / "agent_workflows"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text(
        f"MARKER = {marker!r}\n__version__ = {version!r}\n", encoding="utf-8"
    )
    (pkg / "__main__.py").write_text(
        textwrap.dedent(
            """
            import agent_workflows, sys
            print("MARKER=" + agent_workflows.MARKER)
            sys.exit(42)
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return pkg


def _resolved_module(argv: list[str], cwd: Path, env: dict[str, str]) -> str:
    """Run an identity probe and return the module path the child actually imported."""
    result = subprocess.run(argv, cwd=str(cwd), env=env, capture_output=True, text=True)
    lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def _marker_of(path: str) -> str:
    """Read the MARKER out of whichever package copy was imported."""
    if not path or not os.path.exists(path):
        return "<none>"
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("MARKER"):
            return line.split("=", 1)[1].strip().strip("'\"")
    return "<real-package>"


class _Fixture:
    """A decoy in the child's cwd, a designated parent copy, and a third default-path copy."""

    def __init__(self, temp: Path) -> None:
        self.lane = temp / "lane"
        self.parent = temp / "parent"
        self.third = temp / "third"
        _make_package(self.lane, "DECOY-LANE", "0.0.0-decoy")
        _make_package(self.parent, "PARENT-RUNNER", "1.0.0-parent")
        _make_package(self.third, "THIRD-DEFAULTPATH", "2.0.0-third")

    def env(self, *, select: bool, extra_default: bool = True) -> dict[str, str]:
        """Child env. `select` adds the SELECTING half (the parent root on PYTHONPATH)."""
        env = os.environ.copy()
        parts = []
        if select:
            parts.append(str(self.parent))
        if extra_default:
            # Stands in for site-packages: reachable, but AFTER the selecting entry.
            parts.append(str(self.third))
        env["PYTHONPATH"] = os.pathsep.join(parts)
        return env


class LaneToolIdentityRuntimeTests(unittest.TestCase):
    """Prove the mechanism, in all four directions the plan requires."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.fx = _Fixture(Path(self._temp.name))
        self.addCleanup(self._temp.cleanup)

    #: The `flag` column: whether the launch carries the version-specific `-P`. Both values are
    #: needed, because `-P` and `PYTHONSAFEPATH` are BOTH CPython 3.11 features while the declared
    #: floor is 3.9 (measured on a real 3.9.25: `-P` is REJECTED and `PYTHONSAFEPATH=1` is SILENTLY
    #: IGNORED), so a pin that depended on either would leave every floor interpreter hijackable
    #: while looking green on 3.11+.
    #:
    #: AND THE COLUMN IS LOAD-BEARING ON THE NEGATIVE ROWS, which a first draft of this table got
    #: WRONG and a failing run corrected (audit 2026-09-19, on CPython 3.14.6). `-P` is ITSELF a
    #: suppressing mechanism: with the runner root on PYTHONPATH and `-P` passed, the child imports
    #: PARENT-RUNNER even with no bootstrap at all. So a row meant to demonstrate the defect must NOT
    #: pass `-P`, or the interpreter quietly fixes the very hijack the row exists to reproduce. This is
    #: exactly why the shipped pin cannot rely on `-P`: the mechanism that makes these rows pass on
    #: 3.11+ does not exist on the floor.
    WITH_FLAG = "with -P where available"
    NO_FLAG = "no interpreter flag (the 3.9 floor)"

    #: (case, does the launch SUPPRESS the cwd entry, does the env SELECT the runner root, is the
    #: default-path copy reachable, `-P` policy, the MARKER of the package that must be imported,
    #: why this row exists)
    RESOLUTIONS = (
        (
            "neither half: a bare interpreter launch from the lane cwd",
            False,
            True,
            True,
            NO_FLAG,
            "DECOY-LANE",
            "THE DEFECT ITSELF, REPRODUCED. This is the shipped pre-fix shape, and the row that makes "
            "every other row meaningful: without it a fixture that simply could not reach the decoy "
            "would satisfy all the positive rows. Note the env DOES select here, which is the point of "
            "the next row",
        ),
        (
            "SELECTION only: PYTHONPATH carries the runner root, nothing suppresses the cwd",
            False,
            True,
            True,
            NO_FLAG,
            "DECOY-LANE",
            "THE MEASURED HALF-PIN (finding F6), and the reason the fix needed two parts. BOTH drivers "
            "already prepended the runner's root to the child PYTHONPATH, which READ as this fix and "
            "was measurably INERT, because the cwd entry PRECEDES PYTHONPATH in sys.path. This row is "
            "identical to the one above on purpose: it shows the selecting half changes nothing alone",
        ),
        (
            "SUPPRESSION only: the cwd entry is stripped but nothing selects the runner",
            True,
            False,
            True,
            NO_FLAG,
            "THIRD-DEFAULTPATH",
            "WHY THE FIXTURE NEEDS A THIRD PACKAGE, and why the pin must be POSITIVE rather than "
            "merely not-the-lane. Suppression defeats the decoy and then falls through to the DEFAULT "
            "PATH, which equals the runner's own copy ONLY on an editable install (which this repo is). "
            "A two-package fixture would show this row as a PASS while a normal wheel install silently "
            "ran third-party code",
        ),
        (
            "BOTH halves: suppression plus selection",
            True,
            True,
            True,
            WITH_FLAG,
            "PARENT-RUNNER",
            "THE FIX, stated positively: the child imports the DESIGNATED PARENT copy, not merely "
            "something other than the lane's. This is the only row whose marker is the parent, so it "
            "is the only one that could be produced by a correct two-part pin",
        ),
        (
            "BOTH halves with NO interpreter flag, simulating the 3.9 floor",
            True,
            True,
            True,
            NO_FLAG,
            "PARENT-RUNNER",
            "CORRECTNESS MUST NOT DEPEND ON `-P`. It and `PYTHONSAFEPATH` are both 3.11 features and "
            "the declared floor is >=3.9 (CI runs 3.9-3.14), so this row is what proves the `-c` "
            "bootstrap alone carries the suppressing half. `-P` is kept as belt-and-braces upstream "
            "because it additionally blocks a cwd `sitecustomize.py`, which a post-startup filter "
            "cannot reach",
        ),
    )

    def test_the_pin_resolves_the_right_package_copy_in_every_combination(self):
        wrong: list[str] = []
        for (
            case,
            suppress,
            select,
            extra_default,
            flag_policy,
            expected_marker,
            why,
        ) in self.RESOLUTIONS:
            argv = [sys.executable]
            if flag_policy == self.WITH_FLAG and sys.version_info >= (3, 11):
                argv.append("-P")
            bootstrap = driver._AW_PIN_STRIP if suppress else ""
            argv.extend(["-c", bootstrap + PROBE])
            got = _resolved_module(
                argv,
                self.fx.lane,
                self.fx.env(select=select, extra_default=extra_default),
            )
            marker = _marker_of(got)
            if marker != expected_marker:
                wrong.append(
                    f"  {case} ({flag_policy}):\n"
                    f"    - expected the child to import {expected_marker}, it imported "
                    f"{marker} ({got!r})\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the tooling pin resolved the wrong package copy in {len(wrong)} of "
            f"{len(self.RESOLUTIONS)} combinations. THE NEGATIVE ROWS AND THE POSITIVE ROWS SHARE THIS "
            "TABLE, and it is what makes the whole file non-vacuous: two rows must import the DECOY "
            "(reproducing the defect and the measured half-pin), one must import the THIRD copy "
            "(showing suppression alone picks the wrong package), and two must import the PARENT. A "
            "fixture in which the decoy were simply unreachable would satisfy every positive row while "
            "proving nothing at all. Read the grouping: every row importing PARENT-RUNNER means the "
            "fixture broke rather than the pin improving; a PARENT row importing DECOY-LANE means the "
            "pin is gone. FIX: the pin is SUPPRESSION (strip the cwd entry) plus SELECTION (the "
            "runner's root on PYTHONPATH), and neither half works alone.\n"
            + "\n".join(wrong),
        )

    def test_the_decoys_CLI_really_would_have_run_not_merely_been_importable(self):
        """Kept separate: it runs the decoy's `__main__`, a different surface from the import probe.

        The import probe shows which FILE resolves; this shows the hijacked package's CLI actually
        EXECUTES (its `__main__` prints its marker and exits 42), which is what makes the defect a
        control-plane problem rather than a curiosity.
        """
        result = subprocess.run(
            [sys.executable, "-m", "agent_workflows"],
            cwd=str(self.fx.lane),
            env=self.fx.env(select=True),
            capture_output=True,
            text=True,
        )
        self.assertIn(
            "MARKER=DECOY-LANE",
            result.stdout,
            "the unpinned `-m` form must be shown to EXECUTE the lane's copy, not merely to import "
            f"it; got {result.stdout!r} {result.stderr!r}",
        )

    def test_real_pinned_argv_runs_the_runners_own_cli_from_a_decoy_cwd(self):
        """End-to-end at unit level: the SHIPPED helpers defeat a decoy in the cwd.

        The decoy's `__main__` exits 42 and prints its marker, so a hijack is unmistakable.
        """
        argv = driver.pinned_module_argv(["--version"])
        result = subprocess.run(
            argv,
            cwd=str(self.fx.lane),
            env=driver.pinned_child_env(),
            capture_output=True,
            text=True,
        )
        self.assertNotIn("MARKER=DECOY-LANE", result.stdout + result.stderr)
        self.assertEqual(
            result.returncode,
            0,
            f"pinned `aw --version` should succeed; got {result.returncode}: "
            f"{result.stdout}{result.stderr}",
        )
        self.assertIn("agent-workflows", result.stdout)

    def test_pinned_child_resolves_to_exactly_the_parent_module(self):
        """POSITIVE identity: child module path EQUALS the parent's, from a decoy cwd."""
        argv = (
            [sys.executable]
            + (["-P"] if sys.version_info >= (3, 11) else [])
            + ["-c", runner_shared._AW_PIN_PROBE]
        )
        got = _resolved_module(
            [sys.executable]
            + (["-P"] if sys.version_info >= (3, 11) else [])
            + ["-c", driver._AW_PIN_STRIP + PROBE],
            self.fx.lane,
            driver.pinned_child_env(),
        )
        self.assertEqual(
            os.path.realpath(got),
            _parent_module(),
            "the pinned child must import the RUNNER's OWN copy, not merely something other "
            f"than the lane's; imported {got!r}",
        )
        self.assertTrue(
            (self.fx.lane / "agent_workflows" / "__init__.py").exists(),
            "the decoy must have EXISTED and been ignored, else this proves nothing",
        )
        del argv

    # `test_pin_does_not_depend_on_the_version_specific_flag` was FOLDED IN (audit 2026-09-19) as the
    # `RESOLUTIONS` table's "BOTH halves with NO interpreter flag" row, which drives the identical
    # launch. Its reasoning survives in that row's `why` string and in the `flag` column's own note.

    def test_bootstrap_strips_the_absolute_cwd_not_just_empty_string(self):
        """Under `-m`, sys.path[0] is the ABSOLUTE cwd, so filtering only ''/'.' is inert.

        MEASURED AND STRENGTHENED (audit 2026-09-19). Two problems were found by mutation-testing the
        shipped form of this test.

        FIRST, `assertIn("realpath", driver._AW_PIN_STRIP)` is a source-text pin on a string CONSTANT,
        satisfiable by any use of the word. DELETED.

        SECOND, and worse, the behavioral half was VACUOUS: launched with `-c`, `sys.path[0]` is `''`
        rather than the absolute cwd, so `os.getcwd() in sys.path` is already False before the bootstrap
        runs. Mutating the product to filter only `{'', os.curdir}` -- removing the absolute-cwd strip
        this test is named for -- left the whole file GREEN.

        WHAT MAKES IT BITE: the absolute lane path is placed ON `PYTHONPATH` as well, which is the
        realistic shape (a parent that exports its own cwd, or a nested launch inheriting one) and the
        one where the strip is load-bearing. Measured with the weakened filter, the child imports
        DECOY-LANE; with the shipped filter it imports the parent. Both halves are asserted here.
        """
        probe = driver._AW_PIN_STRIP + (
            "import sys, os\n"
            "print('cwd_in_path=' + str(os.path.realpath(os.getcwd()) in "
            "[os.path.realpath(p) for p in sys.path if p]))\n"
            "import agent_workflows as a\n"
            "print('MARKER=' + getattr(a, 'MARKER', '<real-package>'))\n"
        )
        env = self.fx.env(select=True)
        # THE ABSOLUTE LANE PATH ON PYTHONPATH, which is what a filter of only ''/'.' cannot remove.
        env["PYTHONPATH"] = os.pathsep.join([str(self.fx.lane), env["PYTHONPATH"]])
        env["AW_PIN_KEEP_ROOT"] = str(self.fx.parent)
        result = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=str(self.fx.lane),
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertIn(
            "cwd_in_path=False",
            result.stdout,
            "the bootstrap must remove the ABSOLUTE cwd from sys.path, not only '' and '.'; under "
            f"`-m` the cwd entry IS the absolute path. Got {result.stdout!r} {result.stderr!r}",
        )
        self.assertIn(
            "MARKER=PARENT-RUNNER",
            result.stdout,
            "and the CONSEQUENCE, which is what makes the assertion above non-vacuous: with the lane's "
            "absolute path reachable, a filter of only ''/'.' leaves the child importing the LANE's "
            f"copy. Got {result.stdout!r}",
        )


class ConsoleScriptFallbackTests(unittest.TestCase):
    """E-06: the bare-`aw` fallback carries no interpreter flag, and does not need one."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.fx = _Fixture(Path(self._temp.name))
        self.addCleanup(self._temp.cleanup)

    def test_console_script_is_immune_to_a_cwd_decoy(self):
        """A console script puts its OWN dir, not the cwd, at the head of sys.path.

        Pins the MEASURED reason the fallback is safe, so the guard does not report it as an
        unpinned hole and a future reader does not delete it believing it is the hijack vector.
        """
        scripts = sysconfig.get_path("scripts")
        aw = Path(scripts) / "aw"
        if not aw.exists():
            self.skipTest(f"no `aw` console script installed at {aw}")
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [str(aw), "--version"],
            cwd=str(self.fx.lane),
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertNotIn("MARKER=DECOY-LANE", result.stdout + result.stderr)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("agent-workflows", result.stdout)

    def test_the_m_form_from_the_same_cwd_would_have_been_hijacked(self):
        """The contrast that makes the previous test meaningful, measured side by side."""
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "--version"],
            cwd=str(self.fx.lane),
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertIn(
            "MARKER=DECOY-LANE",
            result.stdout,
            "the unpinned -m form must be shown hijackable from the same cwd where the console "
            f"script is safe; got {result.stdout!r} {result.stderr!r}",
        )


def _classify_sites(module) -> list[dict]:
    """Enumerate nested-`aw` launch sites in `module` DYNAMICALLY and classify each.

    Enumerating dynamically (rather than hardcoding a count) means a new call site cannot be
    added silently, and a drifting site count cannot falsify the guard. Kinds:
      - `module-pinned`   : built by `pinned_module_argv` (the correct shape)
      - `module-pinned-injected` : built by an INJECTED `argv_builder` parameter, which is the shape a
        launcher takes once it lives in `runner_shared` (rununify 05 `ct4w0a`). It counts as PINNED
        here, and it has to, or moving a launcher into the shared module would look like deleting one.
        WHAT THIS KIND CANNOT SEE, stated because it is the honest limit of a source classifier: it
        proves the argv is built by whatever the caller injected, NOT that the caller injected the real
        pin. That second half is asserted separately, and behaviorally, by
        `TheBeginPinSurvivedTheMove`, which checks each host binds `pinned_module_argv`/
        `pinned_child_env` AND that the resulting child env really carries the pin's markers.
      - `module-unpinned` : a raw `[sys.executable, "-m", "agent_workflows", ...]` (a HOLE)
      - `console-script`  : a bare `["aw", ...]` fallback (immune; see E-06)
    """
    tree = ast.parse(_module_source(module))
    sites: list[dict] = []
    for node in ast.walk(tree):
        # Raw module launches: a list literal starting with sys.executable.
        if isinstance(node, ast.List):
            rendered = ast.unparse(node)
            if "sys.executable" in rendered and "'-m'" in rendered.replace('"', "'"):
                if "agent_workflows" in rendered:
                    sites.append(
                        {
                            "kind": "module-unpinned",
                            "line": node.lineno,
                            "src": rendered[:80],
                        }
                    )
            elif rendered.replace('"', "'").lstrip("[").startswith("'aw'"):
                sites.append(
                    {
                        "kind": "console-script",
                        "line": node.lineno,
                        "src": rendered[:80],
                    }
                )
        # Pinned module launches: a call to the shared helper, or to the injected builder that
        # stands in for it inside `runner_shared` (see the `module-pinned-injected` note above).
        if isinstance(node, ast.Call):
            func = ast.unparse(node.func)
            if func.endswith("pinned_module_argv"):
                sites.append(
                    {"kind": "module-pinned", "line": node.lineno, "src": func}
                )
            elif func.endswith("argv_builder"):
                sites.append(
                    {
                        "kind": "module-pinned-injected",
                        "line": node.lineno,
                        "src": func,
                    }
                )
    return sites


# The kinds that count as PINNED. Named once, so a guard cannot count one shape and forget the other.
_PINNED_KINDS = ("module-pinned", "module-pinned-injected")


class NestedAwLaunchSiteGuardTests(unittest.TestCase):
    """E-03: no launch site may be added, or half-pinned, without failing this guard."""

    DRIVERS = (("oc_runipd", driver), ("agy_runipd", agy_runipd))

    def test_no_unpinned_module_launch_sites_remain(self):
        """Every `-m agent_workflows` launch must go through the shared pinned helper."""
        for name, module in self.DRIVERS:
            sites = _classify_sites(module)
            holes = [s for s in sites if s["kind"] == "module-unpinned"]
            self.assertEqual(
                holes,
                [],
                f"{name} has unpinned nested-`aw` launch site(s); each would resolve "
                f"`agent_workflows` from the cwd (the lane): {holes}",
            )

    def test_every_site_is_classified_and_none_unknown(self):
        """The guard must account for EVERY site, with none left unclassified.

        RE-BASED ONTO THE OWNER SET by rununify 05 (`ct4w0a`) E-03, for the SAME reason the maintainer's
        OQ-03 ruling re-based the ttywedge guards: a total keyed to the DRIVER FILES needs an edit every
        time a symbol moves into `runner_shared`, and each such edit is a chance to weaken it. The total
        asserted here is UNCHANGED; what changed is that the shared module's pinned launches now COUNT
        toward it, which they must, because they are the very sites the ruling moved.

        RE-BASED AGAIN by hostdedup Order 01 (`li44r9`) E-07, and this is the LOGICAL CONCLUSION of the
        rununify re-base rather than a new concession. That plan lifted the launch BODIES into
        `runner_shared` and moved the count with them; this one finishes the job for the remaining
        byte-identical launchers (`set_plan_approved`, `driver_finalize`), so the per-driver assertions
        below ("expected to find sites", "at least one PINNED site", "exactly ONE console-script
        fallback") now describe a state no host is in: measured at execution HEAD, oc holds 2 pinned
        sites and agy holds ZERO, because every launcher agy still exposes is a delegation.

        SO THE PER-DRIVER SHAPE ASSERTIONS MOVE TO THE OWNER SET, WHERE THE SITES ACTUALLY ARE, and the
        two properties they existed to protect are asserted THERE rather than dropped:
          * exactly ONE console-script fallback exists across the owner set (it is `set_plan_approved`'s,
            and a second one appearing anywhere would mean a new unpinned-by-design launch); and
          * at least one PINNED module launch site exists.
        The CLASSIFICATION assertion stays PER DRIVER and is the half that must never move: a driver that
        grows a NEW launch site of any kind is still checked here, and an UNPINNED one still fails
        `test_no_unpinned_module_launch_sites_remain` next door, which is the assertion that actually
        guards the defect (`af7i6p`'s lane-shadowed launch) and is untouched by this lift.

        The total is asserted as a FLOOR over the owner set plus the drivers, so it cannot be satisfied
        by deleting sites.
        """
        total = 0
        shared_sites = _classify_sites(runner_shared)
        for site in shared_sites:
            self.assertIn(
                site["kind"],
                {*_PINNED_KINDS, "module-unpinned", "console-script"},
                f"runner_shared: unclassified site {site}",
            )
        total += len(shared_sites)
        all_sites = list(shared_sites)
        for name, module in self.DRIVERS:
            sites = _classify_sites(module)
            for site in sites:
                self.assertIn(
                    site["kind"],
                    {*_PINNED_KINDS, "module-unpinned", "console-script"},
                    f"{name}: unclassified site {site}",
                )
            total += len(sites)
            all_sites.extend(sites)
        pinned = [s for s in all_sites if s["kind"] in _PINNED_KINDS]
        console = [s for s in all_sites if s["kind"] == "console-script"]
        self.assertTrue(
            pinned,
            "expected at least one PINNED module launch site across the owner set",
        )
        self.assertEqual(
            len(console),
            1,
            "expected exactly one console-script fallback across the owner set "
            f"(it is `set_plan_approved`'s); got {console}",
        )
        self.assertGreaterEqual(total, 6, f"expected >=6 classified sites, saw {total}")

    def test_guard_fails_on_an_injected_unpinned_site(self):
        """The guard must FAIL when a new unpinned call site is injected."""
        injected = textwrap.dedent(
            """
            import subprocess, sys
            def sneaky(repo):
                cmd = [sys.executable, "-m", "agent_workflows", "ipd", "set", "executed"]
                return subprocess.run(cmd, cwd=str(repo))
            """
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "injected.py"
            path.write_text(injected, encoding="utf-8")
            tree = ast.parse(injected)
            holes = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.List)
                and "sys.executable" in ast.unparse(node)
                and "agent_workflows" in ast.unparse(node)
            ]
            self.assertTrue(
                holes,
                "the guard's detector must recognise an injected unpinned launch site; if this "
                "fails the guard cannot protect the real drivers either",
            )

    def test_identity_probe_is_not_counted_as_a_nested_aw_launcher(self):
        """The E-04 probe must not create a false 4-vs-3 asymmetry in the ttywedge guard.

        `tests/test_nested_tty_noninteractive.py` enumerates nested-`aw` launchers by their first
        argument's NAME (`argv`/`cmd`) and asserts both drivers expose an EQUAL count. The identity
        probe is a read-only import probe defined once in oc and merely IMPORTED by agy, so naming
        its local `argv` made oc appear to have one more launcher than agy and broke that sibling
        guard. It must stay distinctly named -- while still denying the child a terminal.

        KEPT AS AN AST CHECK, not converted, because the property IS the parameter NAME the sibling
        guard keys on. A behavioral test cannot observe a local variable's name, and the sibling guard
        counts by that name, so the only faithful assertion is over the syntax tree. The DEVNULL half
        is now driven behaviorally instead, by `TheProbeDeniesTheChildATerminal` below.
        """
        tree = ast.parse(
            textwrap.dedent(inspect.getsource(driver.assert_child_tool_identity))
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and ast.unparse(node.func).endswith(
                "subprocess.run"
            ):
                first = ast.unparse(node.args[0]) if node.args else ""
                self.assertNotIn(
                    first,
                    ("argv", "cmd"),
                    "the identity probe's first arg must not be named argv/cmd, or the ttywedge "
                    "symmetry guard will miscount it as a nested-`aw` launcher",
                )

    def test_stdin_devnull_is_not_regressed(self):
        """The g40w37 TTY guarantee must survive this change at every launch site.

        COUNTED ACROSS THE OWNER SET, not per driver file, since rununify Order 02 (`818uru` E-05).
        `run_checked` carried one of each driver's launch sites and now has ONE definition in
        `runner_shared`, so each driver's own file legitimately shows one fewer. The THRESHOLD IS
        DELIBERATELY UNCHANGED at 3: lowering it would silently accept a future regression that
        actually deleted a DEVNULL site, which is the opposite of what this guard is for. The
        guarantee is intact (the same `subprocess.run` call still passes `stdin=subprocess.DEVNULL`);
        only its address moved.

        KEPT (audit 2026-09-19) as the file's one remaining source-text count, and the reason is the
        same one that keeps the AST site guard above: this asserts a property of launch sites
        COLLECTIVELY, including sites no test drives, so a behavioral test over the launchers this file
        can reach would be a strictly weaker claim rather than a replacement. Every launcher this file
        CAN drive now has its DEVNULL asserted behaviorally too
        (`LaunchersPassThePinToTheRealChild` and `TheProbeDeniesTheChildATerminal` below), so the
        remaining value of the count is precisely the sites those cannot reach.
        """
        from agent_workflows import runner_shared

        shared_sites = _module_source(runner_shared).count("stdin=subprocess.DEVNULL")
        for name, module in self.DRIVERS:
            src = _module_source(module)
            self.assertGreaterEqual(
                src.count("stdin=subprocess.DEVNULL") + shared_sites,
                3,
                f"{name} (together with the shared `runner_shared` launch sites it "
                "delegates to) must keep stdin=subprocess.DEVNULL at its subprocess "
                "launches (ttywedge g40w37); the pin must not disturb it",
            )

    def test_both_drivers_share_one_definition_of_the_pin(self):
        """E-05: ONE definition, not a per-driver copy. A second copy is how the half-pin drifted.

        THE `assertNotIn` HALVES WERE REPLACED (audit 2026-09-19) by
        `LaunchersPassThePinToTheRealChild::test_no_launcher_rebuilds_the_pin_for_itself`, which patches
        the shared builder to an UNPINNED stub and asserts the pin does NOT reappear in the env the
        child is handed. `assertNotIn("def pinned_child_env", agy_src)` could only ever say the words
        were not typed; the replacement says a second copy is not REACHED, which is the property.
        """
        self.assertIs(
            agy_runipd.pinned_module_argv,
            driver.pinned_module_argv,
            "agy must reuse oc's pinned_module_argv, not reimplement it",
        )
        self.assertIs(
            agy_runipd.pinned_child_env,
            driver.pinned_child_env,
            "agy must reuse oc's pinned_child_env, not reimplement it",
        )

    def test_both_drivers_are_fixed_symmetrically_over_existing_sites(self):
        """Symmetry WITHOUT requiring equal site counts.

        oc has four module-launch sites to agy's three, because oc alone has
        `finalize_orchestrator`. That asymmetry is expected and must NOT be "fixed" by inventing
        a fourth agy site, so symmetry is asserted over the sites that EXIST.

        THE COUNTS ARE NOW OWNER-SET COUNTS (rununify 05 `ct4w0a` E-03, per the OQ-03 ruling): each
        host's own pinned sites PLUS the pinned sites in `runner_shared` that it reaches through a
        wrapper. `driver_begin`'s argv construction moved there, so agy's own count fell from 3 to 2 and
        oc's from 4 to 3 while NOT ONE launch became unpinned. THE THRESHOLDS ARE UNCHANGED at 4 and 3,
        which is what makes this a re-base and not a weakening: with the shared sites counted, a host
        that really lost a pinned launcher still fails.

        THE `assertIn("af7i6p", src)` PROVENANCE PIN WAS DELETED (audit 2026-09-19). It asserted that
        a plan id appeared SOMEWHERE in a 7000-line module, which is satisfiable by any comment and is
        satisfied by this module's own docstrings; it constrained no behavior and would fail on a
        comment reflow. The pin it was standing in for -- that the pin is really present and really
        reaches the child -- is now asserted behaviorally by
        `LaunchersPassThePinToTheRealChild` below.
        """
        shared_pinned = [
            s for s in _classify_sites(runner_shared) if s["kind"] in _PINNED_KINDS
        ]
        self.assertTrue(
            shared_pinned,
            "the shared module must hold at least one PINNED launch site; if it holds none, the "
            "counts below have silently reverted to per-file and the re-base is undone",
        )
        oc_pinned = [s for s in _classify_sites(driver) if s["kind"] in _PINNED_KINDS]
        agy_pinned = [
            s for s in _classify_sites(agy_runipd) if s["kind"] in _PINNED_KINDS
        ]
        self.assertGreaterEqual(
            len(oc_pinned) + len(shared_pinned),
            4,
            f"oc pinned sites: {oc_pinned} plus shared: {shared_pinned}",
        )
        self.assertGreaterEqual(
            len(agy_pinned) + len(shared_pinned),
            3,
            f"agy pinned sites: {agy_pinned} plus shared: {shared_pinned}",
        )
        self.assertFalse(
            hasattr(agy_runipd, "finalize_orchestrator"),
            "agy is not expected to have finalize_orchestrator; if it gained one, assert its "
            "pin explicitly rather than letting the symmetry check pass by accident",
        )


class ToolIdentityAssertionTests(unittest.TestCase):
    """E-04: residual mismatch must be a loud, recorded, RUN-FATAL refusal."""

    def setUp(self) -> None:
        runner_shared._TOOL_IDENTITY_VERIFIED.clear()
        self.addCleanup(runner_shared._TOOL_IDENTITY_VERIFIED.clear)

    def test_matching_child_passes_and_records_once(self):
        with tempfile.TemporaryDirectory() as temp:
            events = Path(temp) / "events.jsonl"
            record = driver.assert_child_tool_identity(events, cwd=Path(temp))
            self.assertEqual(record["event"], "tool-identity-verified")
            self.assertEqual(record["child_module"], _parent_module())
            self.assertTrue(
                events.exists(), "the outcome must be recorded in the run ledger"
            )
            first = events.read_text(encoding="utf-8")
            # Memoized: a second call must not re-probe or re-record.
            driver.assert_child_tool_identity(events, cwd=Path(temp))
            self.assertEqual(
                first,
                events.read_text(encoding="utf-8"),
                "the check must be memoized per process, not repeated per nested call",
            )

    def test_mismatch_raises_and_is_recorded(self):
        """A deliberately mismatched child must abort with the named diagnostic."""
        with tempfile.TemporaryDirectory() as temp:
            events = Path(temp) / "events.jsonl"
            original = runner_shared._AW_PIN_PROBE
            # Force the probe to report a foreign module path.
            runner_shared._AW_PIN_PROBE = (
                "print('/somewhere/else/agent_workflows/__init__.py')\n"
            )
            try:
                with self.assertRaises(driver.ToolIdentityError) as ctx:
                    driver.assert_child_tool_identity(events, cwd=Path(temp))
            finally:
                runner_shared._AW_PIN_PROBE = original
            message = str(ctx.exception)
            self.assertIn("ABORTING RUN", message)
            self.assertIn("tool-identity mismatch", message)
            self.assertIn("/somewhere/else/agent_workflows/__init__.py", message)
            self.assertIn("tool-identity-mismatch", events.read_text(encoding="utf-8"))

    def test_the_mismatch_diagnostic_is_the_shipped_renderer_not_a_copy(self):
        """The message must NAME what it compared, so an operator can act without reading code.

        Kept separate from the raising test above (which is an `assertRaises`): this asserts the
        CONTENT of the diagnostic on the SAME induced mismatch, and does so by recomputing the two
        paths independently rather than by matching a fixed sentence.
        """
        with tempfile.TemporaryDirectory() as temp:
            events = Path(temp) / "events.jsonl"
            original = runner_shared._AW_PIN_PROBE
            foreign = "/somewhere/else/agent_workflows/__init__.py"
            runner_shared._AW_PIN_PROBE = f"print({foreign!r})\n"
            try:
                with self.assertRaises(driver.ToolIdentityError) as ctx:
                    driver.assert_child_tool_identity(events, cwd=Path(temp))
            finally:
                runner_shared._AW_PIN_PROBE = original
            message = str(ctx.exception)
            self.assertIn(_parent_module(), message, "must name what it EXPECTED")
            self.assertIn(foreign, message, "must name what it GOT")
            self.assertIn(temp, message, "must name the cwd it probed from")


class TheBeginPinSurvivedTheMove(unittest.TestCase):
    """rununify 05 (`ct4w0a`) E-03: the `af7i6p` pin at the BEGIN site, asserted by BEHAVIOR.

    OQ-03 required that the `env=pinned_child_env()` pin "survive the move" rather than be deleted.
    The literal cannot survive VERBATIM: `driver_begin` now has one definition in `runner_shared` that
    receives its env builder as an injected parameter, so the shared body spells it `env_builder()`.
    Searching the shared source for `env_builder(` would prove nothing about the pin, so what replaces
    the text search is the PROPERTY the text was standing in for, in two halves: each host BINDS the
    real `pinned_child_env`, and the env the shared launcher actually hands the child CARRIES the pin.

    THE REPLACEMENT IS STRICTLY STRONGER, AND THAT IS MEASURED RATHER THAN CLAIMED. The old assertion
    read `inspect.getsource(driver_begin)` and searched for a LITERAL, so a COMMENT satisfied it -- and
    on `oc_runipd` a comment is precisely what satisfied it at this plan's execution HEAD (1171f7b2).
    oc's code read `env={**pinned_child_env(), **begin_baseline_env(isolated)}`, which does NOT contain
    the substring `env=pinned_child_env()`; the only match in that function was the explanatory comment
    ABOVE it, which said the literal was kept visible deliberately for this guard. So the shipped guard
    was already passing on oc for a reason unrelated to the pin. That measurement used to be pinned by a
    test that re-read a hardcoded historical commit; it is retired, because a test asserting a fact about
    a DELETED test's vacuity guards no present behavior. The measurement survives in this docstring and
    in git history, which is where a historical fact belongs.
    """

    HOSTS = (("oc_runipd", driver), ("agy_runipd", agy_runipd))

    def _injected_kwargs(self, module) -> dict:
        """The kwargs `module.driver_begin` hands the SHARED launcher, captured from a real call."""
        captured: dict = {}

        def spy(_repo, _id6, _actor, **kwargs):
            captured.update(kwargs)
            return (0, "ok")

        with unittest.mock.patch.object(runner_shared, "driver_begin", spy):
            rc, _msg = module.driver_begin(
                Path("/nonexistent"), "aaa111", "actor", isolated=True
            )
        self.assertEqual(
            rc,
            0,
            f"{module.__name__}.driver_begin must delegate to the shared launcher; if it stopped, "
            "the injected-pin assertions below cannot see anything",
        )
        return captured

    def test_each_host_injects_the_ONE_shared_pin_object_into_the_shared_launcher(self):
        """Half one, by OBJECT IDENTITY on a real call rather than by reading the call's source.

        REPLACES a source search for `env_builder=pinned_child_env` (audit 2026-09-19). That search is
        the exact shape this file's docstring records as satisfiable by a COMMENT. Here the shared
        launcher is patched with a spy, each host's wrapper is really CALLED, and the objects it handed
        over are compared with `assertIs` to the one shared definition. A second copy of the pin, a
        stub, or a host that stopped injecting at all fails; a rename or reformat does not.
        """
        for name, module in self.HOSTS:
            with self.subTest(host=name):
                captured = self._injected_kwargs(module)
                self.assertIs(
                    captured.get("env_builder"),
                    driver.pinned_child_env,
                    f"{name}.driver_begin must inject the ONE shared pinned_child_env object, not "
                    "a second copy and not a stub",
                )
                self.assertIs(
                    captured.get("argv_builder"),
                    driver.pinned_module_argv,
                    f"{name}.driver_begin must inject the ONE shared pinned_module_argv object",
                )
                self.assertTrue(
                    captured.get("isolated"),
                    f"{name}.driver_begin must pass the isolated declaration through; agy's own "
                    "copy silently lacked it before ct4w0a",
                )

    def test_the_env_handed_to_the_begin_child_actually_carries_the_pin(self):
        """Half two, and the load-bearing half: the child env really contains the pin's markers.

        DRIVEN THROUGH THE REAL LAUNCHER (audit 2026-09-19), where this previously rebuilt the env by
        hand and asserted about the reconstruction. `subprocess.run` is patched, so the env asserted
        here is byte-for-byte the mapping the shared launcher hands a child, on BOTH hosts and in both
        isolation modes. It fails if the pin stops REACHING the child, which is the property the
        `af7i6p` lane-shadowing incident bought.
        """
        root = driver.runner_package_root()
        prefix = driver.pinned_module_argv([])
        for name, module in self.HOSTS:
            for isolated in (False, True):
                with self.subTest(host=name, isolated=isolated):
                    spy = _LaunchSpy()
                    with unittest.mock.patch.object(
                        runner_shared.subprocess, "run", spy
                    ):
                        module.driver_begin(
                            Path("/nonexistent"), "aaa111", "actor", isolated=isolated
                        )
                    self.assertEqual(
                        spy.calls,
                        1,
                        "the shared launcher must launch exactly one child",
                    )
                    self.assertEqual(
                        spy.env.get("AW_PIN_KEEP_ROOT"),
                        root,
                        "the suppressing half must be told which root to keep",
                    )
                    self.assertIn(
                        root,
                        spy.env.get("PYTHONPATH", "").split(os.pathsep),
                        "the selecting half must put the runner's own root on PYTHONPATH",
                    )
                    assert spy.argv is not None
                    self.assertEqual(
                        spy.argv[: len(prefix)],
                        prefix,
                        "the argv prefix must be exactly what the shared pinned builder produces, "
                        "so the SUPPRESSING half really reaches the child",
                    )
                    self.assertEqual(
                        spy.kwargs.get("stdin"),
                        subprocess.DEVNULL,
                        "the begin child must still be denied a terminal (ttywedge g40w37)",
                    )

    def test_an_unpinned_env_builder_is_detectable(self):
        """Non-vacuity, MEASURED THROUGH THE LAUNCHER: an injected regression must be visible.

        The control is a builder that really drops the pin, handed to the SAME shared launcher the
        test above drives, so this proves the previous assertion can fail rather than asserting about
        a dict assembled in this file.
        """
        stripped = {
            k: v
            for k, v in os.environ.items()
            if k not in ("AW_PIN_KEEP_ROOT", "PYTHONPATH")
        }
        spy = _LaunchSpy()
        with unittest.mock.patch.object(runner_shared.subprocess, "run", spy):
            runner_shared.driver_begin(
                Path("/nonexistent"),
                "aaa111",
                "actor",
                env_builder=lambda: dict(stripped),
                argv_builder=lambda args: ["true", *args],
            )
        self.assertIsNone(
            spy.env.get("AW_PIN_KEEP_ROOT"),
            "the control must really be unpinned, or this proves nothing",
        )
        self.assertNotIn(
            driver.runner_package_root(),
            spy.env.get("PYTHONPATH", "").split(os.pathsep),
            "an unpinned builder must NOT satisfy the assertion the previous test makes",
        )


class LaunchersPassThePinToTheRealChild(unittest.TestCase):
    """The ex-source-text pins, REPLACED: each launcher's pin asserted on the child it launches.

    WHAT WAS DELETED AND WHY (audit 2026-09-19). Three pins searched a function's source text:
    `driver_finalize` had to contain `pinned_module_argv` and the literal `env=pinned_child_env()`;
    `run_checked` had to contain `pinned_child_env` and must not contain `repo_src`; and each driver's
    module source had to contain one marker from each half of the pin. Every one of them is the shape
    this file's own docstring records as MEASURED to be satisfiable by a comment.

    WHAT REPLACES THEM, and why it is strictly stronger. `subprocess.run` is patched at the module that
    actually performs the launch, the launcher is CALLED, and the assertions are on what the child
    receives: the argv is compared to what `pinned_module_argv` itself builds, and the env must carry
    BOTH halves of the pin (`AW_PIN_KEEP_ROOT` and the runner root on `PYTHONPATH`). A comment cannot
    put a key in an env dict, and a rename cannot break these.

    THE LAUNCHER IS A ROW AND THE HOST IS A COLUMN, because every one of these was one call and two
    assertions differing only in which function was launched. `finalize_orchestrator` is `oc`-only by
    design (see `test_both_drivers_are_fixed_symmetrically_over_existing_sites`), which is why the row
    carries the set of hosts that must have it rather than a separate class.
    """

    #: The `expect_pinned_argv` column's two values. A nested `aw` MUST carry the suppressing
    #: bootstrap in its argv; a launcher whose child is plain `git` legitimately does not, and
    #: collapsing the distinction would let a nested `aw` pass as "well, it launched something".
    NESTED_AW = "argv must be the pinned bootstrap"
    PLAIN_GIT = "argv is a plain git call, no bootstrap expected"

    #: (launcher name, hosts that must expose it, the module whose `subprocess` performs the launch,
    #: a callable driving it, the argv expectation, why this row exists)
    LAUNCHERS = (
        (
            "driver_finalize",
            ("oc_runipd", "agy_runipd"),
            # OWNER RE-BASED FROM "driver" TO "shared" (hostdedup Order 01, `li44r9`, E-07), which is
            # exactly the remedy this table's own failure messages prescribe: "if it now launches
            # through a different module, update this row's owner column". `driver_finalize` was
            # byte-identical in both drivers and now has ONE definition in `runner_shared`, so the
            # `subprocess.run` this row observes happens there. THE CLAIM IS UNCHANGED and is still
            # asserted against the SAME argv and env rules; only the module whose `subprocess` is spied
            # moved. Nothing is exempted: both hosts still appear, and each still drives its OWN
            # wrapper, so a host that failed to bind its pin builders would still fail here.
            "shared",
            lambda module, repo: module.driver_finalize(
                repo, repo / "p.ipd.md", "aaa111", "actor", "message"
            ),
            NESTED_AW,
            (
                "THE PRIMARY LANE-SHADOWED SITE, and the whole reason `af7i6p` exists: its `repo` "
                "argument IS the lane worktree, so an unpinned launch here had the lane's own "
                "unreviewed `agent_workflows` perform the very transition meant to gate it. It is also "
                "the site whose source-text pin was MEASURED to be satisfied by a comment, since the "
                "real code spells the env `{**pinned_child_env(), **...}` and never as the "
                "searched-for literal"
            ),
        ),
        (
            "run_checked",
            ("oc_runipd", "agy_runipd"),
            "shared",
            lambda module, repo: module.run_checked(["git", "status"], cwd=repo),
            PLAIN_GIT,
            (
                "THE HIGH-TRAFFIC LAUNCHER (13 call sites in oc alone) and the one that USED to build "
                "its own PYTHONPATH prepend, which read as a pin and was measurably INERT because the "
                "cwd entry precedes PYTHONPATH in sys.path. It is driven here with a git argv, which "
                "is why its argv column is PLAIN_GIT: this row's claim is about the ENV it supplies "
                "to whatever it launches, since the argv is the caller's"
            ),
        ),
        (
            "finalize_orchestrator",
            ("oc_runipd",),
            "shared",
            lambda module, repo: module.finalize_orchestrator(
                repo, "aaa111", "message"
            ),
            NESTED_AW,
            (
                "THE oc-ONLY ASYMMETRY, pinned so it is covered rather than exempted. It builds a "
                "nested-`aw` argv and launches it THROUGH `run_checked`, so its env pin is INHERITED "
                "while its argv pin is its own -- which is exactly why it needs a row: a rewrite that "
                "gave it a bare `-m agent_workflows` argv would lose the suppressing half with no "
                "count changing and no other test noticing"
            ),
        ),
    )

    HOSTS: ClassVar[dict] = {"oc_runipd": driver, "agy_runipd": agy_runipd}

    def _drive(self, module, launcher_owner, drive):
        """Drive one launcher with `subprocess.run` patched at the module that performs the launch."""
        spy = _LaunchSpy()
        launch_module = module if launcher_owner == "driver" else runner_shared
        with (
            tempfile.TemporaryDirectory() as temp,
            unittest.mock.patch.object(
                module, "_compute_scope_reconciliation", lambda _r, _p: ({}, {})
            ),
            # STUBBED ON THE SHARED MODULE TOO (hostdedup Order 01, `li44r9`, E-07). The driver-level
            # stub above is kept because a host may still route through its own wrapper, but
            # `driver_finalize` now computes the reconciliation inside `runner_shared`, which calls
            # `compute_scope_reconciliation` DIRECTLY rather than through the driver's alias. Without
            # this second stub the launcher reaches the real `ipd_lifecycle.finalize_precheck` and dies
            # reading a plan file this fixture never writes, so the launch under test never happens.
            # This stubs a COLLABORATOR, not the thing asserted: the assertion is about the argv and env
            # handed to `subprocess.run`, which is downstream of it.
            unittest.mock.patch.object(
                runner_shared,
                "compute_scope_reconciliation",
                lambda _r, _p, **_kw: ({}, {}),
            ),
            unittest.mock.patch.object(launch_module.subprocess, "run", spy),
        ):
            drive(module, Path(temp))
        return spy

    def test_every_launcher_hands_its_child_a_pinned_argv_and_a_pinned_env(self):
        root = driver.runner_package_root()
        prefix = driver.pinned_module_argv([])
        wrong: list[str] = []
        driven = 0
        for launcher, hosts, owner, drive, argv_rule, why in self.LAUNCHERS:
            for host in hosts:
                module = self.HOSTS[host]
                problems: list[str] = []
                if not hasattr(module, launcher):
                    problems.append(
                        "the host does not expose this launcher at all, so its pin is unassertable; "
                        "if it legitimately moved, move the row's owner column rather than deleting "
                        "the row"
                    )
                else:
                    spy = self._drive(module, owner, drive)
                    if spy.calls == 0:
                        problems.append(
                            "the launcher never reached `subprocess.run`, so nothing was launched "
                            "and the pin cannot be observed; if it now launches through a different "
                            "module, update this row's owner column"
                        )
                    else:
                        driven += 1
                        if spy.env.get("AW_PIN_KEEP_ROOT") != root:
                            problems.append(
                                "the SUPPRESSING half is absent: the child was not told which root "
                                f"to keep (AW_PIN_KEEP_ROOT={spy.env.get('AW_PIN_KEEP_ROOT')!r}, "
                                f"expected {root!r}), so the bootstrap strips the runner's own root "
                                "along with the lane's cwd"
                            )
                        if root not in spy.env.get("PYTHONPATH", "").split(os.pathsep):
                            problems.append(
                                "the SELECTING half is absent: the runner's own package root is not "
                                f"on the child's PYTHONPATH ({spy.env.get('PYTHONPATH')!r}), so the "
                                "child resolves `agent_workflows` from the default path, which "
                                "equals the runner's own copy ONLY on an editable install"
                            )
                        if spy.kwargs.get("stdin") is not subprocess.DEVNULL:
                            problems.append(
                                "the child was not denied a terminal "
                                f"(stdin={spy.kwargs.get('stdin')!r}); ttywedge g40w37 measured a "
                                "nested `aw` wedging 1h49m on a prompt nobody could answer"
                            )
                        argv = spy.argv or []
                        if (
                            argv_rule == self.NESTED_AW
                            and argv[: len(prefix)] != prefix
                        ):
                            problems.append(
                                "the argv is NOT what `pinned_module_argv` builds, so this nested "
                                f"`aw` has no suppressing half: got {argv[:3]!r}, expected the "
                                f"prefix {prefix[:3]!r}"
                            )
                        if argv_rule == self.PLAIN_GIT and (
                            not argv or str(argv[0]) != "git"
                        ):
                            problems.append(
                                f"expected this row to launch a plain git child; got {argv[:3]!r}. "
                                "If the launcher now builds a nested `aw` itself, move the row to "
                                "NESTED_AW rather than relaxing it"
                            )
                if problems:
                    wrong.append(
                        f"  {launcher} on {host} ({argv_rule}):\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} launcher/host pair(s) ({driven} driven) do not hand their child the "
            "af7i6p tooling pin. THE PIN IS TWO HALVES AND NEITHER ALONE WORKS (measured with three "
            "distinguishable packages): suppression alone selects the DEFAULT-PATH copy, which equals "
            "the runner's own only on an editable install, and selection alone is INERT because the "
            "cwd entry precedes PYTHONPATH. Read the grouping: a SUPPRESSING-half failure on EVERY row "
            "means `pinned_child_env` stopped setting AW_PIN_KEEP_ROOT, so one shared definition broke "
            "for everyone; failures on ONE row mean that launcher alone stopped going through the "
            "shared builders, which is the drift a per-site fix causes. FIX: route the launch through "
            "`pinned_module_argv` + `pinned_child_env` (or through `run_checked`, which binds the env "
            "half), never by editing this table.\n" + "\n".join(wrong),
        )

    def test_no_launcher_rebuilds_the_pin_for_itself(self):
        """NON-VACUITY, and the replacement for `assertNotIn("repo_src", src)`.

        The shared builder is patched to an UNPINNED stub. If any launcher still carried its own
        PYTHONPATH prepend beside the shared one (the measured F6 half-pin, which read as a fix and was
        inert), the pin would REAPPEAR in the child env despite the stub. A text search for `repo_src`
        could only ever say one particular variable name was not typed.
        """
        for host, module in self.HOSTS.items():
            with self.subTest(host=host):
                spy = _LaunchSpy()
                with (
                    unittest.mock.patch.object(
                        module,
                        "pinned_child_env",
                        lambda env=None: {"PATH": "/usr/bin"},
                    ),
                    unittest.mock.patch.object(runner_shared.subprocess, "run", spy),
                ):
                    module.run_checked(["git", "status"], cwd=Path("/"))
                self.assertEqual(
                    spy.env,
                    {"PATH": "/usr/bin"},
                    f"{host}.run_checked must take its env ENTIRELY from the shared builder; an "
                    "extra key here means it rebuilt part of the pin itself, which is the F6 "
                    "half-pin that read as a fix and was measurably inert",
                )


class TheProbeDeniesTheChildATerminal(unittest.TestCase):
    """The E-04 identity probe's own launch contract, asserted on the launch rather than in source.

    REPLACES the `assertIn("stdin=subprocess.DEVNULL", src)` half of the probe-naming guard and the
    `assertIn("child_module"/"expected_module", src)` pins (audit 2026-09-19). Each was a substring
    search over one function; a comment satisfies all three. The NAME half of the probe guard stays an
    AST check, because the property there genuinely IS a parameter name (see that test).
    """

    def setUp(self) -> None:
        runner_shared._TOOL_IDENTITY_VERIFIED.clear()
        self.addCleanup(runner_shared._TOOL_IDENTITY_VERIFIED.clear)

    def test_the_probe_is_launched_pinned_with_no_terminal(self):
        spy = _LaunchSpy(stdout=_parent_module() + "\n1.2.3\n")
        with (
            tempfile.TemporaryDirectory() as temp,
            unittest.mock.patch.object(driver.subprocess, "run", spy),
        ):
            record = driver.assert_child_tool_identity(
                Path(temp) / "events.jsonl", cwd=Path(temp)
            )
        self.assertEqual(
            spy.kwargs.get("stdin"),
            subprocess.DEVNULL,
            "the probe must deny the child a terminal (ttywedge g40w37)",
        )
        self.assertEqual(
            spy.env.get("AW_PIN_KEEP_ROOT"),
            driver.runner_package_root(),
            "the probe must run under the SAME pin a real nested `aw` gets, or it measures a "
            "different child than the one the runner will launch",
        )
        assert spy.argv is not None
        self.assertIn(
            "-c", spy.argv, "the probe launches the suppressing bootstrap via -c"
        )
        self.assertEqual(record["event"], "tool-identity-verified")

    def test_the_PATH_is_the_primary_signal_and_the_version_is_only_context(self):
        """The version is git-describe derived and can COLLIDE; the path cannot.

        Driven in BOTH directions on the same function, which is what makes the claim meaningful: a
        matching path with a wildly different version PASSES, and a matching version with a different
        path RAISES. The source pins this replaces (`assertIn("child_module", src)`) could not tell
        those two cases apart at all.
        """
        cases = (
            (
                "path matches, version differs",
                _parent_module(),
                "WILDLY-DIFFERENT-VERSION",
                False,
                (
                    "THE PATH IS PRIMARY: the version comes from `git describe`, so two trees on the "
                    "same commit differing in uncommitted content can report the same one. A version "
                    "mismatch must NOT abort a run whose child really is the runner's own copy"
                ),
            ),
            (
                "path differs, version matches",
                "/elsewhere/agent_workflows/__init__.py",
                "1.2.3",
                True,
                (
                    "THE OTHER DIRECTION, and the one that catches the real defect: a lane's copy on "
                    "the same commit reports an identical version, so a version-only comparison would "
                    "have passed the very hijack `af7i6p` exists to stop"
                ),
            ),
        )
        wrong: list[str] = []
        for case, child_path, child_version, expect_raise, why in cases:
            runner_shared._TOOL_IDENTITY_VERIFIED.clear()
            spy = _LaunchSpy(stdout=f"{child_path}\n{child_version}\n")
            raised = None
            record = None
            with (
                tempfile.TemporaryDirectory() as temp,
                unittest.mock.patch.object(driver.subprocess, "run", spy),
            ):
                try:
                    record = driver.assert_child_tool_identity(
                        Path(temp) / "events.jsonl", cwd=Path(temp)
                    )
                except driver.ToolIdentityError as exc:
                    raised = exc
            problems: list[str] = []
            if expect_raise and raised is None:
                problems.append(
                    "expected ToolIdentityError, got a PASS; the identity check is not comparing the "
                    "module PATH at all"
                )
            if not expect_raise and raised is not None:
                problems.append(
                    f"expected a PASS, got ToolIdentityError: {str(raised)[:200]!r}; the check has "
                    "started treating the version as authoritative, which aborts runs spuriously"
                )
            if not expect_raise and record is not None:
                if record.get("child_version") != child_version:
                    problems.append(
                        f"the version must still be RECORDED as context; got "
                        f"{record.get('child_version')!r}"
                    )
                if record.get("expected_module") != _parent_module():
                    problems.append(
                        f"the record must name what it expected; got "
                        f"{record.get('expected_module')!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(cases)} identity comparisons are wrong. BOTH ROWS SHARE THIS TABLE "
            "DELIBERATELY: a check that raised on everything satisfies the second row while making "
            "every run abort, and one that raised on nothing satisfies the first while passing the "
            "hijack. FIX: compare the resolved module PATH and record the version as context; never "
            "compare the version.\n" + "\n".join(wrong),
        )


class TheIdentityCheckPrecedesTheFirstNestedAw(unittest.TestCase):
    """The E-04 placement claim, proved by CALL ORDER on a real turn rather than by byte offsets.

    REPLACES `test_assertion_is_invoked_before_the_first_nested_lifecycle_call`, which compared
    `src.index("assert_child_tool_identity")` against `src.index("driver_begin(")` inside
    `execute_item`. That pin had already been patched once to chase the `execute_item_core` refactor,
    and it cannot distinguish a mention in a comment from a call.

    HOW THIS IS STRONGER: both collaborators are patched with spies that APPEND TO ONE LIST, and a real
    `execute_item` is driven on a fixture repository, so the recorded order is the order the shipped
    code actually executes. A reordering that put `driver_begin` first fails; a rename, a reflow, or
    another relocation into a shared core does not.

    HONEST LIMIT: this observes the ONE path the fixture drives (a self-finalizing execute turn in a
    shared tree). The AST ordering guard in `tests/test_rununify_execute_item_gates.py` covers paths no
    test drives, which is why that one is not redundant with this one.
    """

    DRIVERS = (
        ("oc_runipd", driver, "run_opencode"),
        ("agy_runipd", agy_runipd, "run_agy_turn"),
    )

    _PLAN = """# IPD: identity order probe

- Date: 2026-09-19
- Kind: child
- Concern: probe.
- Scope: probe.
- Scope-Paths: src/
- Item-Dependencies: none
- Status: approved
- Set: probe
- Order: 1
- Highest E allocated: 01
- Author: test
- Id: idp001

## Workflow history
- 2026-09-19 approved (test): probe.
"""

    def _git(self, repo: Path, *args: str) -> None:
        subprocess.run(
            ["git", *args], cwd=repo, text=True, capture_output=True, check=True
        )

    def _fixture(self, tmp: Path):
        repo = tmp / "repo"
        repo.mkdir(parents=True)
        self._git(repo, "init", "-q")
        self._git(repo, "config", "user.email", "t@example.invalid")
        self._git(repo, "config", "user.name", "t")
        (repo / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
        )
        (repo / "tracked.txt").write_text("v1\n", encoding="utf-8")
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True)
        plan = pending / "20260919-probe-01-idp001-probe.ipd.md"
        plan.write_text(self._PLAN, encoding="utf-8")
        self._git(repo, "add", "-A")
        self._git(repo, "commit", "-qm", "fixture")
        run_dir = repo / ".aw" / "records" / "runs" / "run-idp"
        (run_dir / "outcomes").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        item = {
            "position": 1,
            "id6": "idp001",
            "setid": "probe",
            "status": "queued",
            "configured_file": str(plan.relative_to(repo)),
            "action": "execute",
        }
        state = {
            "run_id": "run-idp",
            "created_at": "2026-09-19T00:00:00+00:00",
            "updated_at": "2026-09-19T00:00:00+00:00",
            "selectors": ["probe"],
            "repo": str(repo),
            "queue": [item],
            "set_sessions": {},
            "session_id": None,
            "options": {
                "opencode": "/bin/true",
                "agy": "/bin/true",
                "model": "probe",
                "self_finalize": True,
                "no_audit": True,
                "isolate_worktree": False,
            },
        }
        return run_dir, state, item

    def test_tool_identity_is_verified_before_the_first_nested_aw_on_both_hosts(self):
        for name, module, spawn in self.DRIVERS:
            with self.subTest(host=name), tempfile.TemporaryDirectory() as tmp:
                run_dir, state, item = self._fixture(Path(tmp))
                rec = _CallRecorder()
                with (
                    unittest.mock.patch.object(
                        module,
                        spawn,
                        rec.stub("spawn", (0, "ses", str(run_dir / "log"), ["probe"])),
                    ),
                    unittest.mock.patch.object(
                        module, "assert_child_tool_identity", rec.stub("identity")
                    ),
                    unittest.mock.patch.object(
                        module, "driver_begin", rec.stub("begin", (0, "ok"))
                    ),
                    unittest.mock.patch.object(
                        module, "driver_finalize", lambda *a, **k: (0, "ok")
                    ),
                ):
                    module.execute_item(run_dir, state, item, recovery=False)
                order = rec.order
                self.assertIn(
                    "identity",
                    order,
                    f"{name}: the identity check was never invoked on a real execute turn, so no "
                    "nested `aw` this run performs was ever verified",
                )
                self.assertIn("begin", order, f"{name}: driver_begin was never invoked")
                self.assertLess(
                    order.index("identity"),
                    order.index("begin"),
                    f"{name}: tool identity must be verified BEFORE the first nested `aw` "
                    f"(driver_begin); observed call order was {order}",
                )


if __name__ == "__main__":
    unittest.main()
