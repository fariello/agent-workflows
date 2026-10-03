- Id: r4a4ab
- Status: open
- Set: r4a4ab
- Priority: medium
- Work-Kind: chore
- Summary: aw ipd lint --all exits 1 on the live tree, so release_readiness.gate_ipd_lint reports NO-GO and no test can assert a GO verdict

## Workflow history
- 2026-10-02 created (aw backlog): Filed while authoring plan dyiasf (backlog 3rmvik).

Measured at HEAD 75c78b668 by driving the code, not reading it:

1. release_readiness.gate_ipd_lint(repo_root) returns passed=False, detail='ipd lint exit 1', evidence={'returncode': 1}.
2. release_readiness.build_report(suite_passed=True, residual_risk_signed=True, residual_risk_signer='Gabriele Fariello', repo_root=root) therefore returns NO-GO with failing_gates=['ipd_lint'].
3. python3 -m agent_workflows ipd lint --all --agent reports {"findings":49,"exit":1}; the human-readable run reports counts: conforming=141, quarantined=0, legacy/not evaluated=1081, error=7.
4. The 7 error plans fail on IPD-Q501 (a BLOCKING open question still 'open') and IPD-C801 (a code citation with no durable anchor).

Why this is filed rather than fixed in plan dyiasf: the red is a property of OTHER agents' pending plans, not of release_readiness, and clearing another author's open blocking question is outside that plan's Scope-Paths. Plan dyiasf discharges what it owes the finding by asserting NO live-tree verdict in any restored test (its F-04, F-09).

Consequence worth stating plainly: until this is resolved, no test anywhere may assert that build_report yields GO against this repository, and the deleted tests/test_release_readiness.py arms IpdLintGateTests.test_ipd_lint_all_phases_run_and_pass and FullReportTests.test_build_report_go_on_clean_tree must NOT be restored verbatim; they would be red on arrival. Such a test would also be the documented livecorpus hazard: any agent authoring a plan with an open blocking question could turn it red for every concurrent lane.

Work-Kind rationale:
- Selected: chore. build_report has no production caller (tree-wide search outside the module matches only tests/test_release_readiness_child_pin.py), so no user receives a wrong answer or waits longer today.
- Rejected bug: not user-perceptible under the AGENTS.md perceptibility test, since nothing a user runs renders this report.
