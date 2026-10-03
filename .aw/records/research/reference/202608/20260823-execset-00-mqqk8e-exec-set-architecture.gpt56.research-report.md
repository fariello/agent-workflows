---
id: mqqk8e
created: 20260823
set: execset
order: 00
topic: [ipd, orchestration, parallelism, skills, host-adapters]
model: gpt56
kind: research-report
status: reference
outcome: adopted
summary: Architecture for autonomous parallel execution of approved IPD sets across supported coding hosts.
consumed-by: [5ahblp]
---

# Autonomous IPD Set Execution Architecture

## Executive conclusion

Implement one canonical deterministic executor, exposed as `aw ipd execute-set`, and one thin workflow/skill entry point, `/exec-set`. Do not implement separate execution semantics in OpenCode, Codex, Claude Code, or Antigravity prompts. Host adapters should only launch isolated workers, stream structured events, and return validated envelopes to the same coordinator.

The repository already contains nearly all lower-level foundations: typed workflow compilation, an append-only run ledger, evidence capture, completion predicates, a deterministic state machine, bounded packets, human gates, retry/resume, independent verification, worktree isolation, concurrency analysis, capability probes, and skill/adapter generators. The missing layer is a Set compiler and coordinator that applies these facilities across multiple approved IPDs and keeps going after a child is blocked or deferred.

## User requirements converted to invariants

1. The Set coordinator must drain every safe runnable node before asking the human anything.
2. A question does not stop the Set if a robust reversible decision exists, the affected E-item/subgraph can be deferred, or the affected child IPD can be deferred.
3. A child workflow's `STOP` is lexically contained: stop that child/subgraph and return control to the Set coordinator. It is not automatically a Set-wide stop.
4. Skipped work is recorded and never reported as complete. A Set with deferred work is `partial`, not `complete`.
5. All provably safe parallel work runs concurrently. Unknown ownership or dependency information causes serial fallback, never optimistic parallel mutation.
6. Coding work uses the configured coding-model profile. Human-facing prose uses the prose-model profile. Mixed work is split when possible.
7. No worker asks the user directly. Workers return structured decisions, questions, skips, results, and evidence to the coordinator.

## Recommended command and packaging surface

### User entry point

```text
/exec-set <set-id>
/exec-set <set-id> --plan-only
/exec-set resume <run-id>
```

The workflow/skill is a concise router. It resolves the repository, invokes the deterministic CLI, monitors it to a terminal or legitimate hard-stop state, and presents the durable report.

### Deterministic CLI

```text
aw ipd execute-set <set-id> --plan-only
aw ipd execute-set <set-id> [--max-parallel N]
aw run status <run-id>
aw run questions <run-id>
aw run decisions <run-id>
aw run answer <run-id> <question-id> --choice <id> --by-human
aw ipd execute-set --resume <run-id>
aw run cancel <run-id>
aw run finalize <run-id>
```

Planning is an internal mandatory phase of `execute-set`, not a companion workflow the model may forget. `--plan-only` exposes the same compiler for inspection and debugging.

## Execution graph and manifest

Compile every child IPD and E-item into a cross-IPD DAG. Resolve identity by stable `Id`, not path. Read dependencies from explicit structured hints when present and from the orchestrator's child table/current IPD dependency fields for legacy Sets. The generated execution manifest carries:

```json
{
  "node_id": "ipd-abc123:E-02",
  "depends_on": ["ipd-abc123:E-01"],
  "work_class": "coding",
  "model_role": "coding",
  "reads": ["agent_workflows/run_engine.py"],
  "writes": ["agent_workflows/exec_set.py"],
  "generates": [".agents/skills/exec-set/SKILL.md"],
  "shared_surfaces": ["agent_workflows/cli.py"],
  "validation": ["python3 -m unittest tests.test_exec_set"],
  "deferrable": true
}
```

The compiler rejects globally invalid Set structure: a missing orchestrator, missing plans, duplicate IDs, cycles, status/directory contradictions, invalid E/V structure, or ambiguous membership. It does not abort the Set merely because one child lacks approval. It records that child as `deferred_gate`, blocks/defer-propagates only its descendants, and continues every independent approved child. Ambiguous dependencies or write ownership remain executable serially unless they make correct execution impossible.

