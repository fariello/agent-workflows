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

    def test_provenance_states_partition_and_distinctness(self):
        self.assertEqual(
            schema.PRESENT_PROVENANCE | schema.ABSENT_PROVENANCE,
            set(Provenance),
        )
        self.assertEqual(schema.PRESENT_PROVENANCE & schema.ABSENT_PROVENANCE, set())
        self.assertEqual(len(schema.ABSENT_PROVENANCE), 3)

        a, b, c = missing(), unavailable(), not_applicable()
        self.assertNotEqual(a.provenance, b.provenance)
        self.assertNotEqual(b.provenance, c.provenance)
        self.assertNotEqual(a.provenance, c.provenance)
        self.assertEqual(
            {v.provenance.value for v in (a, b, c)},
            {"missing", "unavailable", "not-applicable"},
        )

        zero = recorded(0)
        self.assertTrue(zero.is_present)
        self.assertEqual(zero.as_number(), 0)

        for absent in (missing(), unavailable(), not_applicable()):
            self.assertTrue(absent.is_absent)
            self.assertIsNone(absent.number)
            self.assertNotEqual(absent, zero)
            with self.assertRaises(schema.SchemaError) as ctx:
                absent.as_number()
            self.assertIn("NOT zero", str(ctx.exception))

    def test_value_validation_defaults_and_refusals(self):
        self.assertEqual(missing().or_default(0), 0)
        self.assertEqual(missing().or_default(-1), -1)
        self.assertEqual(recorded(7).or_default(0), 7)

        for provenance in schema.PRESENT_PROVENANCE:
            with self.assertRaises(schema.SchemaError):
                Value(None, provenance)

        for provenance in schema.ABSENT_PROVENANCE:
            with self.assertRaises(schema.SchemaError):
                Value(0, provenance)

        for bad in (float("nan"), float("inf"), float("-inf")):
            with self.assertRaises(schema.SchemaError):
                recorded(bad)

        for bad in (True, "12", None):
            with self.assertRaises(schema.SchemaError):
                Value(bad, Provenance.RECORDED)  # type: ignore[arg-type]

        absent = missing("no-cost-recorded")
        self.assertEqual(absent.number or 0, 0)
        with self.assertRaises(schema.SchemaError):
            absent.as_number()

        self.assertEqual(missing("no-cost-recorded").note, "no-cost-recorded")
        for bad in ("free text with spaces", f"path {_ABS_HOME}", "a" * 200):
            with self.assertRaises(schema.SchemaError):
                missing(bad)


