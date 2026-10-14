# IPD: Add ledger leaves to LIVE_SAFE_LEAVES once aw run init lands

- Date: 2026-10-14
- Kind: child
- Concern: `tests/conformance_matrix.py` exempts the eight `aw runs` subcommands (`runs decisions`, `runs evidence`, `runs next`, `runs questions`, `runs resume`, `runs show`, `runs status`, `runs verify-ledger`) in `EXEMPTION_REGISTRY` with the pre-`v47z9u` reason `"Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace."`, exempts the four `aw run` write leaves (`run start`, `run record`, `run cancel`, `run finalize`) in `MUTATION_EXEMPTION_REGISTRY` with `"Requires target positional argument."`, and omits all eight `aw runs` leaves from `LIVE_SAFE_LEAVES` (`covered_by="declaration"` in `build_matrix`). Once plan `v47z9u` (`hegwri`) lands `aw run init`, the conformance harness can initialize a real `ledger.jsonl` on disk in its session template and live fixture directory, making the eight `aw runs` leaves live conformance scenario rows in `LIVE_SAFE_LEAVES`, wiring `aw run init` into `MUTATION_UNIVERSE`, driving the four `aw run` ledger writers live against the initialized ledger, and replacing the stale `EXEMPTION_REGISTRY` / `MUTATION_EXEMPTION_REGISTRY` rationales with the measured contract citations. Backlog `a4tjxc`.
- Scope: (1) In `tests/conformance_matrix.py`, add `seed_ledger_fixture` (invoking `aw run init --workflow wf.json --run-id run-abcdef1234` and seeding Set projection files `decisions.md` and `open-questions.md`), call it from `build_installed_project_template`, expose `ledger_run_id`, `ledger_path`, and `workflow_path` on `InstalledProjectTemplate` and `IsolatedProject`, add `live_leaf_argv`, add the eight `aw runs` leaves to `LIVE_SAFE_LEAVES`, add `"run init": ["--workflow", "wf.json"]` to `RUNNABLE_ARGV`, and update the eight `EXEMPTION_REGISTRY` and four `MUTATION_EXEMPTION_REGISTRY` entries to cite `docs/cli-output-contract.md Section 3.1` and `agent_workflows/run_cli.py`. (2) In `tests/test_agent_surface_conformance.py`, pass `RUNNABLE_ARGV.get(leaf, [])` in `test_agent_surface_conformance_mutation` so `run init` executes in `MUTATION_UNIVERSE` with its required `--workflow` flag. (3) In `tests/test_exit_contract_conformance.py` and `tests/test_live_conformance_sweep.py`, wire the session-scoped `live_ledger_dir` fixture through `live_leaf_argv` so `test_live_safe_leaves_exit_contract_membership_cheap` and `test_no_color_scenario_is_plain_cheap_leaves` drive all eight `aw runs` leaves against the `aw run init` ledger, and add non-vacuous live conformance tests for the eight `aw runs` leaves and four `aw run` mutation leaves (`run start`, `run record`, `run cancel`, `run finalize`). OUT: migrating `run_cli._emit_machine` from bare JSON dicts (`docs/cli-output-contract.md` Section 3.1, pinned by `tests/test_run_recovery_cli.py`) to `aw.agent/v1` envelopes or collapsing the 8-code run-execution exit vocabulary `{0..7}` into `{0, 1, 2}`; writing `requirement_set` / `verifier_decision` records (`8l1hgw`); persisting `wf.json` beside the ledger (`sflov4`); viewer rendering of ledger-only directories (`nf84rt`).
- Scope-Paths: tests/conformance_matrix.py, tests/test_live_conformance_sweep.py, tests/test_exit_contract_conformance.py, tests/test_agent_surface_conformance.py
- Item-Dependencies: executed:v47z9u
- Status: to-review
- From-Backlog: a4tjxc
- Work-Kind: chore
- Priority: low
- Set: runledger
- Order: 5
- Highest E allocated: 06
- Author: agent:antigravity
- Id: g5s94t

## Workflow history
- 2026-10-14 to-review (agent:antigravity): authored review-ready IPD from backlog a4tjxc

- 2026-10-14 draft (agent:antigravity): created.

## Goal

