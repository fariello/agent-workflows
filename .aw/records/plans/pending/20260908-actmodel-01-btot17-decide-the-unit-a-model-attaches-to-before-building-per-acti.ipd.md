# IPD: Decide the unit a model attaches to before building per action model selection

- Date: 2026-09-08
- Kind: child
- Concern: THE RUNNER RESOLVES ONE MODEL IDENTITY FOR AN ENTIRE RUN, SO NO ACTION CAN CHOOSE A CHEAPER MODEL, AND THE ONE APPROVED PLAN THAT LOOKS LIKE THE FIX COVERS EXACTLY ONE ROLE. Re-verified at HEAD by symbol rather than by remembered line: `runner_profiles` contains NO `role` concept at all (`grep -n role agent_workflows/runner_profiles.py` -> zero hits), and `resolve_launch_profile` resolves a single launch identity for the whole run. NOTE the item cites that function at `:2660`; it is now at `oc_runipd.py:2702`, which is exactly the drift this repository warns about and is why the finding is re-stated on new coordinates.
  `kgpptv` DOES NOT COVER THIS AND A GENERAL MECHANISM WOULD LIKELY SUBSUME IT, which is the whole reason this item exists rather than being closed as duplicate. `kgpptv` (`runprofile-06`, `- Status: approved`, unexecuted) gives the VERIFIER TURN its own resolved profile. That is one hard-coded role, so an arbitrary new action such as the orchestrator probe still has nowhere to declare a preference. The item's own words: a general capability "would likely SUBSUME `kgpptv`, which is worth considering before executing it."
  ONE OF THE ITEM'S PREMISES ABOUT `kgpptv` IS NOW FALSE, AND IT MATTERS FOR THE DESIGN. `kgpptv` was authored believing the profile mechanism is opencode-only (its F-12). Approved plan `tm2cz8` (`hostdefault-01`) makes that false by registering the agy host in `runner_profiles.RUNNER_REGISTRY`, and `ybkmzp`'s Deferred section says so explicitly: "NOTE for whoever executes `kgpptv`: it was authored believing the profile mechanism is oc-only (its F-12), which child 01 makes false, so its scope should be re-read rather than trusted." So a per-action mechanism designed today must be cross-host from the start, not oc-shaped.
  THE MOTIVATING CASE IS REAL BUT DELIBERATELY BOUNDED, WHICH IS WHY THIS IS A DECISION AND NOT A BUILD. Plan `m7gvuz` adds a pre-run probe asking a model one yes/no question per queued orchestrator; paying a top-tier rate for that is wasteful. The maintainer's 2026-09-07 ruling was to use the run's already-resolved model and RECORD which model answered with each cached verdict, so a future reader can distrust a weak verdict. `m7gvuz`'s review then re-verified the gap at round 2 and recorded that an executor reading its OQ-01 as "reuse the per-role resolver" would "find nothing to reuse". And the cost is bounded: probe verdicts are cached against a content digest, so on a stable corpus the probe costs nothing after its first pass, and the waste scales with how often plans CHANGE, not with how often runs happen.
  SO THE DELIVERABLE IS THE DECISION THE ITEM SAYS IS MISSING, NOT A MECHANISM. The item is explicit: "filed as a BACKLOG ITEM rather than an IPD, because it is a decided-but-unscoped design question, not a task list. It graduates into a plan if and when it earns one." Graduating it as a build plan would invent answers to four questions the maintainer reserved, the largest of which (role versus arbitrary action) determines whether an approved plan should be executed or retired.
