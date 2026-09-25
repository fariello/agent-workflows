"""Checkout-mismatch detection and automatic re-execution (IPD `wj5b53`, bug `lcmz33`).

When the `aw` console script (or `python -m agent_workflows`) is invoked inside a
checkout of this toolkit whose package differs from the one being imported (e.g.
in a lane worktree when the editable install points at a different checkout),
this module detects the mismatch and re-executes with the invoked checkout's
package prepended to `PYTHONPATH`.

Marker scoping:
`runner_shared._AW_PIN_BOOTSTRAP` sets `AW_PINNED_CHILD=1` to exempt driver-pinned
nested calls. `check_and_reexec` consumes this marker with `os.environ.pop('AW_PINNED_CHILD', None)`
at the moment it reads it, so the exemption is spent by the process it was meant for
and no descendant sees it (F-8).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import agent_workflows


def find_toolkit_checkout(cwd: str | Path | None = None) -> Path | None:
    """Find the enclosing agent_workflows toolkit checkout, if any.

    Walks `cwd` (resolved) and its parents to the first directory containing a
    `.git` entry (file or directory). If found, returns that directory ONLY if
    `<toplevel>/agent_workflows/__init__.py` exists. Returns None if no git entry
    is found or if the git root has no `agent_workflows/__init__.py`.
    """
    if cwd is None:
        target = Path.cwd().resolve()
    else:
        target = Path(cwd).resolve()

    for candidate in [target, *target.parents]:
        git_entry = candidate / ".git"
        if git_entry.exists():
            init_file = candidate / "agent_workflows" / "__init__.py"
            if init_file.is_file():
                return candidate
            return None
    return None


def _launched_by_pin_bootstrap() -> bool:
    """Was this process started by the runner's pinned bootstrap, judged from its OWN argv and env?

    A SECOND, CHILD-SIDE recognition of a driver-pinned call, needed because the `AW_PINNED_CHILD`
    marker lives in the DRIVER's in-memory `_AW_PIN_BOOTSTRAP` string. A driver process that STARTED
    BEFORE the marker existed keeps launching the old bootstrap for its whole lifetime, while every
    child it spawns imports THIS module fresh from disk. Measured on run-20260925T174509Z-636951: the
    driver started at 17:45Z, `wj5b53` landed at 19:21Z, and from then on every pinned finalize
    re-executed into the LANE's package, silently inverting the driver-authoritative contract
    (spec `7ckptx` A8) until `u27oh3`'s lane code refused its own finalize.

    The signature is the bootstrap's own shape, which no console-script `aw` has: the interpreter was
    run with `-c`, the code string runs `agent_workflows` via `runpy.run_module`, and the env carries
    `AW_PIN_KEEP_ROOT` (set only by `runner_shared.pinned_child_env`). All three are required, so an
    agent turn (which also inherits `AW_PIN_KEEP_ROOT` but runs a console script) is NOT exempted,
    preserving the reason plan `wj5b53` F-4 rejected `AW_PIN_KEEP_ROOT` alone. `sys.orig_argv` is
    Python 3.10+; on older interpreters this returns False and only the marker applies.
    """

    if not os.environ.get("AW_PIN_KEEP_ROOT"):
        return False
    orig = list(getattr(sys, "orig_argv", None) or [])
    if "-c" not in orig:
        return False
    idx = orig.index("-c")
    code = orig[idx + 1] if idx + 1 < len(orig) else ""
    return 'runpy.run_module("agent_workflows"' in code


def check_and_reexec() -> None:
    """Check if cwd is inside a different toolkit checkout than the imported one; re-exec on mismatch.

    Exemptions:
    - `AW_PINNED_CHILD=1` (popped so not inherited by descendants)
    - Shell completion requests (`COMP_LINE` or `_ARGCOMPLETE` in env)
    - Roots are equal (`os.path.realpath(toplevel) == os.path.realpath(imported)`)
    - `AW_NO_REEXEC=1` (warns on stderr, does not re-exec)
    - `AW_REEXEC_FROM` is set (loop guard: warns that re-exec did not take effect, does not re-exec)
    """
    try:
        if os.environ.pop("AW_PINNED_CHILD", None) is not None:
            return

        if _launched_by_pin_bootstrap():
            return

        if "COMP_LINE" in os.environ or "_ARGCOMPLETE" in os.environ:
            return

        toplevel = find_toolkit_checkout()
        if toplevel is None:
            return

        imported_root = os.path.realpath(Path(agent_workflows.__file__).parent.parent)
        toplevel_real = os.path.realpath(toplevel)

        if toplevel_real == imported_root:
            return

        if os.environ.get("AW_NO_REEXEC") == "1":
            print(
                f"aw: invoked in checkout {toplevel_real} but imported agent_workflows from {imported_root}; "
                "(AW_NO_REEXEC set; not re-running)",
                file=sys.stderr,
            )
            sys.stderr.flush()
            return

        if os.environ.get("AW_REEXEC_FROM"):
            print(
                f"aw: invoked in checkout {toplevel_real} but imported agent_workflows from {imported_root}; "
                f"still importing {imported_root} after re-exec; continuing",
                file=sys.stderr,
            )
            sys.stderr.flush()
            return

        print(
            f"aw: invoked in checkout {toplevel_real} but imported agent_workflows from {imported_root}; "
            f"re-running with {toplevel_real}'s package (set AW_NO_REEXEC=1 to disable)",
            file=sys.stderr,
        )
        sys.stderr.flush()
        sys.stdout.flush()

        env = os.environ.copy()
        env["AW_REEXEC_FROM"] = imported_root
        current_pp = env.get("PYTHONPATH", "")
        if current_pp:
            env["PYTHONPATH"] = f"{toplevel_real}{os.pathsep}{current_pp}"
        else:
            env["PYTHONPATH"] = toplevel_real

        argv = [sys.executable, "-m", "agent_workflows", *sys.argv[1:]]

        if os.name == "nt":
            import subprocess

            code = subprocess.call(argv, env=env)
            sys.exit(code)
        else:
            os.execve(sys.executable, argv, env)

    except OSError:
        return
