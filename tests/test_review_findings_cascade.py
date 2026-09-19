"""Tests for revgate Order 03 (7nkcgp): a findings-blocked plan does not release its dependents.

Order 02 (`plqjt7`) made an unescalated gating finding REPORTABLE. This Order makes it BLOCKING for
anything that depends on the plan: an `executed:` edge is no longer satisfied by file location alone.

Covers:
* V-01 - the block itself, on BOTH resolution paths in `dependency_status` (the out-of-queue
  `bucket == "executed"` path AND the in-queue `EXECUTION_SUCCESS_STATES` path), plus proof the
  dependent is `dependency-blocked` and starts NO session, and that resolving the finding un-blocks it.
* V-02 - both host drivers decide IDENTICALLY through ONE shared predicate that lives in a NON-runner
  module, with no runner-to-runner import.
* V-03 - `aw check`'s evaluator reports the condition under a NEW, accurately-named, REGISTERED rule id
  (reuse of the identity verdicts `dangling`/`ambiguous` was evaluated and rejected).
* V-04 - the `dependency-blocked` event payload and the run report name the ROOT CAUSE (finding id +
  severity) and the exact recovery command, additively (the flat `dependencies` list keeps its shape).
* V-05 - transitive cascade (A -> B -> C), the threshold matrix, `off` disabling, and recovery via the
  REAL `--retry-incomplete` flag (a BARE resume does NOT re-queue, so a bare-resume recovery test would
  pass vacuously and enshrine a false claim).
* V-06 - cross-surface non-evasion: the SAME fixture is refused by every authority surface.
* V-07 - the `/exec-set` Set compiler treats a findings-blocked child as a gate and blocks its
  transitive descendants, reusing the EXISTING `_propagate_blocked` cascade, while leaving an
  independent sibling runnable.
* V-08 - the ACTUAL recovery behavior: still blocked after a bare resume, re-queued with
  `--retry-incomplete`, and the runner's re-queue default is UNCHANGED.

EVERY fixture is an ISOLATED tmp repo. No assertion reads this repository's live `.aw/records/runs/`,
live plans, or live `.aw/config/project.json`: asserting against live state is a known defect class
here (pending plan `i79rgh`, Order testinvoke-02), and a threshold assertion that read the live config
would be order-dependent and would break the moment a maintainer set the key.

WHY TABLES: this file's subject is ONE predicate (`rf.subject_gating_blocks`) consumed by FOUR
authority surfaces, and the tests were the same shape repeated per surface and per knob: build an
isolated repo, vary one thing, assert blocked or not blocked. Those are rows.

THE HOST DRIVER IS A COLUMN, NOT A `subTest`. Every blocking test previously looped
`for name, drv in DRIVERS` with a `subTest`, which reports each host as its own failure. That is
exactly backwards for the property being defended: the whole point of V-02 is that the two hosts CANNOT
DIVERGE, so the interesting fact is whether they AGREE, and a divergence must be reported as one
finding naming both answers. The tables below therefore evaluate every row on BOTH drivers and treat
disagreement as its own failure class, which no per-host `subTest` can state.

THE FOUR SURFACES SHARE ONE TABLE for the same reason. A gate proven on three of four surfaces is a
gate with an undocumented bypass, and the realistic regression is in the SHARED predicate, which moves
every surface at once. Reporting them together is what distinguishes "the predicate changed" (all
surfaces move) from "one surface was unwired" (one moves), which is the first question to ask.

THE EXHAUSTIVE `is_gating` TRUTH TABLE IS NOT DUPLICATED HERE. `tests/test_review_findings.py` owns a
21-cell severity x threshold grid over the pure predicate. These tables assert what that grid cannot:
that a threshold in a repo's `project.json` is RESOLVED and reaches each SURFACE. The severity rows are
therefore chosen for plumbing coverage - an AT-threshold boundary row for every active threshold, since
the comparison is `>=` and not `>`, plus a just-below row and the `off` opt-out - and not for
truth-table completeness. A failure here with that grid green means config resolution or surface
wiring broke, not the predicate.

Tests that are NOT rows carry a one-line docstring saying why: a stateful multi-step fixture, a claim
about a module identity rather than an outcome, or a report-rendering assertion whose setup is a
hand-built run state.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import NamedTuple

from agent_workflows import agy_runipd as agy
from agent_workflows import check_engine as ce
from agent_workflows import ipd_set_plan as sp
from agent_workflows import oc_runipd as oc
from agent_workflows import review_findings as rf

DEP_RULE = "check.ipd-dependency-findings-blocked"

#: The two host drivers, exercised through the SAME assertions so neither can drift.
DRIVERS = (("oc", oc), ("agy", agy))


# --------------------------------------------------------------------------------------
# Isolated fixture builders
# --------------------------------------------------------------------------------------


def _src(mod) -> str:
    """Read a module's own source (used to assert structural properties, never behavior)."""
    return Path(str(mod.__file__)).read_text(encoding="utf-8")


def _mkrepo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="aw_revgate03_"))
    for lane in ("pending", "executed", "superseded", "not-executed", "reusable"):
        (d / ".aw" / "records" / "plans" / lane).mkdir(parents=True)
    (d / ".aw" / "records" / "reviews").mkdir(parents=True)
    (d / ".aw" / "config").mkdir(parents=True)
    return d


def _set_threshold(repo: Path, value: str | None) -> None:
    """Write (or remove) `review_findings_gate` in the FIXTURE's project.json (never the live one)."""
    pj = repo / ".aw" / "config" / "project.json"
    if value is None:
        if pj.exists():
            pj.unlink()
        return
    pj.write_text(
        json.dumps({"review_findings_gate": {"block_at": value}}), encoding="utf-8"
    )


def _plan(
    repo: Path,
    id6: str,
    *,
    lane: str = "executed",
    status: str = "executed",
    order: int = 1,
    deps: str = "none",
    set_id: str = "demo",
) -> Path:
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / lane
        / f"20260829-{set_id}-{order:02d}-{id6}-cascade-fixture.ipd.md"
    )
    p.write_text(
        f"# IPD: cascade fixture {id6}\n\n"
        f"- Date: 2026-08-29\n- Kind: child\n- Scope-Paths: x.py\n"
        f"- Item-Dependencies: {deps}\n- Status: {status}\n- Set: {set_id}\n"
        f"- Order: {order}\n- Id: {id6}\n\n"
        f"## Workflow history\n- 2026-08-29 draft (t): created.\n\n"
        f"## Goal\ng\n\n"
        f"## Detailed Implementation Checklist (TODO)\n\n"
        f"- [ ] E-01 do the thing\n  - Depends on: none\n"
        f"  - Expected outcome: done\n  - Execution state: pending\n\n"
        f"## Validation and cross-check (verify before reporting done)\n\n"
        f"- [ ] V-01 validates E-01\n  - Required evidence: paste it\n"
        f"  - Observed evidence:\n  - Result: pending\n",
        encoding="utf-8",
    )
    return p


def _finding(
    fid: str = "F-1", severity: str = "high", decision: str = "open"
) -> rf.Finding:
    return rf.Finding(
        fid,
        severity,
        "IN-SCOPE",
        "rubric",
        "x.py:1",
        "the finding text",
        "Overall:Low",
        decision,
        "the resolution",
    )


