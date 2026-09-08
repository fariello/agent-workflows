# IPD: Decide whether spec requirements get machine-readable tracking, by measuring the corpus and costing the retrofit before building anything

- Date: 2026-09-08
- Kind: child
- Concern: Nothing in this repository can answer "which requirements of an approved spec are still unbuilt?" A spec is visible only as a WHOLE artifact: `aw attention` maps `approved` to `ready` and `implementing` to `active` (`attention_contract.py:262-272`), so an `approved` spec does appear, but there is no way to say "6 of 9 requirements are built". So a spec can sit half-built for weeks with nothing asking which half. Measured: spec `c4gd2h` has been `implementing` for 9 days with ONE workflow-history line, carries `- Blocks-Release: next`, and holds 23 `- R<n>.` requirement bullets that nothing parses.
  THE THREE GAPS ARE REAL AND I VERIFIED EACH. (1) NO PER-REQUIREMENT MODEL: `agent_workflows/specs.py` is 1066 lines and grepping it for `requirement|R[0-9]|partial` yields exactly two incidental hits (`:1048`, `:1063`), both about evidence-artifact resolution; `validate_spec` (`:211-326`) checks status, gate fields, history, priority and work-kind, and nothing else; there is no requirement-level counterpart to `From-Backlog`/`From-Spec`, both of which are whole-artifact id6 links. (2) NO PARTIAL STATE: the canonical enum `SPEC_STATUSES` (`attention_contract.py:241-253`) has nine values and none expresses partial coverage. (3) `implemented` IS NOT SEMANTICALLY VERIFIED, which the code states about itself at `attention_contract.py:453-463`: `aw specs` enforces "presence + format + resolvability, NOT semantic verification that the work truly happened".
  THIS IS AN OPEN QUESTION AND THE MAINTAINER EXPLICITLY DID NOT COMMIT TO IT: "I'm not sure if having a spec is sufficient, since we're not really going back to them for 'hey, what's in the specs that we still need to address'. Maybe that should be a thing? Definitely not sure." So this plan DECIDES; it does not build a tracking mechanism. Writing an implementation plan for an undecided design would be inventing the maintainer's answer.
  THE DECISIVE COST FINDING, which the item does not have and which is why measuring must precede deciding: THERE IS NO SINGLE PARSABLE REQUIREMENT CONVENTION. I surveyed all 28 specs mechanically and found SIX incompatible id conventions in use plus prose-only specs, and THIRTEEN of the 28 have no machine-parsable requirement id at all. So this is not "add a parser"; it is a corpus-wide authoring project. That is the strongest available input to the item's own cost/benefit question and it points at a cheaper answer than the full mechanism.
