# Review findings: plan xvlemm

- Subject-Id: xvlemm
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane after `3cd592d76`. The plan was committed (`fa52d1582`) and byte-identical to the lane input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean`. This is a child plan, not an orchestrator.

Verified (scratch `AW_HOME`/`HOME`/`XDG_CONFIG_HOME` under `/tmp/opencode`, `AW_NO_REEXEC=1`):
- `layout_migration.MigrationManager` matches F-01: "self.config_dir = self.aw_dir / \"config\"" and "cfg_data[\"records_backend\"] = target_backend" into `config.json`.
- Physical classes for a `private-target` repo are all under `<repo>/.aw/`. For `local-only` they are all under `<AW_HOME>/projects/<id>/`. `worktree_lease.worktrees_root` returns `<repo>/.aw/worktrees` and `<AW_HOME>/projects/<id>/worktrees` respectively.
- A `private-target` `local.json` stores `"project_id": "r-2598b2"`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A (cross-plan detection) | `ppu39q` E-02 (revised: `label` branch only with `existing_policy`); review probe: the companion writer resolves to `<repo>/.aw/config/project.json`, the same as the reader | Calling the detector without `existing_policy` returns `None` for a companion pair, so `companion-unsupported` would never fire and the planner would report `not-a-placement-switch`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now passes `resolve_existing_policy(repo)` and short-circuits companion pairs to `companion-unsupported` with no items. E-02, E-03 and V-02 were updated to match. |
| PR-002 | HIGH | IN-SCOPE | A (purity) / E | Review probe: after `touch AGENTS.md`, `git status --porcelain` changed the `.git/index` mtime; with `GIT_OPTIONAL_LOCKS=0` it did not | The "read-only" planner's `git status` can rewrite `.git/index`. The purity snapshot also skipped `.git/`, so it would not catch this. | Overall:Low | FIXED | Every git subprocess now runs with `GIT_OPTIONAL_LOCKS=0` and `core.fsmonitor=false`. The purity test touches a tracked file first and snapshots `.git/`. V-01 checks the index mtime. Added F-05. |
| PR-003 | HIGH | UNDER-SCOPE | A (split brain recurrence) | `project_context.resolve_project_context` "if isinstance(local_pid, str) and local_pid.strip():"; `project_config_dir` derives the id from the path only; review probe: a `cp -a` copy `rc` has derived id `rc-af4372` but its writer resolves to `r-2598b2` | For a moved or copied checkout, a to-home switch would write config to a home dir that `project_config_dir` never reads after the flip. That recreates the `ui1aln` bug. | Overall:Low | FIXED | Added the `project-id-mismatch` blocker (with a mirror check for to-target) and a test fixture for it. The `config_local` rewrite sets the destination id. Added F-06. |
| PR-004 | MEDIUM | IN-SCOPE | E (test fixture validity) | E-03 "copy the tree per test with `shutil.copytree` ... a copy gets its own home dir"; review probe: a copied `local-only` repo returned `resolve_existing_policy` `None` | The planned copy fixture is wrong in both directions. A copied private-target repo collides on the original's home id, and a copied local-only repo has no config at all. | Overall:Low | FIXED | Tests now install a fresh repo per test (about 3 s each, measured). They need git identity env vars and an initial commit, otherwise the 357 installed files stay staged `A` and trip `dirty-aw-tree`. |
| PR-005 | MEDIUM | IN-SCOPE | A (malformed input) | Review probe: with `[1,2` in `project.json`, both `resolve_project_context` and `resolve_existing_policy` returned `private-target` without error | The `unparseable-config` blocker cannot rely on the resolvers, because they silently tolerate the malformed file. | Overall:Low | FIXED | E-02 now has the planner `json.load` each present old config file itself. |
| PR-006 | MEDIUM | IN-SCOPE | G (internal contradiction / cross-plan) | E-01 records clause "EXCLUDING the paths `.aw/.gitignore` already ignores ... keep moving because they are user data"; OQ-01 "so that offer includes them" vs `ozr356` E-03 "do NOT add the switch's staged records to its `files_to_commit`" | The records clause both excluded and included ignored paths. OQ-01 contradicted Order 05. | Overall:Low | FIXED | The rule is now: every records file moves (ignored ones with `tracked=False`) except the generated `INDEX.*` files, which are discarded. OQ-01 was amended to match ozr356. |
| PR-007 | LOW | IN-SCOPE | G | E-03 "`setUpClass`" plus "per test" | After PR-004, the setup wording was inconsistent. | Overall:Low | FIXED | Now uses `setUp`, one repo per test. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What should happen when the stored `project_id` disagrees with the path-derived id? | Block the switch (`project-id-mismatch`). | Write to the derived id (REJECTED: silently orphans the home records the stored id points at). Write to the stored id (REJECTED: `project_config_dir` never reads it, which is the split brain). | `project_context.project_config_dir` "project_id = _derive_project_id(anchor_abs)"; review probe. | yes |
| D-2 | Should git-ignored records move? | Yes, except the generated INDEX files. | Exclude them (REJECTED: `runs/`, `history.jsonl` and `untracked/` are user data that retirement would delete). | `.aw/.gitignore` comments ("box-local", "GENERATED byte-deterministically"). | yes |
| D-3 | Should moved records go into the commit offer? | No; they stay staged and uncommitted. | Include them (REJECTED: contradicts `ozr356` E-03 and spec 11.2 "without committing"). | `ozr356` E-03. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
