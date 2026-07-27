"""Self-tests for Phase 0 conformance harness (scaffolder, renderer, recorder/validator).

Stdlib unittest only.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.support import CONFORMANCE_HARNESS, load_module

CH = load_module("conformance_harness", CONFORMANCE_HARNESS)


class SafetyGuardTests(unittest.TestCase):
    """The isolation guard must protect real home and refuse escaping paths."""

    def test_raises_if_base_is_real_home(self):
        with self.assertRaises(CH.SafetyError) as ctx:
            CH.assert_isolated_base(Path.home())
        self.assertIn("cannot be the real home directory", str(ctx.exception))

    def test_raises_if_base_is_parent_of_real_home(self):
        parent_of_home = Path.home().parent
        with self.assertRaises(CH.SafetyError) as ctx:
            CH.assert_isolated_base(parent_of_home)
        self.assertIn("is a parent of real home directory", str(ctx.exception))

    def test_raises_if_empty_or_none(self):
        with self.assertRaises(CH.SafetyError):
            CH.assert_isolated_base("")

    def test_assert_contained_raises_on_escape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            outside = Path(tmpdir).parent / "outside_file.txt"
            with self.assertRaises(CH.SafetyError) as ctx:
                CH.assert_contained(outside, base)
            self.assertIn("escapes base directory", str(ctx.exception))


class ScaffolderTests(unittest.TestCase):
    """Scaffolder creates an isolated fixture tree with unique nonce and rendered env."""

    def test_scaffold_t2_under_tmp_base(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            res = CH.scaffold(
                base_dir=tmpdir,
                host="opencode",
                version="1.0.0",
                tier="T2",
            )
            base_p = Path(tmpdir).resolve()
            self.assertEqual(res.base_dir, str(base_p))
            self.assertTrue(Path(res.fixture_home).exists())
            self.assertTrue(Path(res.target_repo).exists())
            self.assertTrue(Path(res.external_content).exists())
            self.assertTrue((Path(res.target_repo) / ".git").exists())
            self.assertTrue(Path(res.fixture_path).exists())
            self.assertIn("PROBE-OK-opencode-1.0.0-", res.probe_filename)
            self.assertIn("HOME", res.env_vars)
            self.assertIn("XDG_CONFIG_HOME", res.env_vars)
            self.assertEqual(res.env_vars["HOME"], res.fixture_home)

    def test_scaffold_t1_and_t3(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            res_t1 = CH.scaffold(
                base_dir=tmpdir,
                host="claude_code",
                version="2.0",
                tier="T1",
                nonce="nonce123",
            )
            self.assertEqual(res_t1.tier, "T1")
            self.assertEqual(res_t1.nonce, "nonce123")
            self.assertTrue(Path(res_t1.fixture_path).exists())

        with tempfile.TemporaryDirectory() as tmpdir:
            res_t3 = CH.scaffold(
                base_dir=tmpdir,
                host="antigravity",
                version="3.0",
                tier="T3",
                nonce="nonce456",
            )
            self.assertEqual(res_t3.tier, "T3")
            self.assertTrue(Path(res_t3.fixture_path).exists())

    def test_distinct_nonces_per_run(self):
        with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
            res1 = CH.scaffold(tmpdir1, "codex", "1.0", "T2")
            res2 = CH.scaffold(tmpdir2, "codex", "1.0", "T2")
            self.assertNotEqual(res1.nonce, res2.nonce)


class RendererTests(unittest.TestCase):
    """Renderer produces exact execution and diagnostic commands from host matrix."""

    def test_render_supported_hosts(self):
        hosts = [
            "opencode",
            "claude_code",
            "codex",
            "copilot",
            "cursor",
            "antigravity",
            "gemini_cli",
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            for host in hosts:
                cmds = CH.render_commands(
                    host=host,
                    version="1.0",
                    tier="T2",
                    base_dir=tmpdir,
                    nonce="testnonce",
                )
                self.assertEqual(cmds.host, host)
                self.assertIn(
                    f"PROBE-OK-{host}-1.0-testnonce.txt", cmds.side_effect_check
                )
                self.assertGreater(len(cmds.diagnostic_commands), 0)

    def test_render_variants(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cmds_ni = CH.render_commands(
                "claude_code", "1.0", "T2", tmpdir, "n1", variant="noninteractive"
            )
            self.assertIn("--non-interactive", cmds_ni.host_command)

            cmds_app = CH.render_commands(
                "claude_code", "1.0", "T2", tmpdir, "n1", variant="approval-accepted"
            )
            self.assertIn("--auto-approve", cmds_app.host_command)

            cmds_deny = CH.render_commands(
                "claude_code", "1.0", "T2", tmpdir, "n1", variant="permission-denied"
            )
            self.assertIn("--deny-permissions", cmds_deny.host_command)

    def test_raises_on_unknown_host(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError) as ctx:
                CH.render_commands("unknown_agent", "1.0", "T2", tmpdir, "n1")
            self.assertIn("Unknown host 'unknown_agent'", str(ctx.exception))


class RecorderValidatorTests(unittest.TestCase):
    """Validator enforces Resolved vs. Followed evidence discipline."""

    def test_valid_observation(self):
        obs = CH.OperatorObservation(
            host="opencode",
            version="1.0",
            tier="T2",
            variant="default",
            nonce="nonce123",
            resolved=True,
            diagnostic_evidence="OpenCode context loaded skill conformance_probe successfully.",
            followed=True,
            nonce_side_effect_file="PROBE-OK-opencode-1.0-nonce123.txt",
            side_effect_verified=True,
            operator="opencode-operator",
        )
        CH.validate_observation(obs)
        report = CH.generate_results_report([obs])
        self.assertIn("opencode v1.0", report)
        self.assertIn("PROBE-OK-opencode-1.0-nonce123.txt", report)
        self.assertIn("Required Release Fixture Summary Table", report)

    def test_rejects_followed_without_side_effect_verified(self):
        obs = CH.OperatorObservation(
            host="opencode",
            version="1.0",
            tier="T2",
            variant="default",
            nonce="n1",
            resolved=True,
            diagnostic_evidence="Diagnostic evidence log here.",
            followed=True,
            nonce_side_effect_file="PROBE-OK-opencode-1.0-n1.txt",
            side_effect_verified=False,  # Unverified!
            operator="opencode-operator",
        )
        with self.assertRaises(ValueError) as ctx:
            CH.validate_observation(obs)
        self.assertIn(
            "'Followed' cannot be marked True without side_effect_verified=True",
            str(ctx.exception),
        )

    def test_rejects_followed_without_valid_side_effect_filename(self):
        obs = CH.OperatorObservation(
            host="opencode",
            version="1.0",
            tier="T2",
            variant="default",
            nonce="n1",
            resolved=True,
            diagnostic_evidence="Diagnostic evidence log here.",
            followed=True,
            nonce_side_effect_file="random_file.txt",  # Missing PROBE-OK- prefix!
            side_effect_verified=True,
            operator="opencode-operator",
        )
        with self.assertRaises(ValueError) as ctx:
            CH.validate_observation(obs)
        self.assertIn(
            "without a valid PROBE-OK-* nonce side-effect file", str(ctx.exception)
        )

    def test_rejects_resolved_without_diagnostic_evidence(self):
        obs = CH.OperatorObservation(
            host="opencode",
            version="1.0",
            tier="T2",
            variant="default",
            nonce="n1",
            resolved=True,
            diagnostic_evidence="",  # Empty!
            followed=False,
            nonce_side_effect_file="",
            side_effect_verified=False,
            operator="opencode-operator",
        )
        with self.assertRaises(ValueError) as ctx:
            CH.validate_observation(obs)
        self.assertIn("without concrete diagnostic evidence", str(ctx.exception))

    def test_rejects_followed_when_not_resolved(self):
        obs = CH.OperatorObservation(
            host="opencode",
            version="1.0",
            tier="T2",
            variant="default",
            nonce="n1",
            resolved=False,
            diagnostic_evidence="",
            followed=True,
            nonce_side_effect_file="PROBE-OK-opencode-1.0-n1.txt",
            side_effect_verified=True,
            operator="opencode-operator",
        )
        with self.assertRaises(ValueError) as ctx:
            CH.validate_observation(obs)
        self.assertIn("'Followed' requires 'Resolved' to be True", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
