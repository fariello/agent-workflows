# Review findings: plan 6g08rp

- Subject-Id: 6g08rp
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`b3302e286`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize --agent` clean after revisions.

Re-verified at review HEAD:
- Spec `25kzda` `### 5.5 Retry policy` at line 1380, `### 5.6 Reporting` at 1491, `## Workflow history` at 1744. Table rows at 1446-1457 carry exactly the stale tokens F-01..F-04 name; line 1468 says `approved plan \`ytas91\` introduces`.
- `k8n97m`, `120bhh`, `b8w5o6`, `5j73i6` resolve to no record (`grep -- "- Id: <t>"` over `.aw/records`; `selectors.resolve(... 'plans','k8n97m', allow={MATCH_ID6})` -> no paths).
- Orchestrator `lxb1ew` `## Child IPDs` (lines 98-109) and each child's `- Order:`: 02 `tha7a6`, 04 `ytas91`, 05 `w9nvq4` (hook refusal and red combined suite), 06 `psgyzw` (out-of-scope), 07 `62sdwr` (untooled status, hook bypass); all `- Status: executed`. The plan's eight E-01 mappings are correct.
- `iksylm` F-06 confirms `ytas91` does not cover verifier transport failure.
- `yd4tqw` is pending `to-review`; its E-05 writes `Implementing: yd4tqw (from backlog jodcz3).` (no backticks) and has no step flipping it to `Shipped`.
- `aw specs check` on the spec: conforms, exit 0. `aw sanitize --agent`: clean.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Evidence / G. Executability | `tests/test_fixfirst_end_to_end.py` (no `locate_spec_25kzda`; `test_e05_spec_abort_classes_match` at ~1251 checks `ABORT_CLASSES` vs 4.1); `tests/test_retry_budget_citation.py:24` `locate_spec_25kzda(repo_root)` | E-03 and Step 0 said the module already has `locate_spec_25kzda()` at line 88 and that the E-05 test cross-checks Section 5.5. Neither is true; line 88 is `_setup_matrix_run`. An executor would call a nonexistent helper. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Step 0 corrected; E-03 now adds a local `_locate_spec_25kzda` mirroring the `test_retry_budget_citation.py` locator. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing | E-03 (b) listed a fixed token set; no negative case | The test hard-coded the expected id6 set (including `l4vw9o`, which does not appear in 5.5 at all) and had no contrastive case, so it could not prove the guard fires and would not cover a newly added stale id. Clause (c) checked only five ids and `Shipped`, not that the cited Order matches the plan's `- Order:`, which is exactly F-02's defect class. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now specifies a pure checker that derives backticked id6 tokens from the Notes column, checks every `Order NN, <id6>` citation against the plan's `- Order:`, Set and `executed` status, plus a mutated-copy test that must yield problems for three regressions. V-03 demands both tests' output and the diff. |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness / cross-plan | `.aw/records/plans/pending/20261014-jodcz3-01-yd4tqw-...ipd.md:57-59` (E-05) | OQ-01 claimed `yd4tqw` E-05 flips the row to `Shipped` on execution; it does not, it writes `Implementing: yd4tqw (from backlog jodcz3).` E-02 also gave no rule for when `yd4tqw` already rewrote the row. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 corrected and records the residual (row stays `Implementing:` after `yd4tqw` executes if `6g08rp` runs first; not fixable by this plan). E-02 re-derives `yd4tqw` location via `aw find`, normalizes an existing `yd4tqw` wording, and leaves the `verification_retry_decision` bullet to `yd4tqw`. |
| PR-004 | LOW | UNDER-SCOPE | D. Invariants | Step 0 note on `spec_citations.new_stale_anchors`; V-02 | The line-offset-preservation invariant had no evidence demand. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 now demands `git diff -U0` showing only same-line replacements above `## Workflow history`, plus the `aw find` output that chose the prefix. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate told the executor to run `aw ipd set executed 6g08rp` (bypassing finalize) and lacked a scope fence, honesty rule, never-push, and conditional runner/executor finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Wrote a full execution contract matching repository convention. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where should the Section 5.5 owner check get the spec path? | Local `_locate_spec_25kzda` mirroring the existing one | Import from `tests/test_retry_budget_citation.py` (cross-test-module coupling) | `tests/test_retry_budget_citation.py:24` | yes |
| D-2 | Should the checker require `Shipped` on the `verifier transport failure` row? | No; accept `Implementing:` or `Shipped` | Require `Shipped` (would go red when `yd4tqw` executes without flipping its own row) | `yd4tqw` E-05 wording, lines 57-59 | yes |
| D-3 | Should the live-spec test be marked `livecorpus`? | No; it reads one named spec and resolves the ids it cites, the "read ONE named artifact" shape | Mark `livecorpus` (would deselect it from the default suite) | `tests/livecorpus_notice.py` docstring on single-artifact reads | yes |
