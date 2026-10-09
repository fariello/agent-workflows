"""Behavioral tests for destination-granular egress policy and filtering broker.

Tests fail-closed policy evaluation, construction validation, configuration loading,
and hermetic broker behaviour including same-port destination partitioning and
rejection of malformed requests.
"""

from __future__ import annotations

import socket
import stat
import tempfile
import threading
from pathlib import Path
from typing import Any

import pytest

from agent_workflows.egress_policy import (
    BrokerDecision,
    EgressBroker,
    EgressPolicy,
    PolicyConfigurationError,
    handle_broker_connection,
    load_egress_policy,
)


def _start_echo_listener(
    host: str = "127.0.0.1",
) -> tuple[socket.socket, int, threading.Event, threading.Thread]:
    """Start a local TCP echo listener on an ephemeral port.

    Keeps the listener open until stop_event is set, echoing back any data.
    """
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind((host, 0))
    port = srv.getsockname()[1]
    srv.listen(16)

    stop_event = threading.Event()

    def serve() -> None:
        srv.settimeout(0.2)
        while not stop_event.is_set():
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            def handle_client(c: socket.socket) -> None:
                try:
                    c.settimeout(2.0)
                    while True:
                        data = c.recv(4096)
                        if not data:
                            break
                        c.sendall(data)
                except OSError:
                    pass
                finally:
                    try:
                        c.close()
                    except OSError:
                        pass

            threading.Thread(target=handle_client, args=(conn,), daemon=True).start()
        try:
            srv.close()
        except OSError:
            pass

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return srv, port, stop_event, thread


def _run_client_through_handler(
    policy: EgressPolicy,
    request_bytes: bytes,
    *,
    payload_to_send: bytes | None = None,
) -> tuple[bytes, bytes, BrokerDecision]:
    """Drive handle_broker_connection over socket.socketpair().

    Returns (response_head_bytes, payload_received_bytes, recorded_decision).
    """
    client_end, broker_end = socket.socketpair()
    decisions: list[BrokerDecision] = []

    def record_decision(d: BrokerDecision) -> None:
        decisions.append(d)

    broker_thread = threading.Thread(
        target=handle_broker_connection,
        args=(broker_end, policy),
        kwargs={"on_decision": record_decision},
        daemon=True,
    )
    broker_thread.start()

    client_end.settimeout(5.0)
    client_end.sendall(request_bytes)

    # Read response head
    resp_buf = bytearray()
    while True:
        try:
            chunk = client_end.recv(1024)
        except (OSError, socket.timeout):
            break
        if not chunk:
            break
        resp_buf.extend(chunk)
        if b"\r\n\r\n" in resp_buf:
            break

    # If it was an allowed 200 tunnel and we have a payload to exchange:
    payload_received = bytearray()
    if b"200 Connection Established" in resp_buf and payload_to_send:
        client_end.sendall(payload_to_send)
        while len(payload_received) < len(payload_to_send):
            try:
                chunk = client_end.recv(1024)
            except (OSError, socket.timeout):
                break
            if not chunk:
                break
            payload_received.extend(chunk)

    try:
        client_end.close()
    except OSError:
        pass

    broker_thread.join(timeout=3.0)
    assert decisions, "Expected at least one decision to be recorded"
    return bytes(resp_buf), bytes(payload_received), decisions[0]


