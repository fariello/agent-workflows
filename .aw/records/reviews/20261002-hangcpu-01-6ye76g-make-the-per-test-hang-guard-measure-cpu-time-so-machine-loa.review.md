# Review findings: plan 6ye76g

- Subject-Id: 6ye76g
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `b26231f7c` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review, and `--phase review-finalize` was clean after revision.

Re-verified (scratch probes under a tempdir, no production or test edit):
- `conftest.pytest_runtest_call` arms `_signal.setitimer(_signal.ITIMER_REAL, budget, 1.0)`; `_DEFAULT_TEST_TIMEOUT = 90.0`;
  `TestHangTimeout(BaseException)`; stand-down checks only `SIGALRM`. The rationale comment still says "the slowest
  fast-suite test is ~13s", now stale against F-02.
- `AW_TEST_TIMEOUT` appears only in `conftest.py`. Four `@pytest.mark.timeout` users confirmed (500, 300, 300 plus none other).
- `DEFAULT_STALL_TIMEOUT: float = 900.0` in `oc_runipd.py`, `agy_runipd.py`, `runner_shared.py`.
- Existing guard in a subprocess-driven probe (`-o addopts= -p conftest`, `AW_TEST_TIMEOUT=2`, 6s spin):
  serial `rc 1 ... 1 failed in 2.07s`, `-n 2` `rc 1 ... 1 failed in 3.10s`, guard message present both times.
- Parent CPU per wall second for subprocess loops: `true` 0.27, `git --version` 0.17, `python3 -c pass` 0.01.
- Dual-budget prototype, CPU 1s / wall 4s: `test_subprocess_loop_runaway` FAILED via `wall budget`; `/dev/zero`
  syscall spin FAILED via `CPU budget`; `@pytest.mark.timeout(5)` with 3s sleep PASSED when the marker floors the wall.
