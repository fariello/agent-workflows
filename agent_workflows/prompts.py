"""Owner verbs for the operational prompt STAGING tree (`.aw/records/prompts/`).

IPD `jxqdcw`: `aw prompts new` mints a CONFORMING staged prompt so a prompt is a tooled artifact
like every other record in this repo, instead of a hand-named file with hand-written metadata.

IPD `ubac5n`: a staged prompt now carries an ``<id6>`` in BOTH its filename and its one metadata
comment, so it is a CITABLE artifact like every other record type. This REVERSES `jxqdcw` OQ-02 on
the maintainer's explicit instruction (2026-09-20), which is recorded here rather than presented as
a bug nobody noticed: the legacy form was a resolved choice made on the evidence available then.

What this module owns, and why each property is load-bearing:

* the FILENAME, derived (never hand-typed) as the ONE uniform clustered grammar
  ``YYYYMMDD-<setid>-NN-<id6>-<slug>.prompt.md``, assembled by
  ``artifact_naming.build_clustered_name(..., artifact_type="prompt")``. The id6 is what makes a
  staged prompt resolvable by every `aw` verb (`aw find`, a `From-*`/`consumed-by` citation, the
  research pairing that puts an originating prompt at ``NN=00``); without it a prompt was invisible
  to the whole selector vocabulary. A PRE-CUTOVER legacy ``YYYYMMDD-HHMM-NN-<slug>.prompt.md`` name
  stays valid and is grandfathered by ``check_engine._prompt_requires_id6``; convert one on demand
  with ``aw rename prompts <legacy> --to-id6``;
* the ``<setid>``, taken from ``--set`` or DEFAULTED to the kebab slug (a singleton set of one, the
  same rule ``research_cmd.plan_new`` applies to a lone doc), so the verb needs no new required flag;
* the ``NN`` ORDER WITHIN THE SET (`ubac5n` OQ-01), which is what ``NN`` means in the clustered
  grammar. It REPLACES the former per-minute sequence, whose only reader was this module's own
  minting path, and whose collision purpose is dissolved outright by a repository-unique id6 in the
  name. A second prompt in the SAME set gets ``NN=02``; a singleton gets ``01``;
* the single leading ``<!-- aw-prompt: ... -->`` metadata comment, emitted as exactly ONE line and as
  an HTML comment, now carrying ``Id:`` and ``Set:`` so the handle is readable from INSIDE the file
  and not only from its name. Both properties are contractual, not cosmetic (approved spec
  `prompt-purity lint` P4/P5, R1): an HTML comment is invisible when the file is pasted into a chat,
  and confining the metadata to one line means nothing before the prompt body can be mistaken for
  prompt content. YAML front-matter is forbidden for exactly this reason (it renders as visible
  text), and so is a ``- Id:`` BULLET, which would land as visible text above the prompt body;
* NO body boilerplate. The prompt-purity contract requires the file to contain only the prompt
  addressed to the target AI, so a helpful template would itself be a violation (OQ-03).

Deliberately NOT here: ``aw prompts check`` (the prompt-purity lint) is owned by its own approved
spec, and prompt LIFECYCLE movement stays a ``git mv`` per the staging README. This module also never
writes to or promotes from the gitignored ``untracked/`` quarantine lane.

Stdlib only; Python 3.9 compatible.
"""

from __future__ import annotations

import datetime as _dt
import re
import sys
from pathlib import Path
from typing import List, Optional

from agent_workflows import artifact_core as core
from agent_workflows import artifact_naming as _naming

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

# The legacy faceted staging name: YYYYMMDD-HHMM-NN-<slug>.prompt.md. KEPT as a READER only: the
# grandfathered corpus still uses it (17 files at the 20260920 measurement) and `_existing_id6s`
# below must recognize such a name to skip it rather than mis-parse it. Nothing BUILDS one any more;
# `artifact_naming.build_clustered_name` is the only assembler (IPD ubac5n E-01).
_STAGED_NAME_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<hhmm>\d{4})-(?P<nn>\d{2})-(?P<slug>[a-z0-9-]+)"
    r"(?:\.(?P<facet>[a-z0-9.-]+))?\.md\Z"
)

# The `Id: <id6>` pair INSIDE the one `<!-- aw-prompt: ... -->` comment. This is where a prompt's id6
# lives in-file (IPD ubac5n E-02/E-04); there is deliberately no `- Id:` bullet form for a prompt,
# because a bullet renders as visible text above the prompt body (purity spec R1/P4). Anchored to the
# `Key: value` shape of that comment, so a bare `Id:` elsewhere in a prompt BODY is not read as a
# declaration.
_METADATA_ID_RE = re.compile(r"(?:\A|\|)\s*Id:\s*([0-9a-z]{6})\s*(?=\||$)")


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


