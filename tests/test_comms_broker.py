"""Tests for agent_workflows.comms_broker (IPD nomhl1)."""

from __future__ import annotations

import http.server
import json
import socket
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agent_workflows import comms
from agent_workflows.comms_broker import (
    NUDGE,
    build_restricted_opener,
    deliver,
    main,
    read_header_only,
    scan_once,
    url_policy_refusal,
)


# --- Helpers and Fixtures ----------------------------------------------------------------------


class MockOpenCodeServer(http.server.HTTPServer):
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.received_requests: list[dict] = []


class MockHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # Silence logging
        pass

    def _handle_request(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        self.server.received_requests.append(
            {
                "path": self.path,
                "headers": dict(self.headers),
                "body": body,
            }
        )
        if self.path.startswith("/session/") and self.path.endswith("/prompt_async"):
            if "bogus" in self.path:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'{"name":"NotFoundError"}')
            else:
                self.send_response(204)
                self.end_headers()
        elif self.path == "/redirect_to_external":
            self.send_response(302)
            self.send_header("Location", "http://example.com/evil")
            self.end_headers()
        elif self.path == "/redirect_to_loopback":
            self.send_response(302)
            self.send_header(
                "Location",
                f"http://127.0.0.1:{self.server.server_port}/session/test-session-123/prompt_async",
            )
            self.end_headers()
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"true")

    def do_GET(self):
        self._handle_request()

    def do_POST(self):
        self._handle_request()


