# Review findings: plan xvm6no

- Subject-Id: xvm6no
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `522c7bc42` in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and `--phase review-finalize` was clean after revisions.

Re-verified:
- `runner_shared.StallWatchdog._run`: on `idle >= self.timeout` it calls `self._progress_checker()` once and `touch()`es/continues on True, otherwise reaps. One `progress_checker` slot, settable after construction.
- oc site `oc_runipd.run_opencode`: `watchdog = StallWatchdog(process, timeout=stall_timeout)` then `watchdog.progress_checker = observer.poll`, plus a separate `stall_progress.ProgressPoller(observer, touch_callbacks=(_subagent_progress,), ...)`. agy site `agy_runipd.run_agy_turn`: `StallWatchdog(process, timeout=stall_timeout, progress_checker=observer.poll)` plus a `ProgressPoller`.
- Both launchers export `AW_RUN_ID`/`AW_ITEM_ID6` from `state["run_id"]`/`item["id6"]` ("Always overwrite or pop, never inherit"). `conftest.py` pops both at import time.
- `runner_shared.integration_lock` polls a non-blocking `platform_lock.acquire`, injects `sleep`/`now`, and reports through `progress`; `INTEGRATION_LOCK_PROGRESS_SECONDS = 60.0`. `platform_lock` supports Windows (`os.name == "nt"` branches), so `os.getuid` is not universal.
- `agent_workflows/suite_cache.py` does not exist yet (Order 02 is `reviewed`, not executed). The reviewed 0o0wt2 text provides `run_full_suite`, the `AW_SUITE_SLOTS` resolution, and `serve_failures=False` at the seams.
- `tests/test_stall_progress.py` does NOT exist; the stall-observer tests are `tests/test_stall_progress_agy.py`.
- Feasibility probe (scratch test under gitignored `.aw/state/`, since deleted): a real silent fake-opencode child via `support.make_fake_executable`, driven through `oc_runipd.run_opencode` with `stall_timeout: 1.0` and the `tests/test_commit_run_trailers_env.py` patches, raised `StallTimeout` after 1.78s. So the E-06 end-to-end control cell is reachable in about 2s instead of 3s+.
- Spec `25kzda` names "stall or turn-limit expiry" with evidence "turn timer or runner watchdog" and does not enumerate progress sources; the plan's quoted spec phrase "no observed PROGRESS" does not appear in the spec.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | B. Security / A. Correctness | E-02 "`<tempfile.gettempdir()>/agent-workflows-<uid>/`, mode 0o700"; E-04 `heartbeat-<run_id>-<id6>` built from env | A pre-existing directory in shared `/tmp` owned by another user was not checked, so another user could block or spoof slots. Heartbeat names came from unvalidated env values, which allowed path traversal. `os.getuid` does not exist on Windows. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The directory now resolves `AW_SUITE_LOCK_DIR`, then `XDG_RUNTIME_DIR`, then a per-user temp dir. A directory owned by another uid or writable by group/other is refused, failing open with a warning. Heartbeat ids are validated against `[A-Za-z0-9._-]+`. Windows uses `getpass.getuser()`. |
| PR-002 | HIGH | IN-SCOPE | A. Correctness | E-02 "sidecar holder file per slot" | The plan did not say how a holder file left by a crashed process relates to slot freedom. An executor could check the holder file, and one SIGKILL would then wedge a slot until timeout. | Low | FIXED | The OS lock alone decides; the holder file is advisory, written after acquire and removed on release. New E-06 cell (f) kills a holder and proves the slot is free. Invariant I3. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing | Required tests and V-05 name `tests/test_stall_progress.py` | That file does not exist. | Low | FIXED | Now names `tests/test_stall_progress_agy.py`, `test_commit_run_trailers_env.py` and `test_interrupt_attempt_metadata.py`. |
| PR-004 | MEDIUM | IN-SCOPE | E. Reachability | E-06(f) "a scripted host whose child holds a long suite-slot wait ... `--stall-timeout 3`" | The cell named no harness. Inside a fake host child, "holds a suite-slot wait" depends on Order 02's CLI and real suites. | Low | FIXED | The cell now names the existing launcher harness with a real fake executable that touches the heartbeat for its exported ids, plus the silent control. I measured that the control reaps in 1.78s on current code. It runs on both hosts and must fail with the wiring reverted. |
| PR-005 | MEDIUM | IN-SCOPE | C. Operability | E-03 conditional `conftest.py` scrub "ONLY IF ... leaks"; Scope check under-scope | The plan left a scope-changing decision to the executor. Scrubbing would also break the nested case the guard exists for, because the outer suite IS the slot holder. | Low | FIXED | Decided: the marker is set only in the child env and conftest is unchanged, with the reason given. The honest limit (nested runs are unbounded) is stated. Cell (d) tests both directions; V-03 checks conftest is unchanged. |
| PR-006 | MEDIUM | IN-SCOPE | F. Silent failure | E-02 "Every 60s of waiting it calls progress"; the goal "says so every minute" | The first message would come only after 60s of silent waiting. Poll interval, injectable clock, malformed env values, unsupported lock primitive, and recording contention were all unspecified. | Low | FIXED | The waiting line now prints on the first busy poll, then every `INTEGRATION_LOCK_PROGRESS_SECONDS`. The 1s poll uses an injectable sleep/now. Malformed env falls back with a warning, an unsupported primitive fails open, and `slot` is recorded on `SuiteRunResult` and therefore on the seam records. |
| PR-007 | MEDIUM | IN-SCOPE | A. Correctness | E-04 heartbeat observer; "touch it once per minute WHILE the suite itself runs" | A heartbeat left by an earlier attempt could read as progress. Short stall timeouts (below 60s) are not protected, and tests would need to wait 60s. Heartbeat files accumulate. | Low | FIXED | The first poll records a baseline. `AW_SUITE_HEARTBEAT_SECONDS` exists for tests. The docs state that stall timeouts below 60s are unprotected. Files are removed at turn teardown, and the observer must avoid an import cycle. |
| PR-008 | LOW | IN-SCOPE | C. Architecture | E-05 | The plan did not say whether the statusline `ProgressPoller` changes, or that watcher and agent must derive ids from the same values. | Low | FIXED | Only the watchdog's pre-reap check is wired. The ids come from the values the launchers export. |
| PR-009 | LOW | IN-SCOPE | G. Right-sizing | E-06 bundled the test file with docs and CHANGELOG | One item held two deliverables. | Low | FIXED | Docs and CHANGELOG moved to new E-07/V-07, id from `aw ipd sync`. |
| PR-010 | LOW | IN-SCOPE | G. Contract / accuracy | gate; OQ-01 "Owner: none" and `-n = cpu_count // slots`; Spec sync quoted the phrase "no observed PROGRESS", which the spec does not contain | The execution contract was incomplete, OQ-01 had no owner, the formula did not match 0o0wt2's `max(2, …)`, and the spec citation was inaccurate. | Low | FIXED | Gate rewritten, including a STOP if Order 02's symbols are absent (a prerequisite STOP, not a scope STOP). Owner set to `plan author`, the formula corrected, and the spec citation fixed to the failure-class table. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Default slot count (OQ-01)? | `max(1, cpu_count // 6)`, as authored | 1 slot (queues seven drivers behind a 216s-median suite); unbounded (today's failure) | backlog `58x9mw` measurements; `AW_SUITE_SLOTS` override | yes |
| D-2 | Scrub `AW_SUITE_SLOT_HELD` in conftest? | No | Scrub it (breaks the nested guard for tests that spawn `aw suite` inside the held slot) | conftest import-time scrub pattern; E-03 reasoning | yes |
| D-3 | Wire the heartbeat into the statusline poller as well? | No, watchdog pre-reap check only | Add it to `ProgressPoller` too (more surface, and the statusline is not the kill decision) | `StallWatchdog._run` pre-reap check | yes |
| D-4 | What decides whether a slot is free? | The OS lock only | Holder-file pid liveness (races, PID reuse, cross-host) | `platform_lock` contract; integration-lock precedent | yes |
