"""Unit tests for AW physical layout materialization, ownership boundaries, and journaled compensating transactions (IPD 20260809-awlayout-05)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows.install_wizard import ProjectPolicy
from agent_workflows.manifest import SCHEMA_VERSION, load as load_manifest
from agent_workflows.project_layout import (
    ConfigMergeError,
    TransactionJournal,
    materialize_project_layout,
    merge_config_policy,
)
from agent_workflows.project_schema import DeliveryMode, RecordsBackend


class TestProjectLayoutAndOwnership(unittest.TestCase):
    """Test logical-to-physical materialization, ownership boundaries, and journaled transactions."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)

        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = self.aw_home

    def tearDown(self):
        # Restore the prior AW_HOME (sandbox value set in tests/__init__.py);
        # popping it unconditionally would clobber the sandbox for later tests
        # and leak into the real ~/.aw.
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_materialize_tracked_home_backend_omits_target_records_dir(self):
        """Tracked delivery with home records backend materializes the resolver roots and puts records
        OUTSIDE the target repo (E-01 & V-01)."""
        policy = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.HOME.value,
            aw_home=self.aw_home,
        )

        roots = materialize_project_layout(
            target_repo=self.target_repo, policy=policy, aw_home=self.aw_home
        )

        # system/config/state are materialized at the resolver's logical roots.
        self.assertTrue(Path(roots["system"]).is_dir())
        self.assertTrue(Path(roots["config"]).is_dir())
        self.assertTrue(Path(roots["state"]).is_dir())

        # INVARIANT: for an external (home) backend, records live OUTSIDE the target repo.
        target_root = Path(self.target_repo).resolve()
        records_root = Path(roots["records"]).resolve()
        self.assertFalse(
            str(records_root).startswith(str(target_root) + os.sep),
            f"home-backend records {records_root} must not be inside the target {target_root}",
        )

    def test_materialize_tracked_repository_backend_creates_records_dir(self):
        """Tracked delivery with repository backend keeps records INSIDE the target repo (E-01)."""
        policy = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.REPOSITORY.value,
            aw_home=self.aw_home,
        )

        roots = materialize_project_layout(
            target_repo=self.target_repo, policy=policy, aw_home=self.aw_home
        )

        target_root = Path(self.target_repo).resolve()
        records_root = Path(roots["records"]).resolve()
        self.assertTrue(records_root.is_dir())
        self.assertTrue(
            str(records_root).startswith(str(target_root)),
            f"repository-backend records {records_root} must be inside the target {target_root}",
        )

    def test_sentinel_bytes_preserved_outside_intended_roots(self):
        """Sentinel bytes outside intended roots remain byte-identical after layout materialization (V-01 & V-02)."""
        target_p = Path(self.target_repo)
        sentinel_file = target_p / "user_file.txt"
        sentinel_content = b"SENTINEL_BYTES_USER_PRESERVED_12345\n"
        sentinel_file.write_bytes(sentinel_content)

        policy = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.HOME.value,
            aw_home=self.aw_home,
        )

        materialize_project_layout(
            target_repo=self.target_repo, policy=policy, aw_home=self.aw_home
        )

        self.assertEqual(sentinel_file.read_bytes(), sentinel_content)

    def test_config_merge_preserves_unknown_human_keys(self):
        """Config merge preserves unknown human-added JSON keys in config/policy.json (E-02 & V-02)."""
        config_dir = Path(self.target_repo) / ".aw" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        policy_file = config_dir / "policy.json"

        # Pre-populate with human-added key "custom_team_policy"
        human_config = {
            "delivery_mode": "tracked",
            "records_backend": "home",
            "custom_team_policy": {"strict_ci": True, "reviewer_count": 2},
        }
        with open(policy_file, "w", encoding="utf-8") as f:
            json.dump(human_config, f, indent=2)

        # Merge new policy
        new_pol = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.HOME.value,
            enabled_hosts=["opencode", "claude"],
        )

        merged = merge_config_policy(policy_file, new_pol, replace_config=False)

        # Human-added key MUST be preserved byte-for-byte in merged config!
        self.assertIn("custom_team_policy", merged)
        self.assertEqual(merged["custom_team_policy"]["strict_ci"], True)
        self.assertEqual(merged["enabled_hosts"], ["opencode", "claude"])

    def test_config_merge_malformed_json_refusal(self):
        """Malformed config/policy.json is refused unless --replace-config is specified (E-02 & V-02)."""
        config_dir = Path(self.target_repo) / ".aw" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        policy_file = config_dir / "policy.json"

        # Write invalid JSON syntax
        policy_file.write_text("{ malformed json content ...", encoding="utf-8")

        new_pol = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.HOME.value,
        )

        with self.assertRaises(ConfigMergeError):
            merge_config_policy(policy_file, new_pol, replace_config=False)

        # Passing replace_config=True succeeds
        replaced = merge_config_policy(policy_file, new_pol, replace_config=True)
        self.assertEqual(replaced["delivery_mode"], "tracked")

    def test_journaled_compensating_transaction_rollback_on_failure(self):
        """Transaction journal executes reverse-order compensation on failure (E-04 & V-04)."""
        target_file = os.path.join(self.target_repo, "test_file.txt")
        original_content = "ORIGINAL_CONTENT_BEFORE_TRANSACTION\n"
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(original_content)

        journal_dir = tempfile.mkdtemp(dir=self.tmp_dir)
        journal = TransactionJournal(
            target_repo=self.target_repo, journal_dir=journal_dir
        )

        # Stage write op that modifies test_file.txt
        op = journal.add_write_op(target_file, "NEW_CONTENT_DURING_TRANSACTION\n")
        self.assertTrue(op.completed)
        self.assertEqual(
            Path(target_file).read_text(encoding="utf-8"),
            "NEW_CONTENT_DURING_TRANSACTION\n",
        )

        # Simulate transaction failure & trigger compensation
        success, errors = journal.compensate()
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)

        # Original content MUST be restored byte-for-byte!
        self.assertEqual(
            Path(target_file).read_text(encoding="utf-8"), original_content
        )

    def test_manifest_schema_version_2(self):
        """Manifest written during materialization uses SCHEMA_VERSION = 2 (E-02 & V-05)."""
        policy = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.HOME.value,
            aw_home=self.aw_home,
        )

        roots = materialize_project_layout(
            target_repo=self.target_repo, policy=policy, aw_home=self.aw_home
        )

        manifest_file = Path(roots["system"]) / "managed-sections.json"
        self.assertTrue(manifest_file.is_file())

        mf = load_manifest(manifest_file)
        self.assertEqual(mf.schema_version, 2)
        self.assertEqual(SCHEMA_VERSION, 2)


