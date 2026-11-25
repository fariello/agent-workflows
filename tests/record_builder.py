"""Shared legacy-format test record builder routed through ``artifact_meta``.

All tracked test fixtures for the 8 governed record types are built through
``RecordBuilder`` rather than inline header strings. Every write goes through
``artifact_meta`` (or ``review_findings`` for ``review``), validates fields,
status values, IDs, and placement rules before writing, uses deterministic
dates (``DEFAULT_WHEN = "2026-08-24"``), and enforces ``RECORD_FORMAT == "legacy"``.

Golden baseline provenance (``j6o96i`` E-13 / V-16):
``tests/fixtures/record_builder/ready_plan_text_golden.json`` was generated
before modifying ``tests/support.py`` or adding this module by executing::

    python3 -m pytest -o addopts="" -m "" -n 0 <16 ready_plan_text caller test modules>

with ``tests.support.ready_plan_text`` instrumented to record unique normalized
keyword argument dictionaries and their returned strings, producing 64 distinct
golden parameter sets checked byte-for-byte after the ``ready_plan_text``
delegation change.
"""

from __future__ import annotations

import datetime as _dt
import re as _re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from agent_workflows import (
    artifact_core as _core,
)
from agent_workflows import (
    artifact_meta as _meta,
)
from agent_workflows import (
    artifact_naming as _naming,
)
from agent_workflows import (
    attention_contract as _attention,
)
from agent_workflows import (
    backlog as _backlog,
)
from agent_workflows import (
    ipd_authoring as _authoring,
)
from agent_workflows import (
    lifecycle_dirs as _lifecycle_dirs,
)
from agent_workflows import (
    plans as _plans,
)
from agent_workflows import (
    prompts as _prompts,
)
from agent_workflows import (
    releases as _releases,
)
from agent_workflows import (
    research_contract as _research_contract,
)
from agent_workflows import (
    review_findings as _review_findings,
)

RECORD_FORMAT = "legacy"
DEFAULT_WHEN = "2026-08-24"
DEFAULT_PRIORITY = "medium"
DEFAULT_WORK_KIND = "chore"

_ACTOR: dict[str, Any] = {"tool": "record_builder"}

_PLURAL_FOR_TYPE: dict[str, str] = {
    "ipd": "plans",
    "spec": "specs",
    "backlog": "backlog",
    "research": "research",
    "release": "releases",
    "prompt": "prompts",
    "walkthrough": "walkthroughs",
    "review": "reviews",
}

_FACET_FOR_TYPE: dict[str, str] = {
    "ipd": "ipd",
    "spec": "spec",
    "backlog": "backlog",
    "release": "release",
    "prompt": "prompt",
    "walkthrough": "walkthrough",
}

_VALID_STATUSES: dict[str, frozenset[str]] = {
    "ipd": frozenset(_plans.RECOGNIZED),
    "spec": frozenset(_attention.SPEC_STATUSES),
    "backlog": frozenset(_backlog.STATUSES),
    "research": frozenset(_research_contract.STATUSES),
    "release": frozenset(_releases.RELEASE_STATUSES),
    "prompt": frozenset(_attention._PROMPTS_MAP.keys()),
}

_BULLET_LABELS: dict[str, str] = {
    **_meta._LEGACY_BULLET_LABEL,
    "id": "Id",
    "status": "Status",
    "work_kind": "Work-Kind",
    "priority": "Priority",
    "from_backlog": "From-Backlog",
    "from_spec": "From-Spec",
    "blocks_release": "Blocks-Release",
    "item_dependencies": "Item-Dependencies",
    "graduated_to": "Graduated-To",
    "release_exempt_kind": "Release-Exempt-Kind",
    "release_exempt_ref": "Release-Exempt-Ref",
    "close_evidence": "Close-Evidence",
    "implemented": "Implemented",
}

_YAML_KEYS: dict[str, str] = {
    "id": "id",
    "created": "created",
    "created_day": "created",
    "set": "set",
    "order": "order",
    "topic": "topic",
    "model": "model",
    "research_kind": "kind",
    "kind": "kind",
    "status": "status",
    "outcome": "outcome",
    "summary": "summary",
    "consumed_by": "consumed-by",
    "priority": "priority",
    "ace": "ace",
    "short_description": "short-description",
}

_PROMPT_KEYS: dict[str, str] = {
    "prompt_kind": "Kind",
    "kind": "Kind",
    "id": "Id",
    "set": "Set",
    "status": "Status",
    "created_day": "Created",
    "author": "Author",
    "targets": "Targets",
    "concerns": "Concerns",
    "results_go_to": "Results-Go-To",
    "results": "Results",
    "grounding": "Grounding",
    "goal": "Goal",
    "reviews_spec": "Reviews-Spec",
    "basis": "Basis",
    "relation": "Relation",
    "short_description": "Short-Description",
}


def _require_legacy_format() -> None:
    if RECORD_FORMAT != "legacy":
        raise ValueError(
            f"unsupported RECORD_FORMAT {RECORD_FORMAT!r}; expected 'legacy'"
        )


def _validate_day(when: str) -> str:
    if not isinstance(when, str) or not _re.fullmatch(r"\d{4}-\d{2}-\d{2}", when):
        raise ValueError(f"invalid date {when!r}; expected YYYY-MM-DD")
    _dt.date.fromisoformat(when)
    return when.replace("-", "")


def _validate_id(id6: str) -> str:
    _meta.validate_id6(id6)
    return id6


def _resolve_alias(
    primary: str | None,
    alias: str | None,
    *,
    primary_name: str,
    alias_name: str,
    default: str | None = None,
) -> str | None:
    if primary is not None and alias is not None and primary != alias:
        raise ValueError(
            f"conflicting {primary_name}={primary!r} and {alias_name}={alias!r}"
        )
    if primary is not None:
        return primary
    if alias is not None:
        return alias
    return default


def _validate_fields(record_type: str, fields: dict[str, Any]) -> None:
    allowed = frozenset(_meta.registry_fields(record_type)) - {"type"}
    for key in fields:
        if key not in allowed:
            raise ValueError(f"unknown field {key!r} for record type {record_type!r}")


def _validate_status(
    record_type: str,
    status: str | None,
    *,
    allow_none: bool = False,
) -> None:
    if status is None:
        if allow_none:
            return
        raise ValueError(f"status must not be None for record type {record_type!r}")
    valid = _VALID_STATUSES.get(record_type)
    if valid is not None and status not in valid:
        raise ValueError(
            f"illegal status {status!r} for record type {record_type!r}; "
            f"expected one of {sorted(valid)}"
        )


