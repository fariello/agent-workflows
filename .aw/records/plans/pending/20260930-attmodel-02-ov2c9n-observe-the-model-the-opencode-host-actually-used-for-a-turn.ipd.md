# IPD: Observe the model the OpenCode host actually used for a turn and record it beside the frozen one

- Date: 2026-09-30
- Kind: child
- Concern: THE MODEL ORDER 01 RECORDS IS WHAT THE DRIVER ASKED FOR, AND ON THE DEFAULT CONFIGURATION IT ASKS FOR NOTHING. When no `--model` is passed and no profile supplies one, `oc_runipd.run_opencode` appends no `--model` flag at all (`if options.get(model_key): argv.extend(["--model", options[model_key]])`), so the host picks; the run-level fallback tier fills that gap by resolving the host's own config at launch (`oc_models.resolve_host_default_model`), which is a CONFIG READING and not an observation of the turn. The gap that leaves is measurable and not hypothetical. The config can be unreadable, in which case `resolve_host_default_model` returns a named reason with an empty model (`no-config-found`, `unparseable-config`, `no-default-model-key`, `malformed-model-value`), and the attempt records nothing. The config can also be EDITED between launch and the turn, or name a model the provider silently substitutes. And backlog `7yz545` states the intended route ("OpenCode: from the session's assistant message modelID") on a premise that is FALSE for the event stream: measured at authoring against opencode 1.18.33, a complete turn's `--format json` stream emitted exactly three events (`step_start`, `text`, `step_finish`) and not one key naming a model, matching `runner_shared`'s own recorded census that all 32333 cost-bearing `step_finish` parts carry `{id, reason, snapshot, messageID, sessionID, type, tokens, cost}` and nothing else.
- Scope: Close that gap with the route that DOES work, measured at authoring rather than assumed: OpenCode's own `opencode export <sessionID>` emits the session's authoritative model as `info.model.id` (plus `providerID` and `variant`), and every attempt already records the `sessionID` needed to ask. Add a best-effort, never-raising reader that asks the host for the model of THIS attempt's session and records it as an OBSERVATION in its own keys (`host_model`, `host_model_provider`, `host_model_variant`, `host_model_source`), distinct from Order 01's frozen `model`. EXCLUDES changing Order 01's field or its precedence, because a request and an observation must stay separately falsifiable. EXCLUDES the Antigravity host, whose stream DOES carry a model on its `init` event and therefore needs a different and cheaper mechanism, deferred with the reason recorded. EXCLUDES making anything GATE on the observation, and excludes any refusal, warning-to-failure, or disposition change: a host that cannot be asked must cost the run nothing.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/runner_shared.py, tests/test_attempt_host_model_observation.py
- Item-Dependencies: executed:czut8j
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Backlog: 7yz545
- Set: attmodel
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ov2c9n

## Workflow history

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `7yz545` as Order 02. THIS PLAN EXISTS BECAUSE THE ITEM'S STATED MECHANISM DOES NOT WORK AND A DIFFERENT ONE DOES, both measured at authoring rather than reasoned about. The item asks for "the session's assistant message modelID"; an executed probe turn showed the `--format json` stream carries no model id anywhere, so a reader over the session log would return nothing forever. But `opencode export <sessionID>` returns the model authoritatively, it was executed against three real sessions of different ages (reporting `opus-5.5`, `opus-5` with `variant: high`, and a 2026-07-era `opus-4.8`), and the value sits in the FIRST 4 KiB of the export, which is what makes the route affordable on a 284 MB session. The plan is deliberately the SECOND order rather than the first: Order 01's frozen field needs no host cooperation and is therefore the reliable floor, and this plan adds the observation on top of a floor that already holds.
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Record what the HOST actually ran, not only what the driver asked for, so an attempt launched with no
`--model` stops being unattributable and a substituted model becomes visible instead of invisible.

The test of success is that a turn launched with NO `--model` flag at all still ends with a concrete model
id on its attempt record, and that a host which cannot be asked leaves the run's outcome byte-identical.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the reader, proven against the real host before it is wired anywhere

