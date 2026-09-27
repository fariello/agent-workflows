# IPD: Report the recorded model in run-analytics facts, including display-name models and the verify phase

- Date: 2026-09-26
- Kind: child
- Concern: RUN-ANALYTICS FACTS REPORT `model=''` FOR RUNS THAT RECORDED A MODEL. Three independent causes, re-verified at HEAD `61ef21d8`. (1) DISPLAY NAME DROPPED: every Antigravity run since the display name began being frozen (5 of the 24 runs under `.aw/records/runs/` carrying `options.cost_attribution`, all agy: `run-20260926T013533Z-3116868`, `run-20260926T025247Z-3448107`, `run-20260926T042128Z-3748222`, `run-20260926T051623Z-115951`, `run-20260926T051642Z-116672`) records `options.model = 'Gemini 3.8 Flash (High)'`, and `run_analytics._model_of` returns `''` for all five because `run_analytics._label` rejects anything failing `run_analytics_privacy._LABEL_RE` (no spaces or parentheses). `run_analytics.build_run_facts` on `run-20260926T042128Z-3748222` yields `model=''` at every grain. Independently, the persistence boundary `run_analytics_privacy.project_metric_facts` would REFUSE the value even if `_label` passed it (`key 'model' is not a short closed-vocabulary label`), because `model` is in `_CLOSED_VOCABULARY_KEYS` and `_project_scalar` applies the same regex. (2) NO FALLBACK: `_model_of` reads only `options.model` and never `options[runner_shared.COST_ATTRIBUTION_KEY]["model"]`, which `runner_shared.cost_attribution_record` fills with the host's resolved default when `options.model` is None. No local run shows this shape today (every recorded run has both equal), so it is a latent gap on the oc path where no `--model` is passed, which is the case the `w33lrl` producer was written for. (3) VERIFY MISATTRIBUTED: `build_run_facts` computes one `model` per run and passes it to BOTH the `Phase.EXECUTE` and `Phase.VERIFY` phase facts, although `oc_runipd` writes `options.verify_model` and `options["verify_" + COST_ATTRIBUTION_KEY]` when a verifier profile is resolved. NOTE on commit `b47d7816`: it made `runner_shared.driver_actor` render `model=Gemini-3.8-Flash-High` via `_actor_token`, but that changes only the history actor string; `options.model` still holds the raw display name (verified on all five runs above), so analytics is unaffected by that commit.
- Scope: IN: (a) `run_analytics._model_of` falls back to `options[COST_ATTRIBUTION_KEY]["model"]` when `options.model` is empty; (b) a new `run_analytics._verify_model_of` (`options["verify_" + COST_ATTRIBUTION_KEY]["model"]`, then `options.verify_model`, then the executor model) used for the `Phase.VERIFY` phase fact; (c) a MODEL-ONLY label rule admitting a display name (letters, digits, the existing separators, plus single spaces and parentheses) in both `run_analytics` (a `_model_label` used by the two model readers) and `run_analytics_privacy._project_scalar` (a `model`-key branch), while `_looks_like_path` and an embedded-path check still refuse paths; (d) behavioral tests in `tests/test_run_analytics.py`. OUT: widening any other label key; changing `runner_shared.cost_attribution_record`, the runners, or `driver_actor`; normalizing stored display names; recomputing cost; changing `aw runs` rendering.
- Scope-Paths: agent_workflows/run_analytics.py, agent_workflows/run_analytics_privacy.py, tests/test_run_analytics.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: lixqyc
- Blocks-Release: next
- Set: rafactmodel
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7hek98
- Approval: 2026-09-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; 8 findings PR-1001..PR-1008 all FIXED, 4 decisions D-1..D-4 recorded; review record written. Re-drove every code claim (F-1..F-5 hold) and PROTOTYPED E-04's regex: it admits the display name and refuses all listed paths. PR-1001 (HIGH): E-01's corpus survey finds 0 runs from a lane because records/runs/ is gitignored and execute turns are isolated, and 0 is indistinguishable from 'defect absent'; now mandates runner_shared.runs_repo_root (measured 0 vs 283). PR-1002: E-02's lazy-import instruction was unsatisfiable; key now defined locally and pinned by a test. PR-1003: the loop's first entry is Phase.REVIEW for a review item. PR-1005: OQ-01's flat 'no weakening' was wrong (a bare handle is admitted and sanitizer-flagged); limit now stated in E-04, OQ-01 and the gate with the producer-normalization alternative named for the human. aw ipd lint --phase review-finalize conforming; aw check plans clean for this plan.

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog lixqyc (reclassified bug + Blocks-Release next on 2026-09-26). All three causes re-measured at HEAD 61ef21d8 against the repo's own recorded runs; the privacy projector was found to refuse display names independently of _label, and an embedded-path gap in the proposed widening was found and fenced.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make run-analytics facts carry the model a run actually recorded, for both hosts and for the verify phase separately, without letting a path or free text into the persisted `model` field.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE at the executing HEAD. (a) For every run `state.json` carrying `options.cost_attribution` or `options.verify_cost_attribution`, paste `options.model`, `cost_attribution.model`, `options.verify_model`, `verify_cost_attribution.model`, and `run_analytics._model_of(state)`. (b) Paste the set of `(grain, model)` pairs from `run_analytics.build_run_facts` on one display-name agy run. (c) Paste the outcome of `run_analytics_privacy.project_metric_facts({"model": "Gemini 3.8 Flash (High)"})`. If every display-name run already yields its model, drop cause (1) and say so.
  - RESOLVE THE RUNS ROOT; DO NOT GLOB `.aw/records/runs/` FROM THE CWD. THIS IS THE ITEM MOST LIKELY TO BE REPORTED AS "NO RUNS FOUND" AND SILENTLY SKIPPED, because an execute turn runs in an ISOLATED LANE WORKTREE by default and `records/runs/` is GITIGNORED (`.aw/.gitignore`: `records/runs/`), so a lane has NO runs tree at all. Use the shipped resolver, `runner_shared.runs_repo_root(Path("."))` (which delegates to `attention._resolve_runs_repo_root`), and enumerate under THAT root, or equivalently `run_viewer.discover_run_dirs(runner_shared.runs_repo_root(Path(".")))`. Measured FROM THIS REVIEW'S OWN LANE: the lane's `.aw/records/runs` does not exist, `run_viewer.discover_run_dirs(Path("."))` returns 0, and the resolved root returns 283. The identical trap is already documented twice in `runner_shared` (`runs_repo_root`'s docstring records `0` versus `246` from lane `vddpml`, and the `_SESSION_ID_KEYS` census notes "this lane has no `.aw/records/runs` corpus").
  - PARTS (b) AND (c) DO NOT DEPEND ON THE CORPUS AND MUST BE PASTED EVEN IF (a) FINDS NOTHING: (c) is a pure function call, and (b) can use any display-name run the resolver finds. If the resolved root genuinely holds NO run with `cost_attribution`, say so explicitly, paste the resolver's own answer and the run count proving you looked in the right place, and proceed on (b)/(c) plus E-05's fixtures; a synthetic `state.json` built with the `tests/test_run_analytics.py` fixtures is an acceptable substitute for (a) PROVIDED you label it synthetic. Do NOT report the whole item blocked, and do NOT record "0 runs" as evidence that the defect is absent.
  - Depends on: none
  - Expected outcome: the display-name runs give `_model_of == ''` and every fact `model == ''`; the projector raises `PrivacyRefusal` for the display name.
  - Execution state: pending

### Task group 2: readers

- [ ] E-02 ADD THE COST-ATTRIBUTION FALLBACK to `run_analytics._model_of`: read `options.model`; if it yields an empty label, read `options.get(COST_ATTRIBUTION_KEY)` and, when it is a mapping, its `"model"`. Both reads go through the model label rule of E-04.
  - DO NOT IMPORT `runner_shared`; DEFINE THE KEY LOCALLY AS A STRING AND PIN THE AGREEMENT IN A TEST. The plan originally said to import the constant, lazily if needed, and to keep the import graph unchanged. That instruction is self-defeating: a LAZY import still adds `runner_shared` to `sys.modules` the first time `_model_of` runs, so the stated check cannot pass while the import exists, and it makes the answer depend on whether the function has been called yet. Measured at review: `import agent_workflows.run_analytics` leaves `agent_workflows.runner_shared` ABSENT from `sys.modules` today; `runner_shared.py` is 32452 lines against `run_analytics.py`'s 888, and adding it costs about 48ms of import time (118ms -> 166ms for the two-module import, min of 3). So write `_COST_ATTRIBUTION_KEY = "cost_attribution"` in `run_analytics` with a comment naming `runner_shared.COST_ATTRIBUTION_KEY` as the contract it mirrors, and add ONE assertion to E-05 that the two are equal (importing `runner_shared` inside the TEST, where the cost is irrelevant and the drift is what matters). This is the same "one definition, pinned by a test" posture the repo already uses for cross-module string contracts, and it keeps the analytics import graph free of the runner.
  - Depends on: E-01
  - Expected outcome: a state with `options.model = None` and `cost_attribution.model = "provider/model"` yields `"provider/model"`; a state with both empty yields `""`; `import agent_workflows.run_analytics` still leaves `runner_shared` out of `sys.modules`.
  - Execution state: pending

- [ ] E-03 ADD `run_analytics._verify_model_of(state, executor_model)`: return the first non-empty model label of `options["verify_" + _COST_ATTRIBUTION_KEY]["model"]`, `options["verify_model"]`, else `executor_model`. In `build_run_facts`, compute it once per run beside `model = _model_of(state)` and pass it as `model=` for the `Phase.VERIFY` entry of the PHASE-grain loop only (the loop over `(Phase.EXECUTE ..., exec_usage), (Phase.VERIFY, verify_usage)`), keeping the executor model on every other fact. The IPD, ATTEMPT and RUN grains keep the executor model: they merge or precede the phases and have no single verifier identity.
  - MIND THE FIRST LOOP ENTRY: it is NOT unconditionally `Phase.EXECUTE`. Its expression is `Phase.EXECUTE if item_phase is Phase.EXECUTE else item_phase`, so a `review` item yields `Phase.REVIEW` there (`_phase_of` returns `Phase.REVIEW` for `action == "review"`). Bind the verifier model to the SECOND entry, whose phase is the literal `Phase.VERIFY`, rather than writing a conditional on the loop variable that could also catch `Phase.REVIEW`. The simplest correct form is to put the model in the loop tuple beside the usage, so each entry carries its own.
  - Depends on: E-02
  - Expected outcome: a run whose options carry `verify_cost_attribution.model = "other/verifier"` yields a VERIFY phase fact with `model == "other/verifier"` and an EXECUTE phase fact with the executor model; a run with no verifier fields yields the executor model on both; a `review` item's first-entry phase fact still carries the executor model.
  - Execution state: pending

### Task group 3: admit display names for the model field only

- [ ] E-04 DEFINE ONE MODEL LABEL RULE in `run_analytics_privacy` and use it in both places. Add `_MODEL_LABEL_RE` permitting `_LABEL_RE`'s character class plus single interior spaces and parentheses (for example `^[A-Za-z0-9][A-Za-z0-9._:+@/()-]*(?: [A-Za-z0-9()][A-Za-z0-9._:+@/()-]*)*$`, max 128 chars), and a `_is_model_label(text)` that is true only when `_MODEL_LABEL_RE` matches AND `_looks_like_path(text)` is false AND no whitespace-separated token of the text satisfies `_looks_like_path` (measured at authoring: `_looks_like_path("x /srv/y")` is `False`, so a space would otherwise let an embedded absolute path through) AND the text contains no quote or shell metacharacter (the regex already excludes them). In `_project_scalar`, add a branch BEFORE the generic `_CLOSED_VOCABULARY_KEYS` check: `if key == "model":` accept a pseudonym or `_is_model_label`, else raise `PrivacyRefusal` naming the reason (path vs not-a-label, matching the existing messages). In `run_analytics`, add `_model_label(value)` returning the stripped text when `privacy._is_model_label` holds and `""` otherwise, used by `_model_of` and `_verify_model_of` only; `_label` itself is unchanged. Put a comment on `_MODEL_LABEL_RE` citing the `_LABEL_RE` comment ("It may NOT contain a path separator, a space, a quote or a shell metacharacter, which is what keeps a command line or an absolute path out of a categorical field") as the basis: the space exclusion exists to keep command lines and paths out, which the path checks here still do for this one key, and `_LABEL_RE` already relaxes `/` for `model` for the same reason.
  - THE PROPOSED REGEX WAS PROTOTYPED AT REVIEW AND ADMITS/REFUSES EXACTLY THE LISTED SET, so it is a measured starting point and not a guess. Verified with the literal pattern above plus the three guards: `Gemini 3.8 Flash (High)`, `provider/model` and `its_direct/pt3-claude-opus-5-1m-us` are admitted; `/abs/x`, `x /abs/y`, `a ~/b`, `../m`, `rm -rf; x`, `a "b"`, `C:\Users\<name>`, `x C:/Users/<name>` and a double space are all refused. Driven through a patched `_project_scalar`, `project_metric_facts({"model": "Gemini 3.8 Flash (High)"})` returned it unchanged and `{"outcome": "has spaces"}` still raised.
  - WHICH GUARD EARNS ITS PLACE, because the plan's stated rationale for the per-token check is slightly wrong and the correction matters for anyone tempted to simplify. The regex ALONE already refuses `x /srv/y`, `a ~/b` and `x ../y`, because a space-separated continuation token must START with `[A-Za-z0-9()]` and so cannot start with `/`, `~` or `.`. Of the listed cases the per-token check is load-bearing for exactly ONE, `x C:/Users/<name>` (a Windows drive path mid-string, which the regex admits since `C:/Users/<name>` is all label characters). KEEP THE PER-TOKEN CHECK: it is the guard covering the Windows form and it is cheap defense in depth. Do NOT drop it on the grounds that the regex "already handles" the POSIX cases, and do NOT drop the whole-string `_looks_like_path` either (it catches a bare leading `~` or `..` that the regex's first-character class also rejects, so the two overlap deliberately).
  - THE HONEST LIMIT OF THIS WIDENING, WHICH E-05 CASE (5) MUST NOT BE READ AS COVERING. Admitting spaces means the `model` key can now carry a bare IDENTIFIER that is not path-shaped, and the leak sanitizer would flag it. Measured at review: the bare maintainer handle (no path, no separator) IS admitted by this rule and IS reported by `leak_sanitizer.scan_text` as rule `handle`, as is `Gemini 3.8 Flash (High) <handle>`. That is a REAL narrowing of the boundary and it is accepted here for a stated reason: the value is host-reported and the alternative (blanking every Antigravity model) is the defect being fixed. It is bounded by the fact that `model` is written from `options.model` / `cost_attribution.model` only, both of which a HOST supplies, never a human free-text field. The path class, which is what `_LABEL_RE`'s comment names as the thing to keep out, remains fully refused and is strictly tightened. State this limit in the `_MODEL_LABEL_RE` comment so the next reader does not believe spaces are free.
  - Depends on: E-01
  - Expected outcome: `project_metric_facts({"model": "Gemini 3.8 Flash (High)"})` returns it unchanged; `{"model": "/abs/x"}`, `{"model": "x /abs/y"}`, `{"model": "a ~/b"}`, `{"model": "../m"}`, `{"model": "rm -rf; x"}`, `{"model": 'a "b"'}` all raise `PrivacyRefusal`; `{"outcome": "has spaces"}` still raises (other keys unchanged). A Windows drive path after a space (`x C:/Users/<name>`) also raises, which is the per-token check's own case.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-05 ADD BEHAVIORAL TESTS to `tests/test_run_analytics.py` using the existing `_write_run`/`_core_state` fixtures (pass `state_extra={"options": {...}}`): (1) a display-name run (`options.model = "Gemini 3.8 Flash (High)"`) yields that model on every non-event grain AND survives `build_cache_facts` / `project_run_facts` (the persisted `model` equals the display name); (2) `options.model = None` with `cost_attribution.model = "provider/model"` yields `"provider/model"`; (3) a verifier run (`verify_cost_attribution.model = "other/verifier"`, and separately only `verify_model = "other/verifier"`) yields a VERIFY phase fact with the verifier model and an EXECUTE phase fact with the executor model; (4) a no-verifier run yields the executor model on both phases; (5) PATH REFUSAL: `options.model` set to each of `_ABS_HOME`, `"x " + _ABS_HOME`, `"../escape"`, `"~/m"` yields `model == ""` from `build_run_facts` and the serialized projected facts contain neither `_ABS_HOME` nor `_HANDLE`; (6) projector direct cases from E-04's expected outcome, including a non-model key with a space still refused.
  - ALSO ADD, as case (7), the `_COST_ATTRIBUTION_KEY` agreement assertion E-02 requires: import `runner_shared` INSIDE the test and assert `run_analytics._COST_ATTRIBUTION_KEY == runner_shared.COST_ATTRIBUTION_KEY`. This is the single thing standing between the locally defined string and silent drift, and putting the import in the test keeps it out of the analytics import graph.
  - CASE (1) SAYS "EVERY NON-EVENT GRAIN" AND THAT WORDING IS CORRECT FOR A MEASURED REASON worth stating so nobody "fixes" it: `model` is in `run_analytics_privacy.ALLOWED_METRIC_KEYS` and is NOT in `ALLOWED_EVENT_KEYS` (verified at review), and `project_run_facts` routes the EVENT grain through `project_event_facts`. So an event-grain fact legitimately carries no model, and asserting one there would fail against a correct implementation. `_metric_payload` also OMITS the key entirely when `fact.model` is empty (`if fact.model:`), so case (5) should assert the key is ABSENT from the projected payload rather than present-and-empty.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: all pass; (1), (2), (3) FAIL before the change; (4), (5), (7) and the non-model refusal in (6) pass before and after.
  - Execution state: pending

