# IPD: run_cli --agent error payloads become aw.agent/v1 error records and honor --fields

- Date: 2026-10-17
- Kind: child
- Concern: Every `aw run` / `aw runs` refusal emitted under `--agent` through `run_cli._emit_error` (and the two inline "failed to read ledger" sites in `_run_show` / `_run_evidence`) is a bare `{"ok": false, "error": ..., "exit_code": N}` dict, not an `aw.agent/v1` record, so `agent_schema.validate_agent_record` reports three violations against it (no `schema`, no `kind`, no `cmd`, plus missing `exit`/`outcome`) and the shared `--fields` projection is ignored (measured 2026-10-17: `aw runs status x --agent --fields cmd` prints the full bare dict).
- Scope: For the exit-2 (`run_cli.EXIT_INVALID_INVOCATION`) refusal class under `--agent` only, make `run_cli._emit_error` emit a validated `aw.agent/v1` `kind: "error"` record (`outcome: "cannot-run"`, `exit: 2`, `verified: false`, `complete: false`, `cmd` naming the leaf, a `next` recovery command), keep the legacy `ok`/`error`/`exit_code` keys and any `extra` keys inside it, home-path-redact and ANSI-strip it, and apply `agent_schema.filter_record_fields` for `--fields`, through one reusable emitter that plans `2jzld4` and `u1ujw9` build on. Route the two inline exit-2 payloads through `_emit_error`. Leave human output, every non-2 refusal (exit 1/3/4/5/6/7) and every success payload unchanged; `--json` is unchanged except that the two "failed to read ledger" payloads lose their baked-in `error: ` value prefix (E-02, the `d91i3e` F-17 convention). Update the stale comments, docs, tests and CHANGELOG that describe the old shape.
- Scope-Paths: agent_workflows/run_cli.py, agent_workflows/command_surface.py, tests/test_run_cli_error_payload_keys.py, tests/test_run_recovery_cli.py, docs/cli-output-contract.md, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: jndec6
- Set: jndec6
- Order: 1
- Highest E allocated: 07
- Author: opencode
- Id: 2t033b
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 fixed
- 2026-10-17 to-review (opencode): authored from backlog jndec6; review-ready.
- 2026-10-17 draft (opencode): created.

## Goal

Make every `aw run` / `aw runs` cannot-run refusal (exit 2) under `--agent` a schema-valid `aw.agent/v1` `kind: "error"` record that honors `--fields`, as `docs/cli-output-contract.md` Section 11.4 requires of agent-mode cannot-run errors, without breaking consumers that key off the existing `ok`/`error`/`exit_code` fields and without touching the run family's wider exit vocabulary (Section 3.1).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: emit the record

- [x] E-01 In `agent_workflows/run_cli.py`, add two helpers beside `_emit_machine`: (1) `_agent_cmd(args)` returning `"runs <leaf>"` when `getattr(args, "runs_command", None)` is set, `"run <leaf>"` when `getattr(args, "run_command", None)` is set, else `"run"` (same dest lookup as `run_cli.run_cli`); (2) `_emit_agent_record(args, rec)`, the ONE `--agent` record emitter that plans `2jzld4` E-01 and `u1ujw9` E-01 reuse instead of copying: it passes `rec` through `_redact_output`, then recursively rewrites every string value (dict values and list items at any depth, e.g. `suggested_commands`) with `agent_schema.redact_home_paths` and strips ANSI escapes with `agent_schema._ANSI_ESCAPE_RE.sub("", s)`, projects it with `agent_schema.filter_record_fields` when `args.fields` is set (normalizing a comma-separated string exactly as `run_cli._run_init` already does), and writes `sys.stdout.write(agent_schema.render_guarded_jsonl_record(rec))`. Then change `run_cli._emit_error` so that when `--agent` (or `as_agent`) is active AND `exit_code == EXIT_INVALID_INVOCATION`, it builds `rec = {"error": message, "ok": False, "exit_code": 2, **(extra or {}), "schema": agent_schema.SCHEMA_VERSION, "kind": "error", "cmd": _agent_cmd(args), "exit": 2, "outcome": "cannot-run", "verified": False, "complete": False, "next": <first entry of extra["suggested_commands"] if that list is present and non-empty, else f"aw {_agent_cmd(args)} --help">}` (envelope and legacy keys placed AFTER `extra` so an `extra` key can never override them) and returns after `_emit_agent_record(args, rec)`. Every other case (`--json`, any exit code other than 2, human mode) keeps today's code path byte-for-byte. Return value unchanged.
  - Depends on: none
  - Expected outcome: `aw runs status totalgibberish --agent` prints one JSONL line that `validate_agent_record` accepts, with `cmd: "runs status"`, `exit: 2`, `exit_code: 2`, `ok: false`, `next: "aw runs status --help"`; with `--fields cmd` the line carries only preserved envelope keys plus `cmd`; process exit stays 2.
  - Execution state: performed

- [x] E-02 In `run_cli._run_show` and `run_cli._run_evidence`, replace the inline `except Exception` branch (`err_msg = f"error: failed to read ledger: {exc}"` followed by `_emit_machine(args, {"ok": False, "error": err_msg, "exit_code": 2})`) with `return _emit_error(args, f"failed to read ledger: {exc}", EXIT_INVALID_INVOCATION)`, which is the form `run_cli._build_engine` already uses for the same condition. The human line stays `error: failed to read ledger: ...` because `_emit_error` adds the prefix when printing. DELIBERATE `--json` CHANGE at these two sites only: the machine `error` value loses its baked-in `error: ` prefix (`"error: failed to read ledger: ..."` becomes `"failed to read ledger: ..."`), which is the convention `run_cli._emit_ledger_not_found` docstring (F-17, plan `d91i3e`) already settled for every other leaf and the one `_build_engine` already emits for this exact condition; no test pins the prefixed value (searched `tests/` for `failed to read ledger`: no hit).
  - Depends on: E-01
  - Expected outcome: no remaining `_emit_machine` call in `run_cli.py` builds a literal `"exit_code": 2` payload; grep for `"exit_code": 2}` in `agent_workflows/run_cli.py` returns nothing; the behavior is pinned by E-07 (b).
  - Execution state: performed

