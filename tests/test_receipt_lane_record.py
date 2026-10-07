"""Behavioral regression tests for recording allocated lane in begin receipt (42ertq / m94le9).

Tests outcomes, not code structure (no inspect, ast, regex, or line number pinning).
Consumes tests.support.scope_drift_repo for real git fixtures.
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import (
    agy_runipd,
    check_engine,
    ipd_lifecycle,
    oc_runipd,
    runner_shared,
    worktree_lease,
)
from tests import support


class TestReceiptLaneRecord(unittest.TestCase):
    """Behavioral tests covering all requirements of IPD 42ertq."""

    # -------------------------------------------------------------------------
    # Case (a): The Defect (F-13 heuristic misattribution and contrast)
    # -------------------------------------------------------------------------

    def test_case_a_heuristic_misattribution_and_contrast(self) -> None:
        """Case (a): F-13 heuristic misattribution resolved by recorded lane.

        Subcase 1: Canonical lane abandoned with out-of-scope 'stale.py'. Live
        _attempt2 lane is freshly allocated (uncommitted). With lane recorded:
        0 findings, returns _attempt2.
        Contrast (withheld record): false positive naming 'stale.py', returns canonical.

        Subcase 2 (mirror): Canonical and _attempt3 hold in-scope work. Live _attempt2 lane
        has out-of-scope 'extra.py'. With lane recorded: 1 finding naming 'extra.py'.
        Contrast (withheld record): 0 findings (heuristic selects _attempt3, missing drift).

        Subcase 3 (reused attempt): Abandoned _attempt3 holding work, live re-allocated
        _attempt2. With lane recorded: selects _attempt2. Contrast: selects _attempt3.
        """
        # --- Subcase 1: False-positive prevention ---
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            root, lane_path = support.scope_drift_repo(
                tpath, plan_id="pid001", scope_paths="src/demo.py"
            )
            base = support.git(root, "rev-parse", "HEAD").stdout.strip()

            # Canonical lane commits out-of-scope 'stale.py' and is abandoned
            (lane_path / "stale.py").write_text("out-of-scope", encoding="utf-8")
            support.git(lane_path, "add", "stale.py")
            support.git(lane_path, "commit", "-m", "canonical abandoned commit", "-q")

            # Second allocation attempt-scoped to _attempt2 (clean, freshly allocated)
            handle2 = worktree_lease.allocate_worktree(root, "pid001", base_commit=base)
            self.assertEqual(handle2.branch, "aw/lane/pid001_attempt2")

            # CONTRAST WITHOUT RECORD (today's heuristic):
            tree_no_rec = check_engine._plan_execution_tree(root, "pid001", base)
            self.assertEqual(tree_no_rec, lane_path)  # Heuristic selects canonical!
            findings_no_rec = check_engine.check_scope_drift(root)
            self.assertEqual(len(findings_no_rec), 1)
            self.assertIn("stale.py", findings_no_rec[0].detail)

            # WITH RECORD:
            ok, detail = ipd_lifecycle.record_allocated_lane(
                root,
                "pid001",
                handle2.branch,
                handle2.lane_id,
                base,
                disposition=handle2.disposition,
            )
            self.assertTrue(ok, detail)

            tree_rec = check_engine._plan_execution_tree(
                root, "pid001", base, recorded_branch=handle2.branch
            )
            self.assertEqual(tree_rec, handle2.path)
            findings_with_rec = check_engine.check_scope_drift(root)
            self.assertEqual(len(findings_with_rec), 0)

        # --- Subcase 2: Mirror case (masked true positive) ---
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            root, lane_path = support.scope_drift_repo(
                tpath, plan_id="pid002", scope_paths="src/demo.py"
            )
            base = support.git(root, "rev-parse", "HEAD").stdout.strip()

            # Commit seed in canonical so next is attempt2
            (lane_path / "seed.txt").write_text("seed", encoding="utf-8")
            support.git(lane_path, "add", ".")
            support.git(lane_path, "commit", "-m", "seed canonical", "-q")

            h2 = worktree_lease.allocate_worktree(root, "pid002", base_commit=base)
            (h2.path / "seed2.txt").write_text("seed2", encoding="utf-8")
            support.git(h2.path, "add", ".")
            support.git(h2.path, "commit", "-m", "seed h2", "-q")

            # h3 (abandoned): commit in-scope work
            h3 = worktree_lease.allocate_worktree(root, "pid002", base_commit=base)
            (h3.path / "src").mkdir(parents=True, exist_ok=True)
            (h3.path / "src/demo.py").write_text("in-scope", encoding="utf-8")
            support.git(h3.path, "add", ".")
            support.git(h3.path, "commit", "-m", "in-scope h3", "-q")

            # Teardown h2 and re-allocate it as live lane
            worktree_lease.teardown_worktree(root, h2)
            h2_live = worktree_lease.allocate_worktree(root, "pid002", base_commit=base)

            # In h2_live: commit out-of-scope work
            (h2_live.path / "extra.py").write_text("drift", encoding="utf-8")
            support.git(h2_live.path, "add", ".")
            support.git(h2_live.path, "commit", "-m", "drift h2_live", "-q")

            # CONTRAST WITHOUT RECORD: heuristic selects h3 (attempt 3 > 2), so drift is missed!
            tree_no_rec = check_engine._plan_execution_tree(root, "pid002", base)
            self.assertEqual(tree_no_rec, h3.path)
            findings_no_rec = check_engine.check_scope_drift(root)
            self.assertEqual(len(findings_no_rec), 0)

            # WITH RECORD: records h2_live -> reported!
            ok, detail = ipd_lifecycle.record_allocated_lane(
                root,
                "pid002",
                h2_live.branch,
                h2_live.lane_id,
                base,
                disposition=h2_live.disposition,
            )
            self.assertTrue(ok, detail)

            tree_rec = check_engine._plan_execution_tree(
                root, "pid002", base, recorded_branch=h2_live.branch
            )
            self.assertEqual(tree_rec, h2_live.path)
            findings_with_rec = check_engine.check_scope_drift(root)
            self.assertEqual(len(findings_with_rec), 1)
            self.assertIn("extra.py", findings_with_rec[0].detail)

        # --- Subcase 3: Reused attempt number shape ---
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            root, lane_path = support.scope_drift_repo(
                tpath, plan_id="pid003", scope_paths="src/demo.py"
            )
            base = support.git(root, "rev-parse", "HEAD").stdout.strip()

            (lane_path / "seed.txt").write_text("seed", encoding="utf-8")
            support.git(lane_path, "add", ".")
            support.git(lane_path, "commit", "-m", "canonical seed", "-q")

            h2 = worktree_lease.allocate_worktree(root, "pid003", base_commit=base)
            (h2.path / "seed2.txt").write_text("seed2", encoding="utf-8")
            support.git(h2.path, "add", ".")
            support.git(h2.path, "commit", "-m", "h2 seed", "-q")

            h3 = worktree_lease.allocate_worktree(root, "pid003", base_commit=base)
            self.assertEqual(h3.branch, "aw/lane/pid003_attempt3")

            # Commit in attempt3 (abandoned)
            (h3.path / "src").mkdir(parents=True, exist_ok=True)
            (h3.path / "src/demo.py").write_text("v3", encoding="utf-8")
            support.git(h3.path, "add", ".")
            support.git(h3.path, "commit", "-m", "attempt3 work", "-q")

            # Teardown attempt2 and re-allocate it
            worktree_lease.teardown_worktree(root, h2)
            h2_reused = worktree_lease.allocate_worktree(
                root, "pid003", base_commit=base
            )
            self.assertEqual(h2_reused.branch, "aw/lane/pid003_attempt2")
            (h2_reused.path / "src").mkdir(parents=True, exist_ok=True)
            (h2_reused.path / "src/demo.py").write_text("v2-reused", encoding="utf-8")
            support.git(h2_reused.path, "add", ".")
            support.git(h2_reused.path, "commit", "-m", "reused attempt2 work", "-q")

            # WITHOUT RECORD: heuristic tie-breaks on highest attempt -> h3!
            tree_heuristic = check_engine._plan_execution_tree(root, "pid003", base)
            self.assertEqual(tree_heuristic, h3.path)

            # WITH RECORD: selects h2_reused
            ok, detail = ipd_lifecycle.record_allocated_lane(
                root, "pid003", h2_reused.branch, h2_reused.lane_id, base
            )
            self.assertTrue(ok, detail)
            tree_rec = check_engine._plan_execution_tree(
                root, "pid003", base, recorded_branch=h2_reused.branch
            )
            self.assertEqual(tree_rec, h2_reused.path)

    # -------------------------------------------------------------------------
    # Case (b): The Prohibition (untouched base_head and digests)
    # -------------------------------------------------------------------------

    def test_case_b_prohibition_byte_identical_receipt_keys(self) -> None:
        """Case (b): Recording a lane leaves base_head, digests and scope keys byte-identical."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            root, lane_path = support.scope_drift_repo(tpath, plan_id="pid004")
            base = support.git(root, "rev-parse", "HEAD").stdout.strip()

            rcpt_before = ipd_lifecycle.read_receipt(root, "pid004")
            self.assertIsNotNone(rcpt_before)
            assert rcpt_before is not None

            # Add sample digests to verify they are not disturbed
            rcpt_before["plan_content_digest"] = "sha256:abc111"
            rcpt_before["frozen_region_digest"] = "sha256:abc222"
            rcpt_before["requirement_digest"] = "sha256:abc333"
            rcpt_before["scope_paths"] = ["src/demo.py"]
            rcpt_p = ipd_lifecycle.receipt_path_for(root, "pid004")
            rcpt_p.write_text(json.dumps(rcpt_before), encoding="utf-8")

            # Perform lane update
            ok, detail = ipd_lifecycle.record_allocated_lane(
                root,
                "pid004",
                branch="aw/lane/pid004_attempt2",
                lane_id="pid004_attempt2",
                base_commit=base,
                disposition="attempt-scoped",
            )
            self.assertTrue(ok, detail)

            rcpt_after = ipd_lifecycle.read_receipt(root, "pid004")
            self.assertIsNotNone(rcpt_after)
            assert rcpt_after is not None

            # Compare every key that existed before
            prohibited_keys = [
                "base_head",
                "plan_content_digest",
                "frozen_region_digest",
                "requirement_digest",
                "scope_paths",
            ]
            for key in prohibited_keys:
                self.assertIn(key, rcpt_after)
                self.assertEqual(
                    rcpt_before[key],
                    rcpt_after[key],
                    f"Key {key!r} changed across record_allocated_lane",
                )

            for key, val in rcpt_before.items():
                self.assertEqual(
                    val,
                    rcpt_after[key],
                    f"Pre-existing key {key!r} was mutated across update",
                )

            # Lane block is newly added and correctly populated
            self.assertIn("lane", rcpt_after)
            lane_block = rcpt_after["lane"]
            self.assertEqual(lane_block["branch"], "aw/lane/pid004_attempt2")
            self.assertEqual(lane_block["lane_id"], "pid004_attempt2")
            self.assertEqual(lane_block["base_commit"], base)
            self.assertEqual(lane_block["disposition"], "attempt-scoped")
            self.assertTrue(bool(lane_block["recorded_at"]))

    # -------------------------------------------------------------------------
    # Case (c): Backward Compatibility (v1, v2, v3 without lane block)
    # -------------------------------------------------------------------------

    def test_case_c_backward_compatibility_v1_v2_v3_without_lane(self) -> None:
        """Case (c): Receipts without lane block (v1, v2, and v3) remain fully compatible."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            root, lane_path = support.scope_drift_repo(tpath, plan_id="pid005")
            base = support.git(root, "rev-parse", "HEAD").stdout.strip()

            plan_p = (
                root
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20260901-demo-01-pid005-demo.ipd.md"
            )
            plan_text = plan_p.read_text(encoding="utf-8")
            p_digest = ipd_lifecycle.plan_content_digest(plan_text)
            f_digest = ipd_lifecycle.frozen_region_digest(plan_text)

            # 1. Schema v1 receipt (no frozen_region_digest, no lane)
            rcpt_v1 = {
                "schema_version": 1,
                "kind": "ipd_begin_receipt",
                "plan_id": "pid005",
                "base_head": base,
                "plan_content_digest": p_digest,
            }
            self.assertTrue(ipd_lifecycle.receipt_is_current(rcpt_v1, plan_text))

            # 2. Schema v2 receipt (frozen_region_digest, no lane)
            rcpt_v2 = {
                "schema_version": 2,
                "kind": "ipd_begin_receipt",
                "plan_id": "pid005",
                "base_head": base,
                "plan_content_digest": p_digest,
                "frozen_region_digest": f_digest,
            }
            self.assertTrue(ipd_lifecycle.receipt_is_current(rcpt_v2, plan_text))

            # 3. Schema v3 receipt written by real ipd_lifecycle.begin (no lane)
            rcpt_path = ipd_lifecycle.receipt_path_for(root, "pid005")
            rcpt_path.unlink(missing_ok=True)
            begin_res = ipd_lifecycle.begin(
                root, plan_p, actor="test-runner", timestamp="2026-10-07T00:00:00Z"
            )
            self.assertEqual(
                begin_res.exit_code, ipd_lifecycle.EXIT_OK, begin_res.message
            )
            rcpt_v3 = ipd_lifecycle.read_receipt(root, "pid005")
            self.assertIsNotNone(rcpt_v3)
            assert rcpt_v3 is not None
            self.assertEqual(rcpt_v3["schema_version"], 3)
            self.assertNotIn("lane", rcpt_v3)
            self.assertTrue(ipd_lifecycle.receipt_is_current(rcpt_v3, plan_text))

            # Candidate enumeration fallback runs cleanly on all
            exec_tree = check_engine._plan_execution_tree(root, "pid005", base)
            self.assertEqual(exec_tree, lane_path)

    # -------------------------------------------------------------------------
    # Case (d): Absent / Reclaimed Lane degrades to silence
    # -------------------------------------------------------------------------

    def test_case_d_absent_lane_degrades_to_silence(self) -> None:
        """Case (d): A recorded branch that is gone returns None and emits neither

        check.scope-drift nor check.scope-not-audited even if an un-recorded sibling holds work.
        """
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            root, lane_path = support.scope_drift_repo(
                tpath, plan_id="pid006", scope_paths="src/demo.py"
            )
            base = support.git(root, "rev-parse", "HEAD").stdout.strip()

            # Canonical lane commits out-of-scope file
            (lane_path / "stale.py").write_text("drift", encoding="utf-8")
            support.git(lane_path, "add", "stale.py")
            support.git(lane_path, "commit", "-m", "canonical work", "-q")

            # Allocate attempt2, record it, then delete attempt2
            handle2 = worktree_lease.allocate_worktree(root, "pid006", base_commit=base)
            branch2 = handle2.branch
            ok, detail = ipd_lifecycle.record_allocated_lane(
                root, "pid006", branch2, handle2.lane_id, base
            )
            self.assertTrue(ok, detail)

            # Tear down attempt2 completely
            worktree_lease.teardown_worktree(root, handle2)
            subprocess.run(
                ["git", "-C", str(root), "branch", "-D", branch2],
                capture_output=True,
                check=False,
            )

            # Receipt records branch2 which is absent
            rcpt_data = ipd_lifecycle.read_receipt(root, "pid006")
            assert rcpt_data is not None
            self.assertEqual(rcpt_data.get("lane", {}).get("branch"), branch2)

            # Must return None (never fall through to canonical sibling)
            tree = check_engine._plan_execution_tree(
                root, "pid006", base, recorded_branch=branch2
            )
            self.assertIsNone(tree)

            # check_scope_drift must emit NEITHER check.scope-drift NOR check.scope-not-audited
            findings = check_engine.check_scope_drift(root)
            rules_fired = [f.rule for f in findings]
            self.assertNotIn("check.scope-drift", rules_fired)
            self.assertNotIn("check.scope-not-audited", rules_fired)
            self.assertEqual(len(findings), 0)

    # -------------------------------------------------------------------------
    # Case (e): One Site, Both Hosts (execute_item_core with oc and agy)
    # -------------------------------------------------------------------------

    def test_case_e_one_site_both_hosts(self) -> None:
        """Case (e): execute_item_core records lane for both oc_runipd and agy_runipd."""
        for driver_mod, host_lbls in [
            (oc_runipd, runner_shared.OC_HOST_LABELS),
            (agy_runipd, runner_shared.AGY_HOST_LABELS),
        ]:
            with self.subTest(driver=driver_mod.__name__):
                with tempfile.TemporaryDirectory() as td:
                    tpath = Path(td)
                    repo = tpath / "repo"
                    repo.mkdir()
                    subprocess.run(
                        ["git", "init", "-b", "main", str(repo)],
                        check=True,
                        capture_output=True,
                    )
                    subprocess.run(
                        ["git", "-C", str(repo), "config", "user.name", "Tester"],
                        check=True,
                    )
                    subprocess.run(
                        [
                            "git",
                            "-C",
                            str(repo),
                            "config",
                            "user.email",
                            "test@example.com",
                        ],
                        check=True,
                    )
                    (repo / "README.md").write_text("init", encoding="utf-8")
                    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
                    subprocess.run(
                        ["git", "-C", str(repo), "commit", "-m", "init"], check=True
                    )

                    plan_id = "pid007"
                    plan_dir = repo / ".aw/records/plans/pending"
                    plan_dir.mkdir(parents=True)
                    plan_p = plan_dir / f"20261001-demo-01-{plan_id}-demo.ipd.md"
                    plan_p.write_text(
                        f"# IPD: Demo\n\n- Id: {plan_id}\n- Set: demo\n- Status: approved\n- Scope-Paths: src/demo.py\n\n## Goal\nDemo\n",
                        encoding="utf-8",
                    )
                    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
                    subprocess.run(
                        ["git", "-C", str(repo), "commit", "-m", "plan"], check=True
                    )
                    base = subprocess.run(
                        ["git", "-C", str(repo), "rev-parse", "HEAD"],
                        capture_output=True,
                        text=True,
                        check=True,
                    ).stdout.strip()

                    # Pre-create canonical lane aw/lane/<id6> holding a commit to force
                    # attempt-scoped allocation: aw/lane/<id6>_attempt2
                    canonical_lane = worktree_lease.allocate_worktree(
                        repo, plan_id, base_commit=base
                    )
                    (canonical_lane.path / "seed.txt").write_text(
                        "seed", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "-C", str(canonical_lane.path), "add", "."], check=True
                    )
                    subprocess.run(
                        [
                            "git",
                            "-C",
                            str(canonical_lane.path),
                            "commit",
                            "-m",
                            "seed",
                        ],
                        check=True,
                    )

                    run_dir = tpath / "run"
                    run_dir.mkdir()
                    (run_dir / "outcomes").mkdir()
                    (run_dir / "logs").mkdir()
                    (run_dir / "prompts").mkdir()
                    prompt_p = run_dir / "prompts/p.md"
                    prompt_p.write_text("prompt", encoding="utf-8")

                    item = {
                        "id6": plan_id,
                        "setid": "demo",
                        "action": "execute",
                        "position": 1,
                        "configured_file": str(plan_p),
                        "status": "queued",
                        "attempts": [],
                    }
                    state = {
                        "options": {
                            "isolate_worktree": True,
                            "validate": False,
                            "self_finalize": True,
                        },
                        "repo": str(repo),
                        "run_id": f"run-{driver_mod.__name__}",
                        "queue": [item],
                    }

                    # Mock driver_begin to write a real v3 receipt
                    def fake_begin(
                        r: Path, i6: str, actor: str, **kwargs: object
                    ) -> tuple[int, str]:
                        rcpt = ipd_lifecycle.receipt_path_for(r, i6)
                        rcpt.parent.mkdir(parents=True, exist_ok=True)
                        rcpt.write_text(
                            json.dumps(
                                {
                                    "schema_version": 3,
                                    "kind": "ipd_begin_receipt",
                                    "plan_id": i6,
                                    "base_head": base,
                                }
                            ),
                            encoding="utf-8",
                        )
                        return 0, "ok"

                    def fake_executor(
                        *args: object, **kwargs: object
                    ) -> tuple[int, str, Path, list[str]]:
                        outcome = run_dir / f"outcomes/01-{plan_id}.json"
                        outcome.write_text(
                            json.dumps(
                                {
                                    "disposition": "executed",
                                    "defect_report": {
                                        "state": "none-found",
                                        "findings": [],
                                    },
                                    "pushed": False,
                                }
                            ),
                            encoding="utf-8",
                        )
                        return 0, "sess", run_dir / "logs/t.log", ["agent"]

                    with mock.patch(
                        "agent_workflows.runner_shared.driver_begin",
                        side_effect=fake_begin,
                    ):
                        with mock.patch(
                            "agent_workflows.runner_shared.driver_finalize",
                            return_value=(0, "ok"),
                        ):
                            runner_shared.execute_item_core(
                                run_dir,
                                state,
                                item,
                                recovery=False,
                                host_labels=host_lbls,
                                spawn_executor=fake_executor,
                                spawn_verifier=lambda *a, **k: (0, "v", None, []),
                                raw_launcher=lambda *a, **k: None,
                                run_suite_check=lambda p, s: None,
                                process_backlog_close=lambda *a, **k: None,
                                driver_module=driver_mod,
                            )

                    # Read receipt from disk
                    rcpt_data = ipd_lifecycle.read_receipt(repo, plan_id)
                    self.assertIsNotNone(rcpt_data)
                    assert rcpt_data is not None
                    lane_rec = rcpt_data.get("lane", {})
                    self.assertEqual(
                        lane_rec.get("branch"), f"aw/lane/{plan_id}_attempt2"
                    )
                    self.assertEqual(lane_rec.get("disposition"), "attempt-scoped")

                    # Verify events.jsonl recorded both worktree-allocated and receipt-lane-recorded
                    events = [
                        json.loads(line)
                        for line in (run_dir / "events.jsonl")
                        .read_text(encoding="utf-8")
                        .splitlines()
                    ]
                    wt_events = [
                        e for e in events if e.get("event") == "worktree-allocated"
                    ]
                    rec_events = [
                        e for e in events if e.get("event") == "receipt-lane-recorded"
                    ]
                    self.assertEqual(len(wt_events), 1)
                    self.assertEqual(len(rec_events), 1)
                    self.assertEqual(
                        wt_events[0]["branch"], f"aw/lane/{plan_id}_attempt2"
                    )
                    self.assertEqual(rec_events[0]["branch"], wt_events[0]["branch"])
                    self.assertEqual(lane_rec.get("lane_id"), wt_events[0]["lane_id"])
                    self.assertTrue(rec_events[0]["updated"])

    # -------------------------------------------------------------------------
    # Case (f): Non-fatal when No Receipt Present
    # -------------------------------------------------------------------------

    def test_case_f_non_fatal_when_no_receipt(self) -> None:
        """Case (f): When allocation runs with no receipt present, disposition is unchanged

        and receipt-lane-recorded event records refusal without failing the turn.
        """
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            repo = tpath / "repo"
            repo.mkdir()
            subprocess.run(
                ["git", "init", "-b", "main", str(repo)],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.name", "Tester"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "config",
                    "user.email",
                    "test@example.com",
                ],
                check=True,
            )
            (repo / "README.md").write_text("init", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True)

            plan_id = "pid008"
            plan_dir = repo / ".aw/records/plans/pending"
            plan_dir.mkdir(parents=True)
            plan_p = plan_dir / f"20261001-demo-01-{plan_id}-demo.ipd.md"
            plan_p.write_text(
                f"# IPD: Demo\n\n- Id: {plan_id}\n- Set: demo\n- Status: approved\n- Scope-Paths: src/demo.py\n\n## Goal\nDemo\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "plan"], check=True)

            run_dir = tpath / "run"
            run_dir.mkdir()
            (run_dir / "outcomes").mkdir()
            (run_dir / "logs").mkdir()
            (run_dir / "prompts").mkdir()
            prompt_p = run_dir / "prompts/p.md"
            prompt_p.write_text("prompt", encoding="utf-8")

            item = {
                "id6": plan_id,
                "setid": "demo",
                "action": "execute",
                "position": 1,
                "configured_file": str(plan_p),
                "status": "queued",
                "attempts": [],
            }
            state = {
                "options": {
                    "isolate_worktree": True,
                    "validate": False,
                    "self_finalize": True,
                },
                "repo": str(repo),
                "run_id": "run-no-rcpt",
                "queue": [item],
            }

            # driver_begin succeeds but deliberately writes NO receipt
            def fake_begin(
                r: Path, i6: str, actor: str, **kwargs: object
            ) -> tuple[int, str]:
                return 0, "ok"

            def fake_executor(
                *args: object, **kwargs: object
            ) -> tuple[int, str, Path, list[str]]:
                outcome = run_dir / f"outcomes/01-{plan_id}.json"
                outcome.write_text(
                    json.dumps(
                        {
                            "disposition": "executed",
                            "defect_report": {"state": "none-found", "findings": []},
                            "pushed": False,
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "sess", run_dir / "logs/t.log", ["agent"]

            with mock.patch(
                "agent_workflows.runner_shared.driver_begin", side_effect=fake_begin
            ):
                with mock.patch(
                    "agent_workflows.runner_shared.driver_finalize",
                    return_value=(0, "ok"),
                ):
                    runner_shared.execute_item_core(
                        run_dir,
                        state,
                        item,
                        recovery=False,
                        host_labels=runner_shared.OC_HOST_LABELS,
                        spawn_executor=fake_executor,
                        spawn_verifier=lambda *a, **k: (0, "v", None, []),
                        raw_launcher=lambda *a, **k: None,
                        run_suite_check=lambda p, s: None,
                        process_backlog_close=lambda *a, **k: None,
                        driver_module=oc_runipd,
                    )

            # Turn disposition was NOT failed by the missing receipt
            self.assertNotEqual(item.get("status"), "fail-lane")

            # Check events.jsonl
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            rec_events = [
                e for e in events if e.get("event") == "receipt-lane-recorded"
            ]
            self.assertEqual(len(rec_events), 1)
            self.assertFalse(rec_events[0]["updated"])
            self.assertIn("no readable begin receipt", rec_events[0]["detail"])
