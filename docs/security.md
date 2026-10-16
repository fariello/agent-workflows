# Security

This document describes the hardened security boundaries of the execution runtime and host
integration, and the runbooks that prove each one. The checkers live in
`agent_workflows/security_hardening.py` and are covered by dedicated threat-model tests in
`tests/test_security_hardening.py` and `tests/test_host_runner_redaction.py`.

Leak and secret checks REUSE the repository's canonical tooling. There is no forked scanner:

- The leak sanitizer is `aw sanitize` (alias `aw check-local-leaks`), backed by
  `agent_workflows/leak_sanitizer.py`.
- The secret scanner is `.aw/system/workflows/assess/tools/scan_secrets.py`.

## The boundaries

1. Local servers bind loopback and require auth. `check_local_server_binding` refuses a bind to
   a routable address, refuses non-loopback hostnames or host:port strings, and refuses an
   unauthenticated loopback endpoint. A local headless server may be unauthenticated by default
   on some hosts; the integration must bind a genuine loopback address (such as 127.0.0.1,
   127.0.0.0/8, ::1, or localhost) AND require a token.
2. External files are consented and contained. `check_external_file_access` refuses an access
   with no explicit consent and refuses a path that escapes the consented base (it reuses the
   containment guard `host_capability_registry.assert_contained`).
3. Skills are least privilege. `check_skill_least_privilege` refuses a skill entry point that
   inlines the canonical authoritative body or fails package validation.
4. Evidence is redacted. `check_evidence_redaction` applies the ledger redaction policy (masking
   sensitive keys), runs the CANONICAL leak sanitizer over the payload, and runs the canonical
   secret scanner's credential rules. Maintainer or machine identifying info (such as a home path)
   and credentials fail closed with findings in evidence. The entropy and PII heuristics are
   deliberately not part of this gate because they would refuse routine output such as commit hashes.
   An unavailable secret scanner also fails closed.
5. The real HOME is excluded from probes. `check_real_home_excluded` reuses
   `assert_isolated_base`, which refuses a base equal to or containing the real home.
6. Untrusted text is isolated as data. `check_untrusted_text_isolated` refuses any path that
   executed untrusted repository, tool, or inter-agent text as instructions; it still reads the
   text safely as data and flags an injection attempt.
7. Destructive tools are human-gated. `check_destructive_tool_gated` refuses a destructive tool
   without a genuine human consent, and refuses a non-human role that claims to consent (only
   the human role can record approval; a role cannot synthesize its own consent).
8. Agent turns contain user-config writes. Runner turns export a per-turn seeded copy of
   user configuration via `AW_CONFIG_DIR`. Writes during a turn remain inside the sandbox
   and are discarded at turn exit rather than altering operator settings. Honest limit:
   `AW_CONFIG_DIR` is an environment selector, not a hardened security boundary; an agent
   running with same-user shell access can unset the variable or write to `~/.config` directly.
   The hardened execution profile provides OS-level sandbox enforcement.
9. Agent turns contain AW_HOME writes while preserving project records. Runner turns export
   a per-turn seeded sandbox via `AW_HOME`. Incidental changes to `config/registry.json` and
   scratch project directories created during a turn remain inside the sandbox and are
   discarded at turn exit rather than altering operator registry or polluting storage.
   Project directories that the turn repository already uses under `AW_HOME` (home backend
   or clean-delta delivery) pass through directly so project records stay at their current
   location. Discarded writes are summarized at run exit. Fail-open behavior: if a pass-through
   link cannot be created, the runner logs a warning and leaves `AW_HOME` uncontained rather
   than risking record redirection or loss. Honest limit: `AW_HOME` is an environment
   selector, not an OS-level sandbox boundary; an agent running with same-user shell access can
   unset the variable or access directories directly. The hardened execution profile provides
   OS-level sandbox enforcement.

## Runbooks (how to prove each boundary)

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
