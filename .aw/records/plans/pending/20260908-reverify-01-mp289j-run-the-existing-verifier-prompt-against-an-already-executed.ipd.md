# IPD: Run the existing verifier prompt against an already executed plan without re-executing it

- Date: 2026-09-08
- Kind: child
- Concern: THE INDEPENDENT SKEPTICAL VERIFIER EXISTS AND CAN ONLY EVER RUN AS THE SECOND TURN OF AN EXECUTION, SO IT CANNOT BE ASKED FOR AFTERWARDS. Re-verified at HEAD by symbol: `build_verifier_prompt` composes the fresh-session verification turn and has exactly ONE caller per host, both inside the execute path (`oc_runipd.py:4857` defined, called at `:6379`; `agy_runipd.py:2517` defined, called at `:3643`), both reached only when `validate` is on. NOTE the item's own citations are already stale by roughly 130 and 230 lines (`:4725`/`:2290` for the definitions, `:6230`/`:3409` for the callers), which is exactly the drift this repository warns about and is why every coordinate here is re-stated.
  THE THREE SITUATIONS THAT COST SOMETHING ALL HAPPENED IN THIS REPOSITORY, and the item names them concretely: a run executed with validation OFF, which is the current opencode default by the maintainer's measured 2026-08-31 ruling, so a later independent opinion requires re-executing an already-`executed` plan; an item that reached `substantially-complete` because finalize refused (`nna8yz` in run `run-20260905T211011Z-3780617`, 21.80 dollars of work, finalize refused for a missing begin receipt), where an independent verifier is exactly what a human wants before deciding whether to trust the lane; and six lanes integrated BY HAND during recovery on 2026-09-05, validated by the full suite but never by an independent verifier, with no way to add that signal after the fact.
  ITS VALUE IS CONDITIONAL ON WORK THAT IS NOT DONE, AND THE ITEM SAYS SO EXPLICITLY. The item's own sequencing recommendation is "do `h7qsje` first", reasoning that if per-model verification is wired and a weaker model runs with validation ON, "the in-run verifier covers most of the need and this verb becomes a recovery tool rather than the primary path. Building it first risks adding a surface nobody invokes, for the same reason nobody currently passes `--validate`." VERIFIED AT HEAD: `h7qsje` is `done` as an ITEM, but the work it graduated into is NOT finished. `tm2cz8` (`hostdefault-01`) is `approved` and still in `pending/`; `ybkmzp` (`hostdefault-02`, the child that actually wires the resolved decision into both drivers) is only `to-review`. So the precondition the item names is UNMET, and the sibling plan agrees: `ybkmzp`'s own Deferred section names "A STANDALONE RE-VERIFY VERB for an already-executed plan. Backlog `7u9kbm`, deliberately sequenced after this and inheriting the same cost question."
  SO THIS PLAN IS AUTHORED AS A GATED DESIGN, NOT A BUILD, and its first deliverable is the answer to whether it should exist. The item lists four things to decide "none of which the repository can settle alone", and the fourth is whether the verb is wanted at all given the economics: the maintainer's measured finding is that on the strong executor the verifier added only nits for roughly 33 percent extra cost. A plan that built the verb without answering that would be spending money to add a surface whose in-run twin is already switched off by default.
  ONE CONSTRAINT IS ABSOLUTE AND MUST SHAPE ANY IMPLEMENTATION: reuse `build_verifier_prompt` and the existing outcome schema. The item states it and gives the reason: "It must NOT be a second implementation ... or the two verifiers will drift and neither can be trusted (the same argument `wlxkoz` makes about not building a second completion checker)."
