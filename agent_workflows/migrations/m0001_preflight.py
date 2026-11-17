"""Step-1 preflight checks and apply-time integration lock for m0001 metadata-v2.

Implements spec 4sd62s Section 5.2 step 1:
1. WORKTREE: refuse linked git worktrees unless ``force_worktree=True`` (never overridden
   by ``--force``), and refuse unconditionally when git common dir cannot be established.
2. UNCOMMITTED: refuse uncommitted changes under ``records_root`` unless ``force=True``.
3. LOCK: refuse when the repository integration lock is held or unprobeable unless
   ``force=True``.
4. LANES: refuse when any linked worktree has unmerged or uncommitted changes under the
   plans tree (preserving ``None`` lane landing as ``"unknown"``) unless ``force=True``.
"""

from __future__ import annotations

import contextlib
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union

from agent_workflows import (
    ipd_lifecycle,
    layout_migration,
    platform_lock,
    project_context,
    runner_shared,
)

logger = logging.getLogger(__name__)

_CONSEQUENCE_WORKTREE = (
    "Running inside a linked git worktree overrides the worktree safety gate; "
    "the linked lane may lack the main checkout's local state and sidecar."
)
_CONSEQUENCE_UNCOMMITTED = (
    "Uncommitted changes in .aw/records/: the migration rewrites those files, "
    "so the uncommitted edits are mixed into the migration commit or lost."
)
_CONSEQUENCE_LOCK = (
    "A live run holds the integration lock: the migration cannot acquire the lock, "
    "so it runs and commits without holding it, and it can race a driver that publishes to main."
)
_CONSEQUENCE_LANES = (
    "A lane has unmerged plan changes: when that lane merges later, git reports a conflict "
    "on each file that the migration also rewrote, and a person must resolve it."
)


