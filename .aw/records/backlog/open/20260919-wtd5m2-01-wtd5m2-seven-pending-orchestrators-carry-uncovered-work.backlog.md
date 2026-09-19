- Id: wtd5m2
- Status: open
- Blocks-Release: next
- Set: wtd5m2
- Priority: high
- Work-Kind: bug
- Summary: seven pending orchestrators carry parent-only work no child covers, so the new coverage gate refuses them until children are authored

## Workflow history
- 2026-09-19 created (aw backlog): seven pending orchestrators carry parent-only work no child covers, so the new coverage gate refuses them until children are authored

MEASURED 2026-09-19 at HEAD b5208b0e, by reading every pending Kind: orchestrator plan's FULL item action text (not its first line):

  5e4sb6 (approved) E-01 produce the inventory research artifact; E-02 establish the characterization baseline BEFORE any child runs, writing tests; E-03 verify the whole Set afterwards
  wfjsp4 (approved) E-02/E-03/E-04 three whole-Set verifications no child can demonstrate alone
  a5wdne (reviewed) E-01 verify and record the Set's combined result against all six completion criteria
  tb63qv (reviewed) E-01 verify the Set's combined outcome from the MAIN checkout and record it
  ao1rb7 (approved) E-03 enforce a Set-wide honesty constraint spanning both children's output
  y9s4vm (approved) E-03 confirm backlog 6h7y2y reached its terminal state
  lyo1tz (approved) E-03 confirm backlog cnwy8g was closed by child 02

CLEAR-CUT vs BORDERLINE, stated because the remedy differs. The first four are unambiguous: they produce deliverables, establish baselines before any child runs, or verify a whole Set afterwards, and the runner performs none of them. The last three are borderline reconciliation/confirmation steps that a reviewer may judge to be legitimate orchestration; they are listed so the judgement is made rather than assumed.

WHY THIS IS FILED AS A DEFECT. The runner RETIRES an orchestrator once its children are executed and deliberately SKIPS the pre-transition E/V checkpoint, so each item above is on course to be reported complete having been neither performed nor verified. That is not hypothetical: it already happened to rh5tt6 on 2026-09-08 (commit 8b4e1570, whose message states 'Its own E-*/V-* items were NOT performed') while its E-02 still read 'Execution state: pending'.

THE GATE NOW CATCHES THIS rather than letting it pass silently (spec 25kzda 2.5b / 77tr3o R-12, landed by orchprobe-03 m7gvuz), which is why this is filed now: a run queuing any plan above will REFUSE with a remedy naming the fix. That refusal is CORRECT, and it is the debt this item tracks.

THE REMEDY IS TO AUTHOR A CHILD for each uncovered item and add its row to the parent's child table. DO NOT delete the parents' checklist items to make the gate pass: that checklist is what makes 'execute <setid>' complete and ordered when no runner is involved, and deleting it causes exactly the lost work the gate exists to prevent. Per the plan's OQ-03 the maintainer's ruling is CLEAR FIRST, so that the override never becomes reflex.

Also open, and NOT this item's: rh5tt6's already-unperformed E-02 sits in executed/ and cannot be fixed in place; closing that gap needs a corrective IPD and is the maintainer's call.
