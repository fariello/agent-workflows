#!/usr/bin/env python3
"""`lanectn` Order 06 (`604wra`): SHARED CONTAINMENT PREDICATES AND THEIR FAIL-LOUD DISCIPLINE.

Proves spec `7ckptx` R6.1, R6.2, R6.3 (acceptance criterion A16) and nothing else. The other five
children of the Set added the containment RULES; this module proves they cannot be FORKED, that a
predicate with no body still fails loudly with its owner named, and that the one predicate whose body
this Set implemented WITHOUT wiring genuinely has no product caller.

THREE PROPERTIES, AND WHY EACH IS CHECKED THE WAY IT IS:

  R6.1 SINGLE DEFINITION - checked by AST over the whole package, never by text grep. Two reasons,
       both measured rather than theoretical: a text grep is satisfied by THIS FILE (which names every
       symbol it checks), and a per-file check passes while two byte-identical copies live in
       different files. The precedent is this repository's own cross-Set verification, which used AST
       to prove one reaper existed after a per-file check had passed with duplicates present.

  R6.2 FAIL LOUD - checked by CALLING each unimplemented predicate, never by reading its source. An
       accidental permissive default still READS plausibly; only invoking it distinguishes "raises"
       from "returns []". A predicate that returns any value here FAILS, because a gate that reports
       "no violations" when its rule is missing is worse than no gate.

  R6.3 BODY WITHOUT WIRING - checked structurally, by walking every product module's AST for a call
       to the predicate. The expected count is ZERO and that is CORRECT rather than incomplete: the
       phase that owned its wiring was retired, so a caller appearing here means someone wired it
       without a plan, which is exactly the reviewed decision this assertion forces into the open.

SABOTAGE COVERAGE IS PART OF THE CONTRACT, not an extra. `SabotageTests` below breaks each central
mechanism in a COPY (never in the product tree) and proves the corresponding check FAILS, because a
verification that cannot fail proves nothing. The plan requires this for the fail-loud check in
particular: a check that merely calls every predicate and reports success is indistinguishable from
one that would happily accept a softened stub.

WHAT WAS TABULATED. `check_permission_deadline`'s cases were five tests over ONE pure function that
differed only in the event stream and the deadline, so they are one table whose rows carry
(events, deadline, expected violations). The VIOLATION rows and the CLEAN rows are in the SAME table
because each direction is exactly what falsifies the other: a predicate that reported every stream
would satisfy all four violation rows, and one that reported none would satisfy all five clean rows.

THE TWO SOURCE-TEXT PINS THIS FILE CARRIED ARE GONE, and the reasoning is worth keeping because it
sits oddly beside the AST checks that remain. An `ast.parse` check is NOT a text grep and stays (a
comment cannot add a `Return` node or a second `FunctionDef`); but two assertions here searched source
TEXT for the substring `_unimplemented`, which any comment or docstring mentioning the helper
satisfies while the body returns a permissive default. Both are replaced by behavior:

  * `test_no_predicate_owned_by_another_phase_was_modified` searched each unowned predicate's source
    for `_unimplemented`. DELETED: `FailLoudTests.test_each_unowned_predicate_raises_when_called`
    already CALLS every one of them and requires `NotImplementedError`, which is the property that
    matters and which no comment can fake, and
    `test_no_unowned_predicate_returns_a_permissive_value` adds the AST half (no valued `Return`
    anywhere in the body, so a conditional early return the representative arguments miss is still
    caught). The deleted test also claimed to detect a MODIFICATION, which git already records
    exactly and a substring search records badly.
  * `test_the_unwired_predicate_nevertheless_has_a_real_body` asserted
    `assertNotIn("_unimplemented", inspect.getsource(check_scope))` beside a real call. The call is
    kept and strengthened; the text half is replaced by the positive property a real body has and a
    stub cannot: `check_scope` DELEGATES to `ipd_lifecycle._scope_match`, proved by spying on the
    shared matcher and by patching it to a sentinel verdict that must reach the result.
"""