def next_order_for_set(root: Path, set_id: str) -> int:
    """The next free two-digit `NN` (ORDER WITHIN THE SET) for `set_id` across the whole tree.

    `ubac5n` OQ-01 resolved `NN` to ORDER WITHIN A SET, which is what it means in the clustered
    grammar; the former per-minute sequence is gone. Whole-tree (not just `pending/`) for the same
    reason the per-minute reader was: a set member that already moved to `executed/` still occupies
    its order, so reusing it would give two members of one set the same position.

    A singleton set (the `--set`-omitted default) therefore gets `01`, and a second prompt named into
    the same set gets `02`.
    """

    highest = 0
    for name in _existing_names(root):
        m = _naming.parse_clustered(name)
        if m is None or m.group("set") != set_id:
            continue
        try:
            nn = int(m.group("nn"))
        except ValueError:
            continue
        highest = max(highest, nn)
    return highest + 1


def _existing_id6s(root: Path) -> set:
    """Every id6 already used by a prompt, from its filename slot AND its metadata comment.

    The per-tree half of the mint collision set. `artifact_core.mint_id6` UNIONS this with the
    repository-wide set rather than replacing it (IPD `sk7ggr` E-01), so this never has to be
    complete on its own; it exists so a prompt id6 that is somehow absent from the global scan still
    cannot be re-minted.
    """

    ids: set = set()
    if not root.is_dir():
        return ids
    for p in root.rglob("*.md"):
        if not p.is_file():
            continue
        parts = set(p.relative_to(root).parts)
        if "local" in parts or "untracked" in parts:
            continue
        m = _naming.parse_clustered(p.name)
        if m:
            ids.add(m.group("id6"))
        try:
            first = p.read_text(encoding="utf-8").split("\n", 1)[0]
        except (OSError, UnicodeDecodeError):
            continue
        m_id = _METADATA_ID_RE.search(first)
        if m_id:
            ids.add(m_id.group(1))
    return ids


def _resolve_set_id(
    repo_root: Path, *, explicit: Optional[str], slug: str, id6: str
) -> "tuple":
    """Resolve the clustered name's SET slot. Returns ``(set_id, error)``; either may be None.

    THREE RULES, IN ORDER, and the third exists because of a defect measured during execution:

    1. an EXPLICIT ``--set`` wins, kebab-normalized, and is judged by the ONE shared setid-length
       guard (``config.validate_setid_length_for_authoring``); over the maximum it is REFUSED, which
       is the same answer every other `--set`-taking verb gives;
    2. otherwise the SLUG is used, a singleton set of one, which is the rule
       ``research_cmd.plan_new`` applies to a lone doc;
    3. BUT A DERIVED SET ID IS NEVER A REFUSAL. Measured 2026-09-23: 15 of the 16 legacy prompt
       slugs are LONGER than the 24-character setid maximum (the longest is 50), so rule 2 alone
       would make `aw prompts new --slug <a-typical-prompt-slug>` exit 2 with a message about a flag
       the caller never passed, and the plan requires the verb to stay usable with no new flag. So an
       over-long derived set id falls back to the artifact's OWN id6, which is exactly what
       ``specs.run_new`` does for a standalone spec (`set_id=id6`), is 6 characters by construction,
       and therefore can never trip the guard. A long slug still lands in the SLUG slot, where no
       length policy applies; only the SET slot is bounded.

    The length WARNING (15-24) is returned to the caller for printing rather than swallowed, for
    either an explicit or a derived token.
    """

    from agent_workflows import config as _config

    explicit_token = (explicit or "").strip()
    if explicit_token:
        set_id = core.kebab(explicit_token)
        if not set_id:
            return (
                None,
                "--set must contain at least one alphanumeric character",
            )
        err, warn = _config.validate_setid_length_for_authoring(
            repo_root, set_id, verb="aw prompts new"
        )
        if err:
            return None, err
        if warn:
            sys.stderr.write(f"note: {warn}\n")
        return set_id, None

    derived = core.kebab(slug)
    err, warn = _config.validate_setid_length_for_authoring(
        repo_root, derived, verb="aw prompts new"
    )
    if err:
        # Rule 3: fall back to the id6 rather than refusing a call that passed no `--set`.
        return id6, None
    if warn:
        sys.stderr.write(f"note: {warn}\n")
    return derived, None


