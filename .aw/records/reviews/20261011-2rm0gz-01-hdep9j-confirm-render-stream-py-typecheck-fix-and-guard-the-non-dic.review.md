# Review findings: plan hdep9j

- Subject-Id: hdep9j
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `ef4fbfa96`. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and `--phase review-finalize` was clean after revisions.

Re-verified:
- `render_stream.render_run_summary_table`, branch `elif st in ("fail-depend", "dependency-blocked"):` carries `reasons_map = reasons if isinstance(reasons, dict) else {}` with no `type: ignore`.
- `python3 -m mypy agent_workflows/render_stream.py`: "Success: no issues found in 1 source file".
- `python3 -m pytest -o addopts="" -q tests/test_dependency_block_reporting.py`: "19 passed".
- `tests/test_dependency_block_reporting.py` has `_diag_lines`, `test_frozen_record_no_duplicate_parenthetical_or_blocked`, and imports `Palette`, `render_run_summary_table`; no test feeds a non-dict `unsatisfied_dependency_reasons`.
- Demonstrated: for `reasons` = `["executed:aaa111"]` and `"executed:aaa111"`, `d in reasons` is True and `reasons[d]` raises `TypeError`, so the pre-fix code crashes on these shapes.
- `aw ipd lint --phase pre-transition` reported `check.ipd-uncarried-obligation` on deferred rows 1 and 2 (the error the CI records job fails on).
- Backlog `2rm0gz` is `open`, `Blocks-Release: next`, `Work-Kind: bug`; the plan inherits both.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Records conformance | `aw ipd lint --phase pre-transition`: `check.ipd-uncarried-obligation` "deferred row 1, deferred row 2 ... NO durable carrier" | Both deferred rows lacked a carrier, so the plan could never pass pre-transition and it adds to the `aw check plans` error that fails CI. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Row 1 carries `ezyb4a` (whose E-05 owns the other mypy errors). Row 2 is `Carrier-Declined` (a design choice). The finding is gone at pre-transition. |
| PR-002 | HIGH | IN-SCOPE | E. Test soundness | `render_stream.render_run_summary_table` `if deps else "unmet dependencies"` and `if d in reasons_map` | E-02 did not require that the non-dict value contain the dependency token, or that `unsatisfied_dependencies` be set. Without both, the test passes with or without the narrowing and guards nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires both. It also requires a mutation proof (`reasons_map = reasons` makes the test fail), followed by a restore with `git diff --quiet`. V-02 demands pasted failing output. |
| PR-003 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the open-question status, the scope fence (including `--scope-ack` for `render_stream.py`, which is likely untouched), the paste-output rule, and conditional runner/executor finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all of these. |
| PR-004 | LOW | IN-SCOPE | G. Ownership | OQ-01 `- Owner: none` | A resolved question needs an owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set to `plan author`. |
| PR-005 | LOW | IN-SCOPE | Workflow history order | `## Workflow history` | The history was oldest-first, but the convention is newest-first. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reordered; the review line is on top. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Who carries the other 15 mypy errors? | Plan `ezyb4a` E-05 | File a new backlog item (it would duplicate `ezyb4a`) | `.aw/records/plans/pending/20261012-cihealth-01-ezyb4a-make-ci-pass-again-on-every-leg.ipd.md` E-05 | yes |
| D-2 | Is the mutation proof in scope for a test-only item? | Yes, with restore verification and no commit of the mutation | Trust the pass alone (it cannot show the test discriminates) | the `TypeError` demonstration above | yes |