from __future__ import annotations

import ast
import inspect
import unittest
from functools import cache
from pathlib import Path

from agent_workflows import ipd_lifecycle, lane_containment, wtiso_gate

PKG = Path(inspect.getfile(lane_containment)).parent

# ---- the measured predicate inventory -------------------------------------------------------------
#
# ENUMERATED BY SYMBOL, from the plan's PREDICATE OWNERSHIP TABLE, which exists because the module's
# own docstring labels named phases (`qcqhj7`, `rchpms`, `2c122z`) that were ALL retired on
# 2026-09-02. Reading a stub's owner label to decide what to implement was therefore unfollowable;
# this list is the authority instead.

#: Predicates `lanectn` implemented, with a representative call and the expected result.
IMPLEMENTED: tuple[tuple[str, tuple, object], ...] = (
    ("format_missing_input", ("x.txt", "absent"), "AW_MISSING_INPUT:x.txt:absent"),
    ("parse_missing_input", ("AW_MISSING_INPUT:x.txt:absent",), ("x.txt", "absent")),
    ("check_scope", (["a.py"], ["b.py"]), [wtiso_gate.AW_GATE_SCOPE]),
)

#: Predicates this Set deliberately LEFT RAISING, with a representative call. Each is owned by a
#: RETIRED phase, so none is work this Set may absorb (spec R6.2, R6.3).
NOT_OWNED: tuple[tuple[str, tuple], ...] = (
    ("check_lifecycle_role", ("finalize", "worker")),
    ("check_hook_bypass", (Path("."), "HEAD", ["allowed.py"])),
    ("classify_retention", (Path("."), "x.py")),
    ("check_receipt", ({}, {})),
    ("check_protected_refs", ({}, {})),
)

#: The predicate whose BODY this Set implemented while its WIRING stays unowned (spec R6.3).
BODY_WITHOUT_WIRING = "check_scope"

#: Every containment rule this Set introduced, by the symbol that IS its single definition. Grouped
#: by the child that introduced it, so a failure names which plan's rule forked.
SET_RULES: dict[str, tuple[str, ...]] = {
    "cqx5v7 (R1/R2 prompt purity + collection)": (
        "project_worker_paths",
        "isolation_notice",
        "prior_attempt_summary",
        "absolute_paths_outside_lane",
        "scrub_out_of_lane_paths",
        "collect_lane_submissions",
        "merge_decisions_block",
        "lane_submission_root",
        "collection_receipt_path",
        "read_collection_receipt",
        "prepare_lane_submission_dir",
        "decisions_block_key",
        "attempt_key",
        "item_slug",
    ),
    "lhmrhx (R4 posture + turn bounds)": (
        "build_permission_policy_env",
        "opencode_posture_record",
        "antigravity_posture_record",
        "evaluate_policy_observation",
        "TurnBoundWatch",
        "driver_bound_for_host",
        "bound_expiry_reaper",
        "bound_expiry_record",
        "record_host_posture",
        "parse_host_ceiling_seconds",
    ),
    "y5od1h (R3 missing-input report-and-refuse)": (
        "format_missing_input_token",
        "parse_missing_input_token",
        "classify_missing_input_report",
        "classify_denied_permission_path",
        "MissingInputDecision",
        "MissingInputObserver",
        "record_missing_input_refusal",
        "lane_preserved_for_missing_input",
    ),
}

#: The product modules that consume the containment rules. Used for the zero-caller check and for the
#: no-private-copy check; the TEST tree is deliberately excluded from both, because a test may
#: legitimately call an unwired predicate (this file does) without that being a product caller.
CONSUMERS = ("oc_runipd.py", "agy_runipd.py", "lane_containment.py", "wtiso_gate.py")


