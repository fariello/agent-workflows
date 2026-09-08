# IPD: Cross-host resource telemetry schema, collector, and sampling controls

- Date: 2026-09-08
- Kind: child
- Concern: Capture contemporaneous resource context without leaking host identity or making runner reliability depend on optional probes.
- Scope: Build the telemetry event schema, safe system probes, pseudonymous node identity, lifecycle collector, periodic sampler, overhead limits, and configuration model.
- Scope-Paths: agent_workflows/run_analytics_telemetry.py, agent_workflows/run_analytics_config.py, tests/test_run_analytics_telemetry.py, tests/test_run_analytics_config.py
- Item-Dependencies: executed:bzz5e6
- Status: reviewed
- Readiness: go-pending-approval
- Set: runanalytics
- Order: 3
- Highest E allocated: 08
- Author: Codex
- Id: lhccjf

## Workflow history

- 2026-09-08 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. PR-043..PR-052, ALL TEN FIXED, no open findings. The verdict token is stated explicitly because `plan_readiness.newest_verdict` reads the newest review record's first verdict token and falls back to a negative scan when none is present. THE TWO FINDINGS THAT WOULD HAVE PRODUCED WRONG CODE ARE BOTH ABOUT TRUSTING A SHIPPED AUTHORITY THAT DOES NOT DO WHAT THE PLAN ASSUMED. FIRST (PR-043, F-1): the conventions said to "integrate with existing config authorities", but `config.py` enforces a fixed `_ALLOWED_TOP_KEYS` (`:57-65`) and `normalize()` REBUILDS its output from `default_config()`, so an unregistered telemetry key is silently DROPPED on save; the shipped precedent for exactly this case is `review_findings_gate` (`config.py:1082-1145`), whose own comment says it is read from `.aw/config/project.json` and NOT via the XDG config "which drops unknown keys", round-tripping through `project_schema`'s `unknown_fields`. An executor following the authored convention would have written a setting that vanishes. SECOND (PR-044, F-2), and it is the one that matters most for a privacy plan: THE SHIPPED LEAK DETECTOR DOES NOT FAIL ON A HOSTNAME, which is the exact field this child exists to suppress. Measured, `leak_sanitizer.scan_text` over this machine's hostname returns ZERO findings at default settings; the hostname IS derived as a token (`:416`) but lands in the `warn` tier and is promoted to `fail` only when `hostname_fail = true`, which ships FALSE (`.aw/config/local-leaks-allowlist.toml:35`), and even `include_warn=True` on both `build_ruleset` and `scan_text` reports only `warn`. A username and a home path both return `fail` immediately, so the detector's competence on those two would have masked the gap, and a privacy test resting on `aw sanitize` would have PASSED while the hostname shipped. E-04 now requires a DIRECT assertion against `socket.gethostname()`/`getfqdn()`/short label, with the sanitizer demoted to corroboration and required to carry a control run. THIRD, AN 860-LINE IMPLEMENTATION OF NEARLY THIS PROBE SET ALREADY SHIPS HERE AND THE PLAN NEVER MENTIONED IT (PR-045, F-3): `.aw/system/workflows/benchmark/tools/bench_env.py` covers CPU, RAM breakdown, swap, load, GPU, container hints and filesystem, stdlib-only and read-only, with `_run:63` already bounding every informational command by timeout and swallowing failures, and `scrub:652` already redacting hostname/user/paths; OQ-02 now requires the reuse decision be recorded and notes that a direct import is the WORST option since that path is installed workflow content, not a package module. FOURTH, THE CLEANUP ROUTINE IS SPEC-MANDATED SINGULAR AND "lifecycle shutdown" invited a second one (PR-046, F-4): spec `c4gd2h` R5 prohibits divergent per-level cleanup and A9 requires a structural check that exactly one exists, while `oc_runipd.py:1587-1610` records a prior plan being explicitly REFUSED permission to register `signal.signal` handlers because `runstop` Phase 5 owns them and the designs were incompatible; the fence now forbids editing `runner_shutdown.py` (Order 04 declares it), registering a handler, or calling `clean_shutdown`. ALSO FIXED: the three E-items were mechanically sized, as all ten children carry exactly three and the lint reported conforming both before and after, so it cleared nothing (PR-049, F-7, split to EIGHT items across four groups with V-01..V-08 to bijection, `Highest E allocated` 03 -> 08, the same finding sibling `bzz5e6` had); the bounded-sampler pattern exists TWICE already in `StallWatchdog` and `TurnBoundWatch` and neither was cited (PR-047, F-5); `append_jsonl` fsyncs per event, so the promised overhead bound had to be measured against the real writer rather than an assumed buffered append (PR-048, F-6); the gate carried no execution contract at all, the third sibling in a row with that omission (PR-050, F-8); ten escaped backtick pairs rendered as literal backslashes, after Order 01's six and Order 02's four (PR-051, F-9); no baseline was recorded despite requiring a bare suite run, now `2 failed, 5655 passed` with both failures attributed as pre-existing live-corpus couplings (PR-052, F-10); and "No open questions" hid two genuinely unmade decisions, now OQ-01 (config home, resolved by splitting project policy from machine-local override) and OQ-02, both resolved from repository evidence as D-1..D-5.

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): specified telemetry events, privacy minimization, multi-node behavior, degradation, and sampling controls.