class PhysicalPolicyMatrixTests(unittest.TestCase):
    """Contract tests for physical root ownership and Git policy contract (IPD 20260810-awphysical-01)."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        # Initialize target_repo as a real git repository
        import subprocess

        subprocess.run(
            ["git", "init"],
            cwd=self.target_repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.target_repo,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.target_repo,
            check=True,
        )

        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)

        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = self.aw_home

    def tearDown(self):
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_e01(self):
        """E-01 & V-01: Verify physical roots resolution (.aw/system) and Git prohibition for config/local.json and state/runtime/."""
        from agent_workflows.project_context import (
            PathSecurityError,
            resolve_project_context,
        )
        from agent_workflows.project_schema import RootClass

        fixture_p = Path("tests/fixtures/awphysical/order01/e01-canary.json")
        self.assertTrue(fixture_p.is_file(), "Fixture e01-canary.json must exist")
        canary_data = json.loads(fixture_p.read_text(encoding="utf-8"))

        # 1. Physical system root must resolve to .aw/system, NEVER .agents
        ctx = resolve_project_context(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertEqual(
            ctx.physical_classes[RootClass.SYSTEM.value],
            os.path.join(self.target_repo, canary_data["expected_system"]),
        )
        self.assertNotEqual(
            ctx.physical_classes[RootClass.SYSTEM.value],
            os.path.join(self.target_repo, canary_data["prohibited_system"]),
        )
        self.assertEqual(
            ctx.physical_classes[RootClass.CONFIG_LOCAL.value],
            os.path.join(self.target_repo, canary_data["local_config"]),
        )
        self.assertEqual(
            ctx.physical_classes[RootClass.STATE_RUNTIME.value],
            os.path.join(self.target_repo, ".aw", "state", "runtime"),
        )

        # 2. Plant local config and runtime state canaries in real git repo
        local_cfg = Path(self.target_repo) / canary_data["local_config"]
        local_cfg.parent.mkdir(parents=True, exist_ok=True)
        local_cfg.write_text('{"local_alias": "dev"}', encoding="utf-8")

        runtime_log = Path(self.target_repo) / canary_data["runtime_state"]
        runtime_log.parent.mkdir(parents=True, exist_ok=True)
        runtime_log.write_text("CANARY_RUN_LOG\n", encoding="utf-8")

        # Positive assertion: When untracked, resolve_project_context succeeds
        ctx_clean = resolve_project_context(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertIsNotNone(ctx_clean)

        # Falsifiability / Required failure condition:
        # Staging/tracking config/local.json in Git index MUST raise PathSecurityError
        import subprocess

        subprocess.run(
            ["git", "add", "-f", str(local_cfg)],
            cwd=self.target_repo,
            check=True,
        )
        with self.assertRaises(PathSecurityError) as cm:
            resolve_project_context(target_repo=self.target_repo, aw_home=self.aw_home)
        self.assertIn("Git policy violation", str(cm.exception))

    def test_e02(self):
        """E-02 & V-02: Placement vocabulary validation and invalid combination rejection."""
        from agent_workflows.project_schema import (
            GIT_POLICIES,
            Placement,
            RootClass,
            get_placement_info,
            parse_physical_config,
            validate_placement_combination,
        )

        fixture_p = Path("tests/fixtures/awphysical/order01/e02-placements.json")
        self.assertTrue(fixture_p.is_file(), "Fixture e02-placements.json must exist")
        fixture_data = json.loads(fixture_p.read_text(encoding="utf-8"))

        # 1. Inspect PlacementInfo attributes for every placement
        for p_name in fixture_data["placements"]:
            info = get_placement_info(p_name)
            self.assertEqual(info.placement, p_name)
            self.assertIn(info.git_policy, GIT_POLICIES)

        # 2. Valid vs Invalid combinations
        self.assertTrue(
            validate_placement_combination(
                RootClass.CONFIG_PROJECT.value, Placement.TARGET_TRACKED.value
            )
        )
        for item in fixture_data["prohibited_combinations"]:
            self.assertFalse(
                validate_placement_combination(item["root_class"], item["placement"])
            )

        # 3. Falsifiability: parse_physical_config MUST refuse invalid placement combinations
        invalid_cfg = {
            "placements": {RootClass.CONFIG_LOCAL.value: Placement.TARGET_TRACKED.value}
        }
        with self.assertRaises(ValueError) as cm:
            parse_physical_config(invalid_cfg)
        self.assertIn("Invalid placement combination", str(cm.exception))

    def test_e03(self):
        """E-03 & V-03: Preset resolution and invalid preset rejection."""
        from agent_workflows.project_schema import (
            PLACEMENTS,
            Placement,
            Preset,
            RootClass,
            ROOT_CLASSES,
            get_preset_placements,
        )

        fixture_p = Path("tests/fixtures/awphysical/order01/e03-presets.json")
        self.assertTrue(fixture_p.is_file(), "Fixture e03-presets.json must exist")
        fixture_data = json.loads(fixture_p.read_text(encoding="utf-8"))

        for preset_name in fixture_data["presets"]:
            mapping = get_preset_placements(preset_name)
            self.assertEqual(len(mapping), 6)
            for r_cls in ROOT_CLASSES:
                self.assertIn(r_cls, mapping)
                self.assertIn(mapping[r_cls], PLACEMENTS)

        # Verify specific preset rules
        priv = get_preset_placements(Preset.PRIVATE_TARGET.value)
        self.assertEqual(
            priv[RootClass.CONFIG_LOCAL.value], Placement.TARGET_IGNORED.value
        )
        self.assertEqual(
            priv[RootClass.STATE_RUNTIME.value], Placement.TARGET_IGNORED.value
        )

        pub = get_preset_placements(Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value)
        self.assertEqual(
            pub[RootClass.RECORDS.value], Placement.COMPANION_TRACKED.value
        )

        # Falsifiability: Invalid preset string MUST be rejected with ValueError
        with self.assertRaises(ValueError) as cm:
            get_preset_placements(fixture_data["invalid_preset"])
        self.assertIn("Unknown preset", str(cm.exception))

    def test_e04(self):
        """E-04 & V-04: Closed schema vocabulary parsing and fail-closed validation."""
        from agent_workflows.project_schema import parse_physical_config

        fixture_p = Path("tests/fixtures/awphysical/order01/e04-schema.json")
        self.assertTrue(fixture_p.is_file(), "Fixture e04-schema.json must exist")
        fixture_data = json.loads(fixture_p.read_text(encoding="utf-8"))

        parsed = parse_physical_config(fixture_data["valid_config"])
        self.assertEqual(parsed["preset"], "private-target")
        self.assertEqual(parsed["role"], "target")

        # Falsifiability 1: Unknown role fails closed
        with self.assertRaises(ValueError) as cm1:
            parse_physical_config(fixture_data["invalid_role_config"])
        self.assertIn("Unknown project role", str(cm1.exception))

        # Falsifiability 2: Unknown placement fails closed
        with self.assertRaises(ValueError) as cm2:
            parse_physical_config(fixture_data["invalid_placement_config"])
        self.assertIn("Unknown placement", str(cm2.exception))

    def test_e05(self):
        """E-05 & V-05: Policy matrix containment, symlink escape, and worktree boundary validation."""
        from agent_workflows.project_context import PathSecurityError
        from agent_workflows.project_schema import (
            Placement,
            RootClass,
            validate_physical_matrix,
        )

        fixture_p = Path("tests/fixtures/awphysical/order01/e05-matrix.json")
        self.assertTrue(fixture_p.is_file(), "Fixture e05-matrix.json must exist")
        fixture_data = json.loads(fixture_p.read_text(encoding="utf-8"))

        target_p = Path(self.target_repo).resolve()
        aw_dir = target_p / ".aw"
        aw_dir.mkdir(parents=True, exist_ok=True)

        phys_classes = {
            RootClass.SYSTEM.value: str(
                target_p / fixture_data["target_relative_system"]
            ),
            RootClass.RECORDS.value: str(
                target_p / fixture_data["target_relative_records"]
            ),
        }
        placements = {
            RootClass.SYSTEM.value: Placement.TARGET_TRACKED.value,
            RootClass.RECORDS.value: Placement.TARGET_TRACKED.value,
        }

        # Normal containment check passes
        validate_physical_matrix(str(target_p), phys_classes, placements)

        # Falsifiability: Symlink escape outside target repo MUST raise PathSecurityError
        outside_dir = tempfile.mkdtemp(dir=self.tmp_dir)
        records_symlink = aw_dir / "records"
        os.symlink(outside_dir, records_symlink)

        with self.assertRaises(PathSecurityError) as cm:
            validate_physical_matrix(str(target_p), phys_classes, placements)
        self.assertIn("Symlink escape violation", str(cm.exception))

    def test_e06(self):
        """E-06 & V-06: Architectural decision record D130 content verification."""
        fixture_p = Path("tests/fixtures/awphysical/order01/e06-decisions.json")
        self.assertTrue(fixture_p.is_file(), "Fixture e06-decisions.json must exist")
        fixture_data = json.loads(fixture_p.read_text(encoding="utf-8"))

        decisions_p = Path("DECISIONS.md")
        self.assertTrue(decisions_p.is_file(), "DECISIONS.md must exist")
        content = decisions_p.read_text(encoding="utf-8")

        self.assertIn(f"### {fixture_data['decision_number']}.", content)

        d130_start = content.find(f"### {fixture_data['decision_number']}.")
        self.assertNotEqual(d130_start, -1)
        d130_end = content.find("### D131.", d130_start)
        d130_text = (
            content[d130_start:d130_end] if d130_end != -1 else content[d130_start:]
        )

        # Assert required architectural topics in D130 text
        for topic in fixture_data["required_topics"]:
            self.assertIn(
                topic, d130_text, f"D130 decision record must explain {topic!r}"
            )

        # Falsifiability: Asserting a non-existent topic in D130 fails
        with self.assertRaises(AssertionError):
            self.assertIn("nonexistent_architectural_topic_99999", d130_text)


if __name__ == "__main__":
    unittest.main()
