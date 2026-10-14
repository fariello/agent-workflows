"""Periodic health checkup (CI status and slow checks) runner and record store.

cihealth Order 02 (n7xlhm) E-01 / E-02 / E-03 / E-04 / E-05.

Periodically reads GitHub Actions CI status (read-only, via gh) and runs local slow checks
(stale spec line-anchor citations), writing an atomic record to `.aw/state/checkup/last.json`
under the primary checkout. Surfaceable by `aw checkup`, run start banners, run end summaries,
`aw attention`, and `aw doctor`.
"""

from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Any, Callable, Dict, NamedTuple, Optional, Tuple

from agent_workflows import config
from agent_workflows import platform_lock


# --------------------------------------------------------------------------------------
# Paths and Record Storage (E-01)
# --------------------------------------------------------------------------------------

CHECKUP_STATE_REL = Path(".aw") / "state" / "checkup"
CHECKUP_RECORD_FILENAME = "last.json"
CHECKUP_LOCK_FILENAME = "lock"


def checkup_dir(repo_root: Path | str) -> Path:
    """Return the checkup state directory under the primary checkout."""
    from agent_workflows.runner_shared import runs_repo_root

    primary = runs_repo_root(Path(repo_root))
    return primary / CHECKUP_STATE_REL


def checkup_record_path(repo_root: Path | str) -> Path:
    """Return the path to `.aw/state/checkup/last.json` for repo_root."""
    return checkup_dir(repo_root) / CHECKUP_RECORD_FILENAME


def checkup_lock_path(repo_root: Path | str) -> Path:
    """Return the path to `.aw/state/checkup/lock` for repo_root."""
    return checkup_dir(repo_root) / CHECKUP_LOCK_FILENAME


def write_checkup_record(repo_root: Path | str, record: Dict[str, Any]) -> Path:
    """Atomically write a checkup record under the primary checkout's checkup directory."""
    target_dir = checkup_dir(repo_root)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / CHECKUP_RECORD_FILENAME

    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(target_dir), prefix="last_", suffix=".tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2)
            handle.write("\n")
        os.replace(tmp_path, target_file)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    return target_file


def save_checkup_record(
    repo_root_or_record: Any,
    record_or_repo_root: Any,
) -> Path:
    """Save checkup record accepting either (repo_root, record) or (record, repo_root)."""
    if isinstance(repo_root_or_record, dict):
        return write_checkup_record(record_or_repo_root, repo_root_or_record)
    return write_checkup_record(repo_root_or_record, record_or_repo_root)


def read_checkup_record(repo_root: Path | str) -> Optional[Dict[str, Any]]:
    """Read `.aw/state/checkup/last.json` if it exists, or return None."""
    rec_path = checkup_record_path(repo_root)
    if not rec_path.is_file():
        return None
    try:
        return json.loads(rec_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


# --------------------------------------------------------------------------------------
# CI Reader (E-02)
# --------------------------------------------------------------------------------------


class CiHealth:
    PASSING = "PASSING"
    FAILING = "FAILING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CIRunResult:
    """Typed result of a CI status inspection."""

    status: str  # "PASSING" | "FAILING" | "UNKNOWN"
    conclusion: Optional[str] = None
    latest_commit: Optional[str] = None
    latest_run_created_at: Optional[str] = None
    last_passing_commit: Optional[str] = None
    last_passing_created_at: Optional[str] = None
    commits_since_last_pass: Optional[int] = None
    reason: Optional[str] = None

    @property
    def health(self) -> str:
        return self.status

    @property
    def latest_run_commit(self) -> Optional[str]:
        return self.latest_commit

    @property
    def last_pass_commit(self) -> Optional[str]:
        return self.last_passing_commit

    @property
    def commits_since_pass(self) -> Optional[int]:
        return self.commits_since_last_pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "health": self.status,
            "conclusion": self.conclusion,
            "latest_commit": self.latest_commit,
            "latest_run_created_at": self.latest_run_created_at,
            "last_passing_commit": self.last_passing_commit,
            "last_passing_created_at": self.last_passing_created_at,
            "commits_since_last_pass": self.commits_since_last_pass,
            "reason": self.reason,
        }