- [ ] E-06 CONFIRM THE EXISTING PRIVACY AND LABEL TESTS STAY GREEN, unchanged: `PrivacyBoundaryTests` (both tests, including the shipped leak detector reporting clean over projected facts), `UsageComponentMapTests.test_usage_component_label_safety_and_containment`, and `ProvenanceTests.test_value_validation_defaults_and_refusals`. Do not edit them.
  - ALL FOUR WERE CONFIRMED PRESENT AT REVIEW and none of them can be satisfied by the widening, which is why they are the right guards: `ProvenanceTests` refuses a note with spaces through `run_analytics_schema._LABEL_RE`, a THIRD copy of the label rule in a different module that this plan deliberately does not touch; `UsageComponentMapTests` pins component NAMES through `_LABEL_RE` plus `_looks_like_path`; and `PrivacyBoundaryTests` runs the shipped detector over the serialized projected facts. That last one is the real safety net, and note what it does and does not prove: its fixture's model field is not a leaky value, so it proves the widening did not break the boundary for the values it exercises, NOT that no admissible model string could ever carry an identifier (see E-04's stated limit). Do not present a green run of it as proof of the latter.
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

F-1 through F-6 measured at HEAD `61ef21d8` on this repo's runs corpus, and ALL SIX re-verified at review HEAD `e762c9c5` (F-1, F-2, F-3, F-5 re-driven directly; F-4 and F-6 re-read in the code). F-7 through F-12 were added at review.

