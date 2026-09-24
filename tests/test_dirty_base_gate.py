#!/usr/bin/env python3

"""The dirty-base cases a LANE guard cannot reach (dirtybase Order 01, `3i0aaz`).

WHAT THIS FILE IS FOR, and how it differs from `tests/test_lane_clean_base.py`, which it deliberately
does not touch. That file is plan `nna8yz` E-05's own suite and covers the TRACKED + ISOLATED case:
a lane is built from a commit, so an uncommitted TRACKED edit is silently absent from it, and the
guard refuses. Three cases survived that guard, and they are this file's subject:

  1. UNTRACKED DIRT is invisible to it by explicit design, yet the measured incident is exactly that:
     a stray `aw install` wrote 130+ uncommitted, largely UNTRACKED files into a working tree and on
     at least two occasions an agent did not realize the pollution was its own. So untracked content
     is REPORTED once per run, with its consequence, and REFUSES ON NOTHING.
  2. SHARED-TREE RUNS skipped the guard entirely, because its call site was gated on `if isolate and
     ...`. That is the case where dirt is MOST dangerous - the agent writes directly into the tree it
     is polluting - and it was the least guarded. It now refuses, with a message that is TRUE for a
     shared tree.
  3. NO CONSENT SURFACE existed, so there was no sanctioned way to proceed deliberately over known
     dirt. `--allow-dirty-base` is that surface, and consenting is RECORDED.

THE ASYMMETRY IN (1) IS LOAD-BEARING AND IS THE THING MOST LIKELY TO BE "FIXED" WRONGLY. Untracked
content reports and tracked content refuses, ON BOTH PATHS. Refusing on untracked content would make
an unattended run unstartable in essentially any working checkout and would train operators to pass
the consent flag reflexively, destroying its signal value. `test_untracked_only_does_not_refuse_on_
either_path` exists to make that a test failure rather than a judgment call.

EVERY CASE RUNS AGAINST A `TemporaryDirectory` FIXTURE REPOSITORY, never this checkout. Every case
needs a DIRTY tree, and producing one here would mean dirtying a shared checkout that other agents
and humans are working in. `tests/test_lane_clean_base.py:85-95` established the pattern; this
follows it.
"""

from __future__ import annotations

import argparse
import contextlib
import inspect
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import mock

from agent_workflows import agy_runipd, lane_containment, oc_runipd, runner_shared

#: Both host drivers. Every behavioral assertion below runs against BOTH: a containment rule present
#: on one host only is a defect (spec `7ckptx` CID-3), and the `--full-auto` default really did come
#: to mean opt-in on one runner and opt-out on the other by exactly that route.
DRIVERS = (
    ("oc", oc_runipd, "run_opencode"),
    ("agy", agy_runipd, "run_agy_turn"),
)


#: The approved plan every `execute_item` fixture in this file queues.
_PLAN = """# IPD: dirty-base gate probe

- Date: 2026-09-14
- Kind: child
- Concern: probe.
- Scope: probe.
- Scope-Paths: src/
- Item-Dependencies: none
- Status: approved
- Set: probe
- Order: 1
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history
- 2026-09-14 approved (test): probe.
"""


def _clean_base_fixture(tmp: Path, *, isolate: bool, consent: bool = False):
    """A fixture repo plus the (run_dir, state, item) a real `execute_item` turn needs.

    MODULE-LEVEL so both the WIRING tests and the no-spawn tests drive the SAME shape. They previously
    had one copy each, which is how a wiring test can come to assert about a turn the behavioral tests
    never run.
    """
    repo = _init_repo(tmp)
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True)
    plan = pending / "20260914-probe-01-dbg001-probe.ipd.md"
    plan.write_text(_PLAN.format(id6="dbg001"), encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "add plan")

    run_dir = repo / ".aw" / "records" / "runs" / "run-dbg"
    (run_dir / "outcomes").mkdir(parents=True)
    (run_dir / "prompts").mkdir(parents=True)
    item = {
        "position": 1,
        "id6": "dbg001",
        "setid": "probe",
        "status": "queued",
        "configured_file": str(plan.relative_to(repo)),
        "action": "execute",
    }
    state = {
        "run_id": "run-dbg",
        "created_at": "2026-09-14T00:00:00+00:00",
        "updated_at": "2026-09-14T00:00:00+00:00",
        "selectors": ["probe"],
        "repo": str(repo),
        "queue": [item],
        "set_sessions": {},
        "session_id": None,
        "options": {
            "opencode": "/bin/true",
            "agy": "/bin/true",
            "model": "probe",
            "self_finalize": True,
            "no_audit": True,
            "isolate_worktree": isolate,
            "allow_dirty_base": consent,
        },
    }
    return repo, run_dir, state, item


def _drive_execute_item(
    driver, spawn_name, run_dir, state, item, *, extra_patches=()
) -> int:
    """Run the REAL `execute_item` with the spawn and lifecycle stubbed; return the spawn count.

    `extra_patches` is a tuple of `(target, attribute, replacement)` so a caller can add a spy of its
    own without copying this stub set, which is what keeps every driven assertion in this file talking
    about the same turn.
    """
    spawned: list[Any] = []

    def fake_spawn(*_a, **_k):
        spawned.append(1)
        return 0, "ses", str(run_dir / "log"), ["probe"]

    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch.object(driver, spawn_name, fake_spawn))
        stack.enter_context(
            mock.patch.object(driver, "driver_begin", lambda *a, **k: (0, "ok"))
        )
        stack.enter_context(
            mock.patch.object(driver, "driver_finalize", lambda *a, **k: (0, "ok"))
        )
        stack.enter_context(
            mock.patch.object(
                driver, "assert_child_tool_identity", lambda *a, **k: None
            )
        )
        for target, attribute, replacement in extra_patches:
            stack.enter_context(mock.patch.object(target, attribute, replacement))
        driver.execute_item(run_dir, state, item, recovery=False)
    return len(spawned)


class _OrderRecorder:
    """Records the ORDER in which wrapped collaborators are called, for call-order assertions.

    A CLASS rather than per-test closures: every caller wraps several collaborators inside a loop, and
    a closure over a per-iteration list is the late-binding trap that silently makes one iteration
    assert about another's run.
    """

    def __init__(self) -> None:
        self.order: list[str] = []

    def wrap(self, label: str, real):
        """`real`, but appending `label` to the order log first. The real behavior is preserved."""

        def _wrapped(*args, **kwargs):
            self.order.append(label)
            return real(*args, **kwargs)

        return _wrapped


# `_effective_execute_item_source` was DELETED with its last caller (audit 2026-09-19). It resolved
# `execute_item`'s source text, following the `execute_item_core` relocation and textually substituting
# each host's spawn name, purely so five tests could search or offset-compare that text. Every one of
# those five now drives the real `execute_item` with spies (see `_drive_execute_item`), so nothing in
# this file reads product source to decide a wiring question any more.


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True
    )
    return proc.stdout


def _init_repo(root: Path) -> Path:
    """A fixture repository with one committed tracked file. NEVER this checkout."""
    repo = root / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "t")
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
    )
    (repo / "tracked.txt").write_text("v1\n", encoding="utf-8")
    _git(repo, "add", ".gitignore", "tracked.txt")
    _git(repo, "commit", "-qm", "init")
    return repo


# ======================================================================================================
# E-02: the once-per-run untracked report
# ======================================================================================================
#: The `sample` column's sentinel for "this row does not pin the exact sample, only the total".
ANY_SAMPLE = object()


