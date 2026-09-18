# IPD: Stop the plan-gate execution contract from prescribing a hand-rolled lifecycle move that the finalize gate refuses

- Date: 2026-09-17
- Kind: child
- Concern: functionality
- Scope: Correct the toolkit text that tells every IPD's execution contract to end with a hand-rolled `git mv` + `Status:` edit, which the `aw ipd finalize` gate and the post-transition attribution lint are designed to REFUSE. Measured consequence: a real unattended run (`run-20260917T224036Z-2413656`) completed all of plan `waj7w0`'s work, followed its gate clause literally, was refused by `IPD-M104` and two `IPD-S406` errors, reverted the move, and reported `partial` with the lane unintegrated. Fixes the source template, the four workflows that mandate or verify the contract, and adds a deterministic lint so a plan carrying the wrong wording cannot pass review again.
- Scope-Paths: .aw/system/workflows/templates/plans-README.md, .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/02-review-and-revise.md, .aw/system/workflows/plan-review-long/review-rubric.md, .aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md, agent_workflows/ipd_lint.py, tests/test_ipd_lint.py, tests/test_ipd_authoring.py
- Item-Dependencies: none
- Status: to-review
- Set: gate-contract
- Order: 1
- Highest E allocated: 08
- Author: opencode model=its_direct/pt3-claude-opus-5-1m-us
- Id: dcri4s

## Workflow history

