# IPD: Adopt the self-commit helper across aw archive/group/rename/research set-assign-mv/ipd set/specs set with tests

- Date: 2026-08-25
- Kind: child
- Concern: With the shared `git_commit_helper.offer_commit` (child 01) in place, the records-mutating verbs must actually adopt it so they offer to commit their own path-scoped changes. Today `research_archive.run_archive` (research_archive.py:284) and `plans_archive.run_archive` (plans_archive.py:189) leave their rename + INDEX-regeneration changeset uncommitted; the `group`/`rename` noun-verb commands (a type-parameterized rename+re-cluster) and the `ipd set`/`spec set`/`specs set` status transitions (an in-place `- Status:` + workflow-history rewrite) likewise leave their change uncommitted. Note the two shapes differ: `archive`/`group`/`rename`/`research set-assign`-`mv` produce a multi-file move + INDEX regeneration; the `set` verbs produce an in-place single-file (or whole-Set) metadata rewrite with NO rename. Both leave uncommitted work worth offering to commit, but the touched-path set is collected differently.
- Scope: Wire `offer_commit` into each records-mutating verb so that after it mutates files + regenerates any INDEX, it collects the EXACT set of paths it touched (moved/renamed/deleted paths + regenerated index files) and calls `offer_commit(...)` with a good per-verb default message. The verb set (with VERIFIED backends, plan-review PR-003/PR-004):
  - `aw archive`: `research_archive.run_archive` (research_archive.py:284) + `plans_archive.run_archive` (plans_archive.py:189). Two direct entry points.
  - `aw group`/`aw rename`: these are TYPE-PARAMETERIZED noun-verb commands dispatched by `_run_noun_verb` (cli.py:5601) through `artifact_types.resolve_backend(type, verb)` (artifact_types.py:78-113) to a per-type backend: `plans_refs.run_set_assign`/`run_mv` (plans), `research_refs.run_set_assign`/`run_mv` (research), and `artifact_rename.run_group_*`/`run_rename_*` (specs, prompts, backlog, walkthroughs, roadmaps, releases). They do NOT "live in plans_refs.py" - that module covers only the plans type. INTEGRATION DECISION (see OQ-02): wire the offer ONCE at the `_run_noun_verb` group/rename dispatch site by having each backend RETURN its touched-path set (or a small result object), rather than editing 3+ backend modules independently; if a backend cannot cleanly surface its touched paths, wire that backend directly. Either way ALL group/rename types must be covered, not just plans.
  - `aw research set-assign`/`mv`: `research_refs.run_set_assign` (research_refs.py:285) / `research_refs.run_mv` (research_refs.py:310), dispatched from the `research` command branch (cli.py:7182). CRITICAL EXACTLY-ONCE INVARIANT (plan-review PR-012): these SAME two `research_refs` functions are ALSO the resolve_backend targets for `aw group research`/`aw rename research` (artifact_types.py:85-86), so they are reached by TWO distinct entry points (the `research` command branch AND `_run_noun_verb`). Therefore the `offer_commit` call MUST live at the DISPATCH/command-branch layer (the two call sites in cli.py), NEVER inside the shared `research_refs` backend function - otherwise `aw group research` would fire the offer once inside the backend AND again at the E-07 dispatch site (double-commit). E-03 makes the backend RETURN its touched paths (no committing inside it); the offer is placed by whoever CALLED it.
  - `aw set` / `aw ipd set` / `aw spec set` / `aw prompts set` / `aw backlog set`: ALL route through the SHARED engine `status_set.run_set_command` (status_set.py:808), which flips `- Status:` + appends workflow-history IN PLACE (a single-file, or whole-Set multi-file, metadata rewrite with NO rename). Wire `offer_commit` ONCE in `run_set_command` so every `set` variant is covered by one integration; do NOT wire it per-caller. The touched-path set is the artifact file(s) actually rewritten.
  - `aw specs set` DUAL-PATH caveat (PR-004): the `specs`/`spec` command branch (cli.py:7257) routes the NO-`--status` form to `status_set.run_set_command(scoped_type="specs")` and the `--status <X> <path>` form to `specs.py:run_set` (specs.py:430). To avoid a MISSED path or a DOUBLE offer, the offer must fire in exactly one place per invocation: since `status_set` already covers the no-flag form, either (a) also add the offer to `specs.py:run_set` for the `--status` form (both single-fire, no overlap), or (b) route both forms through `status_set`. The plan chooses and the tests assert exactly one offer per invocation.
  Each verb passes the PRECISE touched-path list tracked explicitly during the mutation, NOT "whatever is dirty". Add `--commit`/`--no-commit` as a SHARED arg group registered on each records-mutating parser (OQ-01). Per-verb default messages (e.g. `chore(research): archive aged artifacts and regenerate index`, `refactor(plans): regroup set <id> and rewrite refs`, `chore(specs): set <id> status <old> -> <new>`).
