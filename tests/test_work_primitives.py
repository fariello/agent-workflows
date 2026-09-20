"""agentadhere Phase 2 (IPD 8dto0g): atomic workflow primitives aw work/test/commit/finish.

Covers:
  E-01/V-01 - aw work begin: validate (fail closed) + allocate isolated worktree via worktree_lease.
  E-02/V-02 - aw test: capture command/exit/output/env bound to the tree; honest forgeable label.
  E-03/V-03 - aw commit: commit only in-scope paths via git_commit_helper.offer_commit; refuse
              out-of-scope; no add -A / no push.
  E-04/V-04 - aw finish: require bound evidence, non-authoritative transition only (never executed).

THE THREE "SINGLE SHARED PATH" CLAIMS ARE BEHAVIORAL, and were source-text searches. Each read
`inspect.getsource(...)` and asserted a symbol's NAME appeared (or did not), which cannot distinguish
the shared object from a same-named local fork, cannot show the call ever RUNS, and is satisfied by a
comment. Each now patches the shared symbol with a spy and drives the real CLI, so a fork sees the
real helper and the spy records nothing.

THE SAFETY CLAIM IS THE ONE THAT CHANGED MOST. `aw finish` must never push or tag (execution
contract, catalog I-02). That was asserted by searching `run_finish`'s source for the strings
`"push"` / `"tag"`, which is weak in BOTH directions: a docstring sentence saying "never pushes"
breaks it, and DELEGATING to any helper that pushes satisfies it. It now runs the real `aw finish`
with `subprocess.Popen` wrapped in an ARGV RECORDER and asserts no recorded git invocation carries
`push` or `tag` as its SUBCOMMAND. That catches an indirect push through `status_set`, through
`git_commit_helper`, or through any future collaborator, which the text pin could not. See
`_GitArgvRecorder` for why `Popen` is the single correct interception point here.
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
from agent_workflows import work_cmd
from agent_workflows import worktree_lease


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
A real goal statement.

## Detailed Implementation Checklist (TODO)

### Task group 1: work
- [ ] E-01 Do a real observable thing.
  - Depends on: none
  - Expected outcome: a real observable result.
  - Execution state: pending

## Validation and cross-check (verify before reporting done)
- [ ] V-01 validates E-01
  - Required evidence: a real falsifiable evidence statement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- Size assessment: standard
- Cohesion rationale: not required
"""

#: git subcommands `aw finish` must never invoke, and what each one would mean if it did.
#:
#: MATCHED AS THE SUBCOMMAND, never as a substring of the whole argv: `git commit -m "do not push"`
#: contains the text `push` and is perfectly legitimate, and the old source-text pin could not tell
#: the two apart. A subcommand is the first non-flag token after `git`.
FORBIDDEN_GIT_SUBCOMMANDS = {
    "push": "publishes local history to a remote; the execution contract forbids an agent pushing, "
    "and `aw finish` is a LOCAL status transition that has no reason to contact a remote",
    "tag": "creates a release-shaped ref; tagging is permitted only inside release-review after an "
    "explicit human GO (RELEASING.md), never as a side effect of finishing an item",
}


def _git_subcommand(argv) -> str | None:
    """Return the git SUBCOMMAND of `argv`, or None when `argv` is not a git invocation.

    Skips the global flags git accepts before its subcommand (`-C <dir>`, `-c k=v`, `--git-dir=...`),
    so `git -C /tmp push` is recognized as `push` rather than as `-C`.
    """
    try:
        tokens = [str(token) for token in argv]
    except TypeError:  # a shell=True string, or anything non-iterable
        tokens = [str(argv)]
    if not tokens:
        return None
    if Path(tokens[0]).name not in ("git", "git.exe"):
        return None
    index = 1
    while index < len(tokens):
        token = tokens[index]
        if not token.startswith("-"):
            return token
        # `-C <dir>` and `-c <cfg>` consume the following token.
        if token in ("-C", "-c"):
            index += 2
            continue
        index += 1
    return None


