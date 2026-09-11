# IPD: Enforce a live bug carrying a release gate in aw check and backfill the existing violations

- Date: 2026-09-11
- Kind: child
- Concern: Writing the rule down and defaulting it at creation still leaves two holes: a hand-authored artifact bypasses the setter entirely, and the 28 already-ungated live bugs stay invisible. Without a checker the rule decays silently again, which is exactly how it reached 28 violations unnoticed.
- Scope: Add one `aw check` rule refusing a live bug-kind item with no release gate, registered in the rule registry so CI fails on it, then backfill the existing violations or record an explicit exemption for each. Does NOT change the creation default (child 02 owns it), does NOT gate other work kinds, and does NOT retroactively gate a bug already `done`.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_bug_gate_check.py, .aw/records/backlog
- Item-Dependencies: executed:di08i9
- Status: to-review
- Set: nobugship
- Order: 3
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: rgaasb
- Blocks-Release: next

## Workflow history

- 2026-09-11 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored as the third part of the answer to the maintainer's 2026-09-11 question, and the part that makes the other two hold. MEASURED at HEAD `2ff2b1b1`: a rule family for exactly this shape already ships, all at `error` severity under invariant `I-07` (`check_engine.py:105-127`): `check.blocking-item-closed-without-gate`, `check.from-backlog-gate-mismatch`, `check.blocks-release-dangling`, `check.from-backlog-dangling`, `check.from-spec-dangling`, plus the heuristic `check.orphaned-live-blocker` at `warning`. So this rule EXTENDS an established family rather than inventing a category, and `evaluate_blocking_close` (`:1980`) is the existing shared predicate for gate legitimacy on close. THE BACKFILL POPULATION AT AUTHORING: 28 live gateless bugs, split 16 `open`, 11 `graduated`, 1 `blocked`. It WILL differ at execution time and the parent's E-01 re-measures it.

## Goal

Make the rule self-maintaining, so a future ungated bug is reported rather than accumulating, and clear the existing 28 so the check starts from a true zero.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: add the check

- [ ] E-01 WRITE THE PREDICATE, REUSING THE FAMILY'S SHAPE RATHER THAN INVENTING ONE. A live bug-kind item with no `- Blocks-Release:` is a finding. LIVE means `open`, `blocked` or `graduated`; a `done` item is NOT flagged, because rewriting a closed bug's gate would assert a history that did not happen, and `parked` is an uncommitted maybe that the attention view already hides.
  COMPOSE WITH `evaluate_blocking_close` RATHER THAN FORKING IT (`check_engine.py:1980`). That predicate already owns gate legitimacy for the CLOSE direction, and this rule is the OPEN direction of the same invariant. One predicate family, one set of terms; a second copy would drift exactly as this repository's other duplicated rules have.
  DECIDE WHETHER A GRADUATED ITEM IS SATISFIED BY ITS PLAN'S GATE, and this is the substantive design choice. `AGENTS.md` already treats a plan carrying `From-Backlog` plus the same `Blocks-Release` as a legitimate HANDOFF that lets an item close. The same logic says a `graduated` bug whose plan carries the gate is not a violation. Measured at authoring, that would EXEMPT NONE of the 11, because none of those plans carries a gate; but the predicate should still express it, or a correctly-handed-off bug would be flagged forever.
  - Depends on: none
  - Expected outcome: a predicate returning a finding per live gateless bug, exempting `done` and `parked`, treating a gated handoff plan as satisfying, and composing with the existing close-direction predicate rather than duplicating it.
  - Execution state: pending

- [ ] E-02 REGISTER THE RULE IN `RULE_REGISTRY` under invariant `I-07` at `error`, matching its four siblings (`check_engine.py:105-116`). CHECK THE INVARIANT FIT BEFORE ASSUMING IT: a defect measured on 2026-09-10 had `check.setid-collision` filed under `I-09` ("filename-grammar conformance"), which does not describe it, so do not repeat that by choosing a convenient id. If `I-07` genuinely covers release-gate preservation, cite the catalog text that says so; if it does not, say so rather than mis-filing.
  STAGE THE SEVERITY ONLY IF THE BACKFILL CANNOT COMPLETE. `error` is correct for the end state and matches the family. If E-04's backfill leaves any item unresolved, the rule must still ship at `error` with those items carrying an explicit recorded exemption, NOT at `warning` with a promise to tighten later; a rule left permanently at `warning` is the failure mode recorded on `rnkqrc` E-05.
  - Depends on: E-01
  - Expected outcome: the rule registered at `error` under a justified invariant id, with the catalog text cited or the mismatch stated.
  - Execution state: pending

