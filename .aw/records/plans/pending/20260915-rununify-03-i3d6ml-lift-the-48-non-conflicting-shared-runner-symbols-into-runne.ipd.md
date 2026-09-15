# IPD: Lift the 48 non-conflicting shared runner symbols into runner_shared with oc as the source

- Date: 2026-09-15
- Kind: child
- Concern: 48 symbols exist in BOTH `oc_runipd.py` and `agy_runipd.py` with no behavioral disagreement, so every fix to one is a fix the other silently misses. This is the bulk of the `rununify` duplication and it needs no judgement call.
- Scope: Move these 48 definitions to `runner_shared.py`, taking the `oc_runipd` version as the source per the maintainer's 2026-09-14 ruling, and leave each host importing the shared name. No behavior change, no host parameter needed (the 8 symbols that DO need one are child 04's).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tests/test_rununify_lift.py
- Item-Dependencies: none
- Status: to-review
- Set: rununify
- Order: 3
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: i3d6ml
- From-Backlog: alw22r

## Workflow history
- 2026-09-15 to-review (aw set): Authored 2026-09-15 from a fresh measurement at HEAD; resolves part of the rununify parent's placeholder child rows per the maintainer's 2026-09-14 oc-preferred ruling.

- 2026-09-15 draft (opencode/its_direct-pt3-claude-opus-5): created.
- 2026-09-15 authored (opencode/its_direct-pt3-claude-opus-5): authored against a fresh measurement at HEAD; the parent's E-01 inventory of 2026-09-03 is stale and the corrected numbers are recorded in Findings.

## Goal

Collapse the 48 shared symbols that carry no behavioral disagreement into ONE definition in
`runner_shared.py`, so a fix lands once and reaches both hosts. This is the largest, lowest-risk slice
of the `rununify` Set and it unblocks the parent's placeholder child rows.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the lift

- [ ] E-01 RE-MEASURE the bucket at execution HEAD before moving anything, using the same mechanical method Findings records (AST compare of each shared symbol with docstrings stripped and host tokens normalized). Emit the three buckets (pure-lift, host-parameter, conflict) and CONFIRM the pure-lift set still has 48 members. If a symbol has moved bucket since authoring, say which and adjust rather than proceeding on a stale list.
  - Depends on: none
  - Expected outcome: a pasted bucket listing at execution HEAD; any drift from the 48 named in Findings is stated explicitly with the symbol name and its new bucket.
  - Execution state: pending

- [ ] E-02 Move the 14 symbols that are ALREADY thin delegations (`build_lane_outcome`, `build_verify_and_continue_notice`, `classify_recovery_disposition`, `discover_plans`, `git_common_dir`, `git_head`, `git_status`, `integrate_lane_branch`, `print_status`, `resolve_prior_lane`, `route_recovery_turn`, `run_checked`, `save_state`, `validate_manifest`). For these the shared implementation already exists or agy already calls oc's; this item RELOCATES the one definition into `runner_shared` and deletes the delegating stub, so no `from agent_workflows.oc_runipd import` survives in `agy_runipd` for them.
  - Depends on: E-01
  - Expected outcome: each of the 14 is defined exactly once, in `runner_shared`; both hosts import it; `grep -c "from agent_workflows.oc_runipd import" agent_workflows/agy_runipd.py` drops by the number of these stubs it held.
  - Execution state: pending

- [ ] E-03 Move the 21 symbols whose CODE is byte-identical once docstrings are stripped (`StallWatchdog`, `_budget_breach_recorder`, `_escalation_recorder`, `_findings_block_reason`, `_observe_between_turn_stop`, `_record_checkpoint_stop`, `_record_deliberate_stop`, `build_isolation_notice`, `build_review_prompt`, `disable_lane_prompt`, `driver_finalize`, `evaluate_clean_base_for_launch`, `handle_stop_command`, `install_stop_triggers`, `locked_run`, `make_integration_validation_runner`, `requeue_interrupted`, `run_lock`, `set_plan_approved`, `sync_receipt_into_worktree`, `terminate_process`). Take the oc docstring as the source, but PRESERVE any agy-only explanatory note by folding it in rather than discarding it; several agy docstrings record why a shared object is re-exported and that reasoning is load-bearing for a future reader.
  - Depends on: E-01
  - Expected outcome: 21 single definitions in `runner_shared`; no agy-only docstring content silently lost (state per symbol whether a note was folded in or there was none).
  - Execution state: pending

