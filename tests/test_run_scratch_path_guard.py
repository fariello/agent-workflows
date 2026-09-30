"""Restored and widened run-scratch path guard.

This is the regression guard deleted by `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"),
restored under plan `fzueyy` (Set `wfartgrowth`).

Order 07 (spec `20260817-2124-01`) moved run scratch from a repo-root `workflow-artifacts/` to
`.aw/workflow-artifacts/`. Order 03 (`9x1rps`) added the original regression guard in `tests/test_docs.py`
to prevent recurrence of the D92 leak (where unignored run records carrying sensitive home paths and
session detail could be created).

Under plan `fzueyy`, this guard is restored and widened from the shipped workflow tree alone to three
surfaces:
1. Shipped workflow bodies: `.aw/system/workflows/**/*.{md,py}` excluding `__pycache__`.
2. Documentation pages: `docs/**/*.md`.
3. Root user-facing docs: `*.md` in repository root, derived via glob minus an explicit exclusion constant.
"""

import re
import unittest

from tests.support import REPO_ROOT

ROOT_DOC_EXCLUSIONS: dict[str, str] = {
    "DECISIONS.md": "Dated historical record; past decisions (e.g. D19) legitimately name the path in use at the time.",
    "CHANGELOG.md": "Dated historical record; past release notes legitimately name the path in use at the time.",
}


def _bare_run_scratch_refs(text: str) -> list[str]:
    """Return every BARE `workflow-artifacts/` PATH reference in ``text``.

    THE UNIT IS OCCURRENCES, NOT LINES (wfartifacts Order 03, finding F-8): some lines carry
    two references, so a line-based sweep under-reports and reports itself complete while
    references remain.

    THREE SPELLINGS ARE DELIBERATELY NOT MATCHED, because none of them is a stale path:

    1. `.aw/workflow-artifacts/` - the live, correct path (the negative lookbehind).
    2. `/workflow-artifacts/` as the ANCHORED GITIGNORE PATTERN. Patterns in the
       framework-owned `.aw/.gitignore` are `.aw/`-relative, so the pattern that ignores run
       scratch is written `/workflow-artifacts/` and a body naming it is CORRECT. Any
       slash-preceded form is therefore allowed, which subsumes case 1.
    3. `workflow-artifacts-README.md`, the installer TEMPLATE FILENAME under
       `.aw/system/workflows/templates/` (a hyphen, not a slash, follows), plus the bare
       segment name in `assess/tools/scan_secrets.py`'s `SKIP_DIR_NAMES` (no trailing slash),
       which must stay bare because that set is matched per path SEGMENT.
    """

    return re.findall(r"(?<![/\w-])workflow-artifacts/", text)


def _shipped_bodies(root=REPO_ROOT):
    workflows_dir = root / ".aw" / "system" / "workflows"
    if not workflows_dir.is_dir():
        return
    for suffix in ("*.md", "*.py"):
        for path in sorted(workflows_dir.rglob(suffix)):
            # `__pycache__` holds compiled build output, not editable shipped bodies;
            # counting it once inflated this surface from 25 files to 28 (finding F-7).
            if "__pycache__" in path.parts:
                continue
            yield path


def _docs_pages(root=REPO_ROOT):
    docs_dir = root / "docs"
    if not docs_dir.is_dir():
        return
    for path in sorted(docs_dir.rglob("*.md")):
        yield path


def _root_docs(root=REPO_ROOT):
    for path in sorted(root.glob("*.md")):
        if path.name not in ROOT_DOC_EXCLUSIONS:
            yield path


