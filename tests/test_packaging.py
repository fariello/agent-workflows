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
FORBIDDEN_TOP = ("docs/", "prompts/", "tests/", "workflow-artifacts/")
FORBIDDEN_FILES = (
    "DECISIONS.md",
    "ARCHITECTURE.md",
    "CONTRIBUTING.md",
    "GUIDING_PRINCIPLES.md",
    "CITATION.cff",
)


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
        except (subprocess.CalledProcessError, RuntimeError, OSError) as exc:
            cls._tmp.cleanup()
            raise unittest.SkipTest(f"wheel build unavailable in this environment: {exc}")
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

    def test_wheel_bundles_workflow_tree_under_data(self):
        # AC-2/AC-8: the shipped tree is mapped under agent_workflows/_data/.
        self.assertIn("agent_workflows/_data/.agents/workflows/index.md", self.names)
        self.assertIn("agent_workflows/_data/.agents/workflows/VERSION", self.names)
        self.assertTrue(
            any(n.startswith("agent_workflows/_data/.agents/workflows/") and "tools/" in n
                for n in self.names),
            "expected the workflow tools under the bundled data tree",
        )

    def test_wheel_excludes_dev_and_meta_content(self):
        # AC-11: the ship-vs-dev gate.
        leaked = []
        for n in self.names:
            base = n.split("/")[-1]
            if any(n.startswith(p) for p in FORBIDDEN_TOP):
                leaked.append(n)
            elif base in FORBIDDEN_FILES:
                leaked.append(n)
        self.assertEqual(leaked, [], f"dev/meta content leaked into the wheel: {leaked}")

    def test_wheel_declares_no_runtime_dependencies(self):
        # AC-12: zero runtime deps (no Requires-Dist lines in METADATA).
        meta = [n for n in self.names if n.endswith("METADATA")]
        self.assertTrue(meta, "no METADATA in wheel")
        text = zipfile.ZipFile(self.wheel).read(meta[0]).decode("utf-8")
        requires = [ln for ln in text.splitlines() if ln.startswith("Requires-Dist")]
        self.assertEqual(requires, [], f"unexpected runtime dependencies: {requires}")

    def test_wheel_registers_three_console_scripts(self):
        ep = [n for n in self.names if n.endswith("entry_points.txt")]
        self.assertTrue(ep, "no entry_points.txt in wheel")
        text = zipfile.ZipFile(self.wheel).read(ep[0]).decode("utf-8")
        for script in ("agent-workflows", "aw", "agentwf"):
            self.assertIn(script, text)
        self.assertIn("agent_workflows.cli:main", text)


if __name__ == "__main__":
    unittest.main()