class _GitArgvRecorder:
    """Record every argv the process spawns while the recorder is installed.

    WHY `subprocess.Popen` IS THE INTERCEPTION POINT. `subprocess.run`, `check_output` and
    `check_call` are thin wrappers that all construct a `Popen`, and the code under test reaches
    subprocess through several modules (`work_cmd._git`, `artifact_core`, `git_commit_helper`), each
    holding its OWN reference to the `subprocess` module. Patching the single `subprocess.Popen`
    attribute therefore observes every route, including a future collaborator this test has never
    heard of, which is precisely the indirection the replaced source-text pin could not see.

    The real `Popen` is still called, so the command under test genuinely runs and the test asserts
    over what a real, successful `aw finish` actually did.
    """

    def __init__(self) -> None:
        self.argvs: list[list[str]] = []

    def __enter__(self) -> "_GitArgvRecorder":
        real_popen = subprocess.Popen

        def recording_popen(args, *a, **kw):
            if isinstance(args, (str, bytes)):
                self.argvs.append([args if isinstance(args, str) else args.decode()])
            else:
                self.argvs.append([str(token) for token in args])
            return real_popen(args, *a, **kw)

        self._patch = mock.patch.object(subprocess, "Popen", recording_popen)
        self._patch.start()
        return self

    def __exit__(self, *exc) -> None:
        self._patch.stop()

    def git_subcommands(self) -> list[str]:
        """Every git subcommand observed, in order (non-git spawns excluded)."""
        return [sub for sub in (_git_subcommand(argv) for argv in self.argvs) if sub]

    def offending(self) -> list[tuple[str, list[str]]]:
        """(subcommand, argv) for every recorded invocation of a forbidden git subcommand."""
        found = []
        for argv in self.argvs:
            sub = _git_subcommand(argv)
            if sub in FORBIDDEN_GIT_SUBCOMMANDS:
                found.append((sub, argv))
        return found


