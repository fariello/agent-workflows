"""The standalone `audit` verb: one independent opinion on an ALREADY-EXECUTED plan.

reverify-01 (`mp289j`), graduated from backlog `7u9kbm`.

WHAT THIS FILE IS DEFENDING, because every class below exists for one measured hazard rather than for
coverage:

  * THE ONE-COMPOSER RULE. Backlog `7u9kbm` forbids a second verifier ("It must NOT be a second
    implementation ... or the two verifiers will drift and neither can be trusted"), which is the same
    argument `wlxkoz` makes against a second completion checker. So the audit prompt must come from THE
    SAME `build_verifier_prompt`, and `TheAuditReusesTheOneVerifierComposer` asserts that by identity
    and by shared content rather than by reading the source.

  * THE IN-RUN TURN MUST NOT MOVE. Plan `mp289j`'s Deferred section permits parameterizing the shared
    composer only on the condition that the in-run verifier's effective prompt is byte-identical before
    and after. `TheInRunPromptIsUnchanged` pins that as an exact-equality property of the DEFAULT call.

  * THE FINISHED PLAN IS IMMUTABLE. OQ-05's maintainer resolution authorizes fixing CODE and refuses
    any edit to the plan DOCUMENT. `TheAuditCannotTouchTheFinishedPlan` asserts the prohibition reaches
    the agent (it is in the prompt) and that the resolver refuses a non-executed subject outright.

  * THE BASE IS USUALLY GONE, AND THAT IS NOT AN ERROR. Measured 2026-09-20: 17 of 561 executed plans
    still have a begin receipt carrying `base_head`, because a clean finalize consumes it. `TheDiffBasis`
    asserts all three reachable bases and that `none` is a first-class answer.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import agy_runipd, oc_runipd, runner_shared

REPO_ROOT = Path(__file__).resolve().parents[1]


def _item(id6: str = "abc123") -> dict:
    return {"position": 1, "id6": id6, "setid": "demo", "attempts": []}


def _state() -> dict:
    return {"run_id": "run-20260101T000000Z-1", "repo": "."}


class TheAuditReusesTheOneVerifierComposer(unittest.TestCase):
    """Backlog `7u9kbm`'s hard constraint, asserted as a property rather than by reading source."""

    def test_both_hosts_delegate_to_the_single_shared_composer(self):
        """A host-local prompt body would be the drift `rununify` exists to remove."""

        for mod in (oc_runipd, agy_runipd):
            with self.subTest(host=mod.__name__):
                self.assertIs(
                    mod.runner_shared.build_verifier_prompt,
                    runner_shared.build_verifier_prompt,
                    f"{mod.__name__} no longer reaches the ONE shared composer",
                )

    def test_the_audit_prompt_comes_from_the_same_function_as_the_in_run_prompt(self):
        """The identity claim, made by MONKEYPATCHING the shared composer and seeing the audit change.

        This is stronger than asserting the two prompts look alike: it proves the audit has no private
        fallback path, because replacing the one composer replaces the audit's output too.
        """

        original = runner_shared.build_verifier_prompt
        calls: list[dict] = []

        def spy(item, state, run_dir, plan_path, *, labels, audit=False, diff_basis=""):
            calls.append({"audit": audit, "diff_basis": diff_basis})
            return "SENTINEL"

        runner_shared.build_verifier_prompt = spy  # type: ignore[assignment]
        try:
            got = oc_runipd.build_verifier_prompt(
                _item(),
                _state(),
                Path("/tmp/run"),
                Path("/tmp/plan.ipd.md"),
                audit=True,
                diff_basis="a basis",
            )
        finally:
            runner_shared.build_verifier_prompt = original  # type: ignore[assignment]

        self.assertEqual(got, "SENTINEL")
        self.assertEqual(calls, [{"audit": True, "diff_basis": "a basis"}])

    def test_the_audit_prompt_keeps_the_reused_requirements_verbatim(self):
        """Requirements 2, 3 and 4 are REUSED, not paraphrased, so the two verifiers judge alike.

        Requirement 4 is the load-bearing one: OQ-05 authorized fixing code, so its fix-and-commit
        sentence (including "Never push") must survive into the audit rendering unchanged. A paraphrase
        here would be a second verifier wearing the first one's name.
        """

        in_run = runner_shared.build_verifier_prompt(
            _item(),
            _state(),
            Path("/tmp/run"),
            Path("/tmp/plan.ipd.md"),
            labels=runner_shared.OC_HOST_LABELS,
        )
        audit = runner_shared.build_verifier_prompt(
            _item(),
            _state(),
            Path("/tmp/run"),
            Path("/tmp/plan.ipd.md"),
            labels=runner_shared.OC_HOST_LABELS,
            audit=True,
        )
        for shared_clause in (
            "2. **Evidence Table (E-* and V-*)**:",
            "- Check every Execution item (`E-*`) and every Validation item (`V-*`) in the IPD.",
            "3. **Run and Verify Test Suite**:",
            "- Paste the actual runner output with exit code.",
            "4. **In-Scope Fixes**:",
            # commitguard `y9vpvv` E-09: the clause now names the TOOLED commit path in both its
            # forms rather than raw `git commit`, per the 2026-09-10 OQ-03 ruling. The parity claim
            # is unchanged: whatever the clause says, BOTH renderings must say it identically, and
            # "Never push" must survive.
            "fix them, re-run validation, and commit through `aw commit <plan> -- <paths>` "
            "(or `aw commit --no-plan -m <msg> -- <paths>` when no plan governs the change), "
            "limited to the paths you name. Never push.",
            '"verdict": "VERIFIED|CORRECTION_REQUIRED|BLOCKED",',
        ):
            with self.subTest(clause=shared_clause[:48]):
                self.assertIn(shared_clause, in_run)
                self.assertIn(
                    shared_clause,
                    audit,
                    "the audit rendering dropped or paraphrased a REUSED clause, which makes it a "
                    "second verifier in substance",
                )

    def test_no_second_composer_exists_in_the_package(self):
        """NEGATIVE proof: exactly ONE `def build_verifier_prompt` body in `agent_workflows/`.

        The two host functions are four-line DELEGATIONS, so they are counted and named here rather
        than being treated as bodies; what must not appear is a third definition, or any other function
        that composes verifier prompt prose of its own.
        """

        definitions: dict[str, list[str]] = {}
        for path in sorted((REPO_ROOT / "agent_workflows").glob("*.py")):
            text = path.read_text(encoding="utf-8")
            for name in re.findall(r"^def (\w*verifier_prompt\w*)\(", text, re.M):
                definitions.setdefault(str(path.relative_to(REPO_ROOT)), []).append(
                    name
                )
        self.assertEqual(
            definitions,
            {
                "agent_workflows/agy_runipd.py": ["build_verifier_prompt"],
                "agent_workflows/oc_runipd.py": ["build_verifier_prompt"],
                "agent_workflows/runner_shared.py": ["build_verifier_prompt"],
            },
            "a verifier-prompt composer appeared somewhere new. The two host entries must stay "
            "DELEGATIONS to the shared one; a third body is the drift backlog `7u9kbm` forbids",
        )

    def test_the_audit_writes_the_existing_outcome_schema(self):
        """The verdict schema is the EXISTING one, extended by two keys rather than replaced.

        `7u9kbm` requires reusing "the existing outcome schema". The two additions are recorded here so
        the extension is deliberate and visible: `diff_basis` (E-02, because a verdict computed with no
        baseline means something narrower) and `findings_filed` (E-03/OQ-01, because a finding must reach
        a tracked carrier).
        """

        audit = runner_shared.build_verifier_prompt(
            _item(),
            _state(),
            Path("/tmp/run"),
            Path("/tmp/plan.ipd.md"),
            labels=runner_shared.OC_HOST_LABELS,
            audit=True,
        )
        for key in (
            '"schema_version": 1',
            '"id6"',
            '"verdict"',
            '"summary"',
            '"evidence"',
            '"tests_run"',
            '"corrections_made"',
            '"diff_basis"',
            '"findings_filed"',
        ):
            with self.subTest(key=key):
                self.assertIn(key, audit)


