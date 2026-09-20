#!/usr/bin/env python3
"""wtiso Phase 0 (`8zgybk` E-06, E-07, E-08): the five ADVERSARIAL guards from research x03wgn
Section 7 / Section 8 Phase 0 item 4.

The Set is ABOUT untrustworthy agents (forgetful, bypassing, lying, or deadlocked), so a
green-path-only suite would be worthless. Each guard here models one such behavior.

THE MANDATORY TWO-FUNCTION SPLIT RULE. Every guard has two halves, and they MUST live in two
separate test functions:

  * `test_<guard>_<observable>_now`  - UNMARKED. Asserts the OBSERVABILITY fact that holds today:
    the raw evidence (git state, token format, timeout constant) from which a driver COULD detect
    the bad behavior. This must pass now and forever.
  * `test_<guard>_<driverguard>_pinned_absent` - `@pytest.mark.xfail(strict=True)`. Asserts the
    DRIVER GUARD that does not exist yet, naming the phase that builds it.

WHY THE SPLIT IS MANDATORY (verified experimentally, not assumed). pytest scores a whole function
as ONE outcome. Putting both halves in a single `xfail(strict=True)` function is a greenwash hole:

  1. the passing half becomes INVISIBLE (the run reports only `1 xfailed`), so a validation item
     demanding proof the observability assertion passed cannot be satisfied; and
  2. worse, if the observability half later REGRESSES, the function STILL reports a green
     `xfailed`, silently masking the exact failure this net exists to catch.

Split, the same guard reports `1 passed, 1 xfailed`, and a planted regression in the passing half
correctly reports `1 failed`.

HOW `strict=True` REPORTS. A pin that unexpectedly starts passing is reported as `failed` with
`[XPASS(strict)]`, never as `xpassed`. So the falsifiable health signal for this module is
`failed == 0` AND `xfailed > 0`: a nonzero `failed` means either a genuine break or a guard that
became real without its owning phase, and `xfailed == 0` means the pins have vanished and the
safety net is gone.
"""

from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import pytest

from agent_workflows import oc_runipd, runner_shutdown
from tests.support import git, init_repo


def _commit_base(repo: Path) -> str:
    """Create an initial commit in `repo` and return its sha (the lane's base)."""

    (repo / "tracked.py").write_text("VALUE = 1\n", encoding="utf-8")
    git(repo, "add", "tracked.py")
    git(repo, "commit", "-q", "-m", "base")
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def _pid_alive(pid: int) -> bool:
    """Is `pid` still running? `os.kill(pid, 0)` sends NO signal; it is a liveness probe."""

    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _captured_oc_launch(case: unittest.TestCase, *, isolated: bool):
    """Drive ONE real `oc_runipd.run_opencode` turn; return `(argv, env)` of the agent launch.

    THE MEASUREMENT SURFACE FOR BOTH GUARDS BELOW, shared because both need the same fact: what the
    driver actually hands the child. Source text cannot answer that, which is the lesson both guards
    record in their own docstrings.

    Records every `lane_containment.TurnBoundWatch` construction on `case.bound_constructions`, so a
    caller can assert WHICH bounds a real turn arms without reading the driver's source.

    THE AGENT LAUNCH IS THE LAST `Popen`: a turn may first spawn host sandbox capability probes,
    whose argv and env carry neither the policy nor the role marking, so taking the first would
    measure the wrong process.
    """

    from unittest import mock

    from agent_workflows import lane_containment

    launches: list[tuple[list[str], dict]] = []
    case.bound_constructions = []
    real_watch = lane_containment.TurnBoundWatch

    class _Proc:
        def __init__(self, argv, *a, **kw):
            launches.append(([str(x) for x in argv], dict(kw.get("env") or {})))
            self.stdout = iter(())
            self.stderr = None
            self.stdin = None

        def poll(self):
            return 0

        def wait(self, *a, **k):
            return 0

    def spy_watch(**kwargs):
        case.bound_constructions.append(dict(kwargs))
        return real_watch(**kwargs)

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        repo = root / "repo"
        repo.mkdir()
        run_dir = root / "run"
        (run_dir / "sessions").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        lane = root / "lane"
        lane.mkdir()
        plan = repo / "p.ipd.md"
        plan.write_text("# p\n", encoding="utf-8")
        prompt = run_dir / "prompts" / "p.md"
        prompt.write_text("do the thing\n", encoding="utf-8")
        item = {
            "id6": "8zgybk",
            "setid": "wtiso",
            "position": 1,
            "attempts": [{"number": 1}],
            "action": "execute",
        }
        state = {
            "run_id": "run-adv",
            "repo": str(repo),
            "options": {"opencode": "opencode"},
            "queue": [item],
        }
        with (
            mock.patch.object(oc_runipd.subprocess, "Popen", _Proc),
            mock.patch.object(lane_containment, "TurnBoundWatch", spy_watch),
            # The R4.2 policy probe would spawn a real host; it is proven separately in
            # `tests/test_lane_permission_posture.py`.
            mock.patch.object(
                oc_runipd,
                "observe_opencode_policy",
                lambda *a, **k: lane_containment.evaluate_policy_observation(
                    None, {}, failure_reason="probe skipped in this test"
                ),
            ),
        ):
            oc_runipd.run_opencode(
                state,
                run_dir,
                item,
                plan,
                prompt,
                1,
                work_dir=str(lane) if isolated else None,
            )
    case.assertTrue(launches, "run_opencode spawned no child at all")
    return launches[-1]