- [ ] E-01 RE-MEASURE THE HOST SURFACE THIS PLAN DEPENDS ON, AT EXECUTION, BEFORE WRITING THE READER. Three facts decide the design and all three are host-version-dependent, so each must be re-derived rather than trusted from this plan: (a) that `opencode export <sessionID>` writes JSON to STDOUT with its progress line on STDERR (measured at authoring: stdout parsed as JSON cleanly while stderr held `Exporting session: <id>`); (b) that `info.model.id` is present and names the model, with `info.model.providerID` and an optional `info.model.variant` beside it; (c) that a nonexistent session id exits NONZERO with `Error: Session not found: <id>` rather than emitting an empty success. Record the `opencode --version` under which the measurement was taken, because authoring measured 1.18.33 and the runbook in `tools/ipdrunner/` documents runs under 1.18.21, so the surface is NOT assumed stable across versions. IF ANY OF THE THREE HAS CHANGED, STOP AND REPORT rather than adapting the reader silently: a changed surface means this plan's premise needs re-deciding, which is a human's call.
  - Depends on: none
  - Expected outcome: pasted `opencode --version`; a pasted successful export's first lines showing `info.model`; a pasted failed export showing the nonzero exit and the error line; an explicit statement that all three match this plan's premises or naming which did not.
  - Execution state: pending

- [ ] E-02 WRITE THE READER AS A BOUNDED, STREAMING, NEVER-RAISING FUNCTION THAT READS ONLY THE EXPORT'S HEAD. Put it in `oc_runipd` (this is an OpenCode-specific host interrogation, and `runner_shared` may import neither runner, so the host-specific reader belongs to the host) with a signature taking a session id and returning a small record or `None`. THE BOUNDED READ IS THE WHOLE DESIGN, AND IT IS MEASURED: a real session's export was 284,367,922 bytes and took about 5 seconds to write in full, while `info.model` sat at byte offset 263. Reading the head and terminating the child returned the model in 4.71 seconds for that session and about 1.3 seconds for two smaller ones, reading 4096 bytes in each case. So: spawn with stdout as a pipe, read a small bounded prefix (4 KiB was sufficient for all three sessions measured, including one whose `directory` field is a long path), terminate the child, parse the prefix by LOCATING the model object rather than by `json.loads` on a truncated document, and return. MUST NOT: read the whole export, buffer it in memory, write it to disk, or block without a timeout. MUST swallow every failure (a missing binary, a nonzero exit, an unparseable prefix, a timeout) and return `None`, for the same reason `runner_shared.turn_telemetry` swallows everything: this runs on the path that just finished an agent turn, and an observability read must never turn a completed turn into a failed one. Give it an INJECTABLE launcher parameter so a test can drive it without a host present.
  - Depends on: E-01
  - Expected outcome: the function exists, returns the model record for a real session id (pasted, with the elapsed time and bytes read), returns `None` for a nonexistent one without raising (pasted), and returns `None` when the binary is absent (pasted, via an injected launcher that raises `FileNotFoundError`).
  - Execution state: pending

### Task group 2: wire it at the one seam that already knows the session id

