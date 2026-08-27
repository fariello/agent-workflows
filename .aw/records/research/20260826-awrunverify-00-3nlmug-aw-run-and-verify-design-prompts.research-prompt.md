---
id: 3nlmug
created: 20260826
set: awrunverify
order: 00
topic: [runner, run-and-verify, dependencies, prompt-provenance, spec-25kzda]
model:
kind: research-prompt
status: intake
outcome: adopted
summary: The two-pass frontier-model design prompts (initial checking-spec + addendum + revision followup) that produced spec 25kzda's aw-run deterministic run-and-verify design
consumed-by: [25kzda]
---

# Provenance: the design prompts that produced spec 25kzda

Captured for durability (previously loose in tmp/). These are the actual prompts handed to a frontier model, in sequence, whose output became `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` (id 25kzda). Kept so the spec's design has traceable provenance: what was asked, in what order, and why. Three phases: (1) the initial checking-spec design prompt; (2) an addendum adding context mid-run; (3) a revision followup folding in four accepted pushbacks + the new dependency-enforcement mechanism. The model's design output itself is NOT reproduced here (it lives in the spec); this doc is the QUESTION provenance, not the answer.

---

## Phase 1 - initial checking-spec design prompt

# Design task: a user-friendly, idiot-proof, deterministic "run and verify" specification for `aw <host> run`

You are an expert CLI/tooling designer and systems engineer. Design a complete, unambiguous specification for how a command-line "runner" should EXECUTE and then DETERMINISTICALLY VERIFY work items of several different file types in a repository-based AI agent workflow toolkit. Produce a detailed, implementation-ready design. Return your entire answer as a single DOWNLOADABLE markdown (`.md`) file (offer it as a file the requester can download), with no preamble outside the file.

## Context you are designing for

A toolkit ("agent-workflows", CLI verb `aw`) drives AI coding agents on two hosts:
- OpenCode (`aw oc run`)
- Antigravity / Gemini (`aw agy run`)

The single canonical user-facing verb is `aw <host> run <selector>`. It replaces older per-host driver scripts. The runner is a multi-turn lifecycle engine: it launches a host agent in a (possibly noninteractive, restartable) session, drives it through the appropriate action for each work item, keeps durable per-run state, and does a skeptical second-turn verification. It must be safe to run unattended (no pushing, path-scoped commits only, never bypass git hooks).

`<selector>` resolves to one or more work items. A work item is a file of a KNOWN TYPE. The known types and their real lifecycle states in this toolkit are:

- **IPD (Implementation Plan Document / "plan")**: a structured plan file. Lifecycle `- Status:` values, in order:
  - Pre-terminal: `draft` -> `to-review` -> `reviewed` -> `approved` (also `auto-approved`, a sibling ready-to-execute tier)
  - Terminal: `executed`, `superseded`, `not-executed`
  - Standing: `reusable`
  - Plans live in disposition directories (`pending/`, `executed/`, `superseded/`, `not-executed/`, `reusable/`) that must agree with the terminal status. Plans carry an execution checklist (`E-*` items) and a validation checklist (`V-*` items) that must be in bijection, plus metadata (`Set`, `Order`, `Scope-Paths`, optional `Blocks-Release`, optional `From-Backlog`). A plan is executed only after every `V-*` item is verified with concrete evidence and the plan is moved to `executed/`.
- **Spec**: a specification document with `- Status:` values `draft` -> `to-review` -> `reviewed` -> `approved` -> `implementing` -> `implemented`, plus `deferred` / `parked` / `superseded`. Moving to `approved` requires explicit human sign-off; moving to `implemented` requires a resolvable evidence citation. Specs graduate INTO IPDs.
- **Backlog item**: a lightweight work item with `- Status:` `open` / `blocked` / `parked` / `done`, a `Priority`, an optional `Blocks-Release` gate, and an optional typed gate (`Gate-Kind`/`Gate-Ref`, required when `blocked`). Backlog items graduate into IPDs (link field `From-Backlog`).
- **Prompt**: a free-form prompt file meant to be sent to an agent and executed once (no lifecycle state).
- **Research prompt / research doc**: research-tree artifacts (prompts, reports, findings, reconciliations) with a `status`/`outcome` in frontmatter.
- **Release record**: a record with `Status` `planned` / `blocked` / `shipped`.
- **Walkthrough**: a narrative record (no execution semantics).

