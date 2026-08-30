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
import re
import tempfile
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
        """OBSERVABILITY (passes today): the token format parses, AND the launch reality that
        motivates qyaime is real.

        Two facts, both true now:

        1. the `AW_MISSING_INPUT:<path>:<why>` shape is unambiguously parseable, so Phase 1 can
           build the classifier on it; and
        2. the runner launches OpenCode with a BARE `--auto` (agent_workflows/oc_runipd.py:1719)
           and ships NO permission configuration, which is the root cause of qyaime: an
           `external_directory` ask in a headless `--auto` turn has nothing to deny it, so the
           turn waits forever.

        NOTE ON WHAT IS DELIBERATELY *NOT* ASSERTED: an earlier draft asserted the literal string
        `external_directory` is absent from the runner source. That string appears NOWHERE in the
        package, so the assertion would be VACUOUSLY true and would keep passing even after the
        deadlock is fixed or the runner deleted. It proves nothing, so it is not used. The
        assertion below targets the actual root cause instead: `--auto` is appended with no
        accompanying permission config.
        """

        m = self.TOKEN_RE.match("AW_MISSING_INPUT:config/local.ini:absent from lane")
        self.assertIsNotNone(m)
        assert m is not None  # narrow for type checkers
        self.assertEqual(m.group("path"), "config/local.ini")
        self.assertEqual(m.group("why"), "absent from lane")

        # A `why` containing colons still parses (the path is the first field only).
        m2 = self.TOKEN_RE.match("AW_MISSING_INPUT:a/b.txt:denied: outside lane")
        self.assertIsNotNone(m2)
        assert m2 is not None
        self.assertEqual(m2.group("path"), "a/b.txt")

        # Non-tokens must not match, or the classifier would fire on ordinary prose.
        self.assertIsNone(self.TOKEN_RE.match("I think AW_MISSING_INPUT would be nice"))

        # CURRENT LAUNCH REALITY: the argv builder appends a bare `--auto`.
        launch_src = inspect.getsource(oc_runipd.run_opencode)
        self.assertIn(
            'argv.append("--auto")',
            launch_src,
            "run_opencode should still append a bare --auto today",
        )

        # ...and the module ships no permission configuration alongside it. If a later phase adds
        # one, THIS assertion fails loudly and must be updated with the fix, which is the point.
        module_src = Path(inspect.getfile(oc_runipd)).read_text(encoding="utf-8")
        self.assertNotIn(
            "OPENCODE_CONFIG_CONTENT",
            module_src,
            "no runner-local OpenCode permission config exists yet",
        )
        self.assertNotIn(
            '"permission"',
            module_src,
            "no permission policy key is passed to the host yet",
        )

    @pytest.mark.xfail(
        strict=True,
        reason="AW_MISSING_INPUT deny/classify/resume lands in qcqhj7/Phase 1",
    )
    def test_missing_input_driver_denial_pinned_absent(self):
        """PINNED ABSENT: no driver-side missing-input deny/classify/resume cycle exists.

        Owned by `qcqhj7` (Phase 1), which adds the minimal input manifest, the response contract,
        and the runner-local config that denies unattended `external_directory` and `question`
        asks.
        """

        from agent_workflows import wtiso_gate

        # Phase 1 fills these bodies in the ONE shared gate library; today they refuse.
        self.assertEqual(
            wtiso_gate.format_missing_input("config/local.ini", "absent from lane"),
            "AW_MISSING_INPUT:config/local.ini:absent from lane",
        )


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
        """OBSERVABILITY (passes today): the ONLY bound is the coarse 600s stall watchdog.

        This pins the exact shape of the gap. A stall watchdog fires on NO OUTPUT, but a session
        blocked on an unanswered permission ask may still emit keepalive events, and even when it
        does not, 600 seconds of a wedged unattended run is the qyaime symptom. There is no
        sub-second, permission-EVENT-driven deadline. Process-group cleanup does exist, so the kill
        mechanism is available to Phase 1; only the trigger is missing.
        """

        # The coarse bound, agent_workflows/oc_runipd.py:1629.
        self.assertEqual(oc_runipd.DEFAULT_STALL_TIMEOUT, 600.0)

        module_src = Path(inspect.getfile(oc_runipd)).read_text(encoding="utf-8")

        # Process-tree kill exists. CONSCIOUS UPDATE (runstop Phase 0, `2ouj70`): the escalation
        # MOVED into the single shared reaper `runner_shutdown.terminate_process` (spec `c4gd2h`
        # R5 forbids the two byte-identical per-driver copies this used to grep for). The
        # capability is unchanged, so this guard now asserts it where it actually lives and that
        # the driver still reaches it. It is deliberately NOT weakened: `killpg`/`getpgid` are
        # still required to exist, and the driver must still delegate to them.
        reaper_src = inspect.getsource(runner_shutdown)
        self.assertIn("killpg", reaper_src)
        self.assertIn("getpgid", reaper_src)
        self.assertIn(
            "runner_shutdown.terminate_process",
            inspect.getsource(oc_runipd.terminate_process),
        )

        # But NO permission-deadline trigger exists. When Phase 1 adds one, this fails loudly and
        # must be updated together with the fix.
        for symbol in (
            "permission_deadline",
            "permission_timeout",
            "PERMISSION_DEADLINE",
        ):
            self.assertNotIn(
                symbol,
                module_src,
                "{0} should not exist before qcqhj7/Phase 1".format(symbol),
            )

    @pytest.mark.xfail(
        strict=True,
        reason="permission-event deadline lands in qcqhj7/Phase 1",
    )
    def test_nested_permission_bounded_kill_pinned_absent(self):
        """PINNED ABSENT: an unanswered CHILD-session permission ask does not yet cause a bounded kill.

        The captured event stream below is the qyaime shape: the ask arrives on a CHILD sessionID,
        not the root, which is why a root-only parser would miss it entirely. Owned by `qcqhj7`
        (Phase 1).
        """

        from agent_workflows import wtiso_gate

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

        violations = wtiso_gate.check_permission_deadline(events, deadline_seconds=5.0)
        self.assertEqual(violations, [wtiso_gate.AW_PERMISSION_DEADLINE])


if __name__ == "__main__":
    unittest.main()
