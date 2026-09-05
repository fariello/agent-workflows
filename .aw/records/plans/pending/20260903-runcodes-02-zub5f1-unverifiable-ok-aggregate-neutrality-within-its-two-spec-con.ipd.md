# IPD: unverifiable-ok aggregate neutrality within its two spec constraints

- Date: 2026-09-03
- Kind: child
- Concern: Spec `25kzda` 2.1 and 4.10 specify `--unverifiable-ok`, a flag that makes an unverifiable item NEUTRAL in the aggregate exit code while leaving the item's own outcome and verification label untouched. It does not exist: `unverifiable_ok` and `unverifiable-ok` both grep to ZERO hits in `agent_workflows/`. The flag is DOUBLY CONSTRAINED and both constraints are the point - it may change ONLY the aggregate, never an item's outcome or label (4.10's `PROMPT-UNVERIFIABLE` row), and it is LEGAL ONLY after contractless prompts were admitted by `--allow-unverifiable` or the interactive `run unverifiable` confirmation. A flag that quietly relabeled an item, or that worked standalone, would be a fail-OPEN reading of the same words.
- Scope: Implement the aggregation predicate PURELY (testable with no live run) so an unverifiable item classifies as a FAILURE contribution by default and as NEUTRAL under the flag, with neutral distinct from success (spec 5.6 grants exit 0 only when every other actionable item is verified, so an integer-sum design cannot express the rule), prove the item's outcome and verification label are byte-identical either way, and refuse the flag when its precondition is absent. Excludes the 13 `RUN-*` codes (Order 1, `wlxkoz`), excludes the retry-budget range (Order 3, `sq61qd`), excludes BUILDING `--allow-unverifiable` or the interactive confirmation (both unbuilt; see F-3 and OQ-01), and excludes wiring anything into either runner module.
- Scope-Paths: agent_workflows/run_evidence.py, tests/test_run_evidence_completion.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: runcodes
- Order: 2
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: zub5f1
- Approval: 2026-09-05, recorded via aw ipd set: status set to approved
- Blocks-Release: next
- From-Spec: 25kzda

## Workflow history
- 2026-09-05 executed (opencode its_direct/pt3-claude-opus-5-1m-us): E-01..E-03 performed and V-01..V-03 verified with pasted evidence at HEAD `022c3509` (implementation commit `022c3509`, started from `d91cd795`). Landed `aggregate_run_exit` as a PURE predicate in `run_evidence.py` with THREE-VALUED contributions (`success`/`neutral`/`failure`), integers confined to `_CLASSIFICATION_EXITS` transcribing spec 5.6's RUN table (deliberately NOT `run_cli.py`'s inspection table), spec `:938`'s six non-maskable classes enumerated as data with all six represented, and `_CLASSIFICATION_PRIORITY` keeping a human gate (3), a run-wide class (4), and interruption (130) outranking a neutralized item per `:936`. E-02's admission precondition refuses a standalone flag and returns the refusal as DATA in the module's existing `CompletionPredicate` shape - no `raise` added (the module still has none) and no exception class - yielding the DEFAULT non-neutral aggregate rather than silently granting neutrality. E-03 added 22 tests, purely additive (`408\t0`; zero deletions, no existing assertion touched). BOTH mandatory sabotages were observed FAILING and reverted: relabeling under the flag broke label-invariance (`'ran' != 'verified'`), and neutral-collapsed-into-success broke the not-all-verified case (`'success' != 'neutral'`); the literal integer-sum variant was also run and was caught by the priority table masking a run-wide abort (`'all_clear' != 'run_wide'`). Suite bare: 31 failed / 4440 passed before, 31 failed / 4462 passed after, with the failing SET byte-identical by `diff` of sorted node ids (all 31 pre-existing; none in this plan's test file). `aw check plans` unchanged at `errors 11 warnings 0` (no-worsening; it does not pass). `aw ipd lint --phase pre-transition` conforming. UNDER-SCOPE AS DESIGNED: no CLI flag exists, so no operator can reach this rule; `runflags-01` (`uyeko5`) owns building `--unverifiable-ok`/`--allow-unverifiable` and binding them to these two parameters. One material decision recorded (D-1: lane worktree vs the primary checkout for the suite baseline). `aw ipd begin`/`finalize` were REFUSED to this worker role (`AW-LIFECYCLE-ROLE-001`); the runner owns the lane transition. Not pushed.
- 2026-09-05 approved (aw set): status set to approved

- 2026-09-04 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 (6 findings, all FIXED in place, zero deferred, zero open). Verified at HEAD `298be4b2`, working tree clean, target plan committed and unchanged, so the pre-review snapshot was correctly skipped. `aw ipd lint --phase author` conforming before review and `--phase review-finalize` conforming after. The plan's own measurements HELD on re-measurement: `unverifiable`-anything is still one prose hit at `run_selection_policy.py:168`, and `run_evidence.py` really is the single completion authority. TWO FINDINGS CHANGED THE DESIGN, not just the wording. PR-001 (HIGH): E-01 told the executor to align the aggregate onto `run_cli.py:35-40`, which is the INSPECTION-command table for `aw run show|evidence|verify-ledger`; the RUN aggregate table is spec 5.6 (`:940-949`) and the two DISAGREE at the same numbers (`run_cli` `3`=blocked, `4`=invalid-evidence vs spec `3`=human-input, `4`=run-wide class), so following the plan as written would have encoded the wrong contract while citing evidence for it. PR-003 (HIGH): "contributes 1 by default and 0 under the flag" collapses NEUTRAL into SUCCESS, because a verified item also contributes 0 - and spec `:944` grants exit 0 only when every OTHER actionable item is verified, so an integer sum cannot express the rule the plan exists to implement; E-01 now requires a three-valued classification with integers only at the exit mapping, and E-03/V-03 gained the not-all-verified case plus a second sabotage, since that defect is invisible to the label-invariance test. THREE MORE: PR-002/F-8, the spec's per-item vocabulary is UNBUILT (`"ran"` and `verification_unavailable` both zero; `run_state.ALL_STATES` and `run_ledger_schema.LANE_OUTCOMES` have no `ran`), so the predicate must treat the outcome/label as opaque pass-through rather than minting runner vocabulary this plan's fence excludes. PR-004, E-02's "typed error or explicit result, consistent with how the module already reports refusals" named two mutually exclusive mechanisms and only one is the convention: the module has ZERO `raise` statements and no exception class, so the refusal is DATA, and the plan now also says a refused invocation yields the DEFAULT aggregate, not the neutral one. PR-005/F-9, spec `:938`'s six non-maskable classes and `:936`'s higher-priority-exit rule were absent from the plan entirely. PR-006/F-10, F-6's "do not run concurrently with Order 1" is prose with NO machine enforcement: executed live, the Set coordinator puts `wlxkoz` and `zub5f1` in the same `parallel_mutating` wave with `conflicts=0`, because `ipd_set_plan.py:1115` compiles the manifest with no ownership declarations so every node carries `writes=()`; the fence now says to verify by inspection instead of trusting the scheduler. Also corrected F-3's own evidence command, which escaped its regex alternation and so returned zero hits for the wrong reason, and OQ-01's `- Status:` from `open` to `resolved` (its body already recorded the maintainer's 2026-09-04 answer). Two reversible decisions recorded (D-1, D-2). Review artifact: `.aw/records/reviews/20260903-runcodes-02-zub5f1-unverifiable-ok-aggregate-neutrality-within-its-two-spec-con.review.md`