def _resolve_disposition(
    plural: str,
    default_disposition: str | None,
    disposition: str | None,
) -> str | None:
    subdirs = _lifecycle_dirs.LIFECYCLE_SUBDIRS.get(plural)
    if subdirs is None:
        if disposition is not None:
            raise ValueError(
                f"record type {plural!r} has no lifecycle subdirectories; "
                f"got disposition={disposition!r}"
            )
        return None
    chosen = default_disposition if disposition is None else disposition
    if chosen not in subdirs:
        raise ValueError(
            f"illegal disposition {chosen!r} for {plural!r}; expected one of {subdirs}"
        )
    return chosen


def _normalize_history_entry(
    entry: str | dict[str, Any], default_day: str, default_actor: str
) -> str:
    if isinstance(entry, str):
        stripped = entry.strip()
        if not stripped:
            return ""
        return stripped if stripped.startswith("- ") else f"- {stripped}"
    if isinstance(entry, dict):
        day = entry.get("day", default_day)
        tag = entry.get("tag") or entry.get("status") or "note"
        actor = entry.get("actor", default_actor)
        msg = entry.get("message") if "message" in entry else entry.get("note", "")
        return f"- {day} {tag} ({actor}): {msg}".rstrip()
    raise TypeError(f"history entry must be str or dict, got {type(entry).__name__}")


def _replace_section(text: str, heading_pattern: str, new_body_lines: list[str]) -> str:
    lines = text.splitlines()
    heading_re = _re.compile(heading_pattern)
    start_idx: int | None = None
    for idx, line in enumerate(lines):
        if heading_re.match(line):
            start_idx = idx
            break
    if start_idx is None:
        return text
    end_idx = len(lines)
    for idx in range(start_idx + 1, len(lines)):
        if lines[idx].startswith("## "):
            end_idx = idx
            break
    replacement: list[str] = [lines[start_idx]]
    if new_body_lines:
        replacement.append("")
        replacement.extend(new_body_lines)
        if end_idx < len(lines):
            replacement.append("")
    elif end_idx < len(lines):
        replacement.append("")
    updated = lines[:start_idx] + replacement + lines[end_idx:]
    return "\n".join(updated).rstrip("\n") + "\n"


def _apply_history(
    text: str,
    history: Sequence[str | dict[str, Any]] | None,
    *,
    default_day: str,
    default_actor: str,
) -> str:
    if history is None:
        return text
    entries = [
        line
        for line in (
            _normalize_history_entry(item, default_day, default_actor)
            for item in history
        )
        if line
    ]
    if _re.search(r"(?m)^## Workflow history\s*$", text):
        return _replace_section(text, r"^## Workflow history\s*$", entries)
    suffix = "## Workflow history\n"
    if entries:
        suffix += "\n" + "\n".join(entries) + "\n"
    return text.rstrip("\n") + "\n\n" + suffix


def _apply_plan_body(text: str, body: str | None) -> str:
    if body is None:
        return text
    lines = text.splitlines()
    hist_idx: int | None = None
    for idx, line in enumerate(lines):
        if line.strip() == "## Workflow history":
            hist_idx = idx
            break
    if hist_idx is None:
        return text.rstrip("\n") + "\n\n" + body.lstrip("\n").rstrip("\n") + "\n"
    end_hist = len(lines)
    for idx in range(hist_idx + 1, len(lines)):
        if lines[idx].startswith("## "):
            end_hist = idx
            break
    head = "\n".join(lines[:end_hist]).rstrip("\n")
    cleaned_body = body.strip("\n")
    if not cleaned_body:
        return head + "\n"
    return head + "\n\n" + cleaned_body + "\n"


def _apply_open_questions(
    text: str,
    open_questions: str | Sequence[str] | None,
) -> str:
    if open_questions is None:
        return text
    if isinstance(open_questions, str):
        oq_lines = (
            open_questions.strip("\n").splitlines() if open_questions.strip() else []
        )
    else:
        oq_lines = []
        for item in open_questions:
            oq_lines.extend(str(item).rstrip("\n").splitlines())
    if _re.search(r"(?m)^## Open [Qq]uestions\s*$", text):
        return _replace_section(text, r"^## Open [Qq]uestions\s*$", oq_lines)
    if not oq_lines:
        return text
    return text.rstrip("\n") + "\n\n## Open questions\n\n" + "\n".join(oq_lines) + "\n"


def _insert_unknown_bullet(text: str, label: str, value: str) -> str:
    region = _meta.metadata_region(text)
    rest = text[len(region) :]
    new_line = f"- {label}: {value}\n"
    anchor = _re.search(r"(?m)^-\s*(?:Status|Id):[^\n]*(?:\n|$)", region)
    if anchor:
        idx = anchor.end()
        if not anchor.group(0).endswith("\n"):
            return region[:idx] + "\n" + new_line + region[idx:] + rest
        return region[:idx] + new_line + region[idx:] + rest
    heading = _re.search(r"(?m)^# [^\n]*\n", region)
    if heading:
        idx = heading.end()
        return region[:idx] + "\n" + new_line + region[idx:] + rest
    return new_line + text


def _apply_raw_yaml_fields(text: str, raw_fields: dict[str, Any]) -> str:
    match = _re.match(r"^---\n(.*?)\n---\n(.*)$", text, _re.DOTALL)
    if not match:
        return text
    fm_lines = match.group(1).splitlines()
    body = match.group(2)
    for raw_key, raw_val in raw_fields.items():
        ykey = _YAML_KEYS.get(raw_key, raw_key)
        pat = _re.compile(r"^" + _re.escape(ykey) + r":.*$")
        if raw_val is None:
            fm_lines = [line for line in fm_lines if not pat.match(line)]
            continue
        rendered_val = "" if raw_val == "" else str(raw_val)
        new_line = f"{ykey}: {rendered_val}" if rendered_val else f"{ykey}: "
        replaced = False
        updated_lines: list[str] = []
        for line in fm_lines:
            if pat.match(line):
                if not replaced:
                    updated_lines.append(new_line)
                    replaced = True
            else:
                updated_lines.append(line)
        if not replaced:
            updated_lines.append(new_line)
        fm_lines = updated_lines
    return "---\n" + "\n".join(fm_lines) + "\n---\n" + body


