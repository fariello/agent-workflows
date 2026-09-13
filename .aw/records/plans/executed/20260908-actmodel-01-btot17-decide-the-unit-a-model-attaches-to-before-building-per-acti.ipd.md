# IPD: Decide the unit a model attaches to before building per action model selection

- Date: 2026-09-08
- Kind: child
- Concern: THE RUNNER RESOLVES ONE MODEL IDENTITY PER RUN FOR EVERY ACTION EXCEPT THE VERIFIER, WHICH NOW HAS ITS OWN. That exception is the fact this plan turns on, and it was already true when the plan was authored. `resolve_launch_profile` (`oc_runipd.py:2613`, located BY SYMBOL) resolves one launch identity for the whole run, so an arbitrary action such as the orchestrator probe still has nowhere to declare a model preference. But `kgpptv` (`runprofile-06`) is `- Status: executed` and its `verify_with` field HAS SHIPPED, so the repository already contains a working per-role model preference with a documented precedence chain, a schema-version bump, and a fail-closed integrity check.
  THE GREP THAT MOTIVATED THIS ITEM IS A VOCABULARY ARTIFACT, NOT A CAPABILITY GAP. `grep role agent_workflows/runner_profiles.py` is still zero, and that measurement is TRUE and MISLEADING: the shipped mechanism spells the concept `verify_with` rather than `role`. So "no action can choose a cheaper model" is false as written; the accurate statement is that ONE role can, by name, and the mechanism was not generalized.
  THE QUESTION IS THEREFORE THE HARDER ONE THE PLAN'S OWN E-01 ANTICIPATED. E-01 said that if `kgpptv` had executed, "the question changes from 'should a general mechanism subsume it' to 'should a general mechanism absorb a shipped special case', which is a harder and different design problem", and instructed the executor to report rather than proceed. That condition is ALREADY MET, so the re-scope is applied here at review rather than left as a trap for an executor. `verify_with` is not a prototype to discard: it is a public field in a versioned on-disk schema, and generalizing it now means either deprecating a shipped key or layering a second mechanism beside it.
  THE OC-ONLY PREMISE IS STILL TRUE AT THE CODE LEVEL, contrary to this plan's original claim. `tm2cz8` executed and `RUNNER_REGISTRY` does carry an `agy` row, but `runner_profiles`, `resolve_launch_profile` and `launch_profile` STILL grep to ZERO in `agy_runipd.py`. A profile naming `runner: agy` can be written and will resolve, and no agy run reads it. So "any per-action design must be cross-host from the outset" does not follow from the registry row; whether to build cross-host first is a real question, but it is not settled by a fact that is not true.
  THE MOTIVATING CASE IS REAL BUT DELIBERATELY BOUNDED, WHICH IS WHY THIS IS A DECISION AND NOT A BUILD. Plan `m7gvuz` adds a pre-run probe asking a model one yes/no question per queued orchestrator; paying a top-tier rate for that is wasteful. The maintainer's 2026-09-07 ruling was to use the run's already-resolved model and RECORD which model answered with each cached verdict, so a future reader can distrust a weak verdict. `m7gvuz`'s F-10 recorded that an executor reading its OQ-01 as "reuse the per-role resolver" would "find nothing to reuse"; that was accurate WHEN WRITTEN (`kgpptv` was then approved and unexecuted) and is now stale, which is exactly why this plan re-measures rather than inherits. And the cost is bounded: probe verdicts are cached against a content digest, so on a stable corpus the probe costs nothing after its first pass, and the waste scales with how often plans CHANGE, not with how often runs happen.
  SO THE DELIVERABLE IS THE DECISION THE ITEM SAYS IS MISSING, NOT A MECHANISM. The item is explicit: "filed as a BACKLOG ITEM rather than an IPD, because it is a decided-but-unscoped design question, not a task list. It graduates into a plan if and when it earns one." Graduating it as a build plan would invent answers to four questions the maintainer reserved, the largest of which (role versus arbitrary action) determines whether an approved plan should be executed or retired.
- Scope: Produce the recorded design decision per-action model selection needs, with the evidence each choice turns on, and implement ONLY what that decision authorizes. The four questions the item lists are the deliverable's shape, re-framed around the fact that a per-role preference (`verify_with`) has ALREADY SHIPPED. EXPLICITLY EXCLUDES building a routing mechanism before the unit is chosen; excludes editing `kgpptv`'s plan file, which is in `executed/`; and excludes removing, renaming or deprecating `verify_with`, whose disposition E-05 may only RECORD.
- Scope-Paths: agent_workflows/runner_profiles.py, .aw/records/specs, tests/test_runner_profiles.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: actmodel
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: btot17
- From-Backlog: 0k74my

## Workflow history
- 2026-09-13 executed (aw oc run): aw oc run self-finalize: btot17 verified (set actmodel, attempt 1).
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-08 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; PR-901..PR-909 all FIXED. Readiness `go-pending-approval`. RECONCILED WITH THE MAINTAINER'S RULING, which landed mid-review: round 1 concluded `REVIEWED - OPEN QUESTIONS` / `no-go` because OQ-01 was then `Blocking: yes`, and the maintainer's commit `93703697` then RESOLVED it (a validated ROLE enum, built now, EXTENDING `verify_with`) while rejecting this plan's cost-control framing outright in favor of fitness for task, and opened a non-blocking OQ-05 for the producing-plus-validating pair. No blocking question remains, hence the verdict and readiness above. That commit also swept my in-progress review edits into the maintainer's own, leaving the document holding BOTH readings, so this pass resolved the contradictions in favor of the ruling: E-02 re-aimed off the struck extensibility count and cost profile onto mapping the five kinds of work to real call sites, E-05 reduced from three dispositions to the chosen EXTEND path with the action-key and defer options struck and the OQ-05 pair explicitly fenced out, four residual "deferral outcome" references corrected (scope justification, required tests, validation evidence, lifecycle move), V-02 and V-05 re-pointed, and the gate rewritten to announce that no blocking question remains and that the ruling wins wherever this document still reasons from cost. A NEW BOUNDARY IS NOW STATED that the decision framing had hidden: with no driver module in scope, this plan ships the SCHEMA and no consumer, so nothing routes a model until a follow-on plan wires it. Reviewed at HEAD `7e633c74`; `aw ipd lint --phase author` conformed clean before semantic review and `--phase review-finalize` after. THE PLAN'S CENTRAL PREMISE WAS FALSE AT AUTHORING TIME AND THE PLAN ITSELF SPECIFIED THE REMEDY. PR-901 (BLOCKER): `kgpptv` is `- Status: executed`, not "approved and unexecuted" as the Concern, the conventions, F-3, F-4 and OQ-01 all stated, and its `verify_with` field HAS SHIPPED, so a per-role model preference already exists with a documented precedence chain, a `SCHEMA_VERSION` 1 -> 2 bump, and a fail-closed dangling-reference check. The plan's own E-01 said that if `kgpptv` had executed the question "changes from 'should a general mechanism subsume it' to 'should a general mechanism absorb a shipped special case', which is a harder and different design problem", and instructed the executor to report rather than proceed; that condition was already met, so the re-scope is applied here rather than left as a trap. PR-902 (HIGH): the motivating grep is a VOCABULARY artifact; zero `role` occurrences is true and misleading, because the shipped mechanism spells the concept `verify_with`, so "no action can choose a cheaper model" is false as written. PR-903 (HIGH): the oc-only premise is TRUE and the plan says it is false; `tm2cz8` executed and `RUNNER_REGISTRY` carries an `agy` row, but `runner_profiles`/`resolve_launch_profile`/`launch_profile` still grep to ZERO in `agy_runipd.py`, so a registry row is not an integration and "must be cross-host from the start" does not follow. PR-904 (HIGH): OQ-03's resolution CONTRADICTS shipped behavior, since `_validate_verify_reference` refuses a dangling reference at load time for a stated integrity reason; the question is now split into unresolvable-reference (refuse) versus unprovidable-at-launch (warn and fall back). PR-905 (HIGH): E-05 would have added a field beside a shipped public key with no instruction about it, so it now requires an explicit extend/supersede/layer disposition. PR-906: question 4's "concrete substrate" does not exist (`m7gvuz` approved/unexecuted, `8tgg6g` reviewed/unexecuted, the answering-model field a design intent). PR-907: `m7gvuz` is not blocked; all three of its questions read `Blocking: no`/`resolved`. PR-908: the plan's own `resolve_launch_profile` citation was already wrong at authoring (`:2702` inherited from a sibling versus the actual `:2613`) while the plan asserted it had re-verified by symbol. PR-909: the stated baseline `1 failed, 5648 passed` is wrong; measured `1 failed, 5866 passed, 3 skipped, 2 xfailed` with the failure in `test_reporting_contract.py`. All nine FIXED in place; the E-item count is unchanged at five because every repair was a re-aim rather than an addition. Root cause worth recording: the plan inherited sibling measurements as current instead of re-deriving them, which is precisely the discipline its own execution contract preaches.
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `0k74my` as a DECISION plan, which is what the item asks for ("a decided-but-unscoped design question, not a task list"). Every measurement re-verified at HEAD rather than trusted: `runner_profiles` still has ZERO `role` occurrences; `resolve_launch_profile` still resolves one identity per run but has MOVED from the item's cited `:2660` to `:2702`; `kgpptv` still reads `approved` and still sits in `pending/`. ONE PREMISE IS NOW FALSE and changes the design space: the item and `kgpptv` both treat the profile mechanism as opencode-only, but approved `tm2cz8` registers the agy host, and `ybkmzp` explicitly warns that `kgpptv`'s F-12 "child 01 makes false, so its scope should be re-read rather than trusted". So any per-action design must be cross-host from the outset. The item's cost bound was also confirmed as the reason this is non-urgent (verdicts cached against a content digest, so waste scales with plan churn rather than run count), which is why the plan's first two E-items are evidence-gathering and its build items are gated behind a blocking question.

