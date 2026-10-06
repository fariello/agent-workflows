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

from agent_workflows import check_engine as ce
from agent_workflows import ipd_lifecycle as il
from agent_workflows import selectors


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _fixture_plan_text(id6: str, history_text: str, status: str = "approved") -> str:
    approval = (
        "- Approval: 2026-09-03, recorded via aw ipd set\n"
        if status == "approved"
        else ""
    )
    return (
        f"# IPD: Fixture {id6}\n\n"
        "- Date: 2026-09-01\n"
        "- Kind: child\n"
        "- Concern: history order fixture\n"
        "- Scope: history order fixture\n"
        "- Scope-Paths: agent_workflows/ipd_lifecycle.py\n"
        "- Item-Dependencies: none\n"
        f"- Status: {status}\n"
        "- Set: demo\n"
        "- Order: 1\n"
        "- Highest E allocated: 01\n"
        "- Priority: medium\n"
        "- Work-Kind: chore\n"
        "- Author: fixture\n"
        f"- Id: {id6}\n"
        f"{approval}"
        "\n## Workflow history\n"
        f"{history_text}\n"
        "\n## Goal\n\nFixture goal.\n"
        "\n## Detailed Implementation Checklist (TODO)\n\n"
        "- [ ] E-01 execute.\n"
        "  - Depends on: none\n"
        "  - Expected outcome: done\n"
        "  - Execution state: pending\n"
        "\n## Project conventions discovered (Step 0)\n\n- none\n"
        "\n## Findings\n\n- none\n"
        "\n## Proposed changes (ordered, validatable)\n\n- none\n"
        "\n## Deferred / out of scope (with reason)\n\n- none\n"
        "\n## Scope check\n\n- none\n"
        "\n## Required tests / validation\n\n- none\n"
        "\n## Spec / documentation sync\n\n- none\n"
        "\n## Open questions\n\n- none\n"
        "\n## Validation and cross-check (verify before reporting done)\n\n"
        "- [ ] V-01 validates E-01\n"
        "  - Required evidence: none\n"
        "  - Observed evidence: none\n"
        "  - Result: pending\n"
        "\n## Approval and execution gate\n\n- none\n"
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
            id6 = selectors.read_front_matter_id(text)
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

        if hasattr(il, "_plan_status_event_groups"):
            groups = il._plan_status_event_groups(content)
            self.assertEqual(
                groups,
                [
                    ("2026-09-01", [("draft", "agent")], True),
                    ("2026-09-02", [("reviewed", "agent")], True),
                    ("2026-09-03", [("approved", "agent")], True),
                ],
            )

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

        if hasattr(il, "_plan_status_event_groups"):
            groups = il._plan_status_event_groups(content)
            self.assertEqual(
                groups,
                [
                    ("2026-09-01", [("draft", "agent")], True),
                    ("2026-09-02", [("reviewed", "agent")], True),
                    ("2026-09-03", [("approved", "agent")], True),
                ],
            )

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

        if hasattr(il, "_plan_status_event_groups"):
            groups = il._plan_status_event_groups(content)
            self.assertEqual(
                groups,
                [
                    ("2026-08-30", [("draft", "agent")], True),
                    ("2026-09-01", [("to-review", "agent")], True),
                    ("2026-09-02", [("reviewed", "agent")], True),
                    ("2026-09-03", [("approved", "agent")], True),
                ],
            )

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

        if hasattr(il, "_plan_status_event_groups"):
            groups = il._plan_status_event_groups(content)
            self.assertEqual(
                groups,
                [
                    ("2026-09-01", [("reviewed", "agent")], True),
                    ("2026-09-02", [("executed", "aw ipd finalize")], True),
                    ("2026-09-03", [("draft", "agent")], True),
                ],
            )

        drift = self._run_check_on_plan(
            "20260901-fix01d-01-fix01d-cross-day.ipd.md", content
        )
        self.assertEqual(len(drift), 1)
        self.assertIn("'executed' -> 'draft'", drift[0].detail)

    def test_fixture_e_discriminating_single_date_tie(self):
        """(e) Single-date draft above approved in one block -> 0 findings (unordered)."""
        history = "- 2026-09-01 draft (agent): ok\n" "- 2026-09-01 approved (agent): ok"
        content = _fixture_plan_text("fix01e", history, status="approved")

        if hasattr(il, "_plan_status_event_groups"):
            groups = il._plan_status_event_groups(content)
            self.assertEqual(
                groups,
                [
                    ("2026-09-01", [("draft", "agent"), ("approved", "agent")], False),
                ],
            )

        drift = self._run_check_on_plan(
            "20260901-fix01e-01-fix01e-single-date.ipd.md", content
        )
        self.assertEqual(drift, [])


if __name__ == "__main__":
    unittest.main()
