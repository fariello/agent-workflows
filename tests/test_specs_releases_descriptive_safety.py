"""Tests for Section 8.8 output-safety enforcement at specs and releases write paths (IPD uz05bl).

Pins:
1. HELPER CONTRACT (E-01): specs._refuse_unsafe_descriptive matches helper shape, returns None for valid,
   and distinguishes embedded newlines, control characters, and length bounds.
2. INJECTION CLOSURE (E-05): newlines in --title, --summary, --version, --message, --blocks-release,
   and --from-backlog across specs new, specs set, specs note, and releases new are refused nonzero without
   modifying or creating files.
3. PRE-FIX DEMONSTRATION (E-05): proof via rendered strings that pre-fix injections forged approvals and gates
   without detection by existing checkers.
4. LENGTH ASYMMETRY AND LATE-CONTROL (E-06): 1200-char single-line --message is accepted by run_set and run_note,
   while 301-char --summary is refused by run_new; a 500-char message with late control character is refused.
5. BOUNDARY AND NON-REGRESSIONS (E-06): exact MAX_DESCRIPTIVE_LEN boundary, required-field refusals unchanged,
   conforming creations succeed, releases new --agent envelope, deliberate library-level under-scope,
   and already-validated run_set flags preserved.
"""

from __future__ import annotations

