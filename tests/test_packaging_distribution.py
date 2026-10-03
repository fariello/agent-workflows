"""Packaging distribution guard (wheel and sdist distribution contents).

Asserts packaging properties that the existing ship-vs-dev wheel guard does not reach:
1. Browser assets: positive, per-asset presence and non-emptiness in both wheel and sdist.
2. Honesty guard: REQUIRED_BROWSER_ASSETS kept honest against run_analytics_spa declarations.
3. Measured-hazard arm: probe demonstration that hatchling silently drops gitignored assets.
4. Sdist distribution contents: sdist allowlist carries browser assets, analytics/layout modules,
   and the bundled system data tree.
5. Console scripts: wheel registers entry points for aw, agent-workflows, and agentwf pointing
   to agent_workflows.cli:main.

Deliberately NOT marked `pytest.mark.slow` (OQ-02), following the precedent in tests/test_packaging.py.
Builds execute well within conftest.py's 90.0s _DEFAULT_TEST_TIMEOUT.
"""

from __future__ import annotations

import configparser
import re
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

from tests.support import REPO_ROOT

#: The browser assets that MUST ship, named explicitly.
#: Kept honest against run_analytics_spa by test_declared_assets_match_the_module.
REQUIRED_BROWSER_ASSETS = (
    "agent_workflows/run_analytics_assets/app.css",
    "agent_workflows/run_analytics_assets/app.js",
)

#: Protected analytics and layout modules that must ship in both distributions (PR-001).
PROTECTED_MODULES = (
    "agent_workflows/run_analytics_spa.py",
    "agent_workflows/run_analytics_report.py",
    "agent_workflows/layout_migration.py",
    "agent_workflows/layout_inventory.py",
)


def _build_wheel(outdir: Path) -> Path:
    """Build a wheel into outdir; return its path. Raises CalledProcessError or RuntimeError on failure."""
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(outdir)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    wheels = list(outdir.glob("*.whl"))
    if not wheels:
        raise RuntimeError("no wheel produced")
    return wheels[0]


