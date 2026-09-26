- Id: 4bhxni
- Status: graduated
- Graduated-To: turnbudget
- Blocks-Release: next
- Set: turnbudget
- Priority: medium
- Work-Kind: followup
- Summary: Tell the agent its remaining turn budget in the execute prompt (x7wfyx item A, never implemented)

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into to-review plan Set turnbudget (commit 2c7068ca).
- 2026-09-23 created (aw backlog): Filed while executing dy9ymn, which implements x7wfyx item B (the driver-side zero-work retry) only. x7wfyx was closed 'done' on 2026-09-22 under the HANDOFF rule, citing dy9ymn's From-Backlog + Blocks-Release, but dy9ymn's scope EXCLUDES item A in terms ('EXCLUDES telling the agent its remaining turn budget, which is x7wfyx's other half'). So item A now has no live carrier: aw ipd lint reports check.ipd-uncarried-obligation twice on dy9ymn for exactly this. This item is that carrier. NOT filed as a bug and NOT release-gating: per dy9ymn F-7 the measured cause was a HOST truncation, not the agent choosing when to stop, so the prompt half no longer addresses the measured defect and is a genuine followup. It is a change to the shared execute prompt with its own regression surface (tests/test_turn_bounds.py asserts three FOREGROUND properties, and tests/test_defect_report.py hard-codes a per-host prompt-length baseline any prompt edit re-bases).
