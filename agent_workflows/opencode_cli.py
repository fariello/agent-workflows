"""OpenCode CLI generation detection and argv adaptation (v1 vs v2).

OpenCode v2 changed three things the runner relies on (measured against `opencode v2.2.7`,
2026-11-12):

- `opencode run` no longer accepts `--dir`. The session runs in the process's working directory,
  which the runner already sets (`cwd=` on the launch), so the flag is simply dropped.
- `opencode run` no longer accepts `--variant`. The variant is folded into the model as
  `provider/model#variant`.
- `opencode export <id>` moved to `opencode session export <id>`.

The JSON event stream (`--format json`) is unchanged, so nothing else needs adapting.

Every launch site builds its argv in the v1 shape and passes it through `adapt_run_argv`, so there
is ONE place that knows the difference.
"""

from __future__ import annotations

import functools
import os
import re
import subprocess
from typing import List, Optional, Sequence

_VERSION_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")


def parse_major(version_text: str) -> Optional[int]:
    """The major version in `opencode --version` output (e.g. 'opencode v2.2.7' -> 2), or None."""
    m = _VERSION_RE.search(version_text or "")
    return int(m.group(1)) if m else None


@functools.lru_cache(maxsize=16)
def major_version(binary: str = "opencode") -> Optional[int]:
    """Ask `binary --version` once per process. None when it cannot be determined.

    Never spawns under pytest (`PYTEST_CURRENT_TEST`): a test's fake binary is a script, and running
    it with `--version` would execute the test's side effects. Unknown means "leave argv alone"."""
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return None
    try:
        proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [str(binary), "--version"],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    return parse_major(proc.stdout or proc.stderr or "")


def is_v2(binary: str = "opencode", major: Optional[int] = None) -> bool:
    found = major if major is not None else major_version(str(binary))
    return found is not None and found >= 2


def adapt_run_argv(argv: Sequence[str], major: Optional[int] = None) -> List[str]:
    """Rewrite a v1-shaped `opencode run ...` argv for the installed OpenCode generation.

    `argv[0]` is the binary. Only option tokens BEFORE a `--` separator are rewritten; the prompt
    after it is never touched. On v1 (or an undetectable version) the argv is returned unchanged.
    """
    out = list(argv)
    if len(out) < 2 or out[1] != "run" or not is_v2(out[0], major):
        return out
    try:
        sep = out.index("--")
    except ValueError:
        sep = len(out)
    head, tail = out[:sep], out[sep:]
    result: List[str] = []
    variant: Optional[str] = None
    model_index: Optional[int] = None
    i = 0
    while i < len(head):
        tok = head[i]
        if tok == "--dir" and i + 1 < len(head):
            i += 2
            continue
        if tok == "--variant" and i + 1 < len(head):
            variant = head[i + 1]
            i += 2
            continue
        if tok in ("--model", "-m") and i + 1 < len(head):
            result.extend([tok, head[i + 1]])
            model_index = len(result) - 1
            i += 2
            continue
        result.append(tok)
        i += 1
    if variant:
        if model_index is not None:
            if "#" not in result[model_index]:
                result[model_index] = f"{result[model_index]}#{variant}"
        # v2 has no way to pass a variant without a model; the default model's default variant is
        # used. Dropping it is better than a launch that fails with "Unrecognized flag".
    return result + tail


def adapt_embedded_run_argv(
    argv: Sequence[str], binary: str, major: Optional[int]
) -> List[str]:
    """`adapt_run_argv` for an argv that may carry a wrapper prefix (a sandbox launcher).

    Finds the `<binary> run` segment and adapts only it. `major` is the version already observed;
    None (unknown) leaves the argv unchanged rather than spawning a probe.
    """
    out = list(argv)
    if major is None:
        return out
    for i in range(len(out) - 1):
        if out[i] == str(binary) and out[i + 1] == "run":
            return out[:i] + adapt_run_argv(out[i:], major=major)
    return out


def export_argv(binary: str, session_id: str, major: Optional[int] = None) -> List[str]:
    """The argv that exports a session as JSON on the installed OpenCode generation."""
    if is_v2(binary, major):
        return [str(binary), "session", "export", session_id]
    return [str(binary), "export", session_id]
