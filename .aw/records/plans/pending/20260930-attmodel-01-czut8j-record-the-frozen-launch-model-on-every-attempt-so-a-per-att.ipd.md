# IPD: Record the frozen launch model on every attempt so a per-attempt model exists at all

- Date: 2026-09-30
- Kind: child
- Concern: NO ATTEMPT RECORD IN THIS REPOSITORY CARRIES A MODEL, so every model question about a run is answered from ONE run-level field that is wrong whenever a run used two models, and is absent entirely on most runs. Three measured facts compose into that. FIRST, the attempt record built in `runner_shared.execute_item_core` has keys `number`, `started_at`, `starting_head`, `starting_branch`, `starting_status`, `prompt`, `prompt_sha256`, `session_id`, `log`, `recovery`, `action`, and gains `ended_at`, `exit_code`, `ending_head`, `ending_branch`, `ending_status`, `argv`, `cost`, `tokens` after the turn: there is no model key on any path, and `run_analytics_statistics.model_comparison`'s docstring states the same ("NO attempt-level model key anywhere"). SECOND, a VERIFIER turn legitimately runs a DIFFERENT model: `oc_runipd.run_opencode` selects `("verify_model", "verify_variant", "verify_agent")` when `use_verifier_launch=True`, so a `--verify-with` run spends under two identities while state records the executor's as the run's. THIRD, the run-level field is often empty: `oc_runipd.initialize_run` copies `resolved_launch.model` verbatim, which is `None` when no `--model` and no profile supplied one, and `agy_models.resolve_agy_default_model` returns `(None, "host-default")` when no `settings.json` exists, which `runner_shared.cost_attribution_record` normalizes to `""` (executed here: `{"host": "agy", "model": "", "model_source": "host-default", "card_reason": "host-card-not-in-any-readable-config"}`). Backlog `7yz545` measured the consequence at the corpus level: about 100 of 298 `state.json` files carry `options.model` or `options.cost_attribution.model`.
- Scope: Write the launch identity THIS turn was launched under onto THE ATTEMPT RECORD, at the one shared seam both hosts already reach, so a per-attempt model EXISTS to be read. Concretely: a new `attempt["model"]` plus `attempt["model_source"]` recorded from the same frozen `options` keys the turn's argv was built from, so an executor attempt records the executor's model and a verifier phase records the verifier's; the same two keys written on the two early-refusal attempt shapes and on the interrupted-attempt path, so an attempt that exists at all carries the field; and `attempt["verify_model"]` beside the existing `verify_cost`/`verify_tokens` when a verifier turn ran under a separate launch. EXCLUDES, deliberately and in order: observing what the HOST actually chose (Order 02 `ov2c9n`, because a frozen request and a host observation are different facts and must not be conflated in one key), and every CONSUMER of the new field (Order 03 `r5fk4k`, so a producer lands and is provable before any reader is repointed at it). EXCLUDES back-filling history: nothing here rewrites an existing `state.json`, for the reason `w33lrl` recorded when it added `cost_attribution` and deliberately did not back-fill.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_attempt_model_identity.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Backlog: 7yz545
- Set: attmodel
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: czut8j

## Workflow history

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `7yz545` as Order 01 of a three-child Set. THIS PLAN IS THE PRODUCER OF THE FIELD AND NOTHING ELSE, which is the split the item's own history argues for: `7hek98` (executed) put the CONSUMER side in and named "changing `runner_shared.cost_attribution_record`, the runners, or `driver_actor`" as out of its scope, and `w33lrl` (executed) put the run-level producer in; the gap neither closed is the ATTEMPT record, which is where a two-model run becomes measurable. ONE CORRECTION TO THE BACKLOG ITEM IS RECORDED HERE RATHER THAN SILENTLY ACTED ON: the item says the OpenCode model comes "from the session's assistant message modelID", and the `--format json` stream carries NO model id (measured at authoring against opencode 1.18.33: a full turn emitted `step_start`, `text` and `step_finish` and not one key naming a model). That does not sink the item, because the model IS reachable by a different route, but the route is a separate mechanism with its own failure modes, so it is Order 02's and this plan takes the route that needs no host cooperation at all.
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make every attempt record name the model it was launched under, so a verifier turn under a second model
stops being attributed to the executor's and a run with no `--model` stops being unattributable.

