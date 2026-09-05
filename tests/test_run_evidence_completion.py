"""Adversarial and functional test suite for evidence capture, validators, completion predicates, and run CLI.

awoptimize Order 04 (`yndh7k`) E-01..E-05, validating V-01..V-05.

Covers:
  * E-01 / V-01: Evidence capture (tool_event, evidence_envelope, provenance binding, env allowlist).
  * E-02 / V-02: False-completion validators (rejection of all 12+ false-completion classes with stable reasons).
  * E-03 / V-03: Completion predicates truth-table (all inputs required, toggling any input false prevents completion).
  * E-04 / V-04: Read-only `aw run show|evidence|verify-ledger` CLI (human + machine, exit codes, redaction, zero writes).
  * E-05 / V-05: Adversarial deception suite (fabricated text, checked boxes, green targeted/red full,
                 stale evidence, test deletion/weakening, mismatched worktree, replay, corruption, identity collision).
"""

from __future__ import annotations

import copy
import datetime
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

from agent_workflows import cli
from agent_workflows import run_evidence as evidence
from agent_workflows import run_ledger_schema as schema
from agent_workflows import run_ledger_store as store


def _sample_run_records(
    run_id: str = "run-abcdef1234",
    head: str = "1111111111111111111111111111111111111111",
    worktree: str = "/repo",
) -> List[Dict[str, Any]]:
    """Build a complete, conforming set of records for a clean passing run."""
    run_rec = {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "run",
        "seq": 0,
        "run_id": run_id,
        "actor": "runtime",
        "timestamp": "2026-08-22T10:00:00Z",
        "parent": "",
        "workflow_digest": "a" * 64,
        "requirement_digest": "b" * 64,
        "repo": "agent-workflows",
        "head": head,
    }
    req_set_rec = {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "requirement_set",
        "seq": 1,
        "run_id": run_id,
        "actor": "runtime",
        "timestamp": "2026-08-22T10:00:01Z",
        "parent": "",
        "requirement_digest": "b" * 64,
        "requirements": [
            {"id": "M-01", "category": "must", "digest": "c" * 64, "text": "Must do X"},
            {
                "id": "V-01",
                "category": "validation",
                "digest": "d" * 64,
                "text": "Verify X",
            },
        ],
        "scope_fence": {},
    }
    step_rec = {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "step_attempt",
        "seq": 2,
        "run_id": run_id,
        "actor": "executor",
        "timestamp": "2026-08-22T10:00:02Z",
        "parent": "",
        "step": "S-01",
        "state": "performed",
        "attempt": 1,
    }
    tool_rec = {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "tool_event",
        "seq": 3,
        "run_id": run_id,
        "actor": "executor",
        "timestamp": "2026-08-22T10:00:03Z",
        "parent": "",
        "argv": ["pytest", "-v"],
        "cwd": worktree,
        "exit_code": 0,
        "stdout_sha256": "e" * 64,
        "stderr_sha256": "0" * 64,
        "truncated": False,
    }
    env_rec = {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "evidence_envelope",
        "seq": 4,
        "run_id": run_id,
        "actor": "executor",
        "timestamp": "2026-08-22T10:00:04Z",
        "parent": "",
        "evidence_kind": "test_report",
        "binds": ["M-01", "V-01", "S-01"],
        "head": head,
        "worktree": worktree,
        "dirty_digest": "clean",
        "stdout_sha256": "e" * 64,
    }
    dec_m01 = {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "verifier_decision",
        "seq": 5,
        "run_id": run_id,
        "actor": "verifier",
        "timestamp": "2026-08-22T10:00:05Z",
        "parent": "",
        "requirement": "M-01",
        "result": "satisfied",
    }
    dec_v01 = {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "verifier_decision",
        "seq": 6,
        "run_id": run_id,
        "actor": "verifier",
        "timestamp": "2026-08-22T10:00:06Z",
        "parent": "",
        "requirement": "V-01",
        "result": "satisfied",
    }
    return [run_rec, req_set_rec, step_rec, tool_rec, env_rec, dec_m01, dec_v01]


# ==================================================================================================
# Task Group 1: Evidence Capture (E-01 / V-01)
# ==================================================================================================


class TestEvidenceCaptureProvenance(unittest.TestCase):
    """V-01 / E-01: Captured command and artifact envelopes contain all provenance fields."""

    def test_environment_allowlist_filters_secrets(self) -> None:
        """Environment filtering strictly enforces allowlist and redacts sensitive keys."""
        dirty_env = {
            "PATH": "/usr/bin:/bin",
            "HOME": "/root",
            "CI": "true",
            "AWS_SECRET_ACCESS_KEY": "fake_aws_key",
            "GITHUB_TOKEN": "fake_github_token",
            "API_KEY": "fake_api_key",
            "UNTRACKED_RANDOM_VAR": "value",
        }
        sanitized = evidence.filter_environment(dirty_env)
        self.assertEqual(sanitized.get("PATH"), "/usr/bin:/bin")
        self.assertEqual(sanitized.get("HOME"), "/root")
        self.assertEqual(sanitized.get("CI"), "true")
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", sanitized)
        self.assertNotIn("GITHUB_TOKEN", sanitized)
        self.assertNotIn("API_KEY", sanitized)
        self.assertNotIn("UNTRACKED_RANDOM_VAR", sanitized)

    def test_build_tool_event_conformance(self) -> None:
        """build_tool_event produces a valid tool_event schema record with hashes."""
        ev = evidence.build_tool_event(
            run_id="run-12345678",
            argv=["echo", "hello"],
            cwd="/workspace",
            exit_code=0,
            stdout="hello\n",
            stderr="",
            actor="executor",
        )
        val_res = schema.validate_record(ev)
        self.assertTrue(val_res.ok, msg=str(val_res.findings))
        self.assertEqual(ev["kind"], "tool_event")
        self.assertEqual(
            ev["stdout_sha256"],
            "5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03",
        )
        self.assertFalse(ev["truncated"])

    def test_build_evidence_envelope_conformance(self) -> None:
        """build_evidence_envelope binds claims to provenance (HEAD, worktree, binds)."""
        env = evidence.build_evidence_envelope(
            run_id="run-12345678",
            evidence_kind="command",
            binds=["M-01", "V-01"],
            head="abc1234",
            worktree="/workspace/repo",
            dirty_digest="clean",
        )
        val_res = schema.validate_record(env)
        self.assertTrue(val_res.ok, msg=str(val_res.findings))
        self.assertEqual(env["kind"], "evidence_envelope")
        self.assertEqual(env["binds"], ["M-01", "V-01"])
        self.assertEqual(env["head"], "abc1234")
        self.assertEqual(env["worktree"], "/workspace/repo")

    def test_build_artifact_ref_conformance(self) -> None:
        """build_artifact_ref creates schema-valid artifact_ref record."""
        art = evidence.build_artifact_ref(
            run_id="run-12345678",
            path="dist/package.whl",
            sha256="a" * 64,
        )
        val_res = schema.validate_record(art)
        self.assertTrue(val_res.ok, msg=str(val_res.findings))
        self.assertEqual(art["kind"], "artifact_ref")
        self.assertEqual(art["path"], "dist/package.whl")


