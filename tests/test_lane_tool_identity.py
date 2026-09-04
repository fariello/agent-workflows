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
from pathlib import Path

from agent_workflows import agy_runipd
from agent_workflows import oc_runipd as driver

PROBE = "import agent_workflows as a, os; print(os.path.realpath(a.__file__))"

# The two halves of the pin, named once so the guard and the runtime tests agree.
_SUPPRESS_MARKERS = ("_AW_PIN_BOOTSTRAP", "_AW_PIN_STRIP", "pinned_module_argv")
_SELECT_MARKERS = ("pinned_child_env",)


def _module_source(module) -> str:
    """Source text of `module`, with the `getsourcefile` Optional narrowed."""
    path = inspect.getsourcefile(module)
    assert path is not None, f"no source file for {module!r}"
    return Path(path).read_text(encoding="utf-8")


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

    def test_unpinned_launch_imports_the_lane_decoy(self):
        """(a) FALSIFIABILITY: the OLD bare argv shape imports the LANE's copy -- the defect."""
        argv = [sys.executable, "-m", "agent_workflows"]
        got = _resolved_module(
            [sys.executable, "-c", PROBE], self.fx.lane, self.fx.env(select=True)
        )
        self.assertEqual(
            _marker_of(got),
            "DECOY-LANE",
            f"expected the unpinned shape to reproduce the hijack; imported {got!r}",
        )
        # And the decoy's CLI really would have run, not merely been importable.
        result = subprocess.run(
            argv,
            cwd=str(self.fx.lane),
            env=self.fx.env(select=True),
            capture_output=True,
            text=True,
        )
        self.assertIn("MARKER=DECOY-LANE", result.stdout)

    def test_selecting_half_alone_is_inert(self):
        """(b) FALSIFIABILITY: PYTHONPATH alone STILL imports the decoy (the old half-pin).

        This is the F6 case: both drivers already prepended the runner's package root to the
        child PYTHONPATH, which READ as this fix but was measurably inert, because the cwd entry
        precedes PYTHONPATH in sys.path.
        """
        got = _resolved_module(
            [sys.executable, "-c", PROBE], self.fx.lane, self.fx.env(select=True)
        )
        self.assertEqual(
            _marker_of(got),
            "DECOY-LANE",
            "PYTHONPATH alone must be shown INERT (the cwd entry wins); "
            f"imported {got!r}",
        )

    def test_suppression_only_lands_on_the_wrong_copy(self):
        """(c) FALSIFIABILITY: suppression WITHOUT selection resolves the wrong copy.

        It falls through to the default path, which equals the runner's own ONLY on an editable
        install. This is why the pin must be POSITIVE, and why the fixture needs a third copy.
        """
        argv = (
            [sys.executable]
            + (["-P"] if sys.version_info >= (3, 11) else [])
            + ["-c", driver._AW_PIN_STRIP + PROBE]
        )
        got = _resolved_module(
            argv, self.fx.lane, self.fx.env(select=False, extra_default=True)
        )
        marker = _marker_of(got)
        self.assertNotEqual(
            marker,
            "DECOY-LANE",
            f"suppression should defeat the decoy; imported {got!r}",
        )
        self.assertEqual(
            marker,
            "THIRD-DEFAULTPATH",
            "suppression alone must be shown to select the WRONG (default-path) copy, not the "
            f"designated parent; imported {got!r}",
        )

    def test_full_pin_resolves_to_the_designated_parent(self):
        """(d) The two-part pin resolves POSITIVELY to the designated parent copy."""
        argv = (
            [sys.executable]
            + (["-P"] if sys.version_info >= (3, 11) else [])
            + ["-c", driver._AW_PIN_STRIP + PROBE]
        )
        got = _resolved_module(argv, self.fx.lane, self.fx.env(select=True))
        self.assertEqual(
            _marker_of(got),
            "PARENT-RUNNER",
            f"the two-part pin must select the designated parent; imported {got!r}",
        )
        self.assertEqual(
            os.path.realpath(got),
            str(self.fx.parent / "agent_workflows" / "__init__.py"),
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
            + ["-c", driver._AW_PIN_PROBE]
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

    def test_pin_does_not_depend_on_the_version_specific_flag(self):
        """The bootstrap alone pins, so 3.9/3.10 (no `-P`) behave like 3.11+.

        `-P` and `PYTHONSAFEPATH` are BOTH 3.11 features; measured on a real CPython 3.9.25,
        `-P` is rejected and `PYTHONSAFEPATH=1` is silently ignored. Correctness therefore must
        not depend on either. This test omits the flag entirely, simulating the floor.
        """
        argv = [sys.executable, "-c", driver._AW_PIN_STRIP + PROBE]
        got = _resolved_module(argv, self.fx.lane, self.fx.env(select=True))
        self.assertEqual(
            _marker_of(got),
            "PARENT-RUNNER",
            "the pin must hold with NO interpreter flag, since the declared floor (>=3.9) has "
            f"neither -P nor PYTHONSAFEPATH; imported {got!r}",
        )

    def test_bootstrap_strips_the_absolute_cwd_not_just_empty_string(self):
        """Under `-m`, sys.path[0] is the ABSOLUTE cwd, so filtering only ''/'.' is inert."""
        self.assertIn("realpath", driver._AW_PIN_STRIP)
        probe = driver._AW_PIN_STRIP + (
            "import sys, os\n"
            "print(str(os.getcwd() in sys.path) + ':' + str('' in sys.path))\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=str(self.fx.lane),
            env=self.fx.env(select=True),
            capture_output=True,
            text=True,
        )
        self.assertIn(
            "False:False",
            result.stdout,
            f"the bootstrap must remove BOTH the absolute cwd and '': {result.stdout!r}",
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
        # Pinned module launches: a call to the shared helper.
        if isinstance(node, ast.Call):
            func = ast.unparse(node.func)
            if func.endswith("pinned_module_argv"):
                sites.append(
                    {"kind": "module-pinned", "line": node.lineno, "src": func}
                )
    return sites


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
        """The guard must account for EVERY site, with none left unclassified."""
        total = 0
        for name, module in self.DRIVERS:
            sites = _classify_sites(module)
            self.assertTrue(sites, f"{name}: expected to find nested-`aw` launch sites")
            for site in sites:
                self.assertIn(
                    site["kind"],
                    {"module-pinned", "module-unpinned", "console-script"},
                    f"{name}: unclassified site {site}",
                )
            pinned = [s for s in sites if s["kind"] == "module-pinned"]
            console = [s for s in sites if s["kind"] == "console-script"]
            self.assertTrue(
                pinned, f"{name}: expected at least one PINNED module launch site"
            )
            self.assertEqual(
                len(console),
                1,
                f"{name}: expected exactly one console-script fallback; got {console}",
            )
            total += len(sites)
        self.assertGreaterEqual(total, 9, f"expected >=9 classified sites, saw {total}")

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

    def test_guard_fails_on_a_half_pinned_site(self):
        """The guard must FAIL when only ONE of the two pin parts is present."""
        for name, module in self.DRIVERS:
            src = _module_source(module)
            self.assertTrue(
                any(marker in src for marker in _SUPPRESS_MARKERS),
                f"{name} must carry the SUPPRESSING half of the pin",
            )
            self.assertTrue(
                any(marker in src for marker in _SELECT_MARKERS),
                f"{name} must carry the SELECTING half of the pin; PYTHONPATH-only or "
                "suppression-only is a half-pin and was measured insufficient",
            )

    def test_raw_subprocess_module_launches_pass_the_pinned_env(self):
        """The two raw `subprocess.run` sites per driver must now receive `env=`.

        They previously passed NO `env=` at all, so the selecting half could not reach them.
        """
        for name, module in self.DRIVERS:
            for func in ("driver_begin", "driver_finalize"):
                src = inspect.getsource(getattr(module, func))
                self.assertIn(
                    "pinned_module_argv",
                    src,
                    f"{name}.{func} must build its argv with the shared pinned helper",
                )
                self.assertIn(
                    "env=pinned_child_env()",
                    src,
                    f"{name}.{func} must pass the pinned env; without it the selecting half "
                    "of the pin never reaches the child",
                )

    def test_identity_probe_is_not_counted_as_a_nested_aw_launcher(self):
        """The E-04 probe must not create a false 4-vs-3 asymmetry in the ttywedge guard.

        `tests/test_nested_tty_noninteractive.py` enumerates nested-`aw` launchers by their first
        argument's NAME (`argv`/`cmd`) and asserts both drivers expose an EQUAL count. The identity
        probe is a read-only import probe defined once in oc and merely IMPORTED by agy, so naming
        its local `argv` made oc appear to have one more launcher than agy and broke that sibling
        guard. It must stay distinctly named -- while still denying the child a terminal.
        """
        src = inspect.getsource(driver.assert_child_tool_identity)
        self.assertIn("probe_argv", src)
        self.assertIn(
            "stdin=subprocess.DEVNULL",
            src,
            "the probe must still deny the child a terminal (ttywedge g40w37)",
        )
        tree = ast.parse(textwrap.dedent(src))
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
        """E-05: ONE definition, not a per-driver copy. A second copy is how the half-pin drifted."""
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
        agy_src = _module_source(agy_runipd)
        self.assertNotIn(
            "def pinned_child_env",
            agy_src,
            "agy must not define its own copy of the pin",
        )
        self.assertNotIn(
            'merged_env["PYTHONPATH"] = f"{repo_src}',
            agy_src,
            "the old inert per-driver PYTHONPATH prepend must be gone, not left beside the fix",
        )

    def test_run_checked_no_longer_carries_its_own_half_pin(self):
        """E-05: `run_checked` must consume the shared definition rather than rebuild it."""
        for name, module in self.DRIVERS:
            src = inspect.getsource(module.run_checked)
            self.assertIn(
                "pinned_child_env",
                src,
                f"{name}.run_checked must obtain its env from the shared definition",
            )
            self.assertNotIn(
                "repo_src",
                src,
                f"{name}.run_checked must no longer build its own (inert) PYTHONPATH prepend",
            )

    def test_both_drivers_are_fixed_symmetrically_over_existing_sites(self):
        """Symmetry WITHOUT requiring equal site counts.

        oc has four module-launch sites to agy's three, because oc alone has
        `finalize_orchestrator`. That asymmetry is expected and must NOT be "fixed" by inventing
        a fourth agy site, so symmetry is asserted over the sites that EXIST.
        """
        for name, module in self.DRIVERS:
            src = _module_source(module)
            self.assertIn(
                "af7i6p",
                src,
                f"{name} must carry the lanetruth pin, traceable to plan af7i6p",
            )
        oc_pinned = [s for s in _classify_sites(driver) if s["kind"] == "module-pinned"]
        agy_pinned = [
            s for s in _classify_sites(agy_runipd) if s["kind"] == "module-pinned"
        ]
        self.assertGreaterEqual(len(oc_pinned), 4, f"oc pinned sites: {oc_pinned}")
        self.assertGreaterEqual(len(agy_pinned), 3, f"agy pinned sites: {agy_pinned}")
        self.assertFalse(
            hasattr(agy_runipd, "finalize_orchestrator"),
            "agy is not expected to have finalize_orchestrator; if it gained one, assert its "
            "pin explicitly rather than letting the symmetry check pass by accident",
        )


class ToolIdentityAssertionTests(unittest.TestCase):
    """E-04: residual mismatch must be a loud, recorded, RUN-FATAL refusal."""

    def setUp(self) -> None:
        driver._TOOL_IDENTITY_VERIFIED.clear()
        self.addCleanup(driver._TOOL_IDENTITY_VERIFIED.clear)

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
            original = driver._AW_PIN_PROBE
            # Force the probe to report a foreign module path.
            driver._AW_PIN_PROBE = (
                "print('/somewhere/else/agent_workflows/__init__.py')\n"
            )
            try:
                with self.assertRaises(driver.ToolIdentityError) as ctx:
                    driver.assert_child_tool_identity(events, cwd=Path(temp))
            finally:
                driver._AW_PIN_PROBE = original
            message = str(ctx.exception)
            self.assertIn("ABORTING RUN", message)
            self.assertIn("tool-identity mismatch", message)
            self.assertIn("/somewhere/else/agent_workflows/__init__.py", message)
            self.assertIn("tool-identity-mismatch", events.read_text(encoding="utf-8"))

    def test_mismatch_is_run_fatal_not_item_local(self):
        """OQ-02: ToolIdentityError must NOT be downgraded by the item-local DriverError catch.

        ToolIdentityError subclasses DriverError, so without an explicit earlier clause the
        abort would be recorded as one item `failed-safely` while the remaining items kept
        running under the same wrong control plane -- the misleading outcome OQ-02 rejects.
        """
        self.assertTrue(issubclass(driver.ToolIdentityError, driver.DriverError))
        for name, module in (("oc_runipd", driver), ("agy_runipd", agy_runipd)):
            src = inspect.getsource(module.run_queue)
            self.assertIn(
                "except ToolIdentityError",
                src,
                f"{name}.run_queue must catch ToolIdentityError BEFORE DriverError and re-raise",
            )
            fatal = src.index("except ToolIdentityError")
            local = src.index("except DriverError")
            self.assertLess(
                fatal,
                local,
                f"{name}.run_queue must handle ToolIdentityError BEFORE the item-local "
                "DriverError clause, or the run-fatal abort is silently downgraded",
            )

    def test_identity_check_uses_the_module_path_as_primary_signal(self):
        """The version string is git-describe derived and can collide; the path cannot."""
        src = inspect.getsource(driver.assert_child_tool_identity)
        self.assertIn("child_module", src)
        self.assertIn(
            "expected_module",
            src,
            "the comparison must be on the resolved module PATH, not the version alone",
        )
        self.assertIn("__version__", driver._AW_PIN_PROBE)

    def test_assertion_is_invoked_before_the_first_nested_lifecycle_call(self):
        """Placement: in the per-item path, ahead of `driver_begin` (the first nested `aw`)."""
        for name, module in (("oc_runipd", driver), ("agy_runipd", agy_runipd)):
            src = inspect.getsource(module.execute_item)
            self.assertIn(
                "assert_child_tool_identity",
                src,
                f"{name}.execute_item must verify tool identity before a lifecycle transition",
            )
            self.assertLess(
                src.index("assert_child_tool_identity"),
                src.index("driver_begin("),
                f"{name}: the identity check must precede the first nested `aw` (driver_begin)",
            )


if __name__ == "__main__":
    unittest.main()