The test of success is not "a key exists". It is that a two-model run, read back from `state.json` alone,
reports two different models on the two phases of one attempt.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the one shared resolver

- [ ] E-01 ADD ONE SHARED RESOLVER IN `runner_shared` THAT ANSWERS "WHICH MODEL WILL THIS TURN RUN UNDER, AND WHO SAID SO", TAKING FROZEN `options` AND A ROLE, AND RETURNING BOTH THE MODEL AND A SOURCE LABEL. Name it for what it answers (for example `launch_model_for_role(options, *, role)`), accept the role vocabulary the runners already distinguish (`execute` and `verify`; a review and a recovery turn are the EXECUTE launch and must resolve to it, see F-04), and return a pair. The PRECEDENCE MUST MATCH WHAT THE ARGV ACTUALLY DOES, because a recorded model that disagrees with the launched one is worse than none: for `verify`, read `options["verify_model"]` only when `options.get("verify_launch_profile")` is truthy, which is the exact condition `oc_runipd.run_opencode` computes as `verify_launch = use_verifier_launch and bool(options.get("verify_launch_profile"))` before it selects the `verify_*` key triple; otherwise fall through to the executor keys. Then, and only when the primary key is empty, fall back to `options[COST_ATTRIBUTION_KEY]["model"]` (and `options["verify_" + COST_ATTRIBUTION_KEY]["model"]` for the verify role), which is the SAME two-tier precedence `run_analytics._model_of`/`_verify_model_of` and `run_dashboard._run_model` already implement, so this introduces no third opinion. Return a SOURCE label from a closed set naming which tier answered (for example `options`, `cost_attribution`, `unrecorded`), because `7hek98` shipped the same distinction at the consumer and a consumer that can see WHY a value is absent can report honestly. RESOLVE `agy`'S `explicit_model` KEY TOO: `agy_runipd.initialize_run` freezes both `model` (the effective one) and `explicit_model` (the CLI one), and `run_dashboard._run_model` reads `opts.get("model") or opts.get("explicit_model")`, so the resolver must agree with that reader rather than ignore a key it already honors. The function must be PURE (a mapping in, a pair out), take no `Path`, read no file, and never raise on a malformed `options` (a non-mapping `cost_attribution` must read as absent, not as an exception on the critical path of launching an agent).
  - Depends on: none
  - Expected outcome: `runner_shared.launch_model_for_role` exists, is pure, and returns the measured pairs for all six shapes in the table under Findings; a pasted transcript calling it directly on each shape, including a non-mapping `cost_attribution` and an empty `options`.
  - Execution state: pending

- [ ] E-02 WRITE `model` AND `model_source` ONTO THE ATTEMPT AT ITS CREATION SITE, WHICH IS THE ONLY PLACE BOTH HOSTS PASS THROUGH. The attempt dict literal in `runner_shared.execute_item_core` (the one carrying `"prompt_sha256"` and `"recovery"`) is built and appended before the turn is spawned, so a model written there is present in `state.json` for the DURATION of the turn rather than only after it ends, which is what makes an INTERRUPTED attempt attributable without a second write path. Resolve with E-01's function for the EXECUTE role, since the executor turn is what this attempt's own `log`, `cost` and `tokens` describe, and the verify phase gets its own field in E-03. Write both keys UNCONDITIONALLY, including when the value is empty, and record the source label as the honest `unrecorded` rather than omitting the pair: an absent key cannot be distinguished by a consumer from a consumer that forgot to read it, and `runner_shared.cost_attribution_record`'s own documented rule is "EVERY UNKNOWN IS NAMED, NEVER OMITTED AND NEVER ZERO". DO NOT TOUCH `argv`: the recorded argv already contains `--model <v>` when one was passed, and it stays the raw launch evidence against which this field can be cross-checked; parsing argv to derive the field would make the record depend on flag order.
  - Depends on: E-01
  - Expected outcome: an executed run (or a driven `execute_item_core` in a test) whose `state.json` shows `model` and `model_source` on the attempt at the moment the turn is running, not only after it ends; the pasted attempt JSON.
  - Execution state: pending

