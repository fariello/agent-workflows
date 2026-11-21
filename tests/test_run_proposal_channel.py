# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for agent proposal channel and coordinator landing (fixfirst-02 tha7a6 E-01..E-05).

Guards that:
1. Valid 'material' proposals file an open backlog item on main, stop the item as fail-gate
   with awaiting-human-decision refusal and needs_input set, and surface in run summary.
2. Valid 'small' proposals file a draft plan in a dedicated Set on main with draft status and
   inherited release gates.
3. Malformed proposals file no record and allow the turn to be handled normally.
4. Injected front-matter lines (e.g. '- Status: approved') in proposal text are sanitized
   and never alter the filed record's metadata.
5. Coordinator performer retries on raced main tip and succeeds.
6. A held integration lock times out safely, leaving main untouched and preserving the record
   in the run directory.
7. Three-item continuation: Item A proposes -> fail-gate + needs_input, Item C cascades
   dependency-blocked, Item B executes, run exits 3, lane branch kept, and proposal on main.
Drives real runner on both OpenCode (oc) and Antigravity (agy) hosts.
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from agent_workflows import agy_runipd, oc_runipd, render_stream, runner_shared
from tests.support import coordinator_role


def _create_test_repo(root: Path) -> Path:
    """Initialize a git repo with required .aw structure and commit."""
    repo = root / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-b", "main", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True)

    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/runs/\n", encoding="utf-8"
    )
    (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")

    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "backlog" / "open").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "releases").mkdir(parents=True, exist_ok=True)
    (
        repo
        / ".aw"
        / "records"
        / "releases"
        / "20261009-rel001-01-rel001-v1.release.md"
    ).write_text(
        "# Release: 1.0.0\n\n- Id: rel001\n- Version: 1.0.0\n- Status: planned\n- Set: rel001 (1.0.0)\n- Order: 01\n",
        encoding="utf-8",
    )
    (repo / ".aw" / "records" / "plans" / "pending" / ".gitkeep").write_text(
        "", encoding="utf-8"
    )
    (repo / ".aw" / "records" / "backlog" / "open" / ".gitkeep").write_text(
        "", encoding="utf-8"
    )

    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "initial repo commit"], cwd=repo, check=True
    )
    return repo


def _create_plan_file(
    repo: Path,
    id6: str,
    *,
    setid: str = "testset",
    order: int = 1,
    status: str = "approved",
    priority: str = "medium",
    work_kind: str = "bug",
    blocks_release: str | None = None,
    dependencies: list[str] | None = None,
) -> Path:
    """Create a conforming plan file under .aw/records/plans/pending/."""
    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plans_dir / f"20261009-{setid}-{order:02d}-{id6}-plan.ipd.md"

    content = f"""# IPD: Test Plan {id6}

- Kind: child
- Status: {status}
- Set: {setid}
- Order: {order}
- Id: {id6}
- Priority: {priority}
- Work-Kind: {work_kind}
"""
    if blocks_release:
        content += f"- Blocks-Release: {blocks_release}\n"
    if dependencies:
        dep_str = ", ".join(dependencies)
        content += f"- Item-Dependencies: {dep_str}\n"
    content += """- Scope-Paths: README.md

## Detailed Implementation Checklist (TODO)
- [ ] E-01 Do work
- [ ] V-01 Verify work
"""
    plan_path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", str(plan_path)], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", f"add plan {id6}"], cwd=repo, check=True)
    return plan_path


def _make_fake_agent_script(tmp_path: Path) -> Path:
    """Create a fake agent script that can serve as both opencode and agy."""
    from tests import support

    return support.make_fake_executable(
        tmp_path / "fake_agent",
        """#!/usr/bin/env python3
import json, os, re, sys
from pathlib import Path

# Print standard stream lines
print(json.dumps({"event": "init", "conversation_id": "ses-1", "init": {"model": "test-model"}}), flush=True)
print(json.dumps({"type": "text", "sessionID": "ses-1", "part": {"text": "working"}}), flush=True)

all_text = ""
for arg in sys.argv[1:]:
    if "Required JSON outcome:" in arg:
        all_text = arg
        break
    if Path(arg).is_file():
        try:
            content = Path(arg).read_text(encoding="utf-8")
            if "Required JSON outcome:" in content:
                all_text = content
                break
        except Exception:
            pass

payload_file = os.environ.get("FAKE_PAYLOAD_FILE")
payload_json = os.environ.get("FAKE_PAYLOAD_JSON")

if payload_file and Path(payload_file).is_file():
    payload_content = Path(payload_file).read_text(encoding="utf-8")
elif payload_json:
    payload_content = payload_json
else:
    payload_content = json.dumps({"disposition": "executed", "defect_report": {"state": "none-found", "findings": []}, "pushed": False})

if all_text:
    m = re.search(r"Required JSON outcome: (\\S+)", all_text)
    if m:
        p = Path(m.group(1))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(payload_content, encoding="utf-8")

    m_pos = re.search(r"Queue position: (\\d+)", all_text)
    m_id6 = re.search(r"Assigned IPD: (\\w+)", all_text)
    m_rd = re.search(r"(?:Run directory|Run root): (\\S+)", all_text)
    if m_pos and m_id6 and m_rd:
        pos = int(m_pos.group(1))
        id6 = m_id6.group(1)
        rd = Path(m_rd.group(1))
        out_dir = rd / "outcomes"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{pos:02d}-{id6}.json").write_text(payload_content, encoding="utf-8")

    # If disposition is executed, also move pending plan to executed so bucket matches
    try:
        data = json.loads(payload_content)
        if data.get("disposition") == "executed" and m_id6:
            id6 = m_id6.group(1)
            m_plan = re.search(r"Plan file at launch: (\\S+)", all_text)
            if m_plan:
                pf = Path(m_plan.group(1))
                if pf.is_file() and "pending" in pf.parts:
                    exec_dir = pf.parent.parent / "executed"
                    exec_dir.mkdir(parents=True, exist_ok=True)
                    pf.rename(exec_dir / pf.name)
    except Exception:
        pass

sys.exit(0)
""",
    )


