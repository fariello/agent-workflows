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
boundary is phase-5 CI running the same engine. The exit code follows the shared severity convention:
``info`` is reported and does not refuse (exit 0), while ``warning`` and ``error`` refuse (exit 1),
because an advisory tier that refuses a commit is a gate nobody decided on and the tier is relied on
as a parking place for an undecided rule (backlog ``p4hmpz``). A rule's internal error is isolated by
the aggregator so it never fails the commit open on an unrelated crash.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple


def check(repo_root: Optional[Path] = None) -> Tuple[int, List[str]]:
    """Run the gate. Returns (exit_code, messages). Exit code follows the shared severity convention:
    exit 0 = ok/no-op/advisory-only, 1 = refused (warning or error findings).

    Delegates to the ONE shared aggregator ``check_engine.check_commit_invariants`` (which re-invokes
    the existing shared rules), so the hook and ``aw check`` never diverge. Each message names the
    rule and its exact recovery command (teaching error). Advisories (``info``) are reported in
    messages but do not refuse the commit (exit 0), because an advisory tier that refuses a commit
    is a gate nobody decided on and the tier is relied on as a parking place for an undecided rule
    (backlog ``p4hmpz``).
    """
    from agent_workflows import artifact_core as _ac
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
    normalized = [
        d if getattr(d, "severity", "") else _ce.enrich_drift(d) for d in drift
    ]
    return _ac.drift_exit_code(normalized), messages


def main(argv: Optional[List[str]] = None, args: Optional[object] = None) -> int:
    """CLI entry for the pre-commit hook. Emits envelope on --agent
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
            loc = "precommit-scope-gate"
            rule = "precommit-scope-gate"
            det = m
            parts = m.split(": ", 2)
            if len(parts) >= 3:
                loc = parts[0]
                rule = parts[1]
                det = parts[2]
            elif len(parts) == 2:
                loc = parts[0]
                det = parts[1]
            diagnostics.append(Diagnostic(location=loc, rule=rule, detail=det))
        if exit_code != 0 and not diagnostics:
            diagnostics.append(
                Diagnostic(
                    location="precommit-scope-gate",
                    rule="precommit-scope-gate",
                    detail="gate refused",
                )
            )
        if exit_code == 0:
            summary = (
                f"precommit-scope-gate: gate passed ({len(messages)} advisory finding(s))"
                if messages
                else "precommit-scope-gate: gate passed"
            )
        else:
            summary = f"precommit-scope-gate: refused ({len(messages)} finding(s))"
        res = CommandResult(
            command="precommit-scope-gate",
            status="clean" if exit_code == 0 else "findings",
            exit_code=exit_code,
            summary=summary,
            diagnostics=diagnostics,
        )
        return get_renderer(ctx).emit(res, ctx)

    if messages:
        if exit_code != 0:
            sys.stderr.write(
                "aw pre-commit scope/invariant gate REFUSED this commit (local prevention; a staged "
                "change violates a repository invariant or falls outside a plan's declared Scope-Paths):\n"
            )
        else:
            sys.stderr.write(
                "aw pre-commit scope/invariant gate REPORTED advisory findings (commit not refused; "
                "advisory detect-and-nudge):\n"
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
