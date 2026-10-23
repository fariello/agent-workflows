# Review findings: plan 92tzo6

- Subject-Id: 92tzo6
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `2aa1e2fd3`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review:
- `tests/test_run_analytics_findings.py` has module-level `pytestmark = pytest.mark.core`; target functions
  `run_analytics_findings.assert_no_causal_language`, `build_finding`, `findings_from_results` exist.
- All four E-01 probes re-run under `-m core tests/test_run_analytics_findings.py`: every one `killed`,
  `baseline_failing: 0` (11, 2, 17, 1 failing), matching plan F-02 (recorded as plan F-04).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric G (step cannot produce its evidence) | plan E-02 "Re-run the E-01 probe for that pair"; `tools/mutation_probe.py` probes committed `HEAD` in its own worktree | On the conditional branch, an added test left uncommitted is invisible to the re-probe, so the re-probe would still report `survived`. | all Low | FIXED | E-02 now commits the test file before the re-probe; V-02 demands the `aw commit` output, a `head:` at or after it, and `newly_failing` naming the added test. |
| PR-002 | LOW | IN-SCOPE | Rubric E | plan E-01/V-01 | `verdict` was not tied to a clean baseline, `error`/`invalid` verdicts had no disposition, and `git diff --stat agent_workflows/` only checks the working tree, not commits. | all Low | FIXED | E-01 records `<base>` and requires `baseline_failing: 0`; V-01 checks both `<base>..HEAD` and the working tree. |
| PR-003 | LOW | IN-SCOPE | Evidence accuracy | plan E-02 "`FindingContractTests`-style", "the causal-language control class"; file classes `ContractRefusalTests`, `CausalLanguageTests` | E-02 named classes that do not exist in the file. | all Low | FIXED | Replaced with the real class names. |
| PR-004 | LOW | IN-SCOPE | Rubric E (unsatisfiable bar) | plan E-03 "within its 30s budget"; sibling `3wkrng` F-06 bare run `59.22s`, not enforced | The core tier already overruns 30s on this host before this plan. | all Low | FIXED | E-03/V-03 require exit 0 with no failures and the budget block pasted verbatim, counted against the item only if a test it added appears among the slowest. |
| PR-005 | LOW | UNDER-SCOPE | Execution contract | plan `## Approval and execution gate` | Gate lacked the paste-actual-output rule, a declarative scope fence (including the expected `--scope-ack` when no edit is made), and runner versus hand `aw ipd finalize` ownership. | all Low | FIXED | Gate rewritten to the repo's standard contract. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep a verification-only plan when every key is already guarded? | Keep; it records the verdict at execution HEAD and keeps the conditional remedy | Retire as no-op (leaves backlog `6ntz8v` without recorded evidence) | review re-probes at `2aa1e2fd3` (plan F-04); plan OQ-01 | yes |
| D-2 | How to treat a pre-existing core budget overrun in E-03? | Paste it; not this item's failure unless a test it added is among the slowest | Keep "within 30s" (unsatisfiable on this host) | `conftest.pytest_sessionfinish`; `3wkrng` F-06 | yes |