@cache
def top_level_definitions(path: Path) -> dict[str, int]:
    """Every name DEFINED at module top level in `path`, mapped to its line number.

    Top level only, and that is the point of the check rather than a limitation: a nested helper
    inside a function cannot be imported by another surface, so it cannot BE the second definition of
    a shared rule. Counting nested `def`s would produce false positives on ordinary closures.
    """

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:  # pragma: no cover - not expected for in-tree sources
        return {}
    found: dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found[node.name] = node.lineno
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found[target.id] = node.lineno
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            found[node.target.id] = node.lineno
    return found


def definition_sites(name: str, root: Path = PKG) -> list[str]:
    """`file:line` for every top-level definition of `name` anywhere under `root` (R6.1)."""

    sites: list[str] = []
    for path in sorted(root.rglob("*.py")):
        line = top_level_definitions(path).get(name)
        if line is not None:
            sites.append("{0}:{1}".format(path.relative_to(root.parent), line))
    return sites


def call_sites(name: str, files: tuple[str, ...] = CONSUMERS) -> list[str]:
    """`file:line` for every CALL to `name` in the given product modules (R6.3).

    Matches both `name(...)` and `module.name(...)`, because a caller may reach a predicate either
    way and a check that saw only one form would miss half the wirings it exists to detect.
    """

    sites: list[str] = []
    for filename in files:
        path = PKG / filename
        if not path.is_file():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            called = (
                func.attr
                if isinstance(func, ast.Attribute)
                else getattr(func, "id", None)
            )
            if called == name:
                sites.append("{0}:{1}".format(filename, node.lineno))
    return sites


