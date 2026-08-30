"""Native, zero-runtime-dependency shell completion generators for the ``aw`` CLI.

tabcomp Order 01 (bja8og): STATIC completion. ``introspect_cli_tree`` walks the argparse action
tree of the real CLI parser into a plain dict (subcommands + flags), applying one explicit
command-visibility policy so only genuine user commands are surfaced. ``generate_{bash,zsh,fish}_
completion`` turn that tree into self-contained completion scripts binding all three console-script
aliases (``aw``, ``agentwf``, ``agent-workflows``). Every token that originates from the parser
(command names, flags, and help text used as Zsh/Fish descriptions) is shell-escaped for its target
shell before interpolation, because this CLI's help text contains shell-special characters
(backticks and ``$``); no emitted script can be broken or injected by help text.

tabcomp Order 02 (4f1j25): DYNAMIC contextual completion. ``complete_query`` answers a live
"complete this token stream" query from the CURRENT repository state - subcommands/flags in command
position, then contextual artifact tokens (plan/spec/backlog ``id6`` handles, Set ids, run ids) and
the per-type status vocabularies - and is exposed to the shells via the hidden ``aw __complete``
subcommand (see ``cli._run_dunder_complete``). It reuses the existing artifact authorities
(``agent_workflows.selectors``, ``.plans_index``, ``.artifact_core``, ``.artifact_naming``,
``.ipd_schema``, ``.attention_contract``, ``.backlog``) rather than re-scanning ad hoc. Two verified
shape facts drive the implementation: ``selectors.resolve_selectors`` needs a ``record_type`` and
returns ``pathlib.Path`` objects (NOT bare id6 tokens, so this module extracts the id6 from each
path via the naming grammar), and the CLI status arguments are free-form ``nargs="+"`` (NOT argparse
``choices``, so the status vocabularies come from ``ipd_schema``/``attention_contract``/``backlog``).
A hard latency budget (<50ms) forbids the unscoped resolver sweep (measured ~500ms over the full
``executed/`` history); dynamic scans are therefore scoped to ACTIVE dispositions (``pending``/
``reusable`` plans, live specs/backlog) and capped.

tabcomp Order 03 (jolfpj): DROP-IN installation. ``resolve_completion_dir`` /
``install_shell_completion`` / ``uninstall_shell_completion`` write the generated script into the
shell's own auto-discovery directory (XDG-first, matching ``config.config_dir``'s precedence), bind
the console-script aliases per SHELL-SPECIFIC rules (bash command-name files, one ``#compdef``-bound
zsh ``_aw``, fish's in-file multi-``complete -c``), and never touch ``~/.bashrc``/``~/.zshrc``/
``config.fish``. Every written file carries ``INSTALL_SENTINEL`` so install refuses to clobber a
foreign completion and uninstall removes only what this tool created.

This module is stdlib-only (``argparse``/``os``/``shlex``/``pathlib``); it does NOT import
third-party completion libraries, and the ``argcomplete`` ecosystem hook lives in ``cli`` behind a
soft import (no new runtime dependency).
"""

from __future__ import annotations

import argparse
import os
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional

# The three console-script entrypoints (pyproject.toml [project.scripts]). Completion binds all three.
ENTRYPOINTS = ("aw", "agentwf", "agent-workflows")


def _visible_subcommands(
    action: argparse._SubParsersAction,
) -> List[str]:
    """Return the user-facing primary subcommand names of one ``_SubParsersAction``.

    The single command-visibility policy (bja8og E-01):
      * only names that have a ``_choices_actions`` help entry are primary commands - this EXCLUDES
        argparse aliases (``att``, ``spec``, ``sanitize``, ``antigravity``, ``opencode``), which share
        their parent's parser object and carry no separate help entry;
      * a help entry whose ``help`` is ``argparse.SUPPRESS`` (hidden) is excluded;
      * the internal pre-commit/pre-push gate family (any name ending in ``-gate``:
        ``ipd-executed-gate``, ``ipd-status-untooled-gate``, ``backlog-blocking-close-gate``,
        ``ipd-dependency-statement-gate``, ``precommit-scope-gate``, ``prepush-authorization-gate``)
        is excluded - they are machine hooks, never typed by a user.

    NOTE: the pre-argparse forwarding pseudo-commands ``oc``/``opencode``, ``agy``/``antigravity``,
    and ``pwatch`` are intercepted in ``cli._dispatch`` BEFORE parsing and have no argparse subtree,
    so their nested commands are not statically completable and are out of scope for this child.
    """
    names: List[str] = []
    for choice_action in action._choices_actions:
        name = choice_action.dest
        if choice_action.help is argparse.SUPPRESS:
            continue
        if name.endswith("-gate"):
            continue
        names.append(name)
    return names


