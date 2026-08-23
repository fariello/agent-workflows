"""Self-tests for generated Agent Skills, host adapters, and the agy fresh verifier.

awoptimize Order 11 (`bmd1ur`) E-05 validates E-01..E-04:
- Generated-artifact + semantic-digest-parity (E-01).
- Per-host adapter metadata gated by the Order-10 registry; reuse (not fork) of the
  engine.py shim generator; role/permission mapping; external-runtime fallback (E-02).
- Discovery diagnostics + skill-authority restriction; disabling a skill leaves the
  explicit runtime invocation usable (E-03).
- agy fresh-session verifier doubles: distinct session identity + Order-08 packet; the
  same-session audit is diagnostic and cannot finalize (E-04).
- Security tests: local-server loopback/auth, permission denial, external-path refusal
  (assert_contained / assert_isolated_base), secret redaction.

Pure stdlib unittest; no live host/agy/network probes.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_verifier as av
from agent_workflows import engine
from agent_workflows import host_adapters as ha
from agent_workflows import host_capability_registry as hcr
from agent_workflows import verify_roles
from agent_workflows.run_ledger_store import RedactionPolicy


# --------------------------------------------------------------------------------------------------
# Shared fixtures / builders
# --------------------------------------------------------------------------------------------------


def make_workflow(
    command="assess",
    body=".aw/system/workflows/assess/HARNESS.md",
    description="Assess a single concern deeply and write an IPD",
    lens="",
    arg_hint="",
):
    return engine.Workflow(
        command=command,
        body=body,
        description=description,
        lens=lens,
        arg_hint=arg_hint,
    )


def make_supported_record(host, version, feature):
    """Build a proven-positive EvidenceRecord that query_capability will mark supported."""
    return hcr.EvidenceRecord(
        host=host,
        exact_version=version,
        feature=feature,
        probe_variant="default",
        result=hcr.STATUS_SUPPORTED,
        source_type=hcr.SOURCE_ISOLATED_PROBE,
        evidence_artifact="PROBE-OK-example.txt",
        resolved=True,
        followed=True,
        side_effect_verified=True,
        diagnostic_evidence="probe resolved and followed with nonce side effect",
    )


def make_verifier_packet(run_id="run-deadbeef01"):
    return verify_roles.build_verifier_packet(
        run_id=run_id,
        workflow_id="assess",
        base_commit="a" * 40,
        head_commit="b" * 40,
        worktree_path="/tmp/isolated-worktree",
        frozen_requirements={"must": ["Do the thing"]},
        declared_scope={"allowed_paths": ["agent_workflows/*"]},
        actual_diff="diff --git a/x.py b/x.py\n+ added",
    )


# --------------------------------------------------------------------------------------------------
# E-01: skill package generation + semantic digest parity
# --------------------------------------------------------------------------------------------------


class SkillPackageTests(unittest.TestCase):
    def setUp(self):
        self.workflow = make_workflow()
        self.pkg = ha.build_skill_package(self.workflow)

    def test_generated_skill_passes_format_validation(self):
        findings = ha.validate_skill_package(self.pkg)
        self.assertEqual(findings, [], f"unexpected validation findings: {findings}")

    def test_trigger_description_distinguishes_use_vs_non_use(self):
        self.assertIn("Use when", self.pkg.trigger_description)
        self.assertIn("Do not use", self.pkg.trigger_description)

    def test_resource_references_resolve_within_package(self):
        files = self.pkg.to_files()
        for ref in self.pkg.resource_paths():
            self.assertIn(ref, files, f"resource ref {ref} does not resolve")

    def test_main_file_meets_budget(self):
        self.assertTrue(self.pkg.within_budget())
        self.assertLessEqual(self.pkg.main_file_bytes(), self.pkg.main_budget_bytes)

    def test_budget_violation_is_detected(self):
        # Falsifiable: a tiny budget must FAIL validation.
        tiny = ha.build_skill_package(self.workflow, main_budget_bytes=10)
        findings = ha.validate_skill_package(tiny)
        self.assertTrue(
            any("exceeds budget" in f for f in findings),
            f"expected budget violation, got {findings}",
        )

    def test_semantic_digest_parity_deterministic_and_matches_scheme(self):
        # Same workflow -> same digest (deterministic); digest matches workflow_profile scheme.
        again = ha.build_skill_package(self.workflow)
        self.assertEqual(self.pkg.semantic_digest, again.semantic_digest)
        self.assertEqual(
            self.pkg.semantic_digest,
            ha.compute_workflow_semantic_digest(self.workflow),
        )

    def test_semantic_digest_changes_when_semantics_change(self):
        other = make_workflow(
            command="verify", body=".aw/system/workflows/verify/HARNESS.md"
        )
        other_pkg = ha.build_skill_package(other)
        self.assertNotEqual(self.pkg.semantic_digest, other_pkg.semantic_digest)

    def test_router_carries_digest_and_explicit_invocation_not_inlined_body(self):
        self.assertIn(self.pkg.semantic_digest, self.pkg.main_file_content)
        self.assertIn(self.pkg.explicit_invocation, self.pkg.main_file_content)

    def test_deterministic_script_verifier_has_direct_test(self):
        # The generated deterministic script must be a real, testable module: exec it.
        script = next(r for r in self.pkg.resources if r.kind == "script")
        ns: dict = {}
        exec(compile(script.content, script.relative_path, "exec"), ns)
        self.assertTrue(ns["verify"](self.pkg.semantic_digest))
        self.assertFalse(ns["verify"]("not-the-digest"))
        self.assertEqual(ns["main"](["prog", self.pkg.semantic_digest]), 0)
        self.assertEqual(ns["main"](["prog", "wrong"]), 1)


# --------------------------------------------------------------------------------------------------
# E-02: host adapters gated by the Order-10 registry, reuse of engine shim generator
# --------------------------------------------------------------------------------------------------


class HostAdapterTests(unittest.TestCase):
    def setUp(self):
        self.registry = hcr.HostCapabilityRegistry()

    def test_unverified_capability_not_advertised_as_supported(self):
        # Empty registry -> everything unverified -> nothing advertised supported.
        adapter = ha.build_host_adapter(
            "opencode", self.registry, exact_version="1.0.0"
        )
        self.assertEqual(adapter.supported_features, [])
        self.assertTrue(adapter.unverified_features)
        for feat in adapter.unverified_features:
            self.assertFalse(adapter.advertises_supported(feat))
            self.assertIn(feat, adapter.capability_reasons)

    def test_registry_promotion_advertises_supported(self):
        rec = make_supported_record("opencode", "1.0.0", "command")
        self.registry.register_record(rec)
        adapter = ha.build_host_adapter(
            "opencode",
            self.registry,
            exact_version="1.0.0",
            candidate_features=["command", "subagent"],
        )
        self.assertIn("command", adapter.supported_features)
        self.assertNotIn("command", adapter.unverified_features)
        # A feature with no evidence stays unverified.
        self.assertIn("subagent", adapter.unverified_features)

    def test_role_mapping_correct(self):
        self.assertEqual(
            ha.map_feature_to_role("opencode", "subagent"), ha.ROLE_ISOLATED_EXECUTOR
        )
        self.assertEqual(
            ha.map_feature_to_role("codex", "exec"), ha.ROLE_NONINTERACTIVE_RUNTIME
        )
        self.assertIsNone(ha.map_feature_to_role("codex", "subagent"))

    def test_external_runtime_fallback_when_feature_absent(self):
        # codex has no isolated_executor native feature -> falls back to runtime coordination.
        target = ha.resolve_role_target("codex", ha.ROLE_ISOLATED_EXECUTOR)
        self.assertEqual(target, ha.HOST_NONINTERACTIVE_RUNTIME["codex"])
        # opencode DOES have a native isolated executor.
        self.assertEqual(
            ha.resolve_role_target("opencode", ha.ROLE_ISOLATED_EXECUTOR), "subagent"
        )

    def test_reuses_engine_shim_generator_not_forked(self):
        # The module must extend, not fork: same symbols, and the bundle's shims are
        # byte-identical to engine.generate_shim_members output.
        self.assertIs(ha.generate_shim_members, engine.generate_shim_members)
        self.assertIs(ha.shim_body, engine.shim_body)
        self.assertEqual(ha.COMMAND_SHIM_DIRS, engine.COMMAND_SHIM_DIRS)

        source_root = _find_source_root()
        workflows = engine.parse_manifest(source_root)
        bundle = ha.generate_adapter_bundle(workflows, source_root, self.registry)
        expected = engine.generate_shim_members(
            workflows, source_root, target_layout="aw"
        )
        self.assertEqual(bundle.shims, expected)
        # Every generated shim is grammatically valid for its host (reused validator).
        for path, content in bundle.shims.items():
            if path.endswith("README.md"):
                continue
            tool = "claude" if path.startswith(".claude") else "opencode"
            self.assertTrue(
                ha.validate_shim_grammar(content, tool),
                f"invalid shim grammar for {path}",
            )

    def test_support_table_never_exceeds_recorded_claim(self):
        rec = make_supported_record("opencode", "1.0.0", "command")
        self.registry.register_record(rec)
        adapters = {
            "opencode": ha.build_host_adapter(
                "opencode",
                self.registry,
                "1.0.0",
                candidate_features=["command", "subagent"],
            ),
        }
        table = ha.build_support_table(adapters)
        self.assertIn("| opencode | 1.0.0 | command | router | supported |", table)
        # subagent had no evidence -> must show unverified, never supported.
        self.assertIn("unverified", table)
        self.assertIn("subagent", table)


# --------------------------------------------------------------------------------------------------
# E-03: discovery diagnostics + skill-authority restriction
# --------------------------------------------------------------------------------------------------


class DiscoveryPolicyTests(unittest.TestCase):
    def test_complex_workflow_becomes_skill_entry_point(self):
        lensed = make_workflow(
            command="assess", lens=".aw/system/workflows/assess/lenses/security.md"
        )
        self.assertEqual(
            ha.classify_discovery_policy(lensed), ha.POLICY_SKILL_ENTRY_POINT
        )

    def test_simple_command_may_remain_generated_command(self):
        simple = make_workflow(
            command="list-workflows",
            body=".aw/system/workflows/list-workflows/HARNESS.md",
            description="List available workflows",
            arg_hint="none",
        )
        self.assertEqual(
            ha.classify_discovery_policy(simple), ha.POLICY_GENERATED_COMMAND
        )

    def test_authority_never_inlined_only_in_skill_prose(self):
        wf = make_workflow()
        pkg = ha.build_skill_package(wf)
        canonical_body = (
            "STEP 1: Freeze requirements.\nSTEP 2: Execute in scope.\n"
            "STEP 3: Verify with a fresh session.\n" * 20
        )
        findings = ha.check_authority_not_inlined(pkg, canonical_body)
        self.assertEqual(findings, [])

    def test_inlined_authority_is_detected(self):
        wf = make_workflow()
        pkg = ha.build_skill_package(wf)
        # Falsifiable: if the canonical body IS inlined into the router, detect it.
        pkg.main_file_content += "\n" + pkg.main_file_content[:250]
        leaked_body = pkg.main_file_content[:250]
        findings = ha.check_authority_not_inlined(pkg, leaked_body)
        self.assertTrue(findings)

    def test_disabling_skill_leaves_explicit_invocation_usable(self):
        pkg = ha.build_skill_package(make_workflow())
        self.assertTrue(ha.disabled_skill_still_invocable(pkg))


# --------------------------------------------------------------------------------------------------
# E-04: agy fresh-session verifier doubles
# --------------------------------------------------------------------------------------------------


class AgyFreshVerifierTests(unittest.TestCase):
    def test_execution_and_verifier_have_distinct_sessions(self):
        exec_dbl, verifier_dbl = av.make_execution_and_verifier_doubles("run-1")
        self.assertNotEqual(
            exec_dbl.identity.session_id, verifier_dbl.identity.session_id
        )
        self.assertEqual(exec_dbl.identity.role, verify_roles.ROLE_EXECUTOR)
        self.assertEqual(verifier_dbl.identity.role, verify_roles.ROLE_VERIFIER)

    def test_fresh_verifier_consumes_packet_and_finalizes(self):
        exec_dbl, verifier_dbl = av.make_execution_and_verifier_doubles("run-2")
        packet = make_verifier_packet()
        result = av.run_fresh_verifier(
            packet,
            exec_dbl.identity,
            verifier_dbl.identity,
            mode=av.MODE_FRESH_SESSION,
        )
        self.assertTrue(result.is_authoritative)
        self.assertTrue(result.can_finalize)
        self.assertEqual(result.packet_digest, packet.packet_digest)
        self.assertEqual(av.finalize_run(result), av.FINAL_VERIFIED)

    def test_fresh_verifier_refuses_same_session_identity(self):
        exec_dbl, _ = av.make_execution_and_verifier_doubles("run-3")
        # A verifier session that collides with the execution session must be refused.
        colliding = av.SessionIdentity(
            session_id=exec_dbl.identity.session_id, role=verify_roles.ROLE_VERIFIER
        )
        packet = make_verifier_packet()
        with self.assertRaises(av.SessionIdentityCollisionError):
            av.run_fresh_verifier(
                packet, exec_dbl.identity, colliding, mode=av.MODE_FRESH_SESSION
            )

    def test_same_session_audit_is_diagnostic_and_cannot_finalize(self):
        exec_dbl, verifier_dbl = av.make_execution_and_verifier_doubles("run-4")
        packet = make_verifier_packet()
        result = av.run_fresh_verifier(
            packet,
            exec_dbl.identity,
            verifier_dbl.identity,
            mode=av.MODE_SAME_SESSION_AUDIT,
        )
        self.assertTrue(result.diagnostic_only)
        self.assertFalse(result.is_authoritative)
        self.assertFalse(result.can_finalize)
        self.assertEqual(result.finalization, av.FINAL_NOT_FINALIZED)
        with self.assertRaises(av.SameSessionCannotFinalizeError):
            av.finalize_run(result)

    def test_non_verifier_role_cannot_author_decision(self):
        exec_dbl, _ = av.make_execution_and_verifier_doubles("run-5")
        bad = av.SessionIdentity(session_id="agy-x", role=verify_roles.ROLE_EXECUTOR)
        packet = make_verifier_packet()
        with self.assertRaises(verify_roles.SelfVerificationForbiddenError):
            av.run_fresh_verifier(packet, exec_dbl.identity, bad)

    def test_doubles_never_spawn_agy(self):
        # A double invoke is deterministic and records the call; no process/network.
        _, verifier_dbl = av.make_execution_and_verifier_doubles("run-6")
        r1 = verifier_dbl.invoke("verify the packet")
        r2 = verifier_dbl.invoke("verify the packet")
        self.assertEqual(r1["response_id"], r2["response_id"])
        self.assertEqual(len(verifier_dbl.calls), 2)


# --------------------------------------------------------------------------------------------------
# Security tests: loopback/auth, permission denial, external path, secret redaction
# --------------------------------------------------------------------------------------------------


class SecurityTests(unittest.TestCase):
    def test_external_path_refusal_via_assert_contained(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = ha.assert_isolated_base(tmp)
            inside = base / "skills" / "assess" / "SKILL.md"
            # Contained path is accepted.
            self.assertEqual(ha.assert_contained(inside, base), inside.resolve())
            # An external path (escaping the base) is refused fail-closed.
            with self.assertRaises(ha.SafetyError):
                ha.assert_contained("/etc/passwd", base)

    def test_isolated_base_refuses_real_home(self):
        with self.assertRaises(ha.SafetyError):
            ha.assert_isolated_base(str(Path.home()))

    def test_permission_denial_capability_fails_closed(self):
        # A denied-permission negative probe must be observed as fail-closed (registry gate).
        with tempfile.TemporaryDirectory() as tmp:
            res = hcr.evaluate_negative_probe(
                hcr.NEGATIVE_PROBE_DENIED_PERMISSION, "opencode", "1.0.0", tmp
            )
            self.assertTrue(res.fail_closed_observed)
            self.assertTrue(res.side_effect_prevented)

    def test_local_server_requires_auth_loopback(self):
        # A server-auth negative probe: unauthenticated endpoint must be rejected (D86/D87).
        with tempfile.TemporaryDirectory() as tmp:
            res = hcr.evaluate_negative_probe(
                hcr.NEGATIVE_PROBE_SERVER_AUTH, "opencode", "1.0.0", tmp
            )
            self.assertTrue(res.fail_closed_observed)

    def test_external_path_negative_probe_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = hcr.evaluate_negative_probe(
                hcr.NEGATIVE_PROBE_EXTERNAL_PATH_REFUSAL, "opencode", "1.0.0", tmp
            )
            self.assertTrue(res.fail_closed_observed)
            self.assertTrue(res.side_effect_prevented)

    def test_secret_redaction_in_adapter_reasons(self):
        # A secret leaking into diagnostic reasons must be redacted before surfacing.
        policy = RedactionPolicy(patterns=["sk-SECRET-TOKEN"])
        payload = {"reason": "probe failed with token sk-SECRET-TOKEN in log"}
        redacted, was = policy.redact(payload)
        self.assertTrue(was)
        self.assertNotIn("sk-SECRET-TOKEN", redacted["reason"])
        self.assertIn("[REDACTED]", redacted["reason"])


# --------------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------------


def _find_source_root() -> Path:
    """Locate the canonical workflow source root (`.aw/system/workflows`)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / ".aw" / "system" / "workflows"
        if (candidate / "index.md").is_file():
            return candidate
        legacy = parent / ".agents" / "workflows"
        if (legacy / "index.md").is_file():
            return legacy
    raise unittest.SkipTest("no workflow source root with index.md found")


if __name__ == "__main__":
    unittest.main()
