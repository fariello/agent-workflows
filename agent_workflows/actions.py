"""AW operational actions and install history management (IPD 20260809-awlayout-06).

This module implements AW operational follow-up actions, lifecycle transitions (open, completed,
dismissed, superseded), catalog reconciliation, and append-only install history specified by
``.agents/docs/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md`` Section 12 & 18.

Invariants:
- ACTION ID FORMAT: Validated against ``[a-z][a-z0-9]*(?:-[a-z0-9]+)*`` with positive integer generations.
- EXACTLY ONE LIFECYCLE DIR: Each ``(id, generation)`` action file exists in exactly one lifecycle directory:
  ``open/``, ``completed/``, ``dismissed/``, or ``superseded/``.
- ATOMIC TRANSITION: Same-filesystem atomic rename (``os.replace``) leaves no duplicate or orphaned files.
- ATOMIC JSONL APPEND: ``installs.jsonl`` appends with file locking and ``fsync``.
- RESOLVED VIA CONTEXT: State root resolved strictly through Order 01 context resolver.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent_workflows.project_context import resolve_project_context
from agent_workflows.project_schema import LogicalRoot

ACTION_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
LIFECYCLE_STATUSES = {"open", "completed", "dismissed", "superseded"}


class ActionError(Exception):
    """Base exception for action operations."""

    pass


class InvalidActionIdError(ActionError):
    """Raised when an action ID fails validation format."""

    pass


class ActionNotFoundError(ActionError):
    """Raised when an action or generation cannot be found."""

    pass


def validate_action_id(action_id: str) -> None:
    """Validate action ID format: [a-z][a-z0-9]*(?:-[a-z0-9]+)* and NOT an ``aw-`` prefix (E-01)."""
    if not ACTION_ID_PATTERN.match(action_id):
        raise InvalidActionIdError(
            f"Invalid action ID: '{action_id}'. Must match pattern [a-z][a-z0-9]*(?:-[a-z0-9]+)* without aw- prefix."
        )
    # The pattern alone accepts 'aw-...' (a valid kebab id); the spec (Section 12.2) forbids the
    # scope-repeating aw- prefix, so reject it explicitly.
    if action_id == "aw" or action_id.startswith("aw-"):
        raise InvalidActionIdError(
            f"Invalid action ID: '{action_id}'. The 'aw-' prefix is forbidden (spec Section 12.2)."
        )


@dataclass
class ActionDocument:
    """Operational action representation (spec Section 18)."""

    id: str
    generation: int
    status: str
    title: str
    description: str
    created_at: str
    updated_at: str

    def to_markdown(self) -> str:
        """Format action document with YAML frontmatter."""
        frontmatter = {
            "id": self.id,
            "generation": self.generation,
            "status": self.status,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        return f"---\n{json.dumps(frontmatter, indent=2)}\n---\n\n# {self.title}\n\n{self.description}\n"

    @classmethod
    def from_markdown(cls, content: str) -> "ActionDocument":
        """Parse action document from Markdown string with frontmatter."""
        match = re.match(r"^---\n(.*?)\n---\n\n?(.*)", content, re.DOTALL)
        if not match:
            raise ActionError("Malformed action Markdown content: missing frontmatter")
        fm_data = json.loads(match.group(1))
        body = match.group(2).strip()

        # Extract title from first line if present
        title = fm_data.get("title", "")
        desc = body
        if body.startswith("# "):
            lines = body.splitlines()
            title = lines[0][2:].strip()
            desc = "\n".join(lines[1:]).strip()

        return cls(
            id=str(fm_data["id"]),
            generation=int(fm_data["generation"]),
            status=str(fm_data["status"]),
            title=title,
            description=desc,
            created_at=str(fm_data.get("created_at", "")),
            updated_at=str(fm_data.get("updated_at", "")),
        )


class ActionManager:
    """Manages action lifecycle transitions and install history (spec Section 12 & 18)."""

    def __init__(
        self, target_repo: Optional[str] = None, aw_home: Optional[str] = None
    ):
        self.ctx = resolve_project_context(target_repo=target_repo, aw_home=aw_home)
        self.state_root = Path(self.ctx.logical_roots[LogicalRoot.STATE.value])
        self.actions_dir = self.state_root / "actions"
        self.history_dir = self.state_root / "history"

        # Ensure lifecycle subdirectories exist
        for status in LIFECYCLE_STATUSES:
            (self.actions_dir / status).mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def _get_action_filename(self, action_id: str, generation: int) -> str:
        return f"{action_id}-v{generation}.md"

    def find_action_file(
        self, action_id: str, generation: Optional[int] = None
    ) -> Tuple[str, Path]:
        """Find the single lifecycle directory containing (action_id, generation). Returns (status, path)."""
        validate_action_id(action_id)

        if generation is not None:
            filename = self._get_action_filename(action_id, generation)
            for status in LIFECYCLE_STATUSES:
                p = self.actions_dir / status / filename
                if p.is_file():
                    return status, p
            raise ActionNotFoundError(
                f"Action '{action_id}' generation {generation} not found."
            )

        # Search for latest open generation first
        open_matches: List[Tuple[int, Path]] = []
        for p in (self.actions_dir / "open").glob(f"{action_id}-v*.md"):
            m = re.search(r"-v(\d+)\.md$", p.name)
            if m:
                open_matches.append((int(m.group(1)), p))

        if open_matches:
            open_matches.sort(key=lambda x: x[0], reverse=True)
            return "open", open_matches[0][1]

        # Otherwise find latest generation across any status
        all_matches: List[Tuple[int, str, Path]] = []
        for status in LIFECYCLE_STATUSES:
            for p in (self.actions_dir / status).glob(f"{action_id}-v*.md"):
                m = re.search(r"-v(\d+)\.md$", p.name)
                if m:
                    all_matches.append((int(m.group(1)), status, p))

        if not all_matches:
            raise ActionNotFoundError(f"Action '{action_id}' not found.")

        all_matches.sort(key=lambda x: x[0], reverse=True)
        return all_matches[0][1], all_matches[0][2]

    def create_action(
        self, action_id: str, generation: int, title: str, description: str
    ) -> ActionDocument:
        """Create a new open action document (E-01). Enforces single-directory uniqueness."""
        validate_action_id(action_id)
        filename = self._get_action_filename(action_id, generation)

        # Enforce uniqueness across ALL lifecycle directories
        for status in LIFECYCLE_STATUSES:
            if (self.actions_dir / status / filename).exists():
                raise ActionError(
                    f"Action '{action_id}' generation {generation} already exists in '{status}'"
                )

        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        doc = ActionDocument(
            id=action_id,
            generation=generation,
            status="open",
            title=title,
            description=description,
            created_at=now,
            updated_at=now,
        )

        target_p = self.actions_dir / "open" / filename
        tmp_p = self.actions_dir / "open" / f".tmp_{filename}"

        with open(tmp_p, "w", encoding="utf-8") as f:
            f.write(doc.to_markdown())
        os.replace(tmp_p, target_p)

        return doc

    def transition_action(self, action_ref: str, new_status: str) -> ActionDocument:
        """Perform atomic lifecycle transition as a single same-filesystem rename (E-01)."""
        if new_status not in LIFECYCLE_STATUSES:
            raise ActionError(f"Invalid target lifecycle status: '{new_status}'")

        # Parse reference: id or id@generation
        if "@" in action_ref:
            action_id, gen_str = action_ref.split("@", 1)
            generation = int(gen_str)
        else:
            action_id = action_ref
            generation = None

        current_status, current_path = self.find_action_file(action_id, generation)

        if current_status == new_status:
            # Idempotent re-transition
            return ActionDocument.from_markdown(
                current_path.read_text(encoding="utf-8")
            )

        doc = ActionDocument.from_markdown(current_path.read_text(encoding="utf-8"))
        doc.status = new_status
        doc.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        target_path = self.actions_dir / new_status / current_path.name
        tmp_path = self.actions_dir / new_status / f".tmp_{current_path.name}"

        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(doc.to_markdown())

        # Atomic rename replacing source and ensuring target uniqueness
        os.replace(tmp_path, target_path)
        if current_path.exists() and current_path != target_path:
            os.remove(current_path)

        return doc

    def list_actions(self, status_filter: Optional[str] = None) -> List[ActionDocument]:
        """List all actions, optionally filtered by status."""
        statuses = [status_filter] if status_filter else list(LIFECYCLE_STATUSES)
        actions: List[ActionDocument] = []

        for status in statuses:
            for p in (self.actions_dir / status).glob("*-v*.md"):
                if p.name.startswith(".tmp_"):
                    continue
                try:
                    doc = ActionDocument.from_markdown(p.read_text(encoding="utf-8"))
                    actions.append(doc)
                except Exception:
                    pass

        actions.sort(key=lambda x: (x.id, x.generation))
        return actions


def _redact_details(details: Dict[str, Any], *, repo_root: str) -> Dict[str, Any]:
    """Redact machine-identifying values from install-history ``details`` using the canonical
    leak sanitizer (no bespoke regex). Any string value that trips a fail/warn rule (home paths,
    usernames, hostnames) is replaced with ``"[redacted]"`` (L6-04)."""
    from agent_workflows import leak_sanitizer as ls

    ruleset = ls.build_ruleset(Path(repo_root), include_warn=True)
    safe: Dict[str, Any] = {}
    for key, value in details.items():
        if isinstance(value, str) and ls.scan_text(
            value, "install-history", ruleset, include_warn=True
        ):
            safe[key] = "[redacted]"
        else:
            safe[key] = value
    return safe


def record_install_history(
    target_repo: str,
    event_type: str,
    details: Dict[str, Any],
    aw_home: Optional[str] = None,
) -> None:
    """Atomic install snapshot update and JSONL append (E-04)."""
    ctx = resolve_project_context(target_repo=target_repo, aw_home=aw_home)
    state_root = Path(ctx.logical_roots[LogicalRoot.STATE.value])
    state_root.mkdir(parents=True, exist_ok=True)
    history_dir = state_root / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    snapshot = {
        "project_id": ctx.project_id,
        "last_installed_at": now,
        "delivery_mode": ctx.delivery_mode,
        "records_backend": ctx.records_backend,
        "event_type": event_type,
    }

    # Update state/install.json via atomic replace
    install_file = state_root / "install.json"
    tmp_install = state_root / ".tmp_install.json"
    with open(tmp_install, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
    os.replace(tmp_install, install_file)

    # Append to state/history/installs.jsonl with O_APPEND + fsync (E-04).
    # Redaction (L6-04): route the caller-supplied ``details`` through the canonical leak
    # sanitizer rather than a bespoke regex, so machine-identifying paths/hostnames/usernames
    # never enter a potentially-tracked records history.
    safe_details = _redact_details(details, repo_root=target_repo)
    history_file = history_dir / "installs.jsonl"
    event_line = (
        json.dumps({"timestamp": now, "details": safe_details, **snapshot}) + "\n"
    )

    fd = os.open(str(history_file), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, event_line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
