"""Read and write orchestrator coverage records in plan files (spec 25kzda Section 2.5e).

The coverage record is stored IN THE PLAN ITSELF (not in a machine-local cache):
- Metadata fields:
  - `- Coverage: pass` or `- Coverage: fail`
  - `- Coverage-Fingerprint: <hex>`
  - `- Coverage-Checked: <YYYY-MM-DD> by <model>`
- On a fail:
  - `## Coverage findings` section listing each quoted passage, one bullet per `QUOTE:` line
- Workflow history line:
  - `- <date> coverage <pass|fail> (<tool>): fingerprint <first 12 hex>, model <model>`

All first-party imports are function-local.
"""

from __future__ import annotations

import datetime
from pathlib import Path
import re
import subprocess
from typing import NamedTuple, Sequence

COVERAGE_PASS = "pass"
COVERAGE_FAIL = "fail"
COVERAGE_ABSENT = "absent"

_COVERAGE_LINE_RE = re.compile(r"^-\s*Coverage:\s*(\S+)\s*$", re.MULTILINE)
_FINGERPRINT_LINE_RE = re.compile(
    r"^-\s*Coverage-Fingerprint:\s*(\S+)\s*$", re.MULTILINE
)
_CHECKED_LINE_RE = re.compile(
    r"^-\s*Coverage-Checked:\s*(\S+)(?:\s+by\s+(.*))?$", re.MULTILINE
)
_STATUS_LINE_RE = re.compile(r"^-\s*Status:\s*(\S+)\s*$", re.MULTILINE)
_READINESS_LINE_RE = re.compile(r"^-\s*Readiness:\s*(.*)$", re.MULTILINE)
_ID_LINE_RE = re.compile(r"^-\s*Id:\s*([0-9a-z]{6})\b", re.MULTILINE)
_HISTORY_HDR_RE = re.compile(r"^##\s*Workflow history\s*$", re.MULTILINE)
_VALIDATION_HDR_RE = re.compile(r"^##\s*Validation and cross-check\b.*$", re.MULTILINE)
_FINDINGS_HDR_RE = re.compile(r"^##\s*Coverage findings\s*$", re.MULTILINE)


class CoverageRecord(NamedTuple):
    """The coverage record parsed from an IPD document."""

    verdict: str
    fingerprint: str = ""
    date: str = ""
    model: str = ""
    quotes: tuple[str, ...] = ()


class CoverageWriteResult(NamedTuple):
    """Result of attempting to write (and optionally commit) a coverage record."""

    written: bool
    committed: bool
    detail: str = ""


def read(plan_text: str) -> CoverageRecord:
    """Read the coverage record from `plan_text`.

    Returns a :class:`CoverageRecord` with verdict `pass`, `fail`, or `absent`.
    On `fail`, parses quotes from the `## Coverage findings` section if present.
    """
    cov_match = _COVERAGE_LINE_RE.search(plan_text)
    if not cov_match:
        return CoverageRecord(verdict=COVERAGE_ABSENT)

    verdict = cov_match.group(1).strip()
    if verdict not in (COVERAGE_PASS, COVERAGE_FAIL):
        return CoverageRecord(verdict=COVERAGE_ABSENT)

    fp_match = _FINGERPRINT_LINE_RE.search(plan_text)
    fingerprint = fp_match.group(1).strip() if fp_match else ""

    chk_match = _CHECKED_LINE_RE.search(plan_text)
    date = chk_match.group(1).strip() if chk_match else ""
    raw_model = (chk_match.group(2) or "").strip() if chk_match else ""
    if not raw_model or raw_model == "host-default":
        model = "by host-default"
    else:
        model = raw_model

    quotes: list[str] = []
    if verdict == COVERAGE_FAIL:
        f_match = _FINDINGS_HDR_RE.search(plan_text)
        if f_match:
            start_pos = f_match.end()
            # find next H2 or EOF
            rest = plan_text[start_pos:]
            next_h2 = re.search(r"^##\s+", rest, re.MULTILINE)
            section_text = rest[: next_h2.start()] if next_h2 else rest
            for line in section_text.splitlines():
                stripped = line.strip()
                if stripped.startswith("- ") or stripped.startswith("* "):
                    bullet = stripped[2:].strip()
                    if (
                        bullet.startswith('"')
                        and bullet.endswith('"')
                        and len(bullet) >= 2
                    ):
                        bullet = bullet[1:-1]
                    quotes.append(bullet)

    return CoverageRecord(
        verdict=verdict,
        fingerprint=fingerprint,
        date=date,
        model=model,
        quotes=tuple(quotes),
    )


