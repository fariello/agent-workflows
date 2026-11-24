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

Reuses: ``backlog.BacklogItem``/``_render_item``/``item_from_text``/``validate_item``,
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


def _existing_walkthrough_ids(wdir: Path) -> set:
    from agent_workflows import artifact_naming as _naming

    ids: set = set()
    if not wdir.is_dir():
        return ids
    for p in wdir.rglob("*.md"):
        if not p.is_file():
            continue
        m = _naming.parse_clustered(p.name)
        if m:
            ids.add(m.group("id6"))
        try:
            content = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("- Id:"):
                val = line.split(":", 1)[1].strip()
                if val:
                    ids.add(val)
    return ids


def _records_legacy_context(repo_root: Path, records_root: Path):
    """Build a phase-B LegacyContext rooted at ``records_root``."""
    from agent_workflows import artifact_meta as _meta

    base_ctx = _meta.legacy_context(repo_root)
    return type(
        "LegacyContext",
        (),
        {
            "logical_roots": {
                "records": str(records_root.resolve()),
                "state": base_ctx.logical_roots["state"],
            },
            "repo_root": Path(repo_root).resolve(),
        },
    )()


def write_walkthrough(
    repo_root: Path,
    *,
    set_id: str,
    order: int,
    target_id6: str,
    slug: str,
    body: str,
    log_format: bool = False,
    short_description: Optional[str] = None,
) -> Path:
    """Write a TRACKED walkthrough to ``.aw/records/walkthroughs/`` using the clustered grammar.

    Mints the walkthrough's own id6 (collision-checked repository-wide), records the documented
    plan as ``- Target-Id: <target_id6>`` in the metadata block per DECISIONS.md D140, builds the
    clustered name (``YYYYMMDD-<set>-NN-<id6>-<slug>.walkthrough.md``), and atomic-writes.

    ``log_format=True`` (metastore `724acb`, used only by `aw walkthrough new` after the metadata
    cutover) creates the walkthrough on the log branch instead: `artifact_meta.create` writes
    ``meta/<id6>.jsonl`` with the create event (carrying ``short_description`` when given) and the
    body behind the in-file mirror. The default keeps the phase-B legacy rendering every existing
    caller relies on, so they are unchanged.
    """
    from agent_workflows import artifact_naming as _naming
    from agent_workflows.record_producers import resolve_record_path

    log_ctx = None
    if log_format:
        # The log branch writes under the SAME records root the log readers (`aw show`, `aw check
        # meta`) use, so the walkthrough and its `meta/<id6>.jsonl` can never land in different trees.
        from agent_workflows import meta_cli as _meta_cli

        log_ctx = _meta_cli.meta_context(repo_root)
        wdir = log_ctx.records_root / "walkthroughs"
    else:
        try:
            wdir = resolve_record_path("walkthroughs", target_repo=str(repo_root))
        except Exception:
            from agent_workflows.project_context import project_records_dir

            wdir = project_records_dir(repo_root) / "walkthroughs"

    minted_id6 = _core.mint_id6(repo_root, _existing_walkthrough_ids(wdir))

    date = datetime.date.today().strftime("%Y%m%d")
    name = _naming.build_clustered_name(
        date=date,
        set_id=set_id,
        order=order,
        id6=minted_id6,
        slug=slug,
        artifact_type="walkthrough",
    )
    wdir.mkdir(parents=True, exist_ok=True)
    dest = wdir / name

    from agent_workflows import artifact_meta as _meta

    if log_ctx is not None:
        fields = {"set": set_id, "order": int(order), "target_id": target_id6}
        if short_description:
            fields["short_description"] = short_description
        res = _meta.create(
            minted_id6,
            "walkthrough",
            fields,
            body,
            destination=dest,
            dry_run=False,
            project_context=log_ctx,
            actor={"tool": "aw walkthrough new"},
        )
        if not isinstance(res, dict) or not res.get("committed"):
            err = res.get("error") if isinstance(res, dict) else res
            raise RuntimeError(f"walkthrough was not created: {err}")
        return dest
    ctx = _records_legacy_context(repo_root, wdir.resolve().parent)
    _meta.create(
        minted_id6,
        "walkthrough",
        {"set": set_id, "order": int(order), "target_id": target_id6},
        body,
        destination=dest,
        dry_run=False,
        project_context=ctx,
        repo_root=repo_root,
        legacy_render=_meta.LegacyRender(
            tag="created",
            day=_core.utc_history_date(),
            actor_label="aw walkthrough",
            history=False,
        ),
    )
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
        pid = _backlog.item_from_text(f.read_text(encoding="utf-8")).id
        if pid:
            existing_ids.add(pid)
    # IPD sk7ggr E-01: repository-wide mint (see artifact_core.mint_id6). This site was absent from
    # the plan's original call-site list and mints a BACKLOG id6, so it needs the global set exactly
    # as `backlog.run_new` does.
    minted_id = _core.mint_id6(repo_root, existing_ids)
    set_val = set_id or minted_id

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

    # Validate BEFORE writing (fail-closed): the promoted item must pass backlog validation.
    root = _backlog._resolve_backlog_root(repo_root)
    today = datetime.date.today().strftime("%Y%m%d")
    slug = _core.kebab_slug(summary or "question", 50, "question")
    filename = "{0}-{1}-01-{2}-{3}.backlog.md".format(today, set_val, minted_id, slug)
    dest = root / "blocked" / filename

    from agent_workflows import artifact_meta as _meta

    ctx = _records_legacy_context(repo_root, root.resolve().parent)
    fields = {
        "status": "blocked",
        "set": set_val,
        "priority": "high",
        "work_kind": "followup",
        "summary": summary.strip(),
        "gate_kind": "decision",
        "gate_ref": gate_ref,
    }
    hist_message = f"promoted blocking question ({gate_ref})"
    render = _meta.LegacyRender(
        tag="created",
        day=_core.utc_history_date(),
        actor_label="aw backlog",
        history=True,
    )
    preview = _meta.create(
        minted_id,
        "backlog",
        fields,
        body,
        destination=dest,
        dry_run=True,
        project_context=ctx,
        repo_root=repo_root,
        message=hist_message,
        legacy_render=render,
    )
    drift = _backlog.validate_item(dest, preview.text)
    if drift:
        raise ValueError(
            "promoted backlog item failed validation: "
            + "; ".join("{0}: {1}".format(d.rule, d.detail) for d in drift)
        )
    _meta.create(
        minted_id,
        "backlog",
        fields,
        body,
        destination=dest,
        dry_run=False,
        project_context=ctx,
        repo_root=repo_root,
        message=hist_message,
        legacy_render=render,
    )
    return PromotionResult(path=dest, backlog_id=minted_id, decision_ref=gate_ref)


