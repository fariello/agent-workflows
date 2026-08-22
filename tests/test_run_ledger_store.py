"""Tests for agent_workflows.run_ledger_store (awoptimize Order 03 6psux0, validates E-01..E-06).

Covers:
- E-01 / V-01: Append-only JSONL ledger store with monotonic seq, timestamps, single-writer lock.
- E-02 / V-02: Crash recovery, torn trailing line truncation, intact prior history.
- E-03 / V-03: Hash chaining and tamper evidence (mutation, insertion, deletion, reordering).
- E-04 / V-04: Explicit typed corruption refusal (BrokenChainError, SequenceGapError, UnparseableLineError, SchemaInvalidRecordError).
- E-05 / V-05: Redaction hooks (pre-append redaction, secrets kept off disk, chain valid over redacted bytes).
- E-06 / V-06: Focused test suite passes, no shallow assertions.
"""

from __future__ import annotations

import concurrent.futures
import json
import re
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

from agent_workflows import run_ledger_schema as schema
from agent_workflows import run_ledger_store as store


def _sample_record(
    kind: str = "run", actor: str = "runtime", **kwargs: Any
) -> Dict[str, Any]:
    """Helper to create a conforming record dictionary for testing."""
    rec: Dict[str, Any] = {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": kind,
        "run_id": "run-abcdef1234",
        "actor": actor,
        "parent": "",
    }
    if kind == "run":
        rec.update(
            {
                "workflow_digest": "a" * 64,
                "requirement_digest": "b" * 64,
                "repo": "agent-workflows",
                "head": "commit-12345",
            }
        )
    elif kind == "step_attempt":
        rec.update(
            {
                "step": "S-01",
                "state": "performed",
                "attempt": 1,
            }
        )
    elif kind == "tool_event":
        rec.update(
            {
                "argv": ["pytest", "-v"],
                "cwd": "/workspace",
                "exit_code": 0,
                "stdout_sha256": "c" * 64,
            }
        )
    elif kind == "verifier_decision":
        rec.update(
            {
                "actor": "verifier",
                "requirement": "R-01",
                "result": "satisfied",
            }
        )
    elif kind == "terminal_transaction":
        rec.update(
            {
                "actor": "coordinator",
                "terminal_status": "executed",
                "moved_to": "executed/",
            }
        )
    rec.update(kwargs)
    return rec


class TestAppendAndReadBack(unittest.TestCase):
    """E-01 / V-01: Append-only store, monotonic sequence assignment, ordering."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ledger_path = Path(self.tmp_dir.name) / "events.jsonl"
        self.store = store.RunLedgerStore(self.ledger_path)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_append_first_record_must_be_run(self) -> None:
        """First record must be of kind 'run'."""
        non_run = _sample_record(kind="step_attempt")
        with self.assertRaises(store.SchemaInvalidRecordError) as ctx:
            self.store.append(non_run)
        self.assertEqual(ctx.exception.seq, 0)
        self.assertTrue(any(f.code == "RL-E041" for f in ctx.exception.findings))

    def test_append_assigns_monotonic_seq_and_timestamp(self) -> None:
        """Appended records receive strictly monotonic seq and valid RFC3339 timestamps."""
        r0 = self.store.append(_sample_record(kind="run"))
        self.assertEqual(r0["seq"], 0)
        self.assertEqual(r0["prev_hash"], store.GENESIS_HASH)
        self.assertTrue(schema.is_timestamp(r0["timestamp"]))

        r1 = self.store.append(_sample_record(kind="step_attempt"))
        self.assertEqual(r1["seq"], 1)
        self.assertEqual(r1["prev_hash"], store.compute_record_hash(r0))
        self.assertTrue(schema.is_timestamp(r1["timestamp"]))

        r2 = self.store.append(_sample_record(kind="tool_event"))
        self.assertEqual(r2["seq"], 2)
        self.assertEqual(r2["prev_hash"], store.compute_record_hash(r1))
        self.assertTrue(schema.is_timestamp(r2["timestamp"]))

        records = self.store.read_records()
        self.assertEqual(len(records), 3)
        self.assertEqual([r["seq"] for r in records], [0, 1, 2])
        self.assertEqual(records[0]["kind"], "run")
        self.assertEqual(records[1]["kind"], "step_attempt")
        self.assertEqual(records[2]["kind"], "tool_event")

    def test_no_api_path_overwrites_or_deletes(self) -> None:
        """Verify API does not expose methods to mutate or delete prior lines."""
        self.assertFalse(hasattr(self.store, "delete"))
        self.assertFalse(hasattr(self.store, "update"))
        self.assertFalse(hasattr(self.store, "truncate"))
        self.assertFalse(hasattr(self.store, "overwrite"))


class TestSingleWriterConcurrency(unittest.TestCase):
    """E-01 / V-01: Single-writer locking ensures serialized appends without interleaving."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ledger_path = Path(self.tmp_dir.name) / "events.jsonl"
        self.store = store.RunLedgerStore(self.ledger_path)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_concurrent_appenders_do_not_interleave(self) -> None:
        """Concurrent appends across threads serialize cleanly with monotonic seqs."""
        self.store.append(_sample_record(kind="run"))

        def append_step(idx: int) -> Dict[str, Any]:
            thread_store = store.RunLedgerStore(self.ledger_path)
            return thread_store.append(
                _sample_record(kind="step_attempt", step=f"S-{idx:02d}")
            )

        num_threads = 20
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(append_step, i + 1) for i in range(num_threads)]
            for f in futures:
                self.assertIsNotNone(f.result())

        records = self.store.read_records()
        self.assertEqual(len(records), num_threads + 1)
        seqs = [r["seq"] for r in records]
        self.assertEqual(seqs, list(range(num_threads + 1)))

        verification = self.store.verify_chain()
        self.assertTrue(
            verification.clean, msg=f"Verification failed: {verification.break_info}"
        )
        self.assertEqual(verification.count, num_threads + 1)

    def test_lock_timeout_fails_closed(self) -> None:
        """Lock contention exceeding timeout raises LedgerLockError (fails closed)."""
        with self.store.writer_lock():
            contending_store = store.RunLedgerStore(self.ledger_path, lock_timeout=0.05)
            with self.assertRaises(store.LedgerLockError):
                contending_store.append(_sample_record(kind="run"))