THE CORPUS ROWS OF F-1, F-3 AND F-4 COULD NOT BE RE-COUNTED AT REVIEW, and that is a property of where a review runs rather than a doubt about the claims: this review executed in a lane worktree with no runs tree (F-7), so the "5 of 24 runs" and "0 runs carry `verify_cost_attribution`" counts are the author's, not re-measured. Every one of those findings was instead re-confirmed from CODE, which is the stronger evidence for a code defect: `_model_of` demonstrably returns `''` for the display name, the projector demonstrably refuses it, `_model_of` demonstrably has no fallback, and the PHASE loop demonstrably passes one `model` to both entries. The counts are corpus colour; the defects are in the functions.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `run_analytics._label` via `_model_of` | A display-name model is dropped to `''`. | 5 agy runs with `options.model = 'Gemini 3.8 Flash (High)'` -> `_model_of == ''`; `build_run_facts(run-20260926T042128Z-3748222)` -> `{('ipd',''),('run',''),('attempt',''),('event',''),('phase','')}`. |
| F-2 | HIGH | `run_analytics_privacy._project_scalar` | The persistence boundary refuses the display name independently of `_label`. | `project_metric_facts({'model':'Gemini 3.8 Flash (High)'})` -> `PrivacyRefusal: key 'model' is not a short closed-vocabulary label (no spaces, quotes or free text)`. |
| F-3 | MEDIUM | `run_analytics._model_of` | No fallback to `cost_attribution.model`. Latent locally: all 24 runs carrying `cost_attribution` have it equal to `options.model`. | Survey over `.aw/records/runs/*/state.json`. |
| F-4 | MEDIUM | `run_analytics.build_run_facts` PHASE loop | The VERIFY phase fact is credited with the executor's model. Latent locally: 0 runs carry `verify_cost_attribution`. | Same survey; one `model=model` for both loop entries. |
| F-5 | HIGH (design hazard) | `run_analytics_privacy._looks_like_path` | Admitting spaces naively would admit an embedded path: `_looks_like_path('x /srv/y')` is `False`. | Measured at authoring; E-04 adds a per-token path check and E-05 case (5) pins it. |
| F-6 | INFO | commit `b47d7816` | It normalized only the history actor (`driver_actor`), not `options.model`; analytics is unaffected. | All 5 display-name runs still hold the raw display name in `options.model`. |
| F-7 | HIGH (executability) | E-01's corpus survey | THE SURVEY CANNOT SEE ANY RUN FROM A LANE. `records/runs/` is gitignored, so an isolated execute worktree has no runs tree and a CWD-relative glob returns zero. E-01 now mandates `runner_shared.runs_repo_root` and forbids reading "0 runs" as absence of the defect. | Measured from THIS review's lane: `.aw/records/runs` absent; `run_viewer.discover_run_dirs(Path("."))` -> 0; `discover_run_dirs(runs_repo_root(Path(".")))` -> 283. The same trap is documented in `runner_shared.runs_repo_root`'s docstring (0 vs 246 from lane `vddpml`) and beside `_SESSION_ID_KEYS`. |
| F-8 | MEDIUM | E-02's import instruction | SELF-DEFEATING AS AUTHORED: a lazy import still enters `sys.modules` on first call, so the "keep the answer unchanged" check cannot pass while the import exists, and the answer becomes call-order dependent. E-02 now defines the key locally and pins the agreement in a test. | `import agent_workflows.run_analytics` -> `runner_shared` absent from `sys.modules`; `runner_shared.py` 32452 lines vs 888; two-module import costs about 48ms more (118ms -> 166ms, min of 3). |
| F-9 | MEDIUM | `build_run_facts` PHASE loop, FIRST entry | The first loop entry is `Phase.EXECUTE if item_phase is Phase.EXECUTE else item_phase`, so it yields `Phase.REVIEW` for a `review` item. A conditional written on the loop variable could mis-bind the verifier model. E-03 now says to bind the SECOND entry and to carry the model in the loop tuple. | `_phase_of` returns `Phase.REVIEW` for `action == "review"`; the loop expression read verbatim. |
| F-10 | MEDIUM | E-04's rationale for the per-token check | THE STATED REASON IS MOSTLY WRONG, though the guard is still needed. The regex alone already refuses `x /srv/y`, `a ~/b` and `x ../y`, because a continuation token must start with `[A-Za-z0-9()]`. The per-token check is load-bearing for exactly one listed case, the Windows `x C:/Users/<name>`. Recorded so nobody simplifies the guard away on a wrong premise. | Per-case guard attribution driven at review: `regex=False` for the POSIX cases; `x C:/Users/<name>` gives `regex=True, whole_path=False, token_path=True`. |
| F-11 | MEDIUM (accepted limit) | the widened `model` rule | ADMITTING SPACES ADMITS A NON-PATH IDENTIFIER. A bare maintainer handle is admitted by the new rule and IS flagged by the shipped leak sanitizer (rule `handle`), as is `Gemini 3.8 Flash (High) <handle>`. Accepted deliberately (the value is host-supplied, never human free text) and now stated in E-04 and in the gate rather than left implicit. | Driven at review against `leak_sanitizer.build_ruleset(Path.cwd())` with a runtime-composed handle. |
| F-12 | INFO | `run_analytics_schema._LABEL_RE`; `Fact.model` | A THIRD label rule exists in the schema module (used for `Value.note` and component names), and it is NOT a gate on `Fact.model`: `Fact` has no `__post_init__` validating `model`. So exactly two surfaces must change, as the plan says, and no third refusal will surprise the executor. | `grep -n "_LABEL_RE" agent_workflows/run_analytics_schema.py` -> the note check and the definition only; `Fact` declares `model: str = ""` with no validator. |

