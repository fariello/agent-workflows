"""Tests for workflow history ordering and lifecycle transition validation (IPD 63h054).

Covers:
1. DerivationIsUnchangedTests: Whole-tree anti-regression guard verifying derive_plan_status
   output matches tests/fixtures/derive_plan_status_baseline.json.
2. HistoryOrderFixtureTests: Fixtures (a)-(e) validating newest-first, oldest-first, mixed,
   cross-day backward, and single-date tie history orders through both
   _plan_status_event_groups (when available) and check_lifecycle_transitions.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import NamedTuple
import unittest

import pytest

from agent_workflows import artifact_meta
from agent_workflows import backlog
from agent_workflows import check_engine as ce
from agent_workflows import ipd_lifecycle as il
from agent_workflows import ipd_lint
from agent_workflows import releases
from agent_workflows import specs
from agent_workflows.migrations import chain as migrations_chain
from tests.record_builder import RecordBuilder


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _fixture_plan_text(id6: str, history_text: str, status: str = "approved") -> str:
    return RecordBuilder().plan(
        id6=id6,
        title=f"Fixture {id6}",
        when="2026-09-01",
        plan_role="child",
        set="demo",
        order=1,
        status=status,
        scope_paths="agent_workflows/ipd_lifecycle.py",
        item_dependencies="none",
        priority="medium",
        work_kind="chore",
        author="fixture",
        approval="2026-09-03, recorded via aw ipd set"
        if status == "approved"
        else None,
        history=[history_text],
        text_only=True,
    )


class DerivationComparisonResult(NamedTuple):
    live_by_id: dict[str, tuple[str, str | None]]
    found_ids: set[str]
    mismatches: list[str]
    duplicate_ids: dict[str, list[str]]
    missing_id_paths: list[str]


def _compare_plan_derivations(
    root: Path, baseline: dict[str, str | None]
) -> DerivationComparisonResult:
    """Compare live terminal plan derivations against an id6-keyed baseline mapping.

    Takes a repository root and an id6-keyed baseline, reads each live terminal
    plan once to extract both its declared id6 and its derived status, and
    returns the comparison data without making assertions.
    """
    live_by_id: dict[str, tuple[str, str | None]] = {}
    seen_ids: dict[str, list[str]] = {}
    missing_id_paths: list[str] = []

    for bucket in ("executed", "superseded", "not-executed"):
        bucket_dir = root / ".aw" / "records" / "plans" / bucket
        if not bucket_dir.is_dir():
            continue
        for p in sorted(bucket_dir.glob("**/*.ipd.md")):
            rel_path = p.relative_to(root).as_posix()
            text = p.read_text(encoding="utf-8")
            id6 = artifact_meta.read_text(text).loose_id
            derived = il.derive_plan_status(text)
            if not id6:
                missing_id_paths.append(rel_path)
                continue
            if id6 in seen_ids:
                seen_ids[id6].append(rel_path)
            else:
                seen_ids[id6] = [rel_path]
                live_by_id[id6] = (rel_path, derived)

    duplicate_ids = {k: v for k, v in seen_ids.items() if len(v) > 1}
    found_ids = set(baseline.keys()) & set(live_by_id.keys())

    mismatches: list[str] = []
    for id6 in sorted(found_ids):
        rel_path, derived = live_by_id[id6]
        expected = baseline[id6]
        if derived != expected:
            mismatches.append(
                f"{id6} ({rel_path}): expected {expected!r}, got {derived!r}"
            )

    return DerivationComparisonResult(
        live_by_id=live_by_id,
        found_ids=found_ids,
        mismatches=mismatches,
        duplicate_ids=duplicate_ids,
        missing_id_paths=missing_id_paths,
    )


class DerivationIsUnchangedTests(unittest.TestCase):
    """Anti-regression guard for derive_plan_status across the whole tree."""

    def test_whole_tree_derivation_is_unchanged(self):
        root = _repo_root()
        baseline_file = root / "tests" / "fixtures" / "derive_plan_status_baseline.json"
        self.assertTrue(
            baseline_file.is_file(), f"Missing baseline fixture: {baseline_file}"
        )

        with open(baseline_file, "r", encoding="utf-8") as f:
            baseline = json.load(f)

        # The size floor is deliberately absolute and is NOT the rotting kind:
        # it bounds the fixture itself, a frozen authored artifact whose entry
        # count changes only when someone edits it, ensuring the coverage
        # fraction cannot become vacuous if the fixture is truncated or emptied.
        self.assertGreaterEqual(
            len(baseline),
            700,
            f"Baseline fixture shrank to {len(baseline)} entries; expected at least 700. "
            "The fixture itself shrank and must be re-keyed from the committed file rather than re-captured.",
        )

        result = _compare_plan_derivations(root, baseline)

        self.assertEqual(
            result.duplicate_ids,
            {},
            f"Duplicate declared id6 found in live terminal plans: {result.duplicate_ids}",
        )
        self.assertEqual(
            result.missing_id_paths,
            [],
            f"Live terminal plans missing declared - Id:: {result.missing_id_paths}",
        )

        print(f"Compared {len(result.found_ids)} plans")
        coverage_threshold = 0.95 * len(baseline)
        missing_count = len(baseline) - len(result.found_ids)
        self.assertGreaterEqual(
            len(result.found_ids),
            coverage_threshold,
            f"Coverage below threshold: found {len(result.found_ids)} of {len(baseline)} "
            f"baseline entries ({missing_count} missing, required >= {coverage_threshold:.1f}). "
            "Baseline ids are missing from the live terminal tree (a plan was deleted, moved "
            "out of a terminal directory, or had its - Id: changed), NOT that derive_plan_status "
            "regressed. A legitimate mass change requires re-keying the fixture.",
        )

        self.assertEqual(
            result.mismatches,
            [],
            f"derive_plan_status changed on {len(result.mismatches)} plans:\n"
            + "\n".join(result.mismatches[:20]),
        )

    def test_derivation_comparison_invariant_to_rename_and_sharding(self):
        """Prove id6-keyed comparison is invariant to file renaming and archive sharding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmproot = Path(tmpdir)
            plans_dir = tmproot / ".aw" / "records" / "plans"
            exec_dir = plans_dir / "executed"
            super_dir = plans_dir / "superseded"
            notexec_dir = plans_dir / "not-executed"
            for d in (exec_dir, super_dir, notexec_dir):
                d.mkdir(parents=True, exist_ok=True)

            plan1_file = exec_dir / "20260901-demo-01-plan01-first-plan.ipd.md"
            plan1_history = (
                "- 2026-09-03 executed (agent): done\n"
                "- 2026-09-02 approved (agent): ok\n"
                "- 2026-09-01 draft (agent): ok"
            )
            plan1_file.write_text(
                _fixture_plan_text("plan01", plan1_history, status="executed"),
                encoding="utf-8",
            )

            plan2_file = super_dir / "20260901-demo-02-plan02-second-plan.ipd.md"
            plan2_history = (
                "- 2026-09-02 approved (agent): ok\n" "- 2026-09-01 draft (agent): ok"
            )
            plan2_file.write_text(
                _fixture_plan_text("plan02", plan2_history, status="approved"),
                encoding="utf-8",
            )

            plan3_file = notexec_dir / "20260901-demo-03-plan03-third-plan.ipd.md"
            plan3_history = "- 2026-09-01 draft (agent): ok"
            plan3_file.write_text(
                _fixture_plan_text("plan03", plan3_history, status="draft"),
                encoding="utf-8",
            )

            baseline = {
                "plan01": "executed",
                "plan02": "approved",
                "plan03": "draft",
            }

            # 1. Verify baseline matches before moves
            res0 = _compare_plan_derivations(tmproot, baseline)
            self.assertEqual(res0.found_ids, {"plan01", "plan02", "plan03"})
            self.assertEqual(res0.mismatches, [])

            # 2. Physically rename every plan file and move one into a YYYYMM/ shard
            shard_dir = exec_dir / "202609"
            shard_dir.mkdir(parents=True, exist_ok=True)
            new_plan1_file = shard_dir / "20260901-renamed-01-plan01-sharded.ipd.md"
            plan1_file.rename(new_plan1_file)

            new_plan2_file = super_dir / "20260901-renamed-02-plan02-renamed.ipd.md"
            plan2_file.rename(new_plan2_file)

            new_plan3_file = notexec_dir / "20260901-renamed-03-plan03-renamed.ipd.md"
            plan3_file.rename(new_plan3_file)

            # Assert comparison still finds every entry and reports zero mismatches
            res_after_moves = _compare_plan_derivations(tmproot, baseline)
            self.assertEqual(res_after_moves.found_ids, {"plan01", "plan02", "plan03"})
            self.assertEqual(res_after_moves.mismatches, [])
            self.assertEqual(res_after_moves.duplicate_ids, {})
            self.assertEqual(res_after_moves.missing_id_paths, [])

            # 3. Discriminating negative: mutate plan history so derived status genuinely changes
            mutated_history = "- 2026-09-04 draft (agent): reopened\n" + plan1_history
            new_plan1_file.write_text(
                _fixture_plan_text("plan01", mutated_history, status="draft"),
                encoding="utf-8",
            )

            res_negative = _compare_plan_derivations(tmproot, baseline)
            self.assertEqual(len(res_negative.mismatches), 1)
            self.assertIn("plan01", res_negative.mismatches[0])
            self.assertIn(
                "expected 'executed', got 'draft'", res_negative.mismatches[0]
            )


