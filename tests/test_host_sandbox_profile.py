"""Self-tests for the OPTIONAL hardened OS-sandbox execution profile (wtiso-07 `1o4eif`).

Covers x03wgn Section 8 "Phase 6" with Sections 1, 4 and 6 Layer 4:

- E-01/E-02 the host capability contract and its EXECUTED (never inspected) probe;
- E-03/E-04 the writable/read-only/inaccessible partition and the read-only git common dir;
- E-05 wrapping the worker argv while leaving the default launch path untouched;
- E-06/E-10 fail-closed dispatch when hard mode is requested but unavailable;
- E-07 read-only discovery then write execution;
- E-08/E-09 the two ADVERSARIAL guarantees: the OS (not policy) denies a worker write to the
  control root / main worktree / sibling lane, and denies git-common-dir mutation while the
  DRIVER's own commit still succeeds.

The adversarial tests are skipped where the EXECUTED probe says the host cannot enforce a
sandbox. That skip is an honest CI outcome, never acceptance evidence: per the plan, a skip
leaves the guarantee UNVERIFIED on that machine.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import host_sandbox_profile as hsp
from agent_workflows.host_sandbox_profile import (
    HardModeUnavailableError,
    HostSandboxCapabilities,
    SandboxPlan,
    SandboxProfileError,
    build_sandbox_plan,
    detect_host_capabilities,
    enter_sandbox,
    landlock_bootstrap_source,
    run_discovery_then_execution,
    select_execution_profile,
)

CONTRACT_FIELDS = (
    "supports_inline_permissions",
    "supports_read_only_phase",
    "supports_session_resume",
    "emits_structured_tool_events",
    "emits_child_permission_events",
    "supports_process_tree_kill",
    "supports_os_sandbox",
)


def _linux_userns_available() -> bool:
    """The SAME executed-attempt probe `detect_host_capabilities` uses (E-02/E-08).

    Deliberately NOT a sysctl or binary-presence check: on the host this phase was written
    on, `unprivileged_userns_clone=1`, `max_user_namespaces=514277`, and both `unshare` and
    `bwrap` were installed, yet no user namespace could be created. Sharing one probe makes
    it impossible for the skip decision and the reported capability to disagree.
    """
    return hsp.os_sandbox_available()


_SANDBOX_REASON = (
    "requires the certified Linux OS sandbox; this host's EXECUTED probe reports it "
    "cannot enforce one, so the OS-denial guarantee is UNVERIFIED here: "
)


def _skip_reason() -> str:
    return _SANDBOX_REASON + repr(hsp.os_sandbox_probe_notes())


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False
    )


class CapabilityContractTests(unittest.TestCase):
    """E-01: the x03wgn Layer 4 contract, fail-closed by default."""

    def test_every_contract_field_exists_and_defaults_false(self):
        caps = HostSandboxCapabilities()
        for name in CONTRACT_FIELDS:
            with self.subTest(field=name):
                self.assertIs(
                    getattr(caps, name),
                    False,
                    f"{name} must default False so an unprobed host claims nothing",
                )

    def test_to_dict_snapshots_the_contract(self):
        snap = HostSandboxCapabilities(platform="linux").to_dict()
        for name in CONTRACT_FIELDS:
            self.assertIn(name, snap)
        self.assertEqual(snap["platform"], "linux")


class CapabilityProbeTests(unittest.TestCase):
    """E-02: the probe must ATTEMPT, not inspect."""

    def setUp(self):
        self._saved_cache = hsp._SANDBOX_PROBE_CACHE
        self._saved_ladder = hsp._SANDBOX_LADDER

    def tearDown(self):
        hsp._SANDBOX_PROBE_CACHE = self._saved_cache
        hsp._SANDBOX_LADDER = self._saved_ladder

    def test_unproven_platforms_report_no_sandbox(self):
        for platform in ("windows", "darwin", "win32", "aix"):
            with self.subTest(platform=platform):
                caps = detect_host_capabilities("opencode", platform)
                self.assertFalse(caps.supports_os_sandbox)
                self.assertIsNone(caps.sandbox_mechanism)

    def test_report_matches_the_actual_attempt(self):
        """The reported capability must equal what a real jail attempt achieves."""
        reported = detect_host_capabilities("opencode").supports_os_sandbox
        hsp._SANDBOX_PROBE_CACHE = None
        actually_worked = hsp._probe_linux_sandbox(force=True)[0] is not None
        self.assertEqual(
            reported,
            actually_worked,
            "supports_os_sandbox must reflect an EXECUTED jail attempt",
        )

    def test_probe_is_not_sysctl_or_binary_presence(self):
        """Forcing every ATTEMPT to fail must flip the capability to False.

        The permissive sysctls and the installed binaries are untouched, so a probe that
        merely inspected them would still report True. This is the fail-OPEN direction the
        design forbids.
        """
        hsp._SANDBOX_PROBE_CACHE = None
        hsp._SANDBOX_LADDER = tuple(
            (name, lambda: (False, "attempt forced to fail"))
            for name, _ in self._saved_ladder
        )
        caps = detect_host_capabilities("opencode")
        self.assertFalse(caps.supports_os_sandbox)
        self.assertIsNone(caps.sandbox_mechanism)
        if Path("/proc/sys/user/max_user_namespaces").exists():
            raw = Path("/proc/sys/user/max_user_namespaces").read_text().strip()
            self.assertTrue(
                raw.isdigit(),
                "sysctl remained readable, so an inspection-based probe would have lied",
            )

    def test_a_raising_probe_is_treated_as_unavailable(self):
        def boom():
            raise RuntimeError("probe exploded")

        hsp._SANDBOX_PROBE_CACHE = None
        hsp._SANDBOX_LADDER = (("landlock", boom),)
        self.assertFalse(detect_host_capabilities("opencode").supports_os_sandbox)


class SandboxPlanTests(unittest.TestCase):
    """E-03 / E-04: the partition and the read-only git common dir."""

    def _paths(self, root: Path) -> dict:
        for rel in (
            "main",
            "main/.aw/worktrees/lane",
            "main/.aw/worktrees/lane/.scratch",
            "main/.aw/worktrees/sibling",
            "control",
            "candidate",
            "creds",
            "main/.git",
        ):
            (root / rel).mkdir(parents=True, exist_ok=True)
        return {
            "lane_worktree": root / "main/.aw/worktrees/lane",
            "lane_scratch": root / "main/.aw/worktrees/lane/.scratch",
            "control_root": root / "control",
            "main_worktree": root / "main",
            "sibling_lane_roots": [root / "main/.aw/worktrees/sibling"],
            "integration_candidate": root / "candidate",
            "credential_paths": [root / "creds"],
            "git_common_dir": root / "main/.git",
            "toolchain_roots": ["/usr", "/lib"],
        }

    def test_build_sandbox_plan_partition(self):
        """V-03: writable is exactly the lane pair; every central path is inaccessible."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            p = self._paths(root)
            plan = build_sandbox_plan(**p)

            self.assertEqual(
                set(plan.writable),
                {str(p["lane_worktree"].resolve()), str(p["lane_scratch"].resolve())},
                "WRITABLE must be exactly the lane worktree + lane scratch",
            )
            for label, path in (
                ("control_root", p["control_root"]),
                ("main_worktree", p["main_worktree"]),
                ("sibling_lane", p["sibling_lane_roots"][0]),
                ("integration_candidate", p["integration_candidate"]),
                ("credentials", p["credential_paths"][0]),
            ):
                canon = str(Path(path).resolve())
                with self.subTest(path=label):
                    self.assertIn(canon, plan.inaccessible)
                    self.assertNotIn(canon, plan.writable)
                    self.assertNotIn(canon, plan.readonly)

    def test_git_common_dir_readonly_and_driver_owns_mutation(self):
        """V-04: the common dir is read-only, never writable; a writable one is refused."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            p = self._paths(root)
            plan = build_sandbox_plan(**p)
            common = str(p["git_common_dir"].resolve())

            self.assertIn(common, plan.readonly)
            self.assertNotIn(common, plan.writable)
            self.assertTrue(plan.driver_owns_git_mutation)

            bad = SandboxPlan(
                writable=[common],
                readonly=[],
                inaccessible=[],
                git_common_dir=common,
            )
            with self.assertRaises(SandboxProfileError):
                bad.validate()

    def test_driver_must_own_git_mutation(self):
        with self.assertRaises(SandboxProfileError):
            SandboxPlan(
                writable=["/tmp/lane"],
                git_common_dir="/tmp/main/.git",
                driver_owns_git_mutation=False,
            ).validate()

    def test_discovery_variant_makes_the_product_tree_readonly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            p = self._paths(root)
            plan = build_sandbox_plan(product_tree_readonly=True, **p)
            lane = str(p["lane_worktree"].resolve())
            self.assertNotIn(lane, plan.writable)
            self.assertIn(lane, plan.readonly)
            self.assertIn(str(p["lane_scratch"].resolve()), plan.writable)


class EnterSandboxTests(unittest.TestCase):
    """E-05: argv wrapping, and the default path left alone."""

    def test_enter_sandbox_wraps_argv_and_default_path_unchanged(self):
        """V-05: the jail launcher is prepended; the default launch argv is untouched."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            lane = root / "lane"
            scratch = lane / ".scratch"
            scratch.mkdir(parents=True)
            plan = build_sandbox_plan(
                lane_worktree=lane,
                lane_scratch=scratch,
                main_worktree=root / "main",
                control_root=root / "control",
                toolchain_roots=["/usr"],
            )
            argv = ["opencode", "run", "--dir", str(lane)]

            caps = HostSandboxCapabilities(
                platform="linux",
                supports_os_sandbox=True,
                sandbox_mechanism="landlock",
            )
            wrapped = enter_sandbox(argv, plan, caps, cwd=lane, scratch_dir=scratch)
            self.assertNotEqual(wrapped, argv, "hardened argv must be wrapped")
            self.assertEqual(wrapped[0], sys.executable)
            self.assertTrue(
                wrapped[1].endswith("aw-landlock-bootstrap.py"),
                f"expected the landlock bootstrap launcher, got {wrapped!r}",
            )
            boot = Path(wrapped[1]).read_text(encoding="utf-8")
            self.assertIn(str(lane.resolve()), boot)
            self.assertIn("landlock_restrict_self", boot)
            self.assertIn(repr(argv), boot, "the real worker argv must be exec'd")

            bwrap_caps = HostSandboxCapabilities(
                platform="linux",
                supports_os_sandbox=True,
                sandbox_mechanism="bwrap",
            )
            bwrapped = enter_sandbox(argv, plan, bwrap_caps, cwd=lane)
            self.assertEqual(bwrapped[0], "bwrap")
            self.assertIn("--unshare-user", bwrapped)
            self.assertEqual(bwrapped[-len(argv) :], argv)

            # DEFAULT PATH: `select_execution_profile` returns "default" and the driver's
            # seam returns argv unchanged - byte for byte, same list.
            from agent_workflows.oc_runipd import _apply_execution_profile

            state = {"options": {}, "repo": str(root), "run_id": "r1"}
            unchanged = _apply_execution_profile(
                state, {"id6": "abc123"}, list(argv), str(lane), str(lane)
            )
            self.assertEqual(unchanged, argv)

    def test_enter_sandbox_refuses_without_capability(self):
        plan = SandboxPlan(writable=["/tmp/lane"], git_common_dir="/tmp/main/.git")
        with self.assertRaises(HardModeUnavailableError):
            enter_sandbox(["true"], plan, HostSandboxCapabilities(platform="linux"))


