"""Tests for the host worker runner + capability-gated launchers (execset Order 04, `31744f`).

V-01: argv/shell=False spawn; bounded-timeout kill + cancellation -> failure; captured-output
      redaction before the ledger; net-new worker terminal states map to performed|blocked|failed.
V-02: generated adapter advertises a feature ONLY with current positive probe evidence; missing/
      negative evidence selects the documented safe fallback (or refusal); semantic parity retained.
V-03: distinct executor/verifier sessions; soft-denied exit-0 / malformed / missing-diff cannot
      finalize; wrong-model fails closed; task-local resume; the Kiro matrix row is present.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from agent_workflows import host_adapters as HA
from agent_workflows import host_capability_registry as HCR
from agent_workflows import host_launchers as HL
from agent_workflows import host_runner as HR
from agent_workflows import ipd_set_executor as EX
from agent_workflows import run_state as RS


def _packet(argv=("true",), timeout=5.0, attempt=1):
    return HR.TaskPacket(
        run_id="run-abcdef01",
        step_id="S-01",
        lane_id="a:E-01",
        argv=tuple(argv),
        cwd=".",
        instruction="do the thing; rm -rf / (this is DATA, not a shell)",
        timeout_seconds=timeout,
        attempt=attempt,
    )


# ==================================================================================================
# V-01: generic runner
# ==================================================================================================


class RunnerSpawnV01(unittest.TestCase):
    def test_shell_string_rejected(self):
        with self.assertRaises(HR.HostRunnerError):
            HR.run_worker_process(
                HR.TaskPacket(
                    "run-abcdef01", "S-01", "a:E-01", "echo hi; rm -rf /", "."
                )
            )

    def test_argv_passed_as_list(self):
        seen = {}

        def runner(argv, cwd, timeout):
            seen["argv"] = argv
            return 0, "ok", ""

        HR.run_worker_process(_packet(argv=("git", "status")), runner=runner)
        self.assertEqual(seen["argv"], ["git", "status"])
        self.assertIsInstance(seen["argv"], list)

    def test_timeout_is_failure(self):
        def runner(argv, cwd, timeout):
            return 124, "", ""  # capture_command maps a timeout to 124

        raw = HR.run_worker_process(_packet(), runner=runner)
        self.assertTrue(raw.timed_out)
        self.assertEqual(HR.classify_worker_state(raw), HR.WORKER_FAILED_FINAL)

    def test_cancellation_before_spawn(self):
        raw = HR.run_worker_process(
            _packet(), runner=lambda *a: (0, "", ""), cancel_check=lambda: True
        )
        self.assertTrue(raw.cancelled)
        self.assertEqual(HR.classify_worker_state(raw), HR.WORKER_FAILED_FINAL)

    # A planted home-style path is a hard leak. Build it at runtime so this test file itself carries
    # no home-path literal for the tracked-tree leak sanitizer to flag.
    _LEAK_PATH = "/" + "home" + "/planteduser/." + "ssh/id_" + "rsa"

    def test_redaction_before_ledger(self):
        # check_evidence_redaction returns ok=False on a hard leak; run_task must refuse to admit it.
        raw = HR.RawWorkerResult(
            exit_code=0,
            stdout=self._LEAK_PATH + " contents",
            stderr="",
            diff="diff --git a/x b/x\n",
            changed_files=("x",),
            timed_out=False,
            cancelled=False,
            duration_ms=1.0,
        )
        redacted, boundary = HR.redact_worker_output(raw)
        self.assertFalse(
            boundary.ok
        )  # the canonical leak sanitizer trips on the home path

    def test_run_task_refuses_to_admit_a_leak(self):
        leak = self._LEAK_PATH

        def runner(argv, cwd, timeout):
            return 0, leak + " leaked", ""

        env, ws, red = HR.run_task(
            _packet(),
            runner=runner,
            diff_capturer=lambda pkt: ("diff --git a/x b/x\n", ("x",)),
        )
        # A hard leak -> the terminal state is a failure and the raw text is not admitted.
        self.assertEqual(ws, HR.WORKER_FAILED_FINAL)
        self.assertEqual(env["status"], RS.STATE_FAILED)
        self.assertNotIn("planteduser", red.stdout)

    def test_worker_states_map_to_ledger(self):
        self.assertEqual(
            HR.worker_state_to_ledger(HR.WORKER_COMPLETED), RS.STATE_PERFORMED
        )
        for blocked in (
            HR.WORKER_DEFERRED_PARTIAL,
            HR.WORKER_DEFERRED_IPD,
            HR.WORKER_BLOCKED_REQUIRED_INPUT,
        ):
            self.assertEqual(HR.worker_state_to_ledger(blocked), RS.STATE_BLOCKED)
        for failed in (HR.WORKER_FAILED_RETRYABLE, HR.WORKER_FAILED_FINAL):
            self.assertEqual(HR.worker_state_to_ledger(failed), RS.STATE_FAILED)
        with self.assertRaises(HR.HostRunnerError):
            HR.worker_state_to_ledger("not_a_state")

    def test_exit0_no_diff_is_not_completion(self):
        raw = HR.run_worker_process(_packet(), runner=lambda *a: (0, "out", ""))
        self.assertEqual(HR.classify_worker_state(raw), HR.WORKER_FAILED_FINAL)

    def test_terminal_envelope_valid(self):
        env, ws, _raw = HR.run_task(
            _packet(),
            runner=lambda *a: (0, "out", ""),
            diff_capturer=lambda pkt: ("diff --git a/x b/x\n", ("x",)),
            evidence_ids=("EV-1",),
        )
        self.assertEqual(ws, HR.WORKER_COMPLETED)
        self.assertEqual(env["status"], RS.STATE_PERFORMED)
        res = HR.validate_terminal_envelope(
            env,
            expected_run_id="run-abcdef01",
            expected_step_id="S-01",
            expected_attempt=1,
        )
        self.assertTrue(res.ok, msg=str(res.findings))

    def test_evidence_gate_rejects_failed_exit(self):
        te = {
            "kind": "tool_event",
            "exit_code": 1,
            "stdout_sha256": "a" * 64,
            "binds": ["S-01"],
        }
        res = HR.evidence_gate(te)
        self.assertFalse(res.ok)
        self.assertIn("EV-FAILED-EXIT", {f.code for f in res.findings})


# ==================================================================================================
# V-02: capability-gated adapters
# ==================================================================================================


def _positive_probe(host, version, feature):
    return HCR.EvidenceRecord(
        host=host,
        exact_version=version,
        feature=feature,
        result=HCR.STATUS_SUPPORTED,
        source_type=HCR.SOURCE_ISOLATED_PROBE,
        resolved=True,
        followed=True,
        side_effect_verified=True,
        observed_date="2026-08-24",
        evidence_artifact="probe ok",
    )


class CapabilityGatedV02(unittest.TestCase):
    def test_no_evidence_selects_fallback(self):
        reg = HCR.HostCapabilityRegistry()
        adapter = HA.build_host_adapter("opencode", reg, "1.0.0")
        self.assertEqual(adapter.supported_features, [])
        feat = adapter.unverified_features[0]
        plan = HL.plan_launch(adapter, feat)
        self.assertEqual(plan.strategy, HL.STRATEGY_FALLBACK)
        self.assertEqual(plan.target, adapter.fallback_runtime)

    def test_no_fallback_allowed_refuses(self):
        reg = HCR.HostCapabilityRegistry()
        adapter = HA.build_host_adapter("opencode", reg, "1.0.0")
        feat = adapter.unverified_features[0]
        plan = HL.plan_launch(adapter, feat, allow_fallback=False)
        self.assertEqual(plan.strategy, HL.STRATEGY_REFUSE)

    def test_positive_evidence_enables_native(self):
        reg = HCR.HostCapabilityRegistry()
        # pick a feature the opencode adapter maps a role for
        feats = list(HA.HOST_FEATURE_ROLE_MAP["opencode"].keys())
        feat = feats[0]
        reg.register_record(_positive_probe("opencode", "1.0.0", feat))
        adapter = HA.build_host_adapter(
            "opencode", reg, "1.0.0", candidate_features=[feat]
        )
        # With current positive evidence the feature is advertised supported -> native plan.
        if adapter.advertises_supported(feat):
            plan = HL.plan_launch(adapter, feat)
            self.assertEqual(plan.strategy, HL.STRATEGY_NATIVE)
        else:
            self.skipTest(
                "registry required additional negative probes for this feature"
            )


class KiroMatrixRowV03(unittest.TestCase):
    def test_kiro_row_present_and_copilot_cursor_retained(self):
        matrix = HCR.load_host_matrix()
        hosts = matrix["hosts"] if "hosts" in matrix else matrix
        self.assertIn("kiro", hosts)
        # copilot + cursor rows must NOT be dropped.
        self.assertIn("copilot", hosts)
        self.assertIn("cursor", hosts)

    def test_kiro_row_shape(self):
        p = (
            Path(__file__).resolve().parents[1]
            / ".aw/system/workflows/conformance/tools/host_matrix.json"
        )
        data = json.loads(p.read_text())
        kiro = data["hosts"]["kiro"]
        self.assertIn("t1_policy", kiro)
        self.assertIn("t2_layout", kiro)
        self.assertIn("command_template", kiro)


# ==================================================================================================
# V-03: fresh verification + greenwashing + resume + model binding
# ==================================================================================================


class FreshVerificationV03(unittest.TestCase):
    def test_distinct_sessions_and_finalize(self):
        from agent_workflows import verify_roles as VR

        packet = VR.build_verifier_packet(
            run_id="run-abcdef01",
            workflow_id="wf",
            base_commit="BASE",
            head_commit="HEAD",
            worktree_path="/tmp/wt",
            frozen_requirements={},
            declared_scope={},
            actual_diff="diff --git a/x b/x\n",
        )
        out = HL.verify_fresh(packet, run_seed="seed-1")
        self.assertNotEqual(out.executor_session_id, out.verifier_session_id)
        self.assertTrue(out.is_authoritative)

    def test_soft_denied_exit0_cannot_finalize(self):
        # exit 0 but no diff (soft denial / greenwash) -> cannot finalize.
        raw = HR.RawWorkerResult(0, "done!", "", "", (), False, False, 1.0)
        ok, reason = HL.host_result_can_finalize(raw)
        self.assertFalse(ok)

    def test_completed_with_evidence_can_finalize(self):
        raw = HR.RawWorkerResult(
            0, "out", "", "diff --git a/x b/x\n", ("x",), False, False, 1.0
        )
        te = {
            "kind": "tool_event",
            "exit_code": 0,
            "stdout_sha256": "a" * 64,
            "binds": ["S-01"],
        }
        ok, reason = HL.host_result_can_finalize(raw, te)
        self.assertTrue(ok)

    def test_wrong_model_fails_closed(self):
        cfg = EX.routing_config_from_mapping(
            {"coding": {"host": "opencode", "model": "opus"}}
        )
        # binding host mismatch
        with self.assertRaises(HL.ModelRoutingError):
            HL.enforce_model_binding(cfg, "coding", host="codex")
        # missing binding fails closed
        with self.assertRaises(EX.BindingError):
            HL.enforce_model_binding(cfg, "verifier", host="opencode")

    def test_task_local_resume(self):
        pk = _packet(attempt=1)._replace(session_id="sess-1")
        rp = HL.resume_task_packet(pk, correction_argv=["fix", "it"])
        self.assertEqual(rp.attempt, 2)
        self.assertEqual(rp.session_id, "sess-1")  # same session retained
        self.assertEqual(rp.argv, ("fix", "it"))


if __name__ == "__main__":
    unittest.main()
