# IPD: Stop orchestrator retirement ticking unperformed items by making the coverage gate's cached PASS mean a coverage child exists rather than a model once said so

- Date: 2026-09-23
- Kind: child
- Concern: TWO ORCHESTRATORS RETIRED TO `executed` LAST NIGHT WITH EVERY ONE OF THEIR SIX E-ITEMS AND SIX V-ITEMS UNPERFORMED, AND THE COVERAGE GATE PASSED THEM. Measured at HEAD `22cf67d9` on run `run-20260923T023317Z-3622118`: `y9s4vm` (Set `graduate`) and `lyo1tz` (Set `runnerlayer`) are both in `.aw/records/plans/executed/`, both still carry `- [ ] E-01`, `- [ ] E-02`, `- [ ] E-03` with `Execution state: pending`, and all six `V-*` items still read `Result: pending`. Their own retirement commits say so outright: "Its own E-*/V-* items were NOT performed; the runner superseded them by enforcing the ordering, the isolation and the per-child merge gate."
  THE GATE DID NOT FAIL TO RUN; IT RETURNED A CACHED PASS. `probe_cache_digest` over each plan's text keys into `.aw/state/runtime/orchestrator-probe-verdicts.json`, and both hit: `y9s4vm` -> `verdict: pass` recorded `2026-09-21T11:01:06Z`, `lyo1tz` -> `verdict: pass` recorded `2026-09-21T02:25:46Z`. So retirement proceeded exactly as designed, skipping the pre-transition E/V checkpoint on the premise that a parent's items are performed by nobody.
  WHETHER THAT PASS WAS RIGHT IS THE WHOLE QUESTION, AND FOR THESE TWO IT WAS ARGUABLY RIGHT AND STILL PRODUCED A FALSE RECORD. Each parent's E-03 asked a real question ("confirm backlog `6h7y2y` reached its correct terminal state"; "confirm backlog `cnwy8g` was closed by child 02"). I checked both by hand: `6h7y2y` is `graduated` and `cnwy8g` is `done`, so the underlying facts hold and no work was lost. But NOTHING VERIFIED THAT, and the plan now asserts on disk that three items were performed when its own commit message says they were not. A record that is true by luck and false in form is the defect: the next such retirement has no reason to be lucky, which is precisely what happened to `rh5tt6` on 2026-09-08 (commit `8b4e1570`, whose message states 'Its own E-*/V-* items were NOT performed' while its E-02 still read pending).
  BACKLOG `wtd5m2` PREDICTED THIS AND ITS CENSUS IS NOW SUBSTANTIALLY STALE, WHICH CHANGES THE REMEDY. It lists seven pending orchestrators carrying uncovered work. Re-measured: TWO of the seven (`y9s4vm`, `lyo1tz`) have since RETIRED, which is the incident above. Of the remaining five, ALL FIVE now have a dedicated coverage child authored to perform the parent's own items: `5e4sb6` -> five children including `i3d6ml`/`tx6q0h`/`ct4w0a` (all `executed`); `wfjsp4` -> `ingpvc` (`approved`, "THE WHOLE-SET VERIFICATION, owning THIS PARENT'S E-01 through E-04"); `a5wdne` -> `04vf1h` (`approved`, "perform this orchestrator's own E-01 as a real agent turn"); `tb63qv` -> `k311gw` (`approved`, "perform this orchestrator's own E-01 ... Added 2026-09-22 after the orchestrator coverage gate refused a run naming `tb63qv`"); `ao1rb7` -> `2s0iym` (`approved`, "Performs THIS PARENT'S E-03"). So the AUTHORING debt `wtd5m2` tracks is essentially DISCHARGED, and what remains is the MECHANISM defect that let two parents retire anyway.
  AND THE CACHE MAKES THE VERDICT DISAGREE WITH THE TREE, WHICH IS THE SHARPEST FINDING. The probe verdicts disagree with `wtd5m2`'s human reading on three of five (`a5wdne`, `tb63qv`, `ao1rb7` all cached `pass` while `wtd5m2` calls their items uncovered) and agree on two (`5e4sb6`, `wfjsp4` cached `fail`). For `a5wdne` the PASS is defensible because `04vf1h` exists to cover E-01, so the model was reading a parent whose child table already named a coverage child. That means the verdict is answering "does a child cover this?" from the plan TEXT, and a cached answer keyed on that text cannot notice that the covering child is still `approved` and has never run.
