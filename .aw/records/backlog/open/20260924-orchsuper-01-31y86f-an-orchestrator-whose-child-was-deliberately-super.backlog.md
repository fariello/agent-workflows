- Id: 31y86f
- Status: open
- Blocks-Release: next
- Set: orchsuper
- Priority: high
- Work-Kind: bug
- Summary: An orchestrator whose child was deliberately SUPERSEDED can never retire: the retirement gate accepts only 'executed', so hostdedup a5wdne is permanently dependency-blocked

## Workflow history
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
