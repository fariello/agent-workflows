# Review findings: plan gjylny

- Subject-Id: gjylny
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (BLOCKER, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane after `52ff6a678`. The plan was committed (`fa52d1582`) and byte-identical to the lane input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean`. This is a child plan, not an orchestrator.

Method. Each probe uses a scratch `AW_HOME`/`HOME`/`XDG_CONFIG_HOME` and a fresh `private-target` install with a committed initial state. The to-home flip is simulated: write a home `project.json` with `delivery_mode: clean-delta`, then delete the in-tree `project.json`, `local.json` and `.aw/config/`. The probe then calls `engine.uninstall_repo(repo, True, home_trees=None)` with `_clean_delta_home_trees` patched to return `None`. That is the most favourable reading of the plan's E-01, which forces `home_trees=None` and skips the auto-detect.

Observed after the simulated flip: `project_config_dir` -> home; `project_system_dir` -> home; `manifest.resolve_manifest_path` -> `<AW_HOME>/projects/r-2e1559/system/managed-sections.json` (absent); `setup_marker_path` -> home `state/runtime`; `_is_clean_delta_install` -> True.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A (data loss on the NEW side) | `agent_workflows/engine.py` `uninstall_repo` step 4 "home_cfg = project_config_dir(repo_root)"; probe actions "removed <AW_HOME>/projects/r-4ff147/config/project.json", ".../state/durable/install.json" | With `home_trees=None` and no in-tree `.aw/config`, step 4's `else:` branch resolves and deletes the freshly flipped HOME config and the whole home `state/`. That is the exact outcome the plan exists to prevent. The plan's mutation proof would not catch it, because the unmutated code also fails. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 (d) skips that branch under `side="target"`. Case (1) seeds home `config`, `state` and `records` and asserts a byte-identical home snapshot. Added F-05 and mutation M2. |
| PR-002 | BLOCKER | IN-SCOPE | A (user-content loss) | `manifest.resolve_manifest_path` "new_path = project_system_dir(root) / ..."; probe: first action "removed .aw/system/workflows/" (fallback sweep); an edited, committed `.opencode/commands/advise.md` was "removed" | After the flip the manifest resolves to the absent home path, so `has_manifest` is False. The pre-manifest fallback sweep then deletes every shim, including user-edited ones. This contradicts the plan's own case (2) and the Goal's "never touching user content". | Overall:Low | FIXED | E-01 (b) and (c) read the in-tree manifest and in-tree system paths explicitly. Case (2) exercises exactly this scenario. Added F-04. |
| PR-003 | HIGH | IN-SCOPE | A / G (wrong mechanism) | `engine.plan_uninstall` "if home_trees is None: home_trees = _clean_delta_home_trees(repo_root)"; `uninstall_repo` treats any non-`None` `home_trees` as clean-delta and indexes `home_trees["project_dir"]` | E-01's "pass `home_trees=None` to `plan_uninstall`" lets it re-auto-detect. The `{}` sentinel only fixes `_system_member_destination`, and passed anywhere else it would raise `KeyError`. `setup_marker_path` also routes home. | Overall:Low | FIXED | `side` is now a keyword on `plan_uninstall` too. The sentinel was removed, and the setup marker uses the explicit in-tree path (E-01 (a), (e)). Added F-06. |
| PR-004 | MEDIUM | UNDER-SCOPE | D (Concern not delivered) | Concern lists `.aw/inbox/README.md` and `.aw/workflow-artifacts/`; probe: a default `uninstall_repo` on a fresh install left `.aw/inbox/README.md`, still in `git ls-files` (it is not in the manifest: the non-system entries are only `.gitignore#aw:untracked`, `AGENTS.md#aw:pointer`, `AGENTS.md#aw:reporting`) | Nothing removed the tracked inbox README, so a `completely-clean-target` repo would keep a tracked AW file. | Overall:Low | FIXED | E-02 removes it only when its bytes equal the `collect_scaffold_members(category="inbox")` template. Empty `.aw/inbox/` and `.aw/workflow-artifacts/` directories are pruned, and anything inside them is preserved. Added case (4b). |
| PR-005 | MEDIUM | IN-SCOPE | E (fixture and suite selection) | E-03 "per-test `copytree`" (see `xvlemm` review PR-004); `ls tests \| grep uninstall` lists only `test_uninstall_layout_artifacts.py`, while `grep -l uninstall_repo tests/*.py` also finds `test_installer.py` | The copy fixture collides on project ids, and the regression-suite selector missed `test_installer.py`. | Overall:Low | FIXED | Tests now use a fresh install per test with git env and an initial commit. The selector is now `grep -l uninstall_repo`. |
| PR-006 | LOW | IN-SCOPE | G (traceability) | V-01/V-03/V-04 | The V-items did not demand evidence for the new bypasses or the second mutation. | Overall:Low | FIXED | V-01 now names bypasses (a) to (e). V-03 names the home snapshot and the PRESERVED action. V-04 names M1 and M2. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should `uninstall_repo` still be reused, given that five resolvers route home? | Yes, behind an explicit `side="target"` that bypasses each of them. | A dedicated sweep (REJECTED, as in OQ-01: it duplicates the drift and manifest rules). Run retirement BEFORE the flip (REJECTED: Order 04 and spec 8.1 put retirement after the authority switch). | `engine.uninstall_repo` source; review probes. | yes |
| D-2 | What should happen to `.aw/inbox/README.md`? | Remove it only if it is byte-identical to the shipped template; otherwise preserve it. | Always remove it (REJECTED: the user may have edited it). Leave it (REJECTED: the target would keep a tracked AW file). | `engine.ensure_inbox_readme` "no-clobber (a user's own README is never overwritten)". | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
