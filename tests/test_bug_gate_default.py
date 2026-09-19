"""Tests for nobugship Order 02 (`di08i9`): the release gate is DEFAULTED on a bug rather than
remembered, and PRESERVED through graduation.

The concern these pin: "we don't ship known bugs" was a rule held only in memory, and measurably not
honored (22 of 68 live bug items carried no `- Blocks-Release:`, and every graduated gateless bug had
a `From-Backlog` carrier while none of the carriers carried a gate). So the gate must arrive by
construction at both points it was lost: creating a bug, and graduating one.

The ten E-04 cases, by name:
  1. case_01_bug_with_no_flag_is_gated_next
  2. case_02_default_is_reported_on_the_human_surface
  3. case_03_default_is_reported_on_the_agent_surface
  4. case_04_explicit_dash_yields_an_ungated_bug
  5. case_05_chore_is_not_gated
  6. case_06_explicit_gate_value_is_not_overwritten
  7. case_07_no_release_record_and_absent_flag_is_ungated_exit_zero  (the case whose REFUSAL broke
     10 existing tests at review; a fresh `aw install` creates no releases dir at all)
  8. case_08_no_release_record_and_explicit_next_still_exits_two     (REGRESSION GUARD: pre-existing
     shipped behavior, correctly passing BEFORE and after, deliberately NOT counted as new coverage)
  9. case_09_status_done_bug_is_not_gated_and_checker_is_clean
 10. case_10_ipd_set_from_backlog_inherits_the_items_gate

Plus the reclassification half (E-02), which is LIVE rather than deferred because its dependency
plan `b5sfwm` has executed and `aw backlog set` now carries `--work-kind`: both DISPATCH PATHS are
covered, because `aw backlog set` forks on whether `--status` was passed and a default wired into one
spelling only would fire inconsistently.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from agent_workflows import backlog as B
from agent_workflows import check_engine as CE
from agent_workflows import releases as R
from agent_workflows import status_set as SS
from agent_workflows.status_set import ArtifactRecord


def _args(**kw):
    ns = argparse.Namespace()
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


def _new(repo: Path, **kw):
    """Invoke `backlog new` capturing BOTH streams, returning (rc, stdout, stderr)."""
    base = dict(
        dir=str(repo),
        summary="an item",
        set=None,
        priority="high",
        work_kind="bug",
        slug=None,
        apply=True,
    )
    base.update(kw)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = B.run_new(_args(**base))
    return rc, out.getvalue(), err.getvalue()


def _record(path: Path, record_type: str, status: str) -> ArtifactRecord:
    """Build the ArtifactRecord the positional setter path consumes. It is normally built by the
    selector layer; these tests exercise `apply_status_change` directly, which is the function BOTH
    the positional `aw backlog set` spelling and `aw ipd set` route through."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"(?m)^- Id:[ \t]*(\S+)[ \t]*$", text)
    ms = re.search(r"(?m)^- Set:[ \t]*(\S+)[ \t]*$", text)
    return ArtifactRecord(
        path=path,
        record_type=record_type,
        id6=m.group(1) if m else None,
        set_id=ms.group(1) if ms else None,
        status=status,
        raw_text=text,
    )


def _sole_item(repo: Path, status: str = "open") -> Path:
    items = sorted((repo / ".aw/records/backlog" / status).glob("*.backlog.md"))
    assert len(items) == 1, f"expected exactly one {status} item, got {items}"
    return items[0]


def _planned_release(repo: Path) -> Path:
    d = repo / ".aw/records/releases"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "20260101-f33nrj-01-f33nrj-two-oh.release.md"
    p.write_text(
        "- Id: f33nrj\n- Status: planned\n- Version: 2.0.0\n- Summary: two point oh\n",
        encoding="utf-8",
    )
    return p


