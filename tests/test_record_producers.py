"""Unit tests for the record/state class consolidation onto the layout model.

Spec `kw5y2s` Section 5.1 items 2 and 4; Set `wslayout` Order 03 (`rodj06`).

WHAT THIS FILE FENCES, and why each fence is here rather than assumed. Order 03 replaced three
hand-written enums and four hand-written subpath maps in `agent_workflows/record_producers.py` with
values DERIVED from `agent_workflows/layout.py`. A derivation is exactly the kind of change that can
look green while quietly altering a routing path, so these tests assert the three properties whose
violation the plan-review identified as the concrete failure modes:

1. THE `records` EMPTY-SUBPATH CARVE-OUT (spec Section 3.2.1, plan-review PR-001). `RecordClass`
   keeps a `RECORDS` member and it maps to the EMPTY string. A naive derivation would either drop
   the member (breaking every existing `RecordClass.RECORDS` caller) or give it `subpath="records"`,
   producing a nonsensical `records/records/` path.
2. THE PRESERVED LEGACY `.agents/` READ PATHS. `_LEGACY_RECORD_CLASS_SUBPATHS` stays DECOUPLED from
   the final map so `resolve_record_read_paths` still finds `.agents/docs/specs` and friends after
   the final layout was flattened out of `docs/`.
3. THE WRITE GUARD, which is a security boundary and must reject exactly what it rejected before.

NON-NARROWING IS THE OTHER HALF. The consolidation is only behavior-preserving if every class that
existed before still exists with the same value, so the pre-Order-03 nine are pinned LITERALLY here
rather than compared against the model (a model comparison would be a tautology once the module
derives from it, and could not catch a narrowing at all - the same reasoning Order 02 applied when
it converted the parity assertions in `tests/test_layout.py`).

NO THIRD-PARTY IMPORTS; plain stdlib `unittest`, matching the rest of the suite.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows import layout as _layout
from agent_workflows import record_producers as RP
from agent_workflows.project_registry import register_or_update_project
from agent_workflows.project_schema import (
    DeliveryMode,
    LogicalRoot,
    RecordsBackend,
    RootClass,
)

# The record classes that existed BEFORE the Order 03 consolidation, with their exact values. Pinned
# as a literal so a narrowing fails here; see the module docstring.
_PRE_CONSOLIDATION_RECORD_CLASSES = (
    "plans",
    "specs",
    "research",
    "records",
    "prompts",
    "comms",
    "walkthroughs",
    "releases",
    "reviews",
)

# The three classes the maintainer's UNION ruling adds (spec Section 3.2, Section 5.1 item 2).
_UNION_NET_NEW_RECORD_CLASSES = ("backlog", "roadmaps", "other")


class DerivedRecordClassTests(unittest.TestCase):
    """`RecordClass` is derived from the layout model without narrowing (E-01)."""

    def test_every_pre_consolidation_class_survives_with_its_value(self) -> None:
        live = {c.value for c in RP.RecordClass}
        for name in _PRE_CONSOLIDATION_RECORD_CLASSES:
            self.assertIn(
                name,
                live,
                "record class {0!r} existed before Order 03 and must not be dropped".format(
                    name
                ),
            )

    def test_static_member_attributes_still_resolve(self) -> None:
        # The derivation upper-cases the value to form the member name, which is the convention the
        # hand-written enums already followed. Every one of these attribute accesses appears in
        # shipped code or tests, so a changed naming rule would be an ImportError-class break.
        self.assertEqual(RP.RecordClass.PLANS.value, "plans")
        self.assertEqual(RP.RecordClass.SPECS.value, "specs")
        self.assertEqual(RP.RecordClass.RESEARCH.value, "research")
        self.assertEqual(RP.RecordClass.RECORDS.value, "records")
        self.assertEqual(RP.RecordClass.PROMPTS.value, "prompts")
        self.assertEqual(RP.RecordClass.COMMS.value, "comms")
        self.assertEqual(RP.RecordClass.WALKTHROUGHS.value, "walkthroughs")
        self.assertEqual(RP.RecordClass.RELEASES.value, "releases")
        self.assertEqual(RP.RecordClass.REVIEWS.value, "reviews")

    def test_union_net_new_classes_are_gained(self) -> None:
        live = {c.value for c in RP.RecordClass}
        for name in _UNION_NET_NEW_RECORD_CLASSES:
            self.assertIn(name, live)
        self.assertEqual(RP.RecordClass.BACKLOG.value, "backlog")
        self.assertEqual(RP.RecordClass.ROADMAPS.value, "roadmaps")
        self.assertEqual(RP.RecordClass.OTHER.value, "other")

    def test_class_set_is_exactly_the_model_vocabulary(self) -> None:
        model = _layout.build_default_layout()
        self.assertEqual(
            {c.value for c in RP.RecordClass},
            set(model.record_classes),
            "the enum must be the model's vocabulary, no more and no less",
        )

    def test_str_mixin_is_preserved_so_value_comparisons_keep_working(self) -> None:
        # `RecordClass` has always been a `str` subclass, and callers compare members to plain
        # strings and use them as dict keys. Losing the mixin would break those silently.
        self.assertIsInstance(RP.RecordClass.PLANS, str)
        self.assertEqual(RP.RecordClass.PLANS, "plans")
        self.assertEqual({RP.RecordClass.PLANS: 1}["plans"], 1)

    def test_enum_module_is_this_module_so_members_stay_picklable(self) -> None:
        # The functional `Enum` API otherwise records the calling frame's module, which breaks
        # pickling of a member; the derivation sets `__module__` explicitly.
        self.assertEqual(RP.RecordClass.__module__, "agent_workflows.record_producers")

    def test_state_class_enums_are_derived_and_unchanged(self) -> None:
        self.assertEqual(
            [c.value for c in RP.DurableStateClass],
            ["install", "history", "actions", "migrations", "routing_receipts"],
        )
        self.assertEqual(
            [c.value for c in RP.RuntimeStateClass],
            ["transactions", "locks", "staging", "backups", "cache", "tmp"],
        )
        self.assertEqual(
            RP.DurableStateClass.ROUTING_RECEIPTS.value, "routing_receipts"
        )
        self.assertEqual(RP.RuntimeStateClass.TRANSACTIONS.value, "transactions")


class RecordsCarveOutTests(unittest.TestCase):
    """The `records` root alias keeps its EMPTY subpath (spec 3.2.1, plan-review PR-001)."""

    def test_records_maps_to_the_empty_subpath(self) -> None:
        self.assertEqual(RP._RECORD_CLASS_SUBPATHS[RP.RecordClass.RECORDS.value], "")

    def test_records_is_not_given_a_literal_records_subpath(self) -> None:
        # THE SPECIFIC DEFECT THE CARVE-OUT PREVENTS: `subpath="records"` under a records ROOT that
        # already ends in `records` yields `.aw/records/records/`.
        self.assertNotEqual(
            RP._RECORD_CLASS_SUBPATHS[RP.RecordClass.RECORDS.value], "records"
        )

    def test_accessor_returns_empty_for_both_carve_outs(self) -> None:
        # `records` is the root ALIAS; `other` is the computed COMPLEMENT. Both denote the records
        # root rather than a child directory, so both must resolve to "".
        self.assertEqual(RP._record_class_subpath("records"), "")
        self.assertEqual(RP._record_class_subpath("other"), "")

    def test_other_has_no_literal_subpath_key(self) -> None:
        # `.aw/records/other/` does not exist: `selectors.record_dirs` computes `other` as the
        # complement of the owned trees, so inventing a literal entry would contradict the model
        # and manufacture a directory the sweep does not use.
        self.assertNotIn("other", RP._RECORD_CLASS_SUBPATHS)

    def test_every_other_class_keeps_a_nonempty_subpath(self) -> None:
        for name, sub in RP._RECORD_CLASS_SUBPATHS.items():
            if name == "records":
                continue
            self.assertTrue(sub, "class {0!r} must keep a real subpath".format(name))

    def test_final_subpaths_are_flat_with_no_docs_nesting(self) -> None:
        # Order 07 flattened the durable doc types out of `docs/`; the derivation must not
        # reintroduce the nesting into the FINAL map (only the LEGACY map keeps it).
        self.assertEqual(RP._RECORD_CLASS_SUBPATHS["specs"], "specs")
        self.assertEqual(RP._RECORD_CLASS_SUBPATHS["research"], "research")
        self.assertEqual(RP._RECORD_CLASS_SUBPATHS["walkthroughs"], "walkthroughs")


class LegacyReadPathTests(unittest.TestCase):
    """`_LEGACY_RECORD_CLASS_SUBPATHS` stays decoupled from the final map (F-3)."""

    def test_doc_family_keeps_its_docs_prefix(self) -> None:
        self.assertEqual(RP._LEGACY_RECORD_CLASS_SUBPATHS["specs"], "docs/specs")
        self.assertEqual(RP._LEGACY_RECORD_CLASS_SUBPATHS["research"], "docs/research")
        self.assertEqual(
            RP._LEGACY_RECORD_CLASS_SUBPATHS["walkthroughs"], "docs/walkthroughs"
        )

    def test_exactly_the_doc_family_differs_from_the_final_subpath(self) -> None:
        # The DECOUPLING is bounded: only these three classes ever had a legacy `docs/` tree. Any
        # other class inheriting a `docs/`-prefixed path would be an invented directory.
        differing = {
            name
            for name, sub in RP._LEGACY_RECORD_CLASS_SUBPATHS.items()
            if sub != RP._RECORD_CLASS_SUBPATHS.get(name)
        }
        self.assertEqual(differing, {"specs", "research", "walkthroughs"})

    def test_net_new_classes_inherit_their_final_subpath_by_absence(self) -> None:
        # Correct-by-absence, exactly as the hand-written `**` spread provided: a class with no
        # override reuses its final subpath. `reviews` is in this group too (it is net-new relative
        # to the legacy `.agents/` tree and carries a deliberate no-override note).
        for name in ("backlog", "roadmaps", "reviews"):
            self.assertEqual(
                RP._LEGACY_RECORD_CLASS_SUBPATHS[name],
                RP._RECORD_CLASS_SUBPATHS[name],
            )

    def test_legacy_map_covers_every_class_the_final_map_does(self) -> None:
        # So a migration read can never fall through to a KeyError for a class that routes fine
        # going forward.
        self.assertEqual(
            set(RP._LEGACY_RECORD_CLASS_SUBPATHS), set(RP._RECORD_CLASS_SUBPATHS)
        )

    def test_records_carve_out_survives_into_the_legacy_map(self) -> None:
        self.assertEqual(RP._LEGACY_RECORD_CLASS_SUBPATHS["records"], "")


class ProjectSchemaAlignmentTests(unittest.TestCase):
    """`LogicalRoot` (4) and `RootClass` (6) stay aligned but NOT collapsed (E-02, F-4)."""

    def test_logical_roots_are_exactly_the_four(self) -> None:
        self.assertEqual(
            [m.value for m in LogicalRoot], ["system", "config", "state", "records"]
        )

    def test_root_classes_are_exactly_the_six(self) -> None:
        self.assertEqual(
            [m.value for m in RootClass],
            [
                "system",
                "config_project",
                "config_local",
                "state_durable",
                "state_runtime",
                "records",
            ],
        )

    def test_the_two_enums_are_not_collapsed(self) -> None:
        # Spec Section 5.1 item 4: they answer different questions. `config` and `state` each split
        # into a tracked and an untracked half whose git policies are opposite.
        self.assertEqual(len(LogicalRoot), 4)
        self.assertEqual(len(RootClass), 6)
        self.assertNotEqual(
            {m.value for m in LogicalRoot}, {m.value for m in RootClass}
        )

    def test_both_enums_agree_with_the_layout_model(self) -> None:
        self.assertEqual({m.value for m in LogicalRoot}, set(_layout.LOGICAL_ROOTS))
        self.assertEqual({m.value for m in RootClass}, set(_layout.ROOT_CLASSES))

    def test_the_alignment_check_rejects_a_dropped_logical_root(self) -> None:
        # The guard must actually reject drift, so it is exercised rather than merely present. A
        # DROPPED member is the realistic drift: someone "simplifies" the enum and the model no
        # longer matches.
        import enum

        from agent_workflows import project_schema as PS

        narrowed = enum.Enum(
            "LogicalRoot",
            [("SYSTEM", "system"), ("CONFIG", "config"), ("STATE", "state")],
            type=str,
        )
        original = PS.LogicalRoot
        try:
            PS.LogicalRoot = narrowed
            with self.assertRaises(RuntimeError) as ctx:
                PS._assert_layout_alignment()
            self.assertIn("records", str(ctx.exception))
        finally:
            PS.LogicalRoot = original

    def test_the_alignment_check_rejects_collapsing_root_classes_to_four(self) -> None:
        # THE SPECIFIC PROHIBITION (spec Section 5.1 item 4): collapsing the six physical placement
        # classes into the four logical roots must not start up.
        import enum

        from agent_workflows import project_schema as PS

        collapsed = enum.Enum(
            "RootClass",
            [
                ("SYSTEM", "system"),
                ("CONFIG", "config"),
                ("STATE", "state"),
                ("RECORDS", "records"),
            ],
            type=str,
        )
        original = PS.RootClass
        try:
            PS.RootClass = collapsed
            with self.assertRaises(RuntimeError):
                PS._assert_layout_alignment()
        finally:
            PS.RootClass = original

    def test_the_alignment_check_passes_for_the_real_vocabularies(self) -> None:
        from agent_workflows import project_schema as PS

        PS._assert_layout_alignment()


class RoutingResolutionTests(unittest.TestCase):
    """`resolve_record_path` routes every class correctly after the derivation (V-01)."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)

        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = self.aw_home
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-rodj06"
        )

        config_dir = Path(self.target_repo) / ".aw" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.json").write_text(
            json.dumps(
                {
                    "delivery_mode": DeliveryMode.TRACKED.value,
                    "records_backend": RecordsBackend.REPOSITORY.value,
                    "aw_home": self.aw_home,
                }
            ),
            encoding="utf-8",
        )
        for rel in (
            (".aw", "records", "plans"),
            (".aw", "state", "durable"),
            (".aw", "state", "runtime"),
        ):
            os.makedirs(os.path.join(self.target_repo, *rel), exist_ok=True)

    def tearDown(self) -> None:
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _resolve(self, record_class: str, sub: str = "") -> str:
        return RP.resolve_record_path(
            record_class,
            sub,
            target_repo=self.target_repo,
            aw_home=self.aw_home,
        ).as_posix()

    def test_records_root_alias_resolves_to_the_root_not_a_nested_dir(self) -> None:
        # THE CARVE-OUT'S OBSERVABLE CONSEQUENCE, which is the point of the whole fence.
        resolved = self._resolve(RP.RecordClass.RECORDS.value)
        self.assertTrue(resolved.endswith(".aw/records"), resolved)
        self.assertNotIn("records/records", resolved)

    def test_records_root_alias_with_a_subpath_does_not_double_the_segment(
        self,
    ) -> None:
        resolved = self._resolve(RP.RecordClass.RECORDS.value, "README.md")
        self.assertTrue(resolved.endswith(".aw/records/README.md"), resolved)

    def test_pre_existing_classes_route_where_they_always_did(self) -> None:
        for name, expected in (
            ("plans", ".aw/records/plans/x.md"),
            ("specs", ".aw/records/specs/x.md"),
            ("research", ".aw/records/research/x.md"),
            ("prompts", ".aw/records/prompts/x.md"),
            ("comms", ".aw/records/comms/x.md"),
            ("walkthroughs", ".aw/records/walkthroughs/x.md"),
            ("releases", ".aw/records/releases/x.md"),
            ("reviews", ".aw/records/reviews/x.md"),
        ):
            resolved = self._resolve(name, "x.md")
            self.assertTrue(
                resolved.endswith(expected),
                "{0!r} resolved to {1!r}, expected it to end with {2!r}".format(
                    name, resolved, expected
                ),
            )

    def test_net_new_classes_route_to_where_those_artifacts_already_live(self) -> None:
        # The union ruling requires the new members' subpaths to MATCH the existing on-disk trees
        # (`.aw/records/backlog/`, `.aw/records/roadmaps/`), not to invent new directories.
        self.assertTrue(
            self._resolve("backlog", "x.md").endswith(".aw/records/backlog/x.md")
        )
        self.assertTrue(
            self._resolve("roadmaps", "x.md").endswith(".aw/records/roadmaps/x.md")
        )

    def test_other_complement_resolves_to_the_records_root(self) -> None:
        # `other` has no directory of its own, so it must resolve to the root rather than raise or
        # fabricate `.aw/records/other/`.
        resolved = self._resolve("other")
        self.assertTrue(resolved.endswith(".aw/records"), resolved)

    def test_state_classes_still_route_under_their_own_roots(self) -> None:
        durable = self._resolve(RP.DurableStateClass.HISTORY.value, "h.json")
        self.assertTrue(durable.endswith(".aw/state/durable/history/h.json"), durable)
        runtime = self._resolve(RP.RuntimeStateClass.LOCKS.value, "l.json")
        self.assertTrue(runtime.endswith(".aw/state/runtime/locks/l.json"), runtime)

    def test_install_durable_class_is_still_a_file_not_a_directory(self) -> None:
        resolved = self._resolve(RP.DurableStateClass.INSTALL.value)
        self.assertTrue(resolved.endswith(".aw/state/durable/install.json"), resolved)

    def test_an_unknown_class_is_still_rejected(self) -> None:
        with self.assertRaises(RP.InvalidRecordClassError):
            self._resolve("nonexistent_class")

    def test_parent_traversal_in_a_subpath_is_still_rejected(self) -> None:
        with self.assertRaises(RP.UnsafeSymlinkError):
            self._resolve("plans", "../../../etc/passwd")

    def test_an_absolute_subpath_is_still_rejected(self) -> None:
        with self.assertRaises(RP.UnsafeSymlinkError):
            self._resolve("plans", "/etc/passwd")

    def test_legacy_read_paths_resolve_for_a_doc_family_class(self) -> None:
        # With a retention manifest present, the legacy `.agents/docs/specs` tree must be returned
        # in ADDITION to the flat primary, which is the whole reason the legacy map stays decoupled.
        manifest = (
            Path(self.target_repo)
            / ".aw"
            / "state"
            / "durable"
            / "migrations"
            / "retention_manifest.json"
        )
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({"retained": True}), encoding="utf-8")
        legacy = Path(self.target_repo) / ".agents" / "docs" / "specs"
        legacy.mkdir(parents=True, exist_ok=True)

        paths = [
            p.as_posix()
            for p in RP.resolve_record_read_paths(
                "specs", target_repo=self.target_repo, aw_home=self.aw_home
            )
        ]
        self.assertTrue(any(p.endswith(".aw/records/specs") for p in paths), paths)
        self.assertTrue(
            any(p.endswith(".agents/docs/specs") for p in paths),
            "the decoupled legacy subpath must still be resolved: {0}".format(paths),
        )

    def test_record_routing_still_reports_the_repository_backend(self) -> None:
        info = RP.resolve_record_routing(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertEqual(info.records_backend, RecordsBackend.REPOSITORY.value)
        self.assertTrue(info.allow_git_stage)
        self.assertEqual(info.commit_destination, "repository")
        self.assertTrue(info.records_root.endswith(".aw/records"), info.records_root)

    def test_git_owner_is_unchanged_for_records_and_runtime(self) -> None:
        self.assertEqual(
            RP.get_git_owner(
                RP.RecordClass.PLANS.value,
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            ),
            "target",
        )
        self.assertIsNone(
            RP.get_git_owner(
                RP.RuntimeStateClass.TRANSACTIONS.value,
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            )
        )

    def test_logical_root_vocabulary_is_still_used_by_the_router(self) -> None:
        info = RP.resolve_record_routing(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertIn(LogicalRoot.RECORDS.value, ("records",))
        self.assertTrue(info.records_root)


class WriteGuardTests(unittest.TestCase):
    """The central write guard is a security boundary and must be unchanged (V-01)."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)

        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = self.aw_home
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-rodj06-guard"
        )
        config_dir = Path(self.target_repo) / ".aw" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.json").write_text(
            json.dumps(
                {
                    "delivery_mode": DeliveryMode.TRACKED.value,
                    "records_backend": RecordsBackend.REPOSITORY.value,
                    "aw_home": self.aw_home,
                }
            ),
            encoding="utf-8",
        )
        for rel in (
            (".aw", "records", "plans"),
            (".aw", "state", "durable"),
            (".aw", "state", "runtime"),
        ):
            os.makedirs(os.path.join(self.target_repo, *rel), exist_ok=True)

    def tearDown(self) -> None:
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_a_legal_record_write_is_permitted(self) -> None:
        target = Path(self.target_repo) / ".aw" / "records" / "plans" / "new.ipd.md"
        result = RP.guard_write(
            target,
            record_class=RP.RecordClass.PLANS.value,
            target_repo=self.target_repo,
            aw_home=self.aw_home,
        )
        self.assertEqual(result, target)

    def test_a_legacy_agents_write_is_still_rejected(self) -> None:
        with self.assertRaises(RP.LegacyWriteError):
            RP.guard_write(
                Path(self.target_repo) / ".agents" / "docs" / "specs" / "x.spec.md",
                record_class=RP.RecordClass.SPECS.value,
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            )

    def test_a_workflow_artifacts_write_is_still_rejected(self) -> None:
        with self.assertRaises(RP.LegacyWriteError):
            RP.guard_write(
                Path(self.target_repo) / "workflow-artifacts" / "assess" / "x.md",
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            )

    def test_a_producer_write_into_the_runtime_state_root_is_still_rejected(
        self,
    ) -> None:
        with self.assertRaises(RP.ForbiddenWriteError):
            RP.guard_write(
                Path(self.target_repo) / ".aw" / "state" / "runtime" / "locks" / "l",
                target_repo=self.target_repo,
                aw_home=self.aw_home,
                is_producer=True,
            )

    def test_a_pre_switch_migration_still_blocks_writes(self) -> None:
        tx = (
            Path(self.target_repo)
            / ".aw"
            / "state"
            / "runtime"
            / "transactions"
            / "migration_transaction.json"
        )
        tx.parent.mkdir(parents=True, exist_ok=True)
        tx.write_text("{}", encoding="utf-8")
        with self.assertRaises(RP.MigrationInFlightError):
            RP.guard_write(
                Path(self.target_repo) / ".aw" / "records" / "plans" / "x.ipd.md",
                record_class=RP.RecordClass.PLANS.value,
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            )

    def test_the_guard_exception_hierarchy_is_unchanged(self) -> None:
        # Callers catch at these levels, so the hierarchy is part of the contract.
        self.assertTrue(issubclass(RP.LegacyWriteError, RP.GuardError))
        self.assertTrue(issubclass(RP.ForbiddenWriteError, RP.GuardError))
        self.assertTrue(issubclass(RP.MigrationInFlightError, RP.GuardError))
        self.assertTrue(issubclass(RP.UnsafeSymlinkError, RP.GuardError))
        self.assertTrue(issubclass(RP.StaleContextError, RP.GuardError))
        self.assertTrue(issubclass(RP.CrossGitStagingError, RP.GuardError))
        self.assertTrue(issubclass(RP.GuardError, RP.RecordProducerError))
        self.assertTrue(issubclass(RP.InvalidRecordClassError, RP.RecordProducerError))
        self.assertTrue(issubclass(RP.InvalidRecordClassError, ValueError))
        self.assertTrue(issubclass(RP.DuplicateAuthorityError, RP.RecordProducerError))


class ProducerInventoryTests(unittest.TestCase):
    """`PRODUCER_INVENTORY` is untouched by the vocabulary consolidation."""

    def test_inventory_is_non_empty_and_every_category_is_a_known_class(self) -> None:
        self.assertTrue(RP.PRODUCER_INVENTORY)
        known = {c.value for c in RP.RecordClass}
        for entry in RP.PRODUCER_INVENTORY:
            self.assertIn(
                entry.category,
                known,
                "producer {0!r} routes to unknown class {1!r}".format(
                    entry.name, entry.category
                ),
            )

    def test_the_legacy_allowlist_still_holds_only_non_writers(self) -> None:
        self.assertTrue(RP.LEGACY_ALLOWLIST)
        self.assertNotIn("agent_workflows/record_producers.py", RP.LEGACY_ALLOWLIST)

    def test_no_known_writer_module_reintroduced_a_legacy_write_sink(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        self.assertEqual(RP.discover_legacy_write_sinks(repo_root), set())


if __name__ == "__main__":
    unittest.main()
