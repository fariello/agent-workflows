"""Numbered metadata migration chain, metadata_schema stamp, and read-path gate.

Implements spec 4sd62s Section 5.1 (migration chain and ``metadata_schema`` stamp) and Section 5.3
(every metadata read refuses an unmigrated repository).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Callable, List, Optional, Set, Tuple, Union

from agent_workflows import project_context
from agent_workflows import project_schema


class MetadataSchemaError(RuntimeError):
    """Raised when a repository's metadata schema lags behind CURRENT_METADATA_SCHEMA.

    Inherits from ``RuntimeError`` rather than ``ValueError`` so ``meta_cli._collect`` does not
    misclassify a repository-wide unmigrated-schema refusal as a per-record ``invalid-record``
    defect.
    """


@dataclass(frozen=True)
class Migration:
    """One step in the numbered metadata migration chain."""

    number: int
    name: str
    target_schema: int
    _is_pending: Callable[[Union[str, Path]], bool] = field(repr=False, compare=False)
    _run: Callable[..., Any] = field(repr=False, compare=False)

    def is_pending(self, repo: Union[str, Path]) -> bool:
        """Return True if this migration has not yet been applied to ``repo``."""
        return self._is_pending(repo)

    def run(
        self,
        repo: Union[str, Path],
        *,
        apply: bool = False,
        force: bool = False,
        force_worktree: bool = False,
        describer: Optional[Any] = None,
    ) -> Any:
        """Execute (or dry-run when ``apply=False``) this migration against ``repo``."""
        return self._run(
            repo,
            apply=apply,
            force=force,
            force_worktree=force_worktree,
            describer=describer,
        )


CURRENT_METADATA_SCHEMA = 1

_WORKFLOW_HISTORY_RE = re.compile(r"^## Workflow history\s*$", re.MULTILINE)

_EXCLUDED_FILENAMES = frozenset(
    {
        "README.md",
        "STATUS.md",
        "conformance-results-template.md",
        "20260712-0156-14-chatgpt-modular-report-template.md",
    }
)
_EXCLUDED_DIRNAMES = frozenset({"comms", "prompt-library"})
# Non-record subdirectories under legacy `.agents/` (host skill packages installed by `aw install`,
# legacy system workflows, inbox, run records, and runtime state).
_AGENTS_NON_RECORD_TOP_DIRS = frozenset({"workflows", "inbox", "runs", "state"})
_AGENTS_NON_RECORD_TOP_FILES = frozenset({"AGENTS.md"})


def _agents_skills_top_dir() -> str:
    """Return the top-level directory under `.agents/` used for installed skills."""
    from agent_workflows import engine as _engine

    skills_posix = _engine.SKILLS_DIR.replace("\\", "/").strip("/")
    if skills_posix == ".agents" or skills_posix.startswith(".agents/"):
        rest = skills_posix.removeprefix(".agents").strip("/")
        if rest:
            return rest.split("/", 1)[0]
    return "skills"


def _validate_metadata_schema_value(value: Any) -> int:
    """Validate that ``metadata_schema`` is a non-boolean integer >= 1."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"Invalid metadata_schema {value!r}: expected an integer >= 1")
    return value


def _resolve_project_json(
    repo: Union[str, Path],
    *,
    config_project: Optional[Union[str, Path]] = None,
) -> Path:
    """Resolve the portable ``project.json`` path for ``repo``."""
    if config_project is not None:
        return Path(config_project)
    return project_context.project_config_dir(repo) / "project.json"