- Scope-Paths: agent_workflows/research_archive.py, agent_workflows/plans_archive.py, agent_workflows/plans_refs.py, agent_workflows/research_refs.py, agent_workflows/artifact_rename.py, agent_workflows/status_set.py, agent_workflows/specs.py, agent_workflows/cli.py, tests/
- Status: approved
- Set: selfcommit
- Order: 2
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: jgcm68
- Approval: 2026-08-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED (PR-001..PR-010); corrected architecture (type-parameterized group/rename dispatch, shared status_set engine, specs dual path), fixed the cli.py prompt-helper citation and non-TTY gating divergence, parameterized on_unrelated_staged, split the multi-concern E-item, authored falsifiable V-evidence, filled execution-contract gates. GO - PENDING HUMAN APPROVAL.

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Adopt the shared `offer_commit` helper across `aw archive`/`group`/`rename`/`research set-assign`-`mv`/`ipd set`/`specs set` so each offers, interactively, to path-scoped-commit exactly the files it touched, with `--commit`/`--no-commit` flags and a good per-verb default message.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: adopt in the archive verbs

- [ ] E-01 Add a SHARED `--commit`/`--no-commit` arg group and register it on every records-mutating parser (archive, group, rename, research set-assign/mv, the `set` family) in cli.py; thread the resolved flags onto the args namespace each backend receives (OQ-01).
  - Depends on: none
  - Expected outcome: every named verb accepts `--commit`/`--no-commit`; the flags reach the backend; `--help` shows them.
  - Execution state: pending
- [ ] E-02 Wire `offer_commit` into `research_archive.run_archive` (research_archive.py:284) and `plans_archive.run_archive` (plans_archive.py:189): collect the exact moved/renamed/deleted paths + regenerated INDEX, call the helper with a `chore(<domain>): archive aged artifacts and regenerate index` message (`on_unrelated_staged="scope"`).
  - Depends on: E-01
  - Expected outcome: `aw archive` (research + plans) interactively offers to commit exactly its touched paths; `--no-commit` skips; non-interactive without `--commit` does not auto-commit.
  - Execution state: pending

### Task group 2: adopt in the type-parameterized regroup/rename dispatch

- [ ] E-03 Make the `group`/`rename` backends surface their touched-path set (e.g. return a small `MutationResult(touched_paths, index_paths)`) across `plans_refs`, `research_refs`, and `artifact_rename`, WITHOUT committing or offering inside the backend (the offer is placed by the caller; PR-012 - `research_refs` is shared by two entry points).
  - Depends on: none
  - Expected outcome: each group/rename backend returns the exact set of paths it moved/renamed + the regenerated index paths and performs NO commit itself; a test reads those return values for plans, research, and one artifact_rename type.
  - Execution state: pending