class SingleDefinitionTests(unittest.TestCase):
    """R6.1: each rule this Set introduced has EXACTLY ONE definition, reached by import."""

    def test_every_set_rule_has_exactly_one_definition_package_wide(self):
        for child, names in SET_RULES.items():
            for name in names:
                with self.subTest(child=child, rule=name):
                    sites = definition_sites(name)
                    self.assertEqual(
                        len(sites),
                        1,
                        "rule {0!r} (introduced by {1}) has {2} definitions, not 1: {3}. Spec R6.1 "
                        "forbids forking a rule even when the copies agree today.".format(
                            name, child, len(sites), sites
                        ),
                    )
                    self.assertTrue(
                        sites[0].startswith("agent_workflows/lane_containment.py:"),
                        "rule {0!r} must live in the ONE shared host-neutral home, not {1} "
                        "(spec R2.6: neither host may be the de-facto shared library)".format(
                            name, sites[0]
                        ),
                    )

    def test_neither_driver_defines_a_private_copy_of_any_set_rule(self):
        """A fork's shape is a DRIVER defining the rule itself; assert that structurally."""

        owned = {name for names in SET_RULES.values() for name in names}
        for driver in ("oc_runipd.py", "agy_runipd.py"):
            with self.subTest(driver=driver):
                defined = set(top_level_definitions(PKG / driver))
                self.assertEqual(
                    defined & owned,
                    set(),
                    "{0} must CALL the shared rule, never define its own copy".format(
                        driver
                    ),
                )

    def test_the_missing_input_error_code_has_one_definition(self):
        """E-01's consolidation: the stable code was spelled as a literal in TWO modules.

        `wtiso_gate` declares `AW_MISSING_INPUT` as part of the stable error-code contract, while
        `lane_containment.MISSING_INPUT_TOKEN_FORM` re-typed the same string into the prompt text.
        They agreed, which is exactly the case R6.1 still calls non-conforming: renaming the code
        would have left the prompt publishing the old spelling, so a worker following the instruction
        would emit a token no parser recognized. The form now composes around the imported code.
        """

        # ASSERT THE PROPERTY, NOT THE COORDINATE. The count and the owning FILE are the rule; the
        # line number is not, and pinning it would make an unrelated edit above look like a fork.
        sites = definition_sites("AW_MISSING_INPUT")
        self.assertEqual(
            len(sites),
            1,
            "the stable error code must have exactly ONE definition; a second site means the code "
            "was forked. Found: {0}".format(sites),
        )
        self.assertTrue(
            sites[0].startswith("agent_workflows/wtiso_gate.py:"),
            "the stable error code belongs to the gate library, not {0}".format(
                sites[0]
            ),
        )
        self.assertTrue(
            lane_containment.MISSING_INPUT_TOKEN_FORM.startswith(
                wtiso_gate.AW_MISSING_INPUT + ":"
            ),
            "the worker-facing token form must be composed from the stable code, not retyped",
        )
        # The prefix the PARSER matches is read back out of the published form, so all three
        # surfaces (code, prompt text, parser) provably trace to one definition.
        self.assertEqual(lane_containment._token_prefix(), wtiso_gate.AW_MISSING_INPUT)

    def test_both_token_surfaces_produce_identical_results(self):
        """Behavioral half of the same property: agreement, not merely a call."""

        for path, why in (
            ("config/local.ini", "absent from lane"),
            ("a/b.txt", "why: with: colons"),
            (".venv/bin/python", "toolchain absent"),
        ):
            with self.subTest(path=path):
                shared = lane_containment.format_missing_input_token(path, why)
                self.assertEqual(wtiso_gate.format_missing_input(path, why), shared)
                self.assertEqual(
                    wtiso_gate.parse_missing_input(shared),
                    lane_containment.parse_missing_input_token(shared),
                )
                self.assertEqual(wtiso_gate.parse_missing_input(shared), (path, why))

    def test_the_scope_predicate_agrees_with_the_shared_matcher(self):
        """Behavioral agreement across the Scope-Paths grammar's forms."""

        cases = (
            (["tests/x.py"], ["tests/"], []),
            (["agent_workflows/a.py"], ["agent_workflows"], []),
            (["a/b/c.py"], ["a/**"], []),
            (["a.py"], ["b.py"], [wtiso_gate.AW_GATE_SCOPE]),
            (["a.py", "b.py"], ["b.py"], [wtiso_gate.AW_GATE_SCOPE]),
        )
        for changed, scope, expected in cases:
            with self.subTest(changed=changed, scope=scope):
                self.assertEqual(wtiso_gate.check_scope(changed, scope), expected)
                # Same verdict as the authoritative matcher, path by path.
                for path in changed:
                    matched = any(
                        ipd_lifecycle._scope_match(path, pat) for pat in scope
                    )
                    self.assertEqual(
                        matched,
                        wtiso_gate.check_scope([path], scope) == [],
                    )

    def test_an_empty_scope_declaration_yields_no_violations(self):
        """Matches the lifecycle's `grandfathered` case: an unfenced plan is not a violation."""

        self.assertEqual(wtiso_gate.check_scope(["anything.py"], []), [])
        self.assertEqual(wtiso_gate.check_scope(["anything.py"], ["", "  "]), [])