def build_prompt_name(
    *, date_compact: str, set_id: str, order: int, id6: str, slug: str
) -> str:
    """Assemble the ONE staged-prompt filename via the single naming authority.

    `YYYYMMDD-<setid>-NN-<id6>-<slug>.prompt.md`. Delegates to
    ``artifact_naming.build_clustered_name`` rather than formatting the grammar here, so this module
    cannot emit a name the checker rejects (the single-source property pinned by
    ``tests/test_naming_authority_single_source.py``).
    """

    return _naming.build_clustered_name(
        date=date_compact,
        set_id=set_id,
        order=order,
        id6=id6,
        slug=slug,
        artifact_type="prompt",
    )


def render_metadata_comment(
    *,
    kind: str,
    status: str,
    created: str,
    id6: Optional[str] = None,
    set_id: Optional[str] = None,
    author: Optional[str] = None,
    targets: Optional[str] = None,
    concerns: Optional[str] = None,
) -> str:
    """The single leading `aw-prompt` line. ONE line, an HTML comment, no trailing body.

    A field with no supplied value is OMITTED rather than emitted with a placeholder: there is no
    shared author/actor resolver in this package to inherit from, and writing a guessed or `unknown`
    author into a tracked artifact would be worse than writing nothing (IPD jxqdcw E-03).

    ``id6``/``set_id`` (IPD `ubac5n` E-02) are written as two more `Key: value` pairs INSIDE this one
    comment, positioned after `Kind:` to match the shape the hand-made
    `20260920-plainlang-01-ng0ga4-...` file already uses. They are deliberately NOT a `- Id:` bullet
    and NOT YAML front matter: either would put visible text above the prompt body and violate
    approved spec `20260808-1958-01-prompt-purity-lint` R1/P4.
    """

    fields = [f"Kind: {kind}"]
    id6_text = (id6 or "").strip()
    if id6_text:
        fields.append(f"Id: {id6_text}")
    set_text = (set_id or "").strip()
    if set_text:
        fields.append(f"Set: {set_text}")
    fields.extend([f"Status: {status}", f"Created: {created}"])
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


def has_metadata_comment(text: str) -> bool:
    """True iff ``text`` opens with the single `<!-- aw-prompt: ... -->` metadata comment.

    The precondition for writing an id6 INTO that comment. Measured 2026-09-20: 11 of the 17 tracked
    prompts have one and 6 do not (the oldest, authored before the comment convention), so a caller
    must be able to ask rather than assume, and `aw rename prompts --to-id6` uses this to report
    truthfully that such a file keeps its id6 in the FILENAME ONLY.
    """

    return "<!-- aw-prompt:" in text.split("\n", 1)[0]


def read_metadata_id6(text: str) -> Optional[str]:
    """The id6 declared inside a prompt's single `<!-- aw-prompt: ... -->` comment, or None.

    Reads the FIRST LINE only, which is where the purity contract puts that comment (R1/P4), so an
    `Id: <id6>` that a prompt BODY happens to quote is never read as a declaration.
    """

    first = text.split("\n", 1)[0]
    if "<!-- aw-prompt:" not in first:
        return None
    m = _METADATA_ID_RE.search(first)
    return m.group(1) if m else None


def inject_metadata_id6(text: str, *, id6: str, set_id: Optional[str] = None) -> str:
    """Return ``text`` with ``Id:`` (and optionally ``Set:``) written INTO its one metadata comment.

    IPD `ubac5n` E-04, and the whole reason this function exists rather than a second writer: this is
    the ONE place a prompt's id6 is written in-file, shared by `aw prompts new` (which renders the
    comment from scratch) and by `aw rename prompts --to-id6` (which must add the key to a comment
    that already exists). A `- Id:` BULLET is never produced, because for a prompt that is visible
    text above the prompt body and an approved-spec violation (`prompt-purity-lint` R1/P4).

    IDEMPOTENT: a comment that already declares an `Id:` is returned UNCHANGED, so a re-run never
    rewrites an established identity. A file with NO leading `aw-prompt` comment is also returned
    unchanged: minting one here would ADD a line above the body of a file whose purity this function
    exists to protect, and 6 of the 17 measured prompts legitimately have no comment at all. The
    caller sees "unchanged" and the rename still happens; the id6 then lives in the FILENAME only,
    which is stated plainly rather than silently repaired.
    """

    lines = text.split("\n")
    if not lines or "<!-- aw-prompt:" not in lines[0]:
        return text
    if _METADATA_ID_RE.search(lines[0]):
        return text

    first = lines[0]
    additions = [f"Id: {id6}"]
    set_text = (set_id or "").strip()
    if set_text and not re.search(r"(?:\A|\|)\s*Set:\s*[^|]+", first):
        additions.append(f"Set: {set_text}")
    insert = " | ".join(additions)

    # Position the new pair(s) directly after `Kind: <kind>` when there is one, which is the shape
    # the existing conforming corpus and `render_metadata_comment` both use; otherwise append them at
    # the end of the field run, just before the trailer sentence.
    m_kind = re.search(r"(Kind:\s*[^|]+?)(\s*\|)", first)
    if m_kind:
        updated = first[: m_kind.end(1)] + f" | {insert}" + first[m_kind.end(1) :]
    else:
        updated = first.replace(
            f" . {_METADATA_TRAILER}", f" | {insert} . {_METADATA_TRAILER}", 1
        )
        if updated == first:
            # No recognizable trailer: append before the closing comment marker.
            updated = re.sub(r"\s*-->\s*\Z", f" | {insert} -->", first)
    lines[0] = " ".join(updated.split())
    return "\n".join(lines)


