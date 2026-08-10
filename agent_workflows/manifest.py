"""Install ownership manifest for agent-workflows (IPD 20260723-1100-01).

A small, self-contained, per-file ownership ledger the installer writes into a target
repo. For every file agent-workflows installs it records the path, a logical id, the file
kind/host, and the sha256 of the content the installer LAST WROTE. The installer uses that
recorded hash to answer "did the USER change this file?" by comparing the on-disk content
to OUR last-installed hash, NOT to the newly-generated expected content. That distinction
is the whole point: a mere version-to-version FORMAT change in our own generated output
(e.g. adding an ``argument-hint`` line) must NOT be mistaken for a user modification.

Design constraints (from the IPD):
- SELF-CONTAINED: the manifest carries all provenance it needs; it never relies on git.
- PATH-PARAMETERIZED: the manifest location is supplied by the caller (default
  ``.agents/agent-workflows/managed-sections.json``); nothing here hardcodes it.
- ATOMIC writes: temp file in the same directory + ``os.replace`` (mirrors config.save),
  so a crash mid-write cannot corrupt an existing manifest.
- STABLE hashing: every hash is taken over a single normalization, and that SAME
  normalization is used by the drift comparison in the engine (plan-review PR-002/M13), so
  a file the installer just wrote always matches its own recorded hash.
- Missing manifest == fresh install.

Stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

# Bump only on a breaking schema change; readers tolerate a newer minor by ignoring
# unknown keys and an older one by supplying defaults.
SCHEMA_VERSION = 2

# Default, relative to a target repo root. The location is POLICY, not mechanism: callers
# pass an absolute path; this constant only documents the default the engine uses.
DEFAULT_MANIFEST_RELPATH = ".agents/agent-workflows/managed-sections.json"

INSTALLER_NAME = "agent-workflows"


def normalize_for_hash(text: str) -> str:
    """Normalization used for BOTH manifest hashing and the engine's drift comparison.

    This intentionally mirrors ``engine.strip_description_and_normalize``: normalize line
    endings, strip per-line whitespace, drop empty lines, and drop the front-matter
    ``description:`` line (its wording is cosmetic and legitimately varies). Keeping the
    two in lockstep is the M13 invariant: if the manifest hashed one normalization while
    the drift check compared another, a file we just wrote would fail to match its own
    recorded hash. The engine re-exports / delegates to this helper so there is exactly
    one normalization.
    """

    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower().startswith("description:"):
            continue
        lines.append(stripped)
    return "\n".join(lines)


def hash_content(text: str) -> str:
    """sha256 (hex) of the normalized content. Deterministic across line endings /
    trailing whitespace / description wording."""

    normalized = normalize_for_hash(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass
class FileEntry:
    """One installed file's ownership record.

    ``sha256`` is the hash of the content the installer LAST WROTE (never the prior
    on-disk content; that is the M12 rule enforced by the caller). ``declined`` is the
    per-file decline tombstone: when True the installer must not re-add the file on future
    installs (the interactive per-directive consent prompt is a later IPD; this is the
    persisted field it will set).
    """

    path: str
    sha256: str
    kind: str = "file"
    host: str = ""
    logical_id: str = ""
    declined: bool = False

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "kind": self.kind,
            "host": self.host,
            "logical_id": self.logical_id,
            "sha256": self.sha256,
        }
        if self.declined:
            out["declined"] = True
        return out

    @classmethod
    def from_dict(cls, path: str, raw: Dict[str, Any]) -> "FileEntry":
        return cls(
            path=path,
            sha256=str(raw.get("sha256", "")),
            kind=str(raw.get("kind", "file")),
            host=str(raw.get("host", "")),
            logical_id=str(raw.get("logical_id", "")),
            declined=bool(raw.get("declined", False)),
        )


@dataclass
class Manifest:
    """The whole ledger. ``files`` is keyed by POSIX-relative path.

    ``managed_sections`` is reserved in the schema for the per-directive sectioned-block
    work (IPD 02); it is round-tripped but not populated here.
    """

    installed_version: str = ""
    installer: str = INSTALLER_NAME
    schema_version: int = SCHEMA_VERSION
    files: Dict[str, FileEntry] = field(default_factory=dict)
    managed_sections: Dict[str, Any] = field(default_factory=dict)

    # --- queries -------------------------------------------------------------

    def get(self, path: str) -> Optional[FileEntry]:
        return self.files.get(path)

    def recorded_hash(self, path: str) -> Optional[str]:
        entry = self.files.get(path)
        return entry.sha256 if entry is not None else None

    def is_declined(self, path: str) -> bool:
        entry = self.files.get(path)
        return bool(entry and entry.declined)

    def matches_recorded(self, path: str, content: str) -> bool:
        """True if ``content`` hashes to the recorded hash for ``path`` (i.e. this is
        OUR file, unchanged by the user). False when there is no record (unknown file) or
        the hash differs (real user drift)."""

        recorded = self.recorded_hash(path)
        if recorded is None:
            return False
        return recorded == hash_content(content)

    # --- mutations -----------------------------------------------------------

    def record(
        self,
        path: str,
        content: str,
        *,
        kind: str = "file",
        host: str = "",
        logical_id: str = "",
    ) -> None:
        """Record the hash of the content JUST WRITTEN for ``path`` (the M12 rule).

        Preserves an existing decline tombstone for the path (recording a file we wrote
        does not silently un-decline it; callers manage decline explicitly)."""

        prior = self.files.get(path)
        self.files[path] = FileEntry(
            path=path,
            sha256=hash_content(content),
            kind=kind,
            host=host,
            logical_id=logical_id,
            declined=bool(prior.declined) if prior else False,
        )

    def mark_declined(self, path: str, *, kind: str = "file", host: str = "") -> None:
        """Persist a decline tombstone so the file is not re-added on future installs."""

        prior = self.files.get(path)
        self.files[path] = FileEntry(
            path=path,
            sha256=prior.sha256 if prior else "",
            kind=prior.kind if prior else kind,
            host=prior.host if prior else host,
            logical_id=prior.logical_id if prior else "",
            declined=True,
        )

    # --- serialization -------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "installer": self.installer,
            "installed_version": self.installed_version,
            "files": {
                path: entry.to_dict() for path, entry in sorted(self.files.items())
            },
            "managed_sections": self.managed_sections,
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "Manifest":
        files_raw = raw.get("files") or {}
        files: Dict[str, FileEntry] = {}
        if isinstance(files_raw, dict):
            for path, entry_raw in files_raw.items():
                if isinstance(entry_raw, dict):
                    files[str(path)] = FileEntry.from_dict(str(path), entry_raw)
        sections = raw.get("managed_sections")
        return cls(
            installed_version=str(raw.get("installed_version", "")),
            installer=str(raw.get("installer", INSTALLER_NAME)),
            schema_version=int(raw.get("schema_version", SCHEMA_VERSION)),
            files=files,
            managed_sections=sections if isinstance(sections, dict) else {},
        )


def load(path: Path) -> Manifest:
    """Read the manifest at ``path``. A missing or unreadable/corrupt manifest yields an
    empty manifest (fresh install), never an exception: absence must be the safe,
    fresh-install case, not a crash."""

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Manifest()
    if not isinstance(raw, dict):
        return Manifest()
    return Manifest.from_dict(raw)


def save(manifest: Manifest, path: Path) -> Path:
    """Atomically write ``manifest`` to ``path`` (temp + os.replace, mirroring
    config.save). Creates the parent directory as needed. Returns the path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n"

    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=".managed-sections.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp_name, str(path))
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return path
