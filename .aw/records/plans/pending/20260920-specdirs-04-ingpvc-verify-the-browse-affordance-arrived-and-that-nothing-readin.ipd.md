# IPD: Verify the browse affordance arrived and that nothing reading a spec broke

- Date: 2026-09-20
- Kind: child
- Concern: Orchestrator `wfjsp4` carries FOUR E-items and no child covers any of them, so the ORCHESTRATOR COVERAGE GATE refused `aw oc run` naming it on 2026-09-21. Three of the four are whole-Set verifications no single child can demonstrate: the browse affordance (E-02) is the Set's entire point and is a property of the migrated tree, the all-surfaces spec-reading proof (E-03) spans readers each child only half touches, and the invariant-survives-its-first-write check (E-04) must run AFTER the migration against all three writers. Because `retire_orchestrator` deliberately skips the pre-transition E/V checkpoint, a runner would mark the parent `executed` with the Set's own load-bearing criteria never checked.
- Scope: Perform the `specdirs` Set's whole-Set verification. IN: confirm the children landed in dependency order, prove the browse affordance exists by directory listing, prove every spec-reading surface still works with the count read from `--json`, and prove the location-equals-status invariant survives a write from all three writers. OUT: making any reader recursive (`y4bdoz`), building the placement library (`r9uvwc`), moving any spec (`1bdxcp`), and promoting the invariant to a fail-closed check rule.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: executed:y4bdoz, executed:r9uvwc, executed:1bdxcp
- Status: to-review
- Set: specdirs
- Order: 4
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ingpvc
- From-Backlog: qzhfk2

## Workflow history

- 2026-09-20 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored to own orchestrator `wfjsp4`'s E-02, E-03 and E-04, which the ORCHESTRATOR COVERAGE GATE refused a run over on 2026-09-21. AGENTS.md prescribes adding a child for uncovered parent work rather than deleting the item, so `wfjsp4`'s checklist is left EXACTLY as authored and this child makes those items performable under a pre-transition E/V checkpoint. E-01 (sequence the children) is ALSO covered here, as this plan's E-01, because verifying the order is part of verifying the Set and the parent's version is likewise unperformable by a runner. RE-MEASURED EVERY FIGURE THE PARENT AND ITS REVIEW CITE, and ALL THREE COUNTS ARE STALE, which is the strongest argument for a re-measuring child rather than a parent asserting numbers from 12 days ago. THE TREE NOW HOLDS 36 SPECS, not the 28 the parent authored or the 29 review re-measured. Distribution at HEAD `41f6a45b`: 13 `approved`, 15 `implemented`, 2 `draft`, 2 `deferred`, 2 `superseded`, 1 `to-review`, 1 `implementing`, which is SEVENTEEN live and 19 terminal (review said 13 live / 16 terminal). So E-02 must re-measure rather than assert, and a reviewer should reject any evidence quoting 28, 29, 12 or 13. THE RETIRED-FILTER TRAP REPRODUCES WITH NEW NUMBERS AND WOULD STILL MISLEAD AN EXECUTOR: `specs._spec_files` returns 36, `check_engine._iter_type_files(repo,'specs')` returns NINETEEN by default, and with `include_retired=True` it returns 36 with the sets EQUAL. The parent's CID-8 warns about this at 29-versus-13; it is now 36-versus-19, and an equality asserted against the default is still guaranteed to fail for a reason unrelated to this Set. THE READER DEFECT IS STILL LIVE, PROVEN BEHAVIORALLY rather than by reading code: in a throwaway repo holding one spec in `.aw/records/specs/draft/` and one at the flat root, `aw specs check --json` reported `{'checked': 1, 'violations': 0}` against 2 files on disk, i.e. it declared conformance having never read the spec in the subdir, while `specs._spec_files` saw 1 and `check_engine._iter_type_files` saw 2. That is exactly the parent's Order-01 blocker and it confirms `executed:y4bdoz` is a correctness edge, not a formality. THE `checked`-AT-ZERO OMISSION IS REAL AND IS WHY `--json` IS THE ONLY VALID COUNT SOURCE: confirmed on the live tree that `aw specs check --json` reports `{'checked': 36, 'violations': 0}`, while the parent measured that the `--agent` record omits `checked` ENTIRELY at zero (a falsy `0` failing an `or` in `result_types.py`) and the human branch prints no count at all. LITERAL PATH CITATIONS: 51 DISTINCT `.aw/records/specs/...spec.md` paths are cited across the tree, of which 33 resolve today and 18 do not. I CHECKED THE 18 RATHER THAN REPORTING A SCARY NUMBER: 16 are test fixtures or throwaway-probe artifacts that never existed as records (`...-01-thing.spec.md`, `...aaa111-demo...`, `...v8vdh6-probe-two...` which is my own probe file, and similar), and only TWO are real pre-existing dangling citations, neither caused by this Set: `agent_workflows/agy_run.py:122` cites `.aw/records/specs/20260809-2211-01-aw-project-layout.spec.md` in a docstring EXAMPLE, and executed plan `u06zo2` cites `.aw/records/specs/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md`, which does not exist in the specs tree. Both are OUT OF SCOPE here and are recorded so a migration executor does not mistake them for damage it caused. `wenmg4`'s `- Scope-Paths:` entry (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) RESOLVES today and is the one the parent's CID-5 names, so it is the citation most at risk from the migration.
- 2026-09-20 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Prove the `specdirs` Set delivered a durable browse affordance rather than a snapshot that decays, by checking the tree, every spec reader, and every spec writer AFTER all three implementation children land, from a plan whose evidence a pre-transition E/V checkpoint actually gates.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm the order that makes the migration safe

