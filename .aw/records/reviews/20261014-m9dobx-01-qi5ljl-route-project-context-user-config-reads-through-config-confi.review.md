# Review findings: plan qi5ljl

- Subject-Id: qi5ljl
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`2c4045e9e`), so no snapshot was needed. `aw ipd lint --phase author` reported conforming. `--phase pre-transition` reported only the expected not-yet-executed `IPD-S404`; the deferred rows already carry carriers.

Claims verified at HEAD:
- Both hard-coded sites exist: `_resolve_effective_aw_home` and `resolve_project_context` under `# Read configuration layers`.
- `config.config_dir()` honors `AW_CONFIG_DIR` > `XDG_CONFIG_HOME` > `~/.config`.
- `leak_sanitizer._config_dir` is the lazy fail-open pattern, and `_is_repos_schema_mapping` already lazily imports `agent_workflows.config`.
- `project_config_dir` calls `_resolve_effective_aw_home(aw_home=aw_home)` without `user_config_dir`, so it takes the default path.
- `conftest._SANDBOX_ENV` sets `AW_HOME` and `XDG_CONFIG_HOME`, and `_restore_home_sandbox` pops `AW_CONFIG_DIR`.
- Commit `4ad21328e` exists.
- The spec line "honoring `XDG_CONFIG_HOME`" is present.
- Release `f33nrj` is `planned`, and `s4pys7` exists.
- `aw sanitize --agent` reports `clean`, exit 0.

I ran a scratch test under the gitignored `.aw/state/` and removed it afterwards:
- With `XDG_CONFIG_HOME` pointing at a temp config holding `aw_home` and `AW_HOME` cleared, current `resolve_project_context` returned `{'detail': 'platform default path', 'source': 'builtin_defaults'}`. That confirms the bug and that E-03(a) fails before the fix.
- With an explicit `user_config_dir`, the E-03(a) assertions (value, `global_defaults`, detail path) all passed. That confirms they are satisfiable after the fix.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Anti-regression | `runner_shared.prepare_agent_user_config` ("copies every regular top-level file"; `for child in real_dir.iterdir(): if child.is_file():`); both hosts set `child_env[_config.CONFIG_DIR_ENV] = str(user_config_handle.path)`; review probe: real dir gave `repository named_global_profile`, the seeded sandbox gave `home builtin_defaults` | After E-02, `resolve_project_context` honors `AW_CONFIG_DIR`, and every agent turn exports that variable pointing at a sandbox seeded with top-level files only. A `profiles/<name>.json` the operator relies on would therefore vanish inside agent turns. That is an unexplained behavior change the plan did not name. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added E-05/V-05: seed the top-level `profiles/` files into the sandbox (reconcile already uses `rglob` with relative keys, so no change is needed there), plus a containment test. Added F-05, and added `runner_shared.py` and `tests/test_agent_user_config_containment.py` to Scope-Paths. |
| PR-002 | MEDIUM | IN-SCOPE | E. Non-vacuity | E-03(b) `AW_CONFIG_DIR` case asserted `records_backend == "home"`; `resolve_project_context` falls back to `RecordsBackend.HOME.value` at `BUILTIN_DEFAULTS` | `home` is also the built-in default, so that assertion passes whether or not `AW_CONFIG_DIR` is honored. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Changed it to `default_records_backend: "repository"`, asserted together with `GLOBAL_DEFAULTS` provenance. |
| PR-003 | MEDIUM | IN-SCOPE | E. Verification feasibility | V-03 "with `agent_workflows/project_context.py` temporarily reverted (then restored)"; AGENTS.md forbids stashing to hide ownership | Reverting the file would discard the uncommitted E-02 edit, and the only safe way to restore it would be a stash. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 and Required tests now simulate the pre-fix lookup in-process by patching `project_context._config_dir` (which E-02 creates) to the hard-coded path, then check `git status`. |
| PR-004 | LOW | IN-SCOPE | E. Test hygiene | E-03 "pop `AW_HOME` and `AW_CONFIG_DIR` ... restoring `os.environ` in `finally`" | A hand-rolled pop and restore is easy to get wrong. The conftest restores only `AW_HOME` and `XDG_CONFIG_HOME`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Switched to `mock.patch.dict(os.environ, ..., clear=True)`. |
| PR-005 | LOW | IN-SCOPE | G. Contract / docs | `resolve_project_context` docstring Levels 4/5 name `~/.config/agent-workflows/...`; Scope-Paths lacked the plan file; OQ-01 `Owner: none` | The docstring would be inaccurate after the fix, the plan file was not declared in Scope-Paths, and the owner was a placeholder. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now updates the docstring. Added the plan path to Scope-Paths and set the owner to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the agent-turn profile regression be handled? | Seed `profiles/` into the sandbox in this plan (E-05) | (a) Make `project_context` ignore `AW_CONFIG_DIR`, which contradicts backlog `m9dobx` ("this reader would ignore that too"); (b) defer to a new backlog item, which would ship a known regression with a release-gating bug fix; (c) recursive seeding, which would copy unknown subtrees into every run dir | Backlog `m9dobx` Context; `runner_shared.reconcile_agent_user_config` uses `rglob`; plan `9y27t2` E-03 rationale on minimizing copies of private config | yes |
| D-2 | How should "tests fail without the fix" be shown? | Patch `_config_dir` in-process | Revert the file (would destroy E-02); stash (forbidden) | AGENTS.md execution contract | yes |
| D-3 | Accept OQ-01 (fixing `_resolve_effective_aw_home` covers `project_config_dir`)? | Yes | Separate fix | `project_config_dir` calls `_resolve_effective_aw_home(aw_home=aw_home)` | yes |