Promote the eight `aw runs` subcommands (`runs decisions`, `runs evidence`, `runs next`, `runs questions`, `runs resume`, `runs show`, `runs status`, `runs verify-ledger`) to `LIVE_SAFE_LEAVES` (`covered_by="live"`) backed by an `aw run init` ledger fixture, wire `aw run init` into `MUTATION_UNIVERSE`, drive the four `aw run` ledger writers live against the fixture ledger, and replace the stale pre-`v47z9u` `EXEMPTION_REGISTRY` / `MUTATION_EXEMPTION_REGISTRY` reasons with the measured contract citations.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reproduce and verify dependency

- [ ] E-01 REPRODUCE at execution HEAD. Verify prerequisite `v47z9u` has landed by running `aw run init --help` (expect exit 0) and checking that `tests/conformance_matrix.py` still omits the eight `aw runs` leaves (`runs decisions`, `runs evidence`, `runs next`, `runs questions`, `runs resume`, `runs show`, `runs status`, `runs verify-ledger`) from `LIVE_SAFE_LEAVES` (`build_matrix` reports `covered_by == "declaration"` for all eight). If `aw run init` is absent or the eight leaves are already `covered_by == "live"`, stop and report the plan as blocked or overtaken with pasted output.
  - Depends on: none
  - Expected outcome: pasted `aw run init --help` output (exit 0) and a one-liner probe confirming all eight `aw runs` leaves have `covered_by == "declaration"` in `conformance_matrix.build_matrix()`.
  - Execution state: pending

### Task group 2: conformance matrix fixture, LIVE_SAFE_LEAVES, and registry truth

- [ ] E-02 Add `LEDGER_FIXTURE_RUN_ID = "run-abcdef1234"`, `LEDGER_FIXTURE_WORKFLOW`, `seed_ledger_fixture(root: Path, run_id: str = LEDGER_FIXTURE_RUN_ID) -> Tuple[Path, Path]`, and `live_leaf_argv(leaf: str, ledger_fixture_dir: Optional[Path] = None) -> List[str]` in `tests/conformance_matrix.py`, and call `seed_ledger_fixture(project_dir)` inside `build_installed_project_template`. `seed_ledger_fixture` must: (a) write `root / "wf.json"` with a minimal one-step workflow (`S-01` satisfying `R-01`, `depends_on: []`); (b) invoke `run_cli(["run", "init", "--workflow", str(wf_path), "--run-id", run_id, "--dir", str(root)])` and assert returncode 0 and that the ledger exists at `runner_shared.state_root(root) / run_id / "ledger.jsonl"`; (c) write minimal Set projection markdown files (`decisions.md` and `open-questions.md`) under `set_records.run_artifacts_dir(root, "exec-set", run_id)` so `runs decisions` and `runs questions` resolve a valid run target without exiting 2. Expose `ledger_run_id: str`, `ledger_path: Path`, and `workflow_path: Path` on `InstalledProjectTemplate` and `IsolatedProject` (updating `clone_isolated_project` to remap `ledger_path` and `workflow_path` into `iso_project_dir`).
  - Depends on: E-01
  - Expected outcome: `build_installed_project_template` and `clone_isolated_project` produce an initialized `ledger.jsonl` via `aw run init`, `wf.json`, and Set projection files, and `live_leaf_argv` returns the runnable argv including `--dir <ledger_fixture_dir>` (and `--workflow <ledger_fixture_dir>/wf.json` for `runs next`, `runs resume`, `runs show`, `runs status`) for the eight `aw runs` leaves.
  - Execution state: pending