- Scope: Decide whether a standalone re-verify verb should exist and, if so, exactly what it verifies against and what it may write; implement only what that decision authorizes, reusing the EXISTING verifier prompt and outcome schema rather than writing a second verifier. EXCLUDES changing the in-run verifier, changing the `validate` default, and any change to what an `executed` plan's record says.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/runner_shared.py, .aw/records/specs, tests/test_standalone_verify.py
- Item-Dependencies: executed:ybkmzp
- Status: to-review
- Set: reverify
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: mp289j
- From-Backlog: 7u9kbm

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `7u9kbm` as a GATED DESIGN plan, honoring the item's own sequencing recommendation rather than overriding it. Every citation re-verified by SYMBOL and found STALE in the item: `build_verifier_prompt` is at `oc_runipd.py:4857` (item said `:4725`) and `agy_runipd.py:2517` (item said `:2290`), with its single callers at `:6379` and `:3643` (item said `:6230`/`:3409`). The one-caller-per-host claim itself is TRUE and re-measured. THE SEQUENCING PRECONDITION IS UNMET, which is why this carries a dependency edge rather than being buildable now: the item says "do `h7qsje` first", and while `h7qsje` is `done` as an ITEM, the plans it graduated into are not finished (`tm2cz8` is `approved` in `pending/`; `ybkmzp`, the child that actually wires the decision into both drivers, is only `to-review`). Sibling plan `ybkmzp` independently agrees, naming this item as "deliberately sequenced after this and inheriting the same cost question". This plan therefore carries `Item-Dependencies: executed:ybkmzp` and a BLOCKING question on whether the verb is wanted at all, since the maintainer's measured finding is that the verifier added only nits for ~33 percent cost on the strong executor, and the in-run twin is currently off by default.

## Goal

Give a human a way to buy an independent opinion on work that is already done, or a recorded decision that this repository deliberately does not offer one, instead of leaving an expensive lane unverifiable and the question unanswered.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm the gap and the precondition

- [ ] E-01 RE-MEASURE THE GAP AND THE SEQUENCING PRECONDITION BY SYMBOL, and write both down before designing anything.
  THE GAP: locate `build_verifier_prompt` in BOTH drivers by NAME and count its callers. This plan measured one per host, both inside the execute path and both gated on `validate`. Do not trust either this plan's or the item's line numbers: the item's four coordinates were all stale by 130 to 230 lines at graduation, and both files are under concurrent edit by live runs.
  THE PRECONDITION: check whether `ybkmzp` has EXECUTED, since that is the child that wires the per-host verification decision into both drivers and is the thing the item's "do `h7qsje` first" recommendation actually depends on. `h7qsje` being `done` as a backlog ITEM is NOT the same as the work being landed, and confusing the two is exactly how a sequencing recommendation gets ignored.
  IF `ybkmzp` HAS NOT EXECUTED, STOP HERE AND REPORT. Task groups 2 and 3 must not be performed: the item's whole cost argument is that with per-model verification wired, a weaker model runs with validation ON and the in-run verifier covers most of the need, making this verb a recovery tool rather than a primary path. Building it before that lands risks "adding a surface nobody invokes".
  - Depends on: none
  - Expected outcome: a symbol-cited statement of the caller count per host and of `ybkmzp`'s status, with an explicit STOP if the precondition is unmet.
  - Execution state: pending

### Task group 2: answer the four questions the item reserved

- [ ] E-02 ANSWER WHAT THE VERB VERIFIES AGAINST, which is the item's question 1 and the one that decides whether the verb is even coherent.
  THE PROBLEM STATED PRECISELY: the in-run verifier reads the execution outcome JSON for THAT attempt, in the worktree, immediately after the work. For a plan executed weeks ago on a different HEAD, "the work" is a historical diff, and verifying it against TODAY's tree answers a different question. The item's own lean is "probably needs an explicit base (the plan's recorded `base_head`) rather than an implicit one".
  VERIFY THAT THE RECORDED BASE IS ACTUALLY AVAILABLE, rather than assuming it. The begin receipt carries `base_head`, but receipts live under gitignored `.aw/state/` and are absent from a fresh clone, and a receipt is CONSUMED on the clean finalize path. So establish, by inspection, whether a plan that finalized cleanly still has a readable base at all. If it does not, that is a finding that reshapes this plan: the verb would need the base supplied explicitly by the operator, or would have to verify against something else entirely.
  BEWARE THE SIBLING MEASUREMENT: a plan's run record lives under `.aw/records/runs/`, which is gitignored and absent from a lane worktree, and `h9cn0y`'s review measured that finalize receives no run id at all. Any design reading a run record must state where that record is guaranteed to exist.
  - Depends on: E-01
  - Expected outcome: a written answer for what the verb compares against, with proof that the chosen base is actually reachable for a cleanly-finalized plan, or a finding that it is not.
  - Execution state: pending

