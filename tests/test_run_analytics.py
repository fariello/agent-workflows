"""Tests for normalized run ingestion, the fact schema and the conservation checks (IPD `8hald1`).

Covers E-04 (fact grains and the irreducible four-state provenance), E-05 (the OPEN token component
map and separated wall/activity time), E-06 (conservation as a sum over ALL components), E-07
(deduplication, partial-run semantics and the quality summary) and E-08 (every fact crosses Order
02's privacy projector, proven both ways with the shipped detector).

THREE CONVENTIONS, EACH FOR A RECORDED REASON.

FIRST, FIXTURES ARE AUTHORITATIVE. The live run corpus is gitignored, mutable, grows with every run,
and carries absolute paths the shipped detector flags at `fail`, so no test here reads it. Every
fixture instead REPRODUCES a property measured on the real corpus at review, most importantly the two
attempts carrying a `reasoning` token key whose exact deltas (2658 and 1120) falsified the four-term
conservation equation. That measurement is what this suite exists to keep true.

SECOND, THE REJECTED FORM IS TESTED ALONGSIDE THE IMPLEMENTED ONE. `check_conservation_four_term` is
never called in production, and it is exercised here specifically so its failure is DEMONSTRATED on
the same data rather than asserted from a review note. That is what stops a later reader from
"simplifying" the open form back into the broken one.

THIRD, NO SENSITIVE LITERAL IS COMMITTED. Canaries are assembled from fragments at runtime, as the
shipped detection engine does with its own patterns, and the privacy tests pair every clean scan with
a CONTROL scan proving the same invocation flags the same canary raw. A projector that refused nothing
and a detector that was not looking are otherwise indistinguishable.

Stdlib unittest only.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import leak_sanitizer as ls
from agent_workflows import run_analytics as ingest
from agent_workflows import run_analytics_privacy as privacy
from agent_workflows import run_analytics_schema as schema
from agent_workflows import run_analytics_sources as sources
from agent_workflows.run_analytics_schema import (
    Grain,
    Phase,
    Provenance,
    Usage,
    Value,
    missing,
    not_applicable,
    recorded,
    unavailable,
)

# Assembled at runtime; never committed as a literal.
_HANDLE = "gfa" + "riello"
_ABS_HOME = "/ho" + "me/" + _HANDLE + "/VC/agent-workflows"
_PROMPT_BODY = "You are an agent. " + "Implement E-01 exactly as written."

#: The two real attempts that falsified the four-term equation, reproduced exactly. The `reasoning`
#: value IS the four-term shortfall, which is the whole finding.
_MEASURED_REASONING_DELTAS = (2658, 1120)


def _core_state(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "created_at": "2026-09-08T10:00:00Z",
        "updated_at": "2026-09-08T11:00:00Z",
        "driver": {"path": f"{_ABS_HOME}/agent_workflows/oc_runipd.py"},
        "manifest": f"{_ABS_HOME}/manifest.json",
        "manifest_sha256": "a" * 64,
        "options": {"model": "provider/model"},
        "queue": [],
        "repo": _ABS_HOME,
        "runbook": f"{_ABS_HOME}/runbook.md",
        "runbook_sha256": "b" * 64,
        "run_id": "run-20260908T100000Z-1234",
        "schema_version": 1,
        "selectors": ["demo"],
        "set_sessions": {},
    }
    assert set(payload) == set(sources.CORE_STATE_KEYS)
    payload.update(overrides)
    return payload


def _attempt(
    number: int = 1,
    *,
    tokens: dict[str, int] | None = None,
    cost: float | None = 1.5,
    start: str = "2026-09-08T10:00:00Z",
    end: str | None = "2026-09-08T10:10:00Z",
    recovery: bool = False,
    verify: bool = False,
) -> dict[str, object]:
    attempt: dict[str, object] = {
        "number": number,
        "started_at": start,
        "recovery": recovery,
    }
    if end is not None:
        attempt["ended_at"] = end
    if cost is not None:
        attempt["cost"] = cost
    if tokens is not None:
        attempt["tokens"] = tokens
    if verify:
        attempt["verify_cost"] = 0.25
        attempt["verify_tokens"] = {"input": 20, "output": 5, "total": 25}
    return attempt


def _item(
    id6: str = "abc123",
    *,
    position: int = 1,
    status: str = "executed",
    action: str = "execute",
    attempts: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "id6": id6,
        "setid": "demo",
        "position": position,
        "status": status,
        "action": action,
        "attempts": attempts if attempts is not None else [_attempt()],
    }


def _write_run(
    root: Path,
    run_id: str = "run-20260908T100000Z-1234",
    *,
    items: list[dict[str, object]] | None = None,
    events: list[str] | None = None,
    state_extra: dict[str, object] | None = None,
    with_prompts: bool = True,
) -> Path:
    run = root / run_id
    (run / "outcomes").mkdir(parents=True, exist_ok=True)
    (run / "sessions").mkdir(exist_ok=True)
    extra = dict(state_extra or {})
    state = _core_state(
        run_id=run_id,
        queue=items if items is not None else [_item()],
        **extra,
    )
    (run / "state.json").write_text(json.dumps(state), encoding="utf-8")
    lines = (
        events
        if events is not None
        else ['{"at":"2026-09-08T10:00:00Z","event":"run-created"}']
    )
    (run / "events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (run / "execution-report.md").write_text("# report\n", encoding="utf-8")
    if with_prompts:
        prompts = run / "prompts"
        prompts.mkdir(exist_ok=True)
        # A real prompt file: the content that must NEVER reach a fact.
        (prompts / "01-abc123-attempt-1.md").write_text(
            f"{_PROMPT_BODY}\nRepo: {_ABS_HOME}\n", encoding="utf-8"
        )
    return run


class ProvenanceTests(unittest.TestCase):
    """E-04: the four-state distinction is irreducible, and absence is NEVER zero."""

    def test_the_six_states_partition_into_present_and_absent(self):
        self.assertEqual(
            schema.PRESENT_PROVENANCE | schema.ABSENT_PROVENANCE,
            set(Provenance),
        )
        self.assertEqual(schema.PRESENT_PROVENANCE & schema.ABSENT_PROVENANCE, set())
        self.assertEqual(len(schema.ABSENT_PROVENANCE), 3)

    def test_missing_unavailable_and_not_applicable_are_DISTINCT_from_each_other(self):
        a, b, c = missing(), unavailable(), not_applicable()
        self.assertNotEqual(a.provenance, b.provenance)
        self.assertNotEqual(b.provenance, c.provenance)
        self.assertNotEqual(a.provenance, c.provenance)
        self.assertEqual(
            {v.provenance.value for v in (a, b, c)},
            {"missing", "unavailable", "not-applicable"},
        )

    def test_each_absent_state_is_DISTINCT_FROM_ZERO_and_refuses_to_be_a_number(self):
        """The gate's own rule, made falsifiable: no absent value can be read as zero."""

        zero = recorded(0)
        self.assertTrue(zero.is_present)
        self.assertEqual(zero.as_number(), 0)

        for absent in (missing(), unavailable(), not_applicable()):
            with self.subTest(state=absent.provenance.value):
                self.assertTrue(absent.is_absent)
                self.assertIsNone(absent.number)
                self.assertNotEqual(absent, zero)
                with self.assertRaises(schema.SchemaError) as ctx:
                    absent.as_number()
                self.assertIn("NOT zero", str(ctx.exception))

    def test_or_default_makes_the_caller_STATE_its_fallback(self):
        self.assertEqual(missing().or_default(0), 0)
        self.assertEqual(missing().or_default(-1), -1)
        self.assertEqual(recorded(7).or_default(0), 7)

    def test_a_present_provenance_with_no_number_is_REFUSED(self):
        for provenance in schema.PRESENT_PROVENANCE:
            with self.subTest(provenance=provenance.value):
                with self.assertRaises(schema.SchemaError):
                    Value(None, provenance)

    def test_an_absent_provenance_carrying_a_number_is_REFUSED(self):
        """The inverse guard: `missing` with a value would be a lie in the type itself."""

        for provenance in schema.ABSENT_PROVENANCE:
            with self.subTest(provenance=provenance.value):
                with self.assertRaises(schema.SchemaError) as ctx:
                    Value(0, provenance)
                self.assertIn("NOT zero", str(ctx.exception))

    def test_a_non_finite_or_non_numeric_present_value_is_REFUSED(self):
        for bad in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(bad=bad):
                with self.assertRaises(schema.SchemaError):
                    recorded(bad)
        for bad in (True, "12", None):
            with self.subTest(bad=bad):
                with self.assertRaises(schema.SchemaError):
                    Value(bad, Provenance.RECORDED)  # type: ignore[arg-type]

    def test_MUTATION_coercing_a_missing_value_to_zero_breaks_a_test(self):
        """The mutation check V-04 demands.

        Simulates the exact defect the four-state vocabulary exists to prevent (a later `or 0`) and
        shows an assertion catches it, then confirms the real API still refuses. Without this, a test
        that only reads present values could not distinguish a working guard from an absent one.
        """

        absent = missing("no-cost-recorded")

        def mutated_read(value: Value) -> float | int:
            return value.number or 0  # THE DEFECT: `or 0` erases the distinction

        self.assertEqual(mutated_read(absent), 0, "the mutation silently yields zero")
        with self.assertRaises(schema.SchemaError):
            absent.as_number()

    def test_a_note_must_be_a_short_label_so_it_survives_the_projector(self):
        self.assertEqual(missing("no-cost-recorded").note, "no-cost-recorded")
        for bad in ("free text with spaces", f"path {_ABS_HOME}", "a" * 200):
            with self.subTest(bad=bad[:20]):
                with self.assertRaises(schema.SchemaError):
                    missing(bad)