class TestCrashRecovery(unittest.TestCase):
    """E-02 / V-02: Crash safety and torn trailing line recovery."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ledger_path = Path(self.tmp_dir.name) / "events.jsonl"
        self.store = store.RunLedgerStore(self.ledger_path)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_recover_on_clean_ledger_is_noop(self) -> None:
        """Clean ledger recovery reports no recovery needed."""
        self.store.append(_sample_record(kind="run"))
        self.store.append(_sample_record(kind="step_attempt"))
        result = self.store.recover()
        self.assertFalse(result.recovered)
        self.assertEqual(result.truncated_bytes, 0)
        self.assertIsNone(result.torn_line)
        self.assertEqual(len(self.store.read_records()), 2)

    def test_recover_truncates_torn_trailing_partial_line(self) -> None:
        """Torn trailing line without newline is safely discarded while prior records stay intact."""
        self.store.append(_sample_record(kind="run"))
        self.store.append(_sample_record(kind="step_attempt", step="S-01"))

        torn_bytes = (
            b'{"schema_version": 1, "kind": "step_attempt", "actor": "runtime", "par'
        )
        with open(self.ledger_path, "ab") as f:
            f.write(torn_bytes)

        with self.assertRaises(store.UnparseableLineError):
            self.store.read_records()

        recovery = self.store.recover()
        self.assertTrue(recovery.recovered)
        self.assertEqual(recovery.truncated_bytes, len(torn_bytes))
        self.assertEqual(recovery.torn_line, torn_bytes.decode("utf-8"))

        records = self.store.read_records()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["kind"], "run")
        self.assertEqual(records[1]["kind"], "step_attempt")

        r2 = self.store.append(_sample_record(kind="tool_event"))
        self.assertEqual(r2["seq"], 2)
        self.assertEqual(len(self.store.read_records()), 3)

    def test_recover_truncates_torn_trailing_unparseable_line_with_newline(
        self,
    ) -> None:
        """Torn trailing unparseable line ending in newline is also safely truncated."""
        self.store.append(_sample_record(kind="run"))

        corrupt_line = b'{"truncated_json_corrupt_trailing\n'
        with open(self.ledger_path, "ab") as f:
            f.write(corrupt_line)

        recovery = self.store.recover()
        self.assertTrue(recovery.recovered)
        self.assertEqual(recovery.truncated_bytes, len(corrupt_line))

        records = self.store.read_records()
        self.assertEqual(len(records), 1)

    def test_recover_refuses_to_truncate_earlier_corrupted_records(self) -> None:
        """Corruption in middle/earlier history is NOT truncated; raises LedgerCorruption."""
        self.store.append(_sample_record(kind="run"))
        self.store.append(_sample_record(kind="step_attempt", step="S-01"))
        self.store.append(_sample_record(kind="step_attempt", step="S-02"))

        lines = self.ledger_path.read_text(encoding="utf-8").splitlines(keepends=True)
        lines[1] = '{"not_valid_json": \n'
        self.ledger_path.write_text("".join(lines), encoding="utf-8")

        with self.assertRaises(store.LedgerCorruption):
            self.store.recover()


class TestHashChainingAndTamperEvidence(unittest.TestCase):
    """E-03 / V-03: SHA-256 hash chaining and tamper detection at exact sequence."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ledger_path = Path(self.tmp_dir.name) / "events.jsonl"
        self.store = store.RunLedgerStore(self.ledger_path)
        self.store.append(_sample_record(kind="run"))
        self.store.append(_sample_record(kind="step_attempt", step="S-01"))
        self.store.append(_sample_record(kind="step_attempt", step="S-02"))
        self.store.append(_sample_record(kind="verifier_decision"))

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_unmodified_ledger_verifies_clean(self) -> None:
        """Unmodified ledger returns clean verification."""
        v = self.store.verify_chain()
        self.assertTrue(v.clean)
        self.assertIsNone(v.break_info)
        self.assertEqual(v.count, 4)

    def test_mutation_of_record_detected_at_next_seq(self) -> None:
        """Modifying record at seq 1 causes chain break at seq 2."""
        lines = self.ledger_path.read_text(encoding="utf-8").splitlines(keepends=True)
        rec1 = json.loads(lines[1])
        rec1["step"] = "S-TAMPERED"
        lines[1] = json.dumps(rec1, sort_keys=True, separators=(",", ":")) + "\n"
        self.ledger_path.write_text("".join(lines), encoding="utf-8")

        v = self.store.verify_chain()
        self.assertFalse(v.clean)
        self.assertIsNotNone(v.break_info)
        self.assertEqual(v.break_info.seq, 2)
        self.assertIn("prev_hash mismatch", v.break_info.reason)

    def test_mutation_of_seq0_genesis_prev_hash_detected(self) -> None:
        """Modifying seq 0 prev_hash causes chain break at seq 0."""
        lines = self.ledger_path.read_text(encoding="utf-8").splitlines(keepends=True)
        rec0 = json.loads(lines[0])
        rec0["prev_hash"] = "f" * 64
        lines[0] = json.dumps(rec0, sort_keys=True, separators=(",", ":")) + "\n"
        self.ledger_path.write_text("".join(lines), encoding="utf-8")

        v = self.store.verify_chain()
        self.assertFalse(v.clean)
        self.assertIsNotNone(v.break_info)
        self.assertEqual(v.break_info.seq, 0)
        self.assertIn("genesis mismatch", v.break_info.reason)

    def test_insertion_of_record_detected(self) -> None:
        """Inserting a bogus record between seq 1 and seq 2 breaks the chain."""
        lines = self.ledger_path.read_text(encoding="utf-8").splitlines(keepends=True)
        bogus_rec = _sample_record(kind="step_attempt", step="S-BOGUS", seq=1)
        bogus_rec["prev_hash"] = "e" * 64
        bogus_line = json.dumps(bogus_rec, sort_keys=True, separators=(",", ":")) + "\n"
        lines.insert(2, bogus_line)
        self.ledger_path.write_text("".join(lines), encoding="utf-8")

        v = self.store.verify_chain()
        self.assertFalse(v.clean)
        self.assertIsNotNone(v.break_info)
        self.assertIn(v.break_info.seq, (1, 2))

    def test_deletion_of_record_detected(self) -> None:
        """Deleting record at seq 1 causes sequence gap and chain break at seq 2."""
        lines = self.ledger_path.read_text(encoding="utf-8").splitlines(keepends=True)
        del lines[1]
        self.ledger_path.write_text("".join(lines), encoding="utf-8")

        v = self.store.verify_chain()
        self.assertFalse(v.clean)
        self.assertIsNotNone(v.break_info)
        self.assertEqual(v.break_info.seq, 2)

    def test_reordering_of_records_detected(self) -> None:
        """Reordering records (swapping seq 1 and seq 2) breaks the chain."""
        lines = self.ledger_path.read_text(encoding="utf-8").splitlines(keepends=True)
        lines[1], lines[2] = lines[2], lines[1]
        self.ledger_path.write_text("".join(lines), encoding="utf-8")

        v = self.store.verify_chain()
        self.assertFalse(v.clean)
        self.assertIsNotNone(v.break_info)
        self.assertIn(v.break_info.seq, (1, 2))