def _run_git(cwd: Path, args: Sequence[str]) -> Tuple[int, str, str]:
    """Run git in ``cwd`` and return ``(returncode, stdout, stderr)`` without raising."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except OSError as exc:
        return 127, "", str(exc)


def _is_within(child: Path, parent: Path) -> bool:
    """Return True if ``child`` equals ``parent`` or sits beneath it."""
    c_res = child.resolve()
    p_res = parent.resolve()
    return c_res == p_res or p_res in c_res.parents


def _parse_worktree_list_porcelain(stdout: str) -> List[Dict[str, Any]]:
    """Parse ``git worktree list --porcelain`` into per-worktree dictionaries."""
    entries: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {}
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                entries.append(current)
                current = {}
            continue
        if line.startswith("worktree "):
            current["worktree"] = line[len("worktree ") :].strip()
        elif line.startswith("HEAD "):
            current["head"] = line[len("HEAD ") :].strip()
        elif line.startswith("branch "):
            current["branch"] = line[len("branch ") :].strip()
        elif line == "detached":
            current["detached"] = True
        elif line == "bare":
            current["bare"] = True
        elif line == "prunable" or line.startswith("prunable "):
            current["prunable"] = True
    if current:
        entries.append(current)
    return entries


def _check_worktree(
    repo_path: Path,
    *,
    force_worktree: bool,
    failures: List[str],
    overridden: List[Dict[str, str]],
    warnings: List[str],
) -> Tuple[Optional[Path], bool]:
    """Evaluate step-1 condition (1) WORKTREE; return ``(common_dir, worktree_overridden)``."""
    common_dir = ipd_lifecycle.checkout_git_common_dir(repo_path)
    rc_gd, out_gd, _err_gd = _run_git(
        repo_path, ["rev-parse", "--path-format=absolute", "--git-dir"]
    )
    if common_dir is None or rc_gd != 0 or not out_gd.strip():
        failures.append(
            "WORKTREE: cannot establish the common directory for this git checkout."
        )
        return None, False

    git_dir = Path(out_gd.strip()).resolve()
    common_resolved = common_dir.resolve()
    if git_dir == common_resolved:
        return common_resolved, False

    detail = f"Running inside a linked git worktree ({git_dir} != {common_resolved})"
    if force_worktree:
        overridden.append(
            {
                "condition": "WORKTREE",
                "detail": detail,
                "consequence": _CONSEQUENCE_WORKTREE,
            }
        )
        warnings.append(
            f"WORKTREE override (--force-worktree): {detail}. {_CONSEQUENCE_WORKTREE}"
        )
        return common_resolved, True

    failures.append(
        f"WORKTREE: {detail}; pass --force-worktree to override "
        "(--force does not override the worktree refusal)."
    )
    return common_resolved, False


def _check_uncommitted_records(
    repo_path: Path,
    records_root: Path,
    *,
    common_dir: Optional[Path],
    force: bool,
    failures: List[str],
    overridden: List[Dict[str, str]],
    warnings: List[str],
) -> None:
    """Evaluate step-1 condition (2) UNCOMMITTED against ``records_root``."""
    status_out = ""
    if _is_within(records_root, repo_path):
        if common_dir is not None:
            rel = records_root.resolve().relative_to(repo_path.resolve())
            pathspec = "." if rel == Path(".") else rel.as_posix()
            rc, out, _ = _run_git(repo_path, ["status", "--porcelain", "--", pathspec])
            if rc == 0:
                status_out = out.strip()
    else:
        rec_git_root = project_context.record_git_root(records_root)
        if rec_git_root is not None:
            rec_res = records_root.resolve()
            root_res = rec_git_root.resolve()
            if (rec_res / ".git").exists() or root_res == rec_res:
                rc, out, _ = _run_git(rec_res, ["status", "--porcelain"])
            else:
                rel = rec_res.relative_to(root_res)
                pathspec = "." if rel == Path(".") else rel.as_posix()
                rc, out, _ = _run_git(
                    root_res, ["status", "--porcelain", "--", pathspec]
                )
            if rc == 0:
                status_out = out.strip()

    if not status_out:
        return

    detail = f"Uncommitted changes under {records_root}: {status_out}"
    if force:
        overridden.append(
            {
                "condition": "UNCOMMITTED",
                "detail": detail,
                "consequence": _CONSEQUENCE_UNCOMMITTED,
            }
        )
        warnings.append(
            f"UNCOMMITTED override (--force): {detail}. {_CONSEQUENCE_UNCOMMITTED}"
        )
    else:
        failures.append(
            f"UNCOMMITTED: {detail}; commit or discard them, or pass --force. "
            f"Consequence if forced: {_CONSEQUENCE_UNCOMMITTED}"
        )


def _check_integration_lock(
    repo_path: Path,
    *,
    force: bool,
    failures: List[str],
    overridden: List[Dict[str, str]],
    warnings: List[str],
) -> bool:
    """Evaluate step-1 condition (3) LOCK; return ``lock_overridden``."""
    lock_path = runner_shared.integration_lock_path(repo_path)
    probe = platform_lock.probe_free(lock_path)
    if probe is True:
        return False

    if probe is False:
        holder = runner_shared.read_integration_lock_holder(repo_path)
        detail = f"Integration lock at {lock_path} is held by a live run" + (
            f" ({holder})" if holder else ""
        )
    else:
        detail = (
            f"Integration lock probe at {lock_path} returned unanswerable (None); "
            "lock state cannot be verified"
        )

    if force:
        overridden.append(
            {
                "condition": "LOCK",
                "detail": detail,
                "consequence": _CONSEQUENCE_LOCK,
            }
        )
        warnings.append(f"LOCK override (--force): {detail}. {_CONSEQUENCE_LOCK}")
        return True

    failures.append(
        f"LOCK: {detail}; wait for the active run or pass --force. "
        f"Consequence if forced: {_CONSEQUENCE_LOCK}"
    )
    return False


def _plans_pathspecs(repo_path: Path, records_root: Path) -> List[str]:
    """Return repo-relative pathspecs for plans trees checked across linked worktrees."""
    pathspecs: List[str] = []
    if _is_within(records_root, repo_path):
        rel = (records_root.resolve() / "plans").relative_to(repo_path.resolve())
        pathspecs.append(rel.as_posix())
    else:
        pathspecs.append(".aw/records/plans")
    if (repo_path / ".agents" / "plans").is_dir() and ".agents/plans" not in pathspecs:
        pathspecs.append(".agents/plans")
    return pathspecs


def _check_linked_lanes(
    repo_path: Path,
    records_root: Path,
    *,
    common_dir: Optional[Path],
    force: bool,
    failures: List[str],
    overridden: List[Dict[str, str]],
    warnings: List[str],
) -> int:
    """Evaluate step-1 condition (4) LANES; return count of linked worktrees checked."""
    if common_dir is None:
        return 0

    rc_wt, out_wt, _ = _run_git(repo_path, ["worktree", "list", "--porcelain"])
    if rc_wt != 0:
        return 0

    rc_ch, out_ch, _ = _run_git(
        repo_path,
        [
            f"--git-dir={common_dir}",
            "rev-parse",
            "--verify",
            "--quiet",
            "HEAD^{commit}",
        ],
    )
    common_head = out_ch.strip() if rc_ch == 0 else ""
    pathspecs = _plans_pathspecs(repo_path, records_root)

    checked = 0
    unmerged_lanes: List[str] = []

    for entry in _parse_worktree_list_porcelain(out_wt):
        wt_str = entry.get("worktree")
        if not wt_str or entry.get("bare") or entry.get("prunable"):
            continue
        wt_path = Path(wt_str)
        if not wt_path.is_dir():
            continue

        rc_wgd, out_wgd, _ = _run_git(
            wt_path, ["rev-parse", "--path-format=absolute", "--git-dir"]
        )
        if (
            rc_wgd == 0
            and out_wgd.strip()
            and Path(out_wgd.strip()).resolve() == common_dir
        ):
            continue

        checked += 1
        raw_branch = entry.get("branch") or ""
        if entry.get("detached"):
            branch_short = ""
        elif raw_branch.startswith("refs/heads/"):
            branch_short = raw_branch[len("refs/heads/") :]
        else:
            branch_short = raw_branch

        wt_ref = raw_branch or (entry.get("head") or "")
        diff_touches = False
        if common_head and wt_ref:
            rc_df, out_df, _ = _run_git(
                repo_path,
                ["diff", "--name-only", f"{common_head}...{wt_ref}", "--", *pathspecs],
            )
            diff_touches = rc_df == 0 and bool(out_df.strip())

        rc_ws, out_ws, _ = _run_git(
            wt_path, ["status", "--porcelain", "--", *pathspecs]
        )
        status_touches = rc_ws == 0 and bool(out_ws.strip())

        if not diff_touches and not status_touches:
            continue

        landed = runner_shared.lane_work_has_landed(repo_path, branch_short)
        # Uncommitted changes in a linked lane are never landed even if the branch tip is.
        if (diff_touches and landed is not True) or status_touches:
            landed_str = (
                "unknown" if landed is None else ("true" if landed else "false")
            )
            branch_label = branch_short or "detached"
            dirty_note = ", uncommitted" if status_touches else ""
            unmerged_lanes.append(
                f"{wt_path} (branch={branch_label}, landed={landed_str}{dirty_note})"
            )

    if unmerged_lanes:
        detail = "; ".join(unmerged_lanes)
        if force:
            overridden.append(
                {
                    "condition": "LANES",
                    "detail": detail,
                    "consequence": _CONSEQUENCE_LANES,
                }
            )
            warnings.append(f"LANES override (--force): {detail}. {_CONSEQUENCE_LANES}")
        else:
            failures.append(
                f"LANES: linked worktree(s) have unmerged plan changes: {detail}; "
                f"merge or remove them, or pass --force. Consequence if forced: {_CONSEQUENCE_LANES}"
            )

    return checked


def check_preflight(
    repo: Union[str, Path],
    *,
    records_root: Optional[Union[str, Path]] = None,
    force: bool = False,
    force_worktree: bool = False,
    skip_uncommitted: bool = False,
) -> Dict[str, Any]:
    """Run spec 4sd62s 5.2 step-1 preflight checks on ``repo`` without writing to disk.

    Raises :class:`agent_workflows.layout_migration.PreflightGateError` on any
    unoverridden condition, naming every failed condition.
    """
    repo_path = Path(repo)
    resolved_records = (
        Path(records_root)
        if records_root is not None
        else project_context.project_records_dir(repo_path)
    )

    failures: List[str] = []
    overridden: List[Dict[str, str]] = []
    warnings: List[str] = []

    common_dir, worktree_overridden = _check_worktree(
        repo_path,
        force_worktree=force_worktree,
        failures=failures,
        overridden=overridden,
        warnings=warnings,
    )
    if not skip_uncommitted:
        _check_uncommitted_records(
            repo_path,
            resolved_records,
            common_dir=common_dir,
            force=force,
            failures=failures,
            overridden=overridden,
            warnings=warnings,
        )
    lock_overridden = _check_integration_lock(
        repo_path,
        force=force,
        failures=failures,
        overridden=overridden,
        warnings=warnings,
    )
    linked_checked = _check_linked_lanes(
        repo_path,
        resolved_records,
        common_dir=common_dir,
        force=force,
        failures=failures,
        overridden=overridden,
        warnings=warnings,
    )

    if failures:
        raise layout_migration.PreflightGateError(
            "m0001 preflight refused:\n- " + "\n- ".join(failures)
        )

    return {
        "ok": True,
        "repo": str(repo_path),
        "records_root": str(resolved_records),
        "worktree_overridden": worktree_overridden,
        "lock_overridden": lock_overridden,
        "overridden": overridden,
        "warnings": warnings,
        "checked": ["WORKTREE", "UNCOMMITTED", "LOCK", "LANES"],
        "linked_worktrees_checked": linked_checked,
    }


@contextlib.contextmanager
def acquire_apply_integration_lock(
    repo: Union[str, Path],
    *,
    apply: bool = True,
    lock_overridden: bool = False,
    force: bool = False,
    timeout: Optional[float] = None,
) -> Iterator[Optional[runner_shared.IntegrationLockOutcome]]:
    """Hold ``integration.lock`` during ``apply=True`` unless dry-run or overridden."""
    if not apply:
        yield None
        return

    if lock_overridden:
        logger.warning(
            "LOCK override (--force): skipping integration.lock acquisition; %s",
            _CONSEQUENCE_LOCK,
        )
        yield None
        return

    with runner_shared.integration_lock(
        Path(repo),
        holder_label="aw migrate metadata",
        timeout=timeout,
    ) as outcome:
        if not outcome.acquired:
            if force:
                logger.warning(
                    "LOCK override (--force): integration lock acquisition timed out (%s); %s",
                    outcome.detail,
                    _CONSEQUENCE_LOCK,
                )
                yield outcome
                return
            raise layout_migration.PreflightGateError(
                f"LOCK: failed to acquire integration lock for apply: {outcome.detail}"
            )
        yield outcome
