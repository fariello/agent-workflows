#!/usr/bin/env python3
"""integearn-03 (`daexj1`): the suite-adjudication seam, proven against REAL captured output.

WHAT THIS FILE ADDS, and why it is a separate file from `tests/test_gate_answer_wiring.py` rather than
more cases in it. That file proves the gatewire-01 (`h5pyqa`) wiring behaves correctly, and it does so
with EVERY suite run and EVERY host turn stubbed, which is the right trade for a fast deterministic
file. This file exists for the cases that CANNOT be proven that way, because the thing under test is
precisely whether the production capture path really produces the values the wiring consumes.

THE DEFECT CLASS THIS FILE EXISTS TO CATCH IS MEASURED AND SHIPPED TWICE.

  * Plan `32ij2j` (now `superseded/`) proposed parsing `FAILED <nodeid>` out of
    `tool_event["stdout_excerpt"]`, a key `run_evidence.build_tool_event` did not write. Its parsed set
    would therefore have been ALWAYS EMPTY, and because its gate compared failing sets as a SUBSET, the
    empty set is a subset of everything: every lane would have earned integration, INCLUDING one that
    broke the whole suite. The gate would have been INVERTED.
  * That same read was ALREADY IN SHIPPED CODE in `oc_runipd.run_suite_check`, so
    `SuiteCheckResult.summary` was always `""` in production and every refusal reason read `no summary
    line parsed`. It was repaired by `h5pyqa` in `run_evidence.capture_command`.

NEITHER WAS CAUGHT BY THE EXISTING TESTS, and the reason is the whole point of this file: every test
around that seam MOCKS `capture_command` and FABRICATES the very key production never produced
(`tests/test_novalnomerge_integration.py:293`, `:319`, `:343`). A stubbed capture cannot notice that the
real capture does not supply the field. So the cases below drive a REAL `python3 -m pytest` against a
REAL temporary test file that REALLY fails, and assert on what genuinely came back.

THE SIX CASES daexj1 E-08 REQUIRES:

  1. A genuinely red suite yields a NON-EMPTY failing id list, extracted from real output (V-08).
  2. The E-02 INVERSION GUARD: a red exit with an EMPTY failing list still ESCALATES rather than
     integrating. The EXIT CODE is the authority and the list is only ever used to make the question
     specific. This is the single most important case here, because it is the one that was shipped
     wrong (V-02).
  3. Each verdict drives its correct action (delegated to the shipped vocabulary; see
     `TheThreeVerdictsDriveTheirActions`).
  4. A missing verdict re-prompts and then exhausts to a REFUSAL, never to an integration.
  5. A clean suite still integrates with NO question issued, so the escalation cannot become an
     unconditional tax on every green run.
  6. Both hosts resolve the SAME objects, asserted by OBJECT IDENTITY rather than by grep (V-09).

WHAT IS DELIBERATELY NOT RE-TESTED HERE: the four-answer vocabulary's own semantics, which
`tests/test_gate_answer_wiring.py` already covers in 1049 lines. Duplicating it would give two files to
update for one behavior change.

THE VOCABULARY NOTE, recorded because the plan's prose and the shipped code differ. daexj1 E-05/E-06
specify three exact prose sentinels (`SAFE TO IGNORE.`, `RETRY TESTS.`, `UNABLE TO FIX.`) parsed out of
worker stdout. The mechanism that SHIPPED (`h5pyqa`, executed 2026-09-20, under a maintainer ruling of
that date) is a four-answer JSON vocabulary in the outcome file: `not-mine` == "safe to ignore",
`fixed` == "retry tests" (and is STRICTER, because the re-run decides rather than the claim), `mine` ==
"unable to fix", plus `needs-human`, which daexj1 did not specify. This file tests the SHIPPED
vocabulary by ACTION, so it keeps proving the plan's required behavior if the tokens are ever renamed,
and it deliberately does not add a second parser for the same question, which is the divergence
daexj1's own E-09 exists to forbid.
"""

from __future__ import annotations

import ast
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from agent_workflows import agy_runipd as AGY  # noqa: E402
from agent_workflows import oc_runipd as OC  # noqa: E402
from agent_workflows import run_evidence  # noqa: E402
from agent_workflows import runner_shared as R  # noqa: E402

#: A test file that REALLY fails, used to drive a REAL pytest run. Two distinct failure SHAPES (a bare
#: assertion and a raised exception) because they render differently in pytest's short summary and a
#: parser that only handles one of them would look correct against a single-shape fixture.
_FAILING_SUITE = (
    "def test_that_passes():\n"
    "    assert True\n"
    "\n"
    "def test_that_fails_on_an_assertion():\n"
    "    assert 1 == 2\n"
    "\n"
    "def test_that_fails_by_raising():\n"
    "    raise ValueError('boom')\n"
)

_PASSING_SUITE = "def test_that_passes():\n    assert True\n"


def _suite_result(
    *,
    passing: bool = False,
    exit_code: int = 1,
    summary: str = "1 failed, 1 passed in 0.01s",
    reason: str = "the driver-run suite did not pass",
    cwd: str = ".",
    timeout_seconds: float = 600.0,
    elapsed_seconds: float = 0.5,
    failures: tuple[str, ...] = ("FAILED tests/test_x.py::test_y - assert 1 == 2",),
) -> "OC.SuiteCheckResult":
    """A `SuiteCheckResult` with sane defaults, so each case states only the field it is about.

    Keyword-only with EXPLICIT defaults rather than a `**kwargs` splat, so a static checker can see the
    field types and a typo in a field name is a `TypeError` here instead of a silently ignored key.
    """

    return OC.SuiteCheckResult(
        passing=passing,
        exit_code=exit_code,
        summary=summary,
        reason=reason,
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        elapsed_seconds=elapsed_seconds,
        failures=failures,
    )


def _revalidation(item: dict) -> dict:
    """The record the runner wrote, typed as a mapping so assertions can index it.

    A one-line accessor rather than a cast at each site: the item mapping is deliberately
    `dict[str, object]` (it stands in for the run's own heterogeneous queue entry), so every
    `_revalidation(item)["passed"]` would otherwise need its own annotation.
    """

    record = item.get("post_merge_revalidation")
    assert isinstance(record, dict), f"no revalidation record was written: {record!r}"
    return record


