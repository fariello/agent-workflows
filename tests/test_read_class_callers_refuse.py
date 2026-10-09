"""Regression tests pinning that read-class repo-scoped verbs refuse a non-surveyable root

(Order 04 of dirsilent, IPD rlhmt9).

Pins:
1. Converted read-class verbs refuse exit 2 for non-surveyable --dir (subdirectory of real project)
   with human stderr naming enclosing root and literal command, and path-free cannot-run agent record.
2. Converted read-class verbs refuse exit 2 for bare invocation outside any AW project.
3. Root controls on surveyable root remain unchanged and see seeded nonzero observables.
4. Write-class verbs remain unchanged as negative controls (deliberately not given refusals).
5. Unchanged write targets for surveyable roots.
6. Pure outcome testing (no source inspection, ast, or symbol counting).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from agent_workflows import agent_schema

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def seeded_fixture(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("read_refusal_fixture")
    repo_dir = base_dir / "test_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    home_dir = base_dir / "home"
    home_dir.mkdir(parents=True, exist_ok=True)
    outside_dir = base_dir / "outside"
    outside_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["AW_NO_REEXEC"] = "1"

    # Git init
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=repo_dir,
        env=env,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        env=env,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir,
        env=env,
        check=True,
    )
    (repo_dir / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, env=env, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir,
        env=env,
        check=True,
    )

    # AW install with repository records backend
    install_cmd = [
        sys.executable,
        "-m",
        "agent_workflows",
        "install",
        ".",
        "--yes",
        "--preset",
        "local-only",
        "--delivery-mode",
        "tracked",
        "--records-backend",
        "repository",
    ]
    subprocess.run(install_cmd, cwd=repo_dir, env=env, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=repo_dir, env=env, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Install AW"], cwd=repo_dir, env=env, check=True
    )

    # Seed 1: release record
    rel_dir = repo_dir / ".aw" / "records" / "releases"
    rel_dir.mkdir(parents=True, exist_ok=True)
    (rel_dir / "20261001-01-rel001-v100.release.md").write_text(
        "# Release: v1.0.0\n\n"
        "- Id: rel001\n"
        "- Version: 1.0.0\n"
        "- Status: planned\n"
        "- Summary: First release\n\n"
        "## Summary\nFirst release.\n",
        encoding="utf-8",
    )

    # Seed 2: active research doc
    res_dir = repo_dir / ".aw" / "records" / "research"
    res_dir.mkdir(parents=True, exist_ok=True)
    (res_dir / "20261001-res001-01-res001-active-doc.research-report.md").write_text(
        "---\n"
        "id: res001\n"
        "created: 20261001\n"
        "set: res001\n"
        "order: 01\n"
        "topic: [test]\n"
        "kind: research-report\n"
        "status: active\n"
        "outcome: none-yet\n"
        "summary: Active research doc\n"
        "---\n\n"
        "# Research: Active Doc\n\n"
        "Active doc body.\n",
        encoding="utf-8",
    )

    # Seed 3: archived research doc
    arc_dir = res_dir / "archive" / "202610"
    arc_dir.mkdir(parents=True, exist_ok=True)
    (arc_dir / "20261001-arc001-01-arc001-archived-doc.research-report.md").write_text(
        "---\n"
        "id: arc001\n"
        "created: 20261001\n"
        "set: arc001\n"
        "order: 01\n"
        "topic: [test]\n"
        "kind: research-report\n"
        "status: archive\n"
        "outcome: none-yet\n"
        "summary: Archived research doc\n"
        "---\n\n"
        "# Research: Archived Doc\n\n"
        "Archived content.\n",
        encoding="utf-8",
    )

    # Seed 4: plan citing arc001 (miscategorized) and dng999 (dangling citation)
    plan_dir = repo_dir / ".aw" / "records" / "plans" / "pending"
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "20261001-plan01-01-pln001-test-plan.ipd.md").write_text(
        "# IPD: Test Plan\n\n"
        "- Id: pln001\n"
        "- Status: pending\n"
        "- Set: plan01\n"
        "- Order: 01\n\n"
        "Cites RSCH-arc001 and RSCH-dng999.\n",
        encoding="utf-8",
    )

    # Subdirectory
    sub_dir = repo_dir / "sub" / "deep"
    sub_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(["git", "add", "-A"], cwd=repo_dir, env=env, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Seed records"], cwd=repo_dir, env=env, check=True
    )

    return {
        "repo": repo_dir,
        "sub": sub_dir,
        "outside": outside_dir,
        "home": home_dir,
        "env": env,
    }


def _run(fixture, args, cwd=None):
    c = cwd or fixture["outside"]
    p = subprocess.run(
        [sys.executable, "-m", "agent_workflows"] + args,
        cwd=c,
        env=fixture["env"],
        capture_output=True,
        text=True,
    )
    return p


# --------------------------------------------------------------------------------------
# 1. Read-class verbs refusal on non-surveyable subdirectory (--dir <sub/deep>)
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cmd_prefix",
    [
        ["releases", "list"],
        ["releases", "show", "rel001"],
        ["research", "check-refs"],
    ],
)
def test_read_verbs_refuse_explicit_subdir_human_and_agent(seeded_fixture, cmd_prefix):
    sub = str(seeded_fixture["sub"])
    repo = str(seeded_fixture["repo"])
    verb_str = " ".join(cmd_prefix[:2])

    # Human surface
    res_h = _run(seeded_fixture, cmd_prefix + ["--dir", sub])
    assert res_h.returncode == 2
    assert repo in res_h.stderr
    assert f"aw {verb_str} --dir {repo}" in res_h.stderr
    assert "is not installed in it" not in res_h.stderr

    # Agent surface
    res_a = _run(seeded_fixture, cmd_prefix + ["--dir", sub, "--agent"])
    assert res_a.returncode == 2
    lines = [ln for ln in res_a.stdout.strip().splitlines() if ln.strip()]
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec.get("kind") == "error"
    assert rec.get("outcome") == "cannot-run"
    assert rec.get("exit") == 2
    assert rec.get("verified") is False
    assert agent_schema.validate_agent_record(rec) == []
    assert sub not in res_a.stdout
    assert repo not in res_a.stdout


def test_research_check_miscategorized_refuses_human_only(seeded_fixture):
    sub = str(seeded_fixture["sub"])
    repo = str(seeded_fixture["repo"])

    res = _run(seeded_fixture, ["research", "check-miscategorized", "--dir", sub])
    assert res.returncode == 2
    assert repo in res.stderr
    assert f"aw research check-miscategorized --dir {repo}" in res.stderr
    assert "is not installed in it" not in res.stderr


# --------------------------------------------------------------------------------------
# 2. Read-class verbs refusal on bare invocation outside any project (cwd=outside, no --dir)
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cmd_prefix",
    [
        ["releases", "list"],
        ["releases", "show", "rel001"],
        ["research", "check-refs"],
    ],
)
def test_read_verbs_refuse_bare_outside_project(seeded_fixture, cmd_prefix):
    res_h = _run(seeded_fixture, cmd_prefix, cwd=seeded_fixture["outside"])
    assert res_h.returncode == 2

    res_a = _run(
        seeded_fixture, cmd_prefix + ["--agent"], cwd=seeded_fixture["outside"]
    )
    assert res_a.returncode == 2
    lines = [ln for ln in res_a.stdout.strip().splitlines() if ln.strip()]
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec.get("kind") == "error"
    assert rec.get("outcome") == "cannot-run"
    assert rec.get("exit") == 2
    assert agent_schema.validate_agent_record(rec) == []


def test_check_miscategorized_bare_outside_project(seeded_fixture):
    res = _run(
        seeded_fixture,
        ["research", "check-miscategorized"],
        cwd=seeded_fixture["outside"],
    )
    assert res.returncode == 2


# --------------------------------------------------------------------------------------
# 3. Root controls on surveyable root are unchanged and nonzero
# --------------------------------------------------------------------------------------


def test_root_controls_see_seeded_observables(seeded_fixture):
    repo = str(seeded_fixture["repo"])

    # releases list
    p = _run(seeded_fixture, ["releases", "list", "--dir", repo])
    assert p.returncode == 0
    assert "rel001" in p.stdout

    # releases show
    p = _run(seeded_fixture, ["releases", "show", "rel001", "--dir", repo])
    assert p.returncode == 0
    assert "rel001" in p.stdout

    # research check-refs sees dangling citation dng999
    p = _run(seeded_fixture, ["research", "check-refs", "--dir", repo])
    assert p.returncode == 1
    assert "dng999" in p.stdout

    # research check-miscategorized sees arc001
    p = _run(seeded_fixture, ["research", "check-miscategorized", "--dir", repo])
    assert p.returncode == 1
    assert "arc001" in p.stdout


# --------------------------------------------------------------------------------------
# 4. Write-class verbs negative controls: behavior unchanged on non-surveyable --dir
# --------------------------------------------------------------------------------------


def test_releases_new_negative_control_sub(seeded_fixture):
    sub = str(seeded_fixture["sub"])
    # releases new preview must NOT refuse with root refusal; it honors --dir verbatim
    p = _run(
        seeded_fixture,
        [
            "releases",
            "new",
            "--version",
            "2.0.0",
            "--summary",
            "second release",
            "--dir",
            sub,
        ],
    )
    assert p.returncode == 0
    assert "would write" in p.stdout
    assert "no AW project found" not in p.stderr


def test_research_mutations_negative_control_sub(seeded_fixture):
    sub = str(seeded_fixture["sub"])

    # research set-assign: fails locally because target is not in sub, NOT a root refusal
    p = _run(
        seeded_fixture,
        ["research", "set-assign", "res001", "--set", "newset", "--dir", sub],
    )
    assert "no AW project found" not in p.stderr

    # research mv: fails locally, NOT a root refusal
    p = _run(
        seeded_fixture,
        ["research", "mv", "res001", "--slug", "newslug", "--dir", sub],
    )
    assert "no AW project found" not in p.stderr

    # archive: fails locally or returns no match, NOT a root refusal
    p = _run(seeded_fixture, ["archive", "res001", "--dir", sub])
    assert "no AW project found" not in p.stderr

    # research promote: exits 0 (nothing to triage), NOT a root refusal
    p = _run(seeded_fixture, ["research", "promote", "--suggest", "--dir", sub])
    assert p.returncode == 0
    assert "no AW project found" not in p.stderr


# --------------------------------------------------------------------------------------
# 5. Unchanged write targets on surveyable root
# --------------------------------------------------------------------------------------


def test_write_targets_on_surveyable_root(seeded_fixture):
    repo = str(seeded_fixture["repo"])

    # releases new targets .aw/records/releases/
    p = _run(
        seeded_fixture,
        [
            "releases",
            "new",
            "--version",
            "2.0.0",
            "--summary",
            "second release",
            "--dir",
            repo,
        ],
    )
    assert p.returncode == 0
    assert ".aw/records/releases/" in p.stdout

    # research set-assign targets .aw/records/research/
    p = _run(
        seeded_fixture,
        ["research", "set-assign", "res001", "--set", "newset", "--dir", repo],
    )
    assert p.returncode == 0
    assert "would rename" in p.stdout
    assert ".aw/records/research/" in p.stdout

    # research mv targets .aw/records/research/
    p = _run(
        seeded_fixture,
        ["research", "mv", "res001", "--slug", "newslug", "--dir", repo],
    )
    assert p.returncode == 0
    assert "would rename" in p.stdout
    assert ".aw/records/research/" in p.stdout

    # archive targets .aw/records/research/archive/
    p = _run(seeded_fixture, ["archive", "res001", "--dir", repo])
    assert p.returncode == 0
    assert "would archive" in p.stdout
    assert "202610/" in p.stdout
