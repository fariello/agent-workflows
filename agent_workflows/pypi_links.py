"""Rewrite relative Markdown links to absolute GitHub URLs for the PyPI long-description (D-PyPI).

PyPI renders a project's long-description (our `README.md`) with NO repository context, so relative
links like `[CLI](docs/cli.md)` or `![diagram](img/x.png)` - correct on GitHub - 404 on PyPI. At
build time a hatchling metadata hook feeds the README text through `rewrite_relative_links` so the
PUBLISHED metadata carries absolute, tag-pinned URLs. The source `README.md` on disk is never
modified (its relative links stay correct for GitHub browsing).

Stdlib only (zero runtime deps, D46). Pure and side-effect-free, so it is directly unit-testable.

Rewritten:
  - relative doc/link targets   -> https://github.com/<owner>/<repo>/blob/<ref>/<path>
  - relative image targets      -> https://github.com/<owner>/<repo>/raw/<ref>/<path>  (by extension)
Left untouched:
  - absolute http(s):// and protocol-relative // links
  - mailto: (and other scheme:) links
  - pure in-page #anchors
  - a relative path that escapes the repo root via ../ (left as-is; the caller may note it)
"""

from __future__ import annotations

import posixpath
import re
from typing import Optional

# Markdown inline links/images: ![alt](target) and [text](target). Captures the target only.
# Handles an optional "title" after the target: (target "title").
_LINK_RE = re.compile(
    r'(?P<bang>!?)\[(?P<text>[^\]]*)\]\((?P<target>[^)\s]+)(?P<title>\s+"[^"]*")?\)'
)

_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".ico")

# Targets we never rewrite (already absolute, external, or in-page).
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")  # e.g. http:, https:, mailto:


def _is_relative_internal(target: str) -> bool:
    """True if target is a relative, repo-internal path we should rewrite."""

    if not target:
        return False
    if target.startswith("#"):  # in-page anchor
        return False
    if target.startswith("//"):  # protocol-relative (external)
        return False
    if _SCHEME_RE.match(target):  # http:, https:, mailto:, etc.
        return False
    return True


def _norm_path(target: str) -> Optional[str]:
    """Normalize a relative target to a clean repo-relative path, or None if it escapes root.

    Strips a leading `./`, drops any `#fragment`/`?query`, and resolves `../`. Returns None when
    the path climbs above the repo root (we leave such links untouched).
    """

    path = target.split("#", 1)[0].split("?", 1)[0]
    if not path:
        return None
    path = path.lstrip("/")  # treat a leading slash as repo-root-relative
    norm = posixpath.normpath(path)
    if norm == "." or norm.startswith("../"):
        return None
    return norm


def _is_image(bang: str, path: str) -> bool:
    return bang == "!" or path.lower().endswith(_IMAGE_EXTS)


def rewrite_relative_links(markdown: str, owner: str, repo: str, ref: str) -> str:
    """Return `markdown` with relative repo-internal links rewritten to absolute GitHub URLs.

    `ref` is the git ref to pin to (e.g. a release tag like `v1.1.0`). Absolute, external,
    mailto, and in-page-anchor links are left unchanged, as is any link that escapes the repo root.
    """

    base = f"https://github.com/{owner}/{repo}"

    def _sub(m: "re.Match[str]") -> str:
        bang = m.group("bang")
        text = m.group("text")
        target = m.group("target")
        title = m.group("title") or ""
        if not _is_relative_internal(target):
            return m.group(0)
        norm = _norm_path(target)
        if norm is None:
            return m.group(0)
        # Preserve a trailing #fragment on doc links (anchors within a page).
        frag = ""
        if "#" in target:
            frag = "#" + target.split("#", 1)[1]
        kind = "raw" if _is_image(bang, norm) else "blob"
        url = f"{base}/{kind}/{ref}/{norm}{frag}"
        return f"{bang}[{text}]({url}{title})"

    return _LINK_RE.sub(_sub, markdown)


def owner_repo_from_url(url: str) -> Optional[tuple]:
    """Parse (owner, repo) from a GitHub URL, or None if it is not a GitHub URL.

    Accepts forms like `https://github.com/owner/repo`, optionally with `.git` or a trailing slash.
    """

    m = re.match(
        r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/#?]+)", url.strip()
    )
    if not m:
        return None
    owner = m.group("owner")
    repo = m.group("repo")
    if repo.endswith(".git"):
        repo = repo[:-4]
    return (owner, repo)
