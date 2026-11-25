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

from pathlib import Path
import os
import re
import subprocess
import tempfile
from typing import NamedTuple, Sequence

COVERAGE_PASS = "pass"
COVERAGE_FAIL = "fail"
COVERAGE_ABSENT = "absent"

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
    from agent_workflows import artifact_meta as _meta

    state = _meta.read_text(_meta.metadata_region(plan_text), record_type="ipd")
    verdict = str(state.fields.get("coverage") or "").strip()
    if verdict not in (COVERAGE_PASS, COVERAGE_FAIL):
        return CoverageRecord(verdict=COVERAGE_ABSENT)

    raw_fp = str(state.fields.get("coverage_fingerprint") or "").strip()
    fingerprint = raw_fp if (raw_fp and len(raw_fp.split()) == 1) else ""

    raw_checked = str(state.fields.get("coverage_checked") or "").strip()
    if " by " in raw_checked:
        date_part, model_part = raw_checked.split(" by ", 1)
        date = date_part.strip()
        raw_model = model_part.strip()
    elif raw_checked.endswith(" by"):
        date = raw_checked[:-3].strip()
        raw_model = ""
    else:
        date = raw_checked
        raw_model = ""
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


def _update_coverage_findings_section(
    text: str, verdict: str, quotes: Sequence[str]
) -> str:
    """Update or remove the `## Coverage findings` H2 body section (`4sd62s` N3)."""
    updated = text
    f_match = _FINDINGS_HDR_RE.search(updated)
    if f_match:
        start_pos = f_match.start()
        rest = updated[f_match.end() :]
        next_h2 = re.search(r"^##\s+", rest, re.MULTILINE)
        end_pos = (f_match.end() + next_h2.start()) if next_h2 else len(updated)
        updated = (
            updated[:start_pos].rstrip() + "\n\n" + updated[end_pos:].lstrip()
        ).rstrip() + "\n"

    if verdict == COVERAGE_FAIL:
        findings_block = ["## Coverage findings", ""]
        for q in quotes:
            findings_block.append(f'- "{q}"')
        findings_str = "\n".join(findings_block) + "\n\n"

        v_match = _VALIDATION_HDR_RE.search(updated)
        if v_match:
            insert_pos = v_match.start()
            updated = (
                updated[:insert_pos].rstrip()
                + "\n\n"
                + findings_str
                + updated[insert_pos:]
            )
        else:
            updated = updated.rstrip() + "\n\n" + findings_str
        updated = updated.rstrip() + "\n"
    return updated


