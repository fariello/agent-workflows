"""Behavioral tests for Section 8.8 bidi control rejection and output-safety.

Discharges acceptance criterion A14:
"a `Gate-Summary` containing a newline, an ANSI/control character ... each fails as
a stable named violation"
by ensuring that the Section 8.8 control-character predicate rejects all nine Unicode
bidirectional overrides and isolates (U+202A..U+202E, U+2066..U+2069) across all consumer
surfaces, while preserving pass-through for legitimate formatting characters
(U+200B..U+200D, U+00AD, U+FEFF) and normal ASCII text.
"""

from __future__ import annotations

import argparse
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import attention_contract as A
from agent_workflows import backlog as B
from agent_workflows import releases
from agent_workflows import specs


def _args(**kw):
    ns = argparse.Namespace()
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


def _call_backlog_new(repo: Path, **kw):
    base = dict(
        dir=str(repo),
        summary="a conforming summary",
        set="s",
        priority="high",
        kind="bug",
        slug="item",
        apply=True,
    )
    base.update(kw)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = B.run_new(_args(**base))
    return rc, out.getvalue(), err.getvalue()


class BidiControlPredicateIndividualTests(unittest.TestCase):
    """Assert each of the nine bidi overrides/isolates is individually rejected by the predicate."""

    def test_reject_u202a_lre(self):
        val = "prefix\u202asuffix"
        self.assertIsNotNone(A._CONTROL_CHAR_RE.search(val))
        self.assertFalse(A.is_safe_descriptive(val))

    def test_reject_u202b_rle(self):
        val = "prefix\u202bsuffix"
        self.assertIsNotNone(A._CONTROL_CHAR_RE.search(val))
        self.assertFalse(A.is_safe_descriptive(val))

    def test_reject_u202c_pdf(self):
        val = "prefix\u202csuffix"
        self.assertIsNotNone(A._CONTROL_CHAR_RE.search(val))
        self.assertFalse(A.is_safe_descriptive(val))

    def test_reject_u202d_lro(self):
        val = "prefix\u202dsuffix"
        self.assertIsNotNone(A._CONTROL_CHAR_RE.search(val))
        self.assertFalse(A.is_safe_descriptive(val))

    def test_reject_u202e_rlo(self):
        val = "prefix\u202esuffix"
        self.assertIsNotNone(A._CONTROL_CHAR_RE.search(val))
        self.assertFalse(A.is_safe_descriptive(val))

    def test_reject_u2066_lri(self):
        val = "prefix\u2066suffix"
        self.assertIsNotNone(A._CONTROL_CHAR_RE.search(val))
        self.assertFalse(A.is_safe_descriptive(val))

    def test_reject_u2067_rli(self):
        val = "prefix\u2067suffix"
        self.assertIsNotNone(A._CONTROL_CHAR_RE.search(val))
        self.assertFalse(A.is_safe_descriptive(val))

    def test_reject_u2068_fsi(self):
        val = "prefix\u2068suffix"
        self.assertIsNotNone(A._CONTROL_CHAR_RE.search(val))
        self.assertFalse(A.is_safe_descriptive(val))

    def test_reject_u2069_pdi(self):
        val = "prefix\u2069suffix"
        self.assertIsNotNone(A._CONTROL_CHAR_RE.search(val))
        self.assertFalse(A.is_safe_descriptive(val))


class LegitimateFormattingPassThroughTests(unittest.TestCase):
    """Assert legitimate zero-width and formatting characters remain accepted."""

    def test_accept_u200b_zwsp(self):
        val = "zero\u200bwidth"
        self.assertIsNone(A._CONTROL_CHAR_RE.search(val))
        self.assertTrue(A.is_safe_descriptive(val))

    def test_accept_u200c_zwnj(self):
        val = "non\u200cjoiner"
        self.assertIsNone(A._CONTROL_CHAR_RE.search(val))
        self.assertTrue(A.is_safe_descriptive(val))

    def test_accept_u200d_zwj(self):
        val = "joiner\u200dchar"
        self.assertIsNone(A._CONTROL_CHAR_RE.search(val))
        self.assertTrue(A.is_safe_descriptive(val))

    def test_accept_u00ad_soft_hyphen(self):
        val = "di\u00adrectory"
        self.assertIsNone(A._CONTROL_CHAR_RE.search(val))
        self.assertTrue(A.is_safe_descriptive(val))

    def test_accept_ufeff_bom(self):
        val = "byte\ufefforder"
        self.assertIsNone(A._CONTROL_CHAR_RE.search(val))
        self.assertTrue(A.is_safe_descriptive(val))

    def test_accept_plain_ascii(self):
        val = "a normal single line of descriptive text"
        self.assertIsNone(A._CONTROL_CHAR_RE.search(val))
        self.assertTrue(A.is_safe_descriptive(val))


class BidiConsumerSurfacesTests(unittest.TestCase):
    """Assert rejection reaches every consumer verb and helper."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / ".aw" / "records" / "backlog" / "open").mkdir(
            parents=True, exist_ok=True
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_consumer_backlog_run_new_rejects_bidi_summary(self):
        """backlog.run_new with a bidi --summary exits 2 and writes NO file."""
        bidi_summary = "fix auth \u202ereversed\u202c now"
        rc, out, err = _call_backlog_new(self.repo, summary=bidi_summary, slug="trojan")
        self.assertEqual(rc, 2)
        backlog_files = list(self.repo.glob("**/*.md"))
        self.assertEqual(
            len(backlog_files),
            0,
            f"Expected no file written, found: {backlog_files}",
        )
        self.assertIn("--summary", err)
        self.assertIn("control", err.lower())

    def test_consumer_specs_refuse_unsafe_descriptive_rejects_bidi(self):
        """specs._refuse_unsafe_descriptive returns a refusal naming control-character cause."""
        bidi_title = "harden auth \u202ereversed\u202c checks"
        refusal = specs._refuse_unsafe_descriptive(
            "aw specs new", "--title", bidi_title
        )
        self.assertIsNotNone(refusal)
        self.assertIn("--title", refusal)
        self.assertIn("control", refusal.lower())

    def test_consumer_validate_gate_ref_rejects_bidi(self):
        """attention_contract.validate_gate_ref returns False for bidi-bearing ref."""
        bidi_ref = "ticket-\u202ereversed\u202c"
        self.assertFalse(A.validate_gate_ref("external", bidi_ref))

    def test_consumer_releases_validate_release_prose_rejects_bidi(self):
        """releases.validate_release returns attention.unsafe-field for bidi control in summary prose."""
        release_text = (
            "# Release 1.0.0\n\n"
            "- Id: rel001\n"
            "- Version: 1.0.0\n"
            "- Status: planned\n\n"
            "## Summary\n\n"
            "This summary prose contains \u202e reversed \u202c bidi characters.\n"
        )
        drifts = releases.validate_release(Path("test.release.md"), release_text)
        rules = [d.rule for d in drifts]
        self.assertIn(
            "attention.unsafe-field",
            rules,
            f"Expected attention.unsafe-field in drifts, got: {drifts}",
        )
        unsafe_drifts = [d for d in drifts if d.rule == "attention.unsafe-field"]
        self.assertTrue(any("control" in d.detail.lower() for d in unsafe_drifts))


if __name__ == "__main__":
    unittest.main()