- 2026-09-17 to-review (opencode model=its_direct/pt3-claude-opus-5-1m-us): authored from a measured production failure in the `cmmc-tracker-sheet-01` target repo (installed toolkit 1.1.1.dev3028+g476354fc), then RE-VERIFIED and filed against this repo at 1.2.1 / HEAD e299a9a5, where the defective text lives. Scope-Paths corrected from a guessed `agent_workflows/workflows/...` layout to the real `.aw/system/workflows/...` sources, and the lint target from `ipd_schema.py` to `ipd_lint.py`, where IPD-M104 (:50) and IPD-S406 (:68) are actually defined.
- 2026-09-17 draft (opencode model=its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the plan-level execution contract tell an executing agent to run `aw ipd finalize`, and stop
telling it to hand-build the terminal transition with `git mv`.

### PROVENANCE: MEASURED DOWNSTREAM, FILED HERE

This defect was measured in a TARGET repository (`cmmc-tracker-sheet-01`) running installed
toolkit `1.1.1.dev3028+g476354fc`, because that is where a real unattended run hit it. The plan is
filed and executed HERE, in the toolkit, because this is where the defective text lives and where a
fix propagates from.

Every citation below has been RE-VERIFIED against this repository at version `1.2.1`
(`HEAD` `e299a9a5`), not merely carried over from the downstream observation. The defect is present
here unchanged: `.aw/system/workflows/templates/plans-README.md:77-78` carries the same wording that
produced the failure. Line numbers in this plan refer to THIS tree.

### THE FAILURE, MEASURED

Run `run-20260917T224036Z-2413656` executed approved plan `waj7w0` on host `antigravity`
(`gemini-3.7-flash-high`) in an isolated lane. Facts, from that run's own state:

- The WORK SUCCEEDED. Two commits on `aw/lane/waj7w0` (head `7014e9e`), every `V-*` item filled with
  observed evidence, the agent's outcome JSON recording `"tests_passed": true` and
  `"132 tests passing across 37 suites"`, and `defect_report.state: none-found`.
- `aw ipd lint --phase pre-transition` on the lane's plan reports **conforming**. So the plan was
  genuinely finishable at that moment.
- The agent then performed the terminal transition BY HAND, because that is what the plan told it to
  do (see the clause below): `git mv` of the plan file, an edit to `- Status:`, and a history line.
- The post-transition lint REFUSED the result:

```text
-    executed     plan        20260916-ux-onboarding-01-waj7w0  error
     ! IPD-M104: Approval: Approval must be absent unless Status is approved
     ! IPD-S406: the newest 'executed' history entry must name a non-generic actor/model
                 (the machine-default 'aw set' / an empty actor is rejected); run the
                 transition via `aw ipd finalize --actor <agent/model>`
     ! IPD-S406: the newest 'executed' history entry must carry a nonempty summary
```

- The agent reverted the move, left the plan at `Status: approved`, and reported `SUCCESS`. The
  runner correctly disagreed and recorded `partial`, preserving the lane with
  `preserved_reason: "the item finished 'partial' rather than executed, so its work was never
  integrated"`. Nine and a half minutes and 27.3M tokens produced nothing on `main`.

### THE ROOT CAUSE

The plan's gate carried this clause, and the agent followed it exactly and in order:

```text
13. On completion, run `aw ipd lint --phase pre-transition`, confirm it reports conforming and
    every `V-*` carries observed evidence, then `git mv` this file to
    `.aw/records/plans/executed/`, set `- Status: executed`, and append a
    `## Workflow history` line.
```

That wording is NOT a local invention. It is prescribed by the toolkit, in
`.aw/system/workflows/templates/plans-README.md:65-78`, which defines the mandatory five-element
execution contract and states element 5 as:

> 5. The lifecycle move on completion (`git mv` to the terminal directory, set `Status:`,
>    append a `## Workflow history` line).

So the toolkit instructs a procedure its own gate refuses. Three failures compound:

1. **The instruction is unsatisfiable by hand.** `IPD-S406` requires the newest terminal history
   entry to name a non-generic actor and carry a nonempty summary, and `IPD-M104` requires the
   `Approval:` field to be ABSENT once `Status` is no longer `approved`. A `git mv` plus a manual
   `Status:` edit produces none of those three things. The error text even names the remedy
   (`run the transition via aw ipd finalize --actor <agent/model>`), which is proof the gate expects
   the CLI and the template contradicts it.
2. **The runner prompt says nothing.** Grepping the emitted prompt
   (`prompts/01-waj7w0-exec-attempt-1.md`) for `finalize`, `git mv`, `executed/` or `transition`
   returns only one passing mention of "do not bypass lifecycle controls". The PLAN TEXT was the
   only transition instruction the agent had, and it pointed the wrong way.
3. **Review cannot catch it.** `aw ipd lint --phase review-finalize` passed on this plan at every
   checkpoint, across three separate `/plan-review` rounds, because the linter validates plan
   STRUCTURE and cannot tell that the prose describes a procedure a later phase will reject.

### WHY THIS IS WORTH A TOOLKIT CHANGE, NOT A LOCAL EDIT

The wording is boilerplate and it has propagated. In the target repo it appears in BOTH pending
plans and in ALL FIVE executed plans. The five executed ones only reached `executed` because their
runs happened to use the delegating CLI path (`aw ipd set executed` transparently delegates into
`finalize`, per `ipd-lifecycle.md:110-113`) rather than obeying the clause; their history lines
carry proper attribution such as `executed (antigravity/gemini-2.5-pro)`. So the contract text has
been wrong for every plan this toolkit has ever scaffolded, and it was survivable only by luck of
which path an agent chose. `waj7w0` is the case where an agent followed the written instruction
instead, and lost a full run to it.

The toolkit already knows the right answer in a DIFFERENT file:
`ipd-lifecycle.md:195-207` documents the ordered terminal transaction (the `git mv` is `:203`) and
`ipd-lifecycle.md:110-113` documents that `aw ipd set executed` delegates into the gated
`aw ipd finalize` transaction requiring `--actor`. The defect is that the PLAN-FACING template,
which is what an executing agent actually reads, was never reconciled with it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Reconcile the evidence against the toolkit tree

- [ ] E-01 Re-confirm the four defect sites in THIS tree before editing, and record the quotes. Authoring already verified them at `1.2.1`/`e299a9a5`, but this repo carries 111 pending plans and moves frequently, so a stale citation is the likeliest way this plan goes wrong. Quote the current text at each: `.aw/system/workflows/templates/plans-README.md:77-78` (element 5, the root), `.aw/system/workflows/plan-review/plan-review.md:353` and `:486-488` (the mandate and the reviewer's ADD instruction), `.aw/system/workflows/plan-review-long/02-review-and-revise.md:85` and `review-rubric.md:19` (the long variant's parity copies), and `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md:203` beside `:110-113` (the contradiction). Also confirm `IPD-M104` (`ipd_lint.py:50`) and `IPD-S406` (`:68`) still carry the semantics this plan relies on. If any site has already been fixed or moved, STOP and report rather than editing blind.
  - Depends on: none
  - Expected outcome: a path map from installed to source, with the defective wording quoted from source, or a report that source and installed disagree.
  - Execution state: pending

### Task group 2: Fix the prescribing text

- [ ] E-02 Correct element 5 of the mandatory execution contract in `templates/plans-README.md`. This is the ROOT of the propagation: every scaffolded plan's gate inherits it. Replace the hand-rolled instruction with the tooled one, so element 5 directs the executor to run `aw ipd finalize --actor <agent/model> --message <summary> --apply` and states that this single command performs the whole terminal transaction (history line, terminal `Status:`, the move, the path-scoped lifecycle commit) and is REQUIRED because a hand-built transition cannot satisfy the attribution lint. Do NOT merely add the CLI as an alternative beside `git mv`: an agent reading two options will pick either, and the measured failure is exactly what happens when it picks the wrong one. Say plainly that `git mv` remains correct ONLY for plan RETIREMENT to `superseded/`/`not-executed/`, which `finalize` deliberately does not perform (`ipd-lifecycle.md:115`), so the distinction is preserved rather than lost.
  - Depends on: E-01
  - Expected outcome: the template's element 5 prescribes `aw ipd finalize`, explains why, and confines `git mv` to retirement.
  - Execution state: pending

- [ ] E-03 Correct the same element in the two review workflows that MANDATE and VERIFY the contract. `plan-review.md:353` and `:486-488` both require the gate to carry "the lifecycle move" and instruct the reviewer to ADD it when missing, so a reviewer following them today re-injects the defective wording into any plan lacking it, and passes any plan that already has it. Update both places to name `aw ipd finalize --actor`, and apply the identical change to the long variant, where the mandate lives in `plan-review-long/02-review-and-revise.md:85` and `plan-review-long/review-rubric.md:19` (VERIFIED: not in `03-resolve-and-finalize.md`, which is where a reader might expect it), and which the toolkit keeps in deliberate parity with the single-file variant. State the parity requirement in the edit so the two do not drift.
  - Depends on: E-02
  - Expected outcome: both review workflows require and verify the tooled transition; neither can re-inject `git mv` as the terminal move.
  - Execution state: pending

- [ ] E-04 Reconcile `ipd-lifecycle.md`'s own terminal-transaction recipe with the CLI it documents elsewhere. `:195-207` lists the transaction as six manual steps whose step 3 (`:203`) is "`git mv` the file", while `:110-113` in the same file states that `aw ipd set executed` transparently delegates into the gated `aw ipd finalize` transaction and that a missing `--actor` fails closed. Those two passages describe different procedures. Rewrite `:195-207` so the manual sequence is presented as WHAT FINALIZE DOES INTERNALLY (useful for understanding and for recovery reasoning), explicitly NOT as a runbook for an agent to perform by hand, and point to the command. Keep the recovery guidance that follows it, which is still correct and valuable.
  - Depends on: E-02
  - Expected outcome: the lifecycle doc no longer reads as authorizing a hand-performed terminal move, and its two passages agree.
  - Execution state: pending

### Task group 3: Make the defect impossible to reintroduce

- [ ] E-05 Add a deterministic lint rule that REFUSES a plan whose gate prescribes a hand-rolled terminal move. Text fixes alone do not stop this: the wording is already copied into every existing plan in at least one downstream repo, and a human or agent authoring a gate from memory will reproduce it. Add a check in `agent_workflows/ipd_lint.py` beside the existing gate/metadata rules that fires when a plan's `Approval and execution gate` section instructs a terminal move by hand (for example `git mv` co-occurring with `executed/` or with a `Status: executed` edit) WITHOUT naming `aw ipd finalize`. Allocate a new rule id in the series used by the existing gate rules, and make the message name the fix, following the pattern `IPD-S406` already sets by naming its own remedy. Fire it from the `author` phase onward so it is caught at drafting, not at execution, and deliberately do NOT fire on retirement wording (`superseded/`, `not-executed/`), which legitimately uses `git mv`.
  - Depends on: E-02
  - Expected outcome: a plan whose gate says "`git mv` this file to executed/" fails lint from the author phase with a message naming `aw ipd finalize`; a plan using the CLI, and a plan describing retirement, both pass.
  - Execution state: pending

- [ ] E-06 Add regression tests for E-05 and for the corrected template. In the toolkit's existing test suite and following its conventions: assert the new rule FIRES on a gate carrying the old wording (use the exact clause 13 text quoted in this plan's Goal as the fixture, since that is the string measured in production), assert it does NOT fire on a gate naming `aw ipd finalize`, assert it does NOT fire on retirement wording, and assert the scaffolded/templated contract text itself contains `aw ipd finalize` and does not instruct `git mv` to `executed/`. The last assertion is the one that keeps the template honest, because it fails if someone edits the template back.
  - Depends on: E-05
  - Expected outcome: four tests, each failing against the pre-fix tree and passing after.
  - Execution state: pending