- Scope: Make retirement unable to tick an item nothing performed. IN: (a) per OQ-01, gate retirement on a STRUCTURAL check (the parent's items are discharged by a named, EXECUTED coverage child) rather than solely on a cached model verdict; (b) make a retirement that proceeds record its own items honestly rather than leaving `- [ ] ... pending` under a terminal status, per OQ-02; (c) a regression test built from the two measured retirements. OUT: re-authoring the five coverage children, which already exist (this plan's own measurement); reversing the two completed retirements, which cannot be fixed in place and needs a corrective plan per `AGENTS.md`; and `rh5tt6`'s 2026-09-08 gap, which `wtd5m2` itself defers to the maintainer.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/ipd_lifecycle.py, tests/test_orchestrator_retirement.py
- Item-Dependencies: none
- Status: to-review
- Set: orchretire
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: kjqqzf
- From-Backlog: wtd5m2
- Blocks-Release: next

## Workflow history

- 2026-09-23 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `wtd5m2`, whose `- Blocks-Release: next` is INHERITED, and RE-AIMED because its census is stale. Re-measured all seven listed orchestrators: two have retired (the incident), and all five survivors now carry a dedicated coverage child, so the authoring debt it tracks is discharged and the MECHANISM defect is what survives.
  THE INCIDENT IS FRESH AND MEASURED, not inferred: `y9s4vm` and `lyo1tz` are in `executed/` with all six E-items and six V-items still `pending`, their retirement commits admit the items were not performed, and both carry a cached `pass` in the probe store dated 2026-09-21, before last night's run.
  I VERIFIED THE UNDERLYING FACTS BY HAND AND REPORT THE HONEST RESULT: both parents' E-03 claims happen to be TRUE (`6h7y2y` is `graduated`, `cnwy8g` is `done`), so no work was lost this time. I am filing it as a defect anyway because nothing verified them and the plans now assert performance their own commits deny; the same mechanism with an unlucky draw is `rh5tt6`.
  THE DESIGN INSIGHT I WANT A REVIEWER TO CHECK is that a text-keyed cached verdict structurally cannot see whether the covering child has actually EXECUTED, which is why OQ-01 proposes a structural gate rather than a better prompt.

## Goal

Make it impossible for orchestrator retirement to mark an item complete that no executed child performed, and make any retirement that does proceed state honestly what it did not do.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the incident and the real debt

- [ ] E-01 RE-MEASURE THE INCIDENT AND THE CENSUS, because this plan's re-aiming depends on both and `wtd5m2`'s own numbers were stale within four days.
  CONFIRM THE TWO RETIREMENTS: show `y9s4vm` and `lyo1tz` in `executed/`, with their E-items' `Execution state:` and V-items' `Result:` values pasted, and quote the retirement commit sentence admitting the items were not performed.
  CONFIRM THE CACHED VERDICTS: compute `probe_cache_digest` over each plan's text, look it up in the probe store, and paste the verdict and its `recorded_at`. At authoring both were `pass`, dated 2026-09-21.
  RE-CENSUS THE FIVE SURVIVORS and, for each, name its coverage child AND that child's CURRENT status. At authoring: `ingpvc`, `04vf1h`, `k311gw`, `2s0iym` all `approved` (authored but NOT yet executed), and `5e4sb6`'s children `executed`. This distinction is the crux: a coverage child that exists but has not run does not discharge anything yet.
  REPORT WHETHER THE UNDERLYING FACTS HELD, as I did, rather than assuming harm. If `6h7y2y`/`cnwy8g` are in their expected states, say so; the defect is the unverified assertion, and overstating the damage would be its own dishonesty.
  - Depends on: none
  - Expected outcome: the two retirements, their cached PASS verdicts, and the five survivors' coverage children with current statuses all pasted; an honest statement of whether any work was actually lost.
  - Execution state: pending

### Task group 2: fix the gate