## Proposed changes (ordered, validatable)

1. E-01 reproduces all causes, against the RESOLVED runs root (not the lane's absent one).
2. E-02 adds the `cost_attribution` fallback, with the key defined locally and pinned by a test.
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
- Under-scope: none remaining. `agent_workflows/runner_shared.py` is not imported by the changed code at all after the review's E-02 correction (the key is defined locally and its agreement with `runner_shared.COST_ATTRIBUTION_KEY` is pinned in a TEST, which is inside the declared `tests/test_run_analytics.py`), so no fourth path is read or written. `run_analytics_schema.py` is deliberately NOT changed: its own `_LABEL_RE` governs `Value.note` and component names, and it is not a gate on `Fact.model` (F-12), so two surfaces is the complete set.
- Scope-Paths justification: `run_analytics.py` holds the readers and the phase loop; `run_analytics_privacy.py` holds the persistence boundary that must admit the same values; `tests/test_run_analytics.py` holds the existing fixtures and privacy tests.
- WHY EACH CAUSE NEEDS ITS OWN FIX, verified at review so the plan cannot be trimmed on a wrong assumption: E-02's fallback ALONE fixes the oc no-flag case with no label change (`cost_attribution.model` there is a resolvable id like `anthropic/claude-sonnet-4`, which today's `_LABEL_RE` already accepts), and it does NOT fix the agy case (where `options.model` and `cost_attribution.model` hold the SAME display name, so the fallback reads a second value the label rule rejects identically). E-04 is therefore load-bearing for the agy defect and E-02 for the oc one; neither substitutes for the other.

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
- Resolution or deferral rationale: YES, MEASURABLY, FOR THE NON-PATH IDENTIFIER CLASS; NO for the path class the guard was written against. The original answer here was a flat "not if the path checks are kept", and review found that too generous. What is proven: the PATH class stays fully refused and is strictly tightened (every case in E-05(5) refuses, including the Windows drive path the per-token check exists for), quotes and shell metacharacters stay excluded, and the rule applies to the `model` key alone. What is NOT true: that the boundary is unchanged. Measured at review, a bare maintainer handle (no path, no separator) IS admitted by the new rule and IS reported by the shipped leak sanitizer as rule `handle` (F-11). The narrowing is ACCEPTED on the ground that `model` is written only from host-supplied fields (`options.model`, `cost_attribution.model`), never from a human free-text field, and that the alternative is the defect being fixed (blanking every Antigravity model). `_LABEL_RE`'s comment names the command-line and absolute-path classes as what the space exclusion protects, and both remain excluded. E-06's leak-detector test stays green unchanged but does NOT prove the stronger claim, and E-04 now says so.
- Carrier-Declined: resolved in place with the limit stated rather than hidden; nothing outstanding after this plan executes.

