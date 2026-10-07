# Review findings: plan yqv6b7

- Subject-Id: yqv6b7
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was committed and byte-identical to the lane input, so no
pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; `--phase review-finalize` after revision:
`clean`. Not an orchestrator, so S407/S408 do not apply.

Verified in code: `plans_refs._ORDER_LINE_RE` and `artifact_rename._ORDER_LINE_RE` are both
`(?m)^- Order:\s*(\d+)\s*$`; `plans_refs._set_metadata` substitutes, returns early only when both Set and Order
lines match, else inserts after `- Id:`; `_validate_plan_order` returns None unless `Kind: child`;
`plan_set_assign` resolves `start_order + i` or `_preserved_order` and returns `(None, err)` before any write;
`run_mv` resolves `order` from `--order`, `om`, or the filename and then calls `_validate_plan_order`;
`artifact_naming.build_clustered_name` formats `{order:02d}` with no range check; `artifact_types` routes plan
`rename`/`group` to `plans_refs.run_mv`/`run_set_assign`; backlog `bmhoxe` is `graduated` with
`Blocks-Release: next`; `xvi55d` pending, `qhcojn` executed; both named existing test files exist.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A (partial failure) / evidence | E-03 "raise a `ValueError` naming the plan otherwise, which the callers already turn into a refusal"; `plans_refs.apply_renames` calls `_set_metadata` then `_core.atomic_write` and `_core.git_mv` per plan with no `try`; `run_set_assign`/`run_mv` call `apply_renames` unguarded | The claim is false. A raise would print a traceback, not exit 2, and on a batch it would fire after earlier plans were already rewritten and moved. That is the partial corruption this plan exists to prevent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires a compute-all-texts pre-pass in `apply_renames` before any write, plus `ValueError` -> `error:`/exit 2 in both verbs. Its expected outcome and V-03 now require a forced raise to leave every plan unchanged and unmoved. |
| PR-002 | MEDIUM | IN-SCOPE | E (mutation test validity) | E-04 "Prove the test can fail by removing the E-01 call and pasting the duplicate-field failure" | Once E-03's widened regex is in place, removing only the range check no longer produces a duplicate field: substitution matches `-1` in place, so the demanded failure cannot occur. Removing only "the E-01 call" also leaves the rename path's E-02 check in place. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with M1 (remove the E-01/E-02 calls: fails on exit code and `--1` filename) and M2 (also restore the old regex: reproduces `IPD-M102`). E-04 and V-04 are updated. |
| PR-003 | MEDIUM | IN-SCOPE | E (boundary test) | E-01 outcome "`--order 98` on two plans refuses the second (resolved 99 is allowed, 100 is not)" | `--order 98` on two plans resolves to 98 and 99, both valid, so the stated refusal cannot happen. The boundary case needs `--order 99`. | Overall:Low | FIXED | E-01 and V-01 now use `--order 99` (refuses resolved 100, writes nothing for either) and `--order 98` (succeeds). Preview without `--apply` is also covered. |
| PR-004 | LOW | IN-SCOPE | G (evidence specificity) | V-03 "list each other reader of the regex" | The readers were not named. | Overall:Low | FIXED | V-03 names `_preserved_order`, `run_mv`'s `om`, and `artifact_rename`'s substitution and line match. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the `_set_metadata` backstop fail safely? | Pre-pass computes every text before any write; verbs map `ValueError` to exit 2. | (a) Drop the assertion. REJECTED: loses the fail-safe the backlog item asked for. (b) Catch per plan mid-loop. REJECTED: leaves earlier plans written. | `plans_refs.apply_renames` loop body; `run_set_assign`/`run_mv` call sites. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