- [ ] E-04 Move the remaining 13 whose differences are MECHANICAL only, taking the oc form in each case per the ruling: `EmptyStatusSelection` and `StallTimeout` (agy adds a redundant `pass`), `_add_output_mode_flags` (help wording), `_lane_reclaim_prompt` (`print("")` vs `print()`, `.format()` vs f-string), `_record_forced_stop` (a quoted vs unquoted type annotation), `attempt_log_path` and `write_prompt` (filename tag ORDER differs, so pick oc's and say so, since this changes on-disk names), `enforce_dependency_preflight` (agy is a delegating wrapper), `expand_selectors` (`_setid` vs `setid`), `reclaim_lanes_on_interrupt` (`.format()` vs f-string), `reconcile_disposition` and `reconcile_interrupted` (`item['configured_file']` vs `item.get('configured_file','')`), `retry_deferred_integrations` (`item` vs `dict(item)`). For the two `.get` cases and the `dict(item)` case, KEEP THE DEFENSIVE FORM (agy's) rather than oc's, because a missing key there raises inside a recovery path; note this as the one deliberate exception to "oc wins" and say why.
  - Depends on: E-01
  - Expected outcome: 13 single definitions; the filename-order change is called out; the three defensive-form exceptions are recorded with their reason.
  - Execution state: pending

### Task group 2: proof

