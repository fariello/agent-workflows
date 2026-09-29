"""Tests for Section 8.8 output-safety enforcement at backlog creation/modification verbs.

Pins:
1. CREATE/CHECK CONTRADICTION (E-04): unsafe shapes rejected by attention_contract.is_safe_descriptive
   (over-length, newline, carriage return, control chars) must be refused at run_new with exit 2,
   writing no file, while conforming summaries succeed and check clean with zero drift.
2. INJECTION CLOSURE (E-05): newlines in --summary, --gate-ref, or --message on run_new, run_set,
   and run_note must be refused with exit 2 without modifying or creating files.
3. LENGTH ASYMMETRY (E-05): 1200-char single-line --message is accepted across all verbs, while
   301-char --summary is refused.
4. NON-REGRESSIONS (E-05): empty-summary refusal unchanged, exact boundary MAX_DESCRIPTIVE_LEN
   conforms, and --agent refusal shape.
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


def _args(**kw):
    ns = argparse.Namespace()
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


def _call_new(repo: Path, **kw):
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


def _call_set(repo: Path, path: Path, **kw):
    base = dict(
        dir=str(repo),
        path=str(path),
        status="open",
        apply=True,
    )
    base.update(kw)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = B.run_set(_args(**base))
    return rc, out.getvalue(), err.getvalue()


def _call_note(repo: Path, path: Path, message: str, **kw):
    base = dict(
        dir=str(repo),
        path=str(path),
        message=message,
        apply=True,
    )
    base.update(kw)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = B.run_note(_args(**base))
    return rc, out.getvalue(), err.getvalue()


class BacklogDescriptiveSafetyTests(unittest.TestCase):
    """Test suite for backlog descriptive safety and refusal helpers (IPD dtg7dz)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / ".aw" / "records" / "backlog" / "open").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo / ".aw" / "records" / "backlog" / "blocked").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo / ".aw" / "records" / "backlog" / "done").mkdir(
            parents=True, exist_ok=True
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _all_backlog_files(self) -> list[Path]:
        return list(self.repo.glob("**/*.md"))

    # ----------------------------------------------------------------------------------
    # E-01: Helper function verification
    # ----------------------------------------------------------------------------------

    def test_helper_refuse_unsafe_descriptive_contract(self):
        """E-01: backlog._refuse_unsafe_descriptive matches required helper shape and results."""
        self.assertTrue(
            hasattr(B, "_refuse_unsafe_descriptive"),
            "Helper _refuse_unsafe_descriptive missing",
        )
        fn = getattr(B, "_refuse_unsafe_descriptive")

        # bound_length=True (default)
        self.assertIsNone(fn("aw backlog new", "--summary", None))
        self.assertIsNone(fn("aw backlog new", "--summary", "ok"))

        msg_nl = fn("aw backlog new", "--summary", "a\nb")
        self.assertIsNotNone(msg_nl)
        self.assertIn("newline", msg_nl.lower())
        self.assertIn("--summary", msg_nl)

        msg_ctrl = fn("aw backlog new", "--summary", "a\x07b")
        self.assertIsNotNone(msg_ctrl)
        self.assertIn("control", msg_ctrl.lower())
        self.assertIn("--summary", msg_ctrl)

        msg_len = fn("aw backlog new", "--summary", "x" * 340)
        self.assertIsNotNone(msg_len)
        self.assertIn("300", msg_len)
        self.assertIn("340", msg_len)
        self.assertIn("--summary", msg_len)

        # bound_length=False (line-integrity mode)
        self.assertIsNone(
            fn("aw backlog note", "--message", "x" * 340, bound_length=False)
        )
        self.assertIsNone(
            fn("aw backlog note", "--message", "x" * 1200, bound_length=False)
        )

        msg_nl_unbound = fn("aw backlog note", "--message", "a\nb", bound_length=False)
        self.assertIsNotNone(msg_nl_unbound)
        self.assertIn("newline", msg_nl_unbound.lower())
        self.assertIn("--message", msg_nl_unbound)

        msg_ctrl_unbound = fn(
            "aw backlog note", "--message", "a\x07b", bound_length=False
        )
        self.assertIsNotNone(msg_ctrl_unbound)
        self.assertIn("control", msg_ctrl_unbound.lower())
        self.assertIn("--message", msg_ctrl_unbound)

    # ----------------------------------------------------------------------------------
    # E-04: Contradiction & unsafe shapes on run_new
    # ----------------------------------------------------------------------------------

    def test_unsafe_shape_over_length_refused(self):
        """E-04: 340-char summary refused with exit 2, writing no file."""
        overlong = "s" * 340
        rc, out, err = _call_new(self.repo, summary=overlong, slug="overlong")
        self.assertEqual(rc, 2)
        self.assertEqual(len(self._all_backlog_files()), 0)
        self.assertIn("--summary", err)
        self.assertIn("300", err)
        self.assertIn("340", err)

    def test_unsafe_shape_newline_refused(self):
        """E-04: embedded newline refused with exit 2, writing no file."""
        nl_summary = "hello\nworld"
        rc, out, err = _call_new(self.repo, summary=nl_summary, slug="nl")
        self.assertEqual(rc, 2)
        self.assertEqual(len(self._all_backlog_files()), 0)
        self.assertIn("--summary", err)
        self.assertIn("newline", err.lower())

    def test_unsafe_shape_carriage_return_refused(self):
        """E-04: embedded carriage return refused with exit 2, writing no file."""
        cr_summary = "hello\rworld"
        rc, out, err = _call_new(self.repo, summary=cr_summary, slug="cr")
        self.assertEqual(rc, 2)
        self.assertEqual(len(self._all_backlog_files()), 0)
        self.assertIn("--summary", err)
        self.assertIn("newline", err.lower())

    def test_unsafe_shape_control_chars_refused(self):
        """E-04: C0 control chars (BEL, ESC) refused with exit 2, writing no file."""
        for name, ctrl in [("bel", "foo\x07bar"), ("esc", "foo\x1bbar")]:
            with self.subTest(control=name):
                rc, out, err = _call_new(self.repo, summary=ctrl, slug=name)
                self.assertEqual(rc, 2)
                self.assertEqual(len(self._all_backlog_files()), 0)
                self.assertIn("--summary", err)
                self.assertIn("control", err.lower())

    def test_paired_conforming_summary_succeeds_and_checks_clean(self):
        """E-04: paired converse: conforming summary succeeds and validate_item reports clean."""
        rc, out, err = _call_new(
            self.repo, summary="A completely conforming summary", slug="clean"
        )
        self.assertEqual(rc, 0)
        files = self._all_backlog_files()
        self.assertEqual(len(files), 1)
        target = files[0]
        drift = B.validate_item(target, target.read_text(encoding="utf-8"))
        self.assertEqual(drift, [])

    def test_paired_no_creation_contradiction_possible(self):
        """E-04: PAIRED property: no input where creation returns 0 yields backlog.summary-unsafe."""
        samples = [
            "valid one",
            "x" * 340,
            "line1\nline2",
            "line1\rline2",
            "bell\x07char",
        ]
        for s in samples:
            rc, _, _ = _call_new(self.repo, summary=s, slug="sample")
            if rc == 0:
                files = self._all_backlog_files()
                target = files[-1]
                rules = [
                    rule
                    for rule, _ in B.validate_item(
                        target, target.read_text(encoding="utf-8")
                    )
                ]
                self.assertNotIn("backlog.summary-unsafe", rules)
            else:
                self.assertEqual(rc, 2)

    # ----------------------------------------------------------------------------------
    # E-05: Injection vectors across verbs
    # ----------------------------------------------------------------------------------

    def test_injection_summary_refused_on_run_new(self):
        """E-05: smuggled - Blocks-Release bullet in --summary is refused at run_new."""
        injected = "legit\n- Blocks-Release: next"
        rc, out, err = _call_new(self.repo, summary=injected, slug="smuggle")
        self.assertEqual(rc, 2)
        self.assertEqual(len(self._all_backlog_files()), 0)
        self.assertIn("--summary", err)
        self.assertIn("newline", err.lower())

    def test_injection_gate_ref_refused_on_run_new(self):
        """E-05: smuggled bullet in --gate-ref is refused at run_new."""
        injected = "TODO.md\n- Blocks-Release: next"
        rc, out, err = _call_new(
            self.repo,
            summary="valid summary",
            status="blocked",
            gate_kind="todo",
            gate_ref=injected,
            slug="smuggle-gate",
        )
        self.assertEqual(rc, 2)
        self.assertEqual(len(self._all_backlog_files()), 0)
        self.assertIn("--gate-ref", err)
        self.assertIn("newline", err.lower())

    def test_injection_message_refused_on_run_new(self):
        """E-05: smuggled bullet in --message is refused at run_new."""
        injected = "note\n- Blocks-Release: next"
        rc, out, err = _call_new(
            self.repo,
            summary="valid summary",
            message=injected,
            slug="smuggle-msg",
        )
        self.assertEqual(rc, 2)
        self.assertEqual(len(self._all_backlog_files()), 0)
        self.assertIn("--message", err)
        self.assertIn("newline", err.lower())

    def test_injection_gate_ref_refused_on_run_set(self):
        """E-05: smuggled bullet in --gate-ref is refused at run_set, leaving file untouched."""
        rc0, _, _ = _call_new(self.repo, summary="base item", slug="base")
        self.assertEqual(rc0, 0)
        item_path = next(self.repo.glob("**/*.md"))
        before_bytes = item_path.read_bytes()

        injected = "TODO.md\n- Blocks-Release: next"
        rc, out, err = _call_set(
            self.repo,
            item_path,
            status="blocked",
            gate_kind="todo",
            gate_ref=injected,
        )
        self.assertEqual(rc, 2)
        self.assertEqual(item_path.read_bytes(), before_bytes)
        self.assertIn("--gate-ref", err)
        self.assertIn("newline", err.lower())

    def test_injection_message_refused_on_run_set(self):
        """E-05: smuggled bullet in --message is refused at run_set, leaving file untouched."""
        rc0, _, _ = _call_new(self.repo, summary="base item", slug="base")
        self.assertEqual(rc0, 0)
        item_path = next(self.repo.glob("**/*.md"))
        before_bytes = item_path.read_bytes()

        injected = "note\n- Blocks-Release: next"
        rc, out, err = _call_set(
            self.repo,
            item_path,
            status="done",
            message=injected,
        )
        self.assertEqual(rc, 2)
        self.assertEqual(item_path.read_bytes(), before_bytes)
        self.assertIn("--message", err)
        self.assertIn("newline", err.lower())

    def test_injection_message_refused_on_run_note(self):
        """E-05: smuggled bullet in --message is refused at run_note, leaving file untouched."""
        rc0, _, _ = _call_new(self.repo, summary="base item", slug="base")
        self.assertEqual(rc0, 0)
        item_path = next(self.repo.glob("**/*.md"))
        before_bytes = item_path.read_bytes()

        injected = "note\n- Blocks-Release: next"
        rc, out, err = _call_note(
            self.repo,
            item_path,
            message=injected,
        )
        self.assertEqual(rc, 2)
        self.assertEqual(item_path.read_bytes(), before_bytes)
        self.assertIn("--message", err)
        self.assertIn("newline", err.lower())

    def test_pre_fix_injection_demonstration_checker_blindness(self):
        """E-05 / F-03 / F-04: proof that checker cannot detect newline front-matter injection."""
        injected_raw = (
            "- Date: 2026-09-28\n"
            "- Set: s\n"
            "- Id: inj001\n"
            "- Status: open\n"
            "- Priority: high\n"
            "- Kind: bug\n"
            "- Summary: legit\n"
            "- Blocks-Release: next\n\n"
            "## Workflow history\n"
            "- 2026-09-28 created (aw backlog): legit\n"
        )
        parsed = B.parse_item(injected_raw)
        self.assertEqual(parsed.summary, "legit")
        self.assertEqual(parsed.blocks_release, "next")
        # Validate that checker reports zero drift because value was split
        fake_path = self.repo / "20260928-s-01-inj001-legit.backlog.md"
        self.assertEqual(B.validate_item(fake_path, injected_raw), [])

    # ----------------------------------------------------------------------------------
    # E-05: Length asymmetry, non-regressions, legitimate inputs
    # ----------------------------------------------------------------------------------

    def test_message_summary_length_asymmetry(self):
        """E-05: 1200-char message accepted across verbs while 301-char summary is refused."""
        long_msg = "m" * 1200
        # Accepted on run_new
        rc_new, _, _ = _call_new(
            self.repo, summary="valid summary", message=long_msg, slug="asym-new"
        )
        self.assertEqual(rc_new, 0)
        item_path = next(self.repo.glob("**/*.md"))

        # Accepted on run_set (moves item to done)
        rc_set, _, _ = _call_set(self.repo, item_path, status="done", message=long_msg)
        self.assertEqual(rc_set, 0)
        item_path = next(self.repo.glob("**/*.md"))

        # Accepted on run_note
        rc_note, _, _ = _call_note(self.repo, item_path, message=long_msg)
        self.assertEqual(rc_note, 0)

        # But 301-char summary is refused
        long_summary = "s" * 301
        rc_s, _, err_s = _call_new(self.repo, summary=long_summary, slug="asym-summary")
        self.assertEqual(rc_s, 2)
        self.assertIn("300", err_s)
        self.assertIn("301", err_s)

    def test_empty_summary_refusal_unchanged(self):
        """E-05 non-regression: empty --summary refusal preserved with unchanged message."""
        rc, out, err = _call_new(self.repo, summary="", slug="empty")
        self.assertEqual(rc, 2)
        self.assertEqual(err, "aw backlog new: --summary is required\n")

    def test_summary_length_boundary(self):
        """E-05 non-regression: exactly MAX_DESCRIPTIVE_LEN accepted, +1 refused."""
        exact_300 = "b" * A.MAX_DESCRIPTIVE_LEN
        rc_300, _, _ = _call_new(self.repo, summary=exact_300, slug="boundary-300")
        self.assertEqual(rc_300, 0)

        over_301 = "b" * (A.MAX_DESCRIPTIVE_LEN + 1)
        rc_301, _, err_301 = _call_new(self.repo, summary=over_301, slug="boundary-301")
        self.assertEqual(rc_301, 2)
        self.assertIn(str(A.MAX_DESCRIPTIVE_LEN), err_301)
        self.assertIn(str(A.MAX_DESCRIPTIVE_LEN + 1), err_301)

    def test_agent_mode_refusal_shape(self):
        """E-05 non-regression: --agent mode refusal returns rc 2 without envelope on stdout."""
        rc, out, err = _call_new(
            self.repo, summary="bad\nsummary", agent=True, slug="agent-mode"
        )
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")
        self.assertIn("newline", err.lower())

    def test_legitimate_multiword_message_and_gate_ref_succeed(self):
        """V-03 (f): legitimate multi-word messages and valid gate refs succeed."""
        rc_new, _, _ = _call_new(
            self.repo,
            summary="A normal descriptive summary",
            status="blocked",
            gate_kind="todo",
            gate_ref="TODO.md",
            message="Initial creation note with multiple words",
            slug="legit",
        )
        self.assertEqual(rc_new, 0)
        item_path = next(self.repo.glob("**/*.md"))

        rc_set, _, _ = _call_set(
            self.repo,
            item_path,
            status="open",
            message="Unblocking the item after resolution",
        )
        self.assertEqual(rc_set, 0)
        item_path = next(self.repo.glob("**/*.md"))

        rc_note, _, _ = _call_note(
            self.repo,
            item_path,
            message="A standard multi-word progress note",
        )
        self.assertEqual(rc_note, 0)