class UsageComponentMapTests(unittest.TestCase):
    """E-05: the token component map is OPEN, and an unseen key is preserved rather than dropped."""

    def test_the_measured_five_key_vocabulary_round_trips(self):
        """`input`/`output`/`cache`/`total` plus `reasoning`: the keys the corpus actually held.

        Note what is ABSENT and was in the authoring plan: there is no cache-read/cache-write split
        anywhere, so a schema with five named columns for it would model data that does not exist.
        """

        raw = {
            "input": 1000,
            "output": 200,
            "cache": 50,
            "reasoning": 25,
            "total": 1275,
        }
        usage = schema.usage_from_mapping(raw)
        self.assertEqual(set(usage.components), set(raw))
        for name, number in raw.items():
            self.assertEqual(usage.components[name].as_number(), number)
        self.assertEqual(
            usage.component_names, ("cache", "input", "output", "reasoning")
        )
        self.assertEqual(usage.total.as_number(), 1275)

    def test_an_attempt_carrying_reasoning_PRESERVES_it(self):
        """The key the authoring plan omitted. Dropping it is the defect this asserts against."""

        usage = schema.usage_from_mapping(
            {"input": 100, "output": 50, "cache": 10, "reasoning": 5, "total": 165}
        )
        self.assertIn("reasoning", usage.components)
        self.assertEqual(usage.components["reasoning"].as_number(), 5)

    def test_an_INVENTED_component_key_survives_with_NO_code_change(self):
        """Openness proven against a key nobody has seen, which is the point of an open map."""

        usage = schema.usage_from_mapping(
            {"input": 10, "output": 5, "quantum_flux_tokens": 7, "total": 22}
        )
        self.assertIn("quantum_flux_tokens", usage.components)
        self.assertEqual(usage.components["quantum_flux_tokens"].as_number(), 7)
        self.assertIn("quantum_flux_tokens", usage.component_names)
        self.assertTrue(
            schema.check_conservation(usage).holds,
            "an unknown component must participate in the sum AUTOMATICALLY",
        )

    def test_a_nested_cache_read_write_shape_is_flattened_like_the_viewer_does(self):
        usage = schema.usage_from_mapping(
            {"input": 10, "cache": {"read": 4, "write": 6}, "total": 20}
        )
        self.assertEqual(usage.components["cache"].as_number(), 10)
        self.assertEqual(usage.components["cache"].note, "flattened")

    def test_an_unparseable_component_becomes_MISSING_not_zero(self):
        usage = schema.usage_from_mapping({"input": "lots", "total": 5})
        self.assertTrue(usage.components["input"].is_absent)
        self.assertEqual(usage.components["input"].provenance, Provenance.MISSING)

    def test_an_absent_usage_mapping_yields_no_components_and_an_absent_cost(self):
        for empty in (None, {}):
            usage = schema.usage_from_mapping(empty)
            self.assertEqual(usage.components, {})
            self.assertTrue(usage.cost.is_absent)

    def test_the_total_is_NEVER_silently_derived(self):
        """A derived total must be LABELED, so nobody mistakes our sum for the provider's report."""

        usage = schema.usage_from_mapping({"input": 10, "output": 5})
        self.assertTrue(usage.total.is_absent, "no reported total means absent, not 15")
        computed = usage.derived_total()
        self.assertEqual(computed.as_number(), 15)
        self.assertEqual(computed.provenance, Provenance.DERIVED)
        self.assertEqual(computed.note, "sum-of-components")

    def test_a_derived_total_over_NO_present_components_is_absent_not_zero(self):
        usage = Usage(components={"input": missing()})
        self.assertTrue(usage.derived_total().is_absent)

    def test_component_numbers_OMITS_absent_components_rather_than_zero_filling(self):
        usage = Usage(
            components={
                "input": recorded(10),
                "output": missing(),
                "total": recorded(10),
            }
        )
        self.assertEqual(usage.component_numbers(), {"input": 10, "total": 10})

    def test_merging_usage_preserves_unknown_keys_and_absence(self):
        merged = schema.merge_usage(
            [
                schema.usage_from_mapping(
                    {"input": 10, "novel": 1, "total": 11}, cost=recorded(1.0)
                ),
                schema.usage_from_mapping({"input": 5, "total": 5}, cost=recorded(0.5)),
                Usage(components={"absent_everywhere": unavailable("old-driver")}),
            ]
        )
        self.assertEqual(merged.components["input"].as_number(), 15)
        self.assertEqual(merged.components["novel"].as_number(), 1)
        self.assertEqual(merged.components["total"].as_number(), 16)
        self.assertTrue(merged.components["absent_everywhere"].is_absent)
        self.assertEqual(
            merged.components["absent_everywhere"].provenance, Provenance.UNAVAILABLE
        )
        self.assertEqual(merged.cost.as_number(), 1.5)
        self.assertEqual(merged.cost.provenance, Provenance.DERIVED, "a sum is derived")

    def test_a_component_name_that_is_not_a_safe_label_is_REFUSED(self):
        """A provider-chosen NAME is attacker-shaped input, so the name is checked, not just the value.

        Includes the EMBEDDED-path case (`tokens<abs-home-path>`), which is the one the sibling
        projector's own path test misses: it only catches a LEADING `/`, `~`, `..` or a drive letter,
        so a path after a harmless prefix satisfies both its label pattern and its path check. That
        is why the schema's component-name pattern forbids `/` outright.
        """

        for bad in (
            f"tokens{_ABS_HOME}",
            "has spaces",
            "../escape",
            "/leading",
            "a/b",
            f"x{_HANDLE}/y",
        ):
            with self.subTest(bad=bad[:24]):
                with self.assertRaises(schema.SchemaError) as ctx:
                    Usage(components={bad: recorded(1)})
                self.assertIn("component label", str(ctx.exception))

    def test_an_unsafe_component_name_from_a_provider_is_DROPPED_not_raised(self):
        """Containment: one hostile key must degrade its own run, never abort the sweep.

        And the DROP must not enter the conservation sum, or a defensive measure would report itself
        as a conservation violation.
        """

        usage = schema.usage_from_mapping(
            {"input": 10, f"evil{_ABS_HOME}": 999, "total": 10}
        )
        self.assertEqual(set(usage.components), {"input", "total"})
        self.assertEqual(usage.dropped_component_count, 1)
        self.assertTrue(
            schema.check_conservation(usage).holds,
            "the dropped count must NOT participate in the sum",
        )
        serialized = json.dumps(usage.to_dict())
        self.assertNotIn(_ABS_HOME, serialized)
        self.assertNotIn(_HANDLE, serialized)

    def test_the_dropped_count_surfaces_as_a_CODE_in_the_quality_summary(self):
        fact = schema.Fact(
            grain=Grain.ATTEMPT,
            run_id="run-1",
            usage=schema.usage_from_mapping(
                {"input": 1, f"evil{_ABS_HOME}": 2, "total": 1}
            ),
        )
        quality = schema.summarize_quality("run-1", [fact])
        self.assertIn("unsafe-component-name-dropped", quality.warnings)
        for warning in quality.warnings:
            self.assertNotIn(_HANDLE, warning)
            self.assertNotIn("/", warning)

    def test_the_dropped_count_survives_a_merge(self):
        merged = schema.merge_usage(
            [
                schema.usage_from_mapping({"input": 1, "bad/name": 2, "total": 1}),
                schema.usage_from_mapping({"input": 1, "total": 1}),
            ]
        )
        self.assertEqual(merged.dropped_component_count, 1)