# ==================================================================================================
# Task Group 2: Evidence Validators (E-02 / V-02)
# ==================================================================================================


class TestEvidenceValidators(unittest.TestCase):
    """V-02 / E-02: Every false-completion class is rejected with its distinct stable reason."""

    def test_valid_fresh_evidence_accepted(self) -> None:
        """Fresh, conforming evidence is accepted."""
        records = _sample_run_records()
        for rec in records:
            res = evidence.validate_evidence(
                rec,
                expected_head="1111111111111111111111111111111111111111",
                expected_worktree="/repo",
                check_filesystem=False,
            )
            self.assertTrue(res.ok, msg=f"Failed on {rec}: {res.findings}")

    def test_reject_missing_output(self) -> None:
        """Missing or empty required output is rejected with EV-MISSING-OUTPUT."""
        rec = {
            "schema_version": 1,
            "kind": "tool_event",
            "seq": 0,
            "run_id": "run-12345678",
            "actor": "executor",
            "timestamp": "2026-08-22T10:00:00Z",
            "parent": "",
            "argv": ["pytest"],
            "cwd": "/repo",
            "exit_code": 0,
            "stdout_sha256": "",
        }
        res = evidence.validate_evidence(rec, require_full_output=True)
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "EV-MISSING-OUTPUT" for f in res.findings))

    def test_reject_fabricated_manual_text(self) -> None:
        """Fabricated manual text without captured tool event is rejected with EV-FABRICATED-TEXT."""
        not_a_record = "I ran pytest and all 50 tests passed successfully."
        res = evidence.validate_evidence(not_a_record)
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "EV-FABRICATED-TEXT" for f in res.findings))

        bogus_kind = {"kind": "manual_claim", "text": "everything is green"}
        res2 = evidence.validate_evidence(bogus_kind)
        self.assertFalse(res2.ok)
        self.assertTrue(any(f.code == "EV-FABRICATED-TEXT" for f in res2.findings))

    def test_reject_stale_head(self) -> None:
        """Evidence captured against an older commit HEAD is rejected with EV-STALE-HEAD."""
        env = {
            "schema_version": 1,
            "kind": "evidence_envelope",
            "seq": 1,
            "run_id": "run-12345678",
            "actor": "executor",
            "timestamp": "2026-08-22T10:00:00Z",
            "parent": "",
            "evidence_kind": "command",
            "binds": ["M-01"],
            "head": "oldcommit1234567890",
            "worktree": "/repo",
        }
        res = evidence.validate_evidence(env, expected_head="newcommit9999999999")
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "EV-STALE-HEAD" for f in res.findings))

    def test_reject_wrong_cwd(self) -> None:
        """Tool executed in wrong directory is rejected with EV-WRONG-CWD."""
        rec = {
            "schema_version": 1,
            "kind": "tool_event",
            "seq": 1,
            "run_id": "run-12345678",
            "actor": "executor",
            "timestamp": "2026-08-22T10:00:00Z",
            "parent": "",
            "argv": ["make", "test"],
            "cwd": "/wrong/dir",
            "exit_code": 0,
            "stdout_sha256": "e" * 64,
        }
        res = evidence.validate_evidence(rec, expected_cwd="/expected/dir")
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "EV-WRONG-CWD" for f in res.findings))

    def test_reject_wrong_worktree(self) -> None:
        """Evidence envelope in wrong worktree is rejected with EV-WRONG-WORKTREE."""
        env = {
            "schema_version": 1,
            "kind": "evidence_envelope",
            "seq": 1,
            "run_id": "run-12345678",
            "actor": "executor",
            "timestamp": "2026-08-22T10:00:00Z",
            "parent": "",
            "evidence_kind": "diff",
            "binds": ["M-01"],
            "head": "commit-1",
            "worktree": "/other/worktree",
        }
        res = evidence.validate_evidence(env, expected_worktree="/target/worktree")
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "EV-WRONG-WORKTREE" for f in res.findings))

    def test_reject_mismatched_command(self) -> None:
        """Captured command differing from expected command is rejected with EV-COMMAND-MISMATCH."""
        rec = {
            "schema_version": 1,
            "kind": "tool_event",
            "seq": 1,
            "run_id": "run-12345678",
            "actor": "executor",
            "timestamp": "2026-08-22T10:00:00Z",
            "parent": "",
            "argv": ["echo", "skipped-tests"],
            "cwd": "/repo",
            "exit_code": 0,
            "stdout_sha256": "e" * 64,
        }
        res = evidence.validate_evidence(rec, expected_command=["pytest", "-n", "auto"])
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "EV-COMMAND-MISMATCH" for f in res.findings))

    def test_reject_expired_host_probe(self) -> None:
        """Expired host probe timestamp beyond TTL is rejected with EV-EXPIRED-PROBE."""
        past_ts = "2026-08-20T00:00:00Z"
        current_dt = datetime.datetime.fromisoformat("2026-08-22T00:00:00+00:00")
        env = {
            "schema_version": 1,
            "kind": "evidence_envelope",
            "seq": 1,
            "run_id": "run-12345678",
            "actor": "executor",
            "timestamp": "2026-08-22T00:00:00Z",
            "parent": "",
            "evidence_kind": "inspection",
            "binds": ["V-01"],
            "head": "c1",
            "worktree": "/repo",
            "probe_timestamp": past_ts,
            "probe_ttl_seconds": 3600.0,
        }
        res = evidence.validate_evidence(env, current_time=current_dt)
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "EV-EXPIRED-PROBE" for f in res.findings))

    def test_reject_truncated_output(self) -> None:
        """Truncated required output is rejected with EV-TRUNCATED-OUTPUT."""
        rec = {
            "schema_version": 1,
            "kind": "tool_event",
            "seq": 1,
            "run_id": "run-12345678",
            "actor": "executor",
            "timestamp": "2026-08-22T10:00:00Z",
            "parent": "",
            "argv": ["pytest"],
            "cwd": "/repo",
            "exit_code": 0,
            "stdout_sha256": "e" * 64,
            "truncated": True,
        }
        res = evidence.validate_evidence(rec, require_full_output=True)
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "EV-TRUNCATED-OUTPUT" for f in res.findings))

    def test_reject_failed_exit_code(self) -> None:
        """Non-zero command exit code is rejected with EV-FAILED-EXIT."""
        rec = {
            "schema_version": 1,
            "kind": "tool_event",
            "seq": 1,
            "run_id": "run-12345678",
            "actor": "executor",
            "timestamp": "2026-08-22T10:00:00Z",
            "parent": "",
            "argv": ["pytest"],
            "cwd": "/repo",
            "exit_code": 1,
            "stdout_sha256": "e" * 64,
        }
        res = evidence.validate_evidence(rec)
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "EV-FAILED-EXIT" for f in res.findings))

    def test_reject_absent_artifact(self) -> None:
        """Missing artifact file on disk is rejected with EV-ABSENT-ARTIFACT."""
        art = {
            "schema_version": 1,
            "kind": "artifact_ref",
            "seq": 1,
            "run_id": "run-12345678",
            "actor": "executor",
            "timestamp": "2026-08-22T10:00:00Z",
            "parent": "",
            "path": "/nonexistent/path/artifact.json",
            "sha256": "a" * 64,
        }
        res = evidence.validate_evidence(art, check_filesystem=True)
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "EV-ABSENT-ARTIFACT" for f in res.findings))

    def test_reject_hash_mismatch(self) -> None:
        """Artifact content sha256 mismatch is rejected with EV-HASH-MISMATCH."""
        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            f.write("actual real content")
            tmp_path = f.name
        try:
            art = {
                "schema_version": 1,
                "kind": "artifact_ref",
                "seq": 1,
                "run_id": "run-12345678",
                "actor": "executor",
                "timestamp": "2026-08-22T10:00:00Z",
                "parent": "",
                "path": tmp_path,
                "sha256": "0" * 64,  # bogus hash
            }
            res = evidence.validate_evidence(art, check_filesystem=True)
            self.assertFalse(res.ok)
            self.assertTrue(any(f.code == "EV-HASH-MISMATCH" for f in res.findings))
        finally:
            os.unlink(tmp_path)

    def test_reject_executor_authored_verifier_decision(self) -> None:
        """Verifier decision authored by executor role is rejected with EV-EXECUTOR-VERIFIER."""
        dec = {
            "schema_version": 1,
            "kind": "verifier_decision",
            "seq": 1,
            "run_id": "run-12345678",
            "actor": "executor",
            "timestamp": "2026-08-22T10:00:00Z",
            "parent": "",
            "requirement": "M-01",
            "result": "satisfied",
        }
        res = evidence.validate_evidence(dec)
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "EV-EXECUTOR-VERIFIER" for f in res.findings))

    def test_reject_redaction_truncation_conflict(self) -> None:
        """Redaction that blocks verification fails closed with EV-REDACTION-CONFLICT."""
        env = {
            "schema_version": 1,
            "kind": "evidence_envelope",
            "seq": 1,
            "run_id": "run-12345678",
            "actor": "executor",
            "timestamp": "2026-08-22T10:00:00Z",
            "parent": "",
            "evidence_kind": "test_report",
            "binds": ["V-01"],
            "head": "c1",
            "worktree": "/repo",
            "redacted": True,
            "redaction_blocks_verification": True,
        }
        res = evidence.validate_evidence(env, require_full_output=True)
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "EV-REDACTION-CONFLICT" for f in res.findings))