def _count_commits_since(
    repo_root: Path | str, sha: Optional[str], branch: str
) -> Optional[int]:
    """Count first-parent commits from sha to branch in repo_root."""
    if not sha:
        return None
    try:
        anc_res = subprocess.run(
            ["git", "merge-base", "--is-ancestor", sha, branch],
            cwd=str(repo_root),
            capture_output=True,
            timeout=10.0,
        )
        if anc_res.returncode != 0:
            return None

        proc = subprocess.run(
            ["git", "rev-list", "--count", "--first-parent", f"{sha}..{branch}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=10.0,
        )
        if proc.returncode == 0:
            return int(proc.stdout.strip())
        return None
    except Exception:
        return None


def count_first_parent_commits(
    sha: Optional[str], branch: str, repo_root: Path | str
) -> Optional[int]:
    """Count first-parent commits from sha to branch in repo_root."""
    return _count_commits_since(repo_root, sha, branch)


def read_ci_status(
    repo_root: Path | str,
    *,
    workflow: Optional[str] = None,
    branch: Optional[str] = None,
    limit: int = 30,
    widened_limit: int = 100,
    timeout: float = 15.0,
    timeout_sec: Optional[float] = None,
) -> CIRunResult:
    """Read CI's result via gh run list, finding newest run and last success."""
    if timeout_sec is not None:
        timeout = timeout_sec
    root = Path(repo_root)
    wf = workflow or config.ci_checkup_workflow(root)
    br = branch or config.ci_checkup_branch(root)

    cmd = [
        "gh",
        "run",
        "list",
        "--workflow",
        wf,
        "--branch",
        br,
        "--json",
        "headSha,conclusion,status,createdAt",
        "--limit",
        str(limit),
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return CIRunResult(status="UNKNOWN", reason="gh: command not found")
    except subprocess.TimeoutExpired:
        return CIRunResult(status="UNKNOWN", reason=f"gh: timed out after {timeout}s")
    except Exception as exc:
        return CIRunResult(status="UNKNOWN", reason=f"gh error: {exc}")

    if proc.returncode != 0:
        err = proc.stderr.strip()
        if "not logged in" in err.lower():
            return CIRunResult(status="UNKNOWN", reason="gh: not logged in")
        return CIRunResult(
            status="UNKNOWN",
            reason=f"gh exited {proc.returncode}: {err or 'unknown error'}",
        )

    try:
        runs = json.loads(proc.stdout)
    except Exception:
        return CIRunResult(status="UNKNOWN", reason="gh: malformed JSON output")

    if not isinstance(runs, list):
        return CIRunResult(status="UNKNOWN", reason="gh: output is not a JSON list")

    if not runs:
        return CIRunResult(
            status="UNKNOWN",
            reason=f"no runs found for workflow {wf} on branch {br}",
        )

    completed = [
        r for r in runs if isinstance(r, dict) and r.get("status") == "completed"
    ]
    if not completed:
        return CIRunResult(
            status="UNKNOWN",
            reason=f"no completed runs found for workflow {wf} on branch {br}",
        )

    latest = completed[0]
    latest_conclusion = latest.get("conclusion")
    latest_sha = latest.get("headSha")
    latest_time = latest.get("createdAt")

    if latest_conclusion == "success":
        commits_ago = _count_commits_since(root, latest_sha, br)
        if commits_ago is None:
            return CIRunResult(
                status="UNKNOWN",
                conclusion="success",
                latest_commit=latest_sha,
                latest_run_created_at=latest_time,
                last_passing_commit=latest_sha,
                last_passing_created_at=latest_time,
                reason=f"commit {latest_sha[:10] if latest_sha else '?'} not in local history",
            )
        return CIRunResult(
            status="PASSING",
            conclusion="success",
            latest_commit=latest_sha,
            latest_run_created_at=latest_time,
            last_passing_commit=latest_sha,
            last_passing_created_at=latest_time,
            commits_since_last_pass=commits_ago,
        )

    # Latest completed run is not success
    passing_runs = [r for r in completed if r.get("conclusion") == "success"]
    if not passing_runs and limit < widened_limit:
        # Widen limit once
        widen_cmd = [
            "gh",
            "run",
            "list",
            "--workflow",
            wf,
            "--branch",
            br,
            "--json",
            "headSha,conclusion,status,createdAt",
            "--limit",
            str(widened_limit),
        ]
        try:
            w_proc = subprocess.run(
                widen_cmd,
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if w_proc.returncode == 0:
                w_runs = json.loads(w_proc.stdout)
                if isinstance(w_runs, list):
                    w_completed = [
                        r
                        for r in w_runs
                        if isinstance(r, dict) and r.get("status") == "completed"
                    ]
                    passing_runs = [
                        r for r in w_completed if r.get("conclusion") == "success"
                    ]
        except Exception:
            pass

    if not passing_runs:
        return CIRunResult(
            status="UNKNOWN",
            conclusion=latest_conclusion,
            latest_commit=latest_sha,
            latest_run_created_at=latest_time,
            reason=f"no passing run in the last {widened_limit} runs",
        )

    passing_run = passing_runs[0]
    pass_sha = passing_run.get("headSha")
    pass_time = passing_run.get("createdAt")
    commits_since = _count_commits_since(root, pass_sha, br)

    if commits_since is None:
        return CIRunResult(
            status="UNKNOWN",
            conclusion=latest_conclusion,
            latest_commit=latest_sha,
            latest_run_created_at=latest_time,
            last_passing_commit=pass_sha,
            last_passing_created_at=pass_time,
            reason=f"commit {pass_sha[:10] if pass_sha else '?'} not in local history",
        )

    return CIRunResult(
        status="FAILING",
        conclusion=latest_conclusion,
        latest_commit=latest_sha,
        latest_run_created_at=latest_time,
        last_passing_commit=pass_sha,
        last_passing_created_at=pass_time,
        commits_since_last_pass=commits_since,
    )


# --------------------------------------------------------------------------------------
# Slow Checks & Assembly (E-03)
# --------------------------------------------------------------------------------------


def _run_spec_anchor_stale(repo_root: Path) -> int:
    """Run stale spec line anchor detection and return count of findings."""
    from agent_workflows import spec_citations

    scan_paths = spec_citations.default_scan_roots(repo_root)
    findings = spec_citations.stale_spec_anchors(repo_root, scan_paths)
    return len(findings)


class SlowCheck(NamedTuple):
    name: str
    runner: Callable[[Path], int]


SLOW_CHECKS: Tuple[SlowCheck, ...] = (
    SlowCheck("check.spec-anchor-stale", _run_spec_anchor_stale),
)


@dataclass(frozen=True)
class SlowChecksResult:
    """Result of running the slow checks tuple."""

    status: str  # "PASSING" | "FAILING" | "UNKNOWN"
    finding_counts: Dict[str, int] = field(default_factory=dict)
    total_findings: int = 0
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "finding_counts": self.finding_counts,
            "total_findings": self.total_findings,
            "reason": self.reason,
        }


def run_slow_checks(
    repo_root: Path | str, *, timeout: float = 30.0
) -> SlowChecksResult:
    """Run registered slow checks within a total bounded time."""
    root = Path(repo_root)
    finding_counts: Dict[str, int] = {}
    total = 0
    start = time.monotonic()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        for check in SLOW_CHECKS:
            elapsed = time.monotonic() - start
            rem = max(0.1, timeout - elapsed)
            future = executor.submit(check.runner, root)
            try:
                cnt = future.result(timeout=rem)
                finding_counts[check.name] = cnt
                total += cnt
            except concurrent.futures.TimeoutError:
                return SlowChecksResult(
                    status="UNKNOWN",
                    finding_counts=finding_counts,
                    total_findings=total,
                    reason=f"slow check {check.name} timed out after {timeout}s",
                )
            except Exception as exc:
                return SlowChecksResult(
                    status="UNKNOWN",
                    finding_counts=finding_counts,
                    total_findings=total,
                    reason=f"slow check {check.name} failed: {exc}",
                )

    status = "PASSING" if total == 0 else "FAILING"
    return SlowChecksResult(
        status=status,
        finding_counts=finding_counts,
        total_findings=total,
    )


def perform_checkup(
    repo_root: Path | str,
    *,
    workflow: Optional[str] = None,
    branch: Optional[str] = None,
    limit: int = 30,
    widened_limit: int = 100,
    gh_timeout: float = 15.0,
    slow_check_timeout: float = 30.0,
) -> Dict[str, Any]:
    """Execute CI read and slow checks, and atomically persist the record."""
    root = Path(repo_root)
    br = branch or config.ci_checkup_branch(root)

    # Determine current commit for branch
    commit = ""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", br],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        if proc.returncode == 0:
            commit = proc.stdout.strip()
        else:
            proc_head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=5.0,
            )
            if proc_head.returncode == 0:
                commit = proc_head.stdout.strip()
    except Exception:
        pass

    ci_res = read_ci_status(
        root,
        workflow=workflow,
        branch=br,
        limit=limit,
        widened_limit=widened_limit,
        timeout=gh_timeout,
    )

    slow_res = run_slow_checks(root, timeout=slow_check_timeout)

    record = {
        "schema_version": 1,
        "commit": commit,
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ci": ci_res.to_dict(),
        "slow_checks": slow_res.to_dict(),
    }

    write_checkup_record(root, record)
    return record


# --------------------------------------------------------------------------------------
# Display & Line Formatting (E-05)
# --------------------------------------------------------------------------------------


def format_checkup_line(
    record: Optional[Dict[str, Any]],
    repo_root: Optional[Path | str] = None,
) -> str:
    """Format one human-readable line representing the checkup record."""
    if record is None:
        return "No checkup yet: run `aw checkup`"

    commits_ago_str = ""
    rec_commit = record.get("commit")
    if rec_commit and repo_root:
        br = config.ci_checkup_branch(repo_root)
        c_ago = _count_commits_since(repo_root, rec_commit, br)
        if c_ago is not None:
            commits_ago_str = f" {c_ago} commits ago"

    ci = record.get("ci", {})
    ci_status = ci.get("status") or ci.get("health") or "UNKNOWN"
    if ci_status == "PASSING":
        ci_str = "CI PASSING"
    elif ci_status == "FAILING":
        last_time = ci.get("last_passing_created_at") or ci.get("last_pass_date")
        date_str = last_time[:10] if last_time else ""
        c_since = (
            ci.get("commits_since_last_pass")
            if ci.get("commits_since_last_pass") is not None
            else ci.get("commits_since_pass")
        )
        if date_str and c_since is not None:
            ci_str = f"CI FAILING since {date_str} ({c_since:,} commits)"
        elif c_since is not None:
            ci_str = f"CI FAILING ({c_since:,} commits)"
        else:
            reason = ci.get("reason")
            ci_str = f"CI FAILING ({reason})" if reason else "CI FAILING"
    else:
        reason = ci.get("reason", "unknown")
        ci_str = f"CI UNKNOWN ({reason})"

    slow = record.get("slow_checks", {})
    if "finding_counts" in slow:
        stale_count = slow.get("finding_counts", {}).get("check.spec-anchor-stale", 0)
    else:
        stale_count = slow.get(
            "check.spec-anchor-stale", slow.get("stale_spec_anchors", 0)
        )
    slow_str = f"spec pointers: {stale_count} stale"

    return f"Checkup{commits_ago_str}: {ci_str}; {slow_str}"


def is_checkup_warning(
    record: Optional[Dict[str, Any]],
    repo_root: Path | str,
) -> bool:
    """Return True if CI last pass is more than interval commits ago."""
    if record is None:
        return False
    interval = config.ci_checkup_interval_commits(repo_root)
    ci = record.get("ci", {})
    c_since = (
        ci.get("commits_since_last_pass")
        if ci.get("commits_since_last_pass") is not None
        else ci.get("commits_since_pass")
    )
    if c_since is not None and c_since > interval:
        return True
    ci_status = ci.get("status") or ci.get("health")
    if ci_status == "FAILING" and c_since is None:
        return True
    return False


# --------------------------------------------------------------------------------------
# Run-Start Trigger & Lock Coordination (E-04)
# --------------------------------------------------------------------------------------


def _is_checkup_due(repo: Path, branch: str, interval: int) -> bool:
    """Check if main has advanced at least interval commits or record is stale/absent."""
    if interval == 0:
        return False
    rec = read_checkup_record(repo)
    if rec is None:
        return True
    rec_commit = rec.get("commit")
    if not rec_commit:
        return True

    # Check ancestry
    anc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", rec_commit, branch],
        cwd=str(repo),
        capture_output=True,
    )
    if anc.returncode != 0:
        return True

    count = _count_commits_since(repo, rec_commit, branch)
    if count is None:
        return True
    return count >= interval


