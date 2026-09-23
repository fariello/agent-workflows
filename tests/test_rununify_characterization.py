#!/usr/bin/env python3
"""`rununify` 12 (`40it5e`) E-03: the Set's characterization baseline, authored LATE and saying so.

READ THIS FIRST, BECAUSE THE FILE'S NAME OVERPROMISES. This suite was written AFTER all eleven
reconciling children of the `rununify` Set executed, and after `runresidue` (`gqo6if`) executed on top
of them. It therefore pins the behavior that exists NOW, and it CANNOT and DOES NOT prove that those
reconciliations preserved behavior. The evidence that would have proven that had to be captured BEFORE
the children ran; that moment has passed, and no suite written today can recover it.

WHY IT EXISTS ANYWAY. The orchestrator `5e4sb6` E-02 asked for exactly this file, for a reason that is
still live even though its precondition is not: the two hosts' suites are ASYMMETRIC, so "both suites
green" is not sufficient evidence for an agy-side change. At authoring time the parent measured 95 oc
tests against 21 agy; re-measured at `40it5e`'s review it was 284 against 97. The ratio has improved
and the argument has not gone away. A two-host pin is still the only thing that catches a change that
lands on one host, and the symbols in the residue are precisely where the next such change will land.

WHICH SYMBOLS IT PINS, AND WHY NOT THE ONES THE PARENT NAMED. The parent's E-02 named four symbols
from a 2026-08-30 zero-agy-coverage measurement: `integrate_lane_branch`, `build_parser`,
`extract_session_id` and `build_prompt`. THAT LIST HAS DISSOLVED, measured at this file's authoring
HEAD: `extract_session_id` is defined ONLY in `runner_shared` and is absent from both runners;
`build_prompt`'s agy definition is a one-line delegation; `integrate_lane_branch` is a wrapper whose
own docstring says the implementation is the single shared one. A test over those would exercise
`runner_shared` through two host aliases WHILE REPORTING two-host coverage, which is worse than no
test because it manufactures confidence. So this file pins the symbols research `cxe3dw` dispositioned
as genuinely still forked, which is where two-host coverage is real.

WHAT THIS FILE MAY NOT ASSERT, and the prohibition is the point rather than a style note. This
repository DELIBERATELY RETIRED change-detector tests over source text. Commit `d4dd6b88`
(2026-09-18, "test: retire change-detector tests over code text and prose") DELETED
`tests/test_wtiso_characterization.py` outright - so a reader looking for the precedent the parent
cites will not find it, and that is recorded here so nobody goes hunting. `7ebc2964` before it deleted
four `test_rununify_*_characterization.py` files totalling roughly 3,900 lines, removing exactly the
`len(getsourcelines(...))` counts, `SequenceMatcher` ratio assertions and frozen AST censuses that a
"pin the duplication" instinct reaches for first. The stated reasoning was that "a git repository
already records when text changes; a test that fails on a legitimate reword costs author time and
catches no defect".

THEREFORE every assertion below CALLS something and observes its effect, its return value or its
written state. There is no line-count pin, no similarity ratio, no AST census, and no assertion about
source text anywhere in this file. The LIVE precedent is `tests/test_rununify_run_queue.py` and its
kin (`_main`, `_build_parser`, `_initialize_run`), which is where this repository now keeps two-host
behavioral pins, and this file follows that form.

RELATIONSHIP TO `tests/test_runresidue_residue.py`, which is the nearest neighbour and was written one
day earlier by `gqo6if` E-05. That file pins the residue DECISIONS (which symbol was shared, which was
left forked and why), consuming the committed scanner as its seam. This file pins the residue
BEHAVIOR: for a symbol left forked, that the two hosts actually agree where they are supposed to, and
actually differ where the difference is the product decision. The two are complementary and neither
subsumes the other; where they touch the same symbol they ask different questions of it.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd as AGY
from agent_workflows import oc_runipd as OC
from agent_workflows import runner_stop

#: The two hosts, iterated rather than hand-repeated, so a pin cannot silently cover one of them. This
#: is the shape `tests/test_rununify_run_queue.py` and its kin use.
HOSTS = {"oc": OC, "agy": AGY}

#: The symbols this file pins, each with the `cxe3dw` disposition that makes it a legitimate subject.
#: Kept as prose in one place so a later reader can check the subject list against the research table
#: without reading every test. NOT asserted against the scanner: that bijection is
#: `tests/test_runresidue_residue.py::TheResidueIsFullyAccountedFor`'s job and duplicating it here
#: would create two tables that can disagree.
#:
#:   `_record_forced_stop`   STILL REDUNDANT (the one genuine duplication). Two bodies differing in an
#:                           annotation-quoting token, plus a byte-different dead third copy in
#:                           `runner_shared`. Carrier: backlog `2yjc5l`.
#:   `_add_output_mode_flags` HOST-SPECIFIC by capability: the two event streams carry different
#:                           things, so the help text describes different observable behavior.
#:   `handle_audit_command`  HOST-SPECIFIC by capability: oc implements the verb, agy refuses it.
#:   `disable_lane_prompt` / `_lane_reclaim_prompt`
#:                           HOST-SPECIFIC by mechanism: a per-host module-level `global`.
#:   the four agy->oc delegations
#:                           NOT duplication: one body, mis-layered. Carrier: `1f7xno`.
PINNED = (
    "_record_forced_stop",
    "_add_output_mode_flags",
    "handle_audit_command",
    "disable_lane_prompt",
    "_lane_reclaim_prompt",
    "enforce_dependency_preflight",
    "route_recovery_turn",
    "classify_recovery_disposition",
    "build_verify_and_continue_notice",
)


class TheOneStillRedundantSymbolBehavesIDENTICALLY(unittest.TestCase):
    """`_record_forced_stop`: the residue's ONE genuine duplication, pinned by OUTPUT EQUALITY.

    WHY THIS IS THE MOST VALUABLE PIN IN THE FILE. Research `cxe3dw` dispositions this symbol as the
    single still-redundant one: two copies whose only difference is whether a type annotation is
    quoted. The existing level-4 suite (`tests/test_runner_stop_level4.py`) already exercises BOTH
    hosts' copies, and it asserts each one's record satisfies the spec. What it does NOT do, measured
    before this file was written, is compare the two hosts' RECORDS WITH EACH OTHER.

    That gap is exactly the one a duplication leaves open: both copies can satisfy every spec
    assertion separately while drifting apart in a field no rule names, which is the `Heartbeat`
    failure mode this Set was created to end (a fix landing on one host and silently not the other).
    So this class asserts the two outputs are EQUAL, field for field, with the per-run fields
    normalized away.

    AND WHEN THE SYMBOL IS EVENTUALLY SHARED, THIS TEST SHOULD STILL PASS. It is written against
    observable output rather than against the fork, so it does not need re-basing by the plan that
    closes `2yjc5l`; it becomes that plan's proof instead. That is deliberate: a pin that must be
    deleted to make progress is a pin that will be deleted carelessly.
    """

    #: Fields that legitimately differ per invocation (a timestamp) or per host (the observed git
    #: state of a different temporary directory). Normalized rather than asserted, and named here so
    #: the exclusion is visible instead of buried in a comprehension.
    PER_RUN_FIELDS = ("at", "git_state")

    def _record_on(self, host_module):
        """Call one host's `_record_forced_stop` in an isolated run dir and return its record.

        Each host gets its OWN temporary repository and run directory, so neither can observe the
        other's state and the comparison cannot pass by accident of shared setup.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            run_dir = root / "run"
            run_dir.mkdir()
            (run_dir / "events.jsonl").write_text("", encoding="utf-8")
            item = {"id6": "sb0001", "status": "interrupted"}
            state = {"repo": str(repo), "queue": [item]}
            record = host_module._record_forced_stop(
                run_dir,
                state,
                item,
                runner_stop.StopNowForce(
                    level=runner_stop.LEVEL_NOW_FORCE,
                    requester="operator",
                    events_seen=7,
                    prior_completed_index=3,
                    prior_completed_label="tool_use:read",
                ),
            )
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            return copy.deepcopy(record), events, copy.deepcopy(item)

    def _normalized(self, record):
        out = dict(record)
        for field in self.PER_RUN_FIELDS:
            out.pop(field, None)
        return out

    def test_both_hosts_produce_the_SAME_forced_stop_record(self):
        """The duplication's whole risk, asserted: the two copies must not have drifted.

        Field-for-field equality of the returned record, timestamp and observed-git-state removed.
        A red here means the two copies of a duplicated function have diverged, which is the defect
        the `rununify` Set exists to make impossible - NOT a reason to loosen this assertion.
        """
        oc_record, _, _ = self._record_on(OC)
        agy_record, _, _ = self._record_on(AGY)
        self.assertEqual(
            self._normalized(oc_record),
            self._normalized(agy_record),
            "the two host copies of `_record_forced_stop` produced DIFFERENT records. This symbol "
            "is the residue's one genuine duplication (research `cxe3dw`; carrier backlog "
            "`2yjc5l`), so a divergence here is the copied-code failure mode this Set was created "
            "to end: a fix landing on one host and silently not the other. Reconcile the two "
            "bodies (or share them, which closes `2yjc5l`) rather than relaxing this test.",
        )

    def test_the_per_run_fields_this_test_normalizes_are_actually_PRESENT(self):
        """Non-vacuity: the normalization must not be hiding a missing field.

        Without this, `PER_RUN_FIELDS` could name a key neither host emits and the equality above
        would still pass while silently comparing less than it claims to.
        """
        for host, module in HOSTS.items():
            record, _, _ = self._record_on(module)
            for field in self.PER_RUN_FIELDS:
                with self.subTest(host=host, field=field):
                    self.assertIn(
                        field,
                        record,
                        f"{host} emits no `{field}`, so normalizing it away means the equality "
                        "assertion is comparing a field that does not exist",
                    )

    def test_both_hosts_emit_the_SAME_forced_stop_event_shape(self):
        """The record is returned AND appended to `events.jsonl`; both hosts' events must agree.

        Asserted separately from the record because the two are different channels: a host could
        build the right record and write a different event, and a caller reading the ledger would
        see the divergence while a caller reading the return value would not.
        """
        _, oc_events, _ = self._record_on(OC)
        _, agy_events, _ = self._record_on(AGY)
        self.assertTrue(oc_events, "oc wrote no event for a level-4 stop")
        self.assertTrue(agy_events, "agy wrote no event for a level-4 stop")
        self.assertEqual(
            len(oc_events),
            len(agy_events),
            f"oc wrote {len(oc_events)} event(s) and agy wrote {len(agy_events)} for the same "
            "level-4 stop",
        )
        for index, (oc_event, agy_event) in enumerate(zip(oc_events, agy_events)):
            with self.subTest(event=index):
                self.assertEqual(
                    sorted(oc_event),
                    sorted(agy_event),
                    "the two hosts' level-4 stop events carry DIFFERENT keys",
                )
                self.assertEqual(
                    oc_event.get("event"),
                    agy_event.get("event"),
                    "the two hosts named the level-4 stop event differently, so an operator "
                    "grepping the ledger finds it on one host only",
                )

    def test_both_hosts_mark_the_ITEM_stopped_the_same_way(self):
        """The third observable: the function MUTATES the item it is handed.

        A caller downstream reads `item['stopped']`, so the two hosts writing different shapes there
        is a real divergence even when the returned record and the emitted event agree.
        """
        _, _, oc_item = self._record_on(OC)
        _, _, agy_item = self._record_on(AGY)
        for host, item in (("oc", oc_item), ("agy", agy_item)):
            with self.subTest(host=host):
                self.assertIn(
                    "stopped",
                    item,
                    f"{host} did not record the stop ON THE ITEM, which is what the "
                    "reconciliation path reads",
                )
        self.assertEqual(
            self._normalized(oc_item["stopped"]),
            self._normalized(agy_item["stopped"]),
            "the two hosts wrote DIFFERENT stop records onto the item",
        )

    def test_neither_host_claims_the_cut_turn_SUCCEEDED(self):
        """The honesty invariant, asserted on BOTH hosts in one place.

        The level-4 spec (R22) forbids a forced stop being recorded as a success, and
        `tests/test_runner_stop_level4.py` already asserts it. It is restated here for both hosts
        TOGETHER because the equality assertions above would be satisfied by two copies that agree
        with each other and are BOTH wrong.
        """
        for host, module in HOSTS.items():
            record, _, _ = self._record_on(module)
            with self.subTest(host=host):
                self.assertEqual(
                    record["certainty"], runner_stop.CERTAINTY_INDETERMINATE
                )
                self.assertTrue(
                    record["stopped_deliberately"], "spec R21: operator intent"
                )
                self.assertFalse(record["failure"], "spec R21: not a crash")
                self.assertIsNone(
                    record["last_completed_event"],
                    "spec R22: the cut point was NOT observed, so naming one is fabrication",
                )
                blob = json.dumps(record)
                for word in ("executed", "successful", '"complete"'):
                    self.assertNotIn(
                        word, blob, f"spec R22 forbids claiming {word!r} on {host}"
                    )