class TestEgressPolicyUnit:
    """Task group 1 unit tests: fail-closed policy semantics and construction."""

    def test_unlisted_destination_denied(self) -> None:
        policy = EgressPolicy([("api.anthropic.com", 443)])
        verdict = policy.decide("github.com", 443)
        assert not verdict.allowed
        assert not bool(verdict)
        assert verdict.destination == "github.com:443"
        assert "github.com:443" in verdict.reason
        assert "not in allow list" in verdict.reason

    def test_allow_listed_destination_allowed(self) -> None:
        policy = EgressPolicy([("api.anthropic.com", 443)])
        verdict = policy.decide("api.anthropic.com", 443)
        assert verdict.allowed
        assert bool(verdict)
        assert verdict.destination == "api.anthropic.com:443"
        assert "api.anthropic.com:443" in verdict.reason
        assert "is allow-listed" in verdict.reason

    def test_empty_policy_denies_everything(self) -> None:
        policy = EgressPolicy()
        verdict = policy.decide("127.0.0.1", 80)
        assert not verdict.allowed
        assert not bool(verdict)
        assert "127.0.0.1:80" in verdict.reason

    def test_same_host_different_port_denied(self) -> None:
        policy = EgressPolicy([("127.0.0.1", 8080)])
        verdict_allowed = policy.decide("127.0.0.1", 8080)
        assert verdict_allowed.allowed

        verdict_denied = policy.decide("127.0.0.1", 8081)
        assert not verdict_denied.allowed
        assert "127.0.0.1:8081" in verdict_denied.reason

    @pytest.mark.parametrize(
        "entry,expected_error",
        [
            (("*", 443), "wildcard host not allowed"),
            (("*.anthropic.com", 443), "wildcard host not allowed"),
            (("", 443), "empty host"),
            (("   ", 443), "empty host"),
            (("example.com", 0), "port out of range"),
            (("example.com", 65536), "port out of range"),
            (("example.com", -1), "port out of range"),
            ((" example.com", 443), "host cannot contain whitespace"),
            (("example.com\n", 443), "host cannot contain whitespace"),
            (("invalid host", 443), "host cannot contain whitespace"),
        ],
    )
    def test_construction_refuses_malformed_entries(
        self, entry: tuple[Any, Any], expected_error: str
    ) -> None:
        with pytest.raises((ValueError, TypeError)) as exc_info:
            EgressPolicy([entry])
        assert expected_error in str(exc_info.value)

    def test_construction_refuses_duplicates(self) -> None:
        with pytest.raises(ValueError) as exc_info:
            EgressPolicy([("api.anthropic.com", 443), ("api.anthropic.com", 443)])
        assert "duplicate destination entry: api.anthropic.com:443" in str(
            exc_info.value
        )

    def test_policy_has_no_allow_all_or_negation_switch(self) -> None:
        # Verify no allow-all parameter or negation flag exists
        policy = EgressPolicy()
        assert not hasattr(policy, "allow_all")
        assert not hasattr(policy, "deny_list")
        assert not hasattr(policy, "negation")
        # Attempting a wildcard to simulate allow-all fails
        with pytest.raises(ValueError):
            EgressPolicy([("*", 443)])


class TestEgressPolicyLoader:
    """Task group 1 loader tests: explicit source configuration, refusal to guess."""

    def test_absent_policy_raises(self) -> None:
        with pytest.raises(PolicyConfigurationError) as exc_info:
            load_egress_policy(None)
        assert "Egress policy configuration is absent" in str(exc_info.value)
        assert "cannot be defaulted or guessed" in str(exc_info.value)

    @pytest.mark.parametrize(
        "invalid_config",
        [
            "",
            "   ",
            "not_a_valid_destination",
            "example.com:not_a_number",
            "example.com:70000",
            "example.com:0",
            "*.example.com:443",
            12345,
            {},
            {"wrong_key": ["127.0.0.1:80"]},
            {"destinations": ["invalid:port:here"]},
        ],
    )
    def test_unparseable_policy_raises(self, invalid_config: Any) -> None:
        with pytest.raises(PolicyConfigurationError):
            load_egress_policy(invalid_config)

    def test_explicit_configuration_formats(self) -> None:
        # String format with commas and newlines
        p1 = load_egress_policy("api.anthropic.com:443, 127.0.0.1:8080")
        assert len(p1.destinations) == 2
        assert p1.decide("api.anthropic.com", 443).allowed
        assert p1.decide("127.0.0.1", 8080).allowed
        assert not p1.decide("github.com", 443).allowed

        # List of strings
        p2 = load_egress_policy(["api.anthropic.com:443", "127.0.0.1:8080"])
        assert len(p2.destinations) == 2

        # Dict format
        p3 = load_egress_policy({"destinations": ["api.anthropic.com:443"]})
        assert len(p3.destinations) == 1
        assert p3.decide("api.anthropic.com", 443).allowed


