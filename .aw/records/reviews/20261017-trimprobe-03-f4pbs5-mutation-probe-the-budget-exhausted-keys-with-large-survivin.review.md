# Review findings: plan f4pbs5

- Subject-Id: f4pbs5
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `cb60e5c80`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review:
- `tools/mutation_probe.py` CLI: `--timeout TIMEOUT_S` is a probe option ("Timeout in seconds for each
  pytest run (default: 1800)"); `tools.mutation_probe.main` splits argv at `--` and forwards
  everything after it ("post_sep") to pytest as the selection.
- `pytest_timeout` is not installed; pytest rejects `--timeout` (exit 4, no junit file), so
  `tools.mutation_probe.probe` returns `error` "baseline run could not produce junit XML".
- Structure, mapping rule and record columns match Order 02 (`lictgf`), which Order 03 appends after;
  Item-Dependencies `executed:g00ljy, executed:lictgf` matches the gate prose.
- Largest `P3` key at authoring N=3150 (`g00ljy` review record), est about 1,522s for baseline plus
  mutant, so a per-run timeout of 3600s is ample once it is actually applied.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric A/G (wrong command) | plan E-02 step (2) "`-- [-n 6 ...] [--timeout 3600 when the count exceeds 3000]`"; `tools.mutation_probe.main` "combined_pytest_args = list(args.pytest_args) + post_sep"; review demonstration recorded as plan F-04 | `--timeout 3600` was placed after `--`, so it went to pytest, which has no such option. Every key over 3,000 collected tests would end `error`, then `unprovable`, without any probe having run. Those are the high-fan-in helpers this plan exists to probe. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Moved `--timeout` before `--` with the reason stated. F-04 records the demonstration. V-02 demands one pasted command line showing the placement, and Required tests forbid an argument-rejection `error`. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric A/E (false verdict) | plan E-02 step (1) "record the collected count"; `lictgf` F-04 | Same defect as `lictgf` PR-001. A preflight with one unresolvable node id exits 4 but still prints a non-zero count, and the probe then runs nothing and reports `survived`. | all Low | FIXED | Applied the `lictgf` rule: exit 0 with at least 1 collected, a `preflight.tsv` log, drop and re-preflight `not found` args, and `empty selection` -> `unprovable`. Added F-05, and the V-02 join is now required. |
| PR-003 | LOW | IN-SCOPE | Rubric G (edge case) | plan E-01 "A `P3` key absent from this narrowed baseline"; `tools.replay_coverage_diff._collect_function_coverage` "subprocess_only" | A key present in the narrowed baseline with no contexts was not routed to the file-level step. | all Low | FIXED | E-01 now routes `subprocess_only: true` to the file-level step as well (same as `lictgf` PR-002). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Fix the timeout by moving it before `--`, or by installing `pytest-timeout`? | Move it before `--` (the probe's own per-run timeout) | Add a test dependency (out of scope: no code or config edits) | `tools.mutation_probe.main` argument split; plan Scope "OUT: any code or test edit" | yes |
