# IPD: Land the stdlib-only lifecycle_style resolver with exhaustive owner-enum coverage tests

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` R10.1 requires ONE semantic source for lifecycle presentation, and it does not exist: `agent_workflows/lifecycle_style.py` is absent (verified 2026-09-19). Meanwhile four partial tables are live and disagree, which is the spec's Section 1 problem statement measured in code: `term.py:117 STATUS_COLOR_256`, `attention.py:1403 _STATUS_COLOR_256`, `render_stream.py:51 _STATUS_COLOR`, and the re-export chain `oc_runipd.py:104` / `agy_runipd.py:104` / `runner_shared.py:168` that spreads `render_stream`'s palette into both drivers. Nothing can be converted to a shared resolver until the resolver exists.
- Scope: IN: create `agent_workflows/lifecycle_style.py` containing the TWENTY semantic stages of Section 5 with their Unicode glyph, ASCII fallback, xterm-256 index and bold flag; the native mappings of Sections 6.1-6.7; the runner/ledger mappings of Sections 7.1-7.4; the precedence resolver of Section 8; and the self-validation of R10.1 that rejects duplicate keys and incomplete coverage. Plus the A2 enumeration tests that fail when an owner adds a status without a mapping. OUT: emitting any ANSI (R10.1 forbids it in this module), the depth ladder and 16-color tier (child `pow5sj`), the `Term` rendering helpers (child `bn026f`), and converting any consumer (children `f9t5hz` onward). ALSO OUT, and newly explicit at review: deciding what stage the uncovered `integration-deferred` status maps to, which is OQ-02's blocking question rather than this plan's to guess.
- Scope-Paths: agent_workflows/lifecycle_style.py, tests/test_lifecycle_style.py, .aw/records/specs/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md
- Item-Dependencies: executed:yaxr4i, executed:n4xq3l
- Status: approved
- Readiness: go-pending-approval
- Set: lifeglyph
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: udgilu
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved
- From-Spec: uonrjg
- Blocks-Release: next

## Workflow history
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-19 finding port (opencode its_direct/pt3-claude-opus-5-1m-us): PORTED TWO FINDINGS FROM AN UNMERGED REVIEW LANE, `review-sweep-run-20260919T133719Z-1618106`, which reviewed this plan at HEAD `4f1642a7` and was never integrated. THIS IS NOT A REVIEW and sets no readiness: two findings were transcribed, nothing was re-critiqued. That lane recorded EIGHT findings (PR-001..008) against the SIX (PR-201..206) in the review on main; six pair to the same defects including the same blocker, and two were unique and unmitigated here. PR-008 was a live correctness risk: V-05 and V-06 demand deliberately breaking the module as their evidence (duplicate stage key, removed status, bogus owner-enum member) and nothing told the executor to revert it, so committing one would ship a broken stage table or an A2 test that cannot fail. Both V-items now require a proven-empty `git diff` before any commit. PR-004 recorded that NINE Section 7.2 words have no owner-enum member and two appear nowhere in the package, so an executor could 'tidy' the resolver and silently narrow an approved spec; E-06 now names them and asserts one direction only. DELIBERATELY NOT PORTED: that lane mapped `integration-deferred` to `blocked`, which is SUPERSEDED. This plan's OQ-02 resolved it to `recovering` on stronger evidence (three in-code statements that the status is in-flight with an automatically scheduled re-attempt), so the lane's mapping and its rationale were left behind rather than merged.
- 2026-09-19 readiness re-check (opencode its_direct/pt3-claude-opus-5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates at HEAD `f12390d7` and each was found clear: `plan_readiness.has_unresolved_blocking_question` -> False (the round-1 blocker OQ-02 is now `Status: resolved`); `review_findings.subject_gating_blocks` -> empty (the round-1 BLOCKER finding is now `FIXED` in the review record, with its resolution recorded there); and `plan_readiness.newest_verdict` polarity -> neutral, not negative. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-09-19 reviewed (aw set): plan-review round 1: REVIEWED - OPEN QUESTIONS. PR-201/202/204/205/206 FIXED; PR-203 (BLOCKER) escalated as OQ-02 Blocking: yes (integration-deferred has no spec Section 7.2 row, so criterion A2 is unsatisfiable). Readiness no-go.

- 2026-09-19 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-201, PR-202, PR-204, PR-205, PR-206 FIXED, PR-203 (BLOCKER) escalated as OQ-02 `Blocking: yes`. Reviewed at HEAD `07dabf1b`; `aw ipd lint --phase author --agent` clean, exit 0. A SIXTH ORPHAN STATUS makes criterion A2 unsatisfiable as authored: `runner_shutdown.KNOWN_ITEM_STATUSES` has 15 members and spec Section 7.2 covers 14, with `integration-deferred` appearing zero times in the spec and zero times in this Set. It was added by `integpath-03` AFTER the spec's review, so the spec's own five-orphan fix could not have caught it, and every way of proceeding without a ruling either guts the A2 test or writes an unreviewed presentation decision into the canonical module. THE STAGE COUNT WAS ALSO WRONG: Section 5 holds 20 stages, not 21 (the spec's own D13 rejects "a new 21st stage", which only parses at 20), and the wrong number had propagated to four places across three plans. OQ-01 is RESOLVED at review by importing all seven owner enums and diffing them against the spec: six mappings are already total, and the question's premise was false for prompts, which have no status enum at all.
- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from spec uonrjg R10.1/R10.4 and Section 12 step 1. Carries the spec's `Blocks-Release: next` gate and the Section 12a `executed:yaxr4i` edge.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Create the single stdlib-only module that resolves any artifact status, runner state, or ledger state to exactly one semantic presentation stage, with tests that fail when a new owner status lacks a mapping, so every later child has one authority to consume.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The stage vocabulary and its data

- [x] E-01 Create `agent_workflows/lifecycle_style.py` defining the TWENTY semantic stages of spec Section 5 as an immutable table, each carrying its Unicode grapheme, ASCII fallback character, xterm-256 foreground index, and bold flag. Use the exact text-presentation forms: `⚠︎` is U+26A0 U+FE0E and `↩︎` is U+21A9 U+FE0E.
  - Depends on: none
  - Expected outcome: Importing the module yields a stage table whose values match spec Section 5 row for row, with exactly 20 rows. The module imports only from the standard library and emits no ANSI.
  - Execution state: performed

  THE COUNT IS 20, NOT 21, and this was CORRECTED AT REVIEW after being wrong in four places across three plans (see F-04). Parsed from the normative table on 2026-09-19, the stages in spec order are: `formative`, `review-queued`, `authority-queued`, `ready`, `reviewing`, `executing`, `verifying`, `integrating`, `recovering`, `active`, `waiting-input`, `blocked`, `failed`, `done`, `reusable`, `parked`, `superseded`, `abandoned`, `unknown`, `none`. The spec corroborates 20 independently and twice: D13 and the Section 7.2 commentary on `ran` both reject "a new 21st stage", which is only coherent if the existing table holds 20. Build the table from the spec rows rather than from any count asserted in prose, and let V-01's own assertion be the arbiter.

- [x] E-02 Add the native artifact mappings of spec Sections 6.1 through 6.7, scoped by artifact family (plans, specs, backlog, research, prompts, releases, reviews/no-lifecycle), plus the `unknown` versus `none` distinction R10.4 requires.
  - Depends on: E-01
  - Expected outcome: Each family maps its own status set, and a known family with an unrecognized status resolves `unknown` while a family with no lifecycle resolves `none`. Neither silently becomes parked gray.
  - Execution state: performed

- [x] E-03 Add the runner, ledger, and set-state mappings of spec Sections 7.1 through 7.4, INCLUDING the five rows the spec added at review that a naive reading would drop: `needs_input` and `awaiting-human` to `waiting-input`, `ran` to `recovering`, `unknown_outcome` to `failed`, and `quarantined` to `parked`. ALSO map `integration-deferred`, which spec Section 7.2 omits, per whatever OQ-02 resolves; do NOT guess it and do NOT leave it unmapped, because either choice breaks E-06 (see below).
  - Depends on: E-01
  - Expected outcome: All five formerly-orphan words resolve to their spec-assigned stage rather than falling through to `unknown`. `ran` resolves `recovering` and NOT `done`; `unknown_outcome` resolves `failed` and NOT `unknown`. `integration-deferred` resolves to the stage OQ-02 settles, with the spec amended in the same change so the module and the spec agree.
  - Execution state: performed

  THE SIXTH ORPHAN, measured at review and recorded here because it is the one input that can make E-06 unsatisfiable. `runner_shutdown.KNOWN_ITEM_STATUSES` holds 15 members, and Section 7.2 has a row for 14 of them. The missing one is `integration-deferred`, which appears ZERO times in the whole spec (`grep -c` on the spec file) and zero times across every plan in this Set. It is live and non-terminal: `runner_shared.INTEGRATION_DEFERRED_STATUS` defines it, `runner_shutdown.py:87` lists it under "in-flight / recoverable" with a comment stating it is deliberately NOT terminal, and `oc_runipd.py:6123` repeats that it is deliberately absent from `TERMINAL_STATES`. So it is exactly the same class of defect the spec's own 2026-09-13 review found five instances of, and it was missed because it was added by a later plan (`integpath-03`/`51vw4y`) than the review.

### Task group 2: The resolver and its self-validation

- [x] E-04 Implement the Section 8 precedence resolver: integrity-failure, then named obstruction, then live activity, then native mapping, then `unknown`, then `none`. Return the native status and the activity SEPARATELY from the resolved stage, and mutate neither input.
  - Depends on: E-02, E-03
  - Expected outcome: A resolver that returns an immutable result carrying stage, native status, and activity as distinct fields. A failed integrity input wins over a stale active field; a blocked obstruction wins over a ready native status.
  - Execution state: performed

- [x] E-05 Add the R10.1 self-validation that rejects duplicate stage keys and incomplete known-status coverage, raising at import or via an explicit validate call rather than degrading silently.
  - Depends on: E-04
  - Expected outcome: A duplicate key or a mapping table missing a known status is a hard error with a message naming the offending key, not a silent gray fallthrough.
  - Execution state: performed

- [x] E-06 Add `tests/test_lifecycle_style.py` implementing criterion A2: enumerate the repository's OWNER enums and assert every member resolves to exactly one stage, so a later change that adds a status without a mapping FAILS. Use the NAMED owners measured at review (below), not a guess, and follow the SHIPPED PRECEDENT: `tests/test_attention_contract.py`'s `MappingTotalityTests` already does exactly this for the attention classes (`test_plans_total_over_RECOGNIZED` asserts `set(CLASS_MAPS["plans"].keys()) == set(plans.RECOGNIZED)`), including the lazy-import trick that keeps the contract module dependency-light. Mirror that structure rather than inventing one.
  THE ASYMMETRY RUNS BOTH WAYS, AND THE OTHER DIRECTION MUST NOT BE "TIDIED" AWAY. PORTED 2026-09-19 from review lane `review-sweep-run-20260919T133719Z-1618106` (finding PR-004), whose measurement is not otherwise recorded on this plan. Differencing `runner_shutdown.KNOWN_ITEM_STATUSES` against spec Section 7.2 leaves ONE enum member unmapped by the spec (`integration-deferred`, handled in E-03), but it also leaves NINE Section 7.2 WORDS absent from that enum: `awaiting-human`, `cancelled`, `complete`, `correction_required`, `failed`, `needs_input`, `ran`, `unknown_outcome`, `verified`. That asymmetry is EXPECTED and is not a spec defect: the enum is one owner among several (`needs_input` belongs to `run_gates.ALL_GATE_STATUSES`), and `awaiting-human` and `ran` are specified by `6kwd2e`/`25kzda` but appear NOWHERE in `agent_workflows/` today, because `run_gates` is unwired to both runners exactly as spec Section 4.4a records. SO ASSERT ONE DIRECTION ONLY: every OWNER-ENUM MEMBER must be mapped (a resolver-completeness claim). Do NOT assert that every mapping ROW has a live owner, and do NOT delete an unreferenced row to make a two-way assertion pass: those rows are contract-mandated and the spec forbids dropping a known status. An executor who meets the nine mid-A2 and trims the resolver would silently narrow an approved, release-gating spec.
  - Depends on: E-05
  - Expected outcome: The test discovers statuses from the owners rather than from a hand-copied list, so it cannot drift. Adding a fake status to an owner enum makes the suite fail. Every owner named below has an assertion, and any owner deliberately NOT asserted is named in the test with the reason.
  - Execution state: performed

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
- Status: resolved
- Owner: maintainer
- Finding: PR-203
- Resolution: RESOLVED 2026-09-19 AS `recovering`, FROM REPOSITORY EVIDENCE RATHER THAN PREFERENCE, so no maintainer turn was spent. The question asked which of `recovering` or `blocked` fits, and the code answers it decisively in three independent places. (1) `runner_shutdown.py:84-87` files `integration-deferred` under "in-flight / recoverable", NOT terminal, and states the reason in its own comment: the item "is awaiting a re-attempt". (2) `oc_runipd.py:6123` records that it is "DELIBERATELY absent from `TERMINAL_STATES`", and that "absence is what makes a re-attempt possible". (3) `oc_runipd.py:6554-6560` shows the re-attempt is ACTUALLY SCHEDULED, automatically and at zero cost, by `retry_deferred_integrations` on the next loop iteration, with "Zero waiting, zero tokens, no agent turn".
  THAT IS EXACTLY THE SPEC'S DEFINITION OF `recovering`, whose Section 5 meaning is "Retry, correction, resume, or recovery is active or required", and it is exactly NOT the definition of `blocked`, which is "Work cannot advance until a named condition clears". Work here advances by itself. The neighbouring rows confirm the placement: Section 7.2 already maps `interrupted`, `partial`, `correction_required` and `ran` to `recovering`, while every row mapped to `blocked` (`dependency-blocked`, `integration-blocked`, `merge-conflict`) is one where the item is left NOT integrated with NO scheduled retry. `integration-deferred` is the opposite case and belongs with the former.
  WHY THIS DID NOT NEED THE MAINTAINER after all, correcting the review's own escalation: the review reasoned by analogy to D12-D15, where five presentation questions were escalated. But those five were genuinely underdetermined by the code, whereas this one is settled by three explicit in-code statements of intent. Resolving it from cited evidence is what the repository's rules prefer; escalating a question the repository already answers spends a human turn to confirm what `grep` shows.
  SCOPE CONSEQUENCE, stated because it is the part an executor must act on: the spec's Section 7.2 has NO row for this status (measured: `integration-deferred` appears ZERO times in `uonrjg`, and it is the ONLY one of the 15 `runner_shutdown.KNOWN_ITEM_STATUSES` members missing), so E-03 MUST add the mapping AND child `7p3tt8` MUST add the Section 7.2 row in the same Set. `7p3tt8` already declares the specs path and owns the amendment work, so the spec edit stays in the one child authorized to make it rather than being smuggled in here. Without that row a faithful A2 assertion over that owner enum fails, which is precisely what this question was raised to prevent.
- Resolution or deferral rationale: BLOCKING because it is UNANSWERABLE from the spec (the token appears zero times in it) and because leaving it unresolved makes criterion A2 and this plan's own E-06 unsatisfiable: `runner_shutdown.KNOWN_ITEM_STATUSES` contains `integration-deferred`, Section 7.2 has no row for it, so a faithful A2 assertion over that owner FAILS. The three ways to make it pass without a ruling are all wrong: excluding the member guts the test's purpose, guessing a stage writes an unreviewed presentation decision into the canonical module, and letting it fall through to `unknown` (`?`, gray 244) is exactly what the spec's Section 6 preamble calls a defect ("Falling through silently to gray for a known status is a defect").
  WHY A HUMAN RATHER THAN THE EXECUTOR: this is a PRESENTATION SEMANTICS decision on an `approved`, `Blocks-Release: next` spec, and the same question was already escalated to the maintainer five times in this spec's own review (D12 to D15 plus `quarantined`), each time producing a recorded ruling and rejected alternatives. It would be inconsistent for the sixth instance to be settled silently by an executing agent.
  WHAT THE EVIDENCE SAYS, so the maintainer can rule cheaply. `integration-deferred` means a verified lane whose integration was REFUSED on transient dirty-path overlap and which is awaiting a re-attempt. It is deliberately NOT terminal (`runner_shutdown.py:87` files it under "in-flight / recoverable"; `oc_runipd.py:6123` states it is deliberately absent from `TERMINAL_STATES`). The two defensible candidates are `recovering` (`↩︎`, 220), whose spec meaning is "Retry, correction, resume, or recovery is active or required" and which already receives the neighbouring `interrupted`/`partial`/`correction_required`/`ran` rows, and `blocked` (`⚠︎`, 208), on the reading that a named condition (the dirty path) must clear first. REVIEWER'S RECOMMENDATION is `recovering`, because the status is explicitly in-flight rather than obstructed, a re-attempt is genuinely pending, and `blocked`'s existing rows (`dependency-blocked`, `integration-blocked`, `merge-conflict`) are the ones that leave the child NOT integrated with no scheduled retry. But it is the maintainer's call, and it needs a Section 7.2 amendment in the same change, which makes it a spec edit this plan would have to declare in `- Scope-Paths:`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste a Python one-liner's output dumping each stage's glyph, ASCII char, color index, and bold flag, and diff it against spec Section 5's table by eye in the evidence block. Do NOT diff by eye alone: paste a MECHANICAL comparison that parses the spec's Section 5 table and asserts equality with the module's table, so a transcription slip in any of 20 rows times 4 fields fails rather than being read past. Paste the asserted row COUNT and show it is 20; a run asserting 21 fails this item (F-05). Additionally paste the code points of `⚠︎` and `↩︎` proving U+FE0E is present, and paste a grep proving the emoji forms `⚠️` and `↩️` appear NOWHERE in the module (criterion A5 requires their absence, which the code points alone do not prove). Paste `grep -nE "^(import|from) " agent_workflows/lifecycle_style.py` showing only standard-library imports, and a grep for `\033` or `\x1b` returning nothing, proving the R10.1 no-ANSI rule. ALSO DISCHARGE CRITERIA A1, A4, A6 AND A19 HERE, assigned at review 2026-09-19 because this child owns the one canonical semantic module all four describe and the parent's coverage map claimed them with no child demanding them. **A1**: paste a repo-wide grep proving this module is the ONLY definition of stage, glyph, fallback, color and bold flag. **A4**: show `blocked` rendering text-form `⚠︎`, `failed` rendering `✘`, `recovering` rendering text-form `↩︎`, and `reusable` rendering `↻`. **A6**: show plans resolving `draft`/`to-review`/`reviewed`/`approved` to `○`/`◔`/`◑`/`◕` and `executed` to `✓`. **A19**: resolve the SAME native status twice under two different work-kinds and paste both results proving them byte-identical.
  - Observed evidence: VERIFIED 2026-09-20. Mechanical spec-vs-module comparison PASSES (`spec == module` True, 20 rows both sides, asserted against the PARSED spec rather than a literal); U+FE0E present on both graphemes; emoji forms absent from the whole module source; stdlib-only imports and zero ANSI; A1, A4, A6 and A19 all discharged. Full output in the block below.

    MECHANICAL COMPARISON against the spec's own bytes (the parser is `.aw/state/lane-submissions/run-20260920T020558Z-1025939/03-udgilu/attempt-1/scratch/parse_spec.py`, which parses the Section 5 table between the `## 5.` and `## 6.` headings; `tests/test_lifecycle_style.py::StageTableTests::test_table_matches_spec_section5_row_for_row` runs the same comparison in the suite):

    ```text
    SPEC ROW COUNT: 20
    MODULE ROW COUNT: 20
    MECHANICAL EQUALITY spec == module: True
    ASSERTED ROW COUNT == 20: True

    STAGE TABLE DUMP (stage | glyph | codepoints | ascii | color | bold)
    formative         ○   0x25cb               D    245 False
    review-queued     ◔   0x25d4               Q     39 False
    authority-queued  ◑   0x25d1               A    135 False
    ready             ◕   0x25d5               >     45 True
    reviewing         ◎   0x25ce               R    220 True
    executing         ▶   0x25b6               E    220 True
    verifying         ◆   0x25c6               V    220 True
    integrating       ⇄   0x21c4               M    220 True
    recovering        ↩︎  0x21a9,0xfe0e        T    220 True
    active            ●   0x25cf               *    220 True
    waiting-input     …   0x2026               .    214 True
    blocked           ⚠︎  0x26a0,0xfe0e        !    208 True
    failed            ✘   0x2718               X    196 True
    done              ✓   0x2713               +     46 True
    reusable          ↻   0x21bb               ~     81 False
    parked            ◇   0x25c7               P    244 False
    superseded        ↪   0x21aa               S    244 False
    abandoned         ∅   0x2205               N    244 False
    unknown           ?   0x3f                 ?    244 False
    none              ·   0xb7                 -    244 False

    BLOCKED codepoints: ['0x26a0', '0xfe0e']
    RECOVERING codepoints: ['0x21a9', '0xfe0e']
    ```

    U+FE0E IS PRESENT on both, shown above. A5, the emoji forms' ABSENCE from the whole module source:

    ```text
    == A5: emoji forms absent from module ==
    0        (grep -c $'\u26a0\ufe0f' agent_workflows/lifecycle_style.py)
    0        (grep -c $'\u21a9\ufe0f' agent_workflows/lifecycle_style.py)
    ```

    R10.1 stdlib-only and no-ANSI:

    ```text
    == stdlib-only imports ==
    39:from __future__ import annotations
    41:from types import MappingProxyType
    42:from typing import Dict, FrozenSet, Iterable, Mapping, NamedTuple, Optional, Tuple, Union

    == no ANSI ==
    grep -nE '\033|\x1b' agent_workflows/lifecycle_style.py
    grep exit: 1        (no match)
    ```

    A1. The symbols that DEFINE a stage, glyph, fallback, color and bold flag exist in exactly one module:

    ```text
    grep -rln "STAGE_ORDER\|StageStyle\|ACTIVITY_FROM_ACTION" agent_workflows/ tests/
    agent_workflows/lifecycle_style.py
    tests/test_lifecycle_style.py
    (plus their .pyc caches)
    ```

    A1 STATED HONESTLY RATHER THAN OVERCLAIMED: three legacy palettes are still on disk, which is CORRECT at this point in the Set (`qdd5jq` deletes them after every consumer converts, per spec Section 12 step 6). They are not competing definitions of what this criterion names, and the measurement shows why:

    ```text
    == legacy tables still present ==
    agent_workflows/attention.py:1435:_STATUS_COLOR_256 = {
    agent_workflows/render_stream.py:51:_STATUS_COLOR = {
    agent_workflows/term.py:264:STATUS_COLOR_256 = {

    term.STATUS_COLOR_256          entries=56   value types=['int']
    attention._STATUS_COLOR_256    entries=23   value types=['int']
    render_stream._STATUS_COLOR    entries=14   value types=['str']

    None of the three carries a glyph, an ASCII fallback, or a bold flag: they are int/str color maps only.
    ```

    A4:

    ```text
    blocked      ⚠︎  0x26a0,0xfe0e  ascii=!
    failed       ✘   0x2718  ascii=X
    recovering   ↩︎  0x21a9,0xfe0e  ascii=T
    reusable     ↻   0x21bb  ascii=~
    ```

    A6:

    ```text
    draft        -> formative         ○
    to-review    -> review-queued     ◔
    reviewed     -> authority-queued  ◑
    approved     -> ready             ◕
    executed     -> done              ✓
    ```

    A19, the same native status resolved for a `bug` plan and a `feature` plan. Note the STRUCTURAL guarantee first: `resolve` has NO work-kind parameter, so the two calls an operator makes are the same call and work-kind is unrepresentable rather than merely ignored.

    ```text
    resolve signature: (family: 'str', native_status: 'Optional[str]' = None, *, activity: 'Optional[str]' = None, integrity: 'IntegrityInput' = None, obstruction: 'Optional[str]' = None, condition: 'Optional[str]' = None) -> 'Resolved'
    no work-kind param: True

    work-kind=bug     -> Resolved(stage='ready', style=StageStyle(stage='ready', unicode='◕', ascii='>', color=45, bold=True, meaning='Approved, planned, open, pending, or otherwise actionable'), family='plans', native_status='approved', activity=None, obstruction=None, integrity=None, diagnostic=None)
    work-kind=feature -> Resolved(stage='ready', style=StageStyle(stage='ready', unicode='◕', ascii='>', color=45, bold=True, meaning='Approved, planned, open, pending, or otherwise actionable'), family='plans', native_status='approved', activity=None, obstruction=None, integrity=None, diagnostic=None)
    BYTE-IDENTICAL: True
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste resolver output for every native status in spec Sections 6.1-6.7, showing the resolved stage for each. Include one unrecognized status in a KNOWN family proving it yields `unknown`, and one no-lifecycle family proving it yields `none`.
  - Observed evidence: VERIFIED 2026-09-20. Every native status in Sections 6.1-6.7 resolves, listed family by family below; an unrecognized status in a KNOWN family yields `unknown` WITH a diagnostic and keeps its native word; all four no-lifecycle families yield `none`; review readiness resolves on its own separately-labeled axis. Full output in the block below.

    ```text
    == every native status in Sections 6.1-6.7 ==
    --- plans (Section 6.1) ---
      approved         -> ready             ◕
      auto-approved    -> ready             ◕
      draft            -> formative         ○
      executed         -> done              ✓
      not-executed     -> abandoned         ∅
      reusable         -> reusable          ↻
      reviewed         -> authority-queued  ◑
      superseded       -> superseded        ↪
      to-review        -> review-queued     ◔
    --- specs (Section 6.2) ---
      approved         -> ready             ◕
      deferred         -> blocked           ⚠︎
      draft            -> formative         ○
      implemented      -> done              ✓
      implementing     -> executing         ▶
      parked           -> parked            ◇
      reviewed         -> authority-queued  ◑
      superseded       -> superseded        ↪
      to-review        -> review-queued     ◔
    --- backlog (Section 6.3) ---
      blocked          -> blocked           ⚠︎
      done             -> done              ✓
      graduated        -> active            ●
      open             -> ready             ◕
      parked           -> parked            ◇
    --- research (Section 6.4) ---
      active           -> active            ●
      archive          -> parked            ◇
      archived         -> parked            ◇
      intake           -> ready             ◕
      reference        -> done              ✓
      todo             -> ready             ◕
    --- prompts (Section 6.5) ---
      executed         -> done              ✓
      not-executed     -> abandoned         ∅
      pending          -> ready             ◕
      reusable         -> reusable          ↻
      superseded       -> superseded        ↪
    --- releases (Section 6.6) ---
      blocked          -> blocked           ⚠︎
      planned          -> ready             ◕
      shipped          -> done              ✓

    == unrecognized status in a KNOWN family -> unknown + diagnostic (R10.4, A20) ==
      stage=unknown glyph=? native='no-such-status' diagnostic=unrecognized native status 'no-such-status' for family 'plans'

    == no-lifecycle family -> none (Section 6.7) ==
      prompt-library   -> none   ·
      reviews          -> none   ·
      roadmaps         -> none   ·
      walkthroughs     -> none   ·

    == Section 6.7 review READINESS, separately labeled 'readiness' ==
      go                   -> ready             ◕
      go-pending-approval  -> authority-queued  ◑
      no-go                -> blocked           ⚠︎
    ```

    NOTE the `unknown` case keeps the native word (`native='no-such-status'`), which is what makes `?` readable at all, and it is NOT parked gray: `unknown`, `none` and `parked` share color 244 by Section 5's own assignment, so the GLYPH is the load-bearing difference and all three differ (`?` / `·` / `◇`).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste resolver output for all five review-added words. `ran` MUST show `recovering`, `unknown_outcome` MUST show `failed`, `needs_input` and `awaiting-human` MUST show `waiting-input`, `quarantined` MUST show `parked`. A run showing `ran` as `done` or `unknown_outcome` as `unknown` FAILS this item. ALSO paste `integration-deferred`'s resolved stage together with the recorded OQ-02 ruling it implements and the `git diff` of the spec's Section 7.2 row added in the same change. A run in which `integration-deferred` resolves to `unknown`, or resolves to a stage with no ruling and no spec row, FAILS this item: the first is the gray fallthrough Section 6 calls a defect, and the second is an unreviewed presentation decision written into the canonical module.
  - Observed evidence: VERIFIED 2026-09-20. All five review-added words resolve to their spec-assigned stage (`ran` -> recovering NOT done; `unknown_outcome` -> failed NOT unknown; `needs_input`/`awaiting-human` -> waiting-input; `quarantined` -> parked), and `integration-deferred` -> recovering per OQ-02's resolved ruling, with the spec Section 7.2 row added in this same change. Diff and output in the block below.

    ```text
    == the five review-added words ==
      ran                -> recovering      ↩︎   (required recovering) OK
      unknown_outcome    -> failed          ✘   (required failed) OK
      needs_input        -> waiting-input   …   (required waiting-input) OK
      awaiting-human     -> waiting-input   …   (required waiting-input) OK
      quarantined        -> parked          ◇   (required parked) OK

      ran is NOT done: True
      unknown_outcome is NOT unknown: True

    == the sixth row: integration-deferred ==
      integration-deferred -> recovering  ↩︎  (not unknown: True, not blocked: True)
    ```

    THE RULING IT IMPLEMENTS is OQ-02, `- Status: resolved`, resolved 2026-09-19 to `recovering` FROM CODE EVIDENCE rather than preference: `runner_shutdown.py:84-87` files the status under "in-flight / recoverable" and says the item "is awaiting a re-attempt"; `oc_runipd.py:6123` records it as DELIBERATELY absent from `TERMINAL_STATES`; `oc_runipd.py:6554-6560` shows `retry_deferred_integrations` actually SCHEDULING that re-attempt at zero cost. Work advances by itself, which is `recovering`'s definition and not `blocked`'s.

    THE SPEC ROW, ADDED IN THIS SAME CHANGE (the `- Scope-Paths:` declaration was added FIRST, in a separate edit, per the plan's Spec / documentation sync rule; see decision 03-udgilu-D1):

    ```text
    diff --git a/.aw/records/specs/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md b/.aw/records/specs/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md
    @@ -333,6 +333,7 @@ only when the subtype is genuinely unavailable.
     | `needs_input`, `awaiting-human` | waiting-input |
     | `ran` | recovering |
     | `unknown_outcome` | failed |
    +| `integration-deferred` | recovering |
     | stale projected `abandoned?` or another inference | unknown |
    ```

    A rationale paragraph was added below the table too (full diff in the execution report). It is a SEPARATE paragraph rather than an extension of the existing one, because that paragraph opens "THE FOUR ROWS ABOVE WERE ADDED AT REVIEW (2026-09-13)" and folding a 2026-09-19 decision into it would assert a history that did not happen (decision 03-udgilu-D3).

    `tests/test_lifecycle_style.py::SpecSectionCoverageTests::test_integration_deferred_has_a_spec_row` pins the module-versus-spec agreement, and it FAILED before the row was added (the one failure in the first run of the new file: `1 failed, 63 passed`), then passed after.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste test output for the Section 8 precedence cases: a failed-integrity input beating a stale active field (criterion A8), a blocked obstruction beating a ready native status (A9), and a live activity beating a native mapping (A7). Also paste evidence the resolver returned native status and activity as separate fields and mutated neither input.
  - Observed evidence: VERIFIED 2026-09-20. `PrecedenceTests` 11 passed: A8 (integrity beats a stale active field), A9 (obstruction beats a ready native status), A7 (activity beats the native mapping while the stored status stays `approved`), plus native status and activity returned as SEPARATE fields, no input mutated, and the tables read-only. Full output in the block below.

    TEST OUTPUT for the precedence cases:

    ```text
    $ python3 -m pytest tests/test_lifecycle_style.py::PrecedenceTests -o addopts="" -v --tb=short
    tests/test_lifecycle_style.py::PrecedenceTests::test_native_status_and_activity_are_returned_separately PASSED [  9%]
    tests/test_lifecycle_style.py::PrecedenceTests::test_condition_beats_activity_but_not_obstruction_or_integrity PASSED [ 18%]
    tests/test_lifecycle_style.py::PrecedenceTests::test_integrity_sound_values_do_not_trip_the_failure_rung PASSED [ 27%]
    tests/test_lifecycle_style.py::PrecedenceTests::test_a19_work_kind_cannot_affect_resolution PASSED [ 36%]
    tests/test_lifecycle_style.py::PrecedenceTests::test_a8_integrity_failure_beats_a_stale_active_field PASSED [ 45%]
    tests/test_lifecycle_style.py::PrecedenceTests::test_tables_are_read_only PASSED [ 54%]
    tests/test_lifecycle_style.py::PrecedenceTests::test_a9_obstruction_beats_a_ready_native_status PASSED [ 63%]
    tests/test_lifecycle_style.py::PrecedenceTests::test_resolver_mutates_no_input PASSED [ 72%]
    tests/test_lifecycle_style.py::PrecedenceTests::test_echoed_native_status_preserves_the_callers_spelling PASSED [ 81%]
    tests/test_lifecycle_style.py::PrecedenceTests::test_integrity_beats_obstruction PASSED [ 90%]
    tests/test_lifecycle_style.py::PrecedenceTests::test_a7_activity_beats_the_native_mapping_without_mutating_it PASSED [100%]
    ============================== 11 passed in 0.12s ==============================
    ```

    And the resolved values themselves, so the assertions are readable rather than merely green:

    ```text
    == A8: failed integrity beats a stale active field ==
       failed ✘ | activity input was 'executing', native 'approved'

    == A9: blocked obstruction beats a ready native status ==
       blocked ⚠︎ | obstruction echoed as: 'gate D-021'

    == A7: live activity beats the native mapping ==
      stage=executing glyph=▶ native_status='approved' activity='executing'
      SEPARATE FIELDS: native_status is not activity -> True

    == no input mutated ==
      caller dict unchanged: True
      module stage table unchanged: True
      tables are read-only: TypeError: 'mappingproxy' object does not support item assignment
    ```

    A7's stored status is UNCHANGED at `approved` while the display reads `executing`, which is the D7 overlay rule: nothing here transitions an artifact.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the raised error (message included) from a deliberately duplicated stage key, and from a mapping table with a known status removed. Silent success on either FAILS this item. THEN REVERT BOTH SCRATCH MUTATIONS AND PROVE IT: paste `git diff` over `agent_workflows/` showing it EMPTY before any commit. PORTED 2026-09-19 from review lane `review-sweep-run-20260919T133719Z-1618106` (finding PR-008), which observed that this item's evidence REQUIRES deliberately breaking the module, and that nothing told the executor to undo it; committing the duplicate key or the removed status would ship a broken stage table.
  - Observed evidence: VERIFIED 2026-09-20. Both raises observed with their messages naming the offending key (duplicate stage key; family declaring a known status it does not map), plus a fresh-interpreter IMPORT-TIME raise proven by breaking the file on disk. BOTH scratch mutations reverted and proven: sha256 identical before/after, and `git diff -- agent_workflows/` EMPTY before any commit. Full output in the block below.

    THE TWO RAISES, both with their messages, both naming the offending key:

    ```text
    == duplicate stage key is REJECTED ==
      LifecycleStyleError: duplicate semantic stage key 'formative': spec Section 5 defines each stage exactly once, so two rows for one key means one of them is wrong

    == a mapping table with a KNOWN STATUS REMOVED is REJECTED ==
      LifecycleStyleError: family 'plans' declares known statuses it does not map: executed

    == restored, and validate() is clean again ==
      validate() raised nothing
      plans table has 'executed' again: True
    ```

    THE IMPORT-TIME RAISE PROVEN SEPARATELY, by breaking the file ON DISK and importing in a fresh interpreter (the in-process checks above exercise the builder and `validate()`; this proves the module actually fails closed at import):

    ```text
    sha256 BEFORE: 38fa5afd2b718a7e8bc5ad5ff22e5b0eaeb7e619786298c7f7c224f235945cbe
    import exit code: 1
    agent_workflows.lifecycle_style.LifecycleStyleError: duplicate semantic stage key 'ready': spec Section 5 defines each stage exactly once, so two rows for one key means one of them is wrong
    reverted
    sha256 AFTER : 38fa5afd2b718a7e8bc5ad5ff22e5b0eaeb7e619786298c7f7c224f235945cbe
    IDENTICAL: yes
    ```

    THE MANDATORY REVERT PROOF, before any commit:

    ```text
    $ git diff -- agent_workflows/
    [empty]
    $ git diff --stat -- agent_workflows/
    [empty]
    $ git status --porcelain -- agent_workflows/
    ?? agent_workflows/lifecycle_style.py
    ```

    The only entry is the UNTRACKED new file this plan creates, which is the expected state; no tracked file under `agent_workflows/` is modified, so neither scratch mutation survived.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Paste the BARE `python3 -m pytest` summary line and compare it against the baseline below. Then paste proof the A2 test actually bites: add a bogus status to an owner enum in a scratch fixture, show the suite FAILING, then remove it and show it passing. A test that cannot fail is not evidence. THE REMOVAL IS MANDATORY, NOT OPTIONAL PHRASING (ported 2026-09-19 from lane `review-sweep-run-20260919T133719Z-1618106`, finding PR-008): paste `git diff` over `agent_workflows/` and `tests/` showing it EMPTY after the fixture is removed and before any commit. Committing the bogus status would leave an A2 test that cannot fail, which is the exact defect this V-item exists to disprove. ALSO paste, for EACH of the seven owners named in E-06, the assertion and its result, so a silently absent family is visible: plans, specs, research, backlog, releases, runner item dispositions, and set states. Paste the prompts assertion too, with its directory-derived source stated (F-06), since there is no `prompts.STATUSES` to enumerate. A V-06 that reports a green suite while covering six of eight families FAILS this item, which is the specific failure mode OQ-01 was recorded against.
  - Observed evidence: VERIFIED 2026-09-20. Bare suite `7157 passed, 3 skipped, 2 xfailed`; the A2 guard PROVEN to fail when a bogus status is added to an owner enum, then reverted with `git diff -- agent_workflows/ tests/` EMPTY; all EIGHT families asserted (13 passed), prompts directory-derived. Four color-env nodes failed on the FIRST run and are pre-existing (a baseline tree without my files failed a DIFFERENT node); filed as backlog `4znh53`. Full output in the block below.

    THE BARE SUITE, run as `python3 -m pytest` with no added flags:

    ```text
    7157 passed, 3 skipped, 2 xfailed, 3 warnings in 170.90s (0:02:50)
    ```

    COMPARED TO THE BASELINE (`8369 passed, 3 skipped, 2 xfailed` recorded at HEAD `07dabf1b`). THE TOTAL FELL RATHER THAN ROSE, and the honest reading is that the baseline number is NOT comparable: this lane is based on `bb714fd8`, eleven commits and several days later, and a `chore/test-sprawl-round4` merge (`8fd2658a`, "replace source-text pins with behavioral tests (46 -> 6 in 18 files)") deliberately DELETED tests in between. The plan's own instruction is to compare NODE IDS rather than totals, so the comparable measurement is the one made IN THIS LANE: a baseline run with this plan's two files removed and its record edits stashed produced `7092 passed`, and the run with them produced `7157 passed`, a rise of 65, which is the size of the new file (64 tests) plus one. Zero new failing node ids.

    THE FIRST FULL RUN REPORTED FOUR FAILURES AND THEY ARE NOT MINE. Reported rather than buried, because a reader of the green line above deserves to know it took three runs. Run 1 (my files present) failed four color nodes: `tests/test_term.py::ShouldColorGridTests::test_every_term_value_matches_the_ruled_expectation`, `::test_every_no_color_force_color_cell_matches_the_ruled_expectation`, `::test_a_falsey_force_color_never_forces_and_never_suppresses`, and `ColorPrecedenceTests::test_env_beats_detection_without_a_flag`. Run 2, on a BASELINE tree with my two files moved out and my record edits stashed, failed a DIFFERENT node: `tests/test_runner_shared.py::SharedColorDecisionTests::test_a_falsey_force_color_no_longer_forces_color_into_a_pipe`. Run 3, on the restored tree, passed entirely. Every affected node passes in isolation (`tests/test_term.py` alone: 34 passed; `test_term` + `test_runner_shared` + `test_pwatch` together: 234 passed; the three failing classes selected directly: 20 passed). The cause is shared mutable state and not a wrong assertion: those tests set and pop `NO_COLOR`/`FORCE_COLOR`/`TERM` in `os.environ`, which is PROCESS-GLOBAL, while `addopts` runs `-n auto --dist=worksteal`, so several land in one worker and observe each other. A baseline failure on a different node in a tree WITHOUT my changes is what makes this pre-existing rather than caused. FILED as backlog `4znh53` (`bug`, `Blocks-Release: next`) rather than left as scrollback.

    THE A2 GUARD BITES. A bogus status added to the OWNER ENUM (`runner_shutdown.KNOWN_ITEM_STATUSES`), on disk so pytest's fresh import sees it:

    ```text
    WITH BOGUS STATUS IN THE OWNER ENUM:
      exit code: 1
      F............                                                            [100%]
      =========================== short test summary info ============================
      FAILED tests/test_lifecycle_style.py::MappingTotalityTests::test_runner_items_total_over_KNOWN_ITEM_STATUSES
      1 failed, 12 passed in 0.15s

    REVERTED.
    runner_shutdown.py sha BEFORE: bee6301c92f07c8cb4ddafa32400d88ea36bb8b146bff70c1cf3d2e008695452
    runner_shutdown.py sha AFTER : bee6301c92f07c8cb4ddafa32400d88ea36bb8b146bff70c1cf3d2e008695452
    ```

    THE MANDATORY REVERT PROOF over BOTH trees, before any commit:

    ```text
    $ git diff -- agent_workflows/ tests/
    [empty]
    $ git diff --stat -- agent_workflows/ tests/
    [empty]
    $ git status --porcelain -- agent_workflows/ tests/
    ?? agent_workflows/lifecycle_style.py
    ?? tests/test_lifecycle_style.py
    ```

    Only the two UNTRACKED new files this plan creates. No tracked file modified, so the bogus status did not survive.

    EVERY FAMILY, EACH WITH ITS ASSERTION AND RESULT (eight families, none silently absent):

    ```text
    $ python3 -m pytest tests/test_lifecycle_style.py::MappingTotalityTests -o addopts="" -v --tb=no
    ::test_gate_statuses_that_section_7_2_names_are_mapped PASSED           [  7%]
    ::test_research_total_over_STATUSES PASSED                              [ 15%]
    ::test_run_ledger_total_over_run_state_ALL_STATES PASSED                [ 23%]
    ::test_specs_total_over_SPEC_STATUSES PASSED                            [ 30%]
    ::test_prompts_directory_derived PASSED                                 [ 38%]
    ::test_runner_items_total_over_KNOWN_ITEM_STATUSES PASSED               [ 46%]
    ::test_comms_acks_total_over_ACK_STATES PASSED                          [ 53%]
    ::test_releases_total_over_RELEASE_STATUSES PASSED                      [ 61%]
    ::test_plans_total_over_RECOGNIZED PASSED                               [ 69%]
    ::test_every_mapped_value_is_a_defined_stage PASSED                     [ 76%]
    ::test_backlog_total_over_STATUSES PASSED                               [ 84%]
    ::test_set_states_total_over_ALL_SET_STATES PASSED                      [ 92%]
    ::test_every_family_has_exactly_one_policy PASSED                       [100%]
    ============================== 13 passed in 0.17s ==============================
    ```

    Mapping the seven NAMED owners to their assertions: plans -> `plans.RECOGNIZED` (9 members); specs -> `attention_contract.SPEC_STATUSES` (9); research -> `research_contract.STATUSES` (4); backlog -> `backlog.STATUSES` (5); releases -> `releases.RELEASE_STATUSES` (3); runner items -> `runner_shutdown.KNOWN_ITEM_STATUSES` (15); set states -> `set_state.ALL_SET_STATES` (7). Each count verified by import at execution time and matching the plan's review-time measurement exactly.

    PROMPTS, DIRECTORY-DERIVED (F-06): `agent_workflows/prompts.py` has NO status enum, so `test_prompts_directory_derived` first asserts `not hasattr(prompts, "STATUSES")` (so the test breaks loudly if one is ever added rather than silently continuing to read directories), then parses `ipd_lint._dir_of`'s anchor tuple out of the source and asserts it equals the five lanes it maps. The lane list therefore cannot drift from the owner it is derived from.

    THREE ASSERTIONS BEYOND E-06's LIST, with their reasons (decision 03-udgilu-D4): `run_state.ALL_STATES` in full, because Section 7.3 is one spec table with TWO owners and `set_state` covers only the `set_`-prefixed half; `comms.ACK_STATES` in full, because Section 7.4's map is provided at all; and `run_gates` for `needs_input` ONLY, because Section 7.2 names that one member and the enum's other five are a gate-DECISION vocabulary the spec deliberately does not map.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved udgilu --by-human`). Its `- Item-Dependencies: executed:yaxr4i, executed:n4xq3l` edges are re-checked at dispatch: `yaxr4i` because spec Section 12a makes it upstream, and `n4xq3l` because the same section forbids building the resolver before the re-review round is recorded.