def _apply_raw_prompt_fields(text: str, raw_fields: dict[str, Any]) -> str:
    lines = text.splitlines()
    if not lines or "<!-- aw-prompt:" not in lines[0]:
        return text
    first = lines[0]
    match = _re.match(
        r"^<!--\s*aw-prompt:\s*(.*?)(?:\s*\.\s*(This HTML comment.*?))?\s*-->$",
        first,
    )
    if not match:
        return text
    meta_part = match.group(1).strip()
    trailer = match.group(2)
    segs = [seg.strip() for seg in meta_part.split(" | ") if seg.strip()]
    for raw_key, raw_val in raw_fields.items():
        pkey = _PROMPT_KEYS.get(raw_key, raw_key)
        prefix = f"{pkey}:"
        if raw_val is None:
            segs = [s for s in segs if not s.startswith(prefix)]
            continue
        new_seg = f"{pkey}: {raw_val}"
        replaced = False
        new_segs: list[str] = []
        for seg in segs:
            if seg.startswith(prefix):
                if not replaced:
                    new_segs.append(new_seg)
                    replaced = True
            else:
                new_segs.append(seg)
        if not replaced:
            new_segs.append(new_seg)
        segs = new_segs
    joined = " | ".join(segs)
    if trailer:
        lines[0] = f"<!-- aw-prompt: {joined} . {trailer} -->"
    else:
        lines[0] = f"<!-- aw-prompt: {joined} -->"
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _apply_raw_fields(
    text: str,
    raw_fields: dict[str, Any] | None,
    *,
    record_type: str,
) -> str:
    if not raw_fields:
        return text
    if record_type == "research":
        return _apply_raw_yaml_fields(text, raw_fields)
    if record_type == "prompt":
        return _apply_raw_prompt_fields(text, raw_fields)
    out = text
    for raw_key, raw_val in raw_fields.items():
        label = _BULLET_LABELS.get(raw_key, raw_key)
        val_str = None if raw_val is None else str(raw_val)
        before = out
        out = _meta.set_legacy_bullet_line(out, label, val_str)
        if out == before and val_str is not None:
            pat = _re.compile(r"(?m)^-\s*" + _re.escape(label) + r":")
            if not pat.search(_meta.metadata_region(out)):
                out = _insert_unknown_bullet(out, label, val_str)
    return out


def _coerce_finding(
    item: _review_findings.Finding | dict[str, Any],
) -> _review_findings.Finding:
    if isinstance(item, _review_findings.Finding):
        finding = item
    elif isinstance(item, dict):
        finding = _review_findings.Finding(
            id=str(item["id"]),
            severity=str(item["severity"]),
            scope=str(item.get("scope", "general")),
            area=str(item.get("area", "general")),
            evidence=str(item.get("evidence", "observed")),
            finding=str(item.get("finding", "")),
            remediation_risk=str(item.get("remediation_risk", "low")),
            decision=str(item["decision"]),
            resolution=str(item.get("resolution", "")),
        )
    else:
        raise TypeError(f"finding must be Finding or dict, got {type(item).__name__}")
    if finding.severity not in _review_findings.SEVERITIES:
        raise ValueError(
            f"illegal finding severity {finding.severity!r}; "
            f"expected one of {_review_findings.SEVERITIES}"
        )
    if finding.decision not in _review_findings.DECISIONS:
        raise ValueError(
            f"illegal finding decision {finding.decision!r}; "
            f"expected one of {_review_findings.DECISIONS}"
        )
    return finding


def _coerce_decision(
    item: _review_findings.Decision | dict[str, Any],
) -> _review_findings.Decision:
    if isinstance(item, _review_findings.Decision):
        return item
    if isinstance(item, dict):
        return _review_findings.Decision(
            id=str(item["id"]),
            question=str(item.get("question", "")),
            chosen=str(item.get("chosen", "")),
            alternatives=str(item.get("alternatives", "none")),
            basis=str(item.get("basis", "evidence")),
            reversible=str(item.get("reversible", "yes")),
        )
    raise TypeError(f"decision must be Decision or dict, got {type(item).__name__}")


def _coerce_rounds(
    rounds: Sequence[_review_findings.Round | dict[str, Any]] | None,
) -> tuple[_review_findings.Round, ...]:
    if rounds is None:
        return (_review_findings.Round(number=1, findings=(), decisions=()),)
    coerced: list[_review_findings.Round] = []
    for idx, item in enumerate(rounds, start=1):
        if isinstance(item, _review_findings.Round):
            findings = tuple(_coerce_finding(f) for f in item.findings)
            decisions = tuple(_coerce_decision(d) for d in item.decisions)
            coerced.append(
                _review_findings.Round(
                    number=item.number,
                    findings=findings,
                    decisions=decisions,
                    line=item.line,
                )
            )
        elif isinstance(item, dict):
            num = int(item.get("number", idx))
            findings = tuple(_coerce_finding(f) for f in item.get("findings", ()))
            decisions = tuple(_coerce_decision(d) for d in item.get("decisions", ()))
            coerced.append(
                _review_findings.Round(
                    number=num,
                    findings=findings,
                    decisions=decisions,
                )
            )
        else:
            raise TypeError(f"round must be Round or dict, got {type(item).__name__}")
    return tuple(coerced)