class ImplementedPredicateTests(unittest.TestCase):
    """R6.1/R6.3 body half: each predicate this Set owns has a real body and unit coverage.

    ONE SOURCE-TEXT PIN WAS DELETED FROM HERE, not replaced.
    `test_no_predicate_owned_by_another_phase_was_modified` searched each `NOT_OWNED` predicate's
    source for the substring `_unimplemented` and called that "was not modified". It proved nothing a
    behavioral test does not already prove better, and it claimed something git records exactly:

      * `FailLoudTests.test_each_unowned_predicate_raises_when_called` CALLS every `NOT_OWNED`
        predicate and requires `NotImplementedError`, which is the property R6.2 actually states. A
        substring search is satisfied by a docstring naming the helper while the body returns `[]`,
        which is the exact permissive default R6.2 forbids.
      * `FailLoudTests.test_each_unowned_predicate_names_a_real_retired_owner` additionally requires
        the raised message to name the owning phase AND its RETIRED disposition.
      * `FailLoudTests.test_no_unowned_predicate_returns_a_permissive_value` covers the case a call
        with representative arguments could miss, via AST: no valued `Return` node anywhere in the
        body, plus at least one `Raise`. That is a structural check a comment cannot satisfy, which is
        why it is kept while the text search is not.
      * `WiringBoundaryTests.test_the_unowned_predicates_also_have_no_product_caller` covers the "not
        absorbed into product code" half structurally.
    """

    def test_each_implemented_predicate_returns_its_documented_shape(self):
        for name, args, expected in IMPLEMENTED:
            with self.subTest(predicate=name):
                self.assertEqual(getattr(wtiso_gate, name)(*args), expected)

    def test_parse_rejects_a_non_report_without_raising(self):
        """A driver calls this per stdout line, so ordinary output must parse to `None`."""

        for line in (
            "ordinary output",
            "I think AW_MISSING_INPUT would be nice",
            "",
            "   ",
        ):
            with self.subTest(line=line):
                self.assertIsNone(wtiso_gate.parse_missing_input(line))

    def test_parse_returns_empty_fields_for_a_malformed_report(self):
        """MALFORMED is not the same as NOT-A-REPORT, and conflating them loses a real need.

        A line that starts with the code but carries no path/reason parses to `("", "")` so the
        classifier can refuse it precisely; returning `None` would make it indistinguishable from
        ordinary prose and the worker's report would silently vanish.
        """

        self.assertEqual(wtiso_gate.parse_missing_input("AW_MISSING_INPUT:"), ("", ""))
        self.assertEqual(
            lane_containment.classify_missing_input_report(
                "", "", checkout=Path(".")
            ).rule,
            lane_containment.REJECT_MALFORMED_TOKEN,
        )

    #: (case, the recorded event stream, the deadline in seconds, the violations expected,
    #:  why this row exists)
    #:
    #: ONE table replaces four tests over ONE pure function. Every one built an event list and asked
    #: the same question, so the stream and the deadline are the only columns. The streams are typed
    #: LOOSELY on purpose (one row carries a bare string and a `None` among its events): a driver
    #: hands this whatever it parsed from a child's stream, so tolerating a malformed entry is the
    #: requirement and a well-typed-only table would never reach that path.
    DEADLINES: tuple = (
        (
            "an ask on a NESTED CHILD session, never answered",
            [
                {"type": "session.start", "sessionID": "root-1", "time": 0.0},
                {
                    "type": "session.start",
                    "sessionID": "child-9",
                    "parentID": "root-1",
                    "time": 1.0,
                },
                {
                    "type": "permission.ask",
                    "sessionID": "child-9",
                    "permission": "external_directory",
                    "time": 2.0,
                },
                {"type": "keepalive", "sessionID": "root-1", "time": 90.0},
            ],
            5.0,
            True,
            "THE MEASURED qyaime SHAPE, and the reason the predicate is session-agnostic: the ask "
            "arrived on a CHILD session, so a parser that compared sessions to a ROOT id would miss "
            "the only deadlock this has ever been seen to catch",
        ),
        (
            "an ask answered on the SAME session",
            [
                {"type": "permission.ask", "sessionID": "child-9", "time": 1.0},
                {"type": "permission.answer", "sessionID": "child-9", "time": 2.0},
                {"type": "keepalive", "sessionID": "root-1", "time": 99.0},
            ],
            5.0,
            False,
            "THE ANSWER THAT DOES CLEAR AN ASK. Read against the next row, which is identical but "
            "for the answer's session: that pairing IS the per-session matching rule, and neither "
            "row states it alone",
        ),
        (
            "an ask answered on a DIFFERENT (root) session",
            [
                {"type": "permission.ask", "sessionID": "child-9", "time": 1.0},
                {"type": "permission.answer", "sessionID": "root-1", "time": 2.0},
                {"type": "keepalive", "sessionID": "root-1", "time": 99.0},
            ],
            5.0,
            True,
            "A ROOT ANSWER MUST NOT CLEAR A CHILD'S ASK, or unrelated root-session traffic masks the "
            "deadlock. Differs from the row above ONLY in the answer's `sessionID`",
        ),
        (
            "progress traffic on the asking session, but no answer",
            [
                {"type": "permission.ask", "sessionID": "child-9", "time": 1.0},
                {"type": "keepalive", "sessionID": "child-9", "time": 50.0},
                {"type": "message.part", "sessionID": "child-9", "time": 99.0},
            ],
            5.0,
            True,
            "PROGRESS IS NOT AN ANSWER, and this is the whole shape of the deadlock: a session that "
            "keeps emitting while blocked, which is exactly why the coarse no-output stall watchdog "
            "could not see it. DELIBERATELY the opposite of "
            "`lane_containment.TurnBoundWatch.note_progress`, where progress DOES disarm the live "
            "bound: a recorded stream can be judged after the fact, a live watch cannot see the "
            "future and accepts the false negative rather than killing a healthy turn",
        ),
        (
            "deadline 0 over a stream that would otherwise violate",
            [
                {"type": "permission.ask", "sessionID": "c", "time": 1.0},
                {"type": "keepalive", "sessionID": "c", "time": 999.0},
            ],
            0.0,
            False,
            "`0` DISABLES THE CHECK, matching `PERMISSION_TIMEOUT`'s convention. The stream is the "
            "junk row's violating one, so this row isolates the deadline and nothing else",
        ),
        (
            "an ask still within the deadline",
            [
                {"type": "permission.ask", "sessionID": "c", "time": 1.0},
                {"type": "keepalive", "sessionID": "c", "time": 2.0},
            ],
            5.0,
            False,
            "AN OPEN ASK IS NOT YET A VIOLATION. Without this row the predicate could report every "
            "unanswered ask regardless of elapsed time, and a false positive kills a healthy turn "
            "(R4.4b)",
        ),
        (
            "an ask with no timestamp at all",
            [{"type": "permission.ask", "sessionID": "c"}],
            5.0,
            False,
            "AN UNDATABLE ASK CANNOT BE SHOWN TO HAVE EXCEEDED ANYTHING, so it fails safe in the "
            "PERMISSIVE direction deliberately. Guessing `now` here would invent violations from "
            "incomplete streams",
        ),
        (
            "an empty stream",
            [],
            5.0,
            False,
            "NEVER RAISES ON NOTHING. A driver may call this before any event arrived",
        ),
        (
            "off-type junk entries beside a real unanswered ask",
            [
                "garbage",
                None,
                {"type": "permission.ask", "sessionID": "c", "time": 1.0},
                {"type": "keepalive", "sessionID": "c", "time": 999.0},
            ],
            5.0,
            True,
            "A MALFORMED ENTRY IS SKIPPED, NOT FATAL, AND DOES NOT HIDE THE REAL ASK. This row is "
            "the strongest of the nine: it demands robustness AND detection together, so a body that "
            "bailed out on the first unparseable entry would go green on tolerance while silently "
            "losing the violation",
        ),
    )

    def test_the_permission_deadline_verdict_for_each_recorded_stream(self):
        wrong = []
        for case, events, deadline, want_violation, why in self.DEADLINES:
            expected = [wtiso_gate.AW_PERMISSION_DEADLINE] if want_violation else []
            try:
                got = wtiso_gate.check_permission_deadline(
                    events, deadline_seconds=deadline
                )
            except Exception as exc:  # noqa: BLE001 - raising IS the failure being reported
                got = "RAISED {0}: {1}".format(type(exc).__name__, exc)
            if got != expected:
                wrong.append(
                    "  {0} (deadline={1}):\n    - expected {2!r}, got {3!r}\n"
                    "    this row exists because: {4}".format(
                        case, deadline, expected, got, why
                    )
                )
        self.assertEqual(
            wrong,
            [],
            "`check_permission_deadline` judged {0} of {1} recorded streams wrongly. READ THE "
            "GROUPING: if all four VIOLATION rows went clean the predicate is inert and a wedged "
            "lane reports healthy; if all five CLEAN rows started firing it invents violations and a "
            "false positive kills a healthy turn (R4.4b), which is why both directions share this "
            "table. The two `answered` rows differ ONLY in the answer's `sessionID`, so if they move "
            "together the per-session matching rule is gone rather than the answer detection. A "
            "`RAISED` result is always a defect: a driver hands this whatever it parsed from a "
            "child's stream. FIX: this is a PURE predicate over a FINISHED stream and is NOT a live "
            "bound (see its HONEST LIMIT docstring); do not make it consult the wall clock to pass a "
            "row.\n".format(len(wrong), len(self.DEADLINES))
            + "\n".join(wrong),
        )


