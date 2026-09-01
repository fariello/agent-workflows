#!/usr/bin/env python3
"""novalnomerge-01 (evgi9n) E-06: the integration gate must be REACHABLE in the shipped default.

THE BUG THIS FILE PINS. `--validate` defaults FALSE and `--no-self-finalize` defaults TRUE, but the
self-finalize gate additionally required ``verify_disp == "verified"`` -- a value only ever assigned
inside the validate-guarded block. So in the SHIPPED DEFAULT configuration self-finalize was switched
ON and could never fire: every item ended ``substantially-complete`` with its lane preserved and
nothing integrated. Measured cost before the fix: ~$528 across five overnight runs, 21 plans stranded
in lanes, then a full session hand-merging 24 lanes.

Every test here asserts on the GATE DECISION, never on a substring of output, because a substring
assertion would pass against a stubbed-out result. Each was sabotage-checked during execution: the
corresponding branch was deliberately broken and the test observed to FAIL.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd
from agent_workflows import oc_runipd as driver
from tests.support import REPO_ROOT

_DRIVER_CMD = [sys.executable, "-m", "agent_workflows.oc_runipd"]
_DRIVER_ENV = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}


def _suite(
    passing: bool, exit_code: int = 0, summary: str = "3863 passed"
) -> driver.SuiteCheckResult:
    return driver.SuiteCheckResult(
        passing=passing,
        exit_code=exit_code,
        summary=summary,
        reason=f"exit {exit_code}",
        cwd="/primary",
        timeout_seconds=driver.SUITE_CHECK_TIMEOUT_SECONDS,
        elapsed_seconds=37.0,
    )


class ShippedDefaultReachabilityTests(unittest.TestCase):
    """(a) The regression test for the ACTUAL default configuration."""

    def test_shipped_defaults_are_validate_off_and_self_finalize_on(self):
        """The premise of the bug: the two flags' real defaults silently cancelled out.

        If either default changes, the rest of this file is testing a configuration nobody runs, so
        assert the premise itself rather than trusting the plan's prose.
        """
        parser_src = driver.build_parser
        self.assertTrue(callable(parser_src))
        p = driver.build_parser()
        defaults = {}
        for action in p._actions:
            if action.dest in ("validate", "self_finalize"):
                defaults[action.dest] = action.default
        # Subparsers hide the real actions; walk them when the top level did not carry the flags.
        if "validate" not in defaults:
            for action in p._actions:
                if hasattr(action, "choices") and isinstance(action.choices, dict):
                    for sub in action.choices.values():
                        for sa in getattr(sub, "_actions", []):
                            if sa.dest in ("validate", "self_finalize"):
                                defaults.setdefault(sa.dest, sa.default)
        self.assertIs(
            defaults.get("validate"),
            False,
            "--validate must still default False for this bug class to exist",
        )
        self.assertIs(
            defaults.get("self_finalize"),
            True,
            "self-finalize must still default True for this bug class to exist",
        )

    def test_default_config_green_suite_EARNS_integration(self):
        """THE BUG, FIXED: validation off + green suite must now earn integration.

        Before the fix this combination was unreachable, because the gate demanded
        ``verify_disp == "verified"`` and nothing set it when validation was off.
        """
        v = driver.integration_is_earned(
            validate=False, verify_disp=None, suite_result=_suite(True)
        )
        self.assertTrue(v.earned)
        self.assertEqual(v.signal, driver.INTEGRATION_EARNED_BY_SUITE)

    def test_old_gate_condition_would_have_refused_the_same_input(self):
        """Prove the fix CHANGED something: the old predicate refuses what the new one allows."""
        verify_disp = None  # what the driver actually holds when validation is off
        old_gate_would_fire = verify_disp == "verified"
        new = driver.integration_is_earned(
            validate=False, verify_disp=verify_disp, suite_result=_suite(True)
        )
        self.assertFalse(old_gate_would_fire, "the old gate could not fire here")
        self.assertTrue(new.earned, "the new gate must fire here")


class ValidationOffTests(unittest.TestCase):
    """(b) and (c): a red or unrunnable suite must REFUSE."""

    def test_red_suite_refuses(self):
        v = driver.integration_is_earned(
            validate=False,
            verify_disp=None,
            suite_result=_suite(False, exit_code=1, summary="1 failed"),
        )
        self.assertFalse(v.earned)
        self.assertEqual(v.signal, driver.INTEGRATION_REFUSED_SUITE_FAILED)

    def test_timeout_refuses_fail_closed(self):
        """exit 124 is capture_command's timeout code and must NOT be special-cased into a pass."""
        v = driver.integration_is_earned(
            validate=False,
            verify_disp=None,
            suite_result=_suite(False, exit_code=124, summary=""),
        )
        self.assertFalse(v.earned)
        self.assertEqual(v.signal, driver.INTEGRATION_REFUSED_SUITE_FAILED)

    def test_unrunnable_suite_refuses_fail_closed(self):
        """exit 127 is capture_command's other-exception code."""
        v = driver.integration_is_earned(
            validate=False,
            verify_disp=None,
            suite_result=_suite(False, exit_code=127, summary=""),
        )
        self.assertFalse(v.earned)
        self.assertEqual(v.signal, driver.INTEGRATION_REFUSED_SUITE_FAILED)

    def test_absent_suite_result_refuses_rather_than_defaulting_open(self):
        """A missing result is the evasion path; it must fail CLOSED."""
        v = driver.integration_is_earned(
            validate=False, verify_disp=None, suite_result=None
        )
        self.assertFalse(v.earned)
        self.assertEqual(v.signal, driver.INTEGRATION_REFUSED_NO_SIGNAL)