- [ ] E-07 Wire `offer_commit` ONCE at the `_run_noun_verb` group/rename dispatch CALL SITE (cli.py:5601) - i.e. after the resolved backend returns, using its returned touched paths - with a `refactor(<type>): regroup/rename <selector> and rewrite refs` message (`on_unrelated_staged="scope"`), covering ALL types via that single call site. The offer is at the dispatch layer, NOT inside any backend (PR-012). This covers `aw group <type>`/`aw rename <type>` for every type; the SEPARATE `aw research set-assign`/`mv` call site is E-04.
  - Depends on: E-01, E-03
  - Expected outcome: `aw group <type>`/`aw rename <type>` for every supported type offer to commit exactly their moved paths + rewritten index via the single dispatch-site call; flags honored; verified for at least plans, research, and one artifact_rename type (e.g. specs); no in-backend offer.
  - Execution state: pending

### Task group 3: adopt in the shared status-set engine and the specs dual path

- [ ] E-04 Wire `offer_commit` at the `aw research set-assign`/`mv` CALL SITE in the `research` command branch (cli.py:7182), using the touched paths RETURNED by `research_refs.run_set_assign`/`run_mv` (E-03), with a `refactor(research): ...` message (`on_unrelated_staged="scope"`). Do NOT place the offer inside the `research_refs` backend (PR-012): those functions are shared with the `aw group research`/`aw rename research` path wired in E-07, so an in-backend offer would double-fire; the offer belongs at each of the two distinct call sites so each entry point fires exactly once.
  - Depends on: E-01, E-03, E-07
  - Expected outcome: `aw research set-assign`/`mv` offer to commit exactly their touched paths; flags honored; `aw group research`/`aw rename research` (E-07) and `aw research set-assign`/`mv` (E-04) EACH fire exactly one offer with no double-commit.
  - Execution state: pending
- [ ] E-05 Wire `offer_commit` ONCE into the shared `status_set.run_set_command` (status_set.py:808) so every `set` variant (`aw set`/`ipd set`/`spec set`/`prompts set`/`backlog set`) offers to commit exactly the artifact file(s) it rewrote (single-file or whole-Set), with a `chore(<type>): set <selector> status <old> -> <new>` message.
  - Depends on: E-01
  - Expected outcome: each `set` variant offers to commit its own path-scoped metadata rewrite; flags honored; unrelated dirty files never folded in.
  - Execution state: pending
- [ ] E-06 Handle the `aw specs set --status <X> <path>` form that routes to `specs.py:run_set` (specs.py:430) so it fires the offer exactly once (no double-offer with the E-05 status_set path, no missed path); resolve per the PR-004 decision (add the offer here for the `--status` form, or route both forms through status_set).
  - Depends on: E-05
  - Expected outcome: both `aw specs set <id6>` and `aw specs set --status <X> <path>` offer to commit exactly once; a test asserts a single offer per invocation on each form.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `research_archive.run_archive` (research_archive.py:284) and `plans_archive.run_archive` (plans_archive.py:189) are the archive entry points.
- `aw group`/`aw rename` are TYPE-PARAMETERIZED: `_run_noun_verb` (cli.py:5601) resolves a per-type backend via `artifact_types.resolve_backend` (artifact_types.py:78-113). Backends: `plans_refs.run_set_assign`/`run_mv` (plans), `research_refs.run_set_assign`/`run_mv` (research), `artifact_rename.run_group_*`/`run_rename_*` (specs, prompts, backlog, walkthroughs, roadmaps, releases). They do NOT all live in `plans_refs.py`.
- `aw set`/`ipd set`/`spec set`/`prompts set`/`backlog set` ALL route through the ONE shared engine `status_set.run_set_command` (status_set.py:808) - an in-place `- Status:` + workflow-history rewrite (single file or whole Set), NO rename. Wire the offer there once.
- `aw specs set` is DUAL-PATH (cli.py:7257): the no-`--status` form -> `status_set.run_set_command(scoped_type="specs")`; the `--status <X> <path>` form -> `specs.py:run_set` (specs.py:430). Must fire exactly one offer per invocation.
- The repo's yes/no prompt helper is `_confirm` (cli.py:2689); `git_commit_helper.offer_commit` (child 01) already encapsulates the correct non-TTY-no-op gating, so verbs just call it.
- Each verb already knows the files it moves/renames/rewrites and regenerates the INDEX - the touched-path set is available at the mutation site; pass it explicitly, do not re-derive from a dirty scan.
- SHARED-BACKEND / EXACTLY-ONCE (PR-012): `research_refs.run_set_assign`/`run_mv` are reached by TWO entry points - the `research` command branch (cli.py:7182) AND `_run_noun_verb` group/rename (artifact_types.py:85-86). Rule: backends only RETURN touched paths (E-03); `offer_commit` is placed by the CALLER at each dispatch/command-branch call site, so each of the two entry points fires exactly once and the shared backend never double-fires. The same discipline applies wherever a mutation backend is reachable by more than one command.