- Scope: Answer the item's five open questions with measured evidence and produce a written recommendation the maintainer can accept or reject, covering: whether requirement tracking should exist at all, and if so the minimum viable form (a convention plus an `aw check` rule, versus a parsed model plus an attention view), the retrofit cost per spec, and whether `implemented` should be computed from coverage. Deliverables are a research record with the corpus measurement and a recommendation section in this plan. EXCLUDES implementing any requirement parser, any new spec status, any new front-matter field, any `aw check` rule, any change to `aw attention`, and any edit to a spec's requirement text. Nothing in `agent_workflows/` changes.
- Scope-Paths: .aw/records/research
- Item-Dependencies: none
- Status: to-review
- Set: specreq
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: si24ia
- From-Backlog: f1sw71

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `f1sw71`. The item carries no `- Blocks-Release:` so none is inherited or invented.
  DELIBERATELY A DECISION PLAN, NOT AN IMPLEMENTATION PLAN, and that is the single most important thing about it. The item is an OPEN QUESTION filed at the maintainer's request with an explicit non-commitment, and it ends with five questions that must be answered "before any implementation". A plan that built a requirement model would be answering those five questions on the maintainer's behalf, on a feature whose own author said "definitely not sure", and would add authoring burden to every future spec on an agent's guess. So the deliverable here is a measurement and a recommendation.
  EVERY FACTUAL CLAIM IN THE ITEM VERIFIED TRUE, with two stale numbers corrected. `specs.py` is now 1066 lines, not 1006, and its two incidental `requirement` hits moved from `:988,:1003` to `:1048,:1063`. The corpus is now 28 specs, not 27, with 6 `approved` rather than 5 (re-counted by parsing `^- Status:` across `.aw/records/specs/*.spec.md`, and cross-checked against `aw next --format json`). Every structural claim held: the `_SPEC_MAP` mapping, the nine-value `SPEC_STATUSES` enum with no partial value, `APPROVAL_FLOOR`'s own admission that `implemented` is not semantically verified, and `check.from-spec-dangling` (`check_engine.py:123-125`) validating only that an id6 resolves.
  THE FINDING THAT CHANGES THE ANSWER, and I measured it rather than assuming a convention existed. I counted requirement-id forms across all 28 specs with one grep per convention. Result: `- G<n> \`[Must]\`` in 7 specs, `- R<n>.` in 1 (that one holding 23 ids), `- R<n> (MUST)` in 3, `- **R-<n>**` in 2, `| I-<n> |` table rows in 1, and dotted `R<n>.<n>` sub-ids in 1 (`7ckptx`, whose own history treats `R3.3a-1` as a parent id whose halves are cited separately). THIRTEEN of 28 specs match NONE of these and state requirements in bare prose `MUST`, including `25kzda`, the release-gating run spec. So a parser cannot be pointed at the corpus: 13 specs would need ids INVENTED from prose and several need convention reconciliation. That reframes the item's cost/benefit question from "is 27 specs enough to justify a parser" to "is the retrofit worth it, and is there a cheaper 80 percent".
  THE ITEM'S OWN EVIDENCE GOT STRONGER WHILE I CHECKED IT. Its example of one spec section in three implementation states (`25kzda` 2.1's retry budget) is verified live: the range check is WIRED (`run_recovery.validate_retry_budget` called from `runner_shared.py`), while `plan_retry` and `retry_budget_remaining` have ZERO production callers and the module says so about itself. And item `trjfyy`, which tracks that, had to CORRECT one of its own filed claims on re-verification, which is itself an instance of the drift this item is about.
  NOTHING COVERS THIS AND SIX PENDING PLANS SAY SO EXPLICITLY. `rnkqrc`, `m867ox`, `y9s4vm`, `jxxec8`, `iuxtjy` and `st5klo` each name `f1sw71` and exclude it as out of scope; two record it as a numbered finding. No plan carries `- From-Backlog: f1sw71`. So the item is live, unclaimed, and known to be a real gap by adjacent work.

## Goal

Give the maintainer a decision-ready answer to "should spec requirements be tracked machine-readably, and if so in what minimum form?", grounded in a measured survey of the 28-spec corpus and an honest retrofit cost, so the answer is chosen rather than defaulted into by whoever writes the next plan.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure the corpus, because the decision turns on the retrofit cost

