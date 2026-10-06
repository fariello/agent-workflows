# IPD: Unify the forked aw backlog set and aw specs set dispatch paths onto one engine

- Date: 2026-10-01
- Kind: orchestrator
- Concern: `aw backlog set` and `aw specs set` each have TWO spellings reaching TWO SEPARATE IMPLEMENTATIONS of overlapping behavior. `cli.main` forks on whether `--status` was PASSED: absent routes to `status_set.run_set_command`, present routes to `backlog.run_set` or `specs.run_set`. The same CLASS of defect has now been found on that fork FIVE times, three of them release-blocking: `43p53n` (gate-field clearing, unreachable from the positional form), `gatefollows`/`vsgd48` (the release-gate default), `mawwlc`/`47ttnv` (the release-gate close predicate skipped at exit 0), plus two MEASURED while authoring this Set and filed as `h4fiwa` (positional `specs set implemented` bypasses the `--evidence` gate entirely) and `fv4b6s` (positional `specs set deferred` writes an out-of-vocabulary `Gate-Kind`). Each of the first three was fixed by DUPLICATING the behavior into the second path, which is the correct minimal fix for a release blocker and also why the class keeps recurring. Backlog `fcnz1r` filed the durable fix and recorded that it needs a spec-level decision first, because the two paths differ in ways that are each deliberate and separately pinned by tests.
- Scope: IN: sequence the five children that take the `set` family from two implementations per verb to one, in an order that ships the two release-gated bug fixes WITHOUT waiting on a blocking maintainer decision, and that lands a differential harness before any behavior moves. OUT: every axis spec `wy9aru` Section 7 assigns elsewhere (the UTC-versus-local clock, the history label, the same-status dedup, the sidecar write order, the dead `apply` read, the defaulted message, the backlog transition table, the closed-item audit, the hand-edit gate, the dead `aw prompts set` verb), each with a named carrier.
- Scope-Paths: .aw/records/plans/pending/20261001-setdisp-00-63zo2f-unify-the-forked-aw-backlog-set-and-aw-specs-set-dispatch-pa.ipd.md
- Item-Dependencies: none
- Status: draft
- Coverage: fail
- Coverage-Fingerprint: 9f031836a1c2a592884ef82c5f36abeb07ece1eedabb9df56b7a886597cc3275
- Coverage-Checked: 2026-10-06 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: chore
- Priority: medium
- From-Backlog: fcnz1r
- From-Spec: wy9aru
- Set: setdisp
- Order: 0
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 63zo2f

## Workflow history
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
  - Expected outcome: `m1jlwm` is `executed`; positional `aw specs set implemented` without resolvable `--evidence` refuses, and positional `aw specs set deferred --gate-kind <invalid>` refuses and writes nothing; carriers `h4fiwa` and `fv4b6s` closed through the evidence route with the gate satisfied rather than cleared.
  - Execution state: pending

- [ ] E-04 CONFIRM m94eht REACHED executed
  - Depends on: E-03
  Confirm child 04 (`m94eht`, make `aw specs set --status` a thin adapter) is `executed`. This child is GATED: it carries `- Item-Dependencies: state:spec:approved:wy9aru`, so it cannot dispatch until the spec is `approved`, which is the transition requiring the maintainer to have answered that spec's blocking OQ-1 about the sidecar. It also amends `implemented` spec `1525-02` R2, declared in its `Scope-Paths`.
  - Expected outcome: `m94eht` is `executed`; `specs.run_set` holds no status validation, write, relocation or history assembly of its own; every specs AGREEMENT assertion in the harness passes unchanged; the `1525-02` R2 amendment landed in the same change as the behavior it describes.
  - Execution state: pending

- [ ] E-05 CONFIRM vhiqo6 REACHED executed
  - Depends on: E-04
  Confirm child 05 (`vhiqo6`, make `aw backlog set --status` a thin adapter) is `executed`. This is the terminal child and the one that closes the class for the verb `fcnz1r` names. It has the widest blast radius in the Set: it flips three separately-owned axes at once (clock, history label, same-status dedup) and changes the git shape of every backlog status transition from a delete-plus-untracked-file to a single staged rename.
  - Expected outcome: `vhiqo6` is `executed`; `backlog.run_set` holds no transition validation, metadata render, relocation or history assembly of its own; the three retrospective parity files (`tests/test_backlog_positional_close_gate.py`, `tests/test_backlog_gate_follows_status.py`, `tests/test_status_set.py::TestGateFieldClearingOnStatusChange`) all pass; `runner_shared.close_backlog_item` works end to end; and each of the six carriers it touches has a measured COMPLETE-or-PARTIAL verdict with closes performed only for the COMPLETE ones.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `c6f6sj` | `20261001-setdisp-01-c6f6sj-deduplicate-the-two-self-commit-helpers-and-the-two-from-bac.ipd.md` | Collapses `specs._offer_specs_set_commit` into `status_set._offer_self_commit` and the duplicated `From-Backlog` gate-inheritance block into one, correcting the copy that prints `aw set:` while running as `aw specs set`. Ungated: no dispatch change, no gate change. | none |