- Scope: Produce the recorded design decision per-action model selection needs, with the evidence each choice turns on, and implement ONLY what that decision authorizes. The four questions the item lists are the deliverable's shape. EXPLICITLY EXCLUDES building a routing mechanism before the unit is chosen, and excludes touching `kgpptv`, whose fate is one of the questions.
- Scope-Paths: agent_workflows/runner_profiles.py, .aw/records/specs, tests/test_runner_profiles.py
- Item-Dependencies: none
- Status: to-review
- Set: actmodel
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: btot17
- From-Backlog: 0k74my

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `0k74my` as a DECISION plan, which is what the item asks for ("a decided-but-unscoped design question, not a task list"). Every measurement re-verified at HEAD rather than trusted: `runner_profiles` still has ZERO `role` occurrences; `resolve_launch_profile` still resolves one identity per run but has MOVED from the item's cited `:2660` to `:2702`; `kgpptv` still reads `approved` and still sits in `pending/`. ONE PREMISE IS NOW FALSE and changes the design space: the item and `kgpptv` both treat the profile mechanism as opencode-only, but approved `tm2cz8` registers the agy host, and `ybkmzp` explicitly warns that `kgpptv`'s F-12 "child 01 makes false, so its scope should be re-read rather than trusted". So any per-action design must be cross-host from the outset. The item's cost bound was also confirmed as the reason this is non-urgent (verdicts cached against a content digest, so waste scales with plan churn rather than run count), which is why the plan's first two E-items are evidence-gathering and its build items are gated behind a blocking question.

## Goal

Give the repository a recorded answer to what a model preference attaches to, so the next action that wants a cheap model has somewhere to declare it and so an approved plan is either executed or retired on evidence rather than by default.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the live state, since two of the item's premises have moved

