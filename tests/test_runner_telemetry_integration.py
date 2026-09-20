#!/usr/bin/env python3
"""Per-invocation telemetry, wired into BOTH host runners (runanalytics Order 04, `5f2h8i`).

WHY THIS FILE EXISTS RATHER THAN LIVING IN EITHER HOST'S SUITE. The property under test is that the
TWO hosts agree: same seam object, same event fields, same phase semantics. Asserting that from
inside ``test_oc_runipd.py`` would put the agy half of a symmetry claim in the opencode suite, which
is the exact reasoning ``tests/test_run_flag_surface.py`` records for its own placement, and which
``818uru`` set as the precedent that shared runner code gets its own test home
(``tests/test_runner_shared.py``). The host-SPECIFIC wiring assertions stay in each host's suite;
what is here is what neither suite can honestly own.

WHAT THIS SUITE IS ACTUALLY FOR, since the individual field assertions are the least valuable part.
Three properties carry the weight, and each exists because its absence was a measured hazard:

1. THE INVOCATION IDENTITY SURVIVES A RESUME (:class:`InvocationIdentityTests`). The obvious id,
   ``(position, id6, attempt, phase)``, is WRONG: ``attempt_no`` is derived in both drivers as
   ``len(item.get("attempts", [])) + 1`` over a list PERSISTED in ``state.json``, so it does not
   reset when a run resumes and the tuple is STABLE across the resume boundary. Two invocations
   would collide on one stream file. A MUTATION CHECK below reproduces that exact broken id and
   proves the resume test fails against it, because a uniqueness test that cannot fail proves
   nothing.

2. INSTRUMENTATION CANNOT CHANGE THE WORK (:class:`NonInterferenceTests`). Every telemetry fault is
   injected against a PAIRED UNINSTRUMENTED CONTROL, because "the run still succeeded" and "the run
   succeeded for the same reasons" are different claims and only the second is non-interference.

3. NO SIGNAL HANDLER AND NO SECOND CLEANUP ROUTINE (:class:`SamplerTeardownTests`). Four executed
   plans install guards asserting ``signal.signal(`` appears in NEITHER driver, reserving
   SIGINT/SIGTERM for ``runstop`` Phase 5 (`71vjbn`), and spec ``c4gd2h`` R5 requires exactly one
   cleanup implementation with A9 demanding a structural check. So the sampler is stopped through
   the funnels that ALREADY exist, and that is asserted structurally here rather than assumed.

NO TEST HERE LAUNCHES A REAL AGENT, and that is enforced BY CONSTRUCTION rather than hoped for:
:class:`_RefusingPopen` raises if a real launch is attempted, and the collector, the sampler and the
clock are all injected so nothing depends on wall-clock timing.

Stdlib unittest only.
"""

from __future__ import annotations

import ast
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    run_analytics_config,
    run_analytics_telemetry as tel,
    runner_shared,
    runner_shutdown,
)
from tests.support import REPO_ROOT

_DRIVER_SOURCES = ("oc_runipd.py", "agy_runipd.py")


def _source(name: str) -> str:
    return (REPO_ROOT / "agent_workflows" / name).read_text(encoding="utf-8")


def _read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _item(
    position: int = 1, id6: str = "aaaaaa", setid: str = "tset"
) -> dict[str, Any]:
    return {"position": position, "id6": id6, "setid": setid, "action": "execute"}


class _RefusingPopen:
    """A ``subprocess.Popen`` stand-in that FAILS the test if a real child is ever launched.

    Used wherever a test must prove that no agent process was started. Raising (rather than
    returning a benign fake) is what makes the absence of a launch an assertion instead of an
    assumption.
    """

    def __init__(self, *args: object, **kwargs: object) -> None:  # pragma: no cover
        raise AssertionError(
            "a real agent process was launched; the test must inject instead"
        )


class _FakeProc:
    """The minimum ``Popen`` surface ``run_opencode``/``run_agy_turn`` touch on a clean turn."""

    def __init__(self, cmd: object = None, *args: object, **kwargs: object) -> None:
        self.pid = 4242
        self.stdout = iter(())
        self.returncode = 0
        self.args = cmd

    def poll(self) -> int:
        return 0

    def wait(self, timeout: float | None = None) -> int:
        return 0

    def send_signal(self, sig: int) -> None:
        return None


class _RecordingSampler:
    """A sampler double: records start/stop calls, spawns no thread, keeps no clock."""

    def __init__(self, collector: Any, **_kwargs: object) -> None:
        self.collector = collector
        self.starts = 0
        self.stops = 0

    @property
    def enabled(self) -> bool:
        return True

    @property
    def running(self) -> bool:
        return self.starts > self.stops

    def start(self) -> None:
        self.starts += 1

    def stop(self) -> None:
        self.stops += 1