def _review(repo: Path, id6: str, *, rounds=None) -> Path:
    if rounds is None:
        rounds = [rf.Round(1, (_finding(),), ())]
    return rf.write_review(
        repo
        / ".aw"
        / "records"
        / "reviews"
        / f"20260829-demo-01-{id6}-cascade.review.md",
        subject_id=id6,
        subject_type="ipd",
        reviewed_at="2026-08-29",
        reviewer="test",
        verdict="REVIEWED - OPEN QUESTIONS",
        rounds=rounds,
    )


def _state(repo: Path, queue: list[dict]) -> dict:
    return {"repo": str(repo), "run_id": "run-test", "queue": queue}


def _item(
    id6: str, deps: list[str], *, status: str = "queued", position: int = 1
) -> dict:
    return {
        "id6": id6,
        "position": position,
        "setid": "demo",
        "status": status,
        "action": "execute",
        "dependencies": deps,
    }


class _RepoCase(unittest.TestCase):
    def setUp(self):
        self.repo = _mkrepo()

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)


# --------------------------------------------------------------------------------------
# V-01 / V-02 / V-05: the runner block, with the HOST as a column
# --------------------------------------------------------------------------------------


class _Row(NamedTuple):
    """One row of the runner-block table.

    `case` and `why` are required; every other field defaults to the canonical blocking fixture (an
    `executed` dependency carrying one round with one `high`/`open` finding, a single queued dependent
    at threshold `high`), so a row names ONLY the knob it turns.
    """

    #: Short label naming the input, used verbatim in the failure report.
    case: str
    #: The RULE this row encodes, not a restatement of the data.
    why: str
    #: Findings per round: a tuple of rounds, each a tuple of (id, severity, decision).
    rounds: tuple[tuple[tuple[str, str, str], ...], ...] = ((("F-1", "high", "open"),),)
    #: `review_findings_gate.block_at`; None writes NO project.json (default resolution).
    threshold: str | None = "high"
    #: "writer" | "malformed" | "absent" - the dependency's review artifact shape.
    artifact: str = "writer"
    #: The dependent queue item's action (only `executed:` work edges are findings-gated).
    action: str = "execute"
    #: Put the dependency IN the queue as an already-`executed` item (the second resolution path).
    in_queue: bool = False
    #: Must the edge be UNSATISFIED (i.e. must the dependent be blocked)?
    blocked: bool = True
    #: Substrings the per-dependency reason must contain when blocked.
    reason_needles: tuple[str, ...] = ()


_MALFORMED_REVIEW = (
    "# Review\n\n- Subject-Id: depaaa\n- Subject-Type: ipd\n\n## Round 1\n\n"
    "| # | Severity |\n|---|---|\n| F-1 |\n"
)


def _build_row(row: _Row) -> tuple[Path, dict, dict]:
    """Materialize one row. Returns (repo, the dependent queue item, the run state)."""
    repo = _mkrepo()
    _plan(repo, "depaaa")
    if row.artifact == "writer":
        rounds = [
            rf.Round(n, tuple(_finding(*f) for f in findings), ())
            for n, findings in enumerate(row.rounds, 1)
        ]
        _review(repo, "depaaa", rounds=rounds)
    elif row.artifact == "malformed":
        (
            repo
            / ".aw"
            / "records"
            / "reviews"
            / "20260829-demo-01-depaaa-cascade.review.md"
        ).write_text(_MALFORMED_REVIEW, encoding="utf-8")
    elif row.artifact != "absent":  # pragma: no cover - guards a table typo
        raise AssertionError(f"unknown artifact shape {row.artifact!r}")
    _set_threshold(repo, row.threshold)

    dependent = _item("itemaa", ["depaaa"], position=2 if row.in_queue else 1)
    dependent["action"] = row.action
    queue = [dependent]
    if row.in_queue:
        queue.insert(0, _item("depaaa", [], status="executed", position=1))
    return repo, dependent, _state(repo, queue)


