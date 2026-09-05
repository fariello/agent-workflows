"""A resumed turn whose PRIOR lane already holds finished work is routed to verify-and-continue.

resumedupe (`txc9l1`) E-06 / V-06. Every case runs on a THROWAWAY git repo built here; none of them
touch this repository's real `.aw/worktrees/`, which may hold live lanes owned by other running
drivers.

WHY THIS FILE EXISTS. Telling a resumed agent it was resuming was tried and MEASURED INSUFFICIENT:
after `build_recovery_lane_notice` shipped the lane facts into the prompt, a resumed turn still
re-implemented work a prior attempt had already committed. The reviewable proof is item `zhr6mc`,
whose two sibling commits share the subject `feat(runner): close a backlog item when the run executes
its last carrier` on INDEPENDENT parents (`42b38acf` on `bcbbfb07`, `8a9b8f32` on `144f3347`), 2118 vs
2260 insertions over the same four files; only the second was merged and the first was retired as
provably superseded. So the judgment moved to the DRIVER, and these cases pin that it actually did.

THE `zhr6mc` SHAPE IS USED DELIBERATELY, AND THE `ntf6sx` ONE IS NOT. The graduating measurement cited
`git diff fb0774b2 7e9c4444` being empty, but `7e9c4444` is a MERGE whose second parent IS `5b8c0004`
and which CONTAINS `fb0774b2`, so that empty diff is guaranteed by ancestry and proves nothing about
re-execution; worse, that second finalize was LEGITIMATE work (the merge had reverted the plan from
`executed/` back to `pending/`). Building the regression case on that shape would pin the wrong
behavior. Hence the sibling-pair shape below.

The cases, each named for the hazard it pins:

  (a)  THE REGRESSION CASE: a prior lane holding two real commits, WITH the resumed turn holding a
       fresh attempt-scoped lane at zero commits, routes `verify-and-continue`.
  (a2) THE INERTNESS GUARD, the single most important assertion here: in exactly that shape the
       decision is NOT `fresh-execution` AND the inspected lane is the PRIOR one. A classifier keyed
       on the turn's OWN lane would answer `fresh-execution` on every resume, so the feature would
       change nothing while its tests passed. Sabotaged in
       `test_a2_sabotage_reading_the_turns_own_lane_is_caught`.
  (b)  a prior lane holding ONLY an INTERRUPTED SNAPSHOT commit routes `fresh-execution`: a snapshot
       is preserved mid-edit work, so redoing it IS correct, and the feature must not blanket-skip
       whenever commits exist.
  (b2) a REAL commit whose BODY merely quotes the snapshot phrase still routes
       `verify-and-continue` (the E-02 subject-only rule).
  (c)  no recorded prior lane, an ABSENT prior lane, and an EMPTY prior lane all route
       `fresh-execution`.
  (d)  an UNREADABLE recorded lane routes `undetermined` and is DISPATCHED as `fresh-execution` with
       a recorded reason: never a skip (E-03's deliberate fail-toward-doing-the-work choice).
  (e)  a FIRST attempt is untouched, and a `fresh-execution` recovery prompt is byte-identical to
       what it was before this change.
  (f)  both drivers agree, which after E-04's delegation means the Antigravity twin RESOLVES to the
       OpenCode implementation rather than copying it.

Assertions are on the routing DECISION and on prompt CONTENT (the prior lane's branch name and its
actual shas), never on the mere presence of the word "recovery", which appears in unrelated prose and
would pass against a stub.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd as AGY
from agent_workflows import oc_runipd as OC
from agent_workflows import worktree_lease as WL


def module_source(module) -> str:
    """A module's own source text. Narrowed here because `__file__` is typed `str | None`."""
    path = getattr(module, "__file__", None)
    assert path is not None, f"{module!r} has no __file__"
    return Path(path).read_text(encoding="utf-8")


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(root), capture_output=True, text=True, check=False
    )


def out(root: Path, *args: str) -> str:
    return git(root, *args).stdout.strip()


def fixture_repo(tmp: Path, name: str = "repo") -> Path:
    root = tmp / name
    root.mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "user.name", "Fixture")
    (root / "README.md").write_text("seed\n")
    git(root, "add", "README.md")
    git(root, "commit", "-q", "-m", "seed")
    return root


