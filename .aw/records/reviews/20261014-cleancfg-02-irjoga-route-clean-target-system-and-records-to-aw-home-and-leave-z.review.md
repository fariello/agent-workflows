# Review findings: plan irjoga

- Subject-Id: irjoga
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `cf0e740fe` in an isolated review lane. The plan was committed and unchanged, so no snapshot was taken. `aw ipd lint --phase author --agent` was clean before the semantic review. After revisions, `--phase review-finalize` reports only the two intended `IPD-Q501` blocking-question errors.

Measured with temp `HOME`/`AW_HOME` and `XDG_CONFIG_HOME`/`AW_CONFIG_DIR` unset:
- Baseline reproduced. `aw install . --preset completely-clean-target -y --no-interactive` returns rc 0 and auto-commits 356 files into the target (161 `.aw/system`, 94 `.agents/skills`, 41 `.aw/records`, 27 `.claude/commands`, 27 `.opencode/commands`, plus `.gitignore`, `.gitleaksignore`, `.github/workflows`, `.aw/inbox`, `.aw/.gitignore`, and `AGENTS.md`). It also leaves 5 ignored paths. AW_HOME receives only `config/` and `state/durable`. `--preset local-only` behaves the same, and its stored `project.json` carries `delivery_mode: clean-delta`.
- End-state simulation. Starting from a real clean-target install, I moved `system` and `records` to `<aw_home>/projects/<id>/` and deleted `<repo>/.aw`. With no other change, `attention`, `check all`, `ipd board`, and `find` refuse with "not installed", and `index all` crashes. I then shimmed E-02's root recognition via `sitecustomize`. After that, `check all` and `attention` run, but `index prompts` still crashes (`prompts.prompts_root`), `backlog new --apply` writes `<repo>/.agents/backlog/...` and `<repo>/.aw/records/history.jsonl`, attention flags `.agents/skills` as uninventoried, and `aw status` reports not installed.
- Grep census (context, not a bar): `.aw/records` literals appear about 420 times in 41 modules, and `.aw/system` about 34 times in 12 modules.
- `resolve_project_context(preset="local-only")` with no stored config gives `delivery_mode: tracked` and an in-tree system. With the stored config it gives `clean-delta` and a home system. For `public-target-private-companion`, `system` stays in-tree.
- Spec `20260810-1447-01` sits under `specs/implemented/`. Its Section 4 heading is "Normative physical contract". Section 5 keeps per-machine control state in the target (`wmuu4k`). `CHANGELOG.md` has no `[Unreleased]` section.
- `python3 -m pytest -o addopts="" -q tests/test_clean_target_config_home.py tests/test_install_consent_truth.py`: 16 passed at base.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | G. Executability / C. Architecture; right-sizing | End-state simulation above; `prompts.prompts_root`; `backlog.BACKLOG_ROOTS`; spec `or061f` Section 11 "Phase 3"; backlog `kvwwt0` final sentence | The plan routes installer writes only. The readers and producers that every later verb uses stay hard-wired to the target, so the first ordinary use re-creates a target delta, or crashes. The real surface is dozens of modules, which matches deferred or061f Phase 3 (which needs Phase 1 first). The backlog itself names this as a maintainer decision. Nine E-items, several bundling 5 to 7 functions, are also too dense to execute as written. | C:High; U:Medium; S:Low; F:High; Overall:High | OPEN | Escalated as plan OQ-03 (`Blocking: yes`, `Finding: PR-001`). The options are to re-scope into a Set, un-park `m15n3k`, or relabel or refuse the preset and retire this plan. |
| PR-002 | HIGH | IN-SCOPE | D. Domain invariants (spec conflict) | spec `20260810-1447-01` Section 5 "Per-machine control state ... stays IN the target repository" (`wmuu4k`); E-05 "`git status --porcelain --ignored` is completely empty" | E-05 drops `.aw/.gitignore` and requires an empty `--ignored` status. That contradicts an implemented decision that keeps control state in the target behind `.aw/.gitignore`. Without that file, the first runner use leaves unignored `.aw/state/` and `.aw/worktrees/` behind. | C:Medium; U:Medium; S:Low; F:High; Overall:High | OPEN | Escalated as plan OQ-04 (`Blocking: yes`, `Finding: PR-002`). The recommended option is `.git/info/exclude` with a `--porcelain`-empty bar. |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness | Resolver probe: `preset="local-only"` without a stored config resolves to `tracked` | Deriving delivery mode from the preset name gives the wrong answer for `local-only`. Routing must read the stored policy. | all Low | FIXED | Added a Step 0 convention: always read the stored `project.json`. |
| PR-004 | MEDIUM | IN-SCOPE | A. Correctness | Proposed change 1 `project_system_dir` step 2 listing `PUBLIC_TARGET_PRIVATE_COMPANION`; spec Section 6 "target tracked" | The preset list would move a companion install's tracked `system` out of the target. | all Low | FIXED | Removed it from the list, and noted the preferred form: delegate to `resolve_project_context().physical_classes["system"]`. |
| PR-005 | MEDIUM | IN-SCOPE | G. Stale target | `CHANGELOG.md` has no `## [Unreleased]`/`### Fixed` | E-08, V-08, and the docs section named a section that does not exist. | all Low | FIXED | Retargeted to a `- Fixed:` bullet under `## 2.0.0 (pending)`. |
| PR-006 | MEDIUM | IN-SCOPE | G. Stale citation / spec sync | Spec path is `specs/implemented/...`; heading "## 4. Normative physical contract"; the p425hv AMENDED paragraph; Section 5 | The spec path and heading were wrong. The sync also omitted the Section 5 paragraph that this plan contradicts. | all Low | FIXED | Corrected the path in `- Scope-Paths:` and everywhere else. E-08 now names the AMENDED sentence and the Section 5 paragraph. |
| PR-007 | MEDIUM | IN-SCOPE | E. Verification (unsatisfiable bar) | E-09/V-09 "full suite passes with zero regressions" | The bar had no base-commit comparison and no fixture isolation rule (an inherited `AW_HOME`/`XDG_CONFIG_HOME` makes home-path assertions vacuous). | all Low | FIXED | Added a base-commit comparison to E-09 and V-09, plus a Step 0 fixture isolation rule that includes git identity so the auto-commit path is exercised. |
| PR-008 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the honesty rule, `aw ipd begin`, never-push, a scope fence, and runner-conditional finalize, and it told the executor to finalize unconditionally. | all Low | FIXED | Rewrote the gate, adding a DO-NOT-EXECUTE clause tied to OQ-03 and OQ-04. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the review re-scope the plan into a Set itself? | No; escalate to the maintainer as OQ-03 | Author child plans now (picks between Phase 3, a Set, or relabeling, which the backlog reserves for the maintainer) | backlog `kvwwt0` "Decision for the maintainer"; spec `or061f` gate on parked `m15n3k` | yes |
| D-2 | Should the review settle the control-state conflict? | No; escalate as OQ-04 | Pick `.git/info/exclude` (overrides nothing but changes the plan's acceptance bar); relocate control state (reopens `wmuu4k`) | spec `20260810-1447-01` Section 5; `wmuu4k` | yes |
| D-3 | How should the `system` path be resolved? | Delegate to `resolve_project_context` with the stored policy | The preset-name list (wrong for companion and for unstored `local-only`) | resolver probes | yes |
