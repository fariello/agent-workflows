"""Tests for cross-host resource telemetry (IPD lhccjf, Set runanalytics, E-01..E-06 and E-08).

WHY THE PRIVACY ASSERTIONS HERE DO NOT REST ON ``aw sanitize``, WHICH IS THE POINT OF THIS SUITE.
Measured on this repository's own detector: :func:`agent_workflows.leak_sanitizer.scan_text` over a
bare hostname returns ZERO findings at default settings. The hostname IS derived as a token but
lands in the ``warn`` tier and is promoted to ``fail`` only when the repo allowlist sets
``hostname_fail = true``, which ships FALSE ("so a shared CI-runner hostname does not fail every
build"); even passing ``include_warn=True`` to both ``build_ruleset`` and ``scan_text`` reports only
``warn``. A username and a home path both return ``fail`` immediately, so the detector's competence
on those two would mask the gap. The hostname is the EXACT field this module exists to suppress, so
a privacy test resting on the sanitizer would PASS while the hostname shipped. Therefore the
load-bearing assertion is DIRECT (the raw hostname string, in all three of its spellings, must not
appear anywhere in the produced JSONL) and the sanitizer scan is CORROBORATING, always paired with a
CONTROL run proving the same invocation flags a seeded username or home path. A clean report and a
detector that was not looking are otherwise indistinguishable.

NO SENSITIVE LITERAL IS COMMITTED IN THIS FILE. Every canary is assembled from fragments at
runtime, the convention the detection engine itself follows for its own patterns. Pasting a
real-shaped canary would make ``aw sanitize --agent`` fail on this very file, which sibling
``bzz5e6``'s review demonstrated by accident.

NO TEST HERE PERFORMS A REAL SUBPROCESS CALL, A REAL SLEEP, OR NETWORK ACCESS, and that is asserted
BY CONSTRUCTION rather than hoped for: the probe layer is reached through an injected adapter, and
the tests that must prove the absence of a subprocess install a stub that RAISES if invoked.

Stdlib unittest only.
"""

from __future__ import annotations

import ast
import json
import re
import socket
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

from agent_workflows import leak_sanitizer as ls
from agent_workflows import run_analytics_config as cfg
from agent_workflows import run_analytics_telemetry as tel
from agent_workflows.runner_shared import append_jsonl
from tests.support import REPO_ROOT

# --- Canaries, assembled from fragments so this file holds no literal leak ----------------------
_HANDLE = "gfa" + "riello"
_HOME_PATH = "/ho" + "me/" + _HANDLE + "/VC/agent-workflows"
_SALT = "a" * 64
_OTHER_SALT = "b" * 64


#: Names that must appear NOWHERE in this module's executable code. Each is a specific prohibition
#: with a named authority, not a style preference:
#:   * ``signal``/``atexit``: spec `c4gd2h` R5 makes cleanup singular and the `runstop` phase owns
#:     SIGINT/SIGTERM registration; `oc_runipd` records a prior plan being refused exactly this.
#:   * ``clean_shutdown``: calling it from here would be a second entry into the one shared routine.
#:   * ``fsync``/``open``: `runner_shared.append_jsonl` is the one writer; a second one would fork
#:     the durability contract.
#:   * ``kill``/``terminate``: this module owns no process policy.
_FORBIDDEN_CODE_IDENTIFIERS = frozenset(
    {
        "signal",
        "atexit",
        "clean_shutdown",
        "runner_shutdown",
        "fsync",
        "kill",
        "terminate",
        "killpg",
        "setitimer",
    }
)


def _code_identifiers(path: Path) -> set[str]:
    """Every NAME and ATTRIBUTE appearing in real code, with docstrings and comments excluded.

    Parsing rather than grepping is the point: this module's docstrings deliberately NAME the very
    things it must not call, in order to explain why it does not call them.
    """

    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif isinstance(node, ast.alias):
            found.add(node.name.split(".")[0])
            if node.asname:
                found.add(node.asname)
    return found


