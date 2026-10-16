"""Self-tests for Host Capability Evidence Registry and Isolated Probes.

awoptimize Order 10 (4fttzq) E-01..E-04:
- E-01: Capability-evidence registry with unverified default, expiry, and static matrix migration.
- E-02: Isolated probe harness with version detection, real-HOME refusal, redaction, nonce verification,
        and machine-validated durable reports.
- E-03: Negative probes for missing skill, denied permission, no user input, path precedence, stale adapter,
        malformed frontmatter, external path refusal, server auth, and background result loss.
- E-04: Full test coverage conforming to stdlib unittest.
"""

from __future__ import annotations

import copy
import datetime
import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import host_capability_registry as hcr
from agent_workflows import release_readiness
from agent_workflows.run_ledger_store import RedactionPolicy


class MigrationAndDefaultTests(unittest.TestCase):
    """Test E-01: migration of static matrix, unverified defaults, and expiry."""

    def setUp(self):
        self.registry = hcr.HostCapabilityRegistry()

    def test_migration_converts_matrix_booleans_to_unverified_records(self):
        matrix_data = {
            "hosts": {
                "opencode": {
                    "display_name": "OpenCode",
                    "t1_policy": {"supported": False, "mechanism": "no out-of-repo"},
                    "t2_layout": {
                        "supported": True,
                        "preferred_path": ".agents/skills/{skill_name}/SKILL.md",
                    },
                    "t3_global": {
                        "supported": True,
                        "global_path": ".config/opencode/skills/{skill_name}/SKILL.md",
                    },
                },
                "claude_code": {
                    "display_name": "Claude Code",
                    "t1_policy": {"supported": True, "mechanism": "import"},
                    "t2_layout": {
                        "supported": True,
                        "preferred_path": ".claude/skills/{skill_name}/SKILL.md",
                    },
                },
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_file = Path(tmpdir) / "host_matrix.json"
            matrix_file.write_text(json.dumps(matrix_data), encoding="utf-8")

            count = self.registry.migrate_from_static_matrix(
                matrix_file, default_version="1.0.0"
            )
            self.assertEqual(count, 5)

            # Assert all migrated records are source_type=static_migration and result=unverified
            records = self.registry.list_records()
            self.assertEqual(len(records), 5)
            for rec in records:
                self.assertEqual(rec.source_type, hcr.SOURCE_STATIC_MIGRATION)
                self.assertEqual(rec.result, hcr.STATUS_UNVERIFIED)

    def test_unproven_capability_query_returns_unverified_never_supported(self):
        # Even if a static matrix had claimed supported=True, the registry defaults it to unverified
        matrix_data = {
            "hosts": {
                "opencode": {
                    "t2_layout": {"supported": True},
                }
            }
        }
        self.registry.migrate_from_static_matrix(matrix_data, default_version="1.0.0")
        eval_res = self.registry.query_capability(
            host="opencode",
            exact_version="1.0.0",
            feature="t2_layout",
        )
        self.assertEqual(eval_res.status, hcr.STATUS_UNVERIFIED)
        self.assertFalse(eval_res.is_supported)
        self.assertTrue(any("Unproven claim" in r for r in eval_res.reasons))

    def test_missing_capability_defaults_to_unverified(self):
        eval_res = self.registry.query_capability(
            host="nonexistent_host",
            exact_version="9.9.9",
            feature="t2_skill_layout",
        )
        self.assertEqual(eval_res.status, hcr.STATUS_UNVERIFIED)
        self.assertFalse(eval_res.is_supported)
        self.assertIn("No capability record found", eval_res.reasons[0])

    def test_expired_record_evaluates_to_unverified(self):
        past_date = (
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=120)
        ).isoformat()
        past_expiry = (
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
        ).isoformat()
        rec = hcr.EvidenceRecord(
            host="codex",
            distribution="default",
            exact_version="1.0.0",
            os="linux",
            mode="default",
            feature="t2_skill_layout",
            configuration={},
            probe_variant="default",
            result=hcr.STATUS_SUPPORTED,
            evidence_artifact="proof.json",
            observed_date=past_date,
            expiry=past_expiry,
            source_type=hcr.SOURCE_ISOLATED_PROBE,
            resolved=True,
            followed=True,
            side_effect_verified=True,
            diagnostic_evidence="Context loaded successfully.",
        )
        self.registry.register_record(rec)

        eval_res = self.registry.query_capability(
            host="codex",
            exact_version="1.0.0",
            feature="t2_skill_layout",
        )
        self.assertEqual(eval_res.status, hcr.STATUS_UNVERIFIED)
        self.assertFalse(eval_res.is_supported)
        self.assertTrue(any("expired" in r.lower() for r in eval_res.reasons))

    def test_default_ttl_expiry_evaluates_to_unverified(self):
        # 100 days ago with default 90-day TTL (expiry=None)
        past_date = (
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=100)
        ).isoformat()
        rec = hcr.EvidenceRecord(
            host="codex",
            distribution="default",
            exact_version="1.0.0",
            os="linux",
            mode="default",
            feature="t2_skill_layout",
            configuration={},
            probe_variant="default",
            result=hcr.STATUS_SUPPORTED,
            evidence_artifact="proof.json",
            observed_date=past_date,
            expiry=None,  # Should use default TTL (90 days)
            source_type=hcr.SOURCE_ISOLATED_PROBE,
            resolved=True,
            followed=True,
            side_effect_verified=True,
            diagnostic_evidence="Context loaded successfully.",
        )
        self.registry.register_record(rec)

        eval_res = self.registry.query_capability(
            host="codex",
            exact_version="1.0.0",
            feature="t2_skill_layout",
        )
        self.assertEqual(eval_res.status, hcr.STATUS_UNVERIFIED)
        self.assertFalse(eval_res.is_supported)

    def test_export_evidence_table_reflects_actual_claims(self):
        rec = hcr.EvidenceRecord(
            host="opencode",
            distribution="native",
            exact_version="1.0.0",
            os="linux",
            mode="default",
            feature="t2_skill_layout",
            configuration={},
            probe_variant="default",
            result=hcr.STATUS_UNVERIFIED,
            evidence_artifact="",
            observed_date="2026-08-22T00:00:00Z",
            expiry=None,
            source_type=hcr.SOURCE_STATIC_MIGRATION,
        )
        self.registry.register_record(rec)
        table = self.registry.export_evidence_table()
        self.assertIn("opencode", table)
        self.assertIn("1.0.0", table)
        self.assertIn("unverified", table)