# ---- Guard 1: the forgetful agent (x03wgn Section 7 row "Agent forgets every custom AW tool") ----


class ForgetfulAgentTests(unittest.TestCase):
    """An agent edits a tracked file in its lane, runs NO `aw` command, writes NO outcome.json,
    and exits 0. x03wgn: "The driver must still observe, validate, report, and either integrate or
    block truthfully." Tool calls improve feedback but are NOT truth."""

    def test_forgetful_agent_git_observable_now(self):
        """OBSERVABILITY (passes today): the work is visible in git with no agent cooperation.

        This is the fact the whole driver-owned-lifecycle design rests on: even a perfectly
        forgetful agent leaves its edit in the working tree, so the driver can derive the outcome
        from git instead of trusting a self-report. If this ever fails, the premise is broken and
        Phase 2 cannot work.
        """

        with tempfile.TemporaryDirectory() as temp:
            repo = init_repo(Path(temp) / "lane")
            base = _commit_base(repo)

            # The forgetful agent: one edit, no `aw` command, no outcome.json, exit 0.
            (repo / "tracked.py").write_text("VALUE = 2\n", encoding="utf-8")

            porcelain = git(repo, "status", "--porcelain").stdout
            self.assertNotEqual(
                porcelain.strip(),
                "",
                "git status must still show the forgetful agent's edit",
            )
            self.assertIn("tracked.py", porcelain)

            # The unstaged diff against the recorded base names the changed file, so the driver can
            # enumerate real changed paths rather than reading a claim.
            diff_names = git(repo, "diff", "--name-only", base).stdout.split()
            self.assertIn("tracked.py", diff_names)

            # And the agent genuinely produced no evidence artifact of its own.
            self.assertFalse((repo / "outcome.json").exists())

    @pytest.mark.xfail(
        strict=True,
        reason="driver-observed OBSERVED state lands in rchpms/Phase 2",
    )
    def test_forgetful_agent_driver_report_pinned_absent(self):
        """PINNED ABSENT: no driver-observed OBSERVED report exists yet.

        Phase 2 (`rchpms`) makes the driver derive an authoritative report from git + process
        facts. Until then there is no such surface, so this must fail. `strict=True` means that if
        it starts passing without Phase 2, the run reports `failed [XPASS(strict)]` and we
        investigate rather than silently assuming the guard arrived.
        """

        # The Phase-2 surface: a driver-side observation that classifies a lane from git alone.
        self.assertTrue(
            hasattr(oc_runipd, "observe_lane_state")
            or hasattr(oc_runipd, "observed_outcome_from_git"),
            "no driver-observed OBSERVED classifier exists yet (owned by rchpms/Phase 2)",
        )


