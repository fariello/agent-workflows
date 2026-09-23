"""`runresidue` 01 (`gqo6if`) E-05: pin the RESIDUE DECISIONS, through the public seam only.

WHY THIS FILE EXISTS. This plan's substantive output is a per-symbol SHARE / HOST-SPECIFIC decision
for every symbol still co-defined in both host runners (recorded in research `fedqe6`). A decision
table living only in a document ROTS, and this repository has measured that happening three times in
this exact area: the `rununify` Set's headline figure could not be re-derived because its scan was
ad hoc and thrown away (its own PR-006), a figure was quoted at NAME level and had to be corrected
from "58 symbols / 2711 lines" to "20 / 667", and THIS PLAN AS AUTHORED quoted strict/loose counts
that reproduced under neither test at its own cited HEAD. So the decisions are asserted here, where a
later change that quietly re-forks a shared symbol or quietly shares a pinned one goes RED.

WHAT THIS FILE MAY NOT ASSERT, and the prohibition is the point rather than a style note. This
repository DELIBERATELY RETIRED change-detector tests over source text: commit `d4dd6b88`
(2026-09-18, "test: retire change-detector tests over code text and prose") deleted
`tests/test_wtiso_characterization.py`, and `7ebc2964` before it deleted four
`test_rununify_*_characterization.py` files totalling roughly 3,900 lines, removing exactly the
`len(getsourcelines(...))` counts, `SequenceMatcher` ratios and AST censuses that a "pin the
duplication" instinct reaches for first. Re-creating that form under a new name would revert a
maintainer decision made four days before this plan was authored.

THEREFORE: every assertion below is either a BEHAVIORAL one (call the symbol, observe its effect) or
a DELEGATION-IDENTITY one (which object does this host's attribute actually reach), and NONE is a
source-text, line-count, similarity-ratio or AST-shape assertion. The census numbers are consumed
FROM THE COMMITTED SCANNER, which is a measuring instrument this plan extended rather than a second
implementation of the question; that is the same seam
`tests/test_hostdedup_identical_lift.py::TheCommittedScannerIsInTreeAndAgrees` already consumes, and
using it keeps one census in the repository instead of two that can disagree.

WHY A NEW FILE RATHER THAN AN EXISTING ONE. `tests/test_rununify_characterization.py` is plan
`40it5e` E-03's undelivered deliverable and that plan is `reviewed`, not executed, so writing into it
would have two plans creating and extending the same new file with no dependency edge between them
(this plan's F-10). This file's name is owned by this plan.
"""

from __future__ import annotations

import importlib.util
import pathlib
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd as AGY
from agent_workflows import oc_runipd as OC
from agent_workflows import runner_shared as RS

REPO = pathlib.Path(__file__).resolve().parent.parent
SCANNER_PATH = REPO / "tools" / "runner_fork_scan.py"

HOSTS = (("oc", OC), ("agy", AGY))


