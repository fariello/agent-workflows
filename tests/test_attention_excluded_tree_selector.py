"""Behavioral regression tests for excluded-tree selector handling in aw attention.

treegap `uxb0tz` E-06.
Guards against false refusal, silent exit, over-broadened exemption, and channel corruption.
"""

from __future__ import annotations

import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import agent_schema
from agent_workflows import attention as att
from agent_workflows import attention_contract as A


def _make_constructed_repo(root: Path) -> Path:
    """Build a minimal isolated repository with one tracked and one excluded artifact."""
    plans = root / ".aw" / "records" / "plans" / "pending"
    walkthroughs = root / ".aw" / "records" / "walkthroughs"
    roadmaps = root / ".aw" / "records" / "roadmaps"
    config = root / ".aw" / "config"
    for d in (plans, walkthroughs, roadmaps, config):
        d.mkdir(parents=True, exist_ok=True)

    (config / "project.json").write_text("{}", encoding="utf-8")

    # One tracked artifact: a pending IPD with id6 'pln001'
    (plans / "20260901-test-01-pln001-sample.ipd.md").write_text(
        "# IPD: sample plan\n\n- Status: draft\n- Id: pln001\n\n## Workflow history\n- 2026-09-01 draft (t): created.\n",
        encoding="utf-8",
    )

    # One excluded artifact: a walkthrough with id6 'wlk001'
    (walkthroughs / "20260901-test-01-wlk001-sample.walkthrough.md").write_text(
        "# Walkthrough: sample\n\nNarrative record of execution.\n",
        encoding="utf-8",
    )

    # An additional excluded artifact: a roadmap with id6 'rdm001'
    (roadmaps / "20260901-test-01-rdm001-sample.roadmap.md").write_text(
        "# Roadmap: sample\n\n- **Status:** DRAFT FOR CONSIDERATION\n\nRoadmap draft.\n",
        encoding="utf-8",
    )

    return root


def _run_attention(root: Path, **kw) -> tuple[int, str, str]:
    base = dict(
        dir=str(root),
        format=None,
        check=False,
        selectors=[],
        no_color=True,
        all=False,
        long=False,
        types=[],
        status=[],
        priority=[],
        blocking=[],
        readiness=[],
        open_questions=False,
        agent=False,
        json=False,
        id6_only=False,
        paths=False,
        filenames=False,
        details=False,
        order_by=None,
        runs=False,
        active=False,
        not_active=False,
        run_status=[],
        arcive_state=[],
        active_state=[],
    )
    base.update(kw)
    args = argparse.Namespace(**base)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = att.run(args)
    return rc, out.getvalue(), err.getvalue()