## Goal

Provide a runner-neutral telemetry collector that records what hardware and load were present when an invocation actually ran, including node changes between attempts. Telemetry must be useful for performance analysis but non-fatal, bounded, configurable, and privacy-minimized.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

RIGHT-SIZING NOTE, recorded because a passing lint did not clear it. This plan was authored with exactly THREE E-items, and so was every one of the Set's ten children; `aw ipd lint --phase author` reported conforming and the density advisory was silent. A schema, a probe layer, an identity scheme, a background sampler, a config model and an overhead budget are not one concern each in three items. Sibling `bzz5e6`'s review found and split the identical pattern (its PR-031). Split into eight items across four groups; each names ONE deliverable and maps to one V-item.

### Task group 1: Schema and safe probes

- [ ] E-01 Define the versioned event ENVELOPE and its strict schema: `start`, `sample`, and `end` records carrying execution/run/IPD/set/attempt/phase/host/model identifiers, wall timestamps, and monotonic offsets. Schema and validation only; no probing, no I/O.
  MAKE THE SCHEMA AN ALLOWLIST, NOT A DENYLIST, and say so in the module docstring. The Findings table below enumerates a forbidden set; that list is a TEST CORPUS, not the implementation strategy. A denylist passes every test written from itself and leaks on the first field nobody imagined. Sibling `bzz5e6` carries the same requirement (its PR-034), so the two must agree: a field is persisted because it appears in an explicit allowlist of reviewed, non-secret, numeric-or-categorical keys, and for no other reason.
  - Depends on: none
  - Expected outcome: typed records that round-trip, REJECT an unknown key rather than dropping it silently, and reject an out-of-vocabulary event kind; a docstring stating the allowlist direction and why.
  - Execution state: pending

- [ ] E-02 Implement the resource PROBES behind an injectable adapter interface: CPU count/capacity, memory totals and availability, load, process RSS/CPU, disk capacity, and tool versions. Portable, read-only, and degrading to a structured `unavailable` rather than raising.
  READ `bench_env.py` BEFORE WRITING ANY PROBE. `.aw/system/workflows/benchmark/tools/bench_env.py` is an 860-line, stdlib-only, READ-ONLY implementation of very nearly this probe set (CPU model/cores/flags, RAM total/free/available/cached, swap, load average, GPU, container/VM hints, filesystem/storage), and the plan as authored never mentioned it. It already solves the problems this item will otherwise re-solve: `_run` (`:63`) wraps every informational command with `capture_output`, an explicit `timeout` (default 15s) and `check=False`, returning `""` on ANY failure so capture is best-effort; `_read` (`:79`) does the same for `/proc` and `/sys`. Its docstring also states the safety posture this item needs ("NEVER changes governors, mounts, swap"; "NEVER fabricates a value it could not read - unknown fields are reported as null"). DECIDE AND RECORD one of: import/extract the shared helpers, copy them with attribution, or write fresh with a stated reason. Do NOT silently produce a second, weaker subprocess wrapper; that is the re-fork this repository keeps paying for.
  - Depends on: E-01
  - Expected outcome: an adapter interface with a real implementation and a fake for tests; every probe bounded by a timeout and an output-size cap; a recorded decision about `bench_env.py` reuse with its reason.
  - Execution state: pending

