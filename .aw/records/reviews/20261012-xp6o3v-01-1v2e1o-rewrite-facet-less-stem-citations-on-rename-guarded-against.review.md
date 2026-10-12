# Review findings: plan 1v2e1o

- Subject-Id: 1v2e1o
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `d96ab9994` in an isolated review lane. The plan was committed and unchanged (`2c2ef0bee`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified:
- `artifact_refs.plan_reference_rewrites_with_warnings` builds only `name_map`, `whole_stem_map` (`_whole_stem` strips only `.md`) and `legacy_stem_map`. `apply_reference_rewrites` sorts FULL_NAME first and then substitutes the rest with `_boundaried`.
- `artifact_naming.ARTIFACT_TYPE_FACETS` has 10 closed facets. `_CLUSTERED_RE` requires `date-set-nn-id6-slug`.
- `DECISIONS.md` cites `20260722-assess-and-00-49eeuc-assess-and-producers-closing-artifacts-report` facet-less (plus an occurrence inside `.aw/records/plans/STATUS.md`, which `_SKIP_NAMES` excludes). The `49eeuc` record has no same-stem sibling.
- Review census: 2692 facet-less stems; 775 shared (768 `ipd`+`review`, 7 `review`+`spec`); 0 facet-less occurrences of shared stems; 201 facet-less occurrences of 70 unique stems in 89 files.
- `j7dsci` is `approved` (pending), `rlcq7g` is executed, `qrokie` is executed, and backlog `0u0ako` is open. The or061f spec and `DECISIONS.md` each cite the qrokie facet-less stem once.
- `tests/test_artifact_refs_rewrite.py` has 14 tests. `test_call_site_plans_refs_shared_prefix_warning_and_reviews_rewrite` drives `rename plans <id6> --slug ... --apply --no-commit`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness (false positive) | `.aw/records/prompt-library/fix-bar.prompt.md`; `artifact_naming._CLUSTERED_RE`; executed plan `y6gsqw` prose "`fix-bar`" | F-04 asserted that every stem embeds date, set, order and id6. That is false for four undated `prompt-library` records. Their facet-less stem (e.g. `fix-bar`, 6 occurrences in 2 files) is ordinary prose, so the unrestricted key would rewrite prose when such a record is renamed. That is exactly the harm the backlog item warned about. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 `_facetless_stem` now returns `None` unless the name parses as clustered or legacy-timestamp. Added F-08, corrected F-04, and added E-04 test (6). |
| PR-002 | MEDIUM | IN-SCOPE | F. UX / silent-noise | review census: 768 of 1441 plan stems have a same-stem `.review.md` | An unconditional shared-stem warning would print on most plan renames, every time a review record exists, while reporting zero skipped citations. That trains users to ignore it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 warns only when a facet-less occurrence of the shared stem is actually found. Added E-04 test (5) and extended V-03. |
| PR-003 | MEDIUM | IN-SCOPE | C. Performance | `count_legacy_prefix_records` walks `.aw/records` per call | Repeating that walk per renamed pair makes an `aw group` of N records cost N corpus walks. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 builds one stem index per planner call. |
| PR-004 | MEDIUM | IN-SCOPE | Evidence | `research_refs.RefEdit`, `research_refs.apply_reference_rewrites` | E-02 claimed every consumer passes `kind` through. `research_refs` drops it and re-derives `FULL_NAME`/`BARE_STEM`, so a research rename applies `facetless-stem` edits with `_boundaried`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The claim is corrected. Added F-09, which shows the result is outcome-equivalent (only hit counts differ) and that the case affects only 2 research records with closed facets. `research_refs` stays untouched. |
| PR-005 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | E-04/V-04 "18 passed (14 prior + 4 new)"; E-05 "zero failures" | Test counts and a fully green bare suite were used as pass bars. Another party's failure would block a correct execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bars are now baseline test names compared by name, plus base-commit failures of tests (1), (2), (4). The bare suite is compared against a pre-change baseline. Census counts are re-measured as context. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the OQ status line, the MUST-paste honesty rule, `aw ipd begin`, the instruction that the executor must not finalize under a runner, and the no-`git mv` rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All of those elements were added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Restrict the facet-less key to dated record names? | Yes (clustered or legacy-timestamp only) | Admit every closed-facet name (rewrites prose like `fix-bar`); guard by a prose heuristic (undecidable) | review census F-08; `artifact_naming._CLUSTERED_RE`, `_LEGACY_TIMESTAMP_RE` | yes |
| D-2 | Warn on every shared stem, or only when a skipped citation exists? | Only when one exists | Unconditional, as the legacy-prefix warning does (fires on ~half of plan renames for nothing) | 768/1441 plan stems paired with a review; 0 shared-stem facet-less occurrences | yes |
| D-3 | Change `research_refs` so it preserves `kind`? | No | Thread `kind` through `research_refs.RefEdit` (touches a third module for a count-only difference) | `research_refs.apply_reference_rewrites`; 2 research records with closed facets | yes |
