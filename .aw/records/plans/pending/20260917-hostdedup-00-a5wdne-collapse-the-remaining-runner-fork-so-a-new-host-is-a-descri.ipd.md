# IPD: Collapse the remaining runner fork so a new host is a descriptor not a runner

- Date: 2026-09-17
- Kind: orchestrator
- Concern: `oc_runipd.py` (9588 lines) and `agy_runipd.py` (5784) still define 34 forked symbols totalling roughly 1752 lines, and the maintainer intends to add runners for codex, claude and hermes. At two hosts a duplicated symbol is written twice; at five it is written five times, and every fix must be remembered five times. This is already costing real defects rather than merely offending taste: `cjefq5`, fixed 2026-09-17, was ONE expression present byte-identically in both runners that mislabeled an executed plan `reviewed` and killed six approved plans plus two orchestrators at queue build across 13 separate runs. The `rununify` Set reduced the fork substantially (`runner_shared.py` grew 773 -> 9182 lines) but its last five children (07-11, the five large functions) were re-scoped at review into analysis-only and each records `NO SPLIT WAS PERFORMED`.
- Scope: Finish the job for everything except the five large functions, and PROVE the result by adding a third host that has no runner module. Order 01 lifts the 17 byte-identical symbols; Order 02 unifies the 12 divergent ones behind the existing `HostLabels` descriptor and fixes the inverted agy->oc dependency; Order 03 demonstrates a runner-less host end to end. The five large functions are deliberately NOT re-planned here (see OQ-01).
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: none
- Status: draft
- Set: hostdedup
- Order: 0
- Highest E allocated: 01
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: a5wdne

## Workflow history

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Make "adding a host is writing a descriptor, not a runner" TRUE and DEMONSTRATED, before three more hosts
multiply the cost of it being false.

THE GOOD NEWS FIRST, because it shapes the whole Set: the abstraction already exists.
`runner_shared.HostLabels` (`runner_shared.py:8530`) is a no-defaults `NamedTuple` carrying every
host-varying string a lifted symbol needs (`command`, `review_command`, `argv_tokens`,
`argv_subcommands`, `product`, `report_title`, `shell_tool`) plus one capability flag
(`emits_launch_identity`), with `OC_HOST_LABELS` and an agy twin bound by each host's thin wrappers. 21
symbols already delegate to `runner_shared` on both hosts. So this Set is not designing a new
architecture; it is finishing the migration into one that is already load-bearing, and then testing it in
the direction it has never been tested: a host with no runner of its own.

THE ORDERING IS BY RISK, ASCENDING, which is deliberate. Order 01 is 17 byte-identical symbols where the
shared body is the current body verbatim and no decision exists to get wrong. Order 02 is 12 symbols that
genuinely differ and need per-symbol judgement. Order 03 is the experiment that can only be meaningful
once the first two have removed the noise. Doing them in the reverse order is roughly how `rununify` 07-11
stalled: hardest first, decisions unresolved, nothing landed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Set-level acceptance

- [ ] E-01 After all three children are `executed`, verify and record the Set's combined result: the forked-symbol count has fallen from 34 to the five large functions alone, no runner imports the other runner, a third host runs with no runner module of its own, and the full suite is green. This orchestrator holds no work of its own beyond this verification.
  - Depends on: none
  - Expected outcome: a measured before/after fork count (baseline 34 symbols / ~1752 oc lines at 2026-09-17), plus evidence for each of the four properties. A regression in any one means the Set is not done regardless of the children's individual states.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | `.aw/records/plans/pending/20260917-hostdedup-01-li44r9-lift-the-seventeen-byte-identical-runner-symbols-into-runner.ipd.md` | Lift the 17 byte-identical symbols (380 oc lines) to one definition each; pure move, no behavior change; re-base the guard that pins them as forked | none |
| 02 | `.aw/records/plans/pending/20260917-hostdedup-02-nmlx47-unify-the-twelve-small-divergent-symbols-behind-hostlabels.ipd.md` | Unify the 12 divergent symbols (488 oc lines) per shape: reconcile 7 drifted, re-point 3 agy stubs off `oc_runipd`, express 2 real differences via `HostLabels`; close the vacuous runner-to-runner guard | `executed:li44r9` |
| 03 | `.aw/records/plans/pending/20260917-hostdedup-03-xdvglg-prove-the-descriptor-seam-by-adding-a-third-host-with-no-new.ipd.md` | Implement the maintainer's host-id ruling, then add a third host defined only by a descriptor and drive a real execution through it; classify whatever the seam cannot express | `executed:nmlx47` |

## Completion criteria (the whole Set is done only when)

- The forked-symbol count has fallen from 34 to the five large functions alone (17 lifted by Order 01, 12
  unified by Order 02), measured by the same AST scan that produced the baseline.
- No runner imports the other runner, and the guard that forbids it rejects the COUPLING rather than one
  spelling of it.
- A third host completes a real IPD execution with NO runner module of its own, and its run attributes to
  that host rather than `unknown`.
- Pre-cutover run records still attribute correctly, per the maintainer's host-id ruling.
- The measured host contract is immortalized under `.aw/records/research/`, so the codex/claude/hermes work
  starts from it.
- `python3 -m pytest` bare and green, pasted (authoring baseline `7825 passed, 3 skipped, 2 xfailed`).

## Cross-IPD validation

- ORDER MATTERS AND IS DECLARED, not left to Set/Order (which is only a tiebreaker): Order 02 depends on
  `executed:li44r9` and Order 03 on `executed:nmlx47`. Order 02's reconciliations are easier to review once
  Order 01 has removed the 17 identical symbols from the diff, and Order 03's third-host experiment is only
  meaningful once the seam is the single path.