- [ ] E-01 CONFIRM ALL THREE IMPLEMENTATION CHILDREN LANDED, AND THAT BOTH PRECONDITION CHILDREN FINALIZED BEFORE THE MIGRATION MOVED A FILE. The order is a CORRECTNESS requirement, not a preference, and each violation has a distinct failure mode: migrating before the READER fix removes every spec from `aw specs check` silently (proven live, see below), and migrating before the PLACEMENT fix produces a tree that drifts on its very next `aw specs set` or `aw specs new`.
  COMPARE FINALIZE COMMITS, NOT ORDER DIGITS. The parent's CID-1 says so explicitly ("Verify by comparing the children's finalize commits, not by trusting Order digits"), and it matters more than usual here because the Order digits in this Set do NOT match its dependency shape: the migration was authored as Order 02 (`1bdxcp`) before the placement child existed, so the placement child is Order 03 and this verification child is Order 04. Use `git log`/`git merge-base --is-ancestor` on the three finalize commits.
  CHECK THAT `1bdxcp` ACTUALLY DECLARES THE PLACEMENT EDGE, because if it does not, a runner may legitimately have executed it early. As authored it declares only `Item-Dependencies: executed:y4bdoz`. If it ran without `executed:r9uvwc`, say so plainly and state whether the tree drifted as a result, rather than reporting the Set clean because all three files are terminal.
  - Depends on: none
  - Expected outcome: all three children `executed` on disk, with pasted commit evidence that `y4bdoz` and `r9uvwc` both finalized BEFORE `1bdxcp`; plus an explicit statement of whether `1bdxcp` declared the placement edge, and the consequence if it did not.
  - Execution state: pending

### Task group 2: the affordance, and everything that reads a spec

- [ ] E-02 VERIFY THE BROWSE AFFORDANCE ACTUALLY ARRIVED, which is the entire point of the Set and the one thing no implementation child can demonstrate alone.
  THE ACCEPTANCE TEST IS A HUMAN ONE, STATED MECHANICALLY: `ls .aw/records/specs/` must show status directories, and listing any ONE of them must answer "what specs are in this state" without opening a file or running a tool. Paste the BEFORE and AFTER listings side by side.
  RE-MEASURE THE DISTRIBUTION, DO NOT QUOTE ANY PLAN. Three different figures are recorded across this Set (28 files, 29 files, 36 files) because agents are authoring specs concurrently. MEASURED AT AUTHORING: 36 files, 17 live, 19 terminal, distributed 13 `approved`, 15 `implemented`, 2 `draft`, 2 `deferred`, 2 `superseded`, 1 `to-review`, 1 `implementing`. Expect a DIFFERENT number at execution and report your own, then confirm every spec sits in a directory matching its `- Status:`.
  DO NOT ACCEPT `aw attention` AS THE PROOF. It already surfaces specs today, and its adequacy is precisely the argument this Set rejects. The deliverable is the HIERARCHY, so the evidence must be a directory listing.
  CHECK THE WHOLE TREE, NOT A SAMPLE. The invariant is "every spec's directory agrees with its `- Status:`", so assert it mechanically over all files rather than spot-checking a few.
  - Depends on: E-01
  - Expected outcome: before/after directory listings showing status partitioning; a re-measured distribution reported rather than copied; and a mechanical whole-tree assertion that every spec's directory equals its status, with any exception named.
  - Execution state: pending

