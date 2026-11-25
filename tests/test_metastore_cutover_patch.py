"""Guard tests for the cumulative metastore cutover documentation patch.

IPD 90iqr1 / E-09, V-09 (spec 4sd62s section 5.4 and C10a).

Verifies that `.aw/system/cutover/metastore-docs.cutover.patch`:
1. Applies cleanly against HEAD via a temporary GIT_INDEX_FILE (no clone).
2. Touches every file marked `rewrite` in the `qhay6a` F-03 disposition table.
3. Touches no file outside the `90iqr1` F-08 allowed documentation set.

This test module reads and applies the patch file; it does not inspect
production source code. Order 13 (`cxxmyv` E-08) removes the patch file and
this guard test at the cutover commit.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

import pytest


pytestmark = pytest.mark.core

REPO_ROOT = Path(__file__).resolve().parents[1]
PATCH_PATH = REPO_ROOT / ".aw" / "system" / "cutover" / "metastore-docs.cutover.patch"

# Copied from the `qhay6a` F-03 disposition table (all 40 rows marked `rewrite`)
# so this test does not depend on reading a plan record that `cxxmyv` retires.
REQUIRED_REWRITE_FILES: frozenset[str] = frozenset(
    {
        "AGENTS.md",
        "agent_workflows/cli.py",
        "agent_workflows/engine.py",
        "agent_workflows/ipd_schema.py",
        ".aw/records/backlog/README.md",
        ".aw/records/plans/README.md",
        ".aw/records/prompts/README.md",
        ".aw/records/releases/README.md",
        ".aw/records/reviews/README.md",
        ".aw/records/specs/README.md",
        ".aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md",
        ".aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md",
        ".aw/records/walkthroughs/README.md",
        ".aw/system/workflows/assess-all/assess-all.md",
        ".aw/system/workflows/assess/assess.md",
        ".aw/system/workflows/assess/templates/ipd.md",
        ".aw/system/workflows/assess/templates/orchestrator-ipd.md",
        ".aw/system/workflows/incident/incident.md",
        ".aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md",
        ".aw/system/workflows/migrate/migrate.md",
        ".aw/system/workflows/plan-review-long/02-review-and-revise.md",
        ".aw/system/workflows/plan-review-long/03-resolve-and-finalize.md",
        ".aw/system/workflows/plan-review-long/plan-review-long.md",
        ".aw/system/workflows/plan-review-long/review-rubric.md",
        ".aw/system/workflows/plan-review/steps/_findings.md",
        ".aw/system/workflows/plan-review/steps/r2-executability.md",
        ".aw/system/workflows/plan-review/steps/s6-rereview.md",
        ".aw/system/workflows/plan-review/steps/s7-finalize.md",
        ".aw/system/workflows/research-prompt/research-prompt.md",
        ".aw/system/workflows/spec-review/README.md",
        ".aw/system/workflows/spec-review/spec-review.md",
        ".aw/system/workflows/spec/spec.md",
        ".aw/system/workflows/templates/plans-README.md",
        ".aw/system/workflows/templates/prompts-README.md",
        ".aw/system/workflows/verify-execution/intent-audit.md",
        ".aw/system/workflows/verify-execution/verify-execution.md",
        ".aw/system/workflows/whatnext/whatnext.md",
        "docs/artifact-lifecycles.md",
        "docs/cli-output-contract.md",
        "docs/run-analytics.md",
    }
)

# Allowed documentation set from `90iqr1` F-08.
ALLOWED_PREFIXES: tuple[str, ...] = (
    ".aw/system/workflows/",
    ".aw/system/cutover/",
    "docs/",
)

ALLOWED_EXACT_PATHS: frozenset[str] = frozenset(
    {
        "AGENTS.md",
        "CONTRIBUTING.md",
        "README.md",
        ".aw/AGENT_QUICKSTART.md",
        ".aw/QUICKSTART.md",
        ".aw/system/managed-sections.json",
        ".aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md",
        ".aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md",
        "agent_workflows/cli.py",
        "agent_workflows/engine.py",
        "agent_workflows/ipd_schema.py",
    }
)

RECORDS_README_RE = re.compile(r"^\.aw/records/[^/]+/README\.md$")


def _is_in_allowed_documentation_set(rel_path: str) -> bool:
    """Return True when rel_path belongs to the 90iqr1 F-08 documentation set."""
    if rel_path in ALLOWED_EXACT_PATHS:
        return True
    if any(rel_path.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        return True
    return bool(RECORDS_README_RE.match(rel_path))


def _patch_touched_paths(patch_path: Path) -> set[str]:
    """Return the set of repository-relative paths touched by patch_path."""
    proc = subprocess.run(
        ["git", "apply", "--numstat", str(patch_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"git apply --numstat failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )
    paths: set[str] = set()
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            raise AssertionError(f"Unexpected git apply --numstat line: {line!r}")
        paths.add(parts[2])
    return paths


class MetastoreCutoverPatchGuardTests(unittest.TestCase):
    """Guard tests keeping the cutover docs patch applicable and scoped."""

    def test_patch_applies_cleanly_to_head(self) -> None:
        """Apply-check the patch against HEAD using a temporary GIT_INDEX_FILE."""
        self.assertTrue(
            PATCH_PATH.is_file(),
            f"Cutover documentation patch is missing: {PATCH_PATH}",
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            env = os.environ.copy()
            env["GIT_INDEX_FILE"] = str(Path(tmp_dir) / "temp.index")

            read_tree = subprocess.run(
                ["git", "read-tree", "HEAD"],
                cwd=REPO_ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                read_tree.returncode,
                0,
                f"git read-tree HEAD failed: {read_tree.stderr.strip()}",
            )

            apply_check = subprocess.run(
                ["git", "apply", "--cached", "--check", str(PATCH_PATH)],
                cwd=REPO_ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                apply_check.returncode,
                0,
                f"Cutover docs patch no longer applies cleanly to HEAD:\n"
                f"{apply_check.stderr.strip()}",
            )

    def test_patch_covers_all_f03_rewrite_files(self) -> None:
        """Every file marked `rewrite` in `qhay6a` F-03 must be touched by the patch."""
        touched = _patch_touched_paths(PATCH_PATH)
        missing = sorted(REQUIRED_REWRITE_FILES - touched)
        self.assertEqual(
            missing,
            [],
            f"Cutover docs patch is missing required F-03 rewrite file(s): {missing}",
        )

    def test_patch_touches_only_f08_documentation_set(self) -> None:
        """No file outside the `90iqr1` F-08 documentation set may be touched."""
        touched = _patch_touched_paths(PATCH_PATH)
        self.assertTrue(touched, "Cutover docs patch touched no files.")
        disallowed = sorted(
            path for path in touched if not _is_in_allowed_documentation_set(path)
        )
        self.assertEqual(
            disallowed,
            [],
            f"Cutover docs patch touches path(s) outside 90iqr1 F-08: {disallowed}",
        )


if __name__ == "__main__":
    unittest.main()
