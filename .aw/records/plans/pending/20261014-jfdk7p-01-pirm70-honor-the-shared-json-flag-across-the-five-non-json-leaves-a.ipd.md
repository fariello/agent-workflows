# IPD: Honor the shared --json flag across the five non-JSON leaves and their sibling branches

- Date: 2026-10-14
- Kind: child
- Concern: Five leaves advertising the shared `--json` flag (`config get`, `config is`, `upgrade-test env`, `upgrade-test probe`, and `upgrade-test clean`) fail to emit parseable JSON on stdout along their error or dry-run/valid-sandbox branches, requiring five `("...", "--json"): "jfdk7p"` entries in `tests/test_shared_flag_honored.KNOWN_BROKEN`.
- Scope: Teach `agent_workflows/cli._emit_config_agent_error`, the `upgrade-test` `HarnessError` handlers in `agent_workflows/cli._dispatch` and `agent_workflows/upgrade_rehearsal.main`, `agent_workflows/upgrade_rehearsal.cmd_env`, and `agent_workflows/upgrade_rehearsal.cmd_clean` to emit parseable, home-path-redacted JSON on stdout whenever `--json` is passed, remove the five `(leaf, "--json"): "jfdk7p"` entries from `tests/test_shared_flag_honored.KNOWN_BROKEN`, and add branch-level behavioral regression coverage in `tests/test_shared_flag_honored.py`.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/upgrade_rehearsal.py, tests/test_shared_flag_honored.py, .aw/records/plans/pending/20261014-jfdk7p-01-pirm70-honor-the-shared-json-flag-across-the-five-non-json-leaves-a.ipd.md
- Item-Dependencies: none
- Status: to-review
- From-Backlog: jfdk7p
- Blocks-Release: next
- Work-Kind: bug
- Priority: medium
- Set: jfdk7p
- Order: 1
- Highest E allocated: 04
- Author: agy/gemini-4-argon-high
- Id: pirm70

## Workflow history
- 2026-10-14 to-review (agy/gemini-4-argon-high): Authored review-ready child IPD from backlog item jfdk7p

- 2026-10-14 draft (agy/gemini-4-argon-high): created.

## Goal

Ensure every leaf advertising the shared `--json` flag emits parseable, home-path-redacted JSON on stdout across all return and refusal branches of `config` (`get`, `is`, and sibling `ConfigError`/refusal callers of `_emit_config_agent_error`) and `upgrade-test` (`env`, `probe`, `clean`, and `HarnessError` exit-2 handlers), retiring all five `("...", "--json"): "jfdk7p"` entries from `tests/test_shared_flag_honored.KNOWN_BROKEN`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-derive baseline at execution HEAD

- [ ] E-01 Re-derive at execution HEAD the stdout/stderr/returncode behavior of the five `jfdk7p` leaves (`config get`, `config is`, `upgrade-test env`, `upgrade-test probe`, `upgrade-test clean`) under `--json` and verify the target code sites in `agent_workflows/cli.py`, `agent_workflows/upgrade_rehearsal.py`, and `tests/test_shared_flag_honored.py` against Findings F-01 through F-05.
  - Depends on: none
  - Expected outcome: A reproduction snippet calling `tests.conformance_matrix.run_cli` with `["--json"]` across the five `jfdk7p` leaves and a targeted `python3 -m pytest tests/test_shared_flag_honored.py -k "json"` run confirm the baseline `KNOWN_BROKEN` failure signatures and verify whether sibling plans (`83ns86` / `aws1tg` or `4y614a`) have already modified `agent_workflows/upgrade_rehearsal.py` or `tests/test_shared_flag_honored.KNOWN_BROKEN`.
  - Execution state: pending

### Task group 2: Honor `--json` on `config` error/refusal paths and across `upgrade-test`

