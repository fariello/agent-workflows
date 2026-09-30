"""Tests for collision-free run directory minting and analytics acceptance of suffixed run IDs.

Covers:
1. runner_shared.mint_run_dir atomic collision resolution and distinct directories.
2. Caller-supplied explicit run IDs returned verbatim without suffixing.
3. Explicit duplicate run IDs raising DriverError ("Run already exists: <id>") without leaking paths.
4. Unsuffixed run ID returned on first attempt when free.
5. Analytics privacy and telemetry validation admitting -N collision suffixes and refusing malformed shapes.
6. runner_shared.telemetry_safe_context keeping the run_id correlation key for suffixed IDs.
7. End-to-end update_cache sweep rebuilding both plain and suffixed runs without build-refused.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import run_analytics
from agent_workflows import run_analytics_cache as cache_mod
from agent_workflows import run_analytics_privacy
from agent_workflows import run_analytics_telemetry
from agent_workflows import runner_shared
from tests.fixtures.run_analytics import write_run


class RunIdCollisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name).resolve()
        (self.repo / ".git").mkdir(parents=True, exist_ok=True)
        (self.repo / ".aw" / "records").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_two_mint_calls_on_collision_return_distinct_ids_and_extant_dirs(
        self,
    ) -> None:
        """Two mint calls with colliding timestamps return distinct IDs and existing dirs."""
        fixed_stamp_id = "run-20260928T120000Z-99999"
        with mock.patch(
            "agent_workflows.runner_shared.new_run_id", return_value=fixed_stamp_id
        ):
            id1, dir1 = runner_shared.mint_run_dir(self.repo)
            id2, dir2 = runner_shared.mint_run_dir(self.repo)

        self.assertEqual(id1, fixed_stamp_id)
        self.assertEqual(id2, f"{fixed_stamp_id}-2")
        self.assertNotEqual(id1, id2)
        self.assertTrue(dir1.is_dir())
        self.assertTrue(dir2.is_dir())
        self.assertNotEqual(dir1, dir2)

    def test_first_automatic_id_is_unsuffixed_when_path_is_free(self) -> None:
        """The first automatic ID has no collision suffix when the path is free."""
        fixed_stamp_id = "run-20260928T120000Z-88888"
        with mock.patch(
            "agent_workflows.runner_shared.new_run_id", return_value=fixed_stamp_id
        ):
            id1, dir1 = runner_shared.mint_run_dir(self.repo)

        self.assertEqual(id1, fixed_stamp_id)
        self.assertTrue(dir1.is_dir())

    def test_caller_supplied_run_id_is_returned_verbatim_not_suffixed(self) -> None:
        """An explicitly provided run_id is returned verbatim without suffixing."""
        custom_id = "run-20260928T120000Z-custom"
        id1, dir1 = runner_shared.mint_run_dir(self.repo, run_id=custom_id)
        self.assertEqual(id1, custom_id)
        self.assertEqual(dir1.name, custom_id)
        self.assertTrue(dir1.is_dir())

    def test_caller_supplied_run_id_whose_directory_already_exists_raises(self) -> None:
        """An explicit run_id collision raises DriverError with exact message and no paths."""
        custom_id = "run-20260928T120000Z-exists"
        _, dir1 = runner_shared.mint_run_dir(self.repo, run_id=custom_id)
        self.assertTrue(dir1.is_dir())

        with self.assertRaises(runner_shared.DriverError) as cm:
            runner_shared.mint_run_dir(self.repo, run_id=custom_id)

        # Must not be a raw FileExistsError
        self.assertNotIsInstance(cm.exception, FileExistsError)
        self.assertEqual(str(cm.exception), f"Run already exists: {custom_id}")
        self.assertNotIn("/", str(cm.exception))
        self.assertNotIn("\\", str(cm.exception))

    def test_analytics_validators_accept_suffixed_id_and_refuse_malformed(self) -> None:
        """Both privacy and telemetry validators accept -N suffixes and refuse malformed IDs."""
        plain_id = "run-20260929T013453Z-1234"
        suffixed_id = "run-20260929T013453Z-1234-2"
        malformed_suffix = "run-20260929T013453Z-1234-good"
        shipped_assertion_refusal = "run-20260908T100000Z-good"

        # Privacy entry point: project_metric_facts
        facts_plain = run_analytics_privacy.project_metric_facts({"run_id": plain_id})
        self.assertEqual(facts_plain["run_id"], plain_id)

        facts_suffixed = run_analytics_privacy.project_metric_facts(
            {"run_id": suffixed_id}
        )
        self.assertEqual(facts_suffixed["run_id"], suffixed_id)

        with self.assertRaises(run_analytics_privacy.PrivacyRefusal):
            run_analytics_privacy.project_metric_facts({"run_id": malformed_suffix})

        with self.assertRaises(run_analytics_privacy.PrivacyRefusal):
            run_analytics_privacy.project_metric_facts(
                {"run_id": shipped_assertion_refusal}
            )

        # Telemetry entry point: validate_event
        base_event = {
            "schema_version": run_analytics_telemetry.TELEMETRY_SCHEMA_VERSION,
            "event_kind": "start",
            "execution_id": "x1",
            "monotonic_offset_seconds": 0.0,
            "wall_timestamp": "2026-09-25T00:00:00Z",
            "sequence": 1,
        }

        event_plain = dict(base_event, run_id=plain_id)
        validated_plain = run_analytics_telemetry.validate_event(event_plain)
        self.assertEqual(validated_plain["run_id"], plain_id)

        event_suffixed = dict(base_event, run_id=suffixed_id)
        validated_suffixed = run_analytics_telemetry.validate_event(event_suffixed)
        self.assertEqual(validated_suffixed["run_id"], suffixed_id)

        event_malformed = dict(base_event, run_id=malformed_suffix)
        with self.assertRaises(run_analytics_telemetry.SchemaRefusal):
            run_analytics_telemetry.validate_event(event_malformed)

        event_shipped_bad = dict(base_event, run_id=shipped_assertion_refusal)
        with self.assertRaises(run_analytics_telemetry.SchemaRefusal):
            run_analytics_telemetry.validate_event(event_shipped_bad)

    def test_telemetry_safe_context_preserves_suffixed_run_id(self) -> None:
        """telemetry_safe_context keeps the run_id correlation field for suffixed IDs."""
        ctx = {
            "run_id": "run-20260929T013453Z-1234-2",
            "ipd_id6": "6mdtnu",
            "set_id": "runidcollide",
            "execution_id": "exec-1",
            "provider": "google",
            "model_variant": "gemini",
            "sequence": 1,
        }
        safe = runner_shared.telemetry_safe_context(ctx)
        self.assertIn("run_id", safe)
        self.assertEqual(safe["run_id"], "run-20260929T013453Z-1234-2")
        self.assertEqual(len(safe), 7)

    def test_analytics_cache_update_sweep_admits_suffixed_run_end_to_end(self) -> None:
        """update_cache sweep rebuilds both plain and suffixed runs without build-refused."""
        runs_root = self.repo / ".aw" / "records" / "runs"
        runs_root.mkdir(parents=True, exist_ok=True)
        r1 = write_run(runs_root, "run-20260901T000000Z-1111111", repo=str(self.repo))
        r2 = write_run(runs_root, "run-20260901T000000Z-1111111-2", repo=str(self.repo))

        report = cache_mod.update_cache(
            [r1, r2],
            build_facts=run_analytics.build_cache_facts,
            repo=self.repo,
        )

        decisions_by_id = {d.run_id: d for d in report.decisions}
        self.assertIn("run-20260901T000000Z-1111111", decisions_by_id)
        self.assertIn("run-20260901T000000Z-1111111-2", decisions_by_id)

        for d in report.decisions:
            self.assertEqual(d.verdict, "rebuild")
            self.assertNotEqual(d.reason, "build-refused")


if __name__ == "__main__":
    unittest.main()