class RecordBuilder:
    """Shared deterministic test fixture builder backed by ``artifact_meta``."""

    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root: Path | None = Path(repo_root) if repo_root is not None else None

    def _require_repo_root(self) -> Path:
        if self.repo_root is None:
            raise ValueError(
                "repo_root is required when writing files (text_only=False)"
            )
        return self.repo_root

    def _dest_path(
        self,
        plural: str,
        disposition: str | None,
        filename: str,
        *,
        ctx: Any = None,
    ) -> tuple[Path, str]:
        if ctx is not None:
            records_dir = Path(ctx.logical_roots["records"])
            if self.repo_root is not None:
                try:
                    rel_records = records_dir.relative_to(self.repo_root.resolve())
                except ValueError:
                    pass
                else:
                    records_dir = self.repo_root / rel_records
        else:
            records_dir = Path(".aw") / "records"
        if disposition:
            rel_path = f"{plural}/{disposition}/{filename}"
            dest = records_dir / plural / disposition / filename
        else:
            rel_path = f"{plural}/{filename}"
            dest = records_dir / plural / filename
        return dest, rel_path

    def _emit_record(
        self,
        *,
        id6: str,
        record_type: str,
        filename: str,
        disposition: str | None,
        fields: dict[str, Any],
        initial_text: str,
        render: _meta.LegacyRender,
        message: str | None = None,
        followup_event: tuple[dict[str, Any], _meta.LegacyRender] | None = None,
        post_process: Sequence[Any] | None = None,
        text_only: bool = False,
    ) -> Path | str:
        plural = _PLURAL_FOR_TYPE[record_type]
        if text_only:
            _, rel_path = self._dest_path(plural, disposition, filename)
            create_ev: dict[str, Any] = {
                "op": "create",
                "path": rel_path,
                "fields": {**fields, "id": id6, "type": record_type},
            }
            if message is not None:
                create_ev["message"] = message
            text = _meta.render_legacy_text(
                initial_text,
                [create_ev],
                record_type=record_type,
                render=render,
                repo_root=self.repo_root,
            )
            if followup_event is not None:
                ev2, render2 = followup_event
                text = _meta.render_legacy_text(
                    text,
                    [ev2],
                    record_type=record_type,
                    render=render2,
                    repo_root=self.repo_root,
                )
            for fn in post_process or ():
                text = fn(text)
            return text

        repo_root = self._require_repo_root()
        ctx = _meta.legacy_context(repo_root)
        dest, _ = self._dest_path(plural, disposition, filename, ctx=ctx)
        dest.parent.mkdir(parents=True, exist_ok=True)
        create_kwargs: dict[str, Any] = {
            "destination": dest,
            "dry_run": False,
            "project_context": ctx,
            "actor": _ACTOR,
            "legacy_render": render,
            "repo_root": repo_root,
        }
        if message is not None:
            create_kwargs["message"] = message
        preview = _meta.create(
            id6,
            record_type,
            fields,
            initial_text,
            **create_kwargs,
        )
        rendered = preview.text
        if followup_event is not None:
            ev2, render2 = followup_event
            append_preview = _meta.append(
                _meta.LegacyTarget(dest, record_type, id6=id6),
                [ev2],
                dry_run=False,
                project_context=ctx,
                actor=_ACTOR,
                legacy_render=render2,
                repo_root=repo_root,
            )
            rendered = append_preview.text
        final_text = rendered
        for fn in post_process or ():
            final_text = fn(final_text)
        if final_text != rendered:
            _core.atomic_write(dest, final_text)
        return dest

    def plan(
        self,
        *,
        id6: str | None = None,
        plan_id: str | None = None,
        kind: str | None = None,
        plan_role: str | None = None,
        title: str = "demo",
        author: str = "tester",
        when: str = DEFAULT_WHEN,
        set_name: str | None = None,
        set: str | None = None,
        order: int = 1,
        status: str = "draft",
        scope_paths: str = "agent_workflows/demo.py, tests/test_demo.py",
        item_dependencies: str = "none",
        priority: str | None = DEFAULT_PRIORITY,
        work_kind: str | None = DEFAULT_WORK_KIND,
        approval: str | None = None,
        readiness: str | None = None,
        disposition: str | None = None,
        slug: str | None = None,
        body: str | None = None,
        history: Sequence[str | dict[str, Any]] | None = None,
        open_questions: str | Sequence[str] | None = None,
        raw_fields: dict[str, Any] | None = None,
        text_only: bool = False,
        **extra_fields: Any,
    ) -> Path | str:
        """Build a legacy IPD fixture via ``ipd_authoring.build_skeleton`` + ``artifact_meta``."""
        _require_legacy_format()
        eff_id = _validate_id(
            _resolve_alias(
                id6, plan_id, primary_name="id6", alias_name="plan_id", default="abc123"
            )
            or "abc123"
        )
        ymd = _validate_day(when)
        eff_role = _resolve_alias(
            plan_role,
            kind,
            primary_name="plan_role",
            alias_name="kind",
            default="child",
        )
        eff_set = _resolve_alias(
            set, set_name, primary_name="set", alias_name="set_name", default="demo"
        )
        assert eff_role is not None and eff_set is not None
        _validate_status("ipd", status)
        eff_disp = _resolve_disposition("plans", "pending", disposition)

        check_fields: dict[str, Any] = {
            "status": status,
            "plan_role": eff_role,
            "title": title,
            "author": author,
            "set": eff_set,
            "order": order,
            "scope_paths": scope_paths,
            "item_dependencies": item_dependencies,
            "priority": priority or DEFAULT_PRIORITY,
            "work_kind": work_kind or DEFAULT_WORK_KIND,
            **extra_fields,
        }
        if approval is not None:
            check_fields["approval"] = approval
        if readiness is not None:
            check_fields["readiness"] = readiness
        _validate_fields("ipd", check_fields)

        skeleton = _authoring.build_skeleton(
            kind=eff_role,
            title=title,
            author=author,
            when=when,
            set_name=eff_set,
            order=order,
            plan_id=eff_id,
        )
        if readiness is not None and history is None:
            skeleton = skeleton.replace(
                "## Workflow history\n\n- ", "## Workflow history\n\n\n- ", 1
            )

        render_fields: dict[str, Any] = {
            "status": status,
            "scope_paths": scope_paths,
            "item_dependencies": item_dependencies,
            "priority": priority or DEFAULT_PRIORITY,
            "work_kind": work_kind or DEFAULT_WORK_KIND,
        }
        if readiness is not None:
            render_fields["readiness"] = readiness
        if approval is not None:
            render_fields["approval"] = approval
        for fk, fv in extra_fields.items():
            if fv is not None:
                render_fields[fk] = fv

        eff_slug = _core.kebab(slug or title or eff_set) or "plan"
        filename = _naming.build_clustered_name(
            date=ymd,
            set_id=eff_set,
            order=order,
            id6=eff_id,
            slug=eff_slug,
            artifact_type="ipd",
        )
        followup: tuple[dict[str, Any], _meta.LegacyRender] | None = None
        if readiness is not None and history is None:
            followup = (
                {
                    "op": "review",
                    "review_kind": "gate",
                    "verdict": "APPROVE",
                    "message": "APPROVE",
                },
                _meta.LegacyRender(
                    tag="/plan-review",
                    day=when,
                    actor_label=author,
                    history=True,
                ),
            )
        post_process = [
            lambda t: _apply_plan_body(t, body),
            lambda t: _apply_open_questions(t, open_questions),
            lambda t: _apply_history(
                t, history, default_day=when, default_actor=author
            ),
            lambda t: _apply_raw_fields(t, raw_fields, record_type="ipd"),
        ]
        return self._emit_record(
            id6=eff_id,
            record_type="ipd",
            filename=filename,
            disposition=eff_disp,
            fields=render_fields,
            initial_text=skeleton,
            render=_meta.LegacyRender(
                tag="draft", day=when, actor_label=author, history=False
            ),
            followup_event=followup,
            post_process=post_process,
            text_only=text_only,
        )

    def spec(
        self,
        *,
        id6: str = "sp1001",
        title: str = "demo",
        author: str = "aw specs new",
        when: str = DEFAULT_WHEN,
        set_name: str | None = None,
        set: str | None = None,
        order: int = 1,
        status: str = "draft",
        summary: str = "",
        disposition: str | None = None,
        slug: str | None = None,
        body: str | None = None,
        history: Sequence[str | dict[str, Any]] | None = None,
        raw_fields: dict[str, Any] | None = None,
        text_only: bool = False,
        **extra_fields: Any,
    ) -> Path | str:
        """Build a legacy spec fixture via ``artifact_meta``."""
        _require_legacy_format()
        eff_id = _validate_id(id6)
        ymd = _validate_day(when)
        eff_set = _resolve_alias(
            set, set_name, primary_name="set", alias_name="set_name", default=eff_id
        )
        assert eff_set is not None
        _validate_status("spec", status)
        eff_disp = _resolve_disposition("specs", status, disposition)

        check_fields: dict[str, Any] = {
            "status": status,
            "author": author,
            "title": title,
            "set": eff_set,
            "order": order,
            **extra_fields,
        }
        _validate_fields("spec", check_fields)

        render_fields: dict[str, Any] = {"status": status, "author": author}
        for fk, fv in extra_fields.items():
            if fv is not None:
                render_fields[fk] = fv

        body_prose = (
            body.strip("\n")
            if body is not None
            else (f"## Scope\n\n{summary}" if summary else "## Scope\n\nSpec scope.")
        )
        initial_text = (
            f"# Spec: {title}\n\n{body_prose}\n" if body_prose else f"# Spec: {title}\n"
        )
        eff_slug = _core.kebab(slug or title or eff_set) or "spec"
        filename = _naming.build_clustered_name(
            date=ymd,
            set_id=eff_set,
            order=order,
            id6=eff_id,
            slug=eff_slug,
            artifact_type="spec",
        )
        post_process = [
            lambda t: _apply_history(
                t, history, default_day=when, default_actor=author
            ),
            lambda t: _apply_raw_fields(t, raw_fields, record_type="spec"),
        ]
        return self._emit_record(
            id6=eff_id,
            record_type="spec",
            filename=filename,
            disposition=eff_disp,
            fields=render_fields,
            initial_text=initial_text,
            render=_meta.LegacyRender(
                tag="created", day=when, actor_label=author, history=True
            ),
            message="created.",
            post_process=post_process,
            text_only=text_only,
        )

    def backlog(
        self,
        *,
        id6: str = "bl1001",
        summary: str = "Demo backlog item",
        priority: str = DEFAULT_PRIORITY,
        work_kind: str = DEFAULT_WORK_KIND,
        status: str = "open",
        when: str = DEFAULT_WHEN,
        set_name: str | None = None,
        set: str | None = None,
        order: int = 1,
        author: str = "aw backlog",
        disposition: str | None = None,
        slug: str | None = None,
        body: str | None = None,
        history: Sequence[str | dict[str, Any]] | None = None,
        raw_fields: dict[str, Any] | None = None,
        text_only: bool = False,
        **extra_fields: Any,
    ) -> Path | str:
        """Build a legacy backlog fixture via ``artifact_meta``."""
        _require_legacy_format()
        eff_id = _validate_id(id6)
        ymd = _validate_day(when)
        eff_set = _resolve_alias(
            set, set_name, primary_name="set", alias_name="set_name", default=eff_id
        )
        assert eff_set is not None
        _validate_status("backlog", status)
        eff_disp = _resolve_disposition("backlog", status, disposition)

        render_fields: dict[str, Any] = {
            "status": status,
            "set": eff_set,
            "priority": priority,
            "work_kind": work_kind,
            "summary": summary,
        }
        for fk, fv in extra_fields.items():
            if fv is not None:
                render_fields[fk] = fv
        _validate_fields("backlog", render_fields)

        eff_slug = _core.kebab(slug or summary or eff_set) or "backlog"
        filename = _naming.build_clustered_name(
            date=ymd,
            set_id=eff_set,
            order=order,
            id6=eff_id,
            slug=eff_slug,
            artifact_type="backlog",
        )

        def _append_backlog_body(text: str) -> str:
            out = _apply_history(text, history, default_day=when, default_actor=author)
            if body is not None and body.strip():
                out = out.rstrip("\n") + "\n\n" + body.strip("\n") + "\n"
            return _apply_raw_fields(out, raw_fields, record_type="backlog")

        return self._emit_record(
            id6=eff_id,
            record_type="backlog",
            filename=filename,
            disposition=eff_disp,
            fields=render_fields,
            initial_text="",
            render=_meta.LegacyRender(
                tag="created", day=when, actor_label=author, history=True
            ),
            message=summary or "created.",
            post_process=[_append_backlog_body],
            text_only=text_only,
        )

    def research(
        self,
        *,
        id6: str = "rs1001",
        topic: str | Sequence[str] = "Demo research topic",
        research_kind: str | None = None,
        kind: str | None = None,
        status: str | None = "reference",
        outcome: str = "informational",
        when: str = DEFAULT_WHEN,
        set_name: str | None = None,
        set: str | None = None,
        order: int = 1,
        model: str = "",
        summary: str = "",
        consumed_by: Sequence[str] | None = None,
        disposition: str | None = None,
        slug: str | None = None,
        body: str | None = None,
        raw_fields: dict[str, Any] | None = None,
        text_only: bool = False,
        **extra_fields: Any,
    ) -> Path | str:
        """Build a legacy research YAML-frontmatter fixture via ``artifact_meta``."""
        _require_legacy_format()
        eff_id = _validate_id(id6)
        ymd = _validate_day(when)
        eff_kind = _resolve_alias(
            research_kind,
            kind,
            primary_name="research_kind",
            alias_name="kind",
            default="research-report",
        )
        eff_set = _resolve_alias(
            set, set_name, primary_name="set", alias_name="set_name", default="demo"
        )
        assert eff_kind is not None and eff_set is not None
        if eff_kind not in _research_contract.KINDS:
            raise ValueError(
                f"illegal research_kind {eff_kind!r}; "
                f"expected one of {sorted(_research_contract.KINDS)}"
            )
        _validate_status(
            "research",
            status,
            allow_none=(eff_kind == "research-prompt"),
        )
        if outcome not in _research_contract.OUTCOMES:
            raise ValueError(
                f"illegal outcome {outcome!r}; "
                f"expected one of {sorted(_research_contract.OUTCOMES)}"
            )
        eff_disp = _resolve_disposition("research", None, disposition)

        if isinstance(topic, str):
            topic_list = [topic.strip()] if topic.strip() else []
            topic_label = topic
        else:
            topic_list = [str(t).strip() for t in topic if str(t).strip()]
            topic_label = ", ".join(topic_list)

        render_fields: dict[str, Any] = {
            "created": ymd,
            "set": eff_set,
            "order": order,
            "topic": topic_list,
            "model": model,
            "research_kind": eff_kind,
            "outcome": outcome,
            "summary": summary,
            "consumed_by": list(consumed_by) if consumed_by is not None else [],
        }
        if status is not None:
            render_fields["status"] = status
        for fk, fv in extra_fields.items():
            if fv is not None:
                render_fields[fk] = fv
        _validate_fields("research", render_fields)

        eff_slug = _core.kebab(slug or topic_label or eff_set) or "research"
        filename = _research_contract.format_name(
            _research_contract.ResearchName(
                date=ymd,
                set_id=eff_set,
                order=f"{int(order):02d}",
                id6=eff_id,
                slug=eff_slug,
                model=model,
                kind=eff_kind,
            )
        )
        initial_text = (
            body
            if body is not None
            else f"# {topic_label or eff_set}\n\n## Findings\n\nResearch notes.\n"
        )
        return self._emit_record(
            id6=eff_id,
            record_type="research",
            filename=filename,
            disposition=eff_disp,
            fields=render_fields,
            initial_text=initial_text,
            render=_meta.LegacyRender(
                tag="created",
                day=when,
                actor_label="human:tester",
                status=status,
                history=False,
            ),
            post_process=[
                lambda t: _apply_raw_fields(t, raw_fields, record_type="research")
            ],
            text_only=text_only,
        )

    def release(
        self,
        *,
        id6: str = "rl1001",
        version: str = "1.0.0",
        status: str = "planned",
        summary: str = "Demo release summary",
        when: str = DEFAULT_WHEN,
        set_name: str | None = None,
        set: str | None = None,
        order: int = 1,
        author: str = "aw releases",
        disposition: str | None = None,
        slug: str | None = None,
        body: str | None = None,
        history: Sequence[str | dict[str, Any]] | None = None,
        raw_fields: dict[str, Any] | None = None,
        text_only: bool = False,
        **extra_fields: Any,
    ) -> Path | str:
        """Build a legacy release fixture via ``artifact_meta``."""
        _require_legacy_format()
        eff_id = _validate_id(id6)
        ymd = _validate_day(when)
        eff_set = _resolve_alias(
            set, set_name, primary_name="set", alias_name="set_name", default=eff_id
        )
        assert eff_set is not None
        _validate_status("release", status)
        eff_disp = _resolve_disposition("releases", None, disposition)

        render_fields: dict[str, Any] = {
            "status": status,
            "version": version,
        }
        if summary and summary.strip():
            render_fields["short_description"] = summary
        for fk, fv in extra_fields.items():
            if fv is not None:
                render_fields[fk] = fv
        _validate_fields("release", render_fields)

        eff_slug = _core.kebab(slug or version or eff_set) or "release"
        filename = _naming.build_clustered_name(
            date=ymd,
            set_id=eff_set,
            order=order,
            id6=eff_id,
            slug=eff_slug,
            artifact_type="release",
        )
        initial_text = (
            body
            if body is not None
            else f"# Release: {version}\n\n## Summary\n\n{summary}\n"
        )
        post_process = [
            lambda t: _apply_history(
                t, history, default_day=when, default_actor=author
            ),
            lambda t: _apply_raw_fields(t, raw_fields, record_type="release"),
        ]
        return self._emit_record(
            id6=eff_id,
            record_type="release",
            filename=filename,
            disposition=eff_disp,
            fields=render_fields,
            initial_text=initial_text,
            render=_meta.LegacyRender(
                tag="created", day=when, actor_label=author, history=True
            ),
            message=summary or "created.",
            post_process=post_process,
            text_only=text_only,
        )

    def prompt(
        self,
        *,
        id6: str = "pr1001",
        prompt_kind: str | None = None,
        kind: str | None = None,
        status: str = _prompts.DEFAULT_STATUS,
        short_description: str = "Demo staged prompt",
        when: str = DEFAULT_WHEN,
        set_name: str | None = None,
        set: str | None = None,
        order: int = 1,
        author: str | None = None,
        disposition: str | None = None,
        slug: str | None = None,
        body: str | None = None,
        raw_fields: dict[str, Any] | None = None,
        text_only: bool = False,
        **extra_fields: Any,
    ) -> Path | str:
        """Build a legacy staged prompt fixture via ``artifact_meta``."""
        _require_legacy_format()
        eff_id = _validate_id(id6)
        ymd = _validate_day(when)
        eff_kind = _resolve_alias(
            prompt_kind,
            kind,
            primary_name="prompt_kind",
            alias_name="kind",
            default="run-once",
        )
        eff_set = _resolve_alias(
            set, set_name, primary_name="set", alias_name="set_name", default=eff_id
        )
        assert eff_kind is not None and eff_set is not None
        if eff_kind not in _prompts.PROMPT_KINDS:
            raise ValueError(
                f"illegal prompt_kind {eff_kind!r}; "
                f"expected one of {_prompts.PROMPT_KINDS}"
            )
        _validate_status("prompt", status)
        eff_disp = _resolve_disposition("prompts", _prompts.PENDING_BUCKET, disposition)

        render_fields: dict[str, Any] = {
            "prompt_kind": eff_kind,
            "set": eff_set,
            "status": status,
            "created_day": when,
            "short_description": short_description,
        }
        if author is not None:
            render_fields["author"] = author
        for fk, fv in extra_fields.items():
            if fv is not None:
                render_fields[fk] = fv
        _validate_fields("prompt", render_fields)

        eff_slug = _core.kebab(slug or short_description or eff_set) or "prompt"
        filename = _naming.build_clustered_name(
            date=ymd,
            set_id=eff_set,
            order=order,
            id6=eff_id,
            slug=eff_slug,
            artifact_type="prompt",
        )
        initial_text = (
            body
            if body is not None
            else f"# Prompt: {short_description}\n\nPrompt body.\n"
        )
        return self._emit_record(
            id6=eff_id,
            record_type="prompt",
            filename=filename,
            disposition=eff_disp,
            fields=render_fields,
            initial_text=initial_text,
            render=_meta.LegacyRender(
                tag="created",
                day=when,
                actor_label=author or "aw prompts new",
                status=status,
                history=False,
                is_prompt=True,
            ),
            post_process=[
                lambda t: _apply_raw_fields(t, raw_fields, record_type="prompt")
            ],
            text_only=text_only,
        )

    def walkthrough(
        self,
        *,
        id6: str = "wt1001",
        target_id: str = "abc123",
        when: str = DEFAULT_WHEN,
        set_name: str | None = None,
        set: str | None = None,
        order: int = 1,
        disposition: str | None = None,
        slug: str | None = None,
        body: str | None = None,
        raw_fields: dict[str, Any] | None = None,
        text_only: bool = False,
        **extra_fields: Any,
    ) -> Path | str:
        """Build a legacy walkthrough fixture via ``artifact_meta``."""
        _require_legacy_format()
        eff_id = _validate_id(id6)
        _validate_id(target_id)
        ymd = _validate_day(when)
        eff_set = _resolve_alias(
            set, set_name, primary_name="set", alias_name="set_name", default="demo"
        )
        assert eff_set is not None
        eff_disp = _resolve_disposition("walkthroughs", None, disposition)

        render_fields: dict[str, Any] = {
            "set": eff_set,
            "order": int(order),
            "target_id": target_id,
        }
        for fk, fv in extra_fields.items():
            if fv is not None:
                render_fields[fk] = fv
        _validate_fields("walkthrough", render_fields)

        eff_slug = _core.kebab(slug or eff_set) or "walkthrough"
        filename = _naming.build_clustered_name(
            date=ymd,
            set_id=eff_set,
            order=order,
            id6=eff_id,
            slug=eff_slug,
            artifact_type="walkthrough",
        )
        initial_text = (
            body
            if body is not None
            else f"# Walkthrough: {eff_set}\n\n## Summary\n\nWalkthrough notes.\n"
        )
        return self._emit_record(
            id6=eff_id,
            record_type="walkthrough",
            filename=filename,
            disposition=eff_disp,
            fields=render_fields,
            initial_text=initial_text,
            render=_meta.LegacyRender(
                tag="created",
                day=when,
                actor_label="aw walkthrough",
                history=False,
            ),
            post_process=[
                lambda t: _apply_raw_fields(t, raw_fields, record_type="walkthrough")
            ],
            text_only=text_only,
        )

    def review(
        self,
        subject: str,
        *,
        rounds: Sequence[_review_findings.Round | dict[str, Any]] | None = None,
        subject_type: str = "ipd",
        when: str = DEFAULT_WHEN,
        reviewed_at: str | None = None,
        reviewer: str = "opencode/test-model",
        verdict: str = "APPROVE",
        set_name: str | None = None,
        set: str | None = None,
        order: int = 1,
        disposition: str | None = None,
        slug: str = "review",
        text_only: bool = False,
    ) -> Path | str:
        """Build a review findings fixture through ``review_findings``."""
        _require_legacy_format()
        eff_subject = _validate_id(subject)
        eff_day = reviewed_at if reviewed_at is not None else when
        ymd = _validate_day(eff_day)
        if subject_type not in _review_findings.SUBJECT_TYPES:
            raise ValueError(
                f"illegal subject_type {subject_type!r}; "
                f"expected one of {_review_findings.SUBJECT_TYPES}"
            )
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError("reviewer must be a non-empty string")
        if not isinstance(verdict, str) or not verdict.strip():
            raise ValueError("verdict must be a non-empty string")
        eff_disp = _resolve_disposition("reviews", None, disposition)
        eff_set = _resolve_alias(
            set,
            set_name,
            primary_name="set",
            alias_name="set_name",
            default=eff_subject,
        )
        assert eff_set is not None
        coerced_rounds = _coerce_rounds(rounds)

        if text_only:
            return _review_findings.render_review(
                subject_id=eff_subject,
                subject_type=subject_type,
                reviewed_at=eff_day,
                reviewer=reviewer,
                verdict=verdict,
                rounds=coerced_rounds,
            )

        repo_root = self._require_repo_root()
        ctx = _meta.legacy_context(repo_root)
        eff_slug = _core.kebab(slug or eff_subject) or "review"
        filename = _review_findings.build_review_name(
            date=ymd,
            set_id=eff_set,
            order=order,
            subject_id6=eff_subject,
            slug=eff_slug,
        )
        dest, _ = self._dest_path("reviews", eff_disp, filename, ctx=ctx)
        return _review_findings.write_review(
            dest,
            subject_id=eff_subject,
            subject_type=subject_type,
            reviewed_at=eff_day,
            reviewer=reviewer,
            verdict=verdict,
            rounds=coerced_rounds,
        )


