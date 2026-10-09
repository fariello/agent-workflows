"""Destination-granular egress policy and parent-owned filtering broker.

Fail-closed outbound egress policy and filtering broker for confined workers.

Network denial by an OS sandbox alone cannot separate a git remote from the
model API on one port, so none is applied by the sandbox profile directly.
This module provides the explicit destination-granular egress policy and the
parent-owned filtering broker that enforces it.

POLICY POSTURE: FAIL-CLOSED AND REFUSE TO GUESS
An absent policy is an ERROR and never an empty-allow-everything or a guessed default.
The allow list must be explicitly configured by the caller; this module does
NOT discover or guess destinations by inspecting host environment, network
state, or ambient configuration. Deny is the default for every destination not
explicitly named in the allow list.

BROKER CONFINEMENT: PARENT-OWNED
The broker listens on an AF_UNIX socket held in the parent process, outside the
worker's network namespace. Because the broker and its policy live in the parent,
the confined process has no mechanism or capability to alter the policy or reconfigure
the allow list.
"""

from __future__ import annotations

import logging
import os
import re
import socket
import stat
import threading
import time
import types
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Self

logger = logging.getLogger(__name__)

MAX_REQUEST_HEAD_BYTES = 4096
CONNECT_TIMEOUT_SECONDS = 5.0
RELAY_TIMEOUT_SECONDS = 30.0

_HOSTNAME_RE = re.compile(r"^[a-zA-Z0-9.-]+$")
_IPV6_RE = re.compile(r"^\[[a-fA-F0-9:.]+\]$")


class PolicyConfigurationError(ValueError):
    """Raised when egress policy configuration is absent or unparseable."""


@dataclass(frozen=True)
class EgressDestination:
    """An explicit allow-listed egress destination: host plus port."""

    host: str
    port: int

    def __post_init__(self) -> None:
        if not isinstance(self.host, str):
            raise TypeError(f"host must be str, got {type(self.host).__name__}")
        if not self.host or not self.host.strip():
            raise ValueError("empty host")
        if self.host != self.host.strip() or any(
            ord(c) <= 32 or ord(c) >= 127 for c in self.host
        ):
            raise ValueError("host cannot contain whitespace or control characters")
        if "*" in self.host:
            raise ValueError(f"wildcard host not allowed: {self.host!r}")
        if not (_HOSTNAME_RE.match(self.host) or _IPV6_RE.match(self.host)):
            raise ValueError(f"invalid characters in host: {self.host!r}")

        if isinstance(self.port, bool) or not isinstance(self.port, int):
            raise TypeError(f"port must be int, got {type(self.port).__name__}")
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"port out of range (1-65535): {self.port}")


@dataclass(frozen=True)
class PolicyVerdict:
    """Explicit verdict returned by EgressPolicy.decide."""

    allowed: bool
    reason: str
    destination: str
    host: str
    port: int

    def __bool__(self) -> bool:
        return self.allowed


@dataclass(frozen=True)
class EgressPolicy:
    """Frozen egress allow list policy with deny-by-default semantics.

    Validation is performed at construction. Malformed, ambiguous, wildcard,
    or duplicate entries are refused. There is no allow-all switch and no negation.
    """

    destinations: tuple[EgressDestination, ...] = field(default_factory=tuple)

    def __init__(
        self,
        destinations: Iterable[EgressDestination | tuple[str, int]] = (),
    ) -> None:
        seen: set[tuple[str, int]] = set()
        validated: list[EgressDestination] = []
        for item in destinations:
            if isinstance(item, EgressDestination):
                dest = item
            elif isinstance(item, (tuple, list)) and len(item) == 2:
                dest = EgressDestination(item[0], item[1])
            else:
                raise ValueError(f"invalid destination entry: {item!r}")
            key = (dest.host, dest.port)
            if key in seen:
                raise ValueError(
                    f"duplicate destination entry: {dest.host}:{dest.port}"
                )
            seen.add(key)
            validated.append(dest)
        object.__setattr__(self, "destinations", tuple(validated))

    def decide(self, host: str, port: int) -> PolicyVerdict:
        """Consult allow list for destination; deny is default."""
        dest_str = f"{host}:{port}"
        for dest in self.destinations:
            if dest.host == host and dest.port == port:
                return PolicyVerdict(
                    allowed=True,
                    reason=f"destination {dest_str} is allow-listed",
                    destination=dest_str,
                    host=host,
                    port=port,
                )
        return PolicyVerdict(
            allowed=False,
            reason=f"destination {dest_str} is not in allow list",
            destination=dest_str,
            host=host,
            port=port,
        )


