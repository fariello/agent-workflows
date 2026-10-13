"""Outcome tests for case-insensitive sensitive key matching in RedactionPolicy.

Covers IPD pbl020 (backlog go20fk):
- Case-insensitive sensitive key matching on both configured and payload keys
- Preserves original payload key spellings in redacted dicts
- Handles nested dicts, list of dicts, and list values under sensitive keys
- Ignores non-string keys (e.g. int) without raising
- End-to-end ledger integration test ensuring secrets are masked before persistence
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from agent_workflows import security_hardening
from agent_workflows.run_ledger_store import RedactionPolicy, RunLedgerStore


class RedactionKeyCasefoldTests(unittest.TestCase):
    """Outcome tests for case-insensitive sensitive key matching in RedactionPolicy."""

    def test_default_policy_redacts_mixed_case_sensitive_keys(self) -> None:
        """Call security_hardening.default_redaction_policy().redact on payloads keyed TOKEN, Authorization, Api_Key."""
        policy = security_hardening.default_redaction_policy()
        payload = {
            "TOKEN": "tok123",
            "Authorization": "Bearer auth123",
            "Api_Key": "key123",
        }
        redacted, was_redacted = policy.redact(payload)
        self.assertTrue(was_redacted)
        self.assertEqual(redacted["TOKEN"], policy.mask)
        self.assertEqual(redacted["Authorization"], policy.mask)
        self.assertEqual(redacted["Api_Key"], policy.mask)
        # Original key spellings are preserved
        self.assertIn("TOKEN", redacted)
        self.assertIn("Authorization", redacted)
        self.assertIn("Api_Key", redacted)

    def test_nested_mixed_case_sensitive_keys(self) -> None:
        """Nested dict with {'outer': {'PASSWORD': ...}} is redacted."""
        policy = security_hardening.default_redaction_policy()
        payload = {"outer": {"PASSWORD": "pwd123"}}
        redacted, was_redacted = policy.redact(payload)
        self.assertTrue(was_redacted)
        self.assertEqual(redacted["outer"]["PASSWORD"], policy.mask)
        self.assertIn("PASSWORD", redacted["outer"])

    def test_list_nested_mixed_case_sensitive_keys(self) -> None:
        """List with {'items': [{'Secret': ...}]} is redacted."""
        policy = security_hardening.default_redaction_policy()
        payload = {"items": [{"Secret": "sec123"}]}
        redacted, was_redacted = policy.redact(payload)
        self.assertTrue(was_redacted)
        self.assertEqual(redacted["items"][0]["Secret"], policy.mask)
        self.assertIn("Secret", redacted["items"][0])

    def test_mixed_case_key_with_list_value_masked_whole(self) -> None:
        """A list value under a mixed-case sensitive key ({'Token': ['a', 'b']}) is masked whole."""
        policy = security_hardening.default_redaction_policy()
        payload = {"Token": ["a", "b"]}
        redacted, was_redacted = policy.redact(payload)
        self.assertTrue(was_redacted)
        self.assertEqual(redacted["Token"], policy.mask)
        self.assertIn("Token", redacted)

    def test_uppercase_configured_key_masks_lowercase_payload_key(self) -> None:
        """A policy constructed with uppercase configured key masks lowercase payload key."""
        policy = RedactionPolicy(sensitive_keys=["X-Api-Key"])
        payload = {"x-api-key": "xkey123"}
        redacted, was_redacted = policy.redact(payload)
        self.assertTrue(was_redacted)
        self.assertEqual(redacted["x-api-key"], policy.mask)
        self.assertIn("x-api-key", redacted)

    def test_lowercase_control_passes(self) -> None:
        """Lowercase sensitive keys continue to be masked."""
        policy = security_hardening.default_redaction_policy()
        payload = {"token": "tok123", "authorization": "auth123"}
        redacted, was_redacted = policy.redact(payload)
        self.assertTrue(was_redacted)
        self.assertEqual(redacted["token"], policy.mask)
        self.assertEqual(redacted["authorization"], policy.mask)

    def test_non_sensitive_key_untouched(self) -> None:
        """Non-sensitive key (stdout) is untouched."""
        policy = security_hardening.default_redaction_policy()
        payload = {"stdout": "unaltered command output"}
        redacted, was_redacted = policy.redact(payload)
        self.assertFalse(was_redacted)
        self.assertEqual(redacted["stdout"], "unaltered command output")

    def test_non_string_int_payload_key_untouched_and_does_not_raise(self) -> None:
        """Payload with an int key ({3: 'v'}) is returned unchanged without raising."""
        policy = security_hardening.default_redaction_policy()
        payload = {3: "v"}
        redacted, was_redacted = policy.redact(payload)
        self.assertFalse(was_redacted)
        self.assertEqual(redacted[3], "v")

    def test_end_to_end_ledger_redacts_mixed_case_authorization(self) -> None:
        """E-05: RunLedgerStore in tmp_path with default_redaction_policy masks mixed-case key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.jsonl"
            policy = security_hardening.default_redaction_policy()
            store = RunLedgerStore(ledger_path, redaction_policy=policy)

            seed = {
                "schema_version": 2,
                "kind": "run",
                "run_id": "run-abc123ff",
                "actor": "executor",
                "parent": "",
                "workflow_digest": "0" * 64,
                "requirement_digest": "1" * 64,
                "repo": "test-repo",
                "head": "a" * 40,
                "Authorization": "Bearer s3cr3t",
            }
            store.append(seed)

            # Assert the ledger file text does not contain s3cr3t
            ledger_text = ledger_path.read_text(encoding="utf-8")
            self.assertNotIn(
                "s3cr3t",
                ledger_text,
                f"Ledger file leaked raw secret: {ledger_text}",
            )

            # read_records() shows the mask
            records = store.read_records()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["Authorization"], policy.mask)
            self.assertTrue(records[0].get("redacted"))
