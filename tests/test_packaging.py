"""Ship-vs-dev packaging gate (IPD-2 Batch B; acceptance criteria AC-11, AC-12).

Builds the wheel and asserts it contains ONLY the shipped product (the agent_workflows
package + the bundled .agents/workflows/ data under agent_workflows/_data/) and NOT the
dev/meta content (docs, prompts, tests, workflow-artifacts, meta docs), and that no runtime
dependency is declared.

Building needs the `build` package and an isolated-build backend fetch; when those are
unavailable (offline, or a minimal env) the test SKIPS rather than fails, so the
stdlib-only suite stays runnable everywhere. CI runs this for real on every OS.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from tests.support import REPO_ROOT

# Dev/meta content that MUST NOT appear in the wheel (ship-vs-dev boundary).
FORBIDDEN_TOP = ("tests/", "workflow-artifacts/")
# The source .agents/ tree is dev/meta EXCEPT .agents/workflows/, which is the shipped
# payload (bundled under agent_workflows/_data/). Nothing from these source subtrees may
# ship in any form (root or under _data/): docs (research/walkthroughs/specs/prompts/
# roadmaps), plans, and the operational prompts staging dir.
FORBIDDEN_AGENTS_SUBSTRINGS = (
    ".agents/docs/",
    ".agents/plans/",
    ".agents/prompts/",
    ".aw/records/",
    ".aw/state/",
)
FORBIDDEN_FILES = (
    "DECISIONS.md",
    "ARCHITECTURE.md",
    "CONTRIBUTING.md",
    "GUIDING_PRINCIPLES.md",
    "CITATION.cff",
)


#: runanalytics Order 07 (`6eq3oq`) E-02: the browser assets that MUST ship, named EXPLICITLY.
#:
#: WHY A POSITIVE, PER-ASSET ASSERTION EXISTS AT ALL. Everything else in this file asserts what must
#: NOT be present (`FORBIDDEN_TOP`, `FORBIDDEN_AGENTS_SUBSTRINGS`, `FORBIDDEN_FILES`) plus a handful
#: of named modules, so before this list the suite would have passed with EVERY browser asset
#: missing (measured: `7 passed`, and none of the seven would have noticed).
#:
#: AND THE FAILURE MODE IS SILENT, WHICH IS WHY ABSENCE-ONLY TESTING IS NOT ENOUGH HERE. Measured
#: with a probe package at execution: hatchling HONORS `.gitignore`, and a wheel built with an asset
#: matching an ignore pattern OMITTED it with exit code 0 and no warning on stderr. A missing asset
#: is therefore not a build error a human would see; it is a report that renders unstyled and inert
#: after install, with a green suite.
#:
#: Kept in sync with `run_analytics_spa.REQUIRED_ASSETS`, and `test_declared_assets_match_the_module`
#: asserts that rather than trusting it, so adding an asset to the module without adding it here
#: fails instead of silently reducing coverage.
REQUIRED_BROWSER_ASSETS = (
    "agent_workflows/run_analytics_assets/app.css",
    "agent_workflows/run_analytics_assets/app.js",
)


def _build_sdist(outdir: Path) -> Path:
    """Build an sdist into outdir; return its path. Raises to signal a skip on failure."""

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


def _build_wheel(outdir: Path) -> Path:
    """Build a wheel into outdir; return its path. Raises to signal a skip on failure."""

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


class PackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import build  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("the 'build' package is not installed")
        cls._tmp = tempfile.TemporaryDirectory()
        try:
            cls.wheel = _build_wheel(Path(cls._tmp.name))
        except (OSError,) as exc:
            # Environment cannot even spawn the build (no interpreter/tooling): a genuine
            # skip, not a package defect.
            cls._tmp.cleanup()
            raise unittest.SkipTest(
                f"wheel build unavailable in this environment: {exc}"
            )
        except (subprocess.CalledProcessError, RuntimeError) as exc:
            # The `build` backend IS installed (import succeeded above) but the build
            # FAILED. That is a real packaging defect (e.g. a force-include pointing at a
            # missing path), NOT an environment issue - fail loudly instead of hiding it
            # behind a skip.
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

    def test_wheel_contains_the_package(self):
        self.assertTrue(any(n.startswith("agent_workflows/") for n in self.names))
        self.assertIn("agent_workflows/cli.py", self.names)
        self.assertIn("agent_workflows/engine.py", self.names)
        self.assertIn("agent_workflows/versioning.py", self.names)
        # D93: the local-leaks surface must ship so `aw check-local-leaks` works post-install.
        self.assertIn("agent_workflows/local_leaks.py", self.names)
        # leak-sanitizer Set (IPD 20260721-1353-01): the unified engine that local_leaks now
        # re-exports must also ship, or the shim import breaks post-install.
        self.assertIn("agent_workflows/leak_sanitizer.py", self.names)
        # leak-sanitizer Set Order 2 (IPD 20260721-1851-01): the config wizard module is
        # imported by `aw sanitize --configure`, so it must ship too.
        self.assertIn("agent_workflows/leak_sanitizer_config.py", self.names)
        # revnjq / IPD m2h1z4: layout_inventory module must ship so migrate-layout works.
        self.assertIn("agent_workflows/layout_inventory.py", self.names)

    def test_wheel_ships_every_browser_asset_BY_NAME(self):
        """runanalytics Order 07 (`6eq3oq`) E-02: a POSITIVE assertion, one per asset.

        The rest of this file asserts ABSENCE of forbidden content, which would pass with every
        asset missing. This asserts PRESENCE, by name, because the failure mode is silent: hatchling
        honors `.gitignore` and drops a matching asset from the wheel at exit 0 with no warning
        (probe-verified).
        """

        missing = [name for name in REQUIRED_BROWSER_ASSETS if name not in self.names]
        self.assertEqual(
            missing,
            [],
            f"browser asset(s) missing from the wheel: {missing}. A gitignored or "
            f"out-of-package asset is dropped SILENTLY by hatchling at exit 0, so this positive "
            f"assertion is the only thing that catches it. Present assets: "
            f"{[n for n in self.names if 'run_analytics_assets' in n]}",
        )

    def test_wheel_browser_assets_are_NON_EMPTY(self):
        """A zero-byte asset ships as happily as a real one and renders exactly as badly."""

        z = zipfile.ZipFile(self.wheel)
        for name in REQUIRED_BROWSER_ASSETS:
            with self.subTest(asset=name):
                self.assertGreater(len(z.read(name)), 0, f"{name} shipped empty")

    def test_declared_assets_match_the_module(self):
        """The list above cannot silently fall behind the module's own declaration."""

        from agent_workflows.run_analytics_spa import ASSETS_DIRNAME, REQUIRED_ASSETS

        expected = tuple(
            f"agent_workflows/{ASSETS_DIRNAME}/{name}" for name in REQUIRED_ASSETS
        )
        self.assertEqual(sorted(REQUIRED_BROWSER_ASSETS), sorted(expected))

    def test_a_gitignored_asset_would_be_DETECTED_rather_than_silently_dropped(self):
        """The measured hatchling behavior, reproduced, so the hazard is demonstrated not asserted.

        Builds a throwaway probe package whose asset directory contains a gitignored file, and shows
        the wheel omits it at exit 0. That is the mechanism this module's positive assertion defends
        against, and demonstrating it here means the defense rests on a reproduced measurement rather
        than on a review note.
        """

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
            # The measured behavior: exit 0, kept file present, ignored file SILENTLY absent.
            self.assertEqual(result.returncode, 0)
            self.assertIn("pkg/assets/kept.css", names)
            self.assertNotIn(
                "pkg/assets/ignored.css",
                names,
                "hatchling no longer honors .gitignore; the positive per-asset assertion above is "
                "still correct but this test's stated rationale needs updating",
            )
            print(
                "MEASURED: hatchling honored .gitignore and omitted pkg/assets/ignored.css "
                f"from the wheel at exit {result.returncode} with no warning"
            )

    def test_wheel_bundles_workflow_tree_under_data(self):
        # AC-2/AC-8: the shipped bundle is mapped under agent_workflows/_data/.aw/system/,
        # NESTED (invokable bundle under workflows/, VERSION a system-root sibling).
        self.assertIn("agent_workflows/_data/.aw/system/workflows/index.md", self.names)
        self.assertIn("agent_workflows/_data/.aw/system/VERSION", self.names)
        self.assertTrue(
            any(
                n.startswith("agent_workflows/_data/.aw/system/workflows/")
                and "tools/" in n
                for n in self.names
            ),
            "expected the workflow tools under the bundled data tree",
        )
        # The bundle ships ONCE: the legacy .agents/workflows/ tree must NOT also ship.
        self.assertFalse(
            any(
                n.startswith("agent_workflows/_data/.agents/workflows/")
                for n in self.names
            ),
            "legacy .agents/workflows/ bundle double-shipped alongside .aw/system/",
        )

    def test_wheel_excludes_dev_and_meta_content(self):
        # AC-11: the ship-vs-dev gate.
        leaked = []
        for n in self.names:
            base = n.split("/")[-1]
            if any(n.startswith(p) for p in FORBIDDEN_TOP):
                leaked.append(n)
            elif any(s in n for s in FORBIDDEN_AGENTS_SUBSTRINGS):
                # The only shipped .agents/ content is .agents/workflows/ under _data/.
                leaked.append(n)
            elif base in FORBIDDEN_FILES:
                leaked.append(n)
        self.assertEqual(
            leaked, [], f"dev/meta content leaked into the wheel: {leaked}"
        )

    def test_wheel_declares_only_the_allowlisted_runtime_dependency(self):
        # AC-12, NARROWED from "zero runtime deps" to "an ALLOWLIST of exactly one" by IPD
        # `y6mfgo`, which declared `filelock`. The original blanket-zero assertion was written
        # under the framing DECISIONS D138 later corrected: D46 stated a FACT about the build of
        # the day (this wheel happens to have no runtime deps), and the "rule" reading was a
        # back-reference a later author added, never a policy D46 established. D138 makes the
        # operative principle dependency MINIMIZATION, not prohibition.
        #
        # So the gate still does real work, and arguably more of it: it PINS the exact dependency
        # set, so an accidental or unreviewed new runtime dep still fails here and has to be added
        # deliberately, with justification, exactly as `filelock` was. It just no longer forbids
        # the category outright.
        #
        # Why `filelock` earned it: six modules used to `import fcntl` at top level, so the package
        # failed at IMPORT on Windows before any of its own code could run. Hand-rolling the
        # replacement is the trap, because `msvcrt.locking` locks a BYTE RANGE rather than the whole
        # file, letting two processes hold "exclusive" locks on one file simultaneously. See
        # `agent_workflows/platform_lock.py`.
        #
        # Optional-dependency extras (declared with `; extra == '<name>'`, e.g. the test-only
        # pytest/pytest-xdist runner) remain unrestricted: they are never installed unless a user
        # asks for the extra and are not imported at runtime.
        ALLOWED_RUNTIME_DEPS = {"filelock"}

        meta = [n for n in self.names if n.endswith("METADATA")]
        self.assertTrue(meta, "no METADATA in wheel")
        text = zipfile.ZipFile(self.wheel).read(meta[0]).decode("utf-8")
        requires = [ln for ln in text.splitlines() if ln.startswith("Requires-Dist")]
        unconditional = [ln for ln in requires if "extra ==" not in ln]

        def _dist_name(line: str) -> str:
            # `Requires-Dist: filelock>=3` -> `filelock`
            spec = line.split(":", 1)[1].strip()
            for boundary in ("=", ">", "<", "!", "~", " ", "[", ";"):
                spec = spec.split(boundary, 1)[0]
            return spec.strip().lower()

        declared = {_dist_name(line) for line in unconditional}
        unexpected = sorted(declared - ALLOWED_RUNTIME_DEPS)
        self.assertEqual(
            unexpected,
            [],
            f"unexpected unconditional runtime dependencies {unexpected}: a new runtime dep "
            f"needs a deliberate justification (DECISIONS D138) and an update to this allowlist, "
            f"not a silent addition. Full set: {unconditional}",
        )
        # And the declared one must actually be there, so a silent DROP is caught too: the package
        # cannot import without it.
        self.assertEqual(
            declared,
            ALLOWED_RUNTIME_DEPS,
            f"the required runtime dependency is missing from the wheel: expected "
            f"{sorted(ALLOWED_RUNTIME_DEPS)}, got {sorted(declared)}",
        )
        print(f"wheel runtime deps (allowlisted): {unconditional}")

    def test_wheel_registers_three_console_scripts(self):
        ep = [n for n in self.names if n.endswith("entry_points.txt")]
        self.assertTrue(ep, "no entry_points.txt in wheel")
        text = zipfile.ZipFile(self.wheel).read(ep[0]).decode("utf-8")
        for script in ("agent-workflows", "aw", "agentwf"):
            self.assertIn(script, text)
        self.assertIn("agent_workflows.cli:main", text)

    def test_wheel_has_no_personal_path_leak(self):
        # D92: no maintainer-specific path/identity token may ship in the wheel. Tokens are
        # assembled at runtime so this test file itself carries no literal leak.
        z = zipfile.ZipFile(self.wheel)
        tokens = (
            "/home/" + "attacker-user",
            "a local checkout dir",
            "hermes" + "-agent",
            "uri" + "-ai-info",
            "rhody" + "-pact",
            "test_" + "user_1",
        )
        leaked = []
        for n in self.names:
            try:
                data = z.read(n).decode("utf-8", "replace")
            except Exception:
                continue
            for t in tokens:
                if t in data:
                    leaked.append(f"{t} in {n}")
        self.assertEqual(
            leaked, [], f"personal-path token(s) leaked into the wheel: {leaked}"
        )

    def test_installed_wheel_migrate_layout_without_tools(self):
        # revnjq / IPD m2h1z4: In an environment where the wheel is extracted/installed
        # without tools/ on the path, importing layout_migration and running migrate-layout
        # must succeed and must not raise ModuleNotFoundError: No module named 'tools'.
        with tempfile.TemporaryDirectory() as extract_dir:
            with zipfile.ZipFile(self.wheel) as z:
                z.extractall(extract_dir)

            cmd = [
                sys.executable,
                "-c",
                (
                    "import sys\n"
                    "# Ensure development checkout and tools/ are purged from sys.path\n"
                    "sys.path = [p for p in sys.path if p and 'agent-workflows' not in p and 'tools' not in p]\n"
                    "sys.path.insert(0, sys.argv[1])\n"
                    "import agent_workflows.layout_migration as lm\n"
                    "import agent_workflows.cli as cli\n"
                    "assert hasattr(lm, 'MigrationManager')\n"
                    "assert hasattr(lm, 'inv_mod')\n"
                    "assert hasattr(lm.inv_mod, 'inventory')\n"
                ),
                extract_dir,
            ]
            res = subprocess.run(
                cmd,
                cwd=extract_dir,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                res.returncode,
                0,
                f"importing layout_migration from installed wheel failed:\nstdout: {res.stdout}\nstderr: {res.stderr}",
            )
            self.assertNotIn("No module named 'tools'", res.stderr)
            self.assertNotIn("ModuleNotFoundError", res.stderr)

            # Also verify migrate-layout CLI invocation on a dummy repo runs without ModuleNotFoundError
            with tempfile.TemporaryDirectory() as dummy_repo:
                cli_cmd = [
                    sys.executable,
                    "-c",
                    (
                        "import sys\n"
                        "sys.path = [p for p in sys.path if p and 'agent-workflows' not in p and 'tools' not in p]\n"
                        "sys.path.insert(0, sys.argv[1])\n"
                        "from agent_workflows.cli import main\n"
                        "sys.argv = ['aw', 'migrate-layout', '--help']\n"
                        "sys.exit(main())\n"
                    ),
                    extract_dir,
                ]
                cli_res = subprocess.run(
                    cli_cmd,
                    cwd=dummy_repo,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    cli_res.returncode,
                    0,
                    f"migrate-layout --help failed:\nstdout: {cli_res.stdout}\nstderr: {cli_res.stderr}",
                )
                self.assertNotIn("ModuleNotFoundError", cli_res.stderr)