## The behavior the design must specify

### A. Selector resolution and mixed-type safety
1. `<selector>` may resolve to a single item, many items, or the literal `all`.
2. If `<selector>` is `all`, the runner operates ONLY on IPDs, unless an explicit flag/syntax says to include or target other types (design that flag/syntax).
3. If the resolved set contains a MIX of file types (e.g. some specs, some prompts, some IPDs), the runner must NOT silently proceed. Design:
   - a required "I know they're mixed, do it anyway" flag for non-interactive use; and
   - an interactive confirmation that summarizes the mix ("You have X specs, Y prompts, Z IPDs. Proceed?") and requires confirmation.
4. The runner should "know" the right thing to do per item based on its type and status (below), while letting the user override where appropriate. (The user can always call `opencode`/`agy` directly for anything unusual; the runner optimizes the common, safe path.)

### B. Per-type "what does 'run' mean" dispatch
Specify precisely what the runner does for each work item, keyed by type and status. Start from these REQUIRED rules and complete/expand them:

- **Prompt**: execute the prompt (one turn), then verify per the checklist below.
- **Spec**: do what is appropriate for the spec's status (e.g. `to-review`/`reviewed` -> run a spec review; `approved` -> author the IPD from it; `implementing` -> ?; terminal states -> refuse/skip with a colored message). Define the full status->action table, including which transitions require human sign-off and must therefore be refused or gated in unattended mode.
- **IPD**:
  - `draft` AND fully fleshed out (all authoring placeholders resolved — this happens constantly: someone finished drafting but forgot to advance the status) -> run a `/plan-review` (equivalent to advancing toward `to-review`/`reviewed`).
  - `draft` but still a stub (unresolved placeholders) -> refuse/skip with a colored message (nothing to review yet).
  - `reviewed` and ready AND `--full-auto` present -> run the equivalent of `aw ipd set approved <id6>` with an appropriate message, THEN execute the plan.
  - `reviewed` without `--full-auto` -> stop and require human approval (do not self-approve).
  - `approved` (or `auto-approved`) -> execute the plan.
  - `executed` / `superseded` / `not-executed` -> complain in color and move on (nothing to do).
  - Define handling for `to-review` and `reusable` too.
- **Backlog item**: propose appropriate behavior (e.g. `open` -> graduate into an IPD? or refuse and tell the user to plan it? `blocked` -> refuse with the gate reason; `done` -> skip). Justify.
- **Research prompt / research doc, Release record, Walkthrough**: propose appropriate, conservative behavior (most likely "not runnable; explain and skip"), with rationale.

For every type, distinguish behavior in INTERACTIVE vs UNATTENDED (`--full-auto`/noninteractive) mode, and specify which actions are FORBIDDEN unattended (e.g. anything requiring genuine human sign-off).

### C. Deterministic post-step verification (the core deliverable)
After the runner drives the agent through a step, it must NOT trust the agent's self-report. It must deterministically check that the agent actually did what it was supposed to, by inspecting repository state (files, git, metadata) — not by reading the transcript. This is the heart of the spec.

Produce, PER FILE TYPE, an explicit checklist of deterministic post-step assertions. Use these REQUIRED IPD checks as the seed and complete them, then design the equivalent checklists for every other type:

- **IPD executed**:
  - Was the plan file moved into `executed/` and does its `- Status:` say `executed`?
  - Are ALL `V-*` validation items marked verified with recorded evidence (not `pending`)?
  - Do the actual changed paths fall within the plan's declared `Scope-Paths`?
  - Was a path-scoped commit created (and only files the plan touched)? Was nothing pushed?
  - Were git hooks NOT bypassed (no `--no-verify`)?
  - Does the structural linter pass at the pre-transition/post-transition phase?
  - If the plan carried `Blocks-Release`/`From-Backlog`, are those consistency invariants still satisfied?