class ConservationTests(unittest.TestCase):
    """E-06: THE most important correction. Conservation is a sum over ALL components."""

    def _measured_attempt(self, reasoning: int) -> Usage:
        """An attempt reproducing a real one: the four-term shortfall EQUALS `reasoning` exactly."""

        input_, output, cache = 100000, 5000, 2000
        total = input_ + output + cache + reasoning
        return schema.usage_from_mapping(
            {
                "input": input_,
                "output": output,
                "cache": cache,
                "reasoning": reasoning,
                "total": total,
            }
        )

    def test_the_all_components_form_HOLDS_on_the_two_measured_reasoning_attempts(self):
        for delta in _MEASURED_REASONING_DELTAS:
            with self.subTest(reasoning=delta):
                result = schema.check_conservation(self._measured_attempt(delta))
                self.assertTrue(result.holds, result.to_dict())
                self.assertEqual(result.delta, 0)
                self.assertEqual(result.reason, "all-components-sum")
                self.assertIn("reasoning", result.components)

    def test_the_four_term_form_FAILS_on_them_by_EXACTLY_the_reasoning_value(self):
        """The measured falsification, reproduced: deltas 2658 and 1120, equal to `reasoning`.

        This is why the authored equation would have fired a FALSE violation on real runs, and why
        the natural repair (loosen the assertion) had to be forestalled.
        """

        for delta in _MEASURED_REASONING_DELTAS:
            with self.subTest(reasoning=delta):
                usage = self._measured_attempt(delta)
                four = schema.check_conservation_four_term(usage)
                self.assertFalse(four.holds, "the REJECTED form must fail here")
                self.assertEqual(
                    four.delta,
                    delta,
                    "the shortfall equals `reasoning` exactly, which identifies the cause",
                )
                self.assertTrue(
                    schema.check_conservation(usage).holds,
                    "and the implemented form must hold on the same data",
                )

    def test_both_forms_AGREE_when_no_reasoning_key_is_present(self):
        """174 of 176 real attempts: the forms are indistinguishable, which is why this was missed."""

        usage = schema.usage_from_mapping(
            {"input": 100, "output": 50, "cache": 10, "total": 160}
        )
        self.assertTrue(schema.check_conservation(usage).holds)
        self.assertTrue(schema.check_conservation_four_term(usage).holds)

    def test_a_GENUINE_mismatch_still_FAILS_so_the_check_can_fire(self):
        """A check that cannot fail detects nothing. This proves it still can."""

        usage = schema.usage_from_mapping(
            {"input": 100, "output": 50, "cache": 10, "total": 999}
        )
        result = schema.check_conservation(usage)
        self.assertFalse(result.holds)
        self.assertEqual(result.expected, 160)
        self.assertEqual(result.actual, 999)
        self.assertEqual(result.delta, 839)
        self.assertEqual(result.reason, "conservation-violation")

    def test_tolerance_defaults_to_ZERO_because_a_tolerant_check_detects_nothing(self):
        usage = schema.usage_from_mapping({"input": 100, "output": 50, "total": 151})
        self.assertFalse(schema.check_conservation(usage).holds)
        self.assertTrue(
            schema.check_conservation(usage, tolerance=1).holds,
            "a tolerance is a caller's EXPLICIT choice, never a default",
        )

    def test_an_absent_total_is_unreconcilable_rather_than_a_violation(self):
        usage = schema.usage_from_mapping({"input": 10, "output": 5})
        result = schema.check_conservation(usage)
        self.assertTrue(result.holds)
        self.assertEqual(result.reason, "no-total-reported")

    def test_a_PARTIALLY_observed_component_set_is_unreconcilable_not_a_violation(self):
        """Calling this a violation would train a reader to ignore violations."""

        usage = Usage(
            components={
                "input": recorded(100),
                "output": missing("unparseable"),
                "total": recorded(160),
            }
        )
        result = schema.check_conservation(usage)
        self.assertTrue(result.holds)
        self.assertEqual(result.reason, "components-incomplete")

    def test_a_total_with_no_components_at_all_is_unreconcilable(self):
        usage = Usage(components={"total": recorded(100)})
        result = schema.check_conservation(usage)
        self.assertTrue(result.holds)
        self.assertEqual(result.reason, "no-components-reported")

    def test_the_result_carries_the_numbers_that_produced_it(self):
        result = schema.check_conservation(
            schema.usage_from_mapping({"input": 3, "output": 4, "total": 7})
        )
        self.assertEqual(
            result.to_dict(),
            {
                "holds": True,
                "expected": 7,
                "actual": 7,
                "delta": 0,
                "components": ["input", "output"],
                "reason": "all-components-sum",
            },
        )