# ---- Guard 2: missing input (x03wgn Section 4) ----------------------------------------------------


class MissingInputTests(unittest.TestCase):
    """A required local file is absent from the lane. x03wgn Section 4 prescribes an
    `AW_MISSING_INPUT:<path>:<why>` response contract plus a driver-side classify/materialize/resume
    cycle that NEVER grants original-checkout access and never prompts interactively."""

    # The regex this Set will use to recognize the token in worker output.
    TOKEN_RE = re.compile(r"^AW_MISSING_INPUT:(?P<path>[^:]+):(?P<why>.+)$")

    def test_missing_input_token_format_now(self):
        """OBSERVABILITY: the token format parses, and the launch reality is asserted AS IT IS NOW.

        THE CHARACTERIZATION CONTRACT WAS OWED AN INVERSION AND NEVER GOT ONE, which is why this
        test's second half changed direction rather than being deleted. As authored (`8zgybk` E-07a)
        it pinned the qyaime root cause: `oc_runipd` launches OpenCode with a BARE `--auto` and ships
        NO permission configuration, so an `external_directory` ask in a headless turn has nothing to
        deny it and waits forever. That defect is FIXED. Executed plan `lanectn` Order 03 (`lhmrhx`,
        in `.aw/records/plans/executed/`) landed spec `7ckptx` R4.1: an isolated turn's child env now
        carries `OPENCODE_CONFIG_CONTENT` with `external_directory=deny` and `question=deny`.

        THE PIN DID NOT NOTICE, and the reason is the failure mode this whole cleanup exists for. It
        asserted `assertNotIn("OPENCODE_CONFIG_CONTENT", module_src)` and
        `assertNotIn('"permission"', module_src)` over the driver's SOURCE TEXT. The fix supplies both
        through NAMED shared symbols (`lane_containment.OPENCODE_RUNTIME_CONFIG_ENV`, whose value IS
        `"OPENCODE_CONFIG_CONTENT"`, and `LANE_PERMISSION_POLICY`), so neither literal appears in
        `oc_runipd.py` and both assertions stayed GREEN while asserting the opposite of reality.
        Measured here: the policy reaches the child, and `"OPENCODE_CONFIG_CONTENT" in
        Path(inspect.getfile(oc_runipd)).read_text()` is still False. A green test asserting a
        defect that is fixed is worse than no test: it reads as a standing claim the fix never landed.

        SO BOTH HALVES ARE NOW DRIVEN, not grepped:

          1. THE TOKEN, through the shipped `wtiso_gate` surfaces rather than a regex this file owns,
             so the format is asserted against the code that actually produces and consumes it.
          2. THE LAUNCH, by capturing the real argv and env handed to `Popen`. `--auto` IS still
             appended (that half was and remains true, and it is the reason a host-side denial is
             load-bearing), and the denial policy IS now supplied alongside it.

        NOTHING IS PINNED ABSENT HERE ANY MORE, so nothing is owed an owner. The missing-input cycle
        itself is asserted present by `test_missing_input_driver_denial_now_exists` below.
        """

        from agent_workflows import lane_containment, wtiso_gate

        # 1. THE TOKEN, through the shipped surfaces. Round trip first, so the format is defined by
        # the code and not by this file's own regex.
        self.assertEqual(
            wtiso_gate.format_missing_input("config/local.ini", "absent from lane"),
            "AW_MISSING_INPUT:config/local.ini:absent from lane",
        )
        self.assertEqual(
            wtiso_gate.parse_missing_input(
                "AW_MISSING_INPUT:config/local.ini:absent from lane"
            ),
            ("config/local.ini", "absent from lane"),
        )
        # A `why` containing colons still parses (the path is the first field only).
        self.assertEqual(
            wtiso_gate.parse_missing_input(
                "AW_MISSING_INPUT:a/b.txt:denied: outside lane"
            ),
            ("a/b.txt", "denied: outside lane"),
        )
        # Non-tokens must not parse, or the classifier would fire on ordinary prose.
        self.assertIsNone(
            wtiso_gate.parse_missing_input("I think AW_MISSING_INPUT would be nice")
        )
        # This module's own regex agrees with the shipped parser, so the two cannot drift.
        match = self.TOKEN_RE.match(
            wtiso_gate.format_missing_input("config/local.ini", "absent from lane")
        )
        self.assertIsNotNone(match)
        assert match is not None  # narrow for type checkers
        self.assertEqual(match.group("path"), "config/local.ini")
        self.assertEqual(match.group("why"), "absent from lane")

        # 2. THE LAUNCH, measured from the real child rather than from source text.
        argv, env = _captured_oc_launch(self, isolated=True)
        self.assertIn(
            "--auto",
            argv,
            "the headless auto-accept launch is still what makes a host-side denial load-bearing",
        )
        policy_key = lane_containment.OPENCODE_RUNTIME_CONFIG_ENV
        self.assertIn(
            policy_key,
            env,
            "INVERTED from the original pin: a runner-supplied permission config now EXISTS "
            "(`lhmrhx`, spec 7ckptx R4.1)",
        )
        policy = json.loads(env[policy_key])["permission"]
        self.assertEqual(policy["external_directory"], "deny")
        self.assertEqual(policy["question"], "deny")
        # WHY THE ORIGINAL PIN COULD NOT SEE THIS, asserted so the lesson is not re-learned: the
        # literal it searched for is genuinely absent from the driver's source, because the value
        # arrives through a named shared constant.
        self.assertEqual(policy_key, "OPENCODE_CONFIG_CONTENT")
        self.assertNotIn(
            policy_key,
            Path(inspect.getfile(oc_runipd)).read_text(encoding="utf-8"),
            "the driver supplies the policy by NAMED constant, which is exactly why a source-text "
            "pin on this literal stayed green after the fix landed",
        )

    def test_missing_input_driver_denial_now_exists(self):
        """CONVERTED FROM A PIN (`lanectn` `604wra`): the missing-input cycle now EXISTS.

        WHY THIS IS NO LONGER `xfail`, stated because silently deleting a pin is how a safety net
        disappears. This module's own contract (see the module docstring) is that a
        `strict=True` pin which starts passing is reported as `failed [XPASS(strict)]` and must be
        investigated. It started passing legitimately: `lanectn` child `y5od1h` shipped the
        report-and-refuse cycle (spec R3) and `604wra` re-pointed the gate-library stubs at it
        (R6.1). So the pin is CONVERTED into a positive assertion of the guard that arrived, which is
        strictly stronger than the pin was.

        NOT the same as the original owner's plan, and the difference is recorded rather than glossed:
        `qcqhj7` (Phase 1) was RETIRED, and its permit-and-copy branch was WITHDRAWN outright by spec
        `7ckptx` R3.3a. The cycle that landed is REPORT-AND-REFUSE: nothing is ever materialized into
        a lane on request. Asserting a "resume" or a successful copy here would assert behavior the
        spec now forbids.
        """

        from agent_workflows import lane_containment, wtiso_gate

        # 1. The token surface is real, and BOTH surfaces agree (one definition, R6.1).
        self.assertEqual(
            wtiso_gate.format_missing_input("config/local.ini", "absent from lane"),
            "AW_MISSING_INPUT:config/local.ini:absent from lane",
        )
        self.assertEqual(
            wtiso_gate.parse_missing_input(
                "AW_MISSING_INPUT:config/local.ini:absent from lane"
            ),
            ("config/local.ini", "absent from lane"),
        )

        # 2. The DRIVER-SIDE classification exists and REFUSES, which is the guard this guard is
        # about: a well-formed request for a real file is still refused, and nothing is copied.
        with tempfile.TemporaryDirectory() as temp:
            repo = init_repo(Path(temp) / "repo")
            _commit_base(repo)
            decision = lane_containment.classify_missing_input_report(
                "tracked.py", "needed by step 3", checkout=repo
            )
        self.assertEqual(
            decision.verdict, lane_containment.MISSING_INPUT_VERDICT_REFUSED
        )
        record = decision.as_dict()
        self.assertFalse(record["copied_into_lane"])
        self.assertFalse(record["granted_original_checkout_access"])

        # 3. And the host-denial half of the original pin's subject: the runner now supplies a
        # permission posture, which is the root cause the observability half above still pins.
        self.assertEqual(
            lane_containment.LANE_PERMISSION_POLICY["external_directory"], "deny"
        )
        self.assertEqual(lane_containment.LANE_PERMISSION_POLICY["question"], "deny")


