# IPD: Cross-host resource telemetry schema, collector, and sampling controls

- Date: 2026-09-08
- Kind: child
- Concern: Capture contemporaneous resource context without leaking host identity or making runner reliability depend on optional probes.
- Scope: Build the telemetry event schema, safe system probes, pseudonymous node identity, lifecycle collector, periodic sampler, overhead limits, and configuration model.
- Scope-Paths: agent_workflows/run_analytics_telemetry.py, agent_workflows/run_analytics_config.py, tests/test_run_analytics_telemetry.py, tests/test_run_analytics_config.py
- Item-Dependencies: executed:bzz5e6
- Status: executed
- Readiness: go-pending-approval
- Set: runanalytics
- Order: 3
- Highest E allocated: 08
- Author: Codex
- Id: lhccjf

## Workflow history
- 2026-09-13 executed (aw oc run): aw oc run self-finalize: lhccjf verified (set runanalytics, attempt 1).
- 2026-09-08 approved (aw set): status set to approved

- 2026-09-08 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. PR-043..PR-052, ALL TEN FIXED, no open findings. The verdict token is stated explicitly because `plan_readiness.newest_verdict` reads the newest review record's first verdict token and falls back to a negative scan when none is present. THE TWO FINDINGS THAT WOULD HAVE PRODUCED WRONG CODE ARE BOTH ABOUT TRUSTING A SHIPPED AUTHORITY THAT DOES NOT DO WHAT THE PLAN ASSUMED. FIRST (PR-043, F-1): the conventions said to "integrate with existing config authorities", but `config.py` enforces a fixed `_ALLOWED_TOP_KEYS` (`:57-65`) and `normalize()` REBUILDS its output from `default_config()`, so an unregistered telemetry key is silently DROPPED on save; the shipped precedent for exactly this case is `review_findings_gate` (`config.py:1082-1145`), whose own comment says it is read from `.aw/config/project.json` and NOT via the XDG config "which drops unknown keys", round-tripping through `project_schema`'s `unknown_fields`. An executor following the authored convention would have written a setting that vanishes. SECOND (PR-044, F-2), and it is the one that matters most for a privacy plan: THE SHIPPED LEAK DETECTOR DOES NOT FAIL ON A HOSTNAME, which is the exact field this child exists to suppress. Measured, `leak_sanitizer.scan_text` over this machine's hostname returns ZERO findings at default settings; the hostname IS derived as a token (`:416`) but lands in the `warn` tier and is promoted to `fail` only when `hostname_fail = true`, which ships FALSE (`.aw/config/local-leaks-allowlist.toml:35`), and even `include_warn=True` on both `build_ruleset` and `scan_text` reports only `warn`. A username and a home path both return `fail` immediately, so the detector's competence on those two would have masked the gap, and a privacy test resting on `aw sanitize` would have PASSED while the hostname shipped. E-04 now requires a DIRECT assertion against `socket.gethostname()`/`getfqdn()`/short label, with the sanitizer demoted to corroboration and required to carry a control run. THIRD, AN 860-LINE IMPLEMENTATION OF NEARLY THIS PROBE SET ALREADY SHIPS HERE AND THE PLAN NEVER MENTIONED IT (PR-045, F-3): `.aw/system/workflows/benchmark/tools/bench_env.py` covers CPU, RAM breakdown, swap, load, GPU, container hints and filesystem, stdlib-only and read-only, with `_run:63` already bounding every informational command by timeout and swallowing failures, and `scrub:652` already redacting hostname/user/paths; OQ-02 now requires the reuse decision be recorded and notes that a direct import is the WORST option since that path is installed workflow content, not a package module. FOURTH, THE CLEANUP ROUTINE IS SPEC-MANDATED SINGULAR AND "lifecycle shutdown" invited a second one (PR-046, F-4): spec `c4gd2h` R5 prohibits divergent per-level cleanup and A9 requires a structural check that exactly one exists, while `oc_runipd.py:1587-1610` records a prior plan being explicitly REFUSED permission to register `signal.signal` handlers because `runstop` Phase 5 owns them and the designs were incompatible; the fence now forbids editing `runner_shutdown.py` (Order 04 declares it), registering a handler, or calling `clean_shutdown`. ALSO FIXED: the three E-items were mechanically sized, as all ten children carry exactly three and the lint reported conforming both before and after, so it cleared nothing (PR-049, F-7, split to EIGHT items across four groups with V-01..V-08 to bijection, `Highest E allocated` 03 -> 08, the same finding sibling `bzz5e6` had); the bounded-sampler pattern exists TWICE already in `StallWatchdog` and `TurnBoundWatch` and neither was cited (PR-047, F-5); `append_jsonl` fsyncs per event, so the promised overhead bound had to be measured against the real writer rather than an assumed buffered append (PR-048, F-6); the gate carried no execution contract at all, the third sibling in a row with that omission (PR-050, F-8); ten escaped backtick pairs rendered as literal backslashes, after Order 01's six and Order 02's four (PR-051, F-9); no baseline was recorded despite requiring a bare suite run, now `2 failed, 5655 passed` with both failures attributed as pre-existing live-corpus couplings (PR-052, F-10); and "No open questions" hid two genuinely unmade decisions, now OQ-01 (config home, resolved by splitting project policy from machine-local override) and OQ-02, both resolved from repository evidence as D-1..D-5.

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): specified telemetry events, privacy minimization, multi-node behavior, degradation, and sampling controls.

## Goal

Provide a runner-neutral telemetry collector that records what hardware and load were present when an invocation actually ran, including node changes between attempts. Telemetry must be useful for performance analysis but non-fatal, bounded, configurable, and privacy-minimized.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

RIGHT-SIZING NOTE, recorded because a passing lint did not clear it. This plan was authored with exactly THREE E-items, and so was every one of the Set's ten children; `aw ipd lint --phase author` reported conforming and the density advisory was silent. A schema, a probe layer, an identity scheme, a background sampler, a config model and an overhead budget are not one concern each in three items. Sibling `bzz5e6`'s review found and split the identical pattern (its PR-031). Split into eight items across four groups; each names ONE deliverable and maps to one V-item.

### Task group 1: Schema and safe probes

- [x] E-01 Define the versioned event ENVELOPE and its strict schema: `start`, `sample`, and `end` records carrying execution/run/IPD/set/attempt/phase/host/model identifiers, wall timestamps, and monotonic offsets. Schema and validation only; no probing, no I/O.
  MAKE THE SCHEMA AN ALLOWLIST, NOT A DENYLIST, and say so in the module docstring. The Findings table below enumerates a forbidden set; that list is a TEST CORPUS, not the implementation strategy. A denylist passes every test written from itself and leaks on the first field nobody imagined. Sibling `bzz5e6` carries the same requirement (its PR-034), so the two must agree: a field is persisted because it appears in an explicit allowlist of reviewed, non-secret, numeric-or-categorical keys, and for no other reason.
  - Depends on: none
  - Expected outcome: typed records that round-trip, REJECT an unknown key rather than dropping it silently, and reject an out-of-vocabulary event kind; a docstring stating the allowlist direction and why.
  - Execution state: performed

- [x] E-02 Implement the resource PROBES behind an injectable adapter interface: CPU count/capacity, memory totals and availability, load, process RSS/CPU, disk capacity, and tool versions. Portable, read-only, and degrading to a structured `unavailable` rather than raising.
  READ `bench_env.py` BEFORE WRITING ANY PROBE. `.aw/system/workflows/benchmark/tools/bench_env.py` is an 860-line, stdlib-only, READ-ONLY implementation of very nearly this probe set (CPU model/cores/flags, RAM total/free/available/cached, swap, load average, GPU, container/VM hints, filesystem/storage), and the plan as authored never mentioned it. It already solves the problems this item will otherwise re-solve: `_run` (`:63`) wraps every informational command with `capture_output`, an explicit `timeout` (default 15s) and `check=False`, returning `""` on ANY failure so capture is best-effort; `_read` (`:79`) does the same for `/proc` and `/sys`. Its docstring also states the safety posture this item needs ("NEVER changes governors, mounts, swap"; "NEVER fabricates a value it could not read - unknown fields are reported as null"). DECIDE AND RECORD one of: import/extract the shared helpers, copy them with attribution, or write fresh with a stated reason. Do NOT silently produce a second, weaker subprocess wrapper; that is the re-fork this repository keeps paying for.
  - Depends on: E-01
  - Expected outcome: an adapter interface with a real implementation and a fake for tests; every probe bounded by a timeout and an output-size cap; a recorded decision about `bench_env.py` reuse with its reason.
  - Execution state: performed

- [x] E-03 Implement the ACCELERATOR probe as its own item, because it is the only probe that shells out to a vendor tool and is the one most likely to hang, flood, or leak. Strict executable allowlist (`nvidia-smi`, `rocm-smi`), explicit timeout, output-size cap, and a parser that persists ONLY numeric and categorical fields.
  NEVER PERSIST RAW STDOUT OR STDERR. A vendor tool's output can carry a hostname, a path, or a serial number, and the whole privacy argument of this child collapses if a parse failure is recorded by storing the text that failed to parse. On `parse_error`, persist the error CODE and the byte length, never the bytes.
  - Depends on: E-02
  - Expected outcome: accelerator inventory and utilization when safely available; `unavailable`/`timeout`/`parse_error` codes otherwise; a test proving no raw tool output reaches the JSONL on any failure path.
  - Execution state: performed

