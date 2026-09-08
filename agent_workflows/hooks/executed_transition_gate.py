"""Local pre-commit gate: refuse a raw (non-finalize) plan-to-`executed` commit (ipdgates Order dulzpy).

Order 07 delegates the CLI path (`aw set executed`) into the gated `aw ipd finalize`, but it cannot
cover the path where an agent NEVER touches the CLI: hand-editing a plan's `- Status:` to `executed`
(or `git mv`-ing a plan into `executed/`) and then committing with a raw `git commit`. That commit runs
no finalize - no receipt, no scope check, no attribution - the exact p7dqwz-class bypass via the editor.

This LOCAL pre-commit hook inspects the STAGED change and, for each PLAN that in this commit either
gained a `- Status: executed`/`done` line it did not have at HEAD, OR was renamed into an `executed/`
directory, REQUIRES durable evidence that `aw ipd finalize` performed THIS transition. Missing/stale
evidence -> the commit is REFUSED with an actionable `aw ipd finalize <plan>` message.

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
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

# The finalize-transaction journal phases that prove finalize is performing / performed THIS
# transition (present at commit time). Imported lazily to keep this module import-light.
_FINALIZE_PHASES = ("ready-to-commit", "committed-incomplete", "complete")

_PLANS_PREFIX = ".aw/records/plans/"
_EXECUTED_SEGMENT = "/executed/"
_STATUS_EXECUTED_LINE = "- status: executed"
_STATUS_DONE_LINE = "- status: done"


def _git(repo_root: Path, args: List[str]) -> Tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
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


def _blob_at(repo_root: Path, ref: str, path: str) -> Optional[str]:
    """The content of ``path`` at ``ref`` (e.g. HEAD or the staged index ``:0:``), or None if absent."""
    spec = f"{ref}:{path}" if ref != ":0:" else f":0:{path}"
    rc, out, _err = _git(repo_root, ["show", spec])
    if rc != 0:
        return None
    return out


def _has_executed_status(text: Optional[str]) -> bool:
    """True if the plan text carries a metadata `- Status: executed` (or `done` alias) line."""
    if not text:
        return False
    for line in text.splitlines():
        low = line.strip().lower()
        if low == _STATUS_EXECUTED_LINE or low == _STATUS_DONE_LINE:
            return True
    return False


def _plan_id_of(text: Optional[str]) -> Optional[str]:
    """Read the `- Id:` id6 from plan text (staged content)."""
    if not text:
        return None
    import re

    m = re.search(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$", text)
    return m.group(1) if m else None


def _staged_plan_executed_transitions(
    repo_root: Path,
) -> List[Tuple[str, Optional[str], str]]:
    """Return (staged_path, plan_id, reason) for each plan gaining executed status / moved to executed/.

    Detection compares the STAGED index (`:0:`) against HEAD:
      * a plan whose staged content has `- Status: executed`/`done` that its HEAD content did NOT
        (a hand-edited status flip), OR
      * a plan renamed INTO an `executed/` directory in this commit (git mv).
    """
    rc, out, _err = _git(
        repo_root, ["diff", "--cached", "--name-status", "-M", "--", _PLANS_PREFIX]
    )
    if rc != 0 or not out.strip():
        return []
    transitions: List[Tuple[str, Optional[str], str]] = []
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
        staged_text = _blob_at(repo_root, ":0:", new_path)
        plan_id = _plan_id_of(staged_text)

        moved_into_executed = _EXECUTED_SEGMENT in ("/" + new_path) and (
            old_path is None or _EXECUTED_SEGMENT not in ("/" + old_path)
        )
        # A status flip: staged content is executed but the HEAD content at the OLD path was not.
        head_text = _blob_at(repo_root, "HEAD", old_path) if old_path else None
        gained_executed = _has_executed_status(
            staged_text
        ) and not _has_executed_status(head_text)

        if moved_into_executed or gained_executed:
            reason = (
                "moved into executed/"
                if moved_into_executed
                else "gained '- Status: executed'"
            )
            transitions.append((new_path, plan_id, reason))
    return transitions


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
        m = re.fullmatch(r"GITHEAD_([0-9a-f]{7,64})", name)
        if not m:
            continue
        sha = m.group(1)
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
    """
    subject = f"lifecycle({plan_id}): finalize"
    for incoming in incoming_commits:
        rc, out, _err = _git(repo_root, ["log", "--format=%s", f"HEAD..{incoming}"])
        if rc != 0:
            continue
        for line in out.splitlines():
            if line.strip().startswith(subject):
                return True
    return False


def check(repo_root: Optional[Path] = None) -> Tuple[int, List[str]]:
    """Run the gate. Returns (exit_code, messages). exit 0 = ok/no-op, 1 = refused."""
    root = _repo_root(repo_root or Path("."))
    transitions = _staged_plan_executed_transitions(root)
    if not transitions:
        return 0, []  # fast no-op: no plan executed-transition staged

    # A merge in progress unlocks the SECOND (in-tree) accepting path, never a blanket exemption.
    # EMPTY means not-a-merge, in which case behavior is byte-identical to before integpath 29wvmj.
    incoming_commits = _merge_incoming_commits(root)

    refusals: List[str] = []
    for staged_path, plan_id, reason in transitions:
        if plan_id is None:
            refusals.append(
                f"{staged_path}: this plan is being moved to executed ({reason}) but has no readable "
                "'- Id:' handle to verify a finalize receipt against; run `aw ipd finalize` instead."
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
                f"'lifecycle({plan_id}): finalize' commit for it, so nothing here shows `aw ipd "
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


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry for the pre-commit hook. Prints refusals to stderr; exits 0 (ok) or 1 (refused)."""
    import sys

    exit_code, messages = check()
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
