"""Shared "commit-what-I-changed" helper: path-scoped, TTY-gated, no ``add -A``, no push.

This is a low-level LEAF module. Records-mutating verbs (``aw archive``, ``aw group``,
``aw rename``, ``aw research set-assign``/``mv``, the shared ``set`` engine, ``specs``) and,
later, the agentadhere ``aw commit`` primitive all reuse :func:`offer_commit` so there is a
SINGLE reusable commit path enforcing the repository contract (AGENTS.md):

* stage ONLY the explicit files the caller touched (``git add -- <paths>``); never ``-A``/``-a``;
* commit with the caller's message; never ``--no-verify``; never ``push``;
* INTERACTIVE-GATED - on a TTY prompt ``[Y/n]`` unless ``assume_yes`` (the ``--commit`` flag);
  NON-interactive without ``assume_yes`` is a NO-OP (skip), matching ``cli._confirm``'s ACTUAL
  decline-on-non-TTY behavior - NOT auto-yes; ``no_commit`` short-circuits to skip;
* NEVER folds in unrelated staged/unstaged changes. ``on_unrelated_staged`` selects the policy
  when the index already holds staged paths OUTSIDE ``paths``: ``"scope"`` (default; commit only
  ``paths``, leave the rest untouched) or ``"refuse"`` (return ``refused-dirty``, commit nothing);
* OPTIONALLY appends Git TRAILERS to the message (``trailers=``, default EMPTY so every existing
  caller is byte-for-byte unaffected). This lets a caller record WHICH run and work item produced
  a commit (``AW-Run: <run-id>``, ``AW-Item: <id6>``) so a deterministic checker can identify
  run-owned commits instead of assuming every commit between a baseline and HEAD belongs to the
  run - which is wrong in a SHARED checkout. The trailers are additive to the MESSAGE only: they
  change no staging, scoping, or rollback behavior. See :func:`compose_message_with_trailers`.

  HONEST LIMIT: a trailer is a CLAIM in a commit message, not an enforced boundary. An agent
  committing by hand can omit or forge one. Identifying run-owned commits is not the same as
  guaranteeing them; the enforcement half (a commit gateway) is deliberately NOT implemented here.

IMPORTANT (import direction): this leaf MUST NOT import ``cli`` (that would invert the
dependency and risk a cycle); the tiny yes/no prompt is reimplemented here instead. The
canonical git subprocess runner lives here as :func:`_git`; ``ipd_lifecycle._git`` delegates to
it so there is a single git-subprocess wrapper across the codebase.
"""

from __future__ import annotations

import inspect
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

# Keep an unpatched reference to subprocess.Popen so internal git-config probes
# inside agent_commit_identity are unaffected when unit tests mock subprocess.Popen
# around runner invocations (run_opencode / run_agy_turn).
_REAL_POPEN = subprocess.Popen

# --------------------------------------------------------------------------------------
# Git trailer conventions (see compose_message_with_trailers)
# --------------------------------------------------------------------------------------

# Canonical trailer KEYS this repository uses to mark a commit as run-owned. Spec 25kzda 4.6:
# the deterministic checker "finds run-owned commits by required immutable trailers such as
# `AW-Run: <run-id>` and `AW-Item: <id6>`, then proves their tree diffs".
TRAILER_KEY_RUN = "AW-Run"
TRAILER_KEY_ITEM = "AW-Item"
TRAILER_KEY_RUNNER = "AW-Runner"

# Environment variable names by which a live run hands its ids to an agent's `aw commit`.
# This is the ONE channel for that handover: the runner writes them and `work_cmd` reads
# them, both importing the names from here so the spelling is single-sourced exactly as the
# trailer keys are.
RUN_ID_ENV = "AW_RUN_ID"
ITEM_ID6_ENV = "AW_ITEM_ID6"
RUNNER_ENV = "AW_RUNNER"
AGENT_RUNNER_ENV = RUNNER_ENV
AGENT_MODEL_ENV = "AW_AGENT_MODEL"
COMMITTER_NAME_ENV = "GIT_COMMITTER_NAME"
COMMITTER_EMAIL_ENV = "GIT_COMMITTER_EMAIL"

# Closed set of recognized runner labels for the AW-Runner trailer.
RUNNER_OC_RUN = "aw oc run"
RUNNER_AGY_RUN = "aw agy run"
RUNNER_AW_COMMIT = "aw commit"
KNOWN_RUNNERS: Tuple[str, ...] = (RUNNER_OC_RUN, RUNNER_AGY_RUN, RUNNER_AW_COMMIT)

# A trailer token, per `git-interpret-trailers`: "there can be no whitespace before or inside the
# <key>, but any number of regular space and tab characters are allowed between the <key> and the
# separator". VERIFIED against git 2.43.0 by probing `git interpret-trailers --parse`: `AW-Run`
# and `A1-b2` parse; `AW_Run`, `AW.Run`, `AW+Run`, `AW/Run`, `AW*Run` and non-ASCII keys do NOT.
# So the accepted token charset is alphanumerics and hyphen only - deliberately NARROWER than a
# permissive guess, because a key git will not parse yields a SILENTLY trailer-less commit.
_TRAILER_TOKEN_RE = re.compile(r"^[A-Za-z0-9-]+$")

# A line that git counts as a trailer when deciding whether a paragraph IS a trailer block.
_TRAILER_LINE_RE = re.compile(r"^([A-Za-z0-9-]+)[ \t]*:")

# A continuation of the preceding trailer's value ("may be split over multiple lines with each
# subsequent line starting with at least one whitespace").
_TRAILER_CONT_RE = re.compile(r"^[ \t]+\S")

# git also ignores comment lines when parsing a trailer block.
_TRAILER_COMMENT_RE = re.compile(r"^#")

# git-generated trailers, which let an OTHERWISE-mixed paragraph still count as a trailer block
# (rule (ii) below). `Signed-off-by:` and the cherry-pick line are the git-generated ones.
_GIT_GENERATED_RE = re.compile(r"^(Signed-off-by[ \t]*:|\(cherry picked from )")

# A `---` divider ends the trailer-searchable region: the trailer group "must either be at the end
# of the input or be the last non-whitespace lines before a line that starts with `---` (followed
# by a space or the end of the line)". VERIFIED: `---` and `--- ` divide; `----` and `---foo` do not.
_DIVIDER_RE = re.compile(r"^---(\s|$)")


class TrailerError(ValueError):
    """A trailer whose SHAPE git could not parse (bad token, embedded newline, no separator).

    Raised at COMPOSITION time rather than producing a commit whose trailers silently fail to
    parse. Per the plan's OQ-02: validate the SHAPE here, and leave REFERENTIAL validity (does
    this id6 resolve to a real artifact?) to the ``aw check`` surface, where every other
    id6-resolution rule in this repo already lives. Do not fork that resolution into a commit helper.
    """


def _is_trailer_block(lines: Sequence[str]) -> bool:
    """Would git parse this paragraph as a trailer block?

    Implements the rule from ``git-interpret-trailers``: a group of one or more lines that
    "(i) is all trailers, or (ii) contains at least one Git-generated or user-configured trailer
    and consists of at least 25% trailers".

    Only case (i) and the git-generated arm of (ii) are modeled. A USER-CONFIGURED trailer
    (``trailer.<token>.key`` in git config) would also satisfy (ii), and this function cannot see
    git config, so it may answer False where git would answer True. That direction is SAFE: we
    then start a new blank-line-separated block, which parses correctly on its own (the earlier
    lines simply keep whatever status they already had). Answering True where git answers False
    is the dangerous direction, and that cannot happen here.
    """

    trailer_count = 0
    other_count = 0
    saw_git_generated = False
    seen_trailer = False
    for line in lines:
        if _TRAILER_COMMENT_RE.match(line):
            continue  # git ignores comments when parsing a block
        if seen_trailer and _TRAILER_CONT_RE.match(line):
            continue  # folded continuation of the previous trailer's value
        if _TRAILER_LINE_RE.match(line):
            trailer_count += 1
            seen_trailer = True
            if _GIT_GENERATED_RE.match(line):
                saw_git_generated = True
        else:
            other_count += 1
            seen_trailer = False
    if trailer_count == 0:
        return False
    if other_count == 0:
        return True  # (i) all trailers
    # (ii) at least one git-generated trailer AND >= 25% trailers, i.e. other <= 3 * trailers.
    return saw_git_generated and other_count <= 3 * trailer_count