- [x] E-03 Rewrite the "DELIBERATELY NOT AN `aw.agent/v1` RECORD (F-16)" paragraph of the `run_cli._emit_error` docstring to state the new split (exit-2 under `--agent` is an `aw.agent/v1` error record carrying the legacy keys; `--json` and non-2 refusals keep the bare shape, carried by backlog `p7bvku`) and to name `tests/test_run_cli_error_payload_keys.py` as the guard; in `agent_workflows/command_surface.py`, replace the two stale comment sentences "`run_cli._emit_error` machine payloads are deliberately not `aw.agent/v1` records and `run_cli` imports `agent_schema` zero times" (in the `runs next` and `runs resume` declaration comments) with a sentence saying the contract is not capped at (0, 1, 2) because only the exit-2 refusals are `aw.agent/v1` records and the wider codes stay bare. No `exit_contract` tuple changes.
  - Depends on: E-01
  - Expected outcome: `git diff agent_workflows/command_surface.py` touches comment lines only; no `CommandDeclaration(...)` field value changes.
  - Execution state: performed

### Task group 2: tests

- [x] E-04 Update the three existing tests in `tests/test_run_cli_error_payload_keys.py` (`test_unknown_target_payload_has_exactly_the_three_keys`, `test_explicit_absent_path_payload_has_exactly_the_three_keys`, `test_empty_ledger_payload_has_exactly_the_three_keys`): keep the exact `{"ok", "error", "exit_code"}` key-set assertion for the `--json` renderer, and for `--agent` assert instead that the output is exactly one non-empty line, `agent_schema.validate_agent_record(payload) == []`, `payload["kind"] == "error"`, `payload["outcome"] == "cannot-run"`, `payload["cmd"] == " ".join(leaf)` (`"runs verify-ledger"` for the explicit-path test), `payload["exit"] == payload["exit_code"] == rc == 2`, `payload["ok"] is False`, `payload["next"] == f"aw {payload['cmd']} --help"`, and the same `error` text assertions as today. Rename the three tests so their names no longer claim "exactly the three keys" (e.g. `..._payload_keys_per_renderer`), and update the module docstring to describe the split (`--json` bare, `--agent` an `aw.agent/v1` error record that retains the three legacy keys).
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_run_cli_error_payload_keys.py -o addopts="" -v` passes; the `--agent` rows would fail against today's code (they require `schema`/`kind`/`cmd`, which the bare dict lacks).
  - Execution state: performed

- [x] E-07 Add new tests to `tests/test_run_cli_error_payload_keys.py` (behavioral, driving `cli.main` as the module already does, P16): (a) `--fields`: `runs status totalgibberish --dir <tmp> --agent --fields cmd` and `run cancel totalgibberish --dir <tmp> --agent --fields cmd` each exit 2, print exactly one line, the record validates, `set(payload) <= agent_schema._PRESERVED_FIELDS | {"cmd"}`, and `"error" not in payload`; the same two invocations with `--json --fields cmd` still print the full bare `{"ok", "error", "exit_code"}` object; (b) the E-02 path (an unexpected read failure, which no file-system fixture produces portably because a chmod-000 file is still readable as root): write an empty file `<tmp>/ledger.jsonl`, patch `agent_workflows.run_ledger_store.RunLedgerStore.read_records` with `unittest.mock.patch(..., side_effect=OSError("boom"))`, then run `runs show <tmp>/ledger.jsonl --agent` and `runs evidence <tmp>/ledger.jsonl --agent` and assert exit 2, a valid `kind: "error"` record whose `error` starts with `failed to read ledger:` (no `error: ` prefix), and that the `--json` form of the same call carries the same unprefixed `error` value; (c) home-path redaction: `run init --workflow <p> --dir <tmp> --agent`, where `<p>` is a POSIX home-style path assembled at test time as `"/".join(["", "home", "someuser", "nope.json"])` (so this source file carries no literal home path), exits 2 with a valid record whose stdout does not contain `someuser`; (d) a non-2 refusal stays bare under `--agent`: run `run init --workflow <wf> --run-id run-0123456789abcdef --dir <tmp> --agent` twice in a scratch repo (fixture shape copied from `tests/test_run_init.py` `_create_scratch_repo` / `SAMPLE_WORKFLOW`), and assert the second call returns `run_cli.EXIT_OPERATIONAL` with a payload carrying `ok is False`, `exit_code == 6`, and no `schema` key.
  - Depends on: E-01, E-02
  - Expected outcome: `python3 -m pytest tests/test_run_cli_error_payload_keys.py -o addopts="" -v` lists the new tests PASSED; (a) and (c) fail against today's code (bare dict, no projection, no record), (b) fails against today's code (prefixed `error: ` value and no record), (d) passes before and after (it guards the boundary).
  - Execution state: performed

- [x] E-05 Update `tests/test_run_recovery_cli.py`: in `test_an_unknown_target_keeps_the_bare_machine_shape`, replace the exact `{"ok", "error", "exit_code"}` equality (which E-01 breaks under `--agent`) with assertions that the record validates, that `{"ok", "error", "exit_code"} <= set(payload)`, and that neither `target_kind` nor `suggested_commands` is present (the negative half this test exists to keep), and rename it to `test_an_unknown_target_carries_no_suggestion_keys`; in `test_both_machine_renderers_carry_the_suggestion_as_data`, keep its assertions and correct the docstring sentence that says these payloads are not `aw.agent/v1` records, and additionally assert under `--agent` that `agent_schema.validate_agent_record(payload) == []` and `payload["next"] == f"aw runs {self.run_id}"` (the first suggestion).
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_run_recovery_cli.py -o addopts="" -k "suggestion or unknown_target" -v` lists both edited tests PASSED.
  - Execution state: performed