### Task group 4: Migration and disclosure

- [ ] E-07 Decide and document what happens to plans ALREADY carrying the defective clause, and record the decision. Every plan scaffolded before this fix has it, including plans already in `executed/` whose history is frozen. Options span leaving them (the delegating CLI path makes most of them survivable), a `aw migrate`-style fixer for pending plans only, or lint grandfathering keyed to a date or a `Scope-Paths` cutoff as Order `oorry1` already did for the attribution lint (`ipd-lifecycle.md:113`). Choose ONE, state the reasoning, and if the choice is grandfathering, implement the cutoff so existing executed plans do not start failing `aw check`. Do NOT rewrite history in terminal directories. This item is a DECISION plus its implementation, not open-ended design: the precedent for the cutoff mechanism already exists in the same file.
  - Depends on: E-05
  - Expected outcome: a stated, implemented policy for pre-existing plans, with no terminal-directory history rewritten and no new failures on the existing executed tree.
  - Execution state: pending

- [ ] E-08 Record the failure and the fix in the toolkit's own release notes or changelog, per its conventions. This defect cost a complete unattended run in a downstream repo and was invisible to three rounds of `/plan-review`, so a downstream maintainer reading only a version bump would not know their existing plans carry an instruction that can strand a lane. State: the symptom (an executed-status transition refused by `IPD-M104`/`IPD-S406`, item reported `partial`, lane preserved unintegrated), the cause (the mandatory contract's element 5 prescribed a hand-rolled move), the fix, and what a downstream repo should do about plans it already has (from E-07's decision). Do NOT overstate it as a security issue; it is a correctness and lost-work defect.
  - Depends on: E-07
  - Expected outcome: release notes state the symptom, cause, fix and downstream action, accurately scoped.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The FAILURE was measured downstream in `cmmc-tracker-sheet-01` at installed toolkit
  `1.1.1.dev3028+g476354fc` (driver `agy_runipd.py` sha256 `9ffb4267...`, per the run's own
  `tool-identity-verified` event). The DEFECT was then re-verified present in THIS repo at `1.2.1`,
  `HEAD` `e299a9a5`; all line numbers below refer to this tree. E-01 re-confirms them at execution
  time.
- The defective wording's source is the mandatory five-element execution contract in
  `.aw/system/workflows/templates/plans-README.md:65-78`, element 5 (`:77-78`).
- `.aw/system/workflows/plan-review/plan-review.md:353` and `:486-488` both require that element and
  tell the reviewer to ADD it if absent, which is the re-injection path. The long variant carries the
  same mandate at `plan-review-long/02-review-and-revise.md:85` and `review-rubric.md:19`.
- `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md:203` documents the transaction step as a manual
  `git mv`; `:110-113` documents CLI delegation into gated `finalize` requiring an attributed
  `--actor` and failing closed without one; `:115` records that finalize deliberately does NOT perform retirement, which is why
  `git mv` must remain documented for `superseded/`/`not-executed/`.
- The gate that refuses a hand-built transition: `IPD-M104` (`Approval:` must be absent unless
  `Status: approved`) and `IPD-S406` (terminal history entry needs a non-generic actor and a
  nonempty summary). `IPD-S406`'s message already names `aw ipd finalize --actor` as the remedy.
- Defense in depth already exists for the raw-commit path: a local pre-commit hook
  (`python3 -m agent_workflows ipd-executed-gate`, `ipd-lifecycle.md:117-127`) refuses a commit
  that moves a plan into `executed/` without finalize evidence in `.aw/state/`. That hook is
  LOCAL and skippable, and it did not fire here because the agent reverted before committing. It is
  a backstop, not a substitute for correct instructions.
- Prose convention for this repo family: no em or en dashes in user-facing prose. `plans-README.md`
  is user-facing; the lint message in `ipd_lint.py` is agent-facing.

## Findings

| ID | Severity | Remediation Risk | Finding |
|----|----------|------------------|---------|
| G-01 | High | Low | **The mandatory execution contract prescribes an unsatisfiable procedure.** `templates/plans-README.md` element 5 instructs `git mv` + `Status:` edit + history line. That cannot satisfy `IPD-S406` (non-generic actor, nonempty summary) or `IPD-M104` (`Approval:` cleared), so an agent that obeys the contract literally is refused by the gate. Measured: one complete unattended run lost, work stranded on an unintegrated lane. |
| G-02 | High | Low | **The review workflows re-inject the defect.** `plan-review.md:353` and `:486-488` (plus `plan-review-long/02-review-and-revise.md:85` and `review-rubric.md:19`) require "the lifecycle move" in every gate and instruct the reviewer to ADD it when missing. So the workflow whose job is to harden a plan writes the failing instruction into it, and passes plans that already carry it. Three review rounds on `waj7w0` did exactly that. |
| G-03 | Medium | Low | **The two lifecycle passages contradict each other.** `ipd-lifecycle.md:195-207` gives a six-step manual transaction whose step 3 (`:203`) is `git mv`; `:110-113` says the CLI delegates into a gated transaction requiring `--actor`. An agent reading the first performs the failing path. |
| G-04 | Medium | Low | **No deterministic check exists for gate PROSE.** `aw ipd lint` validates structure and state, so `review-finalize` passed on a plan whose gate text was guaranteed to fail `post-transition`. The failure was only discoverable by executing the plan, which is the most expensive place to find it. |
| G-05 | Medium | Low | **The runner prompt omits the transition entirely.** Grepping `prompts/01-waj7w0-exec-attempt-1.md` for `finalize`/`git mv`/`executed/`/`transition` yields only "do not bypass lifecycle controls", so the plan's own wrong instruction was the sole guidance. Worth considering whether the driver prompt should name the finalize command, though that is the driver's concern and is recorded here rather than fixed. |
| G-06 | Low | Low | **The defect is already propagated downstream.** In one target repo the wording is in both pending plans and all five executed plans. The executed ones survived only because their runs used the delegating CLI rather than obeying the clause, which is luck, not design. E-07 owns the migration decision. |

## Proposed changes (ordered, validatable)

1. Reconcile installed-copy citations against toolkit source and confirm the defect there (E-01). Remediation Risk Low; this is the guard against editing from a stale subset.
2. Fix the prescribing text at its root and everywhere it is mandated or restated: the template, both review workflows, and the lifecycle doc's manual recipe (E-02 to E-04). Remediation Risk Low, all prose.
3. Make reintroduction impossible with a lint rule plus regression tests, including a test that the template itself stays correct (E-05, E-06). Remediation Risk Low.
4. Decide and implement the policy for pre-existing plans, then disclose the defect in release notes (E-07, E-08). Remediation Risk Low; the grandfathering precedent already exists in-tree.

Ordering rationale: the template is the root, so it is fixed before the files that restate it. The
lint follows the text so its fixture matches the corrected wording. Migration follows the lint,
because the grandfathering decision depends on what the lint would otherwise flag. Disclosure is
last so it can describe the decision accurately.

## Deferred / out of scope (with reason)

- **Changing the driver prompt to name the finalize command (G-05).** The emitted prompt says nothing about the transition, and arguably should, but the prompt is the runner's contract rather than the plan template's, and changing it affects every host and every action class. Recorded as a finding for the driver's owner rather than bundled here. Consequence if unresolved: the plan text remains the only transition instruction, which is exactly why getting the plan text right is this plan's job.
- **Rewriting history in `executed/` plans.** Out of scope on principle: terminal-directory content is frozen history, and the executed plans' actual transitions were correctly attributed anyway. E-07 covers pending plans only.
- **Making the `ipd-executed-gate` pre-commit hook non-skippable or CI-enforced.** The toolkit deliberately has no remote enforcement (`ipd-lifecycle.md:126`), and that is a stated design position, not an oversight to fix in passing.
- **Auditing every other workflow for the same class of contradiction.** This plan fixes the one instance measured in production. A systematic sweep for "toolkit prose that prescribes what a toolkit gate refuses" is a worthwhile separate assessment, and naming it here is not the same as doing it badly now.

## Scope check

- Over-scope: none. Every item traces to G-01 through G-06. E-05's lint is the only NEW mechanism, justified because G-04 shows text fixes alone are undetectable at review time and the wording is already copied widely.
- Under-scope: G-05 (the silent driver prompt) is deliberately deferred to its owner with the reason stated. Nothing else is dropped.
- Right-sizing: 8 E-leaves in four groups, under the 18 advisory threshold. Each is one concern in one focused pass. E-02 to E-04 are separate rather than one "fix the docs" item because they have different owners and different verification: the template is the root, the review workflows are the re-injection path, and the lifecycle doc is an internal contradiction.

## Required tests / validation

- Run the toolkit's own suite BARE, per its conventions, before and after. State the baseline count and reconcile any difference. Do NOT add flags to "help"; if the toolkit configures `addopts`, a bare run is already correct.
- E-06's four tests must be shown FAILING against the pre-fix tree and passing after. Paste both runs. The template-content assertion in particular must be shown to fail if the template is reverted, or it proves nothing.
- Demonstrate the new lint rule END TO END on the exact production fixture: paste the old clause 13 text into a scratch plan, show `aw ipd lint --phase author` refusing it and naming `aw ipd finalize`, then show the corrected wording passing. This is the reproduction of the measured failure and is the single most important piece of evidence.
- Verify the retirement path did not regress: a plan gate describing `git mv` to `superseded/` must still pass.
- Grep the toolkit tree after the edits to confirm no remaining text instructs `git mv` to `executed/` as the terminal move for a plan, and paste the result.
- Do NOT attempt to validate this by executing a real unattended run; the failure is already measured and a live run is an expensive and non-deterministic test.

## Spec / documentation sync

- `templates/plans-README.md` IS the user-facing contract documentation; E-02 is itself the doc change.
- `ipd-lifecycle.md` is the authoritative lifecycle description; E-04 amends it.
- If the toolkit carries an `ipd-spec` spec artifact describing the gate's required elements, it must be amended in the same change and declared in `Scope-Paths`; E-01 should discover whether one exists, since the installed subset in the target repo does not include the specs tree.
- E-08 covers release notes. No other doc changes.

## Open questions

### OQ-01: What should happen to plans that already carry the defective clause?

- Blocking: no
- Status: open
- Owner: toolkit maintainer
- Resolution or deferral rationale: E-07 must choose among leaving them (most survive via CLI delegation), a migration fixer for pending plans, or lint grandfathering with a cutoff. The precedent exists in-tree: Order `oorry1` grandfathered the existing executed tree for the attribution lint via a `Scope-Paths` cutoff (`ipd-lifecycle.md:113`). Non-blocking because any of the three is safe; the requirement is that the choice be stated and that the existing executed tree not start failing `aw check`.

### OQ-02: Should the driver prompt also name the finalize command?

- Blocking: no
- Status: open
- Owner: toolkit maintainer
- Resolution or deferral rationale: the emitted execute prompt mentions the transition nowhere, so a correct plan is currently the only thing standing between an agent and a hand-rolled move. Naming the command in the prompt would be belt-and-braces. Deferred because the prompt is the driver's contract across all hosts and action classes, and this plan should not change it as a side effect. Recorded as G-05.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the installed-to-source path map, with the defective element-5 wording quoted from the toolkit SOURCE file. If source and the installed copy disagree, quote both and state that execution stopped.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the diff of `templates/plans-README.md` element 5. Confirm it names `aw ipd finalize --actor <agent/model> --message <summary> --apply`, states WHY the hand-rolled path is refused, and confines `git mv` to retirement. Confirm it does NOT offer both as alternatives.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: diffs of both review workflows at every place that mandates or verifies the contract, including the reviewer instruction to ADD the element when missing. Quote the parity statement, and confirm by grep that neither file still names `git mv` as the terminal move.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the diff of `ipd-lifecycle.md:195-207`. Quote the rewritten passage showing the manual sequence is presented as finalize's internals rather than an agent runbook, and quote `:110-113` alongside it to show the two now agree. Confirm the recovery guidance survived.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the new rule's code and id. Paste the END-TO-END reproduction: the production clause 13 text in a scratch plan refused at `--phase author` with a message naming `aw ipd finalize`, then the corrected wording passing. Also paste a retirement-wording gate passing, proving the rule does not over-fire.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the four tests and their runner output, all passing, PLUS the pre-fix failing run. Then prove the template assertion is load-bearing: revert the template, paste the FAILING run, restore, paste the passing run.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: state the chosen policy and its reasoning. If grandfathering, paste `aw check` (or the equivalent) over a tree containing pre-existing executed plans showing NO new failures. Confirm no file in a terminal directory was modified.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: quote the release-notes entry. Confirm it states symptom, cause, fix and downstream action, and that it does not characterize the defect as a security issue.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (8 E-leaves). The four groups are separable, but the lint (group 3) must follow the text fixes (group 2) so its fixture matches the corrected wording, and migration (group 4) must follow the lint so the grandfathering decision is informed by what the lint would flag.

This plan must be approved by a human before execution and is not auto-run.

Execution contract for whoever executes this plan:

1. **EXECUTE THIS IN THE `agent-workflows` REPOSITORY, NOT IN THE REPO WHERE IT WAS AUTHORED.** It was written in `cmmc-tracker-sheet-01` because that is where the failure was measured. Re-file it in the toolkit repo first, and treat every path in `Scope-Paths` as INFERRED from an installed subset until E-01 confirms it.
2. NO OPEN QUESTION BLOCKS EXECUTION. OQ-01 is owned by E-07 with three safe options and an in-tree precedent. OQ-02 is deferred to the driver's owner and is recorded, not required.
3. THIS PLAN'S OWN GATE USES THE CORRECTED WORDING (clause 9 below). That is deliberate: a plan fixing this defect must not carry it. If you find yourself about to `git mv` this file to `executed/`, that is the bug this plan exists to remove.
4. DO NOT WEAKEN THE GATE TO MAKE THE HAND-ROLLED PATH WORK. The refusals (`IPD-M104`, `IPD-S406`) are correct and exist to stop an agent writing an unattributed `executed` attestation, which is the same class as the `Readiness` rule. The instruction is what is wrong, not the gate.
5. PRESERVE THE RETIREMENT PATH. `finalize` deliberately does not perform retirement, so `git mv` to `superseded/`/`not-executed/` must remain documented and must not trip the new lint. A fix that breaks retirement is a worse defect than the one being fixed.
6. HARD MUST honesty rule: paste ACTUAL runner output for every test claim, from a bare run. For E-06 paste both the failing and passing runs, and for E-05 paste the end-to-end reproduction rather than asserting the rule works.
7. SCOPE FENCE (a declaration, not a stop order). The declared paths are those in `Scope-Paths`, subject to E-01's reconciliation; expect the real set to include the toolkit's test directory and possibly a specs artifact and a changelog. Editing outside the list is permitted where the work genuinely requires it, but each edit MUST be justified at finalize (`aw ipd finalize --scope-reason`) and each declared path left unmodified MUST be acknowledged (`--scope-ack`). Deliberate exclusions: do not change the driver prompt, do not touch `executed/` history, do not add CI enforcement.
8. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <path>`). Never `git add -A`, bare `git add`, or `-a`. Never push. Verify `git diff --cached --name-only` before every commit.
9. On completion, run `aw ipd lint --phase pre-transition` and confirm it reports conforming with every `V-*` carrying observed evidence, then perform the terminal transition with the TOOLED command, which does the history line, the terminal `Status:`, the move and the path-scoped lifecycle commit as one gated transaction:

       aw ipd finalize --actor '<agent/model>' --message '<summary>' --apply

   Do NOT `git mv` this file and do NOT hand-edit `- Status:`. A hand-built transition cannot satisfy `IPD-S406`'s attribution requirement or clear `Approval:` for `IPD-M104`, which is the exact failure this plan fixes.

Note for the approver: this is a small documentation-and-lint change with an outsized payoff. The
toolkit currently ships a mandatory contract clause instructing every executing agent to perform
the terminal transition in a way its own gate is built to refuse, and the review workflow that is
supposed to harden plans actively inserts that clause. It cost one full unattended run (9m 31s,
27.3M tokens) that completed all its work and delivered none of it, and it was invisible to three
rounds of plan review because the linter checks structure rather than whether the prose describes
a procedure a later phase rejects. The fix is four prose corrections plus one lint rule; the lint
is the part that matters, because the wrong wording is already copied into every plan this toolkit
has scaffolded.
