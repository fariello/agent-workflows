"""Tests for the recorded-decisions audit trail (revgate Order 04, `c621h9` E-06).

Covers the `aw reviews decisions` verb (E-04), the `Reversible` classification (E-03), and the
advisory `check.review-decision-unescalated` rule (E-07), including the adversarial guard OBSERVED
BOTH WAYS: firing on an unescalated irreversible decision AND staying quiet on an escalated one. A
guard never seen to fire is not evidence, and a guard never seen to stay quiet is not evidence either.

EVERY test builds its own ISOLATED FIXTURE REPO under a tmpdir. None reads this checkout's live
`.aw/records/`. That is deliberate: a rule test that scanned the real tree would be order-dependent on
whatever other agents have committed and would break the moment a real review record lands (the
live-state-asserting test defect class that pending plan `i79rgh` exists to fix).
"""

from __future__ import annotations

import io
import json
import re
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from agent_workflows import check_engine, review_findings as rf, reviews

ANSI_RE = re.compile(r"\x1b\[")


def _plan_text(
    *,
    id6: str = "abc123",
    blocking_question: bool = False,
) -> str:
    """A minimal pending-lane IPD carrying an `- Id:`, optionally with a blocking open question."""
    oq = ""
    if blocking_question:
        oq = (
            "\n## Open questions\n\n"
            "### OQ-01: is the irreversible choice acceptable?\n\n"
            "- Blocking: yes\n"
            "- Status: open\n"
            "- Owner: maintainer\n"
            "- Resolution or deferral rationale: pending a maintainer decision\n"
        )
    return (
        "# IPD: fixture plan\n\n"
        "- Date: 2026-08-30\n"
        "- Kind: child\n"
        f"- Id: {id6}\n"
        "- Status: to-review\n"
        "- Set: fixture\n"
        "- Order: 1\n" + oq
    )


def _decision(
    *,
    did: str = "D-1",
    question: str = "which resolver should the verb use?",
    chosen: str = "the shared selectors.resolve",
    alternatives: str = "a hand-rolled id6 matcher",
    basis: str = "selectors.py:347",
    reversible: str = "yes",
) -> rf.Decision:
    return rf.Decision(
        id=did,
        question=question,
        chosen=chosen,
        alternatives=alternatives,
        basis=basis,
        reversible=reversible,
    )


def _finding(
    *, fid: str = "F-1", severity: str = "low", decision: str = "fixed"
) -> rf.Finding:
    return rf.Finding(
        id=fid,
        severity=severity,
        scope="in-scope",
        area="rubric",
        evidence="foo.py:1",
        finding="a thing",
        remediation_risk="low",
        decision=decision,
        resolution="done",
    )


class _Repo:
    """An isolated fixture repo: a plans tree, a reviews tree, and nothing else."""

    def __init__(self, root: Path):
        self.root = root
        self.plans = root / ".aw" / "records" / "plans" / "pending"
        self.reviews = root / ".aw" / "records" / "reviews"
        self.plans.mkdir(parents=True, exist_ok=True)
        self.reviews.mkdir(parents=True, exist_ok=True)

    def write_plan(
        self, *, id6: str = "abc123", blocking_question: bool = False
    ) -> Path:
        p = self.plans / f"20260830-fixture-01-{id6}-a-fixture-plan.ipd.md"
        p.write_text(
            _plan_text(id6=id6, blocking_question=blocking_question), encoding="utf-8"
        )
        return p

    def write_review(
        self,
        *,
        id6: str = "abc123",
        rounds=None,
        decisions=None,
        findings=None,
    ) -> Path:
        if rounds is None:
            rounds = [
                rf.Round(
                    number=1,
                    findings=tuple(findings or (_finding(),)),
                    decisions=tuple(decisions or ()),
                )
            ]
        dest = self.reviews / f"20260830-fixture-01-{id6}-a-fixture-plan.review.md"
        return rf.write_review(
            dest,
            plan_id=id6,
            reviewed_at="2026-08-30",
            reviewer="opencode test",
            verdict="APPROVE",
            rounds=rounds,
        )

    def write_malformed_review(self, *, id6: str = "abc123") -> Path:
        dest = self.reviews / f"20260830-fixture-01-{id6}-a-fixture-plan.review.md"
        dest.write_text(
            "# Plan review findings: {0}\n\n"
            "- Plan-Id: {0}\n"
            "- Reviewed-At: 2026-08-30\n"
            "- Reviewer: opencode test\n"
            "- Verdict: APPROVE\n\n"
            "## Round 1\n\n"
            "### Findings\n\n"
            "| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| F-1 | HGIH | in-scope | rubric | a.py:1 | x | low | open | y |\n".format(
                id6
            ),
            encoding="utf-8",
        )
        return dest


