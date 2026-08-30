# IPD: Migrate user config schema to nested repos hierarchy with automatic migration

- Date: 2026-08-29
- Kind: child
- Concern: User configuration schema organization and migration to nested repos hierarchy without alias bloat.
- Scope: Refactor config schema in config.py to nest repository settings under repos (repos.search, repos.installed, repos.exclude, repos.ignore), auto-migrate legacy configs on load/normalize, update accessors and callers across cli.py, discovery.py, doctor.py, and update the test suite.
- Scope-Paths: agent_workflows/config.py, agent_workflows/cli.py, agent_workflows/discovery.py, agent_workflows/doctor.py, tests/test_config.py, tests/test_discovery.py, tests/test_cli_help_and_errors.py
- Item-Dependencies: none
- Status: to-review
- Set: reposcfg
- Order: 1
- Highest E allocated: 04
- Author: antigravity
- Id: 8h9lap

## Workflow history

- 2026-08-29 draft (antigravity): created.
- 2026-08-29 to-review (antigravity): authored complete plan.

## Goal

Refactor the user configuration schema (`~/.config/agent-workflows/config.json`) from flat repository keys (`search_roots`, `repos`, `exclude`, `ignore`) to a clean nested dictionary under `"repos"` (`repos.search`, `repos.installed`, `repos.exclude`, `repos.ignore`). Automatically migrate legacy configs upon load or normalization without keeping redundant aliases in the schema, update CLI accessors and commands, and verify full backward-compatible migration.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Nested `repos.*` Schema & Auto-Migration in `agent_workflows/config.py`

- [ ] E-01 Refactor `CONFIG_SCHEMA`, `default_config()`, and `normalize()` in `agent_workflows/config.py` to use nested `repos.*` structure with automatic legacy migration.
  - Depends on: none
  - Expected outcome: `CONFIG_SCHEMA` defines `repos` (dict), `repos.search` (list[path]), `repos.installed` (list[path]), `repos.exclude` (list[path|glob]), `repos.ignore` (list[str]), `defaults`, `defaults.backup`, `defaults.prune`, `aw_home`, `config_version`. `normalize()` migrates legacy flat keys (`search_roots`, flat `repos`, `exclude`, `ignore`) to the nested `repos` dictionary. Dotted get/set/add/remove/is functions operate cleanly on nested fields.
  - Execution state: pending

### Task group 2: Update Config Accessors & Callers in `cli.py`, `discovery.py`, and `doctor.py`

- [ ] E-02 Update accessors in `config.py` and caller workflows across `cli.py`, `discovery.py`, and `doctor.py`.
  - Depends on: E-01
  - Expected outcome: `expanded_search_roots`, `expanded_repos`, `expanded_excludes`, `ignore_patterns` (or `discovery_ignores`), and `is_configured` query the nested `repos` mapping. `aw setup`, `aw list-repos`, `aw exclude`, `aw include`, `aw status`, and `aw doctor` operate cleanly with the new layout.
  - Execution state: pending

### Task group 3: CLI Output Formatting and Examples in `cli.py`

- [ ] E-03 Update `_run_config_show` and `p_config` parser help and epilog in `agent_workflows/cli.py`.
  - Depends on: E-02
  - Expected outcome: `aw config show` groups settings under `Settings (repos)` and `Settings (defaults)`. `aw config show repos` prints the entire `repos` dictionary. `aw config show repos.search` prints the targeted setting. Help epilog reflects `repos.search`, `repos.installed`, `repos.exclude`, `repos.ignore`.
  - Execution state: pending

### Task group 4: Comprehensive Tests and Migration Verification

- [ ] E-04 Add unit test coverage in `tests/test_config.py` and update existing tests for the nested `repos.*` schema and auto-migration.
  - Depends on: E-03
  - Expected outcome: Test suite verifies auto-migration of legacy flat config dicts, full roundtrip of get/set/add/remove/is/show for `repos.search`, `repos.installed`, `repos.exclude`, `repos.ignore`, and all existing tests pass with 0 failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Single source of truth for user config is `agent_workflows/config.py`.
- Config lives under `$XDG_CONFIG_HOME/agent-workflows/config.json` (falling back to `~/.config/agent-workflows/config.json`).
- Dotted paths represent nested dictionary properties in JSON (e.g. `defaults.backup`).
- Path items store `~`-preserved paths and expand at use-time.
- Writes are atomic via temporary files and `os.replace`.

