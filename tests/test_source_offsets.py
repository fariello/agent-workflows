"""Tests for pure source offsets detector and CLI (IPD pyuw4v, backlog 7jl2bf).

Asserts OUTCOMES of the detector and the CLI on self-written fixtures, never code structure.
P16 compliant: behavioral assertions only, no code-structure pinning, no live-tree census counts.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path
import pytest

from agent_workflows import check_engine, cli, source_offsets


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Create a minimal AW project repository fixture."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".aw" / "records").mkdir(parents=True)
    return repo


def test_a_comment_citing_past_eof_yields_past_eof(temp_repo: Path) -> None:
    """(a) A comment citing target.py:999 against a 5-line target.py yields one past_eof."""
    target = temp_repo / "target.py"
    target.write_text("# 1\n# 2\n# 3\n# 4\n# 5\n", encoding="utf-8")

    citing = temp_repo / "citing.py"
    citing.write_text("# cites target.py:999\n", encoding="utf-8")

    findings = source_offsets.stale_source_offsets(temp_repo, [temp_repo])
    assert len(findings) == 1
    f = findings[0]
    assert f.file == citing
    assert f.line == 1
    assert f.cited == "target.py:999"
    assert f.offset == 999
    assert f.validity == "past_eof"


def test_b_docstring_citing_blank_line_yields_blank_line_with_physical_line(
    temp_repo: Path,
) -> None:
    """(b) A docstring line citing an offset that lands on a blank line yields one blank_line with the docstring's physical line number."""
    target = temp_repo / "target.py"
    target.write_text("x = 1\n\ny = 2\n", encoding="utf-8")  # line 2 is blank

    citing = temp_repo / "citing.py"
    citing.write_text(
        "def f():\n"
        '    """Docstring start\n'
        "    line 3 cites target.py:2\n"
        '    """\n'
        "    pass\n",
        encoding="utf-8",
    )

    findings = source_offsets.stale_source_offsets(temp_repo, [temp_repo])
    assert len(findings) == 1
    f = findings[0]
    assert f.file == citing
    assert f.line == 3
    assert f.cited == "target.py:2"
    assert f.offset == 2
    assert f.validity == "blank_line"


def test_c_citation_landing_on_bare_close_paren_yields_punct_only(
    temp_repo: Path,
) -> None:
    """(c) A citation landing on a bare `)` yields one punct_only."""
    target = temp_repo / "target.py"
    target.write_text(
        "def f(\n    a,\n    b,\n):\n    pass\n", encoding="utf-8"
    )  # line 4 is '):'

    citing = temp_repo / "citing.py"
    citing.write_text("# cites target.py:4\n", encoding="utf-8")

    findings = source_offsets.stale_source_offsets(temp_repo, [temp_repo])
    assert len(findings) == 1
    f = findings[0]
    assert f.file == citing
    assert f.line == 1
    assert f.cited == "target.py:4"
    assert f.offset == 4
    assert f.validity == "punct_only"


def test_d_citation_landing_on_real_code_yields_none(temp_repo: Path) -> None:
    """(d) A citation landing on real code yields none."""
    target = temp_repo / "target.py"
    target.write_text(
        "def f():\n    return 42\n", encoding="utf-8"
    )  # line 2 is '    return 42'

    citing = temp_repo / "citing.py"
    citing.write_text("# cites target.py:2\n", encoding="utf-8")

    findings = source_offsets.stale_source_offsets(temp_repo, [temp_repo])
    assert len(findings) == 0


def test_e_past_eof_citation_in_string_literal_assignment_yields_none(
    temp_repo: Path,
) -> None:
    """(e) The same past-EOF citation inside an ordinary string literal assignment yields none."""
    target = temp_repo / "target.py"
    target.write_text("x = 1\n", encoding="utf-8")

    citing = temp_repo / "citing.py"
    citing.write_text('s = "target.py:999"\n', encoding="utf-8")

    findings = source_offsets.stale_source_offsets(temp_repo, [temp_repo])
    assert len(findings) == 0


def test_f_citation_naming_nonexistent_file_yields_none(temp_repo: Path) -> None:
    """(f) A citation naming a file that does not exist yields none."""
    citing = temp_repo / "citing.py"
    citing.write_text("# cites nonexistent.py:999\n", encoding="utf-8")

    findings = source_offsets.stale_source_offsets(temp_repo, [temp_repo])
    assert len(findings) == 0


def test_g_past_eof_citation_with_commit_hash_yields_none(temp_repo: Path) -> None:
    """(g) A past-EOF citation whose line also carries `at 6e299712f` yields none."""
    target = temp_repo / "target.py"
    target.write_text("x = 1\n", encoding="utf-8")

    citing = temp_repo / "citing.py"
    citing.write_text("# cites target.py:999 at 6e299712f\n", encoding="utf-8")

    findings = source_offsets.stale_source_offsets(temp_repo, [temp_repo])
    assert len(findings) == 0


def test_h_range_with_end_offset_past_eof_yields_past_eof(temp_repo: Path) -> None:
    """(h) A range `target.py:2-999` yields one past_eof."""
    target = temp_repo / "target.py"
    target.write_text("line1 = 1\nline2 = 2\nline3 = 3\n", encoding="utf-8")

    citing = temp_repo / "citing.py"
    citing.write_text("# range target.py:2-999\n", encoding="utf-8")

    findings = source_offsets.stale_source_offsets(temp_repo, [temp_repo])
    assert len(findings) == 1
    f = findings[0]
    assert f.file == citing
    assert f.line == 1
    assert f.cited == "target.py:2-999"
    assert f.offset == 2
    assert f.validity == "past_eof"


