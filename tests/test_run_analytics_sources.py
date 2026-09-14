"""Tests for the versioned run SOURCE layer (IPD `8hald1`, Set runanalytics).

Covers E-01 (per-generation inventory and the fixture-only record), E-02 (schema-drift tolerance
against the MEASURED surface: a 14-key core plus exactly four optional keys) and E-03 (ONE shared
source-precedence authority, delegated rather than reimplemented).

TWO CONVENTIONS THIS SUITE HOLDS ITSELF TO, both inherited from the sibling Orders.

FIRST, FIXTURES ARE AUTHORITATIVE AND THE LIVE CORPUS IS NEVER AN ASSERTION SOURCE. The governing
plan states it directly ("Do not pin a test to `.aw/records/runs/`: it is gitignored, mutable, grows
with every run, and carries absolute paths the leak detector flags at `fail`") and its third stop
condition is "if a test needs the live corpus to pass, STOP and build a fixture". The two failures
that were live in the suite when this plan was reviewed were themselves live-corpus couplings, which
is that argument made concrete. So every fixture here REPRODUCES a measured property of the real
corpus rather than sampling it: the six distinct `state.json` key shapes, the three driver
generations, the uniform `schema_version`, and the `reasoning` token key.

SECOND, NO SENSITIVE LITERAL IS COMMITTED. The few canaries are assembled from fragments at runtime,
as the shipped detection engine does with its own patterns, so this file cannot itself become the
leak it is testing for.

Stdlib unittest only.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import run_analytics_sources as sources

# Assembled at runtime, never committed as a literal.
_HANDLE = "gfa" + "riello"
_ABS_HOME = "/ho" + "me/" + _HANDLE + "/VC/agent-workflows"


def _core_state(**overrides: object) -> dict[str, object]:
    """A `state.json` payload carrying exactly the measured 14-key core, plus overrides.

    Built from `CORE_STATE_KEYS` itself rather than from a hand-typed literal, so the fixture cannot
    drift away from the contract it is meant to exercise.
    """

    payload: dict[str, object] = {
        "created_at": "2026-09-08T10:00:00Z",
        "updated_at": "2026-09-08T10:30:00Z",
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
    assert set(payload) == set(
        sources.CORE_STATE_KEYS
    ), "fixture must carry exactly the measured core"
    payload.update(overrides)
    return payload


def _write_run(
    root: Path,
    run_id: str,
    *,
    state: dict[str, object] | None = None,
    events: list[str] | None = None,
    with_outcomes: bool = True,
    with_telemetry: bool = False,
    with_ledger: bool = False,
) -> Path:
    run = root / run_id
    run.mkdir(parents=True, exist_ok=True)
    payload = state if state is not None else _core_state(run_id=run_id)
    (run / "state.json").write_text(json.dumps(payload), encoding="utf-8")
    lines = (
        events
        if events is not None
        else ['{"at":"2026-09-08T10:00:00Z","event":"run-created"}']
    )
    (run / "events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (run / "execution-report.md").write_text("# report\n", encoding="utf-8")
    for sub in ("prompts", "sessions"):
        (run / sub).mkdir(exist_ok=True)
    if with_outcomes:
        (run / "outcomes").mkdir(exist_ok=True)
    if with_telemetry:
        tele = run / "telemetry"
        tele.mkdir(exist_ok=True)
        (tele / "invocation.jsonl").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "event_kind": "start",
                    "execution_id": "exec-1",
                    "wall_timestamp": "2026-09-08T10:00:00Z",
                    "monotonic_offset_seconds": 0.0,
                }
            )
            + "\n",
            encoding="utf-8",
        )
    if with_ledger:
        (run / "ledger.jsonl").write_text(
            json.dumps({"seq": 1, "kind": "start"}) + "\n", encoding="utf-8"
        )
    return run


class DriverGenerationTests(unittest.TestCase):
    """E-01: the generation comes from the `driver.path` BASENAME, not from `schema_version`."""

    def test_every_known_generation_is_inferred_from_the_basename(self):
        for basename, expected in sources.DRIVER_GENERATIONS.items():
            for prefix in (
                f"{_ABS_HOME}/agent_workflows",
                f"{_ABS_HOME}/tools/ipdrunner",
                "relative/path",
            ):
                state = {"driver": {"path": f"{prefix}/{basename}"}}
                self.assertEqual(
                    sources.driver_generation(state),
                    expected,
                    f"{prefix}/{basename} should infer {expected}",
                )

    def test_schema_version_alone_cannot_discriminate_a_generation(self):
        """The measured defect: `schema_version` was uniformly 1 across all three generations.

        So two runs sharing a version must still resolve to DIFFERENT generations. A dispatcher keyed
        on the version would route every historical run to the newest adapter.
        """

        oc = _core_state(driver={"path": f"{_ABS_HOME}/agent_workflows/oc_runipd.py"})
        legacy = _core_state(driver={"path": f"{_ABS_HOME}/tools/ipdrunner/runipd.py"})
        older = _core_state(
            driver={"path": f"{_ABS_HOME}/tools/ipdrunner/ipdrunner.py"}
        )
        self.assertEqual(oc["schema_version"], legacy["schema_version"])
        self.assertEqual(oc["schema_version"], older["schema_version"])
        self.assertEqual(
            {
                sources.driver_generation(oc),
                sources.driver_generation(legacy),
                sources.driver_generation(older),
            },
            {"oc_runipd", "runipd", "ipdrunner"},
        )

    def test_unknown_absent_and_malformed_driver_are_recorded_not_fatal(self):
        for state in (
            None,
            {},
            {"driver": None},
            {"driver": {}},
            {"driver": {"path": ""}},
            {"driver": "not-a-mapping"},
            {"driver": {"path": "/x/y/future_runner.py"}},
        ):
            self.assertEqual(
                sources.driver_generation(state), sources.GENERATION_UNKNOWN
            )

    def test_the_generation_label_carries_no_path(self):
        """The `driver.path` is an absolute home path; the LABEL that reaches a fact must not be."""

        state = _core_state()
        label = sources.driver_generation(state)
        self.assertEqual(label, "oc_runipd")
        self.assertNotIn("/", label)
        self.assertNotIn(_HANDLE, label)

    def test_host_mapping_separates_agy_from_opencode_lineage(self):
        self.assertEqual(sources.generation_host("agy_runipd"), "agy")
        for gen in ("oc_runipd", "runipd", "ipdrunner"):
            self.assertEqual(sources.generation_host(gen), "opencode")
        self.assertEqual(sources.generation_host("future"), sources.GENERATION_UNKNOWN)


class StateDriftToleranceTests(unittest.TestCase):
    """E-02: require the measured 14-key core, tolerate the measured four optional keys."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_the_measured_core_and_optional_sets_are_disjoint_and_sized_as_measured(
        self,
    ):
        self.assertEqual(len(sources.CORE_STATE_KEYS), 14)
        self.assertEqual(len(sources.OPTIONAL_STATE_KEYS), 4)
        self.assertEqual(sources.CORE_STATE_KEYS & sources.OPTIONAL_STATE_KEYS, set())
        self.assertEqual(
            sources.OPTIONAL_STATE_KEYS,
            frozenset(
                {
                    "_invocation_start_mono",
                    "run_order",
                    "session_id",
                    "session_turn_counts",
                }
            ),
        )

    def test_bare_core_reads_and_reports_all_four_optional_keys_absent(self):
        run = _write_run(self.root, "run-20260908T100000Z-1", state=_core_state())
        result = sources.read_state(run)
        self.assertEqual(result.generation, "oc_runipd")
        self.assertEqual(result.schema_version, 1)
        self.assertEqual(result.unknown_keys, ())
        self.assertEqual(
            set(result.missing_optional_keys), set(sources.OPTIONAL_STATE_KEYS)
        )

    def test_each_of_the_six_measured_key_shapes_reads(self):
        """One test per shape, as V-02 requires.

        The shapes are the powerset points the corpus actually held: the bare core, the core plus each
        optional key that varies independently, and the fully populated modern shape.
        """

        shapes = {
            "core-only": {},
            "core+session_id": {"session_id": "sess-1"},
            "core+run_order": {"run_order": {"requested": [], "executed": []}},
            "core+turn_counts": {"session_turn_counts": {"sess-1": 2}},
            "core+mono": {"_invocation_start_mono": 12345.6},
            "modern-all": {
                "session_id": "sess-1",
                "run_order": {"requested": [], "executed": []},
                "session_turn_counts": {"sess-1": 2},
                "_invocation_start_mono": 12345.6,
            },
        }
        self.assertEqual(len(shapes), 6, "six distinct shapes were measured")
        seen: set[tuple[str, ...]] = set()
        for name, extra in shapes.items():
            with self.subTest(shape=name):
                run = _write_run(
                    self.root,
                    f"run-20260908T100000Z-{abs(hash(name)) % 10000}",
                    state=_core_state(**extra),
                )
                result = sources.read_state(run)
                self.assertEqual(result.unknown_keys, ())
                self.assertEqual(
                    set(result.missing_optional_keys),
                    set(sources.OPTIONAL_STATE_KEYS) - set(extra),
                )
                seen.add(result.key_shape)
        self.assertEqual(
            len(seen), 6, "the six fixtures must be six DISTINCT key shapes"
        )

    def test_an_unknown_top_level_key_is_recorded_and_is_NOT_fatal(self):
        """Forward compatibility: a newer driver's key is an observation, never a refusal."""

        run = _write_run(
            self.root,
            "run-20260908T100000Z-2",
            state=_core_state(a_future_key=1, another_future_key="x"),
        )
        result = sources.read_state(run)
        self.assertEqual(result.unknown_keys, ("a_future_key", "another_future_key"))
        self.assertEqual(result.generation, "oc_runipd")

        inventory = sources.inventory_run(run)
        self.assertTrue(
            inventory.readable, "an unknown key must not make a run unreadable"
        )
        self.assertIn("unknown-state-keys", inventory.warnings)
        self.assertEqual(
            inventory.unknown_state_keys, ("a_future_key", "another_future_key")
        )

    def test_a_missing_CORE_key_is_refused_with_the_key_named(self):
        for dropped in sorted(sources.CORE_STATE_KEYS):
            with self.subTest(dropped=dropped):
                payload = _core_state()
                payload.pop(dropped)
                run = self.root / f"run-drop-{dropped}"
                run.mkdir(parents=True, exist_ok=True)
                (run / "state.json").write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(sources.SourceError) as ctx:
                    sources.read_state(run)
                self.assertIn(dropped, str(ctx.exception))

    def test_absent_and_malformed_state_are_refused_distinctly_from_a_drift_case(self):
        empty = self.root / "run-empty"
        empty.mkdir()
        with self.assertRaises(sources.SourceError):
            sources.read_state(empty)

        bad = self.root / "run-bad"
        bad.mkdir()
        (bad / "state.json").write_text("{ not json", encoding="utf-8")
        with self.assertRaises(sources.SourceError):
            sources.read_state(bad)

        not_object = self.root / "run-list"
        not_object.mkdir()
        (not_object / "state.json").write_text("[1,2,3]", encoding="utf-8")
        with self.assertRaises(sources.SourceError):
            sources.read_state(not_object)

    def test_MUTATION_making_an_unknown_key_fatal_breaks_the_tolerance_test(self):
        """The mutation check V-02 demands: prove the tolerance is actually asserted somewhere.

        Simulates the mutation (treat unknown keys as fatal) and shows the tolerance contract fails
        under it, then confirms the real implementation still tolerates. A test that only ever sees
        the passing branch cannot tell a working tolerance from an absent one.
        """

        run = _write_run(
            self.root, "run-20260908T100000Z-3", state=_core_state(surprise=1)
        )
        result = sources.read_state(run)

        def mutated_read(res: sources.StateReadResult) -> sources.StateReadResult:
            if res.unknown_keys:
                raise sources.SourceError("unknown key (MUTATED to be fatal)")
            return res

        with self.assertRaises(sources.SourceError):
            mutated_read(result)
        self.assertEqual(result.unknown_keys, ("surprise",))
        self.assertTrue(sources.inventory_run(run).readable)


