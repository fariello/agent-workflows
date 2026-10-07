# Review: Enforce verifier session independence and verifier state authority through verify_roles at the one shared verify site

- Subject-Id: eow7p4
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `0b1646728` in review lane `review-sweep-run-20261007T165410Z-456709`. Target plan
committed and byte-identical to the lane input; pre-review snapshot skipped. `aw ipd lint --phase author`
clean. Dependency `32jpl1` is executed.

Re-verified: `_v_session` occurs once in `runner_shared.py` (the `spawn_verifier` destructuring);
`attempt["session_id"] = session_id` is persisted in `execute_item_core`; `agy_verifier.assert_distinct_sessions`
exists (takes `SessionIdentity` objects); `verify_roles.ROLE_CONTRACTS['verifier'].state_authority` is the three
stated edges; `run_state.TRANSITION_RULES` authorizes both `verifying -> *` edges for `{verifier, runtime}`;
`validate_transition` and `check_transition` both exist; `ACTION_CAPABILITY_REQUIREMENTS` still one empty row;
`VERIFY_DISP_UNVERIFIED`, `VERDICT_REFUSAL_CODE_DECLINED`/`_UNREADABLE`, `verify_absence_text`,
`render_stream.record_refusal`, `integration_is_earned` all resolve. E-01, E-02 and E-04 are sound.

E-03 does not work as written. Measured in-process:
- `map_driver_status_to_run_state("running")` -> `running`; there is no `verifying` entry in Order 01's table, and
  the item's status at the verify site is `"running"` (set at the top of `execute_item_core`; no write between
  there and `spawn_verifier`).
- `validate_transition("running", "verified", "verifier")` -> `ST-ILLEGAL-TRANSITION`.
- `find_runtime_reachability_path("running", "verifying")` -> `['running', 'performed', 'verifying']`.
- `map_verdict("BLOCKED").state` and `map_verdict("NOT CONFORMING").state` -> `fail-verify` (a driver token, not
  a `run_state` position).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / G. Executability | E-03 "USE SIBLING ORDER 01's TRANSLATION for the SOURCE position"; `runner_shared.map_driver_status_to_run_state("running") == "running"`; `run_state.validate_transition("running","verified","verifier")` -> `ST-ILLEGAL-TRANSITION`; `find_runtime_reachability_path` returns `['running','performed','verifying']` | Following E-03 literally makes the report-only authority check flag EVERY verdict unauthorized, a permanent false positive that would also poison the evidence E-03 says is needed to promote it later | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now composes Order 01's two symbols: translate, then `find_runtime_reachability_path(..., "verifying")`, then validate `verifying -> target` as `verifier`, recording the path; absent path recorded as the finding. V-03 demands a recorded path and verdict for three verdicts |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness | `map_verdict("BLOCKED").state == "fail-verify"` | A `BLOCKED` verdict's target is not a `run_state` position, so `verifying -> fail-verify` would read as an illegal edge | All Low | FIXED | E-03 normalizes the target through `map_driver_status_to_run_state` (`fail-verify` -> `correction_required`) or records "no run_state edge"; Expected outcome and V-03 cover `BLOCKED` |
| PR-003 | MEDIUM | UNDER-SCOPE | G. Execution contract | Gate had commit/honesty basics but no scope-fence declaration, no OQ status, no conditional lifecycle ownership, and said "all four `V-*` items" while the plan has five | Executor lacks the runner-versus-hand finalize rule; V-05 could be skipped | All Low | FIXED | Added OQ status, declaration-only fence with genuine-unsafe stop cases, hard-MUST paste rule, runner / hand `aw ipd finalize` split; "four" -> "five" |
| PR-004 | LOW | IN-SCOPE | G. Evidence | OQ-02 carrier `s8veyk`: backlog shows `Graduated-To: hostcapgate`; plan `y9m1ya` adds the execute row | OQ-02 read as unowned policy work | All Low | FIXED | OQ-02 notes the ownership by `hostcapgate` |
| PR-005 | LOW | IN-SCOPE | G. Evidence | Conventions: "37355 lines" (now 41024 by `wc -l`); addopts quoted as `-m 'not slow'` (actual `'not slow and not livecorpus'`) | Stale facts | All Low | FIXED | Both corrected |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001: how should E-03 obtain the `verifying` source position? | Compose Order 01's `map_driver_status_to_run_state` with Order 01's `find_runtime_reachability_path` to `verifying`, recording the path | Hard-code source `verifying` at the verify site (a local re-derivation the plan forbids); add a `verifying` driver status (out of scope, changes the vocabulary E-05(c) pins); defer E-03 | Both symbols are `32jpl1` E-01/E-03 (`runner_shared.py` "runwire (`32jpl1`) E-03 / D-1: Walk run_state.get_legal_transitions"); demonstrated in-process returning `['running','performed','verifying']`, and `validate_transition("verifying","verified","verifier").ok` and `("verifying","correction_required","verifier").ok` both True | yes |