- [ ] E-01 SURVEY EVERY SPEC'S REQUIREMENT CONVENTION AND RECORD THE PER-SPEC RETROFIT COST, one row per spec.
  THIS IS THE LOAD-BEARING ITEM. The item's cost/benefit question cannot be answered without knowing how many specs would need requirement ids INVENTED versus merely parsed. My survey found six incompatible conventions plus 13 prose-only specs, but a survey that decides a policy must be reproducible, so record the exact commands and per-spec results rather than a summary.
  CLASSIFY EACH SPEC INTO ONE OF THREE COSTS, since that is what the decision needs: PARSABLE AS-IS (has consistent machine-readable ids), NEEDS RECONCILIATION (has ids in a convention that differs from whatever is chosen, or mixes two), or NEEDS IDS INVENTED (prose `MUST` only, so a human must decide what the discrete requirements even are). The third class is the expensive one and its count is the decisive number.
  COUNT THE REQUIREMENTS, NOT ONLY THE SPECS. A spec with 47 dotted sub-ids and a spec with 4 are not equal retrofit work. Report a total requirement count for the parsable set so the eventual view's size is known.
  NOTE THE SPECS WITH NO `- Id:` AT ALL, which I found while counting: the oldest live `approved` spec plus both `deferred` specs carry no id6, so they are unreachable by id6 selector. Any join key design must confront that, and it is easy to miss.
  DO NOT NORMALIZE OR EDIT ANY SPEC while surveying. This item reads; it changes nothing. Rewriting a requirement list to fit a convention would be implementing the undecided design.
  - Depends on: none
  - Expected outcome: a per-spec table of convention, requirement count, and retrofit class, with reproducible commands; the count of specs needing ids invented stated as the decisive cost number; specs lacking an `- Id:` flagged.
  - Execution state: pending

- [ ] E-02 MEASURE THE HARM THAT TRACKING WOULD ACTUALLY HAVE PREVENTED, using the corpus's own history rather than argument.
  A FEATURE THAT ADDS AUTHORING BURDEN TO EVERY SPEC NEEDS EVIDENCE OF AVERTED HARM, not just a plausible gap. Look for cases where a partially-implemented spec caused real waste: an agent re-implementing a shipped requirement, a plan blocked while confirming which half of a spec was live, or an `implemented` spec with an unbuilt requirement.
  THREE CANDIDATE CASES ARE ALREADY IDENTIFIED and should be checked rather than rediscovered. First, `c4gd2h`: `implementing` for 9 days, `- Blocks-Release: next`, 23 requirement bullets, one history line; the item states this uncertainty was hit directly while filing `1m3nul`, which had to caution its implementer to verify which stop levels existed before documenting them. Second, `25kzda` 2.1's retry budget: one bullet whose range check shipped, whose two spending helpers have zero production callers, and whose consumption does not exist, i.e. three implementation states in ONE requirement (see `trjfyy`, and plan `xipfy1`). Third, the two `deferred` specs untouched since 2026-08-08.
  LOOK FOR THE STRONGEST DISCONFIRMING CASE TOO, and report it. If the corpus shows that whole-artifact status has been SUFFICIENT in practice, that is the answer and it must not be buried: the honest outcome of this plan may be "do not build this". A survey that can only conclude yes is not a survey.
  QUANTIFY WHERE POSSIBLE. "An agent spent a turn confirming which requirements shipped" is a cost; "this feels risky" is not.
  - Depends on: none
  - Expected outcome: the concrete cases where per-requirement tracking would have prevented measurable waste, each cited to an artifact or commit, plus the strongest case that it would NOT have helped; a plain statement of which way the evidence points.
  - Execution state: pending

### Task group 2: cost the options honestly, including doing nothing