- [ ] E-03 ANSWER WHAT THE VERB MAY WRITE, which is the item's question 2, and treat the constraint as hard rather than negotiable.
  THE CONSTRAINT: an `executed` plan must NOT be edited in place (repository policy, stated in AGENTS.md), so a negative verdict cannot silently reopen it. The item's own answer is that it "should produce a corrective-IPD recommendation or a durable finding, not a status change".
  DECIDE WHERE THE VERDICT LANDS, since "a durable finding" needs an address. Candidates: a run record under `.aw/records/runs/` (gitignored, so invisible to a reviewer and absent from a clone), a review record under `.aw/records/reviews/` (tracked, and its README says the shape is artifact-neutral with `Subject-Id`/`Subject-Type`, though it also says only `/plan-review` produces records today), or a new record type. State the trade: a gitignored verdict cannot be cited in a plan; a tracked one becomes permanent history for a machine-generated opinion.
  A NEGATIVE VERDICT MUST NOT BE SILENTLY DISCARDABLE EITHER. If the verb writes nowhere durable, an operator can run it, dislike the answer, and run it again; that is the shape of a check nobody can trust. Say what stops that, or record that nothing does.
  - Depends on: E-02
  - Expected outcome: a decided, addressed destination for the verdict that respects the immutability policy, with the tracked-versus-gitignored trade stated and the re-run-until-happy hazard addressed.
  - Execution state: pending

- [ ] E-04 ANSWER WHETHER IT NEEDS A LANE, which is the item's question 3 and is a contention question with a measured history.
  THE ISSUE: the in-run verifier runs in the worktree. A standalone one has no lane, and running it against the primary checkout while other agents work there is the contention problem `p8ni63`/`5wdoze` exist for.
  NOTE THE LANDSCAPE HAS MOVED IN THIS PLAN'S FAVOUR: isolation is now the DEFAULT for execute turns (`isolate_worktree` defaults True), and `3i0aaz` graduated the remaining ungated dirty-base cases. So allocating a lane for a standalone verification is the consistent choice rather than a novel one, and `worktree_lease` already owns allocation and teardown.
  BUT A VERIFIER IS READ-MOSTLY, so state whether a full lane is warranted or whether a read-only checkout of the recorded base is both cheaper and more correct. The verb's job is to form an opinion, not to change the tree, and a lane whose changes are then discarded is a lane that mainly costs time.
  - Depends on: E-03
  - Expected outcome: a decided answer on lane allocation with its reasoning, consistent with isolation being the default, and an explicit statement of what the verifier is permitted to write into whatever tree it gets.
  - Execution state: pending

### Task group 3: build only what the ruling authorizes

- [ ] E-05 IMPLEMENT THE DECISION, REUSING THE EXISTING PROMPT AND SCHEMA, OR RECORD THAT THE VERB IS NOT WANTED. Both are real outcomes.
  UNDER A BUILD OUTCOME: add the verb calling the EXISTING `build_verifier_prompt` and writing the EXISTING outcome schema. Do NOT write a second verifier: the item is explicit and cites `wlxkoz`'s argument against a second completion checker. Prefer siting shared logic in `runner_shared.py`, since `rununify` (`5e4sb6`) exists to de-duplicate the two drivers and adding a host-specific copy would enlarge that backlog.
  DO NOT WIRE THE AGY HOST unless the decision requires it. `agy_runipd.py` imports heavily from `oc_runipd.py` and the two are mid-unification; a second host surface doubles the review burden for a verb whose value is still conditional. If only one host gets it, SAY SO in the docs rather than letting a reader infer parity.
  UNDER A NOT-WANTED OUTCOME: write the decision into a spec, including the economics that decided it, so the next person who wants this finds the answer rather than re-deriving it. That is a genuine deliverable: the item's question 4 asks "Is it wanted at all, given the economics?", and a recorded no is more valuable than an unused verb.
  DO NOT CHANGE THE `validate` DEFAULT under either outcome. That default is a measured maintainer ruling from 2026-08-31, and `ybkmzp`/`tm2cz8` own the per-host decision surface.
  - Depends on: E-04
  - Expected outcome: either the verb, reusing prompt and schema with no second verifier and no unrequested second host, or a recorded spec decision that it is not wanted with the economics stated; the `validate` default untouched either way.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE VERIFIER IS REAL AND SINGLE-SITED: `build_verifier_prompt` at `oc_runipd.py:4857` and `agy_runipd.py:2517`, each with exactly ONE caller (`:6379`, `:3643`), both inside the execute path and gated on `validate`.