class ReversibleClassificationTests(unittest.TestCase):
    """E-03: the `Reversible` cell is a three-way judgement, and a blank is not 'reversible'."""

    def test_reversible_values(self):
        for token in ("yes", "YES", " Yes ", "y", "true", "reversible", "yes."):
            self.assertEqual(
                reviews.classify_reversible(token),
                "yes",
                f"{token!r} should be reversible",
            )

    def test_irreversible_values(self):
        for token in ("no", "NO", " No ", "n", "false", "irreversible", "no."):
            self.assertEqual(
                reviews.classify_reversible(token),
                "no",
                f"{token!r} should be irreversible",
            )

    def test_blank_and_typo_are_unknown_not_reversible(self):
        """The load-bearing case: a blank must NOT read as safely reversible."""
        for token in ("", "   ", "maybe", "Reversibel", "sort of"):
            self.assertEqual(
                reviews.classify_reversible(token),
                "unknown",
                f"{token!r} must be unknown, never silently 'yes'",
            )


class DecisionRoundTripTests(unittest.TestCase):
    """A decisions row survives write -> parse -> collect with every cell intact."""

    def test_decision_row_round_trips(self):
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan()
            repo.write_review(decisions=[_decision()])

            rows, diags = reviews.collect_decisions(repo.root)
            self.assertEqual(
                diags, [], "a well-formed review must yield no diagnostics"
            )
            self.assertEqual(len(rows), 1)
            r = rows[0]
            self.assertEqual(r.id, "D-1")
            self.assertEqual(r.plan_id, "abc123")
            self.assertEqual(r.question, "which resolver should the verb use?")
            self.assertEqual(r.chosen, "the shared selectors.resolve")
            self.assertEqual(r.alternatives, "a hand-rolled id6 matcher")
            self.assertEqual(r.basis, "selectors.py:347")
            self.assertEqual(r.reversible, "yes")
            self.assertFalse(r.is_irreversible)
            self.assertEqual(r.round_number, 1)
            self.assertTrue(r.is_current_round)

    def test_audit_includes_every_round_unlike_the_gate(self):
        """The audit reports ALL rounds; the check reads only the current one. Both on purpose."""
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan()
            repo.write_review(
                rounds=[
                    rf.Round(1, (_finding(),), (_decision(did="D-1"),)),
                    rf.Round(2, (_finding(),), (_decision(did="D-2"),)),
                ]
            )

            all_rounds, _ = reviews.collect_decisions(repo.root)
            self.assertEqual([r.id for r in all_rounds], ["D-1", "D-2"])

            current, _ = reviews.collect_decisions(repo.root, current_round_only=True)
            self.assertEqual([r.id for r in current], ["D-2"])


