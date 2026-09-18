# IPD: Stop the plan-gate execution contract from prescribing a hand-rolled lifecycle move that the finalize gate refuses

- Date: 2026-09-17
- Kind: child
- Concern: functionality
- Scope: Correct the toolkit text that tells every IPD's execution contract to end with a hand-rolled `git mv` + `Status:` edit, which the `aw ipd finalize` gate and the post-transition attribution lint are designed to REFUSE. Measured consequence: a real unattended run (`run-20260917T224036Z-2413656`) completed all of plan `waj7w0`'s work, followed its gate clause literally, was refused by `IPD-M104` and two `IPD-S406` errors, reverted the move, and reported `partial` with the lane unintegrated. Fixes the source template, the four workflows that mandate or verify the contract, and adds a deterministic lint so a plan carrying the wrong wording cannot pass review again.
- Scope-Paths: .aw/system/workflows/templates/plans-README.md, .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/02-review-and-revise.md, .aw/system/workflows/plan-review-long/review-rubric.md, .aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md, agent_workflows/ipd_lint.py, tests/test_ipd_lint.py, tests/test_ipd_authoring.py, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Set: gate-contract
- Order: 1
- Highest E allocated: 09
- Readiness: go-pending-approval
- Author: opencode model=its_direct/pt3-claude-opus-5-1m-us
- Id: dcri4s