class UntrackedReportRuleTests(unittest.TestCase):
    """The shared RULE, driven by porcelain text so every case is reachable with no repository.

    THE CLASSIFICATION CASES ARE ONE TABLE (audit 2026-09-19). Four tests each fed one porcelain blob
    to `evaluate_untracked_dirt` and asserted its `clean`, `total` and sometimes `sample`; they differed
    ONLY in the blob, which is the definition of a data-driven cluster.

    THE CLEAN ROW AND THE DIRTY ROWS SHARE THE TABLE, which is what makes it non-vacuous in both
    directions: a rule that reported EVERYTHING as dirt would satisfy the counting rows while making the
    report fire on every clean checkout (and a report that always fires is a report nobody reads), and a
    rule that reported NOTHING would satisfy the clean row while restoring the silence this whole
    feature exists to end. The failure message says which direction collapsed.
    """

    #: (case, porcelain text, expected `clean`, expected `total`, expected `sample` or ANY_SAMPLE,
    #: why this row exists)
    CLASSIFICATIONS = (
        (
            "a clean tree",
            "",
            True,
            0,
            (),
            "SILENCE ON A CLEAN TREE is the row that keeps this report worth reading. A report that "
            "fires on every checkout trains operators to skip it, which would destroy the signal value "
            "of the one case it exists for (the measured 130-file `aw install` pollution event)",
        ),
        (
            "thirty untracked files",
            "".join(f"?? f{i}.txt\n" for i in range(30)),
            False,
            30,
            ANY_SAMPLE,
            "THE TOTAL IS EXACT WHILE THE ENUMERATION IS BOUNDED, and the pair is the point: the "
            "operator needs to know the true SIZE of the pollution (30, not 12) while a 130-path wall "
            "of text is precisely the unread log this replaces. The sample LENGTH is asserted "
            "separately below against the shared limit constant",
        ),
        (
            "tracked dirt mixed with one untracked file",
            " M tracked.py\nM  staged.py\nD  gone.py\n?? new.py\n",
            False,
            1,
            ("new.py",),
            "THE SCOPE BOUNDARY, and the asymmetry this whole file defends: unstaged, staged and "
            "deleted TRACKED paths are the clean-base GUARD's business (it refuses), while this report "
            "answers the UNTRACKED question (it never refuses). A rule that counted all four would "
            "conflate the two questions and make the report look like a refusal",
        ),
        (
            "an ignored path",
            "!! build/\n",
            True,
            0,
            (),
            "`!!` IS NOT `??`. An ignored file is not pollution, it is CONFIGURATION, so reporting it "
            "would flag every build directory in every repository as a problem on every run",
        ),
    )

    def test_every_porcelain_shape_is_classified_correctly(self):
        wrong: list[str] = []
        clean_rows_broken = 0
        dirty_rows_broken = 0
        for case, porcelain, clean, total, sample, why in self.CLASSIFICATIONS:
            report = runner_shared.evaluate_untracked_dirt(porcelain)
            problems: list[str] = []
            if report.clean is not clean:
                problems.append(f"expected clean={clean}, got {report.clean}")
                if clean:
                    clean_rows_broken += 1
                else:
                    dirty_rows_broken += 1
            if report.total != total:
                problems.append(
                    f"expected total={total}, got {report.total}; the TOTAL is exact and is never "
                    "sampled, because the operator needs the real size of the pollution"
                )
            if sample is not ANY_SAMPLE and report.sample != sample:
                problems.append(
                    f"expected sample={sample!r}, got {report.sample!r}; the sample must NAME the "
                    "untracked paths, since a count alone tells an operator nothing actionable"
                )
            if problems:
                wrong.append(
                    f"  {case} ({porcelain!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        direction = ""
        if dirty_rows_broken and not clean_rows_broken:
            direction = (
                f" ALL {dirty_rows_broken} failing row(s) are DIRTY rows, so the rule has gone SILENT: "
                "real untracked pollution is no longer reported, which restores the exact silence this "
                "feature exists to end (an agent not realizing 130 uncommitted files were its own). "
                "The clean row proves nothing while this is true."
            )
        elif clean_rows_broken and not dirty_rows_broken:
            direction = (
                f" ALL {clean_rows_broken} failing row(s) are CLEAN rows, so the rule now reports "
                "dirt EVERYWHERE: the report would fire on every run in every checkout, and an "
                "operator who sees it every time stops reading it. The dirty rows prove nothing while "
                "this is true."
            )
        self.assertEqual(
            wrong,
            [],
            f"`evaluate_untracked_dirt` misclassified {len(wrong)} of "
            f"{len(self.CLASSIFICATIONS)} porcelain shapes.{direction} FIX: the rule's whole job is to "
            "count `??` entries and NOTHING else -- not tracked changes (the guard's question, which "
            "refuses) and not `!!` ignored paths (configuration). Never relax a row to green.\n"
            + "\n".join(wrong),
        )

    def test_the_enumeration_is_bounded_by_the_shared_limit(self):
        """Kept separate: the assertion is against a shared CONSTANT, not against row data.

        Inlining the limit into a table row would let the row and the constant drift apart, and reading
        the constant INTO the row would make the assertion tautological (both sides moving together is
        the trap `tests/test_ipd_lint.py` documents). So the bound is asserted once, here, against a
        population comfortably larger than it.
        """
        report = runner_shared.evaluate_untracked_dirt(
            "".join(f"?? f{i}.txt\n" for i in range(30))
        )
        self.assertEqual(
            len(report.sample),
            runner_shared.UNTRACKED_REPORT_SAMPLE_LIMIT,
            "the ENUMERATION is bounded; a 130-path wall of text is the unread log this replaces",
        )
        self.assertLess(
            len(report.sample),
            report.total,
            "and the fixture must be LARGER than the limit, or boundedness is untested",
        )

    def test_the_consequence_is_stated_CONDITIONALLY(self):
        """F-13: an unconditional "your lanes will be refused" is FALSE and trains operators to
        ignore the report. Integration refuses only on OVERLAP."""
        notice = runner_shared.evaluate_untracked_dirt("?? a.txt\n").notice
        self.assertIn("OVERLAP", notice)
        self.assertIn("disjoint", notice)
        self.assertIn("1 UNTRACKED path(s)", notice)

    def test_the_report_never_tells_anyone_to_touch_un_owned_work(self):
        notice = runner_shared.evaluate_untracked_dirt("?? a.txt\n").notice
        for forbidden in ("git stash", "git reset", "git clean", "stash it", "delete"):
            self.assertNotIn(forbidden, notice)


#: A minimal approved plan the real `initialize_run` accepts, for the wiring tests below.
_WIRING_PLAN = "\n".join(
    [
        "# IPD: {id6}",
        "",
        "- Date: 2026-09-17",
        "- Kind: child",
        "- Status: approved",
        "- Set: guard (the guard set)",
        "- Order: {order}",
        "- Id: {id6}",
        "- Item-Dependencies: none",
        "",
        "## Goal",
        "",
        "Do the thing.",
        "",
    ]
)


class UntrackedReportWiringTests(unittest.TestCase):
    """WHERE the report is emitted, which is the half of E-02 most easily got wrong.

    EVERY CLAIM HERE IS NOW DRIVEN ON A REAL `initialize_run` (audit 2026-09-19), against a throwaway
    fixture repository holding approved plans and one untracked file. The three properties -- it is
    called, it is called ONCE rather than per item, and it is ordered between the shared preflight
    refusals and queue resolution -- are read off spies that record CALL ORDER on that real run.

    THE RECONCILIATION NOTE THIS REPLACES, preserved because the decision must stay re-examinable.
    `test_it_sits_beside_the_shared_preflight_refusals` compared BYTE OFFSETS
    (`init.find("refuse_unimplemented_run_flags") < init.find("report_untracked_dirt_at_run_start")`)
    inside `initialize_run`. It was deleted once on an earlier audit branch and then RESTORED by taking
    main's side, for two stated reasons: main had deliberately PATCHED it twice to follow the
    `initialize_run_core` and `execute_item_core` refactors (a maintainer act, not drift), and its
    ORDERING claim was covered behaviorally NOWHERE ELSE in the suite. That note ended with the exact
    condition for its removal: "If someone gives the ordering a behavioral proof (assert the report is
    emitted before selectors resolve, on a real run), delete this."

    THAT PROOF NOW EXISTS, in `test_the_report_is_ordered_between_the_preflight_refusals_and_queue_
    resolution` below, which is why the offset test is gone. It patches
    `refuse_unimplemented_run_flags`, `report_untracked_dirt_at_run_start` and each host's
    `expand_selectors` with spies appending to ONE list and asserts the recorded order on a real run.
    It is strictly stronger in three ways the offsets could not be: a MENTION in a comment cannot
    satisfy it, a reformat or a third relocation into a shared core cannot break it, and it observes
    the order the code EXECUTES rather than the order it is written (which differ whenever a call sits
    inside a branch or a helper). The offsets' known cost is also gone: it had already broken twice on
    behavior-preserving refactors.

    THE ONE THING THE OFFSETS COVERED AND THIS DOES NOT, stated so the trade is honest: a byte-offset
    scan reads the whole function including branches this fixture does not enter, so a report call
    added to some OTHER path would have moved the offsets. That residual is covered instead by the
    once-per-run assertion, which drives a real multi-item `run_queue` and requires the call count to
    be exactly zero there.
    """

    def _git(self, repo: Path, *args: str) -> None:
        subprocess.run(
            ["git", *args], cwd=repo, text=True, capture_output=True, check=True
        )

    def _fixture_repo(
        self, tmp: Path, *, plans: int = 3, untracked: bool = True
    ) -> Path:
        """A committed repo with `plans` approved plans and (optionally) one untracked file."""
        repo = tmp / "repo"
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True)
        self._git(repo, "init", "-q")
        self._git(repo, "config", "user.email", "t@example.invalid")
        self._git(repo, "config", "user.name", "t")
        (repo / ".gitignore").write_text(".aw/records/runs/\n", encoding="utf-8")
        for index in range(plans):
            id6 = f"aaa{index:03d}"
            (pending / f"20260917-guard-0{index + 1}-{id6}-guard.ipd.md").write_text(
                _WIRING_PLAN.format(id6=id6, order=index + 1), encoding="utf-8"
            )
        self._git(repo, "add", "-A")
        self._git(repo, "commit", "-qm", "fixture")
        if untracked:
            (repo / "stray.log").write_text("noise\n", encoding="utf-8")
        return repo

    def _initialize(self, driver, repo: Path, patches=()) -> tuple[Path, str]:
        """Run the REAL `initialize_run` with `--prepare-only`, returning (run_dir, output)."""
        args = driver.build_parser().parse_args(["start", "all", "--repo", str(repo)])
        args.prepare_only = True
        buffer = io.StringIO()
        with contextlib.ExitStack() as stack:
            for target, attribute, replacement in patches:
                stack.enter_context(mock.patch.object(target, attribute, replacement))
            stack.enter_context(contextlib.redirect_stdout(buffer))
            stack.enter_context(contextlib.redirect_stderr(buffer))
            run_dir = driver.initialize_run(args)
        return run_dir, buffer.getvalue()

    def test_the_report_is_ordered_between_the_preflight_refusals_and_queue_resolution(
        self,
    ):
        """THE BEHAVIORAL PROOF the deleted byte-offset pin's own note asked for.

        Three collaborators are spied on a REAL run and the recorded CALL ORDER is asserted. Both
        neighbours matter and for different reasons: AFTER the shared refusals, because a run that will
        be refused outright must not first print a report about a tree it never touches; BEFORE
        selector expansion, because queue resolution is the first expensive step and the operator must
        see the pollution warning before the run commits to anything.
        """
        for name, driver, _spawn in DRIVERS:
            with self.subTest(driver=name), TemporaryDirectory() as tmp:
                repo = self._fixture_repo(Path(tmp))
                recorder = _OrderRecorder()
                patches = (
                    (
                        runner_shared,
                        "refuse_unimplemented_run_flags",
                        recorder.wrap(
                            "refusals", runner_shared.refuse_unimplemented_run_flags
                        ),
                    ),
                    (
                        runner_shared,
                        "report_untracked_dirt_at_run_start",
                        recorder.wrap(
                            "report",
                            runner_shared.report_untracked_dirt_at_run_start,
                        ),
                    ),
                    (
                        driver,
                        "expand_selectors",
                        recorder.wrap("expand", driver.expand_selectors),
                    ),
                )
                self._initialize(driver, repo, patches)
                self.assertEqual(
                    recorder.order,
                    ["refusals", "report", "expand"],
                    f"{name}: the untracked report must be emitted AFTER the shared preflight "
                    "refusals (so a run about to be refused does not first report on a tree it "
                    "never touches) and BEFORE selector expansion (so the operator sees the "
                    f"pollution before queue resolution). Observed: {recorder.order}",
                )

    def test_the_report_precedes_the_run_directory_so_it_is_not_durable_state(self):
        """The other half of the seam's meaning: it runs before any run state exists.

        Asserted by LOOKING at the filesystem from inside the report call, which a byte-offset scan
        cannot do at all. This is what makes the report advisory rather than something a later reader
        could mistake for a recorded run finding.
        """
        for name, driver, _spawn in DRIVERS:
            with self.subTest(driver=name), TemporaryDirectory() as tmp:
                repo = self._fixture_repo(Path(tmp))
                observed: list[list[str]] = []
                real = runner_shared.report_untracked_dirt_at_run_start

                def peek(*args, _real=real, _seen=observed, _repo=repo, **kwargs):
                    runs = _repo / ".aw" / "records" / "runs"
                    _seen.append(
                        sorted(p.name for p in runs.glob("run-*"))
                        if runs.is_dir()
                        else []
                    )
                    return _real(*args, **kwargs)

                self._initialize(
                    driver,
                    repo,
                    ((runner_shared, "report_untracked_dirt_at_run_start", peek),),
                )
                self.assertEqual(
                    observed,
                    [[]],
                    f"{name}: at report time no run directory may exist yet, or the report reads as "
                    f"durable run state rather than a pre-run advisory; saw {observed}",
                )

    def test_it_is_emitted_ONCE_per_run_and_not_once_per_queue_item(self):
        """F-11: the report belongs at the once-per-run seam, never beside the per-ITEM guard.

        DRIVEN over a THREE-ITEM queue (audit 2026-09-19), which is what makes the claim testable: the
        defect being prevented is a report that says the same thing N times, and a one-item fixture
        cannot tell one emission from per-item emission. Two measurements together: the notice appears
        exactly once in `initialize_run`'s output, and the reporter is called ZERO times across a real
        `run_queue` that dispatches all three items.
        """
        for name, driver, _spawn in DRIVERS:
            with self.subTest(driver=name), TemporaryDirectory() as tmp:
                repo = self._fixture_repo(Path(tmp), plans=3)
                run_dir, output = self._initialize(driver, repo)
                queue = json.loads(
                    (run_dir / "state.json").read_text(encoding="utf-8")
                )["queue"]
                self.assertGreater(
                    len(queue),
                    1,
                    "the fixture must queue MORE THAN ONE item, or 'once per run' is "
                    "indistinguishable from 'once per item'",
                )
                self.assertEqual(
                    output.count("UNTRACKED path(s)"),
                    1,
                    f"{name}: the untracked notice must be emitted exactly ONCE for a "
                    f"{len(queue)}-item run; saw {output.count('UNTRACKED path(s)')}",
                )
                calls: list[int] = []
                real = runner_shared.report_untracked_dirt_at_run_start

                def counting(*args, _real=real, _calls=calls, **kwargs):
                    _calls.append(1)
                    return _real(*args, **kwargs)

                def fake_execute(rd, st, item, *a, _driver=driver, **k):
                    item["status"] = "executed"
                    _driver.save_state(rd, st)

                sink = io.StringIO()
                with (
                    mock.patch.object(
                        runner_shared, "report_untracked_dirt_at_run_start", counting
                    ),
                    mock.patch.object(driver, "execute_item", side_effect=fake_execute),
                    contextlib.redirect_stdout(sink),
                    contextlib.redirect_stderr(sink),
                ):
                    driver.run_queue(run_dir, retry_incomplete=False)
                self.assertEqual(
                    calls,
                    [],
                    f"{name}: the report must NOT be reachable from the per-item path; it fired "
                    f"{len(calls)} time(s) while dispatching {len(queue)} items, which is the "
                    "repeat-N-times defect F-11 names",
                )

    def test_the_status_invocation_asks_git_for_EVERY_untracked_file(self):
        """F-12, DRIVEN: git's DEFAULT porcelain collapses an untracked DIRECTORY to one entry.

        REPLACES `assertIn("--untracked-files=all", UNTRACKED_REPORT_STATUS_ARGS)` (audit 2026-09-19),
        which asserted a constant's CONTENTS and said nothing about the constant being USED. Here the
        reporter's injectable `git_runner` records the args it is actually invoked with, and a second
        row feeds it DEFAULT-porcelain output to show the consequence: the 130-file `aw install` case
        would be reported as a handful of directory names.
        """
        recorded: list[list[str]] = []

        def spy(repo, args, **kwargs):
            recorded.append(list(args))
            return (0, "?? newdir/a.txt\n?? newdir/b.txt\n", "")

        report = runner_shared.report_untracked_dirt_at_run_start(
            Path("/nonexistent"), git_runner=spy, stream=io.StringIO()
        )
        self.assertEqual(
            recorded,
            [["status", "--porcelain", "--untracked-files=all"]],
            "the reporter must ASK git for every untracked file; the default porcelain collapses a "
            f"directory to one entry. Observed invocation: {recorded}",
        )
        self.assertEqual(report.total, 2, "both files must be counted individually")

        def collapsing(repo, args, **kwargs):
            return (0, "?? newdir/\n", "")

        collapsed = runner_shared.report_untracked_dirt_at_run_start(
            Path("/nonexistent"), git_runner=collapsing, stream=io.StringIO()
        )
        self.assertEqual(
            (collapsed.total, collapsed.sample),
            (1, ("newdir/",)),
            "THE CONSEQUENCE ROW, which is what makes the assertion above load-bearing: fed "
            "DEFAULT-porcelain output the report counts ONE directory where the tree holds many "
            "files, so a 130-file pollution event would read as a handful of names",
        )

    #: (case, files to create in the fixture tree (None == no repository at all), expected `total`,
    #: paths that must be NAMED in the report, text that must NOT appear in the emitted stream,
    #: must the stream be EMPTY, why this row exists)
    EMISSIONS = (
        (
            "an untracked DIRECTORY holding three files",
            ("newdir/f0.txt", "newdir/f1.txt", "newdir/f2.txt"),
            3,
            ("newdir/f0.txt", "newdir/f1.txt", "newdir/f2.txt"),
            ("newdir/\n",),
            False,
            "F-12 AS BEHAVIOR ON A REAL REPOSITORY, which is the case the whole `--untracked-files=all` "
            "argument exists for: git's DEFAULT porcelain collapses this to the single entry "
            "`?? newdir/`, so the measured 130-file `aw install` event would have been reported as a "
            "handful of DIRECTORY NAMES and an operator could not tell how much was there",
        ),
        (
            "one stray untracked file",
            ("scratch.log",),
            1,
            ("scratch.log",),
            (),
            False,
            "THE ORDINARY CASE, and the asymmetry this file defends: untracked content is REPORTED and "
            "the run PROCEEDS. Refusing here would make an unattended run unstartable in essentially "
            "any real checkout and would train operators to pass the consent flag reflexively",
        ),
        (
            "a clean tree",
            (),
            0,
            (),
            (),
            True,
            "SILENCE ON A CLEAN TREE. A report that always fires is a report nobody reads, so this row "
            "is what protects the signal value of the row above",
        ),
        (
            "a path that is not a git repository at all",
            None,
            0,
            (),
            (),
            True,
            "A REPORT MUST NEVER FAIL A RUN. Raising here would make this the tracked GUARD in "
            "disguise: failing a run over an inability to DESCRIBE untracked content is strictly worse "
            "than the silence it replaces, and question (2) already fails closed on an unreadable tree",
        ),
    )

    def test_the_report_emits_the_right_thing_for_every_tree_shape(self):
        wrong: list[str] = []
        for case, files, total, named, forbidden, silent, why in self.EMISSIONS:
            stream = io.StringIO()
            problems: list[str] = []
            with TemporaryDirectory() as tmp:
                if files is None:
                    target = Path(tmp) / "not-a-repo"
                else:
                    target = _init_repo(Path(tmp))
                    for rel in files:
                        path = target / rel
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text("x\n", encoding="utf-8")
                try:
                    report = runner_shared.report_untracked_dirt_at_run_start(
                        target, stream=stream
                    )
                except Exception as exc:  # noqa: BLE001 - the point of the last row
                    problems.append(
                        f"the report RAISED {type(exc).__name__}: {exc}. It must never fail a run"
                    )
                    report = None
            if report is not None:
                if report.total != total:
                    problems.append(
                        f"expected total={total}, got {report.total} (sample {report.sample!r})"
                    )
                for path in named:
                    if path not in report.sample:
                        problems.append(
                            f"{path!r} must be NAMED individually in the report sample; got "
                            f"{report.sample!r}"
                        )
                if (report.total == 0) is not report.clean:
                    problems.append(
                        f"`clean` ({report.clean}) disagrees with `total` ({report.total}); the two "
                        "must never diverge or callers branch on different answers"
                    )
            emitted = stream.getvalue()
            if silent and emitted != "":
                problems.append(f"the stream must be EMPTY; emitted {emitted!r}")
            if not silent and not emitted:
                problems.append(
                    "the stream must carry the notice; nothing was emitted, so the operator is told "
                    "nothing about real pollution"
                )
            for banned in forbidden:
                if banned in emitted:
                    problems.append(
                        f"{banned!r} must NOT appear in the emitted notice; its presence means the "
                        "directory was reported instead of its files"
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
            f"the run-start report is wrong for {len(wrong)} of {len(self.EMISSIONS)} tree shapes. "
            "THE SILENT ROWS AND THE REPORTING ROWS SHARE THIS TABLE, and the two failure directions "
            "are opposite: a report that always fires satisfies the reporting rows while becoming "
            "noise an operator learns to skip, and one that never fires satisfies the silent rows "
            "while restoring the exact silence this feature exists to end. The LAST ROW is different "
            "in kind -- it must not RAISE -- because a report that can fail a run is the tracked guard "
            "in disguise. FIX: never relax a row to green.\n" + "\n".join(wrong),
        )