class TimeAccountingTests(unittest.TestCase):
    """E-05: wall time and activity time are separate, and overlap is visible not smoothed."""

    def test_OVERLAPPING_activities_are_NOT_forced_to_sum_to_elapsed_time(self):
        """Two 600s activities overlapping by 300s inside a 1200s window."""

        accounting = schema.account_intervals(
            [(0.0, 600.0), (300.0, 900.0)], wall_start=0.0, wall_end=1200.0
        )
        self.assertEqual(accounting.wall_seconds.as_number(), 1200.0)
        self.assertEqual(
            accounting.observed_activity_seconds.as_number(),
            900.0,
            "the UNION, each wall second counted once",
        )
        self.assertEqual(
            accounting.overlap_seconds.as_number(),
            300.0,
            "the double counting, made VISIBLE",
        )
        self.assertEqual(
            accounting.unattributed_seconds.as_number(),
            300.0,
            "wall time no interval covers",
        )
        self.assertNotEqual(
            accounting.observed_activity_seconds.as_number(),
            accounting.wall_seconds.as_number(),
            "activity is NOT normalized onto elapsed time",
        )

    def test_non_overlapping_activities_report_zero_overlap(self):
        accounting = schema.account_intervals(
            [(0.0, 100.0), (200.0, 300.0)], wall_start=0.0, wall_end=400.0
        )
        self.assertEqual(accounting.observed_activity_seconds.as_number(), 200.0)
        self.assertEqual(accounting.overlap_seconds.as_number(), 0.0)
        self.assertEqual(accounting.unattributed_seconds.as_number(), 200.0)

    def test_fully_nested_intervals_count_the_inner_one_entirely_as_overlap(self):
        accounting = schema.account_intervals(
            [(0.0, 100.0), (25.0, 75.0)], wall_start=0.0, wall_end=100.0
        )
        self.assertEqual(accounting.observed_activity_seconds.as_number(), 100.0)
        self.assertEqual(accounting.overlap_seconds.as_number(), 50.0)
        self.assertEqual(accounting.unattributed_seconds.as_number(), 0.0)

    def test_a_negative_unattributed_value_is_REPORTED_not_floored(self):
        """Activity exceeding the wall window is real evidence of a defect; flooring erases it."""

        accounting = schema.account_intervals(
            [(0.0, 500.0)], wall_start=0.0, wall_end=100.0
        )
        self.assertEqual(accounting.unattributed_seconds.as_number(), -400.0)

    def test_no_intervals_with_a_wall_window_attributes_everything_as_unknown(self):
        accounting = schema.account_intervals([], wall_start=0.0, wall_end=60.0)
        self.assertEqual(accounting.wall_seconds.as_number(), 60.0)
        self.assertEqual(accounting.observed_activity_seconds.as_number(), 0.0)
        self.assertEqual(accounting.unattributed_seconds.as_number(), 60.0)

    def test_no_intervals_and_no_window_is_ABSENT_everywhere_not_zero(self):
        accounting = schema.account_intervals([])
        for value in (
            accounting.wall_seconds,
            accounting.observed_activity_seconds,
            accounting.overlap_seconds,
            accounting.unattributed_seconds,
        ):
            self.assertTrue(value.is_absent)

    def test_intervals_without_a_wall_window_mark_unattributed_UNAVAILABLE(self):
        accounting = schema.account_intervals([(0.0, 10.0)])
        self.assertEqual(accounting.observed_activity_seconds.as_number(), 10.0)
        self.assertEqual(
            accounting.unattributed_seconds.provenance, Provenance.UNAVAILABLE
        )