### Task group 2: Identity and lifecycle

- [x] E-04 Implement the pseudonymous NODE IDENTITY: a locally stable keyed pseudonym derived from machine identity, persisting neither the input nor the raw hostname, with the correlation scope and rotation behavior documented.
  DO NOT ASSUME THE SHIPPED LEAK DETECTOR WILL CATCH A HOSTNAME REGRESSION. Measured 2026-09-08: `leak_sanitizer.scan_text` over this machine's hostname returns NOTHING at default settings. The hostname IS derived as a token (`leak_sanitizer.py:416`) but lands in the `warn` tier, and `_HOSTNAME_REASONS` (`:438`) is promoted to `fail` only when the allowlist sets `hostname_fail = true`, which ships FALSE by default (`.aw/config/local-leaks-allowlist.toml:35`, off "so a shared CI-runner hostname does not fail every build"). Even with `include_warn=True` passed to BOTH `build_ruleset` and `scan_text` it reports only `warn`. By contrast a username and a home path both return `fail` immediately. So `aw sanitize` is a necessary but INSUFFICIENT oracle for exactly the field this item exists to suppress, and a test relying on it would pass while the hostname shipped. Write a DIRECT assertion: the raw hostname string must not appear anywhere in the produced JSONL, asserted against `socket.gethostname()` and `socket.getfqdn()` plus its short label.
  - Depends on: E-01
  - Expected outcome: same node yields a stable pseudonym, a different node a different one; neither the raw hostname nor the derivation input is persisted; a direct hostname-absence assertion that does not depend on the sanitizer's tier configuration.
  - Execution state: performed

- [x] E-05 Implement the COLLECTOR lifecycle: a context-managed object emitting exactly one `start` and a best-effort `end` per execution id, with monotonic timing and idempotent close.
  USE THE EXISTING JSONL AND ATOMIC-WRITE AUTHORITIES, do not hand-roll them: `runner_shared.append_jsonl` (`:458`) and `runner_shared.atomic_write_json` (`:436`) already exist and are used throughout both runners. NOTE THE OVERHEAD PROPERTY THAT MATTERS HERE: `append_jsonl` calls `os.fsync` on EVERY event. That is correct for low-volume run events and is a real per-sample cost for a periodic sampler, so E-07's budget must be measured against the actual writer rather than an assumed buffered append. If the fsync-per-sample cost proves unacceptable, record the finding and the chosen mitigation; do NOT quietly add a second, unsynced writer.
  - Depends on: E-01, E-02
  - Expected outcome: one well-formed JSONL stream per execution; a second `close()` is a no-op; durations derive from a monotonic clock and are never negative.
  - Execution state: performed

- [x] E-06 Implement the periodic SAMPLER as a bounded background thread that stops on every normal, exception and signal-assisted cleanup path, and SKIPS an overlapping sample instead of accumulating work.
  COPY THE SHIPPED PATTERN RATHER THAN INVENTING ONE. This package already contains this exact shape TWICE: `oc_runipd.StallWatchdog` (`:655-714`) and `lane_containment.TurnBoundWatch` (`:1276-1348`). Both use a `threading.Event` for stop, a `daemon=True` thread started in `__enter__`, a `_stop.wait(interval)` loop rather than `sleep`, and `__exit__` setting the event then `join(timeout=1.0)`. Both also clamp the check interval against the bound (`max(0.05, timeout/4.0)`). Reuse that structure so a telemetry thread cannot outlive its run or block shutdown.
  KNOW THE SHUTDOWN CONTRACT YOU MUST NOT FORK. `runner_shutdown.clean_shutdown` is the ONE cleanup routine, mandated by spec `c4gd2h` R5 ("ONE implementation shared by all four levels and by crash recovery. Divergent per-level cleanup is prohibited") with A9 requiring a structural check that exactly one exists; the spec is `- Status: implementing`. This child must therefore expose a small, callable stop API and MUST NOT register a signal handler, add a cleanup path, or call `clean_shutdown` itself. Order 04 (`5f2h8i`) owns the wiring and declares `runner_shutdown.py` in its `Scope-Paths`; this child does not and must not edit it.
  - Depends on: E-05
  - Expected outcome: a sampler whose thread is provably stopped after `__exit__`, on an exception, and on a signal-assisted teardown; an overlapping tick is SKIPPED and counted, never queued; no signal handler and no second cleanup path added.
  - Execution state: performed

### Task group 3: Configuration

- [x] E-07 Implement the validated telemetry CONFIGURATION model: basic `start`/`end` telemetry on by default, periodic sampling opt-in with a bounded interval, and a way to disable telemetry entirely.
  THE CONFIG HOME IS A DECIDED QUESTION WITH A SHIPPED PRECEDENT, AND THE OBVIOUS CHOICE IS WRONG. The conventions section said to "integrate with existing config authorities"; measured, the XDG user config (`config.py`) enforces a FIXED allowlist (`_ALLOWED_TOP_KEYS`, `:57-65`) and `normalize()` REBUILDS the output from `default_config()`, so an unregistered key is silently DROPPED on the next save. The precedent for exactly this situation is `review_findings_gate` (`config.py:1082-1145`), whose comment states it is recorded in the committed portable policy `.aw/config/project.json` "and read HERE and not via the XDG user config (which drops unknown keys)", is DELIBERATELY not registered in `CONFIG_SCHEMA` because `project_schema.parse_portable_policy` preserves unknown keys in `unknown_fields` (`project_schema.py:585`, `:624`) and writes them back on serialization. Follow that precedent: read the telemetry settings with a small never-raising reader, and pick the default direction deliberately. `review_findings_gate` is fail-CLOSED (absent means active) because it is a safety gate; telemetry is the opposite kind of thing, so an absent key must mean the documented default and never an error.
  RESOLVE PER-PROJECT VERSUS PER-MACHINE EXPLICITLY (OQ-01). `.aw/config/project.json` is COMMITTED and `.aw/config/local.json` is gitignored; a telemetry preference is arguably machine-local, and its interval is arguably a project policy. State which key lives where and why.
  - Depends on: E-01
  - Expected outcome: a never-raising reader with documented defaults; an absent, malformed or unknown-valued key lands on the documented default rather than raising; the interval bound enforced in ONE place; the chosen config home recorded with the `review_findings_gate` precedent cited.
  - Execution state: performed

### Task group 4: Proof

- [x] E-08 Prove BOUNDED OVERHEAD and PRIVACY behavior across supported and degraded systems, with injected clocks and probes so no test spends real time or touches a real device.
  Cover, as distinct cases: Linux with procfs; procfs absent; the GPU tool absent; malformed tool output; a probe that TIMES OUT; a probe slower than the sampling interval (which must skip, not accumulate); impossible values; and clock skew. Measure the per-event and per-sample cost against the REAL writer (`append_jsonl`, which fsyncs per event) and state the measured figure rather than an assumed one.
  - Depends on: E-03, E-04, E-06, E-07
  - Expected outcome: every degraded case yields a structured warning and a completed run; a measured overhead figure against the real writer; no test performs a real subprocess call, real sleep, or network access.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE XDG USER CONFIG SILENTLY DROPS AN UNREGISTERED KEY, so "integrate with the existing config authority" is a trap if read as "put it in `config.py`". `config.py` enforces a fixed `_ALLOWED_TOP_KEYS` (`:57-65`) and `normalize()` REBUILDS its output from `default_config()`, so an unknown top-level key does not round-trip. The shipped precedent for a setting that must NOT go there is `review_findings_gate` (`config.py:1082-1145`): its own comment says it is recorded in `.aw/config/project.json` "and read HERE and not via the XDG user config (which drops unknown keys)", it is deliberately absent from `CONFIG_SCHEMA`, and it round-trips because `project_schema.parse_portable_policy` preserves unknown keys in `unknown_fields` (`project_schema.py:585`, `:624`) and re-serializes them. Follow that precedent, and note the DEFAULT DIRECTION differs: that key is fail-CLOSED because it is a safety gate, whereas an absent telemetry key must mean the documented default.