- [ ] E-03 TEST THE RULE AND ITS EXEMPTIONS in a new `tests/test_bug_gate_check.py`, with a falsification pass against pre-change code. Cover: a live gateless bug FLAGGED; a gated bug CLEAN; a `done` gateless bug CLEAN; a `parked` gateless bug CLEAN; a non-bug gateless item CLEAN; and a `graduated` gateless bug whose plan carries the gate CLEAN.
  ALSO ASSERT THE ANTI-FORK PROPERTY, since E-01 requires composition: a grep or import check showing the new predicate consumes the existing close-direction predicate rather than reimplementing gate legitimacy.
  - Depends on: E-02
  - Expected outcome: six behavioral cases plus the anti-fork proof, each new assertion shown failing against pre-change code.
  - Execution state: pending

### Task group 2: clear the existing violations

- [ ] E-04 RE-MEASURE AND BACKFILL, one item at a time, through the shipped setter. Use `aw backlog set <status> <id6> --blocks-release next` rather than hand-editing front matter, so the write goes through the same validation the tool applies elsewhere. RE-DERIVE THE POPULATION FIRST; the authored figure is 28 (16 `open`, 11 `graduated`, 1 `blocked`) and it moves as agents file items.
  DO NOT BLANKET-APPLY. For each item, state the gate applied or the exemption recorded. A bug that genuinely should not gate the release is a legitimate outcome and needs an explicit `- Blocks-Release: -` plus a reason in its history, not silent omission. Two named cases deserve individual judgement rather than a sweep: the `blocked` item `adgtqb` (already gated by a typed dependency, so its release relationship may differ) and any item whose summary suggests it is obsolete rather than open.
  FOR THE 11 GRADUATED ITEMS, GATE THE PLAN TOO, or the handoff exemption in E-01 will not be satisfied and the item will still be flagged. Measured: all 11 have a plan and none carries a gate, so this is 11 plan edits as well as 11 item edits, and those plans are in a shared checkout other agents are editing.
  - Depends on: E-03
  - Expected outcome: a per-item table showing the re-derived population, the action taken (gate applied, or exemption with its reason), and for graduated items the plan that also received the gate.
  - Execution state: pending

- [ ] E-05 PROVE THE CHECK IS AT ZERO AND NOTHING ELSE MOVED. Show the new rule reporting no findings, `aw check backlog` clean, and the release-blocker view carrying the newly gated items. Then show that no item's `- Status:`, `- Priority:` or `- Work-Kind:` changed as a side effect, since the setter takes a status argument and a mistake there would silently move an item's lifecycle state.
  RE-VERIFY THE INDEX BEFORE EVERY COMMIT AND AFTER ANY FAILED HOOK. This item edits up to 39 tracked files in a shared checkout where other agents commit concurrently, and pre-commit's stash and restore can leave their paths staged.
  - Depends on: E-04
  - Expected outcome: the new rule at zero findings, `aw check backlog` clean, no collateral field change on any item, and the staged set proven to contain only this item's files.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- A rule family for release-gate integrity already exists, all `error` under `I-07`: `check.blocking-item-closed-without-gate`, `check.from-backlog-gate-mismatch`, `check.blocks-release-dangling`, `check.from-backlog-dangling`, `check.from-spec-dangling` (`check_engine.py:105-124`), plus `check.orphaned-live-blocker` at `warning`.
