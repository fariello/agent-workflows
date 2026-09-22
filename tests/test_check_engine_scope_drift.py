"""`check.scope-drift` reports ONE finding per plan, carrying the count AND the paths (rcptstale
`wmnmei` E-05).

THE DEFECT. The rule appended one `Drift` per offending PATH, so a single frozen base multiplied into
one finding per file of intervening history. Measured 2026-09-22 at HEAD `132e8333`: 350 findings from
exactly SIX plans (216/94/21/11/6/2). That is a real signal rendered as volume a reader learns to skip,
and the multiplication is independent of WHICH baseline or tree the rule compares against - it is wrong
under every answer to that question, which is why it is fixed separately from the tree selection.

WHAT MUST SURVIVE THE COLLAPSE, each a row or a test below, because each was a way the obvious fix
could have traded one usability failure for another:

* the PATHS, not merely a count: a plan genuinely touching three undeclared files must still say WHICH
  three, or the finding is unactionable;
* the COUNT, stated separately, so a bounded path list never hides the true total;
* one finding PER PLAN, not one per repo: two contributing plans must yield two findings, since a
  global merge would attribute one plan's paths to another;
* `(rule, location)`, which `tests/test_ci_check_parity.py` compares as a SET and which is preserved by
  construction because the location was always the plan file; and
* a populated `recovery`, which the opt-in pre-commit gate prints VERBATIM as its teaching message, so
  an empty one silently degrades the hook while every engine-level assertion still passes.

Every test builds its own temp git repo with a real lane worktree; none reads the live checkout, whose
finding distribution drifts by the hour.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import ipd_lifecycle as life
from agent_workflows import worktree_lease as lease

RULE = "check.scope-drift"


def _plan_text(plan_id: str, scope_paths: str = "src/") -> str:
    return (
        f"# IPD: x\n\n- Id: {plan_id}\n- Kind: child\n- Status: approved\n- Set: t\n- Order: 1\n"
        f"- Scope-Paths: {scope_paths}\n\n## Workflow history\n"
        "- 2026-08-25 approved (aw set): x\n\n## Goal\n\ng\n"
    )


class _DriftFixture(unittest.TestCase):
    """A temp repo with N plans, each with a live receipt and its own lane worktree."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.root, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.root, check=True)
        (self.root / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n", encoding="utf-8"
        )
        self.pending = self.root / ".aw" / "records" / "plans" / "pending"
        self.pending.mkdir(parents=True)
        (self.root / "src").mkdir()

    def _add_plan(self, plan_id: str, scope_paths: str = "src/") -> Path:
        p = self.pending / f"20260828-t-01-{plan_id}-x.ipd.md"
        p.write_text(_plan_text(plan_id, scope_paths), encoding="utf-8")
        return p

    def _commit_all(self, msg: str = "init") -> str:
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", msg], cwd=self.root, check=True)
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def _receipt(self, plan_id: str, base: str) -> None:
        rp = life.receipt_path_for(self.root, plan_id)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(
            json.dumps(
                {"plan_id": plan_id, "base_head": base, "scope_paths": ["src/"]}
            ),
            encoding="utf-8",
        )

    def _lane(self, plan_id: str) -> Path:
        """Allocate the plan's lane at the CURRENT head, via the production allocator."""
        return lease.allocate_worktree(self.root, plan_id).path

    def _dirty(self, lane: Path, *rels: str) -> None:
        """Create out-of-scope files in the lane, COMMITTED so each path is named individually.

        Committed rather than left untracked because `git status` collapses a wholly-untracked
        directory to `other/`, which would report one path where the test means several.
        """
        for rel in rels:
            (lane / rel).parent.mkdir(parents=True, exist_ok=True)
            (lane / rel).write_text("y\n", encoding="utf-8")
        subprocess.run(["git", "add", "--", *rels], cwd=lane, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "lane work", "--", *rels],
            cwd=lane,
            check=True,
        )

    def _hits(self):
        return [d for d in ce.check_scope_drift(self.root) if d.rule == RULE]


