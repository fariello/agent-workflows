# IPD: Split initialize_run into a shared core and a thin host hook

- Date: 2026-09-15
- Kind: child
- Concern: `initialize_run` is written twice (409 lines in `oc_runipd.py`, 339 in `agy_runipd.py`) for the same job. Measured at HEAD it carries 15 differing code lines of which only 6 bear a host token, so most of the divergence is DRIFT in shared logic rather than genuine host specificity, and every fix to one copy is a fix the other silently misses. CORRECTED AT REVIEW 2026-09-16: the 15 REPRODUCES exactly and is the most misleading number in this Set, because TWO of the fifteen are the `state` and `queue.append` dict literals, and unpacking them shows the `options` dict carries 23 distinct keys of which SEVEN are oc-only, SIX are agy-only, and only TEN are shared. The host-token count is FOUR, not six. So the divergence inside those two lines is 13 host-specific keys, not drift, and `initialize_run` is the LEAST shared of the five large functions by content even though it looks like the most shared by line count. See F-8 through F-14 and OQ-03.
- Scope: Extract the host-neutral core of `initialize_run` into `runner_shared.py`, leaving each host a thin hook supplying only what is genuinely its own. Logic resolves to the `oc_runipd` version per the maintainer's 2026-09-14 ruling except where a difference is a real capability, which is called out per difference below. RE-SCOPED AT REVIEW: the split is GATED on OQ-03. Beyond the `options` asymmetry, a relocated core evaluating `__file__` would write `runner_shared.py` into `state['driver']['path']`, which TWO consumers use as the host-identity discriminator by basename, so the naive relocation silently makes every run's host unattributable.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_rununify_initialize_run.py, tests/test_run_flag_surface.py, tests/test_dirty_base_gate.py, tests/test_runner_backlog_close.py, tests/test_run_analytics_sources.py, tests/test_run_viewer.py
- Item-Dependencies: executed:sy7uwh
- Status: approved
- Readiness: go-pending-approval
- Set: rununify
- Order: 9
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: orziju
- Approval: 2026-09-17, human ("approved"): Maintainer directive 2026-09-16: the objective is 100% de-duplication of the redundant code between the two runners; readiness attested by the maintainer (not by an agent, not by a review), with the two supporting rulings (source-reading guards are re-based deliberately, never weakened silently; coordinated de-duplication across symbols is permitted) recorded in each plan's OQ-03 and history
- From-Backlog: alw22r

## Workflow history
- 2026-09-17 approved (aw set, --by-human): Maintainer directive 2026-09-16: the objective is 100% de-duplication of the redundant code between the two runners; readiness attested by the maintainer (not by an agent, not by a review), with the two supporting rulings (source-reading guards are re-based deliberately, never weakened silently; coordinated de-duplication across symbols is permitted) recorded in each plan's OQ-03 and history
- 2026-09-16 reviewed (maintainer, --by-human attestation via askme): MAINTAINER ATTESTATION 2026-09-16: readiness set to `go-pending-approval` BY THE MAINTAINER, not by an agent and not by a review. The prior `no-go` was written by this plan's own 2026-09-16 review round while its blocking OQ-03 was genuinely open. The maintainer then answered that question directly in an interactive session on 2026-09-16 with a single Set-wide directive ('at the end of the SET, there should be one code base shared by the two runners that contains 100% of the otherwise redundant code that currently is duplicated between the two runners'), plus two supporting rulings that dissolved the premises the finding rested on: TESTS ARE NOT IMMOVABLE (a source-reading guard is re-based deliberately as part of the work, never weakened silently; the maintainer cited this repository's own precedent at `tests/test_nested_tty_noninteractive.py:190-203`, whose 41 related tests pass at this HEAD) and COORDINATED DE-DUPLICATION IS PERMITTED (many functions may be de-duplicated together before testing, so a still-double-defined dependency is an ordering matter rather than a blocker). Asked directly how the stale verdict should be cleared, the maintainer chose to attest it themselves rather than fund a further review round. THE ALTERNATIVE WAS PRICED AND REJECTED ON EVIDENCE: the 2026-09-16 round cost roughly 2.5 hours across nine items and produced 1,479 lines of review prose while clearing nothing, and the comparable 2026-09-13 round cost $106.07 and raised four NEW blocking questions, so a further round was not expected to yield a clean sheet. NO AGENT WROTE THIS VALUE ON ITS OWN AUTHORITY. HONEST LIMIT: no independent reviewer re-examined this plan's contents; that assurance lives in the 2026-09-16 round 1 record, not in this attestation. Recorded here because the auto-approve predicate reads this field FIRST (`plan_readiness.is_plan_review_approved`), so a stale `no-go` is a live refusal that would have silently skipped this plan when the Set executed.
- 2026-09-16 reviewed (aw set): Reviewed 2026-09-16 by /plan-review: REVIEWED - OPEN QUESTIONS, NO-GO. 14 findings (PR-001..PR-014), 12 FIXED, PR-001/PR-002 OPEN and escalated as blocking OQ-03. The 15-differing-line count reproduces and HIDES the divergence: two of the fifteen are dict literals whose `options` key set is 7 oc-only, 6 agy-only, 10 shared. A relocated core's `__file__` would also destroy the host-identity discriminator two analytics consumers read.

- 2026-09-16 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO; PR-001 through PR-014 (12 FIXED, PR-001 and PR-002 OPEN and escalated as the new blocking OQ-03). THE HEADLINE NUMBER IS EXACT AND MAXIMALLY MISLEADING, which makes this the most interesting of the four split children reviewed. Verified: 409/339 raw lines, 241/236 code lines, EXACTLY 15 differing lines under AST normalization with docstrings stripped, similarity 0.9345 (the highest in the Set). But TWO of those fifteen are the `state` dict and the `queue.append` dict, single lines after normalization and enormous in content: unpacked, the `options` dict carries 23 distinct keys of which SEVEN are oc-only (`opencode`, `model`-adjacent `variant`, `agent`, `launch_profile`, `auto`, `validate`, `no_audit`), SIX are agy-only (`agy_executable`, `effort`, `timeout`, `new_session`, `dangerously_skip_permissions`, `no_verify`) and only TEN are shared. So by CONTENT this is the least shared of the five large functions while looking like the most shared by line count, and a "relocation with a parameter" would need to parameterize thirteen keys. The host-token count is FOUR, not the plan's six. THE SECOND BLOCKER IS A HAZARD THE PLAN NEVER NAMES, and it is the sharpest one found in any of these four reviews: `initialize_run` writes `state['driver'] = {'path': str(Path(__file__).resolve()), 'sha256': sha256_file(Path(__file__))}` (`oc_runipd.py:3562`, `agy_runipd.py:2345`). `__file__` is evaluated in the DEFINING module, so a core relocated to `runner_shared` writes `runner_shared.py` for BOTH hosts, and `run_analytics_sources.driver_generation` (`:198-207`) maps the BASENAME through `DRIVER_GENERATIONS` to decide the host while `run_viewer.py:858-870` string-matches `oc_runipd`/`agy_runipd` to label a run. Both would silently return `unknown`, making every future run host-unattributable in analytics with no test failing, since neither consumer has a driver-path test over the runners. F-2's stated hazard (the frozen queue shape read by resume) is REAL but I measured it MILDER than claimed: both hosts already write the identical 12-key set and differ only in the ORDER of `kind` and `order`, which JSON round-trips do not preserve as significant. F-5 IS FACTUALLY WRONG in the direction that matters: it says "agy writes a `kind` key into each queue entry; oc does not", and both write it; what differs is that agy DERIVES it via `_plan_kind` because `agy.PlanRecord` lacks the field (`kind in oc: True`, `kind in agy: False`, verified live), which is F-4's point and makes F-5 a duplicate with an inverted claim. ELEVEN pins read `initialize_run`'s source (8 in `test_run_flag_surface.py`, 2 in `test_dirty_base_gate.py`, 1 in `test_runner_backlog_close.py`), TWO of them ORDERING pins that split the source on the literal string `run_dir = state_root` to prove refusals precede durable state (`:745`, `:1340`); 183 tests pass across those three files today. Closure: 34 free names, 16 resolve in `runner_shared`, 8 still double-defined, plus `__file__` and the oc-only `resolve_launch_pair`/`launch_profile_record` which agy has NO equivalent of (zero `runner_profiles` references in agy against 17 in oc), so F-3's warning not to collapse the launch half into the verification half is correct and load-bearing. REVISED IN PLACE: the `options` key table added to the Goal, the `__file__` hazard added as F-9 with its two consumers, F-5 corrected, F-2 downgraded with the measurement, gating E-01 added, the split converted to E-04 (analysis), E-05 added as a guard suite, five test files fenced, and non-vacuity made bidirectional. NOT DECIDED: which of four routes, since a 13-key host-specific `options` dict may mean this function is better left host-owned.

- 2026-09-15 to-review (aw set): Authored 2026-09-15 from a fresh measurement at HEAD; resolves part of the rununify parent's placeholder child rows per the maintainer's 2026-09-14 oc-preferred ruling.

- 2026-09-15 draft (opencode/its_direct-pt3-claude-opus-5): created.
- 2026-09-15 authored (opencode/its_direct-pt3-claude-opus-5): authored from a per-symbol diff measured at HEAD; the differing lines were counted and classified rather than estimated.

## Goal

Give `initialize_run` ONE implementation of everything that is not host-specific, so a fix lands once and reaches
both hosts, without changing what either runner does.

RESTATED AT REVIEW 2026-09-16, because the fifteen-line figure conceals rather than reveals. Two of the
fifteen differing lines are dict literals. Unpacked, the `options` dict this function freezes is where the
divergence actually lives:

| `options` key class | Count | Members |
|---|---|---|
| SHARED (both hosts) | 10 | `action`, `full_auto`, `isolate_worktree`, `max_items_per_session`, `model`, `output_mode`, `self_finalize`, `session`, `stall_timeout`, `verbosity` |
| OC-ONLY | 7 | `opencode`, `variant`, `agent`, `launch_profile`, `auto`, `validate`, `no_audit` (plus the conditional `verify_*` block) |
| AGY-ONLY | 6 | `agy_executable`, `effort`, `timeout`, `new_session`, `dangerously_skip_permissions`, `no_verify` |