class WorkPrimitivesTest(unittest.TestCase):
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
        # gitignore the worktrees + state so the throwaway repo does not embed them
        (self.root / ".gitignore").write_text(
            ".aw/worktrees/\n.aw/state/\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=self.root, check=True)

    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv)
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue() + err.getvalue()

    # ---- E-01 / V-01: aw work begin ----

    def test_work_begin_validates_and_allocates_worktree(self):
        rc, out = self._run(["work", "begin", "wk0001", "--dir", str(self.root)])
        self.assertEqual(rc, 0, out)
        self.assertIn("allocated worktree", out)
        lease = self.root / ".aw" / "state" / "work" / "wk0001" / "work-lease.json"
        self.assertTrue(lease.is_file(), out)
        data = json.loads(lease.read_text(encoding="utf-8"))
        self.assertEqual(data["plan_id"], "wk0001")
        self.assertIn("worktree_path", data)
        # the worktree really exists
        wt = subprocess.run(
            ["git", "worktree", "list"], cwd=self.root, capture_output=True, text=True
        )
        self.assertIn("wk0001", wt.stdout)

    def test_work_begin_fails_closed_on_findings(self):
        """NOT a row: an `assertRaises`-shaped refusal claim, and its setup plants a SECOND
        badly-named plan that no other case wants."""
        # a badly-named plan triggers check.name-nonconformant -> fail closed, no worktree
        (self.plans / "badname.ipd.md").write_text(
            _PLAN.replace("- Id: wk0001", "- Id: bad001").replace(
                "- Set: wk", "- Set: bad"
            ),
            encoding="utf-8",
        )
        rc, out = self._run(["work", "begin", "bad001", "--dir", str(self.root)])
        self.assertEqual(rc, 1, out)
        self.assertIn("refusing to start", out)
        self.assertIn("check.name-nonconformant", out)
        self.assertFalse(
            (
                self.root / ".aw" / "state" / "work" / "bad001" / "work-lease.json"
            ).exists()
        )

    def test_work_begin_allocates_through_the_one_shared_worktree_lease(self):
        """BEHAVIORAL replacement for a pin that searched `work_cmd`'s source for the two NAMES.

        Two claims the text search could not make. FIRST, IDENTITY: `work_cmd` must reach the SAME
        `worktree_lease` module object the rest of the toolkit does, so there is one worktree path
        rather than two that can disagree about lane naming or reuse. SECOND, USE: the shared
        allocator must actually RUN during a real `aw work begin`, with the plan id it was given.
        """
        self.assertIs(
            work_cmd._wl,
            worktree_lease,
            "work_cmd must bind the shared worktree_lease module, not a private copy",
        )
        calls = []
        real_allocate = worktree_lease.allocate_worktree

        def spy(repo_root, plan_id, *args, **kwargs):
            calls.append((Path(repo_root), plan_id))
            return real_allocate(repo_root, plan_id, *args, **kwargs)

        with mock.patch.object(worktree_lease, "allocate_worktree", spy):
            rc, out = self._run(["work", "begin", "wk0001", "--dir", str(self.root)])

        self.assertEqual(rc, 0, out)
        self.assertEqual(
            calls,
            [(self.root, "wk0001")],
            "`aw work begin` must allocate its lane by calling the SHARED "
            "`worktree_lease.allocate_worktree` exactly once, with the repo root and the plan id. "
            f"Recorded calls: {calls!r}. An empty list means work_cmd has its own worktree path "
            "again, which is how two allocators come to disagree about lane reuse.",
        )
        # ...and the lease the command wrote describes the lane the SHARED allocator returned.
        lease = json.loads(
            (
                self.root / ".aw" / "state" / "work" / "wk0001" / "work-lease.json"
            ).read_text(encoding="utf-8")
        )
        self.assertTrue(Path(lease["worktree_path"]).is_dir(), lease)

    # ---- E-02 / V-02: aw test ----

    #: (case, the `python -c` program to run, expected `aw test` exit code, expected recorded
    #: `exit_code` in the evidence record, why this row exists)
    TEST_CAPTURES = (
        (
            "a passing command",
            "print('hi')",
            0,
            0,
            "the baseline, and the row that stops the failing row below from passing vacuously: if "
            "`aw test` returned 1 for everything, the failure row alone would look correct",
        ),
        (
            "a command exiting nonzero",
            "import sys;sys.exit(3)",
            1,
            3,
            "THE HONESTY PROPERTY. The evidence record must carry the child's REAL exit status (3), "
            "not a normalized 0/1, because `aw finish` refuses on a FAILING bound record; a record "
            "that flattened 3 to 0 would let a red suite satisfy the finish gate",
        ),
    )

    def test_test_captures_the_commands_real_outcome_in_a_bound_record(self):
        failures = []
        for case, program, expected_rc, expected_exit, why in self.TEST_CAPTURES:
            rc, out = self._run(
                [
                    "test",
                    "wk0001",
                    "--dir",
                    str(self.root),
                    "--",
                    "python",
                    "-c",
                    program,
                ]
            )
            ev = self.root / ".aw" / "state" / "work" / "wk0001" / "test-evidence.json"
            problems = []
            if rc != expected_rc:
                problems.append(f"`aw test` exited {rc}, expected {expected_rc}: {out}")
            if not ev.is_file():
                problems.append("no evidence record was written")
            else:
                rec = json.loads(ev.read_text(encoding="utf-8"))
                if rec.get("exit_code") != expected_exit:
                    problems.append(
                        f"recorded exit_code {rec.get('exit_code')!r}, expected {expected_exit!r}"
                    )
                if rec.get("command") != ["python", "-c", program]:
                    problems.append(f"recorded command {rec.get('command')!r}")
                # The record must BIND to the tree/commit it ran against, or it cannot be checked
                # for staleness later, and it must label its own assurance honestly.
                for key in ("git_tree", "git_head", "started_at"):
                    if key not in rec:
                        problems.append(f"record lacks the binding field {key!r}")
                if rec.get("assurance") != "local-forgeable":
                    problems.append(
                        f"assurance label is {rec.get('assurance')!r}, expected "
                        "'local-forgeable' (an honest label, since a local record IS forgeable)"
                    )
            if problems:
                failures.append(
                    f"  {case}: {'; '.join(problems)}\n    this row exists because: {why}"
                )
        self.assertEqual(
            failures,
            [],
            f"`aw test` recorded the wrong evidence for {len(failures)} of "
            f"{len(self.TEST_CAPTURES)} commands. Read the rows together: if only the NONZERO row "
            "failed, the recorder is flattening a real failure into a pass, and `aw finish`'s "
            "refusal-on-failing-evidence gate is now defeated by any red command; if both rows "
            "failed on a missing binding field, the record can no longer be checked against the "
            "current tree and every finish would accept STALE evidence. FIX: `work_cmd.run_test` "
            "must record the child's own returncode verbatim plus the tree/head it ran against.\n"
            + "\n".join(failures),
        )

    # ---- E-03 / V-03: aw commit ----

    def test_commit_only_in_scope_paths(self):
        (self.root / "src" / "feature.py").write_text("print('x')\n", encoding="utf-8")
        subprocess.run(["git", "add", "src/feature.py"], cwd=self.root, check=True)
        rc, out = self._run(
            [
                "commit",
                "wk0001",
                "--dir",
                str(self.root),
                "-m",
                "add feature",
                "--",
                "src/feature.py",
            ]
        )
        self.assertEqual(rc, 0, out)
        self.assertIn("committed", out)
        show = subprocess.run(
            ["git", "show", "--stat", "--format=%s", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertIn("add feature", show.stdout)
        self.assertIn("src/feature.py", show.stdout)
        self.assertNotIn(".ipd.md", show.stdout)  # only the in-scope path

    def test_commit_refuses_out_of_scope_staged(self):
        """NOT a row: a refusal whose assertion shape differs (it pins HEAD before and after to show
        no commit was made), and whose setup stages a path the positive case must not have."""
        (self.root / "outofscope.txt").write_text("y\n", encoding="utf-8")
        subprocess.run(["git", "add", "outofscope.txt"], cwd=self.root, check=True)
        (self.root / "src" / "g.py").write_text("print('g')\n", encoding="utf-8")
        head_before = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True
        ).stdout.strip()
        rc, out = self._run(
            ["commit", "wk0001", "--dir", str(self.root), "-m", "g", "--", "src/g.py"]
        )
        self.assertEqual(rc, 1, out)
        self.assertIn("out-of-scope", out)
        self.assertIn("outofscope.txt", out)
        head_after = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True
        ).stdout.strip()
        self.assertEqual(head_before, head_after)  # no commit made

    def test_commit_delegates_to_the_one_shared_commit_helper(self):
        """BEHAVIORAL replacement for a pin that searched `run_commit` for `_gch.offer_commit` and
        `assertNotIn`ed two spellings of a forked `git commit`.

        The old pin could not tell a real delegation from a comment mentioning it, and its
        absence-of-text half was satisfiable by spelling a forked commit differently. This asserts
        the module identity, records the ARGUMENTS handed to the shared helper (so the scope-relevant
        options are visibly delegated rather than re-decided), and separately proves no forked
        `git commit` runs: with the helper stubbed to report nothing committed, no `git commit`
        reaches the argv recorder.
        """
        self.assertIs(
            work_cmd._gch,
            gch,
            "work_cmd must bind the shared git_commit_helper module, not a private copy",
        )
        (self.root / "src" / "feature.py").write_text("print('x')\n", encoding="utf-8")
        subprocess.run(["git", "add", "src/feature.py"], cwd=self.root, check=True)

        recorded = []
        real_offer = gch.offer_commit

        def spy(repo_root, paths, **kwargs):
            recorded.append((Path(repo_root), list(paths), dict(kwargs)))
            return real_offer(repo_root, paths, **kwargs)

        with mock.patch.object(gch, "offer_commit", spy):
            rc, out = self._run(
                [
                    "commit",
                    "wk0001",
                    "--dir",
                    str(self.root),
                    "-m",
                    "add feature",
                    "--",
                    "src/feature.py",
                ]
            )
        self.assertEqual(rc, 0, out)
        self.assertEqual(
            len(recorded),
            1,
            "`aw commit` must route the commit through the SHARED helper exactly once; it called it "
            f"{len(recorded)} time(s). Zero means a forked commit path came back.",
        )
        repo_root, paths, kwargs = recorded[0]
        self.assertEqual(repo_root, self.root)
        self.assertEqual(
            paths,
            ["src/feature.py"],
            "only the explicitly requested paths may be handed to the helper (never `-A`)",
        )
        self.assertEqual(
            kwargs.get("on_unrelated_staged"),
            "scope",
            "the scope posture must be DELEGATED to the shared helper rather than re-decided here, "
            f"so a co-worker's staged file cannot be swept in; kwargs were {sorted(kwargs)!r}",
        )

    def test_commit_holds_no_forked_git_commit_path_of_its_own(self):
        """The absence half of the delegation claim, driven instead of grepped.

        With the shared helper stubbed to commit NOTHING, a `run_commit` carrying its own
        `git commit` fallback would still produce one; the argv recorder shows whether any did.
        """
        (self.root / "src" / "feature.py").write_text("print('x')\n", encoding="utf-8")
        subprocess.run(["git", "add", "src/feature.py"], cwd=self.root, check=True)
        head_before = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True
        ).stdout.strip()

        stub = gch.CommitOutcome(
            status=gch.STATUS_NOTHING_TO_COMMIT,
            message="stubbed: the shared helper committed nothing",
            staged=[],
            commit=None,
        )
        with _GitArgvRecorder() as recorder:
            with mock.patch.object(gch, "offer_commit", lambda *a, **k: stub):
                rc, out = self._run(
                    [
                        "commit",
                        "wk0001",
                        "--dir",
                        str(self.root),
                        "-m",
                        "add feature",
                        "--",
                        "src/feature.py",
                    ]
                )
        self.assertEqual(rc, 1, out)
        commits = [sub for sub in recorder.git_subcommands() if sub == "commit"]
        self.assertEqual(
            commits,
            [],
            "with the SHARED commit helper stubbed to commit nothing, `aw commit` still ran "
            f"`git commit` {len(commits)} time(s), so it carries a forked commit path. Every commit "
            "must go through `git_commit_helper.offer_commit`, which is what snapshots the index "
            "first and commits only the intersection of your paths with what it itself staged; a "
            "bypass is how a co-worker's staged edit gets swept into your commit.",
        )
        head_after = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True
        ).stdout.strip()
        self.assertEqual(head_before, head_after, "nothing may have been committed")

    # ---- E-04 / V-04: aw finish ----

    def _write_evidence(self, exit_code=0, stale=False):
        ev_dir = self.root / ".aw" / "state" / "work" / "wk0001"
        ev_dir.mkdir(parents=True, exist_ok=True)
        tree = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"],
            cwd=self.root,
            capture_output=True,
            text=True,
        ).stdout.strip()
        rec = {
            "schema_version": "aw.work-evidence/v1",
            "plan_id": "wk0001",
            "assurance": "local-forgeable",
            "command": ["true"],
            "exit_code": exit_code,
            "git_tree": "0" * 40 if stale else tree,
            "git_head": "x",
        }
        (ev_dir / "test-evidence.json").write_text(json.dumps(rec), encoding="utf-8")

    def _plan_text(self) -> str:
        return (self.plans / "20260828-wk-01-wk0001-demo.ipd.md").read_text(
            encoding="utf-8"
        )

    #: (case, evidence to write beforehand or None for "write none", the `--to` target, expected exit
    #: code, a substring the refusal/report must carry, the `- Status:` line the plan must hold
    #: AFTERWARDS, why this row exists)
    #:
    #: THE STATUS COLUMN IS WHAT MAKES THE REFUSALS MEAN ANYTHING: a refusal that printed the right
    #: words while still rewriting the plan would satisfy an exit-code-only check.
    #:
    #: EACH NEEDLE IS A STRING ONLY `run_finish` ITSELF EMITS, which mutation testing forced. The
    #: authority row first used the needle `aw ipd finalize`; deleting `run_finish`'s authority gate
    #: left the row GREEN, because the request then fell through to `status_set`, whose own
    #: executed-routing refusal ALSO exits 2 and ALSO names `aw ipd finalize`. Two independent gates
    #: are good news for the repository and bad news for a test that cannot tell them apart, so the
    #: needle is now `aw finish: refusing`, which the downstream gate never prints.
    FINISH_GATES = (
        (
            "the authoritative terminal status",
            {"exit_code": 0},
            "executed",
            2,
            "aw finish: refusing to set 'executed'",
            "- Status: approved",
            "AUTHORITY HONESTY, the hard MUST. `executed` is the authoritative claim that work is "
            "implemented AND verified, and only `aw ipd finalize` may assert it. Note the evidence "
            "here is PRESENT and VALID, so this row proves the refusal is about authority and not a "
            "missing prerequisite; exit 2 (not 1) marks it a misuse rather than a failed check. The "
            "needle names `aw finish` on purpose: `status_set` refuses this route too, so a laxer "
            "needle would credit THIS gate for the DOWNSTREAM one's work (measured, see above)",
        ),
        (
            "no bound evidence at all",
            None,
            "reviewed",
            1,
            "no test evidence",
            "- Status: approved",
            "the evidence REQUIREMENT. Without it `aw finish` would be a plain status setter with an "
            "attestation-shaped name, which is exactly the forged-evidence shape the repository's "
            "attestation rules exist to stop",
        ),
        (
            "evidence bound to a stale tree",
            {"stale": True},
            "reviewed",
            1,
            "STALE tree",
            "- Status: approved",
            "EVIDENCE MUST BIND TO THE TREE IT DESCRIBES. A record from an earlier tree proves "
            "nothing about the current one, and accepting it is how a green run on old code "
            "certifies new code. This is the row that gives the `git_tree` field its purpose",
        ),
        (
            "evidence recording a FAILING run",
            {"exit_code": 3},
            "reviewed",
            1,
            "FAILING run",
            "- Status: approved",
            "a bound record is not enough: it must record a PASS. Without this row, `aw test` "
            "followed by `aw finish` would advance a plan on a red suite, which is the "
            "'tests pass' claim the execution contract forbids asserting without evidence",
        ),
        (
            "a valid non-authoritative transition",
            {"exit_code": 0},
            "reviewed",
            0,
            "transitioned wk0001 -> reviewed",
            "- Status: reviewed",
            "THE POSITIVE ROW, and the one that stops all four refusals above from being vacuous: a "
            "`finish` that refused everything would satisfy them while being useless. It also pins "
            "that the transition is really WRITTEN, which is the only thing the status column can "
            "observe changing",
        ),
    )

    def test_finish_gates_every_shape_of_evidence_and_authority(self):
        failures = []
        for (
            case,
            evidence,
            target,
            expected_rc,
            needle,
            expected_status,
            why,
        ) in self.FINISH_GATES:
            with tempfile.TemporaryDirectory() as temp:
                # A fresh repo per row: several rows differ only in the evidence ON DISK, so a
                # shared tree would let one row's record satisfy the next row's gate.
                inner = _Fixture(Path(temp))
                if evidence is not None:
                    inner.write_evidence(**evidence)
                rc, out = inner.run(
                    ["finish", "wk0001", "--dir", str(inner.root), "--to", target]
                )
                status_text = inner.plan_text()
            problems = []
            if rc != expected_rc:
                problems.append(f"exit {rc}, expected {expected_rc}")
            if needle not in out:
                problems.append(f"output lacks {needle!r}; output was {out!r}")
            if expected_status not in status_text:
                problems.append(
                    f"the plan does not carry {expected_status!r} afterwards, so the transition "
                    "did the wrong thing on disk"
                )
            if problems:
                failures.append(
                    f"  {case} (--to {target}): {'; '.join(problems)}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            failures,
            [],
            f"`aw finish` mis-gated {len(failures)} of {len(self.FINISH_GATES)} cases. Read them "
            "together, because the pattern names the defect: if the four REFUSAL rows failed and the "
            "positive one passed, the gate is open and `aw finish` will advance a plan with absent, "
            "stale, or FAILING evidence (or usurp `aw ipd finalize`'s authority); if only the "
            "POSITIVE row failed, `aw finish` refuses everything and the refusal rows are passing "
            "vacuously. A wrong `- Status:` with a right exit code is the worst combination: the "
            "command printed a refusal and rewrote the plan anyway. FIX: each gate lives in "
            "`work_cmd.run_finish` and must run BEFORE the `status_set` delegation; the terminal "
            "transition stays with `aw ipd finalize`.\n" + "\n".join(failures),
        )

    def test_finish_reports_without_transitioning_when_no_target_is_given(self):
        """NOT a row: the argv shape differs (no `--to` at all), so it cannot share the table's
        target column, and the claim is the absence of a transition rather than a gate verdict."""
        self._write_evidence()
        rc, out = self._run(["finish", "wk0001", "--dir", str(self.root)])
        self.assertEqual(rc, 0, out)
        self.assertIn("bound to the current tree", out)
        self.assertIn("- Status: approved", self._plan_text(), "nothing may have moved")

    def test_finish_never_pushes_or_tags_measured_over_real_git_invocations(self):
        """SAFETY: the execution contract forbids an agent pushing or tagging. Measured, not grepped.

        WHAT THIS REPLACES AND WHY. The previous form searched `run_finish`'s source for `"push"`,
        `"tag"`, `git push` and `git tag`. That was weak in both directions: its own docstring says
        "never pushes, never tags", so ADDING an accurate comment breaks it, while DELEGATING to any
        helper that pushes leaves it green - and `run_finish` does delegate, to `status_set`, which
        reaches git through `artifact_core`. So the pin checked the one function that was never the
        risk.

        The recorder wraps `subprocess.Popen`, the single constructor every `run`/`check_output`/
        `check_call` route goes through, and the assertion is over the git SUBCOMMAND of each real
        invocation. A push anywhere beneath `aw finish`, however deep, is therefore caught; see
        `_GitArgvRecorder` and `_git_subcommand`.
        """
        self._write_evidence()
        with _GitArgvRecorder() as recorder:
            rc, out = self._run(
                ["finish", "wk0001", "--dir", str(self.root), "--to", "reviewed"]
            )
        self.assertEqual(rc, 0, out)
        self.assertIn("- Status: reviewed", self._plan_text(), out)

        # NON-VACUITY: if nothing git-shaped was recorded, the recorder saw nothing and the
        # assertion below would pass no matter what `aw finish` did.
        observed = recorder.git_subcommands()
        self.assertTrue(
            observed,
            "the recorder observed NO git invocation during a successful `aw finish`, so the "
            "forbidden-subcommand assertion below would be vacuous. Either the interception point "
            "moved (see _GitArgvRecorder for why it is `subprocess.Popen`) or `aw finish` no longer "
            "touches git at all.",
        )

        offending = recorder.offending()
        self.assertEqual(
            offending,
            [],
            "`aw finish` invoked a FORBIDDEN git subcommand:\n"
            + "\n".join(
                f"  {sub}: {argv!r}\n    forbidden because: {FORBIDDEN_GIT_SUBCOMMANDS[sub]}"
                for sub, argv in offending
            )
            + "\n(Observed git subcommands this run: "
            + ", ".join(observed)
            + ".) An agent must never push or tag; a tag or release is permitted only inside "
            "release-review after an explicit human GO. Note this catches an INDIRECT invocation "
            "through a collaborator such as `status_set`, so the fix may be in the helper rather "
            "than in `run_finish` itself.",
        )

    def test_the_forbidden_subcommand_scan_fires_on_a_planted_push(self):
        """NON-VACUITY CONTROL for the safety test above, in the same file.

        A safety assertion that cannot be shown to FIRE is decoration. This plants a real
        `git push` (against a local file remote, so nothing leaves the machine) inside the recorder's
        scope and requires the same predicate to catch it, INCLUDING the indirect shape the old
        source-text pin could not see: the push is issued from a helper function, not inline.

        THE REMOTE LIVES INSIDE THIS TEST'S OWN TEMP TREE, in its own `TemporaryDirectory` rather
        than beside `self.root`. Found by running this file twice: a remote placed at
        `self.root.parent` outlived the per-test cleanup, so the SECOND run pushed to a bare repo
        that already carried `refs/heads/planted` and git rejected the non-fast-forward, failing the
        test for a reason that had nothing to do with the property under test.
        """
        remote_home = tempfile.TemporaryDirectory()
        self.addCleanup(remote_home.cleanup)
        remote = Path(remote_home.name) / "planted-remote.git"
        subprocess.run(
            ["git", "init", "-q", "--bare", str(remote)], check=True, cwd=self.root
        )

        def _helper_that_pushes():
            # Deliberately indirect: `run_finish` would satisfy a source-text pin while a callee
            # like this one does the pushing. The recorder sees it regardless.
            subprocess.run(
                ["git", "push", "--quiet", str(remote), "HEAD:refs/heads/planted"],
                cwd=self.root,
                check=True,
                capture_output=True,
            )

        with _GitArgvRecorder() as recorder:
            _helper_that_pushes()
            subprocess.run(
                ["git", "tag", "planted-tag"],
                cwd=self.root,
                check=True,
                capture_output=True,
            )

        caught = sorted(sub for sub, _argv in recorder.offending())
        self.assertEqual(
            caught,
            ["push", "tag"],
            "the forbidden-subcommand scan failed to catch a PLANTED violation, so the safety test "
            f"above proves nothing. It caught {caught!r} out of ['push', 'tag']. Recorded git "
            f"subcommands: {recorder.git_subcommands()!r}. FIX `_git_subcommand` / "
            "`_GitArgvRecorder`, not the test that uses them.",
        )

    def test_the_forbidden_subcommand_scan_does_not_fire_on_a_message_mentioning_push(
        self,
    ):
        """The other half of the control: the scan must key on the SUBCOMMAND, not on a substring.

        This is the false-positive the replaced text pin would have had: `git commit -m "do not
        push"` contains `push`, and a legitimate commit must not be reported as a push.
        """
        (self.root / "src" / "x.py").write_text("print('x')\n", encoding="utf-8")
        with _GitArgvRecorder() as recorder:
            subprocess.run(
                ["git", "add", "src/x.py"],
                cwd=self.root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-q",
                    "-m",
                    "do not push and do not tag",
                    "--",
                    "src/x.py",
                ],
                cwd=self.root,
                check=True,
                capture_output=True,
            )
            # A global flag before the subcommand must not confuse the parser either.
            subprocess.run(
                ["git", "-C", str(self.root), "status", "--porcelain"],
                check=True,
                capture_output=True,
            )
        self.assertEqual(
            recorder.offending(),
            [],
            "the scan reported a forbidden subcommand for an argv that merely MENTIONS push/tag in "
            "a commit message. A substring search over the whole argv (which is what the replaced "
            f"source-text pin effectively did) has exactly this defect. Recorded: {recorder.argvs!r}",
        )
        self.assertEqual(
            recorder.git_subcommands(),
            ["add", "commit", "status"],
            "the parser must skip git's global flags (`-C <dir>`) to find the real subcommand",
        )


