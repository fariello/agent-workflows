# IPD: Make the no-known-bugs release rule durable instead of oral

- Date: 2026-09-11
- Kind: orchestrator
- Concern: The maintainer's rule that EVERY BUG BLOCKS THE NEXT RELEASE ("We don't ship known bugs") is recorded NOWHERE. It exists only in conversation, so every agent must rediscover or remember it, and measurably they do not: 28 of the 60 live bug-kind backlog items carry no release gate, including two filed by the agent authoring this Set hours after being told the rule.
- Scope: Make the rule survive without anyone remembering it, in the three places that make a rule hold here: write it down where it is discoverable, apply it at creation so the default is correct, and enforce it in the checker so drift cannot accumulate silently. Then backfill the existing violations. Does NOT change what counts as a bug, does NOT change the release record's own contract, and does NOT gate any non-bug work-kind.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: none
- Status: to-review
- Set: nobugship
- Order: 0
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: qmgn12
- Blocks-Release: next

## Workflow history

- 2026-09-11 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored after the maintainer asked "I think I've said before that every bug is blocking for next. We don't ship known bugs. How do we ensure that approach persists?" THE ANSWER TO THEIR QUESTION IS THAT IT DOES NOT PERSIST, and the evidence is this session. MEASURED at HEAD `2ff2b1b1`: `grep` for the rule across `AGENTS.md`, `DECISIONS.md`, `GUIDING_PRINCIPLES.md` and `.aw/records/backlog/README.md` returns NOTHING, so the rule is oral. Of 187 backlog items, 103 are `Work-Kind: bug`; 60 of those are live (`open`/`blocked`/`graduated`); and 28 of the 60 carry no `- Blocks-Release:`. TWO OF THE 28 WERE FILED BY THIS AGENT TODAY (`kyb0v5`, `mqmlug`), hours after the maintainer stated the rule in this same session, which is the sharpest available evidence that memory and loaded context are not sufficient mechanisms. A SECOND LEAK WAS FOUND WHILE MEASURING: of the 11 graduated bugs among the 28, ALL 11 have a plan carrying `- From-Backlog:` and NONE of those plans carries `- Blocks-Release:`, so the gate is also lost at the graduation handoff rather than only at creation. That is why child 02 covers preservation as well as defaulting.

## Goal

Make "no known bugs ship" a property the tooling maintains, so the rule holds when nobody remembers it, and make the current violation count visible rather than latent.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: sequence the Set and re-establish its premise

- [ ] E-01 RE-MEASURE THE VIOLATION POPULATION BEFORE ANY CHILD RUNS, because every count in this Set moves as agents file items. RECORD: the total backlog count, the `Work-Kind: bug` count, the live subset (`open`/`blocked`/`graduated`), how many of those carry `- Blocks-Release:`, and how many do not. Authored figures: 187 / 103 / 60 / 32 / 28. ALSO re-measure the graduation leak: for each live gateless bug that is `graduated`, whether a plan carries its `- From-Backlog:` and whether THAT plan carries a gate (authored: 11 of 11 have a plan, 0 of 11 have a gate).
  DO NOT DERIVE THESE FROM THIS PLAN. The whole reason this Set exists is that a stated rule went unchecked; a stated count deserves the same suspicion.
  - Depends on: none
  - Expected outcome: a recorded measurement with the commands that produced it, and an explicit statement of whether child 03's backfill population differs from 28.
  - Execution state: pending

- [ ] E-02 RETIRE THIS ORCHESTRATOR ONLY WHEN ALL THREE CHILDREN ARE `executed`, carrying no work of its own beyond E-01. Order 01 (write it down) is independent. Order 02 (default at creation) and Order 03 (enforce plus backfill) must BOTH land after 01, because the written rule is what they cite as their authority, and 03 should land LAST so the backfill happens once the default is in place and cannot immediately re-diverge.
  - Depends on: E-01
  - Expected outcome: all three children `executed` with their own evidence, and this parent transitioned without performing any child's work.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | Id | Title | Depends on |
|---|---|---|---|
| 01 | `zqs0px` | Record the rule in the contributor rules and the decisions log | none |
| 02 | `di08i9` | Default the gate on a bug at creation and preserve it through graduation | `executed:zqs0px` |
| 03 | `rgaasb` | Enforce it in `aw check` and backfill the existing violations | `executed:di08i9` |

## Completion criteria (the whole Set is done only when)

1. The rule is stated in a tracked, discoverable place and cited by the code that enforces it.
2. `aw backlog new --work-kind bug` produces an item carrying a release gate without the author naming one.
3. A graduation from a gated bug produces a plan that carries the gate, or refuses.
4. `aw check` reports a live bug with no gate, and CI fails on it.
5. The backfill population is zero, or every remaining item carries an explicitly recorded exemption.
6. The bare suite passes, with the actual summary pasted against a baseline established BEFORE the first edit.

## Cross-IPD validation

Child 03's enforcement must be exercised against an item created by child 02's default, proving the two agree rather than each being tested in isolation. Child 01's written rule must be the text child 03's refusal message points to.

## Deferred / out of scope (with reason)

- CHANGING WHAT COUNTS AS A BUG. `Work-Kind` is an author's classification and this Set does not second-guess it. A defect mislabelled `chore` escapes the gate, and that is a real limit stated honestly rather than papered over; see OQ-02.
- GATING OTHER WORK KINDS. The maintainer's rule is about bugs. `feature`, `chore`, `followup` and `security` are untouched, though `security` is arguably a stronger case; raised as OQ-01 rather than assumed.
- THE RELEASE RECORD'S OWN CONTRACT. `next` already resolves to the single `planned` release (`f33nrj`, version 2.0.0, verified). This Set consumes that and does not change it.
- RETROSPECTIVELY GATING BUGS ALREADY `done`. Only live items are in scope; a closed bug shipped or did not, and rewriting its gate now would assert a history that did not happen.

## Scope check

- Over-scope: none. This parent declares only the plans tree and performs no code change; each child declares its own paths.
- Under-scope: the Set does not detect a defect filed under a non-bug kind, and does not decide the `security` question (both above).

## Required tests / validation

Each child owns its tests. Establish the suite baseline by running `python3 -m pytest` bare BEFORE the first edit and paste it; no baseline figure is stated here deliberately, because an unverified number is the failure mode this Set exists to correct.

## Spec / documentation sync

Child 01 performs the documentation change and declares its paths. NOT YET MEASURED at authoring: whether any spec states a release-gating rule that this addition would contradict or duplicate. Child 01 must check rather than assume, and if a spec owns release-gate policy the rule belongs there too.

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

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: the runner retires an orchestrator from child status. Do not fabricate an independent implementation checkpoint for this file.

- [ ] V-01 validates E-01
  - Required evidence: paste the re-measured counts with the exact commands, and state whether they differ from 187/103/60/32/28. Paste the graduation-leak re-measurement with its per-item result. If child 03's population differs from 28, paste the statement given to that child.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste each child's `- Status:` line showing all three `executed`; paste `git diff --stat` over THIS parent's own commits showing it touched no file under `agent_workflows/` or `tests/`; paste `aw check backlog` clean; and paste the live-gateless-bug count showing zero (or each remaining item with its recorded exemption).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until it has been reviewed and a human sets it `approved`.

It carries `- Blocks-Release: next` because a Set whose purpose is to stop known bugs shipping should itself gate the release it protects; shipping 2.0.0 with 28 ungated live bugs is the outcome this Set exists to prevent.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped, never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. This orchestrator carries E-01 deliberately (a premise check no child covers) and must not absorb any child's work.
