"""Tests for bklgrad Order 01 (v58bvy): the `graduated` backlog status.

Covers the vocabulary (E-01), the drift-proof second copy in the dependency schema (E-08), the
attention class mapping (E-02), the close-legitimacy handling (E-03), and the README/code agreement
(E-05).

The load-bearing negative row is the gated `done` row in `CloseLegitimacyTests`: if `graduated` ever
satisfied a release gate, a release could ship with every blocker merely graduated and no code written.

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: take one backlog status
(or one consumer of the status vocabulary), ask one function about it, assert one answer. That is a
(status -> answer) table, which is the natural shape for a CLOSED VOCABULARY and its consumers.

THE VOCABULARY IS THE COLUMN EVERYWHERE. `backlog.STATUSES` is the single source of truth and this
whole suite is about copies of it not drifting, so tables iterate the REAL set (or the real consumer
map) rather than a hand-written list of five strings. A hand-written list would pass while a sixth
status went unmapped, which is precisely the drift class these tests exist to catch: four separate
hardcoded copies of the vocabulary existed before this plan, and two were found only when
`aw backlog set graduated` refused the transition and the mover silently declined to relocate the file.

PROSE PINS WERE REMOVED, not merely reduced. Four tests asserted that particular SENTENCES appear in
`.aw/records/backlog/README.md` and in `AGENTS.md`, including one that scanned a 2600-character window
of AGENTS.md for em and en dashes. Those are change-detectors: they break on every legitimate reword,
they cannot detect prose that is present but wrong, and git already records prose changes. Two of them
were additionally COVERED ELSEWHERE by the repository's own machinery, which is the honest reason to
drop rather than rewrite them, and each removal is recorded at its site below with what replaced it.

WHAT IS KEPT FROM THOSE PINS is any token something NON-HUMAN consumes verbatim, and each kept token
records why: the README's `- Status:` line is a machine-parsed closed vocabulary (so it stays, compared
against `backlog.STATUSES`), as is the module docstring's. Those are not prose assertions; they are two
more copies of the vocabulary, which is this file's whole subject.

Tests that are NOT rows carry a one-line docstring saying why. The recurring reasons: the subject is a
REAL repository file rather than a fixture; the claim is about a CLI parser's own structure; or the
assertion is over a help STRING whose audience is a human reading `--help`.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import attention_contract as A
from agent_workflows import backlog
from agent_workflows import check_engine
from agent_workflows import ipd_schema

REPO_ROOT = Path(__file__).resolve().parents[1]

ITEM = """- Id: {id6}
- Status: {status}
{gate}- Set: tst
- Priority: high
- Kind: feature
- Summary: A test item.

## Workflow history
- 2026-08-29 created (test): A test item.

