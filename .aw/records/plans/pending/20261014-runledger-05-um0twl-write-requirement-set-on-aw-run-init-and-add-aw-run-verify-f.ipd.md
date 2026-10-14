# IPD: Write requirement_set on aw run init and add aw run verify for verifier_decision records

- Date: 2026-10-14
- Kind: child
- Concern: run-ledger CLI requirement_set and verifier_decision writers (backlog 8l1hgw)
- Scope: (1) Add `run_freeze.freeze_workflow_requirements(workflow)` so a workflow mapping's `requirements` list (`[{"id": "R-01", ...}, ...]`) freezes into a `RequirementSet` preserving its explicit `R-NN` ids rather than minting `M-NN` ids, and have `aw run init` (plan `v47z9u`) append the resulting `run_freeze.requirement_set_record` immediately after the `kind: "run"` header record (`seq=1`) with the shared `requirement_digest`. (2) Add the `aw run verify <target> --requirement <id> --result <satisfied|partial|failed|not_verifiable> [--actor verifier]` CLI leaf calling `RunEngine.record_verifier_decision`, registered in `cli.py` and declared in `command_surface.py`, so an operator-created ledger can record verifier decisions and reach `aw run finalize` exit 0. (3) Update `tests/test_run_init.py`, `tests/test_run_recovery_cli.py`, conformance/boundary registries (`tests/conformance_matrix.py`, `tests/test_exit_vocabulary_boundary.py`, `tests/test_usage_refusal_agent_record.py`), `docs/cli-output-contract.md`, and `CHANGELOG.md`. OUT, each carried by its own backlog item: persisting the workflow beside the ledger (`sflov4`), rendering a ledger-only run directory in the `aw runs` viewer (`nf84rt`), and converting the ledger leaves into live conformance-harness scenario rows (`a4tjxc`).
- Scope-Paths: agent_workflows/run_freeze.py, agent_workflows/run_cli.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_run_init.py, tests/test_run_recovery_cli.py, tests/conformance_matrix.py, tests/test_exit_vocabulary_boundary.py, tests/test_usage_refusal_agent_record.py, docs/cli-output-contract.md, CHANGELOG.md
- Item-Dependencies: executed:v47z9u
- Status: to-review
- From-Backlog: 8l1hgw
- Work-Kind: chore
- Priority: low
- Set: runledger
- Order: 5
- Highest E allocated: 07
- Author: antigravity
- Id: um0twl

## Workflow history
- 2026-10-14 to-review (aw set): ready for review

- 2026-10-14 draft (antigravity): created.

## Goal

Give operator-created run ledgers a complete CLI path to `aw run finalize` exit 0 by freezing workflow `R-NN` requirements into a `kind: "requirement_set"` record during `aw run init` (via `run_freeze.freeze_workflow_requirements` + `run_freeze.requirement_set_record`) and adding `aw run verify` to record `kind: "verifier_decision"` records through `RunEngine.record_verifier_decision`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reproduce and freeze workflow requirements on init

- [ ] E-01 Reproduce the two baseline gaps after `v47z9u` in a scratch repo. Run a one-liner showing `run_freeze.freeze_requirements({"must": ["step one"]})` mints `id='M-01'` rather than preserving a workflow's `R-01` id and `aw runs verify-ledger <id>` exits 1 with `"no frozen requirements defined"` after `aw run init --workflow wf.json`. Run `python3 -m agent_workflows run verify --help` to confirm `aw run verify` does not exist (exit 2) and `git grep record_verifier_decision agent_workflows/` to confirm `RunEngine.record_verifier_decision` has zero CLI callers.
  - Depends on: none
  - Expected outcome: pasted outputs confirming the `M-01` id mismatch, the `"no frozen requirements defined"` refusal after `aw run init`, and the absence of `aw run verify`.
  - Execution state: pending