def _parse_destination_token(token: str) -> tuple[str, int]:
    """Parse a single 'host:port' string."""
    token = token.strip()
    if not token:
        raise PolicyConfigurationError("empty destination token")
    if token.startswith("["):
        if "]:" not in token:
            raise PolicyConfigurationError(
                f"malformed IPv6 destination token: {token!r}"
            )
        host, port_str = token.split("]:", 1)
        host = f"{host}]"
    else:
        if ":" not in token:
            raise PolicyConfigurationError(f"destination token missing port: {token!r}")
        host, port_str = token.rsplit(":", 1)
    if not port_str.isdigit():
        raise PolicyConfigurationError(
            f"destination port must be an integer: {token!r}"
        )
    port = int(port_str)
    return host, port


def load_egress_policy(config: Any) -> EgressPolicy:
    """Parse and construct an EgressPolicy from explicit configuration.

    Refuses absent or unparseable configuration. Never guesses or defaults
    to any external endpoint.
    """
    if config is None:
        raise PolicyConfigurationError(
            "Egress policy configuration is absent: explicit policy configuration is required and cannot be defaulted or guessed"
        )

    raw_entries: list[Any] = []
    if isinstance(config, str):
        cleaned = config.strip()
        if not cleaned:
            raise PolicyConfigurationError(
                "Egress policy configuration is empty or whitespace"
            )
        # Split by comma or newline
        tokens = [t.strip() for t in re.split(r"[,\n]+", cleaned) if t.strip()]
        if not tokens:
            raise PolicyConfigurationError(
                "Egress policy configuration contains no entries"
            )
        for token in tokens:
            host, port = _parse_destination_token(token)
            raw_entries.append((host, port))
    elif isinstance(config, dict):
        if "destinations" in config:
            target_list = config["destinations"]
        elif "allow_list" in config:
            target_list = config["allow_list"]
        else:
            raise PolicyConfigurationError(
                "Egress policy dict configuration missing 'destinations' or 'allow_list' key"
            )
        if not isinstance(target_list, Sequence):
            raise PolicyConfigurationError(
                f"Egress policy destinations must be a sequence, got {type(target_list).__name__}"
            )
        for item in target_list:
            if isinstance(item, str):
                raw_entries.append(_parse_destination_token(item))
            elif (
                isinstance(item, (tuple, list))
                and len(item) == 2
                or isinstance(item, EgressDestination)
            ):
                raw_entries.append(item)
            else:
                raise PolicyConfigurationError(
                    f"unsupported destination entry in list: {item!r}"
                )
    elif isinstance(config, (list, tuple)):
        for item in config:
            if isinstance(item, str):
                raw_entries.append(_parse_destination_token(item))
            elif (
                isinstance(item, (tuple, list))
                and len(item) == 2
                or isinstance(item, EgressDestination)
            ):
                raw_entries.append(item)
            else:
                raise PolicyConfigurationError(
                    f"unsupported destination entry in sequence: {item!r}"
                )
    else:
        raise PolicyConfigurationError(
            f"unsupported egress policy configuration type: {type(config).__name__}"
        )

    try:
        return EgressPolicy(raw_entries)
    except (ValueError, TypeError) as exc:
        raise PolicyConfigurationError(str(exc)) from exc


@dataclass(frozen=True)
class BrokerDecision:
    """Auditable record of a broker decision for a client request."""

    destination: str
    verdict: str  # "ALLOWED", "DENIED", "MALFORMED", "UPSTREAM_ERROR"
    status_code: int
    reason: str
    log_line: str
    client_address: str = ""


def _send_broker_response(
    sock: socket.socket,
    status_code: int,
    status_text: str,
    body_text: str | None = None,
) -> None:
    """Send an HTTP response back to the client."""
    lines = [f"HTTP/1.1 {status_code} {status_text}"]
    if body_text is not None:
        body_bytes = (body_text + "\n").encode("utf-8")
        lines.append("Content-Type: text/plain; charset=utf-8")
        lines.append(f"Content-Length: {len(body_bytes)}")
        lines.append("Connection: close")
        header = "\r\n".join(lines) + "\r\n\r\n"
        sock.sendall(header.encode("ascii") + body_bytes)
    else:
        lines.append("\r\n")
        sock.sendall(("\r\n".join(lines)).encode("ascii"))


