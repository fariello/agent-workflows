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

import json
import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

# The gitignored root for per-lane worktrees (matches the `.aw/worktrees/<node>` path the manifest
# compiler synthesizes in ipd_set_plan.node_to_lane_request).
WORKTREES_SUBDIR = ".aw/worktrees"

# Where a lane's durable OWNER record lives (laneorphan-01 `zwnjp3` E-08). Inside the gitignored
# worktrees root, so it is never committed, but OUTSIDE any lane directory, so it survives a
# `git worktree remove` and is still readable for a branch-only leftover.
OWNERS_SUBDIR = WORKTREES_SUBDIR + "/.owners"


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


def lane_branch_name(lane_id: str) -> str:
    """The per-lane branch name for ``lane_id``.

    Callers must NOT reconstruct this by hand from an id6, because allocation may attempt-scope the
    name (see `allocate_worktree`); read `handle.branch` instead. This helper exists for the lane
    classifier and for tests that need the CANONICAL (unscoped) name.
    """
    return "aw/lane/{0}".format(_lane_dirname(lane_id))


# ---- lane classification (laneorphan-01 `zwnjp3` E-01) -------------------------------------------
#
# Allocation, reclamation, and the liveness guard all need to know WHAT ACTUALLY EXISTS for a lane
# before touching it. `inspect_lane` is the single non-mutating substrate for all three; none of them
# may grow its own git probing.
#
# The five states are exhaustive and the STALE one is MANDATORY, not a refinement. A four-state
# scheme (ABSENT/EMPTY/HOLDS-WORK/FOREIGN) has a MEASURED HOLE: a clean leftover lane cut BEFORE main
# advanced has zero commits beyond its OWN base and a clean tree, so it looks EMPTY, yet its base does
# NOT equal the requested base, so an adopt-on-EMPTY precondition fails with nothing else matching it.
# That is exactly the state an interrupted-then-resumed run produces.

LANE_ABSENT = "ABSENT"  # nothing exists (no branch, no registered worktree)
LANE_EMPTY = (
    "EMPTY"  # exists, clean, no commits beyond base, AND base == requested base
)
LANE_STALE = (
    "STALE"  # exists, clean, no commits, but base is an ANCESTOR of the requested base
)
LANE_HOLDS_WORK = "HOLDS-WORK"  # commits beyond its base, or a dirty tree
LANE_FOREIGN = (
    "FOREIGN"  # base is NOT an ancestor of the requested base: not ours to reuse
)

LANE_STATES: Tuple[str, ...] = (
    LANE_ABSENT,
    LANE_EMPTY,
    LANE_STALE,
    LANE_HOLDS_WORK,
    LANE_FOREIGN,
)


class LaneState(NamedTuple):
    """A non-mutating reading of what exists for one lane. See `inspect_lane`."""

    lane_id: str
    state: str  # one of LANE_STATES
    branch: str  # the canonical per-lane branch name (may not exist)
    branch_exists: bool
    worktree_path: Optional[Path]  # registered worktree path, if git has one registered
    worktree_registered: bool
    head: Optional[str]  # the lane's current tip sha, if it has one
    base_sha: Optional[str]  # the lane's OWN base sha (the commit it was cut from)
    requested_base: Optional[str]  # the base sha the caller asked about
    commits_ahead: int  # commits on the lane beyond its own base
    dirty: bool  # uncommitted changes in the lane worktree
    owner: Optional[dict]  # durable owner record (E-08), if readable
    owner_live: Optional[bool]  # True/False when determinable, None when unknown

    @property
    def exists(self) -> bool:
        return self.state != LANE_ABSENT

    @property
    def holds_work(self) -> bool:
        return self.state == LANE_HOLDS_WORK

    @property
    def reclaimable(self) -> bool:
        """Provably empty: safe to tear down. NEVER true for a lane holding commits or dirty files."""
        return (
            self.state in (LANE_EMPTY, LANE_STALE)
            and not self.dirty
            and self.commits_ahead == 0
        )


