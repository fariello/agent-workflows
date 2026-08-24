"""Inspectable + durable records for Set coordination (execset Order 02, `3m4e54` E-03).

Turns the ledger's coordination events (Order 02 E-01) into the human-facing records the user
inspects through normal AW records/attention:

  * Local run projections written under the untracked run-artifacts dir
    ``.aw/workflow-artifacts/<workflow>/<run-id>/`` (the local authoritative run convention):
      - ``decisions.md``       - every autonomous decision (esp. consultation_preferred ones)
      - ``open-questions.md``  - every unresolved runtime question
      - ``deferred-work.md``   - every deferred subgraph/IPD and the nodes it blocks
  * A TRACKED walkthrough under ``.aw/records/walkthroughs/`` at partial/terminal checkpoints,
    written directly to the uniform artifact grammar (there is no programmatic walkthrough writer to
    reuse; we resolve the dir + build the clustered name + atomic-write).
  * A blocked backlog item promoted for an unresolved question, with ``Gate-Kind: decision`` and a
    valid ``D<number>`` ``Gate-Ref`` (per the verified constraint that a decision Gate-Ref must match
    ``^D\\d+$``). The RESUME COMMAND is put in the item BODY, never in ``Gate-Ref`` (which would fail
    validation). ``close_on_answer`` transitions that blocked item to ``done`` when the question is
    answered (net-new close-on-answer behaviour).
  * ``promote_local_checkpoints`` - on recovery, promote any untracked local decision/question
    checkpoint into the tracked walkthrough before releasing another lane.

Reuses: ``backlog.BacklogItem``/``_render_item``/``parse_item``/``validate_item``,
``attention_contract.validate_gate_ref``, ``artifact_naming.build_clustered_name``,
``record_producers.resolve_record_path``, and ``artifact_core.atomic_write``. Emits no consent and
never marks an IPD executed.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import List, Mapping, NamedTuple, Optional, Sequence

from agent_workflows import artifact_core as _core
from agent_workflows import attention_contract as _ac

# The local (untracked) run-artifacts directory convention. Deliberately NOT routed through
# resolve_record_path (which rejects `workflow-artifacts/`); created directly and gitignored.
RUN_ARTIFACTS_SUBDIR = ".aw/workflow-artifacts"

DECISIONS_FILE = "decisions.md"
OPEN_QUESTIONS_FILE = "open-questions.md"
DEFERRED_WORK_FILE = "deferred-work.md"


def run_artifacts_dir(repo_root: Path, workflow: str, run_id: str) -> Path:
    """Return the local, untracked run-artifacts dir ``.aw/workflow-artifacts/<workflow>/<run-id>``."""
    return repo_root / RUN_ARTIFACTS_SUBDIR / workflow / run_id


# --------------------------------------------------------------------------------------------------
# Local projections (pure renderers over ledger coordination records)
# --------------------------------------------------------------------------------------------------


def render_decisions(records: Sequence[Mapping]) -> str:
    """Render ``decisions.md`` from ``autonomous_decision`` records (newest supersedes oldest).

    A record whose id is pointed at by a later record's ``prev`` is marked superseded.
    """
    decisions = [r for r in records if r.get("kind") == "autonomous_decision"]
    superseded = {r.get("prev") for r in decisions if r.get("prev")}
    lines: List[str] = ["# Autonomous decisions", ""]
    if not decisions:
        lines.append("_No autonomous decisions recorded._")
        return "\n".join(lines) + "\n"
    for r in decisions:
        did = r.get("decision_id", "?")
        tag = " (SUPERSEDED)" if did in superseded else ""
        pref = " [consultation_preferred]" if r.get("consultation_preferred") else ""
        lines.append("## {0}{1}{2}".format(did, tag, pref))
        lines.append("- Selected option: {0}".format(r.get("selected_option", "")))
        lines.append("- Confidence: {0}".format(r.get("confidence", "")))
        lines.append("- Reversible: {0}".format(r.get("reversible", "")))
        if r.get("prev"):
            lines.append("- Supersedes: {0}".format(r.get("prev")))
        lines.append(
            "- Recorded: {0} (actor {1})".format(
                r.get("timestamp", ""), r.get("actor", "")
            )
        )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_open_questions(records: Sequence[Mapping]) -> str:
    """Render ``open-questions.md`` from ``question_raised`` records with no resolving disposition."""
    raised = [r for r in records if r.get("kind") == "question_raised"]
    disposed = {
        r.get("question_id")
        for r in records
        if r.get("kind") in ("question_disposition", "human_answer")
    }
    lines: List[str] = ["# Open questions", ""]
    open_qs = [r for r in raised if r.get("question_id") not in disposed]
    if not open_qs:
        lines.append("_No unresolved questions._")
        return "\n".join(lines) + "\n"
    for r in open_qs:
        qid = r.get("question_id", "?")
        lines.append("## {0}".format(qid))
        lines.append("- Context: {0}".format(r.get("context", "")))
        affected = r.get("affected_nodes", []) or []
        lines.append(
            "- Affected nodes: {0}".format(", ".join(affected) if affected else "-")
        )
        lines.append(
            "- Raised: {0} (actor {1})".format(
                r.get("timestamp", ""), r.get("actor", "")
            )
        )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_deferred_work(records: Sequence[Mapping]) -> str:
    """Render ``deferred-work.md`` from ``scope_deferred`` records + their blocked nodes."""
    deferred = [r for r in records if r.get("kind") == "scope_deferred"]
    lines: List[str] = ["# Deferred work", ""]
    if not deferred:
        lines.append("_No deferred scope._")
        return "\n".join(lines) + "\n"
    for r in deferred:
        lines.append("## {0}".format(r.get("scope", "?")))
        lines.append("- Reason: {0}".format(r.get("reason", "")))
        blocks = r.get("blocks", []) or []
        lines.append("- Blocks: {0}".format(", ".join(blocks) if blocks else "-"))
        lines.append(
            "- Recorded: {0} (actor {1})".format(
                r.get("timestamp", ""), r.get("actor", "")
            )
        )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


class ProjectionResult(NamedTuple):
    decisions_path: Path
    open_questions_path: Path
    deferred_work_path: Path


def write_local_projections(
    repo_root: Path,
    workflow: str,
    run_id: str,
    records: Sequence[Mapping],
) -> ProjectionResult:
    """Write the three local projections into the untracked run-artifacts dir. Returns their paths."""
    base = run_artifacts_dir(repo_root, workflow, run_id)
    base.mkdir(parents=True, exist_ok=True)
    dpath = base / DECISIONS_FILE
    qpath = base / OPEN_QUESTIONS_FILE
    wpath = base / DEFERRED_WORK_FILE
    _core.atomic_write(dpath, render_decisions(records))
    _core.atomic_write(qpath, render_open_questions(records))
    _core.atomic_write(wpath, render_deferred_work(records))
    return ProjectionResult(dpath, qpath, wpath)


# --------------------------------------------------------------------------------------------------
# Tracked walkthrough writer
# --------------------------------------------------------------------------------------------------


def render_walkthrough(
    *,
    set_id: str,
    run_id: str,
    checkpoint: str,  # "partial" | "terminal" | "integrated"
    records: Sequence[Mapping],
    summary: str = "",
) -> str:
    """Render the tracked narrative walkthrough body for a Set checkpoint."""
    today = datetime.date.today().isoformat()
    lines: List[str] = [
        "# Set execution walkthrough: {0}".format(set_id),
        "",
        "- Set: {0}".format(set_id),
        "- Run: {0}".format(run_id),
        "- Checkpoint: {0}".format(checkpoint),
        "- Date: {0}".format(today),
        "",
    ]
    if summary:
        lines.append(summary.rstrip())
        lines.append("")
    lines.append("## Autonomous decisions")
    lines.append("")
    lines.append(render_decisions(records))
    lines.append("## Deferred work")
    lines.append("")
    lines.append(render_deferred_work(records))
    lines.append("## Open questions")
    lines.append("")
    lines.append(render_open_questions(records))
    return "\n".join(lines).rstrip() + "\n"


def write_walkthrough(
    repo_root: Path,
    *,
    set_id: str,
    order: int,
    id6: str,
    slug: str,
    body: str,
) -> Path:
    """Write a TRACKED walkthrough to ``.aw/records/walkthroughs/`` using the clustered grammar.

    There is no programmatic walkthrough writer to reuse, so we resolve the dir, build the clustered
    name (``YYYYMMDD-<set>-NN-<id6>-<slug>.walkthrough.md``), and atomic-write.
    """
    from agent_workflows import artifact_naming as _naming
    from agent_workflows.record_producers import resolve_record_path

    try:
        wdir = resolve_record_path("walkthroughs", target_repo=str(repo_root))
    except Exception:
        wdir = repo_root / ".aw" / "records" / "walkthroughs"
    date = datetime.date.today().strftime("%Y%m%d")
    name = _naming.build_clustered_name(
        date=date,
        set_id=set_id,
        order=order,
        id6=id6,
        slug=slug,
        artifact_type="walkthrough",
    )
    wdir.mkdir(parents=True, exist_ok=True)
    dest = wdir / name
    _core.atomic_write(dest, body)
    return dest


# --------------------------------------------------------------------------------------------------
# Backlog promotion + close-on-answer
# --------------------------------------------------------------------------------------------------


class PromotionResult(NamedTuple):
    path: Path
    backlog_id: str
    decision_ref: str


def promote_question_to_backlog(
    repo_root: Path,
    *,
    decision_number: int,
    summary: str,
    resume_command: str,
    context: str = "",
    set_id: Optional[str] = None,
) -> PromotionResult:
    """Promote an unresolved question to a blocked ``Gate-Kind: decision`` backlog item.

    The ``Gate-Ref`` is ``D<decision_number>`` (the ONLY shape a decision gate accepts). The RESUME
    COMMAND is placed in the item BODY (a distinct field), never in ``Gate-Ref`` - stuffing it into
    ``Gate-Ref`` would fail ``attention_contract.validate_gate_ref``. Fails closed if the derived
    ``Gate-Ref`` is somehow invalid.
    """
    from agent_workflows import backlog as _backlog

    gate_ref = "D{0}".format(int(decision_number))
    if not _ac.validate_gate_ref("decision", gate_ref):
        raise ValueError("derived decision Gate-Ref {0!r} is invalid".format(gate_ref))

    existing_ids = set()
    for f in _backlog._iter_items(repo_root):
        pid = _backlog.parse_item(f.read_text(encoding="utf-8")).id
        if pid:
            existing_ids.add(pid)
    item = _backlog.BacklogItem()
    item.id = _core.generate_id6(existing_ids)
    item.status = "blocked"
    item.set = set_id or item.id
    item.priority = "high"
    item.kind = "followup"
    item.summary = summary.strip()
    item.gate_kind = "decision"
    item.gate_ref = gate_ref

    body_lines = [
        "## Question context",
        "",
        context.strip() or "(see run open-questions.md)",
        "",
        "## Resume",
        "",
        "Resume trigger (NOT in Gate-Ref): `{0}`".format(resume_command),
        "",
    ]
    body = "\n".join(body_lines)
    rendered = _backlog._render_item(item, body)

    # Validate BEFORE writing (fail-closed): the promoted item must pass backlog validation.
    root = _backlog._resolve_backlog_root(repo_root)
    today = datetime.date.today().strftime("%Y%m%d")
    slug = (_core.kebab(summary or "question")[:50]) or "question"
    filename = "{0}-{1}-01-{2}-{3}.backlog.md".format(today, item.set, item.id, slug)
    dest = root / "blocked" / filename
    drift = _backlog.validate_item(dest, rendered)
    if drift:
        raise ValueError(
            "promoted backlog item failed validation: "
            + "; ".join("{0}: {1}".format(d.rule, d.detail) for d in drift)
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    _core.atomic_write(dest, rendered)
    return PromotionResult(path=dest, backlog_id=item.id, decision_ref=gate_ref)


def close_on_answer(repo_root: Path, backlog_path: Path) -> Path:
    """Close a promoted blocked decision item once its question is answered (net-new behaviour).

    Transitions the item Status ``blocked -> done``, drops the (now irrelevant) gate fields, appends
    a workflow-history line, and moves the file into the ``done/`` disposition dir. Returns the new
    path. Reuses ``backlog.parse_item``/``_render_item`` so the result stays validation-conformant.
    """
    from agent_workflows import backlog as _backlog

    text = backlog_path.read_text(encoding="utf-8")
    item = _backlog.parse_item(text)
    item.status = "done"
    item.gate_kind = None
    item.gate_ref = None
    # Preserve the existing body (everything after the first blank line following the metadata block
    # and history) by re-extracting the prose that is not the metadata/history header.
    body = _extract_body(text)
    today = datetime.date.today().isoformat()
    close_note = "- {0} done (aw set): question answered; close-on-answer".format(today)
    rendered = _backlog._render_item(item, body)
    # Append the close-on-answer history line right after the created line.
    rendered = _inject_history_line(rendered, close_note)

    root = _backlog._resolve_backlog_root(repo_root)
    dest = root / "done" / backlog_path.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    _core.atomic_write(dest, rendered)
    if backlog_path.resolve() != dest.resolve() and backlog_path.exists():
        backlog_path.unlink()
    return dest


def _extract_body(text: str) -> str:
    """Extract the prose body after the ``## Workflow history`` block (best-effort)."""
    lines = text.splitlines()
    out: List[str] = []
    in_hist = False
    hist_done = False
    for ln in lines:
        if ln.strip() == "## Workflow history":
            in_hist = True
            continue
        if in_hist and not hist_done:
            if ln.startswith("- ") or ln.strip() == "":
                continue
            hist_done = True
        if hist_done:
            out.append(ln)
    return "\n".join(out).strip()