Thirteen of twenty-three keys are host-specific, and several are not cosmetic: `launch_profile` exists
only because oc has a launch-profile store (17 `runner_profiles` references in `oc_runipd`, ZERO in
`agy_runipd`), and `agy_executable` is read at `agy_runipd.py:3010` to resolve the binary. A shared writer
must therefore parameterize thirteen keys, which is not a hook, it is the function's whole output.

And the closure test adds a trap no other child in this Set carries:

| Closure class | Count | Consequence |
|---|---|---|
| Resolves in `runner_shared` today | 16 | moves for free |
| Constant, defined twice, equal | 2 (`DEFAULT_RUNBOOK_TEXT`, `DEFAULT_STALL_TIMEOUT`) | can move with the core |
| Already ONE object (agy imports from oc, or both import a third module) | 4 (`announce_run_order`, `run_order_rationale`, `is_plan_review_approved`, `argparse`) | relocation, not de-duplication |
| OC-ONLY, agy has no equivalent | 2 (`resolve_launch_pair`, `launch_profile_record`) | genuine capability asymmetry; see F-3 |
| STILL DEFINED TWICE | 8 (`EmptyStatusSelection`, `build_dynamic_manifest`, `enforce_dependency_preflight`, `enforce_requested_action`, `expand_selectors`, `parse_plan_file`, `set_plan_approved`, `write_report`) | each becomes an injected parameter |
| `__file__` | 1 | **CANNOT be relocated at all.** See F-9. |

So the honest goal for THIS plan, pending OQ-03, is: MEASURE the `options` partition and the closure, PIN
the driver-identity contract that a naive relocation would break, DELIVER the analysis the Set needs, and
GUARD what was measured, rather than perform a relocation whose shared writer would take thirteen key
parameters and would silently make every run host-unattributable.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

SCOPE GATE ADDED AT REVIEW 2026-09-16. E-01, E-02, E-03 and E-05 are authorized unconditionally: they
measure, they pin the driver-identity contract that has no test today, they enumerate the pins, and they
guard what was measured. THE SPLIT ITSELF IS GATED on OQ-03, which is `Blocking: yes`; E-04 delivers the
ANALYSIS the decision needs and performs no relocation.

### Task group 1: measure before touching

- [x] E-01 MEASURE THE `options` PARTITION AND THE CLOSURE at execution HEAD, and refuse to proceed to E-04 on a stale list. TWO measurements, because the line count is the wrong unit here. (a) Unpack the `state['options']` dict on BOTH hosts and classify every key as shared / oc-only / agy-only; the Goal table records 10 / 7 / 6 at review. (b) Run the closure test: parse `oc_runipd.initialize_run`, collect every free name resolving at MODULE level, and classify into the six classes of the second Goal table. NAME `__file__` SEPARATELY, because it is not a symbol to inject but a construct whose meaning CHANGES on relocation (F-9). This E-item writes NO runner logic.
  - Depends on: none
  - Expected outcome: both tables reproduced at execution HEAD with their members; the host-specific `options` key count stated; the still-double-defined count stated; `__file__` called out as non-relocatable rather than listed as a dependency.
  - Execution state: performed

- [x] E-02 PIN THE DRIVER-IDENTITY CONTRACT, which has NO test today and which a naive relocation silently breaks (F-9). Write tests asserting that for BOTH hosts, a run initialized by that host records a `state['driver']['path']` whose BASENAME is that host's runner module, and that `run_analytics_sources.driver_generation(state)` returns `oc_runipd` / `agy_runipd` accordingly rather than `unknown`, and that `run_viewer`'s label resolves to `OpenCode` / `Antigravity`. THEN write the characterization tests the parent's constraint requires for every branch the split would move, prioritizing agy branches with no existing coverage. This E-item writes TESTS ONLY and changes no runner logic.
  - Depends on: E-01
  - Expected outcome: a committed suite that passes against UNMODIFIED code, that FAILS if `state['driver']['path']` ever names a module other than the initiating host's runner, and that pins the branches a split would move; the previously uncovered agy branches named.
  - Execution state: performed

### Task group 2: the pin inventory

- [x] E-03 ENUMERATE THE ELEVEN SOURCE-INSPECTION PINS and state, per pin, whether a thin caller can satisfy it. F-10 lists them; the deliverable is the per-pin verdict, and for the TWO ORDERING pins that split the source on the literal `run_dir = state_root` (`tests/test_run_flag_surface.py:745`, `:1340`) a statement of what behavioral assertion would preserve the same guarantee, which is that a refusal happens before any durable state exists. Do NOT edit a test in this item. Record the baseline first (183 passed across the three files at review) so a later red is attributable.
  - Depends on: E-01
  - Expected outcome: an eleven-row table (file:line, what it asserts, thin-caller verdict, and for the two ordering pins the behavioral equivalent), plus the pasted green baseline.
  - Execution state: performed

### Task group 3: the split, GATED

- [x] E-04 DO NOT PERFORM THE SPLIT UNTIL OQ-03 IS ANSWERED, and record the analysis rather than silently skipping it. The deliverable is the disclosure, so an executor cannot mistake the omission for an oversight and "finish" it later. State, from E-01 and E-03: (a) how a shared writer would supply THIRTEEN host-specific `options` keys, and whether that is a hook or simply the function's output re-spelled; (b) how `__file__` would be handled, given that passing the caller's module path in is the ONLY correct answer and that it must be proven by E-02's test rather than assumed; (c) the eleven pins and the two ordering ones; (d) whether the oc-only `resolve_launch_pair`/`launch_profile_record` pair should stay host-owned, given agy has ZERO `runner_profiles` references, and what that implies for a shared writer that must emit `launch_profile` for one host and not the other; and (e) a route recommendation with the reason. Change no runner logic in this item.
  - Depends on: E-01, E-03
  - Expected outcome: a written analysis sufficient for the maintainer to answer OQ-03 without re-deriving the measurement, explicitly answering whether a 13-of-23-key host-specific writer is worth sharing at all.
  - Execution state: performed

### Task group 4: proof

