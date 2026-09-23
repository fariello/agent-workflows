"""stalemerge-01 (`87apfx`): a cross-run adjacency conflict must be told from a failure of the work.

WHAT THIS FILE GUARDS, measured on two lanes of `run-20260922T024054Z-2245533` rather than reasoned. Both
`92u0v9` and `xipfy1` finished their work, passed their own suite, finalized on their lane branch, and
were then refused `merge-refused` carrying a verdict reading "it asserts a real failure of the work". For
both that sentence was FALSE: each conflict was a cross-run race in which two branches ADD at one
insertion point, and each was resolved by hand in minutes with the full suite green afterwards. The
refusal is terminal on its FIRST attempt, and three further items in that run reached
`dependency-blocked` behind refused ones, so one mislabelled refusal multiplied into four lost lanes.

THE REPLAY IS THE BACKBONE, not a nicety. `ConflictReplayTests` reconstructs BOTH real conflicts from refs
that still exist (`aw/lane/92u0v9` = `97255449`, `aw/lane/xipfy1` = `d1cc184f`, peers `f9a37808` and
`908db905`) and drives the production path over them, because every single one of this change's four
subtle failure modes was found by measurement and none by reasoning:

  * the cause space is THREE and not six (four gate statuses are unreachable from this call path);
  * the adjacency predicate is UNSOUND on git's DEFAULT two-way markers, which carry no base section;
  * the peer commit must come from the HUNK and not the file's history, which on `xipfy1` names an
    unrelated lane (`f2410f75`, lane `65cuw0`) while the hunk's real author is `908db905`; and
  * `render_stream.record_refusal` does NOT redact, unlike its sibling readers.

WHEN THE REPLAY CANNOT RUN (a clone without these refs, a shallow checkout) it SKIPS rather than passes
vacuously, and the pure-predicate tests below carry the same properties over constructed input so the
file is never reduced to nothing by a missing ref.
"""

from __future__ import annotations

import pathlib
import subprocess
import tempfile
import unittest

from agent_workflows import runner_shared

REPO_ROOT = pathlib.Path(runner_shared.__file__).resolve().parent.parent

# The two measured cases: id6 -> (lane branch, peer commit, the lane's base, the conflicting path).
# Every hash is an ancestor of `origin/main` and both lane branches still exist, so the conflicts are
# reconstructible from REFS rather than only from raw hashes.
MEASURED_CASES = {
    "92u0v9": (
        "aw/lane/92u0v9",
        "f9a37808",
        "f763be8c",
        "agent_workflows/completion.py",
    ),
    "xipfy1": (
        "aw/lane/xipfy1",
        "908db905",
        "d1d6b6eb",
        "agent_workflows/runner_shared.py",
    ),
}

# The commit the NAIVE "last commit touching the file" derivation would name for `xipfy1`. It is lane
# `65cuw0`'s integration merge and is UNRELATED to the conflict; nine commits touched that path in the
# window. Asserted as a NEGATIVE so the naive form cannot be reintroduced as a "simplification".
XIPFY1_WRONG_PEER = "f2410f75"