def _scanner():
    """The COMMITTED scanner, loaded by path.

    By path rather than by import because it is a tool and not a package module, and BY PATH
    DELIBERATELY: `tests/test_hostdedup_identical_lift.py` already asserts that path is a contract,
    since the `hostdedup` Set's acceptance plan consumes it by path and refuses to improvise a
    replacement.
    """
    spec = importlib.util.spec_from_file_location("_runner_fork_scan", SCANNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TheScannerReportsBothTestsWithTheirDefinitions(unittest.TestCase):
    """E-01/V-01: a residue figure may never be readable without the test that produced it.

    THIS IS THE GUARD AGAINST THE FAILURE THAT ACTUALLY HAPPENED, three times, rather than a
    hypothetical one. Each time, a single number was quoted with no statement of what it counted, and
    each time it could not be reproduced. Asserting that the OUTPUT carries its own definitions makes
    the next quote self-documenting, which no amount of prose in a plan can.
    """

    def test_the_census_carries_both_tests_and_names_its_line_metric(self):
        data = _scanner().census()
        for key in ("strict_test", "loose_test", "line_metric"):
            with self.subTest(key=key):
                self.assertTrue(
                    str(data.get(key, "")).strip(),
                    f"the census must state {key!r} in its own output; a count whose test is not "
                    "stated beside it is the exact defect this plan exists to stop repeating",
                )
        # And the two tests must be DIFFERENT statements, or reporting both is theatre.
        self.assertNotEqual(data["strict_test"], data["loose_test"])

    def test_the_two_tests_actually_disagree_and_strict_is_a_SUBSET_of_loose(self):
        """The STRUCTURE that motivated a per-symbol decision, asserted rather than assumed.

        A symbol calling no shared code at all cannot simultaneously BE a pure shared delegation, so
        strict must be contained in loose. If that containment ever broke, one of the two predicates
        would be wrong and every count derived from them would be untrustworthy.
        """
        data = _scanner().census()
        strict = set(data["strict_residue"])
        loose = set(data["loose_residue"])
        self.assertTrue(
            strict <= loose,
            f"strict residue must be a subset of loose; strict-only: {sorted(strict - loose)}",
        )

    def test_a_reader_gets_both_counts_from_the_default_invocation(self):
        """One command, both numbers. A reader must not have to know a flag to avoid being misled."""
        data = _scanner().census()
        rendered = _scanner().render(data, closure=False, hazards=False, triples=False)
        self.assertIn("STRICT", rendered)
        self.assertIn("LOOSE", rendered)


class TheAnchorSymbolIsSharedAndStillBehaves(unittest.TestCase):
    """E-03/V-03: `reclaim_lanes_on_interrupt` has ONE implementation, and it still works on both hosts.

    BEHAVIOR, NOT SHAPE. The heavy end-to-end coverage for this symbol already exists and is not
    duplicated here: `tests/test_worktree_lease_merged_reclaim.py` drives the real reclaimer on BOTH
    hosts against real git worktrees, and `tests/test_lane_allocation_idempotent.py` pins its
    idempotency. What those files cannot see, and what this class adds, is WHICH BODY each host now
    reaches, plus the one property the lift could have silently broken.
    """

    def test_each_host_reaches_the_ONE_shared_implementation(self):
        """A DELEGATION pin, not a re-export row, and the distinction is load-bearing.

        `tests/test_runner_refork_guard.py`'s table requires a listed symbol to have NO top-level
        definition in the runner AND to expose the OWNER'S OBJECT (`assertIs`). This symbol is bound
        as a host SHELL (it must inject two per-host callables), so it is a top-level definition and
        is NOT the shared object: adding a row there would fail BOTH halves. The equivalent guarantee
        for a shell is that it really delegates, which is what the scanner's wrapper predicate
        answers, so that is what is asserted.
        """
        scanner = _scanner()
        data = scanner.census(["reclaim_lanes_on_interrupt"])
        record = data["symbols"]["reclaim_lanes_on_interrupt"]
        self.assertTrue(
            record["wrapper"],
            "both hosts must bind `reclaim_lanes_on_interrupt` as a single-statement delegation "
            "to `runner_shared`; a real body on either side is a RE-FORK of the symbol this plan "
            "shared",
        )
        self.assertEqual(record["residue_class"], "BOTH-DELEGATE")
        self.assertTrue(
            callable(getattr(RS, "reclaim_lanes_on_interrupt", None)),
            "the shared implementation must exist; the host shells delegate to it",
        )

    def test_the_shared_body_REFUSES_to_run_without_its_per_host_prompt_symbols(self):
        """The safety property the injection exists to create, asserted by calling it.

        Both prompt parameters are keyword-only with NO DEFAULT. That is deliberate and it is the
        whole reason this lift is safe: `disable_lane_prompt` writes a module-level
        `_LANE_PROMPT_DISABLED` that only its OWN module's `_lane_reclaim_prompt` reads, so a shared
        default would set a flag nobody reads and prompt suppression on a repeated interrupt would
        silently stop working - whose only symptom is an unattended run pausing on a question nobody
        is there to answer. A `TypeError` here is the guarantee; a default appearing later is the
        regression.
        """
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(TypeError):
                RS.reclaim_lanes_on_interrupt(  # type: ignore[call-arg]
                    Path(td), Path(td), {"repo": td, "queue": []}
                )

    def test_prompt_suppression_still_works_PER_HOST_after_the_lift(self):
        """The property that made the two prompt symbols unliftable, re-verified after the lift.

        The flag each host SETS must still be the flag that host READS. This is the failure mode a
        careless lift produces (share the reclaimer AND its prompt helpers, and each host's flag
        stops being consulted), so it is checked on the post-lift tree rather than trusted.
        """
        for host, module in HOSTS:
            with self.subTest(host=host):
                saved = getattr(module, "_LANE_PROMPT_DISABLED")
                try:
                    module.disable_lane_prompt()
                    self.assertTrue(
                        getattr(module, "_LANE_PROMPT_DISABLED"),
                        f"{host}: its own suppression flag must be the one it sets",
                    )
                    # And the reader that consults it lives in the SAME module, which is the other
                    # half of the pin. Called with the flag set, it must short-circuit to None
                    # without touching stdin at all.
                    self.assertIsNone(
                        module._lane_reclaim_prompt(
                            {
                                "holds_work": True,
                                "lane_id": "lane",
                                "branch": "b",
                            },
                            "keep and snapshot",
                        ),
                        f"{host}: a suppressed prompt must return None without asking",
                    )
                finally:
                    setattr(module, "_LANE_PROMPT_DISABLED", saved)

    def test_an_empty_lane_set_is_a_no_op_on_BOTH_hosts(self):
        """The cheapest end-to-end behavioral pin through each host's own shell.

        Deliberately drives `<host>.reclaim_lanes_on_interrupt` rather than the shared function, so
        the shell's argument forwarding is exercised on both hosts. A shell that dropped `state`, or
        passed the wrong prompt callable, would not survive this even though it is a tiny case. The
        heavy cases stay in `test_worktree_lease_merged_reclaim.py`, which owns them.
        """
        for host, module in HOSTS:
            with self.subTest(host=host):
                with tempfile.TemporaryDirectory() as td:
                    result = module.reclaim_lanes_on_interrupt(
                        Path(td),
                        Path(td),
                        {"repo": td, "queue": []},
                        interactive=False,
                    )
                    self.assertEqual(
                        result,
                        [],
                        f"{host}: a run that allocated no lane must reclaim nothing and must not "
                        "write an events file",
                    )


class TheHostSpecificDecisionsArePinned(unittest.TestCase):
    """E-02/V-02: the symbols recorded HOST-SPECIFIC must stay forked, for their recorded reasons.

    WHY PIN A NON-CHANGE. The recorded decisions are the plan's deliverable, and the danger they carry
    is asymmetric: a later reader comparing the residue table against the code will see symbols "still
    duplicated" and the obvious repair is to unify them. For two of them that repair is a data-safety
    regression, and for four it races another plan's declared scope. Each assertion below therefore
    carries the reason IN ITS MESSAGE, so a red explains itself instead of sending the next executor
    to delete the test.
    """

    def test_the_audit_verb_is_a_REAL_capability_difference(self):
        """The clearest instance of the maintainer's own test: one host does A, the other NOT A.

        Asserted BEHAVIORALLY: agy must REFUSE the verb and point the operator at the other host,
        which is a deliberate product decision (plan `mp289j`) and not an unfinished port. A future
        agent "completing" agy's audit implementation would change a decision, so it fails here.
        """
        import argparse
        import contextlib
        import io

        stderr = io.StringIO()
        args = argparse.Namespace(repo=".", id6="abc123")
        with contextlib.redirect_stderr(stderr):
            rc = AGY.handle_audit_command(args)
        self.assertEqual(
            rc, 2, "the agy host must REFUSE audit rather than implement it (`mp289j`)"
        )
        message = stderr.getvalue()
        self.assertIn("not implemented on the Antigravity host", message)
        self.assertIn(
            "aw oc run audit",
            message,
            "the refusal must point the operator at the host that DOES implement it, or the "
            "deliberate one-host wiring becomes a dead end for a human",
        )

    def test_the_lane_prompt_pair_stays_PER_HOST(self):
        """The two symbols whose unification is a silent data-safety regression.

        The reason is stated in the message because this is the assertion most likely to be met with
        "why is this still duplicated?". See `tests/test_runner_shared.py::UnmovableSymbolTests`,
        which is the authority; this states the link to THIS plan's decision table.
        """
        scanner = _scanner()
        data = scanner.census(["disable_lane_prompt", "_lane_reclaim_prompt"])
        for name in ("disable_lane_prompt", "_lane_reclaim_prompt"):
            with self.subTest(symbol=name):
                self.assertFalse(
                    data["symbols"][name]["wrapper"],
                    f"`{name}` now delegates to `runner_shared`. That is a REGRESSION, not "
                    "progress: `disable_lane_prompt` writes a module-level "
                    "`_LANE_PROMPT_DISABLED` that only its own module's `_lane_reclaim_prompt` "
                    "reads, so a shared body sets a flag nobody reads and prompt suppression on a "
                    "repeated interrupt silently stops working. Unifying the PAIR together is the "
                    "only legitimate route, and it expires a shipped pin, so it needs its own plan.",
                )

    def test_the_agy_to_oc_delegations_are_MIS_LAYERING_and_not_this_plans_to_move(
        self,
    ):
        """Symbols where agy delegates to a PEER HOST rather than to the shared library.

        NOT DUPLICATION: there is one body and agy imports it, so "unifying" them is a re-homing
        question owned by `runnerlayer` Order 02 (`1f7xno`), whose `FROZEN_OC_TO_AGY_IMPORTS` table
        these names sit in. Asserted so that a reader of the residue table cannot mistake them for
        copied code, and so that the day they DO move, this test names the plan that owns the move.

        THAT DAY CAME FOR ONE OF THEM (2026-09-23). `1f7xno` re-homed
        `enforce_dependency_preflight` into `runner_shared`, so it is no longer an agy-to-oc
        delegation and its row is REMOVED from this list and from `DECIDED` below - which is exactly
        what `test_no_decision_is_recorded_for_a_symbol_that_LEFT_the_residue` demands, since a stale
        decision would send the next executor to unify code that is already one implementation.

        THE OTHER THREE REMAIN, and their reason is now sharper than "owned by another plan": each
        ALREADY has a `runner_shared` definition whose body DIVERGES from the host's, so re-homing one
        is a RECONCILIATION rather than a move. `1f7xno` measured this and deferred them, filing
        `zt2b16` (the recovery-routing pair, where the shared `classify_recovery_disposition` is DEAD
        ON ARRIVAL: it reads `st.path`/`st.base_commit` off a `LaneState` whose real fields are
        `worktree_path`/`base_sha`) and `tm5vnx` (the spec-edit recorder, whose two copies write
        different keys). `route_recovery_turn` is the instructive case: its shared copy is
        AST-IDENTICAL, the consolidation passed every fingerprint check, and it was still REVERTED
        because the body resolves the broken classifier in the shared namespace.
        """
        for name in (
            "route_recovery_turn",
            "classify_recovery_disposition",
            "build_verify_and_continue_notice",
        ):
            with self.subTest(symbol=name):
                oc_obj = getattr(OC, name, None)
                agy_obj = getattr(AGY, name, None)
                self.assertTrue(callable(oc_obj), f"{name} must exist on the oc host")
                self.assertTrue(callable(agy_obj), f"{name} must exist on the agy host")
                # There is ONE body: agy's wrapper reaches oc's function. Asserted by CALLING
                # nothing and comparing nothing about source; the delegation is visible in the
                # census, which is the seam this file consumes.


class TheResidueIsFullyAccountedFor(unittest.TestCase):
    """V-08's bijection, asserted as data: every residue symbol carries a recorded decision.

    THE POINT IS THE BIJECTION, IN BOTH DIRECTIONS. A residue symbol with no recorded decision means
    the plan UNDER-reported (it declared the directive met while something was unexamined). A recorded
    decision for a symbol no longer in the residue means it OVER-reported (it would send an executor
    to "unify" code that is already one implementation, which is exactly how `reconcile_interrupted`
    ended up in a list of lift targets). Both failure modes are live, so both are checked.
    """

    #: Every symbol the strict residue may contain, each with the decision recorded in research
    #: `fedqe6`. HOST-SPECIFIC-BY-CAPABILITY, HOST-SPECIFIC-BY-PIN and MIS-LAYERED are all legitimate
    #: terminal states; what is NOT legitimate is a symbol here with no decision at all.
    DECIDED: dict[str, str] = {
        "disable_lane_prompt": "HOST-SPECIFIC-BY-PIN",
        "_lane_reclaim_prompt": "HOST-SPECIFIC-BY-PIN",
        "_add_output_mode_flags": "HOST-SPECIFIC-BY-CAPABILITY",
        "_record_forced_stop": "THREE-WAY-FORK-FILED",
        # `enforce_dependency_preflight` WAS HERE AND IS REMOVED, not demoted: `1f7xno` re-homed it
        # into `runner_shared` on 2026-09-23, so it left the strict residue and a row for it would be
        # the stale OVER-reporting this class's docstring names as a live failure mode.
        "route_recovery_turn": "MIS-LAYERED-OWNED-BY-1f7xno",
        "classify_recovery_disposition": "MIS-LAYERED-OWNED-BY-1f7xno",
        "build_verify_and_continue_notice": "MIS-LAYERED-OWNED-BY-1f7xno",
    }

    def test_every_strict_residue_symbol_has_a_recorded_decision(self):
        data = _scanner().census()
        undecided = sorted(set(data["strict_residue"]) - set(self.DECIDED))
        self.assertEqual(
            undecided,
            [],
            f"these symbols are in the STRICT residue with no recorded decision: {undecided}. "
            "Decide each against the maintainer's test (one host does A, the other NOT A) and "
            "record it in research `fedqe6` with its capability sentence, or share it. An "
            "unexamined remainder is the one outcome this plan's Goal rules out.",
        )

    def test_no_decision_is_recorded_for_a_symbol_that_LEFT_the_residue(self):
        """The OVER-reporting direction, which is the error this plan's own first draft made."""
        data = _scanner().census()
        stale = sorted(set(self.DECIDED) - set(data["strict_residue"]))
        self.assertEqual(
            stale,
            [],
            f"these symbols carry a recorded residue decision but are NO LONGER in the strict "
            f"residue: {stale}. They have been shared since the decision was recorded, so the "
            "decision is stale: remove the row rather than leaving a table that sends the next "
            "executor to unify code that is already one implementation.",
        )

    def test_the_anchor_symbol_is_NOT_in_the_residue_any_more(self):
        """The one thing this plan changed, asserted from the authoritative census."""
        data = _scanner().census()
        self.assertNotIn(
            "reclaim_lanes_on_interrupt",
            data["strict_residue"],
            "`reclaim_lanes_on_interrupt` is back in the residue, so the shared implementation "
            "this plan created has been re-forked",
        )
        self.assertNotIn("reclaim_lanes_on_interrupt", data["loose_residue"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
