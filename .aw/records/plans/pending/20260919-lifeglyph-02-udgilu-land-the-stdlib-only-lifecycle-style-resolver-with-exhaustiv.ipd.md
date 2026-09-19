# IPD: Land the stdlib-only lifecycle_style resolver with exhaustive owner-enum coverage tests

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` R10.1 requires ONE semantic source for lifecycle presentation, and it does not exist: `agent_workflows/lifecycle_style.py` is absent (verified 2026-09-19). Meanwhile four partial tables are live and disagree, which is the spec's Section 1 problem statement measured in code: `term.py:117 STATUS_COLOR_256`, `attention.py:1403 _STATUS_COLOR_256`, `render_stream.py:51 _STATUS_COLOR`, and the re-export chain `oc_runipd.py:104` / `agy_runipd.py:104` / `runner_shared.py:168` that spreads `render_stream`'s palette into both drivers. Nothing can be converted to a shared resolver until the resolver exists.
- Scope: IN: create `agent_workflows/lifecycle_style.py` containing the TWENTY semantic stages of Section 5 with their Unicode glyph, ASCII fallback, xterm-256 index and bold flag; the native mappings of Sections 6.1-6.7; the runner/ledger mappings of Sections 7.1-7.4; the precedence resolver of Section 8; and the self-validation of R10.1 that rejects duplicate keys and incomplete coverage. Plus the A2 enumeration tests that fail when an owner adds a status without a mapping. OUT: emitting any ANSI (R10.1 forbids it in this module), the depth ladder and 16-color tier (child `pow5sj`), the `Term` rendering helpers (child `bn026f`), and converting any consumer (children `f9t5hz` onward). ALSO OUT, and newly explicit at review: deciding what stage the uncovered `integration-deferred` status maps to, which is OQ-02's blocking question rather than this plan's to guess.
- Scope-Paths: agent_workflows/lifecycle_style.py, tests/test_lifecycle_style.py
- Item-Dependencies: executed:yaxr4i, executed:n4xq3l
- Status: reviewed
- Readiness: no-go
- Set: lifeglyph
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: udgilu
- From-Spec: uonrjg
- Blocks-Release: next

## Workflow history
- 2026-09-19 reviewed (aw set): plan-review round 1: REVIEWED - OPEN QUESTIONS. PR-201/202/204/205/206 FIXED; PR-203 (BLOCKER) escalated as OQ-02 Blocking: yes (integration-deferred has no spec Section 7.2 row, so criterion A2 is unsatisfiable). Readiness no-go.

- 2026-09-19 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-201, PR-202, PR-204, PR-205, PR-206 FIXED, PR-203 (BLOCKER) escalated as OQ-02 `Blocking: yes`. Reviewed at HEAD `07dabf1b`; `aw ipd lint --phase author --agent` clean, exit 0. A SIXTH ORPHAN STATUS makes criterion A2 unsatisfiable as authored: `runner_shutdown.KNOWN_ITEM_STATUSES` has 15 members and spec Section 7.2 covers 14, with `integration-deferred` appearing zero times in the spec and zero times in this Set. It was added by `integpath-03` AFTER the spec's review, so the spec's own five-orphan fix could not have caught it, and every way of proceeding without a ruling either guts the A2 test or writes an unreviewed presentation decision into the canonical module. THE STAGE COUNT WAS ALSO WRONG: Section 5 holds 20 stages, not 21 (the spec's own D13 rejects "a new 21st stage", which only parses at 20), and the wrong number had propagated to four places across three plans. OQ-01 is RESOLVED at review by importing all seven owner enums and diffing them against the spec: six mappings are already total, and the question's premise was false for prompts, which have no status enum at all.
- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from spec uonrjg R10.1/R10.4 and Section 12 step 1. Carries the spec's `Blocks-Release: next` gate and the Section 12a `executed:yaxr4i` edge.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Create the single stdlib-only module that resolves any artifact status, runner state, or ledger state to exactly one semantic presentation stage, with tests that fail when a new owner status lacks a mapping, so every later child has one authority to consume.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The stage vocabulary and its data

- [ ] E-01 Create `agent_workflows/lifecycle_style.py` defining the TWENTY semantic stages of spec Section 5 as an immutable table, each carrying its Unicode grapheme, ASCII fallback character, xterm-256 foreground index, and bold flag. Use the exact text-presentation forms: `⚠︎` is U+26A0 U+FE0E and `↩︎` is U+21A9 U+FE0E.
  - Depends on: none
  - Expected outcome: Importing the module yields a stage table whose values match spec Section 5 row for row, with exactly 20 rows. The module imports only from the standard library and emits no ANSI.
  - Execution state: pending

  THE COUNT IS 20, NOT 21, and this was CORRECTED AT REVIEW after being wrong in four places across three plans (see F-04). Parsed from the normative table on 2026-09-19, the stages in spec order are: `formative`, `review-queued`, `authority-queued`, `ready`, `reviewing`, `executing`, `verifying`, `integrating`, `recovering`, `active`, `waiting-input`, `blocked`, `failed`, `done`, `reusable`, `parked`, `superseded`, `abandoned`, `unknown`, `none`. The spec corroborates 20 independently and twice: D13 and the Section 7.2 commentary on `ran` both reject "a new 21st stage", which is only coherent if the existing table holds 20. Build the table from the spec rows rather than from any count asserted in prose, and let V-01's own assertion be the arbiter.

- [ ] E-02 Add the native artifact mappings of spec Sections 6.1 through 6.7, scoped by artifact family (plans, specs, backlog, research, prompts, releases, reviews/no-lifecycle), plus the `unknown` versus `none` distinction R10.4 requires.
  - Depends on: E-01
  - Expected outcome: Each family maps its own status set, and a known family with an unrecognized status resolves `unknown` while a family with no lifecycle resolves `none`. Neither silently becomes parked gray.
  - Execution state: pending

- [ ] E-03 Add the runner, ledger, and set-state mappings of spec Sections 7.1 through 7.4, INCLUDING the five rows the spec added at review that a naive reading would drop: `needs_input` and `awaiting-human` to `waiting-input`, `ran` to `recovering`, `unknown_outcome` to `failed`, and `quarantined` to `parked`. ALSO map `integration-deferred`, which spec Section 7.2 omits, per whatever OQ-02 resolves; do NOT guess it and do NOT leave it unmapped, because either choice breaks E-06 (see below).
  - Depends on: E-01
  - Expected outcome: All five formerly-orphan words resolve to their spec-assigned stage rather than falling through to `unknown`. `ran` resolves `recovering` and NOT `done`; `unknown_outcome` resolves `failed` and NOT `unknown`. `integration-deferred` resolves to the stage OQ-02 settles, with the spec amended in the same change so the module and the spec agree.
  - Execution state: pending

  THE SIXTH ORPHAN, measured at review and recorded here because it is the one input that can make E-06 unsatisfiable. `runner_shutdown.KNOWN_ITEM_STATUSES` holds 15 members, and Section 7.2 has a row for 14 of them. The missing one is `integration-deferred`, which appears ZERO times in the whole spec (`grep -c` on the spec file) and zero times across every plan in this Set. It is live and non-terminal: `runner_shared.INTEGRATION_DEFERRED_STATUS` defines it, `runner_shutdown.py:87` lists it under "in-flight / recoverable" with a comment stating it is deliberately NOT terminal, and `oc_runipd.py:6123` repeats that it is deliberately absent from `TERMINAL_STATES`. So it is exactly the same class of defect the spec's own 2026-09-13 review found five instances of, and it was missed because it was added by a later plan (`integpath-03`/`51vw4y`) than the review.

### Task group 2: The resolver and its self-validation

- [ ] E-04 Implement the Section 8 precedence resolver: integrity-failure, then named obstruction, then live activity, then native mapping, then `unknown`, then `none`. Return the native status and the activity SEPARATELY from the resolved stage, and mutate neither input.
  - Depends on: E-02, E-03
  - Expected outcome: A resolver that returns an immutable result carrying stage, native status, and activity as distinct fields. A failed integrity input wins over a stale active field; a blocked obstruction wins over a ready native status.
  - Execution state: pending

- [ ] E-05 Add the R10.1 self-validation that rejects duplicate stage keys and incomplete known-status coverage, raising at import or via an explicit validate call rather than degrading silently.
  - Depends on: E-04
  - Expected outcome: A duplicate key or a mapping table missing a known status is a hard error with a message naming the offending key, not a silent gray fallthrough.
  - Execution state: pending

- [ ] E-06 Add `tests/test_lifecycle_style.py` implementing criterion A2: enumerate the repository's OWNER enums and assert every member resolves to exactly one stage, so a later change that adds a status without a mapping FAILS. Use the NAMED owners measured at review (below), not a guess, and follow the SHIPPED PRECEDENT: `tests/test_attention_contract.py`'s `MappingTotalityTests` already does exactly this for the attention classes (`test_plans_total_over_RECOGNIZED` asserts `set(CLASS_MAPS["plans"].keys()) == set(plans.RECOGNIZED)`), including the lazy-import trick that keeps the contract module dependency-light. Mirror that structure rather than inventing one.
  - Depends on: E-05
  - Expected outcome: The test discovers statuses from the owners rather than from a hand-copied list, so it cannot drift. Adding a fake status to an owner enum makes the suite fail. Every owner named below has an assertion, and any owner deliberately NOT asserted is named in the test with the reason.
  - Execution state: pending

  THE OWNERS, resolved at review so OQ-01 no longer has to be answered at execution time (all verified by import on 2026-09-19): plans -> `plans.RECOGNIZED` (9 members); specs -> `attention_contract.SPEC_STATUSES` (9); research -> `research_contract.STATUSES` (4); backlog -> `backlog.STATUSES` (5); releases -> `releases.RELEASE_STATUSES` (3); runner item dispositions -> `runner_shutdown.KNOWN_ITEM_STATUSES` (15); set states -> `set_state.ALL_SET_STATES` (7). I checked each against the spec's tables: Sections 6.1, 6.2, 6.3, 6.4, 6.6 and 7.3 are ALREADY TOTAL over their owners (zero uncovered members), so those assertions will pass as soon as the tables are transcribed faithfully.
  TWO OWNERS NEED EXPLICIT HANDLING RATHER THAN AN ASSERTION. (a) `runner_shutdown.KNOWN_ITEM_STATUSES` is total over Section 7.2 EXCEPT `integration-deferred` (E-03), so this assertion FAILS until OQ-02 is resolved; that is correct behavior for a fail-closed test and must not be worked around by excluding the member. (b) PROMPTS HAVE NO ENUM: `agent_workflows/prompts.py` defines only `DEFAULT_STATUS = "pending"` and `PROMPT_KINDS`, and prompt status is carried by DIRECTORY (`pending`/`executed`/`reusable`/`superseded`/`not-executed`, the same five `ipd_lint._dir_of` anchors on at `ipd_lint.py:425`, matching the live `.aw/records/prompts/` subdirs). So assert against that directory-derived set and say in the test that it is directory-derived, because an agent looking for `prompts.STATUSES` will not find one and must not silently skip the family.

## Project conventions discovered (Step 0)

- Verified 2026-09-19: `agent_workflows/lifecycle_style.py` does not exist, so every E-item here is genuinely new work rather than a refactor.
- Verified 2026-09-19: four live lifecycle palettes exist at `term.py:117`, `attention.py:1403`, `render_stream.py:51`, and via re-export into both runners (`oc_runipd.py:104`, `agy_runipd.py:104`, `runner_shared.py:168`). This child does NOT delete them; `qdd5jq` does, after every consumer is converted, per spec Section 12 step 6.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `- Readiness:` is deliberately absent (it is `/plan-review`'s output; IPD-M107 refuses an unattested value).

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | The single semantic source the spec's whole architecture rests on does not exist, so this child is on the critical path for every other code child in the Set. | `ls agent_workflows/lifecycle_style.py` -> No such file or directory, verified 2026-09-19. |
| F-02 | High | Four independent lifecycle palettes are live today, confirming the spec's Section 1 problem statement is current rather than historical. | `term.py:117`, `attention.py:1403`, `render_stream.py:51`, plus re-exports at `oc_runipd.py:104`, `agy_runipd.py:104`, `runner_shared.py:168`. |
| F-03 | Medium | Three of the five review-added rows are judgement calls the spec argues at length, so an implementer working from Section 5 alone would plausibly get them wrong. `ran` to `recovering` (not `done`) and `unknown_outcome` to `failed` (not `unknown`) are the two most likely errors. | `uonrjg` Section 7.2 commentary and D13/D14; `ran` as `done` would paint an exit-1 item as success. |
| F-04 | High | A SIXTH ORPHAN STATUS exists that the spec's own review did not catch, and it makes criterion A2 unsatisfiable as written. `runner_shutdown.KNOWN_ITEM_STATUSES` has 15 members; Section 7.2 covers 14. `integration-deferred` appears ZERO times in the spec and zero times in any plan of this Set, so a faithful A2 assertion over that owner FAILS. It was missed because the plan that introduced it (`integpath-03`/`51vw4y`) landed after the spec's 2026-09-13 review. Carried as blocking OQ-02. | `runner_shutdown.py:87` (listed under "in-flight / recoverable", deliberately non-terminal); `runner_shared.INTEGRATION_DEFERRED_STATUS` at `runner_shared.py:2478`; `oc_runipd.py:6123`; `grep -c integration-deferred` on the spec -> 0. |
| F-05 | Medium | The stage count is 20, not 21, and the wrong number had propagated to four places across three plans of this Set (this plan's Scope and E-01, plus `7p3tt8` E-03 and E-04's "22nd stage"). Parsed from the normative Section 5 table on 2026-09-19: 20 rows. The spec corroborates independently, since D13 and the Section 7.2 `ran` commentary both reject "a new 21st stage", which only parses if 20 exist. Harm if uncorrected: E-01 and a legend drift-guard would each assert a count that cannot hold, so a correct implementation would fail its own validation. | Section 5 table parsed to 20 rows; `uonrjg` D13 and Section 7.2 commentary both say "a new 21st stage". |
| F-06 | Low | Section 6.5 maps prompt statuses, but prompts have NO status enum to enumerate: `prompts.py` defines only `DEFAULT_STATUS` and `PROMPT_KINDS`, and prompt status is carried by directory. An agent implementing A2 by grepping for an owner enum would find none and could silently drop a family the spec explicitly maps. | `agent_workflows/prompts.py:45,49`; the five directory anchors at `ipd_lint.py:425` matching the live `.aw/records/prompts/` subdirs. |

## Proposed changes (ordered, validatable)

1. Stage table with exact graphemes and text-presentation selectors, 20 rows (E-01).
2. Native artifact mappings plus the unknown/none distinction (E-02).
3. Runner, ledger, and set-state mappings including the five review-added rows AND `integration-deferred` per the OQ-02 ruling (E-03).
4. The precedence resolver returning stage, status, and activity separately (E-04).
5. Self-validation rejecting duplicates and incomplete coverage (E-05).
6. Owner-enum enumeration tests implementing A2 (E-06).

## Deferred / out of scope (with reason)

- ANSI emission: R10.1 explicitly forbids it in this module; rendering is `bn026f`'s.
  - Carrier: bn026f
- The depth ladder, the authored 16-color tier, and `aw config` pinning: child `pow5sj`, because they are a `term.py` concern and A12a-A12d are written against the rendering seam, not the semantic one.
  - Carrier: pow5sj
- Deleting the four duplicate tables: child `qdd5jq`, after all consumers convert, per Section 12 step 6. Deleting earlier would break live views.
  - Carrier: qdd5jq
- A display-width helper: spec Section 9.4 records that reusing `render_stream`'s proven ASCII-table-behind-a-capability-flag pattern satisfies the requirement WITHOUT a width helper, and calls that the cheaper route. No helper is built here.
  - Carrier-Declined: A conforming alternative is CHOSEN, not postponed. Section 9.4 is satisfied in full by the ASCII-table-behind-a-capability-flag route, which the spec itself calls the cheaper and already-proven option. Nothing is outstanding; a future consumer needing true width is bound by Section 9.4 to make it shared, which is that change's constraint rather than this plan's debt.

## Scope check

- Over-scope: none. Each E-item maps to a named R10.1 bullet or to criterion A2. Note the CONDITIONAL exception recorded in Spec / documentation sync: applying the OQ-02 ruling requires a one-row `uonrjg` Section 7.2 amendment, which is in scope only once that path is declared.
- Under-scope: ONE GAP, found at review and carried as blocking OQ-02. The plan's E-03 enumerated the five orphan statuses the spec's own review fixed but not the SIXTH one that appeared afterwards (`integration-deferred`, added by `integpath-03`/`51vw4y`), so E-06's A2 assertion over `runner_shutdown.KNOWN_ITEM_STATUSES` could not have passed as authored. Otherwise complete for the semantic layer: the rendering, depth, and conversion layers are deliberately separate children because they have independent test surfaces (capability matrix, config validation, per-consumer snapshots) and would each make this item unreviewable in one pass.

## Required tests / validation

Run the suite BARE: `python3 -m pytest`. Paste the actual summary line. The new `tests/test_lifecycle_style.py` must cover: every stage's glyph/ASCII/color/bold matching Section 5 (mechanically, not by eye) and the row count of 20; every owner enum member resolving (A2) across all eight families named in E-06; the five review-added rows plus `integration-deferred` resolving to their spec-assigned stage; the precedence order of Section 8; and the `unknown` versus `none` distinction (R10.4, criterion A20).

BASELINE, measured in this lane at HEAD `07dabf1b` on 2026-09-19 so an executor can distinguish a pre-existing failure from one it caused:

```text
8369 passed, 3 skipped, 2 xfailed in 100.98s (0:01:40)
```

Compare NODE IDS, not totals: this child ADDS tests, so the total is expected to rise, and only a NEW failing node id is a regression. Do NOT add `-n0`, a second `-q`, or `-p no:randomly` per AGENTS.md.

## Spec / documentation sync

No spec amendment in this child AS CURRENTLY SCOPED. `uonrjg` is implemented BY this Set rather than changed by it, and the one amendment the spec demands (`25kzda` Section 5.6) is carried by child `7p3tt8`. No `.spec.md` file is declared in `- Scope-Paths:` here, which is deliberate and correct while that holds: declaring one would make both runners announce a spec edit this child does not make.

ONE CONDITIONAL EXCEPTION, created by OQ-02 and recorded here because AGENTS.md requires a spec edit be DECLARED before it is made. If the maintainer rules that `integration-deferred` maps to a stage, spec `uonrjg` Section 7.2 MUST gain that row in the same change that adds it to `lifecycle_style.py`, so the module and the contract cannot drift. That amendment REQUIRES adding `.aw/records/specs/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md` to this plan's `- Scope-Paths:` BEFORE execution, since both runners announce declared spec edits before a run and the finalize scope gate reconciles what was actually changed against what was declared. DO NOT edit the spec without that declaration, and do not silently add the row to the module alone: a mapping present in code and absent from the spec is the exact drift this Set exists to end. The `- Scope-Paths:` line is deliberately left unchanged at review because the amendment is contingent on a ruling that has not happened; whoever applies the ruling updates it in the same edit.

## Open questions

### OQ-01: Which owner enums are the authoritative source for the A2 enumeration?

- Blocking: no
- Status: resolved
- Owner: none
- Carrier-Declined: RESOLVED AT REVIEW rather than deferred into execution, so nothing outlives this plan. The owner list is now written into E-06 with each module named and each member count verified by import, and V-06 still requires proof the resulting test can FAIL.
- Resolution or deferral rationale: RESOLVED AT REVIEW (2026-09-19) by importing each candidate owner and diffing it against the spec's tables, which is what the question asked for and is cheaper to do once here than to re-derive at execution. The seven owners and their member counts are recorded in E-06. THE ANSWER CHANGED THE PLAN in two ways a mere restatement would have missed. FIRST, six of the seven owner-to-spec mappings are already TOTAL (zero uncovered members), so most of A2 is transcription rather than discovery, and the one exception is a genuine spec gap now carried as OQ-02. SECOND, the question's premise that "each records tree has an owner module that defines its status vocabulary" is FALSE for prompts: `prompts.py` has no status enum at all, only `DEFAULT_STATUS` and `PROMPT_KINDS`, and prompt status is carried by directory. An agent resolving this at execution from the original wording would most likely have grepped for `prompts.STATUSES`, found nothing, and silently dropped a family that Section 6.5 explicitly maps, which is precisely the "test that passes while covering nothing" outcome the question was recorded to prevent.

### OQ-02: What semantic stage does `integration-deferred` map to, and who amends spec Section 7.2 to say so?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-203
- Resolution or deferral rationale: BLOCKING because it is UNANSWERABLE from the spec (the token appears zero times in it) and because leaving it unresolved makes criterion A2 and this plan's own E-06 unsatisfiable: `runner_shutdown.KNOWN_ITEM_STATUSES` contains `integration-deferred`, Section 7.2 has no row for it, so a faithful A2 assertion over that owner FAILS. The three ways to make it pass without a ruling are all wrong: excluding the member guts the test's purpose, guessing a stage writes an unreviewed presentation decision into the canonical module, and letting it fall through to `unknown` (`?`, gray 244) is exactly what the spec's Section 6 preamble calls a defect ("Falling through silently to gray for a known status is a defect").
  WHY A HUMAN RATHER THAN THE EXECUTOR: this is a PRESENTATION SEMANTICS decision on an `approved`, `Blocks-Release: next` spec, and the same question was already escalated to the maintainer five times in this spec's own review (D12 to D15 plus `quarantined`), each time producing a recorded ruling and rejected alternatives. It would be inconsistent for the sixth instance to be settled silently by an executing agent.
  WHAT THE EVIDENCE SAYS, so the maintainer can rule cheaply. `integration-deferred` means a verified lane whose integration was REFUSED on transient dirty-path overlap and which is awaiting a re-attempt. It is deliberately NOT terminal (`runner_shutdown.py:87` files it under "in-flight / recoverable"; `oc_runipd.py:6123` states it is deliberately absent from `TERMINAL_STATES`). The two defensible candidates are `recovering` (`↩︎`, 220), whose spec meaning is "Retry, correction, resume, or recovery is active or required" and which already receives the neighbouring `interrupted`/`partial`/`correction_required`/`ran` rows, and `blocked` (`⚠︎`, 208), on the reading that a named condition (the dirty path) must clear first. REVIEWER'S RECOMMENDATION is `recovering`, because the status is explicitly in-flight rather than obstructed, a re-attempt is genuinely pending, and `blocked`'s existing rows (`dependency-blocked`, `integration-blocked`, `merge-conflict`) are the ones that leave the child NOT integrated with no scheduled retry. But it is the maintainer's call, and it needs a Section 7.2 amendment in the same change, which makes it a spec edit this plan would have to declare in `- Scope-Paths:`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste a Python one-liner's output dumping each stage's glyph, ASCII char, color index, and bold flag, and diff it against spec Section 5's table by eye in the evidence block. Do NOT diff by eye alone: paste a MECHANICAL comparison that parses the spec's Section 5 table and asserts equality with the module's table, so a transcription slip in any of 20 rows times 4 fields fails rather than being read past. Paste the asserted row COUNT and show it is 20; a run asserting 21 fails this item (F-05). Additionally paste the code points of `⚠︎` and `↩︎` proving U+FE0E is present, and paste a grep proving the emoji forms `⚠️` and `↩️` appear NOWHERE in the module (criterion A5 requires their absence, which the code points alone do not prove). Paste `grep -nE "^(import|from) " agent_workflows/lifecycle_style.py` showing only standard-library imports, and a grep for `\033` or `\x1b` returning nothing, proving the R10.1 no-ANSI rule.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste resolver output for every native status in spec Sections 6.1-6.7, showing the resolved stage for each. Include one unrecognized status in a KNOWN family proving it yields `unknown`, and one no-lifecycle family proving it yields `none`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste resolver output for all five review-added words. `ran` MUST show `recovering`, `unknown_outcome` MUST show `failed`, `needs_input` and `awaiting-human` MUST show `waiting-input`, `quarantined` MUST show `parked`. A run showing `ran` as `done` or `unknown_outcome` as `unknown` FAILS this item. ALSO paste `integration-deferred`'s resolved stage together with the recorded OQ-02 ruling it implements and the `git diff` of the spec's Section 7.2 row added in the same change. A run in which `integration-deferred` resolves to `unknown`, or resolves to a stage with no ruling and no spec row, FAILS this item: the first is the gray fallthrough Section 6 calls a defect, and the second is an unreviewed presentation decision written into the canonical module.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste test output for the Section 8 precedence cases: a failed-integrity input beating a stale active field (criterion A8), a blocked obstruction beating a ready native status (A9), and a live activity beating a native mapping (A7). Also paste evidence the resolver returned native status and activity as separate fields and mutated neither input.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the raised error (message included) from a deliberately duplicated stage key, and from a mapping table with a known status removed. Silent success on either FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste the BARE `python3 -m pytest` summary line and compare it against the baseline below. Then paste proof the A2 test actually bites: add a bogus status to an owner enum in a scratch fixture, show the suite FAILING, then remove it and show it passing. A test that cannot fail is not evidence. ALSO paste, for EACH of the seven owners named in E-06, the assertion and its result, so a silently absent family is visible: plans, specs, research, backlog, releases, runner item dispositions, and set states. Paste the prompts assertion too, with its directory-derived source stated (F-06), since there is no `prompts.STATUSES` to enumerate. A V-06 that reports a green suite while covering six of eight families FAILS this item, which is the specific failure mode OQ-01 was recorded against.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved udgilu --by-human`). Its `- Item-Dependencies: executed:yaxr4i, executed:n4xq3l` edges are re-checked at dispatch: `yaxr4i` because spec Section 12a makes it upstream, and `n4xq3l` because the same section forbids building the resolver before the re-review round is recorded.

