# Review findings: plan hrdmfy

- Subject-Id: hrdmfy
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `ae98b0c55` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review (one info `IPD-Z602`); `--phase review-finalize` was clean after revision (three info `IPD-Z602`).

Re-verified (read-only probes; the plan's change was SIMULATED IN MEMORY by monkeypatching, no repository file
was modified):
- `run_state.check_transition`: `runnable -> running` LEGAL for `runtime`; `pending -> running`,
  `running -> running` illegal; `failed -> runnable` requires `correction_or_retry_planned`.
- `_run_start` wraps `get_runnable_steps`/`release_step`/`start_step` in `with engine.lease():`;
  `RunLedgerStore.append` takes `writer_lock` itself; `_run_record` has no lease and carries the comment
  "Running is ephemeral (not persisted), so it must be re-derived within this same process before the append".
- `runs resume` declaration `exit_contract=(0, 2, 5, 7)`, `command_class="read"`; the `runs next` comment
  paragraph (a) contrasts itself with `runs resume` "where plan `ck0vya` removed it".
- `cli.py` resume help body contains "(exit 3) when a side effect was interrupted mid-flight (unknown_outcome)".
- Spec `c4gd2h` is `implementing`; R19 text matches the plan's quote. `tzqvjn` is `graduated`,
  `Blocks-Release: next`, `Work-Kind: bug`.
- SIMULATION of E-01..E-04 (kind admitted, order-based replay, `start_step` appends, nested lock pass-through):
  fresh engine after `start_step` -> `running`, `detect_unknown_outcomes == ('S-01',)`; `resume` raises
  `UnknownOutcomeError`; `reconcile_unknown_outcome(..., 'performed')` clears it across a fresh engine; CLI
  `run start` exit 0 then `runs resume` exit 3; `run record` exit 0 then `runs resume` exit 0; `run record` on a
  pending step appends `step_started(1)` + `step_attempt(1)`; second `run start` exit 6; `runs next` after start
  exit 3; `run cancel` exit 0. `tests/test_run_recovery_cli.py`, `test_run_cli_declarations.py`,
  `test_run_cli_corruption_exit.py` -> `63 passed`; `test_runs_subdir_root.py`, `test_run_viewer.py`,
  `test_no_project_exit_is_cannot_run.py`, `test_runs_repo_alias.py` and corruption again -> `101 passed`.
- CONCURRENCY: two engines over one file racing `release_step`+`start_step` with the append in a SEPARATE lock
  acquisition from the read -> both `ok`, two `step_started(attempt=1)`. With read+check+append under ONE
  acquisition (held-append) -> one `ok`, one `IllegalTransitionError`, one record.
- The engine cannot re-start a failed step today (`release_step` from `failed` -> `PredicateUnsatisfiedError`;
  `plan_retry` appends `retry` without moving state).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Concurrency / correctness | `run_engine.RunEngine.start_step`; `run_cli._run_start` lease; concurrency simulation above | E-03 + E-04 as written read the step state and append `step_started` in separate lock acquisitions. Two concurrent `aw run start` processes both see `runnable`, both append, both believe they own the step: a silent double execution, the class of failure this plan exists to stop. Pre-existing (the lease only serialized per-process ephemeral state) but the plan was the moment to close it and claimed the lease removal was harmless. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now requires read+check+append under ONE `writer_lock` acquisition via a held-append entry point factored out of `RunLedgerStore.append` (not re-entrancy); `run_ledger_store.py` added to Scope-Paths; E-06 adds a concurrent-start row; V-03 demands the contrastive race demonstration. |
| PR-002 | MEDIUM | UNDER-SCOPE | G. Doc sync | `run_cli._run_record` comment "Running is ephemeral (not persisted)" | Becomes false after E-03; the plan corrects other "ephemeral" claims but missed this one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 corrects it (comment-only); V-04 demands before/after and the `step_started`+`step_attempt` evidence. |
| PR-003 | LOW | UNDER-SCOPE | G. Doc sync | `command_surface.py` `runs next` comment paragraph (a) | Contrasts with `runs resume` where 3 was removed; stale once restored. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 rewords it; V-05 demands before/after. |
| PR-004 | LOW | IN-SCOPE | E. Test feasibility | `release_step` from `failed` refuses; `plan_retry` does not move state | The interrupted-retry row cannot be produced through the engine today; an executor could stall or weaken it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 says to seed it by direct store appends; V-06 checks that. |
| PR-005 | LOW | IN-SCOPE | D. Behavior change disclosure | simulated `runs next` exit 3 / second `run start` exit 6 after a durable start | Cross-process `runs next` and a repeated `run start` change behavior; intended but undisclosed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Disclosed in E-03 as intended fail-closed consequences. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to make start atomic without re-entrant locks? | Held-append store entry point; `start_step` holds `writer_lock` across read/check/append | Keep the race (plan as written); make `writer_lock` re-entrant (plan already rejects, F-08); keep the CLI lease and pass a flag | Concurrency simulation above; `RunLedgerStore.append` body already runs entirely under `writer_lock` | yes |
| D-2 | Split E-04/E-05/E-06 for the info `IPD-Z602` density advisories? | No; each bundle is one change plus the comments it falsifies, verified by one V-item | Split into comment-only children | Advisory is `info`; original E-06 already carried it; the comment edits are meaningless without the code change | yes |
| D-3 | Is the "fix, not remove" decision (OQ-01) sound? | Yes, keep | Remove the dead arm | `c4gd2h` `implementing`, R19 and A6 text confirmed | yes |