## Exact hard-stop policy

For the smallest affected DAG subgraph:

```text
needs_human =
    missing information materially affects safe/correct execution
    AND no robust in-scope decision is available

hard_stop =
    needs_human
    AND affected subgraph cannot be safely deferred
    AND affected IPD cannot be safely deferred
```

Even when `hard_stop` is a candidate, drain every independent safe runnable node first. Then:

| Condition | Required behavior |
| --- | --- |
| Robust, in-scope, reversible choice exists | Record autonomous decision before mutation; continue. |
| No robust choice, affected subgraph deferrable | Record question and skip; block descendants; continue. |
| Subgraph not deferrable, child IPD deferrable | Leave child pending, record deferred IPD; continue. |
| Approval/release/deploy/sign-off missing | Skip the gated side effect if separable; never synthesize approval. |
| No decision and no safe defer/skip | Drain other work, then emit one self-contained `hard_stop_needs_input` packet. |
| Interrupted side effect has unknown outcome | Reconcile from real state; never rerun blindly. If still unknown, defer the affected subgraph/IPD and continue. Ask only when human input is materially required and neither deferral is safe. |

Legacy plan text saying `STOP and report` is contained to that child. Linter failures remain failures: the child cannot execute or transition, but unrelated approved children continue.

### Closed Set-level state machine

The Set coordinator owns a closed state machine separate from individual child lifecycle:

| State | Meaning | May resume? |
| --- | --- | --- |
| `planned` | Immutable manifest exists; no lane has started. | yes |
| `running` | At least one lane is active or runnable. | yes |
| `waiting_input` | Frontier drained; exact hard-stop predicate is true and one self-contained question is emitted. | yes, after `human_answer` |
| `partial` | Frontier drained; work was safely deferred and nothing else is runnable. This invocation ends without asking. | yes, after answer/config/approval changes |
| `complete` | Every required node is independently verified on integrated HEAD. | no |
| `failed` | A non-retryable execution/integrity failure prevents truthful continuation. | no, except explicit recovery creating a new run |
| `cancelled` | Authorized cancellation completed. | no |

Allowed transitions are `planned -> running`; `running -> waiting_input|partial|complete|failed|cancelled`; and `waiting_input|partial -> running` through explicit resume. Only the coordinator may transition Set state. An answer, worker envelope, exit code, child status, or model prose cannot directly do so. `complete` is refused while any required node is unverified, deferred, failed, or unknown.

## Formal records and documentation

### Local authoritative run bundle

Use the repository's existing local-only convention:

```text
.aw/workflow-artifacts/exec-set/<RUN_ID>/
  events.jsonl
  execution-manifest.json
  schedule.json
  decisions.md
  questions.md
  deferred-work.md
  lanes/<lane-id>/packet.json
  lanes/<lane-id>/outcome.json
  integration.md
  final-report.md
```

`events.jsonl` is append-only and hash-chained. Markdown files are generated projections, never hand-edited. Extend the closed ledger vocabulary through a new compatible schema version with `question_raised`, `question_disposition`, `human_answer`, `autonomous_decision`, `scope_deferred`, `work_claim`, `lane_outcome`, `integration_result`, and `set_checkpoint`.

### Durable repository record

At every terminal or partial boundary, and after each integrated commit that carries an autonomous decision, generate/update a conventions-compliant walkthrough under `.aw/records/walkthroughs/` containing the execution summary, commits, validations, autonomous decisions, deferred work, and open questions. Promote each unresolved question to `.aw/records/backlog/blocked/` with `Gate-Kind: decision`, `Gate-Ref: <run-id>/<question-id>`, affected Set/IPD/E IDs, options, recommendation, and exact resume command. This makes outstanding input visible in `aw attention` even if local run scratch is lost. After a crash, resume must project any locally recorded but not yet tracked decision/question checkpoint before releasing new work.

Material architectural/public/security decisions also update the repository's existing ADR/`DECISIONS.md` convention when the approved scope permits. Otherwise create a follow-up backlog item. Do not put runtime questions into an approved IPD's authoring-time `## Open questions`, the record-history status sidecar, or inter-agent comms.