_REVIEW_FIELDS: frozenset[str] = frozenset(
    ("subject_id", "subject_type", "reviewed_at", "reviewer", "verdict")
)

_SUFFIX_TO_RECORD_TYPE: tuple[tuple[str, str], ...] = (
    (".ipd.md", "ipd"),
    (".spec.md", "spec"),
    (".backlog.md", "backlog"),
    (".release.md", "release"),
    (".prompt.md", "prompt"),
    (".walkthrough.md", "walkthrough"),
    (".review.md", "review"),
    (".research-report.md", "research"),
    (".research-prompt.md", "research"),
    (".findings.md", "research"),
    (".survey.md", "research"),
    (".comparison.md", "research"),
)


def _infer_record_type(
    record_path: Path,
    text: str,
    record_type: str | None,
) -> str:
    if record_type is not None:
        if record_type in ("review", "reviews"):
            return "review"
        resolved, _ = _meta._normalize_legacy_types(
            record_type, target_path=record_path
        )
        return resolved or "ipd"

    name = record_path.name
    for suffix, rtype in _SUFFIX_TO_RECORD_TYPE:
        if name.endswith(suffix):
            return rtype

    for part in reversed(record_path.parts[:-1]):
        if part == "reviews":
            return "review"
        mapped = _meta._LEGACY_PLURAL_TO_TYPE.get(part)
        if mapped is not None:
            return mapped

    if text.startswith("<!--") and _meta.has_prompt_metadata_comment(text):
        return "prompt"
    if _meta._YAML_FENCE_OPEN_RE.match(text):
        return "research"
    return "ipd"


