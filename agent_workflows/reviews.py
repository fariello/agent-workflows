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

READ-ONLY EXCEPT FOR ONE DORMANT WRITER. `run_decisions` writes, moves, or mutates nothing. Parsing
is delegated to `review_findings` (pure, never raises) and discovery to the record-path authority via
`review_findings.review_dirs`, so this module holds no `.aw/records/reviews` path literal of its own
and cannot disagree with the writer about where reviews live.

`run_record` (metastore `724acb`, spec `4sd62s` 4.1a) is the one writer: it appends ONE `op: review`
event to the SUBJECT's `meta/<id6>.jsonl` log, which is where a review round lives after the
metadata cutover (a review file has no log of its own). It is DORMANT before the cutover: while the
repository's `metadata_schema` stamp is below 2 it refuses and writes nothing, so `main` keeps one
spelling of review metadata (the hand-written `- Readiness:` bullet) until the migration runs.
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

    Carries enough context to be actionable on its own line of output: which artifact was being
    reviewed, which round recorded it, and where the file is, so a maintainer can go read the
    surrounding findings without a second lookup.
    """

    subject_id: str
    subject_type: str
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
            "subject_id": self.subject_id,
            "subject_type": self.subject_type,
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
    ``(subject_id, review path, round, decision id)`` for deterministic output, and ``diagnostics`` is
    a list of ``(path, Diagnostic)`` pairs.

    ALL ROUNDS ARE INCLUDED BY DEFAULT, unlike the gating rules, which read the current round only.
    That difference is deliberate and is the point of an audit trail: a gate asks "does this plan
    block TODAY", so a superseded finding must stop counting; an audit asks "what did the agents
    decide", and a decision made in round 1 was still made. Pass ``current_round_only=True`` for the
    gate-shaped view (which `check_engine` does).

    Diagnostics are RETURNED, not raised and not printed. A malformed review is a fact the caller
    reports; this function has no opinion about exit codes.
    """
    from agent_workflows import artifact_meta as _am
    from agent_workflows import review_findings as _rf

    repo_root = Path(repo_root)
    rows: List[DecisionRow] = []
    diags: List[tuple] = []

    if paths is None:
        candidates = list(_rf.iter_review_files(repo_root))
    else:
        candidates = [Path(p) for p in paths]

    ctx = None
    records_root: Optional[Path] = None
    scan_repo: Optional[Path] = None
    try:
        ctx = _am.legacy_context(repo_root)
        records_root = Path(ctx.logical_roots["records"])
        scan_repo = _am._scan_repo_root(ctx, records_root)
    except Exception:
        ctx = None

    for path in candidates:
        doc = _rf.parse_review_file(path)
        for d in doc.diagnostics:
            diags.append((path, d))
        subject_id = doc.subject_id
        if not subject_id and ctx is not None and records_root is not None:
            parsed_name = _rf.parse_review_name(path.name)
            fn_id6 = parsed_name["id6"] if parsed_name else ""
            if fn_id6:
                try:
                    stored = _am.stored_path(path, records_root, scan_repo)
                    for rrow in _am.review_rows(fn_id6, project_context=ctx):
                        if rrow.get("path") == stored:
                            subject_id = fn_id6
                            break
                except Exception:
                    pass
        current = doc.current_round()
        cur_no = current.number if current is not None else None
        for rnd in doc.rounds:
            is_cur = cur_no is not None and rnd.number == cur_no and rnd is current
            if current_round_only and not is_cur:
                continue
            for dec in rnd.decisions:
                rows.append(
                    DecisionRow(
                        subject_id=subject_id,
                        subject_type=doc.subject_type,
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

    rows.sort(key=lambda r: (r.subject_id, str(r.review_path), r.round_number, r.id))
    return rows, diags


def _resolve_selector_paths(repo_root: Path, selector: str) -> tuple:
    """Resolve one selector to review file(s) via cached ``review_files`` rows and ``selectors``.

    Returns ``(paths, note)``. ``note`` is a human-facing explanation when the selector resolved to
    nothing, so the caller never has to invent one.

    For an ``id6`` selector, consults the cached ``review_files`` rows in ``artifact_meta`` first
    (matching the review's declared ``Subject-Id`` even when the filename carries a distinct ref
    id6), then falls back to the shared ``selectors`` resolver for filename/setid/stem tokens.
    """
    from agent_workflows import artifact_core as _core
    from agent_workflows import review_findings as _rf
    from agent_workflows import selectors as _sel

    tok = (selector or "").strip()
    if not tok:
        return [], ""

    direct = Path(tok)
    if direct.is_file():
        return [direct], ""

    if _core.ID6_RE.fullmatch(tok):
        try:
            cached_paths, _ = _rf._cached_subject_review_files(repo_root, tok)
        except Exception:
            cached_paths = []
        cached_paths = [p for p in cached_paths if p.name.endswith(".review.md")]
        if cached_paths:
            return cached_paths, ""

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
    any_reviews = any(True for _ in _rf.iter_review_files(repo_root))
    if not any_reviews:
        return [], "no review records exist yet, so no selector can match one"
    return (
        [],
        "no review record matches `{0}` (checked cached review subject ids and review filenames)".format(
            tok
        ),
    )


def run_decisions(args) -> int:
    """`aw reviews decisions [<selector>]`: print the decisions agents made without asking.

    Read-only. Exit contract is ``(0, 2)``: 0 whether or not any decision was found (an empty audit
    trail is a legitimate answer, not a failure), and 2 for an unresolvable selector token (naming no
    artifact anywhere in the repo) or a usage error such as conflicting output flags. There is
    deliberately NO exit 1: this verb REPORTS, it does not judge, and the judging is
    `check.review-decision-unescalated`'s job. Declaring an exit-1 contract would also oblige a
    `domain_failure` conformance scenario this printer cannot produce.
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
        if not paths:
            from agent_workflows.cli import (
                emit_zero_match_selector_refusal,
                selector_tokens_naming_no_artifact,
            )

            refusable = selector_tokens_naming_no_artifact(repo_root, [selector])
            if refusable:
                return emit_zero_match_selector_refusal(
                    ctx=ctx,
                    cmd="reviews decisions",
                    tokens=refusable,
                    next_cmd="aw reviews decisions",
                    next_desc="list all decisions without selector filter",
                    searched="all artifact types",
                )

    rows, diags = collect_decisions(repo_root, paths=paths)
    if only_irreversible:
        rows = [r for r in rows if r.is_irreversible]

    n_irrev = sum(1 for r in rows if r.reversible == "no")
    n_unknown = sum(1 for r in rows if r.reversible == "unknown")
    # `subjects`, not `plans`: after `eyh1fu` a record's subject may be a spec, so a key named
    # `plans` would ASSERT a type the data no longer guarantees. Renamed rather than left, because a
    # misdescribing field name is the same defect in an output payload that `- Plan-Id:` was in the
    # record. No documented contract or consumer reads it (measured: zero hits outside this module).
    subjects = sorted({r.subject_id for r in rows if r.subject_id})

    if rows:
        summary = "{0} recorded decision(s) across {1} reviewed artifact(s)".format(
            len(rows), len(subjects)
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
                        "subjects": len(subjects),
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
                "subjects": subjects,
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
                r.subject_id or "?", r.id, r.round_number, mark, r.question
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


# --------------------------------------------------------------------------------------------------
# `aw reviews record` (metastore `724acb` E-02; spec `4sd62s` 4.1a, 4.2 review payload)
# --------------------------------------------------------------------------------------------------

#: The schema stamp from which a review round is an event in the subject's log (spec 5.3).
LOG_FORMAT_SCHEMA = 2

#: The subject types a review can be about (review front matter `subject_type`, 4.1a R2).
_REVIEW_SUBJECT_TYPES = ("ipd", "spec")


#: The diagnostic rule a dormancy refusal carries, shared by every log-only writer.
UNMIGRATED_RULE = "metadata-schema-unmigrated"


class ReviewEventRefused(ValueError):
    """A refused review payload; ``rule`` is the agent-visible diagnostic rule naming why."""

    def __init__(self, rule: str, message: str) -> None:
        super().__init__(message)
        self.rule = rule


def log_format_refusal(repo_root: Path, verb: str) -> Optional[str]:
    """The dormancy refusal for a log-only writer, or None when the repository is migrated.

    Before the metadata cutover every record is in the legacy bullet format and has no log, so a
    log-only writer must refuse rather than invent a second spelling of the same metadata. Reads the
    stamp through `migrations.chain.read_metadata_schema`, the one reader of `metadata_schema`. A
    stamp that cannot be read is treated as unmigrated: failing closed writes nothing.
    """
    from agent_workflows.migrations import chain as _chain

    try:
        stamp = _chain.read_metadata_schema(repo_root)
    except Exception as exc:  # malformed project.json or stamp: refuse, write nothing
        return "{0}: cannot read metadata_schema ({1}); run `aw migrate metadata` first".format(
            verb, exc
        )
    if stamp is None or stamp < LOG_FORMAT_SCHEMA:
        return (
            "{0}: this repository's metadata_schema is {1}, and this command writes the "
            "metadata log introduced by schema {2}; run `aw migrate metadata` first "
            "(nothing was written)"
        ).format(verb, "absent" if stamp is None else stamp, LOG_FORMAT_SCHEMA)
    return None


def build_review_event(
    *,
    round_number: int,
    review_kind: str,
    verdict: str,
    subject_type: str,
    readiness: Optional[str] = None,
    review_depth: Optional[str] = None,
    reviewer: Optional[str] = None,
    review_ref: Optional[str] = None,
    findings_summary: Optional[str] = None,
) -> Dict[str, Any]:
    """Build one spec-4.1a `op: review` payload, or raise ValueError naming the refused value.

    Refuses: a non-positive round; a kind other than gate or refinement; a verdict outside its
    kind's vocabulary (`artifact_meta.GATE_VERDICTS` / `REFINEMENT_VERDICTS`); `readiness` on a
    refinement round or on a review whose subject is not a plan (4.2: "gate reviews of plans
    only"); a `readiness` or `review_depth` outside the closed enums its readers normalize against
    (`ipd_schema.READINESS_VALUES`, `ipd_schema.REVIEW_DEPTH_VALUES`). The writer
    (`artifact_meta.validate_event`) repeats the kind and verdict refusals; checking here first gives
    the caller a usage message before any lock or file is touched.
    """
    from agent_workflows import artifact_meta as _meta
    from agent_workflows import ipd_schema as _schema

    if not isinstance(round_number, int) or round_number < 1:
        raise ReviewEventRefused(
            "reviews-record.bad-round",
            "--round must be a positive integer, got {0!r}".format(round_number),
        )
    if review_kind == "gate":
        vocab: Sequence[str] = _meta.GATE_VERDICTS
    elif review_kind == "refinement":
        vocab = _meta.REFINEMENT_VERDICTS
    else:
        raise ReviewEventRefused(
            "reviews-record.bad-kind",
            "--kind must be 'gate' or 'refinement'', got {0!r}".format(review_kind),
        )
    verdict_tok = (verdict or "").strip()
    if verdict_tok not in vocab:
        raise ReviewEventRefused(
            "reviews-record.verdict-vocabulary",
            "--verdict {0!r} is not a {1} verdict; expected one of: {2}".format(
                verdict_tok, review_kind, "; ".join(vocab)
            ),
        )
    event: Dict[str, Any] = {
        "op": "review",
        "round": round_number,
        "review_kind": review_kind,
        "verdict": verdict_tok,
    }
    if readiness is not None:
        tok = readiness.strip()
        if review_kind == "refinement":
            raise ReviewEventRefused(
                "reviews-record.readiness-on-refinement",
                "--readiness is refused on a refinement round: only a gate review sets readiness",
            )
        if subject_type != "ipd":
            raise ReviewEventRefused(
                "reviews-record.readiness-not-plan",
                "--readiness is refused for a {0} subject: readiness is recorded only by a gate "
                "review of a plan".format(subject_type),
            )
        if tok not in _schema.READINESS_VALUES:
            raise ReviewEventRefused(
                "reviews-record.readiness-vocabulary",
                "--readiness {0!r} is not recognized; expected one of: {1}".format(
                    tok, ", ".join(sorted(_schema.READINESS_VALUES))
                ),
            )
        event["readiness"] = tok
    if review_depth is not None:
        tok = review_depth.strip()
        if tok not in _schema.REVIEW_DEPTH_VALUES:
            raise ReviewEventRefused(
                "reviews-record.review-depth-vocabulary",
                "--review-depth {0!r} is not recognized; expected one of: {1}".format(
                    tok, ", ".join(sorted(_schema.REVIEW_DEPTH_VALUES))
                ),
            )
        event["review_depth"] = tok
    for key, val in (
        ("reviewer", reviewer),
        ("review_ref", review_ref),
        ("findings_summary", findings_summary),
    ):
        if val is None:
            continue
        sval = str(val).strip()
        if not sval:
            raise ReviewEventRefused(
                "reviews-record.empty-value",
                "--{0} must not be empty".format(key.replace("_", "-")),
            )
        event[key] = sval
    return event


def _scan_subject_log(log_path: Path) -> tuple:
    """``(type, [(review_ref, round), ...])`` read straight from ``log_path``.

    Reads the log rather than `artifact_meta.read` so a refused call touches nothing, not even the
    gitignored cache that `read` refreshes. The type is the one the create (or migration
    checkpoint) event declared; the writer's own replay still validates the whole log on append.
    """
    from agent_workflows import artifact_meta as _meta

    rtype: Optional[str] = None
    rounds: List[tuple] = []
    for line in log_path.read_text(encoding="utf-8").splitlines(keepends=True):
        if not line.strip():
            continue
        ev = _meta.decode_line(line)
        op = ev.get("op")
        if op in ("create", "checkpoint") and isinstance(ev.get("fields"), dict):
            rtype = ev["fields"].get("type", rtype)
        elif op == "review":
            rounds.append((ev.get("review_ref"), ev.get("round")))
    return rtype, rounds


def record_review(
    repo_root: Path,
    subject_id6: str,
    *,
    round_number: int,
    review_kind: str,
    verdict: str,
    readiness: Optional[str] = None,
    review_depth: Optional[str] = None,
    reviewer: Optional[str] = None,
    review_ref: Optional[str] = None,
    findings_summary: Optional[str] = None,
) -> Any:
    """Append one `op: review` event to ``subject_id6``'s log and return a `CommandResult`.

    Refuses with exit 2 and writes nothing when: the repository is not migrated (dormancy); the id6
    is malformed; the subject has no `meta/<id6>.jsonl` log; the subject is not a plan or spec; the
    payload is refused by :func:`build_review_event`; the same round is already recorded for the same
    review file binding (`review_ref`, spec 4.1a K4: exactly one event per round); or the writer
    refuses the append.
    """
    from agent_workflows import artifact_core as _core
    from agent_workflows import artifact_meta as _meta
    from agent_workflows import meta_cli as _meta_cli
    from agent_workflows.result_types import (
        Change,
        CommandResult,
        Diagnostic,
        NextAction,
    )

    verb = "aw reviews record"

    def _refuse(
        rule: str, message: str, next_cmd: str = "aw reviews record --help"
    ) -> Any:
        return CommandResult(
            command="reviews record",
            status="cannot-run",
            exit_code=2,
            summary=message,
            diagnostics=[
                Diagnostic(
                    location=subject_id6 or "-",
                    rule=rule,
                    detail=message + " (nothing was written)"
                    if "nothing was written" not in message
                    else message,
                    severity="error",
                    fix=next_cmd,
                )
            ],
            next_actions=[NextAction(command=next_cmd)],
            verified=False,
            complete=False,
            applied=False,
            repo_root=repo_root,
        )

    dormant = log_format_refusal(repo_root, verb)
    if dormant:
        return _refuse(UNMIGRATED_RULE, dormant, "aw migrate metadata")
    tok = (subject_id6 or "").strip()
    if not _core.ID6_RE.fullmatch(tok):
        return _refuse(
            "reviews-record.invalid-id6",
            "{0}: invalid subject id6 {1!r}: expected 6 lowercase base36 characters".format(
                verb, tok
            ),
        )
    ctx = _meta_cli.meta_context(repo_root)
    log_rel = "meta/{0}.jsonl".format(tok)
    log_path = ctx.records_root / log_rel
    if not log_path.is_file():
        return _refuse(
            "reviews-record.no-log",
            "{0}: {1} has no metadata log ({2}); a review is recorded in its subject's log".format(
                verb, tok, log_rel
            ),
            "aw show {0}".format(tok),
        )
    try:
        subject_type, recorded_rounds = _scan_subject_log(log_path)
    except (OSError, ValueError) as exc:
        return _refuse(
            "reviews-record.unreadable-log",
            "{0}: cannot read {1}: {2}".format(verb, log_rel, exc),
            "aw meta repair {0}".format(tok),
        )
    if subject_type not in _REVIEW_SUBJECT_TYPES:
        return _refuse(
            "reviews-record.subject-type",
            "{0}: {1} is a {2}; a review subject must be a plan or a spec".format(
                verb, tok, subject_type
            ),
        )
    try:
        event = build_review_event(
            round_number=round_number,
            review_kind=review_kind,
            verdict=verdict,
            subject_type=subject_type,
            readiness=readiness,
            review_depth=review_depth,
            reviewer=reviewer,
            review_ref=review_ref,
            findings_summary=findings_summary,
        )
    except ReviewEventRefused as exc:
        return _refuse(exc.rule, "{0}: {1}".format(verb, exc))
    binding = (event.get("review_ref"), event["round"])
    if binding in recorded_rounds:
        return _refuse(
            "reviews-record.duplicate-round",
            "{0}: round {1} is already recorded for {2}{3}; each round has exactly one review "
            "event".format(
                verb,
                event["round"],
                tok,
                " (review_ref {0})".format(binding[0]) if binding[0] else "",
            ),
            "aw show {0}".format(tok),
        )
    try:
        res = _meta.append(
            tok,
            [event],
            project_context=ctx,
            actor={"tool": "aw reviews record"},
        )
    except (ValueError, RuntimeError) as exc:
        return _refuse(
            "reviews-record.writer-refused",
            "{0}: refused by the metadata writer: {1}".format(verb, exc),
        )
    if not isinstance(res, dict) or not res.get("committed"):
        err = res.get("error") if isinstance(res, dict) else res
        return _refuse(
            "reviews-record.writer-refused",
            "{0}: nothing was written: {1}".format(verb, err),
        )
    detail = "review round {0} ({1}): {2}".format(
        event["round"], review_kind, event["verdict"]
    )
    if "readiness" in event:
        detail += "; readiness {0}".format(event["readiness"])
    summary = "recorded {0} for {1}".format(detail, tok)
    warning = res.get("warning")
    if warning:
        summary += "; {0}".format(warning)
    return CommandResult(
        command="reviews record",
        status="ok",
        exit_code=0,
        summary=summary,
        changes=[
            Change(
                path=str(log_path),
                kind="modify",
                detail=detail,
                applied=True,
            )
        ],
        next_actions=[NextAction(command="aw show {0}".format(tok))],
        data={
            "subject": tok,
            "subject_type": subject_type,
            "event": event,
            "seq": res.get("seq"),
        },
        target=tok,
        applied=True,
        verified=True,
        complete=True,
        repo_root=repo_root,
    )


def run_record(args) -> int:
    """`aw reviews record <subject-id6> --round N --kind gate|refinement --verdict V ...`."""
    from agent_workflows.project_context import resolve_verb_repo_root
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import select_output

    ctx = select_output(args)
    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    res = record_review(
        repo_root,
        getattr(args, "subject", "") or "",
        round_number=getattr(args, "round", 0),
        review_kind=getattr(args, "kind", "") or "",
        verdict=getattr(args, "verdict", "") or "",
        readiness=getattr(args, "readiness", None),
        review_depth=getattr(args, "review_depth", None),
        reviewer=getattr(args, "reviewer", None),
        review_ref=getattr(args, "review_ref", None),
        findings_summary=getattr(args, "findings_summary", None),
    )
    if ctx.is_agent or ctx.is_json:
        return get_renderer(ctx).emit(res, ctx)
    if res.exit_code != 0:
        sys.stderr.write("{0}\n".format(res.summary))
        for na in res.next_actions:
            sys.stderr.write("  next: {0}\n".format(na.command))
        return res.exit_code
    sys.stdout.write("aw reviews record: {0}\n".format(res.summary))
    return 0
