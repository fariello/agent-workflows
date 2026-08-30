# IPD: Migrate user config schema to nested repos hierarchy with automatic migration

- Date: 2026-08-29
- Kind: child
- Concern: User configuration schema organization and migration to nested repos hierarchy without alias bloat.
- Scope: Refactor the user config schema in config.py to nest repository settings under repos (repos.search, repos.installed, repos.exclude, repos.ignore); bump config_version to 2 with a version-aware migrate() and a forward-compatibility guard so a newer config is never silently emptied; update accessors and every real call site in cli.py and project_context.py; keep the aw.agent/v1 status payload keys stable; sync the governing spec and CHANGELOG; update every affected test file.
- Scope-Paths: agent_workflows/config.py, agent_workflows/cli.py, agent_workflows/project_context.py, .aw/records/specs/20260706-0000-01-pip-distribution-and-multi-repo-setup.spec.md, CHANGELOG.md, tests/test_config.py, tests/test_cli.py, tests/test_exclude_include_status.py, tests/test_exclude_guard.py, tests/test_installer.py, tests/test_empty_state_ux.py, tests/test_json_and_exitcodes.py
- Item-Dependencies: none
- Status: approved
- Set: reposcfg
- Order: 1
- Highest E allocated: 14
- Author: antigravity
- Id: 8h9lap
- Approval: 2026-08-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-30 approved (aw set): status set to approved

- 2026-08-29 draft (antigravity): created.
- 2026-08-29 to-review (antigravity): authored complete plan.
- 2026-08-30 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-012 fixed in place (config_version 2 + downgrade guard, is_configured() dict trap, repos type change breaking `aw config add ... to repos`, real call-site inventory replacing the wrong doctor.py/discovery.py scope, agent-payload key stability, spec/CHANGELOG sync, E-01/E-02 split into right-sized items, V-items given concrete pasted evidence).
- 2026-08-30 reviewed (aw set): status set to reviewed

## Goal

Refactor the user configuration schema (`~/.config/agent-workflows/config.json`) from flat repository keys (`search_roots`, `repos`, `exclude`, `ignore`) to a clean nested dictionary under `"repos"` (`repos.search`, `repos.installed`, `repos.exclude`, `repos.ignore`). Automatically migrate legacy configs upon load or normalization without keeping redundant aliases in the schema, update CLI accessors and commands, and verify full backward-compatible migration.

Non-goals (bounded to keep this a schema refactor, not a behavior change):

- No change to WHAT discovery/install/exclude do; only WHERE their inputs are read from.
- No change to the `aw.agent/v1` machine payload key names (`search_roots`, `repos_configured` in `aw status`), which are a published contract (`docs/cli-output-contract.md:153`). The on-disk schema and the wire schema are deliberately decoupled here.
- No project-level (`.aw/config/local.json` / `project.json`) schema change.

Hard safety requirement (the reason this is a versioned migration, not a rename): the migration MUST be one-way-safe. `normalize()` today drops every unrecognized top-level key and `save()` re-serializes the normalized dict (`agent_workflows/config.py:632-657`, `agent_workflows/config.py:723`), so an OLDER `aw` binary reading a NEW nested config silently discards the user's search roots, repo allowlist, and never-install blocklist, then persists the emptied file on the next mutating command. Verified locally against the current code with a nested config planted at `$XDG_CONFIG_HOME`:

```
--- config.json AFTER an old-aw read+write:
{ "config_version": 1, "defaults": {...}, "exclude": [], "ignore": [], "repos": [], "search_roots": [] }
```

Losing a user-curated never-install blocklist is a SAFETY regression, not just data loss: `exclude` is what stops `aw install` from writing into a repo the user marked never-install (`agent_workflows/config.py:20-23`). This plan therefore bumps `config_version` to 2 and adds a forward-compatibility guard (E-03) so a newer-versioned config is refused rather than silently emptied.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Schema, migration, and downgrade safety in `agent_workflows/config.py`