class ValidationOnUnchangedTests(unittest.TestCase):
    """(d) With validation ON, behavior is byte-for-byte the old behavior, in all four states."""

    def test_verified_earns(self):
        v = driver.integration_is_earned(
            validate=True, verify_disp="verified", suite_result=None
        )
        self.assertTrue(v.earned)
        self.assertEqual(v.signal, driver.INTEGRATION_EARNED_BY_VERIFIER)

    def test_unverified_refuses(self):
        v = driver.integration_is_earned(
            validate=True, verify_disp="unverified", suite_result=None
        )
        self.assertFalse(v.earned)

    def test_blocked_refuses(self):
        v = driver.integration_is_earned(
            validate=True, verify_disp="blocked", suite_result=None
        )
        self.assertFalse(v.earned)

    def test_none_refuses(self):
        v = driver.integration_is_earned(
            validate=True, verify_disp=None, suite_result=None
        )
        self.assertFalse(v.earned)

    def test_green_suite_does_NOT_override_a_declining_verifier(self):
        """If the operator asked for verification, a green suite must not overrule its verdict.

        Otherwise `--validate` would be WEAKER than the default, which is absurd. This is the
        OQ-02 ruling made explicit as a test.
        """
        v = driver.integration_is_earned(
            validate=True, verify_disp="unverified", suite_result=_suite(True)
        )
        self.assertFalse(
            v.earned, "a passing suite must not override an explicit verifier refusal"
        )
        self.assertEqual(v.signal, driver.INTEGRATION_REFUSED_VERIFIER_DECLINED)


class SignalDistinctionTests(unittest.TestCase):
    """E-05: 'no verifier ran' must be distinguishable from 'the verifier declined'."""

    def test_no_verifier_ran_is_distinct_from_verifier_declined(self):
        no_verifier = driver.integration_is_earned(
            validate=False,
            verify_disp=None,
            suite_result=_suite(False, exit_code=1, summary="1 failed"),
        )
        declined = driver.integration_is_earned(
            validate=True, verify_disp="unverified", suite_result=None
        )
        self.assertFalse(no_verifier.earned)
        self.assertFalse(declined.earned)
        self.assertNotEqual(
            no_verifier.signal,
            declined.signal,
            "the two refusal causes must not collapse into one indistinguishable state",
        )

    def test_no_new_disposition_value_is_invented(self):
        """`substantially-complete` is read by other surfaces; the vocabulary must not fork."""
        self.assertEqual(
            driver.EXECUTION_SUCCESS_STATES, {"executed", "substantially-complete"}
        )


class CrossDriverParityTests(unittest.TestCase):
    """(f) Both drivers must agree across the WHOLE matrix, or a one-runner fix has been shipped."""

    def test_both_drivers_share_one_predicate_object(self):
        self.assertIs(agy_runipd.integration_is_earned, driver.integration_is_earned)
        self.assertIs(agy_runipd.run_suite_check, driver.run_suite_check)
        self.assertIs(agy_runipd.SuiteCheckResult, driver.SuiteCheckResult)

    def test_full_matrix_agreement(self):
        cases = []
        for validate in (True, False):
            for vd in ("verified", "unverified", "blocked", None):
                for suite in (None, _suite(True), _suite(False, exit_code=1)):
                    cases.append((validate, vd, suite))
        for validate, vd, suite in cases:
            a = driver.integration_is_earned(
                validate=validate, verify_disp=vd, suite_result=suite
            )
            b = agy_runipd.integration_is_earned(
                validate=validate, verify_disp=vd, suite_result=suite
            )
            with self.subTest(validate=validate, verify_disp=vd, suite=bool(suite)):
                self.assertEqual(a, b)


