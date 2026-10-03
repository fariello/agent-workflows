"""Pure detector for stale spec line-anchor citations (IPD mt54wr, backlog sbh1o1).

Answers whether a spec line-anchor citation in source files resolves to the heading
the citing prose implies or lands in an invalid location (past end of file, in a code
fence, or on a blank line).

PURE AND CWD-INDEPENDENT: takes repo_root and paths explicitly, never imports check_engine.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union

from agent_workflows import specs


@dataclass(frozen=True)
class StaleSpecAnchor:
    """One spec line-anchor citation finding."""

    file: Path
    line: int
    id6: str
    offset: int
    enclosing_heading: str
    validity: str

    @property
    def is_valid(self) -> bool:
        return self.validity == "valid"


SpecAnchorFinding = StaleSpecAnchor
SpecAnchorCitation = StaleSpecAnchor

_ID6_RE = re.compile(r"\b([a-z0-9]{6})\b")


def _spec_headings_and_fences(
    spec_path: Path,
) -> Tuple[List[str], List[Tuple[int, str]], List[bool]]:
    """Parse a spec markdown file into lines, headings, and code-fence booleans."""
    lines = spec_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    headings: List[Tuple[int, str]] = []
    in_fence: List[bool] = [False] * (len(lines) + 1)

    fence_active = False
    fence_marker = None
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            m = s[:3]
            if not fence_active:
                fence_active = True
                fence_marker = m
                in_fence[i] = True
            elif m == fence_marker:
                in_fence[i] = True
                fence_active = False
                fence_marker = None
            else:
                in_fence[i] = fence_active
        else:
            in_fence[i] = fence_active
            if not fence_active and s.startswith("#"):
                headings.append((i, s))

    return lines, headings, in_fence


def _resolve_offset(
    lines: List[str], headings: List[Tuple[int, str]], in_fence: List[bool], offset: int
) -> Tuple[str, str]:
    """Resolve an offset to (enclosing_heading, validity).

    If the offset lands on an invalid position (past EOF, in a code fence, or on a
    blank line), the validity indicates why and enclosing_heading is empty so the
    offset is not attributed to a preceding heading.
    """
    if offset <= 0 or offset > len(lines):
        return "", "past_eof"
    if in_fence[offset]:
        return "", "in_fence"
    line_text = lines[offset - 1].strip()
    if not line_text:
        return "", "blank_line"

    last_h = ""
    for lno, h in headings:
        if lno <= offset:
            last_h = h
        else:
            break
    return last_h, "valid"


def _extract_named_section(line: str) -> Optional[str]:
    """Extract a named section identifier like '2.1' from the citing line."""
    m = re.search(
        r"(?:section|sec|spec|§)\s+([0-9]+(?:\.[0-9]+)*)", line, re.IGNORECASE
    )
    if m:
        return m.group(1)
    m2 = re.search(r"\b([0-9]+\.[0-9]+(?:\.[0-9]+)*)\b", line)
    if m2:
        return m2.group(1)
    return None


def _heading_matches_section(heading: str, section: str) -> bool:
    """Test whether heading encloses or names the given section identifier."""
    pattern = r"(?:^#+\s*|\bsection\s+|\b)" + re.escape(section) + r"(?:\b|[.\s])"
    return bool(re.search(pattern, heading, re.IGNORECASE))


def _heading_title(heading: str) -> str:
    """Extract the title part of a markdown heading, stripping # and section numbers."""
    s = re.sub(r"^#+\s*", "", heading).strip()
    s = re.sub(r"^[0-9]+(?:\.[0-9]+)*\s*", "", s).strip()
    return s


def _find_anchors_on_line(
    line: str, context_id6: Optional[str], known_specs: Dict
) -> List[Tuple[str, int]]:
    """Find all (spec_id6, offset) line anchors cited on line."""
    res: List[Tuple[str, int]] = []
    # 1. Direct id6 attribution:
    for id6 in known_specs:
        if id6 in line:
            for m in re.finditer(r"(?:`?" + id6 + r"`?)[^:\n]{0,60}?:`?(\d+)\b", line):
                res.append((id6, int(m.group(1))))
            for m in re.finditer(r":`?(\d+)\b[^:\n]{0,60}?(?:`?" + id6 + r"`?)", line):
                tup = (id6, int(m.group(1)))
                if tup not in res:
                    res.append(tup)

    # 2. Bare backtick `:\d+` or bare spec : \d+
    if context_id6 and context_id6 in known_specs:
        for m in re.finditer(r"`:\s*(\d+)`", line):
            off = int(m.group(1))
            tup = (context_id6, off)
            if tup not in res:
                res.append(tup)
        for m in re.finditer(
            r"\bspec(?:\s+[0-9]+(?:\.[0-9]+)*)?\s+:(\d+)\b", line, re.IGNORECASE
        ):
            off = int(m.group(1))
            tup = (context_id6, off)
            if tup not in res:
                res.append(tup)
    return res