def _imported_modules(path: Path) -> set[str]:
    """Every module this file imports, including inside a function body."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
            for alias in node.names:
                modules.add(f"{node.module}.{alias.name}")
    return modules


def _ruleset(*, include_warn: bool = False) -> ls.Ruleset:
    return ls.build_ruleset(REPO_ROOT, include_warn=include_warn)


def _scan(text: str, *, include_warn: bool = False) -> list[ls.Finding]:
    return ls.scan_text(
        text,
        "telemetry-canary",
        _ruleset(include_warn=include_warn),
        include_warn=include_warn,
    )


class FakeClock:
    """A monotonic clock a test drives by hand, so no test spends real time."""

    def __init__(self, start: float = 1000.0) -> None:
        self.now = float(start)

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += float(seconds)


def _collector(
    tmp: Path,
    *,
    adapter: tel.ResourceProbeAdapter | None = None,
    config: cfg.TelemetryConfig | None = None,
    clock: FakeClock | None = None,
    context: dict | None = None,
    writer=None,
) -> tel.TelemetryCollector:
    return tel.TelemetryCollector(
        tmp / tel.TELEMETRY_FILENAME,
        execution_id="exec-01",
        salt=_SALT,
        config=config if config is not None else cfg.TelemetryConfig(),
        adapter=adapter if adapter is not None else tel.FakeResourceProbeAdapter(),
        monotonic=clock if clock is not None else FakeClock(),
        wall_clock=lambda: 1_760_000_000.0,
        context=context,
        writer=writer,
    )


def _read_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


# ================================================================================================
# E-01 / V-01: the schema
# ================================================================================================
class EventSchemaTests(unittest.TestCase):
    """The allowlist envelope: round trips, and REFUSALS rather than silent drops."""

    def _minimal(self, kind: str = "start") -> dict:
        return {
            "schema_version": tel.TELEMETRY_SCHEMA_VERSION,
            "event_kind": kind,
            "execution_id": "exec-01",
            "wall_timestamp": "2026-09-13T20:00:00Z",
            "monotonic_offset_seconds": 0.0,
        }

    def test_each_event_kind_round_trips(self) -> None:
        for kind in ("start", "sample", "end"):
            with self.subTest(kind=kind):
                event = self._minimal(kind)
                validated = tel.validate_event(event)
                self.assertEqual(validated["event_kind"], kind)
                # A round trip through JSON must be byte-stable and re-validate.
                encoded = json.dumps(validated, sort_keys=True)
                self.assertEqual(tel.validate_event(json.loads(encoded)), validated)

    def test_full_event_with_every_payload_round_trips(self) -> None:
        event = self._minimal("sample")
        event.update(
            {
                "sequence": 3,
                "run_id": "run-20260913T195954Z-867725",
                "ipd_id6": "lhccjf",
                "set_id": "runanalytics",
                "position": 1,
                "attempt": 1,
                "phase": "execute",
                "host": "opencode",
                "provider": "its_direct",
                "model": "its_direct/pt3-claude-opus-5-1m-us",
                "node_id": tel.node_pseudonym(salt=_SALT, raw="node-a"),
                "duration_seconds": 12.5,
                "resources": {"cpu_logical_count": 12, "load_average_1m": 1.25},
                "accelerators": [{"vendor": "nvidia", "memory_total_mib": 8192}],
                "tool_versions": {"python": "3.14.0"},
                "warnings": ["accelerator-timeout"],
                "sample_skipped_count": 2,
                "probe_error_count": 1,
            }
        )
        validated = tel.validate_event(event)
        self.assertEqual(
            tel.validate_event(json.loads(json.dumps(validated))), validated
        )

    def test_unknown_key_is_refused_and_not_silently_dropped(self) -> None:
        event = self._minimal()
        event["hostname"] = "some-host"
        with self.assertRaises(tel.SchemaRefusal) as caught:
            tel.validate_event(event)
        self.assertEqual(caught.exception.key, "hostname")
        self.assertIn("REFUSED rather than dropped", str(caught.exception))

    def test_out_of_vocabulary_event_kind_is_refused(self) -> None:
        for kind in ("heartbeat", "START", "", "middle"):
            with self.subTest(kind=kind):
                with self.assertRaises(tel.SchemaRefusal) as caught:
                    tel.validate_event(self._minimal(kind))
                self.assertEqual(caught.exception.key, "event_kind")
                self.assertIn("CLOSED", str(caught.exception))

    def test_unknown_schema_version_is_refused_before_key_checks(self) -> None:
        event = self._minimal()
        event["schema_version"] = tel.TELEMETRY_SCHEMA_VERSION + 1
        event["a_future_field"] = 1
        with self.assertRaises(tel.SchemaRefusal) as caught:
            tel.validate_event(event)
        self.assertEqual(
            caught.exception.key,
            "schema_version",
            "a future generation gets a version diagnostic, not complaints about its own fields",
        )

    def test_missing_required_field_is_refused(self) -> None:
        for name in tel.REQUIRED_FIELDS:
            with self.subTest(missing=name):
                event = self._minimal()
                event.pop(name)
                with self.assertRaises(tel.SchemaRefusal):
                    tel.validate_event(event)

    def test_nested_observation_objects_have_their_own_allowlists(self) -> None:
        event = self._minimal()
        event["resources"] = {"hostname": "some-host"}
        with self.assertRaises(tel.SchemaRefusal) as caught:
            tel.validate_event(event)
        self.assertEqual(caught.exception.key, "hostname")

        event["resources"] = {"cpu_logical_count": 4}
        event["accelerators"] = [{"serial_number": "GPU-123"}]
        with self.assertRaises(tel.SchemaRefusal):
            tel.validate_event(event)

    def test_a_raw_host_identity_cannot_ride_in_through_node_id(self) -> None:
        event = self._minimal()
        event["node_id"] = socket.gethostname()
        with self.assertRaises(tel.SchemaRefusal) as caught:
            tel.validate_event(event)
        self.assertIn("REFUSED", str(caught.exception))

    def test_free_text_is_refused_in_every_string_carrying_field(self) -> None:
        hostile = [
            ("phase", "executing " + _HOME_PATH),
            ("warnings", ["failed to read " + _HOME_PATH]),
            ("tool_versions", {"python": "Python 3.14.0 at " + _HOME_PATH}),
            ("resources", {"container_hint": _HOME_PATH}),
            ("host", "opencode; rm -rf /"),
        ]
        for key, value in hostile:
            with self.subTest(key=key):
                event = self._minimal()
                event[key] = value
                with self.assertRaises(tel.SchemaRefusal):
                    tel.validate_event(event)

    def test_negative_and_non_finite_numbers_are_refused(self) -> None:
        for key, value in (
            ("monotonic_offset_seconds", -1.0),
            ("duration_seconds", -0.001),
            ("sequence", -1),
            ("monotonic_offset_seconds", float("inf")),
            ("monotonic_offset_seconds", float("nan")),
        ):
            with self.subTest(key=key, value=value):
                event = self._minimal()
                event[key] = value
                with self.assertRaises(tel.SchemaRefusal):
                    tel.validate_event(event)

    def test_docstring_states_the_allowlist_direction(self) -> None:
        doc = tel.__doc__ or ""
        self.assertIn("THE SCHEMA IS AN ALLOWLIST", doc)
        self.assertIn("TEST CORPUS", doc)

    def test_build_event_validates_at_construction(self) -> None:
        built = tel.build_event(
            event_kind="start",
            execution_id="exec-01",
            monotonic_offset_seconds=0.0,
            wall_timestamp="2026-09-13T20:00:00Z",
            phase="execute",
        )
        self.assertEqual(built["phase"], "execute")
        with self.assertRaises(tel.SchemaRefusal):
            tel.build_event(
                event_kind="start",
                execution_id="exec-01",
                monotonic_offset_seconds=0.0,
                wall_timestamp="2026-09-13T20:00:00Z",
                hostname="some-host",
            )


class SchemaMutationTests(unittest.TestCase):
    """A mutation check: make the schema DROP instead of REFUSE, and prove a test notices."""

    def test_dropping_instead_of_refusing_breaks_the_boundary(self) -> None:
        event = {
            "schema_version": tel.TELEMETRY_SCHEMA_VERSION,
            "event_kind": "start",
            "execution_id": "exec-01",
            "wall_timestamp": "2026-09-13T20:00:00Z",
            "monotonic_offset_seconds": 0.0,
            "hostname": "some-host",
        }
        # The real behavior.
        with self.assertRaises(tel.SchemaRefusal):
            tel.validate_event(event)

        # THE MUTANT: disable the key allowlist, so unknown keys are no longer refused there.
        def lenient(payload, allowed, where):  # noqa: ANN001 - test-local stub
            return None

        original = tel._refuse_unknown
        tel._refuse_unknown = lenient
        try:
            # The event is STILL refused, and that is the finding worth recording: the boundary has
            # a SECOND, independent line of defense. `_validate_scalar` refuses a key for which no
            # validation rule exists, so the fail-closed default is "unknown key has no rule,
            # therefore refuse" rather than "unknown key is unvalidated, therefore pass". Defeating
            # the boundary takes disabling BOTH, which is the property a single-check design lacks.
            with self.assertRaises(tel.SchemaRefusal) as caught:
                tel.validate_event(event)
            self.assertIn("has no validation rule", str(caught.exception))

            # Now disable that one too, and the leak appears: the key is silently DROPPED, and a
            # caller cannot tell its record was not persisted whole. This is the behavior the real
            # implementation refuses, so the mutation demonstrates the assertions have teeth.
            original_scalar = tel._validate_scalar
            tel._validate_scalar = lambda key, value: value
            try:
                mutated = tel.validate_event(event)
                self.assertEqual(
                    mutated.get("hostname"),
                    "some-host",
                    "with BOTH checks disabled the forbidden field passes straight through",
                )
            finally:
                tel._validate_scalar = original_scalar
        finally:
            tel._refuse_unknown = original
        # Reverted: the refusal names the allowlist again.
        with self.assertRaises(tel.SchemaRefusal) as restored:
            tel.validate_event(event)
        self.assertIn("REFUSED rather than dropped", str(restored.exception))


# ================================================================================================
# E-02 / V-02: probes
# ================================================================================================
class ProbeAdapterTests(unittest.TestCase):
    """The injectable interface, the real implementation, and the fake."""

    def test_real_adapter_probes_this_machine_without_raising(self) -> None:
        adapter = tel.SystemResourceProbeAdapter()
        for name, outcome in (
            ("cpu", adapter.cpu()),
            ("memory", adapter.memory()),
            ("load", adapter.load()),
            ("process", adapter.process()),
            ("tool_versions", adapter.tool_versions()),
            ("disk", adapter.disk(REPO_ROOT)),
        ):
            with self.subTest(probe=name):
                self.assertIsInstance(outcome, tel.ProbeOutcome)
                self.assertIn(outcome.reason, tel.PROBE_REASONS)

    def test_a_denied_probe_degrades_to_a_structured_reason_rather_than_raising(
        self,
    ) -> None:
        adapter = tel.SystemResourceProbeAdapter()
        outcome = adapter.disk("/nonexistent-path-for-telemetry-test")
        self.assertFalse(outcome.ok)
        self.assertIn(outcome.reason, ("unavailable", "permission_denied"))

    def test_absent_procfs_yields_unavailable_not_an_exception(self) -> None:
        adapter = tel.SystemResourceProbeAdapter()
        original = adapter._read_text
        adapter._read_text = lambda path: ""  # procfs absent
        try:
            self.assertEqual(adapter.memory().reason, "unavailable")
        finally:
            adapter._read_text = original

    def test_malformed_procfs_yields_parse_error_with_a_byte_count_only(self) -> None:
        adapter = tel.SystemResourceProbeAdapter()
        adapter._read_text = lambda path: "this is not meminfo at all\n"
        outcome = adapter.memory()
        self.assertEqual(outcome.reason, "parse_error")
        self.assertGreater(outcome.detail_bytes, 0)
        self.assertIsNone(outcome.value, "the offending text is NEVER retained")

    def test_composed_resources_record_every_failure_as_a_label(self) -> None:
        adapter = tel.FakeResourceProbeAdapter(
            cpu=tel.ProbeOutcome("unavailable"),
            memory=tel.ProbeOutcome("timeout"),
            load=tel.ProbeOutcome("not_supported"),
            process=tel.ProbeOutcome("permission_denied"),
        )
        resources = adapter.resources()
        self.assertIn("unavailable", resources)
        # The composed value must pass the schema's label rules, which is what stops a formatted
        # error string (and any path inside it) arriving here.
        tel.validate_event(
            {
                "schema_version": tel.TELEMETRY_SCHEMA_VERSION,
                "event_kind": "sample",
                "execution_id": "exec-01",
                "wall_timestamp": "2026-09-13T20:00:00Z",
                "monotonic_offset_seconds": 1.0,
                "resources": resources,
            }
        )

    def test_every_command_probe_is_bounded_by_a_timeout_and_an_output_cap(
        self,
    ) -> None:
        adapter = tel.SystemResourceProbeAdapter(
            max_probe_seconds=0.5, max_output_bytes=16
        )
        seen: dict = {}

        def fake_run(argv, capture_output, text, timeout, check, stdin):  # noqa: ANN001
            seen["timeout"] = timeout
            seen["check"] = check
            seen["capture_output"] = capture_output
            return subprocess.CompletedProcess(
                argv, 0, "x" * 4096, "stderr-should-be-dropped"
            )

        original = subprocess.run
        subprocess.run = fake_run
        try:
            code, out = adapter._run_bounded(["nvidia-smi"], adapter.max_probe_seconds)
        finally:
            subprocess.run = original
        self.assertEqual(seen["timeout"], 0.5)
        self.assertFalse(
            seen["check"], "check=False: a nonzero exit is data, not an exception"
        )
        self.assertTrue(seen["capture_output"])
        self.assertEqual(code, 0)
        self.assertEqual(len(out), 16, "stdout is TRUNCATED at the cap")
        self.assertNotIn(
            "stderr", out, "stderr is discarded entirely and never returned"
        )

    def test_a_timing_out_command_is_reported_not_raised(self) -> None:
        adapter = tel.SystemResourceProbeAdapter()

        def timeout_run(*args, **kwargs):  # noqa: ANN002, ANN003
            raise subprocess.TimeoutExpired(cmd="nvidia-smi", timeout=1.0)

        original = subprocess.run
        subprocess.run = timeout_run
        try:
            code, out = adapter._run_bounded(["nvidia-smi"], 1.0)
        finally:
            subprocess.run = original
        self.assertEqual(code, -1)
        self.assertEqual(out, "")

    def test_a_missing_executable_is_reported_not_raised(self) -> None:
        adapter = tel.SystemResourceProbeAdapter()

        def oserror_run(*args, **kwargs):  # noqa: ANN002, ANN003
            raise FileNotFoundError("no such tool")

        original = subprocess.run
        subprocess.run = oserror_run
        try:
            code, _out = adapter._run_bounded(["definitely-not-a-tool"], 1.0)
        finally:
            subprocess.run = original
        self.assertEqual(code, -2)

    def test_the_bench_env_reuse_decision_is_recorded_in_the_module(self) -> None:
        # OQ-02 required the decision to be RECORDED with its reason, not merely made.
        doc = tel.__doc__ or ""
        self.assertIn("REUSE DECISION", doc)
        self.assertIn("bench_env.py", doc)
        self.assertIn("WRITE FRESH, MODELED ON IT, WITH ATTRIBUTION", doc)
        self.assertIn("INSTALLED WORKFLOW CONTENT", doc)

    def test_the_module_imports_nothing_from_the_installed_workflow_tree(self) -> None:
        source = Path(tel.__file__).read_text(encoding="utf-8")
        self.assertNotIn("bench_env import", source)
        self.assertNotIn("workflows.benchmark", source)


# ================================================================================================
# E-03 / V-03: the accelerator probe
# ================================================================================================
class AcceleratorProbeTests(unittest.TestCase):
    """The only probe that shells out to a vendor tool, hence its own rules."""

    def _adapter(self, runner) -> tel.SystemResourceProbeAdapter:  # noqa: ANN001
        return tel.SystemResourceProbeAdapter(runner=runner)

    def test_a_well_formed_reading_parses_to_numeric_and_categorical_fields(
        self,
    ) -> None:
        line = "NVIDIA GeForce GTX 1070, 8192, 11, 0, 580.173.02\n"
        adapter = self._adapter(lambda argv, timeout: (0, line))
        # `which` must find something for the probe to attempt a call at all.
        outcome = self._with_which(adapter, "nvidia-smi")
        if outcome.reason == "unavailable":
            self.skipTest(
                "no accelerator tool on PATH and which() could not be stubbed"
            )
        self.assertEqual(outcome.reason, "ok")
        self.assertEqual(len(outcome.value), 1)
        record = outcome.value[0]
        self.assertEqual(record["vendor"], "nvidia")
        self.assertEqual(record["memory_total_mib"], 8192)
        self.assertEqual(record["utilization_percent"], 0)
        # Validates against the accelerator allowlist.
        tel.validate_event(
            {
                "schema_version": tel.TELEMETRY_SCHEMA_VERSION,
                "event_kind": "start",
                "execution_id": "exec-01",
                "wall_timestamp": "2026-09-13T20:00:00Z",
                "monotonic_offset_seconds": 0.0,
                "accelerators": outcome.value,
            }
        )

    def _with_which(self, adapter, tool: str) -> tel.ProbeOutcome:  # noqa: ANN001
        import shutil as shutil_module

        original = tel.shutil.which
        tel.shutil.which = lambda name: f"/usr/bin/{name}" if name == tool else None
        try:
            return adapter.accelerators()
        finally:
            tel.shutil.which = original
        del shutil_module

    def test_absent_tool_yields_unavailable(self) -> None:
        adapter = self._adapter(
            lambda argv, timeout: (_ for _ in ()).throw(
                AssertionError("must not run a command when no tool is present")
            )
        )
        original = tel.shutil.which
        tel.shutil.which = lambda name: None
        try:
            self.assertEqual(adapter.accelerators().reason, "unavailable")
        finally:
            tel.shutil.which = original

    def test_timeout_yields_the_timeout_code(self) -> None:
        adapter = self._adapter(lambda argv, timeout: (-1, ""))
        self.assertEqual(self._with_which(adapter, "nvidia-smi").reason, "timeout")

    def test_malformed_output_yields_parse_error_carrying_only_a_byte_length(
        self,
    ) -> None:
        garbage = "<html><body>error at " + _HOME_PATH + "</body></html>"
        adapter = self._adapter(lambda argv, timeout: (0, garbage))
        outcome = self._with_which(adapter, "nvidia-smi")
        self.assertEqual(outcome.reason, "parse_error")
        self.assertEqual(outcome.detail_bytes, len(garbage.encode("utf-8")))
        self.assertIsNone(outcome.value)
        # THE CRITICAL ASSERTION: the offending bytes are nowhere in the outcome.
        serialized = json.dumps(outcome.to_dict())
        self.assertNotIn(_HOME_PATH, serialized)
        self.assertNotIn("html", serialized)
        self.assertEqual(
            _scan(serialized), [], "the persisted form carries no detectable leak"
        )
        # And the raw text DOES flag, proving the scan above was looking.
        self.assertTrue(
            _scan(garbage), "control: the raw output IS flagged by the detector"
        )

    def test_no_raw_tool_output_reaches_the_jsonl_on_any_failure_path(self) -> None:
        failures = {
            "timeout": (-1, ""),
            "nonzero": (3, "fatal: could not open " + _HOME_PATH),
            "garbage": (0, "unparseable junk from " + _HOME_PATH),
            "html": (0, "<html>" + _HOME_PATH + "</html>"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for label, (code, out) in failures.items():
                with self.subTest(failure=label):
                    stream = root / f"{label}.jsonl"
                    adapter = tel.SystemResourceProbeAdapter(
                        runner=lambda argv, timeout: (code, out)
                    )
                    original = tel.shutil.which
                    tel.shutil.which = lambda name: "/usr/bin/nvidia-smi"
                    try:
                        collector = tel.TelemetryCollector(
                            stream,
                            execution_id="exec-01",
                            salt=_SALT,
                            adapter=adapter,
                            monotonic=FakeClock(),
                            wall_clock=lambda: 1_760_000_000.0,
                        )
                        with collector:
                            pass
                    finally:
                        tel.shutil.which = original
                    text = stream.read_text(encoding="utf-8")
                    self.assertNotIn(_HOME_PATH, text)
                    self.assertNotIn("html", text)
                    self.assertNotIn("fatal", text)
                    self.assertEqual(_scan(text), [])
                    events = _read_events(stream)
                    self.assertTrue(events)
                    for event in events:
                        # Only a CODE, never the text.
                        for warning in event.get("warnings", []):
                            self.assertTrue(warning.startswith("accelerator-"))

    def test_the_executable_allowlist_is_strict(self) -> None:
        self.assertEqual(tel._ACCELERATOR_EXECUTABLES, ("nvidia-smi", "rocm-smi"))
        source = Path(tel.__file__).read_text(encoding="utf-8")
        self.assertNotIn("shell=True", source, "no shell is ever used")

    def test_persisting_raw_output_would_break_this_suite(self) -> None:
        # A mutation check for E-03's prohibition: persist the raw text, prove a test fails.
        garbage = "junk from " + _HOME_PATH
        leaky = tel.ProbeOutcome("parse_error", detail_bytes=len(garbage))
        clean = json.dumps(leaky.to_dict())
        self.assertEqual(_scan(clean), [])

        class LeakyOutcome(tel.ProbeOutcome):
            def to_dict(self) -> dict:
                return {"reason": self.reason, "raw": garbage}

        mutated = json.dumps(LeakyOutcome("parse_error").to_dict())
        self.assertTrue(
            _scan(mutated),
            "the MUTANT that persists raw output IS flagged, so this assertion has teeth",
        )


# ================================================================================================
# E-04 / V-04: node identity
# ================================================================================================
class NodeIdentityTests(unittest.TestCase):
    """The pseudonym, and the DIRECT hostname-absence assertion the sanitizer cannot make."""

    def test_the_same_node_yields_a_stable_pseudonym(self) -> None:
        first = tel.node_pseudonym(salt=_SALT)
        second = tel.node_pseudonym(salt=_SALT)
        self.assertEqual(first, second)
        self.assertRegex(first, r"^node:[0-9a-f]{16}$")

    def test_a_different_node_yields_a_different_pseudonym(self) -> None:
        self.assertNotEqual(
            tel.node_pseudonym(salt=_SALT, raw="node-a"),
            tel.node_pseudonym(salt=_SALT, raw="node-b"),
        )

    def test_rotating_the_salt_invalidates_correlation_by_design(self) -> None:
        self.assertNotEqual(
            tel.node_pseudonym(salt=_SALT, raw="node-a"),
            tel.node_pseudonym(salt=_OTHER_SALT, raw="node-a"),
        )

    def test_a_missing_salt_is_refused_rather_than_defaulted(self) -> None:
        with self.assertRaises(tel.SchemaRefusal):
            tel.node_pseudonym(salt="")

    def test_neither_the_raw_hostname_nor_the_hash_input_appears_in_the_pseudonym(
        self,
    ) -> None:
        raw_input = tel.node_identity_input()
        pseudonym = tel.node_pseudonym(salt=_SALT)
        for spelling in self._hostname_spellings():
            self.assertNotIn(spelling, pseudonym)
        self.assertNotIn(raw_input, pseudonym)

    def _hostname_spellings(self) -> list[str]:
        """All three spellings, because suppressing one and shipping another is the failure."""

        names = {socket.gethostname(), socket.getfqdn()}
        names.add(socket.gethostname().split(".")[0])
        names.add(socket.getfqdn().split(".")[0])
        return sorted(name for name in names if name and len(name) > 2)

    def test_the_raw_hostname_is_absent_from_the_produced_jsonl(self) -> None:
        # THE LOAD-BEARING ASSERTION. Direct, and independent of the sanitizer's tier config.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter = tel.SystemResourceProbeAdapter()
            collector = tel.TelemetryCollector(
                root / tel.TELEMETRY_FILENAME,
                execution_id="exec-01",
                salt=_SALT,
                adapter=adapter,
                config=cfg.TelemetryConfig(enabled=True, sampling_enabled=True),
            )
            with collector:
                collector.sample()
            text = (root / tel.TELEMETRY_FILENAME).read_text(encoding="utf-8")
            self.assertTrue(
                text.strip(), "there must be output for the assertion to mean anything"
            )
            for spelling in self._hostname_spellings():
                with self.subTest(spelling_len=len(spelling)):
                    self.assertNotIn(
                        spelling.lower(),
                        text.lower(),
                        "the raw hostname must not appear in the telemetry stream",
                    )
            events = _read_events(root / tel.TELEMETRY_FILENAME)
            self.assertTrue(
                all(e.get("node_id", "").startswith("node:") for e in events)
            )

    def test_the_sanitizer_does_not_fail_on_a_hostname_which_is_why_the_direct_check_leads(
        self,
    ) -> None:
        # Measured and asserted, so the reason the direct assertion is load-bearing is IN the suite
        # rather than only in a plan's prose. If a future repo config sets `hostname_fail = true`,
        # this test tells the reader the corroboration got stronger; it does not weaken the direct
        # assertion above, which does not depend on it.
        hostname = socket.gethostname()
        findings = _scan(hostname)
        self.assertEqual(
            [f for f in findings if f.severity == "fail"],
            [],
            "the shipped detector does NOT fail on a bare hostname at default settings",
        )
        # CONTROL: the same invocation DOES fail on a username and a home path.
        self.assertTrue(
            [f for f in _scan(_HANDLE) if f.severity == "fail"],
            "control: a handle IS a fail-severity finding, so the scan above was looking",
        )
        self.assertTrue(
            [f for f in _scan(_HOME_PATH) if f.severity == "fail"],
            "control: a home path IS a fail-severity finding",
        )

    def test_sanitizer_scan_of_the_produced_telemetry_is_clean_with_a_control(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            collector = tel.TelemetryCollector(
                root / tel.TELEMETRY_FILENAME,
                execution_id="exec-01",
                salt=_SALT,
                adapter=tel.SystemResourceProbeAdapter(),
                config=cfg.TelemetryConfig(enabled=True, sampling_enabled=True),
            )
            with collector:
                collector.sample()
            text = (root / tel.TELEMETRY_FILENAME).read_text(encoding="utf-8")
            self.assertEqual(
                [f for f in _scan(text) if f.severity == "fail"],
                [],
                "no fail-severity finding in the produced telemetry",
            )
            # CONTROL, without which "clean" and "not looking" are indistinguishable.
            seeded = text + json.dumps({"leaked": _HOME_PATH}) + "\n"
            self.assertTrue(
                [f for f in _scan(seeded) if f.severity == "fail"],
                "control: the SAME invocation flags a seeded home path",
            )

    def test_identity_assembly_never_raises_even_with_every_source_broken(self) -> None:
        originals = (socket.getfqdn, socket.gethostname, tel.platform.node)
        socket.getfqdn = lambda: (_ for _ in ()).throw(OSError("no dns"))
        socket.gethostname = lambda: (_ for _ in ()).throw(OSError("no host"))
        tel.platform.node = lambda: (_ for _ in ()).throw(OSError("no node"))
        try:
            value = tel.node_identity_input()
            self.assertTrue(value)
            self.assertRegex(tel.node_pseudonym(salt=_SALT), r"^node:[0-9a-f]{16}$")
        finally:
            socket.getfqdn, socket.gethostname, tel.platform.node = originals

    def test_no_environment_value_is_a_host_identity_fallback(self) -> None:
        # An env value must never stand in for host identity (a plan convention). Checked on the
        # PARSED function body, so the surrounding docstring that explains the rule cannot trip it.
        tree = ast.parse(Path(tel.__file__).read_text(encoding="utf-8"))
        bodies = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name in ("node_identity_input", "node_pseudonym")
        ]
        self.assertEqual(len(bodies), 2, "both identity functions must be found")
        for func in bodies:
            names = {
                child.attr if isinstance(child, ast.Attribute) else child.id
                for child in ast.walk(func)
                if isinstance(child, (ast.Name, ast.Attribute))
            }
            with self.subTest(function=func.name):
                self.assertNotIn("environ", names)
                self.assertNotIn("getenv", names)
                self.assertNotIn("environb", names)


# ================================================================================================
# E-05 / V-05: the collector
# ================================================================================================
class CollectorLifecycleTests(unittest.TestCase):
    """Exactly one start, a best-effort end, idempotent close, monotonic durations."""

    def test_one_execution_yields_exactly_one_start_and_one_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clock = FakeClock()
            collector = _collector(root, clock=clock)
            with collector:
                clock.advance(2.5)
            events = _read_events(root / tel.TELEMETRY_FILENAME)
            kinds = [e["event_kind"] for e in events]
            self.assertEqual(kinds, ["start", "end"])
            self.assertEqual(events[1]["duration_seconds"], 2.5)
            self.assertEqual([e["sequence"] for e in events], [1, 2])

    def test_a_second_close_is_a_no_op_and_emits_no_second_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            collector = _collector(root)
            collector.start()
            self.assertIsNotNone(collector.close())
            self.assertIsNone(collector.close(), "the second close returns nothing")
            self.assertIsNone(collector.close())
            kinds = [
                e["event_kind"] for e in _read_events(root / tel.TELEMETRY_FILENAME)
            ]
            self.assertEqual(kinds.count("end"), 1)

    def test_a_second_start_emits_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            collector = _collector(root)
            collector.start()
            self.assertIsNone(collector.start())
            collector.close()
            kinds = [
                e["event_kind"] for e in _read_events(root / tel.TELEMETRY_FILENAME)
            ]
            self.assertEqual(kinds.count("start"), 1)

    def test_durations_derive_from_a_monotonic_clock_and_are_never_negative(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clock = FakeClock()
            collector = _collector(root, clock=clock)
            collector.start()
            clock.advance(7.25)
            collector.close()
            events = _read_events(root / tel.TELEMETRY_FILENAME)
            self.assertEqual(events[-1]["duration_seconds"], 7.25)
            self.assertGreaterEqual(events[-1]["monotonic_offset_seconds"], 0.0)

    def test_a_wall_clock_stepping_backwards_cannot_produce_a_negative_duration(
        self,
    ) -> None:
        # CLOCK SKEW: the wall clock jumps back a day (NTP correction, resumed laptop). Durations
        # come from the monotonic clock, so they are unaffected; timestamps remain well formed.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clock = FakeClock()
            wall = {"now": 1_760_000_000.0}
            collector = tel.TelemetryCollector(
                root / tel.TELEMETRY_FILENAME,
                execution_id="exec-01",
                salt=_SALT,
                adapter=tel.FakeResourceProbeAdapter(),
                monotonic=clock,
                wall_clock=lambda: wall["now"],
            )
            collector.start()
            wall["now"] -= 86_400.0
            clock.advance(1.5)
            collector.close()
            events = _read_events(root / tel.TELEMETRY_FILENAME)
            self.assertEqual(events[-1]["duration_seconds"], 1.5)
            for event in events:
                self.assertRegex(
                    event["wall_timestamp"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
                )

    def test_the_writer_is_the_shipped_append_jsonl_and_not_a_new_one(self) -> None:
        # The identity check is the load-bearing one: the default writer must BE the shipped
        # function, not merely resemble it.
        self.assertIn(
            "agent_workflows.runner_shared.append_jsonl",
            _imported_modules(Path(tel.__file__)),
        )
        # And no second writer: no `fsync` and no append-mode `open` anywhere in this module's CODE
        # (its docstring legitimately discusses `append_jsonl`'s per-event fsync, which is why this
        # is an AST check and not a grep).
        identifiers = _code_identifiers(Path(tel.__file__))
        self.assertNotIn("fsync", identifiers)
        tree = ast.parse(Path(tel.__file__).read_text(encoding="utf-8"))
        append_modes = [
            arg.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            for arg in node.args
            if isinstance(arg, ast.Constant)
            and isinstance(arg.value, str)
            and arg.value in ("a", "ab", "a+")
        ]
        self.assertEqual(
            append_modes, [], "this module opens no stream in append mode itself"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            collector = tel.TelemetryCollector(
                root / tel.TELEMETRY_FILENAME,
                execution_id="exec-01",
                salt=_SALT,
                adapter=tel.FakeResourceProbeAdapter(),
                monotonic=FakeClock(),
            )
            self.assertIs(collector._writer, append_jsonl)

    def test_an_unwritable_stream_records_a_warning_and_never_ends_the_run(
        self,
    ) -> None:
        def exploding_writer(path, event):  # noqa: ANN001
            raise OSError("disk full")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            collector = _collector(root, writer=exploding_writer)
            with collector:
                collector.sample()
            self.assertIn("telemetry-write-failed", collector.counters.warnings)

    def test_a_disabled_config_emits_nothing_at_all(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            collector = _collector(root, config=cfg.TelemetryConfig(enabled=False))
            with collector:
                collector.sample()
            self.assertEqual(_read_events(root / tel.TELEMETRY_FILENAME), [])

    def test_an_adapter_that_raises_is_isolated_to_a_warning(self) -> None:
        class HostileAdapter(tel.ResourceProbeAdapter):
            def resources(self, *, disk_path=None):  # noqa: ANN001, ANN201
                raise RuntimeError("probe exploded")

            def accelerators(self):  # noqa: ANN201
                raise RuntimeError("gpu exploded")

            def tool_versions(self):  # noqa: ANN201
                raise RuntimeError("versions exploded")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            collector = _collector(root, adapter=HostileAdapter())
            with collector:
                pass
            events = _read_events(root / tel.TELEMETRY_FILENAME)
            self.assertEqual([e["event_kind"] for e in events], ["start", "end"])
            self.assertIn("resource-probe-failed", collector.counters.warnings)
            self.assertGreater(events[-1]["probe_error_count"], 0)

    def test_allowlisted_context_fields_are_carried_and_others_are_not(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            collector = _collector(
                root,
                context={
                    "ipd_id6": "lhccjf",
                    "set_id": "runanalytics",
                    "host": "opencode",
                    "not_an_allowlisted_field": "dropped",
                },
            )
            with collector:
                pass
            event = _read_events(root / tel.TELEMETRY_FILENAME)[0]
            self.assertEqual(event["ipd_id6"], "lhccjf")
            self.assertEqual(event["host"], "opencode")
            self.assertNotIn("not_an_allowlisted_field", event)


# ================================================================================================
# E-06 / V-06: the sampler
# ================================================================================================
class SamplerTests(unittest.TestCase):
    """Bounded, stoppable on every path, and SKIPPING rather than accumulating."""

    def _sampler(self, root: Path, **kwargs):  # noqa: ANN003, ANN201
        collector = _collector(
            root, config=cfg.TelemetryConfig(enabled=True, sampling_enabled=True)
        )
        collector.start()
        return collector, tel.ResourceSampler(collector, **kwargs)

    def test_the_thread_is_stopped_after_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            collector, sampler = self._sampler(Path(tmp), interval_seconds=0.02)
            with sampler:
                self.assertTrue(sampler.running)
            self.assertFalse(
                sampler.running, "the thread is provably stopped after __exit__"
            )
            self.assertNotIn(
                "aw-telemetry-sampler",
                [t.name for t in threading.enumerate()],
                "no telemetry thread outlives its context",
            )
            collector.close()

    def test_the_thread_is_stopped_after_an_exception_inside_the_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            collector, sampler = self._sampler(Path(tmp), interval_seconds=0.02)
            with self.assertRaises(RuntimeError):
                with sampler:
                    self.assertTrue(sampler.running)
                    raise RuntimeError("boom")
            self.assertFalse(sampler.running)
            collector.close()

    def test_the_thread_is_stopped_by_a_signal_assisted_teardown(self) -> None:
        # A signal-assisted teardown reaches this object through a plain `stop()` call, which is
        # precisely the design: the runner owns signals, this owns a method.
        with tempfile.TemporaryDirectory() as tmp:
            collector, sampler = self._sampler(Path(tmp), interval_seconds=0.02)
            sampler.start()
            self.assertTrue(sampler.running)
            try:
                raise KeyboardInterrupt
            except KeyboardInterrupt:
                sampler.stop()  # what a shutdown routine would call
            self.assertFalse(sampler.running)
            collector.close()

    def test_stop_is_idempotent_and_safe_before_start(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            collector, sampler = self._sampler(Path(tmp))
            sampler.stop()
            sampler.stop()
            self.assertFalse(sampler.running)
            collector.close()

    def test_an_overlapping_tick_is_skipped_and_counted_never_queued(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            collector, sampler = self._sampler(Path(tmp))
            # Simulate a probe still in flight, which is what a probe slower than the interval
            # produces. The next tick must SKIP.
            sampler._sampling.set()
            self.assertFalse(sampler.tick())
            self.assertFalse(sampler.tick())
            self.assertEqual(sampler.samples_skipped, 2)
            self.assertEqual(sampler.samples_taken, 0)
            sampler._sampling.clear()
            self.assertTrue(sampler.tick())
            self.assertEqual(sampler.samples_taken, 1)
            collector.close()
            end = _read_events(Path(tmp) / tel.TELEMETRY_FILENAME)[-1]
            self.assertEqual(
                end["sample_skipped_count"], 2, "skips are COUNTED in the end event"
            )

    def test_a_probe_slower_than_the_interval_skips_rather_than_accumulating(
        self,
    ) -> None:
        # No REAL sleep: the fake adapter's delay is applied through an injected sleeper that only
        # advances a fake clock, and the overlap is produced by a reentrant tick.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clock = FakeClock()
            holder: dict = {}

            def slow_sleeper(seconds: float) -> None:
                clock.advance(seconds)
                sampler = holder.get("sampler")
                if sampler is not None and not holder.get("reentered"):
                    holder["reentered"] = True
                    # A tick arriving WHILE this probe is in flight.
                    holder["result"] = sampler.tick()

            adapter = tel.FakeResourceProbeAdapter(delay=5.0, sleeper=slow_sleeper)
            collector = _collector(
                root,
                adapter=adapter,
                config=cfg.TelemetryConfig(
                    enabled=True, sampling_enabled=True, sample_interval_seconds=1.0
                ),
                clock=clock,
            )
            collector.start()
            sampler = tel.ResourceSampler(
                collector, interval_seconds=1.0, monotonic=clock
            )
            holder["sampler"] = sampler
            self.assertTrue(sampler.tick())
            self.assertIs(holder["result"], False, "the overlapping tick was SKIPPED")
            self.assertEqual(sampler.samples_skipped, 1)
            collector.close()

    def test_the_check_interval_is_clamped_against_the_interval(self) -> None:
        collector_root = tempfile.mkdtemp()
        collector = _collector(Path(collector_root))
        for interval, expected_max in ((60.0, 15.0), (4.0, 1.0), (0.2, 0.2)):
            with self.subTest(interval=interval):
                sampler = tel.ResourceSampler(collector, interval_seconds=interval)
                self.assertLessEqual(sampler.check_interval, expected_max + 1e-9)
                self.assertGreater(sampler.check_interval, 0)

    def test_sampling_does_not_run_when_it_is_not_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            collector = _collector(
                root, config=cfg.TelemetryConfig(sampling_enabled=False)
            )
            collector.start()
            sampler = tel.ResourceSampler(collector, interval_seconds=0.01)
            with sampler:
                self.assertFalse(
                    sampler.running, "an unenabled sampler starts no thread"
                )
            collector.close()

    def test_the_thread_loop_waits_on_the_event_rather_than_sleeping(self) -> None:
        source = Path(tel.__file__).read_text(encoding="utf-8")
        loop = source[source.index("    def _run(self) -> None:\n        last") :]
        self.assertIn("self._stop.wait(self.check_interval)", loop)
        self.assertNotIn("time.sleep", loop)

    def test_this_module_registers_no_signal_handler_and_forks_no_cleanup_path(
        self,
    ) -> None:
        # Spec `c4gd2h` R5 requires ONE cleanup implementation and prohibits divergent per-level
        # cleanup; A9 requires a structural check that exactly one exists. This is that check for
        # this module: it must add no second path and must not call the shared one.
        #
        # THE CHECK PARSES CODE RATHER THAN GREPPING TEXT, deliberately. A substring search over the
        # source matched this module's own DOCSTRINGS, which cite `signal.signal` and
        # `runner_shutdown.clean_shutdown` precisely in order to explain why neither is called. A
        # text search cannot tell an explanation from an invocation, so it would have to be either
        # falsely red (as it was) or defeated by stripping the words it looks for, and the second is
        # how a real regression gets waved through. The AST cannot be fooled by prose.
        for name in _code_identifiers(Path(tel.__file__)):
            with self.subTest(identifier=name):
                self.assertNotIn(name, _FORBIDDEN_CODE_IDENTIFIERS)
        imported = _imported_modules(Path(tel.__file__))
        self.assertNotIn("signal", imported, "no signal module is imported at all")
        self.assertNotIn("atexit", imported)
        self.assertNotIn(
            "agent_workflows.runner_shutdown",
            imported,
            "the shared cleanup routine is neither imported nor called; the runner wires this in",
        )

    def test_the_sampler_shape_matches_the_shipped_watchdogs(self) -> None:
        source = Path(tel.__file__).read_text(encoding="utf-8")
        sampler_source = source[source.index("class ResourceSampler") :]
        for marker in (
            "threading.Event()",
            "daemon=True",
            "self._stop.wait(",
            "join(timeout=1.0)",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, sampler_source)


# ================================================================================================
# E-08 / V-08: degraded systems, overhead, and the no-real-IO guarantee
# ================================================================================================
class DegradedSystemTests(unittest.TestCase):
    """Every degraded case yields a structured warning and a COMPLETED run."""

    def _run_with(
        self, adapter: tel.ResourceProbeAdapter
    ) -> tuple[list[dict], list[str]]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            collector = _collector(
                root,
                adapter=adapter,
                config=cfg.TelemetryConfig(enabled=True, sampling_enabled=True),
            )
            with collector:
                collector.sample()
            return _read_events(
                root / tel.TELEMETRY_FILENAME
            ), collector.counters.warnings

    def test_each_degraded_case_completes_with_a_structured_warning(self) -> None:
        cases = {
            "procfs-absent": tel.FakeResourceProbeAdapter(
                memory=tel.ProbeOutcome("unavailable")
            ),
            "gpu-tool-absent": tel.FakeResourceProbeAdapter(
                accelerators=tel.ProbeOutcome("unavailable")
            ),
            "gpu-malformed": tel.FakeResourceProbeAdapter(
                accelerators=tel.ProbeOutcome("parse_error", detail_bytes=4096)
            ),
            "probe-timeout": tel.FakeResourceProbeAdapter(
                accelerators=tel.ProbeOutcome("timeout")
            ),
            "load-unsupported": tel.FakeResourceProbeAdapter(
                load=tel.ProbeOutcome("not_supported")
            ),
            "permission-denied": tel.FakeResourceProbeAdapter(
                process=tel.ProbeOutcome("permission_denied")
            ),
            "everything-broken": tel.FakeResourceProbeAdapter(
                cpu=tel.ProbeOutcome("unavailable"),
                memory=tel.ProbeOutcome("unavailable"),
                load=tel.ProbeOutcome("unavailable"),
                process=tel.ProbeOutcome("unavailable"),
                tool_versions=tel.ProbeOutcome("unavailable"),
                accelerators=tel.ProbeOutcome("unavailable"),
            ),
        }
        for label, adapter in cases.items():
            with self.subTest(case=label):
                events, _warnings = self._run_with(adapter)
                kinds = [e["event_kind"] for e in events]
                self.assertEqual(
                    kinds,
                    ["start", "sample", "end"],
                    "a degraded host still yields a COMPLETE stream",
                )
                for event in events:
                    tel.validate_event(event)

    def test_impossible_values_are_refused_rather_than_persisted(self) -> None:
        impossible = tel.FakeResourceProbeAdapter(
            cpu=tel.ProbeOutcome("ok", {"cpu_logical_count": float("inf")})
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            collector = _collector(root, adapter=impossible)
            with collector:
                pass
            self.assertIn(
                "telemetry-event-refused",
                collector.counters.warnings,
                "an impossible value is refused and recorded as a code, never written",
            )
            self.assertEqual(_read_events(root / tel.TELEMETRY_FILENAME), [])

    def test_negative_and_absurd_resource_values_do_not_break_the_stream(self) -> None:
        for value in (-1, -0.0001, 2**70):
            with self.subTest(value=value):
                adapter = tel.FakeResourceProbeAdapter(
                    memory=tel.ProbeOutcome("ok", {"memory_total_bytes": value})
                )
                events, _warnings = self._run_with(adapter)
                self.assertEqual(
                    [e["event_kind"] for e in events], ["start", "sample", "end"]
                )


class NoRealIOTests(unittest.TestCase):
    """Asserted BY CONSTRUCTION with stubs that RAISE, never by hoping."""

    def test_a_fake_adapter_run_performs_no_subprocess_no_sleep_and_no_network(
        self,
    ) -> None:
        def exploding_run(*args, **kwargs):  # noqa: ANN002, ANN003
            raise AssertionError("a test must not spawn a real subprocess")

        def exploding_sleep(*args, **kwargs):  # noqa: ANN002, ANN003
            raise AssertionError("a test must not perform a real sleep")

        def exploding_socket(*args, **kwargs):  # noqa: ANN002, ANN003
            raise AssertionError("a test must not open a network connection")

        originals = (subprocess.run, subprocess.Popen, time.sleep, socket.socket)
        subprocess.run = exploding_run
        subprocess.Popen = exploding_run
        time.sleep = exploding_sleep
        socket.socket = exploding_socket
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                clock = FakeClock()
                collector = _collector(root, clock=clock)
                sampler = tel.ResourceSampler(
                    collector, interval_seconds=1.0, monotonic=clock
                )
                with collector:
                    sampler.tick()
                    sampler.tick()
                events = _read_events(root / tel.TELEMETRY_FILENAME)
                self.assertEqual(
                    [e["event_kind"] for e in events],
                    ["start", "sample", "sample", "end"],
                )
        finally:
            subprocess.run, subprocess.Popen, time.sleep, socket.socket = originals


class OverheadTests(unittest.TestCase):
    """Measured against the REAL writer, which fsyncs every event, not an assumed buffered one."""

    def test_per_event_cost_against_the_real_append_jsonl_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # The REAL writer, deliberately: `append_jsonl` calls os.fsync on EVERY event, so a
            # budget measured against an in-memory writer would be measuring the wrong thing.
            collector = tel.TelemetryCollector(
                root / tel.TELEMETRY_FILENAME,
                execution_id="exec-01",
                salt=_SALT,
                adapter=tel.FakeResourceProbeAdapter(),
                config=cfg.TelemetryConfig(enabled=True, sampling_enabled=True),
                monotonic=FakeClock(),
                wall_clock=lambda: 1_760_000_000.0,
            )
            collector.start()
            count = 25
            started = time.perf_counter()
            for _ in range(count):
                collector.sample()
            elapsed = time.perf_counter() - started
            collector.close()
            per_event = elapsed / count
            # A generous ceiling: this asserts the ORDER OF MAGNITUDE (an fsync per event, not a
            # per-event subprocess or a per-event sleep). The measured figure is reported in the
            # plan's validation evidence; this test exists to catch a regression of KIND.
            self.assertLess(
                per_event,
                0.25,
                f"per-event cost {per_event:.6f}s against the real fsyncing writer",
            )
            self.assertEqual(
                len(_read_events(root / tel.TELEMETRY_FILENAME)), count + 2
            )

    def test_sampling_cadence_cannot_exceed_the_configured_rate(self) -> None:
        # The interval floor is the rate guarantee, and it is enforced in ONE place.
        config = cfg.parse_telemetry_settings(
            {"sampling_enabled": True, "sample_interval_seconds": 0.001}
        )
        self.assertGreaterEqual(
            config.sample_interval_seconds,
            cfg.MIN_SAMPLE_INTERVAL_SECONDS,
            "a hostile interval is clamped, so the event rate has a hard ceiling",
        )
        with tempfile.TemporaryDirectory() as tmp:
            collector = _collector(Path(tmp), config=config)
            sampler = tel.ResourceSampler(collector)
            self.assertGreaterEqual(sampler.interval, cfg.MIN_SAMPLE_INTERVAL_SECONDS)


class PrivacyCorpusTests(unittest.TestCase):
    """The forbidden-value list as a TEST CORPUS, which is the only role it has here."""

    def test_no_forbidden_shaped_value_can_be_persisted(self) -> None:
        # Assembled at runtime; no literal canary is committed.
        forbidden = {
            "absolute_path": _HOME_PATH,
            "home_path": "/ho" + "me/" + _HANDLE,
            "network_address": "10.0.0.5:8443",
            "raw_hostname": socket.gethostname(),
            "file_content": "line one\nline two\n",
            "command_line": "git commit -m x -- " + _HOME_PATH,
            "env_value": "PATH=" + _HOME_PATH + "/bin",
            "session_id": "ses_" + "9f3a71c0d2b84e55",
        }
        base = {
            "schema_version": tel.TELEMETRY_SCHEMA_VERSION,
            "event_kind": "start",
            "execution_id": "exec-01",
            "wall_timestamp": "2026-09-13T20:00:00Z",
            "monotonic_offset_seconds": 0.0,
        }
        for label, value in forbidden.items():
            with self.subTest(kind=label, placement="new-key"):
                event = dict(base)
                event[label] = value
                with self.assertRaises(tel.SchemaRefusal):
                    tel.validate_event(event)
            with self.subTest(kind=label, placement="existing-label-key"):
                event = dict(base)
                event["phase"] = value
                with self.assertRaises(tel.SchemaRefusal):
                    tel.validate_event(event)
            with self.subTest(kind=label, placement="nested-resources"):
                event = dict(base)
                event["resources"] = {"container_hint": value}
                with self.assertRaises(tel.SchemaRefusal):
                    tel.validate_event(event)

    def test_this_test_file_and_the_module_are_themselves_clean(self) -> None:
        for path in (Path(tel.__file__), Path(cfg.__file__), Path(__file__)):
            with self.subTest(path=path.name):
                findings = [
                    f
                    for f in _scan(path.read_text(encoding="utf-8"))
                    if f.severity == "fail"
                ]
                self.assertEqual(
                    findings,
                    [],
                    "a committed corpus of real-shaped secrets is a leak that ships",
                )

    def test_no_literal_canary_is_committed_in_this_file(self) -> None:
        source = Path(__file__).read_text(encoding="utf-8")
        # Every canary is assembled, so the literal never appears as one token in the file.
        self.assertNotIn(_HANDLE, source.replace('"gfa" + "riello"', ""))
        self.assertTrue(re.search(r'"gfa"\s*\+\s*"riello"', source))


if __name__ == "__main__":
    unittest.main()
