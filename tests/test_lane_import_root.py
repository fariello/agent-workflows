"""Tests for lane import root resolution (IPD `lhjsu0`, bugs `uin96r`, `0vbdll`, `ccbe60`).

THE DEFECT UNDER TEST. An editable install pins an absolute path to the main checkout in
site-packages (`_editable_impl_agent_workflows.pth`). When an evidence command or subprocess test is
invoked from a lane worktree with a non-root cwd (e.g. `tests/` or a temp repo fixture), Python falls
back through `sys.path` to the editable install's `.pth` entry, silently executing the main checkout's
code instead of the lane worktree's.

WHAT THESE TESTS GUARD (BOTH DIRECTIONS):
1. EVIDENCE CALLER (lane-authoritative): An evidence command or subprocess test invoked from inside
   a worktree (including from a non-root subdirectory) MUST resolve that worktree's package.
2. CONTROL-PLANE CALLER (driver-authoritative, plan `af7i6p`, spec `7ckptx` A8): A driver-spawned
   nested `aw` lifecycle invocation MUST resolve the driver's tooling, even when invoked with cwd
   set to a lane subdirectory.

ALL TESTS USE SYNTHETIC FIXTURES in temporary directories with distinct package markers, never
relying on live worktrees on disk.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from agent_workflows import runner_shared
from tests import support

PROBE = textwrap.dedent(
    """
    import os, sys
    import agent_workflows as a
    _marker = getattr(a, "MARKER", "<real-package>")
    _file = getattr(a, "__file__", None) or (list(getattr(a, "__path__", [])) + [None])[0]
    print(f"MARKER={_marker}")
    print(f"FILE={os.path.realpath(_file) if _file else 'UNRESOLVED'}")
    """
).strip()


def _make_package(root: Path, marker: str, version: str = "1.0.0") -> Path:
    """Create a minimal synthetic `agent_workflows` package with a distinctive MARKER."""
    pkg = root / "agent_workflows"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text(
        f"MARKER = {marker!r}\n__version__ = {version!r}\n", encoding="utf-8"
    )
    (pkg / "__main__.py").write_text(
        textwrap.dedent(
            """
            import agent_workflows, sys
            print("MARKER=" + getattr(agent_workflows, "MARKER", "<unknown>"))
            sys.exit(0)
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return pkg


class _SyntheticFixture:
    """A synthetic environment containing a lane tree, a driver tree, and a fallback tree."""

    def __init__(self, base: Path) -> None:
        self.lane_root = base / "lane_tree"
        self.driver_root = base / "driver_tree"
        self.fallback_root = base / "fallback_tree"

        _make_package(self.lane_root, "SYNTHETIC-LANE", "0.1.0")
        _make_package(self.driver_root, "SYNTHETIC-DRIVER", "1.0.0")
        _make_package(self.fallback_root, "SYNTHETIC-FALLBACK", "2.0.0")

        self.lane_subdir = self.lane_root / "tests" / "nested" / "subrepo"
        self.lane_subdir.mkdir(parents=True, exist_ok=True)