### Task group 3: documentation

- [x] E-06 In `docs/cli-output-contract.md` Section 3 (the "Verbs emitting bare JSON or non-agent payloads" bullet) and Section 3.1 (the sentence "`aw run init` is the one `run`-family leaf whose SUCCESS `--agent` output is an `aw.agent/v1` record while its refusals keep the family's bare-JSON shape"), state that every `aw run`/`aw runs` exit-2 refusal under `--agent` is an `aw.agent/v1` `kind: "error"` record that also carries `ok` and `exit_code` and honors `--fields`, while `--json` refusals, refusals with codes 1 and 3 to 7, and success payloads other than `aw run init` keep the bare shape. In the same Section 3.1 opening paragraph ("These commands emit bare JSON dictionaries or execution manifests rather than `aw.agent/v1` records"), qualify the sentence so it no longer contradicts the new exit-2 rule. Add one `Fixed:` line to the top pending section of `CHANGELOG.md` describing the user-visible change, with no em or en dashes.
  - Depends on: E-01
  - Expected outcome: `git diff docs/cli-output-contract.md CHANGELOG.md` shows only those edits; `python3 -m pytest tests/test_cli_agent_protocol_doc.py tests/test_docs_check.py -o addopts=""` passes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `agent_schema.validate_agent_record` caps `exit` at (0, 1, 2) and requires a `kind: "error"` record to carry `exit=2` and outcome `error`/`cannot-run`; so only the exit-2 class can become a record without a protocol change. Every other `run_cli` code (1 `EXIT_INCOMPLETE`, 3 `EXIT_BLOCKED`, 4 `EXIT_INVALID_EVIDENCE`, 5 `EXIT_CORRUPTED_LEDGER`, 6 `EXIT_OPERATIONAL`, 7 `EXIT_NOT_A_LEDGER`) is part of the separate Section 3.1 vocabulary that spec `25kzda` Section 5.6 row 4 records as deliberately not renumbered (citing spec `6kwd2e` R7.3).
- Precedent for the exact record shape: `run_viewer._usage_refusal` and the unresolvable-target refusal in `run_viewer` already emit `kind: "error"`, `outcome: "cannot-run"`, `exit: 2`, `verified: false`, `complete: false`, `error`, `next` for bare `aw runs`.
- Precedent for `--fields` inside this module: `run_cli._run_init` normalizes `args.fields` (string split on commas) and calls `agent_schema.filter_record_fields` before `agent_schema.render_guarded_jsonl_record` (plan `tgfxin`).
- `agent_schema.render_guarded_jsonl_record` is strict under pytest (`PYTEST_CURRENT_TEST`), so a non-conforming record fails tests loudly rather than being silently substituted.
- `agent_schema.filter_record_fields` keeps `_PRESERVED_FIELDS` (envelope plus `applied`/`total`/`emitted`/`omitted`/`next`); `error`, `ok`, `exit_code` are NOT preserved, so `--fields cmd` drops them, matching every other `--agent` leaf.
- `run_cli._redact_output` scrubs token patterns and secret-named keys; it does not redact home paths, and some `_emit_error` messages embed absolute paths (for example `run directory already exists: {run_dir}` in `run_cli._run_init`), so `agent_schema.redact_home_paths` is needed for the validator's home-path check.
- The `aw runs` ledger leaves are in `tests/conformance_matrix.EXEMPTION_REGISTRY` as `sanctioned_raw` because their SUCCESS payloads are bare; that stays true after this plan, so the registry is not edited.
- `run_cli._emit_projection` passes a literal `2` (not the constant) for a missing `runs decisions|questions` projection, with `extra={"projection", "path"}`; E-01's `exit_code == EXIT_INVALID_INVOCATION` test covers it (2 == 2), so that refusal also becomes a record with `cmd: "runs decisions"` / `"runs questions"`. `tests/test_runs_machine_output_paths.py::test_projection_missing_machine_error` drives it under `--json` only and stays green.
- Pending plans `2jzld4` (Set `nyvyb4`, success records) and `u1ujw9` (Set `p7bvku`, exit-1 refusals) both declare `- Item-Dependencies: executed:2t033b` and reuse this plan's `_agent_cmd` helper and its redact / `--fields` / guarded-render sequence; E-01 therefore factors that sequence into one named helper (`_emit_agent_record`) so they reuse it rather than copy it.
- Tests: behavioral only (P16). `tests/test_run_cli_error_payload_keys.py` and `tests/test_run_recovery_cli.py` are not core-tier, so they must be run explicitly.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | `--agent` refusals are bare dicts and ignore `--fields`. | Measured 2026-10-17 in this lane: `AW_NO_REEXEC=1 python3 -m agent_workflows runs status x --agent --fields cmd --dir <tmp>` printed `{"error":"ledger file not found for target 'x': ...","exit_code":2,"ok":false}`, exit 2. |
| F-2 | The bare shape is a documented, test-pinned choice. | `run_cli._emit_error` docstring "DELIBERATELY NOT AN `aw.agent/v1` RECORD (F-16)"; `tests/test_run_cli_error_payload_keys.py` asserts `set(payload) == {"ok", "error", "exit_code"}` for both renderers; `tests/test_run_recovery_cli.py::test_an_unknown_target_keeps_the_bare_machine_shape` asserts the same for `--agent`. |
| F-3 | The comment justification is stale: `run_cli` does import `agent_schema`. | `from agent_workflows import (... agent_schema, ...)` at the top of `run_cli.py`, used by `_emit_projection` and `_run_init`; `command_surface.py` comments on `runs next` / `runs resume` still say "imports `agent_schema` zero times". |
| F-4 | 21 of the 48 `_emit_error` call sites pass exit 2 (20 `EXIT_INVALID_INVOCATION` plus the literal `2` in `_emit_projection`); the other 27 pass 1, 3, 5 or 6. Inline `_emit_machine` refusals also exist with codes 2 (`_run_show`, `_run_evidence` "failed to read ledger"), 3, 4, 1, 5, 7. | Call-site census of `run_cli.py` taken while authoring. |
| F-5 | Existing consumers key off `ok` and `exit_code`. | `tests/test_run_cli_corruption_exit.py::test_missing_ledger_reports_invalid_invocation` (`--agent`, asserts `ok is False`, `exit_code == 2`); `tests/test_run_recovery_cli.py::test_both_machine_renderers_carry_the_suggestion_as_data` (`{"ok","error","exit_code"} <= set(payload)`). Retaining the keys keeps both green unchanged. |
| F-6 | The two inline "failed to read ledger" payloads bake `error: ` into the machine value, unlike every other leaf. | Measured at review 2026-10-17: `runs show <unreadable-file> --agent` printed `{"error":"error: failed to read ledger: [Errno 13] Permission denied: ...","exit_code":2,"ok":false}`; `run_cli._build_engine` emits the same condition unprefixed; `run_cli._emit_ledger_not_found` docstring F-17 records the unprefixed convention. |
| F-7 | `_emit_error` messages can embed absolute home paths, which the validator rejects. | Measured at review: `run init --workflow <home-style path> --agent` printed `{"error":"failed to load workflow: workflow file not found: <that absolute path>",...}`, exit 2. Under pytest, `render_guarded_jsonl_record` is strict, so an unredacted record raises rather than prints. |

