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

Finalize evidence (DECISION 14-dulzpy-D1): `aw ipd finalize` leaves, at commit time, a durable
transaction JOURNAL under `.aw/state/runtime/transactions/ipd_finalize_<id6>.json` whose phase is a
finalize-transaction phase (`ready-to-commit` during finalize's own commit, then `committed-incomplete`
/`complete`) and which records the plan id + the executed destination path. The hook accepts a
plan->executed staged transition iff such a journal exists for the plan (matching id + dest), which
faithfully realizes OQ-01's "finalize ran this transition" predicate against the artifacts finalize
actually leaves (the begin receipt carries the pending-time digest and is consumed only after the
commit, so the journal is the present-at-commit-time proof). A raw hand-edit has NO such journal.
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


def check(repo_root: Optional[Path] = None) -> Tuple[int, List[str]]:
    """Run the gate. Returns (exit_code, messages). exit 0 = ok/no-op, 1 = refused."""
    root = _repo_root(repo_root or Path("."))
    transitions = _staged_plan_executed_transitions(root)
    if not transitions:
        return 0, []  # fast no-op: no plan executed-transition staged

    refusals: List[str] = []
    for staged_path, plan_id, reason in transitions:
        if plan_id is None:
            refusals.append(
                f"{staged_path}: this plan is being moved to executed ({reason}) but has no readable "
                "'- Id:' handle to verify a finalize receipt against; run `aw ipd finalize` instead."
            )
            continue
        if not _finalize_evidence_ok(root, plan_id, staged_path):
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
