"""Read-only reporting over the typed review records (revgate Order 04, `c621h9` E-04).

WHAT THIS IS FOR. The `plan-review` workflow tells a reviewer to resolve a question from
authoritative evidence rather than asking the human. That rule is right, but it converts questions
into SILENT CHOICES: a reviewer can make ten judgement calls, get one badly wrong, and the maintainer
discovers it only by reading the code it produced. Order 01 (`15zvu6`) gave the review record a typed
`### Decisions` section; this module is the one command that reads it back, so "the agent decided this
itself" becomes a durable, queryable fact instead of a line in a transcript nobody re-reads.

WHY A SEPARATE MODULE. `cli.py` owns registration and dispatch only, matching the owner-verb shape
`specs`/`backlog`/`research` already use: a module with `run_*` entry points that `cli.py` calls. This
verb is the FIRST inhabitant of the `reviews` CLI namespace, which did not exist before it.

STRICTLY READ-ONLY. Nothing here writes, moves, or mutates any file. There is no `--apply`, because
there is nothing to apply. Parsing is delegated to `review_findings` (pure, never raises) and
discovery to the record-path authority via `review_findings.review_dirs`, so this module holds no
`.aw/records/reviews` path literal of its own and cannot disagree with the writer about where reviews
live.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Sequence

#: The `Reversible` cell values that mean IRREVERSIBLE.
#:
#: Compared case-insensitively after stripping. Deliberately a small explicit set rather than
#: "anything that is not yes": a typo like `Reversibel` must NOT silently become "irreversible" and
#: manufacture an escalation obligation, nor silently become "reversible" and hide one. An
#: unrecognized value is reported as `unknown` by :func:`classify_reversible` so it is visible.
_IRREVERSIBLE = ("no", "n", "false", "irreversible")

#: The `Reversible` cell values that mean REVERSIBLE.
_REVERSIBLE = ("yes", "y", "true", "reversible")


def classify_reversible(value: str) -> str:
    """Normalize a `Reversible` cell to ``"yes"``, ``"no"``, or ``"unknown"``.

    ``unknown`` covers both an EMPTY cell and an unrecognized token, and the two are deliberately not
    distinguished: in either case the reviewer did not make the judgement the workflow asks for, and a
    reader must not be told a decision is safely reversible on the strength of a blank.
    """
    tok = (value or "").strip().lower().rstrip(".")
    if tok in _REVERSIBLE:
        return "yes"
    if tok in _IRREVERSIBLE:
        return "no"
    return "unknown"


class DecisionRow(NamedTuple):
    """One recorded decision, joined to the review and round it came from.

    Carries enough context to be actionable on its own line of output: which plan was being reviewed,
    which round recorded it, and where the file is, so a maintainer can go read the surrounding
    findings without a second lookup.
    """

    plan_id: str
    review_path: Path
    round_number: int
    is_current_round: bool
    id: str
    question: str
    chosen: str
    alternatives: str
    basis: str
    reversible_raw: str
    line: int

    @property
    def reversible(self) -> str:
        """``"yes"``, ``"no"``, or ``"unknown"`` (see :func:`classify_reversible`)."""
        return classify_reversible(self.reversible_raw)

    @property
    def is_irreversible(self) -> bool:
        """True for a row the reviewer marked irreversible.

        An `unknown` value is NOT counted as irreversible here: `--irreversible` answers "show me the
        decisions that cannot be undone", and padding it with unclassified rows would dilute exactly
        the list a maintainer reaches for first. Unknown rows still appear in the unfiltered listing,
        and the summary counts them separately so they are not lost.
        """
        return self.reversible == "no"

    def to_dict(self, repo_root: Optional[Path] = None) -> Dict[str, Any]:
        path = str(self.review_path)
        if repo_root is not None:
            try:
                path = str(self.review_path.relative_to(repo_root))
            except ValueError:
                pass
        return {
            "plan_id": self.plan_id,
            "review": path,
            "round": self.round_number,
            "current_round": self.is_current_round,
            "id": self.id,
            "question": self.question,
            "chosen": self.chosen,
            "alternatives": self.alternatives,
            "basis": self.basis,
            "reversible": self.reversible,
            "reversible_raw": self.reversible_raw,
            "line": self.line,
        }


def collect_decisions(
    repo_root,
    *,
    paths: Optional[Sequence[Path]] = None,
    current_round_only: bool = False,
) -> tuple:
    """Gather every recorded decision, plus any parse diagnostics.

    Returns ``(rows, diagnostics)`` where ``rows`` is a list of :class:`DecisionRow` sorted by
    ``(plan_id, review path, round, decision id)`` for deterministic output, and ``diagnostics`` is a
    list of ``(path, Diagnostic)`` pairs.

    ALL ROUNDS ARE INCLUDED BY DEFAULT, unlike the gating rules, which read the current round only.
    That difference is deliberate and is the point of an audit trail: a gate asks "does this plan
    block TODAY", so a superseded finding must stop counting; an audit asks "what did the agents
    decide", and a decision made in round 1 was still made. Pass ``current_round_only=True`` for the
    gate-shaped view (which `check_engine` does).

    Diagnostics are RETURNED, not raised and not printed. A malformed review is a fact the caller
    reports; this function has no opinion about exit codes.
    """
    from agent_workflows import review_findings as _rf

    repo_root = Path(repo_root)
    rows: List[DecisionRow] = []
    diags: List[tuple] = []

    if paths is None:
        candidates = list(_rf.iter_review_files(repo_root))
    else:
        candidates = [Path(p) for p in paths]

    for path in candidates:
        doc = _rf.parse_review_file(path)
        for d in doc.diagnostics:
            diags.append((path, d))
        current = doc.current_round()
        cur_no = current.number if current is not None else None
        for rnd in doc.rounds:
            is_cur = cur_no is not None and rnd.number == cur_no and rnd is current
            if current_round_only and not is_cur:
                continue
            for dec in rnd.decisions:
                rows.append(
                    DecisionRow(
                        plan_id=doc.plan_id,
                        review_path=path,
                        round_number=rnd.number,
                        is_current_round=is_cur,
                        id=dec.id,
                        question=dec.question,
                        chosen=dec.chosen,
                        alternatives=dec.alternatives,
                        basis=dec.basis,
                        reversible_raw=dec.reversible,
                        line=dec.line,
                    )
                )

    rows.sort(key=lambda r: (r.plan_id, str(r.review_path), r.round_number, r.id))
    return rows, diags


def _resolve_selector_paths(repo_root: Path, selector: str) -> tuple:
    """Resolve one selector to review file(s) through the ONE shared resolver.

    Returns ``(paths, note)``. ``note`` is a human-facing explanation when the selector resolved to
    nothing, so the caller never has to invent one.

    WHICH SELECTOR KINDS ACTUALLY WORK, stated honestly because one of them cannot (E-04/F-13). The
    shared resolver's `id6` rule matches a `- Id:` front-matter bullet, but a review artifact carries
    `- Plan-Id:` instead (Order 01 chose that name so the field says whose id6 it is). So an id6
    selector does NOT match a review's front matter. It still resolves, via the `stem`/`substring`
    rules, because the artifact-naming grammar embeds the reviewed plan's id6 in the FILENAME. The
    practical consequence for a caller: `aw reviews decisions c621h9` works, and it works by filename,
    not by front matter. `path` and `setid`-shaped filename matches work the same way. We do NOT
    promise an exact-front-matter `id6` match the artifact cannot support.
    """
    from agent_workflows import selectors as _sel

    tok = (selector or "").strip()
    if not tok:
        return [], ""

    direct = Path(tok)
    if direct.is_file():
        return [direct], ""

    try:
        paths = _sel.resolve_selectors(repo_root, "reviews", [tok])
    except Exception as exc:  # pragma: no cover - resolver is defensive already
        return [], "selector could not be resolved: {0}".format(exc)

    paths = [p for p in paths if p.name.endswith(".review.md")]
    if paths:
        return paths, ""

    # No review matched. Distinguish "no reviews exist at all" from "this selector matched none",
    # because the recovery differs: the first needs a review to be written, the second a better
    # selector.
    from agent_workflows import review_findings as _rf

    any_reviews = any(True for _ in _rf.iter_review_files(repo_root))
    if not any_reviews:
        return [], "no review records exist yet, so no selector can match one"
    return (
        [],
        "no review record matches `{0}` (reviews are matched by FILENAME, which embeds the "
        "reviewed plan's id6; the front matter carries `Plan-Id:` rather than `Id:`)".format(
            tok
        ),
    )


def run_decisions(args) -> int:
    """`aw reviews decisions [<selector>]`: print the decisions agents made without asking.

    Read-only. Exit contract is ``(0, 2)``: 0 whether or not any decision was found (an empty audit
    trail is a legitimate answer, not a failure), and 2 only for a usage error such as conflicting
    output flags. There is deliberately NO exit 1: this verb REPORTS, it does not judge, and the
    judging is `check.review-decision-unescalated`'s job. Declaring an exit-1 contract would also
    oblige a `domain_failure` conformance scenario this printer cannot produce.
    """
    from agent_workflows.project_context import resolve_verb_repo_root
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic,
        Evidence,
        NextAction,
        select_output,
    )

    ctx = select_output(args)
    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    selector = getattr(args, "selector", None)
    only_irreversible = bool(getattr(args, "irreversible", False))

    note = ""
    paths: Optional[List[Path]] = None
    if selector:
        resolved, note = _resolve_selector_paths(repo_root, selector)
        paths = list(resolved)

    rows, diags = collect_decisions(repo_root, paths=paths)
    if only_irreversible:
        rows = [r for r in rows if r.is_irreversible]

    n_irrev = sum(1 for r in rows if r.reversible == "no")
    n_unknown = sum(1 for r in rows if r.reversible == "unknown")
    plans = sorted({r.plan_id for r in rows if r.plan_id})

    if rows:
        summary = "{0} recorded decision(s) across {1} reviewed plan(s)".format(
            len(rows), len(plans)
        )
        if n_irrev:
            summary += "; {0} marked irreversible".format(n_irrev)
        if n_unknown:
            summary += "; {0} with no Reversible judgement".format(n_unknown)
    elif only_irreversible:
        summary = "no irreversible recorded decisions"
    elif note:
        summary = note
    else:
        summary = "no decisions recorded"

    diagnostics = [
        Diagnostic(
            location="{0}:{1}".format(p, d.line),
            rule="reviews.decision-parse",
            detail="{0} {1}".format(d.code, d.message),
            severity="warning",
        )
        for (p, d) in diags
    ]

    if ctx.is_agent or ctx.is_json:
        res = CommandResult(
            command="reviews decisions",
            status="clean",
            exit_code=0,
            summary=summary,
            diagnostics=diagnostics,
            evidence=[
                Evidence(
                    key="decisions",
                    value={
                        "total": len(rows),
                        "irreversible": n_irrev,
                        "unknown_reversible": n_unknown,
                        "plans": len(plans),
                    },
                    status="clean",
                )
            ],
            next_actions=[
                NextAction(
                    command="aw reviews decisions --irreversible",
                    description="show only the decisions that cannot be undone",
                )
            ]
            if rows and not only_irreversible
            else [],
            data={
                "decisions": [r.to_dict(repo_root) for r in rows],
                "total": len(rows),
                "irreversible": n_irrev,
                "unknown_reversible": n_unknown,
                "plans": plans,
                "selector": selector or None,
                "filtered_irreversible": only_irreversible,
            },
            target=selector or None,
            verified=True,
            complete=True,
        )
        return get_renderer(ctx).emit(res, ctx)

    out = sys.stdout
    if not rows:
        out.write("aw reviews decisions: {0}\n".format(summary))
        for d in diagnostics:
            out.write("  warning  {0}  {1}\n".format(d.location, d.detail))
        return 0

    for r in rows:
        try:
            shown = r.review_path.relative_to(repo_root)
        except ValueError:
            shown = r.review_path
        mark = {"no": "IRREVERSIBLE", "yes": "reversible", "unknown": "UNJUDGED"}[
            r.reversible
        ]
        out.write(
            "{0}\t{1}\tround {2}\t{3}\t{4}\n".format(
                r.plan_id or "?", r.id, r.round_number, mark, r.question
            )
        )
        out.write("\tchose: {0}\n".format(r.chosen))
        if r.alternatives:
            out.write("\tinstead of: {0}\n".format(r.alternatives))
        if r.basis:
            out.write("\tbasis: {0}\n".format(r.basis))
        out.write("\tin: {0}:{1}\n".format(shown, r.line))
    out.write("\n{0}\n".format(summary))
    for d in diagnostics:
        out.write("  warning  {0}  {1}\n".format(d.location, d.detail))
    return 0