OPEN QUESTIONS: OQ-01 is RESOLVED (the owner list is written into E-06). OQ-02 is `- Blocking: yes` and UNRESOLVED, so `aw ipd lint` refuses this plan at every checkpoint until a maintainer rules on `integration-deferred`. That refusal is intended: E-03, E-06 and V-03 all depend on the answer, and the three ways to proceed without it each corrupt the canonical module or gut the A2 test. If the ruling adds a Section 7.2 row, ALSO add the `uonrjg` spec path to `- Scope-Paths:` in the same edit, per Spec / documentation sync above.

SCOPE FENCE: the files this plan may write are those declared in `- Scope-Paths:` (`agent_workflows/lifecycle_style.py`, `tests/test_lifecycle_style.py`), plus the `uonrjg` spec ONLY IF the OQ-02 ruling is applied AND that path has been added to the declaration first. An out-of-scope edit is permitted but must then be JUSTIFIED, which `aw ipd finalize` enforces by refusing to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. In particular this child must NOT touch `term.py`, `attention.py`, `render_stream.py`, either runner, or any consumer: it creates the semantic source and converts nothing, and deleting any existing palette here would break live views (that is `qdd5jq`'s work, after every consumer converts). DO STOP AND REPORT for one genuinely unsafe condition: if an owner enum named in E-06 has moved or been renamed so its symbol is absent, report that rather than substituting a hand-copied status list, which is exactly the drift criterion A2 exists to catch.

HONESTY RULE (hard MUST): when reporting tests or measurements, paste the ACTUAL command output. Never claim a suite run, a resolver dump, or an owner-enum assertion you did not run. A V-item's evidence block must contain real output, not a description of expected output.

On completion: append the workflow-history line, set the terminal `Status: executed`, and move this plan to `.aw/records/plans/executed/` via `aw ipd finalize` as a post-gate lifecycle step, never as a checklist item and never as a hand-rolled `git mv`. When a runner owns the turn it performs that finalize itself; a hand-run executor invokes it directly. Commit path-scoped (`git commit -m msg -- <path>`); never `git add -A`; never push.
