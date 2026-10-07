# Review findings: plan urv602

- Subject-Id: urv602
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Re-review in lane `review-sweep-run-20261007T165339Z-456282` at HEAD `b68a196e9`. The plan was committed and byte-identical to the sealed lane input rev-4 (sha256 `f9bfb1ba...8210`). `- Kind: child`. `aw ipd lint --phase author` was conforming. The prior round was on 2026-10-01 (PR-001 BLOCKER through PR-006, all fixed).

Re-measured at this HEAD, and all of the following hold:
- `run_lock` writes `pid={os.getpid()} started={utc_now()}`, with no host.
- `acquire_repo_scoped_lock` writes `{holder_label} pid=...`.
- `LOCK_RECORD_PID_RE` is `(?<!\w)p?id=(\d+)`.
- `'interrupted' in TERMINAL_STATES` and in `TERMINAL_STATES_CANONICAL` are both True.
- `KNOWN_ITEM_STATUSES` lists `queued`/`running`/`interrupted`/`integration-deferred`/`merge-retry` under "# in-flight / recoverable".
- `peer_drivers` has an `except Exception: ... return []` arm with the comment "the caller never REFUSES".
- `worktree_lease._owner_is_live` has the foreign-host arm.
- `run_viewer` defines `HOLDER_LIVE/NONE/UNKNOWN`.
- The three Order 02 entry points (`begin`, `finalize`, `retire_orchestrator`) exist.
- Set-difference census: every `KNOWN_ITEM_STATUSES` token outside the allowlist is in `TERMINAL_STATES`, and the allowlist intersects `TERMINAL_STATES` only at `interrupted`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A correctness / safety | `platform_lock.pid_alive` "NEVER `os.kill(pid, 0)` ON WINDOWS ... KILLS the process it asks about"; plan Goal "a `kill(pid, 0)`-shaped question"; E-05 names no process probe | The plan never names the process-existence primitive. An executor following its framing could call `os.kill(pid, 0)`, which on Windows terminates the live runner the gate is asking about. `pid_alive`'s `None` result and an unparseable pid also had no specified verdict. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 mandates `platform_lock.pid_alive` and forbids `os.kill`, mapping `None` and a missing pid to UNDETERMINABLE. The E-05 outcome table adds those inputs, and V-06 adds arm (12). |
| PR-002 | MEDIUM | IN-SCOPE | A correctness / rationale | `KNOWN_ITEM_STATUSES` minus the allowlist is entirely in `TERMINAL_STATES`; `runner_shared` "a bare `resume` does NOT re-queue a dependency-blocked item" | Excluded statuses such as `dependency-blocked` and the `fail-*` family are re-queueable through `--retry-incomplete`, but the plan never said why NOT HELD is right for them. That leaves the allowlist open to an unprincipled widening or narrowing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 records the rationale: an explicit operator retry goes through the gated `begin`. The rationale goes into the allowlist comment. |
| PR-003 | MEDIUM | IN-SCOPE | Principles / honest deviation | `dvonrn` D2 "a status that is NOT finished (not in TERMINAL_STATES)" | The allowlist correctly departs from the maintainer-ruled D2 parenthetical, but the plan never presented this as a departure from a ruling. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 requires the departure to be named in the predicate comment and in V-04. |
| PR-004 | LOW | IN-SCOPE | E test completeness | V-06 "All ELEVEN"; mutation list in Required tests | The arm count and the mutation set did not cover the review-added arms (`interrupted` drop, discovery `[]`, pid_alive None). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Now twelve arms. Two mutations added: dropping `interrupted`, and returning [] on discovery failure. |
| PR-005 | LOW | IN-SCOPE | Consistency | E-04 "Build it from `peer_drivers` for discovery"; conventions "E-04 must reuse `peer_drivers`" vs E-05 "do not call `peer_drivers` and treat an empty list as absence" | The plan both mandated and forbade reusing `peer_drivers`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both sites now say: reuse `runs_repo_root`/`driver_holder_state`, or a failure-surfacing variant, per E-05. |
| PR-006 | LOW | IN-SCOPE | G execution contract / evidence | gate "STOP: that is Order 02's work"; Required tests "the run-viewer and runner-shutdown surfaces" | The gate's STOP on an out-of-scope behavior edit read as a scope-fence stop. Also, no runner-shutdown test file exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reworded to "do not make that change", as a deliverable property. `tests/test_run_viewer.py` is named, and the runner-shutdown tests are located by grep. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should re-queueable failure statuses (`dependency-blocked`, `fail-*`) count as HELD? | No, NOT HELD, with the rationale recorded | Include every re-queueable token, which would make any failed run block its plan forever | `runner_shared` "a bare `resume` does NOT re-queue a dependency-blocked item"; `--retry-incomplete` dispatch passes through `aw ipd begin` (Order 02 gate) | yes |
| D-2 | How should the test produce `pid_alive` returning None? | Allow monkeypatching `platform_lock.pid_alive` as the one seam | Real OS arrangement (not producible on demand) | `pid_alive` docstring: None only on unclassifiable OSError | yes |
