"""Ship-vs-dev packaging guard (behavioral wheel inspection).

Builds the wheel and asserts:
1. The ship-vs-dev boundary: the wheel contains ONLY the shipped product
   (the agent_workflows package + bundled .aw/system data under agent_workflows/_data/)
   and NONE of the dev/meta content (tests/, workflow-artifacts/, records/, state/, meta docs).
   Asserts positive presence of package and data tree as well as absence of forbidden paths.
2. The runtime dependency allowlist: the unconditional Requires-Dist declarations
   match exactly the allowed runtime dependencies ({"filelock"}), with extras excluded.

Decision on pytest.mark.slow (E-04 / OQ-01):
The file is deliberately NOT marked `pytest.mark.slow`.
Measured build costs at execution HEAD:
- Warm build 1: 6.69s
- Warm build 2: 7.99s
- Cold cache build: 6.70s
These run comfortably inside conftest.py's 90.0s _DEFAULT_TEST_TIMEOUT.
Because pyproject.toml's default addopts deselects `slow` tests (-m 'not slow and not livecorpus'),
and CI's slow test step carries `continue-on-error: true` (making it advisory), marking this
test `slow` would leave the ship-vs-dev boundary without any blocking gate in routine runs,
lane integration, or CI. Leaving it unmarked ensures the guard runs and blocks regressions.

Environment handling:
Building requires the `build` package and isolated environment build tooling.
If `import build` fails (minimal environment), the test skips via unittest.SkipTest.
If `build` is importable but the wheel build fails, the test raises AssertionError
to fail loudly, ensuring real build failures are never concealed as skips.
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
#
# Anchoring and token formatting (F-5 / review measurement):
# `FORBIDDEN_TOP` tokens retain their trailing slashes (e.g. "workflow-artifacts/").
# The wheel legitimately ships the template file:
#   agent_workflows/_data/.aw/system/workflows/templates/workflow-artifacts-README.md
# That filename contains a hyphen, not a slash, so matching "workflow-artifacts/"
# produces ZERO false positives under either startswith or bare substring matching
# (re-measured on the built wheel: 0 hits across all entries).
# The real hazard is loosening the token to a slash-less form ("workflow-artifacts"),
# which WOULD incorrectly match the shipped template file.
# We retain the startswith anchoring and trailing slashes.
FORBIDDEN_TOP = ("tests/", "workflow-artifacts/")
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

    def test_wheel_ship_vs_dev_boundary(self):
        """Assert ship-vs-dev boundary: package and data are present, dev/meta content is absent."""
        # Positive presence assertions (prevents passing on an empty wheel)
        self.assertTrue(
            any(n.startswith("agent_workflows/") for n in self.names),
            "agent_workflows package missing from wheel",
        )
        self.assertIn("agent_workflows/cli.py", self.names)
        self.assertTrue(
            any(n.startswith("agent_workflows/_data/.aw/system/") for n in self.names),
            "bundled .aw/system data tree missing from wheel",
        )
        self.assertIn("agent_workflows/_data/.aw/system/VERSION", self.names)
        self.assertIn("agent_workflows/_data/.aw/system/workflows/index.md", self.names)

        # Absence assertions (forbidden dev/meta content)
        leaked = []
        for n in self.names:
            base = n.split("/")[-1]
            if any(n.startswith(p) for p in FORBIDDEN_TOP):
                leaked.append(n)
            elif any(s in n for s in FORBIDDEN_AGENTS_SUBSTRINGS):
                leaked.append(n)
            elif base in FORBIDDEN_FILES:
                leaked.append(n)
        self.assertEqual(
            leaked, [], f"dev/meta content leaked into the wheel: {leaked}"
        )

    def test_wheel_declares_only_the_allowlisted_runtime_dependency(self):
        """Assert wheel unconditional runtime dependencies equal exactly {"filelock"}.

        DECISIONS D138: Dependency minimization is a principle, not an absolute
        prohibition. The allowed runtime dependency (filelock) replaces unportable
        fcntl usage across platforms. Extras (such as test dependencies) are
        excluded from this assertion.
        """
        ALLOWED_RUNTIME_DEPS = {"filelock"}

        meta = [n for n in self.names if n.endswith("METADATA")]
        self.assertTrue(meta, "no METADATA in wheel")
        text = zipfile.ZipFile(self.wheel).read(meta[0]).decode("utf-8")
        requires = [ln for ln in text.splitlines() if ln.startswith("Requires-Dist")]
        unconditional = [ln for ln in requires if "extra ==" not in ln]

        def _dist_name(line: str) -> str:
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
        self.assertEqual(
            declared,
            ALLOWED_RUNTIME_DEPS,
            f"the required runtime dependency is missing from the wheel: expected "
            f"{sorted(ALLOWED_RUNTIME_DEPS)}, got {sorted(declared)}",
        )


if __name__ == "__main__":
    unittest.main()