class FactTableTests(unittest.TestCase):
    """E-04/E-05: every grain is produced and round-trips, with phases kept separate."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_every_grain_is_produced_and_round_trips(self):
        run = _write_run(
            self.root,
            items=[
                _item(
                    attempts=[
                        _attempt(
                            tokens={
                                "input": 100,
                                "output": 50,
                                "cache": 10,
                                "total": 160,
                            },
                            verify=True,
                        )
                    ]
                )
            ],
        )
        facts = ingest.build_run_facts(run)
        produced = {f.grain for f in facts.facts}
        self.assertEqual(
            produced, {Grain.RUN, Grain.IPD, Grain.ATTEMPT, Grain.PHASE, Grain.EVENT}
        )
        for fact in facts.facts:
            with self.subTest(grain=fact.grain.value):
                payload = fact.to_dict()
                self.assertEqual(payload["schema_version"], schema.FACT_SCHEMA_VERSION)
                self.assertEqual(payload["grain"], fact.grain.value)
                self.assertEqual(json.loads(json.dumps(payload)), payload)

    def test_execute_and_verify_phases_are_SEPARATELY_visible(self):
        run = _write_run(
            self.root,
            items=[
                _item(
                    attempts=[
                        _attempt(
                            tokens={"input": 100, "output": 50, "total": 150},
                            verify=True,
                        )
                    ]
                )
            ],
        )
        facts = ingest.build_run_facts(run)
        phases = {f.phase: f for f in facts.by_grain(Grain.PHASE)}
        self.assertIn(Phase.EXECUTE, phases)
        self.assertIn(Phase.VERIFY, phases)
        self.assertEqual(phases[Phase.EXECUTE].usage.cost.as_number(), 1.5)
        self.assertEqual(phases[Phase.VERIFY].usage.cost.as_number(), 0.25)

    def test_a_verify_phase_that_never_ran_is_NOT_APPLICABLE_not_missing_and_not_zero(
        self,
    ):
        """The distinction that makes the four-state vocabulary load-bearing in real data."""

        run = _write_run(
            self.root,
            items=[_item(attempts=[_attempt(tokens={"input": 10, "total": 10})])],
        )
        facts = ingest.build_run_facts(run)
        verify = next(f for f in facts.by_grain(Grain.PHASE) if f.phase is Phase.VERIFY)
        self.assertEqual(verify.usage.cost.provenance, Provenance.NOT_APPLICABLE)
        self.assertTrue(verify.usage.cost.is_absent)
        with self.assertRaises(schema.SchemaError):
            verify.usage.cost.as_number()

    def test_a_review_action_is_labeled_the_REVIEW_phase(self):
        run = _write_run(self.root, items=[_item(action="review", status="reviewed")])
        facts = ingest.build_run_facts(run)
        self.assertEqual(
            {f.phase for f in facts.by_grain(Grain.ATTEMPT)}, {Phase.REVIEW}
        )

    def test_a_recovery_attempt_is_labeled_the_RECOVERY_phase(self):
        run = _write_run(
            self.root,
            items=[
                _item(
                    attempts=[
                        _attempt(1),
                        _attempt(
                            2,
                            recovery=True,
                            start="2026-09-08T10:20:00Z",
                            end="2026-09-08T10:30:00Z",
                        ),
                    ]
                )
            ],
        )
        facts = ingest.build_run_facts(run)
        by_attempt = {f.attempt: f for f in facts.by_grain(Grain.ATTEMPT)}
        self.assertEqual(by_attempt[1].phase, Phase.EXECUTE)
        self.assertEqual(by_attempt[2].phase, Phase.RECOVERY)
        self.assertIn("recovery-attempt", by_attempt[2].quality_flags)

    def test_the_driver_generation_reaches_a_fact_as_a_LABEL_never_a_path(self):
        run = _write_run(self.root)
        for fact in ingest.build_run_facts(run).facts:
            with self.subTest(grain=fact.grain.value):
                self.assertEqual(fact.driver_generation, "oc_runipd")
                self.assertNotIn("/", fact.driver_generation)
                serialized = json.dumps(fact.to_dict())
                self.assertNotIn(_HANDLE, serialized)
                self.assertNotIn(_ABS_HOME, serialized)

    def test_an_unclosed_attempt_reports_MISSING_time_rather_than_inventing_an_end(
        self,
    ):
        run = _write_run(self.root, items=[_item(attempts=[_attempt(end=None)])])
        attempt = ingest.build_run_facts(run).by_grain(Grain.ATTEMPT)[0]
        self.assertTrue(attempt.time.wall_seconds.is_absent)
        self.assertEqual(attempt.time.wall_seconds.note, "attempt-not-closed")

    def test_an_unreadable_run_yields_NO_facts_and_says_so(self):
        broken = self.root / "run-20260908T100000Z-1002"
        broken.mkdir()
        (broken / "state.json").write_text("{ truncated", encoding="utf-8")
        facts = ingest.build_run_facts(broken)
        self.assertEqual(facts.facts, ())
        self.assertFalse(facts.quality.is_complete)
        self.assertIn("state-unreadable", facts.quality.warnings)

    def test_a_run_grain_conservation_flag_appears_when_an_attempt_violates(self):
        run = _write_run(
            self.root,
            items=[
                _item(
                    attempts=[
                        _attempt(tokens={"input": 100, "output": 50, "total": 999})
                    ]
                )
            ],
        )
        facts = ingest.build_run_facts(run)
        self.assertFalse(facts.conservation_holds)
        attempt = facts.by_grain(Grain.ATTEMPT)[0]
        self.assertIn("conservation-violation", attempt.quality_flags)
        run_fact = facts.by_grain(Grain.RUN)[0]
        self.assertIn("conservation-violation", run_fact.quality_flags)
        self.assertEqual(
            attempt.usage.components["total"].as_number(),
            999,
            "the RAW components are kept so a human can investigate the data",
        )


class DeduplicationAndPartialRunTests(unittest.TestCase):
    """E-07: a resumed or damaged run degrades only ITSELF, and nothing is double counted."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_a_MULTI_ATTEMPT_item_is_not_double_counted(self):
        run = _write_run(
            self.root,
            items=[
                _item(
                    attempts=[
                        _attempt(1, tokens={"input": 100, "total": 100}, cost=1.0),
                        _attempt(
                            2,
                            tokens={"input": 200, "total": 200},
                            cost=2.0,
                            start="2026-09-08T10:20:00Z",
                            end="2026-09-08T10:30:00Z",
                        ),
                    ]
                )
            ],
        )
        facts = ingest.build_run_facts(run)
        attempts = facts.by_grain(Grain.ATTEMPT)
        self.assertEqual(len(attempts), 2, "one fact per attempt, not per source")
        self.assertEqual({a.attempt for a in attempts}, {1, 2})
        ipd = facts.by_grain(Grain.IPD)[0]
        self.assertEqual(
            ipd.usage.components["total"].as_number(),
            300,
            "the item total is the sum of its attempts, counted ONCE",
        )
        self.assertEqual(ipd.usage.cost.as_number(), 3.0)

    def test_a_RESUMED_run_reusing_its_directory_is_not_double_counted(self):
        """Ingesting the same terminal run twice must yield identical numbers, never doubled."""

        run = _write_run(
            self.root,
            items=[_item(attempts=[_attempt(tokens={"input": 100, "total": 100})])],
        )
        first = ingest.build_run_facts(run)
        second = ingest.build_run_facts(run)
        self.assertEqual(len(first.facts), len(second.facts))
        self.assertEqual(
            [f.to_dict() for f in first.facts], [f.to_dict() for f in second.facts]
        )

    def test_identity_keeps_a_genuine_second_attempt_and_a_verify_measurement_apart(
        self,
    ):
        def fact(attempt: int, phase: Phase) -> schema.Fact:
            return schema.Fact(
                grain=Grain.ATTEMPT,
                run_id="run-1",
                ipd_id6="abc123",
                position=1,
                attempt=attempt,
                phase=phase,
                source="state",
            )

        a1 = fact(1, Phase.EXECUTE)
        a2 = fact(2, Phase.EXECUTE)
        v1 = fact(1, Phase.VERIFY)
        dup = fact(1, Phase.EXECUTE)

        kept, dropped = schema.deduplicate([a1, a2, v1, dup])
        self.assertEqual(len(kept), 3, "only the true re-observation is dropped")
        self.assertEqual(dropped, ["duplicate-attempt"])

    def test_a_CORRUPTED_event_line_is_skipped_with_a_warning_and_the_run_still_produces_facts(
        self,
    ):
        """No real-data exemplar exists (all 1428 corpus event lines parsed), so this is fixture-driven."""

        run = _write_run(
            self.root,
            events=[
                '{"at":"2026-09-08T10:00:00Z","event":"run-created"}',
                "{ THIS LINE IS DELIBERATELY CORRUPT",
                '{"at":"2026-09-08T10:00:01Z","event":"ipd-started"}',
            ],
        )
        facts = ingest.build_run_facts(run)
        self.assertEqual(facts.quality.parse_error_count, 1)
        self.assertIn("event-line-unparseable", facts.quality.warnings)
        self.assertEqual(
            len(facts.by_grain(Grain.EVENT)), 2, "the two good lines still yield facts"
        )
        self.assertTrue(facts.by_grain(Grain.RUN), "the run grain is still produced")
        self.assertFalse(facts.quality.is_complete)
        self.assertIn("partial-events", facts.by_grain(Grain.RUN)[0].quality_flags)

    def test_one_damaged_run_does_NOT_affect_another(self):
        good = _write_run(self.root, "run-20260908T100000Z-1001")
        broken = self.root / "run-20260908T100000Z-1002"
        broken.mkdir()
        (broken / "state.json").write_text("{ truncated", encoding="utf-8")

        results, warnings = ingest.ingest_corpus([good, broken])
        self.assertEqual(warnings, [], "a damaged run is contained, not an exception")
        self.assertEqual(len(results), 2)
        by_complete = {r.quality.is_complete for r in results}
        self.assertEqual(by_complete, {True, False})
        healthy = next(r for r in results if r.quality.is_complete)
        self.assertTrue(healthy.facts)
        self.assertEqual(healthy.quality.parse_error_count, 0)

    def test_the_quality_summary_distinguishes_missing_unavailable_and_not_applicable(
        self,
    ):
        run = _write_run(
            self.root,
            items=[
                _item(attempts=[_attempt(tokens={"input": 10, "total": 10}, cost=None)])
            ],
        )
        facts = ingest.build_run_facts(run)
        quality = facts.quality
        self.assertIn("cost", quality.missing_fields)
        self.assertIn("cost", quality.not_applicable_fields)
        self.assertEqual(quality.to_dict()["run_id"], "run-20260908T100000Z-1234")
        # THREE separate buckets, never one "incomplete" flag.
        self.assertEqual(
            set(quality.to_dict())
            & {"missing_fields", "unavailable_fields", "not_applicable_fields"},
            {"missing_fields", "unavailable_fields", "not_applicable_fields"},
        )

    def test_summarize_quality_buckets_each_absent_state_separately(self):
        fact = schema.Fact(
            grain=Grain.ATTEMPT,
            run_id="run-1",
            usage=Usage(
                components={
                    "input": missing("m"),
                    "output": unavailable("u"),
                    "cache": not_applicable("na"),
                },
                cost=unavailable("old-driver"),
            ),
        )
        quality = schema.summarize_quality("run-1", [fact])
        # Each absent value lands in the bucket of ITS OWN provenance and in no other. Asserted as
        # membership plus mutual exclusion rather than as tuple equality, because this fact also has
        # a default TimeAccounting whose four values are legitimately `missing`; demanding an exact
        # tuple would encode that incidental detail into the assertion.
        self.assertIn("tokens.input", quality.missing_fields)
        self.assertIn("tokens.output", quality.unavailable_fields)
        self.assertIn("cost", quality.unavailable_fields)
        self.assertIn("tokens.cache", quality.not_applicable_fields)

        buckets = {
            "missing": set(quality.missing_fields),
            "unavailable": set(quality.unavailable_fields),
            "not-applicable": set(quality.not_applicable_fields),
        }
        for name, expected in (
            ("tokens.input", "missing"),
            ("tokens.output", "unavailable"),
            ("cost", "unavailable"),
            ("tokens.cache", "not-applicable"),
        ):
            with self.subTest(field=name):
                for bucket, members in buckets.items():
                    if bucket == expected:
                        self.assertIn(name, members)
                    else:
                        self.assertNotIn(name, members, f"{name} leaked into {bucket}")

    def test_a_warning_is_a_CODE_never_a_formatted_message(self):
        run = _write_run(
            self.root, events=['{"at":"2026-09-08T10:00:00Z","event":"x"}', "{ bad"]
        )
        for warning in ingest.build_run_facts(run).quality.warnings:
            with self.subTest(warning=warning):
                self.assertNotIn("/", warning)
                self.assertNotIn(" ", warning)
                self.assertNotIn(_HANDLE, warning)