@pytest.fixture
def mock_server():
    server = MockOpenCodeServer(("127.0.0.1", 0), MockHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield server, port
    server.shutdown()
    server.server_close()
    thread.join(timeout=2.0)


# --- Header-only reading tests (E-02, V-02, V-06) ----------------------------------------------


def test_header_only_reading(tmp_path: Path):
    # Create a message file with large payload (> 4096 bytes) containing a sentinel
    sentinel = "SECRET_UNTRUSTED_PAYLOAD_SENTINEL_XYZ123"
    large_payload = f"X-Payload-Sentinel: {sentinel}\n" + (
        "Unimportant padding text line\n" * 200
    )
    payload_bytes = len(large_payload.encode("utf-8"))
    assert (
        payload_bytes > 4096
    ), f"Payload size {payload_bytes} must exceed max_bytes (4096)"

    msg_content = f"""From: proj.sender
To: proj.target
Kind: task
Status: queued
Not-Before: 2026-09-25T12:00:00Z
---
{large_payload}
"""
    msg_path = tmp_path / "test_msg.md"
    msg_path.write_text(msg_content, encoding="utf-8")

    header = read_header_only(msg_path)
    assert header.get("From") == "proj.sender"
    assert header.get("To") == "proj.target"
    assert header.get("Kind") == "task"
    assert header.get("Status") == "queued"
    assert header.get("Not-Before") == "2026-09-25T12:00:00Z"
    assert "X-Payload-Sentinel" not in header
    # Ensure sentinel is not in header dict keys or values
    for k, v in header.items():
        assert sentinel not in k
        assert sentinel not in v


def test_header_only_max_bytes_truncation(tmp_path: Path):
    # A file with no '---' separator that exceeds max_bytes
    words = [
        "Alpha",
        "Bravo",
        "Charlie",
        "Delta",
        "Echo",
        "Foxtrot",
        "Golf",
        "Hotel",
        "India",
        "Juliet",
    ]
    long_headers = "\n".join(
        [f"X-Header-{words[i % len(words)]}: value-{i}" for i in range(500)]
    )
    msg_path = tmp_path / "long_header.md"
    msg_path.write_text(long_headers, encoding="utf-8")

    header = read_header_only(msg_path, max_bytes=200)
    # Should only read headers up to 200 bytes
    assert len(header) > 0
    assert len(header) < 50


# --- URL Policy tests (E-09, V-09) -------------------------------------------------------------


def test_url_policy_permitted_loopback():
    assert url_policy_refusal("http://localhost:8080/path") is None
    assert url_policy_refusal("http://127.0.0.1:9000") is None
    assert url_policy_refusal("http://[::1]:9999/session") is None
    assert url_policy_refusal("https://localhost/doc") is None


def test_url_policy_refused_hosts_and_schemes():
    # Empty
    assert "empty url" in (url_policy_refusal("") or "")

    # Non-http schemes
    assert "file" in (url_policy_refusal("file:///etc/passwd") or "")
    assert "data" in (url_policy_refusal("data:text/plain,hello") or "")
    assert "ftp" in (url_policy_refusal("ftp://localhost/file") or "")

    # Non-loopback external hosts
    assert "not in the permitted loopback set" in (
        url_policy_refusal("http://example.com:8080") or ""
    )
    assert "not in the permitted loopback set" in (
        url_policy_refusal("http://192.168.1.5:8080") or ""
    )

    # Conservative literal-host check: localhost.localdomain and 127.1 resolve to loopback but are refused
    assert "not in the permitted loopback set" in (
        url_policy_refusal("http://localhost.localdomain:8080") or ""
    )
    assert "not in the permitted loopback set" in (
        url_policy_refusal("http://127.1:8080") or ""
    )


def test_url_policy_redirect_to_external_refused(mock_server):
    _, port = mock_server
    opener = build_restricted_opener()
    redirect_url = f"http://127.0.0.1:{port}/redirect_to_external"

    # Opening a URL that redirects to external host must be refused
    req = urllib.request.Request(redirect_url)
    with pytest.raises(ValueError, match="redirect refused by url policy"):
        opener.open(req, timeout=2.0)


# --- Delivery tests (E-03, V-03) ---------------------------------------------------------------


def test_deliver_headless_success(mock_server):
    server, port = mock_server
    target_url = f"http://127.0.0.1:{port}"
    session_id = "test-session-valid-123"

    state = deliver(target_url, mode="headless", session=session_id)
    assert state == "delivered"

    # Verify request payload equals NUDGE constant
    assert len(server.received_requests) == 1
    req = server.received_requests[0]
    assert req["path"] == f"/session/{session_id}/prompt_async"
    assert req["headers"].get("Content-Type") == "application/json"

    body_json = json.loads(req["body"].decode("utf-8"))
    assert body_json == {"parts": [{"type": "text", "text": NUDGE}]}


def test_deliver_tui_mode_unsupported():
    # TUI mode must raise ValueError because observability was not established
    with pytest.raises(ValueError, match="mode 'tui' is not supported"):
        deliver("http://127.0.0.1:8080", mode="tui", session="test-session-123")


def test_deliver_agent_not_running():
    # Find an unused port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        unused_port = s.getsockname()[1]

    state = deliver(
        f"http://127.0.0.1:{unused_port}",
        mode="headless",
        session="test-session-123",
        timeout=1.0,
    )
    assert state == "agent-not-running"


def test_deliver_agent_not_responding_404(mock_server):
    _, port = mock_server
    state = deliver(
        f"http://127.0.0.1:{port}",
        mode="headless",
        session="bogus_session",
        timeout=1.0,
    )
    assert state == "agent-not-responding"


def test_deliver_missing_session():
    state = deliver("http://127.0.0.1:8080", mode="headless", session=None)
    assert state == "agent-not-responding"


# --- Scan and Ack tests (E-04, V-04) ------------------------------------------------------------


def test_scan_once_delivery_and_ack(tmp_path: Path):
    comms_dir = tmp_path / ".aw" / "records" / "comms"
    inbox_dir = comms_dir / "untracked" / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    msg_id = "20260925-1200-01-sender.agent--to--target.agent-task-run"
    msg_file = inbox_dir / f"{msg_id}.md"
    msg_file.write_text(
        """From: sender.agent
To: target.agent
Kind: task
Status: queued
---
Payload body here
""",
        encoding="utf-8",
    )

    now = datetime(2026, 9, 25, 12, 30, 0, tzinfo=timezone.utc)
    deliver_called = 0

    def mock_deliver():
        nonlocal deliver_called
        deliver_called += 1
        return "delivered"

    processed = scan_once(
        comms_dir, "target.agent", now, mock_deliver, broker_id="aw.comms-broker"
    )
    assert processed == [msg_id]
    assert deliver_called == 1

    acks_dir = comms_dir / "untracked" / "acks"
    queued_ack = acks_dir / f"{msg_id}.aw.comms-broker.queued.json"
    delivered_ack = acks_dir / f"{msg_id}.aw.comms-broker.delivered.json"
    assert queued_ack.is_file()
    assert delivered_ack.is_file()

    ack_data = json.loads(delivered_ack.read_text(encoding="utf-8"))
    assert ack_data["re"] == msg_id
    assert ack_data["state"] == "delivered"
    assert ack_data["by"] == "aw.comms-broker"
    assert comms.validate_ack(ack_data) == []
    assert comms.ack_writer_for("delivered") == "broker"


def test_scan_once_already_delivered_not_renudged(tmp_path: Path):
    comms_dir = tmp_path / ".aw" / "records" / "comms"
    inbox_dir = comms_dir / "untracked" / "inbox"
    acks_dir = comms_dir / "untracked" / "acks"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    acks_dir.mkdir(parents=True, exist_ok=True)

    msg_id = "20260925-1200-01-sender.agent--to--target.agent-task-run"
    msg_file = inbox_dir / f"{msg_id}.md"
    msg_file.write_text(
        "From: sender.agent\nTo: target.agent\nKind: task\nStatus: queued\n---\nBody\n"
    )

    # Write existing delivered ack
    delivered_ack = acks_dir / f"{msg_id}.aw.comms-broker.delivered.json"
    delivered_ack.write_text(
        json.dumps(
            {
                "re": msg_id,
                "state": "delivered",
                "by": "aw.comms-broker",
                "at": "2026-09-25T12:00:00Z",
            }
        )
    )

    deliver_called = 0

    def mock_deliver():
        nonlocal deliver_called
        deliver_called += 1
        return "delivered"

    now = datetime(2026, 9, 25, 12, 30, 0, tzinfo=timezone.utc)
    processed = scan_once(comms_dir, "target.agent", now, mock_deliver)
    assert processed == []
    assert deliver_called == 0


def test_scan_once_not_before_future_scheduled(tmp_path: Path):
    comms_dir = tmp_path / ".aw" / "records" / "comms"
    inbox_dir = comms_dir / "untracked" / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    msg_id = "20260925-1200-01-sender.agent--to--target.agent-task-sched"
    msg_file = inbox_dir / f"{msg_id}.md"
    msg_file.write_text(
        """From: sender.agent
To: target.agent
Kind: task
Status: scheduled
Not-Before: 2026-09-25T15:00:00Z
---
Body
""",
        encoding="utf-8",
    )

    now = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
    deliver_called = 0

    def mock_deliver():
        nonlocal deliver_called
        deliver_called += 1
        return "delivered"

    processed = scan_once(
        comms_dir, "target.agent", now, mock_deliver, broker_id="aw.comms-broker"
    )
    assert processed == []
    assert deliver_called == 0

    acks_dir = comms_dir / "untracked" / "acks"
    sched_ack = acks_dir / f"{msg_id}.aw.comms-broker.scheduled.json"
    assert sched_ack.is_file()
    stat1 = sched_ack.stat().st_mtime_ns

    # Second scan: test idempotence (scheduled ack not rewritten)
    time.sleep(0.01)
    processed2 = scan_once(
        comms_dir, "target.agent", now, mock_deliver, broker_id="aw.comms-broker"
    )
    assert processed2 == []
    assert deliver_called == 0
    stat2 = sched_ack.stat().st_mtime_ns
    assert stat1 == stat2, f"st_mtime_ns changed: {stat1} != {stat2}"


def test_scan_once_hostile_to_label_and_broker_id(tmp_path: Path):
    comms_dir = tmp_path / ".aw" / "records" / "comms"
    inbox_dir = comms_dir / "untracked" / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    # Message contains hostile To label in envelope header
    msg_id = "20260925-1200-01-sender.agent--to--target.agent-task-01"
    msg_file = inbox_dir / f"{msg_id}.md"
    msg_file.write_text(
        """From: sender.agent
To: evil-attacker-org.target
Kind: task
Status: queued
---
Body
""",
        encoding="utf-8",
    )

    now = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
    scan_once(
        comms_dir,
        "evil-attacker-org.target",
        now,
        lambda: "delivered",
        broker_id="trusted.broker",
    )

    acks_dir = comms_dir / "untracked" / "acks"
    ack_files = [f.name for f in acks_dir.iterdir()]
    assert len(ack_files) == 2  # queued and delivered
    for name in ack_files:
        assert "evil-attacker-org" not in name
        assert "trusted.broker" in name


def test_scan_once_burst_coalescing(tmp_path: Path):
    comms_dir = tmp_path / ".aw" / "records" / "comms"
    inbox_dir = comms_dir / "untracked" / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    for i in range(3):
        msg_id = f"20260925-1200-0{i}-sender.agent--to--target.agent-task-{i}"
        msg_file = inbox_dir / f"{msg_id}.md"
        msg_file.write_text(
            f"""From: sender.agent
To: target.agent
Kind: task
Status: queued
---
Body {i}
""",
            encoding="utf-8",
        )

    now = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
    deliver_count = 0

    def mock_deliver():
        nonlocal deliver_count
        deliver_count += 1
        return "delivered"

    processed = scan_once(comms_dir, "target.agent", now, mock_deliver)
    assert len(processed) == 3
    assert deliver_count == 1  # Delivered once for the batch


# --- CLI and Main tests (E-05, V-05) ------------------------------------------------------------


def test_main_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["run", "--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "--target-agent" in captured.out
    assert "--target-url" in captured.out
    assert "--mode" in captured.out
    assert "--session" in captured.out


def test_main_refused_broker_id(capsys):
    ret = main(
        [
            "run",
            "--target-agent",
            "target.agent",
            "--target-url",
            "http://127.0.0.1:8080",
            "--mode",
            "headless",
            "--session",
            "session-test-1",
            "--broker-id",
            "../unsafe/broker",
            "--once",
        ]
    )
    assert ret == 2
    captured = capsys.readouterr()
    assert "not filename-safe" in captured.err


def test_main_refused_url(capsys):
    ret = main(
        [
            "run",
            "--target-agent",
            "target.agent",
            "--target-url",
            "http://example.com:8080",
            "--mode",
            "headless",
            "--session",
            "session-test-1",
            "--once",
        ]
    )
    assert ret == 2
    captured = capsys.readouterr()
    assert "refused by policy" in captured.err


def test_main_fresh_clone_missing_untracked(tmp_path: Path):
    # Repo with no untracked/ directory
    repo_root = tmp_path / "repo"
    (repo_root / ".aw" / "system").mkdir(parents=True)
    comms_shared = repo_root / ".aw" / "records" / "comms" / "shared"
    comms_shared.mkdir(parents=True)

    ret = main(
        [
            "run",
            "--target-agent",
            "target.agent",
            "--target-url",
            "http://127.0.0.1:8080",
            "--mode",
            "headless",
            "--session",
            "session-test-1",
            "--repo-root",
            str(repo_root),
            "--once",
        ]
    )
    assert ret == 0