- [ ] E-03 CALL THE READER ONCE PER TURN, AFTER THE TURN ENDS, WHERE THE SESSION ID IS ALREADY IN HAND, AND RECORD IT IN ITS OWN KEYS. `runner_shared.execute_item_core` already extracts the session id from the finished log (via `extract_session_id`, whose result it assigns to the attempt's `session_id` and reconciles against `state["set_sessions"]`) and, immediately after, reads `cost`/`tokens` from the same log through `run_viewer.extract_log_metrics`. That is the seam: the session id exists, the turn is over, and one more best-effort read there adds no branch to any launch path. Record `host_model`, `host_model_provider`, `host_model_variant` and `host_model_source` on the attempt, and record them ONLY when the read succeeded, which is the same conditional discipline `cost`/`tokens` already use (`if att_cost is not None`). DO NOT OVERWRITE Order 01's `model`: the two keys answer different questions and E-05 asserts they can DISAGREE without either being wrong. INJECT THE READER rather than importing it, because `runner_shared` may not import a runner (enforced by `tests/test_runner_shared.py::NoRunnerImportTests`) and because the agy host will pass a different one or none; follow the injection pattern the same function already uses for `spawn_executor`, `driver_begin` and friends, resolving it off `driver_module` with a `None` default so a host that supplies nothing is unaffected.
  - Depends on: E-02
  - Expected outcome: a driven `execute_item_core` whose attempt record carries all four `host_model*` keys after the turn; and a second driven run with the reader injected as unavailable, whose attempt carries NONE of them and is otherwise identical (both pasted).
  - Execution state: pending

- [ ] E-04 BOUND THE COST AND MAKE IT OPTIONAL, BECAUSE A PER-TURN SUBPROCESS IS A REAL COST AND MUST BE REFUSABLE. Two obligations. (a) A HARD TIMEOUT on the read, set low (the measured worst case was 4.71 seconds on the largest session in a 638-session store, so a single-digit-seconds bound is generous) and enforced by killing the child, so a hung host cannot stall a queue; state the chosen bound and the measurement it is based on in the code comment. (b) AN OPT-OUT that does not require editing code: honor the repository's existing configuration surface rather than inventing a flag, since spec `25kzda` Section 2.1 governs the run flag grammar and a NEW CLI flag would require amending it (which this plan's `Scope-Paths` deliberately does not declare). Read the same `run_analytics_config` telemetry switch the per-invocation telemetry already consults, or add a narrowly-scoped key there; whichever is chosen, DEFAULT ON (the field is the point of the Set) and document the off switch. If neither route works without touching the flag grammar, STOP and report rather than adding a flag: an undeclared spec amendment is the failure mode the Set contract exists to prevent.
  - Depends on: E-03
  - Expected outcome: a pasted test showing a deliberately-hanging injected launcher being killed at the bound with the turn's outcome unaffected; and a pasted run with the opt-out engaged, showing NO `host_model*` keys and no subprocess spawned.
  - Execution state: pending

### Task group 3: prove it, including that it cannot hurt a run

- [ ] E-05 PIN THE OBSERVATION BEHAVIORALLY IN A NEW `tests/test_attempt_host_model_observation.py`, WITH THE DISAGREEMENT CASE AS THE CENTRAL ONE. A new file, for the same contention reason Order 01 gave: no pending plan declares this path. Required cases, each an OUTCOME and none of them reading production source: (a) a successful read records all four keys; (b) a failed read (nonzero exit) records none and raises nothing; (c) an absent binary records none and raises nothing; (d) a hanging launcher is killed at the bound and the turn's exit code, disposition and item status are IDENTICAL to a run where the read succeeded; (e) THE DISAGREEMENT CASE: an attempt whose frozen `model` is `provA/requested` and whose host reports `provB/actually-ran` records BOTH, unmodified, so a consumer can see the divergence; (f) a turn launched with NO `--model` at all (frozen `model` empty, source `unrecorded` per Order 01) ends with a concrete `host_model`, which is the coverage this whole Set exists to deliver. Case (f) is the one that must not be omitted or weakened. SHOW ONE CASE RED FIRST and paste both runs.
  - Depends on: E-03, E-04
  - Expected outcome: `tests/test_attempt_host_model_observation.py` with all six cases; pasted `python3 -m pytest tests/test_attempt_host_model_observation.py -o addopts=""` green; plus the pasted RED run proving non-vacuity.
  - Execution state: pending