def _read_state_field(state: _meta.State, field: str) -> Any:
    if field in state.fields:
        return state.fields[field]
    if field == "status":
        return state.status
    if field == "id":
        return state.id6 or None
    if field == "set":
        return state.set_id
    if field == "order" and state.order_nn is not None:
        return str(state.order_nn)
    if field == "short_description":
        return state.short_description
    if state.type == "prompt":
        if field == "prompt_kind":
            return state.fields.get("plan_role")
        if field == "created_day":
            return state.fields.get("created")
    return None


def _bullet_label_for(field: str, record_type: str) -> str:
    if record_type == "review" and field in _REVIEW_FIELDS:
        return "-".join(part.capitalize() for part in field.split("_"))
    label = _BULLET_LABELS.get(field)
    if label is None:
        raise ValueError(f"unknown field {field!r} for record type {record_type!r}")
    return label


def _prompt_comment_segments(text: str) -> list[str]:
    first_line = text.replace("\r\n", "\n").split("\n", 1)[0]
    match = _re.match(
        r"^<!--\s*aw-prompt:\s*(.*?)(?:\s*\.\s*(This HTML comment.*?))?\s*-->$",
        first_line,
    )
    if not match:
        return []
    return [seg.strip() for seg in match.group(1).split(" | ") if seg.strip()]


