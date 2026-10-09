"""CLI interface for managing worker and review sweep lanes (aw lanes list/prune).

lanegc Order 01 (45z93e) E-03, E-04, E-07.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from agent_workflows import lane_containment, run_viewer, runner_shared, worktree_lease
from agent_workflows.term import strip_ansi


def _run_git(cwd: Path, args: Sequence[str]) -> tuple[int, str, str]:
    """Run a git command and return (rc, stdout, stderr)."""
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _repo_rel(repo: Path, path: Path | str | None) -> str:
    """Return path relative to repo root, avoiding absolute paths."""
    if not path or str(path).strip() in ("", "-"):
        return "-"
    try:
        p = Path(path).resolve()
        r = repo.resolve()
        return str(p.relative_to(r))
    except Exception:
        s = str(path)
        # Avoid leaking /home/ in any case
        if "/.aw/" in s:
            idx = s.find(".aw/")
            return s[idx:]
        return s


@dataclass(frozen=True)
class ResolvedLane:
    """A lane resolved to its owning run record and queue item (E-07)."""

    run_dir: Path
    state: dict[str, Any]
    lane_record: dict[str, Any]
    item: dict[str, Any] | None
    is_sweep: bool
    review_items: list[dict[str, Any]] | None


def resolve_lane_to_run(
    repo: Path, branch: str, worktree: Path | str | None = None
) -> ResolvedLane | None:
    """Resolve a lane to the run record and queue item that own it (E-07).

    Discovers run directories with run_viewer.discover_run_dirs, loads each state.json,
    enumerates lanes with runner_shared.lane_records_including_sweep, matches on (branch, worktree),
    and returns the run directory plus owning item (or review items for a sweep lane).
    Returns None when no run record matches. Malformed state.json files are skipped.
    """
    try:
        run_dirs = run_viewer.discover_run_dirs(repo)
    except Exception:
        return None

    # Sort descending so newer runs match first
    run_dirs_sorted = sorted(run_dirs, reverse=True)

    norm_branch = branch.removeprefix("refs/heads/")

    for run_dir in run_dirs_sorted:
        state_file = run_dir / "state.json"
        if not state_file.is_file():
            continue
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            if not isinstance(state, dict):
                continue
        except Exception:
            # Skip malformed state.json, never guess
            continue

        lanes = runner_shared.lane_records_including_sweep(state)
        for lane_rec in lanes:
            if not isinstance(lane_rec, dict):
                continue
            rec_br = str(lane_rec.get("branch") or "").removeprefix("refs/heads/")
            if rec_br != norm_branch:
                continue

            rec_wt = lane_rec.get("worktree")
            if worktree and rec_wt:
                try:
                    wt1 = Path(worktree).resolve()
                    wt2 = Path(rec_wt).resolve()
                    if wt1 != wt2 and str(worktree).rstrip("/") != str(rec_wt).rstrip(
                        "/"
                    ):
                        continue
                except Exception:
                    if str(worktree).rstrip("/") != str(rec_wt).rstrip("/"):
                        continue

            # Found matching lane
            sweep_rec = runner_shared.review_sweep_lane_record(state)
            is_sweep = bool(
                lane_rec.get("status") == "review-sweep"
                or (
                    sweep_rec
                    and str(sweep_rec.get("branch") or "").removeprefix("refs/heads/")
                    == norm_branch
                )
            )

            if is_sweep:
                review_items = [
                    entry
                    for entry in state.get("queue", [])
                    if isinstance(entry, dict)
                    and (
                        entry.get("action") == "review"
                        or entry.get("review_integrated") is not None
                    )
                ]
                return ResolvedLane(
                    run_dir=run_dir,
                    state=state,
                    lane_record=lane_rec,
                    item=None,
                    is_sweep=True,
                    review_items=review_items,
                )

            item = runner_shared.interrupt_lane_item_record(state, lane_rec)
            return ResolvedLane(
                run_dir=run_dir,
                state=state,
                lane_record=lane_rec,
                item=item,
                is_sweep=False,
                review_items=None,
            )

    return None


@dataclass
class LaneRow:
    """Row representing a lane in aw lanes list / prune."""

    lane: str
    branch: str
    worktree: str
    owner_run_pid: str
    live: str
    commits_not_landed: str
    uncommitted: str
    verdict: str
    raw_lane_id: str | None = None
    raw_worktree: Path | None = None
    resolved: ResolvedLane | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lane": self.lane,
            "branch": self.branch,
            "worktree": self.worktree,
            "owner_run_pid": self.owner_run_pid,
            "live": self.live,
            "commits_not_landed": self.commits_not_landed,
            "uncommitted": self.uncommitted,
            "verdict": self.verdict,
        }


def collect_lane_rows(repo: Path) -> list[LaneRow]:
    """Inspect all lanes and worktrees in repo and return classified rows (E-03)."""
    repo = repo.resolve()

    # 1. Enumerate all aw/lane/* branches
    rc, out, _err = _run_git(
        repo, ["for-each-ref", "--format=%(refname:short)", "refs/heads/aw/lane/"]
    )
    lane_branches = [line.strip() for line in out.splitlines() if line.strip()]

    # 2. Enumerate registered worktrees from git
    rc_wt, out_wt, _ = _run_git(repo, ["worktree", "list", "--porcelain"])
    registered_worktrees: list[dict[str, Any]] = []
    if rc_wt == 0:
        cur: dict[str, Any] = {}
        for line in out_wt.splitlines() + [""]:
            line = line.rstrip("\n")
            if not line:
                if cur.get("path"):
                    registered_worktrees.append(cur)
                cur = {}
                continue
            if line.startswith("worktree "):
                cur["path"] = line[len("worktree ") :]
            elif line.startswith("HEAD "):
                cur["head"] = line[len("HEAD ") :]
            elif line.startswith("branch "):
                cur["branch"] = line[len("branch ") :]
            elif line == "detached":
                cur["detached"] = True

    # Map branch -> worktree entry
    branch_to_wt: dict[str, dict[str, Any]] = {}
    for wt in registered_worktrees:
        br = wt.get("branch")
        if br:
            short_br = br.removeprefix("refs/heads/")
            branch_to_wt[short_br] = wt

    rows: list[LaneRow] = []

    # 3. Process each aw/lane/* branch
    for branch in lane_branches:
        lane_id = worktree_lease.lane_id_from_branch(branch) or branch.removeprefix(
            "aw/lane/"
        )

        # Verify ref readability and that the referenced object exists
        rc_rev, _out_rev, err_rev = _run_git(
            repo, ["rev-parse", "--verify", f"{branch}^{{commit}}"]
        )
        if rc_rev != 0:
            err_msg = (
                err_rev.strip().splitlines()[-1]
                if err_rev.strip()
                else "unknown revision"
            )
            rows.append(
                LaneRow(
                    lane=lane_id,
                    branch=branch,
                    worktree="-",
                    owner_run_pid="-",
                    live="-",
                    commits_not_landed="-",
                    uncommitted="-",
                    verdict=f"broken: {err_msg}",
                    raw_lane_id=lane_id,
                )
            )
            continue

        lane_state = worktree_lease.inspect_lane(repo, lane_id)
        raw_wt = lane_state.worktree_path
        wt_str = _repo_rel(repo, raw_wt)

        owner = worktree_lease.read_lane_owner(repo, lane_id)
        owned_by_other_live = worktree_lease.lane_owned_by_other_live_process(
            repo, lane_id
        )
        owner_is_live = lane_state.owner_live

        resolved = resolve_lane_to_run(repo, branch, raw_wt)

        owner_run = (
            resolved.run_dir.name
            if resolved
            else (str(owner.get("run_id")) if owner and owner.get("run_id") else "-")
        )
        owner_pid = owner.get("pid") if owner else None
        owner_run_pid = f"{owner_run} ({owner_pid})" if owner_pid else owner_run

        if owned_by_other_live:
            if owner_is_live is None:
                live_str = "unknown"
            else:
                live_str = "yes"
        elif owner_is_live is False:
            live_str = "no"
        elif owner is not None and owner_is_live is None:
            live_str = "unknown"
        else:
            live_str = "-" if owner is None else "no"

        # Classification via classify_lane_integration
        lane_dict = {
            "branch": branch,
            "lane_id": lane_id,
            "worktree": str(raw_wt or ""),
        }
        classif = runner_shared.classify_lane_integration(repo, lane_dict)
        is_landed = bool(
            classif.get("state") == runner_shared.LANE_LANDED
            or classif.get("landed") is True
        )
        is_empty = bool(classif.get("state") == runner_shared.LANE_EMPTY_OF_WORK)

        if is_landed or is_empty:
            commits_not_landed = "0"
        else:
            commits_not_landed = str(lane_state.commits_ahead)

        uncommitted = "yes" if lane_state.dirty else "no"

        # Verdict
        if owned_by_other_live:
            if owner_is_live is None:
                verdict = "keep: unknown owner"
            else:
                verdict = "keep: live owner"
        elif owner is not None and owner_is_live is None:
            verdict = "keep: unknown owner"
        elif resolved is None:
            verdict = "keep: no run record"
        elif lane_state.dirty:
            verdict = "keep: uncommitted changes"
        elif not is_landed and not is_empty:
            verdict = "keep: unmerged work"
        else:
            verdict = "removable"

        rows.append(
            LaneRow(
                lane=lane_id,
                branch=branch,
                worktree=wt_str,
                owner_run_pid=owner_run_pid,
                live=live_str,
                commits_not_landed=commits_not_landed,
                uncommitted=uncommitted,
                verdict=verdict,
                raw_lane_id=lane_id,
                raw_worktree=raw_wt,
                resolved=resolved,
            )
        )

    # 4. Check for worktrees under .aw/worktrees/ that are not on an aw/lane/* branch
    wt_base = repo / ".aw" / "worktrees"
    if wt_base.is_dir():
        for entry_dir in wt_base.iterdir():
            if not entry_dir.is_dir():
                continue
            if not (entry_dir / ".git").exists():
                # Not a git worktree (e.g. .owners or metadata directory)
                continue
            # Check if this worktree is already represented in rows
            matched_row = False
            for r in rows:
                if r.raw_worktree and r.raw_worktree.resolve() == entry_dir.resolve():
                    matched_row = True
                    break
            if matched_row:
                continue

            # Check branch of this worktree
            wt_info = None
            for wt in registered_worktrees:
                try:
                    if Path(wt["path"]).resolve() == entry_dir.resolve():
                        wt_info = wt
                        break
                except Exception:
                    pass

            wt_branch = (
                wt_info.get("branch", "").removeprefix("refs/heads/") if wt_info else ""
            )
            if not wt_branch.startswith("aw/lane/"):
                rel_path = _repo_rel(repo, entry_dir)
                rows.append(
                    LaneRow(
                        lane=rel_path,
                        branch="-",
                        worktree=rel_path,
                        owner_run_pid="-",
                        live="-",
                        commits_not_landed="-",
                        uncommitted="-",
                        verdict="other: not a lane",
                        raw_worktree=entry_dir,
                    )
                )

    rows.sort(key=lambda r: r.lane)
    return rows


def render_lanes_table(rows: Sequence[LaneRow]) -> str:
    """Format lane rows as an aligned table."""
    headers = [
        "LANE",
        "OWNER RUN/PID",
        "LIVE",
        "COMMITS NOT LANDED",
        "UNCOMMITTED",
        "VERDICT",
    ]
    data = [
        [
            r.lane,
            r.owner_run_pid,
            r.live,
            r.commits_not_landed,
            r.uncommitted,
            r.verdict,
        ]
        for r in rows
    ]

    col_widths = [len(h) for h in headers]
    for row in data:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(strip_ansi(str(val))))

    lines = []
    hdr_line = "  ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    lines.append(hdr_line)
    sep_line = "  ".join("-" * col_widths[i] for i in range(len(headers)))
    lines.append(sep_line)
    for row in data:
        row_line = "  ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row))
        lines.append(row_line)

    return "\n".join(lines)


def _emit_agent_record(
    cmd: str,
    outcome: str,
    exit_code: int,
    *,
    verified: bool = True,
    complete: bool = True,
    extra: dict[str, Any] | None = None,
    args: Any = None,
) -> None:
    """Emit an aw.agent/v1 JSONL record to stdout."""
    from agent_workflows import agent_schema

    rec: dict[str, Any] = {
        "schema": agent_schema.SCHEMA_VERSION,
        "kind": "result",
        "cmd": cmd,
        "outcome": outcome,
        "exit": exit_code,
        "verified": verified,
        "complete": complete,
    }
    if extra:
        rec.update(extra)

    if args and getattr(args, "fields", None):
        fields = args.fields
        if isinstance(fields, str):
            fields = [f.strip() for f in fields.split(",") if f.strip()]
        rec = agent_schema.filter_record_fields(rec, fields)

    sys.stdout.write(agent_schema.render_jsonl_record(rec))


def run_list(args: argparse.Namespace) -> int:
    """Implementation of aw lanes list (E-03)."""
    repo = Path(getattr(args, "dir", None) or os.getcwd()).resolve()
    rows = collect_lane_rows(repo)
    as_agent = getattr(args, "agent", False)
    as_json = getattr(args, "json", False)

    if as_agent:
        _emit_agent_record(
            cmd="lanes list",
            outcome="ok" if rows else "empty",
            exit_code=0,
            verified=True,
            complete=True,
            extra={
                "lanes": [r.to_dict() for r in rows],
                "count": len(rows),
            },
            args=args,
        )
        return 0

    if as_json:
        payload = {
            "lanes": [r.to_dict() for r in rows],
            "count": len(rows),
        }
        print(json.dumps(payload, indent=2))
        return 0

    print(render_lanes_table(rows))
    return 0


def run_prune(args: argparse.Namespace) -> int:
    """Implementation of aw lanes prune [--apply] (E-04)."""
    repo = Path(getattr(args, "dir", None) or os.getcwd()).resolve()
    rows = collect_lane_rows(repo)
    as_agent = getattr(args, "agent", False)
    as_json = getattr(args, "json", False)
    apply_mode = getattr(args, "apply", False)

    removable_rows = [r for r in rows if r.verdict == "removable"]
    broken_rows = [r for r in rows if r.verdict.startswith("broken:")]
    no_record_rows = [r for r in rows if r.verdict == "keep: no run record"]

    if not as_agent and not as_json:
        print(render_lanes_table(rows))
        print()

    if not apply_mode:
        if not as_agent and not as_json:
            for r in removable_rows:
                print(f"will remove worktree {r.worktree} and branch {r.branch}")
            print("dry run: pass --apply to remove")
            if broken_rows:
                print(
                    "Broken branches: inspect manually with git branch -D <branch> or git fsck."
                )
            if no_record_rows:
                print(
                    "Lanes with no run record: inspect manually with git log <branch> or git status."
                )

        if as_agent:
            _emit_agent_record(
                cmd="lanes prune",
                outcome="preview",
                exit_code=0,
                verified=True,
                complete=False,
                extra={
                    "applied": False,
                    "next": "Pass --apply to remove removable lanes: aw lanes prune --apply",
                    "lanes": [r.to_dict() for r in rows],
                    "removable_count": len(removable_rows),
                },
                args=args,
            )
            return 0

        if as_json:
            print(
                json.dumps(
                    {
                        "applied": False,
                        "lanes": [r.to_dict() for r in rows],
                        "removable_count": len(removable_rows),
                    },
                    indent=2,
                )
            )
            return 0

        return 0

    # Apply mode
    refused_any = False
    removed_count = 0
    refused_count = 0

    for r in removable_rows:
        lane_id = r.raw_lane_id or r.lane

        # Re-read ownership immediately before acting (E-04)
        safe, reason = worktree_lease.lane_is_safe_to_adopt(repo, lane_id)
        if not safe:
            if not as_agent and not as_json:
                print(f"refused {r.lane}: {reason}")
            refused_any = True
            refused_count += 1
            continue

        resolved = r.resolved or resolve_lane_to_run(repo, r.branch, r.raw_worktree)
        if resolved is not None:
            holder = run_viewer.driver_holder_state(resolved.run_dir)
            if holder == run_viewer.HOLDER_LIVE:
                if not as_agent and not as_json:
                    print(
                        f"refused {r.lane}: owning run driver lock is held by a live process"
                    )
                refused_any = True
                refused_count += 1
                continue

        wt_path = (
            r.raw_worktree
            if (r.raw_worktree and r.raw_worktree.exists())
            else (repo / ".aw" / "worktrees" / lane_id)
        )
        handle = worktree_lease.WorktreeHandle(
            lane_id=lane_id,
            path=wt_path,
            branch=r.branch,
            base_commit="",
        )

        if resolved is not None and resolved.is_sweep:
            decision = lane_containment.teardown_review_sweep_lane(
                repo=repo,
                handle=handle,
                run_dir=resolved.run_dir,
                items=resolved.review_items,
            )
        else:
            decision = lane_containment.teardown_lane_if_classified(
                repo=repo,
                handle=handle,
                run_dir=resolved.run_dir if resolved else None,
                item=resolved.item if resolved else None,
            )

        if decision.torn_down:
            if not as_agent and not as_json:
                print(f"removed worktree {r.worktree} and branch {r.branch}")
            removed_count += 1
        else:
            refused_any = True
            refused_count += 1
            codes = (
                ", ".join(decision.reason_codes)
                if decision.reason_codes
                else decision.reason
            )
            if not as_agent and not as_json:
                print(f"refused {r.lane}: {decision.reason} ({codes})")

    if not as_agent and not as_json:
        if broken_rows:
            print(
                "Broken branches: inspect manually with git branch -D <branch> or git fsck."
            )
        if no_record_rows:
            print(
                "Lanes with no run record: inspect manually with git log <branch> or git status."
            )

    exit_code = 1 if refused_any else 0

    if as_agent:
        _emit_agent_record(
            cmd="lanes prune",
            outcome="ok" if not refused_any else "fail",
            exit_code=exit_code,
            verified=True,
            complete=True,
            extra={
                "applied": True,
                "lanes": [r.to_dict() for r in rows],
                "removed_count": removed_count,
                "refused_count": refused_count,
            },
            args=args,
        )
        return exit_code

    if as_json:
        print(
            json.dumps(
                {
                    "applied": True,
                    "lanes": [r.to_dict() for r in rows],
                    "removed_count": removed_count,
                    "refused_count": refused_count,
                },
                indent=2,
            )
        )
        return exit_code

    return exit_code