def _asks_the_agent(verdict) -> bool:
    """Would the runner ESCALATE this verdict to the agent? The shipped predicate decides, not a copy."""

    warranted, _reason = R.gate_answer_is_warranted(
        integration_gate_relevant=True,
        earned=verdict.earned,
        integration_signal=verdict.signal,
        session_id="session-under-test",
    )
    return warranted


class TheFailingIdsComeFromREALCapturedOutput(unittest.TestCase):
    """Case 1: drive a REAL failing command and assert the ids came back from ITS OWN output.

    NOT A REDUNDANT COPY of `TheFailingTestNamesAreCaptured` in the sibling file. That class asserts the
    PARSER over strings it supplies. This asserts the PRODUCTION PATH: that `capture_command` really
    hands back output at all, which is the exact property whose absence shipped twice unnoticed.
    """

    def _run_real_suite(self, body: str):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "test_probe.py").write_text(body, encoding="utf-8")
            return OC.run_suite_check(root, "run-under-test", timeout=300.0)

    def test_a_genuinely_red_suite_yields_a_NON_EMPTY_id_list(self) -> None:
        result = self._run_real_suite(_FAILING_SUITE)
        self.assertFalse(result.passing, "the fixture really must fail")
        self.assertEqual(result.exit_code, 1)
        self.assertTrue(
            result.failures,
            "a red suite must yield the failing ids; an EMPTY list here is the exact state that "
            "inverted plan 32ij2j's gate, because an empty set is a subset of everything",
        )
        joined = "\n".join(result.failures)
        self.assertIn("test_that_fails_on_an_assertion", joined)
        self.assertIn("test_that_fails_by_raising", joined)
        self.assertNotIn(
            "test_that_passes",
            joined,
            "a PASSING test must never appear in the failing list, or the agent is asked to "
            "attribute a failure that did not happen",
        )

    def test_the_summary_is_NON_EMPTY_which_it_was_not_in_production(self) -> None:
        """F-10: `summary` was ALWAYS `""` in production, so every refusal read `no summary line parsed`."""

        result = self._run_real_suite(_FAILING_SUITE)
        self.assertTrue(
            result.summary.strip(),
            "summary must be non-empty on a real run; it was always empty in shipped production "
            "because run_suite_check read a tool_event key build_tool_event never wrote",
        )
        self.assertIn("failed", result.summary)

    def test_the_ids_are_NOT_a_count_line(self) -> None:
        """A count cannot be attributed to a diff, which is the whole judgement the answer turns on."""

        result = self._run_real_suite(_FAILING_SUITE)
        for line in result.failures:
            self.assertIn(
                "::",
                line,
                f"{line!r} is not a node id; a count line would tell the agent nothing it can "
                f"attribute to its own change",
            )

    def test_the_capture_was_NOT_stubbed_and_the_real_command_really_ran(self) -> None:
        """Proof of provenance: the ids trace to a real subprocess, not to a fabricated field.

        Asserted by driving `capture_command` DIRECTLY (the production function, unmocked) and showing
        its returned event carries the real exit code and real output text for a command that really
        failed.
        """

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "test_probe.py").write_text(_FAILING_SUITE, encoding="utf-8")
            tool_event, _envelope = run_evidence.capture_command(
                "run-under-test",
                ["python3", "-m", "pytest", "test_probe.py", "-o", "addopts=", "-q"],
                cwd=root,
                evidence_kind="tests",
                actor="driver",
                timeout=300.0,
                max_output_bytes=512_000,
            )
        self.assertEqual(tool_event["exit_code"], 1, "the real command really failed")
        text = str(tool_event.get("stdout_excerpt") or "")
        self.assertTrue(
            text.strip(),
            "capture_command must hand the output text back; when it did not, run_suite_check's "
            "read yielded '' and the integration gate's summary was permanently empty",
        )
        ids = OC.extract_suite_failures(
            text, str(tool_event.get("stderr_excerpt") or "")
        )
        self.assertTrue(
            ids, "the ids must be recoverable from the REAL captured output"
        )

    def test_the_DURABLE_record_still_carries_no_raw_output(self) -> None:
        """D92: names are safe to persist, unbounded command output is a separate and larger decision.

        The LEDGER record must keep carrying digests and lengths only. The failing ids reach the durable
        run record instead (`attempt["suite_check"]["failures"]`), which is what a human reads.
        """

        record = run_evidence.build_tool_event(
            "run-under-test",
            ["python3", "-m", "pytest"],
            ".",
            1,
            "FAILED tests/test_x.py::test_y - assert 1 == 2\n1 failed in 0.1s",
            "",
        )
        for forbidden in ("stdout", "stdout_excerpt", "stderr", "stderr_excerpt"):
            self.assertNotIn(
                forbidden,
                record,
                f"the persisted ledger record must not carry {forbidden!r}: it is a ledger record "
                f"carrying digests, and widening it to hold command output is a schema decision "
                f"this seam does not own",
            )
        self.assertIn("stdout_sha256", record)
        self.assertIn("stdout_len", record)

    def test_a_node_id_carries_no_machine_identifying_string(self) -> None:
        """WHY names are safe where output is not: a node id is repository-relative.

        Pinned rather than asserted, because it is the reason D92's local-leaks rule is not engaged by
        persisting these ids.
        """

        result = self._run_real_suite(_FAILING_SUITE)
        for line in result.failures:
            self.assertNotIn(
                str(pathlib.Path.home()),
                line,
                "a failing id must not carry a home directory path",
            )