class UsageComponentMapTests(unittest.TestCase):
    """E-05: the token component map is OPEN, and an unseen key is preserved rather than dropped."""

    def test_usage_components_open_map_and_flattening(self):
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
        self.assertEqual(usage.total.as_number(), 1275)

        # Reasoning preserved
        u_reas = schema.usage_from_mapping(
            {"input": 100, "output": 50, "cache": 10, "reasoning": 5, "total": 165}
        )
        self.assertEqual(u_reas.components["reasoning"].as_number(), 5)

        # Invented key survives and participates in conservation
        invented = schema.usage_from_mapping(
            {"input": 10, "output": 5, "quantum_flux_tokens": 7, "total": 22}
        )
        self.assertEqual(invented.components["quantum_flux_tokens"].as_number(), 7)
        self.assertTrue(schema.check_conservation(invented).holds)

        # Nested cache flattened
        nested = schema.usage_from_mapping(
            {"input": 10, "cache": {"read": 4, "write": 6}, "total": 20}
        )
        self.assertEqual(nested.components["cache"].as_number(), 10)
        self.assertEqual(nested.components["cache"].note, "flattened")

        # Unparseable becomes missing
        unparseable = schema.usage_from_mapping({"input": "lots", "total": 5})
        self.assertTrue(unparseable.components["input"].is_absent)

        for empty in (None, {}):
            u_empty = schema.usage_from_mapping(empty)
            self.assertEqual(u_empty.components, {})
            self.assertTrue(u_empty.cost.is_absent)

    def test_usage_totals_and_merging(self):
        usage = schema.usage_from_mapping({"input": 10, "output": 5})
        self.assertTrue(usage.total.is_absent)
        computed = usage.derived_total()
        self.assertEqual(computed.as_number(), 15)
        self.assertEqual(computed.provenance, Provenance.DERIVED)

        self.assertTrue(
            Usage(components={"input": missing()}).derived_total().is_absent
        )
        self.assertEqual(
            Usage(
                components={
                    "input": recorded(10),
                    "output": missing(),
                    "total": recorded(10),
                }
            ).component_numbers(),
            {"input": 10, "total": 10},
        )

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
        self.assertEqual(merged.cost.as_number(), 1.5)

    def test_usage_component_label_safety_and_containment(self):
        for bad in (
            f"tokens{_ABS_HOME}",
            "has spaces",
            "../escape",
            "/leading",
            "a/b",
            f"x{_HANDLE}/y",
        ):
            with self.assertRaises(schema.SchemaError):
                Usage(components={bad: recorded(1)})

        usage = schema.usage_from_mapping(
            {"input": 10, f"evil{_ABS_HOME}": 999, "total": 10}
        )
        self.assertEqual(set(usage.components), {"input", "total"})
        self.assertEqual(usage.dropped_component_count, 1)
        self.assertTrue(schema.check_conservation(usage).holds)
        serialized = json.dumps(usage.to_dict())
        self.assertNotIn(_ABS_HOME, serialized)
        self.assertNotIn(_HANDLE, serialized)

        fact = schema.Fact(
            grain=Grain.ATTEMPT,
            run_id="run-1",
            usage=schema.usage_from_mapping(
                {"input": 1, f"evil{_ABS_HOME}": 2, "total": 1}
            ),
        )
        quality = schema.summarize_quality("run-1", [fact])
        self.assertIn("unsafe-component-name-dropped", quality.warnings)

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

    def test_conservation_all_components_holds_and_four_term_divergence(self):
        for delta in _MEASURED_REASONING_DELTAS:
            usage = self._measured_attempt(delta)
            result = schema.check_conservation(usage)
            self.assertTrue(result.holds)
            self.assertEqual(result.delta, 0)
            self.assertIn("reasoning", result.components)

            four = schema.check_conservation_four_term(usage)
            self.assertFalse(four.holds)
            self.assertEqual(four.delta, delta)

        # Both agree when no reasoning key present
        plain = schema.usage_from_mapping(
            {"input": 100, "output": 50, "cache": 10, "total": 160}
        )
        self.assertTrue(schema.check_conservation(plain).holds)
        self.assertTrue(schema.check_conservation_four_term(plain).holds)

    def test_conservation_mismatch_tolerance_and_unreconcilable(self):
        mismatch = schema.usage_from_mapping(
            {"input": 100, "output": 50, "cache": 10, "total": 999}
        )
        res = schema.check_conservation(mismatch)
        self.assertFalse(res.holds)
        self.assertEqual(res.delta, 839)

        tolerant = schema.usage_from_mapping({"input": 100, "output": 50, "total": 151})
        self.assertFalse(schema.check_conservation(tolerant).holds)
        self.assertTrue(schema.check_conservation(tolerant, tolerance=1).holds)

        # Absent or partial total unreconcilable
        self.assertTrue(
            schema.check_conservation(
                schema.usage_from_mapping({"input": 10, "output": 5})
            ).holds
        )
        self.assertTrue(
            schema.check_conservation(
                Usage(
                    components={
                        "input": recorded(100),
                        "output": missing(),
                        "total": recorded(160),
                    }
                )
            ).holds
        )
        self.assertTrue(
            schema.check_conservation(Usage(components={"total": recorded(100)})).holds
        )

        dict_res = schema.check_conservation(
            schema.usage_from_mapping({"input": 3, "output": 4, "total": 7})
        )
        self.assertEqual(dict_res.to_dict()["holds"], True)
        self.assertEqual(dict_res.to_dict()["delta"], 0)


