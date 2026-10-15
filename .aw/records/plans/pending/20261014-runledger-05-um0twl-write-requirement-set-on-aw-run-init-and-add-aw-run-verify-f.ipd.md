# IPD: Write requirement_set on aw run init and add aw run verify for verifier_decision records

- Date: 2026-10-14
- Kind: child
- Concern: No CLI path writes a `requirement_set` or a `verifier_decision` record, so `run_evidence.evaluate_completion` can never be satisfied on an operator-created ledger and `aw run finalize` can never reach exit 0 (measured: `verify-ledger` reports `no frozen requirements defined`). `run_freeze.freeze_requirements` exists but mints `M-NN` ids that do not match a workflow's `R-NN` ids, and `RunEngine.record_verifier_decision` exists with no CLI caller. Backlog `8l1hgw`.
- Scope: (1) Add `run_freeze.freeze_workflow_requirements(workflow)` so a workflow mapping's `requirements` list (`[{"id": "R-01", ...}, ...]`) freezes into a `RequirementSet` preserving its explicit `R-NN` ids rather than minting `M-NN` ids, and have `aw run init` (plan `v47z9u`) append the resulting `run_freeze.requirement_set_record` immediately after the `kind: "run"` header record (`seq=1`) with the shared `requirement_digest`. (2) Add the `aw run verify <target> --requirement <id> --result <satisfied|partial|failed|not_verifiable> [--actor verifier]` CLI leaf calling `RunEngine.record_verifier_decision`, registered in `cli.py` and declared in `command_surface.py`, so an operator-created ledger can record verifier decisions and reach `aw run finalize` exit 0. (3) Update `tests/test_run_init.py`, `tests/test_run_recovery_cli.py`, conformance/boundary registries (`tests/conformance_matrix.py`, `tests/test_exit_vocabulary_boundary.py`, `tests/test_usage_refusal_agent_record.py`), `docs/cli-output-contract.md`, and `CHANGELOG.md`. OUT, each carried by its own backlog item: persisting the workflow beside the ledger (`sflov4`), rendering a ledger-only run directory in the `aw runs` viewer (`nf84rt`), and converting the ledger leaves into live conformance-harness scenario rows (`a4tjxc`).
- Scope-Paths: agent_workflows/run_freeze.py, agent_workflows/run_cli.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_run_freeze.py, tests/test_run_init.py, tests/test_run_recovery_cli.py, tests/conformance_matrix.py, tests/test_exit_vocabulary_boundary.py, tests/test_usage_refusal_agent_record.py, tests/test_completion.py, docs/cli-output-contract.md, CHANGELOG.md
- Item-Dependencies: executed:v47z9u
- Status: reviewed
- Readiness: go-pending-approval
- From-Backlog: 8l1hgw
- Work-Kind: chore
- Priority: low
- Set: runledger
- Order: 5
- Highest E allocated: 10
- Author: antigravity
- Id: um0twl

## Workflow history
- 2026-10-15 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008, PR-009, PR-010
- 2026-10-14 to-review (aw set): ready for review

- 2026-10-14 draft (antigravity): created.

## Goal

Give operator-created run ledgers a complete CLI path to `aw run finalize` exit 0 by freezing workflow `R-NN` requirements into a `kind: "requirement_set"` record during `aw run init` (via `run_freeze.freeze_workflow_requirements` + `run_freeze.requirement_set_record`) and adding `aw run verify` to record `kind: "verifier_decision"` records through `RunEngine.record_verifier_decision`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reproduce and freeze workflow requirements on init

- [ ] E-01 Reproduce the two baseline gaps after `v47z9u` in a scratch repo. In a scratch git repo that contains `.aw/records/` (so `runner_shared.state_root` resolves inside it), run a one-liner showing `run_freeze.freeze_requirements({"must": ["step one"]})` mints `id='M-01'` rather than preserving a workflow's `R-01` id and `aw runs verify-ledger <id>` exits 1 with `"no frozen requirements defined"` after `aw run init --workflow wf.json`. Run `python3 -m agent_workflows run verify --help` to confirm `aw run verify` does not exist (exit 2, `invalid choice: 'verify'`). Also paste the header `requirement_digest` `v47z9u` wrote (its placeholder, `compute_record_hash(workflow["requirements"])`), which E-02 replaces. Stop and report if `aw run init` is absent or already writes a `requirement_set`.
  - Depends on: none
  - Expected outcome: pasted outputs confirming the `M-01` id mismatch, the `"no frozen requirements defined"` refusal after `aw run init`, and the absence of `aw run verify`.
  - Execution state: pending

