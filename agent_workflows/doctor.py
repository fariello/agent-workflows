"""`aw doctor`: a comprehensive, read-only deep repo inspector that aggregates and reports health
signals across git state, framework configuration, version currency, cross-tree attention,
artifact schema/contract integrity, release gates, and local security/leak hygiene into one
structured, actionable report. Composes existing checks; reimplements none; writes nothing."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from agent_workflows import artifact_core as core
from agent_workflows import attention as attention_mod
from agent_workflows import check_engine
from agent_workflows import engine
from agent_workflows import leak_sanitizer
from agent_workflows import term as T
from agent_workflows import versioning


@dataclass
class GitProbeResult:
    available: bool = False
    branch: str = ""
    upstream: str = ""
    ahead: int = 0
    behind: int = 0
    staged: List[Tuple[str, str]] = field(default_factory=list)  # (code, path)
    modified: List[Tuple[str, str]] = field(default_factory=list)  # (code, path)
    untracked: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    drift: List[core.Drift] = field(default_factory=list)


@dataclass
class EnvironmentProbeResult:
    is_source_repo: bool = False
    installed_version: Optional[str] = None
    packaged_version: str = ""
    version_status: str = "current"
    layout: str = "none"  # ".aw", ".agents", or "unconfigured"
    preset: Optional[str] = None
    backend: Optional[str] = None
    setup_needed: bool = False
    drift: List[core.Drift] = field(default_factory=list)


@dataclass
class AttentionProbeResult:
    total_items: int = 0
    by_class: Dict[str, int] = field(default_factory=dict)
    active_release: Optional[str] = None
    release_blockers: List[str] = field(default_factory=list)
    drift: List[core.Drift] = field(default_factory=list)


@dataclass
class ArtifactsProbeResult:
    type_counts: Dict[str, int] = field(default_factory=dict)
    type_drift: Dict[str, List[core.Drift]] = field(default_factory=dict)
    executed_warnings: List[core.Drift] = field(default_factory=list)
    untracked_skipped: int = 0
    all_drift: List[core.Drift] = field(default_factory=list)


@dataclass
class SanitizerProbeResult:
    scanned_files: int = 0
    findings: List[leak_sanitizer.Finding] = field(default_factory=list)
    drift: List[core.Drift] = field(default_factory=list)


@dataclass
class DoctorReport:
    repo_root: Path
    git: GitProbeResult
    env: EnvironmentProbeResult
    attention: AttentionProbeResult
    artifacts: ArtifactsProbeResult
    sanitizer: SanitizerProbeResult
    all_drift: List[core.Drift] = field(default_factory=list)


# --------------------------------------------------------------------------------------
# Probes
# --------------------------------------------------------------------------------------


def probe_git(repo_root: Path) -> GitProbeResult:
    """Inspect git branch, upstream sync status, staged changes, unstaged modifications,
    and untracked files."""
    res = GitProbeResult()
    try:
        if not engine.git_available(repo_root):
            return res
        res.available = True

        proc = subprocess.run(
            ["git", "status", "--porcelain=v1", "-b", "-uall"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            shell=False,
        )
        if proc.returncode != 0:
            res.drift.append(
                core.Drift("<git>", "doctor.probe-failed", "git status failed")
            )
            return res

        lines = proc.stdout.splitlines()
        if lines:
            header = lines[0]
            # Parse `## branch...upstream [ahead X, behind Y]` or `## HEAD (no branch)`
            if header.startswith("## "):
                head_info = header[3:].strip()
                if "..." in head_info:
                    b_part, rest = head_info.split("...", 1)
                    res.branch = b_part.strip()
                    if "[" in rest and "]" in rest:
                        u_part, track = rest.split("[", 1)
                        res.upstream = u_part.strip()
                        track = track.rstrip("]")
                        for part in track.split(","):
                            part = part.strip()
                            if part.startswith("ahead "):
                                try:
                                    res.ahead = int(part.split()[1])
                                except ValueError:
                                    pass
                            elif part.startswith("behind "):
                                try:
                                    res.behind = int(part.split()[1])
                                except ValueError:
                                    pass
                    else:
                        res.upstream = rest.strip()
                else:
                    res.branch = head_info

            for line in lines[1:]:
                if not line or len(line) < 3:
                    continue
                code = line[:2]
                path = line[3:].strip()
                # Conflicts
                if code in ("UU", "AA", "DD", "UD", "DU", "AU", "UA"):
                    res.conflicts.append(path)
                    res.drift.append(
                        core.Drift(
                            path, "doctor.git-conflict", f"unmerged conflict ({code})"
                        )
                    )
                elif code == "??":
                    res.untracked.append(path)
                    res.drift.append(
                        core.Drift(path, "doctor.git-untracked", "untracked file")
                    )
                else:
                    x, y = code[0], code[1]
                    if x in "MADRC":
                        res.staged.append((x, path))
                        res.drift.append(
                            core.Drift(
                                path, "doctor.git-staged", f"staged change ({x})"
                            )
                        )
                    if y in "MD":
                        res.modified.append((y, path))
                        res.drift.append(
                            core.Drift(
                                path,
                                "doctor.git-dirty",
                                f"uncommitted modification ({y})",
                            )
                        )
    except Exception as exc:
        res.drift.append(core.Drift("<git>", "doctor.probe-failed", str(exc)[:120]))
    return res


def probe_environment(repo_root: Path) -> EnvironmentProbeResult:
    """Inspect framework layout, configuration preset/backend, and version currency."""
    res = EnvironmentProbeResult()
    try:
        # Detect framework source repository
        if (repo_root / "agent_workflows").is_dir() and (
            repo_root / "pyproject.toml"
        ).is_file():
            try:
                pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
                if 'name = "agent-workflows"' in pyproject:
                    res.is_source_repo = True
            except OSError:
                pass

        # Layout & config
        has_aw = (repo_root / ".aw").is_dir()
        has_agents = (repo_root / ".agents").is_dir()
        if has_aw and has_agents:
            res.layout = ".aw + .agents (dual layout / split-brain)"
            res.drift.append(
                core.Drift(
                    "<layout>",
                    "doctor.layout-split-brain",
                    "both .aw/ and .agents/ exist simultaneously; run 'aw migrate-layout' or remove stale directory",
                )
            )
        elif has_aw:
            res.layout = ".aw"
        elif has_agents:
            res.layout = ".agents"
        else:
            res.layout = "unconfigured"

        config_path = repo_root / ".aw" / "config.json"
        if not config_path.is_file():
            config_path = repo_root / ".agents" / "config.json"
        if config_path.is_file():
            try:
                import json

                cfg = json.loads(config_path.read_text(encoding="utf-8"))
                res.preset = cfg.get("preset")
                res.backend = cfg.get("records_backend")
            except Exception:
                pass

        # Versioning
        vfile = repo_root / ".aw" / "VERSION"
        if not vfile.is_file():
            vfile = repo_root / ".agents" / "VERSION"
        if vfile.is_file():
            try:
                res.installed_version = vfile.read_text(encoding="utf-8").strip()
            except OSError:
                pass

        try:
            res.packaged_version = versioning.resolve_version(
                engine.resolve_source_root(None)
            )
        except Exception:
            res.packaged_version = ""

        if not res.is_source_repo:
            res.version_status = versioning.status(
                res.installed_version, res.packaged_version
            )
            if res.version_status in ("stale", "unknown", "not-installed"):
                res.drift.append(
                    core.Drift(
                        "<version>",
                        f"doctor.version-{res.version_status}",
                        f"installed={res.installed_version!r} packaged={res.packaged_version!r}",
                    )
                )

        # Setup needed
        res.setup_needed = attention_mod.setup_needed(repo_root)
        if res.setup_needed:
            res.drift.append(
                core.Drift(
                    "<setup>",
                    "doctor.setup-needed",
                    "initial setup-repo action is open and repo is unconfigured",
                )
            )
    except Exception as exc:
        res.drift.append(core.Drift("<version>", "doctor.probe-failed", str(exc)[:120]))
    return res


def probe_attention(repo_root: Path) -> AttentionProbeResult:
    """Inspect cross-tree attention board validity and release gates."""
    res = AttentionProbeResult()
    try:
        items, drift = attention_mod.scan(repo_root)
        res.total_items = len(items)
        res.drift = list(drift)
        for it in items:
            res.by_class[it.attention_class] = (
                res.by_class.get(it.attention_class, 0) + 1
            )
        res.release_blockers = [
            it.path for it in attention_mod.release_blockers(items, repo_root)
        ]
        try:
            from agent_workflows import releases

            act = releases.load_active_release(repo_root)
            if act:
                res.active_release = f"{act.id6} ({act.version})"
        except Exception:
            pass
    except Exception as exc:
        res.drift.append(
            core.Drift("<attention>", "doctor.probe-failed", str(exc)[:120])
        )
    return res


def probe_artifacts(
    repo_root: Path,
    include_untracked: bool = False,
    include_executed: bool = False,
) -> ArtifactsProbeResult:
    """Inspect artifact schema conformity, frontmatter contracts, index reference integrity,
    and set-id collisions across all artifact types. By default excludes untracked/ directories
    and classifies executed/ non-conformances as historical warnings rather than errors."""
    res = ArtifactsProbeResult()
    try:
        from agent_workflows import artifact_types as at

        for t in at.ARTIFACT_TYPES:
            all_files = list(check_engine._iter_type_files(repo_root, t))
            if not include_untracked:
                filtered_files = [p for p in all_files if "untracked" not in p.parts]
                res.untracked_skipped += len(all_files) - len(filtered_files)
            else:
                filtered_files = all_files

            res.type_counts[t] = len(filtered_files)
            if t in check_engine.SUPPORTED:
                tdrift = check_engine.check_type(repo_root, t)
                if tdrift:
                    for d in tdrift:
                        loc = d.location
                        try:
                            p = Path(loc)
                            if p.is_absolute() and p.is_relative_to(repo_root):
                                loc = str(p.relative_to(repo_root))
                        except Exception:
                            pass

                        # Exclude untracked/ items if requested
                        if not include_untracked and "untracked" in loc.split(os.sep):
                            continue

                        drift_item = core.Drift(loc, d.rule, d.detail)
                        # Categorize executed/ artifacts as warnings unless strict
                        if not include_executed and "executed" in loc.split(os.sep):
                            res.executed_warnings.append(drift_item)
                        else:
                            res.type_drift.setdefault(t, []).append(drift_item)
                            res.all_drift.append(drift_item)

        # Global setid collisions across types
        collisions = check_engine.check_collisions(repo_root)
        if collisions:
            for d in collisions:
                loc = d.location
                try:
                    p = Path(loc)
                    if p.is_absolute() and p.is_relative_to(repo_root):
                        loc = str(p.relative_to(repo_root))
                except Exception:
                    pass

                if not include_untracked and "untracked" in loc.split(os.sep):
                    continue

                drift_item = core.Drift(loc, d.rule, d.detail)
                if not include_executed and "executed" in loc.split(os.sep):
                    res.executed_warnings.append(drift_item)
                else:
                    res.all_drift.append(drift_item)
    except Exception as exc:
        res.all_drift.append(
            core.Drift("<artifacts>", "doctor.probe-failed", str(exc)[:120])
        )
    return res


def probe_sanitizer(repo_root: Path) -> SanitizerProbeResult:
    """Scan tracked working tree for maintainer or machine identifying leaks."""
    res = SanitizerProbeResult()
    try:
        findings = leak_sanitizer.scan_working_tree(repo_root)
        res.findings = findings
        for f in findings:
            res.drift.append(
                core.Drift(
                    f.location, f"doctor.leak-{f.rule}", f"{f.severity}: {f.matched}"
                )
            )
    except Exception as exc:
        res.drift.append(
            core.Drift("<sanitizer>", "doctor.probe-failed", str(exc)[:120])
        )
    return res


def collect_doctor_report(
    repo_root: Path,
    include_untracked: bool = False,
    include_executed: bool = False,
    term: Optional[T.Term] = None,
    verbose_progress: bool = False,
) -> DoctorReport:
    """Run all doctor probes with periodic status updates and assemble the DoctorReport."""
    if verbose_progress and term is not None:
        term.line(
            f"{term.severity_label('info')} Checking environment and framework installation..."
        )
        term.stream.flush()

    env_res = probe_environment(repo_root)

    if verbose_progress and term is not None:
        term.line(
            f"{term.severity_label('info')} Inspecting git working tree and sync status..."
        )
        term.stream.flush()

    git_res = probe_git(repo_root)

    if verbose_progress and term is not None:
        term.line(
            f"{term.severity_label('info')} Scanning cross-tree attention view and release gates..."
        )
        term.stream.flush()

    attn_res = probe_attention(repo_root)

    if verbose_progress and term is not None:
        term.line(
            f"{term.severity_label('info')} Running security and local leak sanitizer..."
        )
        term.stream.flush()

    san_res = probe_sanitizer(repo_root)

    if verbose_progress and term is not None:
        term.line(
            f"{term.severity_label('info')} Validating artifact schema contracts and reference integrity..."
        )
        term.stream.flush()

    art_res = probe_artifacts(
        repo_root,
        include_untracked=include_untracked,
        include_executed=include_executed,
    )

    if verbose_progress and term is not None:
        term.line("")

    # De-duplicate drift by (location, rule, detail)
    seen = set()
    combined: List[core.Drift] = []
    for d in (
        git_res.drift
        + env_res.drift
        + attn_res.drift
        + art_res.all_drift
        + san_res.drift
    ):
        key = (d.location, d.rule, d.detail)
        if key not in seen:
            seen.add(key)
            combined.append(d)

    combined.sort(key=lambda d: (d.location, d.rule))
    return DoctorReport(
        repo_root=repo_root,
        git=git_res,
        env=env_res,
        attention=attn_res,
        artifacts=art_res,
        sanitizer=san_res,
        all_drift=combined,
    )


def run_doctor(
    repo_root: Path,
    include_untracked: bool = False,
    include_executed: bool = False,
) -> List[core.Drift]:
    """Aggregate every check signal into one List[Drift]. Read-only, deterministic (sorted
    by (location, rule)). Composes existing checks; reimplements none; writes nothing."""
    report = collect_doctor_report(
        repo_root,
        include_untracked=include_untracked,
        include_executed=include_executed,
    )
    return report.all_drift


def _version_drift(repo_root: Path) -> List[core.Drift]:
    """Legacy helper for testing version drift isolatedly."""
    return probe_environment(repo_root).drift


# --------------------------------------------------------------------------------------
# Human Report Renderer
# --------------------------------------------------------------------------------------


def render_human_report(report: DoctorReport, term: T.Term) -> str:
    """Render a comprehensive, colorized, beautifully structured health inspection report."""
    lines: List[str] = []

    header = term.colorize("aw doctor: deep repo inspection", "bold")
    lines.append(f"{header} ({report.repo_root})")
    lines.append("")

    total_findings = len(report.all_drift)

    # 1. Environment & Framework
    env = report.env
    env_status = (
        "ERROR"
        if any(
            d.rule.startswith("doctor.version-") or d.rule.startswith("doctor.layout-")
            for d in env.drift
        )
        else ("WARN" if env.setup_needed else "INFO")
    )
    badge_env = (
        term.severity_label("error")
        if env_status == "ERROR"
        else (
            term.severity_label("warn")
            if env_status == "WARN"
            else term.severity_label("info")
        )
    )

    lines.append(f"{badge_env} Environment & Framework")
    if env.is_source_repo:
        lines.append(f"  Repository:  Framework source checkout ({report.repo_root})")
        lines.append(
            f"  Package:     agent-workflows {env.packaged_version or '0.1.0'} (source root)"
        )
    else:
        lines.append(f"  Repository:  Target project repository ({report.repo_root})")
        ver_info = f"{env.installed_version or 'not installed'}"
        if env.packaged_version:
            ver_info += f" (packaged: {env.packaged_version})"
        lines.append(f"  Version:     {ver_info} [{env.version_status}]")

    layout_info = env.layout
    if env.preset or env.backend:
        layout_info += f" (preset: {env.preset or 'standard'}, backend: {env.backend or 'repo-tracked'})"
    if "split-brain" in env.layout:
        lines.append(f"  Layout:      {term.color256(layout_info, 196, bold=True)}")
        lines.append(
            f"  Warning:     {term.severity_label('error')} Dual layouts detected (.aw/ and .agents/). Run 'aw migrate-layout' to consolidate."
        )
    else:
        lines.append(f"  Layout:      {layout_info}")
    if env.setup_needed:
        lines.append(
            f"  Notice:      {term.severity_label('warn')} Initial setup needed (setup-repo action open)"
        )
    lines.append("")

    # 2. Git Working Tree
    git = report.git
    git_status = "INFO"
    if git.conflicts or git.modified:
        git_status = "ERROR"
    elif git.untracked or git.staged:
        git_status = "WARN"

    badge_git = (
        term.severity_label("error")
        if git_status == "ERROR"
        else (
            term.severity_label("warn")
            if git_status == "WARN"
            else term.severity_label("info")
        )
    )

    git_count_info = f" ({len(git.drift)} finding(s))" if git.drift else ""
    lines.append(f"{badge_git} Git Working Tree{git_count_info}")
    if not git.available:
        lines.append("  Git:         Not a git repository or git unavailable")
    else:
        track_parts = []
        if git.upstream:
            track_parts.append(f"tracking {git.upstream}")
            if git.ahead:
                track_parts.append(f"ahead {git.ahead}")
            if git.behind:
                track_parts.append(f"behind {git.behind}")
            if not git.ahead and not git.behind:
                track_parts.append("up to date")
        track_str = f" ({', '.join(track_parts)})" if track_parts else ""
        lines.append(f"  Branch:      {git.branch or 'HEAD'}{track_str}")

        if git.conflicts:
            lines.append(
                "  Conflicts:   "
                + term.color256(
                    f"{len(git.conflicts)} unmerged conflict(s)", 196, bold=True
                )
            )
            for c in git.conflicts:
                lines.append(f"    {term.color256('!', 196, bold=True)} {c}")

        if git.staged:
            lines.append(f"  Staged ({len(git.staged)}):")
            for code, p in git.staged:
                lines.append(f"    {term.color256('+', 46, bold=True)} [{code}] {p}")

        if git.modified:
            lines.append(f"  Unstaged modifications ({len(git.modified)}):")
            for code, p in git.modified:
                lines.append(f"    {term.color256('M', 214, bold=True)} [{code}] {p}")

        if git.untracked:
            lines.append(f"  Untracked files ({len(git.untracked)}):")
            for p in git.untracked:
                lines.append(f"    {term.color256('?', 39, bold=True)} {p}")

        if (
            not git.staged
            and not git.modified
            and not git.untracked
            and not git.conflicts
        ):
            lines.append("  Working tree: Clean (0 uncommitted or untracked changes)")
    lines.append("")

    # 3. Cross-Tree Attention & Release Gates
    attn = report.attention
    attn_status = "ERROR" if attn.drift else "INFO"
    badge_attn = (
        term.severity_label("error")
        if attn_status == "ERROR"
        else term.severity_label("info")
    )

    attn_count_info = f" ({len(attn.drift)} violation(s))" if attn.drift else ""
    lines.append(f"{badge_attn} Cross-Tree Attention & Release Gates{attn_count_info}")
    if attn.drift:
        lines.append(
            "  Attention:   "
            + term.color256(
                f"INVALID ({len(attn.drift)} contract violation(s))", 196, bold=True
            )
        )
        for d in attn.drift:
            lines.append(f"    - {d.location}: {d.rule} {d.detail}")
    else:
        breakdown = ", ".join(f"{count} {cls}" for cls, count in attn.by_class.items())
        lines.append(
            f"  Attention:   Valid (0 contract violations across {attn.total_items} items: {breakdown})"
        )

    if attn.active_release:
        rb_str = (
            f" ({len(attn.release_blockers)} active release blocker(s))"
            if attn.release_blockers
            else " (0 active blockers)"
        )
        lines.append(f"  Release:     {attn.active_release}{rb_str}")
        if attn.release_blockers:
            for rb in attn.release_blockers:
                lines.append(f"    > {term.color256(rb, 208, bold=True)}")
    lines.append("")

    # 4. Security & Local Leak Sanitizer
    san = report.sanitizer
    san_status = "ERROR" if san.findings else "INFO"
    badge_san = (
        term.severity_label("error")
        if san_status == "ERROR"
        else term.severity_label("info")
    )

    san_count_info = f" ({len(san.findings)} finding(s))" if san.findings else ""
    lines.append(f"{badge_san} Security & Local Leak Sanitizer{san_count_info}")
    if san.findings:
        lines.append(
            "  Sanitizer:   "
            + term.color256(
                f"{len(san.findings)} leak finding(s) detected", 196, bold=True
            )
        )
        for f in san.findings:
            lines.append(f"    - {f.location}: {f.rule} ({f.severity}: {f.snippet})")
    else:
        lines.append("  Sanitizer:   Clean (0 maintainer/local leak findings)")
    lines.append("")

    # 5. Artifact Integrity & Schema Contracts
    art = report.artifacts
    art_status = (
        "ERROR"
        if art.all_drift
        else ("WARN" if (art.executed_warnings or art.untracked_skipped) else "INFO")
    )
    badge_art = (
        term.severity_label("error")
        if art_status == "ERROR"
        else (
            term.severity_label("warn")
            if art_status == "WARN"
            else term.severity_label("info")
        )
    )

    art_count_info = f" ({len(art.all_drift)} finding(s))" if art.all_drift else ""
    lines.append(f"{badge_art} Artifact Integrity & Schema Contracts{art_count_info}")
    type_summaries = []
    for t, count in art.type_counts.items():
        drift_count = len(art.type_drift.get(t, []))
        if drift_count:
            type_summaries.append(f"{t}: {count} ({drift_count} drift)")
        else:
            type_summaries.append(f"{t}: {count} conforming")
    lines.append(f"  Inventory:   {', '.join(type_summaries)}")

    if art.executed_warnings:
        lines.append(
            f"  Warnings:    {term.severity_label('warn')} {len(art.executed_warnings)} historical non-conformance(s) in executed/ (use --include-executed to check strictly)"
        )
    if art.untracked_skipped:
        lines.append(
            f"  Notice:      {term.severity_label('info')} Excluded {art.untracked_skipped} artifact(s) in untracked/ directories (use --include-untracked to include)"
        )

    if art.all_drift:
        lines.append("  Findings:")
        for d in art.all_drift:
            lines.append(f"    - {d.location}: {d.rule} {d.detail}")
    lines.append("")

    # Summary Line
    lines.append("-" * 78)
    g = sum(1 for d in report.all_drift if d.rule.startswith("doctor.git-"))
    m = sum(
        1
        for d in report.all_drift
        if d.rule.startswith("doctor.name")
        or d.rule.startswith("check.")
        or d.rule.startswith("attention.")
        or "stale-index" in d.rule
    )
    v = sum(1 for d in report.all_drift if d.rule.startswith("doctor.version-"))
    summary = (
        f"aw doctor: {total_findings} finding(s) (git: {g}, names: {m}, version: {v})."
    )
    if (
        all(d.rule == "doctor.git-untracked" for d in report.all_drift)
        and report.all_drift
    ):
        summary += " - untracked files are informational, not errors"
    lines.append(summary)

    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------------------
# CLI Entrypoint
# --------------------------------------------------------------------------------------


def run(args, term: Optional[T.Term] = None) -> int:
    """`aw doctor` entrypoint: run every probe, print findings (or `no findings`), return the
    standard 0/1 exit code. `--agent` emits tab-separated `location\\trule\\tdetail`."""
    repo_root = Path(getattr(args, "dir", None) or os.getcwd())
    if term is None:
        term = T.Term(color=not getattr(args, "no_color", False))

    as_agent = getattr(args, "agent", False) or getattr(args, "as_agent", False)
    include_all = getattr(args, "include_all", False)
    include_untracked = include_all or getattr(args, "include_untracked", False)
    include_executed = include_all or getattr(args, "include_executed", False)

    try:
        drift = run_doctor(
            repo_root,
            include_untracked=include_untracked,
            include_executed=include_executed,
        )
    except TypeError:
        drift = run_doctor(repo_root)

    if as_agent:
        sys.stdout.write(core.render_agent_drift(drift))
    elif not drift:
        sys.stdout.write("aw doctor: no findings.\n")
    else:
        report = collect_doctor_report(
            repo_root,
            include_untracked=include_untracked,
            include_executed=include_executed,
            term=term,
            verbose_progress=True,
        )
        if report.all_drift != drift:
            report.all_drift = drift
        sys.stdout.write(render_human_report(report, term))

    return core.drift_exit_code(drift)