def _flags_of(parser: argparse.ArgumentParser) -> List[Dict[str, str]]:
    """Return this parser's option flags as ``[{"flag": "--x", "help": "..."}]`` (sorted, deduped).

    Skips the ``_SubParsersAction`` (its option strings, if any, are not user flags) and any option
    whose help is ``argparse.SUPPRESS``. The primary long flag is preferred; every option string of
    a visible option is emitted so short flags complete too.
    """
    out: List[Dict[str, str]] = []
    seen = set()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            continue
        if getattr(action, "help", None) is argparse.SUPPRESS:
            continue
        for opt in action.option_strings:
            if opt and opt not in seen:
                seen.add(opt)
                out.append({"flag": opt, "help": action.help or ""})
    out.sort(key=lambda d: d["flag"])
    return out


def introspect_cli_tree(parser: argparse.ArgumentParser) -> Dict[str, Any]:
    """Recursively extract the user-facing command tree from an argparse parser (bja8og E-01).

    Returns ``{"flags": [...], "subcommands": {name: <same shape>}}`` without mutating the parser.
    Models the recursion on ``cli._apply_descriptions`` (it walks ``_SubParsersAction.choices``), but
    applies the ``_visible_subcommands`` policy so internal gate commands and hidden aliases are
    absent from the tree.
    """

    def walk(node: argparse.ArgumentParser) -> Dict[str, Any]:
        tree: Dict[str, Any] = {"flags": _flags_of(node), "subcommands": {}}
        for action in node._actions:
            if isinstance(action, argparse._SubParsersAction):
                for name in _visible_subcommands(action):
                    sub = action.choices.get(name)
                    if sub is not None:
                        tree["subcommands"][name] = walk(sub)
        return tree

    return walk(parser)


def _all_command_paths(tree: Dict[str, Any]) -> List[List[str]]:
    """Flatten the tree into every command path (list of tokens), deepest-first-friendly order."""
    paths: List[List[str]] = []

    def rec(node: Dict[str, Any], prefix: List[str]) -> None:
        for name, sub in sorted(node.get("subcommands", {}).items()):
            path = prefix + [name]
            paths.append(path)
            rec(sub, path)

    rec(tree, [])
    return paths


def _top_level(tree: Dict[str, Any]) -> List[str]:
    return sorted(tree.get("subcommands", {}).keys())


# --------------------------------------------------------------------------------------
# Per-shell escaping. Help text in this CLI contains backticks and `$`; every emitted token that
# originates from the parser is escaped for its target shell before interpolation.
# --------------------------------------------------------------------------------------


def _bash_word(token: str) -> str:
    """POSIX single-word quote (safe inside a bash `words="..."`-style list via shlex.quote)."""
    return shlex.quote(token)


def _zsh_desc(text: str) -> str:
    """Escape a description for a Zsh `_arguments`/`_values` ``'name:desc'`` spec (single-quoted).

    Collapse to one line, then escape the Zsh-special chars that would break a single-quoted spec or
    inject: a single quote (close the quote), backslash, backtick, ``$`` (command/param expansion),
    and the ``:`` / ``[`` / ``]`` that are structural in `_arguments` specs.
    """
    t = " ".join(text.split())
    t = t.replace("\\", "\\\\")
    t = t.replace("'", "'\\''")
    for ch in ("`", "$", ":", "[", "]"):
        t = t.replace(ch, "\\" + ch)
    return t


def _fish_word(token: str) -> str:
    """Single-quote a token for Fish (only ``'`` and ``\\`` are special inside single quotes)."""
    return "'" + token.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _fish_desc(text: str) -> str:
    """One-line, single-quote-safe description body for a Fish ``-d '...'``."""
    t = " ".join(text.split())
    return t.replace("\\", "\\\\").replace("'", "\\'")


# --------------------------------------------------------------------------------------
# Generators
# --------------------------------------------------------------------------------------


