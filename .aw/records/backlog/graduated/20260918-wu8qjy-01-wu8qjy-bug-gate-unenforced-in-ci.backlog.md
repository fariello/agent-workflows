- Id: wu8qjy
- Status: graduated
- Graduated-To: gateci
- Blocks-Release: next
- Set: wu8qjy
- Priority: high
- Work-Kind: bug
- Summary: The release-gate rule is unenforced in CI: no workflow step runs aw check all, and the one step that could report it is advisory

## Workflow history
- 2026-09-23 graduated (aw set): Graduated to IPD 2vw35i (gateci Order 01). CONFIRMED BOTH HALVES at HEAD 22cf67d9. (1) CI NEVER RUNS THE SWEEP: grep -c 'agent_workflows check all' returns ZERO in every workflow file (tests.yml, local-leaks.yml, secret-scan.yml), so the seam hosting the release-gate family never executes remotely. (2) THE RULES ARE UNREACHABLE PER-TYPE: 'aw check backlog --agent' reports 4 findings, none from the gate family, while 'aw check all --agent' reports 49 INCLUDING check.live-bug-ungated against a real item (7l1ggb, a live bug with no Blocks-Release). So a genuine violation exists right now and no per-type invocation can see it. THE FINDING THAT SHAPES THE PLAN, and the reason this is not a one-line fix: deleting the '|| true' from the existing advisory 'check backlog' CI step would red main IMMEDIATELY, because the pre-existing naming debt that DECISION 18-r2ks4k-D1 defers is still live and measurable (check.name-nonconformant x3 plus check.collisions-not-checked). So 2vw35i separates the GATE rules from the CONFORMANCE rules and adds a NARROW named fail-closed step, leaving the advisory step exactly as the maintainer left it. A broad step enforcing all 49 findings would be the same red-gate failure 4y7nzh measured over two days and 143 commits. Rule VERDICTS are explicitly out of scope: 4le6yz and 0cqf33 own specific gate-rule defects, so this plan changes reachability and enforcement only.
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
