"""Prose em/en dash scanner (spec ecmw83 R-07).

Scans markdown text for em dash (U+2014) and en dash (U+2013) characters occurring
in authored prose, excluding non-prose regions:
- YAML `---` front matter
- Metadata block (every line before the first `## ` section heading)
- Fenced code blocks (``` or ~~~)
- Indented code blocks (4 spaces or tab)
- Block quotes (> ...)
- Inline code spans (`...`)
"""

import re
from typing import List, Tuple

_EM_DASH = "\u2014"
_EN_DASH = "\u2013"
_DASH_CHARS = (_EM_DASH, _EN_DASH)

_FENCE_RE = re.compile(r"^(\s*)(```|~~~)")
_CODE_SPAN_RE = re.compile(r"(`+)(.*?)\1")


def find_prose_dashes(text: str) -> List[Tuple[int, int, str]]:
    """Return (1-based line, 1-based column, character) for each em/en dash in prose outside
    fenced code blocks, indented code blocks, block quotes, inline code spans, YAML `---`
    front matter, and the metadata block (every line before the first `## ` heading).
    """
    if not text or (_EM_DASH not in text and _EN_DASH not in text):
        return []
    lines = text.splitlines()
    n = len(lines)
    if n == 0:
        return []

    # YAML front matter: only if the very first line is exactly '---'.
    idx = 0
    if lines[0].strip() == "---":
        idx = 1
        while idx < n and lines[idx].strip() != "---":
            idx += 1
        if idx < n:
            idx += 1  # skip the closing fence

    # Metadata block: every line before the first `## ` section heading (boundary specs._metadata_end uses).
    meta_end = n
    for i in range(idx, n):
        if lines[i].startswith("## "):
            meta_end = i
            break

    start_idx = max(idx, meta_end)
    in_fence = False
    fence_marker = ""
    findings: List[Tuple[int, int, str]] = []

    for i in range(start_idx, n):
        raw = lines[i]
        lineno = i + 1

        m = _FENCE_RE.match(raw)
        if m:
            marker = m.group(2)
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            continue

        if in_fence:
            continue

        if raw.startswith("    ") or raw.startswith("\t"):
            # Indented code block (4 spaces / tab)
            continue

        if raw.lstrip().startswith(">"):
            # Block quote
            continue

        if _EM_DASH not in raw and _EN_DASH not in raw:
            continue

        # Mask out inline code spans within the line
        code_spans = [span_m.span() for span_m in _CODE_SPAN_RE.finditer(raw)]

        for col_idx, ch in enumerate(raw):
            if ch in _DASH_CHARS:
                if not any(start <= col_idx < end for start, end in code_spans):
                    findings.append((lineno, col_idx + 1, ch))

    return findings