# ======================================================================================================
# E-03: the `--no-isolate-worktree` guard
# ======================================================================================================
class SharedTreeGuardRuleTests(unittest.TestCase):
    """The message variant, and the proof it is a variant rather than a rewrite."""

    def test_the_shared_tree_reason_is_TRUE_for_a_shared_tree(self):
        """F-9: the lane wording says "isolated turn" and blames a lane for OMITTING the paths.
        Neither clause is true of a `--no-isolate-worktree` run."""
        result = lane_containment.evaluate_clean_base(" M a.py\n", shared_tree=True)
        self.assertFalse(result.clean)
        self.assertNotIn("isolated turn", result.reason)
        self.assertNotIn("silently omit", result.reason)
        self.assertIn("SHARES this checkout", result.reason)
        self.assertIn("a.py", result.reason)

    def test_the_shared_tree_reason_names_a_remedy_the_operator_may_apply(self):
        """`z2isfg`'s wording discipline: name a real remedy, never touch un-owned work."""
        reason = lane_containment.evaluate_clean_base(
            " M a.py\n", shared_tree=True
        ).reason
        self.assertIn("--no-isolate-worktree", reason)
        self.assertIn("do NOT touch their work", reason)
        for forbidden in ("git stash", "git reset", "git clean", "--force"):
            self.assertNotIn(forbidden, reason)

    def test_the_ISOLATED_reason_is_DISTINCT_and_names_the_paths(self):
        """What proved E-03 relaxed a CONDITION rather than rewriting a RULE: the two paths differ.

        RETARGETED 2026-09-16 by dirtygates Order 01 (`d7qoxv`) E-05, which amended spec R5.4 so the
        ISOLATED path REPORTS instead of refusing. This test previously pinned the isolated refusal
        SENTENCE byte-for-byte; that exact sentence is what `d7qoxv` replaces, so asserting it now
        asserts behavior the amended spec FORBIDS.

        WHAT E-03's PROOF ACTUALLY NEEDED, and what is preserved here: that the shared-tree variant is
        a VARIANT reached through the ONE shared rule, not a second rule, and that the two paths are
        distinguishable. Both are still asserted - the isolated sentence still names every dirty path
        and is still NOT the shared-tree sentence - so the property this test defends survives the
        amendment. The classification half is pinned by
        `test_the_tracked_scope_is_IDENTICAL_on_both_paths` below, which needed no change at all.
        """
        result = lane_containment.evaluate_clean_base(" M a.py\nM  b.py\n")
        self.assertFalse(result.clean)
        self.assertIn("a.py", result.reason)
        self.assertIn("b.py", result.reason)
        self.assertIn("2 dirty TRACKED path(s)", result.reason)
        # The isolated path REPORTS (`d7qoxv`): it is not the shared-tree refusal sentence.
        self.assertFalse(result.refuses)
        self.assertNotIn("SHARES this checkout", result.reason)
        self.assertNotIn("refusing to launch", result.reason)

    def test_the_default_is_the_isolated_wording(self):
        """Additive: every pre-existing call still gets the ISOLATED sentence, not the shared one.

        The wording it checks for was updated with `d7qoxv`'s amendment (the isolated sentence no
        longer says "refusing"), but the property is the original one: `shared_tree` defaults to False,
        so an un-flagged call keeps the isolated meaning.
        """
        reason = lane_containment.evaluate_clean_base(" M a.py\n").reason
        self.assertIn("isolated turn", reason)
        self.assertNotIn("SHARES this checkout", reason)

    def test_the_tracked_scope_is_IDENTICAL_on_both_paths(self):
        """OQ-01: only the MESSAGE differs. The clean/dirty verdict does not."""
        for porcelain in ("", " M a.py\n", "M  b.py\nR  c -> d\n"):
            isolated = lane_containment.evaluate_clean_base(porcelain)
            shared = lane_containment.evaluate_clean_base(porcelain, shared_tree=True)
            with self.subTest(porcelain=porcelain):
                self.assertEqual(isolated.clean, shared.clean)
                self.assertEqual(isolated.dirty_paths, shared.dirty_paths)

    def test_untracked_only_does_not_refuse_on_EITHER_path(self):
        """OQ-01, resolved by the maintainer: untracked content REPORTS and refuses on nothing.

        THE CASE MOST LIKELY TO BE "FIXED" WRONGLY. A refusal here would mean the tracked-only rule
        was silently widened, making `--no-isolate-worktree` nearly unusable in any real checkout and
        training operators to pass `--allow-dirty-base` reflexively.
        """
        with TemporaryDirectory() as tmp:
            repo = _init_repo(Path(tmp))
            (repo / "scratch.log").write_text("noise\n", encoding="utf-8")
            (repo / "notes.md").write_text("notes\n", encoding="utf-8")
            for name, driver, _spawn in DRIVERS:
                for shared in (False, True):
                    with self.subTest(driver=name, shared_tree=shared):
                        result = driver.evaluate_clean_base_for_launch(
                            repo, shared_tree=shared
                        )
                        self.assertTrue(result.clean, result.reason)

    def test_a_dirty_tracked_shared_tree_refuses_on_BOTH_hosts(self):
        with TemporaryDirectory() as tmp:
            repo = _init_repo(Path(tmp))
            (repo / "tracked.txt").write_text("v2\n", encoding="utf-8")
            for name, driver, _spawn in DRIVERS:
                with self.subTest(driver=name):
                    result = driver.evaluate_clean_base_for_launch(
                        repo, shared_tree=True
                    )
                    self.assertFalse(result.clean)
                    self.assertIn("tracked.txt", result.dirty_paths)
                    self.assertIn("tracked.txt", result.reason)
                    self.assertNotIn("isolated turn", result.reason)

    def test_no_SECOND_predicate_and_no_SECOND_git_status_were_added(self):
        """E-03's required shape: the EXISTING guard reached by a RELAXED condition.

        DRIVEN, NOT READ (audit 2026-09-19). This previously counted `_run_git(` occurrences in a
        function's SOURCE and searched it for `lane_containment.evaluate_clean_base(` and
        `--untracked-files=no`. All three are satisfiable by a comment and all three break on a
        reformat; worse, a source count of `_run_git(` says nothing about how many git calls actually
        HAPPEN (a call inside a loop counts once and runs N times).

        WHAT REPLACES THEM, each half stronger than the text it replaces:
          * ONE GIT CALL is measured by patching each host's `_run_git` with a spy and counting
            invocations, which is the real quantity the pin was standing in for;
          * THE ARGS are read off that spy, so `--untracked-files=no` is asserted as an argument really
            passed rather than as a substring present somewhere in the body;
          * DELEGATION is proved by patching the shared rule to return a SENTINEL and asserting the
            host returns that very object (`assertIs`). A host that re-decided the verdict itself could
            not return the sentinel, so no second predicate can hide behind agreement-today.

        THE GIT SPY IS INSTALLED ON `runner_shared` AS WELL AS ON THE DRIVER (hostdedup Order 01,
        `li44r9`, E-07). `evaluate_clean_base_for_launch` was byte-identical in both drivers and now has
        ONE definition in `runner_shared`, so the `_run_git` that performs the call is that module's.
        Patching only the driver's left the real git running against `/nonexistent`. EVERY ASSERTION
        BELOW IS UNCHANGED, including the one-call count and the argument check: the spy still observes
        the single real call, just in the module that now makes it. The driver's own `_run_git` stays
        patched too, so a host that re-grew its own git call would still be counted.
        """
        for name, driver, _spawn in DRIVERS:
            with self.subTest(driver=name):
                sentinel = object()
                git_calls: list[list[str]] = []
                rule_calls: list[tuple[str, bool]] = []

                def spy_git(repo, args, _seen=git_calls, **kwargs):
                    _seen.append(list(args))
                    return (0, " M a.py\n", "")

                def spy_rule(
                    porcelain, *, shared_tree=False, _seen=rule_calls, _out=sentinel
                ):
                    _seen.append((porcelain, shared_tree))
                    return _out

                with (
                    mock.patch.object(driver, "_run_git", spy_git),
                    mock.patch.object(runner_shared, "_run_git", spy_git),
                    mock.patch.object(
                        lane_containment, "evaluate_clean_base", spy_rule
                    ),
                ):
                    verdict = driver.evaluate_clean_base_for_launch(
                        Path("/nonexistent"), shared_tree=True
                    )
                self.assertEqual(
                    len(git_calls),
                    1,
                    f"{name}: the guard must make EXACTLY ONE git call; it made {len(git_calls)} "
                    f"({git_calls}). A second `git status` means a second predicate was added beside "
                    "the shared rule rather than the existing one being reached by a relaxed "
                    "condition",
                )
                self.assertIn(
                    "--untracked-files=no",
                    git_calls[0],
                    f"{name}: the guard's scope must be TRACKED content only; without this argument "
                    "it would refuse on untracked dirt, which is the asymmetry this file exists to "
                    f"defend. Observed args: {git_calls[0]}",
                )
                self.assertIs(
                    verdict,
                    sentinel,
                    f"{name}: the verdict must come STRAIGHT from the one shared rule. Returning "
                    "anything else means this host computes its own answer, which is how the two "
                    "hosts drift on a containment guarantee (CID-3)",
                )
                self.assertEqual(
                    rule_calls,
                    [(" M a.py\n", True)],
                    f"{name}: the host must hand the shared rule git's UNMODIFIED porcelain and pass "
                    f"`shared_tree` THROUGH without interpreting it; saw {rule_calls}",
                )