def commit_in_lane(path: Path, filename: str, subject: str, body: str = "") -> str:
    (path / filename).write_text("work\n")
    git(path, "add", filename)
    args = ["commit", "-q", "-m", subject]
    if body:
        args.extend(["-m", body])
    git(path, *args)
    return out(path, "rev-parse", "HEAD")


# The subject of the real `zhr6mc` duplicate pair, used verbatim so the fixture is recognizably the
# measured shape rather than a generic one.
ZHR6MC_SUBJECT = (
    "feat(runner): close a backlog item when the run executes its last carrier"
)


class ResumeRoutingBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def state(self, repo: Path) -> dict:
        return {"repo": str(repo), "run_id": "run-fixture", "queue": []}

    def item_for(self, lane_handle, **extra) -> dict:
        """A durable item record shaped exactly as the drivers write one at allocation."""
        item = {
            "id6": "zhr6mc",
            "position": 1,
            "setid": "resumedupe",
            "status": "running",
            "attempts": [
                {
                    "number": 1,
                    "worktree_lane_id": lane_handle.lane_id,
                    "worktree_base": lane_handle.base_commit,
                    "worktree_branch": lane_handle.branch,
                    "worktree": str(lane_handle.path),
                }
            ],
        }
        item.update(extra)
        return item

    def resumed_shape(self, repo: Path, lane_id: str = "zhr6mc"):
        """THE REAL SHAPE, built with the REAL allocator rather than a hand-made state dict.

        Returns (prior_handle, current_handle, item). The second `allocate_worktree` is what makes
        this the genuine resume shape: allocation NEVER reuses a lane holding work, so the resumed
        turn gets a fresh attempt-scoped lane at zero commits while the work stays on the displaced
        one. A hand-built dict would assume that away and the inertness guard would prove nothing.
        """
        prior = WL.allocate_worktree(repo, lane_id)
        commit_in_lane(prior.path, "carrier.py", ZHR6MC_SUBJECT)
        commit_in_lane(prior.path, "test_carrier.py", "test: cover the carrier close")
        item = self.item_for(prior)
        current = WL.allocate_worktree(repo, lane_id)
        return prior, current, item


class TestRegressionCase(ResumeRoutingBase):
    """(a) and (a2): the measured duplication shape, and the guard against shipping it inert."""

    def test_a_prior_lane_with_real_commits_routes_verify_and_continue(self):
        repo = fixture_repo(self.tmp)
        prior, current, item = self.resumed_shape(repo)

        # The shape itself must be the resumed one, or the case below proves nothing.
        self.assertEqual(current.disposition, WL.DISPOSITION_ATTEMPT_SCOPED)
        self.assertEqual(current.displaced_from, prior.branch)
        prior_state = WL.inspect_lane(
            repo, prior.lane_id, base_commit=prior.base_commit
        )
        current_state = WL.inspect_lane(
            repo, current.lane_id, base_commit=current.base_commit
        )
        self.assertEqual(prior_state.state, WL.LANE_HOLDS_WORK)
        self.assertEqual(prior_state.commits_ahead, 2)
        self.assertEqual(current_state.state, WL.LANE_EMPTY)
        self.assertEqual(current_state.commits_ahead, 0)

        decision = OC.classify_recovery_disposition(repo, item, self.state(repo))
        self.assertEqual(decision.disposition, OC.DISPOSITION_VERIFY_AND_CONTINUE)
        self.assertEqual(decision.commits_ahead, 2)
        self.assertEqual(len(decision.real_commits), 2)
        self.assertIn(
            ZHR6MC_SUBJECT, [subject for _sha, subject in decision.real_commits]
        )

    def test_a2_the_inspected_lane_is_the_PRIOR_one_not_the_turns_own(self):
        """THE INERTNESS GUARD. A regression that reads the turn's own lane fails HERE, loudly."""
        repo = fixture_repo(self.tmp)
        prior, current, item = self.resumed_shape(repo)
        decision = OC.classify_recovery_disposition(repo, item, self.state(repo))

        self.assertNotEqual(
            decision.disposition,
            OC.DISPOSITION_FRESH_EXECUTION,
            "routing fresh-execution in the duplication shape means the feature is INERT",
        )
        self.assertEqual(decision.inspected_lane_id, prior.lane_id)
        self.assertNotEqual(decision.inspected_lane_id, current.lane_id)
        self.assertEqual(decision.inspected_branch, prior.branch)
        self.assertEqual(decision.lane_state, WL.LANE_HOLDS_WORK)

    def test_a2_sabotage_reading_the_turns_own_lane_is_caught(self):
        """The sabotage E-06 names explicitly, run as a TEST rather than promised in prose.

        Substituting a resolver that returns the CURRENT lane (what a careless refactor would do) must
        flip the decision to `fresh-execution`, which is what `test_a2_...` above fails on. This proves
        that guard is load-bearing and not merely passing.
        """
        repo = fixture_repo(self.tmp)
        _prior, current, item = self.resumed_shape(repo)

        sabotaged = dict(item)
        sabotaged["preserved_lane_id"] = current.lane_id
        sabotaged["preserved_base"] = current.base_commit
        decision = OC.classify_recovery_disposition(repo, sabotaged, self.state(repo))
        self.assertEqual(
            decision.disposition,
            OC.DISPOSITION_FRESH_EXECUTION,
            "reading the turn's OWN lane must be what produces the inert answer",
        )
        self.assertEqual(decision.commits_ahead, 0)

    def test_the_classifier_runs_no_git_write(self):
        """Non-mutation PROVEN by before/after comparison, not asserted in prose."""
        repo = fixture_repo(self.tmp)
        prior, _current, item = self.resumed_shape(repo)
        tip_before = out(repo, "rev-parse", prior.branch)
        status_before = out(prior.path, "status", "--porcelain")
        reflog_before = out(repo, "reflog", "show", prior.branch)

        OC.classify_recovery_disposition(repo, item, self.state(repo))

        self.assertEqual(out(repo, "rev-parse", prior.branch), tip_before)
        self.assertEqual(out(prior.path, "status", "--porcelain"), status_before)
        self.assertEqual(out(repo, "reflog", "show", prior.branch), reflog_before)


