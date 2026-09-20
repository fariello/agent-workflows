"""Tests for the local pre-commit executed-transition gate (ipdgates Order dulzpy).

The hook (agent_workflows.hooks.executed_transition_gate) refuses a raw (non-finalize) plan->executed
commit: a plan that gains `- Status: executed`/`done` or is `git mv`-ed into executed/ with NO matching
finalize journal in .aw/state/ is REFUSED; finalize's own commit (which leaves a finalize journal at
ready-to-commit) PASSES; prompts/non-plan/ordinary commits are not gated. LOCAL best-effort only.

integpath 29wvmj adds the MERGE-AWARE second accepting path and its tests
(`MergeAwareInTreeEvidenceTests` below): during a merge, an incoming-side `lifecycle(<id6>): finalize`
commit is accepted as proof finalize performed the transition, because the journal lives under
gitignored `.aw/state/` and cannot travel with a lane branch. Those tests drive REAL git merges rather
than mocking `MERGE_HEAD`, since the defect being fixed is precisely that real merge state was never read.

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: build a git repo, stage
exactly one kind of change, call `GATE.check`, assert an exit code and one message needle. That is a
(staged situation -> verdict + reason) table, which is the natural shape for a GATE.

THIS IS A SAFETY GATE, SO THE TABLES ARE HELD TO THREE RULES STRICTER THAN THE FILE THEY REPLACE.
FIRST, EVERY DISTINCT REFUSAL REASON KEEPS ITS OWN ROW asserting the SPECIFIC wording reported, never
merely that something was refused: the four reasons this gate can give (`gained '- Status: executed'`,
`moved into executed/`, `no readable '- Id:'`, and the merge-case `this merge carries ... has NO
'lifecycle(<id6>): finalize' commit`) are what tell an operator which remedy applies, and a gate that
collapsed them to one message would satisfy a rc-only assertion while becoming unactionable. Three of
the replaced tests asserted the exit code ALONE, so a refusal naming the wrong plan, or giving the
merge wording outside a merge, would have passed; every row now pins its needle.
SECOND, THE ACCEPTING ROWS SIT IN THE SAME TABLE AS THE REFUSING ONES. A gate that refused
everything satisfies every refusal row on its own while making commits impossible, and one that
accepted everything satisfies every clean row while being the bypass this hook exists to close. Only
adjacency states both halves, and the failure messages say which way the gate broke.
THIRD, EVERY ROW ASSERTS THE GATE MUTATED NOTHING. This is a pre-commit INSPECTOR: it may not move a
plan, rewrite one, or restage anything. The replaced tests never checked, so a "refusal" that had
already completed the transition it was refusing would have passed. Each row snapshots the records
tree plus `git status --porcelain` before the call and requires them byte-identical after, which is
what makes "the plan was NOT moved" a checked claim rather than an assumption.

MODE DISTINCTIONS ARE COLUMNS. The finalize journal's PHASE and its recorded DESTINATION were a test
each; both are now columns on one table, because the property worth stating is that the SAME staged
transition is accepted or refused according to the journal it is paired with, which no single-journal
test can express. Likewise the git HOOK STAGE (`pre-commit` versus `pre-merge-commit`) and whether a
lane carries finalize's own commit are columns on the end-to-end table.

Tests that are NOT rows carry a one-line docstring saying why they stay separate.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_lifecycle as LC
from agent_workflows.hooks import executed_transition_gate as GATE

import tests.test_ipd_lifecycle_cli as LT  # reuse the plan fixtures

#: The subject `aw ipd finalize` itself writes, spelled LITERALLY rather than read back from
#: `artifact_core.finalize_commit_subject`. The gate MATCHES on this string and its refusal QUOTES it
#: back to the operator, so it is a published grammar: referencing the producer's own helper would
#: make both sides move together and a change of subject form invisible here. Do not "tidy" this into
#: a call.
FINALIZE_SUBJECT = "lifecycle({id6}): finalize {id6} -> executed"

#: The exact reason fragments the gate reports, one per distinct refusal cause. Literal for the same
#: reason as above: these are operator-facing wording, not internal constants.
REASON_STATUS_FLIP = "gained '- Status: executed'"
REASON_MOVED = "moved into executed/"
REASON_NO_ID = "no readable"
NON_MERGE_WORDING = "NO matching finalize evidence in .aw/state/"
MERGE_WORDING = "this merge carries"


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")


def _commit_all(root: Path, msg: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=root, check=True)


def _stage(root: Path) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)


def _porcelain(root: Path) -> str:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def _snapshot(root: Path) -> tuple[str, dict]:
    """The gate's whole observable surface: the staged/worktree status plus every record's bytes.

    Taken before and after every `check` call. A gate that MOVED the plan it was refusing, or
    restaged anything, changes one of these; nothing legitimate the gate does changes either.
    """

    records = root / ".aw" / "records"
    files = {}
    if records.is_dir():
        for path in sorted(records.rglob("*")):
            if path.is_file():
                files[str(path.relative_to(root))] = path.read_bytes()
    return _porcelain(root), files


class PreCommitExecutedGateTests(unittest.TestCase):
    """Which staged situations the gate passes, which it refuses, and with WHICH reason.

    ONE table replaces nine tests spread over three comment-delimited groups (`no-op / negative`,
    `refusal (raw bypass)`, and the journal cases). All nine wrote a git repository, staged one change,
    called `GATE.check(root)` and asserted an exit code, so the SITUATION is the data and the verdict
    is the answer.

    THE JOURNAL IS TWO COLUMNS (phase, destination) AND THAT IS MOST OF THE REDUCTION. Three of the
    replaced tests differed only in which journal accompanied an identical staged transition: one
    matching at `ready-to-commit` (accept), one whose `dest_path` named a different plan (refuse), one
    at `prepared` (refuse). The predicate under test is precisely "is THIS journal evidence for THIS
    transition", which is a claim about the PAIR, so the pair belongs on one row and the set of pairs
    belongs in one table. The two accepted non-`ready-to-commit` phases are ALSO rows now, which the
    replaced tests never covered: the accepting set is `ready-to-commit`, `committed-incomplete` and
    `complete`, and a gate that accepted only the first would have passed the old suite while refusing
    every commit made after finalize's own.

    Why the table beats the nine: ONE predicate chain decides every row (is this a plan path, did it
    gain executed status or move into executed/, is there journal evidence, is a merge in progress), so
    the realistic regression breaks several rows at once in a pattern that IS the diagnosis. Nine tests
    report that as nine unrelated `1 != 0` lines; the table reports one failure naming every row that
    moved and says what the grouping means.

    THE THREE NON-GATED ROWS ARE LOAD-BEARING, not filler. The ordinary-file row and the
    still-pending-plan row prove the gate is a NARROW discriminator rather than a blanket refusal of
    commits, and the PROMPT row proves the record-type discriminator holds: a prompt legitimately
    carries `- Status: executed`, so a gate keyed on the status line alone rather than on the plan path
    would block a whole other record type's normal lifecycle.
    """

    #: (case, mutate(self) -> None staging the situation, journal as (phase, dest) or None, expected
    #: exit code, message substrings that must ALL appear, substrings that must appear in NO message,
    #: why this row exists)
    #:
    #: `dest` is "matching" (the journal names the staged executed path) or "other" (it names a
    #: different plan's path), which is how the bind-to-THIS-transition property is expressed as data.
    SITUATIONS = (
        (
            "an ordinary commit touching no plan at all",
            lambda self: self._write_other_file(),
            None,
            0,
            (),
            (),
            "THE FAST NO-OP, and the first of the three rows that stop this gate being a blanket "
            "refusal: the overwhelming majority of commits in this repository touch no plan, so a "
            "gate that spoke up here would make every commit require a bypass and `--no-verify` would "
            "become reflex, which is exactly the habit this hook exists to remove",
        ),
        (
            "a plan edited but left PENDING",
            lambda self: self._edit_plan_keeping_pending(),
            None,
            0,
            (),
            (),
            "TOUCHING a plan is not TRANSITIONING one. Plans are edited constantly while they are "
            "authored and reviewed, and only the executed transition runs gates, so a gate keyed on "
            "'a plan file changed' would block ordinary authoring",
        ),
        (
            "a PROMPT record gaining `- Status: executed`",
            lambda self: self._write_executed_prompt(),
            None,
            0,
            (),
            (),
            "THE RECORD-TYPE DISCRIMINATOR. Prompts have their own lifecycle and legitimately reach "
            "`executed` with no IPD finalize anywhere, so a gate matching the STATUS LINE rather than "
            "the `.aw/records/plans/**.ipd.md` PATH would refuse a different record type's normal "
            "work. This row is what pins the discrimination to the path",
        ),
        (
            "a hand-edited `- Status: executed` in place, no journal",
            lambda self: self._flip_status_in_place(),
            None,
            1,
            ("abc123", "aw ipd finalize", REASON_STATUS_FLIP, NON_MERGE_WORDING),
            (MERGE_WORDING,),
            "THE p7dqwz-CLASS BYPASS THIS HOOK EXISTS FOR: an agent edits the status in an editor and "
            "commits, so no receipt, no scope check and no attribution ever run. The reason needle is "
            "asserted because the STATUS-FLIP and MOVED reasons carry different remedies, and the "
            "plan id is asserted because a refusal that does not name WHICH plan is unactionable in a "
            "commit touching several",
        ),
        (
            "a `git mv` into executed/, no journal",
            lambda self: self._move_into_executed(),
            None,
            1,
            ("abc123", "aw ipd finalize", REASON_MOVED, NON_MERGE_WORDING),
            (MERGE_WORDING,),
            "THE SECOND SPELLING of the same bypass, and it must be detected by a DIFFERENT branch: "
            "the status flip is found by diffing staged content against HEAD, while this is found "
            "from the rename's destination directory. A refactor can easily keep one and lose the "
            "other, and this row plus the one above is what localises which",
        ),
        (
            "a grandfathered plan moved into executed/, no journal",
            lambda self: self._move_into_executed(plan_id="gf1234"),
            None,
            1,
            ("gf1234", "aw ipd finalize", REASON_MOVED),
            (),
            "OQ-01 OPTION B, a POLICY row rather than a mechanism one: being grandfathered exempts a "
            "plan from the `Scope-Paths` ALLOWLIST, not from having run finalize. A reading where "
            "grandfathered means 'ungated' would leave the oldest and least reviewed plans as the one "
            "open door, so this row states the exemption does not extend here",
        ),
        (
            "the same transition WITH finalize's journal at ready-to-commit",
            lambda self: self._move_into_executed(),
            ("ready-to-commit", "matching"),
            0,
            (),
            (),
            "THE POSITIVE ROW, and every refusal row above is vacuous while it is broken: this is "
            "exactly finalize's OWN commit state, so a gate that refused here would make `aw ipd "
            "finalize` unable to commit its own work and the only way to execute a plan would be to "
            "bypass the gate",
        ),
        (
            "the same transition with a journal at committed-incomplete",
            lambda self: self._move_into_executed(),
            ("committed-incomplete", "matching"),
            0,
            (),
            (),
            "THE PHASE IS A COLUMN, and this row was NOT covered before. The accepting set is all "
            "three finalize-transaction phases, because a journal outlives finalize's own commit and "
            "a follow-up commit in the same transaction must not be refused. A gate hardcoded to "
            "`ready-to-commit` passes the row above and fails here",
        ),
        (
            "the same transition with a journal at complete",
            lambda self: self._move_into_executed(),
            ("complete", "matching"),
            0,
            (),
            (),
            "the third accepting phase, for the same reason: the transaction is finished but the "
            "journal is still the durable proof that finalize performed this transition",
        ),
        (
            "a journal at `prepared`, a NON-finalize-transaction phase",
            lambda self: self._move_into_executed(),
            ("prepared", "matching"),
            1,
            ("abc123", "aw ipd finalize", REASON_MOVED),
            (),
            "`prepared` means the journal was written and NOTHING has been mutated yet, so it proves "
            "finalize STARTED, not that it performed the transition. Accepting it would let an "
            "abandoned or rolled-back finalize authorize a hand-completed transition, which is the "
            "bypass with one extra step",
        ),
        (
            "a journal whose dest_path names a DIFFERENT plan",
            lambda self: self._move_into_executed(),
            ("ready-to-commit", "other"),
            1,
            ("abc123", "aw ipd finalize", REASON_MOVED),
            (),
            "THE EVIDENCE IS TRANSITION-BOUND. One finalize leaves one journal, and a stale journal "
            "from a previous plan is a normal thing to find on disk, so a predicate keyed on 'a "
            "journal exists for this id' would let yesterday's finalize authorize today's hand-edit. "
            "Binding to `dest_path` is what makes the journal evidence for THIS transition",
        ),
        # ---------------------------------------------------------------- gatejrnl i4c0c3
        # FOUR ROWS ABOUT ONE DISCRIMINATION: "did this plan ENTER executed/ in this commit" versus
        # "was it merely EDITED while already there". They belong in THIS table rather than in a class
        # of their own precisely because the bug they pin was a bug IN the predicate every row above
        # shares: an ALREADY-executed plan is a situation, and its verdict is the answer.
        (
            "a BODY-ONLY edit to a plan already committed in executed/",
            lambda self: self._edit_already_executed_plan("body"),
            None,
            0,
            (),
            (),
            "THE FALSE POSITIVE i4c0c3 FIXES, and the reason it was expensive rather than merely "
            "annoying: a plan that has sat in executed/ for weeks was classified as TRANSITIONING by "
            "every commit that touched it, no finalize journal can exist for a transition that is not "
            "happening, so the only remedy an operator had was `--no-verify`. A gate that refuses "
            "correct behavior teaches the bypass it exists to prevent, which is worse than no gate",
        ),
        (
            "an edit to an already-executed plan's `## Workflow history`",
            lambda self: self._edit_already_executed_plan("history"),
            None,
            0,
            (),
            (),
            "THE SHAPE THE DEFECT ACTUALLY TOOK IN THE FIELD. A correction to a finalized plan "
            "appends to its history rather than rewriting its body, and it is kept as a SEPARATE row "
            "from the body edit because the history block is where the `- Status:` line's neighbours "
            "live: an implementation discriminating on WHICH REGION of the plan changed would pass "
            "the body row and fail here",
        ),
        (
            "a WHOLESALE content substitution (different `- Id:`) at an already-executed path",
            lambda self: self._substitute_plan_at_executed_path(),
            None,
            1,
            ("zzz999", "aw ipd finalize", REASON_MOVED),
            (MERGE_WORDING,),
            "THE HOLE THE PATH-ONLY FIX WOULD HAVE OPENED (MEASURED: rc 0 without the id binding, rc "
            "1 with it). Exempting an edit because THE PATH held an executed plan makes an executed "
            "FILENAME a shelter: overwrite it with a different plan and a raw plan->executed "
            "transition commits unchallenged. The exemption is therefore bound to the plan's IDENTITY, "
            "and this row is what stops a future simplification dropping that clause as redundant",
        ),
        (
            "a plan ALREADY IN executed/ at HEAD but NOT yet executed, flipped in place",
            lambda self: self._flip_status_inside_executed(),
            None,
            1,
            ("abc123", "aw ipd finalize", REASON_STATUS_FLIP),
            (MERGE_WORDING,),
            "THE ROW THAT PROVES THE EXEMPTION IS ABOUT THE TRANSITION AND NOT ABOUT THE DIRECTORY. "
            "Being in executed/ is not being EXECUTED, so the status flip must still refuse here, and "
            "it refuses through `gained_executed` rather than the path predicate. That only works "
            "because i4c0c3 also repaired `head_text`: while it was read at the rename SOURCE alone "
            "it was None for every `M`, so `gained_executed` compared against NOTHING and was "
            "vacuously true for every executed plan, which IS the false positive above",
        ),
    )

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir()
        (self.root / "tests").mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # --- fixture helpers, each of which STAGES the situation it builds ---
    def _write_plan(
        self, plan_id: str, scope_paths: str = "grandfathered", name=None
    ) -> Path:
        name = name or f"20260824-demo-01-{plan_id}-demo.ipd.md"
        d = self.root / ".aw" / "records" / "plans" / "pending"
        d.mkdir(parents=True, exist_ok=True)
        p = d / name
        p.write_text(
            LT._completed_plan_text(plan_id=plan_id, scope_paths=scope_paths),
            encoding="utf-8",
        )
        return p

    def _executed_dir(self) -> Path:
        d = self.root / ".aw" / "records" / "plans" / "executed"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _write_other_file(self) -> None:
        (self.root / "somefile.txt").write_text("hi\n", encoding="utf-8")
        _stage(self.root)

    def _edit_plan_keeping_pending(self) -> None:
        p = self._write_plan("abc123")
        _commit_all(self.root, "add plan")
        p.write_text(p.read_text() + "\n<!-- edit -->\n", encoding="utf-8")
        _stage(self.root)

    def _write_executed_prompt(self) -> None:
        pdir = self.root / ".aw" / "records" / "prompts" / "executed"
        pdir.mkdir(parents=True)
        (pdir / "20260824-p-01-pr0mp7-x.prompt.md").write_text(
            "# Prompt\n\n- Status: executed\n- Id: pr0mp7\n\nbody\n", encoding="utf-8"
        )
        _stage(self.root)

    def _flip_status_in_place(self, plan_id: str = "abc123") -> None:
        p = self._write_plan(plan_id)
        _commit_all(self.root, "add plan (approved)")
        p.write_text(
            p.read_text().replace("- Status: approved", "- Status: executed"),
            encoding="utf-8",
        )
        _stage(self.root)
        self._staged_plan_name = p.name
        self._staged_plan_id = plan_id

    def _move_into_executed(self, plan_id: str = "abc123") -> None:
        p = self._write_plan(plan_id)
        _commit_all(self.root, "add plan")
        text = p.read_text().replace("- Status: approved", "- Status: executed")
        (self._executed_dir() / p.name).write_text(text, encoding="utf-8")
        p.unlink()
        _stage(self.root)
        self._staged_plan_name = p.name
        self._staged_plan_id = plan_id

    def _commit_plan_already_executed(self, plan_id: str = "abc123") -> Path:
        """A plan COMMITTED in executed/ with `- Status: executed`, i.e. a finished transition at HEAD.

        The commit is the point. `LT._completed_plan_text` yields `- Status: approved`, so a fixture
        that wrote the plan into executed/ and staged it WITHOUT committing would make its own setup
        the transition under test, and a row built on it would prove nothing about a FOLLOW-UP edit.
        """
        p = self._write_plan(plan_id)
        dest = self._executed_dir() / p.name
        dest.write_text(
            p.read_text().replace("- Status: approved", "- Status: executed"),
            encoding="utf-8",
        )
        p.unlink()
        _commit_all(self.root, f"plan {plan_id} already finalized in executed/")
        self._staged_plan_name = dest.name
        self._staged_plan_id = plan_id
        return dest

    def _edit_already_executed_plan(self, where: str) -> None:
        dest = self._commit_plan_already_executed()
        text = dest.read_text(encoding="utf-8")
        if where == "history":
            self.assertIn(
                "## Workflow history",
                text,
                "fixture precondition: the shared plan text must carry a history section to append to",
            )
            text = text.replace(
                "## Workflow history\n",
                "## Workflow history\n- 2026-09-09 note (test): a correction after execution.\n",
                1,
            )
        else:
            text = text + "\nan ordinary follow-up edit to the body\n"
        dest.write_text(text, encoding="utf-8")
        _stage(self.root)

    def _substitute_plan_at_executed_path(self) -> None:
        """Overwrite an already-executed plan's file with a DIFFERENT plan, still claiming executed."""
        dest = self._commit_plan_already_executed()
        dest.write_text(
            LT._completed_plan_text(
                plan_id="zzz999", scope_paths="grandfathered"
            ).replace("- Status: approved", "- Status: executed"),
            encoding="utf-8",
        )
        _stage(self.root)
        self._staged_plan_id = "zzz999"

    def _flip_status_inside_executed(self, plan_id: str = "abc123") -> None:
        """A plan sitting IN executed/ at HEAD with a NON-executed status, flipped in place."""
        p = self._write_plan(plan_id)
        dest = self._executed_dir() / p.name
        dest.write_text(p.read_text(), encoding="utf-8")  # keeps `- Status: approved`
        p.unlink()
        _commit_all(self.root, f"plan {plan_id} in executed/ but NOT yet executed")
        self.assertIn(
            "- Status: approved",
            dest.read_text(encoding="utf-8"),
            "fixture precondition: HEAD must NOT already carry the executed status here",
        )
        dest.write_text(
            dest.read_text(encoding="utf-8").replace(
                "- Status: approved", "- Status: executed"
            ),
            encoding="utf-8",
        )
        _stage(self.root)
        self._staged_plan_name = dest.name
        self._staged_plan_id = plan_id

    def _write_journal(self, phase: str, dest: str) -> None:
        name = self._staged_plan_name
        dest_path = (
            ".aw/records/plans/executed/" + name
            if dest == "matching"
            else ".aw/records/plans/executed/SOME-OTHER-plan.ipd.md"
        )
        LC._write_finalize_journal(
            self.root,
            {
                "schema_version": 1,
                "plan_id": self._staged_plan_id,
                "original_path": ".aw/records/plans/pending/" + name,
                "dest_path": dest_path,
                "phase": phase,
            },
        )

    def test_each_staged_situation_gets_its_own_verdict_and_reason(self):
        wrong = []
        for case, mutate, journal, want_rc, needles, forbidden, why in self.SITUATIONS:
            with self.subTest(case=case):
                self.setUp()
                problems = []
                try:
                    self._staged_plan_name = None
                    self._staged_plan_id = None
                    mutate(self)
                    if journal is not None:
                        self._write_journal(*journal)
                    before = _snapshot(self.root)
                    rc, msgs = GATE.check(self.root)
                    after = _snapshot(self.root)
                    if rc != want_rc:
                        problems.append(
                            f"expected exit code {want_rc}, got {rc} with messages {msgs!r}"
                        )
                    if want_rc == 0 and msgs:
                        problems.append(
                            f"an accepted situation must report NOTHING, got {msgs!r}"
                        )
                    joined = " ".join(msgs)
                    missing = [n for n in needles if n not in joined]
                    if missing:
                        problems.append(
                            f"the refusal must state {missing!r}; it said {joined!r}"
                        )
                    leaked = [f for f in forbidden if f in joined]
                    if leaked:
                        problems.append(
                            f"the refusal must NOT contain {leaked!r} (wrong wording for this "
                            f"situation); it said {joined!r}"
                        )
                    if after[0] != before[0]:
                        problems.append(
                            "THE GATE CHANGED `git status`: it is an inspector and must stage, "
                            f"unstage and move nothing. before={before[0]!r} after={after[0]!r}"
                        )
                    if after[1] != before[1]:
                        moved = sorted(set(before[1]) ^ set(after[1]))
                        problems.append(
                            "THE GATE MUTATED THE RECORDS TREE, so the plan did not stay where the "
                            f"commit had put it; paths that appeared or vanished: {moved!r}"
                        )
                finally:
                    self._tmp.cleanup()
                if problems:
                    wrong.append(
                        f"  {case}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"the gate misjudged {len(wrong)} of {len(self.SITUATIONS)} staged situations. ONE "
            "predicate chain decides all of them, so READ THE GROUPING. If every REFUSAL row now "
            "passes, the gate is off and the raw hand-edit path to `executed` is open again, which is "
            "the single failure this hook exists to prevent. If every ACCEPTING row now refuses, the "
            "gate is a blanket refusal: `aw ipd finalize` cannot commit its own work and operators "
            "will reach for `--no-verify`, which is worse than no gate. If only the three journal "
            "PHASE rows disagree, the accepting phase set changed. If only the `dest_path` row "
            "passes, the evidence stopped binding to THIS transition and any stale journal now "
            "authorizes any transition. If a row failed on WORDING alone the gate still refused, but "
            "unactionably, since the reason is what tells an operator which remedy applies. FIX: a "
            "mutation failure is the most serious kind here and outranks the rest, because a gate "
            "that has already performed the transition it reports refusing is not a gate.\n"
            + "\n".join(wrong),
        )

    def test_real_finalize_own_commit_passes_via_installed_hook(self):
        """Not a row: this runs the REAL `LC.begin`+`LC.finalize` through an installed git hook, so
        its subject is the whole lifecycle rather than a staged situation the table can describe."""
        p = self._write_plan("abc123", scope_paths="grandfathered")
        _commit_all(self.root, "init")
        # Install the real hook and run begin+finalize; finalize's own commit must pass.
        hooks_dir = self.root / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        (hooks_dir / "pre-commit").write_text(
            "#!/bin/bash\nexec python3 -m agent_workflows ipd-executed-gate\n",
            encoding="utf-8",
        )
        (hooks_dir / "pre-commit").chmod(0o755)
        LC.begin(self.root, p, "opencode/test", timestamp="t")
        result = LC.finalize(self.root, p, "opencode/test", "dogfood", apply=True)
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        self.assertTrue((self._executed_dir() / p.name).is_file())