class HistoryOrderFixtureTests(unittest.TestCase):
    """Five fixture tests (a)-(e) for lifecycle transition checking and history grouping."""

    def _run_check_on_plan(self, filename: str, content: str):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmproot = Path(tmpdir)
            pending_dir = tmproot / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True, exist_ok=True)
            plan_file = pending_dir / filename
            plan_file.write_text(content, encoding="utf-8")
            return ce.check_lifecycle_transitions(tmproot, include_untracked=True)

    def test_fixture_a_newest_first(self):
        """(a) NEWEST-FIRST -> oldest-first draft, reviewed, approved (0 findings)."""
        history = (
            "- 2026-09-03 approved (agent): ok\n"
            "- 2026-09-02 reviewed (agent): ok\n"
            "- 2026-09-01 draft (agent): ok"
        )
        content = _fixture_plan_text("fix01a", history, status="approved")

        drift = self._run_check_on_plan(
            "20260901-fix01a-01-fix01a-newest-first.ipd.md", content
        )
        self.assertEqual(drift, [])

    def test_fixture_b_oldest_first(self):
        """(b) OLDEST-FIRST -> oldest-first draft, reviewed, approved (0 findings)."""
        history = (
            "- 2026-09-01 draft (agent): ok\n"
            "- 2026-09-02 reviewed (agent): ok\n"
            "- 2026-09-03 approved (agent): ok"
        )
        content = _fixture_plan_text("fix01b", history, status="approved")

        drift = self._run_check_on_plan(
            "20260901-fix01b-01-fix01b-oldest-first.ipd.md", content
        )
        self.assertEqual(drift, [])

    def test_fixture_c_mixed_blocks(self):
        """(c) MIXED -> draft, to-review, reviewed, approved (0 findings)."""
        history = (
            "- 2026-09-03 approved (agent): ok\n"
            "- 2026-09-02 reviewed (agent): ok\n"
            "\n"
            "- 2026-08-30 draft (agent): ok\n"
            "- 2026-09-01 to-review (agent): ok"
        )
        content = _fixture_plan_text("fix01c", history, status="approved")

        drift = self._run_check_on_plan(
            "20260901-fix01c-01-fix01c-mixed.ipd.md", content
        )
        self.assertEqual(drift, [])

    def test_fixture_d_negative_cross_day_backwards(self):
        """(d) Cross-day executed then draft -> exactly 1 finding naming 'executed' -> 'draft'."""
        history = (
            "- 2026-09-01 reviewed (agent): ok\n"
            "- 2026-09-02 executed (aw ipd finalize): ok\n"
            "- 2026-09-03 draft (agent): ok"
        )
        content = _fixture_plan_text("fix01d", history, status="draft")

        drift = self._run_check_on_plan(
            "20260901-fix01d-01-fix01d-cross-day.ipd.md", content
        )
        self.assertEqual(len(drift), 1)
        self.assertIn("'executed' -> 'draft'", drift[0].detail)

    def test_fixture_e_discriminating_single_date_tie(self):
        """(e) Single-date draft above approved in one block -> 0 findings (unordered)."""
        history = "- 2026-09-01 draft (agent): ok\n" "- 2026-09-01 approved (agent): ok"
        content = _fixture_plan_text("fix01e", history, status="approved")

        drift = self._run_check_on_plan(
            "20260901-fix01e-01-fix01e-single-date.ipd.md", content
        )
        self.assertEqual(drift, [])


