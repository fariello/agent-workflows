# Review findings: plan on0keo

- Subject-Id: on0keo
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at `461fdf679`. The plan was committed and unchanged (`9f3a8122a`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize` clean after revisions.

Re-verified at review HEAD (scratch repos under a temp dir, `AW_HOME`/`XDG_CONFIG_HOME` inside it):
- F-01/F-02/F-03 reproduced: after a hand edit, `persist_project_policy` dropped `run`, `setids`, `release_gate_work_kinds`; `cutovers.spec_id6` `2020-01-01 -> 2026-10-15`; `local.json` lost `run_analytics_sharing`, `runtime_overrides`, `local_aliases`; `ProjectPolicySchema(cutovers={}, setids={}).to_dict()` drops both keys.
- F-04 reproduced: `resolve_existing_policy` -> `('private-target', 'target', ['opencode', 'claude', 'antigravity'], {})` despite stored `role`, `enabled_hosts: ["opencode"]`, `non_secret_consent`.
- F-05 reproduced end to end: subprocess `python3 -m agent_workflows install <repo> -y --no-interactive` on a `local-only` repo -> exit 0, stored `preset: private-target`, `run: None`, `spec_id6: 2026-10-15`.
- `SchemaValidationError`, `FORBIDDEN_PORTABLE_KEYS`, `_check_no_path_leaks`, `cli._cmd_install`, `ProjectContext.companion_repo`, `## [Unreleased]` do not exist; `parse_portable_policy` accepts a partial `{cutovers, run}` document; `role: "companion"` raises `ValueError: Unknown project role`.
- Alias switch: `explicit_preset="clean-target"` stored `preset: clean-target` / `tracked` / `repository`, which `parse_portable_policy` then rejects.
- Cross-placement switch: persisting a coherent `local-only` policy on a `private-target` repo wrote `<AW_HOME>/projects/<id>/config/project.json` and left the in-tree `private-target` file, which `project_config_dir` still resolves.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A. Data integrity | `agent_workflows/project_context.py:755` `project_config_dir`; `install_wizard.persist_project_policy` `proj_json = Path(ctx.physical_classes["config_project"])` | The plan's preset-default refresh on reinstall would make `--preset local-only` on a `private-target` repo write config under `AW_HOME` while the stale in-tree `project.json` stays authoritative (silent split brain, probe-confirmed). The plan also asserted the switch "updates to local-only while preserving custom policy keys", which the design cannot deliver. | C:Low; U:Low; S:Low; F:Low; Overall:Low (for the guard) | FIXED | E-09 refuses a cross-placement switch with `InvalidPolicyError` (exit 1, nothing written); same-placement switches proceed. Real relocation is a migration with tracked-file deletion (Medium-High) and is deferred to new backlog `ui1aln` (`Blocks-Release: next`, carrier in Deferred). Tests and V-06/V-09 assert the refusal. |
| PR-002 | HIGH | IN-SCOPE | G. Evidence | `agent_workflows/project_schema.py:589` `parse_portable_policy`; `grep` finds no `SchemaValidationError`/`FORBIDDEN_PORTABLE_KEYS`/`_check_no_path_leaks` | E-03 and OQ-01 were built on a nonexistent exception and nonexistent filters, so the fallback could not be implemented as written, and the partial-document case it targeted is already handled by the normal parse. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now parses normally and falls back to the raw dict on `ValueError` (unknown preset/role, schema_version > 2). OQ-01 resolution was corrected and cites the review probe (F-07). |
| PR-003 | MEDIUM | IN-SCOPE | G. Evidence | `agent_workflows/cli.py:8240` `_run_install`, `:8302`; `agent_workflows/project_schema.py:792` `ProjectContext` | `cli._cmd_install` does not exist (the function is `_run_install`), and `ProjectContext` has no `companion_repo` field. E-05 told the executor to read it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All references renamed. `companion_dir` is now read from the existing `local.json`. F-04 and F-05 corrected. |
| PR-004 | MEDIUM | IN-SCOPE | D. Invariants | `agent_workflows/project_schema.py:174` `ProjectRole`; probe `ValueError: Unknown project role: 'companion'` | Tests and V-05 used `role = "companion"`, which `parse_portable_policy` rejects, so the planned test fixture would fail for an unrelated reason. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Changed to `source-checkout`, the only non-default role. |
| PR-005 | MEDIUM | IN-SCOPE | A. Correctness | `install_wizard.resolve_policy_noninteractive` existing-policy branch | Alias presets are stored un-normalized, and the stored file is then unparseable (F-06). The plan noted normalization but not that `persist_project_policy` must survive a file already holding such a value. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-06. E-09 normalizes. E-03's raw-dict fallback keeps keys from an already-unparseable file, and E-08 tests that case. |
| PR-006 | MEDIUM | IN-SCOPE | G. Right-sizing | plan E-05 | E-05 bundled a pure resolver change in `project_context.py` with two `install_wizard` functions, covering separate test surfaces. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-05 (hosts precedence, V-05) and new E-09 (wizard round-trip, normalization, guard, V-09). Dependencies and `Highest E allocated: 09` updated. |
| PR-007 | MEDIUM | IN-SCOPE | E. Testing | plan E-08, V-08 | There was one mutation proof covering both writers. Test isolation from the real home was not stated. The subprocess invocation used `agent_workflows.cli` (the repository convention is `-m agent_workflows`) with no child env. Adjacent suites were not named. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Two mutation proofs, each with a diff after restoration. Scratch `AW_HOME`/`XDG_CONFIG_HOME` required. Child env specified. Adjacent suites listed. Counts are re-derived at execution. The slow marker is decided by measurement. |
| PR-008 | LOW | IN-SCOPE | Documentation | `CHANGELOG.md` `## 2.0.0 (pending)` section | E-07 targeted a `## [Unreleased]` heading and `### Fixed` subsection that do not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now adds one flat `- Fixed:` bullet to the pending section (F-09). |
| PR-009 | LOW | IN-SCOPE | G. Evidence | spec `20260810-1447-01` `## 7. Configuration and precedence` | Spec sync cited "Section 9.1" at an unarchived path. The section is 7 and the spec lives under `implemented/`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected the path and section, with the quoted "remain preserved" text. |
| PR-010 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the honesty rule, never-push, a scope-fence declaration, OQ status and the scratch-home rule, and told the executor to finalize unconditionally. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten. The runner owns finalize; the executor finalizes only when executing by hand. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `persist_project_policy` handle a `project.json` that `parse_portable_policy` rejects? | Raw-dict fallback preserving every non-schema key | Refuse the install (new failure mode on a previously working path); overwrite (the bug) | spec `20260810-1447-01` Section 7 "unknown fields ... remain preserved"; probe F-06 | yes |
| D-2 | Where does `resolve_existing_policy` get `companion_dir`? | Existing `local.json` `companion_dir` | Add a field to `ProjectContext` (wider surface, not needed) | `agent_workflows/project_context.py:1256` already reads `merged_local_binding.get("companion_dir")` | yes |
| D-3 | What happens on a reinstall preset switch that changes config placement? | Refuse with `InvalidPolicyError`; defer relocation to `ui1aln` | Implement relocation here (migration plus deletion of tracked files: Medium-High risk, out of the backlog's scope); keep today's incoherent policy; write the new location and leave a split brain | probe: two `project.json` files, `project_config_dir` prefers the in-tree one | yes |
| D-4 | Which role value should the tests use as non-default? | `source-checkout` | `companion` (rejected by schema) | `agent_workflows/project_schema.py:174` `ProjectRole` | yes |
| D-5 | Is a spec amendment needed? | No | Amend spec Section 7 | Section 7 already requires preservation; the guard is wizard behavior | yes |
