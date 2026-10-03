- Id: l8upzx
- Status: done
- Graduated-To: l8upzx
- Set: l8upzx
- Priority: medium
- Work-Kind: chore
- Summary: Restore the deleted Order regression guard for aw group plans and aw rename plans (PlansGroupPreservesOrderTests, deleted in 19313eed)

## Workflow history
- 2026-10-03 done (aw backlog): closed by aw agy run: IPD fv6kep executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260930-l8upzx-01-fv6kep-restore-the-order-preservation-regression-guard-for-aw-group.ipd.md); evidence .aw/records/plans/executed/20260930-l8upzx-01-fv6kep-restore-the-order-preservation-regression-guard-for-aw-group.ipd.md
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: fv6kep
- 2026-09-29 created (aw backlog): Filed at /plan-review of plan 949enf (finding PR-003/F-14).

FOUND 2026-09-29 during /plan-review of plan 949enf (Set j84jg3), which restores the DATE half of a deleted regression guard and is the change that revealed the Order half is also gone.

MEASURED. tests/test_awnaming_grammar_and_producers.py carried TWO regression classes for the plans rename/group verbs:
  - PlansMvPreservesOrderAndDateTests: 'a bare aw rename plans <id6> --slug X must not clobber Order or Date' (vf03z3), asserting both '- Order: 3' and '- Date: 20260810' survive a rename.
  - PlansGroupPreservesOrderTests: e3hzyc's seven cases, covering BOTH group branches (the --rename clustering path and the metadata-only path), plus the must-not-break guards (orchestrator at Order 0, explicit sequential renumber, explicit --order 0).

BOTH were deleted wholesale in commit 19313eed ('test: trim test suite from 9,136 to under 2,000 tests', 318 files changed, 219,063 deletions). Verified: 'grep -rn PreservesOrderAndDate' over the tree returns nothing, and the only surviving test module touching these verbs is tests/test_group_verb_policy.py, whose docstring scopes it to setid length policy alone.

THE CODE IS STILL CORRECT; THE GUARD IS GONE. Re-verified at review that a bare metadata-only 'aw group plans zzz111 --set newset --apply' still preserves '- Order: 3' and does not renumber to 0, so e3hzyc's fix is intact in plans_refs.plan_set_assign (_preserved_order is present and called above the rename split). The defect is purely the missing coverage: an Order regression in either verb would now pass CI silently, which is precisely the state e3hzyc's plan called out when it noted that rename had a regression test and group had none.

WHY NOT FOLDED INTO 949enf. That plan's Scope-Paths are agent_workflows/plans_refs.py and tests/test_group_verb_policy.py, and it restores the DATE half for both verbs as part of its own fix. Restoring the seven Order cases is a different invariant with its own precedent (vf03z3/e3hzyc) and would roughly double that plan's test surface. 949enf's seeded plans do carry an '- Order:' line so an Order change shows up as a failure there, but that is a guard against 949enf's own change, not a replacement for the deleted suite.

SCOPE. Restore Order-preservation coverage for both verbs and both group branches, reading the deleted classes for the case list ('git show 19313eed^:tests/test_awnaming_grammar_and_producers.py'). Do NOT reintroduce the deleted file's subprocess _run_cli shape: an editable install can make a subprocess import the main checkout rather than a lane (backlog ccbe60), so drive cli.main in-process. No production change is expected; if one proves necessary, that is a separate finding.

WORK-KIND. Filed 'chore' rather than 'bug' deliberately: no user-visible behavior is wrong today (the code preserves Order correctly), so there is no live defect to gate a release on. The risk is future regression, which is a coverage debt.
