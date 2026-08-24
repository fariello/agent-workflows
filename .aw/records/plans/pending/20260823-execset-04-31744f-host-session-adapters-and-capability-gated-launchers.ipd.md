# IPD: Host Session Adapters and Capability Gated Launchers

- Date: 2026-08-23
- Kind: child
- Concern: Launch structured fresh workers across coding hosts without duplicating semantics.
- Scope: Generic runner, OpenCode/Codex/Claude/Antigravity/Kiro/Gemini adapters, capability evidence, structured streams, and fresh verification.
- Status: approved
- Set: execset
- Order: 4
- Highest E allocated: 03
- Author: OpenAI GPT 5.6 Sol
- Id: 31744f
- Approval: 2026-08-24, human ("approved. go."): status set to approved

## Workflow history
- 2026-08-24 approved (aw set, --by-human): status set to approved
- 2026-08-23 /plan-review focused security (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH: mandate shell=False/argv worker spawn - avoid the shell=True probe pattern), PR-002 (reuse security_hardening.py boundaries, not net-new), PR-003 (map 6 net-new worker states to ledger performed|blocked|failed), PR-004 (timeout/cancellation is net-new), PR-005 (name reused anti-greenwashing + distinct-session validators to wire host output into). V-01 strengthened.
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (agy_run.py does not exist -> use agy_verifier.py), PR-004 (corrected host matrix facts: 7 rows incl. Copilot/Cursor, Kiro row missing).
- 2026-08-23 to-review (aw set): Authored from current runtime, lifecycle, isolation, and cross-host capability research; ready for plan review.

- 2026-08-23 draft (OpenAI GPT 5.6 Sol): created from official host documentation and repository capability audit.

## Goal

Provide one evidence-gated worker interface that can start, monitor, resume, cancel, and verify isolated tasks on each supported host while keeping the Set coordinator authoritative.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Generic structured runner

- [ ] E-01 Implement `agent_workflows/host_runner.py` with bounded task packets, structured streaming, timeouts, cancellation, session identity, actual-diff capture, stderr/status parsing, and validated terminal envelopes; do not reuse benchmark live gates.
  - Depends on: none
  - Note (verified - process spawning is net-new; pin its security posture): no worker-launcher exists today (net-new). SECURITY (hard requirements): (1) spawn workers with an argv LIST and `shell=False` - NEVER `shell=True` with task-derived content (the existing probe pattern `host_capability_registry.py:711-719` uses `shell=True` and MUST NOT be copied for task packets; this is a command-injection surface). (2) Timeouts and cancellation are genuinely net-new - existing subprocess calls use short fixed timeouts or none (`host_capability_registry.py:350` `timeout=5`; `run_isolated_probe` passes no timeout), so build a real bounded-timeout + kill/cancel path for a long-lived worker; a timed-out/cancelled worker is a failure, never completion. (3) Route ALL captured stdout/stderr/diff through redaction+leak scanning before it enters the ledger (see the reused `security_hardening.check_evidence_redaction` in the Scope check). Reuse `run_packet.StepOutcomeEnvelope` + `run_evidence` validators for the terminal envelope (see Proposed changes); do not treat host exit 0 as success.
  - Expected outcome: the coordinator receives facts, not free-form completion claims.
  - Execution state: pending

### Material change 2: Capability-gated adapters

- [ ] E-02 Add thin per-host launchers generated through the existing adapter/shim code, advertising native subagents, model flags, resume, JSON, worktrees, or permissions only with current positive and fail-closed probe evidence.
  - Depends on: E-01
  - Note (verified): generate via `host_adapters.py` + `engine.py` shim generators; do not fork wrapper generation. The capability/support matrix (`host_capability_registry.py:371-449`, `host_matrix.json`) currently has 7 rows (OpenCode, Codex, Claude Code, Antigravity/AGY, Copilot, Cursor, Gemini) and NO Kiro row, while Kiro already exists as an adapter (`host_adapters.py:70`) and benchmark runner - E-03 adds the missing Kiro matrix row and must not drop the existing Copilot/Cursor rows. v1 skill targets remain OpenCode and Codex (Step-0 conventions).
  - Expected outcome: unsupported/unverified capabilities use a safe external-process fallback or explicit refusal.
  - Execution state: pending

### Material change 3: Fresh verification and host tests

- [ ] E-03 Require distinct executor/verifier sessions, task-local resume for correction, host-specific greenwashing checks, exact model-role binding, and isolated positive/negative probes including the currently missing Kiro matrix row.
  - Depends on: E-02
  - Expected outcome: no same-session audit or host success exit can finalize work without evidence.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Extend `host_adapters.py`, `host_capability_registry.py`, and `engine.py` generators; do not fork wrapper generation.
