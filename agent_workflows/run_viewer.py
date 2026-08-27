"""Run viewer for inspecting and summarizing driver runs (aw oc/agy run records).

Read-only inspection tool for `.aw/records/runs/run-*` directories that displays
the ending state of each IPD step in similar unified format to `aw att` and `aw ipd lint`.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

from agent_workflows.attention import _TREE_COLOR_256, _identity_stem
from agent_workflows.term import Term


@dataclass
class StepSummary:
    position: int
    id6: str
    setid: str
    action: str
    status: str
    configured_file: str
    stem: str
    verification_status: str | None = None
    attempts_count: int = 0
    session_id: str | None = None
    disposition: str | None = None
    summary: str | None = None
    incomplete_requirements: list[str] = field(default_factory=list)


@dataclass
class RunSummary:
    run_id: str
    run_dir: Path
    created_at: str | None = None
    updated_at: str | None = None
    driver: str | None = None
    selectors: list[str] = field(default_factory=list)
    setids: list[str] = field(default_factory=list)
    steps: list[StepSummary] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)


def _find_stem_for_id6(repo_root: Path, id6: str) -> str | None:
    """Find the plan file stem for a given id6 across pending and executed plans."""
    for base_rel in (
        Path(".aw/records/plans/pending"),
        Path(".aw/records/plans/executed"),
        Path(".aw/records/plans/reusable"),
        Path(".agents/plans/pending"),
        Path(".agents/plans/executed"),
    ):
        base = repo_root / base_rel
        if base.is_dir():
            for p in base.glob("*.md"):
                if id6 in p.name:
                    return _identity_stem(str(p))
    return None


def load_run_summary(run_dir: Path, repo_root: Path = Path(".")) -> RunSummary | None:
    """Load a RunSummary from a run directory."""
    if not run_dir.is_dir():
        return None

    state_file = run_dir / "state.json"
    report_file = run_dir / "execution-report.md"

    run_id = run_dir.name
    created_at = None
    updated_at = None
    driver_name = None
    selectors: list[str] = []
    setids: list[str] = []
    steps: list[StepSummary] = []
    counts: dict[str, int] = {}

    if state_file.is_file():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            run_id = state.get("run_id") or run_dir.name
            created_at = state.get("created_at")
            updated_at = state.get("updated_at")

            driver_info = state.get("driver") or {}
            driver_path = (
                driver_info.get("path")
                if isinstance(driver_info, dict)
                else str(driver_info)
            )
            if driver_path:
                if "oc_runipd" in driver_path:
                    driver_name = "OpenCode"
                elif "agy_runipd" in driver_path or "runagy" in driver_path:
                    driver_name = "Antigravity"
                else:
                    driver_name = Path(driver_path).stem

            queue = state.get("queue") or []
            set_set = set()
            for idx, item in enumerate(queue, start=1):
                pos = item.get("position", idx)
                id6 = item.get("id6", "")
                setid = item.get("setid", "")
                if setid:
                    set_set.add(setid)
                action = item.get("action", "execute")
                status = item.get("status", "queued")
                counts[status] = counts.get(status, 0) + 1

                cfg_file = item.get("configured_file", "")
                stem = ""
                if cfg_file:
                    stem = _identity_stem(cfg_file)
                if not stem or stem == id6:
                    discovered = _find_stem_for_id6(repo_root, id6)
                    stem = (
                        discovered
                        if discovered
                        else (f"{setid}-{id6}" if setid else id6)
                    )

                v_status = item.get("verification_status")
                attempts = item.get("attempts") or []
                att_count = len(attempts)

                session_id = None
                if attempts and isinstance(attempts[-1], dict):
                    session_id = attempts[-1].get("session_id")
                    if not updated_at:
                        updated_at = attempts[-1].get("ended_at")

                outcome = item.get("last_outcome") or {}
                disposition = None
                summary_text = None
                incomplete: list[str] = []
                if isinstance(outcome, dict):
                    disposition = outcome.get("disposition")
                    summary_text = outcome.get("summary")
                    raw_incomplete = outcome.get("incomplete_requirements")
                    if isinstance(raw_incomplete, list):
                        incomplete = [str(r) for r in raw_incomplete]

                steps.append(
                    StepSummary(
                        position=pos,
                        id6=id6,
                        setid=setid,
                        action=action,
                        status=status,
                        configured_file=cfg_file,
                        stem=stem,
                        verification_status=v_status,
                        attempts_count=att_count,
                        session_id=session_id,
                        disposition=disposition,
                        summary=summary_text,
                        incomplete_requirements=incomplete,
                    )
                )

            setids = sorted(set_set)
        except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError):
            pass

    # Fallback to report file if state.json was absent or empty
    if not steps and report_file.is_file():
        try:
            report_text = report_file.read_text(encoding="utf-8")
            m_created = re.search(r"(?m)^-\s*Created:\s*(.+)$", report_text)
            if m_created and not created_at:
                created_at = m_created.group(1).strip()
            m_updated = re.search(r"(?m)^-\s*Updated:\s*(.+)$", report_text)
            if m_updated and not updated_at:
                updated_at = m_updated.group(1).strip()
            m_selectors = re.search(r"(?m)^-\s*Selectors:\s*`([^`]+)`", report_text)
            if m_selectors:
                selectors = [
                    s.strip() for s in m_selectors.group(1).split(",") if s.strip()
                ]

            # Parse markdown table
            for line in report_text.splitlines():
                if (
                    line.startswith("|")
                    and not line.startswith("| #")
                    and not line.startswith("|---")
                ):
                    cols = [c.strip() for c in line.split("|")[1:-1]]
                    if len(cols) >= 5:
                        try:
                            pos = int(cols[0])
                        except ValueError:
                            pos = len(steps) + 1
                        id6 = cols[1].replace("`", "").strip()
                        setid = (
                            cols[2].replace("`", "").strip() if len(cols) > 2 else ""
                        )
                        action = (
                            cols[3].replace("`", "").strip()
                            if len(cols) > 3
                            else "execute"
                        )
                        status = cols[4].strip() if len(cols) > 4 else "unknown"
                        v_status = (
                            cols[5].strip()
                            if len(cols) > 5 and cols[5].strip()
                            else None
                        )
                        attempts = 0
                        if len(cols) > 6:
                            try:
                                attempts = int(cols[6].strip())
                            except ValueError:
                                attempts = 1
                        session_id = (
                            cols[7].replace("`", "").strip() if len(cols) > 7 else None
                        )

                        discovered = _find_stem_for_id6(repo_root, id6)
                        stem = (
                            discovered
                            if discovered
                            else (f"{setid}-{id6}" if setid else id6)
                        )
                        counts[status] = counts.get(status, 0) + 1

                        steps.append(
                            StepSummary(
                                position=pos,
                                id6=id6,
                                setid=setid,
                                action=action,
                                status=status,
                                configured_file="",
                                stem=stem,
                                verification_status=v_status,
                                attempts_count=attempts,
                                session_id=session_id,
                            )
                        )
        except (OSError, ValueError, IndexError):
            pass

    return RunSummary(
        run_id=run_id,
        run_dir=run_dir,
        created_at=created_at,
        updated_at=updated_at,
        driver=driver_name,
        selectors=selectors,
        setids=setids,
        steps=steps,
        counts=counts,
    )


def discover_run_dirs(repo_root: Path = Path(".")) -> list[Path]:
    """Discover all run directories across canonical and legacy record roots."""
    roots = [
        repo_root / ".aw" / "records" / "runs",
        repo_root / ".aw" / "runs",
        repo_root / ".agents" / "runs",
    ]
    seen = set()
    found = []
    for r in roots:
        if r.is_dir():
            for p in sorted(r.iterdir()):
                if p.is_dir() and p.name.startswith("run-") and p.name not in seen:
                    seen.add(p.name)
                    found.append(p)
    return found


def resolve_target_runs(
    targets: Sequence[str | Path] | None = None,
    repo_root: Path = Path("."),
) -> list[Path]:
    """Resolve user-specified targets (directories, run_ids, setids, or substrings) to concrete run directories."""
    all_runs = discover_run_dirs(repo_root)

    if not targets:
        return all_runs

    resolved: list[Path] = []
    seen = set()

    for target in targets:
        t_str = str(target).strip()
        if not t_str:
            continue

        p = Path(t_str)
        if p.is_dir() and (p / "state.json").is_file():
            canon = p.resolve()
            if canon not in seen:
                seen.add(canon)
                resolved.append(p)
            continue
        elif (
            p.is_file()
            and p.parent.is_dir()
            and p.name in ("state.json", "events.jsonl", "execution-report.md")
        ):
            canon = p.parent.resolve()
            if canon not in seen:
                seen.add(canon)
                resolved.append(p.parent)
            continue

        # Substring or exact match against run directory name or setid
        matched = False
        for run_p in all_runs:
            if t_str == run_p.name or t_str in run_p.name:
                canon = run_p.resolve()
                if canon not in seen:
                    seen.add(canon)
                    resolved.append(run_p)
                matched = True

        if not matched:
            # Check if target matches a Set ID inside state.json
            for run_p in all_runs:
                s_file = run_p / "state.json"
                if s_file.is_file():
                    try:
                        content = s_file.read_text(encoding="utf-8")
                        if f'"{t_str}"' in content:
                            canon = run_p.resolve()
                            if canon not in seen:
                                seen.add(canon)
                                resolved.append(run_p)
                    except (OSError, json.JSONDecodeError):
                        pass

    return resolved


def _clean_timestamp(ts: str | None) -> str:
    """Format ISO timestamp into clean display date/time."""
    if not ts:
        return ""
    clean = ts.replace("T", " ")
    if "+" in clean:
        clean = clean.split("+")[0]
    if "Z" in clean:
        clean = clean.replace("Z", "")
    return clean[:19]


def format_step_line(step: StepSummary, term: Term, long: bool = False) -> str:
    """Format a single step summary line aligned with aw att / aw ipd lint style."""
    status_word = step.status
    if status_word == "substantially-complete":
        status_word = "complete"

    status_padded = (
        term.status_256(status_word, width=15)
        if getattr(term, "color", False)
        else status_word.ljust(15)
    )

    lead = "   "
    type_word = "plan"
    type_txt = (
        term.color256(type_word, _TREE_COLOR_256, bold=True)
        if getattr(term, "color", False)
        else type_word
    )
    type_prefix = type_txt + (" " * max(0, 10 - len(type_word))) + "  "

    stem = step.stem
    if not stem:
        stem = f"{step.setid}-{step.id6}" if step.setid else step.id6

    badges = []
    if step.attempts_count > 0:
        badges.append(f"[attempts: {step.attempts_count}]")
    if step.verification_status == "verified":
        badges.append(
            term.color256("[verified]", 46, bold=True)
            if getattr(term, "color", False)
            else "[verified]"
        )
    elif step.verification_status == "failed":
        badges.append(
            term.color256("[verify-failed]", 196, bold=True)
            if getattr(term, "color", False)
            else "[verify-failed]"
        )
    if step.action == "review":
        badges.append(
            term.color256("[review]", 226)
            if getattr(term, "color", False)
            else "[review]"
        )

    badge_txt = ("  " + "  ".join(badges)) if badges else ""

    disp_txt = ""
    if step.disposition and step.disposition not in (step.status, status_word):
        disp_styled = (
            term.status_256(step.disposition)
            if getattr(term, "color", False)
            else step.disposition
        )
        disp_txt = f"  {disp_styled}"

    return f"- {lead}{status_padded} {type_prefix}{stem}{badge_txt}{disp_txt}"


def format_run_human(run: RunSummary, term: Term, detail: bool = False) -> str:
    """Format a RunSummary as human terminal text."""
    lines = []

    # Header line: run_id [setid] timestamp (summary counts)
    run_id_txt = (
        term.color256(run.run_id, 33, bold=True)
        if getattr(term, "color", False)
        else run.run_id
    )
    set_txt = ""
    if run.setids:
        sets_joined = ", ".join(run.setids)
        set_txt = f"  [{sets_joined}]"

    date_str = _clean_timestamp(run.created_at or run.updated_at)
    date_txt = f"  {date_str}" if date_str else ""

    tally_parts = []
    for st, cnt in sorted(run.counts.items()):
        st_display = "complete" if st == "substantially-complete" else st
        tally_parts.append(f"{cnt} {st_display}")
    tally_str = ", ".join(tally_parts) if tally_parts else f"{len(run.steps)} steps"
    count_summary = (
        f"  ({len(run.steps)} steps: {tally_str})"
        if tally_parts
        else f"  ({len(run.steps)} steps)"
    )

    lines.append(f"{run_id_txt}{set_txt}{date_txt}{count_summary}")

    for step in run.steps:
        lines.append(format_step_line(step, term))
        if detail:
            if step.incomplete_requirements:
                for req in step.incomplete_requirements:
                    req_txt = (
                        term.color256(f"     ! incomplete: {req}", 214)
                        if getattr(term, "color", False)
                        else f"     ! incomplete: {req}"
                    )
                    lines.append(req_txt)
            if step.summary:
                sum_text = step.summary.strip().replace("\n", " ")
                if len(sum_text) > 120:
                    sum_text = sum_text[:117] + "..."
                sum_txt = (
                    term.color256(f"     * summary: {sum_text}", 245)
                    if getattr(term, "color", False)
                    else f"     * summary: {sum_text}"
                )
                lines.append(sum_txt)

    return "\n".join(lines)


def run_viewer_cli(args: argparse.Namespace) -> int:
    """CLI entry point for `aw runs` / run viewer."""
    repo_root = Path(getattr(args, "dir", None) or ".")
    raw_targets = getattr(args, "target", None) or getattr(args, "targets", None) or []
    if isinstance(raw_targets, str):
        raw_targets = [raw_targets]

    run_dirs = resolve_target_runs(raw_targets, repo_root)

    # Filtering options
    set_filter = getattr(args, "set", None)
    ipd_filter = getattr(args, "ipd", None) or getattr(args, "id6", None)
    status_filter = getattr(args, "status", None)
    failed_only = getattr(args, "failed", False)
    active_only = getattr(args, "active", False)
    latest_only = getattr(args, "latest", False)
    detail = getattr(args, "detail", False) or getattr(args, "long", False)
    is_json = getattr(args, "json", False)
    is_agent = getattr(args, "agent", False) or getattr(args, "as_agent", False)
    no_color = getattr(args, "no_color", False)

    term = Term(color=False if no_color else None)

    summaries: list[RunSummary] = []
    for r_dir in run_dirs:
        summary = load_run_summary(r_dir, repo_root)
        if not summary:
            continue

        if (
            set_filter
            and set_filter not in summary.setids
            and set_filter not in summary.selectors
        ):
            continue

        if ipd_filter and not any(s.id6 == ipd_filter for s in summary.steps):
            continue

        if status_filter and not any(s.status == status_filter for s in summary.steps):
            continue

        if failed_only and not any(
            s.status in ("failed", "partial", "blocked", "interrupted")
            for s in summary.steps
        ):
            continue

        if active_only and not any(s.status == "running" for s in summary.steps):
            continue

        summaries.append(summary)

    if latest_only and summaries:
        summaries = [summaries[-1]]

    if not summaries:
        if is_agent or is_json:
            print(json.dumps({"runs": []}, indent=2 if is_json else None))
            return 0
        term.line("no matching runs found")
        return 0

    if is_json:
        payload = {"runs": [asdict(s) for s in summaries]}
        for r_dict in payload["runs"]:
            r_dict["run_dir"] = str(r_dict["run_dir"])
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if is_agent:
        for s in summaries:
            s_dict = asdict(s)
            s_dict["run_dir"] = str(s_dict["run_dir"])
            print(json.dumps(s_dict, separators=(",", ":"), ensure_ascii=False))
        return 0

    # Human display
    for idx, summary in enumerate(summaries):
        if idx > 0:
            term.line("")
        term.line(format_run_human(summary, term, detail=detail))

    return 0