# ==================================================================================================
# Task Group 3: Completion Predicates Truth-Table (E-03 / V-03)
# ==================================================================================================


class TestCompletionPredicates(unittest.TestCase):
    """V-03 / E-03: Completion is computed; toggling any single input false prevents completion."""

    def test_clean_complete_run_evaluates_true(self) -> None:
        """When all predicates hold, is_complete returns True."""
        records = _sample_run_records()
        evaluation = evidence.evaluate_completion(records, coordinator_authority=True)
        self.assertTrue(evaluation.is_complete)
        self.assertTrue(evidence.is_complete(records, coordinator_authority=True))
        self.assertEqual(len(evaluation.reasons), 0)

    def test_toggle_missing_requirement_verifier_decision_prevents_completion(
        self,
    ) -> None:
        """Missing verifier decision for a frozen requirement prevents completion."""
        records = _sample_run_records()
        # Remove verifier decision for V-01 (seq 6)
        records = [
            r
            for r in records
            if not (
                r.get("kind") == "verifier_decision" and r.get("requirement") == "V-01"
            )
        ]
        evaluation = evidence.evaluate_completion(records)
        self.assertFalse(evaluation.is_complete)
        self.assertFalse(evaluation.predicates["requirements_covered"].satisfied)
        self.assertTrue(any("V-01" in m for m in evaluation.missing_evidence))

    def test_toggle_unperformed_step_prevents_completion(self) -> None:
        """Step in state 'failed' or 'blocked' prevents completion."""
        records = _sample_run_records()
        # Change step S-01 to failed
        for r in records:
            if r.get("kind") == "step_attempt":
                r["state"] = "failed"
        evaluation = evidence.evaluate_completion(records)
        self.assertFalse(evaluation.is_complete)
        self.assertFalse(evaluation.predicates["steps_performed"].satisfied)

    def test_toggle_executor_self_verification_prevents_completion(self) -> None:
        """Verifier decision authored by executor role prevents completion."""
        records = _sample_run_records()
        for r in records:
            if r.get("kind") == "verifier_decision":
                r["actor"] = "executor"
        evaluation = evidence.evaluate_completion(records)
        self.assertFalse(evaluation.is_complete)
        self.assertFalse(evaluation.predicates["verifier_independent"].satisfied)

    def test_toggle_unresolved_failed_command_prevents_completion(self) -> None:
        """Failed tool event without subsequent success prevents completion."""
        records = _sample_run_records()
        for r in records:
            if r.get("kind") == "tool_event":
                r["exit_code"] = 1
        evaluation = evidence.evaluate_completion(records)
        self.assertFalse(evaluation.is_complete)
        self.assertFalse(evaluation.predicates["commands_green"].satisfied)

    def test_toggle_unresolved_correction_prevents_completion(self) -> None:
        """Correction logged without subsequent passing decision prevents completion."""
        records = _sample_run_records()
        # Add a correction at seq 7 for M-01 (after original decision at seq 5)
        cor = {
            "schema_version": schema.LEDGER_SCHEMA_VERSION,
            "kind": "correction",
            "seq": 7,
            "run_id": "run-abcdef1234",
            "actor": "corrector",
            "timestamp": "2026-08-22T10:00:07Z",
            "parent": "",
            "corrects_requirement": "M-01",
            "description": "Bug identified",
        }
        records.append(cor)
        evaluation = evidence.evaluate_completion(records)
        self.assertFalse(evaluation.is_complete)
        self.assertFalse(evaluation.predicates["no_blockers"].satisfied)

    def test_toggle_coordinator_authority_absent_prevents_completion(self) -> None:
        """Coordinator authority=False prevents completion even if all other predicates pass."""
        records = _sample_run_records()
        evaluation = evidence.evaluate_completion(records, coordinator_authority=False)
        self.assertFalse(evaluation.is_complete)
        self.assertFalse(evaluation.predicates["coordinator_authority"].satisfied)
        self.assertFalse(evidence.is_complete(records, coordinator_authority=False))

    def test_model_prose_cannot_flip_completion(self) -> None:
        """Arbitrary model text or non-conforming records evaluate to is_complete=False."""
        self.assertFalse(evidence.is_complete([]))
        self.assertFalse(
            evidence.is_complete(
                [{"prose": "I verified everything, status is complete"}]
            )
        )


