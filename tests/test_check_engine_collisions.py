"""WHICH CORPUS each collision rule sees, and what a per-type check owes its caller (IPD sk7ggr).

THIS MODULE IS ABOUT ENUMERATION, NOT ABOUT THE RULES THEMSELVES. `tests/test_check_engine.py`
already owns the table that says WHICH findings each fixture produces. What was untested, and what
broke in production, is WHICH FILES the rules are run over, so every test here varies the corpus and
holds the fixture fixed.

THE DEFECT. `check_collisions` emits THREE rules from ONE enumeration, and that enumeration honored
the engine's default liveness filter, which skips retired artifacts. For most rules that default is
right (a finished plan's own conformance is nobody's action item); FOR IDENTITY IT IS WRONG, because a
terminal artifact's id6 is permanently cited across the repository. Measured consequence: `aw check
all` reported one id6-collision and MISSED the one whose other side sits in `executed/`, while `aw
doctor` (which passes `include_retired=True` unconditionally) reported it. Two surfaces disagreeing
about what identity IS was the defect.

WHY THE FIX HAD TO BE NARROW, which is the hardest property in this file to hold. Widening the shared
enumeration wholesale ALSO moves the other two rules: measured, `check.setid-collision` 39 -> 86
(overwhelmingly the LEGITIMATE pattern of a backlog item sharing a setid with the plan it graduated
into, a policy question owned by backlog `sjsoqq`) plus two `check.id6-identity-slot` FALSE POSITIVES
(walkthroughs whose filename slot carries their own plan's id6, the documented convention). So the
load-bearing assertions here are NEGATIVE: they say the two neighbouring rules did NOT gain findings.
"""

from __future__ import annotations

import collections
import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce

ID6_COLLISION = "check.id6-collision"
SETID_COLLISION = "check.setid-collision"
IDENTITY_SLOT = "check.id6-identity-slot"
NOT_CHECKED = "check.collisions-not-checked"

PLANS_PENDING = ".aw/records/plans/pending"
PLANS_EXECUTED = ".aw/records/plans/executed"
SPECS = ".aw/records/specs"
BACKLOG_DONE = ".aw/records/backlog/done"
WALK = ".aw/records/walkthroughs"


def _plan_text(id6, setid="demo", desc=None, status="approved"):
    setline = f"{setid} ({desc})" if desc else setid
    return (
        f"# IPD\n\n- Id: {id6}\n- Status: {status}\n- Set: {setline}\n\n## Goal\n\nx\n"
    )


def _spec_text(id6, setid="demo", desc=None, status="draft"):
    setline = f"{setid} ({desc})" if desc else setid
    return (
        f"# Spec\n\n- Id: {id6}\n- Status: {status}\n- Set: {setline}\n\n## Body\n\nx\n"
    )


def _tree(files):
    root = Path(tempfile.mkdtemp())
    (root / ".git").mkdir()
    for rel, text in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


def _by_rule(drift):
    return collections.Counter(d.rule for d in drift)


