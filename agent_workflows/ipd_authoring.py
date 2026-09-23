"""IPD authoring tools: `aw ipd scaffold` and non-destructive `aw ipd sync` (Order 03).

`scaffold` writes a new conformant IPD skeleton from the canonical schema. `sync` assigns stable
ids to newly-authored execution leaves, maintains the allocation watermark, and appends matching
pending validation skeletons WITHOUT rewriting existing identity or authored content.

Both are the only writing `aw ipd` operations and follow the writing-command safety contract
(spec Section 6.2): dry-run by default, explicit ``--apply`` to write, atomic write-to-temp-rename,
scaffold refuses to overwrite without ``--overwrite``, sync refuses destructive change once
execution has begun, exit 0/1/2 (an internal failure is never reported as a successful write).

Stdlib-only, Python 3.9 compatible. Consumes ``agent_workflows.ipd_schema`` and the Order-02 parser
in ``agent_workflows.ipd_lint``; it restates no structure.
"""

from __future__ import annotations

import argparse
import os
import re
from datetime import date
from pathlib import Path
from typing import List, Optional

from agent_workflows import artifact_core as _core
from agent_workflows import ipd_lint as LINT
from agent_workflows import ipd_schema as S

# The schema-owned unassigned-leaf placeholder: an execution-section top-level task item whose
# first text token is exactly this marker is an unassigned leaf that `sync` will number.
UNASSIGNED_MARKER = "E-NEW"

# --------------------------------------------------------------------------------------
# Scaffold
# --------------------------------------------------------------------------------------

# Per-heading placeholder body used in a fresh skeleton (kept minimal but conformant).
_SECTION_BODY = {
    S.H_WORKFLOW_HISTORY: "- {date} draft ({author}): created.",
    S.H_GOAL: "TODO: one or two sentences on what this plan achieves and why.",
    S.H_PROJECT_CONVENTIONS: (
        # citeanchor mzc019 E-02: the anchor convention is emitted HERE, in the skeleton an author
        # reads while writing Findings, and not only in the spec, because an author writing a Findings
        # table is not reading the IPD spec at that moment. Measured on the pending corpus: 81 of 89
        # plans carry `file:line` citations, so the current DEFAULT behavior is to reach for an offset,
        # and the scaffold is the surface that changes a default. ONE LINE ON PURPOSE: the skeleton's
        # value is that it gets read, and every line added lowers the odds the next one is.
        #
        # DO NOT add this string to `_AUTHORING_PLACEHOLDERS` below. That tuple means "still a stub";
        # this is PERMANENT guidance an author is not expected to delete, so listing it would make
        # every plan look forever-unfinished and silence the `check.ipd-draft-ready-to-review` nudge.
        "- TODO: relevant conventions discovered during Step 0.\n"
        "- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number "
        "only appended to one of those and never alone: an offset expires before this plan executes "
        "(spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`)."
    ),
    S.H_FINDINGS: "TODO: findings table or notes.",
    S.H_PROPOSED: "TODO: ordered, validatable proposed changes.",
    S.H_DEFERRED: "TODO: deferred / out of scope, with reason (or 'none').",
    S.H_SCOPE_CHECK: "- Over-scope: none.\n- Under-scope: TODO.",
    S.H_REQUIRED_TESTS: "TODO: how the executed plan is verified.",
    S.H_SPEC_SYNC: "TODO: specs/docs to update, or 'N/A with reason'.",
    S.H_CHILD_IPDS: "TODO: child IPD table (Order | File | What it does | Depends on).",
    S.H_COMPLETION: "- TODO: whole-Set completion criteria.",
    S.H_CROSS_IPD: "- TODO: cross-IPD consistency / no-drift / dependency checks.",
}

_EXEC_INTRO = (
    "Execution-state rule: mark an `E-*` item complete only after performing the action. "
    "That mark is not validation. Right-sizing rule: each E-item must address one concern "
    "and be executable in one focused pass; split when an E-item names multiple distinct deliverables "
    "or independent test-surfaces."
)
_VALID_INTRO = (
    "Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item "
    "complete from memory or from the matching execution checkmark."
)


