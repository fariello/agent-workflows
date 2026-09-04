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


if __name__ == "__main__":
    unittest.main()