- [ ] E-02 Teach `agent_workflows/cli._emit_config_agent_error` to emit a parseable, home-path-redacted JSON error object on stdout and return `2` when `--json` (`getattr(args, "json", False)` or `getattr(args, "as_json", False)`) is active and `--agent` is not.
  - Depends on: E-01
  - Expected outcome: In `agent_workflows/cli._emit_config_agent_error`, after the `if getattr(args, "agent", False):` branch and before the human `term.status("fail", msg)` fallback, when `getattr(args, "json", False) or getattr(args, "as_json", False)` is truthy, `msg` is sanitized via `agent_schema.redact_home_paths(_sanitize_config_agent_error_message(msg))` and `json.dumps({"command": cmd, "error": clean_msg, "exit_code": 2}, indent=2, sort_keys=True)` is printed to stdout with return code `2`, so `config get --json`, `config is --json`, and every other `config` subcommand routing exit-2 errors through `_emit_config_agent_error` (`show`, `set`, `unset`, `add`, `remove`) emit parseable, leak-clean JSON on stdout.
  - Execution state: pending

- [ ] E-03 Teach `agent_workflows/upgrade_rehearsal.py` and `agent_workflows/cli.py` to honor `--json` in the `HarnessError` exit-2 handlers (`upgrade_rehearsal.main` and `cli._dispatch`), in `upgrade_rehearsal.cmd_env` on a valid sandbox, and in `upgrade_rehearsal.cmd_clean` on both the empty-targets (`if not targets:`) and preview-without-`-y` (`if not args.yes:`) branches.
  - Depends on: E-01
  - Expected outcome: (1) A shared helper `upgrade_rehearsal._emit_json_error(command: str, message: str, *, exit_code: int = 2) -> int` prints `json.dumps({"command": f"upgrade-test {command}".strip(), "error": agent_schema.redact_home_paths(message), "exit_code": exit_code}, indent=2)` to stdout and returns `exit_code`, and both `upgrade_rehearsal.main` (`except HarnessError as exc:`) and `cli._dispatch` (`if args.command == "upgrade-test":` `except upgrade_rehearsal.HarnessError as exc:`) call it when `getattr(args, "json", False)` is truthy and `getattr(args, "agent", False)` is false; (2) `upgrade_rehearsal.cmd_env` checks `if getattr(args, "json", False): print(json.dumps({"sandbox": str(sandbox), "env": env}, indent=2)); return 0` before the human `export` loop; and (3) `upgrade_rehearsal.cmd_clean` checks `if getattr(args, "json", False): print(json.dumps([], indent=2)); return 0` inside `if not targets:` and `if getattr(args, "json", False): print(json.dumps({"would_remove": [str(t) for t in targets]}, indent=2)); return 0` inside `if not args.yes:`.
  - Execution state: pending

### Task group 3: Retire `jfdk7p` from `KNOWN_BROKEN` and add branch-level behavioral tests

- [ ] E-04 Remove the five `(leaf, "--json"): "jfdk7p"` entries from `tests/test_shared_flag_honored.KNOWN_BROKEN`, add branch-level behavioral regression tests in `tests/test_shared_flag_honored.py` covering every repaired branch, verify mutation sensitivity on the live working tree with a restoring `try/finally` wrapper, and run the full `python3 -m pytest` suite.
  - Depends on: E-02, E-03
  - Expected outcome: The five `"jfdk7p"` entries are removed from `tests/test_shared_flag_honored.KNOWN_BROKEN` (and if `KNOWN_BROKEN` is completely empty at execution HEAD because `aws1tg` and `4y614a` have already landed, `test_known_broken_citations_resolve` allows an empty dict without failing `assert seen_citations`), new behavioral tests in `tests/test_shared_flag_honored.py` assert parseable JSON and home-path redaction across `config` exit-2 refusals, `upgrade-test env` and `probe` on both valid sandboxes and non-sandbox exit-2 paths (via CLI and standalone `upgrade_rehearsal.main`), and `upgrade-test clean` across empty, preview, and `-y` branches, the mutation proof fails with a reversion and passes after restoration with matching `sha256`, and bare `python3 -m pytest` passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Shared `--json` contract (`docs/cli-output-contract.md` Section 1 "Output Modes", Section 2 "Channel Discipline", Section 4 "Machine-Surface Path Sanitization"): every command advertising `--json` in `SHARED_COMMON_FLAGS` (`agent_workflows/conventions.py` `SHARED_COMMON_FLAGS = frozenset({"--no-color", "--color", "--no-interactive", "--interactive", "--agent", "--json", "--fields", "--verbose"})`) must emit parseable JSON on `stdout` (`json.loads(res.stdout)` succeeds) across both zero and non-zero exit paths, keep human chatter off `stdout`, and redact home-directory paths (`<home>`) in error/summary strings via `agent_workflows.agent_schema.redact_home_paths`.
