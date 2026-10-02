# IPD: Gate the denypush Set on its maintainer decision instead of letting it execute with the decision unanswered

- Date: 2026-10-01
- Kind: child
- Concern: Backlog `wcbpqf` is the DURABLE CARRIER for three maintainer decisions the `denypush` Set raises and cannot answer from repository evidence: (1) `l4vw9o` OQ-01, ship the port-denial capability at all or record the measurement and stop; (2) `pi3bk8` OQ-01, is `supports_deny_tcp_port` the right field name; (3) `x2dwu5` OQ-01, split spec `25kzda` 5.2's bullet into its two halves. THE DEFECT IS THAT FILING THE CARRIER DID NOT GATE ANYTHING, and it is measured, not predicted: all four `denypush` plans are `- Status: approved` (human-approved in commit `86486f1dc`), their `Item-Dependencies` are `none` / `executed:x2dwu5` / `executed:pi3bk8` with NO edge to `wcbpqf`, and `aw ipd lint --phase pre-execution` reports `l4vw9o` and `pi3bk8` CONFORMING today (driven). The pre-execution checkpoint only refuses an open question carrying `Blocking: yes` (`ipd_lint.check_checkpoint`, "unresolved blocking question at pre-execution") and all three are deliberately `Blocking: no`, correctly so per the 2026-09-10 ruling. So `aw oc run` will execute this Set, ship the capability under the un-ruled name, and close every carrier OQ as `executed`, after which `aw attention` classes them `done` and the decision window SHUTS having never been opened. That is the exact decay `wcbpqf` was filed to prevent, reproduced one layer up: the carrier records the question durably and nothing makes anyone answer it.
- Scope: IN: add ONE typed, shipped, dispatch-enforced dependency edge, `state:backlog:done:wcbpqf`, to the two `denypush` plans whose deliverables the decision actually changes (`l4vw9o` the ship/stop decision, `pi3bk8` the field name), written through `aw ipd dependencies set` so the value is canonicalized and validated rather than hand-edited; record on `wcbpqf` what closing it requires and which plans wait on it; and verify by driving `runner_shared.edge_satisfied` that the edge refuses while the item is `open` and releases when it is `done`. OUT: answering any of the three decisions (they are the human's, which is the premise of the carrier and of this plan); changing any plan's `- Status:`, `- Readiness:`, `- Approval:`, E-items, V-items, scope or prose; gating `x2dwu5` or `wzhe4n` (measured below: neither names the field and `x2dwu5` is records-only, so holding them would stop work the decision does not touch); any product code, probe, capability or spec edit, all of which belong to the Set's own children; and a general mechanism for the 29-question population of the same shape, which is deliberately CARRIED by backlog `hc6n7r` (filed at authoring) rather than built here.
- Scope-Paths: .aw/records/plans/pending/20260929-denypush-00-l4vw9o-decide-and-if-approved-build-a-landlock-backed-network-denia.ipd.md, .aw/records/plans/pending/20260929-denypush-02-pi3bk8-add-a-probed-supports-deny-remote-ssh-push-capability-provin.ipd.md, .aw/records/backlog/open/20260929-denypush-01-wcbpqf-decide-port-denial-capability-posture.backlog.md, .aw/records/backlog/open/20261001-denypush-01-hc6n7r-carrier-field-gates-nothing.backlog.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Work-Kind: followup
- Priority: low
- From-Backlog: wcbpqf
- Set: denypush
- Order: 4
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: d5ntkj

## Workflow history

- 2026-10-02 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: REJECT - NEEDS REPLAN; PR-001 (BLOCKER: the gate releases itself; this plan is the SOLE `From-Backlog: wcbpqf` carrier, so on execution `runner_shared.evaluate_backlog_close` returns close=True and `aw backlog set wcbpqf --status done` succeeds from `graduated`, both driven), PR-002 (HIGH: an unmet `state:backlog` edge on an approved plan REFUSES THE WHOLE RUN at `enforce_freeze_time_refusal` (`RUN-DEPENDENCY-UNSATISFIABLE`, spec z7nbn1 1.4), not a per-item `dependency-blocked` deferral, driven), PR-003 (HIGH: premises stale at HEAD ce551c597: `wcbpqf` and `hc6n7r` are `graduated`, `x2dwu5` is `executed`, Scope-Paths name `backlog/open/` paths that no longer exist), PR-004 (MEDIUM: `pi3bk8` OQ-01, the field name, is already resolved at review). Escalated as OQ-03..OQ-05. Plan body left as authored for the replacement author.
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored review-ready while graduating backlog `wcbpqf`. Authoring MEASURED the item's own premises and corrected two of them (F-05, F-06): the item says a rename "must be applied to ALL FOUR plans together, since a half-renamed Set would leave the spec naming a field that does not exist", but only TWO plans name the field (`l4vw9o` 5 hits, `pi3bk8` 11, `x2dwu5` and `wzhe4n` zero) and spec `25kzda` names it ZERO times, so the spec half of that sentence describes a state that does not exist yet. The correction makes the gate NARROWER than the item implies, which is why it is recorded rather than quietly applied.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the `denypush` Set actually WAIT for the decision its own plans say is the maintainer's, using the
typed dependency mechanism the repository already ships and already enforces at dispatch, so the
decision is answered BEFORE the capability ships under an un-ruled name rather than discovered after
the plans are terminal and unwritable.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: gate the two plans the decision changes

- [ ] E-01 Add the edge `state:backlog:done:wcbpqf` to orchestrator `l4vw9o`, through `aw ipd dependencies set l4vw9o state:backlog:done:wcbpqf --yes -m '<why>'`. USE THE VERB, NOT AN EDIT: it canonicalizes and validates every edge against the repository before writing, so a malformed, dangling, ambiguous or cyclic edge is refused rather than persisted, and its own `--help` states the value "persists on a same-status no-op transition", which is what keeps the edge from being dropped by a later `aw ipd set`. `l4vw9o` currently declares `- Item-Dependencies: none`, so the new value REPLACES `none` and the plan gains exactly one edge. Do NOT touch its `- Status: approved`, its `- Approval:` line, its `- Readiness:`, or any other field: the human approved this plan's CONTENT and this item changes only what it waits for.
  - WHY THE ORCHESTRATOR IS GATED AT ALL, given it performs no product change: its OQ-01 IS the ship-or-stop decision, so a `no-go` answer means the Set should not run, and the orchestrator is the one plan whose execution implies the whole Set ran. Gating it is what makes "record the measurement and stop" a reachable outcome rather than a sentence in a resolved question.
  - Depends on: none
  - Expected outcome: `l4vw9o` carries `- Item-Dependencies: state:backlog:done:wcbpqf`; `aw ipd lint --phase pre-execution` still reports it conforming (the edge is legal grammar, so the plan stays structurally valid); and `runner_shared.edge_satisfied` returns False for that edge while `wcbpqf` is `open`. Verified at authoring on a throwaway copy, so this is a reproduction and not a prediction: the identical call on `x2dwu5` rewrote `- Item-Dependencies: none` to `- Item-Dependencies: state:backlog:done:wcbpqf`, exit 0.
  - Execution state: pending

- [ ] E-02 Add the same edge to `pi3bk8`, PRESERVING its existing `executed:x2dwu5` edge, through `aw ipd dependencies set pi3bk8 executed:x2dwu5 state:backlog:done:wcbpqf --yes -m '<why>'`. THE VERB REPLACES THE WHOLE STATEMENT rather than appending to it (its `--help`: "replacing any existing value"), so BOTH edges must be passed in one call; passing only the new one would silently delete the ordering edge that makes the capability's honest description depend on the spec amendment landing first. Measured at authoring on a throwaway copy: the two-edge call yields `- Item-Dependencies: executed:x2dwu5, state:backlog:done:wcbpqf`, exit 0, with the existing edge intact.
  - WHY `pi3bk8` IS THE OTHER GATED PLAN: it is the plan that CREATES the field whose name is undecided. It names `supports_deny_tcp_port` 11 times and also names the rejected alternative `supports_deny_outbound_tcp_port`, so executing it is precisely the act that makes the un-ruled name real in shipped code, in `aw host capabilities` output, and in a test's `CONTRACT_FIELDS` tuple.
  - Depends on: none
  - Expected outcome: `pi3bk8` carries both edges in that order; its `- Status: approved` and every other field are byte-unchanged apart from the dependency line and the history record the verb appends; `aw ipd lint --phase pre-execution` reports it conforming.
  - Execution state: pending

- [ ] E-03 Record on backlog `wcbpqf`, via `aw backlog note`, (a) that `l4vw9o` and `pi3bk8` now declare `state:backlog:done:wcbpqf` and therefore cannot be dispatched until this item is `done`, and (b) the CORRECTED scope of the rename decision measured in F-05: the field name appears in TWO plans, not four, and in ZERO specs, so a rename is a two-file change today and the item's "ALL FOUR plans together" sentence overstates it. Do NOT change the item's `- Status:`, its `- Summary:`, or its three recorded decisions: the decisions are the human's and this plan only records what now waits on them. Use the tooled verb rather than editing the file, so the note lands as a conformant `## Workflow history` record.
  - Depends on: E-01, E-02
  - Expected outcome: a reader of `wcbpqf` learns, from the item itself, which plans are held and what a rename actually costs, without opening either plan. The item stays `open`, which is correct: it is `ready` in `aw attention` (`CLASS_MAPS['backlog']['open'] == 'ready'`, driven) and a human still has to answer it.
  - Execution state: pending

### Task group 2: file the general gap rather than build it

- [ ] E-04 VERIFY the already-filed carrier for the POPULATION this plan's mechanism does not cover, and do not build the mechanism here. Backlog `hc6n7r` was filed AT AUTHORING (`.aw/records/backlog/open/20261001-denypush-01-hc6n7r-carrier-field-gates-nothing.backlog.md`), not deferred to execution, because `check.ipd-uncarried-obligation` is registered `error` and refuses a Deferred row whose `- Carrier:` is prose rather than a bare id6 (driven at authoring: "expected a bare 6-char id6"). So this item CONFIRMS rather than creates: re-derive the population count, check it against the figure the item records, and append a `aw backlog note` record if the number has moved. The measured gap: 29 open questions across 23 pending plans carry a `- Carrier: <id6>` and ZERO are backed by a dependency edge to that carrier (driven by parsing every pending and reusable plan with `ipd_lint.parse` and comparing each open-and-carried OQ's carrier against the plan's own `Item-Dependencies` text). Do NOT add `- Blocks-Release:` to it: `wcbpqf` carries none, so inventing one would forge a gate.
  - WHY FILED AND NOT BUILT, stated because the opposite is tempting: a rule that turned all 29 into findings is a REPOSITORY-WIDE policy change affecting plans this lane did not author and whose authors chose `Blocking: no` deliberately. Shipping it inside a plan graduated from a Set-specific decision carrier would smuggle a corpus-wide gate past the review that such a change deserves.
  - Depends on: E-01, E-02
  - Expected outcome: `hc6n7r` is confirmed present and `open`, its recorded measurement is either re-confirmed or corrected by a tooled note, and the general gap demonstrably survives this plan reaching `executed/`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A TYPED DEPENDENCY EDGE IS THE SHIPPED WAY TO MAKE A PLAN WAIT, and `state:backlog:<status>:<id6>` is legal grammar: `ipd_schema.ITEM_DEP_TYPES` is `("ipd", "spec", "backlog")` and `_ITEM_DEP_STATE_STATUSES["backlog"]` is DERIVED from `backlog.STATUSES` (driven: `done` is admitted). So this plan adds no mechanism; it uses one.
- THE EDGE IS RE-CHECKED AT DISPATCH, not only at queue build, which is what makes it a real gate: `AGENTS.md` states "dependencies are RE-CHECKED AT DISPATCH ... and an unmet edge marks that one item `dependency-blocked` and continues instead of failing the run". So gating two plans does not break a queue containing them; it defers exactly those two.
- `aw ipd dependencies set` REPLACES the whole statement rather than appending (its `--help`: "replacing any existing value"), and a separate `aw ipd dependencies remove` exists for subtraction. E-02 passes both edges for this reason.
- A `--with-dependencies` EXPANSION WOULD REFUSE A BACKLOG TARGET, and this is written down rather than latent: the flag's own help says "PLAN TARGETS ONLY: a spec or backlog dependency target REFUSES, because the run manifest is built from the plans trees and has no queue entry for one". That refusal is about SELECTION EXPANSION, and the same help states every declared dependency "is enforced either way", so the gate this plan adds works without that flag and an operator who passes it gets a loud refusal rather than a silent bypass (F-04).
- THE PRE-EXECUTION CHECKPOINT GATES ONLY A BLOCKING QUESTION: `ipd_lint.check_checkpoint` emits "unresolved blocking question at pre-execution" for an OQ with `Blocking == "yes"` and `Status == "open"`, and nothing else in that phase reads open questions. `check_engine`'s own comment states the honest limit of that reuse: its "true catch rate is UNMEASURED, not perfect".
- A NON-BLOCKING OPEN QUESTION DOES NOT MAKE A PLAN NO-GO (maintainer ruling 2026-09-10, `qhy3i3` OQ-01, cited in several reviews in `.aw/records/reviews/`). This plan does NOT challenge that ruling: it does not change any `- Blocking:` field. It adds a dependency edge, which is a different mechanism and the one the repository provides for "wait for that".
- AN APPROVED PLAN'S CONTENT IS THE HUMAN'S; its dependency statement is tooled metadata. Cite code by SYMBOL or quoted string, never a bare line number (spec `ipd-structure-and-linting` Section 10.2, `IPD-C801`); every citation here names a symbol or quotes content.
- THE SUITE IS RUN BARE as `python3 -m pytest`; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-01 | THE SET CAN EXECUTE TODAY WITH ALL THREE DECISIONS UNANSWERED | All four `denypush` plans carry `- Status: approved` (commit `86486f1dc`, "chore(records): set status approved"); `aw ipd lint --phase pre-execution` on `l4vw9o` prints `◕ approved plan 20260929-denypush-00-l4vw9o [low] conforming`, exit 0 (driven) | This is the defect. Nothing holds the Set, so the capability can ship under an un-ruled name and the decision window closes silently. |
| F-02 | THE THREE CARRIER QUESTIONS ARE ALL NON-BLOCKING, SO THE ONE SHIPPED GATE CANNOT SEE THEM | Driven with `ipd_lint.parse`: `l4vw9o` OQ-01 and `x2dwu5` OQ-01 are each `Blocking='no'`, `Status='open'`, `Owner='maintainer'`, `Carrier='wcbpqf'`; `pi3bk8`'s three OQs are all `resolved` | The fix cannot be "mark them blocking": that would contradict the 2026-09-10 ruling and would also be a different claim about the questions. An independent waiting mechanism is needed, which is the dependency edge. |
| F-03 | THE EDGE REFUSES WHILE THE ITEM IS OPEN, MEASURED END TO END | `runner_shared.edge_satisfied` driven on the real repository with the parsed edge: returns `(False, "state:backlog:done:wcbpqf: backlog wcbpqf is 'open', needs exactly 'done'")`. Its `state:` branch requires the EXACT status and `check_engine.build_dependency_index` resolves `wcbpqf` to `('backlog', 'open', ...)` | The mechanism works and the refusal message NAMES the item and the required status, so an operator hitting it learns what to do. This is the plan's load-bearing claim and it is driven, not reasoned. |
| F-04 | THE GATE IS NOT BYPASSED BY `--with-dependencies` | That flag's help states a backlog target REFUSES (it expands SELECTION and the manifest is plans-only) and that every declared dependency "is enforced either way"; `expand_dependency_closure`'s own comment calls the non-plan refusal "a KNOWN, WRITTEN-DOWN GAP ... rather than a quiet narrowing" | An operator cannot accidentally dissolve the gate by asking for the dependency closure; they get a loud refusal naming the type. Worth stating because a silent bypass would make the gate theatre. |
| F-05 | THE ITEM OVERSTATES THE RENAME'S BLAST RADIUS, IN BOTH HALVES | `grep -c 'deny_tcp_port'` per plan: `l4vw9o` 5, `pi3bk8` 11, `x2dwu5` 0, `wzhe4n` 0. On spec `25kzda` (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`): 0 | `wcbpqf` says a rename "must be applied to ALL FOUR plans together, since a half-renamed Set would leave the spec naming a field that does not exist". Measured: TWO plans name it and the spec names it ZERO times, so the spec clause describes a future state. This is why E-01/E-02 gate two plans and not four, and E-03 records the correction. |
| F-06 | GATING `x2dwu5` WOULD STOP WORK THE DECISION DOES NOT TOUCH | `x2dwu5` is the records-only plan (its Goal: "No code behavior changes"), names the field zero times, and its own OQ-01 is the SPLIT question whose recommendation is already "keep the bullet, add the bounded prose", explicitly "correct either way" | Holding it would delay the measurement record, which is the one outcome EVERY branch of the ship/stop decision wants recorded. `wzhe4n` likewise names the field zero times and depends on `pi3bk8`, so it is held transitively without an edge of its own. |
| F-07 | THE CARRIER-TO-EDGE GAP IS A 29-INSTANCE POPULATION, NOT A ONE-OFF | Driven over every pending and reusable plan, EXCLUDING this one: 29 open questions across 23 plans carry a `- Carrier:` id6; for each, the carrier id6 was compared against the plan's own `Item-Dependencies` text and NONE declares a matching edge. Carriers resolve to a mix of `backlog` (`open` and `graduated`) and `plans` targets. Including this plan the figure is 30, since its own OQ-01 is carried and open | Backlog `hc6n7r` CARRIES this rather than this plan fixing it. A corpus-wide rule is a policy change touching 23 plans this lane did not author; shipping it here would bypass the review it deserves. The count is LIVE, which is why V-04 re-derives it instead of trusting this row. |
| F-08 | NO SHIPPED `check` RULE COVERS THIS | `check_engine.RULE_REGISTRY` has 56 rules (driven); the only question-adjacent ones are `check.review-decision-unescalated` (`warning`) and `check.ipd-carrier-finished-unverified` (`info`), neither of which asks whether a carried OPEN question gates its plan. `check.ipd-uncarried-obligation` is `error` but fires on an obligation with NO carrier, which is the opposite case: `wcbpqf` HAS carriers | Confirms the gap is real and names the two registries a future rule would join, which is what E-04's item must record so the next author does not re-derive it. |
| F-09 | THE RUNNER CLOSES A CARRIER OQ AS DONE WITHOUT IT BEING ANSWERED | `AGENTS.md`: the runner retires an orchestrator once every child is `executed`, and `attention_contract.CLASS_MAPS['backlog']` maps `done -> done` while `open -> ready` (driven). `l4vw9o` OQ-02 already records that the runner sets the source item `graduated` on verification | This is the decay path concretely: after the Set runs, the plans are terminal (and per D156 their records must not be rewritten), so the decision can no longer be applied to them. The gate must therefore act BEFORE execution, which is what a dispatch-time edge does. |
| F-10 | THE TOOLED WRITE PRESERVES THE APPROVAL AND THE OTHER EDGE | Driven on throwaway copies of the real plans: `aw ipd dependencies set x2dwu5 state:backlog:done:wcbpqf --yes` rewrote `none` to the edge (exit 0), and `aw ipd dependencies set pi3bk8 executed:x2dwu5 state:backlog:done:wcbpqf --yes` produced `executed:x2dwu5, state:backlog:done:wcbpqf` with `- Status: approved` intact; `aw ipd lint` then reported `conforming` at both `author` and `pre-execution` | E-01 and E-02 are executable exactly as written, and the verb does not disturb the human's approval. The two-edge call in E-02 is required because the verb replaces the statement. |

## Proposed changes (ordered, validatable)

1. Gate the orchestrator `l4vw9o` on `state:backlog:done:wcbpqf` through the tooled verb (E-01), because
   its OQ-01 is the ship-or-stop decision and its execution implies the whole Set ran.
2. Gate `pi3bk8` on the same edge while preserving `executed:x2dwu5` in one call (E-02), because it is
   the plan that makes the un-ruled field name real.
3. Record on `wcbpqf` which plans now wait on it and the corrected rename scope F-05 measured (E-03).
4. Confirm backlog `hc6n7r`, filed at authoring, still carries the 29-instance general gap, and correct
   its figure if the live population has moved (E-04). The gap is CARRIED, never fixed here.

## Deferred / out of scope (with reason)

- ANSWERING any of the three decisions. They turn on how a PARTIAL guarantee reads to an operator,
  which is a risk-appetite and public-contract judgement, and that is the premise of `wcbpqf` itself.
  - Carrier: wcbpqf
- A GENERAL MECHANISM connecting a `- Carrier:` field to an enforced edge, for the 29-question
  population F-07 measured. FILED AT AUTHORING rather than at execution, so this row cites a real id6
  instead of a promise: a prose placeholder here is refused by `check.ipd-uncarried-obligation`
  (driven at authoring, severity `error`, "expected a bare 6-char id6"), which is the correct refusal.
  - Carrier: hc6n7r
- GATING `x2dwu5` or `wzhe4n`. Measured in F-06: neither names the field, `x2dwu5` is records-only and
  changes no code behavior, and `wzhe4n` is held transitively by its own `executed:pi3bk8` edge.
  - Carrier-Declined: DELIBERATELY NOT WANTED. Holding `x2dwu5` would delay the measurement record,
    which every branch of the ship/stop decision wants recorded, so gating it would make the plan
    strictly worse at the goal it exists for.
- CHANGING any `- Blocking:` field from `no` to `yes` to make the existing checkpoint fire.
  - Carrier-Declined: REFUSED on cited grounds. The 2026-09-10 maintainer ruling (`qhy3i3` OQ-01)
    narrowed `NO-GO` to an unresolved BLOCKING question, and the three authors chose `Blocking: no`
    with stated rationales. Flipping the field would both contradict the ruling and misrepresent what
    each author judged, to obtain a gate the dependency mechanism provides honestly.
- RETROFITTING anything onto a terminal plan. None of the four is terminal today, so nothing is owed;
  if the Set executes before this plan does, D156 forbids rewriting what an executed plan records.
  - Carrier-Declined: NOT APPLICABLE TODAY and recorded so the window is explicit: this plan's value
    is time-sensitive, and it is worth nothing once the Set is terminal.
- ANY product code, probe, capability, docstring or spec edit. Those are the Set's own children's
  deliverables and this plan touches none of them.
  - Carrier-Declined: OUT OF SCOPE BY CONSTRUCTION. This plan changes only dependency metadata and two
    records; it has no product surface.

## Scope check

- Over-scope: none. The four declared paths are the two plans gaining an edge, the decision carrier
  `wcbpqf` gaining a note, and the general-gap carrier `hc6n7r`. ALL FOUR ARE DECLARED, including
  `hc6n7r`, which was filed at AUTHORING rather than at execution: `check.ipd-uncarried-obligation`
  (`error`) refuses a Deferred row whose `- Carrier:` is prose instead of a bare id6, so the item had to
  exist before this plan could lint. Declaring it now avoids the contradiction of a plan that knows it
  will touch a path and does not say so; `ipd_lifecycle._is_implicitly_allowed` does not grant
  `.aw/records/backlog/**`, so an undeclared edit there would have demanded a `--scope-reason` at
  finalize for work the plan already planned.
- Under-scope: none. `x2dwu5` and `wzhe4n` are deliberately NOT declared (F-06), and no product file is
  touched, so no test file needs editing. NOTE that this plan ships NO code, so the suite is a
  regression check rather than the primary gate; the primary gate is the driven `edge_satisfied`
  behavior in V-01 and V-02.

## Required tests / validation

- Run the suite BARE as `python3 -m pytest` and paste the actual summary line. This plan changes no
  code, so the suite is a regression check only; a change in its result would itself be the finding.
- DRIVE `runner_shared.edge_satisfied` for the new edge in BOTH states and paste both results: False
  while `wcbpqf` is `open`, True with the item `done` (arrange the `done` state on a THROWAWAY copy of
  the records tree, never by transitioning the live item, which is the maintainer's act and would
  forge the very answer this plan exists to wait for).
- `aw ipd lint` conforming on both edited plans at `author` and `pre-execution`.
- `aw check plans` and `aw check backlog` reporting no NEW finding naming `l4vw9o`, `pi3bk8`, `wcbpqf`
  or `d5ntkj`. Paste the before and after, since `aw check plans` already reports findings on this
  corpus and a bare "no findings" claim would be false.
- `aw sanitize --agent` exiting zero.

## Spec / documentation sync

- NO SPEC AMENDMENT, and the reason is measured rather than asserted: spec `25kzda` names
  `supports_deny_tcp_port` ZERO times (F-05), so no shipped contract describes the field this plan
  gates, and nothing in 5.2 or 6.1 changes because no behavior and no guarantee changes. This plan adds
  a dependency edge, which spec `25kzda` 2.7 already defines as legal grammar; using a defined
  mechanism as defined requires no amendment. `- Scope-Paths:` therefore declares no `.spec.md` file,
  which is what makes the runners' declared-spec-edit announcement correctly say nothing.
- NO `- From-Spec:` LINK, DELIBERATELY, and the advisory that asks for one is judged rather than obeyed.
  `aw check plans` reports `check.plan-spec-link-missing` on this plan with the fix
  `aw ipd set d5ntkj --from-spec 25kzda`, because the plan CITES spec `25kzda`. That fix would be a
  false claim: the field means the plan GRADUATED FROM that spec, and this plan graduated from backlog
  `wcbpqf` (which it records in `- From-Backlog:`). The citations here are to 2.7's dependency grammar
  as EVIDENCE, not as a parent. The rule is registered `info` (driven) and fires on 25 pending plans
  today, so this is a known advisory tier and not a new finding this plan introduces. Recorded so a
  reviewer sees the advisory was read and declined with a reason, rather than missed.
- NO CHANGELOG ENTRY. Nothing user-visible changes: no command, output, flag or capability is added or
  altered. The change is plan metadata and two records.
- The `## Workflow history` records the verbs append on both plans are the durable documentation of
  which plans wait on which decision, which is why E-01 and E-02 pass `-m`.

## Open questions

### OQ-01: Should a carried, non-blocking open question gate its plan's dispatch in general, or only when a plan author adds an edge by hand?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: wcbpqf
- Resolution or deferral rationale: NOT BLOCKING, because this plan is correct either way: it adds the
  edge BY HAND to two named plans, which is legitimate under any answer, and it deliberately does not
  ship a rule that would impose an answer on the other 29 (F-07, E-04). THE QUESTION IS GENUINELY THE
  MAINTAINER'S because it sits exactly on the boundary the 2026-09-10 ruling drew: that ruling says a
  non-blocking question does not make a plan `NO-GO`, and a general carrier-to-edge rule would make a
  class of non-blocking questions `dependency-blocked` instead, which is a different mechanism reaching
  a similar outcome. Whether that honors the ruling's intent (the question is still not NO-GO; it just
  waits) or evades it (the plan still does not run) is a judgement about what the ruling was FOR, and
  the repository cannot settle it: the ruling's recorded rationale is about plans HELD for reasons their
  authors judged non-stopping, and it is silent on waiting. RECOMMENDED, if the maintainer wants a
  general answer: make it an ADVISORY rule first, following `check.review-decision-unescalated`
  (`warning`) rather than `check.ipd-uncarried-obligation` (`error`, driven), since 29 pending plans
  would be findings on day one and an error-tier rule would turn `aw check` red for authors who did
  nothing wrong. This plan needs no answer to execute.

