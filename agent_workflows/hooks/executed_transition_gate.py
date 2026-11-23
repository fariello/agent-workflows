"""Local pre-commit gate: refuse a raw (non-finalize) plan-to-`executed` commit (ipdgates Order dulzpy).

Order 07 delegates the CLI path (`aw set executed`) into the gated `aw ipd finalize`, but it cannot
cover the path where an agent NEVER touches the CLI: hand-editing a plan's `- Status:` to `executed`
(or `git mv`-ing a plan into `executed/`) and then committing with a raw `git commit`. That commit runs
no finalize - no receipt, no scope check, no attribution - the exact p7dqwz-class bypass via the editor.

This LOCAL pre-commit hook inspects the STAGED change and, for each PLAN that in this commit either
gained a `- Status: executed`/`done` line it did not have at HEAD, OR ARRIVED in an `executed/`
directory, REQUIRES durable evidence that `aw ipd finalize` performed THIS transition. Missing/stale
evidence -> the commit is REFUSED with an actionable `aw ipd finalize <plan>` message.

WHAT IS *NOT* A TRANSITION (gatejrnl i4c0c3): a plan that was ALREADY in `executed/` at HEAD under the
SAME `- Id:` and is merely EDITED - a body correction, an appended `## Workflow history` line. Nothing
transitions in such a commit, so demanding finalize evidence for it is a FALSE POSITIVE whose only
remedy is `--no-verify`, which trains away the very habit this gate exists to build. The exemption is
narrow in two ways that are load-bearing rather than defensive: it requires the path to have EXISTED
at HEAD (so a plan ADDED straight into `executed/` is still gated, being an arrival), and it requires
the HEAD content's `- Id:` to MATCH the staged one (so replacing an already-executed plan's file with a
DIFFERENT plan is still gated, being a raw transition wearing an existing filename). Both the
`moved_into_executed` and `gained_executed` predicates read the HEAD blob at the path the file actually
occupied, since reading it at a rename source alone left BOTH firing on any edit to an executed plan.

Honest limits (never oversold): git hooks are LOCAL, not cloned by default, and skippable with
`--no-verify`. This is a PREVENTION layer, not an absolute gate; the deterministic local backstop is the
`proclint` detector (`aw check`/`aw doctor`). There is deliberately NO remote/CI enforcement.

TWO ACCEPTING PATHS (integpath Order 29wvmj added the second):

1. THE JOURNAL (DECISION 14-dulzpy-D1), consulted FIRST and unchanged: `aw ipd finalize` leaves, at
   commit time, a durable transaction JOURNAL under
   `.aw/state/runtime/transactions/ipd_finalize_<id6>.json` whose phase is a finalize-transaction
   phase (`ready-to-commit` during finalize's own commit, then `committed-incomplete`/`complete`) and
   which records the plan id + the executed destination path. The hook accepts a plan->executed staged
   transition iff such a journal exists for the plan (matching id + dest), which faithfully realizes
   OQ-01's "finalize ran this transition" predicate against the artifacts finalize actually leaves
   (the begin receipt carries the pending-time digest and is consumed only after the commit, so the
   journal is the present-at-commit-time proof). A raw hand-edit has NO such journal.

2. IN-TREE EVIDENCE DURING A MERGE (integpath 29wvmj), used ONLY when the journal is absent AND a
   merge is in progress: a `lifecycle(<id6>): finalize` commit reachable from the INCOMING side of the
   merge (`HEAD..MERGE_HEAD`) and naming THAT plan's id6. The journal cannot travel with a lane branch
   because `.aw/state/` is gitignored, and it is also EPHEMERAL WITHIN a tree (finalize deletes it on
   completion), so before this path EVERY integration of a genuinely finalized lane was refused and
   `--no-verify` became routine practice. A commit, unlike the journal, survives the branch. The merge
   is NOT a blanket exemption: a plan staged into `executed/` inside a merge whose incoming side
   carries no matching finalize commit is still REFUSED, and a finalize commit for a DIFFERENT id6
   does not authorize this plan. Absent `MERGE_HEAD` means not-a-merge, hence refuse (fail closed).

THE LOG-FORMAT BRANCH (IPD `6jd6mh` E-03, spec `4sd62s` AC-16 case 2, 5.2 step 4a). A plan whose
`meta/<id6>.jsonl` log is in the index is judged by the events its log APPENDS in this commit, not by
the journal or the in-tree commit: the transition into `executed` is accepted only when it arrives as
a FINALIZE append (a `transition` to `executed` plus a `set` of `scope_result`, `out_of_scope_paths`
or `widened_paths` in the same append) or an ORCHESTRATOR ROLLUP-RETIREMENT append (a `transition` to
`executed` that carries `path` and sets none of the three scope fields, spec `77tr3o`). Everything
else is a raw transition and is refused: a mirror flip or a `git mv` into `executed/` with no such
append, a bare appended `transition`, and replacing an executed file with a different `id`. A valid
event does not prove which tool wrote it (spec 3c), so this branch is exactly as strong as the event
shapes it reads. The branch is reached only for a plan that HAS a log in the index, so a legacy-format
plan, and every plan before the cutover, keeps the two accepting paths above unchanged.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

# The finalize-transaction journal phases that prove finalize is performing / performed THIS
# transition (present at commit time). Imported lazily to keep this module import-light.
_FINALIZE_PHASES = ("ready-to-commit", "committed-incomplete", "complete")

_PLANS_PREFIX = ".aw/records/plans/"
_EXECUTED_SEGMENT = "/executed/"


def _git(repo_root: Path, args: List[str]) -> Tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _repo_root(start: Path) -> Path:
    rc, out, _err = _git(start, ["rev-parse", "--show-toplevel"])
    if rc == 0 and out.strip():
        return Path(out.strip())
    return start.resolve()


def _is_plan_path(path: str) -> bool:
    """True for a plan IPD record path under .aw/records/plans/** (a `.ipd.md`)."""
    p = path.strip().replace("\\", "/")
    return p.startswith(_PLANS_PREFIX) and p.endswith(".ipd.md")


def _has_executed_status(text: Optional[str]) -> bool:
    """True if the plan text carries a metadata `- Status: executed` (or `done` alias) line."""
    if not text:
        return False
    from agent_workflows import artifact_meta as _meta
    from agent_workflows import plans as _plans

    st = _meta.read_text(text, record_type="ipd")
    raw = st.status or (
        st.legacy_raw_status.strip().split()[0]
        if st.legacy_raw_status and st.legacy_raw_status.strip()
        else None
    )
    return _plans.normalize_status(raw) == "executed"


def _plan_id_of(text: Optional[str]) -> Optional[str]:
    """Read the `- Id:` id6 from plan text."""
    if not text:
        return None
    from agent_workflows import artifact_core as _core
    from agent_workflows import artifact_meta as _meta

    st = _meta.read_text(text, record_type="ipd")
    return st.id6 if (st.id6 and _core.ID6_RE.fullmatch(st.id6)) else None


def _state_is_executed(
    st: Optional[object], fallback_status: Optional[str] = None
) -> bool:
    """True iff an ``artifact_meta.State`` (or mirror status) is canonically ``executed`` (D-2)."""
    from agent_workflows import plans as _plans

    raw: Optional[str] = None
    if st is not None:
        raw = getattr(st, "status", None)
        if not raw:
            lraw = getattr(st, "legacy_raw_status", None)
            if lraw and str(lraw).strip():
                raw = str(lraw).strip().split()[0]
    if not raw:
        raw = fallback_status
    return _plans.normalize_status(raw) == "executed"


def _staged_plan_executed_transitions(
    repo_root: Path,
    log_ids: FrozenSet[str] = frozenset(),
) -> List[Tuple[str, Optional[str], str]]:
    """Return (staged_path, plan_id, reason) for each plan gaining executed status / moved to executed/.

    Detection compares the STAGED index (`:0:`) against HEAD via ``artifact_meta.read_at`` AT THE
    PATH THE FILE OCCUPIED AT HEAD (the rename source for an `R`, the unchanged path for an `A`/`M`/`C`):
      * a plan whose staged status is terminal ``executed`` that its HEAD state did NOT have
        (a hand-edited status flip), OR
      * a plan ARRIVING in an `executed/` directory in this commit, meaning it was not ALREADY there
        at HEAD under the SAME `- Id:` (a `git mv`, an `A` straight into `executed/`, or a wholesale
        content substitution at an already-executed path).

    An ORDINARY EDIT to a plan already in `executed/` under the same `- Id:` is NOT a transition and
    is NOT reported (i4c0c3): nothing is transitioning, so there is no finalize to demand evidence of.

    ``log_ids`` names the plans whose `meta/<id6>.jsonl` log is in the index. For those only, a staged
    in-file mirror that reads `executed` while HEAD's state did not is ALSO a transition, because the
    replayed log (not the mirror) supplies ``staged_state``. Empty (every legacy repository) leaves the
    detection exactly as before.
    """
    from agent_workflows import artifact_meta as _meta
    from agent_workflows import check_engine as _ce

    rc, out, _err = _git(
        repo_root, ["diff", "--cached", "--name-status", "-M", "--", _PLANS_PREFIX]
    )
    if rc != 0 or not out.strip():
        return []
    ctx = _ce._git_read_at_context(repo_root)
    transitions: List[Tuple[str, Optional[str], str]] = []
    with _meta.ephemeral_if_uninitialized():
        for line in out.splitlines():
            parts = line.split("\t")
            if not parts:
                continue
            code = parts[0].strip()
            if code.startswith("R") and len(parts) >= 3:
                old_path, new_path = parts[1].strip(), parts[2].strip()
            elif len(parts) >= 2:
                old_path, new_path = (
                    (None, parts[1].strip())
                    if code in ("A", "M", "C")
                    else (parts[1].strip(), parts[1].strip())
                )
            else:
                continue
            if not _is_plan_path(new_path):
                continue

            plan_id, staged_mirror_status, staged_exists = _meta.resolve_mirror_at(
                new_path, ":0:", project_context=ctx
            )
            staged_state = None
            staged_corrupt: Optional[str] = None
            if plan_id is not None:
                sres = _meta.read_at(
                    plan_id, ":0:", project_context=ctx, path_hint=new_path
                )
                if sres.kind == "ok":
                    staged_state = sres.state
                elif sres.kind == "corrupt":
                    staged_corrupt = sres.error or "corrupt metadata record"
            elif not staged_exists:
                pres = _meta.read_path_at(new_path, ":0:", project_context=ctx)
                if pres.kind == "corrupt":
                    staged_corrupt = pres.error or "corrupt metadata record"

            if staged_corrupt is not None:
                transitions.append((new_path, plan_id, f"corrupt:{staged_corrupt}"))
                continue

            # THE PATH THE FILE ACTUALLY OCCUPIED AT HEAD (i4c0c3): the rename SOURCE for an `R`,
            # and the unchanged path itself for an `A`/`M`/`C`.
            head_path = old_path or new_path
            head_id, head_mirror_status, head_exists = _meta.resolve_mirror_at(
                head_path, "HEAD", project_context=ctx
            )
            head_state = None
            if head_id is not None:
                hres = _meta.read_at(
                    head_id, "HEAD", project_context=ctx, path_hint=head_path
                )
                if hres.kind == "ok":
                    head_state = hres.state

            was_in_executed_at_head = head_exists and _EXECUTED_SEGMENT in (
                "/" + head_path
            )
            same_plan_at_head = plan_id is not None and head_id == plan_id
            moved_into_executed = _EXECUTED_SEGMENT in ("/" + new_path) and not (
                was_in_executed_at_head and same_plan_at_head
            )
            gained_executed = _state_is_executed(
                staged_state, staged_mirror_status
            ) and not _state_is_executed(head_state, head_mirror_status)
            if (
                not gained_executed
                and plan_id in log_ids
                and _state_is_executed(None, staged_mirror_status)
                and not _state_is_executed(head_state, head_mirror_status)
            ):
                gained_executed = True

            if moved_into_executed or gained_executed:
                reason = (
                    "moved into executed/"
                    if moved_into_executed
                    else "gained '- Status: executed'"
                )
                transitions.append((new_path, plan_id, reason))
    return transitions


_SCOPE_FIELDS = frozenset(("scope_result", "out_of_scope_paths", "widened_paths"))


def _indexed_log_ids(repo_root: Path) -> FrozenSet[str]:
    """The id6s whose `meta/<id6>.jsonl` log is in the index (empty in a legacy-format repository)."""
    from agent_workflows import check_engine as _ce

    ctx = _ce._git_read_at_context(repo_root)
    repo_dir, rel_records = _ce._staged_meta_layout(repo_root, ctx)
    return frozenset(_ce._indexed_meta_logs(repo_dir, rel_records))


def _staged_log_only_executed_transitions(
    repo_root: Path,
    log_ids: FrozenSet[str],
    already: FrozenSet[str],
) -> List[Tuple[str, Optional[str], str]]:
    """Plans whose staged `meta/<id6>.jsonl` alone enters `executed` (no `.md` change staged).

    Without this, an appended `transition` to `executed` committed without touching the plan file
    would never reach the gate. Reports ``(rel_log, id6, reason)`` for each plan-type log whose
    replayed status is `executed` staged but not at HEAD and which ``already`` does not cover.
    """
    if not log_ids:
        return []
    from agent_workflows import artifact_meta as _meta
    from agent_workflows import check_engine as _ce

    ctx = _ce._git_read_at_context(repo_root)
    repo_dir, rel_records = _ce._staged_meta_layout(repo_root, ctx)
    meta_dir = f"{rel_records}/meta" if rel_records else "meta"
    rc, out, _err = _git(
        repo_dir,
        [
            "-c",
            "core.quotepath=false",
            "diff",
            "--cached",
            "--no-renames",
            "--name-only",
            "--diff-filter=AM",
            "--",
            meta_dir,
        ],
    )
    if rc != 0 or not out.strip():
        return []
    found: List[Tuple[str, Optional[str], str]] = []
    with _meta.ephemeral_if_uninitialized():
        for line in out.splitlines():
            rel = line.strip()
            stem = (
                rel[len(meta_dir) + 1 : -len(".jsonl")]
                if rel.endswith(".jsonl")
                else ""
            )
            if stem not in log_ids or stem in already:
                continue
            staged = _meta.read_at(stem, ":0:", project_context=ctx)
            if (
                staged.kind != "ok"
                or staged.state is None
                or staged.state.type != "ipd"
            ):
                continue
            head = _meta.read_at(stem, "HEAD", project_context=ctx)
            head_state = head.state if head.kind == "ok" else None
            if _state_is_executed(staged.state) and not _state_is_executed(head_state):
                found.append((rel, stem, "log transitions to executed"))
    return found


def _log_executed_append_verdict(repo_root: Path, plan_id: str) -> Tuple[bool, str]:
    """Judge a log-format plan's transition into `executed` by the events its log appends now.

    Returns ``(accepted, detail)``. Accepted only for a finalize append or an orchestrator
    rollup-retirement append (see the module docstring); ``detail`` names what was found otherwise.
    """
    from agent_workflows import artifact_meta as _meta
    from agent_workflows import check_engine as _ce

    ctx = _ce._git_read_at_context(repo_root)
    with _meta.ephemeral_if_uninitialized():
        staged = _meta.read_at(plan_id, ":0:", project_context=ctx)
        head = _meta.read_at(plan_id, "HEAD", project_context=ctx)
    if staged.kind != "ok" or staged.state is None:
        return False, f"the staged log does not replay ({staged.error or staged.kind})"
    head_seq = (
        int(head.state.last_seq or 0)
        if head.kind == "ok" and head.state is not None
        else 0
    )
    groups: Dict[Any, List[Dict[str, Any]]] = {}
    for ev in staged.history:
        if int(ev.get("seq", 0)) > head_seq:
            groups.setdefault(ev.get("append"), []).append(ev)
    for evs in groups.values():
        trans = next(
            (
                e
                for e in evs
                if e.get("op") == "transition" and e.get("to") == "executed"
            ),
            None,
        )
        if trans is None:
            continue
        scope_set = any(
            e.get("op") == "set"
            and isinstance(e.get("fields"), dict)
            and _SCOPE_FIELDS & set(e["fields"])
            for e in evs
        )
        if scope_set:
            return True, "finalize append"
        if trans.get("path"):
            return True, "orchestrator rollup-retirement append"
        return False, (
            f"append {trans.get('append')} transitions to executed with neither the finalize "
            "scope fields nor a rollup-retirement `path`"
        )
    return False, (
        f"`meta/{plan_id}.jsonl` appends no transition to executed in this commit "
        "(a mirror flip, `git mv`, or file replacement)"
    )


def _finalize_evidence_ok(repo_root: Path, plan_id: str, staged_path: str) -> bool:
    """True iff a finalize transaction journal proves finalize performed THIS plan->executed transition.

    Realizes OQ-01's receipt-consumed predicate against the artifacts finalize leaves at commit time
    (DECISION 14-dulzpy-D1): a journal for ``plan_id`` whose phase is a finalize-transaction phase and
    whose recorded destination path matches the staged executed path. A raw hand-edit has no journal.
    """
    from agent_workflows import ipd_lifecycle as _life

    journal = _life.read_finalize_journal(repo_root, plan_id)
    if journal is None:
        return False
    if journal.get("phase") not in _FINALIZE_PHASES:
        return False
    if journal.get("plan_id") != plan_id:
        return False
    # Bind to THIS transition: the journal's recorded executed destination matches the staged path.
    dest = (journal.get("dest_path") or "").replace("\\", "/")
    staged = staged_path.replace("\\", "/")
    if dest and dest != staged:
        return False
    return True


def _git_dir(repo_root: Path) -> Optional[Path]:
    """The repository's GIT DIR, resolved THROUGH git rather than assumed to be ``<root>/.git``.

    Inside a WORKTREE `.git` is a FILE pointing elsewhere, and this repository uses lane worktrees as
    its normal execution mode, so a hardcoded `<root>/.git/MERGE_HEAD` would silently never match
    there. `git rev-parse --git-dir` may also return a RELATIVE path (a bare `.git` in a normal
    clone), so it is joined against the directory the command ran in before use.
    """
    rc, out, _err = _git(repo_root, ["rev-parse", "--git-dir"])
    if rc != 0 or not out.strip():
        return None
    git_dir = Path(out.strip())
    if not git_dir.is_absolute():
        git_dir = repo_root / git_dir
    return git_dir


def _merge_incoming_commits(repo_root: Path) -> List[str]:
    """The INCOMING commit sha(s) of a merge in progress; EMPTY when no merge is in progress (E-01).

    A LIST, not a single sha, and TWO signals, not one, because the two git hook stages this gate runs
    on expose the merge differently. Both were MEASURED (git 2.43.0) rather than assumed:

      * `pre-commit`, i.e. the HAND sequence `git merge --no-commit` then a separate `git commit`, and
        the conflicted-then-resolved path: `MERGE_HEAD` EXISTS in the git dir and holds one sha per
        incoming side. No `GITHEAD_*` variable is set.
      * `pre-merge-commit`, i.e. an AUTOMATED `git merge` that creates the commit itself: `MERGE_HEAD`
        is ABSENT (git has not written it yet), and the incoming side is exposed only as an
        ENVIRONMENT variable named `GITHEAD_<sha>` per incoming side. `AUTO_MERGE` is NOT a usable
        substitute: it is written by the `ort` strategy and is absent for octopus and `-s resolve`.

    An OCTOPUS merge legitimately has several incoming sides (measured: three `GITHEAD_*` variables for
    a three-lane merge, and `MERGE_HEAD` carries one sha per line), so evidence is searched across all
    of them. An empty result means "not a merge", which makes the caller REFUSE (fail closed).
    """
    git_dir = _git_dir(repo_root)
    shas: List[str] = []
    if git_dir is not None:
        merge_head = git_dir / "MERGE_HEAD"
        try:
            if merge_head.is_file():
                for line in merge_head.read_text(encoding="utf-8").splitlines():
                    sha = line.strip()
                    if sha and sha not in shas:
                        shas.append(sha)
        except OSError:
            pass
    if shas:
        return shas
    # `pre-merge-commit`: no MERGE_HEAD yet, so fall back to git's own GITHEAD_<sha> variables. This is
    # NOT a weaker check: each sha is verified below to be a real commit that is NOT already reachable
    # from HEAD, so an unrelated or forged variable buys nothing an attacker did not already have.
    import os
    import re

    for name in os.environ:
        # CASE-INSENSITIVE on purpose: on Windows `os.environ` UPPER-CASES every key, so git's
        # `GITHEAD_<sha>` arrives as `GITHEAD_<SHA>`; a lowercase-only pattern silently found no
        # incoming side there and refused every legitimate automated merge. Normalize to lowercase.
        m = re.fullmatch(r"GITHEAD_([0-9a-fA-F]{7,64})", name, flags=re.IGNORECASE)
        if not m:
            continue
        sha = m.group(1).lower()
        rc, out, _err = _git(repo_root, ["cat-file", "-t", sha])
        if rc != 0 or out.strip() != "commit":
            continue
        # Must be an INCOMING side: a commit already reachable from HEAD is not being merged in.
        rc_anc, _o, _e = _git(repo_root, ["merge-base", "--is-ancestor", sha, "HEAD"])
        if rc_anc == 0:
            continue
        if sha not in shas:
            shas.append(sha)
    return shas


def _intree_finalize_evidence_ok(
    repo_root: Path, plan_id: str, incoming_commits: List[str]
) -> bool:
    """True iff an INCOMING side of this merge carries `aw ipd finalize`'s own commit for ``plan_id``.

    In-tree evidence is the point (E-02): unlike the gitignored, ephemeral journal, a COMMIT survives
    the lane branch, so a genuinely finalized lane can be integrated without `--no-verify`.

    Three bindings keep this from becoming a blanket merge exemption:
      * PLAN-BOUND: the subject's id6 must equal the staged plan's `- Id:`, exactly as the journal
        predicate binds to ``plan_id`` + ``dest_path``. Finalize for plan A cannot authorize plan B.
      * INCOMING-SIDE-ONLY: the search range is ``HEAD..<incoming>``, so a finalize commit already on
        HEAD long ago cannot be replayed as evidence for a different plan arriving now.
      * EXACT SUBJECT FORM (OQ-02): only `lifecycle(<id6>): finalize`, the subject `aw ipd finalize`
        itself writes. A looser match would let an ordinary work commit that happens to name the plan
        authorize the transition, which is the hand-edit case wearing a different hat.

    The subject STRING is `artifact_core.finalize_commit_subject` (IPD `zexed1` E-02), the same
    definition the producer composes and the run viewer's discrepancy classifier reads, so this gate
    cannot silently stop recognizing a genuine finalize because the subject changed elsewhere. Imported
    lazily to keep this hook's module import-light (stdlib only at module scope).
    """
    from agent_workflows import artifact_core as _core

    subject = _core.finalize_commit_subject(plan_id)
    for incoming in incoming_commits:
        rc, out, _err = _git(repo_root, ["log", "--format=%s", f"HEAD..{incoming}"])
        if rc != 0:
            continue
        for line in out.splitlines():
            if line.strip().startswith(subject):
                return True
    return False


def _candidate_state_durable_dirs(repo_root: Path) -> List[Path]:
    """Resolve durable state root(s) via project_context, falling back to checkout_control_root.

    Checking ``checkout_control_root(repo_root) / 'state' / 'durable'`` after the worktree-local
    project context ensures ``commit_lock.commit_isolated``'s detached ``.aw-isocommit-*`` linked
    worktree still finds the primary checkout's ``m0001`` journal marker.
    """
    from agent_workflows import ipd_lifecycle as _life
    from agent_workflows import project_context as _pc

    candidates: List[Path] = []
    seen: set[Path] = set()

    def _add(p: Optional[object]) -> None:
        if not p:
            return
        cand = Path(str(p))
        try:
            key = cand.resolve()
        except OSError:
            key = cand
        if key not in seen:
            seen.add(key)
            candidates.append(cand)

    try:
        ctx = _pc.resolve_project_context(target_repo=str(repo_root))
        _add(ctx.physical_classes.get("state_durable"))
        _add(ctx.logical_roots.get("state_durable"))
        if ctx.logical_roots.get("state"):
            _add(Path(ctx.logical_roots["state"]) / "durable")
    except Exception:
        pass

    try:
        _add(_life.checkout_control_root(repo_root) / "state" / "durable")
    except Exception:
        pass

    return candidates


def _read_m0001_marker(journal_dir: Path) -> Tuple[Optional[dict], bool]:
    """Read marker dict from ``terminal_commit_marker.json`` or ``journal.json``.

    Returns ``(marker_dict, corrupt_or_invalid)``. Read-only; never mutates journal state.
    """
    import json

    marker_file = journal_dir / "terminal_commit_marker.json"
    if marker_file.is_file():
        try:
            data = json.loads(marker_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None, True
        if not isinstance(data, dict):
            return None, True
        return data, False

    journal_file = journal_dir / "journal.json"
    if journal_file.is_file():
        try:
            jdata = json.loads(journal_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None, True
        if isinstance(jdata, dict):
            marker = jdata.get("terminal_commit_marker")
            if marker is None:
                return None, False
            if isinstance(marker, dict):
                return marker, False
            return None, True
    return None, False


def _migration_marker_accepts(repo_root: Path) -> bool:
    """Return True iff an active ``m0001`` marker matches the current staged ``git write-tree`` id.

    Read-only: reads marker files and runs ``git write-tree`` without mutating refs, index, or
    working tree. Emits a single-line warning to stderr when ``tree_id`` mismatches.
    """
    import sys

    staged_tree: Optional[str] = None
    for state_durable in _candidate_state_durable_dirs(repo_root):
        journal_dir = state_durable / "migrations" / "m0001"
        marker, invalid = _read_m0001_marker(journal_dir)
        if invalid:
            return False
        if marker is None:
            continue
        if marker.get("migration_id") != "m0001":
            return False
        expected_tree = marker.get("tree_id")
        if not isinstance(expected_tree, str) or not expected_tree.strip():
            return False
        expected_tree = expected_tree.strip()

        if staged_tree is None:
            rc, out, _err = _git(repo_root, ["write-tree"])
            if rc != 0 or not out.strip():
                return False
            staged_tree = out.strip()

        if staged_tree == expected_tree:
            return True

        sys.stderr.write(
            f"warning: m0001 terminal commit marker tree_id mismatch "
            f"(expected {expected_tree}, staged {staged_tree}); falling back to standard gate checks.\n"
        )
        return False
    return False


def check(repo_root: Optional[Path] = None) -> Tuple[int, List[str]]:
    """Run the gate. Returns (exit_code, messages). exit 0 = ok/no-op, 1 = refused."""
    # The lifecycle subject grammar the refusal message QUOTES back to the operator, from the one
    # definition the producer and the matcher share (IPD `zexed1` E-02). Lazy, per this module's
    # import-light rule.
    from agent_workflows import artifact_core as _core

    root = _repo_root(repo_root or Path("."))
    # Empty in a legacy-format repository, which keeps every verdict below byte-identical (6jd6mh).
    log_ids = _indexed_log_ids(root)
    transitions = _staged_plan_executed_transitions(root, log_ids)
    transitions += _staged_log_only_executed_transitions(
        root, log_ids, frozenset(t[1] for t in transitions if t[1])
    )
    if not transitions:
        return 0, []  # fast no-op: no plan executed-transition staged

    if _migration_marker_accepts(root):
        return 0, []

    # A merge in progress unlocks the SECOND (in-tree) accepting path, never a blanket exemption.
    # EMPTY means not-a-merge, in which case behavior is byte-identical to before integpath 29wvmj.
    incoming_commits = _merge_incoming_commits(root)

    refusals: List[str] = []
    for staged_path, plan_id, reason in transitions:
        if reason.startswith("corrupt:"):
            detail = reason[len("corrupt:") :]
            id_tag = f" ({plan_id})" if plan_id else ""
            refusals.append(
                f"{staged_path}{id_tag}: staged plan record is unparseable/corrupt ({detail}); "
                "cannot verify executed transition."
            )
            continue
        if plan_id is None:
            refusals.append(
                f"{staged_path}: this plan is being moved to executed ({reason}) but has no readable "
                "'- Id:' handle to verify a finalize receipt against; run `aw ipd finalize` instead."
            )
            continue
        if plan_id in log_ids:
            accepted, detail = _log_executed_append_verdict(root, plan_id)
            if not accepted:
                refusals.append(
                    f"{staged_path} ({plan_id}): raw plan->executed transition ({reason}) on a "
                    f"log-format plan: {detail}. A log-format plan enters executed only through a "
                    f"finalize append or an orchestrator rollup-retirement append; run `aw ipd "
                    f"finalize {plan_id} --actor <agent/model> --message <summary> --apply`."
                )
            continue
        if _finalize_evidence_ok(root, plan_id, staged_path):
            continue
        if incoming_commits and _intree_finalize_evidence_ok(
            root, plan_id, incoming_commits
        ):
            continue
        if incoming_commits:
            # MERGE-CASE refusal (E-04): the refusal is attributed to ABSENT EVIDENCE, never to the
            # presence of a merge, and the remedy neither names `--no-verify` nor tells the operator to
            # commit, stash, reset, or clean anything (the `z2isfg` wording discipline).
            refusals.append(
                f"{staged_path} ({plan_id}): this merge carries this plan into executed/ ({reason}) "
                f"but the incoming side ({', '.join(c[:12] for c in incoming_commits)}) has NO "
                f"'{_core.finalize_commit_subject(plan_id)}' commit for it, so nothing here shows `aw ipd "
                f"finalize` performed this transition. Merging a lane on which finalize genuinely ran "
                f"is accepted; run `aw ipd finalize {plan_id} --actor <agent/model> --message "
                f"<summary> --apply` on the branch that owns this plan (which runs the receipt/scope/"
                f"attribution gates and makes the lifecycle commit), then merge that branch."
            )
        else:
            refusals.append(
                f"{staged_path} ({plan_id}): raw plan->executed transition ({reason}) with NO matching "
                f"finalize evidence in .aw/state/. Do not hand-edit/`git mv` a plan to executed; run "
                f"`aw ipd finalize {plan_id} --actor <agent/model> --message <summary> --apply` "
                "(which runs the receipt/scope/attribution gates and makes the lifecycle commit)."
            )
    if refusals:
        return 1, refusals
    return 0, []


def main(argv: Optional[List[str]] = None, *, args: Optional[object] = None) -> int:
    """CLI entry for the pre-commit hook. Emits structured aw.agent/v1 result on --agent
    or JSON on --json; prints refusals to stderr and returns int exit code in human mode."""
    import sys
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic,
        select_output,
    )

    if args is None and argv:
        import types

        args = types.SimpleNamespace(
            agent="--agent" in argv,
            json="--json" in argv,
        )

    ctx = select_output(args)
    exit_code, messages = check()

    if ctx.is_agent or ctx.is_json:
        diagnostics: List[Diagnostic] = []
        for m in messages:
            loc = "ipd-executed-gate"
            det = m
            if ": " in m:
                parts = m.split(": ", 1)
                loc = parts[0].split()[0]
                det = parts[1]
            diagnostics.append(
                Diagnostic(location=loc, rule="ipd-executed-gate", detail=det)
            )
        if exit_code != 0 and not diagnostics:
            diagnostics.append(
                Diagnostic(
                    location="ipd-executed-gate",
                    rule="ipd-executed-gate",
                    detail="gate refused",
                )
            )
        res = CommandResult(
            command="ipd-executed-gate",
            status="clean" if exit_code == 0 else "findings",
            exit_code=exit_code,
            summary=(
                "ipd-executed-gate: gate passed"
                if exit_code == 0
                else f"ipd-executed-gate: refused ({len(messages)} finding(s))"
            ),
            diagnostics=diagnostics,
        )
        return get_renderer(ctx).emit(res, ctx)

    if messages:
        sys.stderr.write(
            "aw ipd executed-transition gate REFUSED this commit (local prevention; "
            "the raw plan->executed path bypasses the finalize gates):\n"
        )
        for m in messages:
            sys.stderr.write(f"  - {m}\n")
        sys.stderr.write(
            "(This is a LOCAL best-effort hook; `--no-verify` bypasses it and the local `aw check`/"
            "`aw doctor` proclint detector is the backstop.)\n"
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
