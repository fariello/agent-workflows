# IPD: Read the per-attempt model in analytics and the dashboard so coverage reaches the consumers

- Date: 2026-09-30
- Kind: child
- Concern: ORDERS 01 AND 02 WRITE A PER-ATTEMPT MODEL THAT NOTHING READS, so the backlog item's actual ask ("so run analytics can compare models") stays unmet until a consumer is repointed. Three specific consumers are wrong today, each measured. FIRST, `run_dashboard.collect_rows` computes ONE model per run and stamps it onto every row, so a verifier row reports the EXECUTOR's model: executed at authoring against a run whose `options` carried `model: provA/executor-model` and `verify_model: provB/verifier-model`, the dashboard returned `role=main model=provA/executor-model` AND `role=verify model=provA/executor-model`. SECOND, `run_analytics` gets the phase grains right (`Phase.VERIFY` reads `_verify_model_of`) but its ATTEMPT-grain `Fact` takes the run-level executor model unconditionally, so the finest grain is the least accurate. THIRD, `run_analytics_statistics.model_comparison` REFUSES below `MODEL_COVERAGE_THRESHOLD` of 0.80 and its sole production caller passes a LITERAL EMPTY LIST (`stats_mod.model_comparison([])` in `run_analytics_cli`), so the comparison the item wants is not merely refused for want of coverage, it is never fed any attempts at all: executed at authoring, that call returns `Verdict.REFUSED` with `sample_size=0` and "coverage 0.0000", while the same function fed 30 attempts each carrying a model returns `Verdict.COMPUTED`.
- Scope: Make the three consumers read the per-attempt fields Orders 01 and 02 produce, falling back to today's run-level fields so no existing run loses attribution. Concretely: a per-row model in `run_dashboard` so a verifier row reports the verifier's model and the `(unrecorded, <host>)` label is reached only when an attempt genuinely has nothing; an attempt-grain `Fact.model` read from the attempt; and a real attempt population fed to `model_comparison` in place of the empty literal, with the coverage it actually achieves reported rather than asserted. EXCLUDES changing `MODEL_COVERAGE_THRESHOLD` (0.80 is a declared judgement, and moving it to make an arm compute would be reverse-engineering a threshold to a desired answer). EXCLUDES back-filling history, so the honest result is that coverage improves for FUTURE runs and the refusal may legitimately still fire on a corpus dominated by old runs. EXCLUDES the privacy allowlist widening for any key that is not needed, and states which one IS needed.
- Scope-Paths: agent_workflows/run_dashboard.py, agent_workflows/run_analytics.py, agent_workflows/run_analytics_statistics.py, agent_workflows/run_analytics_cli.py, tests/test_run_dashboard.py, tests/test_attempt_model_consumers.py, docs/run-analytics.md
- Item-Dependencies: executed:czut8j
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Backlog: 7yz545
- Set: attmodel
- Order: 3
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: r5fk4k

## Workflow history

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
  - Depends on: none
  - Expected outcome: one function (or one shared accessor tuple) exists; a pasted transcript resolving all six tiers plus a malformed attempt, showing the tier label for each.
  - Execution state: pending

- [ ] E-02 MAKE THE DASHBOARD'S MODEL PER-ROW INSTEAD OF PER-RUN, WHICH IS A THREE-SITE CHANGE AND MUST HIT ALL THREE. `run_dashboard.collect_rows` computes `model, model_source = _run_model(state)` once per run, applies the `(unrecorded, <host>)` per-host label, and stamps the result into the `base` dict at TWO sites (the attempt-claimed one and the unclaimed-session-file one), from which `_row_from_stats` copies it into both the `main` and the `verify` row. Change it so the VERIFY row resolves with the verify role through E-01 while the MAIN row resolves with the execute role, and so an attempt carrying its own model prefers it over the run-level value. KEEP THE `(unrecorded, <host>)` LABELLING EXACTLY AS IT IS, including its per-host suffix and its stated reason ("so an unknown OpenCode model never pools with an unknown Antigravity one"), and keep `_normalize_model`'s prefix stripping applied at the same point, so a row's displayed value stays comparable across hosts. The unclaimed-session-file branch has no attempt to read, so it legitimately keeps the run-level value: say so in a comment rather than leaving a reader to wonder whether that site was missed. DO NOT change `COLUMNS`, the browser payload shape, or `DASHBOARD_SCHEMA_VERSION`: this change alters the VALUE in an existing `model`/`model_source` column and adds no column, so the schema is untouched and the disposable stats cache (keyed on the same version) needs no invalidation.
  - Depends on: E-01
  - Expected outcome: the F-01 two-model run re-measured through `collect_rows`, pasted, showing `role=main` and `role=verify` reporting DIFFERENT models; plus a pasted run with no per-attempt fields at all, showing byte-identical rows to today's output.
  - Execution state: pending

