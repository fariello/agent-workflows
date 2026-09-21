"""`aw ipd recheck-readiness`: RE-EVALUATE a stale `- Readiness: no-go` instead of stranding a plan.

Set rdyrecheck, Order 01 (plan qhy3i3). This module is the CLI SURFACE only; every judgement it
renders is computed in :mod:`agent_workflows.plan_readiness` and :mod:`agent_workflows.review_findings`,
so there is exactly one encoding of each rule and this file cannot drift from the gates it reports on.

THE DEFECT IT ADDRESSES. A `- Readiness: no-go` records a MOMENT, not a condition. Nothing
re-evaluates it when the cause it was set for is removed, and the refusal that reads the field has NO
override by design (`plan_readiness.approval_refusals`: "get the review's readiness changed (re-run
/plan-review) rather than forcing the approval"). So a plan whose blocking question has been ANSWERED
stayed permanently unapprovable, and the only sanctioned remedy was a full re-review of a document
whose findings were already swept to LOW.

WHY THIS VERB IS LEGITIMATE AT ALL, since `AGENTS.md` forbids an agent hand-writing a `- Readiness:`.
The prohibition is NOT relaxed. Three properties make the difference, and each is pinned by a test in
``tests/test_plan_readiness_recheck.py``:

  1. It COMPUTES the value from the three conditions the plan-review contract enumerates, using the
     shipped predicates; it forks none of them.
  2. It can only ever write `no-go` -> `go-pending-approval`, a state that STILL REQUIRES a human.
     `go` is unreachable here by construction: `plan_readiness.recheck_readiness` has no parameter
     that selects the target and asserts the observable written value.
  3. It RECORDS its computed evidence in the plan's own history, labelled a re-check, so the value
     carries its basis exactly as a review's verdict does and `newest_verdict` still resolves to the
     REVIEW record rather than to the re-check.

DRY RUN IS THE DEFAULT, matching `aw ipd scaffold` and `aw ipd sync`. This verb edits an attestation
field, and the preview is what lets a human check the computed reasons before anything is written.
"""

from __future__ import annotations

import argparse
import os
from datetime import date as _date
from pathlib import Path
from typing import List, Sequence, Tuple

from agent_workflows import plan_readiness as PR

#: Dispositions swept when no selector is given. A TERMINAL plan (`executed/`, `superseded/`,
#: `not-executed/`) is deliberately NOT swept: re-checking a plan whose disposition is already
#: settled would rewrite history to no purpose, and a superseded plan's `no-go` is an accurate record
#: of why it was retired. A named selector still reaches one, so the sweep is a default rather than a
#: restriction.
SWEEP_DISPOSITIONS: Tuple[str, ...] = ("pending", "reusable")


def _repo_root(args: argparse.Namespace) -> Path:
    d = getattr(args, "dir", None)
    return Path(d) if d else Path.cwd()


def _actor(args: argparse.Namespace) -> str:
    explicit = getattr(args, "actor", None)
    if explicit:
        return str(explicit)
    return os.environ.get("AW_IPD_AUTHOR") or "agent (aw ipd recheck-readiness)"


def _head(repo_root: Path) -> str:
    """The current commit, for the evidence line. Empty when it cannot be read (never raises)."""
    import subprocess

    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def _sweep_paths(repo_root: Path) -> List[Path]:
    plans = repo_root / ".aw" / "records" / "plans"
    out: List[Path] = []
    for disp in SWEEP_DISPOSITIONS:
        d = plans / disp
        if d.is_dir():
            out.extend(sorted(d.glob("*.ipd.md")))
    return out


def _resolve(repo_root: Path, selectors: Sequence[str]) -> Tuple[List[Path], List[str]]:
    """Selector tokens -> plan paths, plus the tokens that resolved to nothing.

    A direct PATH is accepted before the selector resolver is consulted, so a caller can re-check a
    file the resolver does not index (a fixture, or a plan outside the records tree). Unresolved
    tokens are RETURNED rather than ignored: a typo that silently re-checks nothing would report a
    clean sweep over an empty set, which is the false-clean this whole area exists to avoid.
    """
    if not selectors:
        return _sweep_paths(repo_root), []
    paths: List[Path] = []
    missing: List[str] = []
    seen = set()
    for tok in selectors:
        p = Path(tok)
        if p.is_file():
            if str(p) not in seen:
                seen.add(str(p))
                paths.append(p)
            continue
        try:
            from agent_workflows import selectors as _sel

            found = _sel.resolve_selectors(repo_root, "plans", [tok])
        except Exception:
            found = []
        if not found:
            missing.append(tok)
            continue
        for f in found:
            if str(f) not in seen:
                seen.add(str(f))
                paths.append(Path(f))
    return paths, missing


class _Row:
    """One plan's outcome, carrying BOTH halves so a report can never state an action without a cause."""

    def __init__(self, path: Path, result: "PR.RecheckResult"):
        self.path = path
        self.result = result
        self.action = "refused"
        self.stale: Tuple = ()
        self.stale_applied = False
        self.detail = ""


