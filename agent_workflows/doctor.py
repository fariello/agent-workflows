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
from typing import Any, Dict, List, Optional, Set, Tuple

from agent_workflows import artifact_core as core
from agent_workflows import attention as attention_mod
from agent_workflows import check_engine, engine, leak_sanitizer, versioning
from agent_workflows import term as T
from agent_workflows.renderers import get_renderer
from agent_workflows.result_types import (
    CommandResult,
    Diagnostic,
    Evidence,
    NextAction,
    OutputContext,
    OutputMode,
    select_output,
)


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "branch": self.branch,
            "upstream": self.upstream,
            "ahead": self.ahead,
            "behind": self.behind,
            "staged": self.staged,
            "modified": self.modified,
            "untracked": self.untracked,
            "conflicts": self.conflicts,
            "drift": [
                {"location": d.location, "rule": d.rule, "detail": d.detail}
                for d in self.drift
            ],
        }


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_source_repo": self.is_source_repo,
            "installed_version": self.installed_version,
            "packaged_version": self.packaged_version,
            "version_status": self.version_status,
            "layout": self.layout,
            "preset": self.preset,
            "backend": self.backend,
            "setup_needed": self.setup_needed,
            "drift": [
                {"location": d.location, "rule": d.rule, "detail": d.detail}
                for d in self.drift
            ],
        }


@dataclass
class AttentionProbeResult:
    total_items: int = 0
    by_class: Dict[str, int] = field(default_factory=dict)
    active_release: Optional[str] = None
    release_blockers: List[str] = field(default_factory=list)
    drift: List[core.Drift] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_items": self.total_items,
            "by_class": self.by_class,
            "active_release": self.active_release,
            "release_blockers": self.release_blockers,
            "drift": [
                {"location": d.location, "rule": d.rule, "detail": d.detail}
                for d in self.drift
            ],
        }


@dataclass
class ArtifactsProbeResult:
    type_counts: Dict[str, int] = field(default_factory=dict)
    type_drift: Dict[str, List[core.Drift]] = field(default_factory=dict)
    executed_warnings: List[core.Drift] = field(default_factory=list)
    untracked_skipped: int = 0
    all_drift: List[core.Drift] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type_counts": self.type_counts,
            "type_drift": {
                k: [
                    {"location": d.location, "rule": d.rule, "detail": d.detail}
                    for d in v
                ]
                for k, v in self.type_drift.items()
            },
            "executed_warnings": [
                {"location": d.location, "rule": d.rule, "detail": d.detail}
                for d in self.executed_warnings
            ],
            "untracked_skipped": self.untracked_skipped,
            "all_drift": [
                {"location": d.location, "rule": d.rule, "detail": d.detail}
                for d in self.all_drift
            ],
        }


@dataclass
class SanitizerProbeResult:
    scanned_files: int = 0
    findings: List[leak_sanitizer.Finding] = field(default_factory=list)
    drift: List[core.Drift] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scanned_files": self.scanned_files,
            "findings": [
                {
                    "location": f.location,
                    "line_number": getattr(f, "line_number", None),
                    "rule": f.rule,
                    "severity": getattr(f, "severity", "error"),
                    "snippet": f.snippet,
                }
                for f in self.findings
            ],
            "drift": [
                {"location": d.location, "rule": d.rule, "detail": d.detail}
                for d in self.drift
            ],
        }