class ProfileDispatchTests(unittest.TestCase):
    """E-06 / E-10: fail-closed dispatch. Runs on EVERY platform (no skipif)."""

    def test_hard_mode_requested_without_capability_fails_closed(self):
        """V-10: hardened without capability RAISES; no unsandboxed worker is spawned."""
        caps = HostSandboxCapabilities(platform="windows", supports_os_sandbox=False)
        with self.assertRaises(HardModeUnavailableError):
            select_execution_profile("hardened", caps)

        # And the driver seam must not fall through to a launch: patch Popen so any spawn
        # would be recorded, then prove the raise happened with nothing spawned.
        import agent_workflows.oc_runipd as oc

        spawned: list = []

        class _Boom:
            def __init__(self, *a, **k):
                spawned.append(a)
                raise AssertionError("an unsandboxed worker must NEVER be spawned")

        saved_popen = subprocess.Popen
        saved_detect = oc.detect_host_capabilities
        try:
            subprocess.Popen = _Boom  # type: ignore[assignment]
            oc.detect_host_capabilities = lambda host: caps  # type: ignore[assignment]
            with self.assertRaises(HardModeUnavailableError):
                oc._apply_execution_profile(
                    {
                        "options": {"execution_profile": "hardened"},
                        "repo": "/tmp",
                        "run_id": "r",
                    },
                    {"id6": "abc123"},
                    ["opencode", "run"],
                    "/tmp",
                    "/tmp/lane",
                )
        finally:
            subprocess.Popen = saved_popen  # type: ignore[assignment]
            oc.detect_host_capabilities = saved_detect  # type: ignore[assignment]
        self.assertEqual(spawned, [], "no process may be spawned when hard mode fails")

    def test_default_and_supported_hardened_dispatch(self):
        self.assertEqual(
            select_execution_profile("default", HostSandboxCapabilities()), "default"
        )
        self.assertEqual(
            select_execution_profile(None, HostSandboxCapabilities()), "default"
        )
        self.assertEqual(
            select_execution_profile(
                "hardened", HostSandboxCapabilities(supports_os_sandbox=True)
            ),
            "hardened",
        )

    def test_unknown_profile_is_refused(self):
        with self.assertRaises(SandboxProfileError):
            select_execution_profile(
                "semi-hardened", HostSandboxCapabilities(supports_os_sandbox=True)
            )

    def test_module_publishes_its_guarantees(self):
        doc = (hsp.__doc__ or "").lower()
        for token in ("read-only", "driver", "linux", "git common", "void"):
            self.assertIn(token, doc, f"published guarantees must mention {token!r}")


