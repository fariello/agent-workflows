"""Pure detector for stale Python-source line offset citations (IPD pyuw4v, backlog 7jl2bf).

Answers whether a `<file>.py:<line>[-<line>]` citation in Python comments or docstrings
resolves to an existing file and valid line offset inside the repository, or lands in an
invalid position (past end of file, on a blank line, or on a punctuation-only line).

PURE AND CWD-INDEPENDENT: takes repo_root and paths explicitly, never imports check_engine.
"""

from __future__ import annotations

import io
import os
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Union

from agent_workflows import artifact_core, spec_citations


@dataclass(frozen=True)
class StaleSourceOffset:
    """One stale Python source offset citation finding."""

    file: Path
    line: int
    cited: str
    target: Path
    offset: int
    validity: str

    @property
    def is_valid(self) -> bool:
        return self.validity == "valid"


_CITATION_RE = re.compile(r"\b([A-Za-z_][\w/.]*\.py):(\d+)(?:-(\d+))?\b")
_HEX_TOKEN_RE = re.compile(r"\b(?=[0-9a-f]*[0-9])(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b")
_PUNCT_CHARS = set("()[]{}:;,")


def stale_source_offsets(
    repo_root: Union[str, Path],
    paths: Iterable[Union[str, Path]],
) -> List[StaleSourceOffset]:
    """Pure detector returning stale source offset citations in the given paths."""
    repo_root = Path(repo_root)
    ignored_dirs = artifact_core.get_ignored_dirs(repo_root)

    # (a) TARGET INDEX: walk repo_root for .py files skipping artifact_core.is_ignored_path
    by_rel: Dict[str, Path] = {}
    by_basename: Dict[str, List[Path]] = {}

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [
            d
            for d in dirs
            if not artifact_core.is_ignored_path(
                Path(root) / d, repo_root, ignored_dirs
            )
        ]
        for f in sorted(files):
            if f.endswith(".py"):
                p = Path(root) / f
                if not artifact_core.is_ignored_path(p, repo_root, ignored_dirs):
                    try:
                        rel = p.relative_to(repo_root).as_posix()
                    except ValueError:
                        rel = p.as_posix()
                    by_rel[rel] = p
                    by_basename.setdefault(f, []).append(p)

    # Collect target files to scan under paths
    target_files: List[Path] = []
    seen_target_files: Set[Path] = set()
    for p in paths:
        path_obj = Path(p)
        if not path_obj.is_absolute():
            path_obj = repo_root / path_obj
        if path_obj.is_dir():
            for root, dirs, files in os.walk(path_obj):
                dirs[:] = [
                    d
                    for d in dirs
                    if not artifact_core.is_ignored_path(
                        Path(root) / d, repo_root, ignored_dirs
                    )
                ]
                for f in sorted(files):
                    if f.endswith(".py"):
                        fpath = Path(root) / f
                        if not artifact_core.is_ignored_path(
                            fpath, repo_root, ignored_dirs
                        ):
                            if fpath not in seen_target_files:
                                seen_target_files.add(fpath)
                                target_files.append(fpath)
        elif path_obj.is_file() and path_obj.suffix == ".py":
            if not artifact_core.is_ignored_path(path_obj, repo_root, ignored_dirs):
                if path_obj not in seen_target_files:
                    seen_target_files.add(path_obj)
                    target_files.append(path_obj)

    findings: List[StaleSourceOffset] = []
    lines_cache: Dict[Path, List[str]] = {}

    # (b) SCAN: examine COMMENT tokens and DOCSTRING STRING tokens
    for fpath in target_files:
        try:
            raw_text = fpath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if not _CITATION_RE.search(raw_text):
            continue

        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(raw_text).readline))
        except Exception:
            continue

        flines = raw_text.splitlines()
        prev_sig_type: Optional[int] = None

        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                lno = tok.start[0]
                pline = flines[lno - 1] if 0 < lno <= len(flines) else tok.line
                if not _HEX_TOKEN_RE.search(pline):
                    _scan_citations_on_line(
                        tok.string,
                        fpath,
                        lno,
                        by_rel,
                        by_basename,
                        lines_cache,
                        findings,
                    )
                continue

            if tok.type in (tokenize.ENCODING, tokenize.NL):
                continue

            if tok.type == tokenize.STRING:
                is_docstring = prev_sig_type is None or prev_sig_type in (
                    tokenize.NEWLINE,
                    tokenize.INDENT,
                    tokenize.DEDENT,
                )
                prev_sig_type = tokenize.STRING
                if is_docstring:
                    start_lno = tok.start[0]
                    for idx, line_str in enumerate(tok.string.splitlines()):
                        lno = start_lno + idx
                        pline = flines[lno - 1] if 0 < lno <= len(flines) else line_str
                        if not _HEX_TOKEN_RE.search(pline):
                            _scan_citations_on_line(
                                line_str,
                                fpath,
                                lno,
                                by_rel,
                                by_basename,
                                lines_cache,
                                findings,
                            )
                continue

            prev_sig_type = tok.type

    findings.sort(key=lambda x: (x.file, x.line, x.offset))
    return findings


def _scan_citations_on_line(
    text: str,
    citing_file: Path,
    lno: int,
    by_rel: Dict[str, Path],
    by_basename: Dict[str, List[Path]],
    lines_cache: Dict[Path, List[str]],
    findings: List[StaleSourceOffset],
) -> None:
    for m in _CITATION_RE.finditer(text):
        cited_file = m.group(1)
        offset = int(m.group(2))
        end_offset = int(m.group(3)) if m.group(3) is not None else None

        # (c) RESOLVE
        target: Optional[Path] = None
        if cited_file in by_rel:
            target = by_rel[cited_file]
        else:
            basename = Path(cited_file).name
            sibling = citing_file.parent / basename
            for cand in by_basename.get(basename, []):
                if cand.resolve() == sibling.resolve():
                    target = cand
                    break
            if target is None and len(by_basename.get(basename, [])) == 1:
                target = by_basename[basename][0]

        if target is None:
            continue

        # (d) VERDICT
        if target not in lines_cache:
            try:
                lines_cache[target] = target.read_text(
                    encoding="utf-8", errors="ignore"
                ).splitlines()
            except OSError:
                continue
        lines = lines_cache[target]

        _, start_validity = spec_citations._resolve_offset(
            lines, [], [False] * (len(lines) + 1), offset
        )
        if start_validity in ("past_eof", "blank_line"):
            validity = start_validity
        elif start_validity == "valid":
            target_line = lines[offset - 1].strip()
            if target_line and all(c in _PUNCT_CHARS for c in target_line):
                validity = "punct_only"
            elif end_offset is not None and end_offset > len(lines):
                validity = "past_eof"
            else:
                continue
        else:
            continue

        findings.append(
            StaleSourceOffset(
                file=citing_file,
                line=lno,
                cited=m.group(0),
                target=target,
                offset=offset,
                validity=validity,
            )
        )