| 02 | `afdmn6` | `20261001-setdisp-02-afdmn6-build-the-cross-spelling-differential-harness-that-makes-eve.ipd.md` | Authors `tests/test_set_dispatch_parity.py`: asserts agreement on every axis that agrees today, records the eight that disagree as expected differences naming the child that flips each, and proves the harness can fail. No production code. | `executed:c6f6sj` |
| 03 | `m1jlwm` | `20261001-setdisp-03-m1jlwm-close-the-two-measured-positional-specs-set-gate-bypasses-by.ipd.md` | Unions the `implemented`-needs-evidence refusal and the `deferred`-gate-kind validation across the fork, so neither is bypassable. `Blocks-Release: next`. Closes `h4fiwa` and `fv4b6s`. | `executed:afdmn6` |
| 04 | `m94eht` | `20261001-setdisp-04-m94eht-make-aw-specs-set-status-a-thin-adapter-delegating-to-the-sh.ipd.md` | Reduces `specs.run_set` to an adapter delegating to the shared engine, carrying its three own behaviors in as type-scoped parameters. Amends spec `1525-02` R2. GATED on `wy9aru` reaching `approved`. | `executed:m1jlwm`, `state:spec:approved:wy9aru` |
| 05 | `vhiqo6` | `20261001-setdisp-05-vhiqo6-make-aw-backlog-set-status-a-thin-adapter-delegating-to-the.ipd.md` | Reduces `backlog.run_set` to an adapter, adopts the `git mv` relocation and the ambiguous-selector refusal, keeps `--gate-dir` as an engine parameter, and gives each touched carrier a measured verdict. | `executed:m94eht` |

THE ORDER IS NOT A PREFERENCE AND EACH EDGE HAS A REASON. 01 first because it is the only child gated
on nothing, so the Set makes real progress while the maintainer decision is outstanding. 02 before any
behavior moves, because a harness authored alongside the change it validates proves nothing: an author
writing both shapes the assertions around what the change happens to do. 03 before the migrations
because its two bugs are RELEASE-GATED and must be able to ship without waiting on `wy9aru` OQ-1. 04
before 05 because specs is the simpler path (no `--gate-dir`, no `_render_item` round trip, no
relocation divergence), so it de-risks the larger migration, and because spec `wy9aru` S4 requires the
migration to be incremental and per-verb with the harness green between steps.

THREE LIVE ARTIFACTS OUTSIDE THIS SET MUST LAND BEFORE CHILDREN 04 AND 05, and each edits a function
this Set touches, so landing first costs nothing while landing second costs a conflict with work a
human already reviewed: `jbipfa` (`reviewed`) gives `backlog._reattach_history` its label parameter;
`ulepef` (`to-review`, release-gated) moves the sidecar append after the durable write and already
carries the `2vev8j` amendment; `nvsz19` (`approved`, release-gated) wires the plan transition table
into `status_set.validate_transition_allowed`, the exact function child 03 unions refusals into.

## Completion criteria (the whole Set is done only when)

- All five children are in `.aw/records/plans/executed/` with `- Status: executed` and every `V-*` carrying pasted evidence.
- For EACH of `aw backlog set` and `aw specs set`, both spellings reach one implementation of transition validation, one of the status write, and one of relocation (spec `wy9aru` C1), demonstrated by identical observable behavior across the two spellings and never by a symbol census (`wy9aru` S1).
- No gate is weaker on either spelling than it was on the STRICTER spelling before the Set (`wy9aru` C2). Specifically: all five historical instances have a test proving the refusal fires on BOTH spellings.
- Release-gated carriers `h4fiwa` and `fv4b6s` are `done`, closed through the evidence route rather than by clearing the gate.
- `tests/test_set_dispatch_parity.py` passes identically under the machine's local timezone and under `TZ=UTC`, so no cross-spelling assertion carries a clock dependency.
- The bare suite's failure SET is unchanged except for tests the children explicitly named in advance.
- Every axis spec `wy9aru` Section 7 assigns elsewhere remains OPEN under its own carrier, except where a child's measured evidence proves its item COMPLETE against the item's own scope.

## Cross-IPD validation

