"""Behavioral tests for freshness pruning, bulk field queries, meta-field parsing, and scan_once invalidation."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from agent_workflows import (
    artifact_core,
    artifact_meta,
    check_engine,
    ipd_lint,
    project_context,
    review_findings,
    selectors,
    status_set,
)


def _write_plan(
    repo: Path,
    *,
    filename: str,
    id6: str,
    status: str = "approved",
    deps: str = "none",
    from_backlog: str | None = None,
) -> Path:
    from tests.record_builder import RecordBuilder

    p = repo / ".aw" / "records" / "plans" / "pending" / filename
    p.parent.mkdir(parents=True, exist_ok=True)
    extra: dict[str, object] = {}
    if from_backlog:
        extra["from_backlog"] = from_backlog
    text = str(
        RecordBuilder().plan(
            id6=id6,
            title=f"Plan {id6}",
            set="demo",
            order=1,
            status=status,
            when="2026-11-19",
            item_dependencies=deps,
            body=(
                "## Execution checklist\n"
                "- [ ] E-01: Do work.\n\n"
                "## Validation checklist\n"
                "- [ ] V-01: Verify work."
            ),
            text_only=True,
            **extra,
        )
    )
    p.write_text(text, encoding="utf-8")
    return p


class FreshnessPruningAndBulkQueryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name).resolve()
        (self.repo / ".git").mkdir(parents=True, exist_ok=True)
        (self.repo / ".aw" / "records").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_freshness_prunes_runs_and_comms_but_still_detects_same_size_same_mtime_edits(
        self,
    ) -> None:
        plan = _write_plan(
            self.repo,
            filename="20261119-demo-01-aaa111-sample.ipd.md",
            id6="aaa111",
            status="approved",
        )
        # Drop non-record markdown files under runs/ and comms/ (spec 4sd62s N4).
        run_md = (
            self.repo
            / ".aw"
            / "records"
            / "runs"
            / "run-20261119T000000Z-1"
            / "execution-report.md"
        )
        run_md.parent.mkdir(parents=True, exist_ok=True)
        run_md.write_text("# Report\n\n- Id: rrr999\n", encoding="utf-8")

        comms_md = self.repo / ".aw" / "records" / "comms" / "inbox" / "note.md"
        comms_md.parent.mkdir(parents=True, exist_ok=True)
        comms_md.write_text("# Note\n", encoding="utf-8")

        ctx = project_context.resolve_project_context(target_repo=str(self.repo))
        res = artifact_meta.query(type="ipd", project_context=ctx, include_fields=True)
        self.assertEqual([s.id6 for s in res.rows], ["aaa111"])

        # Verify runs/ and comms/ were never indexed into the files table.
        db_path = Path(ctx.logical_roots["state"]) / "index.db"
        conn = sqlite3.connect(str(db_path))
        try:
            paths = [r[0] for r in conn.execute("SELECT path FROM files").fetchall()]
        finally:
            conn.close()
        self.assertFalse(any(p.startswith("runs/") for p in paths))
        self.assertFalse(any(p.startswith("comms/") for p in paths))

        # AC-26: same-size, same-mtime byte replacement on a real record MUST still be detected.
        st_before = plan.stat()
        old_text = plan.read_text(encoding="utf-8")
        new_text = old_text.replace("- Status: approved", "- Status: reviewed")
        self.assertEqual(len(old_text.encode("utf-8")), len(new_text.encode("utf-8")))
        plan.write_text(new_text, encoding="utf-8")
        os.utime(plan, ns=(st_before.st_atime_ns, st_before.st_mtime_ns))

        res_after = artifact_meta.query(type="ipd", project_context=ctx)
        self.assertEqual(res_after.rows[0].status, "reviewed")

    def test_query_include_fields_matches_individual_read(self) -> None:
        _write_plan(
            self.repo,
            filename="20261119-demo-01-bbb111-first.ipd.md",
            id6="bbb111",
            deps="none",
            from_backlog="bk1234",
        )
        _write_plan(
            self.repo,
            filename="20261119-demo-02-bbb222-second.ipd.md",
            id6="bbb222",
            deps="executed:bbb111",
        )
        ctx = project_context.resolve_project_context(target_repo=str(self.repo))
        bulk = artifact_meta.query(type="ipd", project_context=ctx, include_fields=True)
        self.assertEqual(len(bulk.rows), 2)
        for st in bulk.rows:
            single = artifact_meta.read(st.id6, project_context=ctx)
            self.assertEqual(st.fields, single.fields)


class ScanOnceCacheInvalidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name).resolve()
        (self.repo / ".git").mkdir(parents=True, exist_ok=True)
        (self.repo / ".aw" / "records").mkdir(parents=True, exist_ok=True)
        (self.repo / ".aw" / "config").mkdir(parents=True, exist_ok=True)
        (self.repo / ".aw" / "config" / "project.json").write_text(
            '{"findings_gate_threshold": "high"}\n', encoding="utf-8"
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_scan_once_caches_and_drop_scan_invalidates_reviews_and_state(self) -> None:
        plan_a = _write_plan(
            self.repo,
            filename="20261119-demo-01-ccc111-base.ipd.md",
            id6="ccc111",
            status="approved",
            deps="none",
        )
        plan_b = _write_plan(
            self.repo,
            filename="20261119-demo-02-ccc222-child.ipd.md",
            id6="ccc222",
            status="approved",
            deps="executed:ccc111",
        )
        review = (
            self.repo
            / ".aw"
            / "records"
            / "reviews"
            / "20261119-demo-01-rev111-base.review.md"
        )
        review.parent.mkdir(parents=True, exist_ok=True)
        review.write_text(
            review_findings.render_review(
                subject_id="ccc111",
                subject_type="ipd",
                reviewed_at="2026-11-19",
                reviewer="tester",
                verdict="needs-changes",
                rounds=[
                    review_findings.Round(
                        1,
                        (
                            review_findings.Finding(
                                id="F-01",
                                severity="high",
                                scope="plan",
                                area="E-01",
                                evidence="line 1",
                                finding="Missing guard",
                                remediation_risk="low",
                                decision="open",
                                resolution="",
                            ),
                        ),
                        (),
                    )
                ],
            ),
            encoding="utf-8",
        )

        with selectors.scan_once():
            blocks = review_findings.subject_gating_blocks(self.repo, "ccc111", "high")
            self.assertEqual(len(blocks), 1)
            self.assertEqual(blocks[0].finding_id, "F-01")

            drift_b = check_engine.evaluate_ipd_dependencies(
                self.repo,
                phase="pre-execution",
                plans=[(plan_b, plan_b.read_text(encoding="utf-8"))],
            )
            self.assertTrue(
                any(d.rule == check_engine._REVIEW_DEP_BLOCKED_RULE for d in drift_b)
            )

            st_a = status_set._cached_state_for_path(plan_a, self.repo)
            self.assertIsNotNone(st_a)
            assert st_a is not None
            self.assertEqual(st_a.status, "approved")

            # Fix the review finding on disk and call drop_scan(): the open scope MUST see the update.
            review.write_text(
                review_findings.render_review(
                    subject_id="ccc111",
                    subject_type="ipd",
                    reviewed_at="2026-11-19",
                    reviewer="tester",
                    verdict="approved",
                    rounds=[
                        review_findings.Round(
                            1,
                            (
                                review_findings.Finding(
                                    id="F-01",
                                    severity="high",
                                    scope="plan",
                                    area="E-01",
                                    evidence="line 1",
                                    finding="Missing guard",
                                    remediation_risk="low",
                                    decision="fixed",
                                    resolution="fixed in test",
                                ),
                            ),
                            (),
                        )
                    ],
                ),
                encoding="utf-8",
            )
            selectors.drop_scan()

            blocks_after = review_findings.subject_gating_blocks(
                self.repo, "ccc111", "high"
            )
            self.assertEqual(blocks_after, ())

            drift_b_after = check_engine.evaluate_ipd_dependencies(
                self.repo,
                phase="pre-execution",
                plans=[(plan_b, plan_b.read_text(encoding="utf-8"))],
            )
            self.assertFalse(
                any(
                    d.rule == check_engine._REVIEW_DEP_BLOCKED_RULE
                    for d in drift_b_after
                )
            )


class ParseMetaFieldsAndIterScanFilesTests(unittest.TestCase):
    def test_parse_meta_fields_matches_full_parse_across_fences_and_yaml(self) -> None:
        samples = [
            (
                "---\nfoo: bar\n---\n"
                "# Title\n\n"
                "- Id: ddd111\n"
                "- Status: approved\n"
                "- Item-Dependencies: executed:aaa111\n"
                "```markdown\n"
                "- Status: fake\n"
                "## Fake H2\n"
                "```\n"
                "> - Status: quoted\n"
                "- From-Backlog: bkl999\n\n"
                "## Execution checklist\n"
                "- Status: body-line\n"
            ),
            "# Only H1\n- Id: eee222\n- Item-Dependencies: none\n",
            "",
        ]
        for text in samples:
            self.assertEqual(
                ipd_lint.parse_meta_fields(text), ipd_lint.parse(text).meta_fields
            )

    def test_iter_scan_files_prunes_ignored_runs_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp).resolve()
            (repo / ".git").mkdir()
            (repo / ".gitignore").write_text(".aw/records/runs/\n", encoding="utf-8")
            kept = _write_plan(
                repo,
                filename="20261119-demo-01-fff111-kept.ipd.md",
                id6="fff111",
            )
            ignored = (
                repo / ".aw" / "records" / "runs" / "run-1" / "execution-report.md"
            )
            ignored.parent.mkdir(parents=True, exist_ok=True)
            ignored.write_text("# Ignored\n", encoding="utf-8")

            found = artifact_core.iter_scan_files(repo)
            self.assertIn(kept, found)
            self.assertNotIn(ignored, found)


if __name__ == "__main__":
    unittest.main()