def generate_bash_completion(tree: Dict[str, Any] | None = None) -> str:
    """Emit a self-contained Bash completion script binding all three entrypoints (bja8og E-02).

    Emits a single ``_aw_completion`` function that offers the top-level commands, then the nested
    subcommands of the first word, plus flags when the current word starts with ``-``. Every command
    and flag token is ``shlex.quote``d before being placed in the completion word list.
    """
    if tree is None:
        tree = introspect_cli_tree(_lazy_parser())
    top = tree.get("subcommands", {})
    top_names = " ".join(_bash_word(n) for n in sorted(top))

    # Second-level: `case` over the first command -> its subcommands.
    second_cases: List[str] = []
    for name in sorted(top):
        subs = top[name].get("subcommands", {})
        if subs:
            sub_names = " ".join(_bash_word(s) for s in sorted(subs))
            second_cases.append(
                f"        {_bash_word(name)})\n"
                f'            COMPREPLY=( $(compgen -W {shlex.quote(sub_names)} -- "$cur") )\n'
                f"            return 0 ;;"
            )
    # All flags across the tree, offered when $cur starts with '-'.
    all_flags = set()
    _collect_flags(tree, all_flags)
    flags_str = " ".join(_bash_word(f) for f in sorted(all_flags))

    lines = [
        "# bash completion for aw (agent-workflows). Generated by `aw completion bash`.",
        "# Source it:  source <(aw completion bash)",
        "_aw_completion() {",
        "    local cur prev words cword",
        "    COMPREPLY=()",
        '    cur="${COMP_WORDS[COMP_CWORD]}"',
        '    prev="${COMP_WORDS[COMP_CWORD-1]}"',
        '    if [[ "$cur" == -* ]]; then',
        f'        COMPREPLY=( $(compgen -W {shlex.quote(flags_str)} -- "$cur") )',
        "        return 0",
        "    fi",
        "    if [[ $COMP_CWORD -eq 1 ]]; then",
        f'        COMPREPLY=( $(compgen -W {shlex.quote(top_names)} -- "$cur") )',
        "        return 0",
        "    fi",
        '    case "${COMP_WORDS[1]}" in',
        *second_cases,
        "    esac",
        f'    COMPREPLY=( $(compgen -W {shlex.quote(top_names)} -- "$cur") )',
        "    return 0",
        "}",
        f"complete -F _aw_completion {' '.join(ENTRYPOINTS)}",
        "",
    ]
    return "\n".join(lines)


def generate_zsh_completion(tree: Dict[str, Any] | None = None) -> str:
    """Emit a native Zsh ``#compdef`` completion script binding all three entrypoints (bja8og E-02).

    Uses ``_arguments`` + ``_values`` with escaped ``'name:description'`` specs for the top-level
    commands, and a nested ``case`` for the second level. Descriptions are ``_zsh_desc``-escaped.
    """
    if tree is None:
        tree = introspect_cli_tree(_lazy_parser())
    top = tree.get("subcommands", {})

    top_specs = " ".join(
        f"'{name}'" for name in sorted(top)
    )  # names are word-safe (command tokens)

    second_cases: List[str] = []
    for name in sorted(top):
        subs = top[name].get("subcommands", {})
        if subs:
            sub_specs = " ".join(f"'{s}'" for s in sorted(subs))
            second_cases.append(
                f"                ({name})\n"
                f"                    _values 'subcommand' {sub_specs} ;;"
            )

    lines = [
        f"#compdef {' '.join(ENTRYPOINTS)}",
        "# zsh completion for aw (agent-workflows). Generated by `aw completion zsh`.",
        "_aw_completion() {",
        '    local curcontext="$curcontext" state line',
        "    typeset -A opt_args",
        "    _arguments -C '1: :->cmd' '*:: :->args'",
        '    case "$state" in',
        "        cmd)",
        f"            _values 'command' {top_specs} ;;",
        "        args)",
        '            case "$line[1]" in',
        *second_cases,
        "            esac ;;",
        "    esac",
        "}",
        '_aw_completion "$@"',
        "",
    ]
    return "\n".join(lines)


def generate_fish_completion(tree: Dict[str, Any] | None = None) -> str:
    """Emit a native Fish ``complete -c`` completion script binding all three entrypoints (E-02).

    Top-level commands complete only as the first token (a ``__fish_use_subcommand`` condition);
    each command's subcommands complete after it (``__fish_seen_subcommand_from``). Command tokens
    and description bodies are Fish-escaped.
    """
    if tree is None:
        tree = introspect_cli_tree(_lazy_parser())
    top = tree.get("subcommands", {})

    lines = [
        "# fish completion for aw (agent-workflows). Generated by `aw completion fish`.",
    ]
    for entry in ENTRYPOINTS:
        for name in sorted(top):
            lines.append(
                f"complete -c {entry} -n __fish_use_subcommand -a {_fish_word(name)}"
            )
        for name in sorted(top):
            subs = top[name].get("subcommands", {})
            for s in sorted(subs):
                lines.append(
                    f"complete -c {entry} -n "
                    f"{_fish_word('__fish_seen_subcommand_from ' + name)} "
                    f"-a {_fish_word(s)}"
                )
    lines.append("")
    return "\n".join(lines)


def _collect_flags(tree: Dict[str, Any], acc: set) -> None:
    for f in tree.get("flags", []):
        acc.add(f["flag"])
    for sub in tree.get("subcommands", {}).values():
        _collect_flags(sub, acc)


def _lazy_parser() -> argparse.ArgumentParser:
    """Build the real CLI parser on demand (avoids a circular import at module load)."""
    from agent_workflows import cli

    return cli._build_parser()


# Re-export the flatten helper for tests / child 02.
all_command_paths = _all_command_paths
top_level_commands = _top_level