- [ ] E-02 Add `freeze_workflow_requirements(workflow: Mapping[str, Any]) -> RequirementSet` in `agent_workflows/run_freeze.py` and wire `run_cli._run_init` to append the `kind: "requirement_set"` record (`seq=1`). In `freeze_workflow_requirements`: validate that `workflow.get("requirements")` is a non-empty list of mappings each carrying a unique non-empty string `"id"` and optional `"category"` (in `CATEGORIES`, defaulting to `"must"`) and `"text"` / `"description"` (defaulting to `id` when absent so minimal workflow dicts like `{"id": "R-01"}` freeze without extra keys). Raise `ValueError` with typed `Finding` codes (`RF-E007`..`RF-E009`) on missing/empty/non-list `requirements`, non-mapping or id-less entries, or duplicate ids. Compute each item's SHA-256 digest over `(category, id, _normalize(text))` and return `RequirementSet(requirement_digest=..., items=tuple(items))` preserving each item's `R-NN` `id`. In `run_cli._run_init`: call `frozen = run_freeze.freeze_workflow_requirements(wf)` before opening the store (exiting 2 `EXIT_INVALID_INVOCATION` without writing on `ValueError`), set `"requirement_digest": frozen.requirement_digest` on the `kind: "run"` header (`seq=0`), and immediately append `run_freeze.requirement_set_record(run_id, 1, "runtime", "", "", frozen)` through `RunLedgerStore.append` (`seq=1`).
  - Depends on: E-01
  - Expected outcome: `aw run init --workflow wf.json` writes two conformant records (`kind: "run"` at `seq=0` and `kind: "requirement_set"` at `seq=1`) with identical `requirement_digest` and the workflow's `R-NN` requirement ids, accepted by `run_ledger_schema.validate_records`.
  - Execution state: pending

### Task group 2: add the `aw run verify` CLI writer

- [ ] E-03 Add `_run_verify(args: argparse.Namespace) -> int` in `agent_workflows/run_cli.py`. Resolve the ledger path via `_resolve_or_error(args)` and construct the engine via `_build_engine(args, ledger_file)`. Require `--requirement <req-id>` and `--result <satisfied|partial|failed|not_verifiable>` (checked against `run_ledger_schema.VERIFIER_RESULTS`), returning `_emit_error(..., EXIT_INVALID_INVOCATION)` (exit 2) when either flag is missing or `--result` is outside `VERIFIER_RESULTS`. Check that `req_id` belongs to the run's frozen requirements (from `requirement_set` records in `_records` or the loaded workflow's `requirements`), returning `_emit_error(args, f"unknown requirement '{req_id}'", EXIT_INVALID_INVOCATION)` (exit 2) if unknown. Default `actor = getattr(args, "actor", None) or "verifier"` and call `engine.record_verifier_decision(req_id, result=result, actor=actor)`, catching `run_state.RunStateError` (including `UnauthorizedActorError` when `--actor != "verifier"`) and `store.LedgerLockError` as `EXIT_OPERATIONAL` (exit 6), and `store.LedgerCorruption` as `EXIT_CORRUPTED_LEDGER` (exit 5). Reconstruct state (`snapshot = engine.reconstruct_state()`). In machine mode (`--agent` / `--json`), emit `_snapshot_payload(snapshot)` with `"recorded_decision": {"requirement": req_id, "result": result, "actor": actor}`. In human mode, print `f"Recorded verifier decision: {req_id} -> {result}"`. Return `EXIT_OK` (0) when `result == "satisfied"` and `EXIT_BLOCKED` (3) when `result in ("partial", "failed", "not_verifiable")`.
  - Depends on: E-02
  - Expected outcome: `_run_verify` appends a schema-valid `kind: "verifier_decision"` record via `RunEngine.record_verifier_decision` and exits in the documented `run_cli.EXIT_*` class for each positive and refusal case.
  - Execution state: pending