class SafetyAndIsolationTests(unittest.TestCase):
    """Test E-02: Safety guards refusing real HOME or escaping paths."""

    def test_assert_isolated_base_refuses_real_home(self):
        with self.assertRaises(hcr.SafetyError) as ctx:
            hcr.assert_isolated_base(Path.home())
        self.assertIn("cannot be the real home directory", str(ctx.exception))

    def test_assert_isolated_base_refuses_parent_of_real_home(self):
        parent_of_home = Path.home().parent
        with self.assertRaises(hcr.SafetyError) as ctx:
            hcr.assert_isolated_base(parent_of_home)
        self.assertIn("is a parent of real home directory", str(ctx.exception))

    def test_assert_isolated_base_refuses_empty_path(self):
        with self.assertRaises(hcr.SafetyError) as ctx:
            hcr.assert_isolated_base("")
        self.assertIn("cannot be empty", str(ctx.exception))

    def test_assert_contained_refuses_escaping_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            outside = base.parent / "escape.txt"
            with self.assertRaises(hcr.SafetyError) as ctx:
                hcr.assert_contained(outside, base)
            self.assertIn("escapes base directory", str(ctx.exception))


class ProbeHarnessTests(unittest.TestCase):
    """Test E-02: Scaffolding, command rendering, execution, capture, redaction, and report."""

    def test_scaffold_isolated_fixture_creates_tree_and_nonce(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = hcr.scaffold_probe_fixture(
                base_dir=tmpdir,
                host="opencode",
                version="1.0.0",
                tier="T2",
                feature="t2_skill_layout",
                nonce="abcd1234",
            )
            self.assertEqual(fixture.host, "opencode")
            self.assertEqual(fixture.version, "1.0.0")
            self.assertEqual(fixture.nonce, "abcd1234")
            self.assertTrue(Path(fixture.fixture_home).exists())
            self.assertTrue(Path(fixture.target_repo).exists())
            self.assertTrue((Path(fixture.target_repo) / ".git").exists())
            self.assertTrue(Path(fixture.external_content).exists())
            self.assertEqual(fixture.env_vars["HOME"], fixture.fixture_home)
            self.assertIn(
                "PROBE-OK-opencode-1.0.0-abcd1234.txt", fixture.probe_filename
            )

    def test_detect_host_version_parses_version_output(self):
        # Mock runner returning standard version outputs
        def mock_runner_opencode(cmd, **kwargs):
            return 0, "opencode version 1.0.4 (linux x86_64)", ""

        def mock_runner_agy(cmd, **kwargs):
            return 0, "agy 1.1.17\nGoogle Antigravity CLI", ""

        def mock_runner_missing(cmd, **kwargs):
            raise FileNotFoundError("executable not found")

        v_opencode = hcr.detect_host_version("opencode", runner=mock_runner_opencode)
        self.assertEqual(v_opencode, "1.0.4")

        v_agy = hcr.detect_host_version("antigravity", runner=mock_runner_agy)
        self.assertEqual(v_agy, "1.1.17")

        v_none = hcr.detect_host_version("unknown_bin", runner=mock_runner_missing)
        self.assertIsNone(v_none)

    def test_render_probe_commands_derives_from_adapters(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cmds = hcr.render_probe_commands(
                host="opencode",
                version="1.0.0",
                tier="T2",
                base_dir=tmpdir,
                nonce="nonce99",
            )
            self.assertEqual(cmds.host, "opencode")
            self.assertIn("export HOME=", cmds.script_text)
            self.assertIn("export XDG_CONFIG_HOME=", cmds.script_text)
            self.assertIn("PROBE-OK-opencode-1.0.0-nonce99.txt", cmds.side_effect_check)
            self.assertTrue(
                any("opencode" in line for line in cmds.diagnostic_commands)
            )

    def test_run_isolated_probe_captures_and_verifies_nonce(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = hcr.scaffold_probe_fixture(
                base_dir=tmpdir,
                host="opencode",
                version="1.0.0",
                tier="T2",
                nonce="testnonce",
            )
            cmds = hcr.render_probe_commands(
                host="opencode",
                version="1.0.0",
                tier="T2",
                base_dir=tmpdir,
                nonce="testnonce",
            )

            # Mock runner that simulates creating the expected probe nonce file
            def mock_successful_runner(cmd, env, cwd):
                target_p = Path(cwd) / fixture.probe_filename
                target_p.write_text("testnonce\n", encoding="utf-8")
                return 0, "Loaded skill conformance_probe successfully.", ""

            res = hcr.run_isolated_probe(
                fixture=fixture,
                rendered_cmd=cmds,
                runner=mock_successful_runner,
            )
            self.assertEqual(res.exit_code, 0)
            self.assertTrue(res.side_effect_file_found)
            self.assertTrue(res.side_effect_content_matched)
            self.assertTrue(res.resolved)
            self.assertTrue(res.followed)

    def test_run_isolated_probe_redacts_captured_evidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = hcr.scaffold_probe_fixture(
                base_dir=tmpdir,
                host="claude_code",
                version="2.0",
                tier="T2",
                nonce="secnonce",
            )
            cmds = hcr.render_probe_commands(
                host="claude_code",
                version="2.0",
                tier="T2",
                base_dir=tmpdir,
                nonce="secnonce",
            )

            secret_token = "sk-ant-api03-VERY-SECRET-KEY-12345"
            policy = RedactionPolicy(patterns=[secret_token], mask="[REDACTED_SECRET]")

            def mock_leaky_runner(cmd, env, cwd):
                target_p = Path(cwd) / fixture.probe_filename
                target_p.write_text("secnonce\n", encoding="utf-8")
                return 0, f"Connected with token {secret_token}", ""

            res = hcr.run_isolated_probe(
                fixture=fixture,
                rendered_cmd=cmds,
                runner=mock_leaky_runner,
                redaction_policy=policy,
            )
            self.assertTrue(res.was_redacted)
            self.assertNotIn(secret_token, res.stdout)
            self.assertIn("[REDACTED_SECRET]", res.stdout)

    def test_generate_durable_report_validates_and_formats_9_points(self):
        obs = hcr.OperatorObservation(
            host="opencode",
            version="1.0.0",
            tier="T2",
            variant="default",
            nonce="nonce77",
            resolved=True,
            diagnostic_evidence="OpenCode context loaded skill conformance_probe successfully.",
            followed=True,
            nonce_side_effect_file="PROBE-OK-opencode-1.0.0-nonce77.txt",
            side_effect_verified=True,
            operator="opencode-operator",
        )
        report = hcr.generate_durable_report([obs])
        self.assertIn("# Conformance Probe Results Report", report)
        self.assertIn("opencode v1.0.0", report)
        self.assertIn("PROBE-OK-opencode-1.0.0-nonce77.txt", report)
        self.assertIn("clean temp base", report)
        self.assertIn("YES", report)

    def test_generate_durable_report_rejects_invalid_observation(self):
        # followed=True without side_effect_verified=True must be rejected
        obs = hcr.OperatorObservation(
            host="opencode",
            version="1.0.0",
            tier="T2",
            variant="default",
            nonce="nonce77",
            resolved=True,
            diagnostic_evidence="Loaded skill",
            followed=True,
            nonce_side_effect_file="PROBE-OK-opencode-1.0.0-nonce77.txt",
            side_effect_verified=False,
            operator="opencode-operator",
        )
        with self.assertRaises(ValueError) as ctx:
            hcr.generate_durable_report([obs])
        self.assertIn("side_effect_verified=True", str(ctx.exception))


class NegativeProbeTests(unittest.TestCase):
    """Test E-03: Negative probes across all 9 required classes."""

    def test_negative_probe_missing_skill(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            res = hcr.evaluate_negative_probe(
                probe_class=hcr.NEGATIVE_PROBE_MISSING_SKILL,
                host="opencode",
                version="1.0.0",
                base_dir=tmpdir,
                runner=lambda cmd, env, cwd: (
                    1,
                    "",
                    "Error: Skill 'nonexistent_skill' not found in search paths.",
                ),
            )
            self.assertTrue(res.fail_closed_observed)
            self.assertTrue(res.side_effect_prevented)
            self.assertIn("not found", res.rejection_evidence)
            self.assertEqual(
                res.evidence_record.result, hcr.STATUS_FAIL_CLOSED_VERIFIED
            )

    def test_negative_probe_denied_permission(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            res = hcr.evaluate_negative_probe(
                probe_class=hcr.NEGATIVE_PROBE_DENIED_PERMISSION,
                host="claude_code",
                version="2.0",
                base_dir=tmpdir,
                runner=lambda cmd, env, cwd: (
                    1,
                    "",
                    "PermissionDenied: User rejected write permission to target_repo.",
                ),
            )
            self.assertTrue(res.fail_closed_observed)
            self.assertTrue(res.side_effect_prevented)
            self.assertIn("PermissionDenied", res.rejection_evidence)

    def test_negative_probe_no_user_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            res = hcr.evaluate_negative_probe(
                probe_class=hcr.NEGATIVE_PROBE_NO_USER_INPUT,
                host="codex",
                version="1.0.0",
                base_dir=tmpdir,
                runner=lambda cmd, env, cwd: (
                    2,
                    "",
                    "Fatal: Stdin closed in noninteractive mode; interactive prompt required.",
                ),
            )
            self.assertTrue(res.fail_closed_observed)
            self.assertTrue(res.side_effect_prevented)
            self.assertIn("noninteractive", res.rejection_evidence.lower())

    def test_negative_probe_path_precedence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            res = hcr.evaluate_negative_probe(
                probe_class=hcr.NEGATIVE_PROBE_PATH_PRECEDENCE,
                host="opencode",
                version="1.0.0",
                base_dir=tmpdir,
            )
            self.assertTrue(res.fail_closed_observed)
            self.assertIn("workspace precedence", res.notes.lower())

    def test_negative_probe_stale_adapter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            res = hcr.evaluate_negative_probe(
                probe_class=hcr.NEGATIVE_PROBE_STALE_ADAPTER,
                host="antigravity",
                version="1.1.17",
                base_dir=tmpdir,
                runner=lambda cmd, env, cwd: (
                    1,
                    "",
                    "AdapterSchemaError: Incompatible adapter version 0 vs required 1.",
                ),
            )
            self.assertTrue(res.fail_closed_observed)
            self.assertTrue(res.side_effect_prevented)
            self.assertIn("AdapterSchemaError", res.rejection_evidence)

    def test_negative_probe_malformed_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            res = hcr.evaluate_negative_probe(
                probe_class=hcr.NEGATIVE_PROBE_MALFORMED_FRONTMATTER,
                host="opencode",
                version="1.0.0",
                base_dir=tmpdir,
                runner=lambda cmd, env, cwd: (
                    1,
                    "",
                    "FrontmatterError: Invalid YAML at line 2: unclosed quote.",
                ),
            )
            self.assertTrue(res.fail_closed_observed)
            self.assertTrue(res.side_effect_prevented)
            self.assertIn("FrontmatterError", res.rejection_evidence)

    def test_negative_probe_external_path_refusal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            res = hcr.evaluate_negative_probe(
                probe_class=hcr.NEGATIVE_PROBE_EXTERNAL_PATH_REFUSAL,
                host="codex",
                version="1.0.0",
                base_dir=tmpdir,
                runner=lambda cmd, env, cwd: (
                    1,
                    "",
                    "PathSecurityViolation: Refusing write to external path outside workspace root.",
                ),
            )
            self.assertTrue(res.fail_closed_observed)
            self.assertTrue(res.side_effect_prevented)
            self.assertIn("PathSecurityViolation", res.rejection_evidence)

    def test_negative_probe_server_auth(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            res = hcr.evaluate_negative_probe(
                probe_class=hcr.NEGATIVE_PROBE_SERVER_AUTH,
                host="copilot",
                version="1.0.0",
                base_dir=tmpdir,
                runner=lambda cmd, env, cwd: (
                    1,
                    "",
                    "HTTP 401 Unauthorized: Bearer token missing for daemon endpoint.",
                ),
            )
            self.assertTrue(res.fail_closed_observed)
            self.assertTrue(res.side_effect_prevented)
            self.assertIn("401", res.rejection_evidence)

    def test_negative_probe_background_result_loss(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            res = hcr.evaluate_negative_probe(
                probe_class=hcr.NEGATIVE_PROBE_BACKGROUND_RESULT_LOSS,
                host="cursor",
                version="1.0.0",
                base_dir=tmpdir,
                runner=lambda cmd, env, cwd: (
                    1,
                    "",
                    "AsyncExecutionLost: Background subagent crashed without exit receipt.",
                ),
            )
            self.assertTrue(res.fail_closed_observed)
            self.assertTrue(res.side_effect_prevented)
            self.assertIn("AsyncExecutionLost", res.rejection_evidence)


class PromotionGateTests(unittest.TestCase):
    """Test capability promotion requiring positive AND negative verification."""

    def test_capability_promotion_requires_positive_and_negative_proof(self):
        registry = hcr.HostCapabilityRegistry()
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Positive probe
        pos_rec = hcr.EvidenceRecord(
            host="opencode",
            distribution="native",
            exact_version="1.0.0",
            os="linux",
            mode="default",
            feature="t2_skill_layout",
            configuration={},
            probe_variant="default",
            result=hcr.STATUS_SUPPORTED,
            evidence_artifact="probe-ok.json",
            observed_date=now_str,
            expiry=None,
            source_type=hcr.SOURCE_ISOLATED_PROBE,
            resolved=True,
            followed=True,
            side_effect_verified=True,
            diagnostic_evidence="Skill resolved and followed with valid nonce.",
        )

        # Negative probe
        neg_rec = hcr.EvidenceRecord(
            host="opencode",
            distribution="native",
            exact_version="1.0.0",
            os="linux",
            mode="default",
            feature="t2_skill_layout",
            configuration={},
            probe_variant=hcr.NEGATIVE_PROBE_DENIED_PERMISSION,
            result=hcr.STATUS_FAIL_CLOSED_VERIFIED,
            evidence_artifact="neg-probe.json",
            observed_date=now_str,
            expiry=None,
            source_type=hcr.SOURCE_ISOLATED_PROBE,
            resolved=False,
            followed=False,
            side_effect_verified=False,
            diagnostic_evidence="Permission denied safely rejected.",
        )

        evaluation = registry.promote_capability(
            host="opencode",
            exact_version="1.0.0",
            feature="t2_skill_layout",
            positive_probe=pos_rec,
            negative_probes=[neg_rec],
        )
        self.assertEqual(evaluation.status, hcr.STATUS_SUPPORTED)
        self.assertTrue(evaluation.is_supported)

    def test_negative_probe_failure_blocks_promotion(self):
        registry = hcr.HostCapabilityRegistry()
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        pos_rec = hcr.EvidenceRecord(
            host="opencode",
            distribution="native",
            exact_version="1.0.0",
            os="linux",
            mode="default",
            feature="t2_skill_layout",
            configuration={},
            probe_variant="default",
            result=hcr.STATUS_SUPPORTED,
            evidence_artifact="probe-ok.json",
            observed_date=now_str,
            expiry=None,
            source_type=hcr.SOURCE_ISOLATED_PROBE,
            resolved=True,
            followed=True,
            side_effect_verified=True,
            diagnostic_evidence="Skill resolved and followed with valid nonce.",
        )

        # A negative probe that failed to fail closed (e.g. permission was bypassed!)
        bad_neg_rec = hcr.EvidenceRecord(
            host="opencode",
            distribution="native",
            exact_version="1.0.0",
            os="linux",
            mode="default",
            feature="t2_skill_layout",
            configuration={},
            probe_variant=hcr.NEGATIVE_PROBE_DENIED_PERMISSION,
            result=hcr.STATUS_FAILED,  # Failed to fail closed!
            evidence_artifact="neg-probe-fail.json",
            observed_date=now_str,
            expiry=None,
            source_type=hcr.SOURCE_ISOLATED_PROBE,
            notes="Permission denial was ignored by host.",
        )

        with self.assertRaises(ValueError) as ctx:
            registry.promote_capability(
                host="opencode",
                exact_version="1.0.0",
                feature="t2_skill_layout",
                positive_probe=pos_rec,
                negative_probes=[bad_neg_rec],
            )
        self.assertIn("Negative probe failed", str(ctx.exception))

        # Querying still yields unverified
        eval_res = registry.query_capability(
            host="opencode",
            exact_version="1.0.0",
            feature="t2_skill_layout",
        )
        self.assertEqual(eval_res.status, hcr.STATUS_UNVERIFIED)
        self.assertFalse(eval_res.is_supported)


class TestShippedHostMatrixAndFreshnessGate(unittest.TestCase):
    """Behavioral and falsifiability tests for the shipped default host matrix and freshness gate."""

    def test_shipped_matrix_shape_and_migration(self):
        self.assertTrue(
            hcr.DEFAULT_MATRIX_PATH.is_file(),
            f"Shipped default matrix path {hcr.DEFAULT_MATRIX_PATH} must exist as a file",
        )
        data = hcr.load_host_matrix(hcr.DEFAULT_MATRIX_PATH)
        hosts = data.get("hosts", {})
        expected_hosts = {
            "antigravity",
            "claude_code",
            "codex",
            "copilot",
            "cursor",
            "gemini_cli",
            "kiro",
            "opencode",
        }
        self.assertEqual(set(hosts.keys()), expected_hosts)

        for host_name, cfg in hosts.items():
            self.assertIn("display_name", cfg)
            self.assertTrue(cfg.get("display_name"))
            self.assertIn("command_template", cfg)
            self.assertTrue(cfg.get("command_template"))
            self.assertIn("diagnostic_commands", cfg)

            self.assertIn("t1_policy", cfg)
            self.assertTrue(isinstance(cfg["t1_policy"], dict))
            self.assertTrue(cfg["t1_policy"].get("mechanism"))

            self.assertIn("t2_layout", cfg)
            self.assertTrue(isinstance(cfg["t2_layout"], dict))
            self.assertTrue(cfg["t2_layout"].get("preferred_path"))

            self.assertIn("t3_global", cfg)
            self.assertTrue(isinstance(cfg["t3_global"], dict))
            self.assertTrue(cfg["t3_global"].get("global_path"))

        supported_keys = [
            (h, k)
            for h, cfg in hosts.items()
            for k, v in cfg.items()
            if k.startswith("t") and isinstance(v, dict) and "supported" in v
        ]
        self.assertEqual(
            supported_keys,
            [],
            "Shipped host matrix tier objects must not contain 'supported' booleans",
        )

        reg = hcr.HostCapabilityRegistry()
        migrated_count = reg.migrate_from_static_matrix(data)
        self.assertEqual(migrated_count, 24)

        for host_name in expected_hosts:
            for tier_name in ("t1_policy", "t2_layout", "t3_global"):
                query_res = reg.query_capability(
                    host=host_name, exact_version="1.0.0", feature=tier_name
                )
                self.assertFalse(query_res.is_supported)
                rec = reg.get_record(host_name, "1.0.0", tier_name)
                self.assertIsNotNone(rec)
                self.assertEqual(rec.result, hcr.STATUS_UNVERIFIED)
                self.assertEqual(rec.source_type, hcr.SOURCE_STATIC_MIGRATION)

        for host_name in expected_hosts:
            for tier in ("T1", "T2", "T3"):
                with self.subTest(host=host_name, tier=tier):
                    with tempfile.TemporaryDirectory() as td:
                        base = Path(td)
                        fixture = hcr.scaffold_probe_fixture(
                            base, host_name, "1.0.0", tier=tier
                        )
                        cmds = hcr.render_probe_commands(
                            host_name, "1.0.0", tier, base, fixture.nonce
                        )
                        self.assertIsNotNone(fixture)
                        self.assertIsNotNone(cmds)

    def test_freshness_gate_on_shipped_matrix_and_falsifiability_control(self):
        repo_root = Path(__file__).resolve().parent.parent
        gate_res = release_readiness.gate_capability_freshness(repo_root=repo_root)
        self.assertTrue(
            gate_res.passed,
            f"gate_capability_freshness failed on repo_root: {gate_res.detail}",
        )
        self.assertEqual(gate_res.detail, "no stale capability claims")
        self.assertEqual(
            gate_res.evidence,
            {"stale_claims": [], "claims_checked": 0},
        )

        data = hcr.load_host_matrix(hcr.DEFAULT_MATRIX_PATH)
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            matrix_path = (
                t
                / ".aw"
                / "system"
                / "workflows"
                / "conformance"
                / "tools"
                / "host_matrix.json"
            )
            matrix_path.parent.mkdir(parents=True, exist_ok=True)
            copy_data = copy.deepcopy(data)
            copy_data["hosts"]["antigravity"]["t2_layout"]["supported"] = True
            matrix_path.write_text(json.dumps(copy_data), encoding="utf-8")

            falsify_res = release_readiness.gate_capability_freshness(repo_root=t)
            self.assertFalse(falsify_res.passed)
            self.assertEqual(falsify_res.evidence.get("claims_checked"), 1)
            stale = falsify_res.evidence.get("stale_claims", [])
            self.assertEqual(len(stale), 1)
            self.assertTrue(
                stale[0].startswith("antigravity:t2_layout:"),
                f"Unexpected stale claim prefix: {stale[0]}",
            )


if __name__ == "__main__":
    unittest.main()
