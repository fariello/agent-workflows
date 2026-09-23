- Id: 3ypquf
- Status: open
- Blocks-Release: next
- Set: 3ypquf
- Priority: low
- Work-Kind: bug
- Summary: DeepCleanupTests all_recoverable fails because the installer's own gitignored workflow-artifacts README is classified at-risk

## Workflow history
- 2026-09-23 created (aw backlog): Found while executing IPD i8u6hh (verstamp Order 01).

tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed fails on untouched HEAD. Verified 2026-09-23 on a pristine 'git archive HEAD' export: '2 failed, 8 passed in 27.30s', the same failure with no working-tree changes present.

CAUSE, per the test's own docstring (which already declares it pre-existing at commit 6123749b): the install emits .aw/workflow-artifacts/README.md, which is GITIGNORED by design (D92), so 'git add -A' cannot commit it, and plan_deep_cleanup therefore classifies it as untracked and at-risk, making all_recoverable False even when the user has committed everything they can commit.

THE PRODUCT QUESTION the test raises and does not answer: should plan_deep_cleanup exclude the framework's OWN gitignored run-scratch README from the at-risk set? A user who has committed everything commits nothing that is missing, so telling them cleanup is unrecoverable is a false alarm on the framework's own scratch file. The alternative is that the expectation should change. The docstring explicitly calls this 'a maintainer call about agent_workflows/', which is why the test was left red rather than weakened.

SECOND, SMALLER FINDING: plan i8u6hh's declared test baseline names only ONE pre-existing installer failure (UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory) but there are TWO. The baseline understates the count, so a future executor of any installer-touching plan can mistake this for a regression it introduced. Worth correcting wherever that baseline is restated.

WHERE: agent_workflows/engine.py plan_deep_cleanup (the at-risk classification) and tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed.