## Findings

Adoption is mechanical per integration point: collect the touched paths (already known at the mutation site) and call the child-01 helper with `on_unrelated_staged="scope"`. Three real risks: (1) COVERAGE - group/rename fan out over ~8 artifact types across 3 backend modules, so a naive "edit plans_refs.py" misses most types; the fix is to wire once at the type-parameterized dispatch site (E-07) using backend-returned paths (E-03). (2) EXACTLY-ONCE across DUAL PATHS - the `specs.py` `--status` form vs the status_set no-flag form must not double-offer or miss (E-05/E-06). (3) EXACTLY-ONCE across SHARED BACKENDS (PR-012) - `research_refs.run_set_assign`/`run_mv` are reached by both `aw research set-assign`/`mv` and `aw group/rename research`; the offer must live at each call site (E-04, E-07), never inside the shared backend, or `aw group research` double-commits. Tests assert exactly which paths get committed and that each invocation offers exactly once.

## Proposed changes (ordered, validatable)

1. `cli.py`: shared `--commit`/`--no-commit` arg group on every records-mutating parser; thread flags to backends (E-01).
2. `research_archive.py` + `plans_archive.py`: adopt helper (E-02).
3. `cli.py` `_run_noun_verb` group/rename dispatch + backends (`plans_refs.py`, `research_refs.py`, `artifact_rename.py`): surface touched paths, offer once, cover ALL types (E-03).
4. `research_refs.py` set-assign/mv (E-04); `status_set.py` shared `run_set_command` (E-05); `specs.py` `--status` dual path (E-06).
5. `tests/`: per-integration-point offer/commit/skip/no-fold-in, coverage across group/rename types, and exactly-once assertions for the set family + specs dual path.

## Deferred / out of scope (with reason)

- The shared helper itself: child 01 (dependency).

## Scope check

- Over-scope: none.
- Under-scope: none (all six named verb families are covered).

## Required tests / validation

- For each adopting verb/integration point: interactive run commits exactly the touched paths (+ index); `--no-commit` skips; non-interactive without `--commit` does not auto-commit; an unrelated dirty file is never included; no push occurs.
- Coverage: `aw group`/`aw rename` are tested for at least plans, research, AND one `artifact_rename` type (e.g. specs) to prove the dispatch-site wiring covers non-plans types (guards PR-003).
- Exactly-once: `aw ipd set`/`aw spec set` (via status_set) each fire exactly one offer; `aw specs set <id6>` (status_set path) and `aw specs set --status <X> <path>` (specs.py path) each fire exactly ONE offer with no double-commit (guards PR-004).
- The `set` family commits the correct single file for a single-target transition and the correct file SET for a whole-Set transition.

## Spec / documentation sync

- Update each verb's `--help` and AGENTS.md / relevant READMEs to note the interactive self-commit offer and the `--commit`/`--no-commit` flags.

## Open questions

### OQ-01: Should the flags be per-verb or a single shared arg group applied to all?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: a single shared `--commit`/`--no-commit` arg group registered on each records-mutating parser (E-01), for consistent UX across verbs. Non-blocking; a per-verb duplication would still work but is rejected for consistency.