def _exec_placeholder_leaf() -> str:
    # A fresh scaffold ships one already-assigned E-01 leaf (watermark 01) so it lints conforming
    # immediately. Authors add further work as `E-NEW` leaves and run `aw ipd sync` to assign them.
    return (
        "### Task group 1: TODO\n\n"
        "- [ ] E-01 TODO one observable action.\n"
        "  - Depends on: none\n"
        "  - Expected outcome: TODO observable result.\n"
        "  - Execution state: pending\n\n"
        f"Add further leaves as `- [ ] {UNASSIGNED_MARKER} <action>` and run `aw ipd sync` to assign ids."
    )


def _validation_placeholder() -> str:
    return (
        "- [ ] V-01 validates E-01\n"
        "  - Required evidence: TODO falsifiable evidence.\n"
        "  - Observed evidence:\n"
        "  - Result: pending"
    )


def _gate_body() -> str:
    return (
        "- Size assessment: standard\n"
        "- Cohesion rationale: not required\n\n"
        "TODO: approval + execution gate prose (execution contract, post-gate lifecycle move)."
    )


# --------------------------------------------------------------------------------------
# Authoring-placeholder predicate (agentadhere Phase 1, IPD uisjns E-03; catalog invariant I-12).
# --------------------------------------------------------------------------------------

# The ANCHORED scaffold placeholder markers emitted by `scaffold_text` above (OQ-02: match the
# LITERAL scaffold tokens, NOT a bare `TODO` substring, so legitimate prose containing the word
# "TODO" never false-positives). Each entry is a substring that appears in the scaffold output and
# is meant to be REPLACED by the author. Kept in lock-step with the scaffold helpers above; if a
# scaffold placeholder string changes, update it here (and the E-03 test pins this coupling).
_AUTHORING_PLACEHOLDERS = (
    "- Concern: TODO.",
    "- Scope: TODO.",
    "- Scope-Paths: TODO",
    "- Item-Dependencies: unresolved",
    _SECTION_BODY[
        S.H_GOAL
    ],  # "TODO: one or two sentences on what this plan achieves and why."
    "- [ ] E-01 TODO one observable action.",
    "  - Expected outcome: TODO observable result.",
    "  - Required evidence: TODO falsifiable evidence.",
    "### OQ-01: TODO a question",
    "TODO: approval + execution gate prose",
    UNASSIGNED_MARKER,  # any remaining unassigned `E-NEW` leaf means still authoring
)


def authoring_placeholders_resolved(plan_text: str) -> bool:
    """True iff a plan's text contains NONE of the anchored scaffold authoring placeholders.

    A freshly scaffolded IPD is peppered with literal `TODO.`/`unresolved`/`E-NEW`/placeholder-body
    markers (see `scaffold_text`). While ANY of them remains, the plan is still a stub and MUST NOT
    be nudged toward `to-review`. When ALL are replaced by real authored content, the draft is
    "ready" and the `check.ipd-draft-ready-to-review` rule may nudge the author to advance it.

    Conservative and anchored (OQ-02): it matches the exact scaffold marker strings, so narrative
    prose that merely contains the word "TODO" does not count as an unresolved placeholder.
    """
    return not any(marker in plan_text for marker in _AUTHORING_PLACEHOLDERS)


