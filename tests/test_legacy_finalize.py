"""Behavioral tests for finishing legacy plans (legacyfin `18kg7o`).

Each test builds a real temporary git repository, stamps the repo's cutovers in
`.aw/config/project.json`, and drives the real entry points (`ipd_lifecycle.finalize`,
`cli.main([...])`, `ipd_lint.lint_file`, `config.plan_predates_cutover`), asserting on exit codes,
where the plan file ends up, its recorded history, and printed output.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli
from agent_workflows import config as CFG
from agent_workflows import ipd_lifecycle as LC
from agent_workflows import ipd_lint as L
from agent_workflows import ipd_schema as S
from tests import support

PENDING = Path(".aw/records/plans/pending")

# A plan in the format of a pre-cutover repository: no Kind/Concern/Scope/Author, none of the
# headings added since. Only Date, Status and Id, plus whatever state it recorded.
LEGACY_PLAN = (
    "# IPD: legacy thing\n\n- Date: 2026-07-01\n- Status: approved\n- Id: lg0001\n\n"
    "## Goal\n\nDo the thing.\n"
)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout


class _Repo(unittest.TestCase):
    def setUp(self) -> None:
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git(self.root, "init", "-q")
        _git(self.root, "config", "user.email", "t@e.com")
        _git(self.root, "config", "user.name", "T")
        (self.root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
        self._old_cwd = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, self._old_cwd)
        self.addCleanup(self._tmp.cleanup)

    def stamp(self, **cutovers: str) -> None:
        p = self.root / ".aw/config/project.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps({"schema_version": 2, "cutovers": cutovers}), encoding="utf-8"
        )

    def write_plan(self, text: str, name: str) -> Path:
        p = self.root / PENDING / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def commit(self, msg: str) -> str:
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-q", "-m", msg)
        return _git(self.root, "rev-parse", "HEAD").strip()

    def run_cli(self, *argv: str):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()


class PredicateTests(_Repo):
    def test_strictly_before_cutover_is_legacy(self) -> None:
        self.stamp(ipd_begin_receipt="2026-08-24")
        self.assertTrue(
            CFG.plan_predates_cutover(self.root, "ipd_begin_receipt", "2026-08-23")
        )
        self.assertTrue(
            CFG.plan_predates_cutover(
                self.root, "ipd_begin_receipt", "2026-08-23T23:59:00-05:00"
            )
        )
        self.assertFalse(
            CFG.plan_predates_cutover(self.root, "ipd_begin_receipt", "2026-08-24")
        )
        self.assertFalse(
            CFG.plan_predates_cutover(self.root, "ipd_begin_receipt", "20260901")
        )

    def test_no_cutover_or_no_date_fails_closed(self) -> None:
        self.assertFalse(
            CFG.plan_predates_cutover(self.root, "ipd_begin_receipt", "2020-01-01")
        )
        self.stamp(ipd_begin_receipt="2026-08-24")
        self.assertFalse(
            CFG.plan_predates_cutover(self.root, "ipd_begin_receipt", None)
        )
        self.assertFalse(
            CFG.plan_predates_cutover(self.root, "ipd_begin_receipt", "garbage")
        )


class DeriveBaselineTests(_Repo):
    def test_finds_approval_commit_through_rename_and_edit(self) -> None:
        old = self.root / ".agents/plans/pending/20260701-0001-01-x.md"
        old.parent.mkdir(parents=True)
        old.write_text(LEGACY_PLAN.replace("approved", "draft"), encoding="utf-8")
        self.commit("draft")
        old.write_text(LEGACY_PLAN, encoding="utf-8")
        approval = self.commit("approve")
        new = self.root / PENDING / "20260701-0001-01-x.ipd.md"
        new.parent.mkdir(parents=True)
        _git(self.root, "mv", str(old), str(new))
        new.write_text(LEGACY_PLAN + "\nmore\n", encoding="utf-8")
        self.commit("migrate and edit")
        base = LC.derive_baseline(self.root, new)
        self.assertIsNotNone(base)
        self.assertEqual(base.sha, approval)
        self.assertIn("- Status: approved", base.plan_text)

    def test_none_when_never_approved(self) -> None:
        p = self.write_plan(LEGACY_PLAN.replace("approved", "draft"), "p.ipd.md")
        self.commit("draft only")
        self.assertIsNone(LC.derive_baseline(self.root, p))


class LegacyFinalizeTests(_Repo):
    def setUp(self) -> None:
        super().setUp()
        self.stamp(ipd_begin_receipt="2026-12-31", ipd_plan_format="2026-12-31")
        self.plan = self.write_plan(LEGACY_PLAN, "20260701-0001-01-legacy.ipd.md")
        self.approval = self.commit("approve legacy")

    def test_plain_finalize_moves_plan_and_records_baseline(self) -> None:
        code, out, err = self.run_cli(
            "ipd", "finalize", "lg0001", "--actor", "t", "-m", "done", "--apply"
        )
        self.assertEqual(code, 0, out + err)
        self.assertIn("NOTICE: no begin receipt", err)
        moved = self.root / ".aw/records/plans/executed/20260701-0001-01-legacy.ipd.md"
        self.assertTrue(moved.is_file())
        text = moved.read_text(encoding="utf-8")
        self.assertIn("- Status: executed", text)
        self.assertIn(f"approval commit {self.approval[:12]}", text)
        # No receipt was ever written to disk on the plan's behalf.
        self.assertFalse(
            (self.root / ".aw/state/ipd-lifecycle/lg0001.receipt.json").exists()
        )

    def test_set_executed_takes_same_route(self) -> None:
        code, out, err = self.run_cli(
            "ipd", "set", "executed", "lg0001", "--actor", "t", "-m", "done"
        )
        self.assertEqual(code, 0, out + err)
        self.assertIn("NOTICE: no begin receipt", out + err)
        self.assertTrue(
            (
                self.root / ".aw/records/plans/executed/20260701-0001-01-legacy.ipd.md"
            ).is_file()
        )


class PostCutoverFinalizeTests(_Repo):
    def setUp(self) -> None:
        super().setUp()
        self.stamp(ipd_begin_receipt="2020-01-01", ipd_plan_format="2020-01-01")
        text = support.ready_plan_text(plan_id="nw0001", scope_paths="src/a.py")
        text = (
            text.replace("- [ ] E-01 ", "- [x] E-01 ", 1)
            .replace(
                "  - Execution state: pending", "  - Execution state: performed", 1
            )
            .replace("- [ ] V-01 validates E-01", "- [x] V-01 validates E-01", 1)
            .replace("  - Observed evidence:\n", "  - Observed evidence: ran it.\n", 1)
            .replace("  - Result: pending", "  - Result: pass", 1)
        )
        self.plan = self.write_plan(text, "20260824-demo-01-nw0001-demo.ipd.md")
        self.commit("approve new")

    def test_refuses_and_names_the_flag(self) -> None:
        code, out, _err = self.run_cli(
            "ipd", "finalize", "nw0001", "--actor", "t", "-m", "x"
        )
        self.assertEqual(code, 1)
        self.assertIn("--without-receipt", out)
        self.assertIn("aw ipd begin nw0001", out)
        self.assertTrue(self.plan.is_file())

    def test_scope_check_still_runs_without_receipt(self) -> None:
        code, out, _err = self.run_cli(
            "ipd",
            "finalize",
            "nw0001",
            "--actor",
            "t",
            "-m",
            "x",
            "--apply",
            "--without-receipt",
            "begin skipped",
        )
        self.assertEqual(code, 1)
        self.assertIn("--scope-ack src/a.py", out)
        self.assertTrue(self.plan.is_file())

    def test_empty_reason_refused(self) -> None:
        code, out, _err = self.run_cli(
            "ipd",
            "finalize",
            "nw0001",
            "--actor",
            "t",
            "-m",
            "x",
            "--without-receipt",
            " ",
        )
        self.assertEqual(code, 2)
        self.assertIn("non-empty reason", out)

    def test_reasoned_flag_finalizes_and_records_reason(self) -> None:
        # The scope check still runs from the derived baseline: do the declared work first.
        (self.root / "src").mkdir()
        (self.root / "src/a.py").write_text("x = 1\n", encoding="utf-8")
        self.commit("the work")
        code, out, err = self.run_cli(
            "ipd",
            "finalize",
            "nw0001",
            "--actor",
            "t",
            "-m",
            "x",
            "--apply",
            "--without-receipt",
            "begin skipped by hand run",
        )
        self.assertEqual(code, 0, out + err)
        self.assertIn("NOTICE: finalized WITHOUT a begin receipt", err)
        moved = (
            self.root / ".aw/records/plans/executed/20260824-demo-01-nw0001-demo.ipd.md"
        )
        self.assertIn(
            "reason: begin skipped by hand run", moved.read_text(encoding="utf-8")
        )

    def test_commit_warns_that_begin_was_skipped(self) -> None:
        (self.root / "src").mkdir()
        (self.root / "src/a.py").write_text("x = 1\n", encoding="utf-8")
        _code, _out, err = self.run_cli(
            "commit", "nw0001", "-m", "work", "--", "src/a.py"
        )
        self.assertIn("no begin receipt for nw0001", err)


class LegacyCommitDoesNotWarnTests(_Repo):
    def test_no_warning_for_legacy_plan(self) -> None:
        self.stamp(ipd_begin_receipt="2026-12-31")
        self.write_plan(LEGACY_PLAN, "20260701-0001-01-legacy.ipd.md")
        self.commit("approve legacy")
        _code, _out, err = self.run_cli("test", "lg0001", "--", "true")
        self.assertNotIn("no begin receipt", err)


class LegacyFormatLintTests(_Repo):
    def _lint(self, plan: Path, checkpoint: str):
        return L.lint_file(plan, checkpoint=checkpoint)

    def test_pre_cutover_minimal_plan_conforms_with_advisory(self) -> None:
        self.stamp(ipd_plan_format="2026-12-31")
        plan = self.write_plan(LEGACY_PLAN, "20260701-0001-01-legacy.ipd.md")
        res = self._lint(plan, "pre-transition")
        self.assertEqual(res.disposition, S.DISPOSITION_CONFORMING, res.diagnostics)
        self.assertIn("IPD-L001", [a.code for a in res.advisories])

    def test_post_cutover_same_text_still_refused(self) -> None:
        self.stamp(ipd_plan_format="2026-01-01")
        plan = self.write_plan(LEGACY_PLAN, "20260701-0001-01-legacy.ipd.md")
        res = self._lint(plan, "pre-transition")
        self.assertEqual(res.disposition, S.DISPOSITION_ERROR)
        codes = {d.code for d in res.diagnostics}
        self.assertIn("IPD-M101", codes)
        self.assertIn("IPD-H202", codes)

    def test_legacy_keeps_state_and_identity_rules(self) -> None:
        self.stamp(ipd_plan_format="2026-12-31")
        no_id = LEGACY_PLAN.replace("- Id: lg0001\n", "")
        plan = self.write_plan(no_id, "20260701-0001-01-noid.ipd.md")
        res = self._lint(plan, "pre-transition")
        self.assertEqual(res.disposition, S.DISPOSITION_ERROR)
        self.assertTrue(any("Id" in d.message for d in res.diagnostics))

    def test_author_checkpoint_is_not_downgraded(self) -> None:
        self.stamp(ipd_plan_format="2026-12-31")
        plan = self.write_plan(LEGACY_PLAN, "20260701-0001-01-legacy.ipd.md")
        res = self._lint(plan, "author")
        self.assertEqual(res.disposition, S.DISPOSITION_ERROR)


if __name__ == "__main__":
    unittest.main()


class BulkIdBackfillTests(_Repo):
    """`aw ipd sync <plans...>` / `aw ipd sync --all`: Id-only, preview by default, never terminal."""

    def setUp(self) -> None:
        super().setUp()
        body = "# IPD: {n}\n\n- Date: 2026-07-01\n- Status: approved\n\n## Goal\n"
        self.a = self.write_plan(body.format(n="a"), "20260701-0001-01-a.ipd.md")
        self.b = self.write_plan(body.format(n="b"), "20260701-0001-01-b.ipd.md")
        self.done = self.root / ".aw/records/plans/executed/20260101-0001-01-old.ipd.md"
        self.done.parent.mkdir(parents=True)
        self.done_text = "# IPD: old\n\n- Status: executed\n\n## Goal\n"
        self.done.write_text(self.done_text, encoding="utf-8")
        self.commit("seed")

    def _ids(self, p: Path) -> list:
        return [
            ln
            for ln in p.read_text(encoding="utf-8").splitlines()
            if ln.startswith("- Id: ")
        ]

    def test_all_preview_writes_nothing(self) -> None:
        code, out, _err = self.run_cli("ipd", "sync", "--all")
        self.assertEqual(code, 0, out)
        self.assertIn("would backfill Id in 2 plan(s)", out)
        self.assertEqual(self._ids(self.a), [])

    def test_all_apply_mints_unique_ids_and_skips_terminal(self) -> None:
        code, out, _err = self.run_cli("ipd", "sync", "--all", "--apply")
        self.assertEqual(code, 0, out)
        ia, ib = self._ids(self.a), self._ids(self.b)
        self.assertEqual(len(ia), 1)
        self.assertEqual(len(ib), 1)
        self.assertNotEqual(ia, ib)
        self.assertEqual(self.done.read_text(encoding="utf-8"), self.done_text)
        self.assertIn("1 terminal plan(s) skipped", out)
        # Idempotent: a second run adds nothing.
        _c, out2, _e = self.run_cli("ipd", "sync", "--all", "--apply")
        self.assertIn("backfilled Id in 0 plan(s); 2 already had one", out2)

    def test_explicit_paths_and_unanchored_plan_reported(self) -> None:
        bad = self.write_plan("# IPD: c\n\nno metadata\n", "20260701-0001-01-c.ipd.md")
        code, out, _err = self.run_cli("ipd", "sync", str(self.a), str(bad), "--apply")
        self.assertEqual(code, 1)
        self.assertEqual(len(self._ids(self.a)), 1)
        self.assertEqual(self._ids(self.b), [])
        self.assertIn("cannot place Id", out)


class MigrationSkipsTerminalPlansTests(_Repo):
    def test_executed_plan_bytes_untouched_by_migration(self) -> None:
        legacy = self.root / ".agents/plans"
        (legacy / "pending").mkdir(parents=True)
        (legacy / "executed").mkdir(parents=True)
        done_text = "# IPD: old\n\n- Status: executed\n\n## Goal\n"
        (legacy / "executed/20260101-0001-01-old.md").write_text(
            done_text, encoding="utf-8"
        )
        (legacy / "pending/20260701-0001-01-p.md").write_text(
            LEGACY_PLAN.replace("- Id: lg0001\n", ""), encoding="utf-8"
        )
        self.commit("seed legacy")
        code, out, err = self.run_cli("migrate-layout", "--yes")
        self.assertEqual(code, 0, out + err)
        moved_done = self.root / ".aw/records/plans/executed/20260101-0001-01-old.md"
        self.assertEqual(moved_done.read_text(encoding="utf-8"), done_text)
        moved_pending = self.root / ".aw/records/plans/pending/20260701-0001-01-p.md"
        self.assertIn("- Id: ", moved_pending.read_text(encoding="utf-8"))

    def test_pre_existing_pending_plan_gets_id_backfilled(self) -> None:
        pending_dir = self.root / ".aw/records/plans/pending"
        pending_dir.mkdir(parents=True)
        p = pending_dir / "20260701-0001-01-already-here.md"
        p.write_text(LEGACY_PLAN.replace("- Id: lg0001\n", ""), encoding="utf-8")
        (self.root / ".agents").mkdir(parents=True)
        (self.root / ".agents/README.md").write_text("dummy", encoding="utf-8")
        self.commit("seed existing")
        code, out, err = self.run_cli("migrate-layout", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertIn("- Id: ", p.read_text(encoding="utf-8"))

    def test_pre_existing_aw_gitignore_updated_with_index_ignores(self) -> None:
        aw_dir = self.root / ".aw"
        aw_dir.mkdir(parents=True)
        gi = aw_dir / ".gitignore"
        gi.write_text("records/*/untracked/\n", encoding="utf-8")
        (self.root / ".agents").mkdir(parents=True)
        (self.root / ".agents/README.md").write_text("dummy", encoding="utf-8")
        self.commit("seed gitignore")
        code, out, err = self.run_cli("migrate-layout", "--yes")
        self.assertEqual(code, 0, out + err)
        text = gi.read_text(encoding="utf-8")
        self.assertIn("records/plans/INDEX.json", text)
        self.assertIn("records/plans/INDEX.md", text)


class BareSyncRefusalTests(_Repo):
    def test_bare_sync_refuses_with_agent_record(self) -> None:
        code, out, _err = self.run_cli("ipd", "sync", "--agent")
        self.assertEqual(code, 2)
        rec = json.loads(out.strip().splitlines()[-1])
        self.assertEqual(rec["cmd"], "ipd sync")
        self.assertEqual(rec["exit"], 2)