class TheInRunPromptIsUnchanged(unittest.TestCase):
    """The condition plan `mp289j` attaches to touching the shared composer at all."""

    def test_the_default_call_is_byte_identical_to_an_explicit_non_audit_call(self):
        args = (_item(), _state(), Path("/tmp/run"), Path("/tmp/plan.ipd.md"))
        for labels in (runner_shared.OC_HOST_LABELS, runner_shared.AGY_HOST_LABELS):
            with self.subTest(labels=labels.product):
                self.assertEqual(
                    runner_shared.build_verifier_prompt(*args, labels=labels),
                    runner_shared.build_verifier_prompt(
                        *args, labels=labels, audit=False, diff_basis="ignored"
                    ),
                    "`diff_basis` leaked into the in-run rendering, or `audit=False` is not the "
                    "shipped default. The in-run turn's prompt must be byte-identical",
                )

    def test_the_in_run_prompt_still_names_the_working_tree_and_the_execution_outcome(
        self,
    ):
        """The two things the AUDIT rendering removes must still be present in the IN-RUN one.

        Without this, a later edit could "simplify" by making both renderings the audit one, silently
        removing the diff instruction from the turn that legitimately has a working tree to inspect.
        """

        in_run = runner_shared.build_verifier_prompt(
            _item(),
            _state(),
            Path("/tmp/run"),
            Path("/tmp/plan.ipd.md"),
            labels=runner_shared.OC_HOST_LABELS,
        )
        self.assertIn("working tree diffs produced for this IPD", in_run)
        self.assertIn("Execution Outcome JSON:", in_run)
        self.assertNotIn("HARD PROHIBITION", in_run)