OPEN QUESTIONS: OQ-01 is RESOLVED (the owner list is written into E-06). OQ-02 is `- Blocking: yes` and UNRESOLVED, so `aw ipd lint` refuses this plan at every checkpoint until a maintainer rules on `integration-deferred`. That refusal is intended: E-03, E-06 and V-03 all depend on the answer, and the three ways to proceed without it each corrupt the canonical module or gut the A2 test. If the ruling adds a Section 7.2 row, ALSO add the `uonrjg` spec path to `- Scope-Paths:` in the same edit, per Spec / documentation sync above.

SCOPE FENCE: the files this plan may write are those declared in `- Scope-Paths:` (`agent_workflows/lifecycle_style.py`, `tests/test_lifecycle_style.py`), plus the `uonrjg` spec ONLY IF the OQ-02 ruling is applied AND that path has been added to the declaration first. An out-of-scope edit is permitted but must then be JUSTIFIED, which `aw ipd finalize` enforces by refusing to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. In particular this child must NOT touch `term.py`, `attention.py`, `render_stream.py`, either runner, or any consumer: it creates the semantic source and converts nothing, and deleting any existing palette here would break live views (that is `qdd5jq`'s work, after every consumer converts). DO STOP AND REPORT for one genuinely unsafe condition: if an owner enum named in E-06 has moved or been renamed so its symbol is absent, report that rather than substituting a hand-copied status list, which is exactly the drift criterion A2 exists to catch.

HONESTY RULE (hard MUST): when reporting tests or measurements, paste the ACTUAL command output. Never claim a suite run, a resolver dump, or an owner-enum assertion you did not run. A V-item's evidence block must contain real output, not a description of expected output.

On completion: append the workflow-history line, set the terminal `Status: executed`, and move this plan to `.aw/records/plans/executed/` via `aw ipd finalize` as a post-gate lifecycle step, never as a checklist item and never as a hand-rolled `git mv`. When a runner owns the turn it performs that finalize itself; a hand-run executor invokes it directly. Commit path-scoped (`git commit -m msg -- <path>`); never `git add -A`; never push.