### OQ-02: Which grains get the verifier model?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: The VERIFY phase fact only. The backlog item asks to "bind the verifier phase's model to the conditional verify_cost_attribution"; the IPD and RUN grains merge execute and verify usage and the ATTEMPT grain is the executor's attempt, so none has a single verifier identity. CONFIRMED AT REVIEW that the grain reasoning is accurate: `build_run_facts` merges the two phase usages into the IPD grain (`schema.merge_usage([exec_usage, verify_usage])`), so an IPD-grain fact genuinely spans both models and naming one would misattribute the other. Note also that the EVENT grain carries no model at all by allowlist design (`model` is absent from `ALLOWED_EVENT_KEYS`), so it is outside this question rather than an omission from it.
- Carrier-Declined: resolved in place from the item's own wording plus the merge code; nothing outstanding.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the per-run survey rows, the `(grain, model)` set for one display-name run, and the projector refusal text, with the HEAD hash.
  - ALSO paste the resolved runs root and the run count found under it (`runner_shared.runs_repo_root(Path("."))` and the number of run dirs), so the record proves the survey looked at a populated tree rather than an empty lane. A survey reporting zero runs WITHOUT this pair is not acceptable evidence. If the populated root genuinely holds no `cost_attribution` run, say so and label the synthetic substitute as such.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of `_model_of` and of the `_COST_ATTRIBUTION_KEY` definition with its contract comment; paste `python3 -c "import agent_workflows.run_analytics, sys; print('agent_workflows.runner_shared' in sys.modules)"` showing `False` AFTER the change; paste `_model_of` results for the fallback and both-empty states; paste the case (7) key-agreement assertion passing.
  - The diff must show NO `runner_shared` import in `run_analytics.py`, lazy or otherwise. A lazy import is not an acceptable alternative here (F-8): it would make the `sys.modules` answer depend on whether `_model_of` had been called yet.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of `_verify_model_of` and the PHASE loop; paste EXECUTE and VERIFY phase-fact models for a verifier run and a no-verifier run.
  - ALSO paste the phase-fact model for a `review`-action item, showing the first loop entry (whose phase is `Phase.REVIEW`, not `Phase.EXECUTE`) still carries the EXECUTOR model and was not bound to the verifier (F-9).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the diff of `run_analytics_privacy` (`_MODEL_LABEL_RE`, `_is_model_label`, the `model` branch) and of `_model_label`; paste the outcome of every projector call listed in E-04's expected outcome, INCLUDING the Windows `x C:/Users/<name>` case.
  - ALSO paste the per-guard attribution for the refusals: for each refused input, which of the three guards rejected it (regex, whole-string `_looks_like_path`, per-token). This is required because the per-token check is load-bearing for only one case (F-10) and a future reader must be able to see that rather than infer it, and because it proves the guards were actually wired rather than one of them being dead.
  - ALSO paste the `_MODEL_LABEL_RE` comment showing it states BOTH the basis (the `_LABEL_RE` comment's command-line/path rationale) AND the accepted limit from F-11 (a non-path identifier is now admissible on this key).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_run_analytics.py -o addopts="" -q` passing with its count; then the same with the E-02, E-03 and E-04 hunks temporarily reverted, showing (1) to (3) FAILING and (4), (5) and the non-model refusal passing; then passing again after restoring.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste a narrowed run of the four named existing tests passing, and `git diff --stat` / a diff excerpt showing none of them was edited.
  - STATE WHAT THE GREEN DETECTOR TEST DOES NOT PROVE, in one line: that its fixture's model is not a leaky value, so the pass shows the boundary intact for the values exercised and NOT that no admissible model string could carry an identifier (F-11). Do not present it as the latter.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER, the after-minus-before failing node-ID set (must be empty), and the post-change `(grain, model)` set for the same real agy run (resolved through `runs_repo_root`, per E-01).
  - The post-change `(grain, model)` set must show the model on the metric grains and NO model key on the `event` grain, which is correct by allowlist design and not a miss.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Run-analytics stops blanking the model for Antigravity runs (whose recorded model is a display name like `Gemini 3.8 Flash (High)`), falls back to the resolved model the runner already records when no `--model` was passed, and credits the verify phase to the verifier's model when one was recorded. To do that, the persisted `model` field (and ONLY that field) accepts spaces and parentheses; paths are still refused, and more strictly than today because an embedded path after a space is now caught. This graduates backlog `lixqyc` and inherits its `- Blocks-Release: next`.

THE PRIVACY DECISION YOU ARE ACTUALLY MAKING, stated plainly because it is the one part of this plan that trades something away and the original gate did not say so. Admitting spaces on `model` means that key can now carry a NON-PATH IDENTIFIER. Measured at review: a bare maintainer handle is admitted by the new rule and IS flagged by the shipped leak sanitizer (rule `handle`); so is `Gemini 3.8 Flash (High) <handle>`. The PATH class (absolute, `~`, `..`, Windows drive, and any of those embedded after a space) remains fully refused and is strictly tightened, which is what `_LABEL_RE`'s own comment names as the purpose of the space exclusion. The narrowing is bounded by provenance rather than by the regex: `model` is written only from `options.model` and `cost_attribution.model`, both HOST-supplied, never from a human free-text field. If you are not willing to accept that, the alternative is to normalize the display name at the producer (recorded as out of scope in Deferred) and this plan should not be approved as written.

WHAT THIS DOES NOT CHANGE: the event grain still carries no model (it is not in the event allowlist, by design); `run_analytics_schema`'s own label rule and `Value.note` are untouched; `CORPUS_BASELINE["model_identity_coverage"]` and the `aw runs query` caveat keyed on it are deliberately left stale (Deferred), so a reader who groups by model will still see the historical near-absence caveat after this ships.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/run_analytics.py` (`_model_of`, new `_verify_model_of`/`_model_label`, the new local `_COST_ATTRIBUTION_KEY`, the PHASE loop in `build_run_facts`), `agent_workflows/run_analytics_privacy.py` (new model label rule and the `model` branch of `_project_scalar`), and `tests/test_run_analytics.py`. Expected to need NO edit, and named so the reconciliation has something to check: `agent_workflows/runner_shared.py` (NOT imported by the changed code at all; the key agreement is pinned in the test instead), `agent_workflows/run_analytics_schema.py` (its own `_LABEL_RE` governs notes and component names and is not a gate on `Fact.model`), `run_analytics_privacy.ALLOWED_EVENT_KEYS` (the event grain carries no model by design), and `run_analytics_statistics.CORPUS_BASELINE` / `run_analytics_query`'s caveat (deliberately stale, see Deferred). If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-05 must show the new tests FAILING before the change. No test may assert on source text. THE THREE CLAIMS EASIEST TO FAKE HERE, named so they are checked: (a) the corpus survey, where "0 runs found" from an unresolved lane path looks identical to "the defect is absent" and must be accompanied by the resolved root and run count (F-7); (b) the import-graph claim, which must be re-measured AFTER the change and not asserted from the plan's own text (F-8); and (c) the privacy claim, where a green leak-detector test must not be presented as proof that no admissible model string can carry an identifier (F-11).

GENUINE STOP CONDITIONS: (1) if E-04's guards cannot be made to refuse every E-05 case (5) input while admitting the display name, stop and report rather than widening the label further; (2) if the resolved runs root is reachable but the display-name defect does NOT reproduce there (every display-name run already yields its model), stop and report, because the premise of cause (1) has changed and the privacy widening would then be buying nothing.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition to `executed/` is performed with `aw ipd finalize`, never a raw `git mv`; the RUNNER owns it when it executes this plan in a lane, and the executor otherwise performs it. Then close backlog `lixqyc` `done` with `--evidence` citing the executed plan. ORDER MATTERS AND WAS VERIFIED AT REVIEW: `check_engine.evaluate_blocking_close` on `lixqyc` today REFUSES `done` with "the work has not shipped (carrier is not executed/implemented)", which is correct and expected before this plan finalizes; the item must stay `graduated` until then, and the close becomes legitimate through the HANDOFF path once this plan is in `executed/` (it carries `- From-Backlog: lixqyc` and the same `- Blocks-Release: next`). Do not pre-close the item and do not de-gate it to force the close through.
