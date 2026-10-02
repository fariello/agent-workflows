# IPD: Record the model the Antigravity host ran, which today is neither observed nor recorded

- Date: 2026-10-02
- Kind: child
- Concern: AN `aw agy run` ATTEMPT RECORDS NO OBSERVED MODEL AT ALL, AND ITS FROZEN MODEL IS A CONFIG READING THAT CAN BE EMPTY. `runner_shared.execute_item_core` resolves its model observer off the host module (`observe_host_model = getattr(driver_module, "observe_host_model", None)`) and `agy_runipd` defines no such symbol (measured: zero matches for `observe_host_model` and for `host_model` across `agent_workflows/agy_runipd.py`), so the `None` default silently skips the whole block and no `host_model*` key is ever written on this host. What the attempt does carry is `agy_models.resolve_agy_default_model`'s reading of `~/.gemini/antigravity-cli/settings.json`, frozen into options at `agy_runipd.initialize_run`; that reading returns `(None, "host-default")` on an absent, unparseable, or model-less settings file, and in that case `resolve_attempt_model` falls through to tier 6 and reports `("", "unrecorded")`. Separately, `agy_runipd.render_agy_event` already parses a model out of the stream's `init` event (`model = init_data.get("model", "antigravity")`) and renders it to the terminal without persisting it, so a value is parsed and discarded on every agy turn.
- Scope: Give the Antigravity host the observed-model field the OpenCode host already has, by persisting what the stream reports, and do it WITHOUT repeating `ov2c9n`'s prescription unexamined, because that prescription's premise is false as measured here (F-01/F-02). Define `observe_host_model` in `agy_runipd` with the EXACT signature the existing seam calls, read the `init` event's model from the attempt's own JSONL log (already written line by line at the `log.write(raw_line)` site, so no subprocess and no second host interrogation), and record it in the same four keys OpenCode uses (`host_model`, `host_model_provider`, `host_model_variant`, `host_model_source`) under an agy-specific source label that names the mechanism honestly. EXCLUDES changing the frozen `model` key, `resolve_attempt_model`'s precedence, or any shipped consumer test. EXCLUDES any gate, refusal, or warning-to-failure on a model value or a disagreement, per `25kzda` Section 5.3a's never-a-gate posture for derived observations. EXCLUDES a new CLI flag (spec `25kzda` Section 2.1 governs the run flag grammar and this plan declares no `.spec.md` in `Scope-Paths`). EXCLUDES back-filling history and EXCLUDES the `audit` verb, which writes its own attempt dict outside this seam.
- Scope-Paths: agent_workflows/agy_runipd.py, tests/test_attempt_agy_model_observation.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Backlog: qswokt
- Set: agymodel
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: rejqff

## Workflow history

- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `qswokt`, the named carrier `ov2c9n` recorded for its deferred Antigravity half. THE PRESCRIPTION WAS RE-MEASURED RATHER THAN ADOPTED, AND IT DOES NOT HOLD AS STATED. `ov2c9n` F-04 asserts the agy stream "DOES carry a model" so the agy side needs "only a persist of a value already parsed". Executed against the live host (agy 1.2.14, three probe turns in this lane): `init.model` is a VERBATIM ECHO of the `--model` argument, and when no `--model` is passed it is ABSENT ENTIRELY (`init.model = None`). Since `agy_runipd.run_agy_turn` passes no `--model` on the default configuration path (`explicit_model` is present-and-`None`, so the `"explicit_model" not in options` guard is False and the frozen `model` is never promoted to a flag), the prescribed persist would record NOTHING on exactly the default-configuration runs the field exists to cover. The plan therefore keeps the cheap in-log mechanism (it is the right mechanism) while narrowing the claim the field may make, labeling it as an echo rather than an observation, and recording honestly that the gap for a flagless turn is NOT closable from the stream (F-02, F-06, OQ-01). Also corrected: `ov2c9n`'s F-04 citation of `event["init"]["model"]` defaulting to the literal `"antigravity"` is live in `render_agy_event`, and that default must NOT be persisted, because it is a placeholder and not a model id.
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make an `aw agy run` attempt carry the model it ran under, in the same keys and with the same
consumer path the OpenCode host already uses, so an agy row in the dashboard stops depending
entirely on a config file that may name nothing.

The test of success is that an agy turn launched WITH a model records a concrete `host_model` on its
attempt that `resolve_attempt_model` returns at tier 1, that an agy turn whose stream reports no model
records NO `host_model*` key and is otherwise byte-identical, and that the three shipped dashboard
model tests pass unedited.

