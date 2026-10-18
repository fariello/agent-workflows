#!/usr/bin/env python3
"""Behavioral tests for the red-CI run-start stop and `--allow-red-ci` override (`s4z5n8`).

Drives the real runner entry points (`oc_runipd.main`, `agy_runipd.main`, `cli.main`) with a
scripted host executable and pre-written checkup records, asserting on exit codes, stdout/stderr,
durable events, `aw runs` output, and spawned-agent counts.
"""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

from agent_workflows import agy_runipd, checkup, config, oc_runipd, runner_shared


PLAN_TEMPLATE = """# IPD: Test plan {id6}

- Date: 2026-10-12
- Kind: child
- Concern: test concern.
- Scope: test scope.
- Scope-Paths: src/x.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- Set: {setid}
- Order: {order}
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history
- 2026-10-12 to-review (test): ready for review

## Goal
Test goal.

## Detailed Implementation Checklist (TODO)
- [ ] E-01 Do test
  - Depends on: none
  - Expected outcome: done.
  - Execution state: pending

## Project conventions discovered (Step 0)
- None.

## Findings
| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | Test | Evidence |

## Proposed changes (ordered, validatable)
1. Do E-01.

## Deferred / out of scope (with reason)
- None.

## Scope check
- Over-scope: none.
- Under-scope: none.

## Required tests / validation
- None.

## Spec / documentation sync
None.

## Open questions
None.

## Validation and cross-check (verify before reporting done)
- [ ] V-01 validates E-01
  - Required evidence: test output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- Size assessment: standard
- Cohesion rationale: not required
"""


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def _make_fake_host(tmp_path: Path) -> tuple[Path, Path]:
    from tests.support import make_fake_executable

    spawn_log = tmp_path / "spawned_agents.jsonl"
    host_bin = make_fake_executable(
        tmp_path / "fake-host-agent",
        f"""#!/usr/bin/env python3
import json
import sys
from pathlib import Path

log_path = Path({str(spawn_log)!r})
with log_path.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps({{"argv": sys.argv[1:]}}) + "\\n")
print(json.dumps({{"type": "session", "sessionID": "ses-scripted-1", "session_id": "ses-scripted-1"}}))
sys.exit(0)
""",
    )
    return host_bin, spawn_log


def _spawn_count(spawn_log: Path) -> int:
    if not spawn_log.is_file():
        return 0
    return len(
        [
            line
            for line in spawn_log.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    )


def _write_plan(
    repo: Path, *, id6: str = "tst001", setid: str = "other", order: int = 1
) -> Path:
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True, exist_ok=True)
    plan_path = pending / f"20261012-{setid}-{order:02d}-{id6}-test.ipd.md"
    plan_path.write_text(
        PLAN_TEMPLATE.format(id6=id6, setid=setid, order=order),
        encoding="utf-8",
    )
    return plan_path


def _setup_repo(
    tmp_path: Path,
    *,
    interval: int = 2,
    exempt_sets: list[str] | None = None,
    plans: list[tuple[str, str, int]] | None = None,
    extra_commits: int = 3,
) -> tuple[Path, str, str, list[str]]:
    """Create a git repo with `1 + extra_commits` commits on `main`.

    Returns `(repo, first_sha, tip_sha, all_shas)`.
    """
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n",
        encoding="utf-8",
    )
    cfg_dir = repo / ".aw" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "project.json").write_text(
        json.dumps(
            {
                "ci_checkup_interval_commits": interval,
                "ci_checkup_branch": "main",
                "ci_red_exempt_sets": (
                    ["cihealth"] if exempt_sets is None else exempt_sets
                ),
            }
        ),
        encoding="utf-8",
    )

    plan_specs = plans or [("tst001", "other", 1)]
    for id6, setid, order in plan_specs:
        _write_plan(repo, id6=id6, setid=setid, order=order)

    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "initial commit")
    first_sha = _git(repo, "rev-parse", "HEAD")
    shas = [first_sha]

    for idx in range(extra_commits):
        (repo / f"commit_{idx}.txt").write_text(f"step {idx}\n", encoding="utf-8")
        _git(repo, "add", f"commit_{idx}.txt")
        _git(repo, "commit", "-qm", f"commit {idx + 1}")
        shas.append(_git(repo, "rev-parse", "HEAD"))

    return repo, first_sha, shas[-1], shas