- THE ITEM'S OWN CITATIONS ARE STALE by 130 to 230 lines, which is the concrete case for re-locating by symbol.
- THE SEQUENCING PRECONDITION IS UNMET: `h7qsje` is `done` as an ITEM but `tm2cz8` is `approved` in `pending/` and `ybkmzp` is only `to-review`. Item status is not landed work.
- THE SIBLING PLAN AGREES INDEPENDENTLY: `ybkmzp`'s Deferred section names this item as "deliberately sequenced after this and inheriting the same cost question".
- NO SECOND VERIFIER: reuse `build_verifier_prompt` and the existing outcome schema, per the item and per `wlxkoz`'s argument against a second completion checker.
- RUN RECORDS AND RECEIPTS ARE GITIGNORED: `.aw/records/runs/` and `.aw/state/` are absent from a clone and from a lane worktree, and `h9cn0y`'s review measured that finalize receives no run id. Any design reading them must say where they are guaranteed to exist.
- AN `executed` PLAN IS IMMUTABLE: a negative verdict cannot reopen it; the honest route is a corrective IPD.
- ISOLATION IS THE DEFAULT for execute turns (`isolate_worktree` defaults True), so allocating a lane is consistent rather than novel.
- THE REVIEW RECORD SHAPE IS ARTIFACT-NEUTRAL (`Subject-Id`/`Subject-Type`) but only `/plan-review` produces records today.
- `rununify` (`5e4sb6`) EXISTS TO DE-DUPLICATE THE DRIVERS, so shared logic belongs in `runner_shared.py`.
- Both runner files are under concurrent edit. Suite runs BARE.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the gap is real and re-measured | `build_verifier_prompt` has exactly ONE caller per host, both inside the execute path and gated on `validate`, so verification is available only as the turn after an execution. | `oc_runipd.py:4857`/`:6379`; `agy_runipd.py:2517`/`:3643` |
| F-2 | HIGH | the item's citations are stale | All four coordinates moved: definitions `:4725`->`:4857` and `:2290`->`:2517`, callers `:6230`->`:6379` and `:3409`->`:3643`. | located by symbol at HEAD |
| F-3 | HIGH | the item's own precondition is UNMET | It says "do `h7qsje` first". `h7qsje` is `done` as an ITEM, but `tm2cz8` is `approved` in `pending/` and `ybkmzp` (which wires the decision into both drivers) is only `to-review`. | statuses read at HEAD |
| F-4 | HIGH | the sibling plan independently sequences it after itself | `ybkmzp`'s Deferred section: "A STANDALONE RE-VERIFY VERB ... Backlog `7u9kbm`, deliberately sequenced after this and inheriting the same cost question." | `ybkmzp`'s Deferred section |
| F-5 | HIGH | the economics question is genuinely open | The maintainer's measured finding is that on the strong executor the verifier added only nits for ~33 percent cost, and nobody currently passes `--validate`. A verb inherits that. | the item's question 4 |
| F-6 | MEDIUM | the base to verify against may not be reachable | The receipt carries `base_head` but lives under gitignored `.aw/state/` and is consumed on the clean finalize path, so a cleanly-finalized plan may have no readable base. E-02 must establish this. | `.aw/state/` gitignored; the finalize consumption path |
| F-7 | MEDIUM | run records are unreachable from a clone or lane | `.aw/records/runs/` is gitignored and absent from a lane worktree, and finalize receives no run id. A design reading them must say where they exist. | `h9cn0y` F-13 |
| F-8 | MEDIUM | the verdict has nowhere obviously correct to go | A gitignored verdict cannot be cited; a tracked one makes a machine opinion permanent history. The review-record shape is artifact-neutral but only `/plan-review` writes one today. | `.aw/records/reviews/README.md` |
| F-9 | MEDIUM | the contention question has moved favourably | Isolation is now the DEFAULT for execute turns, so allocating a lane for a standalone verification is consistent rather than novel. | `isolate_worktree` default True |
| F-10 | MEDIUM | a second implementation is forbidden | The item requires reusing `build_verifier_prompt` and the outcome schema, citing `wlxkoz`'s argument against a second completion checker. | the item's "WHAT DONE LOOKS LIKE" |
| F-11 | LOW | the three motivating situations are all real | Validation off by default; `nna8yz` at `substantially-complete` after a refused finalize (21.80 dollars, run `run-20260905T211011Z-3780617`); six lanes hand-integrated 2026-09-05 with no independent verification. | the item's own record |