### Task group 2: the paths an attempt can take that are not the happy one

- [ ] E-03 RECORD THE VERIFIER'S OWN MODEL ON THE ATTEMPT WHEN A VERIFIER TURN RAN UNDER A SEPARATE LAUNCH, BESIDE THE `verify_cost`/`verify_tokens` KEYS THAT ALREADY RECORD ITS SPEND. In `execute_item_core`'s verifier block, the one that already does `attempt["verify_log"] = str(_v_log)` and then writes `verify_cost`/`verify_tokens` from `extract_log_metrics`, add `attempt["verify_model"]` and `attempt["verify_model_source"]` resolved through E-01 with the `verify` role. WRITE THEM ONLY WHEN A VERIFIER TURN ACTUALLY RAN, matching the existing conditional shape of `verify_cost` exactly: a run with no verifier phase must keep the attempt shape it has today, which is the same discipline `kgpptv` used for the `verify_*` option keys and `w33lrl` used for `verify_cost_attribution`. THIS IS THE FIELD THAT MAKES THE SET WORTH DOING: without it a `--verify-with` run's two models collapse to one in every reader, and with it `run_analytics`'s already-shipped `Phase.VERIFY` fact can be fed from the attempt rather than from a run-level field. Note in the code comment WHY this is not simply `options["verify_model"]` read at the consumer: a resume can legitimately reach an attempt whose run-level options were frozen by an earlier invocation, and the attempt is the record of what THAT turn did.
  - Depends on: E-01, E-02
  - Expected outcome: a driven two-model attempt whose record carries `model` naming the executor's and `verify_model` naming the verifier's; and a no-verifier attempt whose record carries NEITHER verify key (pasted JSON for both).
  - Execution state: pending

- [ ] E-04 CARRY THE SAME TWO KEYS ON THE THREE NON-HAPPY ATTEMPT SHAPES, ENUMERATED RATHER THAN GUESSED. `execute_item_core` builds a MINIMAL attempt dict on two early refusal paths that return before any turn is spawned (the scope-target-stale refusal, whose dict carries `scope_target_refused` and `"disposition": "fail-gate"`, and the host-capability refusal, whose dict carries `host_capability_unavailable`), and `runner_shared.record_interrupted_attempt_accounting` post-fills an INTERRUPTED attempt with `session_id`, `cost` and `tokens` read back from the log. Add the resolved `model`/`model_source` to both refusal dicts, so a refusal is attributable to the model that would have run it (a refusal costs nothing, but a corpus that silently drops refusals from the denominator overstates coverage, which is exactly the "measure the minority and report it as the whole" failure `model_comparison` refuses over). For the interrupted path no change may be NEEDED, because E-02 writes the field at creation and an interrupted attempt was created the normal way: VERIFY that by driving an interruption rather than assuming it, and add the write only if the field is genuinely absent. Report which of the three needed a change and which did not.
  - Depends on: E-02
  - Expected outcome: each of the three shapes exercised, with the attempt JSON pasted for each, and a written statement of which required a code change; the interrupted case must show the field surviving `record_interrupted_attempt_accounting` unchanged.
  - Execution state: pending

### Task group 3: prove it, including the shapes that must not change

