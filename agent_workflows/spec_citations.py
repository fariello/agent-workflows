"""Pure detector for stale spec line-anchor citations (IPD mt54wr, backlog sbh1o1).

Answers whether a spec line-anchor citation in source files resolves to the heading
the citing prose implies or lands in an invalid location (past end of file, in a code
fence, or on a blank line).

PURE AND CWD-INDEPENDENT: takes repo_root and paths explicitly, never imports check_engine.
"""

from __future__ import annotations

import contextlib
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple, Union

from agent_workflows import specs


DEFAULT_SCAN_SUBDIRS: Tuple[str, ...] = ("agent_workflows", "tools", "tests")


def default_scan_roots(repo_root: Union[str, Path]) -> List[Path]:
    """Return the candidate scan roots for spec anchor citations under repo_root.

    Returns existing paths among agent_workflows, tools, tests; falls back to [repo_root]
    if none exist.
    """
    root = Path(repo_root)
    roots = [root / d for d in DEFAULT_SCAN_SUBDIRS if (root / d).exists()]
    return roots if roots else [root]


@dataclass(frozen=True)
class NewStaleAnchorsResult:
    """Result of comparing stale spec anchor citations between two commits."""

    status: str  # "new", "none", or "unknown"
    findings: List[StaleSpecAnchor]
    reason: str


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


def _find_unattributed_anchors_on_line(line: str) -> List[int]:
    """Find bare offset citations on a comment or docstring line when no spec id6 is known."""
    offsets: List[int] = []
    # 1. Bare backtick `:\d+`, ONLY if line also contains the word 'spec' (case-insensitive)
    if re.search(r"\bspec\b", line, re.IGNORECASE):
        for m in re.finditer(r"`:\s*(\d+)`", line):
            off = int(m.group(1))
            if off not in offsets:
                offsets.append(off)
    # 2. Bare spec : \d+ or spec [N.N] : \d+
    for m in re.finditer(
        r"\bspec(?:\s+[0-9]+(?:\.[0-9]+)*)?\s+:(\d+)\b", line, re.IGNORECASE
    ):
        off = int(m.group(1))
        if off not in offsets:
            offsets.append(off)
    return offsets


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
        docstring_block_text: Optional[str] = None
        comment_id6: Optional[str] = None
        comment_block_text: Optional[str] = None

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
                                fpath,
                                lno,
                                line,
                                id6,
                                off,
                                spec_cache,
                                findings,
                                block_text=line,
                            )
                        if cur_id6 is None:
                            direct_offs = {a[1] for a in anchors}
                            for off in _find_unattributed_anchors_on_line(line):
                                if off not in direct_offs:
                                    findings.append(
                                        StaleSpecAnchor(
                                            fpath, lno, "", off, "", "unattributed"
                                        )
                                    )
                        continue
                    else:
                        in_docstring = q
                        line_docstring_start = True
                        j = lno - 1
                        doc_lines = [flines[j]]
                        j += 1
                        while j < len(flines):
                            doc_lines.append(flines[j])
                            if q in flines[j]:
                                break
                            j += 1
                        docstring_block_text = "\n".join(doc_lines)
                        doc_known_specs = [
                            t
                            for t in _ID6_RE.findall(docstring_block_text)
                            if t in spec_cache
                        ]
                        docstring_id6 = doc_known_specs[0] if doc_known_specs else None

            active_id6: Optional[str] = None
            block_text: str = ""
            in_block = False

            if in_docstring:
                in_block = True
                block_text = docstring_block_text or ""
                for token in _ID6_RE.findall(line):
                    if token in spec_cache:
                        docstring_id6 = token
                active_id6 = docstring_id6
                if not line_docstring_start and in_docstring in line:
                    in_docstring = None
                    docstring_id6 = None
                    docstring_block_text = None
            elif stripped.startswith("#"):
                in_block = True
                if comment_block_text is None:
                    j = lno - 1
                    comm_lines = []
                    while j < len(flines) and flines[j].strip().startswith("#"):
                        comm_lines.append(flines[j])
                        j += 1
                    comment_block_text = "\n".join(comm_lines)
                    comm_known_specs = [
                        t
                        for t in _ID6_RE.findall(comment_block_text)
                        if t in spec_cache
                    ]
                    comment_id6 = comm_known_specs[0] if comm_known_specs else None
                block_text = comment_block_text or ""
                for token in _ID6_RE.findall(line):
                    if token in spec_cache:
                        comment_id6 = token
                active_id6 = comment_id6
            else:
                comment_id6 = None
                comment_block_text = None
                for token in _ID6_RE.findall(line):
                    if token in spec_cache:
                        active_id6 = token
                        break

            anchors = _find_anchors_on_line(line, active_id6, spec_cache)
            for id6, off in anchors:
                _evaluate_citation(
                    fpath,
                    lno,
                    line,
                    id6,
                    off,
                    spec_cache,
                    findings,
                    block_text=block_text,
                )

            if in_block and active_id6 is None:
                direct_offs = {a[1] for a in anchors}
                for off in _find_unattributed_anchors_on_line(line):
                    if off not in direct_offs:
                        findings.append(
                            StaleSpecAnchor(fpath, lno, "", off, "", "unattributed")
                        )

    return findings


