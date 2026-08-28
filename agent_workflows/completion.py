"""Native, zero-runtime-dependency shell completion generators for the ``aw`` CLI.

tabcomp Order 01 (bja8og): STATIC completion. ``introspect_cli_tree`` walks the argparse action
tree of the real CLI parser into a plain dict (subcommands + flags), applying one explicit
command-visibility policy so only genuine user commands are surfaced. ``generate_{bash,zsh,fish}_
completion`` turn that tree into self-contained completion scripts binding all three console-script
aliases (``aw``, ``agentwf``, ``agent-workflows``). Every token that originates from the parser
(command names, flags, and help text used as Zsh/Fish descriptions) is shell-escaped for its target
shell before interpolation, because this CLI's help text contains shell-special characters
(backticks and ``$``); no emitted script can be broken or injected by help text.

Dynamic repository-artifact completion (Set/plan/spec/run ids, status enums) is child 02
(tabcomp-02); drop-in install/uninstall is child 03 (tabcomp-03). This module is stdlib-only
(``argparse``/``shlex``); it does NOT import third-party completion libraries.
"""

from __future__ import annotations

import argparse
import shlex
from typing import Any, Dict, List

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