- [ ] E-03 Implement the ACCELERATOR probe as its own item, because it is the only probe that shells out to a vendor tool and is the one most likely to hang, flood, or leak. Strict executable allowlist (`nvidia-smi`, `rocm-smi`), explicit timeout, output-size cap, and a parser that persists ONLY numeric and categorical fields.
  NEVER PERSIST RAW STDOUT OR STDERR. A vendor tool's output can carry a hostname, a path, or a serial number, and the whole privacy argument of this child collapses if a parse failure is recorded by storing the text that failed to parse. On `parse_error`, persist the error CODE and the byte length, never the bytes.
  - Depends on: E-02
  - Expected outcome: accelerator inventory and utilization when safely available; `unavailable`/`timeout`/`parse_error` codes otherwise; a test proving no raw tool output reaches the JSONL on any failure path.
  - Execution state: pending

### Task group 2: Identity and lifecycle

- [ ] E-04 Implement the pseudonymous NODE IDENTITY: a locally stable keyed pseudonym derived from machine identity, persisting neither the input nor the raw hostname, with the correlation scope and rotation behavior documented.
  DO NOT ASSUME THE SHIPPED LEAK DETECTOR WILL CATCH A HOSTNAME REGRESSION. Measured 2026-09-08: `leak_sanitizer.scan_text` over this machine's hostname returns NOTHING at default settings. The hostname IS derived as a token (`leak_sanitizer.py:416`) but lands in the `warn` tier, and `_HOSTNAME_REASONS` (`:438`) is promoted to `fail` only when the allowlist sets `hostname_fail = true`, which ships FALSE by default (`.aw/config/local-leaks-allowlist.toml:35`, off "so a shared CI-runner hostname does not fail every build"). Even with `include_warn=True` passed to BOTH `build_ruleset` and `scan_text` it reports only `warn`. By contrast a username and a home path both return `fail` immediately. So `aw sanitize` is a necessary but INSUFFICIENT oracle for exactly the field this item exists to suppress, and a test relying on it would pass while the hostname shipped. Write a DIRECT assertion: the raw hostname string must not appear anywhere in the produced JSONL, asserted against `socket.gethostname()` and `socket.getfqdn()` plus its short label.
  - Depends on: E-01
  - Expected outcome: same node yields a stable pseudonym, a different node a different one; neither the raw hostname nor the derivation input is persisted; a direct hostname-absence assertion that does not depend on the sanitizer's tier configuration.
  - Execution state: pending

- [ ] E-05 Implement the COLLECTOR lifecycle: a context-managed object emitting exactly one `start` and a best-effort `end` per execution id, with monotonic timing and idempotent close.
  USE THE EXISTING JSONL AND ATOMIC-WRITE AUTHORITIES, do not hand-roll them: `runner_shared.append_jsonl` (`:458`) and `runner_shared.atomic_write_json` (`:436`) already exist and are used throughout both runners. NOTE THE OVERHEAD PROPERTY THAT MATTERS HERE: `append_jsonl` calls `os.fsync` on EVERY event. That is correct for low-volume run events and is a real per-sample cost for a periodic sampler, so E-07's budget must be measured against the actual writer rather than an assumed buffered append. If the fsync-per-sample cost proves unacceptable, record the finding and the chosen mitigation; do NOT quietly add a second, unsynced writer.
  - Depends on: E-01, E-02
  - Expected outcome: one well-formed JSONL stream per execution; a second `close()` is a no-op; durations derive from a monotonic clock and are never negative.
  - Execution state: pending

