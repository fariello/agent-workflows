# IPD: Read the per-attempt model in analytics and the dashboard so coverage reaches the consumers

- Date: 2026-09-30
- Kind: child
- Concern: ORDERS 01 AND 02 WRITE A PER-ATTEMPT MODEL THAT NOTHING READS, so the backlog item's actual ask ("so run analytics can compare models") stays unmet until a consumer is repointed. Three specific consumers are wrong today, each measured. FIRST, `run_dashboard.collect_rows` computes ONE model per run and stamps it onto every row, so a verifier row reports the EXECUTOR's model: executed at authoring against a run whose `options` carried `model: provA/executor-model` and `verify_model: provB/verifier-model`, the dashboard returned `role=main model=provA/executor-model` AND `role=verify model=provA/executor-model`. SECOND, `run_analytics` gets the phase grains right (`Phase.VERIFY` reads `_verify_model_of`) but its ATTEMPT-grain `Fact` takes the run-level executor model unconditionally, so the finest grain is the least accurate. THIRD, `run_analytics_statistics.model_comparison` REFUSES below `MODEL_COVERAGE_THRESHOLD` of 0.80 and its sole production caller passes a LITERAL EMPTY LIST (`stats_mod.model_comparison([])` in `run_analytics_cli`), so the comparison the item wants is not merely refused for want of coverage, it is never fed any attempts at all: executed at authoring, that call returns `Verdict.REFUSED` with `sample_size=0` and "coverage 0.0000", while the same function fed 30 attempts each carrying a model returns `Verdict.COMPUTED`.
- Scope: Make the three consumers read the per-attempt fields Orders 01 and 02 produce, falling back to today's run-level fields so no existing run loses attribution. Concretely: a per-row model in `run_dashboard` so a verifier row reports the verifier's model and the `(unrecorded, <host>)` label is reached only when an attempt genuinely has nothing; an attempt-grain `Fact.model` read from the attempt; and a real attempt population fed to `model_comparison` in place of the empty literal, with the coverage it actually achieves reported rather than asserted. EXCLUDES changing `MODEL_COVERAGE_THRESHOLD` (0.80 is a declared judgement, and moving it to make an arm compute would be reverse-engineering a threshold to a desired answer). EXCLUDES back-filling history, so the honest result is that coverage improves for FUTURE runs and the refusal may legitimately still fire on a corpus dominated by old runs. EXCLUDES the privacy allowlist widening for any key that is not needed, and states which one IS needed.
- Scope-Paths: agent_workflows/run_dashboard.py, agent_workflows/run_analytics.py, agent_workflows/run_analytics_statistics.py, agent_workflows/run_analytics_cli.py, tests/test_run_dashboard.py, tests/test_attempt_model_consumers.py, docs/run-analytics.md
- Item-Dependencies: executed:czut8j
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- From-Backlog: 7yz545
- Set: attmodel
- Order: 3
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: r5fk4k

## Workflow history
- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 all FIXED. F-01 and F-02 reproduced end to end against real code rather than read. PR-001 (HIGH): E-02 asserted the unclaimed-session branch has no attempt to read and told the executor to document that excuse; measured, the branch recovers an existing attempt via by_item_attempt and can carry a verify role, so the F-01 defect would have survived in exactly that branch, plus the (unrecorded, host) substitution runs once per run and would leave a bare sentinel once the value went per row. PR-002 (HIGH): E-04's named population source is run grain, not attempt grain (cache entries carry run-level metric_facts; rows holds one aggregate row per run plus accumulated phase rows), so it would have published coverage on a 135-run denominator against a 179-attempt baseline, the exact incomparability OQ-02 forbids; the remedy was in the same function's existing attempt loop. PR-003 (HIGH): the dashboard emits a third role (gate-answer) so a two-role resolver guesses. PR-004: E-01 left its own one-precedence invariant as an execution-time choice permitting duplication. PR-005: an attempt-grain fact is never Phase.VERIFY, so phase-decides-role cannot select the verify chain. PR-006: vnt9it has already executed, and the test_run_flag_surface.py citation is dead (19313eed). PR-007: the docs no-dash rule is mechanically checked and feeds release_readiness.gate_docs_checks, and nothing in the plan ran it. PR-008: my own added cases tripped density advisory IPD-Z602, so E-06 was SPLIT into E-06 plus new E-08 with V-08; advisories back to 0. Suite green: 3527 passed, 2 skipped.

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `7yz545` as Order 03, the consumer half. THE SINGLE MOST IMPORTANT FINDING HERE IS NOT ABOUT MODELS AT ALL: `model_comparison`'s only production caller passes `[]`, so the analysis the item wants would refuse at 0.0000 coverage even on a corpus where every attempt carried a model. Fixing the producer without fixing that call would have delivered the field and no answer, which is why this plan exists as its own order rather than as a tail on Order 01. DEPENDS ON ORDER 01 ONLY, NOT ON ORDER 02, and that is deliberate: Order 01 supplies the frozen per-attempt field this plan's fallback chain is built on, while Order 02's observation is an OPTIONAL top tier that this plan reads when present and does not require. So Orders 02 and 03 may execute in either order or in parallel lanes.
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the model a consumer reports be the model that attempt actually ran under, and make the model
comparison the backlog item asks for receive a real population instead of an empty list.

The test of success is that the two-model run measured in F-01 reports TWO models across its rows, and that
`model_comparison` reports its coverage from a real population, whatever that coverage turns out to be.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one precedence, defined once, so three consumers cannot disagree

- [ ] E-01 DEFINE THE CONSUMER-SIDE PRECEDENCE ONCE AND STATE IT IN FULL, BECAUSE THREE READERS MUST NOT EACH INVENT ONE. The chain, strongest evidence first: (1) the attempt's OBSERVED host model (`attempt["host_model"]`, from Order 02) when present, because it is what the host reports it ran; (2) the attempt's FROZEN model (`attempt["model"]`, from Order 01), which is what the driver asked for; (3) for a VERIFY-role row or fact, the attempt's `verify_model`/`host_model` verify twin before either of the above, because a verify row that falls back to the executor's model is the exact defect F-01 measures; (4) the run-level `options.model` / `options.explicit_model`; (5) the run-level `options.cost_attribution.model` (and the `verify_` twin for a verify row); (6) nothing, reported as unrecorded. Tiers 4 and 5 are TODAY'S behavior and are preserved verbatim so no existing run loses attribution. Implement this as ONE function, and put it where both consumer families can reach it without a new import cycle: `run_dashboard` imports nothing from `run_analytics` today and vice versa, so if no existing shared home fits, state that and duplicate the ORDER as data (a single tuple of accessors) rather than duplicating the LOGIC in two hand-written if-chains. Whichever is chosen, it must be a pure function of an attempt mapping plus a run-state mapping plus a role, and it must return the model AND a source label naming the tier that answered.
  - THE ROLE VOCABULARY IS NOT TWO VALUES, AND A TWO-VALUE SIGNATURE WILL SILENTLY MIS-RESOLVE REAL ROWS (F-08, HIGH). This item speaks only of a VERIFY role and an EXECUTE role, but the dashboard already emits more: `_SESSION_NAME_RE` captures a trailing role segment, and measured against the shipped fixture `tests/test_run_dashboard._write_run` a run emits `role` values `main`, `verify` AND `gate-answer`, with `recovery` reachable by the same pattern. A function accepting only two roles forces every other row into one of them, and `gate-answer` resolved as `execute` is a GUESS rather than a reading. So: accept a role vocabulary that includes at least `main`/`execute`, `verify`, and an explicit OTHER case, and define the OTHER case as resolving through the EXECUTE chain while reporting a source label that does not claim verify provenance. State the chosen vocabulary in the docstring, because E-02 and E-03 both call this and must pass the same values.
  - NAME THE HOME, DO NOT LEAVE IT AS A BRANCH FOR THE EXECUTOR (F-09, MEDIUM). This item offers "one function" or "duplicate the ORDER as data" without deciding, which leaves the Set's single most load-bearing invariant (three readers, one precedence) to an execution-time coin flip, and the fallback branch explicitly permits DUPLICATION, which is what the item's own first sentence exists to prevent. Measured: `run_dashboard` imports nothing from `run_analytics*` (0 matches) and `run_analytics` imports nothing from `run_dashboard`, so there is genuinely no existing shared home between them; but `run_analytics_schema` is already imported by `run_analytics` and is a pure dataclass/vocabulary module with no runner dependency, and `run_dashboard` importing one pure helper from it introduces no cycle. PREFER a single function in one module both import. If the executor finds that import genuinely unacceptable, they must say WHY with the measured import graph and may then fall back to the shared accessor tuple, but a hand-written second if-chain is REFUSED outright.
  - Depends on: none
  - Expected outcome: one function (or, with a stated and measured reason, one shared accessor tuple) exists in a NAMED module, with the chosen role vocabulary in its docstring; a pasted transcript resolving all six tiers plus a malformed attempt, showing the tier label for each; plus a pasted resolution for a `gate-answer` row showing which chain answered and which label it carries.
  - Execution state: pending

