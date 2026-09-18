- Id: evwmm2
- Status: open
- Blocks-Release: next
- Set: evwmm2
- Priority: medium
- Work-Kind: bug
- Summary: aw check's human surface ignores a finding's structured recovery field and prints a generic inspect-frontmatter fix instead

## Workflow history
- 2026-09-18 created (aw backlog): aw check's human surface ignores a finding's structured recovery field and prints a generic inspect-frontmatter fix instead

FOUND 2026-09-18 while executing nobugship rgaasb E-02 (the new check.live-bug-ungated rule). PRE-EXISTING and affects EVERY rule that populates recovery, not only the new one.

WHAT IS WRONG. check_engine.enrich_drift lets a rule attach a structured 'recovery' string (the exact command that fixes the finding), and finding_dict serializes it faithfully, so the --agent record carries it verbatim. But doctor.build_remediation, which the HUMAN renderer consumes, never reads drift.recovery. It pattern-matches the rule id against a hand-maintained if-chain and otherwise falls through to a generic default (doctor.py:1151-1157): summary_fix 'inspect artifact frontmatter and schema conformity.'

MEASURED. A fixture repo holding one live gateless bug, with a recovery of 'aw backlog set open aaa111 --blocks-release next':

    $ aw check all --dir <fixture>
      Issue: check.live-bug-ungated
      - ...open
        1. 20260918-tst-01-aaa111-a-live-gateless-bug.backlog.md
        Fix: inspect <path> frontmatter and schema conformity.

while the same finding's machine record carries the real command:

    "recovery": "aw backlog set open aaa111 --blocks-release next  (or hand the gate to ...)"

WHY IT MATTERS. The human is the audience least able to derive the fix, and is the one shown the
useless string; the agent, which could infer it, gets the good one. It also silently penalizes the
correct implementation: a rule author who follows the family's documented shape and populates
recovery sees their teaching discarded, while the if-chain rewards hardcoding a second copy of the
same command in doctor.py.

SUGGESTED FIX. Have build_remediation prefer drift.recovery when it is non-empty, before falling
through to the generic default, so the if-chain becomes an override rather than the only source.
That is one change in one function and it improves every rule that already populates the field.