class TerminalArtifactCollisionTests(unittest.TestCase):
    """An id6 collision involving a TERMINAL artifact is reported WITHOUT `--all` (E-05).

    ONE table over the terminal dispositions, because the claim is one property measured against each
    spelling of "retired": the id6 pass must ignore the liveness filter entirely. Rows rather than
    separate tests because a regression here (someone restoring `include_retired=include_retired` on
    the enumeration) breaks every row at once, and the table names which dispositions were affected.
    """

    #: (case, the two files, the shared id6, why this row exists)
    PAIRS = (
        (
            "a live plan colliding with an EXECUTED plan",
            (
                (
                    f"{PLANS_PENDING}/20260101-demo-01-dup111-live.ipd.md",
                    _plan_text("dup111"),
                ),
                (
                    f"{PLANS_EXECUTED}/20260101-demo-02-dup111-old.ipd.md",
                    _plan_text("dup111", status="executed"),
                ),
            ),
            "dup111",
            "THE MEASURED REAL CASE's shape (`uyeko5`): the default sweep saw only the live side and "
            "reported nothing, while `aw doctor` reported it. An executed plan's id6 appears in "
            "Item-Dependencies, From-Backlog, review filenames and prose forever, so reusing it "
            "silently redirects every one of those citations",
        ),
        (
            "a live spec colliding with a DONE backlog item",
            (
                (f"{SPECS}/20260101-dup222-01-dup222-s.spec.md", _spec_text("dup222")),
                (
                    f"{BACKLOG_DONE}/20260101-demo-01-dup222-b.backlog.md",
                    "- Id: dup222\n- Status: done\n- Set: demo\n- Priority: medium\n"
                    "- Work-Kind: feature\n- Summary: x\n\n## Detail\n\nx\n",
                ),
            ),
            "dup222",
            "a SECOND retirement spelling (`done/`) in a different pair of trees, so the property is "
            "about retirement in general rather than about the `executed/` directory name",
        ),
        (
            "a live plan colliding with a plan whose STATUS is executed but whose directory is not",
            (
                (
                    f"{PLANS_PENDING}/20260101-demo-01-dup333-live.ipd.md",
                    _plan_text("dup333"),
                ),
                (
                    f"{PLANS_PENDING}/20260101-demo-02-dup333-stale.ipd.md",
                    _plan_text("dup333", status="executed"),
                ),
            ),
            "dup333",
            "retirement has TWO independent mechanisms (directory segment AND frontmatter status), and "
            "`is_retired` honors both, so a fix that special-cased only the directory would leave this "
            "row unreported",
        ),
    )

    def test_a_terminal_collision_is_reported_by_default(self):
        for case, files, shared, why in self.PAIRS:
            with self.subTest(case=case):
                root = _tree(files)
                counts = _by_rule(ce.check_collisions(root))
                self.assertEqual(
                    counts[ID6_COLLISION],
                    1,
                    f"{case}: expected exactly ONE {ID6_COLLISION} from the DEFAULT sweep (no "
                    f"include_retired), got {counts[ID6_COLLISION]}. Findings: {dict(counts)}. "
                    f"WHY: {why}",
                )

    def test_the_finding_names_both_sides(self):
        """A collision finding is unactionable unless it names the OTHER file.

        Separate from the table because it asserts the DETAIL's content rather than the corpus.
        """

        root = _tree(self.PAIRS[0][1])
        found = [d for d in ce.check_collisions(root) if d.rule == ID6_COLLISION]
        self.assertEqual(len(found), 1, f"expected one finding, got {found}")
        self.assertIn(
            "dup111",
            found[0].detail,
            "the detail must name the colliding id6",
        )
        self.assertIn(
            "old.ipd.md",
            found[0].detail,
            "the detail must name the OTHER file (the terminal one), or a user knows there is a clash "
            "without knowing what with - and cannot tell it involves a terminal artifact at all",
        )

    def test_doctor_and_check_now_agree(self):
        """The two surfaces must not disagree about what a collision IS.

        Separate because the claim is about EQUIVALENCE of two corpora rather than about one result:
        `aw doctor` passes `include_retired=True` unconditionally and `aw check` did not, which is the
        precise mechanism by which the live collision stayed invisible on the command people run.
        """

        root = _tree(self.PAIRS[0][1])
        default = sorted(
            d.location for d in ce.check_collisions(root) if d.rule == ID6_COLLISION
        )
        retired = sorted(
            d.location
            for d in ce.check_collisions(root, include_retired=True)
            if d.rule == ID6_COLLISION
        )
        self.assertEqual(
            default,
            retired,
            "the id6-collision SET must be identical with and without include_retired, because that "
            "flag is what `aw check all` and `aw doctor` differ by. If these diverge, the two surfaces "
            "disagree about identity again",
        )


