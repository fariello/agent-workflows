"""Tests for recursive and ignored-path-aware spec enumeration (IPD y4bdoz).

Verifies that specs placed in subdirectories (such as lifecycle status directories)
are discovered by `specs._spec_files` and `aw specs check`, while gitignored
directories (such as `records/*/untracked/`) and standard skip names (README.md,
INDEX.md, STATUS.md) are excluded.
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agent_workflows import check_engine, specs


def _spec_content(status: str = "approved", id6: str = "test01") -> str:
    return (
        f"# Spec: Test Spec {id6}\n\n"
        f"- Date: 2026-09-08\n"
        f"- Status: {status}\n"
        f"- Author: tester\n"
        f"- Id: {id6}\n\n"
        f"## Body\n\n"
        f"Spec body text.\n\n"
        f"## Workflow history\n"
        f"- 2026-09-08 draft (tester): created.\n"
        f"- 2026-09-08 approved (tester): approved.\n"
    )


class SpecsRecursiveReadTests(unittest.TestCase):
    def test_reproduce_subdir_spec_invisibility(self):
        """E-01 reproduction: a spec in a subdirectory must be seen by specs._spec_files

        and aw specs check. Assert by examined COUNT from specs._spec_files and
        the verb's --json data.checked (never from --agent which omits checked at zero,
        and never from verdict text which passes vacuously at zero files).
        """
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
            (repo / ".aw").mkdir(parents=True)
            (repo / ".aw" / ".gitignore").write_text(
                "records/*/untracked/\n", encoding="utf-8"
            )

            spec_dir = repo / ".aw" / "records" / "specs" / "approved"
            spec_dir.mkdir(parents=True)
            spec_file = spec_dir / "20260908-test01-01-test.spec.md"
            spec_file.write_text(_spec_content("approved", "test01"), encoding="utf-8")

            # Helper assertion by COUNT
            found_files = specs._spec_files(repo)
            self.assertEqual(
                len(found_files),
                1,
                f"specs._spec_files must find the spec in approved/, got {found_files}",
            )
            self.assertEqual(found_files[0].resolve(), spec_file.resolve())

            # CLI --json assertion by COUNT
            ns = argparse.Namespace(
                dir=str(repo), path=None, agent=False, json=True, yaml=False
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = specs.run_check(ns)
            self.assertEqual(rc, 0)
            data = json.loads(buf.getvalue())
            self.assertEqual(
                data["data"]["checked"],
                1,
                f"aw specs check --json must report checked=1, got: {data}",
            )
            self.assertEqual(data["data"]["violations"], 0)

    def test_pinned_disagreement_on_subdir_fixture(self):
        """Pins the surfaces on a subdir fixture: check_engine sees it; specs._spec_files must agree."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)

            spec_dir = repo / ".aw" / "records" / "specs" / "approved"
            spec_dir.mkdir(parents=True)
            spec_file = spec_dir / "20260908-test01-01-test.spec.md"
            spec_file.write_text(_spec_content("approved", "test01"), encoding="utf-8")

            check_engine_files = list(check_engine._iter_type_files(repo, "specs"))
            self.assertEqual(len(check_engine_files), 1)

            spec_files = specs._spec_files(repo)
            self.assertEqual(
                len(spec_files),
                1,
                f"specs._spec_files should agree with check_engine, got {spec_files}",
            )

    def test_gitignored_subdir_spec_excluded(self):
        """E-04: A spec inside a gitignored directory (e.g. records/*/untracked/)

        must NOT be returned by specs._spec_files, while a tracked spec in a subdir IS returned.
        """
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
            (repo / ".aw").mkdir(parents=True)
            (repo / ".aw" / ".gitignore").write_text(
                "records/*/untracked/\n", encoding="utf-8"
            )

            # Tracked subdir spec
            approved_dir = repo / ".aw" / "records" / "specs" / "approved"
            approved_dir.mkdir(parents=True)
            tracked_spec = approved_dir / "20260908-test01-01-tracked.spec.md"
            tracked_spec.write_text(
                _spec_content("approved", "test01"), encoding="utf-8"
            )

            # Untracked (gitignored) subdir spec
            untracked_dir = repo / ".aw" / "records" / "specs" / "untracked"
            untracked_dir.mkdir(parents=True)
            ignored_spec = untracked_dir / "20260908-test02-01-ignored.spec.md"
            ignored_spec.write_text(_spec_content("draft", "test02"), encoding="utf-8")

            found = specs._spec_files(repo)
            found_resolved = [p.resolve() for p in found]

            self.assertIn(
                tracked_spec.resolve(),
                found_resolved,
                "Tracked spec in approved/ must be included",
            )
            self.assertNotIn(
                ignored_spec.resolve(),
                found_resolved,
                "Gitignored spec in untracked/ must be excluded",
            )
            self.assertEqual(len(found), 1)

    def test_skip_names_excluded(self):
        """E-03: README.md, INDEX.md, and STATUS.md are skipped in root and subdirectories."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)

            specs_root = repo / ".aw" / "records" / "specs"
            sub_dir = specs_root / "approved"
            sub_dir.mkdir(parents=True)

            (specs_root / "README.md").write_text("# Specs README", encoding="utf-8")
            (specs_root / "INDEX.md").write_text("# Specs INDEX", encoding="utf-8")
            (specs_root / "STATUS.md").write_text("# Specs STATUS", encoding="utf-8")
            (sub_dir / "README.md").write_text("# Approved README", encoding="utf-8")
            (sub_dir / "INDEX.md").write_text("# Approved INDEX", encoding="utf-8")
            (sub_dir / "STATUS.md").write_text("# Approved STATUS", encoding="utf-8")

            real_spec = sub_dir / "20260908-test01-01-test.spec.md"
            real_spec.write_text(_spec_content("approved", "test01"), encoding="utf-8")

            found = specs._spec_files(repo)
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0].resolve(), real_spec.resolve())

    def test_end_to_end_nonconforming_subdir_spec_reported(self):
        """E-04: aw specs check must report a non-conforming spec in a subdirectory with exit 1."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)

            sub_dir = repo / ".aw" / "records" / "specs" / "approved"
            sub_dir.mkdir(parents=True)
            bad_spec = sub_dir / "20260908-bad001-01-bad.spec.md"
            bad_spec.write_text(
                "# Spec: Bad Spec\n\n"
                "- Date: 2026-09-08\n"
                "- Status: notavalidstatus\n"
                "- Id: bad001\n\n"
                "## Body\n\nText\n",
                encoding="utf-8",
            )

            ns = argparse.Namespace(
                dir=str(repo), path=None, agent=False, json=True, yaml=False
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = specs.run_check(ns)

            self.assertEqual(
                rc, 1, "aw specs check must exit 1 on invalid spec in subdir"
            )
            data = json.loads(buf.getvalue())
            self.assertEqual(data["data"]["checked"], 1)
            self.assertGreater(data["data"]["violations"], 0)
            self.assertEqual(data["status"], "findings")

    def test_dual_roots_dedup_resolved_paths(self):
        """E-03: De-duplication by resolved path prevents duplicate entries when roots overlap."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)

            spec_dir = repo / ".aw" / "records" / "specs"
            spec_dir.mkdir(parents=True)
            spec_file = spec_dir / "20260908-test01-01-test.spec.md"
            spec_file.write_text(_spec_content("approved", "test01"), encoding="utf-8")

            # Create symlink or legacy dir pointing to same location
            legacy_dir = repo / ".agents" / "docs" / "specs"
            legacy_dir.parent.mkdir(parents=True)
            legacy_dir.symlink_to(spec_dir, target_is_directory=True)

            found = specs._spec_files(repo)
            self.assertEqual(
                len(found), 1, f"Expected exactly 1 deduped spec, got {found}"
            )

    def test_live_corpus_set_equality_with_check_engine(self):
        """E-04: specs._spec_files and check_engine._iter_type_files(include_retired=True)

        produce identical sets of resolved paths on the live repository.
        """
        repo_root = Path(__file__).resolve().parent.parent
        spec_files_set = {str(p.resolve()) for p in specs._spec_files(repo_root)}
        check_engine_set = {
            str(p.resolve())
            for p in check_engine._iter_type_files(
                repo_root, "specs", include_retired=True
            )
        }
        default_check_engine_count = len(
            list(check_engine._iter_type_files(repo_root, "specs"))
        )

        self.assertEqual(
            spec_files_set,
            check_engine_set,
            f"Set equality failed: {spec_files_set ^ check_engine_set}",
        )
        self.assertEqual(len(spec_files_set), 37)
        self.assertEqual(default_check_engine_count, 20)


if __name__ == "__main__":
    unittest.main()