def _write_checkup_record(
    repo: Path,
    *,
    commit: str,
    status: str = "FAILING",
    last_passing_commit: str | None = None,
    commits_since_last_pass: int | None = 3,
    reason: str | None = None,
) -> dict[str, Any]:
    ci_block: dict[str, Any] = {
        "status": status,
        "health": status,
        "last_passing_commit": last_passing_commit,
        "commits_since_last_pass": commits_since_last_pass,
    }
    if reason is not None:
        ci_block["reason"] = reason
    rec: dict[str, Any] = {
        "schema_version": 1,
        "commit": commit,
        "time": "2026-10-13T12:00:00Z",
        "ci": ci_block,
        "slow_checks": {
            "status": "PASSING",
            "finding_counts": {"check.spec-anchor-stale": 0},
            "total_findings": 0,
        },
    }
    checkup.write_checkup_record(repo, rec)
    return rec


def _run_host_main(
    host_mod: Any,
    argv: list[str],
    *,
    host_bin: Path | None = None,
) -> tuple[int, str, str]:
    full_argv = list(argv)
    if host_bin is not None:
        flag = "--opencode" if host_mod is oc_runipd else "--agy"
        full_argv.extend([flag, str(host_bin)])
    out, err = io.StringIO(), io.StringIO()
    rc = 0
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = host_mod.main(full_argv)
        except SystemExit as exc:
            rc = exc.code if isinstance(exc.code, int) else 2
    return rc, out.getvalue(), err.getvalue()


# --------------------------------------------------------------------------------------
# E-01 / V-01: Config loader and pure predicate
# --------------------------------------------------------------------------------------


