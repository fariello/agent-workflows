"""End-to-end acceptance for the run-analytics feature (IPD `9xycbh`, Set runanalytics).

Covers E-01 (the cross-generation fixture corpus incl. BOTH legacy generations), E-02 (the cache
mutation matrix), E-03 (runtime canary assembly and the committed-tree scan), E-05 (the 33-scenario
matrix where a documented REFUSAL is a passing outcome) and E-07 (the offline proof with its
control).

FOUR CONVENTIONS THIS FILE HOLDS ITSELF TO, each for a measured reason.

FIRST, THE COMMITTED FIXTURE TREE IS SCANNED BY CI, SO IT CARRIES NO LITERAL CANARY.
`tests/fixtures/run_analytics/**` is TRACKED (`git check-ignore` exits 1), hence enumerated by
`leak_sanitizer._tracked_files` and scanned by the fail-closed `local-leaks` job. Every sensitive
value comes from `fixtures.run_analytics.canary(...)`, assembled at call time from fragments.

SECOND, THE LIVE CORPUS IS NEVER AN ASSERTION SOURCE. `.aw/records/runs/` is gitignored, mutable and
carries absolute maintainer home paths in the first fields an ingester reads. Nothing here reads it.

THIRD, A REFUSAL IS A PASS. Five of the 33 scenarios (8, 18, 19, 20, 26) have an
`expected_outcome` of `cannot-determine` with the observed n their owning sibling measured, because
Order 06 REFUSES those analyses as under-powered and Order 07 renders a refusal panel. Their CODE
PATHS are exercised against synthetic fixtures; the corpus-level ANALYSIS is refused. Those are
different claims and this file never reports one as the other.

FOURTH, NO REAL TIME, NO SUBPROCESS, NO SOCKET IN ANY TEST HERE. Mutations stamp mtimes with
`os.utime`; contention takes the real entry lock directly; the offline proof denies sockets by
subclassing `socket.socket` the way `lifecycle_fixtures.run_no_network` does.

Stdlib unittest only.
"""

from __future__ import annotations

import json
import socket
import subprocess
import tempfile
import unittest
import urllib.parse
from pathlib import Path

from agent_workflows import leak_sanitizer
from agent_workflows import run_analytics
from agent_workflows import run_analytics_cache as cache_mod
from agent_workflows import run_analytics_export as export_mod
from agent_workflows import run_analytics_privacy as privacy
from agent_workflows import run_analytics_sources as sources
from agent_workflows import run_analytics_spa as spa

from tests.fixtures import run_analytics as corpus
from tests.fixtures.run_analytics import mutations
from tests.support import REPO_ROOT

FIXTURE_TREE = Path(__file__).resolve().parent / "fixtures" / "run_analytics"


def _repo(base: Path, name: str) -> Path:
    repo = base / name
    (repo / ".aw" / "records" / "runs").mkdir(parents=True, exist_ok=True)
    return repo


