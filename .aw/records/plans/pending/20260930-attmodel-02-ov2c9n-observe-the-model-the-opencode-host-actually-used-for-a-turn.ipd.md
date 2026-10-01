# IPD: Observe the model the OpenCode host actually used for a turn and record it beside the frozen one

- Date: 2026-09-30
- Kind: child
- Concern: THE MODEL ORDER 01 RECORDS IS WHAT THE DRIVER ASKED FOR, AND ON THE DEFAULT CONFIGURATION IT ASKS FOR NOTHING. When no `--model` is passed and no profile supplies one, `oc_runipd.run_opencode` appends no `--model` flag at all (`if options.get(model_key): argv.extend(["--model", options[model_key]])`), so the host picks; the run-level fallback tier fills that gap by resolving the host's own config at launch (`oc_models.resolve_host_default_model`), which is a CONFIG READING and not an observation of the turn. The gap that leaves is measurable and not hypothetical. The config can be unreadable, in which case `resolve_host_default_model` returns a named reason with an empty model (`no-config-found`, `unparseable-config`, `no-default-model-key`, `malformed-model-value`), and the attempt records nothing. The config can also be EDITED between launch and the turn, or name a model the provider silently substitutes. And backlog `7yz545` states the intended route ("OpenCode: from the session's assistant message modelID") on a premise that is FALSE for the event stream: measured at authoring against opencode 1.18.33, a complete turn's `--format json` stream emitted exactly three events (`step_start`, `text`, `step_finish`) and not one key naming a model, matching `runner_shared`'s own recorded census that all 32333 cost-bearing `step_finish` parts carry `{id, reason, snapshot, messageID, sessionID, type, tokens, cost}` and nothing else.
- Scope: Close that gap with the route that DOES work, measured at authoring rather than assumed: OpenCode's own `opencode export <sessionID>` emits the session's authoritative model as `info.model.id` (plus `providerID` and `variant`), and every attempt already records the `sessionID` needed to ask. Add a best-effort, never-raising reader that asks the host for the model of THIS attempt's session and records it as an OBSERVATION in its own keys (`host_model`, `host_model_provider`, `host_model_variant`, `host_model_source`), distinct from Order 01's frozen `model`. EXCLUDES changing Order 01's field or its precedence, because a request and an observation must stay separately falsifiable. EXCLUDES the Antigravity host, whose stream DOES carry a model on its `init` event and therefore needs a different and cheaper mechanism, deferred with the reason recorded. EXCLUDES making anything GATE on the observation, and excludes any refusal, warning-to-failure, or disposition change: a host that cannot be asked must cost the run nothing.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/runner_shared.py, tests/test_attempt_host_model_observation.py
- Item-Dependencies: executed:czut8j
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- From-Backlog: 7yz545
- Set: attmodel
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ov2c9n
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 all FIXED. Host surface re-executed under 1.18.33 rather than read, and two premises did not hold. PR-001 (BLOCKER): info.model is SESSION-CURRENT, not turn-specific (two turns, one session, two models -> export reports only the second), and session reuse is a shipped default (max_items_per_session 4; a review sweep shares one session run-wide), so the titular claim to record what a turn ran was unsupportable; narrowed the claim to the read window, mandated a mechanism-naming source label, pinned it as E-05 case (h), recorded OQ-04. PR-002 (HIGH): the export SPLITS id from providerID where --model JOINS them, so recording bare id would report a false substitution on EVERY oc run, inverting the headline capability; now records the joined value plus case (g). PR-003: reader would hardcode opencode while run_opencode resolves options.get(opencode). PR-004/PR-005: two cited enforcement mechanisms do not exist (NoRunnerImportTests; test_run_flag_surface.py deleted in 19313eed), both rules kept on live bases. PR-006: timings re-measured at 1.41-1.50s vs the plan's 4.71s/1.39s. PR-007/PR-008: host-free required cases; scope fence and conditional finalize ownership added. Suite green: 3512 passed, 2 skipped.

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `7yz545` as Order 02. THIS PLAN EXISTS BECAUSE THE ITEM'S STATED MECHANISM DOES NOT WORK AND A DIFFERENT ONE DOES, both measured at authoring rather than reasoned about. The item asks for "the session's assistant message modelID"; an executed probe turn showed the `--format json` stream carries no model id anywhere, so a reader over the session log would return nothing forever. But `opencode export <sessionID>` returns the model authoritatively, it was executed against three real sessions of different ages (reporting `opus-5.5`, `opus-5` with `variant: high`, and a 2026-07-era `opus-4.8`), and the value sits in the FIRST 4 KiB of the export, which is what makes the route affordable on a 284 MB session. The plan is deliberately the SECOND order rather than the first: Order 01's frozen field needs no host cooperation and is therefore the reliable floor, and this plan adds the observation on top of a floor that already holds.
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Record what the HOST actually ran, not only what the driver asked for, so an attempt launched with no
`--model` stops being unattributable and a substituted model becomes visible instead of invisible.

The test of success is that a turn launched with NO `--model` flag at all still ends with a concrete model
id on its attempt record, and that a host which cannot be asked leaves the run's outcome byte-identical.

WHAT THE MECHANISM CAN AND CANNOT CLAIM, narrowed at review rather than left overstated (F-06). The route is
`opencode export`, whose `info.model` is the session's CURRENT model, so it answers "what model is this
session on" and only answers "what ran this turn" when read in the window between this turn ending and the
next turn in the same session beginning. E-03 reads in exactly that window, so the recorded value IS this
turn's; but the field's source label must name the mechanism and its grain rather than assert turn
provenance, because session reuse is a shipped default (up to `max_items_per_session`, and a whole review
sweep shares one session). The honest claim is therefore "the model this turn's session was on, observed
immediately after the turn", which is strictly stronger than today's nothing and strictly weaker than the
title's wording.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the reader, proven against the real host before it is wired anywhere

- [x] E-01 RE-MEASURE THE HOST SURFACE THIS PLAN DEPENDS ON, AT EXECUTION, BEFORE WRITING THE READER. Three facts decide the design and all three are host-version-dependent, so each must be re-derived rather than trusted from this plan: (a) that `opencode export <sessionID>` writes JSON to STDOUT with its progress line on STDERR (measured at authoring and re-measured at review under 1.18.33: stdout parsed as JSON cleanly while stderr held `Exporting session: <id>`); (b) that `info.model.id` is present and names the model, with `info.model.providerID` and an optional `info.model.variant` beside it; (c) that a nonexistent session id exits NONZERO with `Error: Session not found: <id>` rather than emitting an empty success. Record the `opencode --version` under which the measurement was taken, because authoring measured 1.18.33 and the runbook in `tools/ipdrunner/` documents runs under 1.18.21, so the surface is NOT assumed stable across versions. IF ANY OF THE THREE HAS CHANGED, STOP AND REPORT rather than adapting the reader silently: a changed surface means this plan's premise needs re-deciding, which is a human's call.
  - ADD A FOURTH AND FIFTH MEASUREMENT, BOTH OF WHICH REVIEW MEASURED AS FALSIFYING SOMETHING THIS PLAN ASSUMED. (d) `info.model` IS SESSION-CURRENT, NOT TURN-SPECIFIC (F-06, BLOCKER): re-run review's two-turn probe (one session, turn 1 under model A, turn 2 under model B via `--session`) and paste the export's `info.model` after each turn. If it still reports only the LAST model, the reader is a reader of session state and E-03's design must honor the window F-06 defines rather than claiming to observe "this turn". (e) `info.model.id` IS NOT THE SAME NAMESPACE AS THE DRIVER'S `--model` VALUE (F-07, HIGH): export at least one session whose `providerID` is NOT `uri` and paste `id` beside `providerID`, then paste `oc_models.resolve_host_default_model()` on the same box. Review measured `id='nemotron-3.5-lightning-free'` with `providerID='opencode'` where the launch value was `opencode/nemotron-3.5-lightning-free`, so `id` ALONE is not comparable to the frozen `model` and E-02 must record the joined form as well as the parts.
  - Depends on: none
  - Expected outcome: pasted `opencode --version`; a pasted successful export's first lines showing `info.model`; a pasted failed export showing the nonzero exit and the error line; the pasted two-turn session-mutation probe from (d) showing what `info.model` reports after each turn; the pasted cross-namespace comparison from (e); and an explicit statement that all five match this plan's premises or naming which did not.
  - Execution state: performed

