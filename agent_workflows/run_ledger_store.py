"""Run ledger store: append-only, tamper-evident single-writer JSONL persistence substrate.

awoptimize Order 03 (`6psux0`) E-01..E-05. Provides the append-only, crash-safe, hash-chained ledger
store that persists Order-02-validated records. No executor or caller can rewrite, mutate, or delete
prior records. A single-writer advisory lock serializes appends. Hash chaining over SHA-256 makes any
mutation, insertion, deletion, or reordering detectable at an exact sequence number. Explicit typed
corruption refusal (subclasses of LedgerCorruption) fails closed on any corrupted state. Redaction
hooks sanitize secrets before persistence while keeping the chain valid over redacted bytes.

Pure stdlib implementation conforming to D138 (dependency minimization) and D139 (no runtime YAML).
"""

from __future__ import annotations

import contextlib
import copy
import datetime
import fcntl
import hashlib
import json
import os
import re
import threading
import time
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Pattern,
    Sequence,
    Tuple,
    Union,
)

from agent_workflows import run_ledger_schema as schema
from agent_workflows.run_ledger_schema import Finding

GENESIS_HASH: str = "0" * 64
DEFAULT_LOCK_TIMEOUT: float = 10.0

# The ONLY filename a run ledger owns. The drivers' own append-only event log is `events.jsonl` and is
# a DIFFERENT format (see `is_ledger_shaped`); a ledger must never claim that name (`e6b9kt`).
LEDGER_FILENAME: str = "ledger.jsonl"

# Envelope fields that identify a line as a ledger record at all. A driver event line
# (`{"at":..., "event":..., "run_id":...}`) carries NONE of these, which is what makes wrong-format
# distinguishable from corrupt.
LEDGER_ENVELOPE_MARKERS: Tuple[str, ...] = (
    "schema_version",
    "kind",
    "seq",
    "prev_hash",
)


# ---- exception hierarchy (fail closed) -----------------------------------------------------------


class LedgerCorruption(Exception):
    """Base exception for all ledger corruption and integrity failures (fail closed)."""

    pass


class BrokenChainError(LedgerCorruption):
    """Raised when the SHA-256 hash chain is broken (mutation, deletion, or insertion)."""

    def __init__(self, seq: int, expected: str, actual: str, message: str = "") -> None:
        self.seq = seq
        self.expected = expected
        self.actual = actual
        msg = (
            message
            or f"Broken hash chain at seq {seq}: expected prev_hash {expected!r}, got {actual!r}"
        )
        super().__init__(msg)


class SequenceGapError(LedgerCorruption):
    """Raised when sequence numbers are not strictly monotonic starting from 0."""

    def __init__(self, seq: int, expected_seq: int, message: str = "") -> None:
        self.seq = seq
        self.expected_seq = expected_seq
        msg = message or f"Sequence mismatch at seq {seq}: expected seq {expected_seq}"
        super().__init__(msg)


class UnparseableLineError(LedgerCorruption):
    """Raised when a line in the ledger is not valid JSON."""

    def __init__(self, line_no: int, raw_line: str, message: str = "") -> None:
        self.line_no = line_no
        self.raw_line = raw_line
        msg = message or f"Unparseable JSON at line {line_no}: {raw_line!r}"
        super().__init__(msg)


class SchemaInvalidRecordError(LedgerCorruption):
    """Raised when a ledger record violates the Order-02 schema or state rules."""

    def __init__(
        self, seq: int, findings: Tuple[Finding, ...], message: str = ""
    ) -> None:
        self.seq = seq
        self.findings = findings
        msg = message or f"Schema-invalid record at seq {seq}: {findings}"
        super().__init__(msg)