- [ ] E-01 Redefine `CONFIG_SCHEMA` and `default_config()` for the nested `repos.*` layout, bumping `CONFIG_VERSION` to 2.
  - Depends on: none
  - Expected outcome: `CONFIG_VERSION = 2`. `CONFIG_SCHEMA` (`agent_workflows/config.py:70-117`) defines `repos` (dict), `repos.search` (list[path]), `repos.installed` (list[path]), `repos.exclude` (list[path|glob]), `repos.ignore` (list[str]), plus the unchanged `defaults`, `defaults.backup`, `defaults.prune`, `aw_home`, `config_version`. `default_config()` (`agent_workflows/config.py:580-590`) returns `"repos": {"search": [], "installed": [], "exclude": [], "ignore": []}` and no longer emits the four flat keys. `_ALLOWED_TOP_KEYS` becomes `{"config_version", "repos", "defaults", "aw_home"}` and a new `_ALLOWED_REPOS_KEYS = frozenset({"search", "installed", "exclude", "ignore"})` is added. NOTE: `_ALLOWED_TOP_KEYS` is currently DEAD (declared at `agent_workflows/config.py:44-54`, referenced nowhere else; verified by repo-wide grep); either wire it into `normalize()` as the actual allowlist or delete it. Do not leave a third dead constant behind.
  - Execution state: pending

- [ ] E-02 Rewrite `normalize()` to migrate the legacy flat keys into the nested `repos` mapping.
  - Depends on: E-01
  - Expected outcome: `normalize()` (`agent_workflows/config.py:625-657`) accepts EITHER shape and always returns the nested shape: a nested `repos` dict is coerced key-by-key (paths `~`-preserved via `_preserve_home`, `repos.ignore` as plain strings); a legacy flat config maps `search_roots`->`repos.search`, list-valued `repos`->`repos.installed`, `exclude`->`repos.exclude`, `ignore`->`repos.ignore`. Migration is decided by SHAPE (`isinstance(config.get("repos"), dict)`), not by `config_version` alone, so a hand-edited file with a stale version still migrates. A legacy flat key is honored ONLY when its nested counterpart is absent, so a partially migrated file cannot double-apply or lose data.
  - Execution state: pending

- [ ] E-03 Add the forward-compatibility (downgrade) guard so a newer config is never silently emptied.
  - Depends on: E-02
  - Expected outcome: `migrate()` (`agent_workflows/config.py:688-695`) becomes version-aware: `config_version <= 2` migrates forward as in E-02; a config whose `config_version` is GREATER than `CONFIG_VERSION` is NOT normalized-and-dropped. Instead `load()` (`agent_workflows/config.py:698-709`) returns it in a read-only/passthrough form and `save()` (`agent_workflows/config.py:712-738`) REFUSES to overwrite it, raising `ConfigError` with an actionable message naming the file and telling the user to upgrade `aw`. Rationale: without this, a future version bump repeats exactly the silent-emptying failure documented in the Goal, including the loss of the never-install blocklist. Fail closed: refusing to write is strictly safer than destroying a user's curated config.
  - Execution state: pending

- [ ] E-04 Update the list/dotted mutator and reader helpers to resolve nested `repos.*` keys.
  - Depends on: E-02
  - Expected outcome: `add_config_item`, `remove_config_item`, `is_config_item_present` (`agent_workflows/config.py:299-418`) and `get_config_value`/`set_config_value` (`agent_workflows/config.py:421-560`) read and write through a shared nested-path resolver (one helper, not five copies of split-on-dot logic) so `repos.search`, `repos.installed`, `repos.exclude`, `repos.ignore` behave exactly as the flat keys did. `set_config_value` on `repos` validates the dict against `_ALLOWED_REPOS_KEYS` and rejects an unknown subkey with a `ConfigError` rather than silently dropping it. The `parse_*` helpers need no change (verified: `parse_add_args(['~/src','to','repos.search'])` already returns `('~/src','repos.search')` because they only consult `CONFIG_SCHEMA` membership).
  - Execution state: pending

- [ ] E-05 Handle the BREAKING `repos` type change (list -> dict) on the `aw config` verbs.
  - Depends on: E-04
  - Expected outcome: `aw config add ~/src/foo to repos` works TODAY (`repos` is `list[path]`, verified: returns `['~/src/foo']`); after E-01 `repos` is a `dict`, so the generic list guard would emit the useless `Cannot add item to 'repos': it is not a list (type is dict).` For the list-mutating verbs ONLY (`add`/`remove`/`is`), a bare `repos` target raises a `ConfigError` that names the four concrete subkeys and suggests `repos.installed` as the direct successor of the old flat `repos`. `aw config show repos` / `get repos` still print the whole mapping (a dict read is legitimate). This is the one user-visible break and it must be loud, not cryptic.
  - Execution state: pending

