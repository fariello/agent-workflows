"""Offline execution proof for moved readers (spec `4sd62s` AC-12 reader half; IPD `ffceq0` E-13 / V-13).

Spawns the real `aw` CLI in a subprocess whose `PATH` contains no host model binaries
(`opencode`, `agy`, `claude`) and whose `PYTHONPATH` injects a `sitecustomize` that disables
`socket.socket` so any network attempt raises immediately. Asserts `aw find`,
`aw attention --format json`, and `aw check all --agent` each exit 0.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict

import pytest
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.core

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HOST_BINARIES = ("opencode", "agy", "claude")


def _build_offline_fixture(tmp_path: Path) -> Path:
    repo = (tmp_path / "offline_repo").resolve()
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    (repo / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")

    wf_dir = repo / ".aw" / "system" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    (wf_dir / "index.md").write_text("# Workflows\n", encoding="utf-8")

    cfg_dir = repo / ".aw" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "project.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "preset": "private-target",
                "role": "target",
                "placements": {
                    "system": "target-tracked",
                    "config_project": "target-tracked",
                    "config_local": "target-ignored",
                    "state_durable": "target-tracked",
                    "state_runtime": "target-ignored",
                    "records": "target-tracked",
                },
                "records_backend": "repository",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    recs = repo / ".aw" / "records"
    for sub in ("plans/pending", "specs/approved", "backlog/open"):
        (recs / sub).mkdir(parents=True, exist_ok=True)

    (
        recs / "plans" / "pending" / "20261101-off-01-off001-offline-plan.ipd.md"
    ).write_text(
        RecordBuilder().plan(
            title="Offline Plan",
            when="2026-11-01",
            plan_role="child",
            scope_paths="tests/test_readers_offline.py",
            item_dependencies="none",
            status="draft",
            work_kind="chore",
            priority="low",
            set="off",
            order=1,
            highest_e_allocated="01",
            author="tester",
            review_depth="simple",
            id6="off001",
            history=["- 2026-11-01 draft (tester): created"],
            open_questions="None.",
            body="## Goal\n\nConfirm offline readers succeed without network or model hosts.\n\n## Detailed Implementation Checklist (TODO)\n\n- [ ] E-01 Execute offline reader\n  - Depends on: none\n  - Expected outcome: command exits 0\n  - Execution state: pending\n\n## Project conventions discovered (Step 0)\n\n- None.\n\n## Findings\n\n- None.\n\n## Proposed changes (ordered, validatable)\n\n1. Run offline reader.\n\n## Deferred / out of scope (with reason)\n\nNone.\n\n## Scope check\n\n- Over-scope: none.\n- Under-scope: none.\n\n## Required tests / validation\n\nRun pytest.\n\n## Spec / documentation sync\n\nN/A.\n\n## Validation and cross-check (verify before reporting done)\n\n- [ ] V-01 validates E-01\n  - Required evidence: paste pytest output\n  - Observed evidence:\n  - Result: pending\n\n## Approval and execution gate\n\n- Size assessment: standard\n- Cohesion rationale: not required",
            text_only=True,
        ),
        encoding="utf-8",
    )

    (
        recs / "specs" / "approved" / "20261101-ofs001-01-ofs001-offline-spec.spec.md"
    ).write_text(
        RecordBuilder().spec(
            title="Offline Spec",
            when="2026-11-01",
            id6="ofs001",
            status="approved",
            set="ofs001",
            order=1,
            history=["- 2026-11-01 approved (by-human): approved"],
            body="## Overview\n\nOffline spec body.",
            text_only=True,
        ),
        encoding="utf-8",
    )

    (
        recs / "backlog" / "open" / "20261101-ofb-01-ofb001-offline-item.backlog.md"
    ).write_text(
        RecordBuilder().backlog(
            id6="ofb001",
            status="open",
            set="ofb",
            priority="low",
            work_kind="chore",
            summary="Offline backlog item",
            when="2026-11-01",
            body="### Problem Statement\n\nOffline backlog body.",
            text_only=True,
        ),
        encoding="utf-8",
    )

    return repo


def _offline_env(tmp_path: Path) -> Dict[str, str]:
    # Build a stripped PATH containing only git (no opencode, agy, or claude).
    bin_dir = tmp_path / "stripped_bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    git_bin = shutil.which("git")
    assert git_bin is not None, "git executable required to build stripped PATH"
    git_link = bin_dir / Path(git_bin).name
    if not git_link.exists():
        os.symlink(git_bin, git_link)

    stripped_path = str(bin_dir)
    for host_bin in _HOST_BINARIES:
        assert shutil.which(host_bin, path=stripped_path) is None

    # Inject a sitecustomize that blocks all socket creation and marks activation.
    sc_dir = tmp_path / "offline_site"
    sc_dir.mkdir(parents=True, exist_ok=True)
    marker = tmp_path / "sitecustomize_loaded.txt"
    (sc_dir / "sitecustomize.py").write_text(
        "import pathlib, socket\n"
        f"pathlib.Path({str(marker)!r}).write_text('loaded', encoding='utf-8')\n"
        "_OrigSocket = socket.socket\n"
        "class _BlockedSocket(_OrigSocket):\n"
        "    def __new__(cls, *args, **kwargs):\n"
        "        raise RuntimeError('network disabled by offline reader test')\n"
        "    def __init__(self, *args, **kwargs):\n"
        "        raise RuntimeError('network disabled by offline reader test')\n"
        "def _blocked_conn(*args, **kwargs):\n"
        "    raise RuntimeError('network disabled by offline reader test')\n"
        "socket.socket = _BlockedSocket\n"
        "socket.create_connection = _blocked_conn\n",
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["PATH"] = stripped_path
    existing_pp = env.get("PYTHONPATH", "")
    pp_parts = [str(sc_dir), str(_REPO_ROOT)]
    if existing_pp:
        pp_parts.append(existing_pp)
    env["PYTHONPATH"] = os.pathsep.join(pp_parts)
    env["AW_NONINTERACTIVE"] = "1"
    return env


def _run_offline_aw(
    tmp_path: Path, repo: Path, *aw_args: str
) -> subprocess.CompletedProcess[str]:
    env = _offline_env(tmp_path)
    proc = subprocess.run(
        [sys.executable, "-m", "agent_workflows", *aw_args, "--dir", str(repo)],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    marker = tmp_path / "sitecustomize_loaded.txt"
    assert marker.is_file() and marker.read_text(encoding="utf-8") == "loaded"
    return proc


def test_aw_find_offline_no_host_binaries_no_network(tmp_path: Path) -> None:
    repo = _build_offline_fixture(tmp_path)
    proc = _run_offline_aw(tmp_path, repo, "find", "plans", "--agent")
    assert proc.returncode == 0, f"stderr={proc.stderr}\nstdout={proc.stdout}"
    records = [json.loads(ln) for ln in proc.stdout.splitlines() if ln.strip()]
    assert any(
        r.get("kind") == "item" and "off001" in r.get("path", "") for r in records
    )


def test_aw_attention_json_offline_no_host_binaries_no_network(tmp_path: Path) -> None:
    repo = _build_offline_fixture(tmp_path)
    proc = _run_offline_aw(tmp_path, repo, "attention", "--all", "--format", "json")
    assert proc.returncode == 0, f"stderr={proc.stderr}\nstdout={proc.stdout}"
    payload = json.loads(proc.stdout)
    assert payload["valid"] is True
    ids = {it["id"] for it in payload["items"]}
    assert {"off001", "ofs001", "ofb001"}.issubset(ids)


def test_aw_check_all_agent_offline_no_host_binaries_no_network(tmp_path: Path) -> None:
    repo = _build_offline_fixture(tmp_path)
    proc = _run_offline_aw(tmp_path, repo, "check", "all", "--agent")
    assert proc.returncode == 0, f"stderr={proc.stderr}\nstdout={proc.stdout}"
    records = [json.loads(ln) for ln in proc.stdout.splitlines() if ln.strip()]
    assert len(records) == 1
    assert records[0]["schema"] == "aw.agent/v1"
    assert records[0]["exit"] == 0
    assert records[0]["outcome"] in ("clean", "conforms")