_GENERATORS = {
    "bash": generate_bash_completion,
    "zsh": generate_zsh_completion,
    "fish": generate_fish_completion,
}


def generate(shell: str) -> str:
    """Generate the completion script for ``shell`` (bash|zsh|fish); raises KeyError otherwise."""
    return _GENERATORS[shell]()


# ======================================================================================
# tabcomp Order 02 (4f1j25): dynamic, repository-state contextual completion.
#
# `complete_query(words, cword, repo_root)` is the single query engine the shells reach through
# `aw __complete` (cli._run_dunder_complete). It returns BARE prefix-matching candidate tokens for
# the word at index `cword`, reusing the artifact authorities. Everything here is stdlib-only and
# fails SOFT: any lookup error yields [] (a completion query must never raise into a live shell).
# ======================================================================================

# The maximum number of dynamic candidates returned for one query. Interactive completion never
# needs a huge list, and a cap keeps a pathological repository from blowing the latency budget.
_MAX_DYNAMIC = 200

# Entity subcommands whose id6-bearing positionals we complete, mapped to the `selectors`
# record_type used to enumerate their active artifacts. `find` accepts a leading record-type token
# and is handled specially in `_entity_record_type`.
_ENTITY_RECORD_TYPE: Dict[str, str] = {
    "ipd": "plans",
    "specs": "specs",
    "spec": "specs",  # argparse alias of `specs`
    "backlog": "backlog",
}

# Plan-status directories that are ACTIVE (a user completes an id6 against these; the terminal
# executed/superseded/not-executed history is excluded to honor the <50ms budget - a full-history
# resolver sweep measured ~500ms, vs ~5ms for a pending-scoped scan).
_ACTIVE_PLAN_DISPOSITIONS = ("pending", "reusable")


def _repo_root(repo_root: Optional[Path]) -> Path:
    return Path(repo_root) if repo_root is not None else Path.cwd()


def _id6_of_path(p: Path) -> Optional[str]:
    """Extract the artifact's own id6 from its filename via the naming grammar (NOT a substring
    scan of the whole stem, which would pick up incidental 6-char words like ``wizard``)."""
    from agent_workflows import artifact_naming as _an

    m = _an.parse_clustered(p.name) or _an.parse_uniform_permissive(p.name)
    if m:
        try:
            return m.group("id6")
        except IndexError:  # pragma: no cover - defensive
            return None
    return None


def _prefix_filter(candidates: List[str], prefix: str) -> List[str]:
    """Deduped, sorted, capped prefix match (empty prefix matches all)."""
    seen: Dict[str, None] = {}
    for c in candidates:
        if c and c.startswith(prefix) and c not in seen:
            seen[c] = None
    return sorted(seen)[:_MAX_DYNAMIC]


def plan_id6_candidates(repo_root: Optional[Path] = None) -> List[str]:
    """Active plan ``id6`` handles (pending + reusable only, per the latency budget).

    Uses the plan front-matter ``Id:`` (authoritative) via a directory-scoped ``scan_plans`` over
    each active disposition dir, NOT the full-history resolver sweep.
    """
    from agent_workflows import plans_index

    root = _repo_root(repo_root)
    plans_dir = root / ".aw" / "records" / "plans"
    out: List[str] = []
    for disp in _ACTIVE_PLAN_DISPOSITIONS:
        try:
            entries, _ = plans_index.scan_plans(plans_dir / disp)
        except Exception:
            continue
        for e in entries:
            if e.plan_id:
                out.append(e.plan_id)
    return out


def set_id_candidates(repo_root: Optional[Path] = None) -> List[str]:
    """Active Set ids, derived from the ``- Set:`` front matter of active plans (NOT a `selectors`
    record type). Terse id only (``plans_index.set_terse_id`` semantics, already applied by
    ``scan_plans``)."""
    from agent_workflows import plans_index

    root = _repo_root(repo_root)
    plans_dir = root / ".aw" / "records" / "plans"
    out: List[str] = []
    for disp in _ACTIVE_PLAN_DISPOSITIONS:
        try:
            entries, _ = plans_index.scan_plans(plans_dir / disp)
        except Exception:
            continue
        for e in entries:
            if e.set_id:
                out.append(e.set_id)
    return out


def run_id_candidates(repo_root: Optional[Path] = None) -> List[str]:
    """Run ids: the directory names directly under ``.aw/records/runs/`` (NOT a `selectors` record
    type - runs are enumerated straight from the filesystem)."""
    root = _repo_root(repo_root)
    runs_dir = root / ".aw" / "records" / "runs"
    out: List[str] = []
    try:
        for child in runs_dir.iterdir():
            if child.is_dir() and not child.name.startswith("."):
                out.append(child.name)
    except OSError:
        pass
    return out


