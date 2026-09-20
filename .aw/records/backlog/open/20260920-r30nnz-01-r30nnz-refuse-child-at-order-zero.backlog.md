- Id: r30nnz
- Status: open
- Set: r30nnz
- Priority: low
- Work-Kind: followup
- Summary: Decide whether aw group/rename should refuse to place a Kind: child at Order 0 (consult IPD-M104 at the write site)

## Workflow history
- 2026-09-20 created (aw backlog): Filed while executing plan e3hzyc (E-03/OQ-03): the recorded decision was to NOT build the refusal inside that bug fix, and to carry the question here.

E-03 OF PLAN e3hzyc REQUIRED A RECORDED DECISION, NOT A BUILD, and this item is that record.

THE DECISION: do NOT add the refusal in e3hzyc. Reasons, in order of weight.
1. e3hzyc CLOSED THE ACCIDENTAL PATH, which was the whole observed problem. Nobody types `--order 0` on a child; they omit the flag, and the verb used to substitute zero. With an absent flag now preserving each plan's own Order, a refusal would only ever catch an EXPLICIT `--order 0` on a `Kind: child`, a far rarer mistake.
2. A REFUSAL CHANGES A VERB'S CONTRACT, and `aw group ... --set <new>` is the RECOMMENDED RECOVERY for a setid collision (spec 4w7d6s I4). A new failure mode on the repair path can block a repair, which is the same class of harm the original defect had.
3. IT MUST BE CONDITIONAL ON `- Kind: child`, because an ORCHESTRATOR at Order 0 is correct and common. That conditionality is cheap to state and easy to get wrong, and getting it wrong breaks the common case.

THE COUNTER-ARGUMENT IS REAL, which is why this is filed rather than dismissed. `aw ipd lint` ALREADY KNOWS the rule (IPD-M104: "child Order must be an integer >= 1") and the write site does not consult it. That is the same shape sjsoqq documents for setid collisions at creation: a rule that lives in the checker and not at the moment of writing. Measured during e3hzyc: with a child at Order 0 on disk, `aw ipd lint` exits 1 on IPD-M104 while `aw check plans` and bare `aw check` both exit 0, so nothing in a repo-wide sweep reports it (the reachability half of that is k9awrq's subject).

IF BUILT, the acceptance criteria are: refuse only when the target plan's front matter says `- Kind: child` AND the resolved Order is 0; permit an orchestrator at 0 unconditionally, with a test pinning that case; and name the plan and the rule in the refusal message so an operator can pass a deliberate override or fix the Order.