def _read_request_head(
    client_sock: socket.socket,
) -> tuple[bytes | None, str | None]:
    """Read request head bounded at MAX_REQUEST_HEAD_BYTES."""
    client_sock.settimeout(CONNECT_TIMEOUT_SECONDS)
    buf = bytearray()
    while True:
        try:
            chunk = client_sock.recv(1024)
        except (OSError, socket.timeout):
            return None, "connection error or timeout reading request"
        if not chunk:
            if not buf:
                return None, "empty request"
            break
        buf.extend(chunk)
        if len(buf) > MAX_REQUEST_HEAD_BYTES:
            return None, "request head exceeded size limit"
        if b"\r\n\r\n" in buf:
            pos = buf.index(b"\r\n\r\n")
            return bytes(buf[:pos]), None
        if b"\n\n" in buf:
            pos = buf.index(b"\n\n")
            return bytes(buf[:pos]), None

    return None, "request head missing header delimiter"


def _relay_sockets(
    sock1: socket.socket,
    sock2: socket.socket,
    timeout: float = RELAY_TIMEOUT_SECONDS,
) -> None:
    """Relay bytes bidirectionally between two sockets until EOF or timeout."""
    stop_event = threading.Event()

    def pump(src: socket.socket, dst: socket.socket) -> None:
        src.settimeout(1.0)
        dst.settimeout(timeout)
        last_io = time.monotonic()
        try:
            while not stop_event.is_set():
                try:
                    data = src.recv(65536)
                except socket.timeout:
                    if time.monotonic() - last_io > timeout:
                        break
                    continue
                if not data:
                    break
                last_io = time.monotonic()
                dst.sendall(data)
        except OSError:
            pass
        finally:
            stop_event.set()
            try:
                dst.shutdown(socket.SHUT_WR)
            except OSError:
                pass

    t1 = threading.Thread(
        target=pump, args=(sock1, sock2), name="relay-1-to-2", daemon=True
    )
    t2 = threading.Thread(
        target=pump, args=(sock2, sock1), name="relay-2-to-1", daemon=True
    )
    t1.start()
    t2.start()
    t1.join(timeout=timeout + 2.0)
    t2.join(timeout=timeout + 2.0)


