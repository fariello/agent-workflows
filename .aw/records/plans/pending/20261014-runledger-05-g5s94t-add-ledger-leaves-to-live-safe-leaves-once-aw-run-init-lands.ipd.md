# IPD: Add ledger leaves to LIVE_SAFE_LEAVES once aw run init lands

- Date: 2026-10-14
- Kind: child
- Concern: `tests/conformance_matrix.py` exempts the eight `aw runs` subcommands (`runs decisions`, `runs evidence`, `runs next`, `runs questions`, `runs resume`, `runs show`, `runs status`, `runs verify-ledger`) in `EXEMPTION_REGISTRY` with the pre-`v47z9u` reason `"Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace."`, exempts the four `aw run` write leaves (`run start`, `run record`, `run cancel`, `run finalize`) in `MUTATION_EXEMPTION_REGISTRY` with `"Requires target positional argument."`, and omits all eight `aw runs` leaves from `LIVE_SAFE_LEAVES` (`covered_by="declaration"` in `build_matrix`). Once plan `v47z9u` (`hegwri`) lands `aw run init`, the conformance harness can initialize a real `ledger.jsonl` in an isolated fixture directory, making the eight `aw runs` leaves live conformance scenario rows in `LIVE_SAFE_LEAVES`, wiring `aw run init` into `MUTATION_UNIVERSE`, driving the four `aw run` ledger writers live against the initialized ledger, and replacing the stale `EXEMPTION_REGISTRY` / `MUTATION_EXEMPTION_REGISTRY` rationales with measured contract citations. Backlog `a4tjxc`.
- Scope: (1) In `tests/conformance_matrix.py`, add `seed_ledger_fixture` (invoking `aw run init --workflow <root>/wf.json --run-id run-abcdef1234 --dir <root>` and seeding the Set projection files `decisions.md` and `open-questions.md`) and `live_leaf_argv`, add the eight `aw runs` leaves to `LIVE_SAFE_LEAVES`, add `"run init": ["--workflow", "wf.json"]` to `RUNNABLE_ARGV`, write `wf.json` into the installed-project template (and nothing else, so mutation clones stay a clean `aw install` tree), and update the eight `EXEMPTION_REGISTRY` and four `MUTATION_EXEMPTION_REGISTRY` rationales. (2) In `tests/test_agent_surface_conformance.py`, pass `RUNNABLE_ARGV.get(leaf, [])` in `test_agent_surface_conformance_mutation` so `run init` executes in `MUTATION_UNIVERSE` with its required `--workflow` flag. (3) In `tests/test_exit_contract_conformance.py` and `tests/test_live_conformance_sweep.py`, route every `LIVE_SAFE_LEAVES` invocation through `live_leaf_argv` against a session-scoped `live_ledger_dir` fixture, and add non-vacuous live conformance tests for the eight `aw runs` leaves and the four `aw run` writers. OUT: migrating `run_cli._emit_machine` from bare JSON dicts (`docs/cli-output-contract.md` Section 3.1, pinned by `tests/test_run_recovery_cli.py`) to `aw.agent/v1` envelopes or collapsing the 8-code run-execution exit vocabulary `{0..7}` into `{0, 1, 2}`; giving `runs decisions` / `runs questions` a machine (`--agent`/`--json`) branch (F-07, filed as a new backlog item by E-07); redacting the absolute ledger path that `runs evidence` and `runs verify-ledger` print (F-08, same backlog item); writing `requirement_set` / `verifier_decision` records (`8l1hgw` / `um0twl`); persisting the workflow beside the ledger (`sflov4` / `o34rb3`); viewer rendering of ledger-only directories (`nf84rt` / `3a3hh9`).
- Scope-Paths: tests/conformance_matrix.py, tests/test_live_conformance_sweep.py, tests/test_exit_contract_conformance.py, tests/test_agent_surface_conformance.py, .aw/records/backlog/open
- Item-Dependencies: executed:v47z9u
- Status: approved
- Readiness: go-pending-approval
- From-Backlog: a4tjxc
- Work-Kind: chore
- Priority: low
- Set: runledger
- Order: 5
- Highest E allocated: 09
- Author: agent:antigravity
- Id: g5s94t
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008, PR-009
- 2026-10-14 to-review (agent:antigravity): authored review-ready IPD from backlog a4tjxc

- 2026-10-14 draft (agent:antigravity): created.

## Goal

Promote the eight `aw runs` subcommands (`runs decisions`, `runs evidence`, `runs next`, `runs questions`, `runs resume`, `runs show`, `runs status`, `runs verify-ledger`) to `LIVE_SAFE_LEAVES` (`covered_by="live"`) backed by an `aw run init` ledger fixture, wire `aw run init` into `MUTATION_UNIVERSE`, drive the four `aw run` ledger writers live against the fixture ledger, and replace the stale pre-`v47z9u` `EXEMPTION_REGISTRY` / `MUTATION_EXEMPTION_REGISTRY` reasons with measured contract citations.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reproduce and verify dependency