### Task group 2: the analytics grains and the arm that refuses

- [ ] E-03 READ THE ATTEMPT'S OWN MODEL ON THE ATTEMPT-GRAIN FACT IN `run_analytics.build_run_facts`. Today that function computes `model = _model_of(state)` and `verify_model = _verify_model_of(state, model)` ONCE per run and passes the run-level `model` into every `Grain.ATTEMPT` fact, so the finest grain carries the coarsest attribution. Resolve per attempt through E-01 instead, with the attempt's `phase` deciding the role (the function already computes `attempt_phase`, distinguishing `Phase.RECOVERY`). Leave the PHASE-grain facts alone: they already read `_verify_model_of` for `Phase.VERIFY` and are correct. Preserve `_model_of` and `_verify_model_of` as the run-level tiers rather than deleting them, because `Grain.RUN` and `Grain.IPD` facts legitimately want a run-level answer and because `tests/test_run_analytics.py::ModelAttributionTests::test_case_7_cost_attribution_key_agreement` pins `run_analytics._COST_ATTRIBUTION_KEY == runner_shared.COST_ATTRIBUTION_KEY` and must keep passing. CHECK THE VERSION CONSTANTS AND SAY WHICH MOVED: `INGEST_SCHEMA_VERSION` is documented as bumped "when the RunFacts SHAPE changes" and `FACT_SCHEMA_VERSION` when the fact schema does; this change alters a fact's VALUE and adds no field, so state the finding either way rather than bumping reflexively or silently.
  - Depends on: E-01
  - Expected outcome: the F-01 run's pasted fact list showing the ATTEMPT-grain fact's model resolved from the attempt; a written verdict on each version constant with its reason; the pasted `tests/test_run_analytics.py` run showing `ModelAttributionTests` still green.
  - Execution state: pending

- [ ] E-04 FEED `model_comparison` A REAL ATTEMPT POPULATION INSTEAD OF THE EMPTY LITERAL, AND REPORT WHATEVER COVERAGE RESULTS. `run_analytics_cli` calls `stats_mod.model_comparison([])` under a comment reading "Model comparison refusal (under 80% coverage)", which cannot be true of an empty list: it refuses at 0.0000 for want of any input. Build the attempt population from the same entries the surrounding analyses already use (the module builds `costs`, `wall_times` and `token_totals` from `agg_rows` a few statements above) so each element carries at least `model` and `cost`, which is exactly what `model_comparison` reads. THE REFUSAL MUST REMAIN REACHABLE AND MUST NOT BE WEAKENED: `MODEL_COVERAGE_THRESHOLD` stays 0.80, the `host-default` literal stays excluded from the covered set (`str(a.get("model")).strip() != "host-default"`), and if the real coverage is below threshold the arm REFUSES with the real number, which is the honest outcome and is strictly better than refusing with a fabricated 0.0000. UPDATE THE COMMENT to say what the call now does. Also reconcile the function's own caveat text, which states "coverage improves for FUTURE runs only (Order 04 records model identity per file)": that clause names a different plan's mechanism and, after this Set, is incomplete rather than wrong, so extend it to name the per-attempt field as the other future-coverage source.
  - Depends on: E-01
  - Expected outcome: pasted `model_comparison` output from the real caller on this box, showing a real `observed_coverage` and `attempts_with_model` against a named denominator, with the verdict (REFUSED or COMPUTED) reported as measured and not as hoped.
  - Execution state: pending