- Behavioral gate for shared flags (`tests/test_shared_flag_honored.py`, introduced by IPD `cgsrnb`): `test_shared_flag_honored_readonly` and `test_shared_flag_honored_mutation` drive every leaf in `tests/conformance_matrix.LEAF_PATHS` through `run_cli(leaf, ["--json"], ...)` and assert `_assert_json_honored(leaf, res)` (`json.loads(res.stdout)`). Leaves in `KNOWN_BROKEN` are inverted (`pytest.fail` if they pass while still listed in `KNOWN_BROKEN`), so fixing any of the five `jfdk7p` leaves requires removing its `(leaf, "--json"): "jfdk7p"` entry from `KNOWN_BROKEN` in the same change.
- Sibling plan boundary (`.aw/records/plans/pending/20261014-aws1tg-01-83ns86-honor-the-shared-fields-projection-under-agent-across-the-ni.ipd.md`): pending IPD `83ns86` (`From-Backlog: aws1tg`) touches `agent_workflows/upgrade_rehearsal.py` and `tests/test_shared_flag_honored.py` to wire `--fields` under `--agent` and retire the nine `(leaf, "--fields"): "aws1tg"` entries in `KNOWN_BROKEN`. `83ns86` explicitly leaves the `--json` arms in `upgrade_rehearsal.py` and the five `(leaf, "--json"): "jfdk7p"` entries in `KNOWN_BROKEN` to `jfdk7p`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Run the test suite via bare `python3 -m pytest` (never pass `-n0`, extra `-q`, or `-p no:randomly`). Commit only via `aw commit`.

## Findings

