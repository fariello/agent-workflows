# IPD: Persist workflow beside ledger on aw run init and verify workflow_digest

- Date: 2026-10-14
- Kind: child
- Concern: `aw run init` (plan `v47z9u`) writes only the `workflow_digest` into the `kind: "run"` header record at `runner_shared.state_root(repo) / <run-id> / ledger.jsonl` without persisting the workflow JSON beside the ledger, and `run_cli._load_workflow_arg` reads only an explicit `--workflow` CLI flag before `run_cli._build_engine` falls back to `run_cli._reconstruct_workflow_from_ledger`. Because `_reconstruct_workflow_from_ledger` recovers step IDs only from ledger step records and cannot recover unattempted steps or DAG `depends_on` / `gates` edges, omitting `--workflow` on `aw run start <id> --step S-01` after `aw run init` fails with `error: unknown step 'S-01'` (exit 2) and `aw runs next <id>` reports no runnable steps (exit 3). Furthermore, when `--workflow` is supplied, `_build_engine` never compares the loaded workflow's digest against the header's `workflow_digest`. Backlog `sflov4`.
- Scope: (1) In `agent_workflows/run_cli.py`, add `WORKFLOW_FILENAME = "workflow.json"` and `_workflow_digest(workflow)`, have `_run_init` persist the canonical workflow JSON to `ledger_file.parent / WORKFLOW_FILENAME` alongside `ledger.jsonl`, and update `_load_workflow_arg(args, ledger_file=None)` to fall back to `ledger_file.parent / WORKFLOW_FILENAME` when `--workflow` is not supplied. (2) In `agent_workflows/run_cli.py` inside `_build_engine`, verify that any workflow loaded from `--workflow` or from the persisted `workflow.json` matches the `kind: "run"` header's `workflow_digest`, refusing a mismatch with `EXIT_INVALID_INVOCATION` (exit 2). (3) Align the one hand-seeded `kind: "run"` fixture that the new check actually reaches (`tests/test_run_recovery_cli.py` `_run_record`, F-04) with its test workflow digest, and add behavioral coverage in `tests/test_run_init.py` and `tests/test_run_recovery_cli.py`. (4) Update the `--workflow` help text in `agent_workflows/cli.py`, the `aw run` exit-2 description in `docs/cli-output-contract.md` Section 3.1, and add a CHANGELOG line. OUT, each carried by its own plan in Set `runledger`: adding `aw run init` itself (`v47z9u`), amending spec `25kzda` (`9epp40`), adding ledger leaves to `LIVE_SAFE_LEAVES` (`g5s94t`), writing `requirement_set` / `verifier_decision` records (`um0twl`), and rendering ledger-only directories in the `aw runs` viewer (`3a3hh9`).
- Scope-Paths: agent_workflows/run_cli.py, agent_workflows/cli.py, tests/test_run_init.py, tests/test_run_recovery_cli.py, docs/cli-output-contract.md, CHANGELOG.md
- Item-Dependencies: executed:v47z9u
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: sflov4
- From-Spec: 25kzda
- Set: runledger
- Order: 7
- Highest E allocated: 08
- Author: antigravity
- Id: o34rb3
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008
- 2026-10-14 to-review (aw set): Authored review-ready IPD from backlog sflov4

- 2026-10-14 draft (antigravity): created.

## Goal

Persist the workflow definition as `workflow.json` beside `ledger.jsonl` during `aw run init`, fall back to that sibling file in `run_cli._load_workflow_arg` when `--workflow` is omitted so later `aw run` and `aw runs` leaves do not require `--workflow` repeated, and verify in `run_cli._build_engine` that any loaded workflow's canonical SHA-256 digest matches the `kind: "run"` header's `workflow_digest`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reproduce baseline after v47z9u

