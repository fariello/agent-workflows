"""Tests for comms broker discovery registry and dynamic target resolution (IPD ex539u)."""

from __future__ import annotations

import http.server
import json
import socket
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agent_workflows import comms
from agent_workflows.comms_broker import (
    REGISTRY_SUBDIR,
    main,
    register_target,
    resolve_target,
    scan_once,
    unregister_target,
    validate_descriptor,
)


# --- Mock OpenCode Server Fixture --------------------------------------------------------------


class MockOpenCodeRegistryServer(http.server.HTTPServer):
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.received_requests: list[dict] = []
        self.healthy: bool = True
        self.directory: str = "/tmp/fake-repo"
        self.worktree: str = "/tmp/fake-repo"
        self.session_valid: bool = True


class MockRegistryHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # Silence logging
        pass

    def _record_request(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        self.server.received_requests.append(
            {
                "path": self.path,
                "headers": dict(self.headers),
                "body": body,
            }
        )

    def do_GET(self):
        self._record_request()
        if self.path == "/global/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = json.dumps({"healthy": self.server.healthy, "version": "1.18.32"})
            self.wfile.write(resp.encode("utf-8"))
        elif self.path == "/path":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = json.dumps(
                {
                    "directory": self.server.directory,
                    "worktree": self.server.worktree,
                }
            )
            self.wfile.write(resp.encode("utf-8"))
        elif self.path == "/redirect_evil":
            self.send_response(302)
            self.send_header("Location", "http://evil.example.com/bad")
            self.end_headers()
        elif self.path == "/server_error":
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Internal Server Error")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        self._record_request()
        if self.path.startswith("/session/") and self.path.endswith("/prompt_async"):
            if not self.server.session_valid or "bogus" in self.path:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'{"name":"NotFoundError"}')
            else:
                self.send_response(204)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


