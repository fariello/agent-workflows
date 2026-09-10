- Id: aagh7v
- Status: open
- Set: nopushcap
- Priority: medium
- Work-Kind: followup
- Summary: Remove the unshipped supports_deny_push flag and the three action verdicts nothing enforces

## Workflow history
- 2026-09-09 created (aw backlog): Filed from /askme 2026-09-10 recording a maintainer decision on 4h7tt0 OQ-02: remove supports_deny_push and the review/mutate/contractless_prompt REFUSED verdicts that reference it. Measured at HEAD 8dffd7a0: ACTION_REQUIREMENTS has no consumer outside host_sandbox_profile.py and the runners never read the verdict, so the flag only PRINTS a protection that does not exist. Never shipped (added 30108f78 2026-09-04; newest tag v1.3.0-rc.1 is 2026-07-24). The honest finding survives at run_evidence.py:1505-1517. Also remove the six test references. Do NOT bind the code to a presence-based inference on the way out (host_sandbox_profile.py:88-95).
