- Id: wu8qjy
- Status: open
- Blocks-Release: next
- Set: wu8qjy
- Priority: high
- Work-Kind: bug
- Summary: The release-gate rule is unenforced in CI: no workflow step runs aw check all, and the one step that could report it is advisory

## Workflow history
- 2026-09-18 created (aw backlog): The release-gate rule is unenforced in CI: no workflow step runs aw check all, and the one step that could report it is advisory

FOUND 2026-09-18 while executing nobugship rgaasb E-02, which was required to state which CI step fails on the new rule. The answer is NONE, so the parent Set's completion criterion 4 ('aw check reports a live bug with no gate, and CI fails on it') is only half met.

WHAT IS WRONG. The whole I-07 release-gate rule family (check.live-bug-ungated, check.from-backlog-gate-mismatch, check.blocking-item-closed-without-gate, check.blocks-release-dangling, check.from-backlog-dangling) is wired ONLY into the once-per-full-sweep seam in check_engine.check_types, inside the 'if collisions:' block. check_type('backlog') never reaches it. So:

  * aw check backlog CANNOT report any of these rules. MEASURED on a fixture holding one live
    gateless bug: 'aw check backlog --agent' returned outcome conforms, exit 0, findings 0, while
    'aw check all --agent' on the SAME tree returned findings 1 with check.live-bug-ungated and
    exit 1.
  * .github/workflows/tests.yml runs 'aw check plans' and 'aw check releases' FAIL-CLOSED
    (:153-159), and 'aw check backlog' with '|| true' as ADVISORY (:166-170, deliberately, per
    DECISION 18-r2ks4k-D1, until the backlog name/summary baseline is cleaned).
  * NO workflow step runs 'aw check' or 'aw check all' at all (grepped: the only check steps are
    plans, releases, backlog).

So the rule that enforces 'we do not ship known bugs' exits 1 locally and fails NOTHING remotely. An
agent can push an ungated bug and CI stays green.

WHY IT MATTERS. This Set exists because an oral rule decayed. A rule that only a human's local sweep
enforces is the same failure one layer along: the authoritative boundary in this repository is
explicitly 'the aw check rule + CI, never the local hook alone' (spec pqsx96, I-07's honest-limit
column).

SUGGESTED FIX, one of: (a) add a fail-closed 'aw check all' step, which also brings the other
full-sweep-only rules into CI but will fail today on 279 pre-existing findings, mostly
check.scope-drift; (b) add a narrow fail-closed step for the release-gate family specifically; or (c)
flip the backlog step to fail-closed AND move the family onto a seam the type-scoped command reaches,
which DECISION 18-r2ks4k-D1 gates behind cleaning the backlog baseline first.

NOT FIXED BY rgaasb: .github/workflows/tests.yml is outside its declared Scope-Paths, and (c)
contradicts a recorded decision's stated precondition.
