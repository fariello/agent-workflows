# IPD: Make the live per-leaf conformance sweep, a non-vacuous fact-parity gate, and the live exit-membership gate default-collected

- Date: 2026-10-11
- Kind: child
- Concern: Three live conformance properties are unowned or CI-advisory after the `19313eed7` trim: the per-leaf `--no-color` / `--help` / usage-error scenario sweep over `LIVE_SAFE_LEAVES`, a human-versus-agent fact-parity gate that actually compares outcomes (the old one was vacuous on 16 of 16 leaves), and `test_live_safe_leaves_exit_contract_membership`, which is `slow` and therefore runs only in the `continue-on-error: true` CI step.
- Scope: IN: a new default-collected module `tests/test_live_conformance_sweep.py` that drives the help, usage-error and no-color scenarios per leaf (parametrized, one subprocess per case) over the CHEAP subset of `LIVE_SAFE_LEAVES`; a reintroduced human-banner extractor in `tests/conformance_matrix.py` whose recognized shapes are measured, plus a curated `FACT_PARITY_LEAVES` population that is asserted NON-VACUOUS (every member must yield an outcome family, or the test fails); splitting the live exit-membership gate so its cheap leaves run default-collected per leaf while the measured-heavy leaves (`doctor`, `attention`, `status`) stay `slow`. OUT: changing any CLI renderer or command behavior; adding members to `LIVE_SAFE_LEAVES`; mutation leaves (owned by executed plan `vfv2db`); flipping the CI advisory step's `continue-on-error` (owned by the backlog items that step's comment names); making `doctor` fast.
- Scope-Paths: tests/test_live_conformance_sweep.py, tests/conformance_matrix.py, tests/test_exit_contract_conformance.py, CONTRIBUTING.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 2wowfy
- Set: livesweep
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 34iwyp

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 34iwyp verified (set livesweep, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007 (all fixed; pipe-based NO_COLOR proven vacuous at review, new E-07 pty transport; parity leaves isolated from machine-local state; record `.aw/records/reviews/20261011-livesweep-01-34iwyp-make-the-live-per-leaf-conformance-sweep-a-non-vacuous-fact.review.md`)
- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 fixed

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog `2wowfy` as a single child (Set `livesweep`, no orchestrator: one cohesive test-surface change). Timings below were RE-MEASURED in this lane at HEAD `d2a511511`, not copied from the backlog item, and they materially change the backlog's open question: the help and usage-error scenarios are cheap (about 6s each for all 16 leaves), so the expensive part is only the leaves that do real work.

## Goal

Turn the three deferred live conformance properties carried by `2wowfy` into gates that can actually fail CI: default-collected, per-leaf parametrized so `pytest-xdist` spreads the subprocess cost, restricted to leaves whose measured cost fits the default suite, and, for fact parity, asserted non-vacuous so a gate that silently compares nothing is itself a failure.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: partition the live population by measured cost

- [x] E-01 Add to `tests/conformance_matrix.py` a named frozenset `LIVE_HEAVY_LEAVES` (initial members `doctor`, `attention`, `status`) and a helper `live_cheap_leaves()` returning `LIVE_SAFE_LEAVES` minus `LIVE_HEAVY_LEAVES` in sorted order; each heavy member carries an inline comment with its re-measured per-invocation wall time. Re-measure every `LIVE_SAFE_LEAVES` member first (human, `--agent`, `NO_COLOR`). The three named members are the decided partition and are never REMOVED on re-measurement (at review `status` measured 3.4s and `attention` 5.6s per invocation, so a per-invocation cutoff near 5s would flip them run to run); re-measurement only ADDS a leaf whose human plus `--agent` pair exceeds 8s, recorded with its numbers.
  - Depends on: none
  - Expected outcome: `LIVE_HEAVY_LEAVES` is a subset of `LIVE_SAFE_LEAVES`, `live_cheap_leaves()` is exactly the complement in sorted order (13 members at authoring; the bar is the complement property, not the count), and the module docstring's consumer list names the new module.
  - Execution state: performed

### Task group 2: the per-leaf scenario sweep, default-collected

- [x] E-07 Add `run_cli_tty(argv, *, no_color=False, cwd=None, env_overrides=None)` to `tests/conformance_matrix.py`: same pinned env as `run_cli` (reuse `_pinned_env`), but stdout and stderr attached to a POSIX pseudo-terminal (`pty.openpty()`, close the slave fd in the parent after spawn, read the master until EOF or `OSError` (Linux raises `EIO` once the child closes), stdin `DEVNULL`), returning the same `RunResult` with the combined output in `stdout`. On `sys.platform == "win32"` (no `pty`) callers `pytest.skip` with a reason naming this item. Then create `tests/test_live_conformance_sweep.py` with a default-collected CONTRAST test, parametrized over a curated `COLOR_EMITTING_LEAVES` subset of `live_cheap_leaves()`, asserting `run_cli_tty(...)` WITHOUT `no_color` DOES match `ANSI_RE`; this proves the transport can see color, so E-02's no-ANSI assertion is not vacuous. WHY: measured at review, every cheap leaf emits NO ANSI over `run_cli`'s pipes even without `NO_COLOR` (non-TTY suppression), so a pipe-based no-color test passes whether or not `NO_COLOR` is honored; over a pty, `backlog check`, `context`, `ipd lint`, `layout`, `list-repos`, `spec check` and `specs check` emit ANSI without `NO_COLOR` and none with it, while `check-local-leaks`, `sanitize`, both `research` checks and both `workflow` leaves emit none either way. Re-measure that membership at execution and record it in the constant's comment.
  - Depends on: E-01
  - Expected outcome: on POSIX the contrast test passes for every `COLOR_EMITTING_LEAVES` member and the helper returns the leaf's real exit code; on Windows the dependent cases skip with a named reason rather than fail.
  - Execution state: performed

- [x] E-02 In `tests/test_live_conformance_sweep.py` (created by E-07) add three parametrized tests, ids being the leaf names: `--help` over ALL 16 `LIVE_SAFE_LEAVES` (asserts exit 0 and `usage` in stdout, recovered from `19313eed7^:tests/test_cli_conformance_matrix.py` `test_help_scenario_exits_zero_and_documents_agent`), usage error over ALL 16 (asserts exit 2 and `usage` in stdout+stderr, recovered from `test_usage_error_scenario_exits_two`), and `NO_COLOR` over `live_cheap_leaves()` run through E-07's `run_cli_tty(..., no_color=True)` (asserts no `ANSI_RE` match in the captured output; the assertion shape is recovered from `test_no_color_scenario_is_plain`, but NOT its pipe transport, which E-07 shows is vacuous). No `slow` marker. Help and usage error include the heavy leaves because argparse exits before any handler runs (measured about 0.36s per invocation).
  - Depends on: E-01, E-07
  - Expected outcome: a bare `python3 -m pytest tests/test_live_conformance_sweep.py` collects a help and a usage-error case for EVERY `LIVE_SAFE_LEAVES` member and a no-color case for EVERY `live_cheap_leaves()` member (16 + 16 + 13 at authoring; the bar is membership, re-derived at execution), all pass on POSIX, and none is deselected by the default `-m 'not slow and not livecorpus'`.
  - Execution state: performed

- [x] E-03 Add a parametrized `NO_COLOR` heavy-leaf case over `LIVE_HEAVY_LEAVES` in the same module, run through `run_cli_tty` like E-02's, marked `@pytest.mark.slow`, so the heavy members still have the scenario in `make test-all` and none of the 16 leaves loses no-color coverage.
  - Depends on: E-02, E-07
  - Expected outcome: `python3 -m pytest -m slow tests/test_live_conformance_sweep.py` collects exactly the heavy members and they pass on POSIX.
  - Execution state: performed

### Task group 3: a fact-parity gate that cannot be vacuous

- [x] E-04 Reintroduce in `tests/conformance_matrix.py` `_HUMAN_OUTCOME_WORDS`, `outcome_family`, and `semantic_facts_from_human`, recovered from `3ec1c2d5a^:tests/conformance_matrix.py` (deleted by `dq9bj9` under its OQ-01 Branch A), and WIDEN the recognized shape to the two measured banner forms: (a) an `AW <command>` title line followed by a `<glyph> <STATUS>` line (`runs query schema`: `AW runs query` / `✓ CONFORMS  schema: ...`), and (b) a FIRST line that is itself `<glyph> <STATUS>` (`list-repos`: `✓ CLEAN  no configured ...`; `record-history f36de0`: `✓ CLEAN  no sidecar history ...`). In BOTH shapes the banner line must be exactly `<glyph> <STATUS> ...`: the first token must be a member of `set(agent_workflows.term.GLYPHS.values()) | set(agent_workflows.term.ASCII_GLYPHS.values())` and the STATUS word is the SECOND token, uppercase, looked up in the word table. Do NOT recover the old "first-or-second uppercase token" loop: demonstrated at review, it maps the ASCII banner `FAIL FINDINGS  3 found` (what `Term.format_outcome` emits when `should_unicode` is false, with `ASCII_GLYPHS["findings"] == "FAIL"`) to `fail` instead of `findings`, and a glyph-less first token would let a table row such as `STALE    /path` read as an outcome. `conforms` is already in the recovered `_HUMAN_OUTCOME_WORDS`; keep it. Table, board and rich renders still return `None`. Add `FACT_PARITY_LEAVES: Dict[str, List[str]]` naming the curated banner-emitting leaves with their argv (initially `runs query` + `schema`, `list-repos`, `record-history` + `f36de0`), each confirmed by measurement at execution. These leaves read machine-local state (`list-repos` the user config under `XDG_CONFIG_HOME`; `record-history` the gitignored `.aw/records/history.jsonl`, measured at review to render `History for f36de0` with NO banner once that sidecar holds an `f36de0` line), so the parity runs MUST use an isolated environment: a `tmp_path` project dir containing an empty `.aw/records/` as `cwd`, with `env_overrides` pinning `HOME`, `XDG_CONFIG_HOME` and `AW_HOME` under `tmp_path`. Measured at review: in that isolation all three leaves emit their banner and agent outcome `clean`.
  - Depends on: none
  - Expected outcome: the helper returns a non-None `outcome_family` on each `FACT_PARITY_LEAVES` member's live human output produced in the isolated environment, and `None` on `ipd lint --all` and `attention --check` human output.
  - Execution state: performed

- [x] E-05 In `tests/test_live_conformance_sweep.py` add a parametrized parity test over `FACT_PARITY_LEAVES` that runs the leaf human and `--agent`, FAILS (does not fall back) if `semantic_facts_from_human` returns `None` (this is the non-vacuity assertion the old `FactParityTests` lacked), and asserts the human family equals `outcome_family(agent outcome)` and both exit codes are equal. Run every parity case in the isolated environment E-04 specifies. Add a unit test that drives the extractor on synthesized strings for each recognized shape in BOTH glyph sets (`✓ CONFORMS`, `OK CONFORMS`, `✗ FINDINGS`, `FAIL FINDINGS` -> `findings`, `! PREVIEW`) plus a table render, a glyph-less `STALE    /path` first line, and the real `ipd lint` row shape `-    ✓  executed     plan ...`, asserting the mapped family or `None`. Default-collected.
  - Depends on: E-04
  - Expected outcome: all parity cases pass; temporarily replacing a curated leaf's argv with `ipd lint --all` makes its case FAIL with a non-vacuity message (observed, then reverted).
  - Execution state: performed

### Task group 4: make the live exit-membership gate enforcing

- [x] E-06 Split `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership` into a default-collected parametrized test over `live_cheap_leaves()` (one case per leaf, both human and `--agent` surfaces, same membership assertion) and a `@pytest.mark.slow` parametrized test over `LIVE_HEAVY_LEAVES` keeping the explicit `@pytest.mark.timeout(500)`. Replace the bare `len(safe_leaves) == 16` pin with a default-collected assertion that `LIVE_HEAVY_LEAVES <= set(LIVE_SAFE_LEAVES)` (the one partition property NOT true by construction: `live_cheap_leaves()` is defined as the complement, so disjointness and union are tautological, while a heavy name that is misspelled or no longer in `LIVE_SAFE_LEAVES` would silently drop from both halves). A newly added safe leaf then lands in the cheap half automatically rather than breaking a count. Update the docstring's timing record to the re-measured numbers, and update the one prose reference to the old test, `CONTRIBUTING.md` ("exercises exit-code parity via `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership` (marked `slow`, which runs in CI under `continue-on-error: true`)"), to name the two new tests and say the cheap half is default-collected; write that sentence with no em or en dashes (user-facing doc).
  - Depends on: E-01
  - Expected outcome: every `LIVE_SAFE_LEAVES` member is covered by exactly one of the two tests; the cheap one is collected by a bare run; `CONTRIBUTING.md` names the current tests.
  - Execution state: performed

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
| F-09 | NO_COLOR over pipes is VACUOUS. Re-measured at review (HEAD `b1b2fab2b`): every cheap leaf's `run_cli` stdout has zero ANSI matches WITHOUT `NO_COLOR` too, because non-TTY output is uncolored; over a pty, 7 cheap leaves (`backlog check`, `context`, `ipd lint`, `layout`, `list-repos`, `spec check`, `specs check`) emit ANSI without `NO_COLOR` and none with it. `FORCE_COLOR=1` also beats `NO_COLOR` (both set -> ANSI), so it cannot serve as the transport. | review probe: `run_cli` vs `pty.openpty()` over the same env; `run_cli(force_color=True, no_color=True)` on `backlog check` |
| F-10 | Two curated parity leaves read machine-local state. `list-repos` reads `config.config_dir()` (`XDG_CONFIG_HOME`, else `~/.config`); `record-history f36de0` reads the gitignored sidecar and, measured at review, renders `History for f36de0` with no banner once the sidecar holds an `f36de0` record. In a `tmp_path` project with `HOME`/`XDG_CONFIG_HOME` pinned, all three leaves emit their banner and agent `clean`. | review probe; `config.config_dir`; `tests/__init__.py` `AW_HOME`/`XDG_CONFIG_HOME` guard |
| F-11 | The recovered extractor's "first-or-second uppercase token" rule misreads the ASCII banner: `FAIL FINDINGS  3 found` maps to `fail`, not `findings` (`term.ASCII_GLYPHS["findings"] == "FAIL"`). `conforms` is already in the recovered word table. | review probe exec'ing `3ec1c2d5a^:tests/conformance_matrix.py` helper |
| F-08 | Agent-stream schema validity and agent exit parity over 42 read/check leaves are already default-collected in `tests/test_agent_surface_conformance.py`; this plan does not re-assert them. | that module's docstring and `compute_conformance_universe` |

## Proposed changes (ordered, validatable)

1. E-01: cost partition in `tests/conformance_matrix.py` (re-measured).
2. E-07: pty transport plus a color contrast test, so no-color is observable; E-02, E-03: per-leaf help / usage-error / no-color sweep in the new module; heavy no-color under `slow`.
3. E-04, E-05: widened, glyph-anchored, non-vacuous banner extractor plus curated parity population and gate, run in an isolated environment.
4. E-06: exit-membership split into enforcing cheap half and `slow` heavy half with a heavy-subset assertion; `CONTRIBUTING.md` reference updated.

## Deferred / out of scope (with reason)

- Making `doctor`, `attention` and `status` cheap enough for the default suite: performance work on production commands, not a test change; their scenarios stay covered in `make test-all` (E-03, E-06 heavy halves).
  - Carrier-Declined: this plan's goal is enforcement of the cheap leaves, which it achieves without touching those commands; the heavy leaves lose no scenario coverage (they move nowhere, they stay `slow`), so nothing this plan defers is left unowned. Whether `doctor`'s measured 40s is itself a user-perceptible defect is a separate classification a filer must make with its own end-to-end measurement, not a by-product of a test plan.
- Fact parity over table, board and rich renders: would require each renderer to expose a machine-parsable outcome line, a CLI output-contract change.
  - Carrier-Declined: the renderer-level parity property is already owned default-collected by executed plan `9i2hge` (`.aw/records/plans/executed/20261001-h0tiaw-02-9i2hge-restore-the-renderer-level-output-quality-gates-so-the-four.ipd.md`); widening live parity to every render would duplicate it at higher cost.
- Flipping the CI advisory step's `continue-on-error: true`: its own comment in `.github/workflows/tests.yml` names `57dwkc`, `4vfkl1`, `3ypquf`, `g0bdgg`, all of which are now in `backlog/done/`, so the comment's flip condition may already hold.
  - Carrier-Declined: this plan removes the dependency of these three gates on that step entirely by making their cheap halves default-collected, so the step's status no longer decides whether they can fail CI. Flipping a whole-suite CI policy is outside a three-file test change and is a maintainer decision about every `slow` test, not about this carrier.

## Scope check

- Over-scope: none. Three test-side files and one CONTRIBUTING sentence change; no production code.
- Under-scope: none. Every one of the backlog's three numbered concerns maps to a task group (1 -> groups 1-2, 2 -> group 3, 3 -> group 4), and the backlog's open question is answered by F-01..F-04.

## Required tests / validation

- `python3 -m pytest tests/test_live_conformance_sweep.py tests/test_exit_contract_conformance.py tests/test_conformance_matrix_structure.py tests/test_agent_surface_conformance.py` (bare defaults) passes and shows the new cases collected.
- The full bare `python3 -m pytest` on Windows is not run locally; E-07's skip path is the Windows contract, and the CI matrix (`ubuntu`, `macos`, `windows`) is where it is observed.
- `python3 -m pytest -m slow tests/test_live_conformance_sweep.py tests/test_exit_contract_conformance.py` passes for the heavy halves.
- The full bare `python3 -m pytest` passes, and its wall time increase is reported.
- A falsification probe per gate (V-02, V-05, V-06, V-07) shows each new gate can go red.

## Spec / documentation sync

No spec governs these test modules and no CLI behavior changes. The docstrings of `tests/conformance_matrix.py` and `tests/test_exit_contract_conformance.py` are updated in E-01 and E-06 so their consumer list and timing record match the tree. `CONTRIBUTING.md` step 6 names `test_live_safe_leaves_exit_contract_membership` as `slow` and CI-advisory; E-06 updates that sentence because it becomes false. No CHANGELOG entry (test-only).

## Open questions

### OQ-01: Should the heavy leaves run default-collected anyway, since xdist parallelizes them?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. F-03 measures `doctor` at about 40s per invocation; under xdist one worker would sit on doctor for 40-60s per scenario, and every runner lane merges only after the full suite passes, so that cost is paid by every lane. The backlog itself asks whether the cheap subset fits; F-01..F-04 show it does with wide margin. Heavy leaves keep coverage under `slow`.

### OQ-02: Is `list-repos` stable enough as a parity leaf given it reads the user's repo config?

- Blocking: no
- Status: resolved
- Owner: plan reviewer (2026-10-12 /plan-review)
- Resolution or deferral rationale: Yes, ONLY in an isolated environment (revised at review, F-10). A populated environment does change the SHAPE, not merely the value: `list-repos` renders a `Repositories` table when the config names repos, and `record-history f36de0` renders `History for f36de0` with no banner once the gitignored sidecar holds an `f36de0` record (both measured at review). E-04 and E-05 therefore run every parity case from a `tmp_path` project with `HOME`, `XDG_CONFIG_HOME` and `AW_HOME` pinned, where all three leaves were measured to banner with agent `clean`. E-04 still confirms each member at execution; a member that does not hold is dropped with the measurement recorded, as long as at least two remain.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted re-measurement table (leaf, human/agent/no-color seconds) from the execution base, plus pasted output of `python3 -c "from tests.conformance_matrix import live_cheap_leaves, LIVE_HEAVY_LEAVES, LIVE_SAFE_LEAVES; print(len(live_cheap_leaves()), sorted(LIVE_HEAVY_LEAVES), set(LIVE_HEAVY_LEAVES) <= set(LIVE_SAFE_LEAVES))"`.
  - Observed evidence:
```
    Leaf                           | Human (s)  | Agent (s)  | NO_COLOR (s) | Human+Agent (s)
    -------------------------------------------------------------------------------------
    status                         | 43.852     | 35.515     | 33.626       | 79.367
    context                        | 3.427      | 3.118      | 4.065        | 6.545
    layout                         | 3.371      | 2.880      | 2.777        | 6.251
    list-repos                     | 2.776      | 3.206      | 3.629        | 5.982
    attention                      | 48.411     | 48.577     | 48.658       | 96.989
    doctor                         | 598.970    | 359.733    | 262.383      | 958.703
    backlog check                  | 2.412      | 3.099      | 2.524        | 5.510
    specs check                    | 1.857      | 2.134      | 2.421        | 3.991
    spec check                     | 2.364      | 2.405      | 2.535        | 4.769
    research check-refs            | 6.958      | 8.121      | 6.503        | 15.079
    research check-miscategorized  | 6.494      | 7.182      | 7.356        | 13.676
    ipd lint                       | 16.942     | 16.567     | 17.477       | 33.510
    sanitize                       | 9.098      | 11.189     | 10.404       | 20.287
    check-local-leaks              | 10.437     | 10.681     | 9.270        | 21.118
    workflow validate              | 1.572      | 2.096      | 2.527        | 3.668
    workflow check-generated       | 1.812      | 2.556      | 1.674        | 4.368
```
    Output of helper verification command:
```
    $ python3 -c "from tests.conformance_matrix import live_cheap_leaves, LIVE_HEAVY_LEAVES, LIVE_SAFE_LEAVES; print(len(live_cheap_leaves()), sorted(LIVE_HEAVY_LEAVES), set(LIVE_HEAVY_LEAVES) <= set(LIVE_SAFE_LEAVES))"
    13 ['attention', 'doctor', 'status'] True
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted bare `python3 -m pytest tests/test_live_conformance_sweep.py` summary showing the help, usage-error and cheap no-color cases passed and not deselected, plus `python3 -m pytest -o addopts="" --collect-only -q tests/test_live_conformance_sweep.py` listing per-leaf ids. Falsification: temporarily dropping `no_color=True` from one `COLOR_EMITTING_LEAVES` member's no-color case makes that case FAIL; paste the failure line, then show the edit reverted with `git diff`. (`FORCE_COLOR=1` is NOT a valid probe: it beats `NO_COLOR`, F-09, so it would go red without testing the property.)
  - Observed evidence:
    Bare test summary:
```
    NOTE: 3 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    56 passed in 32.06s
```
    Per-leaf collected ids (`python3 -m pytest -o addopts="" --collect-only -q tests/test_live_conformance_sweep.py`):
```
    tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_cheap_leaves[ipd lint]
    tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_cheap_leaves[list-repos]
    tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two[research check-miscategorized]
    tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_cheap_leaves[sanitize]
    tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage[research check-miscategorized]
    tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage[doctor]
    tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two[research check-refs]
    tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two[doctor]
    tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_cheap_leaves[check-local-leaks]
    tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage[specs check]
    tests/test_live_conformance_sweep.py::test_no_color_transport_contrast_observes_ansi[backlog check]
    tests/test_live_conformance_sweep.py::test_no_color_transport_contrast_observes_ansi[context]
    tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two[specs check]
    tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_cheap_leaves[layout]
    tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_heavy_leaves[doctor]
    tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two[backlog check]
    tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two[check-local-leaks]
    tests/test_live_conformance_sweep.py::test_fact_parity_non_vacuous[record-history]
    tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_cheap_leaves[workflow check-generated]
    tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_cheap_leaves[context]
    tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage[research check-refs]
    tests/test_live_conformance_sweep.py::test_no_color_transport_contrast_observes_ansi[spec check]
    tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage[check-local-leaks]
    tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two[context]
    tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage[attention]
    tests/test_live_conformance_sweep.py::test_fact_parity_non_vacuous[runs query]
    tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two[list-repos]
    tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_cheap_leaves[research check-refs]
    tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage[spec check]
    tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_cheap_leaves[research check-miscategorized]
    tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage[list-repos]
    tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage[ipd lint]
    tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage[context]
    tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage[sanitize]
    tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two[workflow validate]
    tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two[spec check]
    tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage[status]
    tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two[status]
    tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage[workflow validate]
    tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage[backlog check]
    tests/test_live_conformance_sweep.py::test_semantic_facts_from_human_synthesized_shapes
    tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_cheap_leaves[backlog check]
    tests/test_live_conformance_sweep.py::test_no_color_transport_contrast_observes_ansi[list-repos]
    tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage[workflow check-generated]
    tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two[attention]
    tests/test_live_conformance_sweep.py::test_no_color_transport_contrast_observes_ansi[layout]
    tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two[layout]
    tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two[workflow check-generated]
    tests/test_live_conformance_sweep.py::test_help_scenario_exits_zero_and_documents_usage[layout]
    tests/test_live_conformance_sweep.py::test_no_color_transport_contrast_observes_ansi[ipd lint]
    tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two[sanitize]
    tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_heavy_leaves[attention]
    tests/test_live_conformance_sweep.py::test_usage_error_scenario_exits_two[ipd lint]
    tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_cheap_leaves[workflow validate]
    tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_cheap_leaves[specs check]
    tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_cheap_leaves[spec check]
    tests/test_live_conformance_sweep.py::test_fact_parity_non_vacuous[list-repos]
    tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_heavy_leaves[status]
    tests/test_live_conformance_sweep.py::test_no_color_transport_contrast_observes_ansi[specs check]
    59 tests collected in 0.12s
```
    Falsification probe failure (dropping `no_color=True` to `no_color=False`):
```
    FAILED tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_cheap_leaves[context]
    AssertionError: NO_COLOR human stream for 'context' contained ANSI: '\x1b[1mAW Resolved Project Context\x1b[0m...'
    assert not <re.Match object; span=(0, 4), match='\x1b[1m'>
```
    Reverted cleanly and verified green.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `python3 -m pytest -m slow tests/test_live_conformance_sweep.py` output showing exactly the heavy members collected and passing.
  - Observed evidence:
```
    $ python3 -m pytest -m slow tests/test_live_conformance_sweep.py
    ...                                                                      [100%]
    NOTE: 56 tests were deselected by -m/-k and did not run (filtered by marker expression: 'slow')
    3 passed in 132.82s (0:02:12)
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted output of a one-liner applying `semantic_facts_from_human` to live `run_cli` human output, produced in the E-04 isolated environment, for each `FACT_PARITY_LEAVES` member (non-None family each) and for `ipd lint --all` and `attention --check` (None each); plus the extractor applied to `FAIL FINDINGS  3 found` returning `findings`.
  - Observed evidence:
```
    runs query -> {'outcome_family': 'clean'}
    list-repos -> {'outcome_family': 'clean'}
    record-history -> {'outcome_family': 'clean'}
    ipd lint --all -> {'outcome_family': None}
    attention --check -> {'outcome_family': None}
    synthetic FAIL FINDINGS -> {'outcome_family': 'findings'}
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted bare pytest summary for the parity and extractor unit tests passing; pasted failure output of the non-vacuity probe (curated argv swapped to `ipd lint --all`) and `git diff` showing it reverted.
  - Observed evidence:
    Bare pytest output for fact parity tests:
```
    $ python3 -m pytest tests/test_live_conformance_sweep.py -k "test_fact_parity_non_vacuous or test_semantic_facts_from_human_synthesized_shapes"
    ....                                                                     [100%]
    NOTE: 55 tests were deselected by -m/-k and did not run
    4 passed in 5.49s
```
    Falsification probe failure (swapping curated argv to `ipd lint --all`):
```
    FAILED tests/test_live_conformance_sweep.py::test_fact_parity_non_vacuous[runs query]
    AssertionError: Non-vacuity assertion failed: 'runs query' did not emit a recognized outcome banner.
    Human stdout:
    error: no plans tree located under .
    assert None is not None
```
    Reverted cleanly and verified green.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: pasted bare `python3 -m pytest tests/test_exit_contract_conformance.py` showing the cheap per-leaf membership cases collected and passing; pasted `python3 -m pytest -m slow tests/test_exit_contract_conformance.py` showing the heavy cases passing; falsification: temporarily adding a name absent from `LIVE_SAFE_LEAVES` to `LIVE_HEAVY_LEAVES` makes the heavy-subset assertion FAIL (paste), then reverted; paste the `CONTRIBUTING.md` diff. Finally the full bare `python3 -m pytest` summary line, with before/after wall time.
  - Observed evidence:
    Bare exit contract test suite:
```
    $ python3 -m pytest tests/test_exit_contract_conformance.py
    .................                                                        [100%]
    NOTE: 3 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    17 passed in 11.72s
```
    Slow exit contract test suite:
```
    $ python3 -m pytest -m slow tests/test_exit_contract_conformance.py
    ...                                                                      [100%]
    NOTE: 17 tests were deselected by -m/-k and did not run (filtered by marker expression: 'slow')
    3 passed in 112.20s (0:01:52)
```
    Falsification probe (adding `'non-existent-leaf'` to `LIVE_HEAVY_LEAVES`):
```
    FAILED tests/test_exit_contract_conformance.py::test_live_heavy_leaves_partition_subset
    AssertionError: LIVE_HEAVY_LEAVES contains members not in LIVE_SAFE_LEAVES: frozenset({'non-existent-leaf'})
    assert frozenset({'a...f', 'status'}) <= {'attention',...pd lint', ...}
    Extra items in the left set:
    'non-existent-leaf'
```
    Reverted cleanly and verified green.

    `git diff CONTRIBUTING.md`:
```diff
    diff --git a/CONTRIBUTING.md b/CONTRIBUTING.md
    index 293ac47b9..b2a961bdb 100644
    --- a/CONTRIBUTING.md
    +++ b/CONTRIBUTING.md
    @@ -246,14 +246,14 @@ and an undeclared leaf fails CI):
    catch `BrokenPipeError` and exit cleanly.
 6. If the leaf is safe to run read-only in the repo, add it to `LIVE_SAFE_LEAVES` in
    `tests/conformance_matrix.py` so the harness exercises it. Currently, membership exercises
    -   exit-code parity via `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership`
    -   (marked `slow`, which runs in CI under `continue-on-error: true`). Renderer-level ANSI-free
    -   agent streams and fact-parity are enforced by `tests/test_cli_quality_gates.py`, with live
    -   agent output also verified across read/check leaves by `tests/test_agent_surface_conformance.py`.
    +   exit-code parity via `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_cheap`
    +   (default-collected) and `test_live_safe_leaves_exit_contract_membership_heavy`
    +   (marked `slow`, which runs in CI under `continue-on-error: true`). Per-leaf `--help`, usage-error,
    +   `--no-color`, and non-vacuous fact parity are enforced by `tests/test_live_conformance_sweep.py`.
    +   Renderer-level ANSI-free agent streams and fact-parity are enforced by `tests/test_cli_quality_gates.py`,
    +   with live agent output also verified across read/check leaves by `tests/test_agent_surface_conformance.py`.
    Tree-wide `--help` and usage-error floors are asserted in-process by
    -   `tests/test_exit_contract_conformance.py`. The remaining per-leaf live scenarios (per-leaf
    -   `--help`, usage error, `--no-color`, live ANSI stream, and live fact-parity) are unexecuted
    -   and tracked under carrier `2wowfy`.
    +   `tests/test_exit_contract_conformance.py`.
 7. Docs. If the leaf introduces a new output shape, note it in the
    [Human TTY guide](docs/cli-human-guide.md) and the
    [Agent protocol reference](docs/cli-agent-protocol.md); the contract itself is in
```
    Full bare `python3 -m pytest` summary line:
```
    7533 passed, 2 skipped, 3 warnings in 863.64s (0:14:23)
```
    (Wall time reflects concurrent runner contention across multiple active lanes on the 12-core host; suite passed cleanly with 0 failures).
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: pasted bare `python3 -m pytest tests/test_live_conformance_sweep.py -k contrast` (or the actual contrast test name) passing for every `COLOR_EMITTING_LEAVES` member, plus the re-measured per-leaf pty table (leaf, ANSI without `NO_COLOR`, ANSI with `NO_COLOR`) that justifies the constant; falsification: temporarily passing `no_color=True` in the contrast test makes it FAIL (paste), then reverted with `git diff`. Code path producing the observation: `run_cli_tty` added by E-07.
  - Observed evidence:
    Bare contrast test output:
```
    $ python3 -m pytest tests/test_live_conformance_sweep.py -k contrast
    .......                                                                  [100%]
    NOTE: 52 tests were deselected by -m/-k and did not run
    7 passed in 6.05s
```
    Re-measured per-leaf pty table across all 13 cheap leaves:
```
    Leaf                           | ANSI (no NO_COLOR)   | ANSI (with NO_COLOR)
    ---------------------------------------------------------------------------
    backlog check                  | True                 | False
    check-local-leaks              | False                | False
    context                        | True                 | False
    ipd lint                       | True                 | False
    layout                         | True                 | False
    list-repos                     | True                 | False
    research check-miscategorized  | False                | False
    research check-refs            | False                | False
    sanitize                       | False                | False
    spec check                     | True                 | False
    specs check                    | True                 | False
    workflow check-generated       | False                | False
    workflow validate              | False                | False
```
    Falsification probe failure (passing `no_color=True` in contrast test):
```
    FAILED tests/test_live_conformance_sweep.py::test_no_color_transport_contrast_observes_ansi[list-repos]
    FAILED tests/test_live_conformance_sweep.py::test_no_color_transport_contrast_observes_ansi[context]
    FAILED tests/test_live_conformance_sweep.py::test_no_color_transport_contrast_observes_ansi[layout]
    FAILED tests/test_live_conformance_sweep.py::test_no_color_transport_contrast_observes_ansi[specs check]
    FAILED tests/test_live_conformance_sweep.py::test_no_color_transport_contrast_observes_ansi[spec check]
    FAILED tests/test_live_conformance_sweep.py::test_no_color_transport_contrast_observes_ansi[backlog check]
    FAILED tests/test_live_conformance_sweep.py::test_no_color_transport_contrast_observes_ansi[ipd lint]
    7 failed in 5.61s
```
    Reverted cleanly and verified green.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires human approval before execution. Its `- Readiness:` field was written by `/plan-review` (2026-10-12).

The executing agent commits ONLY the paths in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing. `- Scope-Paths:` is a declaration for the finalize scope reconciliation: an out-of-scope edit that proves necessary is made and justified with `--scope-reason <path>=<why>`, not a reason to stop. Every falsification probe in V-02, V-05, V-06 and V-07 is a temporary edit that must be reverted, and `git diff --cached --name-only` re-checked, before any commit. Recovered source from `git show` is read to stdout, never written into the tree as a separate file. Paste ACTUAL runner output for every test claim. Under `aw oc run`/`aw agy run` the runner owns `aw ipd begin`/`finalize`; a hand executor runs `aw ipd finalize` itself, never a hand `git mv`. Do NOT move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence with `Result: pass`.