- [x] E-02 WRITE THE READER AS A BOUNDED, STREAMING, NEVER-RAISING FUNCTION THAT READS ONLY THE EXPORT'S HEAD. Put it in `oc_runipd` (this is an OpenCode-specific host interrogation, and `runner_shared` may import neither runner, so the host-specific reader belongs to the host) with a signature taking a session id and returning a small record or `None`. THE BOUNDED READ IS THE WHOLE DESIGN, AND IT IS MEASURED: a real session's export was 284,367,922 bytes and took about 5 seconds to write in full, while `info.model` sat at byte offset 263. Reading the head and terminating the child returned the model in 4.71 seconds for that session and about 1.3 seconds for two smaller ones, reading 4096 bytes in each case. So: spawn with stdout as a pipe, read a small bounded prefix (4 KiB was sufficient for all three sessions measured, including one whose `directory` field is a long path), terminate the child, parse the prefix by LOCATING the model object rather than by `json.loads` on a truncated document, and return. MUST NOT: read the whole export, buffer it in memory, write it to disk, or block without a timeout. MUST swallow every failure (a missing binary, a nonzero exit, an unparseable prefix, a timeout) and return `None`, for the same reason `runner_shared.turn_telemetry` swallows everything: this runs on the path that just finished an agent turn, and an observability read must never turn a completed turn into a failed one. Give it an INJECTABLE launcher parameter so a test can drive it without a host present.
  - RECORD THE JOINED IDENTIFIER, NOT ONLY `id`, BECAUSE THE TWO NAMESPACES DIFFER AND A NAIVE COMPARISON WOULD READ EVERY ATTEMPT AS A SUBSTITUTION (F-07, HIGH). Measured at review: a turn launched with `--model opencode/nemotron-3.5-lightning-free` exports `info.model.id = "nemotron-3.5-lightning-free"` with `providerID = "opencode"`, so the export SPLITS what the launch flag JOINS. A reader returning `id` alone, compared against Order 01's frozen `model`, therefore reports a DISAGREEMENT on a run where nothing was substituted at all, which is the precise false positive E-05 case (e) exists to make visible and which would make the field actively misleading. So the returned record MUST carry the joined `f"{providerID}/{id}"` as the value written to `host_model`, with `id` and `providerID` preserved separately in the record for a consumer that wants the parts. STATE IN THE CODE COMMENT that the joined form is NOT asserted to equal the frozen value even when no substitution happened (the frozen value may carry a profile alias or a differently-spelled prefix; `run_dashboard._normalize_model` already strips `uri/`, `google/`, `anthropic/` and `openai/` for exactly this class of reason), so a later reader does not add an equality assertion this plan deliberately does not make. Comparing the two is ORDER 03's decision and this plan only records both honestly.
  - USE THE HOST BINARY THE RUN IS ACTUALLY USING, NOT THE LITERAL `opencode` (F-08, MEDIUM). `oc_runipd.run_opencode` resolves its binary as `options.get("opencode") or "opencode"`, so a run launched with `--opencode <path>` drives a different binary than a bare `opencode` on `PATH`. A reader hardcoding `"opencode"` would interrogate the WRONG host (or none) on exactly the runs an operator pinned deliberately, and because the reader swallows every failure the result is a silently absent field rather than an error. Resolve the binary from the frozen `options` the same way, and note in the comment that an absent key falls back to `"opencode"` identically to the launch path.
  - Depends on: E-01
  - Expected outcome: the function exists, returns the model record for a real session id (pasted, with the elapsed time and bytes read), returns `None` for a nonexistent one without raising (pasted), and returns `None` when the binary is absent (pasted, via an injected launcher that raises `FileNotFoundError`); plus a pasted record showing the JOINED `providerID/id` value beside the separate parts, and a pasted demonstration that the binary came from `options["opencode"]` when that key is set.
  - Execution state: performed

### Task group 2: wire it at the one seam that already knows the session id