- [ ] E-06 MEASURE THE REAL COST AND THE REAL COVERAGE ON THIS BOX, AND PUBLISH BOTH NUMBERS. Two measurements, both on whatever corpus the executing machine has. (a) THE PER-TURN COST: time the reader against at least three real sessions of different sizes and report elapsed seconds and bytes read for each, so a reviewer can judge the overhead against a turn that costs minutes. (b) THE COVERAGE DELTA: over the runs available locally, count how many attempts would carry a concrete model from Order 01's frozen field ALONE versus from the frozen field OR this observation, and state both as a fraction. If this lane has no `.aw/records/runs` corpus (it is gitignored and absent from a fresh worktree, which was the case at authoring) say so explicitly and measure (a) against the host's own session store instead, reporting the sample size; do NOT fabricate a corpus number or carry authoring's figures forward as if re-measured. Also run the bare suite and paste the summary line.
  - Depends on: E-05
  - Expected outcome: a pasted table of three timed reads; a pasted coverage fraction with its denominator named, or an explicit statement that no local run corpus exists plus the substitute measurement; a pasted bare `python3 -m pytest` summary line.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The suite is run BARE: `pyproject.toml` `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`. Use `-o addopts=""` for per-test counts from a narrowed run; never `-n0`, never a second `-q`, never `-p no:randomly`.
- `runner_shared` MAY NOT IMPORT EITHER RUNNER (`tests/test_runner_shared.py::NoRunnerImportTests`), which is why this plan's reader lives in `oc_runipd` and is INJECTED into `execute_item_core` through the `driver_module` resolution that function already performs for a dozen other names.
- A NEW CLI FLAG REQUIRES A SPEC AMENDMENT. Spec `25kzda` Section 2.1 declares the run flag grammar and `tests/test_run_flag_surface.py` reads that spec AS A FILE and fails in both directions, so a flag added without amending 2.1 turns the suite red. E-04 is written to avoid a new flag for exactly this reason.
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
key keeps the model id comparable while preserving the distinction.

## Proposed changes (ordered, validatable)

1. Re-measure the three host-surface facts at execution and stop if any changed (E-01).
2. A bounded, streaming, never-raising reader in `oc_runipd` returning the session's model record (E-02).
3. One best-effort call at the post-turn seam in `execute_item_core` where the session id is already in
   hand, recording four `host_model*` keys conditionally, with the reader INJECTED (E-03).
4. A hard timeout and an opt-out that needs no new CLI flag (E-04).
5. A new behavioral test file with six cases including the disagreement and the no-`--model` case (E-05).
6. Published cost and coverage measurements taken on the executing box (E-06).

## Deferred / out of scope (with reason)

- THE ANTIGRAVITY HALF, for the reason in F-04: its model arrives in the stream (`event["init"]["model"]`,
  already parsed and already discarded) so it needs a persist and not an interrogation, and it shares none of
  this plan's cost, timeout or opt-out design. It is a small, separable change and should be filed as its own
  backlog item at execution; Order 00's completion criteria name the residue so the Set does not claim
  coverage it did not deliver on that host.
- THE `audit` VERB, which writes its own `state.json` and its own lean attempt dict without passing through
  `execute_item_core`, so this plan's seam never runs for it. Same reason Order 01 excluded it.
- ANY GATE, REFUSAL OR WARNING-TO-FAILURE ON A DISAGREEMENT. This plan makes a divergence between requested
  and actual VISIBLE; deciding what to do about one is a policy question with a real false-positive cost
  (a provider alias, a version suffix, a normalization difference would all read as divergence), and
  `25kzda` Section 5.3a's "NEVER A GATE" posture for derived observations is the precedent for keeping it
  out.
- READING THE HOST'S SQLITE STORE DIRECTLY. The model is in there (the store's `message.data` JSON carries
  `modelID` per assistant message, confirmed at authoring), and it is REFUSED as a route: it is an
  undocumented internal schema with no compatibility promise, reading another application's live database is
  a correctness and locking hazard, and its path is a machine-local absolute path of exactly the kind the
  leak sanitizer exists to keep out of tracked output. `opencode export` is the host's OWN supported
  interface to the same fact and is used instead.
- BACK-FILLING HISTORY. Same reason as Order 01: `w33lrl` set the precedent, and a session's export is not
  guaranteed to still exist for an old run.

## Scope check

- Over-scope: none. Two production files, one new test file. The `runner_shared` edit is one injected call
  at an existing seam plus the four conditional writes.
- Under-scope: the Antigravity host gains nothing here (named above, with a carrier); the `audit` verb gains
  nothing; a disagreement is recorded but not acted on.

## Required tests / validation

