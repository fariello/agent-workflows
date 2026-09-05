"""Unit tests for the canonical layout model (`agent_workflows/layout.py`; spec `kw5y2s`, Set
`wslayout` Order 01).

THE REGRESSION FENCE THIS FILE EXISTS TO BE. Order 01 is purely additive: nothing consumes
`layout.py` yet, so an INCOMPLETE INTERFACE here looks perfectly green and then fails in Order 02
or 03 as an ImportError or, worse, as a silent traversal change. These tests therefore assert the
model against the LIVE vocabularies it will replace, member for member, so a gap fails HERE.

NO THIRD-PARTY IMPORTS. Schema conformance is checked structurally with the stdlib rather than with
`jsonschema`, which is declared in neither the runtime deps nor the `[test]` extra and is absent on
Python 3.9 (a CI matrix version).

SET-VALUED CONSTANTS ARE COMPARED AS SETS. `selectors.EXCLUDED_RECORD_DIRS` and friends are
frozensets, so a `tuple(...) == tuple(...)` comparison would compare hash iteration order and be
`PYTHONHASHSEED`-dependent; the suite deliberately runs with `pytest-randomly` enabled.
"""

from __future__ import annotations

import json
import unittest

from agent_workflows import artifact_types as AT
from agent_workflows import layout
from agent_workflows import project_schema as PS
from agent_workflows import record_producers as RP
from agent_workflows import selectors


class LayoutModelDefaultsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = layout.build_default_layout()

    def test_logical_roots_are_the_four(self) -> None:
        self.assertEqual(
            set(self.model.logical_roots),
            {r.value for r in PS.LogicalRoot},
            "logical_roots must match project_schema.LogicalRoot exactly",
        )
        self.assertEqual(len(self.model.logical_roots), 4)

    def test_root_classes_are_the_six_and_are_not_collapsed(self) -> None:
        # Spec Section 5.1 item 4: the SIX physical placement classes must not collapse into the
        # FOUR logical roots; they answer different questions.
        self.assertEqual(
            set(self.model.root_classes),
            {r.value for r in PS.RootClass},
        )
        self.assertEqual(len(self.model.root_classes), 6)
        self.assertNotEqual(set(self.model.root_classes), set(self.model.logical_roots))

    def test_record_classes_are_the_union_of_both_live_vocabularies(self) -> None:
        # THE REGRESSION FENCE FOR THE UNION RULING (maintainer, 2026-09-01). A future edit that
        # silently drops `roadmaps`, or any other live type, must fail here.
        live_union = set(AT.ARTIFACT_TYPES) | {r.value for r in RP.RecordClass}
        modeled = set(self.model.record_classes)
        self.assertEqual(
            live_union - modeled,
            set(),
            "every live artifact type and record class must be modeled",
        )
        self.assertIn("roadmaps", modeled)
        self.assertIn("reviews", modeled)
        self.assertIn("backlog", modeled)
        self.assertIn("other", modeled)

    def test_artifact_types_reproduce_the_live_tuple_in_order(self) -> None:
        # ORDER MATTERS: `expand_types` returns types in ARTIFACT_TYPES order and the CLI error
        # message lists them in that order.
        self.assertEqual(
            self.model.artifact_types(include_reviews=False), AT.ARTIFACT_TYPES
        )

    def test_reviews_is_a_type_noun_only_in_the_union_view(self) -> None:
        # Net-new behavior owned and tested by Order 02; here we pin that the model can express
        # BOTH views, so the consolidation is a deliberate choice rather than an accident.
        self.assertNotIn("reviews", self.model.artifact_types(include_reviews=False))
        self.assertIn("reviews", self.model.artifact_types())

    def test_aliases_reproduce_the_live_map_exactly(self) -> None:
        modeled = self.model.alias_map()
        for alias, target in AT._ALIASES.items():
            self.assertEqual(
                modeled.get(alias),
                target,
                "alias {0!r} must be preserved".format(alias),
            )
        self.assertEqual(modeled.get("roadmap"), "roadmaps")
        self.assertEqual(modeled.get("others"), "other")
        self.assertEqual(modeled.get("misc"), "other")

    def test_records_is_the_root_alias_carve_out(self) -> None:
        rc = self.model.record_classes["records"]
        self.assertTrue(rc.is_root_alias)
        self.assertEqual(rc.subpath, "")
        self.assertEqual(
            self.model.record_subpaths()["records"],
            RP._RECORD_CLASS_SUBPATHS[RP.RecordClass.RECORDS.value],
        )
        self.assertEqual(RP._RECORD_CLASS_SUBPATHS[RP.RecordClass.RECORDS.value], "")

    def test_other_is_a_complement_without_a_literal_subpath(self) -> None:
        # `.aw/records/other/` does not exist; `selectors.record_dirs` computes `other` as the
        # complement of the owned trees. A literal `other` subpath would change traversal.
        rc = self.model.record_classes["other"]
        self.assertTrue(rc.is_complement)
        self.assertEqual(rc.subpath, "")
        self.assertNotIn("other", self.model.record_subpaths())

    def test_record_subpaths_match_the_live_final_map(self) -> None:
        modeled = self.model.record_subpaths()
        for name, sub in RP._RECORD_CLASS_SUBPATHS.items():
            self.assertEqual(
                modeled.get(name),
                sub,
                "subpath for {0!r} must be preserved".format(name),
            )

    def test_legacy_docs_prefixed_subpaths_survive(self) -> None:
        # `_LEGACY_RECORD_CLASS_SUBPATHS` must keep working for `.agents/` migration reads, so the
        # model cannot assume one subpath per class.
        modeled = self.model.legacy_record_subpaths()
        self.assertEqual(modeled["specs"], "docs/specs")
        self.assertEqual(modeled["research"], "docs/research")
        self.assertEqual(modeled["walkthroughs"], "docs/walkthroughs")
        for name, sub in RP._LEGACY_RECORD_CLASS_SUBPATHS.items():
            self.assertEqual(modeled.get(name), sub)
        # A SUPERSET, not an equal map, and the delta is exactly the union's net-new classes. They
        # inherit their FINAL subpath by absence of an override, which is the correct-by-absence
        # behavior the live `**` spread already provides; there is no legacy `.agents/` tree for
        # them to read, so hand-adding a legacy entry would invent a path.
        self.assertEqual(
            set(modeled) - set(RP._LEGACY_RECORD_CLASS_SUBPATHS),
            {"backlog", "roadmaps"},
        )
        self.assertEqual(modeled["backlog"], self.model.get_record_subpath("backlog"))
        self.assertEqual(modeled["roadmaps"], self.model.get_record_subpath("roadmaps"))

    def test_lifecycle_subdirs_match_the_live_status_dirs(self) -> None:
        from agent_workflows import backlog as BL

        self.assertEqual(
            set(self.model.record_classes["backlog"].lifecycle_subdirs),
            set(BL.STATUS_DIRS),
        )
        self.assertEqual(
            set(self.model.record_classes["plans"].lifecycle_subdirs),
            {"pending", "executed", "superseded", "not-executed", "reusable"},
        )


