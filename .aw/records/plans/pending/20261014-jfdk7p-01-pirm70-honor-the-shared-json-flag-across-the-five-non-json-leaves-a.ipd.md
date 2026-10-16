# IPD: Honor the shared --json flag across the five non-JSON leaves and their sibling branches

- Date: 2026-10-14
- Kind: child
- Concern: Five leaves advertising the shared `--json` flag (`config get`, `config is`, `upgrade-test env`, `upgrade-test probe`, and `upgrade-test clean`) fail to emit parseable JSON on stdout along their error or dry-run/valid-sandbox branches, requiring five `("...", "--json"): "jfdk7p"` entries in `tests/test_shared_flag_honored.KNOWN_BROKEN`.
- Scope: Teach `agent_workflows/cli._emit_config_agent_error`, the `upgrade-test` `HarnessError` handlers in `agent_workflows/cli._dispatch` and `agent_workflows/upgrade_rehearsal.main`, `agent_workflows/upgrade_rehearsal.cmd_env`, and `agent_workflows/upgrade_rehearsal.cmd_clean` to emit parseable, home-path-redacted JSON on stdout whenever `--json` is passed, remove the five `(leaf, "--json"): "jfdk7p"` entries from `tests/test_shared_flag_honored.KNOWN_BROKEN`, add branch-level behavioral regression coverage in `tests/test_shared_flag_honored.py`, and add one `Fixed:` line to `CHANGELOG.md`. Every `--json` error branch reuses the canonical `renderers.emit_usage_refusal` (a `CommandResult` rendered by `JsonRenderer`, `summary` home-redacted), so no new error shape is introduced.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/upgrade_rehearsal.py, tests/test_shared_flag_honored.py, CHANGELOG.md, .aw/records/plans/pending/20261014-jfdk7p-01-pirm70-honor-the-shared-json-flag-across-the-five-non-json-leaves-a.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- From-Backlog: jfdk7p
- Blocks-Release: next
- Work-Kind: bug
- Priority: medium
- Set: jfdk7p
- Order: 1
- Highest E allocated: 05
- Author: agy/gemini-4-argon-high
- Id: pirm70
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
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

- [ ] E-02 Teach `agent_workflows/cli._emit_config_agent_error` to emit the canonical `--json` cannot-run document on stdout and return `2` when `--json` (`getattr(args, "json", False)` or `getattr(args, "as_json", False)`) is active, by delegating to `renderers.emit_usage_refusal`.
  - Depends on: E-01
  - Expected outcome: In `agent_workflows/cli._emit_config_agent_error`, after the existing `if getattr(args, "agent", False):` branch (left unchanged) and before the human `term.status("fail", msg)` fallback, when `getattr(args, "json", False) or getattr(args, "as_json", False)` is truthy, the function returns `renderers.emit_usage_refusal(cmd, _sanitize_config_agent_error_message(msg), "aw config --help", select_output(args))` (`from agent_workflows import renderers` and `from agent_workflows.result_types import select_output`, imported locally). That prints the `JsonRenderer` document (`"status": "cannot-run"`, `"exit_code": 2`, `summary` passed through `agent_schema.redact_home_paths`) on stdout and returns `2`, so `config get --json`, `config is --json`, and every other `config` subcommand routing exit-2 errors through `_emit_config_agent_error` (`show`, `set`, `unset`, `add`, `remove`) emit parseable, leak-clean JSON on stdout. The human path (no flag) is byte-identical to today.
  - Execution state: pending

