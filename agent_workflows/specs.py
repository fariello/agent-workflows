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

import sys
from pathlib import Path
from typing import List, Optional, Tuple

from agent_workflows import artifact_core as core
from agent_workflows import attention_contract as A

SPECS_ROOT = ".agents/docs/specs"


# --------------------------------------------------------------------------------------
# Parsing helpers (front-matter bullets in the metadata block)
# --------------------------------------------------------------------------------------


def _lines(text: str) -> List[str]:
    return text.split("\n")


def _find_status_index(lines: List[str]) -> int:
    for i, line in enumerate(lines):
        if A.SPEC_STATUS_RE.match(line):
            return i
    return -1


def _read_status(lines: List[str]) -> Optional[str]:
    i = _find_status_index(lines)
    if i < 0:
        return None
    m = A.SPEC_STATUS_RE.match(lines[i])
    return m.group("value") if m else None


def _read_gate(lines: List[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    kind = ref = summary = None
    for line in lines:
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
    for i, line in enumerate(lines):
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


def _spec_files(repo_root: Path) -> List[Path]:
    root = repo_root / SPECS_ROOT
    if not root.is_dir():
        return []
    return sorted(p for p in root.glob("*.md") if p.name != "README.md")


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
    if auth.get("human_token"):
        if not _human_confirmed(args):
            sys.stderr.write(
                "aw specs set: reviewed -> approved requires interactive human confirmation "
                "(a bare flag is insufficient); refused.\n"
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
    out = _append_history(out, f"- {date} {new} (aw specs): {msg}")

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


def _human_confirmed(args) -> bool:
    """The anti-self-approval floor: require an INTERACTIVE human confirmation on a TTY. An executing
    agent (no TTY) cannot satisfy this. An explicit ``--yes-i-am-human`` is honored ONLY when stdin is
    a TTY, so it cannot be passed non-interactively by an agent harness."""

    if getattr(args, "yes_i_am_human", False) and sys.stdin.isatty():
        return True
    if not sys.stdin.isatty():
        return False
    try:
        reply = input(
            "Human approval required to set `approved`. Type 'approve' to confirm: "
        )
    except EOFError:
        return False
    return reply.strip().lower() == "approve"


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