- 2026-09-03 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): SPLIT OUT OF `wlxkoz` (Order 1) at the maintainer's direction, discharging that plan's F10 / review-round-2 PR-004 (three independent concerns bundled; must be split before execution). This child carries the parent's E-03. MEASURED AT AUTHORING rather than inherited: `unverifiable_ok`/`unverifiable-ok` still grep to ZERO in the package, so the flag is genuinely unbuilt. A FINDING THE PARENT DID NOT RECORD, and it shapes this plan (F-3): the flag's PRECONDITION is also unbuilt - `--allow-unverifiable` and the interactive `run unverifiable` confirmation both grep to zero, surviving only as a prose mention in `run_selection_policy.py:168`. So "refuse when the precondition is absent" cannot be implemented against a real flag today, and E-02 therefore implements the refusal against an explicit PARAMETER rather than inventing a CLI surface this plan does not own. Recorded as non-blocking OQ-01 with a defensible default. The parent's E-05 test-ownership question is settled for this child: it touches ONLY `tests/test_run_evidence_completion.py`, never `tests/test_run_recovery_cli.py` (Order 3's file), so the two children cannot collide over a shared test file.

## Goal

Make an unverifiable item skippable in the AGGREGATE without ever making it look verified, so an operator can finish a run with a known-unverifiable step and still cannot be misled about that step's own result.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the aggregation predicate, and the constraint that makes it safe

- [x] E-01 Add the aggregation predicate to `agent_workflows/run_evidence.py` as a PURE function: given the per-item results and an `unverifiable_ok: bool`, return the aggregate classification and the exit code it maps to. Pure means NO live run, NO ledger, NO subprocess: it takes data and returns a value, so the whole rule is testable in isolation.
  RETURN A THREE-VALUED CLASSIFICATION PER ITEM, NOT AN INTEGER SUM (corrected at review, PR-003). An earlier wording said the item "contributes 1 by default and 0 under the flag", which COLLAPSES neutral into success: a verified item also contributes 0, so with an integer sum an implementation cannot distinguish "every other item verified plus one neutral" from "every item verified" - and spec 5.6 (`:944`) makes exit 0 conditional on EVERY other actionable item being verified, so that distinction is load-bearing, not stylistic. Name the three contributions explicitly (for example `success` / `neutral` / `failure`) and let integers appear in exactly ONE place: the mapping from the aggregate classification onto the exit code. Then F-4's "neutral is not complete" is checkable at the type level instead of being a comment.
  USE THE SPEC'S AGGREGATE EXIT TABLE, WHICH IS NOT `run_cli.py`'s (corrected at review, PR-001). The authoritative table for a RUN aggregate is spec `25kzda` 5.6 (`:940-949`): 0 all-verified-or-benign, 1 item failed / `dependency_not_met` / `ran`-without-the-flag, 2 invalid invocation, 3 human input required, 4 the six run-wide classes, 130 interruption. `run_cli.py`'s constants (`:37-50`) are the table for the READ-ONLY inspection commands (`aw run show|evidence|verify-ledger`) and disagree materially with the run table at the same numbers (its `3` is "blocked", its `4` is "invalid evidence"), so aligning to it would encode the wrong contract. Do NOT reconcile or edit `run_cli.py` here; it is outside this plan's Scope-Paths.
  TAKE THE ITEM'S OUTCOME AND LABEL AS OPAQUE PASS-THROUGH DATA (corrected at review, PR-002). MEASURED: the spec's per-item vocabulary is UNBUILT - `"ran"` and `verification_unavailable` both grep to ZERO in `agent_workflows/`, `run_state.ALL_STATES` (`:38-51`) has no `ran`, and `run_ledger_schema.LANE_OUTCOMES` (`:111-113`) has none either. So this predicate must NOT mint that vocabulary (it belongs to the runner surface this plan explicitly excludes): accept the item's outcome and verification label as values it reads and passes through UNCHANGED, and key neutrality off an explicit unverifiable flag/predicate on the item rather than off a string it defines. That is what makes E-03's invariance test assert something real without inventing a second vocabulary.
  NEUTRALITY IS NARROW, AND THE SPEC ENUMERATES ITS LIMITS. Per spec `:938`, `--unverifiable-ok` cannot mask ANY of six classes: a failed prompt process, a scope/containment failure, a host-capability refusal, a `dependency_not_met` item, a human gate, or a run-wide abort class. Carry those six as an explicit enumerated list in the implementation, not as prose, and honor spec `:936`'s "unless a higher-priority exit applies" so a human gate (exit 3) or a run-wide class (exit 4) still wins over a neutralized item. Where a class has no shipped representation to test against, say so in the data rather than omitting it.
  DO NOT WIRE IT INTO A RUNNER and do not add a CLI flag: this plan lands the predicate and its tests only (the parent deferred runner wiring to dissolve the `rununify` sequencing conflict, and that reasoning is inherited).
  - Depends on: none
  - Expected outcome: a pure predicate in `run_evidence.py`; an unverifiable item classifies as `failure` by default and `neutral` under the flag, with `neutral` DISTINCT from `success` at the type level; the aggregate maps onto spec 5.6's table with integers in one place; the item's outcome and verification label are pass-through values the predicate never authors; the six non-maskable classes are an explicit list and a higher-priority exit still wins; other items' contributions are unchanged in both cases; no runner and no CLI touched.
  - Execution state: performed