- [ ] E-05 PIN THE PRODUCER BEHAVIORALLY IN A NEW `tests/test_attempt_model_identity.py`, DRIVING THE REAL `execute_item_core` RATHER THAN ASSERTING ON SOURCE. A new file rather than an addition to `tests/test_runner_shared.py`, because four pending approved plans already declare that path (`cpi6p3`, `8o709f`, `nf71bz`, `zhqt51` among others) while none declares this one, so a new file contends with nothing. The suite's own prohibition applies in full (GUIDING_PRINCIPLES P16): no `inspect.getsource`, no `ast`, no assertion that a comment or a key ORDER is preserved. Required cases, each an OUTCOME: (a) a one-model run records that model on the attempt with source `options`; (b) a run whose `options.model` is `None` but whose `cost_attribution.model` is set records the latter with source `cost_attribution`, which is the shape a no-`--model` oc run actually has; (c) a run with neither records an empty model with source `unrecorded`, and the KEY IS PRESENT; (d) a two-model run records the executor's on `model` and the verifier's on `verify_model`; (e) an `agy`-shaped `options` carrying `explicit_model` resolves through it; (f) a malformed `options` (a string where `cost_attribution` belongs) resolves to `unrecorded` WITHOUT raising. Prove (f) by CALLING the resolver, since it is the guarantee that a telemetry-grade field cannot break a launch. SHOW ONE CASE RED FIRST: revert E-02's write, observe (a) fail, restore, and paste both runs, so the test is proven non-vacuous rather than asserted to be.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: `tests/test_attempt_model_identity.py` exists with all six cases as behavioral assertions; pasted `python3 -m pytest tests/test_attempt_model_identity.py -o addopts=""` green, plus the pasted RED run from the reverted-write experiment.
  - Execution state: pending

- [ ] E-06 PROVE THE THINGS THAT MUST NOT MOVE HAVE NOT MOVED, NAMING THEM INDIVIDUALLY. Three properties are at risk from a new attempt key and each is checked by its own means. (a) THE ANALYTICS SOURCE CONTRACT STILL READS THE STATE FILE CLEAN: `run_analytics_sources.inventory_run` warns `unknown-state-keys` for an unrecognized TOP-LEVEL key, and a key inside an ATTEMPT is invisible to it, which was executed at authoring (a state file carrying `attempts[0]["model"]` warned only `missing-optional-state-keys` and `no-events-stream`, while adding a top-level `attempt_models` key DID add `unknown-state-keys`). Re-run that check at execution and paste it; if it warns, this plan has put the key in the wrong place and must say so rather than widening `KNOWN_STATE_KEYS`. (b) NO RUN-LEVEL FIELD CHANGED: `options.model`, `options.cost_attribution` and their `verify_*` twins are written by `initialize_run` in each host and this plan touches neither host, so assert that a frozen `options` dict is byte-identical before and after by comparing a serialized snapshot. (c) THE SUITE IS GREEN BARE: run `python3 -m pytest` with no added flags and paste the summary line, re-deriving the baseline at execution rather than trusting a number from authoring.
  - Depends on: E-05
  - Expected outcome: pasted `inventory_run` warnings tuple for a state file carrying the new attempt key; a pasted before/after `options` comparison showing equality; a pasted bare `python3 -m pytest` summary line.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation in this plan is by symbol or quoted string for that reason.
- The suite is run BARE: `pyproject.toml` `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`. Adding `-n0`, a second `-q`, or `-p no:randomly` is forbidden by the execution contract; `-o addopts=""` is the sanctioned way to get per-test counts from a narrowed run.
- `runner_shared` MAY NOT IMPORT EITHER RUNNER, enforced by a shipped guard (`tests/test_runner_shared.py::NoRunnerImportTests`). Everything this plan adds is therefore a pure function over the frozen `options` mapping plus writes at seams `execute_item_core` already owns; nothing here may reach into `oc_runipd` or `agy_runipd`.
- A NEW FIELD MUST NAME ITS UNKNOWNS RATHER THAN OMIT THEM. `runner_shared.cost_attribution_record` states the rule and implements it (`CARD_HOST_NOT_READABLE`, `card_reason`, `model_reason`), and `run_analytics_privacy` refuses a free-text value on a closed-vocabulary key, so a `model_source` value must come from a short closed set.
- `run_analytics_privacy` ALREADY ADMITS `model` AND REFUSES `model_source`: executed at authoring, `"model" in ALLOWED_METRIC_KEYS` is `True` while `"model_source" in ALLOWED_METRIC_KEYS` is `False`, and `_project_scalar("model_source", "frozen-launch")` raises `PrivacyRefusal`. That is a CONSUMER-side fact and no obstacle to this plan (the analytics projector never sees a raw attempt record; it sees `Fact` objects), but Order 03 must handle it, and it is recorded here so that plan does not rediscover it.

