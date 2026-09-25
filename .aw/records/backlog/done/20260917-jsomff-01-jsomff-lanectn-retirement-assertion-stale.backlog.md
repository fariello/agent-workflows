- Id: jsomff
- Status: done
- Set: jsomff
- Priority: medium
- Work-Kind: bug
- Summary: tests/test_orchestrator_retirement.py's lanectn assertion is hardcoded to a Set that has since completed, so it fails on every run

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: fixed by 730763b1: lanectn pin re-pointed in tests/test_orchestrator_retirement.py
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-17 created (aw backlog): Found while executing rl67b0

MEASURED 2026-09-17 while executing plan `rl67b0`. `tests/test_orchestrator_retirement.py::RealRepositorySets::test_lanectn_refuses_naming_its_one_unfinished_verification_child` asserts `evaluate_set_retirement(REPO_ROOT, 'lanectn').eligible is False`, on the premise that the real `lanectn` Set still has an unfinished verification child. That Set has since COMPLETED: the evaluator now reports "all 7 child(ren) are executed (cqx5v7, nna8yz, lhmrhx, y5od1h, xdr83v, 604wra, 4fodkt), and every row of the orchestrator's child table resolves to a plan", so the assertion is false and the bare suite is red for everyone.

CONFIRMED PRE-EXISTING AND NOT CAUSED BY `rl67b0`: reproduced in a clean worktree checked out at HEAD with none of that plan's changes present (`1 failed, 136 passed`).

THE UNDERLYING SHAPE, which is what makes this worth an item rather than a one-line edit: the test pins a property of LIVE REPOSITORY RECORDS, so it expires the moment the repository legitimately makes progress. Whoever fixes it should decide whether the intent was 'this specific Set is incomplete' (in which case re-point it at a Set that still is, and it will expire again) or 'an orchestrator naming an unauthored/unfinished child refuses' (in which case build the Set as a fixture and stop reading REPO_ROOT).