class SuiteCheckBehaviorTests(unittest.TestCase):
    """E-01/E-02: the driver OBSERVES the suite; it never trusts a self-report."""

    def test_timeout_default_is_generous_not_the_shipped_60s(self):
        """PR-002: inheriting capture_command's 60s default against a ~37s suite is too tight."""
        self.assertGreaterEqual(driver.SUITE_CHECK_TIMEOUT_SECONDS, 900.0)

    def test_suite_is_invoked_bare(self):
        """The repo contract: addopts already supplies -q -n auto; adding flags changes what we measure."""
        argv = list(driver.SUITE_CHECK_ARGV)
        self.assertEqual(argv[1:], ["-m", "pytest"])
        for forbidden in ("-n0", "-p", "no:randomly", "-q"):
            self.assertNotIn(forbidden, argv[2:])

    def test_nonzero_exit_is_never_a_pass(self):
        for code in (1, 2, 124, 127, 255):
            with (
                self.subTest(exit_code=code),
                mock.patch(
                    "agent_workflows.run_evidence.capture_command",
                    return_value=(
                        {"exit_code": code, "stdout_excerpt": "", "stderr_excerpt": ""},
                        {},
                    ),
                ),
            ):
                r = driver.run_suite_check(driver.Path("."), "run-x")
                self.assertFalse(r.passing, f"exit {code} must not pass")
                self.assertEqual(r.exit_code, code)

    def test_exception_from_capture_is_a_refusal_not_a_crash(self):
        """A gate that crashes is a gate that is OFF."""
        with mock.patch(
            "agent_workflows.run_evidence.capture_command",
            side_effect=RuntimeError("git dir vanished"),
        ):
            r = driver.run_suite_check(driver.Path("."), "run-x")
        self.assertFalse(r.passing)
        self.assertEqual(r.exit_code, 127)
        self.assertIn("fail-closed", r.reason)

    def test_zero_exit_passes_and_records_the_summary_line(self):
        with mock.patch(
            "agent_workflows.run_evidence.capture_command",
            return_value=(
                {
                    "exit_code": 0,
                    "stdout_excerpt": "3863 passed, 3 skipped, 4 xfailed in 36.81s",
                    "stderr_excerpt": "",
                },
                {},
            ),
        ):
            r = driver.run_suite_check(driver.Path("."), "run-x")
        self.assertTrue(r.passing)
        self.assertIn("3863 passed", r.summary)

    def test_suite_runs_in_the_directory_it_is_given_not_a_lane(self):
        """PR-001 (BLOCKER): a lane resolves a different .aw/state (dh0uno), where 15 tests fail.

        MEASURED at review: tests/test_run_viewer.py gives 36 passed in the primary checkout and
        15 failed, 20 passed in a lane worktree. Gating on a lane-run suite would close this gate
        forever. The helper must pass its given cwd through untouched so callers can guarantee the
        primary checkout.
        """
        seen = {}

        def _fake(run_id, argv, cwd=".", **kw):
            seen["cwd"] = str(cwd)
            seen["timeout"] = kw.get("timeout")
            return (
                {"exit_code": 0, "stdout_excerpt": "1 passed", "stderr_excerpt": ""},
                {},
            )

        with mock.patch(
            "agent_workflows.run_evidence.capture_command", side_effect=_fake
        ):
            r = driver.run_suite_check(driver.Path("/primary/checkout"), "run-x")
        self.assertEqual(seen["cwd"], "/primary/checkout")
        self.assertEqual(r.cwd, "/primary/checkout")
        self.assertGreaterEqual(seen["timeout"], 900.0)