## Proposed changes (ordered, validatable)

1. E-01: add `_agent_cmd` and the shared `_emit_agent_record` emitter; build an `aw.agent/v1` error record in `_emit_error` for exit-2 `--agent` refusals.
2. E-02: route the two inline exit-2 payloads through `_emit_error`.
3. E-03: correct the stale docstring and `command_surface` comments.
4. E-04: update the three existing tests in `tests/test_run_cli_error_payload_keys.py`.
5. E-07: add the `--fields`, read-failure, home-path and non-2-stays-bare tests.
6. E-05: update the two `--agent` payload-shape tests in `tests/test_run_recovery_cli.py`.
7. E-06: update `docs/cli-output-contract.md` Sections 3 and 3.1 and add a CHANGELOG line.

## Deferred / out of scope (with reason)

- `--agent` SUCCESS payloads of `runs status|show|next|resume|evidence|verify-ledger|decisions|questions` and `run start|record|cancel|finalize|verify` are bare dicts too: converting them changes every success consumer and the `sanctioned_raw` exemptions, a separate and larger contract change than the backlog item, which names error payloads.
  - Carrier: nyvyb4
- Refusals with exit codes 1, 3, 4, 5, 6, 7 (including `_emit_not_a_ledger`, the corruption payloads, the unknown-outcome and finalize-gate payloads) stay bare: `aw.agent/v1` cannot carry those codes without a protocol decision, and the run-family codes are not to be renumbered (spec `25kzda` 5.6 row 4).
  - Carrier: p7bvku
- `--json` refusals keep the bare shape (the only `--json` change is the E-02 prefix normalization at two sites): `--fields` is defined as a projection "for --agent output" (shared help text), the backlog item names `--agent`, and changing `--json` would break `tests/test_runs_machine_output_paths.py` consumers for no stated need.
  - Carrier-Declined: deliberate design; `--json` is the full structured representation and stays bare (OQ-01, resolved)

## Scope check

- Over-scope: none. Each Scope-Path is either the fix (`run_cli.py`), a stale description of the old shape (`command_surface.py` comments, `docs/cli-output-contract.md`), a test that pins the old shape and would turn red (`tests/test_run_cli_error_payload_keys.py`, `tests/test_run_recovery_cli.py`), or the user-facing record (`CHANGELOG.md`).
- Under-scope: none known. Tests that read `--agent` refusals and are expected to stay green unchanged because the legacy keys are retained: `tests/test_run_cli_corruption_exit.py`, `tests/test_run_cli_human_redaction.py` (asserts exit 2 and `[REDACTED]` only), `tests/test_run_evidence_completion.py`, `tests/test_runs_machine_output_paths.py`, `tests/test_live_conformance_sweep.py` (its `--agent` asserts are `json.loads` of the last line plus key checks), and the remaining `--agent` rows of `tests/test_run_recovery_cli.py`. If any of them fails, that is a scope finding to resolve at execution, not a reason to drop the legacy keys. Run-viewer refusals (`run_viewer.py`) are already records and are untouched.

## Required tests / validation

- `python3 -m pytest tests/test_run_cli_error_payload_keys.py -o addopts="" -v` passes (E-04, E-07).
- `python3 -m pytest tests/test_run_recovery_cli.py tests/test_run_cli_corruption_exit.py tests/test_run_cli_human_redaction.py tests/test_runs_machine_output_paths.py tests/test_run_init.py tests/test_run_cli_declarations.py tests/test_run_evidence_completion.py tests/test_live_conformance_sweep.py -o addopts="" -n auto` passes (E-02, E-05, regressions).
- `python3 -m pytest tests/test_shared_flag_honored.py tests/test_agent_surface_conformance.py tests/test_exit_contract_conformance.py tests/test_cli_agent_protocol_doc.py tests/test_docs_check.py -o addopts="" -n auto` passes (conformance and docs).
- Routine gate `python3 -m pytest` passes.
- `aw sanitize --agent` reports no new finding on the changed files.

## Spec / documentation sync