### OQ-02: Is two plans the right gate boundary, or should the whole Set wait?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM MEASURED EVIDENCE: two plans, `l4vw9o` and `pi3bk8`.
  The decision's three parts change the ship/stop outcome (owned by the orchestrator) and the field
  name (created by `pi3bk8`); measured per plan, `x2dwu5` and `wzhe4n` name the field ZERO times
  (F-05), and `x2dwu5`'s Goal states "No code behavior changes". Gating `x2dwu5` would delay the
  measurement record that EVERY branch of the ship/stop decision wants recorded, including "record the
  measurement and stop", so it would work against the decision it was meant to serve. `wzhe4n` needs no
  edge because it already declares `executed:pi3bk8` and is therefore held transitively. The Set as a
  whole still cannot COMPLETE without the answer, since the orchestrator is gated and `AGENTS.md` makes
  retirement conditional on every child being `executed`, so the narrower boundary loses nothing.

### OQ-03: How should the Set be held so that executing the holding plan cannot itself release the hold?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: OPEN, REPLAN REQUIRED. Measured at review: this plan is the ONLY artifact carrying `- From-Backlog: wcbpqf`, so when it executes the runner's `process_backlog_close` evaluates `evaluate_backlog_close(repo, "wcbpqf", ...)` to `close=True` ("every IPD carrier is executed and this run executed ...") and its `close_backlog_item` argv (`aw backlog set wcbpqf --status done --evidence <this plan>`) succeeds from `graduated` (driven on a scratch copy: exit 0, item moved to `done/`). That satisfies `state:backlog:done:wcbpqf` with no maintainer answer. Candidate shapes for the replacement, which is the human's choice: (a) gate on a NEW decision item that no plan carries via `From-Backlog`, so only a human can close it; (b) have the maintainer move `l4vw9o`/`pi3bk8` out of `approved` until the decision is made, with no edge at all; (c) answer the decision now, which makes the gate unnecessary.

