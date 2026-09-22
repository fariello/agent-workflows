"""Worker-role lifecycle verbs refuse deterministically (wtiso-03 `rchpms` E-04..E-06).

x03wgn Section 2 "Receipt ownership does not mean agent tool compliance" + Section 3
`AW-LIFECYCLE-ROLE-001`. The driver already wraps begin/finalize, but receipt OWNERSHIP alone does not
stop an in-lane agent from running `aw ipd begin`/`aw ipd finalize` ITSELF, which forks a second
receipt and a second lifecycle transaction the driver cannot see (and the in-lane receipt copy then
hides the split). So a process marked `AW_EXECUTION_ROLE=worker` refuses both verbs outright.

ADVERSARIAL SHAPE: the refusal tests drive the REAL CLI in a subprocess with the env var set - not the
predicate - and assert (a) the documented exit code, (b) the `AW-LIFECYCLE-ROLE-001` token on stderr,
and (c) that NO receipt file was created. (c) is the assertion that matters: a refusal that still wrote
a receipt would leave exactly the forked authority this guard exists to prevent.

HONEST LIMIT (asserted nowhere because it is not enforceable here): the env selector is the
operational-default guidance layer, not a hardened boundary. A same-user worker with shell access can
unset it; hard enforcement is an OS sandbox / separate principal (x03wgn Phase 6, `1o4eif`).
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd
from agent_workflows import ipd_authoring as A
from agent_workflows import ipd_lifecycle as LC
from agent_workflows import oc_runipd

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")


def _commit_all(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)


def _ready_plan_text(*, plan_id: str = "abc123") -> str:
    txt = A.build_skeleton(
        kind="child",
        title="demo",
        author="tester",
        when="2026-08-24",
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
            out.append("- Scope-Paths: agent_workflows/demo.py, tests/test_demo.py")
            continue
        if in_meta and ln.startswith("- Item-Dependencies:"):
            out.append("- Item-Dependencies: none")
            continue
        out.append(ln)
        if in_meta and ln.startswith("- Author:"):
            out.append("- Approval: 2026-08-24, human: approved")
    return "\n".join(out) + "\n"


class RoleStatementInPromptsTests(unittest.TestCase):
    """roleadv-01 (`8b9ufm`) E-01: the rule is ADVERTISED at turn start, not only refused at turn end.

    WHY THIS LIVES BESIDE THE REFUSAL TESTS rather than with the other prompt tests: the advertisement
    and the enforcement are one contract, and a reader who changes either must see the other. The
    refusal (`AW-LIFECYCLE-ROLE-001`) is correct and nothing here weakens it; what was missing is that
    the prompt opening the turn said NOTHING about who owns begin/finalize, so an agent paid a whole
    turn to learn a rule that fits in one sentence (measured: plan `03ie04` spent its terminal output
    reasoning about the refusal).

    FOUR BUILDERS, TWO OWNERSHIP BRANCHES, EIGHT ASSERTIONS. The builders are
    `oc_runipd.build_prompt`, `oc_runipd.build_verifier_prompt`, `agy_runipd.build_prompt` and
    `agy_runipd.build_verifier_prompt` (each now a thin host binding over the ONE shared composer in
    `runner_shared`, which is why the statement can be a single constant).

    THE ASYMMETRY A READER MUST NOT MISREAD, stated because eight green assertions look like eight
    proofs and are not. At HEAD, before E-02/E-03, the FOUR POSITIVE assertions (statement PRESENT
    when the driver owns the transition) FAIL, and the FOUR NEGATIVE ones (statement ABSENT under
    `--no-self-finalize`) PASS VACUOUSLY because nothing is emitted in either branch yet. The negative
    four only become load-bearing AFTER the statement exists: they are what stops an unconditional
    statement from telling the one agent that MUST transition its own plan not to.

    RENDERED OUTPUT, NOT SOURCE TEXT. Every assertion CALLS a builder and inspects the returned
    string. A source grep would pass while the sentence sat in a branch no invocation reaches.

    NO AMBIENT ENV. The ownership signal is the run's own frozen `options.self_finalize`, passed
    through the constructed `state` dict, so these assertions behave identically inside a managed
    worker lane and outside one. (This module's
    `ChildEnvWorkerRoleTests.test_driver_own_process_is_not_worker_role` legitimately reds inside a
    lane; nothing here may join it.)
    """

    #: A SHORT STABLE ANCHOR, deliberately not a whole sentence: the rule's token plus one invariant
    #: phrase. A whole-sentence match breaks on every prose improvement, which is how prompt tests
    #: earn their reputation and then get deleted; this shape survives rewording and still fails if
    #: the statement disappears.
    ANCHOR_TOKEN = "AW-LIFECYCLE-ROLE-001"
    ANCHOR_PHRASE = "runner performs `aw ipd begin`"

    def _item(self) -> dict:
        return {"position": 1, "id6": "abc123", "setid": "demo", "attempts": []}

    def _state(self, *, self_finalize: bool | None) -> dict:
        """The run state a builder receives. ``None`` omits ``options`` entirely (defaults to owned)."""
        state: dict = {"run_id": "run-20260101T000000Z-1", "repo": "."}
        if self_finalize is not None:
            state["options"] = {"self_finalize": self_finalize}
        return state

    def _exec_prompt(self, mod, *, self_finalize: bool | None) -> str:
        return mod.build_prompt(
            self._item(),
            self._state(self_finalize=self_finalize),
            Path("/tmp/run-dir"),
            Path("/tmp/repo/plan.ipd.md"),
            False,
        )

    def _verifier_prompt(self, mod, *, self_finalize: bool | None) -> str:
        return mod.build_verifier_prompt(
            self._item(),
            self._state(self_finalize=self_finalize),
            Path("/tmp/run-dir"),
            Path("/tmp/repo/plan.ipd.md"),
        )

    def _builders(self):
        for mod in (oc_runipd, agy_runipd):
            yield f"{mod.__name__}.build_prompt", self._exec_prompt, mod
            yield f"{mod.__name__}.build_verifier_prompt", self._verifier_prompt, mod

    def test_all_four_builders_state_the_role_when_the_driver_owns_the_transition(self):
        """THE FOUR POSITIVE ASSERTIONS. These FAIL at HEAD; that failure is E-01's whole point."""

        for label, build, mod in self._builders():
            for owned in (None, True):  # absent options defaults to owned
                with self.subTest(builder=label, self_finalize=owned):
                    prompt = build(mod, self_finalize=owned)
                    self.assertIn(
                        self.ANCHOR_TOKEN,
                        prompt,
                        f"{label} does not name the rule the runner will refuse",
                    )
                    self.assertIn(
                        self.ANCHOR_PHRASE,
                        prompt,
                        f"{label} does not say who performs begin/finalize",
                    )

    def test_no_builder_states_the_role_when_the_agent_owns_the_transition(self):
        """THE FOUR NEGATIVE ASSERTIONS, vacuous at HEAD and load-bearing after E-02/E-03.

        Under `--no-self-finalize` the AGENT is the only party that can transition the plan (that
        flag's own help text says "the agent must move the plan itself"), so telling it the runner
        owns the verbs would leave the plan in `pending/` transitioned by nobody.
        """

        for label, build, mod in self._builders():
            with self.subTest(builder=label, self_finalize=False):
                prompt = build(mod, self_finalize=False)
                self.assertNotIn(
                    self.ANCHOR_TOKEN,
                    prompt,
                    f"{label} claims the runner owns begin/finalize under --no-self-finalize, "
                    "where the agent is the only party that can transition the plan",
                )
                self.assertNotIn(
                    self.ANCHOR_PHRASE,
                    prompt,
                    f"{label} states the role under --no-self-finalize",
                )

    def test_the_statement_is_ONE_constant_so_the_hosts_cannot_drift(self):
        """Host symmetry as a PROPERTY: the rendered statement is byte-identical across all four."""

        from agent_workflows import ipd_lifecycle as _LC

        block = _LC.runner_owns_lifecycle_notice(True)
        self.assertTrue(block.strip(), "the notice must be non-empty when owned")
        self.assertEqual(
            _LC.runner_owns_lifecycle_notice(False),
            "",
            "the notice must be EMPTY when the agent owns the transition",
        )
        for label, build, mod in self._builders():
            with self.subTest(builder=label):
                self.assertIn(
                    block.strip(),
                    build(mod, self_finalize=True),
                    f"{label} does not render the ONE shared constant",
                )

    def test_the_statement_names_the_agents_terminal_obligation(self):
        """It must say three things and no more: who performs them, that the agent must not, and stop."""

        from agent_workflows import ipd_lifecycle as _LC

        block = _LC.runner_owns_lifecycle_notice(True)
        flat = " ".join(block.split())
        self.assertIn("AW-LIFECYCLE-ROLE-001", flat)
        self.assertIn("runner performs `aw ipd begin` and `aw ipd finalize`", flat)
        self.assertIn("Do NOT run them", flat)
        self.assertIn("outcome file", flat)
        self.assertEqual(
            sorted({c for c in block if ord(c) > 127}),
            [],
            "the statement reaches a prompt asserted pure ASCII",
        )


