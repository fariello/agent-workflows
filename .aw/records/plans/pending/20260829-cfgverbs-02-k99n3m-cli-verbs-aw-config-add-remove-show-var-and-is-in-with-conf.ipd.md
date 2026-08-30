# IPD: CLI verbs aw config add remove show var and is in with conf alias

- Date: 2026-08-29
- Kind: child
- Concern: Provide array mutation and inspection verbs (add, remove, is in), single-variable show, and conf alias for aw config.
- Scope: Array helpers in config.py, CLI subcommands add/remove/show/is in cli.py, "conf" alias in parser, and comprehensive tests.
- Scope-Paths: agent_workflows/config.py, agent_workflows/cli.py, tests/test_config.py
- Item-Dependencies: none
- Status: approved
- Set: cfgverbs
- Order: 2
- Highest E allocated: 03
- Author: antigravity
- Id: k99n3m
- Approval: 2026-08-30, human ("approved"): User requested add, remove, is in, show var, and conf alias

## Workflow history
- 2026-08-30 approved (aw set, --by-human): User requested add, remove, is in, show var, and conf alias
- 2026-08-30 reviewed (aw set): plan authored

- 2026-08-29 draft (antigravity): created.
- 2026-08-29 to-review (antigravity): authored complete plan.

## Goal

Provide array manipulation verbs (`aw config add <value> to <varname>`, `aw config remove <value> from <varname>`), array membership check (`aw config is <value> in <varname>`), single-variable inspection (`aw config show <varname>`), and the top-level command alias `aw conf`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Array Helpers in `agent_workflows/config.py`

- [x] E-01 Implement `parse_add_args`, `parse_remove_args`, `parse_is_args`, `add_config_item`, `remove_config_item`, and `is_config_item_present` in `agent_workflows/config.py`.
  - Depends on: none
  - Expected outcome: Functions validate that target variables are list-typed in `CONFIG_SCHEMA`, handle path normalization and home-preservation, perform idempotency checks, and atomically save updates.
  - Execution state: performed

### Task group 2: CLI Subcommands and `conf` Alias in `agent_workflows/cli.py`

- [x] E-02 Wire `add`, `remove` (alias `rm`), `is`, update `show [varname]`, and add `conf` alias to `p_config` in `agent_workflows/cli.py`.
  - Depends on: E-01
  - Expected outcome: `aw config add <val> to <var>`, `aw config remove <val> from <var>`, `aw config is <val> in <var>`, `aw config show <var>`, and `aw conf ...` invocations work across all syntax forms with clear status and exit codes (0 for present/success, 1 for not-found, 2 for usage errors).
  - Execution state: performed

### Task group 3: Comprehensive Tests in `tests/test_config.py`

- [x] E-03 Add unit test coverage for array helpers, CLI array subcommands, single variable show, and the `conf` alias.
  - Depends on: E-02
  - Expected outcome: All tests pass with full assertion coverage over syntax variants, non-list error handling, path comparisons, and exit codes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Single source of truth for config is `agent_workflows/config.py`.
- Array fields in config (`search_roots`, `repos`, `exclude`, `ignore`) store strings or `~`-preserved paths.
- Aliases are specified via `aliases=["conf"]` in `sub.add_parser("config", ...)` and handled in dispatch.
- Output formatting respects `--no-color`, `NO_COLOR`, `--agent`, and `--json`.

## Findings

- Previous implementation added get, set, and global show.
- Users needed intuitive array manipulation (`add <val> to <var>`, `remove <val> from <var>`, `is <val> in <var>`), targeted `show <var>`, and the `conf` alias shorthand.

## Proposed changes (ordered, validatable)

1. **`agent_workflows/config.py`**:
   - `parse_add_args(tokens: Sequence[str]) -> Tuple[str, str]` (handles `val to var`, `val var`, `var val`).
   - `parse_remove_args(tokens: Sequence[str]) -> Tuple[str, str]` (handles `val from var`, `val var`, `var val`).
   - `parse_is_args(tokens: Sequence[str]) -> Tuple[str, str]` (handles `val in var`, `val var`).
   - `add_config_item(varname: str, item_raw: str, cfg: dict | None = None, auto_save: bool = True) -> Tuple[dict, str, list, bool]`.
   - `remove_config_item(varname: str, item_raw: str, cfg: dict | None = None, auto_save: bool = True) -> Tuple[dict, str, list, bool]`.
   - `is_config_item_present(varname: str, item_raw: str, cfg: dict | None = None) -> Tuple[str, bool]`.

2. **`agent_workflows/cli.py`**:
   - Add `aliases=["conf"]` to `p_config`.
   - Update `p_config_show` with optional `varname` argument.
   - Add `add`, `remove` (aliases `rm`), and `is` subparsers under `config_sub`.
   - Implement `_run_config_add`, `_run_config_remove`, `_run_config_is`, and update `_run_config_show`.
   - Update dispatch for `command in ("config", "conf")`.

3. **`tests/test_config.py`**:
   - Unit tests covering `add_config_item`, `remove_config_item`, `is_config_item_present`, flexible argument parsing, CLI commands `add`, `remove`, `show <varname>`, `is in`, and `aw conf` alias.

## Deferred / out of scope (with reason)

- Modifying per-repo project settings (handled by `aw project`).

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `pytest tests/test_config.py -v`
- Full test suite `pytest`
- `aw sanitize --agent`
- CLI verification commands:
  - `aw config add ~/src to search_roots`
  - `aw config is ~/src in search_roots`
  - `aw config remove ~/src from search_roots`
  - `aw config show search_roots`
  - `aw conf show`

## Spec / documentation sync

- Docstrings in `config.py` and help epilog in `cli.py` updated with array verb examples.

## Open questions

### OQ-01: How to match paths when removing or checking presence

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Compare both normalized `~`-preserved string representation and resolved `Path.resolve()` equality to match regardless of whether the user supplies `~/src` or `/home/user/src`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Python unit tests for `add_config_item`, `remove_config_item`, and `is_config_item_present` pass cleanly.
  - Observed evidence: `pytest tests/test_config.py` runs all helper and argument parsing tests with 35 passed.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: CLI commands `aw config add`, `aw config remove`, `aw config is ... in ...`, `aw config show <var>`, and `aw conf show` execute cleanly.
  - Observed evidence: Invocations of `aw conf show`, `aw conf show search_roots`, `aw conf add ~/testing-dir to search_roots`, `aw conf is ~/testing-dir in search_roots`, `aw conf rm ~/testing-dir from search_roots`, and `aw conf is ~/testing-dir in search_roots` completed with expected 0 and 1 exit codes and clean output.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: `pytest tests/test_config.py` passes all tests cleanly with 0 failures.
  - Observed evidence: `pytest tests/test_config.py -v` reported 35 passed in 2.70s.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

All work is bounded to config schema and CLI verbs with path-scoped changes and deterministic test verification.