### OQ-04: Is a whole-run refusal an acceptable way for this gate to bite?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-002
- Resolution or deferral rationale: OPEN, REPLAN REQUIRED. The plan says the edge defers the two plans as `dependency-blocked` while the run continues. Measured at review, that is false for this edge: `runner_shared.enforce_freeze_time_refusal` raised `DriverError: [RUN-DEPENDENCY-UNSATISFIABLE] pi3bk8 requires state:backlog:done:wcbpqf; ... No work started` for a queue containing `pi3bk8`. That follows spec `z7nbn1` 1.4, which refuses the WHOLE RUN when an edge cannot be met during the run. So any selection containing a gated approved plan (including `aw oc run all`, if it selects them) would run nothing at all. The replacement must either accept that blast radius explicitly or use a hold that removes the plans from execute selection (OQ-03 shape (b)).

### OQ-05: Re-derive the plan's premises against the current tree

- Blocking: yes
- Status: open
- Owner: plan author (replacement)
- Finding: PR-003
- Resolution or deferral rationale: OPEN, REPLAN REQUIRED. At review HEAD `ce551c597`: `wcbpqf` is `graduated` (commit `ab3fc2317`, "graduated by run ...: d5ntkj"), `hc6n7r` is `graduated` to Set `carriergate` (plan `rpw4sb`), and `x2dwu5` is `executed`, so its OQ-01 has already closed unanswered. Two of the four Scope-Paths (`.aw/records/backlog/open/...wcbpqf...`, `.../open/...hc6n7r...`) no longer exist. E-04/V-04's "confirm `- Status: open`" cannot pass. `pi3bk8` OQ-01 (the field name) is `resolved` at review, so decision (2) is no longer open. `rpw4sb` F-08 already measured that `state:backlog:done:<carrier>` refuses a `graduated` carrier. A replacement plan must start from these facts.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `git diff` of `l4vw9o` showing the `- Item-Dependencies:` line changed from `none` to `state:backlog:done:wcbpqf` AND showing NO change to `- Status:`, `- Readiness:`, `- Approval:`, any `E-*`, any `V-*`, or any prose section (the history record the verb appends is expected). Plus pasted `aw ipd lint` output at `author` and `pre-execution` reporting conforming.
  - PROVE THE GATE ACTUALLY REFUSES, which is the whole deliverable. Paste the driven result of `runner_shared.edge_satisfied` for this edge against the live tree, showing False and the reason naming `wcbpqf` and its required status. A diff alone FAILS this item: a declared edge that does not refuse is documentation, and this plan's entire value is that it is enforcement.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff` of `pi3bk8` showing `- Item-Dependencies: executed:x2dwu5, state:backlog:done:wcbpqf`, with the pre-existing `executed:x2dwu5` edge RETAINED. An outcome carrying only the new edge FAILS this item outright, since the verb replaces the statement and losing that edge would let the capability plan run before the spec amendment it depends on. Plus `aw ipd lint` conforming at both phases.
  - PROVE THE RELEASE HALF, not only the refusal. On a THROWAWAY copy of the records tree with `wcbpqf` set `done`, drive `edge_satisfied` for the same edge and paste True. Arranging it on the LIVE item is forbidden here: transitioning `wcbpqf` is the maintainer's act, and doing it to make a test pass would fabricate the answer this plan exists to wait for. A gate proven only to refuse is indistinguishable from one that can never release, which is the fail-closed-looking-like-working shape this Set's own `pi3bk8` review caught in its probe.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `git diff` of `wcbpqf` showing the appended history record and NO change to `- Status:`, `- Summary:`, `- Priority:`, `- Work-Kind:` or any of the three recorded decisions. Quote the added record and confirm it states both halves E-03 requires: which plans are held, and the corrected two-plans-zero-specs rename scope. Also paste `aw check backlog` showing no new finding naming `wcbpqf`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `hc6n7r`'s path and pasted content showing the measurement, the two named registry candidates with their severity tiers, and the undecided policy question. Confirm it carries `- Status: open`, `- Work-Kind: followup` and NO `- Blocks-Release:` (since `wcbpqf` carries none, so inheriting one would forge a gate). Paste `aw find backlog hc6n7r` (or `aw attention`) showing it present, which is the proof the general gap survives this plan going terminal.
  - RE-DRIVE THE 29 COUNT at execution rather than copying it from F-07, and paste the number you get together with the one-liner that produced it. Other sessions author plans in this repository continuously, so the population is LIVE; a figure pasted from this plan would be a claim about a corpus that has since changed. If the number differs, append the corrected figure to `hc6n7r` with `aw backlog note` and say so here, since the item's whole value is the measurement. EXCLUDE this plan from the count, as F-07 did: its own OQ-01 is carried and open, so counting it inflates the figure by one (driven at authoring: 30 including it, 29 excluding it).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