def is_current(plan_text: str) -> bool:
    """Return True iff `plan_text` contains a current coverage record matching its fingerprint."""
    rec = read(plan_text)
    if rec.verdict not in (COVERAGE_PASS, COVERAGE_FAIL) or not rec.fingerprint:
        return False
    from agent_workflows.runner_shared import probe_cache_digest

    return rec.fingerprint == probe_cache_digest(plan_text)


def write(
    plan_path: Path | str,
    verdict: str,
    quotes: Sequence[str] = (),
    model: str = "",
    tool: str = "",
    *,
    commit: bool = False,
    host: str | None = None,
    repo: Path | str | None = None,
) -> CoverageWriteResult:
    """Write the coverage record into `plan_path`.

    Sets `- Coverage:`, `- Coverage-Fingerprint:`, `- Coverage-Checked:` metadata fields,
    replaces or removes `## Coverage findings`, and appends the workflow history line.
    All first-party imports function-local.

    When `commit=True`, checks if `git status --porcelain -- <plan>` shows uncommitted changes
    BEFORE writing; if so, returns without writing or committing. Otherwise makes one
    path-scoped commit of the plan file. A failed commit restores staged index and never raises.
    """
    path = Path(plan_path)
    if not path.is_file():
        return CoverageWriteResult(
            written=False, committed=False, detail=f"plan file not found: {path}"
        )

    plan_text = path.read_text(encoding="utf-8")

    from agent_workflows.runner_shared import probe_cache_digest

    fingerprint = probe_cache_digest(plan_text)
    today = datetime.date.today().isoformat()

    raw_model = (model or "").strip()
    if not raw_model or raw_model in ("host-default", "by host-default"):
        checked_model = "by host-default"
        hist_model = "by host-default"
    else:
        clean = raw_model.removeprefix("by ").strip()
        checked_model = f"by {clean}"
        hist_model = clean

    tool_str = (tool or "").strip() or "aw oc run"
    resolved_host = host if host is not None else ("agy" if "agy" in tool_str else "oc")

    # 1. Dirty-plan check before writing if commit=True
    resolved_repo = (
        Path(repo)
        if repo is not None
        else (path.parent if (path.parent / ".git").is_dir() else Path.cwd())
    )
    rel_path = (
        str(path.relative_to(resolved_repo))
        if path.is_relative_to(resolved_repo)
        else str(path)
    )

    if commit:
        st_proc = subprocess.run(
            ["git", "status", "--porcelain", "--", rel_path],
            cwd=str(resolved_repo),
            capture_output=True,
            text=True,
            check=False,
        )
        if st_proc.returncode == 0 and st_proc.stdout.strip():
            return CoverageWriteResult(
                written=False,
                committed=False,
                detail=f"plan file {rel_path} already has uncommitted changes; record not written",
            )

    # 2. Update metadata fields:
    # Remove existing Coverage fields if present
    lines = plan_text.splitlines()
    filtered_lines: list[str] = []
    first_cov_idx: int | None = None
    for idx, line in enumerate(lines):
        if _COVERAGE_LINE_RE.match(line):
            if first_cov_idx is None:
                first_cov_idx = len(filtered_lines)
            continue
        if _FINGERPRINT_LINE_RE.match(line) or _CHECKED_LINE_RE.match(line):
            continue
        filtered_lines.append(line)

    cov_block = [
        f"- Coverage: {verdict}",
        f"- Coverage-Fingerprint: {fingerprint}",
        f"- Coverage-Checked: {today} {checked_model}",
    ]

    if first_cov_idx is not None:
        # Replaced in place
        insert_idx = first_cov_idx
    else:
        # Inserted after - Status: and any - Readiness:
        status_idx = None
        readiness_idx = None
        for idx, line in enumerate(filtered_lines):
            if _STATUS_LINE_RE.match(line):
                status_idx = idx
            elif (
                status_idx is not None
                and readiness_idx is None
                and _READINESS_LINE_RE.match(line)
            ):
                readiness_idx = idx
            elif line.startswith("## "):
                break
        if readiness_idx is not None:
            insert_idx = readiness_idx + 1
        elif status_idx is not None:
            insert_idx = status_idx + 1
        else:
            # Fallback: after first heading or at top
            insert_idx = 1 if len(filtered_lines) > 1 else 0

    for offset, new_line in enumerate(cov_block):
        filtered_lines.insert(insert_idx + offset, new_line)

    intermediate_text = "\n".join(filtered_lines)
    if plan_text.endswith("\n"):
        intermediate_text += "\n"

    # 3. Handle ## Coverage findings section:
    # Remove any existing ## Coverage findings section
    f_match = _FINDINGS_HDR_RE.search(intermediate_text)
    if f_match:
        start_pos = f_match.start()
        rest = intermediate_text[f_match.end() :]
        next_h2 = re.search(r"^##\s+", rest, re.MULTILINE)
        end_pos = (
            (f_match.end() + next_h2.start()) if next_h2 else len(intermediate_text)
        )
        intermediate_text = (
            intermediate_text[:start_pos].rstrip()
            + "\n\n"
            + intermediate_text[end_pos:].lstrip()
        )

    if verdict == COVERAGE_FAIL:
        findings_block = ["## Coverage findings", ""]
        for q in quotes:
            findings_block.append(f'- "{q}"')
        findings_str = "\n".join(findings_block) + "\n\n"

        v_match = _VALIDATION_HDR_RE.search(intermediate_text)
        if v_match:
            insert_pos = v_match.start()
            intermediate_text = (
                intermediate_text[:insert_pos].rstrip()
                + "\n\n"
                + findings_str
                + intermediate_text[insert_pos:]
            )
        else:
            # Append before end
            intermediate_text = intermediate_text.rstrip() + "\n\n" + findings_str

    # 4. Append history line to ## Workflow history
    hist_entry = f"- {today} coverage {verdict} ({tool_str}): fingerprint {fingerprint[:12]}, model {hist_model}"
    h_match = _HISTORY_HDR_RE.search(intermediate_text)
    if h_match:
        hdr_end = h_match.end()
        # insert directly below ## Workflow history
        intermediate_text = (
            intermediate_text[:hdr_end]
            + "\n"
            + hist_entry
            + intermediate_text[hdr_end:]
        )
    else:
        # No workflow history heading; add one after metadata
        intermediate_text = (
            intermediate_text.rstrip() + f"\n\n## Workflow history\n{hist_entry}\n"
        )

    # Clean up excess blank lines and write
    final_text = intermediate_text.rstrip() + "\n"
    path.write_text(final_text, encoding="utf-8")

    if not commit:
        return CoverageWriteResult(written=True, committed=False, detail="")

    # 5. Git add and commit
    add_proc = subprocess.run(
        ["git", "add", "--", rel_path],
        cwd=str(resolved_repo),
        capture_output=True,
        text=True,
        check=False,
    )
    if add_proc.returncode != 0:
        return CoverageWriteResult(
            written=True,
            committed=False,
            detail=f"git add failed: {add_proc.stderr.strip()}",
        )

    # Derive id6 from plan text or filename
    id6_match = _ID_LINE_RE.search(final_text)
    if id6_match:
        id6 = id6_match.group(1).strip()
    else:
        # Fallback to id6 in path filename
        fname_match = re.search(r"\b([0-9a-z]{6})\b", path.name)
        id6 = fname_match.group(1) if fname_match else path.stem

    commit_msg = f"coverage({resolved_host}): record the coverage answer for {id6}"
    commit_proc = subprocess.run(
        ["git", "commit", "-m", commit_msg, "--", rel_path],
        cwd=str(resolved_repo),
        capture_output=True,
        text=True,
        check=False,
    )
    if commit_proc.returncode != 0:
        subprocess.run(
            ["git", "restore", "--staged", "--", rel_path],
            cwd=str(resolved_repo),
            capture_output=True,
            text=True,
            check=False,
        )
        return CoverageWriteResult(
            written=True,
            committed=False,
            detail=f"git commit failed: {commit_proc.stderr.strip()}",
        )

    return CoverageWriteResult(written=True, committed=True, detail="")