class RunnerBlockTests(unittest.TestCase):
    """`dependency_status`: when an `executed:` edge is NOT satisfied, on BOTH hosts at once.

    Fifteen tests across three classes became this one table. `BlockingTests` varied the resolution
    path, the decision, and the artifact shape; `ThresholdTests` varied the configured threshold
    through a private `_blocked_at` helper; `SharedPredicateTests` re-ran one fixture to compare the
    hosts. All of them built the same repo and asked the same question.

    THE HOST IS A COLUMN AND DISAGREEMENT IS ITS OWN FAILURE CLASS. The replaced tests looped over
    `DRIVERS` inside a `subTest`, so `oc` and `agy` were reported as independent failures, and
    `test_both_drivers_agree_on_the_same_fixture` existed to assert agreement on ONE fixture. That is
    backwards: V-02's property is that the hosts cannot diverge, so agreement must be asserted on
    EVERY row, and a divergence must surface as a single finding naming both answers. It is the
    highest-value signal this file can produce, because a gate one host enforces and the other does
    not is a gate evadable by choosing a host, and a per-host `subTest` shows it as two unrelated red
    lines instead of one contradiction.

    THRESHOLD ROWS ARE BOUNDARY-COMPLETE PER THRESHOLD, not truth-table complete: for `medium`,
    `high`, and `blocker` there is a row AT the threshold (which MUST block, since the comparison is
    `>=`) and one just below it. The exhaustive severity grid lives in tests/test_review_findings.py
    over the pure predicate; these rows prove the configured value is resolved and reaches the runner.

    NEGATIVE ROWS SHARE THE TABLE with blocking rows because they are each other's control. A
    `dependency_status` that returned False for everything would satisfy every blocking row, and one
    that returned True for everything would satisfy every clean row; only both together are evidence.
    The failure message counts them separately and says when the blocking rows are broken, since at
    that moment every clean row is vacuous.
    """

    ROWS: tuple[_Row, ...] = (
        # -- The two resolution paths. ----------------------------------------------------
        _Row(
            "an out-of-queue executed dep carrying a gating finding",
            "the `bucket == 'executed'` path: FILE LOCATION ALONE must no longer satisfy an "
            "`executed:` edge, which is the entire change this Order makes",
            reason_needles=("F-1", "high"),
        ),
        _Row(
            "an in-queue dep already marked executed in THIS run",
            "the `EXECUTION_SUCCESS_STATES` path. Without this SECOND call site the gate would "
            "depend on whether the target happens to be part of the same run, which is exactly the "
            "path-dependent hole this Set exists to remove",
            in_queue=True,
            reason_needles=("F-1", "high"),
        ),
        # -- The control: no artifact at all. ---------------------------------------------
        _Row(
            "an executed dep with NO review artifact",
            "the pre-Order-03 behavior is UNCHANGED for the 400+ plans that have no review: an "
            "absent artifact is silent, which is a safety requirement, not laziness",
            artifact="absent",
            blocked=False,
        ),
        # -- The decision axis. -----------------------------------------------------------
        _Row(
            "the finding marked fixed",
            "`fixed` is the only decision that CLOSES a finding, so it is the only one that may "
            "release the dependent",
            rounds=((("F-1", "high", "fixed"),),),
            blocked=False,
        ),
        _Row(
            "the finding marked deferred",
            "a deferral is a deliberate decision NOT to fix, so it must block a dependent exactly "
            "as `open` does; otherwise deferring is a free bypass",
            rounds=((("F-1", "high", "deferred"),),),
            reason_needles=("deferred",),
        ),
        _Row(
            "the finding marked replan",
            "MEASURED ASYMMETRY, pinned deliberately: the CASCADE blocks on `replan` because it "
            "asks `is_resolved` (only `fixed` resolves), while Order 02's escalation rule EXCLUDES "
            "`replan` via `check_engine._UNFIXED_DECISIONS`. So one `replan` finding blocks "
            "dependents while raising no unescalated-finding complaint. That is the safe direction "
            "for a cascade and it is NOT symmetric with the other gate; do not 'fix' it in either "
            "direction without deciding to",
            rounds=((("F-1", "high", "replan"),),),
            reason_needles=("replan",),
        ),
        # -- Current-round semantics. -----------------------------------------------------
        _Row(
            "raised in round 1, fixed in round 2",
            "current-round semantics: a finding superseded by a later round is not live, so it must "
            "not block anything",
            rounds=((("F-1", "high", "open"),), (("F-1", "high", "fixed"),)),
            blocked=False,
        ),
        _Row(
            "fixed in round 1, reopened in round 2",
            "the CONVERSE, which stops 'read the current round' from degrading into 'any round said "
            "fixed': a reopened finding blocks again",
            rounds=((("F-1", "high", "fixed"),), (("F-1", "high", "open"),)),
            reason_needles=("F-1",),
        ),
        # -- The threshold axis: an AT-threshold boundary row for every active threshold. --
        _Row(
            "a medium finding at threshold medium",
            "BOUNDARY for `medium`: AT the threshold MUST block, because the comparison is >=, not "
            "> . This is the row a 'strictly greater' refactor breaks",
            rounds=((("F-1", "medium", "open"),),),
            threshold="medium",
        ),
        _Row(
            "a low finding at threshold medium",
            "just BELOW `medium`, which is what proves the boundary row above is a real comparison "
            "rather than a constant block",
            rounds=((("F-1", "low", "open"),),),
            threshold="medium",
            blocked=False,
        ),
        _Row(
            "a high finding at threshold high",
            "BOUNDARY for `high`, the default an unconfigured repo resolves to, and therefore the "
            "single most load-bearing row in this table",
            threshold="high",
        ),
        _Row(
            "a medium finding at threshold high",
            "just BELOW `high`: a stricter configured threshold must actually let a medium through, "
            "or the config value does nothing",
            rounds=((("F-1", "medium", "open"),),),
            threshold="high",
            blocked=False,
        ),
        _Row(
            "a blocker finding at threshold blocker",
            "BOUNDARY for `blocker`, the strictest threshold: AT it must still block",
            rounds=((("F-1", "blocker", "open"),),),
            threshold="blocker",
        ),
        _Row(
            "a high finding at threshold blocker",
            "just BELOW `blocker`: the threshold deliberately lets a HIGH pass, which is the whole "
            "reason a repo would configure it",
            threshold="blocker",
            blocked=False,
        ),
        _Row(
            "a blocker finding at threshold medium",
            "ABOVE the threshold: the comparison is an ORDERING, so severities above the bar block "
            "too rather than only the exact match",
            rounds=((("F-1", "blocker", "open"),),),
            threshold="medium",
        ),
        _Row(
            "a high finding with NO project.json",
            "the ABSENT-KEY DEFAULT is fail-CLOSED at `high`, so an unconfigured repo still blocks. "
            "A default resolving to `off` would silently disable the cascade everywhere",
            threshold=None,
        ),
        _Row(
            "a medium finding with NO project.json",
            "and the default is `high` SPECIFICALLY: this row pins WHICH default, since the row "
            "above passes for any default at or below high",
            rounds=((("F-1", "medium", "open"),),),
            threshold=None,
            blocked=False,
        ),
        _Row(
            "a blocker finding at threshold off",
            "`off` DISABLES EVEN A BLOCKER, which is the entire meaning of the documented opt-out "
            "and the row an over-eager 'blockers always block' change would break",
            rounds=((("F-1", "blocker", "open"),),),
            threshold="off",
            blocked=False,
        ),
        # -- The artifact axis. -----------------------------------------------------------
        _Row(
            "a present but unparseable review artifact",
            "a present-but-untrustworthy artifact is an ERROR, not an absence: silently skipping it "
            "is the hole, since a malformed table could otherwise hide any severity",
            artifact="malformed",
        ),
        # -- The action axis. -------------------------------------------------------------
        _Row(
            "the dependent's action is review",
            "only an `executed:` edge consumed by WORK asserts completed-and-verified code. A "
            "review turn reads the prerequisite instead of building on it, so gating it was a "
            "measured defect (see the check-engine table) and it must stay exempt",
            action="review",
            blocked=False,
        ),
    )

    def test_the_runner_blocks_exactly_when_it_should_on_both_hosts(self) -> None:
        wrong = []
        blocking_rows_broken = 0
        clean_rows_broken = 0
        divergences = 0
        for row in self.ROWS:
            repo, dependent, state = _build_row(row)
            try:
                problems = []
                answers = {}
                for name, drv in DRIVERS:
                    satisfied, missing = drv.dependency_status(dependent, state)
                    answers[name] = (bool(satisfied), list(missing))

                if answers["oc"] != answers["agy"]:
                    divergences += 1
                    problems.append(
                        f"THE HOSTS DISAGREE: oc said {answers['oc']!r} and agy said "
                        f"{answers['agy']!r}. The gate is then evadable by choosing a host"
                    )
                else:
                    satisfied, missing = answers["oc"]
                    if satisfied is row.blocked:
                        if row.blocked:
                            blocking_rows_broken += 1
                            problems.append(
                                "the edge was SATISFIED, so the dependent would RUN against a "
                                "prerequisite carrying an unresolved gating finding"
                            )
                        else:
                            clean_rows_broken += 1
                            problems.append(
                                "the edge was UNSATISFIED, so a dependent that should run was "
                                f"blocked (missing={missing!r})"
                            )
                    elif row.blocked:
                        if missing != ["depaaa"]:
                            problems.append(
                                f"the unsatisfied list was {missing!r}, expected exactly "
                                "['depaaa']: the flat list must keep naming the blocking id"
                            )
                        for name, drv in DRIVERS:
                            _s, _m, reasons = drv.dependency_status_detailed(
                                dependent, state
                            )
                            why = reasons.get("depaaa", "")
                            for needle in row.reason_needles:
                                if needle not in why:
                                    problems.append(
                                        f"{name}: the reason does not mention {needle!r}; it "
                                        f"said {why!r}. A block whose cause is unnamed is one an "
                                        "operator cannot clear"
                                    )
                if problems:
                    wrong.append(
                        f"  {row.case}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {row.why}"
                    )
            finally:
                shutil.rmtree(repo, ignore_errors=True)

        notes = []
        if divergences:
            notes.append(
                f"{divergences} row(s) show the TWO HOSTS DISAGREEING, which is the most serious "
                "failure this table can report: V-02's whole claim is that both hosts decide "
                "through ONE predicate in a non-runner module, so a divergence means a runner has "
                "grown its own copy of the logic and the gate can be evaded by switching host."
            )
        if blocking_rows_broken:
            notes.append(
                f"{blocking_rows_broken} MUST-BLOCK row(s) failed, and while they are broken every "
                "clean row here is VACUOUS: a `dependency_status` that never blocks satisfies all "
                "of them."
            )
        elif clean_rows_broken:
            notes.append(
                f"{clean_rows_broken} MUST-NOT-BLOCK row(s) failed while every blocking row "
                "passed, which is the over-blocking direction: work that should proceed is being "
                "refused, and in the `absent` row's case that would strand the entire plan corpus."
            )
        self.assertEqual(
            wrong,
            [],
            f"the runner findings gate is wrong on {len(wrong)} of {len(self.ROWS)} inputs. "
            + " ".join(notes)
            + " Read the failures together, because the shape of the moved set names the cause: if "
            "the AT-threshold rows moved, the comparison changed between >= and >; if a whole "
            "threshold column moved, `review_findings_gate.block_at` resolution broke; if the "
            "`off` row moved, the opt-out is gone; if the ROUND rows moved, `current_findings()` "
            "stopped filtering by round; if the two RESOLUTION-PATH rows split, only one of the "
            "two call sites in `dependency_status` was updated and the gate is evadable by being "
            "in-queue; if the `absent` row moved, the grandfathering that keeps 400+ review-less "
            "plans runnable is gone. FIX: change `review_findings.subject_gating_blocks`, which "
            "both hosts share, rather than either runner.\n" + "\n".join(wrong),
        )


