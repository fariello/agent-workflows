# IPD: CLI verbs aw config get set and show with typed schema registry

- Date: 2026-08-29
- Kind: child
- Concern: Provide direct CLI inspection and mutation of user configuration via get, set, and show verbs backed by a typed schema registry.
- Scope: In-process config schema registry in config.py, CLI subcommands get/set/show in cli.py, and comprehensive tests.
- Scope-Paths: agent_workflows/config.py, agent_workflows/cli.py, tests/test_config.py, tests/test_cli_help_and_errors.py
- Item-Dependencies: none
- Status: executed
- Set: cfgverbs
- Order: 1
- Highest E allocated: 03
- Author: antigravity
- Id: 75ov5j

## Workflow history
- 2026-08-30 executed (antigravity): Implement aw config get, set, and show with typed schema registry [Scope reconciliation - in-scope-unmodified agent_workflows/cli.py: acknowledged; in-scope-unmodified agent_workflows/config.py: acknowledged; in-scope-unmodified tests/test_cli_help_and_errors.py: acknowledged; in-scope-unmodified tests/test_config.py: acknowledged]
- 2026-08-30 approved (aw set, --by-human): User requested get/set/show config verbs backed by schema registry
- 2026-08-30 reviewed (aw set): plan authored
- 2026-08-30 approved (aw set, --by-human): User requested get/set/show config verbs backed by schema registry

- 2026-08-29 draft (antigravity): created.
- 2026-08-29 to-review (antigravity): authored complete plan with typed schema registry and CLI subcommands.

## Goal

Provide `aw config get <varname>`, `aw config set <varname> [to|=| = ] <value>`, and `aw config show` CLI verbs powered by a typed schema registry in `agent_workflows/config.py` that validates types, normalizes paths and booleans, preserves `~` portable path formatting, and atomically saves `config.json`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Typed Schema Registry in `agent_workflows/config.py`

- [x] E-01 Define `CONFIG_SCHEMA` registry with typed entry definitions and implement `get_config_value(key, ...)` and `set_config_value(key, value_str, ...)` in `agent_workflows/config.py`.
  - Depends on: none
  - Expected outcome: `CONFIG_SCHEMA` declares valid keys, types (`list[path]`, `list[str]`, `bool`, `path`, `int`), descriptions, and parsers; `get_config_value` resolves top-level and dotted keys (e.g. `defaults.backup`); `set_config_value` validates and coerces values, updates the configuration mapping, and atomically saves it.
  - Execution state: performed

### Task group 2: CLI Subcommands `get`, `set`, and `show` in `agent_workflows/cli.py`

- [x] E-02 Wire `aw config get`, `aw config set`, and `aw config show` subcommands under `p_config` in `agent_workflows/cli.py`.
  - Depends on: E-01
  - Expected outcome: `aw config show` displays the config file path, file presence, and settings table; `aw config get <key>` outputs the value; `aw config set <key> [to|=| = ] <val>` parses flexible assignment syntax, validates against schema, writes atomically, and prints confirmation.
  - Execution state: performed

### Task group 3: Comprehensive Unit Tests in `tests/test_config.py`

- [x] E-03 Add unit test coverage for schema validation, `get_config_value`, `set_config_value`, and CLI invocations for `show`, `get`, and `set`.
  - Depends on: E-02
  - Expected outcome: All tests pass with 100% assertion coverage over valid/invalid keys, syntax variants (`=`, `to`, space), path preservation, and error handling.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Single source of truth for config is `agent_workflows/config.py`.
- Paths stored in config are `~`-preserved and normalized to `/` separators for cross-OS portability.
- Writes to `config.json` use atomic tempfile + `os.replace`.
- No sensitive tokens/secrets allowed in `config.json`.
- Output formatting respects `--no-color`, `NO_COLOR`, `--agent`, and `--json`.

## Findings

- `aw config` previously only exposed `exclude (list|add|rm)` subcommands.
- Users had no direct way to inspect or adjust settings (like `defaults.backup`, `search_roots`, or `aw_home`) without running full `aw setup` or manually editing JSON.

## Proposed changes (ordered, validatable)

1. **`agent_workflows/config.py`**:
   - Define `ConfigKeySpec` dataclass and `CONFIG_SCHEMA: dict[str, ConfigKeySpec]`.
   - Implement `get_config_value(key: str, cfg: dict | None = None) -> tuple[str, Any]` (returns canonical key name and value).
   - Implement `set_config_value(key: str, value_raw: Any, cfg: dict | None = None) -> tuple[dict, str, Any]` (returns updated dict, canonical key, and parsed value).
   - Support dot notation (`defaults.backup`, `defaults.prune`).
   - Support value parsing for booleans (`true`/`false`/`1`/`0`/`yes`/`no`), lists (comma-separated or JSON list syntax), and paths (`~` preservation).

2. **`agent_workflows/cli.py`**:
   - Add `show`, `get`, `set` subcommands under `config` subparser.
   - Parser for `set` accepts tokens representing `<varname> [to|=| = ] <value>`.
   - Dispatch to `_run_config_show`, `_run_config_get`, and `_run_config_set`.
   - Support `--json` and `--agent` structured reporting.

3. **`tests/test_config.py`**:
   - Unit tests covering `get_config_value`, `set_config_value`, type validations, invalid key errors, flexible CLI syntax handling, and `aw config show` outputs.

## Deferred / out of scope (with reason)

- Modifying per-repository `.aw/config/` local overrides (out of scope; this plan targets the user-level global CLI config `$XDG_CONFIG_HOME/agent-workflows/config.json`).

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `pytest tests/test_config.py -v`
- Full test suite `pytest`
- `aw sanitize --agent`
- Manual CLI invocation checks: `aw config show`, `aw config get defaults.backup`, `aw config set defaults.backup to true`, etc.

## Spec / documentation sync

- `agent_workflows/config.py` module docstring updated to reflect schema and helper utilities.
- CLI help strings in `agent_workflows/cli.py` updated with syntax examples.

## Open questions

### OQ-01: How to handle assignment syntax with "=" or "to" when passed across shell tokens

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: In CLI parsing, collect all argument tokens for `set` and join/split intelligently to seamlessly handle `aw config set foo=bar`, `aw config set foo = bar`, `aw config set foo to bar`, and `aw config set foo bar`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: `python3 -c "from agent_workflows import config; print(config.get_config_value('defaults.backup'))"` runs without error and returns key and bool value.
  - Observed evidence: `('defaults.backup', True)` returned cleanly.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `python3 -m agent_workflows.cli config show`, `python3 -m agent_workflows.cli config get defaults.backup`, and `python3 -m agent_workflows.cli config set defaults.backup to true` execute cleanly and output expected statuses.
  - Observed evidence: `aw config show` displayed settings table and file location; `aw config get` returned `true`; `aw config set defaults.backup to true` returned `OK defaults.backup = True (saved to ~/.config/agent-workflows/config.json)`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: `pytest tests/test_config.py` passes all tests cleanly with 0 failures.
  - Observed evidence: `============================== 27 passed in 2.56s ==============================`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

All work is bounded to config schema and CLI verbs with path-scoped changes and deterministic test verification.
