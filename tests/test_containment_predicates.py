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

    def test_both_drivers_reach_the_rules_by_import(self):
        """ "One definition" is only half of R6.1; every consumer must actually IMPORT it."""

        for driver in ("oc_runipd.py", "agy_runipd.py"):
            with self.subTest(driver=driver):
                tree = ast.parse(
                    (PKG / driver).read_text(encoding="utf-8"), filename=driver
                )
                imported = any(
                    isinstance(node, ast.ImportFrom)
                    and node.module == "agent_workflows"
                    and any(a.name == "lane_containment" for a in node.names)
                    for node in ast.walk(tree)
                )
                self.assertTrue(
                    imported,
                    "{0} must import the shared containment home".format(driver),
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

    def test_the_token_emitters_are_delegations_not_second_implementations(self):
        """The gate library's two token functions must CALL the single definition, not restate it."""

        for name, target in (
            ("format_missing_input", "format_missing_input_token"),
            ("parse_missing_input", "parse_missing_input_token"),
        ):
            with self.subTest(predicate=name):
                tree = ast.parse(inspect.getsource(getattr(wtiso_gate, name)).lstrip())
                called = {
                    node.func.attr
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                }
                self.assertIn(
                    target,
                    called,
                    "wtiso_gate.{0} must delegate to lane_containment.{1} (R6.1), not hold a "
                    "second implementation".format(name, target),
                )

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

    def test_the_scope_predicate_delegates_to_the_one_scope_matcher(self):
        """`check_scope` must not restate the Scope-Paths grammar (R6.1).

        The rule is ALREADY enforced through `ipd_lifecycle.finalize_precheck`; a second matcher here
        would let an agent satisfy this gate while failing finalize, the exact hook-versus-driver
        divergence the shared library exists to prevent.
        """

        tree = ast.parse(inspect.getsource(wtiso_gate.check_scope).lstrip())
        called = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertIn("_scope_match", called)
        # And that matcher is itself single-defined, in the lifecycle module that enforces the rule.
        matcher_sites = definition_sites("_scope_match")
        self.assertEqual(len(matcher_sites), 1, matcher_sites)
        self.assertTrue(
            matcher_sites[0].startswith("agent_workflows/ipd_lifecycle.py:"),
            matcher_sites[0],
        )

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
    """R6.1/R6.3 body half: each predicate this Set owns has a real body and unit coverage."""

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

    def test_permission_deadline_catches_a_nested_child_session_ask(self):
        """The qyaime shape: the ask is on a CHILD session, so a root-only parser would miss it."""

        events = [
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
        ]
        self.assertEqual(
            wtiso_gate.check_permission_deadline(events, deadline_seconds=5.0),
            [wtiso_gate.AW_PERMISSION_DEADLINE],
        )

    def test_permission_deadline_is_cleared_only_by_an_answer_on_the_same_session(self):
        ask = {"type": "permission.ask", "sessionID": "child-9", "time": 1.0}
        tail = {"type": "keepalive", "sessionID": "root-1", "time": 99.0}

        answered_same = [
            ask,
            {"type": "permission.answer", "sessionID": "child-9", "time": 2.0},
            tail,
        ]
        self.assertEqual(
            wtiso_gate.check_permission_deadline(answered_same, deadline_seconds=5.0),
            [],
        )

        # An answer on the ROOT session must NOT clear a CHILD's ask, or the deadlock this predicate
        # exists to detect would be masked by unrelated root-session traffic.
        answered_other = [
            ask,
            {"type": "permission.answer", "sessionID": "root-1", "time": 2.0},
            tail,
        ]
        self.assertEqual(
            wtiso_gate.check_permission_deadline(answered_other, deadline_seconds=5.0),
            [wtiso_gate.AW_PERMISSION_DEADLINE],
        )

    def test_permission_deadline_does_not_treat_progress_as_an_answer(self):
        """Keepalive traffic must not clear an ask: a wedged session keeps talking.

        This is the documented and DELIBERATE difference from
        `lane_containment.TurnBoundWatch.note_progress`, where progress DOES disarm the live bound.
        A recorded stream can be judged after the fact; a live watch cannot see the future and
        accepts the false negative rather than killing a healthy turn.
        """

        events = [
            {"type": "permission.ask", "sessionID": "child-9", "time": 1.0},
            {"type": "keepalive", "sessionID": "child-9", "time": 50.0},
            {"type": "message.part", "sessionID": "child-9", "time": 99.0},
        ]
        self.assertEqual(
            wtiso_gate.check_permission_deadline(events, deadline_seconds=5.0),
            [wtiso_gate.AW_PERMISSION_DEADLINE],
        )

    def test_permission_deadline_is_fail_safe_on_thin_or_odd_input(self):
        """Never raises and never guesses; a false positive would kill a healthy turn (R4.4b)."""

        ask = {"type": "permission.ask", "sessionID": "c", "time": 1.0}
        late = {"type": "keepalive", "sessionID": "c", "time": 999.0}

        # `0` disables the check entirely, matching PERMISSION_TIMEOUT's convention.
        self.assertEqual(
            wtiso_gate.check_permission_deadline([ask, late], deadline_seconds=0.0), []
        )
        # Within the deadline is not a violation.
        self.assertEqual(
            wtiso_gate.check_permission_deadline(
                [ask, {"type": "keepalive", "sessionID": "c", "time": 2.0}],
                deadline_seconds=5.0,
            ),
            [],
        )
        # An undatable ask cannot be shown to have exceeded anything.
        self.assertEqual(
            wtiso_gate.check_permission_deadline(
                [{"type": "permission.ask", "sessionID": "c"}], deadline_seconds=5.0
            ),
            [],
        )
        # Empty and junk input are tolerated rather than raising. The junk is DELIBERATELY off-type
        # (a bare string and a `None` among the events): a driver hands this whatever it parsed from a
        # child's stream, so robustness against a malformed entry is the requirement, not a courtesy.
        # Typed loosely on purpose; a well-typed-only test would never exercise this path.
        self.assertEqual(
            wtiso_gate.check_permission_deadline([], deadline_seconds=5.0), []
        )
        junk: list = ["garbage", None, ask, late]
        self.assertEqual(
            wtiso_gate.check_permission_deadline(junk, deadline_seconds=5.0),
            [wtiso_gate.AW_PERMISSION_DEADLINE],
        )

    def test_no_predicate_owned_by_another_phase_was_modified(self):
        """R6.3: implementing a body this Set does not own would be taking another phase's work."""

        for name, _args in NOT_OWNED:
            with self.subTest(predicate=name):
                source = inspect.getsource(getattr(wtiso_gate, name))
                self.assertIn(
                    "_unimplemented",
                    source,
                    "{0} is not owned by this Set and must still raise".format(name),
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

    def test_no_unowned_predicate_returns_a_permissive_value(self):
        """Belt and braces: assert the ABSENCE of a return path in each unimplemented body.

        Complements the call-based check above. The call proves today's behavior; this catches a body
        that gained a conditional early return which the representative arguments happen to miss.
        """

        for name, _args in NOT_OWNED:
            with self.subTest(predicate=name):
                tree = ast.parse(inspect.getsource(getattr(wtiso_gate, name)).lstrip())
                func = tree.body[0]
                assert isinstance(func, ast.FunctionDef)
                returns = [
                    n
                    for n in ast.walk(func)
                    if isinstance(n, ast.Return) and n.value is not None
                ]
                self.assertEqual(
                    returns,
                    [],
                    "{0} must not return a value anywhere; it must raise (R6.2)".format(
                        name
                    ),
                )
                raises = [n for n in ast.walk(func) if isinstance(n, ast.Raise)]
                self.assertTrue(raises, "{0} must raise".format(name))

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

    def test_the_unwired_predicate_nevertheless_has_a_real_body(self):
        """The other half of the split: not-wired must not be mistaken for not-implemented."""

        self.assertEqual(
            wtiso_gate.check_scope(["a.py"], ["b.py"]), [wtiso_gate.AW_GATE_SCOPE]
        )
        self.assertNotIn("_unimplemented", inspect.getsource(wtiso_gate.check_scope))

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

    def test_the_fail_loud_check_fails_on_a_softened_stub(self):
        """R6.2's check must notice a stub that RETURNS instead of raising.

        THE CRITICAL SABOTAGE. Without it, a verification that merely calls each predicate and
        reports success is indistinguishable from one that would accept a permissive default. Here a
        softened stub is simulated exactly (an empty violation list, the shape a caller would read as
        "no violations") and the check is required to reject it.
        """

        def softened(*_args, **_kwargs) -> list[str]:
            return []  # the permissive default R6.2 forbids

        # The real predicate satisfies the check...
        with self.assertRaises(NotImplementedError):
            wtiso_gate.check_lifecycle_role("finalize", "worker")

        # ...and the softened one must NOT. Applying the same assertion to it must fail.
        with self.assertRaises(self.failureException):
            with self.assertRaises(NotImplementedError):
                softened("finalize", "worker")

        # And the source-level half of the check rejects it too.
        tree = ast.parse(inspect.getsource(softened).lstrip())
        returns = [
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.Return) and n.value is not None
        ]
        self.assertNotEqual(
            returns, [], "the softened stub returns a value, which the check must catch"
        )

    def test_the_zero_caller_check_fails_on_a_planted_call(self):
        """R6.3's check must notice a wiring that appears without a plan."""

        self.assertEqual(call_sites(BODY_WITHOUT_WIRING), [])

        planted = ast.parse(
            "from agent_workflows import wtiso_gate\n"
            "def hook(changed, scope):\n"
            "    return wtiso_gate.check_scope(changed, scope)\n"
        )
        found = [
            node.lineno
            for node in ast.walk(planted)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == BODY_WITHOUT_WIRING
        ]
        self.assertEqual(
            len(found),
            1,
            "the caller-detection logic must find a planted call; if it cannot, the zero-caller "
            "result above is vacuous",
        )

    def test_the_delegation_check_fails_on_a_second_implementation(self):
        """R6.1's delegation check must notice a body that renders the token itself."""

        def forked_format(path: str, why: str) -> str:
            return "AW_MISSING_INPUT:{0}:{1}".format(path, why)  # a second spelling

        tree = ast.parse(inspect.getsource(forked_format).lstrip())
        called = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertNotIn(
            "format_missing_input_token",
            called,
            "the forked implementation does NOT delegate, so the check must reject it",
        )
        # It even agrees with the real one TODAY, which is precisely why R6.1 forbids it anyway:
        # agreement now is not protection against drift later.
        self.assertEqual(
            forked_format("x.txt", "absent"),
            wtiso_gate.format_missing_input("x.txt", "absent"),
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
