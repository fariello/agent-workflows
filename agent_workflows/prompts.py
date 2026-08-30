"""Owner verbs for the operational prompt STAGING tree (`.aw/records/prompts/`).

IPD `jxqdcw`: `aw prompts new` mints a CONFORMING staged prompt so a prompt is a tooled artifact
like every other record in this repo, instead of a hand-named file with hand-written metadata.

What this module owns, and why each property is load-bearing:

* the FILENAME, derived (never hand-typed) as the legacy faceted form
  ``YYYYMMDD-HHMM-NN-<slug>.prompt.md``. That is the shape the whole on-disk corpus already uses,
  and ``artifact_naming``'s own docstring places prompts among the types it does NOT give an id6, so
  the clustered id6 grammar is deliberately NOT used here (IPD jxqdcw OQ-02);
* the ``NN`` per-minute sequence, computed across the WHOLE prompts tree rather than only
  ``pending/``, so a prompt minted after an earlier same-minute prompt already moved to
  ``executed/`` cannot collide with it;
* the single leading ``<!-- aw-prompt: ... -->`` metadata comment, emitted as exactly ONE line and as
  an HTML comment. Both properties are contractual, not cosmetic (approved spec `prompt-purity lint`
  P4/P5, R1): an HTML comment is invisible when the file is pasted into a chat, and confining the
  metadata to one line means nothing before the prompt body can be mistaken for prompt content. YAML
  front-matter is forbidden for exactly this reason (it renders as visible text);
* NO body boilerplate. The prompt-purity contract requires the file to contain only the prompt
  addressed to the target AI, so a helpful template would itself be a violation (OQ-03).

Deliberately NOT here: ``aw prompts check`` (the prompt-purity lint) is owned by its own approved
spec, and prompt LIFECYCLE movement stays a ``git mv`` per the staging README. This module also never
writes to or promotes from the gitignored ``local/``/``untracked/`` quarantine lanes.

Stdlib only; Python 3.9 compatible.
"""

from __future__ import annotations

import datetime as _dt
import re
import sys
from pathlib import Path
from typing import List, Optional

from agent_workflows import artifact_core as core

# The recognized prompt kinds. DERIVED from the measured corpus (`run-once`, `research`, and
# `session-handoff` are the kinds actually in use across `.aw/records/prompts/`) plus the approved
# purity spec, NOT from the staging README, which historically documented a YAML `front-matter Kind:`
# the spec explicitly forbids (IPD jxqdcw F9). A closed set: an unknown kind is refused rather than
# silently written into a tracked artifact.
PROMPT_KINDS = ("run-once", "research", "session-handoff")

# The default lifecycle bucket a freshly minted prompt lands in, and its `Status:` value. Minting is
# always into the tracked staging lane; the lifecycle is the directory (staging README).
DEFAULT_STATUS = "pending"
PENDING_BUCKET = "pending"

# The sentence every conforming prompt in the corpus ends its metadata comment with (measured: 7 of
# 7). Emitted so a minted file matches the corpus and so a reader who DOES see the comment (e.g. in
# an editor) understands it is not part of the prompt.
_METADATA_TRAILER = (
    "This HTML comment is pipeline metadata only; it is invisible when pasted "
    "into a chat and is not part of the prompt."
)

# The legacy faceted staging name: YYYYMMDD-HHMM-NN-<slug>.prompt.md. Used to read back the existing
# per-minute sequence; the BUILDER below is the only thing that assembles a new one.
_STAGED_NAME_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<hhmm>\d{4})-(?P<nn>\d{2})-(?P<slug>[a-z0-9-]+)"
    r"(?:\.(?P<facet>[a-z0-9.-]+))?\.md\Z"
)


def _now() -> _dt.datetime:
    """The local wall clock, isolated in one function so a test can pin it deterministically."""

    return _dt.datetime.now()


def prompts_root(repo_root: Path) -> Path:
    """Prefer an existing `.aw/records/prompts`, else the legacy `.agents/prompts`."""

    new = Path(repo_root) / ".aw" / "records" / "prompts"
    if new.exists():
        return new
    legacy = Path(repo_root) / ".agents" / "prompts"
    if legacy.exists():
        return legacy
    return new


def _existing_names(root: Path) -> List[str]:
    """Every markdown filename anywhere in the prompts tree, EXCLUDING the gitignored lanes.

    Whole-tree (not just `pending/`) on purpose: the per-minute sequence must not reuse an `NN`
    belonging to a prompt that has already moved to `executed/` (or any other bucket), or two
    distinct prompts end up sharing a name in the corpus and in every reference to them.
    """

    names: List[str] = []
    if not root.is_dir():
        return names
    for p in root.rglob("*.md"):
        if not p.is_file():
            continue
        parts = set(p.relative_to(root).parts)
        if "local" in parts or "untracked" in parts:
            continue
        names.append(p.name)
    return names


def next_sequence(root: Path, date_compact: str, hhmm: str) -> int:
    """The next free two-digit `NN` for `<date_compact>-<hhmm>` across the whole prompts tree."""

    highest = 0
    prefix = f"{date_compact}-{hhmm}-"
    for name in _existing_names(root):
        if not name.startswith(prefix):
            continue
        m = _STAGED_NAME_RE.match(name)
        if m is None:
            continue
        try:
            nn = int(m.group("nn"))
        except ValueError:
            continue
        highest = max(highest, nn)
    return highest + 1


