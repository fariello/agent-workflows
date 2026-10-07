"""Tests for check.staged-illegal-backlog-transition commit-scoped gate (IPD miimjb, E-05).

All thirteen cases test observable behavior against real staged git state in throwaway repositories.
No code-pinning tests: no inspect, no ast, no regex over source files, no line counting.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Optional, Tuple

from agent_workflows import attention_contract, backlog, check_engine


def _run(cmd: str, cwd: str | Path) -> str:
    res = subprocess.run(
        cmd,
        cwd=str(cwd),
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return res.stdout


def _init_repo(td: str | Path) -> None:
    _run("git init -q", td)
    _run("git config user.name 'Test Runner'", td)
    _run("git config user.email 'test@example.com'", td)
    for st in backlog.STATUSES:
        os.makedirs(os.path.join(td, f".aw/records/backlog/{st}"), exist_ok=True)


def _make_item(
    id6: str,
    status: str,
    summary: str = "Test item",
    history: Optional[str] = None,
    extra_body: str = "",
    omit_id: bool = False,
) -> str:
    id_line = f"- Id: {id6}\n" if not omit_id else ""
    gate_line = "- Gate-Kind: branch\n- Gate-Ref: main\n" if status == "blocked" else ""
    hist = history or f"- 2026-10-01 {status} (aw backlog): initial\n"
    return (
        f"# {id6}: {summary}\n\n"
        f"- Date: 2026-10-01\n"
        f"- Status: {status}\n"
        f"- Work-Kind: chore\n"
        f"- Priority: low\n"
        f"{id_line}"
        f"- Set: testset\n"
        f"{gate_line}"
        f"\n## Workflow history\n"
        f"{hist}\n"
        f"## Details\n"
        f"Standard item body content for testing.\n"
        f"{extra_body}\n"
    )


def _derive_illegal_edge() -> Tuple[str, str]:
    for s1 in sorted(backlog.STATUSES):
        for s2 in sorted(backlog.STATUSES):
            if s1 != s2 and not attention_contract.backlog_transition_allowed(s1, s2):
                return (s1, s2)
    raise unittest.SkipTest("BACKLOG_TRANSITIONS has no illegal edges to test")


class TestStagedIllegalBacklogTransitionGate(unittest.TestCase):
    """Pin the staged illegal backlog status transition rule by outcome against real git state."""

    def test_a_thorough_illegal_move_refused(self) -> None:
        """(a) An illegal edge performed as a thorough move (status rewritten and file git mv'd) is refused."""
        from_st, to_st = _derive_illegal_edge()
        with tempfile.TemporaryDirectory() as td:
            _init_repo(td)
            id6 = "item01"
            rel_from = f".aw/records/backlog/{from_st}/20261001-{id6}-test.md"
            full_from = os.path.join(td, rel_from)
            with open(full_from, "w", encoding="utf-8") as f:
                f.write(_make_item(id6, from_st))
            _run(f"git add {rel_from}", td)
            _run("git commit -m 'initial' -q", td)

            # Move and edit to illegal status
            rel_to = f".aw/records/backlog/{to_st}/20261001-{id6}-test.md"
            _run(f"git mv {rel_from} {rel_to}", td)
            with open(os.path.join(td, rel_to), "w", encoding="utf-8") as f:
                f.write(_make_item(id6, to_st))
            _run(f"git add {rel_to}", td)

            findings = check_engine.check_staged_illegal_backlog_transition(Path(td))
            self.assertEqual(len(findings), 1)
            f = findings[0]
            self.assertEqual(f.rule, "check.staged-illegal-backlog-transition")
            self.assertEqual(f.location, rel_to)
            self.assertIn(f"from '{from_st}' to '{to_st}'", f.detail)
            self.assertEqual(f.recovery, f"aw backlog set {to_st} {id6}")
            # Assert on-disk state
            self.assertTrue(os.path.exists(os.path.join(td, rel_to)))
            self.assertFalse(os.path.exists(full_from))

    def test_b_heavy_rewrite_delete_plus_add_refused(self) -> None:
        """(b) The SAME illegal edge as a heavy rewrite that git reports as D plus A is also refused (F-03)."""
        from_st, to_st = _derive_illegal_edge()
        with tempfile.TemporaryDirectory() as td:
            _init_repo(td)
            id6 = "item02"
            rel_from = f".aw/records/backlog/{from_st}/20261001-{id6}-test.md"
            full_from = os.path.join(td, rel_from)
            with open(full_from, "w", encoding="utf-8") as f:
                f.write(_make_item(id6, from_st))
            _run(f"git add {rel_from}", td)
            _run("git commit -m 'initial' -q", td)

            # Heavy rewrite: replace body with 120 unique lines so similarity drops below rename threshold
            rel_to = f".aw/records/backlog/{to_st}/20261001-{id6}-test.md"
            _run(f"git mv {rel_from} {rel_to}", td)
            heavy_lines = "\n".join(
                f"Completely new rewritten line {i} replacing content {i * 997}."
                for i in range(120)
            )
            with open(os.path.join(td, rel_to), "w", encoding="utf-8") as f:
                f.write(_make_item(id6, to_st, extra_body=heavy_lines))
            _run(f"git add {rel_to}", td)

            # Verify git diff reports D + A (not R)
            diff_out = _run("git diff --cached --name-status -M", td).strip()
            diff_lines = diff_out.splitlines()
            status_codes = [line.split("\t")[0] for line in diff_lines if line]
            self.assertIn("D", status_codes, f"Expected D in git diff, got: {diff_out}")
            self.assertIn("A", status_codes, f"Expected A in git diff, got: {diff_out}")
            self.assertFalse(
                any(code.startswith("R") for code in status_codes),
                f"Expected no R in git diff, got: {diff_out}",
            )

            # ID6 join must still recover the pair and refuse
            findings = check_engine.check_staged_illegal_backlog_transition(Path(td))
            self.assertEqual(len(findings), 1)
            self.assertEqual(
                findings[0].rule, "check.staged-illegal-backlog-transition"
            )
            self.assertEqual(findings[0].location, rel_to)
            self.assertIn(f"from '{from_st}' to '{to_st}'", findings[0].detail)

    def test_c_lazy_illegal_edit_refused(self) -> None:
        """(c) The same illegal edge as a lazy edit (status rewritten in-place, file left in old dir) is refused."""
        from_st, to_st = _derive_illegal_edge()
        with tempfile.TemporaryDirectory() as td:
            _init_repo(td)
            id6 = "item03"
            rel_path = f".aw/records/backlog/{from_st}/20261001-{id6}-test.md"
            full_path = os.path.join(td, rel_path)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(_make_item(id6, from_st))
            _run(f"git add {rel_path}", td)
            _run("git commit -m 'initial' -q", td)

            # Lazy edit: rewrite status in place
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(_make_item(id6, to_st))
            _run(f"git add {rel_path}", td)

            findings = check_engine.check_staged_illegal_backlog_transition(Path(td))
            self.assertEqual(len(findings), 1)
            self.assertEqual(
                findings[0].rule, "check.staged-illegal-backlog-transition"
            )
            self.assertEqual(findings[0].location, rel_path)
            self.assertIn(f"from '{from_st}' to '{to_st}'", findings[0].detail)

    def test_d_illegal_edit_with_workflow_history_refused(self) -> None:
        """(d) The same illegal edge is refused even when the edit adds a plausible workflow history line."""
        from_st, to_st = _derive_illegal_edge()
        with tempfile.TemporaryDirectory() as td:
            _init_repo(td)
            id6 = "item04"
            rel_from = f".aw/records/backlog/{from_st}/20261001-{id6}-test.md"
            full_from = os.path.join(td, rel_from)
            with open(full_from, "w", encoding="utf-8") as f:
                f.write(_make_item(id6, from_st))
            _run(f"git add {rel_from}", td)
            _run("git commit -m 'initial' -q", td)

            # Thorough move with plausible added history line
            rel_to = f".aw/records/backlog/{to_st}/20261001-{id6}-test.md"
            _run(f"git mv {rel_from} {rel_to}", td)
            hist = (
                f"- 2026-10-01 {from_st} (aw backlog): initial\n"
                f"- 2026-10-02 {to_st} (aw backlog): hand moved to {to_st}\n"
            )
            with open(os.path.join(td, rel_to), "w", encoding="utf-8") as f:
                f.write(_make_item(id6, to_st, history=hist))
            _run(f"git add {rel_to}", td)

            findings = check_engine.check_staged_illegal_backlog_transition(Path(td))
            self.assertEqual(len(findings), 1)
            self.assertEqual(
                findings[0].rule, "check.staged-illegal-backlog-transition"
            )

    def test_e_done_to_open_not_refused(self) -> None:
        """(e) done -> open is NOT refused (shipped contract, test-pinned)."""
        if not attention_contract.backlog_transition_allowed("done", "open"):
            raise unittest.SkipTest("done -> open not permitted by BACKLOG_TRANSITIONS")
        with tempfile.TemporaryDirectory() as td:
            _init_repo(td)
            id6 = "item05"
            rel_from = f".aw/records/backlog/done/20261001-{id6}-test.md"
            with open(os.path.join(td, rel_from), "w", encoding="utf-8") as f:
                f.write(_make_item(id6, "done"))
            _run(f"git add {rel_from}", td)
            _run("git commit -m 'initial' -q", td)

            rel_to = f".aw/records/backlog/open/20261001-{id6}-test.md"
            _run(f"git mv {rel_from} {rel_to}", td)
            with open(os.path.join(td, rel_to), "w", encoding="utf-8") as f:
                f.write(_make_item(id6, "open"))
            _run(f"git add {rel_to}", td)

            findings = check_engine.check_staged_illegal_backlog_transition(Path(td))
            self.assertEqual(findings, [])

    def test_f_graduated_to_open_not_refused(self) -> None:
        """(f) graduated -> open is NOT refused (runner containment rollback)."""
        if not attention_contract.backlog_transition_allowed("graduated", "open"):
            raise unittest.SkipTest(
                "graduated -> open not permitted by BACKLOG_TRANSITIONS"
            )
        with tempfile.TemporaryDirectory() as td:
            _init_repo(td)
            id6 = "item06"
            rel_from = f".aw/records/backlog/graduated/20261001-{id6}-test.md"
            with open(os.path.join(td, rel_from), "w", encoding="utf-8") as f:
                f.write(_make_item(id6, "graduated"))
            _run(f"git add {rel_from}", td)
            _run("git commit -m 'initial' -q", td)

            rel_to = f".aw/records/backlog/open/20261001-{id6}-test.md"
            _run(f"git mv {rel_from} {rel_to}", td)
            with open(os.path.join(td, rel_to), "w", encoding="utf-8") as f:
                f.write(_make_item(id6, "open"))
            _run(f"git add {rel_to}", td)

            findings = check_engine.check_staged_illegal_backlog_transition(Path(td))
            self.assertEqual(findings, [])

    def test_g_forward_edge_not_refused(self) -> None:
        """(g) An ordinary forward edge such as open -> graduated is NOT refused."""
        if not attention_contract.backlog_transition_allowed("open", "graduated"):
            raise unittest.SkipTest(
                "open -> graduated not permitted by BACKLOG_TRANSITIONS"
            )
        with tempfile.TemporaryDirectory() as td:
            _init_repo(td)
            id6 = "item07"
            rel_from = f".aw/records/backlog/open/20261001-{id6}-test.md"
            with open(os.path.join(td, rel_from), "w", encoding="utf-8") as f:
                f.write(_make_item(id6, "open"))
            _run(f"git add {rel_from}", td)
            _run("git commit -m 'initial' -q", td)

            rel_to = f".aw/records/backlog/graduated/20261001-{id6}-test.md"
            _run(f"git mv {rel_from} {rel_to}", td)
            with open(os.path.join(td, rel_to), "w", encoding="utf-8") as f:
                f.write(_make_item(id6, "graduated"))
            _run(f"git add {rel_to}", td)

            findings = check_engine.check_staged_illegal_backlog_transition(Path(td))
            self.assertEqual(findings, [])

    def test_h_newly_staged_item_not_refused(self) -> None:
        """(h) A brand-new item staged at open with no HEAD side is NOT refused (add case)."""
        with tempfile.TemporaryDirectory() as td:
            _init_repo(td)
            id6 = "item08"
            rel_path = f".aw/records/backlog/open/20261001-{id6}-test.md"
            with open(os.path.join(td, rel_path), "w", encoding="utf-8") as f:
                f.write(_make_item(id6, "open"))
            _run(f"git add {rel_path}", td)

            findings = check_engine.check_staged_illegal_backlog_transition(Path(td))
            self.assertEqual(findings, [])

    def test_i_staged_deletion_not_refused(self) -> None:
        """(i) A staged deletion with no index side is NOT refused (delete case)."""
        with tempfile.TemporaryDirectory() as td:
            _init_repo(td)
            id6 = "item09"
            rel_path = f".aw/records/backlog/open/20261001-{id6}-test.md"
            with open(os.path.join(td, rel_path), "w", encoding="utf-8") as f:
                f.write(_make_item(id6, "open"))
            _run(f"git add {rel_path}", td)
            _run("git commit -m 'initial' -q", td)

            _run(f"git rm {rel_path}", td)

            findings = check_engine.check_staged_illegal_backlog_transition(Path(td))
            self.assertEqual(findings, [])

    def test_j_same_status_body_edit_not_refused(self) -> None:
        """(j) A same-status body edit is NOT refused (the no-op)."""
        with tempfile.TemporaryDirectory() as td:
            _init_repo(td)
            id6 = "item10"
            rel_path = f".aw/records/backlog/open/20261001-{id6}-test.md"
            with open(os.path.join(td, rel_path), "w", encoding="utf-8") as f:
                f.write(_make_item(id6, "open"))
            _run(f"git add {rel_path}", td)
            _run("git commit -m 'initial' -q", td)

            with open(os.path.join(td, rel_path), "w", encoding="utf-8") as f:
                f.write(
                    _make_item(id6, "open", extra_body="Updated notes and context.")
                )
            _run(f"git add {rel_path}", td)

            findings = check_engine.check_staged_illegal_backlog_transition(Path(td))
            self.assertEqual(findings, [])

    def test_k_out_of_vocabulary_status_not_refused(self) -> None:
        """(k) Status outside backlog.STATUSES is NOT refused by this rule (left to backlog.status-invalid)."""
        with tempfile.TemporaryDirectory() as td:
            _init_repo(td)
            id6 = "item11"
            rel_path = f".aw/records/backlog/open/20261001-{id6}-test.md"
            with open(os.path.join(td, rel_path), "w", encoding="utf-8") as f:
                f.write(_make_item(id6, "open"))
            _run(f"git add {rel_path}", td)
            _run("git commit -m 'initial' -q", td)

            # Change status to invalid vocabulary token 'nonexistent'
            with open(os.path.join(td, rel_path), "w", encoding="utf-8") as f:
                f.write(_make_item(id6, "nonexistent"))
            _run(f"git add {rel_path}", td)

            findings = check_engine.check_staged_illegal_backlog_transition(Path(td))
            self.assertEqual(findings, [])

    def test_l_unreadable_id_not_refused(self) -> None:
        """(l) Item with no readable - Id: is NOT refused by this rule (left to backlog.id-invalid)."""
        from_st, to_st = _derive_illegal_edge()
        with tempfile.TemporaryDirectory() as td:
            _init_repo(td)
            id6 = "item12"
            rel_path = f".aw/records/backlog/{from_st}/20261001-{id6}-test.md"
            with open(os.path.join(td, rel_path), "w", encoding="utf-8") as f:
                f.write(_make_item(id6, from_st, omit_id=True))
            _run(f"git add {rel_path}", td)
            _run("git commit -m 'initial' -q", td)

            rel_to = f".aw/records/backlog/{to_st}/20261001-{id6}-test.md"
            _run(f"git mv {rel_path} {rel_to}", td)
            with open(os.path.join(td, rel_to), "w", encoding="utf-8") as f:
                f.write(_make_item(id6, to_st, omit_id=True))
            _run(f"git add {rel_to}", td)

            findings = check_engine.check_staged_illegal_backlog_transition(Path(td))
            self.assertEqual(findings, [])

    def test_m_division_of_labour_lazy_vs_thorough(self) -> None:
        """(m) Division of labour: lazy edit reported by BOTH rules; thorough edit reported by this rule alone."""
        from_st, to_st = _derive_illegal_edge()
        with tempfile.TemporaryDirectory() as td:
            _init_repo(td)
            id6_lazy = "item13"
            rel_lazy = f".aw/records/backlog/{from_st}/20261001-{id6_lazy}-lazy.md"
            with open(os.path.join(td, rel_lazy), "w", encoding="utf-8") as f:
                f.write(_make_item(id6_lazy, from_st))
            _run(f"git add {rel_lazy}", td)
            _run("git commit -m 'initial lazy' -q", td)

            # Lazy edit: rewrite status in place, leave in old directory
            with open(os.path.join(td, rel_lazy), "w", encoding="utf-8") as f:
                f.write(_make_item(id6_lazy, to_st))
            _run(f"git add {rel_lazy}", td)

            # Both this rule AND backlog.status-dir-mismatch report lazy edit
            staged_findings = check_engine.check_staged_illegal_backlog_transition(
                Path(td)
            )
            staged_rules = [f.rule for f in staged_findings]
            self.assertIn("check.staged-illegal-backlog-transition", staged_rules)

            at_rest_findings = check_engine.check_type(
                Path(td), "backlog", include_retired=True
            )
            at_rest_rules = [f.rule for f in at_rest_findings]
            self.assertIn("backlog.status-dir-mismatch", at_rest_rules)

        with tempfile.TemporaryDirectory() as td:
            _init_repo(td)
            id6_thorough = "item14"
            rel_from = (
                f".aw/records/backlog/{from_st}/20261001-{id6_thorough}-thorough.md"
            )
            with open(os.path.join(td, rel_from), "w", encoding="utf-8") as f:
                f.write(_make_item(id6_thorough, from_st))
            _run(f"git add {rel_from}", td)
            _run("git commit -m 'initial thorough' -q", td)

            # Thorough edit: git mv to new directory AND rewrite status
            rel_to = f".aw/records/backlog/{to_st}/20261001-{id6_thorough}-thorough.md"
            _run(f"git mv {rel_from} {rel_to}", td)
            with open(os.path.join(td, rel_to), "w", encoding="utf-8") as f:
                f.write(_make_item(id6_thorough, to_st))
            _run(f"git add {rel_to}", td)

            # This rule reports thorough edit, but at-rest backlog.status-dir-mismatch reports NOTHING
            staged_findings = check_engine.check_staged_illegal_backlog_transition(
                Path(td)
            )
            staged_rules = [f.rule for f in staged_findings]
            self.assertIn("check.staged-illegal-backlog-transition", staged_rules)

            at_rest_findings = check_engine.check_type(
                Path(td), "backlog", include_retired=True
            )
            at_rest_rules = [f.rule for f in at_rest_findings]
            self.assertNotIn("backlog.status-dir-mismatch", at_rest_rules)


if __name__ == "__main__":
    unittest.main()
