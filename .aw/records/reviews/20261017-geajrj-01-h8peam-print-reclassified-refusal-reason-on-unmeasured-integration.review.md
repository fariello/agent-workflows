# Review findings: plan h8peam

- Subject-Id: h8peam
- Subject-Type: ipd
- Reviewed-At: 2026-10-18
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `08fa69666`. The plan was committed and byte-identical to
the sealed lane input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent`:
`clean`, 0 findings. After revisions `--phase review-finalize --agent`: `clean`, 0 findings. Not an
orchestrator.

Verified at review by a scratch prototype (gitignored `.aw/state/`, not committed) that drove the real
code paths on HEAD `08fa69666`:
- `oc_runipd.execute_item` and `agy_runipd.execute_item` with a budget-only revalidation red: ladder
  kind `merge-unchecked`, status `merge-retry`; stderr line `... NOT integrated to main (merge-retry):
  [aw-integration-cause=gate-combined-red] integration gate did not pass (integration_failed_combined_red) ...`;
  `item["refusal"]["reason"]` = `the post-merge revalidation measured the merged tree and it was RED and the
  run's correction budget is exhausted (0 of 2 retries spent): ...`; `item["integration_deferral"]` =
  `integration refused because the post-merge revalidation COULD NOT MEASURE ...`.
- `runner_shared.integrate_retired_lane` with an unmeasured stub: stderr `... retired on lane ... NOT
  integrated to main (merge-retry): [aw-integration-cause=gate-combined-red] ...`.
- `runner_shared.reattempt_deferred_integrations` with `ask=True, interactive=True`, limit 0: captured
  question `? lane abc123 cannot integrate: [aw-integration-cause=gate-combined-red] ...`.
- Measured control (`retry_budget=0`, failing id): status `fail-merge`, `measured: True`,
  `integration_deferral` contains `integration_failed_combined_red`.
- Whole-module prototype runtime 7.1s.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric G (executability), evidence | `agent_workflows/runner_shared.py` `integrate_retired_lane` "retired on lane {wt_handle.branch} but NOT integrated" | The plan named `land_retired_lane_turn` in E-01, E-03, findings and scope; no such symbol exists anywhere in the repository. The retired-lane line lives in `integrate_retired_lane`. An executor could not locate the edit or the test target. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Renamed throughout; retired-lane edit split into its own E-02; F-4 re-cited with measured output. |
| PR-002 | HIGH | IN-SCOPE | Rubric E (tests detect the bug) | `agent_workflows/runner_shared.py` `decide_integration_deferral` "could not MEASURE the merge result"; prototype stderr | The tests asserted `could not MEASURE` in stderr. Today's stderr ALREADY contains that lowercase phrase on the `-> integration DEFERRED ...` verdict line, so test 1 and 2 would pass before the fix and could not detect a regression. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now discriminates on uppercase `COULD NOT MEASURE` and asserts on the specific "NOT integrated to main" line; V-04 requires a pre-change run showing the unmeasured cases fail. F-9 added. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric B/F (leak of internal token) | `agent_workflows/runner_shared.py` `read_integration_cause` "THE TOKENS ARE STRIPPED, so nothing an operator reads carries one"; prototype stderr | The fallback `or integ_reason` / `or reason` reintroduces the `[aw-integration-cause=...]` token the module says must never reach an operator; the measured stderr and prompt carry it today. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Every fallback now goes through `read_integration_cause(...)[2]`; tests assert absence of `[aw-integration-cause=`; invariant I-2 added. |
| PR-004 | MEDIUM | IN-SCOPE | Evidence accuracy | `agent_workflows/runner_shared.py` `execute_item_core` `elif cause == INTEGRATION_CAUSE_GATE_COMBINED_RED:` "measured the merged tree and it was RED" | F-3 understated the defect: the refusal record does not merely carry the raw gate text, it asserts "measured the merged tree and it was RED" for an unmeasured item. The test for the refusal reason did not forbid that phrase. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-3 rewritten with the measured value; E-04 case 1 forbids `it was RED` in `item["refusal"]["reason"]`. |
| PR-005 | MEDIUM | UNDER-SCOPE | Rubric E/G (test fixtures, both hosts) | `tests/test_budget_only_combined_red_e2e.py` `_setup_driver_fixture`; `tests/support.py` `declare_execution_role` | Test 1 said "invoke `execute_item_core`" with no fixture; `execute_item_core` requires host labels and launcher injections and is reached via each host's `execute_item`. Without the execution role declared, the item never reaches integration (measured: `KeyError: 'integration_ladder'`). Only one host was covered. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 names the reusable fixture, the patch targets, the role declaration, and requires both hosts; retired-lane and re-attempt fixtures spelled out as demonstrated. |
| PR-006 | LOW | IN-SCOPE | Rubric G (right-sizing, E/V bijection) | plan E-01 (before revision) | E-01 bundled two independent functions and E-02's V-item could not show the retired-lane hunk separately. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-01 (execute), E-02 (retired lane), E-03 (re-attempt prompt), each with its own diff V-item; tests became E-04, runs E-05. |
| PR-007 | LOW | UNDER-SCOPE | Rubric D (invariants, regression set), spec sync | `tests/test_budget_only_combined_red_e2e.py`; `tests/test_oc_runipd.py`; `tests/test_agy_runipd_cli.py` | The regression run omitted the modules that drive these exact paths, invariants were not named, non-goals were not stated, and the spec-sync N/A was not backed by a search. Also the measured-path stderr text change (OQ-02) was undocumented. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the three modules to E-05, an invariant-to-test map, non-goals, F-8 (sites deliberately untouched), OQ-02, and a searched spec-sync N/A; added `Carrier-Evidence` for the now-executed `44nfmd` carrier (`aw check` `check.ipd-carrier-finished-unverified`). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which fallback when `integration_deferral` is absent? | `read_integration_cause(<raw>)[2]` | bare raw reason (leaks the cause token) | `agent_workflows/runner_shared.py` `read_integration_cause` docstring; prototype stderr | yes |
| D-2 | Should a MEASURED refusal's stderr also switch to the recorded reason? | Yes, one rule for all refusals (OQ-02) | branch on unmeasured only (keeps leaking the token on measured refusals) | same; E-04 case 4 still pins `integration_failed_combined_red` on the measured line | yes |
| D-3 | How should tests reach the three sites? | host `execute_item` with the `xc1xh9` fixture for execute; direct calls to `integrate_retired_lane` and `reattempt_deferred_integrations` with stubs | build `execute_item_core` injections by hand (fragile); subprocess end-to-end (slow) | prototype run on HEAD `08fa69666`, 7.1s for all cases | yes |
| D-4 | Change the review-integration report or `reintegrate_lane` too? | No | include them | F-8: neither can produce an unmeasured `record_integration_refusal` reclassification | yes |