def sweep_surfaces(root=REPO_ROOT) -> dict[str, dict]:
    surfaces = {
        "shipped": list(_shipped_bodies(root)),
        "docs": list(_docs_pages(root)),
        "root-docs": list(_root_docs(root)),
    }
    results = {}
    for name, paths in surfaces.items():
        scanned = 0
        offenders: list[str] = []
        doubled_prefix: list[str] = []
        for path in paths:
            scanned += 1
            text = path.read_text(encoding="utf-8")
            hits = _bare_run_scratch_refs(text)
            rel = path.relative_to(root).as_posix()
            if hits:
                offenders.append(f"{rel}: {len(hits)} bare reference(s)")
            if ".aw/.aw/" in text:
                doubled_prefix.append(f"{rel}: contains '.aw/.aw/'")
        results[name] = {
            "scanned": scanned,
            "offenders": offenders,
            "doubled_prefix": doubled_prefix,
        }
    return results


class ShippedRunScratchPathTests(unittest.TestCase):
    """wfartifacts Order 03: no shipped workflow body or doc may name the RETIRED run-scratch path.

    Order 07 (spec `20260817-2124-01`) moved run scratch from a repo-root `workflow-artifacts/`
    to `.aw/workflow-artifacts/`, but references decayed across documentation surfaces.
    Plan `fzueyy` restored and widened this guard to protect shipped workflows, `docs/`, and
    user-facing root docs.
    """

    def test_shipped_dir_exists(self):
        workflows_dir = REPO_ROOT / ".aw" / "system" / "workflows"
        self.assertTrue(workflows_dir.is_dir(), workflows_dir)

    def test_docs_dir_exists(self):
        docs_dir = REPO_ROOT / "docs"
        self.assertTrue(docs_dir.is_dir(), docs_dir)

    def test_no_bare_run_scratch_path_in_swept_surfaces(self):
        results = sweep_surfaces(REPO_ROOT)
        # Non-emptiness assertions per surface (PR-702, F-11)
        self.assertTrue(
            results["shipped"]["scanned"] > 0,
            "no files were scanned for surface 'shipped'",
        )
        self.assertTrue(
            results["docs"]["scanned"] > 0,
            "no files were scanned for surface 'docs'",
        )
        self.assertTrue(
            results["root-docs"]["scanned"] > 0,
            "no files were scanned for surface 'root-docs'",
        )

        for surface_name in ("shipped", "docs", "root-docs"):
            self.assertEqual(
                results[surface_name]["offenders"],
                [],
                f"{surface_name} surface files name the RETIRED repo-root run-scratch path; "
                f"write `.aw/workflow-artifacts/` instead:\n"
                + "\n".join(results[surface_name]["offenders"]),
            )

    def test_no_doubled_aw_prefix_in_swept_surfaces(self):
        results = sweep_surfaces(REPO_ROOT)
        for surface_name in ("shipped", "docs", "root-docs"):
            self.assertTrue(
                results[surface_name]["scanned"] > 0,
                f"no files were scanned for surface '{surface_name}'",
            )
            self.assertEqual(
                results[surface_name]["doubled_prefix"],
                [],
                f"{surface_name} surface files contain doubled '.aw/.aw/' prefix:\n"
                + "\n".join(results[surface_name]["doubled_prefix"]),
            )