def handle_broker_connection(
    client_sock: socket.socket,
    policy: EgressPolicy,
    *,
    connect_timeout: float = CONNECT_TIMEOUT_SECONDS,
    relay_timeout: float = RELAY_TIMEOUT_SECONDS,
    logger: logging.Logger | None = None,
    on_decision: Callable[[BrokerDecision], None] | None = None,
) -> BrokerDecision:
    """Handle a single client CONNECT stream connection (transport-neutral seam).

    Validates request head size, rejects non-CONNECT methods, validates authority
    syntax without echoing raw bytes on error, consults policy, and either
    tunnels or refuses with an explicit 403 Forbidden.
    """
    log = logger or logging.getLogger(__name__)

    try:
        head_bytes, head_err = _read_request_head(client_sock)
        if head_err is not None:
            log_line = f"PROXY REFUSED malformed-request: {head_err}"
            log.warning(log_line)
            _send_broker_response(client_sock, 400, "Bad Request", head_err)
            decision = BrokerDecision(
                destination="unknown",
                verdict="MALFORMED",
                status_code=400,
                reason=head_err,
                log_line=log_line,
            )
            if on_decision:
                on_decision(decision)
            return decision

        assert head_bytes is not None
        try:
            head_str = head_bytes.decode("ascii")
        except UnicodeDecodeError:
            head_err = "request head contained non-ASCII byte encoding"
            log_line = f"PROXY REFUSED malformed-request: {head_err}"
            log.warning(log_line)
            _send_broker_response(client_sock, 400, "Bad Request", head_err)
            decision = BrokerDecision(
                destination="unknown",
                verdict="MALFORMED",
                status_code=400,
                reason=head_err,
                log_line=log_line,
            )
            if on_decision:
                on_decision(decision)
            return decision

        lines = head_str.splitlines()
        if not lines:
            head_err = "empty request line"
            log_line = f"PROXY REFUSED malformed-request: {head_err}"
            log.warning(log_line)
            _send_broker_response(client_sock, 400, "Bad Request", head_err)
            decision = BrokerDecision(
                destination="unknown",
                verdict="MALFORMED",
                status_code=400,
                reason=head_err,
                log_line=log_line,
            )
            if on_decision:
                on_decision(decision)
            return decision

        request_line = lines[0]
        parts = request_line.split(" ")
        if len(parts) != 3:
            head_err = "malformed request line"
            log_line = f"PROXY REFUSED malformed-request: {head_err}"
            log.warning(log_line)
            _send_broker_response(client_sock, 400, "Bad Request", head_err)
            decision = BrokerDecision(
                destination="unknown",
                verdict="MALFORMED",
                status_code=400,
                reason=head_err,
                log_line=log_line,
            )
            if on_decision:
                on_decision(decision)
            return decision

        method, target, version = parts
        if method != "CONNECT":
            head_err = "unsupported method: only CONNECT is permitted"
            log_line = f"PROXY REFUSED malformed-request: {head_err}"
            log.warning(log_line)
            _send_broker_response(client_sock, 400, "Bad Request", head_err)
            decision = BrokerDecision(
                destination="unknown",
                verdict="MALFORMED",
                status_code=400,
                reason=head_err,
                log_line=log_line,
            )
            if on_decision:
                on_decision(decision)
            return decision

        if version not in ("HTTP/1.0", "HTTP/1.1"):
            head_err = "unsupported HTTP version"
            log_line = f"PROXY REFUSED malformed-request: {head_err}"
            log.warning(log_line)
            _send_broker_response(client_sock, 400, "Bad Request", head_err)
            decision = BrokerDecision(
                destination="unknown",
                verdict="MALFORMED",
                status_code=400,
                reason=head_err,
                log_line=log_line,
            )
            if on_decision:
                on_decision(decision)
            return decision

        # Authority validation: refuse control chars, newlines, whitespace, wildcards
        if any(ord(c) <= 32 or ord(c) >= 127 for c in target):
            head_err = (
                "invalid destination syntax: control character or whitespace in target"
            )
            log_line = f"PROXY REFUSED malformed-request: {head_err}"
            log.warning(log_line)
            _send_broker_response(client_sock, 400, "Bad Request", head_err)
            decision = BrokerDecision(
                destination="unknown",
                verdict="MALFORMED",
                status_code=400,
                reason=head_err,
                log_line=log_line,
            )
            if on_decision:
                on_decision(decision)
            return decision

        if "*" in target:
            head_err = "invalid destination syntax: wildcard not permitted"
            log_line = f"PROXY REFUSED malformed-request: {head_err}"
            log.warning(log_line)
            _send_broker_response(client_sock, 400, "Bad Request", head_err)
            decision = BrokerDecision(
                destination="unknown",
                verdict="MALFORMED",
                status_code=400,
                reason=head_err,
                log_line=log_line,
            )
            if on_decision:
                on_decision(decision)
            return decision

        try:
            host, port = _parse_destination_token(target)
            if not (_HOSTNAME_RE.match(host) or _IPV6_RE.match(host)):
                raise PolicyConfigurationError(
                    "invalid destination syntax: illegal characters in host"
                )
            if port < 1 or port > 65535:
                raise PolicyConfigurationError(
                    "invalid destination syntax: port out of range"
                )
        except PolicyConfigurationError:
            head_err = "invalid destination syntax: malformed host:port authority"
            log_line = f"PROXY REFUSED malformed-request: {head_err}"
            log.warning(log_line)
            _send_broker_response(client_sock, 400, "Bad Request", head_err)
            decision = BrokerDecision(
                destination="unknown",
                verdict="MALFORMED",
                status_code=400,
                reason=head_err,
                log_line=log_line,
            )
            if on_decision:
                on_decision(decision)
            return decision

        # Consult policy
        dest_str = f"{host}:{port}"
        verdict = policy.decide(host, port)
        if not verdict.allowed:
            log_line = f"PROXY DENIED {dest_str}: {verdict.reason}"
            log.info(log_line)
            _send_broker_response(client_sock, 403, "Forbidden", verdict.reason)
            decision = BrokerDecision(
                destination=dest_str,
                verdict="DENIED",
                status_code=403,
                reason=verdict.reason,
                log_line=log_line,
            )
            if on_decision:
                on_decision(decision)
            return decision

        # Allowed: open upstream connection
        log_line = f"PROXY ALLOWED {dest_str}: {verdict.reason}"
        log.info(log_line)

        connect_host = (
            host[1:-1] if host.startswith("[") and host.endswith("]") else host
        )
        try:
            upstream_sock = socket.create_connection(
                (connect_host, port), timeout=connect_timeout
            )
        except (OSError, socket.timeout) as exc:
            err_msg = f"upstream connection failed: {exc}"
            _send_broker_response(
                client_sock, 502, "Bad Gateway", "upstream connection failed"
            )
            decision = BrokerDecision(
                destination=dest_str,
                verdict="UPSTREAM_ERROR",
                status_code=502,
                reason=err_msg,
                log_line=f"PROXY ERROR {dest_str}: {err_msg}",
            )
            if on_decision:
                on_decision(decision)
            return decision

        # Tunnel established: send 200 Connection Established
        try:
            client_sock.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            decision = BrokerDecision(
                destination=dest_str,
                verdict="ALLOWED",
                status_code=200,
                reason=verdict.reason,
                log_line=log_line,
            )
            if on_decision:
                on_decision(decision)
            _relay_sockets(client_sock, upstream_sock, timeout=relay_timeout)
            return decision
        finally:
            try:
                upstream_sock.close()
            except OSError:
                pass

    finally:
        try:
            client_sock.close()
        except OSError:
            pass