class _Fixture:
    """A throwaway repo carrying `_PLAN`, for a table row that needs its own tree.

    Kept a plain class rather than a second TestCase so `FINISH_GATES` can build one per row: several
    of its rows differ ONLY in what evidence exists on disk, so sharing `setUp`'s tree would let one
    row's record satisfy the next row's gate.
    """

    def __init__(self, base: Path) -> None:
        self.root = base / "repo"
        self.root.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.root, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.root, check=True)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)
        self.plan = self.plans / "20260828-wk-01-wk0001-demo.ipd.md"
        self.plan.write_text(_PLAN, encoding="utf-8")
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / ".gitignore").write_text(
            ".aw/worktrees/\n.aw/state/\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=self.root, check=True)

    def write_evidence(self, exit_code: int = 0, stale: bool = False) -> None:
        ev_dir = self.root / ".aw" / "state" / "work" / "wk0001"
        ev_dir.mkdir(parents=True, exist_ok=True)
        tree = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"],
            cwd=self.root,
            capture_output=True,
            text=True,
        ).stdout.strip()
        (ev_dir / "test-evidence.json").write_text(
            json.dumps(
                {
                    "schema_version": "aw.work-evidence/v1",
                    "plan_id": "wk0001",
                    "assurance": "local-forgeable",
                    "command": ["true"],
                    "exit_code": exit_code,
                    "git_tree": "0" * 40 if stale else tree,
                    "git_head": "x",
                }
            ),
            encoding="utf-8",
        )

    def run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv)
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue() + err.getvalue()

    def plan_text(self) -> str:
        return self.plan.read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