- [ ] E-06 Update the `config.py` accessors and fix the `is_configured()` truthiness trap.
  - Depends on: E-02
  - Expected outcome: `expanded_search_roots`, `expanded_repos`, `expanded_excludes` (`agent_workflows/config.py:750-774`) read `repos.search`, `repos.installed`, `repos.exclude`; a new `ignore_patterns()` accessor returns `repos.ignore` so callers stop indexing the raw dict. `is_configured()` (`agent_workflows/config.py:741-747`) must test the nested LISTS, not the container: `bool(cfg.get("repos"))` is `True` for the all-empty default mapping (verified), which would make a brand-new user look configured and SUPPRESS the `aw` smart-default setup path (`agent_workflows/cli.py:8667`) and change `aw setup` non-interactive behavior (`agent_workflows/cli.py:5287`). It must remain `False` until at least one search root or installed repo exists.
  - Execution state: pending

### Task group 2: Update the real call sites

- [ ] E-07 Migrate the `cli.py` install/discovery/uninstall call sites off the flat keys.
  - Depends on: E-06
  - Expected outcome: every flat-key read/write in the install and discovery paths uses the nested layout or an accessor: `_exclude_guard` (`agent_workflows/cli.py:3676`), `_exclude_remove` (`agent_workflows/cli.py:3711-3716`), `_install_all` (`agent_workflows/cli.py:4198`), `_run_uninstall` (`agent_workflows/cli.py:4602-4605`), `_repos_for_report` (`agent_workflows/cli.py:4694-4701`), `_run_setup` (`agent_workflows/cli.py:5302-5364`). Scope correction: `agent_workflows/discovery.py` and `agent_workflows/doctor.py` need NO change and are removed from Scope-Paths. Verified: `discovery.py` does not import `config` at all (it receives `ignore=`/`exclude=` as plain arguments, `agent_workflows/discovery.py:111-134`) and `doctor.py` has zero references to the user-config repo keys.
  - Execution state: pending

- [ ] E-08 Migrate the `cli.py` exclude/include/status call sites, keeping the agent payload keys stable.
  - Depends on: E-06
  - Expected outcome: `_run_exclude` (`agent_workflows/cli.py:5159-5211`), `_run_include` (`agent_workflows/cli.py:5226-5273`), `_run_config_exclude` (`agent_workflows/cli.py:5846-5889`), and `_run_status` (`agent_workflows/cli.py:4992-5034`) read/write the nested layout. The `aw status` machine payload KEEPS its existing field names (`"search_roots"`, `"repos_configured"` at `agent_workflows/cli.py:5004-5005`); renaming them would be a breaking `aw.agent/v1` change requiring a `v2` bump per `docs/cli-output-contract.md:153-155`, which is explicitly out of scope. Only the on-disk source of those values changes.
  - Execution state: pending

- [ ] E-09 Disambiguate the `repos` key collision in `project_context.py`.
  - Depends on: E-02
  - Expected outcome: `project_context.py:477-480` reads the user config as RAW JSON (`_read_json_file`, bypassing `normalize()`) and interprets a dict-valued `repos` as a mapping of `repo_abs -> per-repo settings`. After E-01 the nested `repos` is ALSO a dict, so `user_repos.get(repo_abs)` now probes a mapping whose keys are `search`/`installed`/`exclude`/`ignore`. Verified it does not raise (it yields `{}`), so the failure mode is silent and future-fragile, not a crash. Resolve it explicitly: either read per-repo bindings from a distinctly named key, or guard with `_ALLOWED_REPOS_KEYS` so a schema mapping is never mistaken for a per-repo binding table. Add a comment recording that `repos` now has exactly one meaning.
  - Execution state: pending

### Task group 3: CLI presentation and help

- [ ] E-10 Update `_run_config_show` grouping and the `p_config` help/epilog examples.
  - Depends on: E-05
  - Expected outcome: `_run_config_show` (`agent_workflows/cli.py:5415-5535`) groups output under `Settings (repos)` and `Settings (defaults)`; its schema-iterating branch (`agent_workflows/cli.py:5520`) handles a two-level dotted key without printing the raw dict twice (today it `continue`s past `defaults` and special-cases `"." in key`; `repos` needs the same treatment). `aw config show repos` prints the whole mapping and `aw config show repos.search` the single setting, in human, `--json`, and `--agent` modes. The epilog and per-argument help examples (`agent_workflows/cli.py:2288-2371`, nine occurrences of `search_roots`) become `repos.search` / `repos.installed` / `repos.exclude` / `repos.ignore`.
  - Execution state: pending

