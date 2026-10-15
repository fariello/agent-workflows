# Review findings: plan eg6r2t

- Subject-Id: eg6r2t
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`fac51ff60`), so no snapshot was needed. `aw ipd lint --phase author` was clean before the review.

F-4 was re-derived with an independent probe under the gitignored `.aw/state/` (deleted afterwards). It drove the real `oc_runipd.run_queue` and `agy_runipd.run_queue` over the plan's one-item `state.json` with only `execute_item` stubbed:

- oc and agy: `executed` -> `(0, 'executed')`; `substantially-complete` -> `(1, 'substantially-complete')`; `failed-safely` -> `(1, 'failed-safely')`.
- With `mock.patch.object(runner_shared, "run_exit_code", return_value=0)`, all six cases returned 0, so a mutation of `runner_shared.run_exit_code` reaches both hosts.

F-1 and F-2 were confirmed: `git show 19313eed^:tests/test_rununify_run_queue.py` line 2246 has `class TheExitCodeReflectsTheRealOutcome(RunQueueCase)` with the three named tests, and the yuhl6o plan's E-02 row S-29 reads `RETIRE-UNGUARDED | 19313eed`. `runner_shared.EXECUTION_SUCCESS_STATES = {"executed"}` (runner_shared.py:30870) confirms the constant-pin half is now false.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G. Executability / lifecycle gate | `aw ipd lint --phase pre-transition`: `check.ipd-uncarried-obligation: 2 obligation(s) name no durable carrier: deferred row 1, deferred row 2` | Neither Deferred row carried a `Carrier`, `Carrier-Evidence`, or `Carrier-Declined` field, so the plan could not pass its own pre-transition gate after execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a reasoned `Carrier-Declined` to each row. Re-run of pre-transition lint shows only the expected `IPD-S404` not-yet-executed items. |
| PR-002 | MEDIUM | IN-SCOPE | Evidence (F-3) | `grep -rl substantially-complete tests` matches about 30 files; `run_queue(` appears in `test_finalize_sendback.py:1167`, `test_reaskscore_composed.py:271`, `test_oc_runipd.py:5446`, `test_agy_runipd_cli.py:1754`, and others | F-3's evidence claimed the status appears only in three test files. That is false, although the conclusion holds: no live test asserts `run_queue`'s return value for a `substantially-complete` item (callers discard it, drive resume paths, or test `runner_stop.deliberate_stop_exit_code` directly). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote F-3's evidence with the re-derived file set and why none of them guards the property. |
| PR-003 | MEDIUM | IN-SCOPE | E. Verification feasibility | old Required tests "inside a scratch run, monkeypatch `runner_shared.run_exit_code` (or the host's bound name)"; `oc_runipd.py:4570` and `agy_runipd.py:3773` `return runner_shared.run_exit_code(` | The mutation mechanism was hedged ("or the host's bound name") and E-03 was not required to fail under it. V-02 demanded no proof the mutation was reverted. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Named the mechanism (in-place `return 0` in `runner_shared.run_exit_code`, demonstrated reachable via the equivalent patch), required E-02 and E-03 to fail under it, and required an empty `git diff --exit-code agent_workflows/runner_shared.py` after revert. |
| PR-004 | LOW | IN-SCOPE | E. Test strength | E-03 text; E-01 harness text | E-03 did not assert the reloaded status was `failed-safely` (so the nonzero could come from another path), and E-01 did not pin temp-dir cleanup or say no other stub is needed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now asserts the reloaded status; E-01 requires `TemporaryDirectory` with `addCleanup` and only `execute_item` patched. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate`; `- Scope-Paths:`; OQ-01 `Owner: none` | The gate lacked `aw ipd begin`, the scope fence, the honesty rule, the never-tag rule, and conditional finalize ownership. The plan file was missing from Scope-Paths, and `Owner: none` is a placeholder for a question the author resolved. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the full contract and the plan path, and set the owner to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Carry the two deferred rows as backlog items or decline them? | `Carrier-Declined` with reasons | File backlog items (one would restore a P16-forbidden pin; the other duplicates existing coverage in `tests/test_run_exit_aggregate.py`) | AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; `tests/test_run_exit_aggregate.py` `TestRunExitAggregate` | yes |
| D-2 | How should the mutation check break the exit code? | In-place `return 0` in `runner_shared.run_exit_code`, reverted with `git checkout --` | Patching each host's name (neither host binds `run_exit_code` locally; both call it by module attribute) | `oc_runipd.py:4570`, `agy_runipd.py:3773`; review probe output above | yes |
| D-3 | Accept OQ-01 (host file is `tests/test_run_exit_aggregate.py`)? | Yes, as authored | Recreate `tests/test_rununify_run_queue.py` | That file already owns `run_exit_code` coverage (`tests/test_run_exit_aggregate.py:1` docstring) | yes |