## Findings

Measured in this lane at HEAD by execution; the transcripts are pasted where they are load-bearing.

### F-01 The attempt record carries no model on any path

`runner_shared.execute_item_core` builds its attempt dict with `number`, `started_at`, `starting_head`,
`starting_branch`, `starting_status`, `prompt`, `prompt_sha256`, `session_id`, `log`, `recovery`, `action`
(plus a conditional `review_handler`, `scope_target_check_error`, `host_capability_check_error`), and after
the turn adds `ended_at`, `exit_code`, `ending_head`, `ending_branch`, `ending_status`, `log`, `argv`, then
`cost`/`tokens` from `run_viewer.extract_log_metrics`. No model key on any path.
`run_analytics_statistics.model_comparison`'s own docstring records the same: "NO attempt-level model key
anywhere".

### F-02 The run-level field is absent or empty in the two commonest configurations

| Configuration | `options.model` | `cost_attribution.model` | What a reader sees today |
|---|---|---|---|
| oc, `--model` passed or profile supplies one | the model | the same model | the model |
| oc, no `--model`, config readable | `None` | the host default, resolved at launch | the model, via the fallback tier |
| oc, no `--model`, config absent/unparseable | `None` | `""` plus a `model_reason` | `(unrecorded)` |
| agy, `settings.json` present | the settings model | the same | the model |
| agy, no `settings.json` | `None` | `""` | `(unrecorded)` |
| any run created before `w33lrl` | `None` | key absent entirely | `(unrecorded)` |

The agy no-settings row, executed at authoring:

```
agy resolve with empty HOME: (None, 'host-default')
agy cost_attribution record: {"kind": "launch-time-snapshot", "host": "agy", "unit": "$/Mtok",
 "cost_basis": "launch-time snapshot only: ...", "model": "", "model_source": "host-default",
 "card": {}, "card_reason": "host-card-not-in-any-readable-config", "card_config": "",
 "card_config_digest": ""}
```

And the four dashboard readings of those shapes, through `run_dashboard._run_model`:

```
dashboard _run_model, agy no-settings shape : ('(unrecorded)', '')
dashboard _run_model, oc host-default shape : ('x', 'cost_attribution')
dashboard _run_model, oc unresolvable shape : ('(unrecorded)', '')
dashboard _run_model, pre-w33lrl shape      : ('(unrecorded)', '')
```

### F-03 THE TWO-MODEL RUN IS MIS-ATTRIBUTED TODAY, AND THIS IS THE STRONGEST REASON FOR THE FIELD

Executed at authoring against a synthetic run whose `options` carried `model: provA/executor-model`,
`verify_model: provB/verifier-model` and both `cost_attribution` twins, with one attempt carrying a main
log and a verify log:

```
=== DASHBOARD rows (run_dashboard.collect_rows) ===
 role=main    model=provA/executor-model   model_source=options          cost=0.5
 role=verify  model=provA/executor-model   model_source=options          cost=0.5
```

The VERIFY row reports the EXECUTOR's model. The cause is structural rather than a bug in the reader: the
run-level model is computed once per run in `collect_rows` and stamped onto every row's `base` dict, so
there is no per-row model for it to read. Analytics does better on the same input, because
`run_analytics._verify_model_of` exists:

```
=== ANALYTICS facts (run_analytics.build_run_facts) ===
 grain=attempt  phase=execute   attempt=1    model=provA/executor-model
 grain=phase    phase=execute   attempt=None model=provA/executor-model
 grain=phase    phase=verify    attempt=None model=provB/verifier-model
 grain=ipd      phase=execute   attempt=None model=provA/executor-model
 grain=run      phase=unknown   attempt=None model=provA/executor-model
```