- [ ] E-02 MAKE RETIREMENT'S PRECONDITION STRUCTURAL, per OQ-01. Today a cached model verdict keyed on the parent's TEXT decides whether the parent carries uncovered work, and that key cannot express whether the covering child has EXECUTED.
  THE CHECK MUST READ THE TREE, NOT ONLY THE TEXT. `a5wdne`'s cached PASS is defensible precisely because its child table names `04vf1h` as the coverage child, yet `04vf1h` is `approved` and has never run. A gate that accepts "a child is named" while the child is unexecuted will retire the parent with its items still unperformed, which is this incident.
  DO NOT DELETE THE MODEL PROBE. It answers a question no structural check can ("is this prose actually covered by that child's scope?"), and `AGENTS.md` records that it was added after a measured incident. Add the structural precondition; do not replace judgement with a heuristic.
  FAIL CLOSED AND SAY WHICH. `AGENTS.md` already specifies that a refusal names WHICH condition it hit and that refusing leaves the plan in `pending/`, which "is not a failure of the run". Preserve that, and preserve `--allow-uncovered-orchestrator-work` as the maintainer's explicit, justification-requiring override rather than adding a second escape hatch.
  DO NOT MAKE THE REMEDY "DELETE THE PARENT'S CHECKLIST". `AGENTS.md` is emphatic that the parent's checklist is what makes `execute <setid>` complete and ordered when a human drives a Set with no runner, and that deleting it causes the lost work the gate exists to prevent.
  - Depends on: E-01
  - Expected outcome: retirement refuses when a parent's items are discharged only by a child that is not `executed`, naming that child and its status; the model probe is retained; the existing override still works and still requires a justification; no parent checklist is deleted.
  - Execution state: pending

- [ ] E-03 MAKE A PROCEEDING RETIREMENT RECORD ITSELF HONESTLY, per OQ-02. Independently of E-02, a retired parent currently sits in `executed/` with `- [ ] E-01 ... Execution state: pending`, which asserts by form what its commit message denies in prose.
  THE FILE IS THE DURABLE RECORD; THE COMMIT MESSAGE IS NOT WHERE A READER LOOKS. `aw ipd lint` and every human reading the plan see unchecked boxes under a terminal status, so the two disagree. This is the same class as `AGENTS.md`'s attestation rule: a record must not assert work that was not done, and it must not silently omit that it was superseded.
  DO NOT TICK THE BOXES. Marking them `[x]` would be the forgery this plan exists to prevent. The honest form records that retirement SUPERSEDED them and why, leaving their state visibly not-performed.
  - Depends on: E-01
  - Expected outcome: a retired orchestrator's file states, in the file, that its own items were superseded by retirement and not performed; no item is marked complete; `aw ipd lint` does not report the terminal plan as malformed.
  - Execution state: pending

### Task group 3: pin the incident

- [ ] E-04 ADD A REGRESSION TEST BUILT FROM THE TWO MEASURED RETIREMENTS.
  THE FIXTURE MUST BE THE REAL SHAPE: an orchestrator whose every child is `executed`, whose own items are covered only by a coverage child that is NOT executed, and a cached PASS verdict in the probe store. That combination is what produced this incident and no current test reaches it.
  ASSERT THE REFUSAL NAMES THE CAUSE, not merely that it refused, since `AGENTS.md` requires a refusal to say which condition it hit and the whole operational value is that a human knows what to fix.
  DO NOT PIN THE LIVE PLAN CORPUS. `jsomff` records a test in this very file hardcoded to a Set that has since completed and now fails on every run; repeating that would be a self-inflicted repeat of a known defect.
  - Depends on: E-02, E-03
  - Expected outcome: a test failing against pre-E-02 code and passing after, using a synthetic fixture (never the live corpus), asserting both the refusal and the named cause.
  - Execution state: pending

## Project conventions discovered (Step 0)

