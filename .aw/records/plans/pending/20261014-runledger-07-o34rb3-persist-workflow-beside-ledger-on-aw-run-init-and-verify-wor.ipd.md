# IPD: Persist workflow beside ledger on aw run init and verify workflow_digest

- Date: 2026-10-14
- Kind: child
- Concern: `aw run init` (plan `v47z9u`) writes only the `workflow_digest` into the `kind: "run"` header record at `runner_shared.state_root(repo) / <run-id> / ledger.jsonl` without persisting the workflow JSON beside the ledger, and `run_cli._load_workflow_arg` reads only an explicit `--workflow` CLI flag before `run_cli._build_engine` falls back to `run_cli._reconstruct_workflow_from_ledger`. Because `_reconstruct_workflow_from_ledger` recovers step IDs only from ledger step records and cannot recover unattempted steps or DAG `depends_on` / `gates` edges, omitting `--workflow` on `aw run start <id> --step S-01` after `aw run init` fails with `error: unknown step 'S-01'` (exit 2) and `aw runs next <id>` reports no runnable steps (exit 3). Furthermore, when `--workflow` is supplied, `_build_engine` never compares the loaded workflow's digest against the header's `workflow_digest`. Backlog `sflov4`.
- Scope: (1) In `agent_workflows/run_cli.py`, add `WORKFLOW_FILENAME = "workflow.json"` and `_workflow_digest(workflow)`, have `_run_init` persist the canonical workflow JSON to `ledger_file.parent / WORKFLOW_FILENAME` alongside `ledger.jsonl`, and update `_load_workflow_arg(args, ledger_file=None)` to fall back to `ledger_file.parent / WORKFLOW_FILENAME` when `--workflow` is not supplied. (2) In `agent_workflows/run_cli.py` inside `_build_engine`, verify that any workflow loaded from `--workflow` or from the persisted `workflow.json` matches the `kind: "run"` header's `workflow_digest`, refusing a mismatch with `EXIT_INVALID_INVOCATION` (exit 2). (3) Align hand-seeded `kind: "run"` test fixtures in `tests/test_run_recovery_cli.py` and `tests/test_run_cli_declarations.py` with their test workflow digests, and add behavioral coverage in `tests/test_run_init.py` and `tests/test_run_recovery_cli.py`. OUT, each carried by its own plan in Set `runledger`: adding `aw run init` itself (`v47z9u`), amending spec `25kzda` (`9epp40`), adding ledger leaves to `LIVE_SAFE_LEAVES` (`g5s94t`), writing `requirement_set` / `verifier_decision` records (`um0twl`), and rendering ledger-only directories in the `aw runs` viewer (`3a3hh9`).
- Scope-Paths: agent_workflows/run_cli.py, tests/test_run_init.py, tests/test_run_recovery_cli.py, tests/test_run_cli_declarations.py
- Item-Dependencies: executed:v47z9u
- Status: to-review
- Work-Kind: followup
- Priority: low
- From-Backlog: sflov4
- Set: runledger
- Order: 7
- Highest E allocated: 05
- Author: antigravity
- Id: o34rb3

## Workflow history
- 2026-10-14 to-review (aw set): Authored review-ready IPD from backlog sflov4

- 2026-10-14 draft (antigravity): created.

## Goal

Persist the workflow definition as `workflow.json` beside `ledger.jsonl` during `aw run init`, fall back to that sibling file in `run_cli._load_workflow_arg` when `--workflow` is omitted so later `aw run` and `aw runs` leaves do not require `--workflow` repeated, and verify in `run_cli._build_engine` that any loaded workflow's canonical SHA-256 digest matches the `kind: "run"` header's `workflow_digest`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reproduce baseline after v47z9u