@dataclass
class DoctorReport:
    repo_root: Path
    git: GitProbeResult
    env: EnvironmentProbeResult
    attention: AttentionProbeResult
    artifacts: ArtifactsProbeResult
    sanitizer: SanitizerProbeResult
    all_drift: List[core.Drift] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo_root": str(self.repo_root),
            "git": self.git.to_dict(),
            "env": self.env.to_dict(),
            "attention": self.attention.to_dict(),
            "artifacts": self.artifacts.to_dict(),
            "sanitizer": self.sanitizer.to_dict(),
            "all_drift": [
                {"location": d.location, "rule": d.rule, "detail": d.detail}
                for d in self.all_drift
            ],
        }


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
            all_files = list(
                check_engine._iter_type_files(
                    repo_root, t, include_untracked=include_untracked
                )
            )
            if not include_untracked:
                filtered_files = [p for p in all_files if "untracked" not in p.parts]
                res.untracked_skipped += len(all_files) - len(filtered_files)
            else:
                filtered_files = all_files

            res.type_counts[t] = len(filtered_files)
            if t in check_engine.SUPPORTED:
                tdrift = check_engine.check_type(
                    repo_root, t, include_untracked=include_untracked
                )
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

        # Global setid collisions across types, PLUS the proclint 79li67 COMMIT-SCOPED untooled-status
        # detector (a fast no-op unless a plan `- Status:` change is staged). Both are cross-tree /
        # commit-wide rules keyed off git state rather than a single record file.
        collisions = list(
            check_engine.check_collisions(
                repo_root, include_untracked=include_untracked
            )
        )
        try:
            collisions.extend(check_engine.check_status_untooled(repo_root))
        except Exception:
            pass
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


@dataclass
class Remediation:
    """Structured remediation guidance and concrete CLI action for a Drift finding."""

    title: str
    summary_fix: str
    detailed_fix: str
    command: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None


def _infer_artifact_type(path_str: str) -> Optional[str]:
    """Deterministically infer artifact type from path string or extension."""
    if not path_str:
        return None
    norm = path_str.replace("\\", "/")
    if (
        ".aw/records/plans" in norm
        or ".agents/plans" in norm
        or norm.endswith(".ipd.md")
    ):
        return "plans"
    if (
        ".aw/records/specs" in norm
        or ".agents/specs" in norm
        or norm.endswith(".spec.md")
    ):
        return "specs"
    if (
        ".aw/records/prompts" in norm
        or ".agents/prompts" in norm
        or norm.endswith(".prompt.md")
    ):
        return "prompts"
    if (
        ".aw/records/backlog" in norm
        or ".agents/backlog" in norm
        or norm.endswith(".backlog.md")
    ):
        return "backlog"
    if (
        ".aw/records/research" in norm
        or ".agents/research" in norm
        or norm.endswith(".research.md")
    ):
        return "research"
    if (
        ".aw/records/walkthroughs" in norm
        or ".agents/walkthroughs" in norm
        or norm.endswith(".walkthrough.md")
    ):
        return "walkthroughs"
    if (
        ".aw/records/roadmaps" in norm
        or ".agents/roadmaps" in norm
        or norm.endswith(".roadmap.md")
    ):
        return "roadmaps"
    if (
        ".aw/records/comms" in norm
        or ".agents/comms" in norm
        or norm.endswith(".comms.md")
    ):
        return "comms"
    if (
        ".aw/records/releases" in norm
        or ".agents/releases" in norm
        or norm.endswith(".release.md")
    ):
        return "releases"
    return None


def _normalize_rel_path(loc: str, repo_root: Path) -> str:
    """Normalize a drift location to a clean repo-relative POSIX path."""
    if not loc or (loc.startswith("<") and loc.endswith(">")):
        return loc
    try:
        p = Path(loc)
        if p.is_absolute() and p.is_relative_to(repo_root):
            return p.relative_to(repo_root).as_posix()
        return p.as_posix()
    except Exception:
        return loc