class TestSnapshotCompletenessSignal(ResumeRoutingBase):
    """(b) and (b2): the shipped snapshot commit is the completeness signal, matched on the SUBJECT."""

    def test_b_snapshot_only_lane_routes_fresh_execution(self):
        repo = fixture_repo(self.tmp)
        prior = WL.allocate_worktree(repo, "snaponly")
        (prior.path / "half-edited.py").write_text("mid-edit\n")
        sha = WL.snapshot_lane_dirty_work(repo, prior)
        self.assertTrue(sha, "the fixture must actually produce a snapshot commit")
        item = self.item_for(prior)

        decision = OC.classify_recovery_disposition(repo, item, self.state(repo))
        self.assertEqual(decision.disposition, OC.DISPOSITION_FRESH_EXECUTION)
        self.assertTrue(decision.snapshot_only)
        # It must be the SNAPSHOT rule doing this, not an absence of commits.
        self.assertEqual(decision.commits_ahead, 1)
        self.assertEqual(decision.real_commits, ())

    def test_b2_a_real_commit_quoting_the_phrase_in_its_BODY_still_counts_as_work(self):
        repo = fixture_repo(self.tmp)
        prior = WL.allocate_worktree(repo, "bodyquote")
        commit_in_lane(
            prior.path,
            "real.py",
            "fix(lease): document the snapshot convention",
            body=(
                "A commit whose subject starts with "
                + WL.INTERRUPTED_SNAPSHOT_SUBJECT_PREFIX
                + " is preserved mid-edit work, not finished work."
            ),
        )
        item = self.item_for(prior)

        decision = OC.classify_recovery_disposition(repo, item, self.state(repo))
        self.assertEqual(decision.disposition, OC.DISPOSITION_VERIFY_AND_CONTINUE)
        self.assertFalse(decision.snapshot_only)
        self.assertEqual(len(decision.real_commits), 1)

    def test_b2_the_phrase_leading_a_body_LINE_still_counts_as_work(self):
        """The strictest form of the subject-only rule, and the one a lax reader breaks.

        Prefix-anchoring alone is not sufficient protection if a caller feeds the classifier a whole
        MESSAGE: the phrase leading a body line would then sit at the start of what was passed. So the
        commit here puts the phrase at the START of its body's first line, which makes a
        `%B`-reading regression classify a REAL commit as a snapshot and skip finished work.
        """
        repo = fixture_repo(self.tmp)
        prior = WL.allocate_worktree(repo, "bodylead")
        commit_in_lane(
            prior.path,
            "real.py",
            ZHR6MC_SUBJECT,
            body=(
                WL.INTERRUPTED_SNAPSHOT_SUBJECT_PREFIX
                + " is the marker this commit deliberately quotes at the start of its body."
            ),
        )
        item = self.item_for(prior)

        decision = OC.classify_recovery_disposition(repo, item, self.state(repo))
        self.assertEqual(
            decision.disposition,
            OC.DISPOSITION_VERIFY_AND_CONTINUE,
            "a real commit must not be read as a snapshot because its BODY leads with the phrase",
        )
        self.assertFalse(decision.snapshot_only)

    def test_the_classifier_reads_only_the_SUBJECT_line_from_git(self):
        """Pin the mechanism, since the behavior above cannot distinguish `%s` from `%B`.

        `%s` is the subject; `%B` is the raw body. Reading `%B` and prefix-matching it is exactly the
        regression `test_b2_the_phrase_leading_a_body_LINE...` exercises, so the format is pinned here
        rather than left to be rediscovered.
        """
        import ast

        source = module_source(OC)
        node = next(
            n
            for n in ast.parse(source).body
            if isinstance(n, ast.FunctionDef) and n.name == "_lane_commit_subjects"
        )
        rendered = ast.unparse(node)
        self.assertIn("%s", rendered, "the subject format specifier must be used")
        self.assertNotIn(
            "%B", rendered, "reading the raw body would defeat the subject rule"
        )

    def test_the_marker_has_ONE_definition_and_the_writer_uses_it(self):
        """ONE spelling of the phrase, and the writer BUILDS its message from that constant.

        Asserted on the AST rather than on source text: an earlier text form checked for the substring
        `"INTERRUPTED_SNAPSHOT_SUBJECT_PREFIX + "`, which `ruff format` legitimately reflowed onto its
        own line, so the test broke on FORMATTING while the property it cared about still held. The
        property is "the writer references the constant", so that is what is checked.
        """
        import ast

        source = module_source(WL)
        literal = "WIP INTERRUPTED SNAPSHOT (not finished work):"
        self.assertEqual(
            source.count(literal),
            1,
            "the snapshot subject must be spelled exactly once, at its definition",
        )
        writer = next(
            n
            for n in ast.parse(source).body
            if isinstance(n, ast.FunctionDef) and n.name == "snapshot_lane_dirty_work"
        )
        names = {n.id for n in ast.walk(writer) if isinstance(n, ast.Name)}
        self.assertIn(
            "INTERRUPTED_SNAPSHOT_SUBJECT_PREFIX",
            names,
            "the snapshot writer must build its subject from the shared constant",
        )

    def test_the_subject_predicate_is_prefix_anchored(self):
        self.assertTrue(
            WL.commit_subject_is_interrupted_snapshot(
                WL.INTERRUPTED_SNAPSHOT_SUBJECT_PREFIX + " lane abc123"
            )
        )
        self.assertFalse(WL.commit_subject_is_interrupted_snapshot(ZHR6MC_SUBJECT))
        self.assertFalse(
            WL.commit_subject_is_interrupted_snapshot(
                "fix: mention " + WL.INTERRUPTED_SNAPSHOT_SUBJECT_PREFIX + " in docs"
            ),
            "the phrase must be anchored at the START of the subject, not found anywhere in it",
        )


