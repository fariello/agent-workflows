# IPD: Unify the twelve small divergent symbols behind HostLabels

- Date: 2026-09-17
- Kind: child
- Concern: TWELVE symbols are defined in both runners with DIFFERING bodies (488 oc lines), and the divergence is three different shapes needing three different treatments, not one. (a) SEVEN are near-identical (length ratio >0.9, no host token in code): `expand_selectors` 90/90, `reclaim_lanes_on_interrupt` 60/60, `reconcile_disposition` 47/45, `_lane_reclaim_prompt` 37/37, `reconcile_interrupted` 37/37, `_add_output_mode_flags` 6/6 - drift, not capability. (b) THREE are agy STUBS that import the real body FROM `oc_runipd` (`classify_recovery_disposition`, `route_recovery_turn`, `build_verify_and_continue_notice`), so they are already one object but reached through an inverted dependency: the antigravity runner depends on the opencode runner. (c) TWO genuinely differ (`retry_deferred_integrations` 70/49, which carries `aw agy` label text, and `_record_forced_stop` 23/16). A single de-duplication tactic applied to all twelve would be wrong for at least two thirds of them.
- Scope: Resolve all twelve to ONE definition in `runner_shared`, per-shape: reconcile the near-identical seven and lift them; RE-POINT the three agy stubs at `runner_shared` so the runner-to-runner import disappears; and for the two genuine differences, express the difference through `HostLabels` (or an added field) rather than a forked body. Also close the guard hole that let the inverted import be introduced.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_review_findings_cascade.py, tests/test_hostdedup_divergent_unify.py, tests/test_rununify_initialize_run.py
- Item-Dependencies: executed:li44r9
- Status: to-review
- Set: hostdedup
- Order: 2
- Highest E allocated: 06
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: nmlx47

## Workflow history
- 2026-09-17 to-review (aw set): Authored 2026-09-17 from an AST measurement at HEAD (34 forked symbols / ~1752 oc lines across the two runners); complete enough to critique

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Collapse the twelve divergent symbols to one definition each, so that after this plan the only remaining
runner fork is the five large functions, and adding a host means writing a `HostLabels` instance rather
than a body.

THE MOST IMPORTANT FINDING IS NOT THE LINE COUNT. Three of the twelve are agy stubs whose real body lives
in `oc_runipd`, which means the ANTIGRAVITY runner currently depends on the OPENCODE runner. That is the
wrong layering for an N-host future: under it, host number three either imports from `oc_runipd` too
(making the opencode runner a de facto shared library that also happens to be a host) or re-forks the
body. The repository already has a guard against exactly this coupling
(`test_review_findings_cascade.py::test_no_runner_to_runner_import`), and the code evades it by SPELLING:
the guard rejects the substring `import oc_runipd`, so the module-alias form is caught while the
symbol-level `from agent_workflows.oc_runipd import <name>` form is not. `agy_runipd.py:1609` documents
the evasion in a comment that concedes "The coupling is identical either way". There are NINE such imports
in that file today, and the guard passes. Closing that hole is in scope, because otherwise this plan's own
result can be undone by the same spelling.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Re-measure and classify

- [ ] E-01 Re-measure the divergent set at execution HEAD and classify each symbol into one of the three shapes: NEAR-IDENTICAL (drift), AGY-STUB (already one object via an inverted import), or GENUINELY DIFFERENT. For each, record the length pair and whether a host token appears in CODE as opposed to prose. Refuse to proceed on a stale list.
  - Depends on: none
  - Expected outcome: a per-symbol classification against the 2026-09-17 baseline (7 near-identical, 3 agy-stub, 2 genuine; 488 oc lines). A symbol that changed shape is named rather than silently re-bucketed.
  - Execution state: pending

### Task group 2: Fix the layering first

