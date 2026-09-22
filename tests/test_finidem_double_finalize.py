#!/usr/bin/env python3
"""finidem (`ld8lb3`): a begin receipt is a SINGLE-USE token with TWO consumers.

THE MEASURED INCIDENT this file reproduces, from run `run-20260917T210518Z-1714328`, IPD `63425h`:
the driver ran `aw ipd begin` and it succeeded; the agent turn did its work and then finalized the
plan ITSELF (`575f0b32 lifecycle(63425h): finalize 63425h -> executed`); a successful finalize
CONSUMES the receipt (`ipd_lifecycle.py`, "Consume the begin receipt"); the driver's own
`driver_finalize` then ran finalize a SECOND time, found no receipt, and refused with "no begin
receipt for 63425h: run `aw ipd begin` first (fail-closed: no receipt = no execution authority)".
The item was recorded `substantially-complete` and its lane PRESERVED as not-integrated while its
work was complete, committed, and already in `executed/`.

TWO DEFECTS, both covered here:

* BEHAVIORAL (backlog `02371s`): the driver's finalize step was not idempotent, so an
  already-finalized item was refused instead of proceeding to INTEGRATION.
* DIAGNOSTIC (backlog `894vzu`): `finalize_precheck` mapped ONE condition (`receipt is None`) onto a
  message asserting ONE specific cause, so a CONSUMED receipt (the transition already succeeded) was
  indistinguishable from a NEVER-ISSUED one (genuinely no authority), and the remedy it prescribed
  (`aw ipd begin`) is actively harmful in the consumed case.

THE FAIL-OPEN CONTROL IS THE LOAD-BEARING TEST IN THIS FILE, not the happy path. The fix must key on
a POSITIVE, PLAN-BOUND observation that the transition ALREADY HAPPENED, never on the ABSENCE of a
receipt, or "no receipt = no execution authority" inverts from fail-closed to fail-open. Specifically
`run_selection_policy.is_in_terminal_directory` is NOT an admissible predicate: it returns True for
`/reusable/`, which `_IPD_ACTIONS` re-dispatches (`ACTION_EXECUTE`), so keying on it would read a
never-issued receipt on a reusable plan as success. `ReusablePlanIsNotAlreadyFinalized` below fails
if that predicate is ever swapped back in.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import artifact_core as AC
from agent_workflows import ipd_authoring as A
from agent_workflows import ipd_lifecycle as LC
from agent_workflows import runner_shared as RS


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    # Mirror the real repo: the begin receipt lives in the gitignored .aw/state/ tree.
    (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")


def _commit_all(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)


def _ready_plan_text(
    *,
    plan_id: str = "abc123",
    scope_paths: str = "agent_workflows/demo.py, tests/test_demo.py",
) -> str:
    """A conforming child IPD that lints CONFORMING at the pre-execution checkpoint."""
    txt = A.build_skeleton(
        kind="child",
        title="demo",
        author="tester",
        when="2026-09-17",
        set_name="demo",
        order=1,
        plan_id=plan_id,
    )
    out = []
    in_meta = True
    for ln in txt.splitlines():
        if ln.startswith("## "):
            in_meta = False
        if in_meta and ln.startswith("- Status:"):
            out.append("- Status: approved")
            continue
        if in_meta and ln.startswith("- Scope-Paths:"):
            out.append("- Scope-Paths: " + scope_paths)
            continue
        if in_meta and ln.startswith("- Item-Dependencies:"):
            out.append("- Item-Dependencies: none")
            continue
        out.append(ln)
        if in_meta and ln.startswith("- Author:"):
            out.append("- Approval: 2026-09-17, human: approved")
    return "\n".join(out) + "\n"


def _completed_plan_text(**kw: str) -> str:
    """A ready plan whose single E-01/V-01 is performed/pass, so pre-transition lint CONFORMS."""
    t = _ready_plan_text(**kw)
    t = t.replace("- [ ] E-01 ", "- [x] E-01 ", 1).replace(
        "  - Execution state: pending", "  - Execution state: performed", 1
    )
    t = (
        t.replace("- [ ] V-01 validates E-01", "- [x] V-01 validates E-01", 1)
        .replace(
            "  - Observed evidence:\n", "  - Observed evidence: done, verified.\n", 1
        )
        .replace("  - Result: pending", "  - Result: pass", 1)
    )
    return t


def _write_plan(root: Path, text: str, name: str, bucket: str = "pending") -> Path:
    d = root / ".aw" / "records" / "plans" / bucket
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(text, encoding="utf-8")
    return p


class _ScratchRepo(unittest.TestCase):
    """A git-backed throwaway repo holding ONE conforming, approved, executable plan."""

    PLAN_ID = "abc123"
    PLAN_NAME = "20260917-demo-01-abc123-demo.ipd.md"

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir()
        (self.root / "tests").mkdir()
        self.plan = _write_plan(
            self.root, _completed_plan_text(plan_id=self.PLAN_ID), self.PLAN_NAME
        )
        _commit_all(self.root, "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def begin(self) -> None:
        res = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

    def do_inscope_work_and_commit(self) -> None:
        (self.root / "agent_workflows" / "demo.py").write_text(
            "print('x')\n", encoding="utf-8"
        )
        (self.root / "tests" / "test_demo.py").write_text(
            "def test():\n    pass\n", encoding="utf-8"
        )
        _commit_all(self.root, "in-scope work")

    @property
    def executed_plan(self) -> Path:
        return self.root / ".aw" / "records" / "plans" / "executed" / self.PLAN_NAME

    def finalize(self, plan: Path | None = None) -> LC.FinalizeResult:
        return LC.finalize(
            self.root,
            plan or self.plan,
            "opencode/test",
            "did the work",
            apply=True,
        )


class TheSecondFinalizeOfTheSamePlan(_ScratchRepo):
    """E-01/E-02/E-03: the reproduction, and the classification that replaces its refusal.

    THE BASELINE this asserts against, measured at HEAD before the fix (V-01):

        exit_code=1
        message='no begin receipt for abc123: run `aw ipd begin` first (fail-closed: no receipt =
                 no execution authority).'
        findings=('missing begin receipt at .../.aw/state/ipd-lifecycle/abc123.receipt.json',)

    That refusal is FALSE in this situation: begin DID run, authority DID exist, and the transition
    the caller wants has ALREADY HAPPENED. The remedy it prescribes is harmful, because running
    `aw ipd begin` on an already-finalized plan would mint fresh authority for completed work.
    """

    def test_the_first_finalize_succeeds_and_consumes_the_receipt(self):
        """The premise: a successful finalize CONSUMES the receipt, by design. Not a defect."""
        self.begin()
        receipt = LC.receipt_path_for(self.root, self.PLAN_ID)
        self.assertTrue(receipt.is_file())
        self.do_inscope_work_and_commit()
        first = self.finalize()
        self.assertEqual(
            first.exit_code, LC.EXIT_OK, f"{first.message} {first.findings}"
        )
        self.assertTrue(self.executed_plan.is_file())
        self.assertFalse(
            receipt.exists(),
            "a successful finalize must consume the receipt (that is what makes it a PROOF)",
        )

    def test_the_second_finalize_reports_ALREADY_FINALIZED_not_missing_authority(self):
        """THE DEFECT, inverted: the same call now names the cause that is actually true."""
        self.begin()
        self.do_inscope_work_and_commit()
        self.assertEqual(self.finalize().exit_code, LC.EXIT_OK)

        code, message, _evidence, findings = LC.finalize_precheck(
            self.root, self.executed_plan
        )
        self.assertEqual(code, LC.EXIT_FINDINGS, message)
        self.assertIn(
            LC.FINDING_RECEIPT_ALREADY_FINALIZED,
            findings,
            f"expected the ALREADY-FINALIZED finding id; got {findings}",
        )
        self.assertNotIn(
            LC.FINDING_RECEIPT_NEVER_ISSUED,
            findings,
            "a CONSUMED receipt must not be reported as never-issued: that is the defect",
        )
        # E-03: the message states the true situation and does NOT prescribe `aw ipd begin`.
        self.assertIn("already", message.lower())
        self.assertNotIn(
            "aw ipd begin",
            message,
            "running begin on an already-finalized plan would mint authority for completed work",
        )
        self.assertNotIn("no execution authority", message)

    def test_the_already_finalized_message_cites_the_plan_bound_lifecycle_commit(self):
        """The strongest available evidence is the plan-bound commit, so the message names it."""
        self.begin()
        self.do_inscope_work_and_commit()
        self.assertEqual(self.finalize().exit_code, LC.EXIT_OK)
        _code, message, evidence, _findings = LC.finalize_precheck(
            self.root, self.executed_plan
        )
        self.assertEqual(evidence["already_finalized"]["bucket"], "executed")
        commit = evidence["already_finalized"]["lifecycle_commit"]
        self.assertTrue(
            commit, "the plan-bound lifecycle commit must be resolvable here"
        )
        self.assertIn(commit[:12], message)
        subject = AC.finalize_commit_subject(self.PLAN_ID)
        proc = subprocess.run(
            ["git", "log", "--format=%H %s", "-1", commit],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn(subject, proc.stdout)

    def test_a_never_issued_receipt_STILL_refuses_with_the_unchanged_message(self):
        """THE FAIL-CLOSED CONTROL: absence of a receipt on a non-terminal plan is unchanged."""
        code, message, _evidence, findings = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(code, LC.EXIT_FINDINGS)
        self.assertEqual(
            message,
            f"no begin receipt for {self.PLAN_ID}: run `aw ipd begin` first (fail-closed: no "
            "receipt = no execution authority).",
        )
        self.assertIn(LC.FINDING_RECEIPT_NEVER_ISSUED, findings)
        self.assertNotIn(LC.FINDING_RECEIPT_ALREADY_FINALIZED, findings)
        self.assertTrue(
            any("missing begin receipt at" in f for f in findings),
            f"the never-issued finding text must be unchanged; got {findings}",
        )

    def test_a_stale_receipt_STILL_refuses_and_its_branch_is_untouched(self):
        """The third cause keeps its own verdict: a rewritten contract is not a widening."""
        self.begin()
        # Rewrite a frozen REQUIREMENT (E-item action text) -> not an additive widening.
        text = self.plan.read_text(encoding="utf-8").replace(
            "- [x] E-01 ", "- [x] E-01 REWRITTEN REQUIREMENT ", 1
        )
        self.plan.write_text(text, encoding="utf-8")
        _commit_all(self.root, "rewrite a frozen requirement")
        code, message, _evidence, findings = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(code, LC.EXIT_FINDINGS)
        self.assertIn("is STALE", message)
        self.assertIn("re-run `aw ipd begin`", message)
        self.assertIn("plan content digest no longer matches the receipt", findings)
        self.assertNotIn(LC.FINDING_RECEIPT_ALREADY_FINALIZED, findings)
        self.assertNotIn(LC.FINDING_RECEIPT_NEVER_ISSUED, findings)

    def test_the_three_finding_ids_are_DISTINCT(self):
        """E-07: a future change must not silently collapse three causes into one verdict."""
        ids = (
            LC.FINDING_RECEIPT_ALREADY_FINALIZED,
            LC.FINDING_RECEIPT_NEVER_ISSUED,
            LC.FINDING_RECEIPT_STALE,
        )
        self.assertEqual(len(set(ids)), 3, ids)
        for fid in ids:
            self.assertTrue(fid and isinstance(fid, str), ids)


class ReusablePlanIsNotAlreadyFinalized(_ScratchRepo):
    """THE FAIL-OPEN CONTROL (review PR-001). The single most important test in this file.

    `run_selection_policy.is_in_terminal_directory` returns True for `/reusable/`, which is NOT a
    completed disposition: `.aw/records/plans/reusable/README.md` says "Not a terminal state" and
    `_IPD_ACTIONS["reusable"]` is `ACTION_EXECUTE`, so the runner DISPATCHES such a plan repeatedly.
    Keying ALREADY-FINALIZED on that predicate would therefore read a never-issued receipt on every
    reusable run as "already finalized" and integrate with NO execution authority at all - the exact
    fail-open inversion OQ-02 forbids. This test fails if the predicate is ever widened back.
    """

    def test_is_in_terminal_directory_admits_reusable_so_it_is_NOT_the_predicate(self):
        from agent_workflows import run_selection_policy as RSP

        reusable = Path(".aw/records/plans/reusable/20260917-x-01-aaa111-r.ipd.md")
        self.assertTrue(
            RSP.is_in_terminal_directory(reusable),
            "the counterfactual this control exists for: the rejected predicate admits reusable",
        )
        self.assertEqual(RSP._IPD_ACTIONS["reusable"], RSP.ACTION_EXECUTE)
        # The ADMISSIBLE predicate discriminates.
        self.assertEqual(RS.plan_bucket(reusable), "reusable")
        self.assertIs(
            LC.plan_already_finalized(self.root, reusable, "aaa111").already, False
        )

    def test_a_reusable_plan_with_NO_receipt_classifies_NEVER_ISSUED_and_refuses(self):
        plan = _write_plan(
            self.root,
            _completed_plan_text(plan_id="reu777"),
            "20260917-demo-02-reu777-reusable.ipd.md",
            bucket="reusable",
        )
        _commit_all(self.root, "add a reusable plan")
        code, message, _evidence, findings = LC.finalize_precheck(self.root, plan)
        self.assertEqual(code, LC.EXIT_FINDINGS, message)
        self.assertIn(LC.FINDING_RECEIPT_NEVER_ISSUED, findings)
        self.assertNotIn(
            LC.FINDING_RECEIPT_ALREADY_FINALIZED,
            findings,
            "a reusable plan is RE-DISPATCHED, so a missing receipt there is no authority at all",
        )
        self.assertIn("no execution authority", message)
        self.assertTrue(plan.is_file(), "the plan must be left unmoved")


class PlanAlreadyFinalizedPredicate(_ScratchRepo):
    """E-02: the positive, plan-bound observation, asserted directly on the predicate."""

    def test_a_pending_plan_is_not_already_finalized(self):
        verdict = LC.plan_already_finalized(self.root, self.plan, self.PLAN_ID)
        self.assertFalse(verdict.already)
        self.assertEqual(verdict.bucket, "pending")
        self.assertIsNone(verdict.lifecycle_commit)

    def test_a_genuinely_finalized_plan_is_recognized_with_its_commit(self):
        self.begin()
        self.do_inscope_work_and_commit()
        res = self.finalize()
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)
        verdict = LC.plan_already_finalized(self.root, self.executed_plan, self.PLAN_ID)
        self.assertTrue(verdict.already)
        self.assertEqual(verdict.bucket, "executed")
        self.assertEqual(verdict.lifecycle_commit, res.commit)

    def test_the_executed_BUCKET_alone_is_sufficient_when_no_commit_is_resolvable(self):
        """The bucket is the weakest ADMISSIBLE signal, so it must stand on its own.

        A plan can legitimately sit in `executed/` with its lifecycle commit unreachable from this
        checkout's HEAD (it landed on a lane that was never merged here). That is still a completed
        transition, and it is the measured incident's own shape, so the predicate accepts it.
        """
        plan = _write_plan(
            self.root,
            _completed_plan_text(plan_id="exe999"),
            "20260917-demo-03-exe999-hand-placed.ipd.md",
            bucket="executed",
        )
        verdict = LC.plan_already_finalized(self.root, plan, "exe999")
        self.assertTrue(verdict.already)
        self.assertEqual(verdict.bucket, "executed")
        self.assertIsNone(verdict.lifecycle_commit)


class TheFinalizeEntryPointsAgreeWithThePrecheck(_ScratchRepo):
    """`finalize()` must carry the classification through, not just `finalize_precheck`."""

    def test_finalize_of_an_already_finalized_plan_says_so(self):
        self.begin()
        self.do_inscope_work_and_commit()
        self.assertEqual(self.finalize().exit_code, LC.EXIT_OK)
        again = self.finalize(self.executed_plan)
        self.assertEqual(again.exit_code, LC.EXIT_FINDINGS, again.message)
        self.assertIn(LC.FINDING_RECEIPT_ALREADY_FINALIZED, again.findings)
        self.assertNotIn("aw ipd begin", again.message)
        # Nothing was mutated by the refusal: the plan is still the one finalize already made.
        self.assertTrue(self.executed_plan.is_file())


class BothHostsDriverFinalizeIsIdempotent(unittest.TestCase):
    """E-04/E-05: THE DRIVER-LEVEL half, driven through the REAL `driver_finalize` on BOTH hosts.

    This is V-07's acceptable form (2): it exercises the driver's own finalize-and-integrate decision
    in a scratch repo rather than re-asserting E-02's classification, which a unit test on the
    predicate alone would do while proving nothing about the code path that stranded the lane.

    WHY BOTH HOSTS ARE DRIVEN SEPARATELY rather than one being taken as proof of the other:
    `driver_finalize` is genuinely DEFINED TWICE (`oc_runipd`, `agy_runipd`) and so is the whole
    result-handling block, a duplication `tests/test_rununify_execute_item.py` tracks on purpose. The
    shared piece is the DECISION (`runner_shared.finalize_outcome`), and `test_both_hosts_share_the_one_decision`
    below pins that, so a future host that forgot to call it fails here.
    """

    HOSTS = ("oc_runipd", "agy_runipd")

    def _driver(self, host: str):
        import importlib

        return importlib.import_module(f"agent_workflows.{host}")

    def _repo_with_plan(self, root: Path, id6: str):
        from tests.test_oc_runipd import _init_repo_with_conforming_plan

        return _init_repo_with_conforming_plan(root / "repo", id6)

    def _do_work(self, repo: Path) -> None:
        (repo / "src").mkdir(exist_ok=True)
        (repo / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
        subprocess.run(["git", "add", "src/demo.txt"], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "demo: create src/demo.txt"], cwd=repo, check=True
        )

    def test_a_second_driver_finalize_of_an_agent_finalized_plan_SUCCEEDS(self):
        """THE MEASURED INCIDENT, at the driver seam: the agent finalized, the driver ran again.

        Before this fix the second call returned nonzero, which routed the item to
        `handle_finalize_refusal`, left it `substantially-complete`, and PRESERVED the lane as
        not-integrated even though the work was complete and already in `executed/`.
        """
        for host in self.HOSTS:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as temp:
                drv = self._driver(host)
                plan = self._repo_with_plan(Path(temp), "idm001")
                repo = plan.parents[4]
                actor = drv.driver_actor({"options": {"model": "test"}})
                rc, msg = drv.driver_begin(repo, "idm001", actor)
                self.assertEqual(rc, 0, msg)
                self._do_work(repo)

                # The AGENT's own finalize (what a `self_finalize` turn measurably does).
                first_rc, first_msg = drv.driver_finalize(
                    repo, plan, "idm001", actor, "agent finalized it"
                )
                self.assertEqual(first_rc, 0, first_msg)
                executed = repo / ".aw" / "records" / "plans" / "executed" / plan.name
                self.assertTrue(executed.is_file())
                self.assertFalse(LC.receipt_path_for(repo, "idm001").exists())

                # The DRIVER's own finalize, 5m38s later in the measured incident.
                second_rc, second_msg = drv.driver_finalize(
                    repo, executed, "idm001", actor, "driver self-finalize"
                )
                self.assertEqual(
                    second_rc,
                    0,
                    f"{host}: a second finalize of an already-finalized plan must be a NO-OP "
                    f"success so the caller integrates; got {second_rc}: {second_msg}",
                )
                self.assertIn("NO-OP", second_msg)
                self.assertIn("already succeeded", second_msg)
                # Idempotent means UNCHANGED, not "done twice": no second lifecycle commit.
                subjects = subprocess.run(
                    ["git", "log", "--format=%s"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
                self.assertEqual(
                    subjects.count(AC.finalize_commit_subject("idm001")),
                    1,
                    f"{host}: exactly ONE lifecycle commit must exist:\n{subjects}",
                )

    def test_a_NEVER_ISSUED_receipt_still_refuses_at_the_driver_seam(self):
        """THE FAIL-CLOSED CONTROL at the driver seam: no begin, no integration."""
        for host in self.HOSTS:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as temp:
                drv = self._driver(host)
                plan = self._repo_with_plan(Path(temp), "idm002")
                repo = plan.parents[4]
                actor = drv.driver_actor({"options": {"model": "test"}})
                self._do_work(repo)
                rc, msg = drv.driver_finalize(
                    repo, plan, "idm002", actor, "no begin ever ran"
                )
                self.assertNotEqual(
                    rc,
                    0,
                    f"{host}: a never-issued receipt must STILL refuse; got {rc}: {msg}",
                )
                self.assertIn("no begin receipt", msg)
                self.assertIn("no execution authority", msg)
                self.assertTrue(
                    plan.is_file(), f"{host}: the plan must be left unmoved"
                )
                self.assertFalse(
                    (
                        repo / ".aw" / "records" / "plans" / "executed" / plan.name
                    ).exists()
                )

    def test_both_hosts_share_the_one_decision(self):
        """The rule is reached ONCE from both hosts, so they cannot answer differently.

        RE-POINTED, NOT WEAKENED, when hostdedup Order 01 (`li44r9`) consolidated `driver_finalize`.
        This test was written when the body was DUPLICATED per host and asserted the literal
        `finalize_outcome` inside each copy. There is now ONE body in `runner_shared` and the hosts are
        thin wrappers, so the original assertion would fail on a tree where the property is MORE true
        than before. The property itself is unchanged and is asserted in two steps: each host delegates
        to the shared definition, and the shared definition routes through `finalize_outcome`. A host
        that re-forked its own body, or a shared body that dropped the decision, still fails.
        """
        import inspect

        shared_src = inspect.getsource(RS.driver_finalize)
        self.assertIn(
            "finalize_outcome",
            shared_src,
            "the SHARED driver_finalize must route its result through the shared decision; "
            "dropping it here silently un-does finidem `ld8lb3` for BOTH hosts at once",
        )
        for host in self.HOSTS:
            with self.subTest(host=host):
                src = inspect.getsource(self._driver(host).driver_finalize)
                self.assertIn(
                    "runner_shared.driver_finalize",
                    src,
                    f"{host}'s driver_finalize must delegate to the ONE shared definition; a re-forked "
                    "body could answer the idempotency question differently from its twin",
                )

    def test_finalize_outcome_never_keys_on_a_missing_receipt(self):
        """OQ-02, as a property of the shared decision: only a POSITIVE observation flips a refusal."""
        with tempfile.TemporaryDirectory() as temp:
            plan = self._repo_with_plan(Path(temp), "idm003")
            repo = plan.parents[4]
            # A pending plan with NO receipt: the refusal must pass straight through.
            rc, msg = RS.finalize_outcome(
                repo, plan, "idm003", 1, "no begin receipt ..."
            )
            self.assertEqual(rc, 1)
            self.assertEqual(msg, "no begin receipt ...")
            # A zero return is passed through untouched (the normal path gains no new logic).
            rc, msg = RS.finalize_outcome(repo, plan, "idm003", 0, "finalized")
            self.assertEqual((rc, msg), (0, "finalized"))

    def test_finalize_outcome_fails_closed_when_the_predicate_raises(self):
        """A broken observation must leave the refusal in place, never invent a success."""
        with mock.patch.object(
            LC, "plan_already_finalized", side_effect=RuntimeError("git exploded")
        ):
            rc, msg = RS.finalize_outcome(
                Path("/nonexistent"),
                Path("/nonexistent/p.ipd.md"),
                "idm004",
                1,
                "refused",
            )
        self.assertEqual((rc, msg), (1, "refused"))


class TheRunTreatsAnAlreadyFinalizedItemAsExecuted(unittest.TestCase):
    """E-04: the CONSEQUENCE the measured incident actually needed - integration, not a preserved lane.

    `execute_item_core`'s finalize arm branches on `fin_rc`: zero integrates and records the item
    `executed`, nonzero routes to `handle_finalize_refusal`, which records the refusal and leaves the
    item `substantially-complete` (or requeues/fails it). So the item's fate is decided ENTIRELY by
    the code this plan changed, and asserting on that branch is what shows the lane now integrates.
    """

    def test_the_refusal_arm_is_not_entered_for_an_already_finalized_plan(self):
        import tempfile as _tf

        from tests.test_oc_runipd import _init_repo_with_conforming_plan

        with _tf.TemporaryDirectory() as temp:
            from agent_workflows import oc_runipd as drv

            plan = _init_repo_with_conforming_plan(Path(temp) / "repo", "idm005")
            repo = plan.parents[4]
            actor = drv.driver_actor({"options": {"model": "test"}})
            self.assertEqual(drv.driver_begin(repo, "idm005", actor)[0], 0)
            (repo / "src").mkdir(exist_ok=True)
            (repo / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/demo.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "work"], cwd=repo, check=True)
            self.assertEqual(
                drv.driver_finalize(repo, plan, "idm005", actor, "agent did it")[0], 0
            )
            executed = repo / ".aw" / "records" / "plans" / "executed" / plan.name

            called: list[str] = []
            with mock.patch.object(
                RS,
                "handle_finalize_refusal",
                lambda **kw: called.append(kw.get("fin_msg", ""))
                or "substantially-complete",
            ):
                fin_rc, fin_msg = drv.driver_finalize(
                    repo, executed, "idm005", actor, "driver self-finalize"
                )
                if fin_rc != 0:
                    RS.handle_finalize_refusal(
                        run_dir=Path(temp),
                        state={},
                        item={"id6": "idm005"},
                        attempt={},
                        fin_rc=fin_rc,
                        fin_msg=fin_msg,
                        disposition="substantially-complete",
                        host_labels=RS.OC_HOST_LABELS,
                        save_state=lambda *a, **k: None,
                        append_jsonl=lambda *a, **k: None,
                    )
            self.assertEqual(
                called,
                [],
                "an already-finalized item must NOT reach the refusal arm that preserved the lane",
            )


class TheWorkerRoleCannotDelegateAroundTheGuard(_ScratchRepo):
    """E-06 / F-10b: `aw set executed` reached `finalize()` from a worker lane UNGUARDED.

    `worker_role_active` was checked in the CLI wrappers `run_begin`/`run_finalize` ONLY, and
    `status_set` contains ZERO references to it, so `aw set executed <plan>` - which delegates
    straight into `_life.finalize` - performed a full terminal transaction from a worker lane with no
    role refusal at all. `retire_orchestrator` had the identical gap and closed it by checking the
    predicate itself; this is the same fix at the `finalize()` choke point, which covers all three
    callers (the CLI, the rollup, and `status_set`).

    HONEST LIMIT, stated because the opposite claim would be false: the env marker is a SELECTOR, not
    a boundary (the measured incident defeated it with `env -u AW_EXECUTION_ROLE`). Closing THAT
    needs an OS sandbox or a separate principal and is out of scope here.
    """

    def _finalize_with_env(self, env: dict[str, str]) -> LC.FinalizeResult:
        with mock.patch.dict(os.environ, env, clear=False):
            if env.get(LC.EXECUTION_ROLE_ENV) is None:
                os.environ.pop(LC.EXECUTION_ROLE_ENV, None)
            return self.finalize()

    def test_a_worker_role_finalize_performs_NO_transition(self):
        self.begin()
        self.do_inscope_work_and_commit()
        before = self.plan.read_text(encoding="utf-8")
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        res = self._finalize_with_env({LC.EXECUTION_ROLE_ENV: LC.ROLE_WORKER})
        self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN, res.message)
        self.assertIn("AW-LIFECYCLE-ROLE-001", res.message)
        self.assertIn(LC.ROLLUP_REFUSED_WORKER_ROLE, res.findings)
        # NO side effect: no status edit, no move, no commit.
        self.assertTrue(self.plan.is_file())
        self.assertEqual(self.plan.read_text(encoding="utf-8"), before)
        self.assertFalse(self.executed_plan.exists())
        self.assertEqual(
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip(),
            head,
        )

    def test_the_coordinator_path_is_UNAFFECTED(self):
        """A guard that refused the path it protects would be worse than none."""
        self.begin()
        self.do_inscope_work_and_commit()
        res = self._finalize_with_env({LC.EXECUTION_ROLE_ENV: "coordinator"})
        self.assertEqual(res.exit_code, LC.EXIT_OK, f"{res.message} {res.findings}")
        self.assertTrue(self.executed_plan.is_file())

    def test_the_refusal_is_the_FIRST_gate_so_it_cannot_leak_through_another(self):
        """Refused even when everything else about the call is invalid (an empty actor)."""
        with mock.patch.dict(
            os.environ, {LC.EXECUTION_ROLE_ENV: LC.ROLE_WORKER}, clear=False
        ):
            res = LC.finalize(self.root, self.plan, "", "m", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("AW-LIFECYCLE-ROLE-001", res.message)
        self.assertNotIn("non-empty --actor", res.message)

    def test_aw_set_executed_from_a_worker_lane_refuses(self):
        """The DELEGATION path F-10b measured: `aw set executed` via `status_set`."""
        from agent_workflows import status_set as SS

        self.begin()
        self.do_inscope_work_and_commit()
        before = self.plan.read_text(encoding="utf-8")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(Path(LC.__file__).resolve().parents[1])
        env["AW_EXECUTION_ROLE"] = LC.ROLE_WORKER
        proc = subprocess.run(
            [
                "python3",
                "-m",
                "agent_workflows",
                "set",
                "executed",
                self.PLAN_ID,
                "--actor",
                "opencode/test",
                "--message",
                "m",
                "--yes",
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
            env=env,
        )
        combined = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, combined)
        self.assertIn("AW-LIFECYCLE-ROLE-001", combined)
        self.assertTrue(self.plan.is_file(), combined)
        self.assertEqual(self.plan.read_text(encoding="utf-8"), before)
        self.assertFalse(self.executed_plan.exists(), combined)
        # `status_set` reaches the guard through the ONE choke point, not a second copy of it.
        import inspect

        self.assertNotIn("worker_role_active", inspect.getsource(SS))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
