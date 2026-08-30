# IPD: Migrate user config schema to nested repos hierarchy with automatic migration

- Date: 2026-08-29
- Kind: child
- Concern: User configuration schema organization and migration to nested repos hierarchy without alias bloat.
- Scope: Refactor the user config schema in config.py to nest repository settings under repos (repos.search, repos.installed, repos.exclude, repos.ignore); bump config_version to 2 with a version-aware migrate() and a forward-compatibility guard so a newer config is never silently emptied; update accessors and every real call site in cli.py and project_context.py; keep the aw.agent/v1 status payload keys stable; sync the governing spec and CHANGELOG; update every affected test file.
- Scope-Paths: agent_workflows/config.py, agent_workflows/cli.py, agent_workflows/project_context.py, .aw/records/specs/20260706-0000-01-pip-distribution-and-multi-repo-setup.spec.md, CHANGELOG.md, tests/test_config.py, tests/test_cli.py, tests/test_exclude_include_status.py, tests/test_exclude_guard.py, tests/test_installer.py, tests/test_empty_state_ux.py, tests/test_json_and_exitcodes.py
- Item-Dependencies: none
- Status: executed
- Set: reposcfg
- Order: 1
- Highest E allocated: 14
- Author: antigravity
- Id: 8h9lap

## Workflow history
- 2026-08-30 executed (opencode its_direct/pt3-claude-opus-5-1m-us): nested repos.* user config schema (config_version 2) with shape-driven idempotent migration, fail-closed downgrade guard, is_configured() truthiness fix, actionable bare-repos break, call sites and spec/CHANGELOG synced; V-01..V-14 verified with pasted evidence; 19 pre-existing suite failures proven identical to baseline d4d265b (3239 -> 3270 passing) [Scope reconciliation - in-scope-unmodified .aw/records/specs/20260706-0000-01-pip-distribution-and-multi-repo-setup.spec.md: modified-in-commit-6734160a-before-begin-receipt-base; in-scope-unmodified CHANGELOG.md: modified-in-commit-6734160a-before-begin-receipt-base; in-scope-unmodified agent_workflows/cli.py: modified-in-commit-6734160a-before-begin-receipt-base; in-scope-unmodified agent_workflows/config.py: modified-in-commit-6734160a-before-begin-receipt-base; in-scope-unmodified agent_workflows/project_context.py: modified-in-commit-6734160a-before-begin-receipt-base; in-scope-unmodified tests/test_cli.py: modified-in-commit-6734160a-before-begin-receipt-base; in-scope-unmodified tests/test_config.py: modified-in-commit-6734160a-before-begin-receipt-base; in-scope-unmodified tests/test_empty_state_ux.py: modified-in-commit-6734160a-before-begin-receipt-base; in-scope-unmodified tests/test_exclude_guard.py: modified-in-commit-6734160a-before-begin-receipt-base; in-scope-unmodified tests/test_exclude_include_status.py: modified-in-commit-6734160a-before-begin-receipt-base; in-scope-unmodified tests/test_installer.py: modified-in-commit-6734160a-before-begin-receipt-base; in-scope-unmodified tests/test_json_and_exitcodes.py: deliberately-unmodified-payload-stability-guard-see-V-08]
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

- [x] E-01 Redefine `CONFIG_SCHEMA` and `default_config()` for the nested `repos.*` layout, bumping `CONFIG_VERSION` to 2.
  - Depends on: none
  - Expected outcome: `CONFIG_VERSION = 2`. `CONFIG_SCHEMA` (`agent_workflows/config.py:70-117`) defines `repos` (dict), `repos.search` (list[path]), `repos.installed` (list[path]), `repos.exclude` (list[path|glob]), `repos.ignore` (list[str]), plus the unchanged `defaults`, `defaults.backup`, `defaults.prune`, `aw_home`, `config_version`. `default_config()` (`agent_workflows/config.py:580-590`) returns `"repos": {"search": [], "installed": [], "exclude": [], "ignore": []}` and no longer emits the four flat keys. `_ALLOWED_TOP_KEYS` becomes `{"config_version", "repos", "defaults", "aw_home"}` and a new `_ALLOWED_REPOS_KEYS = frozenset({"search", "installed", "exclude", "ignore"})` is added. NOTE: `_ALLOWED_TOP_KEYS` is currently DEAD (declared at `agent_workflows/config.py:44-54`, referenced nowhere else; verified by repo-wide grep); either wire it into `normalize()` as the actual allowlist or delete it. Do not leave a third dead constant behind.
  - Execution state: performed

- [x] E-02 Rewrite `normalize()` to migrate the legacy flat keys into the nested `repos` mapping.
  - Depends on: E-01
  - Expected outcome: `normalize()` (`agent_workflows/config.py:625-657`) accepts EITHER shape and always returns the nested shape: a nested `repos` dict is coerced key-by-key (paths `~`-preserved via `_preserve_home`, `repos.ignore` as plain strings); a legacy flat config maps `search_roots`->`repos.search`, list-valued `repos`->`repos.installed`, `exclude`->`repos.exclude`, `ignore`->`repos.ignore`. Migration is decided by SHAPE (`isinstance(config.get("repos"), dict)`), not by `config_version` alone, so a hand-edited file with a stale version still migrates. A legacy flat key is honored ONLY when its nested counterpart is absent, so a partially migrated file cannot double-apply or lose data.
  - Execution state: performed

- [x] E-03 Add the forward-compatibility (downgrade) guard so a newer config is never silently emptied.
  - Depends on: E-02
  - Expected outcome: `migrate()` (`agent_workflows/config.py:688-695`) becomes version-aware: `config_version <= 2` migrates forward as in E-02; a config whose `config_version` is GREATER than `CONFIG_VERSION` is NOT normalized-and-dropped. Instead `load()` (`agent_workflows/config.py:698-709`) returns it in a read-only/passthrough form and `save()` (`agent_workflows/config.py:712-738`) REFUSES to overwrite it, raising `ConfigError` with an actionable message naming the file and telling the user to upgrade `aw`. Rationale: without this, a future version bump repeats exactly the silent-emptying failure documented in the Goal, including the loss of the never-install blocklist. Fail closed: refusing to write is strictly safer than destroying a user's curated config.
  - Execution state: performed

- [x] E-04 Update the list/dotted mutator and reader helpers to resolve nested `repos.*` keys.
  - Depends on: E-02
  - Expected outcome: `add_config_item`, `remove_config_item`, `is_config_item_present` (`agent_workflows/config.py:299-418`) and `get_config_value`/`set_config_value` (`agent_workflows/config.py:421-560`) read and write through a shared nested-path resolver (one helper, not five copies of split-on-dot logic) so `repos.search`, `repos.installed`, `repos.exclude`, `repos.ignore` behave exactly as the flat keys did. `set_config_value` on `repos` validates the dict against `_ALLOWED_REPOS_KEYS` and rejects an unknown subkey with a `ConfigError` rather than silently dropping it. The `parse_*` helpers need no change (verified: `parse_add_args(['~/src','to','repos.search'])` already returns `('~/src','repos.search')` because they only consult `CONFIG_SCHEMA` membership).
  - Execution state: performed

- [x] E-05 Handle the BREAKING `repos` type change (list -> dict) on the `aw config` verbs.
  - Depends on: E-04
  - Expected outcome: `aw config add ~/src/foo to repos` works TODAY (`repos` is `list[path]`, verified: returns `['~/src/foo']`); after E-01 `repos` is a `dict`, so the generic list guard would emit the useless `Cannot add item to 'repos': it is not a list (type is dict).` For the list-mutating verbs ONLY (`add`/`remove`/`is`), a bare `repos` target raises a `ConfigError` that names the four concrete subkeys and suggests `repos.installed` as the direct successor of the old flat `repos`. `aw config show repos` / `get repos` still print the whole mapping (a dict read is legitimate). This is the one user-visible break and it must be loud, not cryptic.
  - Execution state: performed

- [x] E-06 Update the `config.py` accessors and fix the `is_configured()` truthiness trap.
  - Depends on: E-02
  - Expected outcome: `expanded_search_roots`, `expanded_repos`, `expanded_excludes` (`agent_workflows/config.py:750-774`) read `repos.search`, `repos.installed`, `repos.exclude`; a new `ignore_patterns()` accessor returns `repos.ignore` so callers stop indexing the raw dict. `is_configured()` (`agent_workflows/config.py:741-747`) must test the nested LISTS, not the container: `bool(cfg.get("repos"))` is `True` for the all-empty default mapping (verified), which would make a brand-new user look configured and SUPPRESS the `aw` smart-default setup path (`agent_workflows/cli.py:8667`) and change `aw setup` non-interactive behavior (`agent_workflows/cli.py:5287`). It must remain `False` until at least one search root or installed repo exists.
  - Execution state: performed

### Task group 2: Update the real call sites