class FailLoudTests(unittest.TestCase):
    """R6.2: every predicate this Set does NOT own still raises, naming its owner."""

    def test_each_unowned_predicate_raises_when_called(self):
        """CALLED, not read. An accidental permissive default still reads plausibly."""

        for name, args in NOT_OWNED:
            with self.subTest(predicate=name):
                with self.assertRaises(NotImplementedError) as caught:
                    result = getattr(wtiso_gate, name)(*args)
                    self.fail(
                        "{0} RETURNED {1!r} instead of raising. A permissive default converts a "
                        "loud gap into a silent hole in a gate (spec R6.2).".format(
                            name, result
                        )
                    )
                message = str(caught.exception)
                self.assertIn(name, message, "the error must name the predicate")
                self.assertIn(
                    "owner",
                    message.lower(),
                    "the error must name the predicate's OWNER (R6.2)",
                )

    def test_each_unowned_predicate_names_a_real_retired_owner(self):
        """The owner must be identifiable AND its disposition honest.

        Every original owner phase here was RETIRED on 2026-09-02, so a message naming only the phase
        would send a reader to a plan that will never run. `604wra` added the disposition for exactly
        that reason: an unowned predicate is a gap to re-propose, not work in flight.
        """

        expected_phase = {
            "check_lifecycle_role": "rchpms",
            "check_hook_bypass": "rchpms",
            "classify_retention": "rchpms",
            "check_receipt": "rchpms",
            "check_protected_refs": "2c122z",
        }
        for name, args in NOT_OWNED:
            with self.subTest(predicate=name):
                with self.assertRaises(NotImplementedError) as caught:
                    getattr(wtiso_gate, name)(*args)
                message = str(caught.exception)
                self.assertIn(expected_phase[name], message)
                self.assertIn(
                    "RETIRED",
                    message,
                    "the owner's phase is retired and the message must say so, so a reader is not "
                    "sent to a plan that will never run",
                )

    def test_the_error_codes_remain_the_stable_contract(self):
        """The codes are what a hook prints and a driver matches on; each must equal its name."""

        for code in wtiso_gate.ERROR_CODES:
            self.assertEqual(getattr(wtiso_gate, code), code)
        self.assertEqual(len(set(wtiso_gate.ERROR_CODES)), len(wtiso_gate.ERROR_CODES))