class TheExitCodeIsTheAuthorityAndNotTheList(unittest.TestCase):
    """Case 2, and THE case this file exists for: daexj1 E-02's anti-inversion guard.

    Plan `32ij2j` compared failing SETS as a subset and derived them from an always-empty string, so
    every lane passed including one that broke everything. Under the shipped design the EXIT CODE
    decides and the list only makes the question specific. These cases pin that ordering so a later
    refactor cannot quietly reintroduce the inversion.
    """

    def test_a_RED_exit_with_an_EMPTY_failing_list_still_ESCALATES(self) -> None:
        """THE INVERSION CASE. An empty list must never read as "nothing broke"."""

        verdict = OC.integration_is_earned(
            validate=False,
            verify_disp=None,
            suite_result=_suite_result(passing=False, exit_code=1, failures=()),
        )
        self.assertFalse(
            verdict.earned,
            "a red exit must NOT earn integration merely because no ids were parsed; that is the "
            "exact inversion that sank plan 32ij2j",
        )
        self.assertEqual(verdict.signal, R.INTEGRATION_REFUSED_SUITE_FAILED)
        self.assertTrue(
            _asks_the_agent(verdict),
            "an unparseable red suite must be ESCALATED to the agent, not silently refused and not "
            "silently integrated",
        )

    def test_a_RED_exit_with_an_EMPTY_list_and_an_EMPTY_summary_still_escalates(
        self,
    ) -> None:
        """The worst case: no ids AND no summary. It must still refuse-and-ask, never integrate."""

        verdict = OC.integration_is_earned(
            validate=False,
            verify_disp=None,
            suite_result=_suite_result(
                passing=False, exit_code=1, failures=(), summary=""
            ),
        )
        self.assertFalse(verdict.earned)
        self.assertTrue(_asks_the_agent(verdict))

    def test_the_question_never_shows_an_EMPTY_evidence_section(self) -> None:
        """An empty section reads as "no failures" and would invite a false release."""

        text = _suite_result(failures=(), summary="").failing_text
        self.assertTrue(text.strip())
        prompt = R.gate_answer_question(failing=text, changed_files=("a.py",))
        self.assertIn(text.splitlines()[0][:30], prompt)

    def test_a_PASSING_exit_earns_integration_regardless_of_the_list(self) -> None:
        """The exit code is the authority in BOTH directions, so the ordering is not one-sided.

        A non-empty `failures` tuple on a PASSING result is a nonsense input (it cannot arise from
        `run_suite_check`), and the point is exactly that the verdict does not consult the list.
        """

        verdict = OC.integration_is_earned(
            validate=False,
            verify_disp=None,
            suite_result=_suite_result(
                passing=True,
                exit_code=0,
                summary="9 passed",
                failures=("FAILED stale::leftover",),
            ),
        )
        self.assertTrue(verdict.earned, "exit 0 decides; the list is not the authority")

    def test_a_TIMEOUT_and_an_UNRUNNABLE_suite_both_refuse_fail_closed(self) -> None:
        """124/127 carry no ids at all, and neither may be read as a pass."""

        for code in (124, 127):
            with self.subTest(exit_code=code):
                verdict = OC.integration_is_earned(
                    validate=False,
                    verify_disp=None,
                    suite_result=_suite_result(
                        passing=False, exit_code=code, failures=(), summary=""
                    ),
                )
                self.assertFalse(verdict.earned)
                self.assertTrue(_asks_the_agent(verdict))

    def test_the_verdict_reads_PASSING_and_never_the_failing_list(self) -> None:
        """Structural pin over the AST, so the ordering survives a refactor.

        `integration_is_earned` is the one predicate deciding this. It must branch on the suite's
        PASSING/exit state and must NOT consult `failures`, because the moment it does, an empty list
        acquires meaning and the inversion becomes reachable again.
        """

        source = inspect_source(OC.integration_is_earned)
        tree = ast.parse(source)
        attrs = {
            node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
        }
        self.assertIn(
            "passing",
            attrs,
            "the verdict must consult the suite's passing state",
        )
        self.assertNotIn(
            "failures",
            attrs,
            "integration_is_earned must NOT consult the failing-id list: that is what gives an "
            "empty list decision power and reintroduces 32ij2j's inversion",
        )


class AGreenSuiteIsNeverTaxedWithAQuestion(unittest.TestCase):
    """Case 5: the escalation must not become an unconditional cost on every passing run."""

    def test_a_clean_suite_integrates_with_NO_question_asked(self) -> None:
        verdict = OC.integration_is_earned(
            validate=False,
            verify_disp=None,
            suite_result=_suite_result(
                passing=True, exit_code=0, summary="7694 passed", failures=()
            ),
        )
        self.assertTrue(verdict.earned)
        self.assertFalse(
            _asks_the_agent(verdict),
            "a green suite must spend NO agent turn; an escalation on success would be a tax on "
            "every run",
        )

    def test_a_DECLINED_verifier_is_never_answerable_by_the_agent_it_judged(
        self,
    ) -> None:
        """Out of scope for this plan and pinned so it stays that way.

        A verifier that explicitly declined is a stronger, more specific judgement than a red suite.
        Letting the judged agent answer it away would make `--validate` WEAKER than the default.
        """

        verdict = OC.integration_is_earned(
            validate=True, verify_disp="blocked", suite_result=None
        )
        self.assertFalse(verdict.earned)
        self.assertEqual(verdict.signal, R.INTEGRATION_REFUSED_VERIFIER_DECLINED)
        self.assertFalse(_asks_the_agent(verdict))

    def test_NO_TRUST_SIGNAL_at_all_is_not_asked_about_either(self) -> None:
        """There is nothing to attribute: no suite ran, so the question could only elicit a guess."""

        verdict = OC.integration_is_earned(
            validate=False, verify_disp=None, suite_result=None
        )
        self.assertFalse(verdict.earned)
        self.assertEqual(verdict.signal, R.INTEGRATION_REFUSED_NO_SIGNAL)
        self.assertFalse(_asks_the_agent(verdict))