- [ ] E-01 RE-MEASURE THE GAP AND THE OVERLAP BY SYMBOL, and write both down. Four facts, none of which may be inherited from this plan's prose.
  THE FOUR: (a) `runner_profiles` still has no `role` concept; (b) `resolve_launch_profile` still resolves ONE identity per run, and where it now LIVES (it moved from `:2660` to `:2702` between the item's filing and this graduation); (c) `kgpptv`'s current `- Status:` and directory; (d) whether `tm2cz8` has executed, since that is what makes the mechanism cross-host and therefore changes what a per-action design must cover.
  RE-LOCATE BY SYMBOL, NEVER BY LINE NUMBER. Both runner files are under concurrent edit by live runs and have moved by tens of lines per day. The item's own citation is already stale by 42 lines, which is the concrete demonstration of why.
  IF `kgpptv` HAS EXECUTED, SAY SO AND RE-SCOPE. Its verifier-specific profile would then be shipped behavior, and the question changes from "should a general mechanism subsume it" to "should a general mechanism absorb a shipped special case", which is a harder and different design problem. Report rather than proceeding on the authored assumption.
  - Depends on: none
  - Expected outcome: a symbol-cited statement of all four facts at your HEAD, with an explicit re-scope if `kgpptv` has executed or if a role concept has appeared.
  - Execution state: pending

- [ ] E-02 ENUMERATE EVERY ACTION THAT INVOKES A MODEL, AND WHAT EACH ONE ACTUALLY NEEDS. This is the evidence question 1 turns on, and it cannot be answered from the abstract role-versus-action framing.
  BUILD THE LIST FROM THE CODE, not from the vocabulary. At minimum: the executor turn, the verifier turn, the plan-review turn, and the orchestrator probe `m7gvuz` adds. For each, record whether it invokes a model today, what its cost profile is (one short question versus a long execution), and whether a cheaper model would materially change its output quality.
  THE DISCRIMINATING QUESTION IS EXTENSIBILITY, and the item states it precisely: "A role vocabulary is smaller and easier to validate; an action vocabulary does not need extending every time a new action appears." So the evidence needed is how OFTEN a new model-invoking action appears. Count them historically if you can: if new actions are rare, a validated role enum is better; if they arrive with most Sets, an open action key is better. Do not assert a preference without that count.
  NOTE THE PROBE IS NOT YET REAL. `m7gvuz` is unexecuted and carries its own blocking questions, so the probe is a PROSPECTIVE consumer. Say so rather than counting it as an existing one, and note that if `m7gvuz` is never executed, this item loses its motivating case entirely.
  - Depends on: E-01
  - Expected outcome: a table of model-invoking actions with cost profile and quality sensitivity, plus a measured or explicitly-estimated rate at which new such actions appear; no unit chosen.
  - Execution state: pending

### Task group 2: answer the four questions with evidence

- [ ] E-03 SET OUT THE PRECEDENCE AND FALLBACK ANSWERS, which are questions 2 and 3 and are the two the repository can very nearly answer itself.
  QUESTION 2 (WHERE THE PREFERENCE IS DECLARED) HAS AN ESTABLISHED PATTERN TO FOLLOW RATHER THAN INVENT: the item notes `f2mrsw` already established a per-profile `validate` tri-state, so a precedence chain convention exists. Read it, state whether the same chain applies (per-profile setting, per-run flag, documented precedence), and say what differs for a model preference if anything does.
  QUESTION 3 (UNPROVIDABLE MODEL) HAS A STRONG DEFAULT AND THE ITEM SAYS WHY: "Failing closed on a MODEL CHOICE is probably wrong, since the work can still be done, just more expensively." Contrast this deliberately with the sandbox precedent, where `select_execution_profile` RAISES rather than degrading, because there the degradation silently removes a security boundary. A model fallback removes no boundary; it costs money. State that distinction explicitly, because a future reader who knows the sandbox rule will otherwise apply it here by analogy and fail the run.
  RECORD THE ANSWERS AS RECOMMENDATIONS, NOT AS DECISIONS. Questions 2 and 3 are agent-resolvable from existing precedent, but they only matter once question 1 is answered, so they are inputs to the maintainer's ruling rather than independent commitments.
  - Depends on: E-02
  - Expected outcome: a written recommendation for the declaration site (following `f2mrsw`'s precedence chain) and for the unprovidable-model case (warn and fall back), with the sandbox contrast stated so the analogy is not misapplied.
  - Execution state: pending

- [ ] E-04 ANSWER QUESTION 4 (CACHE VALIDITY ACROSS A PREFERENCE CHANGE) FROM THE DATA THAT ALREADY EXISTS, since this is the one question with a concrete substrate.
  THE ITEM POINTS AT IT: "The probe verdict store already records the answering model for exactly this reason, so the data to make that judgment exists." Verify that claim against `m7gvuz`/`8tgg6g`'s design rather than trusting it, since both are unexecuted and the store may not exist yet.
  THE QUESTION IS WHETHER A VERDICT PRODUCED UNDER MODEL A STAYS VALID WHEN THE PREFERENCE CHANGES TO MODEL B. State the options plainly: invalidate on model change (safe, expensive, and defeats the caching that makes the probe free), keep and record (cheap, and lets a reader distrust a weak verdict, which is what the maintainer already chose for the probe), or keep only when the new model is stronger (requires a model ranking the repository does not have and probably should not invent).
  NOTE THE MAINTAINER ALREADY RULED ON THE ANALOGOUS CASE. The 2026-09-07 ruling for `m7gvuz` was to use the run's model and RECORD which one answered, so a future reader can distrust the verdict. That is the "keep and record" option, already chosen once, which is strong evidence for the general answer without settling it.
  - Depends on: E-03
  - Expected outcome: the three cache options with their costs, a verification of whether the answering-model record actually exists yet, and a recommendation anchored to the maintainer's existing ruling; no cache behavior changed.
  - Execution state: pending

### Task group 3: implement only what the ruling authorizes

- [ ] E-05 IMPLEMENT THE DECISION, WHICH MAY LEGITIMATELY BE "RECORD IT AND BUILD NOTHING YET". Three outcomes are all valid and the plan must not prefer a build.
  UNDER A ROLE VOCABULARY: add a validated role enum to `runner_profiles`' per-profile schema, resolved at run creation. Note `ALLOWED_PROFILE_KEYS` and `_reject_unknown_keys` mean an unknown key is REFUSED, so the field must be declared, not conventional; and `SCHEMA_VERSION` plus `_on_disk_version` mean an OPTIONAL addition must not invalidate an existing on-disk config, which a test must prove.
  UNDER AN ARBITRARY ACTION KEY: the same schema work but with an open map rather than an enum, and correspondingly weaker validation, so the plan must say what catches a typo (a preference for a misspelled action would silently never apply).
  UNDER "DECIDE AND DEFER": write the decision into a spec so the next action that wants a cheap model finds an answer instead of re-deriving this analysis, and change no code. This is a REAL outcome, not a failure: the item filed itself precisely because the design was undecided, and the cost bound (verdicts cached against a content digest, so waste scales with plan churn) is what makes deferral affordable.
  DO NOT TOUCH `kgpptv` UNDER ANY OUTCOME. Whether it should be executed, re-scoped or retired is the maintainer's call inside OQ-01; an agent editing or retiring an approved plan on its own reading would be deciding that question by action.
  - Depends on: E-04
  - Expected outcome: exactly what OQ-01's answer authorizes, with the deferral outcome producing a recorded spec decision and no code change; `kgpptv` untouched in every case.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THERE IS NO ROLE CONCEPT: zero `role` occurrences in `runner_profiles.py`, re-verified at HEAD.
- ONE IDENTITY PER RUN: `resolve_launch_profile` (`oc_runipd.py:2702`, MOVED from the item's cited `:2660`) resolves a single launch identity for the whole run.
- `kgpptv` IS APPROVED AND UNEXECUTED, covers only the VERIFIER role, and a general mechanism would likely subsume it.
- `kgpptv`'s OC-ONLY PREMISE IS NOW FALSE: `tm2cz8` registers the agy host, and `ybkmzp` explicitly warns that `kgpptv`'s F-12 is falsified and "its scope should be re-read rather than trusted".
- A PRECEDENCE-CHAIN PRECEDENT EXISTS: `f2mrsw` established the per-profile `validate` tri-state, so question 2 follows a convention rather than inventing one.
- THE SCHEMA REFUSES UNKNOWN KEYS (`ALLOWED_PROFILE_KEYS`, `_reject_unknown_keys`) and is VERSIONED (`SCHEMA_VERSION`, `_on_disk_version`), so any field must be declared and must not invalidate an existing config.
- THE SANDBOX PRECEDENT MUST NOT BE APPLIED BY ANALOGY: `select_execution_profile` RAISES rather than degrading because degradation there removes a security boundary. A model fallback removes no boundary and costs money instead.
- THE MOTIVATING CONSUMER IS PROSPECTIVE: `m7gvuz` is unexecuted and carries its own blocking questions, so the probe does not exist yet.
- THE COST IS BOUNDED, which is why this is non-urgent: probe verdicts are cached against a content digest, so waste scales with plan churn, not run count.
- Both runner files are under concurrent edit; re-locate every symbol by name. Suite runs BARE.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the gap is real | `runner_profiles` has ZERO `role` occurrences and `resolve_launch_profile` resolves one identity per run, so no action can declare a model preference. | grep at HEAD; `oc_runipd.py:2702` |
| F-2 | HIGH | the item's own citation is already stale | It cites `resolve_launch_profile` at `:2660`; it is now at `:2702`, a 42-line drift. This is the concrete case for re-locating by symbol. | read at HEAD |
| F-3 | HIGH | `kgpptv` covers one role, not the mechanism | It gives the VERIFIER turn its own profile and is `approved`/unexecuted, so an arbitrary action still has nowhere to declare a preference; a general mechanism would likely subsume it. | `kgpptv`'s status and scope |
| F-4 | HIGH | a `kgpptv` premise is now FALSE | It was authored believing the profile mechanism is oc-only (its F-12). `tm2cz8` registers the agy host and `ybkmzp` warns explicitly that its scope "should be re-read rather than trusted". | `ybkmzp`'s Deferred section; `tm2cz8` F-12 |
| F-5 | HIGH | this is a decision, by the item's own framing | "filed as a BACKLOG ITEM rather than an IPD, because it is a decided-but-unscoped design question, not a task list." Graduating it as a build plan would invent four reserved answers. | the item's opening ruling |
| F-6 | MEDIUM | `m7gvuz`'s review confirms nothing is reusable | Round 2 re-verified zero `role` occurrences and recorded that an executor reading its OQ-01 as "reuse the per-role resolver" would "find nothing to reuse". | `m7gvuz` F-10 |
| F-7 | MEDIUM | the motivating consumer does not exist yet | `m7gvuz` is unexecuted with its own blocking questions. If it is never executed, this item loses its motivating case. | `m7gvuz`'s status and OQs |
| F-8 | MEDIUM | the cost bound makes deferral affordable | Verdicts are cached against a content digest, so on a stable corpus the probe costs nothing after the first pass and waste scales with plan churn. | the item's own cost note; `8tgg6g`'s design |
| F-9 | MEDIUM | a precedence precedent exists | `f2mrsw`'s per-profile `validate` tri-state established the convention question 2 should follow. | `f2mrsw`, executed |
| F-10 | MEDIUM | the schema constrains any field | Unknown keys are REFUSED and the schema is versioned, so a preference field must be declared and must not invalidate an existing on-disk config. | `ALLOWED_PROFILE_KEYS`, `_reject_unknown_keys`, `SCHEMA_VERSION`, `_on_disk_version` |
| F-11 | LOW | the wrong precedent is nearby and tempting | `select_execution_profile` RAISES on an unavailable profile because degradation removes a security boundary. Applying that to a model choice would fail runs for no safety gain. | `host_sandbox_profile.select_execution_profile` |

## Proposed changes (ordered, validatable)

1. Re-measure the gap, the overlap and the cross-host change by symbol, re-scoping if `kgpptv` has executed (E-01).
2. Enumerate every model-invoking action with its cost profile and the rate at which new ones appear (E-02).
3. Recommend the declaration site from `f2mrsw`'s precedent and the fallback behavior, stating the sandbox contrast (E-03).
4. Answer the cache-validity question from the answering-model record, anchored to the maintainer's existing ruling (E-04).
5. Implement exactly what the ruling authorizes, including "record it and build nothing yet" (E-05).

## Deferred / out of scope (with reason)

- BUILDING A ROUTING MECHANISM BEFORE THE UNIT IS CHOSEN. The item reserved question 1 and it determines the schema shape, the validation strength and whether an approved plan should be executed or retired. Building first would force that answer by implementation.
- TOUCHING `kgpptv` IN ANY WAY. Its fate is inside OQ-01. An agent re-scoping or retiring an approved plan on its own reading would decide the maintainer's question by action. Note independently that its oc-only premise is already falsified and needs re-reading, which is a REPORT, not a licence to edit.
- EXECUTING OR CHANGING `m7gvuz`. It is the prospective consumer with its own blocking questions, and the maintainer already ruled how the probe picks a model in the interim (use the run's model, record which answered).
- A MODEL RANKING OR STRENGTH ORDER. Question 4's "keep only when the new model is stronger" option needs one, and inventing a ranking would embed a fast-moving external judgement in durable config. Named as an option and recommended against.
- PER-ACTION ROUTING ON THE AGY HOST specifically. `tm2cz8` makes the registry cross-host, but agy still has no `launch_profile` provenance record (`ybkmzp` F-10 records the gap), so per-action routing there depends on work that belongs to the registry consolidation.
- CHANGING THE PROBE'S CACHE BEHAVIOR. `8tgg6g` owns the verdict store; E-04 answers a question ABOUT cache validity without changing it.
- THE `validate` TRI-STATE. `f2mrsw` shipped it and `kgpptv`'s fence forbids touching it; this plan reads it as precedent only.

## Scope check

- Over-scope: none. Under two of three outcomes this plan writes a decision record and at most one optional schema field.
- Scope-Paths justification: `agent_workflows/runner_profiles.py` holds `ALLOWED_PROFILE_KEYS`, `parse_profile`, `_reject_unknown_keys` and `SCHEMA_VERSION`, which is where a role or action field must be declared and validated under the two building outcomes (E-05); `.aw/records/specs` is where the recorded decision lands under EVERY outcome, and is the whole deliverable under "decide and defer"; `tests/test_runner_profiles.py` is the existing schema suite that must prove an existing on-disk config still loads. NO driver module is in scope, deliberately: resolving a preference into a turn's argv is the NEXT plan's work and both runner files are under concurrent edit. Under the deferral outcome `runner_profiles.py` and the test file may finish UNCHANGED, which is the expected outcome and not an incomplete item.
- Under-scope, stated rather than left as `none`: this plan does not build routing, does not touch `kgpptv` or `m7gvuz`, does not invent a model ranking, does not address agy's missing provenance record, does not change the probe's cache, and does not touch the `validate` tri-state. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count. Under the deferral outcome the suite should be untouched, and that is the expected result rather than a missing test.
- THE ACTION INVENTORY (E-02) pasted, with per-action cost profile and quality sensitivity, and the measured or explicitly-estimated rate at which new model-invoking actions appear.
- THE FOUR SYMBOL MEASUREMENTS (E-01) pasted, including where `resolve_launch_profile` now lives and `kgpptv`'s current status.
- Under a building outcome: proof that an EXISTING on-disk `runner_profiles` config still loads unchanged (the schema is versioned and `save` consults `_on_disk_version`), plus a test that an unknown key is still REFUSED so the new field did not loosen validation.
- Under a building outcome: a test that a preference naming an unprovidable model WARNS and falls back rather than failing the run, with the sandbox contrast noted in the test's comment.
- Under the deferral outcome: the spec decision record itself, and NEGATIVE proof that no code changed (`git status` over `agent_workflows/`).
- NEGATIVE PROOF that `kgpptv` was not modified under any outcome.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

THE DECISION RECORD IS THE PRIMARY DELIVERABLE and must live in a spec under `.aw/records/specs`, not only in this plan's prose, because the whole point is that the NEXT action wanting a cheap model finds an answer instead of re-deriving this analysis. That is true under all three outcomes, including deferral: "we considered per-action routing and deliberately did not build it, for these reasons" is exactly the kind of decision this repository loses when it lives only in a closed item.

The record must state the unit chosen (or that none was), the declaration site and precedence, the unprovidable-model behavior WITH the sandbox contrast, the cache-validity answer, and the consequence for `kgpptv`. That last one is the load-bearing part for a reader: an approved plan's fate should be findable from the decision that affects it.

`runner_profiles.py`'s module docstring asserts version-1 registry facts that `tm2cz8` is already correcting (its F-12 lists four such statements). Do NOT correct them here: that is `tm2cz8` E-07's declared, comment-only work, and duplicating it would collide with an approved plan at the finalize scope gate. If `tm2cz8` has not yet executed, note the overlap as a finding.

No existing spec is amended by this plan. If the executor finds spec text asserting that per-role or per-action model selection EXISTS, that is a false claim; declare the spec file in `Scope-Paths` before editing it, per the spec-amendment rule, and record the reason here.

## Open questions

### OQ-01: Is the unit a ROLE, an arbitrary named ACTION, or neither yet?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT AGENT-RESOLVABLE, AND IT DECIDES AN APPROVED PLAN'S FATE, which is what makes it blocking rather than merely first. The item reserved it deliberately and stated the trade: "A role vocabulary is smaller and easier to validate; an action vocabulary does not need extending every time a new action appears." The consequence reaches beyond this plan: a general mechanism "would likely SUBSUME `kgpptv`", which is `approved` and unexecuted, so the answer determines whether that plan should be executed as-is, re-scoped, or retired. An agent choosing the unit would settle that by implication. A third answer is legitimate and may be the right one: record the analysis and build nothing until a second real consumer exists, since the only motivating consumer (`m7gvuz`) is itself unexecuted and the cost is bounded by caching. E-01 to E-04 gather the evidence; nothing in E-05 may be built until this is answered.

### OQ-02: Where should the preference be declared, and with what precedence?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: FOLLOW `f2mrsw`'s ESTABLISHED CHAIN rather than inventing one, i.e. a per-profile setting with an optional per-run override and a documented precedence. The item points at this precedent itself ("`f2mrsw` already established a per-profile `validate` tri-state, so a precedence chain convention exists to follow rather than invent"), and consistency matters more than the specific ordering here: an operator who has learned how `validate` resolves should not have to learn a second, different rule for models. This is non-blocking because it only becomes actionable once OQ-01 names the unit, and because it changes no behavior on its own.

### OQ-03: What happens when a preference names a model the host cannot provide?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: WARN AND FALL BACK TO THE RUN'S MODEL; DO NOT FAIL THE RUN. The item's own reasoning is correct and worth preserving verbatim in the decision record: "Failing closed on a MODEL CHOICE is probably wrong, since the work can still be done, just more expensively." The reason this needs stating rather than being obvious is that the NEAREST precedent points the other way: `select_execution_profile` RAISES on an unavailable hardened profile rather than degrading, and a reader who knows that rule will apply it by analogy. The distinction is what degradation COSTS. There, silently running unsandboxed removes a security boundary the caller believes exists; here, running on the run's model removes no boundary and costs money, which is visible in the run record. So the fallback must be LOUD (recorded in the run state, not merely printed) but must not refuse.

### OQ-04: Does a cached artifact produced under model A stay valid when the preference changes to model B?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: KEEP IT AND RECORD THE ANSWERING MODEL, which is the option the maintainer ALREADY CHOSE for the analogous case. The 2026-09-07 ruling on `m7gvuz` OQ-01 was to use the run's resolved model and record which model answered with each cached verdict "so a future reader can distrust a verdict produced by a weak model". Invalidating on model change is safe but defeats the caching that makes the probe free, which is the same caching that bounds this item's whole cost. Keeping only when the new model is "stronger" needs a model ranking the repository does not have; embedding a fast-moving external judgement in durable config would age badly and is recommended AGAINST. E-04 must still verify that the answering-model record actually exists, since `8tgg6g` is unexecuted and the store may not be built yet.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the ACTUAL output for all four measurements: the `role` grep over `runner_profiles.py`, `resolve_launch_profile`'s current location found BY SYMBOL, `kgpptv`'s `- Status:` and directory, and whether `tm2cz8` has executed. State the line-number drift you observed against this plan's `:2702` citation. If `kgpptv` has executed or a role concept has appeared, paste the re-scope and do not proceed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the action inventory table. It must name, per action, whether it invokes a model today, its cost profile, and its quality sensitivity. Paste the measured or explicitly-estimated rate at which new model-invoking actions appear, with the basis for the estimate. Confirm in one sentence that `m7gvuz`'s probe is recorded as PROSPECTIVE rather than counted as existing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the declaration-site recommendation with the `f2mrsw` precedence chain it follows, quoting the existing convention. Paste the unprovidable-model recommendation AND the sandbox contrast, quoting `select_execution_profile`'s raise-not-degrade behavior and stating in one sentence why it does not apply. Confirm both are recorded as recommendations, not commitments.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the three cache options with their costs. Paste evidence of whether the answering-model record ACTUALLY EXISTS yet (checking `8tgg6g`'s status and any built store), rather than trusting the item's claim that it does. Paste the maintainer's `m7gvuz` ruling as the anchor, and state the recommendation. Confirm no cache behavior was changed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: state which OQ-01 outcome the maintainer chose and paste the resulting change. Under a building outcome: paste the schema diff, a test proving an existing on-disk config still loads, and a test proving an unknown key is still refused. Under deferral: paste the spec decision record and `git status` over `agent_workflows/` proving no code changed. UNDER EVERY OUTCOME: paste NEGATIVE proof that `kgpptv` was not modified, and the BARE `python3 -m pytest` summary lines before and after with the failure-set delta stated.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES A BLOCKING OPEN QUESTION AND THAT IS THE POINT, not an oversight. The item filed itself as a backlog item rather than an IPD precisely because the design was undecided, and OQ-01's answer determines whether an APPROVED plan (`kgpptv`) should be executed, re-scoped or retired. The pre-execution checkpoint refuses a plan holding an unresolved `Blocking: yes` question, which is the correct mechanism to hold task group 3.

E-01 THROUGH E-04 ARE EVIDENCE-GATHERING AND ARE SAFE TO PERFORM FIRST. They change no code and produce exactly the material a maintainer needs to answer OQ-01. E-05 is conditional, and "record the decision and build nothing yet" is a legitimate completed outcome given that the only motivating consumer is itself unexecuted and the cost is bounded by content-digest caching.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Re-locate every symbol by NAME, never by the line numbers cited here: this item's own citation was already 42 lines stale at graduation, and both runner files are under concurrent edit by live runs. Do NOT modify, re-scope or retire `kgpptv` or `m7gvuz`. Do NOT correct `runner_profiles.py`'s version-1 registry docstrings, which are `tm2cz8` E-07's declared comment-only work. Paste ACTUAL command output; never claim a measurement you did not run. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence. Under the deferral outcome the plan still finalizes normally: the deliverable is then the recorded spec decision, which is a real outcome and not a withdrawal.