- [ ] E-03 VERIFY NOTHING THAT READS A SPEC BROKE, across every surface, because this Set moves every spec in the tree and they are cited constantly.
  READ THE EXAMINED COUNT FROM `--json`, NOT FROM `--agent` AND NOT FROM THE HUMAN BRANCH. This is a trap the parent measured directly and it defeats the Set's own load-bearing criterion. The human branch prints only `aw specs check: all specs conform.` with NO count; the `--agent` record OMITS the `checked` key ENTIRELY at ZERO, because a falsy `0` fails an `or` in `result_types.py`; only `--json` reports it. CONFIRMED ON THE LIVE TREE at authoring: `aw specs check --json` returns `{'checked': 36, 'violations': 0}`. So a clean `--agent` record is NOT evidence of a nonzero count. REPORT the zero-omission as a finding for a separate fix; do NOT fix it here.
  THE READER DEFECT IS WHY THIS MATTERS, AND IT IS PROVEN: in a throwaway repo with one spec in `draft/` and one at the root, `aw specs check --json` reported `{'checked': 1}` against 2 files on disk, declaring conformance over an unread file. If `y4bdoz` did its job this is fixed; this item is what proves it.
  DO NOT USE `_iter_type_files` SET EQUALITY WITHOUT `include_retired=True`, or you will chase a non-defect. MEASURED AT AUTHORING on the live tree: `specs._spec_files` 36, `_iter_type_files` default NINETEEN, `include_retired=True` 36 with the sets EQUAL. The default filters retired records and 19 of 36 specs are terminal, so an equality asserted against the default is guaranteed to fail for a reason having nothing to do with this Set.
  THE SURFACES TO PROVE, each with its own command: `aw specs check --json` (examined count equal to the on-disk `*.spec.md` count and nonzero); `aw check specs` and `aw check all` (per-rule counts unchanged apart from anything the migration legitimately fixes, judged per RULE ID and never as a repo-wide total, because this repository carries hundreds of pre-existing findings from other rules); `aw find specs <id6>` for a spec in EACH status directory; `aw attention` (still lists live specs); and `aw doctor` (agrees with `aw check`, since the two have disagreed before on the retired-path filter).
  CITATIONS MUST STILL RESOLVE, AND THE BASELINE IS ALREADY IMPERFECT. MEASURED AT AUTHORING: 51 distinct literal `.aw/records/specs/...spec.md` paths are cited tree-wide, 33 resolve and 18 do not. SIXTEEN of the 18 are test fixtures or probe artifacts that never existed as records; only TWO are real pre-existing dangling citations, NEITHER caused by this Set (`agent_workflows/agy_run.py:122` cites a nonexistent `20260809-2211-01-aw-project-layout.spec.md` in a docstring example, and executed plan `u06zo2` cites a nonexistent `20260920-llbr2b-01-llbr2b-...spec.md`). So do NOT report "18 broken citations" as migration damage: measure the same set before and after and judge on the DELTA. `wenmg4`'s `- Scope-Paths:` entry resolves today and is the one most at risk, because breaking a declared `Scope-Paths` path would make an unrelated plan's finalize scope gate fail.
  RUN THE SUITE BARE and judge on the failing NODE ID delta. Do NOT copy any baseline from this Set: the parent's `1 failed, 5648 passed` was wrong in both count and named failure, `test_orchestrator_retirement.py` passes, and the real failure measured later was environmental (an untracked `opencode-recovery/` dump belonging to another party). DO NOT delete that directory to make the suite green; it is not yours. Measure your own baseline in the executing worktree; AFTER minus BEFORE must be EMPTY.
  - Depends on: E-02
  - Expected outcome: every spec-reading surface proven working with the count read from `--json` and equal to the on-disk count; the retired-filter cross-check done with `include_retired=True`; the citation-resolution DELTA shown empty with the two pre-existing danglers named as pre-existing; `doctor` agreeing with `check`; per-rule-id check deltas rather than totals; an empty bare-suite node-id delta; and the `checked`-at-zero omission reported as a finding.
  - Execution state: pending