# ==================================================================================================
# Task Group 4: Inspection CLI (E-04 / V-04)
# ==================================================================================================


class TestRunCLI(unittest.TestCase):
    """V-04 / E-04: aw run show|evidence|verify-ledger inspection commands."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ledger_path = Path(self.tmp_dir.name) / "events.jsonl"
        self.store = store.RunLedgerStore(self.ledger_path)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_aw_run_show_clean_complete_run(self) -> None:
        """aw run show on complete run exits 0 and reports COMPLETE."""
        records = _sample_run_records()
        for r in records:
            self.store.append(r)

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            exit_code = cli.main(["runs", "show", str(self.ledger_path)])
            out = mock_stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("Outcome: COMPLETE", out)
        self.assertIn("Run: run-abcdef1234", out)

    def test_aw_run_show_incomplete_run(self) -> None:
        """aw run show on incomplete run exits 1 and lists unsatisfied criteria."""
        records = _sample_run_records()
        # Remove verifier decisions
        for r in records[:5]:
            self.store.append(r)

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            exit_code = cli.main(["runs", "show", str(self.ledger_path)])
            out = mock_stdout.getvalue()

        self.assertEqual(exit_code, 1)
        self.assertIn("Outcome: INCOMPLETE", out)

    def test_aw_run_show_agent_json_mode(self) -> None:
        """aw run show --agent and --json emit valid JSON with NO ANSI."""
        records = _sample_run_records()
        for r in records:
            self.store.append(r)

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            exit_code = cli.main(["runs", "show", str(self.ledger_path), "--agent"])
            out = mock_stdout.getvalue().strip()

        self.assertEqual(exit_code, 0)
        self.assertNotIn("\x1b[", out)
        data = json.loads(out)
        self.assertTrue(data["is_complete"])
        self.assertEqual(data["run_id"], "run-abcdef1234")

    def test_aw_run_evidence_lists_and_validates(self) -> None:
        """aw run evidence lists envelopes and validates them."""
        records = _sample_run_records()
        for r in records:
            self.store.append(r)

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            exit_code = cli.main(["runs", "evidence", str(self.ledger_path)])
            out = mock_stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("[VALID] Seq 3 (tool_event)", out)
        self.assertIn("[VALID] Seq 4 (evidence_envelope)", out)

    def test_aw_run_verify_ledger_clean(self) -> None:
        """aw run verify-ledger exits 0 on clean ledger with valid evidence."""
        records = _sample_run_records()
        for r in records:
            self.store.append(r)

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            exit_code = cli.main(["runs", "verify-ledger", str(self.ledger_path)])
            out = mock_stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("Overall Status: PASS", out)

    def test_aw_run_verify_ledger_corrupted_chain_exits_2(self) -> None:
        """aw run verify-ledger exits 2 when hash chain is broken."""
        records = _sample_run_records()
        for r in records:
            self.store.append(r)

        # Mutate line 2
        lines = self.ledger_path.read_text(encoding="utf-8").splitlines(keepends=True)
        rec = json.loads(lines[1])
        rec["requirement_digest"] = "tampered"
        lines[1] = json.dumps(rec, sort_keys=True, separators=(",", ":")) + "\n"
        self.ledger_path.write_text("".join(lines), encoding="utf-8")

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            exit_code = cli.main(["runs", "verify-ledger", str(self.ledger_path)])
            out = mock_stdout.getvalue()

        self.assertEqual(exit_code, 2)
        self.assertIn("Broken chain", out)

    def test_aw_run_makes_no_writes_by_default(self) -> None:
        """aw run show|evidence|verify-ledger makes no filesystem modifications."""
        records = _sample_run_records()
        for r in records:
            self.store.append(r)

        before_bytes = self.ledger_path.read_bytes()
        cli.main(["runs", "show", str(self.ledger_path)])
        cli.main(["runs", "evidence", str(self.ledger_path)])
        cli.main(["runs", "verify-ledger", str(self.ledger_path)])
        after_bytes = self.ledger_path.read_bytes()

        self.assertEqual(before_bytes, after_bytes)


# ==================================================================================================
# Task Group 5: Adversarial Test Suite (E-05 / V-05)
# ==================================================================================================


class TestAdversarialSuite(unittest.TestCase):
    """V-05 / E-05: Adversarial deceptions fail closed with named reasons and intact ledger history."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ledger_path = Path(self.tmp_dir.name) / "events.jsonl"
        self.store = store.RunLedgerStore(self.ledger_path)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_adv_01_fabricated_success_text(self) -> None:
        """Adversary provides claimed success text without captured tool event -> Refused."""
        fake_records = [
            {
                "schema_version": 1,
                "kind": "run",
                "seq": 0,
                "run_id": "run-11112222",
                "actor": "runtime",
                "timestamp": "2026-08-22T10:00:00Z",
                "parent": "",
                "workflow_digest": "a" * 64,
                "requirement_digest": "b" * 64,
                "repo": "agent-workflows",
                "head": "head1",
            },
            {
                "schema_version": 1,
                "kind": "requirement_set",
                "seq": 1,
                "run_id": "run-11112222",
                "actor": "runtime",
                "timestamp": "2026-08-22T10:00:01Z",
                "parent": "",
                "requirement_digest": "b" * 64,
                "requirements": [
                    {
                        "id": "M-01",
                        "category": "must",
                        "digest": "c" * 64,
                        "text": "Do X",
                    }
                ],
                "scope_fence": {},
            },
        ]
        eval_res = evidence.evaluate_completion(fake_records)
        self.assertFalse(eval_res.is_complete)
        self.assertIn("unsatisfied requirements: ['M-01']", eval_res.reasons)

    def test_adv_02_checked_boxes_without_events(self) -> None:
        """Checked boxes in plan markdown without captured ledger events -> Incomplete."""
        empty_records = [
            {
                "schema_version": 1,
                "kind": "run",
                "seq": 0,
                "run_id": "run-11112222",
                "actor": "runtime",
                "timestamp": "2026-08-22T10:00:00Z",
                "parent": "",
                "workflow_digest": "a" * 64,
                "requirement_digest": "b" * 64,
                "repo": "agent-workflows",
                "head": "head1",
            }
        ]
        eval_res = evidence.evaluate_completion(empty_records)
        self.assertFalse(eval_res.is_complete)
        self.assertIn("no frozen requirements defined", eval_res.reasons)
        self.assertIn("no step attempts recorded", eval_res.reasons)

    def test_adv_03_green_targeted_tests_plus_red_full_suite(self) -> None:
        """Targeted test passes but full suite fails -> Completion predicate fails."""
        records = _sample_run_records()
        # Add targeted test tool event (exit 0) and full suite tool event (exit 1)
        targeted_tool = {
            "schema_version": 1,
            "kind": "tool_event",
            "seq": 7,
            "run_id": "run-abcdef1234",
            "actor": "executor",
            "timestamp": "2026-08-22T10:00:07Z",
            "parent": "",
            "argv": ["pytest", "tests/test_single.py"],
            "cwd": "/repo",
            "exit_code": 0,
            "stdout_sha256": "e" * 64,
        }
        full_tool = {
            "schema_version": 1,
            "kind": "tool_event",
            "seq": 8,
            "run_id": "run-abcdef1234",
            "actor": "executor",
            "timestamp": "2026-08-22T10:00:08Z",
            "parent": "",
            "argv": ["make", "test"],
            "cwd": "/repo",
            "exit_code": 1,
            "stdout_sha256": "f" * 64,
        }
        records.extend([targeted_tool, full_tool])
        eval_res = evidence.evaluate_completion(records)
        self.assertFalse(eval_res.is_complete)
        self.assertFalse(eval_res.predicates["commands_green"].satisfied)

    def test_adv_04_stale_evidence_rejected(self) -> None:
        """Evidence captured on commit c1 while expected HEAD is c2 -> Rejected."""
        records = _sample_run_records(head="commit_c1")
        eval_res = evidence.evaluate_completion(records, expected_head="commit_c2")
        self.assertFalse(eval_res.is_complete)
        self.assertFalse(eval_res.predicates["evidence_valid"].satisfied)
        self.assertTrue(any("EV-STALE-HEAD" in r for r in eval_res.reasons))

    def test_adv_05_test_deletion_or_weakening(self) -> None:
        """Test weakening by mismatching artifact content hash -> EV-HASH-MISMATCH."""
        art = {
            "schema_version": 1,
            "kind": "artifact_ref",
            "seq": 1,
            "run_id": "run-abcdef1234",
            "actor": "executor",
            "timestamp": "2026-08-22T10:00:00Z",
            "parent": "",
            "path": "tests/test_run.py",
            "sha256": "e" * 64,
        }
        res = evidence.validate_evidence(
            art,
            expected_file_content="def test_weakened(): pass\n",
            check_filesystem=False,
        )
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "EV-HASH-MISMATCH" for f in res.findings))

    def test_adv_06_mismatched_commit_worktree(self) -> None:
        """Evidence captured in mismatched worktree -> EV-WRONG-WORKTREE."""
        records = _sample_run_records(worktree="/worktree/alpha")
        eval_res = evidence.evaluate_completion(
            records, expected_worktree="/worktree/beta"
        )
        self.assertFalse(eval_res.is_complete)
        self.assertTrue(any("EV-WRONG-WORKTREE" in r for r in eval_res.reasons))

    def test_adv_07_replay_old_evidence_envelope(self) -> None:
        """Replaying evidence envelope with mismatched seq or previous hash breaks the chain."""
        records = _sample_run_records()
        for r in records:
            self.store.append(r)

        # Append duplicate replayed record
        replayed = copy.deepcopy(records[4])
        lines = self.ledger_path.read_text(encoding="utf-8").splitlines(keepends=True)
        lines.append(json.dumps(replayed, sort_keys=True, separators=(",", ":")) + "\n")
        self.ledger_path.write_text("".join(lines), encoding="utf-8")

        chain_ver = self.store.verify_chain()
        self.assertFalse(chain_ver.clean)

    def test_adv_08_ledger_corruption_fails_closed(self) -> None:
        """Tampered ledger record fails closed on read and verify."""
        records = _sample_run_records()
        for r in records:
            self.store.append(r)

        # Corrupt line 3
        lines = self.ledger_path.read_text(encoding="utf-8").splitlines(keepends=True)
        rec = json.loads(lines[3])
        rec["exit_code"] = 0
        rec["argv"] = ["tampered", "command"]
        lines[3] = json.dumps(rec, sort_keys=True, separators=(",", ":")) + "\n"
        self.ledger_path.write_text("".join(lines), encoding="utf-8")

        with self.assertRaises(store.LedgerCorruption):
            self.store.read_records(verify=True)

    def test_adv_09_interrupted_append_recovery(self) -> None:
        """Torn trailing append is truncated, prior history preserved, incomplete run stays incomplete."""
        records = _sample_run_records()[:4]
        for r in records:
            self.store.append(r)

        # Simulate crash: write partial line without newline
        with open(self.ledger_path, "ab") as f:
            f.write(
                b'{"schema_version": 1, "kind": "verifier_decision", "actor": "veri'
            )

        recov = self.store.recover()
        self.assertTrue(recov.recovered)
        self.assertEqual(len(self.store.read_records()), 4)

        eval_res = evidence.evaluate_completion(self.store.read_records())
        self.assertFalse(eval_res.is_complete)

    def test_adv_10_executor_verifier_identity_collision(self) -> None:
        """Executor cannot author verifier_decision; rejected at schema and validator gates."""
        bad_dec = {
            "schema_version": schema.LEDGER_SCHEMA_VERSION,
            "kind": "verifier_decision",
            "seq": 5,
            "run_id": "run-abcdef1234",
            "actor": "executor",
            "timestamp": "2026-08-22T10:00:05Z",
            "parent": "",
            "requirement": "M-01",
            "result": "satisfied",
        }
        val_schema = schema.validate_record(bad_dec)
        self.assertFalse(val_schema.ok)
        self.assertTrue(any(f.code == "RL-E032" for f in val_schema.findings))

        val_ev = evidence.validate_evidence(bad_dec)
        self.assertFalse(val_ev.ok)
        self.assertTrue(any(f.code == "EV-EXECUTOR-VERIFIER" for f in val_ev.findings))

    def test_adv_11_history_preservation_after_failed_attempt(self) -> None:
        """When a step fails and is subsequently retried, both attempts remain in ledger history."""
        r_run = _sample_run_records()[0]
        self.store.append(r_run)

        # Attempt 1: Failed
        att1 = {
            "schema_version": schema.LEDGER_SCHEMA_VERSION,
            "kind": "step_attempt",
            "run_id": "run-abcdef1234",
            "actor": "executor",
            "parent": "",
            "step": "S-01",
            "state": "failed",
            "attempt": 1,
        }
        self.store.append(att1)

        # Tool event 1: Failed
        tool1 = {
            "schema_version": schema.LEDGER_SCHEMA_VERSION,
            "kind": "tool_event",
            "run_id": "run-abcdef1234",
            "actor": "executor",
            "parent": "",
            "argv": ["pytest", "tests/test_x.py"],
            "cwd": "/repo",
            "exit_code": 1,
            "stdout_sha256": "f" * 64,
        }
        self.store.append(tool1)

        # Retry event
        retry = {
            "schema_version": schema.LEDGER_SCHEMA_VERSION,
            "kind": "retry",
            "run_id": "run-abcdef1234",
            "actor": "executor",
            "parent": "",
            "retries_step": "S-01",
            "failure_class": "assertion_error",
            "idempotency_key": "k1",
        }
        self.store.append(retry)

        # Attempt 2: Performed
        att2 = {
            "schema_version": schema.LEDGER_SCHEMA_VERSION,
            "kind": "step_attempt",
            "run_id": "run-abcdef1234",
            "actor": "executor",
            "parent": "",
            "step": "S-01",
            "state": "performed",
            "attempt": 2,
        }
        self.store.append(att2)

        # Tool event 2: Success
        tool2 = {
            "schema_version": schema.LEDGER_SCHEMA_VERSION,
            "kind": "tool_event",
            "run_id": "run-abcdef1234",
            "actor": "executor",
            "parent": "",
            "argv": ["pytest", "tests/test_x.py"],
            "cwd": "/repo",
            "exit_code": 0,
            "stdout_sha256": "e" * 64,
        }
        self.store.append(tool2)

        # Read back all records: all 6 records are preserved in history
        history = self.store.read_records()
        self.assertEqual(len(history), 6)
        self.assertEqual(history[1]["state"], "failed")
        self.assertEqual(history[2]["exit_code"], 1)
        self.assertEqual(history[4]["state"], "performed")
        self.assertEqual(history[5]["exit_code"], 0)