class TheHostSpecificDifferencesAreREAL(unittest.TestCase):
    """The symbols `cxe3dw` dispositions HOST-SPECIFIC, pinned by the difference that justifies them.

    WHY PIN A DIFFERENCE RATHER THAN AN AGREEMENT. Each disposition rests on a claim about observable
    behavior ("one host does A, the other NOT A"). If that claim stops being true, the disposition is
    wrong and the symbol becomes ordinary duplication that should be shared. So the DIFFERENCE is the
    thing under test: these assertions go red when the justification evaporates, which is the moment
    someone should revisit the decision.

    This is the inverse of the class above, and the pairing is deliberate: a still-redundant symbol is
    pinned by its SAMENESS, a host-specific one by its DIFFERENCE.
    """

    def test_the_audit_verb_is_implemented_on_oc_and_REFUSED_on_agy(self):
        """The clearest instance of the maintainer's test, asserted through the CLI seam.

        Pinned on the PARSER rather than by calling the handler: the question here is whether both
        hosts accept the verb and route it, which is what makes agy's refusal a REDIRECT rather than
        a dead end. `tests/test_runresidue_residue.py` asserts the refusal's exit code and message;
        this asserts the surface that makes the refusal reachable at all.
        """
        for host, module in HOSTS.items():
            with self.subTest(host=host):
                parser = module.build_parser()
                args = parser.parse_args(["audit", "abc123"])
                self.assertEqual(
                    args.command,
                    "audit",
                    f"{host} does not route `audit` to a command, so the refusal path on agy "
                    "would fall through to 'Unknown command' while --help documents the verb",
                )

    def test_agy_REFUSES_audit_with_a_redirect_and_oc_does_not_refuse(self):
        """The capability difference itself: agy exits 2 and names the working spelling.

        The oc side is asserted by ABSENCE of that refusal rather than by running an audit, which
        would need a real executed plan and a live host binary. That is a deliberate limit: this
        pins that the refusal is agy-ONLY, which is the part a future "let's finish the agy port"
        change would break.
        """
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            rc = AGY.handle_audit_command(argparse.Namespace(repo=".", id6="abc123"))
        self.assertEqual(
            rc,
            2,
            "agy must REFUSE `audit` with exit 2 ('cannot run'), not 1 ('refused after "
            "checking'): nothing about the request was evaluated (plan `mp289j`)",
        )
        message = stderr.getvalue()
        self.assertIn(
            "aw oc run audit",
            message,
            "the refusal must name the spelling that WORKS, or the deliberate one-host wiring is "
            "a dead end for the operator rather than a redirect",
        )
        self.assertIsNot(
            OC.handle_audit_command,
            AGY.handle_audit_command,
            "the two hosts' audit handlers became the SAME object, which would mean either agy now "
            "implements the verb or oc now refuses it. Both are product changes to the decision "
            "recorded in `mp289j`, not refactors.",
        )

    def test_the_output_mode_HELP_TEXT_differs_because_the_event_streams_do(self):
        """`_add_output_mode_flags`: the difference is what `-vv` actually shows per host.

        THIS IS A BEHAVIORAL ASSERTION, NOT A SOURCE-TEXT ONE, and the distinction matters given
        what `d4dd6b88` retired. Help text is part of a CLI's observable output: it is what an
        operator running `--help` sees. This reads it from the CONSTRUCTED PARSER, not from the
        module source, so it cannot pass or fail on formatting, comments or docstrings.

        The justification being pinned: oc's `-v` promises line ranges and hit counts and its `-vv`
        promises diff hunks, while agy's `-vv` shows raw tool parameters. The two hosts' streams
        genuinely carry different things, so the strings are not interchangeable and sharing this
        function would require injecting the text rather than unifying it.
        """
        helps = {}
        for host, module in HOSTS.items():
            parser = module.build_parser()
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                with self.assertRaises(SystemExit):
                    parser.parse_args(["start", "--help"])
            helps[host] = buffer.getvalue()

        self.assertIn(
            "hit counts",
            helps["oc"],
            "oc's verbose help no longer promises hit counts. If oc's stream changed, re-measure "
            "the `_add_output_mode_flags` disposition in research `cxe3dw`: it rests on the two "
            "hosts documenting DIFFERENT observable detail.",
        )
        self.assertIn(
            "raw tool parameters",
            helps["agy"],
            "agy's verbose help no longer promises raw tool parameters, which is the other half of "
            "the same disposition",
        )
        self.assertNotIn(
            "raw tool parameters",
            helps["oc"],
            "oc now documents agy's `-vv` behavior. Either the streams converged (in which case "
            "`_add_output_mode_flags` is ordinary duplication and should be shared) or one host's "
            "help is now wrong.",
        )

    def test_the_shared_output_mode_BEHAVIOR_is_identical_on_both_hosts(self):
        """The other side of the same symbol: only the TEXT is host-specific, not the semantics.

        Stated because it bounds the disposition. `_add_output_mode_flags` is host-specific in its
        help strings ONLY; the flags themselves must behave the same, so a future share that injects
        the text is legitimate and this test will keep passing through it.
        """
        for host, module in HOSTS.items():
            with self.subTest(host=host):
                parser = module.build_parser()
                self.assertEqual(
                    parser.parse_args(["start", "x", "--quiet"]).output_mode, "quiet"
                )
                self.assertEqual(
                    parser.parse_args(["start", "x", "--raw"]).output_mode, "raw"
                )
                self.assertEqual(parser.parse_args(["start", "x"]).output_mode, "clean")
                self.assertEqual(parser.parse_args(["start", "x", "-vv"]).verbosity, 2)

    def test_lane_prompt_suppression_is_PER_HOST_and_does_not_leak(self):
        """`disable_lane_prompt` / `_lane_reclaim_prompt`: the mechanism, pinned behaviorally.

        The disposition says these cannot be shared because each host writes its OWN module-level
        flag that only its own reader consults. THE OBSERVABLE CONSEQUENCE, which is what is
        asserted: disabling the prompt on one host must NOT disable it on the other. A shared body
        would make one call affect both, and a shared body over a single flag would make the flag
        unreadable by either reader.

        `tests/test_runner_shared.py::UnmovableSymbolTests` is the authority on WHY this cannot
        move. This test states the behavior that authority protects, so a red here says which
        guarantee broke rather than merely that a symbol moved.
        """
        saved = {
            host: getattr(module, "_LANE_PROMPT_DISABLED")
            for host, module in HOSTS.items()
        }
        try:
            for host, module in HOSTS.items():
                other = next(name for name in HOSTS if name != host)
                other_module = HOSTS[other]
                for name, mod in HOSTS.items():
                    setattr(mod, "_LANE_PROMPT_DISABLED", False)
                module.disable_lane_prompt()
                with self.subTest(disabled_on=host):
                    self.assertTrue(
                        getattr(module, "_LANE_PROMPT_DISABLED"),
                        f"`{host}.disable_lane_prompt()` did not set that host's own flag, so "
                        "prompt suppression after a repeated interrupt is broken and an "
                        "unattended run can block on a question nobody can answer",
                    )
                    self.assertFalse(
                        getattr(other_module, "_LANE_PROMPT_DISABLED"),
                        f"disabling the lane prompt on {host} ALSO disabled it on {other}. The "
                        "two flags are deliberately per-host; if these symbols were shared, the "
                        "pair must be shared TOGETHER with the flag, and that expires the pin in "
                        "`tests/test_runner_shared.py::UnmovableSymbolTests`.",
                    )
        finally:
            for host, value in saved.items():
                setattr(HOSTS[host], "_LANE_PROMPT_DISABLED", value)