class TestHermeticBrokerEndToEnd:
    """Task group 2 & 3: hermetic broker test proving same-port partition and input bounds."""

    def test_hermetic_same_port_and_port_partition(self) -> None:
        """PR-701 hermetic test: alias pair on same port P, plus port partition Q."""
        # Start listener 1 on port P
        _srv_p, port_p, stop_p, thread_p = _start_echo_listener()
        # Start listener 2 on port Q
        _srv_q, port_q, stop_q, thread_q = _start_echo_listener()

        try:
            # Policy explicitly lists ONLY 127.0.0.1:P
            policy = EgressPolicy([("127.0.0.1", port_p)])

            # Case 1: 127.0.0.1:P -> MUST BE ALLOWED and reach listener P
            req_allowed = (
                f"CONNECT 127.0.0.1:{port_p} HTTP/1.1\r\n"
                f"Host: 127.0.0.1:{port_p}\r\n\r\n"
            ).encode("ascii")
            resp_head, payload_echo, decision_1 = _run_client_through_handler(
                policy, req_allowed, payload_to_send=b"PING_SAME_PORT\n"
            )
            assert b"200 Connection Established" in resp_head
            assert payload_echo == b"PING_SAME_PORT\n"
            assert decision_1.verdict == "ALLOWED"
            assert decision_1.status_code == 200
            assert decision_1.destination == f"127.0.0.1:{port_p}"
            assert f"127.0.0.1:{port_p}" in decision_1.log_line
            assert "PROXY ALLOWED" in decision_1.log_line

            # Case 2: localhost:P -> SAME PORT P, unlisted host alias -> MUST BE REFUSED
            # Listener P is STILL LIVE! Refusal comes from policy, not a closed socket.
            req_refused_alias = (
                f"CONNECT localhost:{port_p} HTTP/1.1\r\n"
                f"Host: localhost:{port_p}\r\n\r\n"
            ).encode("ascii")
            resp_head_alias, _, decision_2 = _run_client_through_handler(
                policy, req_refused_alias
            )
            assert b"403 Forbidden" in resp_head_alias
            assert f"localhost:{port_p}" in resp_head_alias.decode("utf-8")
            assert decision_2.verdict == "DENIED"
            assert decision_2.status_code == 403
            assert decision_2.destination == f"localhost:{port_p}"
            assert "PROXY DENIED" in decision_2.log_line
            assert f"localhost:{port_p}" in decision_2.log_line

            # Case 3: 127.0.0.1:Q -> PORT PARTITION, unlisted port Q -> MUST BE REFUSED
            # Listener Q is STILL LIVE!
            req_refused_port = (
                f"CONNECT 127.0.0.1:{port_q} HTTP/1.1\r\n"
                f"Host: 127.0.0.1:{port_q}\r\n\r\n"
            ).encode("ascii")
            resp_head_port, _, decision_3 = _run_client_through_handler(
                policy, req_refused_port
            )
            assert b"403 Forbidden" in resp_head_port
            assert f"127.0.0.1:{port_q}" in resp_head_port.decode("utf-8")
            assert decision_3.verdict == "DENIED"
            assert decision_3.status_code == 403
            assert decision_3.destination == f"127.0.0.1:{port_q}"
            assert "PROXY DENIED" in decision_3.log_line
            assert f"127.0.0.1:{port_q}" in decision_3.log_line

        finally:
            stop_p.set()
            stop_q.set()
            thread_p.join(timeout=1.0)
            thread_q.join(timeout=1.0)

    def test_broker_refusal_distinguishable_from_network_fault(self) -> None:
        """E-04 / V-04: refusal produces an explicit HTTP 403 error response."""
        policy = EgressPolicy([("api.anthropic.com", 443)])
        req = b"CONNECT github.com:443 HTTP/1.1\r\n\r\n"
        resp_head, _, decision = _run_client_through_handler(policy, req)

        # Distinguishable 403 Forbidden with plain text body and reason
        assert b"HTTP/1.1 403 Forbidden\r\n" in resp_head
        assert b"Content-Type: text/plain; charset=utf-8\r\n" in resp_head
        assert b"destination github.com:443 is not in allow list\n" in resp_head
        assert decision.status_code == 403
        assert decision.verdict == "DENIED"
        assert decision.destination == "github.com:443"
        assert (
            "PROXY DENIED github.com:443: destination github.com:443 is not in allow list"
            in decision.log_line
        )

    def test_omitted_model_endpoint_refusal_visible(self) -> None:
        """V-02: prove failure is visible when policy omits model endpoint."""
        policy = EgressPolicy([("api.openai.com", 443)])
        # Model client tries to connect to api.anthropic.com:443
        req = b"CONNECT api.anthropic.com:443 HTTP/1.1\r\n\r\n"
        resp_head, _, decision = _run_client_through_handler(policy, req)

        assert b"HTTP/1.1 403 Forbidden" in resp_head
        assert b"destination api.anthropic.com:443 is not in allow list" in resp_head
        assert decision.status_code == 403
        assert decision.verdict == "DENIED"

    def test_refuse_non_connect_method(self) -> None:
        """PR-703: refuse non-CONNECT method with 400 Bad Request and fixed reason."""
        policy = EgressPolicy([("127.0.0.1", 8080)])
        req = b"GET /index.html HTTP/1.1\r\nHost: 127.0.0.1:8080\r\n\r\n"
        resp_head, _, decision = _run_client_through_handler(policy, req)

        assert b"HTTP/1.1 400 Bad Request" in resp_head
        assert b"unsupported method: only CONNECT is permitted" in resp_head
        assert decision.status_code == 400
        assert decision.verdict == "MALFORMED"
        assert "unsupported method" in decision.reason
        assert "GET" not in decision.log_line  # raw input never echoed
        assert "PROXY REFUSED malformed-request:" in decision.log_line

    def test_refuse_over_long_request_head(self) -> None:
        """PR-703: refuse request head exceeding MAX_REQUEST_HEAD_BYTES."""
        policy = EgressPolicy([("127.0.0.1", 8080)])
        req = b"CONNECT " + (b"A" * 5000)
        resp_head, _, decision = _run_client_through_handler(policy, req)

        assert b"HTTP/1.1 400 Bad Request" in resp_head
        assert b"request head exceeded size limit" in resp_head
        assert decision.status_code == 400
        assert decision.verdict == "MALFORMED"
        assert "exceeded size limit" in decision.reason
        assert "AAAA" not in decision.log_line  # raw input never echoed
        assert "PROXY REFUSED malformed-request:" in decision.log_line

    def test_refuse_target_carrying_newline(self) -> None:
        """PR-703: refuse target containing control characters or newlines."""
        policy = EgressPolicy([("127.0.0.1", 8080)])
        req = b"CONNECT evil.com\r\nInjected-Header: evil:443 HTTP/1.1\r\n\r\n"
        resp_head, _, decision = _run_client_through_handler(policy, req)

        assert b"HTTP/1.1 400 Bad Request" in resp_head
        assert decision.status_code == 400
        assert decision.verdict == "MALFORMED"
        assert "Injected-Header" not in decision.log_line  # raw input never echoed
        assert "PROXY REFUSED malformed-request:" in decision.log_line

    def test_upstream_connection_failure(self) -> None:
        """Broker returns 502 Bad Gateway when allow-listed upstream fails to connect."""
        # Find an unused port
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        temp_sock.bind(("127.0.0.1", 0))
        closed_port = temp_sock.getsockname()[1]
        temp_sock.close()

        policy = EgressPolicy([("127.0.0.1", closed_port)])
        req = f"CONNECT 127.0.0.1:{closed_port} HTTP/1.1\r\n\r\n".encode("ascii")
        resp_head, _, decision = _run_client_through_handler(policy, req)

        assert b"HTTP/1.1 502 Bad Gateway" in resp_head
        assert b"upstream connection failed" in resp_head
        assert decision.status_code == 502
        assert decision.verdict == "UPSTREAM_ERROR"