def build_remediation(d: core.Drift, repo_root: Path) -> Remediation:
    """Synthesize a structured Remediation record from a Drift finding."""
    rule = d.rule
    detail = d.detail
    loc = _normalize_rel_path(d.location, repo_root)
    art_type = _infer_artifact_type(loc)

    if "id6-identity-slot" in rule:
        title = "Filename identity-slot id6 is not this file's own identity (D140)"
        return Remediation(
            title=title,
            summary_fix="give this file its own id6 in its filename identity slot and reference the source artifact via a typed frontmatter field (e.g. 'Target-Id: <id6>') per DECISIONS.md D140.",
            detailed_fix=(
                f"this file's identity slot holds another artifact's id6; give {loc} its own newly-minted id6 "
                "and reference the source via a typed frontmatter field (e.g. 'Target-Id: <id6>') per DECISIONS.md D140."
            ),
            command=None,
            file_path=loc,
        )

    if "status-untooled" in rule:
        import re as _re

        title = "Plan status changed without an attributed history entry (looks hand-edited)"
        # Best-effort extraction of the new status word from the detail for a precise command.
        m_status = _re.search(r"changed to '([a-z-]+)'", detail)
        status_word = m_status.group(1) if m_status else "<status>"
        cmd = f"aw set {status_word} <id6>"
        return Remediation(
            title=title,
            summary_fix=(
                f"apply this status change via '{cmd}' (or 'aw ipd set {status_word} <id6>') so it "
                "carries an attributed '## Workflow history' line, instead of hand-editing '- Status:'."
            ),
            detailed_fix=(
                f"the '- Status:' of {loc} changed in this commit with no matching tool-authored "
                f"'## Workflow history' transition line; revert the hand edit and apply the change via "
                f"'{cmd}' (or 'aw ipd set {status_word} <id6>') so an attributed history entry is "
                "appended. This is the intermediate-transition sibling of the terminal 'aw ipd finalize' "
                "gate; it is a LOCAL commit-scoped detector (--no-verify bypasses the hook)."
            ),
            command=cmd,
            file_path=loc,
        )

    if "setid-collision" in rule:
        title = "Set ID collision across artifact records"
        target_type = art_type or "plans"
        cmd = f"aw group {target_type} {loc} --set <new-set-id>"
        return Remediation(
            title=title,
            summary_fix=cmd,
            detailed_fix=f"run '{cmd}' to assign a unique Set ID.",
            command=cmd,
            file_path=loc,
        )

    if "summary-unsafe" in rule:
        title = "Summary is not a single bounded control-char-free line"
        return Remediation(
            title=title,
            summary_fix="edit frontmatter '- Summary:' to be a single-line string without control characters or line breaks.",
            detailed_fix=f"edit frontmatter '- Summary:' in {loc} to be a single-line string without control characters or line breaks.",
            command=None,
            file_path=loc,
        )

    if "name-nonconformant" in rule:
        title = "Filename does not match artifact naming grammar"
        target_type = art_type or "plans"
        cmd = f"aw rename {target_type} {loc}"
        return Remediation(
            title=title,
            summary_fix=cmd,
            detailed_fix=f"run '{cmd}' or rename to match 'YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md'.",
            command=cmd,
            file_path=loc,
        )

    if "stale-index" in rule or rule.startswith("doctor.index-"):
        title = "Manifest index is missing or out of date"
        cmd = f"aw index {art_type}" if art_type else "aw index"
        return Remediation(
            title=title,
            summary_fix="aw index",
            detailed_fix=f"run '{cmd}' to regenerate the manifest index.",
            command=cmd,
            file_path=loc,
        )

    if "blocks-release-dangling" in rule:
        title = "Dangling Blocks-Release reference (target release does not exist)"
        target_type = art_type or "specs"
        cmd = f"aw {target_type} set {loc} --blocks-release next"
        return Remediation(
            title=title,
            summary_fix=cmd,
            detailed_fix=f"update '- Blocks-Release:' in {loc} to point to an existing planned release record or 'next' with '{cmd}'.",
            command=cmd,
            file_path=loc,
        )

    if rule.startswith("doctor.git-dirty"):
        title = "Unstaged git modifications"
        cmd = (
            f'git commit -m "Update" -- {loc}'
            if loc and not loc.startswith("<")
            else 'git commit -m "<msg>" -- <paths>'
        )
        return Remediation(
            title=title,
            summary_fix="review and stage/commit changes with 'git commit -m \"<msg>\" -- <paths>'.",
            detailed_fix=f"review and stage/commit changes with '{cmd}'.",
            command=cmd,
            file_path=loc,
        )

    if rule.startswith("doctor.git-untracked"):
        title = "Untracked files in git working tree"
        return Remediation(
            title=title,
            summary_fix="add files to git, add to .gitignore, or use untracked marker (*.untracked.md).",
            detailed_fix=f"add {loc} to git, add to .gitignore, or use untracked marker (*.untracked.md).",
            command=None,
            file_path=loc,
        )

    if rule.startswith("doctor.git-staged"):
        title = "Staged changes pending git commit"
        cmd = (
            f'git commit -m "Update" -- {loc}'
            if loc and not loc.startswith("<")
            else 'git commit -m "<msg>" -- <paths>'
        )
        return Remediation(
            title=title,
            summary_fix="commit staged changes with 'git commit -m \"<msg>\" -- <paths>'.",
            detailed_fix=f"commit staged changes with '{cmd}'.",
            command=cmd,
            file_path=loc,
        )

    if rule.startswith("doctor.git-conflict"):
        title = "Unmerged git merge conflicts"
        return Remediation(
            title=title,
            summary_fix="resolve conflict markers in the file and git commit.",
            detailed_fix=f"resolve conflict markers in {loc} and git commit.",
            command=None,
            file_path=loc,
        )

    if rule.startswith("doctor.setup-needed"):
        # setupmarker: the per-repo reminder is cleared by the `/setup-repo` WORKFLOW, not by
        # `aw setup` (the machine-wide install wizard, which never touches the marker). The
        # remediation is a workflow to execute rather than an `aw` subcommand; `command` stays
        # non-None so this keeps its top slot in the resolve_next_actions priority chain (a None
        # command is dropped from raw_actions entirely, which would silently demote setup below
        # leak/stale-index).
        title = "Initial repository setup pending"
        cmd = "/setup-repo"
        return Remediation(
            title=title,
            summary_fix=cmd,
            detailed_fix=(
                "run the /setup-repo workflow in this repo (or 'read and execute "
                ".aw/system/workflows/setup-repo/setup-repo.md'); it clears the "
                ".aw/setup-repo-needed.md reminder when it completes successfully. "
                "NOT 'aw setup', which is the machine-wide install wizard."
            ),
            command=cmd,
            file_path=None,
        )

    if rule.startswith("doctor.layout-split-brain"):
        title = "Dual framework layout (.aw/ and .agents/) split-brain"
        cmd = "aw migrate-layout"
        return Remediation(
            title=title,
            summary_fix=cmd,
            detailed_fix="run 'aw migrate-layout' to consolidate legacy .agents/ into .aw/.",
            command=cmd,
            file_path=None,
        )

    if rule.startswith("doctor.version-"):
        title = "Framework version mismatch or stale installation"
        cmd = "aw setup"
        return Remediation(
            title=title,
            summary_fix=cmd,
            detailed_fix="run 'aw setup' or reinstall the framework to update files to the current package version.",
            command=cmd,
            file_path=None,
        )

    if rule.startswith("doctor.leak-"):
        title = "Sensitive token or local leak finding"
        cmd = "aw sanitize --fix"
        return Remediation(
            title=title,
            summary_fix=cmd,
            detailed_fix=f"remove sensitive tokens in {loc} or run 'aw sanitize --fix'.",
            command=cmd,
            file_path=loc,
        )

    title = detail if len(detail) < 60 else rule
    return Remediation(
        title=title,
        summary_fix="inspect artifact frontmatter and schema conformity.",
        detailed_fix=f"inspect {loc} frontmatter and schema conformity.",
        command=None,
        file_path=loc,
    )


