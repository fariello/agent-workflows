# IPD: Make the no-known-bugs release rule durable instead of oral

- Date: 2026-09-11
- Kind: orchestrator
- Concern: The maintainer's rule that EVERY BUG BLOCKS THE NEXT RELEASE ("We don't ship known bugs") is recorded NOWHERE. It exists only in conversation, so every agent must rediscover or remember it, and measurably they do not: live bug-kind backlog items carry no release gate, including two filed by the agent authoring this Set hours after being told the rule. RE-MEASURED AT REVIEW (2026-09-12, HEAD `9582c659`): the oral-rule claim HOLDS EXACTLY (the grep across `AGENTS.md`, `DECISIONS.md`, `GUIDING_PRINCIPLES.md`, `.aw/records/backlog/README.md`, `CONTRIBUTING.md` and `RELEASING.md` still returns nothing), but every COUNT has moved and the direction is favourable: 196 items total (authored 187), 112 `Work-Kind: bug` (103), 68 live (60), 46 gated (32), and 22 GATELESS (28), split 10 `open`, 11 `graduated`, 1 `blocked`. Do not re-quote these either; E-01 re-measures.
- Scope: Make the rule survive without anyone remembering it, in the three places that make a rule hold here: write it down where it is discoverable, apply it at creation so the default is correct, and enforce it in the checker so drift cannot accumulate silently. Then backfill the existing violations. Does NOT change what counts as a bug, does NOT change the release record's own contract, and does NOT gate any non-bug work-kind.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Set: nobugship
- Order: 0
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: qmgn12
- Blocks-Release: next

## Workflow history

- 2026-09-12 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 (BLOCKER, OPEN and escalated to blocking OQ-03), PR-002..PR-007 FIXED; readiness `no-go` because one blocking question remains. Record: `.aw/records/reviews/20260911-nobugship-00-qmgn12-make-the-no-known-bugs-release-rule-durable-instead-of-oral.review.md`. `aw ipd lint --phase author` CONFORMING (clean, 0 findings) on this plan and on all three children before semantic review. DISCLOSURE: same agent/model family authored this Set, so treat as a near-self-review; its value rests on what was EXECUTED. EIGHT things were measured rather than recalled: the oral-rule grep re-run verbatim across six files; all five population counts recomputed from disk; the graduation leak recomputed per-item; the shipped `check_release_gate_consistency` predicate DRIVEN on the live tree; the same predicate driven again in a THROWAWAY COPY after backfilling one item, which is how the blocker was found; the gate spelling tallied across all gated items; the release record's `next` resolution confirmed; and the terminal-plan edit policy read.
  THE SET'S THESIS IS CORRECT AND ITS THREE-PART SHAPE IS RIGHT. The rule really is written nowhere, and the graduation leak reproduces EXACTLY as authored: 11 of 11 graduated gateless bugs have a plan carrying their `- From-Backlog:` and 0 of 11 of those plans carry a gate. Write-it-down, default-at-creation, enforce-and-backfill is the right decomposition and none of it was changed.
  THE BLOCKER IS THAT THE BACKFILL DETONATES A SHIPPED ERROR RULE, and this was proven by execution rather than reasoned. `check.from-backlog-gate-mismatch` (ERROR, exit-blocking, `check_engine.py:2226-2241`) fires when a `From-Backlog` carrier's gate differs from its item's. Child 03 CITES that rule as precedent for its own registration and never notices that its backfill is what trips it: adding `Blocks-Release: next` to the 11 graduated items creates a mismatch against 13 carrier plans, and 2 of those 13 sit in `executed/`, which AGENTS.md forbids editing in place. Measured in a throwaway copy: backfilling ONE item (`t156g1`) immediately produced one `check.from-backlog-gate-mismatch` against a plan in `executed/`. So the Set as sequenced cannot reach a clean checker by any route it authorizes, and its own completion criterion 4 plus V-02's `aw check backlog` clean are unreachable. Escalated as blocking OQ-03 with three costed options.
