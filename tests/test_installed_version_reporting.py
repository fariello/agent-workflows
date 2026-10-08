"""Tests for installed version reporting, bundled VERSION baking, and stale-build warnings.

Validates IPD whz0oi:
- (a) write_bundled_version generates VERSION file without touching source .aw/system/VERSION
- (b) doctor.check_stale_build drift detection and cli.main(["--version"]) stale warning
- (c) slow end-to-end wheel build verifying bundled VERSION equals METADATA and aw --version
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from typing import Optional, Tuple

import pytest

from agent_workflows import __version__, cli, doctor
from tests.support import REPO_ROOT


class InstalledVersionReportingTests(unittest.TestCase):
    def test_write_bundled_version(self):
        """(a) Test that write_bundled_version writes the version and does not touch source."""
        import hatch_build

        source_version_file = REPO_ROOT / ".aw" / "system" / "VERSION"
        source_content = source_version_file.read_text(encoding="utf-8")

        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = hatch_build.write_bundled_version("2.3.4.dev5+g1234567", tmpdir)
            self.assertTrue(out_file.is_file())
            self.assertEqual(
                out_file.read_text(encoding="utf-8"), "2.3.4.dev5+g1234567\n"
            )
            # Verify working tree VERSION is unchanged
            self.assertEqual(
                source_version_file.read_text(encoding="utf-8"), source_content
            )

    def _create_synthetic_fixture(
        self,
        base_dir: Path,
        *,
        version: str = "9.9.9.dev1+gabc1234",
        editable: bool = False,
        has_direct_url: bool = True,
        is_git: bool = True,
        match_head: bool = False,
    ) -> Tuple[Path, Optional[Path], Optional[str]]:
        """Helper to create a synthetic site-packages fixture with dist-info."""
        site_packages = base_dir / "site-packages"
        dist_info = site_packages / f"agent_workflows-{version}.dist-info"
        dist_info.mkdir(parents=True, exist_ok=True)

        (dist_info / "METADATA").write_text(
            f"Metadata-Version: 2.1\nName: agent-workflows\nVersion: {version}\n",
            encoding="utf-8",
        )
        (dist_info / "RECORD").write_text("", encoding="utf-8")

        repo_dir = None
        head_sha = None
        if has_direct_url:
            repo_dir = base_dir / "source_repo"
            repo_dir.mkdir(parents=True, exist_ok=True)
            if is_git:
                subprocess.run(
                    ["git", "init"],
                    cwd=str(repo_dir),
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["git", "config", "user.name", "Test"],
                    cwd=str(repo_dir),
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["git", "config", "user.email", "test@example.com"],
                    cwd=str(repo_dir),
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["git", "commit", "--allow-empty", "-m", "init"],
                    cwd=str(repo_dir),
                    check=True,
                    capture_output=True,
                )
                proc = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=str(repo_dir),
                    check=True,
                    capture_output=True,
                    text=True,
                )
                head_sha = proc.stdout.strip()
                if match_head:
                    # Update dist-info metadata with matching head sha
                    matched_version = f"9.9.9.dev1+g{head_sha[:7]}"
                    (dist_info / "METADATA").write_text(
                        f"Metadata-Version: 2.1\nName: agent-workflows\nVersion: {matched_version}\n",
                        encoding="utf-8",
                    )

            direct_url_data = {
                "dir_info": {"editable": True} if editable else {},
                "url": f"file://{repo_dir.resolve().as_posix()}",
            }
            (dist_info / "direct_url.json").write_text(
                json.dumps(direct_url_data), encoding="utf-8"
            )

        return dist_info, repo_dir, head_sha

    def test_stale_build_drift_detection(self):
        """(b) Stale build drift is detected when local git repo HEAD differs from build sha."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_info, repo_dir, head_sha = self._create_synthetic_fixture(
                Path(tmpdir), version="9.9.9.dev1+gabc1234"
            )
            drift = doctor.check_stale_build(dist_info)
            self.assertIsNotNone(drift)
            self.assertEqual(drift.rule, "doctor.stale-build")
            self.assertIn("abc1234", drift.detail)
            self.assertIn(repo_dir.resolve().as_posix(), drift.detail)
            expected_cmd = f"pip install {repo_dir.resolve().as_posix()}"
            self.assertEqual(drift.recovery, expected_cmd)

            # Test build_remediation
            rem = doctor.build_remediation(drift, REPO_ROOT)
            self.assertEqual(rem.command, expected_cmd)
            self.assertEqual(rem.summary_fix, expected_cmd)
            self.assertIn("Installed build is behind", rem.title)

    def test_no_drift_when_editable(self):
        """(b) Editable install produces no stale-build drift."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_info, _, _ = self._create_synthetic_fixture(
                Path(tmpdir), editable=True
            )
            drift = doctor.check_stale_build(dist_info)
            self.assertIsNone(drift)

    def test_no_drift_when_registry_install(self):
        """(b) Registry install (no direct_url.json) produces no stale-build drift."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_info, _, _ = self._create_synthetic_fixture(
                Path(tmpdir), has_direct_url=False
            )
            drift = doctor.check_stale_build(dist_info)
            self.assertIsNone(drift)

    def test_no_drift_when_non_git_directory(self):
        """(b) Source directory that is not a git repo produces no stale-build drift."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_info, _, _ = self._create_synthetic_fixture(Path(tmpdir), is_git=False)
            drift = doctor.check_stale_build(dist_info)
            self.assertIsNone(drift)

    def test_no_drift_when_version_lacks_git_sha(self):
        """(b) Version lacking +g<sha> segment produces no stale-build drift."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_info, _, _ = self._create_synthetic_fixture(
                Path(tmpdir), version="9.9.9"
            )
            drift = doctor.check_stale_build(dist_info)
            self.assertIsNone(drift)

    def test_no_drift_when_build_is_current(self):
        """(b) Build matching current HEAD produces no stale-build drift."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_info, _, _ = self._create_synthetic_fixture(
                Path(tmpdir), match_head=True
            )
            drift = doctor.check_stale_build(dist_info)
            self.assertIsNone(drift)

    def test_cli_version_stale_and_current_output(self):
        """(b) cli.main(["--version"]) prints note when stale, exactly 1 line when current."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            stale_dist_info, repo_dir, _ = self._create_synthetic_fixture(
                base_dir / "stale", version="9.9.9.dev1+gabc1234"
            )
            current_dist_info, _, _ = self._create_synthetic_fixture(
                base_dir / "curr", match_head=True
            )

            # Test stale fixture
            doctor._ACTIVE_DIST_INFO_OVERRIDE = stale_dist_info
            try:
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf), self.assertRaises(
                    SystemExit
                ) as cm:
                    cli.main(["--version"])
                self.assertEqual(cm.exception.code, 0)
                lines = buf.getvalue().strip().splitlines()
                self.assertEqual(len(lines), 2)
                self.assertEqual(lines[0], f"agent-workflows {__version__}")
                self.assertIn("warning: build is stale; rebuild with", lines[1])
                self.assertIn(repo_dir.resolve().as_posix(), lines[1])
            finally:
                doctor._ACTIVE_DIST_INFO_OVERRIDE = None

            # Test current fixture
            doctor._ACTIVE_DIST_INFO_OVERRIDE = current_dist_info
            try:
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf), self.assertRaises(
                    SystemExit
                ) as cm:
                    cli.main(["--version"])
                self.assertEqual(cm.exception.code, 0)
                lines = buf.getvalue().strip().splitlines()
                self.assertEqual(len(lines), 1)
                self.assertEqual(lines[0], f"agent-workflows {__version__}")
            finally:
                doctor._ACTIVE_DIST_INFO_OVERRIDE = None

    @pytest.mark.slow
    def test_e2e_wheel_build_installed_version_reporting(self):
        """(c) End-to-end wheel build and install verifies bundled VERSION and aw --version."""
        try:
            import build  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("the 'build' package is not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            dist_dir = tmp_path / "dist"
            dist_dir.mkdir()

            # Build wheel
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "build",
                    "--wheel",
                    "--outdir",
                    str(dist_dir),
                ],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                check=True,
            )
            wheels = list(dist_dir.glob("*.whl"))
            self.assertTrue(wheels, "No wheel was produced")
            wheel = wheels[0]

            # Inspect bundled VERSION in wheel
            with zipfile.ZipFile(wheel) as zf:
                bundled_ver = (
                    zf.read("agent_workflows/_data/.aw/system/VERSION")
                    .decode("utf-8")
                    .strip()
                )
                meta_text = [
                    zf.read(name).decode("utf-8")
                    for name in zf.namelist()
                    if name.endswith("METADATA")
                ][0]
                meta_ver = [
                    line.split(":", 1)[1].strip()
                    for line in meta_text.splitlines()
                    if line.startswith("Version:")
                ][0]
                self.assertEqual(bundled_ver, meta_ver)

            # Create venv and install
            venv_dir = tmp_path / "v"
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)],
                check=True,
                capture_output=True,
            )
            pip_bin = venv_dir / "bin" / "pip"
            aw_bin = venv_dir / "bin" / "aw"

            env = dict(os.environ)
            env.pop("PYTHONPATH", None)
            subprocess.run(
                [str(pip_bin), "install", str(wheel)],
                env=env,
                check=True,
                capture_output=True,
            )

            # From a directory outside checkout with AW_NO_REEXEC=1
            proc = subprocess.run(
                [str(aw_bin), "--version"],
                cwd=str(tmp_path),
                env=dict(env, AW_NO_REEXEC="1"),
                capture_output=True,
                text=True,
                check=True,
            )
            lines = proc.stdout.strip().splitlines()
            self.assertEqual(lines[0], f"agent-workflows {meta_ver}")


if __name__ == "__main__":
    unittest.main()