So the two consumers DISAGREE on the same run, and both are reading a run-level field because no
per-attempt one exists. Note the analytics ATTEMPT-grain fact takes the executor's model unconditionally,
which is correct today only because an attempt has no verify model to offer it.

### F-04 A REVIEW AND A RECOVERY TURN USE THE EXECUTOR LAUNCH, AND KEYING OFF THE WRONG SIGNAL IS A KNOWN TRAP

`oc_runipd.run_opencode` selects the verifier key triple on `use_verifier_launch and
bool(options.get("verify_launch_profile"))`, and its own comment records the trap in as many words: keying
the verifier launch off `fresh_session` or off session-absence "would hand the VERIFIER's model to nearly
every EXECUTE turn, which is the DEFAULT configuration", because `fresh_session` is true for every isolated
turn and isolation is the default. E-01's resolver must therefore take the role from its CALLER, exactly as
`run_opencode` does, and must never infer it.

### F-05 THE PER-INVOCATION TELEMETRY STREAM ALREADY CARRIES A MODEL, AND IS NOT A SUBSTITUTE

Both hosts pass `extra_context={"model": options.get(model_key)}` into `runner_shared.turn_telemetry`, and
`run_analytics_telemetry.ALLOWED_FIELDS` admits `model`, `provider` and `model_variant`. So a per-invocation
model is ALREADY recorded when telemetry is enabled (executed at authoring: `read_telemetry_config` on a
repo with no config returns `enabled=True`). It is not a substitute for this field for three measured
reasons: the stream lives under `<run_dir>/telemetry/` and spec `25kzda` Section 5.3a declares it "DERIVED,
BEST-EFFORT, NEVER A GATE"; `turn_telemetry` swallows every failure by design, so absence proves nothing;
and `run_dashboard` and `run_analytics` both read `state.json`, not the telemetry stream. What it DOES give
this plan is a precedent for the value shape and a cross-check: where both exist they must agree, and E-05
may assert that on one case.

### F-06 THE TRIPWIRE THAT WOULD HAVE CAUGHT AN OPTIONS-SHAPE CHANGE NO LONGER EXISTS

