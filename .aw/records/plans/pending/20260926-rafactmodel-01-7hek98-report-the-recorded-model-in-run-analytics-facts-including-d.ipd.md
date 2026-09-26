# IPD: Report the recorded model in run-analytics facts, including display-name models and the verify phase

- Date: 2026-09-26
- Kind: child
- Concern: RUN-ANALYTICS FACTS REPORT `model=''` FOR RUNS THAT RECORDED A MODEL. Three independent causes, re-verified at HEAD `61ef21d8`. (1) DISPLAY NAME DROPPED: every Antigravity run since the display name began being frozen (5 of the 24 runs under `.aw/records/runs/` carrying `options.cost_attribution`, all agy: `run-20260926T013533Z-3116868`, `run-20260926T025247Z-3448107`, `run-20260926T042128Z-3748222`, `run-20260926T051623Z-115951`, `run-20260926T051642Z-116672`) records `options.model = 'Gemini 3.8 Flash (High)'`, and `run_analytics._model_of` returns `''` for all five because `run_analytics._label` rejects anything failing `run_analytics_privacy._LABEL_RE` (no spaces or parentheses). `run_analytics.build_run_facts` on `run-20260926T042128Z-3748222` yields `model=''` at every grain. Independently, the persistence boundary `run_analytics_privacy.project_metric_facts` would REFUSE the value even if `_label` passed it (`key 'model' is not a short closed-vocabulary label`), because `model` is in `_CLOSED_VOCABULARY_KEYS` and `_project_scalar` applies the same regex. (2) NO FALLBACK: `_model_of` reads only `options.model` and never `options[runner_shared.COST_ATTRIBUTION_KEY]["model"]`, which `runner_shared.cost_attribution_record` fills with the host's resolved default when `options.model` is None. No local run shows this shape today (every recorded run has both equal), so it is a latent gap on the oc path where no `--model` is passed, which is the case the `w33lrl` producer was written for. (3) VERIFY MISATTRIBUTED: `build_run_facts` computes one `model` per run and passes it to BOTH the `Phase.EXECUTE` and `Phase.VERIFY` phase facts, although `oc_runipd` writes `options.verify_model` and `options["verify_" + COST_ATTRIBUTION_KEY]` when a verifier profile is resolved. NOTE on commit `b47d7816`: it made `runner_shared.driver_actor` render `model=Gemini-3.8-Flash-High` via `_actor_token`, but that changes only the history actor string; `options.model` still holds the raw display name (verified on all five runs above), so analytics is unaffected by that commit.
- Scope: IN: (a) `run_analytics._model_of` falls back to `options[COST_ATTRIBUTION_KEY]["model"]` when `options.model` is empty; (b) a new `run_analytics._verify_model_of` (`options["verify_" + COST_ATTRIBUTION_KEY]["model"]`, then `options.verify_model`, then the executor model) used for the `Phase.VERIFY` phase fact; (c) a MODEL-ONLY label rule admitting a display name (letters, digits, the existing separators, plus single spaces and parentheses) in both `run_analytics` (a `_model_label` used by the two model readers) and `run_analytics_privacy._project_scalar` (a `model`-key branch), while `_looks_like_path` and an embedded-path check still refuse paths; (d) behavioral tests in `tests/test_run_analytics.py`. OUT: widening any other label key; changing `runner_shared.cost_attribution_record`, the runners, or `driver_actor`; normalizing stored display names; recomputing cost; changing `aw runs` rendering.
- Scope-Paths: agent_workflows/run_analytics.py, agent_workflows/run_analytics_privacy.py, tests/test_run_analytics.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: lixqyc
- Blocks-Release: next
- Set: rafactmodel
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7hek98

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog lixqyc (reclassified bug + Blocks-Release next on 2026-09-26). All three causes re-measured at HEAD 61ef21d8 against the repo's own recorded runs; the privacy projector was found to refuse display names independently of _label, and an embedded-path gap in the proposed widening was found and fenced.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make run-analytics facts carry the model a run actually recorded, for both hosts and for the verify phase separately, without letting a path or free text into the persisted `model` field.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE at the executing HEAD. (a) For every `.aw/records/runs/*/state.json` carrying `options.cost_attribution`, paste `options.model`, `cost_attribution.model`, `options.verify_model`, `verify_cost_attribution.model`, and `run_analytics._model_of(state)`. (b) Paste the set of `(grain, model)` pairs from `run_analytics.build_run_facts` on one display-name agy run. (c) Paste the outcome of `run_analytics_privacy.project_metric_facts({"model": "Gemini 3.8 Flash (High)"})`. If every display-name run already yields its model, drop cause (1) and say so.
  - Depends on: none
  - Expected outcome: the display-name runs give `_model_of == ''` and every fact `model == ''`; the projector raises `PrivacyRefusal` for the display name.
  - Execution state: pending