- `.aw/config/project.json` IS COMMITTED AND `.aw/config/local.json` IS GITIGNORED. That distinction decides where a telemetry preference belongs and is OQ-01, not an implementation detail.
- THE SHUTDOWN ROUTINE IS SPEC-GOVERNED AND MUST NOT BE FORKED. `runner_shutdown.clean_shutdown` is the ONE cleanup implementation, required by spec `c4gd2h` R5 ("Divergent per-level cleanup is prohibited") with A9 demanding a structural check that exactly one exists; the spec reads `- Status: implementing`. `oc_runipd.py:1587-1610` records a prior plan being told NOT to register `signal.signal` handlers because `runstop` Phase 5 (`71vjbn`) owns SIGINT/SIGTERM registration, and that the two designs were incompatible rather than merely duplicated. So this collector exposes a callable stop API and NOTHING else: no signal handler, no cleanup path, no `clean_shutdown` call. Order 04 (`5f2h8i`) owns the wiring and is the plan that declares `runner_shutdown.py` in its `Scope-Paths`; this child does not and must not edit it.
- THE BOUNDED BACKGROUND-THREAD PATTERN ALREADY EXISTS TWICE, so the sampler must not invent a third shape: `oc_runipd.StallWatchdog` (`:655-714`) and `lane_containment.TurnBoundWatch` (`:1276-1348`). Both use a `threading.Event` stop flag, a `daemon=True` thread started in `__enter__`, a `_stop.wait(interval)` loop rather than `sleep`, `__exit__` setting the event then `join(timeout=1.0)`, and an interval clamped against the bound. `TurnBoundWatch` additionally reaches teardown only through the caller-supplied reaper, with the comment "never a bare kill, never a second reaper".
- THE JSONL AND ATOMIC-WRITE AUTHORITIES EXIST: `runner_shared.append_jsonl` (`:458`) and `atomic_write_json` (`:436`). `append_jsonl` calls `os.fsync` on EVERY event, which is correct for low-volume run events and is a per-sample cost a periodic sampler must measure rather than assume away.
- AN 860-LINE READ-ONLY PROBE IMPLEMENTATION ALREADY SHIPS IN THIS REPOSITORY: `.aw/system/workflows/benchmark/tools/bench_env.py`, covering CPU, RAM breakdown, swap, load, GPU, container/VM hints and filesystem, stdlib-only, with a `_run` helper (`:63`) that bounds every informational command by timeout and returns `""` on any failure, a `_read` (`:79`) for `/proc` and `/sys`, and a `scrub()` (`:652`) that replaces hostname/user/paths with placeholders for sharing. Its docstring states the same posture this child needs, including "NEVER fabricates a value it could not read". Reuse, copy with attribution, or justify writing fresh; do not produce a second weaker subprocess wrapper by accident.
- The runners stream child output and have established signal/shutdown paths. The collector must expose a small lifecycle API for Order 04 to call without owning process policy.
- Hardware may vary by cluster node and by resumed attempt, so telemetry is per invocation, not a one-time installation inventory.
- Arbitrary environment capture is prohibited. Only explicitly reviewed non-secret categorical values may be allowlisted, and environment values must never be a fallback for host identity.
- Optional command probes require strict executable allowlists, timeouts, output-size caps, and parsers that persist only numeric/categorical fields, never raw stdout/stderr.

## Findings

### Required decisions (authored)

| Topic | Required decision |
|---|---|
| Identity | Generate a locally stable keyed pseudonym from machine identity where available; persist neither the input nor raw hostname. Document correlation scope and rotation. |
| Sampling default | Capture start/end basic snapshots by default because they are low-volume and necessary to interpret run timing. Ask separately before enabling periodic samples. |
| Model price | Telemetry records provider/model/variant and runner/tool versions, not a guessed price. Pricing is joined by Order 06. |
| Probe failure | Record structured `unavailable`, `timeout`, or `parse_error` codes and continue the run. |
| Overhead | Define a measurable maximum probe time and event rate; skip overlapping samples instead of accumulating work. |

The categories this child must never persist (arbitrary environment values, raw stdout/stderr, file contents, network addresses, absolute paths, raw hostname) are a TEST CORPUS for E-08, NOT the implementation strategy. Implement the ALLOWLIST of E-01. If you find yourself filtering known-bad keys rather than passing known-good ones, stop: that is the failure mode, not the fix.

### Findings (review, measured 2026-09-08 at HEAD `05422cd9`)

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `config.py:57-65`, `:1082-1145`; `project_schema.py:585`, `:624` | **"INTEGRATE WITH EXISTING CONFIG AUTHORITIES" POINTS AT AN AUTHORITY THAT WOULD SILENTLY DISCARD THIS CONFIG.** The XDG user config enforces a fixed `_ALLOWED_TOP_KEYS` and `normalize()` rebuilds its output from `default_config()`, so an unregistered telemetry key does not survive a save. The correct precedent is `review_findings_gate`, whose own comment says it is read from `.aw/config/project.json` and NOT via the XDG config "which drops unknown keys", and which round-trips through `unknown_fields`. An executor following the authored convention literally would have written a setting that vanishes. | source read; `_ALLOWED_TOP_KEYS` and the `review_findings_gate` comment quoted |
| F-2 | HIGH | `leak_sanitizer.py:416`, `:438`, `:485-491`; `.aw/config/local-leaks-allowlist.toml:35` | **THE SHIPPED LEAK DETECTOR DOES NOT FAIL ON A HOSTNAME, WHICH IS THE EXACT FIELD THIS CHILD EXISTS TO SUPPRESS.** Measured: `scan_text` over this machine's hostname returns ZERO findings at default settings. The hostname IS derived as a token but lands in the `warn` tier, promoted to `fail` only when `hostname_fail = true`, which ships FALSE. Even with `include_warn=True` on both `build_ruleset` and `scan_text` it reports only `warn`. A username and a home path both return `fail` immediately, so the detector's apparent competence on those two would have masked the gap. A privacy test resting on `aw sanitize` would pass while the hostname shipped. | `scan_text` called on `gethostname()` (0 findings), on username (`handle`/`fail`), on a home path (`home-path`+`handle`/`fail`); warn-tier match confirmed as `derived:<token>` at `warn` |
| F-3 | HIGH | `.aw/system/workflows/benchmark/tools/bench_env.py` (860 lines; `_run:63`, `_read:79`, `scrub:652`) | **AN 860-LINE, READ-ONLY, STDLIB-ONLY IMPLEMENTATION OF NEARLY THIS EXACT PROBE SET ALREADY SHIPS IN THIS REPOSITORY AND THE PLAN NEVER MENTIONED IT.** It covers CPU, RAM breakdown, swap, load, GPU, container/VM hints and filesystem; `_run` already bounds every informational command with a timeout and swallows all failures to `""`; `scrub()` already redacts hostname/user/paths for sharing. Writing fresh probes without deciding about this is how a second, weaker subprocess wrapper enters the package | file read; helper signatures and docstring quoted |
| F-4 | HIGH | spec `c4gd2h` R5/A9 (`- Status: implementing`); `runner_shutdown.py:1-31`, `clean_shutdown:451`; `oc_runipd.py:1587-1610` | **THE CLEANUP ROUTINE IS SPEC-MANDATED TO BE SINGULAR AND THE PLAN'S "LIFECYCLE SHUTDOWN" WORDING INVITED A SECOND ONE.** R5 prohibits divergent per-level cleanup and A9 requires a structural check that exactly one implementation exists. `oc_runipd.py:1587-1610` records a prior plan being explicitly refused permission to register `signal.signal` handlers because `runstop` Phase 5 owns them and the designs were incompatible. This child must expose a stop API only; Order 04 owns the wiring and is the plan that declares `runner_shutdown.py` | spec requirements read; the refusal comment read; 7 `clean_shutdown` call sites counted |
| F-5 | MEDIUM | `oc_runipd.py:655-714`; `lane_containment.py:1276-1348` | The bounded background-sampler pattern (Event stop flag, daemon thread in `__enter__`, `_stop.wait(interval)` not `sleep`, `__exit__` join with timeout, interval clamped against the bound) exists TWICE already. The plan specified the REQUIREMENT ("samples stop on every cleanup path") without pointing at either, so a third shape would likely have been invented | both classes read |
| F-6 | MEDIUM | `runner_shared.py:458` | `append_jsonl` calls `os.fsync` on EVERY event. Correct for low-volume run events; a real per-sample cost for a periodic sampler. The plan promised a measurable overhead bound without naming the writer whose cost dominates it, so the budget could have been measured against an assumed buffered append | source read |
| F-7 | MEDIUM | plan's E-01..E-03 as authored; all ten `runanalytics` children | **THE THREE E-ITEMS WERE MECHANICALLY SIZED.** E-02-as-authored named five deliverables (identity, snapshots, sampling, shutdown, failure isolation) across unrelated test surfaces. Every one of the Set's ten children carries exactly three items, which is a template rather than a per-child judgement; the count-based lint reported conforming both before and after the split, so a passing lint cleared nothing. Sibling `bzz5e6` had the identical finding (its PR-031) | `grep -c` over all ten children -> 3 each; lint conforming before and after |
| F-8 | MEDIUM | plan gate as authored | The gate carried two sentences and NO execution contract: no scope fence, no path-scoped-commit / never-push rule, no paste-actual-output honesty rule, no lifecycle-move instruction, no statement of the dependency posture. Siblings `xbwq8n` and `bzz5e6` each had the same omission, so it is a Set-wide authoring pattern | plan read; sibling review records read |
| F-9 | LOW | plan source lines 29, 57, 86 (pre-fix) | Ten escaped backtick pairs rendered as literal backslashes instead of code spans. Order 01's review found six, Order 02's found four, so the same shared authoring pipeline produced all three | `grep -n` before the fix |
| F-10 | LOW | suite baseline | Bare `python3 -m pytest` at `05422cd9`: `2 failed, 5655 passed, 3 skipped, 2 xfailed`. Both failures (`test_plan_readiness::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`, `test_orchestrator_retirement::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`) are pinned to the live mutable plan corpus and are pre-existing, not caused here. The plan required a bare suite run but recorded no baseline, so an executor could not tell them from its own | bare run at review |

