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
import ast
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


def _effective_execute_item_source(driver, spawn: str | None = None) -> str:
    fn = driver.execute_item if hasattr(driver, "execute_item") else driver
    src = inspect.getsource(fn)
    if "execute_item_core" in src:
        core_src = inspect.getsource(runner_shared.execute_item_core)
        if spawn:
            core_src = core_src.replace("spawn_executor(", f"{spawn}(")
        return core_src
    return src


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
class UntrackedReportRuleTests(unittest.TestCase):
    """The shared RULE, driven by porcelain text so every case is reachable with no repository."""

    def test_a_clean_tree_reports_nothing_to_report(self):
        report = runner_shared.evaluate_untracked_dirt("")
        self.assertTrue(report.clean)
        self.assertEqual(report.total, 0)

    def test_untracked_entries_are_counted_and_sampled(self):
        porcelain = "".join(f"?? f{i}.txt\n" for i in range(30))
        report = runner_shared.evaluate_untracked_dirt(porcelain)
        self.assertFalse(report.clean)
        self.assertEqual(report.total, 30, "the TOTAL is exact, never sampled")
        self.assertEqual(
            len(report.sample),
            runner_shared.UNTRACKED_REPORT_SAMPLE_LIMIT,
            "the ENUMERATION is bounded; a 130-path wall of text is the unread log this replaces",
        )

    def test_tracked_dirt_is_NOT_in_this_report(self):
        """The report answers the UNTRACKED question; tracked dirt is the guard's business."""
        report = runner_shared.evaluate_untracked_dirt(
            " M tracked.py\nM  staged.py\nD  gone.py\n?? new.py\n"
        )
        self.assertEqual(report.total, 1)
        self.assertEqual(report.sample, ("new.py",))

    def test_ignored_entries_are_not_reported_either(self):
        """`!!` is not `??`. An ignored file is not pollution; it is configuration."""
        self.assertTrue(runner_shared.evaluate_untracked_dirt("!! build/\n").clean)

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

    def test_the_rule_holds_NO_porcelain_format_knowledge(self):
        """E-02: reuse a parser, add none. Asserted by AST over the BODY, not by grep over prose.

        There are TWO porcelain parsers at HEAD, not one (finding F-10):
        `lane_containment.parse_porcelain_paths` is the declared-canonical projection and
        `runner_shared.dirty_tree_overlap` still hand-rolls its own. This rule must call into the
        canonical decoder and must not become a third.
        """
        tree = ast.parse(
            inspect.getsource(runner_shared.evaluate_untracked_dirt).lstrip()
        )
        function = tree.body[0]
        assert isinstance(function, ast.FunctionDef)
        body_nodes = [n for stmt in function.body for n in ast.walk(stmt)]
        called = {
            (
                node.func.attr
                if isinstance(node.func, ast.Attribute)
                else getattr(node.func, "id", "")
            )
            for node in body_nodes
            if isinstance(node, ast.Call)
        }
        self.assertIn("parse_porcelain_entries", called)
        for format_token in ("splitlines", "split"):
            self.assertNotIn(
                format_token,
                called,
                "the format is the decoder's to know, not this rule's",
            )

    def test_dirty_tree_overlap_was_NOT_touched(self):
        """The pre-existing duplicate parser (F-10) is deliberately NOT repaired by this plan.

        `runner_shared.py` is in scope, but `dirty_tree_overlap` is the live integration path three
        sibling `integpath` plans are changing, so collapsing it here would collide with them. This
        pins the decision so a later reader sees a choice rather than an oversight.
        """
        source = inspect.getsource(runner_shared.dirty_tree_overlap)
        self.assertIn('entry.split(" -> ", 1)', source)
        self.assertNotIn("parse_porcelain_paths", source)