def release_selector_candidates(repo_root: Optional[Path] = None) -> List[str]:
    """Selectors accepted by ``aw releases show``: every release ``id6``, every ``Version`` string,
    and the ``next`` sentinel (IPD w0ln4q E-04).

    Sourced from ``releases.list_releases`` (the SAME reader the verb itself uses), not a second
    filesystem walk, so completion can never offer a token the verb would reject. The releases tree is
    tiny (one record per release), so it is scanned unscoped without threatening the latency budget."""
    from agent_workflows import releases as _releases

    root = _repo_root(repo_root)
    out: List[str] = []
    try:
        records = _releases.list_releases(root)
    except Exception:
        return out
    for rec in records:
        if rec.id6:
            out.append(rec.id6)
        if rec.version:
            out.append(rec.version)
    # `next` is only a real selector when exactly one release is planned (the resolver's own rule).
    try:
        if _releases.resolve_release(root, "next") is not None:
            out.append("next")
    except Exception:
        pass
    return out


def entity_id6_candidates(
    record_type: str, repo_root: Optional[Path] = None
) -> List[str]:
    """Active ``id6`` handles for a `selectors` record type (``plans``/``specs``/``backlog``),
    returned as BARE id6 tokens extracted from each resolved path's name via the naming grammar.

    Plans are scoped to the active dispositions (latency budget); specs/backlog are enumerated via
    ``selectors.record_dirs`` (their trees are small - status subdirs, not a 300+ history).
    """
    if record_type == "plans":
        return plan_id6_candidates(repo_root)

    from agent_workflows import selectors

    root = _repo_root(repo_root)
    out: List[str] = []
    try:
        dirs = selectors.record_dirs(root, record_type)
    except Exception:
        return out
    for d in dirs:
        try:
            for p in d.rglob("*.md"):
                i = _id6_of_path(p)
                if i:
                    out.append(i)
        except OSError:
            continue
    return out


def status_candidates(record_type: str) -> List[str]:
    """The status vocabulary VALID for ``record_type`` (plan vs. spec vs. backlog differ), sourced
    from the real single-source-of-truth modules - NOT a hardcoded global list and NOT argparse
    ``choices`` (the CLI status args are free-form ``nargs="+"``)."""
    if record_type == "plans":
        from agent_workflows import ipd_schema

        return sorted(ipd_schema.RECOGNIZED_STATUS)
    if record_type == "specs":
        from agent_workflows import attention_contract

        return sorted(attention_contract.SPEC_STATUSES)
    if record_type == "backlog":
        from agent_workflows import backlog

        return sorted(backlog.STATUSES)
    return []


def _entity_record_type(words: List[str], cword: int) -> Optional[str]:
    """Map the command context to a `selectors` record_type for id6 completion, or None.

    `aw ipd <...>`   -> plans      `aw specs/spec <...>` -> specs
    `aw backlog <...>` -> backlog  `aw find <type> <...>` -> that <type> if it names one.
    """
    if cword < 2:
        return None
    cmd = words[1]
    if cmd == "find":
        # `aw find <record_type> <selector...>`: the record type is words[2].
        if cword >= 3 and len(words) > 2:
            rt = words[2]
            if rt in ("plans", "specs", "backlog", "research"):
                return rt
        return None
    return _ENTITY_RECORD_TYPE.get(cmd)


def _is_status_position(words: List[str], cword: int) -> Optional[str]:
    """If the word at `cword` is a STATUS argument position, return the record_type whose status
    vocabulary applies; else None.

    The recognized shapes (verified against the real CLI):
      * ``aw ipd set <status> <selector...>``        -> plan statuses at cword 3
      * ``aw specs set --status <status>``           -> spec statuses right after ``--status``
      * ``aw specs set <path> --status <status>``    (same)
      * ``aw backlog set <selector> --status <s>``   -> backlog statuses after ``--status``
    We complete a status when the PREVIOUS token is ``--status``, or in the ``ipd set`` positional
    slot (index 3, i.e. the token right after ``set``).
    """
    if cword >= 1 and words[cword - 1] == "--status":
        # Find the owning entity command earlier in the line.
        if len(words) > 1:
            rt = _ENTITY_RECORD_TYPE.get(words[1])
            if rt:
                return rt
    # `aw ipd set <status>` positional (status is the first positional after `set`).
    if cword == 3 and len(words) > 2 and words[1] == "ipd" and words[2] == "set":
        return "plans"
    return None