## Proposed changes (ordered, validatable)

1. E-01 defines the strict, allowlist-shaped event envelope (schema only, no I/O).
2. E-02 adds injectable probe adapters, after deciding what `bench_env.py` gives us for free; E-03 isolates the accelerator probe, the only one that shells out to a vendor tool.
3. E-04 establishes the node pseudonym, with a DIRECT hostname-absence assertion because the shipped sanitizer does not fail on a hostname.
4. E-05 builds the context-managed collector on the existing `append_jsonl` writer; E-06 adds the bounded sampler by copying the shipped watchdog shape, exposing a stop API and forking no cleanup path.
5. E-07 adds the configuration model in the config home the `review_findings_gate` precedent identifies.
6. E-08 proves overhead and privacy against the real writer, with every degraded case covered and no real subprocess, sleep, or network in any test.

## Deferred / out of scope (with reason)

- Hooking collectors into OpenCode and Agy lifecycle code is Order 04 (`5f2h8i`), which declares `oc_runipd.py`, `agy_runipd.py` and `runner_shutdown.py` in its `Scope-Paths` and owns the `25kzda` spec amendment. Verified those declarations rather than assumed them.
- Analysis of resource correlation is Order 06 (`aflsz3`, taxonomy/pricing/statistics/findings). Ingestion of what this child writes is Order 05 (`8hald1`). Both were verified against their front matter.
- Detailed process tracing, file contents, network addresses, and arbitrary environment collection are excluded for privacy and overhead.
- Continuous monitoring outside active runner invocations is not authorized.

## Scope check

- Over-scope: no runner orchestration, run parsing, report UI, submission, or installer prompting. Specifically, and each for a measured reason: do NOT edit `runner_shutdown.py` (spec `c4gd2h` R5/A9 makes cleanup singular and Order 04 declares that file); do NOT register a `signal.signal` handler (`runstop` Phase 5 `71vjbn` owns SIGINT/SIGTERM, and `oc_runipd.py:1587-1610` records a prior plan being refused exactly this); do NOT add a second JSONL or atomic writer beside `runner_shared.append_jsonl` / `atomic_write_json`; do NOT add a second leak sanitizer (`local_leaks` is deliberately a thin re-export of one engine); do NOT register the telemetry key in `config.py`'s `CONFIG_SCHEMA` (the `review_findings_gate` precedent is deliberately absent from it); and do NOT edit either declared spec file, since none is in this child's `Scope-Paths`.
- An out-of-scope edit is not forbidden outright, it must be JUSTIFIED: `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. Declare rather than improvise.
- Under-scope: includes schema, probes, sampler, config, identity, cleanup, warning codes, performance budget, and tests required for safe integration. The `bench_env.py` reuse decision (E-02), the accelerator probe's raw-output prohibition (E-03), the direct hostname assertion (E-04) and the config-home decision (E-07) were under-scope before review.

## Required tests / validation

Baseline, measured bare at HEAD `05422cd9`: `2 failed, 5655 passed, 3 skipped, 2 xfailed`. Both failures (`test_plan_readiness::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today` and `test_orchestrator_retirement::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`) are pinned to the live mutable plan corpus and are PRE-EXISTING. Re-measure in the executing worktree and compare failing NODE IDS; the acceptance criterion is an empty delta against your own baseline, never a total.

NO TEST MAY REACH THE NETWORK, A REAL DEVICE, A REAL SUBPROCESS, OR A REAL SLEEP. Assert that by construction with stubs that RAISE if invoked unexpectedly, not by hoping. A telemetry test that shells out to `nvidia-smi` is not a test, it is a machine-dependent coin flip.

DO NOT COMMIT A CANARY AS A LITERAL. E-08 seeds forbidden-shaped values into fixtures; a committed corpus of real-shaped secrets is a leak that ships. Generate them at test time or assemble them from fragments, as the detection engine does with its own patterns. Sibling `bzz5e6`'s review demonstrated this accidentally: pasting a measured detector result with its literal inputs made `aw sanitize` FAIL on the plan file itself.

- Event-schema round trips and rejection of unknown/private fields.
- Start/end ordering, monotonic durations, sample cadence, no overlap, idempotent close, exception and signal-assisted cleanup.
- Multi-node pseudonym distinction and same-node local stability without persisting identity inputs.
- Missing tools/files/permissions, timeouts, malformed output, impossible values, and clock skew.
- Secret/path/hostname canary scan over JSONL and logs, run as `aw sanitize --agent` WITH a control run proving the same invocation flags a seeded username or home path (a clean report and a detector that was not looking are otherwise indistinguishable), PLUS a direct hostname-absence assertion, because F-2 measured that the sanitizer does not fail on a hostname at default settings. The direct assertion is the load-bearing one; the sanitizer is the corroborating one.
- Scan the TEST tree as well as the produced telemetry, since the fixtures carry the seeded canaries.
- Measured test proving configured sampling does not exceed the documented event rate or block runner execution beyond the probe budget.
- Bare `python3 -m pytest` and `git diff --check`.

## Spec / documentation sync

Order 04 must amend the controlling runner contract if it defines the run artifact inventory. That spec is `25kzda`, which resolves to `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (`- Id: 25kzda`, `- Status: approved`); the filename predates the id6-in-filename convention, so the id is findable only by grepping `- Id:`. Order 04 (`5f2h8i`) ALREADY declares that path in its `Scope-Paths`, so the amendment is owned and announced there, not here.