class TheAuditCannotTouchTheFinishedPlan(unittest.TestCase):
    """OQ-05: fixing code is authorized; editing the finished plan document never is."""

    @classmethod
    def setUpClass(cls):
        cls._temp_dir = TemporaryDirectory()
        cls.repo = Path(cls._temp_dir.name)
        pending_dir = cls.repo / ".aw" / "records" / "plans" / "pending"
        pending_dir.mkdir(parents=True)
        plan = pending_dir / "20260101-demo-01-pen001-pending-plan.ipd.md"
        plan.write_text(
            "- Id: pen001\n- Set: demo\n- Order: 1\n- Status: to-review\n",
            encoding="utf-8",
        )

    @classmethod
    def tearDownClass(cls):
        cls._temp_dir.cleanup()

    def test_the_prohibition_reaches_the_agent(self):
        audit = runner_shared.build_verifier_prompt(
            _item(),
            _state(),
            Path("/tmp/run"),
            Path("/tmp/plan.ipd.md"),
            labels=runner_shared.OC_HOST_LABELS,
            audit=True,
        )
        for clause in (
            "Do NOT edit, re-status, move, or add any commit to the plan file itself",
            "Do NOT append to its `## Workflow history`",
            "immutable by repository policy",
            "closed by a NEW corrective IPD",
            "`aw backlog new`",
        ):
            with self.subTest(clause=clause[:44]):
                self.assertIn(clause, audit)

    def test_a_plan_that_has_not_executed_is_refused_rather_than_audited(self):
        """The subject must be TERMINAL, checked as a directory question via `plan_bucket`.

        Auditing a pending plan is refused because the verb's entire contract is "this is finished and
        immutable": a pending plan already has `/plan-review` and a run.
        """

        target = runner_shared.plan_audit_target(self.repo, "pen001")
        self.assertEqual(target.refusal, runner_shared.AUDIT_PLAN_NOT_EXECUTED)
        self.assertIn("not executed/", target.reason)

    def test_an_unknown_id6_is_refused_with_its_own_code(self):
        target = runner_shared.plan_audit_target(self.repo, "zzzzzz")
        self.assertEqual(target.refusal, runner_shared.AUDIT_PLAN_NOT_FOUND)

    def test_refusals_are_returned_and_never_raised(self):
        """An out-of-band verb must exit nonzero with a sentence, not a traceback."""

        for id6 in ("zzzzzz", "pen001"):
            with self.subTest(id6=id6):
                target = runner_shared.plan_audit_target(self.repo, id6)
                self.assertTrue(target.refusal)
                self.assertTrue(target.reason.strip())