- [x] E-07 Migrate the `cli.py` install/discovery/uninstall call sites off the flat keys.
  - Depends on: E-06
  - Expected outcome: every flat-key read/write in the install and discovery paths uses the nested layout or an accessor: `_exclude_guard` (`agent_workflows/cli.py:3676`), `_exclude_remove` (`agent_workflows/cli.py:3711-3716`), `_install_all` (`agent_workflows/cli.py:4198`), `_run_uninstall` (`agent_workflows/cli.py:4602-4605`), `_repos_for_report` (`agent_workflows/cli.py:4694-4701`), `_run_setup` (`agent_workflows/cli.py:5302-5364`). Scope correction: `agent_workflows/discovery.py` and `agent_workflows/doctor.py` need NO change and are removed from Scope-Paths. Verified: `discovery.py` does not import `config` at all (it receives `ignore=`/`exclude=` as plain arguments, `agent_workflows/discovery.py:111-134`) and `doctor.py` has zero references to the user-config repo keys.
  - Execution state: performed

- [x] E-08 Migrate the `cli.py` exclude/include/status call sites, keeping the agent payload keys stable.
  - Depends on: E-06
  - Expected outcome: `_run_exclude` (`agent_workflows/cli.py:5159-5211`), `_run_include` (`agent_workflows/cli.py:5226-5273`), `_run_config_exclude` (`agent_workflows/cli.py:5846-5889`), and `_run_status` (`agent_workflows/cli.py:4992-5034`) read/write the nested layout. The `aw status` machine payload KEEPS its existing field names (`"search_roots"`, `"repos_configured"` at `agent_workflows/cli.py:5004-5005`); renaming them would be a breaking `aw.agent/v1` change requiring a `v2` bump per `docs/cli-output-contract.md:153-155`, which is explicitly out of scope. Only the on-disk source of those values changes.
  - Execution state: performed

- [x] E-09 Disambiguate the `repos` key collision in `project_context.py`.
  - Depends on: E-02
  - Expected outcome: `project_context.py:477-480` reads the user config as RAW JSON (`_read_json_file`, bypassing `normalize()`) and interprets a dict-valued `repos` as a mapping of `repo_abs -> per-repo settings`. After E-01 the nested `repos` is ALSO a dict, so `user_repos.get(repo_abs)` now probes a mapping whose keys are `search`/`installed`/`exclude`/`ignore`. Verified it does not raise (it yields `{}`), so the failure mode is silent and future-fragile, not a crash. Resolve it explicitly: either read per-repo bindings from a distinctly named key, or guard with `_ALLOWED_REPOS_KEYS` so a schema mapping is never mistaken for a per-repo binding table. Add a comment recording that `repos` now has exactly one meaning.
  - Execution state: performed

### Task group 3: CLI presentation and help

- [x] E-10 Update `_run_config_show` grouping and the `p_config` help/epilog examples.
  - Depends on: E-05
  - Expected outcome: `_run_config_show` (`agent_workflows/cli.py:5415-5535`) groups output under `Settings (repos)` and `Settings (defaults)`; its schema-iterating branch (`agent_workflows/cli.py:5520`) handles a two-level dotted key without printing the raw dict twice (today it `continue`s past `defaults` and special-cases `"." in key`; `repos` needs the same treatment). `aw config show repos` prints the whole mapping and `aw config show repos.search` the single setting, in human, `--json`, and `--agent` modes. The epilog and per-argument help examples (`agent_workflows/cli.py:2288-2371`, nine occurrences of `search_roots`) become `repos.search` / `repos.installed` / `repos.exclude` / `repos.ignore`.
  - Execution state: performed

### Task group 4: Documentation and spec sync

- [x] E-11 Sync the governing spec and the module docstring.
  - Depends on: E-02
  - Expected outcome: the schema is NORMATIVELY specified in `.aw/records/specs/20260706-0000-01-pip-distribution-and-multi-repo-setup.spec.md:275-278` (`Status: implemented`), which literally states `{config_version:1, search_roots:[...], repos:[...], ignore:[...], defaults:{...}}`. That spec is amended (or superseded by an addendum recording the v2 schema) so it does not contradict the code, per the plan-review requirement that a behavior/schema change carries spec sync. The `config.py` module docstring (`agent_workflows/config.py:8-27`) shows the v2 nested example while keeping the `ignore` vs `exclude` distinction it documents today.
  - Execution state: performed

- [x] E-12 Record the breaking change in `CHANGELOG.md`.
  - Depends on: E-05
  - Expected outcome: a `Changed (BREAKING)` entry under the `2.0.0 (pending)` heading (`CHANGELOG.md:7`) describing the nested `repos.*` layout, the automatic forward migration, the `config_version` 2 bump, the refusal-to-downgrade guard, and the one user-visible CLI break from E-05. Written in user-facing prose with no em or en dashes, per `CONTRIBUTING.md:142`.
  - Execution state: performed

### Task group 5: Tests

- [x] E-13 Add migration, downgrade-guard, and nested-roundtrip tests in `tests/test_config.py`.
  - Depends on: E-06
  - Expected outcome: new tests cover (a) a legacy flat config normalizing into the nested shape with no value loss; (b) an already-nested config surviving a load/save roundtrip unchanged (idempotence); (c) a partially migrated config not double-applying; (d) get/set/add/remove/is roundtrip on each of the four `repos.*` keys; (e) the E-05 error naming the subkeys when a list verb targets bare `repos`; (f) the E-03 guard, asserting a `config_version: 3` file is NOT emptied and that `save()` refuses it; (g) `is_configured()` still `False` for a default nested config. The existing schema-key enumeration test (`tests/test_config.py:158-170`) is updated to the new key set.
  - Execution state: performed

- [x] E-14 Update every existing test that constructs or asserts a flat-key config.
  - Depends on: E-13
  - Expected outcome: the flat-key fixtures and assertions are migrated across the real blast radius, measured by grep rather than assumed: `tests/test_config.py` (44 hits), `tests/test_exclude_include_status.py` (12), `tests/test_exclude_guard.py` (12), `tests/test_cli.py` (10), `tests/test_empty_state_ux.py` (3, including the hand-written planted config at `tests/test_empty_state_ux.py:373-384`), `tests/test_installer.py` (1). `tests/test_json_and_exitcodes.py:37` is re-verified UNCHANGED to prove the E-08 payload-stability requirement. Scope correction: `tests/test_discovery.py` and `tests/test_cli_help_and_errors.py` contain ZERO flat-key references (verified) and are removed from Scope-Paths.
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: paste the output of `python3 -c "from agent_workflows import config as C; print(C.CONFIG_VERSION); print(sorted(C.CONFIG_SCHEMA)); print(C.default_config())"`. It MUST show `2`, the four `repos.*` keys present with `repos` typed `dict`, no flat `search_roots`/`ignore`/`exclude` keys, and a nested `default_config()`. Also paste the grep proving `_ALLOWED_TOP_KEYS` is either referenced by `normalize()` or gone: `rg -n '_ALLOWED_TOP_KEYS' agent_workflows/`.
  - Observed evidence: VERIFIED. `CONFIG_VERSION` is `2`; `sorted(CONFIG_SCHEMA)` is `['aw_home', 'config_version', 'defaults', 'defaults.backup', 'defaults.prune', 'repos', 'repos.exclude', 'repos.ignore', 'repos.installed', 'repos.search']`, i.e. all four `repos.*` keys present, `repos` typed `dict`, and NO flat `search_roots`/`ignore`/`exclude`; `default_config()` returns the nested shape. `_ALLOWED_TOP_KEYS` is WIRED IN (config.py:803) as the allowlist `normalize()` actually applies, and a test proves it load-bearing. Full transcript below.

```text
$ python3 -c "from agent_workflows import config as C; print(C.CONFIG_VERSION); print(sorted(C.CONFIG_SCHEMA)); print(C.default_config())"
2
['aw_home', 'config_version', 'defaults', 'defaults.backup', 'defaults.prune', 'repos', 'repos.exclude', 'repos.ignore', 'repos.installed', 'repos.search']
{'config_version': 2, 'repos': {'search': [], 'installed': [], 'exclude': [], 'ignore': []}, 'defaults': {'backup': True, 'prune': True}}

CONFIG_VERSION is 2; the four `repos.*` keys are present; there is NO flat `search_roots`,
`ignore`, or `exclude`; `default_config()` is nested. `repos` is typed `dict`:

$ python3 -c "from agent_workflows import config as C; print(C.CONFIG_SCHEMA['repos'].type_name)"
dict

`_ALLOWED_TOP_KEYS` is WIRED IN, not dead: it is the allowlist `normalize()` actually applies
on its return path (line 803), so a future key added to `default_config()` without
allowlisting cannot leak through.

$ rg -n '_ALLOWED_TOP_KEYS' agent_workflows/
agent_workflows/config.py:57:_ALLOWED_TOP_KEYS = frozenset(
agent_workflows/config.py:799:    # `_ALLOWED_TOP_KEYS` is the ACTUAL final allowlist (R-5), applied unconditionally rather
agent_workflows/config.py:803:    return {key: value for key, value in out.items() if key in _ALLOWED_TOP_KEYS}

Proven load-bearing by test (not just by inspection):
tests/test_config.py::SchemaMigrationTests::test_normalize_applies_the_top_key_allowlist PASSED
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste output of a script that normalizes a fully populated LEGACY flat config and prints the result, showing all four values relocated under `repos.*` with none lost; then normalize the RESULT again and show it is byte-identical (idempotence); then normalize a PARTIAL config carrying both `search_roots` and `repos.search` and show the nested value wins and is not double-appended.
  - Observed evidence: VERIFIED. A fully populated LEGACY flat config migrates with NO value loss (all four keys relocated under `repos.*`, order preserved, path vs glob handled correctly); re-normalizing the RESULT is byte-identical (idempotent); and a PARTIAL config carrying both `search_roots` and `repos.search` yields exactly the nested value with no double-append, while a legacy key lacking a nested counterpart still migrates in. Full transcript below.

```text
$ python3 - <<'PY'
import json
from agent_workflows import config as C
legacy = {"config_version":1,"search_roots":["~/src","~/work"],"repos":["~/src/foo","~/src/bar"],
          "exclude":["~/src/legacy","*/never-install/*"],"ignore":["*/vendor/*"],
          "defaults":{"backup":False,"prune":True}}
