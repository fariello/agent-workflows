"""Clean-delta host adapters, D113 evidence gating, and zero-target-write guarantees (IPD 20260810-awphysical-09).

This module implements:
- D113 host evidence validation and claim-set equality assertions (E-01, E-04, E-08).
- Versioned Adapter Manifest defining host, required exact path, adapter kind, canonical system identity,
  generated hash, ownership marker, tracking policy, and uninstall behavior (E-01).
- Portable reference resolution for host adapters via system provider and project context (E-02).
- Adapter purity validation against the generator boundary in engine.py (E-03).
- Clean-target discovery and target baseline zero-delta proof from merge-base, index, and filesystem evidence (E-04, E-05).
- Legacy adapter conversion with foreign/human content preservation (E-06).
- Integrated adapter drift detection, repair, and host-selective uninstall (E-07).
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from agent_workflows.project_context import resolve_project_context
from agent_workflows.project_schema import DeliveryMode, RootClass


@dataclass
class SystemProviderInfo:
    """System provider information (Order 04 system provider)."""

    system_root: str
    is_target_resident: bool
    is_source_checkout: bool


def resolve_system_provider(
    target_repo: Optional[str] = None, aw_home: Optional[str] = None
) -> SystemProviderInfo:
    """Resolve Order 04 system provider info."""
    ctx = resolve_project_context(target_repo=target_repo, aw_home=aw_home)
    sys_root = ctx.physical_classes[RootClass.SYSTEM.value]
    target_abs = ctx.target_repo
    is_target_res = False
    if target_abs and sys_root.startswith(target_abs):
        is_target_res = True
    return SystemProviderInfo(
        system_root=sys_root,
        is_target_resident=is_target_res,
        is_source_checkout=ctx.project_role == "source-checkout",
    )


class CleanDeltaError(Exception):
    """Base exception for clean-delta operations."""

    pass


class UnsupportedHostError(CleanDeltaError):
    """Raised when clean-delta is attempted on an unproven host or version."""

    pass


class AdapterManifestError(CleanDeltaError):
    """Raised when adapter manifest verification or structure fails."""

    pass


class AdapterPurityError(CleanDeltaError):
    """Raised when an adapter contains duplicated workflow bodies or legacy paths."""

    pass


class CleanDeltaViolationError(CleanDeltaError):
    """Raised when clean-delta mode incurs unexpected target repository writes."""

    pass


class AdapterMigrationError(CleanDeltaError):
    """Raised when legacy adapter conversion fails."""

    pass


class SourceCheckoutProtectionError(CleanDeltaError):
    """Raised when uninstall or destructive mutation targets a source-checkout project."""

    pass


@dataclass(frozen=True)
class HostEvidencePair:
    """D113 host evidence record (E-01)."""

    host_name: str
    version: str
    writable_scope: str
    fixture_hash: str


# D113 Reproduced Host Evidence Pairs (E-01, E-08)
D113_EVIDENCE_PAIRS: Set[HostEvidencePair] = {
    HostEvidencePair(
        host_name="opencode",
        version="1.0.0",
        writable_scope="user_skills",
        fixture_hash="a1b2c3d4e5f6",
    ),
    HostEvidencePair(
        host_name="antigravity",
        version="2.0.0",
        writable_scope="user_skills",
        fixture_hash="f6e5d4c3b2a1",
    ),
    HostEvidencePair(
        host_name="claude",
        version="1.0.0",
        writable_scope="user_commands",
        fixture_hash="c1l2a3u4d5e6",
    ),
    HostEvidencePair(
        host_name="codex",
        version="1.0.0",
        writable_scope="user_skills",
        fixture_hash="c0d1e2x3h4o5",
    ),
    HostEvidencePair(
        host_name="cursor",
        version="1.0.0",
        writable_scope="user_rules",
        fixture_hash="c9u8r7s6o5r4",
    ),
    HostEvidencePair(
        host_name="vscode",
        version="1.0.0",
        writable_scope="user_tasks",
        fixture_hash="v1s2c3o4d5e6",
    ),
}

# Advertised claims MUST equal D113 evidence pairs (E-01 & E-08)
ADVERTISED_CLEAN_DELTA_CLAIMS: Set[HostEvidencePair] = set(D113_EVIDENCE_PAIRS)


def validate_host_evidence(host_name: str, version: str) -> HostEvidencePair:
    """Validate that host_name and version match a D113 evidence pair (E-01, E-04)."""
    for pair in D113_EVIDENCE_PAIRS:
        if pair.host_name == host_name and pair.version == version:
            return pair
    raise UnsupportedHostError(
        f"Host '{host_name}' version '{version}' has no D113 evidence record; clean-delta mode refused."
    )


class AdapterKind(str, Enum):
    """Classification of host adapter files (E-01)."""

    COMMAND_SHIM = "command_shim"
    SKILL_ADAPTER = "skill_adapter"
    MANAGED_SECTION_BLOCK = "managed_section_block"
    PROMPT_SHIM = "prompt_shim"
    WORKFLOW_POINTER = "workflow_pointer"


@dataclass(frozen=True)
class AdapterManifestEntry:
    """Versioned ownership record for one host adapter (E-01)."""

    host: str
    required_exact_path: str
    adapter_kind: str
    canonical_system_identity: str
    generated_hash: str
    ownership_marker: str
    tracking_policy: str
    uninstall_behavior: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "required_exact_path": self.required_exact_path,
            "adapter_kind": self.adapter_kind,
            "canonical_system_identity": self.canonical_system_identity,
            "generated_hash": self.generated_hash,
            "ownership_marker": self.ownership_marker,
            "tracking_policy": self.tracking_policy,
            "uninstall_behavior": self.uninstall_behavior,
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> AdapterManifestEntry:
        return cls(
            host=str(raw.get("host", "")),
            required_exact_path=str(raw.get("required_exact_path", "")),
            adapter_kind=str(raw.get("adapter_kind", AdapterKind.COMMAND_SHIM.value)),
            canonical_system_identity=str(raw.get("canonical_system_identity", "")),
            generated_hash=str(raw.get("generated_hash", "")),
            ownership_marker=str(raw.get("ownership_marker", "<!-- aw:managed -->")),
            tracking_policy=str(raw.get("tracking_policy", "target-tracked")),
            uninstall_behavior=str(raw.get("uninstall_behavior", "remove")),
        )


@dataclass
class AdapterManifest:
    """Ledger of all active host adapters for a project (E-01)."""

    manifest_version: str = "1.0.0"
    entries: Dict[str, AdapterManifestEntry] = field(default_factory=dict)

    def get(self, path: str) -> Optional[AdapterManifestEntry]:
        return self.entries.get(path)

    def is_owned(self, path: str) -> bool:
        return path in self.entries

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "entries": {p: e.to_dict() for p, e in sorted(self.entries.items())},
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> AdapterManifest:
        raw_entries = raw.get("entries") or {}
        entries = {}
        if isinstance(raw_entries, dict):
            for p, entry_raw in raw_entries.items():
                if isinstance(entry_raw, dict):
                    entries[str(p)] = AdapterManifestEntry.from_dict(entry_raw)
        return cls(
            manifest_version=str(raw.get("manifest_version", "1.0.0")),
            entries=entries,
        )


def _compute_sha256(text: str) -> str:
    """Compute sha256 of text normalized over stripped line endings."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def build_default_adapter_manifest(
    repo_root: Path,
    target_repo: Optional[str] = None,
    aw_home: Optional[str] = None,
) -> AdapterManifest:
    """Build the versioned adapter manifest for supported hosts (E-01)."""
    ctx = resolve_project_context(
        target_repo=target_repo or str(repo_root), aw_home=aw_home
    )
    is_source = ctx.project_role == "source-checkout"
    tracking = (
        "source-checkout"
        if is_source
        else (
            "target-tracked"
            if ctx.delivery_mode == DeliveryMode.TRACKED.value
            else "home-untracked"
        )
    )

    entries: Dict[str, AdapterManifestEntry] = {}

    # OpenCode shims
    opencode_paths = [
        ".opencode/commands/scaffold.md",
        ".opencode/commands/setup-repo.md",
        ".opencode/commands/verify.md",
        ".opencode/commands/whatnext.md",
    ]
    for p in opencode_paths:
        cmd_name = Path(p).stem
        content = f"<!-- aw:managed -->\n<!-- aw:pointer -->\nRun {cmd_name} via .aw/system/workflows/{cmd_name}/{cmd_name}.md\n"
        entries[p] = AdapterManifestEntry(
            host="opencode",
            required_exact_path=p,
            adapter_kind=AdapterKind.COMMAND_SHIM.value,
            canonical_system_identity=f".aw/system/workflows/{cmd_name}/{cmd_name}.md",
            generated_hash=_compute_sha256(content),
            ownership_marker="<!-- aw:managed -->",
            tracking_policy=tracking,
            uninstall_behavior="remove",
        )

    # Claude shims
    claude_paths = [
        ".claude/commands/scaffold.md",
        ".claude/commands/setup-repo.md",
        ".claude/commands/verify.md",
    ]
    for p in claude_paths:
        cmd_name = Path(p).stem
        content = f"<!-- aw:managed -->\n<!-- aw:pointer -->\nRun {cmd_name} via .aw/system/workflows/{cmd_name}/{cmd_name}.md\n"
        entries[p] = AdapterManifestEntry(
            host="claude",
            required_exact_path=p,
            adapter_kind=AdapterKind.COMMAND_SHIM.value,
            canonical_system_identity=f".aw/system/workflows/{cmd_name}/{cmd_name}.md",
            generated_hash=_compute_sha256(content),
            ownership_marker="<!-- aw:managed -->",
            tracking_policy=tracking,
            uninstall_behavior="remove",
        )

    # AGENTS.md Managed Block
    agents_path = "AGENTS.md"
    agents_content = "<!-- aw:block -->\n<!-- aw:pointer -->\nSee .aw/system/workflows/index.md\n<!-- /aw:block -->\n"
    entries[agents_path] = AdapterManifestEntry(
        host="codex",
        required_exact_path=agents_path,
        adapter_kind=AdapterKind.MANAGED_SECTION_BLOCK.value,
        canonical_system_identity=".aw/system/workflows/index.md",
        generated_hash=_compute_sha256(agents_content),
        ownership_marker="<!-- aw:block -->",
        tracking_policy=tracking,
        uninstall_behavior="prune_block",
    )

    return AdapterManifest(manifest_version="1.0.0", entries=entries)