- [ ] E-03 Teach `agent_workflows/upgrade_rehearsal.py` and `agent_workflows/cli.py` to honor `--json` in the `HarnessError` exit-2 handlers (`upgrade_rehearsal.main` and `cli._dispatch`), in `upgrade_rehearsal.cmd_env` on a valid sandbox, and in `upgrade_rehearsal.cmd_clean` on both the empty-targets (`if not targets:`) and preview-without-`-y` (`if not args.yes:`) branches.
  - Depends on: E-01
  - Expected outcome: (1) Both `HarnessError` handlers, `upgrade_rehearsal.main` (`except HarnessError as exc:`) and `cli._dispatch` (`if args.command == "upgrade-test":` ... `except upgrade_rehearsal.HarnessError as exc:`), after their existing `--agent` branch, return `renderers.emit_usage_refusal(<cmd>, str(exc), "aw upgrade-test --help", select_output(args))` when `getattr(args, "json", False)` is truthy, where `<cmd>` is `f"upgrade-test {subcmd}"` in `cli._dispatch` and `f"upgrade-test {getattr(args, 'command', '')}".strip()` in `upgrade_rehearsal.main` (the subparser dest is `command`; there is no `args.cmd`). No new error helper is added; (2) `upgrade_rehearsal.cmd_env`, after the `--agent` branch and before the human `export` loop, under `getattr(args, "json", False)` prints `json.dumps({"sandbox": str(sandbox), "env": {k: env[k] for k in ("XDG_CONFIG_HOME", "AW_HOME", "GIT_TERMINAL_PROMPT")}}, indent=2)` and returns `0`. It MUST NOT dump the whole `sandbox_env(...)` dict: that is a copy of `os.environ` (99 keys at review, including any secret-bearing variable of the operator's shell), so emitting it would leak credentials onto stdout. The three keys are exactly the ones the human branch exports; (3) `upgrade_rehearsal.cmd_clean`, after the `--agent` branch inside `if not targets:`, under `--json` prints `json.dumps([], indent=2)` and returns `0` (the same list shape the `-y` branch already prints for `results`), and inside `if not args.yes:` prints `json.dumps({"would_remove": [str(t) for t in targets]}, indent=2)` and returns `0` (mirroring the `--agent` preview data key).
  - Execution state: pending

### Task group 3: Retire `jfdk7p` from `KNOWN_BROKEN` and add branch-level behavioral tests

- [ ] E-04 Remove the five `(leaf, "--json"): "jfdk7p"` entries from `tests/test_shared_flag_honored.KNOWN_BROKEN`, add branch-level behavioral regression tests in `tests/test_shared_flag_honored.py` covering every repaired branch, verify mutation sensitivity on the live working tree with a restoring `try/finally` wrapper, and run the full `python3 -m pytest` suite.
  - Depends on: E-02, E-03
  - Expected outcome: The five `"jfdk7p"` entries are removed from `tests/test_shared_flag_honored.KNOWN_BROKEN` (and if `KNOWN_BROKEN` is completely empty at execution HEAD because `aws1tg` and `4y614a` have already landed, `test_known_broken_citations_resolve` allows an empty dict without failing `assert seen_citations`), new behavioral tests in `tests/test_shared_flag_honored.py` assert parseable JSON (`status == "cannot-run"`, `exit_code == 2` for refusals) and home-path redaction across `config` exit-2 refusals, `upgrade-test env` and `probe` on both valid sandboxes and non-sandbox exit-2 paths (via CLI and standalone `upgrade_rehearsal.main`), and `upgrade-test clean` across empty, preview, and `-y` branches, a test asserts `upgrade-test env <sandbox> --json` carries exactly the keys `XDG_CONFIG_HOME`, `AW_HOME`, `GIT_TERMINAL_PROMPT` under `env` and does NOT contain the value of a sentinel variable planted in the subprocess environment via `run_cli(..., env_overrides={...})`, the mutation proof fails with a reversion and passes after restoration with matching `sha256`, and bare `python3 -m pytest` passes.
  - Execution state: pending

### Task group 4: Release notes

- [ ] E-05 Add one `Fixed:` bullet under the existing `## 2.0.0 (pending)` heading in `CHANGELOG.md` stating that `aw config` refusals and `aw upgrade-test env`, `probe`, and `clean` now print parseable JSON on stdout under `--json` on every branch, including errors. Add no heading, reword no neighbouring bullet, and write no em or en dashes (user-facing prose).
  - Depends on: E-04
  - Expected outcome: a single added `Fixed:` bullet in `CHANGELOG.md` with zero em/en dashes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Shared `--json` contract (`docs/cli-output-contract.md` Section 1 "Output Modes", Section 2 "Channel Discipline", Section 4 "Machine-Surface Path Sanitization"): every command advertising `--json` in `SHARED_COMMON_FLAGS` (`agent_workflows/conventions.py` `SHARED_COMMON_FLAGS = frozenset({"--no-color", "--color", "--no-interactive", "--interactive", "--agent", "--json", "--fields", "--verbose"})`) must emit parseable JSON on `stdout` (`json.loads(res.stdout)` succeeds) across both zero and non-zero exit paths, keep human chatter off `stdout`, and redact home-directory paths (to `~`) in error/summary strings via `agent_workflows.agent_schema.redact_home_paths`.
- Behavioral gate for shared flags (`tests/test_shared_flag_honored.py`, introduced by IPD `cgsrnb`): `test_shared_flag_honored_readonly` and `test_shared_flag_honored_mutation` drive every leaf in `tests/conformance_matrix.LEAF_PATHS` through `run_cli(leaf, ["--json"], ...)` and assert `_assert_json_honored(leaf, res)` (`json.loads(res.stdout)`). Leaves in `KNOWN_BROKEN` are inverted (`pytest.fail` if they pass while still listed in `KNOWN_BROKEN`), so fixing any of the five `jfdk7p` leaves requires removing its `(leaf, "--json"): "jfdk7p"` entry from `KNOWN_BROKEN` in the same change.
- Sibling plan boundary (`.aw/records/plans/pending/20261014-aws1tg-01-83ns86-honor-the-shared-fields-projection-under-agent-across-the-ni.ipd.md`): pending IPD `83ns86` (`From-Backlog: aws1tg`) touches `agent_workflows/upgrade_rehearsal.py` and `tests/test_shared_flag_honored.py` to wire `--fields` under `--agent` and retire the nine `(leaf, "--fields"): "aws1tg"` entries in `KNOWN_BROKEN`. `83ns86` explicitly leaves the `--json` arms in `upgrade_rehearsal.py` and the five `(leaf, "--json"): "jfdk7p"` entries in `KNOWN_BROKEN` to `jfdk7p`.
- Canonical machine refusal (`agent_workflows/renderers.emit_usage_refusal`): given `select_output(args)` it emits a `CommandResult(status="cannot-run", exit_code=2, summary=redact_home_paths(message), next_actions=[...])` through `JsonRenderer` under `--json` (or `AgentRenderer` under `--agent`) and returns `2`; for a human context it prints nothing and returns `2`. Measured at review: `emit_usage_refusal("config-get", "... <home-prefix>/x", "aw config --help", ctx)` (a planted POSIX home-style prefix) printed a JSON document with `"status": "cannot-run"`, `"exit_code": 2`, `"summary": "... ~/x"`. `redact_home_paths` rewrites a home prefix to `~` (not `<home>`); `_sanitize_config_agent_error_message` already rewrites POSIX and macOS home-style prefixes to `<path>` before that.
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
| F-06 | security | high | `agent_workflows/upgrade_rehearsal.py:sandbox_env` | (review 2026-10-15) `sandbox_env` begins `env = dict(os.environ)` and only overrides a handful of keys; at review it returned 99 keys including a planted `AW_FAKE_SECRET_TOKEN`. The `--agent` branch of `cmd_env` is safe only because the compact `aw.agent/v1` record drops `data` (a planted secret was absent even under `--agent --verbose`). The authored `--json` branch `json.dumps({"sandbox": ..., "env": env})` would print the operator's entire environment, secrets included, on stdout. The `--json` branch must emit only the keys the human branch exports. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/cli.py` (`_emit_config_agent_error`, `_dispatch`)** (addresses F-01, F-02):
   - In `_emit_config_agent_error`, immediately after the `if getattr(args, "agent", False):` block, add:
     ```python
     if getattr(args, "json", False) or getattr(args, "as_json", False):
         from agent_workflows import renderers
         from agent_workflows.result_types import select_output

         return renderers.emit_usage_refusal(
             cmd,
             _sanitize_config_agent_error_message(msg),
             "aw config --help",
             select_output(args),
         )
     ```
   - In `_dispatch`, inside the `upgrade-test` `except upgrade_rehearsal.HarnessError as exc:` handler, after the `--agent` check, add:
     ```python
     if getattr(args, "json", False):
         from agent_workflows import renderers
         from agent_workflows.result_types import select_output

         return renderers.emit_usage_refusal(
             f"upgrade-test {subcmd}", str(exc), "aw upgrade-test --help", select_output(args)
         )
     ```
2. **`agent_workflows/upgrade_rehearsal.py` (`cmd_env`, `cmd_clean`, `main`)** (addresses F-02, F-03, F-04):
   - In `cmd_env`, after the `--agent` branch and before the `export` loop:
     ```python
     if getattr(args, "json", False):
         keys = ("XDG_CONFIG_HOME", "AW_HOME", "GIT_TERMINAL_PROMPT")
         print(json.dumps({"sandbox": str(sandbox), "env": {k: env[k] for k in keys}}, indent=2))
         return 0
     ```
     (never the whole `env`, which is a copy of `os.environ`; see F-06).
   - In `cmd_clean`, inside `if not targets:` after the `--agent` branch: `if getattr(args, "json", False): print(json.dumps([], indent=2)); return 0`. Inside `if not args.yes:` after the `--agent` branch: `if getattr(args, "json", False): print(json.dumps({"would_remove": [str(t) for t in targets]}, indent=2)); return 0`.
   - In `main`, inside `except HarnessError as exc:` after the `--agent` branch:
     ```python
     if getattr(args, "json", False):
         from agent_workflows import renderers
         from agent_workflows.result_types import select_output

         return renderers.emit_usage_refusal(
             f"upgrade-test {getattr(args, 'command', '')}".strip(),
             str(exc),
             "aw upgrade-test --help",
             select_output(args),
         )
     ```
3. **`tests/test_shared_flag_honored.py`** (addresses F-05):
   - Remove the five `"jfdk7p"` entries from `KNOWN_BROKEN`.
   - Update `test_known_broken_citations_resolve` so that an EMPTY `KNOWN_BROKEN` (once `aws1tg`, `jfdk7p`, and `4y614a` have all removed their entries) passes rather than failing `assert seen_citations`.
   - Add dedicated behavioral tests verifying:
     - `config get`, `config is`, and at least one refusal each of `config show <bad-key>`, `config set`, `config unset`, `config add`, and `config remove` under `--json` emit a parseable JSON document on stdout with `status == "cannot-run"` and `exit_code == 2`, and no `/home/` or `/Users/` prefix appears in stdout.
     - `upgrade-test env` and `upgrade-test probe` under `--json` emit parseable JSON both on a valid sandbox (`returncode == 0`) and on a non-sandbox path (`returncode == 2`, `status == "cannot-run"`), through both `run_cli` (`cli._dispatch`) and `upgrade_rehearsal.main`; a non-sandbox path built under a planted home-style prefix (assembled from fragments, as `tests/test_json_surface_leak_posture.py` does) appears in `summary` redacted to `~`.
     - `upgrade-test env <sandbox> --json` exposes exactly the three sandbox keys under `env` and never the value of a sentinel environment variable planted via `env_overrides`.
     - `upgrade-test clean` under `--json` emits parseable JSON across all three branches: empty targets (`[]`), non-empty preview without `-y` (`{"would_remove": [...]}` with the sandbox preserved on disk), and confirmed removal with `-y` (list of result records).
4. **`CHANGELOG.md`** (E-05): one `Fixed:` bullet.

## Deferred / out of scope (with reason)

- Retiring the nine `(leaf, "--fields"): "aws1tg"` entries in `tests/test_shared_flag_honored.KNOWN_BROKEN` — owned by sibling pending IPD `83ns86` (`From-Backlog: aws1tg`).
  - Carrier: 83ns86
  - Carrier-Evidence: .aw/records/plans/executed/20261014-aws1tg-01-83ns86-honor-the-shared-fields-projection-under-agent-across-the-ni.ipd.md
- Retiring the four `(leaf, "--fields"): "4y614a"` entries (`ipd scaffold`, `research new`, `research new-comparison`, `storage move`) in `tests/test_shared_flag_honored.KNOWN_BROKEN` — owned by backlog item `4y614a` and its pending IPD `ksmdcd`.
  - Carrier: ksmdcd

## Scope check

- Over-scope: none.
- Under-scope: none after review (the `CHANGELOG.md` line was added as E-05; all five leaves named in backlog item `jfdk7p` and every sibling branch of `_emit_config_agent_error`, `upgrade-test` `HarnessError` handling, `cmd_env`, and `cmd_clean` are covered).

## Required tests / validation

- `python3 -m pytest tests/test_shared_flag_honored.py tests/test_config.py tests/test_config_agent_surface.py tests/test_aw_upgrade_test.py tests/test_json_surface_leak_posture.py` passes with zero `"jfdk7p"` entries remaining in `KNOWN_BROKEN`.
- Mutation proof on the live working tree (restored via `try/finally` and verified by `sha256` before and after): temporarily reverting the `--json` branch in `_emit_config_agent_error` or `cmd_clean` causes `python3 -m pytest tests/test_shared_flag_honored.py -k "json"` to fail, and restoring it passes.
- Full test suite `python3 -m pytest` (bare, with default xdist and random ordering) passes.

## Spec / documentation sync

- `CHANGELOG.md` `Fixed:` bullet (E-05). No spec or contract doc change: `docs/cli-output-contract.md` already specifies that every command advertising `--json` emits parseable JSON on stdout and redacts home-directory paths in error strings; this plan brings `config` and `upgrade-test` into conformance with that documented contract.

## Open questions

### OQ-01: What JSON shape should `--json` refusals of `config` and `upgrade-test` emit?

- Blocking: no
- Status: resolved
- Owner: plan reviewer (opencode/its_direct/pt3-claude-opus-5.5-1m-us)
- Resolution or deferral rationale: Resolved from repository evidence at review, REPLACING the authored ad-hoc `{"command", "error", "exit_code"}` object. `agent_workflows/renderers.emit_usage_refusal` is the existing canonical cannot-run emitter for `--agent` and `--json` (6 callers in `agent_workflows/`), and its `--json` output is the standard `CommandResult` document (`docs/cli-output-contract.md` Section 2: the renderers "expose identical domain facts" and share one redaction posture), with `summary` passed through `redact_home_paths`. It was demonstrated at review on a concrete case (see the Conventions bullet). Reusing it avoids a fourth bespoke error shape (`{"error"}`, `{"error","valid"}` and `{"ok","error","exit_code"}` already exist in `cli.py`, `run_cli.py` and `run_viewer.py`) and keeps the `--agent` branches untouched. The success-path payloads (`cmd_env`, `cmd_clean`) remain raw command data, as the `--json` contract permits.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of the baseline reproduction command invoking `tests.conformance_matrix.run_cli` with `["--json"]` across the five `jfdk7p` leaves (populated by E-01) and `python3 -m pytest tests/test_shared_flag_honored.py -k "json"` at execution HEAD.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff -- agent_workflows/cli.py` showing the `--json` / `as_json` branch in `_emit_config_agent_error` delegating to `renderers.emit_usage_refusal`, plus pasted CLI output from running `python3 -m agent_workflows config get interactive --json` and `python3 -m agent_workflows config is interactive --json` (produced by `_emit_config_agent_error` in E-02) confirming exit code `2`, valid JSON on stdout with `"status": "cannot-run"`, and an empty stderr.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted `git diff -- agent_workflows/upgrade_rehearsal.py agent_workflows/cli.py` showing the `HarnessError` `--json` branches in `upgrade_rehearsal.main` and `cli._dispatch` calling `renderers.emit_usage_refusal`, the `cmd_env` `--json` branch emitting only the three sandbox keys, and the two `cmd_clean` `--json` branches, plus pasted CLI output from `python3 -m agent_workflows upgrade-test env dummy --json`, `python3 -m agent_workflows upgrade-test probe dummy --json`, `python3 -m agent_workflows upgrade-test clean --root <empty-tmp-dir> --json`, and `upgrade-test env <marked-tmp-sandbox> --json` run with a planted sentinel environment variable (produced by E-03), confirming valid JSON on stdout and the sentinel value absent.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `git diff -- tests/test_shared_flag_honored.py` showing removal of all five `"jfdk7p"` entries from `KNOWN_BROKEN` and the new branch-level regression tests, pasted output of the live-tree mutation proof (pre-mutation `sha256`, failing pytest output when a repaired `--json` branch is commented out, restored `sha256` match, and passing pytest output), and pasted output of the full bare `python3 -m pytest` suite.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `git diff CHANGELOG.md` showing exactly one added `Fixed:` bullet under `## 2.0.0 (pending)` and no other change, plus a pasted check confirming zero em or en dashes (`\u2013`, `\u2014`) in the added line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires `/plan-review` and explicit human approval (`aw ipd set approved pirm70 --by-human --message ...`) before execution. It inherits `- Blocks-Release: next` from backlog `jfdk7p`.

Execution contract: all open questions are resolved. Commit only the files named in `- Scope-Paths:`, through `aw commit pirm70 -- <paths>`, never `git add -A` and never `git push`. Run the suite BARE and paste the actual runner output; never claim a test result that was not produced. Mark an `E-*` item `performed` only after performing it, and a `V-*` item `pass` only after inspecting the evidence in a separate pass. Do not claim done until `aw ipd lint --phase pre-transition` reports conforming and every `V-*` item carries concrete pasted evidence with `Result: pass`. Ownership of the transition is conditional: in a managed runner lane (`AW_EXECUTION_ROLE=worker`) the RUNNER owns `aw ipd begin`/`aw ipd finalize`, so the executor commits its work and leaves the move to the runner; executing BY HAND, run `aw ipd begin` before the first edit and `aw ipd finalize` for the terminal move. Never hand-edit the status or `git mv` the file. SCOPE FENCE: an edit outside `- Scope-Paths:` that proves necessary is made and then justified with `aw ipd finalize --scope-reason`, never silently. The E-04 mutation proof edits a tracked source file in place; it MUST be restored (sha256 match) before any commit, and the mutated state is never committed.