def normalize_author(author: str) -> str:
    """The author string in the shape the history readers and the setter guard accept.

    Parentheses become the `key=value` form :func:`oc_runipd.driver_actor` already emits, so the
    tooling stops PRODUCING a shape its own setter refuses (plan fn2l1u E-05, resolving OQ-02).

    WHY THIS EXISTS, since a cosmetic front-matter field looks harmless. ``--author`` reaches TWO
    places, not one: the ``- Author:`` field AND the scaffold's own first history line,
    ``- <date> draft (<author>): created.``. A parenthesized author therefore made scaffold WRITE an
    unparseable history record into every new plan, and 274 of 638 tracked plans carry that shape in
    the field agents then copy into ``--actor``. Normalizing here fixes both write sites at once.

    NORMALIZED, NOT REFUSED, and the CALLER MUST SAY SO: the maintainer's OQ-02 ruling took a third
    option over this plan's own recommendation of a silent rewrite - normalize, but print one line
    telling the caller the value changed, because otherwise the string the user typed is not the
    string recorded. A scaffold call that rewrites the author SILENTLY does not satisfy OQ-02.
    ``run_scaffold`` emits that notice; keep it one line and not styled as an error.

    Pure. Returns the input unchanged (only stripped) when it carries no parenthesis, so the common
    case is untouched and no existing plan's rendering moves.
    """
    text = (author or "").strip()
    if "(" not in text and ")" not in text:
        return text
    # `opencode (its_direct/some-model)` -> `opencode model=its_direct/some-model`, matching
    # `driver_actor`'s rule. A parenthetical that is not a bare model (contains whitespace or an `=`
    # already) is flattened rather than key-tagged, since inventing a key for arbitrary prose would
    # be a guess; either way the result is parenthesis-free, which is what the guard requires.
    m = re.match(r"^(?P<head>[^(]*?)\s*\((?P<inner>.*)\)\s*$", text)
    if m:
        head = m.group("head").strip()
        inner = m.group("inner").strip().replace("(", "").replace(")", "")
        if head and inner:
            tagged = inner if ("=" in inner or " " in inner) else f"model={inner}"
            return f"{head} {tagged}"
        return (head or inner).strip()
    return text.replace("(", "").replace(")", "").strip()


