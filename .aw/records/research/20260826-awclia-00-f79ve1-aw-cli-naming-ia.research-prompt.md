---
id: f79ve1
created: 20260826
set: awclia
order: 00
topic: [cli, information-architecture, naming, pre-release]
model:
kind: research-prompt
status: todo
outcome: none-yet
summary: Originating prompt for the comparison set.
consumed-by: []
---

# Originating prompt (upload-ready; de-named IA/naming design task)

This is the exact blind-named prompt handed to each model in this comparison set. It is a de-named projection of the named ground-truth inventory (research `sk94i0`): current command names are withheld so models name from first principles; real structure + the P1-P15 collisions are preserved. Reports land in orders 01-03; reconciliation in 04.

---

# Design task: name and organize a command-line tool's full capability set from first principles

You are an expert in command-line ergonomics and information architecture. You are given the COMPLETE capability set of a single command-line tool, described WITHOUT any of its current command names (deliberately, so you are not anchored by them). Your job is to design the most intuitive naming and grouping for the whole surface, from scratch. Return your entire answer as a single downloadable markdown (`.md`) file, with nothing outside the file.

The tool is a developer/agent workflow toolkit invoked as a single top-level command (call it `T`). Users type `T <something> ...`. Today it has roughly 44 top-level entries and many nested subcommands; the current names grew organically and are being reconsidered before the tool's first public release, so you may propose ANY naming or grouping with no backward-compatibility constraints.

## The design philosophy to optimize for (this is the target, follow it)

Names must be **plain, common, everyday words whose ordinary meaning matches what the command does.** Specifically:

1. **The word IS the action.** A command that runs something should be called "run"; a command that lists should read as listing. A reader should predict what a command does from its name alone, before reading help.
2. **One word, one meaning.** No single word should mean two different things in different places. If two commands report the state of two different subjects, they must not share a name.
3. **One meaning, one word.** No two different words for the same kind of action (avoid begin/start/kick-off all meaning "start").
4. **Predictable placement.** For any operation a user wants, there should be exactly one obvious place it lives. A user should not have to guess whether an operation hangs off a generic verb or off the specific thing it operates on.
5. **Short and low-friction**, but clarity beats brevity. Prefer common words over jargon.
6. **The name should hint read-vs-write** where reasonable (an inspecting command should not sound like a mutating one, and vice versa).
7. **Namespacing is allowed and encouraged** (`T <group> <action>`), but only where the grouping is intuitive; do not create near-empty groups or force everything into one flat list.

## What you are given: the capability set (NAMES REMOVED ON PURPOSE)

Each capability is described by (a) what it operates on / the subject it concerns, (b) whether it READS or WRITES, and (c) what it does. The real functional STRUCTURE and the real problems are preserved; only the current names are withheld so you name them fresh. Groupings below reflect the tool's actual subjects, not its current command names.