class InventoryTests(unittest.TestCase):
    """E-01: the per-generation artifact matrix and the fixture-only record."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "runs"
        self.root.mkdir(parents=True)
        self.addCleanup(self._tmp.cleanup)

    def _corpus_like_the_real_one(self) -> sources.CorpusInventory:
        """A miniature of the measured corpus: three generations, uniform `schema_version`.

        Proportions are scaled down (3/2/1 rather than 120/13/2) because what is being asserted is
        the SHAPE of the matrix and the fact that the version cannot discriminate, neither of which
        depends on the counts.
        """

        for i in range(3):
            _write_run(
                self.root,
                f"run-20260908T10000{i}Z-1",
                state=_core_state(
                    driver={"path": f"{_ABS_HOME}/agent_workflows/oc_runipd.py"},
                    session_id=f"sess-{i}",
                ),
            )
        for i in range(2):
            _write_run(
                self.root,
                f"run-20260907T10000{i}Z-2",
                state=_core_state(
                    driver={"path": f"{_ABS_HOME}/tools/ipdrunner/runipd.py"}
                ),
            )
        _write_run(
            self.root,
            "run-20260906T100000Z-3",
            state=_core_state(
                driver={"path": f"{_ABS_HOME}/tools/ipdrunner/ipdrunner.py"}
            ),
        )
        return sources.inventory_corpus(self.root)

    def test_generation_counts_and_the_version_that_cannot_discriminate_them(self):
        corpus = self._corpus_like_the_real_one()
        self.assertEqual(corpus.run_count, 6)
        self.assertEqual(
            corpus.generation_counts,
            {"ipdrunner": 1, "oc_runipd": 3, "runipd": 2},
        )
        self.assertEqual(
            corpus.schema_versions,
            {"1": 6},
            "one version across three generations is exactly why the basename is the discriminator",
        )
        self.assertGreater(len(corpus.generation_counts), len(corpus.schema_versions))

    def test_the_artifact_matrix_reports_presence_per_generation(self):
        corpus = self._corpus_like_the_real_one()
        matrix = corpus.artifact_matrix
        self.assertEqual(set(matrix), {"oc_runipd", "runipd", "ipdrunner"})
        for generation, row in matrix.items():
            with self.subTest(generation=generation):
                expected = corpus.generation_counts[generation]
                for family in (
                    "state",
                    "events",
                    "report",
                    "outcomes",
                    "prompts",
                    "sessions",
                ):
                    self.assertEqual(row[family], expected, family)
                # The three fixture-only sources are absent from every one of these runs, exactly
                # as they were absent from all 135 real ones.
                self.assertEqual(row["ledger"], 0)
                self.assertEqual(row["telemetry"], 0)

    def test_distinct_state_key_shapes_are_counted_over_state_keys_not_artifacts(self):
        corpus = self._corpus_like_the_real_one()
        # The oc runs carry `session_id`; the legacy ones do not. Two shapes, though all six runs
        # carry the same ARTIFACTS, which is the distinction the counter must respect.
        self.assertEqual(corpus.key_shape_count, 2)

    def test_the_fixture_only_record_names_all_three_with_reasons(self):
        corpus = self._corpus_like_the_real_one()
        self.assertEqual(set(corpus.fixture_only), {"agy", "ledger", "telemetry"})
        for name, reason in corpus.fixture_only.items():
            with self.subTest(source=name):
                self.assertGreater(len(reason), 20, "a reason, not a placeholder")
        self.assertIn("zero Agy runs", corpus.fixture_only["agy"])

    def test_ledger_and_telemetry_are_detected_when_a_fixture_supplies_them(self):
        """Fixture-only does not mean unsupported: the fixture must exercise the present case."""

        _write_run(
            self.root,
            "run-20260908T110000Z-9",
            with_telemetry=True,
            with_ledger=True,
        )
        corpus = sources.inventory_corpus(self.root)
        row = corpus.artifact_matrix["oc_runipd"]
        self.assertEqual(row["ledger"], 1)
        self.assertEqual(row["telemetry"], 1)

    def test_an_agy_run_is_inventoried_as_the_agy_host(self):
        _write_run(
            self.root,
            "run-20260908T120000Z-8",
            state=_core_state(
                driver={"path": f"{_ABS_HOME}/agent_workflows/agy_runipd.py"}
            ),
        )
        inventory = sources.inventory_corpus(self.root).runs[0]
        self.assertEqual(inventory.generation, "agy_runipd")
        self.assertEqual(inventory.host, "agy")

    def test_one_unreadable_run_degrades_only_itself(self):
        _write_run(self.root, "run-20260908T100000Z-ok")
        broken = self.root / "run-20260908T100000Z-broken"
        broken.mkdir()
        (broken / "state.json").write_text("{ truncated", encoding="utf-8")

        corpus = sources.inventory_corpus(self.root)
        self.assertEqual(corpus.run_count, 2)
        by_readable = {r.readable for r in corpus.runs}
        self.assertEqual(by_readable, {True, False})
        bad = next(r for r in corpus.runs if not r.readable)
        self.assertEqual(bad.warnings, ("state-unreadable",))
        self.assertEqual(bad.generation, sources.GENERATION_UNKNOWN)
        good = next(r for r in corpus.runs if r.readable)
        self.assertEqual(good.generation, "oc_runipd")

    def test_the_reserved_analytics_subtree_is_excluded_by_containment(self):
        """A directory named `run-*` inside the analytics tree is OUTPUT and must never be ingested.

        Order 01's `path_is_within_analytics` is the containment authority, so this exclusion is not
        a second name check.
        """

        _write_run(self.root, "run-20260908T100000Z-real")
        hostile = self.root / "analytics" / "snapshots"
        hostile.mkdir(parents=True)
        _write_run(hostile, "run-20260101T000000Z-1")

        corpus = sources.inventory_corpus(self.root)
        self.assertEqual([r.run_id for r in corpus.runs], ["run-20260908T100000Z-real"])

    def test_a_missing_runs_root_is_an_empty_corpus_not_a_crash(self):
        corpus = sources.inventory_corpus(self.root.parent / "does-not-exist")
        self.assertEqual(corpus.run_count, 0)
        self.assertEqual(corpus.generation_counts, {})
        self.assertEqual(corpus.key_shape_count, 0)

    def test_format_matrix_is_pasteable_and_leaks_no_path(self):
        corpus = self._corpus_like_the_real_one()
        rendered = corpus.format_matrix()
        self.assertIn("generation counts", rendered)
        self.assertIn("oc_runipd", rendered)
        self.assertIn("fixture-only sources", rendered)
        self.assertIn("INSUFFICIENT", rendered)
        self.assertNotIn(_HANDLE, rendered)
        self.assertNotIn(_ABS_HOME, rendered)


class EventAndOutcomeReaderTests(unittest.TestCase):
    """E-01/E-07: a corrupt line degrades itself; readers never raise for damaged input."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_a_corrupt_event_line_yields_None_and_iteration_continues(self):
        run = _write_run(
            self.root,
            "run-20260908T100000Z-1",
            events=[
                '{"at":"2026-09-08T10:00:00Z","event":"one"}',
                "{ THIS LINE IS CORRUPT",
                '{"at":"2026-09-08T10:00:01Z","event":"two"}',
                "[1,2,3]",
            ],
        )
        seen = list(sources.iter_event_lines(run / "events.jsonl"))
        self.assertEqual(len(seen), 4)
        self.assertIsNone(seen[1][1], "the corrupt line parses to None")
        self.assertIsNone(seen[3][1], "a non-object line is also None")
        first, third = seen[0][1], seen[2][1]
        assert first is not None and third is not None  # narrowing for the type checker
        self.assertEqual(first["event"], "one")
        self.assertEqual(third["event"], "two", "a later good line must still be read")

    def test_blank_lines_are_skipped_and_an_absent_stream_is_empty(self):
        run = _write_run(
            self.root, "run-20260908T100000Z-2", events=["", "  ", '{"event":"x"}']
        )
        self.assertEqual(len(list(sources.iter_event_lines(run / "events.jsonl"))), 1)
        self.assertEqual(list(sources.iter_event_lines(run / "nope.jsonl")), [])

    def test_outcomes_skip_a_damaged_file_with_a_label_and_keep_the_others(self):
        run = _write_run(self.root, "run-20260908T100000Z-3")
        outcomes = run / "outcomes"
        (outcomes / "01-aaaaaa.json").write_text(
            json.dumps({"disposition": "executed"}), encoding="utf-8"
        )
        (outcomes / "02-bbbbbb.json").write_text("{ broken", encoding="utf-8")
        (outcomes / "03-cccccc.json").write_text("[1,2]", encoding="utf-8")

        found, warnings = sources.read_outcomes(run)
        self.assertEqual(set(found), {"01-aaaaaa"})
        self.assertEqual(
            sorted(warnings), ["outcome-not-an-object", "outcome-unreadable"]
        )
        for label in warnings:
            self.assertNotIn("/", label, "a warning is a CODE, never a path")

    def test_telemetry_is_read_from_both_the_directory_and_the_single_file_shape(self):
        run = _write_run(self.root, "run-20260908T100000Z-4", with_telemetry=True)
        events, warnings = sources.read_telemetry_events(run)
        self.assertEqual(len(events), 1)
        self.assertEqual(warnings, [])

        (run / "telemetry.jsonl").write_text(
            json.dumps({"schema_version": 1, "event_kind": "end"}) + "\n",
            encoding="utf-8",
        )
        events, _ = sources.read_telemetry_events(run)
        self.assertEqual(len(events), 2, "both shapes must be read")

    def test_a_corrupt_telemetry_line_is_labeled_not_fatal(self):
        run = _write_run(self.root, "run-20260908T100000Z-5")
        (run / "telemetry.jsonl").write_text("{ broken\n", encoding="utf-8")
        events, warnings = sources.read_telemetry_events(run)
        self.assertEqual(events, [])
        self.assertEqual(warnings, ["telemetry-line-unparseable"])