REVIEW 2026-10-02: REJECT - NEEDS REPLAN. Do not approve or execute this plan as written; see OQ-03 to OQ-05 and the review record. Executing it would close `wcbpqf` (PR-001) and refuse whole runs (PR-002).

WHAT A HUMAN WOULD BE APPROVING. Four `denypush` plans are approved and ready to run, and three
maintainer decisions about them are recorded on backlog `wcbpqf` with nothing making anyone answer
them. Measured: `aw ipd lint --phase pre-execution` passes on the orchestrator today, so `aw oc run`
would ship a capability under a field name the maintainer has not ruled on, and would then mark every
plan terminal, after which D156 forbids rewriting their records. This plan makes two of those four
plans WAIT, by declaring one typed dependency edge on `wcbpqf`, using a mechanism that already ships
and that already refuses at dispatch (driven: `state:backlog:done:wcbpqf: backlog wcbpqf is 'open',
needs exactly 'done'`). The visible effect for the maintainer is that running the Set now defers
`l4vw9o` and `pi3bk8` as `dependency-blocked` with a message naming the item to close, instead of
executing them. THE ONE JUDGEMENT TO OVERRULE IF YOU DISAGREE: this gates two plans, not four, because
only two name the undecided field and `x2dwu5` is records-only, so holding it would delay the
measurement record that every branch of the decision wants (OQ-02, F-05, F-06). Say so and the edge
becomes a one-line addition to the other two.

