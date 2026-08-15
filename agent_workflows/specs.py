"""`aw specs` owner verbs for the specs tree (Set attnview, Order 02).

Owner-local writes for `.agents/docs/specs/`: `set` (status transition + typed gates + history),
`note` (history append only), and `check` (validate a spec, or all specs, against the frozen
contract). Consumes the Order 01 contracts in ``attention_contract`` and writes atomically via
``artifact_core.atomic_write``. NEVER stages, commits, or pushes git.

Stdlib-only, Python 3.9 (D46). The transition/authority enforcement (spec Section 7, F11) implements
the anti-self-approval floor: ``reviewed -> approved`` requires an interactive human confirmation
(a mechanism an executing agent cannot satisfy autonomously; a bare flag is insufficient), and
``implementing -> implemented`` requires a resolvable evidence citation (an existing
``.agents/plans/executed/`` IPD path), enforced as presence + format + resolvability, not semantic
verification.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from agent_workflows import artifact_core as core
from agent_workflows import attention_contract as A

SPECS_ROOT = ".aw/records/docs/specs"


# --------------------------------------------------------------------------------------
# Parsing helpers (front-matter bullets in the metadata block)
# --------------------------------------------------------------------------------------


def _lines(text: str) -> List[str]:
    return text.split("\n")


def _metadata_end(lines: List[str]) -> int:
    """The index of the first `## ` section heading (metadata block is everything before it). Gate and
    status bullets are only recognized in this block, so prose EXAMPLES of `- Gate-*`/`- Status:` inside
    a spec body (e.g. this Set's own spec Section 8.4) are not mistaken for real metadata."""

    for i, line in enumerate(lines):
        if line.startswith("## "):
            return i
    return len(lines)


def _find_status_index(lines: List[str]) -> int:
    end = _metadata_end(lines)
    for i in range(end):
        if A.SPEC_STATUS_RE.match(lines[i]):
            return i
    return -1


def _read_status(lines: List[str]) -> Optional[str]:
    i = _find_status_index(lines)
    if i < 0:
        return None
    m = A.SPEC_STATUS_RE.match(lines[i])
    return m.group(1) if m else None


# --------------------------------------------------------------------------------------
# CLI entrypoints
# --------------------------------------------------------------------------------------


def _spec_files(repo_root: Path) -> List[Path]:
    from agent_workflows.record_producers import resolve_record_read_paths

    try:
        roots = list(resolve_record_read_paths("specs", target_repo=str(repo_root)))
    except Exception:
        roots = [repo_root / ".aw" / "records" / "docs" / "specs"]
    # Always include the legacy `.agents/docs/specs` read path for bounded compatibility.
    # resolve_record_read_paths only appends the legacy dir once a migration retention
    # manifest exists; but an UN-migrated repo (the common case until the Order 11
    # self-migration runs) still keeps its specs under `.agents/docs/specs`, and
    # `aw specs check` must continue to see them. Adding it unconditionally is safe: the
    # loop below skips non-existent dirs and dedups.
    legacy = repo_root / ".agents" / "docs" / "specs"
    if legacy not in roots:
        roots.append(legacy)
    files: List[Path] = []
    for r in roots:
        if r.is_dir():
            files.extend(p for p in r.glob("*.md") if p.name != "README.md")
    return sorted(set(files))


def _read_gate(lines: List[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    kind = ref = summary = None
    end = _metadata_end(lines)
    for line in lines[:end]:
        mk = A.GATE_KIND_RE.match(line)
        if mk:
            kind = mk.group("value")
        mr = A.GATE_REF_RE.match(line)
        if mr:
            ref = mr.group("value")
        ms = A.GATE_SUMMARY_RE.match(line)
        if ms:
            summary = ms.group("value")
    return kind, ref, summary


def _history_lines(lines: List[str]) -> List[str]:
    out: List[str] = []
    in_hist = False
    for line in lines:
        if line.strip() == "## Workflow history":
            in_hist = True
            continue
        if in_hist:
            if line.startswith("## "):
                break
            out.append(line)
    return out


# --------------------------------------------------------------------------------------
# Validation (the `check` core; reused by the attention scanner for the specs tree)
# --------------------------------------------------------------------------------------


def validate_spec(path: Path, text: str) -> List[core.Drift]:
    """Return every spec-contract violation for one spec file, as Drift records (rule ids from the
    Order 01 catalog). Pure; does not read anything but the passed text."""

    loc = str(path)
    drift: List[core.Drift] = []
    lines = _lines(text)

    status = _read_status(lines)
    if status is None:
        drift.append(
            core.Drift(
                loc, "attention.missing-status", "no bare-enum `- Status:` bullet"
            )
        )
        # cannot validate further status-dependent rules
    elif status not in A.SPEC_STATUSES:
        drift.append(
            core.Drift(
                loc,
                "attention.unknown-status",
                A.escape_detail(f"status {status!r} not in the spec enum"),
            )
        )

    kind, ref, summary = _read_gate(lines)
    has_gate = kind is not None or ref is not None or summary is not None
    if status == "deferred":
        if kind is None or ref is None:
            drift.append(
                core.Drift(
                    loc,
                    "attention.gate-missing",
                    "deferred spec lacks Gate-Kind/Gate-Ref",
                )
            )
        else:
            if kind not in A.GATE_KINDS:
                drift.append(
                    core.Drift(
                        loc,
                        "attention.gate-malformed",
                        A.escape_detail(f"unknown Gate-Kind {kind!r}"),
                    )
                )
            elif not A.validate_gate_ref(kind, ref):
                drift.append(
                    core.Drift(
                        loc,
                        "attention.gate-malformed",
                        A.escape_detail(f"invalid Gate-Ref for {kind}: {ref!r}"),
                    )
                )
        if summary is not None and not A.is_safe_descriptive(summary):
            drift.append(
                core.Drift(
                    loc,
                    "attention.unsafe-field",
                    "Gate-Summary is over-length or has control chars/newlines",
                )
            )
    elif has_gate:
        drift.append(
            core.Drift(
                loc,
                "attention.gate-forbidden",
                "gate fields present on a non-deferred spec",
            )
        )

    hist = _history_lines(lines)
    if not any(A.HISTORY_RECORD_RE.match(h) for h in hist):
        drift.append(
            core.Drift(
                loc,
                "attention.history-missing",
                "no conformant `## Workflow history` record",
            )
        )

    return drift


# --------------------------------------------------------------------------------------
# Mutating helpers (atomic single-file writes; no git)
# --------------------------------------------------------------------------------------


def _today() -> str:
    # Deterministic authored-date source: the plans/history convention is a YYYY-MM-DD date. We read it
    # from the caller via --date when provided (tests), else the system date.
    import datetime

    return datetime.date.today().isoformat()


def _append_history(lines: List[str], record: str) -> List[str]:
    out = list(lines)
    # find the history section; append after its last record (before the next H2 or EOF)
    for i, line in enumerate(out):
        if line.strip() == "## Workflow history":
            j = i + 1
            end = len(out)
            while j < len(out):
                if out[j].startswith("## "):
                    end = j
                    break
                j += 1
            # insert before trailing blank lines within the section
            insert_at = end
            while insert_at - 1 > i and out[insert_at - 1].strip() == "":
                insert_at -= 1
            out.insert(insert_at, record)
            return out
    # no history section: create one at EOF
    if out and out[-1].strip() != "":
        out.append("")
    out.append("## Workflow history")
    out.append(record)
    return out


def _set_status(lines: List[str], new_status: str) -> List[str]:
    out = list(lines)
    i = _find_status_index(out)
    if i >= 0:
        out[i] = f"- Status: {new_status}"
    return out


def _gate_field_indices(lines: List[str]) -> List[int]:
    idx = []
    end = _metadata_end(lines)
    for i in range(end):
        line = lines[i]
        if (
            A.GATE_KIND_RE.match(line)
            or A.GATE_REF_RE.match(line)
            or A.GATE_SUMMARY_RE.match(line)
        ):
            idx.append(i)
    return idx


def _remove_gate_fields(lines: List[str]) -> List[str]:
    drop = set(_gate_field_indices(lines))
    return [line for i, line in enumerate(lines) if i not in drop]


def _add_gate_fields(
    lines: List[str], kind: str, ref: str, summary: Optional[str]
) -> List[str]:
    out = list(lines)
    i = _find_status_index(out)
    insert = [f"- Gate-Kind: {kind}", f"- Gate-Ref: {ref}"]
    if summary:
        insert.append(f"- Gate-Summary: {summary}")
    if i >= 0:
        for k, line in enumerate(insert):
            out.insert(i + 1 + k, line)
    return out


# --------------------------------------------------------------------------------------
# CLI entrypoints
# --------------------------------------------------------------------------------------


def run_check(args) -> int:
    repo_root = Path(getattr(args, "dir", ".") or ".")
    target = getattr(args, "path", None)
    if target:
        paths = [Path(target)]
    else:
        paths = _spec_files(repo_root)
    drift: List[core.Drift] = []
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            drift.append(
                core.Drift(str(p), "attention.unreadable", "cannot read/decode spec")
            )
            continue
        drift.extend(validate_spec(p, text))
    if getattr(args, "agent", False):
        sys.stdout.write(core.render_agent_drift(drift))
    else:
        if drift:
            for d in drift:
                sys.stdout.write(f"{d.location}: {d.rule}: {d.detail}\n")
            sys.stdout.write(
                "Move pipeline metadata/status into a bare-enum `- Status:` bullet and a conformant history; see the specs contract.\n"
            )
        else:
            sys.stdout.write("aw specs check: all specs conform.\n")
    return core.drift_exit_code(drift)


def run_set(args) -> int:
    path = Path(args.path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        sys.stderr.write(f"aw specs set: cannot read {path}: {exc}\n")
        return 2
    lines = _lines(text)
    old = _read_status(lines)
    new = args.status
    if new not in A.SPEC_STATUSES:
        sys.stderr.write(
            f"aw specs set: {new!r} is not a spec status {sorted(A.SPEC_STATUSES)}\n"
        )
        return 1
    if old is None:
        # allow initializing a status on a spec that lacks one only to a non-authority-gated state
        sys.stderr.write(
            "aw specs set: spec has no `- Status:` bullet to transition; add one via migration first\n"
        )
        return 1
    if old != new and not A.transition_allowed(old, new):
        sys.stderr.write(f"aw specs set: illegal transition {old} -> {new}\n")
        return 1

    # authority floor
    auth = A.TRANSITION_AUTHORITY.get(f"->{new}", {})
    if auth.get("by_human") or auth.get("human_token"):
        if not getattr(args, "by_human", False):
            sys.stderr.write(
                f"aw specs set: {old} -> {new} is a human-only transition; pass --by-human to attest "
                "(and record) that a human approved it. Use --message to say who/how.\n"
            )
            return 1
    if auth.get("evidence"):
        ev = getattr(args, "evidence", None)
        if not ev or not _evidence_resolvable(path, ev):
            sys.stderr.write(
                "aw specs set: implementing -> implemented requires a resolvable --evidence citation "
                "(an existing .agents/plans/executed/ IPD path); refused.\n"
            )
            return 1

    # gate handling
    out = lines
    if new == "deferred":
        gk = getattr(args, "gate_kind", None)
        gr = getattr(args, "gate_ref", None)
        gs = getattr(args, "gate_summary", None)
        if (
            not gk
            or not gr
            or gk not in A.GATE_KINDS
            or not A.validate_gate_ref(gk, gr)
        ):
            sys.stderr.write(
                "aw specs set: deferred requires a valid --gate-kind and --gate-ref\n"
            )
            return 1
        if gs is not None and not A.is_safe_descriptive(gs):
            sys.stderr.write(
                "aw specs set: --gate-summary must be a bounded single control-char-free line\n"
            )
            return 1
        out = _remove_gate_fields(out)
        out = _add_gate_fields(out, gk, gr, gs)
    else:
        out = _remove_gate_fields(out)  # gate fields forbidden on a non-deferred status

    out = _set_status(out, new)
    date = getattr(args, "date", None) or _today()
    msg = args.message
    actor = (
        "(aw specs, --by-human)" if getattr(args, "by_human", False) else "(aw specs)"
    )
    out = _append_history(out, f"- {date} {new} {actor}: {msg}")

    new_text = "\n".join(out)
    # validate the complete result in memory; refuse (byte-identical) if it would not conform
    residual = validate_spec(path, new_text)
    if residual:
        sys.stderr.write(
            "aw specs set: the resulting spec would not conform; refused (file unchanged):\n"
        )
        for d in residual:
            sys.stderr.write(f"  {d.rule}: {d.detail}\n")
        return 1
    core.atomic_write(path, new_text)
    sys.stdout.write(f"aw specs set: {path} -> {new}\n")
    return 0


def run_migrate(args) -> int:
    """One-time first-normalization of a legacy/free-form spec status to the bare enum.

    Unlike ``set``, this does NOT apply the enum-transition graph or the human-token/evidence floor:
    it is an explicit, human-directed migration of the EXISTING corpus (Order 04), not an ongoing
    lifecycle transition. It replaces the current ``Status`` line (a ``- Status:`` bullet OR a bare
    ``Status:`` body line) with a bare-enum ``- Status:`` bullet in the metadata block, folds any
    trailing status prose into a migration history record, optionally adds ``- Canonical: true``,
    optionally sets typed gate fields (required for ``deferred``), removes a free-form ``- Implemented:``
    line (folded to history), then validates the result and refuses (byte-identical) if it would not
    conform. Writes atomically; never touches git.
    """

    path = Path(args.path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        sys.stderr.write(f"aw specs migrate: cannot read {path}: {exc}\n")
        return 2
    new = args.status
    if new not in A.SPEC_STATUSES:
        sys.stderr.write(
            f"aw specs migrate: {new!r} is not a spec status {sorted(A.SPEC_STATUSES)}\n"
        )
        return 1
    lines = _lines(text)

    # capture the old status prose (from a `- Status:` bullet or a bare `Status:` body line) for history
    old_prose = None
    status_bullet_idx = _find_status_index(lines)
    bare_status_idx = -1
    if status_bullet_idx >= 0:
        old_prose = lines[status_bullet_idx][len("- Status:") :].strip()
    else:
        for i, line in enumerate(lines):
            if line.startswith("Status:"):
                bare_status_idx = i
                old_prose = line[len("Status:") :].strip()
                break
            m = re.match(r"^- Status:\s*(.*)$", line)
            if m:
                status_bullet_idx = i
                old_prose = m.group(1).strip()
                break

    out: List[str] = []
    implemented_prose = None
    inserted_status = False
    for i, line in enumerate(lines):
        if i == status_bullet_idx:
            out.append(f"- Status: {new}")
            inserted_status = True
            if getattr(args, "canonical", False):
                out.append("- Canonical: true")
            if new == "deferred":
                gk, gr, gs = (
                    args.gate_kind,
                    args.gate_ref,
                    getattr(args, "gate_summary", None),
                )
                out.append(f"- Gate-Kind: {gk}")
                out.append(f"- Gate-Ref: {gr}")
                if gs:
                    out.append(f"- Gate-Summary: {gs}")
            continue
        if i == bare_status_idx:
            # a bare `Status:` body line -> drop it; a proper metadata bullet is created below
            continue
        if line.startswith("- Implemented:"):
            implemented_prose = line[len("- Implemented:") :].strip()
            continue
        out.append(line)

    if not inserted_status:
        # no status bullet existed (only a bare body line, or none): insert into the metadata block
        # after the last metadata bullet (before the first `## ` heading), else right after the H1.
        meta_end = _metadata_end(out)
        insert_at = 0
        for i in range(meta_end):
            if out[i].startswith("# "):  # H1 title
                insert_at = i + 1
            if out[i].startswith("- "):  # a metadata bullet
                insert_at = i + 1
        add = [f"- Status: {new}"]
        if getattr(args, "canonical", False):
            add.append("- Canonical: true")
        if new == "deferred":
            add.append(f"- Gate-Kind: {args.gate_kind}")
            add.append(f"- Gate-Ref: {args.gate_ref}")
            if getattr(args, "gate_summary", None):
                add.append(f"- Gate-Summary: {args.gate_summary}")
        for k, a in enumerate(add):
            out.insert(insert_at + k, a)

    if new == "deferred":
        if (
            not args.gate_kind
            or not args.gate_ref
            or args.gate_kind not in A.GATE_KINDS
            or not A.validate_gate_ref(args.gate_kind, args.gate_ref)
        ):
            sys.stderr.write(
                "aw specs migrate: deferred requires a valid --gate-kind and --gate-ref\n"
            )
            return 1

    date = getattr(args, "date", None) or _today()
    hist = f"- {date} migrated (aw specs): normalized status to `{new}`"
    if old_prose:
        hist += f" (was: {A.escape_detail(old_prose)[:160]})"
    if implemented_prose:
        hist += f"; folded Implemented line: {A.escape_detail(implemented_prose)[:160]}"
    out = _append_history(out, hist)

    new_text = "\n".join(out)
    residual = validate_spec(path, new_text)
    if residual:
        sys.stderr.write(
            "aw specs migrate: the resulting spec would not conform; refused (file unchanged):\n"
        )
        for d in residual:
            sys.stderr.write(f"  {d.rule}: {d.detail}\n")
        return 1
    core.atomic_write(path, new_text)
    sys.stdout.write(f"aw specs migrate: {path} -> {new}\n")
    return 0


def run_note(args) -> int:
    path = Path(args.path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        sys.stderr.write(f"aw specs note: cannot read {path}: {exc}\n")
        return 2
    lines = _lines(text)
    date = getattr(args, "date", None) or _today()
    out = _append_history(lines, f"- {date} note (aw specs): {args.message}")
    core.atomic_write(path, "\n".join(out))
    sys.stdout.write(f"aw specs note: appended a history record to {path}\n")
    return 0


def _evidence_resolvable(spec_path: Path, evidence: str) -> bool:
    """`implemented` evidence must be a resolvable citation: an existing executed-IPD path."""

    if not A.is_safe_descriptive(evidence):
        return False
    # resolve relative to the repo root (two levels up from .agents/docs/specs/<file>)
    repo_root = (
        spec_path.resolve().parents[3]
        if len(spec_path.resolve().parents) >= 4
        else Path(".")
    )
    candidate = (repo_root / evidence).resolve()
    return candidate.exists() and ".agents/plans/executed" in str(candidate).replace(
        "\\", "/"
    )