class LaneImportRootGuardTests(unittest.TestCase):
    """Guard tree-relative resolution for evidence callers and control-plane callers."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        # Resolve the tempdir: PROBE reports os.path.realpath(__file__), so the fixture roots
        # must be canonical too (macOS /var -> /private/var, Windows 8.3 short names).
        self.fx = _SyntheticFixture(Path(self._temp.name).resolve())
        self.addCleanup(self._temp.cleanup)

    def _probe(
        self,
        argv: list[str],
        cwd: Path,
        env: dict[str, str],
    ) -> tuple[str, str]:
        """Run probe and return (marker, resolved_file)."""
        proc = subprocess.run(
            argv,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
        )
        marker = ""
        resolved_file = ""
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.startswith("MARKER="):
                marker = line.split("=", 1)[1].strip()
            elif line.startswith("FILE="):
                resolved_file = line.split("=", 1)[1].strip()
        return marker, resolved_file

    def test_unpinned_launch_from_lane_subdir_reproduces_defect(self) -> None:
        """From a lane subdirectory, an unpinned subprocess without lane on PYTHONPATH falls back.

        This demonstrates the root cause of `uin96r`/`0vbdll`/`ccbe60`: with no cwd entry in
        sys.path matching the package, Python falls back to site-packages (here simulated by
        fallback_root on PYTHONPATH), silently exercising the wrong tree.
        """
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.fx.fallback_root)
        marker, resolved_file = self._probe(
            [sys.executable, "-c", PROBE],
            cwd=self.fx.lane_subdir,
            env=env,
        )
        self.assertEqual(
            marker,
            "SYNTHETIC-FALLBACK",
            f"Expected fallback package on unpinned subdir launch, got {marker}",
        )
        self.assertTrue(
            resolved_file.startswith(str(self.fx.fallback_root)),
            f"Expected fallback path, got {resolved_file}",
        )

    def test_evidence_caller_from_lane_subdir_resolves_lane_package(self) -> None:
        """An evidence invocation from a lane subdirectory MUST resolve the lane's package.

        Tests from any non-root working directory inside the worktree must measure the lane tree.
        """
        env = os.environ.copy()
        # Evidence invocation sets PYTHONPATH to prepend the lane tree root
        env["PYTHONPATH"] = f"{self.fx.lane_root}{os.pathsep}{self.fx.fallback_root}"
        marker, resolved_file = self._probe(
            [sys.executable, "-c", PROBE],
            cwd=self.fx.lane_subdir,
            env=env,
        )
        self.assertEqual(
            marker,
            "SYNTHETIC-LANE",
            f"Evidence caller from lane subdir must resolve lane package, got {marker}",
        )
        self.assertTrue(
            resolved_file.startswith(str(self.fx.lane_root)),
            f"Expected lane path, got {resolved_file}",
        )

    def test_control_plane_caller_from_lane_subdir_resolves_driver_package(
        self,
    ) -> None:
        """A control-plane invocation from a lane subdirectory MUST resolve the driver's package.

        Guards af7i6p / spec 7ckptx A8: the control-plane pin uses AW_PIN_KEEP_ROOT and the
        _AW_PIN_BOOTSTRAP / _AW_PIN_STRIP shim so driver tooling executes driver code.
        """
        env = os.environ.copy()
        env["PYTHONPATH"] = (
            f"{self.fx.driver_root}{os.pathsep}{self.fx.lane_root}{os.pathsep}{self.fx.fallback_root}"
        )
        env["AW_PIN_KEEP_ROOT"] = str(self.fx.driver_root)

        argv = [sys.executable]
        if sys.version_info >= (3, 11):
            argv.append("-P")
        argv.extend(["-c", runner_shared._AW_PIN_STRIP + PROBE])

        marker, resolved_file = self._probe(
            argv,
            cwd=self.fx.lane_subdir,
            env=env,
        )
        self.assertEqual(
            marker,
            "SYNTHETIC-DRIVER",
            f"Control-plane caller from lane subdir must resolve driver package, got {marker}",
        )
        self.assertTrue(
            resolved_file.startswith(str(self.fx.driver_root)),
            f"Expected driver path, got {resolved_file}",
        )

    def test_both_directions_hold_from_multiple_non_root_subdirectories(self) -> None:
        """Both directions must hold across multiple arbitrary nested subdirectories."""
        subdirs = [
            self.fx.lane_root / "tests",
            self.fx.lane_root / "tests" / "unit",
            self.fx.lane_root / ".aw" / "worktrees",
            self.fx.lane_root / "a" / "b" / "c" / "d",
        ]
        for sdir in subdirs:
            sdir.mkdir(parents=True, exist_ok=True)

            # Direction 1: Evidence caller resolves lane
            env_ev = os.environ.copy()
            env_ev["PYTHONPATH"] = (
                f"{self.fx.lane_root}{os.pathsep}{self.fx.fallback_root}"
            )
            ev_marker, ev_file = self._probe(
                [sys.executable, "-c", PROBE],
                cwd=sdir,
                env=env_ev,
            )
            self.assertEqual(
                ev_marker,
                "SYNTHETIC-LANE",
                f"Evidence caller in {sdir} resolved {ev_marker} instead of SYNTHETIC-LANE",
            )
            self.assertTrue(ev_file.startswith(str(self.fx.lane_root)))

            # Direction 2: Control plane resolves driver
            env_cp = os.environ.copy()
            env_cp["PYTHONPATH"] = (
                f"{self.fx.driver_root}{os.pathsep}{self.fx.lane_root}{os.pathsep}{self.fx.fallback_root}"
            )
            env_cp["AW_PIN_KEEP_ROOT"] = str(self.fx.driver_root)
            argv_cp = [sys.executable]
            if sys.version_info >= (3, 11):
                argv_cp.append("-P")
            argv_cp.extend(["-c", runner_shared._AW_PIN_STRIP + PROBE])

            cp_marker, cp_file = self._probe(
                argv_cp,
                cwd=sdir,
                env=env_cp,
            )
            self.assertEqual(
                cp_marker,
                "SYNTHETIC-DRIVER",
                f"Control plane caller in {sdir} resolved {cp_marker} instead of SYNTHETIC-DRIVER",
            )
            self.assertTrue(cp_file.startswith(str(self.fx.driver_root)))

    def test_support_run_cli_pins_current_repo_tree(self) -> None:
        """support.run_cli resolves the repo tree containing the test suite."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        # Run run_cli from a temp directory outside the repo
        proc = support.run_cli(
            "--help",
            cwd=Path(tmp.name),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("agent-workflows", proc.stdout)

        # Verify that a child spawned via python with the PYTHONPATH from support.run_cli
        # resolves the package under REPO_ROOT
        env = os.environ.copy()
        existing_pp = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{support.REPO_ROOT}{os.pathsep}{existing_pp}".rstrip(
            os.pathsep
        )
        proc_probe = subprocess.run(
            [sys.executable, "-c", PROBE],
            cwd=Path(tmp.name),
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc_probe.returncode, 0)
        resolved = ""
        for line in proc_probe.stdout.splitlines():
            if line.startswith("FILE="):
                resolved = line.split("=", 1)[1].strip()
        expected = os.path.realpath(
            str(support.REPO_ROOT / "agent_workflows" / "__init__.py")
        )
        self.assertEqual(
            resolved,
            expected,
            f"support.run_cli did not resolve REPO_ROOT package: {resolved} != {expected}",
        )