- [x] E-05 Add `tests/test_rununify_initialize_run.py` asserting WHAT THIS PLAN ACTUALLY DID, driven by a named table rather than by the aspiration: the `options` key partition asserted mechanically per host (so a key silently changing class fails), the closure classification asserted, `__file__` asserted to be evaluated in each RUNNER module (not in `runner_shared`), and the eight double-defined symbols asserted STILL double-defined (the inverse assertion, so a later agent cannot "complete" the split piecemeal without the OQ-03 decision). If OQ-03 authorizes the split, extend this file with shared-core object identity and the repo-wide AST anti-re-fork scan (per the parent's F10, not a pairwise check); do NOT write those assertions while the split is ungated, because a test asserting a state the code is not in is a failing test, not a guard.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: a suite that fails if the `options` partition or the closure regresses, if the driver identity moves to a shared module, or if a pinned double definition is unilaterally collapsed; and that does NOT assert an unexecuted split.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `runner_shared.py` is the established home for host-neutral runner logic and imports no runner, so it
  can hold the core without a cycle. It already uses NAME/VALUE INJECTION for exactly this shape
  (`run_checked(..., env_builder=)`, `save_state(..., write_report=)`, `resume_via_launcher(launcher, ...)`),
  which is the pattern the hook should follow rather than a new mechanism.
- `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import` forbids a runner-to-runner
  import, so the core must land in `runner_shared` and never be reached by importing the other host.
  CORRECTED AT REVIEW: that guard is a SUBSTRING check for `"import oc_runipd"` /
  `"import agy_runipd"` (`tests/test_review_findings_cascade.py:308-313`), which agy's
  `from agent_workflows.oc_runipd import (...)` form does not match; agy uses it ten times, and two of
  the names this function closes over (`announce_run_order`, `run_order_rationale`) are single objects
  precisely BECAUSE agy imports them from oc. The rule that does hold is `runner_shared`'s own, asserted
  by AST at `tests/test_runner_shared.py:955`.
- `__file__` IS NOT A SYMBOL AND DOES NOT RELOCATE. It is evaluated in the module where the code is
  DEFINED, so a core moved to `runner_shared` writes `runner_shared.py` into `state['driver']['path']` for
  both hosts. `run_analytics_sources.driver_generation` (`:198-207`) maps the BASENAME through
  `DRIVER_GENERATIONS` (`:133-138`), and `run_viewer.py:858-870` string-matches `oc_runipd`/`agy_runipd`,
  so both would report `unknown`. No existing test covers this for the runners; E-02 writes it.
- ELEVEN PINS READ THIS FUNCTION'S SOURCE, across three test files, TWO of them ordering pins that split
  on the literal `run_dir = state_root`. See F-10. They pass today: 183 tests across the three files,
  measured at review. A thin caller satisfies none of the eleven.
- AGY HAS NO LAUNCH-PROFILE CONCEPT AT ALL: zero `runner_profiles` references in `agy_runipd` against 17
  in `oc_runipd`, and `launch_profile_record`/`resolve_launch_pair` exist only on oc. So F-3's instruction
  not to collapse the launch half into the verification half is not stylistic; there is no agy half to
  collapse into. `tests/test_runner_profiles_e2e.py` (34 tests, green at review) reads
  `state["options"]["launch_profile"]["config_digest"]` directly.
- The parent Set forbids a child changing what a runner DOES, and forbids reconciling a symbol the
  characterization baseline has not pinned. E-01 exists to satisfy the second constraint.
- The execution contract forbids `git add -A`; commit only the declared `Scope-Paths`, path-scoped.

## Findings

| # | Sev | Where | Finding |
|---|---|---|---|
| F-1 | HIGH | measured at HEAD | `initialize_run` differs in only FIFTEEN code lines, and MOST of them disappear once child 06 unifies `PlanRecord`: agy's `kind is None -> _plan_kind(p_path)` fallback exists solely because its record lacked the field. Ordering this after child 06 shrinks the work rather than duplicating it. |
| F-2 | HIGH | `initialize_run`, both hosts | THE HAZARD THIS SPLIT CARRIES: The frozen `state['queue']` shape is read by RESUME. If the two hosts write different queue-entry keys today, a shared writer changes what a resume of an in-flight run finds. Prove a pre-existing run directory from BOTH hosts still resumes. **MEASURED AT REVIEW AND MILDER THAN CLAIMED, so the effort belongs elsewhere.** Both hosts write the IDENTICAL 12-key set (`position`, `id6`, `setid`, `configured_file`, `dependencies`, `kind`, `order`, `from_backlog`, `initial_status`, `action`, `status`, `attempts`); the sets are equal and only the ORDER of `kind` and `order` differs, which JSON round-trips do not treat as significant. So the queue-shape risk is LOW. The resume-proof requirement stays (it is cheap and it is the right shape of evidence), but the SEVERE hazard in this function is F-9's, which the plan does not mention at all. |
| F-3 | MED | `initialize_run` | DIFFERENCE, verification resolution: oc calls `resolve_launch_pair(args)`, agy calls its own `resolve_verification_decision(args)` which already delegates to `runner_shared.resolve_verification_decision`. Plan `ybkmzp` built that shared resolver and wired BOTH hosts to it; oc's `resolve_launch_pair` additionally resolves the LAUNCH profile. Keep both concerns, and do not collapse the launch-profile half into the verification half. |
| F-4 | MED | `initialize_run` | DIFFERENCE, the `kind` fallback: agy re-reads `- Kind:` from disk when the manifest entry lacks it. Child 06 deletes `_plan_kind`, so this branch must be GONE by the time this plan runs, not ported. |
| F-5 | MED | `initialize_run` | ~~DIFFERENCE, the queue entry: agy writes a `kind` key into each queue entry; oc does not.~~ **RETRACTED AT REVIEW: THE CLAIM IS INVERTED AND THE FINDING IS A DUPLICATE.** Measured: BOTH hosts write `kind` into every queue entry, and the twelve-key sets are equal (see F-2). What actually differs is HOW the value is obtained: oc reads `plan.get('kind')` because `oc.PlanRecord` carries the field, while agy falls back to `_plan_kind(p_path)` because `agy.PlanRecord` does NOT (`kind in oc: True`, `kind in agy: False`, verified live). That is exactly F-4's finding, so F-5 adds nothing except an incorrect assertion. Superseded by F-4. |
| F-6 | MED | `initialize_run` | DIFFERENCE, two shared-gate calls: `enforce_draft_admission_gate` and `enforce_mixed_type_gate` differ only in wrapped-line formatting after normalization; no behavioral difference. **CORRECTED AT REVIEW: they differ by the `host=` ARGUMENT, not by formatting.** Both pass `host='oc'` versus `host='agy'` into the shared gate (visible in the AST-normalized diff), which is a genuine host-token parameter and is two of the four host-token lines. The conclusion (no behavioral difference in the CALLER) holds; the stated reason does not. Note `tests/test_run_flag_surface.py:1564` asserts each runner's `initialize_run` contains EXACTLY ONE call site for each gate, so a shared writer must not change the count. |
| F-7 | MED | `initialize_run` | DIFFERENCE, the state dict: differs only by the keys implied above. **MEASURED AT REVIEW AND THIS IS THE PLAN'S CENTRAL UNDERSTATEMENT.** "Differs only by the keys" spans 13 host-specific keys out of 23 in `options` alone (7 oc-only, 6 agy-only, 10 shared; see the Goal table). Three are not cosmetic: `launch_profile` exists only because oc has a profile store, `agy_executable` is read at `agy_runipd.py:3010` to resolve the binary, and `no_audit`/`no_verify` are opposite-polarity spellings of the same concept. Promoted in substance to F-8. |
| F-8 | BLOCKER | the plan's own method; measured at HEAD `4602befb` | **THE FIFTEEN-LINE COUNT IS EXACT AND CONCEALS THE DIVERGENCE.** Two of the fifteen differing lines are the `state` and `queue.append` dict literals, which are one line each only after AST normalization. By CONTENT this is the LEAST shared of the five large functions (13 of 23 `options` keys host-specific) while having the HIGHEST line-level similarity (0.9345). A shared writer would have to parameterize thirteen keys, which is not a hook supplying host specifics, it is the function's entire output supplied by the caller. The plan measured body difference and inferred liftability, the same error as siblings `i3d6ml`, `ty3cj6` and `yrqyxb`, but here the line count actively hides the problem rather than merely failing to reveal it. |
| F-9 | BLOCKER | `oc_runipd.py:3562-3563`, `agy_runipd.py:2345-2346`; `run_analytics_sources.py:198-207`, `:133-138`; `run_viewer.py:858-870` | **A RELOCATED CORE SILENTLY DESTROYS THE HOST-IDENTITY DISCRIMINATOR, and the plan never mentions it.** `initialize_run` writes `state['driver'] = {'path': str(Path(__file__).resolve()), 'sha256': sha256_file(Path(__file__))}`. `__file__` is evaluated in the DEFINING module, so a core in `runner_shared` writes `runner_shared.py` for BOTH hosts. `run_analytics_sources.driver_generation` maps the BASENAME through `DRIVER_GENERATIONS` (`oc_runipd.py` -> `oc_runipd`, `agy_runipd.py` -> `agy_runipd`) and its docstring records that "the basename is the ONLY discriminator that works"; `run_viewer` string-matches `oc_runipd`/`agy_runipd` to label a run OpenCode or Antigravity. Both would return `unknown` for every run created after the split, and NO existing test covers the runners' driver path, so the whole suite would stay green while run analytics lost host attribution permanently. The only correct handling is to pass the CALLER's module path into the core, proven by a test. E-02 writes that test; the hazard is why E-02 precedes any split. |
| F-10 | HIGH | three test files, eleven pins | **ELEVEN PINS READ `initialize_run`'s SOURCE AND A THIN CALLER SATISFIES NONE.** Eight in `tests/test_run_flag_surface.py` (`:370` `enforce_mixed_type_gate` present; `:676` `resolve_retry_budget` present; `:745` ORDERING, splits on `run_dir = state_root` and requires `refuse_unimplemented_run_flags` in the prefix; `:775` `freeze_run_policy_flags` present; `:874` the `full_auto` default spelling; `:1319` an AST call-set containing `runner_shared.enforce_draft_admission_gate`; `:1340` ORDERING, splits on `run_dir = state_root` and additionally requires `expand_selectors` to precede the draft gate; `:1564` EXACTLY ONE call site each for the two gates), two in `tests/test_dirty_base_gate.py` (`:179` `report_untracked_dirt_at_run_start` present, `:191` it must fall between `refuse_unimplemented_run_flags` and `expand_selectors(`), one in `tests/test_runner_backlog_close.py` (`:255` the literal `"from_backlog"`). THE TWO ORDERING PINS (`:745`, `:1340`) plus `test_dirty_base_gate.py:191` encode spec 2.5a's requirement that a refusal precede any durable state. 183 tests pass across the three files at review. None was fenced; all three are now. |
| F-11 | MED | `resolve_launch_pair`, `launch_profile_record` | **A GENUINE CAPABILITY ASYMMETRY, and F-3 is right to protect it.** `agy_runipd` contains ZERO references to `runner_profiles`; `oc_runipd` contains 17. So `launch_profile` is not a key agy forgot, it is a concept agy does not have, and `resolve_launch_pair`/`launch_profile_record` have no agy counterpart at all. Under the maintainer's ruling this is an A / NOT-A case, not an oc-preferred case. `tests/test_runner_profiles_e2e.py` (34 tests, green at review) reads `state["options"]["launch_profile"]["config_digest"]` directly, so a shared writer that emitted the key for both hosts, or for neither, would break it or fabricate provenance agy cannot supply. |
| F-12 | MED | `tests/test_runner_shared.py:1148` | The `save_state` census is NOT affected here (this function calls `atomic_write_json` directly, not `save_state`), which is worth stating because the three sibling children all trip it. Verified: zero `save_state` call sites inside `initialize_run` on either host. So F-12 is a NEGATIVE finding recorded to save the executor a measurement. |
| F-13 | MED | E-02/E-03/E-04 right-sizing as authored | The original E-02 bundled the relocation of a 409-line function, thirteen `options` key decisions, the `__file__` hazard (unnamed), eight injected dependencies, and eleven pin repairs into ONE pass, which the count-based lint cannot see. The re-scoped items are two measurements, one identity-pinning suite, one pin inventory, one written analysis, and one guard suite: one focused pass each. |
| F-14 | LOW | `Item-Dependencies: executed:sy7uwh` | THE DECLARED EDGE IS WELL FOUNDED, unlike three others in this Set, and that is worth recording. F-1/F-4 are correct that agy's `_plan_kind` fallback exists only because `agy.PlanRecord` lacks `kind`, and sibling `sy7uwh` is exactly the plan that unifies the record; `_plan_kind` still exists at `agy_runipd.py:1660`. HOWEVER `sy7uwh` is itself `reviewed`/`no-go` with its own blocking question about that helper's second caller, so this edge points at a plan that cannot currently execute. Worth the maintainer's attention when sequencing, not a defect in this plan. |

## Proposed changes (ordered, validatable)

1. Measure the `options` key partition and the closure at execution HEAD, naming `__file__` as
   non-relocatable rather than as a dependency (E-01).
2. Pin the driver-identity contract that has no test today, then characterize the branches a split
   would move (E-02).
3. Enumerate the eleven source-inspection pins with a per-pin verdict and a behavioral equivalent for
   the two ordering pins (E-03).
4. Record the split analysis as a DELIVERABLE for OQ-03 rather than performing it (E-04).
5. Add the guard suite for what was measured, including the inverse assertions (E-05).

## Deferred / out of scope (with reason)

- The other four large functions of this Set, each owned by its own sibling child, because each is a
  distinct seam and the parent forbids a child exceeding one cohesive seam.
- The 48 no-disagreement symbols (child 03), the 8 host-string symbols (child 04), the two behavior
  conflicts (child 05), and the record type (child 06). All are ordered BEFORE this plan so their
  results are available rather than re-derived. NOTE child 03 was re-scoped at its review from 48 symbols
  to 9, so those results are thinner than this sentence assumes; of this function's eight double-defined
  closure names, child 03 as re-scoped lifts NONE.
- THE SPLIT ITSELF, deferred to OQ-03 rather than attempted. Stated plainly because a reader will
  otherwise assume it was forgotten: a shared writer must supply thirteen host-specific `options` keys and
  must be handed the caller's module path, or it silently makes every run host-unattributable (F-9). Both
  are decisions above this plan's authority.
- UNIFYING `resolve_launch_pair` / `launch_profile_record` ACROSS HOSTS, because agy has no
  launch-profile concept to unify with (F-11). This is an A / NOT-A case under the maintainer's ruling,
  not an oc-preferred case, and it is folded into OQ-03(d) rather than decided here.
- Any behavior change, feature addition, or flag change. This plan as re-scoped changes NO product code:
  every item measures, pins, enumerates, analyses, or guards.

## Scope check

- Over-scope: none. As re-scoped this plan writes tests and analysis only; it modifies no product module.
  Five test paths are declared: three are the pin files E-03 must READ without editing, and two
  (`tests/test_run_analytics_sources.py`, `tests/test_run_viewer.py`) are where E-02's driver-identity
  assertions may most naturally live if the executor prefers extending an existing suite to creating one.
- Under-scope: this plan does not perform the split it is named for. That is deliberate and gated
  (OQ-03), not an omission: E-04's deliverable is the analysis the maintainer needs. It also does not
  attempt to shrink `initialize_run`, which remains a legitimate later refactor.

## Required tests / validation

1. E-01's TWO tables, reproducible: the `options` key partition per host (10 shared / 7 oc-only / 6
   agy-only at review) and the closure classification (34 names, 16 resolving, 8 double-defined), with the
   command that produced each and the HEAD. `__file__` must appear as NON-RELOCATABLE, not as a dependency.
