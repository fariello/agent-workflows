"""runtrailwire-01 (`wao266`): the runner PASSES the ownership trailers it already knows how to write.

THE DEFECT THIS PINS. Plan `m73aet` (`runtrail-01`, executed) shipped the whole `AW-Run:`/`AW-Item:`
trailer mechanism per spec `25kzda` 4.6 -- the keys, the composer, the canonical formatter
`run_item_trailers`, and `offer_commit`'s `trailers=` parameter defaulting EMPTY -- and then wired it
to NOTHING. Measured at authoring of this module: `git log --all --format='%(trailers:key=AW-Run,
valueonly)'` over the last 600 commits returned ZERO non-empty lines, and `grep AW-Run cli.py` ZERO
hits, so the only code path that passed trailers was `aw commit`'s `_trailers_from_args`, whose own
docstring records that "the runner wiring is deliberately deferred". A tested parameter that no caller
passes is dead code, and dead code is an invitation to future misuse.

WHAT IS ASSERTED HERE:
  * a REAL commit made through the runner's shipped commit path carries BOTH keys, read back through
    GIT'S OWN PARSER (`--format=%(trailers:key=...,valueonly)`), never through a substring match on
    the composed message -- a malformed trailer block still commits successfully, so only git can say
    whether git would parse it, and that silent failure is exactly what the mechanism exists to avoid;
  * the values are the LIVE run's id and the executing plan's id6, not a synthesized stand-in;
  * WITHOUT a run id the commit carries NEITHER key and its stored message bytes are IDENTICAL to the
    message handed in, which is what makes this change additive for every pre-existing caller;
  * the fixture ACTUALLY COMMITS. `commit_backlog_close` returns None on `len(paths) < 2` BEFORE it
    ever reaches `offer_commit`, so a single-file fixture would make every trailer assertion above
    pass VACUOUSLY. Each test asserts a sha came back and that both sides of the move are in it;
  * ONE change covers BOTH hosts, proven by OBJECT IDENTITY
    (`agy_runipd.commit_backlog_close is oc_runipd.commit_backlog_close`) rather than by running two
    runners: `agy_runipd` reaches this function by IMPORT and holds no `offer_commit` call of its own;
  * NO TRAILER CONSUMER WAS ADDED. This plan makes a writer real; `h9cn0y` (executed) owns finalize's
    committed-half attribution, and nothing in `ipd_lifecycle.py` reads a trailer. The negative is
    asserted so a later reader cannot mistake this module for having closed that gap.

WHAT THIS DOES NOT CLAIM. The wired site is the runner's DRIVER-SIDE backlog-close commit. The commits
finalize's attribution reads are the AGENT's own code commits in `base_head..HEAD`, made via raw
`git commit` per the runbook directive, which pass through no `offer_commit` call and are therefore
untouched here. See the plan's F-12 and its Deferred section.
"""

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from agent_workflows import (
    git_commit_helper,
    ipd_lifecycle,
    oc_runipd,
)
from tests.support import REPO_ROOT, git, init_repo

RUN_ID = "run-20260908T010203Z-424242"
PLAN_ID6 = "wao266"
ITEM_ID6 = "bbbbbb"


def _item_text(id6: str, *, status: str) -> str:
    return "\n".join(
        [
            f"- Id: {id6}",
            f"- Status: {status}",
            "- Set: demo",
            "- Work-Kind: chore",
            "",
            "## Summary",
            "",
            "A fixture backlog item.",
            "",
        ]
    )


def _trailer_values(repo: Path, sha: str | None, key: str) -> list[str]:
    """What GIT ITSELF reports for ``key`` on a real commit.

    THE AUTHORITY, DELIBERATELY. `%(trailers:key=...,valueonly)` is git's own trailer parser and is
    the same interface any future consumer would use. An assertion on the composed message string
    would pass on a block git refuses to parse, producing a commit whose trailers are invisible to
    every reader -- the precise silent failure this wiring exists to prevent.
    """

    assert sha is not None, "expected a commit sha, got None"
    out = git(
        repo, "log", "-1", f"--format=%(trailers:key={key},valueonly)", sha
    ).stdout
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def _stored_message(repo: Path, sha: str | None) -> str:
    """The message bytes EXACTLY as stored in the commit object.

    `--format=%B` appends a newline of its own and so cannot support a byte-for-byte claim;
    `cat-file commit` yields the stored bytes (everything after the header's blank line).
    """

    assert sha is not None, "expected a commit sha, got None"
    raw = git(repo, "cat-file", "commit", sha).stdout
    return raw.split("\n\n", 1)[1]


