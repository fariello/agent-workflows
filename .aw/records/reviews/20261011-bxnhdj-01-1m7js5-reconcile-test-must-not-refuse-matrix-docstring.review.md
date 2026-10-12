# Review: Reconcile test_must_not_refuse_matrix docstring with Order 02 plans selector routing

- Subject-Id: 1m7js5
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Verified at HEAD `b1b2fab2b`. `aw ipd lint --phase author` reported clean before review. Claims
checked: F-01 (`git show 8c460a9a1 -- tests/test_selector_type_containment.py` flips both plans path
assertions to `rc == 0 and "would rename" in out`), F-02 (docstring of `test_must_not_refuse_matrix`
at `tests/test_selector_type_containment.py:289-292` still reads `rc=2, 'no plan has Id' (pins
pre-existing refusal for Order 02)`), F-03 (re-run: `10 passed in 2.39s`), F-04
(`87m438` executed plan line 371 records the defect and backlog `bxnhdj`). E-02's `rg` probe
currently matches only lines 291-292, so it correctly isolates the residual drift without matching
the unrelated `rc=2` refusal tests at lines 66, 185, 273.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E. Testing (baseline) | plan E-01/E-03, V-01/V-03 | E-03 compares the bare-suite failing set against "a baseline re-measured on the unmodified base", but no E-item measures it before the edit; executor would have to stash/revert to obtain it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now also runs the bare suite pre-edit and records the FAILED node-id set; E-03/V-03 and Required tests compare against that set; added flake-rerun guidance for a post-only failure. |
| PR-002 | LOW | IN-SCOPE | G. Executability | `.aw/records/backlog/graduated/20261001-bxnhdj-*.backlog.md` `Status: graduated` | Deferred section said the runner/maintainer "sets graduated/done"; the item is already graduated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reworded to state it is already graduated and only `done` remains for the runner/maintainer. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where should the pre-edit bare-suite baseline be taken? | In E-01, before any edit | A new separate E-item; measuring by stash in E-03 | Plan already has a Baseline task group (E-01); stash would touch the working tree mid-execution | yes |
