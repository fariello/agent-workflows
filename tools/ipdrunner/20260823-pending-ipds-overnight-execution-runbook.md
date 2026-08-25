# Driver Runbook for the Approved 2026-08-23 IPDs

**Runtime:** OpenCode 1.18.21 with Claude Opus 4.8
**Driver:** `aw oc runipd` (packaged; `tools/ipdrunner/runipd.py` is the compatibility shim)
**Manifest:** `20260823-pending-ipds-driver-manifest.json`
**Execution posture:** Unattended, restartable, maximum safe forward progress, no pushing

## 1. Purpose

This runbook is attached to every noninteractive OpenCode turn launched by the driver. The driver, not an outer model session, owns the queue, durable state, exact Set session IDs, subprocess blocking, restart behavior, and chronological report.

Each IPD is a separate blocking `opencode run` turn. IPDs in the same Set continue the same exact OpenCode session so they retain useful orchestrator and intra-Set context. Different Sets use different sessions. Never use `-c`; the driver persists and supplies exact session IDs.

All 22 target IPDs are already human-approved. Do not ask for approval and do not change approval state except through the legitimate lifecycle transitions required by the approved IPD.

## 2. Recommended invocation

Place the driver, manifest, and this runbook somewhere readable outside or inside the repository. They do not need to be copied into the worktree.

Resolve the exact OpenCode model and primary-agent identifiers first:

```bash
opencode --version
opencode models
opencode agent list
```

The reconciled queue is produced with this selector sequence:

```text
v6zie5 unifyfileio ipdgates proclint execset
```

The initial `v6zie5` is deduplicated when `ipdgates` is expanded later. This creates the intended order:

```text
v6zie5
unifyfileio children and closeout
remaining ipdgates children and closeout
proclint
execset children and closeout
```

Start directly. The primary command is `aw oc runipd` (alias `aw opencode runipd`) in any environment where `aw` is installed; the `python3 tools/ipdrunner/runipd.py ...` form shown below continues to work as a compatibility shim that delegates to the same packaged runner:

```bash
aw oc runipd start \
  --repo /absolute/path/agent-workflows \
  --manifest tools/ipdrunner/20260823-pending-ipds-driver-manifest.json \
  --runbook tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md \
  --model '<provider/model-for-opus-4.8>' \
  --agent '<coding-primary-agent>' \
  v6zie5 unifyfileio ipdgates proclint execset

# equivalent legacy/compat invocation:
python3 tools/ipdrunner/runipd.py start \
  --repo /absolute/path/agent-workflows \
  --manifest tools/ipdrunner/20260823-pending-ipds-driver-manifest.json \
  --runbook tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md \
  --model '<provider/model-for-opus-4.8>' \
  --agent '<coding-primary-agent>' \
  v6zie5 unifyfileio ipdgates proclint execset
```

If OpenCode's configured default is already Opus 4.8 and its normal primary agent is correct, `--model` and `--agent` may be omitted.

To inspect the resolved durable queue before launching anything, add `--prepare-only`, note the printed run ID, then start it with:

```bash
python3 tools/ipdrunner/runipd.py resume \
  --repo /absolute/path/agent-workflows \
  <run-id>
```

## 3. Durable state and restart

The driver stores each run beneath:

```text
.aw/records/runs/<run-id>/
```

This location is repository-specific, shared across worktrees, and survives driver termination. It contains:

```text
state.json
events.jsonl
execution-report.md
decisions-and-questions.md
driver.lock
outcomes/
prompts/
sessions/
```

Inspect a run:

```bash
python3 tools/ipdrunner/runipd.py status \
  --repo /absolute/path/agent-workflows \
  <run-id>
```

Resume queued work after a driver or terminal failure:

```bash
python3 tools/ipdrunner/runipd.py resume \
  --repo /absolute/path/agent-workflows \
  <run-id>
```

A plain `resume` also re-queues the single item that was in flight when the run was interrupted (the one left `interrupted` by crash reconciliation), retrying it in recovery mode so that unit of work is not abandoned. It does not, however, retry items that finished in a `partial`, `failed-safely`, `blocked`, or `dependency-blocked` state; use `--retry-incomplete` for those.

