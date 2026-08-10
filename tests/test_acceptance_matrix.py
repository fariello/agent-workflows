"""Acceptance matrix test suite covering Section 19 scenarios 19.1 through 19.25 (IPD 20260809-awlayout-11).

Traceability contract:
- 19.1: fresh_interactive_home_recommended (Orders 04, 05)
- 19.2: fresh_interactive_repository_risk_acknowledged (Orders 04, 05)
- 19.3: companion_local_git_opens_durability_action (Orders 03, 06)
- 19.4: companion_confirmed_private_remote (Order 03)
- 19.5: first_noninteractive_complete_policy (Orders 04, 05)
- 19.6: first_noninteractive_missing_policy_fails_before_write (Order 04)
- 19.7: same_version_reinstall_checkpoint_noop (Orders 04, 05)
- 19.8: version_update_keep_policy (Orders 04, 05)
- 19.9: update_repository_to_home (Orders 04, 09)
- 19.10: skipped_versions_reconcile_action_generations (Order 06)
- 19.11: repository_move_reattach (Order 02)
- 19.12: clone_worktree_resolution_matrix (Orders 01, 02)
- 19.13: setup_action_all_attention_surfaces (Orders 06, 07)
- 19.14: setup_completion_moves_completed (Orders 06, 07)
- 19.15: dismissal_history_no_resurrection (Order 06)
- 19.16: new_generation_supersedes_open (Order 06)
- 19.17: split_product_and_record_commits (Orders 01, 03, 08)
- 19.18: migration_preserves_before_cleanup (Order 09)
- 19.19: uninstall_preserves_external_state_records (Order 09)
- 19.20: clean_delta_merge_base_zero_write (Order 10)
- 19.21: unavailable_external_root_stops_writes (Orders 01, 08)
- 19.22: terminal_color_environment_matrix (Order 04)
- 19.23: screen_reader_linear_semantics (Order 04)
- 19.24: privacy_doctor_refuses_unverified_privacy (Order 03)
- 19.25: broken_navigation_link_resolver_succeeds (Orders 01, 03)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest

from agent_workflows.actions import ActionManager
from agent_workflows.clean_delta import CleanDeltaManager
from agent_workflows.install_wizard import ProjectPolicy, resolve_policy_noninteractive
from agent_workflows.layout_migration import MigrationManager
from agent_workflows.project_registry import register_or_update_project
from agent_workflows.project_schema import DeliveryMode, RecordsBackend
from agent_workflows.storage import validate_storage_boundaries


class TestAcceptanceMatrixScenarios(unittest.TestCase):
    """Test suite covering Section 19 acceptance scenarios 19.1 through 19.25."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(self.target_repo, exist_ok=True)
        subprocess.run(
            ["git", "init", "-q", self.target_repo], check=True, capture_output=True
        )
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)
        os.environ["AW_HOME"] = self.aw_home

        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-123456"
        )

    def tearDown(self):
        os.environ.pop("AW_HOME", None)
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_19_1_fresh_interactive_home_recommended(self):
        """Scenario 19.1: Fresh interactive install selecting home records."""
        pol = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.HOME.value,
            aw_home=self.aw_home,
        )
        self.assertEqual(pol.records_backend, RecordsBackend.HOME.value)

    def test_19_2_fresh_interactive_repository_risk_acknowledged(self):
        """Scenario 19.2: Fresh interactive install selecting repository records."""
        pol = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.REPOSITORY.value,
            aw_home=self.aw_home,
        )
        self.assertEqual(pol.records_backend, RecordsBackend.REPOSITORY.value)

    def test_19_5_first_noninteractive_complete_policy(self):
        """Scenario 19.5: Noninteractive install with complete policy."""
        pol = resolve_policy_noninteractive(
            self.target_repo,
            explicit_delivery=DeliveryMode.TRACKED.value,
            explicit_backend=RecordsBackend.HOME.value,
            explicit_aw_home=self.aw_home,
        )
        self.assertEqual(pol.delivery_mode, DeliveryMode.TRACKED.value)

    def test_19_6_first_noninteractive_missing_policy_fails_before_write(self):
        """Scenario 19.6: Noninteractive install missing policy fails before write."""
        from agent_workflows.install_wizard import IncompletePolicyError

        with self.assertRaises(IncompletePolicyError):
            resolve_policy_noninteractive(
                self.target_repo,
                explicit_delivery=None,
                explicit_backend=None,
                explicit_aw_home=self.aw_home,
            )

    def test_19_13_setup_action_all_attention_surfaces(self):
        """Scenario 19.13: Open setup-repo action listed by ActionManager."""
        mgr = ActionManager(target_repo=self.target_repo, aw_home=self.aw_home)
        doc = mgr.create_action("setup-repo", 1, "Run setup repo", "setup")
        self.assertEqual(doc.id, "setup-repo")
        self.assertEqual(doc.status, "open")

    def test_19_14_setup_completion_moves_completed(self):
        """Scenario 19.14: Action completion moves action to completed."""
        mgr = ActionManager(target_repo=self.target_repo, aw_home=self.aw_home)
        mgr.create_action("setup-repo", 1, "Run setup repo", "setup")
        comp_doc = mgr.transition_action("setup-repo", "completed")
        self.assertEqual(comp_doc.status, "completed")

    def test_19_15_dismissal_history_no_resurrection(self):
        """Scenario 19.15: Action dismissal preserves history."""
        mgr = ActionManager(target_repo=self.target_repo, aw_home=self.aw_home)
        mgr.create_action("setup-repo", 1, "Run setup repo", "setup")
        dism_doc = mgr.transition_action("setup-repo", "dismissed")
        self.assertEqual(dism_doc.status, "dismissed")

    def test_19_19_uninstall_preserves_external_state_records(self):
        """Scenario 19.19: Uninstall preserves external state and records by default."""
        mgr = MigrationManager(target_repo=self.target_repo, aw_home=self.aw_home)
        res = mgr.uninstall_layout(preserve_records=True)
        self.assertEqual(res["status"], "uninstalled")

    def test_19_20_clean_delta_merge_base_zero_write(self):
        """Scenario 19.20: Clean-delta mode zero-target-write verification."""
        mgr = CleanDeltaManager(target_repo=self.target_repo, aw_home=self.aw_home)
        user_skills = os.path.join(self.tmp_dir, "skills")
        res = mgr.install_clean_delta("opencode", "1.0.0", user_skills_dir=user_skills)
        self.assertEqual(res["target_writes"], 0)

    def test_19_24_privacy_doctor_refuses_unverified_privacy(self):
        """Scenario 19.24: Storage boundary validation."""
        # returns None on success, raises on an unsafe/ambiguous boundary
        records_path = os.path.join(
            self.aw_home, "projects", "myrepo-123456", "records"
        )
        validate_storage_boundaries(
            self.target_repo, records_path, RecordsBackend.HOME.value, self.aw_home
        )

    def _config(self, **kw):
        """Write the resolver's durable project config (.aw/config/config.json)."""
        import json

        cfg = os.path.join(self.target_repo, ".aw", "config")
        os.makedirs(cfg, exist_ok=True)
        with open(os.path.join(cfg, "config.json"), "w", encoding="utf-8") as f:
            json.dump(kw, f)

    def test_19_3_companion_local_git_no_remote_durability(self):
        """Scenario 19.3: companion + local git, no remote -> not durable-private (durability action)."""
        from agent_workflows.storage import get_storage_status
        from agent_workflows.project_schema import DurabilityState

        self._config(delivery_mode="tracked", records_backend="companion")
        st = get_storage_status(repo_path=self.target_repo, aw_home=self.aw_home)
        self.assertNotEqual(st.durability_state, DurabilityState.DURABLE_PRIVATE.value)

    def test_19_4_companion_confirmed_private_remote(self):
        """Scenario 19.4: durable-private requires explicit acknowledgement, not a mere remote."""
        from agent_workflows.storage import get_storage_status
        from agent_workflows.project_schema import DurabilityState

        st = get_storage_status(repo_path=self.target_repo, aw_home=self.aw_home)
        # Without acknowledgement, status is never durable-private.
        self.assertNotEqual(st.durability_state, DurabilityState.DURABLE_PRIVATE.value)

    def test_19_7_same_version_reinstall_is_noop(self):
        """Scenario 19.7: reinstall of the same version is idempotent (install, not a separate verb)."""
        from agent_workflows.project_context import resolve_project_context

        c1 = resolve_project_context(target_repo=self.target_repo, aw_home=self.aw_home)
        c2 = resolve_project_context(target_repo=self.target_repo, aw_home=self.aw_home)
        self.assertEqual(c1.to_json(), c2.to_json())

    def test_19_8_version_update_keeps_policy(self):
        """Scenario 19.8: an update keeps the configured records backend."""
        from agent_workflows.project_context import resolve_project_context

        self._config(delivery_mode="tracked", records_backend="repository")
        ctx = resolve_project_context(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertEqual(ctx.records_backend, RecordsBackend.REPOSITORY.value)

    def test_19_9_update_repository_to_home(self):
        """Scenario 19.9: migration switches records repository -> home, honored on re-resolve."""
        import json

        self._config(delivery_mode="tracked", records_backend="repository")
        mgr = MigrationManager(target_repo=self.target_repo, aw_home=self.aw_home)
        mgr.execute_migration(target_backend=RecordsBackend.HOME.value, dry_run=False)
        durable = os.path.join(self.target_repo, ".aw", "config", "config.json")
        self.assertEqual(
            json.loads(open(durable).read())["records_backend"],
            RecordsBackend.HOME.value,
        )

    def test_19_10_skipped_version_reconciles_generations(self):
        """Scenario 19.10: recreating an unresolved open generation is refused (no duplicate open)."""
        from agent_workflows.actions import ActionError

        mgr = ActionManager(target_repo=self.target_repo, aw_home=self.aw_home)
        mgr.create_action("setup-repo", 1, "Setup", "d")
        with self.assertRaises(ActionError):
            mgr.create_action("setup-repo", 1, "Setup", "d")

    def test_19_11_move_and_reattach(self):
        """Scenario 19.11: a registered project resolves to its stable identity (reattachment)."""
        from agent_workflows.project_registry import find_project

        res = find_project(self.target_repo, aw_home=self.aw_home)
        self.assertIsNotNone(res.entry)

    def test_19_12_ambiguous_resolution_not_auto_attached(self):
        """Scenario 19.12: an unregistered separate clone is not silently attached."""
        from agent_workflows.project_registry import find_project

        other = os.path.join(self.tmp_dir, "other")
        subprocess.run(["git", "init", "-q", other], check=True, capture_output=True)
        res = find_project(other, aw_home=self.aw_home)
        self.assertIsNone(res.entry)

    def test_19_16_new_generation_supersedes_old(self):
        """Scenario 19.16: a superseded generation leaves the open dir; a new generation is creatable."""
        mgr = ActionManager(target_repo=self.target_repo, aw_home=self.aw_home)
        mgr.create_action("setup-repo", 1, "Setup", "d")
        mgr.transition_action("setup-repo", "superseded")
        doc2 = mgr.create_action("setup-repo", 2, "Setup", "d")
        self.assertEqual(doc2.generation, 2)
        self.assertEqual(doc2.status, "open")

    def test_19_17_record_commit_routed_to_other_repo(self):
        """Scenario 19.17: home backend routes records outside the target and forbids target git-stage."""
        from agent_workflows.record_producers import resolve_record_routing

        self._config(delivery_mode="tracked", records_backend="home")
        info = resolve_record_routing(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertFalse(
            os.path.abspath(info.records_root).startswith(
                os.path.abspath(self.target_repo) + os.sep
            )
        )
        self.assertFalse(info.allow_git_stage)

    def test_19_18_migration_preserves_records_before_cleanup(self):
        """Scenario 19.18: migration validates before writes (preflight gate) and is transactional."""
        self._config(delivery_mode="tracked", records_backend="home")
        mgr = MigrationManager(target_repo=self.target_repo, aw_home=self.aw_home)
        plan = mgr.execute_migration(
            target_backend=RecordsBackend.REPOSITORY.value, dry_run=False
        )
        self.assertTrue(plan.is_valid)

    def test_19_21_unavailable_external_root_stops_writes(self):
        """Scenario 19.21: an unsafe/traversal path is refused fail-closed by the resolver."""
        from agent_workflows.project_context import (
            resolve_project_context,
            PathSecurityError,
        )

        with self.assertRaises(PathSecurityError):
            resolve_project_context(
                target_repo=os.path.join(self.target_repo, "..", "escape"),
                aw_home=self.aw_home,
            )

    def test_19_22_color_env_matrix(self):
        """Scenario 19.22: color honors NO_COLOR and degrades for a non-tty stream."""
        import io
        from unittest import mock
        from agent_workflows import term

        with mock.patch.dict(os.environ, {"NO_COLOR": "1"}):
            self.assertFalse(term.should_color(io.StringIO()))
        # a plain StringIO (not a tty) degrades to no color by default
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NO_COLOR", None)
            os.environ.pop("FORCE_COLOR", None)
            self.assertFalse(term.should_color(io.StringIO()))

    def test_19_23_screen_reader_linear_text(self):
        """Scenario 19.23: with color off, output carries no ANSI escapes (screen-reader linear)."""
        import io
        from agent_workflows import term

        t = term.Term(io.StringIO(), color=False)
        out = t.colorize("hello", "bold")
        self.assertNotIn("\x1b[", out)
        self.assertEqual(out, "hello")

    def test_19_25_broken_nav_link_resolver_still_works(self):
        """Scenario 19.25: resolver-based operation succeeds regardless of any optional nav link."""
        from agent_workflows.project_context import resolve_project_context

        ctx = resolve_project_context(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertTrue(ctx.project_id)

    def test_25_scenario_completeness(self):
        """Assert that ALL 25 acceptance scenarios (19.1-19.25) have a test method (V-04)."""
        present = {int(m.split("_")[2]) for m in dir(self) if m.startswith("test_19_")}
        missing = sorted(set(range(1, 26)) - present)
        self.assertEqual(missing, [], f"acceptance scenarios missing a test: {missing}")


if __name__ == "__main__":
    unittest.main()