# ==================================================================================================
# runcodes Order 1 (`wlxkoz`) E-03 / V-03: the `RUN-*` finding-code vocabulary
# ==================================================================================================


_SPEC_PATH = (
    Path(__file__).resolve().parents[1]
    / ".aw"
    / "records"
    / "specs"
    / "20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md"
)


def _parse_spec_run_code_table() -> Dict[str, Dict[str, str]]:
    """Parse spec `25kzda` 4.2's table straight out of the SPEC FILE.

    THE POINT OF PARSING RATHER THAN HARDCODING: the only defect this vocabulary can realistically
    ship is a transcription error, and an expectation copied from the implementation cannot detect
    one. These tests therefore compare the module against the spec's own bytes, so REWORDING either
    side fails. Returns ``{code: {"message": ..., "action": ...}}`` with the surrounding backticks
    stripped, since the backticks are Markdown, not part of the operator-facing string.
    """
    rows: Dict[str, Dict[str, str]] = {}
    for line in _SPEC_PATH.read_text(encoding="utf-8").split("\n"):
        stripped = line.strip()
        if not stripped.startswith("| `RUN-"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split(" | ")]
        if len(cells) != 5:
            continue
        code = cells[0].strip("`")
        rows[code] = {
            "inspects": cells[1],
            "pass_criterion": cells[2],
            "message": cells[3].strip("`"),
            "action": cells[4],
        }
    return rows