def resolve_next_actions(
    drift_list: List[core.Drift], repo_root: Path
) -> Tuple[Optional[str], List[NextAction]]:
    """Deterministically prioritize primary next command and aggregate all next actions."""
    if not drift_list:
        return None, []

    remediations = [build_remediation(d, repo_root) for d in drift_list]
    raw_actions: List[NextAction] = []
    seen_cmds: Set[str] = set()

    for rem in remediations:
        if rem.command and rem.command not in seen_cmds:
            seen_cmds.add(rem.command)
            raw_actions.append(
                NextAction(command=rem.command, description=rem.summary_fix)
            )

    if not raw_actions:
        return None, []

    # Priority ranking for single primary next command:
    # 1. setup-needed ("/setup-repo", a workflow rather than an `aw` subcommand)
    # 2. layout-split-brain ("aw migrate-layout")
    # 3. leak ("aw sanitize --fix")
    # 4. stale-index ("aw index" or "aw index <type>")
    # 5. first actionable command
    primary_cmd: Optional[str] = None
    for action in raw_actions:
        if action.command == "/setup-repo":
            primary_cmd = "/setup-repo"
            break
    if not primary_cmd:
        for action in raw_actions:
            if action.command == "aw migrate-layout":
                primary_cmd = "aw migrate-layout"
                break
    if not primary_cmd:
        for action in raw_actions:
            if action.command == "aw sanitize --fix":
                primary_cmd = "aw sanitize --fix"
                break
    if not primary_cmd:
        for action in raw_actions:
            if action.command.startswith("aw index") or action.command == "aw index":
                primary_cmd = action.command
                break
    if not primary_cmd:
        primary_cmd = raw_actions[0].command

    # Reorder raw_actions so primary_cmd is first
    ordered_actions: List[NextAction] = []
    for action in raw_actions:
        if action.command == primary_cmd:
            ordered_actions.insert(0, action)
        else:
            ordered_actions.append(action)

    return primary_cmd, ordered_actions