class CollapseTests(_DriftFixture):
    """E-05: N offending paths for ONE plan produce exactly ONE finding."""

    def test_many_offending_paths_yield_exactly_one_finding_naming_the_count(self):
        """FIVE out-of-scope paths -> ONE finding whose detail states the count and names each path.

        The pre-collapse rule produced five findings here. Both halves are asserted together on
        purpose: a finding count of one with a detail that lost the paths would pass a count-only test
        while being exactly as unusable as the volume it replaced.
        """
        self._add_plan("aaa111")
        base = self._commit_all()
        self._receipt("aaa111", base)
        lane = self._lane("aaa111")
        rels = [f"other/f{i}.py" for i in range(5)]
        self._dirty(lane, *rels)

        hits = self._hits()
        self.assertEqual(
            len(hits),
            1,
            f"expected ONE collapsed finding for one plan, got {len(hits)}: "
            f"{[d.detail for d in hits]}",
        )
        detail = hits[0].detail
        self.assertIn("5 changed paths are outside", detail)
        for rel in rels:
            self.assertIn(
                rel,
                detail,
                f"the collapsed finding dropped {rel!r}; a count without the paths is unactionable: "
                f"{detail!r}",
            )

    def test_the_finding_still_carries_a_populated_recovery_for_the_hook(self):
        """The pre-commit gate prints `recovery` VERBATIM, so an empty one degrades the hook silently.

        Asserted on the FIELD rather than through the hook (which `tests/test_phase4_hooks.py` covers
        end-to-end), because this is the field-level contract the hook depends on.
        """
        self._add_plan("aaa111")
        base = self._commit_all()
        self._receipt("aaa111", base)
        self._dirty(self._lane("aaa111"), "other/f.py")

        hit = self._hits()[0]
        self.assertTrue(hit.recovery, "recovery must stay populated")
        self.assertIn("Scope-Paths", hit.recovery)
        self.assertTrue(hit.observed, "observed must stay populated")
        self.assertIn("other/f.py", hit.observed)
        self.assertTrue(hit.required, "required must stay populated")

    def test_a_real_three_path_drift_still_names_all_three(self):
        """REAL-DRIFT PRESERVATION: the collapse must not hide a small genuine drift.

        This is the case the collapse could have broken while every volume measurement improved: three
        undeclared files is exactly the drift an operator must be able to act on.
        """
        self._add_plan("aaa111")
        base = self._commit_all()
        self._receipt("aaa111", base)
        self._dirty(self._lane("aaa111"), "other/a.py", "other/b.py", "other/c.py")

        hits = self._hits()
        self.assertEqual(len(hits), 1)
        for rel in ("other/a.py", "other/b.py", "other/c.py"):
            self.assertIn(rel, hits[0].detail)
        self.assertIn("3 changed paths", hits[0].detail)

    def test_a_single_offending_path_reads_as_singular(self):
        """One path is the common case; the message must not say '1 changed paths are'."""
        self._add_plan("aaa111")
        base = self._commit_all()
        self._receipt("aaa111", base)
        self._dirty(self._lane("aaa111"), "other/only.py")

        detail = self._hits()[0].detail
        self.assertIn("1 changed path is outside", detail)
        self.assertIn("other/only.py", detail)

    def test_a_long_path_list_is_bounded_and_says_how_many_it_withheld(self):
        """Bounded, never silently truncated: the tail states the remainder so the total is knowable.

        A finding is read in a pre-commit hook's stderr, so an unbounded list of 200 paths is its own
        usability failure; a truncation that does not SAY it truncated is worse, because the reader
        believes they have the whole list.
        """
        self._add_plan("aaa111")
        base = self._commit_all()
        self._receipt("aaa111", base)
        count = ce._SCOPE_DRIFT_PATHS_NAMED + 7
        self._dirty(self._lane("aaa111"), *[f"other/f{i:03d}.py" for i in range(count)])

        detail = self._hits()[0].detail
        self.assertIn(f"{count} changed paths are outside", detail)
        self.assertIn("and 7 more", detail)
        self.assertIn("other/f000.py", detail)

    def test_no_offending_path_yields_no_finding(self):
        """The collapse must not invent a zero-count finding for a conforming execution."""
        self._add_plan("aaa111")
        base = self._commit_all()
        self._receipt("aaa111", base)
        lane = self._lane("aaa111")
        (lane / "src").mkdir(parents=True, exist_ok=True)
        (lane / "src" / "feat.py").write_text("in scope\n", encoding="utf-8")

        self.assertEqual([d.detail for d in self._hits()], [])