def test_ci_red_exempt_sets_config_loader(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parent.parent
    assert config.ci_red_exempt_sets(repo_root) == ["cihealth"]

    # Missing config file -> default []
    empty_repo = tmp_path / "empty"
    empty_repo.mkdir()
    assert config.ci_red_exempt_sets(empty_repo) == []

    # Direct dict validation: missing key -> []
    assert config.ci_red_exempt_sets({}) == []

    # Valid config file and dict
    valid_repo = tmp_path / "valid"
    (valid_repo / ".aw" / "config").mkdir(parents=True)
    (valid_repo / ".aw" / "config" / "project.json").write_text(
        json.dumps({"ci_red_exempt_sets": ["cihealth", "ci-hotfix"]}),
        encoding="utf-8",
    )
    assert config.ci_red_exempt_sets(valid_repo) == ["cihealth", "ci-hotfix"]

    # Malformed values warn and fall back to []
    for bad_val in ("cihealth", 42, True, ["cihealth", ""], ["cihealth", 99]):
        warnings: list[str] = []
        res = config.ci_red_exempt_sets(
            {"ci_red_exempt_sets": bad_val},
            warn=warnings.append,
        )
        assert res == []
        assert len(warnings) == 1
        assert "ci_red_exempt_sets" in warnings[0]


def test_pure_decide_red_ci_gate_verdicts() -> None:
    q_normal = [{"id6": "tst001", "setid": "other"}]
    q_exempt = [{"id6": "s4z5n8", "setid": "cihealth"}]
    q_mixed = [
        {"id6": "s4z5n8", "setid": "cihealth"},
        {"id6": "tst001", "setid": "other"},
    ]
    rec_red = {
        "ci": {
            "status": "FAILING",
            "last_passing_commit": "abc1234",
            "commits_since_last_pass": 105,
        }
    }
    rec_within = {
        "ci": {
            "status": "FAILING",
            "last_passing_commit": "abc1234",
            "commits_since_last_pass": 80,
        }
    }
    rec_passing = {
        "ci": {
            "status": "PASSING",
            "last_passing_commit": "abc1234",
            "commits_since_last_pass": 0,
        }
    }
    rec_unknown = {
        "ci": {
            "status": "UNKNOWN",
            "reason": "gh not found",
        }
    }

    # (a) red beyond N -> ALLOW-WITH-WARNING (proceeds with warning, does not refuse)
    d_red = runner_shared.decide_red_ci_gate(
        rec_red, interval=100, exempt_sets=["cihealth"], queue=q_normal
    )
    assert d_red.verdict == runner_shared.RED_CI_ALLOW_WITH_WARNING
    assert d_red.proceed
    assert "abc1234" in d_red.message
    assert "105" in d_red.message
    assert "[RUN-RED-CI]" in d_red.message

    # (b) red beyond N with override -> ALLOW-WITH-WARNING
    d_override = runner_shared.decide_red_ci_gate(
        rec_red,
        interval=100,
        exempt_sets=["cihealth"],
        queue=q_normal,
        allow_red_ci="fixing X",
    )
    assert d_override.verdict == runner_shared.RED_CI_ALLOW_WITH_WARNING
    assert d_override.proceed
    assert d_override.override == "fixing X"
    assert "fixing X" in d_override.message

    # (d) all items in exempt set -> ALLOW
    d_exempt = runner_shared.decide_red_ci_gate(
        rec_red, interval=100, exempt_sets=["cihealth"], queue=q_exempt
    )
    assert d_exempt.verdict == runner_shared.RED_CI_ALLOW
    assert d_exempt.proceed
    assert d_exempt.exempt is True

    # (d2) mixed queue -> ALLOW-WITH-WARNING
    d_mixed = runner_shared.decide_red_ci_gate(
        rec_red, interval=100, exempt_sets=["cihealth"], queue=q_mixed
    )
    assert d_mixed.verdict == runner_shared.RED_CI_ALLOW_WITH_WARNING
    assert d_mixed.proceed
    assert "[RUN-RED-CI]" in d_mixed.message

    # (e) missing record and UNKNOWN status -> ALLOW-WITH-WARNING
    d_missing = runner_shared.decide_red_ci_gate(
        None, interval=100, exempt_sets=["cihealth"], queue=q_normal
    )
    assert d_missing.verdict == runner_shared.RED_CI_ALLOW_WITH_WARNING
    assert d_missing.proceed

    d_unknown = runner_shared.decide_red_ci_gate(
        rec_unknown, interval=100, exempt_sets=["cihealth"], queue=q_normal
    )
    assert d_unknown.verdict == runner_shared.RED_CI_ALLOW_WITH_WARNING
    assert d_unknown.proceed

    # (f) interval 0 -> ALLOW silently
    d_zero = runner_shared.decide_red_ci_gate(
        rec_red, interval=0, exempt_sets=["cihealth"], queue=q_normal
    )
    assert d_zero.verdict == runner_shared.RED_CI_ALLOW
    assert d_zero.message == ""

    # (g) red within N and PASSING within N -> ALLOW
    d_within = runner_shared.decide_red_ci_gate(
        rec_within, interval=100, exempt_sets=["cihealth"], queue=q_normal
    )
    assert d_within.verdict == runner_shared.RED_CI_ALLOW
    assert d_within.proceed

    d_pass = runner_shared.decide_red_ci_gate(
        rec_passing, interval=100, exempt_sets=["cihealth"], queue=q_normal
    )
    assert d_pass.verdict == runner_shared.RED_CI_ALLOW
    assert d_pass.proceed

    # (g2) stale record with caller-recounted commits_since_last_pass > N -> ALLOW-WITH-WARNING
    d_recounted = runner_shared.decide_red_ci_gate(
        rec_within,
        interval=100,
        exempt_sets=["cihealth"],
        queue=q_normal,
        commits_since_last_pass=105,
    )
    assert d_recounted.verdict == runner_shared.RED_CI_ALLOW_WITH_WARNING
    assert d_recounted.proceed
    assert d_recounted.commits_since_last_pass == 105


# --------------------------------------------------------------------------------------
# E-03 (a) & (a2): Red beyond N refuses (normal and --prepare-only), readable in aw runs
# --------------------------------------------------------------------------------------


def test_case_a_and_a2_red_beyond_n_warns_at_start_and_end_and_runs(
    tmp_path: Path,
) -> None:
    host_bin, spawn_log = _make_fake_host(tmp_path)
    repo, first_sha, tip_sha, _ = _setup_repo(tmp_path, interval=2, extra_commits=3)
    pass_short = first_sha[:7]
    _write_checkup_record(
        repo,
        commit=tip_sha,
        status="FAILING",
        last_passing_commit=pass_short,
        commits_since_last_pass=3,
    )

    # (a) Normal start does NOT refuse: runs to completion, spawns agent, warns at start and end
    rc, out, err = _run_host_main(
        oc_runipd,
        [
            "tst001",
            "--repo",
            str(repo),
            "--unattended",
            "--no-isolate-worktree",
            "--retry-budget",
            "0",
            "--run-id",
            "run-warned-a",
        ],
        host_bin=host_bin,
    )
    assert rc != 2
    assert _spawn_count(spawn_log) >= 1
    assert pass_short in err
    assert "3 commit(s)" in err
    assert "[RUN-RED-CI]" in err
    # Verify warning appears at start and again at the end (at least 2 occurrences)
    assert err.count("[RUN-RED-CI]") >= 2
    assert err.count("=" * 80) >= 4

    run_dir = repo / ".aw" / "records" / "runs" / "run-warned-a"
    events = [
        json.loads(line)
        for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    gate_events = [e for e in events if e.get("event") == "red-ci-warning"]
    assert len(gate_events) == 1
    assert gate_events[0]["proceed"] is True
    assert gate_events[0]["last_passing_commit"] == pass_short

    # (a2) --prepare-only also proceeds without refusing, printing warning at start and end
    count_before_prep = _spawn_count(spawn_log)
    rc_prep, _out_prep, err_prep = _run_host_main(
        oc_runipd,
        [
            "tst001",
            "--repo",
            str(repo),
            "--unattended",
            "--prepare-only",
            "--run-id",
            "run-warned-prep",
        ],
        host_bin=host_bin,
    )
    assert rc_prep == 0
    assert _spawn_count(spawn_log) == count_before_prep  # prepare-only spawns no agent
    assert pass_short in err_prep
    assert err_prep.count("[RUN-RED-CI]") >= 2


# --------------------------------------------------------------------------------------
# E-03 (b): Override with --allow-red-ci runs and records reason in events and summary
# --------------------------------------------------------------------------------------


def test_case_b_override_runs_and_records_reason_in_events_and_summary(
    tmp_path: Path,
) -> None:
    host_bin, spawn_log = _make_fake_host(tmp_path)
    repo, first_sha, tip_sha, _ = _setup_repo(tmp_path, interval=2, extra_commits=3)
    pass_short = first_sha[:7]
    _write_checkup_record(
        repo,
        commit=tip_sha,
        status="FAILING",
        last_passing_commit=pass_short,
        commits_since_last_pass=3,
    )

    rc, out, err = _run_host_main(
        oc_runipd,
        [
            "tst001",
            "--repo",
            str(repo),
            "--unattended",
            "--no-isolate-worktree",
            "--retry-budget",
            "0",
            "--allow-red-ci",
            "fixing X",
            "--run-id",
            "run-override-b",
        ],
        host_bin=host_bin,
    )
    assert _spawn_count(spawn_log) >= 1
    assert "fixing X" in out
    assert "fixing X" in err

    run_dir = repo / ".aw" / "records" / "runs" / "run-override-b"
    events = [
        json.loads(line)
        for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    override_events = [e for e in events if e.get("event") == "red-ci-override"]
    assert len(override_events) == 1
    assert override_events[0]["reason"] == "fixing X"
    assert override_events[0]["last_passing_commit"] == pass_short
    assert override_events[0]["commits_since_last_pass"] == 3

    report_text = (run_dir / "execution-report.md").read_text(encoding="utf-8")
    assert "Red-CI override: fixing X" in report_text


# --------------------------------------------------------------------------------------
# E-03 (c) & E-05: Empty reason refused by parser, and --allow-red-ci on resume refused
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("host_mod", [oc_runipd, agy_runipd])
def test_case_c_empty_reason_and_resume_refused(tmp_path: Path, host_mod: Any) -> None:
    repo, first_sha, tip_sha, _ = _setup_repo(tmp_path / host_mod.__name__, interval=5)
    _write_checkup_record(
        repo,
        commit=tip_sha,
        status="PASSING",
        last_passing_commit=tip_sha[:7],
        commits_since_last_pass=0,
    )

    # Empty or whitespace-only justification refused by parser
    for empty_val in ("", "   "):
        rc_empty, _out_e, err_e = _run_host_main(
            host_mod,
            [
                "tst001",
                "--repo",
                str(repo),
                "--allow-red-ci",
                empty_val,
            ],
        )
        assert rc_empty != 0
        assert "--allow-red-ci" in err_e

    # Prepare a valid run, then verify `resume --allow-red-ci` is refused
    rc_prep, _out_p, _err_p = _run_host_main(
        host_mod,
        [
            "tst001",
            "--repo",
            str(repo),
            "--unattended",
            "--prepare-only",
            "--run-id",
            "run-for-resume",
        ],
    )
    assert rc_prep == 0

    rc_res, _out_r, err_r = _run_host_main(
        host_mod,
        [
            "resume",
            "run-for-resume",
            "--repo",
            str(repo),
            "--allow-red-ci",
            "late override",
        ],
    )
    assert rc_res == 2
    assert "--allow-red-ci" in err_r
    assert "resume" in err_r.lower()


# --------------------------------------------------------------------------------------
# E-03 (d): Exempt set runs without flag; mixed queue is refused
# --------------------------------------------------------------------------------------


def test_case_d_exempt_set_runs_and_mixed_queue_refused(tmp_path: Path) -> None:
    host_bin, spawn_log = _make_fake_host(tmp_path)
    repo, first_sha, tip_sha, _ = _setup_repo(
        tmp_path,
        interval=2,
        exempt_sets=["cihealth"],
        plans=[
            ("cih001", "cihealth", 1),
            ("oth001", "other", 1),
        ],
        extra_commits=3,
    )
    _write_checkup_record(
        repo,
        commit=tip_sha,
        status="FAILING",
        last_passing_commit=first_sha[:7],
        commits_since_last_pass=3,
    )

    # Mixed queue (`all` selects both `cihealth` and `other`) -> warns and runs
    rc_mixed, _out_m, err_m = _run_host_main(
        oc_runipd,
        [
            "all",
            "--repo",
            str(repo),
            "--unattended",
            "--no-isolate-worktree",
            "--retry-budget",
            "0",
            "--run-id",
            "run-mixed",
        ],
        host_bin=host_bin,
    )
    assert rc_mixed != 2
    assert _spawn_count(spawn_log) >= 1
    assert "[RUN-RED-CI]" in err_m

    # Exempt-only selection (`cihealth`) -> allowed with no flag, agent spawned
    rc_exempt, _out_ex, _err_ex = _run_host_main(
        oc_runipd,
        [
            "cihealth",
            "--repo",
            str(repo),
            "--unattended",
            "--no-isolate-worktree",
            "--retry-budget",
            "0",
            "--run-id",
            "run-exempt",
        ],
        host_bin=host_bin,
    )
    assert _spawn_count(spawn_log) >= 1


# --------------------------------------------------------------------------------------
# E-03 (e): Unknown state and missing record run with a warning
# --------------------------------------------------------------------------------------


def test_case_e_unknown_state_and_missing_record_run_with_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    host_bin, spawn_log = _make_fake_host(tmp_path)
    repo, _first_sha, tip_sha, _ = _setup_repo(tmp_path, interval=2, extra_commits=3)

    # 1. Explicit UNKNOWN checkup record at tip -> warns and runs
    _write_checkup_record(
        repo,
        commit=tip_sha,
        status="UNKNOWN",
        last_passing_commit=None,
        commits_since_last_pass=None,
        reason="gh not authenticated",
    )
    _rc1, _out1, err1 = _run_host_main(
        oc_runipd,
        [
            "tst001",
            "--repo",
            str(repo),
            "--unattended",
            "--no-isolate-worktree",
            "--retry-budget",
            "0",
            "--run-id",
            "run-unknown-rec",
        ],
        host_bin=host_bin,
    )
    count_after_1 = _spawn_count(spawn_log)
    assert count_after_1 >= 1
    assert "WARNING: red-CI gate" in err1
    assert "UNKNOWN" in err1

    # 2. Missing checkup record (when checkup step produces no record) -> warns and runs
    (repo / ".aw" / "state" / "checkup" / "last.json").unlink()
    monkeypatch.setattr(checkup, "run_start_checkup", lambda *a, **k: None)
    _rc2, _out2, err2 = _run_host_main(
        oc_runipd,
        [
            "tst001",
            "--repo",
            str(repo),
            "--unattended",
            "--no-isolate-worktree",
            "--retry-budget",
            "0",
            "--run-id",
            "run-missing-rec",
        ],
        host_bin=host_bin,
    )
    assert _spawn_count(spawn_log) > count_after_1
    assert "WARNING: red-CI gate" in err2


# --------------------------------------------------------------------------------------
# E-03 (f): Interval 0 runs silently
# --------------------------------------------------------------------------------------


def test_case_f_interval_zero_runs_silently(tmp_path: Path) -> None:
    host_bin, spawn_log = _make_fake_host(tmp_path)
    repo, first_sha, tip_sha, _ = _setup_repo(tmp_path, interval=0, extra_commits=3)
    _write_checkup_record(
        repo,
        commit=tip_sha,
        status="FAILING",
        last_passing_commit=first_sha[:7],
        commits_since_last_pass=3,
    )

    _rc, _out, err = _run_host_main(
        oc_runipd,
        [
            "tst001",
            "--repo",
            str(repo),
            "--unattended",
            "--no-isolate-worktree",
            "--retry-budget",
            "0",
            "--run-id",
            "run-interval-zero",
        ],
        host_bin=host_bin,
    )
    assert _spawn_count(spawn_log) >= 1
    assert "red-CI gate" not in err


# --------------------------------------------------------------------------------------
# E-03 (g) & (g2): Red within N runs; stale record whose recount crosses N is refused
# --------------------------------------------------------------------------------------


def test_case_g_and_g2_within_n_runs_and_stale_record_crossing_n_refused(
    tmp_path: Path,
) -> None:
    host_bin, spawn_log = _make_fake_host(tmp_path)
    # 7 commits total: shas[0]..shas[6], interval = 4
    repo, first_sha, tip_sha, shas = _setup_repo(tmp_path, interval=4, extra_commits=6)

    # (g) Record at tip with commits_since_last_pass == 3 <= 4 -> runs
    _write_checkup_record(
        repo,
        commit=tip_sha,
        status="FAILING",
        last_passing_commit=shas[3],
        commits_since_last_pass=3,
    )
    _rc_g, _out_g, _err_g = _run_host_main(
        oc_runipd,
        [
            "tst001",
            "--repo",
            str(repo),
            "--unattended",
            "--no-isolate-worktree",
            "--retry-budget",
            "0",
            "--run-id",
            "run-within-n",
        ],
        host_bin=host_bin,
    )
    count_after_g = _spawn_count(spawn_log)
    assert count_after_g >= 1

    # (g2) Stale record written at shas[4] (only 2 commits behind tip shas[6], so checkup is not due)
    # where last_passing_commit is shas[1] (3 commits behind shas[4], recorded as 3 <= 4,
    # but 5 commits behind current tip shas[6], which crosses interval=4!) -> REFUSED
    _write_checkup_record(
        repo,
        commit=shas[4],
        status="FAILING",
        last_passing_commit=shas[1],
        commits_since_last_pass=3,
    )
    rc_g2, _out_g2, err_g2 = _run_host_main(
        oc_runipd,
        [
            "tst001",
            "--repo",
            str(repo),
            "--unattended",
            "--no-isolate-worktree",
            "--retry-budget",
            "0",
            "--run-id",
            "run-stale-crossed",
        ],
        host_bin=host_bin,
    )
    assert rc_g2 != 2
    assert _spawn_count(spawn_log) > count_after_g
    assert "5 commit(s)" in err_g2
    assert shas[1][:7] in err_g2
    assert "[RUN-RED-CI]" in err_g2


# --------------------------------------------------------------------------------------
# E-03 (h) & (i): Both hosts behave the same for (a), (b), --agent, and --full-auto
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("host_mod", [oc_runipd, agy_runipd])
def test_case_h_and_i_both_hosts_parity_agent_mode_and_full_auto_non_override(
    tmp_path: Path, host_mod: Any
) -> None:
    sub_tmp = tmp_path / host_mod.__name__
    sub_tmp.mkdir(parents=True, exist_ok=True)
    host_bin, spawn_log = _make_fake_host(sub_tmp)
    repo, first_sha, tip_sha, _ = _setup_repo(sub_tmp, interval=2, extra_commits=3)
    pass_short = first_sha[:7]
    _write_checkup_record(
        repo,
        commit=tip_sha,
        status="FAILING",
        last_passing_commit=pass_short,
        commits_since_last_pass=3,
    )

    # (i) --full-auto warns at start and end and runs on either host
    rc_fa, _out_fa, err_fa = _run_host_main(
        host_mod,
        [
            "tst001",
            "--repo",
            str(repo),
            "--unattended",
            "--no-isolate-worktree",
            "--retry-budget",
            "0",
            "--full-auto",
            "--run-id",
            "run-full-auto-warned",
        ],
        host_bin=host_bin,
    )
    assert rc_fa != 2
    assert _spawn_count(spawn_log) >= 1
    assert "[RUN-RED-CI]" in err_fa

    # (h) --agent runs and emits aw.agent/v1 JSON record with red_ci_warning
    rc_ag_ref, out_ag_ref, _err_ag_ref = _run_host_main(
        host_mod,
        [
            "tst001",
            "--repo",
            str(repo),
            "--unattended",
            "--prepare-only",
            "--agent",
            "--run-id",
            "run-agent-prepared",
        ],
        host_bin=host_bin,
    )
    assert rc_ag_ref == 0
    rec_ref = json.loads(out_ag_ref.strip())
    assert rec_ref["schema"] == "aw.agent/v1"
    assert rec_ref["outcome"] == "ok"
    assert "red_ci_warning" in rec_ref
    assert pass_short in rec_ref["red_ci_warning"]
    assert "3 commit(s)" in rec_ref["red_ci_warning"]

    # (h) --agent with --allow-red-ci override runs and emits aw.agent/v1 record carrying override
    _rc_ag_ov, out_ag_ov, _err_ag_ov = _run_host_main(
        host_mod,
        [
            "tst001",
            "--repo",
            str(repo),
            "--unattended",
            "--no-isolate-worktree",
            "--retry-budget",
            "0",
            "--allow-red-ci",
            "fixing X",
            "--agent",
            "--run-id",
            "run-agent-override",
        ],
        host_bin=host_bin,
    )
    assert _spawn_count(spawn_log) >= 1
    rec_ov = json.loads(out_ag_ov.strip())
    assert rec_ov["schema"] == "aw.agent/v1"
    assert rec_ov["red_ci_override"]["reason"] == "fixing X"
    assert rec_ov["red_ci_override"]["last_passing_commit"] == pass_short


def test_red_ci_warning_banner_formatting_and_colors() -> None:
    msg = (
        "WARNING: [RUN-RED-CI] CI has not passed in 618 commit(s) "
        "(threshold: 100; CI status: FAILING; last passing commit: 3a8d2b2)."
    )

    # 1. Plain formatting (color=False)
    plain_lines = runner_shared.format_red_ci_warning_banner(msg, color=False)
    assert len(plain_lines) == 3
    assert plain_lines[0] == "=" * 80
    assert plain_lines[1] == msg
    assert plain_lines[2] == "=" * 80
    assert "\033[" not in "".join(plain_lines)

    # 2. Bold red formatting (color=True)
    styled_lines = runner_shared.format_red_ci_warning_banner(msg, color=True)
    assert len(styled_lines) == 3
    for line in styled_lines:
        assert line.startswith("\033[1;31m")
        assert line.endswith("\033[0m")
    assert msg in styled_lines[1]


@pytest.mark.parametrize("host_mod", [oc_runipd, agy_runipd])
def test_red_ci_warning_banner_printed_at_start_and_end_both_hosts(
    tmp_path: Path, host_mod: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    sub_tmp = tmp_path / host_mod.__name__
    sub_tmp.mkdir(parents=True, exist_ok=True)
    host_bin, spawn_log = _make_fake_host(sub_tmp)
    repo, first_sha, tip_sha, _ = _setup_repo(sub_tmp, interval=2, extra_commits=3)
    pass_short = first_sha[:7]
    _write_checkup_record(
        repo,
        commit=tip_sha,
        status="FAILING",
        last_passing_commit=pass_short,
        commits_since_last_pass=3,
    )

    monkeypatch.setenv("FORCE_COLOR", "1")
    _rc, _out, err = _run_host_main(
        host_mod,
        [
            "tst001",
            "--repo",
            str(repo),
            "--unattended",
            "--no-isolate-worktree",
            "--retry-budget",
            "0",
            "--run-id",
            "run-color-warn",
        ],
        host_bin=host_bin,
    )

    assert _spawn_count(spawn_log) >= 1
    # Check warning banner at start and end
    assert err.count("[RUN-RED-CI]") >= 2
    # Check bold red ANSI escape is present in the output
    assert "\033[1;31m" in err
    assert "=" * 80 in err
