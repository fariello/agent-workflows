# IPD: Resolve color depth once in term.py and add the authored 16-color tier with aw config pinning

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` R9.3a.2 requires ONE color-depth resolver and states that nothing in the package resolves depth today. Verified 2026-09-19 and the claim holds exactly: `term.should_color` returns a plain boolean, and `COLORTERM` and `256color` grep to ZERO occurrences across `agent_workflows/`. So the 256/16/none ladder DECISIONS D42 requires has no implementation, and Section 5's palette would be emitted unconditionally to a 16-color terminal. R9.3a.4 additionally requires the depth be user-pinnable through `aw config`, because detection cannot see a colorblind user and Section 5 places `blocked` (208) and `waiting-input` (214) on an adjacent orange pair.
- Scope: IN: one depth resolver beside `should_color` in `term.py` implementing the R9.3a.2 precedence chain; the AUTHORED 16-color palette of R9.3a.3 with its named collapses; an `aw config` key pinning the depth, refusing an invalid value with a message naming the accepted set; and the A12a-A12d tests. OUT: the semantic stage table itself (child `udgilu`), the lifecycle rendering helpers (child `bn026f`), and any consumer conversion. Also OUT: a per-stage color override beyond what R9.3a.4 marks SHOULD, which is recorded as deferred with its reason rather than silently dropped.
- Scope-Paths: agent_workflows/term.py, agent_workflows/config.py, tests/test_term.py, tests/test_config.py
- Item-Dependencies: executed:yaxr4i, executed:udgilu
- Status: to-review
- Set: lifeglyph
- Order: 3
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: pow5sj
- From-Spec: uonrjg
- Blocks-Release: next

## Workflow history

- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from spec uonrjg Section 9.3a (R9.3a.1-R9.3a.5) and criteria A12a-A12d. Carries the spec's `Blocks-Release: next` gate.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the color depth a single resolved value with a documented precedence chain, give a 16-color terminal an authored palette rather than a mechanical approximation, and let a user pin the depth so the accessibility remedy does not depend on detection seeing something it cannot see.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The depth resolver

- [ ] E-01 Add a single color-depth resolver beside `should_color` in `agent_workflows/term.py`, implementing the R9.3a.2 precedence chain highest-first: `NO_COLOR`/`--no-color`/`TERM=dumb`/non-TTY yields none unconditionally; then an explicit user depth setting; then detected capability via `COLORTERM`/`TERM`; then the default of 256.
  - Depends on: none
  - Expected outcome: Exactly one definition of depth in the package. `NO_COLOR` with a pinned depth still yields none, because an accessibility convention outranks a preference. The default is 256, not the most conservative rung.
  - Execution state: pending

### Task group 2: The authored 16-color tier

- [ ] E-02 Add the AUTHORED 16-color palette required by R9.3a.3 as an explicit table, NOT a mechanical nearest-neighbour mapping of the 11 distinct 256 indices. It MUST preserve three separations: `ready` is not `done`, `blocked` is not `failed`, `waiting-input` is not `blocked`.
  - Depends on: E-01
  - Expected outcome: A 16-color context renders from the authored table. The three separations hold, and the two EXPECTED collapses are present: the five active subtypes plus `active` to one yellow, and the grays (`parked`, `superseded`, `abandoned`, `unknown`, `none`, `formative`) to one neutral.
  - Execution state: pending

### Task group 3: User configurability

- [ ] E-03 Add an `aw config` key pinning the color depth, and make an invalid value REFUSED at validation with a message naming the accepted set. Note this needs a value-constraint mechanism that `ConfigKeySpec` does not currently have (see F-03), so decide and record whether to extend `ConfigKeySpec` declaratively or validate at the setter.
  - Depends on: E-01
  - Expected outcome: A user can pin the depth; an invalid value is refused with the accepted set named; a pinned depth does NOT defeat `NO_COLOR`.
  - Execution state: pending

### Task group 4: The tier tests

- [ ] E-04 Add the A12a and A12c tests: assert each rung of the precedence chain explicitly, including the `NO_COLOR`-beats-pinned-depth case the spec singles out as the one an implementation is most likely to get backwards, plus config refusal of an invalid value.
  - Depends on: E-03
  - Expected outcome: Each rung asserted separately rather than inferred from one composite case. The `NO_COLOR`-with-pin case is its own named test.
  - Execution state: pending

- [ ] E-05 Add the A12b and A12d tests: render one fixture at all three tiers and assert the three separations survive 16-color, the expected collapses are present, and at EVERY tier the glyph and native word are both present so no state is distinguishable by color alone.
  - Depends on: E-02, E-04
  - Expected outcome: One fixture, three tiers, with the R9.3a.5 invariant asserted at each. The collapse assertions pin the 16-color table so a later change cannot quietly re-expand it into colors a 16-color terminal cannot show.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Verified 2026-09-19: `grep -rn "COLORTERM\|256color" --include=*.py agent_workflows/` returns ZERO matches, and `term.should_color` (term.py:90) returns a plain bool documenting only the NO_COLOR/FORCE_COLOR/TTY precedence. The spec's "nothing resolves depth today" claim is accurate.
- Verified 2026-09-19: `AW_ASCII_ONLY` and `FORCE_ASCII` are already implemented in `term.py`, so criterion A12 tests EXISTING behavior rather than new work. The spec says so itself and it checks out.
- `config.CONFIG_SCHEMA` (config.py:90) is a declarative `Dict[str, ConfigKeySpec]`, so ADDING a key is a schema entry. But see F-03: constraining its VALUES is not.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md.
- `- Readiness:` is deliberately absent (it is `/plan-review`'s output; IPD-M107 refuses an unattested value).

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | No depth resolution exists, so the D42 ladder is entirely unimplemented and Section 5's 256 palette would reach a 16-color terminal unchanged. | `COLORTERM`/`256color` grep to zero in `agent_workflows/`; `term.should_color` returns bool (term.py:90-102). |
| F-02 | High | The accessibility need is concrete rather than theoretical: Section 5 puts `blocked` at 208 and `waiting-input` at 214, an adjacent orange pair, which is exactly what a colorblind user may not distinguish and what detection cannot detect. | `uonrjg` Section 5 table; R9.3a.4 rationale ("DETECTION CANNOT SEE THE USER"). |
| F-03 | Medium | The spec's OQ-01 resolution asserts configurability is "a schema entry rather than a new mechanism", and that is only HALF true. `ConfigKeySpec` carries just `key`, `type_name`, `description`, `read_only` (config.py:83-87) with no allowed-values field, and `grep allowed/choices/enum` finds only a hand-rolled `_ALLOWED_REPOS_KEYS` check. So A12c's "REFUSED at validation with a message naming the accepted set" needs a constraint mechanism that does not exist. E-03 names this explicitly rather than inheriting the spec's optimism. | `config.py:83-87`; `_ALLOWED_REPOS_KEYS` at config.py:652,973 is a bespoke check, not a schema feature. |

## Proposed changes (ordered, validatable)

1. One depth resolver beside `should_color` with the R9.3a.2 chain (E-01).
2. The authored 16-color table preserving three separations and two collapses (E-02).
3. An `aw config` depth key with value refusal, extending the constraint mechanism as F-03 requires (E-03).
4. Per-rung precedence tests including NO_COLOR-beats-pin (E-04).
5. Three-tier fixture tests asserting the R9.3a.5 invariant (E-05).

## Deferred / out of scope (with reason)

- The per-stage color override: R9.3a.4 marks the depth pin a MUST and the per-stage override a SHOULD. Deferring the SHOULD is legitimate, but the reason is proportionality rather than effort: a per-stage override multiplies the config surface by 21 stages and needs its own validation and precedence story, while the depth pin already delivers the accessibility remedy F-02 names. Recorded here rather than dropped; criterion A12c's "where implemented" wording anticipates exactly this.
  - Carrier-Declined: R9.3a.4 makes the depth pin a MUST and the per-stage override a SHOULD, and criterion A12c's own wording ("where implemented") anticipates the override being absent. The accessibility remedy F-02 names is delivered by the depth pin, so no requirement is left unmet. Recorded as a deliberate proportionality judgement rather than deferred work; if a user later needs per-stage control it is a new request, not an unpaid debt of this plan.
- The semantic stage table, the rendering helpers, and consumer conversion: children `udgilu`, `bn026f`, and `f9t5hz` onward.
  - Carrier: bn026f
- Truecolor: the spec's ladder is 256/16/none per D42 and names no truecolor rung, so adding one would exceed the spec.
  - Carrier-Declined: OUT OF SPEC rather than deferred. DECISIONS D42 defines the ladder as 256/16/none and names no truecolor rung, so there is no requirement to carry. Adding one would exceed the spec this plan implements.

## Scope check

- Over-scope: none. Every E-item maps to an R9.3a requirement or an A12a-A12d criterion.
- Under-scope: none. Note F-03 identifies work the spec did not anticipate (a config value-constraint mechanism); it is IN scope here via E-03 rather than deferred, because A12c cannot be satisfied without it.

## Required tests / validation

Run the suite BARE: `python3 -m pytest`. Paste the actual summary line. New and extended tests must cover criteria A12a (each precedence rung, explicitly), A12b (the three separations plus the two expected collapses at 16-color), A12c (config pin accepted, invalid value refused with the set named, pin does not defeat `NO_COLOR`), and A12d (glyph and word present at all three tiers).

## Spec / documentation sync

No `.spec.md` edit in this child, deliberately: the accessibility lens was ALREADY corrected during the spec's own review (verified 2026-09-19 at `.aw/system/workflows/assess/lenses/accessibility.md`, which now states the 256/16/none ladder, that a user's explicit choice outranks detection, and that `NO_COLOR` still wins), so the amendment OQ-01 called for is discharged and must not be re-applied. The `25kzda` Section 5.6 amendment is child `7p3tt8`'s. User-facing documentation of the new config key is part of child `7p3tt8`'s documentation item.

## Open questions

### OQ-01: Extend ConfigKeySpec declaratively, or validate the depth value at the setter?

- Blocking: no
- Status: open
- Owner: none
- Carrier-Declined: AN IMPLEMENTATION CHOICE MADE DURING THIS PLAN'S OWN EXECUTION, with both routes conforming. E-03 requires the choice be recorded and V-03 requires naming which route was taken, so the decision is captured in this plan's own evidence rather than handed onward. Criterion A12c is satisfied either way, so no requirement is left outstanding.
- Resolution or deferral rationale: NOT BLOCKING because either route satisfies A12c and the choice is an ordinary implementation judgement the executing agent can make from the code. Recorded because F-03 shows the spec assumed this was free and it is not, so an agent should choose DELIBERATELY rather than discovering the gap mid-execution. The declarative route (an optional allowed-values field on `ConfigKeySpec`) generalizes to future enum keys and is the better shape if any other key wants it; the setter-local route is smaller and matches the existing `_ALLOWED_REPOS_KEYS` precedent. Whichever is chosen, A12c requires the refusal message to NAME the accepted set, which rules out a bare type error.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste `grep -c` proving exactly ONE depth-resolver definition exists in the package (R9.3a.2 requires one definition). Paste the resolver's output under each input condition of the precedence chain.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the authored 16-color table and the resolved 16-color value for each of the 21 stages. Explicitly show `ready` differing from `done`, `blocked` from `failed`, and `waiting-input` from `blocked`. Show the five active subtypes plus `active` sharing one yellow, and the grays sharing one neutral.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the successful `aw config` set of a valid depth, then the REFUSAL of an invalid one with its message showing the accepted set. Paste the chosen mechanism (declarative field or setter check) and say which OQ-01 route was taken.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the per-rung test output, with the `NO_COLOR`-plus-pinned-depth case named and passing separately from the others. A composite test covering the chain in one assertion FAILS this item, since A12a requires each rung asserted explicitly.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the same fixture rendered at 256, at 16, and at none, side by side. At every tier both the glyph and the native word must be visible. Paste the collapse assertions proving they are pinned.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved pow5sj --by-human`). Its `- Item-Dependencies: executed:yaxr4i, executed:udgilu` edges are re-checked at dispatch: `yaxr4i` because it settles the `--color`/`--no-color` flag surface this resolver's top rung reads, and `udgilu` because the 16-color table is authored against the stage vocabulary that child defines.

On completion: append the workflow-history line, set the terminal `Status: executed`, and `git mv` this plan to `.aw/records/plans/executed/` as a post-gate lifecycle step via `aw ipd finalize`, never as a checklist item. Commit path-scoped; never push.
