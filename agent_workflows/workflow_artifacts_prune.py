"""Planner and deleter for pruning aged workflow-artifacts run directories (muza7y).

Reclaims .aw/workflow-artifacts/<workflow>/<run-id>/ with preview-by-default.
Retention policy:
- Keep the newest N runs per workflow (default 5).
- Keep anything younger than D days (default 30d).
- A run is deleted only if it is BOTH outside newest N AND older than D.
- Reader-safety rules:
  1. pinned: run_id in keep_ids.
  2. open-questions: run contains open-questions.md without '_No unresolved questions._'.
  3. unreviewed-decisions: assess-shape run with decisions.md and no open-questions.md,
     unless ipd-link.md points to an existing IPD file.
  4. unfinished-run: release-review run lacking positive completion artifact (12-final-response.md).
  5. sole-durable-output: assess run whose ipd-link.md is absent or records that no IPD was created.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Set

from agent_workflows import set_records

READER_SAFETY_REASONS: Set[str] = {
    "pinned",
    "open-questions",
    "unreviewed-decisions",
    "unfinished-run",
    "sole-durable-output",
}


@dataclass
class PruneEntry:
    workflow: str
    run_id: str
    path: Path
    age_days: int
    decision: str  # "keep" or "delete"
    reason: str  # "pinned", "open-questions", "unreviewed-decisions", "unfinished-run",
    # "sole-durable-output", "newest-N", "younger-than-D", "aged"
    size_bytes: int


@dataclass
class PrunePlan:
    artifacts_root: Path
    entries: List[PruneEntry]

    @property
    def deletions(self) -> List[PruneEntry]:
        return [e for e in self.entries if e.decision == "delete"]

    @property
    def keeps(self) -> List[PruneEntry]:
        return [e for e in self.entries if e.decision == "keep"]

    @property
    def reader_safety_keeps(self) -> List[PruneEntry]:
        return [
            e
            for e in self.entries
            if e.decision == "keep" and e.reason in READER_SAFETY_REASONS
        ]

    @property
    def reclaimable_bytes(self) -> int:
        return sum(e.size_bytes for e in self.deletions)


def _parse_run_date(run_id: str) -> Optional[datetime.date]:
    """Parse leading YYYYMMDD from run_id if valid date."""
    if len(run_id) >= 8 and run_id[:8].isdigit():
        try:
            return datetime.datetime.strptime(run_id[:8], "%Y%m%d").date()
        except ValueError:
            pass
    return None


def _get_newest_mtime(run_dir: Path) -> float:
    """Find newest mtime of any file under run_dir without following symlinks."""
    try:
        newest = run_dir.lstat().st_mtime
    except OSError:
        return 0.0
    for root, _dirs, files in os.walk(run_dir, followlinks=False):
        for f in files:
            fp = Path(root) / f
            try:
                st = fp.lstat()
                if st.st_mtime > newest:
                    newest = st.st_mtime
            except OSError:
                pass
    return newest


def _calculate_dir_size(run_dir: Path) -> int:
    """Calculate total size of all files under run_dir without following symlinks."""
    total = 0
    for root, _dirs, files in os.walk(run_dir, followlinks=False):
        for f in files:
            fp = Path(root) / f
            try:
                total += fp.lstat().st_size
            except OSError:
                pass
    return total


def _calculate_run_age(
    run_id: str, run_dir: Path, today: datetime.date
) -> tuple[int, datetime.date]:
    """Return (age_in_days, run_date) using leading YYYYMMDD or newest file mtime."""
    d = _parse_run_date(run_id)
    if d is not None:
        return max(0, (today - d).days), d
    newest_mtime = _get_newest_mtime(run_dir)
    mtime_date = datetime.date.fromtimestamp(newest_mtime)
    return max(0, (today - mtime_date).days), mtime_date


def _ipd_link_records_no_ipd(text: str) -> bool:
    """Check if ipd-link.md records that no IPD was created (e.g. 'Created: none')."""
    if re.search(r"\bCreated:\s*none\b", text, re.IGNORECASE):
        return True
    if text.strip().lower() in ("none", "none.", "created: none", "created: none."):
        return True
    return False


def _resolve_ipd_link(run_dir: Path, artifacts_root: Path) -> tuple[bool, bool]:
    """Inspect ipd-link.md in run_dir.

    Returns:
        (records_no_ipd, target_ipd_exists)
    """
    link_path = run_dir / "ipd-link.md"
    if not link_path.is_file():
        return False, False
    try:
        content = link_path.read_text(encoding="utf-8")
    except OSError:
        return False, False

    if _ipd_link_records_no_ipd(content):
        return True, False

    # Attempt to locate IPD path in text
    # Determine repo_root relative to artifacts_root
    if (
        artifacts_root.name == "workflow-artifacts"
        and artifacts_root.parent.name == ".aw"
    ):
        repo_root = artifacts_root.parent.parent
    else:
        repo_root = artifacts_root.parent

    # Search for path ending in .ipd.md
    # An optional DRIVE prefix (`C:`) is part of the path: without it a Windows absolute path
    # `C:/<dir>/x.ipd.md` was captured without its drive (from the first `/`), which is not absolute on Windows, so a
    # resolvable link never resolved and the run was wrongly KEPT (measured on the Windows CI runner).
    matches = re.findall(r"(?:[A-Za-z]:)?[\w\-./\\]+\.ipd\.md", content)
    for m in matches:
        target = Path(m)
        if target.is_absolute() and target.is_file():
            return False, True
        if (repo_root / target).is_file():
            return False, True
        if (run_dir / target).is_file():
            return False, True

    return False, False


def plan_prune(
    artifacts_root: Path,
    *,
    keep_last: int = 5,
    older_than_days: float = 30.0,
    keep_ids: Sequence[str] = (),
    today: Optional[datetime.date] = None,
) -> PrunePlan:
    """Pure planner for pruning aged workflow-artifacts run directories.

    Returns PrunePlan with keep or delete decision and reason per run dir.
    Performs zero filesystem modifications.
    """
    if today is None:
        today = datetime.date.today()

    if not artifacts_root.is_dir():
        return PrunePlan(artifacts_root=artifacts_root, entries=[])

    keep_ids_set = set(keep_ids)
    all_entries: List[PruneEntry] = []

    # Only depth-2 directories (<workflow>/<run-id>) are candidates.
    # Depth-1 files (README) and symlinked directories are skipped and never followed.
    for wf_entry in sorted(artifacts_root.iterdir()):
        if not wf_entry.is_dir() or wf_entry.is_symlink():
            continue
        workflow_name = wf_entry.name

        wf_runs: List[tuple[str, Path, int, datetime.date, int]] = []
        for run_entry in wf_entry.iterdir():
            if not run_entry.is_dir() or run_entry.is_symlink():
                continue
            run_id = run_entry.name
            age_days, run_date = _calculate_run_age(run_id, run_entry, today)
            size_bytes = _calculate_dir_size(run_entry)
            wf_runs.append((run_id, run_entry, age_days, run_date, size_bytes))

        # Order within a workflow by age (newest first, run_id as tie-break).
        # Newer date comes first, so sort descending by (run_date, run_id).
        wf_runs.sort(key=lambda x: (x[3], x[0]), reverse=True)

        for idx, (run_id, run_dir, age_days, _run_date, size_bytes) in enumerate(
            wf_runs
        ):
            decision = "keep"
            reason = "newest-N"

            # Check reader-safety rules first
            # 1. Pinned
            if run_id in keep_ids_set:
                decision = "keep"
                reason = "pinned"

            # 2. open-questions in set_records projection shape (E-02)
            elif (
                run_dir / set_records.OPEN_QUESTIONS_FILE
            ).is_file() and "_No unresolved questions._" not in (
                run_dir / set_records.OPEN_QUESTIONS_FILE
            ).read_text(encoding="utf-8", errors="replace"):
                decision = "keep"
                reason = "open-questions"

            # 3. unfinished release-review run (E-04a)
            # 00-run-protocol.md calls the run dir "the authoritative run record" (and "authoritative state").
            # 12-final-response.md is keyed on as the definitive positive completion artifact produced at the
            # end of Section 8 (final ship review). Without it, an in-progress or aborted-pre-flight run is
            # live resumable state, so it must be kept.
            elif (
                workflow_name == "release-review"
                or workflow_name.startswith("release-review-")
            ) and not (run_dir / "12-final-response.md").is_file():
                decision = "keep"
                reason = "unfinished-run"

            # 4. assess sole-durable-output when no IPD was created (E-04b)
            # The assess workflow writes two durable outputs: the IPD and the run record. For a run that
            # proposed no IPD (closing report 'Created: none.'), the run record is the sole output.
            elif (
                workflow_name == "assess" or workflow_name.startswith("assess-")
            ) and _resolve_ipd_link(run_dir, artifacts_root)[0]:
                decision = "keep"
                reason = "sole-durable-output"

            # 5. assess unreviewed-decisions when decisions.md exists without open-questions.md (E-03)
            # The assess workflow hand-authors decisions.md with open questions in prose without writing
            # open-questions.md. Keep unless ipd-link.md resolves to an existing IPD file.
            elif (
                (run_dir / "decisions.md").is_file()
                and not (run_dir / set_records.OPEN_QUESTIONS_FILE).is_file()
                and not _resolve_ipd_link(run_dir, artifacts_root)[1]
            ):
                decision = "keep"
                reason = "unreviewed-decisions"

            # 6. assess run missing ipd-link.md entirely (E-04b fallback)
            elif (
                (workflow_name == "assess" or workflow_name.startswith("assess-"))
                and not (run_dir / "ipd-link.md").is_file()
                and not (run_dir / "decisions.md").is_file()
            ):
                decision = "keep"
                reason = "sole-durable-output"

            # Normal retention rules
            elif idx < keep_last:
                decision = "keep"
                reason = "newest-N"
            elif age_days < older_than_days:
                decision = "keep"
                reason = "younger-than-D"
            else:
                # Outside newest keep_last AND older than older_than_days
                decision = "delete"
                reason = "aged"

            all_entries.append(
                PruneEntry(
                    workflow=workflow_name,
                    run_id=run_id,
                    path=run_dir,
                    age_days=age_days,
                    decision=decision,
                    reason=reason,
                    size_bytes=size_bytes,
                )
            )

    return PrunePlan(artifacts_root=artifacts_root, entries=all_entries)


def apply_prune(plan: PrunePlan) -> List[Path]:
    """Execute deletion of planned delete entries.

    Re-checks that each path is a real directory (not a symlink) resolving inside
    plan.artifacts_root. Paths failing validation are skipped and reported to stderr.
    """
    deleted: List[Path] = []
    root_resolved = plan.artifacts_root.resolve()

    for entry in plan.entries:
        if entry.decision != "delete":
            continue
        p = entry.path

        # Symlink check is load-bearing: Path.is_dir() follows symlinks.
        if p.is_symlink():
            sys.stderr.write(
                f"warning: skipping symlinked run directory {p} (refusing to follow symlink)\n"
            )
            continue

        if not p.is_dir():
            sys.stderr.write(f"warning: skipping non-directory {p}\n")
            continue

        target = p.resolve()
        try:
            rel = target.relative_to(root_resolved)
            if rel == Path("."):
                sys.stderr.write(
                    f"warning: refusing to delete artifacts root itself {p}\n"
                )
                continue
        except ValueError:
            sys.stderr.write(f"warning: skipping path escaping artifacts root {p}\n")
            continue

        shutil.rmtree(target, ignore_errors=False)
        deleted.append(p)

    return deleted


def run_archive(args: argparse.Namespace, term: object) -> int:
    """CLI handler for `aw archive workflow-artifacts`."""
    from agent_workflows import duration
    from agent_workflows.project_context import resolve_verb_repo_root

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    artifacts_root = repo_root / set_records.RUN_ARTIFACTS_SUBDIR

    # A missing tree is an empty result, exit 0
    if not artifacts_root.is_dir():
        if hasattr(term, "empty_result"):
            term.empty_result(summary="no workflow artifacts to prune")
        else:
            print("no workflow artifacts to prune")
        return 0

    raw_age = getattr(args, "age", None)
    try:
        older_than_days = duration.parse_age_duration(raw_age, default_days=30)
    except ValueError as e:
        if hasattr(term, "line"):
            term.line(f"error: {e}")
        else:
            print(f"error: {e}")
        return 2

    keep_last = getattr(args, "keep_last", 5)
    if keep_last is None:
        keep_last = 5

    keep_ids = list(getattr(args, "keep", None) or [])
    apply = bool(getattr(args, "apply", False))

    plan = plan_prune(
        artifacts_root,
        keep_last=keep_last,
        older_than_days=older_than_days,
        keep_ids=keep_ids,
    )

    if not plan.entries:
        if hasattr(term, "empty_result"):
            term.empty_result(summary="no workflow artifacts to prune")
        else:
            print("no workflow artifacts to prune")
        return 0

    print_fn = getattr(term, "line", print)

    if not apply:
        # Preview mode
        for entry in plan.deletions:
            print_fn(
                f"would delete {entry.workflow}/{entry.run_id} ({entry.age_days}d, {entry.reason})"
            )
        for entry in plan.reader_safety_keeps:
            print_fn(f"keep {entry.workflow}/{entry.run_id} ({entry.reason})")

        print_fn(f"kept: {len(plan.keeps)} run(s)")
        print_fn(f"reclaimable: {plan.reclaimable_bytes} bytes")
        print_fn("preview only; re-run with --apply to delete")
        return 0

    # Apply mode
    deleted = apply_prune(plan)
    deleted_set = set(deleted)
    for entry in plan.deletions:
        if entry.path in deleted_set:
            print_fn(
                f"deleted {entry.workflow}/{entry.run_id} ({entry.age_days}d, {entry.reason})"
            )

    return 0
