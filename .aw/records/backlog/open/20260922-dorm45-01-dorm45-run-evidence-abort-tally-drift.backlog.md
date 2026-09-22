- Id: dorm45
- Status: open
- Set: dorm45
- Priority: low
- Work-Kind: chore
- Summary: run_evidence abort-tally comment was already wrong before RUN-NO-PUSH was retired, so the module documented a table it did not have

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing plan 4h7tt0. The abort-semantics comment in agent_workflows/run_evidence.py read 'Two of the 13 codes abort UNCONDITIONALLY; eight abort ONLY under a named 4.1 class; three never abort'. MEASURED at HEAD 2815aa56 BEFORE any edit (by stashing my changes): Counter({'conditional': 6, 'never': 5, 'always': 2}) over 13 codes. So 8/3 was already wrong on arrival, presumably from an earlier edit that changed a row's abort tri-state without updating the prose. 4h7tt0 corrected it to the measured 2/5/5 and recorded BOTH moves rather than overwriting the error, because attributing the whole discrepancy to the retirement would have been false. FILED AS chore RATHER THAN bug on the perceptibility test: this is an internal comment, nothing reads it, and no user-visible output or timing is affected. THE GENERALIZABLE CONCERN: this hand-maintained count sits next to the '13 codes' counts that ARE enforced (validate_finding_table's RC-COUNT plus three tests), so the enforced ones stayed correct while the unenforced neighbour rotted silently. Worth considering whether the abort partition should be computed or test-pinned the way the code count is.