def build_staged_name(*, date_compact: str, hhmm: str, order: int, slug: str) -> str:
    """Assemble the ONE staged-prompt filename: `YYYYMMDD-HHMM-NN-<slug>.prompt.md`."""

    return f"{date_compact}-{hhmm}-{order:02d}-{core.kebab(slug)}.prompt.md"


def render_metadata_comment(
    *,
    kind: str,
    status: str,
    created: str,
    author: Optional[str] = None,
    targets: Optional[str] = None,
    concerns: Optional[str] = None,
) -> str:
    """The single leading `aw-prompt` line. ONE line, an HTML comment, no trailing body.

    A field with no supplied value is OMITTED rather than emitted with a placeholder: there is no
    shared author/actor resolver in this package to inherit from, and writing a guessed or `unknown`
    author into a tracked artifact would be worse than writing nothing (IPD jxqdcw E-03).
    """

    fields = [f"Kind: {kind}", f"Status: {status}", f"Created: {created}"]
    for label, value in (
        ("Author", author),
        ("Targets", targets),
        ("Concerns", concerns),
    ):
        text = (value or "").strip()
        if text:
            fields.append(f"{label}: {text}")
    body = " | ".join(fields)
    # Single line by construction: any newline a caller smuggled into a field would break the
    # purity property (P4/P5), so collapse whitespace instead of trusting the input.
    line = f"<!-- aw-prompt: {body} . {_METADATA_TRAILER} -->"
    return " ".join(line.split())


def _today_iso() -> str:
    return _now().date().isoformat()


def run_new(args) -> int:
    """Mint a conforming staged prompt in `.aw/records/prompts/pending/` (dry-run by default).

    Follows the established owner-verb shape (modeled on ``specs.run_new``): resolve the repo root
    through ``project_context.resolve_verb_repo_root``, derive the slug through ``artifact_core.kebab``
    with a length bound, render, honor dry-run as the DEFAULT with ``--apply`` to write, write via
    ``artifact_core.atomic_write``, and emit through the ``CommandResult``/``select_output``/
    ``get_renderer`` pipeline so ``--agent`` and ``--json`` behave like every other verb.

    Writes the metadata comment and nothing else: the AGENT writes the prompt body.
    """

    from agent_workflows.project_context import resolve_verb_repo_root
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        Change,
        CommandResult,
        select_output,
    )

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    ctx = select_output(args)

    slug_arg = (getattr(args, "slug", None) or "").strip()
    if not slug_arg:
        sys.stderr.write("aw prompts new: --slug is required\n")
        return 2
    slug = core.kebab(slug_arg)[:60].strip("-")
    if not slug:
        sys.stderr.write(
            "aw prompts new: --slug must contain at least one alphanumeric character\n"
        )
        return 2

    kind = (getattr(args, "kind", None) or "research").strip()
    if kind not in PROMPT_KINDS:
        sys.stderr.write(
            "aw prompts new: unrecognized --kind {!r}; expected one of {}\n".format(
                kind, ", ".join(PROMPT_KINDS)
            )
        )
        return 2

    status = (getattr(args, "status", None) or DEFAULT_STATUS).strip()

    date_iso = (getattr(args, "date", None) or "").strip() or _today_iso()
    if not re.match(r"\A\d{4}-\d{2}-\d{2}\Z", date_iso):
        sys.stderr.write(
            f"aw prompts new: --date must be YYYY-MM-DD (got {date_iso!r})\n"
        )
        return 2
    date_compact = date_iso.replace("-", "")

    hhmm = (getattr(args, "time", None) or "").strip() or _now().strftime("%H%M")
    if not re.match(r"\A\d{4}\Z", hhmm):
        sys.stderr.write(f"aw prompts new: --time must be HHMM (got {hhmm!r})\n")
        return 2

    root = prompts_root(repo_root)
    order = next_sequence(root, date_compact, hhmm)
    filename = build_staged_name(
        date_compact=date_compact, hhmm=hhmm, order=order, slug=slug
    )
    dest = root / PENDING_BUCKET / filename

    rendered = (
        render_metadata_comment(
            kind=kind,
            status=status,
            created=date_iso,
            author=getattr(args, "author", None),
            targets=getattr(args, "targets", None),
            concerns=getattr(args, "concerns", None),
        )
        + "\n"
    )

    data = {"path": str(dest), "kind": kind, "status": status, "sequence": order}

    if not getattr(args, "apply", False):
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="prompts new",
                status="clean",
                exit_code=0,
                summary=f"would write {dest}",
                changes=[Change(path=str(dest), kind="create", applied=False)],
                data=data,
                verified=True,
                complete=True,
            )
            return get_renderer(ctx).emit(res, ctx)
        sys.stdout.write(f"--- would write {dest} ---\n{rendered}")
        return 0

    dest.parent.mkdir(parents=True, exist_ok=True)
    core.atomic_write(dest, rendered)

    if ctx.is_agent or ctx.is_json:
        res = CommandResult(
            command="prompts new",
            status="clean",
            exit_code=0,
            summary=f"wrote {dest}",
            changes=[Change(path=str(dest), kind="create", applied=True)],
            data=data,
            verified=True,
            complete=True,
        )
        return get_renderer(ctx).emit(res, ctx)

    sys.stdout.write(f"aw prompts new: wrote {dest}\n")
    return 0