class TransitiveCascadeTests(_RepoCase):
    """The cascade reaches INDIRECT dependents, and does not reach independent items.

    Two tests became one table whose column is the QUESTION asked of one three-item queue: which items
    are blocked, and which item selection actually chooses. They belong together because they are the
    two halves of one property ("everything downstream waits, nothing else does") measured on the SAME
    fixture, and asserting only the first would permit a Set-wide halt.

    Both rows run on both hosts, with disagreement reported as its own failure, for the reason given on
    `RunnerBlockTests`.
    """

    #: (case, the id6 whose status is asked, expected satisfied, expected missing, why)
    CHAIN = (
        (
            "B, the direct dependent of the finding-carrying A",
            "bbb222",
            False,
            ["aaa111"],
            "the DIRECT block: A carries the finding, so B's edge to A is unsatisfied",
        ),
        (
            "C, which depends on B and not on A at all",
            "ccc333",
            False,
            ["bbb222"],
            "the INDIRECT block, and the maintainer's stated rule: C waits because B is not in a "
            "success state. This is what makes 'everything depending on a failed item waits' true "
            "of the whole chain rather than only of immediate dependents. Note C's missing list "
            "names B, not A: the cascade is transitive through the queue, not a reachability "
            "search over findings",
        ),
        (
            "an independent item depending on nothing",
            "indep1",
            True,
            [],
            "the gate blocks DESCENDANTS, not the Set: an unrelated item must stay satisfiable, or "
            "one finding halts everything and the blast radius is the whole run",
        ),
    )

    def test_the_cascade_blocks_descendants_and_spares_independents(self) -> None:
        _set_threshold(self.repo, "high")
        _plan(self.repo, "aaa111")
        _review(self.repo, "aaa111")
        state = _state(
            self.repo,
            [
                _item("aaa111", [], status="executed", position=1),
                _item("bbb222", ["aaa111"], position=2),
                _item("ccc333", ["bbb222"], position=3),
                _item("indep1", [], position=4),
            ],
        )
        by_id = {i["id6"]: i for i in state["queue"]}

        wrong = []
        for case, id6, expect_sat, expect_missing, why in self.CHAIN:
            answers = {
                name: tuple(drv.dependency_status(by_id[id6], state))
                for name, drv in DRIVERS
            }
            problems = []
            if answers["oc"] != answers["agy"]:
                problems.append(
                    f"THE HOSTS DISAGREE: oc={answers['oc']!r} agy={answers['agy']!r}"
                )
            else:
                satisfied, missing = answers["oc"]
                if bool(satisfied) is not expect_sat:
                    problems.append(
                        f"satisfied={bool(satisfied)}, expected {expect_sat}"
                    )
                if list(missing) != expect_missing:
                    problems.append(
                        f"missing={list(missing)!r}, expected {expect_missing!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )

        # The SELECTION half, asserted on the same fixture: a satisfiable item is still CHOSEN while
        # the blocked chain waits. Stated as selection rather than as "independent items still
        # proceed", because the runner's selection loop is ALL-OR-NOTHING at its terminal step (when
        # nothing is satisfiable it blocks every queued item and breaks out of the run). That
        # terminal behavior is PRE-EXISTING and this plan does not change it.
        for name, drv in DRIVERS:
            queued = [i for i in state["queue"] if i["status"] == "queued"]
            chosen = [i["id6"] for i in queued if drv.dependency_status(i, state)[0]]
            if chosen != ["indep1"]:
                wrong.append(
                    f"  {name}: selection chose {chosen!r}, expected exactly ['indep1']\n"
                    "    this row exists because: independent progress is a property of "
                    "SELECTION, and it is what keeps one finding from stalling an entire run"
                )
        self.assertEqual(
            wrong,
            [],
            f"the transitive cascade is wrong in {len(wrong)} of {len(self.CHAIN) + len(DRIVERS)} "
            "checks over ONE A->B->C queue plus an independent sibling. Read them together: if "
            "only the C row moved, the block is not transitive and only IMMEDIATE dependents wait, "
            "so work downstream of a failure proceeds against unverified code; if the INDEPENDENT "
            "row moved to blocked, the cascade over-reaches and one finding halts the whole Set; "
            "if the selection check moved while the per-item rows passed, `dependency_status` is "
            "right but the selection loop stopped honoring it. FIX: the cascade is the queue's own "
            "transitive closure over unsatisfied edges, so extend nothing here - C must be blocked "
            "BY B, never by A directly.\n" + "\n".join(wrong),
        )


class SharedPredicateTests(unittest.TestCase):
    """V-02, asserted STRUCTURALLY: one definition, in a non-runner module, with no host coupling.

    Three tests became one table of source-level claims. These cannot be replaced by behavioral
    assertions, which is why they are kept at all: the `RunnerBlockTests` table proves the hosts
    currently AGREE, but a runner could carry a forked copy of the severity logic that agrees today
    and drifts tomorrow, and that fork is only visible in the source. A runner-to-runner import is the
    same kind of claim - it is not wrong today, it is a coupling that collides with the rununify
    extraction later.
    """

    #: (claim, module or None for the predicate itself, required substrings, forbidden, why)
    CLAIMS = (
        (
            "oc_runipd delegates to the shared predicate",
            oc,
            ("subject_gating_blocks", "_findings_block_reason"),
            ("_SEVERITY_RANK",),
            "the runner must CALL the shared predicate and hold no severity ranking of its own; a "
            "local rank is how the two hosts come to disagree",
        ),
        (
            "agy_runipd delegates to the shared predicate",
            agy,
            ("subject_gating_blocks", "_findings_block_reason"),
            ("_SEVERITY_RANK",),
            "the same claim on the second host, so neither can be the one that forked",
        ),
        (
            "oc_runipd does not import the other runner",
            oc,
            (),
            ("import agy_runipd",),
            "a runner-to-runner import would be a NEW coupling that collides with the rununify "
            "extraction; shared logic belongs in a non-runner module",
        ),
        (
            "agy_runipd does not import the other runner",
            agy,
            (),
            ("import oc_runipd",),
            "the same, in the other direction, since either import creates the coupling",
        ),
    )

    def test_the_predicate_is_shared_not_reimplemented(self) -> None:
        wrong = []
        for claim, module, required, forbidden, why in self.CLAIMS:
            src = _src(module)
            problems = []
            missing = [s for s in required if s not in src]
            if missing:
                problems.append(f"{module.__name__} no longer contains {missing!r}")
            leaked = [s for s in forbidden if s in src]
            if leaked:
                problems.append(
                    f"{module.__name__} now contains {leaked!r}, which it must not"
                )
            if problems:
                wrong.append(
                    f"  {claim}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.CLAIMS)} single-definition claims broke. These are SOURCE "
            "claims because the defect they catch is invisible to behavior: a forked severity "
            "comparison passes every test on the day it is written and only shows up later as the "
            "two hosts disagreeing about what blocks. Read them together: both hosts failing the "
            "same way means the shared predicate was renamed (update the rows); ONE host failing "
            "means that host forked (delete the fork, do not relax the row). FIX: the one "
            "definition lives in `review_findings`; both runners hold thin delegates.\n"
            + "\n".join(wrong),
        )

    def test_the_predicate_lives_in_a_non_runner_module(self) -> None:
        """Kept separate: an identity claim about ONE function object, not a data row."""
        self.assertEqual(
            rf.subject_gating_blocks.__module__,
            "agent_workflows.review_findings",
            "the predicate must live in a non-runner module so both hosts and check_engine can "
            "share it without importing a runner",
        )


# --------------------------------------------------------------------------------------
# V-03: the shared `aw check` evaluator
# --------------------------------------------------------------------------------------


class CheckEngineRuleTests(unittest.TestCase):
    """`evaluate_ipd_dependencies`: which `Item-Dependencies:` edges the findings gate refuses.

    Nine tests became one table. Each built the same two-plan fixture (a findings-carrying target plus
    a dependent declaring an edge to it) and varied one thing: the EDGE KIND, the consuming ACTION, the
    decision, or the threshold. The ACTION axis is where a table earns its place, because the exemption
    and its counterpart are one rule with two directions, and the replaced tests expressed them as a
    permissive test plus a separate strict test whose four cases lived in a `subTest` loop. Reading
    them as one table is what makes "review is exempt, EVERYTHING ELSE including an unknown action is
    strict" a single readable statement, and a fail-open default (an unmapped path silently treated as
    a review) cannot hide between two files.
    """

    #: (case, edge, action mapping, decision, threshold, expected hits, needles, why)
    EDGES = (
        (
            "an executed: edge to a findings-blocked plan",
            "executed:depaaa",
            None,
            "open",
            "high",
            1,
            ("F-1", "high"),
            "THE BASE CASE: an `executed:` edge asserts completed-and-verified work, so an "
            "unresolved gating finding on the target refuses it, reported against the DEPENDENT "
            "(the plan whose edge cannot be satisfied) and naming the finding",
            "dependent",
        ),
        (
            "an exists: edge to the same plan",
            "exists:ipd:depaaa",
            None,
            "open",
            "high",
            0,
            (),
            "`exists:` is a STRUCTURAL claim (the artifact is there), not a claim about completed "
            "work, so it stays ungated. Gating it would make an unresolved finding block plans "
            "that only reference the target",
            "",
        ),
        (
            "an executed: edge whose finding is fixed",
            "executed:depaaa",
            None,
            "fixed",
            "high",
            0,
            (),
            "the clean control: without it, an evaluator that reported the rule for every "
            "`executed:` edge would satisfy the base case above",
            "",
        ),
        (
            "an executed: edge at threshold off",
            "executed:depaaa",
            None,
            "open",
            "off",
            0,
            (),
            "the `off` opt-out must hold on THIS surface too. A threshold honored by the runner "
            "and ignored by `aw check` is a gate a repo cannot actually disable",
            "",
        ),
        (
            "a review action consuming the edge",
            "executed:depaaa",
            "review",
            "open",
            "high",
            0,
            (),
            "spec 25kzda 2.9's REVIEW row. MEASURED DEFECT (2026-09-08): a run was refused at "
            "preflight because `m7gvuz` declared two `executed:` edges whose targets carried "
            "gating findings, yet every plan involved was `to-review`, so the consuming action was "
            "`review` and the run would have written no code at all; 8 selectors and 21 queued "
            "items were refused over an edge the spec exempts. It was also CIRCULAR: the Set "
            "existed to FIX gate defects and the gate blocked reviewing it",
            "",
        ),
        (
            "an execute action consuming the edge",
            "executed:depaaa",
            "execute",
            "open",
            "high",
            1,
            ("F-1",),
            "THE COUNTERPART, so the review exemption cannot be mistaken for a general relaxation: "
            "an execute turn imports, calls, or builds on the prerequisite's code, so the finding "
            "still refuses",
            "dependent",
        ),
        (
            "an orchestrate action consuming the edge",
            "executed:depaaa",
            "orchestrate",
            "open",
            "high",
            1,
            ("F-1",),
            "orchestration retires a Set on the strength of its children's completed work, so it "
            "is strict like execute and not exempt like review",
            "dependent",
        ),
        (
            "an action map that does not mention this plan",
            "executed:depaaa",
            "__unmapped__",
            "open",
            "high",
            1,
            ("F-1",),
            "THE FAIL-CLOSED DEFAULT, and the most important row of the action axis: a path absent "
            "from the map must be treated as STRICT, never as a review. A fail-open default here "
            "would silently exempt every caller that forgot to pass actions",
            "dependent",
        ),
    )

    def test_the_gate_refuses_exactly_the_work_edges(self) -> None:
        wrong = []
        refusing_rows_broken = 0
        for (
            case,
            edge,
            action,
            decision,
            threshold,
            expected,
            needles,
            why,
            loc,
        ) in self.EDGES:
            repo = _mkrepo()
            try:
                _plan(repo, "depaaa")
                _review(
                    repo,
                    "depaaa",
                    rounds=[rf.Round(1, (_finding(decision=decision),), ())],
                )
                dependent = _plan(
                    repo,
                    "itemaa",
                    lane="pending",
                    status="approved",
                    order=2,
                    deps=edge,
                )
                _set_threshold(repo, threshold)
                kwargs = {}
                if action is not None:
                    actions = (
                        {"/nonexistent/other-plan.ipd.md": "review"}
                        if action == "__unmapped__"
                        else {str(dependent): action}
                    )
                    kwargs = {
                        "plans": [(dependent, dependent.read_text(encoding="utf-8"))],
                        "actions": actions,
                    }
                drift = ce.evaluate_ipd_dependencies(
                    repo, phase="pre-execution", **kwargs
                )
                hits = [d for d in drift if d.rule == DEP_RULE]
                problems = []
                if len(hits) != expected:
                    if expected:
                        refusing_rows_broken += 1
                    problems.append(
                        f"expected {expected} hit(s), got {len(hits)}: "
                        f"{[d.detail for d in hits]!r}"
                    )
                elif hits:
                    if loc == "dependent" and hits[0].location != str(dependent):
                        problems.append(
                            f"named {hits[0].location!r}; it must name the DEPENDENT "
                            f"{str(dependent)!r}, which is the plan that cannot proceed"
                        )
                    for needle in needles:
                        if needle not in hits[0].detail:
                            problems.append(
                                f"the detail does not mention {needle!r}; it said "
                                f"{hits[0].detail!r}"
                            )
                if problems:
                    wrong.append(
                        f"  {case}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
            finally:
                shutil.rmtree(repo, ignore_errors=True)
        vacuity = ""
        if refusing_rows_broken:
            vacuity = (
                f" {refusing_rows_broken} MUST-REFUSE row(s) failed, and while they are broken "
                "every exempt row here is VACUOUS: an evaluator that reports nothing satisfies all "
                "of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"the check-engine findings gate is wrong on {len(wrong)} of {len(self.EDGES)} edge/"
            f"action combinations.{vacuity} Read them together: if the `exists:` row started "
            "reporting, the gate spread from work edges to structural ones and will refuse plans "
            "that merely reference a target; if the REVIEW row started reporting, the measured "
            "2026-09-08 defect has regressed and review turns are refused over code they will not "
            "touch; if the UNMAPPED row went to 0, the action default turned FAIL-OPEN and every "
            "caller that omits `actions` now bypasses the gate entirely, which is the most "
            "dangerous single failure in this table. FIX: the exemption keys on the CONSUMING "
            "ACTION being `review`, and every other value, including absent, is strict.\n"
            + "\n".join(wrong),
        )

    def test_rule_id_is_registered_and_distinct_from_the_identity_verdicts(self):
        """Kept separate: claims about ONE registry object plus two id inequalities, not data rows.

        `dangling`/`ambiguous` are IDENTITY verdicts; reusing one here would state something false
        ("no artifact has that id6" / "several do") about a target that resolves perfectly well.
        """
        spec = ce.rule_spec(DEP_RULE)
        self.assertIn(DEP_RULE, ce.RULE_REGISTRY)
        self.assertIsNot(
            spec,
            ce._DEFAULT_RULESPEC,
            "an unregistered id silently falls back to the conservative default with an EMPTY "
            "invariant, leaving the finding unclassified",
        )
        self.assertEqual(spec.severity, "error")
        self.assertEqual(spec.determinism, ce.DET_DETERMINISTIC)
        self.assertNotEqual(DEP_RULE, "check.ipd-dependency-dangling")
        self.assertNotEqual(DEP_RULE, "check.ipd-dependency-ambiguous")


# --------------------------------------------------------------------------------------
# V-07: the `/exec-set` Set compiler (the THIRD authority surface)
# --------------------------------------------------------------------------------------


class SetCompilerGateTests(_RepoCase):
    """`resolve_set`: a findings-blocked child is a GATE, and the gate blocks its descendants.

    Three outcome tests became one table over the same Set fixture, with the finding's state and the
    threshold as columns. The rows assert the gate set, the blocked set, AND the gate reason together,
    because a gate whose reason does not name the finding is indistinguishable from the several OTHER
    reasons this compiler defers a child, and that ambiguity is what made the vacuity trap below
    possible.
    """

    def _set_fixture(self) -> Path:
        """Set `demo`: orchestrator + A(1) -> B(2) -> C(3), plus independent sibling D(4)."""
        plans = self.repo / ".aw" / "records" / "plans"
        orch = plans / "pending" / "20260829-demo-00-orch01-orchestrator.ipd.md"
        orch.write_text(
            "# IPD: orchestrator\n\n"
            "- Date: 2026-08-29\n- Kind: orchestrator\n- Scope-Paths: x.py\n"
            "- Item-Dependencies: none\n- Status: approved\n- Set: demo\n- Order: 0\n"
            "- Id: orch01\n\n## Workflow history\n- 2026-08-29 draft (t): created.\n\n"
            "## Goal\ng\n",
            encoding="utf-8",
        )
        for id6, order in (("aaa111", 1), ("bbb222", 2), ("ccc333", 3), ("ddd444", 4)):
            _plan(
                self.repo,
                id6,
                lane="pending",
                status="approved",
                order=order,
                set_id="demo",
            )
        return plans

    #: (case, decision, threshold, expected gates, expected blocked, reason needles, why)
    OUTCOMES = (
        (
            "an unresolved high finding on the first child",
            "open",
            "high",
            ("aaa111",),
            ("aaa111", "bbb222", "ccc333"),
            ("F-1",),
            "the findings-blocked child becomes a GATE and the serial-inference cascade blocks "
            "every descendant, with the reason naming the FINDING rather than an unexplained id",
        ),
        (
            "the same finding marked fixed",
            "fixed",
            "high",
            (),
            (),
            (),
            "the clean control, and the row that makes the one above non-vacuous: with the finding "
            "resolved there is NO gate at all, so the gate cannot be coming from the child's "
            "status or its position in the Set",
        ),
        (
            "an unresolved high finding at threshold off",
            "open",
            "off",
            (),
            (),
            (),
            "`off` must disable the gate on the Set compiler too; a surface that ignored the "
            "threshold would make the opt-out a partial fiction",
        ),
    )

    def test_a_findings_blocked_child_gates_its_descendants(self) -> None:
        wrong = []
        gating_rows_broken = 0
        for case, decision, threshold, gates, blocked, needles, why in self.OUTCOMES:
            plans = self._set_fixture()
            _set_threshold(self.repo, threshold)
            _review(
                self.repo,
                "aaa111",
                rounds=[rf.Round(1, (_finding(decision=decision),), ())],
            )
            inv = sp.resolve_set(plans, "demo")
            problems = []
            if tuple(inv.deferred_gates) != gates:
                if gates:
                    gating_rows_broken += 1
                problems.append(
                    f"deferred_gates={tuple(inv.deferred_gates)!r}, expected {gates!r}"
                )
            missing = [c for c in blocked if c not in inv.blocked_children]
            if missing:
                problems.append(
                    f"blocked_children is missing {missing!r}; it was "
                    f"{tuple(inv.blocked_children)!r}"
                )
            if not blocked and tuple(inv.blocked_children):
                problems.append(
                    f"blocked_children should be empty, was {tuple(inv.blocked_children)!r}"
                )
            for needle in needles:
                reason = inv.gate_reasons.get("aaa111", "")
                if needle not in reason:
                    problems.append(
                        f"the gate reason does not mention {needle!r}; it said {reason!r}, so an "
                        "operator cannot tell this gate from the other reasons a child defers"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
            # Each row needs a pristine Set: reset between rows rather than across tests.
            shutil.rmtree(self.repo, ignore_errors=True)
            self.repo = _mkrepo()
        vacuity = ""
        if gating_rows_broken:
            vacuity = (
                " The GATING row is among the failures, so the clean rows here are VACUOUS: a "
                "compiler that gates nothing satisfies them."
            )
        self.assertEqual(
            wrong,
            [],
            f"the Set compiler's findings gate is wrong on {len(wrong)} of {len(self.OUTCOMES)} "
            f"states.{vacuity} Read them together: if the gating row lost its DESCENDANTS but kept "
            "the gate, `_propagate_blocked` is no longer being applied and only the gated child "
            "waits while work downstream of it proceeds; if the gate itself vanished, this surface "
            "is no longer consulting the findings predicate at all and `/exec-set` is a bypass "
            "around a gate the runner and `aw check` both enforce; if the REASON stopped naming "
            "F-1, the gate is still right but is now indistinguishable from the several other "
            "reasons a child defers. FIX: this surface must call the same "
            "`subject_gating_blocks` predicate and feed its gate into the EXISTING cascade.\n"
            + "\n".join(wrong),
        )

    def test_independent_sibling_is_not_blocked_with_an_explicit_orchestrator_table(
        self,
    ):
        """Kept separate: needs the REAL orchestrator child-table, a materially different fixture.

        With the legacy fallback every child is serially chained to the previous one, so EVERY later
        sibling is a descendant of the gate and "independent sibling" is not expressible at all. The
        row above therefore cannot carry this claim. Asserted explicitly rather than skipped, since
        descendant-only blocking is the property that keeps this gate from being a Set-wide halt.
        """
        _set_threshold(self.repo, "high")
        plans = self._set_fixture()
        orch = plans / "pending" / "20260829-demo-00-orch01-orchestrator.ipd.md"
        orch.write_text(
            orch.read_text(encoding="utf-8")
            + "\n## Child IPDs, sequence, and dependencies\n\n"
            "| Order | File | Purpose | Depends on |\n|---|---|---|---|\n"
            "| 1 | a.ipd.md | a | none |\n"
            "| 2 | b.ipd.md | b | 1 |\n"
            "| 3 | c.ipd.md | c | 2 |\n"
            "| 4 | d.ipd.md | d | none |\n",
            encoding="utf-8",
        )
        _review(self.repo, "aaa111")
        inv = sp.resolve_set(plans, "demo")
        self.assertEqual(inv.cross_edges_source, "orchestrator-table")
        self.assertEqual(inv.deferred_gates, ("aaa111",))
        # The gate and its transitive descendants block...
        self.assertIn("aaa111", inv.blocked_children)
        self.assertIn("bbb222", inv.blocked_children)
        self.assertIn("ccc333", inv.blocked_children)
        # ...but the INDEPENDENT sibling does not.
        self.assertNotIn("ddd444", inv.blocked_children)

    def test_reuses_the_existing_propagate_blocked_cascade(self):
        """Kept separate: a source-level claim about the module's shape, not an outcome.

        One transitive rule in this module, not a second hand-written cascade.
        """
        src = _src(sp)
        self.assertEqual(src.count("def _propagate_blocked"), 1)
        self.assertIn("_propagate_blocked(child_ids, cross_edges, gates)", src)

    def test_manifest_carries_the_gate_reason(self):
        """Kept separate: asserts the reason survives THREE further renderings (manifest, JSON, human).

        The subject is the serialization chain rather than the gate decision, so merging it into the
        outcome table would conflate "the gate fired" with "the gate's reason is transported".
        """
        _set_threshold(self.repo, "high")
        plans = self._set_fixture()
        _review(self.repo, "aaa111")
        inv = sp.resolve_set(plans, "demo")
        manifest = sp.compile_manifest(inv, plans, base_head="deadbeef")
        self.assertIn("aaa111", manifest.deferred_gates)
        self.assertIn(
            "F-1", json.loads(sp.emit_manifest_json(manifest))["gate_reasons"]["aaa111"]
        )
        self.assertIn("F-1", sp.render_plan_only_human(manifest))


# --------------------------------------------------------------------------------------
# V-04 / V-08: the block names its cause and its exact recovery command
# --------------------------------------------------------------------------------------


class BlockLegibilityTests(_RepoCase):
    """The block must be LEGIBLE: it names its cause, its recovery, and keeps the old payload shape.

    The per-row reason content (finding id + severity) is asserted on EVERY blocking row of
    `RunnerBlockTests` via its `reason_needles` column, which is strictly more coverage than the single
    fixture the replaced `test_reason_map_names_the_finding_id_and_severity` used. What remains here is
    what that column cannot express: the generic-message REGRESSION (a reason that says only
    "dependency not satisfied" is the exact failure being fixed) and the ADDITIVE shape contract.
    """

    def test_the_reason_is_specific_and_the_flat_list_shape_is_unchanged(self) -> None:
        _set_threshold(self.repo, "high")
        _plan(self.repo, "depaaa")
        _review(self.repo, "depaaa")
        state = _state(self.repo, [_item("itemaa", ["depaaa"])])
        wrong = []
        for name, drv in DRIVERS:
            sat, missing, reasons = drv.dependency_status_detailed(
                state["queue"][0], state
            )
            why = reasons.get("depaaa", "")
            if sat:
                wrong.append(
                    f"  {name}: the edge was satisfied; this fixture must block"
                )
                continue
            if why.strip() == "dependency not satisfied":
                wrong.append(
                    f"  {name}: the reason is the GENERIC message, which is precisely the failure "
                    "mode E-04 exists to fix: an operator is told the edge failed but not why, so "
                    "there is no path from the block to the fix"
                )
            # E-04 is ADDITIVE: the flat list[str] must keep its shape for existing consumers.
            if not isinstance(missing, list) or not all(
                isinstance(x, str) for x in missing
            ):
                wrong.append(
                    f"  {name}: the flat unsatisfied list is {missing!r}; it must remain a "
                    "list[str], because the reasons map was added BESIDE it and every existing "
                    "consumer still reads the flat list"
                )
        self.assertEqual(
            wrong,
            [],
            "the dependency block is not legible on "
            f"{len(wrong)} of {len(DRIVERS)} hosts. A block whose cause is unnamed is a block an "
            "operator cannot clear, and a flat list that changed shape breaks every pre-existing "
            "consumer silently. FIX: the reasons map is ADDITIVE beside the flat list; do not "
            "replace one with the other.\n" + "\n".join(wrong),
        )

    def test_recovery_hint_and_report_name_the_actual_flag(self) -> None:
        """Kept separate: the report half builds a HAND-WRITTEN run state and writes a file.

        Merged into one test because the hint and the report are one claim with two renderings: the
        recovery must reach the run report an operator reads, not only `events.jsonl`. The setup is a
        full synthetic `dependency-blocked` state, which no fixture above produces.
        """
        wrong = []
        for name, drv in DRIVERS:
            hint = drv.DEPENDENCY_BLOCK_RECOVERY_HINT
            if "--retry-incomplete" not in hint or "bare" not in hint.lower():
                wrong.append(
                    f"  {name}: the recovery hint is {hint!r}; it must name the REAL "
                    "`--retry-incomplete` flag and say that a BARE resume does not re-queue, "
                    "because a block whose exit is undocumented is a usability failure"
                )
            run_dir = Path(tempfile.mkdtemp(prefix=f"aw_rep_{name}_"))
            try:
                state = {
                    "run_id": "run-x",
                    "repo": str(self.repo),
                    "created_at": "t",
                    "updated_at": "t",
                    "selectors": [],
                    "set_sessions": {},
                    "queue": [
                        {
                            "id6": "itemaa",
                            "position": 1,
                            "setid": "demo",
                            "action": "execute",
                            "status": "dependency-blocked",
                            "attempts": [],
                            "unsatisfied_dependencies": ["depaaa"],
                            "unsatisfied_dependency_reasons": {
                                "depaaa": "depaaa: review finding F-1 is high/open and unresolved"
                            },
                            "dependency_block_recovery": drv.DEPENDENCY_BLOCK_RECOVERY_HINT,
                        }
                    ],
                }
                drv.write_report(run_dir, state)
                text = (run_dir / "execution-report.md").read_text(encoding="utf-8")
                for needle in ("Dependency blocks (why)", "F-1", "--retry-incomplete"):
                    if needle not in text:
                        wrong.append(
                            f"  {name}: the run report does not contain {needle!r}, so the cause "
                            "or the recovery reaches events.jsonl but not the human-read report"
                        )
            finally:
                shutil.rmtree(run_dir, ignore_errors=True)
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} legibility check(s) failed across {len(DRIVERS)} hosts. FIX: the cause "
            "and the exact recovery command must appear in the run report, not only in the event "
            "stream.\n" + "\n".join(wrong),
        )


class RecoverySemanticsTests(unittest.TestCase):
    """V-08: the ACTUAL re-queue behavior, which is NOT automatic and was falsely claimed in the draft.

    Two tests became one table over the two hosts. These read the runner SOURCE deliberately: the claim
    is that the flag is LOAD-BEARING and that the default is UNCHANGED, and a behavioral test of "a
    bare resume does not re-queue" would pass vacuously against a runner that re-queues nothing at all.
    """

    #: (claim, required substrings, why)
    CLAIMS = (
        (
            "dependency-blocked re-queues only under the flag",
            ("if retry_incomplete:",),
            "the re-queue is GATED on the flag, which is what makes `--retry-incomplete` "
            "load-bearing rather than decorative",
        ),
        (
            "start still passes retry_incomplete=False",
            ("retry_incomplete=False",),
            "the DEFAULT is unchanged by this plan: a run that silently re-queued blocked items "
            "would re-attempt work against a prerequisite whose finding is still unresolved",
        ),
        (
            "the flag exists on resume",
            ("--retry-incomplete",),
            "the documented exit must actually be a real flag; a recovery hint naming a "
            "nonexistent flag is worse than none",
        ),
    )

    def test_the_retry_flag_is_load_bearing_on_both_hosts(self) -> None:
        wrong = []
        for claim, required, why in self.CLAIMS:
            for name, drv in DRIVERS:
                src = _src(drv)
                missing = [s for s in required if s not in src]
                if missing:
                    wrong.append(
                        f"  {name}: {claim}: source no longer contains {missing!r}\n"
                        f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} recovery-semantics claim(s) failed. Read them together: if the same "
            "claim failed on BOTH hosts, the recovery contract changed deliberately and these rows "
            "need updating with it; if ONE host failed, the hosts have diverged on recovery, so an "
            "operator's documented escape works on one host and not the other. FIX: if "
            "`retry_incomplete=False` is gone from `start`, a run now re-queues blocked items by "
            "default, which re-attempts work whose prerequisite is still unresolved.\n"
            + "\n".join(wrong),
        )