def test_i_basename_citation_resolves_to_sibling_file_in_citing_dir(
    temp_repo: Path,
) -> None:
    """(i) A basename citation resolves to the sibling file in the citing directory when two same-named files exist elsewhere."""
    dir_a = temp_repo / "dir_a"
    dir_b = temp_repo / "dir_b"
    dir_c = temp_repo / "dir_c"
    dir_a.mkdir()
    dir_b.mkdir()
    dir_c.mkdir()

    # Sibling file has 5 lines, line 15 is past EOF
    sibling_target = dir_a / "target.py"
    sibling_target.write_text("# 1\n# 2\n# 3\n# 4\n# 5\n", encoding="utf-8")

    # Other files elsewhere have 20 and 10 lines
    (dir_b / "target.py").write_text(
        "\n".join(f"# {i}" for i in range(1, 21)) + "\n", encoding="utf-8"
    )
    (dir_c / "target.py").write_text(
        "\n".join(f"# {i}" for i in range(1, 11)) + "\n", encoding="utf-8"
    )

    citing = dir_a / "citing.py"
    citing.write_text("# cites target.py:15\n", encoding="utf-8")

    findings = source_offsets.stale_source_offsets(temp_repo, [temp_repo])
    assert len(findings) == 1
    f = findings[0]
    assert f.file == citing
    assert f.target.resolve() == sibling_target.resolve()
    assert f.offset == 15
    assert f.validity == "past_eof"


def test_j_cli_main_returns_zero_and_prints_finding(temp_repo: Path) -> None:
    """(j) `cli.main(["check", "--source-offsets", "--dir", <fixture>])` returns 0 and prints the finding."""
    target = temp_repo / "target.py"
    target.write_text("# 1\n# 2\n# 3\n# 4\n# 5\n", encoding="utf-8")

    citing = temp_repo / "citing.py"
    citing.write_text("# cites target.py:999\n", encoding="utf-8")

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli.main(["check", "--source-offsets", "--dir", str(temp_repo)])
    out = buf.getvalue()
    assert rc == 0
    assert "target.py:999 -> past_eof" in out


def test_k_cli_agent_subprocess_conforms_exit_zero(
    temp_repo: Path, tmp_path: Path
) -> None:
    """(k) `aw check --source-offsets --agent --dir <fixture>` run as a subprocess exits 0, writes no traceback to stderr, and its first JSON record carries outcome `conforms` and a `check.source-offset-stale` diagnostic with severity `info`."""
    target = temp_repo / "target.py"
    target.write_text("# 1\n# 2\n# 3\n# 4\n# 5\n", encoding="utf-8")

    citing = temp_repo / "citing.py"
    citing.write_text("# cites target.py:999\n", encoding="utf-8")

    checkout_root = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env["PYTHONPATH"] = str(checkout_root)
    env["AW_NO_REEXEC"] = "1"
    home_dir = tmp_path / "home"
    config_dir = home_dir / ".config"
    config_dir.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(home_dir)
    env["XDG_CONFIG_HOME"] = str(config_dir)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "check",
            "--source-offsets",
            "--agent",
            "--dir",
            str(temp_repo),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0
    assert "Traceback" not in proc.stderr
    assert proc.stderr.strip() == ""

    records = [
        json.loads(line) for line in proc.stdout.strip().splitlines() if line.strip()
    ]
    assert len(records) >= 1
    rec = records[0]
    assert rec["outcome"] == "conforms"
    assert rec["exit"] == 0
    diagnostics = rec.get("diagnostics", [])
    assert any(d.get("rule") == "check.source-offset-stale" for d in diagnostics)
    rule_spec = check_engine.rule_spec("check.source-offset-stale")
    assert rule_spec.severity == "info"


def test_l_cli_agent_subprocess_clean_reports_clean_exit_zero(
    temp_repo: Path, tmp_path: Path
) -> None:
    """(l) A clean fixture through the same `--agent` command exits 0 with no diagnostic."""
    target = temp_repo / "target.py"
    target.write_text("# 1\n# 2\n# 3\n# 4\n# 5\n", encoding="utf-8")

    citing = temp_repo / "citing.py"
    citing.write_text("# cites target.py:2\n", encoding="utf-8")

    checkout_root = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env["PYTHONPATH"] = str(checkout_root)
    env["AW_NO_REEXEC"] = "1"
    home_dir = tmp_path / "home"
    config_dir = home_dir / ".config"
    config_dir.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(home_dir)
    env["XDG_CONFIG_HOME"] = str(config_dir)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "check",
            "--source-offsets",
            "--agent",
            "--dir",
            str(temp_repo),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0
    assert "Traceback" not in proc.stderr
    assert proc.stderr.strip() == ""

    records = [
        json.loads(line) for line in proc.stdout.strip().splitlines() if line.strip()
    ]
    assert len(records) >= 1
    rec = records[0]
    assert rec["outcome"] == "clean"
    assert rec["exit"] == 0
    assert not rec.get("diagnostics")