def is_checkup_due(
    repo_root: Path | str,
    interval: Optional[int] = None,
    branch: Optional[str] = None,
) -> bool:
    """Check if checkup is due based on interval and git history."""
    root = Path(repo_root)
    iv = interval if interval is not None else config.ci_checkup_interval_commits(root)
    br = branch or config.ci_checkup_branch(root)
    return _is_checkup_due(root, br, iv)


def run_start_checkup(
    repo: Optional[Path | str] = None,
    run_dir: Optional[Path | str] = None,
    *,
    repo_root: Optional[Path | str] = None,
    events_path: Optional[Path] = None,
    run_id: Optional[str] = None,
    config: Optional[dict] = None,
) -> Optional[str]:
    """Coordinate checkup at run start across parallel runs via exclusive non-blocking lock.

    Emits exactly one event to events.jsonl:
      - checkup-performed
      - checkup-not-due
      - checkup-skipped-peer
      - checkup-failed
    Returns the checkup line to display, or None if skipped/not due.
    """
    from agent_workflows.runner_shared import append_jsonl, utc_now

    repo_arg = repo if repo is not None else repo_root
    if repo_arg is None:
        repo_arg = Path.cwd()
    repo_path = Path(repo_arg)

    if events_path is not None:
        ev_path = Path(events_path)
    elif run_dir is not None:
        ev_path = Path(run_dir) / "events.jsonl"
    elif run_id is not None:
        from agent_workflows.runner_shared import runs_repo_root

        ev_path = runs_repo_root(repo_path) / ".aw" / "runs" / run_id / "events.jsonl"
    else:
        ev_path = repo_path / "events.jsonl"

    run_id_val = run_id or (Path(run_dir).name if run_dir else "run-unknown")

    if config and "ci_checkup_interval_commits" in config:
        interval = config["ci_checkup_interval_commits"]
    else:
        from agent_workflows import config as aw_config

        interval = aw_config.ci_checkup_interval_commits(repo_path)

    if interval == 0:
        append_jsonl(
            ev_path,
            {
                "at": utc_now(),
                "event": "checkup-not-due",
                "run_id": run_id_val,
                "reason": "disabled",
            },
        )
        return None

    if config and "ci_checkup_branch" in config:
        branch = config["ci_checkup_branch"]
    else:
        from agent_workflows import config as aw_config

        branch = aw_config.ci_checkup_branch(repo_path)

    try:
        due = _is_checkup_due(repo_path, branch, interval)
    except Exception as exc:
        append_jsonl(
            ev_path,
            {
                "at": utc_now(),
                "event": "checkup-failed",
                "run_id": run_id_val,
                "reason": str(exc),
            },
        )
        return None

    if not due:
        append_jsonl(
            ev_path,
            {
                "at": utc_now(),
                "event": "checkup-not-due",
                "run_id": run_id_val,
            },
        )
        rec = read_checkup_record(repo_path)
        return format_checkup_line(rec, repo_root=repo_path)

    lock_file = checkup_lock_path(repo_path)
    lock_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        handle = platform_lock.acquire(lock_file)
    except platform_lock.LockBusy:
        append_jsonl(
            ev_path,
            {
                "at": utc_now(),
                "event": "checkup-skipped-peer",
                "run_id": run_id_val,
            },
        )
        rec = read_checkup_record(repo_path)
        return format_checkup_line(rec, repo_root=repo_path)
    except Exception as exc:
        append_jsonl(
            ev_path,
            {
                "at": utc_now(),
                "event": "checkup-failed",
                "run_id": run_id_val,
                "reason": str(exc),
            },
        )
        return None

    with handle:
        # Re-check due inside lock (peer may have just finished)
        try:
            still_due = _is_checkup_due(repo_path, branch, interval)
        except Exception:
            still_due = True

        if not still_due:
            append_jsonl(
                ev_path,
                {
                    "at": utc_now(),
                    "event": "checkup-not-due",
                    "run_id": run_id_val,
                },
            )
            rec = read_checkup_record(repo_path)
            return format_checkup_line(rec, repo_root=repo_path)

        try:
            rec = perform_checkup(repo_path, branch=branch)
            append_jsonl(
                ev_path,
                {
                    "at": utc_now(),
                    "event": "checkup-performed",
                    "run_id": run_id_val,
                    "result": rec,
                },
            )
            return format_checkup_line(rec, repo_root=repo_path)
        except Exception as exc:
            append_jsonl(
                ev_path,
                {
                    "at": utc_now(),
                    "event": "checkup-failed",
                    "run_id": run_id_val,
                    "reason": str(exc),
                },
            )
            return None