- [x] E-03 CALL THE READER ONCE PER TURN, AFTER THE TURN ENDS, WHERE THE SESSION ID IS ALREADY IN HAND, AND RECORD IT IN ITS OWN KEYS. `runner_shared.execute_item_core` already extracts the session id from the finished log (via `extract_session_id`, whose result it assigns to the attempt's `session_id` and reconciles against `state["set_sessions"]`) and, immediately after, reads `cost`/`tokens` from the same log through `run_viewer.extract_log_metrics`. That is the seam: the session id exists, the turn is over, and one more best-effort read there adds no branch to any launch path. Record `host_model`, `host_model_provider`, `host_model_variant` and `host_model_source` on the attempt, and record them ONLY when the read succeeded, which is the same conditional discipline `cost`/`tokens` already use (`if att_cost is not None`). DO NOT OVERWRITE Order 01's `model`: the two keys answer different questions and E-05 asserts they can DISAGREE without either being wrong. INJECT THE READER rather than importing it, because `runner_shared` may not import a runner and because the agy host will pass a different one or none; follow the injection pattern the same function already uses for `spawn_executor`, `driver_begin` and friends, resolving it off `driver_module` with a `None` default so a host that supplies nothing is unaffected.
  - THE IMPORT RULE IS LIVE BUT ITS NAMED GUARD IS NOT, SO DO NOT CITE IT (F-09, MEDIUM). This plan as authored cited `tests/test_runner_shared.py::NoRunnerImportTests` as the enforcement. Measured at review, that class DOES NOT EXIST (zero matches across `tests/`), and neither does the substring guard `test_no_runner_to_runner_import` that `agy_runipd` cites in a comment; both were lost in the `19313eed` suite trim. Order 01's own conventions section records the same finding independently. The RULE still holds and this plan still obeys it (the reader lives in `oc_runipd` and reaches `runner_shared` only by injection), but the executor must NOT rely on a guard catching a violation and must NOT repeat the citation as live. The citation has been removed above rather than left to mislead.
  - WHAT THIS FIELD MAY HONESTLY CLAIM IS NARROWER THAN "WHAT THIS TURN RAN", AND THE NARROWING IS MEASURED (F-06, BLOCKER). `info.model` is the session's CURRENT model, not an immutable record of the turn that produced the attempt. Measured at review on one session across two turns: turn 1 under `opencode/space-bunny-free` exported `info.model.id = "space-bunny-free"`; turn 2 in the SAME session under `opencode/nemotron-3.5-lightning-free` then exported `info.model.id = "nemotron-3.5-lightning-free"`, while the per-message `modelID` values retained BOTH in order (`['space-bunny-free', 'space-bunny-free', 'nemotron-3.5-lightning-free', 'nemotron-3.5-lightning-free']`). So a later turn in the same session OVERWRITES what this reader would report for an earlier one. THIS MATTERS HERE RATHER THAN BEING THEORETICAL, because session reuse is a shipped default: `oc_runipd.run_opencode` resolves a non-isolated turn's session from `state["session_id"]` or `state["set_sessions"][setid]`, rotating only after `options["max_items_per_session"]` (default 4), so up to four consecutive items of a Set share one session by design and a review sweep deliberately shares ONE session across the whole sweep. TWO CONSEQUENCES, BOTH MANDATORY. (1) The read must happen in the window where the answer is still this turn's: call it IMMEDIATELY after the session id is resolved and the turn has ended, BEFORE the next item's turn is launched, which the seam named above already satisfies. Do NOT defer it to finalize, to an end-of-run sweep, or to any consumer. (2) The SOURCE LABEL MUST SAY WHAT WAS ACTUALLY OBSERVED. Do not mint a label that claims turn-level provenance the mechanism cannot deliver; use a value naming the mechanism and its grain (for example `export-session-current`), and state in the code comment that a shared session read LATE would report a successor's model. A label asserting "this turn" would be the unfalsifiable conflation OQ-01 refuses to make between a request and an observation, committed a second time in the observation key itself.
  - Depends on: E-02
  - Expected outcome: a driven `execute_item_core` whose attempt record carries all four `host_model*` keys after the turn; a second driven run with the reader injected as unavailable, whose attempt carries NONE of them and is otherwise identical (both pasted); and the chosen source-label value pasted with the sentence from the code comment that states its grain.
  - Execution state: performed

- [x] E-04 BOUND THE COST AND MAKE IT OPTIONAL, BECAUSE A PER-TURN SUBPROCESS IS A REAL COST AND MUST BE REFUSABLE. Two obligations. (a) A HARD TIMEOUT on the read, set low and enforced by killing the child, so a hung host cannot stall a queue; state the chosen bound and the measurement it is based on in the code comment. RE-DERIVE THE BOUND ON THE EXECUTING BOX RATHER THAN ADOPTING THIS PLAN'S NUMBER: review re-measured the same corpus and got 1.41 to 1.50 seconds across three sessions and two trials each (including the two the plan timed at 4.71s and 1.39s), so the elapsed figure is dominated by host start-up and by cache warmth and is NOT a stable constant. Choose a bound with generous headroom over YOUR measurement and say which measurement it came from. (b) AN OPT-OUT that does not require editing code: honor the repository's existing configuration surface rather than inventing a flag. Read the same `run_analytics_config` telemetry switch the per-invocation telemetry already consults (`read_telemetry_config`, whose `enabled` defaults True and whose readers are total and never raise), or add a narrowly-scoped key to that module; whichever is chosen, DEFAULT ON (the field is the point of the Set) and document the off switch. NOTE WHY THAT MODULE AND NOT `config.py`: `run_analytics_config`'s own header records that `config.py` keeps an allowlist of top-level keys and REBUILDS its output from `default_config()`, so an unregistered key is silently dropped on the next write; `.aw/config/project.json` round-trips unknown keys and is the shipped precedent.
  - THE SPEC-AMENDMENT JUSTIFICATION FOR AVOIDING A FLAG IS STALE, AND THE CONSTRAINT STANDS ON A DIFFERENT AND BETTER BASIS (F-10, LOW). This plan (and Order 00) justify the no-new-flag rule by asserting that `tests/test_run_flag_surface.py` reads spec `25kzda` Section 2.1 AS A FILE and "fails in both directions". Measured at review, THAT TEST FILE DOES NOT EXIST: it was deleted in commit `19313eed` (4,863 lines) along with `tests/test_flag_surface_uniformity.py`, and the only live test that reads the spec as a file is `tests/test_ipd_exec_finding_codes.py`, which parses Section 4.6's finding-code table and not the flag grammar. So adding a flag would NOT turn the suite red, and an executor who discovers that may conclude the constraint was imaginary and add one. KEEP THE CONSTRAINT ANYWAY, on the honest basis: spec `25kzda` Section 2.1 still GOVERNS the run flag grammar, the repository's plan contract obliges a plan that changes a spec-governed contract to declare the `.spec.md` file in `- Scope-Paths:` and amend it in the same change, and this plan's `Scope-Paths` declares no spec file. The difference is that the constraint is now a CONTRACT obligation enforced by review and by the runners' spec-edit reconciliation, not a test that will catch you. If the config route proves impossible, STOP AND REPORT rather than adding a flag; do not rely on a deleted test's absence as permission.
  - Depends on: E-03
  - Expected outcome: a pasted test showing a deliberately-hanging injected launcher being killed at the bound with the turn's outcome unaffected; a pasted run with the opt-out engaged, showing NO `host_model*` keys and no subprocess spawned; and the chosen bound stated beside the measurement taken on the executing box.
  - Execution state: performed

### Task group 3: prove it, including that it cannot hurt a run

- [x] E-05 PIN THE OBSERVATION BEHAVIORALLY IN A NEW `tests/test_attempt_host_model_observation.py`, WITH THE DISAGREEMENT CASE AS THE CENTRAL ONE. A new file, for the same contention reason Order 01 gave: no pending plan declares this path. Required cases, each an OUTCOME and none of them reading production source: (a) a successful read records all four keys; (b) a failed read (nonzero exit) records none and raises nothing; (c) an absent binary records none and raises nothing; (d) a hanging launcher is killed at the bound and the turn's exit code, disposition and item status are IDENTICAL to a run where the read succeeded; (e) THE DISAGREEMENT CASE: an attempt whose frozen `model` is `provA/requested` and whose host reports `provB/actually-ran` records BOTH, unmodified, so a consumer can see the divergence; (f) a turn launched with NO `--model` at all (frozen `model` empty, source `unrecorded` per Order 01) ends with a concrete `host_model`, which is the coverage this whole Set exists to deliver. Case (f) is the one that must not be omitted or weakened. SHOW ONE CASE RED FIRST and paste both runs.
  - ADD TWO CASES THAT PIN WHAT REVIEW MEASURED, because without them the field's two known false-reading modes are untested. (g) THE NAMESPACE CASE (F-07): an export reporting `id = "nemotron-3.5-lightning-free"` with `providerID = "opencode"` must record `host_model` as the JOINED `opencode/nemotron-3.5-lightning-free`, NOT the bare `id`. This is the case that distinguishes a real substitution from a spelling difference, and without it case (e) can pass while the field reports a divergence on every run. (h) THE SHARED-SESSION GRAIN CASE (F-06): drive two attempts that resolve the SAME session id, with the injected reader returning a DIFFERENT model on the second call, and assert that each attempt recorded the value observed in ITS OWN window (so attempt 1 keeps the first model rather than being retro-corrected) AND that the recorded source label is the mechanism-naming one E-03 chose rather than a label claiming turn-level provenance. This pins the honest-grain decision as behavior instead of as a comment. Note the file now carries EIGHT cases, not six.
  - DO NOT SPAWN THE REAL HOST IN THE FAST SUBSET: every case above is driven through the INJECTED launcher, which is what makes them fast and deterministic. If you add any case that spawns the real `opencode` binary, mark it `@pytest.mark.slow` per this plan's own conventions, and do not let the eight required cases depend on a host being installed.
  - Depends on: E-03, E-04
  - Expected outcome: `tests/test_attempt_host_model_observation.py` with all EIGHT cases; pasted `python3 -m pytest tests/test_attempt_host_model_observation.py -o addopts=""` green with the case names visible; plus the pasted RED run proving non-vacuity.
  - Execution state: performed

- [x] E-06 MEASURE THE REAL COST AND THE REAL COVERAGE ON THIS BOX, AND PUBLISH BOTH NUMBERS. Two measurements, both on whatever corpus the executing machine has. (a) THE PER-TURN COST: time the reader against at least three real sessions of different sizes and report elapsed seconds and bytes read for each, so a reviewer can judge the overhead against a turn that costs minutes. (b) THE COVERAGE DELTA: over the runs available locally, count how many attempts would carry a concrete model from Order 01's frozen field ALONE versus from the frozen field OR this observation, and state both as a fraction. If this lane has no `.aw/records/runs` corpus say so explicitly and measure (a) against the host's own session store instead, reporting the sample size; do NOT fabricate a corpus number or carry authoring's figures forward as if re-measured. CONFIRMED AT REVIEW AND STILL TO BE RE-CONFIRMED AT EXECUTION: `.aw/records/runs` does not exist in this lane and `records/runs/` is gitignored (`.aw/.gitignore`), so the no-corpus branch is the EXPECTED path and taking it is not a shortfall. TIME AT LEAST TWO TRIALS PER SESSION and report both, because review measured the elapsed figure to be start-up- and cache-dominated rather than size-dominated (1.41 to 1.50 seconds across three sessions spanning 65 KiB to 4.6 MB, where this plan's authoring figures for two of the same sessions were 4.71s and 1.39s); a single-trial table would present a cold-cache artifact as a size effect. Also run the bare suite and paste the summary line. The review baseline is `3512 passed, 2 skipped, 3 warnings in 174.82s` with `208 tests deselected`, all green, so a failure in your run is either yours or newly pre-existing and must be named either way rather than absorbed.
  - Depends on: E-05
  - Expected outcome: a pasted table of at least three sessions timed at two trials each, with elapsed seconds and bytes read; a pasted coverage fraction with its denominator named, or an explicit statement that no local run corpus exists plus the substitute measurement and its sample size; a pasted bare `python3 -m pytest` summary line compared against review's `3512 passed, 2 skipped`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The suite is run BARE: `pyproject.toml` `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`. Use `-o addopts=""` for per-test counts from a narrowed run; never `-n0`, never a second `-q`, never `-p no:randomly`.
- `runner_shared` MAY NOT IMPORT EITHER RUNNER, which is why this plan's reader lives in `oc_runipd` and is INJECTED into `execute_item_core` through the `driver_module` resolution that function already performs for a dozen other names. THE RULE IS LIVE AND ITS NAMED GUARD IS NOT (F-09): this plan originally cited `tests/test_runner_shared.py::NoRunnerImportTests`, and that class does not exist (zero matches in `tests/`), nor does the substring guard `test_no_runner_to_runner_import` that `agy_runipd` still cites in a comment; both died in the `19313eed` suite trim, as Order 01's conventions independently record. Obey the rule; do not cite a guard that will not catch you.
- A NEW CLI FLAG IS REFUSED BY THE PLAN CONTRACT, NOT BY A TEST (F-10). Spec `25kzda` Section 2.1 declares the run flag grammar, and this repository's contract obliges a plan changing a spec-governed contract to declare the `.spec.md` in `- Scope-Paths:` and amend it in the same change; this plan declares none. The test this plan originally cited as the enforcement, `tests/test_run_flag_surface.py`, WAS DELETED in commit `19313eed` (4,863 lines, alongside `tests/test_flag_surface_uniformity.py`), and the only live spec-file-reading test is `tests/test_ipd_exec_finding_codes.py` over Section 4.6's finding codes. So a flag would not turn the suite red; it would breach the contract silently, which is worse. E-04 avoids a flag on that basis.
- BEST-EFFORT MEANS NEVER RAISES, AND THERE IS A SHIPPED PRECEDENT TO COPY: `runner_shared.turn_telemetry` documents "EVERY FAILURE MODE IS SWALLOWED, and that is the requirement rather than defensive habit" because it wraps the launch of the agent process that does the actual work. This reader runs at the same criticality and adopts the same discipline.
- A SLOW TEST IS MARKED `slow`. Any case in E-05 that spawns a real host binary must carry `@pytest.mark.slow`, because the default suite deselects that marker and a subprocess-spawning test in the fast subset slows every lane.

## Findings

Measured in this lane at HEAD by execution.

### F-01 THE ITEM'S STATED MECHANISM RETURNS NOTHING: the event stream carries no model

A complete real turn was executed at authoring (`opencode run --format json --dir <tmp> "Reply with exactly
the word: ok"`, exit 0, 3 lines) and its whole stream was:

```
{"type": "step_start",  "sessionID": "ses_...", "part": {"id": "...", "messageID": "...", "snapshot": "...", "type": "step-start"}}
{"type": "text",        "sessionID": "ses_...", "part": {"id": "...", "messageID": "...", "type": "text", "text": "ok", "time": {...}}}
{"type": "step_finish", "sessionID": "ses_...", "part": {"id": "...", "reason": "stop", "snapshot": "...", "messageID": "...", "type": "step-finish", "tokens": {...}, "cost": 0.1158652}}
```

No key names a model. This corroborates `runner_shared`'s own recorded census ("all 32333 cost-bearing
`step_finish` parts carry the key set `{id, reason, snapshot, messageID, sessionID, type, tokens, cost}` and
nothing else") and `run_analytics_statistics.model_comparison`'s REFUSED INFERENCE 2 (the 16 `modelID`
occurrences in the corpus sit on `task` tool calls and name a SUB-AGENT). A session-log reader for the model
is therefore not merely unimplemented, it is unimplementable against this stream.

### F-02 THE ROUTE THAT WORKS: `opencode export` reports the model authoritatively

Executed against three real sessions of different ages and sizes:

| Session | reported `info.model` | export size |
|---|---|---|
| the probe turn above | `{"id": "its_direct/pt3-claude-opus-5.5-1m-us", "providerID": "uri", "variant": "default"}` | 4,093 bytes |
| a 119-message run session | `{"id": "its_direct/pt3-claude-opus-5-1m-us", "providerID": "uri", "variant": "high"}` | 1,031,183 bytes |
| a 6,658-message 2026-07 session | `{"id": "its_direct/pt3-claude-opus-4.8-1m-us", "providerID": "uri"}` | 284,367,922 bytes |

Three properties this plan depends on, each measured: the JSON goes to STDOUT while the progress line
`Exporting session: <id>` goes to STDERR (so stdout parses cleanly); `variant` is present sometimes and
absent sometimes, so it must be optional; and a nonexistent session exits 1 with
`Error: Session not found: <id>`, so failure is detectable rather than silent.

### F-03 THE BOUNDED READ IS WHAT MAKES IT AFFORDABLE, and it was executed rather than reasoned about

A full export of the 284 MB session took about 5 seconds. Reading only the head and terminating the child:

```
ses_<probe>    elapsed=1.39s  bytes_read=4093  model_segment='"model": {\n "id": "its_direct/pt3-claude-opus-5.5-1m-us", "providerID": "uri", "variant": "default"'
ses_<284MB>    elapsed=4.71s  bytes_read=4096  model_segment='"model": {\n "id": "its_direct/pt3-claude-opus-4.8-1m-us", "providerID": "uri"},  "version": "1.17.15"'
ses_<119msg>   elapsed=1.32s  bytes_read=4096  model_segment='"model": {\n "id": "its_direct/pt3-claude-opus-5-1m-us", "providerID": "uri", "variant": "high"'
```

`info.model` sat at byte offset 263 in the 284 MB export. 4 KiB was sufficient in all three cases. The
elapsed time is dominated by host startup rather than by bytes, which is why the largest session is only
3.5x the smallest and not 70,000x.

### F-04 THE ANTIGRAVITY HOST NEEDS A DIFFERENT MECHANISM, WHICH IS WHY IT IS DEFERRED HERE

Unlike OpenCode, the Antigravity stream DOES carry a model: `agy_runipd`'s event formatter reads
`event["init"]["model"]` (defaulting to the literal `"antigravity"`) and renders it to the terminal, and that
value is never persisted. So the agy side needs no subprocess at all, only a persist of a value already
parsed in the stream loop. Bundling the two would put a cheap in-stream capture and an out-of-band
subprocess interrogation in one plan with one validation surface, and would make the agy half wait on the
oc half's cost and opt-out design. Deferred with a named carrier (see Deferred).

### F-05 `variant` IS PART OF THE IDENTITY AND DROPPING IT WOULD LOSE A REAL DISTINCTION

Two of the three measured sessions report a `variant` (`default`, `high`) and one reports none. The variant
is a provider-specific reasoning effort that `oc_runipd.run_opencode` passes as its own `--variant` flag and
that `run_analytics_telemetry.ALLOWED_FIELDS` already admits as `model_variant`, so two attempts under the
same model id at different variants are genuinely different configurations. Recording it as its own optional
key keeps the model id comparable while preserving the distinction. Note the variant is reported as the
literal `"default"` for a turn launched with NO `--variant` flag (measured at review), so an absent flag and
an explicit `--variant default` are indistinguishable in the export; the key is still worth recording, but it
cannot be read as evidence that a variant was explicitly requested.

### F-06 REVIEW FINDING, BLOCKER: `info.model` IS SESSION-CURRENT, SO A SHARED SESSION OVERWRITES AN EARLIER TURN'S ANSWER

The plan's title and Goal claim to record "the model the OpenCode host actually used for a turn". Measured at
review, the mechanism cannot deliver turn grain: `info.model` is the session's CURRENT model and a later turn
in the same session REPLACES it.

Executed against a real host (1.18.33), one session, two turns:

```
TURN 1  --model opencode/space-bunny-free            -> export info.model.id = space-bunny-free
TURN 2  --session <same> --model opencode/nemotron-3.5-lightning-free
                                                      -> export info.model.id = nemotron-3.5-lightning-free
full-export per-message modelID census (ordered):
  ['space-bunny-free', 'space-bunny-free', 'nemotron-3.5-lightning-free', 'nemotron-3.5-lightning-free']
```

So the per-message `modelID` values retain both models in order while `info.model` retains only the last.
THIS IS REACHABLE ON THE SHIPPED DEFAULT CONFIGURATION, not only in a contrived probe:
`oc_runipd.run_opencode` resolves a non-isolated turn's session from `state["session_id"]` or
`state["set_sessions"][item["setid"]]` and rotates only once `options["max_items_per_session"]` (default 4)
is reached, so up to four consecutive items of a Set legitimately share one session; a review sweep shares
ONE session across the entire sweep by design (`REVIEW_SWEEP_SESSION_KEY`).

The consequence for this plan is bounded rather than fatal, which is why the remedy is a narrowed claim and
not a replan: reading IMMEDIATELY after the turn ends and before the next turn launches (the seam E-03
already chose) does observe this turn's model. But the FIELD must not claim more than that, and the SOURCE
LABEL is where the honesty lives. E-03 now requires a mechanism-naming label (for example
`export-session-current`) plus a code comment stating that a late read of a shared session would report a
successor's model, and E-05 case (h) pins the behavior. A label asserting turn-level provenance would repeat,
inside the observation key, exactly the request-versus-observation conflation OQ-01 correctly refuses.

### F-07 REVIEW FINDING, HIGH: THE EXPORT SPLITS THE IDENTIFIER THE LAUNCH FLAG JOINS, SO A NAIVE READER REPORTS A FALSE SUBSTITUTION

`info.model` carries `id` and `providerID` as SEPARATE fields, and `id` alone is not in the same namespace as
the `--model` value the driver passes. Measured at review:

```
launched with:  --model opencode/nemotron-3.5-lightning-free
export reports: "id": "nemotron-3.5-lightning-free", "providerID": "opencode"   -> joined: opencode/nemotron-3.5-lightning-free
launched with:  (no --model; host default)
export reports: "id": "its_direct/pt3-claude-opus-5-1m-us", "providerID": "uri" -> joined: uri/its_direct/pt3-claude-opus-5-1m-us
oc_models.resolve_host_default_model() -> model='uri/its_direct/pt3-claude-opus-5.5-1m-us', key='model'
```

Note the second case: the `id` ITSELF contains a slash, so the split is not a simple one-segment prefix and a
reader cannot recover the launch spelling by guessing. A reader recording the bare `id` and a consumer
comparing it against Order 01's frozen `model` would see a mismatch on EVERY oc run, making the plan's
headline capability (a visible substitution) fire constantly on runs where nothing was substituted. E-02 now
requires the joined `providerID/id` as the recorded value with the parts preserved, and E-05 case (g) pins
it. The plan must NOT additionally assert equality with the frozen value even on a clean run: a profile alias
or a differently-spelled prefix can differ legitimately, which is why `run_dashboard._normalize_model` exists
and strips `uri/`, `google/`, `anthropic/` and `openai/`.

### F-08 REVIEW FINDING, MEDIUM: THE READER MUST USE THE RUN'S OWN BINARY, NOT THE LITERAL `opencode`

`oc_runipd.run_opencode` resolves its binary as `options.get("opencode") or "opencode"` and the runner
registers an `--opencode` flag, so an operator may pin a specific binary. A reader hardcoding `"opencode"`
would interrogate a DIFFERENT host than the one that ran the turn, or none at all. Because the reader
swallows every failure by design, the symptom is a silently absent field on exactly the runs an operator
configured deliberately, with no diagnostic. E-02 now requires resolving the binary from the frozen
`options`, falling back to `"opencode"` identically to the launch path.

### F-09 REVIEW FINDING, MEDIUM: THE IMPORT GUARD THIS PLAN CITED AS ENFORCEMENT DOES NOT EXIST

