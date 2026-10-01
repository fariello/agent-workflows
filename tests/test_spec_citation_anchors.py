"""Tests for spec line-anchor citations detector and CLI (IPD mt54wr, backlog sbh1o1).

Asserts OUTCOMES of the detector and the CLI on self-written fixtures, never code structure.
P16 compliant: behavioral assertions only, no code-structure pinning, no live-tree census counts.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import pytest

from agent_workflows import spec_citations


@pytest.fixture
def temp_spec_repo(tmp_path: Path) -> Path:
    """Create a minimal repository fixture with one spec and source files."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    specs_dir = repo_root / ".aw" / "records" / "specs" / "approved"
    specs_dir.mkdir(parents=True)

    spec_text = (
        "# Spec: Sample Protocol\n"
        "\n"
        "- Id: smpl01\n"
        "- Status: approved\n"
        "\n"
        "## Workflow history\n"
        "- 2026-09-01 approved\n"
        "\n"
        "### 1.1 Normative Roles\n"
        "\n"
        "Line 11: Normative content here.\n"
        "Line 12: More normative text.\n"
        "\n"
        "```\n"
        "Line 15: code fence content\n"
        "Line 16: more code fence\n"
        "```\n"
        "\n"
        "### 2.1 Execution Grammar\n"
        "\n"
        "Line 21: Grammar rules here.\n"
    )
    spec_path = specs_dir / "20260901-smpl01-01-smpl01-sample.spec.md"
    spec_path.write_text(spec_text, encoding="utf-8")

    src_dir = repo_root / "agent_workflows"
    src_dir.mkdir()

    return repo_root


def test_citation_landing_under_named_heading_produces_no_finding(
    temp_spec_repo: Path,
) -> None:
    """(a) A citation whose offset lands under the heading the text names produces NO finding."""
    src_file = temp_spec_repo / "agent_workflows" / "mod_a.py"
    src_file.write_text(
        "# According to spec smpl01 Section 1.1 :11, normative rules apply.\n",
        encoding="utf-8",
    )

    findings = spec_citations.stale_spec_anchors(
        temp_spec_repo, [temp_spec_repo / "agent_workflows"]
    )
    assert len(findings) == 0


def test_citation_landing_under_different_heading_produces_one_finding(
    temp_spec_repo: Path,
) -> None:
    """(b) A citation whose offset lands under a DIFFERENT heading produces one finding naming that actual heading."""
    src_file = temp_spec_repo / "agent_workflows" / "mod_b.py"
    src_file.write_text(
        "# According to spec smpl01 Section 2.1 :11, normative rules apply.\n",
        encoding="utf-8",
    )

    findings = spec_citations.stale_spec_anchors(
        temp_spec_repo, [temp_spec_repo / "agent_workflows"]
    )
    assert len(findings) == 1
    finding = findings[0]
    assert finding.id6 == "smpl01"
    assert finding.offset == 11
    assert finding.enclosing_heading == "### 1.1 Normative Roles"
    assert finding.validity == "valid"


def test_past_eof_and_in_fence_offsets_reported_as_invalid(
    temp_spec_repo: Path,
) -> None:
    """(c) An offset past end-of-file and an offset inside a fenced code block are each reported as invalid."""
    src_file = temp_spec_repo / "agent_workflows" / "mod_c.py"
    src_file.write_text(
        "# Citation past EOF: spec smpl01 :999\n"
        "# Citation inside code fence: spec smpl01 :15\n",
        encoding="utf-8",
    )

    findings = spec_citations.stale_spec_anchors(
        temp_spec_repo, [temp_spec_repo / "agent_workflows"]
    )
    assert len(findings) == 2
    by_offset = {f.offset: f for f in findings}

    past_eof = by_offset[999]
    assert past_eof.validity == "past_eof"
    assert past_eof.enclosing_heading == ""

    in_fence = by_offset[15]
    assert in_fence.validity == "in_fence"
    assert in_fence.enclosing_heading == ""


def test_bare_backtick_spelling_detected_in_same_comment_block(
    temp_spec_repo: Path,
) -> None:
    """(d) The bare-backtick spelling (spec `:131`) is detected when preceding line attributes known id6."""
    src_file = temp_spec_repo / "agent_workflows" / "mod_d.py"
    src_file.write_text(
        "# Working with spec smpl01 specification:\n"
        "# As required by spec `:21`, verify grammar.\n",
        encoding="utf-8",
    )

    findings = spec_citations.stale_spec_anchors(
        temp_spec_repo, [temp_spec_repo / "agent_workflows"]
    )
    assert len(findings) == 1
    finding = findings[0]
    assert finding.id6 == "smpl01"
    assert finding.offset == 21
    assert finding.enclosing_heading == "### 2.1 Execution Grammar"


def test_cli_check_specs_source_anchors_exits_zero_with_finding(
    temp_spec_repo: Path,
) -> None:
    """CLI: `aw check specs --source-anchors` on fixture with stale anchor exits 0 and prints finding."""
    src_file = temp_spec_repo / "agent_workflows" / "mod_cli.py"
    src_file.write_text(
        "# Stale anchor: spec smpl01 Section 2.1 :11\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "check",
            "specs",
            "--source-anchors",
            "--dir",
            str(temp_spec_repo),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "spec smpl01 :11 -> ### 1.1 Normative Roles" in proc.stdout


def test_cli_bare_check_specs_omits_finding(temp_spec_repo: Path) -> None:
    """CLI: bare `aw check specs` prints no source-anchor finding and does not run rule."""
    src_file = temp_spec_repo / "agent_workflows" / "mod_cli.py"
    src_file.write_text(
        "# Stale anchor: spec smpl01 Section 2.1 :11\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "check",
            "specs",
            "--agent",
            "--dir",
            str(temp_spec_repo),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert "check.spec-anchor-stale" not in proc.stdout
    assert "spec smpl01 :11" not in proc.stdout


def test_cli_non_specs_positional_type_runs_anchor_report(
    temp_spec_repo: Path,
) -> None:
    """CLI: non-specs positional type (`aw check plans --source-anchors`) runs anchor report and exits 0."""
    src_file = temp_spec_repo / "agent_workflows" / "mod_cli.py"
    src_file.write_text(
        "# Stale anchor: spec smpl01 Section 2.1 :11\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "check",
            "plans",
            "--source-anchors",
            "--dir",
            str(temp_spec_repo),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "spec smpl01 :11 -> ### 1.1 Normative Roles" in proc.stdout