- `ITIMER_PROF` with a background thread spinning while main is in `join()`: handler ran only at 6.0s (end of spin).
- `mat9bt` pending, `- Scope-Paths: tests/test_statusline_behavior.py`, carries the "Do not raise `_DEFAULT_TEST_TIMEOUT`" prose.
- 15 executed plan files name the target nodeid (plan says "at least 12": consistent).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / D. Invariants | `conftest.py` rationale comment ("re-dispatched the same item forever"; `subprocess.run` under `already_landed_lanes`); review probe `python3 iters 116 wall 3.02 parent cpu 0.04` | The plan claimed a CPU budget catches runaways "strictly better" and framed the wall arm as only a deadlock catcher. The founding `8l8dgb` hang was a loop over child processes, which charges ~1% of wall to parent CPU, so the CPU arm cannot see it. Left unstated, an executor could set a near-stall ceiling or later delete the wall arm. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-13; corrected Goal, OQ-01, E-03, E-07, V-03, V-07, the approval paragraph and execution contract: the ceiling is load-bearing and must stay well under the 900s stall budget. |
| PR-002 | HIGH | IN-SCOPE | D. Anti-regression | `tests/test_exit_contract_conformance.py` `@pytest.mark.timeout(500)` docstring "185.650s serially"; OQ-02 | OQ-02 resolved markers as CPU-only and "safe either way". Those tests spend their budget on WALL, so with a global wall ceiling below 300/500 the wall arm would kill them: the marker would become harder to satisfy, the exact incompatibility E-04 forbids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-14; E-04 now specifies the marker sets CPU AND floors the wall at `max(ceiling, n)`, with optional `wall=`; prototype demonstrated (`PASSED test_marker_raises_wall_ceiling`). OQ-02 rewritten, owner set to plan reviewer. |
| PR-003 | MEDIUM | IN-SCOPE | G. Executability | E-04 "there is a way to address the wall ceiling separately" | Override semantics were left to the executor: no env var name, no meaning for `0` across two arms, no marker syntax. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 pins `AW_TEST_WALL_TIMEOUT`, `AW_TEST_TIMEOUT=0` disables both arms, `AW_TEST_WALL_TIMEOUT=0` disables wall only, invalid values fall back; marker registration text updated. V-04 now demands each by run. |
| PR-004 | MEDIUM | UNDER-SCOPE | E. Testing | E-05 class list; F-07 | E-05 omitted the one case that distinguishes `ITIMER_PROF` from `ITIMER_VIRTUAL` (a syscall-bound spin), so V-05's suggested `ITIMER_VIRTUAL` mutation would not be detected. Also no subprocess-loop case and no marker-raises-wall case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added syscall-bound (`/dev/zero` reads, measured `user 0.06 sys 1.91`), subprocess-loop, and marker-floor cases to E-05/V-05; V-05 now names three mutations and which case each must fail. Added the demonstrated subprocess-driving mechanism to E-05. |
| PR-005 | MEDIUM | IN-SCOPE | G. Live-artifact criterion | V-06, Required tests, POST-GATE LIFECYCLE cite F-12 `3 failed, 4624 passed, 2 skipped` as the bar | A live suite count measured at authoring served as the reconciliation bar; HEAD has already moved. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01/V-01 now capture the pre-edit failing nodeid set; V-06 reconciles against it, attributes new failures by isolated rerun, and adds the target's CPU-to-budget ratio as load-invariant evidence since one passing run is weak for a flaky test. |
| PR-006 | MEDIUM | IN-SCOPE | G. Execution contract | POST-GATE LIFECYCLE "Run ... `aw ipd finalize` after every `V-*` reads `pass`" | Unconditional finalize instruction; under `aw oc run` the runner owns the transition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten with conditional runner/executor ownership; no hand `git mv`. |
| PR-007 | LOW | IN-SCOPE | G. Scope-fence wording | Execution contract and Deferred bullet "STOP AND REPORT rather than widening scope" | Stop directive for an out-of-scope product-defect case contradicts the 2026-09-01 scope-fence ruling. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with file via `aw backlog new`, justify any out-of-scope edit with `--scope-reason`. The E-01 stop (premise refuted) is a genuine-unsafe stop and is kept. |
| PR-008 | LOW | UNDER-SCOPE | D. Invariants | Review probe `PROF repeating, main blocked in join while bg spins 6s: handler runs at [6.0]` | Python delivers the CPU handler in the main thread only, so a CPU overrun from a background thread is acted on late when main is blocked in C. Undocumented in the plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-15 and required E-07/V-07 to document it as a further reason the wall arm stays. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What does an existing `@pytest.mark.timeout(n)` mean under a dual budget? | CPU budget `n` AND wall floor `max(ceiling, n)`; optional `wall=` keyword | CPU only (as authored; breaks wall-heavy markers under a low ceiling); wall only (defeats the plan for marked CPU-heavy tests) | `tests/test_exit_contract_conformance.py` docstring "185.650s serially"; prototype `PASSED test_marker_raises_wall_ceiling` | yes |
| D-2 | How is the wall ceiling addressed per run? | New `AW_TEST_WALL_TIMEOUT` env var | Overload `AW_TEST_TIMEOUT` with a `cpu,wall` syntax (less discoverable); no env override (no escape hatch) | `AW_TEST_TIMEOUT` has no consumer outside `conftest.py` (repo grep), so adding a sibling breaks nothing | yes |
| D-3 | What does `0` disable? | `AW_TEST_TIMEOUT=0` / marker `0` disables both arms; `AW_TEST_WALL_TIMEOUT=0` disables wall only | `AW_TEST_TIMEOUT=0` disables CPU only (silently changes today's "0 disables the guard" meaning) | `conftest.pytest_configure` marker text "0 disables"; `conftest.py` comment "`AW_TEST_TIMEOUT=<seconds>` (`0` disables)" | yes |
| D-4 | Is the wall ceiling only a deadlock check? | No: it is the sole defense against subprocess-bound runaways and must stay well under 900s | Treat it as a formality and set it near the stall budget | Probe F-13; `DEFAULT_STALL_TIMEOUT: float = 900.0` | yes |