# ---- Guard 3: hook bypass (x03wgn Section 7 row "Hook bypass") -----------------------------------


class HookBypassTests(unittest.TestCase):
    """An agent commits with `--no-verify`, so the pre-commit gate never runs. x03wgn: "Hooks are
    feedback only; driver invokes same predicates over final observable state.\" """

    def test_hook_bypass_detectable_from_git_now(self):
        """OBSERVABILITY (passes today): what the hook skipped is still visible in git.

        A `--no-verify` commit cannot hide its own content. `git show --name-only` reports the
        forbidden path, so the driver can re-run the same predicate over the observable end state
        and reach the correct verdict regardless of whether the hook ran.
        """

        with tempfile.TemporaryDirectory() as temp:
            repo = init_repo(Path(temp) / "lane")
            _commit_base(repo)

            # Install a pre-commit hook that ALWAYS rejects, to prove the bypass really bypassed.
            hook = repo / ".git" / "hooks" / "pre-commit"
            hook.write_text(
                "#!/bin/sh\necho 'gate: forbidden path'\nexit 1\n", encoding="utf-8"
            )
            hook.chmod(0o755)

            forbidden = repo / "forbidden.py"
            forbidden.write_text("SECRET = 1\n", encoding="utf-8")
            git(repo, "add", "forbidden.py")

            # The hook does block an honest commit...
            blocked = git(repo, "commit", "-m", "honest attempt")
            self.assertNotEqual(
                blocked.returncode,
                0,
                "the pre-commit hook should reject the honest commit",
            )

            # ...and `--no-verify` evades it (this is the adversarial behavior, in a throwaway
            # temp repo; the real repository's own commits never use it).
            bypassed = git(repo, "commit", "--no-verify", "-m", "bypassed")
            self.assertEqual(
                bypassed.returncode,
                0,
                "the --no-verify commit should succeed: {0}".format(bypassed.stderr),
            )

            # THE GUARD PREMISE: the violation is still fully observable after the fact.
            shown = git(repo, "show", "--name-only", "--format=", "HEAD").stdout
            self.assertIn(
                "forbidden.py",
                shown,
                "the bypassed commit's forbidden path must remain visible to the driver",
            )

    @pytest.mark.xfail(
        strict=True,
        reason="shared gate predicate lands in qcqhj7/rchpms",
    )
    def test_hook_bypass_driver_rejection_pinned_absent(self):
        """PINNED ABSENT: the driver cannot yet independently reject what the hook skipped.

        Owned by `qcqhj7`/`rchpms`: the ONE shared predicate library gains a real
        `check_hook_bypass` body that the hook, `aw lane status`, the driver, finalize, and
        integration all call, so an agent cannot satisfy one gate while violating another.
        """

        from agent_workflows import wtiso_gate

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            violations = wtiso_gate.check_hook_bypass(repo, "HEAD", ["allowed.py"])
            self.assertEqual(violations, [wtiso_gate.AW_GATE_HOOK_BYPASS])