### Autonomous decision record

```json
{
  "decision_id": "D-run-a13f-007",
  "scope": {"set":"execset","ipd":"abc123","e":"E-02"},
  "question_considered": "Preserve existing JSON key style?",
  "selected_option": "snake_case",
  "alternatives": ["camelCase"],
  "basis": ["public compatibility tests", "repository convention"],
  "why_no_prompt": "robust reversible choice; independent work remains",
  "consultation_preferred": true,
  "confidence": "high",
  "reversible": true,
  "blast_radius": "local",
  "validation_required": ["contract tests"]
}
```

Record before applying the choice. A reversal is a new immutable event that cites `supersedes`; never rewrite history.

### Deferred question record

```json
{
  "question_id": "Q-run-a13f-004",
  "status": "deferred",
  "question": "Which production tenant is authorized?",
  "why_input_required": "authorization cannot be inferred",
  "affected_nodes": ["ipd:def456:E-03"],
  "disposition": "defer_ipd",
  "options": [{"id":"a","label":"Tenant A"},{"id":"b","label":"Tenant B"}],
  "recommendation": "Do not deploy; continue unrelated Orders",
  "resume": "aw run answer run-a13f Q-004 --choice b --by-human && aw ipd execute-set --resume run-a13f"
}
```

Lifecycle: `raised -> deferred|hard_stop -> answered -> applied -> resolved`, with `superseded` as an alternate terminal disposition.

## Parallel execution and integration

Read-only lanes may overlap. Parallel writers require every condition below:

- separate Git worktrees and fresh worker sessions;
- dependency independence;
- disjoint `writes + generates + shared_surfaces`;
- exclusive path leases;
- no shared lockfile, schema, version, changelog, decision log, IPD, history sidecar, manifest, or generated registry;
- deterministic merge order.

The coordinator alone owns the main worktree, schedule, ledger, IPD checkmarks/evidence, lifecycle transitions, and integration commits. Lanes commit only their allowed paths in their worktree and return structured outcomes. A lane that encounters a consultation-preferred choice must yield a `decision_proposal` before applying it. The coordinator classifies the proposal, appends the autonomous decision (or deferral/question) event, and sends a `decision_authorized` resume message; post-hoc decision ingestion is invalid. After each wave, rebase or replay in topological then IPD-order/lane-ID order, inspect the combined diff, run targeted checks, and finally run full validation at the integrated HEAD. Per-lane green tests do not prove the merged result.

## Model routing

Store host-specific model IDs in configuration, not workflow prose:

```json
{
  "profiles": {
    "coding": {"model":"host-specific coding model","effort":"medium"},
    "prose": {"model":"host-specific prose model","effort":"medium"},
    "verifier": {"model":"independent model or fresh session","effort":"high"}
  }
}
```

Routing rules:

- `coding`: code, tests, build/configuration, schemas, APIs, code comments/docstrings, CLI help, self-documentation, agent documentation, and technical instructions whose correctness depends on code behavior.
- `prose`: website copy, marketing, narrative reports, policies, announcements, and other primarily human-reader content.
- `mixed`: split into a coding fact/implementation lane and a prose authoring lane when outputs are separable. Otherwise route by the primary deliverable and require cross-role verification.
- `verifier`: always a fresh context. The executor never certifies its own V-items or terminal transition.

## Host strategy

One semantic implementation with capability-gated adapters is sufficient.

| Host | Worker strategy | Important constraint |
| --- | --- | --- |
| OpenCode | Independent child session or `opencode run --format json`; external runtime owns worktrees/integration. | Native session forks do not prove file isolation. |
| Codex CLI | Fresh `codex exec` process/session per lane; external worktree; resume task-local session for correction. | Treat native subagent availability as capability evidence, not an assumption. |
| Claude Code | `claude -p`/Agent SDK worker; deny `AskUserQuestion`; optionally use worktree isolation and Stop hooks as defense in depth. | Agent Teams are experimental and interactive-oriented; do not make them authoritative. |
| Antigravity/agy | Headless stream-JSON worker with exact model; use branch workspaces or external worktrees. | Soft-denied tools may still yield exit 0; verify diff, stderr, evidence, and status. |
| Kiro/Gemini CLI | Generate adapters but advertise only after isolated positive and fail-closed capability probes. | Do not claim unsupported or stale capabilities. |

