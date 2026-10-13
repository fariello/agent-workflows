"""Tests for opt-in runner-safety probe memo seam (IPD 8hhd7t)."""

from __future__ import annotations

import unittest
from typing import Dict, List, Tuple

from agent_workflows import host_sandbox_profile as hsp


class RunnerSafetyProbeMemoTests(unittest.TestCase):
    """Behavioral tests for memoized_runner_safety_verdicts and probe caching."""

    def setUp(self) -> None:
        self._saved_probes = dict(hsp._RUNNER_SAFETY_PROBES)
        self._saved_forced = hsp._FORCED_RUNNER_SAFETY
        self._saved_memo = hsp._RUNNER_SAFETY_MEMO

    def tearDown(self) -> None:
        hsp._RUNNER_SAFETY_PROBES.clear()
        hsp._RUNNER_SAFETY_PROBES.update(self._saved_probes)
        hsp._FORCED_RUNNER_SAFETY = self._saved_forced
        hsp._RUNNER_SAFETY_MEMO = self._saved_memo

    def _install_counting_probes(self) -> Dict[str, List[int]]:
        counts: Dict[str, List[int]] = {}
        for name, fn in list(hsp._RUNNER_SAFETY_PROBES.items()):
            if fn is None:
                continue
            counts[name] = [0]

            def make_probe(cap_name: str):
                def probe_fn() -> Tuple[bool, str]:
                    counts[cap_name][0] += 1
                    return True, f"{cap_name}-ok"

                return probe_fn

            hsp._RUNNER_SAFETY_PROBES[name] = make_probe(name)
        return counts

    def test_memo_off_executes_probes_on_each_call(self) -> None:
        """(a) With the memo off two calls execute each probe twice."""
        self.assertIsNone(hsp._RUNNER_SAFETY_MEMO)
        counts = self._install_counting_probes()

        v1, n1 = hsp.probe_runner_safety_capabilities()
        for cap, c in counts.items():
            self.assertEqual(
                c[0], 1, f"Expected 1 execution for {cap} after first call"
            )
            self.assertTrue(v1[cap])
            self.assertEqual(n1[cap], f"{cap}-ok")

        v2, n2 = hsp.probe_runner_safety_capabilities()
        for cap, c in counts.items():
            self.assertEqual(
                c[0], 2, f"Expected 2 executions for {cap} after second call"
            )
            self.assertTrue(v2[cap])
            self.assertEqual(n2[cap], f"{cap}-ok")

    def test_memo_scope_executes_each_probe_once_and_returns_equal_verdicts_and_notes(
        self,
    ) -> None:
        """(b) Inside memoized_runner_safety_verdicts() two calls execute each probe once and return equal verdicts and notes."""
        counts = self._install_counting_probes()

        with hsp.memoized_runner_safety_verdicts():
            v1, n1 = hsp.probe_runner_safety_capabilities()
            for cap, c in counts.items():
                self.assertEqual(c[0], 1, f"Expected 1 execution for {cap}")

            v2, n2 = hsp.probe_runner_safety_capabilities()
            for cap, c in counts.items():
                self.assertEqual(c[0], 1, f"Expected probe count for {cap} to remain 1")

            self.assertEqual(v1, v2)
            self.assertEqual(n1, n2)

    def test_swapping_probe_callable_inside_scope_re_executes_it(self) -> None:
        """(c) Swapping a probe callable inside the scope re-executes it."""
        counts = self._install_counting_probes()
        target_cap = hsp.CAP_FRESH_VERIFIER_SESSION

        with hsp.memoized_runner_safety_verdicts():
            v1, n1 = hsp.probe_runner_safety_capabilities()
            self.assertEqual(counts[target_cap][0], 1)
            self.assertEqual(n1[target_cap], f"{target_cap}-ok")

            # Swap probe callable for target_cap
            new_probe_called = [0]

            def replacement_probe() -> Tuple[bool, str]:
                new_probe_called[0] += 1
                return True, "replacement-probe-ran"

            hsp._RUNNER_SAFETY_PROBES[target_cap] = replacement_probe

            v2, n2 = hsp.probe_runner_safety_capabilities()
            # Old probe count unchanged, new probe called once
            self.assertEqual(counts[target_cap][0], 1)
            self.assertEqual(new_probe_called[0], 1)
            self.assertEqual(n2[target_cap], "replacement-probe-ran")

            # Calling again should use memo for replacement probe
            v3, n3 = hsp.probe_runner_safety_capabilities()
            self.assertEqual(new_probe_called[0], 1)
            self.assertEqual(n3[target_cap], "replacement-probe-ran")

    def test_forced_verdict_wins_and_is_not_cached(self) -> None:
        """(d) A forced verdict via forced_runner_safety_verdicts inside the memo scope wins and is not cached for later unforced calls."""
        counts = self._install_counting_probes()
        target_cap = hsp.CAP_FRESH_VERIFIER_SESSION

        with hsp.memoized_runner_safety_verdicts():
            # First, check that forced verdict precedes probe execution and is not cached
            with hsp.forced_runner_safety_verdicts(
                {target_cap: (False, "forced-denial")}
            ):
                v_forced, n_forced = hsp.probe_runner_safety_capabilities()
                self.assertFalse(v_forced[target_cap])
                self.assertIn("FORCED VERDICT", n_forced[target_cap])
                self.assertIn("forced-denial", n_forced[target_cap])
                # Probe was never executed
                self.assertEqual(counts[target_cap][0], 0)

            # After forced scope exits, unforced call should execute the real probe
            v_after, n_after = hsp.probe_runner_safety_capabilities()
            self.assertTrue(v_after[target_cap])
            self.assertEqual(n_after[target_cap], f"{target_cap}-ok")
            self.assertEqual(counts[target_cap][0], 1)

            # Second unforced call uses memo (does not re-execute)
            v_after2, n_after2 = hsp.probe_runner_safety_capabilities()
            self.assertEqual(counts[target_cap][0], 1)
            self.assertEqual(v_after, v_after2)

            # Forced verdict also overrides an already-memoized probe without shadowing it permanently
            with hsp.forced_runner_safety_verdicts(
                {target_cap: (False, "forced-second")}
            ):
                v_forced2, n_forced2 = hsp.probe_runner_safety_capabilities()
                self.assertFalse(v_forced2[target_cap])
                self.assertIn("forced-second", n_forced2[target_cap])
                self.assertEqual(counts[target_cap][0], 1)

            # Back to unforced call: returns the memoized verdict
            v_after3, n_after3 = hsp.probe_runner_safety_capabilities()
            self.assertTrue(v_after3[target_cap])
            self.assertEqual(n_after3[target_cap], f"{target_cap}-ok")
            self.assertEqual(counts[target_cap][0], 1)

    def test_memo_disabled_after_context_exit_including_on_raise(self) -> None:
        """(e) The memo is disabled again after the context exits, including after the body raises."""
        self.assertIsNone(hsp._RUNNER_SAFETY_MEMO)

        # Normal exit
        with hsp.memoized_runner_safety_verdicts():
            self.assertIsNotNone(hsp._RUNNER_SAFETY_MEMO)
        self.assertIsNone(hsp._RUNNER_SAFETY_MEMO)

        # Exception in body
        with self.assertRaises(ZeroDivisionError):
            with hsp.memoized_runner_safety_verdicts():
                self.assertIsNotNone(hsp._RUNNER_SAFETY_MEMO)
                _ = 1 / 0
        self.assertIsNone(hsp._RUNNER_SAFETY_MEMO)

        # Restores previous memo if nested
        outer_memo = {}
        with hsp.memoized_runner_safety_verdicts(outer_memo):
            self.assertIs(hsp._RUNNER_SAFETY_MEMO, outer_memo)
            inner_memo = {}
            with hsp.memoized_runner_safety_verdicts(inner_memo):
                self.assertIs(hsp._RUNNER_SAFETY_MEMO, inner_memo)
            self.assertIs(hsp._RUNNER_SAFETY_MEMO, outer_memo)
        self.assertIsNone(hsp._RUNNER_SAFETY_MEMO)