## Proposed changes (ordered, validatable)

1. Re-measure the caller count by symbol and `ybkmzp`'s status, stopping if the precondition is unmet (E-01).
2. Decide what the verb verifies against and prove the chosen base is reachable (E-02).
3. Decide where a verdict lands, respecting plan immutability and addressing the re-run-until-happy hazard (E-03).
4. Decide the lane question consistently with isolation being the default (E-04).
5. Build the verb reusing prompt and schema, or record that it is not wanted with the economics (E-05).

## Deferred / out of scope (with reason)

- CHANGING THE IN-RUN VERIFIER in any way. It works, it is the thing being reused, and altering it would put two changes in one review.
- CHANGING THE `validate` DEFAULT. A measured maintainer ruling from 2026-08-31, and the per-host decision surface belongs to `tm2cz8`/`ybkmzp`.
- PER-ROLE OR PER-ACTION MODEL SELECTION for the standalone verifier. `kgpptv` owns the verifier-specific profile and `btot17` (graduated from `0k74my`) owns the general question, which carries its own blocking decision. A standalone verb must use whatever model resolution exists when it lands.
- WIRING THE AGY HOST, unless the decision requires it. The drivers are mid-unification (`5e4sb6`), and a second host surface doubles the review burden for a verb whose value is conditional. If only one host gets it, that must be DOCUMENTED, not inferred.
- ANY CHANGE TO AN `executed` PLAN'S RECORD. Immutable by policy; a negative verdict produces a corrective-IPD recommendation, never an in-place edit or a status change.
- FIXING THE MISSING-RECEIPT CASE that stranded `nna8yz`. That is `integearn`/`integpath` territory; this verb would make such a lane VERIFIABLE after the fact, not prevent the strand.
- RE-VERIFYING THE SIX HAND-INTEGRATED LANES from 2026-09-05. A use of the verb, not part of building or deciding it, and a maintainer's call about spending money on history.

## Scope check

- Over-scope: none. Under the not-wanted outcome this plan writes only a decision record.
- Scope-Paths justification: `agent_workflows/oc_runipd.py` holds `build_verifier_prompt` and the single execute-path caller, so it is where a new entry point must attach under a build outcome (E-05); `agent_workflows/runner_shared.py` is the correct home for logic both hosts might share, since `rununify` exists to de-duplicate the drivers and a host-local copy would enlarge that backlog; `.aw/records/specs` is where the decision lands under EVERY outcome and is the whole deliverable under not-wanted; `tests/test_standalone_verify.py` is new and carries the build outcome's tests. `agy_runipd.py` is deliberately NOT declared: wiring the second host is excluded unless the decision requires it, and declaring it would invite a change this plan does not want. Under the not-wanted outcome the two `agent_workflows/` paths and the test file may finish UNCHANGED, which is the expected outcome and not an incomplete item.
- Under-scope, stated rather than left as `none`: this plan does not change the in-run verifier, the `validate` default, model routing, the agy host, any `executed` plan's record, the missing-receipt strand, or the six historical lanes. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY. Under the not-wanted outcome the suite should be untouched, which is the expected result rather than a missing test.
- THE SYMBOL MEASUREMENTS (E-01): the caller count per host, located by NAME, and `ybkmzp`'s status, with the STOP if unmet.
- Under a build outcome: NEGATIVE PROOF that no second verifier prompt or outcome schema was written (show the searches), which is the item's hard constraint.
- Under a build outcome: a test that the standalone path composes the SAME prompt as the in-run path for equivalent inputs, since that identity is what makes the two verifiers trustworthy.
- Under a build outcome: proof the verb cannot change an `executed` plan's status or body, asserted rather than assumed.
- Under a build outcome: the verdict's destination demonstrated, and whether it is tracked or gitignored stated explicitly.
- Under the not-wanted outcome: the spec decision record, and `git status` over `agent_workflows/` proving no code changed.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

