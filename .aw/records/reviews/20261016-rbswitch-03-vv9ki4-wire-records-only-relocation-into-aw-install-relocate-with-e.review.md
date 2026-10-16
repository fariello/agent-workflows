# Review findings: plan vv9ki4

- Subject-Id: vv9ki4
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane after commit `8e7c149a8`. The plan was committed and unchanged, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent`: `clean`. Child plan. Dependencies `fxbm7j` (reviewed this sweep) and `ozr356` (approved, pending) are not executed, so `--relocate`, `placement_switch.py` and `RecordsRootSwitchRequired` are absent at HEAD; E-01's stop condition covers it.

Verified:
- `CHANGELOG.md` has "## 2.0.0 (pending)"; `README.md` has "### Placement Presets and Storage Backends" (the "Changing presets later" paragraph is added by `ozr356`, as the plan states).
- `ozr356` E-03 already states the to-target commit-offer rule this plan mirrors.
- `engine.install_into_repo` calls `engine.stage_tracked_policy_files`, which stages `.aw/config/project.json` when its `config_project` git policy is `target-git` and appends it to `installed`; `engine.prompt_and_run_commit` commits `installed` paths with `git commit -- <paths>` under `plan.yes`.
- Review probe (scratch `AW_HOME`, `AW_NO_REEXEC=1`): after the backlog-bug reinstall `install <repo> --records-backend home -y --no-interactive`, HEAD was `agent-workflows: sync via installer` with the single change `.aw/config/project.json` (`records_backend` `repository` -> `home`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric E (unsatisfiable assertion) / F (honest messaging) | E-05 case (3) "`git diff --cached --name-status` shows `D` for the record and `M` for `project.json`"; E-02 summary "left staged with the updated project.json"; `agent_workflows/engine.py:2697` `stage_tracked_policy_files`; `engine.prompt_and_run_commit` "cmd = [\"git\", \"commit\", ... \"--\"] + paths_list"; review probe commit touching only `project.json` | Under `-y` the install that follows the switch stages and commits `project.json` path-scoped, so case (3) would observe no staged `M` and fail, and the success message would tell the user `project.json` is staged when it has already been committed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 documents the behavior with evidence and accepts it (today's behavior for any policy change); E-02 message drops the `project.json` staging claim; E-05 (3) asserts no staged `project.json`, and that every new commit is the installer's and names no `.aw/records/` path; E-03 expected outcome and V-03 updated; F-05 added. |
| PR-002 | MEDIUM | IN-SCOPE | Cross-plan consistency | E-01 "Update the Order 01 assertions ... that pin `backlog wbz75c`"; `s07f73` E-05 test (3) "output contains `would leave 1 record files`" | The new message drops `would leave ... record files` too, so a guard test pinning it would fail after E-01, and the instruction named only the `wbz75c` substring. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now names both substrings and their replacements (`--relocate`, `moves 1 record files`). |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the post-switch install be prevented from committing `project.json`? | No; accept today's path-scoped commit and make the tests and message match it. | Exclude `project.json` from the installer commit after a switch (REJECTED: needs an `engine.py` change outside Scope-Paths, diverges from every other policy update, and E-03 already forbids patching `engine.py`). | `engine.stage_tracked_policy_files`; review probe. | yes |
