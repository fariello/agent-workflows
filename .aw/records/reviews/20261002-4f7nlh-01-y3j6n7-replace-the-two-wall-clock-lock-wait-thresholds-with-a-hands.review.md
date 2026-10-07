# Review findings: plan y3j6n7

- Subject-Id: y3j6n7
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `a2b959f5a`. The plan was committed and byte-identical to the lane input, so no pre-review
snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and
`--phase review-finalize` reported conforming after revision.

Re-verified:
- Both tests exist as quoted: `test_two_process_lock_wait_succeeds` (child `time.sleep(1.0)`, `assertGreater(elapsed, 0.7)`,
  `for _ in range(50)` spin) and `test_finalize_lock_WAITS_for_a_short_lived_live_holder` (thread `sleep(0.5)`,
  `assertGreaterEqual(waited, 0.4)`, `assertLess(waited, 5)`, provenance docstring).
- `acquire_finalize_lock(..., timeout, sleep, now)` passes `timeout=budget` explicitly to `contention_wait.wait_until`,
  which calls `try_once()` before its first `sleep`. `FINALIZE_LOCK_POLL_SECONDS = contention_wait.POLL_SECONDS = 0.1`.
- Scratch probe (`.aw/state/probe/`, gitignored) using the handshake against a live holder: unmutated
  `err None polls 2 own True holder_alive True`. Mutation via `functools.partial(wait_until, timeout=0)`:
  `err None polls 2` (NO-OP, the explicit keyword wins). Mutation via a lambda closing over the patched name: `RecursionError`.
  Mutation via default-arg capture `lambda *a, _o=CW.wait_until, **k: _o(*a, **{**k, "timeout": 0})`:
  `err TransactionLockError polls 0`. F-06's sensitivity claim holds once the mutation is done correctly.
- `grep -rln "monotonic()" tests/*.py`: eight modules. `tests/test_platform_lock.py:149` `assertLess(elapsed, 5.0, ...)` confirmed.
- Backlog `4f7nlh`: `graduated`, `Blocks-Release: next`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Verification feasibility | `agent_workflows/ipd_lifecycle.py:608` `contention_wait.wait_until(..., timeout=budget, ...)`; scratch probe results above | The mutation check (V-02/V-03's central bar) was described only as "timeout=0 via a throwaway copy or temporary local edit". The obvious in-process forms are a silent NO-OP (`partial`) or crash (`RecursionError`), so an executor could record a false "mutation fails" or "mutation passes"; editing production code also conflicts with the empty `agent_workflows/` scope. | all Low | FIXED | Validation names the exact in-process `mock.patch.object` wrapper with default-arg capture, both traps, measured results, and forbids a test-side `timeout=0`; V-02/V-03 and the gate updated. |
| PR-002 | MEDIUM | IN-SCOPE | D. Anti-regression | `tests/test_ipd_lifecycle_cli.py` `assertLess(waited, 5, "it must take the lock as soon as the holder releases it")` | E-03 listed assertions to keep but silently dropped the "take it as soon as released" upper-bound property, weakening the sibling test. | all Low | FIXED | E-03 replaces it with a poll-count bound (no more than one sleep after release); explicitly not copied to E-02 where the release is asynchronous; V-03 demands it. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing / reachability | E-02 "assert ... `child.poll() is None`" after acquire | After acquire returns the child has released and exited, so `child.poll() is None` would be false and the assertion unsatisfiable; and the injected `sleep` must really sleep in a two-process test. | all Low | FIXED | E-01 requires a real-sleeping callable, no injected `now`, and per-poll liveness samples; E-02/V-02 assert those samples instead. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | Approval gate | No runner-vs-hand finalize ownership, no `aw ipd begin` lane caveat, no scope-fence declaration, no hands-off for the release-gated `4f7nlh`. | all Low | FIXED | Gate paragraphs added. |
| PR-005 | LOW | UNDER-SCOPE | G. Traceability | E-04 "record it in the Findings section as a follow-up" | A follow-up recorded only in plan prose is untracked (AGENTS.md backlog rule), and the search was underspecified. | all Low | FIXED | E-04 names the eight-module `monotonic()` search (re-derived at execution) and requires filing via `aw backlog new`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to perform the mutation check without editing production code? | In-process `mock.patch.object` of `ipd_lifecycle.contention_wait.wait_until` with default-arg capture | Temporary production edit; `functools.partial`; test-side `timeout=0` | Scratch probe results recorded above | yes |
| D-2 | Keep the "taken promptly" property in E-03? | Yes, as a poll-count bound | Drop it (as authored); keep the wall-clock `assertLess` | GUIDING_PRINCIPLES P16 "Never weaken an assertion"; sibling releases synchronously in-callable | yes |