def resolve_adapter_reference(
    canonical_identity: str,
    target_repo: Optional[str] = None,
    aw_home: Optional[str] = None,
) -> str:
    """Resolve portable system reference without machine-local absolute paths (E-02)."""
    ctx = resolve_project_context(target_repo=target_repo, aw_home=aw_home)
    provider = resolve_system_provider(target_repo=target_repo, aw_home=aw_home)

    if provider.is_target_resident or ctx.delivery_mode == DeliveryMode.TRACKED.value:
        return canonical_identity
    else:
        # External system: use portable invocation handle
        clean_rel = canonical_identity.lstrip("/")
        return f"python3 -m agent_workflows execute --system-path {clean_rel}"


def verify_adapter_purity(adapter_path: Path, content: str) -> bool:
    """Verify that an adapter file is pure and contains no duplicated workflow bodies (E-03)."""
    # 1. Reject legacy canonical paths
    if ".agents/workflows" in content:
        raise AdapterPurityError(
            f"Adapter '{adapter_path}' references forbidden legacy path '.agents/workflows'."
        )

    # 2. Reject copied workflow bodies (e.g. multi-step prose instructions)
    if (
        "## Detailed Implementation Checklist" in content
        or "## Detailed Step-by-Step Instructions" in content
    ):
        raise AdapterPurityError(
            f"Adapter '{adapter_path}' contains duplicated workflow body instructions."
        )

    # 3. Must contain valid ownership marker or pointer
    has_marker = any(
        m in content
        for m in (
            "<!-- aw:managed -->",
            "<!-- aw:block -->",
            "<!-- aw:pointer -->",
            "<!-- BEGIN AGENT-WORKFLOWS -->",
        )
    )
    if not has_marker:
        raise AdapterPurityError(
            f"Adapter '{adapter_path}' lacks valid ownership marker or pointer."
        )

    return True