def build_skeleton(
    *,
    kind: str,
    title: str,
    author: str,
    when: str,
    set_name: Optional[str],
    order: Optional[int],
    plan_id: Optional[str] = None,
) -> str:
    """Return a conformant IPD skeleton for ``kind`` from the schema's H2 order.

    ``plan_id`` is the stable ``- Id:`` handle (6-char base36); when omitted a fresh one is
    generated. Deterministic output for tests can pin ``plan_id``.

    The author is NORMALIZED through :func:`normalize_author` (plan fn2l1u E-05), which covers BOTH
    places it lands - the ``- Author:`` field and the ``draft`` history line - so a parenthesized
    ``--author`` can no longer put an unparseable record into a brand-new plan.
    """
    if plan_id is None:
        # IPD sk7ggr E-02. REACHABILITY, MEASURED: no PRODUCTION path reaches this branch today.
        # `build_skeleton` is the only holder of the old `generate_id6(set())`, and its single
        # production caller (`run_scaffold`, below) always passes `plan_id=plan_id` explicitly; every
        # other caller is under `tests/`. So this was a LATENT TRAP, not a live minting bug.
        #
        # It is fixed rather than merely documented because unreachability is exactly the property a
        # future caller can change silently, and the failure mode is invisible: `generate_id6(set())`
        # checks a candidate against NOTHING, so any id6 it returns is "unique" by vacuous truth and a
        # duplicate is only discovered once the plan is written and cited. Minting against the
        # repository-wide set costs one scan on a path that writes a file anyway.
        #
        # A caller that wants determinism must PIN `plan_id` (the documented contract above); it must
        # not rely on this default being unchecked.
        plan_id = _core.mint_id6(_core.repo_root_of(Path.cwd()))
    author = normalize_author(author)
    order_seq = S.H2_ORDER_BY_KIND[kind]
    lines: List[str] = []
    lines.append(f"# IPD: {title}")
    lines.append("")
    # Metadata block.
    lines.append(f"- Date: {when}")
    lines.append(f"- Kind: {kind}")
    lines.append("- Concern: TODO.")
    lines.append("- Scope: TODO.")
    # Scope-Paths (Order oorry1): the machine-readable allowlist of repo-relative paths this plan
    # may change. Replace the TODO with a comma-separated list of literal paths or bounded
    # pathspecs (e.g. `agent_workflows/foo.py, tests/test_foo.py`), or the reserved sentinel
    # `grandfathered` for a pre-cutoff plan. REQUIRED at the ready-to-execute gate (pre-execution /
    # approved), OPTIONAL while drafting. Absolute paths, `..` escapes, and repo-wide globs are
    # rejected; the plan's own lifecycle artifacts under .aw/records/plans/** are implicit.
    lines.append(
        "- Scope-Paths: TODO (comma-separated repo-relative paths or pathspecs)"
    )
    # Item-Dependencies (ipddeps Order g69y23; spec 25kzda 2.7): the machine-readable, id6-grounded
    # cross-IPD prerequisite statement. Scaffold emits the reserved `unresolved` sentinel (NEVER
    # blank, NEVER `none`) so a freshly scaffolded plan is an HONEST not-ready draft: `unresolved`
    # is a declared-but-not-triaged marker distinct from `none` (an explicit assertion of zero
    # cross-IPD dependencies). Replace it with `none` or a comma-separated edge list
    # (`executed:<id6>` | `exists:<type>:<id6>` | `state:<type>:<status>:<id6>`) via
    # `aw ipd dependencies set`. Positioned immediately after `Scope-Paths` (spec 2.7). DIFFERENT
    # from the intra-plan `Depends on:` E-item ordering.
    lines.append("- Item-Dependencies: unresolved")
    lines.append("- Status: draft")
    lines.append(f"- Set: {set_name}")
    lines.append(f"- Order: {order}")
    lines.append("- Highest E allocated: 01")
    lines.append(f"- Author: {author}")
    lines.append(f"- Id: {plan_id}")
    lines.append("")
    for h in order_seq:
        lines.append(f"## {h}")
        lines.append("")
        if h == S.H_EXECUTION:
            lines.append(_EXEC_INTRO)
            lines.append("")
            lines.append(_exec_placeholder_leaf())
        elif h in (S.H_VALIDATION_CHILD, S.H_VALIDATION_ORCH):
            lines.append(_VALID_INTRO)
            lines.append("")
            lines.append(_validation_placeholder())
        elif h == S.H_OPEN_QUESTIONS:
            lines.append("### OQ-01: TODO a question")
            lines.append("")
            lines.append("- Blocking: no")
            lines.append("- Status: open")
            lines.append("- Owner: none")
            lines.append("- Resolution or deferral rationale: TODO.")
        elif h == S.H_APPROVAL_GATE:
            lines.append(_gate_body())
        else:
            body = _SECTION_BODY.get(h, "TODO.")
            lines.append(body.format(date=when, author=author))
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def _atomic_write(path: Path, text: str) -> None:
    """Write-to-temp-then-rename so an interrupted apply never leaves a partial file (core).

    DELEGATES rather than duplicating, which is the repository's one-mechanism convention
    (``oc_models._atomic_write`` already states it). This body USED to be a byte-for-byte copy of the
    core helper's, and that duplication had a real cost: PLANS are the highest-volume artifact an agent
    writes, ``aw ipd scaffold``/``aw ipd sync`` write them through HERE, and so normalizing only
    ``artifact_core.atomic_write`` would have left plans un-normalized -- the exact churn the
    normalization exists to remove, on the exact tree it matters most for. Delegating means plans
    inherit the markdown trailing-whitespace normalization automatically.
    """
    _core.atomic_write(path, text, prefix=".ipd-tmp-")


_ID_LINE_RE = re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")


def _plans_root_for(path: Path) -> Optional[Path]:
    """Find the plans dir enclosing ``path`` (walk up), or resolve via router."""
    from agent_workflows.record_producers import resolve_record_path

    for parent in [path] + list(path.parents):
        try:
            cand = resolve_record_path("plans", target_repo=str(parent))
            if cand.is_dir():
                return cand
        except Exception:
            pass
        if parent.name == "plans":
            return parent
    return None


def _existing_plan_ids(target_path: Path) -> set:
    """Collect every `- Id:` already present across plans/** (for collision checks)."""

    ids: set = set()
    root = _plans_root_for(target_path.resolve())
    if root is None:
        return ids
    for f in root.rglob("*.md"):
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        m = _ID_LINE_RE.search(text)
        if m:
            ids.add(m.group(1))
    return ids


