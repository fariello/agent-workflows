# Review: Record the resolved model per attempt so run analytics can compare models

- Subject-Id: 1u4olp
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `ad22ff70aff62a1f8b99361aad907cacd8692795` in review lane
`review-sweep-run-20261007T165410Z-456709`. Working tree clean; the target plan was committed and
byte-identical to the lane input (`cmp` returned equal), so the pre-review snapshot was skipped.
Structural preflight: `aw ipd lint --phase author` reported clean (0 findings); `aw ipd coverage 1u4olp`
reported "Orchestrator 1u4olp is ready for review."

Verified from disk: all three children (`czut8j`, `ov2c9n`, `r5fk4k`) sit under
`.aw/records/plans/executed/` with `- Status: executed`; both siblings declare
`Item-Dependencies: executed:czut8j` and `r5fk4k` OQ-03 records why it does not depend on `ov2c9n`; the
three child test files exist (`tests/test_attempt_model_identity.py`,
`tests/test_attempt_host_model_observation.py`, `tests/test_attempt_model_consumers.py`); the three shipped
dashboard tests exist in `tests/test_run_dashboard.py`; `MODEL_COVERAGE_THRESHOLD = 0.80`
(`agent_workflows/run_analytics_statistics.py:117`); the production caller now passes a real population
(`agent_workflows/run_analytics_cli.py:1043`, `stats_mod.model_comparison(attempt_population)`); spec
`25kzda` Section 5.3a "NEVER A GATE" resolves. The sequencing, ownership table and completion criteria are
sound. Four defects in the parent's own prose were found, all citation or contract gaps.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Executability / evidence | Plan completion criterion 7 and Cross-IPD bullet "NO CHILD MAY ADD A CLI FLAG" cite `tests/test_run_flag_surface.py` as reading spec `25kzda` and turning the suite red; `ls tests/test_run_flag_surface.py` -> No such file; `git log -1 19313eed` -> "test: trim test suite from 9,136 to under 2,000 tests"; `ov2c9n` F-10 and `r5fk4k` review both already corrected this citation | The parent asserts a mechanical enforcement that does not exist, so a reader trusts the suite to catch an added flag when nothing would | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both sites now state the test was deleted in `19313eed`, that the obligation rests on the plan contract and undeclared `.spec.md` scope, and that a flag would breach silently |
| PR-002 | LOW | IN-SCOPE | G. Executability / evidence | Plan Cross-IPD bullet "THE THREE SHIPPED DASHBOARD MODEL TESTS" and Required tests cite `r5fk4k`'s V-06 for the unedited-test claim; in `r5fk4k` that obligation is E-08/V-08 ("SPLIT OUT OF E-06 AT REVIEW", review record D-3), while V-06 covers `tests/test_attempt_model_consumers.py` | Stale cross-plan item citation sends a verifier to the wrong evidence | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both sites repointed to V-08 with the split noted |
| PR-003 | MEDIUM | IN-SCOPE | G. Orchestrator coverage | Criterion 9 "Each must be filed as its own backlog item at execution", Scope check under-scope bullet, and the gate's "the two residues in criterion 9 have been filed"; `ov2c9n` Deferred section: Antigravity residue `- Carrier: qswokt` (backlog `qswokt` exists, graduated), `audit` residue `- Carrier-Declined: ... no obligation is outstanding` | The parent demanded a filing act at execution that only the parent would perform, which is exactly parent-only work the runner retires unperformed; the children have in fact already dispositioned both residues | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Criterion 9, Scope check and gate now cite the existing dispositions (`qswokt` filed; `audit` declined by `ov2c9n`) and carry no filing step |
| PR-004 | MEDIUM | UNDER-SCOPE | G. Execution contract | Plan `## Approval and execution gate` (as received) carried approval, ordering and path-scoped commit only: no hard-MUST honesty rule, no scope-fence declaration, and no conditional lifecycle transition (runner retirement versus hand `aw ipd finalize`) | A hand executor had no instruction on who owns the terminal transition, and nothing forbade marking V-items from child self-reports | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now states resolved OQs, a declaration-only scope fence, the paste-actual-output rule, commit discipline, and the runner-retires / hand-finalize split with no hand `git mv` |

### Coverage repair loop (`IPD-S408`)

- Attempt 1: after the edits above, `aw ipd lint --phase review-finalize` reported one `IPD-S408`
  `coverage-record-stale (1u4olp): plan changed since the check ... (fingerprint mismatch)`. Changed: re-ran
  `aw ipd coverage 1u4olp --no-commit`, which reported "Orchestrator 1u4olp is ready for review." and wrote
  `- Coverage: pass` with fingerprint `d60d56985ca0...`. Re-lint at `review-finalize`: clean, 0 findings.
  Checklist rows unchanged (rows: 3 -> 3).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-003: the `audit`-verb residue was never filed as a backlog item; file one now, or accept the child's recorded decline? | Accept `ov2c9n`'s `Carrier-Declined` and say so in criterion 9, leaving a new item to a maintainer who wants it | File a new backlog item from this review; keep the parent's "file at execution" step | `.aw/records/plans/executed/20260930-attmodel-02-ov2c9n-*.ipd.md` Deferred section, `audit` bullet `Carrier-Declined` (single-model turn, model already in its own `options`); a review edits plans only (plan-review Step 0); keeping the step parks parent-only work the runner retires unperformed | yes |