- NO AXIS IS FIXED TWICE, AND NO AXIS IS FIXED BY NOBODY. Check the eight expected-difference assertions child 02 records against the flips children 03, 04 and 05 claim: each must be flipped by exactly one child, and any assertion still unflipped at the end must correspond to a Section 7 axis with a live carrier. An assertion flipped by two children means one of them widened past its reviewed scope.
- NO CARRIER IS CLOSED ON A PARTIAL FIX. Children 03 and 05 both close backlog items. For each close, confirm the item's OWN scope is satisfied, not merely that this Set touched the area: the clock items name five local-clock call sites in `backlog.py` and the Set removes one, so closing one of them would assert a repository-wide fix that did not happen (`AGENTS.md` close-legitimacy rule).
- THE SPEC AMENDMENT TRAVELS WITH ITS BEHAVIOR. Child 04 amends `1525-02` R2 and must land that amendment in the SAME commit as the sidecar behavior (`wy9aru` S5). Child 05 owes no amendment and must NOT add one; if child 04's amendment did not land, child 05 stops rather than amending the spec itself.
- THE THREE RETROSPECTIVE PARITY FILES PASS AFTER EVERY CHILD, not only at the end. Each exists because an asymmetry on that axis caused a release-blocking defect, so they are the Set's regression surface: a failure means a migration reintroduced one of the three defects the Set exists to prevent.
- NO CHILD READS PRODUCTION SOURCE TO PROVE UNIFICATION. Confirm no test added by any child uses `inspect`, `ast`, regex or substring search over production source, counts callers, or asserts docstring text (`AGENTS.md`, GUIDING_PRINCIPLES P16, `wy9aru` S1). "There is now one implementation" is the single most tempting claim to pin with `grep`, and a code-structure pin is forbidden outright.

## Deferred / out of scope (with reason)

- EVERY AXIS SPEC `wy9aru` SECTION 7 ASSIGNS ELSEWHERE is deferred with a named carrier, and the children must NORMALIZE AROUND each rather than fixing or assuming it: the UTC-versus-local clock (`2wae2x`, `fnb8pl`, `lq2w86`, all release-gated), the history label token (`jbipfa`, `reviewed`), the same-status dedup asymmetry (`r74211`), the sidecar write ORDER (`ulepef`, release-gated), the dead `apply` read in the dry-run guard (`19lmbe`, release-gated), the backlog transition table (`t1gbwg`), the audit of items closed through the ungated spelling (`mbjuv5`), the hand-edited-transition gate (`4ynlcg`), and the `production_checks.backlog_graduate_legitimacy` tautological clause.
  - Carrier: wy9aru
- A PRE-EXISTING TEST DEFECT THIS SET EXPOSES IS FILED, NOT FIXED. Child 04's `state:spec:approved:wy9aru` dependency edge is legal and ENFORCED (verified through `ipd_schema.parse_item_dependencies`, `runner_shared.preflight_dependency_findings` and `runner_shared.edge_satisfied`), but `tests/test_terminal_status_vocabulary.py::TestExecutionSuccessStatesNarrowingAndBlastRadius::test_blast_radius_zero_across_pending_plans` globs only the plans trees for every dependency id6 and so reports the spec target as a stranded prerequisite, turning the suite red. DO NOT resolve that failure by deleting or weakening the edge: it is the only mechanism preventing child 04 from executing before the maintainer answers spec `wy9aru`'s blocking question, so removing it would silently discard a human decision gate.
  - Carrier: pyhq6s
- THE DEAD `aw prompts set` VERB IS NOT FIXED BY THIS SET. It is dispatched in `cli.main` and advertised in help but rejected by the parser, so one of the five claimed `set` surfaces is unreachable (MEASURED while authoring). Fixing it is a scope DECISION (register the subparser versus delete the branch and the help claim), not a dispatch question, and it needs the prompt status vocabulary checked against the shared engine's.
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
"Required tests / validation". What is verified HERE is that each child's evidence EXISTS and SAYS what
the child claimed:

- For each child, `AW_NO_REEXEC=1 aw ipd lint --phase post-transition` conforming, and the plan present in `.aw/records/plans/executed/`.
- For each child, every `V-*` carries pasted evidence rather than an assertion of success. A `V-*` whose "Observed evidence" is empty or paraphrased fails this check even if the child is marked executed.
- The bare suite `python3 -m pytest` after the final child, with the `N passed` line pasted, and its failure SET compared BY NAME against the baseline re-derived before the Set began. Counts alone are insufficient: `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` is red at base for part of every day on the local-versus-UTC clock skew, so an unchanged count can hide a real change and a changed count can mean only that the clock moved.
- `AW_NO_REEXEC=1 aw check release-gates`, since the Set closes at least two release-gated carriers.
- The cross-IPD checks in "Cross-IPD validation" above, each answered explicitly.

