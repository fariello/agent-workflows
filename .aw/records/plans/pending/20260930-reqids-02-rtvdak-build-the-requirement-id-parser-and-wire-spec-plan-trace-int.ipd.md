# IPD: Build the requirement-ID parser and wire SPEC-PLAN-TRACE into spec production

- Date: 2026-09-30
- Kind: child
- Concern: `SPEC-PLAN-TRACE` is declared in approved spec `25kzda` 4.8 with a fixed pass criterion, message template and `RETRY, then FAIL ITEM` Action, and it is the ONLY code in that row with zero enforcement: its three siblings ship as `production_checks.spec_plan_count`, `spec_plan_conformance` and `spec_plan_gate_carry`. Spec `z7nbn1` 4.4 deferred it to backlog `vy20et` for want of a requirement-ID convention, and additionally binds the repository to the negative claim that "a produced plan MUST NOT be described as trace-verified" until it exists. Order 01 (`jjh4aj`) supplies the convention as an approved spec; this plan is the code that makes the check real, and without it the convention is a document nothing enforces and `z7nbn1`'s deferral never discharges.
- Scope: IN: (a) a requirement-ID parser reading a spec's declared requirement ids and acceptance-criterion ids per the convention Order 01's spec defines, with the declaration-site rule honored so a MENTIONED id is not counted as a DECLARED one; (b) `production_checks.spec_plan_trace`, a sibling of the three shipped verifiers, returning the same `[(code, subject, message)]` shape and rendering `25kzda` 4.8's message template; (c) its call at the spec-production site in `runner_shared` beside the existing three `findings.extend` calls; (d) the cutover feature key registered in `config.KNOWN_FEATURE_CUTOVERS` so grandfathering is stamped per repository, not hardcoded; (e) behavioral tests in the style of `tests/test_spec_production.py`, including the grandfathered-spec and no-ids PASS cases. OUT: retrofitting any existing spec's requirement ids; a corpus-wide `aw check` rule; a requirements-outstanding `aw attention` view; a partial spec status; a plan-side requirement declaration field; `implemented` computed from coverage; and any edit to `25kzda` unless Order 01's spec decided AMEND, in which case the amendment is carried by whatever plan that spec names and not silently here.
- Scope-Paths: agent_workflows/production_checks.py, agent_workflows/config.py, agent_workflows/runner_shared.py, tests/test_spec_production.py, tests/test_production_checks_trace.py, .aw/records/plans/pending/20260930-reqids-02-rtvdak-build-the-requirement-id-parser-and-wire-spec-plan-trace-int.ipd.md
- Item-Dependencies: executed:jjh4aj
- Status: to-review
- From-Spec: 25kzda
- Work-Kind: feature
- Priority: medium
- From-Backlog: vy20et
- Set: reqids
- Order: 2
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: rtvdak

## Workflow history
- 2026-09-30 same-status (aw set): status unchanged (to-review)

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored review-ready while graduating backlog `vy20et`. Landing sites measured at HEAD `764442f7`: `production_checks.py` (621 lines, three sibling verifiers), the `findings.extend` call site in `runner_shared`, `config.KNOWN_FEATURE_CUTOVERS` (six registered features), and `ipd_lint.ParsedDoc`/`Leaf` for the plan-side E/V items. Gated `executed:jjh4aj` because the convention it parses does not exist until that spec is approved.

## Goal

Make `SPEC-PLAN-TRACE` a real, deterministic check: parse the producing spec's requirement and
acceptance ids, compare them against the produced plans' `E-*` and `V-*` items, and refuse production
when a mandatory requirement or an acceptance criterion is uncited, using the message and Action
`25kzda` 4.8 already specifies. Close `z7nbn1` 4.4's deferral, and describe the result as what it is:
a CITATION check, never a proof of implementation.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-establish the contract and the landing sites

- [ ] E-01 READ ORDER 01's APPROVED SPEC AND EXTRACT THE CONTRACT THIS PLAN IMPLEMENTS, rather than building from this plan's expectations of it. That spec is the authority for five things and each changes the code: the requirement namespace and the families it admits, the DISTINCT acceptance namespace, the declaration-site rule (what makes an id DECLARED rather than MENTIONED), the mandatory-requirement rule (Order 01 recommends "every declared id is mandatory unless marked optional" but the maintainer ratifies at spec approval and may have chosen the `[Must]` marker or a spec-declared set instead), and the grandfathered/no-ids behavior. CONFIRM THE SPEC IS ACTUALLY `approved`: if it is not, STOP AND REPORT, because an unapproved convention is not a contract and `- Item-Dependencies: executed:jjh4aj` guarantees only that the AUTHORING plan executed, not that the human approved its output. RECORD each of the five decisions verbatim; every later item cites this record instead of re-deriving intent.
  - Depends on: none
  - Expected outcome: the five decisions quoted from the approved spec, with its id6 and path, and its `- Status:` confirmed `approved`. If any of the five is absent or ambiguous, that is reported as a blocker rather than filled in by this plan's judgement.
  - Execution state: pending