- [ ] E-04 Register `aw run verify` in `agent_workflows/cli.py` and declare it in `agent_workflows/command_surface.py`. In `cli._build_parser()`: register `p_run_verify = _register_run_leaf(run_sub, "verify", "Record a verifier decision for a requirement in the ledger", _lazy("run_cli", "_run_verify"))` with `--requirement` (`help="Requirement id to verify (e.g. R-01)."`), `--result` (`help="Verifier result: satisfied, partial, failed, or not_verifiable."`), and `--actor` (`default="verifier"`, `help="Role authoring the decision (default: verifier)."`), and list `aw run verify <target> --requirement <id> --result <verdict>` in `p_run`'s help epilog. In `command_surface._DECLARATIONS`: add `CommandDeclaration(command="run verify", command_class="mutation", requires_apply=False, supports_check=False, supports_json=True, supports_agent=True, exit_contract=(0, 2, 3, 5, 6), agent_record_kind="result", notes="Record a verifier decision for a requirement in the append-only ledger.")`.
  - Depends on: E-03
  - Expected outcome: `aw run verify --help` prints the leaf usage and flags, `discover_parser_leaves` includes `"run verify"`, and `get_declaration("run verify")` returns its `CommandDeclaration`.
  - Execution state: pending

### Task group 3: tests, conformance registries, and docs

- [ ] E-05 Extend `tests/test_run_init.py` and `tests/test_run_recovery_cli.py` with end-to-end and table-driven behavioral coverage. In `tests/test_run_init.py`, assert `aw run init --workflow wf.json` creates two records (`["run", "requirement_set"]`) accepted by `run_ledger_schema.validate_records` with matching `requirement_digest` and `R-01` in `requirements`, drive the complete sequence (`init`, `start`, `record --state performed`, `verify-ledger` exit 1 naming `unsatisfied requirements: ['R-01']`, `verify --requirement R-01 --result satisfied` exit 0, `verify-ledger` exit 0 with `Completion Predicates: SATISFIED`, `finalize` exit 0 with `finalized: true` and `run_state: "complete"`, and `status` exit 0), and check that an empty or id-less `requirements` list in `wf.json` exits 2 and writes nothing. In `tests/test_run_recovery_cli.py`, add `("run", "verify", True)` to `TestLedgerResolutionAndWrongFormatVerdict.REFUSAL_LEAVES`, add `run verify` rows to `TestRunCliSubcommands.INVOCATIONS` for exit 2 (missing `--requirement`/`--result`, invalid `--result bogus`, unknown `--requirement R-99`), exit 3 (`--result failed`), exit 6 (`--actor executor`), and exit 0 (`--result satisfied --json`), and add `test_a_recorded_verifier_decision_is_durable_in_the_ledger` asserting a fresh `RunEngine` reconstructs `verifier_decisions == {"R-01": "satisfied"}`.
  - Depends on: E-04
  - Expected outcome: `pytest -o addopts="" tests/test_run_init.py tests/test_run_recovery_cli.py` passes with all new and updated assertions green.
  - Execution state: pending

- [ ] E-06 Update the CLI conformance and boundary registries in `tests/conformance_matrix.py`, `tests/test_exit_vocabulary_boundary.py`, and `tests/test_usage_refusal_agent_record.py`. Add `"run verify"` to `MUTATION_EXEMPTION_REGISTRY` in `tests/conformance_matrix.py` (`reason_kind="arg_fixture_needed"`, `citation="positional argument required"`, `reason="Requires target positional argument."`, matching `run start`/`record`/`cancel`/`finalize`; live conformance scenario conversion is tracked by backlog `a4tjxc`). Add `"run verify"` to `OUT_OF_RANGE_DECLARATION_ALLOWLIST` in `tests/test_exit_vocabulary_boundary.py` (`codes 0, 2, 3, 5, 6`). Increment the expected `REQUIRED_LEAVES` count in `tests/test_usage_refusal_agent_record.py` (`test_exclusion_set_size_and_members`) so `run verify` is exercised by `test_required_arg_leaf_agent_mode` and `test_required_arg_leaf_json_mode`.
  - Depends on: E-05
  - Expected outcome: `pytest -o addopts="" tests/test_command_surface_declarations.py tests/test_conformance_matrix_structure.py tests/test_agent_surface_conformance.py tests/test_exit_vocabulary_boundary.py tests/test_usage_refusal_agent_record.py tests/test_shared_flag_honored.py` passes.
  - Execution state: pending