def _inject_history_line(rendered: str, line: str) -> str:
    """Insert a history line immediately after the ``## Workflow history`` heading's first entry."""
    lines = rendered.splitlines()
    out: List[str] = []
    injected = False
    for ln in lines:
        out.append(ln)
        if not injected and ln.strip() == "## Workflow history":
            # find the first history bullet after this and insert AFTER it
            injected = True  # will insert once we emit the next bullet below
    if not injected:
        return rendered
    # Reconstruct: insert `line` after the first bullet following the history heading.
    final: List[str] = []
    seen_heading = False
    inserted = False
    for ln in out:
        final.append(ln)
        if ln.strip() == "## Workflow history":
            seen_heading = True
            continue
        if seen_heading and not inserted and ln.startswith("- "):
            final.append(line)
            inserted = True
    if not inserted:
        # No existing bullet; append after heading.
        final2: List[str] = []
        for ln in final:
            final2.append(ln)
            if ln.strip() == "## Workflow history":
                final2.append(line)
        final = final2
    return "\n".join(final).rstrip() + "\n"


# --------------------------------------------------------------------------------------------------
# Recovery: promote local untracked checkpoints before new work
# --------------------------------------------------------------------------------------------------


class RecoveryPromotion(NamedTuple):
    promoted: bool
    walkthrough_path: Optional[Path]
    reason: str


