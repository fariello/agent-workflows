"""Tests for bklggrad Order 02 (orb9zb): the shared close-legitimacy predicate + setter gate +
`aw check` consistency rules + WARN transitions + the generalized evidence resolver.

Covers:
- V-02 evaluate_blocking_close: fail-closed on a bare blocking `-> done`; legitimate for HANDOFF,
  SATISFIED, DE-GATED; warn (not error) for blocking `-> parked` and priority-demote-of-blocker.
- V-03 the shared evidence resolver accepts a real in-tree artifact, rejects nonexistent/unsafe;
  specs `implementing -> implemented` behavior unchanged.
- V-04 `aw backlog set done` on a blocking item fails with the three-fix teaching error and
  succeeds via each of the three paths (HANDOFF plan, --evidence, same-call --blocks-release -).
- V-05 `aw check` fires blocking-item-closed-without-gate and from-backlog-gate-mismatch on
  fixtures and is clean otherwise.
- V-06 blocking `-> parked` and priority-demote-of-a-blocker succeed (exit 0) with a warning.

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: write a small records
tree into a temp repo, attempt one transition, assert one outcome. The tables group BY LAYER (the pure
predicate, the evidence resolver, the CLI setter, the cross-tree `aw check` rules) because each layer
is separately reachable and a gate present in one but missing from another is the realistic hole.

THIS IS A FAIL-CLOSED SAFETY GATE, SO NO ROW SETTLES FOR "IT REFUSED" OR "IT ALLOWED". Every row
pins the SPECIFIC outcome: a legitimate close names WHICH legitimacy path matched (`HANDOFF`,
`SATISFIED`, `DE-GATED`), and a refusal pins the severity plus the count of offered fixes, because
`evaluate_blocking_close` has one refusal branch reached from several conditions and a row asserting
only `not legitimate` cannot tell "refused for the right reason" from "refuses everything". The three
fix routes each keep their own row for the same reason: they are three INDEPENDENT ways a maintainer
can legitimately close a release blocker, and collapsing them would let two of the three rot while the
table stayed green.

THE ALLOWING ROWS AND THE REFUSING ROWS SHARE EVERY TABLE, which matters more here than anywhere else
in the suite. A gate that refused every close would satisfy every refusal row while making a release
blocker impossible to close at all, and a gate that allowed everything would satisfy every legitimacy
row while silently dropping release gates - which is the exact defect this machinery exists to
prevent. Each failure message says which direction collapsed.

MODES ARE COLUMNS: the TARGET STATUS (`done`/`parked`/`graduated`), the resolver (the generalized
backlog one versus the stricter specs one), and the GIT STATE of the fixture (staged / committed /
no repo) all vary within one table rather than across classes, because in each case the property
worth stating is that the SAME tree gets a different answer in a different mode.

Tests that are NOT rows carry a one-line docstring saying why they stay separate.
"""

from __future__ import annotations

import argparse
import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch
from pathlib import Path

from agent_workflows import backlog as B
from agent_workflows import check_engine as CE


def _args(**kw):
    ns = argparse.Namespace()
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


def _write_item(
    repo: Path,
    id6: str,
    *,
    status="open",
    priority="high",
    blocks_release: "str | None" = "next",
    setid="demo",
) -> Path:
    d = repo / ".aw" / "records" / "backlog" / status
    d.mkdir(parents=True, exist_ok=True)
    lines = [
        f"- Id: {id6}",
        f"- Status: {status}",
        f"- Set: {setid}",
        f"- Priority: {priority}",
        "- Kind: chore",
        "- Summary: x",
    ]
    if blocks_release:
        lines.append(f"- Blocks-Release: {blocks_release}")
    lines += ["", "## Workflow history", "- 2026-01-01 created (t): x", ""]
    p = d / f"20260101-{setid}-01-{id6}-x.backlog.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _write_plan(
    repo: Path,
    id6: str,
    *,
    from_backlog=None,
    blocks_release=None,
    status="approved",
    setid="demo",
    order="01",
) -> Path:
    d = repo / ".aw" / "records" / "plans" / "pending"
    d.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# IPD: {id6}",
        "",
        "- Date: 2026-08-25",
        "- Kind: child",
        f"- Status: {status}",
        f"- Set: {setid}",
        f"- Order: {int(order)}",
        f"- Id: {id6}",
    ]
    if from_backlog:
        lines.append(f"- From-Backlog: {from_backlog}")
    if blocks_release:
        lines.append(f"- Blocks-Release: {blocks_release}")
    lines += [
        "",
        "## Workflow history",
        "- 2026-08-25 draft (t): x.",
        "",
        "## Goal",
        "x",
    ]
    p = d / f"20260825-{setid}-{order}-{id6}-x.ipd.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _artifact(repo: Path, rel: str) -> str:
    """Materialize an in-tree artifact and return its repo-relative citation."""
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x\n", encoding="utf-8")
    return rel


#: The `path` column's sentinel for "this transition is refused, so no legitimacy path matched".
REFUSED = "REFUSED"

#: The evidence artifact every SATISFIED row cites.
EVIDENCE_REL = ".aw/records/walkthroughs/w.md"

#: How a `PredicateTests.VERDICTS` row supplies the POST-mutation item text. Three-valued on purpose:
#: `AS_IS` (pass the file's own text) and `FROM_FILE` (pass nothing, letting the predicate read it)
#: look equivalent but are not, because a caller that passes text is asserting it evaluated a mutation,
#: and `DEGATED` is the same-call `--blocks-release -`. Collapsing `AS_IS` into `DEGATED` silently
#: removes the gate a row depends on.
FROM_FILE = "predicate reads the file"
DEGATED = "gate stripped in memory"
AS_IS = "file text passed through unchanged"


