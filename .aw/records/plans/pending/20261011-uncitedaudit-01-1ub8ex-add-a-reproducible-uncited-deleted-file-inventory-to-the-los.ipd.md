# IPD: Add a reproducible uncited-deleted-file inventory to the lost-guard census

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `e486tz` asks to audit the trim-deleted test files that no live comment cites. `tools/lost_guard_census.py` already computes that partition (`compute_reach_partition`) but only prints two COUNTS; it never emits the uncited file LIST, so every later step of this Set would have to re-derive the population by hand, which is exactly the irreproducibility the census was built to end (its module docstring: "the SAME number, next week, from a different machine"). Measured at authoring HEAD `fca848304`: `python3 tools/lost_guard_census.py --summary` prints "Uncited deleted files: 209 files holding 3585 removed functions" (the item's 207 / 3,554 is the census's own pinned review baseline at `aa5398132`; the delta is citation cleanup since). Of the 209: 4 were RECREATED at HEAD under the same path (`tests/test_lane_input_manifest.py`, `tests/test_release_readiness.py`, `tests/test_run_analytics_cli.py`, `tests/test_run_summary_table.py`), 16 import nothing from `agent_workflows`, 1 imports only a production module that no longer exists (`wtiso_gate`), 19 are mixed pin/behavioral and 0 are all-pin by `annotate_candidate_file`.
- Scope: IN: add an `--uncited` section (plus `--format json` for it) to `tools/lost_guard_census.py` that lists, per uncited deleted file of a given trim commit, its path, removed-function count, pin/behavioral annotation, the `agent_workflows` modules it imports with each one's existence at HEAD, and whether the same path exists at HEAD (recreated); deterministic sort by path; behavioral tests over a synthesized `tmp_path` git repo; a `tools/README.md` usage line. OUT: replaying or mutating anything (Orders 02, 03); classifying files (Order 05); changing any existing census count or counting rule.
- Scope-Paths: tools/lost_guard_census.py, tests/test_lost_guard_census.py, tools/README.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 1ub8ex

## Workflow history

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Make the uncited deleted-file population a committed, re-derivable list with per-file facts, so the audit in Order 05 consumes a tool's output rather than a hand-built list.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Inventory

- [ ] E-01 In `tools/lost_guard_census.py`, add a function `compute_uncited_inventory(repo_root, commit, cited_paths)` returning one record per deleted test file of `commit` that is NOT in `cited_paths`, sorted by path, with fields `path`, `removed_funcs` (via `extract_test_functions` over `git_show(<commit>^:<path>)`), `pin_funcs`, `behavioral_funcs`, `pin_names` (via `annotate_candidate_file`), `imports` (sorted `agent_workflows` submodule names the file imports, parsed from the blob with `ast`, which is the tool reading HISTORICAL TEST BLOBS, not a test reading production source), `missing_imports` (those with neither `agent_workflows/<name>.py` nor `agent_workflows/<name>/` at HEAD), and `recreated_at_head` (the path exists in the working tree). Add CLI flags `--uncited` (print a labelled table plus a totals line naming the counting rule `D-only-all-defs`) and `--format {text,json}` (json emits the record list for `--uncited`). Reuse `scan_axis_a(...).cited_paths` exactly as `print_summary` does, so the population equals the summary's "Uncited deleted files" count.
  - Depends on: none
  - Expected outcome: `python3 tools/lost_guard_census.py --uncited 19313eed` prints 209 rows (at authoring HEAD) and a totals line whose file and function counts equal the `--summary` reach-partition line; `--format json` emits the same records.
  - Execution state: pending

### Task group 2: Tests and docs

- [ ] E-02 In `tests/test_lost_guard_census.py`, extend the synthesized `tmp_path` repository (`LostGuardCensusSyntheticRepoTests._setup_repo`) or add a sibling fixture so that the trim deletes one cited file, one uncited file importing an `agent_workflows` module present in the fixture tree, one uncited file importing a module absent from it, and one uncited file that the fixture recreates at the same path after the trim. Assert `compute_uncited_inventory` returns exactly the three uncited paths in sorted order with the authored `removed_funcs`, `missing_imports` and `recreated_at_head` values, and drive `main(["--uncited", "--format", "json", <trim_sha>])` with `cwd` set to the fixture (the scanner uses `Path.cwd()`) and assert the parsed JSON equals the function result and the exit code is 0. No `livecorpus` marker; nothing under `.aw/records/` is read; no real trim sha is referenced.
  - Depends on: E-01
  - Expected outcome: the new tests pass in the default bare run and would fail if the cited file were included or if `recreated_at_head` were always false.
  - Execution state: pending

