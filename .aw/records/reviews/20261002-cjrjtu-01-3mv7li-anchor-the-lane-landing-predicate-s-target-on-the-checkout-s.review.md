# Review: Anchor the lane landing predicate's target on the checkout

- Subject-Id: 3mv7li
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean.

THE DEFECT REPRODUCES EXACTLY. All of these were re-derived in this lane on git 2.43.0, on a throwaway checkout under `/tmp`, with a production-shaped lane (`worktree add -b aw/lane/abc123 <path> <explicit-sha>`, then one commit). Each reading is main root vs lane root:

- Unmerged lane:
  - Raw `merge-base --is-ancestor <br> HEAD`: rc 1 vs rc 0.
  - `lane_work_has_landed`: False vs True.
  - `inspect_lane` `merged_into_target`/`reclaimable`: False/False vs True/True, with `state=HOLDS-WORK` and `commits_ahead=1` from both roots, which confirms F-2.
  - `classify_lane_integration` `landed`/`landed_by`: False/None vs True/ancestor, with `integration_target=HEAD` from both.
- Merged lane (`merge --ff-only`): True/reclaimable from both roots.

This is a gated `bug` and the plan's direction is right.

ONE DESIGN DEFECT, measured. The authored primitive returned the main worktree only when the common dir is named `.git`, and `None` otherwise. That makes every lane in a separate-git-dir, submodule, or bare-with-worktrees checkout unanswerable. Those lanes would then fail `attention --check` as `lane-unknown`, and genuinely landed lanes could not be reclaimed. OQ-01's cost claim ("only a bare repository") missed this.

Resolving the target through the common dir (`git --git-dir=<common> rev-parse --verify <target>^{commit}`) answers every layout. Prototype results (main root / lane root):

| Layout | Unmerged lane | Merged lane |
|---|---|---|
| Normal | False / False | True / True |
| Separate-git-dir | False / False | True / True |
| Bare with linked worktrees | False / False (raw lane rc 0) | not measured |

An empty bare repository returns None. `git cherry` with the target resolved this way prints `+` from both roots.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness / regression risk (A, D) | agent_workflows/ipd_lifecycle.py:365 `checkout_control_root` (`if common_dir.name == ".git" and common_dir.parent.is_dir()`); review probe: separate-git-dir `checkout_control_root` -> `start/.aw`, common dir `<x>/store.git` | Anchoring on a "main worktree" derived by the `.git`-name test turns every lane in a non-`.git` common-dir layout into `None`. That fails `attention --check` and blocks reclaiming landed lanes. OQ-01 asserted the cost was bare-only. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | The primitive now returns the common dir, and `checkout_control_root` keeps its own `.git` test. The target is resolved with `--git-dir=<common>`, which was prototyped as correct on 3 layouts. New E-06(e) separate-git-dir case; V-02, V-03 and V-06 extended; OQ-01, F-6 and the Goal reconciled. |
| PR-002 | MEDIUM | IN-SCOPE | Evidence accuracy | `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` line "F3a `aw attention --check` also fails closed on an UNINTEGRATED LANE" | The spec-sync section claimed no spec with that slug exists, which would make F3a a dangling citation. It exists, under a legacy filename. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Paragraph corrected to cite the spec path and F3a. No spec amendment is needed. |
| PR-003 | MEDIUM | IN-SCOPE | Validation honesty / live criteria | E-07 "Authoring measured ... `152 passed`"; sibling lanes measured 3 pre-existing bare-suite failures on 2026-10-02 | E-07/V-07 had no bare-suite baseline, and the authored count served as the expectation. A pre-existing red would be unattributable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A pre-E-02 bare baseline is now required, the bar is no new failure, and 152 is context only. |
| PR-004 | MEDIUM | UNDER-SCOPE | Execution contract | plan `## Approval and execution gate` | The gate was missing the scope-fence declaration semantics, the paste-actual-output rule, and conditional finalize ownership (and did not forbid a hand `git mv`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three added, plus the release-gate handoff note. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which anchor resolves the symbolic target? | The git common dir, via `git --git-dir=<common> rev-parse --verify <target>^{commit}` | Main worktree via the `.git`-name test (authored; breaks separate-git-dir, submodule and bare-with-worktrees); `checkout_control_root(...).parent` (rejected by the plan itself, F-10) | Review prototype on 3 layouts, pasted in the Round 1 summary | yes |
| D-2 | Should `checkout_control_root` change its behavior for separate-git-dir? | No; it keeps its `.git` test, and the refactor stays byte-identical | Unify both onto the common-dir answer (widens blast radius and changes `.aw` placement) | plan E-02 "PURE REFACTOR"; spec 7ckptx R6.1 is satisfied by sharing the git invocation | yes |
| D-3 | Does F3a need a spec amendment? | No | Amend F3a | F3a states the requirement; this plan corrects an input, not the requirement | yes |