### Task group 4: Documentation and spec sync

- [ ] E-11 Sync the governing spec and the module docstring.
  - Depends on: E-02
  - Expected outcome: the schema is NORMATIVELY specified in `.aw/records/specs/20260706-0000-01-pip-distribution-and-multi-repo-setup.spec.md:275-278` (`Status: implemented`), which literally states `{config_version:1, search_roots:[...], repos:[...], ignore:[...], defaults:{...}}`. That spec is amended (or superseded by an addendum recording the v2 schema) so it does not contradict the code, per the plan-review requirement that a behavior/schema change carries spec sync. The `config.py` module docstring (`agent_workflows/config.py:8-27`) shows the v2 nested example while keeping the `ignore` vs `exclude` distinction it documents today.
  - Execution state: pending

- [ ] E-12 Record the breaking change in `CHANGELOG.md`.
  - Depends on: E-05
  - Expected outcome: a `Changed (BREAKING)` entry under the `2.0.0 (pending)` heading (`CHANGELOG.md:7`) describing the nested `repos.*` layout, the automatic forward migration, the `config_version` 2 bump, the refusal-to-downgrade guard, and the one user-visible CLI break from E-05. Written in user-facing prose with no em or en dashes, per `CONTRIBUTING.md:142`.
  - Execution state: pending

### Task group 5: Tests

- [ ] E-13 Add migration, downgrade-guard, and nested-roundtrip tests in `tests/test_config.py`.
  - Depends on: E-06
  - Expected outcome: new tests cover (a) a legacy flat config normalizing into the nested shape with no value loss; (b) an already-nested config surviving a load/save roundtrip unchanged (idempotence); (c) a partially migrated config not double-applying; (d) get/set/add/remove/is roundtrip on each of the four `repos.*` keys; (e) the E-05 error naming the subkeys when a list verb targets bare `repos`; (f) the E-03 guard, asserting a `config_version: 3` file is NOT emptied and that `save()` refuses it; (g) `is_configured()` still `False` for a default nested config. The existing schema-key enumeration test (`tests/test_config.py:158-170`) is updated to the new key set.
  - Execution state: pending

- [ ] E-14 Update every existing test that constructs or asserts a flat-key config.
  - Depends on: E-13
  - Expected outcome: the flat-key fixtures and assertions are migrated across the real blast radius, measured by grep rather than assumed: `tests/test_config.py` (44 hits), `tests/test_exclude_include_status.py` (12), `tests/test_exclude_guard.py` (12), `tests/test_cli.py` (10), `tests/test_empty_state_ux.py` (3, including the hand-written planted config at `tests/test_empty_state_ux.py:373-384`), `tests/test_installer.py` (1). `tests/test_json_and_exitcodes.py:37` is re-verified UNCHANGED to prove the E-08 payload-stability requirement. Scope correction: `tests/test_discovery.py` and `tests/test_cli_help_and_errors.py` contain ZERO flat-key references (verified) and are removed from Scope-Paths.
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

Findings added during plan review (each verified against the code, not assumed):