class TheThreeVerdictsDriveTheirActions(unittest.TestCase):
    """Cases 3 and 4, asserted BY ACTION so a token rename cannot silently break the plan's contract.

    daexj1 names three sentinels; the shipped vocabulary has four answers. The mapping is stated in this
    module's docstring. Each case below names the daexj1 sentinel it stands for.
    """

    def _perform(self, answer, *, reason="because", rerun=None, budget=0):
        """Drive the shipped `perform_gate_answer` with a stubbed ask/outcome. No model turn is spent."""

        import json

        with tempfile.TemporaryDirectory() as d:
            outcome = pathlib.Path(d) / "outcome.json"
            prompts: list[str] = []

            def _ask(prompt: str) -> None:
                prompts.append(prompt)
                payload = (
                    {}
                    if answer is None
                    else {R.GATE_ANSWER_KEY: {"answer": answer, "reason": reason}}
                )
                outcome.write_text(json.dumps(payload), encoding="utf-8")

            result = R.perform_gate_answer(
                suite_result=_suite_result(),
                changed_files=("agent_workflows/x.py",),
                ask=_ask,
                outcome_path=outcome,
                rerun_suite=rerun,
                retry_budget=budget,
                session_id="session-under-test",
            )
            return result, prompts

    def test_SAFE_TO_IGNORE_integrates_and_records_the_explanation(self) -> None:
        """daexj1's `SAFE TO IGNORE.` == shipped `not-mine`."""

        result, _prompts = self._perform(
            R.GATE_ANSWER_NOT_MINE,
            reason="the failure is in a file my diff never touched",
        )
        self.assertTrue(
            result.release, "this is the verdict that lets validated work land"
        )
        self.assertEqual(result.record["answer"], R.GATE_ANSWER_NOT_MINE)
        self.assertIn("never touched", result.record["reason"])

    def test_RETRY_TESTS_re_runs_and_the_RERUN_decides_not_the_claim(self) -> None:
        """daexj1's `RETRY TESTS.` == shipped `fixed`, which is STRICTER: the claim alone never releases."""

        runs: list[int] = []

        def _green_rerun():
            runs.append(1)
            return _suite_result(passing=True, exit_code=0, summary="all green")

        result, _ = self._perform(
            R.GATE_ANSWER_FIXED,
            reason="repaired the import",
            rerun=_green_rerun,
            budget=2,
        )
        self.assertEqual(len(runs), 1, "the suite must actually be re-run")
        self.assertTrue(result.release)
        self.assertIs(result.record["recheck_passed"], True)

    def test_a_RETRY_claim_whose_rerun_STAYS_RED_refuses(self) -> None:
        def _red_rerun():
            return _suite_result(passing=False, exit_code=1)

        result, _ = self._perform(
            R.GATE_ANSWER_FIXED, reason="I think I fixed it", rerun=_red_rerun, budget=1
        )
        self.assertFalse(
            result.release, "an unverified repair claim must never release the lane"
        )
        self.assertIs(result.record["recheck_passed"], False)

    def test_UNABLE_TO_FIX_refuses_and_the_lane_is_preserved(self) -> None:
        """daexj1's `UNABLE TO FIX.` == shipped `mine`. The correct outcome for a genuinely broken change."""

        result, _ = self._perform(R.GATE_ANSWER_MINE)
        self.assertFalse(result.release)
        self.assertTrue(result.record["refuses"])

    def test_NO_VERDICT_refuses_rather_than_integrating(self) -> None:
        """Case 4: exhaustion must land on the SAFE side. Silence is not consent."""

        result, prompts = self._perform(None)
        self.assertEqual(len(prompts), 1, "the agent is asked")
        self.assertFalse(
            result.release,
            "an absent verdict must REFUSE: a wrongly refused lane is preserved and recoverable, a "
            "wrongly integrated one merges work no trust signal cleared",
        )
        self.assertFalse(result.record["usable"])

    def test_an_UNKNOWN_token_refuses_and_is_named_in_the_record(self) -> None:
        result, _ = self._perform("SAFE TO IGNORE.")
        self.assertFalse(
            result.release,
            "an unrecognized token must refuse; the nearest existing agent-verdict reader FAILS OPEN "
            "(oc_runipd's verifier read defaults to 'verified'), and F-13 forbids copying it",
        )
        self.assertTrue(result.record["violation"])

    def test_the_RETRY_loop_is_BOUNDED(self) -> None:
        """Neither loop may be unbounded: each iteration costs a paid model turn."""

        runs: list[int] = []

        def _always_red():
            runs.append(1)
            return _suite_result(passing=False, exit_code=1)

        result, prompts = self._perform(
            R.GATE_ANSWER_FIXED, rerun=_always_red, budget=2
        )
        self.assertLessEqual(len(runs), 2, "re-runs must not exceed the retry budget")
        self.assertLessEqual(len(prompts), 3)
        self.assertFalse(result.release, "exhaustion must refuse, never integrate")

    def test_a_ZERO_budget_never_verifies_and_therefore_refuses(self) -> None:
        result, _ = self._perform(R.GATE_ANSWER_FIXED, rerun=None, budget=0)
        self.assertFalse(result.release)

    def test_every_adjudication_is_recorded_with_the_ids_it_was_SHOWN(self) -> None:
        """daexj1 E-07: a release over a red suite must be auditable afterwards."""

        result, _ = self._perform(R.GATE_ANSWER_NOT_MINE, reason="unrelated flake")
        record = result.record
        for key in (
            "answer",
            "reason",
            "failing_tests",
            "session_id",
            "recheck_attempts",
            "signal",
        ):
            self.assertIn(key, record, f"{key} must be recorded for a later reviewer")
        self.assertTrue(
            record["failing_tests"],
            "the ids the agent was SHOWN must be recorded, or a reviewer cannot check the answer "
            "against the failures it was given",
        )
        self.assertEqual(record["session_id"], "session-under-test")