E-03 justified injection over import by citing `tests/test_runner_shared.py::NoRunnerImportTests` as the
enforcing guard. Measured at review, that class does not exist anywhere under `tests/` (zero matches), and
the related substring guard `test_no_runner_to_runner_import`, which `agy_runipd` still names in a comment,
is equally absent; both were lost in the `19313eed` suite trim. Order 01 recorded the same finding
independently in its own conventions, so the Set now states it consistently. The RULE is still correct and
this plan still obeys it; the citation was removed from E-03 and from the conventions section so the executor
does not rely on a guard that cannot fire.

### F-10 REVIEW FINDING, LOW: THE NO-NEW-FLAG CONSTRAINT RESTS ON A DELETED TEST, AND NEEDED A LIVE BASIS

E-04, the conventions section, and Order 00 all justify avoiding a new CLI flag by asserting that
`tests/test_run_flag_surface.py` reads spec `25kzda` Section 2.1 as a file and "fails in both directions".
That file was DELETED in commit `19313eed` (4,863 lines, together with `tests/test_flag_surface_uniformity.py`
at 460 lines). The only live test that reads a spec as a file is `tests/test_ipd_exec_finding_codes.py`, and
it parses Section 4.6's IPD-EXEC finding-code table, not the flag grammar.

The constraint is still RIGHT and its basis has been corrected in place: Section 2.1 still governs the flag
grammar, and the repository's plan contract requires a plan changing a spec-governed contract to declare the
`.spec.md` in `- Scope-Paths:` and amend it in the same change. The risk this finding removes is specific: an
executor who tested the cited claim, found no such test, and concluded the constraint was imaginary would add
a flag and breach the contract silently, with no red suite to stop them.

## Proposed changes (ordered, validatable)

1. Re-measure the host-surface facts at execution, now FIVE including the session-mutation probe (F-06) and
   the cross-namespace comparison (F-07), and stop if any changed (E-01).
2. A bounded, streaming, never-raising reader in `oc_runipd` returning the session's model record, recording
   the JOINED `providerID/id` and using the run's own binary (E-02).
3. One best-effort call at the post-turn seam in `execute_item_core` where the session id is already in
   hand, recording four `host_model*` keys conditionally, with the reader INJECTED and with a source label
   that names the mechanism's real grain rather than claiming turn provenance (E-03).
4. A hard timeout re-derived on the executing box and an opt-out through the existing config surface (E-04).
5. A new behavioral test file with EIGHT cases: the disagreement, the no-`--model` coverage case, the
   namespace case, and the shared-session grain case (E-05).
6. Published cost and coverage measurements taken on the executing box, two trials per session (E-06).

## Deferred / out of scope (with reason)

- THE ANTIGRAVITY HALF, for the reason in F-04: its model arrives in the stream (`event["init"]["model"]`,
  already parsed and already discarded) so it needs a persist and not an interrogation, and it shares none of
  this plan's cost, timeout or opt-out design. It is a small, separable change and should be filed as its own
  backlog item at execution; Order 00's completion criteria name the residue so the Set does not claim
  coverage it did not deliver on that host.
  - Carrier: qswokt
- THE `audit` VERB, which writes its own `state.json` and its own lean attempt dict without passing through
  `execute_item_core`, so this plan's seam never runs for it. Same reason Order 01 excluded it.
  - Carrier-Declined: The audit verb writes a synthetic attempt dict outside the normal run execution path and is deliberately out of scope; no obligation is outstanding.
- ANY GATE, REFUSAL OR WARNING-TO-FAILURE ON A DISAGREEMENT. This plan makes a divergence between requested
  and actual VISIBLE; deciding what to do about one is a policy question with a real false-positive cost
  (a provider alias, a version suffix, a normalization difference would all read as divergence), and
  `25kzda` Section 5.3a's "NEVER A GATE" posture for derived observations is the precedent for keeping it
  out.
  - Carrier-Declined: Making divergence visible without gating adheres to spec 25kzda Section 5.3a precedent (derived observation, never a gate); no gating obligation is accepted or outstanding.
- READING THE HOST'S SQLITE STORE DIRECTLY. The model is in there (the store's `message.data` JSON carries
  `modelID` per assistant message, confirmed at authoring), and it is REFUSED as a route: it is an
  undocumented internal schema with no compatibility promise, reading another application's live database is
  a correctness and locking hazard, and its path is a machine-local absolute path of exactly the kind the
  leak sanitizer exists to keep out of tracked output. `opencode export` is the host's OWN supported
  interface to the same fact and is used instead.
  - Carrier-Declined: Refused technical approach due to internal unversioned schema, locking hazard, and path leakage risk; replaced by opencode export.
- BACK-FILLING HISTORY. Same reason as Order 01: `w33lrl` set the precedent, and a session's export is not
  guaranteed to still exist for an old run.
  - Carrier-Declined: Historical run states are immutable records under w33lrl precedent and host sessions may not exist; no back-fill obligation is owed.

## Scope check

- Over-scope: none. Two production files, one new test file. The `runner_shared` edit is one injected call
  at an existing seam plus the four conditional writes.
- Under-scope: the Antigravity host gains nothing here (named above, with a carrier); the `audit` verb gains
  nothing; a disagreement is recorded but not acted on.
- UNDER-SCOPE, DELIBERATELY NOT CLOSED HERE AND NAMED AT REVIEW (F-06): the mechanism cannot give TURN grain,
  only session-current-read-immediately-after grain. A turn-exact observation would require the per-message
  `modelID` values, which the export DOES retain in order (measured) but which sit arbitrarily deep in a
  document that can reach hundreds of megabytes, destroying the bounded-head read that makes this plan
  affordable at all. That is a materially different design with a different cost profile, so it is named
  rather than absorbed: this plan delivers the cheap 95-percent answer and labels it honestly. If a consumer
  later needs turn-exact attribution, it is a new plan.

## Required tests / validation

- `tests/test_attempt_host_model_observation.py`, new, EIGHT behavioral cases (E-05), one shown red first,
  every one driven through the injected launcher so none requires a host binary in the fast subset.
- The FIVE host-surface re-measurements from E-01, pasted with the host version, including the two-turn
  session-mutation probe (F-06) and the cross-namespace comparison (F-07).
- THE JOINED IDENTIFIER PROVEN (F-07): the reader's record pasted for a session whose `providerID` is not
  `uri`, showing `host_model` carrying `providerID/id` and not the bare `id`.
- THE SOURCE LABEL'S GRAIN STATED (F-06): the chosen label pasted beside the code comment that says a late
  read of a shared session would report a successor's model.
- The timed reads (two trials per session) and the coverage fraction from E-06, pasted.
- Bare `python3 -m pytest`, summary line pasted, compared against review's `3512 passed, 2 skipped`.

## Spec / documentation sync

- NO SPEC AMENDMENT, AND E-04 IS SHAPED TO KEEP IT THAT WAY, ON A CORRECTED BASIS (F-10). A new CLI flag
  would require amending spec `25kzda` Section 2.1, whose flag grammar that section governs; the obligation
  comes from the repository's plan contract (declare the `.spec.md` in `- Scope-Paths:` and amend it in the
  same change), NOT from a test. The test this plan originally cited, `tests/test_run_flag_surface.py`, was
  deleted in commit `19313eed`, so nothing mechanical will catch an added flag. E-04 therefore requires the
  opt-out to use the existing configuration surface and to STOP and report if that proves impossible.
  `Scope-Paths` declares no `.spec.md` file, so the runners' spec-edit announcement will correctly report
  none.
- Spec `25kzda` Section 5.3a ("DERIVED, BEST-EFFORT, NEVER A GATE") is the governing PRECEDENT for the
  posture this plan takes, and is cited rather than changed: the section governs the telemetry stream, and
  this field lives in `state.json`, so no sentence there becomes false.
- NO DOCS CHANGE HERE. `docs/` carries no run-state schema page. If Order 03 adds one, the `host_model*`
  keys belong in it; that is Order 03's to decide, not this plan's to pre-empt.

## Open questions

### OQ-01: Should the observation overwrite the frozen model when the two disagree?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: NO. TWO KEYS, ALWAYS, AND NEITHER OVERWRITES THE OTHER. The two answer different questions: the frozen value is WHAT WE ASKED FOR (authoritative about the driver's intent, available even when the host cannot be reached) and the observation is WHAT RAN (authoritative about the turn, available only when the host answers). Collapsing them loses the ability to detect a substitution at all, which is one of the two reasons this plan exists. It also makes the field unfalsifiable: a consumer reading a single key cannot tell whether a value came from a config read at launch or from the host afterwards, and `run_dashboard._run_model` already demonstrates the value of returning a SOURCE beside a model for exactly that reason. Order 03 decides the consumer-side PRECEDENCE between them (and should prefer the observation where present, since it is the stronger evidence), which is a reader's decision and deliberately not a writer's.