- [ ] E-07 Document `aw run verify` in `docs/cli-output-contract.md` (Section 3.3 run-execution exit-code list: `aw run verify` exits 0, 2, 3, 5, 6) and add a `CHANGELOG.md` entry under `Unreleased` (no em or en dashes in either). Run `aw sanitize --agent` and the bare test suite `python3 -m pytest`.
  - Depends on: E-06
  - Expected outcome: `docs/cli-output-contract.md` and `CHANGELOG.md` diffs are clean, `aw sanitize --agent` reports `"outcome":"clean"`, and `python3 -m pytest` passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Run the full test suite bare as `python3 -m pytest`; use `-o addopts=""` only for targeted single-file runs during iteration.
- Tests must exercise observable behavior (CLI invocations, exit codes, stdout/stderr payloads, on-disk ledger records) and never inspect source text with `ast`, `inspect`, or regex (P16).
- Every parser leaf in `cli._build_parser()` must carry a matching `CommandDeclaration` in `command_surface.py` (`tests/test_command_surface_declarations.py`).
- Every `aw run <leaf>` command taking a positional `<target>` uses `_register_run_leaf` in `cli.py`, `_resolve_or_error` + `_build_engine` in `run_cli.py`, and `run_cli.EXIT_*` exit codes (`0` ok, `1` incomplete, `2` invalid invocation, `3` blocked, `4` invalid evidence, `5` corrupted ledger, `6` operational/unauthorized, `7` not a ledger).
- User-facing prose in `docs/cli-output-contract.md` and `CHANGELOG.md` must contain no em or en dashes.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by bare line numbers (`IPD-C801`).

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | `run_evidence.evaluate_completion` requires at least one `kind: "requirement_set"` record and a `kind: "verifier_decision"` record (`actor == "verifier"`, `result in ("satisfied", "pass")`) for every frozen requirement id. | `run_evidence.evaluate_completion` extracts `active_requirements` from `kind == "requirement_set"` records (`"no frozen requirements defined"` when empty) and checks `verifier_decisions.get(req_id)` for each `req_id` (`"unsatisfied requirements: ..."` when missing or not satisfied). |
| F-02 | `run_freeze.freeze_requirements` mints `M-NN` / `SC-NN` / `V-NN` / `O-NN` ids from category lists, whereas canonical and DAG workflows identify requirements by `R-NN` ids in `workflow["requirements"]`. | `run_freeze.freeze_requirements` formats `id="{0}-{1:02d}".format(prefix, idx)` with `_CATEGORY_PREFIX["must"] = "M"`, while `workflow_schema._REQUIREMENT_ID_RE` and `run_packet.build_step_packet` use `R-NN` ids from `workflow["requirements"]`. |
| F-03 | `run_freeze.requirement_set_record` already emits a schema-valid `kind: "requirement_set"` record from any `RequirementSet`. | `run_freeze.requirement_set_record` populates `schema_version`, `kind: "requirement_set"`, `requirement_digest: frozen.requirement_digest`, `requirements: [{"id": it.id, "category": it.category, "digest": it.digest, "text": it.text} ...]`, and `scope_fence: dict`, matching `run_ledger_schema._KIND_FIELDS["requirement_set"]`. |
| F-04 | Plan `v47z9u` (`aw run init`) deferred writing `requirement_set` on init to `8l1hgw` specifically because `run_freeze` lacked a workflow requirement freezer that preserves `R-NN` ids. | Plan `v47z9u` `OQ-02` ("No. `hegwri` asks for the header as its minimum, and `run_freeze.requirement_set_record` mints `M-NN` ids that do not match a workflow's `R-NN` ids, so writing one now would bake in an id mismatch. Carried by `8l1hgw`. Reversible.") and `v47z9u` `E-05(b)`. |
| F-05 | `RunEngine.record_verifier_decision` already validates `actor == "verifier"` and appends a conformant `kind: "verifier_decision"` record, and `run_cli._reconstruct_workflow_from_ledger` already recovers requirement ids from `requirement_set` records when `--workflow` is omitted. | `run_engine.RunEngine.record_verifier_decision` raises `run_state.UnauthorizedActorError` if `actor != "verifier"` and appends `kind: "verifier_decision"`; `run_cli._reconstruct_workflow_from_ledger` populates `requirements` from `kind == "requirement_set"` records. |
| F-06 | Adding a new `aw run <leaf>` with positional `target` and exit contract `(0, 2, 3, 5, 6)` touches five test/declaration surfaces beyond `cli.py` and `run_cli.py`. | `command_surface._DECLARATIONS` (`test_command_surface_declarations.py`), `MUTATION_EXEMPTION_REGISTRY` in `tests/conformance_matrix.py`, `OUT_OF_RANGE_DECLARATION_ALLOWLIST` in `tests/test_exit_vocabulary_boundary.py`, `REQUIRED_LEAVES` in `tests/test_usage_refusal_agent_record.py`, and `REFUSAL_LEAVES` in `tests/test_run_recovery_cli.py`. |