### Subject group: managing the tool's own installation across many code repositories
- [W] Install/update the toolkit into one or many repositories (idempotent; a wizard configures placement and storage; writes managed marker files and host integration shims; backs up and prunes).
- [W] First-run guided setup: discover repositories under chosen roots, save user config, optionally install into them.
- [W] Remove the toolkit from a repository (preserving the user's own content).
- [R] List the repositories the tool knows about and whether each is current/stale/not-installed.
- [R] Summarize the environment: versions, config, working-tree state, per-repository currency.
- [R] Deep read-only inspection that aggregates every health/consistency signal into one report.
- [W] Retroactively rename internal quarantine sub-directories to a standard name and fix ignore files.
- [R/W] Transactional migration of the on-disk layout and storage backend, with a rollback journal (inventory/plan/apply/status/resume/rollback/cleanup phases).
- [R/W] Add / list / remove entries on a "never manage this repository" blocklist. (NOTE: there are currently THREE different command surfaces that all edit this one blocklist - see Problem P10.)

### Subject group: the tool's project identity and where records are stored
- [R] Inspect this repo's project identity and whether it matches a registry entry.
- [W] Bind this repo to an existing project identity; update a project's path association after a move.
- [R] Inspect the records-storage backend and its durability guarantees.
- [W] Initialize records storage; attach/detach/move/rebind a companion storage location; set durability policy.
- [R] Run preflight checks on a companion storage location before attaching it.
- [R] Print the resolved project context (identity, mode, storage backend, durability, enabled integrations, and the four logical root directories).
- [R] Given one of four logical root names, print its actual filesystem path (scriptable).

### Subject group: structured plan documents (the tool's core work-plan artifact; call them "plan docs")
A plan doc moves through a lifecycle of readiness states (rough draft -> ready-to-critique -> critiqued -> approved) and then terminal states (done / replaced / abandoned / standing-reusable), and lives in a directory that reflects its terminal state. It contains an execution checklist and a matching validation checklist that must be one-to-one.
- [R] Show a readiness board of plan docs by state.
- [R] Deterministically check ONLY a plan doc's structure and state legality (checklist bijection, heading order, state rules) at one of several lifecycle checkpoints. Proves nothing about semantic quality.
- [R/W] Write a new conformant plan-doc skeleton with the right structure and a derived canonical filename.
- [R/W] Assign stable ids to new execution-checklist items and append matching validation-checklist items (maintain the one-to-one).
- [R] Compile an approved GROUP of plan docs into a validated dependency graph + execution manifest and inspect it (planning only in the current build; does not execute).
- [W] Transition a plan doc's lifecycle state (or a whole group), moving its file between state directories and recording history.
- [W] Fail-closed START of executing one plan doc: run the pre-execution structural check, freeze the declared file-change scope and a content digest and the base version-control commit into a local receipt that acts as execution authority.
- [R/W] Atomic terminal completion of an executed plan doc: validate the start receipt, run the pre-completion check, reconcile the actually-changed files against the declared scope (refuse out-of-scope), record history, set the terminal state, move the file, make a scoped version-control commit, run the post-completion check.

### Subject group: a durable, tamper-evident ledger of an EXECUTION (an "execution record")
This is an append-only, hash-chained event log of ONE execution of work, with steps, evidence envelopes, and a completion predicate. Distinct from plan docs and from the host-driver store below, though all three have been loosely called "runs."
- [R] Inspect an execution record's state, steps, and completion status.
- [R] List and validate the captured evidence/tool-event envelopes in an execution record.
- [R] Verify the execution record's hash chain, sequence continuity, and evidence validity.
- [W] Lease and advance one step of an execution record from pending to running.
- [R] List the steps whose dependencies and approval gates are currently satisfied.
- [W] Append a step-outcome record (performed/blocked/failed) to the append-only log.
- [R] Reconstruct state and report which steps are resumable; refuse if an interrupted step left an unknown outcome.
- [W] Record a terminal cancellation of an execution record.
- [R] Reconstruct and print the whole execution record's state.
- [W] Evaluate the completion predicate and, if satisfied, record terminal completion (requires a coordinator authority role).
- [R] Print an execution's recorded autonomous decisions / its unresolved deferred questions.

### Subject group: DRIVING an external AI agent to actually do work (the "driver")
This is the command a user actually invokes to make an AI coding agent execute or review plan docs. It spawns an external model CLI, keeps its own durable per-run state directory (also historically called a "run"), and drives multi-turn work with a skeptical second-turn verification. There are TWO such drivers for two different external agent hosts, and the tool should support choosing a default host so the host need not always be named. (NOTE: see Problems P1, P2, P12.)
- [W] Start driving: build a durable queue of plan docs and execute/review them, auto-routing by each doc's state (ready-to-critique -> run a critique; approved -> execute step by step); rich options incl. auto-approve, skip-verification, model/session selection.
- [W] Resume an interrupted driving run (optionally retry incomplete/failed items).
- [R] Inspect a driving run's queue positions, attempt counts, and statuses.
- [R/W] Rebuild and print the path to a driving run's human-readable execution report.

### Subject group: operations that apply UNIFORMLY across every artifact type
The tool has ~9 artifact types (plan docs, specs, prompts, research docs, backlog items, walkthroughs, roadmaps, inter-agent messages, release records). The following operations are TYPE-GENERIC: the same operation, parameterized by which type. (NOTE: several of these ALSO exist as type-specific commands on individual types - see Problem P6.)
- [R] Find artifacts of a type (or across all types) by a selector (stable id / state / group / filename fragment).
- [R] Regex content-search within a type (or all).
- [R/W] Rebuild and print a type's index/manifest (or fail on drift).
- [R] Validate artifacts of a type against that type's contract (or validate every type at once).
- [R/W] Rename/move an artifact of a type, rewriting references to it.
- [R/W] Assign an artifact to a group, re-clustering its filename.
- [W] Transition the lifecycle state of an artifact (or a whole group) - overlaps the plan-doc-specific and other type-specific state-transition commands.
- [R/W] Deliberately deep-shelve stale artifacts of a type (targeted or an age-based sweep).

### Subject group: operations SPECIFIC to individual artifact types
- Research docs: create one / create a multi-model comparison set / regroup / rename-within-grammar / detect dangling citations / rebuild index / query index / list not-yet-run research prompts / promote to a status+shelf / set an outcome + provenance / report mis-shelved docs.
- Backlog items: create / transition state (a "blocked" state requires a typed reason gate; a "done" close can carry evidence) / validate the tree.
- Specs: transition state (enforcing a legal transition table + an anti-self-approval floor + typed deferral gates) / append a history note without changing state / validate / one-time normalize a legacy state value.
(NOTE: these type-specific state-transition and validate operations DUPLICATE the type-generic ones above - Problem P6.)

### Subject group: inspecting records, per-artifact history, and an operational action queue
- [R] Inspect a single record OR an operational action, resolving the selector against artifact records first and silently falling back to an operational-action ledger. (Two different stores behind one lookup - Problem P4.)
- [R] Print one artifact's chronological lifecycle history from a global history sidecar. (Read-only, but its current name sounds like a writer - Problem P5/P14.)
- [R] List open operational actions ("what should I do next" at the operational level).
- [R] A cross-tree "what needs attention" view that maps every artifact's state onto ready/active/blocked/done/parked; can fail-closed as a gate. (Overlaps the previous two - Problem P15.)

### Subject group: authoring/compiling the tool's own workflow definitions
- [R] Schema-validate a canonical workflow-definition package.
- [R/W] Compile workflow source packages into runtime projections.
- [R] Recompile and fail if any generated projection drifted from source.

### Subject group: safety / leak scanning
- [R/W] Scan tracked files / staged blobs / version-control history / a built distribution for identifying info that must not appear publicly (home paths, usernames, hostnames, private repo names, session ids); optionally auto-rewrite only the safe cases; a config wizard tunes rules.

### Subject group: local pre-commit gate shims (invoked by version-control hooks, not by hand)
- [R] Refuse a raw commit that terminally completes a plan doc without the proper completion-transaction evidence.
- [R] Flag a raw, untooled intermediate plan-doc state change (a state edit with no tool-authored history line).
- [R] (opt-in) Refuse committing a release-blocking backlog item closed as done without a preserved/satisfied release gate.

## The specific problems to solve (described structurally, names withheld)

- **P1.** The word currently used for "the execution-record ledger" is ALSO the natural word for "actually execute/drive work," but today it points at the ledger-inspection surface, NOT at the driver that actually executes. So the most natural "run/execute" word does not launch execution. Fix which concept owns that word.
- **P2.** THREE distinct stores are all loosely called "runs": (a) the tamper-evident execution-record ledger, (b) the AI-agent driver's per-run state directory, (c) the compiled group-execution manifest. Give them distinguishable names.
- **P3.** At least FIVE different commands report "status" of five different subjects (environment; execution-record ledger; driver queue; project identity; storage). One word, five meanings.
- **P4.** One inspection command silently resolves a selector against artifact records first, then falls back to an unrelated operational-action ledger - two stores behind one lookup.
- **P5.** "History" is split across three unrelated things (a per-artifact history sidecar; the execution-record event log; in-file history sections), and the per-artifact-history command's name sounds like it writes but it only reads.
- **P6.** There are TWO parallel grammars for the same operations: a TYPE-GENERIC form (an action parameterized by type) and TYPE-SPECIFIC forms (the action living on each individual type). The same state-transition, validate, index, and find operations are reachable both ways, so users cannot predict which door to use. Decide a single consistent rule (all-generic, all-specific, or a crisp split) and name accordingly.
- **P7.** "Validate/check" is spread across at least eight surfaces with no single obvious entry point.
- **P8.** The same terminal plan-doc transition is reachable through three different commands with inconsistent required arguments.
- **P9.** "Start/begin/kick-off" is expressed by at least three different words across the plan-doc, execution-record, and driver surfaces.
- **P10.** Three different command surfaces all edit ONE "never-manage" blocklist.
- **P11.** One deep-shelve command has an irregular polymorphic first argument (sometimes a type, sometimes a specific target) that breaks the otherwise-uniform verb-type-selector shape.
- **P12.** The two AI-agent drivers have inconsistent aliasing, and their extra sub-name (driver-flavor) is cosmetic since both expose the same sub-actions; consider dropping it and letting the host be a namespace or a default.
- **P13.** "Move/rename/regroup" operations are scattered across many differently-named commands at different scopes with no shared vocabulary.
- **P14.** Command names do not signal read-vs-write: some read-only commands sound imperative/mutating; some mutating commands preview by default.
- **P15.** "What should I do next?" is answered by three overlapping commands at different scopes (operational actions; cross-tree attention view; the backlog tier).

## Deliverable (return as one downloadable .md file)
1. **Naming philosophy restated** in your own words as the rubric you will apply.
2. **A proposed top-level command map**: the full set of top-level commands and their subcommands, each a plain word, with a one-line gloss, organized into intuitive groups/namespaces. Cover EVERY capability listed above - nothing dropped.
3. **A mapping table**: each capability above -> your proposed command path, so coverage is auditable.
4. **Explicit resolutions to P1-P15**, each naming the concept(s) and the word(s) you chose and why.
5. **The hardest naming calls**, where you were torn, with the runner-up and your tie-break reason (so a human can overrule with context).
6. **A short "consistency rules"** section: the small set of invariants your scheme obeys (e.g. read-vs-write signaling, one-word-one-meaning, the generic-vs-specific rule you chose), so future commands can be named by rule rather than taste.

Choose plain, intuitive words. Prioritize a user correctly guessing what a command does from its name. Where you must make a judgment call, make it and justify it briefly.
