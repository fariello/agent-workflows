#!/usr/bin/env python3
"""Tests for the best-effort subagent-progress observer feeding the stall watchdog.

The observer exists because ``opencode run --format json`` stdout carries ONLY
parent-session events, so a turn working inside a subagent looks idle and gets killed. See
``agent_workflows/stall_progress.py`` for the measured evidence and the attribution route.

The load-bearing tests here are the NEGATIVES: an unrelated session must not count, and
housekeeping noise must not count. If either regressed, a permission-deadlocked run would
become immortal, which is worse than the bug being fixed.
"""

from __future__ import annotations

import os
import threading
import time
import unittest
from pathlib import Path

from agent_workflows import stall_progress as sp

_FIXTURE = Path(__file__).parent / "fixtures" / "opencode-subagent-progress.log"

# The fixture's redacted tokens. `ses_<redacted>...` is the sanitizer-approved form (the
# `session-id` rule at leak_sanitizer.py:81 explicitly allows `ses_<redacted>`).
_PARENT = "ses_<redacted>parent"
_CHILD = "ses_<redacted>child"
_OTHER = "ses_<redacted>other"


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


class LogPathResolutionTests(unittest.TestCase):
    """The log path comes from the environment, never a hardcoded home directory."""

    def test_honors_xdg_data_home(self):
        prev = os.environ.get("XDG_DATA_HOME")
        os.environ["XDG_DATA_HOME"] = "/tmp/xdg-example"
        try:
            self.assertEqual(
                sp.default_log_path(),
                Path("/tmp/xdg-example/opencode/log/opencode.log"),
            )
        finally:
            if prev is None:
                del os.environ["XDG_DATA_HOME"]
            else:
                os.environ["XDG_DATA_HOME"] = prev

    def test_falls_back_to_local_share(self):
        prev = os.environ.pop("XDG_DATA_HOME", None)
        try:
            expected = (
                Path.home() / ".local" / "share" / "opencode" / "log" / "opencode.log"
            )
            self.assertEqual(sp.default_log_path(), expected)
        finally:
            if prev is not None:
                os.environ["XDG_DATA_HOME"] = prev

    def test_module_has_no_hardcoded_home_path(self):
        src = Path(sp.__file__).read_text(encoding="utf-8")
        self.assertNotIn("/home/", src)
        self.assertNotIn("/Users/", src)


class ProgressClassificationTests(unittest.TestCase):
    """Only agent-loop kinds count. This is the true-hang guarantee, not a nicety."""

    def test_agent_loop_kinds_are_progress(self):
        for kind in ("loop", "process", "stream"):
            line = f"timestamp=X level=INFO run=abc message={kind} session.id={_CHILD}"
            self.assertEqual(sp.classify_progress(line), kind)

    def test_housekeeping_kinds_are_not_progress(self):
        # These are exactly the kinds a permission-deadlocked process keeps emitting.
        noise = [
            'message=evaluated permission=bash pattern="x"',
            "message=asking id=per_x permission=external_directory",
            'message="llm runtime selected" runtime=node',
            "message=tracking hash=0000",
            'message="resolved path" path=/tmp/x',
            'message="touching file" path=/tmp/y',
            "message=created id=ses_a parentID=ses_b",
            "message=formatting file=x.py",
        ]
        for line in noise:
            self.assertIsNone(
                sp.classify_progress(f"timestamp=X level=INFO run=abc {line}"),
                f"housekeeping line wrongly counted as progress: {line}",
            )

    def test_progress_kinds_are_a_closed_allowlist(self):
        # A NEW opencode housekeeping kind must not silently become "progress".
        self.assertEqual(
            sp.PROGRESS_MESSAGE_KINDS, frozenset({"loop", "process", "stream"})
        )
        self.assertIsNone(sp.classify_progress("message=some_future_kind session.id=x"))


