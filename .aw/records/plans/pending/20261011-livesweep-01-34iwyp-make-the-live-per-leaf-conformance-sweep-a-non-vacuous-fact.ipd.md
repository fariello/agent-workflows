# IPD: Make the live per-leaf conformance sweep, a non-vacuous fact-parity gate, and the live exit-membership gate default-collected

- Date: 2026-10-11
- Kind: child
- Concern: Three live conformance properties are unowned or CI-advisory after the `19313eed7` trim: the per-leaf `--no-color` / `--help` / usage-error scenario sweep over `LIVE_SAFE_LEAVES`, a human-versus-agent fact-parity gate that actually compares outcomes (the old one was vacuous on 16 of 16 leaves), and `test_live_safe_leaves_exit_contract_membership`, which is `slow` and therefore runs only in the `continue-on-error: true` CI step.
- Scope: IN: a new default-collected module `tests/test_live_conformance_sweep.py` that drives the help, usage-error and no-color scenarios per leaf (parametrized, one subprocess per case) over the CHEAP subset of `LIVE_SAFE_LEAVES`; a reintroduced human-banner extractor in `tests/conformance_matrix.py` whose recognized shapes are measured, plus a curated `FACT_PARITY_LEAVES` population that is asserted NON-VACUOUS (every member must yield an outcome family, or the test fails); splitting the live exit-membership gate so its cheap leaves run default-collected per leaf while the measured-heavy leaves (`doctor`, `attention`, `status`) stay `slow`. OUT: changing any CLI renderer or command behavior; adding members to `LIVE_SAFE_LEAVES`; mutation leaves (owned by executed plan `vfv2db`); flipping the CI advisory step's `continue-on-error` (owned by the backlog items that step's comment names); making `doctor` fast.
- Scope-Paths: tests/test_live_conformance_sweep.py, tests/conformance_matrix.py, tests/test_exit_contract_conformance.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 2wowfy
- Set: livesweep
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 34iwyp

## Workflow history

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog `2wowfy` as a single child (Set `livesweep`, no orchestrator: one cohesive test-surface change). Timings below were RE-MEASURED in this lane at HEAD `d2a511511`, not copied from the backlog item, and they materially change the backlog's open question: the help and usage-error scenarios are cheap (about 6s each for all 16 leaves), so the expensive part is only the leaves that do real work.

## Goal

Turn the three deferred live conformance properties carried by `2wowfy` into gates that can actually fail CI: default-collected, per-leaf parametrized so `pytest-xdist` spreads the subprocess cost, restricted to leaves whose measured cost fits the default suite, and, for fact parity, asserted non-vacuous so a gate that silently compares nothing is itself a failure.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: partition the live population by measured cost

- [ ] E-01 Add to `tests/conformance_matrix.py` a named frozenset `LIVE_HEAVY_LEAVES` (initial members `doctor`, `attention`, `status`) and a helper `live_cheap_leaves()` returning `LIVE_SAFE_LEAVES` minus `LIVE_HEAVY_LEAVES` in sorted order; each heavy member carries an inline comment with its re-measured per-invocation wall time. Re-measure every `LIVE_SAFE_LEAVES` member first (human, `--agent`, `NO_COLOR`) and put any leaf over 5s per invocation in the heavy set rather than trusting the authoring-time list.
  - Depends on: none
  - Expected outcome: `live_cheap_leaves()` returns 13 leaves (or the re-measured count), `LIVE_HEAVY_LEAVES` is a subset of `LIVE_SAFE_LEAVES`, and the module docstring's consumer list names the new module.
  - Execution state: pending

### Task group 2: the per-leaf scenario sweep, default-collected

- [ ] E-02 Create `tests/test_live_conformance_sweep.py` with three parametrized tests, ids being the leaf names: `--help` over ALL 16 `LIVE_SAFE_LEAVES` (asserts exit 0 and `usage` in stdout, recovered from `19313eed7^:tests/test_cli_conformance_matrix.py` `test_help_scenario_exits_zero_and_documents_agent`), usage error over ALL 16 (asserts exit 2 and `usage` in stdout+stderr, recovered from `test_usage_error_scenario_exits_two`), and `NO_COLOR` over `live_cheap_leaves()` (asserts no `ANSI_RE` match in stdout, recovered from `test_no_color_scenario_is_plain`). No `slow` marker. Help and usage error include the heavy leaves because argparse exits before any handler runs (measured about 0.36s per invocation).
  - Depends on: E-01
  - Expected outcome: a bare `python3 -m pytest tests/test_live_conformance_sweep.py` collects 16 + 16 + 13 cases, all pass, and none is deselected by the default `-m 'not slow and not livecorpus'`.
  - Execution state: pending