# --------------------------------------------------------------------------------------
# V-06: cross-surface non-evasion. ONE fixture, EVERY authority surface.
# --------------------------------------------------------------------------------------


class CrossSurfaceNonEvasionTests(_RepoCase):
    """A gate proven on three of four surfaces is a gate with an undocumented bypass.

    This enumerates every surface that grants execution authority and asserts each REFUSES the same
    fixture, then that each RELEASES it once the finding is `fixed`. Two tests became one table whose
    column is the finding's state, because the two directions are one claim: a surface that refuses
    everything is as broken as one that refuses nothing, and only the pair is evidence. The surface
    list is the value here - a future contributor who adds a fifth surface has a single place that
    fails.

    A NOTE ON WHY SURFACE 4 NEEDS ITS OWN CHILD STATUS, recorded because it is a vacuity trap and not
    a detail. The runner and `aw check` surfaces only reach the findings check for a target that is
    ALREADY `executed` (that is what an `executed:` edge asserts). But the Set compiler's
    `RUNNABLE_STATUSES` is `{approved, auto-approved}`, so an `executed` child is ALREADY a gate for a
    PRE-EXISTING reason that has nothing to do with findings. Asserting "the executed child is in
    blocked_children" would therefore pass with this plan's code REVERTED. Surface 4 is consequently
    exercised on a SEPARATE Set whose gated child is `approved`, where the ONLY possible gate cause is
    the finding, and the row additionally requires `gate_reasons` to name the FINDING rather than the
    status. `test_surface_4_control_would_not_gate_without_the_finding` is the explicit control.
    """

    SURFACES = ("oc.dependency_status", "agy.dependency_status", "aw check", "exec-set")

    #: (case, decision, must every surface refuse?, why)
    STATES = (
        (
            "an unresolved high/open finding",
            "open",
            True,
            "EVERY authority surface must refuse the SAME fixture. A surface that lets it through "
            "is an undocumented bypass, and an operator who finds it has a legitimate route around "
            "a gate the other three enforce",
        ),
        (
            "the same finding marked fixed",
            "fixed",
            False,
            "and every surface must RELEASE it once resolved. Without this direction a surface "
            "that refused unconditionally would satisfy the row above while making the gate "
            "unclearable, which is the failure mode that strands work permanently",
        ),
    )

    def _build(self, decision: str) -> dict[str, bool]:
        """Build the fixture at one finding state and ask every authority surface."""
        _set_threshold(self.repo, "high")
        plans = self.repo / ".aw" / "records" / "plans"
        rounds = [rf.Round(1, (_finding(decision=decision),), ())]

        # Surfaces 1-3 run on Set `demo`: an executed/ target carrying the finding.
        _plan(self.repo, "aaa111")
        _review(self.repo, "aaa111", rounds=rounds)
        _plan(
            self.repo,
            "bbb222",
            lane="pending",
            status="approved",
            order=2,
            deps="executed:aaa111",
        )
        # Surface 4 runs on Set `other`: APPROVED children, so the finding is the only gate cause.
        for id6, order in (("eee555", 1), ("fff666", 2)):
            _plan(
                self.repo,
                id6,
                lane="pending",
                status="approved",
                order=order,
                set_id="other",
            )
        _review(self.repo, "eee555", rounds=rounds)

        state = _state(self.repo, [_item("bbb222", ["aaa111"])])
        refused = {}
        for name, drv in DRIVERS:
            satisfied, _ = drv.dependency_status(state["queue"][0], state)
            refused[f"{name}.dependency_status"] = not satisfied
        drift = ce.evaluate_ipd_dependencies(self.repo, phase="pre-execution")
        refused["aw check"] = any(d.rule == DEP_RULE for d in drift)
        inv = sp.resolve_set(plans, "other")
        refused["exec-set"] = (
            "eee555" in inv.blocked_children
            and "fff666" in inv.blocked_children
            and "F-1" in inv.gate_reasons.get("eee555", "")
        )
        return refused

    def test_every_authority_surface_agrees_on_the_same_fixture(self) -> None:
        wrong = []
        for case, decision, must_refuse, why in self.STATES:
            refused = self._build(decision)
            disagreeing = [
                s for s, r in sorted(refused.items()) if r is not must_refuse
            ]
            if disagreeing:
                wrong.append(
                    f"  {case}: expected every surface to "
                    f"{'REFUSE' if must_refuse else 'ALLOW'}, but "
                    f"{disagreeing!r} did not (full verdicts: {refused!r})\n"
                    f"    this row exists because: {why}"
                )
            shutil.rmtree(self.repo, ignore_errors=True)
            self.repo = _mkrepo()
        self.assertEqual(
            wrong,
            [],
            f"the authority surfaces disagree in {len(wrong)} of {len(self.STATES)} states. The "
            f"surfaces are {self.SURFACES!r}. Read them together: if ALL FOUR moved, the shared "
            "`subject_gating_blocks` predicate changed and the whole gate moved with it (which may "
            "be intended, but every row here must then be re-decided); if ONE moved, that surface "
            "was unwired and is now a BYPASS around a gate the other three still enforce, which "
            "is the specific hazard this test exists to detect. FIX: fix the surface, not the "
            "table; and if you added a FIFTH authority surface, add it to `_build` so it can never "
            "be the silent one.\n" + "\n".join(wrong),
        )

    def test_surface_4_control_would_not_gate_without_the_finding(self):
        """Kept separate: the CONTROL that proves the surface-4 row above is not vacuous.

        Same Set, same `approved` statuses, finding FIXED -> no gate at all. Without this control,
        the surface-4 assertion could pass for the pre-existing unapproved-status reason and silently
        stop testing this plan's change.
        """
        _set_threshold(self.repo, "high")
        for id6, order in (("eee555", 1), ("fff666", 2)):
            _plan(
                self.repo,
                id6,
                lane="pending",
                status="approved",
                order=order,
                set_id="other",
            )
        _review(
            self.repo, "eee555", rounds=[rf.Round(1, (_finding(decision="fixed"),), ())]
        )
        inv = sp.resolve_set(self.repo / ".aw" / "records" / "plans", "other")
        self.assertEqual(
            inv.deferred_gates,
            (),
            "with the finding fixed these approved children must NOT be gated; if they are, the "
            "surface-4 assertion is passing for a reason other than the finding",
        )
        self.assertEqual(inv.blocked_children, ())


if __name__ == "__main__":
    unittest.main()