def _setid_length_guard(setid, *, verb: str, repo_root=None) -> int:
    """Apply the shared setid-length guard, printing its error/warning. 0 to proceed, 2 to refuse.

    setidlen `x75obw` E-06. The comparison itself lives in
    :func:`config.validate_setid_length_for_authoring` and is NEVER re-spelled here; this wrapper only
    decides how `aw ipd scaffold` reports it (stdout `error:`/`note:`, matching the messages around it).
    """
    from pathlib import Path as _Path

    from agent_workflows import config as _config

    if repo_root is None:
        try:
            from agent_workflows import project_context as _ctx

            repo_root = _ctx.find_project_root(_Path.cwd()) or _Path.cwd()
        except Exception:
            repo_root = _Path.cwd()
    err, warn = _config.validate_setid_length_for_authoring(repo_root, setid, verb=verb)
    if err:
        print(f"error: {err}")
        return 2
    if warn:
        print(f"note: {warn}")
    return 0


def run_scaffold(args: argparse.Namespace) -> int:
    kind = getattr(args, "kind", None)
    if kind not in S.KINDS:
        print("error: --kind must be child or orchestrator")
        return 2
    title = getattr(args, "title", None)
    target = getattr(args, "path", None)
    if not title:
        print("error: --title is required")
        return 2
    set_name = getattr(args, "set", None)
    order = getattr(args, "order", None)
    if set_name is None:
        print("error: --set is required")
        return 2
    if order is None:
        print("error: --order is required")
        return 2
    # setidlen x75obw E-06 (catalog I-17): the ONE shared setid-length guard, not a local comparison.
    # Refuses over `max_length`; WARNS and proceeds over `warn_length`.
    if _setid_length_guard(set_name, verb="aw ipd scaffold") != 0:
        return 2
    if kind == S.KIND_ORCHESTRATOR and order != 0:
        print("error: orchestrator Order must be 0")
        return 2
    if kind == S.KIND_CHILD and order < 1:
        print("error: child Order must be >= 1")
        return 2
    author = getattr(args, "author", None) or os.environ.get("AW_IPD_AUTHOR")
    if not author:
        print("error: --author is required (or set AW_IPD_AUTHOR)")
        return 2
    # OQ-02, as the maintainer ruled it: NORMALIZE the author, AND SAY SO. A silent rewrite would
    # mean the string the caller typed is not the string recorded, which is a small surprise of its
    # own; one line removes it without refusing an otherwise harmless call. Deliberately NOT styled
    # as an error (this is a cosmetic field), and printed only when the value actually changed.
    _author_normalized = normalize_author(author)
    if _author_normalized != author.strip():
        print(
            f"note: normalized --author to {_author_normalized!r} (parentheses are not used in an "
            "actor/author; qualifiers are rendered key=value so history records stay parseable)"
        )
    author = _author_normalized
    when = date.today().strftime("%Y-%m-%d")
    # An explicit --path is validated against the clustering grammar unless --legacy-name is passed.
    # When --path is omitted, we DERIVE the canonical clustered `.ipd.md` name into `.aw/records/plans/pending/`.
    if target:
        path = Path(target)
        legacy_name = getattr(args, "legacy_name", False)
        from agent_workflows import plans_refs as _refs

        m = _refs._CLUSTERED_RE.match(path.name)
        if not legacy_name:
            if not m or m.group("type") != "ipd":
                print(
                    "error: --path must follow clustering grammar "
                    "YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md (pass --legacy-name to override)"
                )
                return 2
            plan_id = m.group("id6")
        else:
            if m and m.group("type") == "ipd":
                plan_id = m.group("id6")
            else:
                # IPD sk7ggr E-01: repository-wide mint, unioned with the plans tree's own ids.
                plan_id = _core.mint_id6(
                    _core.repo_root_of(path), _existing_plan_ids(path)
                )
    else:
        from agent_workflows import plans_refs as _refs
        from agent_workflows import project_context as _ctx

        try:
            repo_root = _ctx.find_project_root(Path.cwd())
        except Exception:
            repo_root = None
        if repo_root is None:
            repo_root = Path.cwd()
        pending = repo_root / ".aw" / "records" / "plans" / "pending"
        # IPD sk7ggr E-01: repository-wide mint. NOTE the previous per-tree set was `pending` ONLY, so
        # it did not even cover `executed/`; a fresh plan id6 could equal an executed plan's, which is
        # the exact shape of the measured `uyeko5` case.
        plan_id = _core.mint_id6(repo_root, _existing_plan_ids(pending))
        slug = _refs._core.kebab(title)[:60] or "ipd"
        name = _refs.clustered_name(
            date=date.today().strftime("%Y%m%d"),
            set_id=set_name,
            order=order,
            id6=plan_id,
            slug=slug,
            artifact_type="ipd",
        )
        path = pending / name
        target = str(path)
    text = build_skeleton(
        kind=kind,
        title=title,
        author=author,
        when=when,
        set_name=set_name,
        order=order,
        plan_id=plan_id,
    )
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        Change,
        CommandResult,
        select_output,
    )

    ctx = select_output(args)
    if path.exists() and not getattr(args, "overwrite", False):
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="ipd scaffold",
                status="findings",
                exit_code=1,
                summary=f"refusing to overwrite existing path (pass --overwrite): {target}",
            )
            return get_renderer(ctx).emit(res, ctx)
        print(
            f"error: refusing to overwrite existing path (pass --overwrite): {target}"
        )
        return 1

    if not getattr(args, "apply", False):
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="ipd scaffold",
                status="clean",
                exit_code=0,
                summary=f"would write {target} ({text.count(chr(10))} lines)",
                changes=[Change(path=str(path), kind="create", applied=False)],
                data={"path": str(path), "id": plan_id},
                verified=True,
                complete=True,
            )
            return get_renderer(ctx).emit(res, ctx)
        print(f"--- would write {target} ({text.count(chr(10))} lines) ---")
        print(text)
        return 0

    try:
        _atomic_write(path, text)
    except Exception as exc:
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="ipd scaffold",
                status="cannot-run",
                exit_code=2,
                summary=f"scaffold write failed: {exc}",
            )
            return get_renderer(ctx).emit(res, ctx)
        print(f"error: scaffold write failed: {exc}")
        return 2

    if ctx.is_agent or ctx.is_json:
        res = CommandResult(
            command="ipd scaffold",
            status="clean",
            exit_code=0,
            summary=f"wrote {target}",
            changes=[Change(path=str(path), kind="create", applied=True)],
            data={"path": str(path), "id": plan_id},
            verified=True,
            complete=True,
        )
        return get_renderer(ctx).emit(res, ctx)

    print(f"wrote {target}")
    return 0