class TestFreshExecutionCases(ResumeRoutingBase):
    """(c) and (d): every no-work case routes to doing the work, and never to a skip."""

    def test_c_no_recorded_prior_lane_routes_fresh_execution(self):
        repo = fixture_repo(self.tmp)
        decision = OC.classify_recovery_disposition(
            repo, {"id6": "nolane"}, self.state(repo)
        )
        self.assertEqual(decision.disposition, OC.DISPOSITION_FRESH_EXECUTION)
        self.assertIsNone(decision.inspected_lane_id)

    def test_c_an_empty_prior_lane_routes_fresh_execution(self):
        repo = fixture_repo(self.tmp)
        prior = WL.allocate_worktree(repo, "emptylane")
        decision = OC.classify_recovery_disposition(
            repo, self.item_for(prior), self.state(repo)
        )
        self.assertEqual(decision.disposition, OC.DISPOSITION_FRESH_EXECUTION)
        self.assertEqual(decision.commits_ahead, 0)

    def test_c_an_absent_prior_lane_routes_fresh_execution(self):
        repo = fixture_repo(self.tmp)
        prior = WL.allocate_worktree(repo, "goneaway")
        item = self.item_for(prior)
        WL.teardown_worktree(repo, prior)
        decision = OC.classify_recovery_disposition(repo, item, self.state(repo))
        self.assertEqual(decision.disposition, OC.DISPOSITION_FRESH_EXECUTION)
        self.assertEqual(decision.lane_state, WL.LANE_ABSENT)

    def test_d_an_unreadable_lane_is_undetermined_and_dispatched_as_fresh_execution(
        self,
    ):
        """E-03: fail TOWARD doing the work. A skip could leave a plan unimplemented."""
        repo = fixture_repo(self.tmp)
        item = {
            "id6": "unread",
            "position": 1,
            "setid": "resumedupe",
            "status": "running",
            "preserved_lane_id": "unreadable-lane",
            "preserved_base": "HEAD",
        }
        run_dir = repo / ".aw" / "records" / "runs" / "run-fixture"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        state = {"repo": str(repo), "run_id": "run-fixture", "queue": [item]}

        original = WL.inspect_lane

        def boom(*_a, **_k):
            raise OSError("git is unavailable in this fixture")

        WL.inspect_lane = boom
        try:
            decision = OC.classify_recovery_disposition(repo, item, state)
            self.assertEqual(decision.disposition, OC.DISPOSITION_UNDETERMINED)
            self.assertIn("could not be read", decision.reason)
            OC.route_recovery_turn(run_dir, state, item, True)
        finally:
            WL.inspect_lane = original

        record = item["recovery_routing"]
        self.assertEqual(record["disposition"], OC.DISPOSITION_UNDETERMINED)
        self.assertEqual(record["dispatched_as"], OC.DISPOSITION_FRESH_EXECUTION)
        self.assertTrue(record["reason"])

    def test_the_undetermined_asymmetry_is_recorded_in_a_comment(self):
        """A later reader must find the REASON, not 'fix' this into a refusal."""
        source = module_source(OC)
        marker = "FAIL-TOWARD-DOING-THE-WORK"
        self.assertIn(marker, source)
        window = source[source.index(marker) : source.index(marker) + 1200]
        self.assertIn("OPPOSITE", window)
        self.assertIn("UNIMPLEMENTED", window.upper())


