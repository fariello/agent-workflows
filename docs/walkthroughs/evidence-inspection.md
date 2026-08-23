# Walkthrough: inspect evidence

Goal: from a clean state, inspect a run's provenance evidence and verify its integrity.

## Steps

1. List the captured evidence envelopes and tool events for a run:

   ```
   aw run evidence <run-id-or-path>
   ```

   Each envelope records what tool ran, what it produced, and which artifacts it references.
   Secret-bearing environment keys are filtered, so they never appear verbatim.

2. Verify the ledger hash chain and the evidence validity:

   ```
   aw run verify-ledger <run-id-or-path>
   ```

   A clean result means every record is chained by SHA-256 to the previous one with no gap and
   no unparseable line, and no required verification payload was redacted in a way that blocks
   the check.

## Expected result

You can confirm, without reading implementation internals, that the recorded evidence is intact
and that no secret leaked into it.

## Reproduce the redaction boundary in a fixture

The evidence-redaction boundary (redact, then scan with the canonical leak sanitizer) is
deterministic. Drive it directly:

```
python3 -c "from agent_workflows import security_hardening as s; \
r = s.check_evidence_redaction({'authorization': 'Bearer sk-secret', 'stdout': 'ok'}); \
print('boundary holds:', r.ok, '|', r.reason)"
```

The sensitive key is masked before the payload lands, and the redacted text passes the
canonical leak sanitizer.