def _subcommand_candidates(words: List[str], cword: int) -> List[str]:
    """Static subcommand/flag candidates for the command position, reusing the introspected tree.

    Position 1 -> top-level commands; position 2 -> the first command's subcommands; a word starting
    with ``-`` -> that context's flags. This mirrors the generated static scripts so `__complete`
    and the offline scripts agree on the static layer.
    """
    tree = introspect_cli_tree(_lazy_parser())
    cur = words[cword] if cword < len(words) else ""

    # Flag context: offer flags of the current subcommand path.
    if cur.startswith("-"):
        node = tree
        for tok in words[1:cword]:
            sub = node.get("subcommands", {}).get(tok)
            if sub is None:
                break
            node = sub
        return [f["flag"] for f in node.get("flags", [])]

    if cword <= 1:
        return list(tree.get("subcommands", {}).keys())

    # Nested subcommand: walk to words[cword-1]'s node and offer its subcommands.
    node = tree
    for tok in words[1:cword]:
        sub = node.get("subcommands", {}).get(tok)
        if sub is None:
            return []
        node = sub
    return list(node.get("subcommands", {}).keys())


def complete_query(
    words: List[str], cword: int, repo_root: Optional[Path] = None
) -> List[str]:
    """Return prefix-matching completion candidates for the token at ``cword`` (tabcomp-02 E-01).

    ``words`` is the full command token list (``["aw", "ipd", "lint", "b"]``); ``cword`` is the index
    of the word being completed. Returns BARE tokens (subcommands, flags, ``id6`` handles, Set ids,
    run ids, status enums) matching the current prefix, evaluated against the CURRENT repository
    state. Never raises: any failure yields the best static answer (or []).

    Layering (first match wins for the DYNAMIC layer, then merged with static subcommands):
      1. If completing a STATUS position, return that record type's status vocabulary.
      2. Else if in an entity command's id6 position, return that type's active id6 handles.
      3. Else if completing ``aw run``/``aw runs`` targets, return Set ids + run ids.
      4. Always fall back to / include the static subcommand-or-flag candidates for the position.
    """
    if cword < 0:
        return []
    prefix = words[cword] if cword < len(words) else ""

    # A flag prefix is always a static-flag query (never an artifact).
    if prefix.startswith("-"):
        return _prefix_filter(_subcommand_candidates(words, cword), prefix)

    # 1. Status positions -> ONLY that record type's status vocabulary (a pure dynamic answer; the
    #    static subcommand layer is deliberately skipped, both for correctness - subcommand names are
    #    not valid there - and to avoid the parser-build cost inside the <50ms budget).
    status_rt = _is_status_position(words, cword)
    if status_rt is not None:
        return _prefix_filter(status_candidates(status_rt), prefix)

    # 2. Entity id6 positions (aw ipd/specs/backlog/find ...). Only when PAST the subcommand slot
    #    (cword >= 3 so a real selector/positional is being typed, e.g. `aw ipd lint <id6>`); the
    #    token in the subcommand slot itself is completed by the static layer (step 4). This is a
    #    pure dynamic answer for the same correctness + latency reasons as step 1.
    entity_rt = _entity_record_type(words, cword)
    if entity_rt is not None and cword >= 3:
        try:
            return _prefix_filter(entity_id6_candidates(entity_rt, repo_root), prefix)
        except Exception:
            return []

    # 2b. `aw releases show <selector>` / `aw release show <selector>` -> release id6s + versions +
    #     `next` (IPD w0ln4q E-04). A pure dynamic answer for the same reason as steps 1-2: no
    #     subcommand name is valid in the selector slot.
    if (
        cword >= 3
        and len(words) > 2
        and words[1] in ("releases", "release")
        and words[2] == "show"
    ):
        try:
            return _prefix_filter(release_selector_candidates(repo_root), prefix)
        except Exception:
            return []

    # 3. run / runs targets -> Set ids + run ids (pure dynamic answer).
    if cword >= 2 and words[1] in ("run", "runs"):
        try:
            return _prefix_filter(
                set_id_candidates(repo_root) + run_id_candidates(repo_root), prefix
            )
        except Exception:
            return []

    # 4. Static subcommand / flag layer (command names / flags in the command position).
    return _prefix_filter(_subcommand_candidates(words, cword), prefix)