THE DECISION IS THE PRIMARY DELIVERABLE UNDER EITHER OUTCOME and must live in a spec under `.aw/records/specs`, because the item's four questions will otherwise be re-derived by the next person who wants this. Record what the verb verifies against, what it may write and where, whether it takes a lane, and the economics that decided whether it exists at all. A recorded NO is a real answer: an unused verb costs more than a documented decision.

Under a build outcome the verb is operator-facing and needs documentation stating plainly that it forms an OPINION and cannot change an `executed` plan, that a negative verdict leads to a corrective IPD, and WHICH HOST it works on if only one is wired. Write no em or en dashes in that prose.

Spec `25kzda` governs the deterministic run-and-verify surface and enumerates the `aw runs` leaves in its Section 3 command table, so ADDING a verb to that surface may amend a table an approved spec fixes. If E-05 builds a verb that lands there, the spec file MUST be declared in `Scope-Paths` before editing, per the spec-amendment rule, and the reason stated here. That declaration is deliberately not made in advance, since the not-wanted outcome amends nothing.

If the executor finds spec or documentation text asserting that verification can already be requested for an executed plan, that is a false claim and must be corrected in the same change, with the spec declared first.

## Open questions

### OQ-01: Is a standalone re-verify verb wanted at all, given the measured economics?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT AGENT-RESOLVABLE, AND THE ITEM RAISES IT ITSELF as its question 4. The evidence cuts both ways and neither side is a technical judgement. AGAINST: the maintainer measured that on the strong executor the verifier added only nits for roughly 33 percent extra cost, nobody currently passes `--validate`, and the in-run twin is off by default on the opencode host, so an after-the-fact verb may inherit a value proposition that is already declined. FOR: three concrete situations occurred where a human wanted an independent opinion and could not get one, including a 21.80 dollar lane (`nna8yz`) stranded at `substantially-complete` and six lanes hand-integrated with no independent verification. Whether that recovery value justifies the build is a spend decision about the maintainer's own workflow. E-01 through E-04 gather the material; nothing in E-05 may be built until this is answered.

### OQ-02: What does the verb verify against for a plan executed weeks ago?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DELIBERATELY LEFT OPEN because the obvious answer may be UNAVAILABLE, and that must be measured before it is chosen. The item's lean is the plan's recorded `base_head`, which is right in principle: verifying historical work against today's tree answers a different question. But the receipt carrying that base lives under gitignored `.aw/state/` and is CONSUMED on the clean finalize path, so a cleanly-finalized plan may have no readable base at all, and the run record that would substitute is also gitignored and absent from a lane worktree (`h9cn0y` measured that finalize receives no run id). E-02 must establish reachability before this is settled; if the base is genuinely unreachable, the honest options are an operator-supplied base or a verb that verifies something narrower, and both change what the verb MEANS. Non-blocking only because E-02 produces the measurement the answer needs.

### OQ-03: Where does a verdict land, and what stops an operator re-running until they like it?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN BECAUSE BOTH DESTINATIONS HAVE A REAL COST and the choice is about what the repository wants permanently recorded. A gitignored run record cannot be cited in a plan or seen by a reviewer, so a negative verdict effectively evaporates. A tracked record makes a machine-generated opinion part of permanent history, and the review tree's own README notes that only `/plan-review` writes records today, so this would widen what that tree contains. The second half of the question is the sharper one: if the verdict is discardable, an operator can re-run until satisfied, which makes the check untrustworthy in exactly the way `--no-verify` becoming routine was. E-03 must state what prevents that or record that nothing does; an honest "nothing does, and here is why that is acceptable" is a legitimate answer, but it must be written down rather than left implicit.