No `.spec.md` is edited: the change brings `aw run`/`aw runs` exit-2 refusals into the existing `docs/cli-output-contract.md` Section 11.4 rule without changing any spec-governed exit code or flag table (spec `25kzda` 5.6 is untouched because no code changes value). `docs/cli-output-contract.md` Sections 3 and 3.1 are updated (E-06) because they currently describe the bare refusal shape as the rule for the whole family.

## Open questions

### OQ-01: Should `--json` refusals become records too?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. The backlog item names `--agent`; the shared `--fields` help reads "Comma-separated field projection for --agent output"; plan `tgfxin` resolved the same question the same way for `run init` (its OQ-01). See Deferred.

### OQ-02: Drop the legacy `ok` / `exit_code` keys from the record?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Keep them. `validate_agent_record` accepts extra keys, and existing consumers and tests (F-5) read them; dropping them would turn a conformance fix into a breaking change. `--fields` still removes them when the caller asks for a projection, as for any other non-preserved key.

### OQ-03: Which `next` value?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: The first entry of `suggested_commands` when `_emit_ledger_not_found` supplied one (the read command, per `run_cli._driver_run_suggestions` OQ-01 ordering), else `aw <cmd> --help`, the example Section 11.4 gives.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: from the lane root, paste stdout and exit code of `AW_NO_REEXEC=1 python3 -m agent_workflows runs status totalgibberish --dir <scratch> --agent`, the same with `--fields cmd`, and `AW_NO_REEXEC=1 python3 -m agent_workflows runs status totalgibberish --dir <scratch> --json` (code path `run_cli._emit_error` via `_emit_ledger_not_found`, changed by E-01), showing: the first is one line with `"schema":"aw.agent/v1"`, `"kind":"error"`, `"cmd":"runs status"`, `"exit":2`, `"exit_code":2`, `"ok":false`, `"next":"aw runs status --help"`; the second carries no `error`/`ok`/`exit_code` key; the third is the unchanged bare `{"error","exit_code","ok"}` object; all exit 2. Also paste the output of a one-liner piping the first line into `agent_schema.validate_agent_record` printing `[]`.
  - Observed evidence:
```
$ AW_NO_REEXEC=1 python3 -m agent_workflows runs status totalgibberish --dir /tmp --agent
{"schema":"aw.agent/v1","kind":"error","cmd":"runs status","exit":2,"outcome":"cannot-run","verified":false,"complete":false,"error":"ledger file not found for target 'totalgibberish': this reads the hash-chained ledger.jsonl, and no driver run writes one today, so there is nothing here to read rather than something missing from this run. The drivers' own events.jsonl is a different file in a different format and is not a ledger.","ok":false,"exit_code":2,"next":"aw runs status --help"}
exit: 2

$ AW_NO_REEXEC=1 python3 -m agent_workflows runs status totalgibberish --dir /tmp --agent --fields cmd
{"schema":"aw.agent/v1","kind":"error","cmd":"runs status","exit":2,"outcome":"cannot-run","verified":false,"complete":false,"next":"aw runs status --help"}
exit: 2

$ AW_NO_REEXEC=1 python3 -m agent_workflows runs status totalgibberish --dir /tmp --json
{
  "error": "ledger file not found for target 'totalgibberish': this reads the hash-chained ledger.jsonl, and no driver run writes one today, so there is nothing here to read rather than something missing from this run. The drivers' own events.jsonl is a different file in a different format and is not a ledger.",
  "exit_code": 2,
  "ok": false
}
exit: 2

$ AW_NO_REEXEC=1 python3 -m agent_workflows runs status totalgibberish --dir /tmp --agent | python3 -c "import sys, json; from agent_workflows import agent_schema; print(agent_schema.validate_agent_record(json.loads(sys.stdin.read().strip())))"
[]
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `git diff agent_workflows/run_cli.py` hunks for `_run_show` and `_run_evidence`, and the (empty) output of `grep -n '"exit_code": 2}' agent_workflows/run_cli.py`; the behavioral proof is the E-07 (b) test result pasted in V-07.
  - Observed evidence:
```
$ git diff agent_workflows/run_cli.py (_run_show hunk)
@@ -625,12 +662,9 @@ def _run_show(args: argparse.Namespace) -> int:
             _print_human(err_msg)
         return EXIT_CORRUPTED_LEDGER
     except Exception as exc:
-        err_msg = f"error: failed to read ledger: {exc}"
-        if machine:
-            _emit_machine(args, {"ok": False, "error": err_msg, "exit_code": 2})
-        else:
-            _print_human(err_msg)
-        return 2
+        return _emit_error(
+            args, f"failed to read ledger: {exc}", EXIT_INVALID_INVOCATION
+        )

$ git diff agent_workflows/run_cli.py (_run_evidence hunk)
@@ -734,12 +768,9 @@ def _run_evidence(args: argparse.Namespace) -> int:
             _print_human(err_msg)
         return EXIT_CORRUPTED_LEDGER
     except Exception as exc:
-        err_msg = f"error: failed to read ledger: {exc}"
-        if machine:
-            _emit_machine(args, {"ok": False, "error": err_msg, "exit_code": 2})
-        else:
-            _print_human(err_msg)
-        return 2
+        return _emit_error(
+            args, f"failed to read ledger: {exc}", EXIT_INVALID_INVOCATION
+        )

$ grep -n '"exit_code": 2}' agent_workflows/run_cli.py
(empty)
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `git diff agent_workflows/command_surface.py` showing only comment lines changed, and the rewritten `_emit_error` docstring paragraph; paste `python3 -m pytest tests/test_run_cli_declarations.py tests/test_exit_contract_conformance.py -o addopts="" -q` with its `N passed` line.
  - Observed evidence:
```
$ git diff agent_workflows/command_surface.py
diff --git a/agent_workflows/command_surface.py b/agent_workflows/command_surface.py
index 2bbf53cce..b8b3e6cb6 100644
--- a/agent_workflows/command_surface.py
+++ b/agent_workflows/command_surface.py
@@ -1179,8 +1179,8 @@ COMMAND_INVENTORY: Tuple[CommandDeclaration, ...] = (
     # which keys precisely on `1 in decl.exit_contract` for a `read` class, for an outcome this verb
     # does not produce. This obligation is enforced by `tests/test_conformance_matrix_structure.py`,
     # and 1 is omitted on correctness grounds rather than because nothing would catch it. The contract
-    # is not capped at (0, 1, 2) because `run_cli._emit_error` machine payloads are deliberately not
-    # `aw.agent/v1` records and `run_cli` imports `agent_schema` zero times.
+    # is not capped at (0, 1, 2) because only the exit-2 refusals are `aw.agent/v1` records and the wider
+    # codes stay bare.
     CommandDeclaration(
         command="runs next",
         command_class="read",
@@ -1228,8 +1228,8 @@ COMMAND_INVENTORY: Tuple[CommandDeclaration, ...] = (
     # (b) Exit 1 is ABSENT DELIBERATELY: `_run_resume` never returns `EXIT_INCOMPLETE`, and adding it
     # would oblige a `domain_failure` conformance scenario (`tests/conformance_matrix.py`) for an
     # outcome the verb does not produce (same reasoning as `reviews decisions`). The contract is not
-    # capped at (0, 1, 2) because `run_cli._emit_error` machine payloads are deliberately not `aw.agent/v1`
-    # records and `run_cli` imports `agent_schema` zero times.
+    # capped at (0, 1, 2) because only the exit-2 refusals are `aw.agent/v1` records and the wider
+    # codes stay bare.
     CommandDeclaration(
         command="runs resume",
         command_class="read",

Rewritten _emit_error docstring paragraph:
    For the exit-2 (`EXIT_INVALID_INVOCATION`) refusal class under `--agent`, this emits a validated
    `aw.agent/v1` `kind: "error"` record (`outcome: "cannot-run"`, `exit: 2`, `verified: false`,
    `complete: false`, `cmd` naming the leaf, and a `next` recovery command) that retains the legacy
    `ok`/`error`/`exit_code` keys and honors `--fields`. `--json` refusals and non-2 refusals (exit 1
    and 3 to 7) keep the bare JSON shape, carried by backlog `p7bvku`.
    `tests/test_run_cli_error_payload_keys.py` guards this split across leaves and renderers.

$ python3 -m pytest tests/test_run_cli_declarations.py tests/test_exit_contract_conformance.py -o addopts="" -q
..................................                                       [100%]
============================== SLOW TESTS REPORT ===============================
0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
34 passed in 46.29s
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the actual `python3 -m pytest tests/test_run_cli_error_payload_keys.py -o addopts="" -v` output listing the three renamed existing tests PASSED with the `N passed` line; the falsifiability argument is that the new `--agent` assertions require `schema`/`kind`/`cmd`, which the pre-change bare shape (still visible as the V-01 `--json` output) lacks.
  - Observed evidence:
```
$ python3 -m pytest tests/test_run_cli_error_payload_keys.py -o addopts="" -v
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
cachedir: .pytest_cache
Using --randomly-seed=117959269
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/2t033b
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 8 items

tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_empty_ledger_payload_keys_per_renderer PASSED [ 12%]
tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_explicit_absent_path_payload_keys_per_renderer PASSED [ 25%]
tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_non_two_refusal_stays_bare_under_agent PASSED [ 37%]
tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_human_stream_is_not_json PASSED [ 50%]
tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_home_path_redacted_in_error_payload PASSED [ 62%]
tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_ledger_read_failure_emits_unprefixed_error PASSED [ 75%]
tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_unknown_target_payload_keys_per_renderer PASSED [ 87%]
tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_fields_projection_honored_under_agent_and_ignored_under_json PASSED [100%]
============================== SLOW TESTS REPORT ===============================

0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
============================== 8 passed in 3.28s ===============================
```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: from the same `-v` run as V-04, paste the lines showing each new test (the `--fields`, read-failure, home-path and non-2-stays-bare tests) PASSED. Demonstrate sensitivity for (a), (b) and (c): in a scratch directory outside the lane (`git worktree add <scratch> <base commit>`, then copy only the new `tests/test_run_cli_error_payload_keys.py` in), run the three tests against the pre-change `run_cli.py` and paste their FAILED lines; then remove the scratch worktree. (d) is a boundary guard that passes before and after, so no failing run is demanded for it.
  - Observed evidence:
```
From V-04 -v run:
tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_non_two_refusal_stays_bare_under_agent PASSED [ 37%]
tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_home_path_redacted_in_error_payload PASSED [ 62%]
tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_ledger_read_failure_emits_unprefixed_error PASSED [ 75%]
tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_fields_projection_honored_under_agent_and_ignored_under_json PASSED [100%]

Sensitivity demonstration against pre-change base commit (a3e21ca50):
$ (cd /tmp/scratch_sensitivity && python3 -m pytest tests/test_run_cli_error_payload_keys.py -o addopts="" -k "test_fields_projection_honored_under_agent_and_ignored_under_json or test_ledger_read_failure_emits_unprefixed_error or test_home_path_redacted_in_error_payload" -v)
tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_home_path_redacted_in_error_payload FAILED [ 33%]
tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_fields_projection_honored_under_agent_and_ignored_under_json FAILED [ 66%]
tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_ledger_read_failure_emits_unprefixed_error FAILED [100%]