- [ ] E-05 RESOLVE THE PRIVACY BOUNDARY FOR ANY NEW LABEL BEFORE IT CAN REFUSE AN ENTRY, NAMING EXACTLY WHICH KEY NEEDS WHAT. Measured at authoring: `run_analytics_privacy.ALLOWED_METRIC_KEYS` contains `model` and `model_variant` but NOT `model_source`, and `_project_scalar("model_source", "frozen-launch")` raises `PrivacyRefusal("is a string on a key whose values are not free text")`. So a projected fact carrying a `model_source` key would be REFUSED. Two acceptable outcomes and the plan must pick one on evidence: (a) do not project the source at all, keeping it a dashboard-and-report concern (the dashboard is not privacy-projected, verified at authoring: `run_dashboard` imports nothing from `run_analytics_privacy`), which needs NO allowlist change and is the narrower act; or (b) if the source genuinely must reach a projected fact, add it to `ALLOWED_METRIC_KEYS` and `_CLOSED_VOCABULARY_KEYS` together with a test proving the new key cannot carry a path or free text, which is the discipline that module's own comment demands ("adding a key is a deliberate act: it widens the boundary, so it belongs with a test that proves the new key cannot carry a transcript, a path or a command line"). PREFER (a) unless a consumer needs it. Whichever is chosen, state the decision and the evidence; do NOT widen the allowlist speculatively.
  - Depends on: E-03
  - Expected outcome: a written decision naming (a) or (b) with its evidence; if (b), the pasted test proving the new key's value shape is constrained; if (a), a pasted projection of a real fact showing no refusal and no allowlist edit.
  - Execution state: pending

### Task group 3: prove it, and prove nothing old broke

- [ ] E-06 EXTEND THE DASHBOARD'S EXISTING TESTS AND ADD A CONSUMER TEST FILE, KEEPING THE THREE SHIPPED MODEL CASES GREEN. `tests/test_run_dashboard.py` already carries `CollectRowsTests::test_one_row_per_session_with_roles` (asserting `main1["model"] == "some-model"`), `test_unrecorded_model_is_labeled_per_host` (asserting `{"(unrecorded, oc)"}`) and `test_antigravity_run` (asserting the `cost_attribution` fallback reaches `"Flash"`). All three must keep passing UNCHANGED, because each pins a tier this plan preserves; add the new per-row case beside them rather than editing them. Put the cross-consumer cases in a new `tests/test_attempt_model_consumers.py` (a new file, since `tests/test_run_analytics.py` is declared by two other pending plans, `vnt9it` and `yumxwz`, while this path is declared by none). Required cases, all behavioral, none reading production source: (a) the two-model run reports two models across dashboard rows; (b) the same run's ATTEMPT-grain fact takes the attempt's model; (c) an attempt with `host_model` set to something DIFFERENT from its frozen `model` resolves to the observed one with the observation's source label, proving tier 1 beats tier 2; (d) a run with no per-attempt fields produces output identical to today's, which is the regression guard for every historical run; (e) `model_comparison` fed a population whose coverage is deliberately below 0.80 still REFUSES, with its real coverage in the result. SHOW ONE CASE RED FIRST and paste both runs.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the three shipped dashboard model tests pasted green and unedited; `tests/test_attempt_model_consumers.py` with all five cases; the pasted RED run proving non-vacuity.
  - Execution state: pending