class EgressBroker:
    """Parent-owned filtering broker listening on AF_UNIX socket."""

    def __init__(
        self,
        policy: EgressPolicy,
        socket_path: str | Path,
        *,
        connect_timeout: float = CONNECT_TIMEOUT_SECONDS,
        relay_timeout: float = RELAY_TIMEOUT_SECONDS,
        logger: logging.Logger | None = None,
    ) -> None:
        self.policy = policy
        self.socket_path = Path(socket_path).resolve()
        self.connect_timeout = connect_timeout
        self.relay_timeout = relay_timeout
        self.logger = logger or logging.getLogger(__name__)
        self.decisions: list[BrokerDecision] = []
        self._lock = threading.Lock()
        self._server_sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._workers: list[threading.Thread] = []

    def socket_dir_mode(self) -> int:
        """Return the permission mode of the socket parent directory."""
        return stat.S_IMODE(self.socket_path.parent.stat().st_mode)

    def start(self) -> None:
        """Start the AF_UNIX broker listener."""
        if not hasattr(socket, "AF_UNIX"):
            raise RuntimeError("AF_UNIX sockets are not supported on this platform")

        sock_dir = self.socket_path.parent
        sock_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(sock_dir, 0o700)

        if self.socket_path.exists():
            self.socket_path.unlink()

        self._server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server_sock.bind(str(self.socket_path))
        self._server_sock.listen(128)
        self._server_sock.settimeout(0.5)
        self._running = True
        self._thread = threading.Thread(
            target=self._accept_loop,
            name="egress-broker-accept",
            daemon=True,
        )
        self._thread.start()

    def _accept_loop(self) -> None:
        while self._running and self._server_sock:
            try:
                conn, _ = self._server_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            def worker(client_conn: socket.socket) -> None:
                def record(decision: BrokerDecision) -> None:
                    with self._lock:
                        self.decisions.append(decision)

                handle_broker_connection(
                    client_conn,
                    self.policy,
                    connect_timeout=self.connect_timeout,
                    relay_timeout=self.relay_timeout,
                    logger=self.logger,
                    on_decision=record,
                )

            t = threading.Thread(target=worker, args=(conn,), daemon=True)
            with self._lock:
                self._workers.append(t)
            t.start()

    def stop(self) -> None:
        """Stop the broker and unlink the AF_UNIX socket."""
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except OSError:
                pass
            self._server_sock = None

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        if self.socket_path.exists():
            try:
                self.socket_path.unlink()
            except OSError:
                pass

        with self._lock:
            workers = list(self._workers)
        for w in workers:
            w.join(timeout=1.0)

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        self.stop()