- [ ] E-02 Add `freeze_workflow_requirements(workflow: Mapping[str, Any]) -> RequirementSet` in `agent_workflows/run_freeze.py`. Unwrap a compiled `{"workflow": {...}}` mapping first, exactly as `run_engine._normalize_workflow` does (the loaded `--workflow` may be either shape; `wrapped.get("requirements")` is `None`, measured at review). Then validate that the requirements value is a non-empty list of mappings each carrying a unique non-empty string `"id"` and optional `"category"` (in `CATEGORIES`, defaulting to `"must"`) and `"text"` / `"description"` (defaulting to `id` when absent so minimal workflow dicts like `{"id": "R-01"}` freeze without extra keys). Raise `ValueError` with typed `Finding` codes (`RF-E007`..`RF-E009`) on missing/empty/non-list `requirements`, non-mapping or id-less entries, or duplicate ids. Compute each item's digest with the module's own `_digest(category, _normalize(text))` (category-bound, the same function `freeze_requirements` uses, so `diff_requirements` / `refuse_drop_or_redefine` keep working over both freezers) and the set digest exactly as `freeze_requirements` does (SHA-256 over the sorted item digests), returning `RequirementSet(requirement_digest=..., items=tuple(items))` with each item's own `id` preserved in input order. The authored "digest over `(category, id, text)`" is dropped: binding the id into the item digest would make a renumbered but otherwise identical requirement look like a meaning change, the opposite of the module's semantic-identity rule. The new `RF-E007`..`RF-E009` codes are this function's own (the module's existing codes stop at `RF-E006` and resume at `RF-E010`). Ids are NOT required to match `R-NN` (`workflow_schema.is_valid_requirement_id` enforces that for compiled workflows; this freezer only requires a unique non-empty string), so a hand-written test workflow keeps working.
  - Depends on: E-01
  - Expected outcome: `freeze_workflow_requirements({"requirements": [{"id": "R-01"}]})` returns one item with `id == "R-01"`, `category == "must"`, `text == "R-01"`; the wrapped form `{"workflow": {...}}` returns the same set; reordering the list yields the same `requirement_digest`; missing/empty/non-list requirements, an id-less or non-mapping entry, an unknown category, and a duplicate id each raise `ValueError` naming its `RF-E00N` code; the existing `freeze_requirements` outputs are unchanged (unit tests in `tests/test_run_freeze.py`, E-10).
  - Execution state: pending

- [ ] E-08 Wire `run_cli._run_init` (from `v47z9u` E-03) to freeze and append the `requirement_set`. Call `frozen = run_freeze.freeze_workflow_requirements(wf)` during `v47z9u` E-04's validate-before-write phase (before the run directory is reserved), mapping `ValueError` to exit 2 `EXIT_INVALID_INVOCATION` with the finding text and NO filesystem write. Replace `v47z9u`'s placeholder `"requirement_digest": compute_record_hash(workflow.get("requirements", []))` on the header with `frozen.requirement_digest`, then append `run_freeze.requirement_set_record(run_id, 1, "runtime", "", "", frozen)` through the SAME `RunLedgerStore` instance (the store overwrites `seq`/`prev_hash` and fills the empty `timestamp`; measured at review: appended records came back `seq` 0/1 with real timestamps and `validate_records` ok). Hold both appends under one `writer_lock` with `append_held` so no other writer can interleave between header and set, and extend `v47z9u`'s cleanup-on-failure so a failed second append removes the reserved directory (a header without its set would be a ledger that can never complete). BEHAVIOR CHANGE TO DECLARE: a workflow whose `requirements` list is empty or absent, which `v47z9u` accepts, is now refused at init; this is intended (such a run could never reach `finalize` 0) and is stated in the CHANGELOG line (E-07). Under `o34rb3` (if it has executed first), its `workflow.json` write stays inside the same reserved directory and ordering.
  - Depends on: E-02
  - Expected outcome: `aw run init --workflow wf.json` writes exactly two records (`kind: "run"` seq 0, `kind: "requirement_set"` seq 1) with identical `requirement_digest` and the workflow's requirement ids, accepted by `run_ledger_schema.validate_records`; an empty or id-less `requirements` exits 2 and leaves `state_root(repo)` with no new entry.
  - Execution state: pending