- [ ] E-01 REPRODUCE at execution HEAD. Verify prerequisite `v47z9u` has landed by running `aw run init --help` (expect exit 0, listing `--workflow`, `--run-id`, `--dir`), and run a one-liner over `conformance_matrix.build_matrix(cli._build_parser())` confirming the eight `aw runs` leaves are `covered_by == "declaration"`. Re-measure the F-04 table: in a scratch git repo under a temp dir that contains `.aw/records/` (F-09), run `aw run init --workflow <root>/wf.json --run-id run-abcdef1234 --dir <root>`, seed the two projection files, and record each of the eight read leaves' exit code in human, `--agent` and `--json` modes and each writer's exit code. If `aw run init` is absent, the eight leaves are already `covered_by == "live"`, or any measured exit code differs from F-04, stop and report the plan as blocked or overtaken with pasted output (a differing code changes E-09's assertions).
  - Depends on: none
  - Expected outcome: pasted `aw run init --help` output (exit 0), the `build_matrix` probe output, and the re-measured exit-code table matching F-04.
  - Execution state: pending

### Task group 2: conformance matrix fixture, LIVE_SAFE_LEAVES, and registry truth

- [ ] E-02 Add the ledger fixture helpers to `tests/conformance_matrix.py`: `LEDGER_FIXTURE_RUN_ID = "run-abcdef1234"`, `LEDGER_FIXTURE_WORKFLOW` (a one-step workflow: `S-01` satisfying `R-01`, `depends_on: []`, `requirements: [{"id": "R-01"}]`), `seed_ledger_fixture(root: Path, run_id: str = LEDGER_FIXTURE_RUN_ID) -> Path`, and `live_leaf_argv(leaf: str, ledger_fixture_dir: Optional[Path] = None) -> List[str]`. `seed_ledger_fixture` must: (a) create `root / ".aw" / "records"` if absent, so `runner_shared.state_root(root)` resolves INSIDE `root` rather than under the home-scoped projects tree (F-09); (b) write `root / "wf.json"`; (c) invoke `run_cli(["run", "init", "--workflow", str(root / "wf.json"), "--run-id", run_id, "--dir", str(root)])` and assert returncode 0 and that `runner_shared.state_root(root) / run_id / "ledger.jsonl"` is a file whose path starts with `root`; (d) write `decisions.md` containing `_No autonomous decisions recorded._` and `open-questions.md` containing `_No unresolved questions._` under `set_records.run_artifacts_dir(root, "exec-set", run_id)`; (e) return `root`. `live_leaf_argv(leaf, d)` returns `[*leaf.split(), *LIVE_SAFE_LEAVES[leaf]]`, plus for the eight `aw runs` leaves `["--dir", str(d)]` and, for `runs next`, `runs resume`, `runs status` ONLY, `["--workflow", str(d / "wf.json")]` (`runs show` has NO `--workflow` flag and exits 2 `unrecognized arguments` when given one, F-04). For a ledger leaf called with `d is None`, raise `ValueError` so no caller can silently run it against the repository checkout. Also, inside `build_installed_project_template`, write `LEDGER_FIXTURE_WORKFLOW` to `proj_dir / "wf.json"` AFTER the baseline `git status` is captured (so `baseline_status` is unchanged), and do NOT seed a ledger there: the mutation clones only need `wf.json` for `run init`, and a template ledger would pre-occupy `.aw/records/runs/` for every one of the `MUTATION_UNIVERSE` leaves.
  - Depends on: E-01
  - Expected outcome: `seed_ledger_fixture(tmp)` produces a ledger at `tmp/.aw/records/runs/run-abcdef1234/ledger.jsonl` created by `aw run init`, `wf.json`, and the two projection files; `live_leaf_argv("runs show", d)` contains `--dir` and no `--workflow`; `live_leaf_argv("runs status", None)` raises `ValueError`; `live_leaf_argv("ipd lint")` equals `["ipd", "lint", "--all"]`; the installed template contains `wf.json` and no `.aw/records/runs/`.
  - Execution state: pending

- [ ] E-03 Update `LIVE_SAFE_LEAVES` and `RUNNABLE_ARGV` in `tests/conformance_matrix.py`: add `"runs decisions"`, `"runs evidence"`, `"runs next"`, `"runs questions"`, `"runs resume"`, `"runs show"`, `"runs status"`, and `"runs verify-ledger"` to `LIVE_SAFE_LEAVES` with `[LEDGER_FIXTURE_RUN_ID]`, and add `"run init": ["--workflow", "wf.json"]` to `RUNNABLE_ARGV`. Keep the comment block above `LIVE_SAFE_LEAVES` true by adding a sentence that the eight ledger leaves are read-only and run against an isolated `aw run init` fixture via `live_leaf_argv`, never against the repository checkout.
  - Depends on: E-02
  - Expected outcome: `build_matrix()` marks all eight `aw runs` leaves `covered_by="live"`, `live_cheap_leaves()` includes all eight, `RUNNABLE_ARGV["run init"] == ["--workflow", "wf.json"]`.
  - Execution state: pending

- [ ] E-04 Update the exemption rationales in `tests/conformance_matrix.py`, keeping every leaf exempted (the exemptions gate `aw.agent/v1` schema conformance, which these leaves still do not meet; F-01/F-02). (a) The six ledger readers (`runs evidence`, `runs next`, `runs resume`, `runs show`, `runs status`, `runs verify-ledger`) in `EXEMPTION_REGISTRY` become `reason_kind="sanctioned_raw"`, `citation="docs/cli-output-contract.md Section 3.1"`, reason stating that `run_cli._emit_machine` emits bare JSON dicts (pinned by `tests/test_run_recovery_cli.py`) under the Section 3.1 run-execution exit vocabulary rather than `aw.agent/v1` records. (b) `runs decisions` and `runs questions` stay `reason_kind="not_runnable"` with `citation="agent_workflows/run_cli.py"` and a reason stating that `_run_decisions` / `_run_questions` read the `set_records` markdown projections (not `ledger.jsonl`) and print raw markdown under every mode, including `--agent` and `--json` (F-07), citing the backlog item E-07 files. (c) `run start`, `run record`, `run cancel`, and `run finalize` in `MUTATION_EXEMPTION_REGISTRY` stay `reason_kind="arg_fixture_needed"` (`test_mutation_exemption_registry_contract` admits only `arg_fixture_needed`, `fixture_lifecycle`, `owned_elsewhere`, `known_broken`; `sanctioned_raw` there would fail it) with the reason rewritten to name the required target positional and step/state flags, the bare-dict machine contract (`docs/cli-output-contract.md Section 3.1`), and that they are live-tested against the fixture ledger by E-09's mutation test. Update the `# sanctioned_raw (5):` / `# not_runnable (16):` count comments to the new counts.
  - Depends on: E-03
  - Expected outcome: no `EXEMPTION_REGISTRY` entry claims a ledger is absent from the workspace; `tests/test_agent_surface_conformance.py::test_mutation_exemption_registry_contract` and `tests/test_command_surface_declarations.py` pass; the set of exempted leaves in both registries is unchanged except for the absence of `run init` (which was never exempted).
  - Execution state: pending

### Task group 3: wire conformance sweeps and non-vacuous ledger leaf gates

- [ ] E-05 In `tests/test_agent_surface_conformance.py`, update `test_agent_surface_conformance_mutation` to build `full_argv = leaf.split() + RUNNABLE_ARGV.get(leaf, []) + ["--agent"]` (matching `tests/test_shared_flag_honored.py` `test_json_flag_honored_mutation` and `test_fields_flag_honored_mutation`), so `run init` executes in `MUTATION_UNIVERSE` against the clone's `wf.json` and is checked for `aw.agent/v1` validity, exit parity, path-leak absence and fixture isolation. No existing `MUTATION_UNIVERSE` leaf has a `RUNNABLE_ARGV` entry (measured at review: zero overlap), so the change affects only `run init`.
  - Depends on: E-04
  - Expected outcome: `test_agent_surface_conformance_mutation[run init]`, `test_json_flag_honored_mutation[run init]` and `test_fields_flag_honored_mutation[run init]` are collected and pass; if `v47z9u`'s `--json` or `--fields` output does not honor the shared contract, record the measured failure and add a `KNOWN_BROKEN` entry ONLY with a filed backlog id (the existing `test_known_broken_*` contract), never a bare skip.
  - Execution state: pending

- [ ] E-06 In `tests/test_exit_contract_conformance.py` and `tests/test_live_conformance_sweep.py`, add a session-scoped `live_ledger_dir` fixture (`tmp_path_factory.mktemp(...)`, `git init`, then `conformance_matrix.seed_ledger_fixture`) and route EVERY test that runs a `LIVE_SAFE_LEAVES` member with its extra argv (`test_live_safe_leaves_exit_contract_membership_cheap`, `test_live_safe_leaves_exit_contract_membership_heavy`, `test_no_color_scenario_is_plain_cheap_leaves`, `test_no_color_scenario_is_plain_heavy_leaves`, `test_no_color_transport_contrast_observes_ansi`) through `conformance_matrix.live_leaf_argv(leaf, live_ledger_dir)`. Without this, each ledger leaf runs with cwd = repository checkout and exits 2 `ledger file not found`, which is inside every ledger leaf's declared `exit_contract` and so passes VACUOUSLY (F-10). Each module defines its own `live_ledger_dir` fixture calling the same `seed_ledger_fixture` (no new conftest).
  - Depends on: E-05
  - Expected outcome: each of the five sweeps invokes the eight `aw runs` leaves (where it iterates them) with `--dir <live_ledger_dir>`; non-ledger leaves' argv is byte-identical to before (`live_leaf_argv` returns `[*leaf.split(), *LIVE_SAFE_LEAVES[leaf]]` for them); `tests/test_exit_contract_conformance.py` and `tests/test_live_conformance_sweep.py` pass.
  - Execution state: pending

- [ ] E-09 Add two non-vacuous ledger tests to `tests/test_live_conformance_sweep.py`, reusing E-06's `live_ledger_dir`: (a) `test_live_ledger_read_leaves_non_vacuous` over the eight `aw runs` leaves against `live_ledger_dir`, asserting the F-04 exit code exactly in human, `--agent` and `--json` modes (never 2, 5 or 7); for the six ledger readers that `--json` stdout parses as one JSON object and `--agent` stdout's last line parses as one JSON object, with zero ANSI escapes, and that it carries `"run_id": LEDGER_FIXTURE_RUN_ID` for `runs next`, `runs resume`, `runs show`, `runs status` and a `"ledger"` key for `runs evidence` and a `"chain_clean": true` key for `runs verify-ledger`; for `runs decisions` / `runs questions` that stdout contains the projection's marker line in all three modes (pinning today's F-07 behavior so a future machine branch is a visible change); (b) `test_live_ledger_mutation_leaves_conformance`: for each of human, `--agent`, `--json`, and `run_cli_tty(..., no_color=True)`, take a FRESH `seed_ledger_fixture` directory under `tmp_path` and run the sequence `run start --step S-01 --workflow wf.json` (0), `run record --step S-01 --state performed --workflow wf.json` (0), `run finalize --workflow wf.json` (1, incomplete: no frozen requirement set, `8l1hgw`), `run cancel --reason conformance` (0), asserting each exact code, that each code is in the leaf's `exit_contract`, that machine outputs parse as one JSON object, that no output contains an ANSI escape, and, after the sequence, that `runs status --json` reports `run_state == "cancelled"` (proving the writers changed the ledger, not just exited 0).
  - Depends on: E-06
  - Expected outcome: both new tests pass and are non-vacuous (the read-leaf test fails when pointed at a directory with no fixture); `tests/test_conformance_matrix_structure.py`, `tests/test_exit_contract_conformance.py`, `tests/test_live_conformance_sweep.py`, `tests/test_agent_surface_conformance.py` and `tests/test_shared_flag_honored.py` all pass.
  - Execution state: pending