def validate_trailer(trailer: str) -> str:
    """Return ``trailer`` unchanged if git can parse it as ``Key: value``, else raise.

    Rejects an embedded newline (which would break OUT of the trailer block and silently drop
    everything after it), a missing ``:`` separator, an empty key, and a key containing any
    character outside git's token charset. An EMPTY VALUE is allowed: git parses ``Key:`` fine.
    """

    if not isinstance(trailer, str):
        raise TrailerError(f"trailer must be a string, got {type(trailer).__name__}")
    if "\n" in trailer or "\r" in trailer:
        raise TrailerError(
            f"trailer must not contain a newline (it would terminate the trailer block): {trailer!r}"
        )
    if ":" not in trailer:
        raise TrailerError(
            f"trailer must be 'Key: value' (no ':' separator found): {trailer!r}"
        )
    key, _, value = trailer.partition(":")
    key = key.rstrip(" \t")  # git allows space/tab between the key and the separator
    if not key:
        raise TrailerError(f"trailer key must not be empty: {trailer!r}")
    if not _TRAILER_TOKEN_RE.match(key):
        raise TrailerError(
            "trailer key must contain only letters, digits, and '-' (git will not parse "
            f"anything else as a trailer): {trailer!r}"
        )
    if value.strip() and value[:1] not in (" ", "\t"):
        # Not an error for git (`Key:v` parses), but normalize on the conventional single space.
        return f"{key}: {value.strip()}"
    return trailer


def compose_message_with_trailers(message: str, trailers: Sequence[str]) -> str:
    """PURE composition: return ``message`` with ``trailers`` appended as a Git trailer block.

    No git invocation, no I/O - so every body shape is testable directly. With an empty
    ``trailers`` the message is returned COMPLETELY UNCHANGED (byte-for-byte), which is what keeps
    this leaf module's six-plus existing callers unaffected.

    Handles the body shapes that break naive concatenation:

    * a MULTILINE body - the block goes after the whole body, not after the subject;
    * a body that ALREADY ends in a trailer block - the new trailers JOIN that block instead of
      starting a second one. This is the subtle case: a blank line INSIDE a trailer block
      TERMINATES it, so a naive ``message + "\\n\\n" + trailers`` makes git stop recognizing the
      EARLIER trailers. VERIFIED with git 2.43.0: appending ``AW-Run: r1`` after a blank line to a
      body ending ``Co-authored-by: x`` makes ``--parse`` report ONLY ``AW-Run``, silently losing
      the co-author. Joining the block reports both. The commit SUCCEEDS either way, so this
      failure is invisible without asking git to parse.
    * a body with NO trailing newline - normalized before the separator is added;
    * a body containing a ``---`` divider - the trailers are inserted BEFORE the divider, since
      git only recognizes a trailer group at the end of the input or immediately before such a
      divider. This matches what ``git interpret-trailers`` itself does with the same input.
    * a SINGLE-PARAGRAPH message whose only paragraph looks like trailers - a new block is started
      rather than joined, because git requires a trailer group to be "preceded by one or more empty
      lines" and so does not treat a lone first paragraph as trailers at all. Joining there would
      produce a message with NO parseable trailers. (910 of the last 2211 commit messages in this
      repository are single-paragraph, so this shape is the common case, not an edge case.)

    Raises :class:`TrailerError` on a structurally unparseable trailer (see :func:`validate_trailer`).
    """

    cleaned = [validate_trailer(t) for t in trailers]
    if not cleaned:
        return message  # byte-for-byte identical: the existing-caller guarantee

    trailer_text = "\n".join(cleaned)
    if not message.strip():
        # No body to attach to; the trailers ARE the message. git does not parse a lone first
        # paragraph as trailers, but there is no body to preserve, so this is the honest result.
        return trailer_text + "\n"

    body = message.rstrip(
        "\n"
    )  # handles "no trailing newline" and over-long runs alike

    # --- A `---` divider ends the trailer-searchable region: insert BEFORE it. ---
    lines = body.split("\n")
    divider_idx = next((i for i, ln in enumerate(lines) if _DIVIDER_RE.match(ln)), None)
    if divider_idx is not None:
        head = "\n".join(lines[:divider_idx]).rstrip("\n")
        tail = "\n".join(lines[divider_idx:])
        return f"{compose_message_with_trailers(head, cleaned)}\n{tail}\n"

    # --- Does the LAST paragraph already parse as a trailer block? If so, JOIN it. ---
    paragraphs = re.split(r"\n[ \t]*\n", body)
    if len(paragraphs) > 1:
        last_lines = [ln for ln in paragraphs[-1].split("\n") if ln.strip()]
        if _is_trailer_block(last_lines):
            # Join: NO blank line, or the earlier trailers stop parsing as trailers.
            return f"{body}\n{trailer_text}\n"

    # --- Otherwise start a NEW block, separated from the body by exactly one blank line. ---
    return f"{body}\n\n{trailer_text}\n"


def run_item_trailers(run_id: Optional[str], item_id6: Optional[str]) -> List[str]:
    """Build the canonical ``AW-Run``/``AW-Item`` trailer list, skipping any absent value.

    A convenience so callers do not hand-format the keys (and drift). Returns ``[]`` when both are
    absent, which composes to an unchanged message.

    WHERE THE VALUES MUST COME FROM (runtrailwire-01 ``wao266``, now that a real runner consumer
    exists): a LIVE RUN'S OWN STATE. ``oc_runipd.process_backlog_close`` threads ``state["run_id"]``
    and the queue item's ``id6``; ``aw commit`` takes them off a programmatic caller's namespace and
    exposes NO public flag for them, deliberately. For agent commits inside a run, the runner exports
    these ids into the agent turn's environment (``AW_RUN_ID`` and ``AW_ITEM_ID6``) where
    ``work_cmd`` reads them: still a live run's own state, written by the driver, never typed by a
    human. Like ``AW_EXECUTION_ROLE``, an environment variable is a selector a same-user process can
    set, so a trailer is a consistency record, not tamper-proof provenance. They must never come from
    a human, a timestamp, or any other synthesized source. The reason is the whole point of the
    mechanism: these trailers are IMMUTABLE once committed, so their value is exactly that a later
    reader can TRUST them, and a fabricated one makes a false ownership claim permanent. An absent
    value therefore means UNKNOWN ownership and must stay absent - which is what the skipping above
    is for, and why the tempting future change (accepting the ids from a convenience argument so a
    caller need not thread state) would be a regression rather than an improvement.
    """

    out: List[str] = []
    if run_id and str(run_id).strip():
        out.append(f"{TRAILER_KEY_RUN}: {str(run_id).strip()}")
    if item_id6 and str(item_id6).strip():
        out.append(f"{TRAILER_KEY_ITEM}: {str(item_id6).strip()}")
    return out


run_trailers = run_item_trailers

# --------------------------------------------------------------------------------------
# Agent commit identity & runner attribution (IPD yr3d4o E-02)
# --------------------------------------------------------------------------------------

_COMMITTER_NAME_MODEL_RE = re.compile(r"^AW Agent \(([^()]+)\)$")
_SCOPED_GIT_ENV: Optional[Dict[str, str]] = None


