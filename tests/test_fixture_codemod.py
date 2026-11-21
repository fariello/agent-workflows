"""Behavioral tests for ``tools/fixture_codemod.py`` (IPDs ``j2xjtt`` and ``n0li9v``).

Drives ``tools/fixture_codemod.py`` as a subprocess on copies of fixture modules
inside temporary git repositories initialized with ``tests/support.py``
``init_repo``, asserting on exit codes, stdout/stderr, JSON reports, and
rewritten or untouched file contents.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

import pytest

from tests import support

pytestmark = pytest.mark.core

CODEMOD_PATH = Path(__file__).resolve().parent.parent / "tools" / "fixture_codemod.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "fixture_codemod"


def _stage_fixture_in_temp_repo(
    base: Path, fixture_name: str, dest_name: str
) -> tuple[Path, Path]:
    """Initialize a temporary git repository and copy one fixture into ``tests/``."""
    repo = support.init_repo(base / "repo")
    tests_dir = repo / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    target = tests_dir / dest_name
    target.write_bytes((FIXTURES_DIR / fixture_name).read_bytes())
    return repo, target


def _run_codemod(
    repo: Path, *args: str
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any] | None]:
    """Run ``tools/fixture_codemod.py`` via ``sys.executable`` inside ``repo``."""
    proc = subprocess.run(
        [sys.executable, str(CODEMOD_PATH), *args],
        cwd=str(repo),
        env=support.pinned_env(),
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    parsed: dict[str, Any] | None = None
    if "--format" in args:
        idx = args.index("--format")
        if (
            idx + 1 < len(args)
            and args[idx + 1] == "json"
            and proc.returncode == 0
            and proc.stdout.strip()
        ):
            parsed = json.loads(proc.stdout)
    return proc, parsed


class FixtureCodemodRewriteTests(unittest.TestCase):
    """E-04: rewrite cases (a) plain constant, (b) f-string, (c) invalid-input."""

    def test_case_a_plain_constant_rewritten_to_builder_call(self) -> None:
        """Case (a): a plain constant metadata block becomes a RecordBuilder call."""
        with tempfile.TemporaryDirectory() as td:
            repo, target = _stage_fixture_in_temp_repo(
                Path(td), "plain_constant.py.txt", "test_plain_constant.py"
            )
            rel_target = target.relative_to(repo).as_posix()

            proc, report = _run_codemod(repo, "--apply", "--format", "json", rel_target)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stderr, "")
            self.assertIsNotNone(report)
            assert report is not None
            self.assertEqual(report["mode"], "apply")
            self.assertEqual(report["totals"]["sites"], 1)
            self.assertEqual(report["totals"]["rewrites"], 1)
            self.assertEqual(report["totals"]["standard_rewrites"], 1)
            self.assertEqual(report["totals"]["invalid_input_rewrites"], 0)
            self.assertEqual(report["totals"]["refusals"], 0)

            mod = report["modules"][0]
            self.assertTrue(mod["applied"])
            self.assertTrue(mod["changed"])
            self.assertTrue(mod["proof"]["equivalent"])
            self.assertEqual(mod["proof"]["before_hash"], mod["proof"]["after_hash"])
            site = mod["sites"][0]
            self.assertEqual(site["action"], "rewrite")
            self.assertEqual(site["rewrite_class"], "standard")
            self.assertEqual(site["record_type"], "ipd")
            self.assertEqual(site["method"], "plan")

            rewritten = target.read_text(encoding="utf-8")
            self.assertIn("from tests.record_builder import RecordBuilder\n", rewritten)
            self.assertIn("RecordBuilder().plan(", rewritten)
            self.assertIn("title='Plain Constant Plan'", rewritten)
            self.assertIn("id6='pl1001'", rewritten)
            self.assertIn("status='approved'", rewritten)
            self.assertIn("set='demo'", rewritten)
            self.assertIn("order=1", rewritten)
            self.assertIn("text_only=True)", rewritten)
            self.assertNotIn("- Id: pl1001", rewritten)
            self.assertNotIn("- Status: approved", rewritten)
            self.assertIn(
                "# Preserved comment line for byte-preservation checks.", rewritten
            )
            self.assertIn('UNTOUCHED_MARKER = "keep-me-intact"', rewritten)

    def test_case_b_fstring_placeholders_become_keyword_arguments(self) -> None:
        """Case (b): an f-string with field placeholders becomes keyword arguments."""
        with tempfile.TemporaryDirectory() as td:
            repo, target = _stage_fixture_in_temp_repo(
                Path(td), "fstring_placeholders.py.txt", "test_fstring_placeholders.py"
            )
            rel_target = target.relative_to(repo).as_posix()

            proc, report = _run_codemod(repo, "--apply", "--format", "json", rel_target)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stderr, "")
            self.assertIsNotNone(report)
            assert report is not None
            self.assertEqual(report["totals"]["sites"], 1)
            self.assertEqual(report["totals"]["rewrites"], 1)
            self.assertEqual(report["totals"]["standard_rewrites"], 1)
            self.assertEqual(report["totals"]["refusals"], 0)

            mod = report["modules"][0]
            self.assertTrue(mod["changed"])
            self.assertTrue(mod["proof"]["equivalent"])
            site = mod["sites"][0]
            self.assertEqual(site["action"], "rewrite")
            self.assertEqual(site["rewrite_class"], "standard")
            self.assertEqual(site["record_type"], "spec")
            self.assertEqual(site["method"], "spec")
            self.assertEqual(site["kwargs"]["id6"], "spec_id")
            self.assertEqual(site["kwargs"]["status"], "status")
            self.assertEqual(site["kwargs"]["title"], 'f"Demo {spec_id}"')

            rewritten = target.read_text(encoding="utf-8")
            self.assertIn("from tests.record_builder import RecordBuilder\n", rewritten)
            self.assertIn(
                'RecordBuilder().spec(title=f"Demo {spec_id}", id6=spec_id, status=status, text_only=True)',
                rewritten,
            )
            self.assertNotIn("- Id: {spec_id}", rewritten)
            self.assertNotIn("- Status: {status}", rewritten)

    def test_case_c_invalid_value_uses_raw_fields_and_invalid_input_class(self) -> None:
        """Case (c): an invalid value routes through raw_fields= and is listed invalid-input."""
        with tempfile.TemporaryDirectory() as td:
            repo, target = _stage_fixture_in_temp_repo(
                Path(td), "invalid_input.py.txt", "test_invalid_input.py"
            )
            rel_target = target.relative_to(repo).as_posix()

            proc, report = _run_codemod(repo, "--apply", "--format", "json", rel_target)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stderr, "")
            self.assertIsNotNone(report)
            assert report is not None
            self.assertEqual(report["totals"]["sites"], 1)
            self.assertEqual(report["totals"]["rewrites"], 1)
            self.assertEqual(report["totals"]["standard_rewrites"], 0)
            self.assertEqual(report["totals"]["invalid_input_rewrites"], 1)
            self.assertEqual(report["totals"]["refusals"], 0)

            mod = report["modules"][0]
            self.assertTrue(mod["changed"])
            self.assertTrue(mod["proof"]["equivalent"])
            site = mod["sites"][0]
            self.assertEqual(site["action"], "rewrite")
            self.assertEqual(site["rewrite_class"], "invalid-input")
            self.assertEqual(site["record_type"], "spec")
            self.assertEqual(site["raw_fields"], {"Status": "'EXECUTED'"})

            rewritten = target.read_text(encoding="utf-8")
            self.assertIn("from tests.record_builder import RecordBuilder\n", rewritten)
            self.assertIn("RecordBuilder().spec(", rewritten)
            self.assertIn("raw_fields={'Status': 'EXECUTED'}", rewritten)
            self.assertIn("text_only=True)", rewritten)
            self.assertNotIn("- Status: EXECUTED", rewritten)


class FixtureCodemodDryRunAndIdempotenceTests(unittest.TestCase):
    """E-08: cases (e) --dry-run writes nothing, (f) second --apply changes nothing."""

    def test_case_e_dry_run_writes_nothing(self) -> None:
        """Case (e): --dry-run plans the rewrite and leaves the repository untouched."""
        with tempfile.TemporaryDirectory() as td:
            repo, target = _stage_fixture_in_temp_repo(
                Path(td), "dry_run_and_idempotence.py.txt", "test_dry_run_fixture.py"
            )
            rel_target = target.relative_to(repo).as_posix()
            before_bytes = target.read_bytes()

            proc_json, report = _run_codemod(
                repo, "--dry-run", "--format", "json", rel_target
            )
            self.assertEqual(proc_json.returncode, 0, proc_json.stderr)
            self.assertEqual(proc_json.stderr, "")
            self.assertIsNotNone(report)
            assert report is not None
            self.assertEqual(report["mode"], "dry-run")
            self.assertEqual(report["totals"]["sites"], 1)
            self.assertEqual(report["totals"]["rewrites"], 1)
            self.assertFalse(report["modules"][0]["applied"])
            self.assertFalse(report["modules"][0]["changed"])
            self.assertEqual(target.read_bytes(), before_bytes)

            proc_table, _ = _run_codemod(
                repo, "--dry-run", "--format", "table", rel_target
            )
            self.assertEqual(proc_table.returncode, 0, proc_table.stderr)
            self.assertEqual(proc_table.stderr, "")
            self.assertIn("rewrite", proc_table.stdout)
            self.assertIn("release (standard)", proc_table.stdout)
            self.assertEqual(target.read_bytes(), before_bytes)

    def test_case_f_second_apply_is_idempotent_and_changes_nothing(self) -> None:
        """Case (f): a second --apply run reports zero rewrites and changes zero bytes."""
        with tempfile.TemporaryDirectory() as td:
            repo, target = _stage_fixture_in_temp_repo(
                Path(td),
                "dry_run_and_idempotence.py.txt",
                "test_idempotence_fixture.py",
            )
            rel_target = target.relative_to(repo).as_posix()

            first_proc, first_report = _run_codemod(
                repo, "--apply", "--format", "json", rel_target
            )
            self.assertEqual(first_proc.returncode, 0, first_proc.stderr)
            self.assertEqual(first_proc.stderr, "")
            assert first_report is not None
            self.assertEqual(first_report["totals"]["rewrites"], 1)
            self.assertTrue(first_report["modules"][0]["changed"])
            after_first_bytes = target.read_bytes()

            second_proc, second_report = _run_codemod(
                repo, "--apply", "--format", "json", rel_target
            )
            self.assertEqual(second_proc.returncode, 0, second_proc.stderr)
            self.assertEqual(second_proc.stderr, "")
            assert second_report is not None
            self.assertEqual(second_report["totals"]["sites"], 0)
            self.assertEqual(second_report["totals"]["rewrites"], 0)
            self.assertFalse(second_report["modules"][0]["changed"])
            self.assertEqual(second_report["modules"][0]["proof"]["pytest_runs"], 0)
            self.assertTrue(second_report["modules"][0]["proof"]["equivalent"])
            self.assertEqual(target.read_bytes(), after_first_bytes)


class FixtureCodemodRefusalTests(unittest.TestCase):
    """E-11 and E-12: one fixture and test per static refusal reason code."""

    def _assert_static_refusal(
        self,
        fixture_name: str,
        dest_name: str,
        expected_reason: str,
        expected_disposition: str,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo, target = _stage_fixture_in_temp_repo(
                Path(td), fixture_name, dest_name
            )
            rel_target = target.relative_to(repo).as_posix()
            before_bytes = target.read_bytes()

            dry_proc, dry_report = _run_codemod(
                repo, "--dry-run", "--format", "json", rel_target
            )
            self.assertEqual(dry_proc.returncode, 0, dry_proc.stderr)
            self.assertEqual(dry_proc.stderr, "")
            self.assertIsNotNone(dry_report)
            assert dry_report is not None
            self.assertEqual(dry_report["mode"], "dry-run")
            self.assertEqual(dry_report["totals"]["sites"], 1)
            self.assertEqual(dry_report["totals"]["rewrites"], 0)
            self.assertEqual(dry_report["totals"]["refusals"], 1)
            self.assertEqual(dry_report["totals"]["by_reason"][expected_reason], 1)
            self.assertEqual(
                dry_report["totals"]["by_disposition"][expected_disposition], 1
            )
            dry_mod = dry_report["modules"][0]
            self.assertFalse(dry_mod["applied"])
            self.assertFalse(dry_mod["changed"])
            self.assertEqual(len(dry_mod["sites"]), 1)
            dry_site = dry_mod["sites"][0]
            self.assertEqual(dry_site["action"], "refuse")
            self.assertEqual(dry_site["reason"], expected_reason)
            self.assertEqual(dry_site["disposition"], expected_disposition)
            self.assertEqual(target.read_bytes(), before_bytes)

            apply_proc, apply_report = _run_codemod(
                repo, "--apply", "--format", "json", rel_target
            )
            self.assertEqual(apply_proc.returncode, 0, apply_proc.stderr)
            self.assertEqual(apply_proc.stderr, "")
            self.assertIsNotNone(apply_report)
            assert apply_report is not None
            self.assertEqual(apply_report["mode"], "apply")
            self.assertEqual(apply_report["totals"]["sites"], 1)
            self.assertEqual(apply_report["totals"]["rewrites"], 0)
            self.assertEqual(apply_report["totals"]["refusals"], 1)
            apply_mod = apply_report["modules"][0]
            self.assertTrue(apply_mod["applied"])
            self.assertFalse(apply_mod["changed"])
            self.assertEqual(len(apply_mod["sites"]), 1)
            apply_site = apply_mod["sites"][0]
            self.assertEqual(apply_site["action"], "refuse")
            self.assertEqual(apply_site["reason"], expected_reason)
            self.assertEqual(apply_site["disposition"], expected_disposition)
            self.assertEqual(target.read_bytes(), before_bytes)

    def test_refuse_dynamic_construction(self) -> None:
        """E-11: dynamic-construction (hand) leaves the module byte-identical."""
        self._assert_static_refusal(
            "refuse_dynamic_construction.py.txt",
            "test_refuse_dynamic_construction.py",
            "dynamic-construction",
            "hand",
        )

    def test_refuse_unsupported_shape(self) -> None:
        """E-11: unsupported-shape (hand) leaves the module byte-identical."""
        self._assert_static_refusal(
            "refuse_unsupported_shape.py.txt",
            "test_refuse_unsupported_shape.py",
            "unsupported-shape",
            "hand",
        )

    def test_refuse_legacy_format_subject(self) -> None:
        """E-11: legacy-format subject (legacy-kept) leaves the module byte-identical."""
        self._assert_static_refusal(
            "refuse_legacy_format_subject.py.txt",
            "test_legacy_subject_fixture.py",
            "legacy-format subject",
            "legacy-kept",
        )

    def test_refuse_displayed_output_assertion(self) -> None:
        """E-12: displayed-output assertion (legacy-kept) leaves the module byte-identical."""
        self._assert_static_refusal(
            "refuse_displayed_output_assertion.py.txt",
            "test_refuse_displayed_output_assertion.py",
            "displayed-output assertion",
            "legacy-kept",
        )

    def test_refuse_setter_byte_assertion(self) -> None:
        """E-12: setter-byte assertion (legacy-kept) leaves the module byte-identical."""
        self._assert_static_refusal(
            "refuse_setter_byte_assertion.py.txt",
            "test_refuse_setter_byte_assertion.py",
            "setter-byte assertion",
            "legacy-kept",
        )

    def test_refuse_body_prose(self) -> None:
        """E-12: body prose (legacy-kept) leaves the module byte-identical."""
        self._assert_static_refusal(
            "refuse_body_prose.py.txt",
            "test_refuse_body_prose.py",
            "body prose",
            "legacy-kept",
        )


if __name__ == "__main__":
    unittest.main()