# ---- Guard 4: protected-ref mutation (x03wgn Section 4 / Section 7) ------------------------------


class ProtectedRefTests(unittest.TestCase):
    """The shared Git common directory is mutated: an agent writes a stray ref, changes hooks, or
    touches another worktree's administration. x03wgn default mode = DETECTION (snapshot and verify
    protected Git state); hardened mode (Phase 6) denies it outright."""

    def test_protected_ref_mutation_detectable_now(self):
        """OBSERVABILITY (passes today): a before/after snapshot detects the mutation.

        The snapshots are `git worktree list --porcelain` + `git for-each-ref`. Nothing in the
        runner takes them today (that is the gap Phase 5 closes), but the raw detection mechanism
        works, which is what makes the Phase-5 guard implementable.
        """

        with tempfile.TemporaryDirectory() as temp:
            repo = init_repo(Path(temp) / "repo")
            _commit_base(repo)

            def snapshot() -> tuple[str, str]:
                return (
                    git(repo, "worktree", "list", "--porcelain").stdout,
                    git(
                        repo, "for-each-ref", "--format=%(refname) %(objectname)"
                    ).stdout,
                )

            before = snapshot()

            # The adversarial act: write a stray ref into the shared common directory.
            head = git(repo, "rev-parse", "HEAD").stdout.strip()
            wrote = git(repo, "update-ref", "refs/heads/stray-agent-ref", head)
            self.assertEqual(wrote.returncode, 0, wrote.stderr)

            after = snapshot()

            self.assertNotEqual(
                before[1],
                after[1],
                "the ref snapshot must differ after the stray ref write",
            )
            self.assertNotIn("refs/heads/stray-agent-ref", before[1])
            self.assertIn("refs/heads/stray-agent-ref", after[1])

            # A no-op change leaves the snapshot identical, so the detector does not cry wolf.
            self.assertEqual(after, snapshot())