## Proposed changes (ordered, validatable)

1. Reproduce the baseline `M-01` id mismatch, `"no frozen requirements defined"` after `aw run init`, and missing `aw run verify` leaf (E-01).
2. Add `run_freeze.freeze_workflow_requirements(workflow)` preserving `R-NN` requirement ids and have `run_cli._run_init` append both `kind: "run"` (`seq=0`) and `kind: "requirement_set"` (`seq=1`) with matching `requirement_digest` (E-02).
3. Implement `run_cli._run_verify` calling `RunEngine.record_verifier_decision`, and register/declare `aw run verify` in `cli.py` and `command_surface.py` (E-03, E-04).
4. Update `tests/test_run_init.py`, `tests/test_run_recovery_cli.py`, and the CLI conformance/boundary registries (`tests/conformance_matrix.py`, `tests/test_exit_vocabulary_boundary.py`, `tests/test_usage_refusal_agent_record.py`), then update `docs/cli-output-contract.md` and `CHANGELOG.md` and run the full suite (E-05..E-07).

## Deferred / out of scope (with reason)

- Persisting the workflow beside the ledger so later step-DAG leaves (`start`, `record`, `next`) do not require `--workflow` repeated.
  - Carrier: sflov4
- Rendering a ledger-only run directory in the `aw runs` summary viewer instead of showing `0 steps`.
  - Carrier: nf84rt
- Replacing the `not_runnable` and `arg_fixture_needed` exemptions for ledger leaves in `tests/conformance_matrix.py` with live conformance-harness scenario rows.
  - Carrier: a4tjxc

## Scope check

- Over-scope: none.
- Under-scope: none. Both halves named in backlog `8l1hgw` (`requirement_set` writer preserving workflow `R-NN` ids and `verifier_decision` CLI leaf calling `RunEngine.record_verifier_decision`) are delivered and verified end-to-end through `aw run finalize` exit 0.

## Required tests / validation

- `pytest -o addopts="" tests/test_run_init.py tests/test_run_recovery_cli.py`
- `pytest -o addopts="" tests/test_command_surface_declarations.py tests/test_conformance_matrix_structure.py tests/test_agent_surface_conformance.py tests/test_exit_vocabulary_boundary.py tests/test_usage_refusal_agent_record.py tests/test_shared_flag_honored.py`
- Bare full test suite: `python3 -m pytest`
- Leak sanitizer: `aw sanitize --agent`

## Spec / documentation sync

`docs/cli-output-contract.md` Section 3.3 is updated to list `aw run verify` and its exit codes (`0, 2, 3, 5, 6`) alongside `aw run start`, `aw run record`, `aw run cancel`, and `aw run finalize`, and `CHANGELOG.md` gains an entry under `Unreleased`. Spec `25kzda` requires no changes here because its run-ledger storage location bullet in Section 6.2 is updated by `v47z9u` and its Section 1.2 / 5.1 scope language is updated by `9epp40`.

## Open questions