### Task group 2: readers

- [ ] E-02 ADD THE COST-ATTRIBUTION FALLBACK to `run_analytics._model_of`: read `options.model`; if it yields an empty label, read `options.get(runner_shared.COST_ATTRIBUTION_KEY)` and, when it is a mapping, its `"model"`. Import the key constant from `runner_shared` (lazily inside the function if a module-level import would add `runner_shared` to `run_analytics`'s import graph; check with `python3 -c "import agent_workflows.run_analytics, sys; print('agent_workflows.runner_shared' in sys.modules)"` before and after and keep the answer unchanged). Both reads go through the model label rule of E-04.
  - Depends on: E-01
  - Expected outcome: a state with `options.model = None` and `cost_attribution.model = "provider/model"` yields `"provider/model"`; a state with both empty yields `""`.
  - Execution state: pending

- [ ] E-03 ADD `run_analytics._verify_model_of(state, executor_model)`: return the first non-empty model label of `options["verify_" + COST_ATTRIBUTION_KEY]["model"]`, `options["verify_model"]`, else `executor_model`. In `build_run_facts`, compute it once per run beside `model = _model_of(state)` and pass it as `model=` for the `Phase.VERIFY` entry of the PHASE-grain loop only (the loop over `(Phase.EXECUTE ..., exec_usage), (Phase.VERIFY, verify_usage)`), keeping the executor model on every other fact. The IPD, ATTEMPT and RUN grains keep the executor model: they merge or precede the phases and have no single verifier identity.
  - Depends on: E-02
  - Expected outcome: a run whose options carry `verify_cost_attribution.model = "other/verifier"` yields a VERIFY phase fact with `model == "other/verifier"` and an EXECUTE phase fact with the executor model; a run with no verifier fields yields the executor model on both.
  - Execution state: pending

### Task group 3: admit display names for the model field only

- [ ] E-04 DEFINE ONE MODEL LABEL RULE in `run_analytics_privacy` and use it in both places. Add `_MODEL_LABEL_RE` permitting `_LABEL_RE`'s character class plus single interior spaces and parentheses (for example `^[A-Za-z0-9][A-Za-z0-9._:+@/()-]*(?: [A-Za-z0-9()][A-Za-z0-9._:+@/()-]*)*$`, max 128 chars), and a `_is_model_label(text)` that is true only when `_MODEL_LABEL_RE` matches AND `_looks_like_path(text)` is false AND no whitespace-separated token of the text satisfies `_looks_like_path` (measured at authoring: `_looks_like_path("x /srv/y")` is `False`, so a space would otherwise let an embedded absolute path through) AND the text contains no quote or shell metacharacter (the regex already excludes them). In `_project_scalar`, add a branch BEFORE the generic `_CLOSED_VOCABULARY_KEYS` check: `if key == "model":` accept a pseudonym or `_is_model_label`, else raise `PrivacyRefusal` naming the reason (path vs not-a-label, matching the existing messages). In `run_analytics`, add `_model_label(value)` returning the stripped text when `privacy._is_model_label` holds and `""` otherwise, used by `_model_of` and `_verify_model_of` only; `_label` itself is unchanged. Put a comment on `_MODEL_LABEL_RE` citing the `_LABEL_RE` comment ("It may NOT contain a path separator, a space, a quote or a shell metacharacter, which is what keeps a command line or an absolute path out of a categorical field") as the basis: the space exclusion exists to keep command lines and paths out, which the path checks here still do for this one key, and `_LABEL_RE` already relaxes `/` for `model` for the same reason.
  - Depends on: E-01
  - Expected outcome: `project_metric_facts({"model": "Gemini 3.8 Flash (High)"})` returns it unchanged; `{"model": "/abs/x"}`, `{"model": "x /abs/y"}`, `{"model": "a ~/b"}`, `{"model": "../m"}`, `{"model": "rm -rf; x"}`, `{"model": 'a "b"'}` all raise `PrivacyRefusal`; `{"outcome": "has spaces"}` still raises (other keys unchanged).
  - Execution state: pending

### Task group 4: prove it

- [ ] E-05 ADD BEHAVIORAL TESTS to `tests/test_run_analytics.py` using the existing `_write_run`/`_core_state` fixtures (pass `state_extra={"options": {...}}`): (1) a display-name run (`options.model = "Gemini 3.8 Flash (High)"`) yields that model on every non-event grain AND survives `build_cache_facts` / `project_run_facts` (the persisted `model` equals the display name); (2) `options.model = None` with `cost_attribution.model = "provider/model"` yields `"provider/model"`; (3) a verifier run (`verify_cost_attribution.model = "other/verifier"`, and separately only `verify_model = "other/verifier"`) yields a VERIFY phase fact with the verifier model and an EXECUTE phase fact with the executor model; (4) a no-verifier run yields the executor model on both phases; (5) PATH REFUSAL: `options.model` set to each of `_ABS_HOME`, `"x " + _ABS_HOME`, `"../escape"`, `"~/m"` yields `model == ""` from `build_run_facts` and the serialized projected facts contain neither `_ABS_HOME` nor `_HANDLE`; (6) projector direct cases from E-04's expected outcome, including a non-model key with a space still refused.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: all pass; (1), (2), (3) FAIL before the change; (4), (5) and the non-model refusal in (6) pass before and after.
  - Execution state: pending

- [ ] E-06 CONFIRM THE EXISTING PRIVACY AND LABEL TESTS STAY GREEN, unchanged: `PrivacyBoundaryTests` (both tests, including the shipped leak detector reporting clean over projected facts), `UsageComponentMapTests.test_usage_component_label_safety_and_containment`, and `ProvenanceTests.test_value_validation_defaults_and_refusals`. Do not edit them.
  - Depends on: E-05
  - Expected outcome: all listed tests pass after the change, with no edits to them in the diff.
  - Execution state: pending

- [ ] E-07 RUN THE BARE SUITE `python3 -m pytest` before and after the change and compare failing node IDs; then re-run E-01(b) on the same real agy run.
  - Depends on: E-06
  - Expected outcome: the after-minus-before failing node set is empty; the real run now yields `model == 'Gemini 3.8 Flash (High)'` on its non-event facts.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `run_analytics_privacy` is the ONE persistence boundary ("the projector is the boundary, and a filter here would be a second one", `run_analytics._metric_payload` docstring). A model fix that only changes `run_analytics._label` would therefore still be refused at `project_metric_facts`, which is why E-04 changes both through one rule.
- `_LABEL_RE`'s comment already treats `model` as a special case (it permits `/` because `provider/model` is legitimate), which is the precedent for a model-specific relaxation that keeps the path guard.
- The producer contract is pinned: `runner_shared.COST_ATTRIBUTION_KEY = "cost_attribution"`, and `oc_runipd` writes `"verify_" + COST_ATTRIBUTION_KEY` and `verify_model` only when a verifier profile resolves; `agy_runipd` writes `cost_attribution.model = effective_model`, the same value as `options.model`.
- `run_analytics_query` surfaces a "model identity is near-absent" caveat keyed on `run_analytics_statistics.CORPUS_BASELINE["model_identity_coverage"]`, a review-time snapshot; this plan does not edit that constant (it describes the historical corpus it was measured on).
- Tests exercise behavior (maintainer ruling 2026-09-26: no source-text or structure pins). Suites run BARE as `python3 -m pytest`; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `61ef21d8` on this repo's `.aw/records/runs/`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `run_analytics._label` via `_model_of` | A display-name model is dropped to `''`. | 5 agy runs with `options.model = 'Gemini 3.8 Flash (High)'` -> `_model_of == ''`; `build_run_facts(run-20260926T042128Z-3748222)` -> `{('ipd',''),('run',''),('attempt',''),('event',''),('phase','')}`. |
| F-2 | HIGH | `run_analytics_privacy._project_scalar` | The persistence boundary refuses the display name independently of `_label`. | `project_metric_facts({'model':'Gemini 3.8 Flash (High)'})` -> `PrivacyRefusal: key 'model' is not a short closed-vocabulary label (no spaces, quotes or free text)`. |
| F-3 | MEDIUM | `run_analytics._model_of` | No fallback to `cost_attribution.model`. Latent locally: all 24 runs carrying `cost_attribution` have it equal to `options.model`. | Survey over `.aw/records/runs/*/state.json`. |
| F-4 | MEDIUM | `run_analytics.build_run_facts` PHASE loop | The VERIFY phase fact is credited with the executor's model. Latent locally: 0 runs carry `verify_cost_attribution`. | Same survey; one `model=model` for both loop entries. |
| F-5 | HIGH (design hazard) | `run_analytics_privacy._looks_like_path` | Admitting spaces naively would admit an embedded path: `_looks_like_path('x /srv/y')` is `False`. | Measured at authoring; E-04 adds a per-token path check and E-05 case (5) pins it. |
| F-6 | INFO | commit `b47d7816` | It normalized only the history actor (`driver_actor`), not `options.model`; analytics is unaffected. | All 5 display-name runs still hold the raw display name in `options.model`. |

## Proposed changes (ordered, validatable)

1. E-01 reproduces all causes.
2. E-02 adds the `cost_attribution` fallback.
3. E-03 attributes the VERIFY phase to the verifier's model.
4. E-04 admits display names for `model` only, in both the reader and the projector, with a strengthened path check.
5. E-05 adds behavioral tests; E-06 confirms existing privacy tests unchanged; E-07 runs the suite and re-measures the real run.

## Deferred / out of scope (with reason)

- Refreshing `run_analytics_statistics.CORPUS_BASELINE["model_identity_coverage"]` and the query caveat.
  - Carrier-Declined: that constant is a dated snapshot of the corpus it was measured on; re-baselining it is a separate measurement decision, and the caveat is advisory text, not a wrong answer.
- Normalizing the agy display name at the producer (so `options.model` is always an id).
  - Carrier-Declined: the producer is outside this consumer fix's fence (the backlog item states it is a CONSUMER change), and the raw display name is what the host reported.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/runner_shared.py` is READ for `COST_ATTRIBUTION_KEY` only; the runners are not modified.
- Scope-Paths justification: `run_analytics.py` holds the readers and the phase loop; `run_analytics_privacy.py` holds the persistence boundary that must admit the same values; `tests/test_run_analytics.py` holds the existing fixtures and privacy tests.

## Required tests / validation

- New behavioral cases in `tests/test_run_analytics.py` (E-05) with (1) to (3) shown FAILING before the change; existing privacy and label tests unchanged and green (E-06).
- Bare `python3 -m pytest` before and after, plus a re-measurement on a real display-name run (E-07).

## Spec / documentation sync

- N/A for specs: spec `25kzda`'s privacy clause requires "closed-vocabulary labels" and "no absolute path"; a model display name is a host-reported identifier, not free text, and the path refusals are retained and strengthened (F-5). No `.spec.md` is in `- Scope-Paths:`.
- No user docs change.

## Open questions

### OQ-01: Does admitting spaces in `model` weaken the privacy boundary?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: Not if the path checks are kept and tightened, from repository evidence. `_LABEL_RE`'s own comment states the space exclusion exists to keep "a command line or an absolute path out of a categorical field"; E-04 keeps `_looks_like_path`, adds a per-token path check closing the embedded-path route measured in F-5, keeps quotes and shell metacharacters excluded, applies only to the `model` key, and E-06 requires the shipped leak detector test over projected facts to stay green unchanged.

### OQ-02: Which grains get the verifier model?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: The VERIFY phase fact only. The backlog item asks to "bind the verifier phase's model to the conditional verify_cost_attribution"; the IPD and RUN grains merge execute and verify usage and the ATTEMPT grain is the executor's attempt, so none has a single verifier identity.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the per-run survey rows, the `(grain, model)` set for one display-name run, and the projector refusal text, with the HEAD hash.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of `_model_of`; paste the two `sys.modules` import-graph checks (before and after) showing the same answer; paste `_model_of` results for the fallback and both-empty states.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of `_verify_model_of` and the PHASE loop; paste EXECUTE and VERIFY phase-fact models for a verifier run and a no-verifier run.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the diff of `run_analytics_privacy` (`_MODEL_LABEL_RE`, `_is_model_label`, the `model` branch) and of `_model_label`; paste the outcome of every projector call listed in E-04's expected outcome.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_run_analytics.py -o addopts="" -q` passing with its count; then the same with the E-02, E-03 and E-04 hunks temporarily reverted, showing (1) to (3) FAILING and (4), (5) and the non-model refusal passing; then passing again after restoring.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste a narrowed run of the four named existing tests passing, and `git diff --stat` / a diff excerpt showing none of them was edited.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER, the after-minus-before failing node-ID set (must be empty), and the post-change `(grain, model)` set for the same real agy run.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Run-analytics stops blanking the model for Antigravity runs (whose recorded model is a display name like `Gemini 3.8 Flash (High)`), falls back to the resolved model the runner already records when no `--model` was passed, and credits the verify phase to the verifier's model when one was recorded. To do that, the persisted `model` field (and ONLY that field) accepts spaces and parentheses; paths are still refused, and more strictly than today because an embedded path after a space is now caught. This graduates backlog `lixqyc` and inherits its `- Blocks-Release: next`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/run_analytics.py` (`_model_of`, new `_verify_model_of`/`_model_label`, the PHASE loop in `build_run_facts`), `agent_workflows/run_analytics_privacy.py` (new model label rule and the `model` branch of `_project_scalar`), and `tests/test_run_analytics.py`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-05 must show the new tests FAILING before the change. No test may assert on source text.

GENUINE STOP CONDITION: if E-04's per-token path check cannot be made to refuse every E-05 case (5) input while admitting the display name, stop and report rather than widening the label further.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `lixqyc` `done` with `--evidence` citing the executed plan; its release gate is preserved by that handoff.
