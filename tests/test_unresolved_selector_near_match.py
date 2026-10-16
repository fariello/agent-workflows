"""A truncated id6 must be reported as a typo with a suggestion, not as a wrong-type refusal.

Regression: `aw oc run --action plan ufawp` (the backlog id6 is `ufawpb`) said "'ufawp' is a backlog
item (...), not an IPD plan.", which blamed the artifact TYPE although backlog items are legal
`--action plan` targets and the full id6 runs fine.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from agent_workflows import runner_shared


def _repo(tmp_path: Path) -> Path:
    (tmp_path / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    open_dir = tmp_path / ".aw" / "records" / "backlog" / "open"
    open_dir.mkdir(parents=True)
    (open_dir / "20261016-uypgvi-01-ufawpb-readiness-custom.backlog.md").write_text(
        "# Backlog: x\n\n- Id: ufawpb\n- Status: open\n- Set: uypgvi\n",
        encoding="utf-8",
    )
    return tmp_path


def test_truncated_backlog_id6_suggests_full_id6(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    msg = runner_shared.describe_unresolved_plan_selector(repo, "ufawp")
    assert "is a backlog item" not in msg
    assert "not an IPD plan" not in msg
    assert "Did you mean: ufawpb (backlog item)?" in msg


def test_exact_backlog_id6_still_identified_as_backlog(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    msg = runner_shared.describe_unresolved_plan_selector(repo, "ufawpb")
    assert "'ufawpb' is a backlog item" in msg


def test_truncated_backlog_id6_through_the_run_cli(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "oc",
            "run",
            "--action",
            "plan",
            "--prepare-only",
            "ufawp",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "Did you mean: ufawpb (backlog item)?" in out, out
    assert "is a backlog item" not in out
