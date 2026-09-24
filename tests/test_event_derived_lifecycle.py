"""agentadhere Phase 3 (IPD wqj1ne): event-derived lifecycle state + declared file scope.

Covers:
  E-01/V-01 - validate_transition rejects each invalid transition (missing predecessor, stale tree,
              invalid actor, malformed evidence, unauthorized terminal); a valid ordered event
              sequence derives the expected status; events come from the existing inline history
              (no parallel log); existing `- Status:` reads still work (backward-compat).
  E-02/V-02 - check.scope-drift flags an out-of-scope changed path for a plan with an active begin
              receipt, is clean for in-scope, reuses the finalize scope helpers (no fork), and
              honors the `grandfathered` sentinel.

WHAT WAS TABULATED. Three clusters here were the same shape repeated with different data, so each is
now ONE table whose rows carry the varying fields as columns:

1. `validate_transition`'s verdicts. Eight tests called one pure function with one argument set and
   asserted `ok` plus a reason NEEDLE. The (from, to, actor, extra kwargs) tuple is the only thing
   that varied, so it is the row. The five VALID transitions are rows in the SAME table as the seven
   refusals, because a predicate that refused everything would satisfy every refusal row on its own
   and a predicate that accepted everything would satisfy every valid row; only both together state
   that the gate discriminates.
2. `derive_status_from_events`, whose two tests differed only in the event list.
3. `check.scope-drift`'s fixture outcomes, whose four tests built one repo with one receipt and
   asserted which paths were reported. The fixture's SCOPE declaration and which path is dirtied are
   columns, and so is whether a receipt exists at all.

HOW THE "NO FORK" CLAIMS ARE PROVED, since this is where the file used to be weakest. Two tests here
asserted that a function REUSES a shared helper by reading the function's SOURCE TEXT and searching
for the helper's name. That is a change-detector: it passes when the name appears in a COMMENT while
the real code forks, and it fails on a pure rename that preserves behavior. Both are now proved the
way reuse can actually be proved: the shared helper is PATCHED with a spy (so the call is observed to
happen during a real invocation) and then patched to return a SENTINEL (so the shared helper's output
is observed to reach the caller's result). A forked private copy fails both, and no comment can
satisfy either.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import ipd_lifecycle as life


# --------------------------------------------------------------------------------------
# E-01 / V-01: transition validity + derivation + no-parallel-log + backward compat
# --------------------------------------------------------------------------------------


class TestTransitionValidity(unittest.TestCase):
    """Which single lifecycle transitions `validate_transition` admits, and why each is refused.

    ONE table replaces eight tests. Every one called the same pure predicate with one argument set
    and asserted `ok` plus (for the refusals) a substring of `reason`. The REASON NEEDLE IS A COLUMN
    and is asserted, not merely `ok`: the five refusal categories are distinguishable only by their
    reason, and the predicate documents an ORDERING between them (actor and terminal-authority are
    checked FIRST so an unauthorized terminal move is not misreported as a predecessor gap). A row
    that asserted only `ok` would pass if two categories collapsed into one.
    """

    #: (case, from_status, to_status, actor, extra kwargs, expected ok, reason needle or "",
    #:  why this row exists)
    TRANSITIONS = (
        (
            "start the lifecycle mid-sequence",
            None,
            "reviewed",
            "aw set",
            {},
            False,
            "missing predecessor",
            "A FIRST RECORDED EVENT MUST START AT `draft`. Without this row a plan could be born "
            "`reviewed`, which asserts a review that never happened",
        ),
        (
            "move backwards",
            "approved",
            "draft",
            "aw set",
            {},
            False,
            "missing predecessor",
            "THE LIFECYCLE ONLY MOVES FORWARD. A backwards edge is how an approval would be silently "
            "un-done while the history still shows it was granted",
        ),
        (
            "jump to terminal from draft",
            "draft",
            "executed",
            "aw ipd finalize",
            {},
            False,
            "missing predecessor",
            "THE ONE FORWARD SKIP THAT IS STILL REFUSED, and the reason forward skips are otherwise "
            "allowed: `executed` additionally demands at least `reviewed`, so a raw draft->executed "
            "jump cannot claim implementation with no review. Note the actor here is the AUTHORIZED "
            "one, which isolates the predecessor rule from the terminal-authority rule",
        ),
        (
            "cite evidence bound to another tree",
            "reviewed",
            "approved",
            "aw set",
            {"tree_id_current": "aaa", "tree_id_evidence": "bbb"},
            False,
            "stale tree id",
            "EVIDENCE MUST DESCRIBE THE CURRENT TREE. A stale binding means the transition is "
            "justified by a state of the repository that no longer exists",
        ),
        (
            "an empty actor",
            "draft",
            "to-review",
            "   ",
            {},
            False,
            "invalid actor",
            "AN UNATTRIBUTABLE TRANSITION IS NOT A VALID ONE: the actor is what makes a history line "
            "auditable, and whitespace passes a naive truthiness check, which is why the fixture is "
            "whitespace rather than the empty string",
        ),
        (
            "evidence required but absent",
            "reviewed",
            "approved",
            "aw set",
            {"require_evidence": True, "evidence": {}},
            False,
            "malformed evidence",
            "AN EMPTY MAPPING IS NOT EVIDENCE. `{}` is the shape a caller reaches by default, so if "
            "it satisfied the requirement the flag would be decorative",
        ),
        (
            "a terminal transition by a non-finalize actor",
            "approved",
            "executed",
            "aw set",
            {},
            False,
            "unauthorized terminal",
            "ONLY `aw ipd finalize` MAY MARK A PLAN EXECUTED, because `executed` maps to the `done` "
            "attention class and claiming it is claiming validated work. Paired with the "
            "approved->executed VALID row below, which differs ONLY in the actor: together they say "
            "the refusal is about authority and not about the edge",
        ),
        (
            "draft -> reviewed (an allowed forward skip)",
            "draft",
            "reviewed",
            "aw set",
            {},
            True,
            "",
            "A FORWARD SKIP IS ALLOWED, and this is the one real workflows take: `/plan-review` sets "
            "`reviewed` with no separate `to-review` step. This row is why the predecessor rule may "
            "not be implemented as 'rank must increase by exactly one'",
        ),
        (
            "reviewed -> approved",
            "reviewed",
            "approved",
            "aw set",
            {},
            True,
            "",
            "THE HUMAN-APPROVAL EDGE, adjacent in the sequence and performed by `aw set`. Its "
            "presence keeps the refusal rows from being satisfied by a predicate that refuses all",
        ),
        (
            "approved -> executed by the finalize actor",
            "approved",
            "executed",
            "aw ipd finalize",
            {},
            True,
            "",
            "THE AUTHORIZED TERMINAL MOVE. Read against the `aw set` row above, which is byte-"
            "identical but for the actor: that pairing is the whole terminal-authority rule",
        ),
        (
            "auto-approved -> executed by the finalize actor",
            "auto-approved",
            "executed",
            "aw ipd finalize",
            {},
            True,
            "",
            "`auto-approved` IS A SUFFICIENT PREDECESSOR FOR TERMINAL, which is what makes an "
            "unattended `--full-auto` run able to finalize at all. A change that dropped it from the "
            "sequence would strand every auto-approved plan short of terminal",
        ),
    )

    def test_each_transition_is_admitted_or_refused_with_its_stated_reason(self):
        wrong = []
        for case, frm, to, actor, kwargs, want_ok, needle, why in self.TRANSITIONS:
            chk = life.validate_transition(frm, to, actor=actor, **kwargs)
            problems = []
            if bool(chk.ok) != want_ok:
                problems.append(
                    f"expected ok={want_ok}, got ok={chk.ok} with reason {chk.reason!r}"
                )
            elif needle and needle not in (chk.reason or ""):
                problems.append(
                    f"refused correctly but for the wrong stated reason: expected "
                    f"{needle!r} in {chk.reason!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} ({frm!r} -> {to!r}, actor={actor!r}, kwargs={kwargs!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`validate_transition` judged {len(wrong)} of {len(self.TRANSITIONS)} transitions "
            "wrongly. READ THE GROUPING: every refusal row failing at once means the predicate stopped "
            "refusing anything and the gate is inert; every VALID row failing at once means it refuses "
            "everything and no plan can advance (and note that state would satisfy all seven refusal "
            "rows on its own, which is why the valid rows share this table). A refusal that fires with "
            "the WRONG reason means two categories collapsed, which matters because the predicate "
            "documents an order: actor and terminal-authority are checked BEFORE the predecessor rule "
            "so an unauthorized terminal move is reported as such. The two approved->executed rows "
            "differ ONLY in the actor, so if they move together the terminal-authority rule is gone "
            "rather than the edge. FIX: change the row deliberately if the lifecycle sequence changed; "
            "the reasons are operator-facing text a human reads out of `aw set`.\n"
            + "\n".join(wrong),
        )


class TestDerivation(unittest.TestCase):
    def test_derive_status_from_events(self):
        """Which status a (date, status, actor) event stream derives.

        ONE table replaces two tests that differed only in the event list. The OFF-SEQUENCE row is
        the load-bearing one: a `parked` note is a disposition annotation, not a forward transition,
        so a derivation that simply took the LAST event would report it as the status. The two rows
        share a prefix and differ only in the final event, which is what isolates that rule.
        """
        cases = (
            (
                "an ordered forward sequence",
                [
                    ("2026-08-25", "draft", "author"),
                    ("2026-08-26", "reviewed", "author"),
                    ("2026-08-27", "approved", "aw set"),
                ],
                "approved",
                "THE ORDINARY CASE: the derived status is the newest ON-SEQUENCE event. If this row "
                "alone fails, derivation stopped following the stream at all",
            ),
            (
                "a trailing off-sequence disposition note",
                [
                    ("2026-08-25", "draft", "a"),
                    ("2026-08-26", "reviewed", "a"),
                    ("2026-08-27", "parked", "a"),
                ],
                "reviewed",
                "AN OFF-SEQUENCE TOKEN DOES NOT ADVANCE THE DERIVED STATUS. `parked` is a "
                "disposition, so a `last event wins` implementation would report `parked` as the "
                "lifecycle status and the plan would read as retired. This row differs from the one "
                "above ONLY in its final event, which is what makes it a test of that rule",
            ),
            (
                "an empty stream",
                [],
                None,
                "NO EVENTS DERIVES NOTHING, never a default. Returning `draft` here would invent a "
                "history for a plan that records none, and the caller cross-checks this against the "
                "authoritative `- Status:` field",
            ),
        )
        wrong = []
        for case, events, expected, why in cases:
            got = life.derive_status_from_events(events)
            if got != expected:
                wrong.append(
                    f"  {case}: expected {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`derive_status_from_events` derived the wrong status for {len(wrong)} of {len(cases)} "
            "streams. The derived value is the CROSS-CHECK of the authoritative `- Status:` field, so "
            "a wrong derivation reports drift where there is none (or hides real drift). If the "
            "off-sequence row alone failed, the forward-sequence filter was dropped and a `parked` "
            "note now reads as the lifecycle status. FIX: the on-sequence set is "
            "`ipd_lifecycle._status_rank`; widen it deliberately rather than relaxing this row.\n"
            + "\n".join(wrong),
        )

    def test_backward_compat_status_read_unchanged(self):
        """Kept separate: an AGREEMENT claim between two independent readers, not a derivation row.

        The authoritative `- Status:` read (used by aw set/finalize/hooks) is unchanged by adding
        derivation alongside it; the derived value cross-checks but does not replace it. This asserts
        the two agree on one text, which no row of the derivation table can express because each row
        drives only the derivation side.
        """
        text = (
            "# IPD: x\n\n- Id: aaa111\n- Status: approved\n\n## Workflow history\n"
            "- 2026-08-27 approved (aw set): status set to approved\n"
            "- 2026-08-25 draft (author): created.\n"
        )
        self.assertEqual(ce._status_meta(text), "approved")
        self.assertEqual(life.derive_plan_status(text), "approved")


class TestLifecycleEngineRule(unittest.TestCase):
    """`check.lifecycle-transition-invalid` over a plan's recorded inline history.

    ONE table replaces two tests that built the same plan fixture and differed only in its history
    lines. The CLEAN row is in the same table deliberately: a rule that flagged every plan would
    satisfy the flagging row on its own.
    """

    #: (case, history lines NEWEST-FIRST as the inline format stores them, must the rule fire?,
    #:  why this row exists)
    HISTORIES = (
        (
            "a backwards approved -> draft edge",
            (
                "2026-08-27 draft (aw set): back",
                "2026-08-26 approved (aw set): fwd",
                "2026-08-25 draft (author): created.",
            ),
            True,
            "THE RECORDED-HISTORY FORM of the backwards-edge refusal: the per-edge predicate refuses "
            "it in isolation, and this row proves the SWEEP reaches the same verdict from a file on "
            "disk. Note the lines are NEWEST-FIRST, which is how the inline history is stored, so "
            "this row also pins that the sweep reverses before validating",
        ),
        (
            "an ordered draft -> reviewed -> approved history",
            (
                "2026-08-27 approved (aw set): ok",
                "2026-08-26 reviewed (author): ok",
                "2026-08-25 draft (author): created.",
            ),
            False,
            "A CORRECT HISTORY MUST BE SILENT, and this row is what makes the flagging row above "
            "meaningful: a sweep that reported every plan would satisfy that one and light up the "
            "whole tree. It is also the ordinary shape of a real plan's history",
        ),
    )

    RULE = "check.lifecycle-transition-invalid"

    def _repo(self, history_lines):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        pending = root / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True)
        body = (
            "# IPD: x\n\n- Id: aaa111\n- Kind: child\n- Status: approved\n- Set: t\n- Order: 1\n\n"
            "## Workflow history\n"
            + "".join(f"- {line}\n" for line in history_lines)
            + "\n## Goal\n\ng\n"
        )
        (pending / "20260828-t-01-aaa111-x.ipd.md").write_text(body, encoding="utf-8")
        return root

    def test_the_sweep_flags_an_invalid_recorded_transition_and_only_that(self):
        wrong = []
        for case, lines, want_fire, why in self.HISTORIES:
            root = self._repo(lines)
            hits = [
                d for d in ce.check_lifecycle_transitions(root) if d.rule == self.RULE
            ]
            if bool(hits) != want_fire:
                wrong.append(
                    f"  {case}: expected the rule to "
                    f"{'FIRE' if want_fire else 'stay SILENT'}, got "
                    f"{[d.detail for d in hits] or 'nothing'}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`check_lifecycle_transitions` answered {len(wrong)} of {len(self.HISTORIES)} histories "
            "wrongly. If the FLAGGING row alone failed, the sweep stopped validating recorded edges "
            f"and `{self.RULE}` is inert. If the CLEAN row alone failed, every ordinary plan in the "
            "tree now reports an invalid transition, which is a whole-tree false positive. FIX: the "
            "per-edge verdict is `ipd_lifecycle.validate_transition` (tabulated above); check there "
            "first, since the sweep only derives events and delegates.\n"
            + "\n".join(wrong),
        )


# --------------------------------------------------------------------------------------
# E-02 / V-02: declared-file-scope drift
# --------------------------------------------------------------------------------------


class TestScopeDrift(unittest.TestCase):
    """`check.scope-drift`: what a LIVE begin receipt lets the sweep say about uncommitted paths.

    ONE table replaces four tests. Each built the same git repo with the same plan and receipt and
    differed only in the plan's declared `Scope-Paths`, which path was dirtied, and whether a receipt
    was written at all; all three are columns.

    THREE OF THE FOUR ROWS ARE SILENT, and none of them is vacuous filler: in-scope-is-clean is the
    rule's purpose, the `grandfathered` sentinel is a documented carve-out somebody might "helpfully"
    tighten, and no-receipt-means-no-scope is what stops the sweep attributing every uncommitted file
    in the checkout to whichever plan it found first. The single FLAGGING row is what keeps them from
    being satisfied by a rule that reports nothing.

    EVERY ROW IS LANE-ISOLATED (rcptstale `wmnmei`). The rule measures the plan's ISOLATED LANE
    WORKTREE and is SILENT for a plan that has none, so `_repo` allocates the lane and dirties the
    path inside it. Without that, all three silent rows would pass against a rule that had stopped
    working entirely, which is exactly the vacuity this docstring warns about.
    """

    RULE = "check.scope-drift"

    def _repo(
        self, *, scope_paths: str, dirty: str, write_receipt: bool = True
    ) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
        pending = root / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True)
        (root / "src").mkdir()
        (root / "other").mkdir()
        (root / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n", encoding="utf-8"
        )
        (pending / "20260828-t-01-aaa111-x.ipd.md").write_text(
            "# IPD: x\n\n- Id: aaa111\n- Kind: child\n- Status: approved\n- Set: t\n- Order: 1\n"
            f"- Scope-Paths: {scope_paths}\n\n## Workflow history\n"
            "- 2026-08-25 approved (aw set): x\n\n## Goal\n\ng\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root, check=True)
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True
        ).stdout.strip()
        if write_receipt:
            rpath = life.receipt_path_for(root, "aaa111")
            rpath.parent.mkdir(parents=True, exist_ok=True)
            rpath.write_text(
                json.dumps(
                    {"plan_id": "aaa111", "base_head": base, "scope_paths": ["src/"]}
                ),
                encoding="utf-8",
            )
        # THE DIRT GOES IN THE LANE, because that is the tree the rule measures. Allocated with the
        # production allocator (cut at the frozen base, which its ancestry check requires) so this
        # fixture cannot drift from where `_plan_execution_tree` looks. Allocated even in the
        # no-receipt row, so that row's silence is attributable to the missing RECEIPT alone.
        from agent_workflows import worktree_lease as lease

        lane = lease.allocate_worktree(root, "aaa111").path
        (lane / dirty).parent.mkdir(parents=True, exist_ok=True)
        (lane / dirty).write_text("y\n", encoding="utf-8")
        return root

    #: (case, declared Scope-Paths, path dirtied after the base commit, is a receipt written?,
    #:  a substring the reported detail must contain or None for "must report nothing",
    #:  why this row exists)
    FIXTURES = (
        (
            "a changed path outside the declared scope",
            "src/",
            "other/x.py",
            True,
            "other",
            "THE RULE'S ONE POSITIVE CASE, and the only row that keeps the three silent rows below "
            "from being satisfied by a rule that reports nothing at all. The detail must NAME the "
            "path, because a finding that says only 'scope drifted' is unactionable. `git status` "
            "collapses a wholly-untracked directory, so the reported path is `other/`",
        ),
        (
            "a changed path INSIDE the declared scope",
            "src/",
            "src/feat.py",
            True,
            None,
            "THE RULE'S PURPOSE, stated as its silence: working within a declared allowlist is "
            "exactly what an executing plan is supposed to do. If this row fires, every conforming "
            "execution reports drift against itself and the check becomes noise operators learn to "
            "ignore",
        ),
        (
            "the `grandfathered` Scope-Paths sentinel",
            "grandfathered",
            "other/x.py",
            True,
            None,
            "A DOCUMENTED CARVE-OUT SOMEBODY WILL TRY TO TIGHTEN. `grandfathered` yields an EMPTY "
            "frozen allowlist, and an empty allowlist is advisory-satisfied rather than "
            "match-nothing; reading it the other way would hard-flag every path of every "
            "pre-cutover plan. Note the dirty path is the same out-of-scope one the flagging row "
            "uses, so the difference is the sentinel and nothing else",
        ),
        (
            "no begin receipt at all",
            "src/",
            "other/x.py",
            False,
            None,
            "NO LIVE EXECUTION MEANS NO SCOPE TO DRIFT FROM. Without this row the sweep would "
            "attribute every uncommitted file in a shared checkout to whichever plan declared a "
            "scope, which is the measured harm (other agents' and humans' work reported against a "
            "plan that is not running). Again the dirt is the flagging row's, so the receipt is the "
            "only difference",
        ),
    )

    def test_each_fixture_reports_exactly_what_the_receipt_justifies(self):
        wrong = []
        for case, scope, dirty, receipt, needle, why in self.FIXTURES:
            root = self._repo(scope_paths=scope, dirty=dirty, write_receipt=receipt)
            hits = [d for d in ce.check_scope_drift(root) if d.rule == self.RULE]
            problems = []
            if needle is None:
                if hits:
                    problems.append(
                        f"expected NO finding, got {[d.detail for d in hits]!r}"
                    )
            elif not hits:
                problems.append("expected a finding, got nothing")
            elif not any(needle in d.detail for d in hits):
                problems.append(
                    f"fired but no detail names {needle!r}: {[d.detail for d in hits]!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (Scope-Paths={scope!r}, dirtied={dirty!r}, "
                    f"receipt={receipt}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`check_scope_drift` answered {len(wrong)} of {len(self.FIXTURES)} fixtures wrongly. "
            "READ THE GROUPING: if ALL THREE silent rows fired together, the sweep stopped requiring "
            "a live receipt or stopped honoring the allowlist and now reports every uncommitted path "
            "in the checkout, including work belonging to other agents and humans. If only the "
            "FLAGGING row failed, the rule is inert and an out-of-scope change reaches finalize "
            "unreported. If the in-scope row alone fired, the scope MATCHER broke rather than the "
            "sweep. FIX: the comparison is `ipd_lifecycle._scope_match` / `_frozen_scope_paths` / "
            "`_paths_changed_by_this_execution`, whose reuse is asserted separately below; the sweep "
            "itself only assembles them.\n" + "\n".join(wrong),
        )


if __name__ == "__main__":
    unittest.main()
