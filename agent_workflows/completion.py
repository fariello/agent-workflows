"""Native, zero-runtime-dependency shell completion generators for the ``aw`` CLI.

tabcomp Order 01 (bja8og): STATIC completion. ``introspect_cli_tree`` walks the argparse action
tree of the real CLI parser into a plain dict (subcommands + flags + positional ``choices``), applying
one explicit command-visibility policy so only genuine user commands are surfaced.
``generate_{bash,zsh,fish}_completion`` turn that tree into self-contained completion scripts binding
all three console-script aliases (``aw``, ``agentwf``, ``agent-workflows``). A command offers its OWN
arguments in the slot after its name, and a command that declares none offers NOTHING (compargs
4y95tp): the bash generator used to end its `case` with an unconditional top-level fallback, so every
command without a `case` arm (31 of 48 when the fix landed) suggested the whole command list, and
``aw completion in<TAB>`` offered ``index`` - a token the verb then rejected. Treat that count as a
census taken once, not a property: it moves with the command population, and the FIX does not depend on
it. Every token that originates from the parser
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
THAT STATUS FACT IS STILL TRUE, and is narrower than it reads now that this module DOES read positional
``choices`` (compargs 4y95tp): exactly three positionals carry them - ``migrate-layout action``,
``path root``, and ``completion target`` (given real ``choices`` by 4y95tp E-08 so the reported
``aw completion <TAB>`` case became completable at all). Statuses are not among them.
A hard latency budget (<50ms) forbids the unscoped resolver sweep (measured ~500ms over the full
``executed/`` history); dynamic scans are therefore scoped to ACTIVE dispositions (``pending``/
``reusable`` plans, live specs/backlog) and capped.

tabcomp Order 03 (jolfpj): DROP-IN installation. ``resolve_completion_dir`` /
``install_shell_completion`` / ``uninstall_shell_completion`` write the generated script into the
shell's own auto-discovery directory (XDG-first, matching ``config.config_dir``'s precedence), bind
the console-script aliases per SHELL-SPECIFIC rules (bash command-name files, one ``#compdef``-bound
zsh ``_aw``, fish's in-file multi-``complete -c``), and never SILENTLY write ``~/.bashrc``/
``~/.zshrc``/``config.fish`` - the ONLY rc write in this module is the fenced remediation stanza of
compinert Order 01 below, applied only on explicit TTY consent, never under ``--yes`` and never
non-interactively. Every written file carries ``INSTALL_SENTINEL`` so install refuses to clobber a
foreign completion and uninstall removes only what this tool created.

compinert Order 01 (92u0v9): CAN THE INSTALL ACTUALLY TAKE EFFECT? A drop-in file is only completed
if the shell's completion FRAMEWORK is loaded, and on many systems bash-completion is sourced only
by ``/etc/profile.d/bash_completion.sh`` (LOGIN shells), so a new terminal tab gets no completion at
all and the drop-in is inert. ``completion_framework_status`` reports that precondition as three
SEPARATE facts (entry script present / reachable from an interactive non-login shell / the user's rc
already sources it) so the caller can distinguish "install a package" from "add one line", and
``remediation_snippet``/``install_rc_stanza``/``remove_rc_stanza`` print and (ONLY on explicit TTY
consent) apply the one-line fix inside PAIRED FENCE MARKERS so it can be removed and upgraded.

THE NO-SILENT-WRITE PROMISE, STATED PRECISELY (compinert 92u0v9, maintainer ruling 2026-09-12). The
drop-in installer itself still writes NO user rc/dotfile at all. The ONLY code here that can touch
``~/.bashrc`` is ``install_rc_stanza``/``remove_rc_stanza``, which write nothing unless their caller
passes explicit human consent obtained on a TTY; ``--yes`` is deliberately NOT consent, and a
non-interactive run never writes. Reading an rc file to report fact (c) is a READ, never a write.

This module is stdlib-only (``argparse``/``os``/``shlex``/``pathlib``/``subprocess``); it does NOT
import third-party completion libraries, and the ``argcomplete`` ecosystem hook lives in ``cli``
behind a soft import (no new runtime dependency). ``subprocess`` is used for exactly one thing: the
interactive-shell probe below, because asking bash what it loaded is ground truth where parsing rc
files to guess it is not.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

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


def _positional_choices(parser: argparse.ArgumentParser) -> List[str]:
    """Return the argparse ``choices`` of this parser's FIRST user-facing positional, else ``[]``.

    compargs 4y95tp E-02. A command's arguments are not always subparsers: ``aw migrate-layout`` and
    ``aw path`` express theirs as a positional with a fixed ``choices`` vocabulary, which
    ``introspect_cli_tree``'s subparser-only walk could not see, so the generated script had nothing
    true to offer for them. Only the FIRST positional is read, because the completion scripts
    complete the slot immediately after the command name and a later positional's vocabulary is not
    valid there.

    DELIBERATELY SILENT for an unconstrained positional (a path, a selector, an id6): a positional
    with no ``choices`` declares no vocabulary, and inventing one is how the fall-through defect this
    function was added to fix began. Dynamic values come from ``complete_query`` instead.
    """
    for action in parser._actions:
        if action.option_strings:
            continue
        if isinstance(action, argparse._SubParsersAction):
            continue
        if getattr(action, "help", None) is argparse.SUPPRESS:
            continue
        if action.choices:
            return [str(c) for c in action.choices]
        return []
    return []


def introspect_cli_tree(parser: argparse.ArgumentParser) -> Dict[str, Any]:
    """Recursively extract the user-facing command tree from an argparse parser (bja8og E-01).

    Returns ``{"flags": [...], "subcommands": {name: <same shape>}, "choices": [...]}`` without
    mutating the parser. Models the recursion on ``cli._apply_descriptions`` (it walks
    ``_SubParsersAction.choices``), but applies the ``_visible_subcommands`` policy so internal gate
    commands and hidden aliases are absent from the tree.

    ``choices`` (compargs 4y95tp E-02) carries the fixed vocabulary of the node's FIRST user-facing
    positional, captured under its OWN key rather than merged into ``subcommands``: choice tokens are
    not subcommands (they do not nest and carry no flags of their own), so conflating them would make
    a generator emit a third level for something that cannot have one. An unconstrained positional
    deliberately contributes NOTHING, because a positional with no ``choices`` declares no vocabulary
    and guessing one is the defect class this key exists to end.
    """

    def walk(node: argparse.ArgumentParser) -> Dict[str, Any]:
        tree: Dict[str, Any] = {
            "flags": _flags_of(node),
            "subcommands": {},
            "choices": _positional_choices(node),
        }
        for action in node._actions:
            if isinstance(action, argparse._SubParsersAction):
                for name in _visible_subcommands(action):
                    sub = action.choices.get(name)
                    if sub is not None:
                        tree["subcommands"][name] = walk(sub)
        return tree

    return walk(parser)


def _node_candidates(node: Dict[str, Any]) -> List[str]:
    """The tokens valid in the slot right after ``node``'s command name: subcommands + choices.

    compargs 4y95tp E-03. MERGED, not either/or, so a command that ever gains both kinds completes
    both. MEASURED at authoring: no command has both today (the two choices-bearing commands,
    ``migrate-layout`` and ``path``, have no subparsers), so the merge path is LATENT by construction
    and is untested against a real both-kinds command; it is written because the alternative is a
    silent wrong answer the day one appears.
    """
    return sorted(set(node.get("subcommands", {})) | set(node.get("choices", []) or []))


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

    Emits a single ``_aw_completion`` function that offers the top-level commands in the command
    slot, then, in the slot after a command, THAT COMMAND'S OWN arguments: its nested subcommands and
    the fixed ``choices`` vocabulary of its first positional. A command with NEITHER offers NOTHING,
    so bash falls back to its own default (filenames) instead of proposing a token that cannot be
    valid there. Flags are offered when the current word starts with ``-``. Every command, choice and
    flag token is ``shlex.quote``d before being placed in the completion word list.

    THE FALL-THROUGH IS GONE ON PURPOSE (compargs 4y95tp E-01). This function used to end its `case`
    with an unconditional top-level ``COMPREPLY=``, so any command without a `case` arm (31 of 48 when
    the fix landed) suggested the whole command list: ``aw completion in<TAB>`` offered ``index``, which
    the verb then rejected. Do not reintroduce a default arm; an empty ``COMPREPLY`` is the correct
    answer when the parser declares no vocabulary for the position.
    """
    if tree is None:
        tree = introspect_cli_tree(_lazy_parser())
    top = tree.get("subcommands", {})
    top_names = " ".join(_bash_word(n) for n in sorted(top))

    # Second-level: `case` over the first command -> its own subcommands AND positional choices.
    second_cases: List[str] = []
    for name in sorted(top):
        candidates = _node_candidates(top[name])
        if candidates:
            sub_names = " ".join(_bash_word(s) for s in candidates)
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
        # compargs 4y95tp E-01: NO default arm and NO post-`esac` fallback. A command with no arm
        # leaves COMPREPLY empty, which is bash's signal to use its own default completion.
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

    The second level offers a command's OWN arguments - subcommands plus its first positional's fixed
    ``choices`` (compargs 4y95tp E-03) - and nothing when it declares neither. Zsh never had bash's
    top-level fall-through (its inner `case` has no default arm), so E-01 has no counterpart here.
    """
    if tree is None:
        tree = introspect_cli_tree(_lazy_parser())
    top = tree.get("subcommands", {})

    top_specs = " ".join(
        f"'{name}'" for name in sorted(top)
    )  # names are word-safe (command tokens)

    second_cases: List[str] = []
    for name in sorted(top):
        candidates = _node_candidates(top[name])
        if candidates:
            sub_specs = " ".join(f"'{s}'" for s in candidates)
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
    each command's own arguments - its subcommands and its first positional's fixed ``choices``
    (compargs 4y95tp E-03) - complete after it (``__fish_seen_subcommand_from``). Command tokens and
    description bodies are Fish-escaped. Every emitted line is conditional, so fish never had bash's
    top-level fall-through and E-01 has no counterpart here.
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
            for s in _node_candidates(top[name]):
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
    """Run ids: the directory names directly under the resolved runs root (NOT a `selectors` record
    type - runs are enumerated straight from the filesystem)."""
    from agent_workflows.runner_shared import path_is_within_analytics, state_root

    root = _repo_root(repo_root)
    runs_dir = state_root(root)
    out: List[str] = []
    try:
        if runs_dir.is_dir():
            for child in sorted(runs_dir.iterdir()):
                if (
                    child.is_dir()
                    and child.name.startswith("run-")
                    and not path_is_within_analytics(child, root)
                ):
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

    Position 1 -> top-level commands; position 2 -> the first command's own arguments (its
    subcommands AND its first positional's fixed ``choices``); a word starting with ``-`` -> that
    context's flags. This mirrors the generated static scripts so `__complete` and the offline
    scripts agree on the static layer.

    THE CHOICES HALF IS WHY THAT PARITY SENTENCE IS STILL TRUE (compargs 4y95tp E-05). When the static
    generators learned to emit positional ``choices``, this function had to learn it in the same
    change: otherwise ``aw migrate-layout <TAB>`` would offer eight actions through an offline script
    and nothing through ``aw __complete``, and the two surfaces would disagree in the file that
    documents their agreement. Positional ``choices`` are STATIC vocabulary by this contract's own
    definition (fixed in the parser, not read from disk), so they belong in the mirrored layer.
    Both surfaces read the SAME ``introspect_cli_tree`` key through the SAME ``_node_candidates``
    helper, so they cannot drift by construction rather than by discipline.
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

    # Nested position: walk to words[cword-1]'s node and offer ITS own arguments.
    node = tree
    for tok in words[1:cword]:
        sub = node.get("subcommands", {}).get(tok)
        if sub is None:
            return []
        node = sub
    return _node_candidates(node)


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

    # 3. Run-family TARGET positions -> Set ids + run ids (pure dynamic answer).
    #
    # runnamecollapse 0soncw E-08: `run` and `runs` used to be ONE completion surface, which is now
    # wrong in both directions, because the two nouns no longer take the same thing in the same slot:
    #
    #   * `aw runs <TAB>`        -> a TARGET (bare viewer), so offer set ids + run ids.
    #   * `aw runs <leaf> <TAB>` -> a TARGET for that leaf, so offer them here too.
    #   * `aw run <TAB>`         -> a WRITER LEAF (start/record/cancel/finalize), NOT a target. It is
    #                              left to the static subcommand layer below. Offering run ids here
    #                              suggested a shape `aw run` no longer accepts.
    #   * `aw run <leaf> <TAB>`  -> a TARGET for that writer leaf, so offer them.
    #
    # The retired noun therefore still COMPLETES, but it completes its own real surface (its four
    # leaves) instead of targets it cannot take. That is the E-08 decision, asserted in
    # `tests/test_completion.py`.
    if cword == 2 and words[1] == "runs":
        # The FIRST slot after `runs` is genuinely ambiguous by design (that is what the parser's
        # routing action resolves), so completion must offer BOTH what can legally appear there: the
        # nine viewer leaf names AND the targets. Offering only targets hid `aw runs status` from tab
        # completion entirely; offering only leaves would hide every run id.
        try:
            dynamic = set_id_candidates(repo_root) + run_id_candidates(repo_root)
        except Exception:
            dynamic = []
        return _prefix_filter(_subcommand_candidates(words, cword) + dynamic, prefix)
    if cword >= 3 and words[1] == "runs":
        try:
            return _prefix_filter(
                set_id_candidates(repo_root) + run_id_candidates(repo_root), prefix
            )
        except Exception:
            return []
    if cword >= 3 and words[1] == "run":
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
# The core promise, stated precisely since compinert 92u0v9: we NEVER SILENTLY edit `~/.bashrc`,
# `~/.zshrc`, or `config.fish`. The drop-in install below writes NO rc/dotfile at all; the ONLY rc
# write in this module is the fenced remediation stanza (`install_rc_stanza`), which requires
# explicit consent from a human on a TTY, refuses under `--yes`, and never fires non-interactively.
# Instead of editing an rc file, we write the generated
# script into the shell's own auto-discovery directory, which every modern bash-completion
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


def _shell_home() -> Path:
    """The home directory the SHELL sees: ``$HOME`` when set, else ``Path.home()``.

    On POSIX these agree. On Windows ``Path.home()`` reads ``USERPROFILE`` and ignores ``$HOME``,
    but bash (Git Bash, MSYS2, Cygwin) resolves ``~/.bashrc`` and ``~/.local/share`` against
    ``$HOME``, so that is where a completion file or rc stanza must go to be found.
    """
    raw = os.environ.get("HOME")
    return Path(raw) if raw else Path.home()


def _write_text_exact(path: Path, text: str) -> None:
    """Write ``text`` with NO newline translation (a text-mode write emits CRLF on Windows, which
    bash then reads as a stray ``$'\\r'`` on every line)."""
    path.write_bytes(text.encode("utf-8"))


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
    base = Path(raw).expanduser() if raw else _shell_home() / fallback
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
    result identical.

    THIS FUNCTION READS AND WRITES NO USER RC/DOTFILE AT ALL. That is unchanged by compinert 92u0v9,
    which added rc handling as SEPARATE functions (``completion_framework_status`` may READ an rc
    file to report a fact; ``install_rc_stanza`` writes one only on explicit TTY consent). Neither is
    called from here, so this remains a pure drop-in write.

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
    _write_text_exact(primary, _script_with_sentinel(shell))
    primary.chmod(0o644)

    written = [primary]
    for link in aliases:
        if link.exists() or link.is_symlink():
            link.unlink()
        try:
            link.symlink_to(primary.name)
        except OSError:
            # A filesystem without symlink support still gets working completion via a real copy.
            _write_text_exact(link, _script_with_sentinel(shell))
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
    ``skipped``, never deleted. Returns ``{"shell", "dir", "removed", "skipped", "dry_run"}``.

    THIS FUNCTION READS AND WRITES NO USER RC/DOTFILE. Removing the fenced remediation stanza that
    ``install_rc_stanza`` may have appended is ``remove_rc_stanza``'s job, offered by the CLI under
    the same consent rules as the write (``cli._offer_rc_stanza_removal``), so the two directions are
    symmetric without this function acquiring rc authority it does not need.
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


def installed_completion_state(shell: str, target_dir: Optional[Path] = None) -> str:
    """Classify the installed drop-in file for ``shell`` as ``absent``/``current``/``stale``.

    compargs 4y95tp E-06. ``is_completion_installed`` is a PRESENCE check, so an installed script that
    no longer matches what this CLI would generate is indistinguishable from a fresh one: the
    generated file is written once by ``aw completion install`` and NOTHING in the install/upgrade
    path regenerates it, so an upgrade that adds or renames a command leaves the user completing a
    stale vocabulary with no way to find out. This adds the missing third state.

    DETECTION IS A BYTE COMPARISON of the installed body (minus the injected ``INSTALL_SENTINEL``
    line) against a fresh ``generate(shell)``, which is measured sufficient and needs no version
    stamp, timestamp or hash sidecar - each of which would be one more artifact to keep in sync.

    ``absent`` covers both "no file" and "a FOREIGN file" (one without our sentinel), because in both
    cases OUR completion is not installed and the right message is the existing enable-tip, not a
    staleness warning about a file we did not write. READ-ONLY: this never writes or repairs anything.
    """
    try:
        primary = resolve_completion_dir(shell, target_dir) / completion_filename(shell)
    except CompletionInstallError:
        return "absent"
    if not _is_ours(primary):
        return "absent"
    try:
        installed = primary.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "absent"
    body = "\n".join(
        line for line in installed.split("\n") if line.strip() != INSTALL_SENTINEL
    )
    try:
        expected = generate(shell)
    except (
        Exception
    ):  # pragma: no cover - a generator failure is not evidence of staleness
        return "current"
    return "current" if body == expected else "stale"


# ======================================================================================
# compinert Order 01 (92u0v9) E-01..E-03: CAN THE INSTALLED COMPLETION ACTUALLY TAKE EFFECT?
#
# THE DEFECT THIS SECTION EXISTS TO FIX. `aw completion install` writes into a directory whose
# whole purpose is AUTO-DISCOVERY BY THE SHELL'S COMPLETION FRAMEWORK, so that framework being
# loaded is a PRECONDITION of the feature working. The installer checked it nowhere, printed an
# unconditional success line, and told the user to "start a new shell" - which is precisely the
# action that does NOT help when the framework is not sourced for interactive shells. Reported
# 2026-09-12: three OK lines, `exec bash`, and `aw <TAB>` still completed nothing. The install was
# correct; the promise it printed was not.
#
# WHY THREE FACTS AND NOT ONE BOOLEAN (E-01). "bash-completion is not installed on this box" needs
# a package manager; "installed but not sourced from ~/.bashrc" needs one line. A boolean collapses
# those into one word and can only give advice that is wrong for one of them. So the status object
# reports them separately:
#   (a) PRESENT      - an entry script exists on this system (and WHERE it is).
#   (b) REACHABLE    - it is actually loaded in an INTERACTIVE NON-LOGIN shell, which is the case
#                      that fails. Answered by ASKING BASH, never by parsing rc files.
#   (c) RC SOURCES   - the user's own rc already sources it (a READ of the rc file, never a write).
#
# ASKING THE SHELL IS GROUND TRUTH. `bash -ic 'echo ${BASH_COMPLETION_VERSINFO-}'` prints `2` when
# the framework is loaded and EMPTY when it is not. Inferring this from rc-file contents is
# guesswork (sourcing is conditional, nested, and machine-specific); running the shell is the fact.
# The probe is cheap (measured ~0.23s) and any failure/timeout yields UNKNOWN, never a confident
# negative, because telling a user their setup is broken on the strength of a failed probe is worse
# than saying we could not tell.
#
# ZSH AND FISH ASK THE SAME QUESTION WITH DIFFERENT ANSWERS (zsh needs `compinit` to have run; fish
# auto-loads its completions directory), so they report UNKNOWN rather than being forced through
# bash's shape. That is deliberately out of scope here (see the plan's deferred section).
# ======================================================================================

#: The bash-completion entry scripts we look for, in the order a system would prefer them. The
#: `/usr/local` and Homebrew paths matter on macOS and on hand-built installs.
_BASH_COMPLETION_ENTRY_SCRIPTS: Tuple[str, ...] = (
    "/usr/share/bash-completion/bash_completion",
    "/usr/local/share/bash-completion/bash_completion",
    "/opt/homebrew/etc/profile.d/bash_completion.sh",
    "/usr/local/etc/profile.d/bash_completion.sh",
    "/etc/bash_completion",
)

#: How long the interactive-shell probe may take before we call the answer UNKNOWN. An rc file can
#: do arbitrary work at startup, so this is a bound on someone else's code, not on ours.
_PROBE_TIMEOUT_SECONDS = 5.0

#: The three reachability verdicts. UNKNOWN is a first-class answer, not an error: it is what we
#: report for a shell whose check is unimplemented and for a probe that failed or timed out.
REACHABLE_YES = "yes"
REACHABLE_NO = "no"
REACHABLE_UNKNOWN = "unknown"

#: Paired fence markers around the rc stanza (E-03 / F-7). A single sentinel line records where a
#: block BEGINS and nothing about where it ENDS, so uninstall would have to hardcode a line count or
#: re-derive the exact text, and both break the moment a release rewords the stanza. A fenced RANGE
#: can be deleted with no knowledge of its contents and REPLACED in place by an upgrade, so a fix to
#: the stanza can actually reach existing users. Same convention `grok`'s installer uses in the same
#: file, so a user reading their rc sees one shape, not two.
RC_FENCE_OPEN = "# >>> agent-workflows (aw completion install) >>>"
RC_FENCE_CLOSE = "# <<< agent-workflows (aw completion install) <<<"

#: The remediation itself. The `BASH_COMPLETION_VERSINFO` guard is LOAD-BEARING, not decoration:
#: without it this re-sources the whole framework in a login shell that already loaded it. The
#: `shopt -oq posix` guard is the same one Debian's own skeleton rc uses (completion must not load
#: in POSIX mode). The loop covers the same entry-script locations the detector does, so the advice
#: we print matches the fact we measured.
_RC_STANZA_BODY = """\
# Load bash-completion for INTERACTIVE NON-LOGIN shells. On many systems the framework
# is sourced only by /etc/profile.d/bash_completion.sh, which runs for LOGIN shells, so
# a new terminal tab or tmux pane gets no completion at all.
# The BASH_COMPLETION_VERSINFO guard makes this a no-op when it is already loaded.
if ! shopt -oq posix && [ -z "${BASH_COMPLETION_VERSINFO-}" ]; then
    for _bc in /usr/share/bash-completion/bash_completion \\
               /usr/local/share/bash-completion/bash_completion \\
               /etc/bash_completion; do
        [ -r "$_bc" ] && . "$_bc" && break
    done
    unset _bc