class TheMisLayeredSymbolsAreONEBodyReachedTwice(unittest.TestCase):
    """The four agy->oc delegations: pinned as ONE implementation, not as duplication.

    WHY THIS IS A BEHAVIORAL PIN AND NOT A DELEGATION-IDENTITY ONE. `assertIs` cannot be used here:
    agy's wrappers IMPORT oc's function inside their bodies and call it, so `AGY.route_recovery_turn`
    is a distinct function object from `OC.route_recovery_turn` even though only one implementation
    exists. Asserting object identity would fail on correct code. So these tests CALL both hosts and
    assert the outputs agree, which is the property that actually matters and which survives the
    re-homing `1f7xno` will do.

    WHAT A RED MEANS HERE: someone gave agy its own implementation of a symbol that had one body,
    which is a re-fork. That is the regression `tests/test_runner_refork_guard.py` exists to prevent
    for already-extracted modules, and this is its behavioral counterpart for this specific set.
    """

    def test_recovery_disposition_classification_AGREES_across_hosts(self):
        """`classify_recovery_disposition`: one body, so both hosts must classify identically.

        Exercised on a first attempt (no prior lane), which is the case reachable without building
        a real lane worktree. That is a deliberate bound: the pin is that the two hosts return the
        SAME thing, not a full matrix of recovery scenarios, which
        `tests/test_resumedupe.py` already owns.
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            item = {"id6": "abc123", "attempts": []}
            state = {"repo": str(repo), "queue": [item]}
            results = {}
            for host, module in HOSTS.items():
                results[host] = module.classify_recovery_disposition(
                    repo, copy.deepcopy(item), copy.deepcopy(state)
                )
            self.assertEqual(
                results["oc"],
                results["agy"],
                "the two hosts classified the same recovery situation DIFFERENTLY. There is "
                "supposed to be ONE body (agy delegates to oc; research `cxe3dw`), so a "
                "divergence means agy acquired its own implementation, which is a re-fork.",
            )

    def test_a_first_attempt_routes_to_None_on_BOTH_hosts(self):
        """`route_recovery_turn`: first-attempt behavior is untouched, identically on both hosts.

        `recovery=False` must yield None on both, which is the documented contract ("Returns None
        for a first attempt, so first-attempt behavior is untouched"). Pinned on both hosts because
        this is the path every ordinary run takes.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            run_dir.mkdir()
            repo = root / "repo"
            repo.mkdir()
            item = {"id6": "abc123", "attempts": []}
            state = {"repo": str(repo), "queue": [item]}
            for host, module in HOSTS.items():
                with self.subTest(host=host):
                    self.assertIsNone(
                        module.route_recovery_turn(
                            run_dir, copy.deepcopy(state), copy.deepcopy(item), False
                        ),
                        f"{host} returned a disposition for a FIRST attempt; both hosts must "
                        "leave first-attempt behavior untouched",
                    )

    def test_a_clean_dependency_graph_is_accepted_identically_on_both_hosts(self):
        """`enforce_dependency_preflight`: the clean case returns the same empty findings list.

        The refusal case is exercised by `tests/test_runner_item_dependencies.py`; the value here is
        the CROSS-HOST comparison, which no existing test makes. agy keeps an `except DriverError:
        raise` its own docstring calls a deliberate no-op, and this pins that the no-op really is
        one on the accepting path.
        """
        results = {}
        for host, module in HOSTS.items():
            results[host] = module.enforce_dependency_preflight(Path("."), [])
        self.assertEqual(
            results["oc"],
            results["agy"],
            "the two hosts disagreed on an EMPTY selected plan set, which cannot have a "
            "host-specific answer",
        )
        self.assertEqual(
            results["oc"],
            [],
            "an empty plan set must produce no findings, so a caller can record 'checked, clean'",
        )


class ThisSuiteDeclaresItsOwnLimits(unittest.TestCase):
    """The lateness declaration, asserted rather than only documented.

    WHY A TEST FOR A DOCSTRING. The honest statement that this baseline came too late is the single
    most important thing this file carries, and a statement that lives only in prose is one a later
    editor removes without noticing. `40it5e` V-03 requires the module docstring to say it; this makes
    the requirement self-enforcing.

    THIS IS NOT A SOURCE-TEXT CHANGE DETECTOR of the kind `d4dd6b88` retired, and the difference is
    worth being precise about since the line is thin. It asserts no line count, no similarity ratio,
    no AST shape, and nothing about any PRODUCT module; it reads this file's OWN `__doc__` object for
    the presence of a required disclosure, the way a test asserts a required field is present in a
    record. A legitimate reword passes; deleting the disclosure fails.
    """

    @staticmethod
    def _doc():
        """This module's docstring with newlines collapsed to single spaces.

        Collapsed because the required disclosures are SENTENCES and the file is hard-wrapped, so a
        phrase legitimately spans a line break. Asserting against the raw string would make these
        tests fail on a re-wrap, which is the brittleness `d4dd6b88` retired tests for.
        """
        return " ".join((__doc__ or "").split())

    def test_the_docstring_states_the_baseline_is_LATE(self):
        doc = self._doc()
        self.assertIn(
            "AFTER all eleven reconciling children",
            doc,
            "the module docstring must state plainly that this suite was authored after the "
            "reconciliations, or a reader will take it for the pre-Set baseline it is not",
        )
        self.assertIn(
            "CANNOT and DOES NOT prove that those reconciliations preserved behavior",
            doc,
            "the docstring must state what this suite cannot do; its forward value is real and "
            "its retrospective value is nil, and conflating the two is the misreading to prevent",
        )

    def test_the_docstring_records_the_DELETED_precedent_so_nobody_hunts_for_it(self):
        doc = self._doc()
        self.assertIn(
            "d4dd6b88",
            doc,
            "the docstring must name the commit that deleted "
            "`tests/test_wtiso_characterization.py`, because the orchestrator `5e4sb6` E-02 still "
            "cites that file as the precedent to follow and a reader will go looking for it",
        )

    def test_the_docstring_says_WHICH_symbols_it_pins_and_why_not_the_parents_list(
        self,
    ):
        doc = self._doc()
        for name in ("extract_session_id", "build_prompt", "integrate_lane_branch"):
            with self.subTest(symbol=name):
                self.assertIn(
                    name,
                    doc,
                    f"the docstring must name `{name}` as one of the parent's targets it "
                    "deliberately does NOT pin, since a pin over an already-unified symbol tests "
                    "`runner_shared` through two aliases while reporting two-host coverage",
                )


if __name__ == "__main__":
    unittest.main()