class SharedTreeGuardWiringTests(unittest.TestCase):
    """The condition itself: `isolate` no longer gates the call."""

    def test_the_guard_runs_in_BOTH_isolation_modes_with_shared_tree_derived_from_isolate(
        self,
    ):
        """E-03's condition, DRIVEN in both modes rather than read out of the source (audit 2026-09-19).

        WHAT WAS DELETED: `assertNotIn("if isolate and self_finalize and not is_review:", body)` plus
        `assertIn("shared_tree=not isolate", body)`. The first is the most fragile shape in this file --
        a byte-exact copy of one line of product source, including its spacing and its colon, so any
        reformat or added condition breaks it while the behavior is unchanged. Neither says the guard
        actually RUNS.

        WHAT REPLACES IT: the guard is patched with a spy on a real `execute_item` turn and the value of
        `shared_tree` it RECEIVES is recorded, in both isolation modes. The defect being prevented is
        that a `--no-isolate-worktree` run skipped the guard ENTIRELY (its call site was gated on `if
        isolate and ...`), so "the guard was called at all when isolate=False" is the load-bearing half,
        and no source search can establish it.
        """
        wrong: list[str] = []
        # (isolate option, the `shared_tree` value the guard must be handed, why this row exists)
        modes = (
            (
                False,
                True,
                "THE CASE THAT WAS UNGUARDED, and the most dangerous one: the agent writes directly "
                "into the tree it is polluting. Its call site used to be gated on `if isolate`, so the "
                "guard did not run AT ALL here. `shared_tree=True` is what selects the refusal sentence "
                "that is TRUE for a shared tree (the lane wording blames a lane for omitting paths, "
                "which is false of this mode)",
            ),
            (
                True,
                False,
                "THE PRE-EXISTING CASE, which must keep its ISOLATED meaning. If `shared_tree` were "
                "hardcoded True, every isolated turn would get the shared-tree sentence and (per spec "
                "R5.4's split) would REFUSE where it should report, so this row is what keeps the "
                "relaxation additive rather than a behavior change for existing runs",
            ),
        )
        for name, driver, spawn in DRIVERS:
            for isolate, expected_shared_tree, why in modes:
                observed: list[bool] = []
                real = driver.evaluate_clean_base_for_launch

                def spy(repo, *, shared_tree=False, _real=real, _seen=observed):
                    _seen.append(shared_tree)
                    return _real(repo, shared_tree=shared_tree)

                with TemporaryDirectory() as tmp:
                    _repo, run_dir, state, item = _clean_base_fixture(
                        Path(tmp), isolate=isolate
                    )
                    _drive_execute_item(
                        driver,
                        spawn,
                        run_dir,
                        state,
                        item,
                        extra_patches=(
                            (driver, "evaluate_clean_base_for_launch", spy),
                        ),
                    )
                problems: list[str] = []
                if not observed:
                    problems.append(
                        "the clean-base guard was NEVER CALLED on this turn, which is the original "
                        "defect: the call site was gated on `if isolate`, so a shared-tree run (the "
                        "case where dirt is most dangerous) was the least guarded"
                    )
                elif observed != [expected_shared_tree]:
                    problems.append(
                        f"expected the guard to be called exactly once with "
                        f"shared_tree={expected_shared_tree}; observed {observed}. `shared_tree` must "
                        "be derived from `isolate` and passed THROUGH, never re-decided"
                    )
                if problems:
                    wrong.append(
                        f"  {name} with isolate_worktree={isolate}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(DRIVERS) * len(modes)} host/isolation combinations wire the "
            "clean-base guard wrongly. BOTH MODES SHARE THIS TABLE because the two failure directions "
            "are opposite: a guard that never runs leaves the shared-tree case unguarded (the original "
            "defect), and a guard always told `shared_tree=True` makes every ISOLATED turn refuse where "
            "spec R5.4 says it must report. FIX: call the guard unconditionally for a self-finalizing "
            "non-review turn and pass `shared_tree=not isolate`.\n" + "\n".join(wrong),
        )

    #: The in-scope path every `BEGIN_SCOPE` row declares in its plan's `Scope-Paths`.
    IN_SCOPE = "agent_workflows/demo.py"
    #: A committed path NO row declares, so dirtying it is dirt begin must ignore.
    OUT_OF_SCOPE = "unrelated_note.txt"

    #: (case, which committed path to dirty, expected exit code, must a receipt exist,
    #: must the refusal name the path, why this row exists)
    BEGIN_SCOPE = (
        (
            "dirt OUTSIDE the plan's Scope-Paths",
            OUT_OF_SCOPE,
            "ok",
            True,
            False,
            "F-8, AND THE REASON THE SHARED-TREE GUARD IS NOT A DUPLICATE: `aw ipd begin` grants "
            "authority over a tree carrying a co-worker's uncommitted edit to an UNRELATED path, by "
            "design (the path-overlap rule that keeps concurrent agents from thrashing each other). So "
            "begin cannot be relied on to notice whole-tree dirt, which is exactly the hole the "
            "`--no-isolate-worktree` guard fills",
        ),
        (
            "dirt INSIDE the plan's Scope-Paths",
            IN_SCOPE,
            "cannot-run",
            False,
            True,
            "THE CONTROL THAT MAKES THE ROW ABOVE A SCOPING RULE RATHER THAN A BROKEN CHECK. Without "
            "it, a begin that ignored ALL dirt would satisfy the out-of-scope row while having lost "
            "its gate entirely. The refusal must also NAME the offending path, because an operator "
            "told only 'the baseline is ambiguous' cannot act",
        ),
    )

    def test_begin_is_still_SCOPE_SCOPED_so_this_guard_is_additional(self):
        """F-8 DRIVEN END TO END through the real `aw ipd begin` (audit 2026-09-19).

        WHAT WAS DELETED. This asserted four substrings: `_frozen_scope_paths(plan_text)` and
        `_baseline_ambiguity(` in begin's source, `dirty_within` in the helper's source, and the word
        "intentionally" in a DOCSTRING. The last is the clearest case in this file of a pin that reads
        prose: a maintainer rewording a docstring would fail it, and a code change that removed the
        scoping entirely while leaving the word would not.

        WHAT REPLACES IT: the real `begin` is called on a fixture repo holding a real approved plan,
        once with dirt OUTSIDE its `Scope-Paths` and once INSIDE, and the two verdicts are required to
        DIFFER. That is the property the substrings stood in for, and a comment cannot produce a
        receipt file. The sibling `test_begin_really_returns_clean_for_out_of_scope_dirt` was FOLDED IN
        here: it drove the predicate directly, which is the same claim one layer down, so the two are
        now the two rows of this table and the assertion is on begin's own exit code.
        """
        from agent_workflows import ipd_lifecycle as lifecycle

        from tests.test_ipd_lifecycle_cli import (
            _commit_all,
            _init_git,
            _ready_plan_text,
            _write_plan,
        )

        expected_codes = {
            "ok": lifecycle.EXIT_OK,
            "cannot-run": lifecycle.EXIT_CANNOT_RUN,
        }
        wrong: list[str] = []
        for case, dirty_path, verdict, receipt, names_path, why in self.BEGIN_SCOPE:
            with TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                _init_git(root)
                plan = _write_plan(
                    root,
                    _ready_plan_text(plan_id="abc123", scope_paths=self.IN_SCOPE),
                    "20260829-demo-01-abc123-demo.ipd.md",
                )
                (root / "agent_workflows").mkdir(parents=True, exist_ok=True)
                (root / self.IN_SCOPE).write_text(
                    "committed = True\n", encoding="utf-8"
                )
                (root / self.OUT_OF_SCOPE).write_text("committed\n", encoding="utf-8")
                _commit_all(root, "base")
                # A CO-WORKER's uncommitted edit, which is the realistic shape of this dirt.
                (root / dirty_path).write_text(
                    "someone_elses_wip = True\n", encoding="utf-8"
                )
                result = lifecycle.begin(
                    root, plan, "opencode/test", timestamp="2026-08-30T00:00:00Z"
                )
                has_receipt = lifecycle.receipt_path_for(root, "abc123").is_file()
            problems: list[str] = []
            if result.exit_code != expected_codes[verdict]:
                problems.append(
                    f"expected exit {expected_codes[verdict]} ({verdict}), got "
                    f"{result.exit_code}; message was {(result.message or '')[:200]!r}"
                )
            if has_receipt is not receipt:
                problems.append(
                    f"expected a receipt to exist={receipt}, got {has_receipt}; the receipt IS the "
                    "execution authority, so this is the observable consequence rather than a "
                    "restatement of the exit code"
                )
            if names_path and dirty_path not in (result.message or ""):
                problems.append(
                    f"the refusal must NAME the offending path {dirty_path!r}; an operator told only "
                    f"that the baseline is ambiguous cannot act. Message: "
                    f"{(result.message or '')[:200]!r}"
                )
            if names_path and "Scope-Paths" not in (result.message or ""):
                problems.append(
                    "the refusal must say it measured the plan's Scope-Paths, or the operator cannot "
                    "tell this gate from the whole-tree one"
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
            f"`aw ipd begin` answered {len(wrong)} of {len(self.BEGIN_SCOPE)} scope cases wrongly. "
            "BOTH ROWS SHARE THIS TABLE DELIBERATELY AND IN OPPOSITE DIRECTIONS: a begin that refused "
            "ALL dirt would satisfy the in-scope row while making this repository's concurrent-agent "
            "workflow unusable AND making the `--no-isolate-worktree` guard a pure duplicate; a begin "
            "that ignored all dirt would satisfy the out-of-scope row while having no gate at all. FIX: "
            "if the out-of-scope row fails, begin's gate has been widened to the whole tree and F-8's "
            "premise for this file's guard is gone -- resolve that deliberately rather than by editing "
            "this table.\n" + "\n".join(wrong),
        )