### Task group 3: the half that decides whether the affordance is durable

- [ ] E-04 VERIFY THE INVARIANT SURVIVES ITS FIRST WRITE, ON EVERY WRITER, which is what separates a durable affordance from a snapshot that decays on the next transition.
  THE THREE WRITERS, each proven SEPARATELY because they are separate code paths and the parent measured two of them wrong. (1) `aw specs set <status> <selector>` with NO `--status` flag, routing to `status_set.run_set_command`, whose `dest_path` block branches on `("plans","prompts")` and `backlog` with no `specs` case as authored; PROVEN at authoring to report `draft → to-review`, rewrite the status line, and LEAVE THE FILE in `draft/`. (2) `aw specs set <path> --status <enum>`, routing to the forked `specs.run_set`. (3) `aw specs new`, which wrote to the FLAT ROOT at authoring even with a `draft/` directory present.
  CITE CURRENT LINE NUMBERS, NOT THE PARENT'S. The parent cites `status_set.py:840-864` and `specs.py:945`; at HEAD `41f6a45b` those are `status_set.py:1027-1069` and `specs.py:976`, and the branch set now includes `prompts`. Line numbers move; verify before quoting.
  WRITER 2 MAY BE BLOCKED BY A GATE BEFORE IT REACHES PLACEMENT, AND THAT IS NOT A PASS. At authoring I could not reach `specs.run_set`'s placement code: `--status approved` was refused as an `illegal transition to-review -> approved`, and `--status reviewed` was refused because `no review record names aa1111 as its Subject-Id`. Those refusals are CORRECT behavior. So construct a fixture that legitimately passes them (a legal single-step transition, plus a real `.review.md` carrying `- Subject-Id:` and `- Subject-Type: spec` where attestation is required). A transcript ending in a refusal proves the gate works, NOT that placement works. Do NOT weaken a gate to make the fixture easy.
  THE TEST IS THE SAME FOR EACH: run it in a throwaway repo, then assert the resulting file's DIRECTORY equals its `- Status:`. Paste all three results. A pass on one spelling is not evidence about another; that assumption caused the two dual-spelling bypasses this codebase documents in-code at `status_set.py:517-525` and `:549-556`.
  THEN RE-RUN THE WHOLE-TREE INVARIANT after those writes, so a writer that relocates ONE file correctly but leaves the tree inconsistent is caught. E-02's mechanical location-equals-status check must still hold over every spec.
  - Depends on: E-03
  - Expected outcome: all three writers demonstrated placing a spec in its status directory, each proven separately with a fixture that actually reaches the placement code; current file:line citations; and the whole-tree location-equals-status invariant re-asserted and still holding after those writes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR'S UNCOVERED ITEM GETS A CHILD, NOT A DELETION. AGENTS.md: "do NOT delete it: ADD A CHILD for it." `wfjsp4`'s four E-items are untouched; they are discharged by citing this child's evidence.