### OQ-04: Does the standalone verifier need its own lane?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES IF IT NEEDS A TREE AT ALL, and the landscape now makes that the consistent choice rather than a novel one: isolation is the DEFAULT for execute turns (`isolate_worktree` defaults True) and `worktree_lease` already owns allocation and teardown, so running a verification against the primary checkout while other agents work there would be the odd choice, not the safe one. The genuine sub-question E-04 must still answer is whether a full lane is warranted for a READ-MOSTLY turn, or whether a read-only checkout at the recorded base is cheaper and more correct, since the verifier's job is to form an opinion and a lane whose changes are discarded mainly costs time. What is settled is the direction: do NOT run it in the shared primary checkout.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the ACTUAL location of `build_verifier_prompt` in BOTH drivers found by symbol, and the caller count for each, with the surrounding context showing each caller sits inside the execute path and is gated on `validate`. State the line-number drift against this plan's citations. Paste `ybkmzp`'s current `- Status:` and directory, and if it has not executed, paste the STOP and confirm task groups 2 and 3 were not performed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the written answer for what the verb verifies against. Paste the ACTUAL evidence on reachability: whether a cleanly-finalized plan still has a readable `base_head`, checked against a real finalized plan rather than reasoned about, and whether its run record exists outside a lane. If the base is unreachable, paste that finding and the reshaped options.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the decided destination for a verdict and state explicitly whether it is TRACKED or GITIGNORED, with the consequence of that choice. Paste the answer to the re-run-until-happy hazard; if the answer is that nothing prevents it, paste the written justification rather than omitting the question. Confirm in one sentence that no mechanism was proposed that edits an `executed` plan.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the lane decision with its reasoning, and confirm it does not run in the shared primary checkout. If a read-only checkout was chosen over a full lane, paste the reasoning and state what the verifier may write into whatever tree it gets.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: state which OQ-01 outcome the maintainer chose. Under a BUILD outcome: paste NEGATIVE proof that no second verifier prompt or outcome schema exists (show the searches), the test proving the standalone path composes the SAME prompt as the in-run path, the assertion that an `executed` plan's status and body cannot change, and a statement of which host is wired. Under a NOT-WANTED outcome: paste the spec decision record including the economics, and `git status` over `agent_workflows/` proving no code changed. UNDER EITHER: paste the BARE `python3 -m pytest` summary lines before and after with the failure-set delta stated, and confirm the `validate` default is untouched.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN IS GATED TWICE, DELIBERATELY, AND BOTH GATES COME FROM THE ITEM ITSELF. It carries `- Item-Dependencies: executed:ybkmzp` because the item's own sequencing recommendation is "do `h7qsje` first" and `ybkmzp` is the child that actually wires the per-host verification decision into both drivers; `h7qsje` being `done` as a backlog item is NOT the same as that work landing, and `ybkmzp` is currently only `to-review`. And it carries a BLOCKING OQ-01 because the item's fourth question is whether the verb is wanted at all given that the verifier added only nits for roughly 33 percent cost on the strong executor and nobody passes `--validate` today.

E-01 IS SAFE TO PERFORM FIRST and is designed to enforce the first gate: it measures whether `ybkmzp` has executed and STOPS if not. Everything after E-01 is conditional. A recorded decision that the verb is NOT wanted is a legitimate completed outcome and is more valuable than an unused surface.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Re-locate every symbol by NAME, never by the line numbers cited here: this item's four coordinates were ALL stale by 130 to 230 lines at graduation, and both runner files are under concurrent edit by live runs. Do NOT write a second verifier prompt or outcome schema. Do NOT change the `validate` default, the in-run verifier, or any `executed` plan's record. Do NOT wire the agy host unless the decision requires it. If a verb is added to the `aw runs` surface, declare spec `25kzda` in `Scope-Paths` BEFORE editing it. Paste ACTUAL command output. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the reachability measurement for the verification base and the explicit tracked-versus-gitignored statement for the verdict's destination.