# --------------------------------------------------------------------------------------
# CLI Entrypoint (E-03)
# --------------------------------------------------------------------------------------


def run_checkup_cli(
    args: Any,
    term: Optional[Any] = None,
    context: Optional[Any] = None,
) -> int:
    """CLI handler for `aw checkup`."""
    from agent_workflows import project_context
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Evidence,
        select_output,
    )
    import agent_workflows.term as T

    explicit_dir = getattr(args, "dir", None)
    repo_root = project_context.resolve_verb_repo_root(explicit_dir)

    ctx = context or select_output(args)
    term_obj = term or T.Term(stream=ctx.stdout, color=ctx.color)

    rec = perform_checkup(repo_root)
    line = format_checkup_line(rec, repo_root=repo_root)
    ci_status = rec.get("ci", {}).get("status", "UNKNOWN")
    slow_status = rec.get("slow_checks", {}).get("status", "UNKNOWN")
    clean = ci_status == "PASSING" and slow_status == "PASSING"
    status_str = "clean" if clean else "ok"

    if (
        ctx.is_agent
        or ctx.is_json
        or getattr(args, "agent", False)
        or getattr(args, "json", False)
    ):
        evidence = [
            Evidence(
                key="ci",
                value=rec.get("ci", {}),
                status="clean" if ci_status == "PASSING" else "findings",
            ),
            Evidence(
                key="slow_checks",
                value=rec.get("slow_checks", {}),
                status="clean" if slow_status == "PASSING" else "findings",
            ),
        ]
        res = CommandResult(
            command="checkup",
            status=status_str,
            exit_code=0,
            summary=line,
            evidence=evidence,
            data={"record": rec, "record_path": str(checkup_record_path(repo_root))},
            complete=True,
        )
        return get_renderer(ctx).emit(res, ctx)

    # Human output
    label = "ok" if clean else "warn"
    term_obj.status(label, line)
    ci = rec.get("ci", {})
    print(f"  CI Status: {ci.get('status', 'UNKNOWN')}")
    if ci.get("latest_commit"):
        print(
            f"  Latest completed: {ci.get('conclusion')} (commit {ci.get('latest_commit')[:11]})"
        )
    if ci.get("last_passing_commit"):
        c_since = ci.get("commits_since_last_pass")
        c_str = f", {c_since:,} commits ago" if c_since is not None else ""
        print(f"  Last passing: commit {ci.get('last_passing_commit')[:11]}{c_str}")
    if ci.get("reason"):
        print(f"  CI Note: {ci.get('reason')}")

    slow = rec.get("slow_checks", {})
    print("  Slow checks:")
    for rule, count in slow.get("finding_counts", {}).items():
        print(f"    - {rule}: {count} finding(s)")
    if slow.get("reason"):
        print(f"    Note: {slow.get('reason')}")

    rel_record = checkup_record_path(repo_root)
    try:
        from agent_workflows.runner_shared import runs_repo_root

        rel_record = rel_record.relative_to(runs_repo_root(repo_root))
    except Exception:
        pass
    print(f"  Saved record: {rel_record}")
    return 0