2. E-02's driver-identity suite, green against UNMODIFIED code: for BOTH hosts, `state['driver']['path']`
   basename is that host's runner module, `run_analytics_sources.driver_generation(state)` returns
   `oc_runipd`/`agy_runipd` rather than `unknown`, and `run_viewer`'s label resolves to
   `OpenCode`/`Antigravity`. Plus the characterization tests for the branches a split would move, with the
   previously uncovered agy branches named. Both hosts' existing suites alone are NOT sufficient, because
   the parent measured them as asymmetric (95 oc tests versus 21 agy at the time).
3. E-03's eleven-row pin table plus the pasted GREEN BASELINE of the three pin files. Measured at review:
   `python3 -m pytest tests/test_run_flag_surface.py tests/test_dirty_base_gate.py
   tests/test_runner_backlog_close.py -o addopts=""` gave `183 passed`. Re-take at execution HEAD; a
   divergence from 183 is information, not noise.
4. THE RESUME PROOF F-2 asks for, kept because it is cheap and correctly shaped: a pre-existing run
   directory from BOTH hosts still resumes. Note the measurement (identical 12-key sets, differing only in
   `kind`/`order` position) makes this a confirmation rather than a discovery.
5. `tests/test_rununify_initialize_run.py` (new): the `options` partition asserted per host; the closure
   classification asserted; `__file__` asserted to be evaluated in each RUNNER module and not in
   `runner_shared`; the eight double-defined symbols asserted STILL double-defined.
6. NON-VACUITY, BIDIRECTIONAL. Two controls, both pasted. (a) Move ONE `options` key from the oc-only set
   to the shared set in the test's table and show the new suite FAILS, naming the key; restore. (b) Change
   the driver-path assertion to accept `runner_shared.py` and show E-02's suite FAILS, proving it would
   catch F-9's hazard; restore. A guard that only fails one way does not pin a boundary.
7. `tests/test_runner_profiles_e2e.py` green (34 tests at review), because it reads
   `state["options"]["launch_profile"]["config_digest"]` directly and is the suite F-11's asymmetry would
   break first.
8. `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` green.
9. Bare `python3 -m pytest`, summary pasted, no new failure against a baseline taken at YOUR OWN HEAD
   before changing anything. Sibling `i3d6ml`'s review measured a load-dependent timeout that passes in
   isolation, so reproduce any single failure against the pre-change baseline before attributing it here.

## Spec / documentation sync

No `.spec.md` change expected: this is an internal refactor with no operator-visible contract change. IF
execution finds that a spec sentence describes the divergence being removed, amend it in the SAME change
and add the spec path to `Scope-Paths`, per the repository's spec-amendment rule.

REVIEWED 2026-09-16 AND SHARPENED, because two specs bear on this function more directly than the original
sentence suggests. FIRST, `tests/test_run_flag_surface.py:1338` cites SPEC 2.5a by name for the rule that
the draft gate runs "after resolution, BEFORE any lease or session", and `:745` asserts the same shape for
`refuse_unimplemented_run_flags`; those are the two ordering pins, so converting either to a behavioral
assertion touches a spec-stated guarantee and must carry the amendment in the same change with the spec
path declared. SECOND, `state['driver']` is consumed by run analytics as the HOST DISCRIMINATOR (F-9), so
if any spec or the analytics contract documents that field, changing what writes it is an
operator-visible change, not an internal refactor. E-04 must surface both before a route is chosen. As
re-scoped this plan changes no product code, so it forces no amendment today.

## Open questions

### OQ-01: Where exactly does the hook boundary belong?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: At the points Findings names as genuinely host-specific, and nowhere
  else. The test is mechanical rather than aesthetic: if a candidate boundary would require the shared
  core to contain an `if host == ...` branch, the boundary is in the wrong place, because that branch is
  the duplication this Set exists to remove wearing a different shape.

### OQ-02: What if the split cannot be done without changing behavior?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: STOP AND REPORT rather than proceeding. The parent's hard constraint
  is that a child may not change behavior, and E-02's characterization suite is what makes a violation
  visible instead of silent. A partial split that leaves a smaller shared core is an acceptable outcome
  and is strictly better than a complete split that moves behavior; say which branches were left behind
  and why. CONFIRMED AT REVIEW 2026-09-16, AND THE CONDITION HAS OCCURRED. F-9 is the clearest instance in
  this Set of a split that WOULD change behavior invisibly: the `__file__` relocation changes what every
  run records about its own host, and no existing test would notice. F-8's `options` measurement is the
  second instance. So the re-scope below is this plan obeying its own instruction.

### OQ-03: A shared writer needs thirteen host-specific `options` keys and cannot own `__file__`. Which route does the Set take?