def _evaluate_citation(
    fpath: Path,
    lno: int,
    line: str,
    id6: str,
    off: int,
    spec_cache: Dict,
    findings: List[StaleSpecAnchor],
    block_text: str = "",
) -> None:
    if id6 not in spec_cache:
        return
    lines, headings, in_fence = spec_cache[id6]
    enc_h, validity = _resolve_offset(lines, headings, in_fence, off)

    if validity != "valid":
        findings.append(StaleSpecAnchor(fpath, lno, id6, off, enc_h, validity))
        return

    # Table row check (E-03):
    # when an offset resolves `valid` to a line whose stripped text starts with `|`,
    # extract that row's first cell (strip pipes, backticks and whitespace, for example `I-07`)
    # and treat the citation as valid when that token appears in the citing BLOCK:
    # the contiguous run of `#` comment lines, or the docstring, containing the citing line.
    target_line = lines[off - 1].strip()
    if target_line.startswith("|"):
        parts = target_line.split("|")
        if len(parts) > 1:
            first_cell = parts[1].replace("`", "").strip()
            if first_cell and not set(first_cell).issubset({"-", ":", " "}):
                search_text = block_text if block_text else line
                if first_cell in search_text:
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


def _cleanup_worktree(repo: Path, wt_path: Path) -> None:
    """Safely remove a detached temporary worktree and prune."""
    try:
        subprocess.run(
            ["git", "-C", str(repo), "worktree", "remove", "--force", str(wt_path)],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        pass
    try:
        if wt_path.exists():
            shutil.rmtree(wt_path, ignore_errors=True)
    except Exception:
        pass
    try:
        subprocess.run(
            ["git", "-C", str(repo), "worktree", "prune"],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        pass


@contextlib.contextmanager
def _materialize_commit(repo: Path, commit: str) -> Iterator[Path]:
    """Materialize a commit in an ephemeral detached worktree outside tracked paths."""
    wt_path = Path(tempfile.mkdtemp(prefix="aw-spec-anchor-"))
    try:
        res = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "worktree",
                "add",
                "--detach",
                str(wt_path),
                str(commit),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            raise RuntimeError(
                f"git worktree add failed for {commit}: {res.stderr.strip()}"
            )
        yield wt_path
    finally:
        _cleanup_worktree(repo, wt_path)


def new_stale_anchors(
    repo: Union[str, Path], lane_commit: str, base_commit: str
) -> NewStaleAnchorsResult:
    """Compare stale spec line-anchor citations between lane_commit and base_commit.

    Returns NewStaleAnchorsResult with status 'new', 'none', or 'unknown'.
    Never raises: any exception returns 'unknown' with the exception type and message.
    """
    try:
        repo_path = Path(repo)
        lane_sha = str(lane_commit).strip()
        base_sha = str(base_commit).strip()

        # (1) SHORT-CIRCUIT: if git diff --name-only base_commit lane_commit names
        # no .spec.md file and no .py file under the scan roots, return 'none' without scanning.
        diff_res = subprocess.run(
            [
                "git",
                "-C",
                str(repo_path),
                "diff",
                "--name-only",
                base_sha,
                lane_sha,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if diff_res.returncode != 0:
            raise RuntimeError(
                f"git diff failed between {base_sha} and {lane_sha}: {diff_res.stderr.strip()}"
            )

        changed_paths = [
            line.strip() for line in diff_res.stdout.splitlines() if line.strip()
        ]

        scan_roots = default_scan_roots(repo_path)
        rel_roots: List[str] = []
        for r in scan_roots:
            try:
                rel_roots.append(r.relative_to(repo_path).as_posix())
            except ValueError:
                rel_roots.append(r.as_posix())

        has_relevant_change = False
        for p in changed_paths:
            if p.endswith(".spec.md"):
                has_relevant_change = True
                break
            if p.endswith(".py"):
                if "." in rel_roots or any(
                    p == r or p.startswith(r + "/") for r in rel_roots
                ):
                    has_relevant_change = True
                    break

        if not has_relevant_change:
            return NewStaleAnchorsResult(
                status="none",
                findings=[],
                reason="no spec or scanned python files changed",
            )

        # (2) Evaluate BOTH sides at COMMITS via temporary worktrees.
        base_keys: set[Tuple[str, str, int, str]] = set()
        with _materialize_commit(repo_path, base_sha) as base_wt:
            base_wt_roots = default_scan_roots(base_wt)
            base_raw_findings = stale_spec_anchors(base_wt, base_wt_roots)
            for f in base_raw_findings:
                try:
                    rel_p = f.file.relative_to(base_wt).as_posix()
                except ValueError:
                    rel_p = f.file.as_posix()
                try:
                    flines = f.file.read_text(
                        encoding="utf-8", errors="ignore"
                    ).splitlines()
                    citing_line = (
                        flines[f.line - 1].strip() if 1 <= f.line <= len(flines) else ""
                    )
                except OSError:
                    citing_line = ""
                base_keys.add((rel_p, f.id6, f.offset, citing_line))

        new_findings: List[StaleSpecAnchor] = []
        new_finding_details: List[str] = []
        with _materialize_commit(repo_path, lane_sha) as lane_wt:
            lane_wt_roots = default_scan_roots(lane_wt)
            lane_raw_findings = stale_spec_anchors(lane_wt, lane_wt_roots)
            for f in lane_raw_findings:
                try:
                    rel_p = f.file.relative_to(lane_wt).as_posix()
                except ValueError:
                    rel_p = f.file.as_posix()
                try:
                    flines = f.file.read_text(
                        encoding="utf-8", errors="ignore"
                    ).splitlines()
                    citing_line = (
                        flines[f.line - 1].strip() if 1 <= f.line <= len(flines) else ""
                    )
                except OSError:
                    citing_line = ""
                key = (rel_p, f.id6, f.offset, citing_line)
                if key not in base_keys:
                    rel_finding = StaleSpecAnchor(
                        file=Path(rel_p),
                        line=f.line,
                        id6=f.id6,
                        offset=f.offset,
                        enclosing_heading=f.enclosing_heading,
                        validity=f.validity,
                    )
                    new_findings.append(rel_finding)
                    new_finding_details.append(
                        f"- {rel_p}:{f.line}: spec '{f.id6}', offset {f.offset} (citing: {citing_line})"
                    )

        if new_findings:
            reason = (
                f"lane introduced {len(new_findings)} new stale spec line-anchor citation(s):\n"
                + "\n".join(new_finding_details)
            )
            return NewStaleAnchorsResult(
                status="new",
                findings=new_findings,
                reason=reason,
            )

        return NewStaleAnchorsResult(
            status="none",
            findings=[],
            reason="0 new stale spec line-anchor citations introduced",
        )

    except Exception as exc:
        return NewStaleAnchorsResult(
            status="unknown",
            findings=[],
            reason=f"{type(exc).__name__}: {exc}",
        )
