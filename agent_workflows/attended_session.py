#!/usr/bin/env python3
"""Open an INTERACTIVE agent session for a plan that needs a human present (`- Attended: required`).

WHY THIS EXISTS (backlog `rfofos`, maintainer ruling 2026-10-18). A plan that asks the maintainer
live questions cannot run in a headless runner turn, so the runners held it ``not-run`` and told the
maintainer to run ``aw work begin <id6>``, which only allocated a worktree. Running the plan then
took four more manual steps: cd into the worktree, start an agent, and tell it to execute the plan.
Every host this toolkit drives can open an interactive session with the first prompt already given,
so this module does that, for both ``aw work begin`` and the runners when they are at a terminal.

THIS IS AN INTERIM ROUTE, AND IT IS RECORDED AS ONE (DECISIONS D176). Plan Set ``qchan`` (``wpv9r7``,
spec ``6kwd2e``) is building a channel through which a HEADLESS runner turn can ask the maintainer a
question and take the answer while the run continues. Once that lands, an attended plan should be
able to run as an ordinary runner turn, and this hand-off to an interactive session becomes the
fallback rather than the only way. Design work on either should read D176.

THE INTERACTIVE FORMS, checked against each host's ``--help`` on 2026-10-18:

- OpenCode: ``opencode <project dir> --prompt <text> [--model M] [--agent A]`` (the TUI, prompt filled).
- Claude Code: ``claude [--model M] <prompt>`` (interactive session with an initial prompt).
- Antigravity: ``agy --prompt-interactive <text> [--model M] [--effort E]``.

THE CHILD OWNS THE TERMINAL. It inherits stdin, stdout and stderr, and is NOT started in a new
session, so the human can type to it and Ctrl-C reaches it. The parent ignores SIGINT while waiting
(restored afterwards), so interrupting the agent does not also kill the run that is waiting for it.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
from pathlib import Path
from typing import Mapping, Sequence

__all__ = [
    "HOSTS",
    "HOST_BINARIES",
    "execute_prompt",
    "build_interactive_argv",
    "run_interactive_session",
    "pick_host",
]

#: The hosts that can be opened interactively, by the name used on the command line.
HOSTS: tuple[str, ...] = ("opencode", "claude", "agy")

#: The default binary for each host, looked up on PATH.
HOST_BINARIES: dict[str, str] = {
    "opencode": "opencode",
    "claude": "claude",
    "agy": "agy",
}

#: Runner ids as the runners and profiles name them, mapped to the interactive host.
RUNNER_TO_HOST: dict[str, str] = {
    "oc": "opencode",
    "opencode": "opencode",
    "agy": "agy",
    "claude": "claude",
}


def execute_prompt(id6: str, *, outcome_path: str | None = None) -> str:
    """The first message the interactive session receives.

    It names the plan and tells the agent the maintainer is present, which is the whole reason the
    session is interactive. ``outcome_path`` is passed when a RUNNER opened the session: the runner
    reads its outcome file afterwards to decide the item's result, exactly as for a headless turn.
    """

    lines = [
        f"Execute plan {id6} now.",
        "This plan is marked `Attended: required`: the maintainer is here with you in this session,",
        "so ask them directly (use /askme) whenever the plan needs a human answer.",
        "Follow the repository's IPD lifecycle and AGENTS.md as usual.",
    ]
    if outcome_path:
        lines.append(
            f"A runner opened this session and is waiting for it. When you are done, write the "
            f"required JSON outcome to {outcome_path} as the runner prompt describes, then tell the "
            "maintainer they can exit this session so the run continues."
        )
    else:
        lines.append(
            "When the plan is executed, tell the maintainer how to land this worktree's branch."
        )
    return " ".join(lines)


def build_interactive_argv(
    host: str,
    *,
    workdir: Path,
    prompt: str,
    binary: str | None = None,
    model: str | None = None,
    variant: str | None = None,
    agent: str | None = None,
) -> list[str]:
    """The argv that opens ``host`` interactively in ``workdir`` with ``prompt`` already given.

    ``variant`` is passed only where the host's interactive mode accepts one (Antigravity's
    ``--effort``); OpenCode's interactive TUI has no ``--variant`` flag, so its variant comes from
    the TUI's own default.
    """

    name = RUNNER_TO_HOST.get(host, host)
    exe = binary or HOST_BINARIES.get(name, name)
    if name == "opencode":
        argv = [exe, str(workdir), "--prompt", prompt]
        if model:
            argv += ["--model", model]
        if agent:
            argv += ["--agent", agent]
        return argv
    if name == "claude":
        argv = [exe]
        if model:
            argv += ["--model", model]
        return argv + [prompt]
    if name == "agy":
        argv = [exe, "--prompt-interactive", prompt]
        if model:
            argv += ["--model", model]
        if variant:
            argv += ["--effort", variant]
        return argv
    raise ValueError(f"unknown interactive host {host!r}; known: {', '.join(HOSTS)}")


def pick_host(preferred: Sequence[str] = ()) -> str | None:
    """The first host in ``preferred`` (then OpenCode, Claude Code, Antigravity) found on PATH."""

    order = [RUNNER_TO_HOST.get(h, h) for h in preferred if h] + list(HOSTS)
    seen: set[str] = set()
    for name in order:
        if name in seen or name not in HOST_BINARIES:
            continue
        seen.add(name)
        if shutil.which(HOST_BINARIES[name]):
            return name
    return None


def run_interactive_session(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
) -> int:
    """Run ``argv`` attached to this terminal and return its exit code (127 when not found)."""

    previous = None
    try:
        previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
    except (ValueError, OSError):  # not the main thread, or no signal support
        previous = None
    try:
        proc = subprocess.Popen(
            list(argv), cwd=str(cwd), env=dict(env) if env is not None else None
        )
        return proc.wait()
    except FileNotFoundError:
        return 127
    finally:
        if previous is not None:
            try:
                signal.signal(signal.SIGINT, previous)
            except (ValueError, OSError):
                pass


def child_env(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    """This process's environment plus ``extra``; the session runs as the maintainer would."""

    env = dict(os.environ)
    if extra:
        env.update({k: str(v) for k, v in extra.items()})
    return env