- ONE PIN TABLE, EDITED TWICE: both Orders 01 and 02 re-base
  `tests/test_rununify_initialize_run.py`'s `STILL_DOUBLE_DEFINED` / `THIN_WRAPPERS_OVER_RUNNER_SHARED`.
  Each must edit only its own symbols and must not delete an assertion to make the suite pass. `Order 01`
  owns `set_plan_approved`; `Order 02` owns `expand_selectors` and `enforce_dependency_preflight`.
- NO CHILD MAY CHANGE BEHAVIOR TO ACHIEVE DE-DUPLICATION. Order 01 is a pure move. Order 02 preserves a
  real host difference through the descriptor rather than picking a winner. If either finds a behavior
  difference that spec `25kzda` governs, it stops and records a blocking question.
- THE THREE CHILDREN MUST NOT INVENT A SECOND HOST SEAM. `HostLabels` is the one descriptor; a child that
  needs a new host-varying value adds a FIELD to it, justified by a named consumer, rather than introducing
  a parallel mechanism.

## Deferred / out of scope (with reason)

- THE FIVE LARGE FUNCTIONS (`execute_item` 436, `main` 133, `run_queue` 150, `initialize_run` 119,
  `build_parser` 46 oc lines; 884 total) are deliberately NOT re-planned in this Set. See OQ-01: they
  already carry five approved plans, so what they need is a decision about those plans, not a sixth plan.
- Integrating any REAL vendor host (codex, claude, hermes) is out of scope. Order 03 proves the seam admits
  a runner-less host; each real host is its own work with its own credentials and spend.
- The 21 existing thin wrappers are left exactly as they are: they are the sanctioned form, not debt.

## Scope check

- Over-scope: none. This orchestrator holds one verification item plus the child table.
- Under-scope: knowingly. After this Set the five large functions remain forked, so the fork is reduced from
  34 symbols to 5 and from ~1752 lines to ~884, not to zero. Claiming otherwise would misrepresent the
  result; closing that last gap needs the OQ-01 decision.

## Required tests / validation

Children own their own validation. This orchestrator's own check is E-01: the Set-level end state, evidenced
by a re-run of the fork-count scan against the 34-symbol baseline, the runner-to-runner import check, the
third host's run record, and a bare green suite. Note the Set is NOT verifiable structurally alone: it moves
lock, stop-trigger, recovery and integration-retry machinery, which unit tests exercise only partially, so a
real driver execution is required.

## Open questions

### OQ-01: What should happen to `rununify` 07-11, the five plans that were approved to split the five large functions but recorded `NO SPLIT WAS PERFORMED`?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN, and deliberately NOT resolved by filing another plan, because the
  authorization already exists and duplicating it would create two competing mandates for the same code.
  THE SITUATION, measured: each of `yrqyxb` (`execute_item`), `ty3cj6` (`run_queue`), `orziju`
  (`initialize_run`), `s16omw` (`build_parser`) and `3dki3o` (`main`) is filed `executed` in
  `.aw/records/plans/executed/`, and each contains the phrase `NO SPLIT WAS PERFORMED`. Each was re-scoped
  at review into measurement-and-analysis behind a blocking OQ-03, and each OQ-03 was then RESOLVED by the
  maintainer on 2026-09-16 as "ROUTE (A) AS THE OBJECTIVE ... So DO THE SPLIT", with the Set-wide directive
  that "at the end of the SET, there should be one code base shared by the two runners that contains 100% of
  the otherwise redundant code". So the splits are authorized but were not performed, and the plans that
  would have performed them are already terminal.
  THREE ROUTES, and the choice is the maintainer's because it is about lifecycle authority, not code: (a)
  file a NEW Set of five corrective plans citing the resolved OQ-03s as their authority, which is the option
  the conventions point to since a plan in `executed/` must not be reopened; (b) treat the five as
  incomplete and reopen them, which contradicts the rule against editing an executed plan; (c) accept the
  five large functions as permanently host-owned, which contradicts the 2026-09-16 directive and should be
  recorded as a superseding decision if chosen. This Set proceeds on the other 29 symbols either way, so
  this question blocks nothing here.

### OQ-02: Does the third host in Order 03 need to be a real AI host?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, a scripted/dry-run host answers the structural question completely
  and needs no vendor CLI, credentials or spend. The repository already does exactly this: `host_launchers`
  states "No live models are launched in tests (doubles only)" and `host_runner` takes an injectable runner.
  Recorded here because the cheaper answer is also the more rigorous one, and a reader might otherwise
  assume the Set was descoped for convenience.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the re-run fork-count scan against the 2026-09-17 baseline (34 symbols / ~1752 oc
    lines), showing only the five large functions remain; `grep` evidence of no runner-to-runner import;
    the third host's run record showing correct attribution; a pre-cutover record still attributing
    correctly; the research record path; and `python3 -m pytest` bare and green with the summary line
    pasted. Plus all three children shown `executed`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This Set requires explicit human approval before execution. One design decision is already recorded from
the maintainer (Order 03's OQ-02: the descriptor carries an explicit host id, and pre-cutover records must
keep attributing), and one question remains open for the maintainer that blocks nothing here (OQ-01 above,
on the fate of `rununify` 07-11).

Execution contract for every child: work in an isolated worktree, commit only declared `Scope-Paths`,
path-scoped, never `git add -A`, never push. Paste ACTUAL runner output for every V-item; a claim of
success without pasted evidence does not satisfy these gates.

Post-gate lifecycle: this orchestrator is retired to `.aw/records/plans/executed/` by the runner once all
three children are `executed` on disk, spending no agent turn. If executed by hand instead, E-01 must be
genuinely performed rather than inferred from the children's states: three executed children can still
leave a regressed fork count if a later change re-forked a symbol.