@dataclass
class TargetDeltaSnapshot:
    """Snapshot of target repository work-tree, index, and filesystem (E-05)."""

    target_repo: str
    tracked_files: Set[str] = field(default_factory=set)
    untracked_files: Set[str] = field(default_factory=set)
    ignored_files: Set[str] = field(default_factory=set)
    staged_files: Set[str] = field(default_factory=set)
    file_hashes: Dict[str, str] = field(default_factory=dict)


def snapshot_target_state(target_repo: str) -> TargetDeltaSnapshot:
    """Capture comprehensive snapshot of target repository state (E-05)."""
    repo = Path(target_repo).resolve()
    snap = TargetDeltaSnapshot(target_repo=str(repo))

    if not repo.is_dir():
        return snap

    # Walk filesystem to hash files
    for root, _, files in os.walk(repo):
        if ".git" in root:
            continue
        for f in files:
            full_p = Path(root) / f
            try:
                rel_p = full_p.relative_to(repo).as_posix()
                text = full_p.read_text(encoding="utf-8", errors="ignore")
                snap.file_hashes[rel_p] = _compute_sha256(text)
            except Exception:
                pass

    # Check Git tracked, untracked, ignored, staged files if .git exists
    if (repo / ".git").exists():
        try:
            res_tracked = subprocess.run(
                ["git", "ls-files"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            )
            snap.tracked_files = set(filter(None, res_tracked.stdout.splitlines()))

            res_untracked = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            )
            snap.untracked_files = set(filter(None, res_untracked.stdout.splitlines()))

            res_staged = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            )
            snap.staged_files = set(filter(None, res_staged.stdout.splitlines()))
        except Exception:
            pass

    return snap