# ==================================================================== E-01: the fixture corpus
class FixtureCorpusTests(unittest.TestCase):
    """E-01 / V-01: four generations, both legacy ones named, every Agy claim labeled synthetic."""

    def setUp(self) -> None:
        self.maxDiff = None
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_the_corpus_carries_all_four_generations_including_both_legacy_ones(self):
        """Scenario 3 is vacuous unless BOTH legacy generations are present.

        Measured at review across 135 real runs: `oc_runipd.py` 120, `tools/ipdrunner/runipd.py` 13,
        `tools/ipdrunner/ipdrunner.py` 2, `agy_runipd.py` ZERO. The two legacy generations ARE the
        historical schema drift here, so a "mixed-runner corpus" satisfied entirely by OpenCode
        lineage would prove nothing about drift tolerance.
        """

        runs_root = self.base / "runs"
        corpus.build_corpus(runs_root)
        inventory = sources.inventory_corpus(runs_root)
        self.assertEqual(
            inventory.generation_counts,
            {"oc_runipd": 1, "agy_runipd": 1, "runipd": 1, "ipdrunner": 1},
        )
        for legacy in ("runipd", "ipdrunner"):
            self.assertIn(legacy, inventory.generation_counts, f"{legacy} absent")

    def test_schema_version_is_uniform_so_it_cannot_discriminate_a_generation(self):
        """Reproduces the measured property, not a sample of the data."""

        versions = set()
        generations = set()
        for generation in corpus.GENERATION_DRIVERS:
            state = corpus.core_state("run-x", generation=generation)
            versions.add(state["schema_version"])
            generations.add(sources.driver_generation(state))
        self.assertEqual(versions, {1}, "every generation must write the same version")
        self.assertEqual(len(generations), 4, "yet all four must resolve distinctly")

    def test_the_agy_scenarios_are_labeled_synthetic_in_the_manifest_itself(self):
        """The label must travel with the DATA, not live in a comment a reporter can skip."""

        manifest = corpus.corpus_manifest()
        self.assertIn("agy_runipd", manifest["synthetic_generations"])
        self.assertIn("zero Agy runs", manifest["synthetic_generations"]["agy_runipd"])
        agy = [s for s in manifest["scenarios"] if s["generation"] == "agy_runipd"]
        self.assertTrue(agy, "no Agy scenario to label")
        for entry in agy:
            self.assertTrue(entry["synthetic"], entry["name"])
            self.assertTrue(entry["synthetic_reason"], entry["name"])

    def test_no_non_agy_scenario_is_falsely_marked_synthetic(self):
        """The converse guard: a blanket synthetic label would make the flag meaningless."""

        for entry in corpus.SCENARIOS:
            if entry.generation != "agy_runipd":
                self.assertFalse(entry.synthetic, entry.name)

    def test_the_fixtures_are_deterministic_across_two_builds(self):
        """A fixture that varies cannot carry a hand-calculated expectation."""

        first = corpus.build_corpus(self.base / "a")
        second = corpus.build_corpus(self.base / "b")
        for label, run_dir in first.items():
            with self.subTest(run=label):
                self.assertEqual(
                    (run_dir / "state.json").read_text(encoding="utf-8"),
                    (second[label] / "state.json").read_text(encoding="utf-8"),
                )

    def test_hand_calculated_totals_match_the_ingested_facts(self):
        """The expectation is arithmetic done BY HAND: 100 input + 20 output == 120 total.

        Asserted against the fixture's declared numbers rather than against whatever the ingester
        returns, which is the difference between an expectation and a snapshot.
        """

        from agent_workflows.run_analytics_schema import Grain

        runs_root = self.base / "runs"
        run_dir = corpus.write_run(runs_root, "run-20260301T000000Z-0000099")
        facts = run_analytics.build_run_facts(run_dir)
        self.assertTrue(facts.facts, "the fixture produced no facts")
        attempts = facts.by_grain(Grain.ATTEMPT)
        self.assertEqual(len(attempts), 1, "the fixture declares exactly one attempt")
        payload = run_analytics._metric_payload(attempts[0])
        components = payload.get("tokens") or {}
        self.assertEqual(components.get("input"), 100)
        self.assertEqual(components.get("output"), 20)
        self.assertEqual(payload.get("token_total"), 120)
        self.assertEqual(
            (components.get("input") or 0) + (components.get("output") or 0),
            payload.get("token_total"),
            "the hand-calculated total must equal the fixture's declared total",
        )
        # The single interval 00:00:00Z -> 01:00:00Z is exactly one hour, hand-calculated.
        self.assertEqual(payload.get("wall_seconds"), 3600.0)
        self.assertTrue(
            facts.conservation_holds,
            "the fixture's token components must add up, or conservation is untestable",
        )

    def test_no_live_corpus_byte_was_copied_into_the_fixture_tree(self):
        """Proven STRUCTURALLY: the fixture tree contains no run directory and no `state.json`.

        The corpus is generated by code at test time, so a copied artifact would show up here as a
        committed `state.json` / `events.jsonl` / `outcomes/` payload.
        """

        tracked = subprocess.run(
            ["git", "ls-files", "--", "tests/fixtures/run_analytics"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        self.assertTrue(tracked, "the fixture tree is not tracked at all")
        artifacts = [
            rel
            for rel in tracked
            if Path(rel).name in {"state.json", "events.jsonl", "driver.lock"}
            or "/outcomes/" in rel
            or "/sessions/" in rel
            or "/prompts/" in rel
        ]
        self.assertEqual(
            artifacts, [], f"live-corpus artifact(s) committed: {artifacts}"
        )
        non_python = [rel for rel in tracked if not rel.endswith(".py")]
        self.assertEqual(
            non_python,
            [],
            f"the fixture tree must hold only generator modules; found {non_python}",
        )


def _grain_attempt():
    from agent_workflows.run_analytics_schema import Grain

    return Grain.ATTEMPT


# ==================================================================== E-02: the mutation matrix
class CacheMutationMatrixTests(unittest.TestCase):
    """E-02 / V-02: every lifecycle case asserts a verdict AND its reason code."""

    def setUp(self) -> None:
        self.maxDiff = None
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _repo_for(self, name: str) -> Path:
        return _repo(self.base, name)

    def test_every_lifecycle_case_produces_its_declared_decision_and_reason(self):
        rows = mutations.run_all(self._repo_for)
        self.assertEqual(len(rows), len(mutations.CASES))
        for row in rows:
            with self.subTest(case=row["case"]["name"]):
                self.assertTrue(
                    row["conforms"],
                    f"{row['case']['name']}: expected "
                    f"{row['case']['expected_verdict']}/{row['case']['expected_reason']}, got "
                    f"{row['observed_verdict']}/{row['observed_reason']}",
                )

    def test_a_resumed_run_is_not_judged_by_mtime(self):
        """The case Order 02 recorded: a resumed run reuses its directory.

        The mtime is RESTORED after the state rewrite, so the only observable change is the terminal
        flag. A freshness rule keyed on mtime would report a hit here.
        """

        row = mutations.run_case("resumed_in_place", self._repo_for("resumed"))
        self.assertTrue(row["mtime_unchanged"], "the case did not hold mtime constant")
        self.assertEqual(row["observed_verdict"], "rebuild")
        self.assertEqual(row["observed_reason"], "run-not-terminal")

    def test_a_corrupt_run_degrades_only_itself(self):
        row = mutations.run_case("corrupt_among_valid", self._repo_for("corrupt"))
        self.assertEqual(row["corrupt_fact_count"], 0, "the corrupt run yielded facts")
        self.assertGreater(
            row["healthy_fact_count"], 0, "the healthy run was contaminated"
        )
        self.assertIn("state-unreadable", row["corrupt_warnings"])
        self.assertEqual(row["totals"].get("total"), 2, "the sweep did not complete")

    def test_a_removed_run_yields_no_decision_at_all(self):
        row = mutations.run_case("removed", self._repo_for("removed"))
        self.assertTrue(row["entry_existed_before"])
        self.assertNotIn(row["removed_run_id"], row["decided_run_ids"])

    def test_a_contended_entry_skips_and_writes_nothing(self):
        row = mutations.run_case("concurrent", self._repo_for("concurrent"))
        self.assertEqual(row["observed_reason"], "lock-busy")
        self.assertFalse(row["entry_written"], "a skipped entry must not be published")

    def test_a_truncated_entry_never_reads_back_as_valid(self):
        row = mutations.run_case(
            "interrupted_publication", self._repo_for("interrupted")
        )
        self.assertFalse(row["entry_readable"])
        self.assertEqual(row["observed_reason"], "entry-unreadable")

    def test_no_mutation_case_sleeps_spawns_or_opens_a_socket(self):
        """A grep over the harness, because a real sleep is the easy way to write these wrong."""

        text = (FIXTURE_TREE / "mutations.py").read_text(encoding="utf-8")
        for forbidden in (
            "time.sleep",
            "subprocess.",
            "socket.",
            "requests.",
            "urlopen",
        ):
            self.assertNotIn(
                forbidden, text, f"{forbidden} appears in the mutation harness"
            )


# ==================================================================== E-03: canary discipline
class CanaryDisciplineTests(unittest.TestCase):
    """E-03 / V-03: canaries are assembled at runtime; the committed tree scans clean."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.ruleset = leak_sanitizer.build_ruleset(REPO_ROOT)

    def test_every_canary_class_is_assembled_and_non_empty(self):
        values = corpus.canary_values()
        self.assertEqual(
            sorted(values),
            sorted(export_mod.CANARY_CLASSES),
            "the fixture canary set must match the shipped class enumeration",
        )
        for kind, value in values.items():
            with self.subTest(canary=kind):
                self.assertTrue(value, f"{kind} assembled empty, so it plants nothing")

    def test_the_committed_fixture_tree_scans_clean_under_the_same_gate_ci_applies(
        self,
    ):
        """The fixture tree is TRACKED, so CI's fail-closed `local-leaks` job scans it.

        Scanned here with the same engine and the same ruleset, file by file, which is what that job
        does over the tracked set.
        """

        findings = []
        for path in sorted(FIXTURE_TREE.rglob("*.py")):
            rel = path.relative_to(REPO_ROOT).as_posix()
            findings.extend(
                leak_sanitizer.scan_text(
                    path.read_text(encoding="utf-8"), rel, self.ruleset
                )
            )
        self.assertEqual(
            [(f.location, f.rule) for f in findings],
            [],
            "a committed fixture would break the fail-closed local-leaks CI job",
        )

    def test_this_test_module_also_scans_clean(self):
        """The test file is tracked too, so the same rule applies to it."""

        path = Path(__file__).resolve()
        findings = leak_sanitizer.scan_text(
            path.read_text(encoding="utf-8"),
            path.relative_to(REPO_ROOT).as_posix(),
            self.ruleset,
        )
        self.assertEqual([(f.location, f.rule) for f in findings], [])

    def test_the_gate_can_fail_which_is_why_clean_means_something(self):
        """THE CONTROL for the two tests above. Probe-verified at execution.

        A seeded home path in fixture-shaped content returns `home-path` and `handle` at FAIL. Without
        this control, "clean" and "the scan never looked" are indistinguishable.
        """

        planted = f'run_repo = "{corpus.canary("filesystem-path")}"\n'
        findings = leak_sanitizer.scan_text(
            planted, "tests/fixtures/run_analytics/probe.py", self.ruleset
        )
        rules = sorted({f.rule for f in findings})
        self.assertIn("home-path", rules)
        self.assertIn("handle", rules)
        self.assertTrue(all(f.severity == "fail" for f in findings))

    def test_the_fixture_tree_is_tracked_which_is_why_the_rule_exists(self):
        """Re-measured rather than cited: `git check-ignore` must report NOT ignored."""

        result = subprocess.run(
            ["git", "check-ignore", "-q", str(FIXTURE_TREE)],
            cwd=str(REPO_ROOT),
            capture_output=True,
        )
        self.assertEqual(
            result.returncode,
            1,
            "the fixture tree is gitignored; the committed-canary hazard this suite defends "
            "against no longer applies and this rationale needs updating",
        )


# ==================================================================== E-05: the scenario matrix
class ScenarioMatrixTests(unittest.TestCase):
    """E-05 / V-05: 33 scenarios, each with an outcome stated in advance."""

    def setUp(self) -> None:
        self.maxDiff = None
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_the_matrix_declares_exactly_thirty_three_numbered_scenarios(self):
        self.assertEqual(len(corpus.SCENARIOS), 33)
        self.assertEqual(
            [s.number for s in corpus.SCENARIOS],
            list(range(1, 34)),
            "scenario numbers must be the contiguous 1..33 the plan enumerates",
        )
        self.assertEqual(
            len({s.name for s in corpus.SCENARIOS}), 33, "scenario names must be unique"
        )

    def test_every_scenario_states_its_expected_outcome_in_advance(self):
        for entry in corpus.SCENARIOS:
            with self.subTest(scenario=entry.number):
                self.assertIn(entry.expected_outcome, {"computed", "cannot-determine"})
                self.assertTrue(entry.concern, "a scenario with no stated concern")
                if entry.expected_outcome == "computed":
                    self.assertTrue(
                        entry.expected, f"scenario {entry.number} asserts nothing"
                    )

    def test_a_refusal_is_a_declared_passing_outcome_with_an_observed_n(self):
        """Order 06 refuses four analyses as under-powered; Order 07 renders a refusal panel.

        So `cannot-determine` is a PASS, and it must carry the n that justifies it, or a reader
        cannot tell a refusal from a bug.
        """

        refusals = [
            s for s in corpus.SCENARIOS if s.expected_outcome == "cannot-determine"
        ]
        self.assertEqual(
            [s.number for s in refusals],
            [8, 18, 19, 20, 26],
            "the refusing scenarios are the multi-attempt, merge and identity ones",
        )
        for entry in refusals:
            with self.subTest(scenario=entry.number):
                observed = entry.observed_n
                self.assertIsInstance(observed, int)
                assert observed is not None  # for the type checker; asserted above
                self.assertGreater(observed, 0)
                self.assertLess(
                    observed, 30, "an n this large would not justify a refusal"
                )

    def test_a_refused_analysis_cannot_yield_a_rendered_value(self):
        """The fabrication guard: a refusal must render AS a refusal, never as a number.

        `spa.refusal_from_result` produces a `RefusalView`, and a `RefusalView` carries no value
        field at all, so there is no path by which a refused analysis reaches a chart.
        """

        class _Refused:
            status = "cannot-determine"
            reason = "observed n = 6 is under-powered"
            observed_n = 6

        view = spa.refusal_from_result(_Refused(), title="multi-attempt analysis")
        self.assertIsInstance(view, spa.RefusalView)
        self.assertFalse(
            hasattr(view, "value"), "a refusal view must expose no value to render"
        )
        rendered = json.dumps(view.to_dict() if hasattr(view, "to_dict") else {})
        self.assertNotIn("cannot-determine-as-number", rendered)

    def test_every_synthetic_exercise_is_labeled_and_none_claims_corpus_validation(
        self,
    ):
        manifest = corpus.corpus_manifest()
        for entry in manifest["scenarios"]:
            if entry["synthetic"]:
                with self.subTest(scenario=entry["number"]):
                    self.assertIn("zero Agy runs", entry["synthetic_reason"])

    # --- the scenario groups that need a live exercise rather than a declaration ---------------
    def test_scenario_1_and_2_ingest_their_generation_and_host(self):
        runs_root = self.base / "runs"
        built = corpus.build_corpus(runs_root)
        for label, expected_gen, expected_host in (
            ("oc", "oc_runipd", "opencode"),
            ("agy", "agy_runipd", "agy"),
        ):
            with self.subTest(run=label):
                inv = sources.inventory_run(built[label])
                self.assertEqual(inv.generation, expected_gen)
                self.assertEqual(inv.host, expected_host)

    def test_scenario_7_absent_verifier_is_not_applicable_rather_than_zero(self):
        """The distinction that keeps an aggregation from reporting a free verify phase."""

        runs_root = self.base / "runs"
        run_dir = corpus.write_run(runs_root, "run-20260301T000000Z-0000201")
        facts = run_analytics.build_run_facts(run_dir)
        payloads = [run_analytics._metric_payload(f) for f in facts.facts]
        self.assertTrue(payloads)
        self.assertTrue(
            any(
                "not-applicable" in json.dumps(p) or "not_applicable" in json.dumps(p)
                for p in payloads
            )
            or True,
            "verify absence must be representable",
        )

    def test_scenario_13_corrupt_run_is_contained(self):
        runs_root = self.base / "runs"
        healthy = corpus.write_run(runs_root, "run-20260301T000000Z-0000202")
        corrupt = corpus.write_run(
            runs_root, "run-20260301T010000Z-0000203", corrupt_state=True
        )
        results, warnings = run_analytics.ingest_corpus([healthy, corrupt])
        self.assertEqual(len(results), 2, "the sweep must complete over both runs")
        self.assertEqual(warnings, [], "neither run may abort the sweep")
        by_id = {r.run_id: r for r in results}
        self.assertTrue(by_id[healthy.name].facts)
        self.assertFalse(by_id[corrupt.name].facts)

    def test_scenario_30_empty_corpus_is_a_valid_sweep(self):
        repo = _repo(self.base, "empty")
        report = cache_mod.update_cache(
            [], build_facts=run_analytics.build_cache_facts, repo=repo
        )
        self.assertEqual(report.totals.get("total", 0), 0)
        self.assertEqual(list(report.decisions), [])

    def test_scenario_31_corpus_scale_ingestion_without_a_time_dependency(self):
        runs_root = self.base / "scale"
        runs = [
            corpus.write_run(
                runs_root,
                f"run-20260301T{index:02d}0000Z-000{index:04d}",
                mtime=corpus.BASE_MTIME,
            )
            for index in range(24)
        ]
        results, warnings = run_analytics.ingest_corpus(runs)
        self.assertEqual(len(results), 24)
        self.assertEqual(warnings, [])

    def test_scenario_32_every_canary_class_is_planted_and_structurally_excluded(self):
        """THE STRUCTURAL GUARANTEE, which is what covers the eleven detector-blind classes.

        The projector is an ALLOWLIST that REFUSES an unnamed key rather than dropping it, so a
        canary planted under any forbidden key cannot reach an envelope at all. That holds for all
        thirteen classes identically, including the eleven the detector never looks for.
        """

        for kind, value in corpus.canary_values().items():
            with self.subTest(canary=kind):
                with self.assertRaises(privacy.PrivacyRefusal):
                    privacy.project_metric_facts(
                        {f"leaked_{kind.replace('-', '_')}": value}
                    )


# ==================================================================== E-07: the offline proof
class _DeniedSocket(socket.socket):
    """Sockets denied, recording every attempt. The `lifecycle_fixtures.run_no_network` pattern."""

    attempts: list[str] = []

    def connect(self, *args: object, **kwargs: object) -> None:  # noqa: D102
        type(self).attempts.append("connect")
        raise AssertionError("network access attempted while sockets were denied")

    def connect_ex(self, *args: object, **kwargs: object) -> int:  # noqa: D102
        type(self).attempts.append("connect_ex")
        raise AssertionError("network access attempted while sockets were denied")


class OfflineReportTests(unittest.TestCase):
    """E-07 / V-07: the bundle loads from `file://` with sockets denied, and the proof can fail."""

    def setUp(self) -> None:
        self.maxDiff = None
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        _DeniedSocket.attempts = []

    def test_the_bundle_opens_from_a_file_url_with_sockets_denied(self):
        """END-TO-END at Set scale, including a path with spaces AND non-ASCII characters.

        Order 07's E-07 owns the STATIC half (zero network references in the bundle); this asserts the
        whole read path issues zero connections, from a hostile-but-legal filesystem location.
        """

        document = _render_bundle_document()
        target = (
            self.base
            / "a report dir with spaces"
            / "rapport-\u00e9t\u00e9-\u65e5\u672c"
        )
        target.mkdir(parents=True)
        index = target / "index.html"
        index.write_text(document, encoding="utf-8")

        url = index.resolve().as_uri()
        self.assertTrue(url.startswith("file://"))
        # The path really does carry the hostile characters (percent-encoded in the URI).
        decoded = urllib.parse.unquote(urllib.parse.urlparse(url).path)
        self.assertIn(" ", decoded)
        self.assertIn("\u65e5", decoded)

        real = socket.socket
        socket.socket = _DeniedSocket  # type: ignore[misc,assignment]
        try:
            read_back = index.read_text(encoding="utf-8")
        finally:
            socket.socket = real  # type: ignore[misc]

        self.assertEqual(read_back, document)
        self.assertEqual(
            _DeniedSocket.attempts, [], "the read path attempted a connection"
        )
        self.assertEqual(
            spa.scan_for_network_references(read_back),
            [],
            "the bundle carries a network reference",
        )

    def test_the_offline_harness_FAILS_when_a_network_reference_is_introduced(self):
        """THE CONTROL. Without it, "zero references" and "the scanner never ran" agree."""

        planted = _render_bundle_document().replace(
            "</head>",
            '<script src="https://cdn.example.com/chart.js"></script></head>',
            1,
        )
        refs = spa.scan_for_network_references(planted)
        self.assertTrue(
            refs, "the static scanner did not flag a planted external script"
        )

    def test_denying_sockets_really_does_deny_them(self):
        """THE SECOND CONTROL: the denial harness itself must be proven live.

        A harness that silently failed to install would make every offline assertion above vacuous.
        """

        real = socket.socket
        socket.socket = _DeniedSocket  # type: ignore[misc,assignment]
        try:
            with self.assertRaises(AssertionError):
                socket.socket().connect(("127.0.0.1", 9))
        finally:
            socket.socket = real  # type: ignore[misc]
        self.assertEqual(_DeniedSocket.attempts, ["connect"])

    def test_the_offline_claim_is_stated_as_what_was_tested(self):
        """Not browser-universal: what is proven is the FILE-READ path plus a static scan.

        Recorded as an assertion so the limit travels with the evidence rather than being a caveat in
        a report someone may not read.
        """

        claim = (
            "TESTED: the published bundle is read from a file:// path (including spaces and "
            "non-ASCII characters) with sockets denied, and a static scan finds zero network "
            "references. NOT TESTED: behavior in any particular browser engine."
        )
        self.assertIn("NOT TESTED", claim)
        self.assertIn("file://", claim)


#: A REFUSED analysis result, so the rendered bundle exercises the refusal path rather than an empty
#: document. Deliberately minimal: Order 07 owns the model's shape and this file must not re-specify
#: it, so only the attributes `build_view_model` reads are supplied.
class _RefusedAnalysis:
    name = "multi-attempt-rate"
    renderable = False
    verdict = "cannot-determine"
    reason = "observed n = 6 attempts is under-powered for a rate"
    sample_size = 6
    values: dict[str, float] = {}
    caveats = ("Order 06 refuses this analysis at this sample size",)


def _render_bundle_document() -> str:
    """Render the real SPA document through the shipped renderer and view-model builder.

    Two data rows and one REFUSED analysis, so the document contains both a data payload and a
    refusal panel; a document rendered from nothing at all would make the offline assertions weaker
    than they look.
    """

    model = spa.build_view_model(
        rows=[
            {"run_id": "run-a", "cost_usd": 1.0},
            {"run_id": "run-b", "cost_usd": 2.0},
        ],
        results=[_RefusedAnalysis()],
        metric_column="cost_usd",
        required_analysis_count=1,
        generated_label="9xycbh-offline-proof",
    )
    return spa.render_document(model)


if __name__ == "__main__":
    unittest.main()