- Blocking: yes
- Finding: PR-001, PR-002
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-16, and the answer is ROUTE (A)
  AS THE OBJECTIVE, with the route's stated obstacles ruled to be work rather than blockers. The
  maintainer's directive, given directly: "at the end of the SET, there should be one code base shared
  by the two runners that contains 100% of the otherwise redundant code that currently is duplicated
  between the two runners." So DO THE SPLIT. Routes (C) and (D) are refused: both leave this function
  duplicated, which the directive forbids. Route (B)'s re-ordering is PERMITTED as a tactic (see below)
  but is not itself the answer, because it defers rather than achieves.
  THE TWO OBSTACLES THIS QUESTION RESTED ON WERE BOTH RULED ON DIRECTLY, and both dissolve:
  (1) TESTS ARE NOT IMMOVABLE. Asked whether the source-reading pins prevent this work, the maintainer's
  answer was that they do not, and this repository has ALREADY adapted such a guard for shared code:
  `tests/test_nested_tty_noninteractive.py:190-203` counts the shared file's launch sites toward BOTH
  runners, its docstring records why, and all 41 tests in that file plus `tests/test_lane_tool_identity.py`
  pass at this HEAD. A source-reading pin is therefore something to UPDATE DELIBERATELY as part of the
  work: re-base it on the code's new location, record what it now asserts, and prove it still catches the
  regression it was installed for (an injected-regression test, which several of these pins already have).
  WHAT REMAINS FORBIDDEN is WEAKENING a guard silently, i.e. lowering a threshold or deleting an assertion
  so a failure disappears. Re-basing is not weakening. Where a pin asserts the ORDER of safety gates, the
  ordering property must survive the move; assert it on the shared implementation, and if a behavioral
  assertion can replace a source-text one without losing coverage, prefer it and say so.
  (2) THE INJECTED-DEPENDENCY COUNT IS NOT A VETO, AND THE MECHANISM IS ALREADY RULED. This question
  treated N injected parameters as a reason to stop, and cited the maintainer's 2026-09-03 `818uru`
  OQ-02 ruling as being against it. That reads the ruling backwards. The ruling ESTABLISHED the
  mechanism to use: `runner_shared` owns the real function taking each outside dependency as an explicit
  PARAMETER, and each runner keeps a ONE-LINE wrapper at the ORIGINAL name and ORIGINAL signature that
  binds its own dependency (see the executed plan's E-02 note). What that ruling rejected was threading a
  parameter through ~86 CALL SITES, which the wrapper form specifically avoids. So a shared core with N
  parameters plus a thin per-host wrapper IS the sanctioned form, not a violation of it.
  (3) SIBLING COUPLING IS NOT A BLOCKER EITHER. The maintainer confirmed directly that many functions may
  be de-duplicated together before testing, so a dependency that is still double-defined because a SIBLING
  has not landed is to be handled by doing the work in dependency order within the Set, not by refusing.
  Where this plan's dependency count falls materially once a sibling lands, run in that order (route (B)'s
  tactic) and say so in the execution note; where it does not, inject and wrap per (2).
  HOW TO SEQUENCE, since every one of these five children asked the same question: the runner already
  sorts by dependency depth and re-checks dependencies at dispatch, so declared `Item-Dependencies` are
  sufficient to order the work. Do not re-order plans by hand.
  THE ORIGINAL REVIEWER'S MEASUREMENT BELOW IS PRESERVED and E-01 must reproduce it at execution HEAD;
  only its CONCLUSION (that a route decision was owed by the maintainer) is superseded.
  --- original analysis, superseded as to its conclusion ---
  NOT DECIDED, deliberately, because the measurement raises a question
  about whether this function should be shared AT ALL, which is a design call the maintainer owns.
  THE MEASUREMENT, not an opinion. `initialize_run` has the HIGHEST line-level similarity of the five
  large functions (0.9345, only 15 differing lines) and the LOWEST shared CONTENT: 13 of the 23
  `options` keys it freezes are host-specific (7 oc-only, 6 agy-only), and one of them (`launch_profile`)
  reflects a capability agy does not have at all (zero `runner_profiles` references against oc's 17).
  Separately it closes over 8 still-double-defined names, and it evaluates `__file__` to record the
  driver identity that `run_analytics_sources.driver_generation` and `run_viewer` read by BASENAME, so a
  relocated core reports `unknown` for both hosts with no test failing (F-9).
  FOUR ROUTES, with what each costs. (A) SHARE THE WHOLE FUNCTION, passing thirteen `options` keys plus the
  caller's module path plus eight injected symbols: technically possible, and the "shared core" would then
  be a template whose entire output is supplied by its callers, which is not de-duplication in any useful
  sense. (B) SHARE THE PREFIX ONLY, up to and including the gates: the refusal/resolution/gate sequence
  (`refuse_unimplemented_run_flags`, `report_untracked_dirt_at_run_start`, `expand_selectors`,
  `enforce_draft_admission_gate`, `enforce_dependency_preflight`, `enforce_mixed_type_gate`) is genuinely
  identical apart from a `host=` string, is where the ORDERING pins live, and needs no `options` decision
  at all; each host then keeps its own state-and-options writer. This shares the part that is actually
  shared and leaves host-owned the part that is actually host-owned. (C) RE-ORDER after `sy7uwh` executes
  so the `_plan_kind` fallback is gone first: correct as far as it goes, and it removes only one of the
  fifteen differing lines, so it does not change the picture. (D) DO NOT SHARE `initialize_run`: it writes
  each host's launch identity and each host's option set, which is arguably the most legitimately
  host-specific job in either runner.
  RECOMMENDATION: (B), and it is a stronger recommendation than in the sibling children because the seam
  is unusually clean: the prefix is the shared gate sequence, the suffix is the host's own state writer,
  and the boundary falls exactly where the two ordering pins already assert a boundary
  (`run_dir = state_root`). (A) is not recommended. (D) is defensible and should be stated rather than
  reached by attrition. THIS PLAN'S E-01 THROUGH E-05 ARE EXECUTABLE UNDER EVERY ROUTE, including (D), and
  E-02's driver-identity test is worth landing regardless because that contract has NO test today.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: BOTH tables pasted with the commands that produced them and the HEAD. (a) The `options` key partition per host, every key classified, with the shared / oc-only / agy-only counts stated and compared against the 10 / 7 / 6 measured at review. (b) The closure classification of all 34 free names with the still-double-defined count. `__file__` must be listed as NON-RELOCATABLE with the reason, NOT as an injectable dependency. A table that repeats this plan's numbers without re-deriving them at execution HEAD does NOT satisfy this item.
  - Observed evidence: Re-derived at execution HEAD `87682a3b45bc0fca8099ff12b6db305f82d8ef56` with two committed scanners (`options_scan.py`, `closure_scan.py`, both reproduced in the walkthrough's Appendix A).

    **(a) THE `options` PARTITION.** `python3 options_scan.py`, which unpacks the `state` and `options` dict literals from the AST, separates LITERAL keys from CONDITIONAL ones (a `**({...} if cond else {})`) and reads the `**runner_shared.freeze_run_policy_flags(args)` expansion's key set from that function itself:

    ```
    HEAD: 87682a3b45bc0fca8099ff12b6db305f82d8ef56

    --- oc ---
      options literal keys (17): opencode, model, variant, agent, launch_profile, auto, session,
        output_mode, verbosity, stall_timeout, full_auto, validate, no_audit, self_finalize,
        isolate_worktree, max_items_per_session, action
      options CONDITIONAL keys (4): verify_model, verify_variant, verify_agent, verify_launch_profile
      options ** expansion: runner_shared.freeze_run_policy_flags(args)

    --- agy ---
      options literal keys (16): agy_executable, model, effort, timeout, session, new_session,
        dangerously_skip_permissions, no_verify, output_mode, verbosity, stall_timeout, full_auto,
        self_finalize, isolate_worktree, max_items_per_session, action
      options ** expansion: runner_shared.freeze_run_policy_flags(args)

    === state (outer) key partition ===
    SHARED  (17): created_at, driver, manifest, manifest_sha256, options, queue, repo, run_id,
      run_order, runbook, runbook_sha256, schema_version, selectors, session_id,
      session_turn_counts, set_sessions, updated_at
    OC-ONLY (0): (none)
    AGY-ONLY(0): (none)

    freeze_run_policy_flags contributes (12): allow_dirty_base, allow_drafts, allow_mixed,
      allow_unverifiable, follow_generated, full_auto, integration_retry_limit,
      on_integration_blocked, retry_budget, unattended, unverifiable_ok, with_dependencies
    ```

    Three views, because the plan's 23 and a live run's 34 are both correct and count different things (DECISION 10-orziju-D1):

    | View | Shared | OC-only | AGY-only | Union | HOST-SPECIFIC |
    |---|---|---|---|---|---|
    | Source literals, conditional keys EXCLUDED (this plan's Goal table) | 10 | 7 | 6 | 23 | **13** |
    | Source literals, conditional `verify_*` INCLUDED | 10 | 11 | 6 | 27 | 17 |
    | **A LIVE frozen run on each host** (the 12 policy keys included) | 21 | 7 | 6 | 34 | **13** |

    **THE PLAN'S 10 / 7 / 6 = 23 REPRODUCES EXACTLY** under its own view, and the load-bearing number (13 host-specific) is IDENTICAL under the live view. Live-run members, measured by driving `initialize_run` on each host:

    * SHARED (21): `action`, `allow_dirty_base`, `allow_drafts`, `allow_mixed`, `allow_unverifiable`, `follow_generated`, `full_auto`, `integration_retry_limit`, `isolate_worktree`, `max_items_per_session`, `model`, `on_integration_blocked`, `output_mode`, `retry_budget`, `self_finalize`, `session`, `stall_timeout`, `unattended`, `unverifiable_ok`, `verbosity`, `with_dependencies`
    * OC-ONLY (7): `agent`, `auto`, `launch_profile`, `no_audit`, `opencode`, `validate`, `variant`
    * AGY-ONLY (6): `agy_executable`, `dangerously_skip_permissions`, `effort`, `new_session`, `no_verify`, `timeout`

    The shared count rises from 10 to 21 ENTIRELY through the one already-de-duplicated `**` expansion (12 of the 21 keys), so this dict looks more shared than it is precisely because something else was already fixed. Also measured: the OUTER `state` key set is 17/17/0/0, i.e. fully symmetric, so the divergence is confined to `options`.

    **(b) THE CLOSURE.** `python3 closure_scan.py`, full scope tracking (parameters, assignments, walrus, `for`/`with`/`except` targets, comprehension and lambda scopes, nested `def`/`class`, function-local imports, `global`):

    ```
    HEAD: 87682a3b45bc0fca8099ff12b6db305f82d8ef56
    oc  free module-level names : 33
    agy free module-level names : 35
    UNION                       : 37

    reached by oc ONLY  (2): launch_profile_record, resolve_launch_pair
    reached by agy ONLY (4): DEFAULT_MODEL, DEFAULT_TIMEOUT, _plan_kind, resolve_verification_decision

    agy-only                       3  DEFAULT_MODEL, DEFAULT_TIMEOUT, _plan_kind
    agy-only-delegating            1  resolve_verification_decision
    already-one-object             6  Any, Path, announce_run_order, is_plan_review_approved,
                                      run_order_rationale, runner_shared
    equal-constant                 2  DEFAULT_RUNBOOK_TEXT, DEFAULT_STALL_TIMEOUT
    non-relocatable                1  __file__
    oc-only                        2  launch_profile_record, resolve_launch_pair
    resolves-in-runner-shared     12  DriverError, EmptyStatusSelection, SCHEMA_VERSION, action_for,
                                      append_jsonl, atomic_write_json, load_json, new_run_id,
                                      resolve_plan_path, sha256_file, state_root, utc_now
    still-double-defined           7  build_dynamic_manifest, enforce_dependency_preflight,
                                      enforce_requested_action, expand_selectors, parse_plan_file,
                                      set_plan_approved, write_report
    thin-wrapper                   3  discover_plans, git_common_dir, validate_manifest
    TOTAL                         37
    ```

    **STILL-DOUBLE-DEFINED IS 7, NOT THE PLAN'S 8, AND THE REASON IS ATTRIBUTED RATHER THAN GUESSED** (DECISION 10-orziju-D2): `EmptyStatusSelection` was LIFTED into `runner_shared` by sibling `i3d6ml` at commit `d26c1061` ("rununify(i3d6ml): lift the 9 closure-clean shared runner symbols into runner_shared"), between this plan's review and its execution. It now lives at `runner_shared.py:199` and both hosts import it (`oc_runipd.py:287`, `agy_runipd.py:284`). So the fork count IMPROVED by one through the Set working as designed. The count is 37 rather than 34 by classification convention: this scanner counts the module aliases `Any`, `Path` and `runner_shared` as reached names where the plan folded them into other classes; every symbol lands in a class with the same CONSEQUENCE under both conventions.

    **`__file__` IS LISTED AS `non-relocatable`, NOT AS A DEPENDENCY**, and the reason is stated rather than asserted: every other name in the closure is a BINDING a per-host wrapper can supply, which is the sanctioned `818uru` form. `__file__` is not a binding in that sense, because its VALUE is a property of where the code text physically lives. Injecting it (each wrapper passing `Path(__file__)`) is possible and is the ONLY correct route, but it is a different act: the shared core can no longer answer "which file am I" and must be TOLD, permanently, by every caller forever. Listing it as dependency number eight would have made a contract change look like one more parameter.

    Two classification refinements adopted from siblings, both of which would otherwise OVERSTATE the work: the `thin-wrapper` class (`discover_plans`, `git_common_dir`, `validate_manifest`) is a `def` in both modules whose body is a single delegating `runner_shared.X(...)` call, which is the form the maintainer's `818uru` OQ-02 ruling ESTABLISHED; and `resolve_verification_decision` is agy-only but ALREADY DELEGATES to the shared resolver plan `ybkmzp` built, so F-3's instruction not to collapse the launch half into the verification half is load-bearing (the verification half is already shared, and collapsing them would UN-share it).

    Both tables are additionally asserted MECHANICALLY in `tests/test_rununify_initialize_run.py`, so they are re-derived by the suite on every run and cannot go stale unnoticed. NO runner logic was written by this item.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: THREE parts, all pasted. (a) The driver-identity suite green: for BOTH hosts, `state['driver']['path']` basename is that host's runner module, `driver_generation` returns the host generation and not `unknown`, and `run_viewer`'s label is `OpenCode`/`Antigravity`. (b) The characterization suite green against UNMODIFIED code, with the previously uncovered agy branches named. (c) A sabotage of ONE pinned branch showing the suite FAILS and names it (a characterization test that cannot fail pins nothing).
  - Observed evidence: `tests/test_rununify_initialize_run_characterization.py`, 35 tests, every one driving BOTH hosts' real `initialize_run` through `subTest`.

    **(a) + (b) GREEN AGAINST UNMODIFIED CODE:**

    ```
    $ python3 -m pytest tests/test_rununify_initialize_run_characterization.py -o addopts=""
    collected 35 items
    tests/test_rununify_initialize_run_characterization.py .................  [ 48%]
    ..................                                                       [100%]
    ============================== 35 passed in 8.11s ==============================
    ```

    The driver-identity contract is asserted at FOUR consumer levels by `EachHostRecordsItsOwnDriverIdentity`, plus a fifth cross-host assertion: the recorded basename is that host's runner module; the recorded `sha256` is THAT SAME module's digest (so a record cannot name one file and carry another's contents); `run_analytics_sources.driver_generation(state)` returns `oc_runipd`/`agy_runipd` and `generation_host` returns `opencode`/`agy`, neither `unknown`; `run_viewer.load_run_summary(...).driver` renders `OpenCode`/`Antigravity`; and the two hosts record DIFFERENT paths.

    Branches characterized that had NO behavioral coverage before, agy prioritized per the parent's asymmetry constraint (measured 95 oc tests against 21 agy at the time): the four refusal-before-durable-state classes (`ARefusalLeavesNoDurableState`, including the control that a VALID invocation does create exactly one run directory, without which a function refusing everything would pass); the draft admission gate's exclude-not-refuse behavior and its drafts-only refusal (`TheDraftAdmissionGateExcludesRatherThanRefuses`); the mixed-type gate's exactly-one ledger record (`TheMixedTypeGateIsReachedExactlyOnce`, which also catches the ZERO case that was `uyeko5`'s original dead-gate defect); the twelve-key frozen queue shape and both hosts' DIFFERENT routes to a frozen `kind` (oc reads `PlanRecord.kind`, **agy falls back to `_plan_kind(p_path)`** -- the F-4 branch, previously uncovered, now driven on both hosts asserting the same frozen RESULT); each host's own verification polarity (`validate`+`no_audit` versus the negated `no_verify`); the oc-only `launch_profile` in BOTH directions; `full_auto` defaulting to `False` for a Namespace with the attribute DELETED (the behavioral form of the site-2 spelling pin); the once-per-run untracked report counted against a THREE-item queue; the run-id collision refusal; the dependency preflight refusal; and the manifest/runbook digest freeze.

    **(c) SABOTAGE, and it is the plan's F-9 converted from a code-reading claim into a measurement.** `agy_runipd`'s driver record was changed to `Path(runner_shared.__file__)`, which is EXACTLY what a naive relocation of the body into `runner_shared` does:

    ```
    $ python3 -m pytest tests/test_rununify_initialize_run_characterization.py -o addopts=""
    E   AssertionError: PosixPath('.../agent_workflows/runner_shared.py')
                     != PosixPath('.../agent_workflows/agy_runipd.py')
    FAILED ...::EachHostRecordsItsOwnDriverIdentity::test_run_analytics_infers_this_hosts_generation_and_not_unknown
    FAILED ...::EachHostRecordsItsOwnDriverIdentity::test_the_run_viewer_labels_the_run_with_this_hosts_product_name
    FAILED ...::EachHostRecordsItsOwnDriverIdentity::test_the_recorded_driver_path_basename_is_this_hosts_runner_module
    FAILED ...::EachHostRecordsItsOwnDriverIdentity::test_the_recorded_driver_sha256_is_that_same_modules_digest
    ========================= 4 failed, 31 passed in 7.89s =========================
    ```

    **AND WHAT THE REST OF THE SUITE DID ON THAT SAME BROKEN CODE, which is the finding:**

    ```
    $ python3 -m pytest tests/test_run_analytics_sources.py tests/test_run_viewer.py \
          tests/test_run_analytics.py -o addopts=""
    183 passed in 4.25s
    ```

    183 green while every agy run had become host-unattributable. `tests/test_oc_runipd.py` produced a failure set BYTE-IDENTICAL to its pre-sabotage baseline (`diff` of the sorted `FAILED` lines empty, 9 failures both times, all the `AW_EXECUTION_ROLE=worker` lifecycle guard), so nothing anywhere noticed. The reason the consumers did not notice is now understood and recorded: every existing consumer test feeds a HAND-WRITTEN driver fixture (`tests/test_run_analytics_sources.py:49`, `tests/test_run_viewer.py:64`), so the consumers were covered and the PRODUCERS were not. Filed as backlog `9zyanj` (high, bug).

    The sabotage was reverted from a pristine copy taken before it was applied, and `git diff --stat agent_workflows/` is empty; the suite is green again (61 passed across both new files).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the eleven-row pin table (file:line, what it asserts, thin-caller verdict), with a behavioral equivalent stated for the TWO ordering pins that split on `run_dir = state_root` and for `test_dirty_base_gate.py:191`; plus the pasted green baseline of the three pin files with its count, compared against the 183 measured at review. Explicit confirmation that NO test file was edited by this item.
  - Observed evidence: **BASELINE FIRST**, so a later red is attributable, taken before anything in this lane changed:

    ```
    $ python3 -m pytest tests/test_run_flag_surface.py tests/test_dirty_base_gate.py \
          tests/test_runner_backlog_close.py -o addopts=""
    186 passed in 10.95s
    ```

    **186, where this plan measured 183 at review.** The plan states that "a divergence from 183 is information, not noise", so: the three-test growth is ordinary suite growth since 2026-09-15, not drift in what is pinned. Every pin SITE still resolves, which the scanner verifies by line number. The newly-found fourth pin file is green too: `tests/test_lane_clean_base.py` -> `24 passed`.

    **THE PIN INVENTORY IS 14 SITES ACROSS 6 FILES, NOT 11 ACROSS 3** (`python3 pin_scan.py`, which finds all FOUR ways a test reaches this function's text -- `inspect.getsource`, an AST lookup by function name, a `split("def initialize_run")`, and a bare `"def initialize_run"` string literal -- and de-duplicates sites two detectors both see):

    | # | Pin | Kind | Asserts | Thin-caller verdict |
    |---|---|---|---|---|
    | 1 | `tests/test_dirty_base_gate.py:179` | getsource, BOTH hosts | `report_untracked_dirt_at_run_start` present here and ABSENT from `execute_item` | **BREAKS** |
    | 2 | **`tests/test_dirty_base_gate.py:191`** | getsource, BOTH hosts | **ORDERING**: `refuse_unimplemented_run_flags` < the report < `expand_selectors(` | **BREAKS** |
    | 3 | `tests/test_lane_clean_base.py:627` | split-def | the once-per-run seam names `report_untracked_dirt_at_run_start` | **BREAKS** |
    | 4 | `tests/test_run_flag_surface.py:370` | getsource | `enforce_mixed_type_gate` present | **BREAKS** |
    | 5 | `tests/test_run_flag_surface.py:676` | getsource | `resolve_retry_budget` present | **BREAKS** |
    | 6 | **`tests/test_run_flag_surface.py:745`** | getsource | **ORDERING**: splits on `run_dir = state_root`, requires `refuse_unimplemented_run_flags` in the PREFIX | **BREAKS** |
    | 7 | `tests/test_run_flag_surface.py:775` | getsource | `freeze_run_policy_flags` present | **BREAKS** |
    | 8 | `tests/test_run_flag_surface.py:874` | getsource + regex | the exact spelling `getattr(args, "full_auto", False)` | **BREAKS** |
    | 9 | `tests/test_run_flag_surface.py:1319` | getsource + AST call-set | `runner_shared.enforce_draft_admission_gate` is CALLED (AST, not substring, because the comments name it) | **BREAKS** |
    | 10 | **`tests/test_run_flag_surface.py:1340`** | getsource | **ORDERING**: same `run_dir = state_root` split, AND `expand_selectors` must precede the draft gate. Cites SPEC 2.5a by name | **BREAKS** |
    | 11 | `tests/test_run_flag_surface.py:1564` | getsource | EXACTLY ONE call site each for the two gates | **BREAKS** |
    | 12 | `tests/test_runner_backlog_close.py:255` | getsource, BOTH hosts | the literal `"from_backlog"` | **BREAKS** |
    | 13 | `tests/test_oc_runipd_shim.py:41` | text literal | `"def initialize_run"` is **ABSENT** from the shim | **SURVIVES** (negative, gets STRONGER) |
    | 14 | `tests/test_agy_runipd_shim.py:38` | text literal | the same negative assertion | **SURVIVES** |

    **VERDICT: 12 BREAK, 2 SURVIVE. A thin caller satisfies none of the twelve.** Three assert ORDERING (#2, #6, #10), the class whose GUARANTEE must survive a move rather than merely its text.

    **ONE PIN FILE WAS NOT IN `Scope-Paths`: `tests/test_lane_clean_base.py`.** The review fenced the three files it counted; the scanner found this fourth plus the two negative shim pins. Same class of miss sibling `yrqyxb` hit (three undeclared files), so an incomplete fence is now a pattern across three of the four split children rather than an accident. Filed as backlog `akff6y` (low, followup). It cost nothing HERE because E-03 only READS, but a plan that DID perform the split would have been refused at finalize.

    **BEHAVIORAL EQUIVALENTS for the three ordering pins, each ALREADY IMPLEMENTED AND PASSING in `tests/test_rununify_initialize_run_characterization.py`, so this is a demonstrated route rather than a proposal:**

    | Ordering pin | Guarantee | Behavioral equivalent |
    |---|---|---|
    | `test_run_flag_surface.py:745` | a refused invocation costs the operator nothing and leaves NO durable state | `ARefusalLeavesNoDurableState`: four refusal classes (unimplemented flag, out-of-range retry budget, non-repository, invalid dependency graph), each asserting `state_root(repo)` holds no run directory afterwards, PLUS `test_the_control_a_valid_invocation_DOES_create_exactly_one_run_directory` without which a function that refused everything would pass |
    | `test_run_flag_surface.py:1340` | spec 2.5a: after resolution, BEFORE any durable state, so an exclusion has nothing to reconcile | `TheDraftAdmissionGateExcludesRatherThanRefuses`: the draft is withheld while the rest of the queue PROCEEDS; the gate's excluded set is drawn from RESOLVED ids (the after-resolution half); a drafts-only selection freezes no run directory at all |
    | `test_dirty_base_gate.py:191` | the report fires ONCE per run, not once per item, and cannot fail the run | `TheUntrackedDirtReportFiresOncePerRun`: occurrences counted in captured output with a THREE-item queue, so "once" is measured against a varying N rather than fixed at one |

    The non-ordering pins have equivalents too: #11's call-site count becomes exactly one ledger record per run; #12's literal becomes "the LINK reaches the frozen entry, and an absent one freezes `None`"; #8's regex becomes "a Namespace with the attribute DELETED freezes `False`", which is the property the spelling exists to produce. The honest caveat, recorded rather than glossed: a behavioral ordering assertion can be satisfied by a call on an unrelated branch, which a source-offset pin cannot; it is stronger in the way this Set needs, because it survives the relocation. That trade is the maintainer's 2026-09-16 ruling applied.

    **NO TEST FILE WAS EDITED BY THIS ITEM.** Confirmed: `git status --porcelain` shows only the two NEW files this plan adds (`tests/test_rununify_initialize_run.py`, `tests/test_rununify_initialize_run_characterization.py`); the six pin files are untouched, and all six are green (see V-05(e)).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the written analysis, covering parts (a) through (e) E-04 enumerates, and specifically ANSWERING whether a writer with 13 of 23 host-specific keys is worth sharing, plus how `__file__` would be handled and how the oc-only launch-profile pair would be treated given agy has no equivalent. Plus an explicit statement that NO split was performed and that OQ-03 remains the maintainer's, so the omission cannot be read as an oversight.
  - Observed evidence: The full analysis is `.aw/records/walkthroughs/20260917-irclosure-01-ztmh1b-initialize-run-the-line-count-that-hides-the-divergence.walkthrough.md`, section "What the analysis concluded (E-04)". It is a TRACKED record rather than a lane note, deliberately: the lane submission tree is gitignored, which is the correction sibling `yrqyxb` had to make after the fact. Summary of each part:

    **(a) THIRTEEN HOST-SPECIFIC KEYS: hook, or the function's output re-spelled?** Re-spelled. Three routes exist and all three are the same thing: thirteen keyword parameters (the signature then IS oc's option set concatenated with agy's); one `host_options: dict` parameter (honest, and it reduces the shared core's contribution to the ten shared keys plus a `dict.update`); or a host descriptor object (the form sibling `tx6q0h` uses, which works THERE because those symbols differ by a TOKEN, whereas here the descriptor carries 7 oc fields and 6 agy fields with no overlap, i.e. route 2 with a type annotation). **ANSWER TO THE PLAN'S QUESTION: no, a 13-of-34-key writer is not worth sharing as a unit.** But that is NOT "do not share this function", and conflating the two is the trap: the `options` dict is ONE STATEMENT inside a 409-line function, and the function has two halves with a clean seam between them.

    **(b) `__file__`:** by passing the caller's module path in, which is the only correct answer, and it is now PROVEN rather than assumed (V-02(c) shows the assertions failing on the naive relocation). Concretely: each host's wrapper passes `Path(__file__)`; the shared core takes it as a REQUIRED parameter with NO default, because a default is exactly how this regresses silently; `test_the_recorded_driver_path_basename_is_this_hosts_runner_module` fails if a future edit lets the core reach for its own `__file__`, and `test_runner_shared_does_not_write_a_driver_record` catches the narrower error of a shared HELPER acquiring its own driver writer, which the behavioral test would not see while each host still had its own.

    **(c) THE PINS:** 14 sites across 6 files, 12 BREAK and 2 SURVIVE, 3 assert ORDERING, and one file (`tests/test_lane_clean_base.py`) was unfenced. Full table in V-03.

    **(d) THE OC-ONLY LAUNCH-PROFILE PAIR: they should stay HOST-OWNED, and the reason is measured.** `agy_runipd` contains ZERO `runner_profiles` references against oc's 17, and `launch_profile_record`/`resolve_launch_pair` have no agy counterpart at all. Under the maintainer's oc-preferred ruling this is an **A / NOT-A case, not an oc-preferred case**: there is no agy version to prefer oc's over. `tests/test_runner_profiles_e2e.py` (34 tests, green) reads `state["options"]["launch_profile"]["config_digest"]` DIRECTLY, so a shared writer emitting the key for BOTH hosts would fabricate provenance agy cannot supply, and one emitting it for NEITHER would break that suite. **The implication is the sharpest single argument in this analysis: a shared writer must emit a key for ONE host and not the other, which means the shared core contains either a host branch or a caller-supplied dict -- and a host branch inside the shared core is the duplication this Set exists to remove wearing a different shape, which is exactly the mechanical test this plan's own OQ-01 states.** Both directions are now asserted (`test_only_oc_freezes_a_launch_profile_because_only_oc_has_one`), so the asymmetry is a guarded decision rather than a fact someone might tidy away.

    **(e) ROUTE RECOMMENDATION: route (B) as a TACTIC for reaching route (A)'s objective.** Share the PREFIX, leave the state-and-options writer host-owned, and let the seam fall exactly where the ordering pins already say it is. The seam is cleaner here than in any sibling: the prefix (repository validation, manifest/runbook resolution, the five shared flag refusals, the untracked report, `expand_selectors`, the draft gate, the dependency preflight, the `--action` preflight, the mixed-type gate) is identical apart from a `host='oc'`/`host='agy'` argument, needs NO `options` decision, and is where all three ordering pins live; **the boundary falls at `run_dir = state_root(repo) / run_id`, which is LITERALLY the string two of those pins split the source on**, so the tests already agree this is the meaningful line; and the suffix is where the thirteen keys and `__file__` live. Sequencing: (1) let `tx6q0h` land, which lifts `write_report` and `enforce_requested_action`, **two of this function's seven forks**, taking the count to five with this function not moving; (2) lift the closure-clean remainder individually, each with its own behavioral pin, noting `parse_plan_file` is sibling `sy7uwh`'s and that `i3d6ml`'s review recorded `expand_selectors` as blocked on it; (3) extract the prefix, converting the three ordering pins to the equivalents already implemented and keeping them as parallel assertions until the move is proven; (4) decide EXPLICITLY whether the state writer stays host-owned, so "100% de-duplication" for this function has a stated reachable definition rather than being reached by attrition. After step 1 the fork count is five; after step 2, one or two.

    **NO SPLIT WAS PERFORMED, and OQ-03's status is stated precisely rather than left ambiguous.** OQ-03 is `resolved` ON DISK: the maintainer answered it on 2026-09-16 with a Set-wide directive (100% de-duplication, route (A) as the objective, route (B)'s ordering permitted as a tactic). So this plan did NOT withhold the split pending a decision that was already made; it withheld it because the measurement says this position is the wrong place to jump to the destination in one act, and because THIS plan as re-scoped at its own review is a measure-and-guard plan whose five E-items are measurements, pins, an analysis and a guard. What remains for the maintainer is a SEQUENCING judgment, and this analysis makes a recommendation on it rather than asking. The omission cannot be read as an oversight because it is asserted MECHANICALLY: `tests/test_rununify_initialize_run.py::TheSplitHasNotBeenPerformed` (4 tests) asserts both hosts still define the function, `runner_shared` does not, the two definitions are not the same object, and neither host delegates.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: FIVE parts, all pasted. (a) `python3 -m pytest tests/test_rununify_initialize_run.py -o addopts=""` green, including the inverse eight-still-double-defined assertion and the `__file__`-in-the-runner assertion. (b) The BIDIRECTIONAL non-vacuity controls from Required tests item 6, both directions shown failing and then restored, the second one demonstrating the suite WOULD catch F-9. (c) The F-2 resume proof from both hosts. (d) `tests/test_runner_profiles_e2e.py` green. (e) Bare `python3 -m pytest` with no new failure against the baseline taken at execution HEAD, summary pasted, plus both hosts' suites and the three pin files green by name.
  - Observed evidence: **(a) THE GUARD SUITE:**

    ```
    $ python3 -m pytest tests/test_rununify_initialize_run.py -o addopts=""
    collected 26 items
    tests/test_rununify_initialize_run.py ..........................         [100%]
    ============================== 26 passed in 2.13s ==============================
    ```

    Four classes: `TheOptionsPartitionIsPinned` (8, the live partition per host in BOTH directions, including that the four conditional `verify_*` keys are ABSENT from an ordinary run and that the shared keys arrive predominantly through the one already-shared expansion); `TheClosureClassificationIsPinned` (11, every class asserted with the consequence it carries, the oc-only asymmetry re-derived from a live `runner_profiles` reference count of 0 vs 17 so the class cannot go stale by premise, and a disjointness check so the table cannot contradict itself); `TheDriverIdentityIsEvaluatedInEachRunner` (3, the `__file__`-in-each-RUNNER assertion, the inverse that `runner_shared` builds no driver record, and a premise check that the two consumers still read the basename so the class cannot go vacuous by the CONSUMERS changing); `TheSplitHasNotBeenPerformed` (4, the inverse assertions).

    **THE INVERSE ASSERTION IS OVER SEVEN, NOT EIGHT, AND THE DIFFERENCE IS ATTRIBUTED:** `EmptyStatusSelection` was lifted by sibling `i3d6ml` at `d26c1061` (see V-01(b)), so asserting eight would have been asserting a state the code is no longer in, which is a failing test rather than a guard. `test_the_census_totals_are_what_was_measured` pins both 7 and 37 so the change cannot recur unnoticed.

    **(b) BIDIRECTIONAL NON-VACUITY, both directions shown failing and then restored.**

    CONTROL (a), the `options` direction: `launch_profile` moved from `OC_ONLY_OPTION_KEYS` into `SHARED_OPTION_KEYS`.

    ```
    CONTROL (a) APPLIED: `launch_profile` moved from OC_ONLY_OPTION_KEYS into SHARED_OPTION_KEYS
    E       AssertionError: Items in the second set but not the first:
    E       'launch_profile'
    FAILED ...::TheOptionsPartitionIsPinned::test_every_shared_key_is_frozen_by_BOTH_hosts
    FAILED ...::TheOptionsPartitionIsPinned::test_the_counts_are_what_was_measured
    ========================= 2 failed, 24 passed in 2.21s =========================
    ```

    Restored: `26 passed in 2.08s`.

    CONTROL (b), the driver-identity direction, run exactly as the plan specifies and it produced a MORE informative result than the plan anticipated. The assertion was weakened to accept `runner_shared.py`, which is precisely the edit an agent performing the relocation would make to "fix" a red test. On UNMODIFIED code the weakened suite passes (`35 passed`), which is the point: a weakened guard is SILENT. Then the F-9 sabotage was RE-APPLIED with the weakening still in place:

    ```
    F-9 SABOTAGE RE-APPLIED, with the WEAKENED guard in place
    FAILED ...::EachHostRecordsItsOwnDriverIdentity::test_run_analytics_infers_this_hosts_generation_and_not_unknown
    FAILED ...::EachHostRecordsItsOwnDriverIdentity::test_the_recorded_driver_sha256_is_that_same_modules_digest
    FAILED ...::EachHostRecordsItsOwnDriverIdentity::test_the_run_viewer_labels_the_run_with_this_hosts_product_name
    ========================= 3 failed, 32 passed in 8.02s =========================
    ```

    versus `4 failed, 31 passed` with the guard intact. **Weakening one assertion silenced exactly that one and the other three still caught the hazard**, so the four consumer levels are defence in depth rather than four spellings of one check. That was not the expected outcome and it is the better one: no single edit to this class can make the F-9 hazard invisible. Both the weakening and the sabotage were reverted from pristine copies; `git diff --stat agent_workflows/` empty; `61 passed` across both new files afterwards.

    **(c) THE F-2 RESUME PROOF, BOTH HOSTS:**

    ```
    --- oc_runipd
        frozen queue-entry keys (12): action, attempts, configured_file, dependencies, from_backlog,
          id6, initial_status, kind, order, position, setid, status
        requeued by --retry-incomplete : ['orc001']
        statuses after reconcile+requeue: ['queued', 'partial', 'queued']
        action re-derivation agrees     : True  {'orc001': 'orchestrate', 'aaa111': 'execute', 'bbb222': 'execute'}
        policy flags changed on resume  : False
        driver basename SURVIVES resume : oc_runipd.py
        queue shape SURVIVES resume     : True
        => OK
    --- agy_runipd
        frozen queue-entry keys (12): action, attempts, configured_file, dependencies, from_backlog,
          id6, initial_status, kind, order, position, setid, status
        requeued by --retry-incomplete : ['orc001']
        statuses after reconcile+requeue: ['queued', 'partial', 'queued']
        action re-derivation agrees     : True  {'orc001': 'orchestrate', 'aaa111': 'execute', 'bbb222': 'execute'}
        policy flags changed on resume  : False
        driver basename SURVIVES resume : agy_runipd.py
        queue shape SURVIVES resume     : True
        => OK

    RESULT: both hosts resume their own frozen state
    ```

    As F-2 predicted after re-measurement, this is CONFIRMATION rather than discovery: both hosts freeze the identical twelve keys. **The limit is stated rather than glossed** (DECISION 10-orziju-D4): `main(["resume", ...])` acquires the driver lock and enters the dispatch loop, so it HANGS (measured: no return within 120s), and driving it with a stubbed dispatch would stub away the only part `main` adds. So the proof drives the resume path's own state CONSUMERS on state frozen by each host's real `initialize_run`: `load_state` -> `reconcile_interrupted` -> `requeue_interrupted` -> `apply_run_policy_flags_on_resume` -> `save_state`, then re-derives each action with `action_for` exactly as dispatch does. No lock acquisition and no real dispatch are exercised. The proof gained one assertion the plan did not ask for and that is worth more than the rest: a resume REWRITES state, so a driver record produced by a shared module would be PERSISTED wrong by the resume too; that is now checked on both hosts. Two false positives were found and corrected while writing it, both recorded in the script because either would look like a real regression to the next reader: `requeue_interrupted` REORDERS the queue (so comparing entry [0] compares two different items), and it ADDS a transient `recovery_next` key the dispatch loop pops (`oc_runipd.py:8557`/`:8870`), which is resume bookkeeping rather than a frozen-shape change.

    **(d) `tests/test_runner_profiles_e2e.py`, the suite F-11's asymmetry would break first:**

    ```
    $ python3 -m pytest tests/test_runner_profiles_e2e.py -o addopts=""
    tests/test_runner_profiles_e2e.py ..................................     [100%]
    ============================== 34 passed in 3.38s ==============================
    ```

    34, exactly as measured at review.

    **(e) THE BARE SUITE, with the baseline taken at THIS execution HEAD before anything changed.**

    ```
    $ python3 -m pytest                            # PRE-change, HEAD 87682a3b, my two files stashed
    31 failed, 7584 passed, 3 skipped, 2 xfailed in 99.93s (0:01:39)

    $ python3 -m pytest                            # POST-change
    31 failed, 7645 passed, 3 skipped, 2 xfailed in 88.84s (0:01:28)

    $ diff <(pre sorted FAILED lines) <(post sorted FAILED lines)
    IDENTICAL

    $ env -u AW_EXECUTION_ROLE python3 -m pytest   # POST-change, role unset
    7676 passed, 3 skipped, 2 xfailed in 93.96s (0:01:33)
    ```

    **Byte-identical failure sets before and after; +61 passing and NO new failure.** The 31 are an artifact of running inside a runner-managed worker lane: `AW_EXECUTION_ROLE=worker` is set, which makes `ipd_lifecycle` refuse driver-only lifecycle verbs BY DESIGN, and the affected tests call `driver_begin` and friends directly. **With the role unset the suite is COMPLETELY clean** (7676 passed, zero failures), which is a stronger result than sibling `ty3cj6` obtained; it had one load-dependent sigint flake remaining.

    Named suites, all green:

    ```
    $ python3 -m pytest tests/test_run_flag_surface.py tests/test_dirty_base_gate.py \
          tests/test_runner_backlog_close.py tests/test_lane_clean_base.py -o addopts=""
    210 passed in 13.27s          # the three declared pin files + the fourth E-03 found

    $ python3 -m pytest tests/test_run_analytics_sources.py tests/test_run_viewer.py \
          tests/test_run_analytics.py tests/test_oc_runipd_shim.py tests/test_agy_runipd_shim.py -o addopts=""
    192 passed in 5.40s           # the two F-9 consumers + the two negative shim pins

    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_oc_runipd.py \
          tests/test_agy_runipd_cli.py -o addopts=""
    251 passed in 39.62s          # both hosts' own suites
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

OPEN QUESTION GATE. OQ-03 is `Blocking: yes` and OPEN. `aw ipd lint` refuses this plan at every checkpoint
until the maintainer answers it, which is intended: THE SPLIT is not executable on this plan's own
authority. E-01 through E-05 are all authorized unconditionally, because E-04 delivers the ANALYSIS the
decision needs rather than performing the relocation. E-02's driver-identity test is worth landing under
EVERY route, including "do not split", because that contract has no test today.

EXECUTION CONTRACT. Commit ONLY the declared `Scope-Paths`, path-scoped; never `git add -A` and never
push. Paste the ACTUAL runner output for every `V-*`. Run the suite BARE as `python3 -m pytest`; do NOT add
`-n0`, a second `-q`, or `-p no:randomly`. The `Scope-Paths` fence is a DECLARATION so the runner can tell
afterwards whether an out-of-scope file was edited or an in-scope file was not: an out-of-scope edit is
made and then JUSTIFIED at finalize with a `--scope-reason`, and a declared-but-unmodified path needs a
`--scope-ack`. EXPECT TO ACK THE THREE PIN FILES: E-03 READS them and must not edit them, so they will be
declared-but-unmodified by design; the two analytics test files may or may not be touched depending on
where E-02's assertions land.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

REVIEWER'S HIGHEST-VALUE TARGETS, REWRITTEN 2026-09-16 because the original aimed at a hazard the
measurement downgraded: F-9's `__file__` relocation (the sharpest hazard in this Set, because it changes
what every run records about its own host and NO existing test would catch it), F-8's `options` measurement
(13 of 23 keys host-specific behind a 0.9345 similarity score, which is why the line count misleads), and
F-11's launch-profile asymmetry (an A / NOT-A capability gap, not an oc-preferred difference). F-2's queue
hazard was measured and is LOW; do not spend the review budget there.
