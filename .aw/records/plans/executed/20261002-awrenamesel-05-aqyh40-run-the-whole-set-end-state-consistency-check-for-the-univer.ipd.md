# IPD: Run the whole-Set end-state consistency check for the universal selector Set

- Date: 2026-10-02
- Kind: child
- Concern: THE ORCHESTRATOR `95jk4s` CARRIED A WHOLE-SET VERIFICATION THAT NO CHILD OWNED. Its `Required tests / validation` section requires "The end-state consistency check, run once after all four" (`aw rename plans <a filename>`, `aw group plans <a filename>`, `aw archive plans <a filename>` all resolve, `aw rename plans <a spec path>` refuses), its V-04 demands that check be pasted, and its completion criterion 7 requires a green `python3 -m pytest` for the Set. Orders 01 to 04 each verify their OWN change; none runs the combined end state. The runner retires an orchestrator once every child is `executed` and SKIPS the pre-transition E/V checkpoint, so as authored that verification would have been reported complete having never run. The orchestrator coverage probe flagged exactly this. This child owns it.
- Scope: Run, read-only, the Set's end-state consistency check and the full suite at a HEAD where Orders 01 to 04 are all executed, and record the pasted evidence here. EXCLUDES any production code, test, spec, or record change: every verb is run in its default PREVIEW mode (no `--apply`), so nothing on disk moves. If any check fails, this plan records the failure and STOPS; the fix belongs to a new corrective IPD against the owning child, never to this file.
- Scope-Paths: .aw/records/plans/pending/20261002-awrenamesel-05-aqyh40-run-the-whole-set-end-state-consistency-check-for-the-univer.ipd.md
- Item-Dependencies: executed:eby93o, executed:87m438, executed:1x4tdo, executed:3qxuw1
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: gyv9tf
- Blocks-Release: next
- Set: awrenamesel
- Order: 5
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: aqyh40

## Workflow history
- 2026-10-07 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: aqyh40 verified (set awrenamesel, attempt 1).
- 2026-10-03 approved (aw set, --by-human): maintainer approved in session after /plan-review (APPROVE WITH REVISIONS APPLIED)
- 2026-10-03 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 (MEDIUM), PR-002 (MEDIUM), PR-003 (LOW), PR-004 (LOW), all FIXED. Every end-state check re-run in preview mode at review behaves as expected. Findings in .aw/records/reviews/20261002-awrenamesel-05-aqyh40-run-the-whole-set-end-state-consistency-check-for-the-univer.review.md.

- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): created to own the whole-Set end-state verification the orchestrator `95jk4s` carried with no child covering it, after the orchestrator coverage probe refused `aw agy run` on it. The parent's checklist is left unchanged; this child is added as Order 05 in its child table.

## Goal

Prove, once, at the Set's combined end state, that the plans tree's mutating verbs accept the reader's selector vocabulary and that a foreign-type path is refused, so the orchestrator's retirement rests on observed evidence rather than on the four children's separate claims.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: preconditions

- [x] E-01 Confirm all four sibling children read `- Status: executed` on disk and record the HEAD under test.
  - Depends on: none
  - Expected outcome: `eby93o`, `87m438`, `1x4tdo`, `3qxuw1` each sit in `.aw/records/plans/executed/` with `- Status: executed`; `git rev-parse --short HEAD` is recorded. If any is not executed, STOP with state `blocked`.
  - Execution state: performed

### Task group 2: end-state consistency check (preview mode only, never `--apply`)

- [x] E-02 Run `aw rename plans <filename>` and `aw group plans <filename> --set <scratch-set>` against one existing plan addressed by its FILENAME, both without `--apply`.
  - Depends on: E-01
  - Expected outcome: both exit 0 and preview an action on that plan; neither prints `no plan has Id`. For the rename, the previewed target filename's `<id6>` segment equals the plan's DECLARED `- Id:` (parent criterion 3), never the selector string. The target plan still exists at its original path afterwards with `git diff --stat -- <that path>` empty.
  - Execution state: performed

