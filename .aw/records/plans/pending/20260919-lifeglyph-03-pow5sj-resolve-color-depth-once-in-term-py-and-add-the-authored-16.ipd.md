# IPD: Resolve color depth once in term.py and add the authored 16-color tier with aw config pinning

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` R9.3a.2 requires ONE color-depth resolver and states that nothing in the package resolves depth today. Verified 2026-09-19 and the claim holds exactly: `term.should_color` returns a plain boolean, and `COLORTERM` and `256color` grep to ZERO occurrences across `agent_workflows/`. So the 256/16/none ladder DECISIONS D42 requires has no implementation, and Section 5's palette would be emitted unconditionally to a 16-color terminal. R9.3a.4 additionally requires the depth be user-pinnable through `aw config`, because detection cannot see a colorblind user and Section 5 places `blocked` (208) and `waiting-input` (214) on an adjacent orange pair.
- Scope: IN: one depth resolver beside `should_color` in `term.py` implementing the R9.3a.2 precedence chain; the AUTHORED 16-color palette of R9.3a.3 with its named collapses; an `aw config` key pinning the depth, refusing an invalid value with a message naming the accepted set; and the A12a-A12d tests. OUT: the semantic stage table itself (child `udgilu`), the lifecycle rendering helpers (child `bn026f`), and any consumer conversion. Also OUT: a per-stage color override beyond what R9.3a.4 marks SHOULD, which is recorded as deferred with its reason rather than silently dropped.
- Scope-Paths: agent_workflows/term.py, agent_workflows/config.py, tests/test_term.py, tests/test_config.py
- Item-Dependencies: executed:yaxr4i, executed:udgilu, executed:z8ddk0
- Status: approved
- Readiness: go-pending-approval
- Set: lifeglyph
- Order: 3
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: pow5sj
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved
- From-Spec: uonrjg
- Blocks-Release: next

## Workflow history
- 2026-09-20 executed (opencode its_direct/pt3-claude-opus-5-1m-us, lane `pow5sj` of run-20260920T181010Z-757518): E-01..E-05 performed, V-01..V-05 verified with pasted evidence. Suite BARE: `1 failed, 7500 passed, 3 skipped, 2 xfailed` (baseline was `8369 passed, 3 skipped, 2 xfailed`; totals are not comparable across these runs and node ids were compared instead, as this plan's Required-tests section directs). THE ONE FAILURE IS PRE-EXISTING AND UNRELATED, proven by stashing every change and re-running it red: `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`, which asserts `OPENCODE_CONFIG_CONTENT` is absent from a non-isolated turn's environment and fails because this lane itself runs under that variable. OQ-02 IMPLEMENTED AS RULED (READING A): `FORCE_COLOR` keeps its override of `NO_COLOR`, the shipped `test_force_color_overrides_no_color` still passes UNCHANGED, no behavior changed, so NEITHER conditional spec amendment applied and no `.spec.md` was added to `- Scope-Paths:`. OQ-01 resolved to the DECLARATIVE route (`ConfigKeySpec.allowed_values`), proven general against a second key. ONE DEFECT CAUGHT BY THIS PLAN'S OWN NEW GUARD during execution: the palette's first draft merged `authority-queued` (135) onto `blocked`'s magenta (208), a merge R9.3a.3 names no collapse for and that none of the three required separations covers; fixed to bright magenta and now refused at import. TWO OUT-OF-SCOPE TEST EDITS, both narrowing a whole-set snapshot to the claim it exists to make, neither weakening a check: `tests/test_run_analytics_wizard.py` (pinned `_ALLOWED_TOP_KEYS` exactly, so any new config key failed an analytics test) and `tests/test_term_components.py` (pinned the `term` palette-dict list exactly, so the spec-REQUIRED second LADDER RUNG read as a rival palette); recorded as D-02/D-03 and filed as backlog `yzwfql` because the brittleness pattern outlives this instance. F-06's "38 call sites" figure corrected to 58 by measurement (it predated siblings `z8ddk0`/`yaxr4i`); the substance, that this child converts no consumer, holds and is shown by the diff.
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-19 readiness re-check (opencode its_direct/pt3-claude-opus-5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates at HEAD `f12390d7` and each was found clear: `plan_readiness.has_unresolved_blocking_question` -> False (the round-1 blocker OQ-02 is now `Status: resolved`); `review_findings.subject_gating_blocks` -> empty (the round-1 BLOCKER finding is now `FIXED` in the review record, with its resolution recorded there); and `plan_readiness.newest_verdict` polarity -> neutral, not negative. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-09-19 reviewed (aw set): plan-review round 1: REVIEWED - OPEN QUESTIONS. PR-302..PR-305 FIXED; PR-301 (BLOCKER) escalated as OQ-02 Blocking: yes (R9.3a.2's 'unconditional' NO_COLOR rung contradicts Section 9.3's preserve-current-FORCE_COLOR requirement; measured FORCE_COLOR currently wins). Readiness no-go.

- 2026-09-19 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-302, PR-303, PR-304, PR-305 FIXED, PR-301 (BLOCKER) escalated as OQ-02 `Blocking: yes`. Reviewed at HEAD `a5ab0515`; `aw ipd lint --phase author --agent` clean, exit 0. THE SPEC SPECIFIES E-01'S TOP RUNG TWICE AND INCOMPATIBLY: R9.3a.2 calls `NO_COLOR -> none` "unchanged, and unconditional", Section 9.3 requires preserving current `FORCE_COLOR` behavior, and the current behavior (measured by execution, not read) is that `FORCE_COLOR` DEFEATS `NO_COLOR` at `term.py:100-104`, pinned by the shipped test `test_force_color_overrides_no_color`. So "unchanged" is false as written and the literal reading breaks a shipped test; a maintainer must rule. ALSO: the resolver's top rung spans two layers, since `term.should_color` cannot see `--no-color` (the flag is applied in `result_types.select_output`), which E-01 now states so nobody adds argparse awareness to `term.py`. Two counting errors corrected from measurement: 20 stages not 21, and R9.3a.3's "four grays" is six by its own list (five at 244 plus `formative` at 245).
- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from spec uonrjg Section 9.3a (R9.3a.1-R9.3a.5) and criteria A12a-A12d. Carries the spec's `Blocks-Release: next` gate.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the color depth a single resolved value with a documented precedence chain, give a 16-color terminal an authored palette rather than a mechanical approximation, and let a user pin the depth so the accessibility remedy does not depend on detection seeing something it cannot see.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The depth resolver

- [x] E-01 Add a single color-depth resolver beside `should_color` in `agent_workflows/term.py`, implementing the R9.3a.2 precedence chain highest-first: `NO_COLOR`/`--no-color`/`TERM=dumb`/non-TTY yields none; then an explicit user depth setting; then detected capability via `COLORTERM`/`TERM`; then the default of 256. The top rung's exact treatment of `FORCE_COLOR` is OQ-02's blocking question; implement whatever it resolves rather than choosing.
  - Depends on: none
  - Expected outcome: Exactly one definition of depth in the package. `NO_COLOR` with a pinned depth still yields none, because an accessibility convention outranks a preference. The default is 256, not the most conservative rung.
  - Execution state: performed

  TWO SEAM FACTS MEASURED AT REVIEW, because "beside `should_color`" is not by itself enough to place this correctly. FIRST, `term.should_color` CANNOT SEE `--no-color`: it reads only `NO_COLOR`, `FORCE_COLOR`, `TERM` and `isatty()` (`term.py:90-114`), and the FLAG is applied one layer up in `result_types.select_output`, which computes `color_enabled = should_color(out_stream)` only `if not getattr(args, "no_color", False)` (`result_types.py:158-160`). So a depth resolver living in `term.py` can implement three of the four top-rung inputs and MUST take the flag's effect as a parameter (or be called only after the flag has been applied) rather than reaching for `args`. Do not add argparse awareness to `term.py`; that is the layering `yaxr4i` E-03 settles by putting the flag layer ABOVE the env layer. SECOND, `should_color` has 38 call sites across 7 modules, so whatever signature the resolver takes must not force a change at any of them; this child converts no consumer.

### Task group 2: The authored 16-color tier

- [x] E-02 Add the AUTHORED 16-color palette required by R9.3a.3 as an explicit table covering all TWENTY stages, NOT a mechanical nearest-neighbour mapping of the 11 distinct 256 indices. It MUST preserve three separations: `ready` is not `done`, `blocked` is not `failed`, `waiting-input` is not `blocked`.
  - Depends on: E-01
  - Expected outcome: A 16-color context renders from the authored table. The three separations hold, and the two EXPECTED collapses are present: the five active subtypes plus `active` to one yellow, and the six gray-family stages (`parked`, `superseded`, `abandoned`, `unknown`, `none`, `formative`) to one neutral.
  - Execution state: performed

  THE 256 TIER VERIFIED AT REVIEW, so the authored table is written against measured facts rather than the spec's prose. Parsing Section 5's table on 2026-09-19 gives exactly 11 distinct indices, which confirms R9.3a.3's own count: `39` review-queued; `45` ready; `46` done; `81` reusable; `135` authority-queued; `196` failed; `208` blocked; `214` waiting-input; `220` the five active subtypes plus `active` (already one color, so that collapse is free); `244` parked/superseded/abandoned/unknown/none; `245` formative.
  NOTE THE GRAY COUNT: R9.3a.3 says "the four grays" and then lists SIX names. The LIST is right and the WORD is wrong, which the measurement settles: five stages sit at 244 and `formative` sits at 245, so six stages collapse into the one neutral. Implement six. The three separations are all genuinely at risk under a mechanical mapping, since 208 versus 196 (blocked/failed) and 214 versus 208 (waiting-input/blocked) are adjacent-ish in the 256 cube while 45 versus 46 (ready/done) are adjacent by index and completely different in meaning; that adjacency is precisely why R9.3a.3 forbids deriving the tier.

### Task group 3: User configurability

- [x] E-03 Add an `aw config` key pinning the color depth, and make an invalid value REFUSED at validation with a message naming the accepted set. Note this needs a value-constraint mechanism that `ConfigKeySpec` does not currently have (see F-03), so decide and record whether to extend `ConfigKeySpec` declaratively or validate at the setter.
  - Depends on: E-01
  - Expected outcome: A user can pin the depth; an invalid value is refused with the accepted set named; a pinned depth does NOT defeat `NO_COLOR`.
  - Execution state: performed

### Task group 4: The tier tests

- [x] E-04 Add the A12a and A12c tests: assert each rung of the precedence chain explicitly, including the `NO_COLOR`-beats-pinned-depth case the spec singles out as the one an implementation is most likely to get backwards, plus config refusal of an invalid value.
  - Depends on: E-03
  - Expected outcome: Each rung asserted separately rather than inferred from one composite case. The `NO_COLOR`-with-pin case is its own named test.
  - Execution state: performed

- [x] E-05 Add the A12b and A12d tests: render one fixture at all three tiers and assert the three separations survive 16-color, the expected collapses are present, and at EVERY tier the glyph and native word are both present so no state is distinguishable by color alone.
  - Depends on: E-02, E-04
  - Expected outcome: One fixture, three tiers, with the R9.3a.5 invariant asserted at each. The collapse assertions pin the 16-color table so a later change cannot quietly re-expand it into colors a 16-color terminal cannot show.
  - Execution state: performed

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
| F-04 | High | R9.3a.2's top rung and Section 9.3 CONTRADICT each other on `FORCE_COLOR`, so E-01 cannot be written without a ruling. R9.3a.2 calls `NO_COLOR -> none` "unchanged, and unconditional"; Section 9.3 requires preserving current `FORCE_COLOR` behavior; and the current behavior is that `FORCE_COLOR` DEFEATS `NO_COLOR`. So "unchanged" is false as written, and the literal reading breaks a shipped test. Carried as blocking OQ-02. | Measured by execution 2026-09-19: `NO_COLOR=1` + `FORCE_COLOR=1` on a fake TTY -> `should_color` returns True; implemented at `term.py:100-104`; pinned by `tests/test_term.py:48-52` `test_force_color_overrides_no_color`. |
| F-05 | Medium | Two counting errors inherited from prose rather than measurement. (a) The plan says "21 stages" in two places; Section 5 holds 20, and the spec's own D13 rejects "a new 21st stage", which only parses at 20. (b) R9.3a.3 says "the four grays" then lists SIX names; the list is right and the word is wrong, since five stages sit at 244 and `formative` at 245. Left uncorrected, V-02's dump would assert a count that cannot hold and the neutral collapse would be built for four of six stages. | Section 5 parsed -> 20 rows, 11 distinct indices; `uonrjg` D13; spec line 484 "the four grays (`parked`, `superseded`, `abandoned`, `unknown`, `none`, `formative`)". |
| F-06 | Medium | `term.should_color` cannot see `--no-color`, so the resolver's top rung is split across two layers. The flag is applied in `result_types.select_output`, not in `term.py`, and `should_color` has 38 call sites across 7 modules. E-01 as authored said only "beside `should_color`", which invites either adding argparse awareness to `term.py` or silently dropping the flag from the chain. | `term.py:90-114` reads only `NO_COLOR`/`FORCE_COLOR`/`TERM`/`isatty`; `result_types.py:158-160` gates on `args.no_color`; `grep -c should_color` -> 38 call sites in 7 modules. |
| F-03 | Medium | The spec's OQ-01 resolution asserts configurability is "a schema entry rather than a new mechanism", and that is only HALF true. `ConfigKeySpec` carries just `key`, `type_name`, `description`, `read_only` (config.py:83-87) with no allowed-values field, and `grep allowed/choices/enum` finds only a hand-rolled `_ALLOWED_REPOS_KEYS` check. So A12c's "REFUSED at validation with a message naming the accepted set" needs a constraint mechanism that does not exist. E-03 names this explicitly rather than inheriting the spec's optimism. | `config.py:83-87`; `_ALLOWED_REPOS_KEYS` at config.py:652,973 is a bespoke check, not a schema feature. |

## Proposed changes (ordered, validatable)

1. One depth resolver beside `should_color` with the R9.3a.2 chain (E-01).
2. The authored 16-color table preserving three separations and two collapses (E-02).
3. An `aw config` depth key with value refusal, extending the constraint mechanism as F-03 requires (E-03).
4. Per-rung precedence tests including NO_COLOR-beats-pin (E-04).
5. Three-tier fixture tests asserting the R9.3a.5 invariant (E-05).

## Deferred / out of scope (with reason)

- The per-stage color override: R9.3a.4 marks the depth pin a MUST and the per-stage override a SHOULD. Deferring the SHOULD is legitimate, but the reason is proportionality rather than effort: a per-stage override multiplies the config surface by 20 stages and needs its own validation and precedence story, while the depth pin already delivers the accessibility remedy F-02 names. Recorded here rather than dropped; criterion A12c's "where implemented" wording anticipates exactly this.
  - Carrier-Declined: R9.3a.4 makes the depth pin a MUST and the per-stage override a SHOULD, and criterion A12c's own wording ("where implemented") anticipates the override being absent. The accessibility remedy F-02 names is delivered by the depth pin, so no requirement is left unmet. Recorded as a deliberate proportionality judgement rather than deferred work; if a user later needs per-stage control it is a new request, not an unpaid debt of this plan.
- The semantic stage table, the rendering helpers, and consumer conversion: children `udgilu`, `bn026f`, and `f9t5hz` onward.
  - Carrier: bn026f
- Truecolor: the spec's ladder is 256/16/none per D42 and names no truecolor rung, so adding one would exceed the spec.
  - Carrier-Declined: OUT OF SPEC rather than deferred. DECISIONS D42 defines the ladder as 256/16/none and names no truecolor rung, so there is no requirement to carry. Adding one would exceed the spec this plan implements.

## Scope check

- Over-scope: none. Every E-item maps to an R9.3a requirement or an A12a-A12d criterion. Note the CONDITIONAL exception in Spec / documentation sync: if OQ-02 is resolved the literal way, amending Section 9.3 is in scope only once the `uonrjg` spec path is declared.
- Under-scope: ONE GAP, found at review and carried as blocking OQ-02. E-01 could not have been written as authored because the spec specifies its top rung twice and incompatibly (R9.3a.2 "unconditional" versus Section 9.3 "preserve current `FORCE_COLOR` behavior", where current behavior lets `FORCE_COLOR` win). Otherwise complete: F-03 identifies work the spec did not anticipate (a config value-constraint mechanism) and it is IN scope here via E-03 rather than deferred, because A12c cannot be satisfied without it.

## Required tests / validation

Run the suite BARE: `python3 -m pytest`. Paste the actual summary line. New and extended tests must cover criteria A12a (each precedence rung, explicitly), A12b (the three separations plus the two expected collapses at 16-color), A12c (config pin accepted, invalid value refused with the set named, pin does not defeat `NO_COLOR`), and A12d (glyph and word present at all three tiers).

REUSE THE SHIPPED HARNESS rather than building one: `tests/test_term.py` already exercises the `NO_COLOR`/`FORCE_COLOR`/`TERM=dumb`/isatty matrix against `_FakeTTY()` and `_FakePipe()` stream doubles with a `_clear()` env helper (`tests/test_term.py:38-65`), which is exactly the shape the per-rung A12a tests need. A depth rung slots into that class; do not introduce a second stream-double pattern.

BASELINE, measured in this lane at HEAD `a5ab0515` on 2026-09-19 so an executor can tell a pre-existing failure from one it caused:

```text
8369 passed, 3 skipped, 2 xfailed in 100.98s (0:01:40)
```

Compare NODE IDS, not totals: this child ADDS tests, so the total is expected to rise, and only a NEW failing node id is a regression. Watch `tests/test_term.py::...::test_force_color_overrides_no_color` specifically, since OQ-02's ruling decides whether it must keep passing. Do NOT add `-n0`, a second `-q`, or `-p no:randomly` per AGENTS.md.

## Spec / documentation sync

No `.spec.md` edit in this child AS CURRENTLY SCOPED, deliberately: the accessibility lens was ALREADY corrected during the spec's own review (verified again at review 2026-09-19 at `.aw/system/workflows/assess/lenses/accessibility.md:56-65`, which now states the 256/16/none ladder, that a user's explicit choice outranks detection, and that "`NO_COLOR` still wins over any such setting"), so the amendment OQ-01 called for is discharged and must not be re-applied. The `25kzda` Section 5.6 amendment is child `7p3tt8`'s. User-facing documentation of the new config key is part of child `7p3tt8`'s documentation item.

TWO CONDITIONAL SPEC EDITS, recorded here because AGENTS.md requires a spec edit be DECLARED before it is made, and `- Scope-Paths:` is deliberately left unchanged at review since both are contingent on rulings that have not happened. FIRST, if OQ-02 resolves the LITERAL way (`NO_COLOR` beats `FORCE_COLOR` absolutely), Section 9.3's "MUST preserve current `FORCE_COLOR` behavior" must be amended in the same change, because the new behavior would contradict it. SECOND, regardless of that ruling, R9.3a.3's "the four grays" is wrong beside its own six-name list and SHOULD be corrected to six so the next implementer is not misled. Either edit requires adding `.aw/records/specs/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md` to `- Scope-Paths:` FIRST, since both runners announce declared spec edits before a run and the finalize scope gate reconciles what changed against what was declared. Do not edit the spec without that declaration.

## Open questions

### OQ-01: Extend ConfigKeySpec declaratively, or validate the depth value at the setter?

- Blocking: no
- Status: open
- Owner: none
- Carrier-Declined: AN IMPLEMENTATION CHOICE MADE DURING THIS PLAN'S OWN EXECUTION, with both routes conforming. E-03 requires the choice be recorded and V-03 requires naming which route was taken, so the decision is captured in this plan's own evidence rather than handed onward. Criterion A12c is satisfied either way, so no requirement is left outstanding.
- Resolution or deferral rationale: NOT BLOCKING because either route satisfies A12c and the choice is an ordinary implementation judgement the executing agent can make from the code. Recorded because F-03 shows the spec assumed this was free and it is not, so an agent should choose DELIBERATELY rather than discovering the gap mid-execution. The declarative route (an optional allowed-values field on `ConfigKeySpec`) generalizes to future enum keys and is the better shape if any other key wants it; the setter-local route is smaller and matches the existing `_ALLOWED_REPOS_KEYS` precedent. Whichever is chosen, A12c requires the refusal message to NAME the accepted set, which rules out a bare type error.

### OQ-02: Does `FORCE_COLOR` still override `NO_COLOR` at the new depth resolver, or is R9.3a.2's "unconditional" top rung a deliberate behavior change?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-301
- Carrier: nyz8dt
- Resolution: RESOLVED BY THE MAINTAINER 2026-09-19, AS READING A, AND THE RULING IS WIDER THAN THE QUESTION ASKED. `FORCE_COLOR` KEEPS its escape hatch over `NO_COLOR`, so the top rung is `NO_COLOR AND NOT FORCE_COLOR`, `tests/test_term.py:48` keeps passing, and R9.3a.2's "unconditional" is read as unconditional with respect to the DEPTH PIN only. This plan's E-01 is therefore written against current behavior and changes none of it.
  THE RULING ALSO SETTLED TWO THINGS THIS QUESTION DID NOT ASK, both recorded on backlog `nyz8dt` (`Work-Kind: bug`, `Blocks-Release: next`) rather than here, because they are a pre-existing correctness defect in three files this Set does not own. FIRST, `NO_COLOR` IS PRESENCE-ONLY: any setting disables, including the empty string, and no value is interpreted. The reason is CONSISTENCY WITH THE TOOLS OUR USERS ALREADY RUN, measured on a TTY 2026-09-19: for every non-empty value (`0`, `false`, `no`, `off`, `1`) `rg` 14.x, `bat` 0.24.0 and `fd` 9.0.0 are UNANIMOUS that it disables, so interpreting falsey words would make `aw` the only tool in a user's terminal that keeps color at `NO_COLOR=0`. On the EMPTY string the ecosystem is split two to one (`rg` and `bat` disable, `fd` ignores), so the majority was chosen and the divergence is recorded rather than hidden. SECOND, `FORCE_COLOR` INTERPRETS ITS VALUE: `0`/`false`/`no`/`off` mean NOT FORCING and fall through to ordinary TTY detection, per the maintainer's tri-state principle that a prohibition being off does not mean the opposite is on. None of the three tools implements `FORCE_COLOR`, so the Node convention it came from (`0` disables, `1`/`2`/`3` select depth) is the only precedent, and today's behavior of `FORCE_COLOR=0` forcing color ON even to a pipe is backwards under it.
  WHAT THIS PLAN MUST DO WITH THAT: E-01 consumes the single unified `should_color` and MUST NOT reimplement the precedence locally. THE UNIFICATION IS NOW A SIBLING, NOT A BACKLOG ITEM: the maintainer ruled 2026-09-19 to convert backlog `nyz8dt` into child `z8ddk0` of this Set, and this plan now declares `executed:z8ddk0`, so the seam is already one definition when E-01 runs. CORRECTING WHAT THIS RESOLUTION FIRST SAID, because it was wrong and a later reader would otherwise inherit it: an earlier revision claimed the unification was "sequenced after `yaxr4i`" so that the resolver would not be written twice. That was false. `yaxr4i` line 97 asserts "The color ENGINE is already correct and complete... it does not need new color logic", a premise the 2026-09-19 measurements FALSIFY, so `yaxr4i` would never have fixed the divergence and there was no double-write to avoid.
- Resolution or deferral rationale: BLOCKING because the spec answers it BOTH WAYS in adjacent sections and this plan's E-01 cannot be written without a ruling. Section 9.3a.2 lists `NO_COLOR / --no-color / TERM=dumb / non-TTY -> none` and calls that rung "unchanged, and unconditional", and its commentary says plainly that `NO_COLOR` "is an accessibility convention and a preference may not defeat it". But Section 9.3, four lines earlier, requires that "The system MUST preserve current `NO_COLOR`, `FORCE_COLOR`, `TERM=dumb`, TTY ... behavior", and the CURRENT behavior is that `FORCE_COLOR` DOES defeat `NO_COLOR`. Measured at review on 2026-09-19 by execution, not by reading: with `NO_COLOR=1` and `FORCE_COLOR=1` on a fake TTY, `term.should_color` returns **True**, implemented at `term.py:100-104` ("NO_COLOR: any value (even empty) disables, UNLESS FORCE_COLOR is set") and PINNED by a shipped test named `test_force_color_overrides_no_color` (`tests/test_term.py:48-52`).
  SO THE WORD "unchanged" IN R9.3a.2 IS FALSE AS WRITTEN, and the two readings lead to different code and different tests. READING A (preserve current behavior): the top rung is `NO_COLOR AND NOT FORCE_COLOR`, the existing test keeps passing, and R9.3a.2's "unconditional" is loose wording for "unconditional with respect to the DEPTH PIN" rather than with respect to `FORCE_COLOR`. READING B (literal): `NO_COLOR` wins absolutely, which CONTRADICTS Section 9.3, BREAKS `test_force_color_overrides_no_color`, and changes shipped behavior for anyone who sets both. A12a's own text ("`NO_COLOR` with a pinned depth still yields plain text") only ever contrasts `NO_COLOR` with the PIN, never with `FORCE_COLOR`, which is weak evidence for Reading A.
  REVIEWER'S RECOMMENDATION IS READING A: it satisfies both sections at once (the pin never defeats `NO_COLOR`, which is the accessibility promise the spec actually argues for, while `FORCE_COLOR`'s shipped escape hatch survives), it changes no behavior, and it breaks no test. Reading B would be a deliberate behavior change to a documented convention and needs its own decision, its own Section 9.3 amendment, and the deletion of a shipped test. But this is a MAINTAINER call because it is a user-visible behavior question on an `approved`, `Blocks-Release: next` spec, and whichever way it goes the spec should be amended so the next reader is not caught by the same contradiction. If Reading B is chosen, declare the `uonrjg` spec path in `- Scope-Paths:` and amend Section 9.3 in the same change.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste `grep -c` proving exactly ONE depth-resolver definition exists in the package (R9.3a.2 requires one definition). Paste the resolver's output under each input condition of the precedence chain. ALSO paste the OQ-02 ruling being implemented and the resolver's output for the `NO_COLOR=1` PLUS `FORCE_COLOR=1` case, since that is the one input the two spec sections disagree about; an evidence block that omits it FAILS this item. Paste `python3 -m pytest tests/test_term.py -o addopts=""` showing `test_force_color_overrides_no_color` still passing, or, if the ruling deliberately changed it, the spec amendment and the test's replacement. Finally paste a grep proving `term.py` gained no `argparse`/`args` awareness (F-06), and that the 38 existing `should_color` call sites are unchanged.
  - Observed evidence: ONE resolver definition (`term.py:358`) and no other module reading `COLORTERM`/`256color`; every rung measured by execution including `NO_COLOR=1`+`FORCE_COLOR=1` -> `256` (OQ-02 READING A); `test_force_color_overrides_no_color` still PASSES unchanged; `term.py` has zero `argparse`/`args.no_color` occurrences; every `should_color` line in the diff is an addition, so no call site changed. Full pastes below.

    EXACTLY ONE DEFINITION, and no second depth-detection path anywhere in the package:

    ```text
    $ grep -rn "^def resolve_color_depth" --include=*.py agent_workflows/
    agent_workflows/term.py:358:def resolve_color_depth(

    $ grep -rc '^def resolve_color_depth' --include=*.py agent_workflows/ | grep -v ':0'
    agent_workflows/term.py:1

    $ grep -rln "COLORTERM\|256color" --include=*.py agent_workflows/
    agent_workflows/term.py
    ```

    The second grep is the one that makes the first MEANINGFUL: a rival module quietly reading
    `COLORTERM` would be a second depth decision even while the symbol stayed unique. Both
    properties are pinned by `ColorDepthOneDefinitionTests` (AST-based, not substring, per the
    file-local convention), so a regression fails rather than needing a re-grep.

    EVERY RUNG OF THE CHAIN, by execution (`XDG_CONFIG_HOME` pointed at a temporary directory so
    the maintainer's real config cannot influence the reading):

    ```text
    rung4 default (unknown TERM)      -> 256
    rung3 detect TERM=xterm-256color  -> 256
    rung3 detect TERM=xterm-16color   -> 16
    rung3 detect COLORTERM=truecolor  -> 256
    rung1 NO_COLOR=1                  -> none
    rung1 non-TTY (pipe)              -> none
    rung1 TERM=dumb                   -> none
    rung1 override=False (--no-color) -> none
    OQ-02 NO_COLOR=1 + FORCE_COLOR=1  -> 256
    ```

    And the PIN rung, including the case A12a singles out:

    ```text
    unpinned, TERM=xterm-256color     -> 256
    pinned 16 (beats 256 detection)   -> 16
    pinned 16 + NO_COLOR=1            -> none   <-- NO_COLOR beats the pin
    pinned none on a 256 TTY          -> none
    ```

    THE OQ-02 RULING IMPLEMENTED IS READING A (maintainer, 2026-09-19): `FORCE_COLOR` KEEPS its
    escape hatch over `NO_COLOR`, and R9.3a.2's "unconditional" is unconditional with respect to
    the DEPTH PIN only. The `NO_COLOR=1` plus `FORCE_COLOR=1` row above shows `256`, i.e. the
    hatch survives at the depth seam exactly as it does at the boolean one. NO behavior changed
    and no spec amendment is owed, so `- Scope-Paths:` correctly still declares no `.spec.md`.
    The shipped test the ruling turned on still passes, alongside the new depth-level twin:

    ```text
    $ python3 -m pytest "tests/test_term.py::ShouldColorTests::test_force_color_overrides_no_color" \
        "tests/test_term.py::ColorDepthPrecedenceTests::test_force_color_still_overrides_no_color_at_the_depth_resolver" \
        -o addopts="" -v
    tests/test_term.py::ShouldColorTests::test_force_color_overrides_no_color PASSED [ 50%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_force_color_still_overrides_no_color_at_the_depth_resolver PASSED [100%]

    ============================== 2 passed in 0.15s ===============================
    ```

    F-06 DISCHARGED, both halves. `term.py` gained no argparse awareness, and the resolver takes
    the flag as `override=` (forwarded to `should_color`) rather than reaching for a namespace:

    ```text
    $ grep -cn "import argparse\|args\.no_color" agent_workflows/term.py
    0
    ```

    THE 38 EXISTING `should_color` CALL SITES ARE UNCHANGED, verified by the stronger check of
    reading the diff rather than re-counting: every `should_color` line in the diff is an ADDITION
    (a `+`), so no existing call site or signature was edited.

    ```text
    $ git diff agent_workflows/term.py | grep -E "^[-+].*should_color"
    +    1. COLOR IS OFF ENTIRELY -> ``'none'``. Delegated WHOLESALE to :func:`should_color`, which
    +    WHY RUNG 1 DELEGATES TO ``should_color`` INSTEAD OF RE-READING THE ENVIRONMENT (this is the
    +    when it unified three divergent ``should_color`` implementations, and which
    +    ``override`` is forwarded to :func:`should_color` unchanged and carries the same meaning, so a
    +    if not should_color(stream, override=override):
    ```

    CORRECTING THE PLAN'S OWN FIGURE, since honesty outranks matching the authored number: the
    plan (and F-06) say "38 call sites", and the occurrence count at this HEAD is 58 across 9
    modules, not 38. The 38 was measured before siblings `z8ddk0` and `yaxr4i` landed, both of
    which added call sites and delegations. The SUBSTANCE of the requirement (this child converts
    no consumer) holds and is proven by the diff above; only the count was stale.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the authored 16-color table and the resolved 16-color value for each of the TWENTY stages (20, not 21: the count is measured from Section 5's table and corroborated by the spec's own D13, which rejects "a new 21st stage"). A dump covering fewer than 20 stages, or asserting 21, FAILS this item. Explicitly show `ready` differing from `done`, `blocked` from `failed`, and `waiting-input` from `blocked`. Show the five active subtypes plus `active` sharing one yellow, and all SIX gray-family stages (`parked`, `superseded`, `abandoned`, `unknown`, `none`, `formative`) sharing one neutral.
  - Observed evidence: All TWENTY stages dumped with their 256 index and authored 16-color code (`len(STAGE_ORDER)` = 20, palette entries = 20, coverage asserted against `lifecycle_style.ALL_STAGES` rather than a literal count). The three separations all differ (`ready` 96 / `done` 92; `blocked` 35 / `failed` 31; `waiting-input` 93 / `blocked` 35) and both collapses are single-colored (six active -> SGR 33, six grays -> SGR 90, so F-05(b)'s six-not-four is confirmed). One unnamed merge (`authority-queued` on `blocked`'s magenta) was caught by this item's own new guard and fixed. Full pastes below.

    ALL TWENTY STAGES, in spec Section 5 order, with the 256 index beside the authored 16-color
    SGR code so the authoring decisions can be checked against what they replace:

    ```text
    stage               256    16  name
    ----------------------------------------------
    formative           245    90  bright-black
    review-queued        39    34  blue
    authority-queued    135    95  bright-magenta
    ready                45    96  bright-cyan
    reviewing           220    33  yellow
    executing           220    33  yellow
    verifying           220    33  yellow
    integrating         220    33  yellow
    recovering          220    33  yellow
    active              220    33  yellow
    waiting-input       214    93  bright-yellow
    blocked             208    35  magenta
    failed              196    31  red
    done                 46    92  bright-green
    reusable             81    36  cyan
    parked              244    90  bright-black
    superseded          244    90  bright-black
    abandoned           244    90  bright-black
    unknown             244    90  bright-black
    none                244    90  bright-black

    stage count: 20 | palette entries: 20
    ```

    THE COUNT IS 20, NOT 21, and it is measured rather than asserted: `len(LS.STAGE_ORDER)` is 20
    and the palette covers exactly that set (`test_the_palette_covers_every_semantic_stage`
    compares against `lifecycle_style.ALL_STAGES`, so the coverage claim cannot rot the way a
    literal count would). The 256 tier's 11 distinct indices are confirmed independently:
    `[39, 45, 46, 81, 135, 196, 208, 214, 220, 244, 245]`.

    THE THREE REQUIRED SEPARATIONS, each shown to differ:

    ```text
    SEPARATIONS (must differ):
      ready           96 vs done            92  -> differ: True
      blocked         35 vs failed          31  -> differ: True
      waiting-input   93 vs blocked         35  -> differ: True
    ```

    THE TWO EXPECTED COLLAPSES, each one color, and note the gray group is SIX:

    ```text
    COLLAPSES (must be one color each):
      6 stages -> SGR {33}  (reviewing, executing, verifying, integrating, recovering, active)
      6 stages -> SGR {90}  (parked, superseded, abandoned, unknown, none, formative)
    ```

    F-05(b) CONFIRMED BY MEASUREMENT: R9.3a.3's prose says "the four grays" and lists SIX names.
    The list is right and the word is wrong, because five of those stages sit at 244 and
    `formative` at 245. Six are implemented and `test_the_six_gray_family_stages_collapse_to_one_neutral`
    asserts `len(group) == 6` explicitly, so a future edit cannot quietly build the neutral for four.

    THE TABLE IS AUTHORED, NOT DERIVED, and the evidence is the property a derivation cannot have:
    at 256 `ready`(45) and `done`(46) are ADJACENT BY INDEX, yet they take different named colors
    here. Any nearest-neighbour reduction merges that pair first.

    ONE DEFECT THIS ITEM'S OWN GUARD CAUGHT DURING EXECUTION, recorded because a guard that never
    fires is weak evidence. The first draft gave `authority-queued` PLAIN magenta, the same code as
    `blocked`. Those stages are 135 (purple) and 208 (orange) at 256, so nothing suggested merging
    them, and no REQUIRED separation names either stage, meaning every other assertion passed.
    R9.3a.3 names the collapses it accepts, so an UNNAMED merge is an unreviewed loss of a
    distinction; `authority-queued` is now bright magenta (95), and `validate_16_color_palette` plus
    `test_the_palette_merges_no_pair_outside_a_named_collapse` now refuse ANY merge that no declared
    collapse covers. Also asserted: every code is one of the sixteen named colors, so a 256 index
    cannot leak into the tier.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the successful `aw config` set of a valid depth, then the REFUSAL of an invalid one with its message showing the accepted set. Paste the chosen mechanism (declarative field or setter check) and say which OQ-01 route was taken.
  - Observed evidence: `config set color_depth 16` -> `OK` exit 0, read back as `16`, visible in `config show`; `config set color_depth tru3color` -> `FAIL Invalid value for 'color_depth': 'tru3color'. Accepted values: none, 16, 256.` exit 2, with the previous pin still intact afterwards. OQ-01 ROUTE: the DECLARATIVE one (`ConfigKeySpec.allowed_values`, enforced generically in `set_config_value`), proven general by constraining a second key in `DeclarativeAllowedValuesTests`. Full pastes and the reasoning below.

    THE SUCCESSFUL SET, THE REFUSAL, AND THE MESSAGE NAMING THE ACCEPTED SET. Run against the
    WORKING TREE (`python3 -m agent_workflows`, not the `aw` on PATH, which resolves to the
    installed package and would have tested code this plan did not write), with
    `XDG_CONFIG_HOME` pointed at a temporary directory:

    ```text
    $ python3 -m agent_workflows config set color_depth 16
    OK       color_depth = 16 (saved to <tmpdir>/agent-workflows/config.json)
    exit=0

    $ python3 -m agent_workflows config get color_depth
    16

    $ python3 -m agent_workflows config set color_depth tru3color
    FAIL     Invalid value for 'color_depth': 'tru3color'. Accepted values: none, 16, 256.
    exit=2

    $ python3 -m agent_workflows config get color_depth
    16

    $ python3 -m agent_workflows config show | grep -i color_depth
      color_depth          = 16
    ```

    The refusal NAMES THE ACCEPTED SET (`none, 16, 256`) as A12c requires, exits nonzero, and
    LEAVES THE PREVIOUS PIN INTACT (the last `get` still reads 16), so a typo cannot silently
    clear a working setting.

    OQ-01 ROUTE TAKEN: THE DECLARATIVE ONE. `ConfigKeySpec` gained an optional
    `allowed_values: Optional[Tuple[str, ...]]` field (defaulting to `None`, i.e. unconstrained, so
    no pre-existing key changes behavior), and `set_config_value` enforces it generically for any
    key that declares one. TWO REASONS DECIDED IT over the setter-local check, and both are about
    the NEXT enum key rather than this one. FIRST, the alternative already exists here in its
    hand-rolled form and shows its cost: `_ALLOWED_REPOS_KEYS` is validated by a bespoke
    `if canon_key == "repos"` branch inside `set_config_value`, so every future enum key would add
    another branch to one function and each constraint would live away from the key it constrains.
    SECOND, a declarative field is READABLE BY OTHER SURFACES, which a setter-local `if` cannot
    expose: `aw config show` and shell completion can offer the accepted values without
    re-deriving them.

    THE CHOICE IS PROVEN GENERAL rather than merely claimed: `DeclarativeAllowedValuesTests`
    constrains a DIFFERENT key (`aw_home`) through a patched schema and shows the same refusal
    firing with no new code, and separately asserts every other schema key still has
    `allowed_values is None`. Additional properties pinned: the key survives `normalize()` (it is
    on `_ALLOWED_TOP_KEYS`, without which the pin would be SILENTLY dropped on the next write, the
    exact bug `tests/test_run_analytics_wizard.py` records from an earlier plan); the value is
    stored canonically lower-cased; "unset" stays distinct from "pinned" (absent from
    `default_config()`, so detection remains the default path); and a hand-edited invalid value is
    DROPPED by `normalize` and read as `None` by `get_color_depth`, which is the fail-open
    direction a styling read must take.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the per-rung test output, with the `NO_COLOR`-plus-pinned-depth case named and passing separately from the others. A composite test covering the chain in one assertion FAILS this item, since A12a requires each rung asserted explicitly.
  - Observed evidence: 19 separately named tests, `19 passed`, each rung its own node and no composite case: rung 1 has five (`NO_COLOR`, `TERM=dumb`, non-TTY, `override=False`, process-wide override), rung 2 three, rung 3 four, rung 4 one. The `NO_COLOR`-plus-pinned-depth case is its OWN named node, `test_no_color_beats_a_pinned_depth`, passing separately, plus `test_no_color_beats_a_pinned_16_as_well`. Full `-v` output below.

    NINETEEN SEPARATELY NAMED TESTS, one per rung and per edge, with no composite case anywhere:

    ```text
    $ python3 -m pytest tests/test_term.py::ColorDepthPrecedenceTests \
        tests/test_term.py::ColorDepthConfigContractTests -o addopts="" -v -p no:randomly
    collecting ... collected 19 items

    tests/test_term.py::ColorDepthPrecedenceTests::test_an_invalid_pin_in_the_file_falls_through_instead_of_raising PASSED [  5%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_force_color_still_overrides_no_color_at_the_depth_resolver PASSED [ 10%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_no_color_beats_a_pinned_16_as_well PASSED [ 15%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_no_color_beats_a_pinned_depth PASSED [ 21%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_rung1_no_color_flag_override_yields_none PASSED [ 26%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_rung1_no_color_yields_none PASSED [ 31%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_rung1_non_tty_yields_none PASSED [ 36%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_rung1_process_wide_no_color_override_yields_none PASSED [ 42%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_rung1_term_dumb_yields_none PASSED [ 47%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_rung2_a_pinned_256_overrides_16_color_detection PASSED [ 52%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_rung2_a_pinned_depth_overrides_detection PASSED [ 57%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_rung2_a_pinned_none_overrides_a_capable_terminal PASSED [ 63%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_rung3_a_linux_console_resolves_16 PASSED [ 68%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_rung3_colorterm_truecolor_resolves_256_not_a_fourth_rung PASSED [ 73%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_rung3_detection_of_a_16_color_term_overrides_the_default PASSED [ 78%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_rung3_detection_of_a_256_color_term_resolves_256 PASSED [ 84%]
    tests/test_term.py::ColorDepthPrecedenceTests::test_rung4_the_default_is_256_not_the_conservative_rung PASSED [ 89%]
    tests/test_term.py::ColorDepthConfigContractTests::test_every_accepted_value_is_actually_honored_by_the_resolver PASSED [ 94%]
    tests/test_term.py::ColorDepthConfigContractTests::test_the_config_enum_matches_the_resolver_ladder_exactly PASSED [100%]

    ============================== 19 passed in 0.15s ==============================
    ```

    THE `NO_COLOR`-PLUS-PINNED-DEPTH CASE IS ITS OWN NAMED TEST, passing separately:
    `test_no_color_beats_a_pinned_depth` (plus `test_no_color_beats_a_pinned_16_as_well`, so the
    guard is not accidentally 256-specific). It asserts the pin is IN FORCE first and only then
    introduces `NO_COLOR`, so it cannot pass by the pin having silently failed to apply.

    THREE TESTS EARN THEIR PLACE BY EXCLUDING A PLAUSIBLE WRONG IMPLEMENTATION, which is why the
    count is higher than the four rungs. `test_rung2_a_pinned_256_overrides_16_color_detection`
    fails an implementation that takes the MINIMUM of pin and detection (which passes both
    downward-pinning tests). `test_rung4_the_default_is_256_not_the_conservative_rung` uses an
    UNRECOGNIZED `TERM`, the only state where the default is reachable, so an implementation that
    degraded unknown terminals to 16 "to be safe" fails here and nowhere else.
    `test_rung1_no_color_flag_override_yields_none` covers the one top-rung input that never
    appears in `os.environ`. A12c's config-side half is covered by `ColorDepthKeyTests` and
    `DeclarativeAllowedValuesTests` in `tests/test_config.py` (see V-03).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the same fixture rendered at 256, at 16, and at none, side by side. At every tier both the glyph and the native word must be visible. Paste the collapse assertions proving they are pinned.
  - Observed evidence: One 7-row fixture rendered at 256, at 16, and at none, side by side, with the glyph AND the native word present in every row at every tier; the `none` tier emits no escape and both colored tiers do (each asserted, so the invariant cannot pass trivially). Collapse assertions pinned in three places (import-time validator, per-collapse tests, and a deliberate-break test), and the collapses are shown non-lossy: each collapsed group shares one color but has six DISTINCT glyphs. Full render below.

    ONE FIXTURE, THREE TIERS, SIDE BY SIDE. The fixture deliberately includes BOTH members of all
    three required separations plus one member of each expected collapse, so it exercises the
    distinctions the tier must preserve rather than seven arbitrary rows. Escapes are shown literally
    (`\033` rendered as `ESC` would hide the very bytes under test):

    ```text
    stage            | 256 tier                     | 16 tier                    | none tier
    -----------------------------------------------------------------------------------------------
    ready            | [38;5;45m◕[0m approved     | [96m◕[0m approved        | ◕ approved
    done             | [38;5;46m✓[0m executed     | [92m✓[0m executed        | ✓ executed
    blocked          | [38;5;208m⚠︎[0m blocked    | [35m⚠︎[0m blocked        | ⚠︎ blocked
    failed           | [38;5;196m✘[0m failed      | [31m✘[0m failed          | ✘ failed
    waiting-input    | [38;5;214m…[0m needs_input | [93m…[0m needs_input     | … needs_input
    executing        | [38;5;220m▶[0m implementing | [33m▶[0m implementing    | ▶ implementing
    parked           | [38;5;244m◇[0m parked      | [90m◇[0m parked          | ◇ parked

    tier 256  : every row keeps glyph+word = True; escapes present = True
    tier 16   : every row keeps glyph+word = True; escapes present = True
    tier none : every row keeps glyph+word = True; escapes present = False
    ```

    AT EVERY TIER BOTH THE GLYPH AND THE NATIVE WORD ARE PRESENT (R9.3a.5 / A12d), and the `none`
    tier carries no escape at all while the two colored tiers do. That last pair of facts is
    asserted by two tests rather than read off this table, because if BOTH colored tiers had
    silently emitted plain text the invariant tests would pass trivially and prove nothing
    (`test_the_none_tier_emits_no_escape_at_all`, `test_the_two_colored_tiers_do_emit_escapes`).

    NO STATE IS DISTINGUISHABLE BY COLOR ALONE, asserted as the property that actually matters
    rather than by eye: `test_no_state_is_distinguishable_by_color_alone_at_any_tier` strips every
    escape and requires that any two rows carrying DIFFERENT stages still differ. If two rows became
    identical without color, color would be the sole carrier of that distinction, which R9.3a.5
    forbids.

    THE COLLAPSE ASSERTIONS THAT PIN THEM (A12b's "so a later change cannot quietly re-expand them"):

    ```text
    COLLAPSES (must be one color each):
      6 stages -> SGR {33}  (reviewing, executing, verifying, integrating, recovering, active)
      6 stages -> SGR {90}  (parked, superseded, abandoned, unknown, none, formative)
    ```

    Pinned in THREE independent places, so a re-expansion cannot slip through: the import-time
    `validate_16_color_palette` (a defect is a loud failure at first import, not a wrong color
    discovered later in a view), `test_the_active_subtypes_collapse_to_one_yellow` plus
    `test_the_six_gray_family_stages_collapse_to_one_neutral`, and
    `test_the_validator_rejects_a_split_collapse`, which proves the validator actually fires by
    breaking the table on purpose.

    AND THE COLLAPSES ARE SHOWN TO BE NON-LOSSY, which is what makes them acceptable rather than
    merely declared: `test_the_collapsed_stages_remain_separable_without_color` asserts that within
    each collapsed group the stages share one color AND have SIX DISTINCT GLYPHS, so the tier loses
    redundancy and never information.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved pow5sj --by-human`). Its `- Item-Dependencies: executed:yaxr4i, executed:udgilu` edges are re-checked at dispatch: `yaxr4i` because it settles the `--color`/`--no-color` flag surface this resolver's top rung reads, and `udgilu` because the 16-color table is authored against the stage vocabulary that child defines. Both edges are load-bearing here rather than nominal: verified at review, `--color` has NO flag form today (`grep -c '"--color"' agent_workflows/cli.py` -> 0) and `term.should_color` reads no flags at all, so `yaxr4i` E-03's flag-above-env layering is what makes this resolver's top rung implementable.

OPEN QUESTIONS: OQ-01 is non-blocking (an implementation route this plan's own E-03/V-03 record). OQ-02 is `- Blocking: yes` and UNRESOLVED, so `aw ipd lint` refuses this plan at every checkpoint until a maintainer rules on whether `FORCE_COLOR` still overrides `NO_COLOR` at the depth resolver. That refusal is intended: E-01's top rung, V-01's evidence, and the fate of a shipped test all depend on the answer, and guessing would either silently change documented behavior or silently contradict R9.3a.2.

SCOPE FENCE: the files this plan may write are those declared in `- Scope-Paths:` (`agent_workflows/term.py`, `agent_workflows/config.py`, `tests/test_term.py`, `tests/test_config.py`), plus the `uonrjg` spec ONLY IF a conditional amendment above applies AND that path has been added to the declaration first. An out-of-scope edit is permitted but must then be JUSTIFIED, which `aw ipd finalize` enforces by refusing to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. In particular this child must NOT convert any consumer and must NOT delete `term.py`'s `STATUS_COLOR_256`: that deletion is `qdd5jq`'s, after every consumer moves off it, and doing it here would break live views. DO STOP AND REPORT for one genuinely unsafe condition: if `udgilu` landed a stage table whose membership differs from Section 5's 20 rows, the authored 16-color table cannot be written against a known vocabulary; report that rather than inventing the difference away.

HONESTY RULE (hard MUST): when reporting tests or measurements, paste the ACTUAL command output. Never claim a suite run, a resolver dump, a config refusal message, or a three-tier render you did not run.

On completion: append the workflow-history line, set the terminal `Status: executed`, and move this plan to `.aw/records/plans/executed/` via `aw ipd finalize` as a post-gate lifecycle step, never as a checklist item and never as a hand-rolled `git mv`. When a runner owns the turn it performs that finalize itself; a hand-run executor invokes it directly. Commit path-scoped (`git commit -m msg -- <path>`); never `git add -A`; never push.