# ======================================================================================================
# E-05: the consent surface
# ======================================================================================================
class ConsentDecisionTests(unittest.TestCase):
    """The three-way verdict, and the narrowness of what consent covers."""

    def _dirty(self, shared_tree: bool = False) -> Any:
        return lane_containment.evaluate_clean_base(
            " M a.py\n", shared_tree=shared_tree
        )

    def test_a_clean_base_proceeds_without_consent(self):
        decision = runner_shared.clean_base_launch_decision(
            lane_containment.evaluate_clean_base("")
        )
        self.assertEqual(decision.verdict, runner_shared.CLEAN_BASE_PROCEED)
        self.assertFalse(decision.refused)
        self.assertFalse(decision.consented)

    def test_dirty_without_consent_REFUSES(self):
        """RETARGETED to the SHARED-TREE base by `d7qoxv` E-05, which is where the refusal now lives.

        The consent surface exists to override a REFUSAL, and after spec R5.4's path split only the
        shared-tree path refuses. Driving this with the ISOLATED base would now assert a refusal the
        amended spec forbids; the isolated base's verdict is pinned by
        `ConsentIsNotConsultedWhereNothingRefusesTests` below.
        """
        decision = runner_shared.clean_base_launch_decision(
            self._dirty(shared_tree=True)
        )
        self.assertTrue(decision.refused)
        self.assertEqual(decision.dirty_paths, ("a.py",))

    def test_dirty_WITH_consent_proceeds_and_is_labelled_consented(self):
        """RETARGETED to the SHARED-TREE base with its sibling above (`d7qoxv` E-05)."""
        decision = runner_shared.clean_base_launch_decision(
            self._dirty(shared_tree=True), allow_dirty_base=True
        )
        self.assertTrue(decision.consented)
        self.assertFalse(decision.refused)
        self.assertEqual(decision.dirty_paths, ("a.py",))

    def test_the_consent_reason_names_the_paths_and_what_is_NOT_waived(self):
        reason = runner_shared.clean_base_launch_decision(
            self._dirty(shared_tree=True), allow_dirty_base=True
        ).reason
        self.assertIn("a.py", reason)
        self.assertIn("--allow-dirty-base", reason)
        self.assertIn("integration", reason)
        self.assertIn("V-evidence", reason)

    def test_the_refusal_reason_is_the_SHARED_RULES_own(self):
        """Consent adds a verdict; it does not restate what dirty means or how a refusal reads.

        Unchanged by `d7qoxv`: the decision still carries the RULE's own sentence on BOTH paths, which
        is what keeps the wording single-sourced whether it refuses or reports.
        """
        for shared_tree in (False, True):
            base = self._dirty(shared_tree=shared_tree)
            decision = runner_shared.clean_base_launch_decision(base)
            with self.subTest(shared_tree=shared_tree):
                self.assertEqual(decision.reason, base.reason)