Host-native subagents may help inside a scheduled lane, but the set-level coordinator remains the deterministic runtime.

## Worker protocol

Each worker receives a bounded packet and must return a schema-valid envelope. Allowed terminal states are `completed`, `deferred_partial`, `deferred_ipd`, `failed_retryable`, `failed_final`, and `blocked_required_input`. A nonterminal `decision_proposal` yield pauses the lane until the coordinator returns `decision_authorized`, `defer`, or `cancel`; it never asks the user directly. Free-form completion prose cannot mutate the ledger.

```json
{
  "status": "completed",
  "changed_files": ["src/x.py"],
  "checks": [{"command":"pytest -q","exit_code":0,"log":".../pytest.log"}],
  "decisions": [],
  "open_questions": [],
  "deferred_scope": [],
  "blocking_question": null
}
```

## Resume behavior

`aw ipd execute-set --resume` verifies the chain, reconstructs state solely from events, promotes any untracked decision/question checkpoint before new work, refreshes HEAD/worktrees, ingests human answers, closes linked backlog gates, invalidates affected stale evidence, recomputes the DAG/resource conflicts, and releases newly runnable nodes. It recognizes executed children by stable IPD ID after lifecycle moves. Unknown side effects use the existing explicit reconciliation path, then the same decide/defer/IPD-defer predicate; they have no independent human-stop path.

## Why a skill alone is insufficient

A skill is appropriate for discovery, host invocation, and concise operating policy. It is not appropriate for authoritative scheduling, parallel ownership, retries, durable state, stop classification, evidence validation, or completion. Encoding those behaviors only in prose recreates the exact failure mode this project is trying to eliminate: models can ignore, truncate, reinterpret, or prematurely declare completion.

## Recommended implementation sequence

1. Compile Sets/IPDs into a validated execution DAG and manifest.
2. Extend ledger/event types and implement the stop/defer/decision classifier plus durable projections.
3. Build scheduler, leases, worktree integration, model routing, and resume.
4. Add capability-gated launchers for each host.
5. Generate `/exec-set` skill/shims, update `ipd-lifecycle` stop scoping, and add cross-host conformance/evidence tests.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Model claims success without performing work | Typed outcomes, actual diff inspection, evidence IDs, independent verifier, final integrated checks. |
| Parallel lanes conflict semantically | Declared shared surfaces, path leases, worktrees, deterministic integration, full revalidation. |
| Executor asks trivial questions | Workers cannot ask; coordinator applies the exact stop predicate and records choices. |
| Executor silently skips work | Skip/defer events, partial status, durable walkthrough, attention-visible blocked backlog. |
| Host feature changes | Capability registry with expiry and fail-closed probes; thin adapters. |
| Context degradation | Bounded JIT packets and fresh lane/verifier sessions. |

## Sources consulted

- Repository source at `05910e16ca9aa005b8bb76cf789b5c17d5dd7dcc`, especially `run_*`, `orchestrate_isolation.py`, `host_capability_registry.py`, `host_adapters.py`, `ipd-lifecycle`, and the executed `awoptimize` Set.
- OpenCode official documentation: https://opencode.ai/docs/cli/, https://opencode.ai/docs/agents/, https://opencode.ai/docs/skills/, https://opencode.ai/docs/server/, https://opencode.ai/docs/sdk/.
- Claude Code official documentation: https://code.claude.com/docs/en/sub-agents, https://code.claude.com/docs/en/worktrees, https://code.claude.com/docs/en/headless, https://code.claude.com/docs/en/hooks.
- Antigravity official documentation: https://antigravity.google/docs/cli/headless/, https://antigravity.google/docs/cli/subagents/, https://antigravity.google/docs/skills.

## Confidence

High on the repository architecture and stop/record/parallelism design. Medium on exact host CLI flags until the repository's capability probes are rerun against the installed versions; the runtime must treat those as evidence-gated adapter details, not hard-coded facts.