- `retire_orchestrator` SKIPS THE PRE-TRANSITION E/V CHECKPOINT BY DESIGN (`ROLLUP_OMITTED_GATES["pre-transition-ev-checkpoint"]`), on the premise that a parent's items are performed by nobody. That premise is what makes parked parent work dangerous.
- AN ORCHESTRATOR WHOSE CHILD TABLE DECLARES AN UNAUTHORED ROW REFUSES RETIREMENT (`unauthored-child-rows`), which is a SECOND reason `wfjsp4` could not complete: its Order 02 row read `UNAUTHORED`. Plan `r9uvwc` fills it.
- THE SPEC TREE MOVES UNDER YOU: 36 files at authoring versus 28 authored and 29 at review. Re-measure; never quote a plan's count.
- `aw specs check`'s COUNT IS ONLY READABLE FROM `--json`. The human branch prints none; `--agent` omits `checked` entirely at ZERO because a falsy `0` fails an `or`. Live tree returns `{'checked': 36, 'violations': 0}`.
- THE RETIRED FILTER MAKES THE TWO READERS DISAGREE LEGITIMATELY: `_spec_files` 36 versus `_iter_type_files` default 19; equal at 36 with `include_retired=True`. 19 of 36 specs are terminal.
- THE NON-RECURSIVE READER DEFECT IS REAL AND PROVEN BEHAVIORALLY: a throwaway repo returned `{'checked': 1}` against 2 on-disk specs, declaring conformance over an unread subdir spec.
- THE CITATION BASELINE IS ALREADY IMPERFECT: 51 distinct literal spec paths cited, 33 resolve, 18 do not, of which 16 are fixtures/probes and 2 are real pre-existing danglers. Judge on the delta, not the absolute.
- `check.scope-drift` CARRIES HUNDREDS OF PRE-EXISTING FINDINGS in this repository from other agents' in-flight plans with stale frozen bases, so a repo-wide `aw check all` total is not a usable baseline. Compare per RULE ID.

## Findings

| Id | Severity | Location (measured at HEAD `41f6a45b`) | Finding | Evidence |
|---|---|---|---|---|
| F-01 | error | `wfjsp4` E-01..E-04 | All four parent items are covered by no child, and orchestrator retirement skips the E/V checkpoint, so a runner reports them complete unperformed. This plan closes E-01..E-04. | ORCHESTRATOR COVERAGE GATE refused `aw oc run` naming `wfjsp4` on 2026-09-21. |
| F-02 | error | `wfjsp4` child table Order 02 | Declared `UNAUTHORED`, an independent retirement refusal. Filled by `r9uvwc`. | Table row text; `unauthored-child-rows`. |
| F-03 | warn | parent + review distributions | STALE THREE TIMES: 28 authored, 29 at review, 36 at authoring of this plan (17 live / 19 terminal). Any evidence quoting the old figures must be rejected. | Counted over `.aw/records/specs/*.spec.md`. |
| F-04 | error | `specs._spec_files` non-recursive glob | Reproduces behaviorally: `{'checked': 1}` against 2 on-disk specs, conformance declared over an unread subdir spec. Confirms `executed:y4bdoz` is a correctness edge. | Throwaway-repo probe. |
| F-05 | warn | `_iter_type_files` default filter | The CID-8 trap reproduces with new numbers: 36 vs 19 default, 36 vs 36 with `include_retired=True`, sets equal. An equality against the default fails for an unrelated reason. | Measured on the live tree. |
| F-06 | info | `aw specs check --json` | The only surface reporting the examined count; returns `{'checked': 36, 'violations': 0}` on the live tree. `--agent` omits `checked` at zero; human branch prints none. | Measured. |
| F-07 | warn | tree-wide spec path citations | 51 distinct cited, 33 resolve, 18 do not: 16 fixtures/probes, and 2 REAL pre-existing danglers not caused by this Set (`agy_run.py:122` -> `20260809-2211-01-aw-project-layout.spec.md`; plan `u06zo2` -> `20260920-llbr2b-01-llbr2b-...spec.md`). Report the DELTA, not the absolute. | Enumerated and each checked. |
| F-08 | warn | `1bdxcp` `- Item-Dependencies:` | Declares only `executed:y4bdoz`, NOT `executed:r9uvwc`, so nothing mechanically stops the migration running before placement is fixed. E-01 checks whether that happened. | Read at HEAD. |
| F-09 | warn | `wfjsp4` cited line numbers | `status_set.py:840-864` is now `:1027-1069` (and the branch set now includes `prompts`); `specs.py:945` is now `:976`. Verify before quoting. | Read at HEAD. |

