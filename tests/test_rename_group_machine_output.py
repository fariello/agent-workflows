"""Outcome tests for machine output (--json and --agent) on aw rename and aw group.

IPD vfqjc0, Set eeiytw Order 02.
Pins observable outcomes, process stdout, and exit codes via subprocess calls.
No inspect, ast, regex or substring checks over production source code (P16).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

from agent_workflows import agent_schema


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )
    return tmp_path


def _extract_payload_records(stdout: str) -> List[Dict[str, Any]]:
    """Recover aw.agent/v1 records from stdout lines."""
    records = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            parsed = json.loads(line)
            if isinstance(parsed, dict) and parsed.get("schema") == "aw.agent/v1":
                records.append(parsed)
        except Exception:
            continue
    return records


# --------------------------------------------------------------------------------------
# (a) STDOUT parses, on every type, both flags, preview and apply
# --------------------------------------------------------------------------------------


def test_stdout_parses_specs_and_backlog(temp_repo: Path):
    sdir = temp_repo / ".aw/records/specs"
    sdir.mkdir(parents=True, exist_ok=True)
    sf = sdir / "20261001-abc123-01-abc123-demo.spec.md"
    sf.write_text("# Spec Demo\n\n- Id: abc123\n- Set: abc123\n- Order: 01\n")

    bdir = temp_repo / ".aw/records/backlog"
    bdir.mkdir(parents=True, exist_ok=True)
    bf = bdir / "20261001-bbb123-01-bbb123-item.backlog.md"
    bf.write_text("# Backlog Item\n\n- Id: bbb123\n- Set: bbb123\n- Order: 01\n")

    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(["git", "commit", "-m", "init", "-q"], cwd=temp_repo, check=True)

    # 1. specs rename preview --json
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "rename",
            "specs",
            "abc123",
            "--slug",
            "renamed-spec",
            "--json",
            "--dir",
            str(temp_repo),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["schema"] == "aw.agent/v1"
    assert data["status"] == "preview"

    # 2. specs rename preview --agent
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "rename",
            "specs",
            "abc123",
            "--slug",
            "renamed-spec",
            "--agent",
            "--dir",
            str(temp_repo),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    non_blank = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
    assert len(non_blank) == 1
    rec = json.loads(non_blank[0])
    assert rec["schema"] == "aw.agent/v1"
    agent_schema.assert_valid_agent_record(rec)

    # 3. specs rename apply --json
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "rename",
            "specs",
            "abc123",
            "--slug",
            "renamed-spec",
            "--apply",
            "--no-commit",
            "--json",
            "--dir",
            str(temp_repo),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["schema"] == "aw.agent/v1"
    assert data["status"] == "clean"

    # 4. backlog rename apply --agent
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "rename",
            "backlog",
            "bbb123",
            "--slug",
            "renamed-item",
            "--apply",
            "--no-commit",
            "--agent",
            "--dir",
            str(temp_repo),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    non_blank = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
    assert len(non_blank) == 1
    rec = json.loads(non_blank[0])
    assert rec["schema"] == "aw.agent/v1"
    agent_schema.assert_valid_agent_record(rec)


def test_payload_recoverable_on_plans_and_research(temp_repo: Path):
    """Plans and research paths carry a nested index refresh line until Order 03 (gzb2rq).

    Per the sequencing note in IPD vfqjc0 Deferred section, assert payload recoverability
    (extracting exactly one aw.agent/v1 record from stdout) before Order 03 silences the nested line.
    """
    pdir = temp_repo / ".aw/records/plans"
    pdir.mkdir(parents=True, exist_ok=True)
    pf = pdir / "20261001-eeiytw-01-abc123-demo.ipd.md"
    pf.write_text("# Plan Demo\n\n- Id: abc123\n- Set: eeiytw\n- Order: 01\n")

    rdir = temp_repo / ".aw/records/research"
    rdir.mkdir(parents=True, exist_ok=True)
    rf = rdir / "20261001-seta-01-r1id66-res.findings.md"
    rf.write_text("""---