class PredicateTests(unittest.TestCase):
    """V-02: every verdict `evaluate_blocking_close` can reach, in one table.

    ONE table replaces nine tests. Every one of them wrote one backlog item (sometimes one plan),
    called the predicate once, and asserted two or three fields of the returned `CloseVerdict`; they
    differed only in the FIXTURE and the TARGET STATUS, both of which are columns.

    WHY THE TABLE BEATS THE NINE, and it is not primarily about line count. This predicate is a single
    decision tree whose branches are alternatives to each other: DE-GATED is checked before HANDOFF,
    HANDOFF before SATISFIED, and the refusal is what remains. Split into nine tests, a refactor that
    made an EARLIER branch match too eagerly would turn several later rows green-for-the-wrong-reason
    while every test still passed, because each test asserted `legitimate` and at most one other field.
    Here every row pins the `path` the verdict took, so a verdict that is legitimate via the WRONG
    route fails loudly, and the grouping of failures says which branch swallowed the others.

    EVERY FIX ROUTE KEEPS ITS OWN ROW, DELIBERATELY. HANDOFF, SATISFIED and DE-GATED are three
    INDEPENDENT ways a maintainer may legitimately close a release blocker; a single "it was allowed"
    row would let two of the three rot unnoticed. The mismatched-handoff row is the other half of the
    HANDOFF claim: a carrier naming this item but gating a DIFFERENT release is not a handoff, and
    without that row HANDOFF could degrade into "some plan mentions this item".

    THE REFUSAL ROW PINS THE FIX COUNT (three) rather than only the severity, because the refusal is
    the only place a human is TAUGHT the three routes. A refusal offering fewer strands the maintainer
    with a closed door and no key, which in practice gets resolved by hand-editing the file - the
    precise bypass the `aw check` backstop in this file exists to catch.

    THE `item_text` COLUMN IS THREE-VALUED (`FROM_FILE` / `DEGATED` / `AS_IS`) AND MUST STAY SO. The
    predicate evaluates POST-mutation state, which the caller supplies as `item_text`, and the three
    values are genuinely different inputs rather than a bool: `DEGATED` strips the gate (the same-call
    `--blocks-release -`), while `AS_IS` passes the file's text unchanged - which is what a priority
    demote does, since it mutates the priority and NOT the gate. Measured while writing this table: a
    two-valued column collapsed `AS_IS` into `DEGATED`, which removed the gate the demote branch
    requires, so the row got `ok` instead of `warn`. The expectation was wrong, not the code.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    #: (case, the item's `Blocks-Release` (None for an ungated item), the carrier plan's
    #: `Blocks-Release` (None to write no carrier), the evidence citation to pass (None for none),
    #: how the POST-mutation item text reaches the predicate (FROM_FILE / DEGATED / AS_IS),
    #: the target status, the `prior_priority` to pass (None for none), the expected severity, the
    #: expected legitimacy path or REFUSED, why this row exists)
    VERDICTS = (
        (
            "a bare blocking item closed `done`",
            "next",
            None,
            None,
            FROM_FILE,
            "done",
            None,
            "error",
            REFUSED,
            "THE FAIL-CLOSED CORE, and the reason this machinery exists: closing a release-blocking "
            "item with nothing preserving the gate would let the release ship without the work. It "
            "must be an ERROR (not a warning), and it must offer all THREE fixes, because a refusal "
            "with no route out gets resolved by hand-editing the file - the exact bypass the `aw "
            "check` backstop below has to catch",
        ),
        (
            "a HANDOFF carrier declaring the SAME release",
            "next",
            "next",
            None,
            FROM_FILE,
            "done",
            None,
            "ok",
            "HANDOFF",
            "FIX ROUTE 1 OF 3: a plan (or spec) carrying `- From-Backlog: <this id6>` and the SAME "
            "`- Blocks-Release` has inherited the gate, so closing the item drops nothing. This row "
            "keeps its own identity because the three routes are independent - collapsing them into "
            "one allowed row would let two rot while the table stayed green",
        ),
        (
            "a carrier naming this item but gating a DIFFERENT release",
            "next",
            "r9z9z9",
            None,
            FROM_FILE,
            "done",
            None,
            "error",
            REFUSED,
            "THE OTHER HALF OF THE HANDOFF CLAIM. A carrier that gates a different release has NOT "
            "inherited this gate, so the item's release would ship unblocked. Without this row "
            "HANDOFF could degrade into 'some plan mentions this item', which is how a gate goes "
            "missing while every artifact looks correctly linked",
        ),
        (
            "a cited, resolvable in-tree evidence artifact",
            "next",
            None,
            EVIDENCE_REL,
            FROM_FILE,
            "done",
            None,
            "ok",
            "SATISFIED",
            "FIX ROUTE 2 OF 3: the work is DONE and an in-tree artifact proves it, so there is nothing "
            "left to gate. This route is what lets non-plan work (a README, research, a check) close "
            "a blocker at all; without it every blocker would need a plan to hand off to",
        ),
        (
            "an evidence citation pointing at a file that does not exist",
            "next",
            None,
            ".aw/records/walkthroughs/nope.md",
            FROM_FILE,
            "done",
            None,
            "error",
            REFUSED,
            "THE OTHER HALF OF THE SATISFIED CLAIM, and the cheapest bypass to attempt: an unresolvable "
            "citation must NOT buy a close. A resolver that accepted any string would make route 2 a "
            "rubber stamp, and the item above would still pass",
        ),
        (
            "the gate stripped from the item in the same call",
            "next",
            None,
            None,
            DEGATED,
            "done",
            None,
            "ok",
            "DE-GATED",
            "FIX ROUTE 3 OF 3, evaluated on the POST-mutation text: `--blocks-release -` releases the "
            "gate explicitly, so there is nothing to preserve. It is the honest route for 'this never "
            "really blocked the release', and reading post-mutation text is what makes a same-call "
            "de-gate legitimate rather than a two-step dance",
        ),
        (
            "an item that carries no gate at all",
            None,
            None,
            None,
            FROM_FILE,
            "done",
            None,
            "ok",
            "DE-GATED",
            "THE OVERWHELMINGLY COMMON CASE: most items do not gate a release, and closing one must "
            "cost nothing. This row is what stops the gate from taxing every ordinary close, and it "
            "reaches the same DE-GATED verdict as the row above by the same code path - an ungated "
            "item and a de-gated one are indistinguishable by design",
        ),
        (
            "a blocking item PARKED rather than closed",
            "next",
            None,
            None,
            FROM_FILE,
            "parked",
            None,
            "warn",
            None,
            "PARKING IS ALLOWED BUT WARNED, and the three-valued severity is the point: parking hides "
            "the gate from the active release-blocker view without releasing it, so refusing would "
            "block legitimate triage while staying silent would lose the blocker. No legitimacy path "
            "is reported, because none was needed",
        ),
        (
            "a blocking item GRADUATED to a plan",
            "next",
            None,
            None,
            FROM_FILE,
            "graduated",
            None,
            "ok",
            None,
            "GRADUATED PRESERVES THE GATE AND IS NOT A SUBSTITUTE FOR `done`: the item keeps its "
            "`Blocks-Release` and `aw attention` maps `graduated` to ACTIVE, so it stays in the "
            "outstanding blocker set. It must be clean with NO warning (unlike parking, nothing is "
            "hidden), and reaching `done` still requires one of the three routes above - which is what "
            "stops a release shipping with its blockers merely graduated",
        ),
        (
            "a blocking item whose priority is being demoted",
            "next",
            None,
            None,
            AS_IS,
            "open",
            "high",
            "warn",
            None,
            "A DEMOTION IS A CONTRADICTION WORTH SAYING OUT LOUD: an item that gates the release cannot "
            "also be lower priority than it was. It is a WARN because the maintainer may have good "
            "reason, and it is the only row whose verdict depends on the PRIOR state rather than the "
            "post-mutation text alone",
        ),
    )

    def test_every_close_verdict_names_the_specific_route_it_took(self):
        wrong = []
        legitimate_rows_broken = 0
        refusal_rows_broken = 0
        for (
            case,
            gate,
            carrier_gate,
            evidence,
            text_source,
            target,
            prior_priority,
            severity,
            expected_path,
            why,
        ) in self.VERDICTS:
            root = Path(tempfile.mkdtemp(dir=self.root))
            # A demotion row needs the post-mutation priority to be LOWER than `prior_priority`.
            priority = "medium" if prior_priority else "high"
            item = _write_item(root, "aaa111", blocks_release=gate, priority=priority)
            if carrier_gate is not None:
                _write_plan(
                    root, "pl0001", from_backlog="aaa111", blocks_release=carrier_gate
                )
            if evidence == EVIDENCE_REL:
                _artifact(root, EVIDENCE_REL)
            item_text = None
            if text_source == DEGATED:
                item_text = item.read_text(encoding="utf-8").replace(
                    f"- Blocks-Release: {gate}\n", ""
                )
            elif text_source == AS_IS:
                item_text = item.read_text(encoding="utf-8")
            v = CE.evaluate_blocking_close(
                root,
                item,
                target,
                evidence=evidence,
                item_text=item_text,
                prior_priority=prior_priority,
            )
            problems = []
            want_legitimate = expected_path != REFUSED
            if v.legitimate is not want_legitimate:
                problems.append(
                    f"expected legitimate={want_legitimate}, got {v.legitimate!r} "
                    f"(reason: {v.reason!r})"
                )
                if want_legitimate:
                    legitimate_rows_broken += 1
                else:
                    refusal_rows_broken += 1
            if v.severity != severity:
                problems.append(
                    f"expected severity {severity!r}, got {v.severity!r}; the severity is what "
                    "decides whether the CLI refuses, warns, or stays silent"
                )
            if expected_path == REFUSED:
                if len(v.fixes) != 3:
                    problems.append(
                        f"a refusal must offer all THREE fix routes so the maintainer is not left "
                        f"with a closed door; got {len(v.fixes)}: {list(v.fixes)!r}"
                    )
                if v.path is not None:
                    problems.append(
                        f"a refusal must report NO legitimacy path; got {v.path!r}, which means the "
                        "predicate thinks a route matched while still refusing"
                    )
            else:
                if v.path != expected_path:
                    problems.append(
                        f"expected the legitimacy path {expected_path!r}, got {v.path!r}; a close "
                        "allowed via the WRONG route is how an earlier branch comes to swallow the "
                        "later ones unnoticed"
                    )
                if v.fixes:
                    problems.append(
                        f"an allowed transition must offer no fixes; got {list(v.fixes)!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case} (-> {target}, item text: {text_source}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        direction = ""
        if refusal_rows_broken and not legitimate_rows_broken:
            direction = (
                f" ALL {refusal_rows_broken} failing row(s) are REFUSAL rows, so the gate has OPENED: "
                "a release blocker can now be closed with its gate silently dropped, which is the "
                "defect this predicate exists to prevent. The legitimacy rows above prove nothing "
                "while this is true, since a predicate allowing everything satisfies them all."
            )
        elif legitimate_rows_broken and not refusal_rows_broken:
            direction = (
                f" ALL {legitimate_rows_broken} failing row(s) are LEGITIMACY rows, so the gate has "
                "SEALED: a release blocker now cannot be closed by any route, and the refusal rows "
                "above prove nothing, since a predicate refusing everything satisfies them all. That "
                "direction gets worked around by hand-editing files, which loses the audit trail."
            )
        self.assertEqual(
            wrong,
            [],
            f"`evaluate_blocking_close` returned the wrong verdict for {len(wrong)} of "
            f"{len(self.VERDICTS)} transitions.{direction} ONE decision tree decides every row and its "
            "branches are ordered (DE-GATED, then HANDOFF, then SATISFIED, then refuse), so read the "
            "grouping: several allowed rows reporting the SAME wrong `path` means an earlier branch "
            "now matches too eagerly and is swallowing the later ones; a single route's pair of rows "
            "(allow plus its mismatched twin) failing together means that route lost its "
            "discrimination. FIX: never relax a row to green. Each of HANDOFF / SATISFIED / DE-GATED "
            "is an independent way to legitimately close a release blocker, and a row asserting only "
            "`legitimate` could not tell a correct allow from a gate that opened.\n"
            + "\n".join(wrong),
        )


#: `RESOLVER` column values for the evidence table.
SHARED = "check_engine.resolve_evidence_artifact"
SPECS_STRICT = "specs._evidence_resolvable"


class EvidenceResolverTests(unittest.TestCase):
    """V-03: what counts as a resolvable evidence citation, under BOTH resolvers.

    ONE table replaces five tests (four on the shared resolver, one on the specs one). Each passed a
    single citation string and asserted a bool, so the citation is the row and the RESOLVER is a
    column.

    THE RESOLVER BEING A COLUMN IS THE WHOLE REASON THIS IS ONE TABLE, and it states a property no
    single-resolver test can. `specs._evidence_resolvable` DELEGATES its safety, containment and
    existence checks to the shared resolver and then applies its own stricter requirement that the
    artifact be an EXECUTED IPD. So every row is judged by both, which pins two things at once: the
    shared half is genuinely shared (a row the shared resolver refuses must be refused by specs too),
    and the strictness is genuinely additive (the walkthrough and spec rows are accepted by the shared
    resolver and refused by specs). The old tests checked one cell each and could not see either
    relationship; in particular a refactor that let specs stop delegating, or that widened specs onto
    any records file, would have passed all five.

    THE UNSAFE ROWS ARE IN THE SAME TABLE and are the ones that matter most: a citation is
    OPERATOR-SUPPLIED, so traversal and out-of-tree paths are an attack surface, not a typo class. A
    resolver returning True for everything would satisfy both accept rows while making the SATISFIED
    fix route a rubber stamp for closing any release blocker.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        # specs' predicate derives the repo root from the spec file's own location, so a real spec
        # file must exist for its column to be evaluated at all.
        self.spec = self.root / ".aw" / "records" / "specs" / "sp.md"
        self.spec.parent.mkdir(parents=True, exist_ok=True)
        self.spec.write_text("# Spec\n\n- Status: implementing\n", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    #: (case, the citation, whether the file should be created first, what the SHARED resolver must
    #: return, what the STRICTER specs resolver must return, why this row exists)
    CITATIONS = (
        (
            "an executed IPD",
            ".aw/records/plans/executed/e.ipd.md",
            True,
            True,
            True,
            "THE ONLY SHAPE BOTH RESOLVERS ACCEPT, which is what makes the two columns meaningful: a "
            "spec reaching `implemented` demands proof that a plan actually ran, and that proof is "
            "equally good evidence for closing a backlog item",
        ),
        (
            "a walkthrough under the records tree",
            ".aw/records/walkthroughs/w.md",
            True,
            True,
            False,
            "THE DIVERGENCE ROW, and the reason the generalized resolver was written: non-plan work (a "
            "README, research, a check) has no executed IPD to cite, so the backlog gate accepts any "
            "in-tree records artifact. specs must still REFUSE it, because a walkthrough does not "
            "demonstrate that a spec was implemented",
        ),
        (
            "a spec file under the records tree",
            ".aw/records/specs/s.md",
            True,
            True,
            False,
            "the second divergence row, with a different records subtree, so the shared resolver's "
            "acceptance is shown to be about being IN-TREE rather than about one whitelisted "
            "directory - and specs' extra requirement is shown to be `executed/`, not 'anything but "
            "walkthroughs'",
        ),
        (
            "a records path that does not exist",
            ".aw/records/specs/nope.md",
            False,
            False,
            False,
            "EXISTENCE IS CHECKED, not just the shape of the string. A citation is typed by a human "
            "under time pressure, and a plausible-looking path to a missing file is the commonest way "
            "the SATISFIED route would be satisfied by nothing at all",
        ),
        (
            "a traversal escape out of the repo",
            "../../etc/passwd",
            False,
            False,
            False,
            "THE CITATION IS OPERATOR-SUPPLIED, so containment is a SECURITY property rather than "
            "tidiness: resolving outside the repo would let an existing file anywhere on the machine "
            "close a release blocker. Both resolvers must refuse, which is also how specs' delegation "
            "to the shared containment check is pinned",
        ),
        (
            "an existing SOURCE file outside the records tree",
            "agent_workflows/x.py",
            True,
            False,
            False,
            "THE SUBTLE REFUSAL: this file EXISTS and is inside the repo, so it passes safety and "
            "containment and is rejected only by the records-tree requirement. Evidence must be a "
            "durable RECORD a reviewer can read as an account of the work; a source file is the work "
            "itself, and citing it would make every code change self-justifying",
        ),
    )

    def test_both_resolvers_agree_on_safety_and_differ_only_in_strictness(self):
        from agent_workflows import specs

        wrong = []
        accept_cells_broken = 0
        refuse_cells_broken = 0
        for case, citation, create, want_shared, want_specs, why in self.CITATIONS:
            root = Path(tempfile.mkdtemp(dir=self.root))
            spec = root / ".aw" / "records" / "specs" / "sp.md"
            spec.parent.mkdir(parents=True, exist_ok=True)
            spec.write_text("# Spec\n\n- Status: implementing\n", encoding="utf-8")
            if create:
                _artifact(root, citation)
            problems = []
            for resolver, want, got in (
                (
                    SHARED,
                    want_shared,
                    CE.resolve_evidence_artifact(root, citation),
                ),
                (
                    SPECS_STRICT,
                    want_specs,
                    specs._evidence_resolvable(spec, citation),
                ),
            ):
                if bool(got) is not want:
                    problems.append(f"[{resolver}] expected {want}, got {got!r}")
                    if want:
                        accept_cells_broken += 1
                    else:
                        refuse_cells_broken += 1
            if problems:
                wrong.append(
                    f"  {case} ({citation!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        direction = ""
        if refuse_cells_broken and not accept_cells_broken:
            direction = (
                f" ALL {refuse_cells_broken} failing cell(s) are REFUSALS, so a resolver has WIDENED. "
                "That turns the SATISFIED fix route into a rubber stamp: any string that resolves "
                "would close a release blocker, and the accept rows above would still pass."
            )
        elif accept_cells_broken and not refuse_cells_broken:
            direction = (
                f" ALL {accept_cells_broken} failing cell(s) are ACCEPTANCES, so a resolver has "
                "NARROWED and legitimate evidence is being refused; the refusal rows prove nothing "
                "while that is true, since a resolver returning False for everything satisfies them "
                "all."
            )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.CITATIONS)} evidence citations were resolved wrongly."
            f"{direction} The two resolvers are NOT independent - specs delegates safety, containment "
            "and existence to the shared one and then adds an `executed/` requirement - so read the "
            "columns: both columns failing on one row means the SHARED half broke; only the "
            f"{SPECS_STRICT} column failing on the two divergence rows means specs stopped being "
            "stricter (it would then accept any records file as proof a spec was implemented); only "
            f"the {SHARED} column failing means the generalized resolver stopped being more "
            "permissive, which re-breaks closing non-plan work. FIX: the traversal and out-of-tree "
            "rows are a SECURITY boundary on operator-supplied input, never a tidiness rule - do not "
            "relax them.\n" + "\n".join(wrong),
        )