=========================== short test summary info ============================
FAILED tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_home_path_redacted_in_error_payload
FAILED tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_fields_projection_honored_under_agent_and_ignored_under_json
FAILED tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_ledger_read_failure_emits_unprefixed_error
======================= 3 failed, 5 deselected in 2.89s ========================
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_run_recovery_cli.py tests/test_run_cli_corruption_exit.py tests/test_run_cli_human_redaction.py tests/test_runs_machine_output_paths.py tests/test_run_init.py tests/test_run_cli_declarations.py tests/test_run_evidence_completion.py tests/test_live_conformance_sweep.py -o addopts="" -n auto` output with its `N passed` line and zero failures, and the `python3 -m pytest tests/test_run_recovery_cli.py -o addopts="" -k "suggestion or unknown_target" -v` lines showing the two edited tests PASSED.
  - Observed evidence:
```
$ python3 -m pytest tests/test_run_recovery_cli.py tests/test_run_cli_corruption_exit.py tests/test_run_cli_human_redaction.py tests/test_runs_machine_output_paths.py tests/test_run_init.py tests/test_run_cli_declarations.py tests/test_run_evidence_completion.py tests/test_live_conformance_sweep.py -o addopts="" -n auto
6 workers [289 items]
........................................................................ [ 24%]
........................................................................ [ 49%]
........................................................................ [ 74%]
........................................................................ [ 99%]
.                                                                        [100%]
======================== 289 passed in 60.53s (0:01:00) ========================

$ python3 -m pytest tests/test_run_recovery_cli.py -o addopts="" -k "suggestion or unknown_target" -v
tests/test_run_recovery_cli.py::TestLedgerResolutionAndWrongFormatVerdict::test_both_machine_renderers_carry_the_suggestion_as_data PASSED [ 33%]
tests/test_run_recovery_cli.py::TestLedgerResolutionAndWrongFormatVerdict::test_no_renderer_leaks_an_absolute_path_into_the_suggestion PASSED [ 66%]
tests/test_run_recovery_cli.py::TestLedgerResolutionAndWrongFormatVerdict::test_an_unknown_target_carries_no_suggestion_keys PASSED [100%]
======================= 3 passed, 51 deselected in 1.72s =======================
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `git diff docs/cli-output-contract.md CHANGELOG.md`; paste `python3 -m pytest tests/test_cli_agent_protocol_doc.py tests/test_docs_check.py tests/test_shared_flag_honored.py tests/test_agent_surface_conformance.py tests/test_exit_contract_conformance.py -o addopts="" -n auto` with its `N passed` line; paste the bare `python3 -m pytest` routine-gate summary line; paste `aw sanitize --agent` result record.
  - Observed evidence:
```
$ git diff docs/cli-output-contract.md CHANGELOG.md
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 29eccf4b6..d307f1b9a 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -38,6 +38,7 @@ Major storage-layout boundary. The logical model (D126-D129) was superseded by t
 - Changed: Test suite pruned and consolidated to 8622 tests running in 681s median wall time on 6 workers, with coverage parity verified and regression catch verified through a mutation spot-check.
 - Fixed: `runner_shared.check_lane_hook_bypass` and `leak_sanitizer._staged_files` now pass `--no-renames` to `git diff`, ensuring deleted rename sources are removed in disposable worktrees and renamed files are scanned for staged leaks even when git rename detection is enabled.
 - Fixed: `aw releases readiness` now reports gates whose input files are absent as not-applicable instead of failing (or vacuously passing), so release review is usable in managed repositories.
+- Fixed: `aw run` and `aw runs` exit-2 refusals under `--agent` now emit validated `aw.agent/v1` error records that honor `--fields`, while preserving legacy keys and keeping bare JSON for non-2 refusals and `--json` mode.
 - Added: aw run verify records verifier decisions on frozen requirements for an active run ledger, returning exit 0 on satisfied results, exit 3 on non-satisfied results, exit 2 on unknown requirements or invalid arguments, and exit 6 on unauthorized actors or terminal runs.
 - Added: aw run init now freezes workflow requirements preserving R-NN ids and appends a requirement_set record at seq=1 with matching requirement digest, and refuses workflows with empty or missing requirement ids with exit 2.
 - Added: aw run init persists workflow.json beside the ledger and later aw run/runs leaves resolve it automatically when --workflow is omitted, verifying the workflow digest against the run header (refusing mismatches with exit 2).
diff --git a/docs/cli-output-contract.md b/docs/cli-output-contract.md
index f502b752b..41cbf8a37 100644
--- a/docs/cli-output-contract.md
+++ b/docs/cli-output-contract.md
@@ -175,13 +175,13 @@ A condition is classified by its nature and not by its audience, so every audien
 The boundary governing this three-state classification is defined strictly by the record format a verb emits:

 - **Verbs emitting `aw.agent/v1` records**: Strictly bound to `{0, 1, 2}`. Mechanically enforced by `agent_schema.validate_agent_record`, which rejects any `exit` value outside `{0, 1, 2}` with a validation error, and by `agent_schema.render_jsonl_record`, which refuses to render non-conforming records. The exit parity rule in Section 4 requires the embedded `exit` field to equal the process exit code, confining any condition reachable on an agent machine surface to these three states.
-- **Verbs emitting bare JSON or non-agent payloads**: Verbs that do not emit `aw.agent/v1` records (such as `run_cli._emit_error` machine payloads on `aw runs` commands, which emit bare JSON dictionaries without envelope fields) are not bound by the three-state rule. Across the 164 command declarations in the inventory, 10 declarations declare exit codes outside `{0, 1, 2}`, all belonging to the run-execution and lifecycle family (`aw run`, `aw runs`, `aw oc runipd`, `aw agy runipd`, and `aw ipd execute-set`). These commands carry a separate, wider exit vocabulary documented in Section 3.1 below. The two vocabularies are not unified into a single schema.
+- **Verbs emitting bare JSON or non-agent payloads**: Verbs that do not emit `aw.agent/v1` records are not bound by the three-state rule. Under `--agent`, every `aw run`/`aw runs` exit-2 refusal is an `aw.agent/v1` `kind: "error"` record that also carries `ok` and `exit_code` and honors `--fields`, while `--json` refusals, refusals with codes 1 and 3 to 7, and success payloads other than `aw run init` keep the bare shape. Across the 164 command declarations in the inventory, 10 declarations declare exit codes outside `{0, 1, 2}`, all belonging to the run-execution and lifecycle family (`aw run`, `aw runs`, `aw oc runipd`, `aw agy runipd`, and `aw ipd execute-set`). These commands carry a separate, wider exit vocabulary documented in Section 3.1 below. The two vocabularies are not unified into a single schema.

 Readers can inspect `artifact_types.EXIT_CANNOT_RUN` for the shared cannot-run constant and `command_surface.CommandDeclaration.exit_contract` for each command's normative declaration. That declaration enumerates codes the command returns on its own path and deliberately does not enumerate signal-derived codes; an interrupted command exits 130 (or is killed by its signal) without that code appearing in any declaration. The interrupt path emits no `aw.agent/v1` record at all, so Section 4's exit-parity requirement has nothing to pair a signal code with.

 ### 3.1 Run-Execution Exit Vocabulary

-Commands in the run-execution family (`aw run`, `aw runs`, `aw oc runipd`, `aw agy runipd`, and `aw ipd execute-set`) manage and inspect multi-step orchestration runs, ledgers, and execution queues. These commands emit bare JSON dictionaries or execution manifests rather than `aw.agent/v1` records, and they use a wider exit code vocabulary to distinguish operational, corruption, and workflow states.
+Commands in the run-execution family (`aw run`, `aw runs`, `aw oc runipd`, `aw agy runipd`, and `aw ipd execute-set`) manage and inspect multi-step orchestration runs, ledgers, and execution queues. These commands emit bare JSON dictionaries or execution manifests rather than `aw.agent/v1` records (except for `aw run init` success and `aw run`/`aw runs` exit-2 refusals under `--agent`, which emit `aw.agent/v1` records), and they use a wider exit code vocabulary to distinguish operational, corruption, and workflow states.

 The `aw runs` viewer's read paths (bare `aw runs` and its identical leaf `aw runs list`) return exit `0` or `2`, and its opt-in mutating `aw runs repair` may also return `1`, so the viewer stays inside the three-state vocabulary and is not part of either wider table below. Under `--agent`, `aw runs` and `aw runs list` emit `aw.agent/v1` `kind: "item"` records followed by a terminal `kind: "summary"` record carrying `total`, `emitted`, `omitted`, `findings`, `filters`, and optional `excluded_runs` (or a single `kind: "summary"` record when zero items match), and emit `kind: "error"` (`outcome: "cannot-run"`, `exit: 2`) records on target, flag-conflict, and `--since` refusals. The `findings` field on the terminal summary reports the count of issue records and does not alter `outcome: "clean"` or `exit: 0`. Under `--json`, `aw runs` preserves the bare `{"runs": [...]}` success payload (with repo-relative `artifact_discrepancies[*].actual_path` and `collisions` strings) and emits the pretty-printed `kind: "error"` record on refusals.

@@ -197,7 +197,7 @@ Two distinct live exit tables govern these verbs and disagree on the meaning of
    - `6`: Operational failure. Process lock contention, illegal lifecycle transition, or unauthorized state mutation (`run init`, `run start`, `run record`, `run cancel`, `run finalize`, `run verify`).
    - `7`: Not a ledger. Target path exists and contains valid JSONL, but lacks mandatory ledger envelope fields (`runs next`, `runs resume`, `runs status`).

-   `aw run init` is the one `run`-family leaf whose SUCCESS `--agent` output is an `aw.agent/v1` record while its refusals keep the family's bare-JSON shape.
+   `aw run init` is the one `run`-family leaf whose SUCCESS `--agent` output is an `aw.agent/v1` record. Every `aw run`/`aw runs` exit-2 refusal under `--agent` is an `aw.agent/v1` `kind: "error"` record that also carries `ok` and `exit_code` and honors `--fields`, while `--json` refusals, refusals with codes 1 and 3 to 7, and success payloads other than `aw run init` keep the bare shape.

$ python3 -m pytest tests/test_cli_agent_protocol_doc.py tests/test_docs_check.py tests/test_shared_flag_honored.py tests/test_agent_surface_conformance.py tests/test_exit_contract_conformance.py -o addopts="" -n auto
6 workers [391 items]
........................................................................ [ 18%]
........................................................................ [ 36%]
........................................................................ [ 55%]
......................................................................... [ 73%]
........................................................................ [ 92%]
..............................                                           [100%]
======================== 391 passed in 89.83s (0:01:29) ========================

$ python3 -m pytest
753 passed in 115.87s (0:01:55)
(aw suite: 753 passed in 55.49s)

$ aw sanitize --agent
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5856,"findings":0,"evidence":["leak-scan"],"next":null}
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). All open questions are resolved (OQ-01, OQ-02, OQ-03).

SCOPE FENCE. `- Scope-Paths:` is the expected edit set. An out-of-scope edit is permitted only when justified at finalize with `--scope-reason <path>=<why>`; acknowledge a declared path left unmodified with `--scope-ack`.

HONESTY. Every `V-*` evidence block MUST paste the ACTUAL runner or command output; never claim a pass that was not run.

COMMIT. Commit through `aw commit 2t033b -- agent_workflows/run_cli.py agent_workflows/command_surface.py tests/test_run_cli_error_payload_keys.py tests/test_run_recovery_cli.py docs/cli-output-contract.md CHANGELOG.md <this plan>`; never push.

POST-GATE LIFECYCLE. Once every `E-*` is performed, every `V-*` is pass, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that transition; by hand run `aw ipd finalize 2t033b`. Never `git mv` the plan by hand. Dependents `2jzld4` and `u1ujw9` (`- Item-Dependencies: executed:2t033b`) become dispatchable only after that transition.