id: r1id66
created: 20261001
set: seta
order: 01
topic: [test]
model: reconciliation
kind: findings
status: active
outcome: adopted
summary: test
consumed-by: []
---
# Res
""")
    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(["git", "commit", "-m", "init", "-q"], cwd=temp_repo, check=True)

    # plans rename preview --agent
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "rename",
            "plans",
            "abc123",
            "--slug",
            "renamed-demo",
            "--agent",
            "--dir",
            str(temp_repo),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    records = _extract_payload_records(res.stdout)
    assert len(records) == 1
    assert records[0]["schema"] == "aw.agent/v1"
    agent_schema.assert_valid_agent_record(records[0])

    # research mv preview --agent
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "research",
            "mv",
            "r1id66",
            "--slug",
            "renamed-res",
            "--agent",
            "--dir",
            str(temp_repo),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    records = _extract_payload_records(res.stdout)
    assert len(records) == 1
    assert records[0]["schema"] == "aw.agent/v1"
    agent_schema.assert_valid_agent_record(records[0])


# --------------------------------------------------------------------------------------
# (b) PREVIEW record matches the contract field by field
# --------------------------------------------------------------------------------------


def test_preview_record_contract(temp_repo: Path):
    sdir = temp_repo / ".aw/records/specs"
    sdir.mkdir(parents=True, exist_ok=True)
    sf = sdir / "20261001-abc123-01-abc123-demo.spec.md"
    sf.write_text("# Spec Demo\n\n- Id: abc123\n- Set: abc123\n- Order: 01\n")
    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(["git", "commit", "-m", "init", "-q"], cwd=temp_repo, check=True)

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "rename",
            "specs",
            "abc123",
            "--slug",
            "renamed-spec",
            "--agent",
            "--dir",
            str(temp_repo),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    rec = json.loads(res.stdout.strip())
    assert rec["schema"] == "aw.agent/v1"
    assert rec["kind"] == "result"
    assert rec["cmd"] == "rename specs"
    assert rec["outcome"] == "preview"
    assert rec["exit"] == 0
    assert rec["applied"] is False
    assert rec["complete"] is True
    assert rec["verified"] is True
    assert isinstance(rec["changes"], list) and len(rec["changes"]) > 0
    assert "--apply" in rec["next"]
    agent_schema.assert_valid_agent_record(rec)


# --------------------------------------------------------------------------------------
# (c) APPLIED record differs correctly & destination is discoverable
# --------------------------------------------------------------------------------------


def test_applied_record_differs_and_destination_discoverable(temp_repo: Path):
    sdir = temp_repo / ".aw/records/specs"
    sdir.mkdir(parents=True, exist_ok=True)
    sf = sdir / "20261001-abc123-01-abc123-demo.spec.md"
    sf.write_text("# Spec Demo\n\n- Id: abc123\n- Set: abc123\n- Order: 01\n")
    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(["git", "commit", "-m", "init", "-q"], cwd=temp_repo, check=True)

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "rename",
            "specs",
            "abc123",
            "--slug",
            "renamed-spec",
            "--apply",
            "--no-commit",
            "--agent",
            "--dir",
            str(temp_repo),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    rec = json.loads(res.stdout.strip())
    assert rec["applied"] is True
    assert rec["outcome"] == "clean"
    assert rec["exit"] == 0
    # Single-target rename: compact target carries the NEW repo-relative path (PR-201)
    assert (
        rec["target"]
        == ".aw/records/specs/20261001-abc123-01-abc123-renamed-spec.spec.md"
    )
    agent_schema.assert_valid_agent_record(rec)


# --------------------------------------------------------------------------------------
# (d) REFUSALS are error records, not prose
# --------------------------------------------------------------------------------------


def test_refusals_are_error_records(temp_repo: Path):
    sdir = temp_repo / ".aw/records/specs"
    sdir.mkdir(parents=True, exist_ok=True)
    sf = sdir / "20261001-abc123-01-abc123-demo.spec.md"
    sf.write_text("# Spec Demo\n\n- Id: abc123\n- Set: abc123\n- Order: 01\n")
    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(["git", "commit", "-m", "init", "-q"], cwd=temp_repo, check=True)

    # 1. Unknown id6
    res1 = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "rename",
            "specs",
            "nonexist",
            "--slug",
            "renamed",
            "--agent",
            "--dir",
            str(temp_repo),
        ],
        capture_output=True,
        text=True,
    )
    assert res1.returncode == 2
    rec1 = json.loads(res1.stdout.strip())
    assert rec1["kind"] == "error"
    assert rec1["outcome"] == "cannot-run"
    assert rec1["exit"] == 2
    assert rec1["verified"] is False
    assert rec1["complete"] is False
    assert rec1["applied"] is False
    assert rec1["findings"] > 0
    agent_schema.assert_valid_agent_record(rec1)

    # 2. Missing id6 list on group
    res2 = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "group",
            "specs",
            "--set",
            "newgrp",
            "--agent",
            "--dir",
            str(temp_repo),
        ],
        capture_output=True,
        text=True,
    )
    assert res2.returncode == 2
    rec2 = json.loads(res2.stdout.strip())
    assert rec2["kind"] == "error"
    assert rec2["outcome"] == "cannot-run"
    assert rec2["exit"] == 2
    assert rec2["verified"] is False
    assert rec2["complete"] is False
    assert rec2["applied"] is False
    agent_schema.assert_valid_agent_record(rec2)

    # 3. Over-length setid
    long_set = "this-is-a-very-long-setid-that-exceeds-the-maximum-length"
    res3 = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "group",
            "specs",
            "abc123",
            "--set",
            long_set,
            "--agent",
            "--dir",
            str(temp_repo),
        ],
        capture_output=True,
        text=True,
    )
    assert res3.returncode == 2
    rec3 = json.loads(res3.stdout.strip())
    assert rec3["kind"] == "error"
    assert rec3["outcome"] == "cannot-run"
    assert rec3["exit"] == 2
    assert rec3["verified"] is False
    assert rec3["complete"] is False
    assert rec3["applied"] is False
    agent_schema.assert_valid_agent_record(rec3)


# --------------------------------------------------------------------------------------
# (d2) Early refusals (PR-202)
# --------------------------------------------------------------------------------------


def test_early_refusals_are_records(temp_repo: Path):
    # 1. Unknown artifact type
    res1 = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "rename",
            "nosuchtype",
            "abc123",
            "--slug",
            "x",
            "--json",
            "--dir",
            str(temp_repo),
        ],
        capture_output=True,
        text=True,
    )
    assert res1.returncode == 2
    assert not res1.stdout.startswith("FAIL")
    data1 = json.loads(res1.stdout)
    assert data1["schema"] == "aw.agent/v1"
    assert data1["status"] == "cannot-run"
    assert data1["exit_code"] == 2


# --------------------------------------------------------------------------------------
# (d3) No prompt in machine mode (PR-203)
# --------------------------------------------------------------------------------------


def test_no_prompt_in_machine_mode(temp_repo: Path):
    sdir = temp_repo / ".aw/records/specs"
    sdir.mkdir(parents=True, exist_ok=True)
    sf = sdir / "20261001-abc123-01-abc123-demo.spec.md"
    sf.write_text("# Spec Demo\n\n- Id: abc123\n- Set: abc123\n- Order: 01\n")

    tdir = temp_repo / "tests"
    tdir.mkdir(parents=True, exist_ok=True)
    tf = tdir / "test_demo.py"
    tf.write_text("# Reference to 20261001-abc123-01-abc123-demo.spec.md\n")

    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init with test", "-q"], cwd=temp_repo, check=True
    )

    # Run in machine mode with stdin closed: should complete cleanly without prompting
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "rename",
            "specs",
            "abc123",
            "--slug",
            "renamed-spec",
            "--apply",
            "--no-commit",
            "--json",
            "--dir",
            str(temp_repo),
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["schema"] == "aw.agent/v1"
    assert data["status"] == "clean"


# --------------------------------------------------------------------------------------
# (e) The `all` expansion emits exactly ONE record
# --------------------------------------------------------------------------------------


def test_all_expansion_single_record(temp_repo: Path):
    pdir = temp_repo / ".aw/records/plans"
    pdir.mkdir(parents=True, exist_ok=True)
    pf = pdir / "20261001-eeiytw-01-abc123-demo.ipd.md"
    pf.write_text("# Plan Demo\n\n- Id: abc123\n- Set: eeiytw\n- Order: 01\n")
    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(["git", "commit", "-m", "init", "-q"], cwd=temp_repo, check=True)

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "rename",
            "all",
            "abc123",
            "--slug",
            "renamed-demo",
            "--agent",
            "--dir",
            str(temp_repo),
        ],
        capture_output=True,
        text=True,
    )
    # The process exits 2 because 8 types matched nothing
    assert res.returncode == 2
    records = _extract_payload_records(res.stdout)
    # MUST emit exactly ONE record, NOT nine
    assert len(records) == 1
    rec = records[0]
    assert rec["cmd"] == "rename all"
    assert rec["exit"] == 2
    assert rec["outcome"] == "cannot-run"
    agent_schema.assert_valid_agent_record(rec)


# --------------------------------------------------------------------------------------
# (f) Human surface is byte-identical
# --------------------------------------------------------------------------------------


_NESTED_PLANS_INDEX_LINE = (
    "wrote        .aw/records/plans/INDEX.json, INDEX.md (1 plans)\n"
)
_NESTED_RESEARCH_INDEX_LINE = (
    "wrote        .aw/records/research/INDEX.json, INDEX.md (1 docs)\n"
)


def test_human_stdout_byte_identical(temp_repo: Path):
    pdir = temp_repo / ".aw/records/plans"
    pdir.mkdir(parents=True, exist_ok=True)
    pf = pdir / "20261001-eeiytw-01-abc123-demo.ipd.md"
    pf.write_text("# Plan\n\n- Id: abc123\n- Set: eeiytw\n- Order: 01\n")

    sdir = temp_repo / ".aw/records/specs"
    sdir.mkdir(parents=True, exist_ok=True)
    sf1 = sdir / "20261001-abc123-01-abc123-demo.spec.md"
    sf1.write_text("# Spec\n\n- Id: abc123\n- Set: abc123\n- Order: 01\n")
    sf2 = sdir / "20261001-s2id66-01-s2id66-second.spec.md"
    sf2.write_text("# Spec 2\n\n- Id: s2id66\n- Set: s2id66\n- Order: 01\n")

    rdir = temp_repo / ".aw/records/research"
    rdir.mkdir(parents=True, exist_ok=True)
    rf = rdir / "20261001-seta-01-r1id66-res.findings.md"
    rf.write_text("""---