def _today_iso() -> str:
    return _now().date().isoformat()


def run_new(args) -> int:
    """Mint a conforming staged prompt in `.aw/records/prompts/pending/` (dry-run by default).

    Follows the established owner-verb shape (modeled on ``specs.run_new``): resolve the repo root
    through ``project_context.resolve_verb_repo_root``, derive the slug through ``artifact_core.kebab``
    with a length bound, render, honor dry-run as the DEFAULT with ``--apply`` to write, write via
    ``artifact_core.atomic_write``, and emit through the ``CommandResult``/``select_output``/
    ``get_renderer`` pipeline so ``--agent`` and ``--json`` behave like every other verb.

    IPD `ubac5n` E-01/E-02: mints an id6 through the ONE mint seam (``artifact_core.mint_id6``),
    resolves the set id from ``--set`` or the slug, and assembles the clustered name through the ONE
    naming authority. The minted id6 goes in the filename AND in the single metadata comment.

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

    # `--time` is ACCEPTED AND IGNORED FOR THE NAME (IPD ubac5n OQ-01): the clustered grammar has no
    # HHMM slot, so there is nothing for it to fill. It is still VALIDATED rather than silently
    # swallowed, because a caller passing `--time 99` deserves the same refusal it always got, and it
    # is kept rather than removed because the shipped `research-prompt` workflow and existing agent
    # habits pass it; removing it would make argparse exit 2 on a previously valid invocation.
    hhmm = (getattr(args, "time", None) or "").strip()
    if hhmm and not re.match(r"\A\d{4}\Z", hhmm):
        sys.stderr.write(f"aw prompts new: --time must be HHMM (got {hhmm!r})\n")
        return 2

    root = prompts_root(repo_root)
    # IPD sk7ggr E-01: repository-wide mint, unioned with the prompts tree's own ids. Minted BEFORE
    # the set id is resolved, because a derived set id may legitimately FALL BACK to this id6.
    id6 = core.mint_id6(repo_root, _existing_id6s(root))

    set_id, set_err = _resolve_set_id(
        repo_root, explicit=getattr(args, "set", None), slug=slug, id6=id6
    )
    if set_err:
        # The shared setid guard already prefixes the verb name; only an error raised HERE needs one,
        # or the message reads `aw prompts new: aw prompts new: ...`.
        prefix = "" if set_err.startswith("aw prompts new:") else "aw prompts new: "
        sys.stderr.write(f"{prefix}{set_err}\n")
        return 2
    assert set_id is not None

    order = next_order_for_set(root, set_id)
    filename = build_prompt_name(
        date_compact=date_compact,
        set_id=set_id,
        order=order,
        id6=id6,
        slug=slug,
    )
    dest = root / PENDING_BUCKET / filename

    rendered = (
        render_metadata_comment(
            kind=kind,
            status=status,
            created=date_iso,
            id6=id6,
            set_id=set_id,
            author=getattr(args, "author", None),
            targets=getattr(args, "targets", None),
            concerns=getattr(args, "concerns", None),
        )
        + "\n"
    )

    data = {
        "path": str(dest),
        "kind": kind,
        "status": status,
        "id": id6,
        "set": set_id,
        "order": order,
        # `sequence` is KEPT as an alias of `order` so an existing agent/JSON consumer of this
        # verb's envelope does not lose a key it reads; the two are the same number now.
        "sequence": order,
    }

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