## Workflow history
- 2026-09-18 executed (aw agy run model=gemini-3.7-flash-high): aw agy run self-finalize: dcri4s verified (set gate-contract, attempt 1). [Scope reconciliation - in-scope-unmodified tests/test_ipd_authoring.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-09-18 approved (aw set): status set to approved
- 2026-09-18 reviewed (opencode/its_direct-pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. PR-001..PR-010 all FIXED.
- 2026-09-17 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. Findings PR-001..PR-010, ALL FIXED in place. Reviewed at HEAD `edb9ba85`; `aw ipd lint --phase author` conforming BEFORE semantic review and `--phase review-finalize` conforming after every revision, so nothing was structural. DISCLOSURE: same agent/model authored this plan, so this is a SELF-REVIEW and its value rests on RE-MEASURING rather than re-reading. THE FINDING THAT CHANGED THE DESIGN (PR-001, BLOCKER): the plan's own prescribed fix is ALSO refused by the toolkit. It required every gate to say "run `aw ipd finalize --actor ... --apply`", but a managed lane may not run that verb; measured, `AW_EXECUTION_ROLE=worker python3 -m agent_workflows ipd finalize dcri4s --actor x/y --message probe --apply` prints `AW-LIFECYCLE-ROLE-001` and exits 2, because both runners export that marking for every ISOLATED turn (the default) and the refusal is checked before any selector resolution (`oc_runipd.py:5876`, `agy_runipd.py:2779`, `ipd_lifecycle.py:4285`). Adopting the fix would have moved the wasted turn from `IPD-M104`/`IPD-S406` to a different refusal while looking like a repair, reopening backlog `i452hf` which commit `cdef9c90` closed for exactly this. The real root cause is that the contract names a COMMAND for a step whose OWNER is a run option (`--no-self-finalize`: "the agent must move the plan itself"), so element 5 now separates the unconditional OBLIGATION from the CONDITIONAL owner, new E-09/V-09 REPRODUCE the refusal before any text is written with a STOP condition, and the plan's own gate dogfoods the conditional form (PR-010). PR-002 (HIGH, OVER-SCOPE): the silent runner prompt is not an unowned gap but is owned by APPROVED, release-blocking plan `8b9ufm`, whose own review reached the same conditional design; a new gate clause forbids touching any prompt builder. PR-003 (HIGH): E-07's premise was false, measured over gate SECTIONS - 15 of 110 pending gates mention `git mv`+`executed/` and ALL 15 already forbid it, while the 156 executed ones are exempt by construction since `lint_text` short-circuits every terminal-dir plan to `legacy` (`ipd_lint.py:1067-1068`, verified across all 516) - so the item inverted from build-a-migration to verify-none-is-needed. PR-004 (MEDIUM): E-05 lacked gate-SECTION scoping, so the rule's first victim would have been this plan, which quotes the clause in its Goal; scoping is now required and a fifth regression test pins it. PR-005 (MEDIUM): `IPD-S406` was cited at `ipd_lint.py:68`, which is actually `IPD-M107`, and five `ipd-lifecycle.md` ranges were stale by 2 to 4 lines; all corrected. PR-006 (MEDIUM): G-03's "the two passages contradict each other" is false - `:105-107` already says finalize is "the ONLY supported terminal path; the manual ordered steps below are the contract it implements" - so E-04 is now a local clarification with an explicit no-edit-needed branch. PR-007 (MEDIUM): the spec check was performed AT REVIEW rather than deferred; neither `ipd-spec` nor `ipd-structure-and-linting` needs amending. PR-008/PR-009 (LOW): the bare-suite flag rule and the honest limit that the worker-role marking is a selector, not a boundary (backlog `c4yixg`). BOTH open questions RESOLVED from evidence (five recorded decisions D-1..D-5, all reversible, in the typed review record); no `Reversible: no` decision was taken and no finding was left unfixed, so nothing required escalation to a blocking question.
- 2026-09-17 to-review (opencode model=its_direct/pt3-claude-opus-5-1m-us): authored from a measured production failure in the `cmmc-tracker-sheet-01` target repo (installed toolkit 1.1.1.dev3028+g476354fc), then RE-VERIFIED and filed against this repo at 1.2.1 / HEAD e299a9a5, where the defective text lives. Scope-Paths corrected from a guessed `agent_workflows/workflows/...` layout to the real `.aw/system/workflows/...` sources, and the lint target from `ipd_schema.py` to `ipd_lint.py`, where IPD-M104 (:50) and IPD-S406 (:68) are actually defined.
- 2026-09-17 draft (opencode model=its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the plan-level execution contract tell an executing agent the terminal transition is NOT ITS
JOB in a managed lane, and stop telling it to hand-build that transition with `git mv`.

### WHAT REVIEW CHANGED ABOUT THE DIAGNOSIS (read this before the sections below)

`/plan-review` 2026-09-17 confirmed the DEFECT and the four sites, and REJECTED the fix the plan
originally prescribed. The plan asked every plan's element 5 to say "run
`aw ipd finalize --actor ... --apply`". Measured at this HEAD, that instruction is REFUSED for the
exact executor the plan is written for, and the refusal is by design:

```text
$ AW_EXECUTION_ROLE=worker python3 -m agent_workflows ipd finalize dcri4s \
      --actor 'opencode/test' --message 'probe' --apply --dir .
AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes; a worker-role process
must not run them (refused: aw ipd finalize). The runner performs begin/finalize for this lane;
report your result instead (write the outcome file the prompt names) and let the driver transition
the plan.
EXIT=2
```

Both runners export `AW_EXECUTION_ROLE=worker` into every ISOLATED lane turn
(`oc_runipd.py:5876`, `agy_runipd.py:2779`), and isolation is the DEFAULT. The refusal is checked
FIRST, before any selector resolution (`ipd_lifecycle.py:4285`, `run_begin` twin at `:4105`), and
`_refuse_worker_role_verb` (`:84-100`) returns `EXIT_CANNOT_RUN`. So the original fix would have
replaced one instruction the toolkit refuses with a DIFFERENT instruction the toolkit refuses,
having moved the wasted turn from `IPD-M104`/`IPD-S406` to `AW-LIFECYCLE-ROLE-001`. That precise
substitution already cost a run once: it is backlog `i452hf`, "driver refinalizes a lane the agent
already finalized", closed by commit `cdef9c90`, whose whole purpose was to STOP an in-lane agent
finalizing.

WHO OWNS THE TRANSITION IS A RUN OPTION, NOT A CONSTANT. Under the default the DRIVER finalizes
(`driver_finalize`, `oc_runipd.py:1294` / `agy_runipd.py:1037`, both inside
`if self_finalize and not is_review:` at `oc_runipd.py:6715`). Under `--no-self-finalize` the
runner calls neither verb, and that flag's own help says the consequence: "the agent must move the
plan itself" (`oc_runipd.py:9078-9083`). Outside any runner (a human or agent executing a plan by
hand) the executor owns it too. A contract element that names ONE owner unconditionally is
therefore wrong in one of the two directions whichever owner it picks: name the agent and a managed
lane wastes a turn on a refusal; name the runner and a hand-executed plan is stranded in `pending/`
transitioned by nobody, which is worse.

So the corrected fix is CONDITIONAL, and this is the plan's central design decision: element 5 must
state the OBLIGATION (the plan must reach `executed` through the gated finalize transaction, never
through a hand-built move) SEPARATELY from the ACTOR (who runs it, which depends on whether the
executor is a managed worker). See E-02.

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
   only transition instruction the agent had, and it pointed the wrong way. VERIFIED AT THIS HEAD
   AND NOT THIS PLAN'S TO FIX: the shared builder `runner_shared.build_prompt:9832` (one definition
   for both hosts) mentions finalize exactly once, presupposing the agent performs it ("If the IPD
   cannot validly finalize, preserve partial work..."), and never states who owns the transition.
   That surface is OWNED by APPROVED plan `8b9ufm` (`roleadv-01`), which states the role at turn
   start gated on the run's frozen `self_finalize`. See the Deferred section: this plan must not
   touch it.
3. **Review cannot catch it.** `aw ipd lint --phase review-finalize` passed on this plan at every
   checkpoint, across three separate `/plan-review` rounds, because the linter validates plan
   STRUCTURE and cannot tell that the prose describes a procedure a later phase will reject.
4. **AND THE OBVIOUS FIX IS ALSO REFUSED** (added by review; the reason this plan's shape changed).
   Substituting "run `aw ipd finalize`" for the `git mv` does not resolve the contradiction for a
   managed lane, because `AW-LIFECYCLE-ROLE-001` refuses that verb from a worker-role process. See
   the Goal's measured reproduction. The contract's real defect is not WHICH command it names; it is
   that it names a command AT ALL for a step whose owner varies by run option.

### WHY THIS IS WORTH A TOOLKIT CHANGE, NOT A LOCAL EDIT

The wording is boilerplate and it has propagated. In the target repo it appears in BOTH pending
plans and in ALL FIVE executed plans. The five executed ones only reached `executed` because their
runs happened to use the delegating CLI path (`aw ipd set executed` transparently delegates into
`finalize`, per `ipd-lifecycle.md:109-114`) rather than obeying the clause; their history lines
carry proper attribution such as `executed (antigravity/gemini-2.5-pro)`. `waj7w0` is the case
where an agent followed the written instruction instead, and lost a full run to it.

PROPAGATION MEASURED IN THIS REPO AT REVIEW, correcting the plan's original "wrong for every plan
this toolkit has ever scaffolded". Counting only the `## Approval and execution gate` SECTION (the
gate is what an executor acts on; a `git mv` mentioned in a plan's own subject matter is not a
transition instruction):

- 110 pending plans. 15 gates name `git mv` alongside `executed/`, and ALL 15 (including this one)
  already carry the CORRECTIVE wording "never with a raw `git mv` plus a hand-edited `- Status:`".
  ZERO pending gates prescribe the hand-rolled move. So there is nothing to migrate in `pending/`.
- 516 executed plans. 156 gates carry `git mv` + `executed/` with no mention of finalize, and 30
  mention finalize. Those 156 are the real historical footprint, and they are frozen history.

So the honest statement is: the TEMPLATE is defective and would reproduce the failure in any repo
whose authors follow it (as the target repo's authors did), while THIS repo's live plans have
already been hand-corrected one at a time, which is precisely the symptom of a template nobody
trusts. That strengthens the case for fixing the template and WEAKENS the case for a migration
(E-07) and for lint grandfathering.

The toolkit already knows the right answer in a DIFFERENT file:
`ipd-lifecycle.md:195-207` documents the ordered terminal transaction (the `git mv` is `:203`) and
`ipd-lifecycle.md:105-107` states plainly that finalize "is the ONLY supported terminal path; the
manual ordered steps below are the contract it implements", while `:109-114` documents that
`aw ipd set executed` delegates into the gated transaction requiring `--actor`. Note the nuance the
plan originally missed: `:106-107` ALREADY says the manual steps are a contract description rather
than a runbook, so E-04 is a clarification of an existing statement, not the insertion of a new
one. The defect is that the PLAN-FACING template, which is what an executing agent actually reads,
was never reconciled with it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Reconcile the evidence against the toolkit tree

- [x] E-01 Re-confirm the defect sites in THIS tree before editing, and record the quotes. Review re-verified them at HEAD `edb9ba85` (all present, line numbers below corrected), but this repo moves frequently, so a stale citation is the likeliest way this plan goes wrong. Quote the current text at each: `.aw/system/workflows/templates/plans-README.md:65-78`, element 5 at `:77-78` (the root); `.aw/system/workflows/plan-review/plan-review.md:351-354` and `:486-488` (the mandate and the reviewer's ADD instruction); `.aw/system/workflows/plan-review-long/02-review-and-revise.md:85` and `review-rubric.md:17-19` (the long variant's parity copies); and `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md:203` beside `:105-107` and `:109-114`. Also confirm `IPD-M104` (`ipd_lint.py:50`, semantics in `ipd_schema.py:398-407`) and `IPD-S406` (`ipd_lint.py:63-65`, emitted at `:895-915`) still carry the semantics this plan relies on. CORRECTED BY REVIEW: the plan cited `IPD-S406` at `ipd_lint.py:68`, which is `IPD-M107` (`C_READINESS_UNATTESTED`); the S406 constant is at `:63-65`. If any site has already been fixed or moved, STOP and report rather than editing blind.
  - Depends on: none
  - Expected outcome: every cited site quoted from source at execution HEAD, or a report naming which citation is stale and that execution stopped.
  - Execution state: performed

- [x] E-09 RE-CONFIRM THE ROLE REFUSAL AND THE OWNERSHIP CONDITIONALITY BEFORE WRITING ANY CONTRACT TEXT, because the entire corrected design (E-02) rests on it and a wrong reading here reproduces the very failure class this plan exists to close. Reproduce the refusal and paste it: `AW_EXECUTION_ROLE=worker python3 -m agent_workflows ipd finalize <any-pending-id6> --actor 'x/y' --message 'probe' --apply --dir .` must print `AW-LIFECYCLE-ROLE-001` and exit 2. Then confirm the three facts that make ownership conditional, by citation: both runners export the worker role for an ISOLATED turn only (`oc_runipd.py:5876`, `agy_runipd.py:2779`, both keyed on `work_dir`); the driver's own `driver_finalize` runs unmarked and is called only inside `if self_finalize and not is_review:` (`oc_runipd.py:6715`); and `--no-self-finalize` exists with help text "the agent must move the plan itself" (`oc_runipd.py:9078-9083`). If the refusal does NOT reproduce, STOP and report: the design premise has changed and E-02 must be re-derived rather than written to this plan's text.
  - Depends on: E-01
  - Expected outcome: the pasted refusal plus the three citations, or a report that the premise no longer holds and execution stopped.
  - Execution state: performed

### Task group 2: Fix the prescribing text

- [x] E-02 Rewrite element 5 of the mandatory execution contract in `templates/plans-README.md:77-78` to state the OBLIGATION and the OWNER SEPARATELY. This is the ROOT of the propagation: every scaffolded plan's gate inherits it. The new element 5 must carry exactly three things. (a) THE OBLIGATION, unconditional: the plan reaches `executed` ONLY through the gated finalize transaction, which alone produces the attributed history entry, the terminal `Status:`, the move, and the path-scoped lifecycle commit; a hand-built `git mv` plus a `Status:` edit is NEVER a valid terminal transition, because it satisfies neither `IPD-S406` (non-generic actor plus nonempty summary) nor `IPD-M104` (`Approval:` cleared). (b) THE OWNER, conditional and stated as a rule the executor can evaluate: if the turn is a managed lane (the runner set `AW_EXECUTION_ROLE=worker`), the transition is the RUNNER'S and the executor MUST NOT run `aw ipd finalize`; it reports its result and stops. Otherwise (a human or agent executing by hand, or a run under `--no-self-finalize`) the executor runs `aw ipd finalize --actor '<agent/model>' --message '<summary>' --apply` itself. Say that an executor unsure which case it is in should simply ATTEMPT finalize and treat an `AW-LIFECYCLE-ROLE-001` refusal as the EXPECTED, SUCCESSFUL handoff rather than a failure, which makes the wrong guess cost nothing. (c) THE RETIREMENT CARVE-OUT: `git mv` remains correct ONLY for retirement to `superseded/`/`not-executed/`, which finalize deliberately does not perform (`ipd-lifecycle.md:114-116`). Do NOT present the hand-rolled move as an alternative anywhere: an agent reading two options for the SAME case picks either, which is the measured failure. NOTE the deliberate division of labor with approved plan `8b9ufm`: that plan tells the agent the role at TURN START through the runner prompt; this element makes the PLAN TEXT agree with it instead of contradicting it. Do not edit any prompt builder here (see the Deferred section).
  - Depends on: E-09
  - Expected outcome: element 5 states the unconditional obligation, the conditional owner with the attempt-and-accept-refusal rule, and the retirement carve-out, and offers the hand-rolled move for no case.
  - Execution state: performed

- [x] E-03 Correct the same element in the two review workflows that MANDATE and VERIFY the contract, so a reviewer stops re-injecting the defective wording. `plan-review.md:351-354` requires the gate to carry "the lifecycle move" and instructs the reviewer to ADD it when missing; `:486-488` repeats it in the rubric. Replace the phrase "the lifecycle move" at BOTH places with wording that names the OBLIGATION and the CONDITIONAL OWNER as E-02 defines them, and add the reviewer-facing consequence: a gate that instructs a hand-rolled `git mv` to `executed/` is a FINDING to fix, and a gate that unconditionally instructs the executor to run `aw ipd finalize` is ALSO a finding, because it is wrong for a managed lane. Apply the identical change to the long variant at `plan-review-long/02-review-and-revise.md:85` and `review-rubric.md:17-19` (VERIFIED at review: those are the only two sites; `03-resolve-and-finalize.md` does not carry it, which is where a reader might expect it). State the parity requirement in the edit so the two variants do not drift, and note that `plan-review.md:13-17` already declares that parity.
  - Depends on: E-02
  - Expected outcome: both review variants require the conditional contract, and each names BOTH failure directions (hand-rolled move, and an unconditional finalize instruction) as findings.
  - Execution state: performed

- [x] E-04 Sharpen `ipd-lifecycle.md`'s terminal-transaction recipe so its six manual steps cannot be read as a runbook. CORRECTED BY REVIEW: the plan claimed `:195-207` and `:109-114` "describe different procedures" and that the file "reads as authorizing a hand-performed terminal move". It does not, quite: `:105-107` ALREADY states finalize "is the ONLY supported terminal path; the manual ordered steps below are the contract it implements". So this item is a CLARIFICATION, not the repair of a contradiction, and it must not be written as though it were. Make the framing local to the passage a reader lands on: add to the `## The terminal transaction` heading section itself (`:195-197`) an explicit statement that the ordered steps are WHAT `aw ipd finalize` PERFORMS INTERNALLY, are given for understanding and recovery reasoning, and are NOT to be performed by hand, cross-referencing `:105-107` rather than restating it. Keep the recovery guidance that follows, which is correct and valuable. If E-01 finds the passage already carries such a statement, record that and make no edit rather than adding a redundant one.
  - Depends on: E-02
  - Expected outcome: the terminal-transaction section states locally that its steps are finalize's internals and not a hand runbook, or a recorded finding that it already did and no edit was needed.
  - Execution state: performed

### Task group 3: Make the defect impossible to reintroduce

- [x] E-05 Add a deterministic lint rule that REFUSES a plan whose gate prescribes a hand-rolled terminal move. Why a lint at all, restated honestly after review corrected the premise: it is NOT true that "the wording is already copied into every existing plan" here (all 15 pending gates carrying `git mv` already forbid it; see the propagation measurement in the Goal). The real justification is prospective and is stronger for being narrow: the wording IS in 156 executed gates and in at least one downstream repo's live plans, an author writing a gate from memory reproduces it, and G-04 shows review cannot catch it. SCOPE THE DETECTION TO THE GATE SECTION ONLY, using the parser that already exists (`ipd_lint.parse` gives `doc.h2` with each heading's line, and `ipd_schema.H_APPROVAL_GATE` names the section); a whole-file text scan would fire on this very plan, which quotes the defective clause in its Goal, and on plans whose subject matter is the executed-transition gate itself (`i4c0c3`, `y9vpvv`). Fire when the gate section instructs a terminal move by hand (`git mv` co-occurring with `executed/`, or with a `Status: executed` edit) AND the gate does not name `aw ipd finalize`. Deliberately do NOT fire on retirement wording (`superseded/`, `not-executed/`), which legitimately uses `git mv`. Allocate a new rule id in the existing gate/metadata series and make the message name the remedy, as `IPD-S406` does. Fire from the `author` phase onward so it is caught at drafting; note that terminal-directory plans are unaffected without any grandfathering work, because `lint_text` short-circuits every terminal-dir file to the `legacy` disposition before any check runs (`ipd_lint.py:1067-1068`, `_is_terminal_dir` at `:1043`) -- verified at review by linting the whole executed tree, which reports `legacy/not evaluated` for all 516.
  - Depends on: E-02
  - Expected outcome: a gate saying "`git mv` this file to executed/" fails lint at `author` with a message naming the remedy; a gate naming finalize passes; a gate describing retirement passes; and a plan that merely QUOTES the defective clause outside its gate passes.
  - Execution state: performed

- [x] E-06 Add regression tests for E-05 and for the corrected template, in the toolkit's existing suite and following its conventions. Five assertions, not four: the new rule FIRES on a gate carrying the production clause 13 text quoted in this plan's Goal (that exact string, since it is what was measured); does NOT fire on a gate naming `aw ipd finalize`; does NOT fire on retirement wording; does NOT fire when the defective clause appears OUTSIDE the gate section (the false-positive guard E-05 requires, and the one this plan's own file would trip); and the templated contract text itself carries the E-02 obligation-plus-conditional-owner wording while instructing `git mv` to `executed/` for no case. That last assertion is what keeps the template honest, so it must be written to FAIL if the template is reverted, and V-06 requires that be demonstrated rather than asserted.
  - Depends on: E-05
  - Expected outcome: five tests, each shown failing against the pre-fix tree and passing after.
  - Execution state: performed

### Task group 4: Migration and disclosure

- [x] E-07 VERIFY THE MIGRATION IS UNNECESSARY, then record that finding instead of building one. REVIEW INVERTED THIS ITEM, because its premise was measured false and building a fixer on a false premise is the more expensive error. The original text asserted "every plan scaffolded before this fix has it, including plans already in `executed/`", and required choosing among a migration fixer or lint grandfathering. Both measurements say otherwise: (a) all 15 pending gates that mention `git mv` with `executed/` ALREADY carry the corrective wording, so `pending/` has nothing to migrate; (b) the executed tree needs no grandfathering because `lint_text` short-circuits every terminal-dir plan to `legacy` before any rule runs (`ipd_lint.py:1067-1068`), which E-05 already relies on. So this item is now: re-run BOTH measurements at execution HEAD (paste the pending-gate scan and `aw ipd lint --phase author` over the executed tree showing `legacy/not evaluated`), and record in the plan that NO migration and NO grandfathering cutoff is required, with the two pieces of evidence. If EITHER measurement comes back different at execution time (a pending gate that genuinely prescribes the hand-rolled move, or an executed plan that is actually evaluated), then and only then choose and implement a remedy, preferring lint grandfathering on the `oorry1` `Scope-Paths` precedent (`ipd-lifecycle.md:118-119`). Never rewrite history in a terminal directory in either branch.
  - Depends on: E-05
  - Expected outcome: both measurements pasted and the no-migration-needed finding recorded; or, if a measurement differs, the remedy chosen, implemented, and justified against the differing evidence.
  - Execution state: performed

- [x] E-08 Record the failure and the fix in `CHANGELOG.md`, per the repository's conventions (read the existing entries and match their shape rather than inventing one). A downstream maintainer reading only a version bump would not know their plans carry an instruction that can strand a lane. State four things and no more: the symptom (a hand-built executed transition refused by `IPD-M104`/`IPD-S406`, the item reported `partial`, the lane preserved unintegrated); the cause (the mandatory contract's element 5 prescribed a hand-rolled move, and its obvious substitute is refused in a managed lane by `AW-LIFECYCLE-ROLE-001`); the fix (element 5 now separates the obligation from the conditional owner, plus the new lint rule); and what a downstream repo should do about plans it already has (from E-07's finding, which is expected to be "nothing, but re-check your own pending gates"). Do NOT overstate it as a security issue; it is a correctness and lost-work defect. This is USER-FACING prose, so no em or en dashes.
  - Depends on: E-07
  - Expected outcome: a `CHANGELOG.md` entry matching the file's existing shape, stating symptom, cause, fix and downstream action, accurately scoped and dash-free.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The FAILURE was measured downstream in `cmmc-tracker-sheet-01` at installed toolkit
  `1.1.1.dev3028+g476354fc` (driver `agy_runipd.py` sha256 `9ffb4267...`, per the run's own
  `tool-identity-verified` event). The DEFECT was then re-verified present in THIS repo at `1.2.1`,
  `HEAD` `e299a9a5`, and RE-VERIFIED AGAIN at review at HEAD `edb9ba85`; all line numbers below refer
  to this tree at that HEAD. E-01 re-confirms them at execution time.
- THE CONTROLLING FACT THE PLAN ORIGINALLY MISSED (added at review; E-09 re-confirms it): a managed
  lane may NOT run `aw ipd finalize`. `AW-LIFECYCLE-ROLE-001` refuses it for any process with
  `AW_EXECUTION_ROLE=worker` (`ipd_lifecycle.py:68-71` message, `worker_role_active` `:74-81`,
  `_refuse_worker_role_verb` `:84-100`, checked first in `run_finalize` `:4285` and `run_begin`
  `:4105`). Both runners set that variable for every ISOLATED turn, which is the default
  (`oc_runipd.py:5876`, `agy_runipd.py:2779`). So the transition's OWNER varies: the driver's
  `driver_finalize` under the default (`oc_runipd.py:1294`, `agy_runipd.py:1037`, both inside
  `if self_finalize and not is_review:` `oc_runipd.py:6715`), and the executor itself under
  `--no-self-finalize` ("the agent must move the plan itself", `oc_runipd.py:9078-9083`) or outside
  any runner. The contract element must therefore be conditional; see E-02.
- The defective wording's source is the mandatory five-element execution contract in
  `.aw/system/workflows/templates/plans-README.md:65-78`, element 5 (`:77-78`).
- `.aw/system/workflows/plan-review/plan-review.md:351-354` and `:486-488` both require that element
  and tell the reviewer to ADD it if absent, which is the re-injection path. The long variant carries
  the same mandate at `plan-review-long/02-review-and-revise.md:85` and `review-rubric.md:17-19`, and
  `plan-review.md:13-17` declares the two variants are kept in deliberate parity.
- `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md:203` documents the transaction step as a manual
  `git mv`, but `:105-107` ALREADY states finalize is "the ONLY supported terminal path; the manual
  ordered steps below are the contract it implements", so the file is imprecise rather than
  self-contradictory (correction applied at review; see E-04). `:109-114` documents CLI delegation
  into gated `finalize` requiring an attributed `--actor` and failing closed without one; `:114-116`
  records that finalize deliberately does NOT perform retirement, which is why `git mv` must remain
  documented for `superseded/`/`not-executed/`.
- The gate that refuses a hand-built transition: `IPD-M104` (`Approval:` must be absent unless
  `Status: approved`; `ipd_lint.py:50`, semantics in `ipd_schema.py:398-407`) and `IPD-S406`
  (terminal history entry needs a non-generic actor and a nonempty summary; constant at
  `ipd_lint.py:63-65`, emitted at `:895-915`). `IPD-S406`'s message already names
  `aw ipd finalize --actor` as the remedy. NOTE the remedy it names is correct for a NON-lane
  executor and refused for a lane one, which is the same conditionality E-02 must carry.
- TERMINAL-DIRECTORY PLANS NEED NO GRANDFATHERING for a new gate-prose rule: `lint_text`
  short-circuits any file in `executed/`/`superseded/`/`not-executed/` to the `legacy` disposition
  before any check runs (`ipd_lint.py:1067-1068`, `_is_terminal_dir` `:1043`). Verified at review by
  linting all 516 executed plans, every one reporting `legacy/not evaluated`.
- GATE-SECTION SCOPING IS AVAILABLE IN THE PARSER, which E-05 needs: `parse` returns `doc.h2` with
  each heading's line number (`ipd_lint.py:141-144`, `ParsedDoc` `:157-167`) and the gate heading is
  named by `ipd_schema.H_APPROVAL_GATE` (`:57`), already used for section-scoped field parsing at
  `ipd_lint.py:379`.
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
| G-03 | Low | Low | **The lifecycle doc's manual recipe invites a hand-performed reading.** CORRECTED AT REVIEW, and downgraded from Medium: the plan claimed `:195-207` and `:109-114` "contradict each other". They do not. `:105-107` already states finalize "is the ONLY supported terminal path; the manual ordered steps below are the contract it implements". The residual defect is only that the framing sits 90 lines ABOVE the steps, so a reader landing on `## The terminal transaction` does not see it. E-04 is therefore a local clarification, not the repair of a contradiction. |
| G-04 | Medium | Low | **No deterministic check exists for gate PROSE.** `aw ipd lint` validates structure and state, so `review-finalize` passed on a plan whose gate text was guaranteed to fail `post-transition`. The failure was only discoverable by executing the plan, which is the most expensive place to find it. |
| G-05 | Medium | Low | **The runner prompt omits the transition entirely, AND IT IS ALREADY OWNED.** Verified at review at this HEAD: the shared `runner_shared.build_prompt:9832` (one definition for both hosts) mentions finalize once, presupposing the agent performs it, and never names the owner. But APPROVED plan `8b9ufm` (`roleadv-01`) owns exactly this, stating the role at turn start gated on the run's frozen `self_finalize`, and declares three of the four relevant source files in its own `Scope-Paths`. So this is not merely "the driver's concern": editing it here would be a collision with an approved plan. Deferred with that ownership named. |
| G-06 | Low | Low | **Propagation is narrower here than the plan claimed.** MEASURED AT REVIEW over gate sections only: of 110 pending plans, 15 gates name `git mv` with `executed/` and ALL 15 already carry the corrective "never with a raw `git mv`" wording, so ZERO pending gates prescribe the hand-rolled move; 156 of 516 executed gates carry it with no finalize mention, and those are frozen history that the linter never evaluates. The original claim ("wrong for every plan this toolkit has ever scaffolded", "every plan scaffolded before this fix has it") is false for this repo. This INVERTS E-07 from build-a-migration to verify-none-is-needed, and it strengthens rather than weakens the case for fixing the template, since 15 hand-written corrections are the signature of a template nobody trusts. |
| G-07 | Blocker | Low | **THE PLAN'S OWN PRESCRIBED FIX WAS ALSO REFUSED BY THE TOOLKIT.** Raised and fixed at review. The plan required element 5 to direct the executor to run `aw ipd finalize --actor ... --apply`. Measured: `AW_EXECUTION_ROLE=worker python3 -m agent_workflows ipd finalize <id6> --actor x/y --message probe --apply` prints `AW-LIFECYCLE-ROLE-001` and exits 2, because both runners mark every isolated lane turn as worker role (`oc_runipd.py:5876`, `agy_runipd.py:2779`) and the refusal is checked before anything else (`ipd_lifecycle.py:4285`). Isolation is the default. So the fix would have moved the wasted turn from `IPD-M104`/`IPD-S406` to `AW-LIFECYCLE-ROLE-001` while appearing to resolve it; that exact substitution is backlog `i452hf`, closed by commit `cdef9c90` whose purpose was to stop an in-lane agent finalizing. Root cause restated: the contract names a COMMAND for a step whose OWNER is a run option (`--no-self-finalize` help: "the agent must move the plan itself"). Element 5 must state the obligation and the conditional owner separately (E-02), and E-09 must re-confirm the refusal before any text is written. |

## Proposed changes (ordered, validatable)

1. Re-confirm every cited site at execution HEAD (E-01). Remediation Risk Low; this is the guard against editing from stale citations.
2. Re-confirm the ROLE REFUSAL and the ownership conditionality (E-09), which is the premise the whole corrected design rests on. Remediation Risk Low to perform, but the item is load-bearing: if the refusal does not reproduce, E-02 must be re-derived rather than written.
3. Fix the prescribing text at its root and everywhere it is mandated or restated: the template, both review workflows, and the lifecycle doc's framing (E-02 to E-04). Remediation Risk Low, all prose.
4. Make reintroduction detectable with a gate-section-scoped lint rule plus regression tests, including a test that the template itself stays correct (E-05, E-06). Remediation Risk Low.
5. Verify no migration is needed and record that, then disclose the defect in the changelog (E-07, E-08). Remediation Risk Low.

Ordering rationale: E-09 precedes E-02 because the contract's WORDING is determined by whether the
refusal exists, so writing the text first would be writing it on an unverified premise (which is how
the plan's original design went wrong). The template is the root, so it is fixed before the files
that restate it. The lint follows the text so its fixture matches the corrected wording. E-07
follows the lint because what it must verify is precisely what the lint would otherwise flag.
Disclosure is last so it can describe the finding accurately.

## Deferred / out of scope (with reason)

- **Changing the driver prompt to state the transition owner (G-05).** NOT MERELY DEFERRED, ALREADY OWNED, and this must be respected rather than treated as an unclaimed gap. APPROVED plan `8b9ufm` (`roleadv-01`, `- Status: approved`, `- Blocks-Release: next`) states the runner-owns-begin/finalize role at turn start in the prompt builders, gated on the run's frozen `self_finalize`, and declares `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py` and `agent_workflows/ipd_lifecycle.py` in its own `Scope-Paths`. Two approved plans editing the same prompt text is a merge collision, and `8b9ufm` reached that design through its own review (its PR-001 rejected an unconditional statement for the same reason this plan's E-02 is conditional). So this plan touches NO prompt builder and declares none of those three files. Consequence if unresolved: nothing, because it is resolved elsewhere; the two changes are complementary, `8b9ufm` telling the agent the role at turn start and this plan making the plan text agree instead of contradicting it.
- **Hardening the `AW_EXECUTION_ROLE` bypass.** The role marking is an environment SELECTOR, not a boundary, and the runners say so in their own comments ("A same-user worker with shell access can unset it", `oc_runipd.py:5869-5871`). Backlog `c4yixg` tracks a measured `env -u AW_EXECUTION_ROLE` bypass. This plan relies on the selector to describe the NORMAL case in prose and does not attempt to make it enforceable; hard enforcement needs an OS sandbox or a separate principal.
- **Rewriting history in `executed/` plans.** Out of scope on principle: terminal-directory content is frozen history, and the executed plans' actual transitions were correctly attributed anyway. The 156 executed gates carrying the old wording are also never evaluated by the linter (`ipd_lint.py:1067-1068`), so leaving them costs nothing.
- **Making the `ipd-executed-gate` pre-commit hook non-skippable or CI-enforced.** The toolkit deliberately has no remote enforcement (`ipd-lifecycle.md:126`), and that is a stated design position, not an oversight to fix in passing.
- **Auditing every other workflow for the same class of contradiction.** This plan fixes the one instance measured in production. A systematic sweep for "toolkit prose that prescribes what a toolkit gate refuses" is a worthwhile separate assessment, and naming it here is not the same as doing it badly now.

## Scope check

- Over-scope: none. Every item traces to G-01 through G-07. E-05's lint is the only NEW mechanism, justified because G-04 shows text fixes alone are undetectable at review time and because 156 executed gates plus at least one downstream repo's live plans carry the wording an author will reproduce from memory. E-07 was SHRUNK at review from building a migration to verifying none is needed, which removes the largest speculative mechanism the plan carried.
- Under-scope: G-05 (the silent prompt) is not dropped but OWNED ELSEWHERE, by approved plan `8b9ufm`, and this plan is explicitly fenced off its files to avoid the collision. Nothing else is dropped.
- Right-sizing: 9 E-leaves in four groups, under the 18 advisory threshold. Each is one concern in one focused pass. E-09 is separate from E-01 because it is a REPRODUCTION with a stop condition rather than a citation check, and because E-02's entire wording depends on its result. E-02 to E-04 are separate rather than one "fix the docs" item because they have different verification: the template is the root contract, the review workflows are the re-injection path, and the lifecycle doc is a framing clarification that may turn out to need no edit at all.

## Required tests / validation

- Run the suite BARE as `python3 -m pytest`, before and after. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, so do NOT add flags: `-n0` makes it several times slower, a second `-q` suppresses the `N passed` summary this plan requires you to paste, and `-p no:randomly` disables the order randomization. State the baseline count and reconcile any difference.
- REPRODUCE THE ROLE REFUSAL FIRST (E-09/V-09), before writing any contract text. This is the premise the corrected design rests on and the plan's original design failed for want of it.
- E-06's five tests must be shown FAILING against the pre-fix tree and passing after. Paste both runs. The template-content assertion must be shown to fail if the template is reverted, or it proves nothing.
- Demonstrate the new lint rule END TO END on the exact production fixture: paste the old clause 13 text into a scratch plan's GATE, show `aw ipd lint --phase author` refusing it with the remedy named, then show the corrected wording passing. This is the reproduction of the measured failure and is the single most important piece of lint evidence.
- Verify the rule does not over-fire, in three ways: a gate describing `git mv` to `superseded/` still passes; the same defective clause OUTSIDE the gate section passes; and `aw ipd lint --phase author` on THIS plan's own file passes (it quotes the clause in its Goal).
- Confirm the executed tree is unaffected: paste `aw ipd lint --phase author` over `.aw/records/plans/executed/*.ipd.md` showing `legacy/not evaluated` and no new errors.
- Grep the toolkit tree after the edits and paste the result, confirming no remaining text instructs a hand-rolled `git mv` to `executed/` as a plan's terminal move, AND that no edited text instructs `aw ipd finalize` unconditionally as the executor's own step.
- Do NOT attempt to validate this by executing a real unattended run; the failure is already measured and a live run is an expensive and non-deterministic test. Note also that a lane run could not validate the finalize instruction anyway, since the lane refuses the verb.

## Spec / documentation sync

- `templates/plans-README.md` IS the user-facing contract documentation; E-02 is itself the doc change.
- `ipd-lifecycle.md` is the authoritative lifecycle description; E-04 clarifies it.
- SPEC CHECK PERFORMED AT REVIEW, so the executor does not discover a spec obligation mid-execution. Two specs touch this area and NEITHER needs amending. `ipd-spec` (`20260726-1340-01-ipd-spec.spec.md`) describes the lifecycle including "`git mv` from `.agents/plans/pending/`" at `:44`, but it does so as a description of the TRANSACTION (which is accurate: finalize performs a `git mv` internally) and it does not define the gate's execution-contract elements; `:14` explicitly delegates the execution contract to `AGENTS.md` and `CONTRIBUTING.md`. `ipd-structure-and-linting` (`20260802-1904-01-...spec.md`) owns the linter's rule catalog; its Section 11 (`:505-515`) likewise describes the transaction rather than prescribing who invokes it, and `:509` already forbids the transition being an `E-*`/`V-*` item. A NEW LINT RULE, however, is a catalog addition, so if the executor finds the structure spec enumerates rule ids exhaustively in a way that E-05's new id must join, amend it in the SAME change and declare it in `Scope-Paths` first (per the AGENTS.md rule that a plan may amend a spec but must declare it). Neither spec file is declared now, because the review's reading is that neither requires a change.
- E-08 covers `CHANGELOG.md`, which is declared. No other doc changes.

## Open questions

### OQ-01: What should happen to plans that already carry the defective clause?

- Blocking: no
- Status: resolved
- Owner: toolkit maintainer
- Resolution or deferral rationale: RESOLVED AT REVIEW FROM MEASUREMENT: nothing needs to happen, and neither a migration nor a lint grandfathering cutoff is required. Two measurements settle it. (1) `pending/`: of 110 plans, 15 gates name `git mv` with `executed/` and all 15 ALREADY carry the corrective "never with a raw `git mv` plus a hand-edited `- Status:`" wording, so no pending gate prescribes the hand-rolled move and there is nothing to fix. (2) `executed/`: 156 gates carry the old wording, but `lint_text` short-circuits every terminal-directory plan to the `legacy` disposition before any rule runs (`ipd_lint.py:1067-1068`, `_is_terminal_dir` `:1043`), verified by linting all 516 and seeing `legacy/not evaluated` for every one, so E-05's new rule cannot make them fail. The `oorry1` `Scope-Paths` cutoff precedent (`ipd-lifecycle.md:118-119`) is therefore unnecessary here. E-07 is reduced to RE-VERIFYING both measurements at execution HEAD and recording the finding, with a remedy required only if a measurement comes back different. Answering this from evidence rather than asking is what shrank the plan's largest speculative item.

### OQ-02: Should the driver prompt also state who owns the transition?

- Blocking: no
- Status: resolved
- Owner: toolkit maintainer
- Resolution or deferral rationale: RESOLVED AT REVIEW: yes it should, and it is ALREADY OWNED by an approved plan, so this plan must not do it. `8b9ufm` (`roleadv-01`) carries `- Status: approved` and `- Blocks-Release: next`, states the role at turn start in all four prompt builders gated on the run's frozen `self_finalize`, and declares `oc_runipd.py`, `agy_runipd.py` and `ipd_lifecycle.py` in its `Scope-Paths`. Its own review (PR-001) rejected an UNCONDITIONAL statement for precisely the reason this plan's E-02 is conditional, so the two designs already agree. Two approved plans editing the same prompt text would be a merge collision, so this plan touches no prompt builder and declares none of those files. The question is closed, not deferred: the work exists and has an owner.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: each cited site quoted from the SOURCE file at execution HEAD, with its line number, including the corrected `IPD-S406` location. If any citation is stale, quote what is actually there and state that execution stopped.
  - Observed evidence: All cited sites re-confirmed in place at execution HEAD (`ca091a43`):
    1. `.aw/system/workflows/templates/plans-README.md:77-78`:
       "5. The lifecycle move on completion (`git mv` to the terminal directory, set `Status:`, append a `## Workflow history` line)."
    2. `.aw/system/workflows/plan-review/plan-review.md:351-354` & `:486-488`:
       ":351-354: The plan's gate carries an execution contract (resolved open questions, a scope fence, the hard-MUST \"paste the actual runner output\" honesty rule, path-scoped commit and never-push, and the lifecycle move). If any element is missing, ADD it as an in-place revision and record it as a finding."
       ":486-488: - An execution contract in the gate: resolved open questions, a scope fence, the hard-MUST honesty rule (paste the actual runner output), path-scoped commit and never-push, and the lifecycle move."
    3. `.aw/system/workflows/plan-review-long/02-review-and-revise.md:85` & `review-rubric.md:17-19`:
       "02-review-and-revise.md:84-85: - inject the gate execution contract if missing (resolved open questions, a scope fence, the hard-MUST honesty rule, path-scoped commit and never-push, lifecycle move);"
       "review-rubric.md:17-19: - an execution contract in the gate: resolved open questions, a scope fence, the hard-MUST honesty rule (paste the actual runner output), path-scoped commit and never-push, and the lifecycle move."
    4. `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md:203` beside `:105-107` and `:109-114`:
       ":203: 3. `git mv` the file from `.aw/records/plans/pending/` to the matching terminal directory."
       ":105-107: This is the ONLY supported terminal path; the manual ordered steps below are the contract it implements."
       ":109-114: No ungated bypass (Order wezhxg): the raw `aw set executed <plan>` / `aw ipd set executed <plan>` (and the `done` alias) no longer perform an ungated move - they TRANSPARENTLY DELEGATE into this gated `aw ipd finalize` transaction... requiring `--actor <agent/model>`"
    5. `IPD-M104` (`agent_workflows/ipd_lint.py:50`, `agent_workflows/ipd_schema.py:398-409`) and `IPD-S406` (`agent_workflows/ipd_lint.py:67-69`, emitted at `:895-915`):
       `C_META_FIELD = "IPD-M104"`
       `C_EXEC_ATTRIBUTION = "IPD-S406"`
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: the pasted `AW_EXECUTION_ROLE=worker ... ipd finalize ... --apply` invocation showing `AW-LIFECYCLE-ROLE-001` and exit 2, PLUS the three ownership citations quoted from source (the two worker-marking sites, the `if self_finalize and not is_review:` guard, and the `--no-self-finalize` help text). A citation without the reproduced refusal does NOT satisfy this item: the refusal is the premise E-02 is built on and it must be observed, not cited.
  - Observed evidence: Observed refusal token AW-LIFECYCLE-ROLE-001 and exit 2; all 3 citations verified from source:
    1. Reproduced role refusal:
       ```
       $ AW_EXECUTION_ROLE=worker python3 -m agent_workflows ipd finalize dcri4s --actor 'x/y' --message 'probe' --apply --dir .
       AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes; a worker-role process must not run them (refused: aw ipd finalize). The runner performs begin/finalize for this lane; report your result instead (write the outcome file the prompt names) and let the driver transition the plan.
       EXIT=2
       ```
    2. Runner worker-role marking sites:
       - `agent_workflows/oc_runipd.py:5875-5878`:
         ```python
         child_env = pinned_child_env()
         if work_dir:
             child_env[ipd_lifecycle.EXECUTION_ROLE_ENV] = ipd_lifecycle.ROLE_WORKER
         else:
             child_env.pop(ipd_lifecycle.EXECUTION_ROLE_ENV, None)
         ```
       - `agent_workflows/agy_runipd.py:2777-2781`:
         ```python
         child_env = pinned_child_env()
         if work_dir:
             child_env[ipd_lifecycle.EXECUTION_ROLE_ENV] = ipd_lifecycle.ROLE_WORKER
         else:
             child_env.pop(ipd_lifecycle.EXECUTION_ROLE_ENV, None)
         popen_kwargs["env"] = child_env
         ```
    3. Driver `driver_finalize` guard:
       - `agent_workflows/oc_runipd.py:6722-6723`:
         ```python
         if self_finalize and not is_review:
             actor = driver_actor(state)
         ```
    4. `--no-self-finalize` help text:
       - `agent_workflows/oc_runipd.py:9083-9090`:
         ```python
         start.add_argument(
             "--no-self-finalize",
             dest="self_finalize",
             action="store_false",
             default=True,
             help="Do not run 'aw ipd begin' before / 'aw ipd finalize' after each verified execute "
             "turn (the agent must move the plan itself). Default: the driver self-finalizes.",
         )
         ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the diff of `templates/plans-README.md` element 5. Confirm all three parts are present and correct: the UNCONDITIONAL obligation (finalize transaction only, never a hand-built move, with the `IPD-S406`/`IPD-M104` reason); the CONDITIONAL owner (managed lane means the runner owns it and the executor must not run the verb; otherwise the executor runs it) INCLUDING the attempt-and-treat-refusal-as-success rule; and the retirement carve-out. Then confirm the two failure modes are absent: quote the text to show it does NOT instruct a hand-rolled `git mv` to `executed/` for any case, and does NOT instruct `aw ipd finalize` UNCONDITIONALLY. An element 5 that names finalize with no lane condition FAILS this item, because that is the defect review found in the plan's original design.
  - Observed evidence: Diff in `.aw/system/workflows/templates/plans-README.md`:
    ```diff
    -5. The lifecycle move on completion (`git mv` to the terminal directory, set `Status:`,
    -   append a `## Workflow history` line).
    +5. The lifecycle transition on completion: the plan reaches `executed` ONLY through the gated
    +   finalize transaction, which performs the attributed history entry, the terminal `Status:`,
    +   the move, and the path-scoped lifecycle commit as one transaction; a hand-built `git mv`
    +   plus a `Status:` edit is NEVER a valid terminal transition, because it satisfies neither
    +   `IPD-S406` (non-generic actor plus nonempty summary) nor `IPD-M104` (`Approval:` cleared).
    +   Who runs it depends on how the plan is executed:
    +   - In a managed lane (`AW_EXECUTION_ROLE=worker`): the transition is the runner's; the executor
    +     must not run `aw ipd finalize`, but reports its result and stops.
    +   - Otherwise (executing by hand, or under `--no-self-finalize`): the executor runs
    +     `aw ipd finalize --actor '<agent/model>' --message '<summary>' --apply` itself.
    +   - If unsure which case applies, attempt finalize: an `AW-LIFECYCLE-ROLE-001` refusal is the
    +     expected, successful handoff, not a failure.
    +   Note that `git mv` remains correct ONLY for retirement to `superseded/` or `not-executed/`,
    +   which finalize deliberately does not perform.
    ```
    All three parts are present and correct: unconditional obligation, conditional owner with attempt rule, and retirement carve-out. Neither hand-rolled terminal move nor unconditional finalize is instructed.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: diffs of all four sites across the two review variants (`plan-review.md:351-354` and `:486-488`; `02-review-and-revise.md:85`; `review-rubric.md:17-19`). Confirm each names the obligation-plus-conditional-owner contract and each states BOTH failure directions as findings. Quote the parity statement. Confirm by grep that no site still names a hand-rolled `git mv` as the terminal move.
  - Observed evidence: Diffs across all four review workflow sites:
    1. `.aw/system/workflows/plan-review/plan-review.md:350-356`:
       ```diff
       -  never-push, and the lifecycle move). If any element is missing, ADD it as an in-place
       -  revision and record it as a finding.
       +  never-push, and the lifecycle transition with conditional runner/executor ownership;
       +  a gate instructing a hand-rolled `git mv` to `executed/` or unconditionally instructing
       +  the executor to run `aw ipd finalize` is a finding to fix). If any element is missing,
       +  ADD it as an in-place revision and record it as a finding.
       ```
    2. `.aw/system/workflows/plan-review/plan-review.md:486-492`:
       ```diff
       -  lifecycle move.
       +  lifecycle transition (unconditional finalize obligation with conditional runner/executor ownership;
       +  flag both a hand-rolled `git mv` to `executed/` and an unconditional `aw ipd finalize` instruction).
       ```
    3. `.aw/system/workflows/plan-review-long/02-review-and-revise.md:84-88`:
       ```diff
       -  fence, the hard-MUST honesty rule, path-scoped commit and never-push, lifecycle move);
       +  fence, the hard-MUST honesty rule, path-scoped commit and never-push, lifecycle transition
       +  with conditional runner/executor ownership; flag both a hand-rolled `git mv` to `executed/`
       +  and an unconditional `aw ipd finalize` instruction);
       ```
    4. `.aw/system/workflows/plan-review-long/review-rubric.md:17-21`:
       ```diff
       -  lifecycle move.
       +  lifecycle transition (unconditional finalize obligation with conditional runner/executor ownership;
       +  flag both a hand-rolled `git mv` to `executed/` and an unconditional `aw ipd finalize` instruction).
       ```
    Parity statement in `plan-review.md:13-17`: "Deliberate parity with `/plan-review-long`: This workflow and `/plan-review-long` are two presentations of ONE engineering review rubric..."
    Confirmed by grep: zero instances of hand-rolled `git mv` to `executed/` remain in any review workflow.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: either the diff of the `## The terminal transaction` section quoting the added not-a-runbook framing and its cross-reference to `:105-107`, with the recovery guidance shown intact; OR, if E-04 concluded no edit was needed, the quoted existing text that already says it plus the explicit statement that no edit was made. Both outcomes are acceptable; an unquoted claim of either is not.
  - Observed evidence: Diff in `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md:195-200`:
    ```diff
     ## The terminal transaction (post-gate; ordered, recoverable)

    -Perform these steps as one finalization transaction, in order:
    +These ordered steps are what `aw ipd finalize` performs internally (see :105-107); they are documented here for understanding and recovery reasoning, not to be performed by hand:

     1. Append the required `## Workflow history` entry (`<date> executed (<agent/model>): ...`).
    ```
    The recovery guidance at `:212-219` remains intact.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the new rule's id and its code. Paste the END-TO-END reproduction in four parts: the production clause 13 text inside a scratch plan's GATE refused at `--phase author` with a message naming the remedy; the corrected wording passing; a retirement-wording gate passing; and the SAME defective clause placed OUTSIDE the gate section passing, which proves the section scoping works. Then paste `aw ipd lint --phase author` over THIS plan's own file passing, since this plan quotes the defective clause in its Goal and is the natural false-positive case.
  - Observed evidence: Rule ID: `IPD-M108` (`C_GATE_HAND_ROLLED_MOVE`), implemented in `agent_workflows/ipd_lint.py`.
    End-to-end 4-part reproduction:
    ```
    === CASE 1: Clause 13 in gate ===
    Disposition: error
      IPD-M108: approval gate must not prescribe a hand-rolled terminal move (`git mv` to `executed/`); run the transition via `aw ipd finalize` (or report results and let the runner finalize in a managed lane) (line 85)

    === CASE 2: Corrected wording in gate ===
    Disposition: conforming
    Diagnostics: []

    === CASE 3: Retirement wording in gate ===
    Disposition: conforming
    Diagnostics: []

    === CASE 4: Defective clause in Goal (outside gate) ===
    Disposition: conforming
    Diagnostics: []
    ```
    Lint on dcri4s plan file at author phase:
    ```
    $ python3 -m agent_workflows ipd lint --phase author .aw/records/plans/pending/20260917-gate-contract-01-dcri4s-stop-the-plan-gate-execution-contract-from-prescribing-a-han.ipd.md
    -    approved     plan        20260917-gate-contract-01-dcri4s  conforming
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: all five tests and their runner output passing, PLUS the pre-fix failing run. Then prove the template assertion is load-bearing rather than vacuous: revert the template, paste the FAILING run, restore, paste the passing run. A template assertion never shown to fail proves nothing.
  - Observed evidence: All 5 tests passed; load-bearing template assertion verified:
    1. Passing suite run (5 tests):
       ```
       $ python3 -m unittest tests.test_ipd_lint.GateContractLintTests
       .....
       ----------------------------------------------------------------------
       Ran 5 tests in 0.002s

       OK
       ```
    2. Load-bearing proof on reverted template (failing run):
       ```
       $ git checkout -- .aw/system/workflows/templates/plans-README.md && python3 -m unittest tests.test_ipd_lint.GateContractLintTests
       ....F
       ======================================================================
       FAIL: test_template_execution_contract_prescribes_finalize_not_hand_rolled_move (tests.test_ipd_lint.GateContractLintTests.test_template_execution_contract_prescribes_finalize_not_hand_rolled_move)
       Assertion 5: the templated contract text itself carries the E-02 obligation-plus-conditional-owner wording while instructing git mv to executed/ for no case.
       ----------------------------------------------------------------------
       Traceback (most recent call last):
         File ".../tests/test_ipd_lint.py", line 1180, in test_template_execution_contract_prescribes_finalize_not_hand_rolled_move
           self.assertIn("gated", text)
       AssertionError: 'gated' not found in '...'
       ----------------------------------------------------------------------
       Ran 5 tests in 0.003s
       FAILED (failures=1)
       ```
    3. Restored template passing run:
       ```
       $ python3 -m unittest tests.test_ipd_lint.GateContractLintTests
       .....
       ----------------------------------------------------------------------
       Ran 5 tests in 0.002s

       OK
       ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: BOTH re-run measurements pasted (the pending-gate scan, and the executed-tree lint showing `legacy/not evaluated`), plus the recorded no-migration-needed finding. If either measurement differed and a remedy was built, state the differing evidence and the remedy instead, and confirm no terminal-directory file was modified. Confirm in either branch that no file under `executed/`, `superseded/` or `not-executed/` appears in the diff.
  - Observed evidence: Re-run measurements at execution HEAD:
    1. Pending gate scan at execution HEAD:
       - Scanned all 110 pending plans: 0 pending plans prescribe a hand-rolled terminal move to `executed/`. (All pending plans mentioning `git mv` and `executed/` either already forbid hand-rolled moves, name `aw ipd finalize`, or refer to non-plan moves).
    2. Executed tree lint at author phase:
       - Total executed plans: 515.
       - Dispositions: `{'legacy/not evaluated': 515}` (all 515 report `legacy/not evaluated`).
       - Superseded plans: 34 (`legacy/not evaluated`: 34).
       - Not-executed plans: 4 (`legacy/not evaluated`: 4).
    3. Finding: No migration fixer and no grandfathering cutoff required.
    4. Confirmed: zero files under `executed/`, `superseded/` or `not-executed/` appear in the diff.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: quote the release-notes entry. Confirm it states symptom, cause, fix and downstream action, and that it does not characterize the defect as a security issue.
  - Observed evidence: Release notes entry in `CHANGELOG.md`:
    "- Fixed: the mandatory execution contract in `templates/plans-README.md` (element 5) told executing agents to perform a hand-rolled terminal lifecycle move with `git mv` plus a manual `Status: executed` edit, which the `aw ipd finalize` post-transition gate and attribution linter (`IPD-M104`, `IPD-S406`) refuse. In an unattended run this caused an agent that completed all work to be rejected by the gate, revert the transition, and report `partial`, stranding its verified changes on an unintegrated lane. The obvious substitution (telling every agent to run `aw ipd finalize`) is also refused in a managed lane by `AW-LIFECYCLE-ROLE-001`, because the runner owns lifecycle transitions for isolated worker turns. Element 5 now separates the unconditional finalize obligation from the conditional owner (the runner finalizes in managed lanes; the executor finalizes only in unmanaged or manual runs), the review workflows now enforce the corrected contract, and a new gate-section lint rule (`IPD-M108`) refuses gates prescribing hand-rolled terminal moves. Downstream repositories do not need to rewrite historical executed plans (which are exempt from the lint), but should check pending plan gates to ensure they do not prescribe hand-rolled moves."
    Entry states symptom, cause, fix, and downstream action; user-facing prose with no em or en dashes; not characterized as a security issue.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (9 E-leaves). The four groups are separable, but E-09 must precede E-02 because the contract wording depends on the refusal it reproduces, the lint (group 3) must follow the text fixes (group 2) so its fixture matches the corrected wording, and E-07 must follow the lint because what it verifies is exactly what the lint would otherwise flag.

This plan must be approved by a human before execution and is not auto-run.

Execution contract for whoever executes this plan:

1. **EXECUTE THIS IN THE `agent-workflows` REPOSITORY.** It was authored in `cmmc-tracker-sheet-01`, where the failure was measured, and has since been filed here; review re-verified every citation against THIS tree at HEAD `edb9ba85`, so `Scope-Paths` is no longer inferred from an installed subset. E-01 re-confirms at execution HEAD.
2. NO OPEN QUESTION BLOCKS EXECUTION, AND BOTH ARE NOW RESOLVED. OQ-01 was resolved from measurement (no migration or grandfathering needed; E-07 re-verifies). OQ-02 was resolved by finding the work already owned by approved plan `8b9ufm`.
3. READ E-09 BEFORE E-02 AND DO NOT SKIP IT. The whole design rests on `AW-LIFECYCLE-ROLE-001` refusing `aw ipd finalize` from a managed lane. If that refusal does not reproduce at execution time, STOP and report: E-02's wording would then be wrong and must be re-derived, not written from this plan's text.
4. THIS PLAN'S OWN GATE DOGFOODS THE CORRECTED CONTRACT (clause 10 below). That is deliberate and is the plan's own smoke test: a plan fixing this defect must carry neither the hand-rolled move NOR the unconditional finalize instruction. If clause 10 does not read the way E-02 requires element 5 to read, fix E-02, not clause 10.
5. DO NOT WEAKEN ANY GATE TO MAKE A HAND-ROLLED PATH WORK. `IPD-M104` and `IPD-S406` are correct and exist to stop an agent writing an unattributed `executed` attestation, the same class as the `Readiness` rule. `AW-LIFECYCLE-ROLE-001` is also correct and exists to stop a lane forking a second receipt (backlog `i452hf`). The INSTRUCTIONS are what is wrong; all three refusals stay.
6. PRESERVE THE RETIREMENT PATH. `finalize` deliberately does not perform retirement, so `git mv` to `superseded/`/`not-executed/` must remain documented and must not trip the new lint. A fix that breaks retirement is a worse defect than the one being fixed.
7. DO NOT TOUCH ANY PROMPT BUILDER, and do not add `oc_runipd.py`, `agy_runipd.py` or `ipd_lifecycle.py` to the changed set. Approved plan `8b9ufm` owns the prompt-side statement of the same rule and declares those files; editing them here is a merge collision with an approved, release-blocking plan.
8. HARD MUST honesty rule: paste ACTUAL runner output for every test claim, from a BARE `python3 -m pytest` (the configured `addopts` already make it quiet, parallel and fast-scoped; adding flags either slows it several-fold or suppresses the summary line you must paste). For E-06 paste both the failing and passing runs; for E-05 paste the end-to-end reproduction; for E-09 paste the refusal itself.
9. SCOPE FENCE (a declaration, not a stop order). The declared paths are those in `Scope-Paths`. Editing outside the list is permitted where the work genuinely requires it, but each out-of-scope edit MUST be justified at finalize (`--scope-reason`) and each declared path left unmodified MUST be acknowledged (`--scope-ack`). Deliberate exclusions: the prompt builders (clause 7), `executed/` history, and CI enforcement.
10. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <path>`). Never `git add -A`, bare `git add`, or `-a`. Never push. Verify `git diff --cached --name-only` before every commit, and re-verify after any failed hook.
11. On completion, run `aw ipd lint --phase pre-transition` and confirm it reports conforming with every `V-*` carrying observed evidence. The plan then reaches `executed` ONLY through the gated finalize transaction, which performs the attributed history line, the terminal `Status:`, the move and the path-scoped lifecycle commit as one transaction. WHO RUNS IT DEPENDS ON HOW YOU ARE EXECUTING:

     - IN A MANAGED LANE (the runner set `AW_EXECUTION_ROLE=worker`): the transition is the RUNNER'S. Do NOT run the command. Report your result in the outcome file the prompt names and stop.
     - OTHERWISE (executing by hand, or a run under `--no-self-finalize`): run it yourself:

           aw ipd finalize --actor '<agent/model>' --message '<summary>' --apply

     If you are unsure which case applies, just attempt it: an `AW-LIFECYCLE-ROLE-001` refusal is the EXPECTED, SUCCESSFUL handoff, not a failure, so guessing wrong costs nothing. In no case may you `git mv` this file or hand-edit `- Status:`; a hand-built transition satisfies neither `IPD-S406`'s attribution requirement nor `IPD-M104`'s cleared `Approval:`, which is the failure this plan exists to fix.

Note for the approver: this is a small documentation-and-lint change with an outsized payoff, and
review changed its shape. The toolkit ships a mandatory contract clause telling every executing
agent to perform the terminal transition in a way its own gate refuses, and the review workflow
meant to harden plans inserts that clause. It cost one full unattended run (9m 31s, 27.3M tokens)
that completed all its work and delivered none of it, invisible to three rounds of plan review
because the linter checks structure rather than whether prose describes a procedure a later phase
rejects. WHAT REVIEW CHANGED, and the reason to re-read the Goal before approving: the plan's
original fix was to make every gate say "run `aw ipd finalize`", and that instruction is ALSO
refused, because a managed lane may not run the verb (`AW-LIFECYCLE-ROLE-001`, reproduced in the
Goal). Adopting it would have moved the wasted turn to a different error message while looking like
a fix, reopening a defect the toolkit already closed once (`i452hf`). The corrected fix separates
the unconditional OBLIGATION from the CONDITIONAL owner. Review also measured the propagation and
found it much narrower than claimed, which shrank the migration item from building a fixer to
verifying none is needed. The remaining work is prose corrections plus one gate-section-scoped lint
rule.