class TestPromptContent(ResumeRoutingBase):
    """(e) plus E-04: the verify prompt carries the facts, and every other prompt is unchanged."""

    def _run_dir(self, repo: Path) -> Path:
        run_dir = repo / ".aw" / "records" / "runs" / "run-fixture"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        return run_dir

    def test_verify_prompt_names_the_prior_branch_and_its_actual_shas(self):
        repo = fixture_repo(self.tmp)
        prior, _current, item = self.resumed_shape(repo)
        decision = OC.classify_recovery_disposition(repo, item, self.state(repo))
        notice = OC.build_verify_and_continue_notice(repo, decision)

        self.assertIn(prior.branch, notice)
        for sha, subject in decision.real_commits:
            self.assertIn(sha, notice)
            self.assertIn(subject, notice)
        self.assertIn("DIFFERENT BRANCH THAN YOUR WORKING DIRECTORY", notice)
        self.assertIn("Do NOT implement this plan from scratch", notice)
        self.assertIn("BRING FORWARD", notice)
        # A real diffstat, not a placeholder.
        self.assertIn("files changed", notice)

    def test_verify_prompt_never_tells_the_agent_to_write_the_displaced_branch(self):
        repo = fixture_repo(self.tmp)
        _prior, _current, item = self.resumed_shape(repo)
        decision = OC.classify_recovery_disposition(repo, item, self.state(repo))
        notice = OC.build_verify_and_continue_notice(repo, decision)

        # The words appear only inside the PROHIBITION, so assert on the instruction shape: every
        # line mentioning one of them must also be a prohibition.
        for verb in ("git checkout", "merge", "cherry-pick", "rebase"):
            for line in notice.splitlines():
                if verb in line:
                    context = notice[
                        max(0, notice.index(line) - 120) : notice.index(line)
                        + len(line)
                        + 120
                    ]
                    self.assertIn(
                        "Do NOT",
                        context,
                        f"{verb!r} appears outside a prohibition: {line!r}",
                    )

    def test_no_acknowledgement_gate_or_refusal_path_was_added(self):
        """The shipped constraint: a refusal is one more way for an unattended run to stall."""
        import ast

        source = module_source(OC)
        for name in ("build_verify_and_continue_notice", "route_recovery_turn"):
            node = next(
                n
                for n in ast.parse(source).body
                if isinstance(n, ast.FunctionDef) and n.name == name
            )
            body = "\n".join(
                ast.unparse(stmt)
                for stmt in node.body
                if not (
                    isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
                )
            )
            for banned in ("input(", "acknowledgement required"):
                self.assertNotIn(banned, body, f"{name} must not gate the run")

    def test_e_a_first_attempt_prompt_is_unchanged(self):
        repo = fixture_repo(self.tmp)
        _prior, _current, item = self.resumed_shape(repo)
        run_dir = self._run_dir(repo)
        plan = repo / "plan.ipd.md"
        plan.write_text("# plan\n")
        state = self.state(repo)

        for module in (OC, AGY):
            with self.subTest(driver=module.__name__):
                # A first attempt passes recovery=False and no routing, exactly as the drivers do.
                without = module.build_prompt(item, state, run_dir, plan, False)
                decision = OC.classify_recovery_disposition(repo, item, state)
                with_routing = module.build_prompt(
                    item, state, run_dir, plan, False, routing=decision
                )
                self.assertEqual(
                    without,
                    with_routing,
                    "a NORMAL EXECUTION prompt must not gain the verify block",
                )
                self.assertIn("Mode: NORMAL EXECUTION", without)
                self.assertNotIn("ALREADY COMMITTED WORK", without)

    def test_e_a_fresh_execution_recovery_prompt_is_byte_identical_to_no_routing(self):
        """Only `verify-and-continue` changes a prompt; `fresh-execution` must not."""
        repo = fixture_repo(self.tmp)
        prior = WL.allocate_worktree(repo, "emptyprior")
        item = self.item_for(prior)
        run_dir = self._run_dir(repo)
        plan = repo / "plan.ipd.md"
        plan.write_text("# plan\n")
        state = self.state(repo)
        decision = OC.classify_recovery_disposition(repo, item, state)
        self.assertEqual(decision.disposition, OC.DISPOSITION_FRESH_EXECUTION)

        for module in (OC, AGY):
            with self.subTest(driver=module.__name__):
                baseline = module.build_prompt(item, state, run_dir, plan, True)
                routed = module.build_prompt(
                    item, state, run_dir, plan, True, routing=decision
                )
                self.assertEqual(baseline, routed)
                self.assertIn("Mode: RECOVERY/CONTINUATION", baseline)
                self.assertNotIn("ALREADY COMMITTED WORK", baseline)

    def test_a_verify_and_continue_recovery_prompt_gains_the_block(self):
        repo = fixture_repo(self.tmp)
        prior, _current, item = self.resumed_shape(repo)
        run_dir = self._run_dir(repo)
        plan = repo / "plan.ipd.md"
        plan.write_text("# plan\n")
        state = self.state(repo)
        decision = OC.classify_recovery_disposition(repo, item, state)

        for module in (OC, AGY):
            with self.subTest(driver=module.__name__):
                prompt = module.build_prompt(
                    item, state, run_dir, plan, True, routing=decision
                )
                self.assertIn("ALREADY COMMITTED WORK", prompt)
                self.assertIn(prior.branch, prompt)
                # The EXISTING recovery notice is kept, not replaced.
                self.assertIn("continuing an INTERRUPTED attempt", prompt)