- [x] E-03 Run `aw archive plans <filename>` against a terminal-root plan addressed by its FILENAME, and `aw archive plans <a token matching nothing>`, both without `--apply`.
  - Depends on: E-01
  - Expected outcome: the filename resolves to that plan in the preview; the unmatched token exits NONZERO rather than printing a `CLEAN` banner at exit 0; a BARE `aw archive plans` (no target) still exits 0 (parent criterion 4); the target plan still exists at its original path afterwards.
  - Execution state: performed

- [x] E-04 Run `aw rename plans <a repo-relative SPEC path> --slug zzz` without `--apply`.
  - Depends on: E-01
  - Expected outcome: exits nonzero with a refusal naming the type mismatch / out-of-tree path; the spec file is untouched.
  - Execution state: performed

- [x] E-06 Run `aw rename <t> <a repo-relative PLAN path> --slug zzz` without `--apply` for each of the six generic-engine types `specs`, `prompts`, `backlog`, `walkthroughs`, `roadmaps`, `releases` (parent criterion 2).
  - Depends on: E-01
  - Expected outcome: all six exit nonzero with a `<t> verb cannot act on ...` refusal; the plan is still at its original path.
  - Execution state: performed

- [x] E-07 Run `aw archive plans <a terse setid whose plans carry a descriptive parenthetical in - Set:>` without `--apply` (parent criterion 5). Re-derive a qualifying setid at execution (for example by `rg '^- Set: \S+ \(' .aw/records/plans/executed`), do not reuse one from this plan.
  - Depends on: E-01
  - Expected outcome: exits 0 and previews archiving that Set's plans, rather than printing `no terminal-root plan or Set matches`.
  - Execution state: performed

- [x] E-08 For one record under `.aw/records/roadmaps/` (re-derive at execution), compute `check_engine._identity_rename_hint('roadmaps', <id6>, 'Id', False, path=<resolved path>)` and RUN the command it returns without `--apply` (parent criterion 6).
  - Depends on: E-01
  - Expected outcome: the hint names the `roadmaps` type, and running it exits 0.
  - Execution state: performed

### Task group 3: suite