- [ ] E-07 File ONE backlog item with `aw backlog new --apply` (`--set runledger`, `--work-kind chore`, `--priority low`) recording the two measured machine-surface gaps this plan pins but does not fix: (F-07) `runs decisions` / `runs questions` print raw markdown under `--agent` and `--json`; (F-08) `runs evidence --agent|--json` emits an absolute `"ledger"` path and `runs verify-ledger` prints `Ledger: <absolute path>` in human mode. Paste the measured outputs into its body, and cite its id6 in E-04 (b)'s exemption reason.
  - Depends on: E-01
  - Expected outcome: a new `.aw/records/backlog/open/...backlog.md` exists, `aw backlog check` passes, and its id6 appears in the `runs decisions` / `runs questions` exemption reasons.
  - Execution state: pending

- [ ] E-08 Run `aw sanitize --agent` and the bare test suite (`python3 -m pytest`) and paste the actual runner outputs.
  - Depends on: E-09, E-07
  - Expected outcome: `aw sanitize --agent` reports `"outcome": "clean"` (exit 0) and bare `python3 -m pytest` passes with zero failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Run the full test suite bare as `python3 -m pytest` (no `-n0`, no extra `-q`, no `-p no:randomly`). For targeted test runs during development, use `python3 -m pytest -o addopts="" <test_files>`.