## Proposed changes (ordered, validatable)

1. Confirm all three children landed with both preconditions finalized before the migration, by commit evidence (E-01).
2. Prove the browse affordance by before/after directory listings plus a whole-tree location-equals-status assertion, on a re-measured distribution (E-02).
3. Prove every spec-reading surface still works, with the count from `--json`, the retired filter handled, and citation resolution judged on delta (E-03).
4. Prove all three writers place a spec by status, then re-assert the whole-tree invariant (E-04).

This plan ships no product code. Its deliverable is a verification record, which is the correct shape for work the parent could not perform.

## Deferred / out of scope (with reason)

- MAKING ANY READER RECURSIVE. That is `y4bdoz` (Order 01), declared here as a dependency edge.
  - Carrier-Declined: Carrier: `y4bdoz` (Order 01), `approved`, and declared as this plan's `Item-Dependencies` edge. A prerequisite, not deferred work.
- BUILDING THE PLACEMENT LIBRARY OR FIXING ANY WRITER. That is `r9uvwc` (Order 03). This plan PROVES the writers place correctly; it does not make them do so.
  - Carrier-Declined: Carrier: `r9uvwc` (Order 03), `to-review`, which owns the library and all three writers. This plan PROVES they place correctly; it does not build them.
- MOVING ANY SPEC FILE. That is the migration child `1bdxcp`.
  - Carrier-Declined: Carrier: `1bdxcp`, the migration child, `approved`. Another member of this same Set with its own approval and evidence.
- ADDING `executed:r9uvwc` TO `1bdxcp`'s `Item-Dependencies`. That is another plan's file and it is already `approved`; F-08 records the gap and E-01 detects the consequence, but editing a sibling's approved plan is not this plan's business.
  - Carrier-Declined: NOT CARRIED BY A NEW RECORD DELIBERATELY: the gap is recorded as F-08 on this plan AND in the parent `wfjsp4`'s child table as the one integration step to close before the Set runs, and this plan's E-01 DETECTS the consequence if it is not. It is a one-line edit to an approved sibling before execution, not a work item with a lifecycle.
- FIXING THE `checked`-AT-ZERO OMISSION. The parent says to report it as a finding for a separate fix, not to fix it in this Set.
  - Carrier-Declined: Carrier: backlog `uwerb5`, filed 2026-09-20 for exactly this defect (`bug`, `Blocks-Release: next`).
- FIXING THE TWO PRE-EXISTING DANGLING SPEC CITATIONS (`agy_run.py:122`, plan `u06zo2`). Neither is caused by this Set; they are recorded so a migration executor does not mistake them for its own damage.
  - Carrier-Declined: Carrier: backlog `ajomj3`, filed 2026-09-20 naming both citations. Filed rather than declined because these were previously recorded nowhere, and E-03 needs them named so a migration executor does not mistake them for its own damage.
- PROMOTING LOCATION-EQUALS-STATUS TO A FAIL-CLOSED `aw check` RULE. The parent's OQ-03 leaves that severity decision open for the maintainer.
  - Carrier-Declined: The parent orchestrator `wfjsp4` OWNS this as its OQ-03, deliberately left open for the maintainer. Recorded on a live plan, so nothing is lost.
- SHARDING TERMINAL SPECS BY MONTH (parent OQ-02) and THE REVIEWS-LOCATION QUESTION (`sv0sf3`), both deliberately deferred by the parent.
  - Carrier-Declined: Both are OWNED ELSEWHERE and recorded: sharding is the parent `wfjsp4`'s OQ-02 (deliberately open until subdirs exist), and the reviews-location question is backlog `sv0sf3`, whose own text says not to bundle it with a specs migration.
- THE `Readiness:` FIELD. Deliberately ABSENT: it is `/plan-review`'s attested output, and hand-writing it would forge a review that never happened.
  - Carrier-Declined: The ABSENCE is the correct permanent state, not an omission to fix later. `/plan-review` writes that field; hand-writing one forges a review.

## Scope check