- [ ] E-07 MEASURE THE COVERAGE DELTA ON THE EXECUTING BOX AND PUBLISH IT WITH THE BASELINE IT REPLACES, THEN RUN THE BARE SUITE. `run_analytics_statistics.CORPUS_BASELINE` carries the review-time figures this Set was filed against (`runs_with_null_options_model: 130`, `runs_with_options_model: 5`, `attempts_with_resolvable_model: 2`, `model_identity_coverage: 0.011`) and is explicitly labelled `"provenance": "review-time-snapshot"`, `"is_current": false`. DO NOT EDIT THOSE NUMBERS: they are a retained historical baseline and rewriting them would destroy the comparison. Instead MEASURE current coverage over the local corpus and report both figures side by side, stating the denominator. If this lane has no `.aw/records/runs` corpus (gitignored and absent from a fresh worktree, which was the case at authoring) say so explicitly and report the coverage over synthetic runs constructed for E-06 instead, naming them as such; do not present a synthetic figure as a corpus measurement. Then run `python3 -m pytest` bare and paste the summary line, re-deriving the pre-change baseline at execution.
  - Depends on: E-06
  - Expected outcome: the two coverage figures side by side with denominators and provenance named, or an explicit no-corpus statement plus the substitute; `CORPUS_BASELINE` shown UNEDITED (a pasted diff of that region, empty); a pasted bare `python3 -m pytest` summary line.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The suite is run BARE: `pyproject.toml` `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`. Use `-o addopts=""` for per-test counts; never `-n0`, never a second `-q`, never `-p no:randomly`.
- `run_analytics_privacy` IS A DECLARED BOUNDARY, NOT A FORMALITY: its own comment states that adding an allowlist key "widens what is persisted, so it belongs with a test proving the new field cannot carry a path, a transcript, a network address, or host identity". E-05 is written to that standard and prefers not widening it at all.
- THE ANALYTICS CACHE IS DISPOSABLE AND SELF-INVALIDATING on a `state.json` rewrite: `run_analytics_cache.source_fingerprint` folds each relevant file's size and `mtime_ns` into its digest and `_RELEVANT_TOP_LEVEL_FILES` includes `state.json`, so a run whose state gains the new attempt keys re-fingerprints automatically. That is why this plan bumps no cache version, and it is recorded so a reviewer does not ask for one.
- ONE PENDING PLAN IS ABOUT TO TOUCH THE CACHE FINGERPRINT: `vnt9it` (`eventcountbf`) folds producer metric keys into `source_fingerprint` and declares `run_analytics.py`, `run_analytics_cache.py`, `tests/test_run_analytics.py`, `tests/test_run_analytics_cli.py` and `docs/run-analytics.md`. This plan declares two of those paths, so if both are in flight the runner's lane isolation handles the merge, but an executor should read `vnt9it`'s state first and reconcile rather than assume.

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

## Proposed changes (ordered, validatable)

1. One consumer-side precedence chain, defined once, with a source label per tier (E-01).
2. Per-row model resolution in `run_dashboard.collect_rows`, at all three stamping sites, preserving the
   `(unrecorded, <host>)` labelling and `_normalize_model` (E-02).
3. Attempt-grain `Fact.model` read from the attempt in `run_analytics.build_run_facts`, phase grains
   untouched (E-03).
4. A real attempt population fed to `model_comparison`, threshold and `host-default` exclusion unchanged,
   caveat text reconciled (E-04).
5. An evidence-based decision on the privacy allowlist, preferring no widening (E-05).
6. New per-row and cross-consumer tests beside the three unedited shipped ones (E-06).
7. Published coverage delta beside the retained historical baseline, plus the bare suite (E-07).

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
- Under-scope: an unclaimed session file (one no attempt references) keeps the run-level model, because
  there is no attempt to read; the `audit` verb's separate state keeps no per-attempt model at all (Orders
  01 and 02 both exclude it); and the Antigravity observed model is absent until its carrier lands.

## Required tests / validation

- The three shipped `tests/test_run_dashboard.py` model tests, pasted green and UNEDITED (F-05).
- `tests/test_attempt_model_consumers.py`, new, five cases (E-06), one shown red first.
- `tests/test_run_analytics.py::ModelAttributionTests`, pasted green (E-03).
- The real `model_comparison` output from its production caller, pasted with its coverage and denominator
  (E-04).
- The coverage delta beside the retained baseline, and `CORPUS_BASELINE` shown unedited (E-07).
- Bare `python3 -m pytest`, summary line pasted.

## Spec / documentation sync

