"""Tests for descriptive field length classes: one-line and prose (IPD pl1lbb).

Validates the separation of Section 8.8 output-safety bounds into two distinct classes:
- One-line descriptive bound (MAX_DESCRIPTIVE_LEN = 300)
- Prose descriptive bound (MAX_PROSE_DESCRIPTIVE_LEN = 4300)

Requirements covered:
(a) Two bounds are distinct and MAX_DESCRIPTIVE_LEN is 300.
(b) Hostile shapes (newline, BEL, ANSI, C1) are unsafe under BOTH predicates.
(c) Exact-boundary pairs for both classes (300/301 one-line, 4300/4301 prose).
(d) Spec with 400-char Scope and 250-char Summary validates clean, while 301-char Summary
    and 4301-char Scope each drift as attention.unsafe-field.
(e) aw specs new write-path round trip: --summary of 400 chars succeeds and passes validate_spec;
    --summary of 4301 chars is refused with exit code 2.
(f) Regression: drift detail and refusal messages do not echo untrusted values.
"""

from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import attention_contract as A
from agent_workflows import cli, specs

_SPEC_TEMPLATE = """# Spec: Sample Spec

- Date: 2026-10-07
- Status: draft
- Id: {id6}
- Author: test
{extra_metadata}

## Workflow history
- 2026-10-07 draft (test): created.
"""