def model_from_actor(actor: Optional[str]) -> Optional[str]:
    """Extract the model component from a runner/lifecycle actor string.

    Actor strings in the runners and lifecycle have shapes such as
    ``"aw oc run model=opus"``, ``"opencode model=claude-opus-4-6"``,
    ``"opencode/claude-opus-4-6"``, ``"agy/gemini-2.5-pro"``, or ``"human/operator"``.
    Returns ``None`` for ``human/*`` or when no model token is present so
    :func:`resolve_agent_model` can fall back to ``AW_AGENT_MODEL`` or ``"unknown"``.
    """

    s = str(actor or "").strip()
    if not s or s.startswith("human/"):
        return None
    m = re.search(r"\bmodel=([^\s;,\]]+)", s)
    if m:
        return m.group(1).strip() or None
    if "/" in s:
        host, rest = s.split("/", 1)
        if host in ("opencode", "agy", "antigravity", "oc"):
            return rest.strip() or None
    return None


def sanitize_agent_model(raw: Optional[str]) -> str:
    """Sanitize a raw model name for use in ``AW Agent (<model>)`` (E-02).

    Strips newlines, carriage returns, NULs, ``<``, ``>``, and parentheses, and
    collapses whitespace so ``Gemini 3.8 Flash (High)`` becomes
    ``Gemini 3.8 Flash High``. Returns ``"unknown"`` when unset or empty.
    """

    if raw is None:
        return "unknown"
    cleaned = re.sub(r"[\r\n\x00<>()]+", " ", str(raw))
    cleaned = " ".join(cleaned.split())
    return cleaned if cleaned else "unknown"