def assert_field(
    path: Path | str,
    field: str,
    value: Any,
    *,
    record_type: str | None = None,
) -> None:
    """Assert that the record at ``path`` has ``field`` equal to ``value`` in the active format.

    In the legacy format (``RECORD_FORMAT == "legacy"``), reads the record through
    ``artifact_meta.read_text`` and also checks the exact on-disk metadata representation
    (bullet line ``- <Label>: <value>``, YAML ``<key>: <value>``, or prompt comment segment
    ``<Key>: <value>``), so tests are never weaker than direct substring assertions.
    """
    _require_legacy_format()
    record_path = Path(path)
    text = record_path.read_text(encoding="utf-8")
    resolved_type = _infer_record_type(record_path, text, record_type)
    state = _meta.read_text(text, record_type=resolved_type)
    observed = _read_state_field(state, field)

    region_lines = _meta.metadata_region(text).replace("\r\n", "\n").split("\n")

    if resolved_type == "research" and _meta._YAML_FENCE_OPEN_RE.match(text):
        yaml_key = _meta._RESEARCH_YAML_KEY.get(field)
        if yaml_key is None:
            raise ValueError(
                f"unknown field {field!r} for record type {resolved_type!r}"
            )
        expected_str = _meta._format_yaml_value(value, key=yaml_key)
        expected_line = f"{yaml_key}: {expected_str}"
        matching_lines = [
            ln for ln in region_lines if _re.match(rf"^{_re.escape(yaml_key)}:", ln)
        ]
        if observed is None or str(observed) != expected_str:
            raise AssertionError(
                f"{record_path}: field {field!r} mismatch: "
                f"expected {expected_str!r} (exact line {expected_line!r}), "
                f"observed {observed!r} (lines: {matching_lines!r})"
            )
        if expected_line not in region_lines or len(matching_lines) != 1:
            raise AssertionError(
                f"{record_path}: field {field!r} exact-line mismatch: "
                f"expected {expected_line!r} (value {expected_str!r}), "
                f"observed {observed!r} (lines: {matching_lines!r})"
            )
        return

    if resolved_type == "prompt" and _meta.has_prompt_metadata_comment(text):
        key_label = _meta._PROMPT_COMMENT_KEY.get(field)
        if key_label is None:
            raise ValueError(
                f"unknown field {field!r} for record type {resolved_type!r}"
            )
        expected_str = _meta._format_legacy_value(field, value)
        expected_seg = f"{key_label}: {expected_str}"
        segments = _prompt_comment_segments(text)
        matching_segs = [
            seg for seg in segments if _re.match(rf"^{_re.escape(key_label)}:", seg)
        ]
        if observed is None or str(observed) != expected_str:
            raise AssertionError(
                f"{record_path}: field {field!r} mismatch: "
                f"expected {expected_str!r} (exact segment {expected_seg!r}), "
                f"observed {observed!r} (segments: {matching_segs!r})"
            )
        if expected_seg not in segments or len(matching_segs) != 1:
            raise AssertionError(
                f"{record_path}: field {field!r} exact-segment mismatch: "
                f"expected {expected_seg!r} (value {expected_str!r}), "
                f"observed {observed!r} (segments: {matching_segs!r})"
            )
        return

    label = _bullet_label_for(field, resolved_type)
    expected_str = _meta._format_legacy_value(field, value)
    expected_line = f"- {label}: {expected_str}"
    matching_lines = [
        ln for ln in region_lines if _re.match(rf"^-\s*{_re.escape(label)}:", ln)
    ]
    if observed is None or str(observed) != expected_str:
        raise AssertionError(
            f"{record_path}: field {field!r} mismatch: "
            f"expected {expected_str!r} (exact line {expected_line!r}), "
            f"observed {observed!r} (lines: {matching_lines!r})"
        )
    if expected_line not in region_lines or len(matching_lines) != 1:
        raise AssertionError(
            f"{record_path}: field {field!r} exact-line mismatch: "
            f"expected {expected_line!r} (value {expected_str!r}), "
            f"observed {observed!r} (lines: {matching_lines!r})"
        )