- RETIREMENT DELIBERATELY SKIPS THE PRE-TRANSITION E/V CHECKPOINT on the premise that a parent's items are performed by nobody (`AGENTS.md`), which is exactly why a parent carrying real work must be refused BEFORE it retires.
- AN ORCHESTRATOR SHOULD KEEP ITS CHECKLIST: it is what makes a human-driven `execute <setid>` complete and ordered, and deleting it to satisfy the gate causes the lost work the gate prevents (`AGENTS.md`).
- THE VERDICT CACHE IS KEYED ON THE PARENT'S TEXT (`probe_cache_digest` over the plan file), so "a genuine fix changes the key and discards the entry"; it follows that a change OUTSIDE the parent (a child executing) does not invalidate a cached verdict.
- THE OVERRIDE IS `--allow-uncovered-orchestrator-work` and it REQUIRES a justification which is recorded; a second, quieter escape hatch would defeat that design.
- TESTS IN `tests/test_orchestrator_retirement.py` HAVE BEEN PINNED TO LIVE SETS BEFORE and went red when those Sets completed (`jsomff`), so fixtures are required.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER | `retire_orchestrator` + the probe cache | Two orchestrators retired to `executed` with ALL six E-items and six V-items unperformed, passed by a CACHED verdict recorded two days earlier. | `y9s4vm`/`lyo1tz` in `executed/` with `Execution state: pending` x3 and `Result: pending` x3 each; probe store hits `pass` @ `2026-09-21T11:01:06Z` and `2026-09-21T02:25:46Z` |
| F-2 | BLOCKER | the retired plan files | The files assert by FORM what their own commits deny in PROSE: unchecked items under a terminal status, against a commit saying "Its own E-*/V-* items were NOT performed". | both retirement commit messages, quoted |
| F-3 | HIGH | `probe_cache_digest` keying | The verdict is keyed on the parent's TEXT, so it cannot express whether the covering child has EXECUTED. `a5wdne` caches `pass` while its coverage child `04vf1h` is `approved` and has never run. | digest lookups; `04vf1h` status `approved` |
| F-4 | HIGH (narrowing) | `wtd5m2`'s census | Stale within four days: 2 of 7 have retired, and ALL FIVE survivors now have a dedicated coverage child (`ingpvc`, `04vf1h`, `k311gw`, `2s0iym`, plus `5e4sb6`'s executed set). The AUTHORING debt is discharged; the MECHANISM defect survives. | each parent's child table, quoted, with child statuses |
| F-5 | MED | probe verdicts vs human reading | They disagree on 3 of 5 (`a5wdne`, `tb63qv`, `ao1rb7` cached `pass` where `wtd5m2` reads uncovered) and agree on 2 (`5e4sb6`, `wfjsp4` cached `fail`). The disagreement is explained by F-3, not by the model being wrong. | the five digest lookups |
| F-6 | INFO | this incident's blast radius | No work was actually lost: `6h7y2y` is `graduated` and `cnwy8g` is `done`, the states the two E-03 items asked about. The defect is the UNVERIFIED assertion, not a measured loss. | both items' status read on disk |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the incident, the cached verdicts, and the five survivors' coverage children with current statuses.
2. E-02 adds a structural precondition so retirement refuses when the covering child is not `executed`, retaining the model probe and the existing override.
3. E-03 makes a proceeding retirement state in the file that its items were superseded, without ticking them.
4. E-04 pins the incident with a synthetic fixture asserting the refusal and its named cause.

## Deferred / out of scope (with reason)

- RE-AUTHORING THE FIVE COVERAGE CHILDREN. F-4: all five exist. Executing them is ordinary queue work, not this plan's.
- REVERSING THE TWO COMPLETED RETIREMENTS. `AGENTS.md` forbids adding commits to a plan already in `executed/` and requires a corrective plan instead. F-6 records that no work was lost, so the corrective act is a records decision for the maintainer rather than urgent repair; OQ-03 raises it.
- `rh5tt6`'s 2026-09-08 UNPERFORMED E-02 in `executed/`. `wtd5m2` explicitly defers it to the maintainer and it cannot be fixed in place.
- REPLACING THE MODEL PROBE WITH A PURE HEURISTIC. E-02 states why: the probe answers a question structure cannot, and it exists because of a measured incident.
- WIDENING THE CACHE KEY TO INCLUDE CHILD STATUSES. A plausible alternative to E-02 and deliberately not chosen here, because it makes every child transition invalidate every parent's verdict and re-probe, which costs a model call per transition; recorded under OQ-01 so the reviewer can overrule.

## Scope check