## Goal

Give the repository a recorded answer to what a model preference attaches to, so the next action that wants a cheap model has somewhere to declare it and so an approved plan is either executed or retired on evidence rather than by default.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the live state, since the shipped mechanism is the starting point

- [x] E-01 DOCUMENT THE SHIPPED `verify_with` MECHANISM AS THE BASELINE THE DECISION MUST BUILD ON, reading the code rather than this plan's prose. The re-scope this item originally made conditional is ALREADY TRIGGERED: `kgpptv` is `executed` and `verify_with` is in `ALLOWED_PROFILE_KEYS`, so do not spend the item re-confirming a gap that is partly closed.
  WHAT TO RECORD, each located BY SYMBOL: (a) `verify_with`'s precedence chain as the module docstring states it (`explicit --verify-with > profile's own verify_with > defaults.verify_with > ABSENT`); (b) that it is a PROFILE REFERENCE, not an inline model string, and the stated security reason (an inline model "would fork the one place a launch identity is defined"); (c) that `SCHEMA_VERSION` was BUMPED 1 -> 2 for it while `SUPPORTED_SCHEMA_VERSIONS` reads both, so the backward-compatibility question this plan worries about was already answered once, with `ABSENT` as the compatibility story; (d) that a DANGLING reference is REFUSED AT LOAD TIME by `_validate_verify_reference`, with the reason the code gives; (e) that `resolve_launch_profile` (`oc_runipd.py:2613`) still resolves one identity for every OTHER action.
  ALSO RECORD WHAT IS STILL ABSENT, since that is the actual gap: no mechanism lets an ARBITRARY named action declare a preference, and `runner_profiles`/`resolve_launch_profile`/`launch_profile` still grep to ZERO in `agy_runipd.py`, so the mechanism remains oc-only IN PRACTICE even though `RUNNER_REGISTRY` now carries an `agy` row.
  RE-LOCATE BY SYMBOL, NEVER BY LINE NUMBER. Both runner files are under concurrent edit. This plan's own `:2702` citation for `resolve_launch_profile` was already wrong at authoring (it is `:2613`), which is the concrete demonstration.
  - Depends on: none
  - Expected outcome: a symbol-cited description of the SHIPPED per-role mechanism (chain, reference-not-string, version bump, dangling refusal) plus a statement of what remains absent (arbitrary actions, agy in practice), with every line number re-derived at your HEAD.
  - Execution state: performed

- [x] E-02 MAP THE MAINTAINER'S FIVE KINDS OF WORK ONTO THE CALL SITES THAT WOULD CONSUME THEM. The unit is DECIDED (a role), so this item no longer gathers evidence to choose it; it establishes which seams the role map must actually reach, which is what E-05 needs in order to build something usable rather than a schema field nothing reads.
  BUILD THE LIST FROM THE CODE, not from the vocabulary. At minimum: the executor turn, the verifier turn, the review turn, and the orchestrator probe `m7gvuz` adds. For each, record whether it invokes a model today and which of the maintainer's five kinds of work it performs (write prose, write code, write code fast, research online, check content).
  THE EXTENSIBILITY COUNT IS NO LONGER THE DISCRIMINATOR and must not be presented as one: the maintainer's ruling decided the unit on FITNESS FOR TASK, and E-05's role vocabulary comes from the five stated categories rather than from a historical rate. Note any model-invoking seam that fits NONE of the five, since that is a genuine gap in the vocabulary and is worth reporting rather than silently forcing into a category.
  RECORD WHICH SEAMS THE SHIPPED MECHANISM ALREADY SERVES, since the verifier case must become an entry in the extended map rather than a parallel field: the verifier turn already has `verify_with`, and per `kgpptv`'s review a REVIEW turn is not a separate call site at all (it is the execute call site with `item["action"] == "review"`, read only to pick a `--title` label). Verify that at HEAD, because if review is not a distinct seam then a role preference cannot attach to it without new plumbing, which E-05 must know.
  DROP THE COST FRAMING ENTIRELY. The maintainer rejected it ("It is NOT about just getting a cheap model. It's about getting the best model for the job"), so do NOT record a per-action "cost profile" as the deciding attribute; record FITNESS (what kind of work it is, and what a mismatched model would cost in QUALITY). `m7gvuz` remains `approved` and unexecuted, so its probe is prospective, but the plan no longer depends on it: fitness-for-task applies to every run.
  - Depends on: E-01
  - Expected outcome: a table of model-invoking call sites, each mapped to one of the maintainer's five kinds of work (or flagged as fitting none), marking which are ALREADY served by `verify_with` and which need new plumbing to reach; no cost profile as a deciding attribute.
  - Execution state: performed

### Task group 2: answer the four questions with evidence

- [x] E-03 SET OUT THE PRECEDENCE AND FALLBACK ANSWERS, which are questions 2 and 3. Question 2 is now very nearly SETTLED BY SHIPPED CODE rather than merely precedented, and question 3 has a shipped counter-example that must be confronted head on.
  QUESTION 2 (WHERE THE PREFERENCE IS DECLARED) IS ALREADY ANSWERED ONCE, TWICE OVER: `f2mrsw` established the per-profile `validate` tri-state, and `kgpptv` then applied THE SAME CHAIN to a model preference (`explicit flag > profile's own field > defaults.<field> > ABSENT`). So the recommendation is not "invent a chain following a nearby convention" but "the chain a model preference uses already exists and a third variant would be the defect". State the chain, cite it, and say what if anything a per-action key changes about it (chiefly: the third tier's key shape, since an action map is not a scalar).
  QUESTION 3 (UNPROVIDABLE MODEL) IS WHERE THIS PLAN'S RECOMMENDATION CONFLICTS WITH SHIPPED BEHAVIOR, AND THE CONFLICT MUST BE RESOLVED RATHER THAN GLOSSED. This plan recommends "warn and fall back, do not fail the run". But `_validate_verify_reference` REFUSES a dangling `verify_with` at LOAD TIME, and the code states the reason explicitly: a reference resolving to nothing "would silently fall back to the executor's model, so the operator would believe an independent model verified the work when the same model did. That is worse than a dangling default, because the failure is invisible in the result rather than visible in the bill." Read that reasoning and DISTINGUISH TWO CASES, because they genuinely differ: an UNRESOLVABLE REFERENCE (a name matching no profile, a config error, knowable at load time, currently REFUSED) versus a RESOLVED profile naming a model THE HOST CANNOT PROVIDE AT LAUNCH (knowable only at run time). The plan's warn-and-fall-back argument is defensible for the second and directly contradicts shipped behavior for the first.
  THE SANDBOX CONTRAST IS STILL WORTH STATING but is no longer the only nearby precedent, and it is now the WEAKER one: `select_execution_profile` RAISES because degradation removes a security boundary, whereas `verify_with`'s refusal shows this module already fails closed on a MODEL question for an integrity reason, not a security one. A reader who is only warned about the sandbox analogy will still get question 3 wrong.
  RECORD THE ANSWERS AS RECOMMENDATIONS, NOT AS DECISIONS. They only matter once question 1 is answered, so they are inputs to the maintainer's ruling rather than independent commitments.
  - Depends on: E-02
  - Expected outcome: the declaration-site recommendation citing the chain `kgpptv` already shipped for a model preference; and a fallback recommendation that explicitly SEPARATES the unresolvable-reference case (currently refused at load, with the quoted reason) from the unprovidable-model-at-launch case, saying which behavior it recommends for each and why that does not contradict shipped code.
  - Execution state: performed

- [x] E-04 ANSWER QUESTION 4 (CACHE VALIDITY ACROSS A PREFERENCE CHANGE) FROM THE DATA THAT ALREADY EXISTS, since this is the one question with a concrete substrate.
  THE ITEM POINTS AT IT: "The probe verdict store already records the answering model for exactly this reason, so the data to make that judgment exists." Verify that claim against `m7gvuz`/`8tgg6g`'s design rather than trusting it, since both are unexecuted and the store DOES NOT EXIST YET. Measured at review: `m7gvuz` is `approved` and unexecuted, `8tgg6g` is `reviewed` and unexecuted, and `m7gvuz`'s OQ-01 says child 02 "stores the field for exactly this reason" as a DESIGN INTENT, not as shipped state. So the honest finding is that the substrate is planned, not present, and the plan's "this is the one question with a concrete substrate" framing is wrong in the same direction as its `kgpptv` premise.
  THE QUESTION IS WHETHER A VERDICT PRODUCED UNDER MODEL A STAYS VALID WHEN THE PREFERENCE CHANGES TO MODEL B. State the options plainly: invalidate on model change (safe, expensive, and defeats the caching that makes the probe free), keep and record (cheap, and lets a reader distrust a weak verdict, which is what the maintainer already chose for the probe), or keep only when the new model is stronger (requires a model ranking the repository does not have and probably should not invent).
  NOTE THE MAINTAINER ALREADY RULED ON THE ANALOGOUS CASE. The 2026-09-07 ruling for `m7gvuz` was to use the run's model and RECORD which one answered, so a future reader can distrust the verdict. That is the "keep and record" option, already chosen once, which is strong evidence for the general answer without settling it.
  - Depends on: E-03
  - Expected outcome: the three cache options with their costs, a verification of whether the answering-model record actually exists yet, and a recommendation anchored to the maintainer's existing ruling; no cache behavior changed.
  - Execution state: performed

### Task group 3: implement only what the ruling authorizes