def close_on_answer(repo_root: Path, backlog_path: Path) -> Path:
    """Close a promoted blocked decision item once its question is answered (net-new behaviour).

    Transitions the item Status ``blocked -> done``, drops the (now irrelevant) gate fields, appends
    a workflow-history line, and moves the file into the ``done/`` disposition dir via
    ``artifact_meta.append``. Returns the new path.
    """
    from agent_workflows import artifact_meta as _meta
    from agent_workflows import backlog as _backlog
    from agent_workflows import check_engine as _check_engine

    text = backlog_path.read_text(encoding="utf-8")
    item = _backlog.item_from_text(text)
    if item.status != "blocked":
        raise ValueError(
            f"close_on_answer requires status 'blocked', got {item.status!r}"
        )

    root = _backlog._resolve_backlog_root(repo_root)
    dest = root / "done" / backlog_path.name
    ctx = _records_legacy_context(repo_root, root.resolve().parent)
    target = _meta.LegacyTarget(backlog_path, "backlog", item.id or None)
    events = [
        {
            "op": "transition",
            "from": item.status,
            "to": "done",
            "message": "question answered; close-on-answer",
        },
        {"op": "unset", "fields": ["gate_kind", "gate_ref", "gate_summary"]},
    ]
    render = _meta.LegacyRender(
        tag="done",
        day=_core.utc_history_date(),
        actor_label="aw backlog",
        history=True,
    )

    preview = _meta.append(
        target,
        events,
        dry_run=True,
        project_context=ctx,
        legacy_render=render,
        repo_root=repo_root,
        destination=dest,
    )
    drift = _backlog.validate_item(dest, preview.text)
    if drift:
        raise ValueError(
            "closed backlog item failed validation: "
            + "; ".join("{0}: {1}".format(d.rule, d.detail) for d in drift)
        )

    # rendrop 2yqt0a E-08 (review PR-004, F-11): refuse closing an item that carries a live release
    # gate with no handoff and no evidence, so close_on_answer cannot manufacture a done item
    # carrying a dropped release gate that escapes the commit-staged check.
    verdict = _check_engine.evaluate_blocking_close(
        repo_root, backlog_path, "done", item_text=preview.text
    )
    if not verdict.legitimate and verdict.severity == "error":
        fixes = "; ".join(verdict.fixes)
        msg = f"{verdict.reason}; fixes: {fixes}" if fixes else verdict.reason
        raise ValueError(msg)

    _meta.append(
        target,
        events,
        dry_run=False,
        project_context=ctx,
        legacy_render=render,
        repo_root=repo_root,
        destination=dest,
    )
    return dest


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
    target_id6: str,
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
        target_id6=target_id6,
        slug="recovery-checkpoint",
        body=body,
    )
    return RecoveryPromotion(
        True, path, "promoted local checkpoint to tracked walkthrough"
    )


# --------------------------------------------------------------------------------------------------
# `aw walkthrough new` (metastore `724acb` E-03; spec `4sd62s` 4.2 SHORT DESCRIPTION, 4.6)
# --------------------------------------------------------------------------------------------------