- NO SPEC AMENDMENT, measured: no spec mentions `cost_attribution`, `options.model`, the dashboard, or
  `runsdash` (F-06), and spec `25kzda` Section 5.6's per-item JSON object carries no model field, so nothing
  there becomes false. `Scope-Paths` declares no `.spec.md` file and the runners' spec-edit announcement
  will correctly report none.
- `docs/run-analytics.md` IS AMENDED, and it is the only doc that should be: it already explains to a reader
  where a number comes from and why one may be absent, so it is the right home for one short passage stating
  that a model is attributed per attempt, naming the precedence tiers in order, and saying plainly that
  historical runs are not back-filled. Write it in the user-facing register that file already uses, with no
  em or en dashes.
- NO NEW CLI FLAG, so spec `25kzda` Section 2.1's flag grammar is untouched and
  `tests/test_run_flag_surface.py` is unaffected.

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
  - Required evidence: a pasted transcript resolving each of the six tiers in turn, each showing the returned model AND its source label, plus a malformed attempt (a non-mapping where a mapping belongs) resolving to unrecorded without raising. The verify-role case must be shown preferring the attempt's verify model over the executor's, since that is the defect F-01 measures.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: two pasted `collect_rows` outputs. First, the F-01 two-model run, now showing `role=main` and `role=verify` with DIFFERENT models (the same transcript shape as F-01, so the before and after are directly comparable). Second, a run carrying NO per-attempt model fields, whose rows must be identical to today's output including the `(unrecorded, <host>)` label where applicable; state how identity was checked.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the F-01 run's pasted fact list showing the ATTEMPT-grain fact taking the attempt's model while the PHASE-grain facts are unchanged; a written verdict on `INGEST_SCHEMA_VERSION` and `FACT_SCHEMA_VERSION` naming whether each moved and why; and a pasted `python3 -m pytest tests/test_run_analytics.py -o addopts=""` showing `ModelAttributionTests` green, `test_case_7_cost_attribution_key_agreement` included by name.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the pasted `model_comparison` result produced by the REAL production caller on this box, showing a non-fabricated `observed_coverage`, `attempts_with_model` and the total it is over, plus the verdict as measured. A pasted diff or quotation showing `MODEL_COVERAGE_THRESHOLD` still `0.80` and the `host-default` exclusion still present. If the verdict is still REFUSED, that is an acceptable result and must be reported as such, not worked around.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: a written decision naming option (a) or (b) with the evidence it rests on. If (a): a pasted projection of a real fact showing no `PrivacyRefusal` and a statement that `ALLOWED_METRIC_KEYS` was not edited (with a pasted empty diff of that region). If (b): the pasted test proving the new key's values are constrained to a closed vocabulary and cannot carry a path, plus both allowlist edits shown together.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `python3 -m pytest tests/test_run_dashboard.py tests/test_attempt_model_consumers.py -o addopts=""` showing the three shipped model tests green BY NAME and unedited (state how the no-edit claim was verified), and all five new cases green by name. Plus the pasted RED run from the non-vacuity experiment and the restored green.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the current coverage figure and `CORPUS_BASELINE`'s retained figure side by side, each with its denominator and its provenance labelled, OR an explicit statement that this lane has no `.aw/records/runs` corpus plus the substitute synthetic measurement labelled as synthetic. A pasted diff of the `CORPUS_BASELINE` region showing NO change. A pasted bare `python3 -m pytest` summary line with the pre-change baseline stated beside it.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before execution;
an executing agent must not self-approve, and must not hand-write a `- Readiness:` value, which is an output
of review.

It declares `Item-Dependencies: executed:czut8j` (Order 01 only) and is deliberately INDEPENDENT of Order 02;
see OQ-03 for why, and do not add an edge to `ov2c9n` without re-reading it.

At execution, follow the repository execution contract: commit only the seven declared paths through
`aw commit <plan> -- <paths>`, never `git add -A`, never push, and paste the ACTUAL runner output for every
test claim. Do not mark this plan executed until `aw ipd lint --phase pre-transition` conforms AND every
`V-*` item carries pasted evidence. This is the plan that delivers what backlog `7yz545` asked for, so its
completion is what makes the item's `graduated` state honest.