- [ ] E-02 Close the guard hole: make `test_no_runner_to_runner_import` reject the symbol-level `from agent_workflows.oc_runipd import ...` spelling as well as the module-alias form, so the ban is on the COUPLING rather than on one way of writing it. Expect this to make the guard RED against current code (9 such imports), which is the correct starting state and must be recorded, not worked around.
  - Depends on: E-01
  - Expected outcome: a guard that fails at HEAD for a named list of 9 imports, with that failure pasted as the baseline E-03 must clear.
  - Execution state: pending

- [ ] E-03 Re-point the three agy stubs (`classify_recovery_disposition`, `route_recovery_turn`, `build_verify_and_continue_notice`) at `runner_shared` by moving the real body there, so both hosts delegate to a host-neutral module and the inverted dependency is gone. Then re-point the remaining runner-to-runner imports the E-02 guard names, or record per import why it must stay.
  - Depends on: E-02
  - Expected outcome: the E-02 guard GREEN, with zero runner-to-runner imports remaining, or an explicit justified exception list.
  - Execution state: pending

### Task group 3: Reconcile the drift and express the real differences

- [ ] E-04 Reconcile the seven near-identical symbols and lift each to one definition. For every symbol, DIFF the two bodies and state per difference whether it is drift (reconcile to the `oc` version per the maintainer's 2026-09-14 oc-preferred ruling) or a real behavior difference that must be preserved. A reconciliation that silently drops one host's behavior is the failure mode to avoid here.
  - Depends on: E-01
  - Expected outcome: seven symbols with one definition each, and a per-symbol statement of what was reconciled away. Where a real behavior difference is found, it is either expressed via `HostLabels` or the symbol is re-bucketed to E-05 and named.
  - Execution state: pending

- [ ] E-05 Unify the two genuinely different symbols (`retry_deferred_integrations`, `_record_forced_stop`) by expressing the difference through the EXISTING `HostLabels` descriptor, adding a field only where an existing one cannot carry it. `retry_deferred_integrations` differs partly by label text (`aw agy`), which `HostLabels.command` already exists to supply. Justify any new field by naming its consumer, per the descriptor's own stated rule that a field without a named consumer is a parameter nobody reads.
  - Depends on: E-04
  - Expected outcome: both symbols with one shared definition; any new `HostLabels` field justified by a named call site.
  - Execution state: pending

### Task group 4: Guard the result

- [ ] E-06 Add `tests/test_hostdedup_divergent_unify.py` pinning that each of the twelve resolves to ONE definition, and re-base `STILL_DOUBLE_DEFINED` / `THIN_WRAPPERS_OVER_RUNNER_SHARED` for every symbol moved (`expand_selectors` and `enforce_dependency_preflight` are in that pin table today). Assert the anti-re-fork property over the whole set rather than pairwise.
  - Depends on: E-03, E-05
  - Expected outcome: a guard that fails if any of the twelve is re-forked or re-coupled, and updated pin tables with a per-entry reason.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `runner_shared.HostLabels` (`runner_shared.py:8530`) is the ESTABLISHED seam for host-varying values: a
  `NamedTuple` with NO DEFAULTS, carrying `command`, `review_command`, `argv_tokens`, `argv_subcommands`,
  `product`, `report_title`, `shell_tool`, and the capability flag `emits_launch_identity`. Its docstring
  states the rule this plan must honor: every field is justified by a named call site, and a mapping with
  `.get()` is the one form it must not be, so a missing field fails loudly at construction.
- The descriptor deliberately EXCLUDES a variant/profile flag, because that is a host CAPABILITY rather
  than a label (agy has zero `runner_profiles` references against oc's 17). E-05 must respect that
  distinction rather than widening the descriptor into a general options bag.
- The maintainer's 2026-09-14 ruling: where two hosts' logic differs by drift, resolve to the `oc_runipd`
  version unless the difference is a real capability. That is E-04's reconciliation rule.
- The maintainer's 2026-09-16 ruling: tests are not immovable; a source-reading guard is re-based
  deliberately as part of the work, never weakened silently. E-02 and E-06 are such re-bases, and E-02 is
  a STRENGTHENING.
- `test_no_runner_to_runner_import` is currently VACUOUS for the symbol-level import form; the evasion is
  documented in a comment at `agy_runipd.py:1609` that concedes the coupling is identical either way.
- The execution contract forbids `git add -A` and pushing; commit only declared `Scope-Paths`.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | 12 symbols are defined in both runners with differing bodies, 488 oc lines | AST scan at HEAD 2026-09-17 |
| F-2 | 7 of the 12 are near-identical (ratio >0.9, no host token in code), i.e. drift not capability | `expand_selectors` 90/90, `reclaim_lanes_on_interrupt` 60/60, `reconcile_disposition` 47/45, `_lane_reclaim_prompt` 37/37, `reconcile_interrupted` 37/37, `_add_output_mode_flags` 6/6 |
| F-3 | 3 are agy STUBS importing the real body from `oc_runipd`, so the antigravity runner depends on the opencode runner | `agy_runipd.py:2444`, `:2454`, `:2466`, each `from agent_workflows.oc_runipd import <name> as _shared` |
| F-4 | The runner-to-runner guard is VACUOUS for that import form | `test_review_findings_cascade.py:312-313` asserts only `assertNotIn("import oc_runipd", agy_src)`; the symbol-level spelling does not contain it. 9 such imports exist and the guard passes |
| F-5 | The evasion is deliberate and self-documented, conceding the coupling is unchanged | `agy_runipd.py:1609-1614`: "the import FORM is deliberate ... The coupling is identical either way" |
| F-6 | Only 2 of the 12 genuinely differ, and one differs partly by LABEL text the descriptor already carries | `retry_deferred_integrations` 70/49 contains `aw agy`; `HostLabels.command` exists to supply exactly that |
| F-7 | 2 of the 12 are pinned as forked by an existing guard and must be re-based in the same change | `STILL_DOUBLE_DEFINED` contains `expand_selectors` and `enforce_dependency_preflight` (`tests/test_rununify_initialize_run.py:159`) |
| F-8 | After this plan the only remaining fork is the five large functions | 34 forks today: 17 (Order 01) + 12 (this plan) + 5 large |

## Proposed changes (ordered, validatable)

1. Re-measure and classify the twelve into the three shapes (E-01).
2. Strengthen the runner-to-runner guard to ban the coupling rather than one spelling (E-02), accepting a
   red baseline of 9 imports.
3. Move the three stub bodies to `runner_shared` and clear the remaining runner-to-runner imports (E-03).
4. Reconcile the seven drifted symbols to one definition, stating per difference what was reconciled (E-04).
5. Express the two genuine differences through `HostLabels` (E-05).
6. Guard the whole set against re-forking and re-base the existing pin tables (E-06).

## Deferred / out of scope (with reason)

- The five large functions are not in this Set; see the orchestrator's OQ-01. They carry five already
  approved plans whose splits were deliberately not performed, so the next step there is a maintainer
  decision about those plans, not a new plan.
- No behavior change beyond what a reconciliation strictly requires. Where E-04 finds a real behavior
  difference, the resolution is to PRESERVE it via the descriptor, not to pick a winner for tidiness.
- Widening `HostLabels` into a general host-options bag is out of scope: the descriptor's own docstring
  rejects that shape, and `orziju` measured why (a 13-of-23 host-specific `options` dict is not worth
  sharing as a unit).

## Scope check

- Over-scope: arguably E-02, which strengthens a guard rather than de-duplicating. Included deliberately:
  without it, E-03's result is reversible by the same spelling that produced the defect, so the fix would
  not hold.
- Under-scope: the five large functions remain forked after this plan, by design.

## Required tests / validation

- `python3 -m pytest` bare and green with the summary line pasted (authoring baseline `7825 passed, 3
  skipped, 2 xfailed`).
- The E-02 guard shown RED at HEAD (with the 9 imports named) and GREEN after E-03.
- Per-symbol evidence that each of the twelve resolves to one definition.
- A real driver execution on BOTH hosts if reachable; at minimum on `oc`, since E-04/E-05 touch recovery,
  stop and integration-retry paths that unit tests exercise only partially.

## Spec / documentation sync

No `.spec.md` is declared in `Scope-Paths`. Spec `25kzda` constrains runner BEHAVIOR, and this plan is
intended to preserve behavior exactly while unifying implementations. If E-04 or E-05 finds that the two
hosts genuinely BEHAVE differently in a way the spec addresses, that is a spec question: stop and record it
as a blocking open question rather than choosing a winner, since resolving a host behavior difference by
fiat would change a shipped contract.

## Open questions

### OQ-01: Is strengthening the runner-to-runner guard (E-02) in scope for a de-duplication plan?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, because without it this plan's result does not hold. E-03 removes
  the inverted imports; the guard as written would permit them straight back, since it bans a SPELLING and
  not the coupling. Leaving that open would make the de-duplication cosmetic. Scoped narrowly: E-02 changes
  the guard's predicate, not the runners.

### OQ-02: What if reconciling a drifted symbol reveals the two hosts genuinely behave differently?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: PRESERVE the difference through the descriptor and say so; do NOT pick
  a winner. The maintainer's 2026-09-14 ruling prefers the `oc` version for DRIFT, which presupposes the
  difference is accidental. A real behavior difference is a capability, and the descriptor already models
  capabilities (`emits_launch_identity` is precisely such a flag). If the difference touches something spec
  `25kzda` governs, E-04 stops and records a blocking question instead, because collapsing a shipped
  behavior difference by fiat would silently change a contract.

### OQ-03: Are the 9 runner-to-runner imports all removable, or will some need an exception?

- Blocking: no
- Status: open
- Owner: Order 02 E-03
- Resolution or deferral rationale: UNKNOWN at authoring, and deliberately not assumed. Three are the
  stubs this plan moves. The other six were not individually analyzed, and at least one
  (`enforce_dependency_preflight`, `agy_runipd.py:1615`) is documented as having had its fate "SETTLED" by
  `rununify` 02 with the answer "KEEP, narrowed", so it may have a reason to remain. E-03 therefore
  permits a justified exception list rather than requiring zero; what it does not permit is an
  unexamined import.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the per-symbol classification pasted, with length pairs and code-vs-prose host-token
    findings, compared against the 2026-09-17 baseline (7 / 3 / 2, 488 oc lines).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the strengthened guard's FAILURE output at HEAD, naming the 9 runner-to-runner
    imports. A guard that is green before E-03 has not been strengthened.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the guard GREEN, plus `grep` evidence of zero remaining
    `from agent_workflows.oc_runipd import` occurrences in `agy_runipd.py`, or the justified exception list
    with a per-import reason.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: for each of the seven, the two-body diff and a written verdict (drift reconciled to
    oc, or real difference preserved via the descriptor). Plus one-definition evidence per symbol. A
    symbol reconciled with no stated verdict fails this item.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: one-definition evidence for both symbols, the `HostLabels` values each host supplies,
    and for any NEW field the named consumer that justifies it. Show `retry_deferred_integrations` producing
    the correct per-host command text (`aw oc run` vs `aw agy run`) rather than a hardcoded one.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `python3 -m pytest tests/test_hostdedup_divergent_unify.py` green AND shown to fail
    against an introduced re-fork; the pin-table diff with a per-entry reason; `python3 -m pytest` bare and
    green with the summary line pasted; plus a real driver execution, since E-04/E-05 touch recovery, stop
    and integration-retry paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. Unlike Order 01 it is NOT a pure move: E-04
and E-05 reconcile real differences, so the executor must state per symbol what was reconciled and must
stop rather than choose a winner where a difference looks like shipped behavior.

Execution contract: work in an isolated worktree, commit only the declared `Scope-Paths`, path-scoped,
never `git add -A`, never push. Paste ACTUAL runner output for every V-item.

Post-gate lifecycle: `aw ipd finalize` moves this plan to `.aw/records/plans/executed/` only after
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries observed evidence.