- [ ] E-02 RE-MEASURE THE FOUR LANDING SITES at execution HEAD, because `runner_shared.py` is this repository's highest-churn file and every position below will have moved. Locate by SYMBOL or content string, never by a bare offset: (i) `production_checks.py`'s three sibling verifiers `spec_plan_count`, `spec_plan_conformance`, `spec_plan_gate_carry`, recording their exact signature shape and return type, which the new verifier must match; (ii) the spec-production call site, locatable by the content string `spec-production-out-of-scope-paths` and then the consecutive `findings.extend(` calls, recording what is in scope there (the produced plan paths, the spec id6, `host_name`, the run id); (iii) `config.KNOWN_FEATURE_CUTOVERS` and the next free feature key, plus `resolve_cutover_date`'s lookup order; (iv) `ipd_lint`'s `ParsedDoc.exec_leaves` / `valid_leaves` of `Leaf`, confirming `Leaf` still carries `kind`, `ident` and `text`, which is how the plan-side ids are read WITHOUT writing a second plan parser. If any has moved or changed shape, record the new one; if (iv) no longer exposes E/V idents, STOP AND REPORT rather than hand-rolling a plan parser.
  - Depends on: none
  - Expected outcome: the four sites recorded by symbol/content-string with their current shape, and an explicit statement that the new verifier will match the sibling signature and reuse `ipd_lint`'s plan parser rather than adding a second one.
  - Execution state: pending

### Task group 2: the parser

- [ ] E-03 IMPLEMENT THE SPEC-SIDE REQUIREMENT-ID PARSER as a pure function in `production_checks.py`, returning the producing spec's DECLARED requirement ids and DECLARED acceptance ids as two separate sets, per E-01's recorded convention. Honor the declaration-site rule so a CITATION is not counted as a DECLARATION: this is the difference between a check that works and one that silently passes, because a spec citing another spec's `R-12` must not acquire an `R-12` requirement of its own. Keep it PURE (text in, ids out, no filesystem access) so it is testable without a repository fixture, matching the style of the pure helpers already in this module. Do NOT parse a plan here: the plan side is `ipd_lint`'s job (E-02 item iv).
  - Depends on: E-01, E-02
  - Expected outcome: a pure parser function that, given spec text, returns the declared requirement id set and the declared acceptance id set, counting declarations only.
  - Execution state: pending

- [ ] E-04 UNIT-TEST THE PARSER ON REAL CORPUS SHAPES, not on invented ones, because the corpus's variety is the whole reason this convention exists. Cover at minimum: a letter-prefixed spec with a distinct acceptance namespace (`7ckptx` shape: `R<n>.<n>` requirements with `A<n>` acceptance ids), an `AC-`prefixed acceptance spec (`6m4kow` shape), a bare dotted-paragraph spec (`z7nbn1` shape, 37 dotted ids and no letter-prefixed ones), a section-addressed spec with no requirement ids at all (`25kzda` shape), and a spec with NO acceptance section (`77tr3o` shape). Assert on the returned SETS, and include the negative case that gives the declaration-site rule its teeth: text CITING an id must not yield it as declared. These are outcome assertions on a function's return value, not structural assertions about source text.
  - Depends on: E-03
  - Expected outcome: a new test module covering the five corpus shapes plus the citation-vs-declaration negative case, all passing, asserting on returned id sets.
  - Execution state: pending

### Task group 3: the check and its wiring