- Tests must test observable behavior and outcomes by driving CLI commands or functions; never inspect production source code via `inspect`, `ast`, regex, or line counts (P16).
- Cite code by SYMBOL (`module.function` or `module.CONSTANT`) or quoted content string, never by bare line numbers (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Commit only modified paths through `aw commit <plan-id6> -- <paths>`; never push.
- Run `aw sanitize --agent` to verify no local paths or machine identifiers leak into tracked artifacts.
- Exemption registries are CEILINGS (`tests/conformance_matrix.py` header comments): an entry may not be added to silence a red sweep, and a `known_broken` / `owned_elsewhere` mutation entry must cite a resolvable backlog id (`test_mutation_exemption_registry_contract`).

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | `LIVE_SAFE_LEAVES` and `EXEMPTION_REGISTRY` govern two distinct gates in `tests/conformance_matrix.py`. `build_matrix(parser)` marks a leaf's scenario rows (`tty`, `non_tty`, `agent`, `no_color`, `help`, `usage_error`, `json`, `domain_failure`) as `covered_by="live"` iff `decl.command in LIVE_SAFE_LEAVES`, which is consumed by `test_conformance_matrix_structure.py`, `test_live_conformance_sweep.py`, and `test_exit_contract_conformance.py`. By contrast, `EXEMPTION_REGISTRY` and `MUTATION_EXEMPTION_REGISTRY` are consumed only by `test_agent_surface_conformance.py` and `test_shared_flag_honored.py` to gate `aw.agent/v1` envelope schema conformance (`agent_schema.validate_agent_record`). Other leaves with non-`aw.agent/v1` machine output (such as `research check-miscategorized`) are simultaneously members of `LIVE_SAFE_LEAVES` and `EXEMPTION_REGISTRY` (`reason_kind="sanctioned_raw"`). Re-measured at review (HEAD `f140d2448`): `research check-miscategorized` is the only current overlap. | `tests/conformance_matrix.py` (`LIVE_SAFE_LEAVES`, `EXEMPTION_REGISTRY`, `build_matrix`), `tests/test_conformance_matrix_structure.py`, `tests/test_live_conformance_sweep.py`, `tests/test_exit_contract_conformance.py`, `tests/test_agent_surface_conformance.py` (`compute_conformance_universe`, `compute_mutation_conformance_universe`). |
| F-02 | Even against a valid `ledger.jsonl`, none of the six ledger-reading leaves or four ledger-writing leaves emits an `aw.agent/v1` envelope record under `--agent`. `run_cli._emit_machine` emits bare JSON dicts (`json.dumps(sanitized, sort_keys=True, ...)`) and uses the 8-code run-execution exit vocabulary `{0..7}` documented in `docs/cli-output-contract.md` Section 3.1 and pinned by `tests/test_run_recovery_cli.py`. | `agent_workflows/run_cli.py` (`_emit_machine`, `_emit_error`), `docs/cli-output-contract.md` Section 3.1, `tests/test_exit_vocabulary_boundary.py`, `tests/test_run_recovery_cli.py`. |
| F-03 | Two of the eight `aw runs` leaves (`runs decisions` and `runs questions`) do not read `ledger.jsonl` at all: `run_cli._run_decisions` and `run_cli._run_questions` call `_projection_dir(args)` -> `set_records.run_artifacts_dir(Path(repo_root), workflow, run_id)` and read `.aw/workflow-artifacts/<workflow>/<run-id>/decisions.md` and `open-questions.md`. Their current `EXEMPTION_REGISTRY` entries cite `agent_workflows/run_ledger_store.py` and the missing-ledger reason. | `agent_workflows/run_cli.py` (`_projection_dir`, `_run_decisions`, `_run_questions`), `agent_workflows/set_records.py` (`run_artifacts_dir`, `DECISIONS_FILE`, `OPEN_QUESTIONS_FILE`). |
| F-04 | RE-MEASURED AT REVIEW (HEAD `f140d2448`), replacing the authored table, which was wrong in four places. Fixture: a scratch git repo with `.aw/records/plans/`, a hand-appended `kind: "run"` header at `.aw/records/runs/run-abcdef1234/ledger.jsonl` (what `v47z9u` E-03 will write; `aw run init` does not exist yet), `wf.json` (one step `S-01` -> `R-01`), and both projection files with their "none recorded" marker lines. Every leaf invoked with `run-abcdef1234 --dir <root>`; identical codes in human, `--agent`, `--json` and `run_cli_tty(no_color=True)`, zero ANSI in all: `runs decisions` 1 (AUTHORED 0; the "none" marker means exit 1 by `_run_decisions`); `runs questions` 1 (AUTHORED 0, same reason); `runs evidence` 0; `runs next --workflow` 0; `runs resume --workflow` 0; `runs show` 1 WITHOUT `--workflow` (with `--workflow` it exits 2 `unrecognized arguments: --workflow`, because `cli._register_run_leaf` gives `show` no `--workflow`; AUTHORED "`runs show --workflow wf.json`: 1"); `runs status --workflow` 1; `runs verify-ledger` 1. Writers (fresh fixture per mode, sequenced start -> record -> finalize -> cancel): `run start` 0, `run record --state performed` 0, `run finalize` 1 (`no frozen requirements defined`), `run cancel` 0; each also measured in isolation with the same code. All codes are inside each leaf's `command_surface` `exit_contract`. | Review probe script driving `tests.conformance_matrix.run_cli` / `run_cli_tty` over the fixture; `agent_workflows/cli.py` `_register_run_leaf` (`if name in ("start", "next", "record", "resume", "cancel", "status", "finalize"): _pr.add_argument("--workflow", ...)`). |
| F-05 | The authored claim that seeding a ledger in `build_installed_project_template` is harmless was tested: injecting the full seed (ledger, `wf.json`, projections) into the template as a pytest plugin, `tests/test_agent_surface_conformance.py tests/test_shared_flag_honored.py -k mutation` gave `89 passed, 8 xfailed`, so no regression. But the only untracked residue the seed leaves in `git status` is `?? wf.json` (the ledger and projections are gitignored: `.aw/.gitignore` `records/runs/`, `/workflow-artifacts/`), and only `run init` needs anything. The template therefore gets `wf.json` only (E-02), written after `baseline_status` is captured. | Review plugin run (pasted counts above); `.aw/.gitignore`; `tests/conformance_matrix.py` `build_installed_project_template` (`baseline_status` from `git status --short`). |
| F-06 | `test_agent_surface_conformance_mutation` builds `full_argv = leaf.split() + ["--agent"]` without `RUNNABLE_ARGV.get(leaf, [])`, whereas `tests/test_shared_flag_honored.py` `test_json_flag_honored_mutation` and `test_fields_flag_honored_mutation` already include it. No current `MUTATION_UNIVERSE` leaf has a `RUNNABLE_ARGV` entry (review probe: empty intersection over 32 leaves), so adding it changes nothing but `run init`. | `tests/test_agent_surface_conformance.py` (`test_agent_surface_conformance_mutation`), `tests/test_shared_flag_honored.py`, plan `v47z9u` E-02/E-03. |
| F-07 | `runs decisions` and `runs questions` have NO machine branch: under `--agent` and `--json` they print the raw markdown projection, so stdout is not JSON (review probe: `json.loads` fails in both modes). The authored E-05 (a) asserted "parseable JSON ... under both `--agent` and `--json`" only for the six readers, which is correct; this finding records why those two must stay `not_runnable` in the agent-surface registry and why their live test asserts the marker line instead. | `agent_workflows/run_cli.py` `_run_decisions`, `_run_questions` (unconditional `_print_human(text)`); review probe. |
| F-08 | `runs evidence --agent|--json` emits `"ledger": "<absolute path>"`, and `runs verify-ledger` human mode prints `Ledger: <absolute path>`. Not a gate this plan's tests assert on (the exemptions keep them out of the path-leak check), but it is a leak shape (D92) on a surface this plan makes live. Filed by E-07, not fixed here (production code is out of scope). | Review probe outputs; `DECISIONS.md` D92. |
| F-09 | `runner_shared.state_root` resolves INSIDE a directory only when `<dir>/.aw/records` exists; a bare `git init` temp dir resolves under the home-scoped projects tree (review probe: "bare git dir -> OUTSIDE (home)", "with .aw/records -> inside"). A session `live_ledger_dir` built with `tmp_path_factory.mktemp` + `git init` alone would write the fixture ledger outside the temp tree. | `agent_workflows/runner_shared.py` `state_root`; review probe. |
| F-10 | Every ledger leaf's `exit_contract` contains `2`, and run with cwd = repository checkout and no `--dir` each ledger leaf exits 2 (`ledger file not found` / `no ... projection found`). So any sweep that passes `LIVE_SAFE_LEAVES[leaf]` without `live_leaf_argv` (the authored E-05 named only two of the five such tests) passes vacuously while claiming live coverage; `test_no_color_scenario_is_plain_heavy_leaves` and the heavy exit-contract test do not iterate ledger leaves today but share the shape. | `agent_workflows/command_surface.py` (`exit_contract` per leaf, all include 2); review probe "cwd=REPO-no-dir rc=2" for all eight; `tests/test_live_conformance_sweep.py`, `tests/test_exit_contract_conformance.py`. |

## Proposed changes (ordered, validatable)

1. Verify `v47z9u` landed and re-measure F-04 (E-01).
2. Add `seed_ledger_fixture`, `live_leaf_argv`, `LEDGER_FIXTURE_*`, and template `wf.json` (E-02).
3. Add the eight leaves to `LIVE_SAFE_LEAVES` and `run init` to `RUNNABLE_ARGV` (E-03).
4. Rewrite the eight `EXEMPTION_REGISTRY` and four `MUTATION_EXEMPTION_REGISTRY` rationales without changing which leaves are exempt (E-04).
5. Honor `RUNNABLE_ARGV` in `test_agent_surface_conformance_mutation` (E-05).
6. Route all five `LIVE_SAFE_LEAVES` sweeps through `live_leaf_argv` (E-06), and add the two non-vacuous ledger tests (E-09).
7. File the F-07/F-08 backlog item (E-07).
8. `aw sanitize --agent` and the bare suite (E-08).

## Deferred / out of scope (with reason)

- Writing `requirement_set` and `verifier_decision` records so `aw run finalize` can reach complete (`exit 0`) on a CLI-created ledger. When `um0twl` lands, E-09 (b)'s `finalize` expectation (exit 1) changes; `um0twl` also adds `run verify` to `MUTATION_EXEMPTION_REGISTRY`, which this plan does not touch.
  - Carrier: um0twl
- Persisting the workflow beside the ledger at `aw run init` time so later invocations need no `--workflow`.
  - Carrier: o34rb3
- Rendering a ledger-only run directory cleanly in the bare `aw runs` viewer.
  - Carrier: 3a3hh9
  - Carrier-Evidence: .aw/records/plans/executed/20261014-runledger-06-3a3hh9-classify-and-render-ledger-only-run-directories-in-aw-runs-v.ipd.md
- Reconciling spec `25kzda` Section 1.2 step 8 and Section 5.1 with the `rdjka2` decision.
  - Carrier: 9epp40
  - Carrier-Evidence: .aw/records/plans/executed/20261014-runledger-04-9epp40-amend-spec-25kzda-1-2-step-8-and-5-1-to-scope-the-hash-chain.ipd.md
- A machine branch for `runs decisions` / `runs questions`, and redaction of the absolute ledger path in `runs evidence` / `runs verify-ledger` (F-07, F-08).
  - Carrier-Declined: filed as a separate backlog item by E-07 during execution

## Scope check

- Over-scope: none. Production `agent_workflows/` code is untouched; `tests/test_run_recovery_cli.py` and `docs/cli-output-contract.md` Section 3.1 pin bare-JSON emission and the `{0..7}` vocabulary.
- Under-scope: closed at review: three heavy/contrast sweeps also route through `live_leaf_argv` (F-10); the fixture creates `.aw/records/` (F-09); the measured F-04 codes replace the authored ones; F-07/F-08 get a carrier (E-07).

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_conformance_matrix_structure.py tests/test_live_conformance_sweep.py tests/test_exit_contract_conformance.py tests/test_agent_surface_conformance.py tests/test_shared_flag_honored.py tests/test_command_surface_declarations.py` passing.
- Non-vacuity: E-09 (a) asserts exact codes (never 2), and E-09 (b) asserts the ledger's post-sequence state.
- `aw backlog check` passing after E-07.
- `aw sanitize --agent` exiting 0 with `"outcome": "clean"`.
- Full bare test suite `python3 -m pytest` passing.

## Spec / documentation sync

N/A with reason: this plan modifies only test-harness fixtures and conformance sweep modules, plus one new backlog record. No spec describes `LIVE_SAFE_LEAVES` or the exemption registries; the CLI contract for `aw run init` and Section 3.1 of `docs/cli-output-contract.md` are updated by prerequisite plan `v47z9u` (E-06, E-07). No `.spec.md` is in Scope-Paths.

## Open questions

### OQ-01: How should `LIVE_SAFE_LEAVES` entries for the eight `aw runs` leaves resolve the `aw run init` fixture directory during live sweeps without writing into the repository checkout?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: `LIVE_SAFE_LEAVES` maps each of the eight `aw runs` leaves to `[LEDGER_FIXTURE_RUN_ID]`, while `conformance_matrix.live_leaf_argv(leaf, ledger_fixture_dir)` appends `["--dir", str(ledger_fixture_dir)]` (and `["--workflow", str(ledger_fixture_dir / "wf.json")]` for `runs next`, `runs resume`, `runs status` only; `runs show` has no `--workflow`, F-04) from the session-scoped `live_ledger_dir` fixture, which creates `.aw/records/` before seeding so `state_root` stays inside the temp tree (F-09). `live_leaf_argv` raises for a ledger leaf without a fixture dir, so no sweep can silently run one against the checkout (F-10). Revised at review (plan reviewer): the `runs show` exclusion, the `.aw/records/` precondition and the raise were added; the mechanism was demonstrated by the review probe (F-04).

### OQ-02: Should the eight `aw runs` leaves and four `aw run` writers be removed from `EXEMPTION_REGISTRY` / `MUTATION_EXEMPTION_REGISTRY` or kept there with updated rationales while joining `LIVE_SAFE_LEAVES`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Kept, with updated rationales. The eight `aw runs` leaves join `LIVE_SAFE_LEAVES` (live scenario rows) but stay in `EXEMPTION_REGISTRY` because they still do not emit `aw.agent/v1` records (F-02, F-07); `research check-miscategorized` is the existing precedent for membership in both (F-01). `run init` enters `MUTATION_UNIVERSE` unexempted via `RUNNABLE_ARGV`. The four writers stay in `MUTATION_EXEMPTION_REGISTRY` as `arg_fixture_needed` (the only kind the mutation registry contract admits that fits), with a rationale citing Section 3.1 and E-09's live test. Revised at review: the authored E-03 (e) would have cited Section 3.1 without saying which `reason_kind`; `sanctioned_raw` would fail `test_mutation_exemption_registry_contract`, so the kind is now named. `runs decisions` / `runs questions` stay `not_runnable` rather than `sanctioned_raw`, because no contract section sanctions markdown on `--agent`/`--json`; that is a gap, carried by E-07.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `aw run init --help` (exit 0, created by prerequisite `v47z9u`), pasted `build_matrix` probe showing all eight `aw runs` leaves at `covered_by == "declaration"`, and the pasted re-measured exit-code table (eight readers x three modes, four writers) compared row by row with F-04.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff tests/conformance_matrix.py` showing `LEDGER_FIXTURE_RUN_ID`, `LEDGER_FIXTURE_WORKFLOW`, `seed_ledger_fixture` (creating `.aw/records/`, calling `run init`, asserting the ledger path is inside root) and `live_leaf_argv` (with the `runs show` no-`--workflow` case and the `ValueError`), plus the template `wf.json` write after `baseline_status`; and pasted output of a Python one-liner showing `seed_ledger_fixture(tmp)` produced the ledger under `tmp`, `live_leaf_argv("runs show", d)` has no `--workflow`, `live_leaf_argv("runs status", None)` raises, and a built template has `wf.json` and no `.aw/records/runs/`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `git diff` of the `LIVE_SAFE_LEAVES` / `RUNNABLE_ARGV` hunks, plus pasted output of `python3 -m pytest -o addopts="" tests/test_conformance_matrix_structure.py` passing and a pasted `build_matrix` probe showing all eight `aw runs` leaves at `covered_by == "live"`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git diff` of the twelve registry entries (no leaf added or removed, `reason_kind` values as E-04 states, the E-07 id6 cited for `runs decisions` / `runs questions`), plus pasted passing output of `python3 -m pytest -o addopts="" tests/test_agent_surface_conformance.py -k registry_contract tests/test_command_surface_declarations.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `git diff tests/test_agent_surface_conformance.py` showing `RUNNABLE_ARGV.get(leaf, [])` in `test_agent_surface_conformance_mutation`, and pasted `python3 -m pytest -o addopts="" -v tests/test_agent_surface_conformance.py tests/test_shared_flag_honored.py -k "run init"` output listing the three `[run init]` mutation cases and their outcome (each pass, or a strict xfail carrying a filed backlog id).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `git diff` of `tests/test_exit_contract_conformance.py` and `tests/test_live_conformance_sweep.py` showing all five sweeps routed through `live_leaf_argv` and the `live_ledger_dir` fixture, plus pasted `python3 -m pytest -o addopts="" -v tests/test_live_conformance_sweep.py tests/test_exit_contract_conformance.py -k runs` listing the eight `aw runs` leaves in each sweep that iterates them, passing.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: `git diff tests/test_live_conformance_sweep.py` showing the two new tests; pasted `python3 -m pytest -o addopts="" -v tests/test_live_conformance_sweep.py -k ledger` with both passing; and a pasted non-vacuity demonstration: the read-leaf test FAILS when pointed at a temp dir with no fixture (exit 2 observed), then passes again when restored. Reachable through `run_cli.run_cli` dispatch over the ledger E-02's `seed_ledger_fixture` creates.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the new backlog file's path and front matter, pasted `aw backlog check` passing, and its id6 shown in the V-04 diff.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: pasted output of `aw sanitize --agent` showing `"outcome": "clean"` (exit 0) and the pasted summary line of bare `python3 -m pytest` with zero failures (any failing node id must be shown to fail identically on the base commit to be excused).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval and after prerequisite plan `v47z9u` is `executed`. Open questions: all resolved. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit g5s94t -- <paths>`; never push. Paste the actual runner output for every test claim; a claim without pasted output is not evidence. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize g5s94t` only after `aw ipd lint --phase pre-transition` conforms.