- 2026-09-11 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored after the maintainer asked "I think I've said before that every bug is blocking for next. We don't ship known bugs. How do we ensure that approach persists?" THE ANSWER TO THEIR QUESTION IS THAT IT DOES NOT PERSIST, and the evidence is this session. MEASURED at HEAD `2ff2b1b1`: `grep` for the rule across `AGENTS.md`, `DECISIONS.md`, `GUIDING_PRINCIPLES.md` and `.aw/records/backlog/README.md` returns NOTHING, so the rule is oral. Of 187 backlog items, 103 are `Work-Kind: bug`; 60 of those are live (`open`/`blocked`/`graduated`); and 28 of the 60 carry no `- Blocks-Release:`. TWO OF THE 28 WERE FILED BY THIS AGENT TODAY (`kyb0v5`, `mqmlug`), hours after the maintainer stated the rule in this same session, which is the sharpest available evidence that memory and loaded context are not sufficient mechanisms. A SECOND LEAK WAS FOUND WHILE MEASURING: of the 11 graduated bugs among the 28, ALL 11 have a plan carrying `- From-Backlog:` and NONE of those plans carries `- Blocks-Release:`, so the gate is also lost at the graduation handoff rather than only at creation. That is why child 02 covers preservation as well as defaulting.

## Goal

Make "no known bugs ship" a property the tooling maintains, so the rule holds when nobody remembers it, and make the current violation count visible rather than latent.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: sequence the Set and re-establish its premise