class AttributionTests(unittest.TestCase):
    """The two-hop parent-session route: created(parentID=ours) -> child session.id."""

    def _observer(self, **kw):
        return sp.SubagentProgressObserver(log_path=_FIXTURE, start_at_end=False, **kw)

    def test_reports_progress_for_our_attributable_subagent(self):
        obs = self._observer(parent_session_id=_PARENT)
        self.assertTrue(obs.poll(), "attributable subagent progress was not reported")
        self.assertIn(_CHILD, obs.known_children())
        self.assertGreater(obs.progress_count, 0)
        self.assertIsNotNone(obs.last_progress_monotonic)

    def test_does_not_report_progress_for_a_different_session(self):
        # Our parent never spawned ses_<redacted>other; that child belongs to another
        # concurrent opencode process sharing the same machine-wide log.
        obs = self._observer(parent_session_id="ses_<redacted>nobody")
        self.assertFalse(obs.poll(), "unrelated session counted as our progress")
        self.assertEqual(obs.progress_count, 0)
        self.assertEqual(obs.known_children(), frozenset())

    def test_unrelated_child_is_never_added_even_with_a_known_parent(self):
        obs = self._observer(parent_session_id=_PARENT)
        obs.poll()
        children = obs.known_children()
        self.assertIn(_CHILD, children)
        self.assertNotIn(_OTHER, children)

    def test_noise_only_log_reports_no_progress(self):
        # THE NOISY-HANG SHAPE: our own process is chatty but makes no agent-loop progress.
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "opencode.log"
            _write(
                log,
                "\n".join(
                    [
                        f"timestamp=T1 level=INFO run=abc message=created id={_CHILD} parentID={_PARENT}",
                        'timestamp=T2 level=INFO run=abc message=evaluated permission=bash pattern="x"',
                        "timestamp=T3 level=INFO run=abc message=asking id=per_1 permission=external_directory",
                        'timestamp=T4 level=INFO run=abc message="llm runtime selected" runtime=node',
                        "timestamp=T5 level=INFO run=abc message=tracking hash=0",
                        "",
                    ]
                ),
            )
            obs = sp.SubagentProgressObserver(
                parent_session_id=_PARENT, log_path=log, start_at_end=False
            )
            self.assertFalse(
                obs.poll(),
                "housekeeping noise reported as progress (would defeat the kill)",
            )
            # The child WAS learned (the created line is ours) but produced no progress.
            self.assertIn(_CHILD, obs.known_children())
            self.assertEqual(obs.progress_count, 0)

    def test_parent_learned_late_still_attributes(self):
        obs = self._observer(parent_session_id=None)
        obs.set_parent_session(_PARENT)
        self.assertTrue(obs.poll())

    def test_set_parent_session_rejects_junk(self):
        obs = self._observer(parent_session_id=None)
        for junk in (None, "", "not-a-session", 42):
            obs.set_parent_session(junk)  # type: ignore[arg-type]
        self.assertFalse(obs.poll())