class WorkerRolePredicateTests(unittest.TestCase):
    """E-04: the pure predicate and the deterministic error token."""

    def test_worker_role_predicate(self):
        self.assertIs(LC.worker_role_active({"AW_EXECUTION_ROLE": "worker"}), True)
        self.assertIs(LC.worker_role_active({}), False)
        self.assertIs(
            LC.worker_role_active({"AW_EXECUTION_ROLE": "coordinator"}), False
        )
        # An empty/whitespace value is not a worker either (fail OPEN for the role check is correct:
        # only an explicit `worker` marking removes authority).
        self.assertIs(LC.worker_role_active({"AW_EXECUTION_ROLE": ""}), False)
        self.assertIs(LC.worker_role_active({"AW_EXECUTION_ROLE": "  worker  "}), True)
        self.assertTrue(LC.LIFECYCLE_ROLE_ERROR.startswith("AW-LIFECYCLE-ROLE-001"))


class WorkerRoleCliRefusalTests(unittest.TestCase):
    """E-05: the CLI verbs refuse, with no receipt and no transition."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        d = self.root / ".aw" / "records" / "plans" / "pending"
        d.mkdir(parents=True, exist_ok=True)
        self.plan = d / "20260824-demo-01-abc123-demo.ipd.md"
        self.plan.write_text(_ready_plan_text(), encoding="utf-8")
        _commit_all(self.root, "init")
        self.receipt = LC.receipt_path_for(self.root, "abc123")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run_cli(self, *argv: str, role: str | None) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(_REPO_ROOT)
        env.pop("AW_EXECUTION_ROLE", None)
        if role is not None:
            env["AW_EXECUTION_ROLE"] = role
        return subprocess.run(
            [sys.executable, "-m", "agent_workflows", *argv],
            cwd=self.root,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_worker_role_begin_refuses_with_role_error(self):
        proc = self._run_cli(
            "ipd", "begin", str(self.plan), "--actor", "x", role="worker"
        )
        self.assertEqual(
            proc.returncode,
            LC.EXIT_CANNOT_RUN,
            f"stdout={proc.stdout!r} stderr={proc.stderr!r}",
        )
        self.assertIn("AW-LIFECYCLE-ROLE-001", proc.stderr)
        # THE POINT: no execution authority was created.
        self.assertFalse(
            self.receipt.exists(),
            "a refused worker-role begin must write NO receipt",
        )

    def test_worker_role_finalize_refuses_and_writes_no_receipt(self):
        proc = self._run_cli(
            "ipd",
            "finalize",
            str(self.plan),
            "--actor",
            "x",
            "--message",
            "m",
            "--apply",
            role="worker",
        )
        self.assertEqual(
            proc.returncode,
            LC.EXIT_CANNOT_RUN,
            f"stdout={proc.stdout!r} stderr={proc.stderr!r}",
        )
        self.assertIn("AW-LIFECYCLE-ROLE-001", proc.stderr)
        self.assertFalse(self.receipt.exists())
        # And no terminal transition happened: the plan is still where it was.
        self.assertTrue(self.plan.is_file(), "the plan must not have been moved")

    def test_coordinator_role_begin_runs_normally(self):
        """The guard must not break the normal path: with no role marking, the gate runs."""
        proc = self._run_cli("ipd", "begin", str(self.plan), "--actor", "x", role=None)
        self.assertEqual(
            proc.returncode,
            LC.EXIT_OK,
            f"stdout={proc.stdout!r} stderr={proc.stderr!r}",
        )
        self.assertNotIn("AW-LIFECYCLE-ROLE-001", proc.stderr)
        self.assertTrue(
            self.receipt.is_file(),
            "a coordinator-role begin must write the receipt (normal gate ran)",
        )


class ChildEnvWorkerRoleTests(unittest.TestCase):
    """E-06: the drivers mark only the WORKER child, never their own process."""

    def test_both_drivers_mark_only_an_isolated_turn(self):
        """The marking is WIRED into both turn functions, keyed on the lane, and strips a stale value.

        DRIVEN THROUGH A REAL TURN ON EACH HOST, capturing the env actually handed to `Popen`. The
        previous version searched each turn function's SOURCE for `pinned_child_env()`,
        `popen_kwargs["env"] = child_env`, `if work_dir:` and
        `child_env.pop(ipd_lifecycle.EXECUTION_ROLE_ENV, None)`. Every one of those strings appears
        in each driver's explanatory COMMENT block as well as its code (`oc_runipd` spends fourteen
        comment lines naming `pinned_child_env`, `work_dir` and the strip), so the pin could stay
        green with the assignment deleted. This repository measured that exact failure on the
        neighbouring policy injection in the SAME construction: sabotaging it to `pass` left a
        source-text assertion green, and only capturing the child env failed
        (`tests/test_lane_permission_posture.py`).

        FOUR HALVES, each a distinct failure the marking must not have:

          (a) INHERITED ENV IS CARRIED - `AW_PIN_KEEP_ROOT` and `PATH` survive, so the marking rides
              on the SHARED `pinned_child_env` construction rather than a second, minimal one.
          (b) MARKED IN A LANE - `AW_EXECUTION_ROLE=worker` reaches the child of an isolated turn,
              which is what makes an in-lane `aw ipd begin/finalize` hit AW-LIFECYCLE-ROLE-001.
          (c) NOT MARKED OTHERWISE - a non-isolated turn's child carries no marking at all.
          (d) A STALE VALUE IS STRIPPED - with `AW_EXECUTION_ROLE=worker` already in the DRIVER's own
              environment, a non-isolated turn's child still gets none, so a coordinator turn can
              never inherit a marking and refuse its own lifecycle verbs. (c) alone would pass on a
              driver that merely never SETS it.

        The value's round trip through the refusal predicate is asserted by
        `test_the_marking_predicate_round_trips`; this test asserts the drivers really emit it.
        """
        for module, launcher in (
            (oc_runipd, "run_opencode"),
            (agy_runipd, "run_agy_turn"),
        ):
            with self.subTest(driver=module.__name__):
                for stale in (False, True):
                    with (
                        self.subTest(stale_inherited_marking=stale),
                        mock.patch.dict(
                            os.environ,
                            {LC.EXECUTION_ROLE_ENV: LC.ROLE_WORKER} if stale else {},
                            clear=False,
                        ),
                    ):
                        if not stale:
                            os.environ.pop(LC.EXECUTION_ROLE_ENV, None)
                        iso_env = self._child_env(module, launcher, isolated=True)
                        main_env = self._child_env(module, launcher, isolated=False)

                        # (a) the SHARED construction's inherited content is intact.
                        self.assertEqual(
                            iso_env.get("AW_PIN_KEEP_ROOT"),
                            oc_runipd.runner_package_root(),
                            "the marking must ride on the shared pinned child env",
                        )
                        self.assertTrue(iso_env.get("PATH"))
                        # (b) an isolated turn's child IS the managed worker.
                        self.assertEqual(
                            iso_env.get(LC.EXECUTION_ROLE_ENV), LC.ROLE_WORKER
                        )
                        self.assertTrue(LC.worker_role_active(iso_env))
                        # (c)/(d) a non-isolated turn's child is never marked, even when the
                        # driver's own environment carries a stale marking.
                        self.assertNotIn(LC.EXECUTION_ROLE_ENV, main_env)
                        self.assertFalse(LC.worker_role_active(main_env))
                        if stale:
                            # Prove the stale value really was present to be stripped, so this
                            # subTest is not a repeat of the clean one.
                            self.assertEqual(
                                os.environ.get(LC.EXECUTION_ROLE_ENV), LC.ROLE_WORKER
                            )

    def _child_env(self, module, launcher: str, *, isolated: bool) -> dict:
        """The env handed to `Popen` for ONE real turn on `module`'s host.

        The AGENT launch is the LAST `Popen`: a turn may first spawn host capability probes, whose
        env carries neither the marking nor the policy, so taking the first would assert the wrong
        process.
        """
        from unittest import mock

        from agent_workflows import lane_containment

        envs: list[dict] = []

        class _Proc:
            def __init__(self, *a, **kw):
                envs.append(dict(kw.get("env") or {}))
                self.stdout = iter(())
                self.stderr = None
                self.stdin = None

            def poll(self):
                return 0

            def wait(self, *a, **k):
                return 0

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
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
                "id6": "rchpms",
                "setid": "wtiso",
                "position": 1,
                "attempts": [{"number": 1}],
                "action": "execute",
            }
            state = {
                "run_id": "run-1",
                "repo": str(repo),
                "options": {"opencode": "opencode", "agy": "/bin/true"},
                "queue": [item],
            }
            work_dir = str(lane) if isolated else None
            with (
                mock.patch.object(module.subprocess, "Popen", _Proc),
                # The oc host's R4.2 policy probe would spawn a real host; proven separately in
                # `tests/test_lane_permission_posture.py`.
                mock.patch.object(
                    oc_runipd,
                    "observe_opencode_policy",
                    lambda *a, **k: lane_containment.evaluate_policy_observation(
                        None, {}, failure_reason="probe skipped in this test"
                    ),
                ),
            ):
                if module is oc_runipd:
                    module.run_opencode(
                        state, run_dir, item, plan, prompt, 1, work_dir=work_dir
                    )
                else:
                    module.run_agy_turn(
                        state, run_dir, item, prompt, 1, None, False, work_dir=work_dir
                    )
        self.assertTrue(envs, f"{module.__name__}.{launcher} spawned no child")
        return envs[-1]

    def test_the_marking_predicate_round_trips(self):
        """The value the drivers write is exactly the value the refusal predicate recognizes."""
        marked = {"PATH": "/usr/bin"}
        marked[LC.EXECUTION_ROLE_ENV] = LC.ROLE_WORKER
        self.assertTrue(LC.worker_role_active(marked))

        stripped = dict(marked)
        stripped.pop(LC.EXECUTION_ROLE_ENV, None)
        self.assertFalse(LC.worker_role_active(stripped))
        # Everything else survives: the env is explicit, not minimal.
        self.assertEqual(stripped["PATH"], "/usr/bin")

    def test_driver_own_process_is_not_worker_role(self):
        """The DRIVER's own environment must never be worker-marked, or `driver_begin` would refuse."""
        self.assertNotEqual(os.environ.get("AW_EXECUTION_ROLE"), "worker")
        self.assertFalse(LC.worker_role_active(os.environ))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
