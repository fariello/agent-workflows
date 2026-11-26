"""Guard tests for the cumulative metastore cutover code patch.

IPD 2k5t16 / E-05, V-05 (spec 4sd62s section 5.2 and C10a).

`.aw/system/cutover/metastore-code.cutover.patch` is written relative to HEAD plus the
documentation patch (`metastore-docs.cutover.patch`), so this test fills a temporary
GIT_INDEX_FILE from HEAD, applies the docs patch to it, and then apply-checks the code patch.
Nothing touches the working tree or the real index.

`AW_CUTOVER_CODE_PATCH` overrides the code patch path, so the same check can be pointed at a
scratch copy. This module reads and applies the two patch files; it does not inspect production
source code. Order 13 (`cxxmyv` E-08) removes both patches and this guard test at the cutover
commit.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import pytest


pytestmark = pytest.mark.core

REPO_ROOT = Path(__file__).resolve().parents[1]
CUTOVER_DIR = REPO_ROOT / ".aw" / "system" / "cutover"
DOCS_PATCH = CUTOVER_DIR / "metastore-docs.cutover.patch"
CODE_PATCH = Path(
    os.environ.get("AW_CUTOVER_CODE_PATCH")
    or CUTOVER_DIR / "metastore-code.cutover.patch"
)


def _patch_lf_bytes(patch_path: Path) -> bytes:
    """Read patch_path normalized to LF so Windows core.autocrlf checkouts match the LF git index."""
    return patch_path.read_bytes().replace(b"\r\n", b"\n")


def _git(
    args: list[str], env: dict[str, str], *, input_bytes: bytes | None = None
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        env=env,
        input=input_bytes,
        capture_output=True,
        check=False,
    )


def _apply_on_temp_index(docs_patch: Path, code_patch: Path) -> tuple[int, int, str]:
    """Return (docs exit, code-check exit, stderr) on a temporary index filled from HEAD."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(Path(tmp_dir) / "temp.index")
        read_tree = _git(["read-tree", "HEAD"], env)
        if read_tree.returncode != 0:
            raise AssertionError(
                f"git read-tree HEAD failed: "
                f"{read_tree.stderr.decode('utf-8', errors='replace').strip()}"
            )
        docs = _git(
            ["apply", "--cached", "-"], env, input_bytes=_patch_lf_bytes(docs_patch)
        )
        if docs.returncode != 0:
            return docs.returncode, -1, docs.stderr.decode("utf-8", errors="replace")
        code = _git(
            ["apply", "--cached", "--check", "-"],
            env,
            input_bytes=_patch_lf_bytes(code_patch),
        )
        return (
            docs.returncode,
            code.returncode,
            code.stderr.decode("utf-8", errors="replace"),
        )


class MetastoreCutoverCodePatchGuardTests(unittest.TestCase):
    """Keep the cutover code patch applying on top of HEAD plus the docs patch."""

    def test_code_patch_applies_after_docs_patch(self) -> None:
        self.assertTrue(DOCS_PATCH.is_file(), f"docs patch is missing: {DOCS_PATCH}")
        self.assertTrue(CODE_PATCH.is_file(), f"code patch is missing: {CODE_PATCH}")
        docs_rc, code_rc, stderr = _apply_on_temp_index(DOCS_PATCH, CODE_PATCH)
        self.assertEqual(
            docs_rc, 0, f"docs patch no longer applies to HEAD:\n{stderr.strip()}"
        )
        self.assertEqual(
            code_rc,
            0,
            f"code patch no longer applies to HEAD plus the docs patch:\n{stderr.strip()}",
        )

    def test_code_patch_touches_files(self) -> None:
        stat = subprocess.run(
            ["git", "apply", "--numstat", "-"],
            cwd=REPO_ROOT,
            input=_patch_lf_bytes(CODE_PATCH),
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            stat.returncode, 0, stat.stderr.decode("utf-8", errors="replace").strip()
        )
        self.assertTrue(
            stat.stdout.decode("utf-8", errors="replace").strip(),
            "code patch touches no files",
        )

    def test_check_refuses_a_patch_that_no_longer_applies(self) -> None:
        """The check is not vacuous: a code patch whose context is wrong is refused."""
        bad = (
            "diff --git a/agent_workflows/artifact_meta.py b/agent_workflows/artifact_meta.py\n"
            "--- a/agent_workflows/artifact_meta.py\n"
            "+++ b/agent_workflows/artifact_meta.py\n"
            "@@ -1,1 +1,1 @@\n"
            "-this context line does not exist in the file\n"
            "+replacement\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_patch = Path(tmp_dir) / "bad.patch"
            bad_patch.write_bytes(bad.encode("utf-8"))
            docs_rc, code_rc, _stderr = _apply_on_temp_index(DOCS_PATCH, bad_patch)
        self.assertEqual(docs_rc, 0)
        self.assertNotEqual(code_rc, 0)
