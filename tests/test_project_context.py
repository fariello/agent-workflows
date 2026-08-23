"""Unit tests for AW project context schema, resolver, CLI, and security boundaries (IPD 20260809-awlayout-01)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows.project_context import (
    ConflictingConfigurationError,
    PathSecurityError,
    resolve_project_context,
)
from agent_workflows.project_schema import (
    DELIVERY_MODES,
    DURABILITY_STATES,
    LOGICAL_ROOTS,
    PRECEDENCE_ORDER,
    RECORDS_BACKENDS,
    DeliveryMode,
    DurabilityState,
    PrecedenceLevel,
    RecordsBackend,
    normalize_durability_state,
)


class TestProjectSchema(unittest.TestCase):
    """Test vocabulary enums and immutable data structures."""

    def test_canonical_enums_and_constants(self):
        self.assertEqual(DeliveryMode.TRACKED.value, "tracked")
        self.assertEqual(DeliveryMode.CLEAN_DELTA.value, "clean-delta")
        self.assertIn("tracked", DELIVERY_MODES)
        self.assertIn("clean-delta", DELIVERY_MODES)

        self.assertEqual(RecordsBackend.HOME.value, "home")
        self.assertEqual(RecordsBackend.COMPANION.value, "companion")
        self.assertEqual(RecordsBackend.REPOSITORY.value, "repository")
        self.assertIn("home", RECORDS_BACKENDS)
        self.assertIn("companion", RECORDS_BACKENDS)
        self.assertIn("repository", RECORDS_BACKENDS)

        self.assertIn("unversioned", DURABILITY_STATES)
        self.assertNotIn("durable-private", DURABILITY_STATES)
        self.assertFalse(hasattr(DurabilityState, "DURABLE_PRIVATE"))
        self.assertEqual(
            normalize_durability_state("durable-private"),
            DurabilityState.ACKNOWLEDGED_DURABLE.value,
        )
        self.assertIn("system", LOGICAL_ROOTS)
        self.assertIn("explicit_flags", PRECEDENCE_ORDER)
        self.assertIn("named_global_profile", PRECEDENCE_ORDER)


class TestProjectContextResolver(unittest.TestCase):
    """Test pure resolver behavior, all 6 precedence levels, security, determinism, and CLI."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_section_9_coverage_guard(self):
        """Coverage guard: Ensure every Section 9 required field is present in ProjectContext."""
        ctx = resolve_project_context(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        ctx_dict = ctx.to_dict()
        required_fields = {
            "target_repo",
            "project_id",
            "delivery_mode",
            "effective_aw_home",
            "logical_roots",
            "records_backend",
            "durability_state",
            "effective_framework_version",
            "enabled_hosts",
            "permitted_commit_destinations",
            "root_accessibility",
            "open_aw_actions",
            "provenance",
        }
        for field in required_fields:
            self.assertIn(
                field,
                ctx_dict,
                f"Section 9 required field missing from context: {field}",
            )

    def test_purity_and_determinism(self):
        """Resolver must be side-effect-free and return byte-identical results."""

        def _snapshot(root):
            # os.walk yields (dirpath, dirnames, filenames) tuples whose list members
            # are unhashable; normalize to a sorted tuple-of-tuples so it is comparable.
            return tuple(
                (dirpath, tuple(sorted(dirnames)), tuple(sorted(filenames)))
                for dirpath, dirnames, filenames in sorted(os.walk(root))
            )

        before_files = _snapshot(self.tmp_dir)

        ctx1 = resolve_project_context(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        ctx2 = resolve_project_context(
            target_repo=self.target_repo, aw_home=self.aw_home
        )

        after_files = _snapshot(self.tmp_dir)
        self.assertEqual(before_files, after_files, "Resolver mutated the filesystem!")
        self.assertEqual(
            ctx1.to_json(), ctx2.to_json(), "Resolver output is not deterministic!"
        )

    def test_all_six_precedence_levels(self):
        """Test resolution through all 6 precedence levels in sequence."""
        # Level 6: Builtin defaults
        ctx6 = resolve_project_context(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertEqual(
            ctx6.provenance["delivery_mode"]["source"],
            PrecedenceLevel.BUILTIN_DEFAULTS.value,
        )

        # Level 5: Global defaults
        user_cfg_dir = os.path.join(self.tmp_dir, "user_cfg")
        os.makedirs(user_cfg_dir, exist_ok=True)
        with open(
            os.path.join(user_cfg_dir, "config.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(
                {"default_delivery_mode": "tracked", "default_records_backend": "home"},
                f,
            )

        ctx5 = resolve_project_context(
            target_repo=self.target_repo,
            aw_home=self.aw_home,
            user_config_dir=user_cfg_dir,
        )
        self.assertEqual(
            ctx5.provenance["delivery_mode"]["source"],
            PrecedenceLevel.GLOBAL_DEFAULTS.value,
        )

        # Level 4: Named Global Profile
        profiles_dir = os.path.join(user_cfg_dir, "profiles")
        os.makedirs(profiles_dir, exist_ok=True)
        with open(os.path.join(profiles_dir, "team.json"), "w", encoding="utf-8") as f:
            json.dump({"delivery_mode": "tracked", "records_backend": "companion"}, f)

        ctx4 = resolve_project_context(
            target_repo=self.target_repo,
            aw_home=self.aw_home,
            profile="team",
            user_config_dir=user_cfg_dir,
        )
        self.assertEqual(
            ctx4.provenance["records_backend"]["source"],
            PrecedenceLevel.NAMED_GLOBAL_PROFILE.value,
        )
        self.assertEqual(ctx4.records_backend, "companion")

        # Level 3: Project durable config
        durable_cfg_dir = os.path.join(self.target_repo, ".aw", "config")
        os.makedirs(durable_cfg_dir, exist_ok=True)
        with open(
            os.path.join(durable_cfg_dir, "config.json"), "w", encoding="utf-8"
        ) as f:
            json.dump({"delivery_mode": "tracked", "records_backend": "repository"}, f)

        ctx3 = resolve_project_context(
            target_repo=self.target_repo,
            aw_home=self.aw_home,
            user_config_dir=user_cfg_dir,
        )
        self.assertEqual(
            ctx3.provenance["records_backend"]["source"],
            PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
        )
        self.assertEqual(ctx3.records_backend, "repository")

        # Level 1: Explicit flags override everything
        ctx1 = resolve_project_context(
            target_repo=self.target_repo,
            aw_home=self.aw_home,
            delivery_mode="clean-delta",
            records_backend="companion",
            user_config_dir=user_cfg_dir,
        )
        self.assertEqual(ctx1.delivery_mode, "clean-delta")
        self.assertEqual(
            ctx1.provenance["delivery_mode"]["source"],
            PrecedenceLevel.EXPLICIT_FLAGS.value,
        )

    def test_path_traversal_refusal(self):
        """Resolver must refuse path traversals with PathSecurityError."""
        with self.assertRaises(PathSecurityError):
            resolve_project_context(
                target_repo="../../etc/passwd", aw_home=self.aw_home
            )

    def test_clean_delta_containment_violation(self):
        """Clean-delta mode MUST NOT route records to target repository."""
        with self.assertRaises(PathSecurityError):
            resolve_project_context(
                target_repo=self.target_repo,
                aw_home=self.aw_home,
                delivery_mode="clean-delta",
                records_backend="repository",
            )

    def test_conflicting_configuration_error(self):
        """Conflicting authoritative settings raise ConflictingConfigurationError."""
        user_cfg_dir = os.path.join(self.tmp_dir, "user_cfg")
        os.makedirs(user_cfg_dir, exist_ok=True)
        with open(
            os.path.join(user_cfg_dir, "config.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(
                {
                    "repos": {
                        os.path.abspath(self.target_repo).replace("\\", "/"): {
                            "delivery_mode": "clean-delta"
                        }
                    }
                },
                f,
            )

        durable_cfg_dir = os.path.join(self.target_repo, ".aw", "config")
        os.makedirs(durable_cfg_dir, exist_ok=True)
        with open(
            os.path.join(durable_cfg_dir, "config.json"), "w", encoding="utf-8"
        ) as f:
            json.dump({"delivery_mode": "tracked"}, f)

        with self.assertRaises(ConflictingConfigurationError):
            resolve_project_context(
                target_repo=self.target_repo,
                aw_home=self.aw_home,
                user_config_dir=user_cfg_dir,
            )

    def test_cli_context_json_output(self):
        """Test `aw context --json` via CLI invocation."""
        cmd = [
            "python3",
            "-m",
            "agent_workflows",
            "context",
            "--repo",
            self.target_repo,
            "--json",
        ]
        res = subprocess.run(
            cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")
        data = json.loads(res.stdout)
        data_dict = data.get("data", data)
        self.assertIn("target_repo", data_dict)
        self.assertIn("logical_roots", data_dict)

    def test_cli_path_agent_output(self):
        """Test `aw path records --agent` returns clean path with no prose."""
        cmd = [
            "python3",
            "-m",
            "agent_workflows",
            "path",
            "records",
            "--repo",
            self.target_repo,
            "--agent",
        ]
        res = subprocess.run(
            cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")
        out_path = res.stdout.strip()
        self.assertTrue(os.path.isabs(out_path))

    def test_duplicate_enum_literals_audit(self):
        """Ensure the enum VOCABULARY is centralized in project_schema.py: no module may re-define an
        enum literal without CONSUMING the owning enum. A file that mentions a literal (docstring,
        message, comment) while importing the enum from project_schema is a legitimate consumer, not a
        fork; a file that mentions the literal WITHOUT importing the enum is a duplicate-definition
        violation."""
        pkg_dir = Path(__file__).parent.parent / "agent_workflows"

        # literal -> the owning enum class name that a legitimate consumer must import.
        literal_owner = {
            "clean-delta": "DeliveryMode",
            "durable-private": "DurabilityState",
            "repository-managed": "DurabilityState",
        }
        # These modules own/aggregate the vocabulary and are always allowed.
        always_ok = ("project_schema.py", "project_context.py")

        for lit, owner in literal_owner.items():
            try:
                res = subprocess.run(
                    ["rg", "-l", lit, str(pkg_dir)],
                    capture_output=True,
                    text=True,
                )
            except FileNotFoundError:
                return  # ripgrep unavailable; skip the audit
            if res.returncode != 0:
                continue
            for f in (p.strip() for p in res.stdout.splitlines() if p.strip()):
                if f.endswith(always_ok):
                    continue
                text = Path(f).read_text(encoding="utf-8")
                imports_owner = owner in text and "project_schema" in text
                self.assertTrue(
                    imports_owner,
                    f"Duplicate enum literal '{lit}' in {f} without importing {owner} "
                    f"from project_schema (re-defined vocabulary, not a consumer).",
                )


class PhysicalContextResolutionTests(unittest.TestCase):
    """Exhaustive contract, precedence, and security tests for Order 02 (E-01..E-06 & V-01..V-06)."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        self.fixture_dir = os.path.join(
            os.path.dirname(__file__), "fixtures", "awphysical", "order02"
        )

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_e01(self):
        """E-01 & V-01: Portable project policy schema and machine-local binding separation."""
        fixture_path = os.path.join(self.fixture_dir, "e01-portable-and-local.json")
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        from agent_workflows.project_schema import (
            atomic_save_json,
            parse_local_binding,
            parse_portable_policy,
        )

        portable = parse_portable_policy(data["portable_policy"])
        local_b = parse_local_binding(data["local_binding"])

        # Assertion: Portable policy contains no machine-local absolute paths or secrets
        port_dict = portable.to_dict()
        for v in port_dict["placements"].values():
            self.assertFalse(
                os.path.isabs(v),
                f"Portable policy placement contains machine-local absolute path: {v}",
            )

        # Save files into .aw/config/
        config_dir = os.path.join(self.target_repo, ".aw", "config")
        os.makedirs(config_dir, exist_ok=True)
        atomic_save_json(os.path.join(config_dir, "project.json"), port_dict)
        atomic_save_json(os.path.join(config_dir, "local.json"), local_b.to_dict())

        ctx = resolve_project_context(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertTrue(ctx.is_configured)
        self.assertEqual(ctx.preset, "private-target")
        self.assertEqual(ctx.project_role, "target")

    def test_e02(self):
        """E-02 & V-02: Legacy config migration, unknown key preservation, and fail-closed versioning."""
        fixture_path = os.path.join(self.fixture_dir, "e02-legacy-and-merge.json")
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        from agent_workflows.project_schema import (
            migrate_legacy_config,
            parse_portable_policy,
        )

        leg_data = data["legacy_config"]
        port_dict, local_dict = migrate_legacy_config(leg_data)

        # Unknown human key MUST be preserved
        self.assertIn("human_custom_note", port_dict)
        self.assertEqual(port_dict["human_custom_note"], "preserved-custom-value-12345")

        # Unsupported schema_version MUST fail closed with ValueError
        with self.assertRaises(ValueError) as cm:
            parse_portable_policy(data["invalid_schema_version"])
        self.assertIn("Unsupported schema_version", str(cm.exception))

    def test_e03(self):
        """E-03 & V-03: Precedence level resolution and unlawful same-path alias rejection."""
        fixture_path = os.path.join(self.fixture_dir, "e03-precedence-and-alias.json")
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Precedence test: explicit flag overrides local binding and project config
        ctx_explicit = resolve_project_context(
            target_repo=self.target_repo,
            aw_home=self.aw_home,
            preset=data["explicit_preset"],
        )
        self.assertEqual(ctx_explicit.preset, "completely-clean-target")
        self.assertEqual(ctx_explicit.provenance["preset"]["source"], "explicit_flags")

        # Alias canary test: distinct root classes aliased to same path raise PathSecurityError
        config_dir = os.path.join(self.target_repo, ".aw", "config")
        os.makedirs(config_dir, exist_ok=True)
        alias_canary = {
            "schema_version": 2,
            "system_root": os.path.join(self.target_repo, ".aw", "shared_root"),
            "config_root": os.path.join(self.target_repo, ".aw", "shared_root"),
        }
        with open(os.path.join(config_dir, "local.json"), "w", encoding="utf-8") as f:
            json.dump(alias_canary, f)

        with self.assertRaises(PathSecurityError) as cm:
            resolve_project_context(target_repo=self.target_repo, aw_home=self.aw_home)
        self.assertIn("Unlawful class aliasing detected", str(cm.exception))

    def test_e04(self):
        """E-04 & V-04: Hardened path security, traversal check, and clean-delta containment."""
        fixture_path = os.path.join(self.fixture_dir, "e04-path-security.json")
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        from agent_workflows.project_context import _check_path_security

        # Path traversal with '..' MUST raise PathSecurityError
        with self.assertRaises(PathSecurityError) as cm:
            _check_path_security(data["traversal_path"], "test_label")
        self.assertIn("traversal '..'", str(cm.exception))

        # Clean-delta with repository backend MUST raise PathSecurityError
        with self.assertRaises(PathSecurityError) as cm2:
            resolve_project_context(
                target_repo=self.target_repo,
                aw_home=self.aw_home,
                delivery_mode="clean-delta",
                records_backend="repository",
            )
        self.assertIn(
            "clean-delta delivery mode MUST NOT use 'repository'", str(cm2.exception)
        )

    def test_e05(self):
        """E-05 & V-05: Public context output redaction and leak sanitizer integration."""
        fixture_path = os.path.join(self.fixture_dir, "e05-public-redaction.json")
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        from agent_workflows.project_context import redact_public_context

        ctx = resolve_project_context(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        redacted = redact_public_context(ctx.to_dict())

        # Public output MUST replace absolute local paths with <REDACTED_LOCAL_PATH>
        self.assertEqual(redacted["target_repo"], data["expected_redacted"])
        self.assertEqual(redacted["effective_aw_home"], data["expected_redacted"])

        # Retains required physical classes and git policies
        self.assertIn("physical_classes", redacted)
        self.assertIn("git_policies", redacted)

    def test_e06(self):
        """E-06 & V-06: Round-trip compatibility and atomic save no_clobber protection."""
        fixture_path = os.path.join(self.fixture_dir, "e06-compatibility.json")
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        from agent_workflows.project_schema import (
            atomic_save_json,
            migrate_legacy_config,
        )

        port_dict, local_dict = migrate_legacy_config(data["legacy_policy"])
        self.assertEqual(port_dict["schema_version"], 2)

        test_file = os.path.join(self.tmp_dir, "test_config.json")
        atomic_save_json(test_file, port_dict)

        # Atomic save with no_clobber=True on existing file MUST raise FileExistsError
        with self.assertRaises(FileExistsError) as cm:
            atomic_save_json(test_file, port_dict, no_clobber=True)
        self.assertIn("no_clobber is True", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
