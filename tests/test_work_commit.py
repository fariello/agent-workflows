"""commitguard Order 02 (`y9vpvv`) E-08: the PLAN-LESS `aw commit --no-plan` surface.

WHY THIS FILE EXISTS. The commit contract now says an agent MUST commit through `aw commit`, and a
MUST is only compliable if some form of the verb fits every legitimate commit. `aw commit` required
a plan selector, so a backlog item, a spec edit or a typo fix had NO tooled path, which would have
made non-compliance the COMMON case (the failure mode backlog `gjadwm` records: a rule that fires on
correct behavior trains agents to ignore it). `--no-plan` closes that gap, and these cases are what
keep it closed.

EVERY CASE HERE IS BEHAVIORAL AND END TO END, driving the real `cli.main` against a scratch git
repository, in the shape `tests/test_work_primitives.py` already established for this verb. None of
them inspects source text: the hazards below are all parse-time or index-time behaviors that a
source search cannot see.

THE CENTRAL HAZARD IS ARGPARSE, NOT THE FEATURE. `aw commit`'s paths arrive through
`argparse.REMAINDER`, which does not begin capturing until every POSITIONAL is filled, so a declared
`plan` positional SILENTLY EATS THE FIRST PATH: measured before the change, `aw commit --no-plan -m
msg -- a.py b.py` parsed `plan='a.py'` with `path_argv=['b.py']`, which either fails on a nonsense
selector or commits only the REMAINING paths while reporting success. That is why
`test_no_plan_commits_every_path_after_the_marker` asserts on the resulting commit's FILE LIST
rather than only on the exit code: an exit-0 assertion passes while a path is silently dropped.

THE SECOND HAZARD IS THE FLAG BEING IGNORED RATHER THAN REFUSED. `aw commit y9vpvv --no-plan --
a.py` leaves `--no-plan` INSIDE the remainder where a parser-level `store_true` reads False, so the
contradiction would be silently resolved in favor of the plan. Both orderings are therefore pinned.
"""

from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import cli
from agent_workflows import git_commit_helper as gch


_PLAN = """# IPD: Demo work plan

- Date: 2026-08-28
- Kind: child
- Concern: A real concern statement for review.
- Scope: A real scope statement.
- Scope-Paths: src/, tests/
- Item-Dependencies: none
- Status: approved
- Set: wk
- Order: 1
- Highest E allocated: 01
- Author: tester
- Id: wk0001

## Workflow history
- 2026-08-28 approved (aw set): approved

## Goal

Demo.
"""