- [x] E-05 IMPLEMENT THE ROLE-TO-MODEL MAPPING BY EXTENDING `verify_with`, per the maintainer's resolution of OQ-01 (2026-09-08). THE "RECORD IT AND BUILD NOTHING YET" OUTCOME IS STRUCK and must not be taken: the maintainer rejected this plan's cost-control framing entirely ("It is NOT about just getting a cheap model. It's about getting the best model for the job") and the deferral was affordable only under that framing, since fitness-for-task applies to every run rather than to one unexecuted probe. Likewise the ARBITRARY ACTION KEY option is struck: the maintainer's categories are kinds of work, so a validated role enum is the unit.
  BUILD THE ROLE VOCABULARY FROM THE MAINTAINER'S OWN EXAMPLES rather than inventing one: write prose, write code, write code fast, research online, check content. Those five are the stated need; the verifier case must become an entry in the same map rather than remaining a parallel field.
  DO NOT BUILD THE PRODUCING-PLUS-VALIDATING PAIR. "Writing code fast? Gemini 3.8 Flash, with Opus 5 validation" needs a role to name TWO models, which nothing today can express; the maintainer explicitly chose to record it as the next step, and OQ-05 owns it. Smuggling it in here would cross `validate` and `verify_with`, which the module docstring says must not be conflated.
  EXTEND, DO NOT SUPERSEDE OR LAYER. The maintainer's ruling already chose the disposition, so this is an instruction rather than a question: the general role map REUSES `verify_with`'s three settled properties (a PROFILE REFERENCE rather than an inline model string, the existing precedence chain, and the load-time refusal of a dangling reference by `_validate_verify_reference`), and the verifier case becomes an ENTRY in that map. Do NOT add a second field beside `verify_with` and leave a reader to work out which wins; the module docstring argues that two switches for one behavior is precisely what the `validate` precedence chain exists to avoid. Do NOT remove or rename `verify_with` in this plan either: extending keeps the key valid, and retiring a shipped schema key is separate compatibility work.
  SCHEMA MECHANICS. `ALLOWED_PROFILE_KEYS` and `_reject_unknown_keys` mean an unknown key is REFUSED, so the field must be DECLARED, not conventional. On versioning, follow the precedent rather than re-deriving it: `SCHEMA_VERSION` is ALREADY 2 and `SUPPORTED_SCHEMA_VERSIONS` reads `{1, 2}`, and `kgpptv` recorded DECISION 06-kgpptv-D2 on exactly this trade (bump so an older aw says "Upgrade aw" rather than "unknown field"), so state whether this field bumps to 3 and why, citing that decision. An existing on-disk config, including one carrying `verify_with`, must still load and resolve unchanged.
  THE ARBITRARY ACTION KEY IS STRUCK, and the reason is worth keeping because it is evidence rather than preference: `verify_with` is deliberately a reference INTO a validated profile map, which is what makes a bad value catchable at load time, whereas an open action key reintroduces exactly the silent-no-op class (a preference for a misspelled action that never applies) that check exists to prevent.
  "DECIDE AND DEFER" IS NO LONGER AVAILABLE, and the reasoning that recommended it is recorded here as SUPERSEDED so nobody restores it: it rested on the cost bound (verdicts cached against a content digest) and on the unserved population being "a single prospective consumer in an unexecuted plan". Both arguments answer a COST question. The maintainer's ruling is a QUALITY question, where every run is a beneficiary and caching is irrelevant. Do not revive this outcome without a new ruling.
  DO NOT EDIT `kgpptv`. It is in `executed/`, and repository rules forbid adding commits to an executed plan; a post-execution gap is closed with a new corrective IPD. Its plan's fate is not a live question (it shipped); what the ruling disposed of is its FIELD, by extension.
  - Depends on: E-04
  - Expected outcome: a validated role enum in `runner_profiles`' per-profile schema covering the maintainer's five stated kinds of work, EXTENDING `verify_with` (not superseding or layering beside it) with the verifier case as an entry in the same map, a stated schema-version decision citing 06-kgpptv-D2, no producing-plus-validating pair, and `kgpptv`'s plan file untouched.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE WORD `role` IS ABSENT BUT THE CAPABILITY IS NOT: zero `role` occurrences in `runner_profiles.py`, yet `verify_with` IS a per-role model preference. A vocabulary grep is not a capability measurement, and treating it as one is how this plan's premise went wrong.
- A PER-ROLE MODEL PREFERENCE HAS SHIPPED: `verify_with` is in `ALLOWED_PROFILE_KEYS` and `ALLOWED_DEFAULTS_KEYS`, with the chain `explicit --verify-with > profile's own verify_with > defaults.verify_with > ABSENT`.
- ONE IDENTITY PER RUN FOR EVERY OTHER ACTION: `resolve_launch_profile` (`oc_runipd.py:2613`, NOT the `:2702` this plan originally cited) resolves a single launch identity for the whole run.
- `kgpptv` IS EXECUTED, so the question is whether to generalize a SHIPPED special case, not whether to subsume a pending plan. Its plan file is in `executed/` and must not be edited.
- THE MECHANISM IS STILL OC-ONLY IN PRACTICE: `tm2cz8` executed and `RUNNER_REGISTRY` carries an `agy` row, but `runner_profiles`, `resolve_launch_profile` and `launch_profile` all grep to ZERO in `agy_runipd.py`. A registry row is not an integration.
- A PRECEDENCE CHAIN FOR A MODEL PREFERENCE ALREADY EXISTS, not merely a nearby precedent: `f2mrsw` set the pattern with `validate` and `kgpptv` applied it to `verify_with`, so a third variant would be the defect.
- THE SCHEMA REFUSES UNKNOWN KEYS (`ALLOWED_PROFILE_KEYS`, `_reject_unknown_keys`) and is VERSIONED at `SCHEMA_VERSION = 2` reading `{1, 2}`, bumped by `kgpptv` under DECISION 06-kgpptv-D2 with the reason recorded in the docstring.
- A MODEL PREFERENCE ALREADY FAILS CLOSED ON ONE CASE: `_validate_verify_reference` REFUSES a dangling reference at load time, because a silent fallback would let an operator believe an independent model verified the work. This is the nearest precedent for question 3 and it points the OPPOSITE way from this plan's original recommendation.
- THE SANDBOX PRECEDENT IS THE WEAKER ANALOGY: `select_execution_profile` RAISES because degradation removes a security boundary. Worth stating, but `verify_with` shows the module already fails closed on a MODEL question for an integrity reason.
- THE MOTIVATING CONSUMER IS PROSPECTIVE BUT NOT BLOCKED: `m7gvuz` is `approved` and unexecuted with all three of its open questions `- Blocking: no` / `resolved`; `8tgg6g` is `reviewed`. The verdict store and its answering-model field do NOT exist yet.
- THE COST IS BOUNDED, which is why this is non-urgent: probe verdicts are cached against a content digest, so waste scales with plan churn, not run count.
- Both runner files are under concurrent edit; re-locate every symbol by name. Suite runs BARE.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the gap is NARROWER than stated | `resolve_launch_profile` resolves one identity per run for every action EXCEPT the verifier, which has `verify_with`. So "no action can choose a cheaper model" is false; one role can, by name. | `oc_runipd.py:2613`; `ALLOWED_PROFILE_KEYS` contains `verify_with` |
| F-2 | HIGH | this plan's OWN citation was stale at authoring | It cites `resolve_launch_profile` at `:2702` (inherited from `m7gvuz`'s round 2) while asserting it re-verified by symbol; it is at `:2613`. The lesson the plan preaches is the one it did not follow. | `grep -n "def resolve_launch_profile"` at HEAD |
| F-3 | BLOCKER | `kgpptv` IS EXECUTED, not approved | The plan states `- Status: approved`, unexecuted, in the Concern, the conventions, F-3, F-4 and OQ-01. It is `executed` and `verify_with` has shipped. Its own E-01 said this condition changes the design problem and requires a re-scope. | `.aw/records/plans/executed/20260905-runprofile-06-kgpptv-...ipd.md:12` |
| F-4 | HIGH | the grep that motivated the item is a VOCABULARY artifact | Zero `role` occurrences is true and misleading: the shipped mechanism spells the concept `verify_with`. A term search cannot establish a capability gap. | `grep -c role agent_workflows/runner_profiles.py` -> 0, alongside F-1 |
| F-5 | HIGH | the OC-ONLY premise is TRUE, and the plan says it is false | The plan claims `tm2cz8` makes the mechanism cross-host, so a per-action design "must be cross-host from the start". `RUNNER_REGISTRY` does carry `agy`, but `runner_profiles`/`resolve_launch_profile`/`launch_profile` grep to ZERO in `agy_runipd.py`. A registry row is not an integration. | `grep -c` over `agy_runipd.py` -> 0; `tm2cz8` `- Status: executed` |
| F-6 | HIGH | question 3's recommendation contradicts SHIPPED behavior | The plan recommends "warn and fall back, never fail the run" for an unprovidable model. `_validate_verify_reference` REFUSES a dangling `verify_with` at load time, because a silent fallback lets an operator believe an independent model verified the work. The two cases (unresolvable reference versus unprovidable model at launch) must be separated. | `runner_profiles._validate_verify_reference` docstring |
| F-7 | HIGH | this is a decision, by the item's own framing | "filed as a BACKLOG ITEM rather than an IPD, because it is a decided-but-unscoped design question, not a task list." Graduating it as a build plan would invent four reserved answers. | the item's opening ruling |
| F-8 | MEDIUM | F-6's inherited claim is STALE, not wrong | `m7gvuz` F-10's "find nothing to reuse" was accurate when written (`kgpptv` was then approved/unexecuted) and is now false. Quoting a sibling's dated measurement as current is the mechanism by which this plan's premise failed. | `m7gvuz` F-10, which itself cites `- Status: approved` |
| F-9 | MEDIUM | the cache substrate does NOT exist yet | The plan calls question 4 "the one question with a concrete substrate". `m7gvuz` is approved/unexecuted and `8tgg6g` is `reviewed`/unexecuted, and the answering-model field is a DESIGN INTENT in `m7gvuz` OQ-01, not shipped state. | both plans' `- Status:` lines |
| F-10 | MEDIUM | `m7gvuz` is NOT blocked | The plan twice says the probe "carries its own blocking questions". All three of its open questions read `- Blocking: no` / `- Status: resolved`. It is approved and merely not yet run. | `m7gvuz` OQ-01..OQ-03 |
| F-11 | MEDIUM | the precedence chain is SHIPPED for a model preference | `f2mrsw` set the pattern with `validate`; `kgpptv` applied the same chain to `verify_with`. Question 2 is not "follow a nearby convention" but "the chain already exists and a third variant is the defect". | `runner_profiles` docstring, the `verify_with` chain |
| F-12 | MEDIUM | the version-bump question was already decided once | `SCHEMA_VERSION` is 2, `SUPPORTED_SCHEMA_VERSIONS` reads `{1, 2}`, bumped by `kgpptv` under DECISION 06-kgpptv-D2 with the reasoning recorded (bump so an older aw says "Upgrade aw" rather than "unknown field"). A new field's versioning should cite that, not re-derive it. | `SCHEMA_VERSION` docstring |
| F-13 | MEDIUM | `verify_with`'s design resists the open-action-key option | It is deliberately a PROFILE REFERENCE, not an inline model string, which is what makes a dangling value catchable. An open action map reintroduces the silent-no-op class that check prevents. | `ALLOWED_PROFILE_KEYS` comment; `parse_profile`'s `verify_with` branch |
| F-14 | MEDIUM | the cost bound makes deferral affordable, and MORE so now | Verdicts are cached against a content digest, so waste scales with plan churn; and one role is already served, so the unserved population is a single prospective consumer. | the item's cost note; F-1 |
| F-15 | LOW | the sandbox precedent is the WEAKER analogy | `select_execution_profile` RAISES because degradation removes a security boundary. Still worth stating, but `verify_with` shows the module already fails closed on a MODEL question for an integrity reason, which is the closer case. | `host_sandbox_profile.select_execution_profile`; F-6 |
| F-16 | LOW | the stated suite baseline is wrong | The plan cites `1 failed, 5648 passed`. Measured at review: `1 failed, 5866 passed, 3 skipped, 2 xfailed`, the failure being `test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` from untracked `opencode-recovery/` files. | pasted summary line |