class ReviewsDecisionsVerbTests(unittest.TestCase):
    """E-04: the read-only verb, its filter, its machine mode, and its empty state."""

    def _args(self, root: Path, **kw):
        base = dict(
            dir=str(root),
            selector=None,
            irreversible=False,
            agent=False,
            json=False,
            no_color=True,
        )
        base.update(kw)
        return SimpleNamespace(**base)

    def _run(self, root: Path, **kw):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = reviews.run_decisions(self._args(root, **kw))
        return rc, buf.getvalue()

    def test_prints_a_recorded_decision_and_exits_zero(self):
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan()
            repo.write_review(decisions=[_decision()])

            rc, out = self._run(repo.root)
            self.assertEqual(rc, 0)
            self.assertIn("D-1", out)
            self.assertIn("which resolver should the verb use?", out)
            self.assertIn("the shared selectors.resolve", out)
            self.assertIn("a hand-rolled id6 matcher", out)
            self.assertIn("selectors.py:347", out)

    def test_irreversible_filter(self):
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan()
            repo.write_review(
                decisions=[
                    _decision(
                        did="D-1", reversible="yes", question="the undoable question"
                    ),
                    _decision(
                        did="D-2", reversible="no", question="the permanent question"
                    ),
                ]
            )

            rc, out = self._run(repo.root)
            self.assertEqual(rc, 0)
            self.assertIn("D-1", out)
            self.assertIn("D-2", out)

            rc, out = self._run(repo.root, irreversible=True)
            self.assertEqual(rc, 0)
            self.assertIn("D-2", out)
            self.assertIn("the permanent question", out)
            self.assertNotIn("D-1", out)
            self.assertNotIn("the undoable question", out)
            self.assertIn("IRREVERSIBLE", out)

    def test_unknown_reversible_is_not_in_the_irreversible_filter_but_is_counted(self):
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan()
            repo.write_review(decisions=[_decision(did="D-9", reversible="")])

            rc, out = self._run(repo.root)
            self.assertEqual(rc, 0)
            self.assertIn("UNJUDGED", out)
            self.assertIn("no Reversible judgement", out)

            rc, out = self._run(repo.root, irreversible=True)
            self.assertEqual(rc, 0)
            self.assertIn("no irreversible recorded decisions", out)

    def test_agent_mode_is_ansi_free_and_parses_as_json(self):
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan()
            repo.write_review(
                decisions=[
                    _decision(did="D-1", reversible="yes"),
                    _decision(did="D-2", reversible="no"),
                ]
            )

            rc, out = self._run(repo.root, agent=True)
            self.assertEqual(rc, 0)
            self.assertNotRegex(out, ANSI_RE.pattern)
            payload = json.loads(out.strip().splitlines()[0])
            self.assertEqual(payload["cmd"], "reviews decisions")
            self.assertEqual(payload["exit"], 0)

            rc, out = self._run(repo.root, json=True)
            self.assertEqual(rc, 0)
            self.assertNotRegex(out, ANSI_RE.pattern)
            full = json.loads(out)
            data = full.get("data", full)
            self.assertEqual(data["total"], 2)
            self.assertEqual(data["irreversible"], 1)
            ids = [d["id"] for d in data["decisions"]]
            self.assertEqual(ids, ["D-1", "D-2"])

    def test_empty_tree_is_a_clean_empty_state_at_exit_zero(self):
        """E-04's pre-dependency case: no `reviews/` tree must not crash and must not exit 1."""
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
            self.assertFalse((root / ".aw" / "records" / "reviews").exists())

            rc, out = self._run(root)
            self.assertEqual(rc, 0, "an absent reviews tree must exit 0, not 1")
            self.assertIn("no decisions recorded", out)

            rc, out = self._run(root, agent=True)
            self.assertEqual(rc, 0)
            self.assertEqual(json.loads(out.strip().splitlines()[0])["exit"], 0)

    def test_selector_resolves_through_the_shared_resolver(self):
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan(id6="abc123")
            repo.write_review(id6="abc123", decisions=[_decision(did="D-1")])
            repo.write_plan(id6="def456")
            repo.write_review(id6="def456", decisions=[_decision(did="D-7")])

            rc, out = self._run(repo.root, selector="abc123")
            self.assertEqual(rc, 0)
            self.assertIn("D-1", out)
            self.assertNotIn("D-7", out)

    def test_unmatched_selector_is_a_clean_empty_state_not_an_error(self):
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan()
            repo.write_review(decisions=[_decision()])

            rc, out = self._run(repo.root, selector="zzzzzz")
            self.assertEqual(rc, 0)
            self.assertIn("no review record matches", out)