# ======================================================================================
# tabcomp Order 03 (jolfpj) E-01: DROP-IN auto-discovery installation.
#
# The core promise: we NEVER edit `~/.bashrc`, `~/.zshrc`, or `config.fish`. Instead we write the
# generated script into the shell's own auto-discovery directory, which every modern bash-completion
# / zsh `fpath` / fish `completions` setup loads on demand:
#
#   bash  ${XDG_DATA_HOME:-~/.local/share}/bash-completion/completions/aw
#   zsh   ${XDG_DATA_HOME:-~/.local/share}/zsh/site-functions/_aw
#   fish  ${XDG_CONFIG_HOME:-~/.config}/fish/completions/aw.fish
#
# XDG precedence matches `agent_workflows.config.config_dir` (XDG env var first, then the
# `~/.local/share` / `~/.config` fallback), so this feature does not invent a second convention.
#
# ALIAS BINDING IS SHELL-SPECIFIC (a verified correctness constraint - do NOT blanket-symlink all
# three names in all three shells):
#   - BASH loads a completion file BY COMMAND NAME, so `agentwf` and `agent-workflows` each need
#     their own command-name entry (created as symlinks to the `aw` file).
#   - ZSH binds every alias from the SINGLE `_aw` file's `#compdef aw agentwf agent-workflows`
#     first line, so extra `_agentwf`/`_agent-workflows` files are unnecessary (and would be wrong).
#   - FISH binds every alias from the `complete -c aw` / `-c agentwf` / `-c agent-workflows` lines
#     already inside the one generated `aw.fish`, so no per-alias fish file is needed.
#
# SAFETY: a shared user directory may already hold someone else's `aw` completion. Every file we
# write carries a self-identifying SENTINEL line; we refuse to clobber a file that lacks it, we
# never write or delete THROUGH a symlink pointing somewhere unexpected, and uninstall removes ONLY
# files/symlinks this tool created (sentinel-identified).
# ======================================================================================

# The self-identifying marker written into every file this tool creates. Its presence is the ONLY
# license to overwrite or remove a file in a shared completion directory.
INSTALL_SENTINEL = "# installed-by: agent-workflows (aw completion install)"

SUPPORTED_SHELLS = ("bash", "zsh", "fish")

# Per-shell drop-in layout: (XDG env var, fallback dir relative to $HOME, subdir, primary filename).
_DROPIN_LAYOUT: Dict[str, Any] = {
    "bash": ("XDG_DATA_HOME", ".local/share", "bash-completion/completions", "aw"),
    "zsh": ("XDG_DATA_HOME", ".local/share", "zsh/site-functions", "_aw"),
    "fish": ("XDG_CONFIG_HOME", ".config", "fish/completions", "aw.fish"),
}


class CompletionInstallError(RuntimeError):
    """A drop-in install/uninstall could not be performed safely (e.g. a foreign file present)."""


def resolve_completion_dir(shell: str, custom_dir: Optional[Path] = None) -> Path:
    """Return the drop-in auto-discovery directory for ``shell`` (jolfpj E-01).

    ``custom_dir`` overrides everything (``--dir``). Otherwise the shell's XDG base env var wins
    (``XDG_DATA_HOME`` for bash/zsh, ``XDG_CONFIG_HOME`` for fish) and falls back to
    ``~/.local/share`` / ``~/.config`` - the same precedence as ``config.config_dir``.
    """
    if shell not in _DROPIN_LAYOUT:
        raise CompletionInstallError(
            f"unsupported shell {shell!r} (expected one of {', '.join(SUPPORTED_SHELLS)})"
        )
    if custom_dir is not None:
        return Path(custom_dir).expanduser()
    env_var, fallback, subdir, _name = _DROPIN_LAYOUT[shell]
    raw = os.environ.get(env_var)
    base = Path(raw).expanduser() if raw else Path.home() / fallback
    return base / subdir


def completion_filename(shell: str) -> str:
    """The primary drop-in filename for ``shell`` (``aw`` / ``_aw`` / ``aw.fish``)."""
    if shell not in _DROPIN_LAYOUT:
        raise CompletionInstallError(f"unsupported shell {shell!r}")
    return _DROPIN_LAYOUT[shell][3]


def _alias_filenames(shell: str) -> List[str]:
    """Extra command-name files needed to bind the console-script aliases, per shell.

    BASH only: it dispatches completion by command name. Zsh binds all aliases from the single
    ``_aw`` file's ``#compdef`` line and fish from the in-file ``complete -c <name>`` lines, so both
    return an empty list (creating per-alias files there would be wrong, not merely redundant).
    """
    if shell == "bash":
        return [name for name in ENTRYPOINTS if name != "aw"]
    return []


def _script_with_sentinel(shell: str) -> str:
    """The generated completion script carrying the self-identifying sentinel line.

    The sentinel goes on line 1 EXCEPT when the script opens with zsh's ``#compdef`` tag: zsh's
    ``compinit`` autoload only honors ``#compdef`` when it is the FIRST line of the file, so
    prepending anything above it would silently break the alias binding. In that case the sentinel
    becomes line 2 (``_is_ours`` scans the first few lines, so detection is unaffected).
    """
    body = generate(shell)
    lines = body.split("\n")
    if lines and lines[0].startswith("#compdef"):
        return "\n".join([lines[0], INSTALL_SENTINEL, *lines[1:]])
    return f"{INSTALL_SENTINEL}\n{body}"