class SdistBrowserAssetTests(unittest.TestCase):
    """runanalytics Order 07 (`6eq3oq`) E-02: the assets must ship in the SDIST too.

    A SEPARATE CLASS because it needs a separate build, and a separate ASSERTION because the sdist
    include list is a different mechanism from the wheel's: `[tool.hatch.build.targets.sdist].include`
    is an EXPLICIT ALLOWLIST (`/agent_workflows`, `/.aw/system`, `/hatch_build.py`, `/pyproject.toml`,
    `/README.md`, `/LICENSE`, `/NOTICE`), so anything outside `/agent_workflows` is absent from the
    sdist even when the wheel carries it. Asserting only the wheel would leave that half unchecked.
    """

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
                f"sdist build FAILED though 'build' is installed; a packaging defect:\n{detail}"
            )
        import tarfile

        with tarfile.open(cls.sdist) as tar:
            # Strip the leading `<name>-<version>/` component so names match the wheel's form.
            cls.names = [
                member.name.split("/", 1)[1]
                for member in tar.getmembers()
                if "/" in member.name
            ]

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "_tmp"):
            cls._tmp.cleanup()

    def test_sdist_ships_every_browser_asset_BY_NAME(self):
        missing = [name for name in REQUIRED_BROWSER_ASSETS if name not in self.names]
        self.assertEqual(
            missing,
            [],
            f"browser asset(s) missing from the sdist: {missing}. The sdist `include` is an "
            f"explicit allowlist, so an asset outside /agent_workflows is absent even when the "
            f"wheel carries it. Present: {[n for n in self.names if 'run_analytics_assets' in n]}",
        )

    def test_sdist_ships_the_analytics_modules_that_read_those_assets(self):
        for module in (
            "agent_workflows/run_analytics_spa.py",
            "agent_workflows/run_analytics_report.py",
        ):
            with self.subTest(module=module):
                self.assertIn(module, self.names)


if __name__ == "__main__":
    unittest.main()