def _parse_spec_abort_classes() -> List[str]:
    """Parse spec 4.1's EXHAUSTIVE six-row abort-class table out of the spec file."""
    text = _SPEC_PATH.read_text(encoding="utf-8")
    start = text.index("#### Exhaustive `ABORT RUN` set")
    end = text.index("#### Failed-item containment transaction", start)
    classes: List[str] = []
    for line in text[start:end].split("\n"):
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("| ---"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split(" | ")]
        if len(cells) != 2 or cells[0] == "Abort class":
            continue
        classes.append(cells[0])
    return classes


class TestRunFindingCodeVocabulary(unittest.TestCase):
    """E-01 / E-02 / V-01 / V-02: the 13 `RUN-*` codes, their verbatim text, and their bindings."""

    def setUp(self) -> None:
        if not _SPEC_PATH.exists():  # pragma: no cover - installed-package layout
            self.skipTest(f"spec 25kzda not present at {_SPEC_PATH}")
        self.spec_rows = _parse_spec_run_code_table()

    # ---- E-01: the codes exist as data, transcribed verbatim -------------------------------------

    def test_spec_defines_exactly_thirteen_run_codes(self) -> None:
        """Guard the guard: if the SPEC's own table stops having 13 rows, every other case is moot."""
        self.assertEqual(
            len(self.spec_rows),
            13,
            f"spec 4.2 should define 13 RUN-* codes, parsed {sorted(self.spec_rows)}",
        )

    def test_table_enumerates_exactly_the_specs_thirteen_codes(self) -> None:
        self.assertEqual(len(evidence.RUN_FINDING_CODES), 13)
        self.assertEqual(
            sorted(evidence.run_finding_codes()),
            sorted(self.spec_rows),
        )

    def test_every_message_is_verbatim_from_the_spec(self) -> None:
        """A reworded message FAILS here (V-03's non-vacuity requirement)."""
        for code, spec_row in sorted(self.spec_rows.items()):
            with self.subTest(code=code):
                self.assertEqual(
                    evidence.RUN_FINDING_CODES_BY_CODE[code].message,
                    spec_row["message"],
                    f"{code} message is not a verbatim transcription of spec 4.2",
                )

    def test_every_message_carries_the_specs_recovery_command(self) -> None:
        """Spec 4.1: 'Every recovery message ends with a command'."""
        for code, spec_row in sorted(self.spec_rows.items()):
            with self.subTest(code=code):
                recovery = spec_row["message"].rsplit(": ", 1)[-1]
                self.assertTrue(
                    recovery.startswith("aw "),
                    f"{code} spec message does not end in an `aw` command: {recovery!r}",
                )
                self.assertTrue(
                    evidence.RUN_FINDING_CODES_BY_CODE[code].message.endswith(recovery),
                    f"{code} dropped or altered the spec's recovery command",
                )

    def test_every_failure_action_is_verbatim_from_the_spec(self) -> None:
        for code, spec_row in sorted(self.spec_rows.items()):
            with self.subTest(code=code):
                self.assertEqual(
                    evidence.RUN_FINDING_CODES_BY_CODE[code].action,
                    spec_row["action"],
                    f"{code} failure action is not verbatim from spec 4.2",
                )

    def test_inspects_and_pass_criterion_are_verbatim_from_the_spec(self) -> None:
        for code, spec_row in sorted(self.spec_rows.items()):
            with self.subTest(code=code):
                row = evidence.RUN_FINDING_CODES_BY_CODE[code]
                self.assertEqual(row.inspects, spec_row["inspects"])
                self.assertEqual(row.pass_criterion, spec_row["pass_criterion"])

    def test_placeholder_substitution_preserves_the_rest_of_the_message(self) -> None:
        rendered = evidence.spec_message_for(
            "RUN-LEDGER-INTEGRITY", run_id="run-abcdef1234", record="seq=7"
        )
        self.assertIn("run-abcdef1234", rendered)
        self.assertIn("seq=7", rendered)
        self.assertNotIn("<run-id>", rendered)
        self.assertNotIn("<record>", rendered)
        # The recovery command survives substitution.
        self.assertTrue(rendered.endswith("aw runs verify run-abcdef1234"))

    def test_unrendered_message_equals_the_spec_template(self) -> None:
        for code in evidence.run_finding_codes():
            with self.subTest(code=code):
                self.assertEqual(
                    evidence.spec_message_for(code), self.spec_rows[code]["message"]
                )

    def test_unknown_code_raises_rather_than_returning_a_plausible_string(self) -> None:
        with self.assertRaises(KeyError):
            evidence.spec_message_for("RUN-NOT-A-REAL-CODE")

    # ---- spec 4.1: the abort set is EXHAUSTIVE ---------------------------------------------------

    def test_abort_class_set_is_verbatim_from_spec_4_1(self) -> None:
        self.assertEqual(list(evidence.ABORT_CLASSES), _parse_spec_abort_classes())
        self.assertEqual(len(evidence.ABORT_CLASSES), 6)

    def test_no_code_aborts_outside_the_six_enumerated_classes(self) -> None:
        """Spec 4.1: 'No other finding may abort the whole queue'."""
        for row in evidence.RUN_FINDING_CODES:
            with self.subTest(code=row.code):
                for cls in row.abort_classes:
                    self.assertIn(cls, evidence.ABORT_CLASSES)
                if row.abort == evidence.ABORT_NEVER:
                    self.assertEqual(row.abort_classes, ())
                    self.assertFalse(evidence.may_abort_run(row.code))
                else:
                    self.assertTrue(row.abort_classes)
                    self.assertTrue(evidence.may_abort_run(row.code))

    def test_abort_tristate_agrees_with_the_specs_action_text(self) -> None:
        """The tri-state is an INDEX over the verbatim action, so it must be derivable from it."""
        for code, spec_row in sorted(self.spec_rows.items()):
            with self.subTest(code=code):
                action = spec_row["action"]
                row = evidence.RUN_FINDING_CODES_BY_CODE[code]
                if "ABORT RUN" not in action:
                    expected = evidence.ABORT_NEVER
                elif action.strip() == "ABORT RUN":
                    expected = evidence.ABORT_ALWAYS
                else:
                    expected = evidence.ABORT_CONDITIONAL
                self.assertEqual(row.abort, expected, f"{code}: action was {action!r}")

    def test_conditional_abort_is_not_reported_as_unconditional(self) -> None:
        """The specific harm F4 names: an item-local fault must not license aborting the queue."""
        conditional = [
            r.code
            for r in evidence.RUN_FINDING_CODES
            if r.abort == evidence.ABORT_CONDITIONAL
        ]
        self.assertTrue(conditional)
        for code in conditional:
            with self.subTest(code=code):
                # `may_abort_run` is True, but the caller is told WHICH class is required.
                self.assertTrue(evidence.may_abort_run(code))
                self.assertTrue(evidence.abort_classes_for(code))
                self.assertNotEqual(
                    evidence.RUN_FINDING_CODES_BY_CODE[code].abort,
                    evidence.ABORT_ALWAYS,
                )
        always = [
            r.code
            for r in evidence.RUN_FINDING_CODES
            if r.abort == evidence.ABORT_ALWAYS
        ]
        self.assertEqual(
            sorted(always), ["RUN-BASELINE-OWNERSHIP", "RUN-LEDGER-INTEGRITY"]
        )

    # ---- E-02: the bindings, re-measured rather than trusted -------------------------------------

    def test_table_self_validation_passes(self) -> None:
        result = evidence.validate_finding_table()
        self.assertTrue(result.ok, f"table invariants violated: {result.findings}")
        self.assertEqual(result.findings, ())

    def test_every_code_records_a_known_binding_state(self) -> None:
        for row in evidence.RUN_FINDING_CODES:
            with self.subTest(code=row.code):
                self.assertIn(row.binding, evidence.BINDING_STATES)

    def test_every_bound_codes_predicate_actually_resolves(self) -> None:
        """The anti-rot check: if a shipped predicate is renamed or removed, this FAILS.

        A code whose recorded predicate no longer exists is a mapping that has silently rotted, which
        is indistinguishable at runtime from a check that never ran.
        """
        import importlib
        import re as _re

        for row in evidence.RUN_FINDING_CODES:
            if row.binding != evidence.BOUND:
                continue
            for dotted in row.predicates:
                with self.subTest(code=row.code, predicate=dotted):
                    base = _re.sub(r"\[.*\]$", "", dotted)
                    module_name, _, attr_path = base.partition(".")
                    module = importlib.import_module(f"agent_workflows.{module_name}")
                    obj: Any = module
                    for part in attr_path.split("."):
                        obj = getattr(obj, part, None)
                        self.assertIsNotNone(
                            obj, f"{dotted} no longer resolves; the binding has rotted"
                        )

    def test_unbound_codes_claim_no_predicate_and_name_what_they_wait_on(self) -> None:
        unbound = evidence.unbound_run_finding_codes()
        self.assertTrue(unbound, "at least one code is honestly unbound")
        for code in unbound:
            with self.subTest(code=code):
                row = evidence.RUN_FINDING_CODES_BY_CODE[code]
                self.assertEqual(row.predicates, ())
                self.assertTrue(row.waiting_on.strip())

    def test_measured_binding_partition_is_recorded(self) -> None:
        """The measured 2026-09-05 partition, pinned so a silent change is visible in review.

        Not a claim that these bindings are eternal: it is a claim that CHANGING one is a deliberate,
        reviewed act rather than a drive-by edit. `wlxkoz` finding F3 recorded 9/2/2 at an earlier
        HEAD; re-measurement after `mjx7ne`, `m73aet`, and `m2wwns` executed gives 10/2/1.
        """
        self.assertEqual(
            sorted(evidence.bound_run_finding_codes()),
            [
                "RUN-BASELINE-OWNERSHIP",
                "RUN-CHECK-FRESHNESS",
                "RUN-CROSS-TREE",
                "RUN-FRESH-VERIFIER",
                "RUN-FROZEN-IDENTITY",
                "RUN-HOST-ATTEMPT",
                "RUN-HOST-CAPABILITY",
                "RUN-LEDGER-INTEGRITY",
                "RUN-SCOPE-DELTA",
                "RUN-STRUCTURE-PREFLIGHT",
            ],
        )
        by_dependency = [
            r.code
            for r in evidence.RUN_FINDING_CODES
            if r.binding == evidence.UNBOUND_BY_DEPENDENCY
        ]
        unbuilt = [
            r.code
            for r in evidence.RUN_FINDING_CODES
            if r.binding == evidence.UNBOUND_UNBUILT
        ]
        self.assertEqual(
            sorted(by_dependency), ["RUN-COMMIT-CONTENTS", "RUN-COMMIT-GATEWAY"]
        )
        self.assertEqual(unbuilt, ["RUN-NO-PUSH"])

    def test_host_capability_binding_agrees_with_the_shipped_implementation(
        self,
    ) -> None:
        """`RUN-HOST-CAPABILITY` is BOUND only because `mjx7ne` shipped it; prove it still does."""
        from agent_workflows import host_sandbox_profile as hsp

        self.assertEqual(hsp.RUN_HOST_CAPABILITY, "RUN-HOST-CAPABILITY")
        rendered = hsp.format_host_capability_finding(
            host="<host>",
            capability="<capability>",
            item="<item>",
            action="<action>",
            selector="<selector>",
        )
        self.assertEqual(rendered, self.spec_rows["RUN-HOST-CAPABILITY"]["message"])
        # And the vocabulary's own template agrees with that shipped one, so the two cannot drift.
        self.assertEqual(
            evidence.spec_message_for("RUN-HOST-CAPABILITY"),
            rendered,
        )

    def test_no_shipped_ev_code_was_renamed_into_the_new_table(self) -> None:
        """`wlxkoz` must not disturb the shipped `EV-*` taxonomy it merely cites as bindings."""
        result = evidence.validate_evidence({"kind": "not-a-real-kind"})
        self.assertFalse(result.ok)
        self.assertEqual(
            [f.code for f in result.findings],
            ["EV-FABRICATED-TEXT"],
        )
        for row in evidence.RUN_FINDING_CODES:
            with self.subTest(code=row.code):
                self.assertFalse(row.code.startswith("EV-"))

    def test_vocabulary_decides_no_completion(self) -> None:
        """The vocabulary is a NAMING layer: it must not become a second completion authority."""
        records = _sample_run_records()
        self.assertTrue(evidence.is_complete(records))
        # Nothing in the vocabulary participates in that verdict.
        evaluation = evidence.evaluate_completion(records)
        for code in evidence.run_finding_codes():
            self.assertNotIn(code, evaluation.predicates)


if __name__ == "__main__":
    unittest.main()
