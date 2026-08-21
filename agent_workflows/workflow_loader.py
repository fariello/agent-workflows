"""Strict canonical-workflow loader -> normalized intermediate representation (IR).

awoptimize Order 01 (`nmwy3m`) E-03. This is the build-time loader that turns a canonical workflow
SOURCE package (E-02 layout, YAML entry) into a validated, normalized IR that the compiler (E-04)
consumes. It composes the two prior pieces:

  * `workflow_source` (E-02): resolve/parse the package, compute the semantic digest, refuse symlinks.
  * `workflow_schema` (E-01): validate the parsed entry against the typed contract.

It adds the loader-specific obligations from the plan:

  * resolve every resource the entry references and prove CLOSURE (each exists, inside the package);
  * reject path traversal / symlink escape (delegated to E-02's guard, surfaced as a load finding);
  * detect duplicate ids and dependency cycles (delegated to E-01, surfaced here);
  * PRESERVE SOURCE LOCATIONS (which package + which file each resource came from);
  * FAIL CLOSED: on any finding, return findings and NO IR. A partial IR is never produced, so a
    downstream compiler can trust that a returned IR is fully valid and closed.

Determinism + safety: the loader reads files but never writes, never calls a model or the network,
and follows no symlinks. The only third-party touch is the build-time-only YAML parse inside
`workflow_source.parse_entry` (D139); importing this module adds no runtime dependency.

The IR is a plain, JSON-serializable dict so it is inspectable and can itself be hashed/serialized
deterministically by the compiler:

    {
      "ir_version": 1,
      "digest": "<package semantic digest>",
      "source_root": "<abs path, informational>",
      "workflow": { ...the schema-validated entry mapping... },
      "resources": { "<rel-path>": {"path": "<rel-path>", "sha256": "<hash>", "text": "<content>"} },
    }
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from agent_workflows import workflow_schema as _schema
from agent_workflows import workflow_source as _source

IR_VERSION = 1


class LoadResult(NamedTuple):
    """Outcome of loading a package. Exactly one of ``ir`` / non-empty ``findings`` is meaningful:
    on success ``ok`` is True and ``ir`` is the normalized IR; on failure ``ok`` is False, ``ir`` is
    None, and ``findings`` explains every problem (fail closed, no partial IR)."""

    ok: bool
    ir: Optional[Dict[str, Any]]
    findings: Tuple[_schema.Finding, ...]


def load_package(root: Any) -> LoadResult:
    """Load and validate one canonical workflow package into a normalized IR (fail closed).

    Never raises for an invalid or unsafe package: structural/safety problems become findings. Only a
    truly unexpected condition would propagate. Returns a :class:`LoadResult`.
    """

    findings: List[_schema.Finding] = []

    # 1) Resolve the package + refuse symlink escape BEFORE reading anything (E-02 safety guard).
    try:
        paths = _source.resolve_package(root)
    except _source.SourceError as exc:
        return LoadResult(
            False, None, (_schema.Finding("WF-L001", str(root), str(exc)),)
        )
    try:
        _source.assert_no_symlink_escape(paths.root)
    except _source.SourceError as exc:
        return LoadResult(
            False, None, (_schema.Finding("WF-L002", str(paths.root), str(exc)),)
        )

    # 2) Parse the entry file (build-time YAML). A parse error fails closed with location.
    try:
        entry = _source.parse_entry(paths.root)
    except _source.SourceError as exc:
        return LoadResult(
            False, None, (_schema.Finding("WF-L003", _source.ENTRY_FILENAME, str(exc)),)
        )

    # 3) Validate the entry against the typed schema (E-01). Prefix each finding's location with the
    #    package so a multi-package build reports exact provenance.
    result = _schema.validate_workflow(entry)
    wf_id = entry.get("id") if isinstance(entry, dict) else None
    prefix = (
        "{0}:{1}".format(wf_id, _source.ENTRY_FILENAME)
        if isinstance(wf_id, str)
        else _source.ENTRY_FILENAME
    )
    for f in result.findings:
        findings.append(
            _schema.Finding(
                f.code,
                "{0}#{1}".format(prefix, f.where) if f.where else prefix,
                f.message,
            )
        )

    # 4) Resolve referenced resources and prove closure. Each must exist, be a regular file inside the
    #    package, not be generated/cruft, and not escape via traversal. Record source locations.
    resources: Dict[str, Any] = {}
    for rel in _source.referenced_resources(entry):
        loc = "{0}#resources:{1}".format(prefix, rel)
        # Reject absolute paths and any traversal component up front (do not touch the filesystem).
        rel_path = Path(rel)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            findings.append(
                _schema.Finding(
                    "WF-L010", loc, "resource path escapes the package: {0}".format(rel)
                )
            )
            continue
        if _source.is_ignored_rel(rel_path.parts):
            findings.append(
                _schema.Finding(
                    "WF-L011",
                    loc,
                    "resource points at a generated/cruft path: {0}".format(rel),
                )
            )
            continue
        target = paths.root / rel_path
        if target.is_symlink():
            findings.append(
                _schema.Finding(
                    "WF-L012", loc, "resource is a symlink (forbidden): {0}".format(rel)
                )
            )
            continue
        if not target.is_file():
            findings.append(
                _schema.Finding(
                    "WF-L013",
                    loc,
                    "referenced resource does not exist: {0}".format(rel),
                )
            )
            continue
        # Defense in depth: confirm the resolved path stays within the package root.
        try:
            target.resolve().relative_to(paths.root.resolve())
        except ValueError:
            findings.append(
                _schema.Finding(
                    "WF-L014",
                    loc,
                    "resource resolves outside the package: {0}".format(rel),
                )
            )
            continue
        text = target.read_text(encoding="utf-8")
        resources[rel] = {
            "path": rel,
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "text": text,
        }

    # 5) Fail closed: any finding means NO IR.
    if findings:
        return LoadResult(False, None, tuple(findings))

    # 6) Build the normalized IR. The package digest binds the IR to exact source bytes.
    digest = _source.semantic_digest(paths.root)
    ir: Dict[str, Any] = {
        "ir_version": IR_VERSION,
        "digest": digest,
        "source_root": str(paths.root),
        "workflow": entry,
        "resources": resources,
    }
    return LoadResult(True, ir, ())