### OQ-01: Should `requirement_set` be written by `aw run init` at ledger creation or by a separate CLI subcommand?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: `aw run init` writes the `requirement_set` record at `seq=1` immediately after the `kind: "run"` header (`seq=0`). `aw run init` already requires `--workflow PATH` and computes `requirement_digest` from the workflow's `requirements` list (`v47z9u` E-03), and `v47z9u` OQ-02 deferred appending `requirement_set` in `aw run init` to `8l1hgw` solely because `run_freeze` minted `M-NN` ids instead of preserving the workflow's `R-NN` ids. Writing `requirement_set` in `aw run init` guarantees `run.requirement_digest == requirement_set.requirement_digest` by construction and allows `run_cli._reconstruct_workflow_from_ledger` to recover the frozen requirement ids without requiring `--workflow` on subsequent `aw run verify`, `aw runs status`, `aw runs verify-ledger`, or `aw run finalize` calls. Reversible.

### OQ-02: What exit code should `aw run verify` return when recording a non-satisfied verdict (`partial`, `failed`, or `not_verifiable`)?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Return `EXIT_BLOCKED` (`3`) when `result in ("partial", "failed", "not_verifiable")` and `EXIT_OK` (`0`) when `result == "satisfied"`. This mirrors `_run_record` (`run_cli.py`), which appends a `failed` or `blocked` step attempt to the ledger and returns `EXIT_BLOCKED` (`3`) so scripts cannot mistake a recorded failure for a green step. Reversible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted outputs from the baseline reproduction commands in E-01 (`freeze_requirements` minting `M-01`, `verify-ledger` reporting `"no frozen requirements defined"`, and `aw run verify` failing with exit 2).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted output from running `aw run init --workflow wf.json` in a scratch repo (via the `run_cli._run_init` + `run_freeze.freeze_workflow_requirements` path added in E-02) showing the two ledger records (`kind: "run"` at `seq=0` and `kind: "requirement_set"` at `seq=1`) with matching `requirement_digest`, `R-01` in `requirements`, and `run_ledger_schema.validate_records` returning `ok=True`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted output from exercising `run_cli._run_verify` (added in E-03, wired in E-04) in a scratch repo showing `aw run verify <id> --requirement R-01 --result satisfied` exiting 0 and appending a `kind: "verifier_decision"` record (`actor: "verifier"`), `aw run verify <id> --requirement R-01 --result failed` exiting 3, `aw run verify <id> --requirement R-01 --result satisfied --actor executor` exiting 6, and `aw run verify <id> --requirement R-99 --result satisfied` exiting 2.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `aw run verify --help` output showing `--requirement`, `--result`, and `--actor`, `aw run --help` showing the `aw run verify <target>` example, and a one-liner confirming `"run verify"` in `command_surface.discover_parser_leaves(cli._build_parser())` and `command_surface.get_declaration("run verify").exit_contract == (0, 2, 3, 5, 6)`.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted `pytest -o addopts="" tests/test_run_init.py tests/test_run_recovery_cli.py -v` output showing all cases passing, including the full `init -> start -> record -> verify -> verify-ledger -> finalize -> status` sequence reaching exit 0 and `run_state: "complete"`.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted `pytest -o addopts="" tests/test_command_surface_declarations.py tests/test_conformance_matrix_structure.py tests/test_agent_surface_conformance.py tests/test_exit_vocabulary_boundary.py tests/test_usage_refusal_agent_record.py tests/test_shared_flag_honored.py` output passing with 0 failures.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted `git diff -- docs/cli-output-contract.md CHANGELOG.md` showing no em or en dashes, pasted `aw sanitize --agent` output reporting `"outcome":"clean"`, and pasted bare `python3 -m pytest` summary line with 0 failures.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Do not execute this plan until it has been reviewed (`to-review` -> `reviewed`), approved (`approved`), and dispatched via the runner or an explicit execution instruction. After all `E-*` items are `performed` and all `V-*` items are `pass`, transition the plan to `executed` via `aw ipd move <path> --to executed --apply` and commit through `aw commit um0twl -- <paths>`.
