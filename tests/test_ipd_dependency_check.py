"""Tests for ipddeps Order ovbnyq: the shared cross-IPD dependency evaluator + check.ipd-dependency-*
rule family across `aw check` and phased `aw ipd lint`, plus grandfathering cutover.

Covers:
* V-01 - the pure evaluator emits each of the six findings on exactly its own fixture:
  missing / unresolved / malformed / dangling / ambiguous / cycle; clean otherwise.
* V-02 - BOTH `aw check plans` AND `aw check all` surface a dangling and a cyclic finding with the
  same rule IDs; a clean tree passes both; no double-report in the `all` sweep.
* V-03 - the phase matrix: author = advisory for missing/unresolved (blocking for malformed);
  review-finalize/pre-execution/pre-transition = blocking for missing/unresolved/malformed, and the
  repo-resolving dangling/cyclic checks block at those phases (author does not resolve).
* V-04 - grandfathering: with NO cutover marker the current corpus does not mass-fail; with a
  cutover marker a post-cutover missing-field IPD errors while a pre-cutover plan is grandfathered;
  no tool auto-inserts `none` (scaffold emits `unresolved`).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import ipd_lint
from agent_workflows import ipd_schema as S


def _mkrepo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="aw_depchk_"))
    (d / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    (d / ".aw" / "config").mkdir(parents=True)
    return d


def _set_cutover(repo: Path, date: str | None) -> None:
    import json

    pj = repo / ".aw" / "config" / "project.json"
    if date is None:
        if pj.exists():
            pj.unlink()
        return
    pj.write_text(
        json.dumps({"dependency_schema_cutover": {"date": date}}), encoding="utf-8"
    )


def _plan(
    repo: Path,
    *,
    id6: str,
    order: int,
    item_deps: str | None,
    date: str = "2026-08-27",
    setid: str = "demo",
) -> Path:
    pend = repo / ".aw" / "records" / "plans" / "pending"
    dep_line = f"- Item-Dependencies: {item_deps}\n" if item_deps is not None else ""
    p = pend / f"{date.replace('-', '')}-{setid}-{order:02d}-{id6}-p.ipd.md"
    p.write_text(
        f"# IPD: {id6}\n\n"
        f"- Date: {date}\n- Kind: child\n- Scope-Paths: x.py\n"
        f"{dep_line}"
        f"- Status: draft\n- Set: {setid}\n- Order: {order}\n- Id: {id6}\n\n"
        f"## Workflow history\n- {date} draft (t): x\n\n## Goal\ng\n",
        encoding="utf-8",
    )
    return p


def _spec(repo: Path, *, id6: str, status: str = "draft") -> Path:
    d = repo / ".aw" / "records" / "specs"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260101-1200-01-{id6}-s.spec.md"
    p.write_text(
        f"# Spec {id6}\n\n- Id: {id6}\n- Status: {status}\n\n## Summary\ns\n",
        encoding="utf-8",
    )
    return p


def _rules(drift, prefix="check.ipd-") -> list:
    # This helper targets the cross-IPD DEPENDENCY rules. The agentadhere Phase 1 (IPD uisjns)
    # advisory `check.ipd-draft-ready-to-review` shares the `check.ipd-` prefix but is a separate
    # (draft-readiness) concern, so it is excluded here to keep these dependency assertions focused.
    return [
        d.rule
        for d in drift
        if d.rule.startswith(prefix) and d.rule != "check.ipd-draft-ready-to-review"
    ]


# --------------------------------------------------------------------------------------
# V-01: the pure evaluator, one finding per crafted fixture
# --------------------------------------------------------------------------------------


class EvaluatorRuleMatrixTests(unittest.TestCase):
    def setUp(self):
        self.repo = _mkrepo()
        # activate cutover in the past so a missing statement is an error here
        _set_cutover(self.repo, "2020-01-01")

    def _eval(self):
        return ce.evaluate_ipd_dependencies(self.repo, phase="check")

    def test_clean_none_has_no_finding(self):
        _plan(self.repo, id6="aaaaaa", order=1, item_deps="none")
        self.assertEqual(_rules(self._eval()), [])

    def test_missing_statement(self):
        _plan(self.repo, id6="aaaaaa", order=1, item_deps=None)
        self.assertIn(S.RULE_IPD_DEP_MISSING, _rules(self._eval()))

    def test_unresolved_sentinel_blocking_phase(self):
        _plan(self.repo, id6="aaaaaa", order=1, item_deps="unresolved")
        drift = ce.evaluate_ipd_dependencies(self.repo, phase="pre-execution")
        self.assertIn(S.RULE_IPD_DEP_UNRESOLVED, _rules(drift))

    def test_malformed(self):
        _plan(
            self.repo,
            id6="aaaaaa",
            order=1,
            item_deps="executed:aaaaaa, executed:aaaaaa",
        )
        # duplicate edge -> malformed (also self, but duplicate is caught by the parser first)
        self.assertIn(S.RULE_IPD_DEP_MALFORMED, _rules(self._eval()))

    def test_self_dependency_is_malformed(self):
        _plan(self.repo, id6="aaaaaa", order=1, item_deps="executed:aaaaaa")
        self.assertIn(S.RULE_IPD_DEP_MALFORMED, _rules(self._eval()))

    def test_dangling(self):
        _plan(self.repo, id6="aaaaaa", order=1, item_deps="executed:zzzzzz")
        self.assertIn(S.RULE_IPD_DEP_DANGLING, _rules(self._eval()))

    def test_ambiguous_multiple_owners(self):
        # two plans declare the same id6 'dupdup' -> resolving an edge to it is ambiguous
        _plan(self.repo, id6="dupdup", order=1, item_deps="none")
        _plan(self.repo, id6="dupdup", order=2, item_deps="none")
        _plan(self.repo, id6="aaaaaa", order=3, item_deps="executed:dupdup")
        self.assertIn(S.RULE_IPD_DEP_AMBIGUOUS, _rules(self._eval()))

    def test_cycle_two_node(self):
        _plan(self.repo, id6="aaaaaa", order=1, item_deps="executed:bbbbbb")
        _plan(self.repo, id6="bbbbbb", order=2, item_deps="executed:aaaaaa")
        self.assertIn(S.RULE_IPD_DEP_CYCLE, _rules(self._eval()))

    def test_cycle_three_node(self):
        _plan(self.repo, id6="aaaaaa", order=1, item_deps="executed:bbbbbb")
        _plan(self.repo, id6="bbbbbb", order=2, item_deps="executed:cccccc")
        _plan(self.repo, id6="cccccc", order=3, item_deps="executed:aaaaaa")
        self.assertIn(S.RULE_IPD_DEP_CYCLE, _rules(self._eval()))

    def test_cross_type_edge_resolves(self):
        # exists:spec:<id6> resolves against a specs record, not a plans one
        _spec(self.repo, id6="spec01")
        _plan(self.repo, id6="aaaaaa", order=1, item_deps="exists:spec:spec01")
        self.assertEqual(_rules(self._eval()), [])

    def test_spec_edge_dangling_when_only_a_plan_has_that_id6(self):
        # a plan owns 'plnpln' but the edge asks for a SPEC with that id6 -> dangling
        _plan(self.repo, id6="plnpln", order=1, item_deps="none")
        _plan(self.repo, id6="aaaaaa", order=2, item_deps="exists:spec:plnpln")
        self.assertIn(S.RULE_IPD_DEP_DANGLING, _rules(self._eval()))


# --------------------------------------------------------------------------------------
# V-01b: the pure cycle helper
# --------------------------------------------------------------------------------------


class CycleHelperTests(unittest.TestCase):
    def test_acyclic(self):
        self.assertEqual(
            S.item_dependency_cycles({"a": ["b"], "b": ["c"], "c": []}), []
        )

    def test_two_node_cycle(self):
        cycles = S.item_dependency_cycles({"a": ["b"], "b": ["a"]})
        self.assertEqual(len(cycles), 1)

    def test_leaf_target_not_in_graph_no_cycle(self):
        # 'b' is a target but not itself an owner (spec/backlog leaf) -> no cycle
        self.assertEqual(S.item_dependency_cycles({"a": ["b"]}), [])


# --------------------------------------------------------------------------------------
# V-02: aw check plans AND all surface findings once
# --------------------------------------------------------------------------------------


class CheckSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.repo = _mkrepo()
        _set_cutover(self.repo, "2020-01-01")

    def test_check_ipd_dependencies_repo_scan_dangling(self):
        _plan(self.repo, id6="aaaaaa", order=1, item_deps="executed:zzzzzz")
        drift = ce.check_ipd_dependencies(self.repo)
        self.assertIn(S.RULE_IPD_DEP_DANGLING, _rules(drift))

    def test_plans_content_path_includes_dependency_check(self):
        # check_content("plans") must include the dependency finding (reached by aw check plans AND all)
        _plan(self.repo, id6="aaaaaa", order=1, item_deps="executed:zzzzzz")
        content = ce.check_content(self.repo, "plans")
        self.assertIn(S.RULE_IPD_DEP_DANGLING, _rules(content))

    def test_check_all_does_not_double_report(self):
        _plan(self.repo, id6="aaaaaa", order=1, item_deps="executed:zzzzzz")
        drift = ce.check_types(self.repo, ["all"])
        dangling = [
            d
            for d in drift
            if d.rule == S.RULE_IPD_DEP_DANGLING and "aaaaaa" in d.location
        ]
        self.assertEqual(
            len(dangling), 1, "dangling finding must appear exactly once in `all`"
        )

    def test_clean_tree_passes(self):
        _plan(self.repo, id6="aaaaaa", order=1, item_deps="none")
        self.assertEqual(_rules(ce.check_content(self.repo, "plans")), [])


# --------------------------------------------------------------------------------------
# V-03: phased lint matrix (pure syntax fn + resolution pass)
# --------------------------------------------------------------------------------------


class PhasedLintTests(unittest.TestCase):
    def _doc(self, item_deps: str | None):
        dep = f"- Item-Dependencies: {item_deps}\n" if item_deps is not None else ""
        text = (
            "# IPD: x\n\n- Date: 2026-08-27\n- Kind: child\n- Scope-Paths: x.py\n"
            f"{dep}- Status: draft\n- Set: demo\n- Order: 1\n- Id: aaaaaa\n\n"
            "## Workflow history\n- 2026-08-27 draft (t): x\n\n## Goal\ng\n"
        )
        return ipd_lint.parse(text)

    def test_author_missing_is_silent_pure(self):
        # A missing statement emits NOTHING in the pure lint (MISSING is cutover-gated + repo-aware,
        # applied in lint_file), so the pre-cutover corpus is never mass-failed or advisory-polluted.
        blocking, advisory = ipd_lint.check_item_dependencies(
            self._doc(None), "author", "pending"
        )
        self.assertEqual(blocking, [])
        self.assertEqual(advisory, [])

    def test_author_unresolved_is_advisory(self):
        blocking, advisory = ipd_lint.check_item_dependencies(
            self._doc("unresolved"), "author", "pending"
        )
        self.assertEqual(blocking, [])
        self.assertTrue(any(a.code == S.RULE_IPD_DEP_UNRESOLVED for a in advisory))

    def test_author_malformed_is_blocking(self):
        blocking, _adv = ipd_lint.check_item_dependencies(
            self._doc("executed:aaaaaa, executed:aaaaaa"), "author", "pending"
        )
        self.assertTrue(any(b.code == S.RULE_IPD_DEP_MALFORMED for b in blocking))

    def test_missing_is_silent_in_pure_lint(self):
        # The pure syntax fn emits NOTHING for a missing statement (cutover-gated MISSING is applied
        # repo-aware in lint_file); this keeps the pre-cutover corpus from mass-failing/advisory-noise.
        blocking, advisory = ipd_lint.check_item_dependencies(
            self._doc(None), "review-finalize", "pending"
        )
        self.assertEqual(blocking, [])
        self.assertEqual(advisory, [])

    def test_lint_file_missing_blocks_post_cutover(self):
        # A POST-cutover plan missing the field is blocked at a blocking phase via lint_file.
        repo = _mkrepo()
        _set_cutover(repo, "2026-01-01")
        p = _plan(repo, id6="aaaaaa", order=1, item_deps=None, date="2026-08-27")
        res = ipd_lint.lint_file(p, checkpoint="pre-execution")
        self.assertEqual(res.disposition, S.DISPOSITION_ERROR)
        self.assertTrue(any(d.code == S.RULE_IPD_DEP_MISSING for d in res.diagnostics))

    def test_lint_file_missing_grandfathered_pre_cutover(self):
        repo = _mkrepo()
        _set_cutover(repo, "2026-08-01")
        p = _plan(repo, id6="aaaaaa", order=1, item_deps=None, date="2026-01-01")
        res = ipd_lint.lint_file(p, checkpoint="pre-execution")
        self.assertFalse(any(d.code == S.RULE_IPD_DEP_MISSING for d in res.diagnostics))

    def test_review_finalize_unresolved_is_blocking(self):
        for phase in ("review-finalize", "pre-execution", "pre-transition"):
            blocking, _adv = ipd_lint.check_item_dependencies(
                self._doc("unresolved"), phase, "pending"
            )
            self.assertTrue(
                any(b.code == S.RULE_IPD_DEP_UNRESOLVED for b in blocking),
                f"unresolved must block at {phase}",
            )

    def test_valid_statement_passes_all_phases(self):
        for phase in ("author", "review-finalize", "pre-execution", "pre-transition"):
            blocking, _adv = ipd_lint.check_item_dependencies(
                self._doc("none"), phase, "pending"
            )
            self.assertEqual(blocking, [], f"valid `none` must pass {phase}")

    def test_lint_file_resolution_dangling_blocks_at_pre_execution(self):
        repo = _mkrepo()
        _set_cutover(repo, "2020-01-01")
        p = _plan(repo, id6="aaaaaa", order=1, item_deps="executed:zzzzzz")
        res = ipd_lint.lint_file(p, checkpoint="pre-execution")
        self.assertEqual(res.disposition, S.DISPOSITION_ERROR)
        self.assertTrue(any(d.code == S.RULE_IPD_DEP_DANGLING for d in res.diagnostics))


# --------------------------------------------------------------------------------------
# V-04: grandfathering
# --------------------------------------------------------------------------------------


class GrandfatheringTests(unittest.TestCase):
    def test_no_cutover_marker_no_mass_fail(self):
        repo = _mkrepo()
        _set_cutover(repo, None)  # no marker
        # several plans WITHOUT the field
        _plan(repo, id6="aaaaaa", order=1, item_deps=None)
        _plan(repo, id6="bbbbbb", order=2, item_deps=None)
        drift = ce.check_ipd_dependencies(repo)
        self.assertEqual(
            [d for d in drift if d.rule == S.RULE_IPD_DEP_MISSING],
            [],
            "with no cutover marker, missing statements must NOT mass-fail",
        )

    def test_post_cutover_missing_is_error(self):
        repo = _mkrepo()
        _set_cutover(repo, "2026-01-01")
        # plan dated AFTER cutover, missing the field -> error
        _plan(repo, id6="aaaaaa", order=1, item_deps=None, date="2026-08-27")
        drift = ce.check_ipd_dependencies(repo)
        self.assertTrue(any(d.rule == S.RULE_IPD_DEP_MISSING for d in drift))

    def test_pre_cutover_missing_is_grandfathered(self):
        repo = _mkrepo()
        _set_cutover(repo, "2026-08-01")
        # plan dated BEFORE cutover, missing the field -> grandfathered (no missing finding at check)
        _plan(repo, id6="aaaaaa", order=1, item_deps=None, date="2026-01-01")
        drift = ce.check_ipd_dependencies(repo)
        self.assertEqual([d for d in drift if d.rule == S.RULE_IPD_DEP_MISSING], [])

    def test_current_repo_not_mass_failed(self):
        # The REAL repository (this checkout) must not mass-fail the dependency check.
        repo = Path(__file__).resolve().parents[1]
        drift = ce.check_ipd_dependencies(repo)
        missing = [d for d in drift if d.rule == S.RULE_IPD_DEP_MISSING]
        self.assertEqual(
            missing,
            [],
            f"current corpus must not mass-fail; got {len(missing)} missing findings",
        )

    def test_no_tool_auto_inserts_none(self):
        # scaffold emits `unresolved`, never `none`; the setter only writes what the user gives.
        from agent_workflows import ipd_authoring

        import inspect

        src = inspect.getsource(ipd_authoring)
        self.assertIn("- Item-Dependencies: unresolved", src)
        self.assertNotIn("- Item-Dependencies: none", src)


if __name__ == "__main__":
    unittest.main()