class TheDiffBasis(unittest.TestCase):
    """E-02: choose among bases that actually EXIST, and say what the verdict means."""

    def test_an_operator_supplied_base_wins_and_is_labelled_as_theirs(self):
        target = runner_shared.plan_audit_target(REPO_ROOT, "nna8yz", base="HEAD~5")
        self.assertEqual(target.basis, runner_shared.AUDIT_BASIS_OPERATOR)
        self.assertIn("HEAD~5", target.basis_detail)
        self.assertIn("operator's", target.basis_detail)

    def test_a_receipt_absent_plan_is_still_auditable_with_basis_none(self):
        """`none` IS A FIRST-CLASS ANSWER. The maintainer withdrew the stored-baseline premise (OQ-01).

        `nna8yz` is this plan's own motivating example and measured receipt-ABSENT, so if `none` were
        treated as an error the verb would refuse the exact case it was built for.
        """

        target = runner_shared.plan_audit_target(REPO_ROOT, "nna8yz")
        self.assertEqual(target.refusal, "")
        self.assertEqual(target.basis, runner_shared.AUDIT_BASIS_NONE)
        self.assertEqual(target.basis_detail, "")

    def test_the_prompt_states_the_basis_including_when_there_is_none(self):
        """A verdict computed with no baseline means something narrower, so the auditor is TOLD."""

        no_basis = runner_shared.build_verifier_prompt(
            _item(),
            _state(),
            Path("/tmp/run"),
            Path("/tmp/plan.ipd.md"),
            labels=runner_shared.OC_HOST_LABELS,
            audit=True,
        )
        self.assertIn("Diff basis available to you: NONE", no_basis)
        self.assertIn("no historical baseline to diff", no_basis)

        with_basis = runner_shared.build_verifier_prompt(
            _item(),
            _state(),
            Path("/tmp/run"),
            Path("/tmp/plan.ipd.md"),
            labels=runner_shared.OC_HOST_LABELS,
            audit=True,
            diff_basis="the plan's OWN surviving begin receipt, base_head `deadbeef`",
        )
        self.assertIn("base_head `deadbeef`", with_basis)
        self.assertNotIn("Diff basis available to you: NONE", with_basis)

    def test_the_audit_prompt_does_not_promise_an_execution_outcome_file(self):
        """For a historical plan there is no execution outcome JSON, so naming one invites a false defect."""

        audit = runner_shared.build_verifier_prompt(
            _item(),
            _state(),
            Path("/tmp/run"),
            Path("/tmp/plan.ipd.md"),
            labels=runner_shared.OC_HOST_LABELS,
            audit=True,
        )
        self.assertNotIn("Execution Outcome JSON:", audit)
        self.assertIn("Audit Outcome JSON to write:", audit)

    def test_a_surviving_receipt_is_used_when_one_exists(self):
        """The RARE case, asserted on a synthetic repo so it does not depend on which plans still have one."""

        with TemporaryDirectory() as temp:
            repo = Path(temp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            plans = repo / ".aw" / "records" / "plans" / "executed"
            plans.mkdir(parents=True)
            plan = plans / "20260101-demo-01-aaa111-a-demo-plan.ipd.md"
            plan.write_text(
                "# IPD: a demo plan\n\n- Id: aaa111\n- Set: demo\n- Order: 1\n"
                "- Status: executed\n",
                encoding="utf-8",
            )
            from agent_workflows import ipd_lifecycle

            receipt_path = ipd_lifecycle.receipt_path_for(repo, "aaa111")
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "kind": "ipd_begin_receipt",
                        "plan_id": "aaa111",
                        "base_head": "0123456789abcdef0123456789abcdef01234567",
                    }
                ),
                encoding="utf-8",
            )
            target = runner_shared.plan_audit_target(repo, "aaa111")
            self.assertEqual(target.refusal, "")
            self.assertEqual(target.basis, runner_shared.AUDIT_BASIS_RECEIPT)
            self.assertIn("0123456789abcdef", target.basis_detail)
            # The BIAS is stated, because a receipt survives precisely when finalize did not cleanly
            # complete, so the operator must not read a surviving base as a sign of health.
            self.assertIn("did NOT cleanly complete", target.basis_detail)


