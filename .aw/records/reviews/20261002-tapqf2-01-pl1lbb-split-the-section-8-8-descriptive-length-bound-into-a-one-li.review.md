# Review findings: plan pl1lbb

- Subject-Id: pl1lbb
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `033d50385` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review; `--phase review-finalize` was clean after revision.

Re-verified (read-only):
- `python3 -m agent_workflows specs check`, `attention --check --agent`, `check specs`: all exit 1; the two agent
  records each name exactly `.aw/records/specs/to-review/20261001-89xjll-...spec.md` / `attention.unsafe-field`.
  `.github/workflows/tests.yml` runs the first two as named steps.
- Spec `- Scope:` census: 24 specs carry one; exactly one (`89xjll`, 343 chars) exceeds 300.
- `specs.validate_spec` judges `- Scope:` (`scope = _read_scope(lines)`), `Gate-Summary`, and `- Summary:` with
  `A.is_safe_descriptive`; `_render_new_spec` writes `--summary` into `- Scope:`; `run_new` guards `--summary` with
  `_refuse_unsafe_descriptive`, which hard-codes the one-line predicate and bound in its message.
- Probe in a temp repo: `aw specs new --summary <250>` exit 0 and the file validates `[]`; `--summary <400>` exit 2,
  `aw specs new: --summary exceeds maximum length of 300 characters (400 > 300)`.
- Existing tests pinning the old Scope bound: `tests/test_specs_releases_unsafe_field.py`
  `test_spec_scope_unsafe_shapes` (`"x" * 301` over-length shape) and `test_spec_scope_conforming_boundary` (300);
  `tests/test_specs_releases_descriptive_safety.py` `over_summary = "s" * 301` asserting `rc_new == 2` and "300"/"301".
- Backlog `6bolin`: `open`, `Work-Kind: bug`, `Blocks-Release: next`, summary "GrandfatheringAndCheckerTests fails on
  89xjll spec with attention.unsafe-field". `bxnhdj`, `8jeh4x`, `wc5c5e` open. `tapqf2` graduated.
- Bare suite failing set at review (a prior run in this lane at HEAD `0f8de354f`) included
  `test_readiness_absence_invariant.py::test_corpus_partition_pre_review_plans_lack_readiness_field`, not in F-15.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Anti-regression / scope | `tests/test_specs_releases_unsafe_field.py` `test_spec_scope_unsafe_shapes`, `test_spec_scope_conforming_boundary` | E-03 makes a 301-char Scope conform, so two existing tests pinning the amended contract redden; neither file was in Scope-Paths and the plan claimed that suite "must not regress". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 names both tests and the exact update (move to the prose bound, keep control-char shapes and no-echo); file added to Scope-Paths; V-05 demands the diff. |
| PR-002 | HIGH | UNDER-SCOPE | D. Anti-regression / scope | `tests/test_specs_releases_descriptive_safety.py` `over_summary = "s" * 301` | E-04 makes a 301-char `--summary` accepted, reddening this assertion; file not declared. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 names the test and the update; file added to Scope-Paths. |
| PR-003 | MEDIUM | IN-SCOPE | A. Release-gate traceability / OQ-02 | backlog `6bolin` (`bug`, `Blocks-Release: next`) | The live red already has a gated bug record which the plan never cites, so OQ-02 was left open on a false premise (that no gate exists) and `6bolin`'s gate would be orphaned. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Deferred row names `6bolin` as carrier and the post-execution `done --evidence` close; OQ-02 resolved (keep `chore`, gate lives on `6bolin`), recorded as D-1. |
| PR-004 | MEDIUM | IN-SCOPE | E. Unsatisfiable criterion | Required tests "ends at 3 failures, all three named in F-15"; V-05 | Total-count and exact-set demands on a non-green, load- and corpus-sensitive suite; the set already differed at review. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten as a failing-node-id comparison: the target node leaves, none joins. |
| PR-005 | MEDIUM | IN-SCOPE | Evidence / carrier syntax | Deferred row "Carrier: 8jeh4x" + "Carrier-Evidence: ...bxnhdj... (open/)" | `Carrier-Evidence` must cite finished work; citing an OPEN item claims discharge that did not happen. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with `Carrier: 8jeh4x, bxnhdj, wc5c5e`. |
| PR-006 | LOW | IN-SCOPE | G. Executability | E-03 "the two PROSE judgements ... the `- Scope:` check and nothing else"; E-04 helper | Self-contradictory count; E-04 did not say `_refuse_unsafe_descriptive` hard-codes the one-line bound. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 says ONE judgement; E-04 requires a bound selector on the helper with existing callers unchanged. |
| PR-007 | LOW | IN-SCOPE | G. Execution contract | Approval gate paragraph | Missing conditional finalize ownership, scope-fence declaration, dash rule for CHANGELOG; stale "carries no Readiness" sentence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added all three; sentence replaced. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-02: reclassify as `bug` with `Blocks-Release: next`? | Keep `chore`; gate lives on `6bolin` | Reclassify (double-gates one breakage) | `.aw/records/backlog/open/20261001-6bolin-...backlog.md` front matter | yes |
| D-2 | Is two classes with 4300 sound vs. the item's routes? (OQ-01, OQ-03) | Keep the plan's design | Grandfather tier; single raised bound; write-path only | F-02/F-05/F-07/F-08 measurements; spec census above | yes |
| D-3 | Edit existing tests that pin the amended bound? | Yes, minimally, with diff evidence | Leave red; delete them | They assert the exact contract E-06 amends; P16 favors updating behavior tests over deleting | yes |