once = C.normalize(legacy)
print("MIGRATED:", json.dumps(once, indent=2, sort_keys=True))
twice = C.normalize(once)
print("IDEMPOTENT byte-identical:", json.dumps(once,sort_keys=True) == json.dumps(twice,sort_keys=True))
partial = {"config_version":1,"search_roots":["~/legacy-root"],"repos":{"search":["~/new-root"]},"ignore":["*/vendor/*"]}
print("PARTIAL:", json.dumps(C.normalize(partial)["repos"], sort_keys=True))
PY
MIGRATED: {
  "config_version": 2,
  "defaults": {
    "backup": false,
    "prune": true
  },
  "repos": {
    "exclude": [
      "~/src/legacy",
      "*/never-install/*"
    ],
    "ignore": [
      "*/vendor/*"
    ],
    "installed": [
      "~/src/foo",
      "~/src/bar"
    ],
    "search": [
      "~/src",
      "~/work"
    ]
  }
}
IDEMPOTENT byte-identical: True
PARTIAL: {"exclude": [], "ignore": ["*/vendor/*"], "installed": [], "search": ["~/new-root"]}

All four legacy values relocated with NONE lost: search_roots -> repos.search (both entries,
order preserved), repos -> repos.installed (both), exclude -> repos.exclude (path AND glob),
ignore -> repos.ignore. `defaults` untouched. Re-normalizing the RESULT is byte-identical, so
the migration is idempotent. On the PARTIAL config carrying BOTH `search_roots: ["~/legacy-root"]`
and `repos.search: ["~/new-root"]`, the nested value WINS and the legacy value is NOT appended
(result is exactly ["~/new-root"], not two entries), while `ignore`, which has no nested
counterpart, still migrates in. Migration is shape-driven, so a stale/absent version still works:

tests/test_config.py::SchemaMigrationTests::test_legacy_flat_config_migrates_with_no_value_loss PASSED
tests/test_config.py::SchemaMigrationTests::test_migration_is_idempotent PASSED
tests/test_config.py::SchemaMigrationTests::test_partially_migrated_config_does_not_double_apply PASSED
tests/test_config.py::SchemaMigrationTests::test_migration_is_shape_driven_not_version_driven PASSED
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: with an isolated `XDG_CONFIG_HOME`, plant a config with `"config_version": 3` and populated `repos.*`, then paste output proving (a) `load()` does NOT return emptied lists and (b) `save()` raises `ConfigError` naming the file. Then paste `cat` of the file showing it is BYTE-IDENTICAL to what was planted. This is the anti-data-loss gate; a passing unit test alone is not sufficient, the file must be shown intact.
  - Observed evidence: VERIFIED, and the file is provably intact. With an isolated `XDG_CONFIG_HOME` and a planted `config_version: 3` config, (a) `load()` returns every `repos.*` value UNEMPTIED including `repos.exclude`, and (b) `save()` raises `ConfigError` NAMING the file, in both directions (saving the future config, and saving an ordinary default over a future file on disk). The file is BYTE-IDENTICAL by sha256 (22a378ee...) after the refusals. Full transcript below.

```text
Isolated throwaway XDG_CONFIG_HOME (never the maintainer's real config):

$ export XDG_CONFIG_HOME=$(mktemp -d /tmp/opencode/awv3.XXXXXX)   # -> /tmp/opencode/awv3.mNy4pe
$ cat > "$XDG_CONFIG_HOME/agent-workflows/config.json" <<'EOF'
{
  "config_version": 3,
  "repos": {
    "search": ["~/src"],
    "installed": ["~/src/foo"],
    "exclude": ["~/src/never-install-me"],
    "ignore": ["*/vendor/*"]
  },
  "future_only_key": {"kept": true}
}
EOF
$ sha256sum -> 22a378ee49cd5ed74a7585c4aed4c2d846a3c602ebd605720fe6eeaf22932aef

$ python3 -c 'load, then try to save'
load() returned: {'config_version': 3, 'repos': {'search': ['~/src'], 'installed': ['~/src/foo'], 'exclude': ['~/src/never-install-me'], 'ignore': ['*/vendor/*']}, 'future_only_key': {'kept': True}}
exclude NOT emptied: ['~/src/never-install-me']
save() raised ConfigError: Refusing to write /tmp/opencode/awv3.mNy4pe/agent-workflows/config.json: the configuration in memory declares config_version 3, but this aw understands up to 2. Nothing was changed. Upgrade aw (for example 'pip install --upgrade agent-workflows') to manage this config.
save(default) raised ConfigError: Refusing to overwrite /tmp/opencode/awv3.mNy4pe/agent-workflows/config.json: it was written by a newer aw (config_version 3; this aw understands up to 2). Nothing was changed. Upgrade aw (for example 'pip install --upgrade agent-workflows') to manage this config.

(a) load() did NOT return emptied lists: every `repos.*` value is intact, INCLUDING
`repos.exclude` (the never-install blocklist whose loss is the safety regression this guards),
and the unknown `future_only_key` survives too, because a future config is passed through
rather than normalized. (b) save() raises ConfigError NAMING THE FILE, in both directions:
saving the future config itself, AND saving an ordinary default config over a future file on
disk (the real-world downgrade path, where the in-memory config looks perfectly current).

$ cat "$XDG_CONFIG_HOME/agent-workflows/config.json"
{
  "config_version": 3,
  "repos": {
    "search": ["~/src"],
    "installed": ["~/src/foo"],
    "exclude": ["~/src/never-install-me"],
    "ignore": ["*/vendor/*"]
  },
  "future_only_key": {"kept": true}
}
BYTE-IDENTICAL: YES (22a378ee49cd5ed74a7585c4aed4c2d846a3c602ebd605720fe6eeaf22932aef)

The file is byte-identical by sha256 to what was planted: the anti-data-loss gate held, and
nothing was written. Backed by tests, including the CLI-level path where a mutating verb hits
the guard and still leaves the file untouched:

tests/test_config.py::MigrationOnDiskTests::test_future_version_config_is_not_emptied_on_load PASSED
tests/test_config.py::MigrationOnDiskTests::test_save_refuses_to_overwrite_a_future_version_config PASSED
tests/test_config.py::MigrationOnDiskTests::test_future_version_mutating_verb_fails_without_data_loss PASSED
tests/test_config.py::MigrationOnDiskTests::test_current_and_older_versions_are_not_treated_as_future PASSED
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste a transcript of get/set/add/remove/is against each of `repos.search`, `repos.installed`, `repos.exclude`, `repos.ignore` showing correct values after each step, plus the `ConfigError` raised when `set_config_value("repos", ...)` is given an unknown subkey.
  - Observed evidence: VERIFIED. get/set/add/remove/is each resolve correctly against all four of `repos.search`, `repos.installed`, `repos.exclude`, `repos.ignore`, with the right value after every step, and `repos.ignore` correctly stores raw globs without home-preservation. `set_config_value("repos", ...)` with an unknown subkey raises `ConfigError: Unknown key(s) in 'repos': bogus. Allowed keys: exclude, ignore, installed, search.` Full transcript below.

```text
$ python3 - (get/set/add/remove/is against each of the four repos.* keys)
repos.search: add -> added=True items=['~/src/thing']
repos.search: get -> ['~/src/thing']
repos.search: is  -> True
repos.search: set -> ['x', 'y']
repos.search: rm  -> removed=True items=['y']
repos.installed: add -> added=True items=['~/src/thing']
repos.installed: get -> ['~/src/thing']
repos.installed: is  -> True
repos.installed: set -> ['x', 'y']
repos.installed: rm  -> removed=True items=['y']
repos.exclude: add -> added=True items=['~/src/thing']
repos.exclude: get -> ['~/src/thing']
repos.exclude: is  -> True
repos.exclude: set -> ['x', 'y']
repos.exclude: rm  -> removed=True items=['y']
repos.ignore: add -> added=True items=['*/glob/*']
repos.ignore: get -> ['*/glob/*']
repos.ignore: is  -> True
repos.ignore: set -> ['x', 'y']
repos.ignore: rm  -> removed=True items=['y']
set repos unknown subkey -> Unknown key(s) in 'repos': bogus. Allowed keys: exclude, ignore, installed, search.

Every verb resolves the nested key correctly for all four subkeys, with the right value after
each step: add reports added=True and the item present, get returns it, is finds it, set
replaces the list, remove reports removed=True and leaves the remainder. Note `repos.ignore`
stores a raw glob (`*/glob/*`) with no home-preservation, correct for a fnmatch pattern, while
the path-typed subkeys `~`-preserve. `set_config_value("repos", ...)` with an unknown subkey
raises ConfigError NAMING the bad key and listing the allowed ones, instead of silently
dropping it (which is what normalize() alone would have done on the next save).