class TestDurableRecording(ResumeRoutingBase):
    """E-05: the decision and its inputs are readable after the fact, from state alone."""

    def test_the_routing_decision_and_its_inputs_are_recorded(self):
        repo = fixture_repo(self.tmp)
        prior, _current, item = self.resumed_shape(repo)
        run_dir = repo / ".aw" / "records" / "runs" / "run-fixture"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        state = {"repo": str(repo), "run_id": "run-fixture", "queue": [item]}

        OC.route_recovery_turn(run_dir, state, item, True)
        record = item["recovery_routing"]
        self.assertEqual(record["disposition"], OC.DISPOSITION_VERIFY_AND_CONTINUE)
        self.assertEqual(record["dispatched_as"], OC.DISPOSITION_VERIFY_AND_CONTINUE)
        # The INSPECTED LANE ID is the field that tells a reader which lane decided it.
        self.assertEqual(record["inspected_lane_id"], prior.lane_id)
        self.assertEqual(record["inspected_branch"], prior.branch)
        self.assertEqual(record["commits_ahead"], 2)
        self.assertFalse(record["snapshot_only"])
        self.assertEqual(len(record["real_commits"]), 2)
        self.assertTrue(record["reason"])

        events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
        self.assertIn("recovery-routed", events)
        self.assertIn(prior.lane_id, events)

    def test_a_reexecuted_run_is_distinguishable_from_a_verify_run_in_state_alone(self):
        repo = fixture_repo(self.tmp)
        run_dir = repo / ".aw" / "records" / "runs" / "run-fixture"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)

        _prior, _current, verify_item = self.resumed_shape(repo)
        empty = WL.allocate_worktree(repo, "otheritem")
        fresh_item = self.item_for(empty)
        fresh_item["id6"] = "otherid"
        state = {
            "repo": str(repo),
            "run_id": "run-fixture",
            "queue": [verify_item, fresh_item],
        }

        OC.route_recovery_turn(run_dir, state, verify_item, True)
        OC.route_recovery_turn(run_dir, state, fresh_item, True)
        self.assertEqual(
            verify_item["recovery_routing"]["dispatched_as"],
            OC.DISPOSITION_VERIFY_AND_CONTINUE,
        )
        self.assertEqual(
            fresh_item["recovery_routing"]["dispatched_as"],
            OC.DISPOSITION_FRESH_EXECUTION,
        )

    def test_a_first_attempt_records_no_routing(self):
        repo = fixture_repo(self.tmp)
        _prior, _current, item = self.resumed_shape(repo)
        run_dir = repo / ".aw" / "records" / "runs" / "run-fixture"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        state = {"repo": str(repo), "run_id": "run-fixture", "queue": [item]}

        self.assertIsNone(OC.route_recovery_turn(run_dir, state, item, False))
        self.assertNotIn("recovery_routing", item)


