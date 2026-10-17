# Review findings: plan lictgf

- Subject-Id: lictgf
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `9ecf555b8`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review:
- `tools/mutation_probe.py` CLI (`--op`, `--extra-test COMMIT:PATH`, `--format json`, positional
  `pytest_args` after `--`) and `ProbeResult` fields `head`, `verdict`, `wall_s`,
  `extra_tests_overwrote`, `checkout_status_changed` match every name E-02/V-02 use.
- `tools.mutation_probe.probe` with no selection falls back to `-n auto -m "not slow and not
  livecorpus"` (Step 0 claim correct); it builds a disposable `git worktree add --detach ... HEAD`
  and removes it in `finally`, so `git worktree list` unchanged across the batch is attainable.
- `tools.replay_coverage_diff.run_baseline` accepts extra pytest args after `--` and prints `head`,
  `xdist`, `functions`, `subprocess_only`, `wall_s`; `_build_pytest_cmd` already adds
  `-m "not slow and not livecorpus"`, so the plan's repeated `-m` is redundant but harmless.
- `rf1xxr` E-02 mapping rule matches the one this plan restates; `b1mx2w` `## Rollup mutation results`
  row for `check_engine.py::check_system_layout` reads survivor `survived`, control `killed`
  (newly_failing 11) (F-03 correct).
- Orders 03/04/05 reference `## Budget probe results` with "Order 02 columns", consistent with E-03.
- `records/research/INDEX.json`/`INDEX.md` are gitignored, so `aw research index` adds no path to the
  commit; `.aw/state/` is gitignored.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric A/E (false verdict) | plan E-02 step (1) "record the collected count"; `tools/mutation_probe.py` `probe` "candidate_newly_failing = mut_fail - base_fail"; review demonstration (plan F-04) | The preflight only recorded a collected count. Demonstrated at review: one unresolvable node id among valid ones makes pytest print `ERROR: not found` and exit 4 while still reporting `1 test collected`, and the real run then executes nothing (`tests="0"`), which `probe` reports as `survived`. Re-derived node ids can go stale (a test renamed or a context not mapping to a file), so the plan's own guard against the `g00ljy` F-04 false `survived` was incomplete. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 requires exit 0 and at least 1 collected, logs every preflight to `preflight.tsv`, drops `not found` args and re-preflights, and maps a key with no usable selection to `unprovable` (`empty selection`, the `rf1xxr` reason); F-04 records the demonstration; V-02 and Required tests check the join. |
| PR-002 | LOW | IN-SCOPE | Rubric G (edge case) | plan E-01 "A `P2` key absent from this narrowed baseline"; `tools.replay_coverage_diff._collect_function_coverage` "subprocess_only: len(sorted_contexts) == 0" | A key present in the narrowed baseline with no test contexts (`subprocess_only: true`) yields an empty node-id selection, but the plan only routed the ABSENT case to the file-level fallback. | all Low | FIXED | E-01 routes the `subprocess_only: true` case to the file-level step as well. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | When some re-derived node ids no longer resolve, drop them or fail the key? | Drop the unresolved ids, record their count, re-preflight; fall back to files if none remain | Mark the key `unprovable` on any unresolved id (discards a usable narrowed selection); keep them (false `survived`, F-04) | Review demonstration recorded as plan F-04; `rf1xxr` E-02 step 2 "empty selection" reason | yes |