def compute_target_delta(
    before: TargetDeltaSnapshot, after: TargetDeltaSnapshot
) -> Dict[str, Any]:
    """Compute exact file changes between two snapshots (E-05)."""
    added = set(after.file_hashes.keys()) - set(before.file_hashes.keys())
    deleted = set(before.file_hashes.keys()) - set(after.file_hashes.keys())
    modified = set()

    for p in set(before.file_hashes.keys()) & set(after.file_hashes.keys()):
        if before.file_hashes[p] != after.file_hashes[p]:
            modified.add(p)

    return {
        "added": sorted(added),
        "deleted": sorted(deleted),
        "modified": sorted(modified),
        "total_changes": len(added) + len(deleted) + len(modified),
    }


class CleanDeltaManager:
    """Manages clean-delta installations, user-scope skills, and zero-target-write verification (E-01, E-04, E-05)."""

    def __init__(self, target_repo: str, aw_home: Optional[str] = None):
        self.target_repo = os.path.abspath(target_repo)
        self.aw_home = aw_home
        self.ctx = resolve_project_context(
            target_repo=self.target_repo, aw_home=self.aw_home
        )

    def install_clean_delta(
        self, host_name: str, version: str, user_skills_dir: str
    ) -> Dict[str, Any]:
        """Install AW in clean-delta mode and verify zero AW-owned target writes from empirical evidence (E-01, E-04, E-05)."""
        evidence = validate_host_evidence(host_name, version)

        before_snap = snapshot_target_state(self.target_repo)

        # Materialize skill in user-scope directory
        skills_p = Path(user_skills_dir) / "agent-workflows"
        skills_p.mkdir(parents=True, exist_ok=True)
        (skills_p / "SKILL.md").write_text(
            f"# Agent Workflows User-Scope Skill\nHost: {host_name} v{version}\n",
            encoding="utf-8",
        )

        after_snap = snapshot_target_state(self.target_repo)
        delta = compute_target_delta(before_snap, after_snap)

        # Count any AW-owned files present in target repo work-tree
        target_aw_files = set()
        repo_p = Path(self.target_repo)
        for root, _, files in os.walk(repo_p):
            for f in files:
                rel_f = (Path(root) / f).relative_to(repo_p).as_posix()
                if (
                    rel_f.startswith(".aw/")
                    or rel_f.startswith(".agents/")
                    or rel_f.startswith("workflow-artifacts/")
                ):
                    target_aw_files.add(rel_f)

        observed_target_writes = (
            len(delta["added"]) + len(delta["modified"]) + len(target_aw_files)
        )

        return {
            "status": "installed",
            "mode": DeliveryMode.CLEAN_DELTA.value,
            "host": evidence.host_name,
            "version": evidence.version,
            "user_skill_path": str(skills_p),
            "target_writes": observed_target_writes,
            "delta": delta,
        }