class TestExplicitCorruptionRefusal(unittest.TestCase):
    """E-04 / V-04: Explicit typed LedgerCorruption refusal on any read/verify path."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ledger_path = Path(self.tmp_dir.name) / "events.jsonl"
        self.store = store.RunLedgerStore(self.ledger_path)
        self.store.append(_sample_record(kind="run"))
        self.store.append(_sample_record(kind="step_attempt", step="S-01"))

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_chain_break_raises_broken_chain_error(self) -> None:
        """Chain break raises BrokenChainError subclass of LedgerCorruption."""
        lines = self.ledger_path.read_text(encoding="utf-8").splitlines(keepends=True)
        rec0 = json.loads(lines[0])
        rec0["repo"] = "tampered-repo"
        lines[0] = json.dumps(rec0, sort_keys=True, separators=(",", ":")) + "\n"
        self.ledger_path.write_text("".join(lines), encoding="utf-8")

        with self.assertRaises(store.BrokenChainError) as ctx:
            self.store.read_records()
        self.assertIsInstance(ctx.exception, store.LedgerCorruption)
        self.assertEqual(ctx.exception.seq, 1)

    def test_sequence_gap_raises_sequence_gap_error(self) -> None:
        """Sequence gap raises SequenceGapError subclass of LedgerCorruption."""
        lines = self.ledger_path.read_text(encoding="utf-8").splitlines(keepends=True)
        rec1 = json.loads(lines[1])
        rec1["seq"] = 5
        lines[1] = json.dumps(rec1, sort_keys=True, separators=(",", ":")) + "\n"
        self.ledger_path.write_text("".join(lines), encoding="utf-8")

        with self.assertRaises(store.SequenceGapError) as ctx:
            self.store.read_records()
        self.assertIsInstance(ctx.exception, store.LedgerCorruption)
        self.assertEqual(ctx.exception.seq, 5)
        self.assertEqual(ctx.exception.expected_seq, 1)

    def test_unparseable_line_raises_unparseable_line_error(self) -> None:
        """Unparseable JSON raises UnparseableLineError subclass of LedgerCorruption."""
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write("this is not json at all\n")

        with self.assertRaises(store.UnparseableLineError) as ctx:
            self.store.read_records()
        self.assertIsInstance(ctx.exception, store.LedgerCorruption)
        self.assertEqual(ctx.exception.line_no, 3)

    def test_schema_invalid_record_raises_schema_invalid_record_error(self) -> None:
        """Schema-invalid record raises SchemaInvalidRecordError subclass of LedgerCorruption."""
        lines = self.ledger_path.read_text(encoding="utf-8").splitlines(keepends=True)
        rec1 = json.loads(lines[1])
        del rec1["step"]
        lines[1] = json.dumps(rec1, sort_keys=True, separators=(",", ":")) + "\n"
        self.ledger_path.write_text("".join(lines), encoding="utf-8")

        with self.assertRaises(store.SchemaInvalidRecordError) as ctx:
            self.store.read_records()
        self.assertIsInstance(ctx.exception, store.LedgerCorruption)
        self.assertEqual(ctx.exception.seq, 1)
        self.assertTrue(any(f.code == "RL-E020" for f in ctx.exception.findings))


class TestRedactionHooks(unittest.TestCase):
    """E-05 / V-05: Redaction hooks keep secrets off disk while preserving hash chain."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ledger_path = Path(self.tmp_dir.name) / "events.jsonl"

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_redaction_removes_secret_from_disk_and_keeps_chain_valid(self) -> None:
        """Seeded secret is replaced before append, secret is absent from disk, chain is valid."""
        raw_secret = "ghp_VerySecretToken1234567890"
        policy = store.RedactionPolicy(
            patterns=[re.compile(r"ghp_[A-Za-z0-9]+")],
            sensitive_keys=["token", "password", "api_key"],
            mask="[REDACTED_SECRET]",
        )
        ledger_store = store.RunLedgerStore(self.ledger_path, redaction_policy=policy)

        ledger_store.append(_sample_record(kind="run"))

        rec = _sample_record(
            kind="tool_event",
            argv=[
                "curl",
                "-H",
                f"Authorization: Bearer {raw_secret}",
                "https://api.github.com",
            ],
            token=raw_secret,
        )
        appended = ledger_store.append(rec)

        self.assertTrue(appended.get("redacted"))
        self.assertNotIn(raw_secret, json.dumps(appended))
        self.assertIn("[REDACTED_SECRET]", appended["argv"][2])
        self.assertEqual(appended["token"], "[REDACTED_SECRET]")

        raw_disk_content = self.ledger_path.read_text(encoding="utf-8")
        self.assertNotIn(raw_secret, raw_disk_content)
        self.assertIn("[REDACTED_SECRET]", raw_disk_content)

        verification = ledger_store.verify_chain()
        self.assertTrue(verification.clean)
        self.assertEqual(verification.count, 2)

        records = ledger_store.read_records()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[1]["token"], "[REDACTED_SECRET]")


if __name__ == "__main__":
    unittest.main()
