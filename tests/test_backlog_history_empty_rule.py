"""Behavioral tests for backlog.history-empty drift rule (IPD v5m5y8).

Fences:
(a) a conformant item yields no backlog.history-empty;
(b) heading with only an indented history-shaped line yields it with the "no column-zero record" detail;
(c) heading with only blank lines then prose yields it;
(d) no heading yields it with the "no heading" detail (assert the two details differ);
(e) an item written by the real writer (cli.main(["backlog","new",...,"--dir",<root>])) yields no backlog.history-empty;
(f) cli.main(["backlog","check","--dir",<root>]) over a temp repo holding case (b) exits nonzero and names the rule, and over conformant items exits 0;
(g) check_engine record type backlog (drive aw check backlog via cli.main on the same temp repo) reports the rule for case (b).
"""

import contextlib
import io
from pathlib import Path

from agent_workflows import backlog, cli


def _capture_cli(argv: list[str]) -> tuple[int, str, str]:
    """Execute cli.main in-process capturing stdout, stderr, and exit code."""
    out, err = io.StringIO(), io.StringIO()
    code = None
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = cli.main(argv)
        except SystemExit as exc:
            code = exc.code
    return code if code is not None else 0, out.getvalue(), err.getvalue()


def test_case_a_conformant_item_yields_no_history_empty():
    """Case (a): a conformant item yields no backlog.history-empty."""
    text = (
        "- Id: bkl001\n"
        "- Status: open\n"
        "- Set: demo\n"
        "- Priority: high\n"
        "- Work-Kind: feature\n"
        "- Summary: Conformant item\n\n"
        "## Workflow history\n\n"
        "- 2026-10-12 created (aw backlog): initial filing\n\n"
        "## Detail\n\nProse.\n"
    )
    p = Path(".aw/records/backlog/open/20261012-demo-01-bkl001-item.backlog.md")
    drift = backlog.validate_item(p, text)
    history_rules = [d.rule for d in drift if d.rule == "backlog.history-empty"]
    assert history_rules == []


def test_case_b_indented_history_only_yields_no_column_zero_detail():
    """Case (b): heading with only an indented history-shaped line yields it with the 'no column-zero record' detail."""
    text = (
        "- Id: bkl002\n"
        "- Status: open\n"
        "- Set: demo\n"
        "- Priority: high\n"
        "- Work-Kind: feature\n"
        "- Summary: Indented history only\n\n"
        "## Workflow history\n\n"
        "  - 2026-10-12 created (aw backlog): initial filing\n\n"
        "## Detail\n\nProse.\n"
    )
    p = Path(".aw/records/backlog/open/20261012-demo-01-bkl002-item.backlog.md")
    drift = backlog.validate_item(p, text)
    history_drifts = [d for d in drift if d.rule == "backlog.history-empty"]
    assert len(history_drifts) == 1
    assert "no column-zero" in history_drifts[0].detail
    assert (
        "restore the records from git history (an indented line is not a record)"
        in history_drifts[0].detail
    )


def test_case_c_blank_lines_then_prose_yields_history_empty():
    """Case (c): heading with only blank lines then prose yields backlog.history-empty."""
    text = (
        "- Id: bkl003\n"
        "- Status: open\n"
        "- Set: demo\n"
        "- Priority: high\n"
        "- Work-Kind: feature\n"
        "- Summary: Blank lines then prose\n\n"
        "## Workflow history\n\n\n\n"
        "Prose directly under heading without a record.\n"
    )
    p = Path(".aw/records/backlog/open/20261012-demo-01-bkl003-item.backlog.md")
    drift = backlog.validate_item(p, text)
    history_drifts = [d for d in drift if d.rule == "backlog.history-empty"]
    assert len(history_drifts) == 1
    assert "no column-zero" in history_drifts[0].detail


def test_case_d_no_heading_yields_no_heading_detail_and_differs_from_case_b():
    """Case (d): no heading yields it with the 'no heading' detail (assert the two details differ)."""
    text_d = (
        "- Id: bkl004\n"
        "- Status: open\n"
        "- Set: demo\n"
        "- Priority: high\n"
        "- Work-Kind: feature\n"
        "- Summary: No heading\n\n"
        "## Detail\n\nProse.\n"
    )
    text_b = (
        "- Id: bkl002\n"
        "- Status: open\n"
        "- Set: demo\n"
        "- Priority: high\n"
        "- Work-Kind: feature\n"
        "- Summary: Indented history only\n\n"
        "## Workflow history\n\n"
        "  - 2026-10-12 created (aw backlog): initial filing\n\n"
        "## Detail\n\nProse.\n"
    )
    p = Path(".aw/records/backlog/open/20261012-demo-01-bkl004-item.backlog.md")
    drift_d = backlog.validate_item(p, text_d)
    drift_b = backlog.validate_item(p, text_b)
    d_drifts = [d for d in drift_d if d.rule == "backlog.history-empty"]
    b_drifts = [d for d in drift_b if d.rule == "backlog.history-empty"]
    assert len(d_drifts) == 1
    assert len(b_drifts) == 1
    assert "no ## Workflow history heading" in d_drifts[0].detail
    assert (
        "restore the records from git history (an indented line is not a record)"
        in d_drifts[0].detail
    )
    assert d_drifts[0].detail != b_drifts[0].detail