- [x] E-02 Enforce the PRECONDITION: `unverifiable_ok` is legal ONLY when contractless prompts were explicitly admitted. Passing it alone must be REFUSED, not silently honored, because silently honoring it is the fail-open reading (spec 2.1).
  IMPLEMENT IT AGAINST AN EXPLICIT PARAMETER, NOT A FLAG THAT DOES NOT EXIST. MEASURED (F-3): `--allow-unverifiable` and the interactive `run unverifiable` confirmation are BOTH unbuilt (zero hits; only a prose mention at `run_selection_policy.py:168`). So the predicate takes the admission as an explicit argument (for example `unverifiable_admitted: bool`) and refuses when `unverifiable_ok=True` while admission is `False`. The refusal must state which precondition is missing. When the real flag is built, it binds to this parameter; do NOT invent the CLI surface here.
  MECHANISM, DECIDED FROM THE MODULE'S OWN EVIDENCE RATHER THAN LEFT TO THE EXECUTOR (corrected at review, PR-004): RETURN AN EXPLICIT REFUSAL RESULT, DO NOT RAISE. MEASURED: `run_evidence.py` contains ZERO `raise` statements and defines no exception class at all, so "a typed error ... consistent with how the module already reports refusals" named two mutually exclusive options and only one of them is actually this module's convention. The module reports every negative verdict as DATA (`CompletionPredicate(name, satisfied, details)` at `:96-99`, accumulated `reasons` at `:991`), so the refusal must be a value carrying the reason string, exactly like `redaction_blocks_verification` (`:717-727`) reports "verification could not conclude" as a finding rather than an exception. A raise would also break E-01's purity contract in practice, since a caller could not evaluate the aggregate to inspect it.
  THE REFUSAL MUST NOT SILENTLY BECOME NEUTRALITY. State plainly which aggregate a refused invocation yields: it is the DEFAULT (unverifiable contributes `failure`), never neutral, because honoring an illegal flag by ignoring only its error message would be the same fail-open reading spec 2.1 (`:132`) forbids.
  - Depends on: E-01
  - Expected outcome: `unverifiable_ok=True` with admission `False` returns an explicit refusal result whose reason names the missing precondition, and the aggregate it yields is the DEFAULT non-neutral one; with admission `True` the flag is honored; the refusal is returned as data in the module's existing `CompletionPredicate`/`reasons` shape, with no `raise` added and no exception class introduced.
  - Execution state: performed

- [x] E-03 Extend the SHIPPED `tests/test_run_evidence_completion.py` additively; do NOT create a new module and do NOT weaken, remove, or alter any existing assertion. The load-bearing case is the INVARIANT, so make it explicit: for the SAME unverifiable item, run the aggregation with the flag off and on and assert the item's OWN outcome and verification label are IDENTICAL in both, while only the aggregate differs. A test that checks only the aggregate would pass even if the implementation relabeled the item, which is the exact defect spec 4.10 forbids.
  Also cover: the aggregate differing in BOTH directions (off -> contributes, on -> neutral); the precondition refusal from E-02, INCLUDING that a refused invocation yields the DEFAULT aggregate and not the neutral one; a run whose OTHER items fail still failing under the flag (so neutrality is not blanket suppression); and the predicate being exercised with NO live run, which is what E-01's purity buys.
  ADD THE CASE THAT DISTINGUISHES NEUTRAL FROM SUCCESS (added at review, PR-003): assert that a run of one unverifiable item plus one item that is merely SKIPPED-but-not-verified does NOT exit 0 under the flag, because spec 5.6 (`:944`) grants exit 0 only when every other actionable item is VERIFIED. An integer-sum implementation passes every other case in this item and fails only this one, which is precisely why it is required.
  COVER THE SIX NON-MASKABLE CLASSES (added at review, PR-005): assert that the flag does not neutralize a `dependency_not_met` item or a human gate, and that a higher-priority exit still wins (spec `:936`, `:938`). Where a class has no shipped representation to construct, assert against the implementation's own enumerated list so the omission is visible rather than silent.
  - Depends on: E-01, E-02
  - Expected outcome: all cases pass; the label-invariance assertion is present and would fail if the item were relabeled; neutral is proven distinct from success by the not-all-verified case; the six non-maskable classes are covered or explicitly and visibly deferred; existing assertions in the shipped file pass unchanged.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `run_evidence.py` is the SINGLE completion authority (`evaluate_completion:804`, `is_complete:1081`, plus a 13-class `EV-*` false-completion taxonomy). Its own review established that a second completion checker means two disagreeing checkers, so neither can authorize completion. This plan adds an AGGREGATION rule over it, never a rival verdict.