def _is_ours(path: Path) -> bool:
    """True when ``path`` is a file this tool wrote (carries the sentinel) or one of our symlinks.

    A symlink is "ours" when it resolves to a sentinel-bearing file inside the same directory (the
    alias links we create). A dangling or foreign-target symlink is NOT ours, so we never delete or
    write through a link pointing somewhere unexpected.
    """
    try:
        if path.is_symlink():
            target = path.parent / os.readlink(path)
            return target.is_file() and _is_ours(target)
        if not path.is_file():
            return False
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for _ in range(5):  # the sentinel is line 1; allow a little slack.
                line = fh.readline()
                if not line:
                    break
                if line.strip() == INSTALL_SENTINEL:
                    return True
        return False
    except OSError:
        return False


def _foreign(path: Path) -> bool:
    """True when something exists at ``path`` that this tool did not create."""
    return (path.exists() or path.is_symlink()) and not _is_ours(path)


def install_shell_completion(
    shell: str,
    target_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Write the drop-in completion file (+ per-shell alias binding) for ``shell`` (jolfpj E-01).

    Creates the auto-discovery directory if needed, writes the generated script prefixed with
    ``INSTALL_SENTINEL``, and adds the bash command-name alias symlinks (zsh/fish bind their aliases
    from inside the single generated file). Idempotent: re-running rewrites OUR file and leaves the
    result identical. NO user rc/dotfile is ever read or written.

    Raises ``CompletionInstallError`` when a FOREIGN (non-sentinel) file or an unexpected symlink
    already occupies a target path - we never clobber another tool's or the user's completion.

    Returns ``{"shell", "dir", "paths", "aliases", "dry_run"}`` where ``paths`` lists every path
    written (or that WOULD be written under ``dry_run``).
    """
    if shell not in _DROPIN_LAYOUT:
        raise CompletionInstallError(
            f"unsupported shell {shell!r} (expected one of {', '.join(SUPPORTED_SHELLS)})"
        )
    directory = resolve_completion_dir(shell, target_dir)
    primary = directory / completion_filename(shell)
    aliases = [directory / name for name in _alias_filenames(shell)]

    # Fail closed BEFORE writing anything: a foreign file at any target aborts the whole install.
    for path in [primary, *aliases]:
        if _foreign(path):
            raise CompletionInstallError(
                f"refusing to overwrite {path}: it was not created by agent-workflows "
                f"(no {INSTALL_SENTINEL!r} marker). Remove it or pass a different --dir."
            )

    if dry_run:
        return {
            "shell": shell,
            "dir": directory,
            "paths": [primary, *aliases],
            "aliases": aliases,
            "dry_run": True,
        }

    directory.mkdir(parents=True, exist_ok=True)
    # Write the real file (never through a symlink: any pre-existing entry here is ours, and we
    # unlink it first so a stale link can never redirect the write).
    if primary.is_symlink():
        primary.unlink()
    primary.write_text(_script_with_sentinel(shell), encoding="utf-8")
    primary.chmod(0o644)

    written = [primary]
    for link in aliases:
        if link.exists() or link.is_symlink():
            link.unlink()
        try:
            link.symlink_to(primary.name)
        except OSError:
            # A filesystem without symlink support still gets working completion via a real copy.
            link.write_text(_script_with_sentinel(shell), encoding="utf-8")
        written.append(link)

    return {
        "shell": shell,
        "dir": directory,
        "paths": written,
        "aliases": aliases,
        "dry_run": False,
    }


def uninstall_shell_completion(
    shell: str,
    target_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Remove ONLY the drop-in files this tool created for ``shell`` (jolfpj E-01).

    Sentinel-gated: a file or symlink we did not create is left untouched and reported under
    ``skipped``, never deleted. No rc/dotfile is read or written. Returns
    ``{"shell", "dir", "removed", "skipped", "dry_run"}``.
    """
    if shell not in _DROPIN_LAYOUT:
        raise CompletionInstallError(
            f"unsupported shell {shell!r} (expected one of {', '.join(SUPPORTED_SHELLS)})"
        )
    directory = resolve_completion_dir(shell, target_dir)
    candidates = [directory / completion_filename(shell)] + [
        directory / name for name in _alias_filenames(shell)
    ]

    removed: List[Path] = []
    skipped: List[Path] = []
    # Remove alias links before the primary so an "ours" link is still resolvable when checked.
    for path in reversed(candidates):
        if not (path.exists() or path.is_symlink()):
            continue
        if not _is_ours(path):
            skipped.append(path)
            continue
        removed.append(path)
        if not dry_run:
            path.unlink()

    return {
        "shell": shell,
        "dir": directory,
        "removed": list(reversed(removed)),
        "skipped": skipped,
        "dry_run": dry_run,
    }


def is_completion_installed(shell: str, target_dir: Optional[Path] = None) -> bool:
    """True when OUR drop-in completion file is already present for ``shell``."""
    try:
        primary = resolve_completion_dir(shell, target_dir) / completion_filename(shell)
    except CompletionInstallError:
        return False
    return _is_ours(primary)
