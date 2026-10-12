# Review findings: plan 4mv9ul

- Subject-Id: 4mv9ul
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `dbde69ccb`. The plan was committed and byte-identical to the
lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`. Not an orchestrator.

Re-measured: the E-01 snippet prints `['oc profile add', 'oc profile default', 'oc profile list',
'oc profile remove', 'oc profile show', 'oc profile validate-default']`. `python3 -m pytest -o addopts=""
tests/test_command_surface_declarations.py -v` shows both tests PASSED (`2 passed in 0.38s`). The CI step
command `python -m pytest tests/test_command_surface_declarations.py` gives `2 passed in 2.03s`. `--collect-only`
under the default `addopts` collects 2. `.github/workflows/tests.yml` `output-conformance` runs that module.
Commit `f2cd41b19` is the `0yrtne` fix. Backlog `4fe3al` is in `done/`, and `vxqtqm` is `graduated` to
this plan. `0yrtne` F-7 exists and carries the field judgements E-01 cites.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric G (live-artifact criteria); backlog `vxqtqm` ("the BARE suite passes, so this is only visible when the module is run alone") | plan E-03/V-02/V-03 ("2 passed", "`N passed`") | The bars were collected test counts. Also, E-03 proved nothing about the backlog item's actual concern: a bare suite passing is exactly what the item reported while the defect was live. Enforcement needs the module COLLECTED under the default `addopts` and no failure among its node ids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03/V-02/V-03 now require the named tests passing, a `--collect-only` proof under default `addopts`, failing node ids rather than totals, and the CI step excerpt. |
| PR-002 | LOW | UNDER-SCOPE | Rubric G (execution contract) | plan "Approval and execution gate" | The gate lacked the paste-actual-output rule, the staged-set check, a scope fence for the regression path, and who finalizes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All four added, plus the From-Backlog duplicate-closure path. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep a verification-only plan rather than closing `vxqtqm` directly as a duplicate? | Keep (the author's OQ-01). | Direct `aw backlog set done --evidence` (REJECTED here: the item is already `graduated` to this plan, so the From-Backlog handoff is the consistent close). | backlog `vxqtqm` history ("graduated by run ...: 4mv9ul"). | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