class MultiPlanTests(_DriftFixture):
    """E-05: the collapse is PER PLAN. Nothing in a single-plan fixture could catch a global merge."""

    def test_two_contributing_plans_yield_two_findings_one_each(self):
        """Two plans, each with its own lane and its own out-of-scope paths -> exactly TWO findings.

        A collapse that merged globally would report one finding and attribute one plan's paths to the
        other, which is a worse misattribution than the per-file volume it replaced.
        """
        p1 = self._add_plan("aaa111")
        p2 = self._add_plan("bbb222")
        base = self._commit_all()
        self._receipt("aaa111", base)
        self._receipt("bbb222", base)
        self._dirty(self._lane("aaa111"), "other/one.py", "other/two.py")
        self._dirty(self._lane("bbb222"), "other/three.py")

        hits = self._hits()
        self.assertEqual(
            len(hits),
            2,
            f"expected one finding PER PLAN, got {len(hits)}: {[d.detail for d in hits]}",
        )
        by_loc = {Path(d.location).name: d for d in hits}
        self.assertEqual(set(by_loc), {p1.name, p2.name})

        first = by_loc[p1.name].detail
        self.assertIn("2 changed paths", first)
        self.assertIn("other/one.py", first)
        self.assertIn("other/two.py", first)
        self.assertNotIn(
            "other/three.py",
            first,
            "one plan's finding must not name another plan's paths",
        )

        second = by_loc[p2.name].detail
        self.assertIn("1 changed path is", second)
        self.assertIn("other/three.py", second)
        self.assertNotIn("other/one.py", second)


class RuleLocationSetTests(_DriftFixture):
    """E-05: the `(rule, location)` SET is what CI parity compares, and it must not move."""

    def test_the_rule_and_location_pair_is_the_plan_file_and_the_registered_rule(self):
        """Collapsing N findings into one preserves the `(rule, location)` SET by construction, since
        the location was ALWAYS the plan file. Verified rather than assumed, per the plan's gate."""
        plan = self._add_plan("aaa111")
        base = self._commit_all()
        self._receipt("aaa111", base)
        self._dirty(self._lane("aaa111"), "other/a.py", "other/b.py", "other/c.py")

        pairs = {(d.rule, d.location) for d in self._hits()}
        self.assertEqual(pairs, {(RULE, str(plan))})

    def test_the_severity_and_invariant_come_from_the_shared_registry(self):
        """No new rule code and no hand-set severity: the collapsed finding is still the registered
        `check.scope-drift`, enriched from `RULE_REGISTRY` (OQ-02 remains unanswered, and an
        unregistered id would silently default to `error` with an empty invariant)."""
        self._add_plan("aaa111")
        base = self._commit_all()
        self._receipt("aaa111", base)
        self._dirty(self._lane("aaa111"), "other/a.py")

        hit = self._hits()[0]
        spec = ce.rule_spec(RULE)
        self.assertEqual(hit.severity, spec.severity)
        self.assertEqual(hit.assurance, spec.assurance)
        self.assertEqual(hit.determinism, spec.determinism)


if __name__ == "__main__":
    unittest.main()