fi"""


@dataclass(frozen=True)
class FrameworkStatus:
    """Whether an installed drop-in completion can actually take effect, as SEPARATE facts (E-01).

    THE WHOLE POINT IS THAT THESE DO NOT COLLAPSE. ``present=False`` means the user must install a
    package; ``present=True, reachable="no"`` means one line in an rc file fixes it; ``reachable=
    "unknown"`` means we could not tell and must not claim either way. One boolean cannot carry
    three different pieces of advice, and the defect being fixed here was advice that was wrong for
    the failing case.

    Fields:
      ``shell``         the shell this was measured for.
      ``present``       an entry script exists on this system.
      ``entry_script``  which one (``None`` when absent) - printed so a user can verify it.
      ``reachable``     ``yes``/``no``/``unknown``: is the framework LOADED in an interactive
                        NON-LOGIN shell (the case that silently fails).
      ``rc_sources_it`` the user's rc file already sources it (a READ; see ``rc_path``).
      ``rc_path``       the rc file consulted (``None`` when it does not exist).
      ``rc_has_stanza`` OUR fenced stanza (or a hand-added one with the same fence) is already
                        there, so an offer to add it must be a reported no-op, not a duplicate.
      ``detail``        why a probe answered UNKNOWN, for the message and for debugging.
    """

    shell: str
    present: bool
    entry_script: Optional[str] = None
    reachable: str = REACHABLE_UNKNOWN
    rc_sources_it: bool = False
    rc_path: Optional[Path] = None
    rc_has_stanza: bool = False
    detail: str = ""

    @property
    def effective(self) -> bool:
        """True only when completion demonstrably WILL take effect in a new interactive shell."""
        return self.reachable == REACHABLE_YES

    @property
    def needs_remediation(self) -> bool:
        """True for the one state a one-line rc fix repairs: present on the box, not reachable."""
        return self.present and self.reachable == REACHABLE_NO


def find_bash_completion_entry_script(
    candidates: Optional[Sequence[str]] = None,
) -> Optional[str]:
    """Fact (a): the bash-completion entry script present on this system, or ``None`` (E-01).

    Pure lookup over ``_BASH_COMPLETION_ENTRY_SCRIPTS`` (overridable for tests, which is how E-04
    drives the absent state without touching the real filesystem). Readability, not mere existence,
    is the test: an unreadable script cannot be sourced, so it is not usable here.
    """
    for raw in candidates if candidates is not None else _BASH_COMPLETION_ENTRY_SCRIPTS:
        path = Path(raw)
        try:
            if path.is_file() and os.access(path, os.R_OK):
                return str(path)
        except OSError:
            continue
    return None


def probe_bash_completion_loaded(
    timeout: float = _PROBE_TIMEOUT_SECONDS,
) -> Tuple[str, str]:
    """Fact (b): is bash-completion LOADED in an interactive NON-LOGIN shell? (E-01).

    Returns ``(verdict, detail)`` where verdict is ``yes``/``no``/``unknown``.

    THE DISCRIMINATOR IS `bash -ic 'echo ${BASH_COMPLETION_VERSINFO-}'`, and the two flags are the
    whole measurement: ``-i`` makes it INTERACTIVE (so the rc files that decide this are read) and
    the ABSENCE of ``-l`` makes it NON-LOGIN (so ``/etc/profile.d/bash_completion.sh``, which is
    what loads the framework on many systems, does NOT run). That is exactly the shell a new
    terminal tab or tmux pane gives you, which is why this is the case that fails in the field
    while ``bash -lic`` looks fine.

    ANY FAILURE IS UNKNOWN, NEVER "NO". No bash on the box, a timeout, a nonzero exit, an rc file
    that kills the shell: each means we could not measure, and reporting a confident negative from
    an unmeasured state would tell a user their working setup is broken. Writes nothing, and reads
    no file itself - bash reads the user's rc, which is what makes the answer ground truth rather
    than a guess at what those rc files do.
    """
    try:
        proc = subprocess.run(
            ["bash", "-ic", "echo ${BASH_COMPLETION_VERSINFO-}"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return REACHABLE_UNKNOWN, "no `bash` on PATH to probe"
    except subprocess.TimeoutExpired:
        return REACHABLE_UNKNOWN, f"the `bash -ic` probe timed out after {timeout:g}s"
    except OSError as exc:
        return REACHABLE_UNKNOWN, f"the `bash -ic` probe could not run: {exc}"
    if proc.returncode != 0:
        return (
            REACHABLE_UNKNOWN,
            f"the `bash -ic` probe exited {proc.returncode}",
        )
    # An interactive bash prints its own noise (job-control warnings, MOTD fragments) on stderr and
    # sometimes stdout, so take the LAST non-empty stdout line rather than the whole buffer.
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    value = lines[-1] if lines else ""
    if value:
        return REACHABLE_YES, f"BASH_COMPLETION_VERSINFO={value}"
    return (
        REACHABLE_NO,
        "BASH_COMPLETION_VERSINFO is unset in an interactive non-login shell",
    )


def rc_path_for_shell(shell: str) -> Optional[Path]:
    """The rc file that decides fact (b) for ``shell``, or ``None`` when we model none.

    Bash only: ``~/.bashrc`` is the file an interactive non-login bash reads, and it is therefore
    the only file the remediation belongs in. Zsh and fish are deliberately unmodeled here (their
    preconditions differ in kind), so they get ``None`` and, downstream, an UNKNOWN verdict.
    """
    if shell != "bash":
        return None
    return _shell_home() / ".bashrc"


def _read_rc_text(path: Optional[Path]) -> Optional[str]:
    """Read an rc file's text, or ``None`` when it does not exist / cannot be read.

    READING IS NOT WRITING, and the distinction is drawn deliberately because this feature promises
    nine times over not to WRITE a user rc file. Reporting "your rc already handles this" requires
    looking; it changes nothing, creates nothing, and never touches the file's mtime.
    """
    if path is None:
        return None
    try:
        # newline="": keep the file's own line endings so a rewrite preserves them byte-for-byte.
        with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
            return fh.read()
    except OSError:
        return None


def rc_has_our_stanza(text: Optional[str]) -> bool:
    """True when ``text`` already carries the fenced remediation stanza (E-03).

    KEYED ON THE OPENING FENCE, NOT ON AUTHORSHIP, and that is the opposite of the drop-in FILE
    rule on purpose. A foreign file in the completion directory is refused because it is someone
    else's work we must not clobber; a hand-added stanza with this fence means THE USER ALREADY DID
    THE WORK, so the right answer is "already satisfied, nothing to do" rather than appending a
    second copy. Measured on the reporting machine 2026-09-12: exactly that stanza was there,
    hand-added, before this code existed.
    """
    return bool(text) and RC_FENCE_OPEN in text


def rc_sources_bash_completion(text: Optional[str]) -> bool:
    """True when an rc file's text appears to source bash-completion at all (fact (c)).

    ADVISORY AND DELIBERATELY NOT THE VERDICT. Fact (b) (the probe) decides whether completion
    works; this only explains WHY, and distinguishes "your rc already handles this but something
    else is wrong" from "your rc says nothing about it". A textual scan cannot know whether a
    reference is reached at runtime, which is precisely why it does not get to overrule the probe.
    """
    if not text:
        return False
    return any(
        needle in text
        for needle in ("bash-completion", "bash_completion", "BASH_COMPLETION_VERSINFO")
    )


def completion_framework_status(
    shell: str,
    *,
    entry_script_candidates: Optional[Sequence[str]] = None,
    probe: Optional[Callable[[], Tuple[str, str]]] = None,
    rc_path: Optional[Path] = None,
) -> FrameworkStatus:
    """Report whether ``shell``'s completion framework can load, as three separate facts (E-01).

    PURE IN THE SENSE THAT MATTERS: it writes nothing, anywhere. It READS the rc file to report
    fact (c) and it RUNS `bash -ic` to measure fact (b); neither mutates anything, and the rc read
    is explicitly not a write (see ``_read_rc_text``).

    Every input is INJECTABLE (``entry_script_candidates``, ``probe``, ``rc_path``) because the one
    thing this must not do is answer according to whose machine the tests run on. Measured proof
    that the trap is real: the reporting machine flipped from not-reachable to reachable between
    this plan being authored and reviewed, with no code change, because a human edited their
    ``~/.bashrc``. An ambient-environment test would have silently reversed its verdict.

    NON-BASH SHELLS REPORT UNKNOWN rather than a confident negative. Zsh's precondition is that
    ``compinit`` has run and fish auto-loads its completions directory, so bash's probe says nothing
    about them; claiming otherwise would be a wrong answer dressed as a measurement.
    """
    if shell != "bash":
        return FrameworkStatus(
            shell=shell,
            present=True,
            reachable=REACHABLE_UNKNOWN,
            detail=(
                f"no {shell} completion-framework check is implemented; "
                f"{shell} loads completions by its own rules"
            ),
        )

    entry = find_bash_completion_entry_script(entry_script_candidates)
    resolved_rc = rc_path if rc_path is not None else rc_path_for_shell(shell)
    rc_text = _read_rc_text(resolved_rc)

    if entry is None:
        # Nothing to source: the framework is not on this box, so no rc line can help. Do NOT probe
        # in this state - a "no" here would invite advice (add a line) that cannot possibly work.
        return FrameworkStatus(
            shell=shell,
            present=False,
            entry_script=None,
            reachable=REACHABLE_NO,
            rc_sources_it=rc_sources_bash_completion(rc_text),
            rc_path=resolved_rc if rc_text is not None else None,
            rc_has_stanza=rc_has_our_stanza(rc_text),
            detail="no bash-completion entry script found on this system",
        )

    verdict, detail = (probe or probe_bash_completion_loaded)()
    return FrameworkStatus(
        shell=shell,
        present=True,
        entry_script=entry,
        reachable=verdict,
        rc_sources_it=rc_sources_bash_completion(rc_text),
        rc_path=resolved_rc if rc_text is not None else None,
        rc_has_stanza=rc_has_our_stanza(rc_text),
        detail=detail,
    )


def remediation_snippet(*, fenced: bool = False) -> str:
    """The one-line-ish fix a user can paste, optionally wrapped in the paired fences (E-03).

    ONE SOURCE FOR THE PRINTED AND THE WRITTEN FORM, so the text a user is shown is byte-identical
    to the text a consented write appends. Two copies would drift, and the guard is exactly the
    kind of line that gets dropped from a copy.
    """
    if not fenced:
        return _RC_STANZA_BODY
    return f"{RC_FENCE_OPEN}\n{_RC_STANZA_BODY}\n{RC_FENCE_CLOSE}"


def install_rc_stanza(
    rc_path: Path,
    *,
    consent: bool,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Append the fenced remediation stanza to ``rc_path``, ONLY with explicit consent (E-03).

    THE ONLY CODE IN THIS PACKAGE THAT WRITES A USER DOTFILE, authorized by one maintainer ruling
    (OQ-01, 2026-09-12): OFFER the write, opt-in on a TTY. Every other path in this feature still
    writes no rc file at all, which is why the caller - not this function - owns the prompt: this
    function takes ``consent`` as a fact and REFUSES without it, so no future caller can acquire
    consent by accident. ``--yes`` must never be passed as consent here (it preauthorizes install
    mutations, not a user-scoped choice about their login shell).

    Returns ``{"action", "rc_path", "detail"}`` with ``action`` one of:
      ``written``        the stanza was appended (or WOULD be, under ``dry_run``);
      ``already``        an equivalent fenced stanza is already present - a no-op, reported;
      ``declined``       no consent was given, so nothing happened;
      ``absent``         ``rc_path`` does not exist; we REPORT rather than create it.

    WE DO NOT CREATE AN ABSENT ``~/.bashrc``. Creating it is a bigger act than appending to it: on
    some systems its mere existence changes which startup files bash reads, so a convenience fix
    could silently alter the user's shell startup. Reporting is the honest move.

    THE WRITE IS ATOMIC AND NEVER TRUNCATES. This is the user's login shell configuration, so a
    partial write costs them a working shell. Read-modify-write into a temp file in the same
    directory, then ``os.replace`` (the shape ``install_wizard._persist_policy`` uses), preserving
    the file's existing trailing-newline state instead of normalizing it.
    """
    rc_path = Path(rc_path)
    if not consent:
        return {
            "action": "declined",
            "rc_path": rc_path,
            "detail": "no explicit consent, so nothing was written",
        }
    existing = _read_rc_text(rc_path)
    if existing is None:
        return {
            "action": "absent",
            "rc_path": rc_path,
            "detail": (
                f"{rc_path} does not exist; refusing to CREATE it (creating it can change which "
                "startup files bash reads). Create it yourself, then paste the snippet above."
            ),
        }
    if rc_has_our_stanza(existing):
        return {
            "action": "already",
            "rc_path": rc_path,
            "detail": f"{rc_path} already carries the fenced stanza; nothing to do",
        }
    block = remediation_snippet(fenced=True)
    # Preserve the file's own trailing-newline state: a file that ended mid-line gets its line
    # finished, one that ended cleanly is not given a spurious blank, and either way we never
    # rewrite a byte of the user's existing content.
    # A file ending cleanly gets one blank separator line; a file ending MID-LINE gets its line
    # finished first (`\n`) and then that separator, so we never splice our stanza onto the tail of
    # someone's unterminated command.
    if not existing:
        separator = ""
    else:
        separator = "\n" if existing.endswith("\n") else "\n\n"
    new_text = f"{existing}{separator}{block}\n"
    if dry_run:
        return {
            "action": "written",
            "rc_path": rc_path,
            "detail": f"[dry-run] would append the fenced stanza to {rc_path}",
            "dry_run": True,
        }
    tmp = rc_path.parent / f".{rc_path.name}.aw-tmp"
    try:
        _write_text_exact(tmp, new_text)
        os.replace(tmp, rc_path)
    except OSError:
        # Never leave a half-written temp file behind in the user's home directory.
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    return {
        "action": "written",
        "rc_path": rc_path,
        "detail": f"appended the fenced bash-completion stanza to {rc_path}",
    }


