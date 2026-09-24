"""Tests for the incremental per-run analytics cache (IPD bzz5e6, Set runanalytics).

Covers E-01 (envelope + strict loader), E-02 (deterministic fingerprint + freshness verdicts),
E-05 (locking, atomic publication, corruption isolation, busy-lock skip), E-03 (machine-readable
decisions) and E-06's failure-mode half (mutation, concurrency, corruption, idempotence, numeric
conservation).

Two conventions this suite holds itself to. FIRST, no sensitive literal is committed: the few
canaries are assembled from fragments at runtime, as the detection engine does with its own
patterns. SECOND, freshness is asserted against SYNTHETIC run directories built here rather than
against the live corpus, because the live corpus is mutable and gitignored; the one place the real
corpus is consulted, it is treated as read-only and skipped when absent.

Stdlib unittest only.
"""

from __future__ import annotations

import json
import multiprocessing
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from agent_workflows import leak_sanitizer as ls
from agent_workflows import platform_lock
from agent_workflows import run_analytics_cache as cache
from agent_workflows import run_analytics_privacy as privacy
from tests.support import REPO_ROOT

_HANDLE = "gfa" + "riello"
_HOME_PATH = "/ho" + "me/" + _HANDLE + "/VC/agent-workflows"
_PROMPT_BODY = "You are an agent. " + "Implement E-01 exactly as written."

_SALT = "0" * 64


def _make_repo(tmp: Path) -> Path:
    """A minimal repository whose runs root the Order-01 resolver will resolve to."""

    repo = tmp / "repo"
    (repo / ".aw" / "records" / "runs").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "config").mkdir(parents=True, exist_ok=True)
    return repo


