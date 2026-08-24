"""Per-lane git worktree + fresh-session allocation and per-path exclusive leases (execset Order 03,
`m2wwns` E-02).

The concurrency ANALYZER (`orchestrate_isolation.analyze_concurrency_eligibility`) only decides
whether lanes MAY run in parallel and CARRIES a caller-supplied `worktree_path`/`session_id`; it
never creates a git worktree or session, and there is NO per-path exclusive-ownership lease in the
tree (the ledger's `writer_lock` is a different, single-writer-ledger concept). This module supplies
the three genuinely net-new isolation primitives:

  1. `allocate_worktree` / `teardown_worktree` - a real `git worktree add`/`git worktree remove` per
     write lane, rooted under a gitignored `.aw/worktrees/` directory.
  2. `allocate_session` - a fresh, deterministic session id per lane.
  3. `LeaseTable` - a per-path exclusive-ownership lease: a second lane cannot claim a path already
     owned by another lane (path-fencing). Workers never touch `events.jsonl`, source IPDs, history,
     backlog, walkthroughs, or the main worktree; the lease + worktree isolation is what fences them.

Integration itself is NOT re-implemented: callers gather `orchestrate_isolation.LaneOutcome`s and
call `orchestrate_isolation.execute_merge_and_revalidate_gate` (reused verbatim).

The git operations shell out via a small `_git` helper (patterned on `ipd_lifecycle._git`). The lease
table is pure in-memory state. No network or model calls.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

# The gitignored root for per-lane worktrees (matches the `.aw/worktrees/<node>` path the manifest
# compiler synthesizes in ipd_set_plan.node_to_lane_request).
WORKTREES_SUBDIR = ".aw/worktrees"


class WorktreeError(Exception):
    """Raised when a git worktree create/teardown fails."""


class LeaseConflictError(Exception):
    """Raised when a lane tries to claim a path already exclusively owned by another lane."""


def _git(repo_root: Path, args: List[str]) -> Tuple[int, str, str]:
    """Run a git command in ``repo_root``; return (returncode, stdout, stderr)."""
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _lane_dirname(lane_id: str) -> str:
    """A filesystem-safe directory name for a lane id (e.g. ``abc123:E-01`` -> ``abc123_E-01``)."""
    return lane_id.replace(":", "_").replace("/", "_")


# ---- worktree allocation -------------------------------------------------------------------------


class WorktreeHandle(NamedTuple):
    lane_id: str
    path: Path  # absolute worktree path
    branch: str  # the branch created for this lane's worktree
    base_commit: str


def allocate_worktree(
    repo_root: Path,
    lane_id: str,
    *,
    base_commit: str = "HEAD",
) -> WorktreeHandle:
    """Create a REAL git worktree for a write lane, on a fresh per-lane branch off ``base_commit``.

    Returns a WorktreeHandle. Raises WorktreeError on failure (fail-closed; no partial worktree left
    claimed). The worktree lives under the gitignored ``.aw/worktrees/<lane>`` so it never pollutes
    the main checkout.
    """
    name = _lane_dirname(lane_id)
    wt_path = (repo_root / WORKTREES_SUBDIR / name).resolve()
    branch = "aw/lane/{0}".format(name)
    # Resolve base commit to a stable sha for provenance.
    rc, out, err = _git(repo_root, ["rev-parse", base_commit])
    if rc != 0:
        raise WorktreeError(
            "cannot resolve base commit {0!r}: {1}".format(base_commit, err.strip())
        )
    base_sha = out.strip()
    wt_path.parent.mkdir(parents=True, exist_ok=True)
    rc, _out, err = _git(
        repo_root,
        ["worktree", "add", "-b", branch, str(wt_path), base_sha],
    )
    if rc != 0:
        raise WorktreeError(
            "git worktree add failed for lane {0!r}: {1}".format(lane_id, err.strip())
        )
    return WorktreeHandle(
        lane_id=lane_id, path=wt_path, branch=branch, base_commit=base_sha
    )


def teardown_worktree(
    repo_root: Path, handle: WorktreeHandle, *, force: bool = True
) -> None:
    """Remove a lane's git worktree and delete its per-lane branch. Best-effort but fail-loud on the
    worktree removal itself (a leaked worktree would keep a path claimed)."""
    args = ["worktree", "remove", str(handle.path)]
    if force:
        args.append("--force")
    rc, _out, err = _git(repo_root, args)
    if rc != 0:
        raise WorktreeError(
            "git worktree remove failed for lane {0!r}: {1}".format(
                handle.lane_id, err.strip()
            )
        )
    # Delete the per-lane branch (best-effort; a dangling branch is not a correctness hazard).
    _git(repo_root, ["branch", "-D", handle.branch])


# ---- fresh session allocation --------------------------------------------------------------------


class SessionHandle(NamedTuple):
    lane_id: str
    session_id: str


def allocate_session(lane_id: str, run_id: str) -> SessionHandle:
    """Allocate a fresh, deterministic session id for a lane (distinct per lane + run)."""
    return SessionHandle(
        lane_id=lane_id,
        session_id="sess-{0}-{1}".format(run_id, _lane_dirname(lane_id)),
    )


# ---- per-path exclusive lease --------------------------------------------------------------------


class LeaseTable:
    """A per-path exclusive-ownership lease table (net-new). At most one lane may own any given path.

    A lane claims the exact set of paths it will write (its ``files_targeted`` + generated files +
    shared surfaces). A second lane attempting to claim an already-owned path is REJECTED
    (LeaseConflictError), which is what prevents two concurrent workers from touching the same file.
    """

    def __init__(self) -> None:
        # path -> owning lane_id
        self._owner: Dict[str, str] = {}
        # lane_id -> set of paths it owns
        self._held: Dict[str, set] = {}

    def owner_of(self, path: str) -> Optional[str]:
        return self._owner.get(path)

    def held_by(self, lane_id: str) -> Tuple[str, ...]:
        return tuple(sorted(self._held.get(lane_id, set())))

    def claim(self, lane_id: str, paths: Sequence[str]) -> None:
        """Atomically claim ``paths`` for ``lane_id``. Fails closed (no partial claim) if ANY path is
        already owned by a different lane."""
        conflicts = [
            (p, self._owner[p])
            for p in paths
            if p in self._owner and self._owner[p] != lane_id
        ]
        if conflicts:
            p, other = conflicts[0]
            raise LeaseConflictError(
                "lane {0!r} cannot claim path {1!r}: already owned by lane {2!r}".format(
                    lane_id, p, other
                )
            )
        for p in paths:
            self._owner[p] = lane_id
            self._held.setdefault(lane_id, set()).add(p)

    def release(self, lane_id: str) -> None:
        """Release all paths owned by ``lane_id`` (called on lane teardown/integration)."""
        for p in list(self._held.get(lane_id, set())):
            if self._owner.get(p) == lane_id:
                del self._owner[p]
        self._held.pop(lane_id, None)

    def snapshot(self) -> Dict[str, str]:
        """A copy of the current path->owner map (for checkpointing/inspection)."""
        return dict(self._owner)


# ---- worker path-fencing -------------------------------------------------------------------------

# Paths a worker must NEVER touch (enforced by the lease + worktree isolation). These are coordinator-
# owned authoritative surfaces.
FORBIDDEN_WORKER_PATH_HINTS: Tuple[str, ...] = (
    "events.jsonl",
    ".aw/records/plans/",
    ".aw/records/backlog/",
    ".aw/records/walkthroughs/",
    ".aw/records/runs/",
)


def path_is_worker_forbidden(path: str) -> bool:
    """True if ``path`` is a coordinator-owned surface a worker lane must never write."""
    p = path.replace("\\", "/")
    return any(h in p for h in FORBIDDEN_WORKER_PATH_HINTS)


def assert_worker_scope(lane_id: str, paths: Sequence[str]) -> None:
    """Fail closed if a worker lane declares a write to a coordinator-owned surface (path-fencing)."""
    bad = [p for p in paths if path_is_worker_forbidden(p)]
    if bad:
        raise LeaseConflictError(
            "lane {0!r} declares a write to a coordinator-owned surface: {1}".format(
                lane_id, bad
            )
        )