- [x] E-05 Run the full suite bare, `python3 -m pytest`, at the HEAD recorded in E-01.
  - Depends on: E-01
  - Expected outcome: zero failures; the `N passed` summary line is captured verbatim.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `aw rename plans`, `aw group plans` and `aw archive plans` all default to a PREVIEW and write only with `--apply` (their `--help`: "Apply the change (default is a preview)", "Perform the moves (default is preview only)"), which is what lets this child verify without mutating anything.
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` supplies the flags (AGENTS.md).
- An orchestrator holds orchestration, not work of its own; work found on a parent is moved to a CHILD, and the parent's checklist stays (AGENTS.md).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The orchestrator's end-state check was owned by no child. | `95jk4s` `Required tests / validation`: "The end-state consistency check, run once after all four"; its V-04 requires that check pasted; its completion criterion 7 requires a green suite. Orders 01 to 04 each scope their validation to their own module. |
| F-02 | The orchestrator coverage probe refused the run on this parent. | `aw runs`: `[orchestrator-uncovered-work]` for `95jk4s` with remedy "ADD A CHILD for the uncovered work". |
| F-03 | All four siblings are already executed, so this child is immediately dispatchable. | `.aw/records/plans/executed/20260929-awrenamesel-0{1,2,3,4}-*.ipd.md`, each `- Status: executed`. |

## Proposed changes (ordered, validatable)

1. Confirm preconditions (E-01).
2. Run the three plans verbs by filename in preview mode (E-02, E-03).
3. Confirm a foreign-type path is refused by the plans verbs (E-04) and by the six generic-engine types (E-06).
4. Confirm a terse setid with a descriptive parenthetical addresses its Set (E-07) and the roadmap rename hint resolves (E-08).
5. Run the suite (E-05).

No file other than this plan changes.

## Deferred / out of scope (with reason)

- FIXING ANY FAILURE THIS CHECK FINDS. Declined here: a failure is a defect in an already-executed child, and an executed plan's record may not be rewritten, so the remedy is a new corrective IPD against that child (AGENTS.md execution contract).
  - Carrier-Declined: verification-only child; fixes belong to a corrective IPD.

## Scope check

- Over-scope: none. The single Scope-Path is this plan, which is where the evidence is recorded.
- Under-scope: none known; this covers the parent's end-state check, V-04's pasted evidence, and completion criteria 1 to 7 at the combined end state. Criterion 2's research/plans exceptions are covered by the parent's own wording and need no separate check.

## Required tests / validation

The deliverable IS validation: the pasted outputs of every E-item. That nothing was mutated is shown per target (the target file still exists at its original path and `git diff --stat -- <path>` is empty), NOT by a whole-tree `git status`, which is unreliable in this shared checkout because co-workers change it concurrently.

## Spec / documentation sync

N/A: verification only, no behavior change. Spec `z7nbn1` 1.1 is the contract being checked, not amended.

## Open questions

### OQ-01: Should this be folded into the orchestrator instead of a child?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED, A CHILD. The runner retires an orchestrator without running its E/V checkpoint, so verification parked on the parent would never run under a runner (AGENTS.md, orchestrator coverage gate).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the four `- Status: executed` lines with their `executed/` paths, and the HEAD short sha.
  - Observed evidence:
    `git rev-parse --short HEAD`:
    ```
    3a4f8b232
    ```
    Four sibling children status lines in `.aw/records/plans/executed/`:
    ```
    .aw/records/plans/executed/20260929-awrenamesel-01-eby93o-confine-a-path-selector-to-the-requested-type-tree-so-a-muta.ipd.md:
    - Status: executed
    .aw/records/plans/executed/20260929-awrenamesel-02-87m438-route-the-plans-rename-and-group-backends-through-the-shared.ipd.md:
    - Status: executed
    .aw/records/plans/executed/20260929-awrenamesel-03-1x4tdo-give-the-archive-plans-matcher-the-shared-selector-vocabular.ipd.md:
    - Status: executed
    .aw/records/plans/executed/20260929-awrenamesel-04-3qxuw1-derive-the-rename-hint-type-from-where-the-record-lives-so-t.ipd.md:
    - Status: executed
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste both commands, their full output and exit codes (both 0, neither printing `no plan has Id`); show the rename preview's target `<id6>` segment equals the plan's pasted `- Id:` line; paste `git diff --stat -- <target path>` (empty) and `ls <target path>` showing it still exists.
  - Observed evidence:
    Declared plan `- Id:`:
    ```
    $ grep -m 1 "^- Id:" .aw/records/plans/executed/20260808-0004-06-migrate-existing-plans.ipd.md
    - Id: 7qx7ys
    ```
    Rename preview command and output:
    ```
    $ aw rename plans 20260808-0004-06-migrate-existing-plans.ipd.md
    --- would rename 20260808-0004-06-migrate-existing-plans.ipd.md -> 20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd.md ---
    --- would rewrite 1x [full-name] '20260808-0004-06-migrate-existing-plans.ipd.md' -> '20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd.md' in <repo-root>/.aw/records/backlog/graduated/20260920-findtier-01-gyv9tf-rename-plans-filename-selector-refused.backlog.md ---
    --- would rewrite 1x [bare-stem] '20260808-0004-06-migrate-existing-plans.ipd' -> '20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd' in <repo-root>/.aw/records/backlog/graduated/20260920-findtier-01-gyv9tf-rename-plans-filename-selector-refused.backlog.md ---
    --- would rewrite 2x [full-name] '20260808-0004-06-migrate-existing-plans.ipd.md' -> '20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd.md' in <repo-root>/.aw/records/plans/executed/20260908-findtier-02-3i6rso-report-every-record-whose-declared-id-or-set-is-absent-from.ipd.md ---
    --- would rewrite 2x [bare-stem] '20260808-0004-06-migrate-existing-plans.ipd' -> '20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd' in <repo-root>/.aw/records/plans/executed/20260908-findtier-02-3i6rso-report-every-record-whose-declared-id-or-set-is-absent-from.ipd.md ---
    --- would rewrite 11x [full-name] '20260808-0004-06-migrate-existing-plans.ipd.md' -> '20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd.md' in <repo-root>/.aw/records/plans/executed/20260929-awrenamesel-02-87m438-route-the-plans-rename-and-group-backends-through-the-shared.ipd.md ---
    --- would rewrite 7x [bare-stem] '20260808-0004-06-migrate-existing-plans.ipd' -> '20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd' in <repo-root>/.aw/records/plans/executed/20260929-awrenamesel-02-87m438-route-the-plans-rename-and-group-backends-through-the-shared.ipd.md ---
    --- would rewrite 3x [full-name] '20260808-0004-06-migrate-existing-plans.ipd.md' -> '20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd.md' in <repo-root>/.aw/records/plans/executed/20260929-awrenamesel-03-1x4tdo-give-the-archive-plans-matcher-the-shared-selector-vocabular.ipd.md ---
    --- would rewrite 3x [bare-stem] '20260808-0004-06-migrate-existing-plans.ipd' -> '20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd' in <repo-root>/.aw/records/plans/executed/20260929-awrenamesel-03-1x4tdo-give-the-archive-plans-matcher-the-shared-selector-vocabular.ipd.md ---
    --- would rewrite 2x [full-name] '20260808-0004-06-migrate-existing-plans.ipd.md' -> '20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd.md' in <repo-root>/.aw/records/plans/pending/20260929-awrenamesel-00-95jk4s-make-every-mutating-artifact-verb-accept-the-one-universal-s.ipd.md ---
    --- would rewrite 2x [bare-stem] '20260808-0004-06-migrate-existing-plans.ipd' -> '20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd' in <repo-root>/.aw/records/plans/pending/20260929-awrenamesel-00-95jk4s-make-every-mutating-artifact-verb-accept-the-one-universal-s.ipd.md ---
    --- would rewrite 2x [full-name] '20260808-0004-06-migrate-existing-plans.ipd.md' -> '20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd.md' in <repo-root>/.aw/records/reviews/20260929-awrenamesel-02-87m438-route-the-plans-rename-and-group-backends-through-the-shared.review.md ---
    --- would rewrite 1x [bare-stem] '20260808-0004-06-migrate-existing-plans.ipd' -> '20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd' in <repo-root>/.aw/records/reviews/20260929-awrenamesel-02-87m438-route-the-plans-rename-and-group-backends-through-the-shared.review.md ---
    --- would rewrite 2x [full-name] '20260808-0004-06-migrate-existing-plans.ipd.md' -> '20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd.md' in <repo-root>/.aw/records/reviews/20260929-awrenamesel-03-1x4tdo-give-the-archive-plans-matcher-the-shared-selector-vocabular.review.md ---
    --- would rewrite 2x [bare-stem] '20260808-0004-06-migrate-existing-plans.ipd' -> '20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd' in <repo-root>/.aw/records/reviews/20260929-awrenamesel-03-1x4tdo-give-the-archive-plans-matcher-the-shared-selector-vocabular.review.md ---
    --- would rewrite 1x [full-name] '20260808-0004-06-migrate-existing-plans.ipd.md' -> '20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd.md' in <repo-root>/tests/test_plans_rename_selectors.py ---
    --- would rewrite 1x [bare-stem] '20260808-0004-06-migrate-existing-plans.ipd' -> '20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd' in <repo-root>/tests/test_plans_rename_selectors.py ---
    Exit code: 0
    ```
    The previewed target `<id6>` segment is `7qx7ys`, exactly matching declared `- Id: 7qx7ys`.
    Group preview command and output:
    ```
    $ aw group plans 20260808-0004-06-migrate-existing-plans.ipd.md --set scratch
    --- would set Set=scratch Order=06 on 20260808-0004-06-migrate-existing-plans.ipd.md ---
    Exit code: 0
    ```
    Target plan unchanged check:
    ```
    $ git diff --stat -- .aw/records/plans/executed/20260808-0004-06-migrate-existing-plans.ipd.md
    $ ls .aw/records/plans/executed/20260808-0004-06-migrate-existing-plans.ipd.md
    .aw/records/plans/executed/20260808-0004-06-migrate-existing-plans.ipd.md
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the three commands (filename target, unmatched token, bare sweep), their output and exit codes (0, nonzero, 0 respectively), and `ls <target path>` showing the filename target was not moved.
  - Observed evidence:
    1. Filename target:
    ```
    $ aw archive plans 20260808-0004-06-migrate-existing-plans.ipd.md
    --- would archive 20260808-0004-06-migrate-existing-plans.ipd.md -> 202608/ ---
    Exit code: 0
    ```
    2. Unmatched token:
    ```
    $ aw archive plans nonexistent-token-xyz
    ✓ CLEAN  no plan or Set matches 'nonexistent-token-xyz'

    Active filters:
      target: nonexistent-token-xyz

    Next  aw find plans (find plans)
    Exit code: 2
    ```
    3. Bare sweep:
    ```
    $ aw archive plans
    ...
    preview only; re-run with --apply to move
    Exit code: 0
    ```
    4. Target existence check:
    ```
    $ ls .aw/records/plans/executed/20260808-0004-06-migrate-existing-plans.ipd.md
    .aw/records/plans/executed/20260808-0004-06-migrate-existing-plans.ipd.md
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the command, its refusal text and nonzero exit code, and `git diff --stat -- <the spec path>` (empty) showing the spec untouched.
  - Observed evidence:
    ```
    $ aw rename plans .aw/records/specs/deferred/20260725-0957-01-external-delivery-and-skills.spec.md --slug zzz
    error: plans verb cannot act on <repo-root>/.aw/records/specs/deferred/20260725-0957-01-external-delivery-and-skills.spec.md: it is not inside the plans records tree
    Exit code: 2
    ```
    Diff check:
    ```
    $ git diff --stat -- .aw/records/specs/deferred/20260725-0957-01-external-delivery-and-skills.spec.md
    (empty)
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the actual `python3 -m pytest` summary line showing zero failures.
  - Observed evidence:
    ```
    6248 passed, 2 skipped, 3 warnings in 504.49s (0:08:24)
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste, for each of the six types, the command, its exit code (nonzero) and its `<t> verb cannot act on` refusal line; plus `ls <plan path>` showing the plan was not renamed.
  - Observed evidence:
    ```
    === aw rename specs ===
    error: specs verb cannot act on <repo-root>/.aw/records/plans/executed/20260808-0004-06-migrate-existing-plans.ipd.md: it is not inside the specs records tree
    exit: 2
    === aw rename prompts ===
    error: prompts verb cannot act on <repo-root>/.aw/records/plans/executed/20260808-0004-06-migrate-existing-plans.ipd.md: it is not inside the prompts records tree
    exit: 2
    === aw rename backlog ===
    error: backlog verb cannot act on <repo-root>/.aw/records/plans/executed/20260808-0004-06-migrate-existing-plans.ipd.md: it is not inside the backlog records tree
    exit: 2
    === aw rename walkthroughs ===
    error: walkthroughs verb cannot act on <repo-root>/.aw/records/plans/executed/20260808-0004-06-migrate-existing-plans.ipd.md: it is not inside the walkthroughs records tree
    exit: 2
    === aw rename roadmaps ===
    error: roadmaps verb cannot act on <repo-root>/.aw/records/plans/executed/20260808-0004-06-migrate-existing-plans.ipd.md: it is not inside the roadmaps records tree
    exit: 2
    === aw rename releases ===
    error: releases verb cannot act on <repo-root>/.aw/records/plans/executed/20260808-0004-06-migrate-existing-plans.ipd.md: it is not inside the releases records tree
    exit: 2
    ```
    Existence check:
    ```
    $ ls .aw/records/plans/executed/20260808-0004-06-migrate-existing-plans.ipd.md
    .aw/records/plans/executed/20260808-0004-06-migrate-existing-plans.ipd.md
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the `rg` line that selected the setid (showing its parenthetical), the archive command, its exit code (0) and at least one `would archive` line naming a plan of that Set.
  - Observed evidence:
    `rg` selection:
    ```
    $ rg '^- Set: \S+ \(' .aw/records/plans/executed
    .aw/records/plans/executed/20260917-attperf-01-2hj0el-attention-view-and-stranded-lane-drift-performance-optimizat.ipd.md:- Set: attperf (attention-performance)
    ```
    Archive command, output, and exit code:
    ```
    $ aw archive plans attperf
    --- would archive 20260917-attperf-01-2hj0el-attention-view-and-stranded-lane-drift-performance-optimizat.ipd.md -> 202609/ ---
    Exit code: 0
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the python invocation and the hint string it returned (naming `roadmaps`), then the hint command run without `--apply` and its exit code (0).
  - Observed evidence:
    Python hint invocation:
    ```
    $ python3 -c "from pathlib import Path; from agent_workflows import check_engine; p = Path('.aw/records/roadmaps/20260712-7ny1bg-01-7ny1bg-agent-workflows-bounded-iteration-skills-roadmap-for-consideration.roadmap.md').resolve(); print(check_engine._identity_rename_hint('roadmaps', '7ny1bg', 'Id', False, path=p))"
    aw rename roadmaps 7ny1bg --to-id6 --apply
    ```
    Hint command run without `--apply`:
    ```
    $ aw rename roadmaps 7ny1bg --to-id6
    --- would rename .aw/records/roadmaps/20260712-7ny1bg-01-7ny1bg-agent-workflows-bounded-iteration-skills-roadmap-for-consideration.roadmap.md -> 20260712-7ny1bg-01-7ny1bg-agent-workflows-bounded-iteration-skills-roadmap-for-consideration.roadmap.md ---
    --- would record id6 drfea9 in the FILENAME ONLY of 20260712-7ny1bg-01-7ny1bg-agent-workflows-bounded-iteration-skills-roadmap-for-consideration.roadmap.md (no '- Status:'/'- Date:' metadata bullets to add '- Id:' beside; one is NOT added under the heading, because that would put metadata into the document body) ---
    Exit code: 0
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT: open questions are resolved; the scope fence is this plan file only (an out-of-scope edit, should one prove necessary, is made and then justified at finalize via `--scope-reason`); run every verb in preview mode only, never `--apply`; you MUST paste the ACTUAL command output and exit code for every `V-*`, never a paraphrase or an assumed result; commit through `aw commit aqyh40 -- <this plan>`, never `git add -A`, never push. On any check failure, record it as `failed` and stop with the evidence; the fix is a new corrective IPD against the owning child, since executed plans may not be rewritten. POST-GATE LIFECYCLE: the terminal transition requires `aw ipd lint --phase pre-transition` to conform and every `V-*` to read `pass`. In a managed `aw oc run` / `aw agy run` lane the RUNNER owns the finalize transition; when executing by hand, the executor runs `aw ipd finalize` for this plan. Once this child is executed, the runner retires orchestrator `95jk4s`.
