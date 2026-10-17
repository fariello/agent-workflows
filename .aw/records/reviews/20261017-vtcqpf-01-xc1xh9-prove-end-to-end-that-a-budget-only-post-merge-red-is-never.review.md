# Review findings: plan xc1xh9

- Subject-Id: xc1xh9
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `4af5e66b1`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` with one advisory
`IPD-Z602` (E-01 bundles three concerns); after revisions `--phase review-finalize`: `clean`, 0 findings.
Not an orchestrator.

Verified at review:
- `sa629y` is now on `main` (`4af5e66b1`, `- Status: reviewed`); `budget_only` is not yet in
  `runner_shared`, as expected before it executes.
- Every symbol the plan names exists: `INTEGRATION_DEFERRED_STATUS` (`merge-retry`),
  `INTEGRATION_BLOCKED_STATUS` (`fail-merge`), `COMBINED_RED_RETRY_COUNT_KEY`, `REVALIDATION_CACHE_KEY`,
  `INTEGRATION_REFUSAL_UNMEASURED`, `terminal_refusal_verdict` ("MEASURED the merged tree and it was RED"),
  `decide_integration_deferral` ("could not MEASURE"), `start_suite_baseline` (called from
  `execute_item_core`), each host's `retry_deferred_integrations`, and
  `DriverHookAndSuiteFixItTests._setup_driver_fixture`.
- A prototype of the whole module on both hosts, using an unmeasured stand-in for the budget-only shape
  (F-5), passed every first-attempt assertion of E-02, E-03 and E-04.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric D/E (re-attempt half unreachable and non-falsifying) | `agent_workflows/runner_shared.py` `make_integration_validation_runner` "if tree_id and isinstance(cache, dict) and tree_id in cache:"; plan E-02 "switch the revalidation result to passing, call `driver_mod.retry_deferred_integrations`"; F-6 | E-02's retry half could not pass as written, and nothing said why. The per-run revalidation cache is keyed on the merged tree, and an unchanged main rebuilds the same tree. So the retry is served the cached unmeasured reading and the item stays `merge-retry`. Measured on both hosts: no integration; clearing the cache made both integrate. An executor would be pushed to clear the cache in the test, which hides the very defect the test exists to catch. The fix is `sa629y`'s cache exclusion, which the plan neither depended on nor checked. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now checks for the cache exclusion. E-02 asserts the revalidation stub ran again on the retry, forbids clearing the cache, and explains why. F-6 records the measurement. Dependency is now `executed:sa629y` (see PR-002). |
| PR-002 | MEDIUM | IN-SCOPE | Rubric G (stale premise, dependency) | plan F-4 / OQ-01 "`sa629y` exists only on lane branch ... `executed:sa629y` is refused as dangling"; lint with `executed:sa629y` -> `clean` | The authoring-time reason for gating on the proxy `state:backlog:done:o58dro` no longer holds, because `sa629y` is on main and the direct edge lints clean. The proxy is also weaker: closing `o58dro` is a separate act after `sa629y` executes, so it can hold this plan back after the real prerequisite has shipped. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Item-Dependencies: executed:44nfmd, executed:sa629y`. F-4 marked superseded, OQ-01 re-resolved, Carrier changed from `o58dro` to `sa629y`, gate updated. |
| PR-003 | MEDIUM | UNDER-SCOPE | Rubric F (silent mislabel), carrier | `runner_shared.execute_item_core` "finalized on lane {lane_branch} but NOT integrated to main ({fail_status}): {integ_reason}"; F-7 | The prototype showed that the operator's stderr line still says "integration_failed_combined_red ... combined-red" for a refusal recorded as `merge-unchecked`, because it prints the raw gate reason. That is the user-visible half of the `vtcqpf` symptom, and no carrier owned it. It is a production change, so it is out of this test-only plan's scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Filed as backlog `geajrj` (bug, `Blocks-Release: next`) with the measured evidence, and added as a Deferred carrier. E-02 is told not to assert on stderr. F-7 added. |
| PR-004 | LOW | IN-SCOPE | Rubric G (right-sizing) | `IPD-Z602` on E-01; plan E-01 "Confirm the prerequisites landed, then build the fixture" | E-01 bundled a read-only prerequisite check that can block the plan with building the whole fixture and its helpers. These are two concerns with different V evidence, and V-01 mixed them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split: E-01 is the read-only check, and new E-06 (Depends on E-01) builds the fixture. E-02 to E-05 depend on E-06. V-01 is narrowed and V-06 added. `IPD-Z602` is cleared. |
| PR-005 | LOW | IN-SCOPE | Rubric G (execution contract, bar) | plan `## Approval and execution gate`; E-05 "three tests, each over two hosts, pass"; OQ "Owner: none" | The gate lacked an explicit open-question statement, scope-fence declaration, never-push rule and hand-run finalize path. E-05 used a test count as its bar. Both resolved questions recorded no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with every contract element. E-05's bar is now "every test passes for both hosts". Owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Gate on the backlog proxy or on `executed:sa629y`? | `executed:sa629y` | Keep `state:backlog:done:o58dro` (weaker, stale rationale); require both (redundant) | lint clean with the edge at `4af5e66b1`; F-4 | yes |
| D-2 | Where should the console mislabel go? | New backlog `geajrj`, bug, gated on next release | Widen this plan to edit `runner_shared` (collides with `sa629y`/`44nfmd`, breaks the test-only scope); ignore it (user-visible bug) | AGENTS.md "Every live bug gates the next release"; F-7 | yes |