def new_walkthrough(
    repo_root: Path,
    *,
    set_id: str,
    order: int,
    target_id6: str,
    slug: str,
    summary: Optional[str] = None,
):
    """Create a tracked walkthrough AND its metadata log; return a `CommandResult`.

    After the metadata cutover a walkthrough written by hand has no log and `aw check meta` reports
    it as an orphan (spec 4.6), so this is the tooled way to create one. It is DORMANT before the
    cutover: while `metadata_schema` is below 2 it refuses with exit 2 and writes nothing, because the
    legacy branch would write a bullet-format walkthrough instead (C10a: one format on `main`).

    Refuses with exit 2, writing nothing, on: an unmigrated repository; an empty or over-long set
    id; a non-positive order; a malformed target id6 or a target with no metadata log; an empty slug;
    or a ``summary`` that `attention_contract.refuse_unsafe_descriptive` refuses (one line, at most
    300 characters). The summary is the walkthrough's logged ``short_description``.
    """
    from agent_workflows import config as _config
    from agent_workflows import reviews as _reviews
    from agent_workflows.result_types import (
        Change,
        CommandResult,
        Diagnostic,
        NextAction,
    )

    verb = "aw walkthrough new"

    def _refuse(rule: str, message: str, next_cmd: str = "aw walkthrough new --help"):
        return CommandResult(
            command="walkthrough new",
            status="cannot-run",
            exit_code=2,
            summary=message,
            diagnostics=[
                Diagnostic(
                    location=target_id6 or "-",
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

    dormant = _reviews.log_format_refusal(repo_root, verb)
    if dormant:
        return _refuse(_reviews.UNMIGRATED_RULE, dormant, "aw migrate metadata")
    set_tok = _core.kebab(set_id or "")
    if not set_tok:
        return _refuse("walkthrough-new.bad-set", f"{verb}: --set must name a Set id")
    set_err, _set_warn = _config.validate_setid_length_for_authoring(
        repo_root, set_tok, verb=verb
    )
    if set_err:
        return _refuse("walkthrough-new.bad-set", set_err)
    if not isinstance(order, int) or order < 1:
        return _refuse(
            "walkthrough-new.bad-order",
            f"{verb}: --order must be a positive integer, got {order!r}",
        )
    target = (target_id6 or "").strip()
    if not _core.ID6_RE.fullmatch(target):
        return _refuse(
            "walkthrough-new.invalid-target",
            f"{verb}: invalid --target {target!r}: expected 6 lowercase base36 characters",
        )
    from agent_workflows import meta_cli as _meta_cli

    records_root = _meta_cli.meta_context(repo_root).records_root
    if not (records_root / "meta" / f"{target}.jsonl").is_file():
        return _refuse(
            "walkthrough-new.target-no-log",
            f"{verb}: --target {target} has no metadata log (meta/{target}.jsonl); "
            "a walkthrough documents an existing record",
            f"aw show {target}",
        )
    slug_tok = _core.kebab_slug(slug or "", 60, "")
    if not slug_tok:
        return _refuse(
            "walkthrough-new.bad-slug",
            f"{verb}: --slug must contain at least one letter or digit",
        )
    short: Optional[str] = None
    if summary is not None:
        err = _ac.refuse_unsafe_descriptive(
            verb, "--summary", summary, bound_length=True
        )
        if err:
            return _refuse("walkthrough-new.unsafe-summary", err)
        short = summary.strip() or None
        if short is None:
            return _refuse(
                "walkthrough-new.unsafe-summary",
                f"{verb}: --summary must not be empty or whitespace-only",
            )

    title = slug_tok.replace("-", " ")
    body = f"# Walkthrough: {title}\n\n"
    if short:
        body += f"{short}\n"
    try:
        dest = write_walkthrough(
            repo_root,
            set_id=set_tok,
            order=order,
            target_id6=target,
            slug=slug_tok,
            body=body,
            log_format=True,
            short_description=short,
        )
    except (ValueError, RuntimeError) as exc:
        return _refuse(
            "walkthrough-new.writer-refused",
            f"{verb}: refused by the metadata writer: {exc}",
        )
    from agent_workflows import artifact_naming as _naming

    m = _naming.parse_clustered(dest.name)
    new_id6 = m.group("id6") if m else ""
    log_path = records_root / "meta" / f"{new_id6}.jsonl"
    return CommandResult(
        command="walkthrough new",
        status="ok",
        exit_code=0,
        summary=f"created walkthrough {new_id6} for {target}: {dest.name}",
        changes=[
            Change(
                path=str(dest), kind="create", detail="walkthrough body", applied=True
            ),
            Change(
                path=str(log_path), kind="create", detail="metadata log", applied=True
            ),
        ],
        next_actions=[NextAction(command=f"aw show {new_id6}")],
        data={
            "id6": new_id6,
            "set": set_tok,
            "order": order,
            "target_id": target,
            "path": dest.name,
            "short_description": short,
        },
        target=new_id6,
        applied=True,
        verified=True,
        complete=True,
        repo_root=repo_root,
    )