- `tests/test_attempt_host_model_observation.py`, new, six behavioral cases (E-05), one shown red first.
- The three host-surface re-measurements from E-01, pasted with the host version.
- The timed reads and the coverage fraction from E-06, pasted.
- Bare `python3 -m pytest`, summary line pasted.

## Spec / documentation sync

- NO SPEC AMENDMENT, AND E-04 IS SHAPED TO KEEP IT THAT WAY. A new CLI flag would require amending spec
  `25kzda` Section 2.1, whose flag grammar `tests/test_run_flag_surface.py` reads as a file and enforces in
  both directions; E-04 therefore requires the opt-out to use the existing configuration surface and to STOP
  and report if that proves impossible. `Scope-Paths` declares no `.spec.md` file, so the runners' spec-edit
  announcement will correctly report none.
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
- Resolution or deferral rationale: RETURN `None` AND RECORD NOTHING; do NOT widen the read to compensate. A head that lacks the model means the surface changed (the model sat at offset 263 in all three sessions measured, including the 284 MB one), and the correct response to a changed host surface is an honest absence plus E-01's stop-and-report at the next execution, not an unbounded read that would pull hundreds of megabytes through a pipe to find a field that may no longer exist. The frozen field from Order 01 remains present in that case, so an absent observation degrades coverage to Order 01's floor rather than to nothing. This is the same fail-open-to-the-weaker-source discipline `run_viewer.extract_log_metrics` uses when a log carries no cost.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `opencode --version`; the pasted head of a successful export showing `info.model` with its `id` and `providerID`; the pasted nonzero-exit failure for a bogus session id showing the error text; and a written verdict naming each of the three premises as confirmed or changed. A changed premise must be reported, not worked around.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: three pasted invocations of the reader: a real session (showing the returned record, the elapsed seconds and the bytes read, proving the read was BOUNDED and not full), a nonexistent session (returning `None`, no traceback), and an injected launcher raising `FileNotFoundError` (returning `None`, no traceback). The bytes-read figure is required: without it the boundedness claim is unverified.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: two pasted attempt records from driven `execute_item_core` runs, one with the reader available (all four `host_model*` keys present) and one with it unavailable (none of them present, and every other key identical). The second is what proves an unreachable host changes nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: a pasted test run showing a deliberately-hanging launcher killed at the stated bound, with the turn's exit code, disposition and item status shown EQUAL to the successful-read case; plus a pasted run with the opt-out engaged showing no `host_model*` keys and evidence that no subprocess was spawned (for example a launcher that records its invocations, asserted empty). Also paste the chosen timeout value and the measurement justifying it.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `python3 -m pytest tests/test_attempt_host_model_observation.py -o addopts=""` showing all six cases passing BY NAME, with cases (e) the disagreement and (f) the no-`--model` coverage case named explicitly in the output; plus the pasted RED run from the non-vacuity experiment and the restored green. Any case spawning a real host binary must be shown carrying `@pytest.mark.slow`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: a pasted table of at least three timed reader invocations against real sessions of differing sizes, each with elapsed seconds and bytes read; a pasted coverage fraction (attempts attributable from the frozen field alone versus frozen-or-observed) with its denominator named, OR an explicit statement that this lane has no local run corpus plus the substitute measurement and its sample size; and the bare `python3 -m pytest` summary line. Authoring's figures may NOT be reused as the measurement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before execution;
an executing agent must not self-approve, and must not hand-write a `- Readiness:` value, which is an output
of review.

It declares `Item-Dependencies: executed:czut8j` and MUST NOT execute before Order 01 has executed, for a
structural reason rather than a stylistic one: this plan records an OBSERVATION beside a FROZEN value, and
without the frozen value present there is nothing to sit beside and E-05's disagreement case (e) and
coverage case (f) are both inexpressible.

At execution, follow the repository execution contract: commit only the three declared paths through
`aw commit <plan> -- <paths>`, never `git add -A`, never push, and paste the ACTUAL runner output for every
test claim. Do not mark this plan executed until `aw ipd lint --phase pre-transition` conforms AND every
`V-*` item carries pasted evidence.
