"""Lifecycle-matrix fixture tests for awoptimize Order 18 (`0zst62`) E-04.

Every named lifecycle fixture runs from a clean isolated environment and PASSES; the
fail-before-mutation fixtures (``no-credential``, ``unsupported-host``) fail BEFORE any
mutation (assert ``mutated is False``); and a rerun shows no unmanaged drift (the migrator's
own idempotent no-op preview, asserted by the fixtures that mutate).

Stdlib ``unittest`` (repository convention).
"""

from __future__ import annotations

import unittest

from agent_workflows import lifecycle_fixtures as lf


class LifecycleFixtureRegistryTests(unittest.TestCase):
    def test_all_eleven_named_fixtures_present(self):
        expected = {
            "clean-install",
            "legacy-update",
            "partial-state",
            "customized-file",
            "interrupted-update",
            "rollback",
            "downgrade-warning",
            "no-network",
            "no-credential",
            "multi-host-discovery",
            "unsupported-host",
        }
        self.assertEqual(set(lf.ALL_FIXTURES), expected)
        self.assertEqual(len(lf.ALL_FIXTURES), 11)

    def test_every_fixture_has_a_runner(self):
        for name in lf.ALL_FIXTURES:
            self.assertIn(name, lf.FIXTURE_RUNNERS)


class LifecycleFixturePassTests(unittest.TestCase):
    """Every named fixture passes from a clean isolated environment."""

    def test_clean_install_passes(self):
        self.assertTrue(lf.run_fixture("clean-install").passed)

    def test_legacy_update_passes(self):
        self.assertTrue(lf.run_fixture("legacy-update").passed)

    def test_partial_state_passes(self):
        o = lf.run_fixture("partial-state")
        self.assertTrue(o.passed, o.evidence)

    def test_customized_file_passes(self):
        o = lf.run_fixture("customized-file")
        self.assertTrue(o.passed, o.evidence)

    def test_interrupted_update_passes(self):
        o = lf.run_fixture("interrupted-update")
        self.assertTrue(o.passed, o.evidence)

    def test_rollback_passes(self):
        self.assertTrue(lf.run_fixture("rollback").passed)

    def test_no_network_passes(self):
        o = lf.run_fixture("no-network")
        self.assertTrue(o.passed, o.evidence)

    def test_multi_host_discovery_passes(self):
        self.assertTrue(lf.run_fixture("multi-host-discovery").passed)


class FailBeforeMutationTests(unittest.TestCase):
    """The unsupported / no-credential cases fail BEFORE any mutation."""

    def test_no_credential_fails_before_mutation(self):
        o = lf.run_fixture("no-credential")
        # It "passes" as a fixture (correct refusal) but MUST NOT have mutated anything.
        self.assertTrue(o.passed)
        self.assertFalse(o.mutated)

    def test_unsupported_host_refused_before_mutation(self):
        o = lf.run_fixture("unsupported-host")
        self.assertTrue(o.passed)
        self.assertFalse(o.mutated)

    def test_fail_before_mutation_set(self):
        self.assertIn("no-credential", lf.FAIL_BEFORE_MUTATION_FIXTURES)
        self.assertIn("unsupported-host", lf.FAIL_BEFORE_MUTATION_FIXTURES)


class DowngradeWarningTests(unittest.TestCase):
    def test_downgrade_warns_and_is_refused_without_corruption(self):
        o = lf.run_fixture("downgrade-warning")
        self.assertTrue(o.passed, o.evidence)
        # Refused, not mutated; a warning was produced (the data left intact).
        self.assertFalse(o.mutated)
        self.assertEqual(o.evidence["status"], "refused")
        self.assertTrue(o.evidence["warnings"])


class NoUnmanagedDriftTests(unittest.TestCase):
    def test_clean_install_rerun_is_no_op(self):
        o = lf.run_fixture("clean-install")
        # Evidence records the rerun planned ZERO further changes (no unmanaged drift).
        self.assertEqual(o.evidence["rerun_changes"], 0)


class RunAllTests(unittest.TestCase):
    def test_run_all_fixtures_pass(self):
        outcomes = lf.run_all_fixtures()
        self.assertEqual(len(outcomes), len(lf.ALL_FIXTURES))
        failed = [o.name for o in outcomes if not o.passed]
        self.assertEqual(failed, [], f"lifecycle fixtures failed: {failed}")
        # Fail-before-mutation fixtures did not mutate.
        by_name = {o.name: o for o in outcomes}
        for name in lf.FAIL_BEFORE_MUTATION_FIXTURES:
            self.assertFalse(by_name[name].mutated, f"{name} mutated before refusal")


class IsolationTests(unittest.TestCase):
    def test_env_isolated_from_real_home(self):
        # make_isolated_env must never yield a base that is (or contains) the real HOME.
        env = lf.make_isolated_env()
        try:
            from pathlib import Path

            real_home = Path.home().resolve()
            self.assertNotEqual(env.base_dir.resolve(), real_home)
            self.assertNotIn(env.base_dir.resolve(), real_home.parents)
        finally:
            env.cleanup()


if __name__ == "__main__":
    unittest.main()