- [ ] E-05 IMPLEMENT `spec_plan_trace` as a sibling verifier, matching the three shipped ones in signature shape and returning the same `[(code, subject, message)]` list. It reads the producing spec's ids via E-03's parser and each produced plan's `E-*`/`V-*` item text via `ipd_lint`, then applies `25kzda` 4.8's pass criterion: every MANDATORY requirement maps to at least one E item and every acceptance criterion to at least one V item. RENDER `25kzda` 4.8's message template rather than inventing wording, as the three siblings did (each quotes its pass criterion under "Pass criterion (25kzda 4.8):" in its docstring): `[SPEC-PLAN-TRACE] Generated IPD <plan-id> does not cover spec items: <ids>. Correct and sync the IPD, then: aw <host> run resume <run-id>`. IMPLEMENT THE PASS CASES E-01 recorded: a spec that is grandfathered against the stamped cutover, or that declares no ids at all, PASSES rather than failing, or the check would refuse production for specs nobody agreed to retrofit. Also handle the honest asymmetry: a spec with no acceptance section cannot fail the acceptance half.
  - Depends on: E-03, E-01
  - Expected outcome: `production_checks.spec_plan_trace` exists, matches the sibling signature, renders the `25kzda` 4.8 template, and passes (rather than fails) for a grandfathered spec, a spec with no declared ids, and the acceptance half of a spec with no acceptance section.
  - Execution state: pending

- [ ] E-06 REGISTER THE CUTOVER FEATURE KEY in `config.KNOWN_FEATURE_CUTOVERS` with the value E-01 recorded from the approved spec, and follow that registry's own instruction rather than adding a second mechanism: its block comment reads "TO ADD A FEATURE: put its introduction date here, and let `sync_cutovers_on_install` stamp the per-repo boundary. Do not invent a second mechanism; three shipped features use this one." The value is the FEATURE INTRODUCTION date, never the enforcement boundary. STATE THE FAILURE MODE THIS AVOIDS, which the registry's existing entries each record: without the entry, `resolve_cutover_date` falls through to `None` in any repository that has not hand-written the key, grandfathering resolves for every spec forever, and the check ships as decoration.
  - Depends on: E-01
  - Expected outcome: the feature key is registered with the introduction date from the approved spec, and `resolve_cutover_date` returns a non-`None` boundary for it in this repository.
  - Execution state: pending

- [ ] E-07 WIRE THE CHECK INTO THE SPEC-PRODUCTION SITE, adding one `findings.extend(_pc.spec_plan_trace(...))` beside the existing three at the location E-02 measured, passing the same `target_tree`, spec id6, produced paths, `host` and run id the siblings receive. CHANGE NOTHING ELSE about the refusal path: the existing code already maps any finding to `fail-gate`, prints each, records a refusal per finding and preserves the lane, so TRACE inherits `25kzda` 4.8's `RETRY, then FAIL ITEM` Action from machinery that is already there. Do NOT reorder, rename or alter the three existing calls, and do NOT add a second refusal mechanism.
  - Depends on: E-05, E-02
  - Expected outcome: the production site calls four verifiers instead of three, with the new call receiving the same arguments as its siblings and no change to the surrounding refusal, printing or lane-preservation logic.
  - Execution state: pending