class TimeAccountingTests(unittest.TestCase):
    """E-05: wall time and activity time are separate, and overlap is visible not smoothed."""

    def test_time_accounting_overlapping_nested_and_zero_overlap(self):
        # Overlapping activities
        acc = schema.account_intervals(
            [(0.0, 600.0), (300.0, 900.0)], wall_start=0.0, wall_end=1200.0
        )
        self.assertEqual(acc.wall_seconds.as_number(), 1200.0)
        self.assertEqual(acc.observed_activity_seconds.as_number(), 900.0)
        self.assertEqual(acc.overlap_seconds.as_number(), 300.0)
        self.assertEqual(acc.unattributed_seconds.as_number(), 300.0)
        self.assertNotEqual(
            acc.observed_activity_seconds.as_number(), acc.wall_seconds.as_number()
        )

        # Non-overlapping
        acc_non = schema.account_intervals(
            [(0.0, 100.0), (200.0, 300.0)], wall_start=0.0, wall_end=400.0
        )
        self.assertEqual(acc_non.observed_activity_seconds.as_number(), 200.0)
        self.assertEqual(acc_non.overlap_seconds.as_number(), 0.0)

        # Fully nested
        acc_nest = schema.account_intervals(
            [(0.0, 100.0), (25.0, 75.0)], wall_start=0.0, wall_end=100.0
        )
        self.assertEqual(acc_nest.observed_activity_seconds.as_number(), 100.0)
        self.assertEqual(acc_nest.overlap_seconds.as_number(), 50.0)

    def test_time_accounting_edge_cases_and_absent(self):
        # Negative unattributed
        acc_neg = schema.account_intervals(
            [(0.0, 500.0)], wall_start=0.0, wall_end=100.0
        )
        self.assertEqual(acc_neg.unattributed_seconds.as_number(), -400.0)

        # No intervals with window
        acc_empty = schema.account_intervals([], wall_start=0.0, wall_end=60.0)
        self.assertEqual(acc_empty.wall_seconds.as_number(), 60.0)
        self.assertEqual(acc_empty.observed_activity_seconds.as_number(), 0.0)

        # No intervals and no window is absent everywhere
        acc_none = schema.account_intervals([])
        for value in (
            acc_none.wall_seconds,
            acc_none.observed_activity_seconds,
            acc_none.overlap_seconds,
            acc_none.unattributed_seconds,
        ):
            self.assertTrue(value.is_absent)

        # Intervals without wall window mark unattributed unavailable
        acc_no_win = schema.account_intervals([(0.0, 10.0)])
        self.assertEqual(acc_no_win.observed_activity_seconds.as_number(), 10.0)
        self.assertEqual(
            acc_no_win.unattributed_seconds.provenance, Provenance.UNAVAILABLE
        )