class ShippedRunScratchGuardFalsifiabilityTests(unittest.TestCase):
    """The guard must FAIL on a reintroduced reference; one that cannot fail proves nothing."""

    def test_detects_reintroduced_bare_reference(self):
        self.assertEqual(
            _bare_run_scratch_refs(
                "Write the run record to `workflow-artifacts/assess-security/<RUN_ID>/`."
            ),
            ["workflow-artifacts/"],
        )

    def test_detects_two_references_on_one_line(self):
        # The F-8 unit error: a line-based check would count this once and miss a rewrite.
        self.assertEqual(
            len(
                _bare_run_scratch_refs(
                    "Do NOT commit workflow-artifacts/ and never force-add workflow-artifacts/ either."
                )
            ),
            2,
        )

    def test_allows_the_live_prefixed_path(self):
        self.assertEqual(
            _bare_run_scratch_refs("Run records live under `.aw/workflow-artifacts/`."),
            [],
        )

    def test_allows_the_anchored_gitignore_pattern(self):
        self.assertEqual(
            _bare_run_scratch_refs(
                "`.aw/.gitignore` carries the anchored pattern `/workflow-artifacts/`."
            ),
            [],
        )

    def test_allows_the_installer_template_filename(self):
        self.assertEqual(
            _bare_run_scratch_refs("`workflow-artifacts-README.md` is a template."), []
        )

    def test_allows_the_bare_segment_name_used_as_code(self):
        # scan_secrets.py's SKIP_DIR_NAMES holds path SEGMENTS, which carry no slash.
        self.assertEqual(_bare_run_scratch_refs('    "workflow-artifacts",'), [])

    def _create_temp_tree(self):
        import shutil
        import tempfile
        from pathlib import Path

        tmpdir = tempfile.TemporaryDirectory()
        tmp = Path(tmpdir.name)
        shutil.copytree(
            REPO_ROOT / ".aw" / "system" / "workflows",
            tmp / ".aw" / "system" / "workflows",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        shutil.copytree(REPO_ROOT / "docs", tmp / "docs")
        for p in REPO_ROOT.glob("*.md"):
            shutil.copy2(p, tmp / p.name)
        return tmpdir, tmp

    def test_sweep_honors_root_doc_exclusions(self):
        tmpdir, tmp = self._create_temp_tree()
        self.addCleanup(tmpdir.cleanup)
        # Poison an excluded root doc with a bare run scratch reference
        target = tmp / "DECISIONS.md"
        target.write_text(
            target.read_text(encoding="utf-8") + "\nworkflow-artifacts/\n",
            encoding="utf-8",
        )
        results = sweep_surfaces(tmp)
        self.assertTrue(results["root-docs"]["scanned"] > 0)
        self.assertEqual(results["root-docs"]["offenders"], [])

    def test_sweep_detects_poisoned_shipped_body(self):
        tmpdir, tmp = self._create_temp_tree()
        self.addCleanup(tmpdir.cleanup)
        target = tmp / ".aw" / "system" / "workflows" / "plan-review" / "plan-review.md"
        target.write_text(
            target.read_text(encoding="utf-8") + "\nworkflow-artifacts/\n",
            encoding="utf-8",
        )
        results = sweep_surfaces(tmp)
        self.assertEqual(
            results["shipped"]["offenders"],
            [".aw/system/workflows/plan-review/plan-review.md: 1 bare reference(s)"],
        )
        self.assertEqual(results["docs"]["offenders"], [])
        self.assertEqual(results["root-docs"]["offenders"], [])

    def test_sweep_detects_poisoned_docs_page(self):
        tmpdir, tmp = self._create_temp_tree()
        self.addCleanup(tmpdir.cleanup)
        target = tmp / "docs" / "architecture.md"
        target.write_text(
            target.read_text(encoding="utf-8") + "\nworkflow-artifacts/\n",
            encoding="utf-8",
        )
        results = sweep_surfaces(tmp)
        self.assertEqual(results["shipped"]["offenders"], [])
        self.assertEqual(
            results["docs"]["offenders"],
            ["docs/architecture.md: 1 bare reference(s)"],
        )
        self.assertEqual(results["root-docs"]["offenders"], [])

    def test_sweep_detects_poisoned_root_doc(self):
        tmpdir, tmp = self._create_temp_tree()
        self.addCleanup(tmpdir.cleanup)
        target = tmp / "ARCHITECTURE.md"
        target.write_text(
            target.read_text(encoding="utf-8") + "\nworkflow-artifacts/\n",
            encoding="utf-8",
        )
        results = sweep_surfaces(tmp)
        self.assertEqual(results["shipped"]["offenders"], [])
        self.assertEqual(results["docs"]["offenders"], [])
        self.assertEqual(
            results["root-docs"]["offenders"],
            ["ARCHITECTURE.md: 1 bare reference(s)"],
        )