## Findings

- Previous schema mixed flat repository keys (`search_roots`, `repos`, `exclude`, `ignore`) with dotted keys (`defaults.backup`, `defaults.prune`).
- Renaming `search_roots` to `repos.search` eliminates redundant `_root` suffix and groups all repository management concerns under the `repos` namespace.
- Renaming flat `repos` to `repos.installed` clarifies that it is the list of configured/managed repository targets.
- Placing `exclude` and `ignore` under `repos` (`repos.exclude`, `repos.ignore`) clarifies their scope and relationship.
- Automatic migration on load/normalize eliminates the need for permanent alias bloat in the schema.

## Proposed changes (ordered, validatable)

1. **`agent_workflows/config.py`**:
   - Update `_ALLOWED_TOP_KEYS` to `{"config_version", "repos", "defaults", "aw_home"}`.
   - Define `_ALLOWED_REPOS_KEYS = frozenset({"search", "installed", "exclude", "ignore"})`.
   - Update `CONFIG_SCHEMA`:
     - `repos`: `dict`
     - `repos.search`: `list[path]`
     - `repos.installed`: `list[path]`
     - `repos.exclude`: `list[path|glob]`
     - `repos.ignore`: `list[str]`
     - `defaults`: `dict`
     - `defaults.backup`: `bool`
     - `defaults.prune`: `bool`
     - `aw_home`: `path`
     - `config_version`: `int`
   - Update `default_config()` to return `"repos": {"search": [], "installed": [], "exclude": [], "ignore": []}`.
   - Update `normalize(config)` to migrate legacy flat keys into `repos.*`.
   - Update `expanded_search_roots`, `expanded_repos`, `expanded_excludes`, `ignore_patterns` accessors.
   - Update `get_config_value`, `set_config_value`, `add_config_item`, `remove_config_item`, `is_config_item_present` to support dotted keys in `repos.*` and `defaults.*`.

2. **`agent_workflows/cli.py`**:
   - Update `_run_setup`, `_run_exclude`, `_run_include`, `_run_status`, `_run_list` to use updated config structure/accessors.
   - Update `_run_config_show` to handle section inspection (`repos`, `defaults`) and sub-key inspection (`repos.search`, etc.).
   - Update help epilog examples in `p_config`.

3. **`agent_workflows/discovery.py` & `agent_workflows/doctor.py`**:
   - Verify all discovery and doctor calls use updated `config.expanded_*` accessors.

4. **`tests/test_config.py`**:
   - Add tests for legacy config auto-migration.
   - Add tests for `repos.search`, `repos.installed`, `repos.exclude`, `repos.ignore` via `get`, `set`, `add`, `remove`, `is`, `show`.
   - Update tests that verify `config.json` structure and CLI commands.

## Deferred / out of scope (with reason)

- Project-level local config (`.aw/config/local.json`), which is scoped to individual repo settings.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `pytest tests/test_config.py -v`
- Full test suite `pytest`
- `aw sanitize --agent`
- CLI verification commands:
  - `aw config show`
  - `aw config show repos`
  - `aw config show repos.search`
  - `aw config add ~/src to repos.search`
  - `aw config is ~/src in repos.search`
  - `aw config remove ~/src from repos.search`
  - `aw conf show repos`

## Spec / documentation sync

- Docstrings in `config.py` and CLI help epilog in `cli.py` updated with `repos.*` examples.

## Open questions

### OQ-01: Legacy config file on disk migration timing

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: `config.load()` calls `config.normalize()`, which seamlessly transforms legacy flat keys in memory. When any mutating operation (`aw config set`, `aw config add`, `aw setup`, `aw install`) runs, it saves the normalized new layout to disk automatically.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Unit tests in `tests/test_config.py` verify that `normalize()` transforms legacy flat keys to `repos.*` and that `CONFIG_SCHEMA` defines all `repos.*` keys.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `aw setup`, `aw list-repos`, `aw exclude`, `aw include`, and `aw status` operate without errors on new and migrated configs.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `aw config show`, `aw config show repos`, and `aw config show repos.search` display correctly formatted output in human, `--json`, and `--agent` modes.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `pytest tests/test_config.py -v` and full test suite `pytest` pass with 0 failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

All work is bounded to user configuration schema restructuring, auto-migration, CLI display, and tests.
