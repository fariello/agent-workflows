# Review findings: plan k6twdf

- Subject-Id: k6twdf
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`82baafe94`), so no snapshot was needed. `aw ipd lint --phase author` was clean before the review. After the review, `--phase review-finalize` is clean and `--phase pre-transition` reports only the expected unexecuted-state S404 items.

Evidence measured at review, using a prototype of the E-01 helper under gitignored `.aw/state/` (deleted afterwards):

- The four pty cases (no-color, control, TERM=dumb, a non-matching pattern) all gave `4 passed` in about 1s.
- Five consecutive `-n 4` runs each gave `4 passed, 4 warnings`. The warnings are the expected fork `DeprecationWarning`.
- A non-matching pattern still prints a colored header, so `--once python` emits ANSI regardless of which processes exist. The control is therefore not host-dependent.
- Mutation: with `color_enabled = term.should_color(sys.stdout)` in a scratch copy, the first attempt passed 4/4 because the child imported the cwd repo package despite `PYTHONPATH`. With the child's cwd set to the copy, the result was `1 failed, 3 passed`, and the failure was the flag test.
- The deleted original (`19313eed^:tests/test_pwatch.py` `ColorDecisionOnARealTtyTests`) matches the planned helper and tests.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Cross-platform correctness | E-01 "Skip ... when `pty` is unavailable (non-POSIX)"; `agent_workflows/pwatch.py` `read_processes` raises "this script requires Linux"; `.github/workflows/tests.yml` `os: [ubuntu-latest, macos-latest, windows-latest]` | macOS has `pty` but no `/proc`. A POSIX-only skip would run the tests there and fail: pwatch returns 1 with no ANSI, so the control fails. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The skip is now `skipUnless(sys.platform.startswith("linux"))` plus a guarded `import pty`. F-06 records the evidence. |
| PR-002 | MEDIUM | IN-SCOPE | E. Non-vacuity of negative assertions | E-02 asserted exit 0 only on the flag test; E-03 asserted only "ANSI absent" | A crashed or silent child satisfies "ANSI absent" vacuously. The TERM=dumb test had no liveness check at all. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Every pty case now asserts exit 0 and `b"pwatch:"` present. |
| PR-003 | MEDIUM | IN-SCOPE | E. Mutation-check feasibility | Probe: the child resolved `<repo>/agent_workflows` from its cwd ahead of `PYTHONPATH` | The helper did not pin the child's cwd. Run from another directory, it can import a different package than the one under test (in this environment an editable install points at another checkout), so the mutation check could miss the change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The child now runs `os.chdir(repo_root)` before `execve`. The mutation check is ordered in place within E-02, and V-02 demands that the other tests still pass under the mutation. |
| PR-004 | MEDIUM | UNDER-SCOPE | G. Lifecycle / durable carrier; F. Honest docs | `aw ipd lint --phase pre-transition`: `check.ipd-uncarried-obligation: 3 obligation(s) name no durable carrier: deferred row 1, deferred row 2, OQ-01`; `pwatch.main` comment "no live guard currently asserts this pty behavior" | The plan could not finalize. Executing it would also make the production comment false. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `Carrier-Declined` to both deferred rows. Resolved OQ-01 by adding E-04/V-04 (a comment-only edit, ordered after the mutation revert) and added `agent_workflows/pwatch.py` to Scope-Paths. The S404-only result confirms the carrier rule clears. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract and baseline | Gate said "Move to `.aw/records/plans/executed/`"; V-03 demanded `N passed` with no failures and no baseline | The gate implied a hand move, omitted runner/hand finalize ownership and the honesty rule, and had an absolute suite bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate with the full contract. E-01 records a baseline, and V-01/V-03 compare against it. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the stale pwatch comment be updated in this plan (OQ-01)? | Yes, as a comment-only E-04 | Keep it deferred (fails `check.ipd-uncarried-obligation` and leaves a false comment); file a backlog item (overhead for a one-line comment) | pre-transition lint output; `pwatch.main` comment text | yes |
| D-2 | Which skip predicate? | Linux only | POSIX (`pty` importable), which fails on macOS CI | `read_processes` `/proc` requirement; `tests.yml` matrix | yes |