class AdvertisedMetricProductionTests(unittest.TestCase):
    """metgap `6krsym`: a metric the query grammar OFFERS must be one a producer actually emits.

    THE DEFECT THESE PIN. `duration_seconds` and `event_count` were both advertised by
    `run_analytics_query.AGGREGATE_METRICS` and both permitted by Order 02's privacy allowlist, while
    `_metric_payload` emitted NEITHER, so each returned `sample_size: 0` for every run ever cached.
    `duration_seconds` was REMOVED (it would duplicate `wall_seconds`, and `TimeAccounting` refuses a
    single reconciled duration on purpose) and `event_count` is now COMPUTED.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _run_payload(self, run: Path) -> dict:
        projected = ingest.project_run_facts(ingest.build_run_facts(run))
        return projected["run"][0]

    def test_every_offered_metric_is_emitted_by_the_producer_for_a_healthy_run(self):
        """THE STANDING GUARD: advertising a metric no producer writes is the defect itself.

        Written as a loop over the live tuple rather than as a hardcoded list, so adding a metric to
        `AGGREGATE_METRICS` without teaching a producer to emit it fails HERE rather than shipping as
        a silent `sample_size: 0`.
        """

        from agent_workflows import run_analytics_query as query_mod

        run = _write_run(
            self.root,
            items=[
                _item(
                    attempts=[_attempt(tokens={"input": 10, "output": 5, "total": 15})]
                )
            ],
        )
        payload = self._run_payload(run)
        # `tokens` is an open component MAP and `token_total` its provider-reported scalar; a query
        # for `tokens` falls back to `token_total`, so either key satisfies that metric.
        satisfied = set(payload) | ({"tokens"} if "token_total" in payload else set())
        for metric in query_mod.AGGREGATE_METRICS:
            with self.subTest(metric=metric):
                self.assertIn(
                    metric,
                    satisfied,
                    f"{metric} is offered by the query grammar but no producer emits it, so it "
                    "returns sample_size 0 for every run",
                )

    def test_event_count_is_the_number_of_event_facts_the_same_table_holds(self):
        run = _write_run(
            self.root,
            events=[
                '{"at":"2026-09-08T10:00:00Z","event":"run-created"}',
                '{"at":"2026-09-08T10:00:01Z","event":"ipd-started"}',
                '{"at":"2026-09-08T10:00:02Z","event":"ipd-finished"}',
            ],
        )
        facts = ingest.build_run_facts(run)
        payload = self._run_payload(run)
        self.assertEqual(payload["event_count"], 3)
        self.assertEqual(payload["event_count"], len(facts.by_grain(Grain.EVENT)))

    def test_an_unparseable_line_is_NOT_counted_as_an_event(self):
        """The count must agree with the fact table, which excludes a line it could not parse."""

        run = _write_run(
            self.root,
            events=[
                '{"at":"2026-09-08T10:00:00Z","event":"run-created"}',
                "{ THIS LINE IS DELIBERATELY CORRUPT",
            ],
        )
        payload = self._run_payload(run)
        self.assertEqual(payload["event_count"], 1)
        self.assertIn("partial-events", payload["quality_flags"])

    def test_an_events_file_that_EXISTS_and_is_empty_counts_a_real_zero(self):
        run = _write_run(self.root, events=[])
        (run / "events.jsonl").write_text("", encoding="utf-8")
        payload = self._run_payload(run)
        self.assertEqual(
            payload["event_count"],
            0,
            "a file that exists and holds no line is a MEASURED zero, not an absence",
        )

    def test_a_run_with_NO_events_file_OMITS_the_key_rather_than_reporting_zero(self):
        """OMIT, NEVER ZERO-FILL. A zero here would assert a count nobody observed."""

        run = _write_run(self.root)
        (run / "events.jsonl").unlink()
        payload = self._run_payload(run)
        self.assertNotIn("event_count", payload)

    def test_event_count_is_a_RUN_grain_key_and_appears_at_no_other_grain(self):
        run = _write_run(self.root)
        projected = ingest.project_run_facts(ingest.build_run_facts(run))
        self.assertIn("event_count", projected["run"][0])
        for grain in ("ipd", "attempt", "phase"):
            for record in projected.get(grain, []):
                with self.subTest(grain=grain):
                    self.assertNotIn(
                        "event_count",
                        record,
                        "a per-item fact has no event stream of its own to count",
                    )

    def test_duration_seconds_is_NOT_offered_and_is_still_NOT_produced(self):
        """The removal branch, asserted on BOTH halves so a half-state cannot pass.

        Re-adding the name to the grammar without a producer would restore the exact defect, and
        emitting it without offering it would persist a key nothing can query.
        """

        from agent_workflows import run_analytics_query as query_mod

        self.assertNotIn("duration_seconds", query_mod.AGGREGATE_METRICS)
        run = _write_run(self.root)
        self.assertNotIn("duration_seconds", self._run_payload(run))


class TokenAbsenceClassificationTests(unittest.TestCase):
    """metgap `6krsym` E-06: the ingester records WHY a token total is absent, or says nothing.

    Measured over this repository's corpus at authoring time: all 32 token absences across both hosts
    were runs where no agent turn was ever dispatched, and the decisive check (a completed item, a
    non-empty session, no tokens) returned ZERO runs. So the folded `missing` count was reporting
    correctly-empty runs as lost data.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _flags(self, **kwargs) -> set[str]:
        run = _write_run(self.root, **kwargs)
        facts = ingest.build_run_facts(run)
        return set(facts.by_grain(Grain.RUN)[0].quality_flags)

    def test_a_run_WITH_tokens_carries_no_absence_flag_at_all(self):
        flags = self._flags(
            items=[_item(attempts=[_attempt(tokens={"input": 10, "total": 10})])]
        )
        self.assertNotIn(ingest.TOKENS_NOTHING_TO_RECORD_FLAG, flags)
        self.assertNotIn(ingest.TOKENS_RUN_UNFINISHED_FLAG, flags)

    def test_an_item_that_dispatched_NO_attempt_is_nothing_to_record(self):
        flags = self._flags(items=[_item(status="not-attempted", attempts=[])])
        self.assertIn(ingest.TOKENS_NOTHING_TO_RECORD_FLAG, flags)

    def test_an_ORCHESTRATE_only_item_is_nothing_to_record(self):
        """An orchestrator is retired from its children's state and spends no agent turn."""

        flags = self._flags(items=[_item(action="orchestrate", attempts=[])])
        self.assertIn(ingest.TOKENS_NOTHING_TO_RECORD_FLAG, flags)

    def test_an_EMPTY_queue_is_nothing_to_record(self):
        flags = self._flags(items=[])
        self.assertIn(ingest.TOKENS_NOTHING_TO_RECORD_FLAG, flags)

    def test_a_RUNNING_item_is_unfinished_rather_than_nothing_to_record(self):
        """A third state. Collapsing it either way would assert something the run has not settled."""

        flags = self._flags(items=[_item(status="running", attempts=[])])
        self.assertIn(ingest.TOKENS_RUN_UNFINISHED_FLAG, flags)
        self.assertNotIn(ingest.TOKENS_NOTHING_TO_RECORD_FLAG, flags)

    def test_A_GENUINE_LOSS_IS_NEVER_EXPLAINED_AWAY(self):
        """THE LOAD-BEARING ASSERTION of this plan: a dispatched turn with no tokens stays UNEXPLAINED.

        This is the case the new vocabulary must not absorb. An attempt ran, finished, and recorded no
        token total; that is either a producer defect or real data loss, and it must keep reading as
        one.
        """

        flags = self._flags(items=[_item(attempts=[_attempt(tokens=None, cost=2.0)])])
        self.assertNotIn(ingest.TOKENS_NOTHING_TO_RECORD_FLAG, flags)
        self.assertNotIn(ingest.TOKENS_RUN_UNFINISHED_FLAG, flags)

    def test_a_MIXED_queue_with_one_real_execution_is_not_explained_away(self):
        """One genuinely executed item with no tokens outweighs any number of empty ones."""

        flags = self._flags(
            items=[
                _item("aaa111", position=1, status="not-attempted", attempts=[]),
                _item("bbb222", position=2, attempts=[_attempt(tokens=None, cost=1.0)]),
            ]
        )
        self.assertNotIn(ingest.TOKENS_NOTHING_TO_RECORD_FLAG, flags)

    def test_the_flags_are_short_LABELS_that_survive_the_privacy_projector(self):
        run = _write_run(self.root, items=[_item(status="not-attempted", attempts=[])])
        payload = ingest.project_run_facts(ingest.build_run_facts(run))["run"][0]
        self.assertIn(ingest.TOKENS_NOTHING_TO_RECORD_FLAG, payload["quality_flags"])