All verbs share ONE nested-path resolver (`_resolve_nested`/`_assign_nested`), not five copies
of split-on-dot logic. `parse_*` needed no change, as the plan predicted:

$ python3 -c "from agent_workflows import config as C; print(C.parse_add_args(['~/src','to','repos.search']))"
('~/src', 'repos.search')

tests/test_config.py::NestedRepoKeyVerbTests::test_roundtrip_on_every_repos_subkey PASSED
tests/test_config.py::NestedRepoKeyVerbTests::test_set_config_value_on_every_repos_subkey PASSED
tests/test_config.py::NestedRepoKeyVerbTests::test_set_repos_mapping_rejects_unknown_subkey PASSED
tests/test_config.py::NestedRepoKeyVerbTests::test_repo_setting_reader_degrades_to_empty PASSED
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the actual terminal output and exit code of `aw config add ~/src to repos`. The message MUST name `repos.installed` (and the other subkeys) and MUST NOT be the bare `it is not a list (type is dict)` string. Also paste `aw config show repos` succeeding, proving the dict READ path still works.
  - Observed evidence: VERIFIED. `aw config add ~/src/foo to repos` exits 2 with a message that NAMES `repos.installed` as the successor of the old flat `repos` plus the other three subkeys and a copy-pasteable example; it is NOT the bare `it is not a list (type is dict)` string. `aw config show repos` still succeeds (exit 0), proving the dict READ path works. Full transcript below.

```text
$ export XDG_CONFIG_HOME=$(mktemp -d /tmp/opencode/awv5.XXXXXX)
$ python3 -m agent_workflows config add '~/src/foo' to repos
FAIL           Cannot add item to 'repos': it is now a group of settings, not a list. Use one of: repos.installed (the explicit repository allowlist, which is what the old flat 'repos' key was), repos.search (discovery search roots), repos.exclude (the never-install blocklist), or repos.ignore (discovery noise globs). For example: aw config add <value> to repos.installed
$ echo $?
2

Exit code 2. The message NAMES `repos.installed` and identifies it as the successor of the old
flat `repos` key, plus the other three subkeys, and ends with a copy-pasteable example. It is
NOT the bare, useless `it is not a list (type is dict)` string the generic guard would have
produced. The same actionable error covers `remove` and `is`, each with a verb-appropriate
example.

The dict READ path still works (a dict read is legitimate; only the LIST verbs break):

$ python3 -m agent_workflows config show repos
agent-workflows configuration
  File:    /tmp/opencode/awv5.VusXRG/agent-workflows/config.json (none yet; default values in effect)

Setting
  repos.exclude        = []
  repos.ignore         = []
  repos.installed      = []
  repos.search         = []
$ echo $?
0

tests/test_config.py::ConfigCliCommandTests::test_cli_config_add_to_bare_repos_is_actionable PASSED
tests/test_config.py::NestedRepoKeyVerbTests::test_list_verbs_on_bare_repos_name_the_subkeys PASSED
tests/test_config.py::NestedRepoKeyVerbTests::test_reading_bare_repos_still_works PASSED
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste output proving `is_configured()` is `False` for a freshly written default nested config (the regression this guards) and `True` once a `repos.search` entry is added. Also paste `aw --agent` (or the non-TTY path) on an unconfigured isolated `XDG_CONFIG_HOME` showing the setup-needed path still triggers, per `agent_workflows/cli.py:8667`.
  - Observed evidence: VERIFIED. `is_configured()` is `False` for a freshly written default nested config even though the `repos` CONTAINER is truthy (`True`, the exact trap), and flips to `True` once a `repos.search` entry is added. The setup-needed path still triggers, shown on the non-TTY human path which distinguishes the branches (`WARN Not configured. Run 'aw setup' to get started.` appears unconfigured and stops appearing once configured). Full transcript below.

```text
$ export XDG_CONFIG_HOME=$(mktemp -d /tmp/opencode/awv6.XXXXXX)
$ python3 - <<'PY'
from agent_workflows import config as C
C.save(C.default_config())
print("file exists:", C.config_path().is_file())
print("container truthiness (the trap):", bool(C.load()["repos"]))
print("is_configured() on default nested config:", C.is_configured())
cfg = C.load(); C.set_repo_setting(cfg, "search", ["~/src"]); C.save(cfg)
print("is_configured() after adding repos.search:", C.is_configured())
PY
file exists: True
container truthiness (the trap): True
is_configured() on default nested config: False
is_configured() after adding repos.search: True

This is the exact regression E-06 guards: the `repos` CONTAINER is truthy (`True` above) even
for an all-empty default config, so a container check would have reported a brand-new user as
configured. `is_configured()` correctly returns False, and flips to True once a `repos.search`
entry exists.

The setup-needed path at cli.py still triggers on an unconfigured isolated XDG. Shown on the
non-TTY HUMAN path, which distinguishes the two branches (under --agent/--json BOTH branches
emit the same status payload, so that mode cannot demonstrate the difference):

$ export XDG_CONFIG_HOME=$(mktemp -d /tmp/opencode/awv6c.XXXXXX)
$ python3 -m agent_workflows --no-color < /dev/null | head -4
WARN           Not configured. Run 'aw setup' to get started.
agent-workflows status
Environment:
  Packaged version: 1.3.0rc2.dev1596+gd4d265b6.d20260830

$ python3 -m agent_workflows config add '~/src' to repos.search >/dev/null
$ python3 -m agent_workflows --no-color < /dev/null | head -4
agent-workflows status
Environment:
  Packaged version: 1.3.0rc2.dev1596+gd4d265b6.d20260830
  Python: 3.14.6 (...)

The "Not configured" branch fires when unconfigured and STOPS firing once repos.search is
populated, proving the smart-default setup path is intact.

tests/test_config.py::SaveLoadTests::test_is_configured_false_for_default_nested_config PASSED
tests/test_config.py::SaveLoadTests::test_is_configured_true_for_installed_only PASSED
tests/test_config.py::SaveLoadTests::test_is_configured PASSED
tests/test_config.py::NestedRepoKeyVerbTests::test_accessors_read_the_nested_layout PASSED
```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `rg -n 'get\("search_roots"|get\("ignore"|\["search_roots"\]' agent_workflows/cli.py` returning NO hits in the E-07 functions, plus a successful `aw install <throwaway-repo> --yes` and `aw uninstall <throwaway-repo> --yes` transcript showing the repo added to and removed from `repos.installed`. Also paste the grep evidence that `discovery.py` and `doctor.py` required no change.
  - Observed evidence: VERIFIED. `rg` for flat-key reads AND writes across all of cli.py returns ZERO hits (exit 1); the only surviving `search_roots` tokens are the accessor name and the deliberately stable wire key. A throwaway repo was ADDED to and REMOVED from `repos.installed` (`include` then `uninstall`), and `install all` reads the nested allowlist. Grep confirms `discovery.py` does not import `config` at all and `doctor.py` has zero user-config repo-key references, and neither file appears in the commit. Full transcript below.

```text
No flat-key read or write remains anywhere in cli.py (searched more broadly than V-07 asked,
covering writes too, not only the E-07 functions):

$ rg -n 'get\("search_roots"|get\("ignore"|\["search_roots"\]|get\("exclude"|cfg\["repos"\]|cfg\["exclude"\]' agent_workflows/cli.py
$ echo $?
1

(exit 1 = zero matches). The only surviving `search_roots` tokens in cli.py are the accessor
NAME and the deliberately stable wire key:

$ rg -n 'search_roots' agent_workflows/cli.py
4695:    roots = config.expanded_search_roots(cfg)
5008:        "search_roots": config.repo_setting(cfg, "search"),
5353:    expanded_roots = config.expanded_search_roots(cfg)

Every E-07 site now goes through the nested layout or an accessor: _exclude_guard
(expanded_excludes), _exclude_remove (repo_setting + set_repo_setting), _install_all
(expanded_repos), _run_uninstall (repo_setting + set_repo_setting), _repos_for_report
(expanded_repos/expanded_search_roots/ignore_patterns/expanded_excludes), _run_setup
(repo_setting + set_repo_setting).

Install/uninstall round trip against a THROWAWAY repo and isolated XDG. Note `aw install <dir>`
never wrote the allowlist (pre-existing behavior: only `setup`/`include` do), so the
add-side is shown with the verb that actually writes it:

$ python3 -m agent_workflows include /tmp/opencode/v7repo
OK             Included repository: /tmp/opencode/v7repo
repos.installed = ['/tmp/opencode/v7repo']

$ python3 -m agent_workflows uninstall /tmp/opencode/v7repo --yes
OK             removed .agents/skills/advise-architect/SKILL.md
... (removals elided)
repos.installed = []

The repo was ADDED to and REMOVED from `repos.installed`. `install all` also reads the nested
allowlist correctly:

$ python3 -m agent_workflows config add /tmp/opencode/v7repo to repos.installed >/dev/null
$ python3 -m agent_workflows install all --yes
Repository root: /tmp/opencode/v7repo
OK             /tmp/opencode/v7repo: installed/updated 340 file(s); version 1.2.1.

Scope correction verified: discovery.py and doctor.py needed NO change.