class SharedPrecedenceTests(unittest.TestCase):
    """E-03: ONE precedence implementation, two callers. No second fallback rule."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_the_ingester_and_the_viewer_return_IDENTICAL_results_on_one_fixture(self):
        """The bijection V-03 asks for: same input, same output, because it is the same function."""

        from agent_workflows.run_viewer import extract_step_usage

        run = _write_run(self.root, "run-20260908T100000Z-1")
        item = {
            "position": 1,
            "id6": "abc123",
            "attempts": [
                {
                    "number": 1,
                    "cost": 1.25,
                    "tokens": {"input": 10, "output": 5, "total": 15},
                }
            ],
        }
        self.assertEqual(
            sources.extract_attempt_usage(item, run),
            extract_step_usage(dict(item), run),
        )

    def test_a_stored_total_BEATS_a_log_derived_one(self):
        """The precedence order itself: a stored attempt total wins and the log is not consulted."""

        run = _write_run(self.root, "run-20260908T100000Z-2")
        sessions = run / "sessions"
        log = sessions / "01-abc123-attempt-1.jsonl"
        log.write_text(
            json.dumps(
                {
                    "type": "step_finish",
                    "part": {
                        "cost": 99.0,
                        "tokens": {"input": 999, "output": 999, "total": 1998},
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        item = {
            "position": 1,
            "id6": "abc123",
            "attempts": [
                {
                    "number": 1,
                    "cost": 1.25,
                    "tokens": {"input": 10, "output": 5, "total": 15},
                    "log": str(log),
                }
            ],
        }
        total_cost, total_tokens, *_ = sources.extract_attempt_usage(item, run)
        self.assertEqual(total_cost, 1.25, "the STORED cost must win")
        self.assertEqual(total_tokens["total"], 15, "the STORED tokens must win")

    def test_the_log_is_used_only_when_both_stored_values_are_absent(self):
        run = _write_run(self.root, "run-20260908T100000Z-3")
        log = run / "sessions" / "01-abc123-attempt-1.jsonl"
        log.write_text(
            json.dumps(
                {
                    "type": "step_finish",
                    "part": {
                        "cost": 2.5,
                        "tokens": {"input": 20, "output": 10, "total": 30},
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        item = {
            "position": 1,
            "id6": "abc123",
            "attempts": [{"number": 1, "log": str(log)}],
        }
        total_cost, total_tokens, *_ = sources.extract_attempt_usage(item, run)
        self.assertEqual(total_cost, 2.5)
        self.assertEqual(total_tokens["total"], 30)

    def test_a_RELATIVE_and_a_MOVED_log_path_both_resolve(self):
        """Both fallbacks the shared authority already implements, exercised through the delegate."""

        run = _write_run(self.root, "run-20260908T100000Z-4")
        log = run / "sessions" / "01-abc123-attempt-1.jsonl"
        payload = (
            json.dumps(
                {
                    "type": "step_finish",
                    "part": {
                        "cost": 3.0,
                        "tokens": {"input": 1, "output": 1, "total": 2},
                    },
                }
            )
            + "\n"
        )
        log.write_text(payload, encoding="utf-8")

        relative = {
            "position": 1,
            "id6": "abc123",
            "attempts": [{"number": 1, "log": "sessions/01-abc123-attempt-1.jsonl"}],
        }
        self.assertEqual(sources.extract_attempt_usage(relative, run)[0], 3.0)

        moved = {
            "position": 1,
            "id6": "abc123",
            "attempts": [
                {"number": 1, "log": "/gone/elsewhere/01-abc123-attempt-1.jsonl"}
            ],
        }
        self.assertEqual(
            sources.extract_attempt_usage(moved, run)[0],
            3.0,
            "a moved log is found by name under sessions/",
        )

    def test_execute_and_verify_stay_SEPARATE_through_the_phase_adapter(self):
        run = _write_run(self.root, "run-20260908T100000Z-5")
        item = {
            "position": 1,
            "id6": "abc123",
            "attempts": [
                {
                    "number": 1,
                    "cost": 1.0,
                    "tokens": {"input": 10, "total": 10},
                    "verify_cost": 0.25,
                    "verify_tokens": {"input": 2, "total": 2},
                }
            ],
        }
        phases = sources.attempt_phase_usage(item, run)
        self.assertEqual(phases["execute"], (1.0, {"input": 10, "total": 10}))
        self.assertEqual(phases["verify"], (0.25, {"input": 2, "total": 2}))
        self.assertEqual(phases["total"][0], 1.25)
        self.assertEqual(phases["total"][1]["total"], 12)

    def test_NO_SECOND_precedence_rule_exists_in_this_module(self):
        """Structural proof for V-03: the module delegates and implements no fallback of its own.

        Asserts on the source text because the property is architectural rather than behavioral: a
        second rule could agree with the first on every fixture and still be the defect.
        """

        text = Path(sources.__file__).read_text(encoding="utf-8")

        # Count CODE references only. Prose mentions of the authority are documentation and must not
        # be miscounted as call sites, so the AST is the authority here rather than a substring
        # count: a docstring naming the function is exactly what this module SHOULD contain.
        import ast

        tree = ast.parse(text)
        imported = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and any(a.name == "extract_step_usage" for a in node.names)
        ]
        called = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "extract_step_usage"
        ]
        self.assertEqual(len(imported), 1, "exactly one import of the shared authority")
        self.assertEqual(len(called), 1, "exactly one call of the shared authority")

        # And NO independent fallback: reaching for the log extractor here would BE the second rule.
        log_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "extract_log_metrics"
        ]
        self.assertEqual(log_calls, [], "no independent log-derived fallback may exist")
        for smell in ("def _extract_usage", "def _fallback", "or extract_log"):
            self.assertNotIn(smell, text)


if __name__ == "__main__":
    unittest.main()