class NeighbouringRulesMustNotWidenTests(unittest.TestCase):
    """The setid and identity-slot passes keep the CALLER's corpus (E-05, the negative assertions).

    THESE ARE THE TESTS THAT STOP THE FIX FROM BECOMING A REGRESSION. One enumeration feeds three
    rules, so the obvious implementation (hoist `include_retired=True` onto the loop) fixes the id6
    rule and simultaneously ships +47 setid findings that belong to `sjsoqq` plus two false-positive
    walkthrough slot findings. Each test below fails if that happens.
    """

    def test_a_retired_setid_conflict_stays_invisible_by_default(self):
        root = _tree(
            [
                (
                    f"{PLANS_PENDING}/20260101-demo-01-aaa111-a.ipd.md",
                    _plan_text("aaa111", setid="demo", desc="Alpha"),
                ),
                (
                    f"{PLANS_EXECUTED}/20260101-demo-02-bbb222-b.ipd.md",
                    _plan_text("bbb222", setid="demo", desc="Beta", status="executed"),
                ),
            ]
        )
        default = _by_rule(ce.check_collisions(root))
        self.assertEqual(
            default[SETID_COLLISION],
            0,
            "a setid descriptive conflict with a RETIRED plan must NOT be reported by default. "
            "Reporting it is the +47-finding batch this plan's scope explicitly declined to own "
            f"(owned by backlog `sjsoqq`). Got: {dict(default)}",
        )
        asked = _by_rule(ce.check_collisions(root, include_retired=True))
        self.assertEqual(
            asked[SETID_COLLISION],
            1,
            "...but it MUST still be reported when the caller explicitly asks for retired records, or "
            f"the widening broke the setid rule instead of scoping it. Got: {dict(asked)}",
        )

    def test_a_retired_walkthrough_slot_finding_stays_invisible_by_default(self):
        """The walkthrough-names-its-plan's-id6 convention must not become a finding.

        A walkthrough carries its PLAN's id6 in the filename slot while declaring no `- Id:`, which is
        the documented convention and exactly what identity-slot rule (b) would flag. Two real
        instances exist in this repository, so a wholesale widening surfaces two false positives.
        """

        root = _tree(
            [
                (
                    f"{PLANS_EXECUTED}/20260101-demo-01-ccc333-p.ipd.md",
                    _plan_text("ccc333", status="executed"),
                ),
                (
                    f"{WALK}/20260101-demo-01-ccc333-w.walkthrough.md",
                    "# Walkthrough\n\n- Date: 20260101\n\n## Summary\n\nx\n",
                ),
            ]
        )
        default = _by_rule(ce.check_collisions(root))
        self.assertEqual(
            default[IDENTITY_SLOT],
            0,
            "a walkthrough carrying its (retired) plan's id6 in the filename slot is the documented "
            f"convention, NOT a defect, and must not be reported by default. Got: {dict(default)}",
        )