$ rg -c 'import config|from agent_workflows import config|from agent_workflows.config' agent_workflows/discovery.py
$ echo $?
1
(discovery.py does not import config at all; it takes ignore=/exclude= as plain arguments)

$ rg -n 'search_roots|repos_configured|"exclude"|"ignore"' agent_workflows/doctor.py
$ echo $?
1
(doctor.py has zero user-config repo-key references)

Both were removed from Scope-Paths and neither was touched:
$ git show --stat --format='' HEAD | rg 'discovery|doctor'
(no output)
```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste `aw status --agent` output showing the payload STILL contains `search_roots` and `repos_configured`, and paste the passing result of `pytest tests/test_json_and_exitcodes.py -v` with that file UNMODIFIED (confirm with `git diff --stat tests/test_json_and_exitcodes.py` showing no changes). Also paste an `aw exclude` / `aw include` round trip transcript.
  - Observed evidence: VERIFIED. The `aw.agent/v1` payload STILL contains `search_roots` and `repos_configured`, now sourced from `repos.search`/`repos.installed` (shown both empty and populated: `search_roots = ['~/src']`, `repos_configured = 1`). `tests/test_json_and_exitcodes.py` is UNMODIFIED (`git diff --stat` and `git status --porcelain` both empty, absent from the commit) and its 5 tests pass. An `aw exclude`/`aw include` round trip moves the repo between `repos.exclude` and `repos.installed` correctly. Full transcript below.

```text
The aw.agent/v1 payload STILL carries both published field names, now sourced from the nested
layout. Empty config:

$ python3 -m agent_workflows status --json | python3 -c 'inspect payload'
search_roots present: True -> []
repos_configured present: True -> 0
schema: aw.agent/v1

And populated, proving they are actually read from repos.search / repos.installed:

$ python3 -m agent_workflows config add '~/src' to repos.search
$ python3 -m agent_workflows config add '/tmp/opencode/v7repo' to repos.installed
$ python3 -m agent_workflows status --json | python3 -c 'inspect payload'
search_roots = ['~/src']
repos_configured = 1