- [ ] E-06 Implement the periodic SAMPLER as a bounded background thread that stops on every normal, exception and signal-assisted cleanup path, and SKIPS an overlapping sample instead of accumulating work.
  COPY THE SHIPPED PATTERN RATHER THAN INVENTING ONE. This package already contains this exact shape TWICE: `oc_runipd.StallWatchdog` (`:655-714`) and `lane_containment.TurnBoundWatch` (`:1276-1348`). Both use a `threading.Event` for stop, a `daemon=True` thread started in `__enter__`, a `_stop.wait(interval)` loop rather than `sleep`, and `__exit__` setting the event then `join(timeout=1.0)`. Both also clamp the check interval against the bound (`max(0.05, timeout/4.0)`). Reuse that structure so a telemetry thread cannot outlive its run or block shutdown.
  KNOW THE SHUTDOWN CONTRACT YOU MUST NOT FORK. `runner_shutdown.clean_shutdown` is the ONE cleanup routine, mandated by spec `c4gd2h` R5 ("ONE implementation shared by all four levels and by crash recovery. Divergent per-level cleanup is prohibited") with A9 requiring a structural check that exactly one exists; the spec is `- Status: implementing`. This child must therefore expose a small, callable stop API and MUST NOT register a signal handler, add a cleanup path, or call `clean_shutdown` itself. Order 04 (`5f2h8i`) owns the wiring and declares `runner_shutdown.py` in its `Scope-Paths`; this child does not and must not edit it.
  - Depends on: E-05
  - Expected outcome: a sampler whose thread is provably stopped after `__exit__`, on an exception, and on a signal-assisted teardown; an overlapping tick is SKIPPED and counted, never queued; no signal handler and no second cleanup path added.
  - Execution state: pending

### Task group 3: Configuration

- [ ] E-07 Implement the validated telemetry CONFIGURATION model: basic `start`/`end` telemetry on by default, periodic sampling opt-in with a bounded interval, and a way to disable telemetry entirely.
  THE CONFIG HOME IS A DECIDED QUESTION WITH A SHIPPED PRECEDENT, AND THE OBVIOUS CHOICE IS WRONG. The conventions section said to "integrate with existing config authorities"; measured, the XDG user config (`config.py`) enforces a FIXED allowlist (`_ALLOWED_TOP_KEYS`, `:57-65`) and `normalize()` REBUILDS the output from `default_config()`, so an unregistered key is silently DROPPED on the next save. The precedent for exactly this situation is `review_findings_gate` (`config.py:1082-1145`), whose comment states it is recorded in the committed portable policy `.aw/config/project.json` "and read HERE and not via the XDG user config (which drops unknown keys)", is DELIBERATELY not registered in `CONFIG_SCHEMA` because `project_schema.parse_portable_policy` preserves unknown keys in `unknown_fields` (`project_schema.py:585`, `:624`) and writes them back on serialization. Follow that precedent: read the telemetry settings with a small never-raising reader, and pick the default direction deliberately. `review_findings_gate` is fail-CLOSED (absent means active) because it is a safety gate; telemetry is the opposite kind of thing, so an absent key must mean the documented default and never an error.
  RESOLVE PER-PROJECT VERSUS PER-MACHINE EXPLICITLY (OQ-01). `.aw/config/project.json` is COMMITTED and `.aw/config/local.json` is gitignored; a telemetry preference is arguably machine-local, and its interval is arguably a project policy. State which key lives where and why.
  - Depends on: E-01
  - Expected outcome: a never-raising reader with documented defaults; an absent, malformed or unknown-valued key lands on the documented default rather than raising; the interval bound enforced in ONE place; the chosen config home recorded with the `review_findings_gate` precedent cited.
  - Execution state: pending

### Task group 4: Proof

