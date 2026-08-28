"""OPT-IN local pre-commit gate: run the shared checker over the staged commit and TEACH the fix
(agentadhere Phase 4, IPD diundn E-01).

This is the generalized pre-commit layer over the phase-1 policy engine. Where the earlier gates each
enforce ONE commit-scoped invariant, this hook delegates to the SINGLE aggregating surface
``check_engine.check_commit_invariants`` - which itself only re-invokes the already-shared,
commit/receipt-scoped rules (``check.status-untooled``, ``check.blocking-item-closed-without-gate``,
and the phase-3 ``check.scope-drift`` for a plan with an active begin receipt). Because the hook and
``aw check`` run the SAME rules, they can never diverge; NO policy is forked into the hook.

On a refusal the message TEACHES the recovery path (findings 4.4): it names the violated rule and
prints the exact ``aw ...`` recovery command carried in the finding's ``recovery`` field. The scope
invariant enforced is "staged/changed paths within the plan's declared Scope-Paths" (findings 5.3),
NOT the typed command (a hook cannot reconstruct ``git add -A``).

Honest limits (never oversold): git hooks are LOCAL, not cloned by default, and skippable with
``--no-verify``. This is OPT-IN best-effort FEEDBACK, not an authority boundary; the authoritative
boundary is phase-5 CI running the same engine. Fail-closed on a refusal (exit 1); a rule's internal
error is isolated by the aggregator so it never fails the commit open on an unrelated crash.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple


def check(repo_root: Optional[Path] = None) -> Tuple[int, List[str]]:
    """Run the gate. Returns (exit_code, messages). exit 0 = ok/no-op, 1 = refused.

    Delegates to the ONE shared aggregator ``check_engine.check_commit_invariants`` (which re-invokes
    the existing shared rules), so the hook and ``aw check`` never diverge. Each message names the
    rule and its exact recovery command (teaching error).
    """
    from agent_workflows import check_engine as _ce

    root = Path(repo_root) if repo_root is not None else Path(".")
    drift = _ce.check_commit_invariants(root)
    if not drift:
        return 0, []  # fast no-op: no staged invariant violation
    messages: List[str] = []
    for d in drift:
        recovery = getattr(d, "recovery", "") or ""
        if recovery:
            messages.append(
                f"{d.location}: {d.rule}: {d.detail}\n      fix: {recovery}"
            )
        else:
            messages.append(f"{d.location}: {d.rule}: {d.detail}")
    return 1, messages


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry for the pre-commit hook. Prints refusals to stderr; exits 0 (ok) or 1 (refused)."""
    import sys

    exit_code, messages = check()
    if messages:
        sys.stderr.write(
            "aw pre-commit scope/invariant gate REFUSED this commit (local prevention; a staged "
            "change violates a repository invariant or falls outside a plan's declared Scope-Paths):\n"
        )
        for m in messages:
            sys.stderr.write(f"  - {m}\n")
        sys.stderr.write(
            "(This is a LOCAL best-effort OPT-IN hook; `--no-verify` bypasses it, it is not cloned by "
            "default, and it is NOT an authority boundary - the authoritative gate is `aw check` in "
            "required CI.)\n"
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
