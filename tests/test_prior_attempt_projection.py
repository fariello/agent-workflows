"""Tests for the prior-attempt projection contract and first-turn delivery gate.

Spec 7ckptx R1.1/R1.3:
- An isolated turn's prior-attempt projection drops driver-only and path-bearing keys.
- A non-isolated turn receives the attempt record unchanged.
- A FIRST turn carries no prior-attempt facts in its prompt, even for allowlisted keys.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import lane_containment, runner_shared


class PriorAttemptProjectionTests(unittest.TestCase):
    """Behavioral tests for the prior-attempt projection and prompt delivery gates."""

    def test_isolated_projection_drops_driver_only_keys_and_keeps_allowlisted_ones(
        self,
    ) -> None:
        """Isolated projection drops driver-only keys (session_id, turn_correction, prompt)
        while keeping allowlisted keys (exit_code, finalize_refused); non-isolated keeps all;
        and None returns None.
        """
        attempt = {
            "turn_correction": {"what_failed": ["test"]},
            "session_id": "ses-12345",
            "prompt": "/home/user/checkout/prompt.txt",
            "exit_code": 0,
            "finalize_refused": "gate refused: missing evidence",
        }
        lane_root = Path("/tmp/lane-root")

        # Isolated turn: lane_root is provided
        projected = lane_containment.prior_attempt_summary(attempt, lane_root)
        self.assertIsNotNone(projected)
        self.assertEqual(
            projected,
            {
                "exit_code": 0,
                "finalize_refused": "gate refused: missing evidence",
            },
            "isolated turn must drop driver-only keys and preserve allowlisted keys",
        )
        self.assertNotIn("turn_correction", projected)
        self.assertNotIn("session_id", projected)
        self.assertNotIn("prompt", projected)
        self.assertIn("exit_code", projected)
        self.assertIn("finalize_refused", projected)

        # Non-isolated turn: lane_root is None (spec 7ckptx R1.3)
        non_isolated = lane_containment.prior_attempt_summary(attempt, None)
        self.assertEqual(
            non_isolated,
            attempt,
            "non-isolated turn must return the prior attempt dictionary unchanged",
        )

        # None input returns None
        self.assertIsNone(
            lane_containment.prior_attempt_summary(None, lane_root),
            "None prior input must project to None for isolated turn",
        )
        self.assertIsNone(
            lane_containment.prior_attempt_summary(None, None),
            "None prior input must project to None for non-isolated turn",
        )

    def test_a_FIRST_turn_carries_no_prior_attempt_even_for_an_allowlisted_key(
        self,
    ) -> None:
        """A first turn (recovery=False) renders 'Prior attempt: none' even if attempts exist
        with allowlisted keys.
        """
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            lane_root = repo / "lane"
            lane_root.mkdir()
            run_dir = repo / "run"
            run_dir.mkdir()
            plan_path = repo / "plan.ipd.md"
            plan_path.write_text("# IPD: test\n\n- Id: slqvmx\n", encoding="utf-8")

            item = {
                "position": 1,
                "id6": "slqvmx",
                "setid": "attemptkeys",
                "attempts": [
                    {
                        "exit_code": 1,
                        "finalize_refused": "refused reason",
                    }
                ],
            }
            state = {"run_id": "test-run", "repo": str(repo)}

            prompt = runner_shared.build_prompt(
                item,
                state,
                run_dir,
                plan_path,
                recovery=False,
                lane_root=lane_root,
                labels=runner_shared.AGY_HOST_LABELS,
            )

            prompt_lines = prompt.splitlines()
            prior_lines = [
                line for line in prompt_lines if line.startswith("Prior attempt:")
            ]
            self.assertEqual(
                len(prior_lines),
                1,
                "prompt must contain exactly one 'Prior attempt:' line",
            )
            self.assertEqual(
                prior_lines[0],
                "Prior attempt: none",
                "first turn must render 'Prior attempt: none' even when item has attempts with allowlisted keys",
            )


if __name__ == "__main__":
    unittest.main()