### OQ-02: Is a per-turn subprocess acceptable overhead?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: YES, ON THE MEASURED NUMBERS, AND E-04 BOUNDS AND MAKES IT REFUSABLE ANYWAY. The measured cost is 1.3 to 4.7 seconds once per turn, against turns that routinely run for minutes and cost dollars (the corpus baseline records a median attempt cost of $11.79), so the read is a fraction of a percent of a turn. The honest counter-argument is that it is a fraction of a percent of a turn that FAILED FAST too, and a queue of quick refusals would pay it repeatedly; that is why E-03 places the call after a turn that actually RAN (the seam that already read cost and tokens from a real log) rather than on a refusal path, and why E-04 requires both a hard timeout and an opt-out. A cheaper design exists and was rejected as premature: batching one export call per SESSION rather than per attempt, which is correct but complicates the seam for a saving that the measured numbers do not justify. Recorded here so a reviewer may overrule with the numbers in front of them.

### OQ-03: What should the reader do when the export's head does not contain the model?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RETURN `None` AND RECORD NOTHING; do NOT widen the read to compensate. A head that lacks the model means the surface changed (the model sat at offset 263 in all three sessions measured, including the 284 MB one), and the correct response to a changed host surface is an honest absence plus E-01's stop-and-report at the next execution, not an unbounded read that would pull hundreds of megabytes through a pipe to find a field that may no longer exist. The frozen field from Order 01 remains present in that case, so an absent observation degrades coverage to Order 01's floor rather than to nothing. This is the same fail-open-to-the-weaker-source discipline `run_viewer.extract_log_metrics` uses when a log carries no cost. ONE CLAUSE IN THIS RESOLUTION IS NOW KNOWN WRONG AND THE RESOLUTION SURVIVES IT (review): the model did NOT sit at offset 263 in all sessions, it sat at 262, 365 and 367 in review's three, because the offset moves with the length of the preceding `directory` and `title` fields (both of which are free-form and unbounded in principle). That makes the 4 KiB bound an EMPIRICAL headroom figure rather than a derived one, which strengthens the case for returning `None` rather than widening: a head that lacks the model may mean a long path rather than a changed surface, and the honest response to either is the same absence plus a stop-and-report.

### OQ-04: May the field be labelled as the model "this turn" ran, given that the export reports session-current state?

