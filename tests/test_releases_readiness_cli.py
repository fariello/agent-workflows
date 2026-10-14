"""End-to-end behavioral tests for ``aw releases readiness`` (IPD wa64wz E-06).

Every arm drives the command or gate over synthetic temp trees and asserts on
observable outputs, exit codes, and filesystem state (no source reading, P16).
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import pytest

from agent_workflows import agent_schema, cli
from agent_workflows import release_readiness as rr
from tests.test_release_readiness_producers import _setup_full_go_tree

REPO_ROOT = Path(__file__).resolve().parent.parent


def _build_subprocess_go_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build a synthetic tree where every gate (including subprocess gates) can pass."""
    tree = tmp_path / "repo"
    tree.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    _setup_full_go_tree(tree)
    subprocess.run(
        ["git", "init", "-q"],
        cwd=tree,
        stdin=subprocess.DEVNULL,
        check=True,
        capture_output=True,
    )
    (tree / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    return tree


def _run_subprocess(
    argv: Sequence[str], *, cwd: Path
) -> subprocess.CompletedProcess[str]:
    """Run ``python3 -m agent_workflows <argv>`` with PYTHONPATH pinned to REPO_ROOT."""
    env = dict(os.environ)
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{REPO_ROOT}:{existing_pp}" if existing_pp else str(REPO_ROOT)
    env["GIT_CEILING_DIRECTORIES"] = str(cwd.parent)
    env["NO_COLOR"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "agent_workflows", *argv],
        cwd=str(cwd),
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_inproc(argv: List[str]) -> Tuple[int, str, str]:
    """Drive ``cli.main(argv)`` in-process, capturing (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = cli.main(argv)
    return rc, out.getvalue(), err.getvalue()


def _snapshot_tree(root: Path) -> Dict[str, str]:
    """Return a SHA-1 digest map of every file under ``root`` (including ``.git/``)."""
    snap: Dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            snap[rel] = hashlib.sha1(p.read_bytes()).hexdigest()
    return snap


def test_arm_a_go_tree_exits_0_and_renders_go_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (a): --suite-passed --residual-risk-signer qa on the GO tree exits 0 with Verdict: GO."""
    tree = _build_subprocess_go_tree(tmp_path, monkeypatch)
    proc = _run_subprocess(
        [
            "releases",
            "readiness",
            "--suite-passed",
            "--residual-risk-signer",
            "qa",
        ],
        cwd=tree,
    )
    assert proc.returncode == 0, f"stderr={proc.stderr!r}\nstdout={proc.stdout!r}"
    assert "Verdict: GO" in proc.stdout
    assert proc.stderr == ""


def test_arm_b_no_suite_flag_reports_not_supplied_and_emits_stderr_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (b): no suite flag exits 1, full_suite reads not supplied (not RED), hint on stderr only."""
    tree = _build_subprocess_go_tree(tmp_path, monkeypatch)
    rc, out, err = _run_inproc(
        [
            "releases",
            "readiness",
            "--dir",
            str(tree),
            "--residual-risk-signer",
            "qa",
        ]
    )
    assert rc == 1
    assert "| full_suite | FAIL | full suite result not supplied |" in out
    assert "full suite RED" not in out
    assert "Hint:" not in out
    assert "--suite-passed" not in out
    assert "--suite-passed" in err
    assert "--suite-failed" in err
    assert "--residual-risk-signer" in err


def test_arm_c_suite_failed_exits_1_with_full_suite_red(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (c): --suite-failed exits 1 with full suite RED and no attestation hint."""
    tree = _build_subprocess_go_tree(tmp_path, monkeypatch)
    rc, out, err = _run_inproc(
        [
            "releases",
            "readiness",
            "--dir",
            str(tree),
            "--suite-failed",
            "--residual-risk-signer",
            "qa",
        ]
    )
    assert rc == 1
    assert "| full_suite | FAIL | full suite RED |" in out
    assert "Failing gates: full_suite" in out
    assert err == ""


def test_arm_d_missing_signer_exits_1_with_residual_risk_failing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (d): no signer exits 1 with residual_risk failing and hint on stderr."""
    tree = _build_subprocess_go_tree(tmp_path, monkeypatch)
    rc, out, err = _run_inproc(
        [
            "releases",
            "readiness",
            "--dir",
            str(tree),
            "--suite-passed",
        ]
    )
    assert rc == 1
    assert "| residual_risk | FAIL | residual-risk sign-off missing |" in out
    assert "Failing gates: residual_risk" in out
    assert "--residual-risk-signer" in err


def test_arm_e_unproven_host_matrix_claim_fails_capability_freshness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (e): adding one supported: true to host_matrix.json exits 1 with capability_freshness."""
    tree = _build_subprocess_go_tree(tmp_path, monkeypatch)
    matrix_path = (
        tree
        / ".aw"
        / "system"
        / "workflows"
        / "conformance"
        / "tools"
        / "host_matrix.json"
    )
    matrix_path.write_text(
        json.dumps({"hosts": {"test_host": {"feat_x": {"supported": True}}}}),
        encoding="utf-8",
    )
    rc, out, err = _run_inproc(
        [
            "releases",
            "readiness",
            "--dir",
            str(tree),
            "--suite-passed",
            "--residual-risk-signer",
            "qa",
            "--json",
        ]
    )
    assert rc == 1
    payload = json.loads(out)
    assert "capability_freshness" in payload["data"]["failing_gates"]
    assert err == ""


def test_arm_f_agent_mode_emits_schema_valid_record_with_exit_and_diagnostic_parity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (f): --agent emits a schema-valid aw.agent/v1 record with exit parity and diagnostics."""
    tree = _build_subprocess_go_tree(tmp_path, monkeypatch)
    proc_nogo = _run_subprocess(
        ["releases", "readiness", "--agent"],
        cwd=tree,
    )
    assert proc_nogo.returncode == 1
    lines = [ln for ln in proc_nogo.stdout.splitlines() if ln.strip()]
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert agent_schema.validate_agent_record(rec) == []
    assert rec["cmd"] == "releases readiness"
    assert rec["exit"] == proc_nogo.returncode == 1
    assert rec["outcome"] == "findings"
    assert rec["findings"] == 2
    assert len(rec["diagnostics"]) == 2
    rules = {d["rule"] for d in rec["diagnostics"]}
    assert rules == {"readiness.full_suite", "readiness.residual_risk"}

    proc_go = _run_subprocess(
        [
            "releases",
            "readiness",
            "--suite-passed",
            "--residual-risk-signer",
            "qa",
            "--agent",
        ],
        cwd=tree,
    )
    assert proc_go.returncode == 0
    rec_go = json.loads(proc_go.stdout.strip())
    assert agent_schema.validate_agent_record(rec_go) == []
    assert rec_go["cmd"] == "releases readiness"
    assert rec_go["exit"] == proc_go.returncode == 0
    assert rec_go["outcome"] == "clean"
    assert rec_go["findings"] == 0


def test_arm_g_json_output_verdict_matches_exit_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (g): --json output is valid JSON and data.verdict matches the exit code."""
    tree = _build_subprocess_go_tree(tmp_path, monkeypatch)
    rc_go, out_go, _ = _run_inproc(
        [
            "releases",
            "readiness",
            "--dir",
            str(tree),
            "--suite-passed",
            "--residual-risk-signer",
            "qa",
            "--json",
        ]
    )
    assert rc_go == 0
    doc_go = json.loads(out_go)
    assert doc_go["exit_code"] == 0
    assert doc_go["data"]["verdict"] == "GO"

    rc_nogo, out_nogo, _ = _run_inproc(
        [
            "releases",
            "readiness",
            "--dir",
            str(tree),
            "--json",
        ]
    )
    assert rc_nogo == 1
    doc_nogo = json.loads(out_nogo)
    assert doc_nogo["exit_code"] == 1
    assert doc_nogo["data"]["verdict"] == "NO-GO"


def test_arm_h_non_project_dir_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (h): --dir pointing at a non-project directory exits 2."""
    non_proj = tmp_path / "empty_non_project"
    non_proj.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    proc = _run_subprocess(
        ["releases", "readiness", "--dir", str(non_proj)],
        cwd=non_proj,
    )
    assert proc.returncode == 2
    assert proc.stderr.strip() != ""


def test_arm_i_release_alias_is_byte_identical_under_agent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (i): aw release readiness (alias) gives byte-identical --agent output to aw releases readiness."""
    tree = _build_subprocess_go_tree(tmp_path, monkeypatch)
    rc_plural, out_plural, err_plural = _run_inproc(
        ["releases", "readiness", "--dir", str(tree), "--agent"]
    )
    rc_singular, out_singular, err_singular = _run_inproc(
        ["release", "readiness", "--dir", str(tree), "--agent"]
    )
    assert rc_plural == rc_singular == 1
    assert out_plural == out_singular
    assert err_plural == err_singular == ""


def test_arm_j_tree_is_byte_identical_before_and_after_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (j): every file under the tree (including .git/) is byte-identical before and after."""
    tree = _build_subprocess_go_tree(tmp_path, monkeypatch)
    before = _snapshot_tree(tree)
    rc, out, _ = _run_inproc(
        [
            "releases",
            "readiness",
            "--dir",
            str(tree),
            "--suite-passed",
            "--residual-risk-signer",
            "qa",
        ]
    )
    assert rc == 0
    assert "Verdict: GO" in out
    after = _snapshot_tree(tree)
    assert after == before


def test_arm_k_dir_flag_resolves_identically_before_or_after_subcommand(
    tmp_path: Path,
) -> None:
    """Arm (k): aw releases --dir <tree> readiness and aw releases readiness --dir <tree> resolve same dir."""
    parser = cli._build_parser()
    ns_before = parser.parse_args(["releases", "--dir", str(tmp_path), "readiness"])
    ns_after = parser.parse_args(["releases", "readiness", "--dir", str(tmp_path)])
    assert ns_before.dir == ns_after.dir == str(tmp_path)


def test_arm_l_gate_full_suite_none_returns_not_supplied() -> None:
    """Arm (l): gate_full_suite(None) directly returns passed=False, not supplied detail, supplied=False."""
    res = rr.gate_full_suite(None)
    assert res.name == "full_suite"
    assert res.passed is False
    assert res.detail == "full suite result not supplied"
    assert res.evidence.get("supplied") is False