# ---- Guard 5: nested permission deadlock (x03wgn Section 6, R10/R11) -----------------------------


class NestedPermissionDeadlockTests(unittest.TestCase):
    """A nested SUBAGENT session requests external permission. In a headless `--auto` turn nothing
    answers, so the run hangs. x03wgn Section 6 Layer 6 requires parsing root AND child permission
    events with a short permission deadline plus a full process-tree kill."""

    def test_nested_permission_only_stall_watchdog_now(self):
        """CHARACTERIZATION, STILL LIVE: no permission-EVENT bound is armed on a real turn.

        THE PINNED GAP IS STILL REAL, which is why this test keeps its characterization intent
        instead of being deleted or inverted. `lane_containment.PERMISSION_TIMEOUT` ships at `0`
        (DISABLED), so a turn blocked on an unanswered nested permission ask is covered only by the
        coarse no-progress watchdog and by `MAX_TURN_TIMEOUT`. A stall watchdog fires on NO OUTPUT,
        and a session blocked on an ask may still emit keepalives, which is the qyaime symptom.

        WHO OWNS INVERTING IT, so this pin is not orphaned the way the deleted
        `test_wtiso_characterization.py` was. It is NOT a stale pointer at a retired plan: the owner
        is APPROVED SPEC `7ckptx` requirement R4.4b (`.aw/records/specs/`, `- Status: approved`),
        which states the default stays `0` and names exactly what closes it - "the implementing plan
        MUST either (i) provoke a real permission ask, capture the stream, and paste the matched
        line, after which the default may be set to 30 seconds; or (ii) record that detection is not
        possible on stdout". Whichever plan does (i) MUST come back and invert the
        `PERMISSION_TIMEOUT == 0` assertion below. Option (ii) was taken as an INTERIM by executed
        plan `lanectn` Order 03 (`lhmrhx`), which is why the consequence is written down in the
        product (`TestPermissionDetectorIsUnproven` in `tests/test_turn_bounds.py` asserts that).

        WHAT CHANGED HERE, and why the change was not optional. Two of the original assertions were
        SOURCE-TEXT searches over `oc_runipd.py` for `permission_deadline` / `permission_timeout` /
        `PERMISSION_DEADLINE`, on the theory that arming a bound would make one appear. That theory
        is now false: the bound arrived under a DIFFERENT name in a DIFFERENT module
        (`lane_containment.PERMISSION_TIMEOUT`, passed to `TurnBoundWatch`), so the pin would keep
        passing with the bound fully armed - and it very nearly did, since the driver's source does
        already contain the string `PERMISSION_TIMEOUT` inside a comment. The replacement asserts the
        ARMED STATE of a REAL turn's bound instead, which no renaming can evade.
        """

        from agent_workflows import lane_containment

        # THE COARSE BOUND is what a wedged turn is left with, and it is unchanged.
        self.assertEqual(oc_runipd.DEFAULT_STALL_TIMEOUT, 600.0)

        # THE PROCESS-TREE KILL WORKS, driven rather than grepped. The original asserted `killpg` and
        # `getpgid` appear in the reaper's source; a comment satisfies that. Instead: a child that
        # IGNORES SIGINT and SIGTERM, with a grandchild that ignores them too, is reaped through the
        # ONE shared routine, and BOTH die. That is the capability the missing trigger would use.
        self.assertIs(
            oc_runipd.runner_shutdown.terminate_process,
            runner_shutdown.terminate_process,
            "the driver must reach the ONE shared reaper (spec `c4gd2h` R5)",
        )
        ignore_signals = (
            "import signal, subprocess, sys, time\n"
            "signal.signal(signal.SIGINT, signal.SIG_IGN)\n"
            "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        )
        grandchild_code = ignore_signals + "time.sleep(120)\n"
        child = subprocess.Popen(
            [
                sys.executable,
                "-c",
                ignore_signals
                + "g = subprocess.Popen([sys.executable, '-c', {0!r}])\n".format(
                    grandchild_code
                )
                + "print(g.pid, flush=True)\ntime.sleep(120)\n",
            ],
            stdout=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            assert child.stdout is not None
            grandchild_pid = int(child.stdout.readline().strip())
            # Short graces so the SIGKILL-to-the-group escalation is what ends this quickly.
            oc_runipd.runner_shutdown.terminate_process(
                child, sigint_grace=0.3, sigterm_grace=0.3
            )
            self.assertIsNotNone(child.poll(), "the child survived the shared reaper")
            deadline = time.monotonic() + 10.0
            while time.monotonic() < deadline and _pid_alive(grandchild_pid):
                time.sleep(0.05)
            self.assertFalse(
                _pid_alive(grandchild_pid),
                "the GRANDCHILD survived: the process-group kill the missing permission trigger "
                "would rely on is not working",
            )
        finally:
            if child.poll() is None:  # pragma: no cover - defensive
                child.kill()
                child.wait(timeout=5)

        # THE GAP ITSELF, asserted as the ARMED STATE of a real turn's bound rather than as the
        # absence of an identifier. INVERT THIS when spec `7ckptx` R4.4b option (i) is delivered.
        self.assertEqual(
            lane_containment.PERMISSION_TIMEOUT,
            0.0,
            "spec 7ckptx R4.4b keeps the permission bound DISABLED until a real provoked ask is "
            "captured; the plan that captures it must invert this assertion",
        )
        watch = lane_containment.TurnBoundWatch(
            reap=lambda bound, timeout: self.fail(
                "an unarmed permission bound fired: " + bound
            ),
            max_turn_timeout=0,
        )
        with watch:
            # An observed ask CANNOT arm it while the default is 0, which is the whole gap: this is
            # the qyaime shape (the ask arrives, nothing answers, and nothing bounds the wait).
            watch.note_permission_request()
            time.sleep(0.3)
        self.assertIsNone(
            watch.fired,
            "with PERMISSION_TIMEOUT at 0 an observed ask must not arm any bound",
        )
        # ...and MAX_TURN_TIMEOUT is therefore the only bound a real turn arms against a deadlock.
        _argv, _env = _captured_oc_launch(self, isolated=True)
        self.assertEqual(
            [kwargs.get("permission_timeout") for kwargs in self.bound_constructions],
            [None],
            "a real turn must construct exactly ONE bound watch and must not arm a permission "
            "bound; constructions were {0!r}".format(self.bound_constructions),
        )
        self.assertGreater(self.bound_constructions[0]["max_turn_timeout"], 0.0)

    def test_nested_permission_detection_now_exists_but_is_not_armed(self):
        """CONVERTED FROM A PIN (`lanectn` `604wra`): the DETECTOR exists; the live bound does NOT.

        WHY CONVERTED. As `strict=True`, this pin reported `failed [XPASS(strict)]` the moment
        `604wra` implemented `check_permission_deadline`, which is precisely the investigate-me signal
        this module's docstring specifies. Investigated: the pass is legitimate, so the pin becomes a
        positive assertion.

        BUT READ THE SECOND HALF, because converting this to a plain "the guard arrived" test would
        OVERSTATE what shipped, and overstating a guarantee is the failure mode spec `7ckptx` Goal 5
        names. What exists is a PURE PREDICATE over a recorded stream. What does NOT exist is a live
        permission-event bound: `lane_containment.PERMISSION_TIMEOUT` ships at `0` (DISABLED) because
        detection would be pattern matching on the child's stdout and is UNVERIFIED against a real
        provoked ask (spec R4.4b). So this test asserts BOTH halves - the detector works, and the
        bound is still disarmed - which keeps the remaining gap visible instead of declaring victory.

        The captured event stream below is the qyaime shape: the ask arrives on a CHILD sessionID, not
        the root, which is why a root-only parser would miss it entirely.
        """

        from agent_workflows import lane_containment, wtiso_gate

        events = [
            {"type": "session.start", "sessionID": "root-1", "time": 0.0},
            {
                "type": "session.start",
                "sessionID": "child-9",
                "parentID": "root-1",
                "time": 1.0,
            },
            {
                "type": "permission.ask",
                "sessionID": "child-9",
                "permission": "external_directory",
                "path": "/outside/the/lane",
                "time": 2.0,
            },
            {"type": "keepalive", "sessionID": "root-1", "time": 90.0},
        ]

        # HALF 1: the detector catches the NESTED ask, which a root-only parser would miss.
        violations = wtiso_gate.check_permission_deadline(events, deadline_seconds=5.0)
        self.assertEqual(violations, [wtiso_gate.AW_PERMISSION_DEADLINE])

        # ...and does not cry wolf when the ask WAS answered on its own child session.
        answered = events[:-1] + [
            {"type": "permission.answer", "sessionID": "child-9", "time": 3.0},
            {"type": "keepalive", "sessionID": "root-1", "time": 90.0},
        ]
        self.assertEqual(
            wtiso_gate.check_permission_deadline(answered, deadline_seconds=5.0), []
        )

        # HALF 2: THE REMAINING GAP, asserted so it cannot be quietly closed or quietly forgotten.
        # The permission bound is DISARMED (spec R4.4b): its detector is unverified against a real
        # ask, and a false positive would kill a healthy turn. `MAX_TURN_TIMEOUT` is therefore still
        # the ONLY bound covering a permission deadlock. If someone arms `PERMISSION_TIMEOUT`, this
        # fails loudly and must be updated TOGETHER with the captured-stream evidence R4.4b demands.
        self.assertEqual(
            lane_containment.PERMISSION_TIMEOUT,
            0.0,
            "PERMISSION_TIMEOUT must stay disabled until its detector is verified (R4.4b)",
        )
        self.assertGreater(lane_containment.MAX_TURN_TIMEOUT, 0.0)


if __name__ == "__main__":
    unittest.main()