def test_case_e_real_writer_item_yields_no_history_empty(tmp_path):
    """Case (e): an item written by the real writer yields no backlog.history-empty."""
    repo_root = tmp_path / "repo"
    (repo_root / ".aw" / "records" / "backlog" / "open").mkdir(
        parents=True, exist_ok=True
    )
    code, out, err = _capture_cli(
        [
            "backlog",
            "new",
            "--summary",
            "Real writer test item",
            "--priority",
            "high",
            "--work-kind",
            "feature",
            "--set",
            "testset",
            "--dir",
            str(repo_root),
            "--apply",
        ]
    )
    assert code == 0, f"backlog new failed: {err}\n{out}"
    written_files = list(
        (repo_root / ".aw" / "records" / "backlog" / "open").glob("*.md")
    )
    assert len(written_files) == 1
    item_file = written_files[0]
    drift = backlog.validate_item(item_file, item_file.read_text(encoding="utf-8"))
    history_rules = [d.rule for d in drift if d.rule == "backlog.history-empty"]
    assert history_rules == []


def test_case_f_cli_backlog_check(tmp_path):
    """Case (f): cli.main(['backlog', 'check', ...]) exits nonzero and names the rule for case (b), exits 0 for conformant items."""
    repo_root = tmp_path / "repo"
    open_dir = repo_root / ".aw" / "records" / "backlog" / "open"
    open_dir.mkdir(parents=True, exist_ok=True)

    # Place case (b) item (indented history line only)
    b_file = open_dir / "20261012-demo-01-bkl002-case-b.backlog.md"
    b_file.write_text(
        "- Id: bkl002\n"
        "- Status: open\n"
        "- Set: demo\n"
        "- Priority: high\n"
        "- Work-Kind: feature\n"
        "- Summary: Indented history only\n\n"
        "## Workflow history\n\n"
        "  - 2026-10-12 created (aw backlog): initial filing\n\n"
        "## Detail\n\nProse.\n",
        encoding="utf-8",
    )
    code, out, err = _capture_cli(["backlog", "check", "--dir", str(repo_root)])
    assert code != 0
    assert "backlog.history-empty" in out or "backlog.history-empty" in err

    # Replace with conformant item
    b_file.unlink()
    ok_file = open_dir / "20261012-demo-01-bkl001-conformant.backlog.md"
    ok_file.write_text(
        "- Id: bkl001\n"
        "- Status: open\n"
        "- Set: demo\n"
        "- Priority: high\n"
        "- Work-Kind: feature\n"
        "- Summary: Conformant item\n\n"
        "## Workflow history\n\n"
        "- 2026-10-12 created (aw backlog): initial filing\n\n"
        "## Detail\n\nProse.\n",
        encoding="utf-8",
    )
    code_ok, out_ok, err_ok = _capture_cli(
        ["backlog", "check", "--dir", str(repo_root)]
    )
    assert (
        code_ok == 0
    ), f"backlog check over conformant repo failed: {err_ok}\n{out_ok}"


def test_case_g_check_engine_backlog_reports_rule(tmp_path):
    """Case (g): check_engine record type backlog reports the rule for case (b)."""
    repo_root = tmp_path / "repo"
    open_dir = repo_root / ".aw" / "records" / "backlog" / "open"
    open_dir.mkdir(parents=True, exist_ok=True)

    b_file = open_dir / "20261012-demo-01-bkl002-case-b.backlog.md"
    b_file.write_text(
        "- Id: bkl002\n"
        "- Status: open\n"
        "- Set: demo\n"
        "- Priority: high\n"
        "- Work-Kind: feature\n"
        "- Summary: Indented history only\n\n"
        "## Workflow history\n\n"
        "  - 2026-10-12 created (aw backlog): initial filing\n\n"
        "## Detail\n\nProse.\n",
        encoding="utf-8",
    )
    code, out, err = _capture_cli(["check", "backlog", "--dir", str(repo_root)])
    assert code != 0
    assert "backlog.history-empty" in out or "backlog.history-empty" in err
