<!--
Research baseline: OpenCode v1.17.18, tag commit b1fc811, released 2026-07-09.
Research date: 2026-07-13, America/New_York.
Evidence labels: VERIFIED-SOURCE, DOCUMENTED, OBSERVED-EXTERNAL-REPORT, INFERRED, PROPOSED.
No live OpenCode binary was available in the execution sandbox, so runtime claims are source-derived unless explicitly labeled otherwise.
-->
# Implementation Roadmap

## Guiding decision

Treat OpenCode instances as execution workers, not as magical persistent minds that must be awakened through terminal tricks. Maintain durable task state outside the model and use OpenCode's native HTTP/SDK surface to create bounded work sessions.

## Phase 0: exact-version validation

Before implementation, build a regression harness against OpenCode v1.17.18 and every version you intend to support.

Required tests:

- TUI with fixed port and password
- standalone `serve`
- session create
- synchronous prompt
- `prompt_async` from idle
- prompt during active run
- two simultaneous prompts
- SSE status/idle/error events
- TUI append/select/submit
- server restart
- shared persistent session visible through two server processes
- abort and cleanup

Record the runtime `/doc` OpenAPI hash for compatibility detection.

## Phase 1: direct API proof of concept

### Goal

Prove controlled one-way delegation without a plugin.

### Steps

1. Launch receiver:

   ```bash
   OPENCODE_SERVER_PASSWORD="$(openssl rand -base64 32)" \
     opencode serve --hostname 127.0.0.1 --port 4097
   ```

2. Verify `/global/health`, `/project/current`, and `/path`.
3. Create a new session.
4. Send one prompt through the SDK.
5. Subscribe to events and read messages until a final assistant response appears.
6. Abort after a fixed deadline.
7. Never reuse a busy session.

### Exit criteria

- task IDs correlate to session and message IDs
- no prompt loss in 1,000 serialized runs
- failures are detectable and classified
- credentials never appear in logs

## Phase 2: durable local broker

### Goal

Add reliable queueing and instance registration.

### Components

- Python/Rust/Go daemon
- SQLite in WAL mode
- local API over Unix socket, named pipe, or loopback
- instance registry with heartbeat
- task, attempt, lease, event, result, and audit tables
- HMAC or public-key principal authentication

### Core tables

```text
principals
instances
projects
capabilities
tasks
task_attempts
leases
approvals
results
events
nonces
audit_log
```

### Dispatch rules

- one task per new session
- one active dispatch per instance up to configured concurrency
- one active writer per worktree unless explicitly coordinated
- task expiry before dispatch
- capability validation at submission and dispatch
- result reconciliation after any disconnect

## Phase 3: safe filesystem mailbox fallback

Implement only if a no-daemon mode is valuable.

Directory layout:

```text
$XDG_RUNTIME_DIR/ocpeer/
├── keys/
├── inbox/
│   ├── tmp/
│   ├── ready/
│   ├── processing/
│   ├── done/
│   └── dead/
└── outbox/
```

Rules:

- runtime root mode `0700`
- files mode `0600`
- no repository-local mailbox
- reject symlinks and non-regular files
- write, flush, and atomic rename within one filesystem
- claim by rename
- HMAC every envelope
- periodic scan in addition to watcher
- lease file or broker DB for crash recovery

## Phase 4: OpenCode plugin adapter

### Goals

- register worker instance
- show task offer to user
- create scoped sessions
- submit work
- report results
- expose peer tools to sending agents

### Safety defaults

- approval mode enabled
- new session per task
- Build agent not selected automatically
- read-only permission profile
- external directory denied
- network denied
- task/subagent delegation denied
- 30-minute timeout
- one concurrent peer task

## Phase 5: headless worker service

Run workers under a supervisor:

- systemd user service on Linux
- launchd user agent on macOS
- Windows service or scheduled background process under a dedicated account

Use separate worktrees or containers for concurrent write tasks. Rotate OpenCode server credentials on every launch and pass them to the coordinator through a protected channel.

## Phase 6: production hardening

### Reliability

- lease heartbeats
- dead-letter queue
- exponential backoff with jitter
- reconciliation sweeper
- OpenCode version compatibility matrix
- graceful drain before upgrade
- chaos tests for broker, worker, and network failures

### Security

- per-principal signing keys
- least-privilege service accounts
- encrypted secret storage
- signed plugin releases
- SBOM and vulnerability scanning
- tamper-evident audit logs
- emergency kill switch
- cost and token budget limits

### Observability

Metrics:

- queued tasks
- dispatch latency
- execution duration
- retry count
- dead tasks
- active OpenCode sessions
- approval latency
- rejected tasks
- token/cost totals
- event-stream reconnects
- reconciliation discrepancies

## Phase 7: upstream contribution

Prepare a narrowly scoped OpenCode proposal for:

- message origin metadata
- scoped prompt tokens
- stable instance identity endpoint
- atomic queued prompt API
- durable task correlation in events

Include tests demonstrating current same-session race behavior and the proposed semantics.

## Operational runbook

### Receiver unavailable

- keep task queued
- do not start a second server against the same active session
- expire or reroute only under policy

### Worker crashes

- lease expires
- coordinator checks whether the OpenCode session stored a result
- if no result, create a new attempt and new session
- do not resend blindly to the old session

### Human TUI is active

- show a notification
- do not append or submit silently
- offer to accept into a new session

### Repository has uncommitted changes

- read-only task may proceed
- write task should use a new worktree or require explicit approval
- record baseline commit and dirty status

### Emergency stop

- coordinator stops new dispatch
- sends abort to active peer sessions
- revokes instance capabilities
- retains evidence and audit

## Definition of done

The system is production-ready only when:

- every accepted task has exactly one durable broker state
- duplicate requests do not duplicate work
- a crashed worker cannot lose a task silently
- no untrusted prompt can expand its enforced scope
- a receiving human can identify peer-originated work
- two workers cannot unknowingly edit the same worktree
- version-specific OpenCode regressions are detected in CI
- all secrets are protected and redacted
- terminal injection is absent from the production path