@pytest.fixture
def mock_registry_server():
    server = MockOpenCodeRegistryServer(("127.0.0.1", 0), MockRegistryHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield server, port
    server.shutdown()
    server.server_close()
    thread.join(timeout=2.0)


# --- Task Group 1 / E-01, V-01: Descriptor Validation Tests -----------------------------------


def test_validate_descriptor_valid():
    desc_tui = {
        "agent": "proj.agent",
        "url": "http://127.0.0.1:8080",
        "mode": "tui",
        "session": None,
        "pid": 1234,
        "registered_at": "2026-09-25T12:00:00Z",
    }
    assert validate_descriptor(desc_tui) == []

    desc_headless = {
        "agent": "proj.agent2",
        "url": "http://localhost:9000",
        "mode": "headless",
        "session": "session-abc-123",
        "pid": 5678,
        "registered_at": "2026-09-25T12:00:00Z",
    }
    assert validate_descriptor(desc_headless) == []


def test_validate_descriptor_non_loopback_rejected():
    desc_ext = {
        "agent": "proj.agent",
        "url": "http://example.com:8080",
        "mode": "tui",
    }
    problems = validate_descriptor(desc_ext)
    assert len(problems) > 0
    assert any("not in the permitted loopback set" in p for p in problems)

    desc_ip = {
        "agent": "proj.agent",
        "url": "http://192.168.1.1:8080",
        "mode": "tui",
    }
    problems_ip = validate_descriptor(desc_ip)
    assert len(problems_ip) > 0
    assert any("not in the permitted loopback set" in p for p in problems_ip)


def test_validate_descriptor_headless_without_session_rejected():
    desc_no_session = {
        "agent": "proj.agent",
        "url": "http://127.0.0.1:8080",
        "mode": "headless",
        "session": None,
    }
    problems = validate_descriptor(desc_no_session)
    assert len(problems) > 0
    assert any("session is required when mode is 'headless'" in p for p in problems)

    desc_empty_session = {
        "agent": "proj.agent",
        "url": "http://127.0.0.1:8080",
        "mode": "headless",
        "session": "   ",
    }
    problems_empty = validate_descriptor(desc_empty_session)
    assert any(
        "session is required when mode is 'headless'" in p for p in problems_empty
    )


def test_validate_descriptor_unsafe_name_rejected():
    for unsafe in ["../escape", "bad/name", "bad\\name", "C:bad", ""]:
        desc = {
            "agent": unsafe,
            "url": "http://127.0.0.1:8080",
            "mode": "tui",
        }
        problems = validate_descriptor(desc)
        assert len(problems) > 0


def test_validate_descriptor_non_dict_and_invalid_fields():
    assert validate_descriptor("not-a-dict") == ["descriptor must be a JSON object"]

    desc_invalid_mode = {
        "agent": "proj.agent",
        "url": "http://127.0.0.1:8080",
        "mode": "invalid_mode",
    }
    problems = validate_descriptor(desc_invalid_mode)
    assert any("not in ('tui', 'headless')" in p for p in problems)

    desc_invalid_pid = {
        "agent": "proj.agent",
        "url": "http://127.0.0.1:8080",
        "mode": "tui",
        "pid": "not-an-int",
    }
    problems_pid = validate_descriptor(desc_invalid_pid)
    assert any("pid must be an integer" in p for p in problems_pid)

    desc_invalid_reg_at = {
        "agent": "proj.agent",
        "url": "http://127.0.0.1:8080",
        "mode": "tui",
        "registered_at": "not-a-date",
    }
    problems_date = validate_descriptor(desc_invalid_reg_at)
    assert any("not a valid ISO-8601 datetime" in p for p in problems_date)


# --- E-02, V-02: Register / Unregister Subcommands --------------------------------------------


def test_register_unregister_roundtrip(tmp_path: Path):
    repo_root = tmp_path / "repo"
    (repo_root / ".aw" / "system").mkdir(parents=True)
    comms_dir = repo_root / ".aw" / "records" / "comms"

    # 1. Register target
    desc_path = register_target(
        comms_dir,
        agent="proj.target",
        url="http://127.0.0.1:8080",
        mode="headless",
        session="sess-123",
        pid=9999,
    )
    assert desc_path.is_file()
    assert desc_path.name == "proj.target.json"
    assert desc_path.parent == comms_dir / "untracked" / REGISTRY_SUBDIR

    loaded = json.loads(desc_path.read_text(encoding="utf-8"))
    assert loaded["agent"] == "proj.target"
    assert loaded["url"] == "http://127.0.0.1:8080"
    assert loaded["mode"] == "headless"
    assert loaded["session"] == "sess-123"
    assert loaded["pid"] == 9999
    assert comms.parse_not_before(loaded["registered_at"]) is not None

    # 2. Unregister target
    assert unregister_target(comms_dir, "proj.target") is True
    assert not desc_path.exists()
    assert unregister_target(comms_dir, "proj.target") is False


def test_register_unregister_cli(tmp_path: Path, capsys):
    repo_root = tmp_path / "repo"
    (repo_root / ".aw" / "system").mkdir(parents=True)
    comms_dir = repo_root / ".aw" / "records" / "comms"
    registry_dir = comms_dir / "untracked" / REGISTRY_SUBDIR

    # Valid registration via CLI
    ret = main(
        [
            "register",
            "--agent",
            "cli.target",
            "--url",
            "http://127.0.0.1:9090",
            "--mode",
            "headless",
            "--session",
            "cli-session",
            "--repo-root",
            str(repo_root),
        ]
    )
    assert ret == 0
    target_json = registry_dir / "cli.target.json"
    assert target_json.is_file()

    # Unregister via CLI
    ret_unreg = main(
        [
            "unregister",
            "--agent",
            "cli.target",
            "--repo-root",
            str(repo_root),
        ]
    )
    assert ret_unreg == 0
    assert not target_json.exists()

    # Invalid registration exits 2 and writes nothing
    ret_invalid = main(
        [
            "register",
            "--agent",
            "bad.target",
            "--url",
            "http://external.example.com:8080",
            "--mode",
            "headless",
            "--session",
            "cli-session",
            "--repo-root",
            str(repo_root),
        ]
    )
    assert ret_invalid == 2
    captured = capsys.readouterr()
    assert "not in the permitted loopback set" in captured.err
    assert not (registry_dir / "bad.target.json").exists()


# --- E-03, E-04, V-03, V-04: Resolve Target Tests ----------------------------------------------


def test_resolve_target_success(mock_registry_server, tmp_path: Path):
    server, port = mock_registry_server
    repo_root = tmp_path / "my_repo"
    repo_root.mkdir(parents=True)
    comms_dir = repo_root / ".aw" / "records" / "comms"

    server.directory = str(repo_root.resolve())
    server.worktree = str(repo_root.resolve())
    server.healthy = True

    register_target(
        comms_dir,
        agent="target.agent",
        url=f"http://127.0.0.1:{port}",
        mode="headless",
        session="session-456",
    )

    resolved = resolve_target(comms_dir, "target.agent", repo_root)
    assert isinstance(resolved, dict)
    assert resolved["agent"] == "target.agent"
    assert resolved["url"] == f"http://127.0.0.1:{port}"
    assert resolved["mode"] == "headless"
    assert resolved["session"] == "session-456"


def test_resolve_target_directory_mismatch_and_no_nudge(
    mock_registry_server, tmp_path: Path
):
    server, port = mock_registry_server
    repo_root = tmp_path / "my_repo"
    other_repo = tmp_path / "other_repo"
    repo_root.mkdir(parents=True)
    other_repo.mkdir(parents=True)
    comms_dir = repo_root / ".aw" / "records" / "comms"

    server.directory = str(other_repo.resolve())
    server.worktree = str(other_repo.resolve())
    server.healthy = True

    register_target(
        comms_dir,
        agent="target.agent",
        url=f"http://127.0.0.1:{port}",
        mode="headless",
        session="session-456",
    )

    resolved = resolve_target(comms_dir, "target.agent", repo_root)
    assert resolved == "agent-not-responding"

    # Confirm stale descriptor is left in place
    desc_path = comms_dir / "untracked" / REGISTRY_SUBDIR / "target.agent.json"
    assert desc_path.is_file()


def test_resolve_target_worktree_sibling_refused(mock_registry_server, tmp_path: Path):
    """V-04 / E-04: Test that a sibling worktree sharing worktree but different directory is refused."""
    server, port = mock_registry_server
    lane1 = tmp_path / "worktrees" / "lane1"
    lane2 = tmp_path / "worktrees" / "lane2"
    shared_repo = tmp_path / "main_repo"
    lane1.mkdir(parents=True)
    lane2.mkdir(parents=True)
    shared_repo.mkdir(parents=True)

    comms_dir = lane1 / ".aw" / "records" / "comms"

    # Server is serving lane2, but both lane1 and lane2 share the same git common dir / worktree
    server.directory = str(lane2.resolve())
    server.worktree = str(shared_repo.resolve())
    server.healthy = True

    register_target(
        comms_dir,
        agent="target.agent",
        url=f"http://127.0.0.1:{port}",
        mode="headless",
        session="session-456",
    )

    # Resolving from lane1 where repo_root is lane1
    resolved = resolve_target(comms_dir, "target.agent", lane1)
    # Must be refused because directory is authoritative and does not match lane1!
    assert resolved == "agent-not-responding"


def test_resolve_target_missing_descriptor(tmp_path: Path):
    repo_root = tmp_path / "my_repo"
    comms_dir = repo_root / ".aw" / "records" / "comms"
    resolved = resolve_target(comms_dir, "nonexistent.agent", repo_root)
    assert resolved == "agent-not-running"


def test_resolve_target_unhealthy(mock_registry_server, tmp_path: Path):
    server, port = mock_registry_server
    repo_root = tmp_path / "my_repo"
    repo_root.mkdir(parents=True)
    comms_dir = repo_root / ".aw" / "records" / "comms"

    server.directory = str(repo_root.resolve())
    server.worktree = str(repo_root.resolve())
    server.healthy = False

    register_target(
        comms_dir,
        agent="target.agent",
        url=f"http://127.0.0.1:{port}",
        mode="headless",
        session="session-456",
    )

    resolved = resolve_target(comms_dir, "target.agent", repo_root)
    assert resolved == "agent-not-responding"


def test_resolve_target_server_error(mock_registry_server, tmp_path: Path):
    server, port = mock_registry_server
    repo_root = tmp_path / "my_repo"
    repo_root.mkdir(parents=True)
    comms_dir = repo_root / ".aw" / "records" / "comms"

    server.directory = str(repo_root.resolve())

    # Write descriptor pointing to /server_error path or mock server responding 500
    reg_path = comms_dir / "untracked" / REGISTRY_SUBDIR / "target.agent.json"
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    reg_path.write_text(
        json.dumps(
            {
                "agent": "target.agent",
                "url": f"http://127.0.0.1:{port}/server_error",
                "mode": "headless",
                "session": "s1",
            }
        )
    )

    resolved = resolve_target(comms_dir, "target.agent", repo_root)
    assert resolved == "agent-not-responding"


def test_resolve_target_connection_refused(tmp_path: Path):
    repo_root = tmp_path / "my_repo"
    repo_root.mkdir(parents=True)
    comms_dir = repo_root / ".aw" / "records" / "comms"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        unused_port = s.getsockname()[1]

    register_target(
        comms_dir,
        agent="target.agent",
        url=f"http://127.0.0.1:{unused_port}",
        mode="headless",
        session="s1",
    )

    # 10s, not 2s: on Windows a connect to a closed loopback port is retried by the TCP stack for
    # about 2s before WSAECONNREFUSED is reported, so a 2s timeout raced it and saw a TIMEOUT
    # (`agent-not-responding`) on every windows-latest job. A refusal still returns in milliseconds
    # on POSIX, so the larger ceiling costs nothing there.
    resolved = resolve_target(comms_dir, "target.agent", repo_root, timeout=10.0)
    assert resolved == "agent-not-running"


def test_connection_refused_classifier_covers_windows_errno():
    from agent_workflows.comms_broker import _is_connection_refused

    class _WinErr(OSError):
        pass

    win = _WinErr()
    win.winerror = 10061
    assert _is_connection_refused(win)
    assert _is_connection_refused(ConnectionRefusedError())
    assert not _is_connection_refused(TimeoutError())


# --- E-05, E-06, V-05, V-06: Wiring, Explicit URL and Idempotence ------------------------------


def test_scan_once_explicit_url_bypasses_registry(tmp_path: Path):
    repo_root = tmp_path / "my_repo"
    comms_dir = repo_root / ".aw" / "records" / "comms"
    inbox_dir = comms_dir / "untracked" / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    # Register an invalid / broken target descriptor
    register_target(
        comms_dir,
        agent="target.agent",
        url="http://127.0.0.1:1",  # Unreachable port
        mode="headless",
        session="s1",
    )

    msg_id = "20260925-1200-01-sender--to--target.agent-task-01"
    (inbox_dir / f"{msg_id}.md").write_text(
        "From: sender\nTo: target.agent\nKind: task\nStatus: queued\n---\nBody\n"
    )

    deliver_called = 0

    def explicit_deliver_fn():
        nonlocal deliver_called
        deliver_called += 1
        return "delivered"

    now = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
    # When deliver_fn is explicitly supplied (corresponding to explicit --target-url),
    # registry is bypassed
    processed = scan_once(
        comms_dir,
        "target.agent",
        now,
        deliver_fn=explicit_deliver_fn,
        broker_id="aw.comms-broker",
        repo_root=repo_root,
    )
    assert processed == [msg_id]
    assert deliver_called == 1


def test_scan_once_idempotence_against_down_target(tmp_path: Path):
    repo_root = tmp_path / "my_repo"
    comms_dir = repo_root / ".aw" / "records" / "comms"
    inbox_dir = comms_dir / "untracked" / "inbox"
    acks_dir = comms_dir / "untracked" / "acks"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    # No descriptor registered -> target resolution returns 'agent-not-running'
    msg_id = "20260925-1200-01-sender.agent--to--target.agent-task-down"
    (inbox_dir / f"{msg_id}.md").write_text(
        "From: sender.agent\nTo: target.agent\nKind: task\nStatus: queued\n---\nBody\n"
    )

    now = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
    processed1 = scan_once(
        comms_dir,
        "target.agent",
        now,
        deliver_fn=None,
        broker_id="aw.comms-broker",
        repo_root=repo_root,
    )
    assert processed1 == [msg_id]

    # Verify exactly one ack file in acks/
    ack_files = sorted([f.name for f in acks_dir.iterdir()])
    expected_ack_name = f"{msg_id}.aw.comms-broker.agent-not-running.json"
    assert ack_files == [expected_ack_name]
    assert expected_ack_name.startswith(msg_id)

    ack_file = acks_dir / expected_ack_name
    mtime1 = ack_file.stat().st_mtime_ns

    # Second scan: test idempotence across repeated scans
    time.sleep(0.01)
    processed2 = scan_once(
        comms_dir,
        "target.agent",
        now,
        deliver_fn=None,
        broker_id="aw.comms-broker",
        repo_root=repo_root,
    )
    assert processed2 == [msg_id]

    ack_files2 = sorted([f.name for f in acks_dir.iterdir()])
    assert ack_files2 == [expected_ack_name]
    mtime2 = ack_file.stat().st_mtime_ns

    print(f"DEBUG idempotence st_mtime_ns scan1={mtime1} scan2={mtime2}")
    assert mtime1 == mtime2, f"st_mtime_ns modified: {mtime1} != {mtime2}"


# --- E-08, V-08: Four Trust-Boundary and Idempotence Cases -------------------------------------


def test_trust_boundary_case_a_non_loopback_zero_requests(
    mock_registry_server, tmp_path: Path
):
    """Case (a): Non-loopback URL in descriptor is refused with ZERO requests to fixture."""
    server, _ = mock_registry_server
    repo_root = tmp_path / "repo"
    comms_dir = repo_root / ".aw" / "records" / "comms"
    reg_dir = comms_dir / "untracked" / REGISTRY_SUBDIR
    reg_dir.mkdir(parents=True, exist_ok=True)

    # Drop a descriptor with non-loopback URL
    (reg_dir / "evil.agent.json").write_text(
        json.dumps(
            {
                "agent": "evil.agent",
                "url": "http://evil.example.com:8080",
                "mode": "headless",
                "session": "s1",
            }
        )
    )

    initial_requests = len(server.received_requests)
    resolved = resolve_target(comms_dir, "evil.agent", repo_root)
    assert resolved == "agent-not-running"
    print(
        f"DEBUG trust_boundary_a fixture requests count={len(server.received_requests)}"
    )
    assert len(server.received_requests) == initial_requests == 0


def test_trust_boundary_case_b_redirect_to_external_refused(
    mock_registry_server, tmp_path: Path
):
    """Case (b): Redirect to external host is refused by RefusingRedirectHandler."""
    server, port = mock_registry_server
    repo_root = tmp_path / "repo"
    comms_dir = repo_root / ".aw" / "records" / "comms"
    reg_dir = comms_dir / "untracked" / REGISTRY_SUBDIR
    reg_dir.mkdir(parents=True, exist_ok=True)

    # Point descriptor to loopback redirect_evil endpoint
    (reg_dir / "redirect.agent.json").write_text(
        json.dumps(
            {
                "agent": "redirect.agent",
                "url": f"http://127.0.0.1:{port}/redirect_evil",
                "mode": "headless",
                "session": "s1",
            }
        )
    )

    resolved = resolve_target(comms_dir, "redirect.agent", repo_root)
    # Refused because redirect target http://evil.example.com/bad is non-loopback
    assert resolved == "agent-not-responding"
    # Requests on loopback server: 1 request to /redirect_evil, and 0 requests to external host
    print(
        f"DEBUG trust_boundary_b loopback requests={len(server.received_requests)} paths={[r['path'] for r in server.received_requests]}"
    )


def test_trust_boundary_case_c_descriptor_replaced_on_disk_revalidated(tmp_path: Path):
    """Case (c): A descriptor replaced on disk after registration is re-validated on read."""
    repo_root = tmp_path / "repo"
    comms_dir = repo_root / ".aw" / "records" / "comms"

    # Register valid descriptor
    desc_path = register_target(
        comms_dir,
        agent="target.agent",
        url="http://127.0.0.1:8080",
        mode="headless",
        session="s1",
    )
    content_before = desc_path.read_text(encoding="utf-8")
    assert "127.0.0.1" in content_before

    # Attacker or rogue process replaces descriptor on disk with malicious URL
    desc_path.write_text(
        json.dumps(
            {
                "agent": "target.agent",
                "url": "http://evil.example.com:9999",
                "mode": "headless",
                "session": "s1",
            }
        ),
        encoding="utf-8",
    )
    content_after = desc_path.read_text(encoding="utf-8")
    assert "evil.example.com" in content_after

    print(f"DEBUG descriptor before:\n{content_before}")
    print(f"DEBUG descriptor after:\n{content_after}")

    # resolve_target must re-validate and refuse
    resolved = resolve_target(comms_dir, "target.agent", repo_root)
    assert resolved == "agent-not-running"


def test_trust_boundary_case_d_two_consecutive_scans_mtime_unchanged(tmp_path: Path):
    """Case (d): Two consecutive scans against down target leave failure ack st_mtime_ns unchanged."""
    repo_root = tmp_path / "repo"
    comms_dir = repo_root / ".aw" / "records" / "comms"
    inbox_dir = comms_dir / "untracked" / "inbox"
    acks_dir = comms_dir / "untracked" / "acks"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    msg_id = "20260925-1200-01-sender--to--target.agent-task-down-d"
    (inbox_dir / f"{msg_id}.md").write_text(
        "From: sender\nTo: target.agent\nKind: task\nStatus: queued\n---\nBody\n"
    )

    now = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
    scan_once(
        comms_dir,
        "target.agent",
        now,
        deliver_fn=None,
        broker_id="aw.comms-broker",
        repo_root=repo_root,
    )

    ack_file = acks_dir / f"{msg_id}.aw.comms-broker.agent-not-running.json"
    assert ack_file.is_file()
    mtime1 = ack_file.stat().st_mtime_ns

    time.sleep(0.01)
    scan_once(
        comms_dir,
        "target.agent",
        now,
        deliver_fn=None,
        broker_id="aw.comms-broker",
        repo_root=repo_root,
    )

    mtime2 = ack_file.stat().st_mtime_ns
    print(f"DEBUG trust_boundary_d st_mtime_ns: scan1={mtime1} scan2={mtime2}")
    assert mtime1 == mtime2