`tests/test_rununify_initialize_run.py`, the test that pinned the frozen `options` key set and which
`w33lrl` had to edit when it added `cost_attribution`, was DELETED in commit `19313eed` ("test: trim test
suite from 9,136 to under 2,000 tests"). This plan changes no option key, so nothing it does needs that
tripwire; it is recorded because E-06(b) is the compensating check and because a future plan touching
`initialize_run` should know the guard is gone.

## Proposed changes (ordered, validatable)

1. One pure resolver in `runner_shared` mapping frozen `options` plus a role to `(model, source)`, with the
   same two-tier precedence the two existing consumers already use (E-01).
2. `model` and `model_source` written on the attempt at its creation site, unconditionally, with a named
   `unrecorded` source when nothing resolves (E-02).
3. `verify_model` and `verify_model_source` written in the verifier block, conditionally, beside the
   existing `verify_cost`/`verify_tokens` (E-03).
4. The same two keys on the two early-refusal attempt shapes, and verification that the interrupted path
   needs no change (E-04).
5. A new behavioral test file driving `execute_item_core` over six shapes, with one case shown red first
   (E-05).
6. Explicit proof that the analytics source contract, the frozen run-level options, and the bare suite are
   all unchanged (E-06).

## Deferred / out of scope (with reason)

- OBSERVING WHAT THE HOST ACTUALLY CHOSE is Order 02 (`ov2c9n`). The field this plan writes is the REQUEST
  the driver froze, which is authoritative for "what did we ask for" and is silent about a host that
  substituted something else. Conflating the two in one key would make the field unfalsifiable.
- EVERY CONSUMER is Order 03 (`r5fk4k`): `run_dashboard._run_model` and its row stamping,
  `run_analytics._model_of`/`_verify_model_of`, and `run_analytics_statistics.model_comparison`'s coverage
  arm. Landing a producer first is what lets Order 03 measure real coverage instead of arguing about it.
- BACK-FILLING HISTORY is out of scope for the whole Set. `w33lrl` recorded the same decision for
  `cost_attribution` ("the change only WRITES the key at run creation, so every pre-existing run stays
  card-less by construction"), and inventing a model for a past attempt would fabricate provenance.
- NORMALIZING THE MODEL VALUE (stripping `uri/`, `google/` and friends) stays where it is, in
  `run_dashboard._normalize_model`. This field records the value verbatim as the launch used it;
  normalization is a display concern and `7hek98`'s gate paragraph already names "normalize the display
  name at the producer" as a deferred alternative rather than a settled one.
- THE `audit` VERB'S MINIMAL STATE (`oc_runipd.handle_audit_command`) writes its own `state.json` with
  `_audit_launch_options(args)` and a lean attempt dict, bypassing `execute_item_core` entirely, so it gains
  nothing from this plan. It is OUT OF SCOPE because fixing it means editing `oc_runipd.py`, which this plan
  deliberately does not touch, and because an audit turn is a single-model verification whose model is
  already in its own `options`. Filed as a known residue in Order 00's completion criteria rather than
  silently ignored.

## Scope check

- Over-scope: none. Two files, one of them new.
- Under-scope: the `audit` verb's separate state writer keeps no per-attempt model (named above and carried
  in the orchestrator's criteria). Consumers keep reading the run-level field until Order 03, so this plan
  alone changes no output a user sees; that is intended, and it is why Order 03 exists.

## Required tests / validation

- `tests/test_attempt_model_identity.py`, new, six behavioral cases (E-05), with one shown red first.
- `run_analytics_sources.inventory_run` warnings on a state file carrying the new attempt key, pasted
  (E-06a).
- A before/after equality check on the frozen run-level `options` (E-06b).
- Bare `python3 -m pytest`, summary line pasted, baseline re-derived at execution (E-06c).

## Spec / documentation sync

- NO SPEC AMENDMENT, and the reason is measured rather than assumed: `grep` over `.aw/records/specs/` for
  `cost_attribution`, `options.model`, `run_dashboard`, `runsdash` returns NOTHING, so the run-state model
  fields are contracted in code only. Spec `25kzda` Section 5.6's machine per-item JSON object carries no
  model field, so adding one to the ATTEMPT record contradicts nothing there. `Scope-Paths` therefore
  declares no `.spec.md` file.
- Spec `w15vzb` (approved, per-action model selection) is ADJACENT and worth citing without amending: its
  R-6 case B and criterion A-8 require that an unprovidable-at-launch model "WARNS, falls back, and RECORDS
  the fallback in run state", and are recorded OUTSTANDING. This plan does not implement A-8 (it records the
  resolved request, not a fallback event) but it builds the per-attempt place such a record would live, so
  Order 00's Deferred section names the link.
- NO DOCS CHANGE. `docs/` has no page describing the run-state schema or the dashboard (`grep` for
  `run_dashboard` over `docs/` returns nothing), and `docs/run-analytics.md` describes outputs rather than
  state keys. Order 03, which changes what a reader REPORTS, is the plan that should carry any doc update.

## Open questions

### OQ-01: Should `model_source` use the existing `cost_attribution` source vocabulary or its own?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: USE A SMALL PURPOSE-BUILT SET NAMING THE TIER THAT ANSWERED (`options`, `cost_attribution`, `unrecorded`), not `cost_attribution`'s `model_source`, and the reason is that the two answer different questions. `cost_attribution.model_source` records WHO SUPPLIED the model (`cli-argument`, `settings.json`, `host-default`, a profile provenance token), which is already recorded once per run and is not re-derivable per attempt without re-reading a config this seam may not read. This field records WHICH RECORD the attempt's value was read from, which is what a consumer needs in order to report honestly, and it is the same distinction `run_dashboard._run_model` already returns as its second element (`"options"` / `"cost_attribution"` / `""`). Adopting the dashboard's spelling makes Order 03's consumer change a narrowing rather than a translation. The residual cost is accepted and stated: an attempt does not record who supplied the model, only where the value came from; the run-level `cost_attribution.model_source` still answers the first question and is unchanged by this plan.

### OQ-02: Should the resolver live in `runner_shared` or in a new module?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: `runner_shared`, because both hosts must reach the SAME definition and that module is the one place that is already true of. The alternative, a new module, was considered and rejected on a measured layering fact: `agy_runipd` imports 56 names from `oc_runipd` and `oc_runipd` imports none from agy, so a definition in either host deepens the layering defect backlog `cnwy8g` owns, and `runner_shared`'s own header records that this is exactly why `cost_attribution_record` lives there rather than in a runner. A new module would be defensible if the function grew a host-specific reader, which is precisely what Order 02 adds; if that happens, Order 02 may home ITS reader separately, and this one stays put.

### OQ-03: Should a recovery attempt record the recovery turn's model separately?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: NO SEPARATE FIELD, because a recovery turn uses the EXECUTOR launch. `oc_runipd.run_opencode` selects the verifier triple only when its caller passes `use_verifier_launch=True`, and only the verifier call site does; the recovery call site passes `log_suffix="recovery"` and nothing else, so its model IS the executor's and `attempt["model"]` already names it. The attempt separately carries `recovery: true`, so a consumer wanting to stratify recovery turns by model can already do so. This is recorded rather than left implicit because the opposite assumption (that a `fresh_session` turn is a verifier turn) is the trap F-04 documents.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a pasted transcript calling the resolver directly on each of the six shapes in F-02's table plus two malformed ones (a string where `cost_attribution` belongs, and an empty `options`), showing the returned `(model, source)` pair for each and NO exception on the malformed inputs. The `verify` role must be shown returning the EXECUTOR's model when `verify_launch_profile` is absent, which is the condition `oc_runipd.run_opencode` actually gates on.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the attempt JSON read from `state.json` WHILE a turn is in flight (or from a driven `execute_item_core` whose spawn callback dumps the state), showing `model` and `model_source` present before `ended_at` exists. Plus the `unrecorded` case pasted, proving the key is present and not omitted when nothing resolves.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: two pasted attempt records from driven runs: one two-model run where `model` and `verify_model` hold DIFFERENT values, and one no-verifier run whose attempt carries neither `verify_model` nor `verify_model_source`. The second is the one that proves no existing attempt shape changed.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: three pasted attempt records, one per non-happy shape (scope-target refusal, host-capability refusal, interrupted), each showing `model`/`model_source`; plus a written statement naming which of the three required a code change and which already carried the field by construction. An interrupted attempt must be shown AFTER `record_interrupted_attempt_accounting` ran, so the field is proven to survive that post-fill.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `python3 -m pytest tests/test_attempt_model_identity.py -o addopts=""` showing all six cases passing BY NAME, plus the pasted RED output from reverting E-02's write and re-running case (a), plus the restored green. A green run alone does not satisfy this item: a test that cannot fail proves nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: three pasted artifacts. (a) `run_analytics_sources.inventory_run(...).warnings` for a state file whose attempt carries the new keys, which must NOT contain `unknown-state-keys`. (b) A serialized comparison of the frozen run-level `options` before and after this plan's change, showing equality. (c) The bare `python3 -m pytest` summary line, with the pre-change baseline stated beside it so the delta is attributable to the new test file alone.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before execution;
an executing agent must not self-approve, and must not hand-write a `- Readiness:` value, which is an output
of review.

At execution, follow the repository execution contract: commit only the two declared paths through
`aw commit <plan> -- <paths>`, never `git add -A`, never push, and paste the ACTUAL runner output for every
test claim. Do not mark this plan executed or move it to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms AND every `V-*` item above carries pasted evidence. The
backlog item `7yz545` must NOT be set `done` by this plan: it graduates to `graduated` when the Set's
orchestrator retires, and only Order 03 delivers the coverage the item asks for.
