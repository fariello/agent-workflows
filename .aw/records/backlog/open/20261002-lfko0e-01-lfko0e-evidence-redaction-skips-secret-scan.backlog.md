- Id: lfko0e
- Status: open
- Set: lfko0e
- Priority: medium
- Work-Kind: security
- Summary: check_evidence_redaction and host_runner.run_task admit a credential in worker stdout: stage 2 runs only the leak sanitizer, never the secret scanner

## Workflow history
- 2026-10-02 created (aw backlog): filed from /plan-review of gqyold (finding PR-003)

Measured 2026-10-02 at lane HEAD 76faafbc2 during /plan-review of plan gqyold.

agent_workflows/security_hardening.py check_evidence_redaction's docstring says evidence 'MUST NOT leak secrets/identifiers' and the module docstring says it 'passes the canonical leak/secret scanners'; docs/security.md boundary 4 says 'if a secret survives, it fails closed'. Stage 2 only calls leak_sanitizer.scan_text, which detects IDENTIFYING info (home-path, handle), not credentials. scan_text_for_secrets is never consulted.

Probe (AWS-shaped value built from char codes so this file holds no literal):
  s = 'aws_secret_access_key = ' + AKIA + 'IOSFODNN7EXAMPLE' + AKIA + 'IOSFODNN7'
  check_evidence_redaction({'stdout': s}).ok -> True, evidence {'redacted': False}
  scan_text_for_secrets(s) -> ['generic-secret-env']
  host_runner.run_task(packet, runner=lambda a,c,t: (0, s, ''), diff_capturer=...) -> worker_state 'completed', envelope status 'performed', stdout admitted verbatim.
  redact_worker_output(RawWorkerResult(stdout='Authorization: Bearer abc123', ...)) -> ok True, stdout unchanged: the payload keys are always stdout/stderr/diff, none sensitive, and default_redaction_policy has no value patterns, so redact_worker_output can never mask anything.

Not fixed in gqyold because wiring the entropy+PII secret scanner into worker-output admission carries a real false-positive risk (a task failing as a leak on innocuous high-entropy output) and is a design decision: which scanner rules gate admission, and whether to mask or refuse. run_task has no production caller today, which is why this is medium and not high. gqyold pins the current behavior so the change is visible.