class MergeAwareInTreeEvidenceTests(unittest.TestCase):
    """The merge-aware in-tree evidence path (integpath 29wvmj, E-01..E-06).

    Every case here performs a REAL git merge. Nothing mocks `MERGE_HEAD`, because the defect this
    fixes is that real merge state was never consulted, so a mocked fixture would pass against the
    very bug it is meant to detect.

    THREE TABLES replace fourteen tests, split by SUBJECT rather than by scenario: what the merge
    DETECTOR reports, what `check` decides given a merge state, and what git ACTUALLY does with the
    hook installed. The split is deliberate and is not a failure to consolidate further: the detector
    rows assert a list of shas, the decision rows assert an exit code plus wording, and the
    end-to-end rows assert a subprocess's exit status and output, which are three different claims.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._git("init", "-q", ".")
        self._git("config", "user.email", "t@e.com")
        self._git("config", "user.name", "T")
        (self.root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
        self._write_plan_at("pending", "abc123", status="approved")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "base")
        self.base_branch = self._out("rev-parse", "--abbrev-ref", "HEAD")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # --- helpers ---
    def _git(self, *args: str, cwd: Path | None = None) -> None:
        subprocess.run(["git", *args], cwd=str(cwd or self.root), check=True)

    def _out(self, *args: str, cwd: Path | None = None) -> str:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd or self.root),
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout.strip()

    def _plan_name(self, id6: str) -> str:
        return f"20260824-demo-01-{id6}-demo.ipd.md"

    def _write_plan_at(self, bucket: str, id6: str, status: str = "approved") -> Path:
        d = self.root / ".aw" / "records" / "plans" / bucket
        d.mkdir(parents=True, exist_ok=True)
        p = d / self._plan_name(id6)
        text = LT._completed_plan_text(plan_id=id6, scope_paths="grandfathered")
        if status != "approved":
            text = text.replace("- Status: approved", f"- Status: {status}")
        p.write_text(text, encoding="utf-8")
        return p

    def _make_lane(
        self,
        id6: str,
        *,
        finalize_commit: bool,
        branch: str | None = None,
        strip_id: bool = False,
    ) -> str:
        """A lane branch that carries ``id6`` into executed/; optionally with finalize's own subject."""
        branch = branch or f"lane-{id6}"
        self._git("checkout", "-q", "-b", branch, self.base_branch)
        pending = (
            self.root / ".aw" / "records" / "plans" / "pending" / self._plan_name(id6)
        )
        if not pending.is_file():
            self._write_plan_at("pending", id6, status="approved")
            self._git("add", "-A")
            self._git("commit", "-q", "-m", f"add plan {id6}")
        dest_dir = self.root / ".aw" / "records" / "plans" / "executed"
        dest_dir.mkdir(parents=True, exist_ok=True)
        self._git(
            "mv",
            f".aw/records/plans/pending/{self._plan_name(id6)}",
            f".aw/records/plans/executed/{self._plan_name(id6)}",
        )
        dest = dest_dir / self._plan_name(id6)
        text = dest.read_text(encoding="utf-8").replace(
            "- Status: approved", "- Status: executed"
        )
        if strip_id:
            text = (
                "\n".join(
                    line for line in text.splitlines() if not line.startswith("- Id:")
                )
                + "\n"
            )
        dest.write_text(text, encoding="utf-8")
        self._git("add", "-A")
        subject = (
            FINALIZE_SUBJECT.format(id6=id6)
            if finalize_commit
            else f"records: move {id6} into executed/"
        )
        self._git("commit", "-q", "-m", subject)
        self._git("checkout", "-q", self.base_branch)
        return branch

    def _diverge(self, marker: str) -> None:
        """Make the base branch diverge so a merge cannot fast-forward."""
        (self.root / f"{marker}.txt").write_text(marker, encoding="utf-8")
        self._git("add", f"{marker}.txt")
        self._git("commit", "-q", "-m", f"diverge {marker}")

    def _begin_hand_merge(self, branch: str) -> None:
        """The HAND sequence: `git merge --no-commit`, which leaves MERGE_HEAD for `pre-commit`."""
        subprocess.run(
            ["git", "merge", "--no-ff", "--no-commit", branch],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            check=False,
        )
        git_dir = Path(self._out("rev-parse", "--absolute-git-dir"))
        self.assertTrue(
            (git_dir / "MERGE_HEAD").is_file(),
            "fixture precondition: the hand merge must leave a real MERGE_HEAD",
        )

    # ============================================================ E-01: the detector
    #: (case, build(self) -> (directory to probe, expected sha list), why this row exists)
    DETECTOR_STATES = (
        (
            "no merge in progress at all",
            lambda self: (self.root, []),
            "EMPTY MEANS NOT-A-MERGE, and the caller REFUSES on empty, so this row is what makes the "
            "gate FAIL CLOSED. A detector that reported a stale sha here would hand a merge "
            "exemption to every ordinary commit",
        ),
        (
            "a lane exists but no merge has been started",
            lambda self: (self.root, self._lane_without_merge()),
            "A BRANCH IS NOT A MERGE. The evidence path must unlock on merge STATE, never on the mere "
            "existence of a commit somewhere in the repository, or pushing a finalize commit to any "
            "branch would authorize a hand-edit on another",
        ),
        (
            "a hand merge (`git merge --no-commit`) in progress",
            lambda self: (self.root, self._hand_merge_incoming()),
            "THE `pre-commit` STAGE: MERGE_HEAD exists and holds the incoming sha. This is the "
            "positive row, and both rows above are vacuous while it is broken, because a detector "
            "that always returned [] satisfies them both",
        ),
        (
            "a merge inside a WORKTREE, where `.git` is a FILE",
            lambda self: self._worktree_merge_incoming(),
            "E-01 EXISTS BECAUSE OF THIS CASE. In a worktree `.git` is a file pointing elsewhere, so "
            "a hardcoded `<root>/.git/MERGE_HEAD` silently never matches, and lane worktrees are this "
            "repository's NORMAL execution mode: the bug would have stayed live exactly where the "
            "feature is used. The git dir must be resolved THROUGH git",
        ),
    )

    def _lane_without_merge(self) -> list:
        self._make_lane("abc123", finalize_commit=True)
        return []

    def _hand_merge_incoming(self) -> list:
        branch = self._make_lane("abc123", finalize_commit=True)
        self._diverge("d1")
        lane_head = self._out("rev-parse", branch)
        self._begin_hand_merge(branch)
        return [lane_head]

    def _worktree_merge_incoming(self) -> tuple:
        branch = self._make_lane("abc123", finalize_commit=True)
        self._diverge("d1")
        lane_head = self._out("rev-parse", branch)
        wt = self.root / "wt"
        self._git("worktree", "add", "-q", "--detach", str(wt), self.base_branch)
        self.assertTrue(
            (wt / ".git").is_file(), "fixture precondition: .git must be a FILE here"
        )
        subprocess.run(
            ["git", "merge", "--no-ff", "--no-commit", branch],
            cwd=str(wt),
            capture_output=True,
            text=True,
            check=False,
        )
        return wt, [lane_head]

    def test_the_merge_detector_reports_the_incoming_side_in_every_state(self):
        wrong = []
        for case, build, why in self.DETECTOR_STATES:
            with self.subTest(case=case):
                self.setUp()
                problem = None
                try:
                    where, expected = build(self)
                    actual = GATE._merge_incoming_commits(where)
                    if actual != expected:
                        problem = f"expected {expected!r}, got {actual!r}"
                finally:
                    self._tmp.cleanup()
                if problem:
                    wrong.append(
                        f"  {case}:\n    - {problem}\n"
                        f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"`_merge_incoming_commits` was wrong in {len(wrong)} of "
            f"{len(self.DETECTOR_STATES)} states. This one function decides whether the in-tree "
            "evidence path is unlocked at all, so read the grouping: both NON-merge rows reporting a "
            "sha means a merge exemption is now available to ordinary commits and the gate no longer "
            "fails closed; both MERGE rows reporting [] means genuinely finalized lanes can no longer "
            "be integrated and operators go back to `--no-verify`; the WORKTREE row failing alone "
            "means the git dir is being composed as `<root>/.git` again, which breaks the feature "
            "precisely in the lane worktrees it exists for. FIX: resolve the git dir through `git "
            "rev-parse --git-dir` and keep the `GITHEAD_*` fallback, which the `pre-merge-commit` "
            "stage needs because git has not written MERGE_HEAD yet at that point.\n"
            + "\n".join(wrong),
        )

    # ================================== E-02 / E-03 / E-04: what `check` decides given merge state
    #: (case, build(self) -> None leaving the repo staged, expected exit code, substrings that must ALL
    #: appear, substrings that must appear in NO message, why this row exists)
    MERGE_DECISIONS = (
        (
            "a merge whose incoming side carries the matching finalize commit",
            lambda self: self._merge_lane(finalize_commit=True),
            0,
            (),
            (),
            "THE WHOLE POINT OF THE SECOND PATH, and the row that makes the refusals below non-"
            "vacuous. The journal is gitignored AND ephemeral, so it cannot travel with a lane; "
            "before this path every integration of a genuinely finalized lane was refused and "
            "`--no-verify` became routine practice, which is a worse outcome than the gate prevents",
        ),
        (
            "a merge whose incoming side has NO finalize commit",
            lambda self: self._merge_lane(finalize_commit=False),
            1,
            (
                "abc123",
                "lifecycle(abc123): finalize",
                "aw ipd finalize",
                MERGE_WORDING,
            ),
            ("--no-verify", "git stash", "git reset", "git clean"),
            "A MERGE IS NOT A BLANKET EXEMPTION: this is the hand-edit staged inside a merge commit, "
            "which is the bypass the second path could most easily have opened. TWO old tests made "
            "different claims about this ONE input (that it refuses, and that its refusal is "
            "actionable without teaching a bypass), so both are columns on one row rather than two "
            "tests: the refusal must name the plan, quote the subject to look for, and name the "
            "remedy, while naming NEITHER `--no-verify` NOR any tree-mutating command, since telling "
            "an operator to stash or reset in a shared checkout destroys a co-worker's work",
        ),
        (
            "a merge carrying a finalize commit for a DIFFERENT id6",
            lambda self: self._merge_lane_with_foreign_finalize(),
            1,
            ("abc123", MERGE_WORDING),
            (),
            "THE EVIDENCE IS PLAN-BOUND, exactly as the journal predicate binds to plan_id+dest. A "
            "lane routinely carries several finalize commits, so a predicate answering 'does this "
            "merge contain ANY finalize commit' would let one legitimately finalized plan authorize "
            "every other plan riding along beside it",
        ),
        (
            "a finalize commit already reachable from HEAD",
            lambda self: self._merge_lane_with_finalize_on_head(),
            1,
            ("abc123", MERGE_WORDING),
            (),
            "INCOMING-SIDE-ONLY (`HEAD..MERGE_HEAD`). Every finalize commit ever made stays reachable "
            "from HEAD forever, so a search over the whole history would let the FIRST plan ever "
            "finalized authorize every later hand-edit of a plan with the same id6",
        ),
        (
            "a plan with no readable `- Id:`, during a merge",
            lambda self: self._merge_lane(finalize_commit=True, strip_id=True),
            1,
            (REASON_NO_ID,),
            (),
            "WITH NO id6 THE PREDICATE HAS NOTHING TO BIND TO, so a merge must not rescue it. This "
            "row carries the lane's REAL finalize commit, which is what makes it sharp: the only "
            "thing missing is the handle, and an implementation that fell back to 'a merge is in "
            "progress and some finalize commit is present' would accept it",
        ),
        (
            "a hand-edited status flip OUTSIDE any merge",
            lambda self: self._hand_edit_no_merge(),
            1,
            (NON_MERGE_WORDING, "aw ipd finalize"),
            (MERGE_WORDING,),
            "THE NON-MERGE WORDING MUST BE UNCHANGED by the second path. The remedies differ (fix "
            "the journal-less transition here, versus finalize on the branch that owns the plan "
            "there), so the forbidden substring is the load-bearing half: merge wording shown outside "
            "a merge sends an operator to a branch that does not exist",
        ),
        (
            "a `git mv` into executed/ OUTSIDE any merge",
            lambda self: self._git_mv_no_merge(),
            1,
            (REASON_MOVED,),
            (MERGE_WORDING,),
            "the second spelling of the non-merge case, kept because the MOVED reason is produced by "
            "a different detection branch than the status flip and each reason must survive the "
            "merge-awareness change independently",
        ),
    )

    def _merge_lane(self, *, finalize_commit: bool, strip_id: bool = False) -> None:
        branch = self._make_lane(
            "abc123", finalize_commit=finalize_commit, strip_id=strip_id
        )
        self._diverge("d1")
        self._begin_hand_merge(branch)

    def _merge_lane_with_foreign_finalize(self) -> None:
        self._write_plan_at("pending", "other1", status="approved")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "add other plan")
        self.base_branch = self._out("rev-parse", "--abbrev-ref", "HEAD")
        branch = self._make_lane("abc123", finalize_commit=False)
        # Put a finalize commit for a DIFFERENT id6 on the same lane.
        self._git("checkout", "-q", branch)
        (self.root / "unrelated.txt").write_text("x", encoding="utf-8")
        self._git("add", "unrelated.txt")
        self._git("commit", "-q", "-m", FINALIZE_SUBJECT.format(id6="other1"))
        self._git("checkout", "-q", self.base_branch)
        self._diverge("d1")
        self._begin_hand_merge(branch)

    def _merge_lane_with_finalize_on_head(self) -> None:
        self._git(
            "commit", "-q", "--allow-empty", "-m", FINALIZE_SUBJECT.format(id6="abc123")
        )
        self.base_branch = self._out("rev-parse", "--abbrev-ref", "HEAD")
        branch = self._make_lane("abc123", finalize_commit=False)
        self._diverge("d1")
        self._begin_hand_merge(branch)

    def _hand_edit_no_merge(self) -> None:
        p = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / self._plan_name("abc123")
        )
        p.write_text(
            p.read_text(encoding="utf-8").replace(
                "- Status: approved", "- Status: executed"
            ),
            encoding="utf-8",
        )
        self._git("add", "-A")

    def _git_mv_no_merge(self) -> None:
        (self.root / ".aw" / "records" / "plans" / "executed").mkdir(
            parents=True, exist_ok=True
        )
        self._git(
            "mv",
            f".aw/records/plans/pending/{self._plan_name('abc123')}",
            f".aw/records/plans/executed/{self._plan_name('abc123')}",
        )

    def test_merge_state_never_becomes_a_blanket_exemption(self):
        wrong = []
        for case, build, want_rc, needles, forbidden, why in self.MERGE_DECISIONS:
            with self.subTest(case=case):
                self.setUp()
                problems = []
                try:
                    build(self)
                    before = _snapshot(self.root)
                    rc, msgs = GATE.check(self.root)
                    after = _snapshot(self.root)
                    if rc != want_rc:
                        problems.append(
                            f"expected exit code {want_rc}, got {rc} with messages {msgs!r}"
                        )
                    if want_rc == 0 and msgs:
                        problems.append(
                            f"an accepted merge must report NOTHING, got {msgs!r}"
                        )
                    joined = " ".join(msgs)
                    missing = [n for n in needles if n not in joined]
                    if missing:
                        problems.append(
                            f"the refusal must state {missing!r}; it said {joined!r}"
                        )
                    leaked = [f for f in forbidden if f in joined]
                    if leaked:
                        problems.append(
                            f"the refusal must NOT contain {leaked!r}; it said {joined!r}"
                        )
                    if after != before:
                        problems.append(
                            "THE GATE MUTATED THE TREE OR THE INDEX, so a plan did not stay where "
                            "the merge had put it; a refusal that already performed the transition "
                            "is not a refusal"
                        )
                finally:
                    self._tmp.cleanup()
                if problems:
                    wrong.append(
                        f"  {case}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"`check` decided {len(wrong)} of {len(self.MERGE_DECISIONS)} merge situations wrongly. "
            "Read the grouping: if EVERY in-merge refusal row now passes, merge state has become a "
            "blanket exemption and staging a hand-edit inside a merge commit is an open bypass; if "
            "the accepting row refuses, no finalized lane can be integrated at all and `--no-verify` "
            "becomes routine again, which is the practice this path was built to end; if the two "
            "OUTSIDE-a-merge rows changed, the merge-awareness work altered non-merge behavior, which "
            "it is required not to do; if only the wording rows failed the verdicts are right but the "
            "messages send operators to the wrong remedy. FIX: keep the three bindings intact "
            "(plan-bound id6, incoming-side-only `HEAD..MERGE_HEAD`, exact subject form); each row "
            "above corresponds to dropping exactly one of them.\n" + "\n".join(wrong),
        )

    # ================================== E-05 / E-06: end to end, through the installed hook
    #: (case, hook names to install, build(self) -> branch list, whether to run a SEPARATE `git
    #: commit` after the merge, expected process exit status, output substrings required, why)
    INSTALLED_HOOK_RUNS = (
        (
            "hand merge of an evidenced lane, gated at `pre-commit`",
            ("pre-commit",),
            lambda self: [self._prepare_lane(finalize_commit=True)],
            True,
            0,
            (),
            "THE STAGE GIT RUNS FOR THE HAND SEQUENCE. `git merge --no-commit` then `git commit` "
            "fires `pre-commit`, and this row proves the accepting path survives the real hook rather "
            "than only the in-process call, which is what an operator actually experiences",
        ),
        (
            "automated merge of an UNEVIDENCED lane, gated at `pre-merge-commit`",
            ("pre-merge-commit",),
            lambda self: [self._prepare_lane(finalize_commit=False)],
            False,
            1,
            ("abc123",),
            "E-06: THE STAGE GIT ACTUALLY RUNS FOR AN AUTOMATED MERGE, and before this it was not "
            "wired at all, so a `git merge` that created its own commit carried plans into executed/ "
            "COMPLETELY UNGATED. `pre-commit` does not fire for that path, which is why registering "
            "the second stage is a separate requirement and not a duplicate of the row above",
        ),
        (
            "automated merge of an EVIDENCED lane, gated at `pre-merge-commit`",
            ("pre-merge-commit",),
            lambda self: [self._prepare_lane(finalize_commit=True)],
            False,
            0,
            (),
            "the accepting half of the same stage. Paired with the row above, identical but for the "
            "lane's finalize commit, the two state that the new stage DISCRIMINATES rather than "
            "either refusing every automated merge or waving them all through",
        ),
        (
            "an OCTOPUS merge of two evidenced lanes",
            ("pre-merge-commit",),
            lambda self: self._prepare_octopus_lanes(),
            False,
            0,
            (),
            "AN OCTOPUS MERGE HAS SEVERAL INCOMING SIDES, exposed at `pre-merge-commit` as one "
            "`GITHEAD_<sha>` variable each, so evidence must be searched across ALL of them. An "
            "implementation reading only the first would refuse a legitimate multi-lane integration, "
            "and `AUTO_MERGE` is no substitute because the octopus strategy never writes it",
        ),
    )

    def _install_hook(self, *hook_names: str) -> None:
        hooks_dir = Path(self._out("rev-parse", "--absolute-git-dir")) / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        for name in hook_names:
            script = hooks_dir / name
            script.write_text(
                "#!/bin/bash\nexec python3 -m agent_workflows ipd-executed-gate\n",
                encoding="utf-8",
            )
            script.chmod(0o755)

    def _env(self) -> dict:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
        return env

    def _prepare_lane(self, *, finalize_commit: bool) -> str:
        branch = self._make_lane("abc123", finalize_commit=finalize_commit)
        self._diverge("d1")
        return branch

    def _prepare_octopus_lanes(self) -> list:
        self._write_plan_at("pending", "other1", status="approved")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "add other plan")
        self.base_branch = self._out("rev-parse", "--abbrev-ref", "HEAD")
        b1 = self._make_lane("abc123", finalize_commit=True)
        b2 = self._make_lane("other1", finalize_commit=True)
        self._diverge("d1")
        return [b1, b2]

    def test_git_itself_enforces_the_gate_at_both_merge_stages(self):
        wrong = []
        for (
            case,
            hooks,
            build,
            commit_after,
            want_rc,
            needles,
            why,
        ) in self.INSTALLED_HOOK_RUNS:
            with self.subTest(case=case):
                self.setUp()
                problems = []
                try:
                    branches = build(self)
                    self._install_hook(*hooks)
                    merge_args = (
                        ["--no-ff", "--no-commit", *branches]
                        if commit_after
                        else (
                            ["--no-ff", "--no-edit", "-m", "integrate lane", *branches]
                            if len(branches) == 1
                            else ["--no-edit", "-m", "octopus integrate", *branches]
                        )
                    )
                    proc = subprocess.run(
                        ["git", "merge", *merge_args],
                        cwd=str(self.root),
                        capture_output=True,
                        text=True,
                        check=False,
                        env=self._env(),
                    )
                    if commit_after:
                        proc = subprocess.run(
                            ["git", "commit", "-m", "integrate lane"],
                            cwd=str(self.root),
                            capture_output=True,
                            text=True,
                            check=False,
                            env=self._env(),
                        )
                    output = proc.stdout + proc.stderr
                    if proc.returncode != want_rc:
                        problems.append(
                            f"expected git to exit {want_rc}, got {proc.returncode}. Output:\n"
                            f"{output}"
                        )
                    missing = [n for n in needles if n not in output]
                    if missing:
                        problems.append(
                            f"git's output must name {missing!r}; it said:\n{output}"
                        )
                finally:
                    self._tmp.cleanup()
                if problems:
                    wrong.append(
                        f"  {case} (hooks={list(hooks)}):\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"git enforced the gate wrongly in {len(wrong)} of {len(self.INSTALLED_HOOK_RUNS)} real "
            "merges. These rows are the only ones that prove the hook is WIRED rather than merely "
            "correct when called, so read the grouping: every row exiting 0 means the hook is not "
            "firing at all (check the script is executable and `python3 -m agent_workflows "
            "ipd-executed-gate` resolves on PATH with this PYTHONPATH); both `pre-merge-commit` rows "
            "failing while `pre-commit` passes means the second stage is unregistered and automated "
            "merges are ungated, which is precisely the hole E-06 closed; the OCTOPUS row failing "
            "alone means only one incoming side is being searched. FIX: an unexpected exit 0 here is "
            "an open bypass and is more serious than an unexpected exit 1, which merely blocks a "
            "legitimate merge.\n" + "\n".join(wrong),
        )