def assert_no_field(
    path: Path | str,
    field: str,
    *,
    record_type: str | None = None,
) -> None:
    """Assert that ``field`` is absent or unset on the record at ``path`` in the active format."""
    _require_legacy_format()
    record_path = Path(path)
    text = record_path.read_text(encoding="utf-8")
    resolved_type = _infer_record_type(record_path, text, record_type)
    state = _meta.read_text(text, record_type=resolved_type)
    observed = _read_state_field(state, field)

    region_lines = _meta.metadata_region(text).replace("\r\n", "\n").split("\n")

    if resolved_type == "research" and _meta._YAML_FENCE_OPEN_RE.match(text):
        yaml_key = _meta._RESEARCH_YAML_KEY.get(field)
        if yaml_key is None:
            raise ValueError(
                f"unknown field {field!r} for record type {resolved_type!r}"
            )
        non_empty_lines = [
            ln
            for ln in region_lines
            if _re.match(rf"^{_re.escape(yaml_key)}:\s*\S", ln)
        ]
        if (observed is not None and str(observed) != "") or non_empty_lines:
            raise AssertionError(
                f"{record_path}: field {field!r} expected absent, "
                f"observed {observed!r} (lines: {non_empty_lines!r})"
            )
        return

    if resolved_type == "prompt" and _meta.has_prompt_metadata_comment(text):
        key_label = _meta._PROMPT_COMMENT_KEY.get(field)
        if key_label is None:
            raise ValueError(
                f"unknown field {field!r} for record type {resolved_type!r}"
            )
        segments = _prompt_comment_segments(text)
        matching_segs = [
            seg for seg in segments if _re.match(rf"^{_re.escape(key_label)}:", seg)
        ]
        bullet_label = _BULLET_LABELS.get(field)
        matching_bullets = [
            ln
            for ln in region_lines
            if bullet_label and _re.match(rf"^-\s*{_re.escape(bullet_label)}:", ln)
        ]
        if (
            (observed is not None and str(observed) != "")
            or matching_segs
            or matching_bullets
        ):
            raise AssertionError(
                f"{record_path}: field {field!r} expected absent, "
                f"observed {observed!r} "
                f"(segments: {matching_segs!r}, lines: {matching_bullets!r})"
            )
        return

    label = _bullet_label_for(field, resolved_type)
    matching_lines = [
        ln for ln in region_lines if _re.match(rf"^-\s*{_re.escape(label)}:", ln)
    ]
    if (observed is not None and str(observed) != "") or matching_lines:
        raise AssertionError(
            f"{record_path}: field {field!r} expected absent, "
            f"observed {observed!r} (lines: {matching_lines!r})"
        )