- [ ] E-01 Reproduce the baseline behavior in a scratch git repo at execution HEAD after prerequisite `v47z9u` has landed: run `aw run init --workflow wf.json --run-id run-abcdef1234` and confirm `state_root(repo)/run-abcdef1234/workflow.json` is absent, `aw run start run-abcdef1234 --step S-01` without `--workflow` exits `2` (`error: unknown step 'S-01'`), `aw runs next run-abcdef1234` without `--workflow` exits `3` (`No runnable steps`), and `aw run start run-abcdef1234 --step S-01 --workflow wrong_wf.json` exits `0` without checking `workflow_digest`. Also confirm `v47z9u` computes the header digest as `run_ledger_store.compute_record_hash(workflow)` over the loaded `--workflow` mapping (paste `records[0]["workflow_digest"]` beside `compute_record_hash(json.load(open("wf.json")))`); this plan's equality check depends on both sides using that same function over the same mapping. Run in a scratch git repo that contains `.aw/records/` (without it `runner_shared.state_root` resolves under the home-scoped projects tree). Stop and report if `aw run init` is absent, if the header digest is computed differently, or if the behavior is already implemented.
  - Depends on: none
  - Expected outcome: pasted outputs confirming `workflow.json` is absent after `aw run init`, omitting `--workflow` fails on `aw run start` (exit 2) and `aw runs next` (exit 3), a mismatched `--workflow` is not refused, and the header digest equals `compute_record_hash` of the loaded workflow.
  - Execution state: pending

### Task group 2: persist workflow.json on init, fall back in _load_workflow_arg, and verify workflow_digest

