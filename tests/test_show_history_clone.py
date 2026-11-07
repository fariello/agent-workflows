"""AC-2 of spec `4sd62s`: a `git clone --depth 1` contains the full state and history (IPD `1ajqaa` E-08).

The fixture is a migrated-copy plan: its metadata is in the LOG format, four events written
directly with `artifact_meta.encode_event` into `meta/<id6>.jsonl`, plus the two-key front-matter
mirror. It does not go through `artifact_meta.create`/`append` (a later plan makes `append` write
the legacy format while a repository is unmigrated) and does not depend on `aw migrate metadata`.
The test commits, makes a shallow clone with no `.aw/state/`, and runs `aw show --history` there
as a subprocess, so nothing from the source repository's cache can leak into the answer.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agent_workflows import artifact_meta

pytestmark = pytest.mark.core

ID6 = "cl0001"
NAME = f"20261106-clset-01-{ID6}-cloned-plan.ipd.md"
PKG_ROOT = Path(__file__).resolve().parent.parent


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True
    )


def test_depth_one_clone_shows_full_state_and_history(tmp_path: Path) -> None:
    src = tmp_path / "src"
    records = src / ".aw" / "records"
    (records / "plans" / "pending").mkdir(parents=True)
    (records / "meta").mkdir(parents=True)
    _git(tmp_path, "init", "-q", str(src))
    path = f"plans/pending/{NAME}"
    events = [
        {
            "v": 1,
            "seq": 1,
            "append": 1,
            "at": "2026-11-06T12:00:00Z",
            "actor": {"tool": "aw"},
            "op": "create",
            "path": path,
            "fields": {
                "id": ID6,
                "type": "ipd",
                "status": "draft",
                "set": "clset",
                "order": 1,
                "title": "Cloned plan",
            },
        },
        {
            "v": 1,
            "seq": 2,
            "append": 2,
            "at": "2026-11-06T12:01:00Z",
            "actor": {"tool": "aw"},
            "op": "transition",
            "from": "draft",
            "to": "to-review",
        },
        {
            "v": 1,
            "seq": 3,
            "append": 3,
            "at": "2026-11-06T12:02:00Z",
            "actor": {"tool": "aw"},
            "op": "set",
            "fields": {"blocks_release": "next"},
        },
        {
            "v": 1,
            "seq": 4,
            "append": 4,
            "at": "2026-11-06T12:03:00Z",
            "actor": {"tool": "aw"},
            "op": "review",
            "review_kind": "gate",
            "round": 1,
            "verdict": "APPROVE",
        },
    ]
    (records / "meta" / f"{ID6}.jsonl").write_text(
        "".join(artifact_meta.encode_event(e) for e in events), encoding="utf-8"
    )
    (records / "plans" / "pending" / NAME).write_text(
        f"---\nid: {ID6}\nstatus: to-review\n---\n# IPD: Cloned plan\n\nBody.\n",
        encoding="utf-8",
    )
    (src / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
    _git(src, "add", ".gitignore", ".aw/records")
    _git(
        src,
        "-c",
        "user.email=t@example.invalid",
        "-c",
        "user.name=t",
        "commit",
        "-q",
        "-m",
        "x",
    )
    # A second commit, so that `--depth 1` really truncates history.
    (src / "README").write_text("r\n", encoding="utf-8")
    _git(src, "add", "README")
    _git(
        src,
        "-c",
        "user.email=t@example.invalid",
        "-c",
        "user.name=t",
        "commit",
        "-q",
        "-m",
        "y",
    )

    clone = tmp_path / "clone"
    _git(tmp_path, "clone", "-q", "--depth", "1", f"file://{src}", str(clone))
    assert _git(clone, "rev-list", "--count", "HEAD").stdout.strip() == "1"
    assert not (clone / ".aw" / "state").exists()

    env = dict(os.environ)
    env["PYTHONPATH"] = str(PKG_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env["AW_NO_REEXEC"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "show",
            ID6,
            "--history",
            "--json",
            "--dir",
            str(clone),
        ],
        cwd=str(clone),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    [rec] = json.loads(proc.stdout)["data"]["records"]
    assert rec["status"] == "to-review"
    hist = rec["history"]
    assert len(hist) == 4
    assert [e["seq"] for e in hist] == [1, 2, 3, 4]
    assert [e["op"] for e in hist] == ["create", "transition", "set", "review"]
    assert hist[1]["from"] == "draft" and hist[1]["to"] == "to-review"
    assert hist[2]["fields"] == {"blocks_release": "next"}

    agent = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "show",
            ID6,
            "--history",
            "--agent",
            "--dir",
            str(clone),
        ],
        cwd=str(clone),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    rec_a = json.loads(agent.stdout.strip().splitlines()[-1])
    assert agent.returncode == 0 and rec_a["exit"] == 0
    assert f"{ID6}-events:4" in rec_a["evidence"]
    assert f"{ID6}-status:to-review" in rec_a["evidence"]
