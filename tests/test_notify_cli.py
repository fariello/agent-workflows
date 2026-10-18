"""Tests driving the aw notify CLI command family (qchan-11 mrlblc E-04, spec 6kwd2e R10.6, R10.9).

Drives all leaves as subprocesses under the conftest AW_HOME sandbox:
- setup telegram (interactive pty-driven, privacy notice, token prompt, getMe/getWebhookInfo, pairing, tests, lock, non-TTY refusal)
- setup webhook (formats aw, text, ntfy, --url, --url-stdin, redaction of URL path, 500 error handling)
- setup command (argv execution, failure handling)
- status (unconfigured hints, configured channels, safe --agent and --json output)
- disable (user config disabling, unknown channel error, env override rejection)
- test (terse delivery, Telegram button acknowledgment, failing webhook handling)
- listen (foreground listener, lock coordination, routing inbound answers to finished runs, SIGTERM cleanup)
- doc parse check: verifies every 'aw notify ...' invocation in docs/notifications.md against cli._build_parser()
"""

from __future__ import annotations

import http.server
import json
import os
from pathlib import Path
import re
import select
import signal
import stat
import subprocess
import sys
import threading
import time
from typing import Any

from filelock import FileLock
import pytest

from agent_workflows import cli, question_inbox
from agent_workflows.notify import registry
from tests.fake_telegram import run_fake_telegram

pytestmark = pytest.mark.core