class FactTableTests(unittest.TestCase):
    """E-04/E-05: every grain is produced and round-trips, with phases kept separate."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_fact_table_grains_phases_and_driver_label(self):
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
            payload = fact.to_dict()
            self.assertEqual(payload["schema_version"], schema.FACT_SCHEMA_VERSION)
            self.assertEqual(payload["grain"], fact.grain.value)
            self.assertEqual(fact.driver_generation, "oc_runipd")
            self.assertNotIn("/", fact.driver_generation)

        # Phases separately visible
        phases = {f.phase: f for f in facts.by_grain(Grain.PHASE)}
        self.assertIn(Phase.EXECUTE, phases)
        self.assertIn(Phase.VERIFY, phases)
        self.assertEqual(phases[Phase.EXECUTE].usage.cost.as_number(), 1.5)
        self.assertEqual(phases[Phase.VERIFY].usage.cost.as_number(), 0.25)

        # Verify not ran is not applicable
        run_no_ver = _write_run(
            self.root,
            "run-no-ver",
            items=[_item(attempts=[_attempt(tokens={"input": 10, "total": 10})])],
        )
        facts_no_ver = ingest.build_run_facts(run_no_ver)
        verify = next(
            f for f in facts_no_ver.by_grain(Grain.PHASE) if f.phase is Phase.VERIFY
        )
        self.assertEqual(verify.usage.cost.provenance, Provenance.NOT_APPLICABLE)

        # Review and Recovery phases
        run_rev = _write_run(
            self.root, "run-rev", items=[_item(action="review", status="reviewed")]
        )
        self.assertEqual(
            {f.phase for f in ingest.build_run_facts(run_rev).by_grain(Grain.ATTEMPT)},
            {Phase.REVIEW},
        )

        run_rec = _write_run(
            self.root,
            "run-rec",
            items=[_item(attempts=[_attempt(1), _attempt(2, recovery=True)])],
        )
        by_att = {
            f.attempt: f
            for f in ingest.build_run_facts(run_rec).by_grain(Grain.ATTEMPT)
        }
        self.assertEqual(by_att[1].phase, Phase.EXECUTE)
        self.assertEqual(by_att[2].phase, Phase.RECOVERY)

    def test_fact_table_unclosed_broken_and_conservation_flags(self):
        run = _write_run(self.root, items=[_item(attempts=[_attempt(end=None)])])
        attempt = ingest.build_run_facts(run).by_grain(Grain.ATTEMPT)[0]
        self.assertTrue(attempt.time.wall_seconds.is_absent)
        self.assertEqual(attempt.time.wall_seconds.note, "attempt-not-closed")

        broken = self.root / "run-20260908T100000Z-1002"
        broken.mkdir()
        (broken / "state.json").write_text("{ truncated", encoding="utf-8")
        facts = ingest.build_run_facts(broken)
        self.assertEqual(facts.facts, ())
        self.assertFalse(facts.quality.is_complete)
        self.assertIn("state-unreadable", facts.quality.warnings)

        run_viol = _write_run(
            self.root,
            "run-viol",
            items=[
                _item(
                    attempts=[
                        _attempt(tokens={"input": 100, "output": 50, "total": 999})
                    ]
                )
            ],
        )
        facts_viol = ingest.build_run_facts(run_viol)
        self.assertFalse(facts_viol.conservation_holds)
        self.assertIn(
            "conservation-violation",
            facts_viol.by_grain(Grain.ATTEMPT)[0].quality_flags,
        )
        self.assertIn(
            "conservation-violation", facts_viol.by_grain(Grain.RUN)[0].quality_flags
        )


class DeduplicationAndPartialRunTests(unittest.TestCase):
    """E-07: a resumed or damaged run degrades only ITSELF, and nothing is double counted."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_deduplication_multi_attempt_and_resumed(self):
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
        self.assertEqual(len(attempts), 2)
        ipd = facts.by_grain(Grain.IPD)[0]
        self.assertEqual(ipd.usage.components["total"].as_number(), 300)
        self.assertEqual(ipd.usage.cost.as_number(), 3.0)

        # Resumed run not double counted
        second = ingest.build_run_facts(run)
        self.assertEqual(
            [f.to_dict() for f in facts.facts], [f.to_dict() for f in second.facts]
        )

        # Deduplicate function
        def make_fact(att: int, ph: Phase) -> schema.Fact:
            return schema.Fact(
                grain=Grain.ATTEMPT,
                run_id="run-1",
                ipd_id6="abc123",
                position=1,
                attempt=att,
                phase=ph,
                source="state",
            )

        kept, dropped = schema.deduplicate(
            [
                make_fact(1, Phase.EXECUTE),
                make_fact(2, Phase.EXECUTE),
                make_fact(1, Phase.VERIFY),
                make_fact(1, Phase.EXECUTE),
            ]
        )
        self.assertEqual(len(kept), 3)
        self.assertEqual(dropped, ["duplicate-attempt"])

    def test_partial_damaged_run_containment_and_quality_summary(self):
        run = _write_run(
            self.root,
            events=[
                '{"at":"2026-09-08T10:00:00Z","event":"run-created"}',
                "{ THIS LINE IS CORRUPT",
                '{"at":"2026-09-08T10:00:01Z","event":"ipd-started"}',
            ],
        )
        facts = ingest.build_run_facts(run)
        self.assertEqual(facts.quality.parse_error_count, 1)
        self.assertIn("event-line-unparseable", facts.quality.warnings)
        self.assertEqual(len(facts.by_grain(Grain.EVENT)), 2)

        # Damaged run containment
        good = _write_run(self.root, "run-20260908T100000Z-1001")
        broken = self.root / "run-20260908T100000Z-1002"
        broken.mkdir()
        (broken / "state.json").write_text("{ truncated", encoding="utf-8")
        results, warnings = ingest.ingest_corpus([good, broken])
        self.assertEqual(warnings, [])
        self.assertEqual(len(results), 2)
        self.assertEqual({r.quality.is_complete for r in results}, {True, False})

        # Quality summary buckets
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
        self.assertIn("tokens.input", quality.missing_fields)
        self.assertIn("tokens.output", quality.unavailable_fields)
        self.assertIn("cost", quality.unavailable_fields)
        self.assertIn("tokens.cache", quality.not_applicable_fields)

        for warning in facts.quality.warnings:
            self.assertNotIn("/", warning)
            self.assertNotIn(" ", warning)