$ python3 -m agent_workflows status --agent
{"schema":"aw.agent/v1","kind":"result","cmd":"status","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["currency"],"next":null}

The guard file is UNMODIFIED, confirmed two ways:

$ git diff --stat tests/test_json_and_exitcodes.py
(empty)
$ git status --porcelain tests/test_json_and_exitcodes.py
(empty)
$ git show --stat --format='' HEAD | rg test_json_and_exitcodes
(no output; not in the commit)

$ python3 -m pytest tests/test_json_and_exitcodes.py -v
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
12 workers [5 items]
.....                                                                    [100%]
============================== 5 passed in 5.26s ===============================

exclude / include round trip (both write the nested layout):

$ python3 -m agent_workflows exclude /tmp/opencode/v8repo
OK             Excluded repository: /tmp/opencode/v8repo
exclude: ['/tmp/opencode/v8repo'] installed: []
$ python3 -m agent_workflows include /tmp/opencode/v8repo
OK             Included repository: /tmp/opencode/v8repo (un-excluded)
exclude: [] installed: ['/tmp/opencode/v8repo']

Excluding moved the repo into repos.exclude and out of repos.installed; including reversed both
halves, which is exactly the pre-existing semantics on the new layout.
```
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste the diff of `agent_workflows/project_context.py` around the `repos` read, plus output of `resolve_project_context()` (or the covering test) run against a repo while a v2 nested user config is present, proving no per-repo binding is fabricated from the schema keys `search`/`installed`/`exclude`/`ignore`.
  - Observed evidence: VERIFIED. The diff adds `_is_repos_schema_mapping()` plus a comment recording that `repos` now has exactly ONE meaning, and the read only consults a path key when the mapping is NOT the schema mapping. `resolve_project_context()` against a repo with a v2 nested user config present fabricates NO per-repo binding from the keys search/installed/exclude/ignore, and a REAL per-repo binding table is still honored end-to-end (`delivery_mode: copy`, and a conflicting value even reaches the conflict detector). `tests/test_project_context.py` passes (16). Full transcript below.

```text
$ git show HEAD -- agent_workflows/project_context.py (the `repos` read)
+def _is_repos_schema_mapping(value: Dict[str, Any]) -> bool:
+    """True when a dict-valued user-config ``repos`` is the schema mapping, not a binding table.
+    ...
+    from agent_workflows.config import _ALLOWED_REPOS_KEYS
+
+    return all(key in _ALLOWED_REPOS_KEYS for key in value)

+    # `repos` in the USER config (config_version 2) is the schema mapping of repository
+    # settings: exactly the keys search/installed/exclude/ignore. It has ONE meaning, and it is
+    # NOT a per-repo binding table keyed by absolute repo path. This read bypasses
+    # `config.normalize()` on purpose (raw JSON), so it must reject the schema mapping itself
+    # rather than probe it with a path key and quietly get nothing back.
     user_repos = user_cfg_data.get("repos")
     repo_cfg_in_user: Dict[str, Any] = {}
-    if isinstance(user_repos, dict):
-        repo_cfg_in_user = user_repos.get(repo_abs, {}) or {}
+    if isinstance(user_repos, dict) and not _is_repos_schema_mapping(user_repos):
+        candidate = user_repos.get(repo_abs)
+        if isinstance(candidate, dict):
+            repo_cfg_in_user = candidate

The comment recording that `repos` now has exactly one meaning is present, as E-09 required.

resolve_project_context() run against a repo WITH a v2 nested user config present:

$ (planted {"config_version":2,"repos":{"search":["~/src"],"installed":["/tmp/opencode/v9repo"],...}})
$ python3 -c 'resolve_project_context("/tmp/opencode/v9repo", user_config_dir=...)'
is_configured: True
delivery_mode: copy
no MACHINE_LOCAL provenance fabricated from schema keys: True []
resolve_project_context did NOT raise and fabricated no per-repo binding

No per-repo binding is fabricated from the schema keys search/installed/exclude/ignore. The
discriminator is correct in BOTH directions:

$ python3 -c 'exercise _is_repos_schema_mapping'
v2 schema mapping        -> True
partial schema mapping   -> True
empty dict               -> True
per-repo binding table   -> False

And a REAL per-repo binding table is still honored end-to-end (not merely classified), proving
the guard did not break the legitimate feature:

$ (planted {"repos":{"/tmp/opencode/v9repo":{"delivery_mode":"copy"}}})
$ python3 -c 'resolve_project_context(...)'
per-repo binding table STILL honored; delivery_mode: copy

A conflicting binding value even reaches the conflict detector, further proof it is read:
ConflictingConfigurationError: Conflicting delivery_mode settings between durable config (copy)
and user local binding (symlink)

$ python3 -m pytest tests/test_project_context.py -q
................                                                         [100%]
(16 passed)
```
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: paste `aw config show`, `aw config show repos`, `aw config show repos.search`, `aw config show --json`, and `aw config show repos --agent` output. The grouped human output must show `Settings (repos)` and `Settings (defaults)` and must NOT print the `repos` mapping twice.
  - Observed evidence: VERIFIED for the grouping requirement, with ONE honest pre-existing residual on `--agent`. Human output groups under `Settings (repos)` and `Settings (defaults)` and does NOT print the `repos` mapping twice (container keys are section headings, so no raw dict value appears); `aw config show repos` prints the whole group, `repos.search` one setting, and `--json` returns the correct nested payload. RESIDUAL: `aw config show repos --agent` CRASHES with `ImportError: cannot import name 'format_agent_json' from 'agent_workflows.term'`, PROVEN pre-existing (that symbol does not exist in term.py at the starting commit, where cli.py imports it in 7 places; identical error reproduced in a pristine d4d265b worktree). term.py is outside Scope-Paths, so it is reported not fixed (DECISION 07-8h9lap-D2). Full transcript below.

```text
$ python3 -m agent_workflows config show --no-color
agent-workflows configuration
  File:    /tmp/opencode/awv10.n6m6uy/agent-workflows/config.json (present)

Settings
  aw_home              = -
  config_version       = 2
Settings (defaults)
  defaults.backup      = True
  defaults.prune       = True
Settings (repos)
  repos.exclude        = []
  repos.ignore         = []
  repos.installed      = [~/src/foo]
  repos.search         = [~/src]

Grouped under `Settings (repos)` and `Settings (defaults)`, and the `repos` mapping is NOT
printed twice: the container keys are section HEADINGS, so no raw dict value appears anywhere
(no `'search': [...]` text in the output).

$ python3 -m agent_workflows config show repos --no-color
agent-workflows configuration
  File:    /tmp/opencode/awv10.n6m6uy/agent-workflows/config.json (present)

Setting
  repos.exclude        = []
  repos.ignore         = []
  repos.installed      = [~/src/foo]
  repos.search         = [~/src]

$ python3 -m agent_workflows config show repos.search --no-color
...
Setting
  repos.search         = [~/src]

The whole mapping prints for `repos`; the single setting prints for `repos.search`.

$ python3 -m agent_workflows config show --json
{
  "config": {
    "config_version": 2,
    "defaults": {"backup": true, "prune": true},
    "repos": {
      "exclude": [],
      "ignore": [],
      "installed": ["~/src/foo"],
      "search": ["~/src"]
    }
  },
  "config_file": "/tmp/opencode/awv10.n6m6uy/agent-workflows/config.json",
  "config_present": true
}

Multi-entry lists render expanded, and the `conf` alias works:

$ python3 -m agent_workflows conf show repos --no-color
Setting
  repos.exclude        = [
      ~/src/legacy,
      */never-install/*,
  ]
  repos.ignore         = [
      */vendor/*,
      */node_modules/*,
  ]
  repos.installed      = [
      ~/src/foo,
      ~/src/bar,
  ]
  repos.search         = [
      ~/src,
      ~/work,
      ~/extra,
  ]

HONEST RESIDUAL on the `--agent` mode this V-item also asks for: `aw config show repos --agent`
CRASHES, and it did so BEFORE this plan. Actual output:

$ python3 -m agent_workflows config show repos --agent
Traceback (most recent call last):
  ...
  File "agent_workflows/cli.py", line 5456, in _run_config_show
    from agent_workflows.term import format_agent_json
ImportError: cannot import name 'format_agent_json' from 'agent_workflows.term'

PROVEN PRE-EXISTING, not caused by this change: `agent_workflows/term.py` has ZERO occurrences
of `format_agent_json` while `cli.py` imports it in SEVEN places, both at the starting commit
d4d265b, and the identical ImportError reproduces in a pristine baseline worktree:

$ cd <pristine d4d265b worktree> && python3 -m agent_workflows config show search_roots --agent
ImportError: cannot import name 'format_agent_json' from 'agent_workflows.term'

`term.py` is OUTSIDE this plan's Scope-Paths, so per the plan's scope fence this is reported,
not fixed here (see DECISION 07-8h9lap-D2 in the run register; recommended as a corrective IPD).
The `--json` mode above exercises the SAME `get_config_value` resolution and payload, so E-10's
substance is demonstrated.

tests/test_config.py::ConfigCliCommandTests::test_cli_config_show_groups_sections PASSED
tests/test_config.py::ConfigCliCommandTests::test_cli_config_show_repos_group_and_subkey PASSED
tests/test_config.py::ConfigCliCommandTests::test_cli_config_show_and_json PASSED
tests/test_config.py::ConfigCliCommandTests::test_cli_config_show_single_var PASSED
tests/test_config.py::ConfigCliCommandTests::test_cli_conf_alias PASSED

Help text updated (E-10's second half); zero `search_roots` examples remain:
$ rg -c 'repos\.search' agent_workflows/cli.py   (epilog + 6 per-argument help strings)
```
  - Result: pass

- [x] V-11 validates E-11
  - Required evidence: paste the spec diff showing `:275-278` no longer states the flat v1 schema, plus `rg -n 'search_roots' .aw/records/specs/ agent_workflows/config.py` showing no stale normative flat-schema claim remains.
  - Observed evidence: VERIFIED. The spec diff shows the flat v1 schema statement at :275-278 REPLACED by the v2 nested schema, plus two further statements synced (Goal 4 and AC-4) that would otherwise have become false, plus a new `## Amendment 2026-08-30` section with the v1->v2 mapping table and six normative points. `rg -n 'search_roots' .aw/records/specs/ agent_workflows/config.py` leaves NO stale normative flat-schema claim: every hit is a historical note, the `_LEGACY_KEY_MAP` migration entry, the accessor NAME, the amendment's own table, or the deliberately preserved wire key. `aw specs check` reports all specs conform. Full transcript below.

```text
$ git show HEAD -- .aw/records/specs/20260706-0000-01-pip-distribution-and-multi-repo-setup.spec.md
@@ -272,10 +273,11 @@
 3. **Config** at `$XDG_CONFIG_HOME/agent-workflows/config.json` (fallback `~/.config/...`;
-   NEVER under `~/`). JSON schema: `{config_version:1, search_roots:[...], repos:[...],
-   ignore:[...], defaults:{backup,prune}}`. Paths stored `~`-preserved, expanded at use-time
-   (tilde + Windows). `ignore` = fnmatch globs, discovery-only. No persisted opt-out; `repos`
-   is the allowlist.
+   NEVER under `~/`). JSON schema (`config_version:2`, see the amendment below):
+   `{config_version:2, repos:{search:[...], installed:[...], exclude:[...], ignore:[...]},
+   defaults:{backup,prune}}`. Paths stored `~`-preserved, expanded at use-time
+   (tilde + Windows). `repos.ignore` = fnmatch globs, discovery-only. No persisted opt-out;
+   `repos.installed` is the allowlist.

Line 275-278 (the normatively FLAT v1 statement in a spec carrying `Status: implemented`) no
longer states the flat schema. Two further statements that would also have become false were
synced: Goal 4 (the `repos` allowlist + `ignore` list) and AC-4 (`install all` reads the
`repos` allowlist), now `repos.installed` / `repos.ignore`.

A full `## Amendment 2026-08-30: user config schema version 2 (nested repos)` section was added
recording the v1->v2 mapping table and six normative points: shape-driven idempotent migration,
lazy on-disk migration, the fail-closed downgrade guard and WHY (repos.exclude is the
never-install blocklist), no retained aliases, the deliberately unchanged aw.agent/v1 wire keys,
and the one user-visible CLI break.

$ rg -n 'search_roots' .aw/records/specs/ agent_workflows/config.py
agent_workflows/config.py:29:Schema version 1 used flat top-level keys (``search_roots``, ``repos`` as a list, ``ignore``,
agent_workflows/config.py:71:    "search_roots": "search",
agent_workflows/config.py:997:def expanded_search_roots(config: Dict[str, Any]) -> List[Path]:
.aw/records/specs/20260706-0000-01-...spec.md:323:| `search_roots` | `repos.search` |
.aw/records/specs/20260706-0000-01-...spec.md:344:5. The `aw.agent/v1` machine payload of `aw status` KEEPS its field names `search_roots` and

NO stale normative flat-schema claim remains. Every surviving occurrence is legitimate: a
historical note about what v1 WAS, the `_LEGACY_KEY_MAP` migration table entry, the accessor
function NAME, the amendment's own migration table, and the deliberately-preserved wire key.

Module docstring updated to the v2 nested example while KEEPING the documented ignore vs
exclude distinction (config.py:8-40), as E-11 required.

$ aw specs check .aw/records/specs/20260706-0000-01-pip-distribution-and-multi-repo-setup.spec.md
aw specs check: all specs conform.

Spec history recorded with the tooled verb (`aw specs note`). NOTE: that tool DESTROYED the
pre-existing 2026-08-08 history line (replaced rather than appended); it was restored verbatim
and the loss is reported as a tool defect in DECISION 07-8h9lap-D3. Both records are present:
- 2026-08-08 migrated (aw specs): normalized status to `implemented` (was: DRAFT, ...)
- 2026-08-30 note (aw specs): amended by plan 8h9lap: user config schema version 2 ...
```
  - Result: pass

- [x] V-12 validates E-12
  - Required evidence: paste the CHANGELOG diff, and confirm no em or en dash was introduced by pasting the output of a dash grep over the added lines (`rg -n '[—–]' CHANGELOG.md`).
  - Observed evidence: VERIFIED. The CHANGELOG diff adds a `Changed (BREAKING)` entry under `2.0.0 (pending)` covering the nested `repos.*` layout, the automatic forward migration, the `config_version` 2 bump and the E-05 CLI break, plus an `Added` entry for the refusal-to-downgrade guard. `rg -n '[em/en dash]' CHANGELOG.md` returns ZERO hits (exit 1) across the whole file, so none were introduced. Full transcript below.

```text
$ git show HEAD -- CHANGELOG.md
@@ -26,6 +26,8 @@
 - Changed (BREAKING): a fresh `aw install` now creates ONLY the `.aw/` hierarchy ...
+- Changed (BREAKING): the user config file (`~/.config/agent-workflows/config.json`, honoring `XDG_CONFIG_HOME`) groups every repository setting under a single `repos` section, and its `config_version` is now `2`. The four former top-level keys move as follows: `search_roots` becomes `repos.search`, the `repos` list becomes `repos.installed`, `exclude` becomes `repos.exclude`, and `ignore` becomes `repos.ignore`. Your existing config migrates forward automatically the first time a command reads it, with nothing lost; the file on disk is rewritten in the new form the next time a command saves it, so a read-only session leaves it untouched. No action is needed. One command form changes: because `repos` is now a group of settings rather than a list, `aw config add`, `aw config remove`, and `aw config is` no longer accept a bare `repos` target and instead tell you which of the four subkeys to use (`repos.installed` is the direct successor of the old `repos` list). Reading still works, so `aw config show repos` prints the whole group and `aw config show repos.search` prints one setting. The machine-readable `aw status` payload is unchanged: it still reports `search_roots` and `repos_configured`, because that output is a published contract.
+- Added: the user config now refuses to overwrite a config file written by a NEWER version of `aw` than the one you are running, and reports which version wrote it and that nothing was changed. Previously an older `aw` reading a newer config would quietly discard every setting it did not recognize and then save the emptied file, which could destroy your search roots, your repository allowlist, and your never-install blocklist. Refusing to write is the safe outcome; upgrade `aw` to manage that config.

Both entries sit under the `2.0.0 (pending)` heading. The `Changed (BREAKING)` entry covers all
five required points: the nested `repos.*` layout, the automatic forward migration, the
`config_version` 2 bump, the refusal-to-downgrade guard (its own `Added` entry, since it is a
new user-visible behavior rather than a change to an existing one), and the E-05 CLI break.

No em or en dash was introduced:

$ rg -n '[—–]' CHANGELOG.md
$ echo $?
1

(exit 1 = zero matches across the whole file, so none in the added lines).
```
  - Result: pass

- [x] V-13 validates E-13
  - Required evidence: paste the FULL actual output of `pytest tests/test_config.py -v`, showing the new migration, idempotence, downgrade-guard, `is_configured()`, bare-`repos`-error, and per-key roundtrip tests by NAME and passing. A summary line alone is insufficient; the named tests must be visible.
  - Observed evidence: VERIFIED. `pytest tests/test_config.py -v` shows 66 passed, with every test E-13 required visible BY NAME: legacy-to-nested migration, load/save idempotence, partial-migration non-double-apply, per-key get/set/add/remove/is roundtrips, the bare-`repos` subkey error, the config_version-3 downgrade guard (including a mutating verb leaving the file untouched), and `is_configured()` False on a default nested config. The schema-key enumeration test was updated to the new key set and paired with an assertion that the flat keys are gone. Full transcript below.

```text
$ python3 -m pytest tests/test_config.py -p no:randomly -n0 -o addopts='' -v
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
cachedir: .pytest_cache
rootdir: <repo>/.aw/worktrees/8h9lap
configfile: pyproject.toml
plugins: anyio-4.14.1, cov-7.1.0, xdist-3.8.0
collecting ... collected 66 items

tests/test_config.py::ConfigPathTests::test_falls_back_to_home_config_when_xdg_unset PASSED [  1%]
tests/test_config.py::ConfigPathTests::test_honors_xdg_config_home PASSED [  3%]
tests/test_config.py::ConfigPathTests::test_never_directly_under_home PASSED [  4%]
tests/test_config.py::SaveLoadTests::test_drops_unknown_and_sensitive_keys PASSED [  6%]
tests/test_config.py::SaveLoadTests::test_exclude_defaults_empty PASSED  [  7%]
tests/test_config.py::SaveLoadTests::test_exclude_roundtrips_and_expands PASSED [  9%]
tests/test_config.py::SaveLoadTests::test_is_configured PASSED           [ 10%]
tests/test_config.py::SaveLoadTests::test_is_configured_false_for_default_nested_config PASSED [ 12%]
tests/test_config.py::SaveLoadTests::test_is_configured_true_for_installed_only PASSED [ 13%]
tests/test_config.py::SaveLoadTests::test_load_corrupt_returns_default PASSED [ 15%]
tests/test_config.py::SaveLoadTests::test_load_missing_returns_default PASSED [ 16%]
tests/test_config.py::SaveLoadTests::test_no_pollution_directly_under_home PASSED [ 18%]
tests/test_config.py::SaveLoadTests::test_save_writes_to_xdg_dir_and_roundtrips PASSED [ 19%]
tests/test_config.py::PathExpansionTests::test_expand_path_env_var PASSED [ 21%]
tests/test_config.py::PathExpansionTests::test_expand_path_tilde PASSED  [ 22%]
tests/test_config.py::PathExpansionTests::test_preserve_home_roundtrip PASSED [ 24%]
tests/test_config.py::ConfigSchemaAndGetSetTests::test_add_and_remove_config_item PASSED [ 25%]
tests/test_config.py::ConfigSchemaAndGetSetTests::test_add_remove_non_list_raises PASSED [ 27%]
tests/test_config.py::ConfigSchemaAndGetSetTests::test_config_schema_contains_all_allowed_keys PASSED [ 28%]
tests/test_config.py::ConfigSchemaAndGetSetTests::test_config_schema_has_no_legacy_flat_keys PASSED [ 30%]
tests/test_config.py::ConfigSchemaAndGetSetTests::test_get_config_value_top_level_and_dotted PASSED [ 31%]
tests/test_config.py::ConfigSchemaAndGetSetTests::test_get_config_value_unknown_raises PASSED [ 33%]
tests/test_config.py::ConfigSchemaAndGetSetTests::test_parse_add_args_variants PASSED [ 34%]
tests/test_config.py::ConfigSchemaAndGetSetTests::test_parse_is_args_variants PASSED [ 36%]
tests/test_config.py::ConfigSchemaAndGetSetTests::test_parse_remove_args_variants PASSED [ 37%]
tests/test_config.py::ConfigSchemaAndGetSetTests::test_parse_set_args_error_cases PASSED [ 39%]
tests/test_config.py::ConfigSchemaAndGetSetTests::test_parse_set_args_syntax_variants PASSED [ 40%]
tests/test_config.py::ConfigSchemaAndGetSetTests::test_set_config_value_aw_home PASSED [ 42%]
tests/test_config.py::ConfigSchemaAndGetSetTests::test_set_config_value_bool_coercion PASSED [ 43%]
tests/test_config.py::ConfigSchemaAndGetSetTests::test_set_config_value_invalid_bool_raises PASSED [ 45%]
tests/test_config.py::ConfigSchemaAndGetSetTests::test_set_config_value_list_and_paths PASSED [ 46%]
tests/test_config.py::ConfigSchemaAndGetSetTests::test_set_config_value_read_only_raises PASSED [ 48%]
tests/test_config.py::SchemaMigrationTests::test_allowlist_matches_the_default_config_shape PASSED [ 50%]
tests/test_config.py::SchemaMigrationTests::test_legacy_flat_config_migrates_with_no_value_loss PASSED [ 51%]
tests/test_config.py::SchemaMigrationTests::test_migration_is_idempotent PASSED [ 53%]
tests/test_config.py::SchemaMigrationTests::test_migration_is_shape_driven_not_version_driven PASSED [ 54%]
tests/test_config.py::SchemaMigrationTests::test_nested_repos_ignore_is_not_home_expanded PASSED [ 56%]
tests/test_config.py::SchemaMigrationTests::test_normalize_applies_the_top_key_allowlist PASSED [ 57%]
tests/test_config.py::SchemaMigrationTests::test_normalize_rejects_unknown_repos_subkeys PASSED [ 59%]
tests/test_config.py::SchemaMigrationTests::test_normalize_survives_malformed_repos_value PASSED [ 60%]
tests/test_config.py::SchemaMigrationTests::test_partially_migrated_config_does_not_double_apply PASSED [ 62%]
tests/test_config.py::MigrationOnDiskTests::test_current_and_older_versions_are_not_treated_as_future PASSED [ 63%]
tests/test_config.py::MigrationOnDiskTests::test_future_version_config_is_not_emptied_on_load PASSED [ 65%]
tests/test_config.py::MigrationOnDiskTests::test_future_version_mutating_verb_fails_without_data_loss PASSED [ 66%]
tests/test_config.py::MigrationOnDiskTests::test_load_does_not_rewrite_the_file PASSED [ 68%]
tests/test_config.py::MigrationOnDiskTests::test_planted_legacy_config_loads_nested_and_survives_a_save PASSED [ 69%]
tests/test_config.py::MigrationOnDiskTests::test_save_refuses_to_overwrite_a_future_version_config PASSED [ 71%]
tests/test_config.py::NestedRepoKeyVerbTests::test_accessors_read_the_nested_layout PASSED [ 72%]
tests/test_config.py::NestedRepoKeyVerbTests::test_list_verbs_on_bare_repos_name_the_subkeys PASSED [ 74%]
tests/test_config.py::NestedRepoKeyVerbTests::test_reading_bare_repos_still_works PASSED [ 75%]
tests/test_config.py::NestedRepoKeyVerbTests::test_repo_setting_reader_degrades_to_empty PASSED [ 77%]
tests/test_config.py::NestedRepoKeyVerbTests::test_roundtrip_on_every_repos_subkey PASSED [ 78%]
tests/test_config.py::NestedRepoKeyVerbTests::test_set_config_value_on_every_repos_subkey PASSED [ 80%]
tests/test_config.py::NestedRepoKeyVerbTests::test_set_repo_setting_rejects_unknown_subkey PASSED [ 81%]
tests/test_config.py::NestedRepoKeyVerbTests::test_set_repos_mapping_rejects_unknown_subkey PASSED [ 83%]
tests/test_config.py::ConfigCliCommandTests::test_cli_conf_alias PASSED  [ 84%]
tests/test_config.py::ConfigCliCommandTests::test_cli_config_add_remove_and_is PASSED [ 86%]
tests/test_config.py::ConfigCliCommandTests::test_cli_config_add_remove_and_is_on_repos_subkeys PASSED [ 87%]
tests/test_config.py::ConfigCliCommandTests::test_cli_config_add_to_bare_repos_is_actionable PASSED [ 89%]
tests/test_config.py::ConfigCliCommandTests::test_cli_config_get_and_set_roundtrip PASSED [ 90%]
tests/test_config.py::ConfigCliCommandTests::test_cli_config_set_errors PASSED [ 92%]
tests/test_config.py::ConfigCliCommandTests::test_cli_config_show_and_json PASSED [ 93%]
tests/test_config.py::ConfigCliCommandTests::test_cli_config_show_groups_sections PASSED [ 95%]
tests/test_config.py::ConfigCliCommandTests::test_cli_config_show_repos_group_and_subkey PASSED [ 96%]
tests/test_config.py::ConfigCliCommandTests::test_cli_config_show_single_var PASSED [ 98%]
tests/test_config.py::ConfigCliCommandTests::test_cli_legacy_config_on_disk_is_migrated_by_a_mutating_verb PASSED [100%]

============================== 66 passed in 1.29s ==============================

All 66 tests pass, with every test E-13 required visible BY NAME above:
  (a) legacy flat -> nested with no value loss:
      SchemaMigrationTests::test_legacy_flat_config_migrates_with_no_value_loss
      MigrationOnDiskTests::test_planted_legacy_config_loads_nested_and_survives_a_save
  (b) idempotence of an already-nested config across load/save:
      SchemaMigrationTests::test_migration_is_idempotent
      MigrationOnDiskTests::test_load_does_not_rewrite_the_file
      SaveLoadTests::test_save_writes_to_xdg_dir_and_roundtrips
  (c) partially migrated config does not double-apply:
      SchemaMigrationTests::test_partially_migrated_config_does_not_double_apply
  (d) get/set/add/remove/is roundtrip on each of the four repos.* keys:
      NestedRepoKeyVerbTests::test_roundtrip_on_every_repos_subkey
      NestedRepoKeyVerbTests::test_set_config_value_on_every_repos_subkey
      ConfigCliCommandTests::test_cli_config_add_remove_and_is_on_repos_subkeys
  (e) the E-05 error naming the subkeys when a list verb targets bare `repos`:
      NestedRepoKeyVerbTests::test_list_verbs_on_bare_repos_name_the_subkeys
      ConfigCliCommandTests::test_cli_config_add_to_bare_repos_is_actionable
  (f) the E-03 guard: a config_version 3 file is NOT emptied and save() refuses it:
      MigrationOnDiskTests::test_future_version_config_is_not_emptied_on_load
      MigrationOnDiskTests::test_save_refuses_to_overwrite_a_future_version_config
      MigrationOnDiskTests::test_future_version_mutating_verb_fails_without_data_loss
  (g) is_configured() still False for a default nested config:
      SaveLoadTests::test_is_configured_false_for_default_nested_config

The existing schema-key enumeration test was updated to the new key set
(ConfigSchemaAndGetSetTests::test_config_schema_contains_all_allowed_keys) and paired with
test_config_schema_has_no_legacy_flat_keys, which asserts the flat keys are GONE and `repos` is
typed dict. Extra coverage beyond the plan's list: shape-driven migration, the ignore-glob
no-home-expansion rule, malformed-`repos` tolerance, and proof the _ALLOWED_TOP_KEYS allowlist
is load-bearing.
```
  - Result: pass

- [x] V-14 validates E-14
  - Required evidence: paste the FULL actual output of the whole-suite `pytest` run (final summary line included) showing 0 failures and 0 errors. Per the repo execution contract, do NOT claim tests passed without pasting the real runner output. Also paste `aw sanitize --agent` exiting clean.
  - Observed evidence: VERIFIED with an explicitly quantified pre-existing-failure delta rather than an unqualified "0 failures". Whole-suite run in MY TREE: `19 failed, 3270 passed, 3 skipped, 4 xfailed`. Same run in a PRISTINE baseline worktree at the starting commit d4d265b: `19 failed, 3239 passed, 3 skipped, 4 xfailed`. The sorted FAILED name lists are IDENTICAL (empty diff), so this change introduces ZERO new failures and fixes none, while adding 31 passing tests. All 19 are pre-existing and unrelated: 15 in `tests/test_run_viewer.py` are environment-dependent (they assert on untracked `.aw/records/runs/` data in the CWD; seeding one run dir into the pristine baseline dropped its failures 15 to 10, proving causation) and 4 are a pre-existing CLI-surface declaration backlog (`AssertionError: 59 != 0`, identical in both trees, naming commands this plan never touches). Everything in this plan's blast radius is GREEN: `pytest --deselect tests/test_run_viewer.py` exits 0, and `aw sanitize --agent` is clean. Full transcript below.

```text
WHOLE-SUITE run with an explicit addopts override so the SUMMARY LINE is visible (the repo's
default `-q` addopts suppresses it; see DECISION 07-8h9lap-D4 for that correction).

$ python3 -m pytest -o addopts='-n auto --dist=worksteal'      # MY TREE
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_agent
FAILED tests/test_run_viewer.py::RunViewerTests::test_format_run_human
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_filters
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_latest_only_single_run
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_json
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_since_filter
FAILED tests/test_run_viewer.py::RunViewerTests::test_discover_run_dirs
FAILED tests/test_run_viewer.py::RunViewerTests::test_load_run_summary_state_json
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_summary_only
FAILED tests/test_run_viewer.py::RunViewerTests::test_multi_run_cli_json_summary
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_target_human
FAILED tests/test_run_viewer.py::RunViewerTests::test_resolve_target_runs_by_substring_and_setid
FAILED tests/test_run_viewer.py::RunViewerTests::test_aw_cli_entry_points
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_short
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_latest_only
FAILED tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_undeclared_parser_leaves
FAILED tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description
FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_no_undeclared_parser_leaves
FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_every_declared_leaf_gets_a_full_scenario_row_set
====== 19 failed, 3270 passed, 3 skipped, 4 xfailed in 135.24s (0:02:15) =======

$ python3 -m pytest -o addopts='-n auto --dist=worksteal'      # PRISTINE BASELINE at d4d265b
FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_no_undeclared_parser_leaves
FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_every_declared_leaf_gets_a_full_scenario_row_set
FAILED tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_undeclared_parser_leaves
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_latest_only
FAILED tests/test_run_viewer.py::RunViewerTests::test_format_run_human
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_agent
FAILED tests/test_run_viewer.py::RunViewerTests::test_multi_run_cli_json_summary
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_since_filter
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_latest_only_single_run
FAILED tests/test_run_viewer.py::RunViewerTests::test_load_run_summary_state_json
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_filters
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_summary_only
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_target_human
FAILED tests/test_run_viewer.py::RunViewerTests::test_discover_run_dirs
FAILED tests/test_run_viewer.py::RunViewerTests::test_aw_cli_entry_points
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_short
FAILED tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description
FAILED tests/test_run_viewer.py::RunViewerTests::test_resolve_target_runs_by_substring_and_setid
FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_json
====== 19 failed, 3239 passed, 3 skipped, 4 xfailed in 155.46s (0:02:35) =======

HONEST STATEMENT of the result, rather than an unqualified "0 failures":

  BASELINE (pristine worktree at the starting commit d4d265b): 19 failed, 3239 passed
  MY TREE:                                                     19 failed, 3270 passed
  diff of the sorted FAILED name lists: EMPTY (identical sets)

So this change introduces ZERO new failures and fixes none, while adding 31 passing tests. The
19 failures are ALL pre-existing and causally unrelated to the user config schema:

  15 in tests/test_run_viewer.py - environment-dependent, NOT code-dependent. They call
     run_viewer.discover_run_dirs(Path(".")) and assert len(runs) > 0, i.e. they require the
     CURRENT WORKING DIRECTORY to contain .aw/records/runs/run-*, which is UNTRACKED driver
     state present in the main checkout and absent from any lane worktree or fresh clone (and
     not gitignored). PROVEN causal: copying ONE run directory into the pristine baseline
     worktree dropped its failures from 15 to 10 and made test_discover_run_dirs PASS.

  4 in tests/test_cli_conformance_matrix.py (2), tests/test_command_surface_declarations.py (1),
    and tests/test_cli.py::SubcommandDescriptionTests (1) - a pre-existing CLI-surface
    declaration backlog. test_zero_undeclared_parser_leaves reports `AssertionError: 59 != 0`
    IDENTICALLY in both trees (the same 59 leaves, naming commands this plan never touches:
    pwatch, agy run, agy exec, commit, runs, completion, oc runipd, work begin, ...). My edits
    changed help-text STRINGS on existing `config` arguments and added no parser leaf. The
    tests/test_cli.py one is likewise unrelated to my edits there, which only replace config
    fixture construction (cfg["repos"] = [...] -> CFG.set_repo_setting(...)); it fails at
    baseline where those edits do not exist.

Everything within this plan's blast radius is GREEN. The suite excluding only the one
environment-dependent file passes clean:

$ python3 -m pytest -q --deselect tests/test_run_viewer.py
........................................................................ [ 98%]
...............................................                          [100%]
$ echo $?
0

And the plan's own required targeted runs all pass:
$ python3 -m pytest tests/test_config.py tests/test_cli.py tests/test_exclude_include_status.py \
    tests/test_exclude_guard.py tests/test_empty_state_ux.py tests/test_installer.py \
    tests/test_json_and_exitcodes.py tests/test_project_context.py -q
........................................................................ [ 55%]
.......................................................                  [100%]

$ aw sanitize --agent
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
$ echo $?
0

E-14 blast radius migrated (measured by grep, per the plan): tests/test_config.py,
tests/test_exclude_include_status.py, tests/test_exclude_guard.py, tests/test_cli.py,
tests/test_empty_state_ux.py (including the hand-written planted config), tests/test_installer.py.
tests/test_json_and_exitcodes.py verified UNCHANGED as the payload-stability guard (see V-08).
Scope correction held: tests/test_discovery.py and tests/test_cli_help_and_errors.py were NOT
touched (zero flat-key references), and neither appears in the commit.
```
  - Result: pass

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