class TheVerdictDestination(unittest.TestCase):
    """E-03: gitignored per-invocation run directory, APPEND by construction, findings tracked."""

    def test_the_runs_root_is_gitignored_so_a_verdict_is_not_permanent_history(self):
        runs = runner_shared.state_root(REPO_ROOT)
        # ASKED AS A PATH INSIDE THE DIRECTORY, not as the directory name. `.aw/.gitignore:14` is the
        # DIRECTORY-ANCHORED pattern `records/runs/`, and `git check-ignore` returns 1 for the bare
        # `.aw/records/runs` while returning 0 for `.aw/records/runs/` and for anything beneath it
        # (measured 2026-09-20). A verdict is a FILE under that directory, so the question this test
        # must ask is whether a verdict path is ignored, and asking about the bare directory name would
        # make the test fail while the property it checks holds.
        rel = (
            runs / "run-example" / "outcomes" / "01-abc123-verification.json"
        ).relative_to(REPO_ROOT)
        result = subprocess.run(
            ["git", "check-ignore", "-v", str(rel)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"{rel} is NOT gitignored; E-03's tracked-versus-gitignored trade was decided on the "
            f"premise that it is, and a tracked machine verdict is a different decision",
        )

    def test_two_invocations_cannot_collide_so_a_second_opinion_cannot_erase_the_first(
        self,
    ):
        """APPEND-versus-OVERWRITE, answered structurally: each invocation mints its OWN directory.

        Nothing PREVENTS an operator re-running the audit, and nothing can, since the verb is invoked
        on demand. The achievable property is narrower and is what this asserts: a second run does not
        hide the first.

        ASSERTED ON THE DIRECTORY MINTER, NOT ON `new_run_id`, and the difference is a real defect this
        test found. `new_run_id` is `run-<UTC seconds>-<pid>`, so two invocations inside ONE second from
        ONE shell return the SAME id (measured: a set of two calls had length 1). Relying on it would
        have made E-03's whole append answer false for the most likely re-run pattern there is, namely
        an operator running the audit twice in quick succession.
        """

        with TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / ".aw" / "records" / "runs").mkdir(parents=True)
            first_id, first = oc_runipd._fresh_audit_run_dir(repo)
            second_id, second = oc_runipd._fresh_audit_run_dir(repo)
            self.assertNotEqual(
                first,
                second,
                "two audit invocations shared a run directory, so the second verdict would "
                "overwrite the first",
            )
            self.assertNotEqual(first_id, second_id)
            self.assertTrue(first.is_dir() and second.is_dir())

    def test_the_prompt_requires_a_tracked_carrier_for_every_finding(self):
        """OQ-01: report-only was declined. The gitignored verdict is acceptable ONLY because of this."""

        audit = runner_shared.build_verifier_prompt(
            _item(),
            _state(),
            Path("/tmp/run"),
            Path("/tmp/plan.ipd.md"),
            labels=runner_shared.OC_HOST_LABELS,
            audit=True,
        )
        self.assertIn("file a backlog item with `aw backlog new`", audit)
        self.assertIn("Reporting it only in your verdict is NOT", audit)
        self.assertIn("reporting outranks filing", audit)