THIS CHILD DECLARES NO SPEC FILE AND MUST EDIT NONE. Two approved or implementing specs bear on it and both are IMMUTABLE from here: `25kzda` (approved, Order 04's to amend) and `c4gd2h` (`- Status: implementing`, whose R5/A9 make the cleanup routine singular). If execution concludes that either genuinely must change, that is a STOP-and-raise, not a unilateral edit: editing an approved spec would invalidate its human attestation.

Order 10 documents configuration, privacy limits, platform coverage, and overhead. Do not market the telemetry as anonymous. The honest wording is PSEUDONYMOUS with a stated correlation scope, and F-2 is the reason to be precise: the repository's own leak detector does not flag a hostname at default settings, so "our sanitizer reports clean" is not a privacy claim and must never be documented as one.

## Open questions

"No open questions" was not accurate: two decisions the plan REQUIRED were specified nowhere, and both are answerable from repository evidence rather than by asking, so both are recorded resolved with their basis. This mirrors sibling `bzz5e6`, whose review found the same claim hiding two unmade decisions (its PR-035).

### OQ-01: Does the telemetry setting live in the committed project policy or the gitignored machine-local file?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW from repository evidence. NOT the XDG user config: `config.py` enforces `_ALLOWED_TOP_KEYS` (`:57-65`) and `normalize()` rebuilds from `default_config()`, so an unregistered key is silently dropped on save; the `review_findings_gate` precedent (`config.py:1082-1145`) exists for exactly this reason and says so in its own comment. SPLIT BY NATURE OF THE SETTING: the sampling INTERVAL and the enabled/disabled POLICY are project decisions a team should share and review, so they belong in the committed `.aw/config/project.json` alongside `review_findings_gate`, round-tripping through `project_schema`'s `unknown_fields`. A per-machine OPT-OUT (an operator on a constrained box declining sampling) belongs in the gitignored `.aw/config/local.json`, whose `runtime_overrides` map already exists for machine-specific deviation. The precedence is local-overrides-project, and the reader must never raise. One divergence from the precedent is deliberate: `review_findings_gate` is fail-CLOSED because it is a safety gate, while an absent telemetry key must mean the documented default, since failing closed on a missing telemetry setting would break runs to protect nothing.

### OQ-02: Is `bench_env.py` imported, extracted, copied, or ignored?

- Blocking: no
- Status: resolved
- Owner: executor (record the choice; the DIRECTION is decided here)
- Resolution or deferral rationale: RESOLVED AT REVIEW as "do not ignore it, and record which of the other three you chose". The file is real, read-only, stdlib-only and 860 lines, and it already solves the bounded-subprocess and graceful-degradation problems this child would otherwise re-solve (`_run:63`, `_read:79`, `scrub:652`). Importing it directly is the LEAST attractive option and is noted so it is not chosen by default: it lives under `.aw/system/workflows/benchmark/tools/`, which is INSTALLED WORKFLOW CONTENT copied into target repositories, not an importable package module, so a runtime import from `agent_workflows/` would couple the shipped package to a file the installer manages. Extracting the shared helpers into the package, or copying them with attribution, are both defensible. Writing fresh is acceptable ONLY with a stated reason. The executor records the choice in V-02; what is NOT acceptable is producing a second, weaker subprocess wrapper without having considered this one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a round-trip for each of the three event kinds; paste the REJECTION of an unknown key and of an out-of-vocabulary event kind, showing an error rather than a silent drop. Paste the docstring passage stating the allowlist direction. Include a mutation check: make the schema ignore an unknown key instead of rejecting it, show a test fails, revert.
  - Observed evidence: PASS. All three event kinds round-trip byte-stably; an unknown key and an out-of-vocabulary `event_kind` each RAISE `SchemaRefusal` rather than dropping; the allowlist-direction docstring is quoted; and the mutation check found a SECOND independent refusal (a key with no validation rule is refused even with the key allowlist disabled), so defeating the boundary takes disabling both. Detail below.

    ROUND TRIP, all three kinds (each re-validates byte-identically after a JSON round trip):

    ```text
    start   validated={"event_kind": "start", "execution_id": "exec-01", "monotonic_offset_seconds": 0.0, "schema_version": 1, "sequence": 1, "wall_timestamp": "2026-09-13T20:00:00Z"}
            round-trip stable: True
    sample  validated={"event_kind": "sample", ...}   round-trip stable: True
    end     validated={"event_kind": "end", ...}      round-trip stable: True
    ```

    REJECTION of an unknown key, an ERROR and not a silent drop:

    ```text
    raised: SchemaRefusal
    message: telemetry schema refusal: 'hostname' is not in the event allowlist, so it is REFUSED
             rather than dropped (the boundary is an allowlist: add the key deliberately, with a test)
    ```

    REJECTION of an out-of-vocabulary event kind:

    ```text
    'heartbeat'  -> telemetry schema refusal: 'event_kind' must be one of ['end', 'sample', 'start'], got 'heartbeat' (the vocabulary is CLOSED)
    'START'      -> ... got 'START' (the vocabulary is CLOSED)
    ''           -> ... got '' (the vocabulary is CLOSED)
    ```

    DOCSTRING passage stating the allowlist DIRECTION (`run_analytics_telemetry.__doc__`):

    ```text
    THE SCHEMA IS AN ALLOWLIST, AND THAT DIRECTION IS THE WHOLE DESIGN. A field is persisted because
    it appears in :data:`ALLOWED_FIELDS` (or an explicitly named nested allowlist), and for NO other
    reason. This is stated first because the plan governing this module enumerates a forbidden set
    (arbitrary environment values, raw stdout/stderr, file contents, network addresses, absolute
    paths, raw hostname) and that list is a TEST CORPUS, never the implementation strategy.
    ```

    MUTATION CHECK, and it produced a finding worth recording. Disabling the key allowlist
    (`_refuse_unknown` stubbed to a no-op) did NOT admit the field, because a SECOND independent
    check refuses a key for which no validation rule exists:

    ```text
    telemetry schema refusal: 'hostname' has no validation rule, which is itself a refusal
    ```

    Only with BOTH checks disabled (`_validate_scalar` also stubbed to pass values through) does the
    forbidden field survive, i.e. get silently DROPPED-then-passed rather than refused; the test
    asserts that mutant behavior explicitly and then reverts, after which the refusal names the
    allowlist again. That is `SchemaMutationTests::test_dropping_instead_of_refusing_breaks_the_boundary`,
    passing. Full transcript: `.aw/state/lane-submissions/run-20260913T195954Z-867725/01-lhccjf/attempt-1/evidence/v01-schema-evidence.txt`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the adapter interface and its fake; paste a probe result for each field family on this machine and the `unavailable` result with the same probe denied. Paste the recorded `bench_env.py` decision (reuse, copy-with-attribution, or fresh) WITH its reason. Paste proof every command probe carries a timeout and an output-size cap.
  - Observed evidence: PASS. Every field family probed `ok` on this machine and `unavailable`/`parse_error` when denied; the `bench_env.py` decision is WRITE-FRESH-WITH-ATTRIBUTION-AND-NO-IMPORT, recorded in the module docstring with its placement reason; and the one command probe was observed carrying `timeout=0.5`, `check=False`, a 16-byte truncation of 4096 offered bytes, and no stderr. Detail below.

    THE INTERFACE is `ResourceProbeAdapter` (`cpu`/`memory`/`load`/`process`/`disk`/`tool_versions`/
    `accelerators`, plus a composing `resources()`), with two implementations:
    `SystemResourceProbeAdapter` (real, read-only) and `FakeResourceProbeAdapter` (tests; every
    outcome caller-supplied, call-counting, and an injected sleeper so a "slow probe" costs no real
    time).

    EVERY FIELD FAMILY probed on this machine:

    ```text
    cpu            reason=ok   value={'cpu_logical_count': 12, 'cpu_usable_count': 12, 'cpu_architecture': 'x86_64', 'platform_system': 'Linux', 'platform_release_major': '6'}
    memory         reason=ok   value={'memory_total_bytes': 134985220096, 'memory_available_bytes': 121202679808, 'swap_total_bytes': 210453393408, 'swap_free_bytes': 210453393408}
    load           reason=ok   value={'load_average_1m': 1.14, 'load_average_5m': 2.26, 'load_average_15m': 7.34}
    process        reason=ok   value={'process_rss_bytes': 22249472, 'process_cpu_seconds': 0.09}
    tool_versions  reason=ok   value={'python': '3.14.6', 'agent_workflows': '1.3.0rc2.dev2631+g43d6b4bd'}
    disk           reason=ok   value={'disk_total_bytes': 502392688640, 'disk_free_bytes': 163820957696}
    ```

    THE SAME PROBES DENIED (structured reason, no exception):

    ```text
    memory (procfs absent): ProbeOutcome(reason='unavailable', value=None, detail_bytes=0)
    disk (nonexistent):     ProbeOutcome(reason='unavailable', value=None, detail_bytes=0)
    memory (malformed):     ProbeOutcome(reason='parse_error', value=None, detail_bytes=27)
    ```

    THE `bench_env.py` DECISION (OQ-02), recorded in the module docstring: WRITE FRESH, MODELED ON
    IT, WITH ATTRIBUTION, AND IMPORT NOTHING. The REASON is placement, not quality: that file lives
    under `.aw/system/workflows/benchmark/tools/`, which is INSTALLED WORKFLOW CONTENT copied into
    target repositories by the installer and is not an importable package module, so a runtime
    import from `agent_workflows/` would couple the shipped package to a file the installer manages
    and would break in any target repo that has not installed the benchmark workflow. Extracting it
    into the package was rejected as outside this plan's declared `Scope-Paths`. What is borrowed is
    the SHAPE (bounded-subprocess helper, total `/proc` reader, never fabricate an unread value);
    what is deliberately NOT copied is `_run`'s `""`-on-failure return, because an empty string is
    indistinguishable from a successful empty read, so this module returns a typed `ProbeOutcome`
    with an explicit reason code instead. Asserted by
    `ProbeAdapterTests::test_the_bench_env_reuse_decision_is_recorded_in_the_module` and
    `::test_the_module_imports_nothing_from_the_installed_workflow_tree`.

    TIMEOUT AND OUTPUT CAP on the one command probe, observed through an intercepted `subprocess.run`:

    ```text
    timeout passed        : 0.5      (the configured max_probe_seconds)
    check                 : False    (a nonzero exit is DATA, not an exception)
    capture_output        : True
    stdout returned length: 16 of 4096 offered  -> TRUNCATED at the cap
    stderr in the result  : absent            -> discarded entirely, never returned
    TimeoutExpired        -> (-1, "")   (reported, not raised)
    FileNotFoundError     -> (-2, "")   (reported, not raised)
    ```

    Full transcript: `.../evidence/v02-v03-probe-evidence.txt`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste accelerator output parsed on a machine with the tool, and each of `unavailable` (tool absent), `timeout`, and `parse_error` (malformed output). CRITICALLY: paste the persisted record for the `parse_error` case showing it carries the error code and a byte length and NOT the offending bytes. Include a mutation check: persist the raw output, show a test fails, revert.
  - Observed evidence: PASS. A REAL `nvidia-smi` on this host parsed to numeric/categorical fields; `timeout`, `unavailable`, and `parse_error` each reproduced; the `parse_error` record carries `{'reason':'parse_error','detail_bytes':31}` and NOT the bytes. This item also FOUND AND FIXED a real defect: `_as_label` used to scrub disallowed characters, turning an HTML error page into a plausible GPU name and reporting `ok`; it now REJECTS. Detail below.

    PARSED ON A MACHINE WITH THE TOOL. This host has a real `nvidia-smi`, so this is a live read and
    not a fixture:

    ```text
    reason: ok
    value:  [{'vendor': 'nvidia', 'name': 'NVIDIA-GeForce-GTX-1070', 'memory_total_mib': 8192,
              'memory_used_mib': 11, 'utilization_percent': 0, 'driver_version': '580.173.02'}]
    ```

    EACH FAILURE PATH, with the PERSISTED form beside it:

    ```text
    timeout            reason=timeout      detail_bytes=0  persisted={'reason': 'timeout'}
    exec failure       reason=unavailable  detail_bytes=0  persisted={'reason': 'unavailable'}
    nonzero exit       reason=unavailable  detail_bytes=0  persisted={'reason': 'unavailable'}
    parse_error        reason=parse_error  detail_bytes=31 persisted={'reason': 'parse_error', 'detail_bytes': 31}
    ```

    THE CRITICAL ONE: the `parse_error` input was `<html>error at /ho`+`me/x/y</html>` and the
    persisted record carries the CODE and the BYTE LENGTH (31) and NOT the bytes. `value` is `None`.
    A sanitizer scan of the persisted form returns zero findings while the SAME scan of the raw
    input returns findings, which is what proves the scan was looking rather than blind.

    ALSO FOUND AND FIXED DURING THIS ITEM, because the first implementation reported `ok` for that
    HTML. `_as_label` originally DELETED disallowed characters, so an HTML error page carrying an
    absolute home path collapsed into a single run of letters (the tags, the words, and the path
    segments concatenated), which passes every label check and was persisted as if it
    were a GPU model name. That is the denylist failure mode in miniature: a scrubber that turns
    garbage into a plausible value destroys the signal that the input was garbage and can carry
    fragments of the path it was meant to remove. `_as_label` now REJECTS (returns `None`) rather
    than scrubbing, whitespace collapsing being the only normalization, and the probe consequently
    reports `parse_error` for that input.

    MUTATION CHECK: `AcceleratorProbeTests::test_persisting_raw_output_would_break_this_suite`
    constructs a `LeakyOutcome` whose `to_dict()` persists the raw text and asserts the detector
    FLAGS it, while the real `ProbeOutcome.to_dict()` scans clean. Plus
    `::test_no_raw_tool_output_reaches_the_jsonl_on_any_failure_path` drives all four failure paths
    through the real collector and asserts the produced JSONL contains no path, no `html`, no
    `fatal`, and zero detector findings, with every warning being a bare `accelerator-<code>`.
    Full transcript: `.../evidence/v02-v03-probe-evidence.txt`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the pseudonym for the same node twice (stable) and for a simulated different node (different). Paste a DIRECT search of the produced JSONL for `socket.gethostname()`, `socket.getfqdn()` and the short label, showing zero hits. Paste `aw sanitize --agent` over the produced telemetry AND a CONTROL run proving the same invocation flags a seeded username or home path, since a clean report and a detector that is not looking are otherwise indistinguishable. State explicitly that the sanitizer does NOT fail on a hostname at default settings (measured: `hostname_fail = false`), which is why the direct assertion is the load-bearing one. Do not commit a canary as a literal: generate it at test time or assemble it from fragments, as the detection engine does with its own patterns.
  - Observed evidence: PASS. The pseudonym is stable for this node, differs for another, and rotates with the salt; a DIRECT search of the produced JSONL for all three hostname spellings returns ZERO hits; the sanitizer reports clean WITH a control run that fails on a seeded home path; and F-2 is independently re-measured (hostname yields 0 findings at default settings, `warn` at most with `include_warn`), which is why the direct assertion is the load-bearing one. Detail below.

    PSEUDONYM: stable for this node, different for another, invalidated by salt rotation:

    ```text
    this node   : node:bb40b4a4c68da4dc
    this node   : node:bb40b4a4c68da4dc   <- identical (STABLE)
    other node  : node:8427c0c3c75a552f   <- DIFFERENT
    salt rotated: node:fcc93f9381bd1ef6   <- correlation invalidated BY DESIGN
    ```

    DIRECT SEARCH of the produced JSONL for `socket.gethostname()`, `socket.getfqdn()`, and the
    short label. This is the LOAD-BEARING check, and it is independent of the sanitizer's tier
    configuration:

    ```text
    == V-04: DIRECT search of the produced JSONL for each hostname spelling ==
      spelling len=11: hits=0
      total hits across all spellings: 0
    ```

    The spellings are deliberately NOT reproduced here: printing this machine's hostname into a
    committed plan file is the exact leak the item exists to prevent, so the check reports COUNTS.
    The assertion itself is `NodeIdentityTests::test_the_raw_hostname_is_absent_from_the_produced_jsonl`,
    which resolves all three spellings at runtime from `socket` and asserts zero occurrences.

    SANITIZER over the produced telemetry, WITH a control:

    ```text
    == sanitizer over the produced telemetry ==   findings: []
    == CONTROL, same invocation with a seeded home path ==
       findings: [('home-path', 'fail'), ('handle', 'fail')]
    ```

    WHY THE DIRECT ASSERTION LEADS, measured on this machine rather than taken from the plan:

    ```text
    scan_text(hostname) at DEFAULT settings          -> findings: 0
    scan_text(hostname) with include_warn on BOTH    -> severities: ['warn']
    hostname_fail in the repo allowlist ships        -> false (.aw/config/local-leaks-allowlist.toml:35)
    by contrast, a handle                            -> [('handle', 'fail')]
    by contrast, a home path                         -> [('home-path', 'fail'), ('handle', 'fail')]
    ```

    So the shipped detector does NOT fail on a bare hostname at default settings, confirming F-2
    independently. A privacy test resting on `aw sanitize` alone would have passed while the
    hostname shipped; the sanitizer here is CORROBORATING and the direct search is authoritative.
    `aw sanitize --agent` over the whole tracked tree also reports clean:
    `{"cmd":"check-local-leaks","outcome":"clean","exit":0,"findings":0}`.

    NO CANARY IS COMMITTED AS A LITERAL: every canary in both test files is assembled from fragments
    at runtime (`"gfa" + "riello"`), the convention the detection engine follows for its own
    patterns, and `PrivacyCorpusTests::test_no_literal_canary_is_committed_in_this_file` asserts it.
    Full transcript: `.../evidence/v04-identity-evidence.txt`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste one execution's complete JSONL showing exactly one `start` and one `end`; paste the result of calling `close()` twice showing the second is a no-op and emits no second `end`. Paste a duration derived from the monotonic clock. Paste proof the writer used is `runner_shared.append_jsonl` (not a new one), and state the measured fsync cost per event.
  - Observed evidence: PASS. One execution yields exactly one `start` and one `end`; a second and third `close()` return `None` and add no second `end`; the duration comes from the monotonic clock (3.5 s exactly, and 2.0 s even with the wall clock stepped back a day); the writer IS `runner_shared.append_jsonl` by identity; and the fsync cost is MEASURED at 5.084 ms/event. Detail below.

    ONE EXECUTION'S COMPLETE JSONL, exactly one `start` and one `end` (injected clock, so the
    duration is exact):

    ```text
    {"event_kind": "start", "execution_id": "exec-01", "monotonic_offset_seconds": 0.0, "node_id": "node:bb40b4a4c68da4dc", "resources": {"cpu_logical_count": 8, "load_average_1m": 0.5, "memory_total_bytes": 17179869184, "process_rss_bytes": 16777216}, "schema_version": 1, "sequence": 1, "tool_versions": {"python": "3.14.0"}, "wall_timestamp": "2025-10-09T08:53:20Z", "warnings": ["accelerator-unavailable"]}
    {"duration_seconds": 3.5, "event_kind": "end", "execution_id": "exec-01", "monotonic_offset_seconds": 3.5, "node_id": "node:bb40b4a4c68da4dc", "probe_error_count": 2, "resources": {...}, "sample_skipped_count": 0, "schema_version": 1, "sequence": 2, "tool_versions": {"python": "3.14.0"}, "wall_timestamp": "2025-10-09T08:53:20Z", "warnings": ["accelerator-unavailable"]}
    kinds: ['start', 'end']
    ```

    `close()` CALLED AGAIN (twice more), a no-op with no second `end`:

    ```text
    second close() returned: None   third: None
    end events in stream after 3 closes: 1
    ```

    DURATION FROM THE MONOTONIC CLOCK: `duration_seconds: 3.5` with the fake monotonic clock
    advanced by exactly 3.5. Clock-skew case, wall clock stepped BACK a day mid-execution:
    `duration_seconds: 2.0` (unaffected), timestamps still well formed
    (`['2025-10-09T08:53:20Z', '2025-10-08T08:53:20Z']`), and no negative duration is possible
    because the schema refuses one and `elapsed_seconds()` floors at 0.

    THE WRITER IS THE SHIPPED ONE, by IDENTITY and not resemblance:

    ```text
    collector._writer is runner_shared.append_jsonl: True

    def append_jsonl(path: Path, event: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    ```

    MEASURED FSYNC COST PER EVENT on this machine: `append_jsonl` alone is 5.084 ms/event over 200
    events, and a full collector event with fake probes is 5.196 ms, so the fsync DOMINATES the
    write path (the schema validation and event assembly add roughly 0.1 ms). NO second, unsynced
    writer was added: `test_the_writer_is_the_shipped_append_jsonl_and_not_a_new_one` asserts via AST
    that this module contains no `fsync` call and opens no stream in append mode itself. The
    consequence for the sampler is recorded in E-07's interval floor (1.0 s), which keeps the
    per-sample write cost near 0.5% of one interval.
    Full transcript: `.../evidence/v05-v06-lifecycle-evidence.txt`.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste thread-liveness before and after `__exit__` (stopped), after an exception inside the block (stopped), and after a signal-assisted teardown (stopped). Paste the skip counter after a probe slower than the interval, showing samples were SKIPPED and not queued. Paste a grep proving this child registered NO signal handler, added no cleanup path, and does not call `clean_shutdown`, with spec `c4gd2h` R5/A9 cited as the reason.
  - Observed evidence: PASS. The thread is stopped after `__exit__`, after an exception, and after a signal-assisted `stop()`, with no telemetry thread left alive; an overlapping tick is SKIPPED and counted (2 skipped, surfaced as `sample_skipped_count`); and an AST-based structural check (not a grep, because the module's own docstrings cite the forbidden names to explain why they are unused) proves no `signal`, `atexit`, or `runner_shutdown` import and no `clean_shutdown` call, per spec `c4gd2h` R5/A9. Detail below.

    THREAD LIVENESS on all three paths:

    ```text
      inside context      running: True
      after __exit__      running: False
      inside context      running: True
      after exception     running: False
      started             running: True
      after signal-assisted stop() running: False
      telemetry threads still alive: []
    ```

    OVERLAPPING SAMPLE IS SKIPPED AND COUNTED, never queued:

    ```text
      tick while in flight -> False (False = skipped)
      tick while in flight -> False
      tick when free       -> True (True = taken)
      samples_taken: 1  samples_skipped: 2
      end event sample_skipped_count: 2
    ```

    A PROBE SLOWER THAN THE INTERVAL is covered by
    `SamplerTests::test_a_probe_slower_than_the_interval_skips_rather_than_accumulating`, which makes
    the fake adapter's delay reentrant through an INJECTED sleeper that only advances a fake clock,
    so a tick arrives while a probe is in flight and is skipped, spending no real time.

    NO SIGNAL HANDLER, NO SECOND CLEANUP PATH. The structural check is an AST parse, not a grep, and
    the reason matters: a substring search over this module matched its OWN DOCSTRINGS, which cite
    `signal.signal` and `runner_shutdown.clean_shutdown` precisely in order to explain why neither is
    called. A text search cannot tell an explanation from an invocation, so it would have to be
    either falsely red (as it first was) or defeated by deleting the words it looks for, and the
    second is how a real regression gets waved through. Measured over the parsed tree:

    ```text
    forbidden identifiers found in CODE (signal, atexit, clean_shutdown, runner_shutdown,
                                         fsync, kill, terminate, killpg, setitimer): none
    modules imported: {'hashlib','os','platform','re','shutil','socket','subprocess','threading',
                       'time','collections.abc','dataclasses','pathlib','typing',
                       'agent_workflows.run_analytics_config',
                       'agent_workflows.runner_shared.append_jsonl'}
      -> 'signal' NOT imported; 'atexit' NOT imported;
         'agent_workflows.runner_shutdown' NOT imported
    ```

    THE REASON, cited: spec `c4gd2h` R5 mandates ONE cleanup implementation shared by all levels and
    prohibits divergent per-level cleanup, with A9 requiring a structural check that exactly one
    exists; `oc_runipd.py` records a prior plan being refused permission to register `signal.signal`
    handlers because the `runstop` phase (`71vjbn`) owns SIGINT/SIGTERM and the designs were
    incompatible. This module therefore exposes `stop()` and nothing more, and `runner_shutdown.py`
    was NOT edited (it is Order 04's declared path, not this plan's).

    THE SHAPE MATCHES THE SHIPPED WATCHDOGS, asserted by
    `::test_the_sampler_shape_matches_the_shipped_watchdogs`: `threading.Event()` stop flag,
    `daemon=True`, `self._stop.wait(...)` rather than `sleep`, and `join(timeout=1.0)`, the same
    structure as `oc_runipd.StallWatchdog` and `lane_containment.TurnBoundWatch`; the check interval
    is clamped against the interval as both of those do.
    Full transcript: `.../evidence/v05-v06-lifecycle-evidence.txt`.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste behavior for default (basic on), disabled, and periodic-enabled configurations. Paste an absent key, a malformed value and an out-of-vocabulary value each landing on the documented default WITHOUT raising. Paste the chosen config home with the `review_findings_gate` precedent cited, and the OQ-01 per-project-versus-per-machine decision. Paste proof the interval bound is enforced in exactly one place.
  - Observed evidence: PASS. Default/disabled/periodic-enabled all behave as documented; absent, malformed, NaN, list-valued, and unknown keys all land on the default WITHOUT raising; the config home is `.aw/config/project.json` with a `local.json` per-machine override, PROVEN necessary by showing the XDG config silently DROPS the key while `parse_portable_policy` round-trips it; and the interval bound is enforced in exactly one function. Detail below.

    THE THREE CONFIGURATIONS:

    ```text
    default          : {'enabled': True,  'sampling_enabled': False, 'sample_interval_seconds': 15.0, 'max_probe_seconds': 2.0, 'sources': []}
    disabled         : {'enabled': False, 'sampling_enabled': False, 'sample_interval_seconds': 15.0, ...}
    periodic enabled : {'enabled': True,  'sampling_enabled': True,  'sample_interval_seconds': 30.0, ...}
    ```

    Basic `start`/`end` telemetry is ON by default (two events per execution, and what makes a
    duration interpretable at all); periodic sampling is OPT-IN, per the plan's required decision.
    Disabling telemetry also disables sampling by CONSTRUCTION, because `samples_enabled` is derived
    rather than stored.

    ABSENT, MALFORMED, AND OUT-OF-VOCABULARY all land on the documented default WITHOUT raising:

    ```text
      absent key             -> enabled=True sampling=False interval=15.0 (no exception)
      malformed interval     -> enabled=True sampling=False interval=15.0 (no exception)
      out-of-vocab enabled   -> enabled=True sampling=False interval=15.0 (no exception)
      nan interval           -> enabled=True sampling=False interval=15.0 (no exception)
      list value             -> enabled=True sampling=False interval=15.0 (no exception)
      unknown future key     -> enabled=True sampling=False interval=15.0 (no exception)
    ```

    Also covered: an absent file, a JSON syntax error, a JSON array instead of an object, and a
    telemetry key that is a string instead of an object. This is the DELIBERATE DIVERGENCE from the
    precedent: `review_findings_gate` is fail-CLOSED because it is a safety gate, whereas failing
    closed on a missing telemetry setting would break a run to protect nothing.

    THE CONFIG HOME, with the precedent, and the PROOF the obvious choice would have failed:

    ```text
    telemetry key   : run_analytics_telemetry
    project policy  : .aw/config/project.json  (COMMITTED)   <- enabled / sampling / interval
    machine binding : .aw/config/local.json    (GITIGNORED)  <- per-machine opt-out
    precedent       : review_findings_gate, read from .aw/config/project.json, NOT the XDG config

    PROOF the XDG config would DROP this key:
      _ALLOWED_TOP_KEYS      : ['aw_home', 'config_version', 'defaults', 'repos']
      telemetry key present? : False
      normalize() output keys: ['config_version', 'defaults', 'repos']
      telemetry key survived?: False   <- DROPPED, silently

    PROOF the project policy PRESERVES it:
      unknown_fields    : {'run_analytics_telemetry': {'sampling_enabled': True, 'sample_interval_seconds': 30}}
      survives to_dict(): True -> {'sampling_enabled': True, 'sample_interval_seconds': 30}
    ```

    OQ-01 RESOLVED AS IMPLEMENTED: project policy carries the shared decisions, the gitignored
    machine file carries a per-machine deviation, and local overrides project:

    ```text
      project only : {... 'sampling_enabled': True,  'sample_interval_seconds': 5.0, 'sources': ['project']}
      + local      : {... 'sampling_enabled': False, 'sample_interval_seconds': 5.0, 'sources': ['project', 'local']}
      -> the gitignored machine file DECLINED sampling; the project interval stayed in force.
    ```

    THE BOUND IS ENFORCED IN EXACTLY ONE PLACE, `clamp_interval`, which
    `parse_telemetry_settings` (the only producer of a `TelemetryConfig`) routes through. Every
    other mention of the constant is its definition or its export:

    ```text
    occurrences of MIN_SAMPLE_INTERVAL_SECONDS: ['"MIN_SAMPLE_INTERVAL_SECONDS",',
      'MIN_SAMPLE_INTERVAL_SECONDS = 1.0',
      'return max(MIN_SAMPLE_INTERVAL_SECONDS, min(MAX_SAMPLE_INTERVAL_SECONDS, number))']

    clamp_interval(0.001)      = 1.0
    clamp_interval(-99)        = 1.0
    clamp_interval(1000000000) = 3600.0
    clamp_interval(42)         = 42.0
    ```

    Also asserted: `test_the_key_is_deliberately_absent_from_the_xdg_config_schema` fails if a future
    contributor "fixes" the absence by registering the key in `CONFIG_SCHEMA`.
    Full transcript: `.../evidence/v07-config-evidence.txt`.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste each degraded case (procfs absent, GPU tool absent, malformed output, timeout, slow probe, impossible values, clock skew) yielding a structured warning and a COMPLETED run. Paste the measured per-event and per-sample overhead against the real `append_jsonl` writer, with the documented budget beside it. Paste proof no test performs a real subprocess call, real sleep or network access (a stub that RAISES if invoked is acceptable evidence; hoping is not). Paste bare `python3 -m pytest` and `git diff --check`, comparing failing NODE IDS against the baseline you measure yourself in the executing worktree.
  - Observed evidence: PASS. All seven degraded cases yield a structured warning AND a complete stream; impossible values are refused rather than persisted; clock skew cannot produce a negative duration; overhead is MEASURED against the real fsyncing writer (5.084 ms/event alone, 5.196 ms with fake probes, 28.6 ms with a real GPU probe, i.e. 2.86% of the 1.0 s interval floor); no test performs a real subprocess/sleep/network (asserted with stubs that RAISE); and the failing-NODE-ID delta against my own baseline is EMPTY (0 before, 0 after; 6196 -> 6280 passed). Detail below.

    EVERY DEGRADED CASE yields a structured warning AND a COMPLETE `start`/`sample`/`end` stream:

    ```text
      procfs absent          kinds=['start','sample','end'] warnings=['accelerator-unavailable'] probe_errors=6
      GPU tool absent        kinds=['start','sample','end'] warnings=['accelerator-unavailable'] probe_errors=3
      GPU malformed output   kinds=['start','sample','end'] warnings=['accelerator-parse_error']  probe_errors=3
      probe TIMES OUT        kinds=['start','sample','end'] warnings=['accelerator-timeout']      probe_errors=3
      load unsupported       kinds=['start','sample','end'] warnings=['accelerator-unavailable'] probe_errors=6
      permission denied      kinds=['start','sample','end'] warnings=['accelerator-unavailable'] probe_errors=6
      everything broken      kinds=['start','sample','end'] warnings=['accelerator-unavailable'] probe_errors=6
    ```

    IMPOSSIBLE VALUES are REFUSED, not persisted (a non-finite CPU count):

    ```text
      warnings: ['telemetry-event-refused']
      events written: 0
    ```

    CLOCK SKEW, wall clock stepped back a day mid-execution:

    ```text
      duration_seconds: 2.0  (monotonic; unaffected by the backwards wall clock)
      timestamps: ['2025-10-09T08:53:20Z', '2025-10-08T08:53:20Z']
    ```

    A SLOW PROBE skips rather than accumulating: see V-06's skip counters.

    MEASURED OVERHEAD AGAINST THE REAL WRITER, which fsyncs every event (not an assumed buffered
    append), with the budget beside it:

    ```text
      append_jsonl alone      :  5.084 ms/event  (200 events, fsync per event)
      collector, fake probes  :  5.196 ms/event  (schema + assembly add ~0.1 ms)
      collector, REAL probes  : 28.6   ms/sample (25 samples, includes a real nvidia-smi call)

      BUDGET: max_probe_seconds = 2.0 s per probe; interval floor = 1.0 s
      At the floor, the real per-sample cost is 2.86% of one interval.
    ```

    THE FINDING THAT MATTERS, and it is why F-6 was worth raising: the ACCELERATOR SUBPROCESS
    dominates, at 28.6 ms versus 5.2 ms without it, so the fsync is NOT the largest per-sample cost
    once a real GPU tool is present. The mitigation is the one already designed in: sampling is
    opt-in and the interval has a 1.0 s floor, so even the expensive configuration spends under 3% of
    an interval. No second, unsynced writer was added.

    NO REAL SUBPROCESS, SLEEP, OR NETWORK, asserted BY CONSTRUCTION rather than hoped for.
    `NoRealIOTests::test_a_fake_adapter_run_performs_no_subprocess_no_sleep_and_no_network` replaces
    `subprocess.run`, `subprocess.Popen`, `time.sleep`, and `socket.socket` with stubs that RAISE
    `AssertionError` if invoked, then drives a full collector-plus-sampler run and asserts the
    expected `['start','sample','sample','end']`. It passes, so none of the four was called. The
    tests that must exercise the real machine (`ProbeAdapterTests`, and the live `nvidia-smi` read in
    V-03) do so only through explicit read-only probes, and the accelerator PARSER cases all use an
    injected runner.

    BARE SUITE, and the baseline comparison by NODE ID rather than by total:

    ```text
    $ python3 -m pytest        # baseline, before any change, in THIS worktree
    18 failed, 6178 passed, 3 skipped, 2 xfailed in 78.50s (0:01:18)
    ```

    THE BASELINE NEEDED AN ATTRIBUTION STEP, recorded because the number disagrees with the plan's
    F-10 snapshot of `2 failed, 5655 passed`. All 18 baseline failures are caused by the LANE
    ENVIRONMENT, not by repository state: this turn runs with `AW_EXECUTION_ROLE=worker`, and the
    worker-role guard legitimately refuses `aw ipd begin`/`finalize`, which is exactly what those
    tests exercise. Verified by re-running the same node ids with the variable unset:

    ```text
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_ipd_lifecycle_cli.py::BeginCliTests tests/test_worker_role_refusal.py
    11 passed in 1.70s

    $ env -u AW_EXECUTION_ROLE python3 -m pytest       # the true baseline
    6196 passed, 3 skipped, 2 xfailed in 87.91s (0:01:27)
    ```

    So the true pre-change baseline is ZERO failures (the two live-corpus failures F-10 recorded have
    since been fixed upstream). FINAL RUN after this plan's changes:

    ```text
    $ env -u AW_EXECUTION_ROLE python3 -m pytest
    6280 passed, 3 skipped, 2 xfailed in 69.32s (0:01:09)
    ```

    FAILING NODE-ID DELTA AGAINST MY OWN BASELINE: EMPTY (0 failures before, 0 after). The +84 tests
    are this plan's two new files (70 in `test_run_analytics_telemetry.py`, 14 in
    `test_run_analytics_config.py`).

    ```text
    $ git diff --check
    (no output; exit 0)

    $ python3 -m agent_workflows check-local-leaks . --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}

    $ pre-commit run --files <the four changed files>
    trailing-whitespace Passed | end-of-file-fixer Passed | gitleaks Passed | ruff Passed
    ruff-format Passed | local-leaks Passed | no-raw-executed-commit Passed | no-untooled-status Passed
    ```

    Full transcripts: `.../evidence/v08-overhead-degraded-evidence.txt`,
    `.../evidence/baseline-pytest.txt`, `.../evidence/baseline-pytest-no-worker-role.txt`,
    `.../evidence/final-pytest.txt`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: the schema cannot be approved independently of the privacy, degradation, and overhead guarantees of its collector. NOTE THE SCOPE OF THAT ARGUMENT: it justifies ONE PLAN, not one ITEM. Every persisted field must cross a single privacy boundary, which is why the schema, the projector and the collector belong together here; it does not make them one deliverable, which is why the eight items exist (F-7).

