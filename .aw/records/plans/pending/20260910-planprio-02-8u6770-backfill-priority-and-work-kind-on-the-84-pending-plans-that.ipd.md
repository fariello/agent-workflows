# IPD: Backfill Priority and Work-Kind on the 84 pending plans that can inherit from their source item

- Date: 2026-09-10
- Kind: child
- Concern: 84 of the 104 pending plans record the backlog item they graduated from, every one of those references resolves, and every source carries both `Priority` and `Work-Kind`. So 84 plans can be given both values with no judgement call, purely by inheriting from a source the plan itself names.
- Scope: Inherit `Priority` and `Work-Kind` from each pending plan's `- From-Backlog:` source, writing them through the shipped `aw ipd set` setters rather than by hand. Does NOT decide a value for any plan lacking a source (sibling 03 owns those), does NOT touch terminal plans, and does NOT change any vocabulary or add a sort key.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: executed:lkexaw
- Status: to-review
- Set: planprio
- Order: 2
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 8u6770

## Workflow history

- 2026-09-10 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored after the maintainer chose the full option ("enforce at the gate, fix creation, inherit the 84, decide the 20") on 2026-09-10, having asked whether fixing the pending corpus was worth it at all. IT IS WORTH IT PRECISELY BECAUSE MOST OF IT NEEDS NO JUDGEMENT, which is what the measurement showed. MEASURED AT AUTHORING over the 104 pending plans: 84 carry a `- From-Backlog:` id6, ZERO of those references dangle, and ZERO of the resolved sources are missing either field, so all 84 inherit cleanly. The inherited distribution is a real spread rather than a single default: 26 `high`/`bug`, 25 `medium`/`bug`, 11 `medium`/`feature`, 10 `high`/`feature`, 6 `medium`/`chore`, 3 `low`/`feature`, 1 each of `medium`/`followup`, `high`/`security`, `low`/`followup`. A SETTER ALREADY EXISTS AND MUST BE USED: `aw ipd set` carries `--priority` and `--work-kind`, both documented as persisting "on a no-op transition", so this backfill needs no hand-editing of front matter.

## Goal

Give 84 pending plans their two missing fields by inheritance, so the attention board's Priority column is populated for most of the queue without anyone guessing a value.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: derive, then verify, then write

