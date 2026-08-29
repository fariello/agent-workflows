---
id: x03wgn
created: 20260828
set: wtiso
order: 00
topic: [worktree-isolation, state-model, multi-agent-runner, orchestration]
model: gpt56
kind: research-report
status: todo
outcome: none-yet
summary: GPT-5.6 architecture for isolating concurrent agent lanes with a driver-owned control plane and out-of-repo machine state
consumed-by: []
---

# Worktree Isolation and State Model Research Report

**Repository examined:** [`fariello/agent-workflows`](https://github.com/fariello/agent-workflows)
**Code snapshot:** commit [`8d1bcd5160f39b2b60e953902d764f401591039d`](https://github.com/fariello/agent-workflows/tree/8d1bcd5160f39b2b60e953902d764f401591039d), committed 2026-08-28
**Research and access date:** 2026-08-29
**Revision focus:** runner-controlled execution, forgetful agents, enforceable authority, and recovery
**Final hardening pass:** lane self-sufficiency, local artifact retention, protected Git administration, and durable publication

## 1. Executive summary and the single recommended design

**Recommendation:** retain Git worktrees as the product-code isolation primitive, but split the system into a driver-owned control plane and a lane-owned product data plane. Resolve all control paths through one typed `ExecutionContext`, store canonical machine state outside every checkout under a platform state directory keyed to the repository's exact Git common directory, and make the runner perform every mechanical lifecycle prerequisite before it starts a write-capable agent. Before launch, assemble a self-sufficient lane from the committed Git base plus an explicit, digest-verified manifest of required local inputs; never solve a missing input by exposing the original checkout. After execution, classify every lane change as tracked/publishable, locally retained, secret, discardable cache, or unknown, and forbid teardown until each item is integrated, copied and verified, explicitly discarded by policy, or preserved for review. Treat runner-generated prompts, optional lane commands, and Git hooks as compliance and feedback mechanisms, not as the source of truth. The agent may edit files directly, forget every custom tool, omit its outcome file, bypass a hook, or exit with an inaccurate summary; the driver must still discover the actual Git and filesystem result, reconcile material decisions in a generated closure turn, independently validate it, and either integrate or preserve and block it. In the normal profile, central control state is kept outside the worker's cwd, is not named in its prompt, and is mutated only by coordinator code. If "driver only" must be a hard guarantee rather than a reliable operational rule, launch the worker in an OS sandbox or under a separate principal that can write only its lane, and keep the shared Git common directory read-only to the worker. A same-user process with arbitrary shell access cannot be cryptographically or filesystem-enforced from prompts, hooks, environment variables, or Python role checks alone.

### Labeled architecture and ownership layout

```text
PRODUCT DATA PLANE                         CONTROL PLANE
Git common directory identifies checkout  Platform machine-state directory
                                           $XDG_STATE_HOME/agent-workflows/
main worktree/                              checkouts/<checkout-id>/
  tracked repository files                   control/
  .aw/system/                    tracked        runs/<run-id>/
  .aw/config/                    tracked          manifest.json       DRIVER
  .aw/records/                   tracked          events.jsonl        DRIVER
                                                  reports/             DRIVER
lane worktree/                                  receipts/<run>/<lane> DRIVER
  branch aw/lane/<run>/<lane>                  decisions/             DRIVER
  tracked product files          AGENT          transactions/        DRIVER
  .aw/lane/<run>/<lane>/                       lane-registry.json    DRIVER
    contract.json                DRIVER        integration.lock      DRIVER
    input-manifest.json          DRIVER        artifacts/<run>/<lane>/
    input/                       DRIVER          local-retained/     DRIVER
    submissions/                 AGENT         sessions/             DRIVER
      outcome.json   optional/advisory
      decisions.jsonl optional/proposals
      DONE            optional/digest

Driver observes: process events + base/tip + status + diff + tests + submissions
Driver decides:  preserve | request closure | verify | integrate | block

DURABLE PROJECT PUBLICATION
driver-owned publication candidate/
  .aw/records/...                 sanitized projections from the control ledger
  product changes                actual lane delta
  -> merge and validate together before target update
```

`checkout-id` is a machine-local identifier bound in a registry to the canonical result of `git rev-parse --git-common-dir`. `project-id` is a separate portable logical identity. Two independent clones of the same origin get different checkout IDs unless a user explicitly attaches them. Git documents that linked worktrees share a common repository while maintaining per-worktree state such as `HEAD` and the index, and exposes the common directory through `git rev-parse --git-common-dir`. [[R2](#references), [R7](#references)]

### The controlling design principle: behavior, feedback, authority

The revised design separates three concerns that are easy to conflate:

| Layer | Purpose | Mechanisms | May correctness depend on it? |
|---|---|---|---|
| **Behavior** | Make the desired path the easiest and most salient path for the model | Short runner-generated execution packet, exact IDs and commands, just-in-time reminders, optional `aw lane` commands | No |
| **Feedback** | Detect a mistake early enough for the same agent to repair it | Pre-commit hook, scoped path checks, host event parser, closure turn based on observed diff | No, but it reduces expensive failed turns |
| **Authority** | Determine what actually happened and what may be integrated | Driver-created receipt, event ledger, Git inspection, validation, transaction journal, integration lock | Yes |

This resolves the concern that agents naturally edit files and often forget unfamiliar tools. The architecture does not attempt to retrain that behavior into a correctness boundary. Direct editing is expected. Custom agent commands are conveniences for earlier feedback and richer semantic capture. The driver owns the irreversible transitions.

### Driver state machine

The canonical lifecycle is:

```text
PREPARED -> AUTHORIZED -> RUNNING -> OBSERVED -> RECONCILED -> VERIFIED -> INTEGRATED
                              |           |            |
                              +--------> PRESERVED/BLOCKED <---+
```

- **PREPARED:** the driver resolves identity, verifies the target base, creates the lane branch/worktree, records scope, assembles and seals required local inputs, installs or selects policy, and snapshots relevant configuration and protected Git state.
- **AUTHORIZED:** the driver itself creates the begin receipt and durable ledger event. No agent call is needed.
- **RUNNING:** the worker receives a writeable product lane and edits normally. It never receives a capability to mutate canonical control state.
- **OBSERVED:** after process exit or forced termination, the driver records exit status, event stream, worktree status, protected Git state, untracked/ignored files, staged and unstaged changes, commits, changed paths, test artifacts, input modifications, and optional submissions.
- **RECONCILED:** the driver checks scope and decision-record obligations. If semantic attribution is incomplete, it resumes or launches a tightly scoped closure turn with the observed changes already enumerated. No new product edits are permitted in this turn unless the driver explicitly reopens execution.
- **VERIFIED:** independent checks run against the lane tip or a driver-created commit containing preserved working changes.
- **INTEGRATED:** under an integration lock, the driver merges product changes and any sanitized durable record projection into an isolated candidate, validates that exact tree, confirms local artifact harvest, then updates the target only if its expected old tip still matches.

Every transition except product edits during `RUNNING` is performed and journaled by the driver. An agent's final prose is never a state transition.

### Two enforcement profiles

1. **Operational default:** sufficient for a forgetful, non-malicious coding agent. Central paths are outside the lane and absent from the prompt; the lane is pre-materialized; external access is denied; lifecycle commands refuse worker role; the runner and hooks provide precise guidance; and the driver rechecks files, Git refs, and worktree administration. This strongly prevents accidental control-state writes but is not a security boundary against arbitrary same-user shell code.
2. **Hardened execution:** required when "only writer" must be literal. Run the worker in a mount namespace/container/sandbox or as a separate OS principal. Make the lane product files and designated lane scratch writable, dependencies read-only as feasible, and the control root, main worktree, sibling lanes, integration candidate, credentials, and Git common directory inaccessible or read-only. In this profile the worker edits files but the driver owns `git add`, commits, refs, and hooks. A read-only-to-write phase transition can then truly require a prerequisite before the first product edit.

The default should not pay the portability and maintenance cost of a container solely to compensate for model forgetfulness. The runner-owned state machine already makes forgetting safe. Add the hardened profile when threat model, customer policy, or host capability warrants it.

## 2. State taxonomy and the single-source versus per-lane classification

The primary distinction is not tracked versus ignored. The useful dimensions are:

- **Authority:** is the artifact a claim, evidence, or a decision that permits an irreversible action?
- **Writer:** can one component serialize it, or must independent lanes submit concurrently?
- **Lifetime:** should it survive a worker crash, worktree deletion, repository reset, or reclone?
- **Namespace:** is identity per project, checkout, run, lane, plan attempt, or transaction?
- **Reconciliation:** does it merge through Git, import by schema and digest, or never merge at all?

From those dimensions, use five classes:

1. **Product state:** versioned repository content. It is isolated in a lane and reconciled with Git.
2. **Control authority:** receipts, lifecycle states, locks, ledgers, integration records, and authoritative decisions. It is canonical, centrally discoverable, and driver-written.
3. **Transaction state:** recoverable records for an in-flight mutation. It is central but namespaced to the exact attempt and records phase-before-cleanup.
4. **Lane evidence and proposals:** agent-produced output, decision proposals, logs, test hints, and completion claims. It is untrusted until imported or independently reproduced.
5. **Reconstructible cache/telemetry:** safe to delete and regenerate. It is shareable only when the underlying tool documents safe concurrent writers and sound invalidation.

### Classification table

| Artifact or state | Primary class | Canonical writer | Recommended location | Why and how it is reconciled |
|---|---|---|---|---|
| Tracked source, tests, documentation, configuration edits | **PER-LANE agent work** | Worker in assigned lane | Lane worktree and `aw/lane/<run>/<lane>` branch | Git is the reconciliation mechanism. The driver inspects actual changed paths and commits before integration if needed. |
| Main-checkout tracked but uncommitted content | Local workspace overlay, not part of the Git base | User; driver snapshots only with explicit policy | Original checkout unless run starts in explicit snapshot mode | `git worktree add <HEAD>` does not include it. Recommended integration runs require a clean tracked main checkout. Snapshot mode must record and separate the borrowed baseline from the agent delta. |
| Untracked product artifact intentionally requested by the plan | **PER-LANE agent work** | Worker | Lane worktree until classified | The driver must not delete it merely because Git ignores it. It is either added, explicitly discarded with policy, or preserved for review. |
| Required untracked/ignored local input | Lane input evidence, not authority | Driver materializer | Same logical repo-relative path in lane when software expects it, or `input/` for task-only material | Copy or copy-on-write with source digest and policy. Never symlink or hard-link back to the original checkout. Compare before/after digest to detect agent modification. |
| Lane contract and input manifest | Driver projection, not authority | Driver | Read-only lane-local `.aw/lane/<run>/<lane>/` | Lets hooks and the agent understand scope without central access. Canonical authorization remains in control state; the driver verifies the projection digest. |
| Begin receipt or execution authority token | **SINGLE-SOURCE machine-state** | Driver only | `control/receipts/<run>/<lane>/<attempt>.json` | It authorizes a specific checkout, plan digest, lane, scope, base commit, input-manifest digest, and attempt. The driver creates it before launch and consumes/finalizes it. No copy enters a lane. |
| Run manifest and append-only event ledger | **SINGLE-WRITER driver-state** | One driver holding run lock | `control/runs/<run>/` | This is the source of truth for scheduling and state. Worker facts arrive through captured events or submissions and become truth only after driver validation. |
| Run lock | **SINGLE-SOURCE machine-state** | Driver lock abstraction | `control/runs/<run>/locks/driver.lock` | The held OS lock is authority. PID, process start, host, and boot/session ID are diagnostics for recovery. |
| Checkout integration lock | **SINGLE-SOURCE machine-state** | Integrator | `control/integration/lock` | It serializes candidate construction and target ref update across runs. It is distinct from a run driver lock. |
| Process stdout, stderr, and structured host events | **SINGLE-WRITER driver-state** | Driver captures streams | `control/runs/<run>/sessions/<lane>/` | The worker emits bytes; the driver owns the durable file, timestamps it, and records truncation or parser failures. |
| Optional outcome JSON | **PER-LANE agent evidence** | Worker | Lane-local `submissions/outcome.json` | Advisory. Validate IDs/schema/digest, then compare it with observed Git state. Missing or inaccurate JSON cannot erase work or declare success. |
| Decision proposals and deferred questions | **PER-LANE agent evidence** | Worker | Lane-local `submissions/decisions.jsonl` or structured final response | Semantic proposals, not authority. The driver imports, deduplicates, assigns stable IDs, and may request closure for omissions. |
| Authoritative decision register | **SINGLE-WRITER driver-state** | Driver | `control/runs/<run>/decisions/` | Structured records are canonical. Human-readable Markdown is generated from them, avoiding concurrent appends. |
| Execution report | **SINGLE-WRITER driver-state** | Driver projection | `control/runs/<run>/reports/` | Regenerated from ledger, Git observations, verification, and imported proposals. Agents do not edit it. |
| Durable project report/decision publication | Tracked product record derived from control state | Driver publication service | Dedicated publication candidate, ultimately tracked `.aw/records/...` | Sanitized projection of completed control events. It is merged and validated like product code; live receipts, locks, sessions, and journals remain untracked machine state. |
| Finalize journal | **SINGLE-SOURCE transaction state** | Coordinator lifecycle service | `control/transactions/<run>/<lane>/<attempt>/finalize.json` | Binds phases to worktree, branch, base, observed tip/tree, receipt, and candidate commit so restart is idempotent. |
| Runtime layout migration journal | **SINGLE-SOURCE transaction state** | One migration coordinator | `control/transactions/migrations/<tx-id>/` | State relocation is an owned machine transaction, not a directory copy performed independently by lanes. |
| Worktree/branch allocation and leases | **SINGLE-WRITER driver-state** | Scheduler | Ledger events plus `control/lane-registry.json` snapshot | Persist enough to reconstruct from Git after a crash. The present in-memory lease table is not sufficient by itself. |
| Prompt template version, rendered prompt digest, host capability snapshot | **SINGLE-WRITER driver-state** | Runner | Run/lane manifest | Makes compliance behavior reproducible and allows prompt changes to be measured rather than guessed. Do not store secrets or full environment dumps. |
| Hook rejection and remediation events | **SINGLE-WRITER driver-state** when observable | Driver or hook event collector | Run event ledger | Useful feedback and metrics. Absence does not prove compliance because hooks are bypassable. |
| Locally relevant nontracked lane output | Local retained artifact | Worker creates; driver harvests | `control/artifacts/<run>/<lane>/local-retained/` plus manifest | Copy and verify before teardown. Apply retention/size/privacy policy; optionally promote a sanitized item through the publication service. |
| Ephemeral secrets or credentials materialized for a task | Restricted local input | Driver secret injector | Lane-local ephemeral path, outside Git and excluded from ordinary logs/artifact bundles | Provide only when needed. Record metadata/digest policy without secret value; never publish; revoke and securely remove according to platform capability. |
| Dependency/tool caches | Reconstructible, generally **PER-LANE** | Tool process | Lane-local or safe platform cache keyed by content/toolchain | Never treat a cache as lifecycle truth. Share only documented concurrent caches. |
| Worktree directory | Disposable machine substrate | Driver | `worktrees/<run>/<lane>/` under checkout state | The directory is not authority. The branch, journal, and observations must allow recovery when it is absent. |

### Receipt ownership does not mean agent tool compliance

A begin receipt is associated with a lane but it is not lane-owned. The correct invariant is:

> Before the runner grants product write access, the driver has durably recorded authorization for the exact attempt.

It is not:

> The agent must remember to run `aw ipd begin` before its first edit.

If `begin` is mechanical, the driver runs it. If authorization depends on information the agent must discover, use a read-only discovery phase, have the driver validate the discovery output, create the receipt, and only then resume the same session with write access. A prompt cannot create a reliable before-edit barrier because models can edit with ordinary shell or built-in file tools.

### Outcome and decisions need different truth models

The driver can derive the product outcome from observable facts: baseline, branch tip, working tree, index, untracked files, test results, and process events. It cannot always infer *why* a material design choice was made. Therefore:

- Missing outcome JSON is a recoverable completeness problem, not lost work.
- Missing decision attribution can be a finalize blocker when a defined material-decision predicate is triggered.
- A generated closure turn receives the actual changed files, diff summary, failed/passed checks, and known decisions. It is asked only to explain or classify observed choices and unresolved risks.
- The driver stores that response as a proposal, validates identifiers, and records the authoritative decision event.
- If closure remains incomplete, preserve the lane and mark it `BLOCKED_DECISION`, never silently integrate and never destroy it.

Define "material" narrowly and mechanically where possible: public API/schema changes, dependency additions, security boundary changes, migration choices, scope expansion, deviations from explicit IPD constraints, or driver-detected alternatives with durable consequences. Requiring a record for every coding micro-choice would create noise and train the model to ignore the mechanism.

### Durable, local-retained, secret, discardable, and unknown

Before worktree teardown, the driver must place every changed or newly created item in exactly one retention class:

| Retention class | Final disposition | Teardown condition |
|---|---|---|
| `tracked-publish` | Included in the product/publication candidate and committed through Git | Exact blob/tree is reachable from the recorded candidate commit |
| `local-retain` | Copied to the checkout control artifact store with path, size, mode, digest, provenance, and retention deadline | Destination digest verified and harvest event durable |
| `secret-local` | Never tracked or placed in ordinary logs; retained only if explicit restricted policy requires it | Revocation/removal or restricted transfer is recorded without secret content |
| `discardable` | Known cache/temp/build output covered by explicit path and producer policy | Discard authorization records matched rule; broad globs and "ignored means disposable" are forbidden |
| `unknown` | Worktree and branch remain preserved | Human or deterministic policy reclassifies it; teardown is blocked |

This table answers the retention question directly: tracked durable work is retained through Git; useful nontracked work is retained through a verified local artifact manifest; secrets follow a separate restricted path; known caches can be discarded; and unknowns can never disappear merely because they were ignored.

## 3. Mechanism comparison across the four optimization axes

Scores are relative, with **5 best**. Simplicity includes ongoing maintenance and recovery, not merely initial implementation.

| Mechanism | Simplicity / maintenance | Ownership cleanliness | Concurrency robustness | Portability | Conclusion |
|---|---:|---:|---:|---:|---|
| **Typed resolver + out-of-repo control plane + manifest-assembled lane** | **5** after bounded cutover | **5** | **5** | **5** with platform adapters | **Recommended.** One path authority, no copied receipts, no shared worker writes, explicit local inputs/outputs, no inventory of links, ordinary Git lanes. |
| Typed resolver + `$GIT_COMMON_DIR/aw/` control plane | 5 | 3 | 5 | 4 | **Runner-up.** All linked worktrees naturally agree, but AW state is mixed with Git-private administration and may be read-only, relocated, or discarded by repository management. |
| Typed resolver + main checkout's ignored `.aw/state` | 4 | 3 | 4 | 5 | Good transitional location. It still binds machine truth to a mutable working tree and exposes an external path to workers if passed through. |
| Bare `AW_STATE_ROOT` environment override | 3 | 2 | 2 | 5 | Useful transport for an already typed context, insufficient as architecture. It says where, not who may write or how classes reconcile. |
| Runner-passed config object/handle | 5 | 5 | 5 | 5 | Part of the recommendation. Pass opaque identity and role, not a shared writable path to worker code. Coordinator services receive the full resolver/capability. |
| CWD heuristic such as "inside `.aw/worktrees` means find main" | 4 initially | 1 | 2 | 4 | Reject. Topology-dependent magic fails with external worktree paths, nested repos, renamed directories, and alternate callers. |
| Symlink selected ignored directories to main | 2 | 2 | 2 | 2 | Reject. An incomplete-set maintenance trap; real targets remain external; shared races remain; loops and Windows behavior add hazards. |
| Bind mount selected directories | 2 | 3 | 3 | 1 | Reject as default. It hides path topology without fixing writer ownership and adds privileged lifecycle/cleanup. Useful only inside a broader sandbox design. |
| Copy/populate ignored state into every lane and harvest | 2 | 3 | 3 | 4 | Use only for bounded lane inputs/submissions. Copying authority creates forks and reconciliation rules for every future artifact. |
| Full/local/`--shared` clone plus copy/harvest | 2 | 3 | 3 | 4 | A clone still omits ignored working files. Local optimizations add documented race or object-lifetime coupling. [[R4](#references)] |
| Main worktree plus scratch paths and declared leases | 3 | 2 | 2 | 5 | Reject. A general coding agent can write undeclared paths, so product changes again contend in one working tree. |
| Container/OS sandbox per lane | 1-3 | 5 | 5 | 1-3 | Optional hardened profile. It can enforce writable roots but still needs the same state taxonomy, driver, and integration protocol. |

### Why the recommendation is one resolver, not one shared root

Use a typed `ExecutionContext` with named accessors:

```text
ExecutionContext
  project_id                 portable logical identity
  checkout_id                machine-local exact Git checkout identity
  run_id / lane_id / attempt_id
  role                       coordinator | worker | verifier
  host_capabilities          permission/events/resume/sandbox features

PathResolver
  control_run_dir()          coordinator only
  receipt_path()             coordinator only
  transaction_path()         coordinator only
  lane_worktree()            role-aware
  lane_input_dir()           worker readable
  lane_submission_dir()      worker writable, optional
  integration_candidate()    coordinator only
```

Do not let modules concatenate `repo / ".aw" / "state"` or a generic environment root. A generic root silently recreates the existing ownership ambiguity at another location. Path methods must enforce the artifact class and execution role. Worker lifecycle verbs should return a deterministic error such as `AW-LIFECYCLE-ROLE-001: runner owns begin/finalize for managed lanes`.

The coordinator can export selectors to child processes if inner read-only `aw` commands need context:

```text
AW_CHECKOUT_ID=<opaque id>
AW_RUN_ID=<run id>
AW_LANE_ID=<lane id>
AW_ATTEMPT_ID=<attempt id>
AW_EXECUTION_ROLE=worker
AW_LANE_ROOT=<absolute lane path>
```

Do not export the control-root path or coordinator capability. Environment variables are not secrets from a same-user worker, but reducing ambient knowledge prevents accidental access. The coordinator passes its capability in-process or through a private descriptor that is never inherited by worker subprocesses.

### Resolution order

1. In-process `ExecutionContext` created by the coordinator.
2. Pinned opaque IDs in a child environment, resolved through the local checkout registry.
3. Exact canonical Git common-directory registry match.
4. Exact canonical main-checkout path for a legacy unattached checkout.
5. Origin URL as a diagnostic hint only. Ambiguity fails closed.

Never derive a fresh checkout ID from a linked worktree path. The inspected `project_registry.py` already prioritizes exact common-directory matching, while the active drivers and lifecycle code bypass the abstraction in key places. The migration should consolidate existing `project_context.py` and `project_registry.py`, not introduce a third resolver. [[R1](#references)]

### Recommendation and runner-up

The recommendation separates **identity** from **storage**: use Git's common directory to recognize a checkout, but put AW-owned runtime state in an AW-owned platform directory. On Linux use `$XDG_STATE_HOME/agent-workflows`, with `~/.local/state/agent-workflows` fallback. The XDG specification defines this category as state that should persist across application restarts but is not portable data. [[R6](#references)] Use platform-native application-state directories on macOS and Windows behind the same helper.

The runner-up puts control data under `$GIT_COMMON_DIR/aw/`. It needs less registry resolution and all linked worktrees see the same location. However, Git's administrative directory is not a general application storage contract. It may be managed, read-only, relocated, or discarded by clone/reclone operations. It also makes backup and ownership boundaries less obvious. Use it only if avoiding a local registry materially outweighs those concerns.

### What current code implies

At the inspected snapshot:

- `project_context.py` already models logical system/config/state/records roots and supports an external per-project root.
- `project_registry.py` already probes `git rev-parse --git-common-dir` and matches common directory before checkout path or origin.
- `oc_runipd.py` and `agy_runipd.py` still construct the run root relative to the repository, copy receipts into lane worktrees, and put main-run absolute paths in worker prompts.
- `ipd_lifecycle.py` still anchors receipts and journals under worktree-relative `.aw/state`.
- `worktree_lease.py` creates the right broad isolation substrate, but its active lease table is in memory.
- OpenCode runs with lane cwd and `--dir`; its current single-lane integration validation callback does not validate an actual merged candidate.

This is a resolver-adoption, ownership, and runner-protocol cutover rather than a greenfield rewrite. [[R1](#references)]

## 4. Isolation-substrate analysis

### Git worktree: retain as the default

Git worktrees are the best product data-plane primitive for this use case. Git documents linked worktrees as sharing repository data while keeping per-worktree state such as `HEAD` and the index, and supplies lock, repair, remove, prune, and stable porcelain-listing operations. [[R2](#references)]

| Property | Git worktree assessment |
|---|---|
| Setup | Fast, no duplicate object database, one branch and checkout per lane |
| Inner tool consistency | Correct once AW control resolution is cwd-independent; wrong if inner `aw` still assumes `.aw/state` under cwd |
| Merge-back | Excellent local branch provenance and ordinary merge semantics |
| Disk | One working tree per lane plus shared objects |
| Portability | Strong across supported Git platforms; still test Windows paths, locks, and process cleanup |
| Isolation | Filesystem edit separation only; not a security, credential, process, or network sandbox |

Ignored files are not populated because a worktree checks out Git objects and index content, not arbitrary ignored files from another working directory. That behavior is generally true of Git checkouts. The architectural error is expecting machine runtime files to follow product source automatically, not choosing worktrees. [[R2](#references), [R3](#references)]

Allocate uniquely across retries and concurrent runs:

```text
branch:   aw/lane/<run-id>/<lane-id>/<attempt-id>
worktree: <checkout-state>/worktrees/<run-id>/<lane-id>/<attempt-id>
```

Use `git worktree add --lock --reason "aw run <run-id> lane <lane-id>" ...` while active or deliberately preserved. Record branch, path, base, and lock reason durably. Never force-remove a lane until all work is classified and the ledger contains a teardown-authorized event.

### Full clone, local clone, and `--shared` clone

A full clone does not solve ignored machine state. It checks out tracked files, so AW would still need a copy/populate/harvest protocol. It duplicates more Git administrative state and turns local merge-back into fetch/push/bundle coordination between repositories.

Git documents that local clone optimization may hard-link objects and warns of a race with concurrent source changes. It also warns that `--shared` alternates can become corrupt if source-side maintenance removes objects still needed by the dependent clone. [[R4](#references)] A fully independent clone is justified only when lanes must not share Git refs or object administration, which is a stronger and different requirement.

### Worktree plus deliberately populated ignored files

Use this only for a finite, schema-defined exchange surface:

- Driver-provided plan snapshot, prompt packet, or read-only input.
- Optional lane outcome, decision proposal, and closure marker.
- Test artifacts explicitly useful for diagnosis.

Do not populate receipts, ledgers, locks, reports, or lifecycle journals. A hand-maintained copy list for open-ended runtime state will lag the codebase and silently lose new artifacts. A small lane mailbox is safe because its schema and harvest precondition are deliberate.

Even the mailbox should not be required for correctness. The driver captures stdout and host events and inspects the lane after exit. Teardown checks for any unclassified ignored/untracked content, not only expected mailbox names.

### Lane assembly: make the original checkout unnecessary

The best way to reduce requests for files in the original checkout is not a stronger prohibition. It is to make the lane complete before the model starts, tell it that the lane is complete, and give missing inputs a safe recovery path that never grants original-checkout access.

The driver should assemble each lane in this order:

1. **Committed base:** create the worktree from the recorded base commit. For unattended integration, require the target checkout to have no tracked staged or unstaged changes. A worktree created from `HEAD` does not contain such changes. If dirty-base snapshot mode is later added, treat the user's snapshot as a separate immutable baseline and integrate only the agent delta; do not conflate both in one merge.
2. **Task and policy packet:** place the exact IPD/task snapshot, all applicable recognized repository policy files, the rendered lane contract, and any attached inputs in lane-local paths. Rewrite prompt references to lane-relative paths.
3. **Declared local inputs:** apply tracked rules such as `.aw/config/lane-inputs.toml` plus task-discovered references. Copy required untracked or ignored files into the lane at the same repo-relative path when application discovery requires that location; otherwise place them under the lane input directory.
4. **Toolchain/dependency environment:** do not assume an ignored main-checkout `.venv`, `node_modules`, SDK, or generated schema exists in the lane. Point to an explicitly approved read-only environment outside the original checkout, create a lane-specific environment, or materialize the minimum required content. Pre-run a cheap tool-discovery/test-collection probe.
5. **Secrets:** inject only task-required secret/config values through a dedicated policy. Do not copy `.env`, credentials, SSH state, cloud config, or token-bearing files merely because they are ignored. Prevent them from entering prompts, logs, commits, or ordinary artifact bundles.
6. **Escape scan:** reject or explicitly classify repo-relative symlinks whose resolved targets leave the lane. Copies or copy-on-write reflinks are acceptable after digest verification; symlinks and hard links back to the original checkout are not, because they reintroduce mutation and permission coupling.
7. **Manifest seal:** write a lane-local read-only projection of the input manifest and record its digest in canonical control state. Then run the actual command/test discovery expected by the task. Missing essentials fail before model launch.

An input manifest entry should include at least:

```text
repo_relative_path
class: tracked-base | task-input | local-input | toolchain | secret
source_identity                 path or secret handle, withheld from worker when sensitive
source_digest / size / mode
materialization: checkout | copy | reflink | generated | external-readonly
worker_policy: readonly | editable | executable
retention: tracked | local-retain | secret-local | discardable
```

Do not automatically copy every untracked/ignored file. That would import caches, build output, virtual environments, large datasets, credentials, sockets, and the AW control plane. Instead, combine explicit project rules, exact task references, known toolchain adapters, and a preflight inventory. Always exclude `.aw/state`, ignored run directories, `.aw/worktrees`, central control roots, sibling lanes, Git administration, and known secret stores.

### Missing-input recovery without original-checkout access

The lane contract should define one deterministic failure form:

```text
AW_MISSING_INPUT:<repo-relative-path>:<why it is required>
```

When the agent or a tool reports it, the driver should:

1. Preserve and pause the lane rather than opening an interactive permission prompt.
2. Resolve the requested path against the original checkout only in coordinator code.
3. Reject control paths, sibling lanes, secrets not authorized for the task, broad directories, and paths outside the checkout.
4. If policy permits, copy a digest-verified snapshot into the lane, append a new manifest revision, record a corresponding authorization amendment or new attempt, and resume the same session or a new attempt with the change stated explicitly.
5. If policy does not permit it, block with a precise missing-input record.

An external-directory permission event that points into the original checkout can use the same classification path: deny the live access, preserve the event, and consider materializing a safe copy on resume. Never auto-approve the original path. This transforms a likely hang or request for permission into a bounded input-repair cycle.

### Environment and path hygiene

The runner should remove inherited path hints that accidentally point agents or tools to the original checkout, including stale `PWD`/`OLDPWD`, explicit `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, and checkout-specific `PYTHONPATH` or tool configuration. It should then construct a minimal task environment from policy. This is not a security boundary, but it prevents many accidental fallbacks.

The generated task packet should say:

> Your current working directory is the complete authorized repository workspace for this task. Treat it as the repository root. Do not inspect parent directories, the original checkout, or other worktrees. If an expected repository file is missing, emit `AW_MISSING_INPUT:<relative-path>:<reason>` and continue with independent work; do not request external-directory access.

The runner should inject this lane contract at the strongest host-supported instruction level, repeat its short form after session resume or context compaction, and propagate it into subagent/task prompts. A single root user-message instruction is insufficient if child sessions do not inherit it, which must be verified for each host.

### Overlay and bind mount

A bind mount can make a central path appear to be inside a lane, but path appearance is not ownership. Multiple agents would still write the same files, and the system would gain mount privileges, aliasing, cleanup, crash recovery, and OS-specific behavior. It is a poor default and a particularly expensive way to appease one permission classifier.

An overlay can give each worker a writable view while keeping a common base. It then needs a whiteout-aware export and reconciliation protocol, which is more complex than a Git branch for a source repository. Neither mechanism removes the need for central authority state.

### Container or OS sandbox

A container, mount namespace, macOS sandbox profile, Windows restricted token/ACL scheme, or separate OS principal can provide a genuine write boundary. In the hardened profile:

- Writable: lane worktree, lane scratch, explicitly selected build caches.
- Read-only: required toolchain/dependencies and perhaps repository policy files.
- Inaccessible: control root, main worktree, sibling lanes, integration candidate, unrelated user files, credentials not needed by the task.
- Network: disabled or narrowly scoped according to task policy.
- Process: child tree attached to a killable group/job.

This is the only reliable way to prevent an arbitrary shell-capable process from writing central files before or during editing. A linked worktree adds one subtlety: its `.git` file points into the shared Git common directory. If that directory is writable, the worker can potentially mutate shared refs, configuration, hooks, or other worktree administration even when it cannot write the main working files. Hardened mode must therefore keep the common directory read-only to the worker and make the driver own staging and commits. If the worker must have unrestricted Git-write capability, use an isolated clone or a narrowly mediated Git service for hardened mode rather than claiming a worktree is a security boundary. This has real maintenance costs across platforms, so keep it as a host capability/profile. The control-plane design remains identical with or without it.

In the operational default, snapshot protected refs, repository configuration, hook configuration, and `git worktree list --porcelain -z` before launch. After the process tree stops, permit only the expected lane ref and per-worktree changes; any other mutation blocks integration and preserves evidence. This is detection, not prevention, but it closes a major silent-failure gap.

### Why main-tree path leases are insufficient

Declared path leases are useful scheduling hints: they can avoid knowingly parallelizing plans that claim the same files. They cannot confine a general coding agent to declared paths, and they do nothing for newly created or renamed paths. Worktrees limit accidental cross-lane working-file interference; the driver later compares actual changed paths against leases. Do not replace worktrees with trust in scope declarations.

## 5. Merge-back and cross-lane dependency handling

### Lane result formation

At worker exit, do not assume `HEAD` contains all work and do not require the agent to have used a commit tool correctly. The driver should:

1. Record process exit, termination cause, and the final structured-event position.
2. Run `git status --porcelain=v2 -z`, inspect staged/unstaged diffs, enumerate untracked and ignored lane-exchange files, and record lane `HEAD`.
3. Compare actual changed paths with declared scope and forbidden paths.
4. Preserve any product changes. In the simplest policy, require a clean committed lane and give the agent a corrective closure turn. In the more robust policy, the driver creates a clearly attributed checkpoint commit after validation of file classification.
5. Import optional submissions by schema/digest, while treating observed Git state as authoritative.
6. Run lane-level tests against the exact candidate tree.

Driver-owned checkpoint commits are an optional further hardening and simplification. They remove reliance on agent commit discipline and make `base..tip` complete. The trade-off is that the driver must generate a commit message and preserve any intentional split-commit structure. A sensible default is: accept valid agent commits, but if tracked changes remain, create one driver checkpoint commit labeled with run/lane/attempt metadata after scope checks. Never silently commit credentials, large generated files, or unknown ignored content.

### Output harvest and durable publication

Before integration or teardown, compare the final lane with both the Git base and the sealed input manifest:

- An unchanged materialized local input is neither an output nor something to recopy.
- A modified materialized local input is a lane output and must be reclassified. The driver must never write it back over the original source automatically.
- Tracked product changes become the lane Git delta.
- Known useful nontracked outputs are copied into `control/artifacts/<run>/<lane>/local-retained/` with a manifest and verified digest.
- Secret-class files take the restricted secret path and are excluded from ordinary reports and bundles.
- Explicit cache/temp rules authorize discard.
- Any unknown file, type change, escaping symlink, oversized artifact, or failed copy blocks teardown and preserves the lane.

For local artifact harvest, stop and verify the complete worker process tree first, copy rather than link, enforce size/count quotas, preserve the relative path and mode needed for reuse, and record source and destination digests before authorizing deletion. A content-addressed store can deduplicate large local artifacts later, but a simple per-run copy with a verified manifest is the lower-maintenance first implementation.

Live machine control state and durable project records need not be the same files. When a completed run should leave tracked decisions, reports, walkthroughs, or plan records, the driver renders a sanitized projection from the canonical ledger into a driver-owned publication candidate. Merge that projection with the product lane result and validate the combined tree. This preserves durable tracked history without allowing agents to edit the live report or decision register and without putting receipts, locks, session logs, raw prompts, or recovery journals into Git.

### Integration algorithm

Do not validate a textual diff and then merge some other tree. Validate the exact candidate that may become the target:

1. Acquire the checkout-level integration lock.
2. Read and journal `expected_target_tip`.
3. Create a temporary integration worktree/branch at that tip.
4. Merge the lane tip there using the repository's declared strategy. A fast-forward-only policy is simplest when topology permits; Git documents that `--ff-only` refuses rather than creating a merge when the update is not a fast-forward. [[R5](#references)]
5. If merge conflicts occur, abort the candidate merge, preserve the lane, record conflict paths, and request a rebase/reconciliation lane. Do not resolve conflicts in the user's possibly dirty main worktree.
6. Run all required integration checks in the candidate worktree.
7. Re-read the real target tip. If it differs from `expected_target_tip`, discard or retain the candidate for diagnosis and rebuild against the new tip.
8. Update the target ref/worktree through a controlled, journaled operation. If the user's main working tree is dirty, pause or use a designated integration branch according to explicit policy. Never auto-stash or overwrite unrelated user work.
9. Include any driver-owned durable record projection in the same candidate or a deterministically ordered publication candidate, then validate the final combined tree.
10. Record integrated commit, validation evidence, local artifact harvest manifest, and cleanup authorization before removing the lane.

The inspected `orchestrate_isolation` gate works with diffs/changed files and a callback, while current single-lane validation can return true before Git merge. Replace that with an actual candidate worktree. [[R1](#references)]

### Dependencies between lanes

Use an explicit dependency DAG. "B depends on A" must mean whether B needs A's specification only or A's integrated code.

| Dependency case | Scheduling/base rule | Rationale |
|---|---|---|
| No result dependency | A and B branch from the same accepted target tip and may run concurrently | Maximum parallelism; conflicts handled during ordered integration |
| B needs A's committed product result | Do not start B until A is verified and integrated; branch B from the new target tip | Simplest provenance and recovery; B never depends on an unaccepted lane |
| Speculative B on A is explicitly valuable | Branch B from A's immutable lane tip and record `upstream_lane=A` plus exact commit | Allows latency hiding but couples fate; if A changes/rejects, B must be rebased or discarded and revalidated |
| A and B both touch a high-conflict surface | Serialize despite DAG independence | A lease/conflict predictor is a scheduling optimization, not a safety boundary |

The default should be staged merge order: integrate A, then create B. Chaining B directly from A's unintegrated tip is an optimization to enable only when expected latency gain exceeds likely rework.

### Stale bases and conflicts

- A lane is not invalid merely because target advanced. Rebuild the integration candidate on current target and test the actual merge.
- Never force-push or silently rebase an agent branch after evidence has been recorded. Create a reconciliation attempt/branch so the old tip remains auditable.
- Record conflict paths and both tips. A new model turn may resolve in the isolated candidate or a dedicated reconciliation lane, never in shared main.
- Every dependent lane records the exact upstream commit, not only a lane name.
- Integration remains serialized even if execution is parallel.

## 6. The permission-deadlock layered defense

The permission deadlock and agent forgetfulness have the same architectural answer: remove voluntary tool use from the correctness path, then add multiple early-feedback layers.

### Layer 1: keep ordinary worker I/O internal

The generated prompt names only paths under the lane worktree. It does not tell the agent where the main checkout or control root lives. Input and optional submissions are lane-local. The driver captures process streams externally and generates reports itself. This makes `external_directory` unnecessary in the normal run.

Set unattended OpenCode policy to deny unexpected external-directory and interactive-question requests. OpenCode documents `allow`, `ask`, and `deny`; `external_directory` defaults to `ask`, and `--auto` is intended to auto-approve permission requests. Current issue reports nevertheless describe nested subagent permission asks hanging non-interactive `opencode run --auto` sessions, so the documented intent must not be the only defense. [[R8](#references), [R10](#references), [R11](#references)]

Prefer deny over broad allow. An unexpected external path is normally a lane-containment defect. A denial produces a repairable tool failure; broad auto-allow can mutate main or another lane. If a task truly requires a registered compiler, SDK, dependency store, or dataset outside the lane, grant the narrowest read-only path and operation in runner-supplied configuration, never a blanket filesystem grant. The original checkout, control root, sibling lanes, and integration candidates are never eligible for such a convenience grant; required repository content is materialized instead.

OpenCode documents runtime config via `OPENCODE_CONFIG_CONTENT` and its precedence rules. Use the host adapter to pass an exact, versioned policy without editing repository config, then verify at startup that managed/higher-precedence config has not changed the effective policy. [[R9](#references)]

### Layer 2: a short runner-generated execution packet

The runner has a much stronger communication opportunity than a long generic `AGENTS.md`: it knows the exact run, lane, task, paths, phase, and recovery command. Generate a compact packet at launch and a separate closure packet later.

Recommended opening contract:

```text
MANAGED AW LANE: run=<run-id> lane=<lane-id> attempt=<attempt-id>

The runner has already authorized this attempt and owns begin, finalize,
receipts, ledger, reports, and integration. Do not run `aw ipd begin` or
`aw ipd finalize` and do not edit files outside this worktree.

This working directory is the complete authorized repository workspace.
Do not inspect or request the original checkout, parent directories, or other
worktrees. If a required file is missing, report exactly:
  AW_MISSING_INPUT:<repo-relative-path>:<why it is required>
Continue any independent work instead of requesting external access.

When a material plan deviation or durable design choice occurs, use:
  aw lane note decision --kind <kind> --summary <text>
or include it in your final response. This command improves completeness;
the driver will inspect the actual diff regardless.

Report tests, unresolved risks, and material decisions. Do not claim that
your response finalizes or integrates the lane; the driver decides that.
`aw lane status` is available for read-only context or diagnostics, but no
custom AW command is required for the driver to preserve and inspect your work.
```

This instruction is intentionally redundant with enforcement in a few high-value places. It should be near the beginning, use exact identifiers, avoid a catalog of every AW rule, and distinguish mandatory behavior from authority. Do not bury it in a large repository policy document. The runner should still load applicable repository `AGENTS.md` files for coding conventions, then render a clear precedence-aware task packet. Source files and arbitrary comments are task data, not instructions; recognized repository policy files remain applicable unless they conflict with higher-priority runner/system policy.

Version the template and ledger its digest plus variable inputs. Record whether optional note/status commands are used, but optimize primarily for successful work when none are used. This enables controlled prompt changes without pretending the metric is authority.

### Layer 3: run prerequisites automatically

Anything the driver can determine mechanically should happen before launch:

- Resolve checkout/run/lane identity.
- Create and lock worktree/branch.
- Record baseline and scope.
- Create begin receipt and transaction record.
- Validate effective host permission policy.
- Assemble and seal the lane input manifest.
- Run static preflight/tool discovery and mark the attempt authorized.

Do not ask the model to repeat a mechanical preflight that the runner already completed. Expose only a read-only, idempotent `aw lane status` diagnostic and an optional `aw lane note` submission command. Fewer custom verbs improve recall and reduce the chance that an agent mistakes a convenience for a required lifecycle operation. The lane-local contract/manifest lets status and hooks operate without central control access; canonical authorization remains driver-owned.

### Layer 4: phase-gate the exceptional true before-edit prerequisite

If a prerequisite genuinely depends on the agent's analysis, use two phases:

1. **Discovery phase:** repository read access, product tree read-only, only a narrow submission channel writeable. Prompt the agent for scope/choice/evidence.
2. Driver observes the structured event or submission and validates it. A statement in prose alone is insufficient if the host exposes tool events.
3. Driver creates authorization and changes the sandbox or host tool policy to permit product writes.
4. **Execution phase:** resume the same session if supported, or start a new turn with the discovery result injected and write access enabled.

This is the only robust way to force something before an edit. If the host cannot enforce read-only files or phase-specific tools, the barrier is advisory. In that case move the prerequisite into the driver or accept post-edit detection and block integration.

Define a host capability contract rather than scattering OpenCode-specific assumptions:

```text
supports_inline_permissions
supports_read_only_phase
supports_session_resume
emits_structured_tool_events
emits_child_permission_events
supports_process_tree_kill
supports_os_sandbox
```

The shared orchestrator chooses the strongest safe protocol supported by the adapter. `oc_runipd.py` and `agy_runipd.py` should not each reimplement lifecycle, prompt semantics, supervision, and integration.

### Layer 5: Git hooks as corrective feedback

A `pre-commit` hook can reject a commit if scope is violated, forbidden files are staged, an input manifest file was altered, or required decision attribution is known to be missing. It should not reject merely because the agent did not call an optional AW tool. Git documents that a nonzero pre-commit exit aborts the commit, and also that `--no-verify` bypasses it. Hooks run at Git-defined events, not before arbitrary file edits. [[R13](#references)] Therefore:

- Never claim a hook prevents the first edit.
- Never use hook success as integration authority.
- Have the hook and driver call the same pure predicate library so their rules cannot drift.
- Make rejection output short, machine-identifiable, and directly repairable.

Example:

```text
AW-GATE-011: staged path `.aw/records/runs/r123/report.md` is driver-owned.
No commit was created; your working files are unchanged.
Remove that path from the commit and report any intended durable result in your
final response or with `aw lane note decision ...`. Then retry the commit.
The driver will recheck this gate independently.
```

`core.hooksPath` is repository configuration shared through Git administration, so worktree context must be derived explicitly from Git-provided environment and the lane registry. Test multiple simultaneous worktrees. Also account for agents using `git commit --no-verify`, plumbing commands, or not committing at all.

### Layer 6: event-driven deadlock detection and bounded execution

Parse structured host events and fail immediately on an unanswered permission request, especially one attributed to a child/subagent session. Record permission kind, normalized path pattern, session IDs, and last event position. Then terminate the entire process tree. If the denied target is a potentially legitimate file inside the original checkout, route it through the missing-input classifier and resume only after a safe copy is materialized; do not convert the event into a live external grant.

Keep both existing and new time bounds:

- Permission-request deadline: seconds, not minutes.
- No-progress watchdog: resets only on meaningful events, not spinner/heartbeat output.
- Absolute turn deadline: cannot be extended indefinitely by noise.
- Graceful termination window, then process-group/job-object kill.

On termination, immediately enter `OBSERVED`: capture Git state and preserve the lane. A killed model process is not equivalent to failed or absent work.

### Layer 7: independent closure and validation

After execution, generate a closure prompt from facts rather than asking the agent for an unstructured status narrative:

```text
Observed by driver:
- commits: <oids>
- changed paths: <list>
- out-of-scope paths: <list>
- tests: <results>
- detected material changes: <API/schema/dependency/security list>
- imported decisions: <list>

Explain each material change without editing product files. Identify decisions,
deviations, unresolved risks, and tests not run. Do not claim integration.
```

This converts forgotten mid-run reporting into a bounded reconciliation step. It cannot establish objective correctness, so an independent verifier and candidate integration tests remain required.

## 7. Failure-mode and concurrency hazard audit

| Hazard | Failure or ambiguity | Closing guard |
|---|---|---|
| Agent forgets every custom AW tool | Missing outcome/decision/status commands | Driver performs mechanical prerequisites, observes actual state, requests generated closure, and blocks only on unresolved postconditions. Tool calls improve feedback but are not truth. |
| Mechanical prerequisite is mistakenly delegated to agent | Agent edits first or omits it | Runner performs it before launch. If analysis is genuinely required first, enforce a read-only discovery phase; otherwise no before-edit claim is made. |
| Required local file is absent from worktree | Agent requests original checkout or task fails | Input manifest, task-reference scan, tool-discovery probe, and `AW_MISSING_INPUT` repair cycle materialize a safe copy; original path remains denied. |
| Main checkout has tracked uncommitted changes | Lane silently starts from different content | Recommended integration mode requires clean tracked main. Explicit snapshot mode records a separate borrowed baseline and never merges it as agent-authored delta. |
| Useful untracked/ignored main file is absent | Local configuration/data/context silently omitted | Explicit lane-input policy plus task-discovered references; copy/reflink with digest at same logical path; never broad-copy ignored state. |
| Materialized input is modified | Change is written back or discarded incorrectly | Compare final digest to sealed input manifest; treat modification as a new output; never overwrite the source automatically. |
| Symlink or hard link escapes lane | Permission gate fires or original file changes | Pre-launch escape scan; reject, replace with verified copy/reflink, or use narrow read-only external toolchain policy. No links to original checkout. |
| Shared Git common directory is mutated | Agent changes protected refs, hooks, config, or another worktree's administration | Default mode snapshots and verifies protected Git state; hardened mode gives worker read-only Git administration and driver owns commits. Use isolated clone if worker needs unrestricted Git writes. |
| Agent directly edits canonical control files | Corrupt receipt/ledger/report | Do not expose paths or capability; external deny and role guards in default; writable-root OS sandbox/separate principal for hard enforcement; ledger integrity checks detect accidental mutation. |
| Agent final response falsely claims success | Driver might finalize bad or absent work | Never parse prose into lifecycle success without corroboration. Derive status from process, Git, submissions, and tests. |
| Agent omits or falsifies outcome JSON | Work appears lost or success overstated | Treat JSON as advisory; compare IDs/digests with observed base/tip/status/diff; driver generates authoritative report. |
| Missing semantic decisions | Important rationale lost | Material-decision detector plus read-only closure turn; import proposals; unresolved attribution preserves and blocks lane. |
| Worktree-relative state fork | Inner `aw` writes a second receipt/run tree | Typed resolver keyed by checkout ID; worker lifecycle verbs refuse; startup assertion that all linked worktrees resolve same control identity; no cwd heuristic. |
| Receipt copied into lane | Two authorities diverge or are consumed independently | One central driver-created receipt bound to attempt; delete receipt-copy path. |
| Shared agent writes to report/decision Markdown | Interleaving and malformed partial files | Lane-local proposals only; driver is sole structured-record writer and regenerates Markdown views. |
| Partial control-state write | Crash leaves truncated JSON/snapshot | Append events with sequence/checksum; write temp, fsync as policy requires, atomic rename snapshots; journal phase before destructive action. |
| Malicious same-user worker rewrites control root | Policy checks can be bypassed | Explicitly outside default trust guarantee. Use OS sandbox/separate principal; no prompt, hook, MAC in worker-readable environment, or Python role flag can provide this boundary alone. |
| Lane mailbox disappears on teardown | Ignored evidence and work lost | Driver inventories untracked/ignored files, imports by digest, records classification, and requires teardown authorization. Branch/worktree preserved on ambiguity. |
| Unknown ignored files remain | Useful artifact silently deleted | `git status` plus explicit ignored-file inventory under lane; policy classifies preserve/add/discard; unknown means cleanup-required. |
| Locally useful nontracked output is not publishable | It is lost or inappropriately committed | Harvest to local-retained artifact store with source/destination digest, relative path, mode, provenance, retention, and quota; optional later sanitized publication. |
| Cache is mistaken for useful output, or useful output for cache | Storage explosion or silent loss | Discard only exact producer/path rules; ignored status alone never authorizes deletion; unknown blocks teardown. |
| Secret enters Git, logs, prompt, or artifact bundle | Credential exposure | Dedicated secret class/injector; staged secret scan; redaction; exclusion from ordinary harvest; revocation/removal record without value. |
| Agent leaves tracked changes uncommitted | `base..HEAD` misses work | Driver inspects index and working tree; closure or driver checkpoint commit; never merge based only on HEAD. |
| Hook bypass | `--no-verify`, plumbing, no commit | Hooks are feedback only; driver invokes same predicates over final observable state. |
| Hook rule differs from driver | Agent repairs one gate but fails another | One pure policy library with stable error codes used by hook, read-only `aw lane status`, and driver. |
| Hook path context wrong in linked worktree | It reads main/lane identity incorrectly | Resolve via Git common dir plus current worktree and registry; test `core.hooksPath` across concurrent worktrees. |
| Concurrent ledger writers | Interleaved events or lost snapshot | One live driver per run with OS lock; all worker events enter through driver capture; monotonic event sequence and hash chain/checkpoint. |
| Two runs integrate simultaneously | Target moves or merges interleave | One checkout-level integration lock; expected-old-tip recheck; candidate worktree. |
| Validation occurs before actual merge | Passing test does not cover merge result | Merge into candidate first and validate that exact tree. |
| Target advances during validation | Candidate no longer represents update | Compare target tip before ref update; rebuild and revalidate on mismatch. |
| Dirty user main worktree | Merge overwrites or entangles unrelated work | Preflight policy: pause, integrate through designated branch, or request user action. Never auto-stash/reset/overwrite. |
| Merge conflict | Partial merge contaminates main | Conflict occurs only in disposable/preserved candidate; abort safely, record conflict paths/tips, create reconciliation attempt. |
| Scope lease misses undeclared files | Agent changes another lane's logical surface | Worktree contains physical edits; driver inspects real paths before verification/integration. Lease optimizes schedule only. |
| In-memory lease lost on crash | Resume cannot reconstruct ownership | Persist allocation/scope events and lane registry snapshot; reconcile with `git worktree list --porcelain -z`. |
| Branch/worktree name reused | Retry collides or overwrites evidence | Include run, lane, attempt; preserved branch names are immutable recovery anchors. |
| Worker exits or is killed mid-edit | Dirty but valuable partial work | Immediately observe and journal; do not force-remove; offer resume/recovery or checkpoint after classification. |
| Finalize crash before commit | Dirty lane and uncertain phase | Attempt-scoped finalize journal with phase, base, tree/status digest, and owned operations; idempotent recovery. |
| Finalize crash after commit | Commit exists but state says incomplete | Journal candidate commit before cleanup; recovery verifies reachability and resumes post-commit steps without rewriting. |
| Crash during target update | Candidate and target state ambiguous | Journal expected target, candidate commit, update method, and phases; recovery inspects refs and reflogs, never infers from missing process. |
| Orphaned worktree metadata | Path missing or stale administrative entry | Registry stores path/branch/tip; classify before `git worktree repair` or `prune`; preserve branch. Git documents repair and prune. [[R2](#references)] |
| Stale PID lock | Permanent false ownership or unsafe deletion | Prefer OS-held locks released on process death; diagnostics include PID, start time, boot/session ID, and host; consult journal before reclaim. |
| PID reuse | Stale file appears live | Validate process start and boot/session identity, not PID alone. |
| POSIX-only locking | Windows import/runtime failure | Cross-platform lock abstraction. Python documents `fcntl` as Unix-only; inspected active modules import it. [[R12](#references)] |
| Child-agent permission ask is invisible | Headless session hangs | Parse root and child structured events; permission deadline; no-progress and absolute timeouts; kill full process tree. |
| Host `--auto` semantics change | Safety assumptions drift by version | Capability/version probe and a two-level subagent regression test for each supported version. |
| Process child survives parent kill | It continues editing after driver moves on | POSIX process group/cgroup or Windows Job Object; verify tree exit before changing lane state. |
| State root is on filesystem with weak lock/rename semantics | Recovery assumptions fail | Use/test local filesystem requirement or a proven backend; detect/report unsupported placement. |
| Checkout state is deleted or repo recloned | Local evidence unavailable | `aw doctor` reports missing binding/state; export selected durable summaries if audit retention is required; do not pretend machine state is portable project history. |
| Origin URL collision | Wrong clone attaches to state | Origin is hint only; exact common-dir binding or explicit user attachment. |
| Prompt changes silently alter compliance | Regressions look random | Template version and prompt digest in ledger; metrics for optional note/status use, missing-input events, hook rejection, closure completeness, retries, and permission events. |
| Repository text injects conflicting instructions | Worker leaves lane contract | Runner clearly distinguishes recognized policy files from task data; sandbox enforces actual roots; driver validation remains authority. |
| Cleanup exception is suppressed | Leaked branch/worktree hidden | Cleanup result is a ledger event; failure changes run status to cleanup-required and keeps recovery identifiers. |

### Required recovery invariants

A crashed or killed lane is recoverable and unambiguous only when all are true:

1. The ledger durably binds checkout, project, run, lane, attempt, plan digest, scope, base commit, branch, worktree, process/session identity, prompt digest, input-manifest digest, and last completed phase.
2. The lane branch is not deleted until integration or explicit abandonment is durably recorded.
3. Receipts and transaction journals have one canonical location and identify the exact attempt.
4. Driver observations distinguish committed, staged, unstaged, untracked, ignored, and missing content.
5. Submission import is idempotent by content digest and cannot duplicate decisions.
6. Every nontracked output is classified; every `local-retain` copy has a verified source/destination digest; every `unknown` blocks cleanup.
7. Every destructive cleanup has a preceding durable authorization event that names the Git commit, publication result, artifact manifest, and explicit discard rules it relies on.
8. Recovery verifies protected refs/Git administration plus filesystem/process facts and fails closed on disagreement. It never infers success from an absent process, file, or directory.
9. `aw recover <run-id>` can reconcile ledger, refs, `git worktree list`, locks, journals, candidates, input/output manifests, harvested artifacts, and lane content without model assistance.

### Integrity without overengineering

An append-only JSONL ledger with monotonic sequence, previous-event digest, atomic snapshots, and one OS-locked writer is enough to detect accidental truncation/replacement and recover after ordinary crashes. Do not mistake a hash chain for protection against a same-user malicious worker that can rewrite the entire chain. Use filesystem isolation for that threat. This distinction keeps the default design simple and honest.

### Adversarial acceptance tests

The most valuable tests should deliberately model the behavior that motivated this revision:

- A "forgetful agent" edits directly, never runs any custom AW command, writes no outcome JSON, and exits zero. The driver must still observe, validate, report, and either integrate or block truthfully.
- An agent uses `git commit --no-verify`; the driver must independently reject the same violation.
- An agent does not commit; the driver must preserve all tracked/untracked work.
- An agent claims tests passed when they did not; verifier result wins.
- A plan references an approved untracked file that is absent from the worktree; preflight materializes it or the missing-input cycle resumes safely without external access.
- An agent changes a materialized local input and creates an ignored useful output; both are classified and retained without modifying the original source.
- An ignored cache tree and an unknown ignored file coexist; only the explicit cache is discarded and the unknown blocks teardown.
- An agent attempts to update the target ref or shared hook configuration; default mode detects and blocks it, while hardened mode denies it.
- A nested subagent requests external permission; the runner must fail fast, kill the tree, and preserve the lane.
- An agent tries main/control/sibling-lane writes in hardened mode; the OS must deny them.
- Crash injection at every journal boundary: input manifest seal, receipt, process launch, observation, checkpoint, submission import, artifact harvest, candidate merge, publication, validation, target update, and cleanup.
- Two runs finish simultaneously; exactly one integration candidate proceeds at a time and the second rebuilds if target changes.
- Windows tests cover locking, process-tree kill, case normalization, long paths, and worktree cleanup.

## 8. Incremental migration path from the current implementation

The migration should first remove the live failure and agent-compliance assumption, then relocate state. Do not attempt a big-bang filesystem move before the writer model is correct.

### Phase 0: define invariants and add characterization tests

1. Freeze the state taxonomy and assign every existing path a class, namespace, writer, retention rule, and migration owner.
2. Add characterization tests for current `aw oc run <id6>` and `aw agy run` behavior, including inner `aw`, receipt creation/copy, outcome/report paths, dirty exits, and teardown.
3. Inventory committed, tracked-dirty, untracked, ignored, symlinked, toolchain, secret, and generated content in representative real repositories so lane-input rules reflect actual practice rather than a toy checkout.
4. Add the forgetful-agent, missing-input, hook-bypass, protected-ref mutation, and nested-permission-deadlock tests above.
5. Define stable error codes and one pure gate library for runner, hook, lane status, finalize, and integration.

### Phase 1: stop the active deadlock and silent loss

1. Change generated worker prompts so every named worker input/output path is inside the lane.
2. Stop requiring the worker to write decisions, report, or outcome into the main run directory. Capture stdout/events; allow lane-local structured submissions.
3. Require a clean tracked target checkout for unattended integration. Fail before model launch rather than silently omitting local tracked changes.
4. Add a minimal input manifest that copies the task/IPD and explicitly referenced safe local files into the lane. Add the `AW_MISSING_INPUT` response contract and never auto-approve original-checkout access.
5. Pass runner-local OpenCode configuration that denies unattended `external_directory` and `question` asks except explicitly scoped cases.
6. Parse permission events, including nested sessions, and add a short permission deadline. Retain the existing no-progress watchdog and add an absolute deadline.
7. Inventory all lane content before teardown. Preserve on unknown ignored/untracked content, dirty tracked files, unimported submissions, unresolved transaction, or unrecorded commit.
8. Include run and attempt in branch/worktree names.

At this phase, central state may temporarily remain under the main checkout's ignored `.aw/` directory. The immediate invariant is that the worker neither needs nor is instructed to access it.

### Phase 2: move lifecycle authority fully into the runner

1. Before agent launch, the driver performs `begin`, writes the canonical receipt, records baseline/scope/policy, and marks `AUTHORIZED`.
2. Replace worker lifecycle calls with coordinator service calls. Worker-role `aw ipd begin/finalize` returns a corrective noninteractive error.
3. Implement `OBSERVED` from Git/process facts and make agent output advisory.
4. Implement full lane assembly: project input rules, task-reference resolution, toolchain probe, symlink escape scan, secret separation, environment sanitization, and sealed contract/input-manifest projections.
5. Implement the five-way output classifier and verified local artifact harvest. Unknown content blocks teardown.
6. Add one optional, idempotent, read-only `aw lane status` command and one optional `aw lane note <decision|defer>` command that writes only to the lane submission surface or emits structured stdout.
7. Generate the short opening execution packet and read-only closure packet from templates. Inject the short lane contract into child sessions and after resume/compaction where the host permits. Ledger template version/digest.
8. Add the shared gate predicate to pre-commit for early repair, while keeping the driver recheck authoritative.
9. Decide the dirty-exit policy: corrective commit turn or driver checkpoint commit after classification.

This phase directly addresses agents that do not use custom tools. The lifecycle becomes correct even when tool compliance is zero.

### Phase 3: establish one context and resolver

1. Consolidate existing `project_context.py` and `project_registry.py` into a typed `ExecutionContext`/`PathResolver` with role-aware named paths.
2. Bind a machine-local `checkout_id` to the exact canonical Git common directory. Keep portable `project_id` separate.
3. Pass opaque selectors, not the central writable root, to workers.
4. Convert correctness-critical consumers first:
   - shared orchestrator used by `oc_runipd.py` and `agy_runipd.py`
   - `ipd_lifecycle.py`
   - run ledger/viewer/recovery
   - set executor, lease manager, migration manager, and hooks
5. Add a static/AST guard that prohibits new direct construction of `.aw/state` or ignored `.aw/records/runs` paths outside resolver and bounded legacy migration code.
6. Test two linked worktrees: every control path resolves to the identical checkout control root, every lane path differs, and worker role cannot obtain a control mutation path.
7. Snapshot and verify protected refs, repository/hook configuration, and worktree administration across a worker turn.

### Phase 4: relocate runtime state outside the repository

1. Add the platform state helper and store under `checkouts/<checkout-id>/`.
2. Implement `aw migrate-runtime-state --apply` with an exclusive migration lock, dry-run inventory, journal, checksums, and rollback/recovery instructions.
3. If only legacy state exists, migrate it. If both legacy and new roots contain live state, fail closed for explicit reconciliation. Never merge directories heuristically.
4. During one bounded compatibility window, readers may use legacy state only when the new root is empty. All new writes go to the new root. Do not dual-write.
5. Remove receipt synchronization/copying after lifecycle consumers all use the resolver.
6. Retain a narrowly named ignored lane-exchange directory if desired. Do not continue using `.aw/state` as a mixed-purpose compatibility bucket indefinitely.

### Phase 5: candidate integration and complete recovery

1. Persist lane allocation/scope/cleanup events and reconstruct leases after restart.
2. Implement actual candidate integration worktrees, full post-merge validation, checkout integration lock, and expected-target-tip recheck.
3. Implement driver-owned durable publication from sanitized ledger projections and validate it with the product result.
4. Implement `aw recover <run-id>` and `aw doctor --lanes` to reconcile journals, branches, worktrees, processes, locks, candidates, submissions, and harvested artifacts.
5. Add crash injection around every irreversible boundary, including input seal and local-artifact copy/digest verification.
6. Replace direct `fcntl` usage with a tested cross-platform lock abstraction and add Windows Job Object process cleanup.

### Phase 6: optional hard enforcement and host optimization

1. Define the host capability contract and keep OpenCode/Agy adapters thin.
2. Add read-only discovery then write execution when a true before-edit barrier is required and the host can enforce it.
3. Add an OS-sandbox execution profile with explicit writable roots and read-only Git common administration; the driver performs all Git mutations. Start on one supported platform, publish its guarantees, and fail rather than silently degrading when hard mode is requested but unavailable.
4. Do not make hardened mode the default until dependency caches, toolchains, network needs, diagnostics, and cleanup are operationally understood.

### Backward compatibility

Keep these surfaces compatible where practical:

- `aw oc run <id6>` / `aw agy run` selectors and normal user workflow.
- Existing run/plan identifiers, with an added attempt ID.
- Existing project config, augmented by local checkout binding.
- Legacy viewer/recovery reading during a finite migration window.
- Existing lane commits/branches, which recovery can register and preserve.
- Existing tracked durable `.aw/records` concepts, now generated through a driver-owned publication candidate rather than edited as live control state.

Do not preserve compatibility through symlinks, permanent dual writes, copied authority files, two competing path resolvers, or implicit cwd heuristics. Those approaches turn a migration bridge into permanent ambiguity.

### Delivery order by value and risk

If implementation capacity is constrained, the highest-value sequence is:

1. Internal-only prompt paths plus external auto-deny and permission event timeout.
2. Clean-base check, minimal input manifest, and missing-input repair without original access.
3. Driver-created begin/finalize and driver-observed outcomes.
4. Five-way output retention, teardown preservation, and exact corrective hooks/prompts.
5. Shared typed resolver and removal of receipt copies.
6. Out-of-repo state migration.
7. Actual merged-candidate validation, durable publication, and full recovery.
8. Optional sandbox hard mode with driver-owned Git mutation.

This order fixes the known hangs and silent loss before undertaking storage relocation, while every step moves toward the final architecture rather than adding throwaway links or copies.

## 9. Open questions, code verification, and references

### Findings established from the inspected snapshot

1. **State paths are not yet centralized.** A logical-root abstraction exists, but active runners/lifecycle code directly construct `.aw/records/runs` and `.aw/state` paths.
2. **Receipt copying exists.** Both inspected host drivers synchronize the main receipt into the worktree before finalization.
3. **Current prompts direct workers outside the lane.** They include absolute main-run paths for outcomes, decisions, and report while the agent cwd/`--dir` is the lane.
4. **A no-progress watchdog exists.** The OpenCode runner has a default 600-second stall watchdog and POSIX process-group cleanup. Keep it as backstop, not primary permission handling.
5. **Current locking is not fully portable.** Active code uses `fcntl`; Python documents it as Unix-only. [[R12](#references)]
6. **Current single-lane integration validation is not an actual merged-tree validation.** The inspected callback can return true before the later Git merge.
7. **The registry already has the right identity clue.** It matches exact Git common directory before path and treats origin as a weaker hint.

### Questions to verify before implementation is complete

1. **OpenCode versions and effective configuration:** reproduce root and nested-subagent permission behavior on every supported version. Verify `OPENCODE_CONFIG_CONTENT` propagation and report higher-precedence managed policy.
2. **Filesystem permission semantics:** determine exactly which file/shell tools OpenCode's `external_directory` gate covers. Do not rely on undocumented shell-path parsing as containment.
3. **Session continuation:** verify whether a read-only discovery session can be resumed after permissions change without losing context, and whether child-agent events remain observable.
4. **Complete state-path inventory:** statically enumerate every `.aw/state`, `.aw/records/runs`, journal, lock, cache, report, and worktree path. Assign every result to the taxonomy before moving data.
5. **Real local-input inventory:** identify which repositories depend on ignored `.venv`, `node_modules`, `.env`, local datasets, generated schemas, IDE state, or other main-checkout files. Classify each as toolchain, safe lane input, secret, cache, or unsupported.
6. **Host prompt inheritance:** verify which instruction level survives compaction/resume and reaches nested agents. Inject the lane contract per child rather than assuming inheritance.
7. **Lifecycle mutation surface:** determine which tracked indexes/manifests finalization changes and therefore what lock granularity is safe.
8. **Driver duplication:** confirm all `oc`, `agy`, and set-execution entry points can use one scheduler, lifecycle, materializer, observer, gate, artifact harvester, recovery service, and integrator.
9. **Commit ownership:** decide whether driver checkpoint commits are default or fallback, and how intentional multi-commit agent work is preserved.
10. **Material-decision detection:** define the repository-specific mechanical triggers and the maximum closure retries before blocking.
11. **Independent clones:** decide whether users ever intend two clones to share active machine state. Safe default is separate checkout IDs.
12. **Dirty main policy:** clean tracked main is the recommended default; specify whether a future snapshot mode is worth its baseline/delta complexity. Never stash or reset automatically.
13. **Filesystem support:** test lock, atomic rename, fsync, copy/reflink digest verification, crash recovery, path case, and long paths on every supported platform/filesystem. State network-filesystem limitations.
14. **Submodules and nested repositories:** define checkout identity and scope behavior when a lane enters another Git common directory.
15. **Retention and privacy:** specify expiry/export/quota for prompts, model logs, diffs, local-retained artifacts, and reports. Avoid persisting secrets merely for reproducibility.
16. **Sandbox and Git guarantee:** document exactly what hardened mode prevents, whether the Git common directory is read-only, who commits, what remains readable, and whether network/credentials/process spawning are contained.
17. **Prompt metrics:** establish a baseline for optional note/status use, missing-input repair, original-checkout access attempts, hook rejection, missing outcomes, closure retries, permission events, and false-positive material-decision gates before optimizing templates.

### Implementation acceptance criteria

The architecture is complete when all of these can be demonstrated:

- Two concurrent lanes and every inner read-only `aw` resolve the same checkout identity but distinct lane roots.
- A lane that uses no custom tools can still complete safely and produce an accurate driver report.
- A task needing an approved untracked local input receives a digest-verified lane copy and never needs live access to the original checkout.
- A request for a missing original-checkout file is denied, classified, materialized if safe, and resumed without an interactive prompt.
- Tracked-but-uncommitted main content can never be silently omitted: default mode refuses it before launch, and any future snapshot mode records it separately from the agent delta.
- Tracked product changes and sanitized durable AW records survive through Git, while useful nontracked outputs survive through a verified local artifact manifest.
- Secrets never enter Git or ordinary reports/artifact bundles; unknown ignored files prevent teardown.
- A lane cannot silently create authoritative receipts, reports, decisions, locks, journals, or integration records.
- Unexpected mutations to protected refs, Git configuration/hooks, or other worktree administration block integration; hardened workers cannot write the Git common directory.
- In default mode, accidental external writes are denied or detected; in hardened mode, the OS denies them.
- A permission ask cannot leave a headless root or child session waiting indefinitely.
- Killing the worker at any point preserves and classifies all work.
- Integration tests run on the exact merged candidate and target movement forces rebuild.
- Recovery can explain every retained worktree, branch, lock, receipt, transaction, and candidate without invoking a model.
- Removing a lane is always preceded by a durable event proving its content was integrated, explicitly abandoned, or separately preserved.

### References

All references accessed 2026-08-29. Repository-specific statements are facts from the pinned snapshot unless explicitly labeled as recommendations or inferences.

**R1. Repository code and inspected snapshot**

- [`fariello/agent-workflows` at commit `8d1bcd5`](https://github.com/fariello/agent-workflows/tree/8d1bcd5160f39b2b60e953902d764f401591039d)
- [`oc_runipd.py`: receipt synchronization, run paths, prompts, OpenCode cwd, supervision, integration](https://github.com/fariello/agent-workflows/blob/8d1bcd5160f39b2b60e953902d764f401591039d/agent_workflows/oc_runipd.py)
- [`agy_runipd.py`: parallel host-driver behavior](https://github.com/fariello/agent-workflows/blob/8d1bcd5160f39b2b60e953902d764f401591039d/agent_workflows/agy_runipd.py)
- [`ipd_lifecycle.py`: worktree-relative receipts, locks, and journals](https://github.com/fariello/agent-workflows/blob/8d1bcd5160f39b2b60e953902d764f401591039d/agent_workflows/ipd_lifecycle.py)
- [`project_context.py`: logical roots](https://github.com/fariello/agent-workflows/blob/8d1bcd5160f39b2b60e953902d764f401591039d/agent_workflows/project_context.py)
- [`project_registry.py`: Git common-directory matching](https://github.com/fariello/agent-workflows/blob/8d1bcd5160f39b2b60e953902d764f401591039d/agent_workflows/project_registry.py)
- [`worktree_lease.py`: worktree allocation, in-memory leases, forbidden paths](https://github.com/fariello/agent-workflows/blob/8d1bcd5160f39b2b60e953902d764f401591039d/agent_workflows/worktree_lease.py)
- [`orchestrate_isolation.py`: current diff-oriented integration gate](https://github.com/fariello/agent-workflows/blob/8d1bcd5160f39b2b60e953902d764f401591039d/agent_workflows/orchestrate_isolation.py)

**R2. Git worktree documentation**
Git project, [git-worktree](https://git-scm.com/docs/git-worktree.html). Documents linked-worktree behavior, shared and per-worktree Git state, locks, removal, repair, pruning, porcelain output, and `$GIT_COMMON_DIR` relationships.

**R3. Git ignore and checkout-index documentation**
Git project, [gitignore](https://git-scm.com/docs/gitignore.html) and [git-checkout-index](https://git-scm.com/docs/git-checkout-index.html). Establishes the tracked/index versus ignored working-file distinction behind why another worktree does not reproduce ignored runtime files.

**R4. Git clone documentation**
Git project, [git-clone](https://git-scm.com/docs/git-clone). Documents local hard-link optimization, concurrent-source race warning, `--shared` alternates, and object-lifetime/corruption caveats.

**R5. Git merge documentation**
Git project, [git-merge](https://git-scm.com/docs/git-merge). Documents fast-forward, no-fast-forward, and fast-forward-only behavior.

**R6. XDG Base Directory Specification**
freedesktop.org, [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir/latest/index.html). Defines `$XDG_STATE_HOME` and the `~/.local/state` fallback for persistent, non-portable application state.

**R7. Git rev-parse documentation**
Git project, [git-rev-parse](https://git-scm.com/docs/git-rev-parse). Documents `--git-common-dir` as `$GIT_COMMON_DIR` when set, otherwise `$GIT_DIR`.

**R8. OpenCode permissions documentation**
OpenCode, [Permissions](https://opencode.ai/docs/permissions/). Documents `allow`/`ask`/`deny`, `external_directory`, its default `ask` action, granular patterns, and intended `--auto` behavior.

**R9. OpenCode configuration documentation**
OpenCode, [Config](https://opencode.ai/docs/config/). Documents configuration sources and precedence, including runtime `OPENCODE_CONFIG_CONTENT`.

**R10. OpenCode issue #43888**
OpenCode GitHub repository, [Non-interactive `opencode run` hangs forever when a subagent tool hits an `external_directory` ask (v1.18.18)](https://github.com/anomalyco/opencode/issues/43888). Primary issue report dated 2026-08-21; closed as duplicate; explicit allow reported as workaround.

**R11. OpenCode issue #36868**
OpenCode GitHub repository, [`opencode run --auto` hangs indefinitely when a Task subagent requests permission](https://github.com/anomalyco/opencode/issues/36868). Primary issue report dated 2026-07-14 describing root-session-only permission handling and a child-session deadlock.

**R12. Python `fcntl` documentation**
Python Software Foundation, [`fcntl` - the `fcntl` and `ioctl` system calls](https://docs.python.org/3/library/fcntl.html). Documents availability on Unix, not Windows.

**R13. Git hooks documentation**
Git project, [githooks](https://git-scm.com/docs/githooks). Documents hook location/configuration, pre-commit refusal by nonzero exit, hook execution context, and that `pre-commit` can be bypassed with `git commit --no-verify`.
