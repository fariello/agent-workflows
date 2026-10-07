# Review findings: plan i6mby8

- Subject-Id: i6mby8
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `527c93f2e`. The plan was committed and byte-identical to the sealed lane input, so no
pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before revision and
`--phase review-finalize --agent` was clean after it.

Re-verified by reading the code (no production edit):
- `project_context.no_project_message` contains the `lmyeas` inside-project branch ("IS an agent-workflows project root ... Run with: aw <verb> --dir <root>"). Its git tail is gated on `git_root is not None and not is_project_dir(git_root)`.
- `project_context.classify_project_dir`, `ProjectClassification` and `git_root_for_message` exist as described. `_find_git_root` walks for `.git` without a subprocess.
- `attention.run` and `cli._run_plans` hand-roll the same block. Each carries THREE summary strings and builds `NextAction(command="aw install .", description="install agent-workflows in this repo")` gated on `git_root_for_message`, and emits `cannot-run` at `exit_code=2`. The human path returns `EXIT_CANNOT_RUN`.
- Sibling `jei45f` resolves that the validators refuse in the bare-cwd case as well as for explicit `--dir`. All three siblings refer to the primitive only as "Order 01's primitive".
- `~/.aw` exists on this machine, so `$HOME` can be an AW project root.
- Every plan in the Set carries `From-Backlog: rgl2d4`. `rgl2d4` is `open` with `Blocks-Release: next`, and this plan inherits the gate.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | D. Anti-regression / contract | `attention.run` and `cli._run_plans` summary branch: "no AW project found at the working directory or any ancestor; cd into the repository or pass --dir <repo>"; `jei45f` OQ "refuse in BOTH cases" | The plan specified the primitive and its tests over explicit-`--dir` cases only, and said "F-02 quotes both" phrasings. The shipped sites have a THIRD summary for the non-explicit (bare-cwd) case, which sibling `jei45f` relies on. A primitive built to the plan as written would lack it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 lists all three strings verbatim. E-03, Required tests and V-01 now cover the non-explicit variants of (c) and (d), and assert summary EQUALITY per case. |
| PR-002 | MEDIUM | IN-SCOPE | C. Single definition | both sites build `NextAction(command="aw install .", description="install agent-workflows in this repo")` | The primitive returned only the next-action COMMAND, so every call site would re-author the description string. That is the duplication this plan exists to remove. | all Low | FIXED | E-01 now returns the command and the description as plain strings. E-03 and V-01 assert the description. |
| PR-003 | MEDIUM | UNDER-SCOPE | G. Cross-plan interface | `jei45f` E-01 "Call Order 01's primitive"; the same wording in `sjsb04` and `rlhmt9` | The primitive's name and return type are unspecified, and the three dependent plans have no place to discover them. | all Low | FIXED | E-01 and V-01 now require the executor to record the symbol name and return type in V-01's evidence. |
| PR-004 | LOW | UNDER-SCOPE | E. Fixture validity | `~/.aw` exists; `tempfile.gettempdir()` is `/tmp` here but is configurable | A `tempfile` fixture under an AW-project `$HOME` would classify as inside-a-project and silently invalidate cases (c) and (d). This is the same trap class the plan's F-10 records. | all Low | FIXED | E-03 now first asserts `find_project_root(<fixture>) is None` for the no-project fixtures. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does the primitive own the bare-cwd (non-explicit) summary? | Yes, all three shipped strings | Explicit-only, leaving bare-cwd to each verb | shipped strings in `attention.run`/`cli._run_plans`; `jei45f` OQ | yes |
| D-2 | Should the plan fix the primitive's name now? | No; the executor names it and records the name in V-01 | Mandate a name in the plan | The plan deliberately leaves the shape to the executor; the siblings reference it only abstractly | yes |
