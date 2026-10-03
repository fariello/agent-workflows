"""Tests for Section 8.8 output-safety enforcement at research write paths (IPD deftzy).

Pins:
1. HELPER CONTRACT (E-01 / V-01): research_cmd._refuse_unsafe_descriptive matches helper shape,
   delegates to shared owner, returns None for valid, and distinguishes embedded newlines,
   control characters, and length bounds.
2. INJECTION CLOSURE (E-02, E-03, E-04, E-05 / V-02, V-03, V-04): newlines in --summary, --topic tokens,
   and --consumed-by tokens across plan_new, plan_new_comparison, plan_set_outcome, and aw adopt
   are refused nonzero without modifying or creating files.
3. PRE-FIX DEMONSTRATION (E-05): proof via rendered strings that pre-fix injections smuggled front-matter
   keys and release gates without detection by existing checkers (passes before and after).
4. BOUNDARY AND NON-REGRESSIONS (E-06): exact MAX_DESCRIPTIVE_LEN boundary (300 accepted, 301 refused),
   quiet-versus-loud distinction, existing planner refusals unchanged, conforming creations and updates
   succeed, deliberate under-scope of text writers preserved, and --slug/--set kebab safety confirmed.
"""

from __future__ import annotations

import hashlib
import io
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import attention_contract as A
from agent_workflows import cli
from agent_workflows import research_cmd as C
from agent_workflows import research_contract as R


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_cli(argv: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    old_cwd = Path.cwd()
    if cwd is not None:
        os.chdir(cwd)
    try:
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv)
            except SystemExit as e:
                rc = int(e.code or 0)
    finally:
        if cwd is not None:
            os.chdir(old_cwd)
    combined = out.getvalue() + err.getvalue()
    return rc, out.getvalue(), combined


class TestHelperContract(unittest.TestCase):
    """E-01 / V-01: helper contract and delegation."""

    def test_helper_refuse_unsafe_descriptive_contract(self):
        """E-01, V-01: research_cmd._refuse_unsafe_descriptive matches required helper shape and results."""
        self.assertTrue(
            hasattr(C, "_refuse_unsafe_descriptive"),
            "Helper _refuse_unsafe_descriptive missing from research_cmd",
        )
        fn = getattr(C, "_refuse_unsafe_descriptive")

        # bound_length=True (default)
        self.assertIsNone(fn("aw research new", "--summary", None))
        self.assertIsNone(fn("aw research new", "--summary", "ok"))

        msg_nl = fn("aw research new", "--summary", "a\nb")
        self.assertIsNotNone(msg_nl)
        self.assertIn("newline", msg_nl.lower())
        self.assertIn("--summary", msg_nl)

        msg_ctrl = fn("aw research new", "--summary", "a\x07b")
        self.assertIsNotNone(msg_ctrl)
        self.assertIn("control", msg_ctrl.lower())
        self.assertIn("--summary", msg_ctrl)

        msg_len = fn("aw research new", "--summary", "x" * 340)
        self.assertIsNotNone(msg_len)
        self.assertIn("300", msg_len)
        self.assertIn("340", msg_len)
        self.assertIn("--summary", msg_len)

        # bound_length=False (line-integrity mode)
        self.assertIsNone(fn("v", "--flag", "x" * 340, bound_length=False))
        self.assertIsNone(fn("v", "--flag", "x" * 1200, bound_length=False))

        msg_nl_unbound = fn("v", "--flag", "a\nb", bound_length=False)
        self.assertIsNotNone(msg_nl_unbound)
        self.assertIn("newline", msg_nl_unbound.lower())
        self.assertIn("--flag", msg_nl_unbound)

        msg_ctrl_unbound = fn("v", "--flag", "a\x07b", bound_length=False)
        self.assertIsNotNone(msg_ctrl_unbound)
        self.assertIn("control", msg_ctrl_unbound.lower())
        self.assertIn("--flag", msg_ctrl_unbound)

        # MANDATORY late control character check (V-01)
        late_ctrl = "a" * 500 + "\x07" + "b"
        msg_late_ctrl = fn("v", "--flag", late_ctrl, bound_length=False)
        self.assertIsNotNone(
            msg_late_ctrl, "Late control character past char 300 must be refused"
        )
        self.assertIn("control", msg_late_ctrl.lower())
        self.assertIn("--flag", msg_late_ctrl)

        # Side-by-side byte identity check with delegate
        from agent_workflows import backlog as _backlog

        for sample, flag in [
            ("a\nb", "--summary"),
            ("a\x07b", "--summary"),
            ("x" * 340, "--summary"),
        ]:
            ours = fn("v", flag, sample)
            theirs = _backlog._refuse_unsafe_descriptive("v", flag, sample)
            self.assertEqual(ours, theirs)


