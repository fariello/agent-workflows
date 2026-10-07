# Review findings: plan pfub72

- Subject-Id: pfub72
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `2493daf03` in an isolated review-sweep lane. Child plan, depends on `executed:gi1w75`
(reviewed, not yet executed; the runner enforces the edge). Plan committed and byte-identical to the lane input, so no
pre-review snapshot. `aw ipd lint --phase author --agent` clean before semantic review; `--phase review-finalize`
clean after revisions; `check.plan-spec-link-missing` fired on the unrevised plan and is clear after `- From-Spec:`.

Verified:
- `install_history.record_install_history` writes `ctx.logical_roots[LogicalRoot.STATE.value] / "install.json"`;
  `install_wizard.persist_project_policy` step 3 `"installed_version": "2026.8.10"` and `policy.to_dict()` (F-02/F-03).
- `ctx.physical_classes["state_durable"]` resolves to `.aw/state/durable` in a `private-target` scratch target.
- Scratch install with temp HOME `pfhome-zzuniq`: four state files; snapshot `aw_home: null`; after reinstall
  `aw_home` = temp HOME config path and the durable history contains the HOME path; 2 lines in each history (F-05).
- `.aw/state/` reported `!!` (ignored); `check-local-leaks . --agent` clean regardless (F-06).
- `project_layout.install_system_tree` is a third writer; callers only in `tests/test_installer.py` (F-07).
- `tests/test_config.py` cutover fallback tests seed the root history path; `config._find_install_history_cutover`
  reads root first and breaks on the first non-empty file.
- Spec `kw5y2s` Section 3.3 lists `install/`; `layout.DURABLE_STATE_CLASSES` records the live `install.json`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E Testing / B | `agent_workflows/leak_sanitizer.py` scans tracked content; `engine._AW_GITIGNORE_TEMPLATE` `/state/`; F-06 | E-01, V-02 used `check-local-leaks .aw/state` as the leak oracle; it treats the arg as a repo root and scans tracked files only, so it reports clean on gitignored state even when the HOME path is present. V-02 could pass with the leak intact. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Oracle replaced with direct search for a distinctive temp HOME name, and absent `aw_home`/`companion_dir` keys. |
| PR-002 | HIGH | IN-SCOPE | B Security / A | `install_history._redact_details` iterates `details.items()` top-level strings only; `install_wizard.resolve_existing_policy` `aw_home=str(ctx.effective_aw_home)` | E-02 proposed redacting the nested policy "through the existing `_redact_details` logic", which does not walk nested dicts; the leak only appears on REINSTALL, which neither E-01 nor E-05 exercised. | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | FIXED | Policy summary built from `ProjectPolicySchema` portable fields (excludes paths by construction); E-01/V-02/E-05 (a) run a second install. |
| PR-003 | MEDIUM | IN-SCOPE | A / G | `config._find_install_history_cutover` root-first `break`; `tests/test_config.py:1000` root fixture; `engine.install_into_repo` `migrated` list | E-04's placement ("beside") and ordering relative to the history append, its reporting channel, dry-run behavior, and append order were unstated; reader-reorder could affect existing tests not in Scope-Paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 names `install_into_repo`, before the append, `migrated` reporting, silent no-op, dry-run, append order; `tests/test_config.py` added to Scope-Paths; V-04 adds dry-run and diff. |
| PR-004 | LOW | IN-SCOPE | D | `project_layout.install_system_tree` writes literal `"installed_at": "2026-08-10T00:00:00Z"` and `str(system_root)` | A third writer of the same files was unmentioned. Off the install path (test-only callers). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded in E-03 note, F-07 and Scope check; reported to the maintainer. |
| PR-005 | LOW | IN-SCOPE | G Evidence | V-03 `grep ... returning nothing` | V-03 demanded a source grep as the only proof that the wizard stopped writing; behavior evidence (one history line per install) is the real proof (P16 applies to tests; the evidence should still be behavioral). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 demands the diff, the call-site listing, and the 1-then-2 line counts. |
| PR-006 | LOW | IN-SCOPE | Spec sync | spec `kw5y2s` 3.3 `install/: Installation receipts`; `layout.DURABLE_STATE_CLASSES` "`install` is a FILE"; `check.plan-spec-link-missing` | The spec says `install/` while the plan writes `install.json`; unacknowledged. The plan cites the spec without `From-Spec`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Convention and spec-sync note the documented divergence; `- From-Spec: kw5y2s` added. |
| PR-007 | HIGH | UNDER-SCOPE | Project rule | AGENTS.md live-bug rule; `- Work-Kind: bug` | Live bug plan lacked `Blocks-Release`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Blocks-Release: next`. |
| PR-008 | MEDIUM | UNDER-SCOPE | G contract | gate "move the plan to `executed/` with `aw ipd set executed pfub72`" | Gate lacked resolved-OQ statement, honesty rule, scope fence as declaration, temp HOME, conditional finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten to the Set's standard contract with `aw ipd finalize`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to keep paths out of the snapshot policy? | Whitelist `ProjectPolicySchema` portable fields | Deep-walk redaction via the sanitizer | `_redact_details` is top-level only; whitelist cannot leak a new path field | yes |
| D-2 | Fix `project_layout.install_system_tree` here too? | No; reported | Route it through `record_install_history` | no non-test caller (`grep`), different subsystem | yes |
| D-3 | Follow spec `install/` or live `install.json`? | `install.json` | Rename to `install/` | `layout.DURABLE_STATE_CLASSES` comment and tests (`tests/test_layout.py:292`) pin the file | yes |