| ID | Category | Severity | Location (`file:symbol`) | Description |
|---|---|---|---|---|
| F-01 | bug | high | `agent_workflows/cli.py:_emit_config_agent_error` | `_emit_config_agent_error(cmd, msg, term, args)` handles `if getattr(args, "agent", False):` and otherwise falls directly through to `term.status("fail", msg); return 2`, which writes `FAIL     ...` prose on `stdout`. It has no `getattr(args, "json", False) or getattr(args, "as_json", False)` branch. In `tests/conformance_matrix.RUNNABLE_ARGV`, `"config get": ["interactive"]` (unknown key) and `"config is": ["interactive"]` (missing `<varname>`) both hit `_emit_config_agent_error`, causing `config get --json` and `config is --json` (as well as exit-2 refusals on `config show`, `set`, `unset`, `add`, `remove` with `--json`) to emit non-JSON `FAIL` prose on stdout. |
| F-02 | bug | high | `agent_workflows/cli.py:_dispatch`, `agent_workflows/upgrade_rehearsal.py:main` | When an `upgrade-test` subcommand raises `HarnessError` (such as `cmd_env` and `cmd_probe` failing `if not (sandbox / MARKER_NAME).is_file(): raise HarnessError(f"not a sandbox (no {MARKER_NAME}): {sandbox}")` on `RUNNABLE_ARGV` `"upgrade-test env": ["dummy"]` and `"upgrade-test probe": ["dummy"]`), both `cli._dispatch` (`except upgrade_rehearsal.HarnessError as exc:`) and standalone `upgrade_rehearsal.main` (`except HarnessError as exc:`) check `if getattr(args, "agent", False):` and otherwise print `f"error: {exc}"` to `sys.stderr` with zero bytes on `stdout` and return `2`. Neither checks `getattr(args, "json", False)`. |
| F-03 | bug | medium | `agent_workflows/upgrade_rehearsal.py:cmd_env` | Even when `upgrade-test env <sandbox> --json` is invoked against a valid marked sandbox (where `(sandbox / MARKER_NAME).is_file()` succeeds), `cmd_env` only checks `if getattr(args, "agent", False):` and then unconditionally loops `for k, v in env.items(): print(f"export {k}={shlex.quote(v)}")`. Unlike `cmd_probe` (which has `if getattr(args, "json", False): print(json.dumps(state, indent=2)); return 0`), `cmd_env` has no `if getattr(args, "json", False):` branch at all. |
| F-04 | bug | high | `agent_workflows/upgrade_rehearsal.py:cmd_clean` | `cmd_clean` has three return paths, but only the third (after `clean(targets)` when `-y` is passed) checks `if getattr(args, "json", False): print(json.dumps(results, indent=2)); return 0`. The first branch (`if not targets:`, hit by `aw upgrade-test clean --json` when no sandboxes exist) checks `if getattr(args, "agent", False):` and then prints `"Nothing to clean."` on stdout; the second branch (`if not args.yes:`, hit when sandboxes exist and `-y` is omitted) checks `if getattr(args, "agent", False):` and then prints `"Would remove:\n..."` on stdout. |
| F-05 | test-gap | medium | `tests/test_shared_flag_honored.py:KNOWN_BROKEN` | `KNOWN_BROKEN` records five `"jfdk7p"` exceptions (`("config get", "--json")`, `("config is", "--json")`, `("upgrade-test env", "--json")`, `("upgrade-test probe", "--json")`, `("upgrade-test clean", "--json")`). In addition, `test_shared_flag_honored_readonly` only exercises `upgrade-test env` and `upgrade-test probe` with `"dummy"` (the `HarnessError` exit-2 path) and `test_shared_flag_honored_mutation` only exercises `upgrade-test clean` with an empty sandbox root (`if not targets:`), so dedicated branch-level tests are needed to guard `cmd_env --json` on a valid sandbox and `cmd_clean --json` on the non-empty preview (`not args.yes`) branch. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/cli.py` (`_emit_config_agent_error`, `_dispatch`)** (addresses F-01, F-02):
   - In `_emit_config_agent_error(cmd: str, msg: str, term: Terminal, args: object | None = None) -> int`, immediately after the `if getattr(args, "agent", False):` block, add a `--json` branch:
     ```python
     if getattr(args, "json", False) or getattr(args, "as_json", False):
         clean_msg = agent_schema.redact_home_paths(
             _sanitize_config_agent_error_message(msg)
         )
         print(
             json.dumps(
                 {"command": cmd, "error": clean_msg, "exit_code": 2},
                 indent=2,
                 sort_keys=True,
             )
         )
         return 2
     ```
   - In `_dispatch`, inside the `if args.command == "upgrade-test":` `except upgrade_rehearsal.HarnessError as exc:` handler, after the `if getattr(args, "agent", False):` check, add:
     ```python
     if getattr(args, "json", False):
         return upgrade_rehearsal._emit_json_error(sub, str(exc), exit_code=2)
     ```
2. **`agent_workflows/upgrade_rehearsal.py` (`_emit_json_error`, `cmd_env`, `cmd_clean`, `main`)** (addresses F-02, F-03, F-04):
   - Add helper `_emit_json_error(command: str, message: str, *, exit_code: int = 2) -> int` next to `_emit_agent`:
     ```python
     def _emit_json_error(command: str, message: str, *, exit_code: int = 2) -> int:
         from . import agent_schema

         full_cmd = f"upgrade-test {command}".strip()
         payload = {
             "command": full_cmd,
             "error": agent_schema.redact_home_paths(message),
             "exit_code": exit_code,
         }
         print(json.dumps(payload, indent=2))
         return exit_code
     ```
   - In `cmd_env(args: argparse.Namespace) -> int`, after `if getattr(args, "agent", False):` and before `for k, v in env.items():`, add:
     ```python
     if getattr(args, "json", False):
         print(json.dumps({"sandbox": str(sandbox), "env": env}, indent=2))
         return 0
     ```
   - In `cmd_clean(args: argparse.Namespace) -> int`:
     - Inside `if not targets:`, after `if getattr(args, "agent", False):`, add:
       ```python
       if getattr(args, "json", False):
           print(json.dumps([], indent=2))
           return 0
       ```
     - Inside `if not args.yes:`, after `if getattr(args, "agent", False):`, add:
       ```python
       if getattr(args, "json", False):
           print(json.dumps({"would_remove": [str(t) for t in targets]}, indent=2))
           return 0
       ```
   - In `main(argv: Optional[Sequence[str]] = None) -> int`, inside `except HarnessError as exc:`, after `if getattr(args, "agent", False):`, add:
     ```python
     if getattr(args, "json", False):
         return _emit_json_error(args.cmd or "", str(exc), exit_code=2)
     ```
3. **`tests/test_shared_flag_honored.py`** (addresses F-05):
   - Remove the five `"jfdk7p"` entries from `KNOWN_BROKEN`:
     - `("config get", "--json"): "jfdk7p"`
     - `("config is", "--json"): "jfdk7p"`
     - `("upgrade-test env", "--json"): "jfdk7p"`
     - `("upgrade-test probe", "--json"): "jfdk7p"`
     - `("upgrade-test clean", "--json"): "jfdk7p"`
   - Update `test_known_broken_citations_resolve` so that if `KNOWN_BROKEN` is empty (once `aws1tg`, `jfdk7p`, and `4y614a` have all removed their entries), the test returns cleanly rather than failing `assert seen_citations`.
   - Add dedicated behavioral tests verifying:
     - `config get`, `config is`, `config show <bad-key>`, `config set`, `config unset`, `config add`, and `config remove` exit-2 refusals under `--json` emit parseable JSON on stdout with `exit_code == 2` and redact foreign home paths (`<home>`) in `error`.
     - `upgrade-test env` and `upgrade-test probe` under `--json` emit parseable JSON both on a valid sandbox (`returncode == 0`) and on a non-sandbox path (`returncode == 2`, with `<home>` redacted in `error`) through both `run_cli` (`cli._dispatch`) and `upgrade_rehearsal.main`.
     - `upgrade-test clean` under `--json` emits parseable JSON across all three branches: empty targets (`[]`), non-empty preview without `-y` (`{"would_remove": [...]}` with sandbox preserved on disk), and confirmed removal with `-y` (list of removal result records).

## Deferred / out of scope (with reason)

- Retiring the nine `(leaf, "--fields"): "aws1tg"` entries in `tests/test_shared_flag_honored.KNOWN_BROKEN` — owned by sibling pending IPD `83ns86` (`From-Backlog: aws1tg`).
- Retiring the two `(leaf, "--no-color"): "4y614a"` entries in `tests/test_shared_flag_honored.KNOWN_BROKEN` — owned by open backlog item `4y614a`.

## Scope check

- Over-scope: none.
- Under-scope: none (all five leaves named in backlog item `jfdk7p` and every sibling branch of `_emit_config_agent_error`, `upgrade-test` `HarnessError` handling, `cmd_env`, and `cmd_clean` are covered).

## Required tests / validation

- `python3 -m pytest tests/test_shared_flag_honored.py tests/test_config.py tests/test_config_agent_surface.py tests/test_aw_upgrade_test.py tests/test_json_surface_leak_posture.py` passes with zero `"jfdk7p"` entries remaining in `KNOWN_BROKEN`.
- Mutation proof on the live working tree (restored via `try/finally` and verified by `sha256` before and after): temporarily reverting the `--json` branch in `_emit_config_agent_error` or `cmd_clean` causes `python3 -m pytest tests/test_shared_flag_honored.py -k "json"` to fail, and restoring it passes.
- Full test suite `python3 -m pytest` (bare, with default xdist and random ordering) passes.

## Spec / documentation sync

- N/A with reason: `docs/cli-output-contract.md` already specifies that every command advertising `--json` emits parseable JSON on stdout and redacts home-directory paths in error strings; this plan brings `config` and `upgrade-test` into conformance with that documented contract.

## Open questions

### OQ-01: Should `upgrade-test` `HarnessError` under `--json` and `config` `ConfigError` under `--json` use the same `{"command", "error", "exit_code"}` JSON error shape?

- Blocking: no
- Status: resolved
- Owner: agy/gemini-4-argon-high
- Resolution or deferral rationale: Resolved from repository evidence. `docs/cli-output-contract.md` Section 1 ("`--json` Raw command-specific JSON data structure (legacy/data-only)") and `tests/test_shared_flag_honored._assert_json_honored` require stdout to be valid JSON (`json.loads(res.stdout)`) with home-directory paths redacted in error strings (`docs/cli-output-contract.md` Section 4). Emitting `{"command": <cmd>, "error": <redacted-message>, "exit_code": 2}` on both `_emit_config_agent_error` and `upgrade_rehearsal._emit_json_error` gives `--json` callers a deterministic, self-describing JSON object while keeping the `aw.agent/v1` envelope (`_emit_config_agent_record` / `_emit_agent`) exclusive to `--agent`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of the baseline reproduction command invoking `tests.conformance_matrix.run_cli` with `["--json"]` across the five `jfdk7p` leaves (populated by E-01) and `python3 -m pytest tests/test_shared_flag_honored.py -k "json"` at execution HEAD.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff -- agent_workflows/cli.py` showing the `--json` / `as_json` branch in `_emit_config_agent_error` with `agent_schema.redact_home_paths(_sanitize_config_agent_error_message(msg))`, plus pasted CLI output from running `python3 -m agent_workflows config get interactive --json` and `python3 -m agent_workflows config is interactive --json` (produced by `_emit_config_agent_error` in E-02) confirming exit code `2` and valid JSON on stdout.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted `git diff -- agent_workflows/upgrade_rehearsal.py agent_workflows/cli.py` showing `_emit_json_error`, the `HarnessError` `--json` branches in `upgrade_rehearsal.main` and `cli._dispatch`, the `cmd_env` `--json` branch, and the two `cmd_clean` `--json` branches, plus pasted CLI output from `python3 -m agent_workflows upgrade-test env dummy --json`, `python3 -m agent_workflows upgrade-test probe dummy --json`, and `python3 -m agent_workflows upgrade-test clean --json` (produced by E-03) confirming valid JSON on stdout.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `git diff -- tests/test_shared_flag_honored.py` showing removal of all five `"jfdk7p"` entries from `KNOWN_BROKEN` and the new branch-level regression tests, pasted output of the live-tree mutation proof (pre-mutation `sha256`, failing pytest output when a repaired `--json` branch is commented out, restored `sha256` match, and passing pytest output), and pasted output of the full bare `python3 -m pytest` suite.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This IPD is authored to `to-review` from open backlog item `jfdk7p` (`- Blocks-Release: next`). Execution requires explicit approval transition to `approved` (`aw ipd set approved pirm70 --by-human --message ...`), followed by step-by-step execution in an isolated worktree, populating all `E-*` and `V-*` items with concrete pasted evidence, moving the completed plan to `.aw/records/plans/executed/` via `aw ipd set executed pirm70`, and committing through `aw commit`.