id: r1id66
created: 20261001
set: seta
order: 01
topic: [slash-commands]
model: reconciliation
kind: findings
status: active
outcome: adopted
summary: test
consumed-by: []
---
# Res
""")

    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(["git", "commit", "-m", "init all", "-q"], cwd=temp_repo, check=True)

    # 1. rename plans preview
    cmd1 = [
        sys.executable,
        "-m",
        "agent_workflows.cli",
        "rename",
        "plans",
        "abc123",
        "--slug",
        "renamed-demo",
        "--dir",
        str(temp_repo),
    ]
    p1 = subprocess.run(cmd1, capture_output=True, text=True, check=True)
    expected1 = "--- would rename 20261001-eeiytw-01-abc123-demo.ipd.md -> 20261001-eeiytw-01-abc123-renamed-demo.ipd.md ---\n"
    assert p1.stdout == expected1

    # 2. rename plans apply
    cmd2 = [
        sys.executable,
        "-m",
        "agent_workflows.cli",
        "rename",
        "plans",
        "abc123",
        "--slug",
        "renamed-demo",
        "--apply",
        "--no-commit",
        "--dir",
        str(temp_repo),
    ]
    p2 = subprocess.run(cmd2, capture_output=True, text=True, check=True)
    expected2 = (
        "renamed .aw/records/plans/20261001-eeiytw-01-abc123-demo.ipd.md -> .aw/records/plans/20261001-eeiytw-01-abc123-renamed-demo.ipd.md\n"
        + _NESTED_PLANS_INDEX_LINE
    )
    assert p2.stdout == expected2

    # 3. group plans apply
    cmd3 = [
        sys.executable,
        "-m",
        "agent_workflows.cli",
        "group",
        "plans",
        "abc123",
        "--set",
        "newgrp",
        "--apply",
        "--no-commit",
        "--dir",
        str(temp_repo),
    ]
    p3 = subprocess.run(cmd3, capture_output=True, text=True, check=True)
    expected3 = _NESTED_PLANS_INDEX_LINE
    assert p3.stdout == expected3

    # 4. rename specs apply
    cmd4 = [
        sys.executable,
        "-m",
        "agent_workflows.cli",
        "rename",
        "specs",
        "abc123",
        "--slug",
        "renamed-spec",
        "--apply",
        "--no-commit",
        "--dir",
        str(temp_repo),
    ]
    p4 = subprocess.run(cmd4, capture_output=True, text=True, check=True)
    expected4 = "renamed .aw/records/specs/20261001-abc123-01-abc123-demo.spec.md -> .aw/records/specs/20261001-abc123-01-abc123-renamed-spec.spec.md\n"
    assert p4.stdout == expected4

    # 5. group specs --rename apply
    cmd5 = [
        sys.executable,
        "-m",
        "agent_workflows.cli",
        "group",
        "specs",
        "s2id66",
        "--set",
        "specgrp",
        "--rename",
        "--apply",
        "--no-commit",
        "--dir",
        str(temp_repo),
    ]
    p5 = subprocess.run(cmd5, capture_output=True, text=True, check=True)
    expected5 = (
        "renamed .aw/records/specs/20261001-s2id66-01-s2id66-second.spec.md -> .aw/records/specs/20261001-specgrp-01-s2id66-second.spec.md\n"
        "set metadata Set: specgrp in .aw/records/specs/20261001-specgrp-01-s2id66-second.spec.md\n"
    )
    assert p5.stdout == expected5

    # 6. research mv apply
    cmd6 = [
        sys.executable,
        "-m",
        "agent_workflows.cli",
        "research",
        "mv",
        "r1id66",
        "--slug",
        "renamed-res",
        "--apply",
        "--no-commit",
        "--dir",
        str(temp_repo),
    ]
    p6 = subprocess.run(cmd6, capture_output=True, text=True, check=True)
    expected6 = (
        "renamed .aw/records/research/20261001-seta-01-r1id66-res.findings.md -> .aw/records/research/20261001-seta-01-r1id66-renamed-res.findings.md\n"
        "set metadata set/order/kind in .aw/records/research/20261001-seta-01-r1id66-renamed-res.findings.md\n"
        + _NESTED_RESEARCH_INDEX_LINE
    )
    assert p6.stdout == expected6


# --------------------------------------------------------------------------------------
# (h) No absolute path leaks
# --------------------------------------------------------------------------------------


def test_no_absolute_path_leaks(temp_repo: Path):
    sdir = temp_repo / ".aw/records/specs"
    sdir.mkdir(parents=True, exist_ok=True)
    sf = sdir / "20261001-abc123-01-abc123-demo.spec.md"
    sf.write_text("# Spec Demo\n\n- Id: abc123\n- Set: abc123\n- Order: 01\n")
    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(["git", "commit", "-m", "init", "-q"], cwd=temp_repo, check=True)

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "rename",
            "specs",
            "abc123",
            "--slug",
            "renamed-spec",
            "--json",
            "--dir",
            str(temp_repo),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    # The absolute path of temp_repo must NOT appear anywhere in the output
    assert str(temp_repo) not in res.stdout
