# Review findings: plan rrydjy

- Subject-Id: rrydjy
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `5178d0412` in an isolated review lane. The plan was committed and unchanged (`39d9ff11a`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified:
- `tests/test_readiness_absence_invariant.find_field_absent_pending_plan` filters only `/plan-review|reviewed\b`, while `ipd_lint._REVIEW_EVIDENCE_RE` also matches `APPROVE`, `NO-GO`, `REJECT` (F-01, F-02).
- `ipd_lint.check_readiness_attestation` returns `[]` when that regex matches the history (F-02).
- The E-01 planted shape (demoted draft with `APPROVE for execution` history) passes the finder filter, lints `conforming`, and its backfill also lints `conforming`, so the planned deliberate-break control (property 2 red) is reachable (F-03).
- The finder currently picks `o58r3r`; the file passes `10 passed in 1.53s`. `wa64wz` is field-absent, passes the finder filter, and its backfill lints `conforming` (F-04).
- With the finder stubbed to `None`, the synthetic subject passes properties 2, 3 and 4 (F-06).
- `pyproject.toml` `addopts` deselects `livecorpus`; property 1 carries that marker, properties 2-4 do not.
- No `.md`/`.py` outside the module, `executed/` and `reviews/` names the finder or fixture (spec sync N/A holds).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | plan E-02 Expected outcome "collects 10 tests"; V-01 (a) "10 tests and `10 passed`"; V-02 "same 10 node ids"; V-03 (a) "`10 passed`" | A collected test count is an artifact of test organization and may not be a V-item bar. A concurrent addition to this module would make a correct execution fail its own bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bars are now the node-id set recorded at E-01, compared by name; V-03 (a) explicitly names property 2 turning from FAILED (V-01 d) to PASSED as the regression proof. |
| PR-002 | LOW | IN-SCOPE | G. Execution contract | plan `## Approval and execution gate` | The gate lacked the MUST-paste-actual-output honesty rule, the OQ status line, the scope-fence declaration, and the no-hand-`git mv` rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added all four to the gate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep OQ-01 resolved as hermetic synthetic subject rather than adding `livecorpus` to properties 2-4? | Keep the author's resolution | Mark properties 2-4 `livecorpus` (moves a circular test out of the default suite); tighten the finder (F-07, tautological) | plan F-05, F-06; reviewer probe with finder stubbed: P2/P3/P4 ok | yes |
