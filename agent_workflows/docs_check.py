"""Documentation link / command / option / prose checks for the operator docs.

awoptimize Order 18 (`0zst62`) E-01.

Deterministic, read-only checks over the Markdown documentation set:

  * :func:`check_no_unicode_dashes` - user-facing prose must contain NO em (U+2014) or en
    (U+2013) dashes (the AGENTS.md user-facing prose rule); ASCII hyphens only.
  * :func:`check_internal_links`    - a relative Markdown link ``[text](path)`` must resolve to
    a file that exists (a broken link fails).
  * :func:`check_aw_commands`       - every ``aw <subcommand>`` referenced in a fenced command
    block must be a known top-level subcommand (a typo fails).
  * :func:`check_doc`               - run all checks over one doc, returning findings.
  * :func:`check_docs_dir`          - run all checks over a docs directory.

Pure stdlib (D138). Python 3.9+.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

EM_DASH = "\u2014"
EN_DASH = "\u2013"

# Markdown inline link: [text](target)
_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# An `aw <sub>` reference (in prose or fenced blocks).
_AW_CMD_RE = re.compile(r"\baw\s+([a-z][a-z0-9-]*)\b")


@dataclass
class DocFinding:
    """One documentation check finding."""

    doc: str
    line: int
    check: str
    message: str

    def __str__(self) -> str:
        return f"{self.doc}:{self.line}: [{self.check}] {self.message}"


def check_no_unicode_dashes(text: str, doc: str = "") -> List[DocFinding]:
    """Fail on any em or en dash in user-facing prose (ASCII hyphens only)."""
    findings: List[DocFinding] = []
    for i, line in enumerate(text.splitlines(), 1):
        if EM_DASH in line:
            findings.append(
                DocFinding(
                    doc, i, "no-unicode-dashes", "em dash (U+2014) in user-facing prose"
                )
            )
        if EN_DASH in line:
            findings.append(
                DocFinding(
                    doc, i, "no-unicode-dashes", "en dash (U+2013) in user-facing prose"
                )
            )
    return findings


def check_internal_links(text: str, doc_path: Path) -> List[DocFinding]:
    """Fail on a relative Markdown link whose target file does not exist."""
    findings: List[DocFinding] = []
    base = doc_path.parent
    for i, line in enumerate(text.splitlines(), 1):
        for m in _LINK_RE.finditer(line):
            target = m.group(1).strip()
            # Skip external / anchor / mail links.
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            # Strip any in-page anchor.
            path_part = target.split("#", 1)[0]
            if not path_part:
                continue
            resolved = (base / path_part).resolve()
            if not resolved.exists():
                findings.append(
                    DocFinding(
                        str(doc_path.name),
                        i,
                        "internal-link",
                        f"link target '{target}' does not exist",
                    )
                )
    return findings


def check_aw_commands(
    text: str, known_subcommands: Sequence[str], doc: str = ""
) -> List[DocFinding]:
    """Fail on an ``aw <subcommand>`` reference that is not a known top-level subcommand."""
    known = set(known_subcommands)
    findings: List[DocFinding] = []
    for i, line in enumerate(text.splitlines(), 1):
        for m in _AW_CMD_RE.finditer(line):
            sub = m.group(1)
            if sub not in known:
                findings.append(
                    DocFinding(
                        doc,
                        i,
                        "aw-command",
                        f"'aw {sub}' is not a known subcommand",
                    )
                )
    return findings


def known_subcommands() -> List[str]:
    """The set of known top-level ``aw`` subcommands (from the CLI parser)."""
    try:
        from agent_workflows import cli

        parser = cli._build_parser()
        subs: List[str] = []
        for action in parser._actions:  # noqa: SLF001 (argparse introspection)
            choices = getattr(action, "choices", None)
            if choices:
                subs.extend(list(choices))
        return sorted(set(subs))
    except Exception:
        # Conservative fallback: the subcommands referenced by the shipped docs.
        return [
            "run",
            "ipd",
            "sanitize",
            "check-local-leaks",
            "doctor",
            "status",
            "install",
            "attention",
            "benchmark",
        ]


def check_doc(
    doc_path: Path, subcommands: Optional[Sequence[str]] = None
) -> List[DocFinding]:
    """Run all checks over a single doc file."""
    text = doc_path.read_text(encoding="utf-8")
    subs = list(subcommands) if subcommands is not None else known_subcommands()
    findings: List[DocFinding] = []
    findings.extend(check_no_unicode_dashes(text, doc_path.name))
    findings.extend(check_internal_links(text, doc_path))
    findings.extend(check_aw_commands(text, subs, doc_path.name))
    return findings


def check_docs_dir(
    docs_dir: Path, subcommands: Optional[Sequence[str]] = None
) -> List[DocFinding]:
    """Run all checks over every ``*.md`` file under a docs directory."""
    from agent_workflows import artifact_core as _core

    subs = list(subcommands) if subcommands is not None else known_subcommands()
    findings: List[DocFinding] = []
    ignored_dirs = _core.get_ignored_dirs(docs_dir)
    for md in sorted(docs_dir.rglob("*.md")):
        if _core.is_ignored_path(md, docs_dir, ignored_dirs):
            continue
        findings.extend(check_doc(md, subs))
    return findings


__all__ = [
    "EM_DASH",
    "EN_DASH",
    "DocFinding",
    "check_no_unicode_dashes",
    "check_internal_links",
    "check_aw_commands",
    "known_subcommands",
    "check_doc",
    "check_docs_dir",
]