class ConservationSurveyTests(unittest.TestCase):
    """E-06: the both-forms survey, which makes the measurement reproducible rather than cited."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_the_survey_reproduces_the_measured_divergence_between_the_two_forms(self):
        """A corpus shaped like the real one: most attempts agree, the `reasoning` ones do not."""

        plain = [
            _item(
                f"plain{i:02d}",
                position=i,
                attempts=[
                    _attempt(
                        tokens={"input": 100, "output": 50, "cache": 10, "total": 160}
                    )
                ],
            )
            for i in range(1, 5)
        ]
        reasoning = [
            _item(
                f"reason{i:02d}",
                position=10 + i,
                attempts=[
                    _attempt(
                        tokens={
                            "input": 100000,
                            "output": 5000,
                            "cache": 2000,
                            "reasoning": delta,
                            "total": 107000 + delta,
                        }
                    )
                ],
            )
            for i, delta in enumerate(_MEASURED_REASONING_DELTAS, 1)
        ]
        run = _write_run(self.root, items=plain + reasoning)

        survey = ingest.conservation_survey([run])
        self.assertEqual(survey["attempts_checked"], 6)
        self.assertEqual(
            survey["all_components"]["held"], 6, "the implemented form holds on ALL"
        )
        self.assertEqual(survey["all_components"]["failed"], 0)
        self.assertEqual(
            survey["four_term"]["held"],
            4,
            "the REJECTED form holds only on the plain ones",
        )
        self.assertEqual(survey["four_term"]["failed"], 2)
        self.assertEqual(
            sorted(f["delta"] for f in survey["four_term"]["failures"]),
            sorted(_MEASURED_REASONING_DELTAS),
            "and its deltas equal the `reasoning` values exactly",
        )
        for failure in survey["four_term"]["failures"]:
            self.assertEqual(failure["delta"], failure["reasoning"])

    def test_the_survey_names_each_failure_so_it_is_auditable(self):
        run = _write_run(
            self.root,
            items=[
                _item(
                    "bad001",
                    attempts=[_attempt(tokens={"input": 1, "output": 1, "total": 99})],
                )
            ],
        )
        survey = ingest.conservation_survey([run])
        failure = survey["all_components"]["failures"][0]
        self.assertEqual(failure["ipd_id6"], "bad001")
        self.assertEqual(failure["attempt"], 1)
        self.assertEqual(failure["delta"], 97)

    def test_a_damaged_run_does_not_end_the_survey(self):
        good = _write_run(
            self.root,
            "run-20260908T100000Z-1001",
            items=[
                _item(
                    attempts=[_attempt(tokens={"input": 10, "output": 5, "total": 15})]
                )
            ],
        )
        broken = self.root / "run-20260908T100000Z-1002"
        broken.mkdir()
        (broken / "state.json").write_text("{ nope", encoding="utf-8")
        survey = ingest.conservation_survey([good, broken])
        self.assertEqual(
            survey["attempts_checked"], 1, "the healthy run's attempt is still surveyed"
        )
        self.assertEqual(survey["all_components"]["held"], 1)

    def test_an_attempt_with_NO_reported_total_is_not_counted_as_checked(self):
        """Only an attempt carrying a provider total can be reconciled, so only those are counted."""

        run = _write_run(
            self.root,
            items=[_item(attempts=[_attempt(tokens=None)])],
        )
        self.assertEqual(ingest.conservation_survey([run])["attempts_checked"], 0)


class PrivacyBoundaryTests(unittest.TestCase):
    """E-08: every fact crosses Order 02's projector, proven BOTH ways with the shipped detector."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_every_grain_is_projected_through_Order_02s_projector(self):
        run = _write_run(
            self.root,
            items=[
                _item(
                    attempts=[
                        _attempt(
                            tokens={
                                "input": 100,
                                "output": 50,
                                "reasoning": 5,
                                "total": 155,
                            },
                            verify=True,
                        )
                    ]
                )
            ],
        )
        facts = ingest.build_run_facts(run)
        projected = ingest.project_run_facts(facts)
        self.assertEqual(set(projected), {"run", "ipd", "attempt", "phase", "event"})
        for grain, records in projected.items():
            for record in records:
                with self.subTest(grain=grain):
                    allowed = (
                        privacy.ALLOWED_EVENT_KEYS
                        if grain == "event"
                        else privacy.ALLOWED_METRIC_KEYS
                    )
                    self.assertTrue(
                        set(record) <= set(allowed), set(record) - set(allowed)
                    )

    def test_the_projector_REFUSES_a_fact_carrying_a_key_it_does_not_name(self):
        """Refused, never dropped: that is the difference between a provable boundary and a hope."""

        with self.assertRaises(privacy.PrivacyRefusal) as ctx:
            privacy.project_metric_facts({"repo": _ABS_HOME})
        self.assertIn("repo", str(ctx.exception))
        self.assertIn("allowlist", str(ctx.exception))

    def test_NO_prompt_response_file_content_or_absolute_path_is_retained(self):
        run = _write_run(self.root)
        self.assertTrue(
            (run / "prompts" / "01-abc123-attempt-1.md").is_file(),
            "the fixture must actually contain the forbidden content",
        )
        serialized = json.dumps(ingest.project_run_facts(ingest.build_run_facts(run)))
        for forbidden in (
            _PROMPT_BODY,
            _ABS_HOME,
            _HANDLE,
            "oc_runipd.py",
            "state.json",
        ):
            with self.subTest(forbidden=forbidden[:24]):
                self.assertNotIn(forbidden, serialized)

    def test_the_shipped_detector_reports_CLEAN_over_projected_facts(self):
        run = _write_run(self.root)
        projected = json.dumps(
            ingest.project_run_facts(ingest.build_run_facts(run)), indent=1
        )
        ruleset = ls.build_ruleset(Path.cwd())
        findings = ls.scan_text(projected, "projected-facts.json", ruleset)
        self.assertEqual(
            [f.rule for f in findings], [], f"unexpected findings: {findings}"
        )

    def test_CONTROL_the_same_invocation_FLAGS_the_raw_repo_field(self):
        """Without this, a clean report and a detector that was not looking are indistinguishable.

        The control is the raw `repo` field, which every real `state.json` carries as an absolute
        home path; the shipped detector flags it at `fail`.
        """

        run = _write_run(self.root)
        raw_state = (run / "state.json").read_text(encoding="utf-8")
        raw_repo_line = json.dumps({"repo": _ABS_HOME})

        ruleset = ls.build_ruleset(Path.cwd())
        control = ls.scan_text(raw_repo_line, "raw-state.json", ruleset)
        self.assertTrue(control, "the detector MUST flag the raw repo field")
        self.assertEqual({f.severity for f in control}, {"fail"})
        self.assertIn(
            "home-path",
            {f.rule for f in control},
            f"expected a home-path rule, got {sorted(f.rule for f in control)}",
        )

        whole = ls.scan_text(raw_state, "raw-state.json", ruleset)
        self.assertTrue(whole, "the whole raw state file is also flagged")

    def test_the_projector_is_the_ONLY_path_by_which_a_fact_is_persisted(self):
        """Call-path proof: `build_cache_facts` output is already projected."""

        run = _write_run(self.root)
        metric_facts, event_facts, flags, warnings = ingest.build_cache_facts(run)
        self.assertTrue(set(metric_facts) <= set(privacy.ALLOWED_METRIC_KEYS))
        for event in event_facts:
            self.assertTrue(set(event) <= set(privacy.ALLOWED_EVENT_KEYS))
        # Idempotent: re-projecting changes nothing, which is what "already crossed" means.
        self.assertEqual(privacy.project_metric_facts(metric_facts), metric_facts)
        for label in list(flags) + list(warnings):
            self.assertNotIn("/", label)

    def test_an_unrealistic_run_id_is_REFUSED_by_the_projector(self):
        """The projector pins `run_id` to the real `run-<UTC stamp>-<pid>` shape, and that is correct.

        Recorded as a test because it caught a defect in this suite's OWN fixtures, which used ids
        like `...Z-good`. A fixture whose ids cannot occur in reality would have let the ingester
        ship having never met a value the boundary accepts.
        """

        with self.assertRaises(privacy.PrivacyRefusal):
            privacy.project_metric_facts({"run_id": "run-20260908T100000Z-good"})
        self.assertEqual(
            privacy.project_metric_facts({"run_id": "run-20260908T100000Z-1234"}),
            {"run_id": "run-20260908T100000Z-1234"},
        )

    def test_a_recorded_cost_is_never_labeled_an_estimate(self):
        """`cost_is_estimate` distinguishes priced money from reported money; Order 06 owns pricing."""

        run = _write_run(self.root)
        metric_facts, *_ = ingest.build_cache_facts(run)
        self.assertIn("cost", metric_facts)
        self.assertIs(metric_facts["cost_is_estimate"], False)