- **Silent downgrade destroys the config, including a safety control.** `normalize()` drops unknown top-level keys and `save()` persists the normalized result (`agent_workflows/config.py:632-657`, `:723`), so an older `aw` reading a v2 nested config zeroes `search_roots`/`repos`/`exclude`/`ignore` and writes the emptied file back. Reproduced locally. Because `exclude` is the never-install blocklist that guards `aw install` (`agent_workflows/config.py:20-23`), this is a safety regression, which is why E-03 adds a fail-closed guard and `config_version` moves to 2.
- **`is_configured()` inverts for new users.** It returns `bool(cfg.get("search_roots") or cfg.get("repos"))` (`agent_workflows/config.py:747`). Under the nested layout the default `repos` mapping is a non-empty dict, so the check becomes unconditionally `True` (verified), silently disabling the unconfigured-user setup path at `agent_workflows/cli.py:8667` and altering `aw setup` at `agent_workflows/cli.py:5287`. E-06 fixes this.
- **`repos` changes type, breaking a working command.** `aw config add <path> to repos` succeeds today because `repos` is `list[path]` (verified). As a dict it hits the generic guard and reports `it is not a list (type is dict)`, which does not tell the user that `repos.installed` is the successor. E-05 makes the break explicit and actionable.
- **The original Scope-Paths were wrong in both directions.** `discovery.py` never imports `config` (it takes `ignore=`/`exclude=` as arguments, `agent_workflows/discovery.py:111-134`) and `doctor.py` has no user-config repo-key references, so neither needs editing; meanwhile `project_context.py` (untouched by the original plan) reads `repos` raw and would be affected. Similarly `tests/test_discovery.py` and `tests/test_cli_help_and_errors.py` have zero flat-key hits, while `test_cli.py`, `test_exclude_include_status.py`, `test_exclude_guard.py`, `test_empty_state_ux.py`, and `test_installer.py` do. Corrected in E-07/E-09/E-14.
- **`repos` would carry two incompatible meanings.** `project_context.py:477-480` treats a dict-valued `repos` as a per-repo settings mapping keyed by absolute repo path. The nested schema makes `repos` a dict of `search`/`installed`/`exclude`/`ignore`. It does not crash (verified: yields `{}`), so the collision is silent. E-09 disambiguates it.
- **The wire format must not move with the disk format.** `aw status` publishes `search_roots` and `repos_configured` in its payload (`agent_workflows/cli.py:5004-5005`); `docs/cli-output-contract.md:153-155` makes any breaking field-semantics change an `aw.agent/v2` matter. E-08 pins these names and `tests/test_json_and_exitcodes.py:37` is kept as the guard.
- **A normative spec contradicts the change.** The schema is specified as v1 flat in `.aw/records/specs/20260706-0000-01-pip-distribution-and-multi-repo-setup.spec.md:275-278`, whose `Status:` is `implemented`. E-11 syncs it so the spec does not silently become false.
- **`_ALLOWED_TOP_KEYS` is dead code.** Declared at `agent_workflows/config.py:44-54` and referenced nowhere else (repo-wide grep); `normalize()` enforces the allowlist implicitly by rebuilding from `default_config()`. E-01 requires wiring or deleting it rather than adding a second unused constant beside it.
- **Migration must be shape-driven and idempotent.** Deciding by `config_version` alone would skip a hand-edited file with a stale version, and re-applying legacy keys over already-nested values could clobber them. E-02 fixes migration on shape and honors a legacy key only when its nested counterpart is absent.

## Proposed changes (ordered, validatable)

1. **`agent_workflows/config.py`** (E-01..E-06):
   - Bump `CONFIG_VERSION` to `2`.
   - Update `_ALLOWED_TOP_KEYS` to `{"config_version", "repos", "defaults", "aw_home"}` and either wire it into `normalize()` or delete it (it is currently dead).
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
   - Update `normalize(config)` to migrate legacy flat keys into `repos.*`, keyed on SHAPE, honoring a legacy key only when its nested counterpart is absent (idempotent).
   - Make `migrate()` version-aware and add the fail-closed downgrade guard in `load()`/`save()` for `config_version > CONFIG_VERSION`.
   - Update `expanded_search_roots`, `expanded_repos`, `expanded_excludes`, and add `ignore_patterns`.
   - Fix `is_configured()` to test the nested lists, not the container dict.
   - Update `get_config_value`, `set_config_value`, `add_config_item`, `remove_config_item`, `is_config_item_present` to resolve dotted `repos.*` and `defaults.*` through ONE shared nested-path helper, and give bare `repos` an actionable error on the list-only verbs.

2. **`agent_workflows/cli.py`** (E-07, E-08, E-10):
   - Migrate the install/discovery/uninstall sites: `_exclude_guard` (:3676), `_exclude_remove` (:3711-3716), `_install_all` (:4198), `_run_uninstall` (:4602-4605), `_repos_for_report` (:4694-4701), `_run_setup` (:5302-5364).
   - Migrate the exclude/include/status sites: `_run_exclude` (:5159-5211), `_run_include` (:5226-5273), `_run_config_exclude` (:5846-5889), `_run_status` (:4992-5034), preserving the `search_roots`/`repos_configured` payload key names.
   - Update `_run_config_show` (:5415-5535) for section and sub-key inspection, including its `CONFIG_SCHEMA` iteration at :5520.
   - Update the `p_config` epilog and per-argument help examples (:2288-2371).

