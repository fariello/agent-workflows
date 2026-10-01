"""Tests pinning the Section 8.8 descriptive-field bound on composed lane drift details.

Drives the real producer (attention.stranded_lane_drift) end-to-end against an isolated
fixture repository outside this checkout.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
import unittest

from agent_workflows import attention
from agent_workflows import attention_contract as A
from agent_workflows import runner_shared as rs


def _git(cwd: pathlib.Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def _make_lane_fixture_repo(root: pathlib.Path) -> pathlib.Path:
    repo = root / "repo"
    repo.mkdir(parents=True)
    for cmd in (
        ["git", "init", "-q", "-b", "main"],
        ["git", "config", "user.email", "test@example.invalid"],
        ["git", "config", "user.name", "Test"],
    ):
        subprocess.run(cmd, cwd=repo, check=True)
    (repo / "f.txt").write_text("one\n", encoding="utf-8")
    subprocess.run(["git", "add", "f.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
    (repo / ".aw" / "records").mkdir(parents=True, exist_ok=True)
    return repo


class AttentionLaneDetailBoundTests(unittest.TestCase):
    """Pin the Section 8.8 descriptive-field bound on composed lane details."""

    def test_superseded_lane_detail_satisfies_descriptive_bound(self):
        """Case (a): A SUPERSEDED lane matching live-corpus shape must satisfy is_safe_descriptive."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self.assertNotIn(".aw/worktrees", str(root))
            repo = _make_lane_fixture_repo(root)

            # Plan is executed (terminal)
            plan_dir = repo / ".aw" / "records" / "plans" / "executed"
            plan_dir.mkdir(parents=True, exist_ok=True)
            (plan_dir / "20260101-set-01-3brgb6-slug.ipd.md").write_text(
                "# IPD: probe\n\n- Id: 3brgb6\n- Status: executed\n", encoding="utf-8"
            )
            subprocess.run(
                ["git", "add", ".aw/records/plans/executed"], cwd=repo, check=True
            )
            subprocess.run(
                ["git", "commit", "-qm", "plan executed"], cwd=repo, check=True
            )

            base = _git(repo, "rev-parse", "HEAD")
            lane_dir = repo / ".aw" / "worktrees" / "3brgb6"
            branch = "aw/lane/3brgb6"
            subprocess.run(
                ["git", "worktree", "add", "-q", "-b", branch, str(lane_dir), base],
                cwd=repo,
                check=True,
            )
            (lane_dir / "work.txt").write_text("work\n", encoding="utf-8")
            subprocess.run(["git", "add", "work.txt"], cwd=lane_dir, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "lane work"], cwd=lane_dir, check=True
            )

            # Advance main so lane is not an ancestor
            (repo / "adv.txt").write_text("adv\n", encoding="utf-8")
            subprocess.run(["git", "add", "adv.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "adv main"], cwd=repo, check=True)

            # Record run state matching live corpus
            run_id = "run-20260928T160357Z-4129130"
            state_dir = rs.state_root(repo) / run_id
            state_dir.mkdir(parents=True, exist_ok=True)
            state = {
                "run_id": run_id,
                "repo": str(repo),
                "queue": [
                    {
                        "id6": "3brgb6",
                        "position": 1,
                        "status": "substantially-complete",
                        "preserved_worktree": str(lane_dir),
                        "preserved_branch": branch,
                        "preserved_lane_id": "3brgb6",
                        "preserved_base": base,
                        "preserved_disposition": "created",
                        "preserved_reason": "ended without integrating",
                        "integration_signal": "verifier",
                        "attempts": [
                            {
                                "worktree": str(lane_dir),
                                "worktree_branch": branch,
                                "worktree_lane_id": "3brgb6",
                                "worktree_base": base,
                                "integration_detail": f"gate refused in {repo}",
                            }
                        ],
                    }
                ],
            }
            (state_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

            resolved = attention._resolve_runs_repo_root(repo)
            self.assertEqual(resolved, repo)

            drifts = attention.stranded_lane_drift(repo)
            self.assertEqual(len(drifts), 1)
            drift = drifts[0]
            self.assertEqual(drift.location, branch)
            self.assertEqual(drift.rule, attention.LANE_SUPERSEDED_RULE)
            self.assertEqual(drift.severity, "info")

            # Check outcome against Section 8.8 descriptive contract
            print(f"\nCase (a) detail (len={len(drift.detail)}): {drift.detail}")
            self.assertLessEqual(
                len(drift.detail),
                A.MAX_DESCRIPTIVE_LEN,
                f"composed detail exceeds Section 8.8 bound: {len(drift.detail)} > {A.MAX_DESCRIPTIVE_LEN}",
            )
            self.assertTrue(
                A.is_safe_descriptive(drift.detail),
                "composed detail fails is_safe_descriptive",
            )

            # P16: Check required semantic facts without pinning exact sentence bytes
            # Fact 1: commits did not reach the target
            self.assertIn("commits not in", drift.detail)
            # Fact 2: plan reached a terminal directory
            self.assertIn("plan terminal", drift.detail)
            # Fact 3: work landed in a later attempt
            self.assertIn("landed by later attempt", drift.detail)
            # Fact 4: prune superseded husk rather than recover work at risk
            self.assertIn("prune superseded husk", drift.detail)
            self.assertIn("not work at risk", drift.detail)

    def test_stranded_lane_detail_satisfies_descriptive_bound(self):
        """Case (b): A STRANDED lane must satisfy is_safe_descriptive (non-regression)."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self.assertNotIn(".aw/worktrees", str(root))
            repo = _make_lane_fixture_repo(root)

            # Plan is pending (non-terminal)
            plan_dir = repo / ".aw" / "records" / "plans" / "pending"
            plan_dir.mkdir(parents=True, exist_ok=True)
            (plan_dir / "20260101-set-01-dvonrn-slug.ipd.md").write_text(
                "# IPD: probe\n\n- Id: dvonrn\n- Status: approved\n", encoding="utf-8"
            )
            subprocess.run(
                ["git", "add", ".aw/records/plans/pending"], cwd=repo, check=True
            )
            subprocess.run(
                ["git", "commit", "-qm", "plan pending"], cwd=repo, check=True
            )

            base = _git(repo, "rev-parse", "HEAD")
            lane_dir = repo / ".aw" / "worktrees" / "dvonrn"
            branch = "aw/lane/dvonrn"
            subprocess.run(
                ["git", "worktree", "add", "-q", "-b", branch, str(lane_dir), base],
                cwd=repo,
                check=True,
            )
            (lane_dir / "work.txt").write_text("work\n", encoding="utf-8")
            subprocess.run(["git", "add", "work.txt"], cwd=lane_dir, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "lane work"], cwd=lane_dir, check=True
            )

            # Advance main
            (repo / "adv.txt").write_text("adv\n", encoding="utf-8")
            subprocess.run(["git", "add", "adv.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "adv main"], cwd=repo, check=True)

            # Record run state
            run_id = "run-20260929T021205Z-3914774"
            state_dir = rs.state_root(repo) / run_id
            state_dir.mkdir(parents=True, exist_ok=True)
            state = {
                "run_id": run_id,
                "repo": str(repo),
                "queue": [
                    {
                        "id6": "dvonrn",
                        "position": 1,
                        "status": "substantially-complete",
                        "preserved_worktree": str(lane_dir),
                        "preserved_branch": branch,
                        "preserved_lane_id": "dvonrn",
                        "preserved_base": base,
                        "preserved_disposition": "created",
                        "preserved_reason": "ended without integrating",
                        "attempts": [
                            {
                                "worktree": str(lane_dir),
                                "worktree_branch": branch,
                                "worktree_lane_id": "dvonrn",
                                "worktree_base": base,
                                "integration_detail": f"gate refused in {repo}",
                            }
                        ],
                    }
                ],
            }
            (state_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

            resolved = attention._resolve_runs_repo_root(repo)
            self.assertEqual(resolved, repo)

            drifts = attention.stranded_lane_drift(repo)
            self.assertEqual(len(drifts), 1)
            drift = drifts[0]
            self.assertEqual(drift.location, branch)
            self.assertEqual(drift.rule, attention.LANE_STRANDED_RULE)
            self.assertEqual(drift.severity, "error")

            print(f"\nCase (b) detail (len={len(drift.detail)}): {drift.detail}")
            self.assertLessEqual(
                len(drift.detail),
                A.MAX_DESCRIPTIVE_LEN,
                f"composed detail exceeds Section 8.8 bound: {len(drift.detail)} > {A.MAX_DESCRIPTIVE_LEN}",
            )
            self.assertTrue(
                A.is_safe_descriptive(drift.detail),
                "composed detail fails is_safe_descriptive",
            )
            self.assertIn("holds work that is NOT reachable from", drift.detail)

    def test_extreme_prefix_shape_records_observation(self):
        """Case (c): Deliberately extreme prefix shape records length without asserting <= 300."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self.assertNotIn(".aw/worktrees", str(root))
            repo = _make_lane_fixture_repo(root)

            # Executed plan
            plan_dir = repo / ".aw" / "records" / "plans" / "executed"
            plan_dir.mkdir(parents=True, exist_ok=True)
            (plan_dir / "20260101-set-01-abc123-slug.ipd.md").write_text(
                "# IPD: probe\n\n- Id: abc123\n- Status: executed\n", encoding="utf-8"
            )
            subprocess.run(
                ["git", "add", ".aw/records/plans/executed"], cwd=repo, check=True
            )
            subprocess.run(
                ["git", "commit", "-qm", "plan executed"], cwd=repo, check=True
            )

            base = _git(repo, "rev-parse", "HEAD")
            # 40-character worktree directory name matching live corpus longest
            long_wt_name = "review-sweep-run-20260930T233654Z-235565"
            lane_dir = repo / ".aw" / "worktrees" / long_wt_name
            branch = "aw/lane/abc123"
            subprocess.run(
                ["git", "worktree", "add", "-q", "-b", branch, str(lane_dir), base],
                cwd=repo,
                check=True,
            )
            (lane_dir / "work.txt").write_text("work\n", encoding="utf-8")
            subprocess.run(["git", "add", "work.txt"], cwd=lane_dir, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "lane work"], cwd=lane_dir, check=True
            )
            # Make worktree dirty to add "uncommitted changes" to prefix
            (lane_dir / "dirty.txt").write_text("uncommitted\n", encoding="utf-8")

            # Advance main
            (repo / "adv.txt").write_text("adv\n", encoding="utf-8")
            subprocess.run(["git", "add", "adv.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "adv main"], cwd=repo, check=True)

            # Two runs to trigger "newest run X of N runs" collapse
            longest_run_id = "run-20260824T140112Z-2227235"
            older_run_id = "run-20260823T100000Z-1111111"
            for r_id in (older_run_id, longest_run_id):
                state_dir = rs.state_root(repo) / r_id
                state_dir.mkdir(parents=True, exist_ok=True)
                state = {
                    "run_id": r_id,
                    "repo": str(repo),
                    "queue": [
                        {
                            "id6": "abc123",
                            "position": 1,
                            "status": "substantially-complete",
                            "preserved_worktree": str(lane_dir),
                            "preserved_branch": branch,
                            "preserved_lane_id": "abc123",
                            "preserved_base": base,
                            "preserved_disposition": "created",
                            "preserved_reason": "ended without integrating",
                            "integration_signal": "merge-failed",
                            "attempts": [
                                {
                                    "worktree": str(lane_dir),
                                    "worktree_branch": branch,
                                    "worktree_lane_id": "abc123",
                                    "worktree_base": base,
                                    "integration_detail": f"gate refused in {repo}",
                                }
                            ],
                        }
                    ],
                }
                (state_dir / "state.json").write_text(
                    json.dumps(state), encoding="utf-8"
                )

            resolved = attention._resolve_runs_repo_root(repo)
            self.assertEqual(resolved, repo)

            drifts = attention.stranded_lane_drift(repo)
            self.assertEqual(len(drifts), 1)
            drift = drifts[0]

            # RECORDED OBSERVATION: print the composed length for this extreme shape
            print(f"\nCase (c) detail (len={len(drift.detail)}): {drift.detail}")
            print(
                f"Case (c) observation: composed length={len(drift.detail)} "
                f"against MAX_DESCRIPTIVE_LEN={A.MAX_DESCRIPTIVE_LEN} "
                f"(honest residual: {len(drift.detail) - A.MAX_DESCRIPTIVE_LEN} over bound)"
            )

            # Per PR-1102 / F-10, assert ONLY the single-line and control-character halves
            # of is_safe_descriptive; DO NOT assert len(drift.detail) <= MAX_DESCRIPTIVE_LEN
            self.assertNotIn("\n", drift.detail, "detail must be a single line")
            self.assertNotIn(
                "\r", drift.detail, "detail must not contain carriage return"
            )
            self.assertFalse(
                bool(A._CONTROL_CHAR_RE.search(drift.detail)),
                "detail must not contain control characters",
            )