- `evaluate_blocking_close` (`:1980`) is the shared predicate backing the setter, the check rules and an opt-in hook, so gate legitimacy has ONE owner and must not be forked.
- `AGENTS.md` already defines a legitimate HANDOFF as a plan carrying `From-Backlog` plus the same `Blocks-Release`, which is the shape the graduated exemption should reuse.
- A rule left permanently at `warning` is a recorded failure mode (`rnkqrc` E-05's obligation), so staged severity must have a stated end state.

## Findings

| Id | Severity | Finding |
|---|---|---|
| F-1 | HIGH | Nothing reports an ungated live bug today, which is how the count reached 28 unnoticed. Documentation and a creation default both leave the hand-authored route open, so a checker is what makes the rule self-maintaining. |
| F-2 | HIGH | The backfill is larger than it looks: 11 of the 28 are `graduated` and ALL 11 have a plan carrying no gate, so satisfying the handoff exemption means editing 11 plans as well as 11 items, in a shared checkout. |
| F-3 | MEDIUM | The rule extends an established family rather than inventing a category, so severity, invariant and predicate shape are all determined by precedent rather than by choice. |
| F-4 | MEDIUM | The invariant id must be justified, not assumed: a 2026-09-10 measurement found `check.setid-collision` filed under an invariant that does not describe it, and that mistake is easy to repeat. |
| F-5 | LOW | Two items in the population need individual judgement rather than a sweep: the one `blocked` item, whose release relationship may differ, and any item that is obsolete rather than genuinely open. |

## Proposed changes (ordered, validatable)

1. A predicate for a live gateless bug, composing with the close-direction predicate (E-01).
2. Registration at `error` under a justified invariant (E-02).
3. Six behavioral tests plus an anti-fork proof, with falsification (E-03).
4. A per-item backfill through the shipped setter, including the 11 plans (E-04).
5. Proof of zero findings and no collateral change (E-05).

## Deferred / out of scope (with reason)

- THE CREATION DEFAULT. Child 02 owns it, and this child depends on it so the backfill cannot immediately re-diverge.
- BUGS ALREADY `done`. Not flagged and not backfilled: a closed bug shipped or did not, and asserting a gate now would rewrite history.
- OTHER WORK KINDS, including `security`. The parent's OQ-01.
- A DEFECT MISLABELLED AS `chore`. The rule keys on `Work-Kind` and cannot see it; the parent's OQ-02 measures the leak and child 01 states it as a limit.

## Scope check

- Over-scope: none. The checker, one new test file, and the backlog tree the backfill edits.
- Under-scope: E-04 must also edit 11 PLAN files to satisfy the handoff exemption, which the declared `Scope-Paths` does not include. That is deliberate and must be handled as a declared out-of-scope edit at finalize with a reason per path, OR the plan paths must be added to `Scope-Paths` before execution; the executor must choose and record which, rather than editing undeclared files silently.

## Required tests / validation

`tests/test_bug_gate_check.py` with a falsification pass. Establish the suite baseline by running `python3 -m pytest` bare BEFORE the first edit and paste it; no figure is stated here deliberately.

## Spec / documentation sync

N/A with reason: child 01 records the rule and this child enforces it. The refusal message must POINT AT child 01's written text rather than restating policy, so the two cannot drift.

## Open questions

### OQ-01: Does a graduated bug whose plan carries the gate satisfy the rule?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: YES, AND E-01 IS WRITTEN THAT WAY, resolved from the existing contract rather than asked. `AGENTS.md` already defines a legitimate HANDOFF as a plan carrying `From-Backlog: <item>` plus the same `Blocks-Release`, and uses exactly that to let a gated item close without dropping its gate. The OPEN direction of the same invariant should recognise the same handoff, or a correctly-handed-off bug would be flagged forever and the rule would train people to ignore it. Non-blocking because it changes which items are flagged, not whether the rule is right: measured at authoring it exempts NONE of the 11, since none of those plans carries a gate. Record the decision in E-01's outcome.

### OQ-02: Should the rule also flag a gated item whose gate does not resolve?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NO, BECAUSE IT ALREADY EXISTS. `check.blocks-release-dangling` (`check_engine.py:111`) is precisely that rule, at `error` under the same invariant. Duplicating it here would fork a shipped check, which is the drift this repository repeatedly pays for. Resolve by CITING that rule in the new rule's docstring so a reader sees the division of labour: this one catches an ABSENT gate, that one catches an UNRESOLVABLE one. Non-blocking and resolvable without the maintainer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the predicate's output for SIX fixtures (live gateless bug, gated bug, `done` gateless bug, `parked` gateless bug, non-bug gateless item, graduated gateless bug with a gated plan), each with the verdict and reason. Paste the ANTI-FORK proof: a grep showing the predicate consumes `evaluate_blocking_close` or a helper factored from it rather than reimplementing gate legitimacy.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `RULE_REGISTRY` entry showing `error` and the chosen invariant id, and paste the invariant catalog text that justifies the choice. If no invariant fits, paste that finding instead and state what was done about it. Paste `aw check backlog --agent` reporting the new rule id.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_bug_gate_check.py -o addopts=""` with per-test names, then the FALSIFICATION showing the new cases FAIL against pre-change code.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the re-derived population with the command that produced it and state how it differs from 28. Paste the per-item table: id6, status, action (gate applied or exemption with reason), and for each graduated item the plan id6 that also received the gate. Paste one item's `git diff` proving only the gate line and history changed. Confirm no hand-edit was used.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new rule reporting ZERO findings, `aw check backlog` clean, and `aw attention` showing the release-blocker set including the newly gated items. Paste a grep proving no item's `Status`, `Priority` or `Work-Kind` changed. Paste `git diff --cached --name-only` from before the final commit proving only this item's files were staged. State explicitly how the out-of-scope plan edits were handled (declared in `Scope-Paths`, or reconciled at finalize with a reason per path). Finally paste the bare `python3 -m pytest` summary against the pre-edit baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until it has been reviewed and a human sets it `approved`.

It carries `- Item-Dependencies: executed:di08i9` because backfilling before the creation default lands would let the population re-diverge immediately, and the checker would then report violations the tooling itself was still creating.

It carries `- Blocks-Release: next` in line with the rule it enforces.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths` plus any out-of-scope path declared and reasoned at finalize, path-scoped, never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark.

NOTE TWO HAZARDS. FIRST, this item edits up to 39 tracked files in a SHARED CHECKOUT: verify `git diff --cached --name-only` before every commit, re-verify after any failed hook, and never sweep in a change you did not make. SECOND, the backfill must not become a blanket sweep: a bug that genuinely should not gate the release needs an explicit recorded exemption, and applying `next` to all 28 without judgement would trade one silent wrongness for another.