def promote_local_checkpoints(
    repo_root: Path,
    *,
    workflow: str,
    run_id: str,
    set_id: str,
    order: int,
    id6: str,
    records: Sequence[Mapping],
) -> RecoveryPromotion:
    """On recovery, promote any untracked local decision/question checkpoint into a tracked walkthrough.

    If the local run-artifacts dir holds decision/question projections (i.e. there is unflushed
    coordination state), write a tracked ``partial`` walkthrough capturing it BEFORE releasing
    another lane, so a crash never loses a recorded decision. Idempotent: a no-op when there is
    nothing to promote.
    """
    base = run_artifacts_dir(repo_root, workflow, run_id)
    has_local = base.is_dir() and (
        (base / DECISIONS_FILE).exists() or (base / OPEN_QUESTIONS_FILE).exists()
    )
    has_records = any(
        r.get("kind") in ("autonomous_decision", "question_raised", "scope_deferred")
        for r in records
    )
    if not (has_local or has_records):
        return RecoveryPromotion(False, None, "no local checkpoint to promote")
    body = render_walkthrough(
        set_id=set_id,
        run_id=run_id,
        checkpoint="partial",
        records=records,
        summary="Recovery checkpoint: promoting local decision/question state before new work.",
    )
    path = write_walkthrough(
        repo_root,
        set_id=set_id,
        order=order,
        id6=id6,
        slug="recovery-checkpoint",
        body=body,
    )
    return RecoveryPromotion(
        True, path, "promoted local checkpoint to tracked walkthrough"
    )