class AttentionExcludedTreeSelectorTests(unittest.TestCase):
    def test_excluded_tree_id6_exits_zero_and_names_reason(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_constructed_repo(Path(td))
            rc, out, err = _run_attention(root, selectors=["wlk001"])
            self.assertEqual(rc, 0)
            # Silence guard: output on the human surface must be non-empty (written to stderr)
            combined = out + err
            self.assertTrue(
                len(combined.strip()) > 0, "Silence guard failed: output is empty"
            )
            self.assertIn("walkthroughs", err)
            self.assertIn("wlk001", err)
            self.assertIn(".walkthrough.md", err)
            # Names the recorded tree policy reason
            wlk_policy = [p for p in A.TREE_POLICY if p.name == "walkthroughs"][0]
            self.assertIn(wlk_policy.reason, err)
            self.assertIn("aw find wlk001", err)
            # stdout must be empty on human board
            self.assertEqual(out, "")

    def test_bogus_token_still_exits_two(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_constructed_repo(Path(td))
            rc, out, err = _run_attention(root, selectors=["bogus999"])
            self.assertEqual(rc, 2)
            self.assertIn("bogus999", err)
            self.assertIn("no artifact matched selector", err)
            self.assertEqual(out, "")

    def test_mixed_invocation_exits_two_and_retains_explanation(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_constructed_repo(Path(td))
            rc, out, err = _run_attention(root, selectors=["wlk001", "bogus999"])
            self.assertEqual(rc, 2)
            # Must carry the explanation for the excluded token
            self.assertIn("wlk001", err)
            self.assertIn("walkthroughs", err)
            # AND the refusal for the bogus token
            self.assertIn("bogus999", err)
            self.assertIn("no artifact matched selector", err)
            # Verify ordering: explanation for wlk001 appears before refusal for bogus999
            wlk_idx = err.find("wlk001")
            bogus_refusal_idx = err.find("no artifact matched selector")
            self.assertTrue(
                wlk_idx < bogus_refusal_idx,
                "Ordering failed: explanation must appear before refusal",
            )

    def test_agent_surface_record_validates_as_result(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_constructed_repo(Path(td))
            rc, out, err = _run_attention(root, selectors=["wlk001"], agent=True)
            self.assertEqual(rc, 0)
            self.assertEqual(err, "")
            payload = json.loads(out)
            # Schema validation
            agent_schema.assert_valid_agent_record(payload)
            self.assertEqual(payload["kind"], "result")
            self.assertEqual(payload["outcome"], "clean")
            self.assertIs(payload["verified"], True)
            self.assertIs(payload["complete"], True)
            self.assertEqual(payload["exit"], 0)
            self.assertIn("wlk001", payload["excluded_selectors"])
            self.assertIn("wlk001", payload["excluded_tree_selectors"])
            self.assertIn("aw find wlk001", payload["next"])

    def test_list_mode_stdout_byte_identical_for_pipes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_constructed_repo(Path(td))
            # Test --paths
            rc, out, err = _run_attention(root, selectors=["wlk001"], paths=True)
            self.assertEqual(rc, 0)
            self.assertEqual(
                out,
                "",
                "List mode stdout must be 0 bytes so pipe contract is preserved",
            )
            self.assertIn("wlk001", err)

            # Test --filenames
            rc_fn, out_fn, err_fn = _run_attention(
                root, selectors=["wlk001"], filenames=True
            )
            self.assertEqual(rc_fn, 0)
            self.assertEqual(out_fn, "")
            self.assertIn("wlk001", err_fn)

            # Test --id6-only
            rc_id, out_id, err_id = _run_attention(
                root, selectors=["wlk001"], id6_only=True
            )
            self.assertEqual(rc_id, 0)
            self.assertEqual(out_id, "")
            self.assertIn("wlk001", err_id)

    def test_check_surface_replaces_validity_sentence_and_no_drift(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_constructed_repo(Path(td))
            rc, out, err = _run_attention(root, selectors=["wlk001"], check=True)
            self.assertEqual(rc, 0)
            self.assertNotIn("aw attention --check: the view is valid.", out)
            self.assertNotIn("the view is valid.", out)
            self.assertIn("wlk001", out)
            self.assertIn("walkthroughs", out)
            self.assertNotIn("drift", out.lower())
            self.assertNotIn("violation", out.lower())
            self.assertEqual(err, "")

    def test_tracked_tree_id6_not_intercepted_by_helper(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_constructed_repo(Path(td))
            # pln001 is in tracked tree 'plans'; resolve_excluded_tree_policy must return empty
            policies = att.resolve_excluded_tree_policy("pln001", root)
            self.assertEqual(policies, [])
            # And attention command should resolve it as a tracked artifact
            rc, out, err = _run_attention(root, selectors=["pln001"])
            self.assertEqual(rc, 0)
            self.assertIn("pln001", out)

    def test_roadmap_selector_exits_zero_with_reason(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_constructed_repo(Path(td))
            rc, out, err = _run_attention(root, selectors=["rdm001"])
            self.assertEqual(rc, 0)
            self.assertIn("roadmaps", err)
            self.assertIn("rdm001", err)
            rdm_policy = [p for p in A.TREE_POLICY if p.name == "roadmaps"][0]
            self.assertIn(rdm_policy.reason, err)
            self.assertIn("aw find rdm001", err)


if __name__ == "__main__":
    unittest.main()