def _categorize_drift(d: core.Drift, repo_root: Path) -> Tuple[str, str, str, str, str]:
    """Categorize a Drift finding into (issue_title, directory, filename, extra_detail, fix_action)."""
    rem = build_remediation(d, repo_root)
    title = rem.title
    fix = rem.detailed_fix
    loc = rem.file_path or d.location

    extra = ""
    if "setid-collision" in d.rule and "conflicts with" in d.detail:
        parts = d.detail.split("conflicts with", 1)
        conflict_target = parts[1].strip()
        try:
            first_tok = conflict_target.split()[0]
            c_path = Path(first_tok)
            if c_path.is_absolute() and c_path.is_relative_to(repo_root):
                rel_c = str(c_path.relative_to(repo_root))
                conflict_target = conflict_target.replace(first_tok, rel_c)
        except Exception:
            pass
        extra = f"conflicts with {conflict_target}"

    p = Path(loc)
    if loc.startswith("<") and loc.endswith(">"):
        dir_str = loc
        fname = loc
    elif p.parent != Path("."):
        dir_str = p.parent.as_posix()
        fname = p.name
    else:
        fname = loc
        found = (
            [
                cand
                for cand in repo_root.rglob(fname)
                if not core.is_ignored_path(cand, repo_root)
            ]
            if fname
            not in (
                "<git>",
                "<version>",
                "<setup>",
                "<layout>",
                "<attention>",
                "<artifacts>",
                "<sanitizer>",
            )
            else []
        )
        if found:
            try:
                dir_str = found[0].parent.relative_to(repo_root).as_posix()
            except Exception:
                dir_str = "."
        else:
            dir_str = "."

    return title, dir_str, fname, extra, fix


# --------------------------------------------------------------------------------------
# Human Report Renderer
# --------------------------------------------------------------------------------------