- [ ] E-03 SPECIFY THE THREE VIABLE OPTIONS AT EQUAL DETAIL, so they can be compared rather than one being a straw man.
  THE OPTIONS, each to be costed against E-01's numbers: (A) DO NOTHING, keeping whole-artifact status and relying on backlog items and plans to carry known gaps, which is what happens today and demonstrably works for `trjfyy`. (B) A CONVENTION PLUS A CHECK RULE: pick one requirement-id form, document it for NEW specs only, and add an `aw check` rule that a spec's requirements are well formed, with no attention view and no computed status. (C) THE FULL MECHANISM: parsed requirement ids, a plan-side declaration of which requirements it implements, validated as resolvable, a "requirements outstanding" view in `aw attention`, and `implemented` computed from coverage.
  COST OPTION A AT THE SAME DETAIL AS THE OTHERS. It is the incumbent and the item's own dependency note observes that routing obligations to backlog items and plans "works today". A comparison that treats doing nothing as a non-option is rigged.
  FOR EACH OPTION STATE: authoring burden per new spec, retrofit burden using E-01's three classes, which of the item's three gaps it actually closes, what it would have caught in E-02's cases, and its failure mode when someone does not follow it. The last is what usually decides: a convention nobody follows is worse than no convention because it produces false confidence.
  ANSWER THE ITEM'S FIVE QUESTIONS EXPLICITLY, one at a time, since they are the item's actual ask: do requirements get stable ids and are they parsed; does a plan declare which requirements it implements and is that validated; does `aw attention` gain a view or is it only an `aw check` rule; is `implemented` computed from coverage; and is the corpus large enough to justify it.
  NOTE WHERE EACH OPTION WOULD TOUCH, without touching it: the enum lives at `attention_contract.py:241-253` and is pinned by `tests/test_attention_contract.py`'s totality tests, so a new status is a contract change; a check rule would register beside `check.from-spec-dangling` (`check_engine.py:123-125`); a new `aw specs` subcommand would be a sibling of `check` (`cli.py:4383`). Say so, and change none of them.
  - Depends on: E-01, E-02
  - Expected outcome: three options specified at equal detail, each costed against the measured retrofit classes, each mapped to the gaps it closes and the E-02 cases it would have caught, each with its failure mode; the item's five questions answered explicitly.
  - Execution state: pending

- [ ] E-04 STATE A RECOMMENDATION WITH ITS REASONING AND ITS STRONGEST COUNTERARGUMENT, and make clear the decision is the maintainer's.
  RECOMMEND ONE OPTION PLAINLY. A survey that ends "here are three options, you decide" hands back the same undecided question the item already contains and wastes the measurement.
  INCLUDE THE STRONGEST ARGUMENT AGAINST THE RECOMMENDATION, sourced from the evidence rather than invented for balance. If E-01 shows 13 specs need ids invented, that is a real argument against option C regardless of its benefits.
  BE EXPLICIT THAT THE CHOICE IS THE MAINTAINER'S. This is a cost/benefit and authoring-burden judgment on a feature its requester was openly unsure about, which makes it exactly the class of decision an agent must not settle. Recommend; do not decide.
  IF THE RECOMMENDATION IS "DO NOTHING", SAY SO WITHOUT HEDGING. That is a legitimate and possibly correct outcome, and the item should then be closed as decided rather than left open forever.
  - Depends on: E-03
  - Expected outcome: one recommended option stated plainly, its reasoning tied to E-01 and E-02 evidence, its strongest counterargument stated, and an explicit statement that the maintainer decides.
  - Execution state: pending

### Task group 3: make the work durable

- [ ] E-05 IMMORTALIZE THE SURVEY AS A RESEARCH RECORD, because a decision input that lives only in a plan body is lost once the plan is filed under `executed/`.
  USE THE TOOLING, NEVER HAND-NAME. `aw research new` derives the conforming name and starter front matter and is dry-run by default; `aw research index --apply` maintains the manifest. Hand-naming a research file or hand-editing the index is explicitly forbidden.
  THE RECORD MUST CONTAIN THE REPRODUCIBLE MEASUREMENT, not just conclusions: the exact commands, the per-spec table, and the date and HEAD measured at. A corpus survey dates immediately, and a future reader needs to know whether to re-run it or trust it.
  NOTE THAT NO RESEARCH RECORD ON THIS TOPIC EXISTS. I checked: the only near-hit discusses per-requirement disposition in a worker/verifier RUN protocol, which is a different subject. So this is a genuine addition rather than a duplicate.
  DO NOT DROP ANYTHING INTO `.aw/inbox/`, which is a gitignored raw-drop zone for external material and is not a records tree.
  - Depends on: E-04
  - Expected outcome: a research record created through `aw research new` with the reproducible per-spec survey, the harm cases, the option comparison and the recommendation, plus the manifest refreshed through `aw research index`; no hand-named file and no hand-edited index.
  - Execution state: pending