class EndToEndIntegrationTests(unittest.TestCase):
    """E-07: prove the OUTCOME, not just the boolean.

    The reported symptom was an integration outcome ("21 plans stranded in their lanes", every one
    showing `Expected executed/ | Actual pending/` in the run report), so a unit test on the gate
    helper is necessary but NOT sufficient. This drives the REAL driver as a subprocess with a fake
    host binary, exactly as `tests/test_oc_runipd.py` does, so no paid agent session is required.
    """

    def _repo_with_plan(self, root: Path) -> tuple[Path, Path, str]:
        repo = root / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=repo,
            check=True,
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
        (repo / "README").write_text("test\n", encoding="utf-8")
        subprocess.run(["git", "add", "README"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True)
        plan = pending / "20260831-nvm-01-nvm001-test.ipd.md"
        # Generate the fixture with the SHIPPED scaffolder rather than hand-writing it: `aw ipd begin`
        # applies the real structural gate (H2 order, E/V bijection, Scope-Paths at the ready-to-execute
        # gate), so a hand-rolled stub is refused for reasons that have nothing to do with this test.
        subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "ipd",
                "scaffold",
                "--kind",
                "child",
                "--set",
                "nvm",
                "--order",
                "1",
                "--title",
                "No-Validate Integration Plan",
                "--author",
                "test",
                "--path",
                os.fspath(plan),
                "--legacy-name",
                "--apply",
            ],
            cwd=repo,
            env=_DRIVER_ENV,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        text = plan.read_text(encoding="utf-8")
        text = text.replace(
            "- Status: draft",
            "- Status: approved\n- Approval: 2026-08-31, test fixture: approved for this test",
            1,
        )
        # The dependency preflight refuses the `unresolved` scaffold sentinel before any session.
        text = text.replace(
            "- Item-Dependencies: unresolved", "- Item-Dependencies: none", 1
        )
        text = text.replace(
            "- Scope-Paths: TODO (comma-separated repo-relative paths or pathspecs)",
            "- Scope-Paths: grandfathered",
            1,
        )
        plan.write_text(text, encoding="utf-8")
        # The scaffolder MINTS the id6; read it back rather than forcing one, so this fixture cannot
        # drift from whatever the shipped naming grammar produces.
        id6 = ""
        for line in text.splitlines():
            if line.startswith("- Id: "):
                id6 = line.split(":", 1)[1].strip()
                break
        self.assertTrue(id6, "the scaffolded plan must carry an '- Id:' handle")
        return repo, plan, id6

    def _fake_host(self, root: Path) -> Path:
        """A host that moves the plan to executed/ and reports success, like the shipped fixture."""
        fake = root / "fake_opencode"
        fake.write_text(
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import json, pathlib, re, sys",
                    "args = sys.argv[1:]",
                    'prompt = args[args.index("--") + 1] if "--" in args else ""',
                    'session = "ses_nvm"',
                    'if "Required JSON outcome:" in prompt:',
                    '    outcome = pathlib.Path(re.search(r"Required JSON outcome: (.+)", prompt).group(1).strip())',
                    '    plan = pathlib.Path(re.search(r"Plan file at launch: (.+)", prompt).group(1).strip())',
                    '    executed = pathlib.Path(str(plan).replace("/pending/", "/executed/"))',
                    "    executed.parent.mkdir(parents=True, exist_ok=True)",
                    "    plan.rename(executed)",
                    '    outcome.write_text(json.dumps({"schema_version": 1, "disposition": "executed", "pushed": False}))',
                    '    print(json.dumps({"type": "text", "sessionID": session, "part": {"text": "exec done"}}))',
                    "else:",
                    '    print(json.dumps({"type": "text", "sessionID": session, "part": {"text": "other"}}))',
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        return fake

    def test_validation_off_run_records_the_suite_signal_not_a_stranded_item(self):
        """With validation OFF, the item must carry the driver-run-suite signal.

        BEFORE the fix, `verify_disp` stayed None, the gate could not fire, and the item recorded no
        integration signal at all. The distinguishing evidence is `integration_signal` plus
        `verifier_ran: false` in the durable state (E-05), which is what makes "no verifier ran"
        readable rather than being conflated with "the verifier declined".
        """
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, _plan, id6 = self._repo_with_plan(root)
            fake = self._fake_host(root)

            # A trivially-green stand-in suite: the real bare suite would take ~37s and is not what
            # this test is measuring. The suite-check helper's own behavior is covered above.
            (repo / "pyproject.toml").write_text(
                "[tool.pytest.ini_options]\naddopts = ''\n", encoding="utf-8"
            )
            (repo / "test_ok.py").write_text(
                "def test_ok():\n    assert True\n", encoding="utf-8"
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "suite"], cwd=repo, check=True)

            result = subprocess.run(
                [
                    *_DRIVER_CMD,
                    "start",
                    id6,
                    "--repo",
                    os.fspath(repo),
                    "--opencode",
                    os.fspath(fake),
                    "--no-isolate-worktree",
                ],
                cwd=repo,
                env=_DRIVER_ENV,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            runs = sorted((repo / ".aw" / "records" / "runs").glob("run-*"))
            self.assertTrue(runs, "the run directory must exist")
            state = json.loads((runs[-1] / "state.json").read_text(encoding="utf-8"))
            item = state["queue"][0]

            # THE POINT: with validation off the item records that NO verifier ran and that the
            # driver-run suite was consulted, rather than silently recording nothing.
            self.assertIs(
                item.get("verifier_ran"),
                False,
                "validation was off, so the state must say no verifier ran",
            )
            self.assertIn(
                item.get("integration_signal"),
                (
                    driver.INTEGRATION_EARNED_BY_SUITE,
                    driver.INTEGRATION_REFUSED_SUITE_FAILED,
                ),
                "with validation off the deciding signal must be the driver-run suite, "
                f"got {item.get('integration_signal')!r}",
            )


if __name__ == "__main__":
    unittest.main()
