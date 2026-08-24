"""Local pre-commit gate: flag a raw (untooled) INTERMEDIATE plan status change (proclint 79li67).

The `ipdgates` Set gates the high-stakes TERMINAL transition (a plan -> `executed`): Order dulzpy's
pre-commit hook refuses a raw `git commit` of a plan that gained `- Status: executed`/`done` or was
moved into `executed/` without a finalize journal. But NOTHING catches a hand-edited INTERMEDIATE
transition (`draft`->`to-review`->`reviewed`->`approved`), and `approved` is a trust boundary. This
LOCAL pre-commit hook is the INTERMEDIATE-transition SIBLING of Order dulzpy.

It inspects the STAGED change and, for each PLAN whose `- Status:` changed in this commit with NO
matching tool-authored `## Workflow history` transition line for the new status, REFUSES the commit
with an actionable `aw set <status> <id6>` message. `aw set`/`aw ipd set` append
`- <date> <status> (<actor>): <message>` on every transition (status_set.py:504); a staged status
change with no such line is the fingerprint of a careless hand-edit.

Honest limits (never oversold): this is PREDICATE A (textual) - it catches only the CARELESS omission
(a status flip with no note added). It does NOT catch a hand-edit that also writes a plausible history
line; that limit is accepted (this is a safety net, the preventive layer is the `aw set` delegation +
the `ipdgates` gates). Git hooks are LOCAL, not cloned by default, and skippable with `--no-verify`.
There is deliberately NO remote/CI enforcement (local only, mirroring Order dulzpy's human decision);
the same detector also rides `aw check`/`aw doctor` (over changed files) as the deterministic backstop.

Commit-scoping means historical records are never examined (NO grandfathering) and `executed/` records
are excluded (terminal; a move OUT of `executed/` is a staged change and IS checked). Only plan IPDs
are examined - history-less types (prompts/releases) carry no `## Workflow history` and are excluded.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple


def check(repo_root: Optional[Path] = None) -> Tuple[int, List[str]]:
    """Run the gate. Returns (exit_code, messages). exit 0 = ok/no-op, 1 = refused.

    Delegates detection to the ONE commit-scoped rule in ``check_engine.check_status_untooled`` (the
    same rule ``aw check``/``aw doctor`` surface), so the hook and the check never diverge.
    """
    from agent_workflows import check_engine as _ce

    root = Path(repo_root) if repo_root is not None else Path(".")
    drift = _ce.check_status_untooled(root)
    if not drift:
        return 0, []  # fast no-op: no untooled plan status change staged
    return 1, [f"{d.location}: {d.detail}" for d in drift]


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry for the pre-commit hook. Prints refusals to stderr; exits 0 (ok) or 1 (refused)."""
    import sys

    exit_code, messages = check()
    if messages:
        sys.stderr.write(
            "aw untooled-status gate REFUSED this commit (local prevention; a plan's `- Status:` "
            "changed with no attributed `## Workflow history` line - it looks hand-edited):\n"
        )
        for m in messages:
            sys.stderr.write(f"  - {m}\n")
        sys.stderr.write(
            "(This is a LOCAL best-effort hook; `--no-verify` bypasses it, a hand-edit that also "
            "adds a plausible history line evades it, and `aw check`/`aw doctor` is the backstop.)\n"
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