class TheSuiteRunsWhereTheMergedCodeActuallyIs(unittest.TestCase):
    """daexj1 E-03/E-04: the revalidation stub is gone and the gate can now say NO.

    THE PROPERTY THAT MATTERS, and it is the one the previous constant-True runner could not have: the
    suite must run against a tree that CONTAINS the work being integrated. It is not enough to assert
    "a suite ran". `isolate_worktree` defaults TRUE, so the lane's commits are NOT in main when the gate
    asks its question, and `execute_merge_and_revalidate_gate` is DIFF-BASED, so no merged tree exists on
    disk either. Every case below therefore checks WHICH tree was measured, not merely that something was.
    """

    def _repo_with_a_lane(self, root: pathlib.Path):
        """A real git repo on `main` plus a lane branch adding `lane_work.py`. Returns (repo, base)."""

        import subprocess

        repo = root / "repo"
        repo.mkdir()

        def git(*args: str) -> str:
            proc = subprocess.run(
                ["git", *args], cwd=repo, capture_output=True, text=True
            )
            self.assertEqual(proc.returncode, 0, f"{args}: {proc.stderr}")
            return proc.stdout.strip()

        git("init", "-q", "-b", "main")
        git("config", "user.email", "t@example.invalid")
        git("config", "user.name", "t")
        (repo / "base_file.py").write_text("BASE = 1\n", encoding="utf-8")
        git("add", "base_file.py")
        git("commit", "-qm", "base")
        base = git("rev-parse", "HEAD")
        git("checkout", "-q", "-b", "aw/lane/xx1111")
        (repo / "lane_work.py").write_text("LANE = 2\n", encoding="utf-8")
        git("add", "lane_work.py")
        git("commit", "-qm", "the lane's work")
        git("checkout", "-q", "main")
        self.assertFalse(
            (repo / "lane_work.py").exists(),
            "the fixture must reproduce the real shape: the lane's work is NOT in main",
        )
        return repo, base

    def _item(self, base: str) -> dict[str, object]:
        return {
            "id6": "xx1111",
            "preserved_base": base,
            "preserved_branch": "aw/lane/xx1111",
        }

    def test_the_suite_measures_a_tree_CONTAINING_the_lane_work(self) -> None:
        """THE E-03 assertion. Main does not contain the work; the measured tree must."""

        observed: dict[str, object] = {}

        def _spy_suite(path, _run_id):
            tree = pathlib.Path(path)
            observed["path"] = tree
            observed["has_lane_work"] = (tree / "lane_work.py").exists()
            observed["has_base"] = (tree / "base_file.py").exists()
            return _suite_result(
                passing=True, exit_code=0, summary="green", failures=()
            )

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base = self._repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = self._item(base)
            runner = R.make_integration_validation_runner(
                {
                    "repo": str(repo),
                    "run_id": "run-under-test",
                    "options": {"validate": False},
                },
                run_dir,
                item,
                suite_check=_spy_suite,
            )
            verdict = runner("a diff", ("lane_work.py",))

            self.assertTrue(verdict)
            self.assertTrue(
                observed.get("has_lane_work"),
                "the revalidation must measure a tree containing the lane's work; measuring the "
                "primary checkout proves only that a tree WITHOUT the work is green, which is the "
                "measurement mismatch this item exists to fix",
            )
            self.assertTrue(
                observed.get("has_base"), "the merge result must also carry the base"
            )
            measured = observed.get("path")
            assert isinstance(measured, pathlib.Path)
            self.assertFalse(
                measured.exists(),
                "the ephemeral worktree must be cleaned up after the run",
            )

    def test_a_COMBINED_RED_suite_makes_the_runner_REFUSE(self) -> None:
        """The gate must be ABLE to say no; the previous runner structurally could not."""

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base = self._repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = self._item(base)
            runner = R.make_integration_validation_runner(
                {
                    "repo": str(repo),
                    "run_id": "r",
                    "options": {"validate": False},
                },
                run_dir,
                item,
                suite_check=lambda *_a: _suite_result(
                    passing=False, exit_code=1, reason="combined RED"
                ),
            )
            self.assertFalse(runner("a diff", ("lane_work.py",)))
            record = _revalidation(item)
            self.assertFalse(record["passed"])
            self.assertIn("RED", record["reason"])
            self.assertTrue(
                record["tree"], "the record must name WHICH tree was measured"
            )

    def test_the_suite_runs_ONCE_per_distinct_merge_result(self) -> None:
        """daexj1 E-04, asserted as a COUNT rather than an assertion about intent."""

        calls: list[str] = []

        def _counting(path, _run_id):
            calls.append(str(path))
            return _suite_result(passing=True, exit_code=0, failures=())

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base = self._repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            state = {
                "repo": str(repo),
                "run_id": "r",
                "options": {"validate": False},
            }
            first, second = self._item(base), self._item(base)
            R.make_integration_validation_runner(
                state, run_dir, first, suite_check=_counting
            )("d", ("lane_work.py",))
            R.make_integration_validation_runner(
                state, run_dir, second, suite_check=_counting
            )("d", ("lane_work.py",))

            self.assertEqual(
                len(calls),
                1,
                "the same merge result must be measured ONCE; re-running the suite per lane over an "
                "identical tree pays the cost twice for one fact",
            )
            self.assertFalse(_revalidation(first)["cached"])
            self.assertTrue(_revalidation(second)["cached"])
            self.assertEqual(
                _revalidation(first)["tree"],
                _revalidation(second)["tree"],
                "the cache key must be the merged TREE id, which is the identity of the thing tested",
            )

    def test_a_DIFFERENT_merge_result_is_measured_SEPARATELY(self) -> None:
        """The cache must not answer for a tree it never measured."""

        import subprocess

        calls: list[str] = []

        def _counting(path, _run_id):
            calls.append(str(path))
            return _suite_result(passing=True, exit_code=0, failures=())

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base = self._repo_with_a_lane(root)
            subprocess.run(
                ["git", "checkout", "-q", "-b", "aw/lane/yy2222", base],
                cwd=repo,
                check=True,
            )
            (repo / "other_work.py").write_text("OTHER = 3\n", encoding="utf-8")
            subprocess.run(["git", "add", "other_work.py"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "different work"], cwd=repo, check=True
            )
            subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)

            run_dir = root / "run"
            run_dir.mkdir()
            state = {
                "repo": str(repo),
                "run_id": "r",
                "options": {"validate": False},
            }
            R.make_integration_validation_runner(
                state, run_dir, self._item(base), suite_check=_counting
            )("d", ("lane_work.py",))
            other: dict[str, object] = {
                "id6": "yy2222",
                "preserved_base": base,
                "preserved_branch": "aw/lane/yy2222",
            }
            R.make_integration_validation_runner(
                state, run_dir, other, suite_check=_counting
            )("d", ("other_work.py",))
            self.assertEqual(
                len(calls),
                2,
                "two distinct merge results are two distinct measurements",
            )

    def test_NO_suite_checker_FAILS_CLOSED_rather_than_passing(self) -> None:
        """The exact regression that would restore the inert gate. `None` must never mean yes."""

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            run_dir = root / "run"
            run_dir.mkdir()
            item: dict[str, object] = {"id6": "xx1111"}
            self.assertFalse(
                R.make_integration_validation_runner(
                    {"options": {"validate": False}}, run_dir, item
                )("d", ()),
                "with no checker the runner must refuse; a True here is a way to land an "
                "unvalidated lane while reporting a green gate",
            )
            self.assertIn("fail-closed", _revalidation(item)["reason"])

    def test_an_UNRESOLVABLE_lane_fails_closed_and_says_why(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            run_dir = root / "run"
            run_dir.mkdir()
            item: dict[str, object] = {
                "id6": "xx1111",
                "preserved_base": "",
                "preserved_branch": "",
            }
            self.assertFalse(
                R.make_integration_validation_runner(
                    {"repo": str(root), "options": {"validate": False}},
                    run_dir,
                    item,
                    suite_check=lambda *_a: _suite_result(passing=True, exit_code=0),
                )("d", ())
            )
            self.assertIn("could not be resolved", _revalidation(item)["reason"])

    def test_a_FIRST_ATTEMPT_item_resolves_its_lane_from_the_LIVE_attempt(self) -> None:
        """`l2mzxn`: the shape the gate ACTUALLY sees mid-run must resolve, and used not to.

        WHY THIS CASE EXISTS AND THE SIBLINGS ABOVE DID NOT CATCH IT. Every other case in this class
        hand-populates `preserved_base`/`preserved_branch` on the item (`_item`). Those fields are written
        by `lane_containment.record_preserved_lane_state` on the POST-turn PRESERVATION path, which runs
        AFTER integration and only when the item did NOT reach `executed`. So the fixtures describe a
        state that CANNOT exist when the gate asks its question, and the first-attempt shape - the only
        shape a live run actually presents - went unexercised.

        MEASURED CONSEQUENCE (2026-09-21, run `run-20260921T105933Z-1994623`): items `i1hlgx`, `k9awrq`
        and `quqyc4` each finished a full successful agent turn and were then refused `merge-conflict`
        with `base=False, head=False` recorded and the suite invoked ZERO times. No git conflict existed
        (`git merge-tree --write-tree` exited 0 for all three) and the merged tree was green
        (`7991 passed`). With `--validate` off (the DEFAULT) this refused every isolated first-attempt
        item, so the gate was inverted: it could only say no.

        THIS TEST IS FALSIFIABLE and was PROVEN so: against the pre-fix resolution it fails with the
        `base=False, head=False` refusal and `calls == 0`.
        """

        calls: list[pathlib.Path] = []

        def _spy(path, _run_id):
            calls.append(pathlib.Path(path))
            return _suite_result(passing=True, exit_code=0, summary="green")

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base = self._repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            # EXACTLY the call-site shape: the attempt carries the lane, the item carries no
            # `preserved_*` field, because nothing has preserved anything yet.
            item: dict[str, object] = {
                "id6": "xx1111",
                "attempts": [
                    {
                        "worktree_base": base,
                        "worktree_branch": "aw/lane/xx1111",
                    }
                ],
            }
            verdict = R.make_integration_validation_runner(
                {
                    "repo": str(repo),
                    "run_id": "r",
                    "options": {"validate": False},
                },
                run_dir,
                item,
                suite_check=_spy,
            )("a diff", ("lane_work.py",))

            self.assertTrue(
                verdict,
                "a first-attempt item whose attempt names its lane must be resolvable; refusing it "
                "makes the gate reject every isolated item in the DEFAULT configuration",
            )
            self.assertEqual(
                len(calls),
                1,
                "the suite must actually RUN; the measured defect was a refusal reached with the "
                "suite invoked zero times, so a verdict alone does not prove the fix",
            )
            self.assertNotIn("could not be resolved", _revalidation(item)["reason"])

    def test_the_lane_resolver_prefers_the_attempt_and_falls_back_to_preserved(
        self,
    ) -> None:
        """Both readers are live, and the PRECEDENCE is the point.

        The attempt is authoritative because it exists DURING the turn, which is when the gate asks. The
        `preserved_*` fields remain the fallback for a LATER caller (`aw <host> integrate <id6>`, the
        deferral ladder) reading an item whose lane was preserved after the fact. Asserting the order
        stops a future edit from 'simplifying' back to the preserved-only read that caused `l2mzxn`.
        """

        self.assertEqual(
            R.resolve_lane_endpoints(
                {
                    "attempts": [{"worktree_base": "aaa", "worktree_branch": "br/a"}],
                    "preserved_base": "bbb",
                    "preserved_branch": "br/b",
                }
            ),
            ("aaa", "br/a", ""),
            "the LIVE attempt must win over the post-turn preservation fields",
        )
        self.assertEqual(
            R.resolve_lane_endpoints(
                {"preserved_base": "bbb", "preserved_branch": "br/b"}
            ),
            ("bbb", "br/b", ""),
            "with no attempt the preserved fields must still answer",
        )
        self.assertEqual(
            R.resolve_lane_endpoints({"id6": "xx1111"}),
            ("", "", ""),
            "an item naming no lane at all must resolve to nothing, so the caller fails closed",
        )
        self.assertEqual(
            R.resolve_lane_endpoints(
                {
                    "attempts": [
                        {"worktree_base": "old", "worktree_branch": "br/old"},
                        {"worktree_base": "new", "worktree_branch": "br/new"},
                    ]
                }
            ),
            ("new", "br/new", ""),
            "the LATEST attempt that names a lane is the current one",
        )

    def test_an_EXCEPTION_from_the_suite_refuses_instead_of_aborting_the_run(
        self,
    ) -> None:
        """A crash mid-integration must preserve the lane, not raise through the driver."""

        def _explodes(*_a):
            raise RuntimeError("the suite process died")

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base = self._repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = self._item(base)
            self.assertFalse(
                R.make_integration_validation_runner(
                    {
                        "repo": str(repo),
                        "run_id": "r",
                        "options": {"validate": False},
                    },
                    run_dir,
                    item,
                    suite_check=_explodes,
                )("d", ())
            )
            self.assertIn("errored", _revalidation(item)["reason"])

    def test_materializing_a_CONFLICTING_merge_returns_None_and_not_a_guess(
        self,
    ) -> None:
        """Three-valued, exactly as `merge_write_set` already is: unknown is not empty and not a pass."""

        import subprocess

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = root / "repo"
            repo.mkdir()

            def git(*args: str):
                return subprocess.run(
                    ["git", *args], cwd=repo, capture_output=True, text=True
                )

            git("init", "-q", "-b", "main")
            git("config", "user.email", "t@example.invalid")
            git("config", "user.name", "t")
            (repo / "c.py").write_text("ORIGINAL\n", encoding="utf-8")
            git("add", "c.py")
            git("commit", "-qm", "base")
            base = git("rev-parse", "HEAD").stdout.strip()
            git("checkout", "-q", "-b", "lane")
            (repo / "c.py").write_text("LANE VERSION\n", encoding="utf-8")
            git("add", "c.py")
            git("commit", "-qm", "lane")
            head = git("rev-parse", "HEAD").stdout.strip()
            git("checkout", "-q", "main")
            (repo / "c.py").write_text("MAIN VERSION\n", encoding="utf-8")
            git("add", "c.py")
            git("commit", "-qm", "main diverges")
            main_head = git("rev-parse", "HEAD").stdout.strip()

            path, _tree, reason = R.materialize_merge_result(
                repo, main_head, head, work_root=root / "wt"
            )
            self.assertIsNone(
                path, "a conflicting merge must not be materialized as a guess"
            )
            self.assertTrue(reason, "the unknown must be explained")
            # And the real merge base still works, proving the fixture is a genuine conflict rather
            # than a broken invocation.
            ok_path, ok_tree, _ = R.materialize_merge_result(
                repo, base, head, work_root=root / "wt2"
            )
            self.assertIsNotNone(ok_path)
            self.assertTrue(ok_tree)
            if ok_path is not None:
                R.release_merge_result(repo, ok_path)

    def test_materializing_creates_NO_branch_and_moves_NO_ref(self) -> None:
        """This runs in a SHARED checkout, so it must not touch main, the lane, or any index."""

        import subprocess

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base = self._repo_with_a_lane(root)

            def refs():
                return subprocess.run(
                    ["git", "show-ref"], cwd=repo, capture_output=True, text=True
                ).stdout

            before_refs = refs()
            before_head = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True
            ).stdout
            before_status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo,
                capture_output=True,
                text=True,
            ).stdout

            head = subprocess.run(
                ["git", "rev-parse", "aw/lane/xx1111"],
                cwd=repo,
                capture_output=True,
                text=True,
            ).stdout.strip()
            path, _tree, _why = R.materialize_merge_result(
                repo, base, head, work_root=root / "wt"
            )
            self.assertIsNotNone(path)
            assert path is not None
            self.assertTrue((path / "lane_work.py").exists())
            R.release_merge_result(repo, path)

            self.assertEqual(before_refs, refs(), "no ref may be created or moved")
            self.assertEqual(
                before_head,
                subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                ).stdout,
                "HEAD must not move",
            )
            self.assertEqual(
                before_status,
                subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                ).stdout,
                "the working tree must be untouched; another agent may be working here",
            )

    def test_VALIDATION_ON_does_NOT_get_a_second_gate(self) -> None:
        """`integration_is_earned`'s two modes are ALTERNATIVES, and revalidation must not merge them.

        With `--validate` ON the VERIFIER's verdict is the trust signal, and that predicate deliberately
        refuses to let a green suite override a decline. A post-merge suite run that could REFUSE a
        verifier-earned integration would make `--validate` stricter than the mode it is an alternative
        to, which is a second gate the operator never asked for. MEASURED when this was first written
        without the distinction: 14 tests went red across three files, every one a validate-ON path.
        """

        ran: list[str] = []

        def _should_not_run(path, _run_id):
            ran.append(str(path))
            return _suite_result(passing=False, exit_code=1)

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base = self._repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            for opts in (
                {"validate": True},
                {"no_audit": False},  # validate is DERIVED true from this
                {"no_verify": False},
            ):
                with self.subTest(options=opts):
                    item = self._item(base)
                    verdict = R.make_integration_validation_runner(
                        {"repo": str(repo), "run_id": "r", "options": opts},
                        run_dir,
                        item,
                        suite_check=_should_not_run,
                    )("d", ("lane_work.py",))
                    self.assertTrue(
                        verdict,
                        "a verifier-earned integration must not be refused by a second signal",
                    )
                    self.assertTrue(
                        _revalidation(item)["skipped"],
                        "the record must say it was NOT measured rather than implying a suite ran",
                    )
            self.assertEqual(
                ran, [], "no suite may be run for a verifier-governed integration"
            )

    def test_VALIDATION_OFF_is_the_mode_that_DOES_revalidate(self) -> None:
        """The complement of the case above, so the distinction is pinned in both directions."""

        ran: list[str] = []

        def _counting(path, _run_id):
            ran.append(str(path))
            return _suite_result(passing=True, exit_code=0, failures=())

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base = self._repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = self._item(base)
            self.assertTrue(
                R.make_integration_validation_runner(
                    {
                        "repo": str(repo),
                        "run_id": "r",
                        "options": {"validate": False},
                    },
                    run_dir,
                    item,
                    suite_check=_counting,
                )("d", ("lane_work.py",))
            )
            self.assertEqual(len(ran), 1, "the suite-earned mode MUST revalidate")
            self.assertFalse(_revalidation(item)["skipped"])

    def test_the_mode_is_resolved_IDENTICALLY_to_the_dispatch_seam(self) -> None:
        """The two-mode resolution must not FORK from `execute_item_core`'s.

        This is the F-4-shaped hazard in this change: the modes are resolved in two places, and the two
        hosts freeze OPPOSITE-POLARITY keys (`oc_runipd.py:3477-3478` writes `validate` AND `no_audit`;
        `agy_runipd.py:2190` writes ONLY `no_verify`), so a resolution that handled one host's shape and
        not the other's would silently skip revalidation on that host. Pinned over the REAL frozen shapes
        rather than over invented ones, and asserted against the dispatch seam's own source so the two
        cannot drift apart unnoticed.
        """

        real_shapes = [
            ({"validate": True, "no_audit": False}, True),  # oc, verifier on
            ({"validate": False, "no_audit": True}, False),  # oc, shipped default
            ({"no_verify": False}, True),  # agy, verifier on
            ({"no_verify": True}, False),  # agy, --no-verify
            ({}, True),  # legacy record with neither key
        ]
        for opts, expected_validate in real_shapes:
            with self.subTest(options=opts):
                validate = opts.get("validate", False)
                if "validate" not in opts:
                    validate = not (opts.get("no_verify") or opts.get("no_audit"))
                self.assertEqual(
                    validate,
                    expected_validate,
                    f"{opts} must resolve to validate={expected_validate}",
                )

        # AND the runner must AGREE with that resolution, observed by whether a suite runs.
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base = self._repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            for opts, expected_validate in real_shapes:
                with self.subTest(options=opts, phase="runner"):
                    ran: list[str] = []

                    def _counting(path, _run_id, _ran=ran):
                        _ran.append(str(path))
                        return _suite_result(passing=True, exit_code=0, failures=())

                    item = self._item(base)
                    R.make_integration_validation_runner(
                        {"repo": str(repo), "run_id": "r", "options": opts},
                        run_dir,
                        item,
                        suite_check=_counting,
                    )("d", ("lane_work.py",))
                    self.assertEqual(
                        ran == [],
                        expected_validate,
                        f"with options {opts} the suite should "
                        f"{'NOT run' if expected_validate else 'RUN'}",
                    )

        # The dispatch seam still resolves it the same way, read from its own source.
        seam = inspect_source(R.execute_item_core)
        self.assertIn('validate = opts.get("validate", False)', seam)
        self.assertIn(
            'validate = not (opts.get("no_verify") or opts.get("no_audit"))',
            seam,
            "if the dispatch seam's resolution changes, this runner's copy must change with it",
        )

    def test_NO_TESTS_COLLECTED_is_not_read_as_a_broken_merge(self) -> None:
        """pytest exit 5 means "nothing to run", and a tree with no tests cannot have been broken.

        Narrow on purpose: only 5. A real failure (1), a timeout (124) and a spawn failure (127) must all
        keep refusing, because each of those IS a reason to doubt the merge.
        """

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base = self._repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()

            item = self._item(base)
            self.assertTrue(
                R.make_integration_validation_runner(
                    {"repo": str(repo), "run_id": "r", "options": {"validate": False}},
                    run_dir,
                    item,
                    suite_check=lambda *_a: _suite_result(
                        passing=False, exit_code=5, summary="", reason="no tests ran"
                    ),
                )("d", ()),
                "exit 5 must not be read as 'the merge broke the tree'",
            )
            self.assertIn("collected NO tests", _revalidation(item)["reason"])

            for code in (1, 124, 127):
                with self.subTest(exit_code=code):
                    other = self._item(base)
                    self.assertFalse(
                        R.make_integration_validation_runner(
                            {
                                "repo": str(repo),
                                "run_id": "r",
                                "options": {"validate": False},
                            },
                            run_dir,
                            other,
                            suite_check=lambda *_a, _c=code: _suite_result(
                                passing=False, exit_code=_c
                            ),
                        )("d", ()),
                        f"exit {code} is a real reason to doubt the merge and must refuse",
                    )

    def test_BOTH_hosts_pass_their_own_suite_checker_to_the_factory(self) -> None:
        """E-03 on both hosts, asserted over the AST so a host cannot silently keep the old shape."""

        for module in (OC, AGY):
            with self.subTest(host=module.__name__):
                tree = ast.parse(
                    pathlib.Path(str(module.__file__)).read_text(encoding="utf-8")
                )
                calls = [
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "make_integration_validation_runner"
                ]
                self.assertTrue(calls, f"{module.__name__} must build the runner")
                for call in calls:
                    kwargs = {kw.arg for kw in call.keywords}
                    self.assertIn(
                        "suite_check",
                        kwargs,
                        f"{module.__name__} builds the validation runner without injecting "
                        f"suite_check, so its integration gate would fail closed on every lane",
                    )


