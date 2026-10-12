# Review findings: plan xl1iko

- Subject-Id: xl1iko
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (LOW, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `f8d99c044`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent`: `clean` before review;
`--phase review-finalize`: `clean` after revision. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply.

Verified at review:
- F-01: the five bold bullets in `review-rubric.md` `## A. Plan completeness` match `plan-review.md`
  `### G. Plan executability` in name and order. `Live-artifact` is 355 characters against 1150. The other three
  sliced bullets compared are byte-identical. `Maintainer sizing signals` also differs under a naive slice, but only
  because the long-form section continues with trailing prose after the last bullet. The bullet sentence itself is
  identical.
- Both copies of the target bullet are single lines, so E-01's one-line replacement yields `1 1` in numstat. This
  was prototyped in a detached worktree that was later removed.
- F-03: with E-01 prototyped, the current test fails as the plan predicts (`1 failed, 9 passed`).
- E-02's assertions were prototyped on in-memory copies using `support.section`. HEAD fails (6 anchors missing).
  The reconciled copy passes. A one-word edit to either copy fails on inequality. Deleting the long-form bullet
  raises `SectionBoundError`.
- `LONG_FORM_POINTER_ANCHORS` is referenced only in `tests/test_v_item_evidence_durability.py`.
- The sibling tests (`test_plan_review_feasibility_rule.py`, `test_v_item_demonstration_reachability.py`) assert
  only `assertIn` anchors, so the longer bullet cannot break them.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | E testing (mutation determinism) | Required tests, mutations (b)/(c) "change one word" | The mutation word was unspecified. A word that also occurs outside the bullet could be edited elsewhere and leave the test passing, which would be a false negative on the proof. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The plan now names a token that occurs once per copy (`permitted` in "a test function name is permitted only as a non-binding pointer"). This was verified at review. |
| PR-002 | LOW | IN-SCOPE | E evidence / repo contract | Required tests and V-02/V-03 narrowed runs without `-o addopts=""`; AGENTS.md repository development contract | A narrowed pytest run inherits `-q -n auto` plus the marker filter, so pasted output would lack per-test detail. The contract says to clear the defaults with `-o addopts=""` for narrowed views. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The narrowed runs now use `-o addopts=""`. Bare-suite runs are unchanged. |
| PR-003 | LOW | UNDER-SCOPE | G honesty of expected outcome / C context | E-02 Expected outcome ("FAILS if ... the long-form bullet is deleted"); `.aw/system/managed-sections.json` | If the bullet is deleted, the test raises `SectionBoundError` instead of failing an assertion. It still fails, but the executor should expect an error. Separately, the manifest `sha256` for both files is already stale, which a reader might wrongly attribute to this plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02's expected outcome now notes the error mode and the review demonstration. F-06 records the pre-existing manifest staleness. F-07 records the unrelated pointer and the absence of generated copies. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should this plan refresh the stale `managed-sections.json` hashes? | No. Record them as context (F-06). | Add the manifest to Scope-Paths and refresh it. Rejected because the staleness predates this plan and also covers `plan-review.md`, which this plan must not edit, and fixing it is outside the backlog item. | `git log` of the manifest versus the rubric; `sha256sum` comparison. | yes |
| D-2 | Should the deletion case raise an error, or should it be made a clean assertion? | Accept the `SectionBoundError` and document it. | Wrap it in `assertIn(prefix, section_a)` first. Not required, since either way the test fails, but the executor may add it. | `tests/support.py` `section` "Refuses rather than falls back". | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
