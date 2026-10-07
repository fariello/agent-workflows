# Review findings: plan gzsfqn

- Subject-Id: gzsfqn
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `dcffc9691` in an isolated review-sweep lane. Child plan (own first `- Kind:` bullet reads
`child`), depends on `executed:pfub72` (reviewed, not yet executed; the runner enforces the edge). Plan committed and
byte-identical to the lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent` clean before semantic
review and after revisions; `check_engine.check_durable_carrier` returns nothing for this plan.

Demonstrations (temp dirs, `AW_NO_REEXEC=1`, temp `HOME`, git identity in env):
- Fresh `aw install . --preset private-target -y --no-interactive` into a committed package.json-only repo: `git status
  --short` -> `?? .aw/config/`; `git ls-files .aw/config` empty; `git check-ignore -v .aw/workflow-artifacts/README.md`
  -> `.aw/.gitignore:75:/workflow-artifacts/`; log "Gitignore (run scratch): ... is NOT ignored", "Git: staging changes
  (no commit)", "Changes are STAGED but NOT committed", then "Changes committed successfully." (F-04).
- Same without `-y`: "aborted; nothing changed.", empty index and status (F-05).
- Upgrade over a committed install with `project.json` committed by hand: status empty, run-scratch line correct, STAGED
  line still printed (F-06).
- Log lists `[added    ] .aw/workflow-artifacts/README.md` though it is ignored and untracked (F-08).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G. Executability / C. Architecture | `cli._run_install` calls `persist_project_policy(...)` before `_install_one(...)`; `_install_one` shared by `cli._install_all` and `aw setup` | E-02 did not say where staging happens; the writer is outside `install_into_repo`, so a fix in `_run_install` alone would miss the shared core or double-stage. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 puts one helper in `engine.install_into_repo` after `sync_cutovers_on_install`, gated on stored git policy, ignore check and porcelain change; `persist_project_policy` returns the written paths. |
| PR-002 | HIGH | IN-SCOPE | E. Testing (reachability) | F-05; `cli._confirm_install` returns False when non-interactive without `-y` | E-05(c)'s "non-interactive run that declines the commit" is unreachable: the CLI aborts before writing; no `--no-commit` on `aw install`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05(e) drives `engine.prompt_and_run_commit` directly with `yes=False` on a staged temp repo. |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness | F-06; `engine.print_summary` "Git: staging changes (no commit)" and STAGED block gated on `installed or pruned` | E-04 left two false lines: the "Git:" header and the STAGED line on a no-change upgrade (manifest `[overwrite]` every run). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 neutralizes the header, moves the closing line into `prompt_and_run_commit` after its porcelain filter; E-05(d), V-04 cover the upgrade. |
| PR-004 | MEDIUM | UNDER-SCOPE | D. Anti-regression | `config.sync_cutovers_on_install` writes `project.json` when cutovers are missing; called in `persist_project_policy` and `install_into_repo` | Upgrades can modify a tracked `project.json`; the plan only tested fresh installs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 covers modified as well as new; V-02 adds an upgrade with `cutovers` removed. |
| PR-005 | LOW | IN-SCOPE | G. Executability | `engine.install_into_repo` is the one core for `engine.run` and `cli._install_one` | E-03 said "both the single-repo and batch install paths", implying two call sites; there is one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 names the one function and the sibling statuses to check. |
| PR-006 | LOW | IN-SCOPE | Honest documentation | F-05 | OQ-01's rationale assumed a non-interactive decline path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Resolution text corrected; answer unchanged. |
| PR-007 | HIGH | UNDER-SCOPE | Project rule (Every live bug gates the next release) | `AGENTS.md` live-bug rule; `- Work-Kind: bug` without `Blocks-Release`; `i99ykd` review PR-002 | Live bug plan did not gate release `next`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Blocks-Release: next`. |
| PR-008 | LOW | IN-SCOPE | G. Execution contract | gate "move the plan to `executed/` with `aw ipd set executed gzsfqn`" | Gate lacked resolved-OQ statement, honesty rule, scope fence as declaration, temp HOME, and conditional finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten to the Set's contract shape. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where to stage the wizard's writes? | Inside `engine.install_into_repo` via one helper | In `cli._run_install` after `persist_project_policy`; in `prompt_and_run_commit` | F-07: the core is shared by every entry point; cutover sync rewrites `project.json` inside the core too | yes |
| D-2 | Where does the single closing line live? | `engine.prompt_and_run_commit` | Keep it in `print_summary` with a pre-computed outcome | Only `prompt_and_run_commit` knows whether a commit happened and owns the porcelain filter | yes |
| D-3 | Fix the `[added]` tag on the ignored run-scratch README here? | No, record only | Fold into E-04 | Not part of D03/N1; status and commit are already correct for it | yes |
