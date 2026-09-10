- Id: pfh5qa
- Status: open
- Set: runspendrep
- Priority: medium
- Work-Kind: bug
- Summary: run summary table reports 0.00 spend and blank tokens for an interrupted item while aw runs reports 2.17 and 3.62M for the same item, so the two surfaces disagree and the table under-reports real spend

## Workflow history
- 2026-09-10 created (aw backlog): run summary table reports 0.00 spend and blank tokens for an interrupted item while aw runs reports 2.17 and 3.62M for the same item, so the two surfaces disagree and the table under-reports real spend

MEASURED 2026-09-10 in `run-20260910T004521Z-2724478` (opencode, 39 items, position 34, plan `utwr6y`,
the one item of 39 that was interrupted by the stall guard).

THE TWO SURFACES DISAGREE ABOUT THE SAME ITEM:

    run summary table:  Spend $0.00   Tok tot -        Tok in -   Tok out -   Tok cache -
    aw runs <run-id>:   Spend $2.17   Tok tot 3.62M

BOTH CANNOT BE RIGHT, and the ledger settles which is: `state.json` carries NO cost or token keys at all
for that item or its attempt (verified: `[k for k in attempt if 'cost' in k or 'token' in k]` is empty),
while summing the attempt's own session log (`sessions/34-utwr6y-attempt-1.jsonl`) yields EXACTLY
`$2.17` and `3,619,537` tokens. So `aw runs` derives its figure from the session log and is correct;
the summary table reads the absent state field and prints zero.

WHY IT MATTERS, and the honest scale first: this is ONE item's $2.17 inside a $494.30 run, so the total
is off by well under one percent and no decision would have changed. It is filed because the ERROR
DIRECTION is the dangerous one. Interrupted work is exactly the work that gets retried, and a retry
spends again; a surface that reports interrupted attempts as free makes a retry loop look cheaper than
it is, and the cost is invisible in precisely the case where an operator is deciding whether to resume.
The same reasoning applies to the run TOTAL, which sums the per-item figures.

DO NOT FIX IT BY SWITCHING THE TABLE TO PARSE SESSION LOGS. That would give two independent cost
derivations that can drift, which is the defect class this repository already treats as a hazard (P8).
The likely correct fix is to make the interrupt path WRITE the accounting it already has into
`state.json`, so one ledger feeds both surfaces. Verify that against the writer before acting; this is
an inference from the artifacts, not a reading of the code.

RELATED, and probably the same root cause: backlog `hyit04` records that the same interrupted attempt
also lost its `session_id`, which likewise exists in the log and is null in the state. If one writer
persists both on the success path only, the two items may close together; check before assuming it.

ALSO WORTH DECIDING, and it is a genuine question rather than a task: whether a KILLED attempt's spend
should be counted in the run total at all. It is real money that was really spent, so counting it is
defensible; excluding it while labelling it excluded is also defensible. Printing `$0.00` as if nothing
was spent is the one option that is not.
