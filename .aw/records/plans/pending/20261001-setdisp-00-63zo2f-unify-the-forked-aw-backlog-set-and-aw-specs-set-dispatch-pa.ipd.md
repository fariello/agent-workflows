# IPD: Unify the forked aw backlog set and aw specs set dispatch paths onto one engine

- Date: 2026-10-01
- Kind: orchestrator
- Concern: `aw backlog set` and `aw specs set` each have TWO spellings reaching TWO SEPARATE IMPLEMENTATIONS of overlapping behavior. `cli.main` forks on whether `--status` was PASSED: absent routes to `status_set.run_set_command`, present routes to `backlog.run_set` or `specs.run_set`. The same CLASS of defect has now been found on that fork FIVE times, three of them release-blocking: `43p53n` (gate-field clearing, unreachable from the positional form), `gatefollows`/`vsgd48` (the release-gate default), `mawwlc`/`47ttnv` (the release-gate close predicate skipped at exit 0), plus two MEASURED while authoring this Set and filed as `h4fiwa` (positional `specs set implemented` bypasses the `--evidence` gate entirely) and `fv4b6s` (positional `specs set deferred` writes an out-of-vocabulary `Gate-Kind`). Each of the first three was fixed by DUPLICATING the behavior into the second path, which is the correct minimal fix for a release blocker and also why the class keeps recurring. Backlog `fcnz1r` filed the durable fix and recorded that it needs a spec-level decision first, because the two paths differ in ways that are each deliberate and separately pinned by tests.
- Scope: IN: sequence the five work children plus the Order 06 Set-level audit child that take the `set` family from two implementations per verb to one, in an order that ships the two release-gated bug fixes WITHOUT waiting on a blocking maintainer decision, and that lands a differential harness before any behavior moves. OUT: every axis spec `wy9aru` Section 7 assigns elsewhere (the UTC-versus-local clock, the history label, the same-status dedup, the sidecar write order, the dead `apply` read, the defaulted message, the backlog transition table, the closed-item audit, the hand-edit gate, the dead `aw prompts set` verb), each with a named carrier.
- Scope-Paths: .aw/records/plans/pending/20261001-setdisp-00-63zo2f-unify-the-forked-aw-backlog-set-and-aw-specs-set-dispatch-pa.ipd.md, .aw/records/plans/pending/20261007-setdisp-06-7zb4ny-audit-the-five-setdisp-children-together-and-run-the-set-lev.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: 8a462bdd73338c3baf6bb3fe84e0108ec426ad11f04d70a7644882021a29d5a9
- Coverage-Checked: 2026-10-07 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: chore
- Priority: medium
- From-Backlog: fcnz1r
- From-Spec: wy9aru
- Set: setdisp
- Order: 0
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 63zo2f
- Approval: 2026-10-08, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-08 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Named the setdispgate overlap (wdyz5n/ju3rhs carry the h4fiwa/fv4b6s gates) and accepted HANDOFF or SATISFIED closes; re-derived the outside prerequisites (jbipfa, nvsz19 executed; ulepef approved, now checked in E-04/V-04); fixed five-vs-six child counts; restated the Section 7 criterion as a property; added finalize ownership; OQ-02 resolved.
- 2026-10-07 coverage pass (aw oc run): fingerprint 8a462bdd7333, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 to-review (aw set): returned to review: Set-level checks now owned by new Order 06 7zb4ny; coverage pass recorded; open questions are non-blocking executor measurements
- 2026-10-07 coverage pass (aw oc run): fingerprint 8d9329855500, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 coverage fail (aw oc run): fingerprint 84f4f14ca276, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 coverage fail (aw oc run): fingerprint 02581037a741, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 coverage fail (aw oc run): fingerprint 256303951ead, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): added Order 06 `7zb4ny`, which performs the Set-level checks this plan listed with no owner (the coverage probe's 2026-10-06 findings); child table, checklist and Scope-Paths updated.
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: The bare suite pytest after the final child compared by name against baseline

- 2026-10-06 coverage fail (aw oc run): fingerprint 9f031836a1c2, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `fcnz1r`. Spec `wy9aru` was authored alongside this Set to supply the canonicity rulings `fcnz1r` says are needed before any code moves; two previously-unknown gate bypasses were MEASURED while authoring and filed as release-gated carriers (`h4fiwa`, `fv4b6s`), plus one dead verb (`68sur3`). This orchestrator carries ONLY the child-completion checklist; every deliverable belongs to a child.
- 2026-10-01 draft (opencode/its_driver/pt3-claude-opus-5-1m-us): created.

## Goal

Leave each of `aw backlog set` and `aw specs set` with ONE implementation of transition validation, the
status write and relocation, reached by both of its spellings, so the recurring class of
gate-reachable-from-one-spelling-only is closed by construction rather than by remembering to write
every future gate twice.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

THIS ORCHESTRATOR CARRIES NO WORK OF ITS OWN. Every item below confirms that a CHILD completed; none
produces a deliverable, establishes a baseline, or reconciles a record. That is deliberate and
mechanical: the runner RETIRES an orchestrator once every child is `executed` and deliberately SKIPS
the pre-transition `E-*`/`V-*` checkpoint, on the premise that a parent's own items are performed by
nobody. Work parked here would therefore be marked complete having never been performed (`AGENTS.md`).
The checklist exists because most Sets are run by a human or agent told simply to "execute setdisp",
with no runner involved, and deleting it causes exactly the partial execution it prevents.

### Task group 1: the children, in dependency order

- [ ] E-01 CONFIRM c6f6sj REACHED executed
  - Depends on: none
  Confirm child 01 (`c6f6sj`, deduplicate the two self-commit helpers and the two From-Backlog gate-inheritance blocks) is `executed`, with its own validation evidence present. This child is FIRST because it is the only one gated on nothing: it changes no dispatch route and no gate, so it can proceed while the spec's blocking question is open.
  - Expected outcome: `c6f6sj` is in `.aw/records/plans/executed/` with `- Status: executed`, every `V-*` carrying pasted evidence, and the duplicated self-commit helper and inheritance block each reduced to one implementation.
  - Execution state: pending

- [ ] E-02 CONFIRM afdmn6 REACHED executed
  - Depends on: E-01
  Confirm child 02 (`afdmn6`, the cross-spelling differential harness) is `executed`. This child adds NO production code: it asserts the axes that currently AGREE and records the axes that currently DISAGREE, so that each later migration's effect is attributable to a specific flipped assertion rather than lost among forty candidate axes.
  - Expected outcome: `afdmn6` is `executed`, `tests/test_set_dispatch_parity.py` exists and passes under both the machine's local timezone and `TZ=UTC`, and its evidence includes at least two throwaway-probe demonstrations proving the harness actually detects a regression.
  - Execution state: pending

- [ ] E-03 CONFIRM m1jlwm REACHED executed
  - Depends on: E-02
  Confirm child 03 (`m1jlwm`, close the two measured positional `specs set` gate bypasses) is `executed`. This child carries `- Blocks-Release: next` and is deliberately independent of the spec's blocking question: it UNIONS two refusals across the existing fork rather than removing the fork, so a release blocker is not held hostage to a design decision.
  OVERLAP WITH SET `setdispgate` (found at review, see OQ-02): the SAME two bypasses also have their own `From-Backlog` carriers outside this Set, `wdyz5n` (carrier of `h4fiwa`, `reviewed`) and `ju3rhs` (carrier of `fv4b6s`, `approved`), both ungated (`- Item-Dependencies: none`) and therefore likely to execute BEFORE `m1jlwm`. Each of those plans and `m1jlwm` already requires whichever executes second to CONSUME the first's refusal rather than add a second copy. Confirm here which route installed each refusal; do not require `m1jlwm` itself to have written it.
  - Expected outcome: `m1jlwm` is `executed` (or retired to `superseded/` by a maintainer choosing the `setdispgate` route, OQ-02); on BOTH spellings `aw specs set implemented` without resolvable `--evidence` refuses, and `aw specs set deferred --gate-kind <invalid>` refuses and writes nothing; exactly ONE implementation of each refusal exists, observed behaviorally (no source census); carriers `h4fiwa` and `fv4b6s` are `done` with the gate satisfied (HANDOFF route through `wdyz5n`/`ju3rhs` executing, or SATISFIED route with `--evidence`), never cleared.
  - Execution state: pending

- [ ] E-04 CONFIRM m94eht REACHED executed
  - Depends on: E-03
  Confirm child 04 (`m94eht`, make `aw specs set --status` a thin adapter) is `executed`. This child is GATED: it carries `- Item-Dependencies: state:spec:approved:wy9aru`, so it cannot dispatch until the spec is `approved`, which is the transition requiring the maintainer to have answered that spec's blocking OQ-1 about the sidecar. It also amends `implemented` spec `1525-02` R2, declared in its `Scope-Paths`.
  - Expected outcome: `m94eht` is `executed`; `ulepef` (the sidecar write-ORDER fix `m94eht` adopts, see "THE ONE LIVE ARTIFACT" below) reached `executed` BEFORE `m94eht` ran; `specs.run_set` holds no status validation, write, relocation or history assembly of its own; every specs AGREEMENT assertion in the harness passes unchanged; the `1525-02` R2 amendment landed in the same change as the behavior it describes.
  - Execution state: pending

- [ ] E-05 CONFIRM vhiqo6 REACHED executed
  - Depends on: E-04
  Confirm child 05 (`vhiqo6`, make `aw backlog set --status` a thin adapter) is `executed`. This is the terminal child and the one that closes the class for the verb `fcnz1r` names. It has the widest blast radius in the Set: it flips three separately-owned axes at once (clock, history label, same-status dedup) and changes the git shape of every backlog status transition from a delete-plus-untracked-file to a single staged rename.
  - Expected outcome: `vhiqo6` is `executed`; `backlog.run_set` holds no transition validation, metadata render, relocation or history assembly of its own; the three retrospective parity files (`tests/test_backlog_positional_close_gate.py`, `tests/test_backlog_gate_follows_status.py`, `tests/test_status_set.py::TestGateFieldClearingOnStatusChange`) all pass; `runner_shared.close_backlog_item` works end to end; and each of the six carriers it touches has a measured COMPLETE-or-PARTIAL verdict with closes performed only for the COMPLETE ones.
  - Execution state: pending

- [ ] E-06 CONFIRM 7zb4ny REACHED executed
  - Depends on: E-05
  - Expected outcome: `7zb4ny` reads `- Status: executed` on disk, with every Set-level check below performed and pasted in its V-items.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `c6f6sj` | `20261001-setdisp-01-c6f6sj-deduplicate-the-two-self-commit-helpers-and-the-two-from-bac.ipd.md` | Collapses `specs._offer_specs_set_commit` into `status_set._offer_self_commit` and the duplicated `From-Backlog` gate-inheritance block into one, correcting the copy that prints `aw set:` while running as `aw specs set`. Ungated: no dispatch change, no gate change. | none |
| 02 | `afdmn6` | `20261001-setdisp-02-afdmn6-build-the-cross-spelling-differential-harness-that-makes-eve.ipd.md` | Authors `tests/test_set_dispatch_parity.py`: asserts agreement on every axis that agrees today, records the eight that disagree as expected differences naming the child that flips each, and proves the harness can fail. No production code. | `executed:c6f6sj` |
| 03 | `m1jlwm` | `20261001-setdisp-03-m1jlwm-close-the-two-measured-positional-specs-set-gate-bypasses-by.ipd.md` | Unions the `implemented`-needs-evidence refusal and the `deferred`-gate-kind validation across the fork, so neither is bypassable. `Blocks-Release: next`. Closes `h4fiwa` and `fv4b6s`. | `executed:afdmn6` |
| 04 | `m94eht` | `20261001-setdisp-04-m94eht-make-aw-specs-set-status-a-thin-adapter-delegating-to-the-sh.ipd.md` | Reduces `specs.run_set` to an adapter delegating to the shared engine, carrying its three own behaviors in as type-scoped parameters. Amends spec `1525-02` R2. GATED on `wy9aru` reaching `approved`. | `executed:m1jlwm`, `state:spec:approved:wy9aru` |
| 05 | `vhiqo6` | `20261001-setdisp-05-vhiqo6-make-aw-backlog-set-status-a-thin-adapter-delegating-to-the.ipd.md` | Reduces `backlog.run_set` to an adapter, adopts the `git mv` relocation and the ambiguous-selector refusal, keeps `--gate-dir` as an engine parameter, and gives each touched carrier a measured verdict. | `executed:m94eht` |
| 06 | `7zb4ny` | `20261007-setdisp-06-7zb4ny-audit-the-five-setdisp-children-together-and-run-the-set-lev.ipd.md` | Performs every Set-level check below after the last child: the per-child evidence audit, the eight-assertion flip table, the partial-close check, the amendment-with-behavior and no-source-read checks, the parity files after every child and under `TZ=UTC`, the bare-suite failure set by id, and `check release-gates`. Measurement only. | `executed:afdmn6`, `executed:m1jlwm`, `executed:m94eht`, `executed:vhiqo6` |

THE ORDER IS NOT A PREFERENCE AND EACH EDGE HAS A REASON. 01 first because it is the only child gated
on nothing, so the Set makes real progress while the maintainer decision is outstanding. 02 before any
behavior moves, because a harness authored alongside the change it validates proves nothing: an author
writing both shapes the assertions around what the change happens to do. 03 before the migrations
because its two bugs are RELEASE-GATED and must be able to ship without waiting on `wy9aru` OQ-1. 04
before 05 because specs is the simpler path (no `--gate-dir`, no `_render_item` round trip, no
relocation divergence), so it de-risks the larger migration, and because spec `wy9aru` S4 requires the
migration to be incremental and per-verb with the harness green between steps.

THE ONE LIVE ARTIFACT OUTSIDE THIS SET THAT MUST LAND BEFORE CHILDREN 04 AND 05 is `ulepef`
(`approved` at review 2026-10-07, release-gated): it moves the sidecar append after the durable write,
already carries the `2vev8j` amendment, and `m94eht` adopts its write order (its own gate says "Plan
`ulepef` must also have landed (F-02)"). NO `- Item-Dependencies:` edge enforces this today (`m94eht`
declares only `executed:m1jlwm, state:spec:approved:wy9aru`), so E-04 checks it explicitly. As authored
this paragraph also named `jbipfa` (label parameter on `backlog._reattach_history`) and `nvsz19` (plan
transition table in `status_set.validate_transition_allowed`); RE-MEASURED at review, both are now in
`.aw/records/plans/executed/`, so they are satisfied prerequisites, not live ones. Re-derive this list
at execution rather than trusting it.

THE SAME TWO RELEASE-GATED BYPASSES CHILD 03 FIXES ALSO HAVE CARRIERS IN SET `setdispgate`: `wdyz5n`
(`From-Backlog: h4fiwa`) and `ju3rhs` (`From-Backlog: fv4b6s`, which also widens the fix to the backlog
twin). Those are the plans actually carrying the `h4fiwa`/`fv4b6s` gates (`m1jlwm` carries
`From-Backlog: fcnz1r`), and both are ungated. Each of the three plans already says the second to run
must consume the first's refusal. Which route a maintainer prefers is OQ-02.

## Completion criteria (the whole Set is done only when)

- All six children (Orders 01 to 06) are in `.aw/records/plans/executed/` with `- Status: executed` and every `V-*` carrying pasted evidence (or, for `m1jlwm` only, retired to `superseded/` under OQ-02 with both refusals demonstrably installed by `wdyz5n`/`ju3rhs`).
- For EACH of `aw backlog set` and `aw specs set`, both spellings reach one implementation of transition validation, one of the status write, and one of relocation (spec `wy9aru` C1), demonstrated by identical observable behavior across the two spellings and never by a symbol census (`wy9aru` S1).
- No gate is weaker on either spelling than it was on the STRICTER spelling before the Set (`wy9aru` C2). Specifically: all five historical instances have a test proving the refusal fires on BOTH spellings.
- Release-gated carriers `h4fiwa` and `fv4b6s` are `done`, closed through the HANDOFF or SATISFIED route rather than by clearing the gate.
- `tests/test_set_dispatch_parity.py` passes identically under the machine's local timezone and under `TZ=UTC`, so no cross-spelling assertion carries a clock dependency.
- The bare suite's failure SET is unchanged except for tests the children explicitly named in advance.
- Every axis spec `wy9aru` Section 7 assigns elsewhere is either still live under its own carrier or was closed by THAT carrier's own work, never closed by this Set except where a child's measured evidence proves the item COMPLETE against the item's own scope. (Several Section 7 carriers had already closed by review on 2026-10-07, e.g. `r74211`, `19lmbe`, `t1gbwg`, `mbjuv5`, `68sur3`; re-derive at execution.)

## Cross-IPD validation

OWNER: every check in this section and every whole-Set item in Completion criteria and Required tests is performed by Order 06 `7zb4ny` after the last migration child; this plan performs none of them.

- NO AXIS IS FIXED TWICE, AND NO AXIS IS FIXED BY NOBODY. Check the eight expected-difference assertions child 02 records against the flips children 03, 04 and 05 claim: each must be flipped by exactly one child, and any assertion still unflipped at the end must correspond to a Section 7 axis with a live carrier. An assertion flipped by two children means one of them widened past its reviewed scope.
- NO CARRIER IS CLOSED ON A PARTIAL FIX. Children 03 and 05 (and, for `h4fiwa`/`fv4b6s`, possibly `wdyz5n`/`ju3rhs` via HANDOFF) close backlog items. For each close, confirm the item's OWN scope is satisfied, not merely that this Set touched the area: the clock items name five local-clock call sites in `backlog.py` and the Set removes one, so closing one of them would assert a repository-wide fix that did not happen (`AGENTS.md` close-legitimacy rule).
- THE SPEC AMENDMENT TRAVELS WITH ITS BEHAVIOR. Child 04 amends `1525-02` R2 and must land that amendment in the SAME commit as the sidecar behavior (`wy9aru` S5). Child 05 owes no amendment and must NOT add one; if child 04's amendment did not land, child 05 stops rather than amending the spec itself.
- THE THREE RETROSPECTIVE PARITY FILES PASS AFTER EVERY CHILD, not only at the end. Each exists because an asymmetry on that axis caused a release-blocking defect, so they are the Set's regression surface: a failure means a migration reintroduced one of the three defects the Set exists to prevent.
- NO CHILD READS PRODUCTION SOURCE TO PROVE UNIFICATION. Confirm no test added by any child uses `inspect`, `ast`, regex or substring search over production source, counts callers, or asserts docstring text (`AGENTS.md`, GUIDING_PRINCIPLES P16, `wy9aru` S1). "There is now one implementation" is the single most tempting claim to pin with `grep`, and a code-structure pin is forbidden outright.

## Deferred / out of scope (with reason)

- EVERY AXIS SPEC `wy9aru` SECTION 7 ASSIGNS ELSEWHERE is deferred with a named carrier, and the children must NORMALIZE AROUND each rather than fixing or assuming it: the UTC-versus-local clock (`2wae2x`, `fnb8pl`, `lq2w86`, all release-gated), the history label token (`jbipfa`, `reviewed`), the same-status dedup asymmetry (`r74211`), the sidecar write ORDER (`ulepef`, release-gated), the dead `apply` read in the dry-run guard (`19lmbe`, release-gated), the backlog transition table (`t1gbwg`), the audit of items closed through the ungated spelling (`mbjuv5`), the hand-edited-transition gate (`4ynlcg`), and the `production_checks.backlog_graduate_legitimacy` tautological clause.
  - Carrier: wy9aru
- A PRE-EXISTING TEST DEFECT THIS SET EXPOSES IS FILED, NOT FIXED. Child 04's `state:spec:approved:wy9aru` dependency edge is legal and ENFORCED (verified through `ipd_schema.parse_item_dependencies`, `runner_shared.preflight_dependency_findings` and `runner_shared.edge_satisfied`), but `tests/test_terminal_status_vocabulary.py::TestExecutionSuccessStatesNarrowingAndBlastRadius::test_blast_radius_zero_across_pending_plans` globs only the plans trees for every dependency id6 and so reports the spec target as a stranded prerequisite, turning the suite red. DO NOT resolve that failure by deleting or weakening the edge: it is the only mechanism preventing child 04 from executing before the maintainer answers spec `wy9aru`'s blocking question, so removing it would silently discard a human decision gate.
  - Carrier: pyhq6s
- THE DEAD `aw prompts set` VERB IS NOT FIXED BY THIS SET. It was dispatched in `cli.main` and advertised in help but rejected by the parser (MEASURED while authoring). Its carrier `68sur3` is `done` as of review (closed via executed IPD `gm9baj`), so no child may touch it.
  - Carrier: 68sur3
- THE CLI GRAMMAR IS NOT CHANGED. Both spellings keep working with the same arguments, no verb is renamed or removed, and nothing is deprecated. This is an internal convergence; a user's commands continue to work (`wy9aru` Section 3a).
- NO STATUS VOCABULARY, STATUS MEANING, OR TRANSITION TABLE IS CHANGED. The Set reduces the number of places a transition is enforced from two to one per verb; it does not decide which transitions are legal. That is `t1gbwg`'s question for backlog items, and `nvsz19`'s for plans.
  - Carrier: t1gbwg
- THE PER-ARTIFACT METADATA STORE IS NOT PRE-EMPTED. Spec `4sd62s` (`reviewed`) is the eventual replacement of the history storage model; children touching history writers must not anticipate it.
  - Carrier: 4sd62s

## Scope check

- Over-scope: none. This orchestrator declares only its own file and edits only its own checklist; every production and test path belongs to a child and is declared there.
- Under-scope: none. The orchestrator carries no deliverable, by design (see the note under "Detailed Implementation Checklist"): any work found to be parent-only must become a NEW CHILD with a row in the table above, never an item parked here, because the runner retires an orchestrator without running its `E-*`/`V-*` checkpoint.

## Required tests / validation

This orchestrator runs no tests of its own; every test belongs to a child and is listed in that child's
"Required tests / validation". Every whole-Set check below is performed by Order 06 `7zb4ny` (E-01 to E-06),
after the last migration child, and NOT by this plan:

- For each child, `AW_NO_REEXEC=1 aw ipd lint --phase post-transition` conforming, and the plan present in `.aw/records/plans/executed/`. (Owner: `7zb4ny`.)
- For each child, every `V-*` carries pasted evidence rather than an assertion of success. A `V-*` whose "Observed evidence" is empty or paraphrased fails this check even if the child is marked executed. (Owner: `7zb4ny`.)
- The bare suite `python3 -m pytest` after the final child, with the `N passed` line pasted, and its failure SET compared BY NAME against the baseline that child 01 `c6f6sj` re-derived and recorded in its own evidence before its first edit (that is the pre-Set baseline; this plan measures none). Counts alone are insufficient: `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` is red at base for part of every day on the local-versus-UTC clock skew, so an unchanged count can hide a real change and a changed count can mean only that the clock moved. (Owner: `7zb4ny`.)
- `AW_NO_REEXEC=1 aw check release-gates`, since the Set closes at least two release-gated carriers. (Owner: `7zb4ny`.)
- The cross-IPD checks in "Cross-IPD validation" above, each answered explicitly. (Owner: `7zb4ny`.)

## Open questions

### OQ-01: is the eventual single engine `status_set`, or a new module extracted from it?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED by spec `wy9aru` Section 4.1 in favor of `status_set` as the surviving implementation, with `backlog.run_set` and `specs.run_set` reduced to thin adapters that keep their names and signatures. Three reasons, in order of weight: it is already the shared engine (four reachable verbs plus `aw finish` reach it, against one each for the others), it already holds the capabilities the flag paths lack (multi-selector batch, setid resolution, `--force`, structured output), and `2lcqno`'s setid semantics plus `z7nbn1`'s one-action-table thesis are both already implemented there. Extracting a new module would mean rewriting four working callers to gain nothing the delegation does not already give.

### OQ-02: which plan owns the `h4fiwa`/`fv4b6s` fixes, child 03 `m1jlwm` or Set `setdispgate` (`wdyz5n`, `ju3rhs`)?

- Blocking: no
- Status: resolved
- Owner: plan reviewer (2026-10-07 /plan-review)
- Resolution or deferral rationale: RESOLVED by keeping all three plans and accepting whichever lands first as the owner of each refusal, because each plan already states that rule (`wdyz5n` gate: "Whichever of the two executes SECOND must consume the evidence branch the first installed"; `ju3rhs` gate: "whichever executes second must REBASE ONTO the first rather than add a second copy"), and only `wdyz5n`/`ju3rhs` carry the items' `From-Backlog` gates, so they are the HANDOFF route that closes them. `m1jlwm` then either confirms and pins both refusals on both spellings, or a maintainer retires it to `superseded/`; E-03/V-03 accept either. Reversible: yes (a maintainer can retire one route at any time). A maintainer who prefers the Set to own both fixes follows the retire-and-move-gate instruction in those plans' gates.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `c6f6sj`'s path under `.aw/records/plans/executed/` with its `- Status:` line quoted; pasted `aw ipd lint --phase post-transition` for it; and the quoted evidence from its V-02 showing the `aw specs set:` prefix now printed by the inheritance notice (the drift this child corrects).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: `afdmn6`'s executed path and lint result; pasted `tests/test_set_dispatch_parity.py` run under BOTH the local timezone and `TZ=UTC`; and the quoted probe demonstrations from its V-05 proving the harness detects a regression on two distinct axes.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: `m1jlwm`'s executed path and lint result (or its `superseded/` path and RETIRED header if OQ-02's alternative was taken); the re-measured refusals for both bypasses on BOTH spellings quoted from its V-01 and V-02; a statement, with the plan path, of which plan (`m1jlwm`, `wdyz5n` or `ju3rhs`) installed each refusal and that the later one consumed it rather than adding a copy, shown by one behavioral refusal per spelling (no source census); and `h4fiwa` and `fv4b6s` read back showing `- Status: done`, `- Blocks-Release:` still present, and the closing history line naming the executed carrier or `--evidence` path, confirming HANDOFF or SATISFIED rather than a cleared gate.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `m94eht`'s executed path and lint result; `ulepef`'s executed path plus `git log --format='%h %cI %s' -1 -- <path>` for both `ulepef` and `m94eht` showing `ulepef` landed first; `wy9aru`'s `- Status:` quoted as `approved` with its OQ-1 answer, proving the dependency edge was satisfied rather than bypassed; the `1525-02` R2 amendment diff; and the harness's specs agreement assertions shown passing unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `vhiqo6`'s executed path and lint result; pasted `git status --porcelain` from its V-04 showing a single `R` rename for a backlog status change; the three retrospective parity files' results quoted from its V-05; the `runner_shared.close_backlog_item` end-to-end evidence; and its six per-carrier COMPLETE-or-PARTIAL verdicts, with confirmation that no PARTIAL item was closed.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `grep -n '^- Status:' <7zb4ny plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This orchestrator is `to-review` and requires `/plan-review` followed by explicit human approval. Its
children carry their own approvals; approving this plan approves the SEQUENCE and the scope fences, not
the children's contents.

TWO THINGS A HUMAN SHOULD DECIDE BEFORE THIS SET RUNS UNATTENDED. FIRST, spec `wy9aru` carries a
BLOCKING open question (OQ-1: does the sidecar write survive unification as a type conditional, or is
it dropped?) whose answer turns on whether anyone uses `aw record-history`. Children 01, 02 and 03 are
deliberately independent of it and can run now; children 04 and 05 carry a machine-readable
`state:spec:approved:wy9aru` dependency and will be reported `dependency-blocked` by the runner until
the spec is approved, which is the correct behavior and not a failure of the run. SECOND, child 05
changes the git shape of every backlog status transition and flips three separately-owned axes at once;
if that is not wanted yet, approve 01 through 04 and hold 05.

Execution contract (`AGENTS.md`): each child commits ONLY the files it changed, limited to its declared
`Scope-Paths`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never
`--no-verify`, and never push. Paste ACTUAL runner output for every test claim.

Post-gate lifecycle: this orchestrator is retired to `.aw/records/plans/executed/` only once ALL SIX
children are `executed` on disk. Under a runner, retirement is the runner's (orchestrator rollup); a
human or agent executing by hand verifies V-01 to V-06 first and then uses `aw ipd finalize`, never a
hand `git mv`. The backlog item `fcnz1r` is set to `graduated` by the runner upon
verification; no plan in this Set sets it, and no agent should set it `done`, since `graduated` means
the design is handed off while `done` means the code is written and validated.
