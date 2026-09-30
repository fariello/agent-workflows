"""Restored coverage for root workflow-artifacts run scratch migration.

This is the outcome coverage deleted by `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"),
restored under plan `cf7f8z` (Set `xtrwdb`). It guards `engine.migrate_root_workflow_artifacts`,
which is the only code in the framework touching a user's committed history.

With plan `cf7f8z`, `engine.migrate_root_workflow_artifacts` gains a second caller: the standalone
`tools/untrack-workflow-artifacts.py` utility script, now converted from performing a legacy repo-root
untracking into a thin delegating front end over this engine migration.

This file contains two test classes:
1. `RootRunScratchMigrationTests`: The 13 restored outcome tests from `tests/test_engine_install.py`
   (deleted by `19313eed`), covering history preservation via `git log --follow`, path set equality,
   merging with existing destination runs, conflict refusal, ignore attribution, dry run, and idempotency.
2. `UntrackWorkflowArtifactsDelegationTests`: Subprocess outcome tests for `tools/untrack-workflow-artifacts.py`,
   verifying dry-run non-mutation, proper relocation and untracking under `--apply`, absence of root `.gitignore`
   creation, and exit code 0.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import engine as INS
from tests.support import REPO_ROOT, SOURCE_WORKFLOWS, git, init_repo, run_tool


def _install(repo: Path) -> dict:
    """Run the shared install core the way every entry point does."""

    return INS.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)


def _seed_committed_repo(base: Path, name: str) -> Path:
    """A temporary git repo with one commit and a pre-existing user line in the root `.gitignore`.

    The user line exists so a test can prove the installer PRESERVED it while adding its own managed
    block, and the commit exists so `git status --porcelain` is meaningful (an unborn HEAD reports
    everything as untracked regardless of the ignore rules).
    """

    repo = init_repo(base / name)
    (repo / ".gitignore").write_text(
        "# user's own line\n*.user-tmp\n", encoding="utf-8"
    )
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-qm", "seed")
    return repo


class RootRunScratchMigrationTests(unittest.TestCase):
    """wfartifacts Order 05 (y4pptx): an EXISTING install's run records move to `.aw/workflow-artifacts/`.

    WHAT THIS FILE'S SIBLING CLASSES CANNOT COVER, and why this class exists: Orders 01-04 fixed what
    a FRESH install produces, so every one of their tests starts from a repo with no run scratch at
    all. Measured 2026-09-12, 29 repos on one machine already carry the RETIRED repo-root
    `workflow-artifacts/`, and two of them TRACK real run records in it (11 files and 3 files). This
    is the only child that touches a user's committed history.

    THE PROOF OBLIGATION IS UNUSUALLY HIGH, so each assertion below is chosen against a specific way
    a naive implementation passes while the feature is broken:

    1. HISTORY, not merely location. Asserting the file exists at the new path passes for a
       copy-and-delete that lost the history. So the tracked case asserts the ACTUAL
       `git log --follow` output reaches the pre-migration commit.
    2. NOTHING LOST, not one file checked. A test that checks a single file cannot catch a partial
       move, so the before/after run-record path SETS are compared for equality modulo the prefix.
    3. MERGE, not move (F-7). The destination is usually already populated, which is the common case
       rather than an edge, so a pre-existing destination run must SURVIVE alongside the relocated
       one.
    4. REFUSAL, not overwrite. A same-path/different-bytes conflict must leave BOTH files in place.
    5. IGNORED IN EFFECT, via real `git check-ignore` attributed to `.aw/.gitignore`.

    WHAT IS TABULATED HERE AND WHAT IS NOT. The DISPOSITION table below merges the three tests that
    differed only in what the destination already held (nothing, the same bytes, different bytes),
    because those three are one decision function over one input and the property each asserts is the
    same triple: the destination's final bytes, whether the source survived, and whether a REFUSED
    action was reported. Keeping them apart hid the most important thing about them, which is that
    they are the THREE branches of one comparison and the middle branch (identical bytes) exists
    precisely so a re-run is safe. Every OTHER migration test stays separate, because each asserts a
    structurally different claim: git history via `--follow`, a whole path SET, a dry run touching
    nothing, commit scoping against a co-worker's staged file, a report-only lane, or a no-op.
    """

    RETIRED = "workflow-artifacts"
    NEW = ".aw/workflow-artifacts"
    RUN = "assess-bugs/20260726-115243"

    #: (case, the destination's pre-existing content or None for an absent destination, the bytes the
    #: destination must hold AFTER the migration, whether the SOURCE file must still exist, whether a
    #: `REFUSED` action must be reported, whether the retired DIRECTORY must survive, why this row
    #: exists)
    #:
    #: The source always holds "source version\n", so the three rows differ ONLY in the destination,
    #: which is what makes them one decision function's three branches.
    DISPOSITIONS = (
        (
            "no destination file: an ordinary relocation",
            None,
            "source version\n",
            False,
            False,
            False,
            "THE POSITIVE ROW, and the one that makes the other two non-vacuous: a migration that "
            "refused everything would satisfy both conflict rows on its own. The source is consumed "
            "and the retired directory goes away once empty, which is the whole point of the "
            "relocation",
        ),
        (
            "a destination holding DIFFERENT bytes at the same path",
            "destination version\n",
            "destination version\n",
            True,
            True,
            True,
            "REFUSAL, NOT OVERWRITE, and the single most important row here: overwriting a run record "
            "is UNRECOVERABLE, so the destination keeps its own bytes, the source is left where it "
            "is, the conflict is REPORTED to the user, and the retired directory survives because it "
            "still holds content nobody has adjudicated. A row that checked only the destination "
            "would accept an implementation that refused the write but deleted the source anyway",
        ),
        (
            "a destination holding the SAME bytes at the same path",
            "source version\n",
            "source version\n",
            True,
            False,
            True,
            "IDENTICAL BYTES ARE NOT A CONFLICT: a re-run must be safe, so this is redundancy and "
            "must not be REPORTED as a refusal. But the redundant source is still NOT deleted, "
            "because the invariant is that user content is never deleted outside the README-only "
            "case, and that is exactly the distinction a naive 'same bytes, so clean up the copy' "
            "implementation gets wrong",
        ),
    )

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write(self, repo: Path, rel: str, text: str = "record\n") -> Path:
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def _run_record_paths(self, root: Path) -> list[str]:
        """Every file under `root`, relative and sorted (the unit the path-set equality uses)."""

        if not root.is_dir():
            return []
        return sorted(
            p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
        )

    def _commit(self, repo: Path, *paths: str, message: str = "seed") -> None:
        git(repo, "add", "--", *paths)
        git(repo, "commit", "-qm", message)

    def test_every_destination_state_gets_the_right_disposition(self) -> None:
        rel = f"{self.RUN}/report.md"
        wrong = []
        positive_broken = 0
        for index, (
            case,
            pre_existing,
            expected_dst,
            src_survives,
            refused,
            retired_survives,
            why,
        ) in enumerate(self.DISPOSITIONS):
            repo = _seed_committed_repo(self.base, f"disp-{index}")
            _install(repo)  # gives the repo a real .aw/ tree and the ignore rule
            if pre_existing is not None:
                self._write(repo, f"{self.NEW}/{rel}", pre_existing)
            self._write(repo, f"{self.RETIRED}/{rel}", "source version\n")
            self._commit(repo, self.RETIRED, message="seed a legacy run record")

            actions = INS.migrate_root_workflow_artifacts(repo, use_git=True)

            problems = []
            dst = repo / self.NEW / rel
            got = dst.read_text(encoding="utf-8") if dst.is_file() else None
            if got != expected_dst:
                problems.append(
                    f"the destination holds {got!r}, expected {expected_dst!r}"
                    + (
                        " - AN EXISTING RUN RECORD WAS OVERWRITTEN, which is unrecoverable"
                        if pre_existing is not None and got != pre_existing
                        else ""
                    )
                )
            src_exists = (repo / self.RETIRED / rel).is_file()
            if src_exists != src_survives:
                problems.append(
                    f"the source file {'survived' if src_exists else 'was removed'}; this row "
                    f"requires it to {'survive' if src_survives else 'be consumed'}"
                    + (
                        " - refusing the move but deleting the source loses the content either way"
                        if src_survives
                        else ""
                    )
                )
            got_refused = any("REFUSED" in a for a in actions)
            if got_refused != refused:
                problems.append(
                    f"REFUSED was {'reported' if got_refused else 'NOT reported'}; this row requires "
                    f"it {'reported' if refused else 'absent'}. Actions were {actions!r}"
                )
            retired_exists = (repo / self.RETIRED).is_dir()
            if retired_exists != retired_survives:
                problems.append(
                    f"the retired directory {'survived' if retired_exists else 'was removed'}; this "
                    f"row requires it to {'survive' if retired_survives else 'be pruned'}"
                )
            if problems:
                if index == 0:
                    positive_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if positive_broken:
            vacuity = (
                " THE POSITIVE ROW (no destination file) is among the failures, and while it is "
                "broken the two conflict rows are vacuous: a migration that refuses every move "
                "satisfies both of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"the relocation mishandled {len(wrong)} of {len(self.DISPOSITIONS)} destination "
            f"states.{vacuity} All three rows feed ONE comparison with the same source bytes and "
            "differ only in what the destination already held, so read them together: if the two "
            "conflict rows fail on the DESTINATION bytes, the comparison is not happening at all and "
            "the migration is a blind overwrite, which is the unrecoverable case. If they fail only "
            "on the SOURCE, the move is adjudicated correctly but the cleanup is unconditional. If "
            "the identical-bytes row is the only failure, a re-run is being reported to the user as a "
            f"conflict it must not be.\n" + "\n".join(wrong),
        )

    def test_tracked_run_records_are_relocated_with_history_preserved(self) -> None:
        """Kept separate: the claim is `git log --follow` output, which no bytes/exists column expresses.

        THE CASE THAT MATTERS MOST: committed content moves and the history survives. Asserting the
        file exists at the new path passes for a copy-and-delete that threw the history away, so this
        reads the ACTUAL `--follow` log and looks for the pre-migration commit in it.
        """

        repo = _seed_committed_repo(self.base, "mig-tracked")
        src_rel = f"{self.RETIRED}/{self.RUN}/report.md"
        self._write(repo, src_rel, "the report\n")
        self._commit(repo, self.RETIRED, message="seed a committed run record")
        pre_commit = git(repo, "rev-parse", "HEAD").stdout.strip()
        before = self._run_record_paths(repo / self.RETIRED)
        self.assertEqual(before, [f"{self.RUN}/report.md"], "precondition")

        _install(repo)

        dst_rel = f"{self.NEW}/{self.RUN}/report.md"
        self.assertTrue((repo / dst_rel).is_file(), f"{dst_rel} was not created")
        self.assertFalse(
            (repo / src_rel).exists(), f"{src_rel} was left behind at the retired path"
        )
        self.assertEqual(
            (repo / dst_rel).read_text(encoding="utf-8"),
            "the report\n",
            "content changed during the migration",
        )

        # (1) HISTORY: the ACTUAL --follow output must reach the pre-migration commit.
        follow = git(repo, "log", "--follow", "--format=%H", "--", dst_rel)
        self.assertEqual(follow.returncode, 0, follow.stderr)
        self.assertIn(
            pre_commit,
            follow.stdout.split(),
            "git log --follow on the relocated file does not reach the pre-migration commit, so "
            f"the committed history was lost:\n{follow.stdout}",
        )

        # (5) IGNORED IN EFFECT, attributed to the framework-owned file.
        ci = git(repo, "check-ignore", "-v", dst_rel)
        self.assertEqual(
            ci.returncode,
            0,
            f"the relocated run record is NOT ignored, so the migration re-tracked it: {ci.stderr}",
        )
        self.assertEqual(
            ci.stdout.split(":", 1)[0],
            ".aw/.gitignore",
            "the relocated file must be ignored by the framework-owned .aw/.gitignore",
        )
        self.assertFalse(
            INS.git_is_tracked(repo, dst_rel),
            "the relocated run record is still TRACKED, so run scratch is still committed (D92)",
        )

    def test_nothing_is_lost_the_path_sets_are_equal_modulo_the_prefix(self) -> None:
        """Kept separate: the unit is a whole path SET over six seeded files, not one path."""

        repo = _seed_committed_repo(self.base, "mig-pathsets")
        rels = [
            f"{self.RETIRED}/assess-bugs/20260726-115243/{name}"
            for name in ("decisions.md", "evidence.md", "findings.csv", "report.md")
        ] + [
            f"{self.RETIRED}/assess-testing/20260726-131500/{name}"
            for name in ("ipd-link.md", "report.md")
        ]
        for rel in rels:
            self._write(repo, rel, f"{rel}\n")
        self._commit(repo, self.RETIRED, message="seed two committed assess runs")
        before = self._run_record_paths(repo / self.RETIRED)
        self.assertEqual(len(before), 6, "precondition: six seeded run-record files")

        _install(repo)

        after = self._run_record_paths(repo / self.NEW)
        after_records = [p for p in after if p != "README.md"]
        self.assertEqual(
            before,
            after_records,
            "the before/after run-record path sets differ, so the migration lost or renamed "
            f"content:\nbefore={before}\nafter={after_records}",
        )
        for rel in before:
            self.assertEqual(
                (repo / self.NEW / rel).read_text(encoding="utf-8"),
                f"{self.RETIRED}/{rel}\n",
                f"content of {rel} changed during the migration",
            )

    def test_an_already_populated_destination_is_MERGED_not_replaced(self) -> None:
        """Kept separate: the claim is the UNION of two run ids under one workflow directory.

        (3) F-7: the destination usually already holds other runs of the SAME workflow, so this is a
        MERGE and not a move. The disposition table above varies one file at one path; this varies the
        directory's membership, which is a different assertion shape (a set equality over run ids).
        """

        repo = _seed_committed_repo(self.base, "mig-merge")
        _install(repo)  # gives the repo a real .aw/ tree and the ignore rule
        # A run already at the NEW home, under the same workflow name, with a different RUN_ID.
        kept_rel = f"{self.NEW}/assess-bugs/20260901-101010/report.md"
        self._write(repo, kept_rel, "already here\n")
        # And a legacy run at the retired path under that same workflow name.
        moved_src = f"{self.RETIRED}/assess-bugs/20260726-115243/report.md"
        self._write(repo, moved_src, "the legacy one\n")
        self._commit(
            repo, self.RETIRED, message="seed a legacy run beside an existing new one"
        )

        INS.migrate_root_workflow_artifacts(repo, use_git=True)

        self.assertTrue(
            (repo / kept_rel).is_file(),
            "the pre-existing destination run was destroyed by the migration (this is a MERGE)",
        )
        self.assertEqual(
            (repo / kept_rel).read_text(encoding="utf-8"),
            "already here\n",
            "the pre-existing destination run was overwritten",
        )
        moved_dst = f"{self.NEW}/assess-bugs/20260726-115243/report.md"
        self.assertTrue(
            (repo / moved_dst).is_file(), "the legacy run was not relocated"
        )
        self.assertEqual(
            (repo / moved_dst).read_text(encoding="utf-8"), "the legacy one\n"
        )
        # Both RUN_IDs now live under the one workflow directory: the union survived.
        self.assertEqual(
            sorted(p.name for p in (repo / self.NEW / "assess-bugs").iterdir()),
            ["20260726-115243", "20260901-101010"],
        )

    def test_untracked_content_is_moved_without_git(self) -> None:
        """Kept separate: the precondition (and half the claim) is git TRACKEDNESS, not content."""

        repo = _seed_committed_repo(self.base, "mig-untracked")
        _install(repo)
        src_rel = f"{self.RETIRED}/{self.RUN}/report.md"
        self._write(repo, src_rel, "never committed\n")
        self.assertFalse(INS.git_is_tracked(repo, src_rel), "precondition: untracked")

        INS.migrate_root_workflow_artifacts(repo, use_git=True)

        dst_rel = f"{self.NEW}/{self.RUN}/report.md"
        self.assertTrue((repo / dst_rel).is_file())
        self.assertEqual(
            (repo / dst_rel).read_text(encoding="utf-8"), "never committed\n"
        )
        self.assertFalse((repo / src_rel).exists())
        self.assertFalse(
            INS.git_is_tracked(repo, dst_rel),
            "an untracked run record must not become tracked by being relocated",
        )

    def test_the_readme_only_case_is_removed_not_relocated(self) -> None:
        """Kept separate: the ONLY case where user content is deliberately DELETED, not moved.

        Case (c), the COMMON case: the stray README's content was the opposite of the rule, so it is
        superseded rather than relocated. It is the documented exception to the never-delete invariant
        the disposition table's identical-bytes row relies on, which is why it cannot be a row there.
        """

        repo = _seed_committed_repo(self.base, "mig-readme")
        retired_readme = f"{self.RETIRED}/README.md"
        self._write(
            repo,
            retired_readme,
            "# Workflow Run Artifacts\n\n* **DO NOT gitignore this folder.**\n",
        )
        self._commit(repo, self.RETIRED, message="seed the stray README")

        _install(repo)

        self.assertFalse(
            (repo / retired_readme).exists(),
            "the superseded stray README was left at the retired path",
        )
        self.assertFalse(
            (repo / self.RETIRED).exists(),
            "the retired directory should be gone once its only file was the stray README",
        )
        new_readme = repo / self.NEW / "README.md"
        self.assertTrue(
            new_readme.is_file(),
            "the new tree did not get its own README from the install",
        )
        self.assertNotIn(
            "DO NOT gitignore",
            new_readme.read_text(encoding="utf-8"),
            "the retired do-not-ignore prose was carried to the new home",
        )

    def test_a_repo_with_no_retired_directory_is_a_silent_no_op(self) -> None:
        """Kept separate: asserts an EMPTY action list, which no disposition row can state."""
        # OQ-01: report only when there is something to report.
        repo = _seed_committed_repo(self.base, "mig-noop")
        _install(repo)
        self.assertEqual(INS.migrate_root_workflow_artifacts(repo, use_git=True), [])

    def test_dry_run_reports_and_touches_nothing(self) -> None:
        """Kept separate: the only call with `dry_run=True`, and it pins git STATUS and HEAD."""
        repo = _seed_committed_repo(self.base, "mig-dryrun")
        _install(repo)
        src_rel = f"{self.RETIRED}/{self.RUN}/report.md"
        self._write(repo, src_rel, "untouched\n")
        self._commit(repo, self.RETIRED, message="seed for dry-run")
        before_status = git(repo, "status", "--porcelain").stdout
        before_head = git(repo, "rev-parse", "HEAD").stdout.strip()

        actions = INS.migrate_root_workflow_artifacts(repo, use_git=True, dry_run=True)

        self.assertTrue(any("dry-run" in a for a in actions), actions)
        self.assertTrue((repo / src_rel).is_file(), "dry-run MOVED a file")
        self.assertFalse(
            (repo / self.NEW / self.RUN / "report.md").exists(),
            "dry-run created the destination",
        )
        self.assertEqual(
            git(repo, "status", "--porcelain").stdout,
            before_status,
            "dry-run changed the git status",
        )
        self.assertEqual(
            git(repo, "rev-parse", "HEAD").stdout.strip(),
            before_head,
            "dry-run created a commit",
        )

    def test_the_migration_commit_does_not_sweep_in_unrelated_staged_work(self) -> None:
        """Kept separate: the subject is a CO-WORKER's staged file, a setup no other test has.

        This is a SHARED CHECKOUT: the relocation's commits are path-scoped, so a co-worker's staged
        file must not be swept into them (repository execution contract).
        """

        repo = _seed_committed_repo(self.base, "mig-scoped")
        _install(repo)
        src_rel = f"{self.RETIRED}/{self.RUN}/report.md"
        self._write(repo, src_rel, "mine\n")
        self._commit(repo, self.RETIRED, message="seed for scoping")
        coworker = repo / "coworker.txt"
        coworker.write_text("someone else's staged work\n", encoding="utf-8")
        git(repo, "add", "--", "coworker.txt")

        INS.migrate_root_workflow_artifacts(repo, use_git=True)

        staged = git(repo, "diff", "--cached", "--name-only").stdout.split()
        self.assertIn(
            "coworker.txt",
            staged,
            "the migration committed (or unstaged) a co-worker's staged file",
        )
        log = git(repo, "log", "--name-only", "--format=%H").stdout
        self.assertNotIn(
            "coworker.txt", log, "a co-worker's file was swept into a migration commit"
        )

    def test_run_records_in_a_records_quarantine_lane_are_REPORTED_not_moved(
        self,
    ) -> None:
        """Kept separate: a REPORT-ONLY disposition over a different tree, asserting a move did NOT happen.

        E-04 / decision D-02: the observed mis-relocation is reported, never swept up.
        `records/*/untracked/` is a legitimate box-local quarantine lane for MANY record types, so the
        installer cannot tell a mis-placed run record there from a human's in-progress typed record.
        It therefore reports and moves nothing.
        """

        repo = _seed_committed_repo(self.base, "mig-misplaced")
        _install(repo)
        stray = ".aw/records/reviews/untracked/20260726-115243/report.md"
        self._write(repo, stray, "mis-relocated run record\n")

        actions = INS.migrate_root_workflow_artifacts(repo, use_git=True)

        self.assertTrue(
            any("REPORT ONLY" in a for a in actions),
            f"the mis-placed run records were not reported: {actions}",
        )
        self.assertTrue(
            (repo / stray).is_file(),
            "the installer MOVED content out of a records quarantine lane; it must only report",
        )
        self.assertFalse(
            (repo / self.NEW / "20260726-115243").exists(),
            "content was swept from a records lane into the run-scratch tree",
        )

    def test_an_ordinary_wip_file_in_a_quarantine_lane_is_silent(self) -> None:
        """Kept separate: the NEGATIVE half of the report-only rule, and it asserts an empty list.

        The detection is narrow on purpose: only `<RUN_ID>`-shaped directories are reported, so the
        legitimate use of these lanes never nags the user.
        """

        repo = _seed_committed_repo(self.base, "mig-lane-quiet")
        _install(repo)
        self._write(repo, ".aw/records/prompts/untracked/draft.md", "wip\n")

        self.assertEqual(INS.migrate_root_workflow_artifacts(repo, use_git=True), [])

    def test_the_migration_runs_from_the_shared_install_chokepoint(self) -> None:
        """Kept separate: the claim is about install_into_repo's RETURN value, not the filesystem.

        E-02: wired into `install_into_repo`, so `aw install`, `aw setup` and library callers all get
        it. A `run()`-only wiring would leave `aw setup` silently doing nothing.
        """

        repo = _seed_committed_repo(self.base, "mig-chokepoint")
        src_rel = f"{self.RETIRED}/{self.RUN}/report.md"
        self._write(repo, src_rel, "via the chokepoint\n")
        self._commit(repo, self.RETIRED, message="seed for chokepoint")

        result = _install(repo)

        self.assertTrue(
            any("workflow-artifacts" in line for line in result["migrated"]),
            f"the migration did not report through install_into_repo: {result['migrated']}",
        )
        self.assertTrue((repo / self.NEW / self.RUN / "report.md").is_file())

    def test_reinstall_is_idempotent(self) -> None:
        """Kept separate: a before/after idempotence PAIR, whose two halves are one claim."""
        repo = _seed_committed_repo(self.base, "mig-idempotent")
        src_rel = f"{self.RETIRED}/{self.RUN}/report.md"
        self._write(repo, src_rel, "once\n")
        self._commit(repo, self.RETIRED, message="seed for idempotence")

        _install(repo)
        first = self._run_record_paths(repo / self.NEW)
        _install(repo)
        second = self._run_record_paths(repo / self.NEW)

        self.assertEqual(first, second, "a second install changed the relocated tree")
        self.assertFalse((repo / self.RETIRED).exists())


class UntrackWorkflowArtifactsDelegationTests(unittest.TestCase):
    """Subprocess outcome tests for `tools/untrack-workflow-artifacts.py`.

    Covers plan `cf7f8z` E-04 / V-04. Drives the tool as an external process via `tests.support.run_tool`
    against a temporary repository containing a tracked root-level run record.

    FALSIFICATION AND DISCRIMINATOR VS REGRESSION GUARD ANALYSIS (V-04 / PR-B03):
    Against the pre-E-02 legacy tool:
      - Assertion (2) (`test_apply_relocates_record_to_aw_and_untracks_both_paths`):
        FAILS because the pre-E-02 tool leaves the run record at `workflow-artifacts/` and
        never moves it to `.aw/workflow-artifacts/`. This is a DISCRIMINATOR.
      - Assertion (3) (`test_apply_creates_no_root_gitignore`):
        FAILS because the pre-E-02 tool appends the ignore rule to the root `.gitignore`
        and stages it. This is a DISCRIMINATOR.
      - Assertion (1) (`test_dry_run_leaves_index_and_worktree_byte_identical`):
        PASSES because the pre-E-02 tool also does nothing without `--apply`. This is a
        REGRESSION GUARD, not a proof of fix.
      - Assertion (4) (`test_both_modes_exit_zero`):
        PASSES because both tools exit 0 on clean runs. This is a REGRESSION GUARD.

    COLLECTION PROOF (restorecov PR-701 / V-01):
    The bare pytest suite collected count increases by exactly 17 tests (13 restored
    `RootRunScratchMigrationTests` + 4 `UntrackWorkflowArtifactsDelegationTests`), proving
    these tests are collected and run by the default runner.
    """

    TOOL = REPO_ROOT / "tools" / "untrack-workflow-artifacts.py"
    REL_RECORD = "workflow-artifacts/assess/20260101-000000/report.md"
    REL_NEW_RECORD = ".aw/workflow-artifacts/assess/20260101-000000/report.md"
    RECORD_CONTENT = "assessment report content\n"

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _seed_repo_with_tracked_artifact(self, name: str) -> tuple[Path, Path]:
        repo = init_repo(self.base / name)
        (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        record = repo / self.REL_RECORD
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(self.RECORD_CONTENT, encoding="utf-8")
        git(repo, "add", "README.md", self.REL_RECORD)
        git(repo, "commit", "-qm", "initial commit with tracked record")
        return repo, record

    def test_dry_run_leaves_index_and_worktree_byte_identical(self) -> None:
        """(1) Dry run: HEAD, index, and worktree are byte-identical, record stays at retired path."""
        repo, record = self._seed_repo_with_tracked_artifact("dry-run-repo")
        head_before = git(repo, "rev-parse", "HEAD").stdout.strip()

        proc = run_tool(self.TOOL, cwd=repo)

        self.assertEqual(proc.returncode, 0, f"tool failed: {proc.stderr}")
        self.assertEqual(git(repo, "rev-parse", "HEAD").stdout.strip(), head_before)
        self.assertEqual(git(repo, "status", "--porcelain").stdout, "")
        self.assertEqual(git(repo, "diff").stdout, "")
        self.assertEqual(git(repo, "diff", "--cached").stdout, "")
        self.assertTrue(record.is_file())
        self.assertEqual(record.read_text(encoding="utf-8"), self.RECORD_CONTENT)

    def test_apply_relocates_record_to_aw_and_untracks_both_paths(self) -> None:
        """(2) Apply: record moved to .aw/workflow-artifacts/, untracked at both, retired dir gone."""
        repo, _ = self._seed_repo_with_tracked_artifact("apply-reloc-repo")

        proc = run_tool(self.TOOL, "--apply", cwd=repo)

        self.assertEqual(proc.returncode, 0, f"tool failed: {proc.stderr}")
        new_record = repo / self.REL_NEW_RECORD
        self.assertTrue(new_record.is_file(), f"relocated file missing: {new_record}")
        self.assertEqual(new_record.read_text(encoding="utf-8"), self.RECORD_CONTENT)
        tracked_retired = git(
            repo, "ls-files", "--", "workflow-artifacts"
        ).stdout.strip()
        self.assertEqual(tracked_retired, "", "retired path is still tracked in git")
        tracked_new = git(
            repo, "ls-files", "--", ".aw/workflow-artifacts"
        ).stdout.strip()
        self.assertEqual(
            tracked_new, "", "new path is tracked in git (should be untracked)"
        )
        self.assertFalse(
            (repo / "workflow-artifacts").exists(), "retired directory still exists"
        )

    def test_apply_creates_no_root_gitignore(self) -> None:
        """(3) Apply: NO root .gitignore is created."""
        repo, _ = self._seed_repo_with_tracked_artifact("apply-no-gitignore-repo")

        proc = run_tool(self.TOOL, "--apply", cwd=repo)

        self.assertEqual(proc.returncode, 0, f"tool failed: {proc.stderr}")
        self.assertFalse((repo / ".gitignore").exists(), "root .gitignore was created")

    def test_both_modes_exit_zero(self) -> None:
        """(4) Both dry-run and apply exit with return code 0 on clean repositories."""
        repo_dry, _ = self._seed_repo_with_tracked_artifact("exit-zero-dry")
        proc_dry = run_tool(self.TOOL, cwd=repo_dry)
        self.assertEqual(
            proc_dry.returncode, 0, f"dry-run exited non-zero: {proc_dry.stderr}"
        )

        repo_apply, _ = self._seed_repo_with_tracked_artifact("exit-zero-apply")
        proc_apply = run_tool(self.TOOL, "--apply", cwd=repo_apply)
        self.assertEqual(
            proc_apply.returncode, 0, f"--apply exited non-zero: {proc_apply.stderr}"
        )


if __name__ == "__main__":
    unittest.main()