class DeclaredDuplicateIsReportedExactlyOnceTests(unittest.TestCase):
    """D140's declared-duplicate shape yields ONE finding, not two (E-03, OQ-01).

    THE BLIND SPOT IS REAL: `_check_identity_slots` returns ZERO findings for two files of different
    types that both DECLARE and both SLOT the same id6, because rule (a) compares each file's slot to
    its OWN declared Id (they agree) and rule (b) is skipped for any file that declares an Id.

    THE RESOLUTION WAS "SURFACE IT, DO NOT DUPLICATE IT". The fact is already reported by the
    `seen_ids` pass as one `check.id6-collision`, which is the correct and sufficient finding; the
    reason the live instance was invisible was the retired filter (E-05) and an unbounded parser (owned
    by `76w6mq`), never a missing rule. Emitting a second finding for one fact would hand an operator
    two remedies for one problem, so these tests pin the ONE-finding outcome in both directions.
    """

    def test_a_declared_duplicate_across_types_yields_exactly_one_finding(self):
        root = _tree(
            [
                (
                    f"{PLANS_PENDING}/20260101-dup444-01-dup444-p.ipd.md",
                    _plan_text("dup444"),
                ),
                (f"{SPECS}/20260101-dup444-01-dup444-s.spec.md", _spec_text("dup444")),
            ]
        )
        counts = _by_rule(ce.check_collisions(root))
        self.assertEqual(
            counts[ID6_COLLISION],
            1,
            f"the declared duplicate must be reported once. Got: {dict(counts)}",
        )
        self.assertEqual(
            counts[IDENTITY_SLOT],
            0,
            "the identity-slot rule must NOT also fire for the same fact: two findings for one "
            "problem give an operator two remedies and no way to choose. If this starts failing, a "
            f"declared-duplicate case was added to `_check_identity_slots`. Got: {dict(counts)}",
        )

    def test_the_identity_slot_rule_still_catches_a_FOREIGN_slot_id6(self):
        """The negative control: scoping the slot rule must not disable it.

        Without this, an implementation that simply deleted the slot rule would satisfy every
        no-double-reporting assertion above.
        """

        root = _tree(
            [
                (
                    f"{PLANS_PENDING}/20260101-demo-01-own111-p.ipd.md",
                    _plan_text("own111"),
                ),
                (
                    f"{WALK}/20260101-demo-01-own111-w.walkthrough.md",
                    "# Walkthrough\n\n- Date: 20260101\n- Id: oth222\n\n## Summary\n\nx\n",
                ),
            ]
        )
        counts = _by_rule(ce.check_collisions(root))
        self.assertEqual(
            counts[IDENTITY_SLOT],
            1,
            "a file whose filename slot holds ANOTHER file's id6 while declaring a different Id of its "
            f"own is a genuine D140 violation and must still be reported. Got: {dict(counts)}",
        )

    def test_a_conformant_pair_and_legacy_slug_names_are_not_mass_flagged(self):
        """The `_is_real_id6` discriminator is load-bearing and must survive.

        It exists because legacy slugs whose first word matches `[0-9a-z]{6}` (`assess`, `agents`)
        were being flagged wholesale. A change that widened the slot rule without preserving it would
        mass-flag conformant history.
        """

        root = _tree(
            [
                (
                    f"{PLANS_PENDING}/20260101-demo-01-fine11-a.ipd.md",
                    _plan_text("fine11"),
                ),
                (f"{SPECS}/20260101-fine22-01-fine22-b.spec.md", _spec_text("fine22")),
                (
                    f"{PLANS_EXECUTED}/20260101-assess-00-assess-documentation.ipd.md",
                    "# IPD: legacy\n\n- Status: executed\n\n## Goal\n\nx\n",
                ),
            ]
        )
        counts = _by_rule(ce.check_collisions(root))
        self.assertEqual(
            counts[ID6_COLLISION],
            0,
            f"distinct conformant ids must produce no collision. Got: {dict(counts)}",
        )
        self.assertEqual(
            counts[IDENTITY_SLOT],
            0,
            "a legacy name whose slug's first word merely LOOKS like an id6 (`assess`) must not be "
            f"flagged. Got: {dict(counts)}",
        )