REPO_ROOT = Path(__file__).resolve().parent.parent


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _run_cli_subprocess(
    argv: list[str],
    *,
    env: dict[str, str],
    stdin_data: str | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run `sys.executable -m agent_workflows notify ...` with captured I/O."""
    cmd = [sys.executable, "-m", "agent_workflows", "notify", *argv]
    return subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        input=stdin_data,
        capture_output=True,
        text=True,
        env=env,
    )


def _run_scripted_pty(
    argv: list[str],
    *,
    env: dict[str, str],
    interactions: list[tuple[str, bytes]] | None = None,
    dynamic_handler: Any | None = None,
    timeout: float = 15.0,
    cwd: Path | None = None,
) -> tuple[int, str]:
    """Run `sys.executable -m agent_workflows notify ...` on a POSIX pty with scripted interaction."""
    if sys.platform == "win32":
        pytest.skip("pty is not available on Windows")

    import pty

    cmd = [sys.executable, "-m", "agent_workflows", "notify", *argv]
    pid, master_fd = pty.fork()
    if pid == 0:  # Child process replaced by execve
        os.chdir(str(cwd or REPO_ROOT))
        os.execve(sys.executable, cmd, env)

    os.set_blocking(master_fd, False)
    output = bytearray()
    start_time = time.time()
    interaction_idx = 0
    child_exited = False
    exit_status = 0

    while time.time() - start_time < timeout:
        r, _, _ = select.select([master_fd], [], [], 0.05)
        if r:
            try:
                chunk = os.read(master_fd, 4096)
                if not chunk:
                    break
                output.extend(chunk)
            except OSError:
                break

        out_str = output.decode("utf-8", errors="replace")

        # Static scripted interaction trigger -> response
        if interactions and interaction_idx < len(interactions):
            trigger, response = interactions[interaction_idx]
            if trigger in out_str:
                if response:
                    os.write(master_fd, response)
                interaction_idx += 1

        # Dynamic callback interaction
        if dynamic_handler is not None:
            dynamic_handler(out_str, master_fd)

        # Check if child process has exited
        wpid, ws = os.waitpid(pid, os.WNOHANG)
        if wpid == pid:
            child_exited = True
            exit_status = ws
            break

    # Drain any remaining bytes from master_fd
    try:
        while True:
            chunk = os.read(master_fd, 4096)
            if not chunk:
                break
            output.extend(chunk)
    except OSError:
        pass
    os.close(master_fd)

    if not child_exited:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.1)
            wpid, ws = os.waitpid(pid, os.WNOHANG)
            if wpid == 0:
                os.kill(pid, signal.SIGKILL)
                _, ws = os.waitpid(pid, 0)
            exit_status = ws
        except ProcessLookupError:
            pass
        except ChildProcessError:
            pass

    return os.waitstatus_to_exitcode(exit_status), output.decode(
        "utf-8", errors="replace"
    )


class _LoopbackWebhookServer:
    """Threaded loopback HTTP server recording webhook payloads."""

    def __init__(self, status_code: int = 200):
        self.status_code = status_code
        self.received_requests: list[dict[str, Any]] = []
        self._server: http.server.ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self.port: int = 0

    def start(self) -> None:
        outer = self

        class _Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                pass

            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length) if length > 0 else b""
                outer.received_requests.append(
                    {
                        "path": self.path,
                        "headers": dict(self.headers),
                        "body_bytes": body,
                        "body_text": body.decode("utf-8", errors="replace"),
                    }
                )
                self.send_response(outer.status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"{}")

        self._server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.port = self._server.server_port
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"


# -----------------------------------------------------------------------------
# Test Cases
# -----------------------------------------------------------------------------


def test_setup_telegram_refuses_non_tty(tmp_path: Path) -> None:
    """setup telegram refuses non-interactive execution with exit 2 and writes no file (E-01, A54)."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True)
    env = dict(os.environ)
    env["AW_HOME"] = str(aw_home)
    env["PYTHONPATH"] = str(REPO_ROOT)

    # 1. Non-interactive stdin (DEVNULL)
    res = _run_cli_subprocess(["setup", "telegram"], env=env, stdin_data=None)
    assert res.returncode == 2
    assert "interactive terminal" in res.stderr
    assert not (aw_home / "notify.json").exists()

    # 2. Refuses --agent flag
    res_agent = _run_cli_subprocess(
        ["setup", "telegram", "--agent"], env=env, stdin_data=None
    )
    assert res_agent.returncode == 2
    assert "--agent" in res_agent.stderr
    assert not (aw_home / "notify.json").exists()


def test_setup_telegram_wrong_token(tmp_path: Path) -> None:
    """setup telegram with an invalid token exits nonzero and writes nothing (E-01)."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True)

    with run_fake_telegram() as fake:
        env = dict(os.environ)
        env["AW_HOME"] = str(aw_home)
        env["AW_NOTIFY_TELEGRAM_BASE_URL"] = fake.base_url
        env["PYTHONPATH"] = str(REPO_ROOT)

        # fake_telegram returns 401 when token contains 'invalid'
        code, out = _run_scripted_pty(
            ["setup", "telegram"],
            env=env,
            interactions=[("Enter Telegram bot token:", b"invalid_token_12345\n")],
        )

        assert code != 0
        assert "Error verifying bot token" in out or "401" in out
        assert not (aw_home / "notify.json").exists()


def test_setup_telegram_declined_webhook_deletion(tmp_path: Path) -> None:
    """setup telegram exits 1 and writes nothing when active webhook deletion is declined (E-01)."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True)

    with run_fake_telegram() as fake:
        fake.webhook_url = "https://example.com/existing-webhook"
        env = dict(os.environ)
        env["AW_HOME"] = str(aw_home)
        env["AW_NOTIFY_TELEGRAM_BASE_URL"] = fake.base_url
        env["PYTHONPATH"] = str(REPO_ROOT)

        code, out = _run_scripted_pty(
            ["setup", "telegram"],
            env=env,
            interactions=[
                ("Enter Telegram bot token:", b"123456789:ABCfakeTokenXYZ\n"),
                ("Delete active webhook? [y/N]:", b"n\n"),
            ],
        )

        assert code == 1
        assert "Webhook deletion declined" in out
        assert not (aw_home / "notify.json").exists()


def test_setup_telegram_declined_identity(tmp_path: Path) -> None:
    """setup telegram exits 1 and writes nothing when pairing identity is declined (E-01)."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True)

    with run_fake_telegram() as fake:
        env = dict(os.environ)
        env["AW_HOME"] = str(aw_home)
        env["AW_NOTIFY_TELEGRAM_BASE_URL"] = fake.base_url
        env["PYTHONPATH"] = str(REPO_ROOT)

        token_sent = False
        pairing_sent = False
        declined_sent = False

        def handler(out_str: str, master_fd: int) -> None:
            nonlocal token_sent, pairing_sent, declined_sent
            if "Enter Telegram bot token:" in out_str and not token_sent:
                os.write(master_fd, b"123456789:ABCfakeTokenXYZ\n")
                token_sent = True
            m = re.search(r"start=([a-zA-Z0-9_-]+)", out_str)
            if m and not pairing_sent:
                phrase = m.group(1)
                fake.add_text_update(
                    update_id=1,
                    user_id=101010,
                    chat_id=101010,
                    text=f"/start {phrase}",
                )
                pairing_sent = True
            if "Confirm identity and pair? [y/N]:" in out_str and not declined_sent:
                os.write(master_fd, b"n\n")
                declined_sent = True

        code, out = _run_scripted_pty(
            ["setup", "telegram"],
            env=env,
            dynamic_handler=handler,
        )

        assert code == 1
        assert "Identity confirmation declined" in out
        assert not (aw_home / "notify.json").exists()


def test_setup_telegram_held_lock(tmp_path: Path) -> None:
    """setup telegram exits 1 with remedy message when receiver lock is held (E-01)."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True)
    notify_dir = aw_home / "notify"
    notify_dir.mkdir(parents=True)

    # Pre-acquire the lock for bot ID 123456789
    lock_file = notify_dir / "telegram-123456789.lock"
    holder_lock = FileLock(str(lock_file), timeout=1)
    holder_lock.acquire()

    try:
        with run_fake_telegram() as fake:
            env = dict(os.environ)
            env["AW_HOME"] = str(aw_home)
            env["AW_NOTIFY_TELEGRAM_BASE_URL"] = fake.base_url
            env["PYTHONPATH"] = str(REPO_ROOT)

            code, out = _run_scripted_pty(
                ["setup", "telegram"],
                env=env,
                interactions=[
                    ("Enter Telegram bot token:", b"123456789:ABCfakeTokenXYZ\n")
                ],
            )

            assert code == 1
            assert "stop the run or use a second bot" in out
            assert not (aw_home / "notify.json").exists()
    finally:
        holder_lock.release()


def test_setup_telegram_interactive_success(tmp_path: Path) -> None:
    """Guided Telegram setup completes pairing, verification tests, and saves 0600 config (E-01, V-01)."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True)

    with run_fake_telegram() as fake:
        env = dict(os.environ)
        env["AW_HOME"] = str(aw_home)
        env["AW_NOTIFY_TELEGRAM_BASE_URL"] = fake.base_url
        env["PYTHONPATH"] = str(REPO_ROOT)

        token_sent = False
        pairing_sent = False
        confirm_sent = False
        test_sent = False

        def handler(out_str: str, master_fd: int) -> None:
            nonlocal token_sent, pairing_sent, confirm_sent, test_sent
            if "Enter Telegram bot token:" in out_str and not token_sent:
                os.write(master_fd, b"123456789:ABCfakeTokenXYZ\n")
                token_sent = True

            m = re.search(r"start=([a-zA-Z0-9_-]+)", out_str)
            if m and not pairing_sent:
                phrase = m.group(1)
                # 1. Ignored group message with phrase (chat_type="group")
                fake.add_text_update(
                    update_id=1,
                    user_id=88888,
                    chat_id=88888,
                    text=f"group {phrase}",
                    chat_type="group",
                )
                # 2. Ignored bot message with phrase
                fake.add_text_update(
                    update_id=2,
                    user_id=77777,
                    chat_id=77777,
                    text=f"/start {phrase}",
                    is_bot=True,
                )
                # 3. Valid private pairing message from user 424242
                fake.add_text_update(
                    update_id=3,
                    user_id=424242,
                    chat_id=424242,
                    text=f"/start {phrase}",
                )
                pairing_sent = True

            if "Confirm identity and pair? [y/N]:" in out_str and not confirm_sent:
                os.write(master_fd, b"y\n")
                confirm_sent = True

            if "Sending test question with buttons" in out_str and not test_sent:
                if fake.sent_messages:
                    msg_id = fake.sent_messages[-1]["message_id"]
                    # Button from wrong user -> ignored
                    fake.add_button_update(
                        update_id=4,
                        user_id=99999,
                        chat_id=99999,
                        message_id=msg_id,
                        callback_data="setup:opt1",
                    )
                    # Button from paired user -> accepted
                    fake.add_button_update(
                        update_id=5,
                        user_id=424242,
                        chat_id=424242,
                        message_id=msg_id,
                        callback_data="setup:opt1",
                    )
                    # Reply from wrong user -> ignored
                    fake.add_text_update(
                        update_id=6,
                        user_id=99999,
                        chat_id=99999,
                        text="unauthorized reply",
                        reply_to_message_id=msg_id,
                    )
                    # Reply from paired user -> accepted
                    fake.add_text_update(
                        update_id=7,
                        user_id=424242,
                        chat_id=424242,
                        text="authorized reply",
                        reply_to_message_id=msg_id,
                    )
                    test_sent = True

        code, out = _run_scripted_pty(
            ["setup", "telegram"],
            env=env,
            dynamic_handler=handler,
        )

        assert code == 0, f"Setup exited {code}. Output:\n{out}"
        assert "Privacy & Data Notice for Telegram Notifications:" in out
        assert "Verified bot: @fake_bot" in out
        assert "Detected pairing request:" in out
        assert "User ID: 424242" in out
        assert "Button click confirmed." in out
        assert "Threaded reply confirmed." in out
        assert "Setup complete! Telegram notifications configured." in out
        assert "mode: terse" in out

        # Verify config saved with 0600 mode and mode: terse
        cfg_file = aw_home / "notify.json"
        assert cfg_file.is_file()
        file_mode = stat.S_IMODE(cfg_file.stat().st_mode)
        assert file_mode == 0o600

        data = json.loads(cfg_file.read_text(encoding="utf-8"))
        assert data["telegram"]["enabled"] is True
        assert data["telegram"]["token"] == "123456789:ABCfakeTokenXYZ"
        assert data["telegram"]["user_id"] == "424242"
        assert data["telegram"]["chat_id"] == "424242"
        assert data["telegram"]["mode"] == "terse"


def test_setup_webhook_aw_and_text(tmp_path: Path) -> None:
    """setup webhook sends test notification and saves config for aw and text formats (E-05, V-05)."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True)
    server = _LoopbackWebhookServer(status_code=200)
    server.start()

    try:
        env = dict(os.environ)
        env["AW_HOME"] = str(aw_home)
        env["PYTHONPATH"] = str(REPO_ROOT)

        # 1. format: aw
        url_aw = f"{server.base_url}/secret/path/aw"
        res_aw = _run_cli_subprocess(
            ["setup", "webhook", "--url", url_aw, "--format", "aw"], env=env
        )
        assert res_aw.returncode == 0
        assert "/secret/path/aw" not in res_aw.stdout
        assert "/secret/path/aw" not in res_aw.stderr
        req_aw = server.received_requests[-1]
        assert req_aw["path"] == "/secret/path/aw"
        body_aw = json.loads(req_aw["body_text"])
        assert "run_id" in body_aw

        # 2. format: text
        url_text = f"{server.base_url}/secret/path/text"
        res_text = _run_cli_subprocess(
            ["setup", "webhook", "--url", url_text, "--format", "text"], env=env
        )
        assert res_text.returncode == 0
        assert "/secret/path/text" not in res_text.stdout
        assert "/secret/path/text" not in res_text.stderr
        req_text = server.received_requests[-1]
        assert req_text["path"] == "/secret/path/text"
        assert "aw notify setup" in req_text["body_text"]
    finally:
        server.stop()


def test_setup_webhook_ntfy_and_stdin(tmp_path: Path) -> None:
    """setup webhook supports ntfy format and --url-stdin with path redaction (E-05, V-05)."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True)
    server = _LoopbackWebhookServer(status_code=200)
    server.start()

    try:
        env = dict(os.environ)
        env["AW_HOME"] = str(aw_home)
        env["PYTHONPATH"] = str(REPO_ROOT)

        # 1. format: ntfy
        url_ntfy = f"{server.base_url}/secret/path/ntfy"
        res_ntfy = _run_cli_subprocess(
            ["setup", "webhook", "--url", url_ntfy, "--format", "ntfy"], env=env
        )
        assert res_ntfy.returncode == 0
        assert "/secret/path/ntfy" not in res_ntfy.stdout
        assert "/secret/path/ntfy" not in res_ntfy.stderr
        req_ntfy = server.received_requests[-1]
        assert req_ntfy["path"] == "/secret/path/ntfy"
        assert "aw notify setup" in req_ntfy["body_text"]
        assert "Title" in req_ntfy["headers"]

        # 2. --url-stdin reads URL without echo
        url_stdin = f"{server.base_url}/secret/path/stdin"
        res_stdin = _run_cli_subprocess(
            ["setup", "webhook", "--url-stdin", "--format", "aw"],
            env=env,
            stdin_data=f"{url_stdin}\n",
        )
        assert res_stdin.returncode == 0
        assert "/secret/path/stdin" not in res_stdin.stdout
        assert "/secret/path/stdin" not in res_stdin.stderr

        # Verify saved config in notify.json
        cfg_file = aw_home / "notify.json"
        assert cfg_file.is_file()
        cfg_data = json.loads(cfg_file.read_text(encoding="utf-8"))
        assert cfg_data["webhook"]["enabled"] is True
        assert cfg_data["webhook"]["url"] == url_stdin
        assert cfg_data["webhook"]["format"] == "aw"
        assert cfg_data["webhook"]["mode"] == "terse"
    finally:
        server.stop()


def test_setup_webhook_500_failure(tmp_path: Path) -> None:
    """setup webhook exits 1 and writes nothing when endpoint returns HTTP 500 (E-05, V-05)."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True)
    server = _LoopbackWebhookServer(status_code=500)
    server.start()

    try:
        env = dict(os.environ)
        env["AW_HOME"] = str(aw_home)
        env["PYTHONPATH"] = str(REPO_ROOT)

        url_fail = f"{server.base_url}/secret/fail/500"
        res = _run_cli_subprocess(["setup", "webhook", "--url", url_fail], env=env)
        assert res.returncode == 1
        assert "Webhook test failed" in res.stderr
        assert not (aw_home / "notify.json").exists()
        assert "/secret/fail/500" not in res.stdout
        assert "/secret/fail/500" not in res.stderr
    finally:
        server.stop()


def test_setup_command_lifecycle(tmp_path: Path) -> None:
    """setup command runs test execution and saves config only on success (E-05)."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True)
    env = dict(os.environ)
    env["AW_HOME"] = str(aw_home)
    env["PYTHONPATH"] = str(REPO_ROOT)

    # 1. Success script
    script_ok = tmp_path / "dummy_ok.py"
    output_log = tmp_path / "cmd_output.log"
    script_ok.write_text(
        f"import sys, pathlib\n"
        f"pathlib.Path({str(output_log)!r}).write_text('OK ' + ' '.join(sys.argv[1:]))\n"
        f"sys.exit(0)\n",
        encoding="utf-8",
    )

    res_ok = _run_cli_subprocess(
        ["setup", "command", "--", sys.executable, str(script_ok), "--flag"],
        env=env,
    )
    assert res_ok.returncode == 0
    assert output_log.is_file()
    assert "--flag" in output_log.read_text(encoding="utf-8")

    cfg_file = aw_home / "notify.json"
    assert cfg_file.is_file()
    cfg_data = json.loads(cfg_file.read_text(encoding="utf-8"))
    assert cfg_data["command"]["enabled"] is True
    assert cfg_data["command"]["command"] == [sys.executable, str(script_ok), "--flag"]
    assert cfg_data["command"]["mode"] == "terse"

    # 2. Failure script: exits 1 and overwrites nothing
    script_fail = tmp_path / "dummy_fail.py"
    script_fail.write_text("import sys\nsys.exit(1)\n", encoding="utf-8")

    res_fail = _run_cli_subprocess(
        ["setup", "command", "--", sys.executable, str(script_fail)],
        env=env,
    )
    assert res_fail.returncode == 1
    assert "Command hook test failed" in res_fail.stderr


def test_status_unconfigured(tmp_path: Path) -> None:
    """status displays setup hints when unconfigured, and safe agent output (E-02, V-02)."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True)
    env = dict(os.environ)
    env["AW_HOME"] = str(aw_home)
    env["PYTHONPATH"] = str(REPO_ROOT)

    res_unconf = _run_cli_subprocess(["status"], env=env)
    assert res_unconf.returncode == 0
    assert "No notification channels configured." in res_unconf.stdout
    assert "aw notify setup telegram" in res_unconf.stdout

    res_unconf_agent = _run_cli_subprocess(["status", "--agent"], env=env)
    assert res_unconf_agent.returncode == 0
    rec = json.loads(res_unconf_agent.stdout)
    assert rec["schema"] == "aw.agent/v1"
    assert rec["cmd"] == "notify status"
    assert rec["exit"] == 0


def test_status_configured(tmp_path: Path) -> None:
    """status displays channel details when configured without leaking tokens or paths (E-02, V-02)."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True)
    env = dict(os.environ)
    env["AW_HOME"] = str(aw_home)
    env["PYTHONPATH"] = str(REPO_ROOT)

    cfg_file = aw_home / "notify.json"
    cfg_file.write_text(
        json.dumps(
            {
                "telegram": {
                    "enabled": True,
                    "token": "secret_token_value_xyz",
                    "chat_id": "987654321",
                    "user_id": "987654321",
                    "mode": "terse",
                },
                "webhook": {
                    "enabled": True,
                    "url": "https://hooks.example.com/secret/path/token123",
                    "format": "aw",
                    "mode": "terse",
                },
            }
        ),
        encoding="utf-8",
    )

    res_conf = _run_cli_subprocess(["status"], env=env)
    assert res_conf.returncode == 0
    assert "Channel: telegram" in res_conf.stdout
    assert "Channel: webhook" in res_conf.stdout
    assert "secret_token_value_xyz" not in res_conf.stdout
    assert "987654321" not in res_conf.stdout
    assert "/secret/path/token123" not in res_conf.stdout

    res_agent = _run_cli_subprocess(["status", "--agent"], env=env)
    assert res_agent.returncode == 0
    agent_out = res_agent.stdout
    assert "secret_token_value_xyz" not in agent_out
    assert "987654321" not in agent_out
    assert "/secret/path/token123" not in agent_out
    rec = json.loads(agent_out)
    assert rec["schema"] == "aw.agent/v1"
    assert rec["cmd"] == "notify status"
    assert rec["exit"] == 0

    res_json = _run_cli_subprocess(["status", "--json"], env=env)
    assert res_json.returncode == 0
    json_out = res_json.stdout
    assert "secret_token_value_xyz" not in json_out
    assert "987654321" not in json_out
    assert "/secret/path/token123" not in json_out
    jdata = json.loads(json_out)
    assert "channels" in jdata
    assert "telegram" in jdata["channels"]
    assert "webhook" in jdata["channels"]


def test_disable_and_env_protection(tmp_path: Path) -> None:
    """disable disables user channels, rejects unknown channels, and protects env overrides (E-02)."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True)
    cfg_file = aw_home / "notify.json"
    cfg_file.write_text(
        json.dumps(
            {
                "telegram": {
                    "enabled": True,
                    "token": "token123",
                    "chat_id": "123",
                    "mode": "terse",
                }
            }
        ),
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["AW_HOME"] = str(aw_home)
    env["PYTHONPATH"] = str(REPO_ROOT)

    # 1. Disable existing telegram channel
    res = _run_cli_subprocess(["disable", "telegram"], env=env)
    assert res.returncode == 0
    cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
    assert cfg["telegram"]["enabled"] is False

    # 2. Disable unknown channel exits 1 (E-02)
    res_unk = _run_cli_subprocess(["disable", "foobar"], env=env)
    assert res_unk.returncode == 1
    assert "Unknown channel" in res_unk.stderr

    # 3. Disable channel configured via env
    env["AW_NOTIFY_WEBHOOK_URL"] = "https://example.com/webhook"
    res_env = _run_cli_subprocess(["disable", "webhook"], env=env)
    assert res_env.returncode == 1
    assert "AW_NOTIFY_WEBHOOK_URL" in res_env.stderr


def test_notify_test_webhook_success(tmp_path: Path) -> None:
    """test sends verification notifications to working webhook (E-02, V-02)."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True)
    server_ok = _LoopbackWebhookServer(status_code=200)
    server_ok.start()

    try:
        env = dict(os.environ)
        env["AW_HOME"] = str(aw_home)
        env["PYTHONPATH"] = str(REPO_ROOT)

        cfg_file = aw_home / "notify.json"
        cfg_file.write_text(
            json.dumps(
                {
                    "webhook": {
                        "enabled": True,
                        "url": f"{server_ok.base_url}/hook",
                        "format": "aw",
                        "mode": "terse",
                    }
                }
            ),
            encoding="utf-8",
        )
        res_ok = _run_cli_subprocess(["test", "webhook"], env=env)
        assert res_ok.returncode == 0
        assert "Webhook test delivered" in res_ok.stdout
    finally:
        server_ok.stop()


def test_notify_test_webhook_failure(tmp_path: Path) -> None:
    """test exits 1 when webhook test fails (E-02, V-02)."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True)
    server_fail = _LoopbackWebhookServer(status_code=500)
    server_fail.start()

    try:
        env = dict(os.environ)
        env["AW_HOME"] = str(aw_home)
        env["PYTHONPATH"] = str(REPO_ROOT)

        cfg_file = aw_home / "notify.json"
        cfg_file.write_text(
            json.dumps(
                {
                    "webhook": {
                        "enabled": True,
                        "url": f"{server_fail.base_url}/fail",
                        "format": "aw",
                        "mode": "terse",
                    }
                }
            ),
            encoding="utf-8",
        )
        res_fail = _run_cli_subprocess(["test", "webhook"], env=env)
        assert res_fail.returncode == 1
        assert "Webhook test failed" in res_fail.stderr
    finally:
        server_fail.stop()


def test_listen_lifecycle_and_answering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """listen coordinates lock, routes inbound Telegram answers to finished runs, and exits 0 on SIGTERM (E-06, V-06)."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True)
    monkeypatch.setenv("AW_HOME", str(aw_home))
    run_dir = tmp_path / "run_finished"
    run_dir.mkdir(parents=True)

    # Write a registered open question in run_dir through question_inbox
    plan1 = tmp_path / "20261017-qchan-09-it0001-test.ipd.md"
    plan1.write_text("# Plan it0001\n- Id: it0001\n", encoding="utf-8")
    item1 = {
        "position": 1,
        "id6": "it0001",
        "current_attempt": 1,
        "configured_file": str(plan1),
        "artifact_path": str(plan1),
        "repo": str(tmp_path),
    }
    qid = "01-it0001-a1-q1"
    question_inbox.write_question(
        run_dir=run_dir,
        item=item1,
        question={
            "question_id": qid,
            "text": "Choose deploy target",
            "options": ["Staging", "Production"],
            "allow_free_text": True,
        },
        attempt=1,
        repo=tmp_path,
    )

    with run_fake_telegram() as fake:
        env = dict(os.environ)
        env["AW_HOME"] = str(aw_home)
        env["AW_NOTIFY_TELEGRAM_BASE_URL"] = fake.base_url
        env["PYTHONPATH"] = str(REPO_ROOT)

        # 1. Listen without telegram configured -> exits 1 with hint
        res_notg = _run_cli_subprocess(["listen"], env=env)
        assert res_notg.returncode == 1
        assert "setup telegram" in res_notg.stderr

        # Configure telegram channel
        cfg_file = aw_home / "notify.json"
        cfg_file.write_text(
            json.dumps(
                {
                    "telegram": {
                        "enabled": True,
                        "token": "123456789:ABCtokenXYZ",
                        "chat_id": "424242",
                        "user_id": "424242",
                        "mode": "terse",
                    }
                }
            ),
            encoding="utf-8",
        )

        # Register routing token for question Q1
        registry.register(
            channel="telegram",
            key="btn_tok_123",
            run_dir=run_dir,
            question_id=qid,
            option=1,
        )

        # Start primary listen process
        listen_cmd = [sys.executable, "-m", "agent_workflows", "notify", "listen"]
        proc1 = subprocess.Popen(
            listen_cmd,
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        try:
            # Wait for proc1 to acquire lock
            bot_id = "123456789"
            t_lock_start = time.time()
            while (
                time.time() - t_lock_start < 2.0
                and not (aw_home / "notify" / f"telegram-{bot_id}.lock.pid").exists()
            ):
                time.sleep(0.02)

            # 2. Second listen process attempts to start and is rejected
            res_second = _run_cli_subprocess(["listen"], env=env)
            assert res_second.returncode == 1
            assert "receiver lock held" in res_second.stderr
            assert str(proc1.pid) in res_second.stderr

            # 3. Simulate button press update for btn_tok_123
            fake.add_button_update(
                update_id=101,
                user_id=424242,
                chat_id=424242,
                message_id=5000,
                callback_data="btn_tok_123",
            )

            # Wait for answer file to be written
            answer_file = run_dir / "answers" / f"{qid}.json"
            deadline = time.time() + 5.0
            while time.time() < deadline and not answer_file.exists():
                time.sleep(0.05)

            assert (
                answer_file.is_file()
            ), f"Expected answer file {answer_file} to be created"
            ans_data = json.loads(answer_file.read_text(encoding="utf-8"))
            assert ans_data["channel"] == "telegram"
            assert ans_data["choice"] == 1

            # 4. Terminate proc1 with SIGTERM
            time.sleep(0.1)
            proc1.send_signal(signal.SIGTERM)
            stdout1, stderr1 = proc1.communicate(timeout=5.0)
            assert (
                proc1.returncode in (0, 1)
                if sys.platform == "win32"
                else proc1.returncode == 0
            )
            if sys.platform != "win32":
                assert "Answer recorded" in stdout1

            # Lock file should now be free
            bot_lock = aw_home / "notify" / "telegram-123456789.lock"
            test_lock = FileLock(str(bot_lock), timeout=0)
            test_lock.acquire()
            test_lock.release()
        finally:
            if proc1.poll() is None:
                proc1.kill()
                proc1.communicate()


def test_docs_notifications_command_lines_parse() -> None:
    """Every 'aw notify ...' command line in docs/notifications.md parses under real CLI parser (E-03, E-04)."""
    doc_path = REPO_ROOT / "docs" / "notifications.md"
    assert doc_path.is_file()

    doc_text = doc_path.read_text(encoding="utf-8")
    parser = cli._build_parser()

    # Find code blocks and inline command references
    command_lines: list[str] = []
    for line in doc_text.splitlines():
        line = line.strip()
        if line.startswith("aw notify ") or line.startswith("$ aw notify "):
            cmd = line.lstrip("$ ").strip()
            # Omit shell pipes or comments if any
            cmd = cmd.split("#")[0].strip()
            command_lines.append(cmd)

    assert (
        len(command_lines) >= 8
    ), f"Expected at least 8 command examples, found {len(command_lines)}"

    for cmd_str in command_lines:
        tokens = cmd_str.split()
        assert tokens[:2] == ["aw", "notify"]
        argv = tokens[1:]  # ["notify", ...]
        try:
            parsed = parser.parse_args(argv)
            assert getattr(parsed, "command", None) == "notify"
        except SystemExit as err:
            pytest.fail(
                f"Command line from doc failed to parse: {cmd_str!r} (exit {err.code})"
            )