def render_human_report(report: DoctorReport, term: T.Term) -> str:
    """Render a comprehensive, colorized, beautifully structured health inspection report."""
    lines: List[str] = []
    repo_root = report.repo_root

    header = term.colorize("aw doctor: deep repo inspection", "bold")
    lines.append(f"{header} ({repo_root})")
    lines.append("")

    total_findings = len(report.all_drift)

    # 1. Environment & Framework
    env = report.env
    env_findings = [
        d
        for d in env.drift
        if d.rule.startswith("doctor.version-") or d.rule.startswith("doctor.layout-")
    ]
    env_count_str = f" ({len(env_findings)} finding(s))" if env_findings else ""
    hdr_env = term.colorize("Environment & Framework", "bold") + (
        term.color256(env_count_str, 196, bold=True) if env_findings else ""
    )
    lines.append(hdr_env)
    if env.is_source_repo:
        lines.append(f"  Repository:  Framework source checkout ({repo_root})")
        lines.append(
            f"  Package:     agent-workflows {env.packaged_version or '0.1.0'} (source root)"
        )
    else:
        lines.append(f"  Repository:  Target project repository ({repo_root})")
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
            "  Warning:     Dual layouts detected (.aw/ and .agents/). Run 'aw migrate-layout' to consolidate."
        )
    else:
        lines.append(f"  Layout:      {layout_info}")
    if env.setup_needed:
        lines.append(
            f"  Notice:      {term.color256('Initial setup needed (setup-repo action open)', 214)}"
        )
    lines.append("")

    # 2. Git Working Tree
    git = report.git
    git_count_info = f" ({len(git.drift)} finding(s))" if git.drift else ""
    hdr_git = term.colorize("Git Working Tree", "bold") + (
        term.color256(git_count_info, 196 if git.conflicts else 214, bold=True)
        if git.drift
        else ""
    )
    lines.append(hdr_git)
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
    attn_count_info = f" ({len(attn.drift)} violation(s))" if attn.drift else ""
    hdr_attn = term.colorize("Cross-Tree Attention & Release Gates", "bold") + (
        term.color256(attn_count_info, 196, bold=True) if attn.drift else ""
    )
    lines.append(hdr_attn)
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
    san_count_info = f" ({len(san.findings)} finding(s))" if san.findings else ""
    hdr_san = term.colorize("Security & Local Leak Sanitizer", "bold") + (
        term.color256(san_count_info, 196, bold=True) if san.findings else ""
    )
    lines.append(hdr_san)
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
    art_count_info = f" ({len(art.all_drift)} finding(s))" if art.all_drift else ""
    hdr_art = term.colorize("Artifact Integrity & Schema Contracts", "bold") + (
        term.color256(art_count_info, 196 if art.all_drift else 214, bold=True)
        if art.all_drift
        else ""
    )
    lines.append(hdr_art)
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
            f"  Warnings:    {len(art.executed_warnings)} historical non-conformance(s) in executed/ (use --include-executed to check strictly)"
        )
    if art.untracked_skipped:
        lines.append(
            f"  Notice:      Excluded {art.untracked_skipped} artifact(s) in untracked/ directories (use --include-untracked to include)"
        )

    if art.all_drift:
        lines.append("  Findings:")
        groups = {}
        for d in art.all_drift:
            title, dir_str, fname, extra, fix = _categorize_drift(d, repo_root)
            key = (title, fix)
            if key not in groups:
                groups[key] = {}
            if dir_str not in groups[key]:
                groups[key][dir_str] = []
            groups[key][dir_str].append((fname, extra))

        for (title, fix), dir_map in groups.items():
            lines.append(f"    {term.color256('Issue: ' + title, 214, bold=True)}")
            for dir_str, files in dir_map.items():
                lines.append(f"    - {term.color256(dir_str, 39)}")
                for idx, (fname, extra) in enumerate(files, 1):
                    item_line = f"      {idx}. {fname}"
                    if extra:
                        item_line += f"\n         {term.color256('-> ' + extra, 244)}"
                    lines.append(item_line)
            lines.append(f"    {term.color256('Fix: ' + fix, 44)}")
            lines.append("")
    else:
        lines.append("")

    # Summary Line & Table
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

    if total_findings == 0:
        lines.append("aw doctor: no findings (repository is healthy).")
    else:
        summary = f"aw doctor: {total_findings} finding(s) (git: {g}, names: {m}, version: {v})."
        if (
            all(d.rule == "doctor.git-untracked" for d in report.all_drift)
            and report.all_drift
        ):
            summary += " - untracked files are informational, not errors"
        lines.append(summary)
        lines.append("")
        lines.append(term.colorize("Summary of issues and proposed fixes:", "bold"))

        summary_groups = {}
        for d in report.all_drift:
            rem = build_remediation(d, repo_root)
            key = (rem.title, rem.summary_fix)
            summary_groups[key] = summary_groups.get(key, 0) + 1

        for idx, ((title, fix), count) in enumerate(summary_groups.items(), 1):
            plural = "file" if count == 1 else "files"
            lines.append(f"  {idx}. {term.colorize(title, 'bold')} ({count} {plural})")
            lines.append(f"     {term.color256('Fix: ' + fix, 44)}")

    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------------------
# CLI Entrypoint
# --------------------------------------------------------------------------------------

_RUN_DOCTOR_CODE = getattr(run_doctor, "__code__", None)