3. **`agent_workflows/project_context.py`** (E-09):
   - Disambiguate the raw-JSON `repos` read at :477-480 so a v2 schema mapping is never mistaken for a per-repo binding table.

4. **`.aw/records/specs/20260706-0000-01-...spec.md` and `CHANGELOG.md`** (E-11, E-12):
   - Amend the normative v1 flat schema statement at :275-278; add the breaking-change CHANGELOG entry.

5. **Tests** (E-13, E-14):
   - Add migration, idempotence, downgrade-guard, `is_configured()`, and nested-roundtrip coverage in `tests/test_config.py`.
   - Migrate flat-key fixtures in `tests/test_cli.py`, `tests/test_exclude_include_status.py`, `tests/test_exclude_guard.py`, `tests/test_empty_state_ux.py`, `tests/test_installer.py`.
   - Leave `tests/test_json_and_exitcodes.py` unchanged as the payload-stability guard.

Sequencing note: E-01 through E-06 land together as one coherent config.py change set; the suite will not be green until E-14, so the executor should not interpret intermediate red tests as failure. Only the final state must be green.

## Deferred / out of scope (with reason)

- Project-level local config (`.aw/config/local.json`), which is scoped to individual repo settings.
- Renaming the `aw status` machine payload fields `search_roots`/`repos_configured` to match the new disk layout. Deferred deliberately: `docs/cli-output-contract.md:153-155` makes a breaking field-semantics change an `aw.agent/v2` bump, which is a far larger blast radius than this schema refactor. The disk schema and the wire schema stay decoupled here.
- Deleting the legacy-key migration path in a later release. Keeping it indefinitely is cheap (a few lines in `normalize()`) and removing it is a separate decision with its own compatibility window.

## Scope check

- Over-scope: none. `agent_workflows/discovery.py` and `agent_workflows/doctor.py` were REMOVED from scope after verification showed neither reads the user-config repo keys (`discovery.py` does not import `config`; `doctor.py` has no such references). `tests/test_discovery.py` and `tests/test_cli_help_and_errors.py` were removed for the same reason (zero flat-key hits).
- Under-scope (added during review): `agent_workflows/project_context.py` (the raw-JSON `repos` read that now collides with the schema mapping), the `config_version` bump plus downgrade guard, the `is_configured()` truthiness fix, the `repos` type-change error path, the normative spec sync, the CHANGELOG entry, and the five additional test files that construct flat-key configs.

## Required tests / validation

