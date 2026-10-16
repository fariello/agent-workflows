# Review findings: plan jl0bv0

- Subject-Id: jl0bv0
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `38d107d18`. The plan was committed (`66162bd7c`) and byte-identical to the lane input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean`. The plan is a child, not an orchestrator.

Verified:
- F-1 reproduced: `python3 -m pytest -o addopts="" -q tests/test_clean_target_recognition.py` -> `7 failed in 8.94s`.
- Helper `TestCleanTargetRecognition._strip_in_target_residue` at `tests/test_clean_target_recognition.py:212` runs `rm -r --cached .`, `add README.md`, unconditional `commit -m 'Clean residue'` (`check=True`), `clean -fdx`; called at `:82` (clean_repo, `completely-clean-target`) and `:125` (local_repo, `local-only`).
- Backlog `a48b4m` (graduated) carries `Blocks-Release: next`, `Work-Kind: bug`; plan inherits both and `From-Backlog: a48b4m`.
- Executed plans `3m8aix` and `fnnwj3` exist under `executed/`; sibling modules `test_clean_target_control_state.py`, `test_clean_target_zero_delta_e2e.py` exist.
- Mechanism demonstration (OQ-01, a HOW question): scratch copy of the module under `/tmp` with the exact E-01 guard plus a probe print: `7 passed in 42.40s`; `git diff --cached --quiet` returned 0 at BOTH `clean_repo` and `local_repo` in every setUp.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric A/D (claim accuracy) | `tests/test_clean_target_recognition.py:125` `self._strip_in_target_residue(self.local_repo)`; demo probe `DEMO local_repo diff-cached rc 0` x7 | E-01 Expected outcome asserted `local-only` leaves tracked residue that is still committed; demonstrated false: both call sites are zero-delta, so the commit branch is never exercised today. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 Expected outcome and F-2 now state both sites are zero-delta and the nonzero branch is retained for future residue. |
| PR-002 | LOW | IN-SCOPE | Rubric G (test count as bar) | plan `## Required tests / validation` and V-01 "ending in `7 passed`" | A collected test count is an artifact of test organization and may not be a V-item's bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bar rewritten to every collected test passing, zero failed/errors, no setUp `CalledProcessError`, count re-derived at execution. |
| PR-003 | LOW | UNDER-SCOPE | Rubric G (execution contract) | plan `## Approval and execution gate` | Gate lacked scope fence, explicit paste-actual-output honesty rule, and lifecycle transition with runner/executor ownership (`aw ipd finalize` by hand, runner otherwise, no `git mv`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all elements, matching executed sibling `3m8aix`. |
| PR-004 | LOW | IN-SCOPE | Step 3.1 (HOW question / Owner) | plan OQ-01 `- Owner: none` | OQ-01 chose a mechanism without a cited demonstration and recorded no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owner set to `plan author`; resolution cites the scratch demonstration (`7 passed`). |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Guard with `diff --cached --quiet`, or `commit --allow-empty`, or port the reset recipe? | Guard and skip (plan's choice, confirmed). | `--allow-empty` (adds meaningless fixture commit); reset recipe from `test_clean_target_control_state.py` (larger change, needs pre_sha plumbing at both call sites). | Backlog `a48b4m` names both guard forms; scratch demo `7 passed in 42.40s`. | yes |
| D-2 | Keep the commit branch at all, given both sites are zero-delta today? | Keep it. | Delete the commit (REJECTED: would silently leave residue staged-as-removed if a future preset writes tracked files, and changes helper intent). | Demo probe rc 0 at both sites; helper purpose per its name and `fnnwj3`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