def _registered_worktrees(repo_root: Path) -> Dict[str, dict]:
    """Map branch ref -> {path, head} for every worktree git has REGISTERED.

    Uses `git worktree list --porcelain`, which is the reliable discovery surface: a lane branch can
    survive with NO worktree directory, and a directory-existence check would miss it entirely.
    """
    rc, out, _err = _git(repo_root, ["worktree", "list", "--porcelain"])
    if rc != 0:
        return {}
    by_branch: Dict[str, dict] = {}
    cur: dict = {}
    for line in out.splitlines() + [""]:
        line = line.rstrip("\n")
        if not line:
            if cur.get("branch"):
                by_branch[cur["branch"]] = cur
            cur = {}
            continue
        if line.startswith("worktree "):
            cur["path"] = line[len("worktree ") :]
        elif line.startswith("HEAD "):
            cur["head"] = line[len("HEAD ") :]
        elif line.startswith("branch "):
            cur["branch"] = line[len("branch ") :]
        elif line == "locked" or line.startswith("locked "):
            cur["locked"] = line[len("locked ") :] if len(line) > len("locked") else ""
    return by_branch


def _lane_base_sha(repo_root: Path, branch: str, head: str) -> Optional[str]:
    """The commit the lane was CUT FROM, read from the branch's creation reflog entry.

    `git branch` writes a `branch: Created from <sha>` reflog entry, so the lane's own base survives
    even after the lane commits on top of it (verified at git 2.43.0). Falls back to the merge-base
    against the default branch, and finally to the head itself.
    """
    rc, out, _err = _git(repo_root, ["reflog", "show", "--no-abbrev", branch])
    if rc == 0 and out.strip():
        lines = out.strip().splitlines()
        created = lines[-1]
        marker = "branch: Created from "
        if marker in created:
            sha = created.split(marker, 1)[1].strip()
            rc2, out2, _e2 = _git(
                repo_root, ["rev-parse", "--verify", sha + "^{commit}"]
            )
            if rc2 == 0:
                return out2.strip()
        # No creation entry (reflog trimmed): the OLDEST recorded position is the best base we have.
        first = created.split()[0]
        rc2, out2, _e2 = _git(repo_root, ["rev-parse", "--verify", first + "^{commit}"])
        if rc2 == 0:
            return out2.strip()
    return head or None


def inspect_lane(
    repo_root: Path,
    lane_id: str,
    *,
    base_commit: str = "HEAD",
) -> LaneState:
    """Classify a lane WITHOUT mutating anything (E-01). Never runs a write command.

    Reports the branch, the registered worktree, the lane head, the lane's OWN base sha (not merely a
    boolean, so callers can compare rather than re-probe), whether the tree is dirty, how far the lane
    is ahead of its base, the durable owner record, and one of the five `LANE_STATES`.
    """
    branch = lane_branch_name(lane_id)
    rc, out, _err = _git(repo_root, ["rev-parse", base_commit])
    requested_base = out.strip() if rc == 0 else None

    rc, out, _err = _git(repo_root, ["rev-parse", "--verify", branch])
    branch_exists = rc == 0
    head = out.strip() if rc == 0 else None

    registered = _registered_worktrees(repo_root).get("refs/heads/" + branch)
    wt_path = (
        Path(registered["path"]) if registered and registered.get("path") else None
    )
    worktree_registered = registered is not None
    if head is None and registered and registered.get("head"):
        head = registered["head"]

    owner = read_lane_owner(repo_root, lane_id)
    owner_live = _owner_is_live(owner) if owner else None

    if not branch_exists and not worktree_registered:
        return LaneState(
            lane_id=lane_id,
            state=LANE_ABSENT,
            branch=branch,
            branch_exists=False,
            worktree_path=None,
            worktree_registered=False,
            head=None,
            base_sha=None,
            requested_base=requested_base,
            commits_ahead=0,
            dirty=False,
            owner=owner,
            owner_live=owner_live,
        )

    base_sha = _lane_base_sha(repo_root, branch, head or "") if head else None

    commits_ahead = 0
    if head and base_sha:
        rc, out, _err = _git(
            repo_root, ["rev-list", "--count", "{0}..{1}".format(base_sha, head)]
        )
        if rc == 0 and out.strip().isdigit():
            commits_ahead = int(out.strip())

    dirty = False
    if wt_path is not None and wt_path.is_dir():
        rc, out, _err = _git(wt_path, ["status", "--porcelain"])
        dirty = rc == 0 and bool(out.strip())

    if commits_ahead > 0 or dirty:
        state = LANE_HOLDS_WORK
    elif base_sha and requested_base and base_sha == requested_base:
        state = LANE_EMPTY
    elif (
        base_sha
        and requested_base
        and _git(repo_root, ["merge-base", "--is-ancestor", base_sha, requested_base])[
            0
        ]
        == 0
    ):
        # Clean and empty, but cut from an OLDER base: adopting it would mis-attribute main's own
        # intervening commits to this execution (see `allocate_worktree`).
        state = LANE_STALE
    else:
        state = LANE_FOREIGN

    return LaneState(
        lane_id=lane_id,
        state=state,
        branch=branch,
        branch_exists=branch_exists,
        worktree_path=wt_path,
        worktree_registered=worktree_registered,
        head=head,
        base_sha=base_sha,
        requested_base=requested_base,
        commits_ahead=commits_ahead,
        dirty=dirty,
        owner=owner,
        owner_live=owner_live,
    )