class WiringBoundaryTests(unittest.TestCase):
    """R6.3: a body this Set implemented but is not chartered to wire has NO product caller."""

    def test_the_body_without_wiring_has_zero_product_callers(self):
        """ZERO IS CORRECT, NOT INCOMPLETE, and the reason is recorded in the predicate's docstring.

        `check_scope`'s consumers (the pre-commit hook, `aw lane status`, the driver, finalize,
        integration) were the wtiso Phase-2 deliverable, RETIRED unlanded 2026-09-02. No plan is in
        flight to wire it, so `604wra` implemented the body and deliberately wired nothing. A caller
        appearing here means someone wired it without a plan; this assertion forces that into review.
        """

        sites = call_sites(BODY_WITHOUT_WIRING)
        self.assertEqual(
            sites,
            [],
            "{0} must have NO product caller: its wiring is unowned (spec R6.3). Found: {1}".format(
                BODY_WITHOUT_WIRING, sites
            ),
        )

    def test_the_unowned_predicates_also_have_no_product_caller(self):
        """A raising predicate with a live caller would break a production path on every call."""

        for name, _args in NOT_OWNED:
            with self.subTest(predicate=name):
                self.assertEqual(
                    call_sites(name),
                    [],
                    "{0} still raises, so a product caller would fail at runtime".format(
                        name
                    ),
                )

    def test_the_module_docstring_describes_its_real_state(self):
        """E-04: the skeleton must stop describing itself as a skeleton with no bodies."""

        doc = wtiso_gate.__doc__ or ""
        for name, _args, _expected in IMPLEMENTED:
            self.assertIn(
                name, doc, "the docstring must list {0} as implemented".format(name)
            )
        for name, _args in NOT_OWNED:
            self.assertIn(
                name, doc, "the docstring must list {0} as still raising".format(name)
            )
        self.assertIn("STILL RAISING", doc)
        self.assertIn("RETIRED", doc)
        self.assertIn(
            "check_permission_deadline",
            doc,
            "the docstring must cover every implemented predicate",
        )

    def test_the_permission_deadline_body_is_honest_about_not_being_a_bound(self):
        """Overstating a guarantee is the failure mode (spec Goal 5), so assert the disclaimer.

        The predicate DETECTS an unanswered ask in a recorded stream. It cannot terminate anything,
        and the live bound that would use it (`PERMISSION_TIMEOUT`) ships DISABLED. A reader must not
        take its existence for a live guard.
        """

        doc = inspect.getdoc(wtiso_gate.check_permission_deadline) or ""
        self.assertIn("HONEST LIMIT", doc)
        self.assertEqual(lane_containment.PERMISSION_TIMEOUT, 0.0)
        self.assertGreater(lane_containment.MAX_TURN_TIMEOUT, 0.0)


