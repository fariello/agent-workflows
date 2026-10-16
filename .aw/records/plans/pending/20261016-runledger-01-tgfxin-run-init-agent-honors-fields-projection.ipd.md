# IPD: run init --agent honors --fields projection

- Date: 2026-10-16
- Kind: child
- Concern: `aw run init --agent --fields <f>` ignores the shared `--fields` projection and emits the full record (including `run_id` and `ledger`).
- Scope: Apply `agent_schema.filter_record_fields` to the `--agent` success record in `run_cli._run_init`, add a behavioral regression test, and retire the `("run init", "--fields")` KNOWN_BROKEN ceiling entry.
- Scope-Paths: agent_workflows/run_cli.py, tests/test_run_init.py, tests/test_shared_flag_honored.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: gm9saf
- Blocks-Release: next
- Set: runledger
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: tgfxin

## Workflow history
- 2026-10-16 to-review (aw set): status set to to-review

- 2026-10-16 draft (opencode): created.

## Goal

Make `aw run init --agent --fields <list>` project its terminal `result` record down to the requested fields plus the preserved envelope (`agent_schema._PRESERVED_FIELDS`), exactly as every other `--agent` leaf does, so `tests/test_shared_flag_honored.py::test_fields_flag_honored_mutation[run init]` passes without an xfail ceiling entry.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Honor the projection in run init

- [ ] E-01 In `run_cli._run_init`, in the `--agent` branch (the block building `rec` with `"cmd": "run init"` and writing `agent_schema.render_guarded_jsonl_record(rec)`), when `getattr(args, "fields", None)` is set, normalize it to a list (split a string on commas and strip empties, the same normalization `cli._emit_config_agent_record` uses for `args.fields`) and replace `rec` with `agent_schema.filter_record_fields(rec, fields)` before rendering. Leave the `--json` and human branches unchanged.
  - Depends on: none
  - Expected outcome: `aw run init --workflow wf.json --agent --fields cmd` emits one valid `aw.agent/v1` record whose keys are a subset of `_PRESERVED_FIELDS | {"cmd"}` (no `run_id`, no `ledger`); `--fields cmd,run_id` keeps `run_id` and drops `ledger`; without `--fields` the record is byte-identical in key set to today.
  - Execution state: pending

- [ ] E-02 Add a behavioral test to `tests/test_run_init.py` that drives `run_cli("run", "init", "--workflow", <wf>, "--agent", "--fields", "cmd", cwd=repo)` and asserts exit 0, exactly one JSONL line, `agent_schema.validate_agent_record` returns no errors, `run_id` and `ledger` are absent, and that a second invocation with `--fields cmd,run_id` retains `run_id` matching `^run-[0-9a-f]{16}$` and omits `ledger`. Also assert the ledger file was still created on disk (projection must not change the side effect).
  - Depends on: E-01
  - Expected outcome: new test passes against the fixed code and would fail against the unfixed code (keys `ledger`/`run_id` present).
  - Execution state: pending