class TheVerbRunsEndToEnd(unittest.TestCase):
    """The whole path with a FAKE host binary, because the unit assertions above cannot see wiring.

    THIS CLASS EARNED ITS PLACE: writing it found two real defects that every prompt-level assertion
    above passed straight through. (1) `run_opencode` opens the attempt log with `log_path.open("w")`
    and does not create `sessions/`, so the verb raised FileNotFoundError at the moment of launch,
    AFTER writing the prompt and allocating a lane. (2) `new_run_id` is second-granular, so two audits
    in one second shared a directory and the second verdict overwrote the first, falsifying E-03's
    append answer.

    The fake host reads the verdict path OUT OF THE PROMPT, which incidentally proves the prompt really
    names a writable path rather than merely containing plausible prose.
    """

    FAKE_HOST = """#!/usr/bin/env python3
import json, re, sys, pathlib
prompt = sys.argv[-1]
m = re.search(r"Audit Outcome JSON to write: `([^`]+)`", prompt)
assert m, "the audit prompt did not name a verdict path"
p = pathlib.Path(m.group(1))
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps({
    "schema_version": 1, "id6": "aaa111", "verdict": "CORRECTION_REQUIRED",
    "summary": "an E-item claims a test that does not exist",
    "evidence": [], "tests_run": [], "corrections_made": [],
    "diff_basis": "none", "findings_filed": ["bk1234"],
}))
print(json.dumps({"type": "message", "sessionID": "ses_fake"}))
sys.exit(0)
"""

    PLAN_TEXT = (
        "# IPD: a demo\n\n- Id: aaa111\n- Set: demo\n- Order: 1\n- Status: executed\n"
    )

    def _fixture(self, root: Path) -> tuple[Path, Path, Path]:
        repo = root / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        plans = repo / ".aw" / "records" / "plans" / "executed"
        plans.mkdir(parents=True)
        plan = plans / "20260101-demo-01-aaa111-a-demo.ipd.md"
        plan.write_text(self.PLAN_TEXT, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.email=t@t",
                "-c",
                "user.name=t",
                "commit",
                "-qm",
                "init",
            ],
            cwd=repo,
            check=True,
        )
        host = root / "fakehost"
        host.write_text(self.FAKE_HOST, encoding="utf-8")
        host.chmod(0o755)
        return repo, plan, host

    @staticmethod
    def _run_dirs(repo: Path) -> list[Path]:
        root = repo / ".aw" / "records" / "runs"
        return sorted(d for d in root.iterdir() if d.name.startswith("run-"))

    def test_an_audit_records_a_verdict_and_leaves_the_plan_byte_identical(self):
        with TemporaryDirectory() as temp:
            repo, plan, host = self._fixture(Path(temp))
            rc = oc_runipd.handle_audit_command(
                argparse.Namespace(
                    repo=str(repo),
                    id6="aaa111",
                    base=None,
                    isolate_worktree=False,
                    opencode=str(host),
                )
            )
            self.assertEqual(rc, 0)

            runs = self._run_dirs(repo)
            self.assertEqual(len(runs), 1)
            state = json.loads((runs[0] / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["kind"], "audit")
            self.assertEqual(state["queue"][0]["action"], "audit")
            self.assertEqual(state["queue"][0]["status"], "audited")
            self.assertEqual(
                state["audit"]["verdict"]["verdict"], "CORRECTION_REQUIRED"
            )
            self.assertEqual(state["audit"]["verdict"]["findings_filed"], ["bk1234"])

            # THE IMMUTABILITY CLAIM, asserted rather than assumed (V-05 requires exactly this).
            self.assertEqual(plan.read_text(encoding="utf-8"), self.PLAN_TEXT)
            tracked_dirt = [
                line
                for line in subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                ).stdout.splitlines()
                if ".aw/records/runs" not in line
            ]
            self.assertEqual(
                tracked_dirt,
                [],
                "the audit changed tracked files in the checkout; only its own gitignored run "
                "directory may appear",
            )

    def test_two_audits_in_the_same_second_do_not_overwrite_each_other(self):
        with TemporaryDirectory() as temp:
            repo, _plan, host = self._fixture(Path(temp))
            args = argparse.Namespace(
                repo=str(repo),
                id6="aaa111",
                base=None,
                isolate_worktree=False,
                opencode=str(host),
            )
            self.assertEqual(oc_runipd.handle_audit_command(args), 0)
            self.assertEqual(oc_runipd.handle_audit_command(args), 0)
            self.assertEqual(
                len(self._run_dirs(repo)),
                2,
                "the second audit reused the first's run directory, so its verdict overwrote one an "
                "operator may still need",
            )

    def test_a_turn_that_writes_no_verdict_exits_nonzero_rather_than_claiming_success(
        self,
    ):
        """A silent host must not read as VERIFIED. The absence of an opinion is not an opinion."""

        with TemporaryDirectory() as temp:
            repo, _plan, _host = self._fixture(Path(temp))
            silent = Path(temp) / "silenthost"
            silent.write_text(
                "#!/usr/bin/env python3\nimport sys\nsys.exit(0)\n", encoding="utf-8"
            )
            silent.chmod(0o755)
            rc = oc_runipd.handle_audit_command(
                argparse.Namespace(
                    repo=str(repo),
                    id6="aaa111",
                    base=None,
                    isolate_worktree=False,
                    opencode=str(silent),
                )
            )
            self.assertEqual(rc, 1)
            state = json.loads(
                (self._run_dirs(repo)[0] / "state.json").read_text(encoding="utf-8")
            )
            self.assertEqual(state["queue"][0]["status"], "no-verdict")