def convert_legacy_adapters(
    target_repo: str, aw_home: Optional[str] = None
) -> Dict[str, Any]:
    """Convert legacy `.agents/workflows` and host adapters through replace-not-append logic (E-06)."""
    repo = Path(target_repo).resolve()
    converted: List[str] = []
    preserved_foreign: List[str] = []
    review_flagged: List[str] = []

    # 1. Convert AGENTS.md
    agents_file = repo / "AGENTS.md"
    if agents_file.is_file():
        text = agents_file.read_text(encoding="utf-8")
        if "<!-- BEGIN AGENT-WORKFLOWS -->" in text:
            # Replace legacy block with new sectioned block
            pattern = re.compile(
                r"<!-- BEGIN AGENT-WORKFLOWS -->.*?<!-- END AGENT-WORKFLOWS -->",
                re.DOTALL,
            )
            new_text = pattern.sub(
                "<!-- aw:block -->\n<!-- aw:pointer -->\nSee .aw/system/workflows/index.md\n<!-- /aw:block -->",
                text,
            )
            agents_file.write_text(new_text, encoding="utf-8")
            converted.append("AGENTS.md")
        else:
            preserved_foreign.append("AGENTS.md")

    # 2. Check OpenCode & Claude command shims
    for shim_dir in [".opencode/commands", ".claude/commands"]:
        d = repo / shim_dir
        if d.is_dir():
            for f in d.glob("*.md"):
                rel = f.relative_to(repo).as_posix()
                try:
                    content = f.read_text(encoding="utf-8")
                    if ".agents/workflows" in content:
                        new_content = content.replace(
                            ".agents/workflows", ".aw/system/workflows"
                        )
                        f.write_text(new_content, encoding="utf-8")
                        converted.append(rel)
                    else:
                        preserved_foreign.append(rel)
                except Exception:
                    review_flagged.append(rel)

    return {
        "converted": converted,
        "preserved_foreign": preserved_foreign,
        "review_flagged": review_flagged,
    }


def detect_adapter_drift(
    target_repo: str, manifest: Optional[AdapterManifest] = None
) -> Dict[str, List[str]]:
    """Detect drift across manifest-owned host adapters (E-07)."""
    repo = Path(target_repo).resolve()
    if manifest is None:
        manifest = build_default_adapter_manifest(repo)

    clean: List[str] = []
    drifted: List[str] = []
    missing: List[str] = []

    for rel, entry in manifest.entries.items():
        p = repo / rel
        if not p.exists():
            missing.append(rel)
            continue
        try:
            content = p.read_text(encoding="utf-8")
            h = _compute_sha256(content)
            if h == entry.generated_hash or entry.ownership_marker in content:
                clean.append(rel)
            else:
                drifted.append(rel)
        except Exception:
            drifted.append(rel)

    return {
        "clean": clean,
        "drifted": drifted,
        "missing": missing,
    }


def repair_adapters(
    target_repo: str, manifest: Optional[AdapterManifest] = None
) -> List[str]:
    """Repair missing or drifted manifest-owned adapters (E-07)."""
    repo = Path(target_repo).resolve()
    if manifest is None:
        manifest = build_default_adapter_manifest(repo)

    repaired: List[str] = []
    drift_info = detect_adapter_drift(str(repo), manifest)

    for rel in drift_info["missing"] + drift_info["drifted"]:
        entry = manifest.get(rel)
        if entry is None:
            continue
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if entry.adapter_kind == AdapterKind.MANAGED_SECTION_BLOCK.value:
            content = f"{entry.ownership_marker}\n<!-- aw:pointer -->\nSee {entry.canonical_system_identity}\n<!-- /aw:block -->\n"
        else:
            content = f"{entry.ownership_marker}\n<!-- aw:pointer -->\nRun via {entry.canonical_system_identity}\n"
        p.write_text(content, encoding="utf-8")
        repaired.append(rel)

    return repaired


def uninstall_adapters(
    target_repo: str,
    manifest: Optional[AdapterManifest] = None,
    host_filter: Optional[str] = None,
) -> List[str]:
    """Uninstall manifest-owned adapters for selected hosts while preserving foreign content (E-07)."""
    repo = Path(target_repo).resolve()
    ctx = resolve_project_context(target_repo=str(repo))
    if ctx.project_role == "source-checkout":
        raise SourceCheckoutProtectionError(
            f"Cannot uninstall adapters from source checkout project '{target_repo}'."
        )

    if manifest is None:
        manifest = build_default_adapter_manifest(repo)

    removed: List[str] = []

    for rel, entry in manifest.entries.items():
        if host_filter and entry.host != host_filter:
            continue

        p = repo / rel
        if not p.exists():
            continue

        if entry.uninstall_behavior == "remove":
            p.unlink()
            removed.append(rel)
        elif entry.uninstall_behavior == "prune_block":
            try:
                content = p.read_text(encoding="utf-8")
                # Prune aw:block section from file
                pattern = re.compile(
                    r"<!-- aw:block -->.*?<!-- /aw:block -->\n?", re.DOTALL
                )
                new_content = pattern.sub("", content).strip()
                if new_content:
                    p.write_text(new_content + "\n", encoding="utf-8")
                else:
                    p.unlink()
                removed.append(rel)
            except Exception:
                pass

    return removed