class ReviewDecisionCheckRuleTests(unittest.TestCase):
    """E-07: the advisory rule, observed FIRING and observed STAYING QUIET."""

    def _sweep(self, repo: _Repo):
        return check_engine.check_review_decision_unescalated(repo.root)

    def test_fires_on_unescalated_irreversible_decision(self):
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan(blocking_question=False)
            repo.write_review(decisions=[_decision(did="D-2", reversible="no")])

            drift = self._sweep(repo)
            self.assertEqual(
                len(drift), 1, f"expected exactly one finding, got {drift}"
            )
            d = drift[0]
            self.assertEqual(d.rule, "check.review-decision-unescalated")
            self.assertIn("D-2", d.detail)
            self.assertIn("irreversible", d.detail)

    def test_quiet_when_escalated_via_blocking_open_question(self):
        """The other half of the guard: an ESCALATED irreversible decision must not fire."""
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan(blocking_question=True)
            repo.write_review(decisions=[_decision(did="D-2", reversible="no")])

            self.assertEqual(self._sweep(repo), [])

    def test_quiet_when_maintainer_was_told(self):
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan(blocking_question=False)
            repo.write_review(
                decisions=[
                    _decision(
                        did="D-3",
                        reversible="no",
                        basis="selectors.py:347; maintainer told 2026-08-30",
                    )
                ]
            )

            self.assertEqual(self._sweep(repo), [])

    def test_quiet_on_reversible_decision(self):
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan(blocking_question=False)
            repo.write_review(decisions=[_decision(did="D-1", reversible="yes")])

            self.assertEqual(self._sweep(repo), [])

    def test_reports_a_decision_with_no_reversible_judgement(self):
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan(blocking_question=False)
            repo.write_review(decisions=[_decision(did="D-4", reversible="")])

            drift = self._sweep(repo)
            self.assertEqual(len(drift), 1)
            self.assertIn("no `Reversible` judgement", drift[0].detail)

    def test_absent_artifact_is_silent(self):
        """MANDATORY: no `.review.md` must produce NOTHING, or the whole corpus would be reported."""
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan(blocking_question=False)
            # No review written at all.
            self.assertEqual(self._sweep(repo), [])

    def test_malformed_artifact_is_reported_and_does_not_raise(self):
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan(blocking_question=False)
            repo.write_malformed_review()

            drift = self._sweep(repo)
            self.assertTrue(drift, "a malformed review must be reported, not skipped")
            self.assertTrue(
                any("malformed" in d.detail for d in drift),
                f"expected a malformed-artifact finding, got {[d.detail for d in drift]}",
            )

    def test_only_the_current_round_carries_an_obligation(self):
        """A round-1 irreversible decision superseded by round 2 no longer fires."""
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan(blocking_question=False)
            repo.write_review(
                rounds=[
                    rf.Round(
                        1, (_finding(),), (_decision(did="D-1", reversible="no"),)
                    ),
                    rf.Round(
                        2, (_finding(),), (_decision(did="D-2", reversible="yes"),)
                    ),
                ]
            )

            self.assertEqual(self._sweep(repo), [])

    def test_terminal_lane_plans_are_grandfathered(self):
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            executed = repo.root / ".aw" / "records" / "plans" / "executed"
            executed.mkdir(parents=True, exist_ok=True)
            (executed / "20260830-fixture-01-abc123-a-fixture-plan.ipd.md").write_text(
                _plan_text(id6="abc123"), encoding="utf-8"
            )
            repo.write_review(decisions=[_decision(did="D-2", reversible="no")])

            self.assertEqual(
                self._sweep(repo),
                [],
                "a terminal-lane plan must not be retroactively litigated",
            )

    def test_registered_as_an_advisory_warning_not_an_error(self):
        """Registration is behavioral: an unregistered id defaults to ERROR severity."""
        spec = check_engine.RULE_REGISTRY["check.review-decision-unescalated"]
        self.assertEqual(spec.severity, "warning")
        self.assertNotEqual(spec, check_engine._DEFAULT_RULESPEC)

    def test_the_finding_carries_the_registered_warning_severity(self):
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan(blocking_question=False)
            repo.write_review(decisions=[_decision(did="D-2", reversible="no")])

            drift = self._sweep(repo)
            self.assertEqual(len(drift), 1)
            self.assertEqual(drift[0].severity, "warning")
            self.assertEqual(
                check_engine.finding_dict(drift[0])["severity"],
                "warning",
                "the serialized finding must carry the registered severity",
            )

    def test_warning_severity_still_drives_a_nonzero_findings_exit(self):
        """PINS THE MEASURED TRUTH so no future reader overreads 'advisory'.

        `artifact_core.drift_exit_code` exempts only `info`, so this `warning` DOES produce exit 1.
        What the severity buys is the absence of a LIFECYCLE gate, not immunity from the exit code. If
        someone later 'clarifies' the docs to claim a warning cannot fail a check, this test fails.
        """
        from agent_workflows.artifact_core import drift_exit_code

        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan(blocking_question=False)
            repo.write_review(decisions=[_decision(did="D-2", reversible="no")])

            drift = self._sweep(repo)
            self.assertEqual(
                drift_exit_code(drift),
                1,
                "a warning-severity finding contributes to the findings exit; only info is exempt",
            )

    def test_adds_no_lifecycle_gate(self):
        """The real content of 'advisory' here: no `aw ipd lint` checkpoint references this rule.

        Its Order 02 sibling IS wired into two lint checkpoints. This one deliberately is not, which is
        the sense in which the plan's OQ-01 resolved 'nothing blocks'.
        """
        from agent_workflows import ipd_lint

        src = Path(ipd_lint.__file__).read_text(encoding="utf-8")
        self.assertNotIn(
            "review_decision",
            src,
            "this rule must not be wired into a lint checkpoint; it is a report-only backstop",
        )
        self.assertNotIn("check.review-decision-unescalated", src)

    def test_wired_into_the_plans_type_content_path_exactly_once(self):
        """Guards against a double-report: one CALL site, plus the one definition."""
        src = Path(check_engine.__file__).read_text(encoding="utf-8")
        occurrences = src.count("check_review_decision_unescalated")
        definitions = src.count("def check_review_decision_unescalated")
        self.assertEqual(definitions, 1, "exactly one definition expected")
        self.assertEqual(
            occurrences - definitions,
            1,
            "the sweep must be called from exactly ONE place, or `aw check all` double-reports",
        )

    def test_reached_by_both_check_plans_and_check_all(self):
        """The plans-type content path is shared, so one wiring serves both entry points."""
        with TemporaryDirectory() as td:
            repo = _Repo(Path(td))
            repo.write_plan(blocking_question=False)
            repo.write_review(decisions=[_decision(did="D-2", reversible="no")])

            for target in (["plans"], ["all"]):
                drift = check_engine.check_types(repo.root, target)
                hits = [
                    d for d in drift if d.rule == "check.review-decision-unescalated"
                ]
                self.assertEqual(
                    len(hits),
                    1,
                    f"`aw check {target[0]}` must reach the rule exactly once, got {hits}",
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