- Over-scope: `runner_shared.py` and `ipd_lifecycle.py` are in scope ONLY for the retirement precondition and the honest-record write. Do not change queue ordering, dependency evaluation, or the merge gate.
- Under-scope: if E-03's honest-record form requires an `aw ipd lint` rule change to remain conforming, `agent_workflows/ipd_lint.py` is undeclared and must be added deliberately before editing.

## Required tests / validation

- `python3 -m pytest` bare, per the execution contract, with the actual summary line pasted.
- Targeted: `tests/test_orchestrator_retirement.py`.
- E-04's test MUST be demonstrated FAILING against pre-E-02 code; the incident shipped green, so a test that never failed proves nothing.
- E-04 MUST use a synthetic fixture, never the live plan corpus (`jsomff` records that exact hazard in this file).
- The existing retirement tests must stay green, proving the legitimate retirement path (a parent whose items ARE covered by executed children) still works.

## Spec / documentation sync

- Spec `25kzda` 2.5b and `77tr3o` R-12 specify the coverage gate. If E-02 changes its PRECONDITION, that is a contract change and the spec must be amended in the same change; declare the `.spec.md` in `- Scope-Paths:` BEFORE editing, per the spec-amendment rule, since the runners announce declared spec edits at run start and reconcile them at finalize.
- `AGENTS.md`'s runner paragraph states that retirement is "gated on EVERY child being `executed` and on nothing else qualifying"; if E-02 adds a condition, that sentence needs updating so the documented behavior matches.

## Open questions

### OQ-01: Structural precondition, or widen the cache key?

- Blocking: no
- Status: open
- Owner: this plan's executor, escalating to the maintainer because it touches a specified gate
- Resolution or deferral rationale: NOT blocking, because E-02 must implement one and either closes F-1/F-3. STRUCTURAL PRECONDITION (refuse when the item-covering child is not `executed`) is recommended: it is deterministic, needs no model call, and directly expresses the property that was violated. WIDENING THE CACHE KEY to include child statuses would also work and is conceptually tidier, but it invalidates every parent's verdict on every child transition and so spends a model call per transition, which is a real cost on a large Set. A third option, PROBE FRESHNESS (expire a verdict after N hours), is rejected: it would have changed nothing here, since both verdicts were only two days old and the tree had moved underneath them, so freshness is not the axis that failed.

### OQ-02: What should a retired parent's file say about its own items?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking; E-03 requires the file to stop asserting by form what the commit denies, and the exact wording is a presentation choice. The constraint that matters is that items must NOT be ticked (that would be forgery). Candidates: append a superseded note per item; add a single parent-level statement above the checklist; or record it in the workflow history only. Prefer a form `aw ipd lint` can validate, so a future retirement cannot omit it.

### OQ-03: Should the two completed retirements be corrected in the record?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking and deliberately not performed here. `y9s4vm` and `lyo1tz` are in `executed/` asserting three performed items each; F-6 establishes their underlying claims were in fact true, so nothing is broken in the tree, but the records overstate what happened. `AGENTS.md` forbids editing a plan already in `executed/` and requires a corrective IPD, which is a maintainer decision about whether the record is worth correcting given no work was lost. Raised rather than assumed so it is not silently dropped.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted E/V states for both retired parents; both retirement commit sentences quoted; both cached verdicts with `recorded_at`; the five survivors each with their coverage child and that child's current status; and an explicit statement of whether any work was lost.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: a fixture orchestrator whose coverage child is not `executed`, run through retirement, with the pasted REFUSAL naming that child and its status; plus a pasted case showing a legitimately covered parent still retires; plus proof `--allow-uncovered-orchestrator-work` still overrides and still records its justification.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: a retired fixture plan's file pasted, showing the superseded statement present and NO item marked `[x]`; plus `aw ipd lint` output for that file showing it conforms.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the new test pasted FAILING against pre-E-02 code and PASSING after; confirmation by inspection that it uses a synthetic fixture and reads no live plan; the existing retirement tests pasted green; plus the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the paths named in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, declaring any spec file before amending it, never `git add -A`, and never pushes. Test claims must paste actual runner output. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the plan moves to `.aw/records/plans/executed/`.