- **IPD reviewed (from a `/plan-review`)**: was the status advanced legitimately? was a review record/history line written? does it still lint?
- **Spec** (per action): was the status transition legitimate and tool-authored (not a hand-edit)? for `implemented`, is the evidence citation resolvable? for IPD-authoring from a spec, does a conformant IPD now exist and link back?
- **Prompt**: define what "success" even means for a free-form prompt (this is genuinely hard — address it honestly: exit status? a declared expected artifact? or is it inherently unverifiable and must be labeled so?).
- **Backlog / research / release / walkthrough**: define the deterministic checks or state honestly that there are none.

For each check, specify: what is inspected, the pass/fail criterion, the exact remediation message shown on failure (name the violated invariant and the precise `aw ...` recovery command), and whether failure ABORTS the run, SKIPS the item, or RETRIES.

### D. Cross-cutting requirements
Address all of these in the design:
1. **Determinism**: every check must be a pure function of repository state; no reliance on agent narrative or LLM judgment. Where a requirement is inherently non-deterministic (e.g. "did the prompt succeed"), say so explicitly and propose the least-bad observable proxy.
2. **Idiot-proofing / safety**: default to the safe action; require explicit flags for anything destructive, self-approving, or mixed-type; never push; never bypass hooks; only path-scoped commits.
3. **Restartability**: the runner keeps durable per-run state; define how a re-run resumes, skips already-done items, and re-verifies rather than blindly re-executing.
4. **Ordering & dependencies**: when running many IPDs, respect Set/Order and any declared dependencies; define the queue semantics.
5. **Reporting**: define a machine-readable per-item outcome (planned/ran/verified/failed/skipped + reason) and a human colored summary.
6. **Failure taxonomy**: enumerate failure classes (agent didn't act, acted wrongly, partially acted, self-reported success but check failed, hook refused, out-of-scope change, unauthorized status change) and the runner's response to each.
7. **Interactive vs unattended parity**: the SAME deterministic checks run in both modes; only the prompting/approval behavior differs.

## Deliverable format (return as a downloadable .md file)
Structure your answer as:
1. **Executive summary** (the model, in a few sentences).
2. **Selector resolution & mixed-type policy** (flags, prompts, the `all`->IPD rule).
3. **Per-type dispatch table**: rows = (type x status), columns = interactive action, unattended action, forbidden-unattended.
4. **Per-type deterministic verification checklists** (the core): for each type, a table of (check, what is inspected, pass criterion, failure remediation message + recovery command, on-failure action = abort/skip/retry).
5. **Cross-cutting design** (determinism, safety, restartability, ordering, reporting, failure taxonomy).
6. **Open questions & honest limits** (especially where verification is impossible and must be labeled probabilistic).
7. **A concrete worked example**: trace `aw oc run all --full-auto` over a mixed queue (a stub draft IPD, a fleshed-out draft IPD, a reviewed IPD, an approved IPD, an already-executed IPD, a spec, and a prompt), showing each dispatch decision, each post-step check, and each outcome.

Optimize for: maximum user-friendliness, maximum idiot-proofing (safe-by-default, explicit override for anything risky), and maximum determinism (repository-state checks, never trust the transcript). Be specific and prescriptive; prefer concrete rules over principles. Where you must make a judgment call, state it and justify it briefly.

---

## Phase 2 - addendum (added while phase 1 was running)

# Addendum / additional context to the "run and verify" design task

This supplements the design task you are already working on (the specification for how `aw <host> run <selector>` should execute and deterministically verify each known file type). Fold the following context into your design. It does not change the deliverable; it removes two sources of unnecessary hedging and keeps your spec durable.

## 1. Nothing is released yet — design the clean end state, with NO backward-compatibility

The runner surface (`aw oc run`, `aw agy run`) and its predecessor driver scripts have **not been released**. There are:
- no external users,
- no callers to protect,
- no compatibility contract, and
- no deprecation obligations.

Therefore:
- Do NOT propose backward-compatibility shims, alias verbs (e.g. keeping an old `runipd`/`runagy` name alongside `run`), transitional residue, or deprecation paths.
- Design ONLY the clean, final end-state behavior. If an older name or path exists today, assume it is being deleted, not preserved.
- Optimize purely for the best final design; spend no words on migration or compatibility.

## 2. Names and syntax are being consolidated — design against ROLES, not current filenames

The internal module names, script names, and some CLI syntax are actively being renamed and consolidated right now (for example, the per-host runner engine modules and the old driver script names are changing, and the sole user-facing verb is becoming `aw <host> run`). The exact final identifiers are NOT fixed.

Therefore, write your specification against the ROLES, not any specific current filename or legacy verb:
- "the `run` verb" (`aw oc run` / `aw agy run`) — the single canonical entry point,
- "the host runner engine" — the multi-turn lifecycle/queue/state-machine module behind it,
- "the deterministic checker" — whatever surface performs the repository-state verification.

Do not anchor examples or checks on any specific current module/script name; refer to these roles so the spec stays correct after the rename lands.

## 3. Resolve, don't preserve, the multi-mode "run" overload

The current runner conflates several behaviors under one script: driving an IPD/plan through its lifecycle (the valuable queue runner) AND one-shot behaviors (execute a single prompt string, execute a prompt file, author an IPD from a spec). In your design:
- Treat `run` as meaning exactly ONE thing: drive a work item (or queue of work items) through the appropriate action for its type and status, then deterministically verify it.
- If a one-shot "just send this single prompt to the agent" behavior is still worth keeping, give it its OWN distinct verb (e.g. `aw <host> prompt` or `aw <host> exec`) rather than overloading `run`.
- If a behavior is obsolete now that the full runner exists, recommend deleting it rather than carrying it forward.
- State explicitly, for each behavior currently bundled into the old script, whether it becomes part of `run`, becomes a separate verb, or is dropped.

Everything else in the original task stands. Return your complete design as a single downloadable markdown (`.md`) file.

---

## Phase 3 - revision followup (pushbacks + dependency-enforcement)

# Follow-up to the "run and verify" design task: required revisions + a new dependency-enforcement mechanism

This is a follow-up to the design you already produced (the `aw <host> run` deterministic run-and-verify specification). Produce a REVISED version of that design that (A) incorporates the specific revisions below, and (B) adds a new mechanism for cross-item dependencies that the original under-addressed. Return the complete revised design as a single downloadable markdown (`.md`) file. Keep everything from the original that these instructions do not change; where these instructions conflict with the original, these win.

Two independent asks, in two sections. Address both.

---

## Section A: Required revisions to the existing design

Incorporate each of these. For each, state briefly in the revised design how you resolved it.

### A1. Scope violation should FAIL THE ITEM, not ABORT THE ENTIRE RUN
The original aborts the whole run (and all independent downstream items) when one item changes an out-of-scope path (`RUN-SCOPE-DELTA`, and the worked example where one item's scope slip stops the queue). This is too aggressive for the primary use case: an unattended, overnight, multi-item run where the operator wants maximum safe forward progress.

Revise so that:
- An out-of-scope mutation on one item is a **FAIL ITEM** (mark it failed, roll back / quarantine its own changes, block only ITS dependents), and the queue continues with independent items.
- Reserve **ABORT RUN** strictly for whole-repository integrity/safety failures where continuing is unsafe or meaningless: corrupt run ledger, ownership/lease conflict, unknown/non-idempotent external outcome, push attempt, hook-bypass attempt, and identity/type ambiguity. Enumerate the ABORT-RUN set explicitly and justify why each cannot be a per-item failure.
- Be precise about how a failed item's partial changes are contained so they cannot leak into a later item's commit (e.g. restore owned paths to baseline before continuing).

### A2. Retry budget must be configurable, not a hard-coded 2
The original asserts a default of two correction attempts. Keep two as the DEFAULT, but make it configurable (a flag and/or repository policy), specify the valid range and the behavior at zero (no auto-correction; fail on first failed check), and state which failure classes are never retryable regardless of budget (unchanged from the original's non-retryable list).

### A3. Contractless-prompt exit code should be operator-selectable
The original always exits nonzero for an acknowledged contractless prompt (verification unavailable). Keep nonzero as the safe DEFAULT, but let the operator opt into treating an acknowledged, ran-to-completion contractless prompt as a non-failing outcome (e.g. a `--unverifiable-ok` policy) so that legitimate exploratory prompt use does not always report failure. The item's verification state must STILL be reported as `unavailable` (never `verified`); only the process exit code / aggregate run success is affected. Specify the exact interaction with the run's overall exit code.

### A4. Host asymmetry (oc vs agy) must be explicit
The original treats "the host" as a uniform "launch a session" abstraction. In reality the two hosts differ in session model, tool/hook interception, and sandbox/permission capabilities, and the no-push / hook-enforcement / commit-gateway guarantees may hold on one host but not the other.

Revise so that:
- The design references a per-host CAPABILITY DESCRIPTOR (what the host can enforce: deny push-capable network/credentials, intercept the commit path, run in an isolated worktree, enforce a tool policy). Treat the exact descriptor format as an implementation detail, but require its existence.
- State the FAIL-CLOSED rule crisply: if a host cannot enforce a guarantee that an action requires (e.g. no-push for unattended mutation), that action is refused on that host with an actionable message, rather than proceeding on trust.
- Make clear which guarantees are host-independent (they are proved from repository/Git state after the fact) versus host-dependent (they require the host to have controlled execution). Put each §5.2 safety guarantee in one bucket or the other.

---

## Section B: New requirement — first-class, enforced, cross-item dependencies

The original's dependency handling (Set/Order plus a queue DAG) is insufficient because in this toolkit there is NO enforced, machine-readable, cross-item dependency statement today. What exists:
- Within a single IPD, execution leaves carry an intra-plan `Depends on: <E-ids|none>` field (dependencies BETWEEN steps of the same plan).
- Between IPDs, only `Set` + `Order` implies ordering, which is a weak convention, not a verified dependency graph.
- There is no required, id6-grounded statement of "this whole IPD depends on these other work items."

Design the following, and integrate it into the revised run-and-verify spec.

### B1. A required, id6-grounded cross-item dependency statement
- Every IPD MUST carry a top-level dependency statement expressed in terms of stable id6 handles of other work items (IPDs, and where meaningful specs/backlog items). The statement must be MANDATORY and must explicitly permit "no dependencies" as a first-class, affirmative value (so the absence of dependencies is a stated fact, not an omission). Distinguish clearly between "declared: none" (the author asserted there are no dependencies) and "missing" (the author never addressed it) — only the former is acceptable.
- Specify the field: its name, its exact grammar (id6 tokens, the affirmative-none sentinel, optional edge qualifiers if useful such as "must be executed" vs "must merely exist"), where it lives in the IPD metadata block, and how it relates to the existing intra-plan `Depends on` E-item field (they are different layers; name them unambiguously so they never collide).
- Address whether specs and backlog items also carry it or whether the mandatory requirement is IPD-only in v1 (recommend and justify).

### B2. Runner semantics for dependencies (honor + skip-cascade)
Revise the runner so it:
- Builds the dependency graph from these declared statements (not merely Set/Order), validates it (no cycles, all id6s resolve), and refuses to run on an invalid graph.
- Never runs an item before every dependency it requires has been satisfied (for an "must be executed" edge, satisfied = the dependency reached its verified terminal success; for a "must exist" edge, satisfied = the referenced item exists in the required state).
- If a dependency is NOT met and cannot be met in this run (it failed, was skipped as non-runnable, is terminally superseded/not-executed, or is a human gate that stopped), then the dependent item is SKIPPED and recorded as **dependency-not-met**, and that unmet state CASCADES: anything depending on the skipped item is itself dependency-not-met. Specify the exact propagation and the per-item reason codes.
- Specify how declared cross-item dependencies interact with the existing Set/Order ordering (explicit declared dependencies win; Set/Order is a tiebreaker among independent ready nodes, never an override).

### B3. An enforcement mechanism CONSISTENT with the existing model
The toolkit already enforces some invariants at commit time via LOCAL, COMMIT-SCOPED, TYPE-SCOPED pre-commit hooks that each delegate to a SINGLE shared `check_engine` rule (so the hook, `aw check`, and CI can never diverge). Two existing examples: a gate that refuses an untooled plan status change, and a gate that refuses closing a release-blocking backlog item without a preserved gate. Both are opt-in-installable, local, commit-scoped, and back a matching `aw check` rule.

Design the dependency-statement enforcement to MATCH this exact model. Specify:
- The shared predicate / `check_engine` rule (a stable rule id, e.g. `check.ipd-missing-dependency-statement` and `check.ipd-dependency-dangling` / `check.ipd-dependency-cycle`) that: flags an IPD lacking the mandatory dependency statement; flags a statement whose id6 does not resolve; flags a cycle. Give each a severity, an assurance class, and the exact recovery command.
- How the SAME predicate is surfaced across ALL of: `aw check` (repository-wide, the portable authority), `aw ipd lint` (per-plan, at the author/pre-execution/pre-transition phases — decide which phase makes the statement mandatory so existing pre-cutoff plans are grandfathered rather than mass-failed), an OPT-IN local pre-commit hook (commit-scoped, type-scoped to plan `.ipd.md` files, delegating to the same predicate), and the runner's pre-flight graph validation. One predicate, many surfaces, no divergence.
- The GRANDFATHERING policy: making the statement mandatory must not retroactively fail every existing plan at the always-on author metadata check. Recommend how to introduce mandatoriness (e.g. a reserved affirmative-none sentinel that existing plans can be swept to, or a cutoff/phase where it becomes required), mirroring how this toolkit already grandfathers other newly-required fields.
- How the runner "forces agents to think about and state dependencies": e.g. authoring/scaffold emits the field as a required-to-resolve placeholder; the draft-readiness / to-review gate treats a missing or unresolved dependency statement as "not ready"; the deterministic checker refuses to advance or execute a plan whose dependency statement is missing or unresolved. Make the point of forcing DETERMINISTIC, not a prose reminder.

### B4. Verification checklist additions
Add to the per-type deterministic verification checklists (in the same table format as the original §4) the dependency checks, at minimum:
- dependency statement present and well-formed (mandatory-field check, with grandfather rule);
- every declared dependency id6 resolves to a real work item;
- no cycle in the declared graph;
- at execution time, every required dependency is in its required satisfied state, else the item is skipped dependency-not-met (not failed, not executed);
- the cascade is recorded: dependents of an unmet dependency are themselves dependency-not-met.
For each: what is inspected, pass criterion, exact failure message + recovery command, and on-failure action (fail item / skip dependency-not-met / abort run — using the REVISED A1 abort discipline).

---

## Deliverable
Return one downloadable markdown (`.md`) file: the complete revised run-and-verify design, with Section A revisions folded into the existing structure and Section B integrated (new dependency field, runner semantics, the one-predicate-many-surfaces enforcement mechanism, and the added verification checks). Keep the original's strengths (deterministic repository-state authority, honest limits, worked example) and update the worked example to demonstrate: a dependency-not-met skip cascade, and an item refused because a required host guarantee is unavailable. Preserve the pre-release/no-compat and design-against-roles constraints from earlier: no backward-compatibility shims, no legacy aliases, and refer to roles ("the run verb", "the host runner engine", "the deterministic checker") rather than specific current filenames.