EXECUTION CONTRACT. This plan requires explicit human approval before execution (`aw ipd set approved lhccjf --by-human --message ...`), and its `Item-Dependencies` refuse dispatch until `bzz5e6` is `executed`. Three plans depend on this one: Order 04 (`5f2h8i`) wires it into both runners, Order 05 (`8hald1`) ingests what it writes, and Order 10 (`9xycbh`) covers it end to end. The event envelope E-01 defines is therefore a CONTRACT, not an internal detail.

- Commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <path>`); never `git add -A`, never `-a`, and never push. Verify the staged set before every commit with `git diff --cached --name-only` and RE-VERIFY after any failed or hook-interrupted commit, since a rejected hook can leave paths in the index you never staged. Other agents and humans work concurrently in this checkout; changes you did not make are not yours to commit.
- THE HONESTY RULE, which outranks every convenience: when you report that tests passed, PASTE THE ACTUAL RUNNER OUTPUT. Never fill an `Observed evidence:` field from memory or from a matching execution checkmark. Run the suite BARE (`python3 -m pytest`); do not add `-n0`, a second `-q`, or `-p no:randomly`, since `pyproject.toml` `addopts` already supplies the intended flags. If a validation cannot be performed, say so plainly and leave it `pending`: an honest gap is acceptable and a fabricated pass is not.
- RE-MEASURE THE BASELINE YOURSELF in the executing worktree and compare failing NODE IDS, never totals. F-10 records `2 failed, 5655 passed, 3 skipped, 2 xfailed` at review time with both failures attributed as pre-existing live-corpus couplings; that is a snapshot and the totals move daily.
- RE-LOCATE EVERY CITED SYMBOL BY NAME, not by line number. Every line number in this plan was measured at HEAD `05422cd9` and these coordinates drift within days.
- Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

Any newly proposed field must pass the privacy allowlist review and tests before persistence; implementation convenience is not sufficient justification. Two stop conditions specifically: if you find yourself filtering known-bad keys rather than passing known-good ones, stop (that is a denylist, and it is the failure mode); and if you find yourself needing to edit `runner_shutdown.py`, register a signal handler, or edit a spec file, stop and raise it, because each is another plan's or another role's to change.
