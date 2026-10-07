"""Tests for gate-ref resolution and drift sweeps (check.gate-ref-dangling, check.gate-ref-discharged).

Covers (E-05):
Case 1: resolve_gate_ref resolves an id6 to its artifact and a repo-relative path to that path,
        and reports unresolved otherwise.
Case 2: An #anchor suffix does not defeat the path route.
Case 3: A dangling artifact ref yields exactly one check.gate-ref-dangling at error.
Case 4: A dangling todo ref yields exactly one check.gate-ref-dangling at error.
Case 5: A resolvable-and-live ref yields NO finding from either rule.
Case 6: A malformed ref yields none from either rule (no double reporting).
Case 7: A decision ref yields none from EITHER new rule (sole ownership in check.decision-ref-dangling).
Case 8: A gate whose target is executed yields exactly one check.gate-ref-discharged (adgtqb shape).
Case 9: A gate whose target is a parked backlog item yields exactly one check.gate-ref-discharged
        (deferred specs shape).
Case 10: A target whose (record_type, status) raises in class_of yields NO discharged finding.
Case 11: A path-route target yields NO discharged finding (paths carry no status).
Case 12: THE MANAGED-TARGET-REPO CASE: foreign TODO namespace (T-12) and empty index yield unknown
         and NO finding from either rule.
Case 13: Falsifiable negatives asserting rule id and severity for both rules.
Case 14: A todo ref of ../-escaping shape pointing at an outside file does NOT resolve by path route.
Case 15: A gate on a non-live carrier (open backlog item, non-deferred spec) yields nothing.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine


def _create_backlog_item(
    root: Path,
    status: str,
    id6: str,
    *,
    gate_kind: str | None = None,
    gate_ref: str | None = None,
) -> Path:
    item_dir = root / ".aw" / "records" / "backlog" / status
    item_dir.mkdir(parents=True, exist_ok=True)
    file_path = item_dir / f"20261001-test01-01-{id6}-item.backlog.md"
    gate_lines = ""
    if gate_kind:
        gate_lines += f"- Gate-Kind: {gate_kind}\n"
    if gate_ref:
        gate_lines += f"- Gate-Ref: {gate_ref}\n"
    content = (
        f"- Id: {id6}\n"
        f"- Status: {status}\n"
        "- Set: test01\n"
        "- Priority: low\n"
        "- Work-Kind: chore\n"
        f"- Summary: test item {id6}\n"
        f"{gate_lines}\n"
        "## Workflow history\n"
        "- 2026-10-01 created (test): created\n\n"
        "Prose\n"
    )
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _create_spec(
    root: Path,
    status: str,
    id6: str,
    *,
    gate_kind: str | None = None,
    gate_ref: str | None = None,
) -> Path:
    spec_dir = root / ".aw" / "records" / "specs" / status
    spec_dir.mkdir(parents=True, exist_ok=True)
    file_path = spec_dir / f"20261001-test01-01-{id6}-spec.spec.md"
    gate_lines = ""
    if gate_kind:
        gate_lines += f"- Gate-Kind: {gate_kind}\n"
    if gate_ref:
        gate_lines += f"- Gate-Ref: {gate_ref}\n"
    content = (
        f"# Spec: Test {id6}\n\n"
        f"- Id: {id6}\n"
        f"- Status: {status}\n"
        f"{gate_lines}\n"
        "## Workflow history\n"
        f"- 2026-10-01 {status} (test): {status}\n\n"
        "Prose\n"
    )
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _create_plan(
    root: Path,
    status_dir: str,
    id6: str,
    *,
    plan_status: str | None = None,
) -> Path:
    if plan_status is None:
        plan_status = status_dir
    plan_dir = root / ".aw" / "records" / "plans" / status_dir
    plan_dir.mkdir(parents=True, exist_ok=True)
    file_path = plan_dir / f"20261001-test01-01-{id6}-plan.ipd.md"
    content = (
        f"# IPD: Test {id6}\n\n"
        f"- Id: {id6}\n"
        f"- Status: {plan_status}\n"
        "- Set: test01\n"
        "- Order: 1\n\n"
        "## Workflow history\n"
        f"- 2026-10-01 {status_dir} (test): done\n\n"
        "Prose\n"
    )
    file_path.write_text(content, encoding="utf-8")
    return file_path


class GateRefResolutionTests(unittest.TestCase):
    def test_01_helper_resolution_routes(self):
        """Case 1: resolve_gate_ref resolves an id6 to its artifact and a repo-relative path,
        and reports unresolved otherwise."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan_path = _create_plan(root, "executed", "bbbbbb")
            doc_file = root / "docs" / "guide.md"
            doc_file.parent.mkdir(parents=True)
            doc_file.write_text("# Guide\n", encoding="utf-8")

            index = check_engine.build_dependency_index(root)

            # Id6 route
            res_id6 = check_engine.resolve_gate_ref(
                root, "artifact", "bbbbbb", index=index
            )
            self.assertEqual(res_id6.verdict, "resolved")
            self.assertEqual(res_id6.route, "id6")
            self.assertEqual(res_id6.record_type, "plans")
            self.assertEqual(res_id6.status, "executed")
            self.assertEqual(res_id6.path, str(plan_path))

            # Path route
            res_path = check_engine.resolve_gate_ref(
                root, "artifact", "docs/guide.md", index=index
            )
            self.assertEqual(res_path.verdict, "resolved")
            self.assertEqual(res_path.route, "path")
            self.assertEqual(res_path.path, "docs/guide.md")

            # Nonexistent path
            res_unres = check_engine.resolve_gate_ref(
                root, "artifact", "nosuchfile.md", index=index
            )
            self.assertEqual(res_unres.verdict, "unresolved")

            # Nonexistent id6
            res_unres_id6 = check_engine.resolve_gate_ref(
                root, "artifact", "zzzzzz", index=index
            )
            self.assertEqual(res_unres_id6.verdict, "unresolved")

    def test_02_path_route_anchor_suffix(self):
        """Case 2: An #anchor suffix does not defeat the path route."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            doc_file = root / "README.md"
            doc_file.write_text("# Readme\n", encoding="utf-8")
            index = check_engine.build_dependency_index(root)

            res = check_engine.resolve_gate_ref(
                root, "artifact", "README.md#installation", index=index
            )
            self.assertEqual(res.verdict, "resolved")
            self.assertEqual(res.route, "path")
            self.assertEqual(res.path, "README.md")

    def test_03_dangling_artifact_ref_reports_error(self):
        """Case 3: A dangling artifact ref yields exactly one check.gate-ref-dangling at error."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _create_backlog_item(
                root,
                "blocked",
                "aaaaaa",
                gate_kind="artifact",
                gate_ref="nonexistent/doc.md",
            )

            findings = check_engine.check_gate_ref_dangling(root)
            self.assertEqual(len(findings), 1)
            f = findings[0]
            self.assertEqual(f.rule, "check.gate-ref-dangling")
            self.assertEqual(f.severity, "error")
            self.assertIn("nonexistent/doc.md", f.detail)

    def test_04_dangling_todo_ref_reports_error(self):
        """Case 4: A dangling todo ref yields exactly one check.gate-ref-dangling at error."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Create a carrier spec pointing at a non-existent id6 'zzzzzz'
            _create_spec(
                root, "deferred", "cccccc", gate_kind="todo", gate_ref="zzzzzz"
            )

            findings = check_engine.check_gate_ref_dangling(root)
            self.assertEqual(len(findings), 1)
            f = findings[0]
            self.assertEqual(f.rule, "check.gate-ref-dangling")
            self.assertEqual(f.severity, "error")
            self.assertIn("zzzzzz", f.detail)

    def test_05_resolvable_and_live_ref_yields_no_finding(self):
        """Case 5: A resolvable-and-live ref yields NO finding from either rule."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Target is an open backlog item (class_of -> 'ready')
            _create_backlog_item(root, "open", "target")
            # Carrier is a blocked backlog item pointing at the open item
            _create_backlog_item(
                root, "blocked", "gated1", gate_kind="todo", gate_ref="target"
            )

            dangling = check_engine.check_gate_ref_dangling(root)
            discharged = check_engine.check_gate_ref_discharged(root)
            self.assertEqual(dangling, [])
            self.assertEqual(discharged, [])

    def test_06_malformed_ref_skipped(self):
        """Case 6: A malformed ref yields none from either rule, pinning no-double-report."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Ref containing whitespace is invalid for validate_gate_ref
            _create_backlog_item(
                root,
                "blocked",
                "aaaaaa",
                gate_kind="artifact",
                gate_ref="invalid ref with spaces",
            )

            dangling = check_engine.check_gate_ref_dangling(root)
            discharged = check_engine.check_gate_ref_discharged(root)
            self.assertEqual(dangling, [])
            self.assertEqual(discharged, [])

    def test_07_decision_ref_skipped_by_new_rules(self):
        """Case 7: A decision ref yields none from EITHER new rule (owned by check.decision-ref-dangling)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _create_backlog_item(
                root, "blocked", "aaaaaa", gate_kind="decision", gate_ref="D999"
            )

            dangling = check_engine.check_gate_ref_dangling(root)
            discharged = check_engine.check_gate_ref_discharged(root)
            self.assertEqual(dangling, [])
            self.assertEqual(discharged, [])

    def test_08_executed_target_reports_discharged(self):
        """Case 8: A gate whose target is executed yields exactly one check.gate-ref-discharged (adgtqb shape)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _create_plan(root, "executed", "yvvf98")
            _create_backlog_item(
                root, "blocked", "adgtqb", gate_kind="artifact", gate_ref="yvvf98"
            )

            dangling = check_engine.check_gate_ref_dangling(root)
            discharged = check_engine.check_gate_ref_discharged(root)
            self.assertEqual(dangling, [])
            self.assertEqual(len(discharged), 1)
            f = discharged[0]
            self.assertEqual(f.rule, "check.gate-ref-discharged")
            self.assertEqual(f.severity, "warning")
            self.assertIn("yvvf98", f.detail)
            self.assertIn("executed", f.detail)
            self.assertIn("done", f.detail)

    def test_09_parked_target_reports_discharged(self):
        """Case 9: A gate whose target is a parked backlog item yields exactly one check.gate-ref-discharged
        (deferred specs shape)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _create_backlog_item(root, "parked", "ju93oc")
            _create_spec(
                root, "deferred", "spec01", gate_kind="todo", gate_ref="ju93oc"
            )

            dangling = check_engine.check_gate_ref_dangling(root)
            discharged = check_engine.check_gate_ref_discharged(root)
            self.assertEqual(dangling, [])
            self.assertEqual(len(discharged), 1)
            f = discharged[0]
            self.assertEqual(f.rule, "check.gate-ref-discharged")
            self.assertEqual(f.severity, "warning")
            self.assertIn("ju93oc", f.detail)
            self.assertIn("parked", f.detail)

    def test_10_unmappable_target_status_yields_no_discharged(self):
        """Case 10: A target whose (record_type, status) raises in class_of yields NO discharged finding."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Create a fake index where target has an unmappable status
            target_id = "unmapp"
            fake_index = check_engine._DepIndex(
                owners={target_id: [("plans", "PENDING_UNKNOWN", "/path/to/fake")]}
            )
            _create_backlog_item(
                root, "blocked", "aaaaaa", gate_kind="artifact", gate_ref=target_id
            )

            discharged = check_engine.check_gate_ref_discharged(root, index=fake_index)
            self.assertEqual(discharged, [])

    def test_11_path_route_target_yields_no_discharged(self):
        """Case 11: A path-route target yields NO discharged finding (paths carry no status)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            doc_file = root / "NOTES.md"
            doc_file.write_text("# Notes\n", encoding="utf-8")
            _create_backlog_item(
                root, "blocked", "aaaaaa", gate_kind="artifact", gate_ref="NOTES.md"
            )

            dangling = check_engine.check_gate_ref_dangling(root)
            discharged = check_engine.check_gate_ref_discharged(root)
            self.assertEqual(dangling, [])
            self.assertEqual(discharged, [])

    def test_12_managed_target_repo_cannot_judge(self):
        """Case 12: THE MANAGED-TARGET-REPO CASE: foreign TODO namespace (T-12) and empty index yield unknown
        and NO finding from either rule."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Part 1: Foreign TODO namespace (T-12)
            _create_backlog_item(
                root, "blocked", "aaaaaa", gate_kind="todo", gate_ref="T-12"
            )
            res_t12 = check_engine.resolve_gate_ref(root, "todo", "T-12")
            self.assertEqual(res_t12.verdict, "unknown")

            dangling = check_engine.check_gate_ref_dangling(root)
            discharged = check_engine.check_gate_ref_discharged(root)
            self.assertEqual(dangling, [])
            self.assertEqual(discharged, [])

            # Part 2: Empty index simulating inventory failure in build_dependency_index
            empty_idx = check_engine._DepIndex(owners={})
            res_empty = check_engine.resolve_gate_ref(
                root, "todo", "bbbbbb", index=empty_idx
            )
            self.assertEqual(res_empty.verdict, "unknown")

            dang_empty = check_engine.check_gate_ref_dangling(root, index=empty_idx)
            disch_empty = check_engine.check_gate_ref_discharged(root, index=empty_idx)
            self.assertEqual(dang_empty, [])
            self.assertEqual(disch_empty, [])

    def test_13_falsifiable_negative_rule_and_severity(self):
        """Case 13: Falsifiable negatives asserting rule id and severity for both rules."""
        # Falsifiable negative for check.gate-ref-dangling: rule id and error severity
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _create_backlog_item(
                root, "blocked", "item01", gate_kind="artifact", gate_ref="nosuch.md"
            )
            dangling = check_engine.check_gate_ref_dangling(root)
            self.assertEqual(len(dangling), 1)
            dang_finding = dangling[0]
            self.assertEqual(dang_finding.rule, "check.gate-ref-dangling")
            self.assertEqual(dang_finding.severity, "error")

        # Falsifiable negative for check.gate-ref-discharged: rule id and warning severity
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _create_plan(root, "executed", "tgt002")
            _create_backlog_item(
                root, "blocked", "item02", gate_kind="artifact", gate_ref="tgt002"
            )
            discharged = check_engine.check_gate_ref_discharged(root)
            self.assertEqual(len(discharged), 1)
            disch_finding = discharged[0]
            self.assertEqual(disch_finding.rule, "check.gate-ref-discharged")
            self.assertEqual(disch_finding.severity, "warning")

    def test_14_path_containment_escaping_ref(self):
        """Case 14: A todo ref of ../-escaping shape pointing at an outside file does NOT resolve by path route."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            outside_file = root.parent / "outside_marker.txt"
            outside_file.write_text("outside", encoding="utf-8")
            try:
                esc_ref = f"../{outside_file.name}"
                res = check_engine.resolve_gate_ref(root, "todo", esc_ref)
                self.assertNotEqual(res.route, "path")
                self.assertEqual(res.verdict, "unknown")
            finally:
                if outside_file.exists():
                    outside_file.unlink()

    def test_15_non_live_carrier_yields_nothing(self):
        """Case 15: A gate on a non-live carrier (open backlog item, non-deferred spec) yields nothing."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Open backlog item with dangling ref (should be ignored by these sweeps)
            _create_backlog_item(
                root, "open", "open01", gate_kind="artifact", gate_ref="dangling.md"
            )
            # Approved spec with dangling ref (should be ignored by these sweeps)
            _create_spec(
                root, "approved", "spec02", gate_kind="todo", gate_ref="zzzzzz"
            )

            dangling = check_engine.check_gate_ref_dangling(root)
            discharged = check_engine.check_gate_ref_discharged(root)
            self.assertEqual(dangling, [])
            self.assertEqual(discharged, [])
