# Review findings: plan u3enlv

- Subject-Id: u3enlv
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `6f3cbaf05`. The plan was committed and unchanged, so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review and `--phase review-finalize` clean after.

Re-verified at review HEAD by driving the real functions:
- F-01 reproduces exactly: `FAILED` -> `tool_call_from_event` `None`, `commands=[]`, `missing_command_count=0`, verdict `indeterminate`/`missing-command-text`, dashboard `tool_calls 0`, renderer `'❯ bash:  python3 -m pytest'`. `DONE`/`ERROR` as stated. `ACTIVE` and `CANCELED` -> not observed, renderer `None`.
- Gates: `run_dashboard._agy_line` `if state not in ("DONE", "ERROR")`; `verifier_corroboration.tool_call_from_event` `(state != "DONE" and state != "ERROR") or stype != "tool"`, `is_error = state == "ERROR"`; `agy_runipd.render_agy_event` two `("DONE", "ERROR", "FAILED")` gates; `agy_runipd._AGY_STATE_TO_STATUS` `"FAILED": "error"`.
- `verifier_corroboration` imports stdlib only; `run_dashboard` already imports `tool_call_from_event` from it. `agy_runipd` does not import it today; adding the import creates no cycle (it imports nothing from `agent_workflows`).
- `DASHBOARD_SCHEMA_VERSION = 3`, `test_dashboard_schema_version_is_3`; last decision `### D162`.
- `n8we3u` is `approved` and also bumps the version 3 -> 4 and takes D163; it defers `8fiybc` with `- Carrier: 8fiybc`.
- Mixed `FAILED` + `DONE` log with a matching claim: `corroborated`, `observed_count=1` PRE-fix.
- Widened reader search: `agy_view.format_record`, `run_viewer`, `stall_progress`, `runner_shared` text collector, `agy_run._progress_messages` carry no terminal-state gate to reconcile.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A. Correctness (cache) | `run_dashboard._StatsCache.__init__` "raw.get(\"schema\") == DASHBOARD_SCHEMA_VERSION"; `n8we3u` E-04 "Bump ... from 3 to 4" | F-06 claimed "either order works" with the merge gate reconciling the overlap. If both lanes are cut from the same base, both write `= 4` and `_is_4`; git merges identical hunks with no conflict, so the second change ships with no version bump and stale cached counts are served for unchanged logs. No test catches it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `executed:n8we3u` to `Item-Dependencies` (n8we3u is approved, so this costs nothing); E-04 now bumps from the live value (4 -> 5); E-09 takes the next free D-number; E-01 pastes both; gate prerequisite updated; F-06 rewritten. |
| PR-002 | MEDIUM | IN-SCOPE | E. Vacuous test | review measurement: mixed log `corroborated`, `observed_count=1` pre-fix | E-06's mixed `DONE`+`FAILED` case asserted only `corroborated`, which already holds before the fix, so it cannot fail pre-fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The case now also asserts `observed_count == 2`, with the reason recorded. |
| PR-003 | MEDIUM | IN-SCOPE | E. Test oracle | E-08 "equals `state in AGY_ERROR_STATES`" | The parity test derived its expectation from the constants under test, so a wrong constant would redefine the oracle and still pass. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-08 now requires a literal per-state expectation table in the test. |
| PR-004 | LOW | IN-SCOPE | E. Mutation proof | V-08 reverted only the dashboard gate | The divergence proof did not cover the corroboration gate, which is the other analytics reader. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-08 now reverts each analytics gate in turn. |
| PR-005 | LOW | IN-SCOPE | Evidence accuracy | `CorroborationVerdict` fields: `verdict`, `reason_code`, ... (no `reason`) | E-01, E-06 and V-03 named a `reason` field that does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Renamed to `reason_code` everywhere. |
| PR-006 | MEDIUM | UNDER-SCOPE | G. Carrier discipline | `aw check all`: `check.ipd-uncarried-obligation` (error) "deferred row 1 ... row 6" | No Deferred row named a carrier, so `aw check` reported an error on this plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rows now carry `Carrier: n8we3u`, `Carrier: iuhx9d`, or `Carrier-Declined:` with reasons. `aw check` now reports only the info-level lifecycle note. |
| PR-007 | LOW | IN-SCOPE | G. Execution contract | Approval gate | The gate did not state runner ownership of `aw ipd begin` or the hand-run begin step. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added conditional begin/finalize ownership. |
| PR-008 | LOW | IN-SCOPE | G. Scope check | Scope check "Under-scope: none known" based on one literal search | The search covered only the literal tuple, not every `step_update` reader. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Widened at review; the result is recorded in the Scope check (no further readers need changing). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to stop a silent double-bump collision with `n8we3u`? | Add `executed:n8we3u` edge | Keep "either order" (unsafe, see PR-001); fold the bump into one plan (crosses another Set member's scope) | `n8we3u` `- Status: approved`; `_StatsCache.__init__` schema gate | yes |
| D-2 | Keep OQ-01 (FAILED equals ERROR) as resolved by the author? | Keep | Escalate to the maintainer | `agy_runipd._AGY_STATE_TO_STATUS` "FAILED": "error"; the verdict is observational (D160), so a wrong call is cheap to reverse | yes |