WHAT THIS FIELD MAY HONESTLY CLAIM IS NARROWER THAN THE OPENCODE TWIN'S, and the narrowing is the
reason this plan is not a mechanical port. OpenCode's value comes from `opencode export`, which is the
host reporting its own session state back. Antigravity's value comes from the `init` event, which
measurement shows is the host ECHOING the argument it was given (F-01). An echo is weaker evidence
than an observation: it proves the host ACCEPTED the model (a bogus value is rejected with a nonzero
exit before any `init` event is emitted, measured in F-03) but it is not independent of the request.
The source label must therefore say `init-event-echo` and not reuse `export-session-current`, and the
plan must not claim to have closed the flagless-turn gap, which it provably cannot (F-02).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure the host surface, because this plan exists to correct a stale premise

- [ ] E-01 RE-MEASURE THE FOUR HOST FACTS THIS PLAN TURNS ON, AT EXECUTION, BEFORE WRITING ANY CODE, AND STOP IF ANY HAS CHANGED. Each was measured at authoring against agy 1.2.14 and each is version-dependent, so none may be trusted from this document. (a) THE ECHO: a turn launched `--model gemini-3.8-flash-low` emits a first-line `init` event whose `init.model` is exactly `"gemini-3.8-flash-low"`; a turn launched `--model "Gemini 3.8 Flash (High)"` echoes that display-name spelling verbatim. (b) THE ABSENCE, WHICH IS THE FINDING THAT RESHAPED THIS PLAN: a turn launched with NO `--model` at all emits an `init` event with NO `model` key (`init.model is None`). (c) THE REJECTION: a turn launched `--model totally-bogus-model-xyz` exits NONZERO having emitted no usable stream, so an echoed value does at least prove host acceptance. (d) THE STREAM CENSUS: across all events of a complete turn, `model` appears in the `init` event ONLY and in no `step_update` or `result` event, so `init` is the only in-stream source. Record `agy --version` beside the measurements. IF (b) NOW REPORTS A MODEL FOR A FLAGLESS TURN, STOP AND REPORT: that would mean the host began observing rather than echoing, which makes OQ-01's gap closable and changes this plan's central claim, and that is a human's call rather than an executor's.
  - NOTE THE FLAG UNIT, because the obvious invocation fails: `--print-timeout` requires a duration UNIT (`180s`), and a bare `180` exits 2 with `missing unit in duration "180"`. Measured at authoring; it cost a wasted probe.
  - PROBE INSIDE A GITIGNORED DIRECTORY, not the working tree: `.aw/records/runs/` is ignored (`.aw/.gitignore` line `records/runs/`), which is where authoring's probes were run and why they left the tree clean. Do NOT probe into a tracked path and do NOT commit probe output.
  - Depends on: none
  - Expected outcome: pasted `agy --version`; the pasted first `init` line for each of the three launch shapes in (a) and (b) with `init.model` extracted and shown; the pasted nonzero exit and error text from (c); the pasted per-event model-key census from (d); and an explicit statement that all four match this plan's premises or naming exactly which did not.
  - Execution state: pending

