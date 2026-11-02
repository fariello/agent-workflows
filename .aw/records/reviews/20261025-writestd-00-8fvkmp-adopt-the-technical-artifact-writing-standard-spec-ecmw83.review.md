# Review findings: plan 8fvkmp

- Subject-Id: 8fvkmp
- Subject-Type: ipd
- Reviewed-At: 2026-11-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `3c7a96799` in a runner review-sweep lane worktree (non-interactive). The lane-input
copy (revision 1) is byte-identical to the tracked plan (committed, unmodified), so no pre-review
snapshot. `aw ipd lint --phase author` clean and `aw ipd coverage 8fvkmp` "ready for review" before
revisions. After revisions `--phase review-finalize` first reported `IPD-S408` because the gate text
changed the coverage fingerprint; the re-probe passed, and the lint is now clean.

Note on lane state: this lane also holds the round-1 review of child `k2x0yl` (commit `3c7a96799`).
The `g4719s` review commit `9b2d88cfd` sits on `aw/parked/run-20261102T043053Z-1740891/g4719s`, not on
this lane, so in this tree `g4719s` still reads `to-review`. Its blocking OQ-01 is cited from that
review.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Completion criteria | Unqualified `AC-0n` ids | Qualified `ecmw83` AC-0n | Spec trace convention (89xjll 6.2b). |
| Completion criteria, `jhdti8` row | "Runner plan-production prompts name the standard" | Adds that review turns reach it through workflow bodies | Matches `jhdti8` Scope and `build_review_prompt`. |
| Cross-IPD validation | "`yz4jdm` V-04 ... assert the named path exists in an installed repository" | Names the creating E-items and limits the installed-repository claim to `gzhw9c` and `e4n4p3` | `yz4jdm` E-04 asserts the written file names the path; it does not install. |
| Cross-IPD validation | "`sfez3e` V-05 and `uog8nc` V-02 paste its output" | States what each pastes, and notes no cutover | Exact match to the child V-items. |
| Gate | Partial execution contract | Spec-approval precondition, child OQ precondition, fence as declaration, paste output, retirement ownership, finalize, never `git mv` | S7 rule. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step R1

- Checked: every row of `## Child IPDs` against the child files' `- Id:`, `- Order:`, `- Kind:`, `- Item-Dependencies:` (all match); `3bwrfx` is in `executed/`; spec `ecmw83` R-01 to R-11, AC-01 to AC-08, G1 to G4, status `to-review`; each cross-IPD claim against the named child V-item and the E-item that creates its test (`gzhw9c` E-04, `yz4jdm` E-04, `e4n4p3` E-07, `sfez3e` V-05, `uog8nc` V-02, `381ml6` V-04 and E-01 baseline); `jhdti8` Scope (excludes `build_review_prompt`); `runner_shared.edge_satisfied` (a `state:` edge requires the EXACT status for an execute turn).

### Step R2

- Checked: E/V bijection 9/9; each E/V a CONFIRM row bound to a child id6 with `aw find plans` evidence (non-tautological, reachable); Scope-Paths is the plan itself; `aw ipd coverage 8fvkmp` ready; E-item `Depends on:` matches the child edges (E-06's missing `3bwrfx` is external to the Set and lives on `e4n4p3` itself).
- Spec trace pooled over the ten Set plans (`production_checks._compute_spec_trace_coverage`): uncovered requirements G1 to G4, R-01 to R-03, R-05, R-06, R-08 to R-11 and acceptance criteria AC-01 to AC-04, AC-06 to AC-08 in this lane. These are child-plan citation-form gaps (children cite unqualified `R-0n` or put the id after the field colon). They matter once the spec reaches `implementing`: `run_selection_policy.implementing_spec_needs_plan` would queue a plan-production turn. They are owned by each child's own review (as `g4719s` and `k2x0yl` round 1 already did) and are not orchestrator work.
- Probed `state:spec:approved:ecmw83` on the orchestrator through `aw ipd dependencies set` (which commits itself: `936036230`), then reverted to `none` (`eb25dfd88`). The edge would block the parent permanently once the spec advances to `implementing`, because `edge_satisfied` requires the exact status. Net effect on the plan: two `same-status` history lines.

### Step R7

- Checked: Set-wide ordering and dependency DAG (matches the Mermaid diagram); every spec requirement R-01 to R-11 has an owning child (Scope check claim holds); no two children own the same deliverable; `g4719s` (reviewed in a parallel lane) carries blocking OQ-01, which gates every child depending on `executed:g4719s`; `k2x0yl` round 1 removed the advisory's authoring-date cutover so the sweeps can see pre-existing dashes (consistent with this plan's cross-IPD claim).

### Step S5

- Checked: no open questions on the orchestrator. Human-only items already have an owner: spec `ecmw83` approval (maintainer, gate text) and `g4719s` OQ-01 (blocking in that child). No new question.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | medium | UNDER-SCOPE | G execution contract | plan gate; spec `ecmw83` "- Status: to-review" | The gate did not say the spec must be approved before children run, and did not carry the full contract (fence as declaration, finalize ownership, no hand `git mv`, no `git add -A`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Gate rewritten. A `state:spec:approved` edge was tried and rejected (D-1). |
| PR-002 | low | IN-SCOPE | R1 references | `yz4jdm` E-04 "runs each of the three verbs with `--apply` in a temporary repository" | The cross-IPD bullet claimed `yz4jdm` V-04 asserts the path exists in an installed repository; it does not install. | Low | fixed | Bullet narrowed and names the creating E-items. |
| PR-003 | low | IN-SCOPE | G spec trace | `production_checks._compute_spec_trace_coverage` `cite_pattern` | Completion criteria cited unqualified AC ids. | Low | fixed | Qualified with `ecmw83`. Child-level trace gaps recorded in Step R2 for the children's reviews. |
| PR-004 | low | IN-SCOPE | R7 cross-plan | `jhdti8` Scope "EXCLUDES `build_review_prompt`"; spec `ecmw83` R-06 "authoring and review prompts" | The completion criterion did not say how review prompts satisfy R-06. | Low | fixed | Criterion names `e4n4p3` as co-owner through workflow bodies. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Encode "spec `ecmw83` approved" as an `Item-Dependencies` edge on the orchestrator? | No; state it in the gate | `state:spec:approved:ecmw83` on the parent or on every child | `runner_shared.edge_satisfied` requires the exact status for execute turns, so the edge would block forever once the spec reaches `implementing`; probe and revert in commits `936036230`, `eb25dfd88` | yes |
| D-2 | Fix the Set-wide spec-trace gaps in the children from this review? | No; record them for each child's own review | Edit nine children here | Plan-review scope is the named plan; `_findings.md` "fix it in the owning plan" | yes |