Retry interrupted, partial, blocked, dependency-blocked, or safely failed items in recovery mode:

```bash
python3 tools/ipdrunner/runipd.py resume \
  --repo /absolute/path/agent-workflows \
  --retry-incomplete \
  <run-id>
```

The driver must never blindly infer success from its own prior process. It reconciles an interrupted item with the actual IPD location and outcome records. A model-authored `"disposition": "executed"` is not authoritative unless the real lifecycle artifact is in the executed state.

## 4. Session topology

The driver creates and persists one session per Set:

| Set | Session use |
|---|---|
| `ipdgates` | Starts with `v6zie5`, becomes idle while `unifyfileio` runs, then resumes by exact ID for the remaining lifecycle plans and closeout |
| `unifyfileio` | Naming, identity, resolver, reference, history, and orchestrator closeout |
| `proclint` | Singleton `79li67` plan |
| `execset` | Graph, decision/skip rules, scheduler, adapters, shims, and orchestrator closeout |

The first turn in a Set omits `--session`, causing `opencode run` to create a new session. Every JSON event contains its `sessionID`; the driver extracts and stores it. Later turns use `--session <exact-id>`. Each foreground process blocks until OpenCode reports that the session is idle.

When resuming `ipdgates` after `unifyfileio`, refresh repository instructions and source state. Retain conceptual Set context, but do not rely on stale file observations from before the refactor.

## 5. Noninteractive question policy

OpenCode noninteractive execution does not provide a live human-answer channel. Do not invoke an interactive question tool or wait for input.

When a material question arises:

1. Search the approved IPD, its orchestrator, repository instructions, decisions, specifications, source, tests, history, and current primary documentation where relevant.
2. Identify viable options and their effects on scope, compatibility, safety, reversibility, and later approved IPDs.
3. Prefer the explicitly specified, repository-established, least disruptive, reversible, and testable approach.
4. If a reasonable recommended approach exists, choose it, record it, implement it, validate it, and continue.
5. If no reasonable approach exists, record it as deferred, complete every independent part of the IPD, preserve partial work safely, and exit the turn without fabricating completion.

Every question that could reasonably have been asked of the human but was answered autonomously must be written to `decisions-and-questions.md` using:

```text
## DECISION <position>-<id6>-D<number>
- IPD:
- Timestamp:
- Question:
- Evidence consulted:
- Options considered:
- Selected approach:
- Why this is recommended:
- Confidence: very low | low | med low | medium | med high | high | very high
- Scope/files affected:
- Reversibility:
- Validation:
- Human review requested:
```

An unresolved question must use:

```text
## DEFERRED <position>-<id6>-Q<number>
- IPD:
- Timestamp:
- Question:
- Evidence consulted:
- Options considered:
- Why no reasonable approach was available:
- Work completed despite the question:
- Work blocked:
- Dependency effect:
- Exact preserved state:
- Recommended human action:
```

If no material question arose, the per-IPD outcome must say so explicitly.

## 6. Forward-progress rule

Do not abandon an IPD merely because one part is blocked. Continue every independent requirement, test, documentation update, and read-only validation within its approved scope.

Do not terminate the overall run because one IPD exits nonzero, cannot finalize, or has a deferred question. The driver will record the outcome and scan for another dependency-valid item.

If an IPD cannot finalize:

- use a repository-supported nonterminal checkpoint if available;
- otherwise preserve work in an attributable isolated branch/worktree;
- do not mix it into the next IPD;
- do not stash or discard it;
- report the exact branch/worktree, HEAD, files, tests, and remaining work; and
- leave the main execution checkout safe for later turns.

Stop the entire run only when no safe runnable work remains or continued execution would risk irreversible loss, repository corruption, compromised credentials, authority impersonation, or unattributable cross-agent changes that cannot be isolated.

## 7. Plan order and critical gates

### 7.1 Independent remediation

1. `v6zie5`, p7dqwz isolation residue.

This is independent. If it cannot execute, record the issue and continue to `unifyfileio`.

### 7.2 `unifyfileio`

2. `o6b8l3`, canonical naming/grammar.
3. `9a655p`, filename identity/id6 uniqueness.
4. `laykok`, selector-to-file resolver.
5. `3cmnfc`, reference matcher/rewriter/dangling policy.
6. `52zgqr`, rename/regroup history ledger.
7. `g6mbht`, Set validation and closeout.