def _build_sdist(outdir: Path) -> Path:
    """Build an sdist into outdir; return its path. Raises CalledProcessError or RuntimeError on failure."""
    subprocess.run(
        [sys.executable, "-m", "build", "--sdist", "--outdir", str(outdir)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    sdists = list(outdir.glob("*.tar.gz"))
    if not sdists:
        raise RuntimeError("no sdist produced")
    return sdists[0]


class WheelPackagingDistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import build  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("the 'build' package is not installed")
        cls._tmp = tempfile.TemporaryDirectory()
        try:
            cls.wheel = _build_wheel(Path(cls._tmp.name))
        except OSError as exc:
            cls._tmp.cleanup()
            raise unittest.SkipTest(
                f"wheel build unavailable in this environment: {exc}"
            )
        except (subprocess.CalledProcessError, RuntimeError) as exc:
            cls._tmp.cleanup()
            detail = getattr(exc, "stderr", "") or getattr(exc, "stdout", "") or ""
            raise AssertionError(
                "wheel build FAILED though the 'build' backend is installed; this is a "
                f"packaging defect, not an environment skip:\n{detail}\n{exc}"
            )
        cls.names = zipfile.ZipFile(cls.wheel).namelist()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "_tmp"):
            cls._tmp.cleanup()

    def test_wheel_ships_every_browser_asset_by_name(self):
        """E-01: Positive per-asset presence assertions for browser assets in the wheel."""
        missing = [name for name in REQUIRED_BROWSER_ASSETS if name not in self.names]
        self.assertEqual(
            missing,
            [],
            f"browser asset(s) missing from the wheel: {missing}. A gitignored or "
            f"out-of-package asset is dropped SILENTLY by hatchling at exit 0, so this positive "
            f"assertion is the only thing that catches it. Present assets: "
            f"{[n for n in self.names if 'run_analytics_assets' in n]}",
        )

    def test_wheel_browser_assets_are_non_empty(self):
        """E-01: Asset non-emptiness assertion in the wheel."""
        z = zipfile.ZipFile(self.wheel)
        sizes = {}
        for name in REQUIRED_BROWSER_ASSETS:
            with self.subTest(asset=name):
                self.assertIn(name, self.names)
                data = z.read(name)
                sizes[name] = len(data)
                self.assertGreater(len(data), 0, f"{name} shipped empty (0 bytes)")
        print(f"observed wheel asset sizes: {sizes}")

    def test_wheel_ships_protected_analytics_and_layout_modules_by_name(self):
        """E-01 / PR-001: Assert the four protected modules ship by name in the wheel."""
        missing = [m for m in PROTECTED_MODULES if m not in self.names]
        self.assertEqual(
            missing,
            [],
            f"protected modules missing from the wheel: {missing}",
        )

    def test_declared_assets_match_the_module(self):
        """E-02: Honesty guard ensuring REQUIRED_BROWSER_ASSETS matches run_analytics_spa."""
        from agent_workflows.run_analytics_spa import ASSETS_DIRNAME, REQUIRED_ASSETS

        expected = {
            f"agent_workflows/{ASSETS_DIRNAME}/{name}" for name in REQUIRED_ASSETS
        }
        declared = set(REQUIRED_BROWSER_ASSETS)
        diff_missing = sorted(expected - declared)
        diff_extra = sorted(declared - expected)
        self.assertEqual(
            declared,
            expected,
            f"REQUIRED_BROWSER_ASSETS out of sync with run_analytics_spa module! "
            f"Missing from test: {diff_missing}, Unexpected in test: {diff_extra}",
        )
        print(f"honesty guard verified: declared={declared}, expected={expected}")

    def test_a_gitignored_asset_would_be_detected_rather_than_silently_dropped(self):
        """E-03: Measured hazard arm reproducing hatchling silent gitignore drop."""
        with tempfile.TemporaryDirectory() as td:
            probe = Path(td)
            (probe / "pkg" / "assets").mkdir(parents=True)
            (probe / "pkg" / "__init__.py").write_text("", encoding="utf-8")
            for name in ("kept.css", "ignored.css"):
                (probe / "pkg" / "assets" / name).write_text("a{}", encoding="utf-8")
            (probe / "pyproject.toml").write_text(
                "[build-system]\n"
                'requires = ["hatchling"]\n'
                'build-backend = "hatchling.build"\n'
                "[project]\n"
                'name = "awprobepkg"\n'
                'version = "0.0.1"\n'
                "[tool.hatch.build.targets.wheel]\n"
                'packages = ["pkg"]\n',
                encoding="utf-8",
            )
            (probe / ".gitignore").write_text("ignored.css\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "build",
                    "--wheel",
                    "--outdir",
                    str(probe / "dist"),
                ],
                cwd=str(probe),
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                self.skipTest(f"probe build unavailable: {result.stderr[-300:]}")
            wheels = list((probe / "dist").glob("*.whl"))
            names = zipfile.ZipFile(wheels[0]).namelist()

            match = re.search(r"hatchling==([\w\.]+)", result.stderr)
            hatchling_version = match.group(1) if match else "resolved-by-build"

            print(
                f"probe measurement: hatchling {hatchling_version}, exit_code={result.returncode}, "
                f"kept_present={'pkg/assets/kept.css' in names}, ignored_present={'pkg/assets/ignored.css' in names}"
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("pkg/assets/kept.css", names)
            self.assertNotIn(
                "pkg/assets/ignored.css",
                names,
                "hatchling no longer honors .gitignore; the positive per-asset assertion above is "
                "still correct but this test's stated rationale needs updating",
            )

    def test_wheel_registers_three_console_scripts(self):
        """E-05: Console script registration and target mapping assertion."""
        ep = [n for n in self.names if n.endswith("entry_points.txt")]
        self.assertTrue(ep, "no entry_points.txt in wheel")
        text = zipfile.ZipFile(self.wheel).read(ep[0]).decode("utf-8")
        cp = configparser.ConfigParser()
        cp.read_string(text)
        self.assertIn(
            "console_scripts",
            cp.sections(),
            "no [console_scripts] section in entry_points.txt",
        )
        mapping = dict(cp["console_scripts"])
        expected = {
            "agent-workflows": "agent_workflows.cli:main",
            "agentwf": "agent_workflows.cli:main",
            "aw": "agent_workflows.cli:main",
        }
        self.assertEqual(
            mapping,
            expected,
            f"console_scripts mapping does not match expected: got {mapping}, expected {expected}",
        )
        print(f"console_scripts mapping: {mapping}")


class SdistPackagingDistributionTests(unittest.TestCase):
    """E-04: Sdist distribution contents assertions."""

    @classmethod
    def setUpClass(cls):
        try:
            import build  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("the 'build' package is not installed")
        cls._tmp = tempfile.TemporaryDirectory()
        try:
            cls.sdist = _build_sdist(Path(cls._tmp.name))
        except OSError as exc:
            cls._tmp.cleanup()
            raise unittest.SkipTest(f"sdist build unavailable: {exc}")
        except (subprocess.CalledProcessError, RuntimeError) as exc:
            cls._tmp.cleanup()
            detail = getattr(exc, "stderr", "") or getattr(exc, "stdout", "") or ""
            raise AssertionError(
                f"sdist build FAILED though 'build' is installed; a packaging defect:\n{detail}\n{exc}"
            )
        with tarfile.open(cls.sdist) as tar:
            # Strip the leading `<name>-<version>/` component so names match the wheel's form.
            # Skip directory members and members without a `/`.
            cls.names = [
                member.name.split("/", 1)[1]
                for member in tar.getmembers()
                if "/" in member.name and not member.isdir()
            ]

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "_tmp"):
            cls._tmp.cleanup()

    def test_sdist_ships_every_browser_asset_by_name(self):
        """E-04: Sdist ships browser assets by name."""
        missing = [name for name in REQUIRED_BROWSER_ASSETS if name not in self.names]
        self.assertEqual(
            missing,
            [],
            f"browser asset(s) missing from the sdist: {missing}. The sdist `include` is an "
            f"explicit allowlist, so an asset outside /agent_workflows is absent even when the "
            f"wheel carries it. Present: {[n for n in self.names if 'run_analytics_assets' in n]}",
        )
        print(f"sdist browser assets verified: {REQUIRED_BROWSER_ASSETS}")

    def test_sdist_ships_analytics_and_layout_modules_by_name(self):
        """E-04: Sdist ships analytics and layout modules by name."""
        missing = [m for m in PROTECTED_MODULES if m not in self.names]
        self.assertEqual(
            missing,
            [],
            f"protected modules missing from the sdist: {missing}",
        )
        print(f"sdist protected modules verified: {PROTECTED_MODULES}")

    def test_sdist_ships_bundled_system_data_tree(self):
        """E-04: Sdist ships the bundled system data tree."""
        self.assertTrue(
            any(n.startswith(".aw/system/") for n in self.names),
            "bundled .aw/system data tree missing from sdist",
        )
        self.assertIn(".aw/system/VERSION", self.names)
        self.assertIn(".aw/system/workflows/index.md", self.names)
        print(
            "sdist bundled system data tree verified (.aw/system/VERSION and .aw/system/workflows/index.md)"
        )


if __name__ == "__main__":
    unittest.main()
