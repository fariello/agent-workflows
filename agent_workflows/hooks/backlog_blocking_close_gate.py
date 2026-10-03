"""Local pre-commit gate: refuse committing a release-blocking backlog item closed to `done`
without a preserved-or-satisfied gate (bklggrad f1dhht; child 03 of the close-legitimacy Set).

The child-02 setter gate (`aw backlog set done`, backlog.run_set -> check_engine.evaluate_blocking_close)
refuses an illegitimate blocking close. But that gate can be BYPASSED by hand-editing a backlog file
(flip `- Status: done`, move it into `done/`) and committing directly, which silently drops a release
gate - exactly the hand-edit bypass the findings doc (bu9yij, section 7.7) says a local pre-commit hook
should catch. This hook is that bypass-catcher.

It inspects the STAGED change and, for each backlog item newly showing `- Status: done` (or moved into
`done/`) that carries `- Blocks-Release:` with no legitimate gate, REFUSES the commit with a teaching
message naming the three fixes. It delegates the legitimacy decision to the SINGLE shared predicate
`check_engine.evaluate_blocking_close` (via `check_engine.check_release_gate_consistency`'s commit-scoped
`check.blocking-item-closed-without-gate` rule), so the hook, the setter, and `aw check` can never
diverge. Per OQ-01 the hook gates the fail-closed `done` case ONLY (blocking->parked / priority-demote
WARNs are surfaced by `aw check`/`aw attention`, not at commit time).

Commit-time legitimacy is reconstructed from PERSISTED state only (the predicate is called WITHOUT an
`evidence=` arg): HANDOFF (EVERY same-gate `From-Backlog` carrier present in the staged tree with the
same `Blocks-Release` must be executed or implemented) and DE-GATED (`Blocks-Release` absent from the
staged item) are decidable from the staged tree. A transient `--evidence` CLI arg is NOT visible to the
hook, but the setter now durably persists the citation as a `- Close-Evidence:` bullet (gateatrest
f7igdu, via `backlog.set_close_evidence_line`), so the SATISFIED path IS honored from persisted state.

Honest limits (never oversold): git hooks are LOCAL, not cloned by default, and skippable with
`--no-verify`. This hook is OPT-IN (NOT installed by default) - the authoritative, portable boundary is
the child-02 `aw check` rule (`check.blocking-item-closed-without-gate`) + CI (wired later by the
agentadhere Phase-5 child), never the local hook alone. Commit-scoping means historical `done/` items
closed before this guard existed are grandfathered (never retroactively flagged).
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

_RULE = "check.blocking-item-closed-without-gate"


def check(repo_root: Optional[Path] = None) -> Tuple[int, List[str]]:
    """Run the gate. Returns (exit_code, messages). exit 0 = ok/no-op, 1 = refused.

    Delegates detection to the ONE commit-scoped rule in
    ``check_engine.check_release_gate_consistency`` (the same predicate the setter and ``aw check``
    use), filtered to the fail-closed ``done`` case (``check.blocking-item-closed-without-gate``), so
    the hook and the check never diverge. Fast no-op when no backlog done-close is staged.
    """
    from agent_workflows import check_engine as _ce

    root = Path(repo_root) if repo_root is not None else Path(".")
    drift = [d for d in _ce.check_release_gate_consistency(root) if d.rule == _RULE]
    if not drift:
        return 0, []
    return 1, [f"{d.location}: {d.detail}" for d in drift]


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
            loc = "backlog-blocking-close-gate"
            det = m
            if ": " in m:
                parts = m.split(": ", 1)
                loc = parts[0]
                det = parts[1]
            diagnostics.append(Diagnostic(location=loc, rule=_RULE, detail=det))
        if exit_code != 0 and not diagnostics:
            diagnostics.append(
                Diagnostic(
                    location="backlog-blocking-close-gate",
                    rule=_RULE,
                    detail="gate refused",
                )
            )
        res = CommandResult(
            command="backlog-blocking-close-gate",
            status="clean" if exit_code == 0 else "findings",
            exit_code=exit_code,
            summary=(
                "backlog-blocking-close-gate: gate passed"
                if exit_code == 0
                else f"backlog-blocking-close-gate: refused ({len(messages)} finding(s))"
            ),
            diagnostics=diagnostics,
        )
        return get_renderer(ctx).emit(res, ctx)

    if messages:
        sys.stderr.write(
            "aw backlog-blocking-close gate REFUSED this commit (local prevention; a "
            "release-blocking backlog item was closed to `done` without a preserved-or-satisfied "
            "gate - it looks hand-edited, bypassing `aw backlog set done`):\n"
        )
        for m in messages:
            sys.stderr.write(f"  - {m}\n")
        sys.stderr.write(
            "Fix via one of: hand the gate to a plan (`- From-Backlog: <id6>` + the same "
            "`- Blocks-Release:` on a plan), clear it (`aw backlog set done <item> --blocks-release -`), "
            "or cite evidence (`aw backlog set done <item> --evidence <path>`).\n"
            "(This is a LOCAL best-effort, OPT-IN hook; `--no-verify` bypasses it; the portable "
            "authority is the `aw check` rule + CI.)\n"
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
