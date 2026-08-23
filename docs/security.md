# Security

This document describes the hardened security boundaries of the execution runtime and host
integration, and the runbooks that prove each one. The checkers live in
`agent_workflows/security_hardening.py`; the threat-model tests are in
`tests/test_security_hardening.py`.

Leak and secret checks REUSE the repository's canonical tooling. There is no forked scanner:

- The leak sanitizer is `aw sanitize` (alias `aw check-local-leaks`), backed by
  `agent_workflows/leak_sanitizer.py`.
- The secret scanner is `.aw/system/workflows/assess/tools/scan_secrets.py`.

## The boundaries

1. Local servers bind loopback and require auth. `check_local_server_binding` refuses a bind to
   a routable address and refuses an unauthenticated loopback endpoint. A local headless server
   may be unauthenticated by default on some hosts; the integration must bind 127.0.0.1 (or ::1)
   AND require a token.
2. External files are consented and contained. `check_external_file_access` refuses an access
   with no explicit consent and refuses a path that escapes the consented base (it reuses the
   containment guard `host_capability_registry.assert_contained`).
3. Skills are least privilege. `check_skill_least_privilege` refuses a skill entry point that
   inlines the canonical authoritative body or fails package validation.
4. Evidence is redacted. `check_evidence_redaction` applies the ledger redaction policy and then
   runs the CANONICAL leak sanitizer over the redacted text; if a secret survives, it fails
   closed.
5. The real HOME is excluded from probes. `check_real_home_excluded` reuses
   `assert_isolated_base`, which refuses a base equal to or containing the real home.
6. Untrusted text is isolated as data. `check_untrusted_text_isolated` refuses any path that
   executed untrusted repository, tool, or inter-agent text as instructions; it still reads the
   text safely as data and flags an injection attempt.
7. Destructive tools are human-gated. `check_destructive_tool_gated` refuses a destructive tool
   without a genuine human consent, and refuses a non-human role that claims to consent (only
   the human role can record approval; a role cannot synthesize its own consent).

## Runbooks (how to prove each boundary)

Run the whole threat-model suite:

```
python3 -m pytest tests/test_security_hardening.py -q
```

Run the canonical leak scan over the tracked tree (exit 0 means clean):

```
aw sanitize --agent
```

Run the canonical secret scanner over the working tree:

```
python3 .aw/system/workflows/assess/tools/scan_secrets.py .
```

## Responsibility boundary

The tool enforces the boundaries deterministically and fails closed. The agent operates inside
them. Only the human consents to a destructive action; the agent cannot self-authorize one.

## Limitations

- The untrusted-text classifier flags known injection markers; it is a defense-in-depth signal,
  not a guarantee that all injection is detected. The primary control is that untrusted text is
  always handled as data, never executed as instructions.