class NotALedgerError(Exception):
    """Raised when a file is healthy JSONL but is NOT a run ledger at all (wrong format).

    Deliberately NOT a `LedgerCorruption` subclass. Wrong-format and corrupt are DIFFERENT diagnoses:
    calling a healthy driver event log 'corrupt' accuses good data of damage it does not have
    (`e6b9kt`). Corruption means 'this IS a ledger and it has been damaged or tampered with'; this
    means 'this is not a ledger, so no verdict about its integrity is being made'.
    """

    def __init__(self, path: Union[str, Path], detail: str = "") -> None:
        self.path = Path(path)
        self.detail = detail
        msg = f"{self.path} is not a run ledger file"
        if detail:
            msg = f"{msg}: {detail}"
        super().__init__(msg)


class LedgerLockError(Exception):
    """Raised when the single-writer lock cannot be acquired within timeout or is lost."""

    pass


# ---- result structures ---------------------------------------------------------------------------


class ChainBreak(NamedTuple):
    seq: int
    expected: str
    actual: str
    reason: str


class ChainVerification(NamedTuple):
    clean: bool
    break_info: Optional[ChainBreak]
    count: int


class RecoveryResult(NamedTuple):
    recovered: bool
    truncated_bytes: int
    torn_line: Optional[str]


# ---- hash calculation ----------------------------------------------------------------------------


def is_ledger_shaped(rec: Any) -> bool:
    """True when a parsed line carries the ledger envelope markers, i.e. it IS a ledger record.

    Deliberately SHALLOW: it asks 'is this the right KIND of file' and says nothing about integrity.
    A record that is ledger-shaped but damaged (tampered `prev_hash`, seq gap, bad per-kind field)
    stays the corruption checker's business, so this predicate can never mask real tampering.
    """
    if not isinstance(rec, Mapping):
        return False
    return any(marker in rec for marker in LEDGER_ENVELOPE_MARKERS)


def classify_jsonl_file(path: Union[str, Path]) -> str:
    """Classify a JSONL file WITHOUT judging ledger integrity.

    Returns one of: `missing`, `empty`, `unparseable` (not JSON at all), `not-a-ledger` (valid JSON
    lines carrying none of the ledger envelope markers), or `ledger` (the first line is
    ledger-shaped, so integrity verification is the right next question).
    """
    p = Path(path)
    if not p.exists() or not p.is_file():
        return "missing"
    try:
        raw = p.read_bytes()
    except OSError:
        return "missing"
    if not raw.strip():
        return "empty"
    for raw_line in raw.splitlines():
        stripped = raw_line.decode("utf-8", errors="replace").strip()
        if not stripped:
            continue
        try:
            rec = json.loads(stripped)
        except json.JSONDecodeError:
            return "unparseable"
        return "ledger" if is_ledger_shaped(rec) else "not-a-ledger"
    return "empty"


