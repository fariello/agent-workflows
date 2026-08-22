"""Tests for agent_workflows.run_ledger_schema (awoptimize Order 02 E-06, validates E-01..E-03).

Covers: a round-trip conforming fixture per record kind; schema-version rejection; per-kind field
omission/wrong-type rejection; the int-vs-bool guard; and each anti-false-completion state rule
(RL-E032, RL-E035, RL-E040, RL-E041) rejected with its stable code.
"""

import unittest

from agent_workflows import run_ledger_schema as S


def _envelope(kind, actor="runtime", seq=0, parent=""):
    return {
        "schema_version": S.LEDGER_SCHEMA_VERSION,
        "kind": kind,
        "seq": seq,
        "run_id": "run-deadbeef",
        "actor": actor,
        "timestamp": "2026-08-22T00:00:00Z",
        "parent": parent,
    }


_SHA = "a" * 64


def _fixture(kind):
    """A minimal conforming record for each of the 12 kinds."""
    rec = _envelope(kind)
    extras = {
        "run": {
            "workflow_digest": _SHA,
            "requirement_digest": _SHA,
            "repo": "agent-workflows",
            "head": "abc123",
        },
        "requirement_set": {
            "requirement_digest": _SHA,
            "requirements": [],
            "scope_fence": {},
        },
        "requirement_revision": {
            "prev_digest": _SHA,
            "new_digest": "b" * 64,
            "reason": "meaning changed",
        },
        "step_attempt": {"step": "S-01", "state": "performed", "attempt": 1},
        "tool_event": {
            "argv": ["pytest"],
            "cwd": ".",
            "exit_code": 0,
            "stdout_sha256": _SHA,
        },
        "evidence_envelope": {
            "evidence_kind": "test_report",
            "binds": ["R-01"],
            "head": "abc123",
            "worktree": "clean",
        },
        "artifact_ref": {"path": "dist/x.whl", "sha256": _SHA},
        "verifier_decision": {"requirement": "R-01", "result": "satisfied"},
        "correction": {"corrects_requirement": "R-01", "description": "fixed"},
        "retry": {
            "retries_step": "S-01",
            "failure_class": "flaky",
            "idempotency_key": "k1",
        },
        "human_approval": {"gate": "pre-execution", "approver": "Gabriele Fariello"},
        "terminal_transaction": {
            "terminal_status": "executed",
            "moved_to": "executed/",
        },
    }[kind]
    rec.update(extras)
    # verifier_decision must be authored by the verifier role.
    if kind == "verifier_decision":
        rec["actor"] = "verifier"
    return rec


class RoundTripPerKindTest(unittest.TestCase):
    def test_every_kind_has_a_conforming_fixture(self):
        self.assertEqual(len(S.RECORD_KINDS), 12)
        for kind in sorted(S.RECORD_KINDS):
            res = S.validate_record(_fixture(kind))
            self.assertTrue(
                res.ok, msg="{0} should validate: {1}".format(kind, res.findings)
            )


class SchemaVersionTest(unittest.TestCase):
    def test_unsupported_schema_version_rejected(self):
        rec = _fixture("run")
        rec["schema_version"] = 999
        res = S.validate_record(rec)
        self.assertFalse(res.ok)
        self.assertIn("RL-E012", {f.code for f in res.findings})


class PerKindFieldTest(unittest.TestCase):
    def test_missing_per_kind_field_named_and_coded(self):
        rec = _fixture("tool_event")
        del rec["exit_code"]
        res = S.validate_record(rec)
        self.assertFalse(res.ok)
        f = [x for x in res.findings if x.code == "RL-E020"]
        self.assertTrue(f)
        self.assertEqual(f[0].where, "exit_code")

    def test_wrong_typed_per_kind_field_rejected(self):
        rec = _fixture("tool_event")
        rec["exit_code"] = "0"  # str, not int
        res = S.validate_record(rec)
        self.assertFalse(res.ok)
        self.assertIn("RL-E021", {f.code for f in res.findings})

    def test_bool_is_not_accepted_where_int_required(self):
        rec = _fixture("tool_event")
        rec["exit_code"] = True  # bool must not satisfy int
        res = S.validate_record(rec)
        self.assertFalse(res.ok)
        self.assertIn("RL-E021", {f.code for f in res.findings})


class StateRuleTest(unittest.TestCase):
    def test_RL_E032_executor_authored_verifier_decision_rejected(self):
        rec = _fixture("verifier_decision")
        rec["actor"] = "executor"
        res = S.validate_record(rec)
        self.assertFalse(res.ok)
        self.assertIn("RL-E032", {f.code for f in res.findings})

    def test_RL_E035_executor_authored_terminal_transaction_rejected(self):
        rec = _fixture("terminal_transaction")
        rec["actor"] = "executor"
        res = S.validate_record(rec)
        self.assertFalse(res.ok)
        self.assertIn("RL-E035", {f.code for f in res.findings})

    def test_RL_E040_non_increasing_seq_rejected(self):
        run = _fixture("run")
        run["seq"] = 0
        step = _fixture("step_attempt")
        step["seq"] = 0  # not strictly increasing
        res = S.validate_records([run, step])
        self.assertFalse(res.ok)
        self.assertIn("RL-E040", {f.code for f in res.findings})

    def test_RL_E041_first_record_not_run_rejected(self):
        step = _fixture("step_attempt")
        step["seq"] = 0
        res = S.validate_records([step])
        self.assertFalse(res.ok)
        self.assertIn("RL-E041", {f.code for f in res.findings})

    def test_valid_sequence_accepted(self):
        run = _fixture("run")
        run["seq"] = 0
        step = _fixture("step_attempt")
        step["seq"] = 1
        res = S.validate_records([run, step])
        self.assertTrue(res.ok, msg=str(res.findings))


if __name__ == "__main__":
    unittest.main()