- [ ] E-02 Persist `workflow.json` beside `ledger.jsonl` in `run_cli._run_init`. In `agent_workflows/run_cli.py`, define `WORKFLOW_FILENAME: str = "workflow.json"` and `_workflow_digest(workflow: Mapping[str, Any]) -> str` returning `store.compute_record_hash(workflow)`, compute the `kind: "run"` header's `workflow_digest` via `_workflow_digest(workflow)`, and write `json.dumps(workflow, sort_keys=True, indent=2, ensure_ascii=False) + "\n"` to `ledger_file.parent / WORKFLOW_FILENAME` via `artifact_core.atomic_write` (a `.json` destination is written byte-for-byte), BEFORE appending the header record, inside the same reserved run directory `v47z9u` E-04 creates with `mkdir(exist_ok=False)`, so that `v47z9u`'s cleanup-on-failure removes it too. Ordering rationale: if the write lands and the append fails, cleanup removes both; if the append landed first and the write failed, a valid ledger would exist with no `workflow.json` and every later leaf would silently fall back to the step-less skeleton. Any `workflow.json` write failure removes the reserved directory and exits `EXIT_OPERATIONAL` (6), the code `v47z9u` already uses for init-time filesystem failures. `json.dumps(..., indent=2)` round-trips to the same mapping, so `compute_record_hash(json.loads(file))` equals the header digest (the hash canonicalizes with `sort_keys=True, separators=(",", ":")`, independent of the file's own whitespace).
  - Depends on: E-01
  - Expected outcome: `aw run init --workflow wf.json` writes `state_root(repo)/<run-id>/workflow.json` whose `compute_record_hash(json.loads(...))` equals `records[0]["workflow_digest"]`; every `v47z9u` refusal case (existing id, malformed id, missing/invalid/non-object workflow) leaves no `workflow.json` and no run directory.
  - Execution state: pending

- [ ] E-03 Update `run_cli._load_workflow_arg` to fall back to `ledger_file.parent / WORKFLOW_FILENAME` when `--workflow` is omitted. In `agent_workflows/run_cli.py`, add optional parameter `ledger_file: Optional[Path] = None` to `_load_workflow_arg` so that when `getattr(args, "workflow", None)` is not supplied and `ledger_file is not None` and `(ledger_file.parent / WORKFLOW_FILENAME).is_file()`, it loads and returns the JSON mapping from `ledger_file.parent / WORKFLOW_FILENAME`. Change BOTH branches to raise `ValueError` when the file parses to a non-object JSON value (today the explicit `--workflow` branch returns `None` for a non-dict, which silently falls back to the step-less reconstructed skeleton); `_build_engine` already maps `ValueError` (and `json.JSONDecodeError`, a `ValueError` subclass) to exit 2 `failed to load workflow`. The sibling file is used ONLY when `--workflow` is omitted; an explicit `--workflow` always wins and is then checked by E-04.
  - Depends on: E-02
  - Expected outcome: `_load_workflow_arg(args, ledger_file)` returns the persisted `workflow.json` mapping when `--workflow` is omitted, returns `None` when neither is present, and a JSON array in either source refuses with exit 2 `failed to load workflow` instead of falling back.
  - Execution state: pending

- [ ] E-04 Enforce `workflow_digest` verification against the `kind: "run"` header record in `run_cli._build_engine`. In `agent_workflows/run_cli.py` inside `_build_engine(args: argparse.Namespace, ledger_file: Path)`, pass `ledger_file` to `_load_workflow_arg(args, ledger_file)` and, when `workflow is not None`, compare `actual_digest = _workflow_digest(workflow)` against `expected_digest = str(run_rec.get("workflow_digest") or "")` from `records[0]`, returning `None, records, _emit_error(args, f"workflow digest mismatch: ledger expects {expected_digest}, got {actual_digest}", EXIT_INVALID_INVOCATION)` (exit `2`) when `expected_digest` is non-empty and differs from `actual_digest`. Name the SOURCE in the message (`--workflow <path as given>` or the sibling `workflow.json`, by filename, never an absolute path) so an operator knows which file to fix. Hash the mapping exactly as loaded (including a `{"workflow": {...}}` compiled wrapper, which `run_engine._normalize_workflow` unwraps later), because that is what `v47z9u` E-03 hashes at init. Placement: the check runs after the `if not records:` guard and before `RunEngine(...)`, and only `_build_engine` callers are affected (`run start|record|cancel|finalize`, `runs next|resume|status`); `runs show|evidence|verify-ledger` read records directly and never load a workflow.
  - Depends on: E-03
  - Expected outcome: any `aw run` or `aw runs` leaf reaching `_build_engine` with an explicit `--workflow` or a sibling `workflow.json` whose canonical SHA-256 digest disagrees with `records[0]["workflow_digest"]` refuses with `EXIT_INVALID_INVOCATION` (`2`) and `"workflow digest mismatch"` without mutating `ledger.jsonl`.
  - Execution state: pending

### Task group 3: align test fixtures and add behavioral tests

- [ ] E-05 Align the hand-seeded `kind: "run"` fixture in `tests/test_run_recovery_cli.py` and add a digest-mismatch refusal row. Update `_run_record` so `"workflow_digest"` defaults to `ledger_store.compute_record_hash(_WORKFLOW)`, and add an `INVOCATIONS` row asserting a mismatched `--workflow` (a copy of `_WORKFLOW` with one step's `action` changed) exits `2` (`EXIT_INVALID_INVOCATION`) with `"workflow digest mismatch"` and leaves the ledger byte-identical. Do NOT edit `tests/test_run_cli_declarations.py`: its `sha256:`-prefixed placeholder digests can never equal a bare 64-hex `compute_record_hash`, yet a simulation of E-03/E-04 at review left all six of its tests passing (F-04), because none of them reaches a mismatch the test asserts against; changing them would be churn.
  - Depends on: E-04
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_run_recovery_cli.py tests/test_run_cli_declarations.py` passes with all existing rows and the new digest-mismatch row green; before the `_run_record` fix, the simulated check fails exactly `test_every_invocation_exits_in_its_class_and_says_why` and `test_a_recorded_attempt_is_durable_in_the_ledger` (measured at review, F-04).
  - Execution state: pending

- [ ] E-06 Extend `tests/test_run_init.py` (created by `v47z9u` E-05; its scratch repos contain `.aw/records/`) with subprocess tests asserting observable outcomes only: (a) `aw run init` creates `workflow.json` beside `ledger.jsonl` whose `compute_record_hash(json.loads(...))` equals `records[0]["workflow_digest"]`; (b) on a two-step DAG (`S-02` depends on `S-01`), WITHOUT `--workflow`: `aw runs next` lists only `S-01` (exit 0), `aw run start --step S-01` exit 0, `aw run record --step S-01 --state performed` exit 0, `aw runs next` then lists `S-02` (proving `depends_on` came from the persisted file, not the step-less skeleton), `aw runs status` shows both steps; (c) a mismatched `--workflow` exits 2 with `workflow digest mismatch` and the ledger is byte-identical; (d) an edited `workflow.json` exits 2 likewise; (e) a `workflow.json` containing a JSON array exits 2 `failed to load workflow`; (f) a deleted `workflow.json` falls back to the reconstructed skeleton (today's behavior, OQ-02). Show (a) and (b) failing on the base commit.
  - Depends on: E-05
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_run_init.py` shows cases (a) through (f) passing, with (a) and (b) shown failing before the change.
  - Execution state: pending

- [ ] E-08 Document the new contract. In `agent_workflows/cli.py` `_register_run_leaf`, change the `--workflow` help from "Optional workflow JSON (id/steps/requirements); else derived from the ledger." to say it defaults to the `workflow.json` that `aw run init` saved beside the ledger, falls back to ledger-derived steps only when that file is absent, and is refused (exit 2) when its digest differs from the run header. In `docs/cli-output-contract.md` Section 3.1 table 1, extend the code `2` description with "workflow digest mismatch". Add one CHANGELOG line under the top pending release (no em or en dashes).
  - Depends on: E-06
  - Expected outcome: `aw run start --help` shows the new text; the doc and CHANGELOG diffs; `tests/test_completion.py` and `tests/test_command_surface_declarations.py` pass (help text is not pinned there, re-check at execution).
  - Execution state: pending

- [ ] E-07 Run `aw sanitize --agent` and the bare test suite `python3 -m pytest`.
  - Depends on: E-08
  - Expected outcome: `aw sanitize --agent` reports `"outcome": "clean"` (exit 0) and bare `python3 -m pytest` passes with zero failures.
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
| F-04 | MEASURED AT REVIEW (HEAD `cd17d8b86`) by injecting the E-03/E-04 check into `_build_engine` as a pytest plugin over every test file that seeds a `kind: "run"` record (`test_run_recovery_cli`, `test_run_cli_declarations`, `test_runs_subdir_root`, `test_run_cli_human_redaction`, `test_capture_command_contract`, `test_redaction_key_casefold`): `2 failed, 99 passed`. The two failures are both in `tests/test_run_recovery_cli.py` (`test_every_invocation_exits_in_its_class_and_says_why`, `test_a_recorded_attempt_is_durable_in_the_ledger`), caused by `_run_record`'s placeholder `"workflow_digest": "a" * 64` meeting a real `--workflow`. With `_run_record` also simulated to use `compute_record_hash(_WORKFLOW)`, `tests/test_run_recovery_cli.py` went `52 passed`. `tests/test_run_cli_declarations.py` passed all six tests UNCHANGED under the check, so the authored edit to it (`test_runs_resume_exit_3_is_reachable_and_declared`) is unnecessary; the other four files never pass `--workflow` to a `_build_engine` leaf. | Review plugin runs (pasted counts); `tests/test_run_recovery_cli.py` `_run_record`, `_WORKFLOW`. |
| F-05 | Persisting `workflow.json` beside `ledger.jsonl` in `state_root(repo)/<run-id>/workflow.json` does not conflict with existing test fixtures or with sibling `runledger` plans (`v47z9u`, `9epp40`, `g5s94t`, `um0twl`, `3a3hh9`). | Re-checked at review: no test or production file names `workflow.json` (`grep`), existing tests write `wf.json` beside `run.jsonl`; `run_viewer.py` (and `3a3hh9`) classifies run directories by `state.json`, `execution-report.md`, and `ledger.jsonl`; `g5s94t` E-02 writes `wf.json` and invokes `aw run init --workflow <root>/wf.json`, so after this plan its fixture directories gain a `workflow.json` that its leaves then pick up (consistent, since the digest matches). |
| F-06 | `_load_workflow_arg` returns `None` (not an error) when `--workflow` names a file whose JSON is not an object, so `_build_engine` silently falls back to the step-less skeleton. The authored E-03 raised `ValueError` only for the new sibling branch, leaving the two branches inconsistent. | `agent_workflows/run_cli.py` `_load_workflow_arg` (`return data if isinstance(data, dict) else None`); `_build_engine` (`except (OSError, ValueError)` -> exit 2). |
| F-07 | The digest equality depends on BOTH sides hashing the same mapping with the same function. `v47z9u` E-03 specifies `run_ledger_store.compute_record_hash(workflow)` over the loaded `--workflow` mapping (`_load_workflow_arg` returns the compiled `{"workflow": {...}}` wrapper as-is); this plan's `_workflow_digest` is that same call. If `v47z9u` ships a different canonicalization, every operator ledger would refuse. | `v47z9u` E-03 text; `run_ledger_store.compute_record_hash`; `run_engine._normalize_workflow` (unwraps `workflow` key after loading). E-01 now verifies the equality empirically before any edit. |
| F-08 | Write ordering at init is a partial-failure question the authored E-02 left open ("after appending the initial ledger record(s)"): a header appended with no `workflow.json` would make every later `--workflow`-less leaf fall back silently. `v47z9u` E-04 reserves the run directory atomically and removes it on append failure, which covers a file written first. | `v47z9u` E-04; `artifact_core.atomic_write` (non-markdown written byte-for-byte). |
| F-09 | User-facing text describing `--workflow` becomes false after this change: the help reads "Optional workflow JSON (id/steps/requirements); else derived from the ledger." and `docs/cli-output-contract.md` Section 3.1 code `2` lists no digest refusal. The authored Spec/doc sync section claimed nothing needed updating. | `agent_workflows/cli.py` `_register_run_leaf` (`--workflow` help); `docs/cli-output-contract.md` Section 3.1 ("`2`: Invalid invocation or usage error. Missing ledger, invalid flags, or command syntax error"). |

## Proposed changes (ordered, validatable)

1. Reproduce the missing sibling `workflow.json`, the `--workflow`-less `aw run start` / `aw runs next` failures, and the unchecked `--workflow` digest mismatch after `v47z9u` (E-01).
2. Add `WORKFLOW_FILENAME = "workflow.json"` and `_workflow_digest` in `agent_workflows/run_cli.py`, and persist `workflow.json` beside `ledger.jsonl` in `_run_init` (E-02).
3. Update `run_cli._load_workflow_arg(args, ledger_file)` to fall back to `ledger_file.parent / WORKFLOW_FILENAME` when `--workflow` is omitted (E-03).
4. Enforce `workflow_digest` verification in `run_cli._build_engine` whenever a workflow is loaded from `--workflow` or from the sibling `workflow.json`, refusing mismatches with `EXIT_INVALID_INVOCATION` (`2`) (E-04).
5. Update the hand-seeded `workflow_digest` in `tests/test_run_recovery_cli.py` (`_run_record`), add a digest-mismatch refusal row to `TestRunCliSubcommands.INVOCATIONS` (E-05), and extend `tests/test_run_init.py` with end-to-end tests (E-06).
6. Update the `--workflow` help, the Section 3.1 code-2 description and the CHANGELOG (E-08).
7. Run `aw sanitize --agent` and bare `python3 -m pytest` (E-07).

## Deferred / out of scope (with reason)

- Creating `aw run init` itself and recording the run-ledger storage location in spec `25kzda` Section 6.2.
  - Carrier: v47z9u
  - Carrier-Evidence: .aw/records/plans/executed/20261012-runledger-03-v47z9u-add-aw-run-init-the-one-writer-of-a-conformant-ledger-header.ipd.md
- Amending spec `25kzda` Section 1.2 step 8 and Section 5.1 to scope `ledger.jsonl` to `aw run`.
  - Carrier: 9epp40
  - Carrier-Evidence: .aw/records/plans/executed/20261014-runledger-04-9epp40-amend-spec-25kzda-1-2-step-8-and-5-1-to-scope-the-hash-chain.ipd.md
- Promoting the `aw runs` ledger leaves to `LIVE_SAFE_LEAVES` in `tests/conformance_matrix.py`.
  - Carrier: g5s94t
  - Carrier-Evidence: .aw/records/plans/executed/20261014-runledger-05-g5s94t-add-ledger-leaves-to-live-safe-leaves-once-aw-run-init-lands.ipd.md
- Freezing `requirement_set` on `aw run init` and adding `aw run verify` for `verifier_decision` records.
  - Carrier: um0twl
- Classifying and rendering ledger-only run directories in `agent_workflows/run_viewer.py`.
  - Carrier: 3a3hh9
  - Carrier-Evidence: .aw/records/plans/executed/20261014-runledger-06-3a3hh9-classify-and-render-ledger-only-run-directories-in-aw-runs-v.ipd.md

## Scope check

- Over-scope: the authored edit to `tests/test_run_cli_declarations.py` was removed (measured unnecessary, F-04).
- Under-scope: closed at review: the explicit-branch non-object refusal (F-06), init write ordering (F-08), the help/contract-doc/CHANGELOG update (F-09) and the digest-function check in E-01 (F-07) were added. Both options identified in backlog `sflov4` (persisting the workflow beside the ledger with fallback in `run_cli._load_workflow_arg` AND refusing a workflow whose digest disagrees with the `kind: "run"` header) are implemented and tested together because they are complementary halves of binding a run directory to its initialized workflow.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_run_init.py tests/test_run_recovery_cli.py tests/test_run_cli_declarations.py`
- Leak sanitizer: `aw sanitize --agent`
- Bare full test suite: `python3 -m pytest`

## Spec / documentation sync

- Docs: `agent_workflows/cli.py` `--workflow` help and `docs/cli-output-contract.md` Section 3.1 code `2` are updated by E-08 (F-09), plus a CHANGELOG line. The exit code itself is unchanged (`EXIT_INVALID_INVOCATION`, already in every affected leaf's declared `exit_contract`), so `command_surface` declarations need no edit.
- Spec: none. Spec `25kzda` Section 6.2's ledger-location bullet is recorded by `v47z9u` E-06; no spec section defines how a workflow is resolved for a later leaf, and this plan does not add one. No `.spec.md` is in Scope-Paths.

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
- Resolution or deferral rationale: When `--workflow` is not passed and `(ledger_file.parent / WORKFLOW_FILENAME).is_file()` is `False`, `_load_workflow_arg(args, ledger_file)` returns `None` and `_build_engine` falls back to `_reconstruct_workflow_from_ledger(records)` without running the full-workflow digest check against the reconstructed skeleton. This preserves backward compatibility for all ledger-only unit tests that seed `run.jsonl` directly without `aw run init`. Re-measured at review: under a simulation of the check, the four test files that seed a header but never pass `--workflow` to a `_build_engine` leaf passed unchanged (F-04). E-06 (f) pins the deleted-file fallback. Reversible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted outputs from the scratch-repo reproduction commands in E-01 showing no `workflow.json` created by pre-change `aw run init`, `aw run start <id> --step S-01` (no `--workflow`) exiting `2` with `unknown step 'S-01'`, `aw runs next <id>` (no `--workflow`) exiting `3`, `aw run start <id> --step S-01 --workflow wrong_wf.json` exiting `0`, and the pasted pair `records[0]["workflow_digest"]` / `compute_record_hash(<loaded wf.json>)` being equal.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output from running `aw run init --workflow wf.json` in a scratch repo (exercising `run_cli._run_init` updated in E-02) showing `state_root(repo)/<id>/workflow.json` created beside `ledger.jsonl` with `compute_record_hash(json.loads(...))` matching `records[0]["workflow_digest"]`, plus the `git diff` of `_run_init` showing the write precedes the header append inside the reserved directory, and one pasted refusal (existing `--run-id`) leaving no `workflow.json`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted output from running `aw runs next <id>` and `aw run start <id> --step S-01` without `--workflow` in a scratch repo (exercising `run_cli._load_workflow_arg` updated in E-03) showing both commands exiting `0` and resolving `S-01` from the persisted `workflow.json`, and a pasted `--workflow` pointing at a JSON array exiting `2` with `failed to load workflow`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted output from running `aw run start <id> --step S-01 --workflow wrong_wf.json` (exercising the `run_cli._build_engine` digest check added in E-04) showing exit `2` (`EXIT_INVALID_INVOCATION`) with `"workflow digest mismatch: ledger expects ..., got ..."` naming the source file (no absolute path), and `sha256sum ledger.jsonl` identical before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the `tests/test_run_recovery_cli.py` diff (no `tests/test_run_cli_declarations.py` diff), and pasted output of `python3 -m pytest -o addopts="" tests/test_run_recovery_cli.py tests/test_run_cli_declarations.py -v` passing with the new workflow-digest-mismatch row and `test_runs_resume_exit_3_is_reachable_and_declared` green.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" tests/test_run_init.py -v` showing cases (a) through (f) passing, and pasted output of (a) and (b) failing on the base commit.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: the `agent_workflows/cli.py`, `docs/cli-output-contract.md` and `CHANGELOG.md` diffs (no em or en dashes in the latter two), and pasted `aw run start --help` showing the new `--workflow` text.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted output of `aw sanitize --agent` reporting `"outcome": "clean"` (exit 0) and pasted summary line of bare `python3 -m pytest` passing with zero failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval and after prerequisite plan `v47z9u` is `executed`. Open questions: all resolved. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit o34rb3 -- <paths>`; never push. Paste the actual runner output for every test claim; a claim without pasted output is not evidence. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize o34rb3` only after `aw ipd lint --phase pre-transition` conforms.
