"""Behavior tests pinning severity truth and count conservation across doctor and attention surfaces.

IPD: nwcf8j (Set sevtruth, Order 1).
Governs:
- aw doctor summary line bucket exhaustiveness (count conservation: git + names + version + other == total).
- aw attention diagnostic severity preservation (a drift's real severity is preserved into JSON/agent payloads rather than flattened to error, without altering exit codes).

Tests test observable behavior, command outputs, and exit codes only; no production source code inspection.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


from agent_workflows import runner_shared as rs
from tests.support import init_repo, run_cli


def _summary_line_buckets(output: str) -> tuple[int, int, int, int, int]:
    """Parse the aw doctor summary line into (total, git, names, version, other)."""
    pattern = re.compile(
        r"aw doctor:\s+(\d+)\s+finding\(s\)\s+\(git:\s+(\d+),\s+names:\s+(\d+),\s+version:\s+(\d+)(?:,\s+other:\s+(\d+))?\)\."
    )
    for line in output.splitlines():
        match = pattern.search(line)
        if match:
            total = int(match.group(1))
            g = int(match.group(2))
            m = int(match.group(3))
            v = int(match.group(4))
            o = int(match.group(5)) if match.group(5) is not None else 0
            return total, g, m, v, o
    raise ValueError(f"No aw doctor summary line found in output:\n{output}")


def test_doctor_summary_bucket_count_conservation(tmp_path: Path) -> None:
    """The aw doctor summary line's buckets must sum to the reported total (count conservation).

    Per E-04 and F-13: a bare fixture sums exactly (e.g. 5 findings = 0 git + 4 names + 1 version + 0 other)
    and does not discriminate. Planting a research document with outcome: adopted and consumed-by: []
    provokes the unbucketed adopted-without-consumer rule, creating a nonzero remainder at base.
    The test asserts count conservation (git + names + version + other == total).
    """
    repo = init_repo(tmp_path / "doctor_repo")

    # Plant a research doc that produces an unbucketed finding (adopted-without-consumer)
    r_dir = repo / ".aw" / "records" / "research"
    r_dir.mkdir(parents=True)
    doc = r_dir / "20260901-testset-01-tst001-test-doc.research-report.md"
    doc.write_text(
        "---\n"
        "id: tst001\n"
        "title: Test Doc\n"
        "status: active\n"
        "outcome: adopted\n"
        "consumed-by: []\n"
        "model: test-model\n"
        "---\n\n"
        "# Test Doc\n",
        encoding="utf-8",
    )

    proc = run_cli("doctor", cwd=repo)
    assert proc.returncode != 0

    total, g, m, v, o = _summary_line_buckets(proc.stdout)
    remainder_at_base = total - (g + m + v)

    # Prove the fixture deliberately provoked a nonzero residue outside (git, names, version)
    assert (
        remainder_at_base > 0
    ), f"Fixture must provoke a nonzero residue; got total={total}, g={g}, m={m}, v={v}"

    # Invariant: buckets must exhaustively account for every finding
    assert (
        g + m + v + o == total
    ), f"Doctor summary buckets do not conserve count: {g} + {m} + {v} + {o} != {total}"


def test_attention_diagnostic_preserves_drift_severity_and_exit_code(
    tmp_path: Path,
) -> None:
    """The aw attention diagnostics must preserve each drift's real severity without moving the exit code.

    Route: manufactures a non-error severity by fabricating run records in a fixture repo so
    stranded_lane_drift yields a superseded lane (attention.lane-superseded at severity='info'),
    which is faithful to F-05.
    Built under pytest's tmp_path (outside the repository) to ensure attention._resolve_runs_repo_root
    does not walk up to this checkout's lanes (F-11).
    """
    repo = init_repo(tmp_path / "attention_repo")

    # Assert fixture path is outside the git worktree of the test suite (F-11)
    assert ".aw/worktrees" not in str(repo)

    # Plant an executed plan
    plan_dir = repo / ".aw" / "records" / "plans" / "executed"
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "20260101-set-01-3brgb6-slug.ipd.md").write_text(
        "# IPD: probe\n\n- Id: 3brgb6\n- Status: executed\n", encoding="utf-8"
    )
    subprocess.run(
        ["git", "add", ".aw/records/plans/executed"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "commit", "-qm", "plan executed"], cwd=repo, check=True)

    base = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()
    lane_dir = repo / ".aw" / "worktrees" / "3brgb6"
    branch = "aw/lane/3brgb6"
    subprocess.run(
        ["git", "worktree", "add", "-q", "-b", branch, str(lane_dir), base],
        cwd=repo,
        check=True,
    )
    (lane_dir / "work.txt").write_text("work\n", encoding="utf-8")
    subprocess.run(["git", "add", "work.txt"], cwd=lane_dir, check=True)
    subprocess.run(["git", "commit", "-qm", "lane work"], cwd=lane_dir, check=True)

    # Advance main so the lane is not an ancestor
    (repo / "adv.txt").write_text("adv\n", encoding="utf-8")
    subprocess.run(["git", "add", "adv.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "adv main"], cwd=repo, check=True)

    # Fabricate run records matching superseded lane
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

    # 1. Drive --check --json path
    proc_check = run_cli("attention", "--check", "--json", cwd=repo)

    # Assertion A: Exit-code independence (drift carries info severity, which does not fail check)
    assert (
        proc_check.returncode == 0
    ), f"Expected exit code 0, got {proc_check.returncode}: {proc_check.stderr}"

    data_check = json.loads(proc_check.stdout)
    superseded_diags = [
        d
        for d in data_check.get("diagnostics", [])
        if d.get("rule") == "attention.lane-superseded" and d.get("location") == branch
    ]
    assert (
        len(superseded_diags) == 1
    ), f"Expected 1 superseded lane diagnostic for {branch}, found: {data_check.get('diagnostics')}"

    # Assertion B: Severity preservation (preserves stamped info severity instead of flattening to error)
    assert (
        superseded_diags[0]["severity"] == "info"
    ), f"Diagnostic severity was flattened to '{superseded_diags[0]['severity']}', expected 'info'"

    # 2. Drive non-check --agent --verbose path
    proc_noncheck = run_cli("attention", "--agent", "--verbose", cwd=repo)
    assert (
        proc_noncheck.returncode == 0
    ), f"Expected exit code 0, got {proc_noncheck.returncode}: {proc_noncheck.stderr}"

    data_noncheck = json.loads(proc_noncheck.stdout)
    superseded_diags_nc = [
        d
        for d in data_noncheck.get("diagnostics", [])
        if d.get("rule") == "attention.lane-superseded" and d.get("location") == branch
    ]
    assert len(superseded_diags_nc) == 1
    assert (
        superseded_diags_nc[0]["severity"] == "info"
    ), f"Non-check diagnostic severity was flattened to '{superseded_diags_nc[0]['severity']}', expected 'info'"