### OQ-02: Wire the group/rename offer at the dispatch site or in each backend?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED (plan-review PR-003): prefer wiring ONCE at the `_run_noun_verb` group/rename dispatch (cli.py:5601), having each backend return its touched-path set, so all ~8 artifact types (across plans_refs, research_refs, artifact_rename) are covered by one call rather than 3+ duplicated call sites. If a specific backend cannot cleanly surface its touched paths without disproportionate change, wire that backend directly instead - but the invariant is that NO group/rename type is left without an offer. Finalize the exact return-shape (e.g. a small `MutationResult(touched_paths, index_paths)`) in implementation; non-blocking because either mechanism satisfies the coverage requirement.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `aw archive --help`, `aw group plans --help`, `aw rename plans --help`, `aw set --help`, and `aw research set-assign --help` output all show `--commit` and `--no-commit`; a test asserts the flags reach each backend's args namespace. Paste the runner output.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: A test drives `research_archive.run_archive` and `plans_archive.run_archive` on a temp repo with an aged artifact and an unrelated dirty file; asserts the offer commits exactly the moved paths + regenerated INDEX, `--no-commit` skips, non-interactive-without-`--commit` is a no-op, and the unrelated dirty file is never committed. Paste pytest output.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: A test calls each group/rename backend (plans_refs, research_refs, and one artifact_rename type) and asserts the returned touched-path/index set exactly matches the files the backend moved/regenerated. Paste pytest output.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: A test drives `aw research set-assign`/`mv` AND `aw group research`/`aw rename research` (both entry points into the shared `research_refs` backend), asserting EACH fires exactly ONE commit offer for its own touched paths with NO double-commit (guards PR-012: the offer is at the call site, not in the backend). Paste pytest output.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: A test drives `status_set.run_set_command` for a single-target transition (commits exactly one artifact file) AND a whole-Set transition (commits exactly the Set's files), asserting the offer fires once, `--no-commit` skips, non-interactive-without-`--commit` is a no-op, and an unrelated dirty file is never included. Paste pytest output.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: A test asserts BOTH `aw specs set <id6>` (status_set path) and `aw specs set --status <X> <path>` (specs.py path) fire exactly ONE commit offer each with no double-commit and no missed path (guards PR-004). Paste pytest output.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: A test exercises the `_run_noun_verb` group/rename dispatch for at least plans, research, AND one artifact_rename type (e.g. specs), asserting each offers to commit exactly its backend-returned moved paths + rewritten index via the single dispatch-site wiring, that a non-plans type IS covered (guards PR-003), and that the offer fires exactly once per invocation. Paste pytest output.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: touch ONLY the declared `Scope-Paths` (research_archive.py, plans_archive.py, plans_refs.py, research_refs.py, artifact_rename.py, status_set.py, specs.py, cli.py, tests/) plus this plan's own file. Scope fence: adopt the child-01 `git_commit_helper.offer_commit` across the records-mutating verbs; do NOT modify the helper itself (child 01 owns it) and do NOT change verb behavior beyond adding the commit offer + the shared `--commit`/`--no-commit` flags. Dependency: child 01 (`cv1rfd`) must be executed first (the helper must exist). Open questions: OQ-01 and OQ-02 are resolved; no blocking question remains. Honesty rule (hard MUST): when reporting tests/validation passed, paste the ACTUAL runner output (the `run_checks.py`/pytest command and its result); never claim success not run. Commit only files this plan changes, path-scoped (`git commit -- <path>`); never `git add -A`/`-a`; never push; never `--no-verify`. On completion perform the terminal transition via `aw ipd begin <plan> --actor <agent/model>` then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`; do NOT hand-edit the terminal transition or move the file by hand. This plan awaits `/plan-review` and explicit human approval (`Status: approved`) before it may be executed.