- [ ] E-05 Add `tests/test_rununify_lift.py` asserting the lift held: each of the 48 names resolves to the SAME OBJECT from both hosts (`oc_runipd.X is agy_runipd.X`), `runner_shared` is the defining module for each (`X.__module__`), and neither runner still holds a second `def`/`class` for any of them (AST scan, repo-wide per the parent's F10, not a pairwise check).
  - Depends on: E-02, E-03, E-04
  - Expected outcome: a test file that FAILS if any of the 48 is re-forked into a runner, and that names which symbol broke.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shared.py` is the established home for host-neutral runner logic (6231 lines at authoring),
  created by this Set's own child `818uru`. It imports no runner, which is why it can hold both hosts'
  shared code without a cycle.
- `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import` asserts the SUBSTRING
  `import oc_runipd` never appears in `agy_runipd`. NOTE FOR THE EXECUTOR: agy currently satisfies
  that guard only on a technicality, using the symbol-level `from agent_workflows.oc_runipd import X`
  spelling because the substring test looks for the module-alias form. `enforce_dependency_preflight`
  documents this in its own body. Completing E-02 removes those imports outright and makes the guard
  meaningful again rather than merely satisfied.
- The oc-to-agy import count is pinned at 57 by
  `tests/test_orchestrator_probe_cache.py::test_the_oc_to_agy_import_count_did_not_increase`. This
  plan should DECREASE it, which will fail that assertion. Re-measure it DOWNWARD and record the new
  count with a note, exactly as its own message instructs; do not delete the assertion.
- The execution contract forbids `git add -A`; commit only the declared `Scope-Paths`, path-scoped.

## Findings

| # | Sev | Where | Finding |
|---|---|---|---|
| F-1 | HIGH | parent `5e4sb6` E-01 note, artifact `tvnq50` | THE INVENTORY IS STALE and its headline number is the reason this Set stalled. It recorded 88 shared symbols, 52 diverged, and 46 undecided pending human reading. Re-measured at HEAD: 66 shared, and the "needs a human decision" set is FOUR, not 46. |
| F-2 | HIGH | measured at HEAD | The 66 shared symbols partition as: 14 already delegating, 21 identical code with prose-only differences, 8 differing only in a host label/title/argv token, 2 genuine behavior conflicts, 3 record-type coupled, 5 large host-shaped functions, and 13 mechanical-only. The 48 in THIS plan carry no disagreement at all. |
| F-3 | MED | `agy_runipd.py` | 14 symbols are already thin wrappers delegating to oc or to `runner_shared`. The duplication for these is nominal, but the delegating stub keeps a runner-to-runner import alive, which is why they are in scope rather than skipped. |
| F-4 | MED | `attempt_log_path`, `write_prompt` | These two differ in the ORDER of the filename tag (`-{id6}-{prefix}{tag}` vs `-{id6}{tag}-{prefix}`), so unifying CHANGES ON-DISK FILENAMES for one host. Not a behavior change in logic but it is observable, so it must be stated rather than absorbed. |
| F-5 | MED | `reconcile_disposition`, `reconcile_interrupted`, `retry_deferred_integrations` | agy uses the DEFENSIVE form (`item.get('configured_file','')`, `dict(item)`) where oc indexes directly. Blind application of "oc wins" would reintroduce a `KeyError` on a recovery path where the key can legitimately be absent. This plan keeps agy's form for exactly these three and says so. |
| F-6 | LOW | `tests/test_orchestrator_probe_cache.py:1187` | The oc-to-agy import count baseline (57) will DROP when E-02 lands, failing that assertion. Expected, and the assertion's own message prescribes re-measuring rather than deleting. |

## Proposed changes (ordered, validatable)

1. Re-measure the buckets at execution HEAD (E-01) and refuse to proceed on a stale list.
2. Relocate the 14 already-delegating definitions and delete the stubs (E-02).
3. Lift the 21 prose-only symbols, folding in any agy-only docstring reasoning (E-03).
4. Lift the 13 mechanical-only symbols, oc form except the three defensive cases (E-04).
5. Add the anti-re-fork suite and re-measure the import-count baseline downward (E-05).

## Deferred / out of scope (with reason)

- The 8 host-parameter symbols (`driver_actor`, `write_report`, `build_prompt`,
  `build_verifier_prompt`, `render_continuation_hint`, `enforce_requested_action`,
  `_detect_driver_command`, `_compute_scope_reconciliation`): child 04. They need a host-label
  parameter designed once, which is a different act from a lift.
- `extract_session_id` and `driver_begin`: child 05. Genuine behavior conflicts needing the maintainer's
  union/adopt rulings.
- `PlanRecord`, `parse_plan_file`, `build_dynamic_manifest`: child 06. Coupled to a test that
  explicitly PINS the two record types as distinct, so unifying them overrides an earlier decision.
- `execute_item`, `run_queue`, `initialize_run`, `build_parser`, `main`: children 07 through 11, one
  each. These are genuinely host-shaped and need a core/hook split, not a winner.

## Scope check

- Over-scope: none. Three source files plus two test files.
- Under-scope: this plan does not reduce either runner's line count by as much as the symbol count
  suggests, because 14 of the 48 are already stubs. The real win is one definition per symbol.

## Required tests / validation

1. `tests/test_rununify_lift.py` (new): object identity across both hosts for all 48, `__module__` is
   `runner_shared`, and an AST scan proving no runner re-forks any of them.
2. The existing guards must stay green, named because they constrain this change:
   `tests/test_runner_shared.py`, `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import`,
   `tests/test_orchestrator_probe_cache.py` (its import-count baseline re-measured DOWNWARD with a note).
3. Both hosts' suites: `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`.
4. Bare `python3 -m pytest`, summary line pasted, at or above the 7308-passed baseline of 2026-09-14.
5. NON-VACUITY: for three lifted symbols chosen across the three groups, sabotage the shared
   definition and show the new suite FAILS, then restore. A lift suite that cannot fail proves nothing.

## Spec / documentation sync

No `.spec.md` change. This is an internal refactor with no operator-visible contract change, with ONE
exception to disclose: F-4's filename-order unification changes a prompt/log filename for one host.
That is not spec-governed (no spec names those filenames), but it must appear in the execution report.

## Open questions

### OQ-01: For the three defensive-form cases, does "oc is preferred" override the safer form?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: NO. The maintainer's ruling was "oc_runipd.py is always the
  preferred version UNLESS there are significant differences (one does A the other NOT A)". A direct
  index versus a defaulted `.get` on a recovery path IS such a difference: one raises where the other
  continues, and the raising form is reachable when `configured_file` is absent from a frozen queue
  entry. Keeping agy's defensive form is the ruling applied, not an exception to it. Recorded per
  symbol in E-04.

### OQ-02: Should the filename-order difference (F-4) be resolved toward oc even though it renames files?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: Yes, oc's order, per the standing ruling. The names are internal
  run-record artifacts, nothing parses them by position (they are globbed by `id6`), and leaving two
  spellings alive is precisely the drift this Set exists to end. It is called out in the execution
  report because it is observable on disk, which is the honest treatment rather than silence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted bucket listing produced at execution HEAD, showing the pure-lift set and its size, plus an explicit statement of any symbol that changed bucket since this plan was authored.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `oc_runipd.X is agy_runipd.X` results for all 14, plus a before/after count of `from agent_workflows.oc_runipd import` occurrences in `agy_runipd.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted identity results for all 21, and a per-symbol statement of whether an agy-only docstring note was folded into the shared docstring or there was none to fold.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted identity results for all 13; the chosen form quoted for `attempt_log_path` and `write_prompt`; and the three defensive-form retentions shown in the shared source with their reason.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: THREE parts, all pasted. (a) `python3 -m pytest tests/test_rununify_lift.py -o addopts=""` green. (b) The NON-VACUITY control: three sabotaged shared definitions each producing a named failure, then restored green. (c) Bare `python3 -m pytest` at or above 7308 passed with zero new failures, plus the re-measured oc-to-agy import count and the note recorded in its assertion.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the declared `Scope-Paths`, path-scoped (`git commit -m msg -- <path>`);
never `git add -A` and never push. Paste the ACTUAL runner output for every `V-*`. Run the suite BARE as
`python3 -m pytest`.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

REVIEWER'S HIGHEST-VALUE TARGETS: F-5's three defensive-form retentions (a blind "oc wins" here
reintroduces a `KeyError` on a recovery path), and V-05(b)'s non-vacuity control, because a lift suite
asserting object identity is exactly the kind of test that can pass vacuously if it resolves names
through the wrong module.
