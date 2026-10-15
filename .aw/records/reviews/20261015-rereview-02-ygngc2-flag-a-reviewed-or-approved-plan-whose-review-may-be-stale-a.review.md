# Review findings: plan ygngc2

- Subject-Id: ygngc2
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `23863c32a`. Plan committed (`fb917fb58`) and byte-identical to
the lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`. Not an
orchestrator.

Re-measured at HEAD: every cited symbol resolves (`plan_readiness.is_review_history_entry`,
`_open_question_blocks`, `approval_refusals`; `check_engine._blob_text`, `check_ipd_draft_ready`,
`check.ipd-draft-ready-to-review` RuleSpec info; `ipd_lint._draft_ready_advisory`;
`ipd_lifecycle.frozen_region_digest`; `status_set.validate_transition_allowed`, `_demotion_warning`;
`attention._plans_record`, `Item.blocks_release`). Prototype of E-01 over the live tree: 78 candidate
plans (`reviewed` 4, `approved` 74), all 78 have a `plan-review:` commit, 0 flagged. Motivating case
`jmogmv` between `c8a62f9de` and `111f08acf`: OQ-01 `Blocking: yes` open -> resolved,
`frozen_region_digest` equal, so reason (a) detects it. Timing: per-plan `git log` loop 14.2s;
`aw attention --format json` 5.06s; bulk `git log --name-only` + `git cat-file --batch` + digests 0.78s.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric C (performance, user-perceptible) | plan E-01 "Bound cost: one `git log` per plan"; measured 14.2s for 78 plans vs 5.06s `aw attention`; bulk path 0.78s | One `git log` per candidate roughly triples `aw attention` and adds ~14s to `aw check`; by the repo's perceptibility rule this would ship a bug. OQ-01 deferred the fix to "cache per HEAD if slow", an undemonstrated HOW. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now specifies one bulk `git log --name-only` + one `git cat-file --batch` resolver used by every surface (demonstrated 0.78s); E-02/E-04 call it once per sweep, never per plan; OQ-01 revised with the demonstration; F-4 added. |
| PR-002 | MEDIUM | UNDER-SCOPE | Rubric D (compatibility, versioned contract) | `attention.SCHEMA_VERSION = 4` and its additive-bump log; `tests/test_attention.py:118,2162,3759` pin `schema_version == 4`; attention spec F8 | Adding `review_stale` to the JSON items without a version bump breaks that payload's own precedent; the pinned tests and the attention spec were not in scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 bumps to 5, updates the pins as recorded truth, notes the attention spec; both paths added to Scope-Paths. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric C (KISS, single path) | plan E-01 fallback "else the first commit whose diff adds a line accepted by `is_review_history_entry`" | The fallback needs a per-commit diff scan (the slow path) and a second locator, while serving zero live plans (all 78 have a `plan-review:` commit). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fallback removed; OQ-02 records the decision and the limit; E-06 documents it. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric G (executability) | `status_set._prepare_status_change` (`_demotion_warning`), `run_set_command` (`demotion_warnings`, `res_data["warnings"]`); `validate_transition_allowed` returns `(bool, Optional[str])` only | E-03 pointed at `validate_transition_allowed` "or" another location; that function has no warning channel. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 pins the hook to `_prepare_status_change` and the existing warning channel, excludes `auto-approved`. |
| PR-005 | MEDIUM | UNDER-SCOPE | Rubric E (tests) | plan E-05 (pre-review) | Missing cases: `Blocking: no` answered, E-item continuation-line edit, `## Findings`-only edit, rename after review, non-git dir, non-stale approve twin, lint advisory. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 adds each; fixtures carry `.aw/records/` to keep repo-root resolution in the temp dir. |
| PR-006 | LOW | IN-SCOPE | Rubric G (verification strength) | plan V-01..V-06 (pre-review) | V items lacked the info-severity proof shape, the non-stale contrast, and command-level timing evidence. | all Low | FIXED | V-02 demands `rule_spec` severity plus a `drift_exit_code` contrast; V-03 a non-stale twin; V-04 three before/after timings. |
| PR-007 | LOW | IN-SCOPE | Rubric G (execution contract) | plan gate (pre-review) | Gate lacked scope-fence declaration, conditional lifecycle ownership, and a note that the remedy names `ggsdrl`'s not-yet-landed `--yes`. | all Low | FIXED | Gate rewritten. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to bound the git cost? | One bulk `git log --name-only` + one `git cat-file --batch` per sweep. | Per-plan `git log` (REJECTED: 14.2s measured); per-HEAD cache (REJECTED: new state to invalidate, and unnecessary at 0.78s). | review timing at `23863c32a`. | yes |
| D-2 | Keep the history-entry fallback locator? | No. | Keep it (REJECTED: 0 live plans need it, slow path). | 78/78 candidates have a `plan-review:` commit. | yes |
| D-3 | Bump attention `schema_version`? | Yes, 4 -> 5. | Add silently (REJECTED: contradicts the payload's recorded bump precedent). | `attention.py` `SCHEMA_VERSION` comment log. | yes |
| D-4 | Where does the approval warning attach? | `_prepare_status_change` via the `demotion_warning` channel. | `validate_transition_allowed` (REJECTED: no warning channel). | `status_set.py` `_PreparedStatusChange`, `run_set_command`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