- THERE ARE TWO DIFFERENT EXIT TABLES AND THEY DISAGREE (corrected at review). The RUN aggregate table is spec `25kzda` 5.6 (`:940-949`): 0/1/2/3/4/130. `run_cli.py` (`:11-14` docstring, `:37-50` constants) is the INSPECTION-command table for `aw run show|evidence|verify-ledger`, and at the same numbers it means different things (`3` blocked, `4` invalid evidence, `5` corrupted ledger, `6` operational, `7` not-a-ledger). This plan's aggregate MUST follow the spec table; `run_cli.py` is not this plan's contract and is not in its Scope-Paths.
- The module reports negative verdicts as DATA, never by raising: it contains ZERO `raise` statements and defines no exception class (measured). `CompletionPredicate(name, satisfied, details)` (`:96-99`) and the accumulated `reasons` list (`:991`) are the shapes a refusal must take.
- `redaction_blocks_verification` (`:717-727`) is the existing precedent for "verification could not conclude", which is the same family of condition as unverifiable, and it is reported as an `EV-REDACTION-CONFLICT` finding rather than an exception. Read it before designing a new one.
- THE SPEC'S PER-ITEM OUTCOME VOCABULARY IS NOT BUILT (measured at review). `"ran"` and `verification_unavailable` grep to ZERO in `agent_workflows/`; `run_state.ALL_STATES` (`:38-51`) is the STEP/run state machine (`pending`..`complete`) and has no `ran`; `run_ledger_schema.LANE_OUTCOMES` (`:111-113`) is `performed|blocked|failed|deferred|unknown_outcome|skipped`. So there is no shipped `ran`/`unavailable` label for this predicate to read, which is exactly why E-01 treats the outcome and label as opaque pass-through data instead of minting the vocabulary.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | The flag is entirely unbuilt: `unverifiable_ok` and `unverifiable-ok` both grep to ZERO hits under `agent_workflows/`. Re-measured at authoring, not inherited from the parent. | `rg 'unverifiable' agent_workflows/*.py` returns ONE line, a prose comment at `run_selection_policy.py:168` |
| F-2 | The constraint is what matters, not the flag. Spec 4.10's `PROMPT-UNVERIFIABLE` row and 2.1 together mean the flag may change ONLY the aggregate: an implementation that relabeled the item would satisfy a naive aggregate test while breaking the actual contract. That is why E-03's label-invariance case is the load-bearing one. | spec `25kzda` 2.1 bullet; 4.10 `PROMPT-UNVERIFIABLE` row |
| F-3 | **FOUND AT AUTHORING; the parent did not record it, and it changes E-02's shape.** The flag's PRECONDITION is ALSO unbuilt: `--allow-unverifiable` and the interactive `run unverifiable` confirmation both grep to zero and survive only as prose. So "refuse when the precondition is absent" has no real flag to read. E-02 therefore takes the admission as an explicit PARAMETER rather than inventing a CLI surface this plan does not own. RE-MEASURED AT REVIEW and still true; the citation was also CORRECTED, since the command as originally written (`rg 'allow.unverifiable\|allow_unverifiable'`) escapes the alternation and so matches a literal backslash - it returns zero hits for the wrong reason, which would let a future re-measurement "confirm" the finding without testing it. | `rg 'allow.unverifiable|allow_unverifiable' agent_workflows/` -> exactly one hit, the prose mention at `run_selection_policy.py:168` |
| F-4 | "Neutral" is ambiguous and the ambiguity is dangerous. Neutral must mean "does not make the aggregate fail", NOT "counted as complete" and NOT "suppresses other items". SHARPENED AT REVIEW: the danger is concrete, not abstract. An integer-contribution design (1 by default, 0 under the flag) gives a neutral item the SAME contribution as a verified one, and spec 5.6 (`:944`) grants exit 0 only when every OTHER actionable item is verified, so the sum cannot decide the case it exists to decide. E-01 therefore requires a three-valued classification with integers appearing only at the exit-code mapping. | spec `25kzda` `:944` vs `:937`; `run_cli.py:37-50` (the DIFFERENT inspection table, not this plan's contract) |
| F-8 | FOUND AT REVIEW. THE SPEC'S PER-ITEM VOCABULARY IS UNBUILT, so an implementation that keys neutrality off the string `ran` would be inventing the runner-surface vocabulary this plan's own fence excludes. `"ran"` and `verification_unavailable` grep to ZERO in the package; the two shipped vocabularies are the step state machine (`run_state.ALL_STATES:38-51`, no `ran`) and the lane outcomes (`run_ledger_schema.LANE_OUTCOMES:111-113`, no `ran`). E-01 therefore takes the outcome and label as opaque pass-through values. | `rg '"ran"' agent_workflows/` -> 0; `rg 'verification_unavailable' agent_workflows/` -> 0; `run_state.py:38-51`; `run_ledger_schema.py:111-113` |
| F-9 | FOUND AT REVIEW. THE SIX NON-MASKABLE CLASSES WERE NOT IN THE PLAN AT ALL. Spec `:938` enumerates exactly what `--unverifiable-ok` may never mask (failed prompt process, scope/containment failure, host-capability refusal, `dependency_not_met`, human gate, run-wide abort class) and `:936` reserves higher-priority exits. The plan's only guard was the generic "other items still fail", which does NOT cover a human gate (exit 3) or a run-wide class (exit 4) being outranked. Added to E-01 as an explicit enumeration and to E-03/V-01 as coverage. | spec `25kzda` `:936`, `:938`, `:947-948` |
| F-10 | FOUND AT REVIEW; F-6's "do not run concurrently" is a HUMAN instruction with NO machine enforcement, so state it as such. MEASURED: `aw ipd execute-set` compiles the manifest with NO ownership declarations (`ipd_set_plan.py:1115` calls `compile_manifest` without `ownership=`), so every node gets `writes=()` and the disjoint-file rule (`orchestrate_isolation.py:859-872`) sees nothing to conflict over. Executed live: two nodes for `wlxkoz` and `zub5f1` return `execution_mode='parallel_mutating'`, `conflicts=0`. The isolated worktrees make a silent same-file overwrite unlikely, but nothing derives the conflict from `Scope-Paths`, so the ONLY real protections are the declared `Item-Dependencies` edge and the fence text. | `ipd_set_plan.py:1115`; `orchestrate_isolation.py:859-872`; `worktree_lease.py:778` (the per-path lease exists but has no caller outside `tests/test_ipd_set_executor.py:306`) |
| F-5 | SPLIT PROVENANCE: this is the parent's E-03, which had `Depends on: E-01` only for the table it did not actually need, and which shared a Scope-Paths list with a 13-code transcription task and a retry-budget check in a different module. | parent `wlxkoz` F10 / review round 2 PR-004 |
| F-6 | NO TEST-FILE CONTENTION WITH ORDER 3. This child touches only `tests/test_run_evidence_completion.py`; Order 3 owns `tests/test_run_recovery_cli.py`. Order 1 (`wlxkoz`) claims BOTH of this plan's paths (`run_evidence.py` and this test file), so this child and Order 1 must not run concurrently on them. NOTE the enforcement gap F-10 measures: that "must not" is prose, not a gate. | this plan's Scope-Paths against `wlxkoz`'s and `sq61qd`'s; see F-10 |
| F-7 | CONTENTION TO CHECK, inherited from the parent: APPROVED `0soncw` also claims `tests/test_run_evidence_completion.py` and is rewriting the `aw run` command strings its assertions invoke. Additive-only is a mitigation, not immunity. | parent F8; `0soncw`'s Scope-Paths |

## Proposed changes (ordered, validatable)

1. Add the pure aggregation predicate with default and flagged behavior (E-01).
2. Enforce the precondition against an explicit admission parameter, refusing the standalone flag (E-02).
3. Extend the shipped test module, with label-invariance as the load-bearing case (E-03).

## Deferred / out of scope (with reason)

- BUILDING `--allow-unverifiable` OR the interactive `run unverifiable` confirmation. Both unbuilt (F-3). **NOW OWNED BY `runflags-01` (`uyeko5`), authored 2026-09-04**, which registers the whole spec-2.1 flag surface on both runners and binds `--unverifiable-ok` to THIS plan's predicate; the parameter seam E-02 builds is the seam that plan plugs into, so the gap is tracked rather than left in prose. They are a user-facing admission surface with their own interactive-confirmation design; this plan consumes the admission as a parameter so it binds cleanly when they exist. See OQ-01.
- ADDING THE `--unverifiable-ok` CLI FLAG ITSELF. Same reason: the predicate is the deliverable here, and the CLI surface belongs with the admission flag it depends on.
- THE 13 `RUN-*` CODES: Order 1 (`wlxkoz`).
- THE RETRY-BUDGET RANGE: Order 3 (`sq61qd`).
- WIRING INTO `oc_runipd.py` / `agy_runipd.py`. Inherited from the parent, which deferred runner wiring to dissolve the `rununify` (`5e4sb6`) sequencing conflict rather than answer it.

## Scope check

- Over-scope: none. One shipped module gains a pure predicate; one shipped test module gains cases.
- Under-scope, DELIBERATE and stated plainly: when this plan completes, NO operator can pass `--unverifiable-ok`, because neither it nor its precondition flag exists as a CLI surface. The predicate lands tested and importable and nothing consults it yet. That is the same honest position the parent took about the 13 codes, and it is why the flag work is named in Deferred rather than implied.

## Required tests / validation

- THE LABEL-INVARIANCE CASE IS MANDATORY: same unverifiable item, flag off and on, item outcome and verification label IDENTICAL, only the aggregate different. Without it the suite cannot detect the one defect spec 4.10 forbids.
- THE NEUTRAL-IS-NOT-SUCCESS CASE IS EQUALLY MANDATORY: one unverifiable item plus one non-verified skip must NOT yield exit 0 under the flag (spec `25kzda:944`). Both mandatory cases must be observed FAILING against a deliberately broken implementation (V-03), since an invariant never seen to fail is not established.
- The aggregate must be shown differing in BOTH directions, and a run with other failing items must still fail under the flag (neutrality is not blanket suppression).
- The six non-maskable classes (spec `:938`) and the higher-priority-exit rule (`:936`) must be covered, or any class with no shipped representation explicitly and visibly recorded as uncovered.
- The precondition refusal must be shown, naming the missing admission, returned as DATA (no `raise` added to `run_evidence.py`), and yielding the DEFAULT aggregate rather than the neutral one.
- The predicate must be exercised with NO live run, proving E-01's purity.
- Every PRE-EXISTING assertion in `tests/test_run_evidence_completion.py` passes unchanged.
- Full suite BARE (`python3 -m pytest`), compared against YOUR OWN pre-change measurement at the HEAD you started from. No `-n0`, no second `-q`, no `-p no:randomly`.
- Measure in the PRIMARY checkout, not a scratch worktree (`tests/test_run_viewer.py` shows ~15 phantom failures in a detached worktree; backlog `dh0uno`).
- `aw check plans` NO-WORSENING against your own fresh baseline; do NOT claim it passes.

## Spec / documentation sync

- Implements the `--unverifiable-ok` rule of spec `25kzda` 2.1 (`:132`), 4.10 (`:674`), and the aggregate table of 5.6 (`:935-949`). No spec text changes.
- Record in the predicate's docstring that the CLI flag and its precondition flag are NOT yet built and that the admission arrives as a parameter, so the next reader does not conclude the feature is user-reachable.
- ALSO record in the docstring which exit table the predicate implements (spec 5.6's RUN table), and that it is deliberately NOT `run_cli.py`'s inspection table, whose 3/4/5/6/7 mean different things. Two disagreeing tables in one package is a trap for the next reader, and naming the one in force is cheaper than reconciling them (reconciliation is out of scope here).
- Record that the item's outcome/verification label are pass-through values, and that the spec's `ran`/`unavailable` vocabulary is not yet built anywhere in the package (F-8), so a later reader does not assume this predicate is where that vocabulary lives.

## Open questions

### OQ-01: Should this plan also build `--allow-unverifiable`, or only consume the admission?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: ANSWERED 2026-09-04 by the maintainer, and not by deferring: the flags are owned by a NEW plan, `runflags-01` (`uyeko5`), which registers all seven missing spec-2.1 flags on both runners and binds this one to the predicate E-01/E-02 land here. This plan still consumes only, and the flag is no longer untracked. ORIGINAL RATIONALE RETAINED: NOT BLOCKING, and the default is to consume only. Spec 2.1 makes `--unverifiable-ok` legal only after contractless prompts were admitted by `--allow-unverifiable` or the interactive `run unverifiable` confirmation, and MEASUREMENT shows neither exists (F-3). Building them here would add an interactive-confirmation surface, which is a different concern with its own UX and its own fail-open risks, and bundling it is precisely what got the parent plan split. So this plan takes the admission as an explicit parameter and the refusal is fully testable today; when the flags are built they bind to that parameter with no rework. If you want the flags in this plan, say so and they become their own E-items with their own confirmation design.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the predicate's signature and body showing it is PURE (no ledger, no subprocess, no run directory). Paste the aggregate for an unverifiable item with the flag OFF and ON, showing the per-item classification is THREE-VALUED and that `neutral` is a distinct value from `success` (not the same integer); paste the single place integers appear, i.e. the mapping onto spec 5.6's exit table (`25kzda:940-949`). Do NOT cite `run_cli.py`'s constants as the aggregate table: they are the inspection-command table and disagree at 3 and 4 (see the conventions section), and citing them would be evidence for the wrong contract.
    Paste the not-all-verified case: one unverifiable item plus one non-verified skip must NOT yield exit 0 under the flag (spec `:944`). Paste a case proving neutrality is NOT blanket suppression: a run whose other items fail must still fail under the flag. Paste the enumerated list of the six non-maskable classes (spec `:938`) as it appears in the code, and show a higher-priority exit still winning (spec `:936`). Finally, show the predicate does not author the item's outcome or verification label: paste the pass-through and confirm no new outcome vocabulary was introduced.
  - Observed evidence: measured at HEAD `022c3509` (implementation commit) in the lane worktree `.aw/worktrees/zub5f1`; see D-1 for why the primary checkout was not used and why that does not weaken the comparison.
    PURITY. Signature, `agent_workflows/run_evidence.py:2088`: `def aggregate_run_exit(items: Sequence[AggregatedItem], *, unverifiable_ok: bool = False, unverifiable_admitted: bool = False, invalid_invocation: Optional[str] = None, run_wide_abort_class: Optional[str] = None, interrupted: bool = False) -> RunAggregation`. The body reads only its arguments: no `Path`, no `subprocess`, no ledger, no run directory, no clock. Proven behaviorally, not just by reading - `test_predicate_is_pure_no_live_run_no_filesystem_no_subprocess` evaluates the aggregate with `subprocess.run` and `Path.exists` both patched to raise `AssertionError`, and it passes.
    THREE-VALUED, AND NEUTRAL IS NOT SUCCESS (`python3 -c` against the shipped module):
    ```
    OFF contribution='failure' classification='item_failure' exit=1
    ON  contribution='neutral' classification='all_clear' exit=0
    CONTRIBUTIONS = ('success', 'neutral', 'failure')
    neutral != success: True
    ```
    THE ONE PLACE INTEGERS APPEAR is `_CLASSIFICATION_EXITS` (`run_evidence.py:1846`), transcribing spec 5.6's RUN table:
    ```
    _CLASSIFICATION_EXITS = {'all_clear': 0, 'item_failure': 1, 'invalid_invocation': 2, 'needs_input': 3, 'run_wide': 4, 'interrupted': 130}
    _CLASSIFICATION_PRIORITY = ('interrupted', 'run_wide', 'needs_input', 'invalid_invocation', 'item_failure', 'all_clear')
    ```
    `run_cli.py`'s constants are NOT cited as the aggregate table. `test_exit_table_is_spec_5_6_not_the_run_cli_inspection_table` asserts the divergence is real (`run_cli.EXIT_BLOCKED == 3` and `EXIT_INVALID_EVIDENCE == 4` against this predicate's `needs_input == 3` and `run_wide == 4`), so a future reconciliation cannot make that test vacuous.
    NOT-ALL-VERIFIED (spec `:944`), the case an integer sum fails: `not-all-verified under flag: exit=1 classification='item_failure' contribs=['neutral', 'failure']`. Contrast case, proving the assertion discriminates rather than merely being pessimistic: one neutral plus one VERIFIED item does reach `exit=0`.
    NEUTRALITY IS NOT BLANKET SUPPRESSION: `other item fails under flag: exit=1 classification='item_failure'`.
    THE SIX NON-MASKABLE CLASSES as enumerated in code (`NON_MASKABLE_CLASSES`, `run_evidence.py:1901`), via `non_maskable_classes()`:
    ```
    ('a failed prompt process', 'scope/containment failure', 'host-capability refusal', 'dependency-not-met item', 'human gate', 'run-wide abort class')
    ```
    All six are `represented=True` (none deferred), each naming its signal; `validate_non_maskable_table()` returns `EvidenceValidationResult(ok=True, findings=())` and `test_non_maskable_classes_match_the_spec_text` parses spec `:938`'s own line so a dropped or reworded class fails. HIGHER-PRIORITY EXITS STILL WIN (spec `:936`), with the flag frozen and honored throughout: `human gate outranks: exit=3 classification='needs_input'`; `run-wide outranks: exit=4 classification='run_wide'` (asserted for all six of `ABORT_CLASSES`); interruption outranks even that at `exit=130`.
    NO VOCABULARY AUTHORED (F-8): `item OFF outcome/verification: ran / unavailable`, `item ON outcome/verification: ran / unavailable`, and `same object off/on: True True` - the `ItemAggregation` carries the caller's `AggregatedItem` BY IDENTITY, so the predicate cannot have rewritten it. `test_predicate_does_not_author_the_item_vocabulary` additionally feeds `outcome="totally-made-up"` through unchanged and greps this plan's own source block to assert neutrality is never keyed off a `"ran"`/`"unavailable"` string comparison.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the refusal when `unverifiable_ok=True` and admission is `False`, showing (a) the reason names the missing precondition, (b) it is RETURNED AS DATA in the module's existing shape and not raised, and (c) the aggregate it yields is the DEFAULT non-neutral one. Paste `rg -n 'raise ' agent_workflows/run_evidence.py` showing the module still contains no `raise`, since adding one would both break E-01's purity and depart from the module's measured convention. Paste the honored case when admission is `True`. Confirm NO CLI flag was added (paste a grep showing `--unverifiable-ok` and `--allow-unverifiable` are still absent from the CLI), since inventing the surface is outside this plan's fence.
  - Observed evidence: measured at HEAD `022c3509`.
    THE REFUSAL, returned as DATA:
    ```
    REFUSED invocation:
      refusals = (CompletionPredicate(name='unverifiable_ok_requires_admission', satisfied=False, details='--unverifiable-ok is legal only when contractless prompts were explicitly admitted by --allow-unverifiable or the interactive `run unverifiable` confirmation; that admission is absent, so aggregate neutrality was NOT applied and the default aggregate stands'),)
      unverifiable_ok_applied = False
      contribution = failure
      classification='item_failure' exit=1
      is CompletionPredicate: True
      reasons = ('refused --unverifiable-ok: missing precondition (contractless prompts were not explicitly admitted)', 'prompt-1: unverifiable and --unverifiable-ok was not frozen')
    ```
    (a) the reason NAMES the missing precondition, both flag spellings; (b) it is a `CompletionPredicate`, the module's existing shape, alongside a `reasons` entry; (c) the aggregate is the DEFAULT non-neutral one - contribution `failure`, exit 1 - not neutral. `test_refusal_is_not_downgraded_to_invalid_invocation` also asserts it is NOT laundered into exit 2, which would discard the real item verdict.
    NO `raise` ADDED. `rg -n 'raise ' agent_workflows/run_evidence.py` returns exactly ONE line, and it is DOCSTRING PROSE, not a statement: `2117:    contains zero ``raise`` statements and defines no exception class, and a raise would also defeat`. The executable form returns nothing: `rg -n '^\s+raise\b' agent_workflows/run_evidence.py` -> zero matches (exit 1). `rg -n 'class .*Error|class .*Exception' agent_workflows/run_evidence.py` -> zero matches (exit 1), so no exception class was introduced either. `test_refusal_is_returned_as_data_and_the_module_still_never_raises` asserts this from the test suite as well.
    HONORED CASE: `HONORED: refusals=() applied=True exit=0`. And admission ALONE grants nothing: `test_admission_alone_changes_nothing` shows `unverifiable_admitted=True, unverifiable_ok=False` still yields exit 1.
    NO CLI FLAG ADDED. The registration form an argparse call would use is absent: `rg -n "['\"]--unverifiable-ok['\"]|['\"]--allow-unverifiable['\"]" agent_workflows/` -> zero matches (exit 1). The bare-substring grep does return hits, and ALL of them are prose: one pre-existing comment at `run_selection_policy.py:168` plus this plan's own docstrings/comments in `run_evidence.py`. `test_no_cli_flag_was_added_by_this_plan` asserts the quoted form is absent from every module in the package, so a later accidental registration fails here.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the LABEL-INVARIANCE test and its output: the same unverifiable item under flag off and on, with the item's own outcome and verification label shown IDENTICAL in both and only the aggregate differing. Then PROVE IT IS NOT VACUOUS: deliberately make the implementation relabel the item under the flag, paste the assertion FAILING, and revert. An invariance test never observed failing does not establish the invariant, and this is the one defect spec 4.10 forbids.
    RUN THE SAME SABOTAGE ON THE NEUTRAL-IS-NOT-SUCCESS CASE: change the implementation to give a neutral item the same contribution as a verified one (the integer-sum design F-4 warns about), paste the not-all-verified assertion FAILING, and revert. That defect is as shippable as the relabeling one and no other case in this plan detects it.
    Paste `git diff tests/test_run_evidence_completion.py` proving no existing assertion was altered, plus the bare full-suite summary with its HEAD compared against your own pre-change baseline, measured in the primary checkout.
  - Observed evidence: measured at HEAD `022c3509`; pre-change baseline measured by me at HEAD `d91cd795` before any edit.
    THE LABEL-INVARIANCE TEST is `test_item_outcome_and_verification_label_are_identical_with_the_flag_off_and_on`. It aggregates the SAME item twice and asserts `off.items[0].item.outcome == on.items[0].item.outcome`, the same for `verification`, that both are literally `ran`/`unavailable`, that the source item is unmutated, and `assertIs` on both records; then that ONLY the aggregate differs (`failure`/exit 1 vs `neutral`/exit 0). Live output of the same comparison:
    ```
    item OFF outcome/verification: ran / unavailable
    item ON  outcome/verification: ran / unavailable
    same object off/on: True True
    OFF contribution='failure' ... exit=1
    ON  contribution='neutral' ... exit=0
    ```
    SABOTAGE 1, THE INVARIANT IS NOT VACUOUS. Made the flagged branch relabel the item (`item._replace(outcome="verified", verification="passed")`), the exact defect spec 4.10 forbids. Observed FAILING:
    ```
    >       self.assertEqual(off.items[0].item.outcome, on.items[0].item.outcome)
    E       AssertionError: 'ran' != 'verified'
    E       - ran
    E       + verified
    tests/test_run_evidence_completion.py:1742: AssertionError
    FAILED tests/test_run_evidence_completion.py::TestUnverifiableOkAggregateNeutrality::test_item_outcome_and_verification_label_are_identical_with_the_flag_off_and_on
    1 failed, 86 deselected in 0.18s
    ```
    Reverted; the file is byte-identical to the committed version (the sabotages were applied to a copy-restored working file, and the committed tree at `022c3509` contains none of them).
    SABOTAGE 2, NEUTRAL-IS-NOT-SUCCESS IS NOT VACUOUS, run in BOTH forms F-4 describes. Form (a), the flagged branch returns `CONTRIBUTION_SUCCESS` instead of `CONTRIBUTION_NEUTRAL` - a neutral item getting exactly a verified item's contribution. Observed FAILING on the not-all-verified case:
    ```
    >       self.assertEqual(
                result.items[0].contribution, evidence.CONTRIBUTION_NEUTRAL
            )
    E       AssertionError: 'success' != 'neutral'
    E       - success
    E       + neutral
    FAILED tests/test_run_evidence_completion.py::TestUnverifiableOkAggregateNeutrality::test_neutral_plus_a_non_verified_skip_is_not_exit_zero
    1 failed, 86 deselected in 0.18s
    ```
    Form (b), the LITERAL integer-sum aggregate the plan warns about: contributions summed as `0` for success-or-neutral and `1` otherwise, with exit 0 iff the sum is 0. Observed FAILING, and note WHICH assertion caught it - the priority table, i.e. the sum silently masked a run-wide abort class:
    ```
    >               self.assertEqual(result.classification, evidence.AGGREGATE_RUN_WIDE)
    E               AssertionError: 'all_clear' != 'run_wide'
    E               - all_clear
    E               + run_wide
    FAILED tests/test_run_evidence_completion.py::TestUnverifiableOkAggregateNeutrality::test_run_wide_abort_class_outranks_everything_but_interruption
    1 failed, 21 passed, 65 deselected in 0.23s
    ```
    A third, weaker form (collapsing the CONSTANT so `CONTRIBUTION_NEUTRAL == "success"`) was also observed failing, on `test_neutral_is_a_distinct_value_from_success` (`AssertionError: 'success' == 'success'`). All sabotages reverted before commit.
    NO EXISTING ASSERTION ALTERED. `git diff --numstat tests/test_run_evidence_completion.py` against the pre-change tree: `408\t0\ttests/test_run_evidence_completion.py` - 408 insertions, ZERO deletions. `git diff | grep -E '^-' | grep -v '^---'` returns nothing, so not one existing line was removed or modified; the new class is appended before the `if __name__` block. (`agent_workflows/run_evidence.py` is likewise `509\t0`, additive only.)
    FULL SUITE, BARE (`python3 -m pytest`, no `-n0`, no second `-q`, no `-p no:randomly`).
    Pre-change baseline at HEAD `d91cd795`:
    ```
    31 failed, 4440 passed, 3 skipped, 4 xfailed in 32.25s
    ```
    After, at HEAD `022c3509`:
    ```
    31 failed, 4462 passed, 3 skipped, 4 xfailed in 37.34s
    ```
    +22 passing (this plan's new tests), same 3 skipped and 4 xfailed. The failing SET is identical, not merely the count: `diff` of the sorted `FAILED` node ids from both runs is EMPTY, so nothing was broken and nothing pre-existing was accidentally fixed. Zero of the 31 are in `tests/test_run_evidence_completion.py`, which is 87 passed / 0 failed on its own. The 31 pre-existing failures are the known worktree-phantom cluster (`test_run_viewer.py`, `test_oc_runipd.py`, `test_agy_runipd_cli.py`, `test_ipd_lifecycle_cli.py`, and neighbors); see D-1.
    `aw check plans`: `errors 11   warnings 0` after, identical to my own pre-change baseline of `errors 11   warnings 0`. NO-WORSENING, and it does NOT pass: the 11 errors are pre-existing `wslayout` plan-frontmatter errors, untouched by this plan and outside its Scope-Paths.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 3 E-leaves, one task group, one concern: make an unverifiable item neutral in the aggregate without ever making it look verified.

Open questions: OQ-01 (build the admission flags here, or consume only) is RESOLVED, answered by the maintainer 2026-09-04 and now owned by `runflags-01` (`uyeko5`). Its `- Status:` was corrected from `open` to `resolved` at review: the body already recorded the answer, so leaving it `open` misreported the plan as carrying an unanswered question. No blocking question remains.

This plan is `to-review` and requires explicit human approval before execution.

Scope fence: touch ONLY `agent_workflows/run_evidence.py` and `tests/test_run_evidence_completion.py` (test file: additive cases only; no existing assertion weakened, removed, or altered). Do NOT add any CLI flag (`--unverifiable-ok` or `--allow-unverifiable`) and do NOT build the interactive confirmation. Do NOT touch `run_recovery.py` (Order 3 owns it). Do NOT touch `run_cli.py`: its exit constants are the INSPECTION table, this plan implements the spec 5.6 RUN table, and reconciling the two is a separate concern no plan currently owns. Do NOT touch either runner module. Do NOT mint the spec's `ran`/`unavailable` per-item vocabulary (F-8): it belongs to the runner surface this plan excludes. Do NOT create a new test module or a second completion authority. SIBLING COORDINATION (F-6, and read F-10 before relying on it): Order 1 (`wlxkoz`) also claims `tests/test_run_evidence_completion.py` and `run_evidence.py`, so do not execute this child concurrently with it; re-read both files immediately before editing. THAT SERIALIZATION IS NOT MACHINE-ENFORCED - measured, the Set coordinator admits these two children into the same parallel wave (`conflicts=0`) because it compiles the manifest with no ownership declarations - so if you are running under `aw ipd execute-set`, VERIFY by inspection that Order 1 is not in flight rather than assuming the scheduler prevented it. COORDINATION, inherited (F-7): APPROVED `0soncw` also claims that test file and is rewriting the command strings its assertions invoke; re-measure it (`git log --oneline -- <file>`) before editing and report rather than merging blind if it has landed changes. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt). Do NOT edit a sibling plan.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at, from the PRIMARY checkout. The load-bearing evidence is V-03's TWO SABOTAGES: the label-invariance test must be observed FAILING against a deliberately relabeling implementation, AND the not-all-verified test must be observed FAILING against an implementation that gives a neutral item the same contribution as a verified one. Those are the two defects this plan can realistically ship, and each is invisible to the other's test. Do NOT describe the flag as available to operators: neither it nor its precondition exists as a CLI surface when this plan completes, and the Scope check says so. Do NOT claim `aw check plans` passes; the bar is no-worsening against your own fresh baseline.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Several sessions commit to this checkout CONCURRENTLY: run `git diff --cached --name-only` before every commit and unstage anything you did not modify with `git restore --staged <path>`, and re-run that check after any failed commit attempt, since a hook failure invalidates it. Prefer `aw commit <plan> -- <paths>`.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