class _BaseResearchRepo(unittest.TestCase):
    """Throwaway repo with git init and research directories."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="aw_test_res_safety_"))
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
        self.research = self.tmp / ".aw" / "records" / "research"
        self.research.mkdir(parents=True, exist_ok=True)
        self.inbox = self.tmp / ".aw" / "inbox"
        self.inbox.mkdir(parents=True, exist_ok=True)

    def _all_research_docs(self) -> list[Path]:
        return sorted(
            p for p in self.research.rglob("*.md") if p.name not in ("INDEX.md",)
        )

    def _create_conforming_doc(
        self, slug: str = "targ", summary: str = "legit target"
    ) -> Path:
        rc, out, err = _run_cli(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                slug,
                "--summary",
                summary,
                "--apply",
            ],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 0, f"Failed to create conforming doc: {err}")
        docs = self._all_research_docs()
        self.assertTrue(docs, "No doc created")
        return docs[-1]


class TestResearchNewInjection(_BaseResearchRepo):
    """E-02, E-03, E-05 / V-02, V-03: plan_new and research new injection refusals."""

    def test_plan_new_summary_injection_refused(self):
        """E-02, E-05: plan_new returns (None, err) on summary newline."""
        injected = "legit\nstatus: reference\nblocks-release: next"
        files, err = C.plan_new(
            research_root=self.research,
            kind="findings",
            slug="x",
            summary=injected,
        )
        self.assertIsNone(files)
        self.assertIsNotNone(err)
        self.assertIn("--summary", err)
        self.assertIn("newline", err.lower())

    def test_cli_research_new_summary_injection_refused(self):
        """E-02, E-05, V-02(a): aw research new refuses summary injection at exit 2, writing no file."""
        injected = "legit\nstatus: reference\nblocks-release: next"
        rc, out, err = _run_cli(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "x",
                "--summary",
                injected,
                "--apply",
            ],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 2)
        self.assertEqual(self._all_research_docs(), [])
        self.assertIn("--summary", err)
        self.assertIn("newline", err.lower())

    def test_cli_research_new_preview_refused_on_summary_injection(self):
        """E-02, V-02(c), F-12: preview without --apply refuses summary injection and emits no rendered block."""
        injected = "legit\nstatus: reference"
        rc, out, err = _run_cli(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "x",
                "--summary",
                injected,
            ],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 2)
        self.assertNotIn("status: reference", out)
        self.assertIn("--summary", err)
        self.assertIn("newline", err.lower())

    def test_plan_new_topic_token_injection_refused(self):
        """E-03, E-05: plan_new refuses crafted bracket-closing topic token."""
        crafted = "a]\nstatus: reference\nblocks-release: next\njunk: [x"
        files, err = C.plan_new(
            research_root=self.research,
            kind="findings",
            slug="x",
            summary="ok",
            topic=[crafted],
        )
        self.assertIsNone(files)
        self.assertIsNotNone(err)
        self.assertIn("--topic", err)
        self.assertIn("newline", err.lower())
        self.assertIn("a]", err)

    def test_cli_research_new_topic_injection_refused(self):
        """E-03, E-05, V-03(a): aw research new refuses crafted topic injection at exit 2, writing no file."""
        crafted = "a]\nstatus: reference\nblocks-release: next\njunk: [x"
        rc, out, err = _run_cli(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "x",
                "--summary",
                "ok",
                "--topic",
                crafted,
                "--apply",
            ],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 2)
        self.assertEqual(self._all_research_docs(), [])
        self.assertIn("--topic", err)
        self.assertIn("newline", err.lower())
        self.assertIn("a]", err)


class TestResearchNewComparisonInjection(_BaseResearchRepo):
    """E-03, E-05 / V-03(c), V-03(d): plan_new_comparison injection refusals."""

    def test_plan_new_comparison_summary_injection_refused(self):
        """E-03, E-05, V-03(d): plan_new_comparison refuses summary newline (flag currently not written per ol1m2q)."""
        injected = "legit\nstatus: reference"
        files, err = C.plan_new_comparison(
            research_root=self.research,
            set_id="comp",
            slug="x",
            models=["gpt56"],
            summary=injected,
        )
        self.assertIsNone(files)
        self.assertIsNotNone(err)
        self.assertIn("--summary", err)
        self.assertIn("newline", err.lower())

    def test_cli_research_new_comparison_summary_injection_refused(self):
        """E-03, E-05, V-03(d): aw research new-comparison refuses summary newline at exit 2, writing no file."""
        injected = "legit\nstatus: reference"
        rc, out, err = _run_cli(
            [
                "research",
                "new-comparison",
                "--set",
                "comp",
                "--slug",
                "x",
                "--models",
                "gpt56",
                "--summary",
                injected,
                "--apply",
            ],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 2)
        self.assertEqual(self._all_research_docs(), [])
        self.assertIn("--summary", err)
        self.assertIn("newline", err.lower())

    def test_plan_new_comparison_topic_token_injection_refused(self):
        """E-03, E-05, V-03(c): plan_new_comparison refuses topic token with newline."""
        crafted = "a]\nstatus: reference"
        files, err = C.plan_new_comparison(
            research_root=self.research,
            set_id="comp",
            slug="x",
            models=["gpt56"],
            topic=[crafted],
        )
        self.assertIsNone(files)
        self.assertIsNotNone(err)
        self.assertIn("--topic", err)
        self.assertIn("newline", err.lower())

    def test_cli_research_new_comparison_topic_injection_refused(self):
        """E-03, E-05, V-03(c): aw research new-comparison refuses topic token injection at exit 2, writing no file."""
        crafted = "a]\nstatus: reference"
        rc, out, err = _run_cli(
            [
                "research",
                "new-comparison",
                "--set",
                "comp",
                "--slug",
                "x",
                "--models",
                "gpt56",
                "--topic",
                crafted,
                "--apply",
            ],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 2)
        self.assertEqual(self._all_research_docs(), [])
        self.assertIn("--topic", err)
        self.assertIn("newline", err.lower())


class TestResearchSetOutcomeInjection(_BaseResearchRepo):
    """E-04, E-05 / V-04: plan_set_outcome and CLI set-outcome injection refusals."""

    def test_plan_set_outcome_consumed_by_injection_refused(self):
        """E-04, E-05: plan_set_outcome returns (None, None, err) on consumed_by token newline."""
        doc_path = self._create_conforming_doc("set-test")
        id6 = R.parse_name(doc_path.name)[0].id6
        crafted = "aaaaaa]\nstatus: active\njunk: [x"

        path, new_text, err = C.plan_set_outcome(
            self.research,
            id6,
            outcome="adopted",
            consumed_by=[crafted],
            repo_root=self.tmp,
        )
        self.assertIsNone(path)
        self.assertIsNone(new_text)
        self.assertIsNotNone(err)
        self.assertIn("--consumed-by", err)
        self.assertIn("newline", err.lower())
        self.assertIn("aaaaaa]", err)

    def test_cli_research_set_outcome_consumed_by_injection_refused(self):
        """E-04, E-05, V-04(a): aw research set-outcome refuses consumed-by injection at exit 2, preserving byte-identity."""
        doc_path = self._create_conforming_doc("set-test-cli")
        id6 = R.parse_name(doc_path.name)[0].id6
        before_hash = _sha256(doc_path)
        crafted = "aaaaaa]\nstatus: active\njunk: [x"

        rc, out, err = _run_cli(
            [
                "research",
                "set-outcome",
                id6,
                "--consumed-by",
                crafted,
                "--to",
                "adopted",
                "--apply",
                "--dir",
                str(self.tmp),
            ],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 2)
        self.assertEqual(_sha256(doc_path), before_hash)
        self.assertIn("--consumed-by", err)
        self.assertIn("newline", err.lower())


class TestAdoptInjection(_BaseResearchRepo):
    """E-02, E-05 / V-02(d): aw adopt injection and heading-derived safety."""

    def test_adopt_summary_flag_injection_refused(self):
        """E-02, E-05, V-02(d): aw adopt refuses newline in --summary, surviving inbox original and writing no record."""
        drop = self.inbox / "report.md"
        drop.write_text("# Valid Title\n\nBody prose here.\n", encoding="utf-8")
        injected = "legit\nstatus: reference\nblocks-release: next"

        rc, out, err = _run_cli(
            [
                "adopt",
                str(drop),
                "--summary",
                injected,
                "--apply",
                "--dir",
                str(self.tmp),
            ],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 2)
        self.assertTrue(drop.exists(), "Inbox original drop must survive refusal")
        self.assertEqual(self._all_research_docs(), [])
        self.assertIn("--summary", err)
        self.assertIn("newline", err.lower())

    def test_adopt_heading_ansi_escape_refused_with_actionable_message(self):
        """E-02, E-05, V-02(d), PR-004: aw adopt refuses drop with ANSI escape heading, names heading source and --summary override."""
        drop = self.inbox / "ansi_drop.md"
        drop.write_text(
            "# Report \x1b[31mRed\x1b[0m\n\nBody prose here.\n", encoding="utf-8"
        )

        rc, out, err = _run_cli(
            ["adopt", str(drop), "--apply", "--dir", str(self.tmp)],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 2)
        self.assertTrue(drop.exists(), "Inbox original drop must survive refusal")
        self.assertEqual(self._all_research_docs(), [])
        self.assertIn("control", err.lower())
        self.assertIn("derived from the drop's first heading", err)
        self.assertIn("--summary", err)
        self.assertIn("override", err.lower())


class TestPreFixDemonstration(unittest.TestCase):
    """E-05, V-05: rendered-string proofs that pre-fix injections smuggled keys (passes before and after)."""

    def test_pre_fix_summary_injection_smuggles_keys_and_checker_blind(self):
        """E-05, F-02, F-10: rendered string with summary newline overrides status, smuggles gate, and checker blind."""
        rendered = C.build_frontmatter(
            id6="t3st01",
            created="20261001",
            set_id="x",
            order="00",
            topic=[],
            model=None,
            kind="findings",
            status="todo",
            outcome="none-yet",
            summary="legit\nstatus: reference\nblocks-release: next",
        )
        parsed = R.parse_frontmatter(rendered)
        self.assertEqual(parsed.get("status"), "reference")
        self.assertEqual(parsed.get("blocks-release"), "next")
        self.assertEqual(R.validate_frontmatter(parsed), [])

    def test_pre_fix_crafted_topic_token_smuggles_keys_and_checker_blind(self):
        """E-05, F-05, V-03(b): rendered string with crafted topic token smuggles keys and checker blind."""
        crafted = "a]\nstatus: reference\nblocks-release: next\njunk: [x"
        rendered = C.build_frontmatter(
            id6="t3st02",
            created="20261001",
            set_id="x",
            order="00",
            topic=[crafted],
            model=None,
            kind="research-prompt",
            status=None,
            outcome="none-yet",
            summary="ok",
        )
        parsed = R.parse_frontmatter(rendered)
        self.assertEqual(parsed.get("topic"), ["a"])
        self.assertEqual(parsed.get("status"), "reference")
        self.assertEqual(parsed.get("blocks-release"), "next")
        self.assertEqual(parsed.get("junk"), ["x"])
        self.assertEqual(R.validate_frontmatter(parsed), [])

    def test_pre_fix_crafted_consumed_by_smuggles_status_and_checker_blind(self):
        """E-05, F-06, V-04(b): update_frontmatter_fields with crafted consumed-by smuggles status and checker blind."""
        base = C.build_frontmatter(
            id6="t3st03",
            created="20261001",
            set_id="x",
            order="00",
            topic=["ok"],
            model=None,
            kind="findings",
            status="todo",
            outcome="none-yet",
            summary="ok",
            consumed_by=["orig"],
        )
        crafted = "[aaaaaa]\nstatus: active\njunk: [x]"
        updated = C.update_frontmatter_fields(base, {"consumed-by": crafted})
        parsed = R.parse_frontmatter(updated)
        self.assertEqual(parsed.get("consumed-by"), ["aaaaaa"])
        self.assertEqual(parsed.get("status"), "active")
        self.assertEqual(parsed.get("junk"), ["x"])
        self.assertEqual(R.validate_frontmatter(parsed), [])


class TestBoundaryAndNonRegressions(_BaseResearchRepo):
    """E-06, V-06: boundary, quiet-form, and non-regressions."""

    def test_summary_length_boundary_300_accepted_301_refused(self):
        """E-06, V-06: boundary test proves 300 characters accepted and 301 refused."""
        summary_300 = "x" * A.MAX_DESCRIPTIVE_LEN
        files_300, err_300 = C.plan_new(
            research_root=self.research,
            kind="findings",
            slug="bound-ok",
            summary=summary_300,
        )
        self.assertIsNone(
            err_300, f"300 chars should be accepted, got error: {err_300}"
        )
        self.assertIsNotNone(files_300)

        summary_301 = "x" * (A.MAX_DESCRIPTIVE_LEN + 1)
        files_301, err_301 = C.plan_new(
            research_root=self.research,
            kind="findings",
            slug="bound-bad",
            summary=summary_301,
        )
        self.assertIsNone(files_301)
        self.assertIsNotNone(err_301)
        self.assertIn("300", err_301)
        self.assertIn("301", err_301)

    def test_quiet_versus_loud_distinction_both_refused(self):
        """E-06, V-06: quiet bracket-closing topic and consumed-by are refused, though pre-fix validated clean."""
        crafted_topic = "a]\nstatus: reference\nblocks-release: next\njunk: [x"
        files_t, err_t = C.plan_new(
            research_root=self.research,
            kind="findings",
            slug="x",
            summary="ok",
            topic=[crafted_topic],
        )
        self.assertIsNone(files_t)
        self.assertIsNotNone(err_t)

        doc_path = self._create_conforming_doc("quiet-test")
        id6 = R.parse_name(doc_path.name)[0].id6
        crafted_consumed = "aaaaaa]\nstatus: active\njunk: [x"
        path_c, new_c, err_c = C.plan_set_outcome(
            self.research,
            id6,
            outcome="adopted",
            consumed_by=[crafted_consumed],
            repo_root=self.tmp,
        )
        self.assertIsNone(path_c)
        self.assertIsNotNone(err_c)

    def test_existing_planner_refusals_preserved(self):
        """E-06(a), V-06: five existing planner refusals keep their exact messages."""
        # 1. unknown kind
        _, err_k = C.plan_new(
            research_root=self.research,
            kind="unknown-kind-xyz",
            slug="x",
            summary="ok",
        )
        self.assertIsNotNone(err_k)
        self.assertIn("unknown kind 'unknown-kind-xyz'", err_k)

        # 2. malformed model token
        _, err_m = C.plan_new(
            research_root=self.research,
            kind="findings",
            slug="x",
            summary="ok",
            model="bad_model!",
        )
        self.assertIsNotNone(err_m)
        self.assertIn(
            "malformed model token 'bad_model!'; must match [a-z0-9-]+", err_m
        )

        # 3. priority must be one of
        _, err_p = C.plan_new(
            research_root=self.research,
            kind="findings",
            slug="x",
            summary="ok",
            priority="invalid-prio",
        )
        self.assertIsNotNone(err_p)
        self.assertIn("priority must be one of ['high', 'low', 'medium']", err_p)

        # 4. a --slug or --summary is required to derive the name
        _, err_s = C.plan_new(
            research_root=self.research,
            kind="findings",
            slug="",
            summary="",
        )
        self.assertIsNotNone(err_s)
        self.assertEqual(err_s, "a --slug or --summary is required to derive the name")

        # 5. outcome must be one of
        doc_path = self._create_conforming_doc("prio-targ")
        id6 = R.parse_name(doc_path.name)[0].id6
        _, _, err_o = C.plan_set_outcome(
            self.research,
            id6,
            outcome="invalid-outcome",
            consumed_by=None,
            repo_root=self.tmp,
        )
        self.assertIsNotNone(err_o)
        self.assertIn("outcome must be one of", err_o)

    def test_conforming_creation_and_modifications_succeed(self):
        """E-06(b), V-06: conforming research creations and outcome updates succeed and check clean."""
        # Conforming creation with multi-topic
        rc, out, err = _run_cli(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "good-doc",
                "--summary",
                "A conforming summary.",
                "--topic",
                "topic1,topic2",
                "--apply",
            ],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 0, f"Expected 0 exit, got {rc}: {err}")
        docs = self._all_research_docs()
        self.assertTrue(docs)
        content = docs[-1].read_text(encoding="utf-8")
        self.assertIn("topic: [topic1, topic2]", content)

        # Index and check on fixture
        rc_idx, _, _ = _run_cli(["research", "index"], cwd=self.tmp)
        self.assertEqual(rc_idx, 0)
        rc_chk, out_chk, _ = _run_cli(["check", "research", "--agent"], cwd=self.tmp)
        self.assertEqual(rc_chk, 0, f"check research failed: {out_chk}")

        # Conforming comparison scaffold
        files_comp, err_comp = C.plan_new_comparison(
            research_root=self.research,
            set_id="comp-set",
            slug="comp-slug",
            models=["gpt56", "sonnet5"],
            summary="A comparison summary.",
            topic=["a", "b"],
        )
        self.assertIsNone(err_comp)
        self.assertEqual(len(files_comp), 4)  # prompt + 2 models + recon

        # Conforming set-outcome updates
        id6 = R.parse_name(docs[-1].name)[0].id6
        path_set, new_text, err_set = C.plan_set_outcome(
            self.research,
            id6,
            outcome="adopted",
            consumed_by=["plan01", "spec02"],
            repo_root=self.tmp,
        )
        self.assertIsNone(err_set)
        self.assertIsNotNone(new_text)
        self.assertIn("consumed-by: [plan01, spec02]", new_text)

        # Conforming set-outcome clear sentinel '-'
        path_clr, new_clr, err_clr = C.plan_set_outcome(
            self.research,
            id6,
            outcome="adopted",
            consumed_by=None,
            clear_consumed=True,
            repo_root=self.tmp,
        )
        self.assertIsNone(err_clr)
        self.assertIsNotNone(new_clr)
        self.assertIn("consumed-by: []", new_clr)

    def test_slug_and_set_remain_unguarded_and_kebabed(self):
        """E-06(c), V-06, OQ-03: --slug and --set remain unguarded and kebab a newline-bearing value safely."""
        files, err = C.plan_new(
            research_root=self.research,
            kind="findings",
            slug="legit\nstatus: active",
            summary="ok",
        )
        self.assertIsNone(err)
        self.assertIsNotNone(files)
        self.assertIn("legit-status-active", files[0].path.name)
        parsed = R.parse_frontmatter(files[0].content)
        self.assertNotIn("status: active", files[0].content)
        self.assertEqual(parsed.get("status"), "todo")

        files_set, err_set = C.plan_new(
            research_root=self.research,
            kind="findings",
            set_id="my\nset",
            slug="clean-slug",
            summary="ok",
        )
        self.assertIsNone(err_set)
        self.assertIsNotNone(files_set)
        self.assertIn("my-set", files_set[0].path.name)
        parsed_set = R.parse_frontmatter(files_set[0].content)
        self.assertEqual(parsed_set.get("set"), "my-set")

    def test_refusal_writes_nothing_listing_unchanged(self):
        """E-06(d), V-06: refused plan_new call leaves research tree directory listing unchanged."""
        before = sorted(p.name for p in self.research.rglob("*.md"))
        C.plan_new(
            research_root=self.research,
            kind="findings",
            slug="x",
            summary="unsafe\nnewline",
        )
        after = sorted(p.name for p in self.research.rglob("*.md"))
        self.assertEqual(before, after)

    def test_deliberate_under_scope_text_writers_unchanged(self):
        """E-06(e), V-06: update_frontmatter_fields and _set_priority_line remain text writers (deliberate under-scope)."""
        base = C.build_frontmatter(
            id6="t3st99",
            created="20261001",
            set_id="x",
            order="00",
            topic=[],
            model=None,
            kind="findings",
            status="todo",
            outcome="none-yet",
            summary="ok",
            consumed_by=[],
        )
        unsafe_raw = "[a]\nstatus: active"
        substituted = C.update_frontmatter_fields(base, {"consumed-by": unsafe_raw})
        self.assertIn(unsafe_raw, substituted)

        unsafe_prio = "high\nstatus: active"
        prio_sub = C._set_priority_line(base, unsafe_prio)
        self.assertIn(unsafe_prio, prio_sub)