- [ ] E-08 TEST THE WIRED CHECK END-TO-END IN BOTH DIRECTIONS, in the style `tests/test_spec_production.py` already uses for the three siblings (a fake agent turn producing plans into a temp repo, then asserting on the run's disposition). Prove: (i) a produced plan that cites every mandatory requirement and every acceptance criterion PASSES production; (ii) a produced plan that omits one mandatory requirement FAILS with the `SPEC-PLAN-TRACE` code, the omitted id named in the message, and the lane preserved; (iii) a grandfathered producing spec PASSES even with an uncovered requirement, proving the grandfathering is live and not merely written; and (iv) the three existing codes still behave exactly as before, so this wiring regressed nothing. Assert on real dispositions and message content, never on source structure. FINALLY, record the honest limit in the code where a future reader will meet it: the check proves a plan CITES a requirement, not that it implements it.
  - Depends on: E-07, E-06
  - Expected outcome: four behavioral tests passing, covering pass, fail-with-named-id, grandfathered-pass, and no-regression of the three sibling codes; and the citation-not-implementation limit recorded in the verifier's docstring.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE VERIFIER SHAPE IS ALREADY SET BY THREE SIBLINGS. `production_checks.py` verifiers take `(repo, <source>_id6, ...)` plus keyword-only `host` and sometimes `run_id`, and return `list[tuple[str, str, str]]` of `(code, subject, message)`. Its module docstring states the contract: "Each verifier returns a list of findings `[(code, plan_or_source_id6, message)]` rendered from the 25kzda 4.8 message templates." The new verifier conforms rather than inventing a shape.
- THE MESSAGE TEMPLATES ARE QUOTED FROM `25kzda` 4.8, NOT PARAPHRASED. Each shipped verifier's docstring carries its pass criterion under "Pass criterion (25kzda 4.8):" and its message f-string matches the spec's template. E-05 follows this.
- THE REFUSAL PATH IS SHARED AND NEEDS NO NEW CODE. At the production site, any non-empty `findings` sets `disposition = "fail-gate"`, prints each finding, calls `record_refusal` per finding and calls `lane_containment.record_lane_preserved`. A fourth verifier inherits all of it by returning findings in the same shape.
- THE CUTOVER REGISTRY IS SINGULAR AND SAYS SO IN ITS OWN COMMENT. `config.KNOWN_FEATURE_CUTOVERS` holds the FEATURE INTRODUCTION date; `sync_cutovers_on_install` stamps the per-repo boundary; `resolve_cutover_date` reads `.aw/config/project.json` `cutovers.<feature>` first. Six features are registered (`spec_id6`, `dependency_schema`, `carrier_obligations`, `setid_length`, `prompt_id6`, `walkthrough_id6`), and this repository's stamped `cutovers` block carries five of them.
- THE PLAN SIDE IS ALREADY PARSED; DO NOT WRITE A SECOND PARSER. `ipd_lint` yields a `ParsedDoc` with `exec_leaves` and `valid_leaves` of `Leaf`, each carrying `kind` ("E"/"V"), `ident` (e.g. "E-01"), `text`, and for V rows a `target`. `production_checks.py` already imports `ipd_lint as _lint` and calls `_lint.lint_file`, so the dependency exists.
- TESTS ASSERT OUTCOMES, NOT CODE STRUCTURE. The repository forbids tests that read production source with `inspect`/`ast`/regex, assert caller counts or symbol censuses, or pin docstring text (GUIDING_PRINCIPLES P16). E-04 and E-08 are written as return-value and disposition assertions for that reason.
- THE SUITE IS RUN BARE. `python3 -m pytest`, because `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Authoring baseline at HEAD `764442f7`: `3387 passed, 2 skipped, 3 warnings in 137.99s`.

## Findings

| Id | What was measured | Evidence | Why it matters here |
|---|---|---|---|
| F-01 | TRACE is the ONLY unbuilt code in its row, and its landing module exists | `production_checks.py` implements the three siblings and its docstring names exactly those three as in scope from "spec 25kzda 4.8 / z7nbn1 4.4". Executed plan `aeq7f8` V-09 recorded `grep -rn 'SPEC-PLAN-TRACE' agent_workflows/` empty (exit 1). | The work is an addition to a live, tested module, not new infrastructure. It also means the deferred code was not half-built, so there is no partial implementation to reconcile. |
| F-02 | The produced plan paths are IN HAND where TRACE must run | At the production site, `runner_shared` discovers newly produced plans by diffing `_ce._iter_plan_ipds(target_tree)` against `baseline_plan_ids` into `new_produced_paths`, then passes that list to `spec_plan_conformance` and `spec_plan_gate_carry`. | This is the hinge of the whole Set. Research `vkub9o` concluded "The blocker is the missing plan-to-spec edge, not the missing requirement parser", having measured 0 plans carrying `- From-Spec: c4gd2h`. That objection does NOT reach this check, because the dispatcher computed the plan set itself moments earlier. |
| F-03 | TRACE judges only specs reaching `ACTION_PLAN`, which is `approved` alone | `run_selection_policy._SPEC_ACTIONS` maps `"approved": ACTION_PLAN` with the comment "author conformant IPDs linked by From-Spec"; `implemented`/`deferred`/`parked`/`superseded` map to `ACTION_SKIP`, and `draft`, `to-review`, `reviewed` and `implementing` are deliberately absent. | The corpus-wide retrofit `vkub9o` costed is not in scope. Measured at HEAD `764442f7`, 10 of 12 `approved` specs already declare requirement ids and 7 declare acceptance ids, so the judged population is the best-addressed subset. |
| F-04 | The acceptance half is structurally weaker than the requirement half | Over the 12 `approved` specs: 5 use `AC`/`A`-prefixed acceptance ids (`7ckptx` 36, `6kwd2e` 49, `uonrjg` 25, `w15vzb` 12, `6m4kow` 11), 5 have an acceptance section with no ids on its lines, and 2 (`25kzda`, `77tr3o`) have no acceptance section at all. | E-05 must make the no-acceptance-section case a PASS. Without that, TRACE would refuse production for two `approved` specs on a criterion they never adopted. |
| F-05 | "Mandatory" has no marker in general use | `[Must]` appears in 10 of 38 specs and in only 2 of 12 `approved` ones (`2vev8j`, `5tapom`). Most specs express obligation in prose `MUST`. | E-01 must read the ratified rule off the approved spec rather than choosing. Order 01 recommends "every declared id is mandatory unless marked optional" precisely because the marker-based reading is measurably vacuous on the judged population. |
| F-06 | The plan-side E/V parse needs no new code | `ipd_lint.Leaf` carries `kind`, `ident`, `text`, `target`; `ParsedDoc` carries `exec_leaves` and `valid_leaves`; `production_checks.py` already imports `ipd_lint as _lint`. | Writing a second plan parser would be the drift this repository repeatedly warns about. E-02 item (iv) makes reuse a checked precondition rather than an intention. |
| F-07 | The grandfathering mechanism is stamped, not hardcoded, and omitting the key fails OPEN | `config.KNOWN_FEATURE_CUTOVERS`'s comment: "Do not invent a second mechanism; three shipped features use this one." Its `prompt_id6` and `walkthrough_id6` entries each record the same failure mode in their own comments: without the entry `resolve_cutover_date` "falls through to its tier-3 `None`". | E-06 exists as a separate item because forgetting it does not break a test loudly; it silently grandfathers every spec forever and the check becomes decoration. |
| F-08 | Five pending plans already declare a `25kzda` edit, so this plan must not add a sixth | Measured at HEAD `764442f7`: pending plans `00pirb`, `cpi6p3`, `mt54wr`, `6uhtko` and `4gx141` declare `25kzda` edits. | This plan's `- Scope-Paths:` deliberately excludes every `.spec.md`. If Order 01's spec decided AMEND, the amendment belongs to the plan that spec names, not to a silent edit here. |
| F-09 | `runner_shared.py` is the highest-churn file in the repository | Repository instructions and multiple pending plans record it; `agent_workflows/production_checks.py` was 621 lines at authoring and `agent_workflows/specs.py` moved from 1097 lines (measured by `vkub9o` on 2026-09-20) to 1319 at HEAD `764442f7`, a 20 percent growth in ten days. | Every position in this plan is given by symbol or content string, and E-02 re-measures before any edit. A plan of this shape that trusted authoring offsets would not apply. |
| F-10 | Dependency on Order 01 is on the SPEC's APPROVAL, which an `executed:` edge cannot express | The grammar offers `executed:`/`exists:`/`state:` edges over plans. `jjh4aj` reaching `executed` proves the spec was AUTHORED and moved to `to-review`; it cannot prove a human approved it, and `aw spec set approved --by-human` is the only route to that. | `- Item-Dependencies: executed:jjh4aj` is necessary but NOT sufficient, which is why E-01 makes "confirm the spec is `approved`, else STOP AND REPORT" its own explicit precondition rather than an assumption. |

## Proposed changes (ordered, validatable)

1. Read the five ratified decisions off Order 01's approved spec and confirm it is `approved` (E-01); re-measure the four landing sites (E-02).
2. Implement the pure spec-side requirement/acceptance id parser honoring the declaration-site rule (E-03) and unit-test it against five real corpus shapes plus the citation-vs-declaration negative (E-04).
3. Implement `spec_plan_trace` as a fourth sibling verifier rendering `25kzda` 4.8's template, with the grandfathered, no-ids and no-acceptance-section PASS cases (E-05).
4. Register the cutover feature key so grandfathering is stamped per repository (E-06).
5. Wire one `findings.extend` call at the production site, changing nothing else about the refusal path (E-07).
6. Prove the wired check in four directions and record the citation-not-implementation limit in the code (E-08).

## Deferred / out of scope (with reason)

- RETROFITTING ANY EXISTING SPEC's REQUIREMENT IDS.
  - Carrier-Declined: SETTLED POLICY, not deferred work. Order 01's spec sets the policy as going-forward with per-spec grandfathering, and `vkub9o` Q5 recommends against retrofitting; performing it would edit approved specs' requirement text, which this plan is forbidden to do. The grandfathering registered by E-06 is what makes the non-retrofitted specs permanently valid, so nothing is left outstanding.
- A CORPUS-WIDE `aw check` RULE ON REQUIREMENT IDS.
  - Carrier-Declined: REJECTED OPTION, with the cost measured. `vkub9o` Option B records the unavoidable dilemma: a rule over a non-conforming corpus must either exempt specs (proving little) or fail closed and block unrelated work, and a `warning` in `aw check` exits nonzero here, which would red every run and teach readers to ignore it. This check fires only at production, where the plans are in hand. `vkub9o` is the durable record should the maintainer revisit it.
- A REQUIREMENTS-OUTSTANDING `aw attention` VIEW, A PARTIAL SPEC STATUS, A PLAN-SIDE REQUIREMENT DECLARATION FIELD, AND `implemented` COMPUTED FROM COVERAGE.
  - Carrier-Declined: REJECTED OPTION (`vkub9o` Option C), on costs this plan does not disturb: a `SPEC_STATUSES` change is pinned by totality tests, and an `implemented` computed from plan-side declarations inverts `APPROVAL_FLOOR`'s stated refusal to verify semantically. A costed and rejected option is not an outstanding obligation; `vkub9o` holds the analysis.
- AMENDING `25kzda` 4.8.
  - Carrier-Declined: NOT THIS PLAN'S DECISION AND NOT OUTSTANDING WORK. Order 01's spec decides adopt-or-amend (its E-07); this plan ADOPTS the template and declares no `.spec.md` in `- Scope-Paths:`. If that spec chose AMEND, it names the carrying plan and that plan owns the edit, which E-01 reads and records. Five pending plans already queue `25kzda` edits (F-08), so a silent sixth here is exactly what must not happen.
- THE OTHER NINE UNBUILT `SPEC-*` CODES AND THE `implementing`-SPEC CHILD DISPATCH.
  - Carrier-Declined: OWNED ELSEWHERE BY AN APPROVED CONTRACT. `z7nbn1` 4.4 lists them explicitly as NOT IN SCOPE and leaves them with approved spec `25kzda` 4.8, which is a durable record revisited whenever that spec is. They are not this Set's obligation and were never in `vy20et`'s scope.

## Scope check

- Over-scope: none. Two production modules gain one function and one registry entry, one gains a single call, and two test modules are added or extended. `- Scope-Paths:` names `tests/test_spec_production.py` because E-08's sibling-regression case belongs beside the existing three codes' tests, and a new `tests/test_production_checks_trace.py` for E-04's pure-parser unit tests.
- Under-scope: TRACE will judge only specs dispatched through the production action, so a spec whose plans were authored by hand is never checked. That is deliberate and is the scoping that makes the check buildable at all (F-02, F-03); the broader corpus question is `vkub9o` Option C and is out of scope. Also under-scope by design: the check proves CITATION, not implementation, so a plan can satisfy TRACE by naming a requirement in an E item that does not implement it. E-08 requires that limit be written where a reader meets it.

## Required tests / validation

TWO TEST SURFACES, both asserting on OUTCOMES rather than code structure (GUIDING_PRINCIPLES P16: no
`inspect`/`ast`/regex reads of production source, no caller counts, no docstring pins). FIRST, pure
unit tests for the parser (E-04) over five real corpus shapes plus the citation-vs-declaration
negative, asserting on returned id sets. SECOND, end-to-end production tests (E-08) in the style
`tests/test_spec_production.py` already uses for the three siblings, driving a fake agent turn in a
temp repo and asserting on the run's real disposition and message content: pass, fail with the omitted
id named and the lane preserved, grandfathered-pass, and no regression of the three existing codes.
The bare suite (`python3 -m pytest`) is run before and after, with the after-minus-before failing
node-ID set required to be EMPTY against the authoring baseline `3387 passed, 2 skipped` at HEAD
`764442f7`; that baseline is re-established at execution rather than trusted, since this plan waits on
Order 01 and on a human approval.

## Spec / documentation sync

NO `.spec.md` IS EDITED BY THIS PLAN, and `- Scope-Paths:` is written to make that checkable. Three
relationships are nevertheless discharged in code and in this plan's record. (1) `25kzda` 4.8's TRACE
row is ADOPTED verbatim in the verifier's message and docstring, matching how the three siblings quote
their pass criteria; if Order 01's approved spec chose AMEND instead, E-01 records that and the
amendment belongs to the plan that spec names (F-08), not here. (2) `z7nbn1` 4.4 deferred TRACE and
states that until it exists "a produced plan MUST NOT be described as trace-verified"; this plan is
what discharges the deferral, so E-08's evidence is what a later editor of `z7nbn1` will cite. (3)
Research `vkub9o` recommended against building a parser; the reconciliation (its objection was the
missing join edge, which F-02 shows does not apply here) is recorded in Order 01's spec and restated in
F-02 so a reader of this plan alone is not misled into thinking the survey was ignored.

## Open questions

### OQ-01: If the maintainer ratified the `[Must]`-marker reading, is TRACE worth shipping at all?

- Blocking: no
- Status: resolved
- Owner: maintainer (already answerable at Order 01's spec approval)
- Resolution or deferral rationale: measured (F-05), `[Must]` appears in only 2 of the 12 `approved` specs TRACE can judge, so under a marker-based mandatory rule the requirement half would be vacuous for 10 of 12 and the check would pass by default on almost everything. Order 01 therefore recommends "every declared id is mandatory unless marked optional". RESOLVED for this plan's purposes: E-01 READS the ratified rule and implements it as approved, whatever it is, so this plan is correct under all three options and needs no re-authoring. NOT BLOCKING for that reason. But the consequence is recorded honestly so it is not discovered later: if the marker reading was ratified, this plan still ships a working check whose requirement half is largely inert on today's corpus, and the right response is a follow-up backlog item proposing the optional-marker opt-out, NOT a silent widening of the rule inside this plan. An executor who finds that situation should report it rather than reinterpret the spec.

### OQ-02: Does TRACE run when a produced plan is an ORCHESTRATOR, whose items are child-tracking rows rather than deliverables?

- Blocking: no
- Status: resolved
- Owner: none (settled from repository evidence)
- Resolution or deferral rationale: a spec production action may write a Set, and an Order-0 orchestrator's checklist rows are TYPED CHILD-TRACKING ROWS of the fixed form `- [ ] E-NN CONFIRM <child-id6> REACHED <status>` (`ipd_lint._ORCH_ROW_RE`), which by construction cite no requirement. Applying TRACE per-plan would therefore fail every Set that has an orchestrator, for a structural reason unrelated to coverage. RESOLVED: evaluate coverage across the produced plan SET collectively (a requirement cited by any produced plan is covered) rather than demanding every plan cover every requirement, and treat an orchestrator's child-tracking rows as contributing nothing rather than as a violation. This follows the repository's own statement that an orchestrator "holds orchestration, not work of its own", and it is consistent with `SPEC-PLAN-COUNT`'s existing set-level reading ("at least one new IPD links to the spec"). Recorded here rather than left implicit because a per-plan reading is the more obvious implementation and is wrong; E-05 and E-08 must implement and prove the set-level one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the approved spec's path, `- Id:` and `- Status:` line showing `approved`, plus the verbatim quotes of all five ratified decisions (requirement namespace and families, acceptance namespace, declaration-site rule, mandatory rule, grandfathered/no-ids behavior). If the spec is not `approved`, paste its actual status and confirm the plan STOPPED rather than proceeding.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for each of the four sites, paste what was found and how it was located (symbol or quoted content string, no bare offsets): the three sibling signatures from `production_checks.py`; the `findings.extend` block and the lines computing the produced plan list at the production site; the `KNOWN_FEATURE_CUTOVERS` entries with the chosen next free key; and the `Leaf`/`ParsedDoc` field list proving `kind`/`ident`/`text` are still exposed. State explicitly that the new verifier will match the sibling signature and reuse `ipd_lint`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the parser function's signature and docstring, then paste a Python session (or test output) calling it on two real spec texts from the tree and printing the two returned sets, showing requirement and acceptance ids separated. Confirm by demonstration that it performs no filesystem access (text in, sets out).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new test module's node IDs and the `python3 -m pytest <module>` output showing all pass. Confirm each of the five corpus shapes is covered by naming the test that covers it and the real spec it is modelled on, and paste the citation-vs-declaration negative test's body showing it asserts a CITED id is NOT returned as declared. Confirm no test reads production source with `inspect`/`ast`/regex.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `spec_plan_trace`'s signature, docstring (showing the `25kzda` 4.8 pass criterion quoted as the siblings do) and its message f-string, and confirm the rendered text matches `25kzda` 4.8's template `[SPEC-PLAN-TRACE] Generated IPD <plan-id> does not cover spec items: <ids>. Correct and sync the IPD, then: aw <host> run resume <run-id>`. Paste test output proving the three PASS cases return an empty finding list: grandfathered spec, spec with no declared ids, and the acceptance half for a spec with no acceptance section.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `KNOWN_FEATURE_CUTOVERS` diff showing the new key and its introduction date, confirm the date matches what E-01 recorded from the approved spec, and paste a call to `resolve_cutover_date` for that feature in this repository showing a non-`None` boundary. State in one sentence the failure mode avoided (fall-through to `None`, grandfathering everything forever).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the diff at the production call site showing exactly one added `findings.extend(...)` call and no other change, then paste the surrounding refusal block unchanged (the `fail-gate` assignment, the per-finding print, `record_refusal`, `record_lane_preserved`). Confirm the new call receives the same `target_tree`, spec id6, produced paths, host and run id as its siblings, and that the three existing calls were not reordered or altered.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the four end-to-end tests' node IDs and output: (i) full-coverage production PASSES; (ii) a plan omitting one mandatory requirement FAILS with disposition `fail-gate`, the `SPEC-PLAN-TRACE` code and the omitted id present in the message, and the lane preserved; (iii) a grandfathered producing spec PASSES despite an uncovered requirement; (iv) the three sibling codes' existing tests still pass. Paste the ORCHESTRATOR case proving OQ-02's set-level reading: a produced Set containing an Order-0 orchestrator does NOT fail merely because its child-tracking rows cite no requirement. Then paste the bare `python3 -m pytest` summary line BEFORE and AFTER with the after-minus-before failing node-ID set (must be EMPTY), and quote the citation-not-implementation limit from the verifier's docstring.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. `SPEC-PLAN-TRACE` becomes a real gate. After this, running an `approved`
spec as a production action checks that the plans it just wrote actually CITE the spec's requirements
and acceptance criteria, and REFUSES the item (preserving the lane) when they do not, using the message
and `RETRY, then FAIL ITEM` Action `25kzda` 4.8 already specifies. A spec predating the stamped cutover,
or declaring no ids, PASSES rather than failing, so nothing is retroactively broken.

WHAT IT DOES NOT BUY, STATED PLAINLY BECAUSE THE NAME OVERSELLS IT. This is a CITATION check. It proves
a plan names a requirement; it cannot prove the plan implements it. A plan can satisfy TRACE with an E
item that mentions `R-04` and does nothing about it. Plan review remains the real coverage check, and
E-08 requires this limit be written into the code where a future reader meets it rather than living only
here.

DO NOT EXECUTE BEFORE ORDER 01's SPEC IS APPROVED, AND THE DEPENDENCY EDGE IS NOT SUFFICIENT TO ENSURE
THAT. `- Item-Dependencies: executed:jjh4aj` guarantees the spec was AUTHORED and handed to review; it
cannot express "and a human approved it", because the grammar has no such edge (F-10). The whole content
of this plan is determined by five decisions that only the approved spec fixes, so E-01 makes the
approval an explicit checked precondition and requires STOP AND REPORT if it is missing. An agent
executing this Set by hand must honor the same order; the runner will mark this item
`dependency-blocked` if `jjh4aj` has not executed, but it cannot detect an unapproved spec for you.

THE REVIEWER'S SHARPEST QUESTION, NAMED RATHER THAN AVOIDED. In-tree research `vkub9o` explicitly
recommends "Do NOT build: a requirement parser". This plan builds one. The reconciliation is F-02: the
survey's decisive objection was a MISSING JOIN EDGE, measured as 0 plans carrying `- From-Spec:` for the
spec it studied, and that objection does not reach a check running inside the production dispatcher,
which computed the produced plan list itself moments before. If a reviewer rejects that reconciliation,
this plan should not execute, and the right correction is to Order 01's spec rather than to this code.

EXECUTION CONTRACT. Commit only the paths named in `- Scope-Paths:` through `aw commit <plan> -- <paths>`;
never `git add -A`, never `-a`, never `--no-verify`, never push. Do not edit any `.spec.md`. Do not
change the three existing verifiers or the shared refusal path. Do not write structure-pinning tests
(no `inspect`/`ast`/regex over production source, no caller counts, no docstring pins). Run the suite
BARE (`python3 -m pytest`) and paste real output in every `V-*`; a validation item without observed
evidence is not verified. Do not edit backlog `vy20et`'s requirements and do not set it `done`.

POST-GATE LIFECYCLE MOVE. When every `E-*` is performed and every `V-*` carries pasted evidence, run
`aw ipd lint --phase pre-transition` and confirm it reports conforming, then move this plan to
`.aw/records/plans/executed/` through the tooled transition (`aw ipd finalize` / the runner's
self-finalize), never by hand-editing the status or `git mv`-ing the file.