# ---- lane ownership / liveness (laneorphan-01 `zwnjp3` E-08) -------------------------------------
#
# Adoption must never hand a LIVE driver's worktree to a second driver. This is reachable today, not
# hypothetically: the driver run lock is per-run-directory, so it does NOT serialize two concurrent
# `aw oc run` processes in one checkout, and lane names derive from the bare id6 with no run scoping,
# so two runs given the same plan produce the SAME lane name. A freshly allocated, not-yet-committed
# lane of a LIVE run classifies EMPTY at the same base, so adopt-on-EMPTY alone would collide.
#
# MECHANISM CHOSEN: a durable OWNER RECORD (json under `.aw/worktrees/.owners/<lane>.json`) carrying
# hostname, pid, and boot-scoped process identity. `git worktree lock` was the alternative and is
# available at git 2.43.0, but it is rejected here for two reasons: it is keyed on the WORKTREE, so it
# says nothing about a branch-only leftover (the likelier residue), and a lock left by a killed process
# is indistinguishable from a live one, which would make the ACTUAL target case (a dead owner)
# unadoptable. The record is readable in both cases and lets a dead owner be told from a live one.
#
# FAIL SAFE: any doubt (unreadable record, foreign host, unknown pid semantics) falls through to
# attempt-scoped allocation rather than adopting.


def _owner_record_path(repo_root: Path, lane_id: str) -> Path:
    return (
        repo_root / OWNERS_SUBDIR / "{0}.json".format(_lane_dirname(lane_id))
    ).resolve()


def _process_start_token(pid: int) -> Optional[str]:
    """A boot-scoped token distinguishing THIS process from a later pid reuse, or None if unknown."""
    try:
        with open(
            "/proc/{0}/stat".format(pid), "r", encoding="utf-8", errors="replace"
        ) as fh:
            fields = fh.read().rsplit(")", 1)[-1].split()
        # field 22 after the comm field is starttime (jiffies since boot)
        return fields[19]
    except Exception:
        return None