Do not close `g6mbht` unless all required children are genuinely executed and Set-wide checks pass.

### 7.3 Remaining `ipdgates`

8. `oorry1`, Scope-Paths schema, using the existing lifecycle.
9. `xjbvu2`, begin receipt, using the existing terminal lifecycle.
10. `v7e88a`, atomic finalize. This is the first plan that may self-finalize after its implementation is present and tested.
11. `qmt3yk`, two-way scope reconciliation, dogfooding begin/finalize.
12. `3xh53a`, rollback/failure semantics, dogfooding begin/finalize.

Before `wezhxg`, verify all of the following:

- `v7e88a`, `qmt3yk`, and `3xh53a` are executed;
- a representative begin/finalize completed end-to-end;
- forward finalization made the correct path-scoped commit;
- injected failures rolled back or left the specified recoverable state;
- corrected retry succeeded;
- checker, doctor, index, lifecycle, failure-injection, and regression tests pass; and
- every valid plan retains a proven terminal path.

If any condition fails, do not execute `wezhxg`. Record the failed lockout checkpoint and continue only dependency-valid work.

13. `wezhxg`, remove raw terminal bypasses.
14. `dulzpy`, local executed-transition pre-commit gate. OQ-01 is reported resolved; verify rather than reopening it without evidence.
15. `do64fh`, Set validation and closeout through the new lifecycle.

### 7.4 `proclint`

16. `79li67`, intermediate untooled-transition detection.

Revalidate its checker, doctor, installer, and hook integration against completed `unifyfileio` and `dulzpy` before implementation. It must compose with the terminal gate rather than replace or duplicate it.

### 7.5 `execset`

17. `iy1a2g`, Set graph compiler/manifest.
18. `3m4e54`, deferred questions, autonomous decisions, and skips.
19. `m2wwns`, scheduler, worktrees, routing, and resume.
20. `31744f`, host adapters and capability-gated launchers.
21. `2h7777`, `/exec-set` workflow, skills, shims, and conformance.
22. `5ahblp`, adversarial/recovery validation and closeout.

The implementation turns remain serial even where eventual concurrency is supported. This run is bootstrapping the scheduler itself.

## 8. Per-IPD requirements

Each turn must:

- read all applicable repository instructions;
- read its assigned IPD in full;
- read its current orchestrator and prerequisite outcomes;
- refresh actual repository state;
- execute only its assigned IPD;
- honor declared Scope-Paths and acceptance criteria;
- use the lifecycle available at that bootstrap stage;
- record all autonomous decisions and deferred questions;
- run required tests and regression checks;
- run applicable checker, doctor, index, hook, and lifecycle validation;
- inspect changed and staged paths before commit/finalization;
- claim executed only when the authoritative lifecycle state supports it;
- preserve incomplete work safely and attributably;
- write the required JSON outcome; and
- explicitly report `"pushed": false`.

## 9. Safety requirements

- Do not push.
- Do not use `git add -A`, `git add .`, `git commit -a`, or `--no-verify`.
- Do not disable hooks or validation.
- Do not hand-edit terminal state, receipts, history, or test evidence.
- Do not change an IPD's requirements to make it easier.
- Do not broaden scope opportunistically.
- Do not reset, clean, stash, overwrite, or discard unrelated work.
- Do not mix separate IPDs in one commit.
- Preserve actual test output and failure status.
- Treat model-authored reports as claims that must agree with repository evidence.

## 10. Morning review

The driver prints the run ID and state directory when it starts. Review in this order:

1. `decisions-and-questions.md`
2. `execution-report.md`
3. `outcomes/`
4. `sessions/`
5. Actual Git branches, commits, worktrees, IPD lifecycle state, and checks

The report distinguishes attempted, executed, partial, blocked, failed, dependency-blocked, interrupted, and not-attempted plans. Do not treat a completed driver process as proof that every IPD executed.

## 11. Final rule

When a reasonable recommended approach exists, decide, record, implement, validate, and continue. When none exists, defer, preserve, and continue elsewhere. Do not stop the overall run while safe dependency-valid work remains.
