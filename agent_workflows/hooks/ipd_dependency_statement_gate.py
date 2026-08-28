"""OPT-IN local pre-commit gate: refuse a staged IPD with an invalid/cyclic cross-IPD dependency
statement (ipddeps Order mp88bl; spec 25kzda 2.10).

The child-02 `aw check`/`aw ipd lint` enforcement of `Item-Dependencies` can be bypassed by
hand-editing an IPD's statement (or staging a malformed/cyclic one) and committing directly. This
LOCAL, opt-in, COMMIT-SCOPED pre-commit hook catches that at commit time, delegating to the SAME
shared evaluator (`check_engine.evaluate_ipd_dependencies`) that `aw check`/`aw ipd lint` call, so the
hook and the check never diverge (the bklggrad `backlog-blocking-close-gate` / `ipd-status-untooled-
gate` one-predicate model).

Commit-scoping: only STAGED `.ipd.md` files are examined, over a STAGED-OVERLAY snapshot (staged blob
content over the on-disk tree) so a staged edge that introduces/participates in a cycle is caught; a
finding on a file this commit did NOT touch is dropped, so an unrelated commit is never blocked on a
pre-existing finding. Refuses (exit 1) only on a staged MALFORMED / DANGLING / AMBIGUOUS / CYCLIC
statement - and on `unresolved` ONLY where the staged plan is simultaneously advancing to a blocking
phase (its staged `- Status:` is `to-review`/`reviewed`/`approved`/`auto-approved`); a plain draft
carrying `unresolved` is a legitimate honest stub and remains committable (OQ-01, consistent with the
child-02 phase matrix). Prints the SAME `check.ipd-dependency-*` rule IDs + recovery commands as
`aw check`.

Honest limits (never oversold): git hooks are LOCAL, not cloned by default, and skippable with
`--no-verify`. There is deliberately NO CI enforcement here; the portable authority is child-02's
`aw check` rule (+ CI). This is a best-effort local bypass-catcher, not the primary control.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Staged `- Status:` values at/after which an `unresolved` statement should block (advancing to a
# blocking phase). A plain `draft` staying draft is left committable.
_ADVANCING_STATUSES = frozenset(("to-review", "reviewed", "approved", "auto-approved"))

# Only these rules refuse a commit (unresolved is conditionally added per the staged Status).
_HARD_REFUSE_RULES = (
    None  # resolved lazily from ipd_schema to avoid an import at module load
)


def _staged_ipd_overlay(repo_root: Path) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Return (overlay, staged_status) for every staged `.ipd.md`.

    overlay: path_str -> staged blob text (``:0:``); staged_status: path_str -> staged `- Status:`.
    Fast-empty when nothing is staged under a plans tree. Additions/modifications/renames are
    included; pure deletions are skipped (nothing to check).
    """
    from agent_workflows import check_engine as _ce

    overlay: Dict[str, str] = {}
    statuses: Dict[str, str] = {}
    rc, out, _err = _ce._git_capture(
        repo_root, ["diff", "--cached", "--name-status", "-M"]
    )
    if rc != 0 or not out.strip():
        return overlay, statuses
    for line in out.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        code = parts[0].strip()
        if code.startswith("D"):
            continue  # a pure deletion carries no statement to check
        new_path = parts[-1].strip()
        if not new_path.endswith(".ipd.md"):
            continue
        staged_text = _ce._blob_text(repo_root, ":0:", new_path)
        if staged_text is None:
            continue
        abs_ps = str((repo_root / new_path).resolve())
        overlay[abs_ps] = staged_text
        st = _ce._status_meta(staged_text)
        if st is not None:
            statuses[abs_ps] = st.strip().lower()
    return overlay, statuses


def check(repo_root: Optional[Path] = None) -> Tuple[int, List[str]]:
    """Run the gate. Returns (exit_code, messages). exit 0 = ok/no-op, 1 = refused.

    Delegates to the ONE shared ``check_engine.evaluate_ipd_dependencies`` over a staged overlay +
    the staged IPD path set, keeping only findings on staged files. Same rule IDs/messages as
    ``aw check`` (no divergence). Fast no-op when no `.ipd.md` is staged.
    """
    from agent_workflows import check_engine as _ce
    from agent_workflows import ipd_schema as _S

    root = Path(repo_root).resolve() if repo_root is not None else Path(".").resolve()
    overlay, statuses = _staged_ipd_overlay(root)
    if not overlay:
        return 0, []  # fast no-op: no staged IPD

    staged_plans = [(Path(ps), text) for ps, text in overlay.items()]
    # Evaluate at a blocking phase so dangling/ambiguous/cycle/malformed are all errors; the overlay
    # makes the whole-repo graph reflect the staged content.
    drift = _ce.evaluate_ipd_dependencies(
        root, phase="pre-execution", plans=staged_plans, overlay=overlay
    )

    staged_locations = {str(Path(ps).resolve()) for ps in overlay}

    def _on_staged_file(location: str) -> bool:
        try:
            return str(Path(location).resolve()) in staged_locations
        except OSError:
            return location in staged_locations

    hard_rules = {
        _S.RULE_IPD_DEP_MALFORMED,
        _S.RULE_IPD_DEP_DANGLING,
        _S.RULE_IPD_DEP_AMBIGUOUS,
        _S.RULE_IPD_DEP_CYCLE,
    }
    messages: List[str] = []
    for d in drift:
        # Commit-scoping: never block on a finding located in a file this commit did not touch.
        if not _on_staged_file(d.location):
            continue
        if d.rule in hard_rules:
            messages.append(f"{d.location}: {d.rule}: {d.detail}")
        elif d.rule == _S.RULE_IPD_DEP_UNRESOLVED:
            # OQ-01: `unresolved` blocks ONLY when the staged plan is advancing to a blocking phase.
            st = statuses.get(str(Path(d.location).resolve()))
            if st in _ADVANCING_STATUSES:
                messages.append(f"{d.location}: {d.rule}: {d.detail}")
        # MISSING is intentionally NOT hard-refused by the hook (it is cutover-gated policy enforced
        # by `aw check`/lint; a missing statement is not a hand-edited-invalid-statement bypass).
    if messages:
        return 1, messages
    return 0, []


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry for the pre-commit hook. Prints refusals to stderr; exits 0 (ok) or 1 (refused)."""
    import sys

    exit_code, messages = check()
    if messages:
        sys.stderr.write(
            "aw ipd-dependency-statement gate REFUSED this commit (local prevention; a staged IPD's "
            "`- Item-Dependencies` is invalid/cyclic - fix it with `aw ipd dependencies set <id6> "
            "none|<edge...>`):\n"
        )
        for m in messages:
            sys.stderr.write(f"  - {m}\n")
        sys.stderr.write(
            "(This is a LOCAL best-effort OPT-IN hook; `--no-verify` bypasses it, it is not cloned by "
            "default, and `aw check`/CI is the portable authority.)\n"
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
