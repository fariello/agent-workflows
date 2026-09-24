- Id: 31y86f
- Status: done
- Blocks-Release: next
- Set: orchsuper
- Priority: high
- Work-Kind: bug
- Summary: An orchestrator whose child was deliberately SUPERSEDED can never retire: the retirement gate accepts only 'executed', so hostdedup a5wdne is permanently dependency-blocked

## Workflow history
- 2026-09-24 done (aw set): FIXED at 65e51ec0. Retirement now accepts any TERMINAL child status, derived from ipd_schema.TERMINAL via the new set_retirement_terminal_statuses() rather than compared against the single value SET_RETIREMENT_DONE_STATUS. Still an allowlist, so a status invented later is refused until someone admits it in ipd_schema; retirement and dependency edges keep separate constants because they ask different questions. The eligible message also stopped lying: it now names each child's real disposition ('3 executed (li44r9, xdvglg, 04vf1h) and 1 deliberately retired and will never run (nmlx47: superseded)') instead of asserting all four executed. Regression test test_a_deliberately_retired_child_does_not_wedge_its_set asserts both directions and is proven non-vacuous (reverting the predicate alone makes it fail). VERIFIED END TO END: Set hostdedup retired, a5wdne is now in executed/, and nothing remains in pending for that Set. Full bare suite 8910 passed, 5 skipped, 2 xfailed. NOTE ON THE DELAY IN CONFIRMING IT: two runs kept reporting the old refusal after the fix landed, because the driver executed from a STALE LANE WORKTREE (.aw/worktrees/lkexaw_attempt4, recorded in the run's own state.json driver.path) whose copy predates the fix. That is backlog uin96r/0vbdll/ccbe60, not a defect in this fix; running via 'python3 -m agent_workflows' from the main checkout retired it immediately.
- 2026-09-24 created (aw backlog): An orchestrator whose child was deliberately SUPERSEDED can never retire: the retirement gate accepts only 'executed', so hostdedup a5wdne is permanently dependency-blocked

MEASURED 2026-09-24 on run run-20260924T165302Z-1635336 and again on a clean tree.

THE STUCK STATE. Set 'hostdedup' has four children and ALL FOUR are terminal:
  li44r9  executed
  nmlx47  superseded   <- deliberately retired 2026-09-23, work overtaken by 1f7xno
  xdvglg  executed
  04vf1h  executed
Its orchestrator a5wdne is nevertheless reported dependency-blocked with 'Set hostdedup has 1 child(ren) not yet executed that this run will NOT act on: nmlx47 (superseded)'. The remedy the runner prints ('run the missing children') is UNACTIONABLE: nmlx47 is retired on purpose and must never run.

CAUSE. runner_shared.SET_RETIREMENT_DONE_STATUS is the single literal 'executed', and the retirement predicate tests child status against it, so the two OTHER legitimate terminal dispositions are unrepresentable. Verified: inspect.getsource(ipd_lifecycle.retire_orchestrator) contains no 'superseded'.

WHY THIS IS A BUG AND NOT A RECORDS PROBLEM. superseded and not-executed are FIRST-CLASS terminal dispositions with their own directories, and AGENTS.md requires a plan that will never run to be retired into one of them rather than filed as executed (which 'would falsely claim implementation'). So the lifecycle mandates a state the retirement gate cannot accept, and any Set containing a retired child is permanently wedged.

THE WRONG FIXES, both of which a later agent will be tempted by:
  1. Hand-finalize the orchestrator. That writes 'executed' over a Set whose child never ran.
  2. Delete the child's row from the orchestrator's table. AGENTS.md forbids exactly this, because it retires the parent over work that never completed and destroys the checklist that makes a human-driven 'execute <setid>' complete.

THE SHAPE OF A REAL FIX. Retirement should accept a child in ANY terminal disposition, distinguishing 'completed' from 'deliberately retired' in the recorded reason rather than in the pass/fail decision, so a Set closes when no child can still make progress. The child table already carries the distinction in prose ('RETIRED 2026-09-23 as superseded ... this row is CLOSED, not outstanding'), which is exactly the signal the predicate cannot see.

BLAST RADIUS: any Set with a superseded or not-executed child. hostdedup is the measured instance; a5wdne also holds backlog dstnso open, since its close was never evaluated.