- OpenCode and Codex are v1 skill targets; other hosts remain unverified until probes.
- `agy_verifier.py` (`agent_workflows/agy_verifier.py:1`, verified to exist) is the authoritative fresh-session verifier contract; use it. NOTE (verified): there is NO `agy_run.py` module in the tree - the name appears only as a compat-migration test-surface string (`compat_migration.py:276-278`), so do not plan to reuse an `agy_run.py`; same-session/same-conversation review must not be treated as authoritative regardless.
- Host native teams/subagents differ; set-level orchestration must not depend on them.

## Findings

OpenCode is strong for heterogeneous model routing but needs external worktree/integration control. Claude has mature subagents/worktrees/hooks but Agent Teams are experimental. Antigravity supports fresh asynchronous/branch workers, but soft-denied tools may still yield exit 0. Codex can use fresh `codex exec` sessions with external worktrees; native delegation remains capability-gated.

## Proposed changes (ordered, validatable)

Worker terminal states: `completed`, `deferred_partial`, `deferred_ipd`, `failed_retryable`, `failed_final`, `blocked_required_input`. These are host-worker-specific and NET-NEW (they do not exist in the codebase); E-01 MUST define them AND map each down to the authoritative ledger attempt states `performed|blocked|failed` (`run_state.py:29-31`) - e.g. `completed->performed`, `deferred_*/blocked_required_input->blocked`, `failed_*->failed` - so nothing bypasses the ledger vocabulary. Every result carries changed files, checks with exit/log evidence, decisions, questions, deferred scope, and blocking question. Workers cannot ask users directly.

Anti-greenwashing is REUSE, not net-new: wire the host worker's exit code / stdout / stderr / diff INTO the existing validators - `run_evidence.validate_evidence` (`EV-FAILED-EXIT`, `EV-MISSING-OUTPUT`, `EV-FABRICATED-TEXT`, `EV-EXPIRED-PROBE`), `agent_schema` exit/outcome parity, `verify_roles.py:1738` (success-claim vs non-zero-exit guard), and `run_packet` prose/evidence rejection - so a host exit-0 with no verified side effect can never become `completed`. Distinct-session enforcement is REUSE too: use `agy_verifier.assert_distinct_sessions` / `run_fresh_verifier` (same-session is diagnostic-only and cannot finalize).

Prefer one fresh process/session per lane; resume it for corrections; start a distinct clean verifier. The coordinator owns worktrees unless a probed native worktree mode is selected, never both.

## Deferred / out of scope (with reason)

- Host-native experimental team orchestration is optional acceleration only.
- Live paid-model benchmarks remain operator-run and separate.

## Scope check

- Over-scope: none.
- Under-scope: redact secrets/paths and bind any local server to loopback with authentication - but REUSE the existing `agent_workflows/security_hardening.py` boundary suite (Order 18), do NOT reimplement: `check_evidence_redaction` (RedactionPolicy + canonical leak sanitizer over captured worker output), `check_local_server_binding` (loopback + required auth; a live server does not exist today, so this applies only if `host_runner` starts one, e.g. OpenCode server mode), `check_external_file_access`, `check_real_home_excluded`, `check_untrusted_text_isolated`, and `check_destructive_tool_gated`. `host_runner`'s spawn + output-capture path MUST call these checkers rather than open-code equivalents.

## Required tests / validation

Use model-free doubles plus isolated operator probes for missing binary, denied permissions, soft denial with exit 0, malformed output, timeout, lost background result, stale session, same-session verifier, path escape, server auth, and exact model routing.

## Spec / documentation sync

Generate the support matrix from unexpired evidence and document fallback behavior, not aspirational capability.

## Open questions

### OQ-01: One implementation per host?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: one semantic runner plus thin adapters; separate implementations would drift.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: runner-double tests prove malformed/free-form/timeout/success-without-diff outcomes cannot become completed. SPECIFICALLY: (a) a test proves workers are spawned with an argv list and `shell=False` (a task packet containing shell metacharacters does NOT reach a shell); (b) a bounded-timeout test proves a hung worker is killed and recorded as failure, and cancellation terminates the process; (c) a redaction test proves captured stdout/stderr/diff pass through `security_hardening.check_evidence_redaction` before entering the ledger (a planted home-path/secret is masked/blocked); (d) each net-new worker terminal state maps to the correct `performed|blocked|failed` ledger state.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: generated adapter and capability-fixture tests prove only unexpired positive probes advertise each feature, missing/negative evidence selects the documented safe fallback, and semantic digests remain in parity.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: executor and verifier session IDs differ; soft-denied exit-zero, malformed envelope, wrong model, missing diff/check, timeout, and stale-session fixtures all fail without terminal completion.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes build the runner, adapters, and independent verification proof.

Requires executed Order 03 and explicit approval. Do not run live models in agent-executed tests or claim support without current probe evidence.