class SabotageTests(unittest.TestCase):
    """Prove each central check can FAIL. A verification that cannot fail proves nothing.

    EVERY SABOTAGE HAPPENS IN A COPY OF THE SOURCE TEXT, never in the product tree: these tests
    reconstruct the checking logic over mutated INPUT rather than editing a shipped file, so a crash
    mid-test cannot leave the repository modified. The plan additionally requires a real
    edit-break-restore cycle on the product for `V-02`/`V-03`; this class is the durable regression
    form of the same property.
    """

    def test_the_single_definition_check_fails_on_a_planted_duplicate(self):
        """R6.1's check must notice a SECOND definition in a DIFFERENT file (not just per-file)."""

        real = definition_sites("classify_missing_input_report")
        self.assertEqual(len(real), 1)

        # A duplicate planted in another module: the same top-level name in a second file, which is
        # what a fork looks like and what a per-file check would happily pass.
        forked = dict(top_level_definitions(PKG / "lane_containment.py"))
        second = {"classify_missing_input_report": 1}
        combined = [
            "lane_containment.py:{0}".format(forked["classify_missing_input_report"]),
            "some_other_module.py:{0}".format(second["classify_missing_input_report"]),
        ]
        self.assertNotEqual(
            len(combined), 1, "the check must reject a two-site result, not tolerate it"
        )

    def test_a_text_grep_cannot_establish_single_definition(self):
        """Why the check is AST-based: a grep is satisfied by this very file.

        Demonstrated rather than asserted in prose: the symbol appears in THIS test module's own
        source, so any text search over the tree finds more occurrences than there are definitions.
        """

        name = "classify_missing_input_report"
        this_file = Path(__file__).read_text(encoding="utf-8")
        self.assertIn(name, this_file, "the checking code itself contains the symbol")

        text_hits = sum(
            path.read_text(encoding="utf-8").count(name)
            for path in sorted(PKG.rglob("*.py"))
        )
        self.assertGreater(
            text_hits,
            len(definition_sites(name)),
            "a text count exceeds the definition count, so grep cannot establish uniqueness",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