class PerTypeCheckStatesItsLimitTests(unittest.TestCase):
    """A per-type `aw check <type>` must not imply collision-clean (E-06).

    MEASURED DEFECT: `aw check research` reported `errors 0 warnings 0` and exited 0 over a tree that
    held a real id6 collision, because the collision scan is gated on the `all` target. An author who
    checks the type they just wrote was told they were fine. A SILENT clean bill of health is the
    failure mode, so the fix is to SAY the limit.
    """

    def test_a_per_type_run_says_collisions_were_not_examined(self):
        root = _tree(
            [
                (
                    f"{PLANS_PENDING}/20260101-demo-01-aaa111-a.ipd.md",
                    _plan_text("aaa111"),
                )
            ]
        )
        drift = ce.check_types(root, ["plans"])
        notices = [d for d in drift if d.rule == NOT_CHECKED]
        self.assertEqual(
            len(notices),
            1,
            f"a per-type check must emit exactly one {NOT_CHECKED} notice. Got: "
            f"{dict(_by_rule(drift))}",
        )
        # The REMEDY must be present, but it lives in `required`/`recovery` rather than in `detail`.
        # WHY THE SPLIT: `doctor.build_remediation` has no case for this rule and its generic fallback
        # uses `detail` as the human report's TITLE only when it is under 60 characters, so `detail` is
        # kept short on purpose and the explanation moves to the structured fields. Asserting across
        # all three is what keeps the remedy reachable no matter which surface a caller reads.
        self.assertIn(
            "aw check all",
            f"{notices[0].detail} {notices[0].observed} {notices[0].required} {notices[0].recovery}",
            "the notice must name the command that DOES check, or it reports a limitation without a "
            "remedy",
        )
        self.assertEqual(
            notices[0].recovery,
            "aw check all",
            "the machine-readable recovery field must carry the exact command, since that is what "
            "agent-mode consumers act on",
        )
        self.assertIn(
            "does NOT mean collision-clean",
            notices[0].observed,
            "the notice must say plainly that a clean per-type result is not a collision-clean result; "
            "that sentence IS the removal of the false clean",
        )

    def test_the_notice_is_info_and_does_not_fail_the_gate(self):
        """The limit must be stated WITHOUT inventing a failure.

        A per-type run that examines no collisions is behaving correctly, so this must not turn a
        clean check red; `drift_exit_code` ignores `info`. If this becomes an error, every per-type
        check in every consumer and hook starts failing.
        """

        from agent_workflows import artifact_core as core

        root = _tree(
            [
                (
                    f"{PLANS_PENDING}/20260101-demo-01-aaa111-a.ipd.md",
                    _plan_text("aaa111"),
                )
            ]
        )
        drift = ce.check_types(root, ["plans"])
        notice = [d for d in drift if d.rule == NOT_CHECKED][0]
        self.assertEqual(notice.severity, "info", "the notice must be info-severity")
        self.assertEqual(
            core.drift_exit_code([notice]),
            0,
            "an info-severity notice must not drive a nonzero exit code",
        )

    def test_the_full_sweep_does_NOT_emit_the_notice(self):
        """`aw check all` runs the scan, so claiming it did not would be a lie.

        The mirror of the test above, and it is what keeps the notice honest rather than boilerplate.
        """

        root = _tree(
            [
                (
                    f"{PLANS_PENDING}/20260101-demo-01-aaa111-a.ipd.md",
                    _plan_text("aaa111"),
                )
            ]
        )
        drift = ce.check_types(root, ["all"])
        self.assertEqual(
            [d for d in drift if d.rule == NOT_CHECKED],
            [],
            "the full sweep DOES examine collisions, so it must not claim otherwise",
        )

    def test_a_per_type_run_over_a_colliding_tree_still_reports_no_collision(self):
        """The HONEST statement of what E-06 does and does not fix.

        E-06 removes the false CLEAN, not the blindness: a per-type run still does not perform the
        cross-tree scan (OQ-02 left running it to the maintainer as a cost decision). This test pins
        that so nobody reads the notice as "per-type now checks collisions".
        """

        root = _tree(
            [
                (
                    f"{PLANS_PENDING}/20260101-dup555-01-dup555-p.ipd.md",
                    _plan_text("dup555"),
                ),
                (f"{SPECS}/20260101-dup555-01-dup555-s.spec.md", _spec_text("dup555")),
            ]
        )
        drift = ce.check_types(root, ["plans"])
        self.assertEqual(
            _by_rule(drift)[ID6_COLLISION],
            0,
            "a per-type run still does not scan for collisions; if it now does, OQ-02 was resolved "
            "differently and this test should be updated to match",
        )
        self.assertEqual(
            len([d for d in drift if d.rule == NOT_CHECKED]),
            1,
            "...which is exactly why the notice must be present: this tree DOES hold a collision",
        )


if __name__ == "__main__":
    unittest.main()