- [ ] E-02 CONFIRM, BY CODE READING AND BY A DRIVEN CALL, THAT THE DEFAULT-CONFIGURATION RUNNER PATH PASSES NO `--model`, BECAUSE THAT IS WHAT MAKES (b) BITE IN PRODUCTION RATHER THAN ONLY IN A PROBE. `agy_runipd.initialize_run` freezes `"model": effective_model` (CLI value or `agy_models.resolve_agy_default_model`'s settings reading) and `"explicit_model": cli_model`, so on a run started with no `--model` the key `explicit_model` IS PRESENT with value `None`. `run_agy_turn`'s promotion guard is `if model_flag is None and "explicit_model" not in options`, whose second conjunct is then FALSE, so the frozen `model` is NOT promoted and no `--model` reaches the child. Verify this by evaluating the guard against both option shapes and pasting the result, rather than by asserting it from the prose. THIS IS THE JOINT THAT DECIDES OQ-01: if the guard were to promote the frozen model, the echo would cover the default path and the gap would close by itself.
  - DO NOT "FIX" THE GUARD AS PART OF THIS PLAN. Promoting the frozen config model into a `--model` flag on every turn would change what the host is ASKED for, not what is recorded about it, which is a behavior change to the launch path and is out of this plan's scope and its `Scope-Paths` intent. Record it as an option in OQ-01 for a human to decide.
  - Depends on: E-01
  - Expected outcome: the guard evaluated and pasted for both shapes (present-and-`None` versus absent), showing no flag promoted in the default case; plus a pasted statement of what `resolve_agy_default_model()` returns on the executing box and what `resolve_attempt_model` therefore reports today for such an attempt.
  - Execution state: pending

### Task group 2: the reader, at the signature the existing seam actually calls

- [ ] E-03 DEFINE `observe_host_model` IN `agy_runipd` WITH THE EXACT SIGNATURE `execute_item_core` CALLS, READING THE ATTEMPT'S OWN LOG RATHER THAN SPAWNING ANYTHING. The seam calls it as `observe_host_model(session_id, options=..., repo_root=...)` and wraps the call in `try/except Exception: host_model_rec = None`, so A SIGNATURE MISMATCH IS SILENTLY SWALLOWED AND THE FEATURE SIMPLY NEVER WORKS. Measured at authoring: calling the OpenCode twin with an extra `log_path=` keyword raises `TypeError: observe_host_model() got an unexpected keyword argument 'log_path'`, which at that seam would be indistinguishable from a host that could not be asked. So the signature MUST be positional `session_id` plus keyword-only `options` and `repo_root`, accepting and ignoring what it does not need, and E-05 must assert the keys appear rather than merely asserting the function returns a record in isolation. THE LOG IS THE SOURCE: `run_agy_turn` writes every stream line to `attempt_log_path(...)` at its `log.write(raw_line)` site and the `init` event is the FIRST line, so the read is a single-line parse of a file this host already wrote (timed at authoring: 0.131 ms). Resolve the log by the same `attempt_log_path` the writer used. NEVER RAISE, for the same reason `runner_shared.turn_telemetry` swallows everything: this runs immediately after a completed agent turn and an observability read must not turn a completed turn into a failed one.
  - DO NOT PERSIST THE `"antigravity"` PLACEHOLDER. `render_agy_event` reads `init_data.get("model", "antigravity")` for DISPLAY, and that literal is a placeholder, not a model id; persisting it would write a value that looks concrete, would be returned by `resolve_attempt_model` at tier 1 ahead of a real frozen model, and would therefore make the record WORSE than the absent field it replaces. Return `None` when the key is missing or blank, which is the (b) case and is the common one.
  - DO NOT SPAWN A SUBPROCESS AND DO NOT READ THE CONVERSATION STORE. The host offers no `export` subcommand (so the OpenCode route does not transfer), and the per-conversation SQLite stores under the host's app data dir carry only an opaque `model_enum` placeholder (`MODEL_PLACEHOLDER_M318`, measured at authoring across the local corpus) rather than a model id, so that route is both useless and refused on the same grounds `ov2c9n` refused OpenCode's store: an undocumented internal schema with no compatibility promise, a locking hazard against a live application, and a machine-local absolute path of exactly the kind the leak sanitizer exists to keep out.
  - Depends on: E-02
  - Expected outcome: the function exists in `agy_runipd`; a pasted call with the SEAM'S EXACT keyword set returning the record for a log whose `init` carries a model; a pasted call returning `None` for a log whose `init` carries none; a pasted call returning `None` for a missing log file, an unparseable first line, and an `init` carrying the literal `"antigravity"`, none of them raising.
  - Execution state: pending

- [ ] E-04 CHOOSE AND DOCUMENT THE SOURCE LABEL SO THE FIELD CANNOT BE READ AS STRONGER EVIDENCE THAN IT IS, AND FILL THE PROVIDER KEY HONESTLY. Record `host_model_source` as a value naming THIS mechanism and its grain, `init-event-echo`, and state in the code comment that the value is the host's echo of the `--model` argument rather than an independent observation, that it is absent for a flagless turn, and that it does prove host acceptance because a bogus model is rejected before any `init` event is emitted. DO NOT REUSE `export-session-current`: that label names OpenCode's `opencode export` mechanism, and reusing it would assert a mechanism that was never run. MIND THE DEFAULT IN THE CONSUMER: `resolve_attempt_model` substitutes the literal `"export-session-current"` when `host_model_source` is absent but `host_model` is present, so this plan MUST always write the source key alongside the model key; writing the model alone would mislabel an agy echo as an OpenCode export. For `host_model_provider`, the agy `init` event carries NO provider field, so write the empty string rather than inventing one (the OpenCode twin writes `""` when `providerID` is absent, so the empty value is the established shape). Omit `host_model_variant` entirely unless the re-measurement in E-01 finds a variant in the stream; the host takes reasoning effort as a separate `--effort` flag and does not report it on `init`.
  - Depends on: E-03
  - Expected outcome: the chosen label pasted beside the code comment stating its grain and its echo nature; a pasted record showing `host_model_source` written on every success path; a pasted `resolve_attempt_model` call on a synthetic attempt carrying this plan's keys, showing the agy label returned rather than the OpenCode default.
  - Execution state: pending

### Task group 3: prove it, including that it cannot hurt a run and cannot break a consumer

- [ ] E-05 PIN THE BEHAVIOR IN A NEW `tests/test_attempt_agy_model_observation.py`, DRIVEN THROUGH `execute_item_core` AND NOT ONLY THROUGH THE READER. A new file, because no pending plan declares this path and because the OpenCode twin's file (`tests/test_attempt_host_model_observation.py`) is organized around a launcher-injected subprocess this plan does not use. Required cases, each an OUTCOME, none of them reading production source, none requiring a host binary: (a) an attempt whose log's `init` carries a model records all three keys this plan writes, with the agy source label; (b) an attempt whose log's `init` carries NO model records NONE of them and is otherwise identical to (a)'s run in exit code, disposition, and item status; (c) an attempt whose log carries the literal `"antigravity"` records none, which is the placeholder guard; (d) a missing or unparseable log records none and raises nothing; (e) THE SEAM-CONTRACT CASE, which is the one that must not be omitted: the reader is invoked BY `execute_item_core` through the real `driver_module` resolution (not passed explicitly), proving the symbol is found where the seam looks for it and that its signature matches, since a mismatch there is swallowed and invisible; (f) THE CONSUMER CASE: an attempt carrying this plan's keys is returned by `resolve_attempt_model` at tier 1 with the agy source label, ahead of a frozen `model` that differs, and both values remain on the record unmodified.
  - SHOW ONE CASE RED FIRST and paste both runs, so the file is proven non-vacuous.
  - Depends on: E-04
  - Expected outcome: the new file with all SIX cases; a pasted `python3 -m pytest tests/test_attempt_agy_model_observation.py -o addopts=""` green with case names visible; plus the pasted RED run proving non-vacuity.
  - Execution state: pending

- [ ] E-06 PROVE THE SHIPPED CONSUMER TESTS STILL PASS UNEDITED, AND RUN THE BARE SUITE. Three shipped dashboard tests already assert model attribution and one of them is the agy row specifically: `tests/test_run_dashboard.py::test_antigravity_run` asserts `rows[0]["model"] == "Flash"` from a fixture whose agy `init` event is `{"event": "init", "init": {"tools": []}}` (NO model key, which is this plan's (b) case) and whose model therefore comes from `options["cost_attribution"]["model"]` at tier 5. That test MUST pass WITHOUT EDITING IT: if this plan's reader wrote anything for a model-less `init`, the tier-1 value would displace `"Flash"` and the test would fail, so the test is a live guard on the placeholder-and-absence discipline rather than merely adjacent. Also pass unedited: `test_unrecorded_model_is_labeled_per_host` and `test_per_row_model_attribution_across_roles`. Run the three named tests, then the bare suite, and paste both. DO NOT EDIT ANY OF THE THREE; if one fails, the reader is wrong, not the test.
  - Depends on: E-05
  - Expected outcome: a pasted run of the three named dashboard tests, green, with a `git diff --stat -- tests/test_run_dashboard.py` showing NO change to that file; plus a pasted bare `python3 -m pytest` summary line.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The suite is run BARE: `pyproject.toml` `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`. Use `-o addopts=""` for per-test counts from a narrowed run; never `-n0`, never a second `-q`, never `-p no:randomly`.
- `runner_shared` MAY NOT IMPORT EITHER RUNNER, which is why the host-specific reader lives in `agy_runipd` and reaches the shared loop only by the `getattr(driver_module, "observe_host_model", None)` resolution `execute_item_core` already performs for a dozen other names. THE RULE IS LIVE AND ITS NAMED GUARD IS NOT: `ov2c9n` recorded that `tests/test_runner_shared.py::NoRunnerImportTests` does not exist (lost in the `19313eed` suite trim) and that `agy_runipd` still cites a `test_no_runner_to_runner_import` guard that is equally absent. Obey the rule; do not cite a guard that will not catch you.
- A NEW CLI FLAG IS REFUSED BY THE PLAN CONTRACT, NOT BY A TEST. Spec `25kzda` Section 2.1 governs the run flag grammar, and the repository contract obliges a plan changing a spec-governed contract to declare the `.spec.md` in `Scope-Paths` and amend it in the same change; this plan declares none and needs none. `ov2c9n` recorded that the test once cited as the enforcement, `tests/test_run_flag_surface.py`, was DELETED in `19313eed`, so a flag would not turn the suite red; it would breach the contract silently, which is worse.
- BEST-EFFORT MEANS NEVER RAISES, with a shipped precedent to copy: `runner_shared.turn_telemetry` documents that "EVERY FAILURE MODE IS SWALLOWED, and that is the requirement rather than defensive habit". The twin `observe_host_model` in `oc_runipd` adopts the same discipline and so does this one.
- THE OBSERVED-MODEL KEY SET AND ITS CONSUMER ARE ALREADY ESTABLISHED, so this plan adds a producer and not a schema: `execute_item_core` writes `host_model`, `host_model_provider`, `host_model_variant`, `host_model_source` conditionally (the same `if ... is not None` discipline `cost`/`tokens` use), and `run_analytics_schema.resolve_attempt_model` reads them as its tier 1.
- THE PRIVACY ALLOWLIST ALREADY ADMITS THE LABELS and must not be widened by this plan: `run_analytics_privacy` admits `model`, `provider`, and `model_variant` as closed-vocabulary categorical labels. `ov2c9n`'s Set recorded that `model_source` is NOT allowlisted and that widening it was deliberately avoided; this plan does not widen it either.
- PROBE IN A GITIGNORED DIRECTORY: `.aw/.gitignore` ignores `records/runs/`, which is where a host probe can be run without dirtying the tree. This lane has no `.aw/records/runs` corpus to begin with, so a coverage-fraction measurement over local runs is not available and must not be fabricated.

## Findings

Measured in this lane at HEAD by execution against agy 1.2.14. Probe output was written under the
gitignored `.aw/records/runs/` and is not committed.

### F-01 BLOCKER FOR THE PRESCRIBED DESIGN: `init.model` IS AN ECHO OF THE ARGUMENT, NOT AN OBSERVATION

`ov2c9n` F-04 deferred this work with the reason that the agy stream "DOES carry a model" and so needs
"no subprocess at all, only a persist of a value already parsed". The first half is true and the
inference is not. Three live turns, same box, same host version:

| launched with | first-line `init.model` | exit |
|---|---|---|
| `--model gemini-3.8-flash-low` | `'gemini-3.8-flash-low'` | 0 |
| `--model "Gemini 3.8 Flash (High)"` | `'Gemini 3.8 Flash (High)'` | 0 |
| no `--model` at all | `None` (key absent) | 0 |

The value is returned in whatever spelling it was given, including a display name with spaces and
parentheses, and it disappears when nothing was given. That is the signature of an echo, not of a host
reporting its own state. The contrast with the OpenCode twin is the whole reason this plan is not a
port: `opencode export` answers from the session's own record, which is why `ov2c9n` could call its
field an observation.

### F-02 THE CONSEQUENCE THAT RESHAPED THE PLAN: THE DEFAULT RUNNER PATH IS EXACTLY THE FLAGLESS CASE

The echo would be adequate if the runner always passed `--model`. It does not. `initialize_run` freezes
`"explicit_model": cli_model`, so a run started without `--model` leaves that key PRESENT with value
`None`, and `run_agy_turn`'s promotion guard `if model_flag is None and "explicit_model" not in options`
fails its second conjunct and promotes nothing:

```
no-CLI-model case -> --model passed? False value= None
CLI-model case     -> --model passed? True  value= 'x'
```

So on the default configuration the child receives no `--model`, the `init` event carries no model, and
a naive persist records nothing. The field would appear to work for anyone who tested it with an
explicit `--model` and would be silently empty in normal use, which is a worse outcome than a field
that is honestly absent and labeled. This is why E-02 verifies the guard and why OQ-01 exists.

### F-03 THE ECHO IS NOT WORTHLESS: IT PROVES HOST ACCEPTANCE

A rejected model never reaches an `init` event at all:

```
$ agy -p ... --model totally-bogus-model-xyz
error: invalid model selection (--model "totally-bogus-model-xyz" --effort ""):
  model totally-bogus-model-xyz is not recognized as a known model or custom model in settings
exit 1
```

So when `init.model` IS present it tells us the host recognized and accepted that model, which the
frozen config reading alone does not: `settings.json` could name a model the host would reject. The
field is therefore worth recording with an honest label, which is E-04's job, rather than abandoned.

### F-04 THE STREAM HAS NO OTHER MODEL SOURCE, AND NEITHER DOES THE SIDECAR STORE

Per-event model-key census across all events of each probe turn:

```
probe.jsonl    init modelkeys=['model']   step_update [] x3   result []
nomodel.jsonl  init modelkeys=[]          step_update [] x3   result []
disp.jsonl     init modelkeys=['model']   step_update [] x3   result []
```

`init` is the only event that ever names a model. Two adjacent routes were checked and both are dead:
the host's per-session `transcript.jsonl` files (read by `agy_sessions.get_sessions`) contain zero
occurrences of `"model"` across the local corpus, and `history.jsonl` records only
`['display', 'timestamp', 'type', 'workspace']`. The per-conversation SQLite stores DO match the string
`model`, but only as an opaque enum (`model_enum = MODEL_PLACEHOLDER_M318`, plus a
`used_non_gemini_model` boolean), which is not a model id and is refused as a route anyway on
`ov2c9n`'s grounds. There is no `agy export` subcommand, so the OpenCode mechanism has no analogue.

### F-05 THE SEAM SWALLOWS A SIGNATURE MISMATCH, SO THE CONTRACT MUST BE TESTED AT THE SEAM

`execute_item_core` calls the injected reader inside `try/except Exception: host_model_rec = None`.
Measured on the existing twin:

```
>>> oc_runipd.observe_host_model("ses_x", options={}, repo_root=None, log_path="/tmp/x")
TypeError: observe_host_model() got an unexpected keyword argument 'log_path'
```

At that call site such a `TypeError` is caught and becomes "no record", indistinguishable from a host
that could not be asked. A reader authored with a convenient-looking `log_path=` parameter would
therefore pass its own unit tests and do nothing in production. Hence E-03's exact-signature
requirement and E-05 case (e), which drives the real `driver_module` resolution rather than passing the
observer explicitly.

### F-06 THE CONSUMER DEFAULTS AN ABSENT SOURCE TO THE OPENCODE MECHANISM, AND A SHIPPED TEST GUARDS THE ABSENCE CASE

`resolve_attempt_model` reads tier 1 as `host_model` with
`src = str(att.get("host_model_source") or "export-session-current")`. So an attempt carrying a model
with no source key is reported as having come from `opencode export`, a mechanism that never ran on
this host. E-04 therefore requires the source key on every success path.

Independently, `tests/test_run_dashboard.py::test_antigravity_run` asserts `model == "Flash"` for a
fixture whose agy `init` event is `{"event": "init", "init": {"tools": []}}`, i.e. F-01's absent-model
case, with the value arriving from `options["cost_attribution"]["model"]` at tier 5. If this plan's
reader wrote anything at all for a model-less `init` (the `"antigravity"` placeholder being the obvious
trap, since `render_agy_event` defaults to it), tier 1 would displace `"Flash"` and that shipped test
would fail. The test is a live guard on this plan's placeholder discipline, which is why E-06 forbids
editing it.

## Proposed changes (ordered, validatable)

1. Re-measure the four host facts (E-01) and the launch-path guard (E-02), stopping if the echo
   behavior has changed, because this plan's central claim depends on it.
2. Add `observe_host_model` to `agy_runipd`, at the seam's exact signature, reading the `init` event
   from the attempt's own JSONL log and returning `None` for an absent, blank, or placeholder model
   (E-03).
3. Write `host_model`, `host_model_provider` (empty, no provider in the stream), and
   `host_model_source = init-event-echo` on every success path, with the code comment stating the
   grain (E-04).
4. Pin six behavioral cases in a new `tests/test_attempt_agy_model_observation.py`, including the
   seam-contract case and the consumer-precedence case, with one shown red first (E-05).
5. Prove the three shipped dashboard model tests pass unedited and run the bare suite (E-06).

No change to `runner_shared` is required or proposed: the seam, the key writes, and the consumer
precedence all already exist from `ov2c9n` and `r5fk4k`, and the only thing missing on this host is the
symbol the seam looks for.

## Deferred / out of scope (with reason)

- CLOSING THE FLAGLESS-TURN GAP, which is F-02's finding and is NOT closable from the stream. The two
  routes that would close it both change behavior beyond recording: promoting the frozen config model
  into a `--model` flag on every turn changes what the host is ASKED for, and making the runner query
  `agy models` to resolve a default is a new per-run subprocess against a host surface this plan did
  not design for. Both are human decisions about launch behavior rather than recording, so they are
  raised in OQ-01 rather than absorbed.
- THE `audit` VERB, which writes its own `state.json` and its own lean attempt dict without passing
  through `execute_item_core`, so this plan's seam never runs for it. Same reason `ov2c9n` and its
  Order 01 excluded it; the Set orchestrator `1u4olp` names it as a separate residue.
- ANY GATE, REFUSAL, OR WARNING-TO-FAILURE on a model value or on a disagreement between the frozen and
  echoed values. `25kzda` Section 5.3a's never-a-gate posture for derived observations is the
  precedent, and `ov2c9n` declined the same obligation explicitly.
- READING THE HOST'S CONVERSATION STORE. Refused on measurement (F-04: it holds an opaque
  `MODEL_PLACEHOLDER_M318` enum, not a model id) and on principle (undocumented internal schema, no
  compatibility promise, locking hazard against a live application, machine-local absolute path of the
  kind the leak sanitizer exists to exclude).
- BACK-FILLING HISTORY. Same reason `ov2c9n` and `w33lrl` gave: a run record is an immutable record of
  what was observed at the time, and writing a model into an old attempt would assert an observation
  that never happened.
- A VERIFY-ROLE TWIN (`verify_host_model`). `resolve_attempt_model` documents a verify tier that reads
  `verify_host_model`, and measured at authoring NOTHING in `runner_shared` writes that key on EITHER
  host (zero matches), so the verify-role observation is absent for OpenCode too. Adding it here would
  make this host diverge from the twin in the opposite direction; it is a Set-level gap, not an agy
  one, and is named rather than silently skipped.
- WIDENING THE PRIVACY ALLOWLIST to admit `host_model_source`. `model_source` is already not
  allowlisted and `1u4olp` recorded a deliberate preference not to widen it; this plan inherits that
  choice rather than reopening it.

## Scope check

- Over-scope: none. One production file gains one function; one new test file. No shared-runner edit,
  no schema change, no consumer change, no spec amendment.
- Under-scope: the flagless default-configuration turn still records no echoed model (F-02, OQ-01); the
  `audit` verb gains nothing; a frozen-versus-echoed disagreement is recorded but not acted on; no
  verify-role twin on either host.
- UNDER-SCOPE, DELIBERATELY NOT CLOSED HERE AND NAMED RATHER THAN ABSORBED: this plan does not deliver
  an OBSERVATION on this host, because measurement shows the host offers none (F-01, F-04). It delivers
  an honest echo with a label that says so. A true observation would require a host surface that does
  not exist today (no `export` subcommand, no model in the transcript, an opaque enum in the store), so
  the honest position is a labeled echo plus a recorded gap, not a field that overstates itself.

## Required tests / validation

- `tests/test_attempt_agy_model_observation.py`, new, SIX behavioral cases (E-05), one shown red first,
  none requiring a host binary: the echo recorded, the absence recorded as nothing, the `"antigravity"`
  placeholder rejected, a missing/unparseable log tolerated, the SEAM-CONTRACT case driving the real
  `driver_module` resolution, and the CONSUMER case asserting tier-1 precedence with the agy label.
- The four host re-measurements from E-01, pasted with `agy --version`, including the flagless turn that
  carries no model.
- The launch-path guard from E-02, evaluated and pasted for both option shapes.
- The source label from E-04 pasted beside its code comment, plus a `resolve_attempt_model` call showing
  the agy label returned rather than the `export-session-current` default.
- The three shipped dashboard model tests (`test_antigravity_run`,
  `test_unrecorded_model_is_labeled_per_host`, `test_per_row_model_attribution_across_roles`) passing
  UNEDITED, with `git diff --stat -- tests/test_run_dashboard.py` showing no change (E-06).
- Bare `python3 -m pytest`, summary line pasted.
- NO COVERAGE-FRACTION MEASUREMENT IS CLAIMED: this lane has no `.aw/records/runs` corpus (the path is
  gitignored and absent), so an attempt-level coverage fraction is unavailable and must be reported as
  unavailable rather than fabricated.

## Spec / documentation sync

N/A, with reason. No spec governs the observed-model keys: they were introduced by `ov2c9n` under spec
`25kzda` without amending it, and this plan adds a second producer of the SAME keys with no change to
their meaning, their precedence, or the consumer contract. No `.spec.md` is declared in `Scope-Paths`
and none is touched. Specifically NOT amended: `25kzda` Section 2.1 (the run flag grammar), because this
plan adds no CLI flag by design; and `w15vzb` (per-action model selection), whose outstanding A-8
obligation concerns an unprovidable model WARNING and falling back, which is a SELECTION behavior this
plan does not touch and must not be miscredited with.

## Open questions

### OQ-01: should the runner pass the frozen config model as `--model` so the echo covers the default path, or is a labeled gap the right answer?

- Blocking: no
- Status: open
- Owner: human (maintainer)
- Resolution or deferral rationale: NOT BLOCKING, because this plan delivers a correct and honestly
  labeled field either way: with an explicit `--model` it records the accepted echo, and without one it
  records nothing and says so. The question is whether the gap should be closed, and both routes change
  LAUNCH behavior rather than recording, which is the maintainer's call and not an executor's. Option A,
  do nothing: the field is empty on default-configuration runs and `resolve_attempt_model` falls back to
  the frozen config reading at tier 2 (or to `unrecorded` at tier 6 when `settings.json` names nothing).
  Cheapest, and the gap is visible rather than hidden. Option B, promote the frozen model into a
  `--model` flag on every turn by relaxing `run_agy_turn`'s `"explicit_model" not in options` guard:
  closes the gap completely, but it changes what the host is asked for on every existing run, and a
  config value the host would REJECT currently costs nothing while under Option B it would fail the turn
  (F-03 shows rejection is a nonzero exit before any work). That risk is why this is not an executor's
  decision. Option C, resolve the host's own default by running `agy models` once per run: records a
  real default without changing the request, at the cost of a new per-run subprocess and a new host
  surface to depend on. RECOMMENDED: Option A now (this plan), with Option B or C filed as its own
  backlog item if the maintainer wants the default path covered.

### OQ-02: should the `verify_host_model` key be written, given nothing on either host writes it today?

- Blocking: no
- Status: open
- Owner: human (maintainer)
- Resolution or deferral rationale: NOT BLOCKING and deliberately out of scope. `resolve_attempt_model`
  documents a verify tier reading `verify_host_model`, and measured at authoring NOTHING writes that key
  in `runner_shared` on either host, so a verifier turn's model resolves through the frozen verify keys
  or the executor chain. Writing it here would make Antigravity the ONLY host with a verify-role
  observation, which is a cross-host asymmetry in the opposite direction from the one this plan closes.
  The honest resolution is that this is a Set-level gap belonging to a plan that touches both hosts; it
  is recorded so the next reader does not mistake the empty tier for an oversight of this plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: pasted `agy --version`; pasted first `init` line for all three launch shapes with `init.model` extracted, showing the two echoes and the one absence; pasted nonzero exit and error text for the bogus model; pasted per-event model-key census showing `model` in `init` only; and an explicit sentence stating all four facts match this plan or naming which did not. A re-measurement that finds a model for a FLAGLESS turn must be reported as a STOP, not adapted around.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the promotion guard evaluated and pasted for both option shapes (`explicit_model` present-and-`None` versus absent), showing no `--model` promoted in the default case; plus the pasted return of `agy_models.resolve_agy_default_model()` on the executing box and a pasted statement of what `resolve_attempt_model` reports today for such an attempt.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted successful call using the SEAM'S EXACT keyword set (`observe_host_model(session_id, options=..., repo_root=...)`) returning the record; pasted `None` returns for each of an `init` with no model, an `init` carrying the literal `"antigravity"`, a missing log file, and an unparseable first line, with no traceback in any case; plus a pasted `inspect.signature` of the new function showing no parameter the seam does not pass.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the chosen `host_model_source` value pasted beside the code comment stating that it is the host's echo of the argument, absent for a flagless turn, and proof of acceptance; a pasted record showing the source key present on every success path and `host_model_provider` as the empty string; and a pasted `resolve_attempt_model` call on an attempt carrying these keys returning the agy label rather than the `export-session-current` default.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `python3 -m pytest tests/test_attempt_agy_model_observation.py -o addopts=""` green with all six case names visible; the pasted RED run of one case before its fix, proving non-vacuity; and explicit confirmation that case (e) drives `execute_item_core` through the real `driver_module` resolution rather than passing the observer explicitly, since that is the case that catches the swallowed signature mismatch in F-05.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted green run of `tests/test_run_dashboard.py::test_antigravity_run`, `::test_unrecorded_model_is_labeled_per_host`, and `::test_per_row_model_attribution_across_roles`; pasted `git diff --stat -- tests/test_run_dashboard.py` showing NO change to that file; and a pasted bare `python3 -m pytest` summary line. A failure in any of the three is evidence the reader is wrong and must not be resolved by editing the test.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution; it is authored `to-review` and carries no
`Readiness:` field, because that field is an output of `/plan-review` and writing one here would forge a
review that has not happened.

EXECUTION CONTRACT. Commit only the files named in `Scope-Paths`, through
`aw commit <plan> -- <paths>`, never `git add -A` or a bare/`-a` commit, and never push. Verify the
staged set with `git diff --cached --name-only` before every commit and unstage anything not yours with
`git restore --staged <path>`, since this checkout is shared. Paste ACTUAL runner output for every test
claim. Probe the host only inside the gitignored `.aw/records/runs/` and commit no probe output.

STOP CONDITIONS, both of which are re-measurements rather than judgements. If E-01 (b) finds that a
flagless turn now DOES report a model, stop and report: the host changed from echoing to observing,
which makes OQ-01's gap self-closing and changes this plan's central claim. If any of the three shipped
dashboard model tests in E-06 fails, stop and fix the reader; do not edit the test.

POST-GATE LIFECYCLE. Execution runs through `aw ipd begin` and the atomic finalize, and the plan moves
to `.aw/records/plans/executed/` only once `aw ipd lint --phase pre-transition` conforms and every
`V-*` above carries pasted evidence with `Result: pass`. The backlog item `qswokt` is set to
`graduated` by the runner on verification; this plan does not set it `done`.
