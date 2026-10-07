# Review findings: plan xzlu9b

- Subject-Id: xzlu9b
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `01ad8b2ae` in an isolated review-sweep lane. Child plan (own first `- Kind:` bullet reads
`child`). Plan committed and byte-identical to the lane input, so no pre-review snapshot. `aw ipd lint --phase author
--agent` clean (advisory `IPD-Z602` only) before semantic review; `aw ipd lint --phase review-finalize --agent` clean
(advisory `IPD-Z602` only) after revisions; `check_engine.check_durable_carrier` returns nothing for this plan.

Demonstrations (scratch repos under the temp dir, `AW_NO_REEXEC=1`, temp `HOME` for the real install):
- Ignore pair `/inbox/*` + `!/inbox/README.md`: `git check-ignore -q` rc `1 .aw/inbox/README.md`,
  `0 .aw/inbox/drop.md`, `0 .aw/inbox/sub/README.md`, `1 .aw/records/comms/shared/inbox/.gitkeep`; `git add
  .aw/inbox/README.md` rc 0; `git status --ignored` lists `!! .aw/inbox/drop.md`, `!! .aw/inbox/sub/`.
- Old rule `/inbox/`: `git add .aw/inbox/README.md` prints "The following paths are ignored by one of your
  .gitignore files: .aw/inbox".
- This repository: `git ls-files .aw/inbox` -> `.aw/inbox/README.md`; `git check-ignore -v --no-index` ->
  `.aw/.gitignore:28:/inbox/`.
- Fresh `aw install --preset private-target -y --no-interactive`: `ls -la .aw/inbox` -> "No such file or directory".

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Honest documentation / prior decision | `.aw/inbox/README.md` "Why this directory is gitignored": "Force-adding this single file is preferred over narrowing the ignore pattern"; `lznpv6` E-06 | The README this plan copies into every target documents the opposite design and instructs `git add -f`; shipping it verbatim would contradict the new ignore rule. The plan also did not engage the recorded reason for the old choice. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 rewrites that section; OQ-01 and F-05 explain why the old objection (aimed at `/inbox/*.md`) does not apply to `/inbox/*`; V-02 greps for the stale text. |
| PR-002 | HIGH | IN-SCOPE | A. Correctness (ordering) | `engine.install_into_repo` runs `ensure_*_readmes` before `create_setup_artifacts`; `engine.git_add_optional` returns False on "ignored by" | On an upgrade the old `/inbox/` rule is live when the ensurer runs, so the README would be written but silently not staged, failing the plan's own goal for every existing install. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 runs `_ensure_aw_gitignore` before the ensurer and reports an unstaged README as skipped; E-05(b) asserts staging on upgrade with a mutation proof; V-03 pastes `git diff --cached`. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing (satisfiability) | `attention.inbox_waiting` single call site: the human board footer | E-05(c) asserted an inbox count in `aw attention --format json`, which carries none, so the test was unwritable as specified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05(c) asserts on the human footer line; (d) added for nested-subdir containment. |
| PR-004 | MEDIUM | IN-SCOPE | C. Reuse canonical mechanism | `engine.collect_scaffold_members` categories; `engine.run` `--diff` preview uses `category=None` | A bespoke writer would miss the `--diff` preview and the aw-vs-legacy layout gating the scaffold map already provides; "both install paths" was inaccurate (one chokepoint, `install_into_repo`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 adds an `inbox` scaffold category (aw layout only) and one ensurer in `install_into_repo`. |
| PR-005 | LOW | UNDER-SCOPE | G. Executability | "post-install next-steps text" unnamed; printed by `cli._install_one`; `cli.py` absent from Scope-Paths | The pointer edit had no named site and touched an undeclared file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 names the block; `agent_workflows/cli.py` added to Scope-Paths. |
| PR-006 | HIGH | UNDER-SCOPE | Project rule (Every live bug gates the next release) | `AGENTS.md` live-bug rule; `- Work-Kind: bug` without `Blocks-Release`; `i99ykd` review PR-002 | Live bug plan did not gate release `next`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Blocks-Release: next`. |
| PR-007 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Gate lacked resolved-OQ statement, honesty rule, scope fence as declaration, temp HOME, a guard against touching others' inbox drops in this repo, and conditional finalize ownership (it said `aw ipd set executed` unconditionally). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Ratify reversing `lznpv6`'s force-add choice in favour of `/inbox/*` + `!/inbox/README.md`? | Ratify | Keep force-add and have the installer `git add -f` the README | F-04 demonstration keeps new drops ignored by default; `lznpv6` E-06 explicitly left "force-add or narrowed ignore" open; a force-add in the installer would also force-add on targets whose users never asked | yes |
| D-2 | Should `aw uninstall --deep` remove `.aw/inbox`? | No; recorded as `Carrier-Declined` | Add `.aw/inbox` to `_DEEP_CLEANUP_ROOTS` | The directory may hold a user's unadopted raw drops; deleting user material is out of this defect's scope | yes |