def _git(repo: pathlib.Path, args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(["git", *args], cwd=str(repo), text=True, capture_output=True)
    return proc.returncode, proc.stdout, proc.stderr


def _refs_available(case: str) -> bool:
    branch, peer, base, _path = MEASURED_CASES[case]
    for ref in (branch, peer, base):
        rc, _out, _err = _git(REPO_ROOT, ["rev-parse", "--verify", f"{ref}^{{commit}}"])
        if rc != 0:
            return False
    return True


def _drive_write_site(
    reason: str, *, item: dict | None = None, options: dict | None = None
) -> dict:
    """Run the SHARED ladder write site over a throwaway run directory, returning the mutated item.

    THE REAL FUNCTION, not a reimplementation of it: `record_integration_refusal` is where the cause is
    read, the verdict chosen, the ladder written and the resolver refusal emitted, so a test that
    reproduced those steps would prove only that the test agrees with itself.
    """
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = pathlib.Path(tmp)
        state: dict = {"options": dict(options or {}), "queue": []}
        mutable = dict(item or {})
        runner_shared.record_integration_refusal(
            run_dir=run_dir,
            state=state,
            item=mutable,
            attempt={},
            integ_kind=runner_shared.INTEGRATION_REFUSAL_CONFLICT,
            integ_reason=reason,
            branch="aw/lane/demo",
            save_state=lambda *_a, **_k: None,
            append_jsonl=lambda *_a, **_k: None,
        )
    return mutable


class CauseChannelTests(unittest.TestCase):
    """E-01: WHICH of the three reachable causes fired must be recorded, and an old record must be honest.

    The measured gap this closes: `ld8lb3`'s recorded `integration_deferral` DOES contain
    `integration_failed_combined_red` (it leaked out of the gate's own status line), while `92u0v9`'s and
    `xipfy1`'s contain NO `integration_failed_*` token at all, because the git-conflict arm formats a human
    message and returns the bare kind. So for exactly the class this change is about, the cause was
    recorded nowhere.
    """

    def test_the_token_round_trips_and_is_STRIPPED_from_what_a_human_reads(self):
        tagged = runner_shared.tag_integration_cause(
            runner_shared.INTEGRATION_CAUSE_GIT_CONFLICT,
            "the operator-facing sentence",
            shape=runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY,
        )
        cause, shape, text = runner_shared.read_integration_cause(tagged)
        self.assertEqual(cause, runner_shared.INTEGRATION_CAUSE_GIT_CONFLICT)
        self.assertEqual(shape, runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY)
        self.assertEqual(
            text,
            "the operator-facing sentence",
            "the token is an implementation detail and must never reach an operator",
        )
        self.assertNotIn(runner_shared.INTEGRATION_CAUSE_TOKEN_PREFIX, text)

    def test_the_shape_token_is_OPTIONAL(self):
        cause, shape, text = runner_shared.read_integration_cause(
            runner_shared.tag_integration_cause(
                runner_shared.INTEGRATION_CAUSE_GATE_COMBINED_RED, "measured red"
            )
        )
        self.assertEqual(cause, runner_shared.INTEGRATION_CAUSE_GATE_COMBINED_RED)
        self.assertEqual(shape, runner_shared.CONFLICT_SHAPE_UNKNOWN)
        self.assertEqual(text, "measured red")

    def test_an_OLD_record_with_no_token_reads_as_UNKNOWN(self):
        """THE DURABILITY RULE `LEGACY_INTEGRATION_STATUS_ALIASES` exists for, applied to a new field.

        Run directories are DURABLE RECORDS. Every run already on disk was written before this channel
        existed, so an absent key must read as UNKNOWN and never as any particular cause: guessing one
        would fabricate a measurement nobody made.
        """
        recorded = (
            "merge-back conflict in 1 file(s): agent_workflows/completion.py; "
            "CONFLICT (content): Merge conflict in agent_workflows/completion.py"
        )
        cause, shape, text = runner_shared.read_integration_cause(recorded)
        self.assertEqual(cause, runner_shared.INTEGRATION_CAUSE_UNKNOWN)
        self.assertEqual(shape, runner_shared.CONFLICT_SHAPE_UNKNOWN)
        self.assertEqual(text, recorded, "an untokened reason passes through unchanged")

        item = _drive_write_site(recorded)
        self.assertEqual(
            item["integration_ladder"][runner_shared.INTEGRATION_CAUSE_KEY],
            runner_shared.INTEGRATION_CAUSE_UNKNOWN,
        )

    def test_a_cause_NAMED_IN_PROSE_is_not_mistaken_for_the_field(self):
        """The token is ANCHORED at the string start, so a quoted refusal cannot forge a cause.

        This matters because agents paste previous refusals into reports, and a mid-string match would let
        a quotation assert a measurement.
        """
        cause, _shape, _text = runner_shared.read_integration_cause(
            "a previous run said "
            + runner_shared.tag_integration_cause("git-merge-conflict", "x")
        )
        self.assertEqual(cause, runner_shared.INTEGRATION_CAUSE_UNKNOWN)

    def test_the_gate_status_map_is_THREE_reachable_causes_and_fails_closed(self):
        """E-03's taxonomy claim, asserted as a NEGATIVE on the four unreachable statuses.

        `orchestrate_isolation` defines SIX `INTEGRATION_FAILED_*` statuses, but `integrate_lane_branch`
        calls the gate with one completed lane, `merge_order=[id6]`, base == `handle.base_commit` and NO
        `declared_scope`, and `build_lane_outcome` hard-codes `STATUS_COMPLETED` with
        `per_lane_validation_passed=True`. So `_MISSING_LANE`, `_STALE_BASE`, `_SCOPE_VIOLATION` and
        `_LANE_FAILURE` each need an input this path cannot supply. Mapping one would assert that a verdict
        sentence had been authored and tested for it, and none has been.
        """
        from agent_workflows import orchestrate_isolation

        self.assertEqual(
            runner_shared.integration_cause_for_gate_status(
                orchestrate_isolation.INTEGRATION_FAILED_CONFLICT
            ),
            runner_shared.INTEGRATION_CAUSE_GATE_CONFLICT_MARKERS,
        )
        self.assertEqual(
            runner_shared.integration_cause_for_gate_status(
                orchestrate_isolation.INTEGRATION_FAILED_COMBINED_RED
            ),
            runner_shared.INTEGRATION_CAUSE_GATE_COMBINED_RED,
        )
        for unreachable in (
            orchestrate_isolation.INTEGRATION_FAILED_MISSING_LANE,
            orchestrate_isolation.INTEGRATION_FAILED_STALE_BASE,
            orchestrate_isolation.INTEGRATION_FAILED_SCOPE_VIOLATION,
            orchestrate_isolation.INTEGRATION_FAILED_LANE_FAILURE,
        ):
            with self.subTest(status=unreachable):
                self.assertEqual(
                    runner_shared.integration_cause_for_gate_status(unreachable),
                    runner_shared.INTEGRATION_CAUSE_UNKNOWN,
                    "this status is UNREACHABLE from `integrate_lane_branch`'s call, so mapping it "
                    "would author an untestable claim; see INTEGRATION_CAUSE_GATE_CONFLICT_MARKERS",
                )
        for junk in (None, 42, "", "integration_failed_invented"):
            with self.subTest(value=junk):
                self.assertEqual(
                    runner_shared.integration_cause_for_gate_status(junk),
                    runner_shared.INTEGRATION_CAUSE_UNKNOWN,
                )

    def test_the_cause_is_written_ADDITIVELY_onto_the_existing_ladder_record(self):
        """No reader changes: the cause joins `integration_ladder` rather than becoming a new status.

        The naming rule for these states is fixed (the name states the NEXT ACTION, not the internal
        cause: `merge-retry` retries itself, `merge-needs-human` needs you, `merge-refused` is the gate
        declining, `merge-unchecked` is the gate unable to judge), which is exactly why a CAUSE field was
        added instead of a fifth status.
        """
        item = _drive_write_site(
            runner_shared.tag_integration_cause(
                runner_shared.INTEGRATION_CAUSE_GATE_COMBINED_RED, "measured red"
            )
        )
        ladder = item["integration_ladder"]
        self.assertEqual(
            ladder[runner_shared.INTEGRATION_CAUSE_KEY],
            runner_shared.INTEGRATION_CAUSE_GATE_COMBINED_RED,
        )
        for preserved in (
            "kind",
            "deferrable",
            "status",
            "deferred",
            "attempts_used",
            "limit",
            "policy",
            "verdict",
        ):
            with self.subTest(key=preserved):
                self.assertIn(preserved, ladder)
        self.assertEqual(ladder["kind"], runner_shared.INTEGRATION_REFUSAL_CONFLICT)
        self.assertEqual(item["status"], runner_shared.INTEGRATION_REFUSAL_CONFLICT)
        self.assertNotIn(
            runner_shared.INTEGRATION_CAUSE_TOKEN_PREFIX,
            item["integration_deferral"],
            "the item's own diagnostic string must stay operator-facing",
        )


class AdjacencyPredicateTests(unittest.TestCase):
    """E-02: three-valued, and it must REFUSE to judge git's default two-way markers.

    THE FAILURE DIRECTION IS ASYMMETRIC, which is why UNKNOWN is a verdict rather than an error: a wrong
    `adjacency-only` tells a resolver a SEMANTIC conflict is safe to keep-both, which is how bad code
    reaches main. A wrong UNKNOWN costs only a manual read.
    """

    ADJACENT = (
        "context\n"
        "<<<<<<< ours\n"
        "ours added one\n"
        "ours added two\n"
        "||||||| base\n"
        "=======\n"
        "theirs added one\n"
        ">>>>>>> theirs\n"
        "trailing\n"
    )
    SEMANTIC = (
        "<<<<<<< ours\n"
        "ours rewrote the line\n"
        "||||||| base\n"
        "the base line both sides touched\n"
        "=======\n"
        "theirs rewrote the line\n"
        ">>>>>>> theirs\n"
    )
    TWO_WAY = (
        "<<<<<<< ours\n"
        "ours added one\n"
        "=======\n"
        "theirs added one\n"
        ">>>>>>> theirs\n"
    )

    def test_both_sides_only_adding_is_ADJACENCY_ONLY(self):
        verdict = runner_shared.classify_conflict_hunk_shape(self.ADJACENT)
        self.assertEqual(verdict.verdict, runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY)
        self.assertEqual(verdict.hunks, 1)

    def test_a_side_editing_a_line_the_base_carried_is_SEMANTIC(self):
        verdict = runner_shared.classify_conflict_hunk_shape(self.SEMANTIC)
        self.assertEqual(verdict.verdict, runner_shared.CONFLICT_SHAPE_SEMANTIC)
        self.assertIn("NON-EMPTY base section", verdict.reason)

    def test_a_TWO_WAY_hunk_is_UNKNOWN_and_NEVER_adjacency_only(self):
        """THE CONTROL THE WHOLE PREDICATE RESTS ON, and the one PR-003 caught as unsound.

        Measured on `xipfy1`'s real stage blobs: `--diff3` gives 7 ours / 0 base / 10 theirs lines (the
        empty base section adjacency-only requires), while the DEFAULT two-way hunk has no base section at
        all, making "both sides only ADDED" indistinguishable from "both sides REPLACED the same base
        lines". `merge.conflictStyle` is unset both locally and globally in this repository, so DEFAULT is
        what a caller reading the working tree actually gets.
        """
        verdict = runner_shared.classify_conflict_hunk_shape(self.TWO_WAY)
        self.assertEqual(verdict.verdict, runner_shared.CONFLICT_SHAPE_UNKNOWN)
        self.assertNotEqual(
            verdict.verdict, runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY
        )
        self.assertIn("base section", verdict.reason)

    def test_a_MIXED_file_is_judged_on_its_WORST_hunk_not_its_first(self):
        """A file whose first hunk is three-way and whose second is not must not pass on the first."""
        verdict = runner_shared.classify_conflict_hunk_shape(
            self.ADJACENT + self.TWO_WAY
        )
        self.assertEqual(verdict.verdict, runner_shared.CONFLICT_SHAPE_UNKNOWN)
        self.assertEqual(verdict.hunks, 2)

    def test_unparseable_and_empty_input_are_UNKNOWN(self):
        for bad in (
            None,
            "",
            "no markers at all\n",
            "<<<<<<< ours\nunterminated\n",
            "<<<<<<< ours\n<<<<<<< nested\n=======\n>>>>>>> t\n",
            "=======\n>>>>>>> theirs\n",
        ):
            with self.subTest(text=repr(bad)[:40]):
                self.assertEqual(
                    runner_shared.classify_conflict_hunk_shape(bad).verdict,
                    runner_shared.CONFLICT_SHAPE_UNKNOWN,
                )

    def test_a_whitespace_only_base_section_is_still_EMPTY(self):
        """A base contributing only blank lines means neither side changed a line of CONTENT."""
        verdict = runner_shared.classify_conflict_hunk_shape(
            "<<<<<<< ours\na\n||||||| base\n\n   \n=======\nb\n>>>>>>> theirs\n"
        )
        self.assertEqual(verdict.verdict, runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY)


class TerminalVerdictTests(unittest.TestCase):
    """E-03: the verdict must stop asserting a failure of the work for a conflict that is not one.

    WORDS CHANGE, VERDICTS DO NOT. Every cause keeps exactly the terminality it had; the class below
    proves that with a before/after table over every reachable cause.
    """

    def test_the_conflict_verdict_NO_LONGER_claims_a_failure_of_the_work(self):
        verdict = runner_shared.decide_integration_deferral(
            integ_kind=runner_shared.INTEGRATION_REFUSAL_CONFLICT,
            attempts_used=1,
            limit=10,
            cause=runner_shared.INTEGRATION_CAUSE_GIT_CONFLICT,
        ).reason
        self.assertNotIn(
            "failure of the work",
            verdict,
            "THE MEASURED DEFECT: this sentence told an operator a verified lane's code was broken "
            "when the conflict was a cross-run race resolved by hand in minutes",
        )
        self.assertIn("NOT A STATEMENT ABOUT THE LANE'S CODE", verdict)
        self.assertIn("main is UNTOUCHED", verdict)

    def test_every_new_verdict_KEEPS_both_shipped_pinned_substrings(self):
        """The two shipped assertions in `tests/test_runner_shared.py` are HONORED, not weakened.

        `test_the_terminal_verdict_NAMES_the_condition_instead_of_listing_four` requires
        `"terminal on its first attempt"` AND a pointer to the field carrying the cause, and forbids
        `"stale base"` / `"scope violation"`; `test_merge_conflict_is_TERMINAL_ON_ITS_FIRST_ATTEMPT_
        and_consumes_no_budget` requires the first. Asserted here over EVERY branch so a future edit to
        one sentence cannot quietly drop the contract from that branch alone.
        """
        for cause in (
            runner_shared.INTEGRATION_CAUSE_GIT_CONFLICT,
            runner_shared.INTEGRATION_CAUSE_GATE_CONFLICT_MARKERS,
            runner_shared.INTEGRATION_CAUSE_GATE_COMBINED_RED,
            runner_shared.INTEGRATION_CAUSE_UNKNOWN,
            "something-nobody-wrote",
        ):
            with self.subTest(cause=cause):
                verdict = runner_shared.terminal_refusal_verdict("merge-refused", cause)
                self.assertIn("terminal on its first attempt", verdict)
                self.assertNotIn("stale base", verdict)
                self.assertNotIn("scope violation", verdict)
                self.assertTrue(
                    "integration_ladder.cause" in verdict
                    or "integration_deferral" in verdict,
                    "having stopped guessing, each verdict must point at the field carrying the "
                    "cause, or the specific cause becomes unfindable",
                )

    def test_an_UNKNOWN_cause_falls_back_to_todays_wording_BYTE_FOR_BYTE(self):
        """The fail-closed direction, and what keeps every record on disk reading as it does today."""
        today = (
            "integration refusal kind 'merge-refused' is terminal on its first attempt: it is "
            "neither the transient dirty-overlap condition nor an unmeasured-gate refusal, so "
            "it asserts a real failure of the work (see the recorded integration_deferral for "
            "the gate's specific status) and repetition alone cannot clear it"
        )
        for cause in (
            runner_shared.INTEGRATION_CAUSE_UNKNOWN,
            "a-cause-from-the-future",
            "",
        ):
            with self.subTest(cause=cause):
                self.assertEqual(
                    runner_shared.terminal_refusal_verdict("merge-refused", cause),
                    today,
                )
        self.assertEqual(
            runner_shared.decide_integration_deferral(
                integ_kind=runner_shared.INTEGRATION_REFUSAL_CONFLICT,
                attempts_used=1,
                limit=10,
            ).reason,
            today,
            "the DEFAULT `cause` must reproduce today's sentence, so no existing caller changed",
        )

    def test_NO_cause_changes_status_or_deferrability(self):
        """The before/after table V-03 requires: this change touches WORDS, never VERDICTS."""
        rows = {}
        for cause in (
            runner_shared.INTEGRATION_CAUSE_GIT_CONFLICT,
            runner_shared.INTEGRATION_CAUSE_GATE_CONFLICT_MARKERS,
            runner_shared.INTEGRATION_CAUSE_GATE_COMBINED_RED,
            runner_shared.INTEGRATION_CAUSE_UNKNOWN,
        ):
            decision = runner_shared.decide_integration_deferral(
                integ_kind=runner_shared.INTEGRATION_REFUSAL_CONFLICT,
                attempts_used=1,
                limit=10,
                cause=cause,
            )
            rows[cause] = (decision.status, decision.deferred, decision.limit)
        self.assertEqual(
            set(rows.values()),
            {(runner_shared.INTEGRATION_REFUSAL_CONFLICT, False, 10)},
            f"a cause changed a VERDICT rather than only its wording: {rows}",
        )

    def test_the_two_DEFERRABLE_kinds_are_untouched_by_the_cause_parameter(self):
        for kind in (
            runner_shared.INTEGRATION_REFUSAL_TRANSIENT,
            runner_shared.INTEGRATION_REFUSAL_UNMEASURED,
        ):
            for cause in (
                runner_shared.INTEGRATION_CAUSE_UNKNOWN,
                runner_shared.INTEGRATION_CAUSE_GIT_CONFLICT,
            ):
                with self.subTest(kind=kind, cause=cause):
                    plain = runner_shared.decide_integration_deferral(
                        integ_kind=kind, attempts_used=1, limit=10
                    )
                    with_cause = runner_shared.decide_integration_deferral(
                        integ_kind=kind, attempts_used=1, limit=10, cause=cause
                    )
                    self.assertEqual(plain, with_cause)
                    self.assertTrue(plain.deferred)


class ResolverRecordTests(unittest.TestCase):
    """E-04: the refusal must carry the facts a resolver needs, and NO absolute path."""

    def test_a_git_conflict_emits_a_refusal_through_the_ONE_writer(self):
        item = _drive_write_site(
            runner_shared.tag_integration_cause(
                runner_shared.INTEGRATION_CAUSE_GIT_CONFLICT,
                "merge-back conflict in 1 file(s): agent_workflows/completion.py",
                shape=runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY,
            )
        )
        refusal = item.get("refusal")
        self.assertIsNotNone(
            refusal, "the shipped Diagnostics block renders a `Refusal` for ANY status"
        )
        assert refusal is not None
        self.assertEqual(refusal["code"], runner_shared.INTEGRATION_REFUSAL_CONFLICT)
        self.assertIn("agent_workflows/completion.py", refusal["reason"])
        self.assertIn("KEEP BOTH SIDES", refusal["remedy"])
        self.assertIn("one irreversible move", refusal["remedy"])

    def test_a_SEMANTIC_conflict_gets_the_record_WITHOUT_the_keep_both_suggestion(self):
        """Telling a resolver to keep both sides of a CONTESTED hunk is how bad code reaches main."""
        for shape in (
            runner_shared.CONFLICT_SHAPE_SEMANTIC,
            runner_shared.CONFLICT_SHAPE_UNKNOWN,
        ):
            with self.subTest(shape=shape):
                item = _drive_write_site(
                    runner_shared.tag_integration_cause(
                        runner_shared.INTEGRATION_CAUSE_GIT_CONFLICT,
                        "merge-back conflict in 1 file(s): agent_workflows/x.py",
                        shape=shape,
                    )
                )
                remedy = item["refusal"]["remedy"]
                self.assertNotIn("KEEP BOTH SIDES", remedy)
                self.assertIn("on their merits", remedy)

    def test_a_NON_conflict_cause_emits_NO_conflict_refusal(self):
        """A combined-red refusal is not a conflict, so it must not acquire conflict-resolution advice."""
        item = _drive_write_site(
            runner_shared.tag_integration_cause(
                runner_shared.INTEGRATION_CAUSE_GATE_COMBINED_RED, "measured red"
            )
        )
        self.assertIsNone(item.get("refusal"))

    def test_the_facts_carry_NO_absolute_path(self):
        """F-9: `record_refusal` does NOT redact, unlike `integration_refusal_detail`.

        Verified at review by rendering a refusal whose reason contained an absolute home path and reading
        it back verbatim out of the Diagnostics block. So everything this change writes must ALREADY be
        relative: repository-relative paths, branch names, commit hashes.
        """
        detail = {
            "base_commit": "f763be8c",
            "shape": runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY,
            "files": [
                {
                    "path": "agent_workflows/completion.py",
                    "shape": runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY,
                    "shape_reason": "empty base section",
                    "hunks": 1,
                    "peer_commit": "f9a378087d33368b8db92b6c81b8e86a78409c1a",
                    "peer_reason": "one commit",
                    "peer_subject": "work: .aw/records/plans/pending/x.ipd.md",
                }
            ],
        }
        rendered = runner_shared.format_conflict_resolver_facts(
            detail
        ) + runner_shared.conflict_resolver_remedy(
            runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY, branch="aw/lane/92u0v9"
        )
        for line in rendered.splitlines():
            for token in line.split():
                self.assertFalse(
                    token.startswith("/"),
                    f"an absolute path reached the refusal record: {token!r}",
                )

    def test_an_UNPINNABLE_peer_reports_UNKNOWN_rather_than_a_plausible_wrong_commit(
        self,
    ):
        facts = runner_shared.format_conflict_resolver_facts(
            {
                "base_commit": "d1d6b6eb",
                "shape": runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY,
                "files": [
                    {
                        "path": "agent_workflows/runner_shared.py",
                        "shape": runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY,
                        "shape_reason": "empty base section",
                        "hunks": 1,
                        "peer_commit": None,
                        "peer_reason": "the hunk's lines resolve to 3 different commits",
                        "peer_subject": None,
                    }
                ],
            }
        )
        self.assertIn("peer commit UNKNOWN", facts)
        self.assertIn("resolve to 3 different commits", facts)

    def test_the_REVIEW_path_gets_the_resolver_record_TOO(self):
        """E-05's stated-and-pinned answer to the review path's asymmetry (F-10).

        THE ANSWER IS YES, BOTH PATHS, and the SITING is what delivers it. `render_record_integration_
        refusal` has exactly ONE call site, in the EXECUTE arm, so a refused REVIEW integration records
        the ladder verdict and no `Refusal` at all. Emitting E-04's record from the SHARED ladder write
        site (`record_integration_refusal`) rather than beside that one call site covers both arms with no
        second mechanism - and a reviewer whose lane lost a cross-run race needs the same three facts a
        code lane's resolver does.

        PINNED BY DRIVING THE WRITE SITE WITH A REVIEW ITEM, which is exactly what the review arm passes
        (`action: "review"`), and asserting the record is present. If a future change moves this emission
        back beside the execute-only renderer, this test fails and names why.
        """
        item = _drive_write_site(
            runner_shared.tag_integration_cause(
                runner_shared.INTEGRATION_CAUSE_GIT_CONFLICT,
                "merge-back conflict in 1 file(s): .aw/records/plans/pending/x.ipd.md",
                shape=runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY,
            ),
            item={"id6": "rev001", "action": "review"},
        )
        self.assertEqual(
            runner_shared.integration_action_for_item(item),
            runner_shared.INTEGRATION_ACTION_REVIEW,
            "the fixture must genuinely be a review item, or this pins nothing",
        )
        self.assertIsNotNone(
            item.get("refusal"),
            "FIX: emit the resolver record from the SHARED ladder write site, not beside the "
            "execute-only `render_record_integration_refusal` call; a refused review lane needs the "
            "conflicting paths, the adjacency verdict and the peer commit exactly as an execute lane does",
        )
        self.assertIn(".aw/records/plans/pending/x.ipd.md", item["refusal"]["reason"])
        self.assertEqual(
            item["integration_ladder"][runner_shared.INTEGRATION_CAUSE_KEY],
            runner_shared.INTEGRATION_CAUSE_GIT_CONFLICT,
            "and the cause must be recorded for a review refusal too",
        )

    def test_the_peer_derivation_needs_a_TARGET_SIDE_line_to_search_on(self):
        with tempfile.TemporaryDirectory() as tmp:
            peer, why = runner_shared.peer_commit_for_conflict(
                pathlib.Path(tmp),
                path="x.py",
                merged_text="<<<<<<< ours\n|||||||\n=======\ntheirs only\n>>>>>>> theirs\n",
                base_commit="deadbeef",
            )
        self.assertIsNone(peer)
        self.assertIn("no target-side line", why)


class ConflictReplayTests(unittest.TestCase):
    """THE BACKBONE: drive the production path over the TWO REAL recorded conflicts.

    Each is reconstructed by checking out the PEER commit into a scratch worktree and merging the lane
    branch into it, which is exactly the "main advanced past the lane base" case
    `integrate_lane_branch`'s conflict arm handles.
    """

    def _replay(self, case: str):
        branch, peer, base, _path = MEASURED_CASES[case]
        with tempfile.TemporaryDirectory() as tmp:
            work = pathlib.Path(tmp) / "wt"
            rc, _out, err = _git(
                REPO_ROOT, ["worktree", "add", "--detach", str(work), peer]
            )
            if rc != 0:  # pragma: no cover - environment, not behavior
                self.skipTest(f"could not create a scratch worktree at {peer}: {err}")
            try:
                rc, out, err = _git(
                    work, ["merge", "--no-ff", "--no-edit", "-m", "replay", branch]
                )
                self.assertNotEqual(
                    rc, 0, "the recorded conflict must still reproduce from these refs"
                )
                self.assertTrue(runner_shared.merge_in_progress(work))
                conflicted = runner_shared.conflicted_paths(work)
                detail = runner_shared.build_conflict_resolver_detail(
                    work, paths=conflicted, base_commit=base
                )
                _git(work, ["merge", "--abort"])
            finally:
                _git(REPO_ROOT, ["worktree", "remove", "--force", str(work)])
        return conflicted, detail

    def test_92u0v9_is_ADJACENCY_ONLY_and_names_its_real_peer(self):
        if not _refs_available("92u0v9"):  # pragma: no cover - environment
            self.skipTest("the `92u0v9` refs are not present in this checkout")
        conflicted, detail = self._replay("92u0v9")
        self.assertEqual(conflicted, ["agent_workflows/completion.py"])
        self.assertEqual(detail["shape"], runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY)
        entry = detail["files"][0]
        self.assertEqual(entry["shape"], runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY)
        self.assertTrue(
            str(entry["peer_commit"]).startswith("f9a37808"),
            f"expected peer f9a37808, got {entry['peer_commit']}",
        )

    def test_xipfy1_names_the_HUNKS_author_and_NOT_the_last_commit_touching_the_file(
        self,
    ):
        """F-6c, the case the naive derivation gets WRONG, asserted in both directions.

        The most recent commit touching `agent_workflows/runner_shared.py` in the window is `f2410f75`
        (lane `65cuw0`'s integration merge, unrelated); the commit that actually wrote the conflicting
        hunk is `908db905`, found with `git log -S` on a line the hunk added. Nine commits touched that
        path in the window, so the naive form is not merely imprecise, it names the wrong lane.
        """
        if not _refs_available("xipfy1"):  # pragma: no cover - environment
            self.skipTest("the `xipfy1` refs are not present in this checkout")
        conflicted, detail = self._replay("xipfy1")
        self.assertEqual(conflicted, ["agent_workflows/runner_shared.py"])
        self.assertEqual(detail["shape"], runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY)
        entry = detail["files"][0]
        peer = str(entry["peer_commit"])
        self.assertTrue(
            peer.startswith("908db905"), f"expected peer 908db905, got {peer}"
        )
        self.assertFalse(
            peer.startswith(XIPFY1_WRONG_PEER),
            "the peer must come from the HUNK, not from the file's recent history",
        )

    def test_the_replayed_conflicts_reach_the_write_site_with_the_new_cause(self):
        """END TO END over a real conflict: the cause reaches `integration_ladder`, and the verdict flips.

        This is the assertion the two measured lanes needed and did not have: `92u0v9`'s and `xipfy1`'s
        recorded ladders carry `cause` nowhere and a verdict claiming their code failed.
        """
        available = [c for c in MEASURED_CASES if _refs_available(c)]
        if not available:  # pragma: no cover - environment
            self.skipTest("neither measured case's refs are present in this checkout")
        for case in available:
            with self.subTest(case=case):
                conflicted, detail = self._replay(case)
                tagged = runner_shared.tag_integration_cause(
                    runner_shared.INTEGRATION_CAUSE_GIT_CONFLICT,
                    runner_shared.format_conflict_resolver_facts(detail),
                    shape=str(detail["shape"]),
                )
                item = _drive_write_site(tagged)
                self.assertEqual(
                    item["integration_ladder"][runner_shared.INTEGRATION_CAUSE_KEY],
                    runner_shared.INTEGRATION_CAUSE_GIT_CONFLICT,
                )
                self.assertNotIn(
                    "failure of the work", item["integration_ladder"]["verdict"]
                )
                self.assertIn(conflicted[0], item["refusal"]["reason"])
                self.assertIn("KEEP BOTH SIDES", item["refusal"]["remedy"])

    def test_re_merging_on_a_FRESHER_BASE_does_not_clear_either_conflict(self):
        """F-7, the load-bearing NEGATIVE result that bounds this whole change's scope.

        The originating backlog item's first remedy was to re-merge the lane onto current `main`, on the
        reasoning that two purely additive changes must combine. That is FALSE and is asserted here so a
        future reader cannot re-propose it without the suite contradicting them: `merge-tree` of the lane
        tip against a base that ALREADY CONTAINS the peer commit STILL conflicts. "Purely additive"
        describes the SEMANTICS (which is why a human resolution is trivial and lossless) and says nothing
        about MERGEABILITY, because git has no basis to order two insertions at one location.
        """
        checked = 0
        for case, (branch, peer, _base, path) in MEASURED_CASES.items():
            if not _refs_available(case):  # pragma: no cover - environment
                continue
            with self.subTest(case=case):
                rc, out, err = _git(
                    REPO_ROOT, ["merge-tree", "--write-tree", branch, peer]
                )
                self.assertNotEqual(
                    rc,
                    0,
                    f"{case} unexpectedly merged cleanly against a base containing its peer; if this "
                    "is genuinely true now, RE-MEASURE before widening this change's scope",
                )
                self.assertIn(path, out + err)
                checked += 1
        if not checked:  # pragma: no cover - environment
            self.skipTest("neither measured case's refs are present in this checkout")


class AntiRegressionControls(unittest.TestCase):
    """E-06's three controls: each FAILS if the property it guards is deliberately broken.

    These are not restatements of the tests above. Each names a specific way a future change could undo
    this one while every other test stayed green, which is why each says WHAT to do instead.
    """

    def test_control_a_the_conflict_verdict_may_NEVER_regain_a_failure_of_the_work_claim(
        self,
    ):
        """CONTROL (a). Break it by routing `INTEGRATION_CAUSE_GIT_CONFLICT` to the fallback wording.

        The forbidden phrases are asserted as a SET so a paraphrase does not slip past: the measured harm
        was an operator reading "failure of the work" about a lane whose suite was green, and any sentence
        meaning the same thing costs the same.
        """
        verdict = runner_shared.terminal_refusal_verdict(
            "merge-refused", runner_shared.INTEGRATION_CAUSE_GIT_CONFLICT
        )
        for forbidden in (
            "failure of the work",
            "failure of this work",
            "the work failed",
            "a real failure",
        ):
            with self.subTest(phrase=forbidden):
                self.assertNotIn(
                    forbidden.lower(),
                    verdict.lower(),
                    "FIX: a git conflict is not a statement about the lane's code. Say what happened "
                    "(two branches changed one region, main is untouched, the lane is preserved) and "
                    "leave the judgement out; see `terminal_refusal_verdict`",
                )

    def test_control_b_a_plain_conflict_may_NEVER_become_DEFERRABLE(self):
        """CONTROL (b). Break it by adding `INTEGRATION_REFUSAL_CONFLICT` to
        `classify_integration_refusal`'s tuple.

        WHY THIS IS OUT OF SCOPE AND MUST STAY OUT: a retry recomputes the same conflict from the same two
        commits (there is no base-refresh machinery anywhere in `agent_workflows/`), so promoting it would
        burn the retry budget and change nothing. This control is the durable form of that exclusion,
        which is stronger than a note in a plan nobody re-reads.
        """
        self.assertFalse(
            runner_shared.classify_integration_refusal(
                runner_shared.INTEGRATION_REFUSAL_CONFLICT
            ),
            "FIX: revert whatever made `merge-refused` deferrable. Repetition cannot order two "
            "insertions at one location, so a retry spends budget for a guaranteed identical refusal",
        )
        for cause in (
            runner_shared.INTEGRATION_CAUSE_GIT_CONFLICT,
            runner_shared.INTEGRATION_CAUSE_GATE_CONFLICT_MARKERS,
            runner_shared.INTEGRATION_CAUSE_GATE_COMBINED_RED,
            runner_shared.INTEGRATION_CAUSE_UNKNOWN,
        ):
            with self.subTest(cause=cause):
                decision = runner_shared.decide_integration_deferral(
                    integ_kind=runner_shared.INTEGRATION_REFUSAL_CONFLICT,
                    attempts_used=1,
                    limit=1000,
                    cause=cause,
                )
                self.assertFalse(
                    decision.deferred,
                    "no CAUSE may make a conflict deferrable; the cause selects WORDS only",
                )
                self.assertEqual(
                    decision.status, runner_shared.INTEGRATION_REFUSAL_CONFLICT
                )

    def test_control_c_a_hunk_with_NO_base_section_may_NEVER_read_adjacency_only(self):
        """CONTROL (c). Break it by treating a missing `|||||||` section as an empty one.

        This is the one way E-02 could tell a resolver a SEMANTIC conflict is safe to keep-both, and it is
        the exact unsoundness the first draft of the predicate had: git's DEFAULT conflict style is
        two-way, so the hazard is the DEFAULT rather than an edge case.
        """
        two_way_variants = (
            "<<<<<<< a\nx\n=======\ny\n>>>>>>> b\n",
            "lead\n<<<<<<< a\nx\nx2\n=======\n>>>>>>> b\ntail\n",
            "<<<<<<< a\n=======\ny\n>>>>>>> b\n",
        )
        for text in two_way_variants:
            with self.subTest(text=text[:24]):
                verdict = runner_shared.classify_conflict_hunk_shape(text)
                self.assertNotEqual(
                    verdict.verdict,
                    runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY,
                    "FIX: a hunk with no `|||||||` base section proves nothing about whether either "
                    "side ADDED or REPLACED. Return UNKNOWN and re-read the conflict with `--diff3` "
                    "or from the three merge stages",
                )
                self.assertEqual(verdict.verdict, runner_shared.CONFLICT_SHAPE_UNKNOWN)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