class ConsumerInterfaceTests(unittest.TestCase):
    """What Orders 02 and 03 import. A gap here is an ImportError in a LATER child."""

    def setUp(self) -> None:
        self.model = layout.build_default_layout()

    def test_primary_types_equal_the_live_known_primary_types(self) -> None:
        self.assertEqual(
            set(self.model.primary_types()), set(selectors.KNOWN_PRIMARY_TYPES)
        )
        self.assertEqual(len(self.model.primary_types()), 9)
        # And it is exactly ARTIFACT_TYPES minus `other`, which is how the live set is derived.
        self.assertEqual(
            set(self.model.primary_types()), set(AT.ARTIFACT_TYPES) - {"other"}
        )

    def test_non_primary_record_dirs_equal_the_live_set(self) -> None:
        self.assertEqual(
            set(self.model.non_primary_record_dirs()),
            set(selectors.NON_PRIMARY_RECORD_DIRS),
        )
        # Load-bearing: `reviews` must stay OUT of the `other` sweep. When it was in neither the
        # primary types nor the exclusions, a bare id6 matched twice and `aw set approved <id6>`
        # refused for every reviewed plan.
        self.assertIn("reviews", self.model.non_primary_record_dirs())

    def test_traversal_exclusions_equal_the_live_set_as_sets(self) -> None:
        # SETS, NOT TUPLES: EXCLUDED_RECORD_DIRS is a frozenset, so a positional comparison would
        # depend on PYTHONHASHSEED.
        self.assertEqual(
            set(self.model.traversal_exclusions), set(selectors.EXCLUDED_RECORD_DIRS)
        )
        self.assertEqual(len(self.model.traversal_exclusions), 7)
        # Pinned to the current seven: the widening to node_modules/venv/.venv is a deliberate,
        # separately validated behavior change owned by Order 02, not a side effect of sourcing.
        for widening in ("node_modules", "venv", ".venv"):
            self.assertNotIn(widening, self.model.traversal_exclusions)

    def test_exclusions_are_deterministically_ordered(self) -> None:
        # The model exposes an ORDERED tuple as part of its contract, so assert the order against a
        # literal expected sequence, never against the frozenset's incidental iteration order.
        self.assertEqual(
            self.model.traversal_exclusions,
            (
                ".git",
                ".system_generated",
                "__pycache__",
                "runs",
                "scratch",
                "temp",
                "tmp",
            ),
        )

    def test_other_sweep_skip_union_is_derived_from_the_three_inputs(self) -> None:
        # The DERIVED union is what actually gates the `other` complement in `selectors.py`.
        self.assertEqual(
            set(self.model.other_sweep_skip_dirs()),
            set(selectors._OTHER_SWEEP_SKIP_DIRS),
        )
        self.assertIn("reviews", self.model.other_sweep_skip_dirs())

    def test_the_three_dir_sets_are_disjoint(self) -> None:
        primary = set(self.model.primary_types())
        non_primary = set(self.model.non_primary_record_dirs())
        excluded = set(self.model.traversal_exclusions)
        self.assertEqual(primary & non_primary, set())
        self.assertEqual(primary & excluded, set())
        self.assertEqual(non_primary & excluded, set())

    def test_durable_state_classes_equal_the_live_vocabulary(self) -> None:
        self.assertEqual(
            set(self.model.durable_state_classes),
            {d.value for d in RP.DurableStateClass},
        )
        self.assertEqual(
            dict(self.model.durable_state_classes), RP._DURABLE_STATE_SUBPATHS
        )
        # `install` is a FILE (the install receipt), not a directory. That is the live value.
        self.assertEqual(self.model.durable_state_classes["install"], "install.json")

    def test_runtime_state_classes_equal_the_live_vocabulary(self) -> None:
        self.assertEqual(
            set(self.model.runtime_state_classes),
            {r.value for r in RP.RuntimeStateClass},
        )
        self.assertEqual(
            dict(self.model.runtime_state_classes), RP._RUNTIME_STATE_SUBPATHS
        )


class NormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = layout.build_default_layout()

    def test_canonical_and_alias_tokens_normalize(self) -> None:
        self.assertEqual(self.model.normalize_type("plans"), "plans")
        self.assertEqual(self.model.normalize_type("plan"), "plans")
        self.assertEqual(self.model.normalize_type("roadmap"), "roadmaps")
        self.assertEqual(self.model.normalize_type("misc"), "other")
        self.assertEqual(self.model.normalize_type("others"), "other")

    def test_normalization_agrees_with_the_live_helper_for_every_live_token(
        self,
    ) -> None:
        for token in list(AT.ARTIFACT_TYPES) + list(AT._ALIASES) + ["all"]:
            self.assertEqual(
                self.model.normalize_type(token),
                AT.normalize_type(token),
                "normalize_type({0!r}) must not change".format(token),
            )

    def test_all_expansion_token_passes_through(self) -> None:
        # `all` is NOT a record class and must never become one, but it MUST survive: every
        # `aw <verb> all` invocation depends on it.
        self.assertEqual(self.model.normalize_type("all"), "all")
        self.assertEqual(layout.EXPANSION_TOKEN_ALL, "all")
        self.assertNotIn("all", self.model.record_classes)
        self.assertTrue(self.model.is_known_type("all"))

    def test_expand_type_matches_the_live_expansion(self) -> None:
        self.assertEqual(
            self.model.expand_type("all", AT.ARTIFACT_TYPES),
            AT.expand_types("all", AT.ARTIFACT_TYPES),
        )
        self.assertEqual(self.model.expand_type("plan", AT.ARTIFACT_TYPES), ["plans"])

    def test_unknown_type_raises_valueerror_listing_the_valid_set(self) -> None:
        # MATCHES THE LIVE CONTRACT: `artifact_types.normalize_type` RAISES (it does not degrade),
        # and the message advertises `all`. `selectors.record_dirs` keeps its own returns-[]
        # convention; the two are deliberately NOT unified.
        for bad in ("nosuchtype", "", None):
            with self.assertRaises(ValueError) as ctx:
                self.model.normalize_type(bad)
            self.assertIn("unknown artifact type", str(ctx.exception))
            self.assertIn("all", str(ctx.exception))

    def test_is_known_type_is_falsy_tolerant_like_the_live_helper(self) -> None:
        for token in (None, ""):
            self.assertFalse(self.model.is_known_type(token))
            self.assertEqual(self.model.is_known_type(token), AT.is_type_token(token))
        for token in list(AT.ARTIFACT_TYPES) + list(AT._ALIASES) + ["all"]:
            self.assertTrue(self.model.is_known_type(token))

    def test_get_record_subpath_resolves_aliases_and_carve_outs(self) -> None:
        self.assertEqual(self.model.get_record_subpath("plan"), "plans")
        self.assertEqual(self.model.get_record_subpath("records"), "")
        self.assertEqual(self.model.get_record_subpath("other"), "")
        with self.assertRaises(ValueError):
            self.model.get_record_subpath("nosuchtype")
        with self.assertRaises(ValueError):
            # `all` is an expansion token, not a resolvable class.
            self.model.get_record_subpath("all")

    def test_records_alias_is_reachable_by_name_but_not_as_a_type_noun(self) -> None:
        # THE TWO QUESTIONS ARE DIFFERENT AND THE MODEL KEEPS THEM APART. `records` is a legitimate
        # RECORD CLASS (`RecordClass.RECORDS`, whose callers must keep working) but has never been
        # an `ARTIFACT_TYPES` member, so accepting it as a CLI type noun would silently widen the
        # CLI surface. `resolve_class_name` accepts it; `normalize_type` rejects it.
        self.assertIn("records", self.model.record_classes)
        self.assertNotIn("records", self.model.artifact_types())
        self.assertEqual(self.model.resolve_class_name("records"), "records")
        self.assertEqual(self.model.get_record_class("records").is_root_alias, True)
        with self.assertRaises(ValueError):
            self.model.normalize_type("records")
        self.assertFalse(self.model.is_known_type("records"))
        self.assertEqual(AT.is_type_token("records"), False)

    def test_resolve_class_name_rejects_unknown_and_the_all_token(self) -> None:
        with self.assertRaises(ValueError):
            self.model.resolve_class_name("nosuchtype")
        with self.assertRaises(ValueError) as ctx:
            self.model.resolve_class_name("all")
        self.assertIn("expansion token", str(ctx.exception))


class SerializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = layout.build_default_layout()

    def test_document_has_the_required_top_level_keys(self) -> None:
        doc = self.model.to_dict("1.2.3")
        for key in (
            "schema_version",
            "framework_version",
            "logical_roots",
            "record_classes",
            "state_classes",
            "traversal_exclusions",
        ):
            self.assertIn(key, doc)
        self.assertEqual(doc["schema_version"], 1)
        self.assertEqual(doc["framework_version"], "1.2.3")
        self.assertEqual(set(doc["state_classes"]), {"durable", "runtime"})

    def test_emitted_state_classes_are_state_root_relative(self) -> None:
        doc = self.model.to_dict("1.2.3")
        self.assertEqual(doc["state_classes"]["durable"]["history"], "durable/history")
        self.assertEqual(doc["state_classes"]["runtime"]["locks"], "runtime/locks")

    def test_emitted_record_classes_omit_the_root_alias(self) -> None:
        doc = self.model.to_dict("1.2.3")
        self.assertNotIn(
            "records",
            doc["record_classes"],
            "emitting the records root alias invites a records/records/ path",
        )
        self.assertEqual(len(doc["record_classes"]), 11)

    def test_serialization_is_byte_identical_across_calls(self) -> None:
        # `hauwqh` relies on re-emission being a NO-OP for an unchanged version.
        first = self.model.to_json("1.2.3")
        second = self.model.to_json("1.2.3")
        self.assertEqual(first, second)
        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))
        self.assertEqual(
            layout.build_default_layout().to_json("1.2.3"),
            first,
            "two freshly built models must serialize identically",
        )

    def test_json_key_order_is_stable(self) -> None:
        keys = list(json.loads(self.model.to_json("1.2.3")).keys())
        self.assertEqual(
            keys,
            [
                "schema_version",
                "framework_version",
                "logical_roots",
                "record_classes",
                "state_classes",
                "traversal_exclusions",
            ],
        )
        self.assertTrue(self.model.to_json("1.2.3").endswith("\n"))

    def test_schema_is_stable_and_json_serializable(self) -> None:
        self.assertEqual(self.model.to_schema_json(), self.model.to_schema_json())
        json.loads(self.model.to_schema_json())


class SchemaConformanceTests(unittest.TestCase):
    """Structural conformance checked with the STDLIB (no `jsonschema` dependency)."""

    def setUp(self) -> None:
        self.model = layout.build_default_layout()
        self.schema = self.model.to_schema()
        self.doc = json.loads(self.model.to_json("1.2.3"))

    def test_every_required_top_level_property_is_present(self) -> None:
        for key in self.schema["required"]:
            self.assertIn(key, self.doc)

    def test_no_additional_top_level_properties(self) -> None:
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(set(self.doc), set(self.schema["properties"]))

    def test_schema_version_matches_the_declared_enum(self) -> None:
        self.assertIn(
            self.doc["schema_version"],
            self.schema["properties"]["schema_version"]["enum"],
        )

    def test_logical_roots_satisfy_their_required_keys_and_types(self) -> None:
        required = self.schema["properties"]["logical_roots"]["required"]
        for key in required:
            self.assertIn(key, self.doc["logical_roots"])
        for value in self.doc["logical_roots"].values():
            self.assertIsInstance(value, str)

    def test_each_record_class_entry_satisfies_the_schema(self) -> None:
        entry_schema = self.schema["properties"]["record_classes"][
            "additionalProperties"
        ]
        types = {"string": str, "array": list, "object": dict, "integer": int}
        for name, entry in self.doc["record_classes"].items():
            self.assertIsInstance(entry, dict, name)
            for key in entry_schema["required"]:
                self.assertIn(key, entry, "{0} missing {1}".format(name, key))
            for key, value in entry.items():
                declared = entry_schema["properties"].get(key)
                self.assertIsNotNone(
                    declared, "{0}.{1} is undeclared in the schema".format(name, key)
                )
                self.assertIsInstance(value, types[declared["type"]])
                if declared["type"] == "array":
                    for item in value:
                        self.assertIsInstance(item, str)

    def test_state_classes_satisfy_the_schema(self) -> None:
        state_schema = self.schema["properties"]["state_classes"]
        for key in state_schema["required"]:
            self.assertIn(key, self.doc["state_classes"])
        for group in self.doc["state_classes"].values():
            self.assertIsInstance(group, dict)
            for value in group.values():
                self.assertIsInstance(value, str)

    def test_traversal_exclusions_satisfy_the_schema(self) -> None:
        self.assertIsInstance(self.doc["traversal_exclusions"], list)
        for item in self.doc["traversal_exclusions"]:
            self.assertIsInstance(item, str)


if __name__ == "__main__":
    unittest.main()
