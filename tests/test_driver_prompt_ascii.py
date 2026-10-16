"""Behavioral tests for driver prompt pure-ASCII invariant and lifecycle notice embedding (IPD dojh96).

Restores behavioral coverage asserting that the driver execution, recovery, and verifier
prompts rendered by oc_runipd and agy_runipd across both self_finalize modes, as well as the
lifecycle notice itself, are pure ASCII, and that prompts embed the exact notice for their
mode (GUIDING_PRINCIPLES P16).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd, ipd_lifecycle, oc_runipd


class DriverPromptAsciiTests(unittest.TestCase):
    """Behavioral pure-ASCII and lifecycle notice embedding tests."""

    def test_lifecycle_notice_is_pure_ascii_in_both_modes(self) -> None:
        """E-01: runner_owns_lifecycle_notice returns non-empty pure-ASCII text in both modes."""
        for driver_owns in (True, False):
            for run_id in (None, "run-20260101T000000Z-1"):
                with self.subTest(driver_owns=driver_owns, run_id=run_id):
                    notice = ipd_lifecycle.runner_owns_lifecycle_notice(
                        driver_owns, run_id=run_id
                    )
                    self.assertTrue(
                        notice,
                        f"Notice was empty for driver_owns={driver_owns}, run_id={run_id}",
                    )
                    bad = sorted({c for c in notice if ord(c) > 127})
                    self.assertEqual(
                        bad,
                        [],
                        f"Non-ASCII characters {bad} in lifecycle notice (driver_owns={driver_owns}, run_id={run_id})",
                    )

    def test_driver_prompts_are_pure_ascii(self) -> None:
        """E-02: all 12 driver prompt renderings are pure ASCII."""
        item = {"position": 1, "id6": "abc123", "setid": "demo", "attempts": []}
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            run_dir = base / "run"
            plan_path = base / "plan.ipd.md"
            for mod in (oc_runipd, agy_runipd):
                for self_finalize in (True, False):
                    state = {
                        "run_id": "run-20260101T000000Z-1",
                        "repo": base,
                        "options": {"self_finalize": self_finalize},
                    }
                    exec_prompt = mod.build_prompt(
                        item, state, run_dir, plan_path, False
                    )
                    recovery_prompt = mod.build_prompt(
                        item, state, run_dir, plan_path, True
                    )
                    verifier_prompt = mod.build_verifier_prompt(
                        item, state, run_dir, plan_path
                    )
                    for surface, prompt in (
                        ("exec", exec_prompt),
                        ("recovery", recovery_prompt),
                        ("verifier", verifier_prompt),
                    ):
                        with self.subTest(
                            module=mod.__name__,
                            self_finalize=self_finalize,
                            surface=surface,
                        ):
                            bad = sorted({c for c in prompt if ord(c) > 127})
                            self.assertEqual(
                                bad,
                                [],
                                f"Non-ASCII characters {bad} in {mod.__name__} {surface} (self_finalize={self_finalize})",
                            )

    def test_driver_prompts_embed_the_notice_for_their_mode(self) -> None:
        """E-03: all 12 renderings embed the notice matching their mode, and not the opposite."""
        item = {"position": 1, "id6": "abc123", "setid": "demo", "attempts": []}
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            run_dir = base / "run"
            plan_path = base / "plan.ipd.md"
            for mod in (oc_runipd, agy_runipd):
                for self_finalize in (True, False):
                    state = {
                        "run_id": "run-20260101T000000Z-1",
                        "repo": base,
                        "options": {"self_finalize": self_finalize},
                    }
                    expected_notice = ipd_lifecycle.runner_owns_lifecycle_notice(
                        self_finalize, run_id=state["run_id"]
                    )
                    opposite_notice = ipd_lifecycle.runner_owns_lifecycle_notice(
                        not self_finalize, run_id=state["run_id"]
                    )
                    exec_prompt = mod.build_prompt(
                        item, state, run_dir, plan_path, False
                    )
                    recovery_prompt = mod.build_prompt(
                        item, state, run_dir, plan_path, True
                    )
                    verifier_prompt = mod.build_verifier_prompt(
                        item, state, run_dir, plan_path
                    )
                    for surface, prompt in (
                        ("exec", exec_prompt),
                        ("recovery", recovery_prompt),
                        ("verifier", verifier_prompt),
                    ):
                        with self.subTest(
                            module=mod.__name__,
                            self_finalize=self_finalize,
                            surface=surface,
                        ):
                            self.assertIn(
                                expected_notice,
                                prompt,
                                f"{mod.__name__} {surface} (self_finalize={self_finalize}) did not embed expected notice",
                            )
                            self.assertNotIn(
                                opposite_notice,
                                prompt,
                                f"{mod.__name__} {surface} (self_finalize={self_finalize}) embedded opposite notice",
                            )


if __name__ == "__main__":
    unittest.main()