- Blocking: no
- Status: resolved
- Owner: reviewer (plan-review, 2026-10-01)
- Resolution or deferral rationale: NO. LABEL THE MECHANISM AND ITS GRAIN, NOT THE CLAIM THE PLAN WISHED FOR. Measured at review (F-06), `info.model` is the session's CURRENT model: two turns in one session under different models left the export reporting only the SECOND, while the per-message `modelID` values retained both in order. Session reuse is a shipped default rather than a contrived case (`max_items_per_session` defaults to 4, and a review sweep shares one session run-wide), so the overwrite is reachable in normal operation. THREE OPTIONS WERE CONSIDERED. (1) Read the per-message `modelID` for true turn grain: REJECTED, because those values sit arbitrarily deep in a document measured at 284 MB, which destroys the bounded-head read that makes the whole plan affordable; it is named in Scope check as a separate future plan rather than absorbed. (2) Keep the plan's wording and accept that the field sometimes names a successor's model: REJECTED, because an unfalsifiable field is exactly what OQ-01 refuses for the frozen-versus-observed pair, and committing the same conflation inside the observation key would be worse for being hidden. (3) CHOSEN: read in the window where the answer is still this turn's (immediately after the turn ends, before the next launches, which is the seam E-03 already picked) and make the SOURCE LABEL name the mechanism and grain, with the limitation stated in a code comment and pinned by E-05 case (h). This is a REVERSIBLE decision: it constrains a label and a comment, both editable, and Order 03 remains free to decide what a consumer does with the value. Recorded rather than escalated as blocking because the plan remains sound and valuable under option (3), and because the narrowing REDUCES what the plan asserts rather than expanding its scope; a maintainer who wants true turn grain should say so and get a separate plan, which Scope check now names.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted `opencode --version`; the pasted head of a successful export showing `info.model` with its `id` and `providerID`; the pasted nonzero-exit failure for a bogus session id showing the error text; the pasted TWO-TURN SESSION-MUTATION PROBE (F-06) showing `info.model` after turn 1 under model A and after turn 2 under model B in the SAME session, which is what establishes the grain the field may claim; the pasted CROSS-NAMESPACE COMPARISON (F-07) showing a non-`uri` `providerID` beside its `id` and `oc_models.resolve_host_default_model()`'s value on the same box; and a written verdict naming each of the FIVE premises as confirmed or changed. A changed premise must be reported, not worked around. Review's own measurements for the two new probes are in F-06 and F-07 and may NOT be pasted in place of re-running them.
  - Observed evidence: All five host-surface facts re-measured and confirmed under opencode 1.18.33; two-turn probe confirmed info.model is session-current (PR-001/F-06); cross-namespace comparison confirmed export splits providerID and id (F-07).
    1. opencode version:
    ```
    $ opencode --version
    1.18.33
    ```
    2. Head of successful export (JSON to stdout, progress to stderr):
    ```
    $ opencode export ses_<probe>
    Exporting session: ses_<probe>
    {
      "info": {
        "id": "ses_<probe>",
        "slug": "silent-falcon",
        "projectID": "449edf331178f4340ef9a39c043dc8b88beeda08",
        "directory": "<repo-root>",
        "path": "",
        "title": "Confirm with \"ok\"",
        "agent": "build",
        "model": {
          "id": "nemotron-3.5-lightning-free",
          "providerID": "opencode",
          "variant": "default"
        },
        "version": "1.18.33",
        "summary": { ...
    ```
    3. Nonexistent session exits nonzero (code 1) with error text on stderr:
    ```
    $ opencode export ses_<nonexistent>
    Exporting session: ses_<nonexistent>
    Error: Session not found: ses_<nonexistent>
    (exit code: 1)
    ```
    4. Two-turn session-mutation probe (F-06) re-executed on this host:
    Probe session `ses_<probe>`:
    - Turn 1 ran with `opencode run --model opencode/space-bunny-free "Confirm with 'ok'"`
    - Turn 2 ran with `opencode run --session <ses_id> --model opencode/nemotron-3.5-lightning-free "Confirm with 'ok'"`
    Messages census vs session export `info.model`:
    ```
    messages[1].info (assistant turn 1): modelID='space-bunny-free', providerID='opencode'
    messages[3].info (assistant turn 2): modelID='nemotron-3.5-lightning-free', providerID='opencode'
    export info.model: {'id': 'nemotron-3.5-lightning-free', 'providerID': 'opencode', 'variant': 'default'}
    ```
    Turn 1's model was overwritten at the session-level `info.model` by Turn 2, confirming `info.model` is session-current (PR-001/F-06).
    5. Cross-namespace comparison (F-07) on this box:
    ```
    Export reports: id='nemotron-3.5-lightning-free', providerID='opencode' -> joined: opencode/nemotron-3.5-lightning-free
    resolve_host_default_model(): HostDefaultModel(model='uri/its_direct/pt3-claude-opus-5.5-1m-us', key='model', reason='', config_digest='0b4284410c2f6013218d824c5025a07eb1563f75bf5152118556dbeb6f0c028f', config_name='opencode.json')
    ```
    The export splits what launch joins, and id can contain slashes (`its_direct/pt3-claude-opus-5.5-1m-us`), confirming F-07.
    6. Written verdict on the 5 premises:
    - (a) JSON on stdout, progress line on stderr: CONFIRMED.
    - (b) info.model.id present with providerID and optional variant: CONFIRMED.
    - (c) nonexistent session exits nonzero (code 1) with Error: Session not found: CONFIRMED.
    - (d) info.model is session-current, not turn-specific: CONFIRMED.
    - (e) info.model splits providerID and id where launch joins: CONFIRMED.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: three pasted invocations of the reader: a real session (showing the returned record, the elapsed seconds and the bytes read, proving the read was BOUNDED and not full), a nonexistent session (returning `None`, no traceback), and an injected launcher raising `FileNotFoundError` (returning `None`, no traceback). The bytes-read figure is required: without it the boundedness claim is unverified. PLUS THE JOINED IDENTIFIER (F-07): a pasted record for a session whose `providerID` is NOT `uri`, showing `host_model` equal to `providerID/id` and NOT the bare `id`, with the separate parts also present; and the quoted code comment stating that the joined value is not asserted equal to the frozen one. PLUS THE BINARY RESOLUTION (F-08): a pasted demonstration that the reader used `options["opencode"]` when that key was set, for example an injected launcher recording the argv it was handed.
  - Observed evidence: Reader verified across real session (bounded 4096 bytes read), nonexistent session (None returned), and absent binary (None returned); joined providerID/id identifier recorded; options[opencode] binary resolution confirmed.
    1. Three reader invocations:
    - Real session (bounded read):
    ```python
    >>> rec = oc_runipd.observe_host_model("ses_<probe>")
    >>> rec
    {'host_model': 'opencode/nemotron-3.5-lightning-free', 'host_model_provider': 'opencode', 'host_model_source': 'export-session-current', 'id': 'nemotron-3.5-lightning-free', 'providerID': 'opencode', 'host_model_variant': 'default', 'variant': 'default'}
    # elapsed: 4.32s, bytes read: 4096 (bounded prefix out of full export)
    ```
    - Nonexistent session:
    ```python
    >>> oc_runipd.observe_host_model("ses_<nonexistent>")
    None
    ```
    - Injected launcher raising FileNotFoundError:
    ```python
    >>> oc_runipd.observe_host_model("ses_<probe>", launcher=lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("opencode not found")))
    None
    ```
    2. Joined identifier (F-07):
    For providerID `opencode` and id `nemotron-3.5-lightning-free`, `host_model` is joined as `opencode/nemotron-3.5-lightning-free` rather than bare `nemotron-3.5-lightning-free`:
    `{'host_model': 'opencode/nemotron-3.5-lightning-free', 'host_model_provider': 'opencode', 'id': 'nemotron-3.5-lightning-free', 'providerID': 'opencode'}`
    Quoted code comment from `agent_workflows/oc_runipd.py`:
    > "The joined identifier f'{providerID}/{id}' is recorded in host_model, with providerID and id preserved separately. The joined form is NOT asserted to equal the frozen launch model value even when no substitution happened (e.g. the launch value may use a profile alias or a differently-spelled prefix; run_dashboard._normalize_model already strips uri/, google/, anthropic/, openai/ for this reason). Comparing the two is Order 03's decision and this reader records what the host reported honestly."
    3. Binary resolution (F-08):
    Injected launcher recording argv:
    ```python
    captured_argv = []
    oc_runipd.observe_host_model("ses_123", options={"opencode": "/custom/bin/my-opencode"}, launcher=recording_launcher)
    # captured_argv: [['/custom/bin/my-opencode', 'export', 'ses_123']]
    ```
    The reader uses `options.get("opencode") or "opencode"`, matching `run_opencode` launch semantics.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: two pasted attempt records from driven `execute_item_core` runs, one with the reader available (all four `host_model*` keys present) and one with it unavailable (none of them present, and every other key identical). The second is what proves an unreachable host changes nothing. PLUS THE HONEST GRAIN (F-06, and OQ-04's recorded resolution), which must be checked here rather than assumed: paste the `host_model_source` VALUE actually written, confirm it names the mechanism and its grain (and does NOT assert that the value is turn-specific), and quote the code comment stating that a late read of a shared session would report a successor's model. Also state which call site the read was placed at and confirm it executes BEFORE the next item's turn is launched. A record whose source label claims turn provenance FAILS this item even if all four keys are present.
  - Observed evidence: Driven execute_item_core verified with observer present (all 4 host_model* keys recorded) and absent (zero keys, byte-identical attempt record); honest grain export-session-current verified; call site executes immediately post-turn before next item.
    1. Driven `execute_item_core` attempt records:
    Attempt with observer available:
    ```json
    {
      "number": 1,
      "started_at": "2026-10-01T20:29:07+00:00",
      "starting_head": "61548f0f3b27d939726fcebca92a2bcbda80e216",
      "starting_branch": "main",
      "starting_status": "?? .aw/",
      "prompt": "/tmp/tmpaugyenqu/.aw/runs/run-test/prompts/01-tst001-exec-attempt-1.md",
      "prompt_sha256": "a48bc5a03657c9107aa683fd4a620f144df5ed09f837078b2eae5bd792ccfdea",
      "session_id": "ses_abc123",
      "log": "/tmp/tmpaugyenqu/.aw/runs/run-test/logs/test.log",
      "recovery": false,
      "action": "execute",
      "model": "opencode/nemotron-3.5-lightning-free",
      "model_source": "options",
      "ended_at": "2026-10-01T20:29:07+00:00",
      "exit_code": 0,
      "ending_head": "61548f0f3b27d939726fcebca92a2bcbda80e216",
      "ending_branch": "main",
      "ending_status": "?? .aw/",
      "argv": [
        "mock_agent"
      ],
      "host_model": "opencode/nemotron-3.5-lightning-free",
      "host_model_provider": "opencode",
      "host_model_variant": "default",
      "host_model_source": "export-session-current",
      "disposition": "fail-gate",
      "verification": null,
      "verification_status": null,
      "defect_report": {
        "state": "none-found",
        "verdict": "valid",
        "findings": [],
        "coerced": false,
        "coercions": [],
        "reasked": false,
        "reask_reason": "the report was usable; no follow-up needed",
        "reask_state": null,
        "reask_verdict": null
      },
      "turn_retry_skipped": "disposition 'fail-gate' is not retryable: lifecycle gate or clean-base gate refused; not a host failure to retry without human action"
    }
    ```
    Attempt with observer unavailable (returns None):
    ```json
    {
      "number": 1,
      "started_at": "2026-10-01T20:29:07+00:00",
      "starting_head": "61548f0f3b27d939726fcebca92a2bcbda80e216",
      "starting_branch": "main",
      "starting_status": "?? .aw/",
      "prompt": "/tmp/tmpaugyenqu/.aw/runs/run-test/prompts/01-tst001-exec-attempt-1.md",
      "prompt_sha256": "a48bc5a03657c9107aa683fd4a620f144df5ed09f837078b2eae5bd792ccfdea",
      "session_id": "ses_abc123",
      "log": "/tmp/tmpaugyenqu/.aw/runs/run-test/logs/test.log",
      "recovery": false,
      "action": "execute",
      "model": "opencode/nemotron-3.5-lightning-free",
      "model_source": "options",
      "ended_at": "2026-10-01T20:29:07+00:00",
      "exit_code": 0,
      "ending_head": "61548f0f3b27d939726fcebca92a2bcbda80e216",
      "ending_branch": "main",
      "ending_status": "?? .aw/",
      "argv": [
        "mock_agent"
      ],
      "disposition": "fail-gate",
      "verification": null,
      "verification_status": null,
      "defect_report": {
        "state": "none-found",
        "verdict": "valid",
        "findings": [],
        "coerced": false,
        "coercions": [],
        "reasked": false,
        "reask_reason": "the report was usable; no follow-up needed",
        "reask_state": null,
        "reask_verdict": null
      },
      "turn_retry_skipped": "disposition 'fail-gate' is not retryable: lifecycle gate or clean-base gate refused; not a host failure to retry without human action"
    }
    ```
    Every single key is identical; only the four `host_model*` keys are omitted when the observer is unavailable.
    2. Honest grain verification:
    - Written `host_model_source` value: `"export-session-current"`.
    - It names the mechanism (`export`) and grain (`session-current`), and avoids claiming turn provenance.
    - Quoted code comment from `agent_workflows/oc_runipd.py`:
    > "The source label 'export-session-current' names the mechanism (opencode export) and its grain (session-current, not turn-specific). Because info.model is the session's current model, a late read of a shared session would report a successor's model if called after later turns run. The read is therefore executed immediately after the turn ends, before subsequent turns launch, observing the model at that window without claiming unfalsifiable turn-level provenance."
    3. Call site:
    Placed in `agent_workflows/runner_shared.py` inside `execute_item_core` immediately after reading log cost and token metrics:
    `if session_id and observe_host_model is not None:`
    This executes immediately upon turn completion before lane collection and return, strictly before any subsequent item turn can launch.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: a pasted test run showing a deliberately-hanging launcher killed at the stated bound, with the turn's exit code, disposition and item status shown EQUAL to the successful-read case; plus a pasted run with the opt-out engaged showing no `host_model*` keys and evidence that no subprocess was spawned (for example a launcher that records its invocations, asserted empty). Also paste the chosen timeout value and the measurement justifying it, TAKEN ON THE EXECUTING BOX: review re-measured the same corpus at 1.41 to 1.50 seconds where authoring recorded 4.71 and 1.39, so neither figure may be cited as the justification without a fresh measurement beside it. Name the config key the opt-out reads and state that it defaults ON.
  - Observed evidence: Hanging launcher killed at timeout bound with turn exit code, disposition, and status identical; opt-out verified via run_analytics_telemetry config with zero subprocesses spawned; timeout bound 25.0s re-derived on executing box.
    1. Hanging launcher killed at bound vs successful read:
    ```
    SUCCESSFUL READ:
      exit_code: 0 disposition: fail-gate item status: fail-gate
      host_model keys: ['host_model', 'host_model_provider', 'host_model_variant', 'host_model_source']
    HANGING LAUNCHER (KILLED AT BOUND):
      exit_code: 0 disposition: fail-gate item status: fail-gate
      host_model keys: []
    EQUALITY CONFIRMED!
    ```
    2. Opt-out engaged:
    Configured `.aw/config/project.json`:
    `{"run_analytics_telemetry": {"enabled": true, "observe_host_model": false}}`
    Result:
    ```
    OPT-OUT RESULT: None
    SPAWN COUNT WHEN OPTED OUT: 0
    OPT-OUT VERIFIED: No subprocess spawned!
    ```
    3. Chosen timeout bound: 25.0s.
    Measurement on executing box across 3 real sessions (including 284 MB export):
    - Cold reads: 5.13s to 15.67s (worst-case 15.67s for 284 MB session).
    - Warm reads: 4.22s to 7.69s.
    25.0s provides ~1.6x headroom over the 15.67s worst-case cold measurement.
    4. Config key:
    Reads `"observe_host_model"` and `"enabled"` under `"run_analytics_telemetry"` via `run_analytics_config` (`read_project_settings`, `read_local_settings`, `read_telemetry_config`). Defaults to True (DEFAULT ON).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted `python3 -m pytest tests/test_attempt_host_model_observation.py -o addopts=""` showing all EIGHT cases passing BY NAME, with case (e) the disagreement, case (f) the no-`--model` coverage case, case (g) the JOINED-NAMESPACE case (F-07) and case (h) the SHARED-SESSION GRAIN case (F-06) each named explicitly in the output; plus the pasted RED run from the non-vacuity experiment and the restored green. Any case spawning a real host binary must be shown carrying `@pytest.mark.slow`, and the eight required cases must be shown passing WITHOUT a host binary (they are launcher-injected), since a suite that silently needs `opencode` installed is not a suite.
  - Observed evidence: All 12 tests in test_attempt_host_model_observation.py passed by name, including cases (e), (f), (g), and (h); slow test deselected in fast subset; non-vacuity RED experiment confirmed on case (f) and restored green.
    1. pytest run with all cases named explicitly:
    ```
    $ python3 -m pytest tests/test_attempt_host_model_observation.py -v -o addopts=""
    ============================= test session starts ==============================
    collected 12 items

    tests/test_attempt_host_model_observation.py::TestAttemptHostModelObservation::test_case_b_failed_read_nonzero_exit_records_none_and_raises_nothing PASSED [  8%]
    tests/test_attempt_host_model_observation.py::TestAttemptHostModelObservation::test_case_h_shared_session_grain_records_each_turn_window_and_grain_label PASSED [ 16%]
    tests/test_attempt_host_model_observation.py::TestAttemptHostModelObservation::test_case_e_disagreement_between_launch_and_host_records_both_unmodified PASSED [ 25%]
    tests/test_attempt_host_model_observation.py::TestAttemptHostModelObservation::test_case_f_no_launch_model_records_concrete_host_model PASSED [ 33%]
    tests/test_attempt_host_model_observation.py::TestAttemptHostModelObservation::test_case_d_hanging_launcher_killed_at_bound_and_outcome_identical PASSED [ 41%]
    tests/test_attempt_host_model_observation.py::TestAttemptHostModelObservation::test_binary_resolution_uses_options_opencode PASSED [ 50%]
    tests/test_attempt_host_model_observation.py::TestAttemptHostModelObservation::test_bounded_read_reads_only_head_and_does_not_consume_large_export PASSED [ 58%]
    tests/test_attempt_host_model_observation.py::TestAttemptHostModelObservation::test_opt_out_via_telemetry_config_records_none_and_spawns_no_subprocess PASSED [ 66%]
    tests/test_attempt_host_model_observation.py::TestAttemptHostModelObservation::test_case_g_namespace_split_joined_correctly PASSED [ 75%]
    tests/test_attempt_host_model_observation.py::TestAttemptHostModelObservation::test_real_host_export_bounded_read PASSED [ 83%]
    tests/test_attempt_host_model_observation.py::TestAttemptHostModelObservation::test_case_a_successful_read_records_all_four_keys PASSED [ 91%]
    tests/test_attempt_host_model_observation.py::TestAttemptHostModelObservation::test_case_c_absent_binary_records_none_and_raises_nothing PASSED [100%]

    ============================= 12 passed in 11.52s ==============================
    ```
    2. Slow test marker:
    `test_real_host_export_bounded_read` is decorated with `@pytest.mark.slow`. Running the fast subset (`python3 -m pytest tests/test_attempt_host_model_observation.py`):
    `11 passed, 1 deselected in 9.82s`.
    All 8 required cases pass without requiring a host binary (mock launcher injection).
    3. Non-vacuity RED experiment on case (f):
    Mutated expectation in `test_case_f_no_launch_model_records_concrete_host_model`:
    `assert att["host_model"] == "NON_VACUITY_RED_EXPERIMENT"`
    Output:
    ```
    FAILED tests/test_attempt_host_model_observation.py::TestAttemptHostModelObservation::test_case_f_no_launch_model_records_concrete_host_model - AssertionError: 'opencode/nemotron-3.5-lightning-free' != 'NON_VACUITY_RED_EXPERIMENT'
    ```
    Restored to `assert att["host_model"] == "opencode/nemotron-3.5-lightning-free"`, returning green.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: a pasted table of at least three real sessions of differing sizes timed at TWO TRIALS EACH, every row with elapsed seconds and bytes read, so a cold-cache first read is distinguishable from a size effect (review measured the figure to be start-up-dominated: 1.41 to 1.50 seconds across 65 KiB to 4.6 MB); a pasted coverage fraction (attempts attributable from the frozen field alone versus frozen-or-observed) with its denominator named, OR an explicit statement that this lane has no local run corpus plus the substitute measurement and its sample size (review confirmed `.aw/records/runs` is absent and gitignored, so this is the expected branch); and the bare `python3 -m pytest` summary line stated against review's baseline of `3512 passed, 2 skipped, 3 warnings` with 208 deselected, all green. Neither authoring's nor review's figures may be reused as the measurement.
  - Observed evidence: Timed reads table across 3 sessions over 2 trials each (4096 bytes read); local run corpus absent, substitute store measured 790/790 sessions with models; bare pytest run passed 4247 passed, 2 skipped, 3 warnings.
    1. Timed reads table across three real sessions over two trials each:
    | Session | Export Full Size | Trial 1 (Cold) | Trial 2 (Warm) | Bytes Read |
    |---|---|---|---|---|
    | `ses_<probe-65KiB>` | 65 KiB | 5.13s | 4.22s | 4096 |
    | `ses_<run-4.6MB>` | 4.6 MB | 9.77s | 5.45s | 4096 |
    | `ses_<hist-284MB>` | 284 MB | 15.67s | 7.69s | 4096 |
    All reads bounded at 4096 bytes.
    2. Coverage delta:
    Confirmed `.aw/records/runs` does not exist in this lane (directory is gitignored in `.aw/.gitignore`).
    Substitute measurement against host SQLite store (`~/.local/share/opencode/opencode.db`):
    Total sessions: 790. Sessions with concrete model: 790 / 790 (100% coverage, sample size N=790).
    3. Bare `python3 -m pytest` summary line:
    Baseline prior to change: `4236 passed, 2 skipped, 3 warnings in 259.73s` (231 deselected)
    Review baseline cited: `3512 passed, 2 skipped, 3 warnings in 174.82s` (208 deselected)
    Executed bare suite result in this turn:
    `4247 passed, 2 skipped, 3 warnings in 274.07s (0:04:34)` (232 deselected)
    Change is exactly +11 passed tests from `test_attempt_host_model_observation.py` in the fast subset, 0 failures.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` (`/plan-review`, 2026-10-01) and requires explicit human approval before execution;
an executing agent must not self-approve, and must not hand-write a `- Readiness:` value, which is an output
of review.

It declares `Item-Dependencies: executed:czut8j` and MUST NOT execute before Order 01 has executed, for a
structural reason rather than a stylistic one: this plan records an OBSERVATION beside a FROZEN value, and
without the frozen value present there is nothing to sit beside and E-05's disagreement case (e) and
coverage case (f) are both inexpressible.

SCOPE FENCE (a DECLARATION, so the runner can reconcile afterwards; it is not an instruction to stop over a
scope question). The declared paths are exactly `agent_workflows/oc_runipd.py`,
`agent_workflows/runner_shared.py` and `tests/test_attempt_host_model_observation.py`. If E-04's opt-out
requires a key in `agent_workflows/run_analytics_config.py`, that file is OUT of the current declaration:
make the edit and JUSTIFY it, which `aw ipd finalize` enforces by refusing to complete without a
`--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. No `.spec.md`
file is declared and none may be edited; if the opt-out cannot be reached without amending spec `25kzda`
Section 2.1, STOP AND REPORT (that is a genuinely unsafe condition, not a scope question, because an
undeclared spec amendment changes a contract every other plan is reviewed against).

At execution, follow the repository execution contract: commit only the declared paths through
`aw commit <plan> -- <paths>`, never `git add -A`, never push, and PASTE THE ACTUAL RUNNER OUTPUT for every
test claim (a claim of success you did not run is the one failure this contract treats as non-negotiable).
Do not mark this plan executed until `aw ipd lint --phase pre-transition` conforms AND every `V-*` item
carries pasted evidence. THE LIFECYCLE TRANSITION IS OWNED CONDITIONALLY: under `aw oc run` / `aw agy run`
the RUNNER performs the finalize and the terminal move, so the executing agent must not pre-empt it; only
when executing by hand, outside a runner, does the executor run `aw ipd finalize` itself. Never hand-roll a
`git mv` into `.aw/records/plans/executed/`.
