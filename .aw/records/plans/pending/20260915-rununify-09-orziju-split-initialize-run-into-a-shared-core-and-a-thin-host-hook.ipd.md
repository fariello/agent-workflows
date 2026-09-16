# IPD: Split initialize_run into a shared core and a thin host hook

- Date: 2026-09-15
- Kind: child
- Concern: `initialize_run` is written twice (409 lines in `oc_runipd.py`, 339 in `agy_runipd.py`) for the same job. Measured at HEAD it carries 15 differing code lines of which only 6 bear a host token, so most of the divergence is DRIFT in shared logic rather than genuine host specificity, and every fix to one copy is a fix the other silently misses. CORRECTED AT REVIEW 2026-09-16: the 15 REPRODUCES exactly and is the most misleading number in this Set, because TWO of the fifteen are the `state` and `queue.append` dict literals, and unpacking them shows the `options` dict carries 23 distinct keys of which SEVEN are oc-only, SIX are agy-only, and only TEN are shared. The host-token count is FOUR, not six. So the divergence inside those two lines is 13 host-specific keys, not drift, and `initialize_run` is the LEAST shared of the five large functions by content even though it looks like the most shared by line count. See F-8 through F-14 and OQ-03.
- Scope: Extract the host-neutral core of `initialize_run` into `runner_shared.py`, leaving each host a thin hook supplying only what is genuinely its own. Logic resolves to the `oc_runipd` version per the maintainer's 2026-09-14 ruling except where a difference is a real capability, which is called out per difference below. RE-SCOPED AT REVIEW: the split is GATED on OQ-03. Beyond the `options` asymmetry, a relocated core evaluating `__file__` would write `runner_shared.py` into `state['driver']['path']`, which TWO consumers use as the host-identity discriminator by basename, so the naive relocation silently makes every run's host unattributable.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_rununify_initialize_run.py, tests/test_run_flag_surface.py, tests/test_dirty_base_gate.py, tests/test_runner_backlog_close.py, tests/test_run_analytics_sources.py, tests/test_run_viewer.py
- Item-Dependencies: executed:sy7uwh
- Status: reviewed
- Readiness: no-go
- Set: rununify
- Order: 9
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: orziju
- From-Backlog: alw22r

## Workflow history
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

- [ ] E-01 MEASURE THE `options` PARTITION AND THE CLOSURE at execution HEAD, and refuse to proceed to E-04 on a stale list. TWO measurements, because the line count is the wrong unit here. (a) Unpack the `state['options']` dict on BOTH hosts and classify every key as shared / oc-only / agy-only; the Goal table records 10 / 7 / 6 at review. (b) Run the closure test: parse `oc_runipd.initialize_run`, collect every free name resolving at MODULE level, and classify into the six classes of the second Goal table. NAME `__file__` SEPARATELY, because it is not a symbol to inject but a construct whose meaning CHANGES on relocation (F-9). This E-item writes NO runner logic.
  - Depends on: none
  - Expected outcome: both tables reproduced at execution HEAD with their members; the host-specific `options` key count stated; the still-double-defined count stated; `__file__` called out as non-relocatable rather than listed as a dependency.
  - Execution state: pending

- [ ] E-02 PIN THE DRIVER-IDENTITY CONTRACT, which has NO test today and which a naive relocation silently breaks (F-9). Write tests asserting that for BOTH hosts, a run initialized by that host records a `state['driver']['path']` whose BASENAME is that host's runner module, and that `run_analytics_sources.driver_generation(state)` returns `oc_runipd` / `agy_runipd` accordingly rather than `unknown`, and that `run_viewer`'s label resolves to `OpenCode` / `Antigravity`. THEN write the characterization tests the parent's constraint requires for every branch the split would move, prioritizing agy branches with no existing coverage. This E-item writes TESTS ONLY and changes no runner logic.
  - Depends on: E-01
  - Expected outcome: a committed suite that passes against UNMODIFIED code, that FAILS if `state['driver']['path']` ever names a module other than the initiating host's runner, and that pins the branches a split would move; the previously uncovered agy branches named.
  - Execution state: pending

### Task group 2: the pin inventory

- [ ] E-03 ENUMERATE THE ELEVEN SOURCE-INSPECTION PINS and state, per pin, whether a thin caller can satisfy it. F-10 lists them; the deliverable is the per-pin verdict, and for the TWO ORDERING pins that split the source on the literal `run_dir = state_root` (`tests/test_run_flag_surface.py:745`, `:1340`) a statement of what behavioral assertion would preserve the same guarantee, which is that a refusal happens before any durable state exists. Do NOT edit a test in this item. Record the baseline first (183 passed across the three files at review) so a later red is attributable.
  - Depends on: E-01
  - Expected outcome: an eleven-row table (file:line, what it asserts, thin-caller verdict, and for the two ordering pins the behavioral equivalent), plus the pasted green baseline.
  - Execution state: pending