def remove_rc_stanza(rc_path: Path, *, dry_run: bool = False) -> Dict[str, Any]:
    """Remove the fenced remediation stanza from ``rc_path`` if we (or an equal fence) put it there.

    THE SYMMETRY THAT MAKES THE WRITE ACCEPTABLE (E-03). An install that writes with an uninstall
    that abandons the write leaves the user's rc permanently altered by a tool they just removed.
    Because the stanza is FENCED, this deletes a RANGE with no knowledge of its contents, so a
    later release rewording the stanza does not break removal.

    Returns ``{"action", "rc_path", "detail"}`` with ``action`` one of ``removed``, ``absent``
    (no such file) or ``none`` (no stanza to remove). Atomic, like the write.
    """
    rc_path = Path(rc_path)
    existing = _read_rc_text(rc_path)
    if existing is None:
        return {
            "action": "absent",
            "rc_path": rc_path,
            "detail": f"{rc_path} does not exist",
        }
    stripped, removed = _strip_fenced_block(existing)
    if not removed:
        return {
            "action": "none",
            "rc_path": rc_path,
            "detail": f"{rc_path} carries no agent-workflows stanza; left untouched",
        }
    if dry_run:
        return {
            "action": "removed",
            "rc_path": rc_path,
            "detail": f"[dry-run] would remove the fenced stanza from {rc_path}",
            "dry_run": True,
        }
    tmp = rc_path.parent / f".{rc_path.name}.aw-tmp"
    try:
        _write_text_exact(tmp, stripped)
        os.replace(tmp, rc_path)
    except OSError:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    return {
        "action": "removed",
        "rc_path": rc_path,
        "detail": f"removed the fenced bash-completion stanza from {rc_path}",
    }


def _strip_fenced_block(text: str) -> Tuple[str, bool]:
    """Delete every ``RC_FENCE_OPEN``..``RC_FENCE_CLOSE`` range from ``text``.

    Returns ``(new_text, removed_anything)``. An UNTERMINATED opening fence is left ALONE rather
    than deleting to end-of-file: truncating the rest of a user's rc because our closing marker was
    lost would be a far worse failure than leaving a stanza behind. The blank line we inserted
    before the block is absorbed with it, so an install/uninstall round trip restores the file
    byte-for-byte.
    """
    lines = text.splitlines(keepends=True)
    out: List[str] = []
    removed = False
    i = 0
    while i < len(lines):
        if lines[i].strip() == RC_FENCE_OPEN:
            close = None
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == RC_FENCE_CLOSE:
                    close = j
                    break
            if close is None:
                out.append(lines[i])  # unterminated: keep it, never truncate the file.
                i += 1
                continue
            # Absorb the single blank separator line we added ahead of the block, so a round trip
            # is byte-identical rather than leaving a growing run of blank lines.
            if out and out[-1].strip() == "":
                out.pop()
            removed = True
            i = close + 1
            continue
        out.append(lines[i])
        i += 1
    return "".join(out), removed