class TestEgressBrokerUnixSocket:
    """AF_UNIX socket broker listener integration test."""

    @pytest.mark.skipif(
        not hasattr(socket, "AF_UNIX"),
        reason="AF_UNIX sockets are not supported on this platform",
    )
    def test_af_unix_broker_lifecycle_and_directory_mode(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp", prefix="eb_") as tmp_dir_str:
            sock_dir = Path(tmp_dir_str) / "sock_dir"
            sock_path = sock_dir / "broker.sock"

            policy = EgressPolicy([("127.0.0.1", 8080)])
            broker = EgressBroker(policy, sock_path)

            with broker:
                # Verify directory mode is 0o700
                dir_mode = broker.socket_dir_mode()
                assert dir_mode == 0o700
                assert stat.S_IMODE(sock_dir.stat().st_mode) == 0o700
                assert sock_path.exists()

                # Connect via AF_UNIX client
                client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client.settimeout(3.0)
                client.connect(str(sock_path))

                # Send CONNECT for unlisted destination
                client.sendall(b"CONNECT github.com:443 HTTP/1.1\r\n\r\n")
                resp = client.recv(4096)
                client.close()

                assert b"HTTP/1.1 403 Forbidden" in resp

            # After broker stops, socket file must be unlinked
            assert not sock_path.exists()
            # Verify decisions were recorded on the broker
            assert len(broker.decisions) == 1
            assert broker.decisions[0].destination == "github.com:443"
            assert broker.decisions[0].status_code == 403