- [ ] E-01 RE-MEASURE THE VIOLATION POPULATION BEFORE ANY CHILD RUNS, because every count in this Set moves as agents file items. RECORD: the total backlog count, the `Work-Kind: bug` count, the live subset (`open`/`blocked`/`graduated`), how many of those carry `- Blocks-Release:`, and how many do not. Authored figures: 187 / 103 / 60 / 32 / 28; RE-MEASURED AT REVIEW (2026-09-12, HEAD `9582c659`): 196 / 112 / 68 / 46 / 22. Both sets are already historical; derive your own. ALSO re-measure the graduation leak: for each live gateless bug that is `graduated`, whether a plan carries its `- From-Backlog:` and whether THAT plan carries a gate (authored 11 of 11 have a plan, 0 of 11 have a gate; re-measured at review, IDENTICAL, so this is the Set's most durable finding).
  DO NOT DERIVE THESE FROM THIS PLAN. The whole reason this Set exists is that a stated rule went unchecked; a stated count deserves the same suspicion.
  MEASURE THE COLLISION POPULATION TOO, which review found and which the authored item omitted: for every live gateless bug you intend to backfill, enumerate EVERY plan and spec carrying its `- From-Backlog:`, and record each carrier's own `- Blocks-Release:` and its DIRECTORY. That set is what `check.from-backlog-gate-mismatch` will flag the moment the backfill lands (PR-001, blocking OQ-03), and a carrier in `executed/` cannot be brought into agreement by editing it. At review the count was 13 carriers, 2 of them terminal. Report it to child 03 explicitly rather than letting it discover the mismatch mid-backfill.
  - Depends on: none
  - Expected outcome: a recorded measurement with the commands that produced it, an explicit statement of whether child 03's backfill population differs from the review figure of 22, and the per-carrier collision table with each carrier's gate and directory.
  - Execution state: pending

- [ ] E-02 RETIRE THIS ORCHESTRATOR ONLY WHEN ALL THREE CHILDREN ARE `executed`, carrying no work of its own beyond E-01. Order 01 (write it down) is independent. Order 02 (default at creation) and Order 03 (enforce plus backfill) must BOTH land after 01, because the written rule is what they cite as their authority, and 03 should land LAST so the backfill happens once the default is in place and cannot immediately re-diverge.
  DO NOT DISPATCH ORDER 03 UNTIL OQ-03 IS ANSWERED. Its backfill is what trips the shipped `check.from-backlog-gate-mismatch` rule, and the answer decides whether the carriers are co-updated, whether the rule is taught a graduated-item exception, or whether the two terminal carriers are exempted by a recorded decision. Orders 01 and 02 are unaffected by that question and may proceed.
  IF THE RUNNER REFUSES THE RETIREMENT, THAT IS NOT A RUN FAILURE: retirement is gated on every child being `executed` and on nothing else qualifying. Report the reason it recorded rather than forcing the transition.
  - Depends on: E-01
  - Expected outcome: all three children `executed` with their own evidence, and this parent transitioned without performing any child's work; any refusal reported verbatim.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | Id | Title | Depends on |
|---|---|---|---|
| 01 | `zqs0px` | Record the rule in the contributor rules and the decisions log | none |
| 02 | `di08i9` | Default the gate on a bug at creation and preserve it through graduation | `executed:zqs0px` |
| 03 | `rgaasb` | Enforce it in `aw check` and backfill the existing violations | `executed:di08i9` (AND OQ-03 answered) |

ORDER 03 CARRIES AN UNRESOLVED PRECONDITION BEYOND ITS DEPENDENCY EDGE. Its backfill collides with the shipped `check.from-backlog-gate-mismatch` rule (PR-001), so the edge alone does not make it runnable; OQ-03 must be answered first. The dependency metadata is CORRECT as written and was deliberately not changed by review: the collision is not an ordering problem between children, it is a missing decision about how the gate is propagated to carriers, and two of the affected carriers are immutable.

## Completion criteria (the whole Set is done only when)

1. The rule is stated in a tracked, discoverable place and cited by the code that enforces it.
2. `aw backlog new --work-kind bug` produces an item carrying a release gate without the author naming one.
3. A graduation from a gated bug produces a plan that carries the gate, or refuses.
4. `aw check` reports a live bug with no gate, and CI fails on it.
5. The backfill population is zero, or every remaining item carries an explicitly recorded exemption.
6. NO NEW `check.from-backlog-gate-mismatch` FINDING SURVIVES THE BACKFILL. This is the criterion PR-001 exists to protect and it is NOT implied by criterion 5: an item can be correctly gated while its `From-Backlog` carrier is not, which is precisely what the backfill creates. Measured at review, gating the 11 graduated items would newly flag 13 carriers, 2 of them in `executed/`. Whatever OQ-03 decides, the end state must be a checker with no new mismatch, reached without editing a plan in a terminal directory.
7. The bare suite passes, with the actual summary pasted against a baseline established BEFORE the first edit.

## Cross-IPD validation

Child 03's enforcement must be exercised against an item created by child 02's default, proving the two agree rather than each being tested in isolation. Child 01's written rule must be the text child 03's refusal message points to.

THE TWO RULES MUST BE EXERCISED TOGETHER, NOT SEPARATELY, which review found is the gap that hides PR-001. Child 03 adds a rule requiring a live bug to carry a gate, and a rule ALREADY SHIPS requiring a `From-Backlog` carrier's gate to MATCH its item's (`check.from-backlog-gate-mismatch`, ERROR, `check_engine.py:2226-2241`). Satisfying the new rule on a graduated item is what VIOLATES the old one. So the cross-check must run BOTH over the tree after the backfill and show zero findings from EACH, on the same tree state, in one command. Testing the new rule alone would report success while the sweep is red.

RUN THE COLLISION EXPERIMENT IN A THROWAWAY COPY BEFORE TOUCHING THE REAL TREE. Review did exactly this (copy the repo, backfill ONE graduated item, call `check_engine.check_release_gate_consistency`) and it surfaced the blocker in one step: backfilling `t156g1` produced `check.from-backlog-gate-mismatch` against a plan in `executed/`. Repeat that cheap experiment at execution time to confirm OQ-03's chosen remedy actually clears it, rather than discovering it mid-backfill across 22 items in a shared checkout.

## Deferred / out of scope (with reason)

- CHANGING WHAT COUNTS AS A BUG. `Work-Kind` is an author's classification and this Set does not second-guess it. A defect mislabelled `chore` escapes the gate, and that is a real limit stated honestly rather than papered over; see OQ-02.
- GATING OTHER WORK KINDS. The maintainer's rule is about bugs. `feature`, `chore`, `followup` and `security` are untouched, though `security` is arguably a stronger case; raised as OQ-01 rather than assumed.
- THE RELEASE RECORD'S OWN CONTRACT. `next` already resolves to the single `planned` release (`f33nrj`, version 2.0.0; RE-VERIFIED at review). This Set consumes that and does not change it. Note also that every one of the 86 gated backlog items spells the gate as the literal `next` rather than an id6 (tallied at review), so the backfill should use `next` for consistency and no id6 spelling needs supporting.
- WEAKENING `check.from-backlog-gate-mismatch`. Listed here so it is a deliberate exclusion rather than a tempting shortcut: option (d) in OQ-03 would blunt the shipped ERROR rule that catches a dropped graduation handoff, which is the SAME class of leak this Set discovered in its own corpus. If OQ-03 is answered any other way, this stays out of scope.
- RETROSPECTIVELY GATING BUGS ALREADY `done`. Only live items are in scope; a closed bug shipped or did not, and rewriting its gate now would assert a history that did not happen.

## Scope check

- Over-scope: none. This parent declares only the plans tree and performs no code change; each child declares its own paths.
- Under-scope: the Set does not detect a defect filed under a non-bug kind, and does not decide the `security` question (both above). IT ALSO DOES NOT, AS AUTHORED, RECONCILE THE `From-Backlog` CARRIERS ITS OWN BACKFILL PUTS INTO VIOLATION (PR-001, blocking OQ-03). Child 03's `- Scope-Paths:` declares `agent_workflows/check_engine.py`, `tests/test_bug_gate_check.py` and `.aw/records/backlog` and NOT the plans tree, so under option (a) or (c) that declaration must grow before it can co-update a carrier. That is a genuine gap rather than deliberate exclusion.

## Required tests / validation

Each child owns its tests. Establish the suite baseline by running `python3 -m pytest` bare BEFORE the first edit and paste it. FOR REFERENCE ONLY, review measured it bare at HEAD `9582c659`: `5971 passed, 3 skipped, 2 xfailed`. Do NOT quote that as your baseline; re-measure and judge on the failure-SET delta, because an unverified number is the failure mode this Set exists to correct. Run the suite BARE: the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`, so adding `-n0` or a second `-q` makes the run slower and suppresses the summary line the contract requires you to paste.

ALSO ESTABLISH A CHECKER BASELINE, not only a suite baseline, because this Set's risk is in the sweep rather than in pytest. Before the first edit, record the finding count of `check.from-backlog-gate-mismatch` (review measured ZERO on the live tree) and the total counts from `aw check backlog` and `aw check plans`. The Set's own completion criterion 6 is a statement about that delta.

## Spec / documentation sync

Child 01 performs the documentation change and declares its paths. MEASURED AT REVIEW, so it is no longer an open question whether the rule is already written somewhere: the grep across `AGENTS.md`, `DECISIONS.md`, `GUIDING_PRINCIPLES.md`, `.aw/records/backlog/README.md`, `CONTRIBUTING.md` and `RELEASING.md` returns NOTHING for "don't ship known bugs", "every bug blocks", or "no known bugs", so the rule is genuinely oral and child 01 ADDS text rather than reconciling a contradiction. Child 01 must still check whether a SPEC owns release-gate policy, which review did not exhaust.

ONE DOCUMENTED CONTRACT IS ADJACENT AND MUST NOT BE CONTRADICTED: `AGENTS.md`'s "Release gates" section already defines `Blocks-Release` and states the close-legitimacy predicate, and it distinguishes `Blocks-Release` (an item gates a release) from `Blocked-By` (the item's own state). Child 01's new rule is a POLICY about which items must carry that field, not a change to the field's meaning, and it should be written so that distinction stays intact.

## Open questions

### OQ-01: Should `security` also gate the next release automatically?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: RAISED SO THE OMISSION IS DELIBERATE RATHER THAN AN OVERSIGHT. The maintainer's stated rule is about bugs; a `security` item is arguably a stronger case for never shipping, and treating it as ungated while a low-priority bug is gated would be hard to defend. But extending a rule the maintainer did not state is exactly the kind of inference that produced the misrecorded optionality this session already had to correct, so it is asked rather than assumed. Non-blocking because the Set is coherent for bugs alone and adding a second kind later is a one-line change to whatever predicate child 03 builds. Measured at authoring: 1 live `security` item exists, so the immediate impact is small either way.

### OQ-02: Does a defect filed as `chore` or `followup` escape the gate, and is that acceptable?

- Blocking: no
- Status: open
- Owner: this plan's executor for the measurement, the maintainer only if the leak is large
- Resolution or deferral rationale: RESOLVE BY MEASURING, THEN REPORT. The gate keys on `Work-Kind`, which is an author's judgement, so a genuine defect filed as `chore` is invisible to it. That is a real limit and must be stated in child 01's written rule rather than discovered later. The executor should sample the live `chore` and `followup` items for ones whose summary describes a defect and report the count; if it is small the limit is acceptable and the written rule simply names it, and if it is large the classification itself needs attention, which is a different piece of work. Non-blocking because the gate is a strict improvement over nothing regardless of the leak's size.

### OQ-03: Backfilling a graduated bug's gate violates the SHIPPED `from-backlog-gate-mismatch` rule, and two affected carriers are immutable. How is the gate propagated?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: MEASURED BY EXECUTION, NOT PREDICTED, WHICH IS WHY IT IS BLOCKING. `check.from-backlog-gate-mismatch` ships today at ERROR severity in the exit-blocking sweep (`check_engine.py:2226-2241`, registered `:105-124` under `I-07`) and fires whenever a plan or spec carrying `- From-Backlog: <item>` has a `- Blocks-Release:` that DIFFERS from that item's. Child 03 cites this very rule family as the precedent for its own registration and does not notice that its backfill is what trips it. VERIFIED IN A THROWAWAY COPY of the repo at review: adding `- Blocks-Release: next` to graduated item `t156g1` and calling the shipped predicate immediately produced one `check.from-backlog-gate-mismatch` naming plan `5wtzqv`, which sits in `executed/`. Enumerated across the whole population, gating the 11 graduated gateless bugs would newly flag 13 carrier plans: 11 in `pending/` (`1f7xno`, `9kmbr0`, `lyo1tz` all from item `cnwy8g`, plus `76w6mq`, `akzy45`, `i1hlgx`, `k9awrq`, `m867ox`, `vdabn5`, `yeh7gc`, `zexed1`) and 2 in `executed/` (`5wtzqv` from `t156g1`, `h9cn0y` from `hyx1dg`).
  THE TERMINAL PAIR IS THE PART THAT HAS NO ROUTE INSIDE THE SET'S CURRENT AUTHORITY. AGENTS.md is explicit: "Do NOT add commits to a plan already in `.aw/records/plans/executed/`; close a post-execution gap with a new corrective IPD, not an in-place edit." So the obvious remedy (co-update every carrier's gate) is available for the 11 pending carriers and FORBIDDEN for the 2 terminal ones. Meanwhile completion criterion 4 and V-02's "paste `aw check backlog` clean" are unreachable while any mismatch stands, so the Set as sequenced cannot finish by any route it authorizes.
  FOUR OPTIONS, EACH COSTED. (a) CO-UPDATE THE PENDING CARRIERS AND EXEMPT THE TERMINAL PAIR BY RECORDED DECISION: child 03 adds `- Blocks-Release: next` to the 11 pending plans and records why the 2 terminal ones are left, ideally by having the rule skip a carrier in a terminal directory (a defensible narrowing: a finished plan's gate is history, not a live claim). Cost: child 03's `Scope-Paths` must grow the plans tree, and the rule gains a directory-aware condition. Benefit: the sweep goes clean, no immutable file is touched, and the narrowing is independently correct. (b) NARROW THE NEW RULE TO `open`/`blocked` AND LEAVE `graduated` ITEMS UNGATED, on the ground that a graduated item's gate is meant to live on its plan (the handoff contract). Cost: 11 real bugs stay ungated and the leak this Set discovered goes unfixed, which contradicts its own concern statement. Benefit: no collision at all. (c) BACKFILL THE GATE ONTO THE PLANS INSTEAD OF THE ITEMS for graduated bugs, matching the documented handoff shape where the plan is the gate carrier. Cost: the 2 terminal carriers still cannot be edited, so it collapses into (a) for those. Benefit: closest to the existing `From-Backlog` contract. (d) TEACH THE MISMATCH RULE THAT AN ITEM-GATE WITHOUT A CARRIER-GATE IS A ONE-WAY OK, flagging only a CONFLICTING pair. Cost: weakens a shipped ERROR rule for every future case, not just this one, and the rule exists precisely to catch a dropped handoff. Benefit: no file edits anywhere.
  RECOMMENDATION (a), because it fixes the leak the Set exists to fix, touches no immutable artifact, and the directory-aware narrowing it needs is defensible on its own terms rather than being a special case carved for this Set. (d) is the one to avoid: it would blunt the exact rule that would otherwise have caught this Set's own graduation leak.
  DELIBERATELY NOT DONE HERE: review did not edit child 03, did not widen any `Scope-Paths`, and did not touch the shipped rule. Only this orchestrator was in the review's scope ledger, and choosing among four options that trade off a shipped contract against a backfill is the maintainer's call.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: the runner retires an orchestrator from child status. Do not fabricate an independent implementation checkpoint for this file.

- [ ] V-01 validates E-01
  - Required evidence: paste the re-measured counts with the exact commands, and state how they differ from BOTH prior readings (authored 187/103/60/32/28; review 196/112/68/46/22). Paste the graduation-leak re-measurement with its per-item result. If child 03's population differs from the review figure of 22, paste the statement given to that child. ALSO paste the per-carrier collision table required by E-01: every plan or spec carrying a to-be-backfilled item's `- From-Backlog:`, with that carrier's own gate and its DIRECTORY, and state how many sit in a terminal directory. A measurement that omits the collision table is a FAILED validation, because it is the input OQ-03's chosen remedy has to be applied to.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste each child's `- Status:` line showing all three `executed`; paste `git diff --stat` over THIS parent's own commits showing it touched no file under `agent_workflows/` or `tests/`; and paste the live-gateless-bug count showing zero (or each remaining item with its recorded exemption).
    ON THE CHECKER, REQUIRE A DELTA AND NAME BOTH RULES. Paste `aw check backlog` AND `aw check plans`, each compared against a baseline captured BEFORE the first edit, and state explicitly that `check.from-backlog-gate-mismatch` count is unchanged from that baseline (review measured it at ZERO on the live tree, so any occurrence after the backfill is NEW and is PR-001 materializing). Do not merely assert "clean": `aw check plans` carries pre-existing findings unrelated to this Set, so a clean claim would be either false or achieved by editing another party's artifacts, which the shared-checkout rule forbids.
    ALSO paste OQ-03's recorded answer and which option it selected, plus the throwaway-copy re-run of the collision experiment showing the chosen remedy clears it.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and carries `- Readiness: no-go`. It must NOT be executed: blocking OQ-03 is open, so `aw ipd lint` refuses this plan at every checkpoint until the maintainer answers it, and a human must then set it `approved`. Answer it with `/askme`; an executor must not decide it mid-run, because two of the four options change a shipped ERROR rule's behavior.

It carries `- Blocks-Release: next` because a Set whose purpose is to stop known bugs shipping should itself gate the release it protects; shipping 2.0.0 with 22 ungated live bugs (re-measured at review) is the outcome this Set exists to prevent.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped, never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. This orchestrator carries E-01 deliberately (a premise check no child covers) and must not absorb any child's work.

FOUR CORRECTIONS FROM REVIEW THAT MUST NOT BE RE-INHERITED:

1. Do NOT re-quote the authored counts 187/103/60/32/28. Re-measured at review: 196/112/68/46/22, and both readings are now historical. The graduation leak (11 of 11 with a plan, 0 of 11 with a gate) reproduced EXACTLY and is the Set's durable finding.
2. Do NOT backfill a graduated item's gate without settling OQ-03 first. It creates a `check.from-backlog-gate-mismatch` ERROR against 13 carriers, 2 of them in `executed/` where in-place edits are forbidden. Proven by experiment, not inferred.
3. Do NOT require `aw check plans` or `aw check backlog` to be CLEAN. Require a per-rule DELTA against a baseline captured before the first edit, and never reduce a count by editing another party's artifact.
4. Do NOT park a deliverable on this orchestrator beyond E-01's premise check. The runner retires an orchestrator with no agent turn and skips its E/V checkpoint, so anything parked here is marked done having never been performed. If the Set needs a step no child covers, ADD A CHILD for it.