### Task group 2: add the `aw run verify` CLI writer

- [ ] E-03 Add `_run_verify(args: argparse.Namespace) -> int` in `agent_workflows/run_cli.py`. Resolve the ledger path via `_resolve_or_error(args)` and construct the engine via `_build_engine(args, ledger_file)`. Require `--requirement <req-id>` and `--result <satisfied|partial|failed|not_verifiable>` (checked against `run_ledger_schema.VERIFIER_RESULTS`), returning `_emit_error(..., EXIT_INVALID_INVOCATION)` (exit 2) when either flag is missing or `--result` is outside `VERIFIER_RESULTS`. Check that `req_id` belongs to the run's FROZEN requirements, read ONLY from the `requirement_set` records in `_records` (what `run_evidence.evaluate_completion` counts), never from `--workflow` (a workflow can name a requirement the run never froze, and recording a decision for it would never move completion; the engine itself accepts any string, measured at review: `record_verifier_decision("R-99", ...)` appended). A ledger with no `requirement_set` (pre-`um0twl`, or hand-seeded) refuses every `--requirement` with exit 2 naming `no frozen requirements`. Also refuse with `EXIT_OPERATIONAL` (6) when `snapshot.state in run_state.TERMINAL_STATES` (a decision appended after `complete` or `cancelled` changes nothing and the engine does not refuse it, measured at review). On unknown, returning `_emit_error(args, f"unknown requirement '{req_id}'", EXIT_INVALID_INVOCATION)` (exit 2) if unknown. Default `actor = getattr(args, "actor", None) or "verifier"` and call `engine.record_verifier_decision(req_id, result=result, actor=actor)`, catching `run_state.RunStateError` (including `UnauthorizedActorError` when `--actor != "verifier"`) and `store.LedgerLockError` as `EXIT_OPERATIONAL` (exit 6), and `store.LedgerCorruption` as `EXIT_CORRUPTED_LEDGER` (exit 5). Reconstruct state (`snapshot = engine.reconstruct_state()`). In machine mode (`--agent` / `--json`), emit `_snapshot_payload(snapshot)` with `"recorded_decision": {"requirement": req_id, "result": result, "actor": actor}`. In human mode, print `f"Recorded verifier decision: {req_id} -> {result}"`. Return `EXIT_OK` (0) when `result == "satisfied"` and `EXIT_BLOCKED` (3) when `result in ("partial", "failed", "not_verifiable")`. Validate `--result` BEFORE calling the engine: an invalid result otherwise surfaces as `SchemaInvalidRecordError`, a `LedgerCorruption` subclass, which this handler would map to exit 5 ("corrupted") for an operator typo. A later decision for the same requirement supersedes an earlier one (the snapshot and `evaluate_completion` keep the last, measured: `satisfied` then `failed` reads `failed`), so re-verifying is the correction path and needs no flag.
  - Depends on: E-08
  - Expected outcome: `_run_verify` appends a schema-valid `kind: "verifier_decision"` record via `RunEngine.record_verifier_decision` and exits in the documented `run_cli.EXIT_*` class for each positive and refusal case.
  - Execution state: pending