## Open questions

### OQ-01: is the eventual single engine `status_set`, or a new module extracted from it?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED by spec `wy9aru` Section 4.1 in favor of `status_set` as the surviving implementation, with `backlog.run_set` and `specs.run_set` reduced to thin adapters that keep their names and signatures. Three reasons, in order of weight: it is already the shared engine (four reachable verbs plus `aw finish` reach it, against one each for the others), it already holds the capabilities the flag paths lack (multi-selector batch, setid resolution, `--force`, structured output), and `2lcqno`'s setid semantics plus `z7nbn1`'s one-action-table thesis are both already implemented there. Extracting a new module would mean rewriting four working callers to gain nothing the delegation does not already give.

## Coverage findings

- "- The bare suite `python3 -m pytest` after the final child, with the `N passed` line pasted, and its failure SET compared BY NAME against the baseline re-derived before the Set began. Counts alone are insufficient: `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` is red at base for part of every day on the local-versus-UTC clock skew, so an unchanged count can hide a real change and a changed count can mean only that the clock moved."
- "- `AW_NO_REEXEC=1 aw check release-gates`, since the Set closes at least two release-gated carriers."
- "- For each child, every `V-*` carries pasted evidence rather than an assertion of success. A `V-*` whose "Observed evidence" is empty or paraphrased fails this check even if the child is marked executed."
- "- The cross-IPD checks in "Cross-IPD validation" above, each answered explicitly."
- "- NO AXIS IS FIXED TWICE, AND NO AXIS IS FIXED BY NOBODY. Check the eight expected-difference assertions child 02 records against the flips children 03, 04 and 05 claim: each must be flipped by exactly one child, and any assertion still unflipped at the end must correspond to a Section 7 axis with a live carrier. An assertion flipped by two children means one of them widened past its reviewed scope."
- "- NO CARRIER IS CLOSED ON A PARTIAL FIX. Children 03 and 05 both close backlog items. For each close, confirm the item's OWN scope is satisfied, not merely that this Set touched the area: the clock items name five local-clock call sites in `backlog.py` and the Set removes one, so closing one of them would assert a repository-wide fix that did not happen (`AGENTS.md` close-legitimacy rule)."
- "- THE THREE RETROSPECTIVE PARITY FILES PASS AFTER EVERY CHILD, not only at the end. Each exists because an asymmetry on that axis caused a release-blocking defect, so they are the Set's regression surface: a failure means a migration reintroduced one of the three defects the Set exists to prevent."
- "- NO CHILD READS PRODUCTION SOURCE TO PROVE UNIFICATION. Confirm no test added by any child uses `inspect`, `ast`, regex or substring search over production source, counts callers, or asserts docstring text (`AGENTS.md`, GUIDING_PRINCIPLES P16, `wy9aru` S1). "There is now one implementation" is the single most tempting claim to pin with `grep`, and a code-structure pin is forbidden outright."
- "- `tests/test_set_dispatch_parity.py` passes identically under the machine's local timezone and under `TZ=UTC`, so no cross-spelling assertion carries a clock dependency."
- "- The bare suite's failure SET is unchanged except for tests the children explicitly named in advance."
- "- Every axis spec `wy9aru` Section 7 assigns elsewhere remains OPEN under its own carrier, except where a child's measured evidence proves its item COMPLETE against the item's own scope."

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
  - Required evidence: `m1jlwm`'s executed path and lint result; the re-measured refusals for both bypasses on BOTH spellings quoted from its V-01 and V-02; and `h4fiwa` and `fv4b6s` read back showing `- Status: done` with the evidence citation recorded, confirming the SATISFIED route rather than a cleared gate.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `m94eht`'s executed path and lint result; `wy9aru`'s `- Status:` quoted as `approved` with its OQ-1 answer, proving the dependency edge was satisfied rather than bypassed; the `1525-02` R2 amendment diff; and the harness's specs agreement assertions shown passing unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `vhiqo6`'s executed path and lint result; pasted `git status --porcelain` from its V-04 showing a single `R` rename for a backlog status change; the three retrospective parity files' results quoted from its V-05; the `runner_shared.close_backlog_item` end-to-end evidence; and its six per-carrier COMPLETE-or-PARTIAL verdicts, with confirmation that no PARTIAL item was closed.
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

Post-gate lifecycle: this orchestrator is retired to `.aw/records/plans/executed/` only once ALL FIVE
children are `executed` on disk. The backlog item `fcnz1r` is set to `graduated` by the runner upon
verification; no plan in this Set sets it, and no agent should set it `done`, since `graduated` means
the design is handed off while `done` means the code is written and validated.
