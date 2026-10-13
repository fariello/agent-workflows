# Review findings: plan ev7t1w

- Subject-Id: ev7t1w
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `fd2b21d66`. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and `--phase review-finalize` was clean after revisions.

Re-verified:
- The Set measurement command (verbatim from `yuhl6o`) over the 17 source files prints the same 27 hits as S-01..S-27, `UNRETIRED 27`; enclosing symbols match.
- The AST-equivalence command against `HEAD` over the 17 files prints `AST-DIFFER []`.
- F-01 (`tools/lost_guard_census.py` `print_classifier`, `git_show(... "80db6750c^:tests/test_orchestrator_probe_cache.py")`, `mixed_example`) and F-02 (`ipd_lifecycle._run_record_committed_paths` incident narrative) are as described and correctly excluded.
- Removal history: `git show 80db6750c -- tests/<file>` removes `test_no_hardcoded_reviews_path_in_check_engine` (S-08), `test_wired_into_the_plans_type_content_path_exactly_once` with `src.count("check_review_decision_unescalated")` (S-10), `SourceInvariantTests.test_every_structural_invariant_holds` (S-17/S-18), `test_render_stream_imports_no_first_party_module_that_could_cycle` (S-22), `test_facet_enum_tuple_literal_defined_in_exactly_one_module` (S-03/S-05/S-20). `git show 19313eed^:tests/test_review_findings.py | grep -c test_no_hardcoded_reviews_path_in_check_engine` is 0. Guards named in sibling `9rthek` all survive to `19313eed^` (checked), so the issue is local to this plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Evidence / D. Honest documentation | `git show 80db6750c -- tests/test_review_findings.py` (`test_no_hardcoded_reviews_path_in_check_engine`); `tests/test_review_decisions.py` (`src.count(...)`); `tests/test_review_findings_gate.py` (`SourceInvariantTests`); `tests/test_refusal_surfacing.py` | E-02 told the executor to confirm S-08/S-10 from `git show 19313eed^:<path>`, but neither test exists there; they were removed in `80db6750c`. The same is true for S-17/S-18/S-22 and likely S-03/S-05/S-20. Applying the uniform "deleted in `19313eed`" wording would misdate every one of those removals in shipped prose, and the measurement cannot detect it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Findings F-03. E-02 now records a `Removed-by` commit per site found with `git log -S`, and E-03 requires `80db6750c` sites to name it (with `19313eed` as the later file deletion), following `dtelfb`. V-02 and V-03 demand the evidence. |
| PR-002 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | E-02 "27 (plus deltas)" | The bar was the authoring count of a drifting population. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bar is now one row per E-01 hit, re-derived; 27 kept as context. Findings records the review-HEAD re-measurement. |
| PR-003 | MEDIUM | IN-SCOPE | E. Evidence sufficiency | E-03 expected outcome; V-03 | `UNRETIRED 0` proves only that `19313eed` is nearby, not that the text is true. V-03 did not demand the edited passages. S-10/S-11 also give a design reason ("a prose mention would fail" the counter) that no longer binds. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 requires true-at-HEAD prose, forbids non-prose changes, and keeps the S-10/S-11 reason as history. V-03 demands each passage quoted. |
| PR-004 | LOW | UNDER-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the OQ status line, scope fence, the MUST-paste honesty rule, staged-set verification, the concurrent-edit stop, runner/executor ownership of begin/finalize, and the no-`git mv` rule. E-04 had no rule for a pre-existing failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten in the sibling `65d5zf` shape; E-04 and V-04 require a pre-existence re-run. |
| PR-005 | LOW | IN-SCOPE | Plan hygiene | OQ-01 `- Owner: none` | A resolved question carried no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Name `80db6750c` in the rewritten prose where it removed the guard, though the Set measurement keys only on `19313eed`? | Yes; name both, so the measurement still sees `19313eed` and the history is correct | Uniform "deleted in `19313eed`" (misdates removals); change the Set measurement to accept either sha (edits a sibling's shared command, wider blast radius) | `git show 80db6750c -- tests/...` excerpts above; sibling `dtelfb` E-05 names `80db6750c` for the same reason | yes |
| D-2 | Leave the per-site `Removed-by` to the executor rather than fixing it in the review? | Yes; the review lists known `80db6750c` sites, and E-02 re-derives for all 27 | Hard-code a full table now (would skip the execution-time check) | E-02 evidence rule | yes |
