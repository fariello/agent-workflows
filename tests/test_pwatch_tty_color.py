"""Behavioral tests for pwatch --no-color and terminal color decision on a real pty (IPD k6twdf)."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest

try:
    import pty
except ImportError:
    pty = None  # type: ignore[assignment]


REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_pwatch_on_pty(
    argv: list[str],
    env_overrides: dict[str, str | None] | None = None,
) -> tuple[bytes, int]:
    """Run `python -m agent_workflows.pwatch <argv>` on a real pty; return (bytes, exit_code).

    Runs the packaged pwatch under pty.fork. In the child: chdir(REPO_ROOT), sets PYTHONPATH,
    clears NO_COLOR/FORCE_COLOR, sets TERM=xterm-256color plus per-case overrides, and execve immediately.
    The parent drains the master fd until EOF/EIO, waits for child exit, and returns captured bytes and exit code.
    """
    assert pty is not None, "pty module is required"
    pid, fd = pty.fork()
    if pid == 0:  # pragma: no cover - child process replaced by execve
        os.chdir(REPO_ROOT)
        env = dict(os.environ)
        env["PYTHONPATH"] = str(REPO_ROOT)
        env.pop("NO_COLOR", None)
        env.pop("FORCE_COLOR", None)
        env["TERM"] = "xterm-256color"
        if env_overrides:
            for k, v in env_overrides.items():
                if v is None:
                    env.pop(k, None)
                else:
                    env[k] = v
        cmd = [sys.executable, "-m", "agent_workflows.pwatch", *argv]
        os.execve(sys.executable, cmd, env)

    captured = bytearray()
    try:
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            captured.extend(chunk)
    except OSError:
        # Master fd read raises OSError (EIO on Linux) when child exits
        pass
    finally:
        os.close(fd)
        _, status = os.waitpid(pid, 0)

    exit_code = os.waitstatus_to_exitcode(status)
    return bytes(captured), exit_code


@unittest.skipUnless(sys.platform.startswith("linux"), "pwatch requires Linux (/proc)")
@unittest.skipUnless(pty is not None, "pty module is required")
class TestPwatchTtyColor(unittest.TestCase):
    def test_no_color_flag_suppresses_color_on_a_real_tty(self) -> None:
        captured, exit_code = _run_pwatch_on_pty(["--once", "--no-color", "python"])
        self.assertEqual(exit_code, 0)
        self.assertIn(b"pwatch:", captured)
        self.assertNotIn(
            b"\033[",
            captured,
            "pwatch --no-color emitted ANSI escape sequences on a real TTY",
        )

    def test_a_real_tty_gets_color_without_the_flag(self) -> None:
        captured, exit_code = _run_pwatch_on_pty(["--once", "python"])
        self.assertEqual(exit_code, 0)
        self.assertIn(b"pwatch:", captured)
        self.assertIn(
            b"\033[",
            captured,
            "pwatch emitted no ANSI escape sequences on a capable real TTY",
        )

    def test_term_dumb_is_plain_on_a_real_tty(self) -> None:
        captured, exit_code = _run_pwatch_on_pty(
            ["--once", "python"],
            env_overrides={"TERM": "dumb"},
        )
        self.assertEqual(exit_code, 0)
        self.assertIn(b"pwatch:", captured)
        self.assertNotIn(
            b"\033[",
            captured,
            "pwatch under TERM=dumb emitted ANSI escape sequences on a real TTY",
        )


if __name__ == "__main__":
    unittest.main()