class AdvertisedMetricProductionTests(unittest.TestCase):
    """metgap `6krsym`: a metric the query grammar OFFERS must be one a producer actually emits."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _run_payload(self, run: Path) -> dict:
        projected = ingest.project_run_facts(ingest.build_run_facts(run))
        return projected["run"][0]

    def test_advertised_metrics_emitted_and_duration_seconds_absent(self):
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
        satisfied = set(payload) | ({"tokens"} if "token_total" in payload else set())
        for metric in query_mod.AGGREGATE_METRICS:
            self.assertIn(metric, satisfied)

        self.assertNotIn("duration_seconds", query_mod.AGGREGATE_METRICS)
        self.assertNotIn("duration_seconds", payload)

    def test_event_count_semantics_and_grains(self):
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

        # Unparseable line not counted
        run_corrupt = _write_run(
            self.root,
            "run-20260908T100000Z-2001",
            events=['{"at":"2026-09-08T10:00:00Z","event":"run-created"}', "{ CORRUPT"],
        )
        self.assertEqual(self._run_payload(run_corrupt)["event_count"], 1)

        # Empty events file counts 0
        run_empty = _write_run(self.root, "run-20260908T100000Z-2002", events=[])
        (run_empty / "events.jsonl").write_text("", encoding="utf-8")
        self.assertEqual(self._run_payload(run_empty)["event_count"], 0)

        # No events file omits key
        run_no_ev = _write_run(self.root, "run-20260908T100000Z-2003")
        (run_no_ev / "events.jsonl").unlink()
        self.assertNotIn("event_count", self._run_payload(run_no_ev))

        # Event count is RUN grain only
        projected = ingest.project_run_facts(facts)
        for grain in ("ipd", "attempt", "phase"):
            for record in projected.get(grain, []):
                self.assertNotIn("event_count", record)


class TokenAbsenceClassificationTests(unittest.TestCase):
    """metgap `6krsym` E-06: the ingester records WHY a token total is absent, or says nothing."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _flags(self, **kwargs) -> set[str]:
        run = _write_run(self.root, **kwargs)
        facts = ingest.build_run_facts(run)
        return set(facts.by_grain(Grain.RUN)[0].quality_flags)

    def test_token_absence_flags_for_empty_or_unfinished(self):
        flags_tokens = self._flags(
            items=[_item(attempts=[_attempt(tokens={"input": 10, "total": 10})])]
        )
        self.assertNotIn(ingest.TOKENS_NOTHING_TO_RECORD_FLAG, flags_tokens)
        self.assertNotIn(ingest.TOKENS_RUN_UNFINISHED_FLAG, flags_tokens)

        # Dispatched no attempt
        self.assertIn(
            ingest.TOKENS_NOTHING_TO_RECORD_FLAG,
            self._flags(items=[_item(status="not-attempted", attempts=[])]),
        )
        # Orchestrate-only
        self.assertIn(
            ingest.TOKENS_NOTHING_TO_RECORD_FLAG,
            self._flags(items=[_item(action="orchestrate", attempts=[])]),
        )
        # Empty queue
        self.assertIn(ingest.TOKENS_NOTHING_TO_RECORD_FLAG, self._flags(items=[]))

        # Running item is unfinished
        flags_run = self._flags(items=[_item(status="running", attempts=[])])
        self.assertIn(ingest.TOKENS_RUN_UNFINISHED_FLAG, flags_run)
        self.assertNotIn(ingest.TOKENS_NOTHING_TO_RECORD_FLAG, flags_run)

        # Flag in projected payload
        run = _write_run(
            self.root,
            "run-20260908T100000Z-2004",
            items=[_item(status="not-attempted", attempts=[])],
        )
        payload = ingest.project_run_facts(ingest.build_run_facts(run))["run"][0]
        self.assertIn(ingest.TOKENS_NOTHING_TO_RECORD_FLAG, payload["quality_flags"])

    def test_token_absence_loss_never_explained_away(self):
        # Dispatched turn with no tokens stays unexplained
        flags_loss = self._flags(
            items=[_item(attempts=[_attempt(tokens=None, cost=2.0)])]
        )
        self.assertNotIn(ingest.TOKENS_NOTHING_TO_RECORD_FLAG, flags_loss)
        self.assertNotIn(ingest.TOKENS_RUN_UNFINISHED_FLAG, flags_loss)

        # Mixed queue
        flags_mix = self._flags(
            items=[
                _item("aaa111", position=1, status="not-attempted", attempts=[]),
                _item("bbb222", position=2, attempts=[_attempt(tokens=None, cost=1.0)]),
            ]
        )
        self.assertNotIn(ingest.TOKENS_NOTHING_TO_RECORD_FLAG, flags_mix)