WHAT A REVIEWER SHOULD PUSH HARDEST ON. FIRST, THE GATE MUST BE ABLE TO RELEASE. A gate proven only to
refuse is indistinguishable from one that can never release, and this Set has already been bitten by
exactly that shape: `pi3bk8`'s review found a probe design whose fail-closed False was unreachable from
True on any host. V-02 therefore demands the True case on a throwaway tree, and forbids arranging it on
the live item. SECOND, THIS PLAN MUST NOT BECOME A POLICY CHANGE. The carrier-to-edge gap is 29
questions wide (F-07) and the temptation is to ship a `check` rule; that would impose an answer to
OQ-01 on 29 plans this lane did not author, so E-04 FILES it instead. A reviewer should check that no
E-item touches `check_engine`. THIRD, THE APPROVAL MUST SURVIVE. The human approved these plans'
CONTENT; this plan changes only what they wait for, so V-01 and V-03 demand diffs showing `- Status:`,
`- Readiness:` and `- Approval:` untouched.

Execution contract: commit only the four paths named in `Scope-Paths`, all of which already exist,
through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. This is a SHARED
CHECKOUT: verify the staged set with `git diff --cached --name-only` before committing, unstage
anything that is not yours with `git restore --staged <path>`, and re-verify after any failed raw
commit attempt. Note that `aw ipd dependencies set` and `aw backlog note` COMMIT THEIR OWN WRITES by
default, so E-01 through E-03 each produce a commit; do not re-commit those paths, and record the
resulting hashes as evidence. Run the suite BARE as `python3 -m pytest` and PASTE ITS ACTUAL SUMMARY
LINE; the same hard-MUST governs every pasted `edge_satisfied` result and every lint and check output
the `V-*` items demand.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop). THREE
NEGATIVE CONSTRAINTS CARRY REAL WEIGHT. FIRST, do NOT answer any of the three decisions, and do NOT set
`wcbpqf` to `done`, `graduated` or `blocked`: closing it is the maintainer's act, and an agent closing
it would dissolve the gate this plan just built while asserting an answer that was never given. SECOND,
do NOT change any `- Blocking:` field, any plan's `- Status:`, `- Readiness:` or `- Approval:`, or any
E/V item, prose or scope of an approved plan. THIRD, do NOT add a `check` rule, a `RULE_REGISTRY` entry
or any corpus-wide enforcement: that is the deferral `hc6n7r` carries and OQ-01's undecided policy. An
out-of-scope edit that turns out to be necessary is to be MADE and then JUSTIFIED to `aw ipd finalize`
with a `--scope-reason` per path, which is not a reason to stop. Every path this plan expects to touch
is DECLARED, so no `--scope-reason` is anticipated; a declared path left unmodified needs a
`--scope-ack` instead.

LIFECYCLE TRANSITION. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete observed evidence.
Reaching `executed/` is UNCONDITIONALLY OWED, but its OWNER is CONDITIONAL: under `aw oc run` /
`aw agy run` the RUNNER owns the terminal transition and finalize, so do NOT invoke `aw ipd finalize`
yourself in a runner-driven execution; a HAND execution invokes it
(`aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`). Never hand-edit
`- Status:` and never hand-roll a `git mv` into `executed/`. Backlog `wcbpqf` must remain `open`: this
plan is graduated FROM it, and the runner's usual `graduated` transition is itself the thing to watch,
since an item set `graduated` still reports `open`-side `ready` only while its status is `open`. If the
runner would transition `wcbpqf`, that is a finding to report rather than to accept, because the gate
this plan installs reads the item's EXACT status.

TIMING. This plan is worth nothing once the `denypush` Set is terminal (F-09, D156), so it should be
reviewed and run BEFORE that Set. It declares no edge on the Set's plans deliberately: an
`Item-Dependencies` edge expresses "wait for", and this plan must run FIRST, which the dependency
grammar cannot express. If a queue would run `denypush` ahead of this plan, say so rather than letting
both proceed.