class SetterGateTests(unittest.TestCase):
    """V-04/V-06: what `aw backlog set` actually does to the file, end to end.

    ONE table replaces six tests (five close attempts plus the parked-warns test that used to live in
    a separate class). All six invoked `B.run_set` once and asserted the exit code plus where the file
    ended up, differing in the FIXTURE, the TARGET STATUS and the flags - all columns.

    WHY THIS LAYER IS TESTED SEPARATELY FROM THE PREDICATE, rather than trusted to it: the predicate
    returns a verdict, and the setter must HONOR it. Those are two different failures. A setter that
    computed a refusal and then moved the file anyway would pass every predicate row in this file, so
    each row here asserts the FILESYSTEM outcome - that a refused close left the item exactly where it
    was and wrote nothing into `done/`, and that an allowed one actually moved. That is the claim a
    maintainer depends on, and it is not derivable from the verdict.

    THE REFUSAL ROW PINS THE TEACHING TEXT by the tokens a human acts on: `From-Backlog`,
    `--evidence`, and `--blocks-release -`. A refusal that merely says no is worse than useless here,
    because the workaround a blocked maintainer reaches for is hand-editing the file, which bypasses
    this gate entirely - and that bypass is exactly what the `aw check` backstop below has to catch.

    THE DE-GATE ROW ALSO ASSERTS THE GATE IS GONE FROM THE MOVED FILE, and the other allowed rows
    assert it SURVIVES. Without that column `--blocks-release -` could be accepted as a magic word
    that permits the close while leaving the field in place, which would close the item while leaving
    a dangling gate on a done record.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _set(self, root, path, **kw):
        base = dict(
            dir=str(root),
            path=str(path),
            status="done",
            message="",
            apply=True,
            blocks_release=None,
            evidence=None,
            force=False,
        )
        base.update(kw)
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = B.run_set(_args(**base))
        return rc, out.getvalue(), err.getvalue()

    #: (case, the item's `Blocks-Release`, the carrier plan's `Blocks-Release` (None for no carrier),
    #: kwargs for `run_set`, the expected exit code, whether the file must have MOVED to the target
    #: directory, whether `Blocks-Release` must still be present in the moved file (None when it did
    #: not move), substrings stderr must contain, why this row exists)
    TRANSITIONS = (
        (
            "a bare blocking close, refused",
            "next",
            None,
            {},
            1,
            False,
            None,
            ("refused", "From-Backlog", "--evidence", "--blocks-release -"),
            "THE GATE ITSELF, asserted at the layer a maintainer meets it. Exit 1 is what stops a "
            "script, and the file staying put is what makes the refusal real: a setter that refused "
            "in words and moved the file anyway would pass every predicate row in this file. The three "
            "needles are the routes OUT - a refusal that only says no gets worked around by hand-"
            "editing, which is the bypass the `aw check` backstop below exists to catch",
        ),
        (
            "a close legitimized by a HANDOFF carrier",
            "next",
            "next",
            {},
            0,
            True,
            True,
            (),
            "FIX ROUTE 1 END TO END. The gate must SURVIVE in the moved file: the release is still "
            "blocked, now by the plan, so stripping the field on close would lose the fact that this "
            "item ever gated anything",
        ),
        (
            "a close legitimized by cited evidence",
            "next",
            None,
            {"evidence": EVIDENCE_REL},
            0,
            True,
            True,
            (),
            "FIX ROUTE 2 END TO END, and the route with no plan involved at all - which is why it "
            "exists: non-plan work would otherwise be unclosable. The gate survives here too, since "
            "the field records history rather than a live obligation",
        ),
        (
            "a close with `--blocks-release -` in the SAME call",
            "next",
            None,
            {"blocks_release": "-"},
            0,
            True,
            False,
            (),
            "FIX ROUTE 3 END TO END, and the only row where the gate must be ABSENT afterwards. "
            "Without that column the flag could be a magic word that permits the close while leaving "
            "the field in place, closing the item and leaving a dangling gate on a done record. It "
            "also proves the setter evaluates POST-mutation state rather than demanding two commands",
        ),
        (
            "an ungated item closed normally",
            None,
            None,
            {},
            0,
            True,
            False,
            (),
            "THE GATE MUST NOT TAX THE ORDINARY CASE. Most items gate no release, and if this row "
            "failed the whole backlog would be unclosable - a far louder outage than the one the gate "
            "prevents, which is why it sits in the same table as the refusal",
        ),
        (
            "a blocking item parked rather than closed",
            "next",
            None,
            {"status": "parked"},
            0,
            True,
            True,
            ("warning",),
            "THE WARN PATH END TO END (V-06): parking must SUCCEED (exit 0, file moved) while still "
            "telling the operator the gate is now hidden from the active view. Exit code and warning "
            "text are asserted together because a warning that set a nonzero exit would break every "
            "triage script, and a silent success would lose the blocker",
        ),
        (
            "a blocking item graduated to a plan",
            "next",
            None,
            {"status": "graduated"},
            0,
            True,
            True,
            (),
            "GRADUATION IS THE CLEAN HANDOFF STATE: exit 0, no warning at all (nothing is hidden, "
            "unlike parking), and the gate PRESERVED so `aw attention` keeps counting the item as an "
            "outstanding release blocker. Placed beside the parked row so the two warn/silent "
            "behaviors cannot be conflated",
        ),
    )

    def test_the_setter_honors_every_verdict_on_disk(self):
        wrong = []
        refusal_rows_broken = 0
        success_rows_broken = 0
        for (
            case,
            gate,
            carrier_gate,
            kwargs,
            expect_rc,
            expect_moved,
            gate_survives,
            needles,
            why,
        ) in self.TRANSITIONS:
            root = Path(tempfile.mkdtemp(dir=self.root))
            item = _write_item(root, "aaa111", blocks_release=gate)
            if carrier_gate is not None:
                _write_plan(
                    root, "pl0001", from_backlog="aaa111", blocks_release=carrier_gate
                )
            if kwargs.get("evidence") == EVIDENCE_REL:
                _artifact(root, EVIDENCE_REL)
            target_status = kwargs.get("status", "done")
            rc, _out, err = self._set(root, item, **kwargs)
            moved = root / ".aw" / "records" / "backlog" / target_status / item.name
            problems = []
            if rc != expect_rc:
                problems.append(
                    f"expected exit code {expect_rc}, got {rc}; stderr was {err.strip()!r}"
                )
                if expect_rc:
                    refusal_rows_broken += 1
                else:
                    success_rows_broken += 1
            if moved.exists() is not expect_moved:
                problems.append(
                    f"expected the item {'to be MOVED to' if expect_moved else 'to STAY OUT of'} "
                    f"backlog/{target_status}/; moved.exists()={moved.exists()!r}"
                )
                if expect_moved:
                    success_rows_broken += 1
                else:
                    refusal_rows_broken += 1
            if not expect_moved and not item.exists():
                problems.append(
                    "the original item file is GONE even though the transition was refused, so the "
                    "refusal mutated the tree"
                )
                refusal_rows_broken += 1
            if expect_moved and moved.exists() and gate_survives is not None:
                has_gate = "Blocks-Release" in moved.read_text(encoding="utf-8")
                if has_gate is not gate_survives:
                    problems.append(
                        f"expected `Blocks-Release` to be {'PRESENT' if gate_survives else 'ABSENT'} "
                        f"in the moved file, found present={has_gate!r}"
                    )
            missing = [n for n in needles if n not in err]
            if missing:
                problems.append(
                    f"stderr must contain {missing!r} (that text is how the operator learns what to "
                    f"do next); stderr was {err.strip()!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (-> {target_status}, flags={kwargs!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        direction = ""
        if refusal_rows_broken and not success_rows_broken:
            direction = (
                f" {refusal_rows_broken} REFUSAL expectation(s) failed, so the setter is now letting a "
                "release-blocking close through; the success rows prove nothing while that is true, "
                "since a setter that allows everything satisfies them all."
            )
        elif success_rows_broken and not refusal_rows_broken:
            direction = (
                f" {success_rows_broken} SUCCESS expectation(s) failed, so the setter refuses closes "
                "it must allow. That is the direction maintainers work around by hand-editing the "
                "file, which bypasses this gate entirely and loses the workflow-history record."
            )
        self.assertEqual(
            wrong,
            [],
            f"`aw backlog set` behaved wrongly for {len(wrong)} of {len(self.TRANSITIONS)} "
            f"transitions.{direction} This layer's job is to HONOR the predicate's verdict on DISK, "
            "which is a separate failure from computing it wrongly, so read what broke: an exit code "
            "wrong while the file placement is right means the verdict is being misread; the file "
            "MOVED on the refusal row means the verdict is computed and then ignored (the worst case, "
            "because the CLI reports a refusal while the gate is gone); a missing stderr needle means "
            "the refusal stopped teaching the way out. FIX: check the predicate table above first - if "
            "its rows pass and these fail, the bug is in this setter, not in the gate logic.\n"
            + "\n".join(wrong),
        )


def _git(root, *args):
    return subprocess.run(
        ["git", *args], cwd=str(root), capture_output=True, text=True, check=False
    )


#: `GIT STATE` column values for the consistency table.
STAGED = "staged in this commit"
COMMITTED = "already committed (historical)"
NO_REPO = "no git repository"


class ConsistencyCheckTests(unittest.TestCase):
    """V-05/V-06: which cross-tree rules fire on which tree, and at which severity.

    ONE table replaces six tests (five `aw check` fixtures plus the orphaned-live-blocker warn test
    that used to live in a separate class). Each built one records tree, called one check function,
    and asserted that one rule was or was not present, so the tree is the row and the GIT STATE is a
    column.

    THE ERROR AND WARN SURFACES ARE ASSERTED TOGETHER ON EVERY ROW, which is the merge's real payoff
    and is not expressible one rule at a time. `check_release_gate_consistency` sets the exit code
    while `release_gate_warnings` must never do so, and the split exists precisely so an advisory
    finding cannot fail CI. A rule migrating from one function to the other is therefore a severity
    change - a warning that starts blocking commits, or a hard error that goes advisory - and each old
    test could only see its own half. The matching-carrier row is where this bites: it must be clean
    on the error surface AND present on the warn surface, one tree and two opposite claims.

    THE GIT STATE IS A COLUMN because the hand-edit backstop is deliberately COMMIT-SCOPED: it fires
    only on a done+blocking item STAGED in this commit, so historical items closed before the gate
    existed are grandfathered. That is a property of one rule observed under two git states, which no
    single-state test can state. The `no git repository` rows show the other rules do not depend on
    git at all.

    ROWS PIN THE EXACT RULE SET on both surfaces rather than `any(...)`. An `any` check cannot see a
    second, spurious finding appearing, and a rule engine that emitted every rule on every tree would
    have satisfied every one of the six tests this replaces.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _init_git(self, root):
        _git(root, "init", "-q")
        _git(root, "config", "user.email", "t@e.com")
        _git(root, "config", "user.name", "T")
        _git(root, "config", "commit.gpgsign", "false")

    #: (case, the item's status, the item's `Blocks-Release`, the carrier plan's `Blocks-Release`
    #: (None for no carrier), the git state, the EXACT sorted error rules expected, the EXACT sorted
    #: warn rules expected, a substring the warn detail must contain (None to skip), why this row
    #: exists)
    TREES = (
        (
            "a done+blocking item staged with nothing preserving its gate",
            "done",
            "next",
            None,
            STAGED,
            ["check.blocking-item-closed-without-gate"],
            [],
            None,
            "THE HAND-EDIT BACKSTOP, and the reason this rule exists at all: the setter gate above is "
            "bypassable by editing the file and staging it, so `aw check` catches the fingerprint of "
            "that bypass. It must be an ERROR, since an advisory warning would not stop the commit",
        ),
        (
            "the same item, already committed rather than staged",
            "done",
            "next",
            None,
            COMMITTED,
            [],
            [],
            None,
            "GRANDFATHERING IS DELIBERATE AND IS WHY THE RULE IS COMMIT-SCOPED. Items closed before "
            "this gate existed are historical fact; flagging them would make `aw check` permanently "
            "red on a tree nobody can legally edit, and a permanently-red check is an ignored check. "
            "The tree here is IDENTICAL to the row above and only the git state differs, which is the "
            "whole claim",
        ),
        (
            "a done+blocking item staged WITH a matching handoff carrier",
            "done",
            "next",
            "next",
            STAGED,
            [],
            [],
            None,
            "THE LEGITIMATE CLOSE MUST BE CLEAN, and this row carries the non-vacuity load for the "
            "backstop: a rule that flagged every staged done item would satisfy the first row on its "
            "own. It also proves the check reuses the same legitimacy predicate the setter does, "
            "rather than a second, stricter opinion",
        ),
        (
            "a live carrier gating a DIFFERENT release from its source item",
            "open",
            "next",
            "r9z9z9",
            NO_REPO,
            ["check.from-backlog-gate-mismatch"],
            [],
            None,
            "A BROKEN HANDOFF, caught from the other end: the plan claims to graduate this item but "
            "gates another release, so the item's release would ship unblocked. The item is still "
            "`open` here, which is the point - the damage is detectable before anyone tries to close "
            "it. No git repo is needed, which shows this rule is tree-based rather than commit-scoped",
        ),
        (
            "a live carrier gating the SAME release as its open source item",
            "open",
            "next",
            "next",
            NO_REPO,
            [],
            ["check.orphaned-live-blocker"],
            "Fix: aw backlog set done aaa111",
            "ONE TREE, TWO OPPOSITE CLAIMS, and the row that makes the two surfaces worth asserting "
            "together: the handoff is CORRECT so nothing may block the exit code, yet the item is now "
            "redundantly open so the human view should nudge. It must be WARN-only; promoting it to "
            "the error surface would fail CI on a tree where nothing is wrong. The detail needle pins "
            "a runnable Fix command naming the item's id6, so `aw attention` can surface a "
            "cut-and-paste remedy instead of prose",
        ),
    )

    def test_each_tree_produces_exactly_its_rules_on_the_right_severity_surface(self):
        wrong = []
        firing_rows_broken = 0
        clean_cells_broken = 0
        for (
            case,
            status,
            gate,
            carrier_gate,
            git_state,
            expect_errors,
            expect_warns,
            detail_needle,
            why,
        ) in self.TREES:
            root = Path(tempfile.mkdtemp(dir=self.root))
            if git_state in (STAGED, COMMITTED):
                self._init_git(root)
            item = _write_item(root, "aaa111", status=status, blocks_release=gate)
            if carrier_gate is not None:
                _write_plan(
                    root, "pl0001", from_backlog="aaa111", blocks_release=carrier_gate
                )
            if git_state in (STAGED, COMMITTED):
                _git(root, "add", str(item.relative_to(root)))
            if git_state == COMMITTED:
                _git(root, "commit", "-q", "-m", "seed")
            errors = CE.check_release_gate_consistency(root)
            warns = CE.release_gate_warnings(root)
            problems = []
            for surface, got_drift, expected in (
                ("ERROR (sets the exit code)", errors, expect_errors),
                ("WARN (advisory only)", warns, expect_warns),
            ):
                got = sorted(d.rule for d in got_drift)
                if got != sorted(expected):
                    problems.append(
                        f"[{surface}] expected exactly {sorted(expected)!r}, got {got!r}"
                    )
                    if expected:
                        firing_rows_broken += 1
                    else:
                        clean_cells_broken += 1
            if detail_needle is not None:
                details = [d.detail for d in warns]
                if not any(detail_needle in (d or "") for d in details):
                    problems.append(
                        f"no warning detail contains {detail_needle!r}, so the attention view has no "
                        f"cut-and-paste remedy to surface; details were {details!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case} (item status={status}, git={git_state}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        direction = ""
        if firing_rows_broken and not clean_cells_broken:
            direction = (
                f" {firing_rows_broken} FIRING expectation(s) failed, so a rule has gone quiet: a "
                "dropped gate or a broken handoff would now pass `aw check` unnoticed. The clean rows "
                "prove nothing while that is true, since an engine reporting nothing satisfies them "
                "all."
            )
        elif clean_cells_broken and not firing_rows_broken:
            direction = (
                f" {clean_cells_broken} CLEAN expectation(s) failed, so a rule now fires on a tree "
                "where nothing is wrong. On the ERROR surface that means red CI with no legal fix "
                "(the grandfathered row cannot be edited), and a permanently-red check is an ignored "
                "check."
            )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.TREES)} trees produced the wrong findings.{direction} Each "
            "row is judged on BOTH severity surfaces, so read which surface moved: a rule appearing "
            "on the WARN surface when it belongs on the ERROR one means a blocking gate went advisory "
            "and commits that drop a release gate will now succeed; the reverse means an advisory "
            "nudge is failing CI. The two identical staged/committed rows differ ONLY in git state, so "
            "if they fail together the commit-scoping went and every historical done item in the "
            "repository just became a finding. FIX: rows pin the EXACT rule set rather than `any(...)` "
            "on purpose - a spurious extra finding is as unusable as a missing one, since a human "
            "cannot tell which complaint to act on.\n" + "\n".join(wrong),
        )

    def test_multiple_blockers_build_one_plan_handoff_index(self):
        """Kept separate: the claim is a CALL COUNT under a patched collaborator, not a finding set.

        Every table row asserts which rules a tree produces; this asserts HOW the advisory path
        computes them - the plans tree is scanned once for the whole sweep rather than once per open
        blocker. That needs `CE._iter_plan_ipds` patched and a three-item fixture, which is materially
        different setup, and the property is invisible to any assertion over the returned findings.
        """
        _write_item(self.root, "aaa111", status="open", blocks_release="next")
        _write_item(self.root, "bbb222", status="open", blocks_release="release2")
        _write_item(self.root, "ccc333", status="open", blocks_release="next")
        _write_plan(self.root, "pl0001", from_backlog="aaa111", blocks_release="next")
        _write_plan(
            self.root, "pl0002", from_backlog="bbb222", blocks_release="different"
        )

        real_iter = CE._iter_plan_ipds
        calls = 0

        def counted_iter(repo_root):
            nonlocal calls
            calls += 1
            yield from real_iter(repo_root)

        with patch.object(CE, "_iter_plan_ipds", side_effect=counted_iter):
            warnings = CE.release_gate_warnings(self.root)

        self.assertEqual(calls, 1)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].rule, "check.orphaned-live-blocker")
        self.assertIn("done aaa111", warnings[0].detail)


if __name__ == "__main__":
    unittest.main()