def _write_run(
    runs_root: Path,
    run_id: str,
    *,
    terminal: bool = True,
    events: int = 3,
    cost: float = 1.25,
) -> Path:
    """A synthetic run directory in the shape the drivers write."""

    run_dir = runs_root / run_id
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    state = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T01:00:00Z",
        # A real state.json carries an absolute maintainer path here. Kept as a canary on purpose:
        # it is the FIRST field an ingester reads, so the projector must never let it through.
        "repo": _HOME_PATH,
        "queue": [
            {
                "position": 1,
                "id6": "aaa111",
                "status": "executed" if terminal else "running",
            }
        ],
    }
    (run_dir / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    lines = [
        json.dumps({"type": "turn", "seq": i, "cost": cost, "prompt": _PROMPT_BODY})
        for i in range(events)
    ]
    (run_dir / "events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (run_dir / "outcomes" / "01-aaa111.json").write_text(
        json.dumps({"disposition": "executed", "cost": cost}), encoding="utf-8"
    )
    # Churn files that must NOT participate in freshness.
    (run_dir / "execution-report.md").write_text("# report\n", encoding="utf-8")
    return run_dir


def _facts_builder(cost: float = 1.25, tokens: dict | None = None):
    """A stand-in fact producer. Parsing is Order 05's job; this suite only needs valid facts.

    It nonetheless READS the analytics-relevant sources, because that is what a real producer does
    and it is what makes the "a cached pass reads fewer source files" measurement honest rather
    than tautological.
    """

    def build(run_dir: Path):
        (run_dir / "state.json").read_text(encoding="utf-8")
        (run_dir / "events.jsonl").read_text(encoding="utf-8")
        for outcome in sorted((run_dir / "outcomes").glob("*.json")):
            outcome.read_text(encoding="utf-8")
        metric = {
            "run_id": run_dir.name,
            "cost": cost,
            "cost_currency": "USD",
            "tokens": tokens or {"input": 100, "output": 20, "cache": 5, "total": 125},
            "token_total": 125,
            "duration_seconds": 3600.0,
            "phase": "execute",
            "outcome": "executed",
            "event_count": 3,
        }
        events = [
            {
                "event_type": "turn",
                "sequence": 0,
                "cost": cost,
                "payload_byte_count": 128,
            },
        ]
        return metric, events, ["parsed-clean"], []

    return build


def _envelope(run_dir: Path, root_id: str, **kw) -> cache.CacheEnvelope:
    metric, events, flags, warns = _facts_builder()(run_dir)
    return cache.build_entry(
        run_id=run_dir.name,
        root_id=root_id,
        run_dir=run_dir,
        metric_facts=metric,
        event_facts=events,
        quality_flags=flags,
        warnings=warns,
        **kw,
    )


def _root_id() -> str:
    return privacy.pseudonymize("/runs/root", salt=_SALT, domain="root")


# ================================================================= E-01: envelope + strict loader
class EnvelopeRoundTripTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.repo = _make_repo(self.tmp)
        self.runs = self.repo / ".aw" / "records" / "runs"
        self.root_id = _root_id()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_envelope_records_every_contracted_member(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-1")
        env = _envelope(run_dir, self.root_id)
        payload = cache.encode_envelope(env)
        self.assertEqual(
            sorted(payload),
            sorted(cache.ENVELOPE_FIELDS),
            "the envelope contract changed",
        )
        self.assertEqual(payload["schema_version"], cache.CACHE_SCHEMA_VERSION)
        self.assertTrue(payload["source_fingerprint"].startswith("sha256:"))
        self.assertTrue(payload["is_complete"])
        self.assertEqual(payload["source_coverage"]["file_count"], 3)

    def test_round_trip_conserves_every_numeric_fact_exactly(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-2")
        metric = {
            "cost": 0.4213,  # float
            "token_total": 125,  # int
            "duration_seconds": 3600.5,  # float
            "tokens": {
                "input": 100,
                "output": 20,
                "cache": 5,
                "reasoning": 7,
                "total": 132,
            },
            "event_count": 42,
            "cost_currency": "USD",
        }
        env = cache.build_entry(
            run_id=run_dir.name,
            root_id=self.root_id,
            run_dir=run_dir,
            metric_facts=metric,
        )
        decoded = cache.decode_envelope(
            json.loads(json.dumps(cache.encode_envelope(env)))
        )
        for key in ("cost", "token_total", "duration_seconds", "event_count"):
            with self.subTest(fact=key):
                self.assertEqual(
                    decoded.metric_facts[key],
                    metric[key],
                    f"{key} was not conserved exactly: "
                    f"before={metric[key]!r} after={decoded.metric_facts[key]!r}",
                )
        self.assertEqual(decoded.metric_facts["tokens"], metric["tokens"])
        self.assertIsInstance(decoded.metric_facts["token_total"], int)
        self.assertIsInstance(decoded.metric_facts["cost"], float)

    def test_unknown_envelope_field_is_refused_and_named_not_dropped(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-3")
        payload = cache.encode_envelope(_envelope(run_dir, self.root_id))
        payload["surprise_field"] = "anything"
        with self.assertRaises(cache.CacheEnvelopeError) as ctx:
            cache.decode_envelope(payload)
        message = str(ctx.exception)
        self.assertIn(
            "surprise_field", message, "the diagnostic must NAME the offending key"
        )
        self.assertIn("refused rather than dropped", message)

    def test_a_drop_would_have_passed_so_the_refusal_is_the_assertion(self) -> None:
        """Distinguishes REFUSE from DROP: a dropping loader would return a valid envelope here."""

        run_dir = _write_run(self.runs, "run-20260101T000000Z-4")
        payload = cache.encode_envelope(_envelope(run_dir, self.root_id))
        payload["extra"] = 1
        try:
            cache.decode_envelope(payload)
        except cache.CacheEnvelopeError:
            return
        self.fail(
            "decode_envelope silently accepted an unknown field (a drop, not a refusal)"
        )

    def test_future_schema_version_is_refused_with_a_forward_compatible_diagnostic(
        self,
    ) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-5")
        payload = cache.encode_envelope(_envelope(run_dir, self.root_id))
        payload["schema_version"] = cache.CACHE_SCHEMA_VERSION + 1
        with self.assertRaises(cache.CacheVersionError) as ctx:
            cache.decode_envelope(payload)
        message = str(ctx.exception)
        self.assertIn("NEWER", message)
        self.assertIn("refusing to misparse", message)

    def test_past_schema_version_is_refused_as_a_rebuild_not_a_migration(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-6")
        payload = cache.encode_envelope(_envelope(run_dir, self.root_id))
        payload["schema_version"] = 0
        with self.assertRaises(cache.CacheVersionError) as ctx:
            cache.decode_envelope(payload)
        self.assertIn("rebuilding rather than migrating", str(ctx.exception))

    def test_missing_required_field_is_refused(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-7")
        payload = cache.encode_envelope(_envelope(run_dir, self.root_id))
        del payload["metric_facts"]
        with self.assertRaises(cache.CacheEnvelopeError) as ctx:
            cache.decode_envelope(payload)
        self.assertIn("metric_facts", str(ctx.exception))

    def test_a_hand_edited_entry_cannot_reintroduce_a_forbidden_field(self) -> None:
        """The read path re-projects, because a cache file on disk can be edited."""

        run_dir = _write_run(self.runs, "run-20260101T000000Z-8")
        payload = cache.encode_envelope(_envelope(run_dir, self.root_id))
        payload["metric_facts"]["repo"] = _HOME_PATH
        with self.assertRaises(privacy.PrivacyRefusal):
            cache.decode_envelope(payload)


# ============================================================ E-02: fingerprint + freshness verdict
class FingerprintTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.repo = _make_repo(self.tmp)
        self.runs = self.repo / ".aw" / "records" / "runs"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_fingerprint_is_repeatable_for_unchanged_inputs(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-10")
        self.assertEqual(
            cache.source_fingerprint(run_dir), cache.source_fingerprint(run_dir)
        )

    def test_fingerprint_is_byte_identical_across_separate_processes(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-11")
        code = (
            "import sys;"
            "sys.path.insert(0, %r);"
            "from agent_workflows import run_analytics_cache as c;"
            "print(c.source_fingerprint(%r))" % (str(REPO_ROOT), str(run_dir))
        )
        outs = []
        for _ in range(2):
            proc = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                cwd=str(self.repo),
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            outs.append(proc.stdout.strip())
        self.assertEqual(outs[0], outs[1])
        self.assertEqual(
            outs[0],
            cache.source_fingerprint(run_dir),
            "the fingerprint must be identical in a separate process, not merely repeatable here",
        )

    def test_mutating_an_analytics_input_changes_the_fingerprint(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-12")
        before = cache.source_fingerprint(run_dir)
        events = run_dir / "events.jsonl"
        events.write_text(events.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")
        self.assertNotEqual(before, cache.source_fingerprint(run_dir))

    def test_churn_in_an_irrelevant_file_does_not_change_the_fingerprint(self) -> None:
        """Otherwise the driver's own report rewrite would defeat the cache entirely."""

        run_dir = _write_run(self.runs, "run-20260101T000000Z-13")
        before = cache.source_fingerprint(run_dir)
        (run_dir / "execution-report.md").write_text(
            "# rewritten\n\nmore\n", encoding="utf-8"
        )
        self.assertEqual(before, cache.source_fingerprint(run_dir))

    def test_directory_mtime_alone_would_have_been_insufficient(self) -> None:
        """A same-size in-place edit leaves the DIRECTORY mtime untouched; the digest still moves."""

        run_dir = _write_run(self.runs, "run-20260101T000000Z-14")
        dir_mtime_before = run_dir.stat().st_mtime_ns
        before = cache.source_fingerprint(run_dir)
        state = run_dir / "state.json"
        text = state.read_text(encoding="utf-8")
        time.sleep(0.01)
        state.write_text(
            text.replace('"position": 1', '"position": 2'), encoding="utf-8"
        )
        self.assertEqual(
            dir_mtime_before,
            run_dir.stat().st_mtime_ns,
            "precondition: an in-place edit must not change the directory mtime",
        )
        self.assertNotEqual(before, cache.source_fingerprint(run_dir))

    def test_terminal_state_participates_in_the_fingerprint(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-15", terminal=False)
        live = cache.source_fingerprint(run_dir)
        self.assertFalse(cache.run_is_terminal(run_dir))
        state = run_dir / "state.json"
        payload = json.loads(state.read_text(encoding="utf-8"))
        payload["queue"][0]["status"] = "executed"
        state.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.assertTrue(cache.run_is_terminal(run_dir))
        self.assertNotEqual(live, cache.source_fingerprint(run_dir))

    def test_a_held_driver_lock_makes_a_run_non_terminal(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-16")
        self.assertTrue(cache.run_is_terminal(run_dir))
        handle = platform_lock.acquire(run_dir / "driver.lock")
        try:
            self.assertFalse(
                cache.run_is_terminal(run_dir),
                "a live driver.lock holder means the run can still write",
            )
        finally:
            handle.release()


class FreshnessVerdictTests(unittest.TestCase):
    """Every required case from the plan, each with the reason code a consumer sees."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.repo = _make_repo(self.tmp)
        self.runs = self.repo / ".aw" / "records" / "runs"
        self.root_id = _root_id()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _decide(self, run_dir: Path):
        return cache.decide(run_dir, root_id=self.root_id, repo=self.repo)

    def _publish(self, run_dir: Path, **kw) -> None:
        env = _envelope(run_dir, self.root_id, **kw)
        cache._publish(env, repo=self.repo)

    def test_first_scan_is_a_rebuild_with_no_entry(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-20")
        decision, envelope = self._decide(run_dir)
        self.assertEqual((decision.verdict, decision.reason), ("rebuild", "no-entry"))
        self.assertIsNone(envelope)

    def test_unchanged_completed_run_is_a_hit(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-21")
        self._publish(run_dir)
        decision, envelope = self._decide(run_dir)
        self.assertEqual(
            (decision.verdict, decision.reason), ("hit", "fresh-complete-entry")
        )
        assert envelope is not None, "a hit must return the reusable envelope"
        self.assertEqual(envelope.run_id, run_dir.name)

    def test_mutated_run_rebuilds_with_fingerprint_changed(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-22")
        self._publish(run_dir)
        events = run_dir / "events.jsonl"
        events.write_text(events.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")
        decision, _ = self._decide(run_dir)
        self.assertEqual(
            (decision.verdict, decision.reason), ("rebuild", "fingerprint-changed")
        )

    def test_in_progress_run_is_never_a_stable_hit(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-23", terminal=False)
        self._publish(run_dir)
        decision, envelope = self._decide(run_dir)
        self.assertEqual(
            (decision.verdict, decision.reason), ("rebuild", "run-not-terminal")
        )
        self.assertIsNone(envelope)

    def test_a_resumed_run_reusing_its_directory_rebuilds(self) -> None:
        """The case directory mtime and even a matching fingerprint cannot catch."""

        run_dir = _write_run(self.runs, "run-20260101T000000Z-24")
        self._publish(run_dir)
        self.assertEqual(self._decide(run_dir)[0].verdict, "hit")
        state = run_dir / "state.json"
        payload = json.loads(state.read_text(encoding="utf-8"))
        payload["queue"][0]["status"] = "running"  # resumed IN PLACE
        state.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        decision, _ = self._decide(run_dir)
        self.assertEqual(
            (decision.verdict, decision.reason), ("rebuild", "run-not-terminal")
        )

    def test_an_entry_cached_mid_run_is_not_reused_when_the_run_completes(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-25")
        self._publish(run_dir, is_complete=False)
        decision, _ = self._decide(run_dir)
        self.assertEqual(
            (decision.verdict, decision.reason), ("rebuild", "entry-incomplete")
        )

    def test_added_run_rebuilds_and_existing_runs_stay_hits(self) -> None:
        first = _write_run(self.runs, "run-20260101T000000Z-26")
        self._publish(first)
        second = _write_run(self.runs, "run-20260101T000000Z-27")
        self.assertEqual(self._decide(first)[0].verdict, "hit")
        self.assertEqual(self._decide(second)[0].reason, "no-entry")

    def test_removed_run_leaves_the_other_entries_intact(self) -> None:
        first = _write_run(self.runs, "run-20260101T000000Z-28")
        second = _write_run(self.runs, "run-20260101T000000Z-29")
        self._publish(first)
        self._publish(second)
        import shutil

        shutil.rmtree(second)
        self.assertEqual(self._decide(first)[0].verdict, "hit")
        self.assertFalse(second.exists())

    def test_schema_version_change_rebuilds(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-30")
        self._publish(run_dir)
        target = cache.entry_path(self.root_id, run_dir.name, self.repo)
        payload = json.loads(target.read_text(encoding="utf-8"))
        payload["schema_version"] = cache.CACHE_SCHEMA_VERSION + 1
        target.write_text(json.dumps(payload), encoding="utf-8")
        decision, _ = self._decide(run_dir)
        self.assertEqual(
            (decision.verdict, decision.reason), ("rebuild", "schema-version-mismatch")
        )

    def test_corrupt_entry_rebuilds_rather_than_raising(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-31")
        self._publish(run_dir)
        target = cache.entry_path(self.root_id, run_dir.name, self.repo)
        target.write_text("{not json at all", encoding="utf-8")
        decision, _ = self._decide(run_dir)
        self.assertEqual(
            (decision.verdict, decision.reason), ("rebuild", "entry-unreadable")
        )

    def test_every_emitted_reason_is_a_declared_code(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-32")
        for reason in (self._decide(run_dir)[0].reason,):
            self.assertIn(reason, cache.REASON_CODES)


# ================================================== E-05: publication safety, locking, corruption
class PublicationSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.repo = _make_repo(self.tmp)
        self.runs = self.repo / ".aw" / "records" / "runs"
        self.root_id = _root_id()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_entry_is_written_inside_the_reserved_analytics_tree(self) -> None:
        from agent_workflows.runner_shared import path_is_within_analytics

        run_dir = _write_run(self.runs, "run-20260101T000000Z-40")
        cache._publish(_envelope(run_dir, self.root_id), repo=self.repo)
        target = cache.entry_path(self.root_id, run_dir.name, self.repo)
        self.assertTrue(target.is_file())
        self.assertTrue(
            path_is_within_analytics(target, self.repo),
            "the cache must live inside the Order-01 reserved tree",
        )
        self.assertIn("analytics", target.parts)
        self.assertIn("cache", target.parts)

    def test_the_path_is_resolved_through_the_resolver_not_composed(self) -> None:
        source = (REPO_ROOT / "agent_workflows" / "run_analytics_cache.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn(
            '".aw"',
            source,
            "the cache module must not compose the runs root from a literal; "
            "Order 01's resolver owns it",
        )
        self.assertIn("analytics_cache_dir", source)

    def test_a_busy_lock_is_a_recorded_skip_and_never_a_wait_or_a_partial_write(
        self,
    ) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-41")
        env = _envelope(run_dir, self.root_id)
        directory = cache.entry_dir(self.root_id, run_dir.name, self.repo)
        directory.mkdir(parents=True, exist_ok=True)
        holder = platform_lock.acquire(directory / "entry.lock")
        try:
            started = time.monotonic()
            decision = cache._publish(env, repo=self.repo)
            elapsed = time.monotonic() - started
        finally:
            holder.release()
        self.assertEqual((decision.verdict, decision.reason), ("skip", "lock-busy"))
        self.assertLess(
            elapsed, 1.0, f"a busy lock must not wait (took {elapsed:.3f}s)"
        )
        self.assertFalse(
            (directory / cache.ENTRY_FILENAME).exists(),
            "a contended publish must not leave a partial entry",
        )
        self.assertIn("skipped without waiting", decision.detail)

    def test_a_busy_lock_is_visible_in_the_decision_output_not_a_silent_pass(
        self,
    ) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-42")
        directory = cache.entry_dir(self.root_id, run_dir.name, self.repo)
        directory.mkdir(parents=True, exist_ok=True)
        holder = platform_lock.acquire(directory / "entry.lock")
        try:
            report = cache.update_cache(
                [run_dir],
                build_facts=_facts_builder(),
                repo=self.repo,
                root_id=self.root_id,
                salt=_SALT,
            )
        finally:
            holder.release()
        self.assertEqual(report.totals["skip"], 1)
        self.assertEqual(report.decisions[0].reason, "lock-busy")

    def test_interruption_never_publishes_a_partial_entry(self) -> None:
        """The write goes through the atomic helper, so a crash mid-write leaves the PRIOR entry."""

        run_dir = _write_run(self.runs, "run-20260101T000000Z-43")
        cache._publish(_envelope(run_dir, self.root_id), repo=self.repo)
        target = cache.entry_path(self.root_id, run_dir.name, self.repo)
        good = target.read_text(encoding="utf-8")

        import agent_workflows.run_analytics_cache as mod

        real = mod.atomic_write_json

        def exploding(path, data):  # noqa: ANN001
            raise KeyboardInterrupt("simulated interruption mid-publish")

        mod.atomic_write_json = exploding
        try:
            with self.assertRaises(KeyboardInterrupt):
                cache._publish(_envelope(run_dir, self.root_id), repo=self.repo)
        finally:
            mod.atomic_write_json = real
        self.assertEqual(
            target.read_text(encoding="utf-8"),
            good,
            "the prior valid entry must survive an interrupted publish",
        )
        cache.load_entry(target)  # still decodes

    def test_no_temp_file_is_left_behind_after_a_successful_publish(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-44")
        cache._publish(_envelope(run_dir, self.root_id), repo=self.repo)
        directory = cache.entry_dir(self.root_id, run_dir.name, self.repo)
        leftovers = [p.name for p in directory.iterdir() if p.name.startswith(".")]
        self.assertEqual(leftovers, [], f"temp files left behind: {leftovers}")

    def test_the_lock_is_released_after_publication(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-45")
        cache._publish(_envelope(run_dir, self.root_id), repo=self.repo)
        lock_file = (
            cache.entry_dir(self.root_id, run_dir.name, self.repo) / "entry.lock"
        )
        self.assertIsNot(
            platform_lock.probe_free(lock_file),
            False,
            "the entry lock must not stay held",
        )

    def test_one_corrupt_entry_is_rebuilt_without_touching_its_neighbours(self) -> None:
        good_a = _write_run(self.runs, "run-20260101T000000Z-46")
        bad = _write_run(self.runs, "run-20260101T000000Z-47")
        good_b = _write_run(self.runs, "run-20260101T000000Z-48")
        for run in (good_a, bad, good_b):
            cache._publish(_envelope(run, self.root_id), repo=self.repo)
        neighbour_before = cache.entry_path(
            self.root_id, good_a.name, self.repo
        ).read_text(encoding="utf-8")
        cache.entry_path(self.root_id, bad.name, self.repo).write_text(
            "\x00\x01 not json", encoding="utf-8"
        )

        report = cache.update_cache(
            [good_a, bad, good_b],
            build_facts=_facts_builder(),
            repo=self.repo,
            root_id=self.root_id,
            salt=_SALT,
        )
        by_run = {d.run_id: d for d in report.decisions}
        self.assertEqual(by_run[good_a.name].verdict, "hit")
        self.assertEqual(by_run[good_b.name].verdict, "hit")
        self.assertEqual(by_run[bad.name].verdict, "rebuild")
        self.assertEqual(by_run[bad.name].reason, "entry-unreadable")
        self.assertEqual(
            cache.entry_path(self.root_id, good_a.name, self.repo).read_text(
                encoding="utf-8"
            ),
            neighbour_before,
            "a neighbour's entry must be byte-identical after another entry was rebuilt",
        )
        cache.load_entry(cache.entry_path(self.root_id, bad.name, self.repo))

    def test_one_refused_fact_set_does_not_end_the_sweep(self) -> None:
        ok_run = _write_run(self.runs, "run-20260101T000000Z-49")
        bad_run = _write_run(self.runs, "run-20260101T000000Z-50")

        def build(run_dir: Path):
            if run_dir.name == bad_run.name:
                return {"repo": _HOME_PATH}, [], [], []
            return _facts_builder()(run_dir)

        report = cache.update_cache(
            [bad_run, ok_run],
            build_facts=build,
            repo=self.repo,
            root_id=self.root_id,
            salt=_SALT,
        )
        by_run = {d.run_id: d for d in report.decisions}
        self.assertEqual(by_run[bad_run.name].verdict, "skip")
        self.assertEqual(by_run[bad_run.name].reason, "build-refused")
        self.assertEqual(by_run[ok_run.name].verdict, "rebuild")

    def test_a_producer_exception_is_isolated_and_its_message_is_redacted(self) -> None:
        ok_run = _write_run(self.runs, "run-20260101T000000Z-51")
        bad_run = _write_run(self.runs, "run-20260101T000000Z-52")

        def build(run_dir: Path):
            if run_dir.name == bad_run.name:
                raise RuntimeError(f"cannot parse {_HOME_PATH}/state.json")
            return _facts_builder()(run_dir)

        report = cache.update_cache(
            [bad_run, ok_run],
            build_facts=build,
            repo=self.repo,
            root_id=self.root_id,
            salt=_SALT,
        )
        by_run = {d.run_id: d for d in report.decisions}
        self.assertEqual(by_run[bad_run.name].verdict, "skip")
        self.assertNotIn(_HANDLE, by_run[bad_run.name].detail)
        self.assertEqual(by_run[ok_run.name].verdict, "rebuild")

    def test_two_concurrent_analyzers_leave_exactly_one_valid_entry(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-53")
        ctx = multiprocessing.get_context("spawn")
        queue: "multiprocessing.Queue[str]" = ctx.Queue()
        procs = [
            ctx.Process(
                target=_concurrent_publish,
                args=(
                    str(REPO_ROOT),
                    str(self.repo),
                    str(run_dir),
                    self.root_id,
                    queue,
                ),
            )
            for _ in range(2)
        ]
        for p in procs:
            p.start()
        for p in procs:
            p.join(timeout=60)
        results = []
        while not queue.empty():
            results.append(queue.get())
        self.assertEqual(len(results), 2, f"both analyzers must report: {results}")
        for line in results:
            self.assertIn(line.split(":", 1)[0], {"rebuild", "skip"}, line)
        target = cache.entry_path(self.root_id, run_dir.name, self.repo)
        self.assertTrue(target.is_file())
        cache.load_entry(target)  # exactly one valid entry, never a torn one

    def test_the_module_uses_platform_lock_and_no_raw_lock_primitive(self) -> None:
        source = (REPO_ROOT / "agent_workflows" / "run_analytics_cache.py").read_text(
            encoding="utf-8"
        )
        self.assertIsNone(
            re.search(
                r"^\s*(?:import|from)\s+(?:fcntl|filelock)\b", source, re.MULTILINE
            ),
            "a lock implemented directly on filelock/fcntl is a failed item",
        )
        self.assertIn("platform_lock.acquire", source)
        self.assertIn("platform_lock.LockBusy", source)

    def test_publication_refuses_a_directory_outside_the_analytics_tree(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-54")
        env = _envelope(run_dir, self.root_id)
        import agent_workflows.run_analytics_cache as mod

        real = mod.entry_dir
        outside = self.tmp / "escaped"
        mod.entry_dir = lambda *a, **k: outside  # noqa: ARG005
        try:
            with self.assertRaises(cache.CacheError) as ctx:
                mod._publish(env, repo=self.repo)
        finally:
            mod.entry_dir = real
        self.assertIn("outside the reserved analytics tree", str(ctx.exception))
        self.assertFalse((outside / cache.ENTRY_FILENAME).exists())


def _concurrent_publish(
    repo_root: str, repo: str, run_dir: str, root_id: str, queue
) -> None:  # noqa: ANN001
    """Child-process worker for the concurrency test (module level so `spawn` can pickle it)."""

    import sys as _sys

    _sys.path.insert(0, repo_root)
    from agent_workflows import run_analytics_cache as c
    from pathlib import Path as _P

    metric = {"cost": 1.0, "event_count": 1, "phase": "execute"}
    env = c.build_entry(
        run_id=_P(run_dir).name,
        root_id=root_id,
        run_dir=_P(run_dir),
        metric_facts=metric,
    )
    decision = c._publish(env, repo=repo)
    queue.put(f"{decision.verdict}:{decision.reason}")


# ============================================================ E-03: machine-readable observability
class DecisionOutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.repo = _make_repo(self.tmp)
        self.runs = self.repo / ".aw" / "records" / "runs"
        self.root_id = _root_id()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _update(self, runs, **kw):
        return cache.update_cache(
            runs,
            build_facts=_facts_builder(),
            repo=self.repo,
            root_id=self.root_id,
            salt=_SALT,
            **kw,
        )

    def test_report_carries_per_run_verdicts_with_reasons_and_totals(self) -> None:
        hit_run = _write_run(self.runs, "run-20260101T000000Z-60")
        rebuild_run = _write_run(self.runs, "run-20260101T000000Z-61")
        skip_run = _write_run(self.runs, "run-20260101T000000Z-62")
        self._update([hit_run])  # seed a hit

        directory = cache.entry_dir(self.root_id, skip_run.name, self.repo)
        directory.mkdir(parents=True, exist_ok=True)
        holder = platform_lock.acquire(directory / "entry.lock")
        try:
            report = self._update([hit_run, rebuild_run, skip_run])
        finally:
            holder.release()

        payload = report.to_dict()
        self.assertEqual(
            payload["totals"],
            {"hit": 1, "miss": 0, "rebuild": 1, "skip": 1, "total": 3},
        )
        by_run = {d["run_id"]: d for d in payload["decisions"]}
        self.assertEqual(by_run[hit_run.name]["verdict"], "hit")
        self.assertEqual(by_run[rebuild_run.name]["verdict"], "rebuild")
        self.assertEqual(by_run[skip_run.name]["verdict"], "skip")
        for decision in payload["decisions"]:
            self.assertIn(decision["reason"], cache.REASON_CODES)
            self.assertTrue(decision["detail"])

    def test_the_report_is_json_serializable_as_a_stable_shape(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-63")
        payload = self._update([run_dir]).to_dict()
        encoded = json.dumps(payload, sort_keys=True)
        self.assertEqual(json.loads(encoded), payload)
        self.assertEqual(
            sorted(payload),
            ["decisions", "schema_version", "totals"],
            "the consumer contract",
        )
        self.assertEqual(
            sorted(payload["decisions"][0]), ["detail", "reason", "run_id", "verdict"]
        )

    def test_a_second_unchanged_analysis_reads_strictly_fewer_source_files(
        self,
    ) -> None:
        """Counted with an instrumented open(), not asserted as 'should be fewer'."""

        runs = [_write_run(self.runs, f"run-20260101T000000Z-7{i}") for i in range(3)]
        source_names = {"state.json", "events.jsonl", "01-aaa111.json"}
        counts: list[int] = []

        # `io.open` is what `Path.read_text` and `builtins.open` both reach, so instrumenting it
        # counts every real source read rather than only the ones spelled `open(...)`.
        import io as _io

        real_open = _io.open

        for _ in range(2):
            opened: list[str] = []

            def counting_open(file, *a, **k):  # noqa: ANN001
                if not isinstance(file, int):
                    text = os.fsdecode(os.fspath(file))
                    if Path(text).name in source_names and "analytics" not in text:
                        opened.append(text)
                return real_open(file, *a, **k)

            _io.open = counting_open
            try:
                self._update(runs)
            finally:
                _io.open = real_open
            counts.append(len(opened))

        self.assertGreater(counts[0], 0, "the first pass must read the sources")
        self.assertLess(
            counts[1],
            counts[0],
            f"a cached second pass must read fewer source files: first={counts[0]} second={counts[1]}",
        )

    def test_repeated_unchanged_analysis_is_byte_stable_apart_from_generated_at(
        self,
    ) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-80")
        self._update([run_dir])
        target = cache.entry_path(self.root_id, run_dir.name, self.repo)
        first = json.loads(target.read_text(encoding="utf-8"))
        self._update([run_dir])  # a hit: must not rewrite
        second = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(first, second, "a hit must not rewrite the entry at all")

        # And a forced rebuild differs ONLY in the explicitly volatile metadata.
        volatile = {"generated_at"}
        env = _envelope(run_dir, self.root_id, generated_at="2030-01-01T00:00:00Z")
        cache._publish(env, repo=self.repo)
        third = json.loads(target.read_text(encoding="utf-8"))
        differing = {k for k in set(first) | set(third) if first.get(k) != third.get(k)}
        self.assertTrue(
            differing <= volatile,
            f"unexpected non-volatile differences between two unchanged rebuilds: "
            f"{sorted(differing - volatile)}",
        )

    def test_update_cache_is_idempotent(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-81")
        first = self._update([run_dir]).totals
        second = self._update([run_dir]).totals
        third = self._update([run_dir]).totals
        self.assertEqual(first["rebuild"], 1)
        self.assertEqual(second["hit"], 1)
        self.assertEqual(second, third, "a settled cache must produce a settled report")


# ================================================================== E-06: adversarial privacy proof
class AdversarialPrivacyTests(unittest.TestCase):
    """Seeded canaries plus the SHIPPED detector, each clean scan paired with its control."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.repo = _make_repo(self.tmp)
        self.runs = self.repo / ".aw" / "records" / "runs"
        self.root_id = _root_id()
        self.ruleset = ls.build_ruleset(REPO_ROOT)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _scan_cache_tree(self) -> list[ls.Finding]:
        """Point the detector AT THE CACHE, which a working-tree scan would never reach."""

        findings: list[ls.Finding] = []
        root = cache.cache_root(self.repo)
        for path in sorted(root.rglob("*")):
            if path.is_file():
                findings.extend(
                    ls.scan_text(
                        path.read_text(encoding="utf-8", errors="replace"),
                        path.name,
                        self.ruleset,
                    )
                )
        return findings

    def _seeded_canaries(self) -> dict[str, object]:
        """Assembled at runtime from fragments. Nothing here is a committed literal."""

        return {
            "prompt": _PROMPT_BODY,
            "absolute_path": _HOME_PATH + "/agent_workflows/cli.py",
            "mac_path": "/Us" + "ers/" + _HANDLE + "/src",
            "windows_path": "C:" + "\\Users\\" + _HANDLE,
            "command": "git commit -m x -- " + _HOME_PATH,
            "hostname": _HANDLE + "-laptop.local",
            "username": _HANDLE,
            "private_repo": "her" + "mes-agent",
            "session_id": "ses_" + "9f3a71c0d2b84e55",
            "env_secret": "sk-" + "live" + "_" + "51H8xQ2mZk9Lw3Rt7Yv0Bn4Cp6Ds8Fg1",
            "high_entropy_token": "AKIA" + "IOSFODNN7EXAMPLE",
        }

    def test_control_the_detector_flags_every_seeded_canary_in_raw_form(self) -> None:
        """Without this, a clean cache scan cannot be told from a detector that was not looking."""

        flagged = 0
        for name, value in self._seeded_canaries().items():
            findings = ls.scan_text(str(value), name, self.ruleset)
            if findings:
                flagged += 1
        self.assertGreaterEqual(
            flagged,
            7,
            "CONTROL: the shipped detector must flag the path/identity/session canaries in raw form",
        )
        for name in (
            "absolute_path",
            "mac_path",
            "windows_path",
            "username",
            "private_repo",
            "session_id",
        ):
            with self.subTest(canary=name):
                self.assertTrue(
                    ls.scan_text(
                        str(self._seeded_canaries()[name]), name, self.ruleset
                    ),
                    f"CONTROL FAILED for {name}",
                )

    def test_seeded_canaries_reach_no_cache_file_and_the_detector_reports_clean(
        self,
    ) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-90")
        canaries = self._seeded_canaries()

        def hostile_build(_run_dir: Path):
            metric = {
                "cost": 1.0,
                "event_count": 2,
                "phase": "execute",
                "tokens": {"input": 1, "output": 2, "total": 3},
                "source_root_id": self.root_id,
            }
            events = [{"event_type": "turn", "sequence": 0, "payload_byte_count": 10}]
            return metric, events, ["parsed-clean"], []

        report = cache.update_cache(
            [run_dir],
            build_facts=hostile_build,
            repo=self.repo,
            root_id=self.root_id,
            salt=_SALT,
        )
        self.assertEqual(report.totals["rebuild"], 1)

        blob = ""
        root = cache.cache_root(self.repo)
        for path in sorted(root.rglob("*")):
            if path.is_file():
                blob += path.read_text(encoding="utf-8", errors="replace")
        for name, value in canaries.items():
            with self.subTest(canary=name):
                self.assertNotIn(str(value), blob, f"{name} reached a cache file")
        self.assertNotIn(_HANDLE, blob)

        findings = self._scan_cache_tree()
        self.assertEqual(
            findings,
            [],
            f"the shipped detector found leaks in the cache tree: "
            f"{[(f.rule, f.location) for f in findings]}",
        )

    def test_a_producer_that_hands_over_a_canary_is_refused_not_sanitized(self) -> None:
        """Silently scrubbing would hide from the producer that it leaked; refusal does not."""

        run_dir = _write_run(self.runs, "run-20260101T000000Z-91")
        for key, value in self._seeded_canaries().items():
            with self.subTest(canary=key):
                with self.assertRaises(privacy.PrivacyRefusal):
                    cache.build_entry(
                        run_id=run_dir.name,
                        root_id=self.root_id,
                        run_dir=run_dir,
                        metric_facts={key: value},
                    )

    def test_the_state_json_repo_field_never_reaches_the_cache(self) -> None:
        """The measured worst case: the FIRST field an ingester reads is an absolute home path."""

        run_dir = _write_run(self.runs, "run-20260101T000000Z-92")
        raw_state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        self.assertTrue(
            ls.scan_text(raw_state["repo"], "state.json", self.ruleset),
            "precondition: the raw repo field must be a detected leak",
        )
        with self.assertRaises(privacy.PrivacyRefusal):
            cache.build_entry(
                run_id=run_dir.name,
                root_id=self.root_id,
                run_dir=run_dir,
                metric_facts={"repo": raw_state["repo"]},
            )

    def test_no_warning_or_diagnostic_string_in_the_cache_carries_a_path(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-93")
        with self.assertRaises(privacy.PrivacyRefusal):
            cache.build_entry(
                run_id=run_dir.name,
                root_id=self.root_id,
                run_dir=run_dir,
                metric_facts={"cost": 1.0},
                warnings=[f"could not read {_HOME_PATH}/events.jsonl"],
            )

    def test_this_test_file_holds_no_literal_leak(self) -> None:
        source = Path(__file__).read_text(encoding="utf-8")
        findings = ls.scan_text(source, "self", self.ruleset)
        self.assertEqual(
            findings,
            [],
            f"this test file must not commit a literal canary: "
            f"{[(f.rule, f.location) for f in findings]}",
        )

    def test_the_cache_module_is_self_clean(self) -> None:
        source = (REPO_ROOT / "agent_workflows" / "run_analytics_cache.py").read_text(
            encoding="utf-8"
        )
        self.assertEqual(ls.scan_text(source, "module", self.ruleset), [])

    def test_numeric_conservation_across_encode_decode_for_every_fact(self) -> None:
        run_dir = _write_run(self.runs, "run-20260101T000000Z-94")
        metric = {
            "cost": 12.345678,
            "token_total": 987654321,
            "duration_seconds": 0.000123,
            "cpu_seconds": 61.5,
            "max_rss_bytes": 2**33,
            "event_count": 0,
            "tokens": {"input": 2**31 + 1, "output": 0, "cache": 7, "total": 2**31 + 8},
        }
        env = cache.build_entry(
            run_id=run_dir.name,
            root_id=self.root_id,
            run_dir=run_dir,
            metric_facts=metric,
        )
        cache._publish(env, repo=self.repo)
        loaded = cache.load_entry(
            cache.entry_path(self.root_id, run_dir.name, self.repo)
        )
        for key, before in metric.items():
            with self.subTest(fact=key):
                self.assertEqual(
                    loaded.metric_facts[key],
                    before,
                    f"{key}: before={before!r} after={loaded.metric_facts[key]!r}",
                )

    def test_the_module_documents_that_the_cache_is_not_release_safe(self) -> None:
        """The limitation must live in the module, where a consumer will actually look."""

        doc = (privacy.__doc__ or "") + (cache.__doc__ or "")
        lowered = doc.lower()
        self.assertIn("not anonymous", lowered)
        self.assertIn("residual", lowered)
        for token in ("minimized", "redacted"):
            self.assertIn(token, lowered)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