def read_metadata_schema(
    repo: Union[str, Path],
    *,
    config_project: Optional[Union[str, Path]] = None,
) -> Optional[int]:
    """Read ``metadata_schema`` from ``repo``'s resolved ``project.json``, or ``None`` if absent."""
    proj_path = _resolve_project_json(repo, config_project=config_project)
    if not proj_path.exists():
        return None
    raw = json.loads(proj_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(
            f"Expected JSON object in {proj_path}, got {type(raw).__name__}"
        )
    if "metadata_schema" not in raw or raw["metadata_schema"] is None:
        return None
    return _validate_metadata_schema_value(raw["metadata_schema"])


def write_metadata_schema(
    repo: Union[str, Path],
    value: int,
    *,
    config_project: Optional[Union[str, Path]] = None,
) -> Path:
    """Atomically write ``metadata_schema: value`` into ``repo``'s resolved ``project.json``."""
    validated = _validate_metadata_schema_value(value)
    proj_path = _resolve_project_json(repo, config_project=config_project)
    proj_path.parent.mkdir(parents=True, exist_ok=True)

    if proj_path.exists():
        raw = json.loads(proj_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(
                f"Expected JSON object in {proj_path}, got {type(raw).__name__}"
            )
        data: dict[str, Any] = dict(raw)
    else:
        default_schema_version = getattr(
            project_schema,
            "SCHEMA_VERSION",
            project_schema.ProjectPolicySchema().schema_version,
        )
        data = {"schema_version": default_schema_version}

    data["metadata_schema"] = validated
    payload = json.dumps(data, indent=2) + "\n"

    fd, tmp_name = tempfile.mkstemp(
        dir=str(proj_path.parent),
        prefix=f".tmp_{proj_path.name}_",
        suffix=".tmp",
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, proj_path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise
    return proj_path


def _is_v2_mirror_text(text: str, filename: str) -> bool:
    """Return True if ``text`` matches one of the v2 mirror formats."""
    from agent_workflows import artifact_meta

    parsers: List[Callable[[str], Any]] = [
        artifact_meta.parse_artifact_mirror,
        artifact_meta.parse_review_mirror,
        artifact_meta.parse_staged_prompt_mirror,
    ]
    if filename.endswith(".walkthrough.md"):
        parsers.append(artifact_meta.parse_walkthrough_mirror)

    for parser in parsers:
        try:
            parser(text)
            return True
        except ValueError:
            continue
    return False


def repo_has_legacy_records(
    repo: Union[str, Path],
    *,
    records_root: Optional[Union[str, Path]] = None,
) -> bool:
    """Return True if ``repo`` holds any unmigrated legacy `.md` records."""
    repo_path = Path(repo)
    primary_root = (
        Path(records_root)
        if records_root is not None
        else project_context.project_records_dir(repo_path)
    )
    agents_root = repo_path / ".agents"
    agents_resolved: Optional[Path] = (
        agents_root.resolve() if agents_root.is_dir() else None
    )

    candidate_roots: List[Tuple[Path, bool]] = []
    seen_roots: Set[Path] = set()
    for candidate in (primary_root, agents_root):
        if not candidate.is_dir():
            continue
        resolved = candidate.resolve()
        if resolved in seen_roots:
            continue
        seen_roots.add(resolved)
        is_agents = agents_resolved is not None and resolved == agents_resolved
        candidate_roots.append((candidate, is_agents))

    skills_top_dir = _agents_skills_top_dir()

    for root_dir, is_agents in candidate_roots:
        for cur_dir, dirs, files in os.walk(root_dir):
            cur_path = Path(cur_dir)
            is_root_level = cur_path == root_dir
            pruned_dirs: List[str] = []
            for dname in dirs:
                if dname in _EXCLUDED_DIRNAMES or dname.endswith(".data"):
                    continue
                if (
                    is_agents
                    and is_root_level
                    and (
                        dname == skills_top_dir or dname in _AGENTS_NON_RECORD_TOP_DIRS
                    )
                ):
                    continue
                pruned_dirs.append(dname)
            dirs[:] = pruned_dirs

            for fname in files:
                if not fname.endswith(".md"):
                    continue
                if fname in _EXCLUDED_FILENAMES or fname.startswith("INDEX."):
                    continue
                if (
                    is_agents
                    and is_root_level
                    and fname in _AGENTS_NON_RECORD_TOP_FILES
                ):
                    continue
                if is_agents:
                    return True
                text = (cur_path / fname).read_text(encoding="utf-8", errors="replace")
                if _WORKFLOW_HISTORY_RE.search(text):
                    return True
                if not _is_v2_mirror_text(text, fname):
                    return True

    return False


def require_current_schema(
    repo: Union[str, Path],
    *,
    config_project: Optional[Union[str, Path]] = None,
    records_root: Optional[Union[str, Path]] = None,
) -> None:
    """Raise MetadataSchemaError when ``repo``'s effective metadata schema is behind current."""
    stamp = read_metadata_schema(repo, config_project=config_project)
    if stamp is not None and stamp >= CURRENT_METADATA_SCHEMA:
        return
    if stamp is None and CURRENT_METADATA_SCHEMA <= 1:
        return

    effective = (
        stamp
        if stamp is not None
        else (
            1
            if repo_has_legacy_records(repo, records_root=records_root)
            else CURRENT_METADATA_SCHEMA
        )
    )
    if effective < CURRENT_METADATA_SCHEMA:
        raise MetadataSchemaError(
            f"Repository metadata schema is {effective} (current is {CURRENT_METADATA_SCHEMA}); "
            "run `aw migrate metadata` before reading metadata."
        )


def _m0001_is_pending(repo: Union[str, Path]) -> bool:
    stamp = read_metadata_schema(repo)
    effective = (
        stamp if stamp is not None else (1 if repo_has_legacy_records(repo) else 2)
    )
    return effective < 2


def _m0001_run(
    repo: Union[str, Path],
    *,
    apply: bool = False,
    force: bool = False,
    force_worktree: bool = False,
    describer: Optional[Any] = None,
) -> Any:
    from agent_workflows.migrations import m0001_metadata_v2

    return m0001_metadata_v2.run(
        repo,
        apply=apply,
        force=force,
        force_worktree=force_worktree,
        describer=describer,
    )


MIGRATIONS: Tuple[Migration, ...] = (
    Migration(
        number=1,
        name="metadata-v2",
        target_schema=2,
        _is_pending=_m0001_is_pending,
        _run=_m0001_run,
    ),
)


def pending_migrations(repo: Union[str, Path]) -> List[Migration]:
    """Return MIGRATIONS entries in chain order that are pending and within CURRENT_METADATA_SCHEMA."""
    return [
        m
        for m in MIGRATIONS
        if m.target_schema <= CURRENT_METADATA_SCHEMA and m.is_pending(repo)
    ]
