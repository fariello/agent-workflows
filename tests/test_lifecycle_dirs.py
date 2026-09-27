"""Tests for single-source lifecycle subdirectory table (Set placelib, Order 01, IPD d1lo52)."""

from __future__ import annotations

from pathlib import Path
import unittest

from agent_workflows import attention_contract
from agent_workflows import backlog
from agent_workflows import engine
from agent_workflows import ipd_lint
from agent_workflows import ipd_schema
from agent_workflows import layout
from agent_workflows import lifecycle_dirs
from agent_workflows import plans
from agent_workflows import record_placement
from agent_workflows import status_set


class ConsumerAgreementTests(unittest.TestCase):
    """Verify every consumer agrees with the canonical lifecycle_dirs table."""

    def test_record_classes_and_has_lifecycle_subdirs(self) -> None:
        model = layout.build_default_layout()
        for name, rc in model.record_classes.items():
            expected = lifecycle_dirs.subdirs_for(name)
            self.assertEqual(
                rc.lifecycle_subdirs,
                expected,
                f"layout record_class {name!r} lifecycle_subdirs mismatch",
            )
            self.assertEqual(
                record_placement.has_lifecycle_subdirs(name),
                bool(expected),
                f"record_placement.has_lifecycle_subdirs({name!r}) mismatch",
            )

    def test_target_subdir_identity(self) -> None:
        for rec_type, subdirs in lifecycle_dirs.LIFECYCLE_SUBDIRS.items():
            for d in subdirs:
                self.assertEqual(
                    record_placement.target_subdir(rec_type, d),
                    d,
                    f"target_subdir({rec_type!r}, {d!r}) did not return {d!r}",
                )

    def test_backlog_status_dirs(self) -> None:
        self.assertEqual(
            backlog.STATUS_DIRS, lifecycle_dirs.LIFECYCLE_SUBDIRS["backlog"]
        )

    def test_plans_disposition_dirs(self) -> None:
        expected = lifecycle_dirs.LIFECYCLE_SUBDIRS["plans"] + (
            lifecycle_dirs.PLANS_DONE_ALIAS,
        )
        self.assertEqual(plans.DISPOSITION_DIRS, expected)

    def test_engine_constants(self) -> None:
        self.assertEqual(
            engine.PLAN_LIFECYCLE_SUBDIRS, lifecycle_dirs.LIFECYCLE_SUBDIRS["plans"]
        )
        self.assertEqual(
            engine.PROMPT_LIFECYCLE_SUBDIRS, lifecycle_dirs.LIFECYCLE_SUBDIRS["prompts"]
        )

    def test_specs_status_vocabularies(self) -> None:
        specs_tuple = lifecycle_dirs.LIFECYCLE_SUBDIRS["specs"]
        self.assertEqual(attention_contract.SPEC_STATUSES, frozenset(specs_tuple))
        self.assertEqual(status_set.TYPE_STATUSES["specs"], set(specs_tuple))
        self.assertEqual(
            ipd_schema._ITEM_DEP_STATE_STATUSES["spec"], frozenset(specs_tuple)
        )

    def test_ipd_lint_dir_of(self) -> None:
        for d in lifecycle_dirs.LIFECYCLE_SUBDIRS["plans"]:
            self.assertEqual(ipd_lint._dir_of(Path("x") / d / "p.ipd.md"), d)

    def test_layout_to_dict_positional_specs_order(self) -> None:
        doc = layout.build_default_layout().to_dict("0")
        emitted_specs_subdirs = doc["record_classes"]["specs"]["lifecycle_subdirs"]
        self.assertEqual(
            emitted_specs_subdirs, list(lifecycle_dirs.LIFECYCLE_SUBDIRS["specs"])
        )

    def test_record_placement_has_lifecycle_subdirs_aliases(self) -> None:
        self.assertIs(record_placement.has_lifecycle_subdirs("plan"), True)
        self.assertIs(record_placement.has_lifecycle_subdirs("spec"), True)
