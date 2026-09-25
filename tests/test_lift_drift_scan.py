from __future__ import annotations

import ast
import pathlib
import sys
import unittest

from tests import support

TOOLS_DIR = pathlib.Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import lift_drift_scan  # noqa: E402


class LiftDriftScanGuardTests(unittest.TestCase):
    """Fast guard for resolved-signature arity defects and spawn-path stop handler verbs.

    LIMITATION: A static arity check detects missing required positional or keyword-only parameters
    for bare-name calls within runner_shared. It cannot see wrong-type or wrong-value arguments when
    the argument count is satisfied.
    """

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def test_resolved_signature_arity_violations_match_allowlist(self):
        """Assert arity violation set equals exactly the allowlisted deferred entry (carrier zt2b16)."""
        head_path = lift_drift_scan.package_dir() / "runner_shared.py"
        head_tree = ast.parse(head_path.read_text(encoding="utf-8"))
        raw_violations = lift_drift_scan.scan_arity_violations(head_tree)
        found = {
            f"{caller} -> {callee} missing {missing}"
            for caller, callee, missing, _ in raw_violations
        }

        # Exact allowlist: empty set (recovone cdxcbh resolved route_recovery_turn -> save_state).
        # This is an EXACT set comparison, not a count or subset test, so any new arity defect fails the guard.
        allowed: set[str] = set()
        self.assertEqual(
            found,
            allowed,
            "Resolved-signature check must match empty allowlist (no arity violations in runner_shared)",
        )

    def test_execute_item_core_spawn_path_stop_handlers_raise(self):
        """Assert execute_item_core spawn-path StopNowForce and StopAtCheckpoint handlers end in raise."""
        head_path = lift_drift_scan.package_dir() / "runner_shared.py"
        head_tree = ast.parse(head_path.read_text(encoding="utf-8"))
        handlers = lift_drift_scan.get_spawn_path_stop_handlers(head_tree)

        self.assertIn("runner_stop.StopNowForce", handlers)
        self.assertIn("runner_stop.StopAtCheckpoint", handlers)

        stop_force_verb, stop_force_style = handlers["runner_stop.StopNowForce"]
        stop_cp_verb, stop_cp_style = handlers["runner_stop.StopAtCheckpoint"]

        self.assertEqual(
            stop_force_verb,
            "raise",
            "StopNowForce spawn-path handler must end in raise (not return)",
        )
        self.assertEqual(
            stop_cp_verb,
            "raise",
            "StopAtCheckpoint spawn-path handler must end in raise (not return)",
        )
        self.assertEqual(
            stop_force_style,
            "via-call",
            "StopNowForce spawn-path handler must assign item status via reconcile_disposition call",
        )
        self.assertEqual(
            stop_cp_style,
            "via-call",
            "StopAtCheckpoint spawn-path handler must assign item status via reconcile_disposition call",
        )


if __name__ == "__main__":
    unittest.main()
