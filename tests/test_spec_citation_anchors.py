"""Tests for spec line-anchor citations detector and CLI (IPD mt54wr, backlog sbh1o1).

Asserts OUTCOMES of the detector and the CLI on self-written fixtures, never code structure.
P16 compliant: behavioral assertions only, no code-structure pinning, no live-tree census counts.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import pytest

from agent_workflows import agent_schema, check_engine, cli, spec_citations


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
    """(d) The bare-backtick spelling is detected when preceding line attributes known id6."""
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


def test_a_table_row_anchor_key_cell_in_block_produces_no_finding(
    temp_spec_repo: Path,
) -> None:
    """(a) A table-row anchor whose key cell appears on a neighbouring comment line produces no finding."""
    spec_path = (
        temp_spec_repo
        / ".aw"
        / "records"
        / "specs"
        / "approved"
        / "20260901-tbl001-01-tbl001-table.spec.md"
    )
    spec_path.write_text(
        "# Spec: Table\n\n- Id: tbl001\n- Status: approved\n\n## 1. Catalog\n\n| I-07 | Release-gate preservation |\n",
        encoding="utf-8",
    )
    src_file = temp_spec_repo / "agent_workflows" / "mod_tbl_a.py"
    src_file.write_text(
        "# I-07 invariant verified here:\n"
        "# as documented in spec tbl001 :8\n"
        "# I-07 preservation confirmed.\n",
        encoding="utf-8",
    )
    findings = spec_citations.stale_spec_anchors(temp_spec_repo, [src_file])
    assert len(findings) == 0


def test_b_table_row_anchor_key_cell_absent_produces_one_finding(
    temp_spec_repo: Path,
) -> None:
    """(b) A table-row anchor with the key cell absent from the block produces one finding."""
    spec_path = (
        temp_spec_repo
        / ".aw"
        / "records"
        / "specs"
        / "approved"
        / "20260901-tbl001-01-tbl001-table.spec.md"
    )
    spec_path.write_text(
        "# Spec: Table\n\n- Id: tbl001\n- Status: approved\n\n## 1. Catalog\n\n| I-07 | Release-gate preservation |\n",
        encoding="utf-8",
    )
    src_file = temp_spec_repo / "agent_workflows" / "mod_tbl_b.py"
    src_file.write_text(
        "# Some general comments with key cell absent:\n"
        "# as documented in spec tbl001 :8\n"
        "# without mentioning the key cell.\n",
        encoding="utf-8",
    )
    findings = spec_citations.stale_spec_anchors(temp_spec_repo, [src_file])
    assert len(findings) == 1
    assert findings[0].id6 == "tbl001"
    assert findings[0].offset == 8
    assert findings[0].enclosing_heading == "## 1. Catalog"
    assert findings[0].validity == "valid"


def test_c_unattributed_spec_anchor_in_block_naming_no_id6_produces_finding(
    temp_spec_repo: Path,
) -> None:
    """(c) An unattributed bare spec anchor in a block naming no id6 produces one finding with validity 'unattributed'."""
    src_file = temp_spec_repo / "agent_workflows" / "mod_unattr.py"
    src_file.write_text(
        "# Generic comment block naming no spec id6:\n"
        "# as specified by spec `:11`, verify this.\n",
        encoding="utf-8",
    )
    findings = spec_citations.stale_spec_anchors(temp_spec_repo, [src_file])
    assert len(findings) == 1
    assert findings[0].id6 == ""
    assert findings[0].offset == 11
    assert findings[0].enclosing_heading == ""
    assert findings[0].validity == "unattributed"


def test_d_bare_backtick_offset_without_spec_word_produces_no_finding(
    temp_spec_repo: Path,
) -> None:
    """(d) A line citing a colon offset with no 'spec' word produces no finding."""
    src_file = temp_spec_repo / "agent_workflows" / "mod_nospec.py"
    src_file.write_text(
        "# Generic self-reference:\n" "# see the comment at `:11` for details.\n",
        encoding="utf-8",
    )
    findings = spec_citations.stale_spec_anchors(temp_spec_repo, [src_file])
    assert len(findings) == 0


def test_e_cli_check_specs_source_anchors_agent_stale_anchor_conforms_exit_zero(
    temp_spec_repo: Path,
) -> None:
    """(e) CLI: `aw check specs --source-anchors --agent` with stale anchor exits 0, has outcome 'conforms', and check.spec-anchor-stale diagnostic."""
    src_file = temp_spec_repo / "agent_workflows" / "mod_cli_stale.py"
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
            "--agent",
            "--dir",
            str(temp_spec_repo),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "Traceback" not in proc.stderr
    assert "ValueError" not in proc.stderr
    assert proc.stdout.strip()
    records = []
    for line in proc.stdout.strip().splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    result_recs = [
        r for r in records if r.get("kind") == "result" or r.get("cmd") == "check"
    ]
    assert len(result_recs) >= 1
    rec = result_recs[0]
    assert rec["outcome"] == "conforms"
    assert rec["exit"] == 0
    assert any(
        d.get("rule") == "check.spec-anchor-stale" for d in rec.get("diagnostics", [])
    )


def test_f_cli_check_specs_source_anchors_agent_clean_reports_clean_exit_zero(
    temp_spec_repo: Path,
) -> None:
    """(f) CLI: `aw check specs --source-anchors --agent` with no stale anchor reports outcome 'clean' and exit 0."""
    src_file = temp_spec_repo / "agent_workflows" / "mod_cli_clean.py"
    src_file.write_text(
        "# Clean anchor: spec smpl01 Section 1.1 :11\n",
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
            "--agent",
            "--dir",
            str(temp_spec_repo),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "Traceback" not in proc.stderr
    assert proc.stdout.strip()
    records = []
    for line in proc.stdout.strip().splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    result_recs = [
        r for r in records if r.get("kind") == "result" or r.get("cmd") == "check"
    ]
    assert len(result_recs) >= 1
    rec = result_recs[0]
    assert rec["outcome"] == "clean"
    assert rec["exit"] == 0
    assert rec.get("findings", 0) == 0


def test_g_cli_bare_check_source_anchors_agent_verbose_findings_conforms_exit_zero(
    temp_spec_repo: Path,
) -> None:
    """(g) CLI: bare `aw check --source-anchors --agent --verbose` reports outcome 'conforms', exit 0, and verbose evidence."""
    src_file = temp_spec_repo / "agent_workflows" / "mod_cli_g.py"
    src_file.write_text(
        "# Stale anchor: spec smpl01 Section 2.1 :11\n\n"
        "# Generic comment block naming no spec id6:\n"
        "# as specified by spec `:11`, verify this.\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "check",
            "--source-anchors",
            "--agent",
            "--verbose",
            "--dir",
            str(temp_spec_repo),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "Traceback" not in proc.stderr
    assert "ValueError" not in proc.stderr
    assert proc.stdout.strip()
    records = []
    for line in proc.stdout.strip().splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    result_recs = [
        r for r in records if r.get("kind") == "result" or r.get("cmd") == "check"
    ]
    assert len(result_recs) >= 1
    rec = result_recs[0]
    assert rec["outcome"] == "conforms"
    assert rec["exit"] == 0
    assert rec["target"] == "source-anchors"
    assert rec["findings"] == 2
    assert rec["findings_by_severity"] == {"error": 0, "warning": 0, "info": 2}
    ev_by_key = {e["key"]: e for e in rec["evidence"]}
    assert ev_by_key["source_anchors"]["status"] == "conforms"
    assert ev_by_key["rules"]["status"] == "conforms"
    assert ev_by_key["rules"]["value"] == {"errors": 0, "warnings": 0, "info": 2}
    diagnostics = rec.get("diagnostics", [])
    assert len(diagnostics) == 2
    assert all(d.get("rule") == "check.spec-anchor-stale" for d in diagnostics)
    assert all(d.get("severity") == "info" for d in diagnostics)
    assert any(
        "encloses '### 1.1 Normative Roles'" in d.get("detail", "") for d in diagnostics
    )
    assert any("unattributed" in d.get("detail", "") for d in diagnostics)
    assert agent_schema.validate_agent_record(rec) == []


def test_h_cli_check_source_anchors_agent_non_info_severity_reports_findings_exit_one(
    temp_spec_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """(h) CLI: `aw check --source-anchors --agent --verbose` reports outcome 'findings' and exit 1 when rule severity is non-info."""
    src_file = temp_spec_repo / "agent_workflows" / "mod_cli_h.py"
    src_file.write_text(
        "# Stale anchor: spec smpl01 Section 2.1 :11\n",
        encoding="utf-8",
    )
    monkeypatch.setitem(
        check_engine.RULE_REGISTRY,
        "check.spec-anchor-stale",
        check_engine.RULE_REGISTRY["check.spec-anchor-stale"]._replace(
            severity="error"
        ),
    )
    ret = cli.main(
        [
            "check",
            "--source-anchors",
            "--agent",
            "--verbose",
            "--dir",
            str(temp_spec_repo),
        ]
    )
    captured = capsys.readouterr()
    assert ret == 1
    assert captured.err == ""
    assert captured.out.strip()
    records = []
    for line in captured.out.strip().splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    result_recs = [
        r for r in records if r.get("kind") == "result" or r.get("cmd") == "check"
    ]
    assert len(result_recs) >= 1
    rec = result_recs[0]
    assert agent_schema.validate_agent_record(rec) == []
    assert rec["outcome"] == "findings"
    assert rec["exit"] == 1
    assert rec["target"] == "source-anchors"
    assert rec["findings"] == 1
    assert rec["findings_by_severity"] == {"error": 1, "warning": 0, "info": 0}
    ev_by_key = {e["key"]: e for e in rec["evidence"]}
    assert ev_by_key["source_anchors"]["status"] == "findings"
    assert ev_by_key["rules"]["status"] == "findings"
    assert ev_by_key["rules"]["value"] == {"errors": 1, "warnings": 0, "info": 0}