class CacheHandoffTests(unittest.TestCase):
    """E-08: the round trip through Order 02's cache, using its resolver and its envelope."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.repo = self.tmp / "repo"
        (self.repo / ".aw" / "records" / "runs").mkdir(parents=True)
        (self.repo / ".aw" / "config").mkdir(parents=True)
        self.runs_root = self.repo / ".aw" / "records" / "runs"

    def _terminal_run(self, run_id: str = "run-20260908T100000Z-1234") -> Path:
        return _write_run(
            self.runs_root,
            run_id,
            items=[
                _item(
                    attempts=[
                        _attempt(
                            tokens={
                                "input": 100,
                                "output": 50,
                                "reasoning": 5,
                                "total": 155,
                            }
                        )
                    ]
                )
            ],
        )

    def test_facts_reach_the_cache_ONLY_through_build_entry_and_round_trip(self):
        from agent_workflows import run_analytics_cache as cache

        run = self._terminal_run()
        report = ingest.update_analytics_cache([run], repo=self.repo)
        self.assertEqual(report.totals["total"], 1)
        self.assertEqual(
            report.decisions[0].verdict,
            "rebuild",
            report.decisions[0].to_dict(),
        )

        salt = privacy.load_or_create_salt(cache.cache_root(self.repo))
        root_id = cache.source_root_id(self.runs_root, salt=salt)
        entry = cache.load_entry(cache.entry_path(root_id, run.name, self.repo))
        self.assertEqual(entry.run_id, run.name)
        self.assertTrue(entry.is_complete)
        self.assertEqual(entry.metric_facts["tokens"]["reasoning"], 5)
        self.assertEqual(entry.metric_facts["token_total"], 155)

    def test_a_second_sweep_is_a_HIT_so_ingestion_is_incremental(self):
        run = self._terminal_run()
        ingest.update_analytics_cache([run], repo=self.repo)
        second = ingest.update_analytics_cache([run], repo=self.repo)
        self.assertEqual(second.decisions[0].verdict, "hit")
        self.assertEqual(second.decisions[0].reason, "fresh-complete-entry")

    def test_the_cached_entry_is_CLEAN_under_the_shipped_detector(self):
        from agent_workflows import run_analytics_cache as cache

        run = self._terminal_run()
        ingest.update_analytics_cache([run], repo=self.repo)
        salt = privacy.load_or_create_salt(cache.cache_root(self.repo))
        root_id = cache.source_root_id(self.runs_root, salt=salt)
        stored = cache.entry_path(root_id, run.name, self.repo).read_text(
            encoding="utf-8"
        )

        ruleset = ls.build_ruleset(Path.cwd())
        self.assertEqual(
            ls.scan_text(stored, "entry.json", ruleset),
            [],
            "the published entry must carry no forbidden value",
        )
        # CONTROL: the SOURCE the entry was built from is flagged, so the scan was looking.
        self.assertTrue(
            ls.scan_text(
                (run / "state.json").read_text(encoding="utf-8"), "state.json", ruleset
            )
        )

    def test_a_NON_TERMINAL_run_is_never_cached_as_stable(self):
        run = _write_run(
            self.runs_root,
            "run-20260908T110000Z-9",
            items=[_item(status="running", attempts=[_attempt(end=None)])],
        )
        report = ingest.update_analytics_cache([run], repo=self.repo)
        self.assertEqual(report.decisions[0].reason, "run-not-terminal")

    def test_a_damaged_run_is_skipped_without_ending_the_sweep(self):
        good = self._terminal_run("run-20260908T100000Z-1001")
        broken = self.runs_root / "run-20260908T100000Z-1002"
        broken.mkdir()
        (broken / "state.json").write_text("{ truncated", encoding="utf-8")

        report = ingest.update_analytics_cache([good, broken], repo=self.repo)
        self.assertEqual(report.totals["total"], 2)
        verdicts = {d.run_id: d.verdict for d in report.decisions}
        self.assertEqual(verdicts["run-20260908T100000Z-1001"], "rebuild")
        self.assertIn(verdicts["run-20260908T100000Z-1002"], {"rebuild", "skip"})


if __name__ == "__main__":
    unittest.main()