# --------------------------------------------------------------------------------------
# Sync
# --------------------------------------------------------------------------------------

_UNASSIGNED_LEAF_RE = re.compile(rf"^- \[ \] {re.escape(UNASSIGNED_MARKER)}\b(.*)$")
_WATERMARK_RE = re.compile(r"^- Highest E allocated:\s*([0-9]+)\s*$")
_VALIDATION_HEADING_RE = re.compile(r"^## Validation and cross-check\b")
_GATE_HEADING_RE = re.compile(r"^## Approval and execution gate\b")


def _fmt_suffix(n: int) -> str:
    return f"{n:02d}"


class SyncResult:
    def __init__(self) -> None:
        self.new_text = ""
        self.assigned: List[str] = []
        self.errors: List[str] = []
        self.changed = False


def compute_sync(text: str, *, directory: Optional[str]) -> SyncResult:
    """Compute the sync result for ``text``. Pure: returns new text + assigned ids + errors."""
    res = SyncResult()

    # Preflight with the linter's parser and refuse on any structural error EXCEPT the presence of
    # unassigned E-NEW leaves (which is exactly what we are here to fix).
    doc = LINT.parse(text)
    status = doc.meta_fields.get("Status", "")
    # Refuse structural change once execution has begun or approval is granted (Section 6.1).
    if status in ("approved", "auto-approved"):
        res.errors.append(
            f"refusing sync: Status is '{status}'; use the amendment/re-review workflow"
        )
        return res
    # Any non-initial execution/validation state means execution has begun -> refuse.
    for lf in doc.exec_leaves:
        if lf.kind == "E" and (
            lf.checked or lf.fields.get("Execution state", "pending") != "pending"
        ):
            res.errors.append(
                f"refusing sync: execution has begun ({lf.ident} is not pending); use amendment/re-review"
            )
            return res
    for lf in doc.valid_leaves:
        if lf.kind == "V" and (
            lf.checked
            or lf.fields.get("Result", "pending") != "pending"
            or lf.fields.get("Observed evidence", "").strip()
        ):
            res.errors.append(
                f"refusing sync: validation has begun ({lf.ident}); use amendment/re-review"
            )
            return res

    # Watermark preflight.
    wm_raw = doc.meta_fields.get(S.META_WATERMARK)
    if wm_raw is None:
        res.errors.append("refusing sync: metadata is missing 'Highest E allocated'")
        return res
    try:
        watermark = int(wm_raw)
    except ValueError:
        res.errors.append("refusing sync: 'Highest E allocated' is not an integer")
        return res
    present = [
        S.suffix_of(lf.ident)
        for lf in doc.exec_leaves
        if lf.kind == "E" and S.suffix_of(lf.ident) is not None
    ]
    werr = S.watermark_error(watermark, [p for p in present if p is not None])
    if werr:
        res.errors.append(f"refusing sync: {werr}")
        return res

    # Locate unassigned leaves in source order; assign from watermark+1.
    lines = text.splitlines()
    next_suffix = watermark + 1
    new_v_rows: List[str] = []
    out: List[str] = []
    in_exec = False
    for raw in lines:
        if raw.startswith("## "):
            in_exec = raw[3:].strip() == S.H_EXECUTION
        if in_exec:
            m = _UNASSIGNED_LEAF_RE.match(raw)
            if m:
                new_id = "E-" + _fmt_suffix(next_suffix)
                out.append(f"- [ ] {new_id}{m.group(1)}")
                res.assigned.append(new_id)
                new_v_rows.append(
                    f"- [ ] V-{_fmt_suffix(next_suffix)} validates {new_id}\n"
                    "  - Required evidence: TODO falsifiable evidence.\n"
                    "  - Observed evidence:\n"
                    "  - Result: pending"
                )
                next_suffix += 1
                continue
        out.append(raw)

    if not res.assigned:
        # Nothing to do; still valid (idempotent no-op).
        res.new_text = text
        res.changed = False
        return res

    new_watermark = next_suffix - 1
    # Advance the watermark line.
    for i, raw in enumerate(out):
        if _WATERMARK_RE.match(raw):
            out[i] = f"- Highest E allocated: {_fmt_suffix(new_watermark)}"
            break

    # Insert the new V rows immediately before the approval gate, appended after existing V rows.
    # Find the gate heading; insert new V rows just before its preceding blank line.
    gate_idx = None
    for i, raw in enumerate(out):
        if _GATE_HEADING_RE.match(raw):
            gate_idx = i
            break
    if gate_idx is None:
        res.errors.append(
            "refusing sync: no approval gate heading to anchor validation rows"
        )
        return res
    # Walk back over trailing blank lines before the gate.
    insert_at = gate_idx
    while insert_at - 1 >= 0 and out[insert_at - 1].strip() == "":
        insert_at -= 1
    v_block: List[str] = []
    for row in new_v_rows:
        v_block.append(row)
    out[insert_at:insert_at] = v_block + [""]

    res.new_text = "\n".join(out).rstrip("\n") + "\n"
    res.changed = True
    return res