@pytest.mark.core
class ArtifactMetaHistoryMigrationTests(unittest.TestCase):
    """Fast behavioral regression tests for artifact_meta history helpers and migrated readers."""

    def test_split_history_section_cases(self) -> None:
        # 1. Missing heading
        no_heading = "# Spec\n\n- Id: sp0001\n\n## Goal\nKeep things simple.\n"
        sec_missing = artifact_meta.split_history_section(no_heading)
        self.assertEqual(sec_missing[0], no_heading)
        self.assertEqual(sec_missing[1], artifact_meta.HistoryBlock([], [], ""))
        self.assertFalse(sec_missing[2])

        # 2. Empty heading
        empty_heading = "# Item\n\n- Id: bk0001\n\n## Workflow history\n\n"
        sec_empty = artifact_meta.split_history_section(empty_heading)
        self.assertEqual(sec_empty.before_heading, "# Item\n\n- Id: bk0001\n\n")
        self.assertEqual(sec_empty.block.records, [])
        self.assertTrue(sec_empty.has_heading)

        # 3. Heading with multiple spaces/tabs, records, and trailing body
        with_records = (
            "# Item\n\n- Id: bk0002\n\n"
            "##  \tWorkflow history  \n"
            "- 2026-11-24 open (tester): second\n"
            "- 2026-11-23 created (tester): first\n\n"
            "## Body\nTrailing prose.\n"
        )
        sec_records = artifact_meta.split_history_section(with_records)
        self.assertEqual(sec_records.before_heading, "# Item\n\n- Id: bk0002\n\n")
        self.assertTrue(sec_records.has_heading)
        self.assertEqual(
            sec_records.block.records,
            [
                "- 2026-11-24 open (tester): second",
                "- 2026-11-23 created (tester): first",
            ],
        )
        self.assertEqual(sec_records.block.body, "## Body\nTrailing prose.")

        # 4. Fenced heading only is ignored
        fenced_only = (
            "# Spec\n\n"
            "```markdown\n"
            "## Workflow history\n"
            "- 2026-11-01 fake (author): inside backtick fence\n"
            "```\n\n"
            "~~~markdown\n"
            "## Workflow history\n"
            "- 2026-11-02 fake (author): inside tilde fence\n"
            "~~~\n"
        )
        sec_fenced = artifact_meta.split_history_section(fenced_only)
        self.assertEqual(sec_fenced.before_heading, fenced_only)
        self.assertEqual(sec_fenced.block, artifact_meta.HistoryBlock([], [], ""))
        self.assertFalse(sec_fenced.has_heading)

        # 5. Fenced heading followed by real unfenced heading splits at the real one
        fenced_then_real = (
            "# Spec\n\n"
            "```markdown\n"
            "## Workflow history\n"
            "- 2026-11-01 fake (author): inside fence\n"
            "```\n\n"
            "## Workflow history\n"
            "- 2026-11-24 approved (author): real record\n"
        )
        sec_real = artifact_meta.split_history_section(fenced_then_real)
        self.assertTrue(sec_real.has_heading)
        self.assertIn("inside fence", sec_real.before_heading)
        self.assertEqual(
            sec_real.block.records,
            ["- 2026-11-24 approved (author): real record"],
        )

    def test_history_record_blocks_and_lifecycle_groups(self) -> None:
        text = (
            "# Plan\n\n"
            "```markdown\n"
            "## Workflow history\n"
            "- 2026-01-01 executed (fake): fenced heading ignored\n"
            "```\n\n"
            "## Workflow history\n\n"
            "- 2026-09-03 approved (agent): ok\n"
            "  indented continuation stays in block\n"
            "- 2026-09-02 reviewed (agent): ok\n"
            "\n"
            "- 2026-08-30 draft (agent): ok\n"
            "  another continuation line\n"
            "- 2026-09-01 to-review (agent): ok\n\n"
            "## Goal\n"
            "- 2026-09-04 executed (agent): not in history section\n"
        )
        blocks = artifact_meta.history_record_blocks(text)
        self.assertEqual(
            blocks,
            [
                [
                    "- 2026-09-03 approved (agent): ok",
                    "- 2026-09-02 reviewed (agent): ok",
                ],
                [
                    "- 2026-08-30 draft (agent): ok",
                    "- 2026-09-01 to-review (agent): ok",
                ],
            ],
        )

        # Verify _plan_status_event_groups produces oldest-first ordered date groups
        groups = il._plan_status_event_groups(text)
        dates = [g[0] for g in groups]
        statuses = [ev[0] for _d, evs, _ord in groups for ev in evs]
        self.assertEqual(
            dates, ["2026-08-30", "2026-09-01", "2026-09-02", "2026-09-03"]
        )
        self.assertEqual(statuses, ["draft", "to-review", "reviewed", "approved"])

        # End-to-end check_lifecycle_transitions with continuation lines in mixed blocks
        history_with_cont = (
            "- 2026-09-03 approved (agent): ok\n"
            "  indented continuation detail\n"
            "- 2026-09-02 reviewed (agent): ok\n"
            "\n"
            "- 2026-08-30 draft (agent): ok\n"
            "- 2026-09-01 to-review (agent): ok"
        )
        plan_text = _fixture_plan_text("mig01a", history_with_cont, status="approved")
        with tempfile.TemporaryDirectory() as tmpdir:
            tmproot = Path(tmpdir)
            pending_dir = tmproot / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True, exist_ok=True)
            (pending_dir / "20260901-demo-01-mig01a-cont.ipd.md").write_text(
                plan_text, encoding="utf-8"
            )
            self.assertEqual(
                ce.check_lifecycle_transitions(tmproot, include_untracked=True), []
            )

    def test_history_section_bullets_ipd_lint_and_matching_history(self) -> None:
        text = (
            "# IPD: Sample\n"  # line 1
            "\n"  # line 2
            "```markdown\n"  # line 3
            "## Workflow history\n"  # line 4
            "- 2026-01-01 approved (aw set): fenced before real\n"  # line 5
            "```\n"  # line 6
            "\n"  # line 7
            "## Workflow history\n"  # line 8
            "- 2026-11-24 approved (aw ipd set): status set to approved\n"  # line 9
            "```text\n"  # line 10
            "- 2026-11-20 fake (aw set): fenced inside history\n"  # line 11
            "## Fake heading inside fence\n"  # line 12
            "```\n"  # line 13
            "  - nested bullet\n"  # line 14
            "- 2026-11-23 draft (author): created\n"  # line 15
            "\n"  # line 16
            "## Goal\n"  # line 17
            "- goal bullet outside history\n"  # line 18
        )
        lines = artifact_meta.history_section_lines(text)
        self.assertEqual(
            lines,
            [
                (9, "- 2026-11-24 approved (aw ipd set): status set to approved"),
                (14, "  - nested bullet"),
                (15, "- 2026-11-23 draft (author): created"),
            ],
        )

        doc = ipd_lint.parse(text)
        self.assertEqual(doc.history_lines, lines)
        self.assertTrue(ce._has_matching_history_line(text, "approved"))
        self.assertFalse(ce._has_matching_history_line(text, "executed"))

    def test_backlog_validate_item_distinct_history_empty_details(self) -> None:
        p = Path(".aw/records/backlog/open/20261124-demo-01-bk9001-sample.backlog.md")
        base_fields = dict(
            id6="bk9001",
            status="open",
            set="demo",
            priority="high",
            work_kind="feature",
            summary="Sample item",
            text_only=True,
        )
        ok_text = RecordBuilder().backlog(
            **base_fields,
            history=["- 2026-11-24 created (aw backlog): initial"],
            body="## Detail\nProse.",
        )
        self.assertEqual(
            [
                d
                for d in backlog.validate_item(p, ok_text)
                if d.rule == "backlog.history-empty"
            ],
            [],
        )

        empty_heading_text = RecordBuilder().backlog(
            **base_fields,
            history=[],
            body="  - 2026-11-24 created (aw backlog): indented only",
        )
        drifts_empty = [
            d
            for d in backlog.validate_item(p, empty_heading_text)
            if d.rule == "backlog.history-empty"
        ]
        self.assertEqual(len(drifts_empty), 1)
        self.assertIn("heading present but no column-zero", drifts_empty[0].detail)

        no_heading_text = (
            RecordBuilder()
            .backlog(**base_fields, history=[])
            .split("\n\n## Workflow history")[0]
            + "\n\n```markdown\n## Workflow history\n- 2026-11-24 created (aw backlog): fenced\n```\n"
        )
        drifts_missing = [
            d
            for d in backlog.validate_item(p, no_heading_text)
            if d.rule == "backlog.history-empty"
        ]
        self.assertEqual(len(drifts_missing), 1)
        self.assertIn("no ## Workflow history heading", drifts_missing[0].detail)
        self.assertNotEqual(drifts_missing[0].detail, drifts_empty[0].detail)

    def test_releases_parse_release_strips_bullet_prefix(self) -> None:
        rel_text = (
            "# Release: v1.2.3\n\n"
            "- Id: rel123\n"
            "- Version: v1.2.3\n"
            "- Status: planned\n"
            "- Summary: Release summary\n\n"
            "## Workflow history\n"
            "- 2026-11-24 planned (aw releases): created\n"
            "  - nested detail\n"
            "```markdown\n"
            "- 2026-11-20 fenced (aw releases): ignored\n"
            "```\n\n"
            "## Notes\n"
            "- trailing note bullet\n"
        )
        rec = releases.parse_release(
            Path("20261124-rel-01-rel123-v1-2-3.release.md"), rel_text
        )
        self.assertEqual(
            rec.history,
            ("2026-11-24 planned (aw releases): created", "nested detail"),
        )

    def test_specs_validate_spec_history_presence(self) -> None:
        p = Path(".aw/records/specs/20261124-sp9001-01-sp9001-demo.spec.md")
        good = RecordBuilder().spec(
            id6="sp9001",
            title="Demo spec",
            when="2026-11-24",
            status="draft",
            history=["- 2026-11-24 draft (aw specs): created"],
            text_only=True,
        )
        self.assertEqual(
            [
                d
                for d in specs.validate_spec(p, good)
                if d.rule == "attention.history-missing"
            ],
            [],
        )

        empty_hist = RecordBuilder().spec(
            id6="sp9001",
            title="Demo spec",
            when="2026-11-24",
            status="draft",
            history=[],
            text_only=True,
        )
        drifts = [
            d
            for d in specs.validate_spec(p, empty_hist)
            if d.rule == "attention.history-missing"
        ]
        self.assertEqual(len(drifts), 1)

    def test_check_spec_test_citations_normative_vs_history_exemption(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "tests").mkdir(parents=True, exist_ok=True)
            spec_path = (
                repo
                / ".aw"
                / "records"
                / "specs"
                / "20261124-sp9002-01-sp9002-cite.spec.md"
            )

            # Nonexistent citation only in Workflow history is exempt
            exempt_text = (
                "# Spec\n\n- Id: sp9002\n- Status: draft\n\n"
                "## Goal\nNo test citations here.\n\n"
                "## Workflow history\n"
                "- 2026-11-24 draft (author): verified tests/test_deleted_history_only.py\n"
            )
            self.assertEqual(
                ce.check_spec_test_citations_for_text(repo, spec_path, exempt_text), []
            )

            # Nonexistent citation in normative body after a fenced heading STILL fires
            fenced_then_body = (
                "# Spec\n\n- Id: sp9002\n- Status: draft\n\n"
                "```markdown\n"
                "## Workflow history\n"
                "- 2026-11-24 note (author): example\n"
                "```\n\n"
                "## Acceptance\nGuarded by tests/test_missing_normative_wgn3bl.py.\n\n"
                "## Workflow history\n"
                "- 2026-11-24 draft (author): created\n"
            )
            drifts = ce.check_spec_test_citations_for_text(
                repo, spec_path, fenced_then_body
            )
            self.assertEqual(len(drifts), 1)
            self.assertEqual(drifts[0].rule, "check.test-citation-dangling")
            self.assertIn("tests/test_missing_normative_wgn3bl.py", drifts[0].detail)

    def test_migrations_chain_repo_has_legacy_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            plans_dir = repo / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True, exist_ok=True)
            plan_path = plans_dir / "20261124-demo-01-mig901-v2.ipd.md"

            # Valid v2 mirror whose only Workflow history heading is inside a fence -> NOT legacy
            plan_path.write_text(
                "---\nid: mig901\nstatus: draft\n---\n\n"
                "# Plan\n\n"
                "```markdown\n"
                "## Workflow history\n"
                "- 2026-11-24 draft (author): fenced example\n"
                "```\n",
                encoding="utf-8",
            )
            self.assertFalse(migrations_chain.repo_has_legacy_records(repo))

            # Valid v2 mirror that still carries an unfenced Workflow history heading -> legacy
            plan_path.write_text(
                "---\nid: mig901\nstatus: draft\n---\n\n"
                "# Plan\n\n"
                "## Workflow history\n"
                "- 2026-11-24 draft (author): legacy inline section\n",
                encoding="utf-8",
            )
            self.assertTrue(migrations_chain.repo_has_legacy_records(repo))


if __name__ == "__main__":
    unittest.main()