def compute_record_hash(rec_or_line: Union[Mapping[str, Any], str, bytes]) -> str:
    """Compute deterministic SHA-256 hex digest of a record dictionary or raw line string/bytes."""
    if isinstance(rec_or_line, (str, bytes)):
        if isinstance(rec_or_line, str):
            raw_bytes = rec_or_line.rstrip("\r\n").encode("utf-8")
        else:
            raw_bytes = rec_or_line.rstrip(b"\r\n")
        return hashlib.sha256(raw_bytes).hexdigest()
    # Canonical JSON serialization for mappings
    raw_str = json.dumps(rec_or_line, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


# ---- redaction hooks -----------------------------------------------------------------------------


class RedactionPolicy:
    """Pre-append redaction policy to scrub secrets before records land in the ledger."""

    def __init__(
        self,
        patterns: Sequence[Union[str, Pattern[str]]] = (),
        sensitive_keys: Sequence[str] = (),
        mask: str = "[REDACTED]",
        custom_hook: Optional[
            Callable[[Dict[str, Any]], Tuple[Dict[str, Any], bool]]
        ] = None,
    ) -> None:
        compiled_patterns: List[Pattern[str]] = []
        for p in patterns:
            if isinstance(p, str):
                compiled_patterns.append(re.compile(re.escape(p)))
            else:
                compiled_patterns.append(p)
        self.patterns = tuple(compiled_patterns)
        self.sensitive_keys = frozenset(sensitive_keys)
        self.mask = mask
        self.custom_hook = custom_hook

    def _redact_value(
        self, val: Any, parent_key: Optional[str] = None
    ) -> Tuple[Any, bool]:
        if parent_key in self.sensitive_keys:
            return self.mask, True

        if isinstance(val, str):
            modified = False
            curr = val
            for pat in self.patterns:
                if pat.search(curr):
                    curr = pat.sub(self.mask, curr)
                    modified = True
            return curr, modified

        if isinstance(val, list):
            res_list = []
            modified = False
            for item in val:
                new_item, item_mod = self._redact_value(item, parent_key)
                res_list.append(new_item)
                if item_mod:
                    modified = True
            return res_list, modified

        if isinstance(val, dict):
            res_dict = {}
            modified = False
            for k, v in val.items():
                new_v, v_mod = self._redact_value(v, k)
                res_dict[k] = new_v
                if v_mod:
                    modified = True
            return res_dict, modified

        return val, False

    def redact(self, record: Mapping[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """Redact sensitive data from a record mapping. Returns (redacted_dict, was_redacted)."""
        cloned = copy.deepcopy(dict(record))
        redacted_dict, was_redacted = self._redact_value(cloned)
        if self.custom_hook is not None:
            redacted_dict, custom_redacted = self.custom_hook(redacted_dict)
            was_redacted = was_redacted or custom_redacted
        if was_redacted:
            redacted_dict["redacted"] = True
        return redacted_dict, was_redacted


# ---- run ledger store ----------------------------------------------------------------------------


class RunLedgerStore:
    """Append-only, tamper-evident single-writer JSONL ledger store."""

    def __init__(
        self,
        path: Union[str, Path],
        lock_path: Optional[Union[str, Path]] = None,
        redaction_policy: Optional[RedactionPolicy] = None,
        lock_timeout: float = DEFAULT_LOCK_TIMEOUT,
    ) -> None:
        self._path = Path(path)
        self._lock_path = Path(lock_path) if lock_path else Path(str(path) + ".lock")
        self._redaction_policy = redaction_policy
        self._lock_timeout = lock_timeout
        self._process_lock = threading.Lock()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def lock_path(self) -> Path:
        return self._lock_path

    @contextlib.contextmanager
    def writer_lock(self, timeout: Optional[float] = None) -> Iterator[None]:
        """Acquire single-writer lock combining process-level and advisory file-level lock."""
        lock_timeout = self._lock_timeout if timeout is None else timeout
        acquired_thread_lock = self._process_lock.acquire(timeout=lock_timeout)
        if not acquired_thread_lock:
            raise LedgerLockError(
                f"Failed to acquire thread writer lock for {self._lock_path} within {lock_timeout}s"
            )

        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_file = None
        try:
            lock_file = open(self._lock_path, "a+")
            fd = lock_file.fileno()
            start_time = time.monotonic()
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except (BlockingIOError, IOError, OSError):
                    if (time.monotonic() - start_time) >= lock_timeout:
                        raise LedgerLockError(
                            f"Failed to acquire advisory lock on {self._lock_path} within {lock_timeout}s"
                        )
                    time.sleep(0.01)
            yield
        finally:
            if lock_file is not None:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                except (IOError, OSError):
                    pass
                try:
                    lock_file.close()
                except (IOError, OSError):
                    pass
            self._process_lock.release()

    def _require_ledger_shape(self) -> None:
        """Fail with `NotALedgerError` when this file is valid JSONL of a NON-ledger format.

        Only the wholesale case is caught (the first non-blank line carries no envelope marker at
        all). A ledger-shaped-but-damaged file falls straight through to the corruption checks.
        """
        classification = classify_jsonl_file(self._path)
        if classification == "not-a-ledger":
            # The wording deliberately makes NO claim about the file's integrity, and a test asserts
            # the message never contains the word 'corrupt': the file is healthy, just not a ledger.
            raise NotALedgerError(
                self._path,
                "the file is valid JSONL but carries none of the ledger envelope fields "
                f"({', '.join(LEDGER_ENVELOPE_MARKERS)}). A run ledger is named "
                f"'{LEDGER_FILENAME}'; the drivers' own event log 'events.jsonl' is a different "
                "format and is read with `aw runs`. The file itself looks intact",
            )

    def _get_tail_state(self) -> Tuple[int, str]:
        """Inspect ledger tail to find next seq and prev_hash. Must be called under writer_lock."""
        if not self._path.exists() or self._path.stat().st_size == 0:
            return 0, GENESIS_HASH

        # Read last line
        lines = self._path.read_bytes().splitlines()
        if not lines:
            return 0, GENESIS_HASH

        last_raw = lines[-1]
        try:
            rec = json.loads(last_raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise UnparseableLineError(
                len(lines),
                last_raw.decode("utf-8", errors="replace"),
                f"Cannot determine ledger tail state due to unparseable trailing line (run recover() to fix): {exc}",
            ) from exc

        last_seq = rec.get("seq")
        if not isinstance(last_seq, int) or isinstance(last_seq, bool):
            raise LedgerCorruption(f"Invalid seq in trailing record: {last_seq}")

        prev_hash = compute_record_hash(last_raw)
        return last_seq + 1, prev_hash

    def append(
        self,
        record: Mapping[str, Any],
        *,
        redaction_policy: Optional[RedactionPolicy] = None,
    ) -> Dict[str, Any]:
        """Append one Order-02 validated record. Atomically assigns seq, prev_hash, and timestamp."""
        with self.writer_lock():
            next_seq, prev_hash = self._get_tail_state()

            rec_to_write: Dict[str, Any] = copy.deepcopy(dict(record))
            rec_to_write["seq"] = next_seq
            rec_to_write["prev_hash"] = prev_hash

            if not rec_to_write.get("timestamp"):
                rec_to_write["timestamp"] = datetime.datetime.now(
                    datetime.timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ")

            active_policy = redaction_policy or self._redaction_policy
            if active_policy is not None:
                rec_to_write, _ = active_policy.redact(rec_to_write)

            # Validate record against Order-02 schema
            val_res = schema.validate_record(rec_to_write)
            if not val_res.ok:
                raise SchemaInvalidRecordError(next_seq, val_res.findings)

            # Anti-false-completion state check: first record must be kind run
            if next_seq == 0 and rec_to_write.get("kind") != "run":
                raise SchemaInvalidRecordError(
                    0,
                    (
                        Finding(
                            "RL-E041", "kind", "first ledger record must be kind 'run'"
                        ),
                    ),
                )

            # Canonical JSON line
            line_str = json.dumps(rec_to_write, sort_keys=True, separators=(",", ":"))
            line_bytes = (line_str + "\n").encode("utf-8")

            self._path.parent.mkdir(parents=True, exist_ok=True)
            # Atomic append + fsync
            fd = os.open(str(self._path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
            try:
                os.write(fd, line_bytes)
                os.fsync(fd)
            finally:
                os.close(fd)

            return rec_to_write

    def read_records(self, *, verify: bool = True) -> List[Dict[str, Any]]:
        """Read all records from ledger. If verify=True, fails closed on any corruption.

        Raises `NotALedgerError` (NOT a corruption error) when the file is healthy JSONL of some other
        format, so a caller reports 'wrong format' rather than accusing good data of being corrupt.
        """
        if not self._path.exists() or self._path.stat().st_size == 0:
            return []

        if verify:
            self._require_ledger_shape()

        raw_bytes = self._path.read_bytes()
        lines = raw_bytes.splitlines(keepends=True)
        records: List[Dict[str, Any]] = []

        expected_seq = 0
        expected_prev_hash = GENESIS_HASH

        for idx, raw_line in enumerate(lines):
            line_no = idx + 1
            line_str = raw_line.decode("utf-8", errors="replace")
            if not raw_line.endswith(b"\n"):
                raise UnparseableLineError(
                    line_no,
                    line_str,
                    f"Torn trailing line without newline at line {line_no}",
                )

            stripped = line_str.rstrip("\r\n")
            try:
                rec = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise UnparseableLineError(
                    line_no, stripped, f"Invalid JSON at line {line_no}: {exc}"
                ) from exc

            if verify:
                val_res = schema.validate_record(rec)
                if not val_res.ok:
                    raise SchemaInvalidRecordError(
                        rec.get("seq", idx), val_res.findings
                    )

                seq = rec.get("seq")
                if seq != expected_seq:
                    raise SequenceGapError(seq, expected_seq)

                prev_hash = rec.get("prev_hash")
                if prev_hash != expected_prev_hash:
                    raise BrokenChainError(seq, expected_prev_hash, prev_hash)

                if idx == 0 and rec.get("kind") != "run":
                    raise SchemaInvalidRecordError(
                        0,
                        (
                            Finding(
                                "RL-E041",
                                "kind",
                                "first ledger record must be kind 'run'",
                            ),
                        ),
                    )

            expected_prev_hash = compute_record_hash(raw_line)
            expected_seq = idx + 1
            records.append(rec)

        return records

    def verify_chain(self, *, raise_on_error: bool = False) -> ChainVerification:
        """Walk the ledger and verify sequence continuity and SHA-256 hash chaining.

        Raises `NotALedgerError` when the file is not a ledger at all, REGARDLESS of `raise_on_error`:
        that flag chooses how to report a corruption VERDICT, and no verdict is being made here.
        """
        if not self._path.exists() or self._path.stat().st_size == 0:
            return ChainVerification(clean=True, break_info=None, count=0)

        self._require_ledger_shape()

        raw_bytes = self._path.read_bytes()
        lines = raw_bytes.splitlines(keepends=True)

        expected_seq = 0
        expected_prev_hash = GENESIS_HASH
        processed_count = 0

        for idx, raw_line in enumerate(lines):
            line_no = idx + 1
            line_str = raw_line.decode("utf-8", errors="replace")
            if not raw_line.endswith(b"\n"):
                err = UnparseableLineError(
                    line_no, line_str, f"Torn line at line {line_no}"
                )
                if raise_on_error:
                    raise err
                return ChainVerification(
                    clean=False,
                    break_info=ChainBreak(
                        expected_seq, "complete line", line_str, "torn line"
                    ),
                    count=processed_count,
                )

            stripped = line_str.rstrip("\r\n")
            try:
                rec = json.loads(stripped)
            except json.JSONDecodeError as exc:
                err = UnparseableLineError(
                    line_no, stripped, f"Invalid JSON at line {line_no}: {exc}"
                )
                if raise_on_error:
                    raise err
                return ChainVerification(
                    clean=False,
                    break_info=ChainBreak(
                        expected_seq, "valid JSON", stripped, "unparseable line"
                    ),
                    count=processed_count,
                )

            val_res = schema.validate_record(rec)
            if not val_res.ok:
                err = SchemaInvalidRecordError(rec.get("seq", idx), val_res.findings)
                if raise_on_error:
                    raise err
                return ChainVerification(
                    clean=False,
                    break_info=ChainBreak(
                        rec.get("seq", idx),
                        "valid schema",
                        str(val_res.findings),
                        "schema violation",
                    ),
                    count=processed_count,
                )

            seq = rec.get("seq")
            if seq != expected_seq:
                err = SequenceGapError(seq, expected_seq)
                if raise_on_error:
                    raise err
                return ChainVerification(
                    clean=False,
                    break_info=ChainBreak(seq, str(expected_seq), str(seq), "seq gap"),
                    count=processed_count,
                )

            prev_hash = rec.get("prev_hash")
            if prev_hash != expected_prev_hash:
                reason = "genesis mismatch" if seq == 0 else "prev_hash mismatch"
                err = BrokenChainError(seq, expected_prev_hash, prev_hash, reason)
                if raise_on_error:
                    raise err
                return ChainVerification(
                    clean=False,
                    break_info=ChainBreak(seq, expected_prev_hash, prev_hash, reason),
                    count=processed_count,
                )

            expected_prev_hash = compute_record_hash(raw_line)
            expected_seq += 1
            processed_count += 1

        return ChainVerification(clean=True, break_info=None, count=processed_count)

    def recover(self) -> RecoveryResult:
        """Crash recovery: truncate ONLY a torn trailing partial line, leaving prior history intact."""
        with self.writer_lock():
            if not self._path.exists() or self._path.stat().st_size == 0:
                return RecoveryResult(
                    recovered=False, truncated_bytes=0, torn_line=None
                )

            raw_bytes = self._path.read_bytes()
            total_len = len(raw_bytes)

            lines = raw_bytes.splitlines(keepends=True)
            if not lines:
                return RecoveryResult(
                    recovered=False, truncated_bytes=0, torn_line=None
                )

            # Check if all lines are valid
            valid_end_offset = 0
            expected_seq = 0
            expected_prev_hash = GENESIS_HASH

            for idx, raw_line in enumerate(lines):
                is_last_line = idx == len(lines) - 1
                line_no = idx + 1

                # Check if this line is cleanly terminated and parseable
                if not raw_line.endswith(b"\n"):
                    if is_last_line:
                        # Trailing line missing newline -> candidate for recovery truncation
                        # All prior lines up to valid_end_offset must be valid!
                        torn_str = raw_line.decode("utf-8", errors="replace")
                        self._truncate_to(valid_end_offset)
                        return RecoveryResult(
                            recovered=True,
                            truncated_bytes=total_len - valid_end_offset,
                            torn_line=torn_str,
                        )
                    else:
                        raise UnparseableLineError(
                            line_no, raw_line.decode("utf-8", errors="replace")
                        )

                stripped = raw_line.rstrip(b"\r\n").decode("utf-8", errors="replace")
                try:
                    rec = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    if is_last_line:
                        # Last line is unparseable -> trailing crash artifact
                        self._truncate_to(valid_end_offset)
                        return RecoveryResult(
                            recovered=True,
                            truncated_bytes=total_len - valid_end_offset,
                            torn_line=stripped,
                        )
                    else:
                        raise UnparseableLineError(line_no, stripped) from exc

                # Check schema and chain
                val_res = schema.validate_record(rec)
                if not val_res.ok:
                    if is_last_line:
                        # If the very last line is corrupt in schema, it could be a torn append
                        self._truncate_to(valid_end_offset)
                        return RecoveryResult(
                            recovered=True,
                            truncated_bytes=total_len - valid_end_offset,
                            torn_line=stripped,
                        )
                    else:
                        raise SchemaInvalidRecordError(
                            rec.get("seq", idx), val_res.findings
                        )

                seq = rec.get("seq")
                if seq != expected_seq:
                    raise SequenceGapError(seq, expected_seq)

                prev_hash = rec.get("prev_hash")
                if prev_hash != expected_prev_hash:
                    reason = "genesis mismatch" if seq == 0 else "prev_hash mismatch"
                    raise BrokenChainError(seq, expected_prev_hash, prev_hash, reason)

                expected_prev_hash = compute_record_hash(raw_line)
                expected_seq += 1
                valid_end_offset += len(raw_line)

            # Entire file is clean
            return RecoveryResult(recovered=False, truncated_bytes=0, torn_line=None)

    def _truncate_to(self, target_len: int) -> None:
        """Safely truncate ledger file to target_len and fsync."""
        with open(self._path, "r+b") as f:
            f.truncate(target_len)
            f.flush()
            os.fsync(f.fileno())

    def count(self) -> int:
        """Return number of valid records in ledger."""
        return len(self.read_records())

    def last_record(self, *, verify: bool = True) -> Optional[Dict[str, Any]]:
        """Return the last record or None if ledger is empty."""
        records = self.read_records(verify=verify)
        return records[-1] if records else None