class TestDriverSymmetry(ResumeRoutingBase):
    """(f): a one-driver fix would leave the other driver duplicating a full turn's work."""

    def test_both_drivers_expose_the_routing_surface(self):
        for name in (
            "classify_recovery_disposition",
            "resolve_prior_lane",
            "build_verify_and_continue_notice",
            "route_recovery_turn",
        ):
            for module in (OC, AGY):
                with self.subTest(symbol=name, driver=module.__name__):
                    self.assertTrue(
                        callable(getattr(module, name, None)),
                        f"{module.__name__} is missing {name}",
                    )

    def test_the_antigravity_twin_DELEGATES_rather_than_copying(self):
        """Delegation, so a fix to one cannot leave the other behind (the `rununify` lesson)."""
        import ast

        source = module_source(AGY)
        tree = ast.parse(source)
        for name in (
            "classify_recovery_disposition",
            "resolve_prior_lane",
            "build_verify_and_continue_notice",
            "route_recovery_turn",
        ):
            node = next(
                n
                for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == name
            )
            body = [
                stmt
                for stmt in node.body
                if not (
                    isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
                )
            ]
            rendered = "\n".join(ast.unparse(stmt) for stmt in body)
            with self.subTest(symbol=name):
                self.assertIn("from agent_workflows.oc_runipd import", rendered)
                self.assertIn("_shared(", rendered)
                # A delegating wrapper is an import plus a return; more than that is a re-fork.
                self.assertLessEqual(len(body), 2, f"{name} grew logic: {rendered}")

    def test_both_drivers_agree_across_the_whole_matrix(self):
        repo = fixture_repo(self.tmp)
        state = self.state(repo)

        _prior, _current, verify_item = self.resumed_shape(repo)
        empty = WL.allocate_worktree(repo, "emptycase")
        snap = WL.allocate_worktree(repo, "snapcase")
        (snap.path / "loose.py").write_text("mid\n")
        WL.snapshot_lane_dirty_work(repo, snap)

        cases = {
            "verify": (verify_item, OC.DISPOSITION_VERIFY_AND_CONTINUE),
            "empty": (self.item_for(empty), OC.DISPOSITION_FRESH_EXECUTION),
            "snapshot": (self.item_for(snap), OC.DISPOSITION_FRESH_EXECUTION),
            "none": ({"id6": "nolane"}, OC.DISPOSITION_FRESH_EXECUTION),
        }
        for label, (item, expected) in cases.items():
            with self.subTest(case=label):
                oc = OC.classify_recovery_disposition(repo, item, state)
                agy = AGY.classify_recovery_disposition(repo, item, state)
                self.assertEqual(oc.disposition, expected)
                self.assertEqual(oc, agy)

    def test_both_drivers_record_the_displaced_lane_at_allocation(self):
        """`resolve_prior_lane`'s last fallback needs this in DURABLE state, not only in an event."""
        for module in (OC, AGY):
            source = module_source(module)
            self.assertIn('attempt["worktree_displaced_from"]', source, module.__name__)

    def test_both_drivers_route_before_allocating_their_own_lane(self):
        """ORDERING IS LOAD-BEARING: classifying after allocation reads an always-empty lane."""
        source_by_module = {
            OC: "route_recovery_turn(run_dir, state, item, recovery)",
            AGY: "route_recovery_turn(run_dir, state, item, recovery)",
        }
        for module, call in source_by_module.items():
            source = module_source(module)
            with self.subTest(driver=module.__name__):
                self.assertIn(call, source)
                routing_at = source.index(call)
                alloc_at = source.index("allocate_isolation_worktree(repo,")
                self.assertLess(
                    routing_at,
                    alloc_at,
                    "routing must be classified BEFORE this turn's lane is allocated",
                )