class DegradationTests(unittest.TestCase):
    """Best-effort: every failure mode returns nothing and raises nothing."""

    def test_missing_log_returns_nothing_raises_nothing(self):
        obs = sp.SubagentProgressObserver(
            parent_session_id=_PARENT,
            log_path=Path("/nonexistent/definitely/not/here/opencode.log"),
        )
        self.assertFalse(obs.poll())
        self.assertIsNone(obs.last_progress_monotonic)

    def test_unreadable_log_returns_nothing_raises_nothing(self):
        import tempfile

        if os.geteuid() == 0:
            self.skipTest("root bypasses file permissions")
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "opencode.log"
            _write(log, f"message=loop session.id={_CHILD}\n")
            log.chmod(0o000)
            try:
                obs = sp.SubagentProgressObserver(
                    parent_session_id=_PARENT, log_path=log, start_at_end=False
                )
                self.assertFalse(obs.poll())
            finally:
                log.chmod(0o644)

    def test_garbage_log_returns_nothing_raises_nothing(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "opencode.log"
            log.write_bytes(b"\x00\x01\x02 not a log at all \xff\xfe\n" * 50)
            obs = sp.SubagentProgressObserver(
                parent_session_id=_PARENT, log_path=log, start_at_end=False
            )
            self.assertFalse(obs.poll())

    def test_mid_line_truncated_tail_is_not_misparsed(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "opencode.log"
            # A partial line with no trailing newline must be held back, not parsed.
            _write(
                log,
                f"timestamp=T1 level=INFO run=abc message=created id={_CHILD} parentID={_PARENT}\n"
                f"timestamp=T2 level=INFO run=abc message=lo",
            )
            obs = sp.SubagentProgressObserver(
                parent_session_id=_PARENT, log_path=log, start_at_end=False
            )
            self.assertFalse(obs.poll(), "partial line was parsed as progress")
            # Completing the line then yields the progress.
            with log.open("a", encoding="utf-8") as fh:
                fh.write(f"op session.id={_CHILD} step=0\n")
            self.assertTrue(obs.poll())

    def test_truncation_reanchors_without_crashing(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "opencode.log"
            _write(log, "x" * 5000 + "\n")
            obs = sp.SubagentProgressObserver(
                parent_session_id=_PARENT, log_path=log, start_at_end=True
            )
            _write(log, "tiny\n")  # rotation/truncation: file is now smaller
            self.assertFalse(obs.poll())
            with log.open("a", encoding="utf-8") as fh:
                fh.write(
                    f"message=created id={_CHILD} parentID={_PARENT}\n"
                    f"message=loop session.id={_CHILD} step=0\n"
                )
            self.assertTrue(obs.poll())


class BoundednessTests(unittest.TestCase):
    """The observer reads FORWARD from its start offset; it never re-reads history."""

    def test_pre_start_content_is_never_read(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "opencode.log"
            # Pre-seed a LARGE history that already contains attributable progress. If the
            # observer re-read history it would fabricate progress from a previous turn.
            pre = (
                f"message=created id={_CHILD} parentID={_PARENT}\n"
                f"message=loop session.id={_CHILD} step=0\n"
            ) * 2000
            _write(log, pre)
            size = log.stat().st_size
            self.assertGreater(size, 100_000)

            obs = sp.SubagentProgressObserver(
                parent_session_id=_PARENT, log_path=log, start_at_end=True
            )
            self.assertFalse(
                obs.poll(), "observer re-read pre-start history and fabricated progress"
            )
            self.assertEqual(obs.progress_count, 0)

            # Only content appended AFTER start is observed.
            with log.open("a", encoding="utf-8") as fh:
                fh.write(
                    f"message=created id={_CHILD} parentID={_PARENT}\n"
                    f"message=loop session.id={_CHILD} step=9\n"
                )
            self.assertTrue(obs.poll())
            self.assertEqual(obs.progress_count, 1)

    def test_tolerates_concurrent_appends_across_polls(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "opencode.log"
            _write(log, f"message=created id={_CHILD} parentID={_PARENT}\n")
            obs = sp.SubagentProgressObserver(
                parent_session_id=_PARENT, log_path=log, start_at_end=False
            )
            obs.poll()
            total = 0
            for step in range(5):
                with log.open("a", encoding="utf-8") as fh:
                    # Interleave an unrelated process's lines, as the real shared log does.
                    fh.write(f"message=loop session.id={_OTHER} step={step}\n")
                    fh.write(f"message=loop session.id={_CHILD} step={step}\n")
                self.assertTrue(obs.poll())
                total += 1
            self.assertEqual(obs.progress_count, total)


class PollerThreadHygieneTests(unittest.TestCase):
    """The poller thread is scope-bound: it cannot outlive the turn or leak per attempt."""

    def test_thread_does_not_outlive_the_context(self):
        obs = sp.SubagentProgressObserver(
            parent_session_id=_PARENT, log_path=_FIXTURE, start_at_end=False
        )
        before = {t.name for t in threading.enumerate()}
        with sp.ProgressPoller(obs, interval=0.05):
            time.sleep(0.15)
            during = {t.name for t in threading.enumerate()}
            self.assertIn("aw-subagent-progress", during)
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            if "aw-subagent-progress" not in {t.name for t in threading.enumerate()}:
                break
            time.sleep(0.02)
        after = {t.name for t in threading.enumerate()}
        self.assertNotIn("aw-subagent-progress", after)
        self.assertEqual(before - after, set())

    def test_repeated_attempts_do_not_accumulate_threads(self):
        for _ in range(4):
            obs = sp.SubagentProgressObserver(
                parent_session_id=_PARENT, log_path=_FIXTURE, start_at_end=False
            )
            with sp.ProgressPoller(obs, interval=0.05):
                time.sleep(0.06)
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            live = [
                t for t in threading.enumerate() if t.name == "aw-subagent-progress"
            ]
            if not live:
                break
            time.sleep(0.02)
        self.assertEqual(
            [t for t in threading.enumerate() if t.name == "aw-subagent-progress"], []
        )

    def test_poller_touches_registered_sinks_on_progress(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "opencode.log"
            _write(log, f"message=created id={_CHILD} parentID={_PARENT}\n")
            obs = sp.SubagentProgressObserver(
                parent_session_id=_PARENT, log_path=log, start_at_end=False
            )
            touched = []
            with sp.ProgressPoller(
                obs, touch_callbacks=(lambda: touched.append(1),), interval=0.05
            ):
                time.sleep(0.1)
                with log.open("a", encoding="utf-8") as fh:
                    fh.write(f"message=loop session.id={_CHILD} step=0\n")
                deadline = time.monotonic() + 3.0
                while time.monotonic() < deadline and not touched:
                    time.sleep(0.02)
            self.assertTrue(touched, "poller did not touch the watchdog on progress")

    def test_a_raising_sink_does_not_break_the_poller(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "opencode.log"
            _write(log, f"message=created id={_CHILD} parentID={_PARENT}\n")
            obs = sp.SubagentProgressObserver(
                parent_session_id=_PARENT, log_path=log, start_at_end=False
            )
            good = []

            def bad():
                raise RuntimeError("sink blew up")

            with sp.ProgressPoller(
                obs, touch_callbacks=(bad, lambda: good.append(1)), interval=0.05
            ):
                time.sleep(0.1)
                with log.open("a", encoding="utf-8") as fh:
                    fh.write(f"message=loop session.id={_CHILD} step=0\n")
                deadline = time.monotonic() + 3.0
                while time.monotonic() < deadline and not good:
                    time.sleep(0.02)
            self.assertTrue(good, "a raising sink suppressed the other sinks")


class FixtureHygieneTests(unittest.TestCase):
    """The committed fixture must carry no real session token (leak_sanitizer rule)."""

    def test_fixture_contains_no_unredacted_session_id(self):
        import re

        text = _FIXTURE.read_text(encoding="utf-8")
        # Same rule as leak_sanitizer.py:81.
        rule = re.compile(r"\bses_(?!<redacted>)[0-9A-Za-z]{8,}")
        self.assertEqual(rule.findall(text), [])

    def test_fixture_pins_the_observed_opencode_version(self):
        text = _FIXTURE.read_text(encoding="utf-8")
        self.assertIn(f"version={sp.OBSERVED_OPENCODE_VERSION}", text)


if __name__ == "__main__":
    unittest.main()