## Project conventions discovered (Step 0)

- SIX INCOMPATIBLE REQUIREMENT CONVENTIONS EXIST AND 13 OF 28 SPECS HAVE NONE. Measured per convention: `- G<n> \`[Must]\`` (7 specs), `- R<n>.` (1 spec, 23 ids), `- R<n> (MUST)` (3), `- **R-<n>**` (2), `| I-<n> |` (1, 15 ids), dotted `R<n>.<n>` (1). This is the plan's central fact.
- THE SPEC STATUS ENUM IS A PINNED CONTRACT. `SPEC_STATUSES` (`attention_contract.py:241-253`) is nine values, deliberately single-defined "so the coverage test diffs one symbol per tree", and `tests/test_attention_contract.py` asserts totality. Adding a status is a contract change, not a code tweak.
- THE CODE ALREADY ADMITS GAP 3 IN WRITING. `APPROVAL_FLOOR` (`attention_contract.py:453-463`) states `aw specs` enforces "presence + format + resolvability, NOT semantic verification that the work truly happened". Quote it rather than re-deriving it.
- `From-Backlog` AND `From-Spec` ARE WHOLE-ARTIFACT LINKS. `check.from-spec-dangling` (`check_engine.py:123-125`) is a literal id6 set-membership test. There is no requirement-level join key, and that absence is exactly gap 1.
- SIX PENDING PLANS ALREADY EXCLUDE THIS ITEM BY ID (`rnkqrc`, `m867ox`, `y9s4vm`, `jxxec8`, `iuxtjy`, `st5klo`). Consume their reasoning; do not re-derive it.
- THE `specdirs` SET IS A COLLISION RISK FOR ANY FUTURE IMPLEMENTATION, not for this plan: `1bdxcp` declares `agent_workflows/specs.py` and `.aw/records/specs` in its scope and moves specs into status subdirectories. Another reason to decide before building.
- RESEARCH RECORDS ARE TOOL-MANAGED. `aw research new` and `aw research index` own naming and the manifest; hand-naming is forbidden.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses). This plan changes no code, so its own suite expectation is a NO-DELTA run.

## Findings