class TestBranchNameInversion(ResumeRoutingBase):
    """The measured hazard in `displaced_from`: it is a BRANCH name, not a lane id."""

    def test_a_recorded_branch_name_resolves_to_the_lane_that_actually_exists(self):
        repo = fixture_repo(self.tmp)
        prior = WL.allocate_worktree(repo, "invert")
        commit_in_lane(prior.path, "w.py", ZHR6MC_SUBJECT)
        current = WL.allocate_worktree(repo, "invert")
        self.assertEqual(current.displaced_from, prior.branch)

        # Feeding the BRANCH name to inspect_lane as a lane id is the trap: it re-sanitizes into a
        # name that does not exist and classifies ABSENT, hiding the work entirely.
        displaced = current.displaced_from
        assert displaced is not None  # narrowed: asserted equal to prior.branch above
        naive = WL.inspect_lane(repo, displaced)
        self.assertEqual(naive.state, WL.LANE_ABSENT)

        lane_id = WL.lane_id_from_branch(displaced)
        assert lane_id is not None
        correct = WL.inspect_lane(repo, lane_id, base_commit=prior.base_commit)
        self.assertEqual(correct.state, WL.LANE_HOLDS_WORK)
        self.assertEqual(correct.branch, prior.branch)

    def test_the_displaced_from_fallback_finds_the_work(self):
        """An attempt that died before the preservation path still resolves its prior lane."""
        repo = fixture_repo(self.tmp)
        prior = WL.allocate_worktree(repo, "fallback")
        commit_in_lane(prior.path, "w.py", ZHR6MC_SUBJECT)
        current = WL.allocate_worktree(repo, "fallback")

        # Only `worktree_displaced_from` is recorded: no preserved_* fields, no worktree_lane_id.
        item = {
            "id6": "fallbk",
            "attempts": [
                {
                    "number": 1,
                    "worktree_displaced_from": current.displaced_from,
                    "worktree_base": prior.base_commit,
                }
            ],
        }
        _lane_id, _base, branch = OC.resolve_prior_lane(item)
        self.assertEqual(branch, prior.branch)
        decision = OC.classify_recovery_disposition(repo, item, self.state(repo))
        self.assertEqual(decision.disposition, OC.DISPOSITION_VERIFY_AND_CONTINUE)
        self.assertEqual(decision.inspected_branch, prior.branch)

    def test_a_non_lane_branch_name_is_rejected_rather_than_mangled(self):
        self.assertIsNone(WL.lane_id_from_branch("main"))
        self.assertIsNone(WL.lane_id_from_branch(""))
        self.assertIsNone(WL.lane_id_from_branch("aw/lane/"))
        self.assertEqual(WL.lane_id_from_branch("aw/lane/abc123"), "abc123")

    def test_the_inversion_round_trips_for_an_attempt_scoped_lane(self):
        branch = WL.lane_branch_name("abc123:attempt2")
        self.assertEqual(branch, "aw/lane/abc123_attempt2")
        lane_id = WL.lane_id_from_branch(branch)
        assert lane_id is not None
        self.assertEqual(WL.lane_branch_name(lane_id), branch)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