class DescriptiveLengthClassesTests(unittest.TestCase):
    """Test suite covering Section 8.8 one-line and prose length classes."""

    def test_bounds_are_distinct_and_constants_defined(self):
        """(a) Bounds are distinct, MAX_DESCRIPTIVE_LEN is 300, and fields set is correct."""
        self.assertEqual(A.MAX_DESCRIPTIVE_LEN, 300)
        self.assertEqual(A.MAX_PROSE_DESCRIPTIVE_LEN, 4300)
        self.assertNotEqual(A.MAX_DESCRIPTIVE_LEN, A.MAX_PROSE_DESCRIPTIVE_LEN)
        self.assertEqual(
            A.PROSE_DESCRIPTIVE_FIELDS, frozenset({"Scope", "Concern", "Question"})
        )

    def test_hostile_shapes_unsafe_under_both_predicates(self):
        """(b) Hostile shapes (newline, BEL, ANSI, C1) are unsafe under BOTH predicates."""
        hostile_shapes = [
            "line1\nline2",
            "line1\rline2",
            "value\x07bel",
            "value\x1b[31mansi\x1b[0m",
            "value\x85c1",
        ]
        for shape in hostile_shapes:
            self.assertFalse(
                A.is_safe_descriptive(shape),
                f"{shape!r} must be unsafe under is_safe_descriptive",
            )
            self.assertFalse(
                A.is_safe_prose_descriptive(shape),
                f"{shape!r} must be unsafe under is_safe_prose_descriptive",
            )

    def test_exact_boundary_pairs(self):
        """(c) Exact-boundary pairs: 300/301 for one-line, 4300/4301 for prose."""
        # One-line boundary
        one_line_300 = "x" * 300
        one_line_301 = "x" * 301
        self.assertTrue(A.is_safe_descriptive(one_line_300))
        self.assertFalse(A.is_safe_descriptive(one_line_301))

        # Under prose predicate, 301 is safe
        self.assertTrue(A.is_safe_prose_descriptive(one_line_301))

        # Prose boundary
        prose_4300 = "x" * 4300
        prose_4301 = "x" * 4301
        self.assertTrue(A.is_safe_prose_descriptive(prose_4300))
        self.assertFalse(A.is_safe_prose_descriptive(prose_4301))

    def test_spec_validation_prose_and_oneline_fields(self):
        """(d) 400-char Scope + 250-char Summary is clean; 301 Summary and 4301 Scope drift."""
        # Clean case: 400-char Scope and 250-char Summary
        clean_text = _SPEC_TEMPLATE.format(
            id6="cln001",
            extra_metadata=f"- Scope: {'s' * 400}\n- Summary: {'m' * 250}",
        )
        drift = specs.validate_spec(Path("tests/clean.spec.md"), clean_text)
        self.assertEqual(drift, [])

        # 301-char Summary drifts
        over_summary_text = _SPEC_TEMPLATE.format(
            id6="ovrsum",
            extra_metadata=f"- Scope: {'s' * 400}\n- Summary: {'m' * 301}",
        )
        drift_sum = specs.validate_spec(
            Path("tests/over_sum.spec.md"), over_summary_text
        )
        self.assertEqual([d.rule for d in drift_sum], ["attention.unsafe-field"])
        self.assertIn("Summary", drift_sum[0].detail)

        # 4301-char Scope drifts
        over_scope_text = _SPEC_TEMPLATE.format(
            id6="ovrscp",
            extra_metadata=f"- Scope: {'s' * 4301}\n- Summary: {'m' * 250}",
        )
        drift_scope = specs.validate_spec(
            Path("tests/over_scope.spec.md"), over_scope_text
        )
        self.assertEqual([d.rule for d in drift_scope], ["attention.unsafe-field"])
        self.assertIn("Scope", drift_scope[0].detail)

    def test_write_path_round_trip_and_agreement(self):
        """(e) run_new accepts 400-char summary, resulting spec passes validate_spec; 4301 refused."""
        tmp = Path(tempfile.mkdtemp(prefix="aw_test_writepath_"))
        self.addCleanup(lambda: shutil.rmtree(tmp, ignore_errors=True))
        subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
        (tmp / ".aw" / "records" / "specs" / "draft").mkdir(parents=True, exist_ok=True)

        # 400-char summary accepted and passes validate_spec
        sum_400 = "s" * 400
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc_400 = cli.main(
                    [
                        "specs",
                        "new",
                        "--title",
                        "Valid Scope",
                        "--slug",
                        "valid-scope",
                        "--summary",
                        sum_400,
                        "--apply",
                        "--dir",
                        str(tmp),
                    ]
                )
            except SystemExit as e:
                rc_400 = int(e.code or 0)
        self.assertEqual(rc_400, 0, f"Expected rc 0: {err.getvalue()}")
        created_files = list(tmp.glob(".aw/records/specs/**/*.spec.md"))
        self.assertTrue(created_files)
        created_spec = created_files[0]
        drift = specs.validate_spec(
            created_spec, created_spec.read_text(encoding="utf-8")
        )
        self.assertEqual(drift, [])

        # 4301-char summary refused at exit 2
        sum_4301 = "s" * 4301
        out2 = io.StringIO()
        err2 = io.StringIO()
        with redirect_stdout(out2), redirect_stderr(err2):
            try:
                rc_4301 = cli.main(
                    [
                        "specs",
                        "new",
                        "--title",
                        "Over Scope",
                        "--slug",
                        "over-scope",
                        "--summary",
                        sum_4301,
                        "--apply",
                        "--dir",
                        str(tmp),
                    ]
                )
            except SystemExit as e:
                rc_4301 = int(e.code or 0)
        self.assertEqual(rc_4301, 2)
        err_msg = err2.getvalue()
        self.assertIn("4300", err_msg)
        self.assertIn("4301", err_msg)

    def test_no_echo_untrusted_value_regression(self):
        """(f) Drift detail and CLI refusal message do not echo untrusted values."""
        hostile_scope = "SECRET_TOKEN_" + "x" * 4300
        text = _SPEC_TEMPLATE.format(
            id6="noecho",
            extra_metadata=f"- Scope: {hostile_scope}",
        )
        drift = specs.validate_spec(Path("tests/no_echo.spec.md"), text)
        self.assertEqual(len(drift), 1)
        self.assertNotIn("SECRET_TOKEN_", drift[0].detail)

        # Refusal message check
        err = specs._refuse_unsafe_descriptive(
            "aw specs new", "--summary", hostile_scope, prose=True
        )
        self.assertIsNotNone(err)
        self.assertNotIn("SECRET_TOKEN_", err)
        self.assertIn("4300", err)


if __name__ == "__main__":
    unittest.main()
