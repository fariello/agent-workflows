# Review findings: plan 9380pe

- Subject-Id: 9380pe
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`917cea8be`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize --agent` clean after revisions.

Re-verified at review HEAD `b17a9d4b3`:
- `runners_monitor.run_table_dashboard` (line ~552): `stop_cleanly(_sig, _frame)` raises `SystemExit(0)`, registered for SIGINT and SIGTERM, `except (KeyboardInterrupt, SystemExit): return 0`, `finally` writes `pwatch.LEAVE_ALT_SCREEN` only when interactive; no handler restore. Matches F-01/F-03.
- `runners_monitor.main` delegates `--tree` to `pwatch.main`; `pwatch.main` delegates `--runners --table` to `runners_monitor.run_table_dashboard` (pwatch.py ~973). Matches F-02/F-06.
- Subprocess probe with isolated `--repo` tmp dir: `runners` SIGINT 0, SIGTERM 0; `pwatch --runners --table` SIGINT 0, SIGTERM 0; first line seen, ~0.5s each. Matches F-01/F-04.
- `ww744p` is `approved` in `pending/`; `tests/test_pwatch_signal_exit.py` absent; dependency edge live. Last `DECISIONS.md` entry is already `D168`.
- `command_surface.CommandDeclaration.exit_contract` comment (measurement 3) and `tests/test_exit_contract_conformance.py` docstring name `pwatch` returning 0 on signals; `ww744p` E-05 rewrites both.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E. Testing | E-04 (1)-(3): "reading the first line from stdout" via `stdout.readline()` | An unbounded `readline()` blocks forever if the dashboard never prints a frame (e.g. a regression in startup), hanging the xdist worker; `wait(timeout=10)` only bounds the post-signal wait. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires a bounded first-line read (select with 10s timeout, kill and fail), `sys.executable`, repo-root cwd, POSIX skip; V-04 demands the hunk. |
| PR-002 | LOW | IN-SCOPE | A. Correctness | Python `signal.getsignal` returns `None` for non-Python handlers; `signal.signal(sig, None)` raises `TypeError` | E-03's unconditional restore could raise inside `finally` and mask the return code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 restores only non-`None` saved handlers. |
| PR-003 | LOW | IN-SCOPE | Evidence | `DECISIONS.md` last heading `### D168` | E-06's hint "D168 at authoring" is already taken. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Hint corrected; re-read rule kept. |
| PR-004 | LOW | UNDER-SCOPE | D. Invariants / doc truth | `command_surface.py` exit_contract comment measurement 3; `tests/test_exit_contract_conformance.py` docstring; `ww744p` E-05 | After `ww744p` rewrites these to enumerate signal codes per verb, they may cite the runners dashboard's `0` on SIGTERM, which E-02 makes false; the plan (F-05) checked only the pre-`ww744p` text. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 (c) re-greps after `ww744p` and updates the one sentence as a justified out-of-scope edit if present; V-01 demands the output. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | Gate "POST-GATE LIFECYCLE" | Said the runner sets backlog `uu4rfe` to `graduated` on verification (it is already graduated) and did not state that the scope fence is a declaration with `--scope-reason`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected the backlog sentence; added the scope-fence nature paragraph, keeping the E-01 safety GATE stops. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Accept OQ-01 (SIGTERM -> 143, SIGINT -> 0, return not re-raise)? | Accept as authored | Keep 0; SIG_DFL re-raise | F-02 survey; `ww744p` OQ-01; D162 | yes |
| D-2 | Handle a possibly stale D162 comment after `ww744p`? | Conditional one-sentence fix as justified out-of-scope edit | Add the two files to Scope-Paths unconditionally; ignore | `ww744p` E-05 scope; fence-is-declaration rule | yes |
