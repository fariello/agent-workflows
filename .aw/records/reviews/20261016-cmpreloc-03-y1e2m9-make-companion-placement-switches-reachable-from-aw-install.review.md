# Review findings: plan y1e2m9

- Subject-Id: y1e2m9
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane after `833719577` (the `fo08zx` review, which added the dated cross-reference this plan carries). The plan was committed, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before and `--phase review-finalize` clean after revisions.

Re-verified: `install_wizard.resolve_policy_noninteractive` "companion = explicit_companion or existing_policy.companion_dir" (F-04); `project_context.resolve_project_context` records branch default `f"{repo_abs}.aw"` (F-05); `cli._run_install` fresh-install attach block "if getattr(policy, \"companion_dir\", None):" (F-03); `install_wizard.collect_policy_interactive` "Enter companion directory path"; `persist_project_policy` carries an existing `companion_dir` for a companion backend; `ozr356` adds `--relocate-resume`/`--relocate-rollback` and `render_plan`; `ozr356` E-03 and `engine.prompt_and_run_commit` (path-scoped installer commit under `-y` for a non-clean-delta install); CHANGELOG `## 2.0.0 (pending)` and README `### Placement Presets and Storage Backends` exist; spec `20260810-1447-01` is `implemented` with `## 8. Installer and wizard requirements` (Section 8.1 is added by `ppu39q`, not yet executed; E-03's stop clause covers that).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A/G. Reachability | `xc8nae` E-02 (interim `companion-unsupported`); `fo08zx` E-06 (`allow_companion` opt-in) and this plan's own history cross-reference | No E-item removed the interim blocker, so after E-01 every companion `--relocate` would still refuse and E-04 cases (1), (2), (4) and (5) could not pass; the three Order 01/02 test modules that pin the interim behavior were outside `- Scope-Paths:`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-05/V-05 removes the blocker and keyword in the same commit as E-01's attach gating, retargets the three modules (added to Scope-Paths) preserving each protected behavior, with a stop clause if the chain differs; E-04 depends on E-05 and runs `tests/test_placement_switch_plan.py` too. |
| PR-002 | MEDIUM | IN-SCOPE | E. Test soundness | `ozr356` E-03 "under `-y`, commits installer paths"; `engine.prompt_and_run_commit` | E-04 case (2) asserted target `git rev-list --count HEAD` unchanged under `-y`, but a non-clean-delta install may legitimately make a path-scoped installer commit, so the assertion could fail on correct behavior while missing the real invariant (the switch's own changes are not committed). | Overall:Low | FIXED | Case (2) now asserts `HEAD` still contains the moved record and `project.json` and the companion commit count is unchanged. |
| PR-003 | LOW | IN-SCOPE | E. Evidence | E-02 "No em or en dashes in any rendered string"; V-02 | V-02 did not demand evidence for the dash rule on rendered output. | Overall:Low | FIXED | V-02 adds a pasted 0-dash check on the preview output. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where does the interim blocker removal land? | This plan, same commit as the attach gating | A separate follow-up plan (leaves the Set unable to reach its Goal) | `fo08zx` OQ-03, F-07; this plan's history cross-reference | yes |
| D-2 | Assert the target commit count unchanged in case (2)? | No; assert content of `HEAD` instead | Keep the count (fragile against today's installer commit) | `ozr356` E-03; `engine.prompt_and_run_commit` | yes |