- [ ] E-02 MAKE THE DASHBOARD'S MODEL PER-ROW INSTEAD OF PER-RUN. `run_dashboard.collect_rows` computes `model, model_source = _run_model(state)` once per run, applies the `(unrecorded, <host>)` per-host label, and stamps the result into the `base` dict at two construction sites (the attempt-claimed one and the unclaimed-session-file fallback), from which `_row_from_stats` copies it into every row it builds. Change it so the VERIFY row resolves with the verify role through E-01 while the MAIN row resolves with the execute role, and so an attempt carrying its own model prefers it over the run-level value. KEEP THE `(unrecorded, <host>)` LABELLING EXACTLY AS IT IS, including its per-host suffix and its stated reason ("so an unknown OpenCode model never pools with an unknown Antigravity one"), and keep `_normalize_model`'s prefix stripping applied so a row's displayed value stays comparable across hosts. DO NOT change `COLUMNS`, the browser payload shape, or `DASHBOARD_SCHEMA_VERSION`: this change alters the VALUE in an existing `model`/`model_source` column and adds no column, so the schema is untouched. The disposable per-file stats cache stores token/cost figures per session FILE and no model at all (verified at review), so it needs no invalidation either.
  - THE ITEM'S SITE COUNT AND ITS CLAIM ABOUT THE UNCLAIMED BRANCH ARE BOTH WRONG, AND THE SECOND IS THE DEFECT (F-07, HIGH). As authored this item is headed "A THREE-SITE CHANGE AND MUST HIT ALL THREE" while naming only TWO sites, so an executor cannot tell what the third is. Worse, it asserts that the unclaimed-session-file branch "has no attempt to read, so it legitimately keeps the run-level value" and instructs that this be written into a comment. Measured at review, that is FALSE in the case that matters: that branch parses the session filename with `_SESSION_NAME_RE`, derives `id6` and attempt `number` from it, and does `base = by_item_attempt.get((id6, number))`, so when an attempt record EXISTS but its log was not claimed (a differently-suffixed session file, which the shipped fixture exercises with `-gate-answer`) the branch reuses that attempt's `base` and therefore HAS an attempt to read. It also derives `role` from the same filename and can yield `verify` (both `...-attempt-1-verify.jsonl` and `...-verify-attempt-1.jsonl` match), so an unclaimed VERIFY session file would keep the EXECUTOR's model, which is precisely the defect F-01 measures, surviving in the one branch this item told the executor to leave alone. SO: the three sites are (1) the `by_item_attempt` `base` built in the attempt loop, (2) the verify-row resolution for that attempt, and (3) the unclaimed-session branch, which MUST resolve per-row using the `base` it recovered from `by_item_attempt` when one exists and its filename-derived role. Only the genuinely synthesized `base` (the `if base is None` arm, where no attempt record was found) legitimately keeps the run-level value; say THAT in the comment, not the broader claim.
  - RESOLVE THE UNRECORDED LABEL PER ROW, NOT ONCE PER RUN (F-07, same site). Today `if model == UNRECORDED: model = "(unrecorded, {host})"` runs ONCE on the run-level value before any row exists. Once the value is per row, that substitution must move to where each row's value is known, or a row whose own attempt resolves a model will be fine while a row that resolves nothing will carry a bare `UNRECORDED` sentinel instead of the labelled form, silently changing an output the shipped test `test_unrecorded_model_is_labeled_per_host` asserts over EVERY row of its run (`{r["model"] for r in rows} == {"(unrecorded, oc)"}`). That test is the regression guard for exactly this mistake and must pass unedited.
  - Depends on: E-01
  - Expected outcome: the F-01 two-model run re-measured through `collect_rows`, pasted, showing `role=main` and `role=verify` reporting DIFFERENT models; a pasted run with no per-attempt fields at all, showing rows identical to today's output with the `(unrecorded, <host>)` label intact; and a pasted run carrying an UNCLAIMED verify session file for an attempt that exists, showing that row resolving the VERIFIER's model rather than the executor's.
  - Execution state: pending

### Task group 2: the analytics grains and the arm that refuses

