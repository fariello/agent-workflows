- Id: wi2pmm
- Status: open
- Blocks-Release: next
- Set: wi2pmm
- Priority: medium
- Work-Kind: bug
- Summary: test_runner_stop_level4's ten slow end-to-end tests fail when the slow marker is cleared

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing plan fduoj4 (runrecon-02).

MEASURED 2026-09-22 at HEAD 27a446d4, on UNMODIFIED code (every edit of plan fduoj4 stashed first, so this is not that plan's doing).

WHAT HAPPENS. A bare `python3 -m pytest` is green, because `pyproject.toml` `addopts` supplies `-m 'not slow'` and these tests are marked slow. Clear the defaults with `python3 -m pytest tests/test_runner_stop_level4.py -o addopts=""` and ten tests fail:

  RealEntryPointTests::test_the_refusal_comes_from_the_real_requeue_path
  RealEntryPointTests::test_plain_resume_refuses_and_exits_nonzero_without_running_anything
  RealEntryPointTests::test_resume_with_retry_incomplete_is_refused_too
  AgyDriverParityTests::test_agy_is_cut_immediately_and_records_the_same_indeterminacy
  IndeterminateInTheLedgerTests::test_a_missing_outcome_json_is_not_read_as_information
  IndeterminateInTheLedgerTests::test_the_ledger_records_indeterminacy_git_state_and_the_reconciliation_need
  ImmediateInterruptTests::test_cleanliness_is_identical_to_a_level_3_stop
  ImmediateInterruptTests::test_a_silent_child_is_still_cut_promptly
  ImmediateInterruptTests::test_the_turn_is_cut_without_waiting_for_a_checkpoint
  PromotionGateEndToEndTests::test_a_force_cut_after_the_plan_moved_is_never_recorded_executed

The proximate assertion in several is `self.assertTrue(runner_stop.is_indeterminate(run.item(...)))` returning False, i.e. the fixture's forced stop did not leave the `stopped` record with `certainty: indeterminate` that spec c4gd2h R18/R19 require. These launch real driver subprocesses with a fake child, so the cause may be the fixture harness rather than the product.

WHY IT IS FILED AS A BUG RATHER THAN A CHORE. What these ten tests pin is spec c4gd2h's level-4 anti-fabrication behavior: that a force-cut turn is recorded INDETERMINATE and is never re-run or promoted on inference. That guarantee is currently unverified by any passing end-to-end test, so a regression in it would ship silently. The user-perceptible impact is not latency but a wrong answer about whether work completed, which is the class of defect the level-4 machinery exists to prevent.

WHAT IS NOT CLAIMED. I did not determine whether the PRODUCT or only the TEST HARNESS is broken; the unit-level gates for the same behavior DO pass (PromotionGateTests, and the new control test in plan fduoj4 that proves an indeterminate item is refused even when its outcome file claims success). So the guarantee is pinned at unit level and unpinned end-to-end. Whoever picks this up should establish which side is at fault before changing either.

FIRST STEP: run one of the three ImmediateInterruptTests with `-s` and inspect the fake child's recorded `stopped` payload.