def stale_spec_anchors(
    repo_root: Union[str, Path], paths: Iterable[Union[str, Path]]
) -> List[StaleSpecAnchor]:
    """Pure detector returning stale spec line-anchor citations in the given paths."""
    repo_root = Path(repo_root)
    spec_files = specs._spec_files(repo_root)
    spec_map: Dict[str, Path] = {}
    for sp in spec_files:
        try:
            m = specs._SPEC_ID_RE.search(sp.read_text(encoding="utf-8"))
            if m:
                spec_map[m.group(1)] = sp
        except (OSError, UnicodeDecodeError):
            continue

    spec_cache: Dict[str, Tuple[List[str], List[Tuple[int, str]], List[bool]]] = {}
    for id6, sp in spec_map.items():
        spec_cache[id6] = _spec_headings_and_fences(sp)

    target_files: List[Path] = []
    for p in paths:
        path_obj = Path(p)
        if not path_obj.is_absolute():
            path_obj = repo_root / path_obj
        if path_obj.is_dir():
            for root, _, files in os.walk(path_obj):
                for f in sorted(files):
                    if f.endswith(".py"):
                        target_files.append(Path(root) / f)
        elif path_obj.is_file():
            target_files.append(path_obj)

    findings: List[StaleSpecAnchor] = []

    for fpath in target_files:
        try:
            flines = fpath.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue

        in_docstring: Optional[str] = None
        docstring_id6: Optional[str] = None
        comment_id6: Optional[str] = None

        for lno, line in enumerate(flines, 1):
            stripped = line.strip()
            line_docstring_start = False

            if in_docstring is None:
                m_q = re.search(r'("""|\'\'\')', line)
                if m_q:
                    q = m_q.group(1)
                    rest = line[m_q.end() :]
                    if q in rest:
                        cur_id6 = None
                        for token in _ID6_RE.findall(line):
                            if token in spec_cache:
                                cur_id6 = token
                                break
                        anchors = _find_anchors_on_line(line, cur_id6, spec_cache)
                        for id6, off in anchors:
                            _evaluate_citation(
                                fpath, lno, line, id6, off, spec_cache, findings
                            )
                        continue
                    else:
                        in_docstring = q
                        docstring_id6 = None
                        line_docstring_start = True

            active_id6: Optional[str] = None
            if in_docstring:
                for token in _ID6_RE.findall(line):
                    if token in spec_cache:
                        docstring_id6 = token
                active_id6 = docstring_id6
                if not line_docstring_start and in_docstring in line:
                    in_docstring = None
                    docstring_id6 = None
            elif stripped.startswith("#"):
                for token in _ID6_RE.findall(line):
                    if token in spec_cache:
                        comment_id6 = token
                active_id6 = comment_id6
            else:
                comment_id6 = None
                for token in _ID6_RE.findall(line):
                    if token in spec_cache:
                        active_id6 = token
                        break

            anchors = _find_anchors_on_line(line, active_id6, spec_cache)
            for id6, off in anchors:
                _evaluate_citation(fpath, lno, line, id6, off, spec_cache, findings)

    return findings


def _evaluate_citation(
    fpath: Path,
    lno: int,
    line: str,
    id6: str,
    off: int,
    spec_cache: Dict,
    findings: List[StaleSpecAnchor],
) -> None:
    if id6 not in spec_cache:
        return
    lines, headings, in_fence = spec_cache[id6]
    enc_h, validity = _resolve_offset(lines, headings, in_fence, off)

    if validity != "valid":
        findings.append(StaleSpecAnchor(fpath, lno, id6, off, enc_h, validity))
        return

    named_sec = _extract_named_section(line)
    if named_sec:
        if _heading_matches_section(enc_h, named_sec):
            return
        findings.append(StaleSpecAnchor(fpath, lno, id6, off, enc_h, validity))
        return

    title = _heading_title(enc_h)
    if title and len(title) >= 4 and title.lower() in line.lower():
        return

    findings.append(StaleSpecAnchor(fpath, lno, id6, off, enc_h, validity))