- [ ] E-08 Prove BOUNDED OVERHEAD and PRIVACY behavior across supported and degraded systems, with injected clocks and probes so no test spends real time or touches a real device.
  Cover, as distinct cases: Linux with procfs; procfs absent; the GPU tool absent; malformed tool output; a probe that TIMES OUT; a probe slower than the sampling interval (which must skip, not accumulate); impossible values; and clock skew. Measure the per-event and per-sample cost against the REAL writer (`append_jsonl`, which fsyncs per event) and state the measured figure rather than an assumed one.
  - Depends on: E-03, E-04, E-06, E-07
  - Expected outcome: every degraded case yields a structured warning and a completed run; a measured overhead figure against the real writer; no test performs a real subprocess call, real sleep, or network access.
  - Execution state: pending

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

Order 04 must amend the controlling runner contract if it defines the run artifact inventory. That spec is `25kzda`, which resolves to `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` (`- Id: 25kzda`, `- Status: approved`); the filename predates the id6-in-filename convention, so the id is findable only by grepping `- Id:`. Order 04 (`5f2h8i`) ALREADY declares that path in its `Scope-Paths`, so the amendment is owned and announced there, not here.

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

- [ ] V-01 validates E-01
  - Required evidence: paste a round-trip for each of the three event kinds; paste the REJECTION of an unknown key and of an out-of-vocabulary event kind, showing an error rather than a silent drop. Paste the docstring passage stating the allowlist direction. Include a mutation check: make the schema ignore an unknown key instead of rejecting it, show a test fails, revert.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the adapter interface and its fake; paste a probe result for each field family on this machine and the `unavailable` result with the same probe denied. Paste the recorded `bench_env.py` decision (reuse, copy-with-attribution, or fresh) WITH its reason. Paste proof every command probe carries a timeout and an output-size cap.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste accelerator output parsed on a machine with the tool, and each of `unavailable` (tool absent), `timeout`, and `parse_error` (malformed output). CRITICALLY: paste the persisted record for the `parse_error` case showing it carries the error code and a byte length and NOT the offending bytes. Include a mutation check: persist the raw output, show a test fails, revert.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the pseudonym for the same node twice (stable) and for a simulated different node (different). Paste a DIRECT search of the produced JSONL for `socket.gethostname()`, `socket.getfqdn()` and the short label, showing zero hits. Paste `aw sanitize --agent` over the produced telemetry AND a CONTROL run proving the same invocation flags a seeded username or home path, since a clean report and a detector that is not looking are otherwise indistinguishable. State explicitly that the sanitizer does NOT fail on a hostname at default settings (measured: `hostname_fail = false`), which is why the direct assertion is the load-bearing one. Do not commit a canary as a literal: generate it at test time or assemble it from fragments, as the detection engine does with its own patterns.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste one execution's complete JSONL showing exactly one `start` and one `end`; paste the result of calling `close()` twice showing the second is a no-op and emits no second `end`. Paste a duration derived from the monotonic clock. Paste proof the writer used is `runner_shared.append_jsonl` (not a new one), and state the measured fsync cost per event.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste thread-liveness before and after `__exit__` (stopped), after an exception inside the block (stopped), and after a signal-assisted teardown (stopped). Paste the skip counter after a probe slower than the interval, showing samples were SKIPPED and not queued. Paste a grep proving this child registered NO signal handler, added no cleanup path, and does not call `clean_shutdown`, with spec `c4gd2h` R5/A9 cited as the reason.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste behavior for default (basic on), disabled, and periodic-enabled configurations. Paste an absent key, a malformed value and an out-of-vocabulary value each landing on the documented default WITHOUT raising. Paste the chosen config home with the `review_findings_gate` precedent cited, and the OQ-01 per-project-versus-per-machine decision. Paste proof the interval bound is enforced in exactly one place.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste each degraded case (procfs absent, GPU tool absent, malformed output, timeout, slow probe, impossible values, clock skew) yielding a structured warning and a COMPLETED run. Paste the measured per-event and per-sample overhead against the real `append_jsonl` writer, with the documented budget beside it. Paste proof no test performs a real subprocess call, real sleep or network access (a stub that RAISES if invoked is acceptable evidence; hoping is not). Paste bare `python3 -m pytest` and `git diff --check`, comparing failing NODE IDS against the baseline you measure yourself in the executing worktree.
  - Observed evidence:
  - Result: pending

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