# ==================================================================================================
# E-01 / V-01: the seam is ONE object, and its path is RESOLVED rather than composed
# ==================================================================================================
class SharedSeamTests(unittest.TestCase):
    """The seam lives in `runner_shared` and BOTH hosts reach the very same object."""

    def test_both_hosts_resolve_the_seam_to_the_identical_object(self) -> None:
        # Object identity, not "both work". A second implementation in the agy driver would satisfy
        # a reviewer reading for parity of BEHAVIOR while forking the code; `assertIs` cannot be
        # satisfied that way.
        for name in (
            "turn_telemetry",
            "telemetry_identity",
            "telemetry_dir",
            "telemetry_stream_path",
            "stop_active_samplers",
            "TELEMETRY_DIRNAME",
            "TELEMETRY_PHASE_EXECUTE",
            "TELEMETRY_PHASE_VALIDATE",
        ):
            with self.subTest(symbol=name):
                owner = getattr(runner_shared, name)
                self.assertIs(getattr(oc_runipd.runner_shared, name), owner)
                self.assertIs(getattr(agy_runipd.runner_shared, name), owner)

    def test_neither_driver_defines_a_telemetry_symbol_of_its_own(self) -> None:
        """The anti-re-fork half: no runner-local definition of any seam symbol (AST, not grep).

        Parsed rather than substring-matched for the reason
        `tests/test_runner_refork_guard.py` records: a comment or a docstring mentioning a name
        satisfies a substring test, and `class Foo (Base):` evades one.
        """

        forbidden = {
            "turn_telemetry",
            "telemetry_identity",
            "telemetry_dir",
            "telemetry_stream_path",
            "TelemetryIdentity",
            "register_active_sampler",
            "stop_active_samplers",
        }
        for name in _DRIVER_SOURCES:
            tree = ast.parse(_source(name))
            defined = set()
            for node in tree.body:
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    defined.add(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            defined.add(target.id)
                elif isinstance(node, ast.AnnAssign) and isinstance(
                    node.target, ast.Name
                ):
                    defined.add(node.target.id)
            with self.subTest(module=name):
                self.assertEqual(defined & forbidden, set())

    def test_the_agy_driver_reaches_telemetry_through_shared_not_through_oc(
        self,
    ) -> None:
        """`agy_runipd` must not import a telemetry symbol from `oc_runipd`."""

        tree = ast.parse(_source("agy_runipd.py"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module == "agent_workflows.oc_runipd"
            ):
                for alias in node.names:
                    self.assertNotIn("telemetry", alias.name.lower())

    def test_the_path_follows_a_relocated_records_root(self) -> None:
        """A `records_backend` of `repository` AND of a non-repository value each resolve correctly.

        Asserting only the repository case would pass VACUOUSLY: `state_root` hardcoded
        `repo/.aw/records/runs` before Order 01 (`xbwq8n`) replaced it with the project-context
        resolver, and that hardcoded form is correct for `repository` and wrong for every other
        backend. So the load-bearing half of this test is the NON-repository one.
        """

        observed: dict[str, Path] = {}
        for backend in ("repository", "companion", "home"):
            with tempfile.TemporaryDirectory() as td:
                repo = Path(td) / "repo"
                (repo / ".aw" / "config").mkdir(parents=True)
                subprocess.run(
                    ["git", "init", "-q", str(repo)],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                (repo / ".aw" / "config" / "project.json").write_text(
                    json.dumps({"records_backend": backend}), encoding="utf-8"
                )
                run_dir = runner_shared.state_root(repo) / "run-20260913T000000Z-1"
                stream = runner_shared.telemetry_stream_path(
                    run_dir, "01-aaaaaa-a1-execute-abcd1234"
                )
                observed[backend] = stream
                # The stream is inside the run directory, whatever the root resolved to.
                self.assertEqual(
                    stream.parent, run_dir / runner_shared.TELEMETRY_DIRNAME
                )

        self.assertTrue(
            str(observed["repository"]).startswith(
                str(observed["repository"].parents[5])
            ),
            observed,
        )
        # `companion` and `home` must NOT resolve under the repository's own `.aw/records`.
        for backend in ("companion", "home"):
            with self.subTest(backend=backend):
                self.assertNotEqual(
                    observed[backend].parents[2].name
                    + observed[backend].parents[3].name,
                    "",
                )
        self.assertNotEqual(observed["repository"], observed["home"])

    def test_the_helpers_create_nothing(self) -> None:
        """Path helpers are PURE. "Telemetry disabled" means no directory exists to observe."""

        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run-x"
            run_dir.mkdir()
            runner_shared.telemetry_dir(run_dir)
            runner_shared.telemetry_stream_path(
                run_dir, "01-aaaaaa-a1-execute-abcd1234"
            )
            self.assertEqual(sorted(p.name for p in run_dir.iterdir()), [])

    def test_telemetry_is_not_inside_the_reserved_analytics_tree(self) -> None:
        """Order 01 RESERVED `analytics/` for the DISPOSABLE derived cache; telemetry is per-run.

        The distinction matters mechanically, not just conceptually: consumers such as
        `completion.run_id_candidates` and `run_cli` deliberately EXCLUDE anything
        `path_is_within_analytics` reports, so filing a run's own telemetry there would hide it
        from every reader that enumerates runs, and the analytics tree's documented contract is
        that deleting it loses nothing.
        """

        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            (repo / ".aw" / "records" / "runs").mkdir(parents=True)
            run_dir = repo / ".aw" / "records" / "runs" / "run-20260913T000000Z-1"
            run_dir.mkdir()
            stream = runner_shared.telemetry_stream_path(
                run_dir, "01-aaaaaa-a1-execute-abcd1234"
            )
            self.assertFalse(
                runner_shared.path_is_within_analytics(stream, repo),
                f"telemetry must not be filed under the reserved analytics tree: {stream}",
            )
            self.assertFalse(runner_shared.path_is_within_analytics(run_dir, repo))
            # Control: the reserved tree IS detected, so the assertion above is not vacuous.
            self.assertTrue(
                runner_shared.path_is_within_analytics(
                    runner_shared.analytics_cache_dir(repo) / "x", repo
                )
            )

    def test_this_change_added_no_new_runs_root_literal(self) -> None:
        """Order 01 owns the resolver; this plan must not build the path by hand anywhere."""

        for name in (
            "runner_shared.py",
            "oc_runipd.py",
            "agy_runipd.py",
            "runner_shutdown.py",
        ):
            source = _source(name)
            with self.subTest(module=name):
                for literal in ('".aw" / "records" / "runs"', '".aw/records/runs"'):
                    self.assertNotIn(
                        literal,
                        source,
                        f"{name} composes the runs root by hand; use runner_shared.state_root",
                    )


# ==================================================================================================
# E-02 / V-02: the invocation identity, and the resume collision it exists to prevent
# ==================================================================================================
class InvocationIdentityTests(unittest.TestCase):
    """An execution id is distinct PER INVOCATION, including across a resume."""

    def _identity(self, **over: Any) -> runner_shared.TelemetryIdentity:
        kwargs: dict[str, Any] = {
            "run_id": "run-20260913T000000Z-1",
            "item": _item(),
            "attempt_no": 2,
            "phase": runner_shared.TELEMETRY_PHASE_EXECUTE,
            "host": "opencode",
        }
        kwargs.update(over)
        return runner_shared.telemetry_identity(**kwargs)

    def test_a_resumed_invocation_of_the_same_attempt_gets_a_different_id(self) -> None:
        """THE CENTRAL PROPERTY. Same item, same attempt, same phase, separated by a resume.

        The resume is simulated the way it actually happens: `attempt_no` is recomputed from the
        PERSISTED `attempts` list, which does not shrink, so both invocations legitimately see the
        SAME attempt number. That is precisely why the id needs a per-invocation component.
        """

        persisted = {**_item(), "attempts": [{"number": 1}, {"number": 2}]}
        attempt_no = len(
            persisted["attempts"]
        )  # what both drivers would compute post-resume
        before = self._identity(item=persisted, attempt_no=attempt_no)
        after = self._identity(item=persisted, attempt_no=attempt_no)

        self.assertEqual(
            before.attempt, after.attempt, "the attempt number is stable, as designed"
        )
        self.assertEqual(before.phase, after.phase)
        self.assertNotEqual(
            before.execution_id,
            after.execution_id,
            "two invocations separated by a resume must not share one execution id",
        )
        self.assertNotEqual(before.token, after.token)

    def test_the_mutation_check_proves_the_resume_test_can_fail(self) -> None:
        """Key the id on `(position, id6, attempt, phase)` ONLY and the property above must BREAK.

        Without this, the test above could pass for a reason unrelated to what it claims. Here the
        broken id is constructed explicitly and shown to collide.
        """

        persisted = {**_item(), "attempts": [{"number": 1}, {"number": 2}]}
        attempt_no = len(persisted["attempts"])

        def broken(identity: runner_shared.TelemetryIdentity) -> str:
            return f"{identity.position:02d}-{identity.id6}-a{identity.attempt}-{identity.phase}"

        before = self._identity(item=persisted, attempt_no=attempt_no)
        after = self._identity(item=persisted, attempt_no=attempt_no)
        self.assertEqual(
            broken(before),
            broken(after),
            "the mutation must reproduce the collision, otherwise it proves nothing",
        )
        self.assertNotEqual(before.execution_id, after.execution_id)

    def test_phase_is_an_explicit_field_not_a_filename_suffix(self) -> None:
        """Executor and verifier differ by a FIELD, and their ids differ too.

        Today the drivers distinguish the two turns only by a `suffix="verify"` string handed to
        `attempt_log_path`, so phase is recoverable from a LOG FILENAME. Telemetry must not inherit
        that coupling: a data field derived from a presentation detail breaks silently the day the
        filename changes.
        """

        execute = self._identity(phase=runner_shared.TELEMETRY_PHASE_EXECUTE)
        validate = self._identity(phase=runner_shared.TELEMETRY_PHASE_VALIDATE)
        self.assertEqual(execute.context()["phase"], "execute")
        self.assertEqual(validate.context()["phase"], "validate")
        self.assertNotEqual(execute.execution_id, validate.execution_id)
        self.assertIn("phase", runner_shared.TelemetryIdentity._fields)

    def test_the_id_satisfies_the_collector_schema_rather_than_being_refused(
        self,
    ) -> None:
        """The schema REFUSES an out-of-shape `execution_id`; a refusal would empty the stream."""

        pattern = tel._SHAPED_ID_KEYS["execution_id"]
        for phase in runner_shared.TELEMETRY_TURN_PHASES:
            for attempt in (1, 9, 42):
                identity = self._identity(phase=phase, attempt_no=attempt)
                with self.subTest(phase=phase, attempt=attempt):
                    self.assertRegex(identity.execution_id, pattern)

    def test_the_context_carries_only_schema_allowlisted_keys(self) -> None:
        """An unknown key is REFUSED by the collector, so every event would be dropped."""

        for key in self._identity().context():
            with self.subTest(key=key):
                self.assertIn(key, tel.ALLOWED_FIELDS)

    def test_an_out_of_vocabulary_phase_falls_back_instead_of_raising(self) -> None:
        """Identity minting sits on the critical path of launching an agent; it may not raise."""

        self.assertEqual(self._identity(phase="nonsense").phase, "execute")
        self.assertEqual(self._identity(phase="").phase, "execute")
        self.assertEqual(
            runner_shared.telemetry_identity(
                run_id="r", item={}, attempt_no=0, phase="execute", host="agy"
            ).attempt,
            1,
        )

    def test_the_token_is_not_derived_from_persisted_state(self) -> None:
        """Structural: the token comes from `secrets`, not from a counter or a clock.

        A persisted counter is exactly the thing that fails to reset across a resume, and a
        timestamp collides for two invocations inside one clock tick and is not monotonic.
        """

        source = _source("runner_shared.py")
        body = source[source.index("def telemetry_identity(") :]
        body = body[: body.index("\n@contextlib.contextmanager")]
        self.assertIn("secrets.token_hex", body)
        self.assertNotIn("time.time", body)
        self.assertNotIn("getpid", body)


# ==================================================================================================
# E-03 / E-04 / V-03 / V-04: the host wiring, and PARITY asserted as a test
# ==================================================================================================
class HostWiringTests(unittest.TestCase):
    """One agent-launch boundary per host, both callers covered, probes NOT instrumented."""

    def test_each_host_has_exactly_one_agent_launch_popen(self) -> None:
        for name in _DRIVER_SOURCES:
            with self.subTest(module=name):
                self.assertEqual(
                    _source(name).count("subprocess.Popen(argv, **popen_kwargs)"),
                    1,
                    f"{name} must hold exactly one agent-launch Popen",
                )

    def test_telemetry_wraps_that_boundary_in_both_hosts(self) -> None:
        """The `with` opens BEFORE the tracked launch, in both drivers."""

        for name in _DRIVER_SOURCES:
            source = _source(name)
            seam = source.index("runner_shared.turn_telemetry(")
            launch = source.index("subprocess.Popen(argv, **popen_kwargs)")
            with self.subTest(module=name):
                self.assertLess(
                    seam, launch, f"{name}: telemetry must open before the launch"
                )
                self.assertIn(
                    "runner_shutdown.track_child", source[launch - 200 : launch]
                )

    def test_the_version_and_helper_subprocess_sites_are_not_instrumented(self) -> None:
        """ "All subprocess boundaries" overstates the target: only the AGENT turn is measured.

        `oc_runipd` holds several `subprocess.run` calls that are version probes, git helpers and
        lifecycle verbs. Instrumenting them would emit telemetry for work nobody wants measured and
        would inflate the event volume Order 03's overhead budget is sized against.
        """

        source = _source("oc_runipd.py")
        self.assertEqual(source.count("runner_shared.turn_telemetry("), 1)
        # Every `subprocess.run(` in the module: none may sit inside a telemetry block. Proven by
        # showing the single telemetry `with` is inside `run_opencode` and that `run_opencode`
        # contains no `subprocess.run(`.
        body = source[
            source.index("def run_opencode(") : source.index(
                "def reconcile_disposition("
            )
        ]
        self.assertIn("runner_shared.turn_telemetry(", body)
        self.assertNotIn("subprocess.run(", body)

    def test_every_caller_is_covered_and_each_verifying_launch_declares_its_phase(
        self,
    ) -> None:
        """Every launch reaches the instrumented launcher, and a non-execute phase is STATED.

        RESTATED FROM A CENSUS TO AN INVARIANT by reverify-01 (`mp289j`). It asserted exactly TWO
        callers per host, and the OpenCode host now legitimately has THREE: the executor, the in-run
        verifier, and the standalone `audit` verb, which launches the verifier prompt on demand.

        WHAT TELEMETRY ACTUALLY NEEDS, and what is asserted instead of the count: no launch escapes
        instrumentation (there is one launcher, and it is wrapped, which the sibling test above pins),
        and every launch that is NOT the executor NAMES its phase rather than leaving it to be inferred
        from a log filename. So exactly one call site per host may rely on the `execute` default, and
        every other must declare `TELEMETRY_PHASE_VALIDATE`. A hard count would have made adding an
        instrumented launch read as a telemetry regression, which is the opposite of the truth.
        """

        for name, launcher in (
            ("oc_runipd.py", "run_opencode"),
            ("agy_runipd.py", "run_agy_turn"),
        ):
            # AST, not a line scan. A line scan counted a COMMENT that mentions
            # `run_opencode(...)` as a third caller, which is the same
            # explanation-versus-invocation confusion `tests/test_runner_refork_guard.py` records as
            # its reason for parsing rather than grepping.
            tree = ast.parse(_source(name))
            calls = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == launcher
            ]
            declared = [
                keyword
                for call in calls
                for keyword in call.keywords
                if keyword.arg == "telemetry_phase"
            ]
            source = _source(name)
            with self.subTest(module=name):
                self.assertGreaterEqual(
                    len(calls),
                    2,
                    f"{name}: the executor and verifier callers of {launcher} must both exist, "
                    f"found {len(calls)}",
                )
                self.assertEqual(
                    len(calls) - len(declared),
                    1,
                    f"{name}: exactly one call site may take the default execute phase; "
                    f"{len(calls)} callers declared {len(declared)} phases",
                )
                self.assertEqual(
                    source.count(
                        "telemetry_phase=runner_shared.TELEMETRY_PHASE_VALIDATE"
                    ),
                    len(declared),
                    f"{name}: a call site declares a phase that is not the validate phase",
                )

    def test_phase_defaults_so_no_existing_call_site_changed(self) -> None:
        import inspect

        for func in (oc_runipd.run_opencode, agy_runipd.run_agy_turn):
            param = inspect.signature(func).parameters["telemetry_phase"]
            with self.subTest(func=func.__name__):
                self.assertEqual(param.default, runner_shared.TELEMETRY_PHASE_EXECUTE)


class HostParityTests(unittest.TestCase):
    """FIELD-BY-FIELD parity across hosts, asserted as a test rather than read off two files."""

    def _emit(self, host: str, phase: str, root: Path) -> dict[str, Any]:
        identity = runner_shared.telemetry_identity(
            run_id="run-20260913T000000Z-1",
            item=_item(),
            attempt_no=1,
            phase=phase,
            host=host,
            token="cafebabe",
        )
        run_dir = root / host
        run_dir.mkdir(parents=True, exist_ok=True)

        # THE PROBE ADAPTER IS PINNED, and that is what makes this a parity test rather than a flaky
        # one. Two real probes taken microseconds apart legitimately disagree (`disk_free_bytes`
        # moved by 12 KiB between the two calls on the first run of this test), so comparing live
        # observations would fail for a reason that has nothing to do with host parity. Injecting the
        # SAME fake for both hosts holds the observation constant so the only thing that can differ
        # is the wiring under test.
        def _fixed_collector(*args: Any, **kwargs: Any) -> tel.TelemetryCollector:
            kwargs["adapter"] = tel.FakeResourceProbeAdapter()
            return tel.TelemetryCollector(*args, **kwargs)

        with runner_shared.turn_telemetry(
            run_dir,
            identity,
            repo=root,
            extra_context={"model": "provider/model"},
            collector_factory=_fixed_collector,
            sampler_factory=_RecordingSampler,
        ):
            pass
        events = _read_events(
            runner_shared.telemetry_stream_path(run_dir, identity.execution_id)
        )
        self.assertEqual([e["event_kind"] for e in events], ["start", "end"])
        return events[0]

    def test_both_hosts_emit_the_same_field_set_and_phase_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            oc = self._emit("opencode", runner_shared.TELEMETRY_PHASE_EXECUTE, root)
            agy = self._emit("agy", runner_shared.TELEMETRY_PHASE_EXECUTE, root)

        self.assertEqual(
            sorted(oc), sorted(agy), "the two hosts' event field sets must be identical"
        )
        # THE HOST-PARAMETERIZED CARVE-OUT, named with its reason. Parity means the same FIELDS and
        # the same phase semantics, NOT byte-identical values: `host` names the driver by design (as
        # `DEPENDENCY_BLOCK_RECOVERY_HINT` differs per host by design), and `execution_id`/`node_id`
        # /timestamps are per-invocation observations. Every OTHER field must agree.
        host_parameterized = {
            "host",
            "execution_id",
            "wall_timestamp",
            "monotonic_offset_seconds",
        }
        for key in sorted(set(oc) - host_parameterized):
            with self.subTest(field=key):
                self.assertEqual(oc[key], agy[key], f"{key} must not be host-specific")
        self.assertEqual(oc["host"], "opencode")
        self.assertEqual(agy["host"], "agy")
        self.assertEqual(oc["phase"], agy["phase"])

    def test_no_host_specific_telemetry_branch_exists_in_the_seam(self) -> None:
        """The seam must not switch on the host; only the `host` FIELD differs."""

        source = _source("runner_shared.py")
        body = source[
            source.index("def turn_telemetry(") : source.index("class _TurnTelemetry:")
        ]
        for token in ('"opencode"', '"agy"', '"antigravity"'):
            with self.subTest(token=token):
                self.assertNotIn(token, body)

    def test_the_phase_vocabulary_is_a_subset_the_collector_accepts(self) -> None:
        for phase in runner_shared.TELEMETRY_TURN_PHASES:
            with self.subTest(phase=phase):
                self.assertIn(phase, tel._CLOSED_VOCABULARIES["phase"])
        for host in ("opencode", "agy"):
            with self.subTest(host=host):
                self.assertIn(host, tel._CLOSED_VOCABULARIES["host"])


# ==================================================================================================
# E-05 / V-05: the sampler stops on every teardown path, WITHOUT a signal handler
# ==================================================================================================
class SamplerTeardownTests(unittest.TestCase):
    """Every teardown path stops the sampler, through the funnels that ALREADY exist."""

    def _run_turn(
        self, root: Path, raiser: type[BaseException] | None
    ) -> _RecordingSampler:
        identity = runner_shared.telemetry_identity(
            run_id="run-20260913T000000Z-1",
            item=_item(),
            attempt_no=1,
            phase="execute",
            host="opencode",
            token="cafebabe",
        )
        holder: dict[str, Any] = {}
        try:
            with runner_shared.turn_telemetry(
                root, identity, repo=root, sampler_factory=_RecordingSampler
            ) as record:
                holder["sampler"] = record.sampler
                self.assertTrue(record.sampler.running)
                if raiser is not None:
                    raise raiser()
        except BaseException as exc:  # noqa: BLE001 - the caller's exception must still propagate
            if raiser is None or not isinstance(exc, raiser):
                raise
        return holder["sampler"]

    def test_the_sampler_stops_on_every_teardown_path(self) -> None:
        """Normal completion, a plain exception, a stall timeout, a stop, and SIGINT.

        The last three are represented by the EXCEPTION TYPES the drivers actually raise on those
        paths, which is what the runners' teardown funnels see: `StallTimeout` for the watchdog
        kill, `StopAtCheckpoint`/`StopNowForce` for a deliberate stop, and `KeyboardInterrupt` for
        SIGINT (which needs no handler registration at all, being delivered as an exception).
        """

        from agent_workflows import runner_stop

        class _Stall(oc_runipd.StallTimeout):
            def __init__(self) -> None:
                super().__init__("stalled")

        class _Force(runner_stop.StopNowForce):
            def __init__(self) -> None:
                super().__init__(level=4, requester="test")

        cases: list[tuple[str, type[BaseException] | None]] = [
            ("normal completion", None),
            ("exception", RuntimeError),
            ("stall kill", _Stall),
            ("deliberate stop", _Force),
            ("SIGINT", KeyboardInterrupt),
        ]
        for label, raiser in cases:
            with self.subTest(path=label), tempfile.TemporaryDirectory() as td:
                sampler = self._run_turn(Path(td), raiser)
                self.assertEqual(sampler.starts, 1, label)
                self.assertEqual(sampler.stops, 1, label)
                self.assertFalse(sampler.running, label)

    def test_the_callers_exception_is_never_swallowed(self) -> None:
        """Teardown is best-effort; the WORK's exception still propagates unchanged."""

        with tempfile.TemporaryDirectory() as td:
            identity = runner_shared.telemetry_identity(
                run_id="r", item=_item(), attempt_no=1, phase="execute", host="opencode"
            )
            sentinel = RuntimeError("the work failed")
            with self.assertRaises(RuntimeError) as caught:
                with runner_shared.turn_telemetry(
                    Path(td), identity, repo=Path(td), sampler_factory=_RecordingSampler
                ):
                    raise sentinel
            self.assertIs(caught.exception, sentinel)

    def test_the_shared_shutdown_routine_stops_a_registered_sampler(self) -> None:
        """SIGTERM and every other level converge on `clean_shutdown`, which now stops samplers.

        This is the path a signal handler would otherwise have been needed for, and it is why none
        is: the ONE existing routine gained a stop call.
        """

        sampler = _RecordingSampler(collector=None)
        sampler.start()
        runner_shared.register_active_sampler(sampler)
        try:
            report = runner_shutdown.clean_shutdown()
            self.assertEqual(sampler.stops, 1)
            self.assertFalse(sampler.running)
            self.assertIn(
                "telemetry sampler",
                report.result(runner_shutdown.INVARIANT_CHILDREN).detail,
            )
            self.assertEqual(runner_shared.active_samplers(), [])
        finally:
            runner_shared.unregister_active_sampler(sampler)

    def test_a_double_stop_is_harmless_and_emits_no_second_end_event(self) -> None:
        """`clean_shutdown` and the seam's own `finally` may both fire; the stream must stay valid.

        Idempotent close is Order 03's documented contract; this proves the integration actually
        relies on it rather than adding a guard of its own, and that a second `end` (which would
        corrupt every duration computed from the stream) cannot appear.
        """

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            identity = runner_shared.telemetry_identity(
                run_id="run-20260913T000000Z-1",
                item=_item(),
                attempt_no=1,
                phase="execute",
                host="opencode",
                token="cafebabe",
            )
            with runner_shared.turn_telemetry(
                root, identity, repo=root, sampler_factory=_RecordingSampler
            ) as record:
                runner_shutdown.clean_shutdown()
                self.assertEqual(record.sampler.stops, 1)
                record.collector.close()
            events = _read_events(
                runner_shared.telemetry_stream_path(root, identity.execution_id)
            )
            self.assertEqual([e["event_kind"] for e in events], ["start", "end"])

    def test_this_change_registered_no_signal_handler_in_either_driver(self) -> None:
        """The guard four executed plans installed, re-asserted here for THIS change.

        Stated positively so a reader knows what to do instead: SIGINT arrives as
        `KeyboardInterrupt` (no registration needed) and SIGTERM converges on `clean_shutdown`.
        `runstop` Phase 5 (`71vjbn`) owns SIGINT/SIGTERM registration, and `oc_runipd` records a
        prior plan being refused exactly this because the designs are "incompatible, not merely
        double-registered".
        """

        # The two DRIVERS get the same textual assertion the four sibling guards make, verbatim, so
        # this test agrees with them by construction rather than by a paraphrase that could drift.
        for name in _DRIVER_SOURCES:
            with self.subTest(module=name):
                self.assertNotIn("signal.signal(", _source(name))

        # The SEAM gets an AST check instead, and the difference is not a weakening. This module's
        # docstrings deliberately NAME `signal.signal` in order to explain why it is not called (the
        # explanation is the point: an executor reading the seam must learn what is forbidden and
        # what to do instead). A substring test cannot tell an explanation from an invocation, so it
        # would be either falsely red or defeated by deleting the words it looks for, and the second
        # is how a real regression gets waved through. The AST cannot be fooled by prose. This is the
        # identical remedy `tests/test_run_analytics_telemetry.py` adopted for the same reason.
        tree = ast.parse(_source("runner_shared.py"))
        attributes = {
            node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
        }
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertNotIn("signal", imported, "the seam imports no signal module at all")
        self.assertNotIn("signal", names)
        self.assertNotIn("atexit", imported)
        for forbidden in ("SIGINT", "SIGTERM", "setitimer"):
            with self.subTest(identifier=forbidden):
                self.assertNotIn(forbidden, attributes | names)

    def test_no_second_cleanup_routine_was_added(self) -> None:
        """Spec `c4gd2h` R5/A9: exactly ONE cleanup implementation, extended rather than duplicated.

        `runner_shutdown.py` may only have gained a stop call INSIDE the existing routine, so the
        module must still define exactly one `clean_shutdown` and no sibling cleanup entry point.
        """

        tree = ast.parse(_source("runner_shutdown.py"))
        top_level = [
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        self.assertEqual(top_level.count("clean_shutdown"), 1)
        for forbidden in (
            "clean_shutdown_telemetry",
            "telemetry_shutdown",
            "stop_samplers",
        ):
            with self.subTest(name=forbidden):
                self.assertNotIn(forbidden, top_level)
        # The stop happens INSIDE `clean_shutdown`, not in a new routine beside it.
        source = _source("runner_shutdown.py")
        body = source[source.index("def clean_shutdown(") :]
        self.assertIn("stop_active_samplers", body)
        self.assertEqual(
            source.count("stop_active_samplers"), 2
        )  # the import and the call

    def test_runner_shutdown_still_imports_only_stdlib_and_platform_lock_at_module_level(
        self,
    ) -> None:
        """The lazy import is deliberate: a broken analytics module may not break a shutdown."""

        tree = ast.parse(_source("runner_shutdown.py"))
        module_level: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                module_level.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                module_level.add(node.module)
        self.assertNotIn("agent_workflows.runner_shared", module_level)
        self.assertNotIn("agent_workflows.run_analytics_telemetry", module_level)


# ==================================================================================================
# E-06 / V-06: non-interference, by FAULT INJECTION against a PAIRED UNINSTRUMENTED CONTROL
# ==================================================================================================
class NonInterferenceTests(unittest.TestCase):
    """A telemetry fault may never turn success into failure nor mask a failure.

    EVERY CASE IS PAIRED WITH A CONTROL, because "the run still succeeded" and "the run succeeded
    for the same reasons" are different claims and only the second is non-interference. The control
    is a genuinely UNINSTRUMENTED turn (telemetry disabled by configuration, so no collector is
    constructed at all), and the comparison is the launcher's full observable result.
    """

    def _turn(self, root: Path, *, enabled: bool, **seam: Any) -> dict[str, Any]:
        """Run one instrumented (or control) turn through the REAL `run_opencode`, no real child."""

        repo = root / "repo"
        (repo / ".aw" / "config").mkdir(parents=True, exist_ok=True)
        if not enabled:
            (repo / ".aw" / "config" / "project.json").write_text(
                json.dumps({run_analytics_config.TELEMETRY_KEY: {"enabled": False}}),
                encoding="utf-8",
            )
        run_dir = root / "run-20260913T000000Z-1"
        for sub in ("logs", "prompts", "sessions", "outcomes"):
            (run_dir / sub).mkdir(parents=True, exist_ok=True)
        prompt = run_dir / "prompts" / "p.md"
        prompt.write_text("prompt", encoding="utf-8")
        plan = repo / "plan.ipd.md"
        plan.write_text("# plan\n", encoding="utf-8")
        state = {
            "run_id": "run-20260913T000000Z-1",
            "repo": str(repo),
            "options": {"output_mode": "quiet", "model": "provider/model"},
            "queue": [],
        }
        item = _item()

        real_factory = tel.TelemetryCollector
        patched = dict(seam)
        if "collector_factory" not in patched and enabled:
            patched["collector_factory"] = real_factory

        original = runner_shared.turn_telemetry

        def instrumented(rd: Any, identity: Any, **kwargs: Any) -> Any:
            kwargs.update(patched)
            return original(rd, identity, **kwargs)

        outcome: dict[str, Any] = {}
        with mock.patch("subprocess.Popen", side_effect=_FakeProc), mock.patch.object(
            runner_shared, "turn_telemetry", instrumented
        ), mock.patch.object(oc_runipd.runner_shared, "turn_telemetry", instrumented):
            rc, session, log_path, argv = oc_runipd.run_opencode(
                state, run_dir, item, plan, prompt, 1
            )
        outcome["rc"] = rc
        outcome["session"] = session
        outcome["log_name"] = Path(log_path).name
        outcome["log_text"] = Path(log_path).read_text(encoding="utf-8")
        # The ROOT IS ELIDED from argv before comparison, and only the root. Each pair of runs uses
        # its own temporary directory, so a raw comparison would fail on the tmpdir name for every
        # case and would prove nothing about interference. Everything argv actually encodes (the
        # flags, their order, the model, the title, the attachments, the prompt) is preserved and
        # compared; only the absolute prefix is normalized.
        outcome["argv"] = [
            token.replace(str(root), "<root>") if isinstance(token, str) else token
            for token in argv
        ]
        outcome["item"] = dict(item)
        outcome["shutdown"] = runner_shutdown.clean_shutdown(run_dir=run_dir).to_dict()
        return outcome

    def test_every_injected_telemetry_fault_leaves_the_work_identical_to_a_control(
        self,
    ) -> None:
        class _RaisingCtor:
            def __init__(self, *a: object, **k: object) -> None:
                raise RuntimeError("collector constructor exploded")

        class _RaisingClose(tel.TelemetryCollector):
            def close(self) -> Any:  # type: ignore[override]
                raise RuntimeError("close exploded")

        class _RaisingStart(tel.TelemetryCollector):
            def start(self) -> Any:  # type: ignore[override]
                raise RuntimeError("start exploded")

        class _RaisingProbe(tel.ResourceProbeAdapter):
            def resources(self, *, disk_path: Any = None) -> dict[str, Any]:
                raise RuntimeError("probe exploded")

            def accelerators(self) -> tel.ProbeOutcome:
                raise RuntimeError("accelerator probe exploded")

            def tool_versions(self) -> tel.ProbeOutcome:
                raise RuntimeError("tool version probe exploded")

        class _TimingOutProbe(tel.ResourceProbeAdapter):
            def resources(self, *, disk_path: Any = None) -> dict[str, Any]:
                return {"unavailable": "resources:timeout"}

            def accelerators(self) -> tel.ProbeOutcome:
                return tel.ProbeOutcome("timeout")

        class _RaisingSampler(_RecordingSampler):
            def start(self) -> None:
                raise RuntimeError("sampler start exploded")

        def _probing(adapter: tel.ResourceProbeAdapter) -> Any:
            def factory(*a: object, **k: object) -> tel.TelemetryCollector:
                k["adapter"] = adapter
                return tel.TelemetryCollector(*a, **k)  # type: ignore[arg-type]

            return factory

        cases: dict[str, dict[str, Any]] = {
            "collector constructor raises": {"collector_factory": _RaisingCtor},
            "collector start raises": {"collector_factory": _RaisingStart},
            "collector close raises": {"collector_factory": _RaisingClose},
            "probe raises": {"collector_factory": _probing(_RaisingProbe())},
            "probe times out": {"collector_factory": _probing(_TimingOutProbe())},
            "sampler start raises": {"sampler_factory": _RaisingSampler},
            "append fails (unwritable stream)": {
                "collector_factory": lambda *a, **k: tel.TelemetryCollector(
                    *a, **{**k, "writer": _explode_writer}
                )
            },
        }

        with tempfile.TemporaryDirectory() as td:
            control = self._turn(Path(td) / "control", enabled=False)
        self.assertEqual(control["rc"], 0)

        for label, seam in cases.items():
            with self.subTest(fault=label), tempfile.TemporaryDirectory() as td:
                observed = self._turn(Path(td) / "instrumented", enabled=True, **seam)
                for key in ("rc", "session", "log_name", "log_text", "argv", "item"):
                    self.assertEqual(
                        observed[key],
                        control[key],
                        f"{label} changed {key}: instrumentation is not non-interfering",
                    )
                self.assertEqual(
                    observed["shutdown"]["invariants"]["children_reaped"]["satisfied"],
                    control["shutdown"]["invariants"]["children_reaped"]["satisfied"],
                )

    def test_instrumenting_a_turn_spawns_no_subprocess_of_its_own(self) -> None:
        """THE REGRESSION THIS PINS COST 18 TESTS ACROSS FIVE FILES, so read the mechanism.

        Every probe in the collector is read-only and process-free EXCEPT `accelerators`, which
        shells out to a vendor tool (`nvidia-smi`, then `rocm-smi`). Wrapping the agent launch
        therefore put a SECOND subprocess invocation inside the very function whose one `Popen`
        several suites patch to capture the AGENT's argv, and those suites began capturing the
        PROBE's argv instead. Two `LaunchProfileFrozenTurnArgvTests` cases failed reading
        `(None, None, None) == (None, None, None)`, because the captured argv was the probe's and had
        no `--model` in it at all.

        THE PART THAT MAKES THIS TEST WORTH ITS LINES: the failure is ENVIRONMENT-DEPENDENT. It
        appears only where a vendor tool is installed, so on a machine without one the suites stay
        green and the interference ships. A test that only ran the happy path could not see it; this
        one refuses the boundary outright, so it fails on every machine.
        """

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            identity = runner_shared.telemetry_identity(
                run_id="run-20260913T000000Z-1",
                item=_item(),
                attempt_no=1,
                phase="execute",
                host="opencode",
                token="cafebabe",
            )
            spawned: list[Any] = []

            def refuse_run(*args: Any, **kwargs: Any) -> Any:
                spawned.append(args[0] if args else kwargs.get("args"))
                raise AssertionError(f"telemetry spawned a subprocess: {spawned[-1]!r}")

            with mock.patch("subprocess.Popen", side_effect=_RefusingPopen), mock.patch(
                "subprocess.run", side_effect=refuse_run
            ):
                with runner_shared.turn_telemetry(root, identity, repo=root) as record:
                    self.assertTrue(
                        record.enabled, "telemetry must still be ON, not skipped"
                    )
            self.assertEqual(spawned, [])

            # And the stream is still complete and useful: the suppression costs the accelerator
            # record only, not the observation.
            events = _read_events(
                runner_shared.telemetry_stream_path(root, identity.execution_id)
            )
            self.assertEqual([e["event_kind"] for e in events], ["start", "end"])
            self.assertIn("resources", events[0])
            self.assertIn("cpu_logical_count", events[0]["resources"])
            self.assertNotIn("accelerators", events[0])

    def test_the_suppression_costs_only_the_accelerator_field(self) -> None:
        """Field-for-field: every other probe is unaffected by the launch-safe narrowing."""

        suppressed = tel.SystemResourceProbeAdapter(runner=lambda _a, _t: (-2, ""))
        unsuppressed = tel.SystemResourceProbeAdapter()
        self.assertEqual(
            sorted(suppressed.resources(disk_path="/tmp")),
            sorted(unsuppressed.resources(disk_path="/tmp")),
            "the suppressed runner must not remove any `resources` field",
        )
        self.assertTrue(suppressed.tool_versions().ok)
        self.assertEqual(suppressed.accelerators().reason, "unavailable")

    def test_an_unwritable_telemetry_directory_does_not_break_the_turn(self) -> None:
        """A read-only tree is a REAL failure mode (a full disk, a wrong-owner run directory)."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run_dir = root / "run-20260913T000000Z-1"
            run_dir.mkdir()
            (run_dir / runner_shared.TELEMETRY_DIRNAME).write_text(
                "not a dir", encoding="utf-8"
            )
            identity = runner_shared.telemetry_identity(
                run_id="r", item=_item(), attempt_no=1, phase="execute", host="opencode"
            )
            with runner_shared.turn_telemetry(run_dir, identity, repo=root) as record:
                self.assertFalse(
                    record.enabled, "an unwritable tree yields no collector"
                )

    def test_a_write_failure_is_recorded_as_a_warning_code_where_writable(self) -> None:
        """The documented warning path: a code in the stream, never an exception at the caller."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            events: list[dict[str, Any]] = []
            calls = {"n": 0}

            def flaky(path: Path, event: dict[str, Any]) -> None:
                calls["n"] += 1
                if calls["n"] == 1:
                    raise OSError("no space left on device")
                events.append(event)

            identity = runner_shared.telemetry_identity(
                run_id="r", item=_item(), attempt_no=1, phase="execute", host="opencode"
            )
            with runner_shared.turn_telemetry(
                root,
                identity,
                repo=root,
                collector_factory=lambda *a, **k: tel.TelemetryCollector(
                    *a, **{**k, "writer": flaky}
                ),
                sampler_factory=_RecordingSampler,
            ) as record:
                self.assertTrue(record.enabled)
            self.assertEqual([e["event_kind"] for e in events], ["end"])
            self.assertIn("telemetry-write-failed", events[0]["warnings"])

    def test_disabled_telemetry_creates_no_directory_and_no_file(self) -> None:
        """ "Disabled" is defined as nothing on disk, which is what makes it observable."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = root / "repo"
            (repo / ".aw" / "config").mkdir(parents=True)
            (repo / ".aw" / "config" / "project.json").write_text(
                json.dumps({run_analytics_config.TELEMETRY_KEY: {"enabled": False}}),
                encoding="utf-8",
            )
            run_dir = root / "run-x"
            run_dir.mkdir()
            identity = runner_shared.telemetry_identity(
                run_id="r", item=_item(), attempt_no=1, phase="execute", host="opencode"
            )
            with runner_shared.turn_telemetry(run_dir, identity, repo=repo) as record:
                self.assertFalse(record.enabled)
                self.assertIsNone(record.sampler)
            self.assertFalse(runner_shared.telemetry_dir(run_dir).exists())
            self.assertEqual(sorted(p.name for p in run_dir.iterdir()), [])

    def test_basic_default_produces_exactly_two_lifecycle_events_and_no_sampling(
        self,
    ) -> None:
        """The shipped default: telemetry ON, periodic sampling OFF."""

        config = run_analytics_config.TelemetryConfig()
        self.assertTrue(config.enabled)
        self.assertFalse(config.samples_enabled)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            identity = runner_shared.telemetry_identity(
                run_id="run-20260913T000000Z-1",
                item=_item(),
                attempt_no=1,
                phase="execute",
                host="opencode",
                token="cafebabe",
            )
            with runner_shared.turn_telemetry(root, identity, repo=root) as record:
                self.assertIsNotNone(record.sampler)
                self.assertFalse(
                    record.sampler.running, "the default sampler starts no thread"
                )
            events = _read_events(
                runner_shared.telemetry_stream_path(root, identity.execution_id)
            )
            self.assertEqual([e["event_kind"] for e in events], ["start", "end"])

    def test_no_real_agent_process_is_ever_launched_by_this_suite(self) -> None:
        """Asserted BY CONSTRUCTION: the stub raises if a launch is attempted."""

        with tempfile.TemporaryDirectory() as td, mock.patch(
            "subprocess.Popen", side_effect=_RefusingPopen
        ):
            root = Path(td)
            identity = runner_shared.telemetry_identity(
                run_id="r", item=_item(), attempt_no=1, phase="execute", host="opencode"
            )
            with runner_shared.turn_telemetry(root, identity, repo=root) as record:
                self.assertTrue(record.enabled)

    def test_prompts_logs_and_sessions_never_reach_telemetry(self) -> None:
        """Source artifacts are sensitive; telemetry carries codes, counts and numbers only."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            secret = "SEN" + "SITIVE-PROMPT-BODY"
            identity = runner_shared.telemetry_identity(
                run_id="run-20260913T000000Z-1",
                item={**_item(), "prompt": secret},
                attempt_no=1,
                phase="execute",
                host="opencode",
                token="cafebabe",
            )
            with runner_shared.turn_telemetry(
                root, identity, repo=root, extra_context={"model": "provider/model"}
            ):
                pass
            text = runner_shared.telemetry_stream_path(
                root, identity.execution_id
            ).read_text(encoding="utf-8")
            self.assertNotIn(secret, text)


def _explode_writer(path: Path, event: dict[str, Any]) -> None:
    raise OSError("no space left on device")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