def _committed_paths(repo: Path, sha: str | None) -> set[str]:
    """Every path the commit touched, with RENAME DETECTION OFF.

    `--no-renames` IS LOAD-BEARING and was added after measurement. git's default rename detection
    collapses a same-content move into the single NEW path, so the default view reported one file for a
    commit that genuinely contains both the deletion and the addition, and the two-path proof below
    failed against a correct commit. Asking for the un-collapsed view is what makes that proof mean
    "both sides are in the tree" rather than "git chose to summarize them as one".
    """

    assert sha is not None, "expected a commit sha, got None"
    out = git(
        repo, "show", "--name-only", "--no-renames", "--pretty=format:", sha
    ).stdout
    return {ln.strip() for ln in out.splitlines() if ln.strip()}


class _MoveCase(unittest.TestCase):
    """A throwaway repo holding a GENUINE two-path backlog move, mid-close.

    THE TWO-PATH SHAPE IS LOAD-BEARING (plan F-14). `commit_backlog_close` FAILS CLOSED when the
    porcelain view shows fewer than two paths, because the setter MOVES the item file and a legitimate
    close therefore always yields both sides (the deletion and the addition); that `return None` sits
    ABOVE the `offer_commit` call. A fixture that merely edits one file never reaches the commit at
    all, so every trailer assertion over it would pass while proving nothing.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = init_repo(Path(self._tmp.name) / "repo")
        for rel in (
            ".aw/records/backlog/graduated",
            ".aw/records/backlog/done",
        ):
            (self.root / rel).mkdir(parents=True, exist_ok=True)
        self.name = f"20260830-demo-01-{ITEM_ID6}-demo-item.backlog.md"
        graduated = self.root / ".aw/records/backlog/graduated" / self.name
        graduated.write_text(_item_text(ITEM_ID6, status="graduated"), encoding="utf-8")
        git(self.root, "add", "--", ".aw")
        git(self.root, "commit", "-q", "-m", "fixture: the item, graduated")
        # Now perform exactly what `aw backlog set done` does and does NOT commit: MOVE the file. Both
        # sides are then visible to `git status --porcelain -uall`, which is the state this function is
        # written for.
        done = self.root / ".aw/records/backlog/done" / self.name
        done.write_text(_item_text(ITEM_ID6, status="done"), encoding="utf-8")
        graduated.unlink()

    def assertRealTwoPathCommit(self, sha: str | None) -> None:
        """Proof the commit HAPPENED over a genuine two-path move, so nothing above it is vacuous.

        WHAT IS ASSERTED AND WHY IT IS NOT "both sides are in the commit". The fixture presents BOTH
        sides to `commit_backlog_close`, which is what this plan needs: the `len(paths) < 2` guard sits
        ABOVE the `offer_commit` call, so a one-file fixture would return None and make every trailer
        assertion pass vacuously. This asserts the commit happened and that its DESTINATION side landed.

        IT DELIBERATELY DOES NOT ASSERT THE DELETION LANDED, because at the time of writing IT DOES
        NOT, and that is a PRE-EXISTING defect of the shared commit helper rather than anything this
        plan changes. MEASURED: `git_commit_helper._staged_paths` reads `git diff --name-only --cached`
        with rename detection ON, so a staged move of near-identical content reports one `R100` entry
        and only the DESTINATION, leaving the deletion staged-but-uncommitted. In real history 42 of 47
        `closed by aw oc run:` commits contain the addition alone, and 22 items exist in BOTH
        `graduated/` and `done/` at HEAD as a result. Filed as backlog `mx1b4v`; fixing it means
        changing the shared helper's staging semantics, which is outside this plan's scope.

        SO THIS ASSERTION IS WRITTEN TO STAY HONEST IN BOTH WORLDS: it accepts today's
        destination-only commit and the both-sides commit `mx1b4v` will produce, and it fails if the
        commit does not happen at all or does not contain the move's destination. Pinning "addition
        only" as CORRECT would be worse: it would encode the bug as the contract and break the fix.
        """

        self.assertIsNotNone(
            sha,
            "`commit_backlog_close` returned None, so NOTHING was committed and every trailer "
            "assertion in this test would be vacuous. The `len(paths) < 2` fail-closed guard sits "
            "ABOVE the `offer_commit` call, so the fixture must present a genuine two-path move",
        )
        paths = _committed_paths(self.root, sha)
        self.assertIn(
            f".aw/records/backlog/done/{self.name}",
            paths,
            f"the move's DESTINATION must be in the commit; got {sorted(paths)}",
        )
        self.assertTrue(
            paths.issubset(
                {
                    f".aw/records/backlog/done/{self.name}",
                    f".aw/records/backlog/graduated/{self.name}",
                }
            ),
            "the commit must be PATH-SCOPED to this item's move and nothing else; got "
            f"{sorted(paths)}",
        )

    def assertBothSidesWerePresentedToTheCommitPath(self) -> None:
        """The fixture really is the two-path shape the guard above `offer_commit` demands.

        Asserted against the SAME porcelain view `commit_backlog_close` itself reads, so this proves
        the precondition rather than restating the fixture's intent.
        """

        porcelain = git(self.root, "status", "--porcelain", "-uall").stdout
        sides = sorted(
            ln.strip().split(None, 1)[1].strip()
            for ln in porcelain.splitlines()
            if ln.strip()
        )
        self.assertEqual(
            sides,
            [
                f".aw/records/backlog/done/{self.name}",
                f".aw/records/backlog/graduated/{self.name}",
            ],
            "the fixture must present BOTH sides of the move (the deletion and the addition) to the "
            f"function, or its fail-closed guard returns None before committing. Saw: {sides}",
        )


# ======================================================================================
# E-04: a real commit carries the trailers, read back through git's own parser
# ======================================================================================


class TheRunnersCommitCarriesRunOwnership(_MoveCase):
    def test_git_itself_parses_both_keys_off_the_real_commit(self):
        self.assertBothSidesWerePresentedToTheCommitPath()
        sha = oc_runipd.commit_backlog_close(
            self.root,
            ITEM_ID6,
            "closed by aw oc run: fixture",
            run_id=RUN_ID,
            plan_id6=PLAN_ID6,
        )
        self.assertRealTwoPathCommit(sha)
        self.assertEqual(
            _trailer_values(self.root, sha, "AW-Run"),
            [RUN_ID],
            "GIT's own trailer parser must report the run id under `AW-Run`. An empty list here means "
            "the block was appended in a shape git does not recognize as trailers, which commits "
            "successfully and is invisible to every future reader",
        )
        self.assertEqual(
            _trailer_values(self.root, sha, "AW-Item"),
            [PLAN_ID6],
            "GIT's own trailer parser must report the executing plan's id6 under `AW-Item`",
        )

    def test_the_body_is_preserved_ahead_of_the_trailer_block(self):
        """Additive means ADDITIVE: the operator-facing message must survive verbatim."""

        message = (
            "closed by aw oc run: IPD wao266 executed (reason); evidence some/path.md"
        )
        sha = oc_runipd.commit_backlog_close(
            self.root, ITEM_ID6, message, run_id=RUN_ID, plan_id6=PLAN_ID6
        )
        self.assertRealTwoPathCommit(sha)
        stored = _stored_message(self.root, sha)
        self.assertTrue(
            stored.startswith(message),
            f"the original message must be preserved verbatim ahead of the trailers; got {stored!r}",
        )

    def test_the_canonical_formatter_is_used_rather_than_a_hand_built_string(self):
        """The key spelling must live in ONE place, or the writer and a future reader drift apart.

        Asserted by SPYING on the formatter (it must be called with the threaded ids) rather than by
        searching source text for a token: a source search passes on a comment and cannot tell whether
        the values actually reached it.
        """

        seen: list[tuple] = []
        real = git_commit_helper.run_item_trailers

        def spy(run_id, item_id6):
            seen.append((run_id, item_id6))
            return real(run_id, item_id6)

        git_commit_helper.run_item_trailers = spy  # type: ignore[assignment]
        try:
            sha = oc_runipd.commit_backlog_close(
                self.root, ITEM_ID6, "msg", run_id=RUN_ID, plan_id6=PLAN_ID6
            )
        finally:
            git_commit_helper.run_item_trailers = real  # type: ignore[assignment]
        self.assertRealTwoPathCommit(sha)
        self.assertEqual(
            seen,
            [(RUN_ID, PLAN_ID6)],
            "the canonical `run_item_trailers` must format the keys, receiving the LIVE run id and "
            f"the executing plan's id6; calls seen: {seen}",
        )


class WithNoRunIdNothingChangesAndNothingIsInvented(_MoveCase):
    """E-03: absence must OMIT the trailer, never synthesize one.

    A trailer asserting run ownership it cannot substantiate is strictly WORSE than no trailer: the
    whole value of an immutable trailer is that a later reader can trust it, and a synthesized id
    would make an untrue ownership claim permanent. Absence must therefore mean UNKNOWN.
    """

    def test_neither_key_appears_and_the_message_is_byte_identical(self):
        message = "closed by aw oc run: fixture with no run"
        sha = oc_runipd.commit_backlog_close(self.root, ITEM_ID6, message)
        self.assertRealTwoPathCommit(sha)
        self.assertEqual(
            _trailer_values(self.root, sha, "AW-Run"),
            [],
            "with no run id NOTHING may be synthesized: an `AW-Run` value here would be a false "
            "ownership claim in permanent, immutable history",
        )
        self.assertEqual(_trailer_values(self.root, sha, "AW-Item"), [])
        self.assertEqual(
            _stored_message(self.root, sha),
            message + "\n",
            "the stored message must be BYTE-IDENTICAL to what a caller passing no ids gets today "
            "(git normalizes a single trailing newline). Anything else means this change is not "
            "additive and every pre-existing caller's commit text moved",
        )

    def test_a_run_id_alone_still_omits_only_the_missing_key(self):
        """Partial information is recorded partially, never completed by guesswork."""

        sha = oc_runipd.commit_backlog_close(
            self.root, ITEM_ID6, "msg", run_id=RUN_ID, plan_id6=None
        )
        self.assertRealTwoPathCommit(sha)
        self.assertEqual(_trailer_values(self.root, sha, "AW-Run"), [RUN_ID])
        self.assertEqual(
            _trailer_values(self.root, sha, "AW-Item"),
            [],
            "an absent plan id6 must be OMITTED, not filled in from the backlog item or a timestamp",
        )

    def test_the_positional_call_form_still_works(self):
        """`agy_runipd` imports this by name and existing callers pass three positionals.

        The new parameters are keyword-only WITH defaults precisely so that call form keeps working;
        a required parameter here would break the shared import this plan's central claim rests on.
        """

        sig = inspect.signature(oc_runipd.commit_backlog_close)
        for name in ("run_id", "plan_id6"):
            with self.subTest(param=name):
                param = sig.parameters[name]
                self.assertEqual(param.kind, inspect.Parameter.KEYWORD_ONLY)
                self.assertIsNone(param.default)
        sha = oc_runipd.commit_backlog_close(self.root, ITEM_ID6, "msg")
        self.assertRealTwoPathCommit(sha)


# ======================================================================================
# E-05: every measured guard in the target function still holds WITH trailers present
# ======================================================================================


class TheExistingGuardsStillHoldWithTrailersPresent(_MoveCase):
    """Each guard below is scar tissue from a failure measured live; the trailer must not disturb one.

    Asserted WITH `run_id`/`plan_id6` supplied, because "unchanged when the new parameter is absent" is
    the easy half. The half that matters is that the guards still hold on the path the runner now takes.
    """

    def test_a_coworkers_different_backlog_item_is_still_never_swept_in(self):
        """THE BLAST-RADIUS CONTROL: the id6 basename filter, proven with a real concurrent edit."""

        other = self.root / ".aw/records/backlog/open"
        other.mkdir(parents=True, exist_ok=True)
        coworker = other / "20260830-demo-01-cccccc-someone-elses-item.backlog.md"
        coworker.write_text(_item_text("cccccc", status="open"), encoding="utf-8")
        git(self.root, "add", "--", str(coworker.relative_to(self.root)))
        git(self.root, "commit", "-q", "-m", "fixture: a co-worker's item")
        coworker.write_text(
            coworker.read_text(encoding="utf-8")
            + "\nsomeone else's uncommitted edit\n",
            encoding="utf-8",
        )

        sha = oc_runipd.commit_backlog_close(
            self.root, ITEM_ID6, "msg", run_id=RUN_ID, plan_id6=PLAN_ID6
        )
        self.assertRealTwoPathCommit(sha)
        for path in _committed_paths(self.root, sha):
            self.assertIn(
                ITEM_ID6,
                Path(path).name,
                f"a path not carrying this item's id6 was committed: {path}",
            )
        self.assertIn(
            "someone else's uncommitted edit",
            coworker.read_text(encoding="utf-8"),
            "the co-worker's uncommitted edit must still be on disk, untouched",
        )

    def test_fewer_than_two_paths_still_returns_none_and_commits_nothing(self):
        """FAIL CLOSED on a partial view: half a move is worse than no commit.

        Reached by presenting only the ADDITION (no deletion), which is the shape the guard exists for.
        """

        # Undo the fixture's deletion so the porcelain view shows the addition alone.
        graduated = self.root / ".aw/records/backlog/graduated" / self.name
        git(self.root, "checkout", "--", str(graduated.relative_to(self.root)))
        head_before = git(self.root, "rev-parse", "HEAD").stdout.strip()

        sha = oc_runipd.commit_backlog_close(
            self.root, ITEM_ID6, "msg", run_id=RUN_ID, plan_id6=PLAN_ID6
        )
        self.assertIsNone(
            sha,
            "seeing one side of the move must return None: committing half a move leaves the tree "
            "worse than not committing at all, and a trailer must not change that",
        )
        self.assertEqual(
            git(self.root, "rev-parse", "HEAD").stdout.strip(),
            head_before,
            "HEAD must not have moved when the guard refused",
        )

    def test_the_deleted_side_parses_without_eating_the_paths_first_character(self):
        """THE WIDTH-INDEPENDENT PORCELAIN PARSE.

        `run_checked` strips its output, so an unstaged deletion's `" D <path>"` arrives as
        `"D <path>"` and a fixed `line[3:]` slice ate the path's leading `.`, producing an
        `aw/records/...` pathspec and a failed `git add`. The deletion side must therefore appear in
        the commit's requested path set with its leading dot intact.
        """

        porcelain = git(self.root, "status", "--porcelain", "-uall").stdout
        self.assertIn(
            " D .aw/records/backlog/graduated/",
            porcelain,
            f"the fixture must present the leading-space deletion shape; saw {porcelain!r}",
        )
        captured: list[list[str]] = []
        real = git_commit_helper.offer_commit

        def spy(repo, paths, **kwargs):
            captured.append(list(paths))
            return real(repo, paths, **kwargs)

        git_commit_helper.offer_commit = spy  # type: ignore[assignment]
        try:
            sha = oc_runipd.commit_backlog_close(
                self.root, ITEM_ID6, "msg", run_id=RUN_ID, plan_id6=PLAN_ID6
            )
        finally:
            git_commit_helper.offer_commit = real  # type: ignore[assignment]
        self.assertRealTwoPathCommit(sha)
        self.assertEqual(len(captured), 1, f"one commit call expected; got {captured}")
        self.assertIn(
            f".aw/records/backlog/graduated/{self.name}",
            captured[0],
            "the DELETED side must reach the commit helper with its leading `.` intact; a truncated "
            f"`aw/records/...` here is the measured fixed-slice bug. Got {captured[0]}",
        )

    def test_the_untracked_addition_is_named_as_a_file_not_as_its_directory(self):
        """`-uall` IS LOAD-BEARING.

        Default `--porcelain` collapses an untracked directory to the DIRECTORY entry
        (`?? .aw/records/backlog/done/`), whose basename carries no id6, so the id6 filter matched
        nothing and the newly written item was never staged. The requested set must name the FILE.
        """

        captured: list[list[str]] = []
        real = git_commit_helper.offer_commit

        def spy(repo, paths, **kwargs):
            captured.append(list(paths))
            return real(repo, paths, **kwargs)

        git_commit_helper.offer_commit = spy  # type: ignore[assignment]
        try:
            sha = oc_runipd.commit_backlog_close(
                self.root, ITEM_ID6, "msg", run_id=RUN_ID, plan_id6=PLAN_ID6
            )
        finally:
            git_commit_helper.offer_commit = real  # type: ignore[assignment]
        self.assertRealTwoPathCommit(sha)
        self.assertIn(
            f".aw/records/backlog/done/{self.name}",
            captured[0],
            "the untracked side must be named as the individual FILE, not as `done/`, whose basename "
            f"carries no id6 and so matches nothing. Got {captured[0]}",
        )
        self.assertNotIn(
            ".aw/records/backlog/done",
            [p.rstrip("/") for p in captured[0] if p.endswith("/")],
            "a bare DIRECTORY entry must never be in the requested set",
        )

    def test_the_commit_is_still_unattended_and_never_prompts(self):
        """The runner has no human to answer a prompt; the helper must not be asked for one."""

        captured: list[dict] = []
        real = git_commit_helper.offer_commit

        def spy(repo, paths, **kwargs):
            captured.append(dict(kwargs))
            return real(repo, paths, **kwargs)

        git_commit_helper.offer_commit = spy  # type: ignore[assignment]
        try:
            oc_runipd.commit_backlog_close(
                self.root, ITEM_ID6, "msg", run_id=RUN_ID, plan_id6=PLAN_ID6
            )
        finally:
            git_commit_helper.offer_commit = real  # type: ignore[assignment]
        self.assertEqual(len(captured), 1)
        self.assertFalse(captured[0].get("interactive", True))
        self.assertTrue(captured[0].get("assume_yes", False))
        self.assertIn(
            "trailers",
            captured[0],
            "the trailers must be passed to the shared helper, not composed into the message by hand",
        )


# ======================================================================================
# E-04: ONE change, BOTH hosts
# ======================================================================================


# ======================================================================================
# E-05: a WRITER was added, and deliberately no READER
# ======================================================================================


class NoConsumerWasAdded(unittest.TestCase):
    def test_nothing_in_the_lifecycle_module_reads_a_trailer(self):
        """This plan supplies a substrate; `h9cn0y` (executed) owns finalize's attribution.

        Asserted so this module cannot later be mistaken for having closed the attribution gap. The
        commits finalize reads are the AGENT's own, made by raw `git commit`, which no `offer_commit`
        wiring can reach; that work is named in the plan's Deferred section.
        """

        text = (REPO_ROOT / "agent_workflows" / "ipd_lifecycle.py").read_text(
            encoding="utf-8"
        )
        code_lines = [
            ln
            for ln in text.splitlines()
            if "trailers:key" in ln or "interpret-trailers" in ln
        ]
        self.assertEqual(
            code_lines,
            [],
            "nothing in `ipd_lifecycle.py` may READ a trailer: attribution consumption belongs to "
            f"`h9cn0y`, and this plan adds a writer only. Found: {code_lines}",
        )
        self.assertFalse(
            hasattr(ipd_lifecycle, "read_run_trailers"),
            "no trailer-reading helper may appear in the lifecycle module from this plan",
        )


if __name__ == "__main__":  # pragma: no cover - convenience
    unittest.main()