- [ ] E-04 Register `aw run verify` in `agent_workflows/cli.py` and declare it in `agent_workflows/command_surface.py`. In `cli._build_parser()`: add a `("verify", <help>, <desc>)` row to `_run_leaf_specs` (the registrar's signature is `_register_run_leaf(group, name, help_text, desc)`, called in the `for _leaf_name, ... in _run_leaf_specs` loop; it takes no handler, routing is by `run_command` in `run_cli.run_cli`), so `verify` lands on `run_sub` because it is not in `run_viewer.RUNS_VIEWER_LEAF_NAMES`; inside `_register_run_leaf` add `--workflow` (it reaches `_build_engine`), `--actor` (add `"verify"` to the existing `if name in ("start", "record", "cancel", "finalize")` tuple; leave its `default=None`, the handler defaults to `verifier`), and an `if name == "verify":` block adding `--requirement` (`help="Requirement id to verify (e.g. R-01)."`), `--result` (`help="Verifier result: satisfied, partial, failed, or not_verifiable."`), and `--result`; add `if sub == "verify": return _run_verify(args)` to `run_cli.run_cli` and `verify` to its usage string; list `aw run verify <target> --requirement <id> --result <verdict>` in `p_run`'s help epilog. In `command_surface.COMMAND_INVENTORY`, add a declaration matching its siblings' REAL fields (the authored `requires_apply`/`supports_check`/`supports_json`/`supports_agent`/`notes` keywords do not exist on `CommandDeclaration` and would raise `TypeError` at import): `CommandDeclaration(command="run verify", command_class="mutation", human_recipe="status", agent_record_kind="result", mutation_gate="none", empty_error_renderer="renderer_boundary", legacy_flags=("--workflow", "--actor", "--requirement", "--result", "--agent", "--json"), exit_contract=(0, 2, 3, 5, 6))`, modeled on `run record`.
  - Depends on: E-03
  - Expected outcome: `aw run verify --help` exits 0 listing `target`, `--requirement`, `--result`, `--actor`, `--workflow`, `--dir`; `discover_parser_leaves` includes `"run verify"`; `get_declaration("run verify").exit_contract == (0, 2, 3, 5, 6)`; `tests/test_conformance_matrix_structure.py` and `tests/test_command_surface_declarations.py` pass. `verify` collides with no existing leaf (review probe: the only `verify` leaf is `runs verify-ledger`).
  - Execution state: pending

### Task group 3: tests, conformance registries, and docs

- [ ] E-05 Add CLI behavioral coverage, asserting outcomes only (never source text). (b) In `tests/test_run_init.py` (created by `v47z9u` E-05; its scratch repos contain `.aw/records/`), assert `aw run init --workflow wf.json` creates two records (`["run", "requirement_set"]`) accepted by `run_ledger_schema.validate_records` with matching `requirement_digest` and `R-01` in `requirements`, drive the complete sequence (`init`, `start`, `record --state performed`, `verify-ledger` exit 1 naming `unsatisfied requirements: ['R-01']`, `verify --requirement R-01 --result satisfied` exit 0, `verify-ledger` exit 0 with `Completion Predicates: SATISFIED`, `finalize` exit 0 with `finalized: true` and `run_state: "complete"`, and `status` exit 0), and check that an empty or id-less `requirements` list in `wf.json` exits 2 and writes nothing; show the sequence failing on the base commit (`invalid choice: 'verify'`). (c) In `tests/test_run_recovery_cli.py`, add `("run", "verify", True)` to `TestLedgerResolutionAndWrongFormatVerdict.REFUSAL_LEAVES` and update the count prose that test class carries ("Ten of them", "four of the ten leaves WRITE") to eleven and five; add `run verify` rows to `TestRunCliSubcommands.INVOCATIONS` (whose `incomplete` seed already carries `_requirement_set(["R-01"])`) for exit 2 (missing `--requirement`/`--result`, invalid `--result bogus` with the ledger byte-identical afterwards, unknown `--requirement R-99`), exit 3 (`--result failed`), exit 6 (`--actor executor`; and on the `complete` seed, a decision on a terminal run), and exit 0 (`--result satisfied --json` carrying `recorded_decision`); and add one test asserting a fresh `RunEngine` reconstructs `verifier_decisions == {"R-01": "satisfied"}` after the CLI call. Test function names here are non-binding pointers.
  - Depends on: E-04, E-10
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_run_init.py tests/test_run_recovery_cli.py` passes with all new and updated assertions green, and the end-to-end sequence is shown failing on the base commit.
  - Execution state: pending

- [ ] E-10 Create `tests/test_run_freeze.py` (no test module covers `run_freeze` today; measured at review, only `tests/test_agy_runipd_cli.py` imports it) with unit cases for every E-02 expected outcome, including that `freeze_requirements({"must": ["x"]})` still yields `M-01`.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_run_freeze.py` passes, each case named for the outcome it asserts.
  - Execution state: pending

- [ ] E-06 Update the CLI conformance and boundary registries in `tests/conformance_matrix.py`, `tests/test_exit_vocabulary_boundary.py`, and `tests/test_usage_refusal_agent_record.py`. Add `"run verify"` to `MUTATION_EXEMPTION_REGISTRY` in `tests/conformance_matrix.py` (`reason_kind="arg_fixture_needed"`, `citation="positional argument required"`, `reason="Requires target positional argument."`, matching `run start`/`record`/`cancel`/`finalize`; live conformance scenario conversion is tracked by backlog `a4tjxc`). Add `"run verify"` to `OUT_OF_RANGE_DECLARATION_ALLOWLIST` in `tests/test_exit_vocabulary_boundary.py` (`codes 0, 2, 3, 5, 6`). Increment the expected `REQUIRED_LEAVES` count in `tests/test_usage_refusal_agent_record.py` (`test_exclusion_set_size_and_members`) by exactly one from its value at execution HEAD (re-derive it; `v47z9u` E-08 also bumps it, so do not assume 67 or 68), so `run verify` is exercised by `test_required_arg_leaf_agent_mode` and `test_required_arg_leaf_json_mode`. Add `"verify"` to the exact `aw run <TAB>` expectation in `tests/test_completion.py` (the "WRITING noun's own first slot" row, which pins the list with `equals` and which `v47z9u` E-08 extends with `init`). If plan `g5s94t` has already executed, also extend its writer test in `tests/test_live_conformance_sweep.py` only if it enumerates writers by a computed list (it names four explicitly, so no change is expected); record which case applied.
  - Depends on: E-05
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_command_surface_declarations.py tests/test_conformance_matrix_structure.py tests/test_agent_surface_conformance.py tests/test_exit_vocabulary_boundary.py tests/test_usage_refusal_agent_record.py tests/test_shared_flag_honored.py tests/test_completion.py` passes.
  - Execution state: pending

- [ ] E-07 Document `aw run verify` in `docs/cli-output-contract.md` Section 3.1 ("Run-Execution Exit Vocabulary"; the authored "Section 3.3" does not exist): add `run verify` to the parentheticals of codes `0`, `2`, `3`, `5` and `6` in table 1. Add a `CHANGELOG.md` entry under the top pending release section (there is no `Unreleased` heading; the file's open sections are `2.0.0 (pending)` and `1.3.0 (pending)`) covering `aw run verify`, the `requirement_set` now written by `aw run init`, and the new init refusal of an empty `requirements` list (no em or en dashes in either).
  - Depends on: E-06
  - Expected outcome: the `docs/cli-output-contract.md` and `CHANGELOG.md` diffs, with no em or en dashes.
  - Execution state: pending

- [ ] E-09 Run `aw sanitize --agent` and the bare test suite `python3 -m pytest`.
  - Depends on: E-07
  - Expected outcome: `aw sanitize --agent` reports `"outcome":"clean"` (exit 0) and bare `python3 -m pytest` passes with zero failures.
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
| F-06 | Adding a new `aw run <leaf>` with positional `target` and exit contract `(0, 2, 3, 5, 6)` touches six test/declaration surfaces beyond `cli.py` and `run_cli.py`. | `command_surface.COMMAND_INVENTORY` (`test_command_surface_declarations.py`, `test_conformance_matrix_structure.py`), `MUTATION_EXEMPTION_REGISTRY` in `tests/conformance_matrix.py`, `OUT_OF_RANGE_DECLARATION_ALLOWLIST` in `tests/test_exit_vocabulary_boundary.py`, `REQUIRED_LEAVES` in `tests/test_usage_refusal_agent_record.py`, `REFUSAL_LEAVES` in `tests/test_run_recovery_cli.py`, and the exact `aw run <TAB>` list in `tests/test_completion.py` (`equals ["as", "cancel", "finalize", "ipd", "record", "start"]`, which `v47z9u` E-08 extends with `init`). |
| F-07 | END-TO-END FEASIBILITY, measured at review (HEAD `252e476c5`) because `aw run init` and `aw run verify` do not exist yet: in a scratch repo with `.aw/records/`, a `kind: "run"` header plus a `requirement_set` built from a simulated R-NN-preserving freezer and `run_freeze.requirement_set_record(..., seq=1, timestamp="")` were appended through `RunLedgerStore.append`; the store assigned seq 0/1 and real timestamps and `validate_records` returned ok, header and set digests equal. Then via the real CLI: `runs verify-ledger` exit 1 `unsatisfied requirements: ['R-01']` and `no step attempts recorded`; `run start` 0; `run record --state performed` 0; `verify-ledger` exit 1 `unsatisfied requirements: ['R-01']`; after `RunEngine.record_verifier_decision("R-01", "satisfied", actor="verifier")`, `verify-ledger` exit 0 `Completion Predicates: SATISFIED`; `runs status` exit 1 (`running`); `run finalize --json` exit 0 `finalized: true`, `run_state: "complete"`; `runs status` exit 0 with and without `--workflow`. So the plan's goal is reachable with no change beyond the two writers. | Review probe (deleted afterwards). |
| F-08 | `RunEngine.record_verifier_decision` validates only the actor: it appended a decision for an unfrozen `R-99`, appended one on a CANCELLED run, and a later decision supersedes an earlier one (`satisfied` then `failed` reads `failed`). An invalid `result` raises `SchemaInvalidRecordError`, a `LedgerCorruption` subclass. | Review probe; `run_engine.RunEngine.record_verifier_decision`; `run_ledger_store.SchemaInvalidRecordError(LedgerCorruption)`. E-03 adds the frozen-id, terminal-run and pre-engine `--result` checks. |
| F-09 | `freeze_requirements` binds the CATEGORY (not the id) into each item digest (`_digest(category, normalized)`), and the drop/redefine checks (`diff_requirements`, `refuse_drop_or_redefine`) compare by id over those digests. The authored digest over `(category, id, text)` would diverge from the module's semantic-identity rule. A compiled workflow wraps its body as `{"workflow": {...}}` (`run_engine._normalize_workflow` unwraps it), and `wrapped.get("requirements")` is `None` (measured). `workflow_schema` requires `R-NN` ids and a non-empty `text` for compiled workflows, but `run_cli` accepts any JSON object as `--workflow`. | `agent_workflows/run_freeze.py` (`_digest`, `freeze_requirements`, `diff_requirements`); `agent_workflows/run_engine.py` `_normalize_workflow`; `agent_workflows/workflow_schema.py` `_validate_requirements`. |
| F-10 | The authored E-04 and docs referenced things that do not exist: `_register_run_leaf(run_sub, "verify", ..., _lazy(...))` (the real signature is `(group, name, help_text, desc)`, driven by `_run_leaf_specs`, with no handler argument); `CommandDeclaration(requires_apply=..., supports_check=..., supports_json=..., supports_agent=..., notes=...)` (none of those fields exist; the dataclass would raise `TypeError` at import); `command_surface._DECLARATIONS` (it is `COMMAND_INVENTORY`); `docs/cli-output-contract.md` Section 3.3 (the run vocabulary is Section 3.1; 3.2 is severity tiers); a CHANGELOG `Unreleased` heading (none; open sections are `2.0.0 (pending)` and `1.3.0 (pending)`). | `agent_workflows/cli.py` `_register_run_leaf`, `_run_leaf_specs`; `agent_workflows/command_surface.py` `CommandDeclaration`, `COMMAND_INVENTORY`; `docs/cli-output-contract.md` headings; `CHANGELOG.md` headings. |

## Proposed changes (ordered, validatable)

1. Reproduce the baseline `M-01` id mismatch, `"no frozen requirements defined"` after `aw run init`, and missing `aw run verify` leaf (E-01).
2. Add `run_freeze.freeze_workflow_requirements(workflow)` preserving the workflow's requirement ids (E-02).
3. Wire `run_cli._run_init` to append `kind: "requirement_set"` (`seq=1`) under one writer lock with matching `requirement_digest` (E-08).
4. Implement `run_cli._run_verify` (E-03), and register/declare `aw run verify` in `cli.py`, `run_cli.run_cli` and `command_surface.py` (E-04).
5. Behavioral tests (E-05), census/registry tests (E-06), docs and CHANGELOG (E-07), sanitize and the bare suite (E-09).

## Deferred / out of scope (with reason)

- Persisting the workflow beside the ledger so later step-DAG leaves (`start`, `record`, `next`) do not require `--workflow` repeated.
  - Carrier: sflov4 (plan `o34rb3`). No ordering edge is needed: both plans edit `_run_init`, and E-08 states how the two writes coexist.
- Rendering a ledger-only run directory in the `aw runs` summary viewer instead of showing `0 steps`.
  - Carrier: nf84rt
- Replacing the `not_runnable` and `arg_fixture_needed` exemptions for ledger leaves in `tests/conformance_matrix.py` with live conformance-harness scenario rows.
  - Carrier: a4tjxc (plan `g5s94t`). That plan's writer test expects `run finalize` exit 1 ("no frozen requirement set, `8l1hgw`"); after this plan the reason becomes `unsatisfied requirements` and the code stays 1, so no edit is needed there unless it asserts the reason text.
- A `--clear` / revoke for a verifier decision: a later decision already supersedes (F-08).
  - Carrier: none needed.

## Scope check

- Over-scope: none.
- Under-scope: closed at review: frozen-id, terminal-run and pre-engine `--result` checks (F-08), the compiled-wrapper unwrap and digest alignment (F-09), the corrected registration/declaration/doc anchors (F-10), the completion-census file and new `tests/test_run_freeze.py` (F-06), atomic two-record init, the empty-requirements behavior change, and splitting init wiring from the freezer (E-08). Both halves named in backlog `8l1hgw` (`requirement_set` writer preserving workflow `R-NN` ids and `verifier_decision` CLI leaf calling `RunEngine.record_verifier_decision`) are delivered and verified end-to-end through `aw run finalize` exit 0.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_run_freeze.py tests/test_run_init.py tests/test_run_recovery_cli.py`
- `python3 -m pytest -o addopts="" tests/test_command_surface_declarations.py tests/test_conformance_matrix_structure.py tests/test_agent_surface_conformance.py tests/test_exit_vocabulary_boundary.py tests/test_usage_refusal_agent_record.py tests/test_shared_flag_honored.py tests/test_completion.py`
- Invariants and their tests: header and set digests equal by construction (E-05 b); a decision for an unfrozen id never lands (E-05 c); a typo'd `--result` never reads as corruption (E-05 c); the existing `M-NN` freezer is unchanged (E-10); a refused init writes nothing (E-05 b).
- Bare full test suite: `python3 -m pytest`
- Leak sanitizer: `aw sanitize --agent`

## Spec / documentation sync

`docs/cli-output-contract.md` Section 3.1 is updated to list `aw run verify` in the code `0`, `2`, `3`, `5` and `6` parentheticals alongside `aw run start`, `aw run record`, `aw run cancel`, and `aw run finalize`, and `CHANGELOG.md` gains an entry under the top pending release. `aw run verify` emits bare JSON under `--agent`/`--json` like its four siblings (`run_cli._emit_machine`), which Section 3.1 already describes for the family; no `aw.agent/v1` record is promised. Spec `25kzda` requires no changes here because its run-ledger storage location bullet in Section 6.2 is updated by `v47z9u` and its Section 1.2 / 5.1 scope language is updated by `9epp40`.

## Open questions

### OQ-01: Should `requirement_set` be written by `aw run init` at ledger creation or by a separate CLI subcommand?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: `aw run init` writes the `requirement_set` record at `seq=1` immediately after the `kind: "run"` header (`seq=0`). `aw run init` already requires `--workflow PATH` and computes `requirement_digest` from the workflow's `requirements` list (`v47z9u` E-03), and `v47z9u` OQ-02 deferred appending `requirement_set` in `aw run init` to `8l1hgw` solely because `run_freeze` minted `M-NN` ids instead of preserving the workflow's `R-NN` ids. Writing `requirement_set` in `aw run init` guarantees `run.requirement_digest == requirement_set.requirement_digest` by construction and allows `run_cli._reconstruct_workflow_from_ledger` to recover the frozen requirement ids without requiring `--workflow` on subsequent `aw run verify`, `aw runs status`, `aw runs verify-ledger`, or `aw run finalize` calls. Demonstrated at review (F-07): with a seq-1 `requirement_set`, the full chain reached `finalize` exit 0 and `runs status` exit 0 without `--workflow`. Reversible.

### OQ-02: What exit code should `aw run verify` return when recording a non-satisfied verdict (`partial`, `failed`, or `not_verifiable`)?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Return `EXIT_BLOCKED` (`3`) when `result in ("partial", "failed", "not_verifiable")` and `EXIT_OK` (`0`) when `result == "satisfied"`. This mirrors `_run_record` (`run_cli.py`), which appends a `failed` or `blocked` step attempt to the ledger and returns `EXIT_BLOCKED` (`3`) so scripts cannot mistake a recorded failure for a green step. Reversible.

### OQ-03: Which requirement ids may `aw run verify` record a decision for?

- Blocking: no
- Status: resolved
- Owner: plan reviewer
- Resolution or deferral rationale: Only ids present in the run's `requirement_set` records, refusing anything else with exit 2. Basis: `run_evidence.evaluate_completion` counts only frozen ids, so a decision for any other id is inert, and the engine would append it unchecked (F-08, measured). Reading ids from `--workflow` instead was rejected because a workflow can name a requirement the run never froze. A ledger with no `requirement_set` therefore cannot be verified through this leaf, which is correct: it can never complete either. Reversible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted outputs from the baseline reproduction commands in E-01 (`freeze_requirements` minting `M-01`, `verify-ledger` reporting `"no frozen requirements defined"`, `aw run verify` failing with exit 2 `invalid choice`, and the header's placeholder `requirement_digest`).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the `agent_workflows/run_freeze.py` diff, and a pasted Python one-liner calling `freeze_workflow_requirements` on the plain and wrapped forms of a one-requirement workflow showing the same `requirement_digest` and `id == "R-01"`.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: pasted output from running `aw run init --workflow wf.json` in a scratch repo with `.aw/records/` (via `run_cli._run_init` -> `run_freeze.freeze_workflow_requirements`, wired in E-08) showing the two ledger records (`kind: "run"` at `seq=0` and `kind: "requirement_set"` at `seq=1`) with matching `requirement_digest`, `R-01` in `requirements`, and `run_ledger_schema.validate_records` returning `ok=True`; plus a pasted init with `"requirements": []` exiting 2 and a before/after listing of `state_root(repo)` that is identical.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: pasted passing output of `python3 -m pytest -o addopts="" -v tests/test_run_freeze.py` covering each E-02 expected outcome (id preservation, wrapper unwrap, order-independent set digest, each `RF-E00N` refusal, `freeze_requirements` still yielding `M-01`).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted output from exercising `run_cli._run_verify` (added in E-03, wired in E-04) in a scratch repo showing `aw run verify <id> --requirement R-01 --result satisfied` exiting 0 and appending a `kind: "verifier_decision"` record (`actor: "verifier"`), `aw run verify <id> --requirement R-01 --result failed` exiting 3, `aw run verify <id> --requirement R-01 --result satisfied --actor executor` exiting 6, `aw run verify <id> --requirement R-99 --result satisfied` exiting 2, `--result bogus` exiting 2 (not 5) with the ledger unchanged, and a verify on a finalized run exiting 6.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: the `cli.py`, `run_cli.py` dispatcher and `command_surface.py` diffs, pasted `aw run verify --help` output showing `--requirement`, `--result`, `--actor` and `--workflow`, `aw run --help` showing the `aw run verify <target>` example, and a one-liner confirming `"run verify"` in `command_surface.discover_parser_leaves(cli._build_parser())` and `command_surface.get_declaration("run verify").exit_contract == (0, 2, 3, 5, 6)`.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted `python3 -m pytest -o addopts="" -v tests/test_run_freeze.py tests/test_run_init.py tests/test_run_recovery_cli.py` output showing all cases passing, including the full `init -> start -> record -> verify -> verify-ledger -> finalize -> status` sequence reaching exit 0 and `run_state: "complete"`, and the pasted base-commit failure of that sequence.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: the four registry/census diffs (with the `REQUIRED_LEAVES` old value measured at execution HEAD and the new value one higher), and pasted `python3 -m pytest -o addopts="" tests/test_command_surface_declarations.py tests/test_conformance_matrix_structure.py tests/test_agent_surface_conformance.py tests/test_exit_vocabulary_boundary.py tests/test_usage_refusal_agent_record.py tests/test_shared_flag_honored.py tests/test_completion.py` output passing with 0 failures.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted `git diff -- docs/cli-output-contract.md CHANGELOG.md` showing the Section 3.1 parentheticals and the CHANGELOG entry, with no em or en dashes.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: pasted `aw sanitize --agent` output reporting `"outcome":"clean"`, and the pasted bare `python3 -m pytest` summary line with 0 failures (any failing node id must be shown to fail identically on the base commit to be excused).
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval and after prerequisite plan `v47z9u` is `executed` (`- Item-Dependencies: executed:v47z9u`). Open questions: all resolved. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit um0twl -- <paths>`; never push. Paste the actual runner output for every test claim; a claim without pasted output is not evidence. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize um0twl` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` is `pass`. Do not hand-move the file to `executed/`.