- [ ] E-03 Add a parametrized `NO_COLOR` heavy-leaf case over `LIVE_HEAVY_LEAVES` in the same module, marked `@pytest.mark.slow`, so the heavy members still have the scenario in `make test-all` and none of the 16 leaves loses no-color coverage.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest -m slow tests/test_live_conformance_sweep.py` collects exactly the heavy members and they pass.
  - Execution state: pending

### Task group 3: a fact-parity gate that cannot be vacuous

- [ ] E-04 Reintroduce in `tests/conformance_matrix.py` `_HUMAN_OUTCOME_WORDS`, `outcome_family`, and `semantic_facts_from_human`, recovered from `3ec1c2d5a^:tests/conformance_matrix.py` (deleted by `dq9bj9` under its OQ-01 Branch A), and WIDEN the recognized shape to the two measured banner forms: (a) an `AW <command>` title line followed by a `<glyph> <STATUS>` line (`runs query schema`: `AW runs query` / `✓ CONFORMS  schema: ...`), and (b) a FIRST line that is itself `<glyph> <STATUS>` (`list-repos`: `✓ CLEAN  no configured ...`; `record-history f36de0`: `✓ CLEAN  no sidecar history ...`). Add `CONFORMS` to the word table if absent. Table, board and rich renders still return `None`. Add `FACT_PARITY_LEAVES: Dict[str, List[str]]` naming the curated banner-emitting leaves with their argv (initially `runs query` + `schema`, `list-repos`, `record-history` + `f36de0`), each confirmed by measurement at execution.
  - Depends on: none
  - Expected outcome: the helper returns a non-None `outcome_family` on each `FACT_PARITY_LEAVES` member's live human output, and `None` on `ipd lint --all` and `attention --check` human output.
  - Execution state: pending

- [ ] E-05 In `tests/test_live_conformance_sweep.py` add a parametrized parity test over `FACT_PARITY_LEAVES` that runs the leaf human and `--agent`, FAILS (does not fall back) if `semantic_facts_from_human` returns `None` (this is the non-vacuity assertion the old `FactParityTests` lacked), and asserts the human family equals `outcome_family(agent outcome)` and both exit codes are equal. Add a unit test that drives the extractor on synthesized strings for each recognized shape plus a table render and a `STALE  /path` row, asserting the mapped family or `None`. Default-collected.
  - Depends on: E-04
  - Expected outcome: all parity cases pass; temporarily replacing a curated leaf's argv with `ipd lint --all` makes its case FAIL with a non-vacuity message (observed, then reverted).
  - Execution state: pending

### Task group 4: make the live exit-membership gate enforcing

- [ ] E-06 Split `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership` into a default-collected parametrized test over `live_cheap_leaves()` (one case per leaf, both human and `--agent` surfaces, same membership assertion) and a `@pytest.mark.slow` parametrized test over `LIVE_HEAVY_LEAVES` keeping the explicit `@pytest.mark.timeout(500)`. Replace the bare `len(safe_leaves) == 16` pin with an assertion that the two partitions are disjoint and their union equals `LIVE_SAFE_LEAVES`, so a newly added leaf is covered rather than breaking a count. Update the docstring's timing record to the re-measured numbers.
  - Depends on: E-01
  - Expected outcome: every `LIVE_SAFE_LEAVES` member is covered by exactly one of the two tests; the cheap one is collected by a bare run.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Bare suite is `python3 -m pytest`; `pyproject.toml` `addopts` deselects `slow` and `livecorpus`, and `.github/workflows/tests.yml` runs `-m slow` only in the step named "Run slow-marked tests (ADVISORY until the known slow failures are fixed)" with `continue-on-error: true`. So "default-collected" is the only placement that can fail CI.
- `conftest.py` hang guard: `_DEFAULT_TEST_CPU_TIMEOUT = 60.0` (parent CPU, which a subprocess wait barely consumes) and `_DEFAULT_TEST_WALL_TIMEOUT = 240.0`. The backlog's "90s" figure predates this two-arm guard; per-leaf parametrization keeps every case far below both arms.
- Restorations recover source with `git show <rev>^:<path>` rather than rewriting from a docstring (precedent: executed `dq9bj9` and `9i2hge` in Set `h0tiaw`).
- `tests.conformance_matrix.run_cli` pins `COLUMNS`, `TERM`, clears `NO_COLOR`/`FORCE_COLOR`, uses `stdin=DEVNULL`, and runs from the repo root; reuse it unchanged.
- P16: tests drive the CLI by subprocess and assert outputs and exit codes; no source reading.

## Findings

| Id | Finding | Evidence (measured in this lane, HEAD `d2a511511`) |
|---|---|---|
| F-01 | `--help` over all 16 `LIVE_SAFE_LEAVES` takes 5.81s total, 0 failures. | ad hoc driver over `run_cli([*leaf.split(), "--help"])` |
| F-02 | Usage error over all 16 takes 5.71s total, 0 failures (all exit 2 with `usage`). | same driver with `USAGE_ERROR_FLAG` |
| F-03 | `NO_COLOR` human run over all 16 takes 59.55s, 0 ANSI hits; `doctor` alone 39.57s, `attention` 5.48s, `status` 3.28s; the other 13 sum to about 11s, none over 2.3s. | per-leaf timing from the same driver |
| F-04 | Human+agent pair cost per leaf (excluding doctor): `attention` 9.70s, `status` 6.23s, all others at or under 4.3s. | second driver running both surfaces |
| F-05 | Of `LIVE_SAFE_LEAVES` plus `RUNNABLE_ARGV`, only three leaves emit an outcome banner: `runs query schema` (`AW runs query` / `✓ CONFORMS ...`, agent outcome `clean`), `list-repos` (first line `✓ CLEAN ...`, agent `clean`), `record-history f36de0` (first line `✓ CLEAN ...`, agent `clean`). All three exit 2 on a bad flag. | second driver; first two non-empty lines printed per leaf |
| F-06 | `semantic_facts_from_human`, `outcome_family` and `_HUMAN_OUTCOME_WORDS` no longer exist in the tree; `dq9bj9` deleted them (its OQ-01 Branch A) and handed them to this carrier. The old helper only accepted the `AW ` title form, so it would miss `list-repos` and `record-history`. | `git show 3ec1c2d5a^:tests/conformance_matrix.py`; executed `dq9bj9` deletion table |
| F-07 | `test_live_safe_leaves_exit_contract_membership` is `@pytest.mark.slow` + `timeout(500)` and pins `len(safe_leaves) == 16`. | `tests/test_exit_contract_conformance.py` |
| F-08 | Agent-stream schema validity and agent exit parity over 42 read/check leaves are already default-collected in `tests/test_agent_surface_conformance.py`; this plan does not re-assert them. | that module's docstring and `compute_conformance_universe` |

## Proposed changes (ordered, validatable)

1. E-01: cost partition in `tests/conformance_matrix.py` (re-measured).
2. E-02, E-03: per-leaf help / usage-error / no-color sweep in the new module; heavy no-color under `slow`.
3. E-04, E-05: widened, non-vacuous banner extractor plus curated parity population and gate.
4. E-06: exit-membership split into enforcing cheap half and `slow` heavy half with a partition-completeness assertion.

## Deferred / out of scope (with reason)

- Making `doctor`, `attention` and `status` cheap enough for the default suite: performance work on production commands, not a test change; their scenarios stay covered in `make test-all` (E-03, E-06 heavy halves).
- Fact parity over table, board and rich renders: would require each renderer to expose a machine-parsable outcome line, a CLI output-contract change. The renderer-level parity property is already owned default-collected by executed `9i2hge`.
- Flipping the advisory CI step: owned by the backlog items listed in that step's comment (`57dwkc`, `4vfkl1`, `3ypquf`, `g0bdgg`).

## Scope check

- Over-scope: none. Only three test-side files change; no production code.
- Under-scope: none. Every one of the backlog's three numbered concerns maps to a task group (1 -> groups 1-2, 2 -> group 3, 3 -> group 4), and the backlog's open question is answered by F-01..F-04.

## Required tests / validation

- `python3 -m pytest tests/test_live_conformance_sweep.py tests/test_exit_contract_conformance.py tests/test_conformance_matrix_structure.py tests/test_agent_surface_conformance.py` (bare defaults) passes and shows the new cases collected.
- `python3 -m pytest -m slow tests/test_live_conformance_sweep.py tests/test_exit_contract_conformance.py` passes for the heavy halves.
- The full bare `python3 -m pytest` passes, and its wall time increase is reported.
- A falsification probe per gate (V-02, V-05, V-06) shows each new gate can go red.

## Spec / documentation sync

N/A: no spec governs these test modules and no user-facing behavior changes. The docstrings of `tests/conformance_matrix.py` and `tests/test_exit_contract_conformance.py` are updated in E-01 and E-06 so their consumer list and timing record match the tree.

## Open questions

### OQ-01: Should the heavy leaves run default-collected anyway, since xdist parallelizes them?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. F-03 measures `doctor` at about 40s per invocation; under xdist one worker would sit on doctor for 40-60s per scenario, and every runner lane merges only after the full suite passes, so that cost is paid by every lane. The backlog itself asks whether the cheap subset fits; F-01..F-04 show it does with wide margin. Heavy leaves keep coverage under `slow`.

### OQ-02: Is `list-repos` stable enough as a parity leaf given it reads the user's repo config?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The parity assertion compares human to agent on the SAME environment, so the outcome value can vary without flaking; only the banner shape must hold. E-05's non-vacuity assertion will surface it immediately if a populated environment renders a table instead, and E-04 requires each member to be confirmed by measurement at execution; a member that does not hold is dropped with the measurement recorded, as long as at least two remain.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted re-measurement table (leaf, human/agent/no-color seconds) from the execution base, plus pasted output of `python3 -c "from tests.conformance_matrix import live_cheap_leaves, LIVE_HEAVY_LEAVES, LIVE_SAFE_LEAVES; print(len(live_cheap_leaves()), sorted(LIVE_HEAVY_LEAVES), set(LIVE_HEAVY_LEAVES) <= set(LIVE_SAFE_LEAVES))"`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted bare `python3 -m pytest tests/test_live_conformance_sweep.py` summary showing the help, usage-error and cheap no-color cases passed and not deselected, plus `python3 -m pytest -o addopts="" --collect-only -q tests/test_live_conformance_sweep.py` listing per-leaf ids. Falsification: setting `FORCE_COLOR=1` in one case's run (temporary edit) makes that case FAIL; paste the failure line, then show the edit reverted with `git diff`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `python3 -m pytest -m slow tests/test_live_conformance_sweep.py` output showing exactly the heavy members collected and passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted output of a one-liner applying `semantic_facts_from_human` to live `run_cli` human output for each `FACT_PARITY_LEAVES` member (non-None family each) and for `ipd lint --all` and `attention --check` (None each).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted bare pytest summary for the parity and extractor unit tests passing; pasted failure output of the non-vacuity probe (curated argv swapped to `ipd lint --all`) and `git diff` showing it reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted bare `python3 -m pytest tests/test_exit_contract_conformance.py` showing the cheap per-leaf membership cases collected and passing; pasted `python3 -m pytest -m slow tests/test_exit_contract_conformance.py` showing the heavy cases passing; falsification: temporarily adding a fake leaf to `LIVE_SAFE_LEAVES` makes the partition-completeness assertion FAIL (paste), then reverted. Finally the full bare `python3 -m pytest` summary line, with before/after wall time.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires human approval before execution. It carries no `- Readiness:` field; that is an output of `/plan-review`.

The executing agent commits ONLY the paths in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing. Every falsification probe in V-02, V-05 and V-06 is a temporary edit that must be reverted, and `git diff --cached --name-only` re-checked, before any commit. Recovered source from `git show` is read to stdout, never written into the tree as a separate file. Paste ACTUAL runner output for every test claim. Under `aw oc run`/`aw agy run` the runner owns `aw ipd begin`/`finalize`; a hand executor runs `aw ipd finalize` itself, never a hand `git mv`. Do NOT move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence with `Result: pass`.