### Task group 3: the split, GATED

- [ ] E-04 DO NOT PERFORM THE SPLIT UNTIL OQ-03 IS ANSWERED, and record the analysis rather than silently skipping it. The deliverable is the disclosure, so an executor cannot mistake the omission for an oversight and "finish" it later. State, from E-01 and E-03: (a) how a shared writer would supply THIRTEEN host-specific `options` keys, and whether that is a hook or simply the function's output re-spelled; (b) how `__file__` would be handled, given that passing the caller's module path in is the ONLY correct answer and that it must be proven by E-02's test rather than assumed; (c) the eleven pins and the two ordering ones; (d) whether the oc-only `resolve_launch_pair`/`launch_profile_record` pair should stay host-owned, given agy has ZERO `runner_profiles` references, and what that implies for a shared writer that must emit `launch_profile` for one host and not the other; and (e) a route recommendation with the reason. Change no runner logic in this item.
  - Depends on: E-01, E-03
  - Expected outcome: a written analysis sufficient for the maintainer to answer OQ-03 without re-deriving the measurement, explicitly answering whether a 13-of-23-key host-specific writer is worth sharing at all.
  - Execution state: pending

### Task group 4: proof

- [ ] E-05 Add `tests/test_rununify_initialize_run.py` asserting WHAT THIS PLAN ACTUALLY DID, driven by a named table rather than by the aspiration: the `options` key partition asserted mechanically per host (so a key silently changing class fails), the closure classification asserted, `__file__` asserted to be evaluated in each RUNNER module (not in `runner_shared`), and the eight double-defined symbols asserted STILL double-defined (the inverse assertion, so a later agent cannot "complete" the split piecemeal without the OQ-03 decision). If OQ-03 authorizes the split, extend this file with shared-core object identity and the repo-wide AST anti-re-fork scan (per the parent's F10, not a pairwise check); do NOT write those assertions while the split is ungated, because a test asserting a state the code is not in is a failing test, not a guard.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: a suite that fails if the `options` partition or the closure regresses, if the driver identity moves to a shared module, or if a pinned double definition is unilaterally collapsed; and that does NOT assert an unexecuted split.
  - Execution state: pending

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
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT DECIDED, deliberately, because the measurement raises a question
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

- [ ] V-01 validates E-01
  - Required evidence: BOTH tables pasted with the commands that produced them and the HEAD. (a) The `options` key partition per host, every key classified, with the shared / oc-only / agy-only counts stated and compared against the 10 / 7 / 6 measured at review. (b) The closure classification of all 34 free names with the still-double-defined count. `__file__` must be listed as NON-RELOCATABLE with the reason, NOT as an injectable dependency. A table that repeats this plan's numbers without re-deriving them at execution HEAD does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: THREE parts, all pasted. (a) The driver-identity suite green: for BOTH hosts, `state['driver']['path']` basename is that host's runner module, `driver_generation` returns the host generation and not `unknown`, and `run_viewer`'s label is `OpenCode`/`Antigravity`. (b) The characterization suite green against UNMODIFIED code, with the previously uncovered agy branches named. (c) A sabotage of ONE pinned branch showing the suite FAILS and names it (a characterization test that cannot fail pins nothing).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the eleven-row pin table (file:line, what it asserts, thin-caller verdict), with a behavioral equivalent stated for the TWO ordering pins that split on `run_dir = state_root` and for `test_dirty_base_gate.py:191`; plus the pasted green baseline of the three pin files with its count, compared against the 183 measured at review. Explicit confirmation that NO test file was edited by this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the written analysis, covering parts (a) through (e) E-04 enumerates, and specifically ANSWERING whether a writer with 13 of 23 host-specific keys is worth sharing, plus how `__file__` would be handled and how the oc-only launch-profile pair would be treated given agy has no equivalent. Plus an explicit statement that NO split was performed and that OQ-03 remains the maintainer's, so the omission cannot be read as an oversight.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: FIVE parts, all pasted. (a) `python3 -m pytest tests/test_rununify_initialize_run.py -o addopts=""` green, including the inverse eight-still-double-defined assertion and the `__file__`-in-the-runner assertion. (b) The BIDIRECTIONAL non-vacuity controls from Required tests item 6, both directions shown failing and then restored, the second one demonstrating the suite WOULD catch F-9. (c) The F-2 resume proof from both hosts. (d) `tests/test_runner_profiles_e2e.py` green. (e) Bare `python3 -m pytest` with no new failure against the baseline taken at execution HEAD, summary pasted, plus both hosts' suites and the three pin files green by name.
  - Observed evidence:
  - Result: pending

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