class TestProposalValidator(unittest.TestCase):
    """E-01: Unit tests for pure proposal validation and front-matter sanitization."""

    def test_absent_proposal(self) -> None:
        v1 = runner_shared.validate_proposal(None)
        self.assertTrue(v1.is_absent)
        self.assertFalse(v1.is_valid)
        self.assertFalse(v1.is_malformed)

        v2 = runner_shared.validate_proposal({})
        self.assertTrue(v2.is_absent)

        v3 = runner_shared.validate_proposal({"proposal": None})
        self.assertTrue(v3.is_absent)

    def test_valid_proposal(self) -> None:
        data = {
            "proposal": {
                "kind": "tool-defect",
                "blocked_by": "aw tool crashed with exit code 2",
                "why": "tool needs new subparser for custom flags",
                "proposed_change": "add subparser support in cli.py",
                "paths": ["agent_workflows/cli.py"],
                "size": "material",
            }
        }
        v = runner_shared.validate_proposal(data)
        self.assertTrue(v.is_valid)
        self.assertFalse(v.is_malformed)
        self.assertFalse(v.is_absent)
        self.assertEqual(len(v.violations), 0)
        self.assertIsNotNone(v.sanitized_proposal)
        self.assertEqual(v.sanitized_proposal["size"], "material")

    def test_malformed_missing_key(self) -> None:
        data = {
            "proposal": {
                "kind": "gate-change",
                # missing blocked_by
                "why": "gate is too strict",
                "proposed_change": "relax gate regex",
                "paths": ["agent_workflows/runner_shared.py"],
                "size": "small",
            }
        }
        v = runner_shared.validate_proposal(data)
        self.assertTrue(v.is_malformed)
        self.assertFalse(v.is_valid)
        self.assertTrue(any("blocked_by" in s for s in v.violations))

    def test_malformed_bad_enum(self) -> None:
        data = {
            "proposal": {
                "kind": "not-a-valid-kind",
                "blocked_by": "something failed",
                "why": "cannot fix",
                "proposed_change": "change something",
                "paths": ["file.py"],
                "size": "huge",  # bad size
            }
        }
        v = runner_shared.validate_proposal(data)
        self.assertTrue(v.is_malformed)
        self.assertTrue(any("kind" in s for s in v.violations))
        self.assertTrue(any("size" in s for s in v.violations))

    def test_malformed_over_length(self) -> None:
        long_blocked = "x" * 600
        data = {
            "proposal": {
                "kind": "tool-defect",
                "blocked_by": long_blocked,
                "why": "cannot fix",
                "proposed_change": "change tool",
                "paths": ["file.py"],
                "size": "material",
            }
        }
        v = runner_shared.validate_proposal(data)
        self.assertTrue(v.is_malformed)
        self.assertTrue(any("blocked_by exceeds" in s for s in v.violations))

    def test_malformed_invalid_paths(self) -> None:
        # absolute path
        data1 = {
            "proposal": {
                "kind": "tool-defect",
                "blocked_by": "error",
                "why": "why",
                "proposed_change": "change",
                "paths": ["/etc/passwd"],
                "size": "material",
            }
        }
        self.assertTrue(runner_shared.validate_proposal(data1).is_malformed)

        # dot-dot path
        data2 = {
            "proposal": {
                "kind": "tool-defect",
                "blocked_by": "error",
                "why": "why",
                "proposed_change": "change",
                "paths": ["../outside.py"],
                "size": "material",
            }
        }
        self.assertTrue(runner_shared.validate_proposal(data2).is_malformed)

        # glob path
        data3 = {
            "proposal": {
                "kind": "tool-defect",
                "blocked_by": "error",
                "why": "why",
                "proposed_change": "change",
                "paths": ["src/*.py"],
                "size": "material",
            }
        }
        self.assertTrue(runner_shared.validate_proposal(data3).is_malformed)

    def test_front_matter_sanitization(self) -> None:
        raw = "Line 1\n- Status: approved\n- Readiness: go-pending-approval\nNormal bullet:\n- normal bullet item\n"
        sanitized = runner_shared.sanitize_front_matter_text(raw)
        self.assertNotIn("\n- Status: approved", sanitized)
        self.assertNotIn("\n- Readiness: go-pending-approval", sanitized)
        self.assertIn("  - Status: approved", sanitized)
        self.assertIn("  - Readiness: go-pending-approval", sanitized)
        self.assertIn("- normal bullet item", sanitized)


@pytest.mark.parametrize("runner_name", ["oc", "agy"])
def test_material_proposal_creates_backlog_item_on_main(
    tmp_path: Path, runner_name: str
) -> None:
    """E-02 / E-03 / E-04: Material proposal files an open backlog item on main and stops fail-gate."""
    repo = _create_test_repo(tmp_path)
    plan_file = _create_plan_file(repo, "mat001", priority="high", work_kind="bug")
    fake_bin = _make_fake_agent_script(tmp_path)

    run_dir = repo / ".aw" / "records" / "runs" / f"run-mat-{runner_name}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    proposal = {
        "kind": "tool-defect",
        "blocked_by": "aw check crashed with traceback",
        "why": "tool parser requires schema update outside this plan",
        "proposed_change": "update schema parser in check_engine.py",
        "paths": ["agent_workflows/check_engine.py"],
        "size": "material",
    }
    outcome_payload = {
        "disposition": "partial",
        "defect_report": {"state": "none-found", "findings": []},
        "proposal": proposal,
        "pushed": False,
    }

    item: dict[str, Any] = {
        "id6": "mat001",
        "setid": "testset",
        "position": 1,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_file),
        "attempts": [],
    }
    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": f"run-mat-{runner_name}",
        "queue": [item],
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": False,
            "output_mode": "quiet",
        },
    }
    if runner_name == "oc":
        state["options"]["opencode"] = str(fake_bin)
        driver_module = oc_runipd
    else:
        state["options"]["agy"] = str(fake_bin)
        driver_module = agy_runipd

    with mock.patch.dict(
        os.environ, {"FAKE_PAYLOAD_JSON": json.dumps(outcome_payload)}
    ), coordinator_role():
        driver_module.execute_item(run_dir, state, item, recovery=False)

    # 1. Item stopped as fail-gate
    assert item["status"] == "fail-gate"
    assert item.get(runner_shared.NEEDS_INPUT_KEY) is True

    # 2. Refusal is awaiting-human-decision
    refusal = item.get("refusal") or {}
    assert refusal.get("code") == render_stream.GATE_ANSWER_NEEDS_HUMAN_CODE
    assert "tool-defect" in refusal.get("reason", "")
    assert "mat001" in refusal.get("remedy", "")
    assert "inspect proposal" in refusal.get("remedy", "")

    # 3. Exactly one backlog record landed on main
    bl_dir = repo / ".aw" / "records" / "backlog" / "open"
    bl_files = list(bl_dir.glob("*.backlog.md"))
    assert len(bl_files) == 1, f"Expected 1 backlog file on main, got {bl_files}"
    bl_content = bl_files[0].read_text(encoding="utf-8")
    assert "- Status: open" in bl_content
    assert "- Priority: high" in bl_content
    assert "aw check crashed with traceback" in bl_content

    # 4. Summary table renders proposal first
    summary = render_stream.render_run_summary_table(state, run_dir)
    assert "AWAITING HUMAN DECISION (fail-gate)" in summary
    assert "proposal:" in summary
    assert "blocked by: aw check crashed with traceback" in summary
    assert "view: aw show" in summary