- [ ] E-01 Reproduce the two baseline gaps in a scratch git repo at execution HEAD (with prerequisite `v47z9u` landed). (a) Run `aw run init --workflow wf.json --run-id run-abcdef1234` and confirm `state_root(repo)/run-abcdef1234/ledger.jsonl` is created without a sibling `workflow.json`. (b) Run `aw run start run-abcdef1234 --step S-01` and `aw runs next run-abcdef1234` without `--workflow` and confirm `start` exits `2` (`error: unknown step 'S-01'`) and `next` exits `3` (`No runnable steps`). (c) Run `aw run start run-abcdef1234 --step S-01 --workflow wrong_wf.json` (where `wrong_wf.json` defines `S-01` with a different `action` and digest) and confirm it exits `0` without checking `workflow_digest`. Stop and report if `aw run init` is absent or if the behavior has already been implemented.
  - Depends on: none
  - Expected outcome: pasted outputs confirming `workflow.json` is not written on `aw run init`, omitting `--workflow` fails on `aw run start` (exit 2) and `aw runs next` (exit 3), and passing a mismatched `--workflow` is not refused.
  - Execution state: pending

### Task group 2: persist workflow.json on init, fall back in _load_workflow_arg, and verify workflow_digest

- [ ] E-02 Persist `workflow.json` in `run_cli._run_init` and fall back to it in `run_cli._load_workflow_arg`. In `agent_workflows/run_cli.py`: (a) define `WORKFLOW_FILENAME: str = "workflow.json"` and `_workflow_digest(workflow: Mapping[str, Any]) -> str` returning `store.compute_record_hash(workflow)`; (b) in `_run_init`, use `_workflow_digest(workflow)` for the `kind: "run"` header's `workflow_digest`, and after appending the initial ledger record(s) to `ledger_file`, write `json.dumps(workflow, sort_keys=True, indent=2, ensure_ascii=False) + "\n"` to `ledger_file.parent / WORKFLOW_FILENAME` (ensuring all refusal paths exit before creating or modifying `workflow.json`); (c) update `_load_workflow_arg(args: argparse.Namespace, ledger_file: Optional[Path] = None) -> Optional[Dict[str, Any]]` so when `getattr(args, "workflow", None)` is omitted and `ledger_file is not None` and `(ledger_file.parent / WORKFLOW_FILENAME).is_file()`, it loads and returns the JSON mapping from `ledger_file.parent / WORKFLOW_FILENAME`, raising `ValueError` if a workflow file parses to a non-dict JSON value.
  - Depends on: E-01
  - Expected outcome: `aw run init --workflow wf.json` writes `state_root(repo)/<run-id>/workflow.json` beside `ledger.jsonl`, and `_load_workflow_arg(args, ledger_file)` returns that workflow mapping whenever `--workflow` is omitted on subsequent `aw run` / `aw runs` invocations.
  - Execution state: pending

- [ ] E-03 Verify `workflow_digest` against the `kind: "run"` header record in `run_cli._build_engine`. In `agent_workflows/run_cli.py` inside `_build_engine(args: argparse.Namespace, ledger_file: Path)`: pass `ledger_file` to `_load_workflow_arg(args, ledger_file)`; when `workflow is not None`, read `expected_digest = str(run_rec.get("workflow_digest") or "")` from the `kind: "run"` header record (`records[0]`) and compute `actual_digest = _workflow_digest(workflow)`; if `expected_digest` is non-empty and `actual_digest != expected_digest`, return `None, records, _emit_error(args, f"workflow digest mismatch: ledger expects {expected_digest}, got {actual_digest}", EXIT_INVALID_INVOCATION)` (exit `2`). When `workflow is None` (neither `--workflow` nor sibling `workflow.json` exists), continue falling back to `_reconstruct_workflow_from_ledger(records)`.
  - Depends on: E-02
  - Expected outcome: any `aw run` or `aw runs` leaf reaching `_build_engine` with an explicit `--workflow` or a sibling `workflow.json` whose canonical SHA-256 digest disagrees with `records[0]["workflow_digest"]` refuses with `EXIT_INVALID_INVOCATION` (`2`) and `"workflow digest mismatch"` without mutating `ledger.jsonl`.
  - Execution state: pending

### Task group 3: align test fixtures and add behavioral tests