def _restore_file_bytes(path: Path, raw_bytes: bytes) -> None:
    """Atomically restore `raw_bytes` to `path` so a failed append leaves zero partial write."""
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".aw-restore-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw_bytes)
        os.replace(tmp_name, path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


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
    """Write the coverage record into `plan_path` through `artifact_meta.append`.

    Sets `- Coverage:`, `- Coverage-Fingerprint:`, `- Coverage-Checked:` metadata fields
    and prepends the workflow history line via one `op: "coverage"` event, while updating or
    removing the `## Coverage findings` body section (`4sd62s` N3). All first-party imports
    are function-local.

    When `commit=True`, checks if `git status --porcelain -- <plan>` shows uncommitted changes
    BEFORE writing; if so, writes the record without committing and returns `written=True, committed=False`.
    Otherwise makes one path-scoped commit of the plan file. A failed commit restores staged index and never raises.
    If `artifact_meta.append` raises, restores the pre-call bytes and returns `written=False, committed=False`.
    """
    path = Path(plan_path)
    if not path.is_file():
        return CoverageWriteResult(
            written=False, committed=False, detail=f"plan file not found: {path}"
        )

    pre_bytes = path.read_bytes()
    plan_text = pre_bytes.decode("utf-8")

    from agent_workflows import artifact_core as _core
    from agent_workflows import artifact_meta as _meta
    from agent_workflows import project_context as _proj_ctx
    from agent_workflows.runner_shared import probe_cache_digest

    fingerprint = probe_cache_digest(plan_text)
    today = _core.utc_history_date()

    raw_model = (model or "").strip()
    if not raw_model or raw_model in ("host-default", "by host-default"):
        clean_model = ""
        hist_model = "by host-default"
    else:
        clean_model = raw_model.removeprefix("by ").strip()
        hist_model = clean_model or "by host-default"

    tool_str = (tool or "").strip() or "aw oc run"
    resolved_host = host if host is not None else ("agy" if "agy" in tool_str else "oc")

    if repo is not None:
        resolved_repo = Path(repo)
    else:
        owner = _proj_ctx.record_owner_root(path)
        if owner is not None:
            resolved_repo = owner
        else:
            cand = _core.repo_root_of(path)
            resolved_repo = path.parent if cand == path.resolve() else cand

    git_repo = _proj_ctx.record_git_root(path) or resolved_repo
    rel_path = (
        str(path.relative_to(git_repo)) if path.is_relative_to(git_repo) else str(path)
    )

    # 1. Dirty-plan check before writing if commit=True
    dirty = False
    dirty_reason = ""
    if commit:
        st_proc = subprocess.run(
            ["git", "--no-optional-locks", "status", "--porcelain", "--", rel_path],
            cwd=str(git_repo),
            capture_output=True,
            text=True,
            check=False,
        )
        if st_proc.returncode == 0 and st_proc.stdout.strip():
            dirty = True
            dirty_reason = (
                f"plan file {rel_path} already has uncommitted changes; "
                "record written without commit"
            )

    # 2. Update/remove ## Coverage findings body section (N3) and append op="coverage".
    id6_or_none = _meta.read_loose_id(plan_text)
    body_text = _update_coverage_findings_section(plan_text, verdict, quotes)

    event: dict[str, object] = {
        "op": "coverage",
        "coverage": verdict,
        "coverage_fingerprint": fingerprint,
        "message": f"fingerprint {fingerprint[:12]}, model {hist_model}",
    }
    actor_dict: dict[str, str] = {"tool": tool_str}
    if clean_model:
        actor_dict["model"] = clean_model
    render = _meta.LegacyRender(
        tag=f"coverage {verdict}",
        day=today,
        actor_label=tool_str,
        checked_by=clean_model or "host-default",
        history=True,
    )

    try:
        if body_text != plan_text:
            _core.atomic_write(path, body_text)
        _meta.append(
            _meta.LegacyTarget(path, "plans", id6_or_none),
            [event],
            actor=actor_dict,
            legacy_render=render,
            repo_root=resolved_repo,
            project_context=_meta.legacy_context(resolved_repo),
        )
    except Exception as exc:
        if path.is_file() and path.read_bytes() != pre_bytes:
            _restore_file_bytes(path, pre_bytes)
        return CoverageWriteResult(
            written=False,
            committed=False,
            detail=str(exc),
        )

    final_text = path.read_text(encoding="utf-8")

    if not commit:
        return CoverageWriteResult(written=True, committed=False, detail="")

    if dirty:
        return CoverageWriteResult(written=True, committed=False, detail=dirty_reason)

    # 3. Git add and commit
    add_proc = subprocess.run(
        ["git", "add", "--", rel_path],
        cwd=str(git_repo),
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
    declared_id6 = _meta.read_loose_id(final_text)
    if declared_id6:
        id6 = declared_id6
    else:
        fname_match = re.search(r"\b([0-9a-z]{6})\b", path.name)
        id6 = fname_match.group(1) if fname_match else path.stem

    from agent_workflows import git_commit_helper as _gch

    commit_msg = f"coverage({resolved_host}): record the coverage answer for {id6}"
    ident = _gch.agent_commit_identity(
        git_repo,
        model=None if hist_model == "by host-default" else hist_model,
        item_id6=id6,
        message=commit_msg,
    )
    commit_proc = subprocess.run(
        ["git", "commit", "-m", ident.message, "--", rel_path],
        cwd=str(git_repo),
        env=ident.env,
        capture_output=True,
        text=True,
        check=False,
    )
    if commit_proc.returncode != 0:
        subprocess.run(
            ["git", "restore", "--staged", "--", rel_path],
            cwd=str(git_repo),
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