- Over-scope: none. This plan reads state and asserts properties; it changes no product code and moves no record.
- Scope-Paths justification: `.aw/records/plans/pending` only, matching the parent's own justification, because this plan's single deliverable is a verification record written into its own file (which `_is_implicitly_allowed` already covers) as it moves through the lifecycle. E-02, E-03 and E-04 READ the specs tree, the readers, and the writers, and reading is not declaring. If a verification DISCOVERS a defect needing a code fix, that is a finding plus a corrective IPD, not an undeclared edit here.
- Under-scope: this plan fixes no reader, no writer and no citation, moves no spec, adds no check rule, and does not edit `1bdxcp`'s dependency field. Each is excluded above with its owner.

## Required tests / validation

- `aw specs check --json` reports a nonzero examined count EQUAL to the on-disk `*.spec.md` count.
- `aw check specs` and `aw check all` compared per RULE ID against a pre-migration baseline, never as a repo-wide total (this repository carries hundreds of pre-existing `check.scope-drift` findings from other agents' in-flight plans).
- `aw find specs <id6>` resolves a spec in EACH status directory.
- `aw attention` still lists live specs; `aw doctor` agrees with `aw check` on the spec set.
- Any `_spec_files` versus `_iter_type_files` equality passes `include_retired=True`.
- The citation-resolution set measured BEFORE and AFTER, with an empty delta and the two pre-existing danglers named.
- All three writers proven in throwaway repos, pasted separately, with writer 2 reaching placement rather than a gate refusal.
- Bare suite `python3 -m pytest`, judged on the failing NODE ID delta against a baseline measured in the executing worktree; AFTER minus BEFORE must be EMPTY. Do not copy any figure from this Set's plans, and do not delete another party's untracked files to make the suite green.

## Spec / documentation sync

- NO SPEC AMENDMENT IS MADE OR NEEDED BY THIS PLAN, and no `.spec.md` path is declared in `Scope-Paths`. The amendment this Set requires (`kw5y2s`'s `specs` record-class row, ruled by the maintainer in the parent's OQ-05) is carried by `r9uvwc`, which declares that path up front so the runners announce it. This plan VERIFIES the outcome and must not edit a contract.
- IF E-02 OR E-03 FINDS THE SHIPPED TREE CONTRADICTS `kw5y2s` AFTER `r9uvwc` RAN, that is a finding to report, not a spec edit to make here: an undeclared spec change is reported by both runners at run end and is exactly the drift the declaration mechanism exists to prevent.

## Open questions

### OQ-01: If E-01 finds the migration ran before the placement fix, does this plan stop or record and continue?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: A CONTINGENT CERTIFICATION-POLICY QUESTION, not an obligation this plan incurs. If the order was violated, E-02 through E-04's evidence is exactly what REVEALS the resulting drift, so nothing disappears unrecorded, and the remedy (a corrective IPD) is already prescribed. What is open is how strictly a partially-correct migration should be allowed to count as delivered, which is a maintainer judgement rather than work anyone owes.
- Resolution or deferral rationale: NON-BLOCKING because the honest action is the same either way at this plan's level: MEASURE and REPORT. F-08 records that `1bdxcp` declares only `executed:y4bdoz`, so nothing mechanically prevents the migration preceding placement, and if that happened the tree may have drifted on any `aw specs set` or `aw specs new` performed in between. RECOMMENDATION: record it as a finding, complete E-02 through E-04 anyway (their evidence is exactly what reveals whether drift occurred), and if drift IS found, file a corrective IPD rather than repairing the tree from a verification plan. The open part is whether the maintainer would prefer this plan to REFUSE to certify the Set in that case, which would make the Set incomplete until a corrective plan runs. Left to them because it is a judgement about how much a partially-correct migration should be allowed to count as delivered.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste all three children's `- Status:` lines and paths, plus the COMMIT evidence (`git log` timestamps or `git merge-base --is-ancestor` results) showing `y4bdoz` and `r9uvwc` both finalized BEFORE `1bdxcp`. Order digits are not evidence. Paste `1bdxcp`'s `- Item-Dependencies:` line as it actually stood at execution and state explicitly whether it declared `executed:r9uvwc`; if it did not, state whether the migration nonetheless ran after placement and what that implies for the tree.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the BEFORE and AFTER `ls .aw/records/specs/` listings side by side, plus a listing of one status directory demonstrating it answers "what is in this state" with no tool. Paste your OWN re-measured file count and distribution and compare against the 36 / 17 live / 19 terminal recorded here, explaining the difference; evidence quoting 28, 29, 12 or 13 is REJECTED as stale. Paste the mechanical whole-tree assertion output showing every spec's directory equals its `- Status:`, over all files rather than a sample, naming any exception. `aw attention` output does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw specs check --json` showing `checked` EQUAL to the on-disk `*.spec.md` count and nonzero (a `--agent` clean record does NOT satisfy this, since it omits `checked` at zero). Paste the `_spec_files` versus `_iter_type_files(include_retired=True)` equality and note the default-filter count separately so the 19-versus-36 gap is not misread as a defect. Paste `aw find specs <id6>` for a spec in EACH status directory, `aw attention` listing live specs, and `aw doctor` agreeing with `aw check`. Paste the per-RULE-ID check comparison (never a repo-wide total). Paste the citation-resolution BEFORE and AFTER sets with an empty delta, naming the two pre-existing danglers as pre-existing. Paste the bare-suite failing node id delta showing it is empty, against a baseline you measured here.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste three SEPARATE writer transcripts, each showing the command, the resulting file's DIRECTORY, and its `- Status:`. For writer 2, paste the fixture construction and show the command REACHED the placement code; a transcript ending in `illegal transition` or `no review record names ...` does NOT satisfy this item. Cite CURRENT file:line for each writer (the parent's `status_set.py:840-864` and `specs.py:945` are stale). Then paste the whole-tree location-equals-status assertion re-run AFTER those writes, showing it still holds.
  - STATE WHO PERFORMED THIS ITEM AND IN WHAT MODE (agent-executed child, or human). This child exists precisely so the answer is never "nobody".
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`. No `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened.

THIS PLAN RUNS LAST IN ITS SET, BY CONSTRUCTION. It declares `Item-Dependencies: executed:y4bdoz, executed:r9uvwc, executed:1bdxcp` because a whole-Set verification cannot precede the Set. Under a runner, `dependency_depth` sorts it last and every edge is re-checked AT DISPATCH, so if any child has not landed this item is marked `dependency-blocked` and the run continues rather than failing. That is correct behavior and not a defect to report.

NOTE THE ORDER DIGITS IN THIS SET DO NOT MATCH ITS DEPENDENCY SHAPE, and that is deliberate rather than an error. The parent's table describes `01` reader, `02` writer, `03` migration, but the migration was authored as Order 02 (`1bdxcp`) before the writer row existed, so the placement child took Order 03 and this verification child takes Order 04. Renumbering an approved sibling is not this plan's business; the ENFORCEMENT lives in the `Item-Dependencies` fields the runner reads at dispatch, which is why this plan names all three explicitly.

WHAT THIS PLAN DOES TO ITS PARENT: NOTHING is deleted from `wfjsp4`. Its E-01 through E-04 stay exactly as authored, because that checklist is what makes `execute specdirs` complete when a human drives the Set with no runner involved. This plan's row is ADDED to the parent's child table so the Set is covered, which lets the coverage gate pass and lets the runner retire the parent honestly once every child is `executed`. The parent's items are then discharged by CITING this child's pasted evidence.

Execution contract: commit ONLY files you changed, path-scoped (`git commit -m msg -- <path>`), never `git add -A`, never `-a`, and never push. THIS IS A SHARED CHECKOUT with other agents and humans working concurrently: verify the staged set with `git diff --cached --name-only` before every commit and `git restore --staged <path>` anything that is not yours, and re-verify after ANY failed hook, because `pre-commit` restores unstaged changes on rejection and can leave paths you never staged in the index. Do NOT delete or stage another party's untracked files (notably any `opencode-recovery/` dump), even to make a suite green. Do not weaken a transition-legality or review-attestation gate to make a writer fixture easier. When every `E-*` is performed and every `V-*` carries pasted evidence, move this plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never by hand.