| Id | Severity | Location (measured at HEAD `fac69fbd`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `.aw/records/specs/*.spec.md` (28 files) | NO SINGLE PARSABLE REQUIREMENT CONVENTION EXISTS. Six incompatible id forms are in use and 13 of 28 specs match none, stating requirements as bare prose `MUST`, including `25kzda`, the release-gating run spec. A parser cannot simply be pointed at the corpus. | one grep per convention across all 28 specs |
| F-2 | N/A | `attention_contract.py:262-272` | SPECS ARE VISIBLE AT WHOLE-ARTIFACT LEVEL: `_SPEC_MAP` maps `approved` to `ready` and `implementing` to `active`, so a spec awaiting implementation does surface. The gap is granularity, not visibility. | source read |
| F-3 | N/A | `attention_contract.py:241-253` | NO PARTIAL-IMPLEMENTATION STATE. `SPEC_STATUSES` is nine values and none expresses "6 of 9 requirements built". Pinned by `tests/test_attention_contract.py` totality tests, so any addition is a contract change. | source read |
| F-4 | N/A | `agent_workflows/specs.py` (1066 lines), `validate_spec:211-326` | NO REQUIREMENT MODEL. Grepping for `requirement|R[0-9]|partial` yields two incidental hits (`:1048`, `:1063`), both about evidence resolution; `validate_spec` checks status, gate, history, priority, work-kind and nothing else. Corrects the item's stale 1006-line and `:988,:1003` citations. | grep, source read |
| F-5 | N/A | `attention_contract.py:453-463`, `check_engine.py:123-125` | `implemented` IS NOT SEMANTICALLY VERIFIED, and the code says so about itself; `check.from-spec-dangling` validates only that an id6 resolves to a spec, never that requirements are covered. | source read |
| F-6 | MED | spec `c4gd2h` | THE SHARPEST CASE IS LIVE: `implementing` since 2026-08-30 with ONE history line, `- Blocks-Release: next`, and 23 `- R<n>.` requirement bullets that nothing parses. Its uncertainty was hit directly while filing `1m3nul`. | spec read; that item's text |
| F-7 | MED | `25kzda` 2.1, `run_recovery.py` | ONE REQUIREMENT IN THREE IMPLEMENTATION STATES, verified by symbol: `validate_retry_budget` is CALLED from `runner_shared.py`, while `plan_retry` and `retry_budget_remaining` have zero production callers (the module documents itself as DORMANT) and the consumption does not exist. Tracked by `trjfyy` -> plan `xipfy1`. | source read; call-site grep |
| F-8 | MED | corpus tally | THE ITEM'S MEASUREMENT IS STALE BUT ITS CONCLUSION HOLDS: 28 specs now, not 27, with 6 `approved` not 5; 12 specs are non-terminal. The item's "9 in ready/active" is still right. | parsed `^- Status:`; cross-checked with `aw next --format json` |
| F-9 | MED | 3 specs | THREE LIVE SPECS CARRY NO `- Id:` AT ALL (the oldest `approved` one and both `deferred` ones), so they are unreachable by id6 selector. Any requirement join key must handle this and the item does not mention it. | front-matter read |
| F-10 | N/A | six pending plans | NOTHING COVERS THIS AND ADJACENT WORK KNOWS IT: `rnkqrc`, `m867ox`, `y9s4vm`, `jxxec8`, `iuxtjy` and `st5klo` each name `f1sw71` and exclude it, two as numbered findings. No plan carries `- From-Backlog: f1sw71`. | grep across pending plans |
| F-11 | LOW | `.aw/records/research/` | NO RESEARCH RECORD ON THIS TOPIC EXISTS. The only near-hit discusses per-requirement disposition in a worker/verifier run protocol, a different subject. So E-05 adds rather than duplicates. | grep across 63 research entries |
| F-12 | LOW | `aw specs --help` | NO HOST FOR A REQUIREMENTS VIEW: the subcommands are `new`, `set`, `note`, `check`, `migrate`. A view would be a new subcommand, a sibling of `check`. | ran `--help` |

## Proposed changes (ordered, validatable)

1. E-01 surveys all 28 specs, classifying each into parsable-as-is, needs-reconciliation, or needs-ids-invented, with requirement counts and reproducible commands.
2. E-02 measures the harm per-requirement tracking would actually have prevented, including the strongest disconfirming case.
3. E-03 specifies three options (do nothing, convention plus check rule, full mechanism) at equal detail and answers the item's five questions explicitly.
4. E-04 states one recommendation with its reasoning and strongest counterargument, and that the maintainer decides.
5. E-05 immortalizes the survey as a research record through `aw research new` and refreshes the manifest.

## Deferred / out of scope (with reason)

- IMPLEMENTING ANY REQUIREMENT MODEL, PARSER, STATUS, FIELD, CHECK RULE OR ATTENTION VIEW. The whole point: the item is an open question whose author said "definitely not sure", and it lists five things that must be decided "before any implementation". Building any of it here would answer those five questions on the maintainer's behalf and impose authoring burden on every future spec from an agent's guess.
- EDITING ANY SPEC'S REQUIREMENT TEXT, including retrofitting ids or normalizing conventions. That IS the retrofit whose cost this plan measures. Doing it while measuring it would be implementing the undecided option.
- ADDING A SPEC STATUS FOR PARTIAL IMPLEMENTATION. `SPEC_STATUSES` (`attention_contract.py:241-253`) is a pinned single-defined contract with totality tests. It may be an outcome of the decision; it is not a step in making it.
- MAKING `implemented` COMPUTED FROM COVERAGE. Question 4 of the item's five. Answered in E-03, not built.
- THE `specdirs` REORGANIZATION. Independent work (`wfjsp4`, `y4bdoz`, `1bdxcp`) that moves specs into status subdirectories and declares `specs.py` in scope. Untouched here, and noted as a collision risk for any FUTURE implementation.
- FIXING THE THREE SPECS WITH NO `- Id:` (F-9). A real defect for id6 selectors and worth its own item, but not this plan's concern; flagged for the maintainer rather than swept in.

## Scope check

- Over-scope: none. The only declared path is `.aw/records/research`, written by E-05. E-01 through E-04 are analysis whose output lands in that record and in this plan's own body.
- Under-scope: stated rather than left as `none`. Deliberately, NOTHING in `agent_workflows/` changes and no spec is edited, so after this plan the three gaps still exist exactly as described. That is the intended end state: the deliverable is a decision, not a mechanism. If the maintainer accepts a recommendation other than "do nothing", the implementation is a SEPARATE plan and this one must not be read as having delivered it.

## Required tests / validation

THIS PLAN CHANGES NO CODE, so the primary validation is EVIDENCE QUALITY, not a green suite. Each `V-*` demands the measurement be reproducible: pasted commands with their actual output, not summaries. Still run `python3 -m pytest` bare in the executing worktree and show a NO-DELTA result against the worktree baseline, comparing failing node ids, since a plan claiming to change no code must prove it. Run `aw specs check` (expected: all specs conform) so the survey's premise that the corpus is structurally valid is stated rather than assumed, and `aw research index --check` after E-05 to prove the manifest is consistent. Any count in the deliverable must be reproducible by a pasted command; a number I cannot re-derive is not evidence.

## Spec / documentation sync

NO SPEC IS AMENDED AND NONE MAY BE. This plan decides whether a mechanism should exist; it changes no behavior any spec describes, and it must not edit a spec's requirement text even to make it parsable (that is the retrofit being costed). That is the justification to record.
THE DECISION'S CONSEQUENCE FOR SPEC AUTHORING IS THE POINT, and if the maintainer accepts option B or C, the FOLLOW-ON plan will need to amend whichever spec governs spec authoring, declaring that file in its `- Scope-Paths:` so the runners announce the edit at run start. Identify that spec in the recommendation so the follow-on does not have to rediscover it, and note whether the requirement-id convention would belong there or in `.aw/records/specs/README.md`.
DO NOT EDIT `.aw/records/specs/README.md` HERE either: documenting a convention is implementing option B.

## Open questions

### OQ-01: Should this plan recommend, or only present options?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as RECOMMEND, with the decision explicitly left to the maintainer. Presenting three costed options and stopping would hand back the same undecided question the item already contains, wasting the measurement: the maintainer's stated difficulty is not a lack of options but not knowing whether it is worth it. A recommendation with its strongest counterargument is more useful and still leaves the choice open, which is the line an agent must respect on a cost/benefit and authoring-burden judgment.

### OQ-02: If the recommendation is a convention, does it apply retroactively?

- Blocking: no
- Status: open
- Owner: the maintainer for the scope call, this plan's executor for the recommendation
- Resolution or deferral rationale: NOT blocking, because E-01 measures the retrofit cost either way and E-03 must cost both variants. It is recorded because it is where the cost is concentrated: F-1 shows 13 of 28 specs would need requirement ids INVENTED from prose, which is human judgment about what a spec's discrete requirements even are, not mechanical work. A going-forward-only convention is nearly free but leaves the existing 12 non-terminal specs (including release-gating `25kzda` and `c4gd2h`) outside the mechanism, which is exactly where the item's motivating pain is. That tension is the real decision and the recommendation should confront it rather than split the difference silently.

### OQ-03: Should the three specs with no `- Id:` be fixed as part of any requirement work?

- Blocking: no
- Status: open
- Owner: the maintainer
- Resolution or deferral rationale: NOT blocking and deliberately not fixed here. F-9: three live specs (the oldest `approved` one and both `deferred` ones) carry no `- Id:`, so they cannot be named by id6 selector, which means any requirement join key keyed on `<spec-id6>.<req-id>` cannot reference their requirements at all. That is a real prerequisite for option C and a small standalone defect worth its own item regardless of this decision. Flagged rather than swept in, because pre-cutover legacy spec names are grandfathered and minting ids for them is a records change the maintainer should authorize.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the per-spec table covering ALL specs in the tree, with each spec's convention, requirement count, and retrofit class. Paste the exact commands used, with their raw output, so a reader can re-derive the counts; a summary without commands is not evidence. State the total spec count and the count in each of the three retrofit classes, and confirm the three counts sum to the total. Paste the list of specs carrying no `- Id:`. Confirm by `git status` that no spec file was modified.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for each harm case, paste the artifact or commit evidence, not a description: for `c4gd2h` its `- Status:`, its history lines and its requirement count; for `25kzda` 2.1 the call-site grep showing `validate_retry_budget` called and `plan_retry`/`retry_budget_remaining` with zero production callers. Paste the strongest DISCONFIRMING case with its evidence. State plainly which way the evidence points, including if it points at "do nothing".
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the three options at equal detail, each with authoring burden, retrofit burden expressed in E-01's classes, which of the three gaps it closes, which E-02 cases it would have caught, and its failure mode. Paste the item's five questions each with its explicit answer. Confirm option A (do nothing) is costed at the same detail as B and C. Confirm by `git status` that nothing in `agent_workflows/` was modified.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the recommendation, its reasoning tied to specific E-01 and E-02 evidence, and its strongest counterargument. Paste the explicit statement that the maintainer decides. If the recommendation is "do nothing", confirm it is stated without hedging and say what should then happen to backlog `f1sw71`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `aw research new` invocation and the path it derived, proving the file was tool-named rather than hand-named. Paste the record's measurement section showing the reproducible commands and the HEAD and date measured at. Paste `aw research index --check` (or the apply plus a check) showing the manifest consistent. Paste `python3 -m pytest` bare with the worktree baseline beside it and a node-id comparison showing NO DELTA. Paste `aw specs check`. Paste `git diff --cached --name-only` showing only research-tree paths and this plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY `.aw/records/research` (plus this plan's own file). Do NOT modify anything in `agent_workflows/`. Do NOT edit any spec, including adding requirement ids or normalizing a convention: that is the retrofit being costed, not a step in costing it. Do NOT add a spec status, a front-matter field, an `aw check` rule, an `aw specs` subcommand, or an `aw attention` view. Do NOT edit `.aw/records/specs/README.md`. Do NOT touch the `specdirs` Set's files. Do NOT hand-name the research file or hand-edit its index; use `aw research new` and `aw research index`. Do NOT drop anything into `.aw/inbox/`. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN, and RE-MEASURE THE CORPUS rather than reusing my counts. Find `SPEC_STATUSES`, `_SPEC_MAP`, `APPROVAL_FLOOR`, `validate_spec` and `check_from_spec_dangling` by name. The spec count and status tally WILL have moved: they moved between the item's filing and this plan (27 to 28 specs, 5 to 6 approved), so treat every number here as a datum to reproduce, not to cite.

THIS PLAN'S OUTPUT IS A RECOMMENDATION, NOT A DECISION. The maintainer chooses. Do not write an approval or readiness attestation for the design, and do not treat a recommendation as license to start implementing it in a later E-item.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved si24ia --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, backlog `f1sw71` (carried as `- From-Backlog:`) should be set according to the outcome: `done` if the recommendation is "do nothing" and the maintainer accepts it, since the open question is then answered and closed; `graduated` if the maintainer accepts a mechanism, because the implementation is then a separate plan and the item's substance survives. Do NOT close it `done` on the strength of a recommendation the maintainer has not accepted. That item carries no release gate, so none is inherited.