- [ ] E-03 Update `LIVE_SAFE_LEAVES`, `RUNNABLE_ARGV`, `EXEMPTION_REGISTRY`, and `MUTATION_EXEMPTION_REGISTRY` in `tests/conformance_matrix.py`. (a) Add `"runs decisions"`, `"runs evidence"`, `"runs next"`, `"runs questions"`, `"runs resume"`, `"runs show"`, `"runs status"`, and `"runs verify-ledger"` to `LIVE_SAFE_LEAVES` with `[LEDGER_FIXTURE_RUN_ID]`, promoting all eight to `covered_by="live"` in `build_matrix()` and `live_cheap_leaves()`. (b) Add `"run init": ["--workflow", "wf.json"]` to `RUNNABLE_ARGV`. (c) Update the six ledger-reading entries (`runs evidence`, `runs next`, `runs resume`, `runs show`, `runs status`, `runs verify-ledger`) in `EXEMPTION_REGISTRY` from the stale `"Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace."` rationale to `reason_kind="sanctioned_raw"`, `citation="docs/cli-output-contract.md Section 3.1"`, explaining that `run_cli._emit_machine` emits bare JSON dicts (pinned by `tests/test_run_recovery_cli.py`) and uses the Section 3.1 run-execution exit vocabulary `{0..7}` rather than `aw.agent/v1` envelopes. (d) Update `runs decisions` and `runs questions` in `EXEMPTION_REGISTRY` to `citation="agent_workflows/run_cli.py"`, explaining that `_run_decisions` and `_run_questions` read `set_records` markdown projections (`decisions.md`, `open-questions.md`) rather than `ledger.jsonl` and emit raw markdown via `_print_human` with no `--agent` envelope branch. (e) Update `run start`, `run record`, `run cancel`, and `run finalize` in `MUTATION_EXEMPTION_REGISTRY` to cite `docs/cli-output-contract.md Section 3.1` alongside their required step/state flags and bare-dict machine contract.
  - Depends on: E-02
  - Expected outcome: `build_matrix()` marks all eight `aw runs` leaves as `covered_by="live"`, `live_cheap_leaves()` includes all eight, `RUNNABLE_ARGV` includes `"run init"`, and no entry in `EXEMPTION_REGISTRY` claims a ledger is absent from the workspace.
  - Execution state: pending

### Task group 3: wire conformance sweeps and non-vacuous ledger leaf gates

- [ ] E-04 In `tests/test_agent_surface_conformance.py`, update `test_agent_surface_conformance_mutation` to include `RUNNABLE_ARGV.get(leaf, [])` when constructing `full_argv` (`full_argv = leaf.split() + RUNNABLE_ARGV.get(leaf, []) + ["--agent"]`, matching `tests/test_shared_flag_honored.py` `test_json_flag_honored_mutation` and `test_fields_flag_honored_mutation`), so `run init` executes in `MUTATION_UNIVERSE` against `iso.project_dir / "wf.json"` and is verified for `aw.agent/v1` schema validity, exit parity, and path-leak absence.
  - Depends on: E-03
  - Expected outcome: `test_agent_surface_conformance.py` and `test_shared_flag_honored.py` run and pass with `run init` live in `MUTATION_UNIVERSE`.
  - Execution state: pending

- [ ] E-05 In `tests/test_exit_contract_conformance.py` and `tests/test_live_conformance_sweep.py`, add a session-scoped `live_ledger_dir` fixture (calling `conformance_matrix.seed_ledger_fixture`) and wire `conformance_matrix.live_leaf_argv(leaf, live_ledger_dir)` into `test_live_safe_leaves_exit_contract_membership_cheap` (`tests/test_exit_contract_conformance.py`) and `test_no_color_scenario_is_plain_cheap_leaves` (`tests/test_live_conformance_sweep.py`). Add `test_live_ledger_read_leaves_non_vacuous_and_machine_json` and `test_live_ledger_mutation_leaves_conformance` in `tests/test_live_conformance_sweep.py` that: (a) drive all eight `aw runs` leaves against `live_ledger_dir` and assert returncode is in `{0, 1}` (never `2` not-found, `5` corrupted, or `7` wrong-format) and that the six ledger readers emit parseable JSON dicts containing `"run_id": LEDGER_FIXTURE_RUN_ID` (or `"ledger"` for `runs evidence`) with zero ANSI escapes under both `--agent` and `--json`; (b) drive the four `aw run` mutation leaves (`run start`, `run record`, `run cancel`, `run finalize`) in a fresh `clone_isolated_project` clone against the `aw run init`-seeded ledger across human, `--agent`, `--json`, and `run_cli_tty(..., no_color=True)` modes, asserting returncodes are in each leaf's declared `exit_contract` (`0` for `start`, `record`, `cancel`; `1` for `finalize`, never `2`), `--agent` and `--json` outputs parse as JSON dicts with zero ANSI escapes, and `no_color=True` TTY output contains zero ANSI escapes.
  - Depends on: E-04
  - Expected outcome: `test_conformance_matrix_structure.py`, `test_exit_contract_conformance.py`, `test_live_conformance_sweep.py`, `test_agent_surface_conformance.py`, and `test_shared_flag_honored.py` all pass with the eight `aw runs` leaves in `LIVE_SAFE_LEAVES`, `run init` in `MUTATION_UNIVERSE`, and the four `aw run` mutation leaves verified live against the `aw run init` ledger.
  - Execution state: pending