@pytest.mark.parametrize("runner_name", ["oc", "agy"])
def test_small_proposal_creates_draft_plan_on_main(
    tmp_path: Path, runner_name: str
) -> None:
    """E-02 / E-03: Small proposal files a draft plan in a dedicated Set on main."""
    repo = _create_test_repo(tmp_path)
    plan_file = _create_plan_file(
        repo, "sml001", priority="medium", work_kind="bug", blocks_release="rel-123"
    )
    fake_bin = _make_fake_agent_script(tmp_path)

    run_dir = repo / ".aw" / "records" / "runs" / f"run-sml-{runner_name}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    proposal = {
        "kind": "gate-change",
        "blocked_by": "regex failed on trailing newline",
        "why": "small adjustment to gate pattern with no behavior change",
        "proposed_change": "strip trailing newline before regex match",
        "paths": ["agent_workflows/runner_shared.py"],
        "size": "small",
    }
    outcome_payload = {
        "disposition": "partial",
        "defect_report": {"state": "none-found", "findings": []},
        "proposal": proposal,
        "pushed": False,
    }

    item: dict[str, Any] = {
        "id6": "sml001",
        "setid": "testset",
        "position": 1,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_file),
        "attempts": [],
    }
    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": f"run-sml-{runner_name}",
        "queue": [item],
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": False,
            "output_mode": "quiet",
        },
    }
    if runner_name == "oc":
        state["options"]["opencode"] = str(fake_bin)
        driver_module = oc_runipd
    else:
        state["options"]["agy"] = str(fake_bin)
        driver_module = agy_runipd

    with mock.patch.dict(
        os.environ, {"FAKE_PAYLOAD_JSON": json.dumps(outcome_payload)}
    ), coordinator_role():
        driver_module.execute_item(run_dir, state, item, recovery=False)

    # 1. Item stopped as fail-gate
    assert item["status"] == "fail-gate"
    assert item.get(runner_shared.NEEDS_INPUT_KEY) is True

    # 2. Plan file created in pending with Set prop-sml001 and draft status
    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
    matching = list(plans_dir.glob("*-prop-sml001-01-*.ipd.md"))
    assert len(matching) == 1, f"Expected 1 draft plan, found {matching}"
    plan_text = matching[0].read_text(encoding="utf-8")
    assert "- Status: draft" in plan_text
    assert "- Set: prop-sml001" in plan_text
    assert "- Blocks-Release: rel-123" in plan_text
    assert "regex failed on trailing newline" in plan_text


@pytest.mark.parametrize("runner_name", ["oc", "agy"])
def test_malformed_proposal_handled_normally(tmp_path: Path, runner_name: str) -> None:
    """E-01 / E-05: Malformed proposal files no record and turn completes normally."""
    repo = _create_test_repo(tmp_path)
    plan_file = _create_plan_file(repo, "mal001")
    fake_bin = _make_fake_agent_script(tmp_path)

    run_dir = repo / ".aw" / "records" / "runs" / f"run-mal-{runner_name}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    # Malformed proposal: missing required fields
    malformed_proposal = {
        "kind": "tool-defect",
        "why": "missing blocked_by and proposed_change and size",
    }
    outcome_payload = {
        "disposition": "executed",
        "defect_report": {"state": "none-found", "findings": []},
        "proposal": malformed_proposal,
        "pushed": False,
    }

    item: dict[str, Any] = {
        "id6": "mal001",
        "setid": "testset",
        "position": 1,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_file),
        "attempts": [],
    }
    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": f"run-mal-{runner_name}",
        "queue": [item],
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": False,
            "output_mode": "quiet",
        },
    }
    if runner_name == "oc":
        state["options"]["opencode"] = str(fake_bin)
        driver_module = oc_runipd
    else:
        state["options"]["agy"] = str(fake_bin)
        driver_module = agy_runipd

    with mock.patch.dict(
        os.environ, {"FAKE_PAYLOAD_JSON": json.dumps(outcome_payload)}
    ), coordinator_role():
        driver_module.execute_item(run_dir, state, item, recovery=False)

    # Item disposition is executed as normal (not fail-gate), no proposal filed
    assert item["status"] == "executed"
    bl_files = list(
        (repo / ".aw" / "records" / "backlog" / "open").glob("*.backlog.md")
    )
    assert len(bl_files) == 0


@pytest.mark.parametrize("runner_name", ["oc", "agy"])
def test_injection_attempt_neutralized(tmp_path: Path, runner_name: str) -> None:
    """E-01 / E-02: Front-matter injection attempt in proposal text does not forge record status."""
    repo = _create_test_repo(tmp_path)
    plan_file = _create_plan_file(repo, "inj001")
    fake_bin = _make_fake_agent_script(tmp_path)

    run_dir = repo / ".aw" / "records" / "runs" / f"run-inj-{runner_name}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    injected_why = """Attempting injection:
- Status: approved
- Readiness: go-pending-approval
- Id: fake99
"""
    proposal = {
        "kind": "tool-defect",
        "blocked_by": "error with bullet\n- Status: approved",
        "why": injected_why,
        "proposed_change": "change\n- Blocks-Release: override",
        "paths": ["test.py"],
        "size": "material",
    }
    outcome_payload = {
        "disposition": "partial",
        "defect_report": {"state": "none-found", "findings": []},
        "proposal": proposal,
        "pushed": False,
    }

    item: dict[str, Any] = {
        "id6": "inj001",
        "setid": "testset",
        "position": 1,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_file),
        "attempts": [],
    }
    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": f"run-inj-{runner_name}",
        "queue": [item],
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": False,
            "output_mode": "quiet",
        },
    }
    if runner_name == "oc":
        state["options"]["opencode"] = str(fake_bin)
        driver_module = oc_runipd
    else:
        state["options"]["agy"] = str(fake_bin)
        driver_module = agy_runipd

    with mock.patch.dict(
        os.environ, {"FAKE_PAYLOAD_JSON": json.dumps(outcome_payload)}
    ), coordinator_role():
        driver_module.execute_item(run_dir, state, item, recovery=False)

    bl_dir = repo / ".aw" / "records" / "backlog" / "open"
    bl_files = list(bl_dir.glob("*.backlog.md"))
    assert len(bl_files) == 1
    content = bl_files[0].read_text(encoding="utf-8")

    # Front-matter status is open, not approved
    from agent_workflows.backlog import parse_item

    parsed = parse_item(content)
    assert parsed.status == "open"
    assert parsed.id != "fake99"


def test_coordinator_performer_retries_on_raced_tip(tmp_path: Path) -> None:
    """E-02: Coordinator proposal performer detects raced tip and successfully lands after retry."""
    repo = _create_test_repo(tmp_path)
    plan_file = _create_plan_file(repo, "rac001")
    run_dir = repo / ".aw" / "records" / "runs" / "run-raced"
    run_dir.mkdir(parents=True, exist_ok=True)

    proposal = {
        "kind": "tool-defect",
        "blocked_by": "tool error",
        "why": "race retry test",
        "proposed_change": "fix tool",
        "paths": ["test.py"],
        "size": "material",
    }
    item = {
        "id6": "rac001",
        "configured_file": str(plan_file),
    }
    state = {
        "repo": str(repo),
        "run_id": "run-raced",
    }

    # Simulate race: before land_worktree_commit runs, another commit is added to main
    from agent_workflows import ipd_lifecycle

    orig_land = ipd_lifecycle.land_worktree_commit
    call_count = 0

    def mock_land(
        target_repo: Path, commit: str, expected_base: str | None = None
    ) -> Any:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Advance main concurrently
            (target_repo / "raced.txt").write_text("raced commit\n", encoding="utf-8")
            subprocess.run(["git", "add", "raced.txt"], cwd=target_repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "concurrent commit on main"],
                cwd=target_repo,
                check=True,
            )
            return ipd_lifecycle.ReconcileLanding(
                status=ipd_lifecycle.RECONCILED_RACED,
                returncode=128,
                detail="main advanced concurrently",
            )
        return orig_land(target_repo, commit, expected_base=expected_base)

    with mock.patch(
        "agent_workflows.ipd_lifecycle.land_worktree_commit", side_effect=mock_land
    ), coordinator_role():
        res = runner_shared.perform_coordinator_proposal_file(
            run_dir=run_dir,
            state=state,
            item=item,
            proposal=proposal,
        )

    assert res.filed is True
    assert call_count == 2
    bl_files = list(
        (repo / ".aw" / "records" / "backlog" / "open").glob("*.backlog.md")
    )
    assert len(bl_files) == 1


def test_coordinator_performer_held_integration_lock(tmp_path: Path) -> None:
    """E-02: Held integration lock timeout leaves main untouched and stores record in run_dir."""
    repo = _create_test_repo(tmp_path)
    plan_file = _create_plan_file(repo, "lck001")
    run_dir = repo / ".aw" / "records" / "runs" / "run-locked"
    run_dir.mkdir(parents=True, exist_ok=True)

    proposal = {
        "kind": "tool-defect",
        "blocked_by": "lock error",
        "why": "lock timeout test",
        "proposed_change": "fix tool",
        "paths": ["test.py"],
        "size": "material",
    }
    item = {
        "id6": "lck001",
        "configured_file": str(plan_file),
    }
    state = {
        "repo": str(repo),
        "run_id": "run-locked",
    }

    head_before = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Acquire lock with a mock or zero timeout holder
    @contextlib.contextmanager
    def fake_lock(*a, **k):
        yield runner_shared.IntegrationLockOutcome(
            acquired=False,
            handle=None,
            waited_seconds=5.0,
            holder="peer-agent",
            detail="the repository integration lock is held; waited 5s and gave up",
        )

    with mock.patch(
        "agent_workflows.runner_shared.integration_lock", side_effect=fake_lock
    ), coordinator_role():
        res = runner_shared.perform_coordinator_proposal_file(
            run_dir=run_dir,
            state=state,
            item=item,
            proposal=proposal,
            timeout=0.01,
        )

    assert res.filed is False
    assert "lock" in (res.reason or "").lower()

    # Main untouched
    head_after = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert head_before == head_after
    assert (
        len(list((repo / ".aw" / "records" / "backlog" / "open").glob("*.backlog.md")))
        == 0
    )

    # Saved under run_dir/proposals
    saved_proposals = list((run_dir / "proposals").glob("*proposal.backlog.md"))
    assert len(saved_proposals) == 1
    assert "lock timeout test" in saved_proposals[0].read_text(encoding="utf-8")


@pytest.mark.parametrize("runner_name", ["oc", "agy"])
def test_three_item_continuation_e03(tmp_path: Path, runner_name: str) -> None:
    """E-03 / E-05: Three-item run: A proposes -> fail-gate, C cascades dependency-blocked, B executes, run exits 3."""
    repo = _create_test_repo(tmp_path)

    # Item A: proposes
    plan_a = _create_plan_file(
        repo, "aaa001", setid="s1", order=1, priority="medium", work_kind="bug"
    )
    # Item B: independent, succeeds
    plan_b = _create_plan_file(
        repo, "bbb002", setid="s1", order=2, priority="medium", work_kind="bug"
    )
    # Item C: depends on A
    plan_c = _create_plan_file(
        repo,
        "ccc003",
        setid="s1",
        order=3,
        dependencies=["executed:aaa001"],
        priority="medium",
        work_kind="bug",
    )

    fake_bin = _make_fake_agent_script(tmp_path)

    run_dir = repo / ".aw" / "records" / "runs" / f"run-3item-{runner_name}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    proposal_a = {
        "kind": "tool-defect",
        "blocked_by": "compiler bug in tool",
        "why": "tool needs patch",
        "proposed_change": "patch compiler",
        "paths": ["tools/compiler.py"],
        "size": "material",
    }
    outcome_a = {
        "disposition": "partial",
        "defect_report": {"state": "none-found", "findings": []},
        "proposal": proposal_a,
        "pushed": False,
    }
    outcome_b = {
        "disposition": "executed",
        "defect_report": {"state": "none-found", "findings": []},
        "pushed": False,
    }

    # Queue with A, B, C
    item_a = {
        "id6": "aaa001",
        "setid": "s1",
        "position": 1,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_a),
        "attempts": [],
    }
    item_b = {
        "id6": "bbb002",
        "setid": "s1",
        "position": 2,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_b),
        "attempts": [],
    }
    item_c = {
        "id6": "ccc003",
        "setid": "s1",
        "position": 3,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_c),
        "dependencies": ["executed:aaa001"],
        "attempts": [],
    }

    state = {
        "repo": str(repo),
        "run_id": f"run-3item-{runner_name}",
        "queue": [item_a, item_b, item_c],
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": False,
            "output_mode": "quiet",
        },
    }

    if runner_name == "oc":
        state["options"]["opencode"] = str(fake_bin)
        driver_module = oc_runipd
    else:
        state["options"]["agy"] = str(fake_bin)
        driver_module = agy_runipd

    runner_shared.save_state(run_dir, state)

    # Script fake responses per item
    def side_effect_executor(
        state_arg: Any,
        rd_arg: Any,
        it_arg: Any,
        *args: Any,
        **kwargs: Any,
    ) -> tuple[int, str | None, Path, list[str]]:
        current_id6 = it_arg["id6"]
        out_file = rd_arg / f"outcomes/{it_arg['position']:02d}-{current_id6}.json"
        if current_id6 == "aaa001":
            out_file.write_text(json.dumps(outcome_a), encoding="utf-8")
        elif current_id6 == "bbb002":
            out_file.write_text(json.dumps(outcome_b), encoding="utf-8")
            exec_dir = repo / ".aw" / "records" / "plans" / "executed"
            exec_dir.mkdir(parents=True, exist_ok=True)
            if plan_b.exists():
                plan_b.rename(exec_dir / plan_b.name)
        log_f = rd_arg / f"logs/{current_id6}.log"
        log_f.parent.mkdir(parents=True, exist_ok=True)
        log_f.write_text("dummy log\n", encoding="utf-8")
        return (0, "ses-1", log_f, [])

    with mock.patch.object(
        driver_module,
        "run_opencode" if runner_name == "oc" else "run_agy_turn",
        side_effect=side_effect_executor,
    ), coordinator_role():
        rc = driver_module.run_queue(run_dir, state)

    final_state = runner_shared.load_state(run_dir)
    by_id = {it["id6"]: it for it in final_state["queue"]}

    # Item A: fail-gate with awaiting-human-decision refusal
    assert by_id["aaa001"]["status"] == "fail-gate"
    ref_a = by_id["aaa001"].get("refusal") or {}
    assert ref_a.get("code") == render_stream.GATE_ANSWER_NEEDS_HUMAN_CODE

    # Item C: dependency-blocked / fail-depend
    assert by_id["ccc003"]["status"] in ("dependency-blocked", "fail-depend")
    assert len(by_id["ccc003"]["attempts"]) == 0

    # Item B: executed
    assert by_id["bbb002"]["status"] == "executed"

    # Run exits 3 (needs input)
    assert rc == 3

    # Proposal present on main
    bl_files = list(
        (repo / ".aw" / "records" / "backlog" / "open").glob("*.backlog.md")
    )
    assert len(bl_files) == 1
    assert "compiler bug in tool" in bl_files[0].read_text(encoding="utf-8")


@pytest.mark.parametrize("runner_name", ["oc", "agy"])
def test_needs_attended_proposal_marks_plan_and_files_no_stub(
    tmp_path: Path, runner_name: str
) -> None:
    """A `needs-attended` proposal marks the proposing plan `Attended: required` on main and files
    no new plan or backlog item (regression: `lkn1zt` -> scaffold stub `ee3htj`)."""
    repo = _create_test_repo(tmp_path)
    plan_file = _create_plan_file(repo, "att001")
    fake_bin = _make_fake_agent_script(tmp_path)

    run_dir = repo / ".aw" / "records" / "runs" / f"run-att-{runner_name}"
    for sub in ("outcomes", "prompts"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)

    outcome_payload = {
        "disposition": "blocked",
        "defect_report": {"state": "none-found", "findings": []},
        "proposal": {
            "kind": "needs-attended",
            "blocked_by": "plan says: needs a human answering live prompts",
            "why": "an unattended turn cannot answer the maintainer's questions",
            "proposed_change": "run it in an attended session",
            "paths": [str(plan_file.relative_to(repo))],
            "size": "small",
        },
        "pushed": False,
    }
    item: dict[str, Any] = {
        "id6": "att001",
        "setid": "testset",
        "position": 1,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_file),
        "attempts": [],
    }
    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": f"run-att-{runner_name}",
        "queue": [item],
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": False,
            "output_mode": "quiet",
        },
    }
    if runner_name == "oc":
        state["options"]["opencode"] = str(fake_bin)
        driver_module = oc_runipd
    else:
        state["options"]["agy"] = str(fake_bin)
        driver_module = agy_runipd

    with mock.patch.dict(
        os.environ, {"FAKE_PAYLOAD_JSON": json.dumps(outcome_payload)}
    ), coordinator_role():
        driver_module.execute_item(run_dir, state, item, recovery=False)

    assert item.get(runner_shared.NEEDS_INPUT_KEY) is True
    refusal = item.get("refusal") or {}
    assert refusal.get("code") == runner_shared.ATTENDED_REQUIRED_CODE
    assert "aw work begin att001" in refusal.get("remedy", "")

    # The proposing plan on main now carries the marker (committed, not just written).
    on_main = subprocess.run(
        ["git", "show", f"main:{plan_file.relative_to(repo).as_posix()}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "- Attended: required" in on_main

    # No stub plan and no backlog item were filed.
    pending = repo / ".aw" / "records" / "plans" / "pending"
    assert not list(pending.glob("*-prop-att001-*.ipd.md"))
    backlog_open = repo / ".aw" / "records" / "backlog" / "open"
    assert not list(backlog_open.glob("*.backlog.md"))


def test_attended_plan_is_held_at_queue_build(tmp_path: Path) -> None:
    """An `Attended: required` plan is frozen not-run with needs_input and spends no turn."""
    repo = _create_test_repo(tmp_path)
    plan_file = _create_plan_file(repo, "att002")
    text = plan_file.read_text(encoding="utf-8").replace(
        "- Scope-Paths: README.md\n", "- Scope-Paths: README.md\n- Attended: required\n"
    )
    plan_file.write_text(text, encoding="utf-8")

    entry: dict[str, Any] = {"id6": "att002", "action": "execute", "status": "queued"}
    assert runner_shared.hold_attended_plan(entry, plan_file) is True
    assert entry["status"] == "not-run"
    assert entry[runner_shared.NEEDS_INPUT_KEY] is True
    assert entry["refusal"]["code"] == runner_shared.ATTENDED_REQUIRED_CODE

    review: dict[str, Any] = {"id6": "att002", "action": "review", "status": "queued"}
    assert runner_shared.hold_attended_plan(review, plan_file) is False
    assert review["status"] == "queued"

    plain = _create_plan_file(repo, "att003", order=2)
    entry3: dict[str, Any] = {"id6": "att003", "action": "execute", "status": "queued"}
    assert runner_shared.hold_attended_plan(entry3, plain) is False
    assert entry3["status"] == "queued"


@pytest.mark.parametrize("runner_name", ["oc", "agy"])
def test_attended_plan_not_dispatched_at_queue_freeze(
    tmp_path: Path, runner_name: str
) -> None:
    """End to end through the driver's own queue freeze (`start --prepare-only`): the attended
    plan is frozen not-run with needs_input and the attended remedy; a plain sibling still queues."""
    from tests.test_freeze_time_refusal import _init_repo, _write_plan

    repo = _init_repo(tmp_path)
    att = _write_plan(repo, "att004", order=1)
    att.write_text(
        att.read_text(encoding="utf-8").replace(
            "- Id: att004\n", "- Id: att004\n- Attended: required\n"
        ),
        encoding="utf-8",
    )
    _write_plan(repo, "pln005", order=2)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "plans"], cwd=repo, check=True)

    module = oc_runipd if runner_name == "oc" else agy_runipd
    args = module.build_parser().parse_args(
        ["start", "att004", "pln005", "--prepare-only", "--repo", str(repo)]
    )
    run_dir = Path(module.initialize_run(args))
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    by_id = {e["id6"]: e for e in state["queue"]}
    assert by_id["att004"]["status"] == "not-run"
    assert by_id["att004"][runner_shared.NEEDS_INPUT_KEY] is True
    assert by_id["att004"]["refusal"]["code"] == runner_shared.ATTENDED_REQUIRED_CODE
    assert by_id["pln005"]["status"] == "queued"


def test_attended_field_value_is_linted() -> None:
    """`- Attended:` accepts only `required`; any other value is a metadata error, absence is silent."""
    from agent_workflows import ipd_schema

    ok = ipd_schema.validate_metadata({"Attended": "required"})
    assert not [e for e in ok if e.field == "Attended"]
    bad = ipd_schema.validate_metadata({"Attended": "maybe"})
    assert [e for e in bad if e.field == "Attended"]
    none = ipd_schema.validate_metadata({})
    assert not [e for e in none if e.field == "Attended"]


def test_stale_attempt1_proposal_ignored_when_attempt2_outcome_not_collected(
    tmp_path: Path,
) -> None:
    """When attempt 2 in an isolated lane yields no fresh outcome, a prior attempt's stale proposal is never re-filed."""
    from tests import support

    repo = _create_test_repo(tmp_path)
    p = _create_plan_file(repo, "stl001", order=1)
    run_id = "run-stale-proposal"
    run_dir = repo / ".aw" / "records" / "runs" / run_id
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    # Prior attempt left an outcome file containing a proposal on run_dir/outcomes/
    stale_outcome = {
        "schema_version": 1,
        "id6": "stl001",
        "disposition": "partial",
        "proposal": {
            "kind": "different-approach",
            "blocked_by": "stale attempt 1 blocker",
            "why": "prior attempt could not resolve it",
            "proposed_change": "stale proposal from attempt 1",
            "paths": ["README.md"],
            "size": "small",
        },
        "defect_report": {"state": "none-found", "findings": []},
        "pushed": False,
    }
    (run_dir / "outcomes" / "01-stl001.json").write_text(
        json.dumps(stale_outcome), encoding="utf-8"
    )

    silent_agent = support.make_fake_executable(
        tmp_path / "silent_agent",
        """#!/usr/bin/env python3
import json, sys
print(json.dumps({"event": "init", "conversation_id": "ses-2", "init": {"model": "test-model"}}), flush=True)
print(json.dumps({"type": "text", "sessionID": "ses-2", "part": {"text": "done without writing outcome"}}), flush=True)
sys.exit(0)
""",
    )
    item: dict[str, Any] = {
        "id6": "stl001",
        "setid": "testset",
        "position": 1,
        "action": "execute",
        "status": "queued",
        "configured_file": str(p.relative_to(repo)),
        "attempts": [
            {"number": 1, "disposition": "awaiting-human", "session_id": "ses-1"}
        ],
    }
    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": run_id,
        "queue": [item],
        "options": {
            "opencode": str(silent_agent),
            "no_verify": True,
            "validate": False,
            "no_audit": True,
            "self_finalize": False,
            "isolate_worktree": True,
        },
    }
    runner_shared.save_state(run_dir, state)

    with (
        mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
        mock.patch.object(
            oc_runipd,
            "run_suite_check",
            return_value=runner_shared.SuiteCheckResult(
                True, 0, "ok", "ok", "", 0.1, 0.1
            ),
        ),
        coordinator_role(),
    ):
        oc_runipd.execute_item(run_dir, state, item, recovery=False)

    assert "proposal_record" not in item
    assert "proposal_record" not in item["attempts"][-1]
    events = [
        json.loads(line)
        for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert not any(e.get("event") == "agent-proposal-filed" for e in events)


class TestProposalSummaryTruncation(unittest.TestCase):
    """l7d19a E-02: Unit tests for word-boundary proposal summary and slug truncation helpers."""

    def test_summary_short_string_unchanged(self) -> None:
        self.assertEqual(
            runner_shared._truncate_proposal_summary("Fix parser edge case"),
            "Fix parser edge case",
        )

    def test_summary_normalizes_newlines_and_tabs(self) -> None:
        raw = "  Fix\tproposal\n\r\nsummary   whitespace\t\n"
        self.assertEqual(
            runner_shared._truncate_proposal_summary(raw),
            "Fix proposal summary whitespace",
        )

    def test_summary_truncates_multi_word_on_word_boundary(self) -> None:
        text = (
            "Create and execute a scoped follow-up plan for coordinator "
            "truncation across all proposal paths"
        )
        # 'scoped' straddles char 24; 'truncation' straddles char 60.
        result = runner_shared._truncate_proposal_summary(text, max_chars=60)
        self.assertEqual(
            result,
            "Create and execute a scoped follow-up plan for coordinator",
        )
        self.assertLessEqual(len(result), 60)

    def test_summary_preserves_word_ending_exactly_at_max_chars(self) -> None:
        # 'Create and execute a scoped follow-up plan to unify proposal' is exactly 60 chars.
        exact_prefix = "Create and execute a scoped follow-up plan to unify proposal"
        self.assertEqual(len(exact_prefix), 60)
        text = f"{exact_prefix} summaries cleanly"
        self.assertEqual(
            runner_shared._truncate_proposal_summary(text, max_chars=60),
            exact_prefix,
        )

    def test_summary_single_unbroken_token_over_max_chars(self) -> None:
        token = "superlongunbrokentoken" * 5
        result = runner_shared._truncate_proposal_summary(token, max_chars=60)
        self.assertEqual(result, token[:60])
        self.assertEqual(len(result), 60)

    def test_summary_strips_trailing_punctuation_at_cut(self) -> None:
        text = (
            "Refactor the parser, validator, and formatter: "
            "ensure full coverage of every proposal branch"
        )
        result = runner_shared._truncate_proposal_summary(text, max_chars=50)
        self.assertEqual(result, "Refactor the parser, validator, and formatter")

    def test_summary_all_punctuation_prefix_fallback_is_non_empty(self) -> None:
        text = "...... " + ("word " * 20)
        result = runner_shared._truncate_proposal_summary(text, max_chars=10)
        self.assertEqual(result, "......")
        self.assertTrue(len(result) > 0)

        single_punct_token = "---...:::???" * 10
        result_single = runner_shared._truncate_proposal_summary(
            single_punct_token, max_chars=15
        )
        self.assertEqual(result_single, single_punct_token[:15])

    def test_slug_short_string_unchanged(self) -> None:
        self.assertEqual(
            runner_shared._truncate_proposal_slug("Proposal from 60mazt: fix tool"),
            "proposal-from-60mazt-fix-tool",
        )

    def test_slug_truncates_multi_word_on_hyphen_boundary(self) -> None:
        summary = (
            "Proposal from trc001: Create and execute a scoped "
            "follow-up plan for coordinator"
        )
        slug = runner_shared._truncate_proposal_slug(summary, max_chars=50)
        self.assertEqual(slug, "proposal-from-trc001-create-and-execute-a-scoped")
        self.assertLessEqual(len(slug), 50)
        self.assertFalse(slug.endswith("-"))

    def test_slug_preserves_token_ending_exactly_at_max_chars(self) -> None:
        exact_slug = "proposal-from-60mazt-create-and-execute-a-detailed"
        self.assertEqual(len(exact_slug), 50)
        result = runner_shared._truncate_proposal_slug(
            f"{exact_slug}-followup-plan", max_chars=50
        )
        self.assertEqual(result, exact_slug)

    def test_slug_single_unbroken_token_over_max_chars(self) -> None:
        token = "abcdefghijklmnopqrstuvwxyz" * 3
        slug = runner_shared._truncate_proposal_slug(token, max_chars=50)
        self.assertEqual(slug, token[:50])

    def test_slug_empty_or_punctuation_defaults_to_proposal(self) -> None:
        self.assertEqual(runner_shared._truncate_proposal_slug(""), "proposal")
        self.assertEqual(
            runner_shared._truncate_proposal_slug("... --- !!!"), "proposal"
        )


def test_coordinator_material_proposal_truncates_summary_and_slug_on_word_boundaries(
    tmp_path: Path,
) -> None:
    """l7d19a E-02: Live material proposal keeps complete words in - Summary: and backlog slug."""
    from agent_workflows import artifact_naming, backlog

    repo = _create_test_repo(tmp_path)
    plan_file = _create_plan_file(repo, "trc001", priority="low", work_kind="bug")
    run_dir = repo / ".aw" / "records" / "runs" / "run-trunc-mat"
    run_dir.mkdir(parents=True, exist_ok=True)

    # 'scoped' straddles char 24; 'truncation' straddles char 60; 'follow' straddles slug char 50.
    long_change = (
        "Create and execute a scoped follow-up plan for coordinator "
        "truncation across all proposal paths"
    )
    proposal = {
        "kind": "tool-defect",
        "blocked_by": "summary truncated mid-word",
        "why": "needs complete words in summary and filename slug",
        "proposed_change": long_change,
        "paths": ["agent_workflows/runner_shared.py"],
        "size": "material",
    }
    item = {"id6": "trc001", "configured_file": str(plan_file)}
    state = {"repo": str(repo), "run_id": "run-trunc-mat"}

    with coordinator_role():
        res = runner_shared.perform_coordinator_proposal_file(
            run_dir=run_dir,
            state=state,
            item=item,
            proposal=proposal,
        )

    assert res.filed is True
    bl_files = list(
        (repo / ".aw" / "records" / "backlog" / "open").glob("*.backlog.md")
    )
    assert len(bl_files) == 1
    bl_file = bl_files[0]
    bl_text = bl_file.read_text(encoding="utf-8")

    expected_summary = (
        "Proposal from trc001: Create and execute a scoped "
        "follow-up plan for coordinator"
    )
    parsed_item = backlog.parse_item(bl_text)
    assert parsed_item.summary == expected_summary
    assert "Create and execute a sco\n" not in bl_text

    parsed_name = artifact_naming.parse_clustered(bl_file.name)
    assert parsed_name is not None
    slug = parsed_name.group("slug")
    assert len(slug) <= 50
    assert slug == "proposal-from-trc001-create-and-execute-a-scoped"
    assert backlog.validate_item(bl_file, bl_text) == []


def test_coordinator_small_proposal_truncates_title_on_word_boundary(
    tmp_path: Path,
) -> None:
    """l7d19a E-02: Live small proposal produces complete-word # IPD: title and valid draft IPD."""
    from agent_workflows import artifact_naming, ipd_lint

    repo = _create_test_repo(tmp_path)
    plan_file = _create_plan_file(repo, "trc002", priority="low", work_kind="bug")
    run_dir = repo / ".aw" / "records" / "runs" / "run-trunc-small"
    run_dir.mkdir(parents=True, exist_ok=True)

    long_change = (
        "Create and execute a scoped follow-up plan for coordinator "
        "truncation across all proposal paths"
    )
    proposal = {
        "kind": "gate-change",
        "blocked_by": "title truncated mid-word",
        "why": "needs complete words in scaffolded draft title",
        "proposed_change": long_change,
        "paths": ["agent_workflows/runner_shared.py"],
        "size": "small",
    }
    item = {"id6": "trc002", "configured_file": str(plan_file)}
    state = {"repo": str(repo), "run_id": "run-trunc-small"}

    with coordinator_role():
        res = runner_shared.perform_coordinator_proposal_file(
            run_dir=run_dir,
            state=state,
            item=item,
            proposal=proposal,
        )

    assert res.filed is True
    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
    matching = list(plans_dir.glob("*-prop-trc002-01-*.ipd.md"))
    assert len(matching) == 1
    created_plan = matching[0]
    plan_text = created_plan.read_text(encoding="utf-8")

    expected_title = (
        "# IPD: Proposal from trc002: Create and execute a scoped "
        "follow-up plan for coordinator"
    )
    assert plan_text.splitlines()[0] == expected_title

    parsed_name = artifact_naming.parse_clustered(created_plan.name)
    assert parsed_name is not None
    lint_result = ipd_lint.lint_file(created_plan, checkpoint="author")
    assert lint_result.passing, lint_result.diagnostics
    assert lint_result.diagnostics == []


@pytest.mark.parametrize("size", ["material", "small"])
def test_coordinator_fallback_record_truncates_on_word_boundary(
    tmp_path: Path, size: str
) -> None:
    """l7d19a E-02: Fallback record uses word-boundary truncation when integration lock is held."""
    repo = _create_test_repo(tmp_path)
    plan_file = _create_plan_file(repo, "lck002")
    run_dir = repo / ".aw" / "records" / "runs" / f"run-locked-{size}"
    run_dir.mkdir(parents=True, exist_ok=True)

    long_change = (
        "Create and execute a scoped\tfollow-up plan for coordinator\n"
        "truncation across all proposal paths"
    )
    proposal = {
        "kind": "tool-defect",
        "blocked_by": "lock error",
        "why": "lock timeout word-boundary test",
        "proposed_change": long_change,
        "paths": ["agent_workflows/runner_shared.py"],
        "size": size,
    }
    item = {"id6": "lck002", "configured_file": str(plan_file)}
    state = {"repo": str(repo), "run_id": f"run-locked-{size}"}

    @contextlib.contextmanager
    def fake_lock(*a: Any, **k: Any):
        yield runner_shared.IntegrationLockOutcome(
            acquired=False,
            handle=None,
            waited_seconds=5.0,
            holder="peer-agent",
            detail="the repository integration lock is held; waited 5s and gave up",
        )

    with mock.patch(
        "agent_workflows.runner_shared.integration_lock", side_effect=fake_lock
    ), coordinator_role():
        res = runner_shared.perform_coordinator_proposal_file(
            run_dir=run_dir,
            state=state,
            item=item,
            proposal=proposal,
            timeout=0.01,
        )

    assert res.filed is False
    expected_tail = (
        "Proposal from lck002: Create and execute a scoped "
        "follow-up plan for coordinator"
    )
    if size == "small":
        saved = list((run_dir / "proposals").glob("*proposal.ipd.md"))
        assert len(saved) == 1
        text = saved[0].read_text(encoding="utf-8")
        assert text.splitlines()[0] == f"# IPD: {expected_tail}"
    else:
        saved = list((run_dir / "proposals").glob("*proposal.backlog.md"))
        assert len(saved) == 1
        text = saved[0].read_text(encoding="utf-8")
        assert f"- Summary: {expected_tail}" in text