class ConservationSurveyTests(unittest.TestCase):
    """E-06: the both-forms survey, which makes the measurement reproducible rather than cited."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_conservation_survey_divergence_auditing_and_resilience(self):
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
        self.assertEqual(survey["all_components"]["held"], 6)
        self.assertEqual(survey["all_components"]["failed"], 0)
        self.assertEqual(survey["four_term"]["held"], 4)
        self.assertEqual(survey["four_term"]["failed"], 2)
        self.assertEqual(
            sorted(f["delta"] for f in survey["four_term"]["failures"]),
            sorted(_MEASURED_REASONING_DELTAS),
        )

        # Auditable failure detail
        run_bad = _write_run(
            self.root,
            "run-bad",
            items=[
                _item(
                    "bad001",
                    attempts=[_attempt(tokens={"input": 1, "output": 1, "total": 99})],
                )
            ],
        )
        failure = ingest.conservation_survey([run_bad])["all_components"]["failures"][0]
        self.assertEqual(failure["ipd_id6"], "bad001")
        self.assertEqual(failure["delta"], 97)

        # Damaged run resilience
        broken = self.root / "run-broken"
        broken.mkdir()
        (broken / "state.json").write_text("{ nope", encoding="utf-8")
        surv_res = ingest.conservation_survey([run_bad, broken])
        self.assertEqual(surv_res["attempts_checked"], 1)

        # Attempt with no total not counted
        run_no_tot = _write_run(
            self.root, "run-no-tot", items=[_item(attempts=[_attempt(tokens=None)])]
        )
        self.assertEqual(
            ingest.conservation_survey([run_no_tot])["attempts_checked"], 0
        )


class PrivacyBoundaryTests(unittest.TestCase):
    """E-08: every fact crosses Order 02's projector, proven BOTH ways with the shipped detector."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_privacy_projector_allowlist_boundaries_and_sanitizer_clean(self):
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
            allowed = (
                privacy.ALLOWED_EVENT_KEYS
                if grain == "event"
                else privacy.ALLOWED_METRIC_KEYS
            )
            for record in records:
                self.assertTrue(set(record) <= set(allowed))

        # Refusal on unallowed key
        with self.assertRaises(privacy.PrivacyRefusal):
            privacy.project_metric_facts({"repo": _ABS_HOME})

        # No forbidden strings retained
        serialized = json.dumps(projected)
        for forbidden in (
            _PROMPT_BODY,
            _ABS_HOME,
            _HANDLE,
            "oc_runipd.py",
            "state.json",
        ):
            self.assertNotIn(forbidden, serialized)

        # Shipped detector reports clean over projected facts
        ruleset = ls.build_ruleset(Path.cwd())
        findings = ls.scan_text(serialized, "projected-facts.json", ruleset)
        self.assertEqual([f.rule for f in findings], [])

    def test_privacy_detector_control_and_projector_invariants(self):
        # CONTROL: detector flags raw repo field
        ruleset = ls.build_ruleset(Path.cwd())
        control = ls.scan_text(
            json.dumps({"repo": _ABS_HOME}), "raw-state.json", ruleset
        )
        self.assertTrue(control)
        self.assertEqual({f.severity for f in control}, {"fail"})

        # Projector sole path
        run = _write_run(self.root)
        metric_facts, event_facts, flags, warnings = ingest.build_cache_facts(run)
        self.assertTrue(set(metric_facts) <= set(privacy.ALLOWED_METRIC_KEYS))
        for event in event_facts:
            self.assertTrue(set(event) <= set(privacy.ALLOWED_EVENT_KEYS))
        self.assertEqual(privacy.project_metric_facts(metric_facts), metric_facts)

        # Unrealistic run id refused
        with self.assertRaises(privacy.PrivacyRefusal):
            privacy.project_metric_facts({"run_id": "run-20260908T100000Z-good"})
        self.assertEqual(
            privacy.project_metric_facts({"run_id": "run-20260908T100000Z-1234"}),
            {"run_id": "run-20260908T100000Z-1234"},
        )
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

    def test_cache_handoff_lifecycle_cleanliness_and_resilience(self):
        from agent_workflows import run_analytics_cache as cache

        run = self._terminal_run()
        report = ingest.update_analytics_cache([run], repo=self.repo)
        self.assertEqual(report.totals["total"], 1)
        self.assertEqual(report.decisions[0].verdict, "rebuild")

        salt = privacy.load_or_create_salt(cache.cache_root(self.repo))
        root_id = cache.source_root_id(self.runs_root, salt=salt)
        entry = cache.load_entry(cache.entry_path(root_id, run.name, self.repo))
        self.assertEqual(entry.run_id, run.name)
        self.assertTrue(entry.is_complete)
        self.assertEqual(entry.metric_facts["token_total"], 155)

        # Hit on second sweep
        second = ingest.update_analytics_cache([run], repo=self.repo)
        self.assertEqual(second.decisions[0].verdict, "hit")

        # Stored entry clean under detector
        stored = cache.entry_path(root_id, run.name, self.repo).read_text(
            encoding="utf-8"
        )
        ruleset = ls.build_ruleset(Path.cwd())
        self.assertEqual(ls.scan_text(stored, "entry.json", ruleset), [])

        # Non-terminal run not cached as stable
        run_running = _write_run(
            self.runs_root,
            "run-20260908T110000Z-9",
            items=[_item(status="running", attempts=[_attempt(end=None)])],
        )
        rep_run = ingest.update_analytics_cache([run_running], repo=self.repo)
        self.assertEqual(rep_run.decisions[0].reason, "run-not-terminal")

        # Damaged run skipped
        broken = self.runs_root / "run-20260908T100000Z-1002"
        broken.mkdir()
        (broken / "state.json").write_text("{ truncated", encoding="utf-8")
        rep_dam = ingest.update_analytics_cache([run, broken], repo=self.repo)
        self.assertEqual(rep_dam.totals["total"], 2)


if __name__ == "__main__":
    unittest.main()