import hashlib
import io
import re
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import attention_contract as A
from agent_workflows import cli
from agent_workflows import releases as R
from agent_workflows import specs as S


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_cli(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            rc = cli.main(argv)
        except SystemExit as e:
            rc = int(e.code or 0)
    return rc, out.getvalue(), err.getvalue()


class SpecsReleasesDescriptiveSafetyTests(unittest.TestCase):
    """Test suite for specs and releases descriptive safety (IPD uz05bl)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="aw_test_safety_"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.tmp,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Tester"], cwd=self.tmp, check=True
        )
        self.specs_dir = self.tmp / ".aw" / "records" / "specs" / "draft"
        self.specs_dir.mkdir(parents=True, exist_ok=True)
        self.releases_dir = self.tmp / ".aw" / "records" / "releases" / "planned"
        self.releases_dir.mkdir(parents=True, exist_ok=True)

    def _create_conforming_spec(
        self, title: str = "Base Spec", slug: str = "base"
    ) -> Path:
        rc, out, err = _run_cli(
            [
                "specs",
                "new",
                "--title",
                title,
                "--slug",
                slug,
                "--summary",
                "ok",
                "--apply",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(rc, 0, f"Failed to create conforming spec: {err}")
        files = list(self.tmp.glob(".aw/records/specs/**/*.spec.md"))
        self.assertTrue(files, "No spec created")
        return files[-1]

    # ----------------------------------------------------------------------------------
    # E-01: Helper function verification
    # ----------------------------------------------------------------------------------

    def test_helper_refuse_unsafe_descriptive_contract(self):
        """E-01: specs._refuse_unsafe_descriptive matches required helper shape and results."""
        self.assertTrue(
            hasattr(S, "_refuse_unsafe_descriptive"),
            "Helper _refuse_unsafe_descriptive missing from specs",
        )
        fn = getattr(S, "_refuse_unsafe_descriptive")

        # bound_length=True (default)
        self.assertIsNone(fn("aw specs new", "--title", None))
        self.assertIsNone(fn("aw specs new", "--title", "ok"))

        msg_nl = fn("aw specs new", "--title", "a\nb")
        self.assertIsNotNone(msg_nl)
        self.assertIn("newline", msg_nl.lower())
        self.assertIn("--title", msg_nl)

        msg_ctrl = fn("aw specs new", "--title", "a\x07b")
        self.assertIsNotNone(msg_ctrl)
        self.assertIn("control", msg_ctrl.lower())
        self.assertIn("--title", msg_ctrl)

        msg_len = fn("aw specs new", "--title", "x" * 340)
        self.assertIsNotNone(msg_len)
        self.assertIn("300", msg_len)
        self.assertIn("340", msg_len)
        self.assertIn("--title", msg_len)

        # bound_length=False (line-integrity mode)
        self.assertIsNone(
            fn("aw specs note", "--message", "x" * 340, bound_length=False)
        )
        self.assertIsNone(
            fn("aw specs note", "--message", "x" * 1200, bound_length=False)
        )

        msg_nl_unbound = fn("aw specs note", "--message", "a\nb", bound_length=False)
        self.assertIsNotNone(msg_nl_unbound)
        self.assertIn("newline", msg_nl_unbound.lower())
        self.assertIn("--message", msg_nl_unbound)

        msg_ctrl_unbound = fn(
            "aw specs note", "--message", "a\x07b", bound_length=False
        )
        self.assertIsNotNone(msg_ctrl_unbound)
        self.assertIn("control", msg_ctrl_unbound.lower())
        self.assertIn("--message", msg_ctrl_unbound)

        # MANDATORY late control character check (F-15)
        late_ctrl = "a" * 500 + "\x07" + "b"
        msg_late_ctrl = fn("aw specs note", "--message", late_ctrl, bound_length=False)
        self.assertIsNotNone(
            msg_late_ctrl, "Late control character past char 300 must be refused"
        )
        self.assertIn("control", msg_late_ctrl.lower())
        self.assertIn("--message", msg_late_ctrl)

    # ----------------------------------------------------------------------------------
    # E-05 / E-02: specs new injection refusal
    # ----------------------------------------------------------------------------------

    def test_specs_new_title_injection_refused(self):
        """E-02, E-05: aw specs new refuses newline in --title at exit 2, writing no file."""
        injected = "Legit\n- Status: approved"
        rc, out, err = _run_cli(
            [
                "specs",
                "new",
                "--title",
                injected,
                "--slug",
                "x",
                "--summary",
                "ok",
                "--apply",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(list(self.tmp.glob(".aw/records/specs/**/*.spec.md")), [])
        self.assertIn("--title", err)
        self.assertIn("newline", err.lower())

    def test_specs_new_summary_injection_refused(self):
        """E-02, E-05: aw specs new refuses newline in --summary at exit 2, writing no file."""
        injected = "legit\n- Blocks-Release: next"
        rc, out, err = _run_cli(
            [
                "specs",
                "new",
                "--title",
                "Legit",
                "--slug",
                "x",
                "--summary",
                injected,
                "--apply",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(list(self.tmp.glob(".aw/records/specs/**/*.spec.md")), [])
        self.assertIn("--summary", err)
        self.assertIn("newline", err.lower())

    def test_specs_new_preview_refused_on_title_injection(self):
        """E-02, F-12: aw specs new preview without --apply refuses newline in --title, printing no body."""
        injected = "Legit\n- Status: approved"
        rc, out, err = _run_cli(
            [
                "specs",
                "new",
                "--title",
                injected,
                "--slug",
                "x",
                "--summary",
                "ok",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(rc, 2)
        self.assertNotIn("# Spec: Legit", out)
        self.assertIn("--title", err)
        self.assertIn("newline", err.lower())

    # ----------------------------------------------------------------------------------
    # E-05 / E-03 / E-07: specs set & specs note injection refusal (byte-identity preserved)
    # ----------------------------------------------------------------------------------

    def test_specs_set_message_injection_refused(self):
        """E-03, E-05: aw specs set refuses newline in --message at exit 2, preserving sha256 byte-identity."""
        spec_path = self._create_conforming_spec("Set Msg", "set-msg")
        before_hash = _sha256(spec_path)

        injected = "ok\n- Blocks-Release: next"
        rc, out, err = _run_cli(
            [
                "specs",
                "set",
                str(spec_path),
                "--status",
                "to-review",
                "--message",
                injected,
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(
            rc, 2, f"Expected rc=2 for specs set message refusal, got {rc}: {err}"
        )
        # Refusal must leave file byte-identical
        self.assertEqual(_sha256(spec_path), before_hash)
        self.assertIn("--message", out + err)
        self.assertIn("newline", (out + err).lower())

    def test_specs_note_message_injection_refused(self):
        """E-03, E-05: aw specs note refuses newline in --message at exit 2, preserving sha256 byte-identity."""
        spec_path = self._create_conforming_spec("Note Msg", "note-msg")
        before_hash = _sha256(spec_path)

        injected = "ok\n- Blocks-Release: next"
        rc, out, err = _run_cli(
            ["specs", "note", str(spec_path), "--message", injected]
        )
        self.assertEqual(
            rc, 2, f"Expected rc=2 for specs note message refusal, got {rc}: {err}"
        )
        self.assertEqual(_sha256(spec_path), before_hash)
        self.assertIn("--message", err)
        self.assertIn("newline", err.lower())

    def test_specs_set_blocks_release_injection_refused(self):
        """E-07, E-05: aw specs set refuses newline in --blocks-release at exit 2, preserving sha256."""
        spec_path = self._create_conforming_spec("Set BR", "set-br")
        before_hash = _sha256(spec_path)

        injected = "next\n- Status: approved"
        rc, out, err = _run_cli(
            [
                "specs",
                "set",
                str(spec_path),
                "--status",
                "to-review",
                "--blocks-release",
                injected,
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(
            rc,
            2,
            f"Expected rc=2 for specs set blocks-release refusal, got {rc}: {err}",
        )
        self.assertEqual(_sha256(spec_path), before_hash)
        self.assertIn("--blocks-release", out + err)
        self.assertIn("newline", (out + err).lower())

    def test_specs_set_from_backlog_injection_refused(self):
        """E-07, E-05: aw specs set refuses newline in --from-backlog at exit 2, preserving sha256."""
        spec_path = self._create_conforming_spec("Set FB", "set-fb")
        before_hash = _sha256(spec_path)

        injected = "x\n- Status: approved"
        rc, out, err = _run_cli(
            [
                "specs",
                "set",
                str(spec_path),
                "--status",
                "to-review",
                "--from-backlog",
                injected,
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(
            rc, 2, f"Expected rc=2 for specs set from-backlog refusal, got {rc}: {err}"
        )
        self.assertEqual(_sha256(spec_path), before_hash)
        self.assertIn("--from-backlog", out + err)
        self.assertIn("newline", (out + err).lower())

    # ----------------------------------------------------------------------------------
    # E-05 / E-04: releases new injection refusal
    # ----------------------------------------------------------------------------------

    def test_releases_new_version_injection_refused(self):
        """E-04, E-05: aw releases new refuses newline in --version at exit 2, writing no file."""
        injected = "9.9.9\n- Blocks-Release: next"
        rc, out, err = _run_cli(
            [
                "releases",
                "new",
                "--version",
                injected,
                "--summary",
                "legit",
                "--apply",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(
            list(self.tmp.glob(".aw/records/releases/**/*.release.md")), []
        )
        self.assertIn("--version", err)
        self.assertIn("newline", err.lower())

    def test_releases_new_summary_injection_refused(self):
        """E-04, E-05: aw releases new refuses newline in --summary at exit 2, writing no file."""
        injected = "legit\n- Blocks-Release: next"
        rc, out, err = _run_cli(
            [
                "releases",
                "new",
                "--version",
                "9.9.9",
                "--summary",
                injected,
                "--apply",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(
            list(self.tmp.glob(".aw/records/releases/**/*.release.md")), []
        )
        self.assertIn("--summary", err)
        self.assertIn("newline", err.lower())

    # ----------------------------------------------------------------------------------
    # E-05: Pre-fix demonstration via rendered string (passes before and after)
    # ----------------------------------------------------------------------------------

    def test_pre_fix_title_injection_forges_approval_and_checker_blind(self):
        """E-05, F-03, F-06: rendered spec with title newline forges status approved and passes checker."""
        rendered = S._render_new_spec(
            title="Legit\n- Status: approved",
            id6="id6abc",
            date_iso="2026-10-01",
            summary="ok",
        )
        lines = rendered.splitlines()
        self.assertEqual(S._read_status(lines), "approved")
        self.assertEqual(S._find_status_index(lines), 1)
        # Prior to IPD 1znlxy the checker was blind to duplicate bullets; now it reports the duplicate Status bullet.
        dummy_path = self.tmp / "dummy.spec.md"
        drift = S.validate_spec(dummy_path, rendered)
        self.assertEqual(len(drift), 1)
        self.assertEqual(drift[0].rule, "spec.metadata-bullet-repeated")
        self.assertEqual(drift[0].detail, "metadata bullet - Status: appears 2 times")

    def test_pre_fix_summary_injection_smuggles_gate_and_checker_blind(self):
        """E-05, F-01, F-02, F-06: rendered spec with summary newline smuggles Blocks-Release and passes checker."""
        rendered = S._render_new_spec(
            title="Legit",
            id6="id6abc",
            date_iso="2026-10-01",
            summary="legit\n- Blocks-Release: next",
        )
        m = re.search(r"(?m)^- Blocks-Release:\s*(\S+)\s*$", rendered)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "next")
        dummy_path = self.tmp / "dummy.spec.md"
        self.assertEqual(S.validate_spec(dummy_path, rendered), [])

    # ----------------------------------------------------------------------------------
    # E-06: Length asymmetry, late control char, boundary, and non-regressions
    # ----------------------------------------------------------------------------------

    def test_message_summary_length_asymmetry_and_late_control_refused(self):
        """E-06, F-09, F-15: 1200-char clean message accepted by set and note, 301-char summary refused by new,
        and 500-char message with late control character refused by set and note."""
        spec_path = self._create_conforming_spec("Asym Spec", "asym-spec")

        # 1200-char clean message accepted on specs set
        long_msg = "m" * 1200
        rc_set, _, err_set = _run_cli(
            [
                "specs",
                "set",
                str(spec_path),
                "--status",
                "to-review",
                "--message",
                long_msg,
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(
            rc_set, 0, f"Expected 1200-char message accepted on specs set: {err_set}"
        )

        # Re-glob spec because transition moves it
        spec_files = list(self.tmp.glob(".aw/records/specs/**/*.spec.md"))
        self.assertTrue(spec_files)
        spec_path = spec_files[0]

        # 1200-char clean message accepted on specs note
        rc_note, _, err_note = _run_cli(
            ["specs", "note", str(spec_path), "--message", long_msg]
        )
        self.assertEqual(
            rc_note, 0, f"Expected 1200-char message accepted on specs note: {err_note}"
        )

        # 4301-char summary refused on specs new
        over_summary = "s" * (A.MAX_PROSE_DESCRIPTIVE_LEN + 1)
        rc_new, _, err_new = _run_cli(
            [
                "specs",
                "new",
                "--title",
                "Title",
                "--slug",
                "over",
                "--summary",
                over_summary,
                "--apply",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(rc_new, 2)
        self.assertIn(str(A.MAX_PROSE_DESCRIPTIVE_LEN), err_new)
        self.assertIn(str(A.MAX_PROSE_DESCRIPTIVE_LEN + 1), err_new)

        # Late control character ("a"*500 + "\x07" + "b") REFUSED on both set and note
        spec_ctrl = self._create_conforming_spec("Ctrl Spec", "ctrl-spec")
        late_ctrl = "a" * 500 + "\x07" + "b"
        before_hash = _sha256(spec_ctrl)

        rc_set_ctrl, out_set_ctrl, err_set_ctrl = _run_cli(
            [
                "specs",
                "set",
                str(spec_ctrl),
                "--status",
                "to-review",
                "--message",
                late_ctrl,
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(
            rc_set_ctrl,
            2,
            f"Expected specs set to refuse late control char: {err_set_ctrl}",
        )
        self.assertEqual(_sha256(spec_ctrl), before_hash)
        self.assertIn("control", (out_set_ctrl + err_set_ctrl).lower())

        rc_note_ctrl, _, err_note_ctrl = _run_cli(
            ["specs", "note", str(spec_ctrl), "--message", late_ctrl]
        )
        self.assertEqual(
            rc_note_ctrl,
            2,
            f"Expected specs note to refuse late control char: {err_note_ctrl}",
        )
        self.assertEqual(_sha256(spec_ctrl), before_hash)
        self.assertIn("control", err_note_ctrl.lower())

    def test_summary_length_exact_boundary(self):
        """E-06: exactly MAX_PROSE_DESCRIPTIVE_LEN (4300) accepted, +1 (4301) refused."""
        exact_prose = "x" * A.MAX_PROSE_DESCRIPTIVE_LEN
        rc_exact, _, err_exact = _run_cli(
            [
                "specs",
                "new",
                "--title",
                "Exact Prose",
                "--slug",
                "b-prose",
                "--summary",
                exact_prose,
                "--apply",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(
            rc_exact,
            0,
            f"Expected {A.MAX_PROSE_DESCRIPTIVE_LEN} chars accepted: {err_exact}",
        )

        over_prose = "x" * (A.MAX_PROSE_DESCRIPTIVE_LEN + 1)
        rc_over, _, err_over = _run_cli(
            [
                "specs",
                "new",
                "--title",
                "Over Prose",
                "--slug",
                "b-over",
                "--summary",
                over_prose,
                "--apply",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(rc_over, 2)
        self.assertIn(str(A.MAX_PROSE_DESCRIPTIVE_LEN), err_over)
        self.assertIn(str(A.MAX_PROSE_DESCRIPTIVE_LEN + 1), err_over)

    def test_non_regression_required_flags_unchanged(self):
        """E-06 non-regression (a): required flag errors keep their exit codes and messages."""
        rc_title, _, err_title = _run_cli(
            ["specs", "new", "--title", "", "--dir", str(self.tmp)]
        )
        self.assertEqual(rc_title, 2)
        self.assertEqual(err_title, "aw specs new: --title is required\n")

        rc_ver, _, err_ver = _run_cli(
            [
                "releases",
                "new",
                "--version",
                "",
                "--summary",
                "ok",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(rc_ver, 2)
        self.assertEqual(err_ver, "aw releases new: --version is required\n")

        rc_sum, _, err_sum = _run_cli(
            [
                "releases",
                "new",
                "--version",
                "1.0.0",
                "--summary",
                "",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(rc_sum, 2)
        self.assertEqual(err_sum, "aw releases new: --summary is required\n")

    def test_non_regression_conforming_creations_pass_validation(self):
        """E-06 non-regression (b): conforming specs and releases pass validate_spec and validate_release."""
        spec_path = self._create_conforming_spec("Conforming Spec", "conforming-spec")
        self.assertEqual(
            S.validate_spec(spec_path, spec_path.read_text(encoding="utf-8")), []
        )

        rc_rel, _, err_rel = _run_cli(
            [
                "releases",
                "new",
                "--version",
                "1.0.0",
                "--summary",
                "conforming release",
                "--apply",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(rc_rel, 0, f"releases new failed: {err_rel}")
        rel_files = list(self.tmp.glob(".aw/records/releases/**/*.release.md"))
        self.assertTrue(rel_files)
        rel_path = rel_files[0]
        self.assertEqual(
            R.validate_release(rel_path, rel_path.read_text(encoding="utf-8")), []
        )

    def test_non_regression_releases_new_agent_envelope(self):
        """E-06 non-regression (c): releases new --agent emits well-formed cannot-run envelope on refusal."""
        import json

        rc, out, err = _run_cli(
            [
                "releases",
                "new",
                "--version",
                "1.0.0",
                "--summary",
                "bad\nsummary",
                "--agent",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(rc, 2)
        envelope = json.loads(out.strip())
        self.assertEqual(envelope.get("schema"), "aw.agent/v1")
        self.assertEqual(envelope.get("outcome"), "cannot-run")
        self.assertEqual(envelope.get("exit"), 2)

    def test_non_regression_releases_library_functions_unchanged(self):
        """E-06 non-regression (d): create_release and plan_release still write unsafe summaries at library level."""
        # Deliberate under-scope: direct library call is unguarded
        rel_path = R.create_release(self.tmp, "2.0.0", "unsafe\n- Blocks-Release: next")
        self.assertTrue(rel_path.exists())
        content = rel_path.read_text(encoding="utf-8")
        self.assertIn("- Blocks-Release: next", content)

    def test_non_regression_already_validated_run_set_flags_preserved(self):
        """E-06 non-regression (e): already-validated run_set flags preserve existing refusals and exit codes."""
        spec_path = self._create_conforming_spec("Flags Spec", "flags-spec")

        # --gate-summary must be bounded single control-char-free line (exit 2)
        rc_gs, out_gs, err_gs = _run_cli(
            [
                "specs",
                "set",
                str(spec_path),
                "--status",
                "deferred",
                "--gate-kind",
                "external",
                "--gate-ref",
                "GH#123",
                "--gate-summary",
                "bad\ngate summary",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(rc_gs, 2)
        self.assertIn(
            "aw set: --gate-summary must not contain embedded newlines",
            out_gs + err_gs,
        )

        # --graduated-to takes lowercase-kebab setids (exit 2)
        rc_gt, out_gt, err_gt = _run_cli(
            [
                "specs",
                "set",
                str(spec_path),
                "--status",
                "to-review",
                "--graduated-to",
                "bad\nsetid",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(rc_gt, 2)
        self.assertIn(
            "aw set: --graduated-to takes lowercase-kebab setids", out_gt + err_gt
        )

        # --priority invalid choice (exit 2)
        rc_prio, _, err_prio = _run_cli(
            [
                "specs",
                "set",
                str(spec_path),
                "--status",
                "to-review",
                "--priority",
                "bad\nprio",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(rc_prio, 2)
        self.assertIn("invalid choice", err_prio)

        # --work-kind invalid choice (exit 2)
        rc_wk, _, err_wk = _run_cli(
            [
                "specs",
                "set",
                str(spec_path),
                "--status",
                "to-review",
                "--work-kind",
                "bad\nkind",
                "--dir",
                str(self.tmp),
            ]
        )
        self.assertEqual(rc_wk, 2)
        self.assertIn("invalid choice", err_wk)


if __name__ == "__main__":
    unittest.main()