- [ ] E-03 READ THE ATTEMPT'S OWN MODEL ON THE ATTEMPT-GRAIN FACT IN `run_analytics.build_run_facts`. Today that function computes `model = _model_of(state)` and `verify_model = _verify_model_of(state, model)` ONCE per run and passes the run-level `model` into every `Grain.ATTEMPT` fact, so the finest grain carries the coarsest attribution. Resolve per attempt through E-01 instead, with the attempt's `phase` deciding the role (the function already computes `attempt_phase`, distinguishing `Phase.RECOVERY`). Leave the PHASE-grain facts alone: they already read `_verify_model_of` for `Phase.VERIFY` and are correct. Preserve `_model_of` and `_verify_model_of` as the run-level tiers rather than deleting them, because `Grain.RUN` and `Grain.IPD` facts legitimately want a run-level answer and because `tests/test_run_analytics.py::ModelAttributionTests::test_case_7_cost_attribution_key_agreement` pins `run_analytics._COST_ATTRIBUTION_KEY == runner_shared.COST_ATTRIBUTION_KEY` and must keep passing. CHECK THE VERSION CONSTANTS AND SAY WHICH MOVED: `INGEST_SCHEMA_VERSION` is documented as bumped "when the :class:`RunFacts` SHAPE changes" and `FACT_SCHEMA_VERSION` when the fact schema does; this change alters a fact's VALUE and adds no field, so state the finding either way rather than bumping reflexively or silently. NOTE WHERE EACH ONE LIVES, because they are in DIFFERENT modules and only one is in this plan's `Scope-Paths` (measured at review: `INGEST_SCHEMA_VERSION` is defined in `run_analytics`, which is declared; `FACT_SCHEMA_VERSION` is defined in `run_analytics_schema`, which is NOT). If the verdict is that `FACT_SCHEMA_VERSION` must move, that is an out-of-scope edit to make and JUSTIFY, not a reason to skip the verdict.
  - AN ATTEMPT-GRAIN FACT IS NEVER `Phase.VERIFY`, SO "THE ATTEMPT'S PHASE DECIDES THE ROLE" UNDER-SPECIFIES THE ONE CASE THIS SET EXISTS FOR (F-10, MEDIUM). Measured: `attempt_phase = Phase.RECOVERY if is_recovery else item_phase`, and `_phase_of` returns only `Phase.REVIEW` (for `action == "review"`) or `Phase.EXECUTE`. So the attempt-grain phase is drawn from `{review, execute, recovery}` and the VERIFY role is unreachable through it, which means a phase-driven role never selects the verify chain and the attempt-grain fact keeps taking an executor-side model. That is CORRECT for this fact (an attempt-grain fact's usage is the executor turn's `cost`/`tokens`, and the verifier's spend is carried separately), so the fix is to SAY SO rather than to invent a verify attempt fact: map `review` and `execute` and `recovery` all to E-01's EXECUTE chain, state in a comment that an attempt-grain fact is deliberately executor-side and that the verifier's model stays on the PHASE-grain `Phase.VERIFY` fact which already reads `_verify_model_of`, and do NOT add a second attempt-grain fact for the verify phase (that would change the fact COUNT and therefore the `RunFacts` shape, which is the one thing `INGEST_SCHEMA_VERSION` exists to track). V-03 now requires that comment quoted, so the decision is recorded rather than implied.
  - Depends on: E-01
  - Expected outcome: the F-01 run's pasted fact list showing the ATTEMPT-grain fact's model resolved from the attempt and the PHASE-grain facts unchanged; a written verdict on each version constant naming its defining module and whether it moved; the quoted comment recording that an attempt-grain fact is deliberately executor-side; the pasted `tests/test_run_analytics.py` run showing `ModelAttributionTests` still green.
  - Execution state: pending

- [ ] E-04 FEED `model_comparison` A REAL ATTEMPT POPULATION INSTEAD OF THE EMPTY LITERAL, AND REPORT WHATEVER COVERAGE RESULTS. `run_analytics_cli` calls `stats_mod.model_comparison([])` under a comment reading "Model comparison refusal (under 80% coverage)", which cannot be true of an empty list: it refuses at 0.0000 for want of any input. Build the attempt population so each element carries at least `model` and `cost`, which is exactly what `model_comparison` reads.
  - THE SOURCE THIS ITEM NAMES CANNOT YIELD ATTEMPT GRAIN, AND USING IT WOULD SILENTLY REDEFINE THE DENOMINATOR OQ-02 FORBIDS REDEFINING (F-11, HIGH). As authored the item says to build the population "from the same entries the surrounding analyses already use (the module builds `costs`, `wall_times` and `token_totals` from `agg_rows`)". Measured at review, neither source is attempt grain. `entries` are analytics CACHE entries whose `metric_facts` (`run_analytics_query._facts_of`) are RUN-level (`cost`, `wall_seconds`, `token_total`, `model`, `host_kind`, `status`) and carry no attempt list at all. `rows` is built with exactly two shapes, a `phase: "aggregate"` row per run and up to four per-run PHASE rows (`review`/`execute`/`verifier`/`recovery`) whose attempt figures are ACCUMULATED into phase buckets by the loop over `item["attempts"]`; `agg_rows` then selects the aggregate ones. So passing either would hand `model_comparison` run or phase records while its parameter is named `attempts`, its coverage is attempts-with-model over total attempts, and `CORPUS_BASELINE` records the comparison figure as "2 of 179 attempts" with 135 runs. A 135-denominator figure published against a 179-denominator baseline is exactly the incomparability OQ-02 says must not happen. THE REMEDY, and the executor must do this rather than reuse `agg_rows`: the per-phase block ALREADY opens each run's `state.json` and ALREADY loops `for item in s_data.get("queue", []): for att in item.get("attempts", [])`, so an attempt-grain population is constructible THERE, one element per attempt, each carrying the model resolved through E-01 and that attempt's own `cost`. Build it in that existing loop and pass it. IF that proves impossible, REPORT the limitation and leave the call refusing rather than passing run rows, which OQ-02 already requires.
  - STATE THE DENOMINATOR YOU PUBLISHED AND SAY WHETHER IT IS COMPARABLE. Whatever population is built, V-04 requires the total named; if the denominator is not attempts, that must be stated as a known incomparability with the retained baseline rather than presented as a coverage improvement. THE REFUSAL MUST REMAIN REACHABLE AND MUST NOT BE WEAKENED: `MODEL_COVERAGE_THRESHOLD` stays 0.80, the `host-default` literal stays excluded from the covered set (`str(a.get("model")).strip() != "host-default"`), and if the real coverage is below threshold the arm REFUSES with the real number, which is the honest outcome and is strictly better than refusing with a fabricated 0.0000. UPDATE THE COMMENT to say what the call now does. Also reconcile the function's own caveat text, which states "coverage improves for FUTURE runs only (Order 04 records model identity per file)": that clause names a different plan's mechanism and, after this Set, is incomplete rather than wrong, so extend it to name the per-attempt field as the other future-coverage source.
  - Depends on: E-01
  - Expected outcome: pasted `model_comparison` output from the real caller on this box, showing a real `observed_coverage` and `attempts_with_model` against a named denominator, with the verdict (REFUSED or COMPUTED) reported as measured and not as hoped.
  - Execution state: pending

- [ ] E-05 RESOLVE THE PRIVACY BOUNDARY FOR ANY NEW LABEL BEFORE IT CAN REFUSE AN ENTRY, NAMING EXACTLY WHICH KEY NEEDS WHAT. Measured at authoring: `run_analytics_privacy.ALLOWED_METRIC_KEYS` contains `model` and `model_variant` but NOT `model_source`, and `_project_scalar("model_source", "frozen-launch")` raises `PrivacyRefusal("is a string on a key whose values are not free text")`. So a projected fact carrying a `model_source` key would be REFUSED. Two acceptable outcomes and the plan must pick one on evidence: (a) do not project the source at all, keeping it a dashboard-and-report concern (the dashboard is not privacy-projected, verified at authoring: `run_dashboard` imports nothing from `run_analytics_privacy`), which needs NO allowlist change and is the narrower act; or (b) if the source genuinely must reach a projected fact, add it to `ALLOWED_METRIC_KEYS` and `_CLOSED_VOCABULARY_KEYS` together with a test proving the new key cannot carry a path or free text, which is the discipline that module's own comment demands ("adding a key is a deliberate act: it widens the boundary, so it belongs with a test that proves the new key cannot carry a transcript, a path or a command line"). PREFER (a) unless a consumer needs it. Whichever is chosen, state the decision and the evidence; do NOT widen the allowlist speculatively.
  - Depends on: E-03
  - Expected outcome: a written decision naming (a) or (b) with its evidence; if (b), the pasted test proving the new key's value shape is constrained; if (a), a pasted projection of a real fact showing no refusal and no allowlist edit.
  - Execution state: pending

### Task group 3: prove it, and prove nothing old broke

- [ ] E-06 ADD THE NEW CROSS-CONSUMER TEST FILE `tests/test_attempt_model_consumers.py`, SEVEN BEHAVIORAL CASES, NONE READING PRODUCTION SOURCE. A NEW FILE, and the contention citation is corrected at review while the conclusion survives (F-12, LOW): `vnt9it` is NOT pending, it is already in `.aw/records/plans/executed/`, so it contends nothing; measured, FIVE other pending plans declare `tests/test_run_analytics.py` (`yumxwz` approved, `wqiofa` reviewed, `o55eli` reviewed, plus Order 00 and this plan), while `tests/test_attempt_model_consumers.py` is declared by nothing but Order 00's orchestration table. The cases: (a) the two-model run reports two models across dashboard rows; (b) the same run's ATTEMPT-grain fact takes the attempt's model; (c) an attempt whose `host_model` differs from its frozen `model` resolves to the observed one with the observation's source label, proving tier 1 beats tier 2; (d) a run with no per-attempt fields produces output identical to today's, the regression guard for every historical run; (e) `model_comparison` fed a population whose coverage is deliberately below 0.80 still REFUSES, with its real coverage in the result; (f) an UNCLAIMED verify session file belonging to an attempt that EXISTS resolves the VERIFIER's model, the branch F-07 found this plan had told the executor to skip; (g) a row whose own resolution yields nothing still carries the `(unrecorded, <host>)` label rather than a bare sentinel, the regression the per-row move can silently cause. SHOW ONE CASE RED FIRST and paste both runs.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: `tests/test_attempt_model_consumers.py` exists with all SEVEN cases green by name; the pasted RED run proving non-vacuity and the restored green.
  - Execution state: pending

- [ ] E-08 KEEP THE THREE SHIPPED DASHBOARD MODEL TESTS GREEN AND UNEDITED, AND ADD THE PER-ROW CASE BESIDE THEM. SPLIT OUT OF E-06 AT REVIEW: it is a different file, a different test-surface, and a different obligation (preserving shipped behavior rather than asserting new behavior), so bundling it tripped the density advisory `IPD-Z602`. `tests/test_run_dashboard.py` already carries `CollectRowsTests::test_one_row_per_session_with_roles` (asserting `main1["model"] == "some-model"`, i.e. tier 4 plus `_normalize_model`), `test_unrecorded_model_is_labeled_per_host` (asserting `{"(unrecorded, oc)"}` over EVERY row, i.e. tier 6) and `test_antigravity_run` (asserting the `cost_attribution` fallback reaches `"Flash"`, i.e. tier 5). All three must keep passing UNCHANGED, because each pins a tier this plan PRESERVES rather than replaces; an edit to any of them is the signal that a tier was broken rather than extended. ADD the new per-row case beside them, in that file, exercising a two-model run through `collect_rows`. Review measured these tests green at HEAD together with `tests/test_run_analytics.py` at `44 passed`.
  - Depends on: E-02
  - Expected outcome: the three shipped model tests pasted green BY NAME with an empty `git diff` of the regions asserting them, plus the new per-row case green by name.
  - Execution state: pending

- [ ] E-07 MEASURE THE COVERAGE DELTA ON THE EXECUTING BOX AND PUBLISH IT WITH THE BASELINE IT REPLACES, THEN RUN THE BARE SUITE. `run_analytics_statistics.CORPUS_BASELINE` carries the review-time figures this Set was filed against (`runs_with_null_options_model: 130`, `runs_with_options_model: 5`, `attempts_with_resolvable_model: 2`, `model_identity_coverage: 0.011`) and is explicitly labelled `"provenance": "review-time-snapshot"`, `"is_current": false`. DO NOT EDIT THOSE NUMBERS: they are a retained historical baseline and rewriting them would destroy the comparison. Instead MEASURE current coverage over the local corpus and report both figures side by side, stating the denominator. If this lane has no `.aw/records/runs` corpus say so explicitly and report the coverage over synthetic runs constructed for E-06 instead, naming them as such; do not present a synthetic figure as a corpus measurement. CONFIRMED AT REVIEW AND STILL TO BE RE-CONFIRMED: `.aw/records/runs` does not exist in this lane and `records/runs/` is gitignored (`.aw/.gitignore`), so the no-corpus branch is the EXPECTED path and taking it is not a shortfall. Review re-verified every `CORPUS_BASELINE` figure this item quotes and all four are exact, plus `provenance: review-time-snapshot` and `is_current: False`. Then run `python3 -m pytest` bare and paste the summary line, re-deriving the pre-change baseline at execution; review measured `3527 passed, 2 skipped, 3 warnings` with 208 deselected, all green.
  - RUN THE SHIPPED DOCS CHECKER AFTER EDITING `docs/run-analytics.md`, BECAUSE A DASH THERE FAILS A RELEASE GATE (F-13, MEDIUM). This plan's Spec/doc-sync section correctly tells the author to write the new passage with no em or en dashes, but no E-item or V-item ever checks it, and the house no-dash rule is MECHANICALLY ENFORCED for `docs/`: `agent_workflows.docs_check.check_no_unicode_dashes` (with `EM_DASH`/`EN_DASH`) runs over the docs tree, and its findings feed `release_readiness.gate_docs_checks`, a named RELEASE GATE. Measured at review, `docs_check.check_doc(Path("docs/run-analytics.md"))` returns 0 findings today, so this plan starts from a clean file and any new finding is attributable to this change. So: after the doc edit, run the checker over that file and paste the result; a nonzero finding count must be fixed before this item completes, not left for a release to discover.
  - Depends on: E-06, E-08
  - Expected outcome: the two coverage figures side by side with denominators and provenance named, or an explicit no-corpus statement plus the substitute; `CORPUS_BASELINE` shown UNEDITED (a pasted diff of that region, empty); the pasted `docs_check` result for `docs/run-analytics.md` showing 0 findings after the edit; a pasted bare `python3 -m pytest` summary line.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The suite is run BARE: `pyproject.toml` `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`. Use `-o addopts=""` for per-test counts; never `-n0`, never a second `-q`, never `-p no:randomly`.
- `run_analytics_privacy` IS A DECLARED BOUNDARY, NOT A FORMALITY: its own comment states that adding an allowlist key "widens what is persisted, so it belongs with a test proving the new field cannot carry a path, a transcript, a network address, or host identity". E-05 is written to that standard and prefers not widening it at all.
- THE ANALYTICS CACHE IS DISPOSABLE AND SELF-INVALIDATING on a `state.json` rewrite: `run_analytics_cache.source_fingerprint` folds each relevant file's size and `mtime_ns` into its digest and `_RELEVANT_TOP_LEVEL_FILES` includes `state.json`, so a run whose state gains the new attempt keys re-fingerprints automatically. That is why this plan bumps no cache version, and it is recorded so a reviewer does not ask for one.
- THE CACHE-FINGERPRINT CONTENTION WARNING IS SPENT: `vnt9it` (`eventcountbf`) HAS ALREADY EXECUTED and sits in `.aw/records/plans/executed/` (measured at review), so it contends nothing and its producer-metric-key folding is already in the tree rather than in flight. The live contention is different and is recorded instead: among PENDING plans, `agent_workflows/run_dashboard.py` is declared by three others (`z3ifg8` approved, `qvfd4l` reviewed, `o55eli` reviewed), `run_analytics_cli.py` by two (`e6f0jx` approved, `mcdvx0` reviewed), `run_analytics_statistics.py` by one (`z3ifg8` approved), and `run_analytics.py` by NONE (Order 01 mentions it only in prose and does not declare it). An executor should re-derive this at execution rather than trust the list, since the runner's lane isolation handles the merge but a human reading a conflict wants to know who else is in the file.
- THE NO-DASH RULE FOR `docs/` IS MECHANICALLY ENFORCED AND FEEDS A RELEASE GATE: `docs_check.check_no_unicode_dashes` runs over the docs tree and its findings reach `release_readiness.gate_docs_checks`. `docs/run-analytics.md` has 0 findings today, so E-07's required checker run is what keeps the plan's own style instruction from becoming a release blocker.

## Findings

Measured in this lane at HEAD by execution.

### F-01 THE DASHBOARD MIS-ATTRIBUTES EVERY VERIFIER ROW, AND ANALYTICS DISAGREES WITH IT ON THE SAME RUN

A synthetic run whose `options` carried `model: provA/executor-model`, `verify_model: provB/verifier-model`
and both `cost_attribution` twins, with one attempt carrying a main log and a verify log:

```
=== DASHBOARD rows (run_dashboard.collect_rows) ===
 role=main    model=provA/executor-model   model_source=options          cost=0.5
 role=verify  model=provA/executor-model   model_source=options          cost=0.5

=== ANALYTICS facts (run_analytics.build_run_facts) ===
 grain=attempt  phase=execute   attempt=1    model=provA/executor-model
 grain=phase    phase=execute   attempt=None model=provA/executor-model
 grain=phase    phase=verify    attempt=None model=provB/verifier-model
 grain=ipd      phase=execute   attempt=None model=provA/executor-model
 grain=run      phase=unknown   attempt=None model=provA/executor-model
```

Two defects in one transcript. The dashboard's verify row reports the executor's model, because the model is
computed once per run and stamped onto every row. And the two consumers DISAGREE about the same run's verify
phase, because analytics has `_verify_model_of` and the dashboard has no per-row equivalent.

### F-02 THE MODEL COMPARISON IS FED AN EMPTY LIST BY ITS ONLY PRODUCTION CALLER

`run_analytics_cli` contains exactly one call, `results.append(stats_mod.model_comparison([]))`, under the
comment "Model comparison refusal (under 80% coverage)". Executed at authoring:

```
verdict: Verdict.REFUSED | sample_size: 0
reason: model identity resolves for 0 of 0 attempts (coverage 0.0000), below the declared threshold 0.80; ...

with 100% coverage -> verdict: Verdict.COMPUTED | sample: 30
```

So the arm WORKS and would compute given a population; it is simply never given one. This is the load-bearing
finding of the plan: without E-04, Orders 01 and 02 could deliver perfect per-attempt coverage and this
analysis would still report 0.0000.

### F-03 THE PRIVACY PROJECTOR ADMITS `model` AND REFUSES `model_source`

Executed at authoring:

```
'model' allowed        : True
'model_source' allowed : False
'model_variant' allowed: True
project_scalar('model', 'provA/executor-model') -> provA/executor-model
project_scalar('model', 'frozen-launch')        -> frozen-launch
project_scalar('model_source', 'frozen-launch') -> REFUSED: PrivacyRefusal: key 'model_source' is a string on a key whose values are not free text
```

So a source label may travel as a `model` VALUE (it satisfies the model label pattern) but not under a
`model_source` KEY. The dashboard is unaffected either way: it imports nothing from
`run_analytics_privacy`, verified by search. E-05 decides on this evidence and prefers not widening the
allowlist.

### F-04 THE SOURCE LABEL ALREADY EXISTS IN THE DASHBOARD AND ITS VOCABULARY IS THE ONE TO EXTEND

`run_dashboard._run_model` already returns a `(model, source)` pair whose source is `"options"`,
`"cost_attribution"` or `""`, and `model_source` is already a shipped COLUMN in `COLUMNS` and a groupable
dimension in the browser asset (`DIMS.model`, the facet list, and the detail panel's `Model` row rendering
`(from <source>)`). So this plan EXTENDS an existing vocabulary with the new tiers rather than introducing a
concept, and needs no column, no payload-shape change and no `DASHBOARD_SCHEMA_VERSION` bump.

### F-05 THE THREE SHIPPED DASHBOARD MODEL TESTS EACH PIN A TIER THIS PLAN MUST PRESERVE

`tests/test_run_dashboard.py` carries `test_one_row_per_session_with_roles` (run-level `options.model`
reaching a main row as `"some-model"`, i.e. tier 4 plus `_normalize_model`),
`test_unrecorded_model_is_labeled_per_host` (the `(unrecorded, oc)` label, i.e. tier 6), and
`test_antigravity_run` (the `cost_attribution` fallback reaching `"Flash"`, i.e. tier 5). All three describe
behavior this plan keeps, so all three must pass UNEDITED; an edit to any of them is a signal that a tier was
broken rather than extended.

### F-06 NO SPEC AND NO DOC DESCRIBES THESE SURFACES, MEASURED

`grep` over `.aw/records/specs/` for `cost_attribution`, `options.model`, `run_dashboard` and `runsdash`
returns nothing, and `grep` over `docs/` for `run_dashboard` returns nothing. Spec `25kzda` Section 5.6's
machine per-item JSON object carries no model field. So no contract becomes false by this change.
`docs/run-analytics.md` DOES describe outputs a reader consumes (it explains cost provenance and why a cost
may be absent), which is why it is the one doc this plan declares: a reader who sees a model attributed per
attempt should find the precedence written down somewhere.

### F-07 REVIEW FINDING, HIGH: THE UNCLAIMED-SESSION BRANCH *DOES* HAVE AN ATTEMPT TO READ, AND THE PLAN TOLD THE EXECUTOR TO SKIP IT

E-02 as authored was headed "A THREE-SITE CHANGE AND MUST HIT ALL THREE" while naming only TWO sites, and it
asserted that the unclaimed-session-file branch "has no attempt to read, so it legitimately keeps the
run-level value", instructing that this be written into a comment. The assertion is false in the case that
matters. Measured in `run_dashboard.collect_rows`:

- the branch matches the filename with `_SESSION_NAME_RE`, deriving `id6` and the attempt `number`;
- it then does `base = by_item_attempt.get((id6, number))`, so when an attempt record EXISTS but its log was
  not claimed, it REUSES that attempt's `base` and has the attempt's own fields available;
- it derives `role` from the same filename, and that role can be `verify` (both `...-attempt-1-verify.jsonl`
  and `...-verify-attempt-1.jsonl` match the pattern, verified by executing the regex).

So an unclaimed VERIFY session file for an existing attempt would keep the EXECUTOR's model, which is exactly
the defect F-01 measures, surviving in the one branch the plan excused. Only the `if base is None` arm, which
synthesizes a `base` because no attempt record was found, legitimately keeps the run-level value. The three
sites are now stated explicitly in E-02 and case (f) in E-06 pins the behavior.

A SECOND DEFECT AT THE SAME SITE: the `(unrecorded, <host>)` substitution runs ONCE on the run-level value
before any row exists (`if model == UNRECORDED: model = "(unrecorded, {0})".format(host)`). Moving the value
per row without moving that substitution leaves a row resolving nothing carrying the bare `UNRECORDED`
sentinel, which silently changes an output the shipped `test_unrecorded_model_is_labeled_per_host` asserts
over EVERY row of its run. E-02 now requires the substitution move with the value, and E-06 case (g) pins it.

### F-08 REVIEW FINDING, HIGH: THE DASHBOARD EMITS MORE THAN TWO ROLES, SO A TWO-ROLE RESOLVER MIS-RESOLVES REAL ROWS

E-01's chain is written for a VERIFY role and an EXECUTE role only. Measured against the shipped fixture
`tests/test_run_dashboard._write_run`, one run already produces three distinct `role` values:
`[(1, "main"), (1, "verify"), (2, "gate-answer"), (2, "main")]`, and `_SESSION_NAME_RE`'s trailing `role`
group accepts any lowercase-plus-hyphen segment, so `recovery` is reachable by the same route. A resolver
accepting only two roles forces `gate-answer` into one of them, and resolving it as `execute` by accident is a
guess rather than a reading. E-01 now requires an explicit OTHER case that resolves through the EXECUTE chain
while reporting a label that does not claim verify provenance, and requires the vocabulary in the docstring
because E-02 and E-03 both call it.

### F-09 REVIEW FINDING, MEDIUM: E-01 LEFT ITS OWN CENTRAL INVARIANT AS AN EXECUTION-TIME COIN FLIP

E-01 opens by insisting three readers must not each invent a precedence, then offers "one function" OR
"duplicate the ORDER as data (a single tuple of accessors)" without deciding, conditioned on whether "no
existing shared home fits". That leaves the Set's load-bearing invariant to the executor, and the fallback
explicitly permits duplication. Measured: `run_dashboard` imports nothing from `run_analytics*` (0 matches)
and `run_analytics` imports nothing from `run_dashboard`, so the stated absence of a shared home is real; but
`run_analytics_schema` is already imported by `run_analytics`, is a pure vocabulary/dataclass module, and
importing one helper from it into `run_dashboard` creates no cycle. E-01 now PREFERS the single function in a
named module, allows the accessor-tuple fallback only with a measured justification, and REFUSES a
hand-written second if-chain outright.

### F-10 REVIEW FINDING, MEDIUM: AN ATTEMPT-GRAIN FACT IS NEVER `Phase.VERIFY`, SO "PHASE DECIDES THE ROLE" CANNOT SELECT THE VERIFY CHAIN

E-03 says to resolve per attempt "with the attempt's `phase` deciding the role". Measured in
`run_analytics.build_run_facts`, `attempt_phase = Phase.RECOVERY if is_recovery else item_phase`, and
`_phase_of` returns only `Phase.REVIEW` (when `action == "review"`) or `Phase.EXECUTE`. So an attempt-grain
fact's phase is drawn from `{review, execute, recovery}` and `Phase.VERIFY` is unreachable there, confirmed by
executing a two-model run: the attempt-grain fact's phase was `execute` while `verify` appeared only at
PHASE grain.

That is the CORRECT shape (an attempt-grain fact's usage is the executor turn's own `cost`/`tokens`, and the
verifier's spend is carried separately), so the remedy is to state it rather than to invent a verify attempt
fact. E-03 now maps all three reachable phases to the EXECUTE chain, requires a comment recording that an
attempt-grain fact is deliberately executor-side with the verifier's model staying on the already-correct
`Phase.VERIFY` phase fact, and explicitly FORBIDS adding a second attempt-grain fact (which would change the
fact count and therefore the `RunFacts` shape that `INGEST_SCHEMA_VERSION` exists to track).

Also corrected: E-03 named `FACT_SCHEMA_VERSION` beside `INGEST_SCHEMA_VERSION` without saying they live in
different modules. `INGEST_SCHEMA_VERSION` is defined in `run_analytics` (declared in `Scope-Paths`);
`FACT_SCHEMA_VERSION` is defined in `run_analytics_schema`, which is NOT declared. The verdict is still
required; if it says the constant must move, that is an out-of-scope edit to make and justify.

### F-11 REVIEW FINDING, HIGH: THE POPULATION SOURCE E-04 NAMES IS RUN GRAIN, NOT ATTEMPT GRAIN

E-04 instructed the executor to build the `model_comparison` population "from the same entries the surrounding
analyses already use (the module builds `costs`, `wall_times` and `token_totals` from `agg_rows`)". Measured,
neither source is attempt grain:

- `entries` are analytics CACHE entries whose `metric_facts` (read via `run_analytics_query._facts_of`) are
  RUN-level (`cost`, `wall_seconds`, `token_total`, `model`, `host_kind`, `status`, `event_count`) with no
  attempt list at all;
- `rows` is built with exactly two shapes, one `phase: "aggregate"` row per run and up to four per-run PHASE
  rows (`review`/`execute`/`verifier`/`recovery`) whose per-attempt figures are ACCUMULATED into phase
  buckets by the loop over `item["attempts"]`; `agg_rows` then selects the aggregate ones.

`model_comparison`'s parameter is named `attempts`, its coverage is attempts-with-model over total attempts,
and `CORPUS_BASELINE` records the comparison as "2 of 179 attempts" against 135 runs. Passing run or phase
records would therefore publish a coverage figure on a different denominator than the baseline E-07 must
report beside it, which is precisely the incomparability OQ-02 forbids, and it would do so silently.

THE REMEDY IS AVAILABLE IN THE SAME FUNCTION: the per-phase block already opens each run's `state.json` and
already loops `for item in s_data.get("queue", []): for att in item.get("attempts", [])`, so an attempt-grain
population is constructible there, one element per attempt carrying the E-01-resolved model and that
attempt's own `cost`. E-04 now directs the executor to that loop, and requires reporting the limitation and
leaving the call refusing if it proves impossible, rather than passing run rows.

### F-12 REVIEW FINDING, LOW: ONE CITED CONTENDING PLAN HAS ALREADY EXECUTED

E-06 justified a new test file because `tests/test_run_analytics.py` "is declared by two other pending plans,
`vnt9it` and `yumxwz`". Measured, `vnt9it` is not pending: it is in `.aw/records/plans/executed/`, so it
contends nothing and its cache-fingerprint change is already in the tree. The conventions section repeats the
error more strongly, warning that `vnt9it` "IS ABOUT TO TOUCH THE CACHE FINGERPRINT" and telling the executor
to read its state and reconcile, which is spent advice.

The CONCLUSION survives on better evidence: five other pending plans declare that path (`yumxwz` approved,
`wqiofa` reviewed, `o55eli` reviewed, plus Order 00 and this plan), while
`tests/test_attempt_model_consumers.py` is declared by nothing but Order 00's table. Both sites are corrected,
and the conventions section now records the LIVE contention on the four production paths instead
(`run_dashboard.py` three, `run_analytics_cli.py` two, `run_analytics_statistics.py` one, `run_analytics.py`
none).

### F-13 REVIEW FINDING, MEDIUM: THE DOC'S NO-DASH RULE IS MECHANICALLY ENFORCED AND FEEDS A RELEASE GATE, AND NOTHING IN THIS PLAN CHECKED IT

The Spec/documentation-sync section correctly tells the author to write the new `docs/run-analytics.md`
passage "with no em or en dashes", but no `E-*` or `V-*` item verified it. That rule is not a style
preference for this tree: `agent_workflows.docs_check.check_no_unicode_dashes` (with the `EM_DASH` and
`EN_DASH` constants) runs over the docs tree through `check_doc`/`check_docs_dir`, and those findings feed
`release_readiness.gate_docs_checks`, a NAMED RELEASE GATE. Measured at review,
`docs_check.check_doc(Path("docs/run-analytics.md"))` returns 0 findings, so the file is clean today and any
new finding would be attributable to this change and would surface at release time rather than at execution.
E-07 now requires running the checker after the doc edit and pasting a zero-finding result, and V-07 demands
it.

## Proposed changes (ordered, validatable)

1. One consumer-side precedence chain, defined once in a NAMED module, with a source label per tier and a
   role vocabulary wider than two values (E-01).
2. Per-row model resolution in `run_dashboard.collect_rows` at all three real sites, INCLUDING the
   unclaimed-session branch that recovers an existing attempt's `base`, with the `(unrecorded, <host>)`
   substitution moved per row and `_normalize_model` preserved (E-02).
3. Attempt-grain `Fact.model` read from the attempt in `run_analytics.build_run_facts`, phase grains
   untouched, with the deliberately executor-side grain recorded in a comment (E-03).
4. A genuine ATTEMPT-grain population fed to `model_comparison`, built in the existing `state.json` attempt
   loop rather than from run-grain `agg_rows`, threshold and `host-default` exclusion unchanged, caveat text
   reconciled (E-04).
5. An evidence-based decision on the privacy allowlist, preferring no widening (E-05).
6. A new cross-consumer test file with seven cases (E-06), and the three shipped dashboard model tests kept
   green and unedited with the per-row case added beside them (E-08).
7. Published coverage delta beside the retained historical baseline, the docs checker run after the doc edit,
   plus the bare suite (E-07).

## Deferred / out of scope (with reason)

- MOVING `MODEL_COVERAGE_THRESHOLD`. 0.80 is a declared judgement with a written rationale ("a comparison
  stratified on an identity known for a minority of records measures the minority and reports it as the
  whole"), and lowering it so an arm computes would be exactly the reverse-engineering the repository's own
  threshold documentation warns against. If the measured coverage after this Set is still below 0.80, the
  honest output is a refusal carrying the real number.
- BACK-FILLING HISTORY, so a corpus dominated by pre-Set runs may legitimately keep refusing. `w33lrl` set
  this precedent for `cost_attribution` and `model_comparison`'s own caveat already says coverage improves
  for future runs only.
- EDITING `CORPUS_BASELINE`. It is labelled a retained review-time snapshot with `is_current: false`, and
  rewriting it would destroy the before/after comparison E-07 exists to publish.
- NORMALIZING THE MODEL VALUE AT THE PRODUCER. `run_dashboard._normalize_model` keeps stripping provider
  prefixes at the display boundary. `7hek98`'s gate paragraph names producer-side normalization as a
  deferred alternative and it stays deferred: doing it at the producer would change what is RECORDED, which
  is a different decision from what is DISPLAYED.
- THE ANTIGRAVITY OBSERVED-MODEL CAPTURE, deferred by Order 02 (`ov2c9n`) with a named carrier. This plan's
  precedence chain reads `host_model` when present and is therefore ready for it with no further change,
  which is why it is a fallback chain rather than a hard dependency.

## Scope check

- Over-scope: `docs/run-analytics.md` is declared although this plan's core is code. It is in scope because
  this change alters what a documented output MEANS (a model attributed per attempt rather than per run),
  and leaving the doc silent would make the tool's own explanation of its numbers stale.
- Under-scope: a session file whose attempt record cannot be found at all (the `if base is None` arm) keeps
  the run-level model, because there is genuinely no attempt to read; CORRECTED AT REVIEW (F-07), an
  unclaimed session file whose attempt record DOES exist is now in scope and resolves per row, since the
  branch recovers that attempt's `base` and can carry a `verify` role. The `audit` verb's separate state
  keeps no per-attempt model at all (Orders 01 and 02 both exclude it), and the Antigravity observed model is
  absent until its carrier lands.
- Under-scope, NAMED AT REVIEW AND NOT CLOSED HERE: the `opencode/` prefix is NOT stripped by
  `_normalize_model` while `uri/` is (measured: `uri/its_direct/pt3-claude-opus-5-1m-us` normalizes to
  `its_direct/pt3-claude-opus-5-1m-us`, whereas `opencode/nemotron-3.5-lightning-free` is returned
  unchanged). Order 02 records `host_model` as a JOINED `providerID/id`, so an observed `opencode/...` value
  and a frozen value may normalize asymmetrically and read as two models in a group-by. That is a DISPLAY
  normalization question on a shipped function whose behavior three tests pin, it is not required for this
  plan's correctness, and widening the strip list would change existing grouped output; it is named here so
  the executor does not "fix" it mid-change, and it belongs in its own plan if a consumer needs it.

## Required tests / validation

- The three shipped `tests/test_run_dashboard.py` model tests, pasted green and UNEDITED, with a `git diff` of
  that file proving only the new case was added (F-05, E-08).
- `tests/test_attempt_model_consumers.py`, new, SEVEN cases (E-06), one shown red first, including the
  unclaimed-verify case (f) and the per-row unrecorded-label case (g) that F-07 added.
- `tests/test_run_analytics.py::ModelAttributionTests`, pasted green (E-03).
- The real `model_comparison` output from its production caller, pasted with its coverage and the DENOMINATOR
  NAMED, plus a statement of whether that denominator is attempts and therefore comparable with the retained
  baseline (E-04, F-11).
- The coverage delta beside the retained baseline, and `CORPUS_BASELINE` shown unedited (E-07).
- `docs_check.check_doc(Path("docs/run-analytics.md"))` pasted with 0 findings AFTER the doc edit (E-07,
  F-13), since those findings feed a release gate.
- Bare `python3 -m pytest`, summary line pasted, against review's green `3527 passed, 2 skipped`.

## Spec / documentation sync

- NO SPEC AMENDMENT, measured: no spec mentions `cost_attribution`, `options.model`, the dashboard, or
  `runsdash` (F-06), and spec `25kzda` Section 5.6's per-item JSON object carries no model field, so nothing
  there becomes false. `Scope-Paths` declares no `.spec.md` file and the runners' spec-edit announcement
  will correctly report none.
- `docs/run-analytics.md` IS AMENDED, and it is the only doc that should be: it already explains to a reader
  where a number comes from and why one may be absent, so it is the right home for one short passage stating
  that a model is attributed per attempt, naming the precedence tiers in order, and saying plainly that
  historical runs are not back-filled. Write it in the user-facing register that file already uses, with no
  em or en dashes. THAT RULE IS MECHANICALLY ENFORCED HERE AND FEEDS A RELEASE GATE (F-13):
  `docs_check.check_no_unicode_dashes` runs over the docs tree and its findings reach
  `release_readiness.gate_docs_checks`, and the file is at 0 findings today, so E-07 requires running the
  checker after the edit rather than trusting the instruction.
- NO NEW CLI FLAG, so spec `25kzda` Section 2.1's flag grammar is untouched. DO NOT CITE
  `tests/test_run_flag_surface.py` AS THE ENFORCEMENT: that file was DELETED in commit `19313eed` (4,863
  lines, alongside `tests/test_flag_surface_uniformity.py`), measured at review, and the same stale citation
  was corrected in Order 02. Nothing mechanical would catch an added flag; the obligation is the plan
  contract's (declare the `.spec.md` in `- Scope-Paths:` and amend it in the same change), which this plan
  honors by adding no flag at all.

## Open questions

### OQ-01: Should the OBSERVED model outrank the FROZEN one in the consumer chain?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: YES, OBSERVED FIRST, and the reason is evidential rather than aesthetic. The frozen value is a RECORD OF INTENT resolved before the turn ran, and in the commonest configuration it is not even a request (no `--model` is passed at all, and the run-level tier fills in by reading a config file, which can be edited between launch and turn). The observed value is the host reporting what it actually used. When the two disagree, a report that shows the request is describing something that did not happen. The residual risk is accepted and mitigated: an observation is best-effort and may be absent, which is why it is a TIER and not a replacement, and the source label makes which tier answered visible in the dashboard's detail panel and in any report. A reviewer who disagrees can reorder tiers 1 and 2 in one function, which is the reason E-01 requires the precedence be defined once.

### OQ-02: Should `model_comparison` be fed ATTEMPT-grain or RUN-grain rows?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: ATTEMPT-GRAIN, because that is what the function's own contract reads and what its refusal counts. Its parameter is named `attempts`, it computes coverage as attempts carrying a model over total attempts, and it groups cost `by_model` per attempt; its docstring reports the review-time measurement as "2 of 179 attempts". Feeding run aggregates would silently redefine the denominator and make the published coverage figure incomparable with the baseline E-07 must report beside it. The practical wrinkle is honest and stated: the CLI's surrounding analyses are built from per-run `agg_rows`, so E-04 must assemble an attempt-level population rather than reuse `agg_rows` directly, and if the available entries cannot yield attempt grain the executor must report that limitation rather than quietly passing run rows.

### OQ-03: Does this plan need Order 02 executed first?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: NO, AND THE FRONT MATTER SAYS SO DELIBERATELY: `Item-Dependencies: executed:czut8j` names Order 01 only. Order 01 supplies `attempt["model"]`, which is the tier this plan's whole fallback chain is anchored on and without which E-02's per-row resolution has nothing new to read. Order 02's `host_model` is an OPTIONAL top tier: the chain reads it when present and skips it when absent, which is the same tolerance it already applies to a pre-`w33lrl` run's missing `cost_attribution`. So Orders 02 and 03 are mutually independent and may execute in either order or in parallel lanes. E-06 case (c) exercises the observed tier with a synthetic attempt carrying `host_model`, so it passes whether or not Order 02 has landed, which is what makes the independence real rather than asserted.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a pasted transcript resolving each of the six tiers in turn, each showing the returned model AND its source label, plus a malformed attempt (a non-mapping where a mapping belongs) resolving to unrecorded without raising. The verify-role case must be shown preferring the attempt's verify model over the executor's, since that is the defect F-01 measures. PLUS THE WIDER ROLE VOCABULARY (F-08): a pasted resolution for a `gate-answer` role showing which chain answered and a source label that does NOT claim verify provenance, with the docstring's declared vocabulary quoted. PLUS THE NAMED HOME (F-09): state the module the function lives in and paste the import both consumers use; if the accessor-tuple fallback was taken instead, paste the measured import graph that justified it. A second hand-written if-chain fails this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: THREE pasted `collect_rows` outputs. First, the F-01 two-model run, now showing `role=main` and `role=verify` with DIFFERENT models (the same transcript shape as F-01, so the before and after are directly comparable). Second, a run carrying NO per-attempt model fields, whose rows must be identical to today's output including the `(unrecorded, <host>)` label where applicable; state how identity was checked. Third, THE UNCLAIMED-VERIFY CASE (F-07): a run with a verify session file that no attempt's `verify_log` claims but whose attempt record EXISTS, showing that row resolving the VERIFIER's model rather than the executor's, which is the branch this plan originally excused. Also name the three sites changed and confirm the `(unrecorded, <host>)` substitution now runs per row rather than once per run.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the F-01 run's pasted fact list showing the ATTEMPT-grain fact taking the attempt's model while the PHASE-grain facts are unchanged; a written verdict on `INGEST_SCHEMA_VERSION` and `FACT_SCHEMA_VERSION` naming the DEFINING MODULE of each (they are in different modules and only one is declared in `Scope-Paths`, F-10), whether each moved, and why; the QUOTED COMMENT recording that an attempt-grain fact is deliberately executor-side and that the verifier's model stays on the `Phase.VERIFY` phase fact (F-10); confirmation that the fact COUNT per attempt is unchanged, since a second attempt-grain fact would alter the `RunFacts` shape; and a pasted `python3 -m pytest tests/test_run_analytics.py -o addopts=""` showing `ModelAttributionTests` green, `test_case_7_cost_attribution_key_agreement` included by name.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the pasted `model_comparison` result produced by the REAL production caller on this box, showing a non-fabricated `observed_coverage`, `attempts_with_model` and the total it is over, plus the verdict as measured. A pasted diff or quotation showing `MODEL_COVERAGE_THRESHOLD` still `0.80` and the `host-default` exclusion still present. If the verdict is still REFUSED, that is an acceptable result and must be reported as such, not worked around. PLUS THE GRAIN PROOF (F-11), which is the point of this item: state WHERE the population was built and show it is one element per ATTEMPT, not per run or per phase. Review measured that neither source the plan originally named can supply attempt grain (cache `entries` carry run-level `metric_facts` with no attempt list; `rows` holds only an `aggregate` row per run plus up to four accumulated phase rows). So paste the denominator and say plainly whether it counts attempts and is therefore comparable with `CORPUS_BASELINE`'s "2 of 179 attempts"; a run- or phase-grain denominator presented as coverage FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: a written decision naming option (a) or (b) with the evidence it rests on. If (a): a pasted projection of a real fact showing no `PrivacyRefusal` and a statement that `ALLOWED_METRIC_KEYS` was not edited (with a pasted empty diff of that region). If (b): the pasted test proving the new key's values are constrained to a closed vocabulary and cannot carry a path, plus both allowlist edits shown together.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `python3 -m pytest tests/test_attempt_model_consumers.py -o addopts=""` showing all SEVEN cases green BY NAME, with case (c) the observed-beats-frozen case, case (e) the still-refuses case, case (f) the unclaimed-verify case (F-07) and case (g) the per-row unrecorded-label case (F-07) each named explicitly in the output. Plus the pasted RED run from the non-vacuity experiment and the restored green; a green run alone does not satisfy this item, because a test that cannot fail proves nothing. The three SHIPPED dashboard tests are E-08's subject and are validated by V-08, deliberately not duplicated here.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: pasted `python3 -m pytest tests/test_run_dashboard.py -o addopts=""` showing `test_one_row_per_session_with_roles`, `test_unrecorded_model_is_labeled_per_host` and `test_antigravity_run` green BY NAME, plus the new per-row case green by name. The UNEDITED claim must be shown, not asserted: paste a `git diff` of `tests/test_run_dashboard.py` and confirm it contains ONLY the added case, with no hunk touching the three named tests. Review measured this file green with `tests/test_run_analytics.py` at `44 passed`, so state your count beside that. An edit to any of the three is the signal that a tier was broken rather than extended and FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the current coverage figure and `CORPUS_BASELINE`'s retained figure side by side, each with its denominator and its provenance labelled, OR an explicit statement that this lane has no `.aw/records/runs` corpus plus the substitute synthetic measurement labelled as synthetic (review confirmed the directory is absent and gitignored, so this is the expected branch). A pasted diff of the `CORPUS_BASELINE` region showing NO change; review re-verified all four retained figures plus `provenance` and `is_current` as exact, so any difference is an edit this plan forbids. THE DOCS CHECKER RUN (F-13): pasted `docs_check.check_doc(Path("docs/run-analytics.md"))` output after the doc edit showing 0 findings, since a dash there reaches `release_readiness.gate_docs_checks` and would block a release rather than fail this plan's tests. A pasted bare `python3 -m pytest` summary line with the pre-change baseline stated beside it; review measured `3527 passed, 2 skipped, 3 warnings`, all green.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` (`/plan-review`, 2026-10-01) and requires explicit human approval before execution;
an executing agent must not self-approve, and must not hand-write a `- Readiness:` value, which is an output
of review.

It declares `Item-Dependencies: executed:czut8j` (Order 01 only) and is deliberately INDEPENDENT of Order 02;
see OQ-03 for why, and do not add an edge to `ov2c9n` without re-reading it.

SCOPE FENCE (a DECLARATION, so the runner can reconcile afterwards; it is not an instruction to stop over a
scope question). The declared paths are exactly `agent_workflows/run_dashboard.py`,
`agent_workflows/run_analytics.py`, `agent_workflows/run_analytics_statistics.py`,
`agent_workflows/run_analytics_cli.py`, `tests/test_run_dashboard.py`,
`tests/test_attempt_model_consumers.py` and `docs/run-analytics.md`. TWO FORESEEABLE OUT-OF-SCOPE EDITS ARE
NAMED HERE RATHER THAN DISCOVERED LATE: E-01's shared home, if it lands in a module neither family declares
(for example `run_analytics_schema.py`), and E-03's `FACT_SCHEMA_VERSION` verdict, which lives in
`run_analytics_schema.py` and is NOT declared. Either is an edit to MAKE and then JUSTIFY, which
`aw ipd finalize` enforces by refusing to complete without a `--scope-reason` per out-of-scope path and a
`--scope-ack` per declared-but-unmodified path. No `.spec.md` file is declared and none may be edited; if the
work turns out to require amending spec `25kzda`, STOP AND REPORT, since an undeclared spec amendment changes
a contract every other plan is reviewed against.

At execution, follow the repository execution contract: commit only the declared paths through
`aw commit <plan> -- <paths>`, never `git add -A`, never push, and PASTE THE ACTUAL RUNNER OUTPUT for every
test claim (a claim of success you did not run is the one failure this contract treats as non-negotiable).
Do not mark this plan executed until `aw ipd lint --phase pre-transition` conforms AND every `V-*` item
carries pasted evidence. THE LIFECYCLE TRANSITION IS OWNED CONDITIONALLY: under `aw oc run` / `aw agy run`
the RUNNER performs the finalize and the terminal move, so the executing agent must not pre-empt it; only
when executing by hand, outside a runner, does the executor run `aw ipd finalize` itself. Never hand-roll a
`git mv` into `.aw/records/plans/executed/`. This is the plan that delivers what backlog `7yz545` asked for,
so its completion is what makes the item's `graduated` state honest.