def write_lane_owner(repo_root: Path, lane_id: str, **extra: object) -> Path:
    """Record durably that THIS process owns ``lane_id`` (E-08). Survives process exit."""
    path = _owner_record_path(repo_root, lane_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    pid = os.getpid()
    record = {
        "lane_id": lane_id,
        "host": socket.gethostname(),
        "pid": pid,
        "start_token": _process_start_token(pid),
        "allocated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    record.update({k: v for k, v in extra.items() if v is not None})
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    tmp.replace(path)
    return path


def read_lane_owner(repo_root: Path, lane_id: str) -> Optional[dict]:
    """Read a lane's durable owner record, or None when absent/unreadable."""
    path = _owner_record_path(repo_root, lane_id)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def clear_lane_owner(repo_root: Path, lane_id: str) -> None:
    """Drop a lane's owner record (called on teardown; best-effort)."""
    try:
        _owner_record_path(repo_root, lane_id).unlink()
    except Exception:
        pass


def _owner_is_live(owner: dict) -> Optional[bool]:
    """True if the recorded owner process is still running, False if gone, None if undeterminable."""
    if not isinstance(owner, dict):
        return None
    pid = owner.get("pid")
    host = owner.get("host")
    if not isinstance(pid, int):
        return None
    if host and host != socket.gethostname():
        # A record from another machine: we cannot tell, so treat as UNKNOWN (never adopt).
        return None
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # alive but not ours to signal
    except Exception:
        return None
    token = owner.get("start_token")
    if token is not None:
        current = _process_start_token(pid)
        if current is not None and current != token:
            return False  # pid was REUSED by a different process; the owner is gone
    return True


def lane_owned_by_other_live_process(repo_root: Path, lane_id: str) -> bool:
    """True only when a DIFFERENT, still-running process owns this lane.

    This is the question both adoption and interrupt-time reclamation actually need to ask, and it is
    NOT "is the owner alive". A driver reclaiming its own lanes at shutdown is itself the live owner of
    every one of them, so a bare liveness test would make reclamation a no-op and leak every lane,
    which is the exact defect being fixed. Undeterminable liveness counts as owned (fail safe).
    """
    owner = read_lane_owner(repo_root, lane_id)
    if owner is None:
        return _owner_record_path(repo_root, lane_id).exists()
    if owner.get("pid") == os.getpid() and owner.get("host") == socket.gethostname():
        return False
    return _owner_is_live(owner) is not False


def lane_is_safe_to_adopt(repo_root: Path, lane_id: str) -> Tuple[bool, str]:
    """Positive-evidence liveness gate (E-08): may we take over this lane's worktree?

    Returns (safe, reason). Fails SAFE: an owner that is live, or whose liveness cannot be
    determined, is NOT adoptable. A lane with no owner record at all IS adoptable, because records are
    only ever written by an allocating driver and its absence means no driver claims it.

    ADOPTION MUST STAY POSSIBLE FOR THE ACTUAL TARGET CASE, a lane whose owning process is gone, so
    this distinguishes a dead owner from a live one rather than refusing all adoption. It also treats
    THIS process as an allowed owner: a driver re-allocating its own lane (a retry inside one run) is
    the resumable case, not a collision. The hazard E-08 exists for is a DIFFERENT live process.
    """
    owner = read_lane_owner(repo_root, lane_id)
    if owner is None:
        # Distinguish NO record (nothing claims the lane, adoptable) from an UNREADABLE one (a claim
        # we cannot evaluate, so fail safe and attempt-scope instead).
        if _owner_record_path(repo_root, lane_id).exists():
            return False, "owner record present but unreadable; failing safe"
        return True, "no owner record; unclaimed"
    if owner.get("pid") == os.getpid() and owner.get("host") == socket.gethostname():
        return True, "owned by THIS process (pid {0}); self-reallocation".format(
            os.getpid()
        )
    live = _owner_is_live(owner)
    if live is True:
        return False, "owner pid {0} on {1} is LIVE".format(
            owner.get("pid"), owner.get("host")
        )
    if live is None:
        return False, "owner liveness undeterminable ({0!r}); failing safe".format(
            {k: owner.get(k) for k in ("host", "pid")}
        )
    return True, "owner pid {0} is gone".format(owner.get("pid"))


# ---- worktree allocation -------------------------------------------------------------------------

# Allocation dispositions (E-03). Reported to the CALLER rather than emitted as ledger events here:
# this module imports only stdlib and is reused to allocate disposable candidate worktrees, so an
# event hook here would both couple a low-level primitive to run context and misrecord candidates.
DISPOSITION_CREATED = "created"
DISPOSITION_ADOPTED = "adopted"
DISPOSITION_ATTEMPT_SCOPED = "attempt-scoped"


class WorktreeHandle(NamedTuple):
    lane_id: str
    path: Path  # absolute worktree path
    branch: str  # the branch created for (or adopted for) this lane's worktree
    base_commit: str
    # laneorphan-01 (`zwnjp3`) E-03: which outcome actually occurred. Defaulted so existing
    # positional construction and unpacking keep working.
    disposition: str = DISPOSITION_CREATED
    # When attempt-scoped, the lane this allocation was DISPLACED FROM (left untouched).
    displaced_from: Optional[str] = None
    # The reason an adoption was declined, when one was.
    disposition_detail: Optional[str] = None


def _attempt_scoped_lane_id(repo_root: Path, lane_id: str, base_commit: str) -> str:
    """The next free ``<lane_id>:attemptN`` id. Rides the EXISTING name sanitizer (`:` -> `_`), so it
    needs no new naming mechanism: `abc123:attempt2` becomes branch `aw/lane/abc123_attempt2`."""
    for n in range(2, 1000):
        candidate = "{0}:attempt{1}".format(lane_id, n)
        st = inspect_lane(repo_root, candidate, base_commit=base_commit)
        if st.state == LANE_ABSENT:
            return candidate
    raise WorktreeError(
        "cannot attempt-scope lane {0!r}: 998 attempt-scoped lanes already exist".format(
            lane_id
        )
    )


def allocate_worktree(
    repo_root: Path,
    lane_id: str,
    *,
    base_commit: str = "HEAD",
    allow_adopt: bool = True,
) -> WorktreeHandle:
    """Create a REAL git worktree for a write lane, on a per-lane branch off ``base_commit``.

    IDEMPOTENT FOR THE SAME LANE IDENTITY (laneorphan-01 `zwnjp3` E-02): a run must never be
    permanently wedged by its OWN leftovers, so this tolerates lane debris instead of raising:

      * ABSENT      -> create, exactly as before (`disposition="created"`).
      * EMPTY       -> ADOPT the existing lane (`disposition="adopted"`). A lane created by
                       `git worktree add -b <branch> <path> <base>` IS the base commit, so an empty
                       lane at the REQUESTED base is byte-identical to a fresh allocation. Gated on a
                       liveness check: a lane a LIVE process owns is never adopted.
      * STALE       -> attempt-scope. NOT adopted even though it is clean and empty, and the reason is
                       correctness, not tidiness: `aw ipd begin` freezes `base_head` at main's CURRENT
                       head and finalize computes this execution's changed set as
                       `git diff --name-only base_head..HEAD`, so committing on a lane cut from an
                       OLDER base makes main's own intervening commits appear in that delta and be
                       attributed to this execution.
      * HOLDS-WORK  -> attempt-scope. The existing lane may hold real unmerged work; leave it exactly
                       as it is and discoverable.
      * FOREIGN     -> attempt-scope. Not this run's lane to reuse.

    Attempt-scoping allocates `<lane_id>:attemptN` (branch `aw/lane/<lane>_attemptN`) ALONGSIDE the
    existing lane, which is left byte-identical. `handle.disposition` says which happened and
    `handle.displaced_from` names the lane displaced.

    Still FAILS CLOSED on a genuinely broken `git worktree add`. Note a failed add still CREATES the
    branch, so the failure path cleans that up, but ONLY when no branch existed before this call:
    a name-based delete would destroy a pre-existing lane branch that may hold unmerged commits.
    Consequently a failed allocation over a PRE-EXISTING branch legitimately leaves that branch in
    place, untouched.
    """
    rc, out, err = _git(repo_root, ["rev-parse", base_commit])
    if rc != 0:
        raise WorktreeError(
            "cannot resolve base commit {0!r}: {1}".format(base_commit, err.strip())
        )
    base_sha = out.strip()

    existing = inspect_lane(repo_root, lane_id, base_commit=base_sha)
    disposition = DISPOSITION_CREATED
    displaced_from: Optional[str] = None
    detail: Optional[str] = None
    target_lane = lane_id

    if existing.state == LANE_EMPTY and allow_adopt:
        safe, why = lane_is_safe_to_adopt(repo_root, lane_id)
        if safe and existing.worktree_registered and existing.worktree_path is not None:
            write_lane_owner(
                repo_root,
                lane_id,
                branch=existing.branch,
                worktree=str(existing.worktree_path),
                base_commit=base_sha,
                disposition=DISPOSITION_ADOPTED,
            )
            return WorktreeHandle(
                lane_id=lane_id,
                path=existing.worktree_path,
                branch=existing.branch,
                base_commit=base_sha,
                disposition=DISPOSITION_ADOPTED,
                displaced_from=None,
                disposition_detail="adopted empty lane at the requested base ({0})".format(
                    why
                ),
            )
        if not safe:
            detail = "declined to adopt: {0}".format(why)
        else:
            detail = "declined to adopt: branch exists with no registered worktree"
        target_lane = _attempt_scoped_lane_id(repo_root, lane_id, base_sha)
        disposition = DISPOSITION_ATTEMPT_SCOPED
        displaced_from = existing.branch
    elif existing.state != LANE_ABSENT:
        detail = "existing lane classified {0}; left untouched".format(existing.state)
        target_lane = _attempt_scoped_lane_id(repo_root, lane_id, base_sha)
        disposition = DISPOSITION_ATTEMPT_SCOPED
        displaced_from = existing.branch

    name = _lane_dirname(target_lane)
    wt_path = (repo_root / WORKTREES_SUBDIR / name).resolve()
    branch = "aw/lane/{0}".format(name)
    # Record the PRE-CALL ref state, so the failure path can clean up ONLY a branch THIS call made.
    pre_call_branch_existed = _git(repo_root, ["rev-parse", "--verify", branch])[0] == 0
    wt_path.parent.mkdir(parents=True, exist_ok=True)
    rc, _out, err = _git(
        repo_root,
        ["worktree", "add", "-b", branch, str(wt_path), base_sha],
    )
    if rc != 0:
        if not pre_call_branch_existed:
            # A failed add still creates the branch; delete the one WE created (and only that one).
            _git(repo_root, ["branch", "-D", branch])
        raise WorktreeError(
            "git worktree add failed for lane {0!r}: {1}".format(
                target_lane, err.strip()
            )
        )
    write_lane_owner(
        repo_root,
        target_lane,
        branch=branch,
        worktree=str(wt_path),
        base_commit=base_sha,
        disposition=disposition,
    )
    return WorktreeHandle(
        lane_id=target_lane,
        path=wt_path,
        branch=branch,
        base_commit=base_sha,
        disposition=disposition,
        displaced_from=displaced_from,
        disposition_detail=detail,
    )


def teardown_worktree(
    repo_root: Path, handle: WorktreeHandle, *, force: bool = True
) -> None:
    """Remove a lane's git worktree and delete its per-lane branch. Fail-loud on the worktree removal
    itself (a leaked worktree would keep a path claimed).

    DATA-SAFETY WARNING, and it is not theoretical: this deletes the per-lane BRANCH as well as the
    worktree, and `--force` also destroys UNCOMMITTED files in the lane. MEASURED: after tearing down
    a lane holding one commit, the branch is gone, `git reflog show <branch>` is EMPTY, and the commit
    survives only as an UNREFERENCED object, i.e. garbage-collectable with no ref and no reflog to
    recover it from; and uncommitted lane files are gone from git AND from disk with nothing to
    recover. So the branch deletion is a DATA-SAFETY HAZARD for any lane that holds work, NOT the
    "best-effort, not a correctness hazard" cleanup an earlier comment here claimed.

    Callers must therefore CLASSIFY FIRST and tear down only a provably-empty lane. Use
    `inspect_lane` (`LaneState.reclaimable`) or the drivers' `reclaim_lanes_on_interrupt`, which
    preserves anything holding work. Never call this on an unclassified lane.
    """
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
    _git(repo_root, ["branch", "-D", handle.branch])
    clear_lane_owner(repo_root, handle.lane_id)


def snapshot_lane_dirty_work(
    repo_root: Path, handle: WorktreeHandle, *, note: str = ""
) -> Optional[str]:
    """COMMIT a preserved lane's UNCOMMITTED work to its own lane branch, marked as an interrupted
    snapshot (laneorphan-01 `zwnjp3` E-09). Returns the snapshot commit sha, or None when the lane
    tree was already clean (no empty snapshot is ever made).

    Why this exists: `git worktree remove --force` destroys a lane's uncommitted files from git AND
    from disk, unrecoverably and silently (measured). Merely declining to delete them leaves them one
    careless cleanup away from gone, with no record of what they were. A commit on the lane branch is
    unlosable, inspectable, and revertible by comparison.

    This is NOT the auto-stash the house rules forbid: that prohibition protects a HUMAN's checkout
    from being rewritten, whereas this writes only inside a driver-created lane whose sole content is
    that turn's work. Nothing outside the lane worktree is touched and main is never committed to.

    Two deliberate implementation choices keep it inside the execution contract. Staging is
    PATH-SCOPED to the exact paths `git status --porcelain` reports, never `git add -A`/`--all`. And
    the commit is made with PLUMBING (`write-tree` + `commit-tree` + `update-ref`) rather than
    `git commit`, so no hook runs and no `--no-verify` is needed: a hook that rejected or rewrote the
    snapshot would defeat the one thing this function exists to guarantee, which is that the work
    cannot be lost.
    """
    wt = Path(handle.path)
    if not wt.is_dir():
        return None
    rc, out, _err = _git(wt, ["status", "--porcelain"])
    if rc != 0 or not out.strip():
        return None
    paths: List[str] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        entry = line[3:] if len(line) > 3 else ""
        if " -> " in entry:  # a rename: stage both sides
            old, new = entry.split(" -> ", 1)
            paths.extend([old.strip().strip('"'), new.strip().strip('"')])
        elif entry:
            paths.append(entry.strip().strip('"'))
    if not paths:
        return None
    # PATH-SCOPED staging of exactly the lane's own dirty paths (never `add -A`/`--all`).
    rc, _out, err = _git(wt, ["add", "--", *paths])
    if rc != 0:
        raise WorktreeError(
            "cannot stage interrupted snapshot for lane {0!r}: {1}".format(
                handle.lane_id, err.strip()
            )
        )
    message = (
        "WIP INTERRUPTED SNAPSHOT (not finished work): lane {0}\n\n"
        "Recorded by the driver when the run was interrupted, so the lane's uncommitted edits\n"
        "could not be lost. This is a preservation snapshot, NOT validated or reviewed work.\n"
        "Inspect, amend, or discard it deliberately.\n".format(handle.lane_id)
    )
    if note:
        message += "\n{0}\n".format(note)
    rc, tree, err = _git(wt, ["write-tree"])
    if rc != 0:
        raise WorktreeError(
            "cannot write interrupted-snapshot tree for lane {0!r}: {1}".format(
                handle.lane_id, err.strip()
            )
        )
    rc, parent, _err = _git(wt, ["rev-parse", "HEAD"])
    args = ["commit-tree", tree.strip()]
    if rc == 0 and parent.strip():
        args.extend(["-p", parent.strip()])
    args.extend(["-m", message])
    rc, commit, err = _git(wt, args)
    if rc != 0:
        raise WorktreeError(
            "cannot record interrupted snapshot for lane {0!r}: {1}".format(
                handle.lane_id, err.strip()
            )
        )
    sha = commit.strip()
    rc, _out, err = _git(
        wt, ["update-ref", "-m", "aw: interrupted lane snapshot", "HEAD", sha]
    )
    if rc != 0:
        raise WorktreeError(
            "cannot advance lane {0!r} to its interrupted snapshot: {1}".format(
                handle.lane_id, err.strip()
            )
        )
    return sha


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
