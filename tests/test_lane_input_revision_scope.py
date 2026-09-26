"""Tests for scoping lane input revisions to their turn (IPD xzroy8, spec 7ckptx R5.1a / A12b)."""

from __future__ import annotations

import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from agent_workflows import lane_containment, oc_runipd


class LaneInputRevisionScopeTests(unittest.TestCase):
    """Verify each isolated turn attaches the plan/inputs from ITS OWN revision."""

    def _capture_argv(
        self,
        *,
        item: dict,
        plan_path: Path,
        work_dir: str | None = None,
        runbook_path: Path | None = None,
    ) -> list[str]:
        captured: dict[str, list[str]] = {}

        class _Proc:
            def __init__(self, argv):
                captured["argv"] = argv
                self.stdout = io.StringIO("")
                self.stderr = io.StringIO("")
                self.returncode = 0

            def wait(self, timeout=None):
                return 0

            def poll(self):
                return 0

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = root / "run"
            for name in ("sessions", "outcomes", "prompts", "logs"):
                (run_dir / name).mkdir(parents=True, exist_ok=True)
            prompt = root / "prompt.txt"
            prompt.write_text("prompt content", encoding="utf-8")
            state = {
                "run_id": "run-scope-test",
                "repo": str(root),
                "session_id": None,
                "set_sessions": {},
                "session_turn_counts": {},
                "options": {"opencode": "opencode"},
            }
            if runbook_path:
                state["runbook"] = str(runbook_path)

            with mock.patch.object(
                oc_runipd.subprocess,
                "Popen",
                side_effect=lambda argv, **_kw: _Proc(argv),
            ):
                try:
                    oc_runipd.run_opencode(
                        state,
                        run_dir,
                        item,
                        plan_path,
                        prompt,
                        1,
                        work_dir=work_dir,
                    )
                except Exception:
                    pass
        return captured.get("argv") or []

    def test_review_turn_attaches_own_turn_revision_not_latest(self):
        """E-03: review sweep turn attaches its own revision (rev-3), not latest on disk (rev-5)."""
        with tempfile.TemporaryDirectory() as temp:
            lane = Path(temp) / "lane"
            lane.mkdir()
            planA = Path(temp) / "planA.ipd.md"
            planB = Path(temp) / "planB.ipd.md"
            planA.write_text("# PLAN A\n", encoding="utf-8")
            planB.write_text("# PLAN B\n", encoding="utf-8")

            # Out-of-position dispatch order: plan B at rev-5, plan A at rev-3
            lane_containment.materialize_lane_inputs(
                lane_root=lane, plan_path=planB, revision=5
            )
            lane_containment.materialize_lane_inputs(
                lane_root=lane, plan_path=planA, revision=3
            )

            item = {
                "position": 3,
                "id6": "revaaa",
                "setid": "s1",
                "action": "review",
                "attempts": [{"lane_input_revision": 3}],
            }

            argv = self._capture_argv(item=item, plan_path=planA, work_dir=str(lane))
            attachments = lane_containment.attachment_values(argv)
            self.assertEqual(len(attachments), 1)
            attached_plan = attachments[0]
            self.assertEqual(Path(attached_plan).parent.name, "rev-3")
            self.assertEqual(
                Path(attached_plan).read_text(encoding="utf-8").strip(),
                "# PLAN A",
            )

    def test_no_regression_case_a_empty_or_missing_attempt_revision_attaches_latest(
        self,
    ):
        """E-04 (a): empty attempts or missing lane_input_revision key attaches latest revision."""
        with tempfile.TemporaryDirectory() as temp:
            lane = Path(temp) / "lane"
            lane.mkdir()
            planA = Path(temp) / "planA.ipd.md"
            planB = Path(temp) / "planB.ipd.md"
            planA.write_text("# PLAN A\n", encoding="utf-8")
            planB.write_text("# PLAN B\n", encoding="utf-8")

            lane_containment.materialize_lane_inputs(
                lane_root=lane, plan_path=planA, revision=1
            )
            lane_containment.materialize_lane_inputs(
                lane_root=lane, plan_path=planB, revision=2
            )

            for attempts_variant in ([], [{}]):
                item = {
                    "position": 1,
                    "id6": "revaaa",
                    "setid": "s1",
                    "action": "review",
                    "attempts": attempts_variant,
                }
                argv = self._capture_argv(
                    item=item, plan_path=planA, work_dir=str(lane)
                )
                attachments = lane_containment.attachment_values(argv)
                self.assertEqual(len(attachments), 1)
                attached_plan = attachments[0]
                self.assertEqual(Path(attached_plan).parent.name, "rev-2")
                self.assertEqual(
                    Path(attached_plan).read_text(encoding="utf-8").strip(),
                    "# PLAN B",
                )

    def test_no_regression_case_b_non_isolated_turn_attaches_fallback(self):
        """E-04 (b): non-isolated turn (work_dir=None) attaches fallback unchanged."""
        with tempfile.TemporaryDirectory() as temp:
            planA = Path(temp) / "planA.ipd.md"
            planA.write_text("# PLAN A\n", encoding="utf-8")

            item = {
                "position": 1,
                "id6": "revaaa",
                "setid": "s1",
                "action": "review",
                "attempts": [{"lane_input_revision": 1}],
            }
            argv = self._capture_argv(item=item, plan_path=planA, work_dir=None)
            attachments = lane_containment.attachment_values(argv)
            self.assertEqual(attachments, [str(planA)])

    def test_no_regression_case_c_execute_turn_localizes_runbook_to_same_turn_revision(
        self,
    ):
        """E-04 (c): execute turn localizes runbook attachment to same turn revision as plan."""
        with tempfile.TemporaryDirectory() as temp:
            lane = Path(temp) / "lane"
            lane.mkdir()
            plan = Path(temp) / "plan.ipd.md"
            runbook = Path(temp) / "runbook.md"
            plan.write_text("# PLAN\n", encoding="utf-8")
            runbook.write_text("# RUNBOOK\n", encoding="utf-8")

            lane_containment.materialize_lane_inputs(
                lane_root=lane,
                plan_path=plan,
                runbook_path=runbook,
                revision=1,
            )

            item = {
                "position": 1,
                "id6": "exec01",
                "setid": "s1",
                "action": "execute",
                "attempts": [{"lane_input_revision": 1}],
            }
            argv = self._capture_argv(
                item=item,
                plan_path=plan,
                work_dir=str(lane),
                runbook_path=runbook,
            )
            attachments = lane_containment.attachment_values(argv)
            self.assertEqual(len(attachments), 2)
            self.assertEqual(Path(attachments[0]).parent.name, "rev-1")
            self.assertEqual(Path(attachments[1]).parent.name, "rev-1")
            self.assertEqual(
                Path(attachments[0]).read_text(encoding="utf-8").strip(),
                "# RUNBOOK",
            )
            self.assertEqual(
                Path(attachments[1]).read_text(encoding="utf-8").strip(),
                "# PLAN",
            )


if __name__ == "__main__":
    unittest.main()