class UntrackedReportWiringTests(unittest.TestCase):
    """WHERE the report is emitted, which is the half of E-02 most easily got wrong."""

    def test_it_is_called_from_initialize_run_on_BOTH_hosts(self):
        """F-11: `initialize_run` is the once-per-run seam. `execute_item` is once per ITEM."""
        for name, driver, _spawn in DRIVERS:
            with self.subTest(driver=name):
                init = inspect.getsource(driver.initialize_run)
                self.assertIn("report_untracked_dirt_at_run_start", init)
                # And NOT beside the per-item guard, where it would repeat N times.
                self.assertNotIn(
                    "report_untracked_dirt_at_run_start",
                    inspect.getsource(driver.execute_item),
                )

    def test_it_sits_beside_the_shared_preflight_refusals(self):
        """The established both-hosts preflight seam, before the run directory exists."""
        for name, driver, _spawn in DRIVERS:
            with self.subTest(driver=name):
                init = inspect.getsource(driver.initialize_run)
                if "initialize_run_core" in init:
                    init = inspect.getsource(runner_shared.initialize_run_core)
                self.assertLess(
                    init.find("refuse_unimplemented_run_flags"),
                    init.find("report_untracked_dirt_at_run_start"),
                )
                expand_idx = init.find("expand_selectors(")
                if expand_idx < 0:
                    expand_idx = init.find("expand_selectors_fn(")
                self.assertLess(
                    init.find("report_untracked_dirt_at_run_start"),
                    expand_idx,
                    "the report must precede queue resolution",
                )

    def test_the_status_invocation_uses_untracked_files_all(self):
        """F-12: git's DEFAULT porcelain collapses an untracked DIRECTORY to one entry, which would
        report the 130-file `aw install` case as a handful of directory names."""
        self.assertIn(
            "--untracked-files=all", runner_shared.UNTRACKED_REPORT_STATUS_ARGS
        )

    def test_an_untracked_DIRECTORY_is_not_collapsed(self):
        """F-12 as behavior, on a real repository: the FILES are named, not the directory."""
        with TemporaryDirectory() as tmp:
            repo = _init_repo(Path(tmp))
            (repo / "newdir").mkdir()
            for i in range(3):
                (repo / "newdir" / f"f{i}.txt").write_text("x\n", encoding="utf-8")
            stream = io.StringIO()
            report = runner_shared.report_untracked_dirt_at_run_start(
                repo, stream=stream
            )
            self.assertEqual(report.total, 3, report.sample)
            for i in range(3):
                self.assertIn(f"newdir/f{i}.txt", report.sample)
            self.assertNotIn("newdir/\n", stream.getvalue())

    def test_the_report_is_emitted_and_the_run_is_NOT_refused(self):
        with TemporaryDirectory() as tmp:
            repo = _init_repo(Path(tmp))
            (repo / "scratch.log").write_text("noise\n", encoding="utf-8")
            stream = io.StringIO()
            report = runner_shared.report_untracked_dirt_at_run_start(
                repo, stream=stream
            )
            self.assertFalse(report.clean)
            self.assertIn("scratch.log", stream.getvalue())

    def test_a_clean_tree_emits_NOTHING(self):
        """Silence on a clean tree: a report that always fires is a report nobody reads."""
        with TemporaryDirectory() as tmp:
            repo = _init_repo(Path(tmp))
            stream = io.StringIO()
            runner_shared.report_untracked_dirt_at_run_start(repo, stream=stream)
            self.assertEqual(stream.getvalue(), "")

    def test_an_unreadable_tree_does_not_raise(self):
        """A report must never fail a run; that would be the tracked guard in disguise."""
        with TemporaryDirectory() as tmp:
            report = runner_shared.report_untracked_dirt_at_run_start(
                Path(tmp) / "not-a-repo", stream=io.StringIO()
            )
            self.assertTrue(report.clean)


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

        Asserted structurally because "did you add a second predicate?" is a question about code
        shape. Each host's guard helper must still make exactly ONE git call and must still delegate
        the verdict to the one shared rule.
        """
        for name, driver, _spawn in DRIVERS:
            with self.subTest(driver=name):
                source = inspect.getsource(driver.evaluate_clean_base_for_launch)
                if "runner_shared.evaluate_clean_base_for_launch" in source:
                    source = inspect.getsource(
                        runner_shared.evaluate_clean_base_for_launch
                    )
                self.assertEqual(source.count("_run_git("), 1)
                self.assertIn("lane_containment.evaluate_clean_base(", source)
                self.assertIn("--untracked-files=no", source)


class SharedTreeGuardWiringTests(unittest.TestCase):
    """The condition itself: `isolate` no longer gates the call."""

    def test_the_guard_call_is_no_longer_gated_on_isolate(self):
        for name, driver, _spawn in DRIVERS:
            with self.subTest(driver=name):
                body = _effective_execute_item_source(driver)
                self.assertNotIn(
                    "if isolate and self_finalize and not is_review:",
                    body,
                    "the `isolate` condition must be relaxed, not kept",
                )
                self.assertIn("shared_tree=not isolate", body)

    def test_begin_is_still_SCOPE_SCOPED_so_this_guard_is_additional(self):
        """F-8. If `aw ipd begin`'s dirty gate ever became WHOLE-TREE, this guard would be a
        duplicate. It is not: begin returns `clean` for dirt outside a plan's `Scope-Paths` BY
        DESIGN, which is the deliberate path-overlap rule protecting concurrent agents.
        """
        from agent_workflows import ipd_lifecycle, run_evidence

        # The SCOPING happens at begin's call site, which passes the plan's frozen Scope-Paths in.
        begin_source = inspect.getsource(ipd_lifecycle.begin)
        self.assertIn("_frozen_scope_paths(plan_text)", begin_source)
        self.assertIn("_baseline_ambiguity(", begin_source)
        # And the helper delegates the measurement to the path-scoped predicate.
        self.assertIn(
            "dirty_within", inspect.getsource(ipd_lifecycle._baseline_ambiguity)
        )
        self.assertIn(
            "intentionally",
            (run_evidence.dirty_within.__doc__ or ""),
            "begin's narrowness must remain a documented deliberate choice",
        )

    def test_begin_really_returns_clean_for_out_of_scope_dirt(self):
        """The same claim as behavior rather than as a docstring reading."""
        from agent_workflows.ipd_lifecycle import _scope_match
        from agent_workflows.run_evidence import dirty_within

        with TemporaryDirectory() as tmp:
            repo = _init_repo(Path(tmp))
            (repo / "other.txt").write_text("dirty\n", encoding="utf-8")
            _git(repo, "add", "other.txt")
            _git(repo, "commit", "-qm", "add other")
            (repo / "other.txt").write_text("now dirty\n", encoding="utf-8")
            # The SAME matcher begin uses, so this measures begin's real answer.
            self.assertEqual(
                dirty_within(str(repo), ["agent_workflows/foo.py"], _scope_match),
                "clean",
            )
            # And the control: dirt INSIDE the scope is not ignored, which is what makes the
            # narrowness a scoping rule rather than a broken check.
            self.assertNotEqual(
                dirty_within(str(repo), ["other.txt"], _scope_match), "clean"
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
        """R6.1/CID-3: the split lives in `CleanBaseResult.refuses`, which both hosts reach."""
        self.assertFalse(self._isolated_dirty().refuses)
        self.assertTrue(self._dirty_shared().refuses)
        self.assertFalse(lane_containment.evaluate_clean_base("").refuses)
        source = inspect.getsource(runner_shared.clean_base_launch_decision)
        self.assertIn("base.refuses", source)
        # And neither driver re-decides it with its own `isolate` test in the branch.
        for name, driver, _spawn in DRIVERS:
            with self.subTest(driver=name):
                body = _effective_execute_item_source(driver)
                self.assertIn("decision.warned", body)

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
        """Hand-registering on a parser is precisely how `--full-auto` diverged."""
        for name, driver, _spawn in DRIVERS:
            with self.subTest(driver=name):
                source = Path(driver.__file__ or "").read_text(encoding="utf-8")
                self.assertNotIn('"--allow-dirty-base"', source)
                self.assertNotIn("'--allow-dirty-base'", source)

    def test_the_spec_DECLARES_it_in_2_1s_run_stanza(self):
        """A flag registered without a spec declaration fails the contract test, and vice versa.

        Read through the CONTRACT TEST'S OWN parser rather than by eye: its stanza scoping decides
        the answer, so a declaration outside the `run <selector>` stanza would not count.
        """
        from tests.test_run_flag_surface import SpecFlagListTests

        declared = SpecFlagListTests("test_no_owned_flag_is_absent_from_the_spec")
        self.assertIn("--allow-dirty-base", declared.spec_grammar_flags())

    def test_it_is_FROZEN_into_run_state(self):
        base: dict[str, Any] = {
            row.dest: False for row in runner_shared.RUN_POLICY_FLAGS
        }
        base["retry_budget"] = None
        base["allow_dirty_base"] = True
        frozen = runner_shared.freeze_run_policy_flags(argparse.Namespace(**base))
        self.assertIs(frozen["allow_dirty_base"], True)

    def test_it_does_NOT_suppress_the_untracked_report(self):
        """Consenting to proceed is not a request to be told less. The report has no flag input."""
        signature = inspect.signature(runner_shared.report_untracked_dirt_at_run_start)
        self.assertNotIn("allow_dirty_base", signature.parameters)
        self.assertNotIn(
            "allow_dirty_base",
            inspect.getsource(runner_shared.evaluate_untracked_dirt),
        )

    def test_it_does_NOT_reach_the_integration_time_overlap_refusal(self):
        """That check protects a DIFFERENT party's work at a DIFFERENT time; not this flag's to
        waive. `dirty_tree_overlap` takes no consent parameter and mentions none."""
        signature = inspect.signature(runner_shared.dirty_tree_overlap)
        self.assertNotIn("allow_dirty_base", signature.parameters)
        self.assertNotIn(
            "allow_dirty_base", inspect.getsource(runner_shared.integrate_lane_branch)
        )


# ======================================================================================================
# The guard fires BEFORE any spawn, and touches nothing
# ======================================================================================================
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

    def _tree_snapshot(self, repo: Path) -> tuple[str, str]:
        return (
            _git(repo, "status", "--porcelain", "--untracked-files=all"),
            _git(repo, "stash", "list"),
        )

    def _drive(self, driver, spawn_name, run_dir, state, item):
        """Run `execute_item` with the spawn and the lifecycle patched; return spawn call count."""
        spawned: list[Any] = []

        def fake_spawn(*a, **k):
            spawned.append((a, k))
            return 0, "ses", str(run_dir / "log"), ["probe"]

        with (
            mock.patch.object(driver, spawn_name, fake_spawn),
            mock.patch.object(driver, "driver_begin", lambda *a, **k: (0, "ok")),
            mock.patch.object(driver, "driver_finalize", lambda *a, **k: (0, "ok")),
            mock.patch.object(
                driver, "assert_child_tool_identity", lambda *a, **k: None
            ),
        ):
            driver.execute_item(run_dir, state, item, recovery=False)
        return len(spawned)

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
                self.assertIn(
                    "shared_tree=not isolate", _effective_execute_item_source(driver)
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

    def test_the_guard_still_PRECEDES_spawn_and_allocation_structurally(self):
        """The ordering claim, kept separately from the firing claim above.

        This is the `tests/test_lane_clean_base.py:158-190` method and it establishes something the
        patched-spawn tests cannot: that no reordering can put a spawn or a lane allocation ahead of
        the guard, including on a code path no test drives.
        """
        for name, driver, spawn in DRIVERS:
            with self.subTest(driver=name):
                body = _effective_execute_item_source(driver, spawn=spawn)
                guard_at = body.find("evaluate_clean_base_for_launch(")
                spawn_at = body.find(f"{spawn}(")
                alloc_at = body.find("allocate_isolation_worktree(")
                self.assertNotEqual(guard_at, -1)
                self.assertNotEqual(spawn_at, -1)
                self.assertNotEqual(alloc_at, -1)
                self.assertLess(guard_at, spawn_at)
                self.assertLess(guard_at, alloc_at)

    def test_neither_driver_RE_IMPLEMENTS_the_consent_decision(self):
        """CID-3: one decision reached from both hosts, never two that merely agree today."""
        for name, driver, _spawn in DRIVERS:
            with self.subTest(driver=name):
                body = _effective_execute_item_source(driver)
                self.assertIn("clean_base_launch_decision(", body)
                self.assertNotIn("CLEAN_BASE_REFUSE", body)
                self.assertNotIn("CLEAN_BASE_CONSENTED", body)


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