class TheVerbSurface(unittest.TestCase):
    """E-05 / D5: the noun, the shim membership, and the declared-both-implemented-one split."""

    @staticmethod
    def _subparsers(mod) -> dict:
        parser = mod.build_parser()
        found: dict = {}
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                found.update(action.choices)
        return found

    def test_both_hosts_declare_the_verb_through_the_one_shared_declarator(self):
        for mod in (oc_runipd, agy_runipd):
            with self.subTest(host=mod.__name__):
                self.assertIn("audit", self._subparsers(mod))
        self.assertIs(
            oc_runipd.runner_shared.add_audit_parser,
            runner_shared.add_audit_parser,
        )
        self.assertIs(
            agy_runipd.runner_shared.add_audit_parser,
            runner_shared.add_audit_parser,
        )

    def test_the_two_hosts_render_the_same_verb(self):
        """Only the program name and the `aw oc run`/`aw agy run` example prefix may differ.

        The same strictness `stop` gets, for the same reason: a verb that exists on both hosts but
        documents itself differently has forked in the only way an operator can see.
        """

        rendered = {}
        for mod in (oc_runipd, agy_runipd):
            rendered[mod.__name__] = self._subparsers(mod)["audit"].format_help()

        def normalize(text: str) -> str:
            for host_specific, placeholder in (
                ("runagy", "<prog>"),
                ("runipd", "<prog>"),
                ("aw agy run", "aw <host> run"),
                ("aw oc run", "aw <host> run"),
            ):
                text = text.replace(host_specific, placeholder)
            return text

        self.assertEqual(
            normalize(rendered[oc_runipd.__name__]),
            normalize(rendered[agy_runipd.__name__]),
            "the two hosts' `audit` verbs are not the same verb",
        )

    def test_the_verb_is_in_both_implicit_start_shim_sets(self):
        """A missing token rewrites `audit <id6>` into `start audit <id6>`, i.e. a paid execution.

        Read off `main`'s AST, matching how `test_runner_stop_triggers` reads it, because the set is
        deliberately an inline literal inside `main` rather than a module constant.
        """

        import ast
        import inspect
        import textwrap

        for mod in (oc_runipd, agy_runipd):
            with self.subTest(host=mod.__name__):
                tree = ast.parse(textwrap.dedent(inspect.getsource(mod.main)))
                shim = None
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign) and any(
                        isinstance(t, ast.Name) and t.id == "subcommands"
                        for t in node.targets
                    ):
                        shim = set(ast.literal_eval(node.value))
                        break
                self.assertIsNotNone(shim, f"{mod.__name__} has no inline shim set")
                assert shim is not None
                self.assertIn(
                    "audit",
                    shim,
                    f"{mod.__name__} would rewrite `audit <id6>` into `start audit <id6>`, paying "
                    f"for an execution attempt against an already-executed plan",
                )

    def test_a_bare_audit_is_not_rewritten_into_a_run_launch(self):
        """The CONSEQUENCE, observed rather than inferred: no run directory may be created.

        The discriminator is deliberately not "it exited nonzero", because a launched run can also
        fail; it is that nothing was minted under the runs root.
        """

        with TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            rc = oc_runipd.main(["audit", "nosuch", "--repo", str(repo)])
            self.assertEqual(rc, 1, "a refused audit must exit 1, not launch")
            runs = repo / ".aw" / "records" / "runs"
            self.assertFalse(
                runs.exists() and any(runs.iterdir()),
                f"`audit` was rewritten into `start`: a run was created under {runs}",
            )

    def test_the_agy_binding_refuses_and_names_the_working_spelling(self):
        """Declared on both hosts, implemented on one, and the one that is not says so out loud."""

        rc = agy_runipd.handle_audit_command(argparse.Namespace(id6="abc123", repo="."))
        self.assertEqual(
            rc,
            2,
            "a not-implemented verb must exit 2 (cannot run), not 1 (refused after checking)",
        )

    def test_the_verb_is_not_on_the_read_only_runs_noun(self):
        """F-18: `aw runs` self-describes as read-only with FOUR named exceptions.

        A verb that launches a model turn and writes belongs to neither half of that split, which is
        why it hangs off the host runner noun alongside `stop` and `integrate`.
        """

        from agent_workflows import cli

        parser = cli._build_parser()
        runs_parser = None
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                runs_parser = action.choices.get("runs")
        self.assertIsNotNone(runs_parser, "the `aw runs` noun disappeared")
        assert runs_parser is not None
        leaves: set[str] = set()
        for action in runs_parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                leaves |= set(action.choices)
        self.assertNotIn(
            "audit",
            leaves,
            "`audit` was added to the READ-ONLY half of the run surface; it launches a model turn "
            "and writes a verdict, so it belongs on the host runner noun",
        )


if __name__ == "__main__":
    unittest.main()