def _run_stale_findings(
    repo_root: Path, path: Path, apply: bool, actor: str, today: str
) -> Tuple[Tuple, bool, str]:
    """The escalation RETURN PATH for one plan: report, and under ``apply`` append a closing round.

    Returns ``(stale, applied, detail)``. Reports nothing and writes nothing when the plan carries no
    resolved question whose `- Finding:` reference names a currently-blocking finding, which is the
    NEGATIVE case: an unanswered question leaves its finding blocking.
    """
    from agent_workflows import review_findings as RF

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return (), False, "unreadable: {0}".format(exc)
    import re

    m = re.search(r"(?m)^-\s*Id:\s*([0-9a-z]{6})\s*$", text)
    if not m:
        return (), False, "no `- Id:` bullet, so no review record can be matched"
    stale = RF.stale_escalated_findings(repo_root, m.group(1), text)
    if not stale:
        return (), False, ""
    if not apply:
        return stale, False, "dry-run: no round appended"
    # Group by review record: one appended round closes every stale finding in that record at once,
    # rather than appending a round per finding, which would fragment one event across rounds.
    by_record: dict = {}
    for s in stale:
        by_record.setdefault(s.review_path, []).append(s)
    applied = False
    details: List[str] = []
    for review_path, items in sorted(by_record.items()):
        new_text = RF.append_round_resolving_stale(
            review_path, items, date=today, actor=actor, apply=True
        )
        if new_text is None:
            details.append(
                "refused to amend {0} (unparseable or no current round)".format(
                    review_path
                )
            )
            continue
        applied = True
        details.append(
            "appended a round to {0} marking {1} fixed".format(
                review_path, ", ".join(s.finding_id for s in items)
            )
        )
    return stale, applied, "; ".join(details)


def run_recheck_readiness(args: argparse.Namespace) -> int:
    """Recompute, report per condition, and write only when every condition is clear.

    Exit contract: 0 when the sweep completed (whether or not anything was written; a REFUSAL is a
    correct outcome and not an error), 1 when a named selector resolved to nothing, 2 when the verb
    could not run at all.
    """
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        Change,
        CommandResult,
        Diagnostic,
        select_output,
    )

    ctx = select_output(args)
    repo_root = _repo_root(args)
    apply = bool(getattr(args, "apply", False))
    want_stale = bool(getattr(args, "stale_findings", False))
    actor = _actor(args)
    today = _date.today().isoformat()
    head = _head(repo_root)

    selectors = list(getattr(args, "selectors", None) or [])
    paths, missing = _resolve(repo_root, selectors)

    if not paths and not missing:
        summary = "no plans to re-check (swept {0})".format(
            ", ".join(SWEEP_DISPOSITIONS)
        )
        if ctx.is_agent or ctx.is_json:
            return get_renderer(ctx).emit(
                CommandResult(
                    command="ipd recheck-readiness",
                    status="clean",
                    exit_code=0,
                    summary=summary,
                    changes=[],
                    verified=True,
                    complete=True,
                ),
                ctx,
            )
        print(summary)
        return 0

    rows: List[_Row] = []
    for path in paths:
        # THE STALE-FINDING HALF RUNS FIRST, deliberately. It can CHANGE the second condition's answer
        # (a closed finding stops blocking), so running the readiness recompute first would report a
        # refusal the same invocation then invalidates.
        stale: Tuple = ()
        stale_applied = False
        stale_detail = ""
        if want_stale:
            stale, stale_applied, stale_detail = _run_stale_findings(
                repo_root, path, apply, actor, today
            )
        result, new_text = PR.recheck_readiness(
            repo_root, path, apply=apply, date=today, actor=actor, head=head
        )
        row = _Row(path, result)
        row.stale = stale
        row.stale_applied = stale_applied
        if result.may_write:
            row.action = "updated" if apply else "would-update"
            row.detail = "`{0}` -> `{1}`".format(
                PR.RECHECK_SOURCE_READINESS, PR.RECHECK_TARGET_READINESS
            )
        else:
            row.detail = "; ".join(result.refusals)
        if stale_detail:
            row.detail = (row.detail + " | stale findings: " + stale_detail).strip(" |")
        rows.append(row)

    written = [r for r in rows if r.action == "updated"]
    would = [r for r in rows if r.action == "would-update"]
    refused = [r for r in rows if r.action == "refused"]
    summary = "{0} plan(s) re-checked: {1} {2}, {3} refused (each refusal names its surviving cause)".format(
        len(rows),
        len(written) + len(would),
        "updated" if apply else "would update",
        len(refused),
    )

    if ctx.is_agent or ctx.is_json:
        changes = [
            Change(
                path=str(r.path),
                kind="update",
                applied=(r.action == "updated"),
                detail=r.detail,
            )
            for r in rows
            if r.action != "refused"
        ]
        diagnostics = [
            Diagnostic(
                location=str(r.path),
                rule="readiness.recheck-refused",
                detail=r.detail,
                severity="info",
            )
            for r in refused
        ]
        diagnostics.extend(
            Diagnostic(
                location=tok,
                rule="readiness.selector-unresolved",
                detail="selector matched no plan",
                severity="error",
            )
            for tok in missing
        )
        return get_renderer(ctx).emit(
            CommandResult(
                command="ipd recheck-readiness",
                status="findings" if missing else "clean",
                exit_code=1 if missing else 0,
                summary=summary,
                changes=changes,
                diagnostics=diagnostics,
                verified=True,
                complete=True,
            ),
            ctx,
        )

    for tok in missing:
        print("error: selector matched no plan: {0}".format(tok))
    for r in rows:
        print("")
        print("{0}  [{1}]".format(r.result.id6 or r.path.name, r.action))
        print("  path: {0}".format(r.path))
        print(
            "  readiness: {0}".format(r.result.readiness or "(absent or out-of-vocab)")
        )
        for cond in r.result.conditions:
            print(
                "  {0} {1}: {2}".format(
                    "HOLDS " if cond.holds else "clear ", cond.name, cond.reason
                )
            )
        for s in r.stale:
            print("  stale-escalation: {0}".format(s.describe()))
        if r.action == "refused":
            for reason in r.result.refusals:
                print("  REFUSED: {0}".format(reason))
        else:
            print("  {0}: {1}".format(r.action, r.detail))
    print("")
    print(summary)
    if not apply and (would or any(r.stale for r in rows)):
        print("(dry-run: nothing was written. Pass --apply to write.)")
    return 1 if missing else 0