def resolve_agent_model(
    explicit: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> str:
    """Resolve the effective model identifier with deterministic precedence (E-02).

    Precedence:
    1. Explicit ``explicit`` argument (when non-empty and not ``"unknown"``).
    2. ``AW_AGENT_MODEL`` in ``env`` (or ``os.environ`` when ``env`` is ``None``).
    3. ``GIT_COMMITTER_NAME`` matching ``^AW Agent \\(([^()]+)\\)$`` in ``env``.
    4. ``"unknown"``. Never guessed.
    """

    if explicit is not None and str(explicit).strip():
        cand = sanitize_agent_model(explicit)
        if cand != "unknown":
            return cand
    env_map: Mapping[str, str] = os.environ if env is None else env
    env_model = env_map.get(AGENT_MODEL_ENV)
    if env_model is not None and str(env_model).strip():
        cand = sanitize_agent_model(env_model)
        if cand != "unknown":
            return cand
    committer_name = (env_map.get(COMMITTER_NAME_ENV) or "").strip()
    m = _COMMITTER_NAME_MODEL_RE.match(committer_name)
    if m:
        cand = sanitize_agent_model(m.group(1))
        if cand != "unknown":
            return cand
    return "unknown"


def resolve_agent_runner(
    explicit: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Optional[str]:
    """Resolve the runner label for ``AW-Runner``, validated against ``KNOWN_RUNNERS``.

    Precedence:
    1. Explicit ``explicit`` argument.
    2. ``AW_RUNNER`` in ``env`` (or ``os.environ`` when ``env`` is ``None``).
    3. ``None`` (no ``AW-Runner`` trailer emitted when unknown).
    """

    if explicit is not None and str(explicit).strip():
        val = str(explicit).strip()
        return val if val in KNOWN_RUNNERS else None
    env_map: Mapping[str, str] = os.environ if env is None else env
    env_val = env_map.get(RUNNER_ENV)
    if env_val is not None and str(env_val).strip():
        val = str(env_val).strip()
        return val if val in KNOWN_RUNNERS else None
    return None


def tag_agent_email(raw_email: Optional[str]) -> str:
    """Tag ``raw_email`` as an ``aw`` agent committer address (E-02).

    * ``<local>@<domain>`` -> ``<local>+aw@<domain>`` when ``<local>`` has no ``+``.
    * ``<local>@<domain>`` -> ``<local>-aw@<domain>`` when ``<local>`` already contains ``+``.
    * Idempotent when ``<local>`` already ends with ``+aw`` or ``-aw``.
    * Returns ``""`` when ``raw_email`` is empty or lacks ``@`` (no committer override).
    """

    s = str(raw_email or "").strip().strip("<>").strip()
    if not s or "@" not in s:
        return ""
    local, sep, domain = s.rpartition("@")
    local = local.strip()
    domain = domain.strip()
    if not sep or not local or not domain:
        return ""
    if local.endswith("+aw") or local.endswith("-aw"):
        return f"{local}@{domain}"
    if "+" in local:
        return f"{local}-aw@{domain}"
    return f"{local}+aw@{domain}"


class AgentCommitIdentity(NamedTuple):
    """Resolved committer/author identity, trailer set, message, and subprocess env."""

    committer_name: str
    committer_email: str
    author_name: Optional[str]
    author_email: Optional[str]
    model: str
    runner: Optional[str]
    trailers: Tuple[str, ...]
    message: str
    env: Dict[str, str]


_ESSENTIAL_OS_ENV_KEYS: Tuple[str, ...] = (
    "SystemRoot",
    "WINDIR",
    "SYSTEMDRIVE",
    "PATH",
    "PATHEXT",
    "COMSPEC",
    "TEMP",
    "TMP",
    "USERPROFILE",
    "HOME",
)


def _ensure_essential_os_env(target: Dict[str, str]) -> None:
    """Ensure operating system process-execution variables are preserved.

    On Windows, CreateProcess fails with [WinError 87] (ERROR_INVALID_PARAMETER) if
    SystemRoot is missing from lpEnvironment, and executables cannot be located if
    PATH is missing. On all platforms, child processes need PATH and temp/home vars.
    When a caller passes a narrowed or empty env (e.g. base_env={} in tests to isolate
    from caller state), copy missing OS execution vars from os.environ.
    """
    for key in _ESSENTIAL_OS_ENV_KEYS:
        if key in os.environ:
            if os.name == "nt":
                key_lower = key.lower()
                if not any(k.lower() == key_lower for k in target):
                    target[key] = os.environ[key]
            elif key not in target:
                target[key] = os.environ[key]


def _git_config_get(
    repo_root: Path,
    key: str,
    *,
    env: Optional[Mapping[str, str]] = None,
) -> Optional[str]:
    """Read a single ``git config --get <key>`` value using ``_REAL_POPEN``.

    Uses ``_REAL_POPEN`` directly so unit tests that patch ``subprocess.Popen`` around
    runner turns or spy on ``_git`` do not intercept internal git-config lookups.
    """

    cwd_path: Optional[str] = None
    try:
        if repo_root and repo_root.is_dir():
            cwd_path = str(repo_root)
        elif repo_root and repo_root.parent.is_dir():
            cwd_path = str(repo_root.parent)
    except OSError:
        cwd_path = None

    proc_env: Optional[Dict[str, str]] = None
    if env is not None:
        proc_env = dict(env)
        _ensure_essential_os_env(proc_env)

    try:
        proc = _REAL_POPEN(
            ["git", "config", "--get", key],
            cwd=cwd_path,
            env=proc_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        out, _err = proc.communicate(timeout=5)
        if proc.returncode == 0 and out:
            val = out.strip()
            return val if val else None
    except Exception:
        return None
    return None


_EXISTING_AW_TRAILER_KEY_RE = re.compile(r"(?m)^(AW-Runner|AW-Run|AW-Item)[ \t]*:")


def _compose_identity_message(message: str, ident_trailers: Sequence[str]) -> str:
    """Compose ``message`` with ``ident_trailers`` without duplicating existing ``AW-*`` keys (E-02).

    Never adds an ``AW-Runner``, ``AW-Run``, or ``AW-Item`` trailer whose key is already
    present in ``message`` (e.g. ``commit_review_lane_output`` already stamps ``AW-Run`` /
    ``AW-Item`` and ``AW-Committed-By: driver``).
    """

    cleaned_ident = [validate_trailer(t) for t in ident_trailers]
    if not cleaned_ident:
        return message

    existing_keys = set(_EXISTING_AW_TRAILER_KEY_RE.findall(message or ""))
    to_add: List[str] = []
    for t in cleaned_ident:
        key = t.split(":", 1)[0].strip()
        if key not in existing_keys:
            to_add.append(t)
            existing_keys.add(key)

    if not to_add:
        return message
    return compose_message_with_trailers(message, to_add)


_ENV_RUN_ID_RE = re.compile(r"^run-[A-Za-z0-9_-]+$")
_ENV_ITEM_ID6_RE = re.compile(r"^[a-z0-9]{6}$")


def agent_commit_identity(
    repo_root: Path,
    *,
    model: Optional[str] = None,
    runner: Optional[str] = None,
    run_id: Optional[str] = None,
    item_id6: Optional[str] = None,
    message: Optional[str] = None,
    base_env: Optional[Mapping[str, str]] = None,
) -> AgentCommitIdentity:
    """Resolve the agent committer identity, signing override, trailers, and git env (E-02).

    * COMMITTER NAME: ``AW Agent (<model>)``, where ``<model>`` is resolved by
      :func:`resolve_agent_model` and never guessed.
    * COMMITTER EMAIL: user's email from ``GIT_AUTHOR_EMAIL`` or ``git config user.email``
      in ``repo_root`` tagged via :func:`tag_agent_email`. When no user email is configured
      or it lacks ``@``, sets no committer override in ``env``.
    * AUTHOR: never set by this helper, so git's normal author identity applies.
    * SIGNING: when ``commit.gpgsign=true`` and ``user.signingkey`` is unset in ``repo_root``,
      appends ``GIT_CONFIG_COUNT``/``GIT_CONFIG_KEY_<n>=user.signingkey``/
      ``GIT_CONFIG_VALUE_<n>=<Name <email>>`` so ``gpg`` signs with the user's key rather
      than looking up a key for the ``+aw`` committer address.
    * TRAILERS: ``AW-Runner: <runner>`` (when known), plus ``AW-Run`` and ``AW-Item`` when
      present, never duplicating a key ``message`` already carries.
    """

    env_in: Dict[str, str] = dict(os.environ if base_env is None else base_env)

    cfg_name = _git_config_get(repo_root, "user.name", env=env_in)
    cfg_email = _git_config_get(repo_root, "user.email", env=env_in)
    cfg_gpgsign = _git_config_get(repo_root, "commit.gpgsign", env=env_in)
    cfg_signingkey = _git_config_get(repo_root, "user.signingkey", env=env_in)

    author_name = (env_in.get("GIT_AUTHOR_NAME") or "").strip() or cfg_name or None
    raw_email = (env_in.get("GIT_AUTHOR_EMAIL") or "").strip() or cfg_email or None
    author_email = raw_email

    committer_email = tag_agent_email(raw_email)
    resolved_model = resolve_agent_model(model, env=env_in)
    committer_name = f"AW Agent ({resolved_model})" if committer_email else ""
    resolved_runner = resolve_agent_runner(runner, env=env_in)

    if run_id is not None and str(run_id).strip():
        resolved_run_id: Optional[str] = str(run_id).strip()
    else:
        env_run = (env_in.get(RUN_ID_ENV) or "").strip()
        resolved_run_id = env_run if _ENV_RUN_ID_RE.match(env_run) else None

    if item_id6 is not None and str(item_id6).strip():
        resolved_item_id6: Optional[str] = str(item_id6).strip()
    else:
        env_item = (env_in.get(ITEM_ID6_ENV) or "").strip()
        resolved_item_id6 = env_item if _ENV_ITEM_ID6_RE.match(env_item) else None

    t_list: List[str] = []
    if resolved_runner:
        t_list.append(f"{TRAILER_KEY_RUNNER}: {resolved_runner}")
    t_list.extend(run_item_trailers(resolved_run_id, resolved_item_id6))
    trailers_tuple: Tuple[str, ...] = tuple(t_list)

    out_message = (
        _compose_identity_message(message, trailers_tuple)
        if message is not None
        else ""
    )

    out_env: Dict[str, str] = dict(env_in)
    if committer_email:
        out_env[COMMITTER_NAME_ENV] = committer_name
        out_env[COMMITTER_EMAIL_ENV] = committer_email

        # When commit.gpgsign is true and user.signingkey is unset, point user.signingkey
        # at the user's own ident so gpg requests the user's key, not the +aw address (E-02, F-09).
        if (cfg_gpgsign or "").strip().lower() in (
            "true",
            "1",
            "yes",
            "on",
        ) and not (cfg_signingkey or "").strip():
            user_ident = (
                f"{author_name} <{raw_email}>" if author_name else f"<{raw_email}>"
            )
            try:
                count = int(out_env.get("GIT_CONFIG_COUNT", "0") or "0")
            except ValueError:
                count = 0
            already_set = any(
                out_env.get(f"GIT_CONFIG_KEY_{i}") == "user.signingkey"
                for i in range(max(count, 0))
            )
            if not already_set:
                out_env[f"GIT_CONFIG_KEY_{count}"] = "user.signingkey"
                out_env[f"GIT_CONFIG_VALUE_{count}"] = user_ident
                out_env["GIT_CONFIG_COUNT"] = str(count + 1)

    return AgentCommitIdentity(
        committer_name=committer_name,
        committer_email=committer_email,
        author_name=author_name,
        author_email=author_email,
        model=resolved_model,
        runner=resolved_runner,
        trailers=trailers_tuple,
        message=out_message,
        env=out_env,
    )


def export_agent_child_env(
    child_env: Dict[str, str],
    repo_root: Path,
    *,
    model: Optional[str],
    runner: Optional[str],
) -> Dict[str, str]:
    """Populate ``child_env`` with agent committer identity and runner/model env vars (E-04).

    Applies the same overwrite-or-pop discipline as ``AW_RUN_ID`` / ``AW_ITEM_ID6`` so an
    outer run's identity never leaks into a nested driver when values are absent.
    """

    ident = agent_commit_identity(
        repo_root,
        model=model,
        runner=runner,
        base_env=child_env,
    )
    if ident.committer_email:
        child_env.update(ident.env)
    else:
        child_env.pop(COMMITTER_NAME_ENV, None)
        child_env.pop(COMMITTER_EMAIL_ENV, None)

    if ident.runner:
        child_env[RUNNER_ENV] = ident.runner
    elif runner and str(runner).strip() in KNOWN_RUNNERS:
        child_env[RUNNER_ENV] = str(runner).strip()
    else:
        child_env.pop(RUNNER_ENV, None)

    if model is not None and str(model).strip():
        sanitized = sanitize_agent_model(model)
        if sanitized != "unknown":
            child_env[AGENT_MODEL_ENV] = sanitized
        else:
            child_env.pop(AGENT_MODEL_ENV, None)
    elif ident.model != "unknown":
        child_env[AGENT_MODEL_ENV] = ident.model
    else:
        child_env.pop(AGENT_MODEL_ENV, None)
    return child_env


def _accepts_kwarg(fn: Any, kw_name: str) -> bool:
    """Return True if ``fn`` (or its callable ``side_effect``) accepts ``kw_name`` or ``**kwargs``."""

    target = fn
    side_effect = getattr(fn, "side_effect", None)
    if callable(side_effect):
        target = side_effect
    try:
        sig = inspect.signature(target)
    except (TypeError, ValueError):
        return False
    for param in sig.parameters.values():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True
        if param.name == kw_name and param.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            return True
    return False


def _accepts_env_kwarg(fn: Any) -> bool:
    """Return True if ``fn`` accepts an ``env`` keyword argument (or ``**kwargs``)."""

    return _accepts_kwarg(fn, "env")


def call_git_with_env(
    git_fn: Any,
    repo_root: Path,
    args: List[str],
    env: Optional[Mapping[str, str]] = None,
) -> Tuple[int, str, str]:
    """Call ``git_fn(repo_root, args)`` with ``env``, supporting 2-arg test spies."""

    global _SCOPED_GIT_ENV
    prev_env = _SCOPED_GIT_ENV
    _SCOPED_GIT_ENV = dict(env) if env is not None else prev_env
    try:
        if env is not None and _accepts_env_kwarg(git_fn):
            return git_fn(repo_root, args, env=env)
        return git_fn(repo_root, args)
    finally:
        _SCOPED_GIT_ENV = prev_env


# Outcome status literals (kept as plain strings so callers/tests can compare directly).
STATUS_COMMITTED = "committed"
STATUS_SKIPPED = "skipped"
STATUS_DECLINED = "declined"
STATUS_REFUSED_DIRTY = "refused-dirty"
STATUS_NOTHING_TO_COMMIT = "nothing-to-commit"
STATUS_ERROR = "error"

#: Maximum attempts for ISO_RACED compare-and-swap retries (E-06).
ISO_RACED_MAX_ATTEMPTS: int = 5


class CommitOutcome(NamedTuple):
    """Structured result of an :func:`offer_commit` attempt.

    ``status`` is one of the ``STATUS_*`` literals. ``commit`` is the new HEAD sha on
    ``committed``, else ``None``. ``staged`` is the exact repo-relative path set that was
    staged/committed (subset of the requested ``paths`` that actually existed/were tracked).
    ``message`` is a human-readable explanation (used for warnings/errors).

    ``hook_fixed`` names the paths a MUTATING pre-commit hook rewrote, which the isolated commit then
    landed on a single retry (see :func:`commit_lock.commit_isolated`), and
    ``hook_fixed_diverged`` the subset whose working-tree copy was left holding a PEER's content
    instead of the committed bytes. Reporting them is deliberate: a retry commits content the caller
    did not write, so absorbing it silently would hide a mutation. Both are APPENDED with defaults,
    because this is a ``NamedTuple`` that callers unpack positionally as well as by name.

    ``abandoned`` carries the sequence of stranded commit shas retained under
    ``refs/aw/abandoned/isolated/`` across all attempts in an ``ISO_RACED`` retry loop (E-04).
    Appended with empty default tuple for positional contract compatibility.
    """

    status: str
    commit: Optional[str]
    staged: Tuple[str, ...]
    message: str
    hook_fixed: Tuple[str, ...] = ()
    hook_fixed_diverged: Tuple[str, ...] = ()
    abandoned: Tuple[str, ...] = ()


def lockfree_git_argv(args: Sequence[str]) -> List[str]:
    """``["git", *args]``, with ``--no-optional-locks`` inserted for a read-only ``status``.

    ``git status`` opportunistically refreshes the index and so takes ``<git-dir>/index.lock``; a
    process killed in that window (a timeout, a test hang guard, a cancelled agent) strands a 0-byte
    lock that refuses the NEXT commit in that checkout. ``--no-optional-locks`` makes status
    read-only. Only the first non-option word is inspected, so every mutating command is untouched.
    Single shared definition so each git wrapper in the package applies the same rule.
    """

    argv = list(args)
    i = 0
    while i < len(argv) and argv[i].startswith("-"):
        i += 2 if argv[i] in ("-C", "-c") else 1
    if i < len(argv) and argv[i] == "status" and "--no-optional-locks" not in argv[:i]:
        return ["git", "--no-optional-locks", *argv]
    return ["git", *argv]


def _git(
    repo_root: Path,
    args: List[str],
    *,
    env: Optional[Mapping[str, str]] = None,
) -> Tuple[int, str, str]:
    """Run a git command in ``repo_root``; return (returncode, stdout, stderr).

    The single canonical git-subprocess wrapper for the codebase; ``ipd_lifecycle._git``
    delegates here so there is no duplicated runner. When ``env`` is provided (or scoped via
    :func:`call_git_with_env`), passes that environment mapping to the ``git`` subprocess.
    """

    effective_env = env if env is not None else _SCOPED_GIT_ENV
    sub_env: Optional[Dict[str, str]] = None
    if effective_env is not None:
        sub_env = dict(effective_env)
        _ensure_essential_os_env(sub_env)
    proc = subprocess.run(
        lockfree_git_argv(args),
        cwd=str(repo_root),
        env=sub_env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _is_interactive(interactive: Optional[bool] = None) -> bool:
    """Resolve the effective interactivity.

    ``interactive`` explicitly overrides (used by tests and callers that already know the
    channel); ``None`` falls back to :func:`agent_workflows.term.is_interactive`.
    """

    # An explicit argument represents a programmatic caller's statement about a channel it
    # already knows (e.g. runner_shared passing interactive=False, or a test driving interactive=True),
    # rather than an operator's ambient flag wish (--interactive) that CI must be allowed to veto.
    # Therefore an explicit boolean is returned directly, while None delegates to the four-rung
    # resolver in term.is_interactive.
    if interactive is not None:
        return bool(interactive)

    from agent_workflows import term as _term

    return _term.is_interactive(override=None)


def _prompt(message: str, paths: Sequence[str]) -> bool:
    """Tiny ``[Y/n]`` yes/no render, equivalent to ``cli._confirm``'s interactive branch.

    Reimplemented locally (NOT imported from ``cli``) to keep this a leaf module. Only ever
    called when already known-interactive; an empty answer defaults to YES, while an EOF or
    explicit 'n'/'no' is a safe NO.
    """

    shown = "\n".join(f"  {p}" for p in paths)
    prompt = f"{message}\n{shown}\nCommit these path-scoped changes? [Y/n] "
    try:
        answer = input(prompt).strip().lower()
    except EOFError:
        return False
    return answer in ("", "y", "yes")


def _staged_paths(repo_root: Path) -> List[str]:
    """Repo-relative paths currently in the index (staged), rename-aware: BOTH SIDES of a rename.

    THE BUG THIS FIXES, measured 2026-09-22 across 36 corrupted backlog items. This function used
    `git diff --name-only --cached`, which for a STAGED RENAME prints ONLY THE DESTINATION. The
    docstring already claimed "rename-aware" and the implementation was not. Two things in
    :func:`offer_commit` read this set, and for a rename the second one silently dropped half the
    move:

      * `our_staged = now_staged & set(rel_paths)` keeps only paths git reported, so a caller that
        correctly named BOTH sides of its own `git mv` got the SOURCE filtered out; and
      * the commit is then `git commit -- <our_staged>`, which commits the addition WITHOUT the
        paired deletion, leaving the source file both present in HEAD and staged-for-deletion.

    MEASURED CONSEQUENCE, which is why this is a data-integrity fix and not a tidiness one. Every
    `aw oc run` backlog close routes here via `oc_runipd.commit_backlog_close`. `status_set` had
    already been fixed (2026-09-13) to relocate with `git mv` precisely so the move would be ONE
    staged rename with "no halves to pair up and no half to lose" - but this function then lost the
    half anyway. Result: 36 items whose id6 exists in TWO status directories at once (e.g. `bplplj`
    in both `graduated/` and `done/`), each created by a commit containing `A done/...` and no
    `D graduated/...`, which `aw attention` correctly reports as `attention.duplicate-id` and which
    made its whole board non-authoritative ("VIEW INVALID"). The uncommitted deletion was still
    sitting in the originating lane worktree days later.

    `--name-status -z` IS THE FIX rather than post-processing `--name-only`: a rename record carries
    BOTH paths, and the NUL form is used because a rename record is itself NUL-separated
    (`R<score>\\0<old>\\0<new>`) and a path may legitimately contain whitespace, so splitting on
    whitespace would corrupt exactly the paths this repository's artifact names are full of.

    Returning BOTH sides is correct for both readers. `pre_staged` (the unrelated-staged check)
    becomes MORE accurate, because a rename's source genuinely IS staged content; and `our_staged`
    now contains whatever the caller legitimately named, so a caller that names one side alone is
    unaffected while a caller that names both gets an atomic move. A path this function reports is
    never force-added and never staged by it: this is a READ.
    """

    rc, out, _err = _git(repo_root, ["diff", "--name-status", "--cached", "-z"])
    if rc != 0:
        return []
    fields = [f for f in out.split("\0") if f != ""]
    paths: List[str] = []
    i = 0
    while i < len(fields):
        status = fields[i]
        # A rename/copy status is `R<score>`/`C<score>` and consumes TWO path fields (old, new);
        # every other status consumes one. Guard the index arithmetic so a truncated or unexpected
        # record cannot raise mid-commit: this runs inside the stage+commit window.
        if status[:1] in ("R", "C"):
            for candidate in fields[i + 1 : i + 3]:
                if candidate and candidate not in paths:
                    paths.append(candidate)
            i += 3
            continue
        if i + 1 < len(fields):
            candidate = fields[i + 1]
            if candidate and candidate not in paths:
                paths.append(candidate)
        i += 2
    return paths


def _contained_files(repo_root: Path, dir_paths: Sequence[str]) -> List[str]:
    """Repo-relative paths of changed/untracked files inside ``dir_paths``.

    Uses ``git status --porcelain -z -uall`` so untracked directories are expanded to individual
    files (F-8) while respecting .gitignore, without forcing or staging anything.
    """

    if not dir_paths:
        return []
    rc, out, _err = _git(
        repo_root, ["status", "--porcelain", "-z", "-uall", "--", *dir_paths]
    )
    if rc != 0 or not out:
        return []
    entries = out.split("\0")
    files: List[str] = []
    i = 0
    while i < len(entries):
        entry = entries[i]
        if not entry:
            i += 1
            continue
        if len(entry) >= 3:
            status = entry[:2]
            path = entry[3:]
            if path and path not in files:
                files.append(path)
            # If status is rename/copy (R or C), the next field is the old path
            if status[0] in ("R", "C") or status[1] in ("R", "C"):
                i += 1
                if i < len(entries) and entries[i]:
                    old_path = entries[i]
                    if old_path not in files:
                        files.append(old_path)
        i += 1
    return files


def _in_index(repo_root: Path, rel_path: str) -> bool:
    """Whether the index still holds an entry for ``rel_path``.

    Distinguishes the two reasons a path can be absent from the WORKING TREE, which `git add` treats
    very differently. A tracked file the caller DELETED is still in the index, so `git add -- <path>`
    correctly stages that deletion. A file that was moved with `git mv` is NOT in the index at its old
    location (the rename is already staged), so naming it makes `git add` fail with "pathspec did not
    match any files" AND stage nothing else in the same invocation.

    `git ls-files --error-unmatch` is the direct question and needs no output parsing: it exits 0 when
    the index has the entry and nonzero when it does not.
    """

    rc, _out, _err = _git(repo_root, ["ls-files", "--error-unmatch", "--", rel_path])
    return rc == 0


def _ignored_paths(repo_root: Path, rel_paths: Sequence[str]) -> List[str]:
    """Subset of ``rel_paths`` that ``git add`` would REFUSE because .gitignore excludes them.

    Exists because ``git add -- <ignored-path>`` is NOT tolerant: it exits 1 and stages NOTHING,
    including the non-ignored paths in the same invocation, so one generated-and-now-gitignored
    file in a mixed path-set would take the REAL artifact's commit down with it (measured
    2026-09-06; see :func:`offer_commit`).

    The predicate is ``git check-ignore``, which was measured to agree EXACTLY with ``git add``'s
    refusal condition: it reports a path ignored only when the path is untracked AND matched by an
    ignore rule. In particular it does NOT report a path that is TRACKED but happens to match a
    pattern (git honors the index over .gitignore there, and ``git add`` accepts it), nor a
    tracked DELETION of such a path, so filtering on this predicate cannot silently drop a real
    change. A nonexistent path is likewise not reported, and is left in the set so that git's own
    "pathspec did not match" error still surfaces rather than being swallowed here.

    Returns an empty list on any git failure: the filter is a safety net, and a broken probe must
    not itself start dropping paths.
    """

    if not rel_paths:
        return []
    # Batch form: one subprocess regardless of path count. -z keeps paths with spaces intact.
    proc = subprocess.run(
        ["git", "check-ignore", "-z", "--stdin"],
        cwd=str(repo_root),
        input="\0".join(rel_paths) + "\0",
        capture_output=True,
        text=True,
    )
    # rc 0 = at least one path ignored, 1 = none ignored, >1 = real error.
    if proc.returncode > 1:
        return []
    ignored = {p for p in proc.stdout.split("\0") if p}
    return [p for p in rel_paths if p in ignored]


def _normalize(paths: Sequence[str], repo_root: Path) -> List[str]:
    """Coerce the caller's paths to repo-relative POSIX strings, de-duplicated, order-stable."""

    seen: dict = {}
    root = repo_root.resolve()
    for p in paths:
        pp = Path(p)
        if pp.is_absolute():
            try:
                rel = pp.resolve().relative_to(root).as_posix()
            except ValueError:
                rel = pp.as_posix()
        else:
            rel = pp.as_posix()
        rel = rel.strip()
        if rel:
            seen.setdefault(rel, None)
    return list(seen.keys())


def offer_commit(
    repo_root: Path,
    paths: Sequence[str],
    *,
    message: str,
    assume_yes: bool = False,
    no_commit: bool = False,
    interactive: Optional[bool] = None,
    on_unrelated_staged: str = "scope",
    trailers: Sequence[str] = (),
    model: Optional[str] = None,
    runner: Optional[str] = None,
    run_id: Optional[str] = None,
    item_id6: Optional[str] = None,
) -> CommitOutcome:
    """Offer to commit ONLY ``paths`` (path-scoped), enforcing the repo contract.

    Parameters
    ----------
    repo_root:
        Repository root the git commands run in.
    paths:
        The exact files the caller touched (repo-relative or absolute), including deletions and
        renames. ONLY these are ever staged (``git add -- <paths>``), and a path that .gitignore
        EXCLUDES is dropped from the staging set first, with a note naming it on stderr (see
        below). Callers must therefore not rely on a generated, gitignored file being committed
        here.

        DIRECTORY ARGUMENTS ARE REFUSED BEFORE STAGING (``STATUS_ERROR``), naming the contained
        files so the corrected invocation is copy-pasteable. Siting the refusal ahead of staging
        guarantees that a refused call leaves the index untouched (no mutation, no rollback).
    message:
        Commit message. Never combined with ``--no-verify``; the commit is path-scoped
        (``git commit -- <paths>``) and is never pushed.
    assume_yes:
        The ``--commit`` flag. When true, commit without prompting (the only way to commit
        non-interactively).
    no_commit:
        The ``--no-commit`` escape hatch. Short-circuits to ``skipped`` regardless of TTY, except
        for a directory argument which refuses with ``error`` even under preview.
    interactive:
        Explicit interactivity override (used by tests and programmatic callers);
        ``None`` delegates to :func:`agent_workflows.term.is_interactive`, which requires
        both stdin and the output stream to be a TTY and honors ``AW_NONINTERACTIVE``/``CI``.
    on_unrelated_staged:
        Policy when the index already holds staged paths OUTSIDE ``paths``:
        ``"scope"`` (default) commits only ``paths`` and leaves the rest staged-but-uncommitted;
        ``"refuse"`` returns ``refused-dirty`` and commits nothing. In BOTH modes a path outside
        ``paths`` is NEVER staged by this helper.
    trailers:
        Optional Git trailers (``"Key: value"`` strings) appended to ``message`` as a trailer
        block, e.g. ``["AW-Run: run-...", "AW-Item: m73aet"]`` so a checker can tell which run and
        work item produced the commit. DEFAULTS EMPTY, in which case the message is used
        byte-for-byte unchanged. Affects the MESSAGE only - never the staging, scoping, or rollback
        behavior. A structurally unparseable trailer returns an ``error`` outcome and commits
        NOTHING, rather than creating a commit whose trailers silently do not parse. See
        :func:`compose_message_with_trailers`.

    Returns
    -------
    CommitOutcome
        ``committed`` (with the new sha; reports any named paths that had nothing to commit),
        ``skipped`` (gate declined it non-interactively or ``no_commit`` for non-directory paths),
        ``declined`` (interactive user said no), ``refused-dirty`` (``on_unrelated_staged="refuse"``
        and the index held unrelated staged paths), ``nothing-to-commit`` (no requested path exists/changed,
        or EVERY requested path is gitignored), or ``error`` (e.g. a directory argument was passed,
        which refuses even under ``no_commit``; the ``no_commit`` short-circuit still precedes other
        post-staging/dirty checks so a preview is not a general oracle).

    Notes
    -----
    GITIGNORED PATHS ARE FILTERED, NOT FORCED. ``git add -- <ignored-path>`` exits 1 and stages
    NOTHING AT ALL, so a single gitignored entry in an otherwise valid path-set made this helper
    return ``error`` and create no commit, losing the real artifact's commit too (measured
    2026-09-06). Such paths are therefore dropped BEFORE staging and reported by name; the
    remaining paths commit normally. Nothing is ever force-added: a path the repository has
    chosen to ignore is one it has chosen not to track. See :func:`_ignored_paths` for why the
    predicate cannot drop a tracked file or a tracked deletion.
    """

    if on_unrelated_staged not in ("scope", "refuse"):
        raise ValueError(
            f"on_unrelated_staged must be 'scope' or 'refuse', got {on_unrelated_staged!r}"
        )

    # Compose the message BEFORE touching the index: a malformed trailer must abort with nothing
    # staged, not leave a half-prepared index behind. With no trailers this returns `message` itself.
    try:
        full_message = compose_message_with_trailers(message, trailers)
    except TrailerError as exc:
        return CommitOutcome(STATUS_ERROR, None, (), f"invalid trailer: {exc}")

    rel_paths = _normalize(paths, repo_root)
    if not rel_paths:
        return CommitOutcome(
            STATUS_NOTHING_TO_COMMIT, None, (), "no paths given to commit"
        )

    # --- Refuse directory arguments BEFORE staging and BEFORE no_commit (OQ-01 / F-6 / F-7 / IPD o39zn9). ---
    # A directory argument is staged by `git add -- <dir>`, but git reports the contained FILES at
    # `_staged_paths`, so `our_staged = now_staged & set(rel_paths)` drops them. That dropped the
    # destination of records moves and committed deletions alone (ca8e22e4 / F-1 / F-2). An
    # all-directories call returned `nothing-to-commit` having already staged the full move with no
    # rollback (F-6). Refusing BEFORE staging ensures the index remains untouched.
    #
    # Sited before `no_commit` so a dry-run preview discovers the refusal instead of reporting a
    # misleading `skipped: --no-commit requested` (a dry run that cannot see a refusal is worse than
    # no dry run, because it is read as a clean result). Still sited before any staging so a refused
    # call leaves the index untouched.
    #
    # The predicate catches paths that ARE or WERE directories: `(repo_root / p).is_dir()` checks the
    # filesystem (live or untracked directories), while `_contained_files` checks git status for paths
    # whose contents were deleted or moved away (the emptied-directory records move shape). An emptied
    # directory does not exist on disk, but git knows its deleted contents; without this git-derived
    # branch, a mixed call naming an emptied directory commits the file half and leaves staged deletions
    # behind in the shared index (F-11). Deleted plain files must NOT match, so we ensure the contained
    # set is not exactly `[p]` itself.
    dir_paths = []
    for p in rel_paths:
        target = repo_root / p
        if target.is_dir():
            dir_paths.append(p)
        elif not target.exists():
            contained = _contained_files(repo_root, [p])
            if contained and contained != [p]:
                dir_paths.append(p)
    if dir_paths:
        contained = _contained_files(repo_root, dir_paths)
        hint = f": {', '.join(contained)}" if contained else ""
        return CommitOutcome(
            STATUS_ERROR,
            None,
            (),
            f"refusing directory argument(s): {', '.join(dir_paths)}; name explicit file path(s) instead{hint}",
        )

    if no_commit:
        return CommitOutcome(STATUS_SKIPPED, None, (), "skipped: --no-commit requested")

    # --- Drop gitignored paths BEFORE staging (never force-add them). ---
    # A single ignored path makes `git add` exit 1 having staged NOTHING, which previously turned
    # into `error` and no commit at all, silently losing the real artifact's commit. Degrade to
    # "that one path is not committed" instead, and say which.
    ignored = _ignored_paths(repo_root, rel_paths)
    if ignored:
        print(
            "note: not committing gitignored path(s): " + ", ".join(ignored),
            file=sys.stderr,
        )
        rel_paths = [p for p in rel_paths if p not in set(ignored)]
        if not rel_paths:
            return CommitOutcome(
                STATUS_NOTHING_TO_COMMIT,
                None,
                (),
                "nothing to commit: every requested path is gitignored: "
                + ", ".join(ignored),
            )

    # --- Unrelated pre-staged content: decide BEFORE we stage anything. ---
    pre_staged = set(_staged_paths(repo_root))
    unrelated_staged = sorted(pre_staged - set(rel_paths))
    if unrelated_staged and on_unrelated_staged == "refuse":
        return CommitOutcome(
            STATUS_REFUSED_DIRTY,
            None,
            (),
            "refusing to commit: unrelated staged changes present: "
            + ", ".join(unrelated_staged),
        )

    # --- TTY gate (matches cli._confirm's ACTUAL behavior: decline on non-TTY w/o assume_yes). ---
    if assume_yes:
        proceed = True
    elif _is_interactive(interactive):
        proceed = _prompt(
            "The following path-scoped changes are ready to commit:", rel_paths
        )
        if not proceed:
            return CommitOutcome(
                STATUS_DECLINED, None, (), "declined: user answered no at prompt"
            )
    else:
        # Non-interactive without --commit/assume_yes: NO-OP (never commit silently).
        return CommitOutcome(
            STATUS_SKIPPED,
            None,
            (),
            "skipped: non-interactive; pass --commit to commit these changes",
        )

    # --- Serialize the stage+commit window against every other self-committing `aw` verb. ---
    # MEASURED HARM (2026-09-06): `pre-commit` stashes unstaged changes, runs hooks, then restores the
    # stash OVER whatever is on disk, so a peer process writing a tracked file inside that window has
    # its write DESTROYED (not in `git stash`, not in the patch file). Holding the shared writer lock
    # for the whole window stops OUR verbs from being that peer. It is not a guarantee: a hand-run
    # `git commit` or an editor-on-save is outside this lock, which is why every failure path below
    # still fails closed. See `commit_lock` for the reproduction and the honest limit.
    from agent_workflows import commit_lock as _lock

    try:
        with _lock.writer_lock(repo_root, owner="git_commit_helper.offer_commit"):
            # --- Stage ONLY the requested paths (never -A/-a). ---
            # git add -- <path> on a deleted path stages the deletion; a nonexistent, never-tracked
            # path would error, so we let git report it and surface as an error outcome.
            #
            # AN ALREADY-STAGED RENAME'S SOURCE IS NEITHER. Relocating callers now use `git mv`
            # (`artifact_core.git_mv`), which STAGES the rename, so the OLD path is already in the index
            # and is gone from disk. `git add` on it fails "pathspec did not match any files", which took
            # the WHOLE commit down (git add stages nothing on failure) and left the move half-committed:
            # measured 2026-09-13, commit `52837644` holds the addition alone and the unstaged deletion it
            # left behind refused 27 of 42 items in run `run-20260913T031350Z-1732436`.
            # Such a path needs no `git add` at all, so drop it from the ADD set while keeping it in
            # `rel_paths` for the staged-intersection and commit steps below.
            #
            # THE TEST IS "GONE FROM DISK AND ALREADY GONE FROM HEAD'S WORKING SET", i.e. a path that no
            # longer exists and that the index no longer has an entry for. Do NOT test membership in
            # `_staged_paths()`: for a staged rename git reports only the DESTINATION there, so the source
            # is absent from it and a `p not in _staged_paths()` test wrongly keeps the source in the ADD
            # set, which is the same failure with extra steps (measured while writing this fix).
            add_paths = [
                p
                for p in rel_paths
                if (repo_root / p).exists() or _in_index(repo_root, p)
            ]
            if add_paths:
                rc, _out, err = _git(repo_root, ["add", "--", *add_paths])
                if rc != 0:
                    # Roll back any partial staging of OUR paths so we leave the index as we found it.
                    _git(repo_root, ["reset", "--quiet", "HEAD", "--", *rel_paths])
                    return CommitOutcome(
                        STATUS_ERROR, None, (), f"git add failed: {err.strip()}"
                    )

            # Which of our requested paths actually ended up staged (existed / had a diff)?
            now_staged = set(_staged_paths(repo_root))
            our_staged = sorted(now_staged & set(rel_paths))
            if not our_staged:
                # Nothing of ours changed (already committed / identical); no empty commit.
                # Roll back any unexpected staging residue to restore the pre-call index state (F-6).
                residue = sorted(now_staged - pre_staged)
                if residue:
                    _git(repo_root, ["reset", "--quiet", "HEAD", "--", *residue])
                    return CommitOutcome(
                        STATUS_NOTHING_TO_COMMIT,
                        None,
                        (),
                        f"nothing to commit: requested path(s) had no staged changes ({', '.join(rel_paths)}); reset staged residue: {', '.join(residue)}",
                    )
                return CommitOutcome(
                    STATUS_NOTHING_TO_COMMIT,
                    None,
                    (),
                    f"nothing to commit: requested path(s) have no staged changes ({', '.join(rel_paths)})",
                )

            # --- Path-scoped commit, performed in an ISOLATED worktree. ---
            # Never --no-verify, never push. The isolation is what protects a CONCURRENT WRITER:
            # committing here would let pre-commit stash the SHARED tree and then restore over a peer's
            # in-flight edit, destroying it (measured). `commit_isolated` runs the SAME hooks in a private
            # worktree instead, and advances the branch under a compare-and-swap.
            ident = agent_commit_identity(
                repo_root,
                model=model,
                runner=runner,
                run_id=run_id,
                item_id6=item_id6,
                message=full_message,
            )
            full_message = ident.message

            def _call_commit_isolated() -> Any:
                if _accepts_kwarg(_lock.commit_isolated, "model"):
                    return _lock.commit_isolated(
                        repo_root,
                        our_staged,
                        message=full_message,
                        model=model,
                        runner=runner,
                        run_id=run_id,
                        item_id6=item_id6,
                    )
                return _lock.commit_isolated(
                    repo_root, our_staged, message=full_message
                )

            iso = _call_commit_isolated()

            # E-06: ISO_RACED_MAX_ATTEMPTS is a deliberate COST bound from plan 9bq5o4
            # ("each attempt re-runs the FULL pre-commit hook set in a fresh worktree").
            # It is NOT to be raised to make this arm rarer: each attempt runs inside
            # the shared writer lock, so a longer loop holds that lock and blocks every other
            # aw verb across the repository.
            abandoned_shas: list = list(getattr(iso, "abandoned", ()))

            if iso.status == _lock.ISO_RACED:
                # Another commit moved HEAD between snapshot and compare-and-swap.
                # Re-attempt the isolated commit on the new tip, bounded by wall time and an attempt cap.
                from agent_workflows import contention_wait

                raced_attempts = 1

                def _try_raced_commit() -> tuple[bool, Any]:
                    nonlocal iso, raced_attempts
                    if raced_attempts >= ISO_RACED_MAX_ATTEMPTS:
                        return True, iso
                    raced_attempts += 1
                    iso = _call_commit_isolated()
                    if getattr(iso, "abandoned", ()):
                        abandoned_shas.extend(iso.abandoned)
                    if iso.status == _lock.ISO_COMMITTED:
                        return True, iso
                    if iso.status == _lock.ISO_RACED:
                        return False, iso
                    return True, iso

                def _holder_fn() -> Optional[str]:
                    rc, out, _ = _git(repo_root, ["rev-parse", "--short", "HEAD"])
                    return f"new tip {out.strip()}" if rc == 0 and out.strip() else None

                contention_wait.wait_until(
                    _try_raced_commit,
                    what="isolated commit compare-and-swap on new tip",
                    holder=_holder_fn,
                    timeout=contention_wait.TIMEOUT_SECONDS,
                    poll=contention_wait.POLL_SECONDS,
                    report_every=contention_wait.REPORT_SECONDS,
                )

            if iso.status == _lock.ISO_COMMITTED:
                # A MUTATING hook may have rewritten our own paths and had the commit retried once
                # (`commit_isolated`). Say so rather than reporting a bare success: the committed bytes are
                # then the HOOK's, not exactly what the caller wrote, and an operator who is not told that
                # has no way to notice.
                shortfall = [p for p in rel_paths if p not in set(our_staged)]
                shortfall_note = (
                    f" ({len(shortfall)} path(s) had nothing to commit: {', '.join(shortfall)})"
                    if shortfall
                    else ""
                )
                note = ""
                if iso.hook_fixed:
                    note = (
                        f" (the pre-commit hooks fixed {', '.join(iso.hook_fixed)} and the commit "
                        "succeeded on a single retry)"
                    )
                if iso.hook_fixed_diverged:
                    note += (
                        f" NOTE: {', '.join(iso.hook_fixed_diverged)} was changed by another writer "
                        "during the commit, so the working tree keeps THEIR content"
                    )
                return CommitOutcome(
                    STATUS_COMMITTED,
                    iso.commit,
                    tuple(our_staged),
                    f"committed {len(our_staged)} path(s) as {iso.commit}{note}{shortfall_note}",
                    tuple(iso.hook_fixed),
                    tuple(iso.hook_fixed_diverged),
                    tuple(abandoned_shas),
                )

            # Every non-success path leaves the caller's staging as it was found, then reports honestly.
            _git(repo_root, ["reset", "--quiet", "HEAD", "--", *our_staged])
            if iso.status == _lock.ISO_NOTHING:
                return CommitOutcome(
                    STATUS_NOTHING_TO_COMMIT,
                    None,
                    (),
                    f"nothing to commit: {iso.detail}",
                    tuple(iso.hook_fixed),
                    tuple(iso.hook_fixed_diverged),
                    tuple(abandoned_shas),
                )
            return CommitOutcome(
                STATUS_ERROR,
                None,
                tuple(our_staged),
                f"git commit failed: {iso.detail}",
                tuple(iso.hook_fixed),
                tuple(iso.hook_fixed_diverged),
                tuple(abandoned_shas),
            )
    except _lock.CommitLockBusy as exc:
        return CommitOutcome(STATUS_ERROR, None, (), str(exc))