- [ ] E-04 Align hand-seeded `kind: "run"` test fixtures in `tests/test_run_recovery_cli.py` and `tests/test_run_cli_declarations.py` with their workflow digests, and add a digest-mismatch refusal row to `TestRunCliSubcommands.INVOCATIONS`. In `tests/test_run_recovery_cli.py`: update `_run_record` so `"workflow_digest"` defaults to `ledger_store.compute_record_hash(_WORKFLOW)` (matching the `_WORKFLOW` written by `_materialize` and `_workflow_file`), and add a row to `TestRunCliSubcommands.INVOCATIONS` (with a `"wrong-workflow-digest"` seed or mismatched workflow path) asserting that `aw run start` / `aw run record` with a mismatched `--workflow` exits `2` (`EXIT_INVALID_INVOCATION`) with `"workflow digest mismatch"`. In `tests/test_run_cli_declarations.py`: update `test_runs_resume_exit_3_is_reachable_and_declared` so `store_3`'s `kind: "run"` header carries `"workflow_digest": compute_record_hash(wf_dict)` matching `wf_path`.
  - Depends on: E-03
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_run_recovery_cli.py tests/test_run_cli_declarations.py` passes with all existing and new digest-mismatch rows green.
  - Execution state: pending

- [ ] E-05 Extend `tests/test_run_init.py` with end-to-end subprocess tests for persisted workflow fallback and digest verification, then run `aw sanitize --agent` and the bare test suite `python3 -m pytest`. In `tests/test_run_init.py`, assert: (a) `aw run init --workflow wf.json` creates `state_root(repo)/<id>/workflow.json` whose canonical SHA-256 digest matches `records[0]["workflow_digest"]`; (b) on a two-step workflow (`S-01` root, `S-02` with `depends_on: ["S-01"]`), running `aw runs next <id>`, `aw run start <id> --step S-02` (refused exit 3 because `S-01` is unperformed), `aw run start <id> --step S-01` (exit 0), `aw runs resume <id>` (exit 3 `unknown_outcome`), `aw run record <id> --step S-01 --state performed` (exit 0), `aw runs next <id>` (exit 0 listing `S-02`), and `aw runs status <id>` all work WITHOUT `--workflow`; (c) passing `--workflow other.json` with a different digest or tampering with `state_root(repo)/<id>/workflow.json` exits `2` (`EXIT_INVALID_INVOCATION`) with `"workflow digest mismatch"` and leaves `ledger.jsonl` byte-identical; (d) `aw run init` refusal cases leave no `workflow.json` on disk.
  - Depends on: E-04
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_run_init.py` passes, `aw sanitize --agent` reports `"outcome": "clean"`, and the bare suite `python3 -m pytest` passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Run the full test suite bare as `python3 -m pytest`; use `python3 -m pytest -o addopts="" <files>` only for targeted runs during development.
- Tests must test observable behavior and outcomes (CLI invocations, exit codes, stdout/stderr, on-disk files) and never inspect source code via `ast`, `inspect`, or regex (P16).
- Canonical JSON hashing for ledger records and workflow dicts uses `json.dumps(obj, sort_keys=True, separators=(",", ":"))` via `run_ledger_store.compute_record_hash` (`agent_workflows/run_ledger_store.py` `def compute_record_hash` and plan `v47z9u` E-03).
- Exit code `2` (`run_cli.EXIT_INVALID_INVOCATION`) is the declared exit code for bad invocations, unreadable/invalid workflow files, and mismatched `--workflow` inputs across all `aw run` and `aw runs` leaves (`agent_workflows/run_cli.py` `EXIT_INVALID_INVOCATION`).
- Cite code by SYMBOL (`module.function` or `module.CONSTANT`) or by a quoted content string, never by bare line numbers (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | `run_cli._load_workflow_arg` reads only `getattr(args, "workflow", None)` and returns `None` whenever `--workflow` is omitted on the CLI. | `agent_workflows/run_cli.py` `def _load_workflow_arg`: checks `wf_path = getattr(args, "workflow", None)` and returns `None` immediately when falsy. |
| F-02 | When `_load_workflow_arg` returns `None`, `run_cli._build_engine` falls back to `run_cli._reconstruct_workflow_from_ledger(records)`, which recovers step IDs only from `step_attempt` records and sets `depends_on: []` and no `gates` on every step. | `agent_workflows/run_cli.py` `def _reconstruct_workflow_from_ledger` and `def _build_engine`: a fresh ledger created by `aw run init` has zero `step_attempt` records, so `aw run start <id> --step S-01` without `--workflow` exits `2` (`"unknown step 'S-01'"`) and `aw runs next <id>` without `--workflow` exits `3` (`"No runnable steps"`). Even after steps are attempted, DAG `depends_on` and `gates` are absent from the reconstructed skeleton. |
| F-03 | `run_cli._build_engine` never compares a loaded workflow's digest against the `kind: "run"` header record's `workflow_digest`. | `agent_workflows/run_cli.py` `def _build_engine`: loads `workflow = _load_workflow_arg(args)` and passes `workflow` directly to `run_engine.RunEngine(workflow, ledger_store, run_id=run_id)` without reading `run_rec.get("workflow_digest")`. |
| F-04 | Two existing test files hand-seed `kind: "run"` records with placeholder `workflow_digest` strings while passing `--workflow`: `tests/test_run_recovery_cli.py` (`_run_record` sets `"workflow_digest": "a" * 64`) and `tests/test_run_cli_declarations.py` (`test_runs_resume_exit_3_is_reachable_and_declared` sets `"workflow_digest": "sha256:" + "0" * 64` on `store_3`). | `tests/test_run_recovery_cli.py` `def _run_record` and `tests/test_run_cli_declarations.py` `def test_runs_resume_exit_3_is_reachable_and_declared`. Updating both fixtures to compute `compute_record_hash` over their test workflow dict allows `_build_engine` to enforce `workflow_digest` equality uniformly with zero special-case exemptions. |
| F-05 | Persisting `workflow.json` beside `ledger.jsonl` in `state_root(repo)/<run-id>/workflow.json` does not conflict with existing test fixtures or with sibling `runledger` plans (`v47z9u`, `9epp40`, `g5s94t`, `um0twl`, `3a3hh9`). | Existing tests write `wf.json` (never `workflow.json`) alongside `run.jsonl` when testing `_reconstruct_workflow_from_ledger` fallback; `run_viewer.py` (and `3a3hh9`) classifies run directories by `state.json`, `execution-report.md`, and `ledger.jsonl`. |

## Proposed changes (ordered, validatable)

1. Reproduce the missing sibling `workflow.json`, the `--workflow`-less `aw run start` / `aw runs next` failures, and the unchecked `--workflow` digest mismatch after `v47z9u` (E-01).
2. Add `WORKFLOW_FILENAME = "workflow.json"` and `_workflow_digest` in `agent_workflows/run_cli.py`, persist `workflow.json` beside `ledger.jsonl` in `_run_init`, and fall back to `ledger_file.parent / WORKFLOW_FILENAME` in `_load_workflow_arg(args, ledger_file)` when `--workflow` is omitted (E-02).
3. Enforce `workflow_digest` verification in `run_cli._build_engine` whenever a workflow is loaded from `--workflow` or from the sibling `workflow.json`, refusing mismatches with `EXIT_INVALID_INVOCATION` (`2`) (E-03).
4. Update the hand-seeded `workflow_digest` values in `tests/test_run_recovery_cli.py` (`_run_record`) and `tests/test_run_cli_declarations.py` (`test_runs_resume_exit_3_is_reachable_and_declared`), add a digest-mismatch refusal row to `TestRunCliSubcommands.INVOCATIONS`, and extend `tests/test_run_init.py` with end-to-end tests for `--workflow`-less execution and digest mismatch refusal (E-04, E-05).

## Deferred / out of scope (with reason)

- Creating `aw run init` itself and recording the run-ledger storage location in spec `25kzda` Section 6.2.
  - Carrier: v47z9u
- Amending spec `25kzda` Section 1.2 step 8 and Section 5.1 to scope `ledger.jsonl` to `aw run`.
  - Carrier: 9epp40
- Promoting the `aw runs` ledger leaves to `LIVE_SAFE_LEAVES` in `tests/conformance_matrix.py`.
  - Carrier: g5s94t
- Freezing `requirement_set` on `aw run init` and adding `aw run verify` for `verifier_decision` records.
  - Carrier: um0twl
- Classifying and rendering ledger-only run directories in `agent_workflows/run_viewer.py`.
  - Carrier: 3a3hh9

## Scope check

- Over-scope: none.
- Under-scope: none. Both options identified in backlog `sflov4` (persisting the workflow beside the ledger with fallback in `run_cli._load_workflow_arg` AND refusing a workflow whose digest disagrees with the `kind: "run"` header) are implemented and tested together because they are complementary halves of binding a run directory to its initialized workflow.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_run_init.py tests/test_run_recovery_cli.py tests/test_run_cli_declarations.py`
- Leak sanitizer: `aw sanitize --agent`
- Bare full test suite: `python3 -m pytest`

## Spec / documentation sync

N/A with reason: `docs/cli-output-contract.md` and `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` already document `EXIT_INVALID_INVOCATION` (`2`) as the invalid-invocation exit code for `aw run` / `aw runs` leaves, and `cli.py` already documents `--workflow` as `"Optional workflow JSON (id/steps/requirements); else derived from the ledger."` Prerequisite plan `v47z9u` updates `25kzda` Section 6.2 and `docs/cli-output-contract.md` for `aw run init`.

## Open questions

### OQ-01: Should this plan implement workflow persistence beside the ledger, workflow digest verification against the `kind: "run"` header, or both?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Implement both. Persisting `workflow.json` beside `ledger.jsonl` on `aw run init` and falling back to it in `run_cli._load_workflow_arg` removes the need to repeat `--workflow` on every subsequent `aw run` / `aw runs` command, while verifying `_workflow_digest(workflow) == run_rec["workflow_digest"]` in `run_cli._build_engine` prevents an operator from accidentally passing a different `--workflow` file (or running against a tampered `workflow.json`) that disagrees with the run's frozen `workflow_digest`. Both checks live in the same 25 lines of `agent_workflows/run_cli.py`. Reversible.

### OQ-02: How should `run_cli._build_engine` handle hand-seeded ledgers in unit tests that have no sibling `workflow.json` and omit `--workflow`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: When `--workflow` is not passed and `(ledger_file.parent / WORKFLOW_FILENAME).is_file()` is `False`, `_load_workflow_arg(args, ledger_file)` returns `None` and `_build_engine` falls back to `_reconstruct_workflow_from_ledger(records)` without running the full-workflow digest check against the reconstructed skeleton. This preserves backward compatibility for all ledger-only unit tests that seed `run.jsonl` directly without `aw run init`. Reversible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted outputs from the scratch-repo reproduction commands in E-01 showing no `workflow.json` created by pre-change `aw run init`, `aw run start <id> --step S-01` (no `--workflow`) exiting `2` with `unknown step 'S-01'`, `aw runs next <id>` (no `--workflow`) exiting `3`, and `aw run start <id> --step S-01 --workflow wrong_wf.json` exiting `0`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output from running `aw run init --workflow wf.json` in a scratch repo (exercising `run_cli._run_init` and `run_cli._load_workflow_arg` updated in E-02) showing `state_root(repo)/<id>/workflow.json` created beside `ledger.jsonl`, followed by `aw runs next <id>` and `aw run start <id> --step S-01` (both without `--workflow`) exiting `0`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted output from running `aw run start <id> --step S-01 --workflow wrong_wf.json` (exercising the `run_cli._build_engine` digest check added in E-03) showing exit `2` (`EXIT_INVALID_INVOCATION`) with `"workflow digest mismatch: ledger expects ..., got ..."` and an unchanged record count in `ledger.jsonl`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" tests/test_run_recovery_cli.py tests/test_run_cli_declarations.py -v` passing with all `TestRunCliSubcommands.INVOCATIONS` rows (including the new workflow-digest-mismatch row) and `test_runs_resume_exit_3_is_reachable_and_declared` green.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" tests/test_run_init.py -v` passing, pasted output of `aw sanitize --agent` reporting `"outcome": "clean"`, and pasted summary line of bare `python3 -m pytest` passing with zero failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval and after prerequisite plan `v47z9u` is `executed`. Open questions: all resolved. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit o34rb3 -- <paths>`; never push. Paste the actual runner output for every test claim; a claim without pasted output is not evidence. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize o34rb3` only after `aw ipd lint --phase pre-transition` conforms.