- [ ] E-03 Add `--uncited` and `--uncited --format json` usage lines to the `lost_guard_census.py` section of `tools/README.md`.
  - Depends on: E-01
  - Expected outcome: README section lists the new flags with one sentence each.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The census is the single committed instrument for trim questions (`tools/lost_guard_census.py` module docstring "THE COMMITTED LOST-GUARD CENSUS SCANNER"); extending it beats a second scanner (P8, single source of truth).
- Tests for it synthesize git history under `tmp_path` and never touch the real trim shas (`tests/test_lost_guard_census.py` module docstring; plan `oyh28b` E-06).
- Tests must exercise behavior, not read production source (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES.md` Section 16). The tool's own `ast` parse of historical test blobs is production behavior and is not a test pin.
- Suite runs bare: `python3 -m pytest`; narrowed runs use `-o addopts=""` (repo-local development contract in `AGENTS.md`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The uncited population is 209 files / 3,585 functions at HEAD; the item's 207 / 3,554 is the pinned baseline. | `python3 tools/lost_guard_census.py --summary` at `fca848304`: "Uncited deleted files: 209 files holding 3585 removed functions"; the same output prints "[Review baseline at aa5398132: 91 cited / 207 uncited files ...]". |
| F-02 | No existing flag emits the file list. | `main` argparse in `tools/lost_guard_census.py` defines `--summary`, `--axis-a`, `--axis-b`, `--axis`, `--classifier`, `--dedupe`, `--triage`, `--all`; `compute_reach_partition` returns only counts (`ReachPartition`). |
| F-03 | 4 uncited paths exist again at HEAD, so "deleted" is not "absent"; the audit must know which. | Authoring probe: `[p for p in uncited if Path(p).exists()]` -> the 4 paths named in Concern. |
| F-04 | Import facts partition the population usefully: 16 files import no `agent_workflows` symbol, 1 imports only a vanished module (`wtiso_gate`), 134 distinct live modules are imported. | Authoring probe over `git show 19313eed^:<path>` for all 209 files. |
| F-05 | Pin annotation: 31 pin vs 3,554 behavioral functions, 19 mixed files, 0 all-pin. | `annotate_candidate_file` over all 209 paths at authoring HEAD. |

## Proposed changes (ordered, validatable)

1. `compute_uncited_inventory` plus `--uncited` / `--format json` (E-01).
2. Synthesized-repo behavioral tests (E-02).
3. README usage (E-03).

## Deferred / out of scope (with reason)

- Classifying each file's verdict: owned by Order 05 (`8d0qsg`) of this Set, which consumes this output.
  - Carrier: 8d0qsg

## Scope check

- Over-scope: none.
- Under-scope: none; the population count may drift from 209 as comments change, which is why the tool prints it rather than this plan pinning it.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_lost_guard_census.py` passes with the new tests.
- `python3 tools/lost_guard_census.py --uncited 19313eed` totals equal the `--summary` uncited line on the same tree.
- Bare `python3 -m pytest`, actual summary pasted; no new failures versus a baseline run taken at execution start.

## Spec / documentation sync

N/A for specs: no `.spec.md` governs the census (plan `oyh28b` "Spec / documentation sync"). `tools/README.md` is updated (E-03).

## Open questions

### OQ-01: Should the inventory cover `80db6750c` too?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The function takes `commit` as a parameter, so it does; `80db6750c` deleted zero files (`--summary`: "Files deleted: 0"), so its inventory is empty by construction and needs no special case.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted head and totals line of `python3 tools/lost_guard_census.py --uncited 19313eed`, pasted `--summary` reach-partition lines from the same tree showing equal file and function counts, and the first two records of `--uncited --format json 19313eed`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest -o addopts="" -q tests/test_lost_guard_census.py` summary line; plus a pasted run of the new test after temporarily (in a scratch copy under `/tmp`, never the tracked file) forcing `recreated_at_head=False`, showing it fails, so the test is proven sensitive.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff tools/README.md` showing the two usage lines; pasted bare `python3 -m pytest` summary line with no new failures versus the execution-start baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT: commit only the declared `- Scope-Paths:` through `aw commit <plan> -- <paths>`; never `git add -A`, never `--no-verify`, never push. Paste actual runner output for every claim. Under `aw oc run` / `aw agy run` the runner performs finalize and the lifecycle move; by hand, finalize with `aw ipd finalize`, never a hand `git mv`.