class BothHostsShareEveryAdjudicationSymbol(unittest.TestCase):
    """Case 6 / daexj1 E-09: proven by OBJECT IDENTITY, never by grep.

    A second copy of a verdict parser is exactly how the two hosts drift on what counts as a verdict.
    """

    ADJUDICATION_SYMBOLS = (
        "gate_answer_is_warranted",
        "perform_gate_answer",
        "validate_gate_answer",
        "gate_answer_question",
        "gate_answer_record",
        "integration_is_earned",
        "run_suite_check",
        "make_integration_validation_runner",
        "SuiteCheckResult",
    )

    def test_both_hosts_resolve_the_SAME_objects(self) -> None:
        for name in self.ADJUDICATION_SYMBOLS:
            with self.subTest(symbol=name):
                oc_obj = getattr(OC, name, None)
                agy_obj = getattr(AGY, name, None)
                if oc_obj is None and agy_obj is None:
                    # Lives only in the shared module; then BOTH must reach it there.
                    self.assertTrue(
                        hasattr(R, name),
                        f"{name} must exist somewhere both hosts can reach",
                    )
                    continue
                self.assertIsNotNone(oc_obj, f"oc must expose {name}")
                self.assertIsNotNone(agy_obj, f"agy must expose {name}")
                self.assertIs(
                    oc_obj,
                    agy_obj,
                    f"{name} must be ONE object on both hosts; two copies of a verdict parser is "
                    f"how the hosts drift on what counts as a verdict",
                )

    def test_the_adjudication_logic_lives_in_the_SHARED_module(self) -> None:
        for name in (
            "gate_answer_is_warranted",
            "perform_gate_answer",
            "validate_gate_answer",
            "gate_answer_question",
            "make_integration_validation_runner",
        ):
            with self.subTest(symbol=name):
                obj = getattr(R, name)
                self.assertEqual(
                    getattr(obj, "__module__", ""),
                    "agent_workflows.runner_shared",
                    f"{name} must be OWNED by runner_shared, not by a host driver",
                )

    def test_agy_gained_NO_new_direct_import_of_the_adjudication_seam(self) -> None:
        """agy must reach shared behavior through `runner_shared`, never by importing `oc_runipd`.

        Scoped to the symbols THIS plan is about. agy legitimately imports many names from oc for
        historical reasons, and asserting "zero oc imports" would fail for reasons unrelated to this
        change.
        """

        tree = ast.parse(pathlib.Path(str(AGY.__file__)).read_text(encoding="utf-8"))
        from_oc: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").endswith(
                "oc_runipd"
            ):
                from_oc.update(alias.name for alias in node.names)
        for name in (
            "gate_answer_is_warranted",
            "perform_gate_answer",
            "validate_gate_answer",
            "gate_answer_question",
            "gate_answer_record",
        ):
            self.assertNotIn(
                name,
                from_oc,
                f"agy must not import {name} from oc_runipd; the shared owner is runner_shared",
            )

    def test_the_shared_module_imports_NO_host_driver(self) -> None:
        """The existing anti-divergence rule, re-asserted here because this plan adds to that module."""

        tree = ast.parse(pathlib.Path(str(R.__file__)).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn(
                    "runipd",
                    (node.module or ""),
                    "runner_shared must never import a host driver; host specifics are INJECTED",
                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("runipd", alias.name)


def inspect_source(obj) -> str:
    """`inspect.getsource` without importing `inspect` at module scope for one call."""

    import inspect as _inspect

    return _inspect.getsource(obj)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