Body.
"""


def _write_item(root: Path, id6: str, status: str, gate: str = "") -> Path:
    d = root / ".aw" / "records" / "backlog" / status
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260829-tst-01-{id6}-a-test-item.backlog.md"
    gate_line = f"- Blocks-Release: {gate}\n" if gate else ""
    p.write_text(ITEM.format(id6=id6, status=status, gate=gate_line), encoding="utf-8")
    return p


class VocabularyTests(unittest.TestCase):
    """E-01: `graduated` is a first-class status between `open` and `done`, and none was dropped.

    ONE table replaces four tests (`graduated_in_statuses`, `ordering_places_graduated_between_open
    _and_done`, `existing_statuses_preserved`, `graduated_item_is_discovered_and_typed`). Each asked
    one question about one status, so the STATUS is the row and the question is a column: is it in the
    frozen set, is it in the ordered directory tuple, where does it sort, and is an item filed under it
    actually discovered on disk.

    EVERY STATUS GETS EVERY CHECK, which is what the split shape could not do. `graduated` had a
    discovery test because it was the new one; the other four did not, so a status present in the
    vocabulary but whose directory the scanner skipped was invisible for four of five values. That is
    not hypothetical: the mover silently declining to relocate a file is one of the two defects this
    plan was written to fix.

    THE ORDER COLUMN IS AN INDEX, NOT A PAIR OF INEQUALITIES. `STATUS_DIRS` is an ORDERED tuple that
    decides display order, so pinning each status's exact position states the whole sequence, where the
    replaced test stated only that `graduated` fell somewhere between `open` and `done` (which
    `open, blocked, graduated, parked, done` also satisfies). The lifecycle reads
    open -> graduated -> done with `blocked` and `parked` after, and that is now readable as a table.

    THE ROWS ARE CHECKED AGAINST THE REAL VOCABULARY FOR COMPLETENESS, so adding a sixth status without
    a row here fails rather than being quietly untested.
    """

    #: (status, its exact index in the ordered `STATUS_DIRS` tuple, why this row exists)
    STATUSES = (
        (
            "open",
            0,
            "the status an item is BORN in, so it sorts first. `aw attention` maps it to `ready`, "
            "meaning action is owed on the item itself",
        ),
        (
            "graduated",
            1,
            "THE STATUS THIS PLAN ADDED, and it sits between `open` and `done` because that is the "
            "lifecycle: the design is handed off to a plan or spec, but the code is not yet written. "
            "Its position is what makes a status listing read in lifecycle order rather than "
            "alphabetically",
        ),
        (
            "blocked",
            2,
            "a LIVE status carrying a typed gate, after the two that describe progress. Listed here "
            "because the drift risk is a status being DROPPED while attention is on the new one: every "
            "pre-existing member is a row for exactly that reason",
        ),
        (
            "parked",
            3,
            "an intentionally dormant item. It must survive as a member, and (see the attention table) "
            "must NOT be what `graduated` maps to, since graduated work is live",
        ),
        (
            "done",
            4,
            "TERMINAL, and last. The distinction between this and `graduated` is the entire point of "
            "the plan: `done` claims the code is written and validated",
        ),
    )

    def test_every_status_is_a_member_a_directory_and_discoverable_in_order(self):
        wrong = []
        for status, index, why in self.STATUSES:
            problems = []
            if status not in backlog.STATUSES:
                problems.append(
                    f"missing from backlog.STATUSES, which is {sorted(backlog.STATUSES)!r}"
                )
            dirs = list(backlog.STATUS_DIRS)
            if status not in dirs:
                problems.append(
                    f"missing from backlog.STATUS_DIRS, which is {dirs!r}; an item filed under it has "
                    "no directory to live in"
                )
            elif dirs.index(status) != index:
                problems.append(
                    f"expected STATUS_DIRS index {index}, got {dirs.index(status)} (full order "
                    f"{dirs!r}); this tuple decides display order, so the lifecycle would read out of "
                    "sequence"
                )
            with TemporaryDirectory() as td:
                root = Path(td)
                path = _write_item(root, "aaa111", status)
                found = list(backlog._iter_items(root))
                if path not in found:
                    problems.append(
                        f"an item written to {status}/ was NOT discovered by `_iter_items` (it found "
                        f"{[p.parent.name for p in found]!r}); a status whose directory the scanner "
                        "skips is invisible to every reader, which is how `aw backlog set` came to "
                        "silently decline to move a file"
                    )
                elif path.parent.name != status:
                    problems.append(
                        f"the item was filed under {path.parent.name!r} rather than {status!r}"
                    )
            if problems:
                wrong.append(
                    f"  {status!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        untabulated = sorted(
            set(backlog.STATUSES) - {status for status, _i, _w in self.STATUSES}
        )
        if untabulated:
            wrong.append(
                f"  STATUSES GREW: {untabulated!r} exist in backlog.STATUSES but have no row here, so "
                "they are untested for membership, ordering and discovery.\n"
                "    this row exists because: a new status added without a row would inherit none of "
                "the guarantees above, which is exactly the silence this suite exists to prevent"
            )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} backlog status(es) are not fully wired up. `backlog.STATUSES` is THE single "
            "source of truth for this vocabulary and every consumer derives from it (see "
            "NoDuplicateVocabularyTests), so A ROW MISSING FROM `STATUSES` means the status does not "
            "exist at all, while a row present in `STATUSES` but MISSING A DIRECTORY or undiscovered "
            "means it exists on paper and is invisible in practice, which is the worse failure: "
            "`aw attention` and `aw backlog` would simply not see those items. FIX: if a status was "
            "deliberately added, add its row (and its attention-class row) rather than widening this "
            "one; if one was deliberately removed, remove its row here and check nothing still files "
            "items under it.\n" + "\n".join(wrong),
        )

    def test_unknown_status_still_rejected(self):
        """Kept separate: the claim is about a NON-MEMBER, so it has no row in a per-status table.

        The table above proves the five real statuses are wired up; this proves the set is CLOSED. A
        vocabulary that accepted anything would satisfy every row above while making `- Status:` a free
        text field, and a typo'd status is an item no reader can classify.
        """
        self.assertNotIn("bogus", backlog.STATUSES)


class DependencySchemaTests(unittest.TestCase):
    """E-08: `state:backlog:<status>:<id6>` parses for EVERY status, and only for those.

    ONE table replaces three tests (`state_backlog_graduated_edge_parses`, `bogus_backlog_status_edge
    _still_rejected`, `every_backlog_status_is_a_legal_state_edge`). All three fed one token to
    `parse_item_dependencies` and asked whether it was accepted, so the TOKEN is the row and
    accept/reject is a column. The rejection case belongs in the same table as the acceptances for the
    usual reason: a parser that accepted every status string and one that accepted none are opposite
    failures, and a table holding both cannot pass under either.

    THE ACCEPTING ROWS ARE GENERATED FROM `backlog.STATUSES` rather than listed, because the property
    E-08 states is that the parser is governed by the DERIVED set. A hand-written list of five statuses
    would pass while a sixth was unparseable, which is the exact defect E-08 fixed: before it,
    `state:backlog:graduated:...` was rejected, making the new status undeclarable as a dependency.

    THE ACCEPTED ROWS PIN THE PARSED EDGE'S FIELDS, not just the absence of an error. An edge that
    parses into the wrong `target_type` or the wrong `status` resolves against the wrong tree, which is
    a silent wrong answer rather than a refusal.
    """

    def test_every_backlog_status_makes_a_legal_state_edge_and_nothing_else_does(self):
        #: (token, the expected (target_type, status) or None meaning the token must be REJECTED, why)
        cases = [
            (
                f"state:backlog:{status}:abc123",
                ("backlog", status),
                "generated from `backlog.STATUSES` rather than hand-listed, which is the whole point "
                "of E-08: the parser must be governed by the DERIVED vocabulary, so a status added "
                "tomorrow is declarable without touching the schema",
            )
            for status in sorted(backlog.STATUSES)
        ]
        cases.append(
            (
                "state:backlog:bogus:abc123",
                None,
                "THE CLOSED-SET ROW: an out-of-vocabulary status must be REFUSED with an error and "
                "must yield no edge. Without it, every accepting row above is satisfied by a parser "
                "that accepts any string, and a typo'd status would become a dependency edge that "
                "resolves against nothing",
            )
        )
        wrong = []
        for token, expected, why in cases:
            edges, _ok, err = ipd_schema.parse_item_dependencies(token)
            problems = []
            if expected is None:
                if err is None:
                    problems.append(
                        "expected a parse ERROR, got none; the status vocabulary is not closed"
                    )
                if edges:
                    problems.append(
                        f"expected NO edges, got {[(e.target_type, e.status) for e in edges]!r}; a "
                        "refused token must not also produce an edge"
                    )
            else:
                if err is not None:
                    problems.append(f"expected no error, got {err!r}")
                if len(edges) != 1:
                    problems.append(f"expected exactly 1 edge, got {len(edges)}")
                else:
                    got = (edges[0].target_type, edges[0].status)
                    if got != expected:
                        problems.append(
                            f"expected (target_type, status) {expected!r}, got {got!r}; an edge that "
                            "parses into the wrong type resolves against the wrong records tree, "
                            "which is a silent wrong answer rather than a refusal"
                        )
            if problems:
                wrong.append(
                    f"  {token!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the dependency parser mishandled {len(wrong)} of {len(cases)} `state:backlog:` tokens. "
            "THE ACCEPTING ROWS ARE GENERATED FROM `backlog.STATUSES`, so if SEVERAL failed together "
            "the schema has stopped deriving from that set and is re-listing the vocabulary, which is "
            "the drift E-08 exists to prevent (before it, `state:backlog:graduated:...` was rejected "
            "and the new status was undeclarable). If ONLY the `bogus` row failed, the set stopped "
            "being CLOSED and any typo is now a legal edge. FIX: do NOT fix a failing accept row by "
            "adding a literal to the schema; make it read `backlog.STATUSES`.\n"
            + "\n".join(wrong),
        )


class NoDuplicateVocabularyTests(unittest.TestCase):
    """E-01/E-08 drift guard: every consumer DERIVES the vocabulary; none re-lists it.

    ONE table replaces four tests. Each imported one consumer, read its backlog-status vocabulary, and
    compared it to `backlog.STATUSES`, differing only in WHICH consumer and in how that consumer spells
    its copy (a set, a frozenset, a sorted list of candidates, a dict's keys). THE CONSUMER IS
    THEREFORE THE ROW, with a small accessor per row to normalize the spelling.

    Why the table beats the four, and this is the strongest case in the file: the failure mode is
    SYSTEMIC. Four separate hardcoded copies of this vocabulary existed, and two were discovered only
    when `aw backlog set graduated` refused the transition and the mover silently declined to relocate
    the file. When a new status is added, EVERY re-listing copy breaks at once; four tests report that
    as four unrelated red lines, while one table reports it as a single failure naming every consumer
    that needs updating, which is the actual work list.

    THE COMPARISON IS AGAINST THE LIVE SET, never against a literal five, so adding a status is enough
    to make this fail for any consumer that did not derive it.
    """

    #: (consumer, a callable returning that consumer's backlog-status vocabulary as a set, why this
    #: consumer matters)
    CONSUMERS = (
        (
            "status_set.TYPE_STATUSES['backlog'] (the `aw backlog set` transition validator)",
            lambda: set(
                __import__(
                    "agent_workflows.status_set", fromlist=["TYPE_STATUSES"]
                ).TYPE_STATUSES["backlog"]
            ),
            "ONE OF THE TWO COPIES FOUND THE HARD WAY: it is what REFUSED "
            "`aw backlog set graduated`, so a stale copy here makes a real, shipped status "
            "unreachable through the only supported way to set it",
        ),
        (
            "ipd_schema._ITEM_DEP_STATE_STATUSES['backlog'] (the dependency-edge parser)",
            lambda: set(ipd_schema._ITEM_DEP_STATE_STATUSES["backlog"]),
            "a stale copy here makes a status UNDECLARABLE as a dependency "
            "(`state:backlog:<status>:<id6>` is refused), so a plan cannot express that it waits on "
            "an item in that state. See DependencySchemaTests for the parser-level view",
        ),
        (
            "completion.status_candidates('backlog') (shell tab completion)",
            lambda: set(
                __import__(
                    "agent_workflows.completion", fromlist=["status_candidates"]
                ).status_candidates("backlog")
            ),
            "the LOWEST-STAKES copy and the easiest to forget, which is why it is a row: a status "
            "missing from completion is a status a maintainer never discovers exists, and this suite "
            "is about the gap between what the code accepts and what a user can reach",
        ),
        (
            "attention_contract.CLASS_MAPS['backlog'] (the cross-tree attention view)",
            lambda: set(A.CLASS_MAPS["backlog"]),
            "an UNMAPPED status raises rather than defaulting, so a missing entry here makes "
            "`aw attention` fail on any item carrying it. See AttentionClassTests for what each status "
            "must map TO",
        ),
    )

    def test_every_consumer_derives_the_status_vocabulary(self):
        truth = set(backlog.STATUSES)
        wrong = []
        for consumer, read, why in self.CONSUMERS:
            got = read()
            if got != truth:
                wrong.append(
                    f"  {consumer}:\n"
                    f"    - missing {sorted(truth - got)!r}\n"
                    f"    - extra {sorted(got - truth)!r}\n"
                    f"    this consumer matters because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.CONSUMERS)} consumers no longer agree with "
            f"`backlog.STATUSES` ({sorted(truth)!r}). SEVERAL FAILING TOGETHER, ALL MISSING THE SAME "
            "STATUS, is the signature of a status added to `backlog.py` alone: the fix is to make each "
            "listed consumer DERIVE from `backlog.STATUSES` rather than to add the literal in four "
            "places, which is how four hardcoded copies accumulated in the first place. FIX: the "
            "consequences differ per consumer and are named above; the two expensive ones are the "
            "setter (a shipped status becomes unreachable through the CLI) and the attention map "
            "(`aw attention` raises on any item carrying the unmapped status).\n"
            + "\n".join(wrong),
        )


class AttentionClassTests(unittest.TestCase):
    """E-02: every backlog status maps to the right cross-tree attention class.

    ONE table replaces four tests (`graduated_maps_to_active`, `graduated_is_not_done_or_ready_or
    _parked`, `class_map_is_total_over_the_enum`, `existing_mappings_unchanged`). Each asked
    `A.class_of` about one or more statuses and asserted the answer, so the STATUS is the row and the
    expected class is the column.

    THE `is NOT done/ready/parked` TEST IS ABSORBED RATHER THAN DROPPED, and it is worth saying how: it
    made a DIFFERENT KIND of claim about the same input (three inequalities instead of one equality),
    which looks like a reason to keep two tests. It is not, because asserting the EXACT class already
    implies every inequality it listed. What the old test really carried was the REASONS those three
    wrong answers would be bad, and those are preserved as prose on the `graduated` row, where they
    belong: each one names a concrete consequence rather than a preference.

    TOTALITY IS CHECKED IN BOTH DIRECTIONS in one place. The map must have no status missing (an
    unmapped status makes `class_of` raise, so `aw attention` fails on any item carrying it) and no
    entry the vocabulary does not have (a stale entry is a status that was removed while its mapping
    lived on). The replaced test checked only the first direction.
    """

    #: (status, the expected attention class, why this mapping is the right one)
    MAPPINGS = (
        (
            "open",
            A.READY,
            "`ready` means ACTION IS OWED ON THE ITEM ITSELF: nobody has picked it up, so it belongs "
            "in the list a maintainer works from",
        ),
        (
            "graduated",
            A.ACTIVE,
            "THE MAPPING THIS PLAN EXISTS FOR, and three wrong answers are each specifically bad. "
            "`done` would DROP IT FROM THE RELEASE-BLOCKER SET, which is the failure that matters: a "
            "release could ship with every blocker merely graduated and no code written. `ready` would "
            "claim action is owed on the ITEM, but the design is already handed off and the work now "
            "lives on the plan or spec. `parked` would call it dormant when it is deliberately live. "
            "`active` is the only class that keeps it visible as outstanding without re-asking for the "
            "design work",
        ),
        (
            "blocked",
            A.BLOCKED,
            "an item that cannot proceed until its typed gate clears. Distinct from `active` precisely "
            "so a reader can tell work in progress from work that is waiting on something else",
        ),
        (
            "parked",
            A.PARKED,
            "intentionally dormant, and HIDDEN from the default attention view. That is why "
            "`graduated` must not map here: parking a live handoff would make it invisible",
        ),
        (
            "done",
            A.DONE,
            "TERMINAL, and the class that legitimately drops an item from the blocker set, which is "
            "exactly why reaching it is gated on preserving or releasing the release gate (see "
            "CloseLegitimacyTests)",
        ),
    )

    def test_every_status_maps_to_its_class_and_the_map_is_total(self):
        wrong = []
        for status, expected, why in self.MAPPINGS:
            try:
                got = A.class_of("backlog", status)
            except A.UnknownNativeStatus as exc:
                # An unmapped status RAISES rather than defaulting to a class, deliberately: the
                # docstring on `class_of` says the caller renders a violation instead of guessing.
                wrong.append(
                    f"  {status!r}:\n"
                    f"    - `class_of` RAISED {type(exc).__name__}: {exc}. An unmapped status makes "
                    "`aw attention` fail on any item carrying it, so this is an outage of the view "
                    "rather than a wrong label\n"
                    f"    this mapping matters because: {why}"
                )
                continue
            if got != expected:
                wrong.append(
                    f"  {status!r}:\n"
                    f"    - expected class {expected!r}, got {got!r}\n"
                    f"    this mapping matters because: {why}"
                )
        tabulated = {status for status, _c, _w in self.MAPPINGS}
        unmapped = sorted(set(backlog.STATUSES) - set(A.CLASS_MAPS["backlog"]))
        stale = sorted(set(A.CLASS_MAPS["backlog"]) - set(backlog.STATUSES))
        untabulated = sorted(set(backlog.STATUSES) - tabulated)
        for label, names, consequence in (
            (
                "UNMAPPED in CLASS_MAPS",
                unmapped,
                "`class_of` raises on these, so `aw attention` fails outright for any item carrying "
                "one; the view is unavailable rather than merely incomplete",
            ),
            (
                "STALE entries in CLASS_MAPS",
                stale,
                "these are mapped but are not statuses, so a removed status's mapping outlived it and "
                "the map no longer describes the vocabulary",
            ),
            (
                "present in STATUSES but with no row here",
                untabulated,
                "these have no asserted class, so a wrong mapping for them would pass silently",
            ),
        ):
            if names:
                wrong.append(
                    f"  {label}: {names!r}\n"
                    f"    - consequence: {consequence}\n"
                    "    this check exists because: the map and the vocabulary must agree EXACTLY, in "
                    "both directions"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} problem(s) in the backlog attention-class mapping. THE CLASS DECIDES "
            "VISIBILITY, so read the direction a wrong answer moves an item: toward `done` or `parked` "
            "it DISAPPEARS from the release-blocker view (the dangerous direction, because a release "
            "can then ship with an outstanding blocker nobody sees), and toward `ready` it reappears as "
            "work already handed off, which wastes a maintainer's attention. FIX: an UNMAPPED status is "
            "worse than a mis-mapped one because `class_of` raises, taking the whole `aw attention` "
            "view down rather than labelling one item wrongly.\n" + "\n".join(wrong),
        )


class CloseLegitimacyTests(unittest.TestCase):
    """E-03: which transitions a RELEASE-GATED item may take, and which fail closed.

    ONE table replaces three tests (`graduated_is_legitimate_for_a_gated_item`, `graduated_is_not_a
    _substitute_for_done`, `ungated_item_unaffected`). Each wrote one item into a temp repo, called
    `evaluate_blocking_close`, and asserted the verdict, differing only in whether the item carried
    `- Blocks-Release:` and in the target status. BOTH ARE THEREFORE COLUMNS, and making the gate a
    column is what states the actual property: the SAME transition is legitimate on an ungated item and
    refused on a gated one, which is a comparison no single-fixture test can make.

    ROWS ASSERT THE SEVERITY AND THE REASON, not just a boolean, because this predicate is consumed
    three ways (the `aw backlog set` setter, the `aw check` rules, and an opt-in pre-commit hook) and
    they route on the severity. A verdict that is `legitimate=True` with the wrong severity silently
    changes whether a maintainer sees a warning at all.

    THE `done` ROW IS THE LOAD-BEARING ONE IN THE WHOLE FILE. If `graduated` ever satisfied a release
    gate, a release could ship with every blocker merely graduated and no code written; the mirror
    failure is `done` being accepted on a gated item, which drops the gate outright. Both directions are
    rows.
    """

    #: (case, the `- Blocks-Release:` value ("" for none), the target status, expected legitimate,
    #: expected severity, a substring the reason must contain or None, why this row exists)
    TRANSITIONS = (
        (
            "a gated item -> graduated",
            "next",
            "graduated",
            True,
            "ok",
            "preserves gate",
            "THE POINT OF `graduated`: it is an HONEST transition for a gated item, because the item "
            "stays a release blocker. The reason must SAY it preserves the gate, since that is what "
            "tells a maintainer this is not a way of quietly closing the item",
        ),
        (
            "a gated item -> done",
            "next",
            "done",
            False,
            "error",
            None,
            "LOAD-BEARING: `done` on a release-gated item FAILS CLOSED with no handoff, evidence, or "
            "explicit de-gate. Closing it would silently drop the gate, so the release could ship with "
            "the blocker gone from the view and the work never done. `error` rather than `warn` "
            "because the setter refuses on it",
        ),
        (
            "an UNGATED item -> done",
            "",
            "done",
            True,
            "ok",
            None,
            "THE CONTROL FOR THE ROW ABOVE, and the reason the gate is a column: `done` is perfectly "
            "legitimate when there is no gate to drop. Without this row the rule could be 'never "
            "allow done', which would make the ordinary close path unreachable",
        ),
        (
            "an UNGATED item -> graduated",
            "",
            "graduated",
            True,
            "ok",
            None,
            "an ungated item is unaffected by this predicate entirely, which is what keeps the gate "
            "check from becoming a general transition policy it was never designed to be",
        ),
        (
            "a gated item -> parked",
            "next",
            "parked",
            True,
            "warn",
            None,
            "THE THIRD SEVERITY, and the row that proves the verdict is not a boolean: parking a "
            "release blocker is ALLOWED but WARNS, because it hides the gate from the active "
            "release-blocker view without releasing it. A predicate collapsing this to `ok` loses the "
            "warning a maintainer needs; collapsing it to `error` forbids a legitimate act",
        ),
    )

    def test_every_transition_on_a_gated_and_an_ungated_item(self):
        wrong = []
        for (
            case,
            gate,
            target,
            legitimate,
            severity,
            needle,
            why,
        ) in self.TRANSITIONS:
            with TemporaryDirectory() as td:
                root = Path(td)
                path = _write_item(root, "bbb222", "open", gate=gate)
                verdict = check_engine.evaluate_blocking_close(root, path, target)
            problems = []
            if verdict.legitimate is not legitimate:
                problems.append(
                    f"expected legitimate={legitimate}, got {verdict.legitimate!r} "
                    f"(reason {verdict.reason!r})"
                )
            if verdict.severity != severity:
                problems.append(
                    f"expected severity {severity!r}, got {verdict.severity!r}; the setter, the "
                    "`aw check` rules and the pre-commit hook all route on this value, so a wrong "
                    "severity changes whether a maintainer is stopped, warned, or told nothing"
                )
            if needle and needle not in verdict.reason:
                problems.append(
                    f"the reason does not contain {needle!r}: {verdict.reason!r}"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"check_engine.evaluate_blocking_close was wrong on {len(wrong)} of "
            f"{len(self.TRANSITIONS)} transitions. THE GATE IS A COLUMN, so compare the gated and "
            "ungated rows for the SAME target before editing anything: if both `-> done` rows moved "
            "together the predicate stopped reading `- Blocks-Release:` at all, whereas if only the "
            "GATED one moved the gate policy itself changed. FIX: the gated `-> done` row going "
            "legitimate is the dangerous failure and is silent by construction, because a release then "
            "ships with its blocker closed and no handoff, evidence, or de-gate recorded anywhere. A "
            "severity-only failure is not cosmetic either: `warn` becoming `ok` removes the only "
            "notice a maintainer gets that parking a blocker hid it from the release view.\n"
            + "\n".join(wrong),
        )


class DocumentationAgreementTests(unittest.TestCase):
    """E-05: the two OTHER copies of the status vocabulary, in documentation, must equal the code's.

    WHAT WAS REMOVED HERE, and why. Three tests pinned PROSE:

    * `test_readme_documents_graduated_directory` asserted the README contains `graduated/` and matches
      `graduated/.*active`. Both facts are already asserted structurally and more strongly elsewhere in
      this file: `VocabularyTests` proves `graduated` is a real directory that items are discovered in,
      and `AttentionClassTests` proves it maps to `active`. Pinning a sentence that RESTATES those adds
      no falsifiability, and it breaks whenever the README is reworded.
    * `test_agents_md_documents_the_contract` asserted four phrases appear in `AGENTS.md`
      (`graduated`->`active`, `REVIEW-READY plans`, `From-Backlog`, "`graduated`, NOT `done`"). That
      text is GENERATED, not hand-written: it comes from `engine.agents_managed_block`, and
      `test_shared_checkout_contract.py` already asserts the generated block carries the
      graduation contract (`InstalledContractContentTests`, `test_the_graduation_contract_ships_to
      _adopters`) while `test_reporting_contract.py` asserts this repo's AGENTS.md matches that block
      byte for byte. Asserting the phrases here tested the same generator through a copy, and did it by
      needle, so it would break on any rewording that kept the meaning.
    * `test_agents_md_contract_has_no_em_or_en_dash` scanned a 2600-character WINDOW of AGENTS.md for
      U+2014 and U+2013. It is covered twice over: `test_agent_contract_test_invocation.py` runs the
      same check on the execution-contract section, and `test_shared_checkout_contract.py`'s
      `test_every_block_is_pure_ascii` is strictly stronger, since it refuses ANY non-ASCII character
      anywhere in the generated block rather than two codepoints in a fixed-length window. A
      byte-offset window is also the fragile kind of pin: inserting a paragraph moves the section and
      the assertion silently starts checking different text.

    WHAT IS KEPT, and why each is NOT a prose pin. The two remaining tests parse a `- Status:` line out
    of a document and compare the parsed set to `backlog.STATUSES`. Those lines are a CLOSED VOCABULARY
    that is consumed verbatim: the README's line is the documented contract a human copies when hand
    writing an item's front matter, and both are the fourth and fifth copies of the very set this file
    exists to keep from drifting. Neither asserts any sentence around the line, and neither hardcodes
    the five values, so a reword is free and a vocabulary change fails.

    They are left as TWO tests rather than one table: the two documents need different regexes (the
    module docstring's line is indented) and one reads a FILE from the repository while the other reads
    a live module's `__doc__`, so the setup differs in kind rather than in data.
    """

    def test_readme_status_list_matches_statuses(self):
        """Kept: the README's `- Status:` line is a CLOSED VOCABULARY a human copies verbatim.

        Not a prose pin. It parses the line and compares the SET to `backlog.STATUSES`, asserting
        nothing about the wording around it, so the README can be rewritten freely while a vocabulary
        change fails here.
        """
        readme = REPO_ROOT / ".aw" / "records" / "backlog" / "README.md"
        text = readme.read_text(encoding="utf-8")
        m = re.search(r"^- Status: (.+)$", text, re.M)
        self.assertIsNotNone(m, "README must document a `- Status:` line")
        assert m is not None
        documented = {s.strip() for s in m.group(1).split("|")}
        self.assertEqual(
            documented,
            set(backlog.STATUSES),
            "README status list must equal backlog.STATUSES",
        )

    def test_module_docstring_status_list_matches_statuses(self):
        """The `backlog.py` docstring's own `- Status:` line must equal the code's vocabulary.

        Kept separate from the README test above: the subject is a live module's `__doc__` rather than a
        file on disk, and the line is INDENTED there, so the two need different regexes.

        It read the pre-`graduated` four for as long as `graduated` had shipped, which is the same
        drift class the README test above already guards, one file over. Asserted against
        `backlog.STATUSES` rather than a literal so a future member cannot desynchronize it.
        """
        m = re.search(r"^    - Status: (.+)$", backlog.__doc__ or "", re.M)
        self.assertIsNotNone(m, "the module docstring must document a `- Status:` line")
        assert m is not None
        documented = {s.strip() for s in m.group(1).split("|")}
        self.assertEqual(
            documented,
            set(backlog.STATUSES),
            "backlog.py's docstring status list must equal backlog.STATUSES",
        )


class CliStatusSurfaceTests(unittest.TestCase):
    """bkgradcli: the CLI must OFFER every status the code accepts.

    WHY THIS EXISTS, measured 2026-09-19. `graduated` shipped as a real status (a directory in
    `STATUS_DIRS`, a valid `- Status:`, an `aw attention` class of `active`) and both setters always
    ACCEPTED it, because they validate against `backlog.STATUSES`. But the two argparse help strings
    were hand-typed with the pre-`graduated` four, so `aw backlog set --help` documented only
    `open | blocked | parked | done`. The consequence was not cosmetic: an `aw attention` advisory
    told a maintainer to close a release-blocking item `done`, and `--help` offered no `graduated`,
    so the only reachable closure asserted that unwritten code was written and validated. That is
    precisely the false completion claim `graduated` was introduced to prevent.

    Pinned as PROPERTIES against `backlog.STATUSES`, following
    `test_work_kind.py::test_the_cli_choices_match_the_shared_vocab`, so a future status is offered
    automatically and a hand-typed regression fails here.

    ONE table replaces three of the four tests (`backlog_set_offers_every_status`,
    `backlog_new_offers_every_status`, `both_status_help_strings_name_graduated`). All three walked the
    argparse tree to one `--status` action and asserted something about it, differing only in WHICH
    subcommand, so THE SUBCOMMAND IS THE ROW. The two claims each row makes (the `choices` set equals
    the vocabulary, and the help string names every status) are columns, and they belong together
    because the measured defect was exactly a DISAGREEMENT between them: the choices were derived and
    correct while the help string was hand-typed and stale.

    THE HELP COLUMN NOW CHECKS EVERY STATUS, NOT JUST `graduated`. The replaced test looked only for the
    word `graduated`, which was the status that happened to be missing; a table can afford to check the
    whole vocabulary, so the next hand-typed help string omitting a DIFFERENT status fails too. That is
    the generalization the incident actually argues for: the bug was not about `graduated`, it was about
    a help string that does not derive from the enum.
    """

    def _action(self, path: tuple[str, ...], dest: str):
        from agent_workflows import cli

        import argparse

        node = cli._build_parser()
        for name in path:
            sub = next(
                a for a in node._actions if isinstance(a, argparse._SubParsersAction)
            )
            node = sub.choices[name]
        return next(a for a in node._actions if getattr(a, "dest", "") == dest)

    #: (the subcommand path, why this surface matters)
    SURFACES = (
        (
            ("backlog", "set"),
            "THE SURFACE THE INCIDENT HAPPENED ON: an `aw attention` advisory told a maintainer to "
            "close a release-blocking item, and because `--help` offered only the pre-`graduated` "
            "four, the only reachable closure asserted that unwritten code was written and validated",
        ),
        (
            ("backlog", "new"),
            "the CREATE path, which had the same hand-typed list. An item cannot be BORN `graduated` "
            "often, but a status missing here is still a status a maintainer never learns exists, and "
            "the two help strings drifted together precisely because neither derived from the enum",
        ),
    )

    def test_every_backlog_status_is_offered_and_named_in_help(self):
        vocabulary = set(backlog.STATUSES)
        wrong = []
        for path, why in self.SURFACES:
            action = self._action(path, "status")
            problems = []
            choices = set(action.choices or ())
            if choices != vocabulary:
                problems.append(
                    f"`choices` is {sorted(choices)!r}, expected {sorted(vocabulary)!r} "
                    f"(missing {sorted(vocabulary - choices)!r}, extra {sorted(choices - vocabulary)!r})"
                )
            help_text = action.help or ""
            unnamed = sorted(s for s in vocabulary if s not in help_text)
            if unnamed:
                problems.append(
                    f"the help string does not name {unnamed!r}: {help_text!r}. `--help` is where a "
                    "maintainer READS the options, so a status the parser accepts but the help omits "
                    "is a status nobody chooses"
                )
            if problems:
                wrong.append(
                    f"  aw {' '.join(path)} --status:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this surface matters because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.SURFACES)} backlog CLI status surfaces disagree with "
            f"`backlog.STATUSES` ({sorted(vocabulary)!r}). READ WHICH COLUMN FAILED, because the two "
            "mean different things: a `choices` mismatch REFUSES a legal status outright, while a HELP "
            "mismatch accepts it silently and simply never tells the maintainer it exists, which is the "
            "measured 2026-09-19 defect (choices were derived and correct, the help was hand-typed and "
            "stale, and a maintainer closed a release-blocking item `done` because `graduated` was not "
            "offered). FIX: derive BOTH from `backlog.STATUSES`, following "
            "`test_work_kind.py::test_the_cli_choices_match_the_shared_vocab`; do not re-type the list "
            "with the missing value added, which is how it went stale in the first place.\n"
            + "\n".join(wrong),
        )

    def test_set_help_distinguishes_graduated_from_done(self):
        """Kept separate: the claim is about EXPLANATORY prose, not about vocabulary coverage.

        The table above proves every status is OFFERED and NAMED. This proves the `set` help
        additionally says which of the two confusable ones to pick, and it is the one surface where that
        matters: offering the word is not enough, because the cost of choosing `done` wrongly is a false
        claim that code was written. Asserted on `set` only, since `new` does not carry the explanation.
        """
        help_text = (self._action(("backlog", "set"), "status").help or "").lower()
        self.assertIn("handed off", help_text)
        self.assertIn("not yet written", help_text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