class ConsentIsNotConsultedWhereNothingRefusesTests(unittest.TestCase):
    """`d7qoxv` E-05: an ISOLATED dirty base WARNS, and consent is not claimed over it.

    WHY THIS IS A SEPARATE ASSERTION AND NOT A TWEAK TO THE CONSENT TESTS. Reporting `consented` on a
    path that never refused would record that the operator overrode a guard which never fired - a false
    audit entry in the one direction an audit most needs to trust, and it would also destroy the
    consent flag's signal value by making it appear routinely on runs that needed no override.
    """

    def _isolated_dirty(self) -> Any:
        return lane_containment.evaluate_clean_base(" M a.py\n")

    def test_an_isolated_dirty_base_WARNS_rather_than_refusing(self):
        decision = runner_shared.clean_base_launch_decision(self._isolated_dirty())
        self.assertEqual(decision.verdict, runner_shared.CLEAN_BASE_WARN)
        self.assertTrue(decision.warned)
        self.assertFalse(decision.refused)
        self.assertFalse(decision.consented)
        self.assertEqual(decision.dirty_paths, ("a.py",))

    def test_consent_does_not_relabel_a_warning_as_consented(self):
        """`--allow-dirty-base` overrides a refusal; it must not claim credit where none was needed."""
        decision = runner_shared.clean_base_launch_decision(
            self._isolated_dirty(), allow_dirty_base=True
        )
        self.assertEqual(decision.verdict, runner_shared.CLEAN_BASE_WARN)
        self.assertFalse(decision.consented)

    def test_the_verdict_is_read_from_the_RULE_not_decided_per_host(self):
        """R6.1/CID-3: the split lives in `CleanBaseResult.refuses`, and NOTHING else decides it.

        REPLACES `assertIn("base.refuses", source)` (audit 2026-09-19) with the strongest available
        form: a LYING result. `refuses` is fed a value that CONTRADICTS what the shared rule would
        compute for that shape -- an isolated result claiming it refuses, and a shared-tree result
        claiming it does not -- and the decision must follow the FIELD both times. A decision that
        re-derived the split from `shared_tree` (the `if isolate` fork this function exists to prevent,
        and the exact route by which `--full-auto` came to mean opt-in on one runner and opt-out on the
        other) would follow the shape instead and fail here. A source search could never tell the two
        apart, since both spellings mention the same names.
        """
        # The real rule's own answers first, so the contradictions below are known to BE contradictions.
        self.assertFalse(self._isolated_dirty().refuses)
        self.assertTrue(self._dirty_shared().refuses)
        self.assertFalse(lane_containment.evaluate_clean_base("").refuses)

        class _Lying:
            """A result whose `refuses` disagrees with what its `shared_tree` would imply."""

            clean = False
            dirty_paths = ("a.py",)
            reason = "a fake reason, single-sourced from the rule in real life"

            def __init__(self, shared_tree: bool, refuses: bool) -> None:
                self.shared_tree = shared_tree
                self.refuses = refuses

        refusing_isolated = runner_shared.clean_base_launch_decision(
            _Lying(shared_tree=False, refuses=True)
        )
        self.assertEqual(
            refusing_isolated.verdict,
            runner_shared.CLEAN_BASE_REFUSE,
            "the decision must follow the RULE's `refuses` field. An ISOLATED result that says it "
            "refuses must REFUSE; reaching `warn` here means the decision re-derived the split from "
            "`shared_tree` itself, which is the per-host fork R6.1/CID-3 forbids",
        )
        warning_shared = runner_shared.clean_base_launch_decision(
            _Lying(shared_tree=True, refuses=False)
        )
        self.assertEqual(
            warning_shared.verdict,
            runner_shared.CLEAN_BASE_WARN,
            "and the other direction: a SHARED-TREE result that says it does not refuse must WARN. "
            "Both directions are needed, because a decision hardcoded to either verdict would satisfy "
            "one of them alone",
        )

    def test_the_hosts_CONSUME_the_warn_verdict_rather_than_re_deciding_it(self):
        """The other half of CID-3: each host must ACT on the decision's `warned` flag.

        REPLACES `assertIn("decision.warned", body)` (audit 2026-09-19). Driven on a real turn over an
        ISOLATED dirty base, where the shipped behavior is to REPORT and LAUNCH: the observable
        consequence is that the attempt records the warning and the paths, which is what an operator
        reads. A host that ignored `warned` would launch silently and record nothing, and the source
        search could not tell that from a mention in a comment.
        """
        for name, driver, spawn in DRIVERS:
            with self.subTest(driver=name), TemporaryDirectory() as tmp:
                repo, run_dir, state, item = _clean_base_fixture(
                    Path(tmp), isolate=True
                )
                (repo / "tracked.txt").write_text("someone else\n", encoding="utf-8")
                spawns = _drive_execute_item(driver, spawn, run_dir, state, item)
                self.assertGreaterEqual(
                    spawns, 1, f"{name}: an isolated dirty base must still LAUNCH"
                )
                attempt = item["attempts"][-1]
                self.assertIn(
                    "clean_base_warning",
                    attempt,
                    f"{name}: the host must consume the decision's WARN verdict and record it. "
                    "Without this the run launches over a dirty base in silence, which removes the "
                    "operator's only signal",
                )
                self.assertIn("tracked.txt", attempt["clean_base_dirty_paths"])
                self.assertNotIn(
                    "clean_base_consented",
                    attempt,
                    f"{name}: nothing refused, so consent must NOT be claimed",
                )

    def _dirty_shared(self) -> Any:
        return lane_containment.evaluate_clean_base(" M a.py\n", shared_tree=True)