def _backfill_id(text: str, existing: set) -> tuple[str, Optional[str]]:
    """Insert a `- Id:` line after `- Author:` if the block lacks one. Returns (new_text, id|None)."""

    if _ID_LINE_RE.search(text):
        return text, None
    new_id = _core.generate_id6(existing)
    # Insert immediately after the `- Author:` metadata line.
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("- Author:"):
            nl = "\n" if line.endswith("\n") else ""
            lines.insert(i + 1, f"- Id: {new_id}{nl}")
            return "".join(lines), new_id
    return text, None  # no Author line; leave untouched (lint will flag the missing Id)


def run_sync(args: argparse.Namespace) -> int:
    target = getattr(args, "path", None)
    if not target:
        print("error: a FILE is required")
        return 2
    path = Path(target)
    if not path.is_file():
        print(f"error: not a file: {target}")
        return 2
    try:
        text = path.read_text(encoding="utf-8")
        # Backfill a missing stable `Id` first (plans-adopter Order 02), then sync E/V leaves.
        # IPD sk7ggr E-01: a BACKFILLED id6 is a mint like any other, so it is collision-checked
        # against the repository-wide set (unioned with the plans tree's ids), not the plans tree alone.
        text_after_id, backfilled_id = _backfill_id(
            text,
            _existing_plan_ids(path) | _core.global_id6s(_core.repo_root_of(path)),
        )
        res = compute_sync(text_after_id, directory=LINT._dir_of(path))
    except Exception as exc:
        print(f"error: sync failed to run: {exc}")
        return 2
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        Change,
        CommandResult,
        Diagnostic,
        select_output,
    )

    ctx = select_output(args)
    if res.errors:
        if ctx.is_agent or ctx.is_json:
            diagnostics = [
                Diagnostic(
                    location=str(path),
                    rule="ipd.sync_error",
                    detail=str(e),
                    severity="error",
                )
                for e in res.errors
            ]
            res_cmd = CommandResult(
                command="ipd sync",
                status="findings",
                exit_code=1,
                summary=f"sync failed with {len(res.errors)} error(s)",
                diagnostics=diagnostics,
            )
            return get_renderer(ctx).emit(res_cmd, ctx)
        for e in res.errors:
            print(e)
        return 1

    if not res.changed and backfilled_id is None:
        if ctx.is_agent or ctx.is_json:
            res_cmd = CommandResult(
                command="ipd sync",
                status="clean",
                exit_code=0,
                summary="no unassigned leaves and Id present; nothing to sync",
                changes=[],
                verified=True,
                complete=True,
            )
            return get_renderer(ctx).emit(res_cmd, ctx)
        print("no unassigned leaves and Id present; nothing to sync")
        return 0

    if not getattr(args, "apply", False):
        parts = []
        if backfilled_id is not None:
            parts.append(f"Id {backfilled_id}")
        if res.assigned:
            parts.append(", ".join(res.assigned))
        if ctx.is_agent or ctx.is_json:
            res_cmd = CommandResult(
                command="ipd sync",
                status="clean",
                exit_code=0,
                summary=f"would assign: {'; '.join(parts)}",
                changes=[
                    Change(
                        path=str(path),
                        kind="update",
                        applied=False,
                        detail="; ".join(parts),
                    )
                ],
                verified=True,
                complete=True,
            )
            return get_renderer(ctx).emit(res_cmd, ctx)
        print(
            "--- would assign: {0} (dry-run; pass --apply) ---".format("; ".join(parts))
        )
        return 0

    try:
        _atomic_write(path, res.new_text)
    except Exception as exc:
        if ctx.is_agent or ctx.is_json:
            res_cmd = CommandResult(
                command="ipd sync",
                status="cannot-run",
                exit_code=2,
                summary=f"sync write failed: {exc}",
            )
            return get_renderer(ctx).emit(res_cmd, ctx)
        print(f"error: sync write failed: {exc}")
        return 2

    done = []
    if backfilled_id is not None:
        done.append(f"backfilled Id {backfilled_id}")
    if res.assigned:
        done.append("assigned {0}; watermark advanced".format(", ".join(res.assigned)))

    if ctx.is_agent or ctx.is_json:
        res_cmd = CommandResult(
            command="ipd sync",
            status="clean",
            exit_code=0,
            summary="; ".join(done) if done else "synced",
            changes=[
                Change(
                    path=str(path), kind="update", applied=True, detail="; ".join(done)
                )
            ],
            verified=True,
            complete=True,
        )
        return get_renderer(ctx).emit(res_cmd, ctx)

    print("; ".join(done) if done else "synced")
    return 0