class DiscoveryThenExecutionTests(unittest.TestCase):
    """E-07: read-only discovery, then write execution."""

    def test_discovery_then_execution_barrier(self):
        """V-07: no barrier is CLAIMED without the capability; with it, phase 1 is read-only."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            lane = root / "lane"
            scratch = lane / ".scratch"
            scratch.mkdir(parents=True)
            (lane / "product.txt").write_text("original\n", encoding="utf-8")

            incapable = HostSandboxCapabilities(
                platform="linux",
                supports_read_only_phase=False,
                emits_structured_tool_events=True,
            )
            result = run_discovery_then_execution(
                lane_worktree=lane,
                lane_scratch=scratch,
                capabilities=incapable,
                run_discovery=lambda plan: self.fail("must not run without a barrier"),
                validate_submission=lambda s: True,
                run_execution=lambda plan, s: self.fail("must not execute"),
            )
            self.assertFalse(result.barrier_enforced)
            self.assertIn("advisory", result.reason.lower())

            capable = HostSandboxCapabilities(
                platform="linux",
                supports_read_only_phase=True,
                emits_structured_tool_events=True,
                supports_os_sandbox=True,
                sandbox_mechanism="landlock",
            )
            seen: dict = {}

            def discovery(plan):
                seen["discovery"] = plan
                return {"scope": ["product.txt"]}

            def execution(plan, submission):
                seen["execution"] = plan
                return "executed"

            ok = run_discovery_then_execution(
                lane_worktree=lane,
                lane_scratch=scratch,
                capabilities=capable,
                run_discovery=discovery,
                validate_submission=lambda s: isinstance(s, dict) and "scope" in s,
                run_execution=execution,
                toolchain_roots=["/usr"],
            )
            self.assertTrue(ok.barrier_enforced)
            self.assertTrue(ok.discovery_validated)
            self.assertEqual(ok.execution_result, "executed")
            lane_c = str(lane.resolve())
            self.assertNotIn(lane_c, seen["discovery"].writable)
            self.assertIn(lane_c, seen["discovery"].readonly)
            self.assertIn(lane_c, seen["execution"].writable)

    def test_prose_only_submission_does_not_authorize_writes(self):
        """A prose claim is insufficient (x03wgn Layer 4 step 2)."""
        with tempfile.TemporaryDirectory() as tmp:
            lane = Path(tmp).resolve() / "lane"
            scratch = lane / ".scratch"
            scratch.mkdir(parents=True)
            caps = HostSandboxCapabilities(
                platform="linux",
                supports_read_only_phase=True,
                emits_structured_tool_events=True,
            )
            result = run_discovery_then_execution(
                lane_worktree=lane,
                lane_scratch=scratch,
                capabilities=caps,
                run_discovery=lambda plan: "I promise I analyzed the scope.",
                validate_submission=lambda s: isinstance(s, dict),
                run_execution=lambda plan, s: self.fail(
                    "product writes must NOT be authorized on an invalid submission"
                ),
                toolchain_roots=["/usr"],
            )
            self.assertTrue(result.barrier_enforced)
            self.assertFalse(result.discovery_validated)

    @unittest.skipIf(not _linux_userns_available(), _SANDBOX_REASON)
    def test_phase_one_product_write_is_denied_by_os(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            lane = root / "lane"
            scratch = lane / ".scratch"
            scratch.mkdir(parents=True)
            product = lane / "product.txt"
            product.write_text("original\n", encoding="utf-8")

            plan = build_sandbox_plan(
                lane_worktree=lane,
                lane_scratch=scratch,
                product_tree_readonly=True,
                toolchain_roots=hsp._default_toolchain_roots() + [str(root)],
            )
            caps = detect_host_capabilities("opencode")
            script = scratch / "attempt.py"
            script.write_text(
                "open({!r}, 'w').write('worker overwrote the product')\n".format(
                    str(product)
                ),
                encoding="utf-8",
            )
            argv = enter_sandbox(
                [sys.executable, str(script)], plan, caps, scratch_dir=scratch
            )
            proc = subprocess.run(argv, capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(product.read_text(encoding="utf-8"), "original\n")


@unittest.skipIf(not _linux_userns_available(), _SANDBOX_REASON)
class AdversarialOsDenialTests(unittest.TestCase):
    """E-08 / E-09: the OS - not policy - denies the write."""

    def test_hardened_worker_write_to_control_main_sibling_denied_by_os(self):
        """V-08: control-root, main-worktree, and sibling-lane writes are OS-denied."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            main = root / "main"
            lane = main / ".aw/worktrees/lane"
            sibling = main / ".aw/worktrees/sibling"
            control = root / "control"
            scratch = lane / ".scratch"
            for d in (lane, sibling, control, scratch):
                d.mkdir(parents=True, exist_ok=True)

            targets = {
                "control": control / "run-state.json",
                "main": main / "PRODUCT.txt",
                "sibling": sibling / "stolen.txt",
            }
            plan = build_sandbox_plan(
                lane_worktree=lane,
                lane_scratch=scratch,
                control_root=control,
                main_worktree=main,
                sibling_lane_roots=[sibling],
                toolchain_roots=hsp._default_toolchain_roots(),
            )
            caps = detect_host_capabilities("opencode")

            attempt = scratch / "attempt.py"
            attempt.write_text(
                "import json, sys\n"
                f"targets = {{k: v for k, v in {{'control': {str(targets['control'])!r},"
                f" 'main': {str(targets['main'])!r},"
                f" 'sibling': {str(targets['sibling'])!r}}}.items()}}\n"
                "out = {}\n"
                "for name, path in targets.items():\n"
                "    try:\n"
                "        open(path, 'w').write('owned by a malicious worker')\n"
                "        out[name] = 'WROTE'\n"
                "    except OSError as exc:\n"
                "        out[name] = 'DENIED:%s' % exc.errno\n"
                "sys.stdout.write(json.dumps(out))\n",
                encoding="utf-8",
            )
            # Sanity: the lane itself IS writable, so a denial elsewhere is a real
            # boundary rather than a broken interpreter.
            argv = enter_sandbox(
                [sys.executable, str(attempt)], plan, caps, scratch_dir=scratch
            )
            proc = subprocess.run(argv, capture_output=True, text=True)
            self.assertEqual(
                proc.returncode, 0, f"probe did not run: {proc.stderr[-800:]}"
            )
            import json as _json

            observed = _json.loads(proc.stdout)
            for name in ("control", "main", "sibling"):
                with self.subTest(target=name):
                    self.assertTrue(
                        observed[name].startswith("DENIED:"),
                        f"{name} write was NOT denied by the OS: {observed[name]}",
                    )
                    self.assertEqual(
                        observed[name],
                        "DENIED:%d" % 13,
                        "expected EACCES (13) from the kernel",
                    )
                    self.assertFalse(
                        targets[name].exists(),
                        f"{name} target must not exist after a denied write",
                    )

    def test_hardened_worker_git_common_dir_mutation_denied(self):
        """V-09: ref/hook/config mutation is denied; the DRIVER's commit still succeeds."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            main = root / "main"
            main.mkdir(parents=True)
            self.assertEqual(_git("init", "-q", ".", cwd=main).returncode, 0)
            _git("config", "user.email", "driver@example.invalid", cwd=main)
            _git("config", "user.name", "driver", cwd=main)
            (main / "f.txt").write_text("base\n", encoding="utf-8")
            _git("add", "f.txt", cwd=main)
            self.assertEqual(_git("commit", "-qm", "base", cwd=main).returncode, 0)

            lane = main / ".aw/worktrees/lane"
            lane.parent.mkdir(parents=True, exist_ok=True)
            self.assertEqual(
                _git(
                    "worktree",
                    "add",
                    "-q",
                    "-b",
                    "aw/lane/test",
                    str(lane),
                    "HEAD",
                    cwd=main,
                ).returncode,
                0,
            )
            scratch = lane / ".scratch"
            scratch.mkdir(parents=True, exist_ok=True)

            common = Path(
                _git("rev-parse", "--git-common-dir", cwd=lane).stdout.strip()
            )
            if not common.is_absolute():
                common = (lane / common).resolve()
            common = common.resolve()

            hook = common / "hooks" / "pre-commit"
            hook.parent.mkdir(parents=True, exist_ok=True)
            hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            config_before = (common / "config").read_bytes()
            hook_before = hook.read_bytes()
            refs_before = _git(
                "for-each-ref", "--format=%(refname) %(objectname)", cwd=main
            ).stdout

            plan = build_sandbox_plan(
                lane_worktree=lane,
                lane_scratch=scratch,
                main_worktree=main,
                git_common_dir=common,
                toolchain_roots=hsp._default_toolchain_roots() + [str(root)],
            )
            self.assertIn(str(common), plan.readonly)
            self.assertNotIn(str(common), plan.writable)
            caps = detect_host_capabilities("opencode")

            attempt = scratch / "attempt.py"
            attempt.write_text(
                "import json, subprocess, sys\n"
                f"lane = {str(lane)!r}\n"
                f"hook = {str(hook)!r}\n"
                "out = {}\n"
                "def run(name, args):\n"
                "    p = subprocess.run(['git', '-C', lane] + args,"
                " capture_output=True, text=True)\n"
                "    out[name] = p.returncode\n"
                "out['read_status'] = subprocess.run(['git','-C',lane,'status',"
                "'--porcelain'], capture_output=True, text=True).returncode\n"
                "run('update_ref', ['update-ref', 'refs/heads/evil', 'HEAD'])\n"
                "run('config', ['config', 'core.hooksPath', '/tmp/evil'])\n"
                "run('git_add', ['add', '-A'])\n"
                "try:\n"
                "    open(hook, 'w').write('#!/bin/sh\\nexfiltrate\\n')\n"
                "    out['hook_write'] = 'WROTE'\n"
                "except OSError as exc:\n"
                "    out['hook_write'] = 'DENIED:%s' % exc.errno\n"
                "sys.stdout.write(json.dumps(out))\n",
                encoding="utf-8",
            )
            argv = enter_sandbox(
                [sys.executable, str(attempt)],
                plan,
                caps,
                cwd=lane,
                scratch_dir=scratch,
            )
            proc = subprocess.run(argv, capture_output=True, text=True)
            self.assertEqual(
                proc.returncode, 0, f"probe did not run: {proc.stderr[-800:]}"
            )
            import json as _json

            observed = _json.loads(proc.stdout)

            # The worker can still READ git (the common dir is read-only, not inaccessible),
            # which proves the denials below are about WRITE, not a broken toolchain.
            self.assertEqual(
                observed["read_status"], 0, f"git read must still work: {observed}"
            )
            for name in ("update_ref", "config", "git_add"):
                with self.subTest(op=name):
                    self.assertNotEqual(
                        observed[name], 0, f"{name} must be DENIED, got rc=0"
                    )
            self.assertTrue(str(observed["hook_write"]).startswith("DENIED:"))

            # Nothing in the common dir changed.
            self.assertEqual(hook.read_bytes(), hook_before, "hook bytes changed")
            self.assertEqual(
                (common / "config").read_bytes(), config_before, "config changed"
            )
            self.assertEqual(
                _git(
                    "for-each-ref", "--format=%(refname) %(objectname)", cwd=main
                ).stdout,
                refs_before,
                "refs changed despite a read-only common dir",
            )

            # THE DRIVER (unsandboxed) owns git mutation, and it still works.
            (lane / "f.txt").write_text("driver edit\n", encoding="utf-8")
            self.assertEqual(_git("add", "f.txt", cwd=lane).returncode, 0)
            self.assertEqual(
                _git(
                    "-c",
                    "user.email=driver@example.invalid",
                    "-c",
                    "user.name=driver",
                    "commit",
                    "-qm",
                    "driver-owned commit",
                    cwd=lane,
                ).returncode,
                0,
            )
            oid = _git("rev-parse", "HEAD", cwd=lane).stdout.strip()
            self.assertEqual(
                _git("cat-file", "-e", oid, cwd=main).returncode,
                0,
                "the driver's lane commit must be reachable",
            )


class LandlockBootstrapTests(unittest.TestCase):
    """The generated bootstrap must be syntactically valid and self-restricting."""

    def test_bootstrap_source_compiles_and_restricts_before_exec(self):
        src = landlock_bootstrap_source(
            writable=["/tmp/lane"], readonly=["/usr"], argv=["true"], cwd="/tmp"
        )
        compile(src, "<bootstrap>", "exec")
        self.assertLess(
            src.index("landlock_restrict_self"),
            src.index("os.execvp"),
            "the ruleset must be enforced BEFORE the worker image is exec'd",
        )


if __name__ == "__main__":
    unittest.main()