class _Base(unittest.TestCase):
    """A repo with a `.aw/records/backlog` tree. A PLANNED RELEASE IS NOT CREATED BY DEFAULT: the
    no-release repo is the shape a fresh `aw install` produces, so it is the base case, not the edge
    case."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        (self.repo / ".aw/records/backlog").mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()


class CreationDefaultTests(_Base):
    """E-01: the gate is defaulted at creation, with its escapes and its fallbacks."""

    def test_case_01_bug_with_no_flag_is_gated_next(self):
        _planned_release(self.repo)
        rc, _out, _err = _new(self.repo, slug="c1", blocks_release=None)
        self.assertEqual(rc, 0)
        text = _sole_item(self.repo).read_text(encoding="utf-8")
        self.assertIn("- Blocks-Release: next", text)
        self.assertEqual(B.parse_item(text).blocks_release, "next")

    def test_case_02_default_is_reported_on_the_human_surface(self):
        _planned_release(self.repo)
        rc, out, _err = _new(self.repo, slug="c2", blocks_release=None)
        self.assertEqual(rc, 0)
        # OQ-01 (and the maintainer's 2026-09-10 `y4adch` ruling): the notice must name the FIELD,
        # the VALUE applied, and WHY, or it is not actionable.
        self.assertIn("Blocks-Release", out)
        self.assertIn("next", out)
        self.assertIn("defaulted", out)
        self.assertIn("--blocks-release -", out)

    def test_case_03_default_is_reported_on_the_agent_surface(self):
        # THE HALF A HUMAN-ONLY NOTICE MISSES: `run_new`'s --agent/--json branch RETURNS before the
        # human write, and a runner is the most likely caller of this verb, so a notice that exists
        # only on stdout prose is invisible to the consumer that most needs it.
        _planned_release(self.repo)
        rc, out, _err = _new(
            self.repo, slug="c3", blocks_release=None, agent=True, json=False
        )
        self.assertEqual(rc, 0)
        rec = json.loads(out.strip().splitlines()[-1])
        self.assertEqual(rec["exit"], 0)
        # The COMPACT agent record does not carry `data`, so the fact rides an Evidence receipt.
        self.assertIn("blocks-release-default:next", rec["evidence"])
        # And it must NOT be reported as a finding: a normal filing is not a defect.
        self.assertEqual(rec["findings"], 0)

        # The FULL --json representation carries the machine-readable data keys too.
        rc, out, _err = _new(
            self.repo, slug="c3b", blocks_release=None, agent=False, json=True
        )
        self.assertEqual(rc, 0)
        payload = json.loads(out)
        self.assertEqual(payload["data"]["blocks_release"], "next")
        self.assertIs(payload["data"]["blocks_release_defaulted"], True)
        self.assertIn(
            "Blocks-Release", payload["data"]["blocks_release_default_notice"]
        )

    def test_case_04_explicit_dash_yields_an_ungated_bug(self):
        # A DEFAULT IS NOT A PROHIBITION. An author may deliberately file an ungated bug, and the
        # flag already distinguishes an ABSENT value from an explicit `-`.
        _planned_release(self.repo)
        rc, _out, _err = _new(self.repo, slug="c4", blocks_release="-")
        self.assertEqual(rc, 0)
        text = _sole_item(self.repo).read_text(encoding="utf-8")
        self.assertNotIn("Blocks-Release", text)
        self.assertIsNone(B.parse_item(text).blocks_release)

    def test_case_05_chore_is_not_gated(self):
        # The gating work-kind set is `bug` ALONE (parent OQ-01: `security` deliberately excluded).
        _planned_release(self.repo)
        rc, out, _err = _new(
            self.repo, slug="c5", work_kind="chore", blocks_release=None
        )
        self.assertEqual(rc, 0)
        text = _sole_item(self.repo).read_text(encoding="utf-8")
        self.assertNotIn("Blocks-Release", text)
        self.assertNotIn("defaulted", out)
        self.assertEqual(B.GATE_DEFAULT_KINDS, frozenset({"bug"}))

    def test_case_06_explicit_gate_value_is_not_overwritten(self):
        _planned_release(self.repo)
        rc, _out, _err = _new(self.repo, slug="c6", blocks_release="f33nrj")
        self.assertEqual(rc, 0)
        text = _sole_item(self.repo).read_text(encoding="utf-8")
        self.assertIn("- Blocks-Release: f33nrj", text)
        self.assertNotIn("- Blocks-Release: next", text)

    def test_case_07_no_release_record_and_absent_flag_is_ungated_exit_zero(self):
        # THE CASE WHOSE REFUSAL BROKE 10 EXISTING TESTS AT REVIEW. A fresh `aw install` creates NO
        # `.aw/records/releases/` directory, so "no planned release" is the NORMAL state of an
        # adopter repo; refusing here would make `aw backlog new --work-kind bug` fail outright in
        # every freshly installed repo. Fall back to ungated, exit 0, and SAY WHY.
        self.assertFalse((self.repo / ".aw/records/releases").exists())
        rc, out, _err = _new(self.repo, slug="c7", blocks_release=None)
        self.assertEqual(rc, 0)
        text = _sole_item(self.repo).read_text(encoding="utf-8")
        self.assertNotIn("Blocks-Release", text)
        self.assertIn("not defaulting", out)
        self.assertIn("does not resolve", out)

    def test_case_08_no_release_record_and_explicit_next_still_exits_two(self):
        # REGRESSION GUARD, NOT NEW COVERAGE: this is pre-existing SHIPPED behavior that passes both
        # before and after this change, asserted here because the fallback above must apply ONLY to
        # the ABSENT case. An explicit value the author typed and that does not resolve must still
        # refuse, or that shipped contract silently regresses.
        rc, _out, err = _new(self.repo, slug="c8", blocks_release="next")
        self.assertEqual(rc, 2)
        self.assertIn("does not resolve to a release record", err)
        self.assertEqual(
            list((self.repo / ".aw/records/backlog").rglob("*.backlog.md")), []
        )

    def test_case_09_status_done_bug_is_not_gated_and_checker_is_clean(self):
        # A GATED `done` ITEM IS A SHIPPED EXIT-BLOCKING ERROR. `--status done --work-kind bug` is
        # legal, so without this skip CREATION is the one route that manufactures the very violation
        # child 03 exists to eliminate (the setter already refuses that transition).
        _planned_release(self.repo)
        rc, out, _err = _new(self.repo, slug="c9", status="done", blocks_release=None)
        self.assertEqual(rc, 0)
        item = _sole_item(self.repo, status="done")
        text = item.read_text(encoding="utf-8")
        self.assertNotIn("Blocks-Release", text)
        self.assertIn("not defaulting", out)

        # Drive the SHIPPED checker on the created item, staged, since the rule is commit-scoped.
        env_git = ["git", "-C", str(self.repo)]
        subprocess.run(env_git + ["init", "-q"], check=True, capture_output=True)
        subprocess.run(env_git + ["add", "--", ".aw"], check=True, capture_output=True)
        self.assertEqual(CE.check_release_gate_consistency(self.repo), [])

        # COUNTERFACTUAL, so this test proves the skip is load-bearing rather than merely observing
        # a clean tree: the gate the default WOULD have written is exactly what the checker rejects.
        item.write_text(R.set_blocks_release_line(text, "next"), encoding="utf-8")
        subprocess.run(env_git + ["add", "--", ".aw"], check=True, capture_output=True)
        rules = [d.rule for d in CE.check_release_gate_consistency(self.repo)]
        self.assertIn("check.blocking-item-closed-without-gate", rules)

    def test_parked_bug_is_not_gated(self):
        # Same reason as `done`, one layer softer: a parked maybe is not live work (the attention
        # view hides it), so gating a release on one asserts an obligation nobody has taken on.
        _planned_release(self.repo)
        rc, out, _err = _new(self.repo, slug="cp", status="parked", blocks_release=None)
        self.assertEqual(rc, 0)
        text = _sole_item(self.repo, status="parked").read_text(encoding="utf-8")
        self.assertNotIn("Blocks-Release", text)
        self.assertIn("not defaulting", out)

    def test_decide_gate_default_is_the_single_shared_predicate(self):
        # The decision is consumed from THREE call sites (creation + both setter spellings). Pinning
        # the predicate directly is what keeps a future change from re-forking it per call site.
        _planned_release(self.repo)
        self.assertEqual(
            B.decide_gate_default(
                self.repo, kind="bug", status="open", explicit_blocks_release=None
            )[0],
            "next",
        )
        # An explicit value (including `-`) always wins.
        self.assertIsNone(
            B.decide_gate_default(
                self.repo, kind="bug", status="open", explicit_blocks_release="-"
            )[0]
        )
        # An existing gate is never overwritten.
        self.assertIsNone(
            B.decide_gate_default(
                self.repo,
                kind="bug",
                status="open",
                explicit_blocks_release=None,
                existing_blocks_release="f33nrj",
            )[0]
        )
        # A non-gating kind decides nothing AND says nothing.
        self.assertEqual(
            B.decide_gate_default(
                self.repo, kind="chore", status="open", explicit_blocks_release=None
            ),
            (None, None),
        )


class ReclassificationDefaultTests(_Base):
    """E-02: the gate follows a work kind BECOMING `bug`, on BOTH dispatch paths.

    `aw backlog set` forks on whether `--status` was PASSED: the positional spelling routes to
    `status_set.apply_status_change`, the `--status` spelling to `backlog.run_set`. Both are covered
    deliberately, because a default that fires for one spelling of one verb and not the other is
    worse than not shipping it: it teaches a false expectation.
    """

    def _make_chore(self, slug: str) -> Path:
        rc, _out, _err = _new(
            self.repo, slug=slug, work_kind="chore", blocks_release=None
        )
        self.assertEqual(rc, 0)
        return sorted((self.repo / ".aw/records/backlog/open").glob(f"*{slug}*"))[0]

    def test_status_spelling_defaults_the_gate_on_reclassification(self):
        _planned_release(self.repo)
        item = self._make_chore("r1")
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            rc = B.run_set(
                _args(
                    dir=str(self.repo),
                    path=str(item),
                    status="open",
                    work_kind="bug",
                    priority=None,
                    blocks_release=None,
                    message=None,
                    gate_kind=None,
                    gate_ref=None,
                    evidence=None,
                    apply=True,
                )
            )
        self.assertEqual(rc, 0)
        text = sorted((self.repo / ".aw/records/backlog/open").glob("*r1*"))[
            0
        ].read_text(encoding="utf-8")
        self.assertIn("- Blocks-Release: next", text)
        self.assertIn("- Work-Kind: bug", text)
        self.assertIn("defaulted", out.getvalue())

    def test_positional_spelling_defaults_the_gate_on_reclassification(self):
        _planned_release(self.repo)
        item = self._make_chore("r2")
        rec = _record(item, "backlog", "open")
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            SS.apply_status_change(
                rec,
                "open",
                self.repo,
                _args(
                    dir=str(self.repo),
                    work_kind="bug",
                    priority=None,
                    blocks_release=None,
                    from_backlog=None,
                    item_dependencies=None,
                    message=None,
                    actor="aw set",
                ),
            )
        text = sorted((self.repo / ".aw/records/backlog").rglob("*r2*"))[0].read_text(
            encoding="utf-8"
        )
        self.assertIn("- Blocks-Release: next", text)
        self.assertIn("- Work-Kind: bug", text)
        self.assertIn("defaulted", out.getvalue())

    def test_reclassifying_away_from_bug_leaves_an_existing_gate(self):
        # DO NOT REMOVE A GATE WHEN A WORK KIND CHANGES AWAY FROM `bug`: it may have been set
        # deliberately for another reason, and silently clearing it would lose a decision.
        _planned_release(self.repo)
        rc, _out, _err = _new(self.repo, slug="r3", blocks_release=None)
        self.assertEqual(rc, 0)
        item = sorted((self.repo / ".aw/records/backlog/open").glob("*r3*"))[0]
        self.assertIn("- Blocks-Release: next", item.read_text(encoding="utf-8"))
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            rc = B.run_set(
                _args(
                    dir=str(self.repo),
                    path=str(item),
                    status="open",
                    work_kind="chore",
                    priority=None,
                    blocks_release=None,
                    message=None,
                    gate_kind=None,
                    gate_ref=None,
                    evidence=None,
                    apply=True,
                )
            )
        self.assertEqual(rc, 0)
        text = sorted((self.repo / ".aw/records/backlog/open").glob("*r3*"))[
            0
        ].read_text(encoding="utf-8")
        self.assertIn("- Blocks-Release: next", text)
        self.assertIn("- Work-Kind: chore", text)


class GraduationInheritanceTests(_Base):
    """E-03: `aw ipd set --from-backlog` carries the item's gate onto the plan."""

    def _plan(self, id6: str = "aaa111") -> Path:
        d = self.repo / ".aw/records/plans/pending"
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"20260918-gradset-01-{id6}-graduation-target.ipd.md"
        p.write_text(
            "# IPD: Graduation target\n\n"
            "- Date: 2026-09-18\n- Kind: child\n- Status: to-review\n"
            f"- Set: gradset\n- Order: 1\n- Id: {id6}\n\n"
            "## Workflow history\n- 2026-09-18 to-review (t): authored\n",
            encoding="utf-8",
        )
        return p

    def _graduate(self, plan: Path, item_id6: "str | None", **extra):
        rec = _record(plan, "plans", "to-review")
        base = dict(
            dir=str(self.repo),
            from_backlog=item_id6,
            blocks_release=None,
            work_kind=None,
            priority=None,
            item_dependencies=None,
            message=None,
            actor="aw set",
        )
        base.update(extra)
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            SS.apply_status_change(rec, "to-review", self.repo, _args(**base))
        return out.getvalue()

    def test_case_10_ipd_set_from_backlog_inherits_the_items_gate(self):
        _planned_release(self.repo)
        rc, _out, _err = _new(self.repo, slug="g1", blocks_release=None)
        self.assertEqual(rc, 0)
        item = _sole_item(self.repo)
        item_id6 = B.parse_item(item.read_text(encoding="utf-8")).id
        plan = self._plan()
        self.assertNotIn("Blocks-Release", plan.read_text(encoding="utf-8"))

        out = self._graduate(plan, item_id6)

        text = plan.read_text(encoding="utf-8")
        self.assertIn(f"- From-Backlog: {item_id6}", text)
        self.assertIn("- Blocks-Release: next", text)
        self.assertIn("inherited", out)
        # ONE metadata line, at the shared writer's canonical position (directly after `- Status:`),
        # proving it went through `releases.set_blocks_release_line` and not a second writer.
        self.assertEqual(len(re.findall(r"(?m)^- Blocks-Release:", text)), 1)
        lines = text.splitlines()
        self.assertEqual(
            lines[lines.index("- Status: to-review") + 1], "- Blocks-Release: next"
        )
        # And the tree is consistent: the carrier's gate MATCHES the item's.
        self.assertEqual(
            [
                d.rule
                for d in CE.check_release_gate_consistency(self.repo)
                if d.rule == "check.from-backlog-gate-mismatch"
            ],
            [],
        )

    def test_ungated_item_leaves_the_plan_ungated(self):
        _planned_release(self.repo)
        rc, _out, _err = _new(self.repo, slug="g2", blocks_release="-")
        self.assertEqual(rc, 0)
        item_id6 = B.parse_item(_sole_item(self.repo).read_text(encoding="utf-8")).id
        plan = self._plan()
        self._graduate(plan, item_id6)
        text = plan.read_text(encoding="utf-8")
        self.assertIn(f"- From-Backlog: {item_id6}", text)
        self.assertNotIn("Blocks-Release", text)

    def test_explicit_blocks_release_in_the_same_call_wins(self):
        _planned_release(self.repo)
        rc, _out, _err = _new(self.repo, slug="g3", blocks_release=None)
        self.assertEqual(rc, 0)
        item_id6 = B.parse_item(_sole_item(self.repo).read_text(encoding="utf-8")).id
        plan = self._plan()
        self._graduate(plan, item_id6, blocks_release="f33nrj")
        text = plan.read_text(encoding="utf-8")
        self.assertIn("- Blocks-Release: f33nrj", text)
        self.assertNotIn("- Blocks-Release: next", text)

    def test_existing_carrier_gate_is_never_overwritten(self):
        # A plan may legitimately gate a release its originating item never knew about (the shipped
        # asymmetry: the mismatch rule protects against a DROPPED handoff, not a better-informed
        # plan). Overwriting would silently discard that decision.
        _planned_release(self.repo)
        rc, _out, _err = _new(self.repo, slug="g4", blocks_release=None)
        self.assertEqual(rc, 0)
        item_id6 = B.parse_item(_sole_item(self.repo).read_text(encoding="utf-8")).id
        plan = self._plan()
        plan.write_text(
            R.set_blocks_release_line(plan.read_text(encoding="utf-8"), "f33nrj"),
            encoding="utf-8",
        )
        self._graduate(plan, item_id6)
        text = plan.read_text(encoding="utf-8")
        self.assertIn("- Blocks-Release: f33nrj", text)
        self.assertEqual(len(re.findall(r"(?m)^- Blocks-Release:", text)), 1)

    def test_clearing_from_backlog_writes_no_gate(self):
        plan = self._plan()
        self._graduate(plan, "-")
        text = plan.read_text(encoding="utf-8")
        self.assertNotIn("From-Backlog", text)
        self.assertNotIn("Blocks-Release", text)

    def test_blocks_release_of_item_lookup(self):
        _planned_release(self.repo)
        rc, _out, _err = _new(self.repo, slug="g5", blocks_release=None)
        self.assertEqual(rc, 0)
        item_id6 = B.parse_item(_sole_item(self.repo).read_text(encoding="utf-8")).id
        self.assertEqual(B.blocks_release_of_item(self.repo, item_id6), "next")
        self.assertIsNone(B.blocks_release_of_item(self.repo, "zzzzzz"))
        self.assertIsNone(B.blocks_release_of_item(self.repo, "-"))


if __name__ == "__main__":
    unittest.main()