class ConsentFlagSurfaceTests(unittest.TestCase):
    """One table row, one default, both hosts. And a spec declaration in the same change."""

    def test_the_row_exists_with_the_fields_E05_requires(self):
        row = runner_shared.RUN_POLICY_FLAGS_BY_FLAG["--allow-dirty-base"]
        self.assertEqual(row.dest, "allow_dirty_base")
        self.assertEqual(row.kind, "bool")
        self.assertTrue(
            row.implemented,
            "`implemented=False` would make the flag REFUSE rather than consent",
        )
        self.assertTrue(row.freeze)
        self.assertEqual(row.resume_rule, runner_shared.RESUME_NONE_DEFAULT)
        self.assertIn("clean_base_launch_decision", row.owner)

    def test_it_is_registered_on_BOTH_hosts_with_ONE_default(self):
        """The `--full-auto` divergence is the measured failure being prevented."""
        defaults = set()
        for name, driver, _spawn in DRIVERS:
            parser = driver.build_parser()
            sub = [
                a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
            ][0].choices["start"]
            options = {opt for a in sub._actions for opt in a.option_strings}
            with self.subTest(driver=name):
                self.assertIn("--allow-dirty-base", options)
                self.assertIn("--no-allow-dirty-base", options)
                self.assertIn("--allow-dirty-base", sub.format_help())
            for action in sub._actions:
                if "--allow-dirty-base" in action.option_strings:
                    defaults.add(action.default)
        self.assertEqual(
            defaults, {False}, f"hosts disagree on the default: {defaults}"
        )

    def test_NEITHER_driver_hand_registers_it(self):
        """Hand-registering on a parser is precisely how `--full-auto` diverged.

        REPLACES two `assertNotIn` searches over each driver's whole 7000-line source (audit
        2026-09-19), which could only say the quoted flag name was not TYPED -- so a mention in a
        comment failed them, and a hand-registration spelled with a variable would have passed.

        WHAT REPLACES THEM, and why it is the strongest available shape for a "single source" claim: the
        shared `RUN_POLICY_FLAGS` table is patched with the row REMOVED, and both hosts' parsers are
        then required to STOP offering the flag. A host that registered it by hand would keep it, which
        is the divergence being prevented. It also proves the positive direction (the shared table is
        genuinely what puts the flag there) in the same measurement.
        """
        without_row = tuple(
            row
            for row in runner_shared.RUN_POLICY_FLAGS
            if row.flag != "--allow-dirty-base"
        )
        self.assertEqual(
            len(without_row),
            len(runner_shared.RUN_POLICY_FLAGS) - 1,
            "the shared table must really hold exactly one `--allow-dirty-base` row, or this "
            "measurement proves nothing",
        )
        with mock.patch.object(runner_shared, "RUN_POLICY_FLAGS", without_row):
            for name, driver, _spawn in DRIVERS:
                with self.subTest(driver=name):
                    parser = driver.build_parser()
                    sub = [
                        a
                        for a in parser._actions
                        if isinstance(a, argparse._SubParsersAction)
                    ][0].choices["start"]
                    options = {opt for a in sub._actions for opt in a.option_strings}
                    self.assertNotIn(
                        "--allow-dirty-base",
                        options,
                        f"{name} still offers --allow-dirty-base with the shared table's row removed, "
                        "so it registers the flag ITSELF. Hand-registering on a parser is exactly how "
                        "`--full-auto` came to mean opt-in on one runner and opt-out on the other",
                    )

    def test_the_spec_DECLARES_it_in_2_1s_run_stanza(self):
        """A flag registered without a spec declaration fails the contract test, and vice versa.

        Left alone (audit 2026-09-19): it borrows ANOTHER test file's parser, which is setup no sibling
        shares, and its subject is the SPEC document rather than either host's behavior.

        Read through the CONTRACT TEST'S OWN parser rather than by eye: its stanza scoping decides
        the answer, so a declaration outside the `run <selector>` stanza would not count.
        """
        from tests.test_run_flag_surface import SpecFlagListTests

        # Borrow the contract test's PARSER, not one of its test methods. unittest requires a real
        # method name to instantiate a TestCase, and naming a specific one couples this file to that
        # file's method names: a rename there raised ValueError here and broke a test about a flag,
        # for a reason that had nothing to do with the flag. `spec_grammar_flags` is the helper being
        # borrowed, and it is a stable public-ish name, so use it as the placeholder.
        declared = SpecFlagListTests("spec_grammar_flags")
        self.assertIn(
            "--allow-dirty-base",
            declared.spec_grammar_flags(),
            "spec 2.1's `run <selector>` stanza must DECLARE --allow-dirty-base. Read through the "
            "contract test's own parser rather than by eye, because its stanza scoping decides the "
            "answer: a declaration outside that stanza does not count",
        )

    def test_it_is_FROZEN_into_run_state(self):
        """Left alone: its setup (a synthetic Namespace over the whole flag table) is materially
        different from every sibling, which drives a parser or the shared rule."""
        base: dict[str, Any] = {
            row.dest: False for row in runner_shared.RUN_POLICY_FLAGS
        }
        base["retry_budget"] = None
        base["allow_dirty_base"] = True
        frozen = runner_shared.freeze_run_policy_flags(argparse.Namespace(**base))
        self.assertIs(frozen["allow_dirty_base"], True)

    def test_consent_does_NOT_suppress_the_untracked_report(self):
        """Consenting to proceed is not a request to be told less.

        THE SIGNATURE CHECKS ARE KEPT (they inspect a real `Signature` object, not source text, so a
        comment cannot satisfy them), and the source searches beside them are REPLACED by behavior
        (audit 2026-09-19): the report is DRIVEN over a tree that is dirty in BOTH senses, once with
        consent frozen on and once off, and its output must be identical. That is the property the
        search stood in for, and unlike the search it would catch suppression implemented through
        module state or a keyword the search did not name.
        """
        self.assertNotIn(
            "allow_dirty_base",
            inspect.signature(
                runner_shared.report_untracked_dirt_at_run_start
            ).parameters,
            "the report must take no consent input at all; a flag it cannot see is a flag that "
            "cannot silence it",
        )
        emitted: list[str] = []
        for consent in (False, True):
            with TemporaryDirectory() as tmp:
                repo, _run_dir, _state, _item = _clean_base_fixture(
                    Path(tmp), isolate=False, consent=consent
                )
                (repo / "stray.log").write_text("noise\n", encoding="utf-8")
                (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
                stream = io.StringIO()
                report = runner_shared.report_untracked_dirt_at_run_start(
                    repo, stream=stream
                )
                self.assertFalse(
                    report.clean,
                    "the fixture must really be dirty, or this proves nothing",
                )
                emitted.append(stream.getvalue())
        self.assertEqual(
            emitted[0],
            emitted[1],
            "the untracked report must be BYTE-IDENTICAL with and without `--allow-dirty-base` "
            "frozen on. Consenting to launch over a dirty base is not a request to be told less, and "
            "a report that quietened itself under consent would hide the pollution case this report "
            f"exists for. Without consent: {emitted[0]!r}; with: {emitted[1]!r}",
        )

    def test_consent_does_NOT_reach_the_integration_time_overlap_refusal(self):
        """That check protects a DIFFERENT party's work at a DIFFERENT time; not this flag's to waive.

        THE SIGNATURE CHECK IS KEPT (a real `Signature`, not source text). The
        `assertNotIn("allow_dirty_base", getsource(integrate_lane_branch))` beside it is REPLACED by
        driving `dirty_tree_overlap` itself: consent is frozen ON and the overlap predicate must STILL
        report the overlap, which is the property. The search could not have distinguished the
        parameter being absent from it being read out of module state.
        """
        self.assertNotIn(
            "allow_dirty_base",
            inspect.signature(runner_shared.dirty_tree_overlap).parameters,
            "the integration-time overlap check must take no consent input; it guards ANOTHER "
            "party's uncommitted work, which this run's operator has no standing to waive",
        )
        with TemporaryDirectory() as tmp:
            repo, _run_dir, _state, _item = _clean_base_fixture(
                Path(tmp), isolate=False, consent=True
            )
            (repo / "tracked.txt").write_text(
                "a third party's edit\n", encoding="utf-8"
            )
            overlap = runner_shared.dirty_tree_overlap(repo, ["tracked.txt"])
            self.assertTrue(
                overlap,
                "with `--allow-dirty-base` frozen ON, an overlapping dirty path must STILL be "
                "reported by the integration-time check. Consent covers launching this run over a "
                f"dirty base and nothing else. Got {overlap!r}",
            )


# ======================================================================================================
# The guard fires BEFORE any spawn, and touches nothing
# ======================================================================================================


class NoSpawnAndNothingTouchedTests(unittest.TestCase):
    """The load-bearing behavioral proof: the refusal PRECEDES the spawn, and dirt is left alone.

    HOW THIS IS STRONGER THAN THE SHIPPED PRECEDENT, and why both are kept. `tests/
    test_lane_clean_base.py:158-190` establishes ordering STRUCTURALLY, by comparing `body_text.find`
    positions inside `execute_item`, and says why. A structural assertion is acceptable for the
    ORDERING claim but cannot show the guard actually FIRED. So the spawn is PATCHED here and
    asserted never called, which establishes firing; the structural test is kept separately below for
    the ordering claim.
    """

    def _fixture(self, tmp: Path, isolate: bool, consent: bool = False):
        """The shared module-level fixture; kept as a method so every call site below is untouched."""
        return _clean_base_fixture(tmp, isolate=isolate, consent=consent)

    def _tree_snapshot(self, repo: Path) -> tuple[str, str]:
        return (
            _git(repo, "status", "--porcelain", "--untracked-files=all"),
            _git(repo, "stash", "list"),
        )

    def _drive(self, driver, spawn_name, run_dir, state, item):
        """Run `execute_item` with the spawn and the lifecycle patched; return spawn call count."""
        return _drive_execute_item(driver, spawn_name, run_dir, state, item)

    def test_a_shared_tree_run_over_dirty_tracked_paths_refuses_BEFORE_any_spawn(self):
        for name, driver, spawn in DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                repo, run_dir, state, item = self._fixture(Path(tmp), isolate=False)
                (repo / "tracked.txt").write_text("someone else\n", encoding="utf-8")
                before = self._tree_snapshot(repo)

                spawns = self._drive(driver, spawn, run_dir, state, item)

                self.assertEqual(spawns, 0, "the guard did not fire before the spawn")
                self.assertEqual(item["status"], "blocked")
                self.assertIn("tracked.txt", item["clean_base_refusal"])
                # The message is shared-tree-correct, not the lane's.
                self.assertNotIn("isolated turn", item["clean_base_refusal"])
                self.assertIn("SHARES this checkout", item["clean_base_refusal"])
                # NOTHING WAS TOUCHED: byte-identical status, no stash entry created.
                self.assertEqual(self._tree_snapshot(repo), before)

    def test_the_refusal_is_recorded_as_an_EVENT_on_both_hosts(self):
        for name, driver, spawn in DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                repo, run_dir, state, item = self._fixture(Path(tmp), isolate=False)
                (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
                self._drive(driver, spawn, run_dir, state, item)
                events = [
                    json.loads(line)
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                    if line.strip()
                ]
                refusals = [e for e in events if e.get("event") == "clean-base-refused"]
                self.assertEqual(len(refusals), 1, events)
                self.assertEqual(refusals[0]["dirty_paths"], ["tracked.txt"])

    def test_the_SAME_run_PROCEEDS_with_allow_dirty_base(self):
        for name, driver, spawn in DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                repo, run_dir, state, item = self._fixture(
                    Path(tmp), isolate=False, consent=True
                )
                (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")

                spawns = self._drive(driver, spawn, run_dir, state, item)

                # RE-MEASURED 2026-09-14 when lane `b7xarm` (defreport-01) was integrated. This
                # asserted `== 1`; the property it exists to pin is that the clean-base guard
                # LAUNCHED the turn instead of refusing before any spawn (the `== 0` cases above),
                # so the bound is `>= 1`, not a spawn count. `b7xarm` adds ONE bounded same-session
                # re-ask when a turn returns no conforming defect report, and this fixture's fake
                # spawn returns none, so a second launch here is that re-ask working as designed
                # (`runner_shared.defect_reask_is_warranted`). It fires only because the fake's
                # disposition is `partial`; every refusal case in this class keeps `== 0` because
                # `blocked` is in `DEFECT_REASK_SKIPPED_STATUSES`, which is what makes this
                # relaxation safe rather than a loosening that would hide a guard regression.
                self.assertGreaterEqual(spawns, 1, "consent must let the turn launch")
                self.assertNotEqual(item["status"], "blocked")
                self.assertNotIn("clean_base_refusal", item)
                # NON-VACUITY. Pre-change this path had NO guard at all (the call was gated on
                # `isolate`), so "it launched" was already true for the WRONG reason. What must be
                # true now is that the guard RAN, SAW the dirt, and was overridden deliberately.
                self.assertIn("clean_base_consented", item["attempts"][-1])
                self.assertEqual(
                    item["attempts"][-1]["clean_base_dirty_paths"], ["tracked.txt"]
                )

    def test_the_CONSENT_is_recorded_as_an_event_naming_the_paths(self):
        for name, driver, spawn in DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                repo, run_dir, state, item = self._fixture(
                    Path(tmp), isolate=False, consent=True
                )
                (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
                self._drive(driver, spawn, run_dir, state, item)
                events = [
                    json.loads(line)
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                    if line.strip()
                ]
                consents = [
                    e for e in events if e.get("event") == "clean-base-consented"
                ]
                self.assertEqual(len(consents), 1, events)
                self.assertEqual(consents[0]["dirty_paths"], ["tracked.txt"])
                self.assertIn("--allow-dirty-base", consents[0]["detail"])

    def test_untracked_only_shared_tree_run_PROCEEDS(self):
        """OQ-01 end to end: untracked dirt must not block a `--no-isolate-worktree` run."""
        for name, driver, spawn in DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                repo, run_dir, state, item = self._fixture(Path(tmp), isolate=False)
                (repo / "stray.log").write_text("noise\n", encoding="utf-8")

                spawns = self._drive(driver, spawn, run_dir, state, item)

                # RE-MEASURED 2026-09-14 with lane `b7xarm`; see the sibling consent test for the
                # full reasoning. `>= 1` because `b7xarm`'s one bounded defect-report re-ask can add
                # a second launch; the property pinned here is that untracked dirt does NOT refuse
                # before the spawn, which the `== 0` refusal cases in this class still hold exactly.
                self.assertGreaterEqual(spawns, 1, "untracked dirt must not refuse")
                self.assertNotIn("clean_base_refusal", item)
                # NON-VACUITY: it must launch because the guard RAN and found the tracked tree
                # clean, not because the guard was skipped. Pre-change this passed for the latter
                # reason, so without this assertion the test could not tell the two apart.
                self.assertNotIn("clean_base_consented", item["attempts"][-1])
                # The `shared_tree=not isolate` source search that used to sit here is REPLACED by
                # `SharedTreeGuardWiringTests::test_the_guard_runs_in_BOTH_isolation_modes_with_
                # shared_tree_derived_from_isolate`, which records the value the guard is actually
                # HANDED on a real turn in both modes.
                self.assertEqual(
                    item["attempts"][-1].get("clean_base_warning"),
                    None,
                    f"{name}: an untracked-only tree is CLEAN by this guard's scope, so there must be "
                    "no warning either; a warning here means the tracked scope was widened to "
                    "untracked content, which is the asymmetry this file exists to defend",
                )

    def test_the_ISOLATED_path_REPORTS_and_LAUNCHES_and_still_touches_nothing(self):
        """RETARGETED 2026-09-16 by dirtygates Order 01 (`d7qoxv`) E-05.

        WHAT THIS USED TO ASSERT, and why it could not stay. It pinned the ISOLATED refusal message
        byte-for-byte, as E-03's proof that it had relaxed a CONDITION rather than rewritten a RULE.
        Spec R5.4 has since been amended to SPLIT that obligation by path: the shared-tree turn is
        still refused (asserted by this class's sibling above, which is unchanged and remains E-03's
        real proof), while an isolated turn is REPORTED and PROCEEDS.

        WHAT IS PRESERVED, because it is the half that was never about the refusal: the guard STILL
        TOUCHES NOTHING. The tree snapshot comparison is kept exactly as it was, so a change that
        launched the turn by stashing, resetting or otherwise disturbing another party's uncommitted
        work still fails here.
        """
        for name, driver, spawn in DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                repo, run_dir, state, item = self._fixture(Path(tmp), isolate=True)
                (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
                before = self._tree_snapshot(repo)

                spawns = self._drive(driver, spawn, run_dir, state, item)

                # LAUNCHED, not refused. `>= 1` for the `b7xarm` re-ask reason this class records.
                self.assertGreaterEqual(spawns, 1, "the isolated turn must launch")
                self.assertNotEqual(item["status"], "blocked")
                self.assertNotIn("clean_base_refusal", item)
                # The paths are still NAMED, in durable state: removing the refusal must not remove
                # the operator's signal.
                attempt = item["attempts"][-1]
                self.assertIn("tracked.txt", attempt["clean_base_dirty_paths"])
                self.assertIn("tracked.txt", attempt["clean_base_warning"])
                # NON-VACUITY: it launched because the guard RAN and reported, not because it was
                # skipped. And consent was NOT claimed, since nothing refused.
                self.assertNotIn("clean_base_consented", attempt)
                # NOTHING WAS TOUCHED, the assertion this test keeps verbatim from before the split.
                self.assertEqual(self._tree_snapshot(repo), before)

    def test_the_guard_PRECEDES_both_the_spawn_and_the_lane_allocation(self):
        """The ordering claim, now recorded as CALL ORDER on a real turn (audit 2026-09-19).

        WHAT WAS DELETED: three `body.find(...)` byte offsets compared inside `execute_item`. This was
        the file's second offset pin, and it had already been re-based once onto `execute_item_core`.

        WHAT REPLACES IT: all three collaborators are patched with spies on a real ISOLATED turn and the
        recorded order is asserted. Both orderings matter for different reasons: BEFORE the ALLOCATION
        because a lane cut from a contaminated base carries the contamination into the lane, and BEFORE
        the SPAWN because a refusal after the agent has launched has already spent the turn.

        HONEST LIMIT, and why the sibling AST guard is not redundant. This observes the ONE path this
        fixture drives. `tests/test_rununify_execute_item_gates.py` asserts the same two orderings on
        the CALL GRAPH, which covers branches no test enters; that is the assurance an offset scan was
        really providing, and it lives there rather than here.
        """
        for name, driver, spawn in DRIVERS:
            with self.subTest(driver=name), TemporaryDirectory() as tmp:
                _repo, run_dir, state, item = _clean_base_fixture(
                    Path(tmp), isolate=True
                )
                recorder = _OrderRecorder()

                # Allocation RAISES, so the turn stops there: that both proves the guard already ran
                # and keeps this fixture from creating a real git worktree.
                def refuse_to_allocate(*_a, _log=recorder.order, **_k):
                    _log.append("allocate")
                    raise RuntimeError("probe: allocation deliberately refused")

                _drive_execute_item(
                    driver,
                    spawn,
                    run_dir,
                    state,
                    item,
                    extra_patches=(
                        (
                            driver,
                            "evaluate_clean_base_for_launch",
                            recorder.wrap(
                                "guard", driver.evaluate_clean_base_for_launch
                            ),
                        ),
                        (driver, "allocate_isolation_worktree", refuse_to_allocate),
                        (
                            driver,
                            spawn,
                            recorder.wrap(
                                "spawn",
                                lambda *_a, _log=str(run_dir / "log"), **_k: (
                                    0,
                                    "ses",
                                    _log,
                                    ["probe"],
                                ),
                            ),
                        ),
                    ),
                )
                self.assertEqual(
                    recorder.order[:2],
                    ["guard", "allocate"],
                    f"{name}: the clean base must be judged BEFORE a lane is allocated from it "
                    "(allocating first branches a worktree off a contaminated base) and before the "
                    f"agent is spawned (a refusal after launch has already spent the turn). Observed "
                    f"call order: {recorder.order}",
                )
                self.assertNotIn(
                    "spawn",
                    recorder.order,
                    f"{name}: with allocation refused the turn must not have reached the spawn, which "
                    "is what shows the guard sits ahead of BOTH",
                )

    def test_neither_driver_RE_IMPLEMENTS_the_consent_decision(self):
        """CID-3: one decision reached from both hosts, never two that merely agree today.

        REPLACES a source search for `clean_base_launch_decision(` plus two `assertNotIn`s on verdict
        constant names (audit 2026-09-19). What replaces them is the strongest form for a "one shared
        decision" claim: the SHARED decision function is patched to return a verdict that CONTRADICTS
        what the real one would produce for this input -- a REFUSAL over an untracked-only (clean) tree
        -- and the host must obey it. A host that reached its own conclusion would launch instead.

        A MEASUREMENT THAT CORRECTED THIS TEST'S FIRST DRAFT, recorded because it strengthens the claim
        rather than weakening it: patching `driver.clean_base_launch_decision` raises AttributeError,
        because NEITHER host has such an attribute at all. The shared core resolves the decision with
        `getattr(driver_module, "clean_base_launch_decision", <shared>)`, and both hosts fall through to
        the shared one. So the patch target is `runner_shared`, and the hosts' lack of the attribute is
        itself asserted below -- which is a strictly better version of the deleted `assertNotIn` on
        constant names, since it inspects the module's real namespace rather than its text.
        """
        for name, driver, _spawn_unused in DRIVERS:
            self.assertNotIn(
                "clean_base_launch_decision",
                vars(driver),
                f"{name} defines its OWN clean_base_launch_decision. Two decisions that agree today "
                "is exactly the CID-3 divergence this asserts against; the shared core already falls "
                "back to the one in `runner_shared`, so a host copy can only diverge",
            )
        for name, driver, spawn in DRIVERS:
            with self.subTest(driver=name), TemporaryDirectory() as tmp:
                repo, run_dir, state, item = _clean_base_fixture(
                    Path(tmp), isolate=False
                )
                (repo / "stray.log").write_text("noise\n", encoding="utf-8")
                forced = runner_shared.CleanBaseDecision(
                    verdict=runner_shared.CLEAN_BASE_REFUSE,
                    dirty_paths=("forced-sentinel.py",),
                    reason="forced refusal injected by the shared decision function",
                )
                spawns = _drive_execute_item(
                    driver,
                    spawn,
                    run_dir,
                    state,
                    item,
                    extra_patches=(
                        (
                            runner_shared,
                            "clean_base_launch_decision",
                            lambda *_a, _out=forced, **_k: _out,
                        ),
                    ),
                )
                self.assertEqual(
                    spawns,
                    0,
                    f"{name}: the host must OBEY the shared decision. This tree is clean by the real "
                    "rule, so launching here means the host re-decided the verdict itself rather than "
                    "consuming the one shared decision (CID-3)",
                )
                self.assertEqual(item["status"], "blocked")
                self.assertEqual(
                    item["clean_base_refusal"],
                    forced.reason,
                    f"{name}: the recorded refusal must be the SHARED decision's own `reason`, "
                    "byte-for-byte, not a locally reconstructed sentence",
                )
                # MEASURED WHILE WRITING THIS (audit 2026-09-19), and the expectation corrected rather
                # than the code: `item["clean_base_refusal"]` holds the REASON only; the decision's
                # `dirty_paths` are recorded on the ATTEMPT, under `clean_base_dirty_paths`. The first
                # draft asserted the paths appeared in the item's refusal string and was simply wrong
                # about where the runner puts them.
                self.assertEqual(
                    item["attempts"][-1]["clean_base_dirty_paths"],
                    list(forced.dirty_paths),
                    f"{name}: the attempt must record the SHARED decision's paths, which is how a "
                    "host that recomputed them would be caught: this tree's real dirty set is EMPTY, "
                    "so only a host consuming the injected decision can report the sentinel",
                )


class HostsAgreeTests(unittest.TestCase):
    """CID-3 stated directly: the two hosts answer every case identically."""

    def test_both_hosts_return_the_same_verdict_throughout(self):
        with TemporaryDirectory() as tmp:
            repo = _init_repo(Path(tmp))
            observed: list[tuple[bool, tuple[str, ...]]] = []

            def snapshot(shared: bool) -> None:
                verdicts = [
                    driver.evaluate_clean_base_for_launch(repo, shared_tree=shared)
                    for _n, driver, _s in DRIVERS
                ]
                self.assertEqual(
                    {(v.clean, v.dirty_paths, v.reason) for v in verdicts},
                    {(verdicts[0].clean, verdicts[0].dirty_paths, verdicts[0].reason)},
                    "hosts disagree",
                )
                observed.append((verdicts[0].clean, verdicts[0].dirty_paths))

            for shared in (False, True):
                snapshot(shared)  # clean
            (repo / "untracked.txt").write_text("x\n", encoding="utf-8")
            for shared in (False, True):
                snapshot(shared)  # untracked only: still clean
            (repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
            for shared in (False, True):
                snapshot(shared)  # dirty tracked: refused

            self.assertEqual(
                [c for c, _p in observed],
                [True, True, True, True, False, False],
                observed,
            )


if __name__ == "__main__":
    unittest.main()