- [ ] E-03 Remove the `("run init", "--fields"): "gm9saf"` entry from `KNOWN_BROKEN` in `tests/test_shared_flag_honored.py` (the dict becomes empty, keeping its ceiling comment), so the strict-xfail case becomes a normal passing case.
  - Depends on: E-01
  - Expected outcome: `test_fields_flag_honored_mutation[run init]` runs as a plain test and passes; no XPASS(strict) failure.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_schema.filter_record_fields(record, fields)` is the single projection helper; it keeps `_PRESERVED_FIELDS` (mandatory envelope plus `applied`/`total`/`emitted`/`omitted`/`next`) and the requested keys. Callers include `cli._emit_config_agent_record` (which normalizes a string `args.fields` with `split(",")`) and `renderers` (`context.fields`).
- `tests/test_shared_flag_honored.py` documents `KNOWN_BROKEN` as a strict-xfail ceiling: "if a leaf is fixed without removing its entry, the test turns red with XPASS." So E-03 is mandatory, not optional, once E-01 lands.
- `tests/conformance_matrix.py` `RUNNABLE_ARGV` supplies `"run init": ["--workflow", "wf.json"]` for the mutation sweep.
- Prior art: executed plan `83ns86` (Set `aws1tg`) honored `--fields` across other `--agent` leaves; `ksmdcd` did so for usage refusals.
- Repo test contract: behavioral tests only (no source inspection); run the suite bare with `python3 -m pytest`.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | `run_cli._run_init` builds its `--agent` record inline and renders it without consulting `args.fields`. | `run_cli._run_init`: `sys.stdout.write(agent_schema.render_guarded_jsonl_record(rec))` directly after the dict literal containing `"run_id": run_id, "ledger": rel_ledger`. |
| F-2 | The gap is currently masked by a strict xfail. | `tests/test_shared_flag_honored.py` `KNOWN_BROKEN = {("run init", "--fields"): "gm9saf"}`. |
| F-3 | Error paths in `run_cli` emit bare `ok`/`error`/`exit_code` dicts, not `aw.agent/v1` records, by documented design (`run_cli._emit_error` docstring, "DELIBERATELY NOT AN `aw.agent/v1` RECORD (F-16)"). | Out of scope here; see Deferred. |

## Proposed changes (ordered, validatable)

1. E-01: project the `--agent` success record in `_run_init` via `filter_record_fields`.
2. E-02: add a behavioral regression test in `tests/test_run_init.py`.
3. E-03: drop the now-obsolete KNOWN_BROKEN entry.

## Deferred / out of scope (with reason)

- Converting `run_cli` error payloads to `aw.agent/v1` records and projecting them: a separate contract change across every `_emit_machine`/`_emit_error` site, explicitly deferred in the `_emit_error` docstring; the backlog item names only the success-record projection.
- Applying `--fields` to `--json` output: `--fields` is documented as "field projection for --agent output", so `--json` stays unprojected.

## Scope check

- Over-scope: none.
- Under-scope: none; the three Scope-Paths cover the fix, its regression test, and the ceiling entry the fix would otherwise turn red.

## Required tests / validation

- `python3 -m pytest tests/test_run_init.py` passes, including the new projection test (E-02).
- `python3 -m pytest tests/test_shared_flag_honored.py -o addopts="" -n auto -k "run and init"` shows `test_fields_flag_honored_mutation[run init]` PASSED (not XFAIL/XPASS) and `test_known_broken_no_dead_entries` / `test_known_broken_citations_resolve` pass.
- Routine gate `python3 -m pytest` passes.

## Spec / documentation sync

N/A: `docs/cli-output-contract.md` already requires every `--agent` leaf to honor `--fields`; this fix brings `run init` into conformance without changing the contract. No spec edits.

## Open questions

### OQ-01: Should `--fields` also project `--json` output for run init?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. The shared `--fields` help text reads "Comma-separated field projection for --agent output (envelope fields are preserved)", and the failing gate (`test_fields_flag_honored_mutation`) exercises `--agent` only.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the stdout of `aw run init --workflow <wf.json> --agent --fields cmd` run in a scratch repo (code path `run_cli._run_init` `--agent` branch, created by E-01) showing a single record whose keys exclude `run_id` and `ledger`, plus the stdout of the same command without `--fields` showing both keys still present; paste the `git diff agent_workflows/run_cli.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the actual `python3 -m pytest tests/test_run_init.py -o addopts="" -v` output showing the new projection test PASSED and the `N passed` summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the actual `python3 -m pytest tests/test_shared_flag_honored.py -o addopts="" -v -k "run and init or known_broken"` output showing `test_fields_flag_honored_mutation[run init]` PASSED (not XFAIL, not XPASS), plus the bare `python3 -m pytest` routine-gate summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit through `aw commit <this plan> -- agent_workflows/run_cli.py tests/test_run_init.py tests/test_shared_flag_honored.py`; never push. Move to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence with `Result: pass`.