## Proposed changes (ordered, validatable)

1. Document the SHIPPED `verify_with` mechanism as the baseline, plus what remains genuinely absent (E-01).
2. Map the maintainer's five kinds of work onto the real call sites, marking which `verify_with` already serves and which need new plumbing (E-02).
3. Record the declaration site from the chain `kgpptv` already shipped, and split the fallback question into unresolvable-reference versus unprovidable-at-launch (E-03).
4. Answer the cache-validity question, stating that its substrate is planned rather than present (E-04).
5. Build the validated role enum EXTENDING `verify_with`, per the maintainer's ruling, with no producing-plus-validating pair (E-05).

## Deferred / out of scope (with reason)

- BUILDING A ROUTING MECHANISM BEFORE THE UNIT IS CHOSEN. The item reserved question 1 and it determines the schema shape, the validation strength, and now also the disposition of a SHIPPED public key (`verify_with`). Building first would force that answer by implementation.
- EDITING `kgpptv`'s PLAN FILE. It is in `executed/` and repository rules forbid adding commits to an executed plan; a post-execution gap is closed with a new corrective IPD. Its fate is no longer an open question (F-3), so what OQ-01 decides is the disposition of its FIELD, not of the plan.
- REMOVING, RENAMING OR DEPRECATING `verify_with` IN THIS PLAN. Even under a building outcome, E-05 may only RECORD the extend/supersede/layer disposition; actually retiring a shipped schema key is a separate change with its own compatibility work and belongs to whatever plan implements the general mechanism.
- EXECUTING OR CHANGING `m7gvuz`. It is the prospective consumer, approved and not yet run, with all its open questions resolved (F-10), and the maintainer already ruled how the probe picks a model in the interim (use the run's model, record which answered).
- A MODEL RANKING OR STRENGTH ORDER. Question 4's "keep only when the new model is stronger" option needs one, and inventing a ranking would embed a fast-moving external judgement in durable config. Named as an option and recommended against.
- PER-ACTION ROUTING ON THE AGY HOST specifically. `tm2cz8` added an `agy` REGISTRY ROW, but the host reads no profiles at all (`runner_profiles`, `resolve_launch_profile` and `launch_profile` grep to ZERO in `agy_runipd.py`; F-5), so cross-host routing depends on an integration that does not exist rather than on a missing provenance record alone. This is a correction to this plan's original claim that the mechanism is already cross-host.
- CHANGING THE PROBE'S CACHE BEHAVIOR. `8tgg6g` owns the verdict store; E-04 answers a question ABOUT cache validity without changing it.
- THE `validate` TRI-STATE. `f2mrsw` shipped it and this plan reads it as precedent only. Note the distinction the module insists on: `validate` decides WHETHER a verifier turn runs, `verify_with` decides WHICH profile runs it, and conflating them is called out as a defect in the module docstring.

## Scope check

- Over-scope: none. Under two of three outcomes this plan writes a decision record and at most one optional schema field.
- Scope-Paths justification: `agent_workflows/runner_profiles.py` holds `ALLOWED_PROFILE_KEYS`, `parse_profile`, `_reject_unknown_keys`, `SCHEMA_VERSION` and the shipped `verify_with` machinery, so it is both where the role enum is declared (E-05) and the primary READ target for E-01's baseline description; `.aw/records/specs` is where the decision record lands; `tests/test_runner_profiles.py` is the existing schema suite that must prove an existing on-disk config, including one carrying `verify_with`, still loads. NO driver module is in scope, deliberately: resolving a role into a turn's argv is the NEXT plan's work and both runner files are under concurrent edit. NOTE THE CONSEQUENCE OF THAT FENCE NOW THAT THE RULING MADE THIS A BUILD PLAN: this plan ships the SCHEMA and no consumer, so nothing routes a model until a follow-on plan wires it. That is a deliberate boundary, not an omission, but E-05 must state it so nobody reads a merged role map as working routing. Since the deferral outcome is struck, `runner_profiles.py` and the test file are now EXPECTED to change.
- Under-scope was CLOSED at review on one point: E-01 originally spent its effort re-measuring a gap that shipped code had partly closed, and E-05 had no instruction about the shipped `verify_with` key it would have sat beside. Both are now explicit (F-3, F-13). Otherwise: this plan does not build routing, does not edit `kgpptv`'s plan file or `m7gvuz`, does not retire or rename `verify_with`, does not invent a model ranking, does not build agy's missing profile integration, does not change the probe's cache, and does not touch the `validate` tri-state. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline MEASURED at review on HEAD `7e633c74`: `1 failed, 5866 passed, 3 skipped, 2 xfailed`, the failure being `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` from untracked `opencode-recovery/` files and unrelated to this plan (F-16). Criterion: AFTER minus BEFORE is EMPTY, never an absolute count. Re-baseline in your own tree. The suite is now EXPECTED to grow, since the deferral outcome is struck and E-05 builds.
- THE ACTION INVENTORY (E-02) pasted, with per-action cost profile and quality sensitivity, which actions `verify_with` ALREADY serves, and the measured or explicitly-estimated rate at which new model-invoking actions appear.
- THE SHIPPED-BASELINE DESCRIPTION (E-01) pasted: `verify_with`'s precedence chain, its reference-not-string design, the `SCHEMA_VERSION` 1 -> 2 bump, the dangling-reference refusal, and `resolve_launch_profile`'s location re-derived BY SYMBOL at your HEAD.
- Under a building outcome: proof that an EXISTING on-disk `runner_profiles` config still loads unchanged (the schema is versioned and reads `{1, 2}`), plus a test that an unknown key is still REFUSED so the new field did not loosen validation, plus proof that a document carrying `verify_with` still loads and resolves exactly as before.
- Under a building outcome: a test for EACH of OQ-03's two cases, since they now have opposite expected behaviors: an unresolvable REFERENCE is REFUSED (matching `_validate_verify_reference`), and a resolved profile whose model the host cannot provide WARNS and falls back with the fallback recorded in run state.
- The spec decision record itself, which the maintainer's ruling makes MORE important rather than less: it must record the unit chosen, the EXTEND disposition of `verify_with`, the fitness-for-task rationale that replaced the cost framing, and the pairing requirement OQ-05 still owns.
- NEGATIVE proof that no producing-plus-validating pair was built, since OQ-05 remains the maintainer's open question.
- NEGATIVE PROOF that `kgpptv`'s plan file in `executed/` was not modified, and that `verify_with` was not removed or renamed, under any outcome.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

THE DECISION RECORD IS THE PRIMARY DELIVERABLE and must live in a spec under `.aw/records/specs`, not only in this plan's prose, because the whole point is that the NEXT action wanting a cheap model finds an answer instead of re-deriving this analysis. That is true under all three outcomes, including deferral: "we considered per-action routing and deliberately did not build it, for these reasons" is exactly the kind of decision this repository loses when it lives only in a closed item.

The record must state the unit chosen (or that none was), the declaration site and precedence, the fallback behavior for BOTH of OQ-03's cases WITH the reason they differ, the cache-validity answer, and THE DISPOSITION OF `verify_with` (extend, supersede, or layer). That last one is the load-bearing part for a reader: a shipped schema key's future should be findable from the decision that affects it. Where the original plan promised "the consequence for `kgpptv`", the honest deliverable is the consequence for its FIELD, since the plan itself has executed (F-3).

`tm2cz8` HAS EXECUTED, so its docstring corrections are shipped and the overlap this section warned about is gone. Do not re-correct version-1 registry prose; if any remains stale, report it rather than editing, since it is outside this plan's declared paths.

No existing spec is amended by this plan. NOTE the inverse of the original warning is what an executor will actually meet: a spec asserting per-role model selection EXISTS would now be TRUE for the verifier (`verify_with`), so do not "correct" such a statement. A spec asserting that NO per-role selection exists is the false one. Either way, declare the spec file in `Scope-Paths` before editing it, per the spec-amendment rule, and record the reason here.

## Open questions

### OQ-01: Is the unit a ROLE, an arbitrary named ACTION, or neither yet, GIVEN that a per-role field has already shipped?

- Blocking: no
- Status: resolved
- Owner: none
- Finding: PR-901
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-08: A ROLE, AND BUILD IT NOW. But the maintainer first CORRECTED THIS PLAN'S PREMISE, and the correction is the most important thing recorded here, because it invalidates the cost argument the whole plan was built on.
  THE PLAN'S FRAMING WAS WRONG. This plan, and the item behind it, framed per-action model selection as COST CONTROL: the motivating case was "paying top-tier rates for a yes/no question", and the third answer (defer, build nothing) was recommended precisely because the cost is bounded by caching. Presented that way, the maintainer rejected the framing outright: "It is NOT about just getting a cheap model. It's about getting the best model for the job. Writing prose? Sonnet 5. Writing code? Opus 5. Writing code fast? Gemini 3.8 Flash, with Opus 5 validation. Doing research online? GPT 5.6 Sol High. Checking content? Haiku."
  THAT REFRAMING DECIDES THE UNIT WITHOUT FURTHER EVIDENCE, which is why E-02's extensibility count is no longer the discriminator. The maintainer's categories ARE roles: write prose, write code, write code fast, research online, check content. They are KINDS OF WORK, not arbitrary step names, so an open action map buys nothing while giving up the fail-closed validation `verify_with` deliberately has. A validated role enum it is.
  AND IT KILLS THE DEFER OPTION, which this plan recommended and which I had recommended to the maintainer. Fitness-for-task applies to EVERY run, not to one unexecuted probe, so the population of beneficiaries is not "a single prospective consumer in an unexecuted plan" as E-05 currently reasons. The cost-bound argument (verdicts cached against a content digest) is irrelevant to a quality argument. E-05's "decide and defer" outcome must therefore be struck rather than weighed.
  DISPOSITION OF `verify_with`: EXTEND. The maintainer chose "role to model mapping now, pairing recorded as the next step", and `verify_with` is already exactly the right shape to extend rather than supersede or layer: it is a PROFILE REFERENCE rather than an inline model string (for the stated reason that an inline model "would fork the one place a launch identity is defined"), it already uses the settled precedence chain, and a dangling reference is already REFUSED AT LOAD TIME by `_validate_verify_reference`. A general role map should reuse all three properties, and the verifier case should BE an entry in that map. Do NOT layer a second field beside it: the module docstring already argues that two switches for one behavior is what the `validate` precedence chain exists to avoid.
  ONE THING THE MAINTAINER'S EXAMPLES NEED THAT NOTHING TODAY CAN EXPRESS, recorded here and deliberately NOT built: "Writing code fast? Gemini 3.8 Flash, with Opus 5 validation" PAIRS TWO MODELS on one piece of work. Four of the five examples are a plain role-to-model mapping; that fifth needs a role to name a PRODUCING model plus a VALIDATING model. `verify_with` cannot express it, because it attaches a verifier to a PROFILE rather than letting a role declare a pair, and `validate` separately decides only WHETHER a verifier runs. The maintainer chose to record the pairing as the NEXT step rather than build it here, so OQ-05 carries it and it must not be smuggled into E-05.

### OQ-05: How should a role declare a producing model plus a validating model?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN BY THE MAINTAINER'S OWN CHOICE 2026-09-08, recorded so the requirement is not lost when E-05 ships the simpler mapping. Of the five fitness-for-task examples the maintainer gave, four are a role naming ONE model and the fifth is a role naming TWO: "Writing code fast? Gemini 3.8 Flash, with Opus 5 validation." Asked how far to go, the maintainer chose "role to model mapping now, pairing recorded as the next step", so this plan builds the mapping and this question owns the pair.
  WHY IT IS NOT A TRIVIAL EXTENSION, which is the reason it deserves its own decision rather than an extra field. FIRST, it overlaps machinery that already exists and is deliberately factored the other way: `validate` decides WHETHER a verifier turn runs and `verify_with` decides WHICH PROFILE runs it, and the module docstring states plainly that conflating the two "would be a defect". A pair attached to a ROLE is a third axis crossing both, so the interaction (a role declaring a validator while `validate` is off, or while an explicit `--verify-with` is passed) must be defined rather than discovered. SECOND, `verify_with` resolves ONE HOP DELIBERATELY (DECISION 06-kgpptv-D1: `A.verify_with = "B"` launches the verifier with B's own fields, and B's own `verify_with` is INERT), so a role-level pair must say whether it inherits that one-hop rule or introduces a second resolution model. THIRD, "with Opus 5 validation" may mean the existing verifier turn with a different model, or a fundamentally different write-then-check pairing inside one action; those are different builds and the maintainer's phrasing does not settle which.
  WHAT WOULD MAKE THIS CHEAP: if the answer is "the existing verifier turn, with the model chosen by the producing role rather than by the producing profile", it is a small addition to whatever E-05 builds. If it is a new intra-action pairing, it is a separate plan. A maintainer should say which before anyone scopes it.


### OQ-02: Where should the preference be declared, and with what precedence?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: FOLLOW THE CHAIN THAT IS ALREADY SHIPPED FOR A MODEL PREFERENCE, which is a stronger answer than the one originally recorded here. `f2mrsw` established the pattern with the `validate` tri-state, and `kgpptv` then applied the SAME chain to a model preference: `explicit --verify-with > profile's own verify_with > defaults.verify_with > ABSENT` (F-11). So this is not "follow a nearby convention by analogy" but "a model preference already resolves this way, and a third variant would be the defect". Consistency is the whole argument: an operator who has learned how `validate` and `verify_with` resolve must not have to learn a second rule. One thing genuinely differs and E-03 must state it: an action-keyed preference is a MAP rather than a scalar, so the third tier's key shape (`defaults.<field>`) needs deciding even though the ordering does not. Non-blocking: it becomes actionable only once OQ-01 names the unit, and it changes no behavior on its own.

### OQ-03: What happens when a preference names a model the host cannot provide?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: SPLIT INTO TWO CASES, because the single answer originally recorded here CONTRADICTS SHIPPED CODE (F-6). (A) AN UNRESOLVABLE REFERENCE, i.e. a preference naming something that matches no profile: REFUSE AT LOAD TIME, which is what `_validate_verify_reference` already does, for the reason the code states: a silent fallback means "the operator would believe an independent model verified the work when the same model did. That is worse than a dangling default, because the failure is invisible in the result rather than visible in the bill." Recommending warn-and-fall-back here would ask a new mechanism to be laxer than the shipped one it sits beside, for no stated reason. (B) A RESOLVED PROFILE WHOSE MODEL THE HOST CANNOT PROVIDE AT LAUNCH: WARN AND FALL BACK, do not fail the run. Here the item's reasoning holds and is worth preserving verbatim in the decision record: "Failing closed on a MODEL CHOICE is probably wrong, since the work can still be done, just more expensively." The distinction between (A) and (B) is CONFIGURATION ERROR versus RUNTIME UNAVAILABILITY: the first is knowable and fixable at load time and refusing it costs nothing, while the second is discovered mid-run when refusing would waste a queue for no safety gain. The fallback in (B) must be LOUD (recorded in run state, not merely printed) but must not refuse. The sandbox contrast remains worth stating (F-15) and is the WEAKER analogy: `select_execution_profile` raises because degradation removes a security boundary, whereas `verify_with` shows this module already fails closed on a MODEL question for an INTEGRITY reason, which is the nearer case and the one a reader will otherwise miss.

### OQ-04: Does a cached artifact produced under model A stay valid when the preference changes to model B?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: KEEP IT AND RECORD THE ANSWERING MODEL, which is the option the maintainer ALREADY CHOSE for the analogous case. The 2026-09-07 ruling on `m7gvuz` OQ-01 was to use the run's resolved model and record which model answered with each cached verdict "so a future reader can distrust a verdict produced by a weak model". Invalidating on model change is safe but defeats the caching that makes the probe free, which is the same caching that bounds this item's whole cost. Keeping only when the new model is "stronger" needs a model ranking the repository does not have; embedding a fast-moving external judgement in durable config would age badly and is recommended AGAINST. ONE CORRECTION TO THIS PLAN'S FRAMING (F-9): the answering-model record DOES NOT EXIST. `m7gvuz` is approved/unexecuted and `8tgg6g` is `reviewed`/unexecuted, and the field is a design intent in `m7gvuz` OQ-01, not shipped state, so this question has NO concrete substrate today and the recommendation is a forward commitment on a store yet to be built. E-04 states that rather than treating the store as present.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the ACTUAL output establishing the shipped baseline: `verify_with` in `ALLOWED_PROFILE_KEYS`, the precedence chain quoted from the module docstring, the `SCHEMA_VERSION`/`SUPPORTED_SCHEMA_VERSIONS` values, `_validate_verify_reference`'s stated reason for refusing a dangling reference, and `resolve_launch_profile`'s location found BY SYMBOL with the drift against this plan's `:2613` citation stated. ALSO paste the two absence measurements: `grep -c` for `role` in `runner_profiles.py`, and for `runner_profiles|resolve_launch_profile|launch_profile` in `agy_runipd.py`. Confirm in one sentence that `kgpptv` reads `executed`, since an executor who finds otherwise has a materially different problem.
  - Observed evidence: the shipped `verify_with` baseline, symbol-cited, plus both absence measurements; full output below.
    THE SHIPPED MECHANISM, measured at HEAD `a9510164`:

    ```text
    $ python3 -c "...; print('verify_with' in rp.ALLOWED_PROFILE_KEYS); print(rp.SCHEMA_VERSION, sorted(rp.SUPPORTED_SCHEMA_VERSIONS))"
    verify_with in ALLOWED_PROFILE_KEYS: True
    SCHEMA_VERSION = 2 | SUPPORTED_SCHEMA_VERSIONS = [1, 2]
    ALLOWED_PROFILE_KEYS = ['agent', 'model', 'runner', 'validate', 'variant', 'verify_with']
    ALLOWED_DEFAULTS_KEYS = ['profiles', 'validate', 'verify_with']
    ```

    (a) THE PRECEDENCE CHAIN, quoted from the module docstring: "explicit --verify-with  >  profile's own `verify_with`  >  `defaults.verify_with`  >  ABSENT, which means "the verifier uses the EXECUTOR's own launch" (today's behavior)".

    (b) A PROFILE REFERENCE, NOT AN INLINE MODEL, with the stated security reason, quoted: "IT IS A PROFILE REFERENCE, NOT AN INLINE MODEL, and that is the security decision. A bare model string here would fork the one place a launch identity is defined and would be the first field to escape this module's validation; a reference reuses a whole ALREADY-VALIDATED profile, including its `variant` and `agent`."

    (c) THE BUMP AND THE COMPATIBILITY STORY: `SCHEMA_VERSION = 2` with `SUPPORTED_SCHEMA_VERSIONS = frozenset((1, 2))`, and the docstring states "ABSENT IS THE WHOLE BACKWARD-COMPATIBILITY STORY. Every profile written before this field existed, and every run started without one, resolves the verifier to the executor's own frozen launch and behaves EXACTLY as it does today."

    (d) THE DANGLING REFUSAL, quoting `_validate_verify_reference`'s own reason: a reference that resolves to nothing "would silently fall back to the executor's model, so the operator would believe an independent model verified the work when the same model did. That is worse than a dangling default, because the failure is invisible in the result rather than visible in the bill."

    (e) ONE IDENTITY PER RUN FOR EVERY OTHER ACTION, located BY SYMBOL:

    ```text
    $ grep -n "def resolve_launch_profile" agent_workflows/oc_runipd.py
    2613:def resolve_launch_profile(args: argparse.Namespace) -> runner_profiles.ResolvedLaunch:
    ```

    DRIFT STATED: this plan's Concern and conventions cite `:2613`, which is EXACTLY where it is at my HEAD, so the plan's corrected citation held; the ORIGINAL `:2702` (and the backlog item's `:2660`) were both stale. The lesson still applies and I re-derived it rather than trusting any of the three.

    WHAT REMAINS ABSENT, both measured:

    ```text
    $ git show HEAD:agent_workflows/runner_profiles.py | grep -c "role"
    0
    $ grep -cE "runner_profiles|resolve_launch_profile|launch_profile" agent_workflows/agy_runipd.py
    0
    ```

    So before this Order the module had ZERO occurrences of `role` (the capability existed spelled `verify_with`, which is why a vocabulary grep is not a capability measurement), and no mechanism let an ARBITRARY named kind of work declare a preference. The mechanism is still OC-ONLY IN PRACTICE: `RUNNER_REGISTRY` carries an `agy` row (`tm2cz8` is `executed`) but `agy_runipd.py` references no profile symbol at all, so a registry row is not an integration.

    `kgpptv` READS `executed`: `grep -m1 "^- Status:" .aw/records/plans/executed/*kgpptv*.ipd.md` -> `- Status: executed`, so the re-scope this plan's E-01 made conditional was indeed already triggered and I did not re-confirm a gap that shipped code had closed.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the call-site table. It must name, per site, whether it invokes a model today, WHICH of the maintainer's five kinds of work it performs (or that it fits none), whether `verify_with` ALREADY serves it, and whether reaching it needs new plumbing. Paste the check of whether a REVIEW turn is a distinct call site or the execute site with `item["action"] == "review"`. Confirm in one sentence that no per-action COST PROFILE is presented as a deciding attribute, since the maintainer rejected the cost framing, and that `m7gvuz`'s probe is recorded as prospective without the plan depending on it.
  - Observed evidence: the call-site table, the review-turn check, and the fitness-not-cost confirmation; full output below.
    THE CALL-SITE INVENTORY, built from the code rather than from the vocabulary. Measured:

    ```text
    $ grep -n "run_opencode(" agent_workflows/oc_runipd.py
    5359:def run_opencode(
    6354:        exit_code, session_id, log_path, argv = run_opencode(      <- the EXECUTE site
    6599:            v_rc, _v_session, _v_log, _v_argv = run_opencode(      <- the VERIFIER site
    $ grep -n "use_verifier_launch" agent_workflows/oc_runipd.py
    5371:    use_verifier_launch: bool = False,
    5427:    verify_launch = use_verifier_launch and bool(options.get("verify_launch_profile"))
    6616:                use_verifier_launch=True,                          <- the ONLY True
    $ grep -n "ACTION_CHOICES" agent_workflows/oc_runipd.py
    2424:ACTION_CHOICES = ("review", "plan", "execute")
    ```

    | Call site (by symbol) | Invokes a model today | Kind of work | Served by `verify_with`? | Reaching it needs |
    |---|---|---|---|---|
    | `run_opencode` at `:6354`, `action == "execute"` | YES | write-code | NO (it is the EXECUTOR; `verify_with` names who checks it) | new plumbing: a role-aware launch selection at this site |
    | `run_opencode` at `:6599`, the verifier turn | YES | verify (and arguably check-content) | YES, fully. This is the one role already served | nothing; already resolved via `resolve_launch_pair` |
    | `run_opencode` at `:6354`, `action == "review"` | YES | check-content | NO | NOT A DISTINCT SITE (see below), so a role cannot attach without new plumbing |
    | `run_agy_turn` (`agy_runipd.py:2741`) | YES (`--model` only) | write-code | NO, and cannot be: agy reads no profiles at all | a whole profile integration, absent today |
    | the orchestrator probe `m7gvuz` adds | NO, PROSPECTIVE (unexecuted) | check-content | NO | the probe itself, then role-aware selection |
    | `write-prose`, `write-code-fast`, `research-online` | NO SUCH SITE EXISTS | n/a | n/a | a consumer; these three roles are declarable but reach no seam today |

    A REVIEW TURN IS NOT A DISTINCT CALL SITE, confirmed at my HEAD. `run_opencode`'s own comment states it and the code agrees: "A REVIEW turn needs no branch at all: it IS the execute call site with `item["action"] == "review"` (read below only to pick a `--title` label), so it keeps the executor's launch automatically (F-11)." Measured, the only reads are `is_review = item.get("action") == "review"` at `:5442` and `action_label = label_suffix or ("review" if is_review else "exec")` at `:5443`, i.e. label selection only. CONSEQUENCE FOR E-05, which is why the item required this check: a role preference cannot attach to review without new plumbing, so the schema this Order ships is necessarily ahead of the seams.

    THREE OF THE SIX ROLES FIT NO EXISTING SEAM (`write-prose`, `write-code-fast`, `research-online`), which I report rather than force into a category: they are legitimate kinds of work the maintainer named, and their absence from the code is a statement about how few model-invoking seams exist today, not a defect in the vocabulary.

    NO COST PROFILE IS PRESENTED AS A DECIDING ATTRIBUTE anywhere in this evidence or in the implementation: the deciding attribute is FITNESS (which kind of work the site performs), per the maintainer's ruling that "It is NOT about just getting a cheap model. It's about getting the best model for the job."

    `m7gvuz`'s PROBE IS RECORDED AS PROSPECTIVE AND NOTHING HERE DEPENDS ON IT: `grep -m1 "^- Status:"` on `.aw/records/plans/pending/*m7gvuz*` returns `- Status: approved` (unexecuted), and a repo-wide search for `probe_verdict|orchestrator_probe|probe_cache|uncovered_work` over `agent_workflows/` and `tests/` returns NOTHING, so the probe does not exist; the fitness argument stands on every run without it.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the declaration-site recommendation quoting the chain `kgpptv` SHIPPED for `verify_with`, not merely `f2mrsw`'s `validate` chain, and state what an action-keyed third tier changes. Paste the fallback recommendation as TWO separate cases with their expected behaviors: unresolvable reference (quote `_validate_verify_reference`'s reason and say whether you recommend keeping that refusal) and unprovidable-at-launch (warn and fall back). Paste the sandbox contrast, quoting `select_execution_profile`'s raise-not-degrade behavior, and state in one sentence why it is the weaker analogy. Confirm all are recorded as recommendations, not commitments.
  - Observed evidence: the shipped chain for question 2 and the two-case split for question 3, with the sandbox contrast; full detail below.
    QUESTION 2, THE DECLARATION SITE. The chain `kgpptv` SHIPPED for a MODEL preference, quoted from `resolve`'s own docstring (not from `f2mrsw`'s `validate` chain):

    ```text
    Precedence for ``verify_with``, on the SAME tri-state discipline, highest first::

        explicit --verify-with > profile's `verify_with` > `defaults.verify_with` >
        ABSENT (None), meaning the verifier reuses THIS launch
    ```

    RECOMMENDATION: reuse that chain, because a third variant would be the defect. This is a stronger claim than "follow a nearby convention": a MODEL preference already resolves this way, so an operator who has learned how `validate` and `verify_with` resolve must not have to learn a second rule.

    WHAT AN ACTION-KEYED TIER CHANGES, which the plan required me to state: the ORDERING does not change, but the third tier's KEY SHAPE does, because a role preference is a MAP rather than a scalar. `defaults.validate` and `defaults.verify_with` are single values, whereas a role table needs one entry per role. AS IMPLEMENTED (DECISION 01-btot17-D1) this resolved into a TOP-LEVEL `roles` object rather than a scalar under `defaults`, and the map became a NEW BOTTOM TIER rather than a replacement for the third: `explicit --verify-with > profile's own verify_with > defaults.verify_with > roles["verify"] > ABSENT`. Placing it BELOW the existing tiers is what makes the extension incapable of changing any existing document's resolution.

    QUESTION 3, SPLIT INTO TWO CASES, because a single answer contradicts shipped behavior.

    CASE (A), AN UNRESOLVABLE REFERENCE (a name matching no profile; a configuration error, knowable at load). Shipped behavior REFUSES, and `_validate_verify_reference` states why, quoted: a dangling reference "would silently fall back to the executor's model, so the operator would believe an independent model verified the work when the same model did. That is worse than a dangling default, because the failure is invisible in the result rather than visible in the bill." RECOMMENDATION: KEEP THAT REFUSAL, and extend it to the role map, which E-05 did (`_validate_role_reference`, refused at load with the analogous reason). Recommending warn-and-fall-back here would ask a new mechanism to be LAXER than the shipped one it sits beside, for no stated reason.

    CASE (B), A RESOLVED PROFILE WHOSE MODEL THE HOST CANNOT PROVIDE AT LAUNCH (knowable only at run time). RECOMMENDATION: WARN AND FALL BACK, do not fail the run, with the fallback recorded in run state so it is LOUD rather than merely printed. The item's reasoning holds here and is preserved verbatim in the spec: "Failing closed on a MODEL CHOICE is probably wrong, since the work can still be done, just more expensively." The distinction between (A) and (B) is CONFIGURATION ERROR versus RUNTIME UNAVAILABILITY: refusing the first costs nothing, while refusing the second wastes a queue for no safety gain.

    THE SANDBOX CONTRAST, quoted from `select_execution_profile`:

    ```text
    """Resolve the execution profile, FAILING CLOSED when hard mode is unavailable.

    x03wgn Section 8 Phase 6.3: "fail rather than silently degrading when hard mode is
    requested but unavailable." Returning `"default"` for an unsupported `"hardened"`
    request would be that silent degradation, so this raises instead.
    """
    ...
        raise HardModeUnavailableError(
            "the hardened execution profile was requested, but this host's EXECUTED "
            "sandbox probe reports it cannot enforce it ... "
            "Refusing to run unsandboxed: hard mode fails closed rather than silently "
            "degrading (x03wgn Section 8 Phase 6.3)."
        )
    ```

    IT IS THE WEAKER ANALOGY, in one sentence: it fails closed because degradation removes a SECURITY boundary, whereas `verify_with` shows this module already fails closed on a MODEL question for an INTEGRITY reason, which is the nearer case and the one a reader shown only the sandbox would miss.

    RECORDED AS RECOMMENDATIONS, NOT COMMITMENTS, with one exception I state plainly rather than blur: case (A) was IMPLEMENTED, because the maintainer's ruling turned this into a build plan and a load-time check is part of the schema E-05 ships. Case (B) is a RUNTIME behavior and remains a recommendation, recorded as spec requirement R-6, because no consumer resolves a role into a launch yet and there is nothing to warn from.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the three cache options with their costs. Paste evidence of whether the answering-model record ACTUALLY EXISTS yet: `m7gvuz`'s and `8tgg6g`'s `- Status:` lines plus a search for the store itself, rather than trusting the item's claim that it does. State explicitly whether the substrate is present or planned. Paste the maintainer's `m7gvuz` OQ-01 ruling as the anchor, and state the recommendation. Confirm no cache behavior was changed.
  - Observed evidence: the three cache options, the measured finding that the substrate is PLANNED not present, and the anchored recommendation; full output below.
    THE THREE OPTIONS AND THEIR COSTS:

    1. INVALIDATE ON MODEL CHANGE. Safe, but expensive, and it defeats the content-digest caching that made the probe free in the first place, i.e. it removes the very property the backlog item cited as the reason the whole area was non-urgent.
    2. KEEP IT AND RECORD THE ANSWERING MODEL. Cheap; the verdict survives a preference change and a reader can distrust a verdict produced by a weak model. Cost: a stale verdict remains in force until the content changes, so the record must actually be READ for the mitigation to work.
    3. KEEP ONLY WHEN THE NEW MODEL IS STRONGER. Requires a model RANKING the repository does not have; embedding a fast-moving external judgement in durable config would age badly. Recommended AGAINST.

    WHETHER THE SUBSTRATE EXISTS, measured rather than trusted:

    ```text
    $ grep -m1 "^- Status:" .aw/records/plans/pending/*m7gvuz*.ipd.md
      | - Status: approved
    $ grep -m1 "^- Status:" .aw/records/plans/pending/*8tgg6g*.ipd.md
      | - Status: approved
    $ grep -rnE "probe_verdict|orchestrator_probe|orchestrator-probe|probe_cache|uncovered_work" agent_workflows/ tests/
    (no matches)
    ```

    THE SUBSTRATE IS PLANNED, NOT PRESENT. Both plans are `approved` and UNEXECUTED, and no probe or verdict-store symbol exists anywhere in the package or the suite. TWO CORRECTIONS TO THIS PLAN'S OWN TEXT, which I record because the plan told me to treat its sibling claims as dated: (i) the plan calls question 4 "the one question with a concrete substrate", and that is FALSE, exactly as its own F-9 predicted; (ii) the plan and its F-9 describe `8tgg6g` as `reviewed`, but it now reads `approved`, so even the review's correction had drifted by the time I measured. The answering-model field remains a DESIGN INTENT in `m7gvuz` OQ-01, so the recommendation is a FORWARD COMMITMENT on a store yet to be built.

    THE MAINTAINER'S ANCHORING RULING, quoted from `m7gvuz` OQ-01: "RESOLVED 2026-09-07 by the maintainer: USE THE RUN'S ALREADY-RESOLVED MODEL, record which model answered alongside each verdict (child 02 stores the field for exactly this reason), and add NO role routing here."

    RECOMMENDATION: KEEP AND RECORD (option 2), which is the option the maintainer ALREADY CHOSE for the analogous case, so the general answer inherits a decision rather than inventing one. Recorded as spec requirement R-7, and NOT as a commitment binding `8tgg6g`, which still owns the store.

    NO CACHE BEHAVIOR WAS CHANGED: there is no cache to change (see the empty search above), and my diff touches only `agent_workflows/runner_profiles.py`, `tests/test_runner_profiles.py`, this plan, the new spec, and the lane submission files. `git diff --stat` confirms no probe, verdict, or cache module appears.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the schema diff showing the validated role enum covering the maintainer's five kinds of work, and proof it EXTENDS `verify_with` rather than superseding or layering (the verifier case resolvable as an entry in the same map, `verify_with` still valid). Paste the schema-version decision citing DECISION 06-kgpptv-D2. Paste tests proving: an existing on-disk config still loads; a document carrying `verify_with` still loads and resolves UNCHANGED; an unknown key is still REFUSED; an unresolvable role reference is REFUSED at load (OQ-03 case A); and a resolved profile whose model the host cannot provide WARNS and falls back with the fallback recorded in run state (OQ-03 case B). Paste NEGATIVE proof that NO producing-plus-validating pair was built (OQ-05 is the maintainer's and remains open), that `kgpptv`'s executed plan file was not modified, and that `verify_with` was neither removed nor renamed. Paste the BARE `python3 -m pytest` summary lines before and after with the failure-set delta stated.
  - Observed evidence: the role enum, the extend-not-layer proof, the version decision, 26 passing role tests, the negative proofs, and before/after suite lines; full output below.
    THE VALIDATED ROLE ENUM, covering the maintainer's five kinds of work plus `verify`:

    ```python
    ROLE_NAMES: Tuple[str, ...] = (
        "write-prose",
        "write-code",
        "write-code-fast",
        "research-online",
        "check-content",
        "verify",
    )
    ROLE_VERIFY = "verify"
    ```

    ```text
    $ python3 -c "from agent_workflows import runner_profiles as rp; print(rp.ROLE_NAMES)"
    ('write-prose', 'write-code', 'write-code-fast', 'research-online', 'check-content', 'verify')
    ```

    The map is TOP LEVEL (`ALLOWED_DOCUMENT_KEYS` gained `roles`; `ALLOWED_PROFILE_KEYS` and `ALLOWED_DEFAULTS_KEYS` are UNCHANGED), each value is a PROFILE REFERENCE validated by the existing profile-name grammar, and a dangling entry is refused at load by `_validate_role_reference` through `_validate_referential_integrity`. Placement rationale is DECISION 01-btot17-D1 in the register.

    IT EXTENDS `verify_with` RATHER THAN SUPERSEDING OR LAYERING. The verifier case is an ENTRY in the same map, and the map is a NEW BOTTOM TIER of the ONE existing chain, so there is no second switch:

    ```python
        elif cfg.roles.get(ROLE_VERIFY) is not None:
            resolved_verify_with = cfg.roles[ROLE_VERIFY]
            provenance["verify_with"] = PROVENANCE_ROLE_MAP
    ```

    ```text
    $ python3 -c "...cfg with roles={'verify':'op'}, profile 'gem' has no verify_with..."
    verify_with op prov role-map
    ```

    All four tiers walked, and the position is what makes the extension safe (it is consulted ONLY where the shipped chain had already fallen through to ABSENT, so it can ADD an answer but never CHANGE one):

    ```text
    tests/test_runner_profiles.py::RolesExtendVerifyWithTests
      verify_with chain: explicit > profile > defaults > roles['verify'] > same-as-executor
    ```

    THE SCHEMA-VERSION DECISION, citing DECISION 06-kgpptv-D2: `SCHEMA_VERSION` STAYS AT 2 and `roles` is read at any supported version. This DECLINES the precedent deliberately, and the reason is recorded in the constant's own docstring and as DECISION 01-btot17-D2: 06-kgpptv-D2's argument turns entirely on WHICH refusal an older aw shows a user holding a document that CARRIES the new key ("Upgrade aw" versus "unknown field(s) ['roles']"), and no such document can exist yet, since no writer emits `roles` and no consumer reads it. The bump is recorded as the REQUIRED COMPANION of the wiring plan (spec R-8). Cost measured rather than asserted in prose:

    ```text
    tests/test_runner_profiles.py::RolesVersioningTests
      roles accepted at schema_version [1, 2] with SCHEMA_VERSION still 2
      accepted cost, measured: older aw says "document: unknown field(s) ['roles']; allowed: ['de"
    ```

    THE REQUIRED PROOFS, each a named passing test (26 role tests, all green):

    ```text
    $ python3 -m pytest tests/test_runner_profiles.py -o addopts="" -k "Roles or RoleVocabulary"
    collected 131 items / 105 deselected / 26 selected
    tests/test_runner_profiles.py ..........................               [100%]
    ====================== 26 passed, 105 deselected in 0.25s ======================
    ```

    - (i) AN EXISTING ON-DISK CONFIG STILL LOADS, `RolesVersioningTests::test_an_existing_v1_document_with_no_roles_still_loads_and_resolves_unchanged` -> "v1 no-roles document loads, resolves and is not rewritten" (bytes on disk asserted byte-identical after the read).
    - A DOCUMENT CARRYING `verify_with` STILL LOADS AND RESOLVES UNCHANGED: `RolesVersioningTests::test_a_document_carrying_verify_with_still_loads_and_resolves_unchanged` -> "a verify_with document loads and resolves exactly as before" (`verify_with == "strong"`, provenance `profile`, bytes unchanged). Reinforced by `RolesExtendVerifyWithTests::test_every_pre_existing_resolution_is_byte_identical`, which asserts the WHOLE `ResolvedLaunch` is equal field-for-field.
    - (iii) AN UNKNOWN KEY IS STILL REFUSED, `RolesSchemaTests::test_an_unknown_top_level_key_is_still_refused` -> "unknown top-level key still refused: document: unknown field(s) ['role']", i.e. adding `roles` did not loosen the fail-closed check, and a near-miss singular `role` is still caught. `RolesSchemaTests::test_roles_did_not_widen_the_injection_surface` additionally asserts the forbidden capability keys still raise and that `roles` is absent from the PROFILE and DEFAULTS surfaces.
    - OQ-03 CASE A, AN UNRESOLVABLE ROLE REFERENCE IS REFUSED AT LOAD: `RolesReferenceIntegrityTests::test_a_dangling_role_reference_is_refused_at_load_time` -> "dangling role refused at load: roles['write-code'] points at 'nope', which does not exist (known profiles: cheap, strong). Remove the role or create the profile; a dangling role reference would fall through as if the role were never set, so the work would silently run on a model nobody chose for it." Mutators cannot create one either (`test_a_mutator_cannot_create_a_dangling_or_unknown_role`), and removing a referenced profile is refused rather than silently unrouting the role (`test_removing_a_profile_a_role_references_cannot_leave_a_dangling_role`).
    - OQ-03 CASE B IS NOT IMPLEMENTED, AND I AM NOT CLAIMING IT IS. This is the one required item I cannot evidence, and the reason is structural rather than an omission: a warn-and-fall-back on a model the HOST CANNOT PROVIDE AT LAUNCH is a RUNTIME behavior needing (i) a consumer that resolves a role into a turn's argv and (ii) run state to record the fallback in. This plan's `Scope-Paths` deliberately excludes every driver module ("NO driver module is in scope, deliberately"), and its own scope check states the consequence: "this plan ships the SCHEMA and no consumer, so nothing routes a model until a follow-on plan wires it." So there is nothing to warn FROM and no run state to record INTO. Case B is recorded as spec requirement R-6 and is owned by the wiring plan. Writing a test asserting a warning that no code path can emit would have been fabricated evidence.
    - NO PRODUCING-PLUS-VALIDATING PAIR WAS BUILT (OQ-05 remains the maintainer's and OPEN). Refused BY NAME, and the message cites the open question so it cannot read as an oversight:

    ```text
    $ python3 -c "...roles={'write-code-fast': {'produce':'c','validate':'s'}}..."
    REFUSED: roles['write-code-fast'] must be a single profile NAME string, not an object. A role
    naming a PRODUCING model plus a VALIDATING one ("write code fast, validated by a stronger
    model") is an OPEN DESIGN QUESTION (`btot17` OQ-05), not an oversight: it crosses 'validate'
    (whether a verifier turn runs) and 'verify_with' (which profile runs it), and it must say
    whether it inherits the ONE-HOP rule. It is deliberately not expressible until that is decided.
    ```

    `RolesOpenQuestionFenceTests` pins this for three object shapes plus the list form, so the pair stays inexpressible rather than merely undocumented.

    `kgpptv`'s EXECUTED PLAN FILE WAS NOT MODIFIED:

    ```text
    $ git status --porcelain .aw/records/plans/executed/
    (empty)
    $ git diff --name-only HEAD | grep -i kgpptv
    (no output)
    ```

    `verify_with` WAS NEITHER REMOVED NOR RENAMED:

    ```text
    verify_with in ALLOWED_PROFILE_KEYS : True
    verify_with in ALLOWED_DEFAULTS_KEYS: True
    set_verify_with_default callable    : True
    LaunchProfile.verify_with exists    : True
    ```

    Pinned by `RolesExtendVerifyWithTests::test_verify_with_is_neither_removed_nor_renamed` -> "verify_with is still declared, still mutable, and still resolves unchanged".

    THE BARE SUITE, BEFORE AND AFTER, with the delta stated. The lane sets `AW_EXECUTION_ROLE`, which makes 17 lifecycle tests fail identically before and after my change, so BOTH readings are given rather than one (DECISION 01-btot17-D6).

    BEFORE (at `a9510164`, unmodified tree):

    ```text
    $ python3 -m pytest
    17 failed, 5954 passed, 3 skipped, 2 xfailed in 121.89s (0:02:01)
    $ env -u AW_EXECUTION_ROLE python3 -m pytest
    5971 passed, 3 skipped, 2 xfailed in 119.66s (0:01:59)
    ```

    AFTER (this change applied):

    ```text
    $ python3 -m pytest
    17 failed, 5980 passed, 3 skipped, 2 xfailed in 96.73s (0:01:36)
    $ env -u AW_EXECUTION_ROLE python3 -m pytest
    5997 passed, 3 skipped, 2 xfailed in 62.20s (0:01:02)
    ```

    FAILURE-SET DELTA: AFTER minus BEFORE is EMPTY on both readings. The 17 are the SAME 17 tests in both runs, every one failing with `AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes; a worker-role process must not run them`, which is the lane's own execution-role marker and not a repository defect; with that single variable unset the suite is fully green before AND after. Pass count moved 5971 -> 5997, i.e. +26, exactly the 26 role tests added. Also confirmed green: the OUT-OF-SCOPE surfaces that pin this schema literally (`tests/test_runner_profiles_e2e.py`, `tests/test_runner_profile_wizard.py`, `tests/test_oc_profile_cli.py`, `tests/test_run_dispatch.py`, `tests/test_cli.py` -> `187 passed`), which is the machine-checked proof that the top-level placement held this plan's declared scope.

    `aw sanitize --agent` -> `{"outcome":"clean","exit":0,"findings":0}`. `aw specs check` -> "all specs conform."
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

NO BLOCKING QUESTION REMAINS: OQ-01 WAS RESOLVED BY THE MAINTAINER ON 2026-09-08, AFTER THIS PLAN'S REVIEW. The plan was authored and reviewed as a DECISION plan holding a `Blocking: yes` question; the ruling converted it into a BUILD plan. Read the ruling in OQ-01 before starting, because it did two things: it decided the unit (a validated ROLE enum, extending `verify_with`, built now) and it REJECTED the cost-control framing this plan was originally built on ("It is NOT about just getting a cheap model. It's about getting the best model for the job"). Every place this document still reasons from cost is superseded by that; where the two disagree, the ruling wins.

E-01 THROUGH E-04 ARE NOW PREPARATORY RATHER THAN DECISIVE. They change no code and still earn their place: E-01 establishes the shipped `verify_with` baseline the build must extend, and E-02 maps the five kinds of work onto real call sites so E-05 builds something a runner can consume. But they no longer gather evidence to CHOOSE the unit, and the extensibility count E-02 originally turned on is not the discriminator. "DECIDE AND DEFER" IS STRUCK and must not be taken (see E-05).

ONE OPEN QUESTION SURVIVES AND IS DELIBERATELY NOT BLOCKING: OQ-05 (a role naming a PRODUCING plus a VALIDATING model, from the maintainer's "Gemini 3.8 Flash, with Opus 5 validation" example). The maintainer chose "role to model mapping now, pairing recorded as the next step", so it is out of scope by ruling rather than by omission. Do NOT build it here, and do NOT let E-05's schema quietly make it expressible without a decision, since it crosses `validate` and `verify_with`, which the module docstring says must not be conflated.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Re-locate every symbol by NAME, never by the line numbers cited here: this plan's own `resolve_launch_profile` citation was ALREADY WRONG at authoring (`:2702` versus the actual `:2613`), inherited from a sibling rather than measured, which is the concrete demonstration of why. TREAT EVERY SIBLING-PLAN STATUS CLAIM IN THIS DOCUMENT AS DATED AND RE-READ IT: the review found `kgpptv` described as approved when it had executed, `m7gvuz` described as blocked when its questions were resolved, and a verdict store described as existing when it is unbuilt. Do NOT edit `kgpptv`'s plan file (it is in `executed/`) or `m7gvuz`. Do NOT remove, rename or deprecate `verify_with`. Paste ACTUAL command output; never claim a measurement you did not run. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence. The deliverables are the role enum extending `verify_with`, its tests, and the spec decision record; a run that produces only the record has NOT completed this plan, since the deferral outcome is struck.