- `pytest tests/test_config.py -v`
- Targeted regression of the files that build config fixtures: `pytest tests/test_cli.py tests/test_exclude_include_status.py tests/test_exclude_guard.py tests/test_empty_state_ux.py tests/test_installer.py tests/test_json_and_exitcodes.py -v`
- Full test suite `pytest` (runs with `-n auto` per `conftest.py`)
- `aw ipd lint --phase pre-transition --agent <this plan>`
- `aw sanitize --agent`
- CLI verification commands (run against an isolated `XDG_CONFIG_HOME`, never the maintainer's real config):
  - `aw config show`
  - `aw config show repos`
  - `aw config show repos.search`
  - `aw config add ~/src to repos.search`
  - `aw config is ~/src in repos.search`
  - `aw config remove ~/src from repos.search`
  - `aw conf show repos`
  - `aw config add ~/src to repos` (MUST fail with the actionable subkey message from E-05)
  - `aw status --agent` (payload MUST still carry `search_roots` and `repos_configured`)
- Migration verification with a planted legacy config under an isolated `XDG_CONFIG_HOME`: write a v1 flat config with all four keys populated, run a mutating command, and confirm every value is preserved under `repos.*` with nothing lost.

Validation-safety rule: every command above that can WRITE config MUST run with `XDG_CONFIG_HOME` pointed at a throwaway directory. Do not validate this plan against the maintainer's real `~/.config/agent-workflows/config.json`; a bug in the migration would destroy exactly the data this plan is meant to preserve.

## Spec / documentation sync

- `.aw/records/specs/20260706-0000-01-pip-distribution-and-multi-repo-setup.spec.md:275-278` amended: it currently specifies the flat v1 schema normatively and carries `Status: implemented`, so leaving it untouched would make an approved spec false. (E-11)
- `CHANGELOG.md` gains a `Changed (BREAKING)` entry under `2.0.0 (pending)`, in user-facing prose with no em or en dashes per `CONTRIBUTING.md:142`. (E-12)
- Module docstring in `agent_workflows/config.py:8-27` shows the v2 nested schema, preserving the documented `ignore` vs `exclude` distinction. (E-11)
- CLI help epilog and per-argument examples in `agent_workflows/cli.py:2288-2371` updated to `repos.*`. (E-10)
- No change to `docs/cli-output-contract.md`: the wire format is deliberately unchanged (see Deferred).

## Open questions

### OQ-01: Legacy config file on disk migration timing

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: `config.load()` calls `config.normalize()`, which seamlessly transforms legacy flat keys in memory. When any mutating operation (`aw config set`, `aw config add`, `aw setup`, `aw install`) runs, it saves the normalized new layout to disk automatically. Verified against the code during plan review: `load()` is read-only (`agent_workflows/config.py:698-709`, it calls `migrate()` and never `save()`), and the three mutators persist via `save(normalized)` at `agent_workflows/config.py:341`, `:390`, `:557`. So a read-only user's file stays on disk in v1 form until the first mutation, which is the intended lazy migration.

### OQ-02: Downgrade behavior when an older `aw` meets a v2 config

- Blocking: no
- Status: resolved
- Owner: plan-review
- Resolution or deferral rationale: resolved from repository evidence rather than escalated, because the repo answers it. An older `aw` CANNOT be taught to read v2, so the only lever is making the CURRENT version fail closed for the NEXT bump. Evidence: `normalize()` rebuilds from `default_config()` and drops unknown keys (`agent_workflows/config.py:632-657`), and `save()` writes `normalize(config)` (`agent_workflows/config.py:723`), so an unrecognized-shape config is silently emptied and persisted (reproduced locally). Decision: bump `config_version` to 2 and add the E-03 guard so a config newer than the running binary is never normalized-and-overwritten; `save()` refuses with an actionable `ConfigError`. Accepted residual risk, stated honestly: any `aw` version ALREADY released cannot honor this guard, so a user who downgrades across this specific boundary can still lose the flat keys. The mitigation is the CHANGELOG breaking-change notice (E-12); the guard prevents a recurrence at every future bump.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the output of `python3 -c "from agent_workflows import config as C; print(C.CONFIG_VERSION); print(sorted(C.CONFIG_SCHEMA)); print(C.default_config())"`. It MUST show `2`, the four `repos.*` keys present with `repos` typed `dict`, no flat `search_roots`/`ignore`/`exclude` keys, and a nested `default_config()`. Also paste the grep proving `_ALLOWED_TOP_KEYS` is either referenced by `normalize()` or gone: `rg -n '_ALLOWED_TOP_KEYS' agent_workflows/`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste output of a script that normalizes a fully populated LEGACY flat config and prints the result, showing all four values relocated under `repos.*` with none lost; then normalize the RESULT again and show it is byte-identical (idempotence); then normalize a PARTIAL config carrying both `search_roots` and `repos.search` and show the nested value wins and is not double-appended.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: with an isolated `XDG_CONFIG_HOME`, plant a config with `"config_version": 3` and populated `repos.*`, then paste output proving (a) `load()` does NOT return emptied lists and (b) `save()` raises `ConfigError` naming the file. Then paste `cat` of the file showing it is BYTE-IDENTICAL to what was planted. This is the anti-data-loss gate; a passing unit test alone is not sufficient, the file must be shown intact.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a transcript of get/set/add/remove/is against each of `repos.search`, `repos.installed`, `repos.exclude`, `repos.ignore` showing correct values after each step, plus the `ConfigError` raised when `set_config_value("repos", ...)` is given an unknown subkey.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the actual terminal output and exit code of `aw config add ~/src to repos`. The message MUST name `repos.installed` (and the other subkeys) and MUST NOT be the bare `it is not a list (type is dict)` string. Also paste `aw config show repos` succeeding, proving the dict READ path still works.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste output proving `is_configured()` is `False` for a freshly written default nested config (the regression this guards) and `True` once a `repos.search` entry is added. Also paste `aw --agent` (or the non-TTY path) on an unconfigured isolated `XDG_CONFIG_HOME` showing the setup-needed path still triggers, per `agent_workflows/cli.py:8667`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `rg -n 'get\("search_roots"|get\("ignore"|\["search_roots"\]' agent_workflows/cli.py` returning NO hits in the E-07 functions, plus a successful `aw install <throwaway-repo> --yes` and `aw uninstall <throwaway-repo> --yes` transcript showing the repo added to and removed from `repos.installed`. Also paste the grep evidence that `discovery.py` and `doctor.py` required no change.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `aw status --agent` output showing the payload STILL contains `search_roots` and `repos_configured`, and paste the passing result of `pytest tests/test_json_and_exitcodes.py -v` with that file UNMODIFIED (confirm with `git diff --stat tests/test_json_and_exitcodes.py` showing no changes). Also paste an `aw exclude` / `aw include` round trip transcript.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the diff of `agent_workflows/project_context.py` around the `repos` read, plus output of `resolve_project_context()` (or the covering test) run against a repo while a v2 nested user config is present, proving no per-repo binding is fabricated from the schema keys `search`/`installed`/`exclude`/`ignore`.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste `aw config show`, `aw config show repos`, `aw config show repos.search`, `aw config show --json`, and `aw config show repos --agent` output. The grouped human output must show `Settings (repos)` and `Settings (defaults)` and must NOT print the `repos` mapping twice.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste the spec diff showing `:275-278` no longer states the flat v1 schema, plus `rg -n 'search_roots' .aw/records/specs/ agent_workflows/config.py` showing no stale normative flat-schema claim remains.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: paste the CHANGELOG diff, and confirm no em or en dash was introduced by pasting the output of a dash grep over the added lines (`rg -n '[—–]' CHANGELOG.md`).
  - Observed evidence:
  - Result: pending

- [ ] V-13 validates E-13
  - Required evidence: paste the FULL actual output of `pytest tests/test_config.py -v`, showing the new migration, idempotence, downgrade-guard, `is_configured()`, bare-`repos`-error, and per-key roundtrip tests by NAME and passing. A summary line alone is insufficient; the named tests must be visible.
  - Observed evidence:
  - Result: pending

- [ ] V-14 validates E-14
  - Required evidence: paste the FULL actual output of the whole-suite `pytest` run (final summary line included) showing 0 failures and 0 errors. Per the repo execution contract, do NOT claim tests passed without pasting the real runner output. Also paste `aw sanitize --agent` exiting clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

All work is bounded to user configuration schema restructuring, auto-migration, the downgrade guard, affected call sites, CLI display, spec/CHANGELOG sync, and tests.

### Execution contract

- **Open questions:** OQ-01 and OQ-02 are resolved (see above). No blocking question remains. Do not begin if any question has been reopened.
- **Scope fence:** touch ONLY the files in `Scope-Paths`. Specifically do NOT edit `agent_workflows/discovery.py` or `agent_workflows/doctor.py` (verified unaffected), and do NOT rename the `aw status` machine payload fields (an `aw.agent/v2` matter, explicitly deferred). If the work appears to require a file outside `Scope-Paths`, STOP and report rather than widening scope silently.
- **Validation isolation (safety):** every config-writing validation command MUST run with `XDG_CONFIG_HOME` set to a throwaway directory. Never validate against the maintainer's real `~/.config/agent-workflows/config.json`.
- **Honesty rule (hard MUST):** paste the ACTUAL runner output for every validation item. Never claim a test passed that was not run. An unrun check is `blocked`, not `pass`.
- **Commit rule:** commit ONLY the files you changed, path-scoped (`git commit -m "<msg>" -- <path> ...`). Never `git add -A`, never `git commit -a`, and NEVER push. Other agents are working in this same checkout: before each commit run `git diff --cached --name-only` and unstage anything you did not modify. Note that `agent_workflows/cli.py` and `agent_workflows/doctor.py` currently have UNCOMMITTED changes by another party; do not sweep them into your commit.
- **Lifecycle move:** this plan is NOT complete until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries pasted evidence. Only then perform the terminal transaction (workflow-history line, terminal `Status:`, `git mv` to `.aw/records/plans/executed/`, path-scoped lifecycle commit). The move is a post-gate transaction, never a checklist item.