- [ ] E-01 RE-DERIVE THE INHERITANCE TABLE AT EXECUTION TIME AND PRINT IT, one row per plan: the plan's id6, its `- From-Backlog:` source id6, the source's `Priority` and `Work-Kind`, and the source's own file path. DO NOT REUSE THIS PLAN'S COUNTS. The population moves as other agents graduate items and author plans, and the parent's E-01 exists to re-measure it; if the count is no longer 84, proceed with whatever the measurement says and record the difference.
  RESOLVE, DO NOT PARSE. A `- From-Backlog:` id6 must be resolved to an actual backlog file, exactly as `check.from-backlog-dangling` already does. A dangling reference must be REPORTED and SKIPPED, never guessed at, and never silently treated as a plan with no source (that would move it into sibling 03's population without anyone deciding to).
  - Depends on: none
  - Expected outcome: a printed per-plan table with the four values and the source path, the count stated, and any dangling reference named and excluded.
  - Execution state: pending

- [ ] E-02 SANITY-CHECK THE DERIVED VALUES BEFORE WRITING ANY, because inheritance is only as good as the sources. Report the distribution and inspect the tails: any source whose `Priority` is absent or outside `low|medium|high`, any whose `Work-Kind` is outside `bug|feature|chore|security|followup`, and any plan whose inherited `Priority` disagrees with its own `- Blocks-Release:` state in a way worth flagging (a release-blocking plan inheriting `low` is not necessarily wrong, but it should be SEEN rather than written silently).
  DO NOT CORRECT A SOURCE ITEM. If a source's value looks wrong, report it; editing backlog items is outside this plan's declared scope and belongs to whoever owns that item.
  - Depends on: E-01
  - Expected outcome: the distribution printed, every out-of-vocabulary or absent source value named, and every release-blocking plan inheriting `low` or `medium` listed for a human to see.
  - Execution state: pending

- [ ] E-03 WRITE THE VALUES THROUGH THE SHIPPED SETTER, one plan at a time, using `aw ipd set <current-status> <id6> --priority <p> --work-kind <k>`. Both flags are documented as persisting on a NO-OP transition, so a plan keeps its current status and only the two fields change; verify that on the first plan before doing the rest.
  DO NOT HAND-EDIT FRONT MATTER, and do not batch-rewrite with a script that writes the lines directly. The setter owns field position and history, and a direct write would bypass both. If the setter cannot express a case, report it rather than working around it.
  EXPECT AND HANDLE THE STATUS-TRANSITION GUARD: a no-op transition on some statuses may refuse or may require a message. Record exactly which invocation form worked, so the next agent doing a bulk field write has it.
  - Depends on: E-02
  - Expected outcome: every derived plan carries both fields with the inherited values; the exact working invocation is recorded; no plan's `- Status:` changed as a side effect.
  - Execution state: pending

- [ ] E-04 PROVE NOTHING ELSE MOVED, which matters because this plan edits 84 files in a shared checkout. Show that only the two field lines and each plan's history changed, that no plan's `Status`, `Readiness`, `Set`, `Order` or `Id` differs, and that `aw check plans` and `aw ipd lint` report no new finding class.
  RE-VERIFY THE INDEX BEFORE EACH COMMIT. Other agents are committing concurrently; `git diff --cached --name-only` must contain only plans this item changed, and a failed hook invalidates that check (re-run it after any failure).
  - Depends on: E-03
  - Expected outcome: a diff summary showing only the expected field and history lines, an assertion that no other metadata field changed on any plan, and `aw check plans` clean.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `aw ipd set --priority` and `--work-kind` exist and are documented as persisting "on a no-op transition", which is precisely the affordance a field-only backfill needs.
- A cross-tree id6 reference must be RESOLVED, not parsed: `check.from-backlog-dangling` already treats an unresolvable `From-Backlog` as a finding, so this plan must not accept one.
- An absent `Priority` renders as unprioritized and a value must never be fabricated (`xprio` orchestrator `u5vyye` OQ-01). Inheritance is not fabrication: the value comes from an artifact the plan itself names.

## Findings

| Id | Severity | Finding |
|---|---|---|
| F-1 | MEDIUM | 84 of 104 pending plans can inherit both fields with zero judgement: all 84 `- From-Backlog:` references resolve and all 84 sources carry both fields. Measured at authoring. |
| F-2 | MEDIUM | The inherited values are a genuine spread, not a single default, so the result is useful rather than uniform: 26 `high`/`bug`, 25 `medium`/`bug`, 11 `medium`/`feature`, 10 `high`/`feature`, 6 `medium`/`chore`, 3 `low`/`feature`, and three singletons. |
| F-3 | LOW | A setter already exists for both fields and persists on a no-op transition, so no hand-editing and no new tooling is needed for the write. |
| F-4 | LOW | This plan touches 84 files in a shared checkout where other agents commit concurrently, so the index must be re-verified before every commit and after any failed hook. That is an execution hazard rather than a design one, and E-04 owns it. |

## Proposed changes (ordered, validatable)

1. Re-derive and print the inheritance table, resolving every source (E-01).
2. Sanity-check the derived values and surface the tails without correcting any source (E-02).
3. Write both fields through the shipped setter, never by hand (E-03).
4. Prove no other field or status moved, and the checkers stay clean (E-04).

## Deferred / out of scope (with reason)

- THE 20 PLANS WITH NO SOURCE ITEM. Sibling 03 owns them, because they need a judgement this plan deliberately does not make.
- CORRECTING A SOURCE BACKLOG ITEM whose value looks wrong. Reported by E-02, not edited: those items are outside this plan's declared scope.
- TERMINAL PLANS. Immutable by policy, and exempt by the sentinel sibling 01 adds.
- ANY PLAN AUTHORED AFTER SIBLING 01 LANDS, which will carry the fields from the scaffold and needs no backfill.

## Scope check

- Over-scope: none. Only the pending plans tree is declared, and only two fields plus history are written.
- Under-scope: this plan leaves 20 pending plans without values by design; the Set is incomplete until sibling 03 runs.

## Required tests / validation

No new test file: this plan changes records, not code, and its correctness is demonstrated by the derivation table plus the no-collateral-change proof. Run the bare suite (`python3 -m pytest`) anyway and paste the summary, since a record change should not affect it and a difference would be informative. Establish the baseline BEFORE the first edit.

## Spec / documentation sync

N/A: sibling 01 amends the spec that defines the metadata fields. This plan writes values into existing recognized fields and changes no contract.

## Open questions

### OQ-01: Should a release-blocking plan that inherits a low or medium priority be corrected?

- Blocking: no
- Status: open
- Owner: this plan's executor for the reading, the maintainer only if a correction is proposed
- Resolution or deferral rationale: INHERIT FAITHFULLY AND REPORT THE MISMATCH; DO NOT SILENTLY OVERRIDE. `Blocks-Release` and `Priority` are orthogonal by design, and the source backlog item `p9o1oo` says so explicitly: the "urgent/drop-everything" case "is already covered orthogonally by `Blocks-Release`, so no 4th tier". So a release-blocking plan carrying `medium` is not a contradiction and must not be auto-promoted. E-02 lists these cases precisely so a human can see them; if any looks genuinely wrong, that is a source-item correction owned elsewhere. Non-blocking because the backfill is correct under either reading.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the full re-derived table with the command that produced it, and the count. State explicitly whether the count differs from the authored 84. Paste any dangling `- From-Backlog:` found, or state that none was.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the value distribution, every source value outside the two vocabularies (or state none), and the list of release-blocking plans inheriting `low`/`medium`. Confirm no source backlog item was modified (`git status` showing no change under `.aw/records/backlog/`).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the exact working `aw ipd set` invocation for the FIRST plan plus its `git diff` showing only the two fields and history changed and `- Status:` unchanged. Then paste a spot check of three more plans' resulting metadata blocks. Confirm no hand-edit was used.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `git diff --stat` over this item's commits, a grep proving no plan's `Status`/`Readiness`/`Set`/`Order`/`Id` line changed, `aw check plans` clean, and `aw att --type plan` showing a populated Priority column. Paste `git diff --cached --name-only` from before the final commit proving only this item's files were staged. Finally paste the bare `python3 -m pytest` summary against the pre-edit baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until it has been reviewed and a human sets it `approved`.

It carries `- Item-Dependencies: executed:lkexaw` deliberately: backfilling before the gate and the scaffold fix exist would write values nothing enforces and would leave the root cause in place, so a runner must hold this item until sibling 01 has landed.

Execution contract for whoever runs it: commit ONLY paths under the declared `Scope-Paths`, path-scoped, never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark.

NOTE THE SHARED-CHECKOUT HAZARD, which is this plan's main execution risk: it edits 84 tracked files while other agents commit concurrently. Verify `git diff --cached --name-only` before EVERY commit, re-verify after any failed hook (pre-commit's stash/restore can leave another agent's paths in the index), and never revert or sweep in a change you did not make.