class PlanLessCommitTest(unittest.TestCase):
    """`aw commit --no-plan` must be a real tooled path, not a rubber stamp."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.root, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.root, check=True)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)
        (self.plans / "20260828-wk-01-wk0001-demo.ipd.md").write_text(
            _PLAN, encoding="utf-8"
        )
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / ".gitignore").write_text(
            ".aw/worktrees/\n.aw/state/\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=self.root, check=True)

    # -- helpers ------------------------------------------------------------------------

    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv)
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue() + err.getvalue()

    def _head(self) -> str:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True
        ).stdout.strip()

    def _committed_files(self, rev: str = "HEAD") -> list[str]:
        out = subprocess.run(
            ["git", "show", "--name-only", "--format=", rev],
            cwd=self.root,
            capture_output=True,
            text=True,
        ).stdout
        return sorted(ln.strip() for ln in out.splitlines() if ln.strip())

    def _write(self, rel: str, text: str = "x\n") -> str:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return rel

    # -- E-01 / V-01: the mode exists and every path reaches the commit ------------------

    def test_no_plan_commits_a_path_no_plan_governs(self):
        """The gap-closing case: a file outside any plan's territory gets a tooled commit."""
        rel = self._write("notes.md", "a note\n")
        rc, out = self._run(
            [
                "commit",
                "--no-plan",
                "--dir",
                str(self.root),
                "-m",
                "docs: notes",
                "--",
                rel,
            ]
        )
        self.assertEqual(rc, 0, out)
        self.assertEqual(self._committed_files(), ["notes.md"], out)

    def test_no_plan_commits_every_path_after_the_marker(self):
        """THE ARGPARSE REGRESSION GUARD, and the reason this asserts the FILE LIST.

        With a `plan` positional declared beside `path_argv`'s REMAINDER, this exact argv parsed
        `plan='note-a.md'` and `path_argv=['note-b.md']`, so the first path was consumed as a
        SELECTOR. An exit-code-only assertion cannot see that: the command can exit 0 having
        committed a subset. Two paths is the minimum that distinguishes the two behaviors.
        """
        a = self._write("note-a.md", "a\n")
        b = self._write("note-b.md", "b\n")
        rc, out = self._run(
            [
                "commit",
                "--no-plan",
                "--dir",
                str(self.root),
                "-m",
                "docs: two notes",
                "--",
                a,
                b,
            ]
        )
        self.assertEqual(rc, 0, out)
        self.assertEqual(
            self._committed_files(),
            ["note-a.md", "note-b.md"],
            "EVERY path after `--` must reach the commit and NONE may be read as a plan selector. "
            "A commit holding only the SECOND path means the first was consumed as a selector by "
            "an `argparse.REMAINDER`-adjacent positional, which is the measured failure this case "
            f"exists to catch. Output was:\n{out}",
        )

    def test_omitting_both_a_plan_and_the_flag_still_refuses(self):
        """The relaxation must be OPT-IN: a forgotten selector is still a usage error, not a
        silently plan-less commit."""
        rel = self._write("orphan.md")
        head_before = self._head()
        rc, out = self._run(
            ["commit", "--dir", str(self.root), "-m", "no selector", "--", rel]
        )
        self.assertEqual(rc, 2, out)
        self.assertIn("selector is required", out)
        self.assertEqual(head_before, self._head(), "nothing may have been committed")

    def test_the_plan_bearing_form_is_unchanged(self):
        """The regression side: adding the mode must not disturb `aw commit <plan> -- <paths>`."""
        rel = self._write("src/feature.py", "print('x')\n")
        rc, out = self._run(
            [
                "commit",
                "wk0001",
                "--dir",
                str(self.root),
                "-m",
                "feat: feature",
                "--",
                rel,
            ]
        )
        self.assertEqual(rc, 0, out)
        self.assertEqual(self._committed_files(), ["src/feature.py"], out)

    # -- E-02 / V-02: the reduction in safety is NAMED, and the real protection survives --

    def test_no_plan_names_the_protections_it_skips(self):
        """A reduced-safety mode must say so out loud; a silent skip is how one comes to be
        trusted. Asserted on the PROTECTIONS by name, not on the exact sentence, so the wording
        stays free to improve."""
        rel = self._write("named.md")
        rc, out = self._run(
            [
                "commit",
                "--no-plan",
                "--dir",
                str(self.root),
                "-m",
                "docs: named",
                "--",
                rel,
            ]
        )
        self.assertEqual(rc, 0, out)
        missing = [
            needle
            for needle in ("Scope-Paths", "plan validation", "--no-plan")
            if needle not in out
        ]
        self.assertEqual(
            missing,
            [],
            "the plan-less notice must NAME the plan-derived protections it skips "
            f"(missing: {missing!r}); output was:\n{out}",
        )

    def test_no_plan_still_excludes_a_co_workers_staged_file(self):
        """THE PROTECTION THAT MUST NOT WEAKEN. `offer_commit`'s snapshot-then-intersect is the only
        mechanism that STRUCTURALLY stops a concurrent agent's staged edit being swept into your
        commit, and it has nothing to do with plans, so plan-less mode must keep it."""
        coworker = self._write("coworker.md", "their work in progress\n")
        subprocess.run(["git", "add", coworker], cwd=self.root, check=True)
        mine = self._write("mine.md", "my work\n")

        rc, out = self._run(
            [
                "commit",
                "--no-plan",
                "--dir",
                str(self.root),
                "-m",
                "docs: mine",
                "--",
                mine,
            ]
        )
        self.assertEqual(rc, 0, out)
        self.assertEqual(
            self._committed_files(),
            ["mine.md"],
            "a co-worker's ALREADY-STAGED file must not enter a --no-plan commit of different "
            f"paths; the commit held {self._committed_files()!r}. Output:\n{out}",
        )
        staged_after = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=self.root,
            capture_output=True,
            text=True,
        ).stdout.split()
        self.assertIn(
            "coworker.md",
            staged_after,
            "their work must be left exactly as it was, still staged and uncommitted, never "
            f"unstaged or discarded; staged set afterwards was {staged_after!r}",
        )

    def test_no_plan_routes_through_the_one_shared_commit_helper(self):
        """Plan-less mode must not become a second commit path. Driven, not grepped: with the
        SHARED helper stubbed to commit nothing, a forked `git commit` would still produce a
        commit."""
        rel = self._write("delegated.md")
        head_before = self._head()
        stub = gch.CommitOutcome(
            status=gch.STATUS_NOTHING_TO_COMMIT,
            message="stubbed: the shared helper committed nothing",
            staged=(),
            commit=None,
        )
        recorded = []

        def spy(repo_root, paths, **kwargs):
            recorded.append((Path(repo_root), list(paths), dict(kwargs)))
            return stub

        with mock.patch.object(gch, "offer_commit", spy):
            rc, out = self._run(
                [
                    "commit",
                    "--no-plan",
                    "--dir",
                    str(self.root),
                    "-m",
                    "docs: delegated",
                    "--",
                    rel,
                ]
            )
        self.assertEqual(rc, 1, out)
        self.assertEqual(
            len(recorded),
            1,
            "plan-less mode must route through the SHARED helper exactly once; it called it "
            f"{len(recorded)} time(s). Zero means a forked commit path.",
        )
        _root, paths, kwargs = recorded[0]
        self.assertEqual(paths, [rel])
        self.assertEqual(
            kwargs.get("on_unrelated_staged"),
            "scope",
            "the scope posture must still be DELEGATED to the shared helper in plan-less mode, "
            f"so a co-worker's staged file cannot be swept in; kwargs were {sorted(kwargs)!r}",
        )
        self.assertEqual(
            head_before,
            self._head(),
            "with the shared helper committing nothing, no commit may appear, or `aw commit "
            "--no-plan` carries a forked commit path of its own",
        )

    # -- E-03 / V-03: the ambiguous and under-specified invocations are REFUSED -----------

    #: (case, argv tail, the needle the refusal must name, why the shape is dangerous)
    REFUSALS = (
        (
            "a plan selector BEFORE --no-plan",
            ["wk0001", "--no-plan"],
            "--no-plan",
            "a contradiction: one token says a plan governs the commit, the other says none does. "
            "A silent precedence rule would make the result depend on undocumented order",
        ),
        (
            "a plan selector AFTER --no-plan",
            ["--no-plan", "wk0001"],
            "--no-plan",
            "THE SHAPE ARGPARSE CANNOT SEE. Here the flag lands inside the REMAINDER, so a "
            "parser-level store_true reads False and the flag is IGNORED rather than refused; the "
            "commit would then silently proceed under the plan the operator said not to use",
        ),
    )

    def test_a_contradictory_invocation_is_a_usage_error(self):
        failures = []
        for case, tail, needle, why in self.REFUSALS:
            rel = self._write("contradiction.md")
            head_before = self._head()
            rc, out = self._run(
                ["commit", *tail, "--dir", str(self.root), "-m", "x", "--", rel]
            )
            problems = []
            if rc != 2:
                problems.append(f"exited {rc}, expected 2 (a usage error)")
            if needle not in out:
                problems.append(f"the refusal never named {needle!r}: {out.strip()!r}")
            if head_before != self._head():
                problems.append("it created a commit despite refusing")
            if problems:
                failures.append(
                    f"  {case}: {'; '.join(problems)}\n    this row exists because: {why}"
                )
        self.assertEqual(
            failures,
            [],
            "a contradictory `aw commit` invocation must be refused with exit 2 in BOTH token "
            "orders. Read the rows together: if only the second failed, the refusal is implemented "
            "with argparse's own mutual exclusion, which never runs for a flag REMAINDER swallowed, "
            "so the flag is silently ignored.\n" + "\n".join(failures),
        )

    def test_no_plan_without_a_message_is_a_usage_error(self):
        """`aw commit <plan>` derives its message from the plan, so plan-less mode has no message
        source. Refuse rather than committing under a placeholder nobody chose."""
        rel = self._write("unmessaged.md")
        head_before = self._head()
        rc, out = self._run(["commit", "--no-plan", "--dir", str(self.root), "--", rel])
        self.assertEqual(rc, 2, out)
        self.assertIn("-m", out)
        self.assertEqual(head_before, self._head(), "nothing may have been committed")

    # -- the mode must not quietly become a push or an `add -A` --------------------------

    def test_no_plan_stages_only_the_named_paths(self):
        """An untracked file the operator did NOT name must be left alone, which is the `add -A`
        reflex this whole contract exists to stop."""
        named = self._write("named-only.md")
        self._write("unnamed.md", "not mine to commit\n")
        rc, out = self._run(
            [
                "commit",
                "--no-plan",
                "--dir",
                str(self.root),
                "-m",
                "docs: named only",
                "--",
                named,
            ]
        )
        self.assertEqual(rc, 0, out)
        self.assertEqual(self._committed_files(), ["named-only.md"], out)
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.root,
            capture_output=True,
            text=True,
        ).stdout
        self.assertIn(
            "?? unnamed.md",
            status,
            f"an unnamed file must stay untracked and untouched; status was:\n{status}",
        )

    def test_no_plan_records_the_requested_message_verbatim(self):
        """The message is the operator's, not a derived placeholder."""
        rel = self._write("messaged.md")
        rc, out = self._run(
            [
                "commit",
                "--no-plan",
                "--dir",
                str(self.root),
                "-m",
                "chore(backlog): close an item with no plan",
                "--",
                rel,
            ]
        )
        self.assertEqual(rc, 0, out)
        subject = subprocess.run(
            ["git", "log", "-1", "--format=%s"],
            cwd=self.root,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(subject, "chore(backlog): close an item with no plan")

    def test_no_plan_honors_no_commit_as_a_preview(self):
        """`--no-commit` must still short-circuit, so a plan-less invocation can be previewed."""
        rel = self._write("previewed.md")
        head_before = self._head()
        rc, out = self._run(
            [
                "commit",
                "--no-plan",
                "--no-commit",
                "--dir",
                str(self.root),
                "-m",
                "docs: preview",
                "--",
                rel,
            ]
        )
        self.assertEqual(
            head_before, self._head(), f"a preview must commit nothing: {out}"
        )
        self.assertNotEqual(rc, 0, out)


class PlanLessCommitJsonShapeTest(unittest.TestCase):
    """The `--no-plan` flag must be DECLARED on the parser, so `--help` is honest about it.

    Kept separate from the behavioral class because it needs no git fixture. The declaration is
    load-bearing beyond documentation: it is what lets the flag parse when it PRECEDES the selector.
    """

    def test_the_flag_is_declared_and_documented(self):
        parser = cli._build_parser()
        text = io.StringIO()
        with redirect_stdout(text):
            try:
                parser.parse_args(["commit", "--help"])
            except SystemExit:
                pass
        help_text = text.getvalue()
        missing = [
            needle
            for needle in ("--no-plan", "Scope-Paths", "requires -m")
            if needle not in help_text
        ]
        self.assertEqual(
            missing,
            [],
            "`aw commit --help` must document the plan-less mode and what it gives up "
            f"(missing: {missing!r}); help was:\n{help_text}",
        )

    def test_the_verb_still_reports_a_machine_readable_surface(self):
        """Guard against the flag addition breaking the shared output parents."""
        parser = cli._build_parser()
        ns = parser.parse_args(["commit", "--no-plan", "--", "a.py"])
        self.assertTrue(hasattr(ns, "agent"))
        self.assertTrue(hasattr(ns, "json"))
        self.assertTrue(getattr(ns, "no_plan"))
        self.assertEqual(json.loads(json.dumps(list(ns.path_argv))), ["--", "a.py"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