def inspect_repo(
    repo_root: Path,
    include_untracked: bool = False,
    include_executed: bool = False,
    term: Optional[T.Term] = None,
    verbose_progress: bool = False,
) -> CommandResult:
    """Run all doctor probes and assemble a typed CommandResult with fact parity across renderers."""
    report = collect_doctor_report(
        repo_root,
        include_untracked=include_untracked,
        include_executed=include_executed,
        term=term,
        verbose_progress=verbose_progress,
    )

    # Honor monkeypatched run_doctor in unit test suites
    if getattr(run_doctor, "__code__", None) is not _RUN_DOCTOR_CODE:
        try:
            report.all_drift = run_doctor(
                repo_root,
                include_untracked=include_untracked,
                include_executed=include_executed,
            )
        except TypeError:
            report.all_drift = run_doctor(repo_root)

    exit_code = core.drift_exit_code(report.all_drift)
    status = "clean" if exit_code == 0 else "findings"
    total_findings = len(report.all_drift)

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

    if total_findings == 0:
        summary = "no findings (repository is healthy)."
    else:
        summary = f"{total_findings} finding(s) (git: {g}, names: {m}, version: {v})."

    diagnostics: List[Diagnostic] = []
    for d in report.all_drift:
        _title, _dir_str, _fname, _extra, fix = _categorize_drift(d, repo_root)
        diagnostics.append(
            Diagnostic(
                location=d.location,
                rule=d.rule,
                detail=d.detail,
                severity="error",
                fix=fix or None,
            )
        )

    evidence: List[Evidence] = [
        Evidence(
            key="git",
            value={
                "available": report.git.available,
                "branch": report.git.branch,
                "staged": len(report.git.staged),
                "modified": len(report.git.modified),
                "untracked": len(report.git.untracked),
            },
            status="clean" if not report.git.drift else "findings",
        ),
        Evidence(
            key="env",
            value={
                "is_source_repo": report.env.is_source_repo,
                "layout": report.env.layout,
                "version_status": report.env.version_status,
            },
            status="clean" if not report.env.drift else "findings",
        ),
        Evidence(
            key="attention",
            value={
                "total_items": report.attention.total_items,
                "by_class": dict(report.attention.by_class),
            },
            status="clean" if not report.attention.drift else "findings",
        ),
        Evidence(
            key="sanitizer",
            value={
                "scanned_files": report.sanitizer.scanned_files,
                "findings": len(report.sanitizer.findings),
            },
            status="clean" if not report.sanitizer.findings else "findings",
        ),
        Evidence(
            key="artifacts",
            value={
                "type_counts": dict(report.artifacts.type_counts),
                "untracked_skipped": report.artifacts.untracked_skipped,
                "executed_warnings": len(report.artifacts.executed_warnings),
            },
            status="clean" if not report.artifacts.all_drift else "findings",
        ),
    ]

    _primary_next, next_actions = resolve_next_actions(report.all_drift, repo_root)

    return CommandResult(
        command="doctor",
        status=status,
        exit_code=exit_code,
        summary=summary,
        diagnostics=diagnostics,
        evidence=evidence,
        next_actions=next_actions,
        data={
            "report": report.to_dict(),
            "human_rendered": render_human_report(report, term or T.Term()),
            "counts": {"git": g, "names": m, "version": v},
        },
        complete=True,
    )


def run(
    args: Any,
    term: Optional[T.Term] = None,
    context: Optional[OutputContext] = None,
) -> int:
    """`aw doctor` entrypoint: run every probe, emit structured output via the renderer boundary,
    and return the standard 0/1 exit code."""
    repo_root = Path(getattr(args, "dir", None) or os.getcwd())
    if context is None:
        if term is not None and not (
            getattr(args, "agent", False) or getattr(args, "as_agent", False)
        ):
            context = OutputContext(
                mode=OutputMode.HUMAN,
                color=term.color,
                stdout=term.stream or sys.stdout,
            )
        else:
            context = select_output(args)
    if term is None:
        term = T.Term(stream=context.stdout, color=context.color)

    include_all = getattr(args, "include_all", False)
    include_untracked = include_all or getattr(args, "include_untracked", False)
    include_executed = include_all or getattr(args, "include_executed", False)

    if context.is_human:
        # Human CLI mode: immediate start announcement and single probe execution
        term.line(
            f"{term.severity_label('info')} Starting aw doctor repository health check..."
        )
        term.stream.flush()

    result = inspect_repo(
        repo_root,
        include_untracked=include_untracked,
        include_executed=include_executed,
        term=term,
        verbose_progress=context.is_human,
    )

    renderer = get_renderer(context)
    return renderer.emit(result, context)