class PreCommitConfigStageRegistrationTests(unittest.TestCase):
    """`.pre-commit-config.yaml` must install and register the gate for BOTH git stages (E-06).

    This is a CONFIGURATION assertion only. It is NOT evidence that the stage fires; that is proven by
    the real-merge tests above, which install the hook and run actual merges.

    ONE table replaces two tests. Both parsed the same YAML file once and asserted one fact about it,
    differing only in WHICH key they read, so the key and its expected value are the data.

    THE KEY NAMES ARE SPELLED LITERALLY AND EXACTLY, because `pre-commit` reads this file and a
    misspelled key is SILENTLY IGNORED: `default_install_hook_types` typo'd installs only
    `pre-commit`, and the automated-merge stage then goes unregistered with no error anywhere. That
    failure mode is invisible in CI, which is why the spelling is asserted here rather than inferred.
    """

    #: (case, read(data) -> actual value, the exact expected value, why this row exists)
    REGISTRATIONS = (
        (
            "`default_install_hook_types` installs BOTH stages",
            lambda data: data.get("default_install_hook_types"),
            ["pre-commit", "pre-merge-commit"],
            "WITHOUT THIS KEY NOTHING ELSE MATTERS: `pre-commit install` writes only the hook types "
            "listed here, so an automated `git merge` fires no hook at all and the gate's "
            "`pre-merge-commit` registration below is dead configuration",
        ),
        (
            "`default_stages` stays pinned to pre-commit alone",
            lambda data: data.get("default_stages"),
            ["pre-commit"],
            "INSTALLING A SECOND HOOK TYPE MUST NOT RUN EVERY HOOK MID-MERGE. Without this pin the "
            "content-MUTATING hooks (ruff --fix, the whitespace fixers) would rewrite files in the "
            "middle of a merge resolution, which corrupts a conflict resolution in progress",
        ),
        (
            "exactly one hook opts into pre-merge-commit",
            lambda data: [
                hook["id"]
                for repo in data["repos"]
                for hook in repo["hooks"]
                if "pre-merge-commit" in (hook.get("stages") or [])
            ],
            ["ipd-executed-transition-gate"],
            "THE OPT-IN IS THE OTHER HALF of the pin above: the gate must be the ONLY hook that runs "
            "at merge time. Asserting the exact LIST rather than membership is what catches a second "
            "hook being added to the merge stage later, which is how a mutating hook would creep back "
            "into a merge",
        ),
    )

    def setUp(self):
        self.cfg_path = Path(__file__).resolve().parents[1] / ".pre-commit-config.yaml"
        self.cfg = self.cfg_path.read_text(encoding="utf-8")

    def test_both_git_stages_are_registered_with_only_the_gate_at_merge_time(self):
        import yaml

        data = yaml.safe_load(self.cfg)
        wrong = []
        for case, read, expected, why in self.REGISTRATIONS:
            try:
                actual = read(data)
            except (KeyError, TypeError) as exc:
                actual = f"<unreadable: {exc!r}>"
            if actual != expected:
                wrong.append(
                    f"  {case}:\n    - expected {expected!r}, got {actual!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.REGISTRATIONS)} stage registrations in "
            f"{self.cfg_path.name} are wrong. All three describe ONE decision (run this gate, and "
            "only this gate, at merge time), so read the grouping: the install-types row failing "
            "alone means no merge-stage hook is installed and the other two are moot; the two "
            "stage rows failing together means every hook now runs mid-merge, including the ones "
            "that REWRITE files during a conflict resolution. FIX: a key here is silently ignored "
            "when misspelled, so compare the spelling character by character rather than assuming "
            "the value is wrong.\n" + "\n".join(wrong),
        )


if __name__ == "__main__":
    unittest.main()