- [ ] E-06 Run `aw sanitize --agent` and the bare test suite (`python3 -m pytest`) and paste the actual runner outputs.
  - Depends on: E-05
  - Expected outcome: `aw sanitize --agent` reports `"outcome": "clean"` (exit 0) and bare `python3 -m pytest` passes with zero failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Run the full test suite bare as `python3 -m pytest` (no `-n0`, no extra `-q`, no `-p no:randomly`). For targeted test runs during development, use `python3 -m pytest -o addopts="" <test_files>`.
- Tests must test observable behavior and outcomes by driving CLI commands or functions; never inspect production source code via `inspect`, `ast`, regex, or line counts (P16).
- Cite code by SYMBOL (`module.function` or `module.CONSTANT`) or quoted content string, never by bare line numbers (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Commit only modified paths through `aw commit <plan-id6> -- <paths>`; never push.
- Run `aw sanitize --agent` to verify no local paths or machine identifiers leak into tracked artifacts.

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | `LIVE_SAFE_LEAVES` and `EXEMPTION_REGISTRY` govern two distinct gates in `tests/conformance_matrix.py`. `build_matrix(parser)` marks a leaf's scenario rows (`tty`, `non_tty`, `agent`, `no_color`, `help`, `usage_error`, `json`, `domain_failure`) as `covered_by="live"` iff `decl.command in LIVE_SAFE_LEAVES`, which is consumed by `test_conformance_matrix_structure.py`, `test_live_conformance_sweep.py`, and `test_exit_contract_conformance.py`. By contrast, `EXEMPTION_REGISTRY` and `MUTATION_EXEMPTION_REGISTRY` are consumed only by `test_agent_surface_conformance.py` and `test_shared_flag_honored.py` to gate `aw.agent/v1` envelope schema conformance (`agent_schema.validate_agent_record`). Other leaves with non-`aw.agent/v1` machine output (such as `research check-miscategorized`) are simultaneously members of `LIVE_SAFE_LEAVES` and `EXEMPTION_REGISTRY` (`reason_kind="sanctioned_raw"`). | `tests/conformance_matrix.py` (`LIVE_SAFE_LEAVES`, `EXEMPTION_REGISTRY`, `build_matrix`), `tests/test_conformance_matrix_structure.py` (`UndeclaredLeafGuardTests.test_matrix_has_at_least_one_passing_row_per_live_leaf`), `tests/test_live_conformance_sweep.py`, `tests/test_exit_contract_conformance.py`, `tests/test_agent_surface_conformance.py` (`compute_conformance_universe`, `compute_mutation_conformance_universe`). |
| F-02 | Even against a valid `ledger.jsonl`, none of the six ledger-reading leaves (`runs evidence`, `runs next`, `runs resume`, `runs show`, `runs status`, `runs verify-ledger`) or four ledger-writing leaves (`run start`, `run record`, `run cancel`, `run finalize`) emits an `aw.agent/v1` envelope record under `--agent`. `run_cli._emit_machine` emits bare JSON dicts (`json.dumps(redacted, sort_keys=True)`) and uses the 8-code run-execution exit vocabulary `{0..7}` documented in `docs/cli-output-contract.md` Section 3.1 and pinned by `tests/test_run_recovery_cli.py` (`TestRunCliSubcommands`, `TestLedgerResolutionAndWrongFormatVerdict.test_both_machine_renderers_carry_the_suggestion_as_data`, `test_an_unknown_target_keeps_the_bare_machine_shape`). | `agent_workflows/run_cli.py` (`_emit_machine`, `_emit_error` F-16 note), `agent_workflows/command_surface.py` (`runs next`, `runs resume` comments), `docs/cli-output-contract.md` Section 3.1, `tests/test_exit_vocabulary_boundary.py` (`RUN_EXECUTION_MULTI_CODE_COMMANDS`), `tests/test_run_recovery_cli.py`. |
| F-03 | Two of the eight `aw runs` leaves (`runs decisions` and `runs questions`) do not read `ledger.jsonl` at all: `run_cli._run_decisions` and `run_cli._run_questions` call `_projection_dir(args)` -> `set_records.run_artifacts_dir(Path(repo_root), workflow, run_id)` and read `.aw/workflow-artifacts/<workflow>/<run-id>/decisions.md` and `open-questions.md`, printing raw markdown via `_print_human` unconditionally with no `_machine(args)` branch. Their current `EXEMPTION_REGISTRY` entries falsely cite `agent_workflows/run_ledger_store.py` and `"Requires an on-disk hash-chained ledger.jsonl file..."`. | `agent_workflows/run_cli.py` (`_projection_dir`, `_run_decisions`, `_run_questions`), `agent_workflows/set_records.py` (`run_artifacts_dir`). |
| F-04 | Against a valid ledger (`run-abcdef1234`) initialized with a 1-step workflow `wf.json` (`S-01` satisfying `R-01`, `depends_on: []`) and seeded Set projection files (`decisions.md`, `open-questions.md`), all eight `aw runs` leaves and all four `aw run` mutation leaves satisfy every `LIVE_SAFE_LEAVES` and live conformance invariant: `--help` exits 0; `USAGE_ERROR_FLAG` exits 2; `run_cli_tty(..., no_color=True)` emits zero ANSI escapes; and human + `--agent` returncodes fall inside `decl.exit_contract` while specifically avoiding missing-target exit `2` (`runs evidence`: 0, `runs next --workflow wf.json`: 0, `runs resume --workflow wf.json`: 0, `runs decisions`: 0, `runs questions`: 0, `runs show --workflow wf.json`: 1, `runs status --workflow wf.json`: 1, `runs verify-ledger`: 1, `run start --workflow wf.json --step S-01`: 0, `run record --workflow wf.json --step S-01 --state performed`: 0, `run cancel --reason ...`: 0, `run finalize --workflow wf.json`: 1). | Empirical subprocess probe in Step 0 against `RunLedgerStore` + `run_cli` in a temporary directory. |
| F-05 | Seeding `.aw/records/runs/run-abcdef1234/ledger.jsonl` and `wf.json` inside `build_installed_project_template` is compatible with every existing leaf in `MUTATION_UNIVERSE`. `runner_shared.state_root(tpl.template_dir)` resolves to `<template_dir>/.aw/records/runs` (because `.aw/records/plans` exists in the template), which `shutil.copytree` in `clone_isolated_project` copies into each per-test `IsolatedProject`. Empirical check of `archive`, `lanes prune`, `runs analyze`, `runs export`, `runs submit`, and `storage *` against a template containing `.aw/records/runs/run-abcdef1234/ledger.jsonl` showed zero regressions. | `tests/conformance_matrix.py` (`build_installed_project_template`, `clone_isolated_project`), `agent_workflows/runner_shared.py` (`state_root`), empirical Step 0 probe. |
| F-06 | `test_agent_surface_conformance_mutation` in `tests/test_agent_surface_conformance.py` constructs `full_argv = leaf.split() + ["--agent"]` without `+ RUNNABLE_ARGV.get(leaf, [])`, whereas `tests/test_shared_flag_honored.py` (`test_json_flag_honored_mutation` and `test_fields_flag_honored_mutation`) already includes `extra_argv = RUNNABLE_ARGV.get(leaf, [])`. Adding `RUNNABLE_ARGV.get(leaf, [])` in `test_agent_surface_conformance_mutation` allows `run init` (added by `v47z9u` with required `--workflow PATH`) to run in `MUTATION_UNIVERSE` via `"run init": ["--workflow", "wf.json"]` in `RUNNABLE_ARGV`. | `tests/test_agent_surface_conformance.py` (`test_agent_surface_conformance_mutation`), `tests/test_shared_flag_honored.py` (`test_json_flag_honored_mutation`, `test_fields_flag_honored_mutation`), plan `v47z9u` E-02/E-03. |

## Proposed changes (ordered, validatable)

1. Verify at execution HEAD that `v47z9u` (`aw run init`) has landed and reproduce the current `covered_by == "declaration"` state of the eight `aw runs` leaves (E-01).
2. Add `seed_ledger_fixture` (calling `aw run init` and seeding Set projection files) and `live_leaf_argv` to `tests/conformance_matrix.py`, wire `seed_ledger_fixture` into `build_installed_project_template`, and expose `ledger_run_id`, `ledger_path`, and `workflow_path` on `InstalledProjectTemplate` and `IsolatedProject` (E-02).
3. Add the eight `aw runs` leaves to `LIVE_SAFE_LEAVES`, add `"run init": ["--workflow", "wf.json"]` to `RUNNABLE_ARGV`, and update the eight `EXEMPTION_REGISTRY` and four `MUTATION_EXEMPTION_REGISTRY` entries to reflect the Section 3.1 bare-JSON / multi-code contract and `set_records` projection architecture (E-03).
4. Update `test_agent_surface_conformance_mutation` in `tests/test_agent_surface_conformance.py` to honor `RUNNABLE_ARGV.get(leaf, [])` so `run init` executes live in `MUTATION_UNIVERSE` (E-04).
5. Wire `live_ledger_dir` and `live_leaf_argv` into `tests/test_exit_contract_conformance.py` and `tests/test_live_conformance_sweep.py`, and add non-vacuous live conformance tests for both the eight `aw runs` read leaves and the four `aw run` mutation leaves against the `aw run init` ledger (E-05).
6. Run `aw sanitize --agent` and the bare `python3 -m pytest` suite (E-06).

## Deferred / out of scope (with reason)

- Writing `requirement_set` and `verifier_decision` records so `aw run finalize` can reach complete (`exit 0`) on a CLI-created ledger.
  - Carrier: 8l1hgw
- Persisting the workflow beside the ledger at `aw run init` time so subsequent `aw run` / `aw runs` invocations do not need `--workflow`.
  - Carrier: sflov4
- Rendering a ledger-only run directory cleanly in the bare `aw runs` viewer.
  - Carrier: nf84rt
- Reconciling spec `25kzda` Section 1.2 step 8 and Section 5.1 with the `rdjka2` decision.
  - Carrier: 66ls4r

## Scope check

- Over-scope: none. Production `agent_workflows/run_cli.py` behavior is intentionally untouched because `tests/test_run_recovery_cli.py` and `docs/cli-output-contract.md` Section 3.1 pin bare JSON dict emission and the `{0..7}` exit vocabulary on the existing 10 ledger leaves.
- Under-scope: none. All eight `aw runs` leaves become `LIVE_SAFE_LEAVES` (`covered_by="live"`), `run init` is live in `MUTATION_UNIVERSE`, and the four `aw run` mutation leaves are live-tested against the `aw run init` ledger in `test_live_conformance_sweep.py`.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_conformance_matrix_structure.py tests/test_live_conformance_sweep.py tests/test_exit_contract_conformance.py tests/test_agent_surface_conformance.py tests/test_shared_flag_honored.py` passing.
- `aw sanitize --agent` exiting 0 with `"outcome": "clean"`.
- Full bare test suite `python3 -m pytest` passing.

## Spec / documentation sync

N/A with reason: this plan modifies only test-harness fixtures and conformance sweep modules (`tests/conformance_matrix.py`, `tests/test_live_conformance_sweep.py`, `tests/test_exit_contract_conformance.py`, `tests/test_agent_surface_conformance.py`). The CLI contract for `aw run init` and Section 3.1 of `docs/cli-output-contract.md` is updated by prerequisite plan `v47z9u` (E-06, E-07).

## Open questions

### OQ-01: How should `LIVE_SAFE_LEAVES` entries for the eight `aw runs` leaves resolve the `aw run init` fixture directory during live sweeps without writing into the repository checkout?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: `LIVE_SAFE_LEAVES` maps each of the eight `aw runs` leaves to `[LEDGER_FIXTURE_RUN_ID]` (`["run-abcdef1234"]`), while `conformance_matrix.live_leaf_argv(leaf, ledger_fixture_dir)` appends `["--dir", str(ledger_fixture_dir)]` (and `["--workflow", str(ledger_fixture_dir / "wf.json")]` for `runs next`, `runs resume`, `runs show`, `runs status`) when `ledger_fixture_dir` is provided by the session-scoped `live_ledger_dir` fixture in `test_live_conformance_sweep.py` and `test_exit_contract_conformance.py`. This keeps the repository checkout untouched, exercises `aw run init` in an isolated session temp directory, and guarantees non-vacuous execution (`returncode in {0, 1}`, never missing-file `2`).

### OQ-02: Should the eight `aw runs` leaves and four `aw run` writers be removed from `EXEMPTION_REGISTRY` / `MUTATION_EXEMPTION_REGISTRY` or kept there with updated Section 3.1 rationales while joining `LIVE_SAFE_LEAVES`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Both: the eight `aw runs` leaves join `LIVE_SAFE_LEAVES` (so `build_matrix` marks their scenario rows `covered_by="live"` and `test_live_conformance_sweep.py` + `test_exit_contract_conformance.py` drive them live), `run init` (which emits an `aw.agent/v1` record per `v47z9u` E-03) enters `MUTATION_UNIVERSE` unexempted via `RUNNABLE_ARGV`, the four `aw run` writers get a dedicated live conformance test against the `aw run init` ledger in `test_live_conformance_sweep.py`, and the `EXEMPTION_REGISTRY` / `MUTATION_EXEMPTION_REGISTRY` entries for the pre-existing leaves are updated from the stale missing-ledger rationale to `docs/cli-output-contract.md Section 3.1` / `agent_workflows/run_cli.py` because `tests/test_run_recovery_cli.py` pins their bare-JSON output shape and `{0..7}` exit vocabulary.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `aw run init --help` exiting 0 (created by prerequisite plan `v47z9u`) and pasted output of the `conformance_matrix.build_matrix()` check showing all eight `aw runs` leaves at `covered_by == "declaration"` before E-03.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff` of `tests/conformance_matrix.py` showing `seed_ledger_fixture`, `live_leaf_argv`, `InstalledProjectTemplate`, `build_installed_project_template`, and `clone_isolated_project`, plus pasted output of a Python one-liner invoking `build_installed_project_template` (created in E-02) confirming `ledger_path.is_file()` and `workflow_path.is_file()`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `git diff` of `tests/conformance_matrix.py` showing the eight `aw runs` leaves in `LIVE_SAFE_LEAVES`, `"run init"` in `RUNNABLE_ARGV`, and updated `EXEMPTION_REGISTRY` / `MUTATION_EXEMPTION_REGISTRY` entries, plus pasted output of `python3 -m pytest -o addopts="" tests/test_conformance_matrix_structure.py` passing with all eight `aw runs` leaves at `covered_by == "live"`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git diff` of `tests/test_agent_surface_conformance.py` showing `RUNNABLE_ARGV.get(leaf, [])` in `test_agent_surface_conformance_mutation`, and pasted output of `python3 -m pytest -o addopts="" tests/test_agent_surface_conformance.py tests/test_shared_flag_honored.py -k "run_init or mutation"` passing (exercising the path wired in E-03 and E-04).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `git diff` of `tests/test_exit_contract_conformance.py` and `tests/test_live_conformance_sweep.py`, and pasted output of `python3 -m pytest -o addopts="" tests/test_conformance_matrix_structure.py tests/test_exit_contract_conformance.py tests/test_live_conformance_sweep.py tests/test_agent_surface_conformance.py tests/test_shared_flag_honored.py` passing with the new live ledger read and mutation tests exercised.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted output of `aw sanitize --agent` showing `"outcome": "clean"` (exit 0) and pasted summary output of bare `python3 -m pytest` passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval and after prerequisite plan `v47z9u` is `executed`. Open questions: all resolved. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit g5s94t -- <paths>`; never push. Paste the actual runner output for every test claim; a claim without pasted output is not evidence. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize g5s94t` only after `aw ipd lint --phase pre-transition` conforms.
