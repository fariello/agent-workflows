# IPD: Add a reproducible uncited-deleted-file inventory to the lost-guard census

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `e486tz` asks to audit the trim-deleted test files that no live comment cites. `tools/lost_guard_census.py` already computes that partition (`compute_reach_partition`) but only prints two COUNTS; it never emits the uncited file LIST, so every later step of this Set would have to re-derive the population by hand, which is exactly the irreproducibility the census was built to end (its module docstring: "the SAME number, next week, from a different machine"). Measured at authoring HEAD `fca848304`: `python3 tools/lost_guard_census.py --summary` prints "Uncited deleted files: 209 files holding 3585 removed functions" (the item's 207 / 3,554 is the census's own pinned review baseline at `aa5398132`; the delta is citation cleanup since). Of the 209: 4 were RECREATED at HEAD under the same path (`tests/test_lane_input_manifest.py`, `tests/test_release_readiness.py`, `tests/test_run_analytics_cli.py`, `tests/test_run_summary_table.py`), 13 import nothing from `agent_workflows` under the import rule E-01 defines (18 if only module-level imports were counted, which is why the rule is pinned), 3 import a production module that no longer exists (`wtiso_gate`) and 1 of those imports nothing else from `agent_workflows` (`tests/test_wtiso_taxonomy_freeze.py`), 19 are mixed pin/behavioral and 0 are all-pin by `annotate_candidate_file`.
- Scope: IN: add an `--uncited` section (plus `--format json` for it) to `tools/lost_guard_census.py` that lists, per uncited deleted file of a given trim commit, its path, removed-function count, pin/behavioral annotation, the `agent_workflows` modules it imports with each one's existence at HEAD, and whether the same path exists at HEAD (recreated); deterministic sort by path; behavioral tests over a synthesized `tmp_path` git repo; a `tools/README.md` usage line. OUT: replaying or mutating anything (Orders 02, 03); classifying files (Order 05); changing any existing census count or counting rule.
- Scope-Paths: tools/lost_guard_census.py, tests/test_lost_guard_census.py, tools/README.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 1ub8ex

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 1ub8ex verified (set uncitedaudit, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007. Reviewed at HEAD b1b2fab2b. Import parse rule pinned and Concern/F-04 counts corrected (13 empty, 3 wtiso_gate importers, 140 modules); CLI/JSON contract fully specified for the --from-json consumers; E-02 uses a sibling fixture and subprocess CLI; live counts made context; baseline and unchanged-output checks added; gate itemized. Record: .aw/records/reviews/20261011-uncitedaudit-01-1ub8ex-add-a-reproducible-uncited-deleted-file-inventory-to-the-los.review.md.
- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Make the uncited deleted-file population a committed, re-derivable list with per-file facts, so the audit in Order 05 consumes a tool's output rather than a hand-built list.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Inventory

- [x] E-01 In `tools/lost_guard_census.py`, add a function `compute_uncited_inventory(repo_root, commit, cited_paths)` returning one record per path in `compute_commit_census(repo_root, commit).deleted_paths` that is NOT in `cited_paths` (the same population `compute_reach_partition` puts in `uncited_deleted`), sorted by path, as plain JSON-serializable dicts with exactly these keys:
  - `commit` (the argument as given), `path`.
  - `removed_funcs`: `len(extract_test_functions(git_show(repo_root, f"{commit}^:{path}")))`, so the per-file sum equals `ReachPartition.funcs_in_uncited`.
  - `pin_funcs`, `behavioral_funcs`, `pin_names`: from `annotate_candidate_file(repo_root, commit, path)` (at review, `pin_funcs + behavioral_funcs == removed_funcs` held for all 209 files).
  - `imports`: sorted, de-duplicated `agent_workflows` top-level submodule names, parsed from the same blob with `ast` (the tool reading HISTORICAL TEST BLOBS, not a test reading production source). Rule, pinned because the counts in Concern depend on it: walk EVERY node (`ast.walk`, so function-local imports count; module-level-only parsing gives 18 empty files instead of 13); for `ast.Import`, `agent_workflows.X[.Y...]` contributes `X`; for `ast.ImportFrom` with `level == 0`, `from agent_workflows.X[.Y...] import ...` contributes `X`, and `from agent_workflows import N` contributes `N` only when `<commit>^:agent_workflows/N.py` or `<commit>^:agent_workflows/N/__init__.py` exists (`git cat-file -e`), so a re-exported symbol is not mistaken for a module; bare `import agent_workflows` and relative imports contribute nothing. An unparsable blob yields `imports: []`.
  - `missing_imports`: the subset of `imports` with neither `repo_root/agent_workflows/<name>.py` nor `repo_root/agent_workflows/<name>/` on disk (the census reads the working tree everywhere, e.g. `scan_axis_a`'s `dangling_paths`; "at HEAD" in this plan means that tree).
  - `recreated_at_head`: `(repo_root / path).is_file()`.
  Add CLI flags `--uncited` and `--format {text,json}` (default `text`). `--uncited` is a section flag: it joins the `do_all` exclusion list in `main` (so `--uncited` alone prints ONLY the inventory) but is NOT added to `--all`. Text output: a header naming the commit and the counting rule `RULE_D_ONLY_ALL_DEFS`, one row per record (path, removed, pin, behavioral, recreated, missing imports), then a totals line `Uncited deleted files: <N> files holding <M> removed functions (D-only-all-defs)`. `--format json` with `--uncited` writes ONLY `json.dumps(records, indent=2, sort_keys=True)` to stdout, where `records` is the concatenation over the positional commits in the order given (each record carries its `commit`), so the output parses with `json.loads` and is the file Orders 02 and 04 consume via `--from-json`. `--format json` without `--uncited` exits 2 via `parser.error` (no other section has a JSON form; silently ignoring it would emit text a consumer then fails to parse). Compute `cited_paths` as `scan_axis_a(repo_root, args.commits).cited_paths`, exactly as `main` already does for `print_summary`, so the population equals the summary's "Uncited deleted files" count. Change no existing section's output.
  - Depends on: none
  - Expected outcome: on the execution tree, the `--uncited 19313eed` totals line's file and function counts equal the `--summary 19313eed` "Uncited deleted files" line, re-derived at execution (209 / 3,585 at review HEAD `b1b2fab2b` is context, not the bar); `--uncited --format json 19313eed` parses as a list whose length and `removed_funcs` sum equal those same counts; `--format json` alone exits 2.
  - Execution state: performed

### Task group 2: Tests and docs

- [x] E-02 In `tests/test_lost_guard_census.py`, add a SIBLING fixture method (do not edit `_setup_repo`, whose exact counts four existing tests assert) on `LostGuardCensusSyntheticRepoTests`, which already builds repos under a `tempfile.TemporaryDirectory` (the suite's `tmp_path` equivalent). The fixture commits a before tree with `agent_workflows/present_mod.py`, `agent_workflows/gone_mod.py`, a shipped file citing `tests/test_cited.py`, and four test files; then a trim commit deletes all four test files and `agent_workflows/gone_mod.py`; then a third commit re-adds `tests/test_recreated.py`. The four deleted files: `tests/test_cited.py` (cited), `tests/test_present.py` (imports `present_mod` at module level), `tests/test_gone.py` (imports `gone_mod` INSIDE a test function, exercising the `ast.walk` rule), `tests/test_recreated.py` (imports nothing from `agent_workflows`). Each has a distinct authored test-function count. Assert:
  - `compute_uncited_inventory(repo, trim_sha, scan_axis_a(repo, [trim_sha]).cited_paths)` returns exactly the three uncited paths in sorted order with the authored `removed_funcs`, `imports` (`["present_mod"]`, `["gone_mod"]`, `[]`), `missing_imports` (`[]`, `["gone_mod"]`, `[]`) and `recreated_at_head` (`False`, `False`, `True`) values.
  - The CLI, run as a subprocess `[sys.executable, <tool_path>, "--uncited", "--format", "json", trim_sha]` with `cwd=repo` (the pattern `test_cli_summary_output_and_rules` uses, so the test never changes the pytest process's cwd under xdist), exits 0 and its stdout `json.loads` to a list equal to the function result.
  - The same CLI with `--uncited` and no `--format` exits 0 and its stdout contains `Uncited deleted files: 3 files holding <sum> removed functions` and `RULE_D_ONLY_ALL_DEFS`, and the `--summary` subprocess's reach line for the same fixture reports the same two numbers.
  - `--format json` without `--uncited` exits 2.
  No `livecorpus` marker; nothing under `.aw/records/` is read; no real trim sha is referenced.
  - Depends on: E-01
  - Expected outcome: the new tests pass in the default bare run and would fail if the cited file were included, if `recreated_at_head` were always false, or if function-local imports were skipped.
  - Execution state: performed

- [x] E-03 Add `--uncited` and `--uncited --format json` usage lines to the `### Usage` block of the `## \`lost_guard_census.py\`` section of `tools/README.md`, matching the existing `# comment` + command style, and state that the JSON list is the input for `--from-json` consumers. `tools/README.md` is user-facing prose: no em or en dashes.
  - Depends on: E-01
  - Expected outcome: README section lists the new flags with one sentence each.
  - Execution state: performed

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
| F-04 | Import facts partition the population usefully, and the counts depend on the parse rule, so E-01 pins it. Under E-01's rule: 13 files import no `agent_workflows` module, 3 import the vanished `wtiso_gate` (`tests/test_wtiso_taxonomy_freeze.py` imports only it; `tests/test_containment_predicates.py` and `tests/test_wtiso_adversarial.py` import it alongside live modules), 140 distinct modules are imported (139 live). Module-level-only parsing reports 18 empty files, missing 5 that import inside functions. No `from agent_workflows import <non-module>` and no deeper dotted import occurs in the population. | Review probe (2026-10-12, HEAD `b1b2fab2b`) over `git show 19313eed^:<path>` for all 209 files; the authoring probe's "16 / 1 / 134" used an unstated rule and is superseded. |
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

- Before any edit (start of E-01), run bare `python3 -m pytest` and keep its summary line and the sorted list of failing node ids as the execution-start baseline.
- `python3 -m pytest -o addopts="" tests/test_lost_guard_census.py` passes with the new tests (no extra `-q`: `addopts` is cleared, so one `-q` is harmless, but none is needed).
- `python3 tools/lost_guard_census.py --uncited 19313eed` totals equal the `--summary 19313eed` uncited line on the same tree; `--format json` parses and agrees.
- Existing sections unchanged: `--summary 19313eed` output is byte-identical before and after the change (`diff` of the two captures is empty).
- Bare `python3 -m pytest`, actual summary pasted; failing node ids after minus baseline failing node ids is empty.

## Spec / documentation sync

N/A for specs: no `.spec.md` governs the census (plan `oyh28b` "Spec / documentation sync"). `tools/README.md` is updated (E-03).

## Open questions

### OQ-01: Should the inventory cover `80db6750c` too?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: The function takes `commit` as a parameter, so it does; `80db6750c` deleted zero files (`--summary`: "Files deleted: 0"), so its inventory is empty by construction and needs no special case. With several positional commits the JSON is one flat list whose records each carry `commit` (E-01), so an empty commit simply contributes no records.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: (a) the pasted execution-start bare `python3 -m pytest` summary line (the baseline V-03 compares against); (b) pasted header and totals line of `python3 tools/lost_guard_census.py --uncited 19313eed` and the pasted `--summary 19313eed` "Uncited deleted files" line from the same tree, with equal file and function counts (re-derived now, not compared to 209 / 3,585); (c) pasted output of `python3 tools/lost_guard_census.py --uncited --format json 19313eed | python3 -c 'import json,sys; r=json.load(sys.stdin); print(len(r), sum(x["removed_funcs"] for x in r), sum(x["recreated_at_head"] for x in r)); print(json.dumps(r[:2], indent=2))'`, showing the same two counts plus the recreated count and the first two records with every E-01 key; (d) pasted exit code of `python3 tools/lost_guard_census.py --format json 19313eed` (2); (e) empty `diff` of `--summary 19313eed` captured before E-01's edit and after it.
  - Observed evidence:
    (a) Baseline pytest summary: `7456 passed, 2 skipped, 3 warnings in 964.10s (0:16:04)` (0 failing node ids).
    (b) Header and totals line of `python3 tools/lost_guard_census.py --uncited 19313eed`:
    ```
    ==============================================================================
    UNCITED DELETED FILES (19313eed) - RULE: D-only-all-defs
    ==============================================================================
    ...
    Uncited deleted files: 209 files holding 3585 removed functions (D-only-all-defs)
    ```
    Pasted `--summary 19313eed` reach line from same tree:
    ```
        Uncited deleted files: 209 files holding 3585 removed functions
    ```
    (c) Output of `python3 tools/lost_guard_census.py --uncited --format json 19313eed | python3 -c ...`:
    ```
    209 3585 4
    [
      {
        "behavioral_funcs": 33,
        "commit": "19313eed",
        "imports": [
          "attention",
          "clean_delta",
          "engine",
          "install_wizard",
          "layout_inventory",
          "layout_migration",
          "project_context",
          "project_registry",
          "project_schema",
          "record_producers",
          "storage",
          "term"
        ],
        "missing_imports": [],
        "path": "tests/test_acceptance_matrix.py",
        "pin_funcs": 1,
        "pin_names": [
          "test_e07"
        ],
        "recreated_at_head": false,
        "removed_funcs": 34
      },
      {
        "behavioral_funcs": 5,
        "commit": "19313eed",
        "imports": [
          "attention",
          "engine",
          "install_history",
          "project_context",
          "project_registry",
          "project_schema"
        ],
        "missing_imports": [],
        "path": "tests/test_actions.py",
        "pin_funcs": 0,
        "pin_names": [],
        "recreated_at_head": false,
        "removed_funcs": 5
      }
    ]
    ```
    (d) `python3 tools/lost_guard_census.py --format json 19313eed`: exited with code 2 (`lost_guard_census.py: error: --format json requires --uncited`).
    (e) `diff -u /tmp/summary_19313eed_before.txt /tmp/summary_19313eed_after.txt`: empty diff (exit code 0).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_lost_guard_census.py` summary line showing the new tests collected and passing; plus pasted runs, each in a scratch copy under `/tmp/opencode/` (copy `tools/lost_guard_census.py` and `tests/test_lost_guard_census.py` into `<scratch>/tools/` and `<scratch>/tests/`, then run `PYTHONPATH=<scratch> python3 -m pytest -o addopts="" -p no:cacheprovider --rootdir <scratch> <scratch>/tests/test_lost_guard_census.py` from `<scratch>`; never mutate the tracked file), of the new tests failing under each of three mutants: `recreated_at_head` forced `False`; the cited-path exclusion removed; `ast.walk` replaced by iteration over the module body only. The method was demonstrated at review on an existing test (mutating `annotate_candidate_file`'s pin test to `if False:` gave `1 failed, 4 passed`).
  - Observed evidence:
    `python3 -m pytest -o addopts="" tests/test_lost_guard_census.py`: `6 passed in 2.16s`.
    Scratch mutation runs under `/tmp/opencode/census_mutants`:
    1. Mutant 1 (`recreated_at_head` forced `False`): `FAILED tests/test_lost_guard_census.py::LostGuardCensusSyntheticRepoTests::test_uncited_inventory_and_cli` (`AssertionError: Lists differ: [False, False, False] != [False, False, True]`, `1 failed, 5 passed in 0.93s`).
    2. Mutant 2 (cited-path exclusion removed): `FAILED tests/test_lost_guard_census.py::LostGuardCensusSyntheticRepoTests::test_uncited_inventory_and_cli` (`AssertionError: Lists differ: ['tests/test_cited.py', ...] != ['tests/test_gone.py', ...]`, `1 failed, 5 passed in 0.95s`).
    3. Mutant 3 (`ast.walk` replaced by iteration over `tree.body` only): `FAILED tests/test_lost_guard_census.py::LostGuardCensusSyntheticRepoTests::test_uncited_inventory_and_cli` (`AssertionError: Lists differ: [[], ['present_mod'], []] != [['gone_mod'], ['present_mod'], []]`, `1 failed, 5 passed in 1.06s`).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `git diff tools/README.md` showing the two usage lines and no em or en dash in the added text (`git diff tools/README.md | grep '^+' | grep -c $'\u2014\|\u2013'` prints 0); pasted bare `python3 -m pytest` summary line, and the failing node ids after minus the V-01(a) baseline failing node ids, which must be empty.
  - Observed evidence:
    `git diff tools/README.md`:
    ```diff
    +# Print inventory of uncited deleted files with per-file facts:
    +python3 tools/lost_guard_census.py --uncited
    +
    +# Output uncited inventory as JSON for --from-json consumers:
    +python3 tools/lost_guard_census.py --uncited --format json
    ```
    `git diff tools/README.md | grep '^+' | grep -c $'\u2014\|\u2013'` prints `0`.
    Post-implementation bare `python3 -m pytest`: `7457 passed, 2 skipped, 3 warnings in 806.11s (0:13:26)`.
    Failing node IDs after minus baseline failing node IDs: empty set (0 failures).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT:
- Open questions: OQ-01 is resolved; none remain.
- Scope fence (a declaration, not a stop rule): the change is expected to touch only `- Scope-Paths:`. If an out-of-scope edit proves necessary, make it and justify it at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared path left unmodified).
- Invariants: every existing census section's output and every existing count is unchanged (V-01(e)); the inventory population equals the `--summary` uncited partition by construction (same `cited_paths`, same `deleted_paths`); the tool never writes to the repository.
- Honesty: paste the ACTUAL runner output for every claim; never claim a result you did not run.
- Commit: only the declared paths, through `aw commit <plan> -- <paths>`; verify `git diff --cached --name-only` lists only your paths; never `git add -A`, never `--no-verify`, never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs finalize and the lifecycle move; when executing by hand, finalize with `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms; never a hand `git mv`.
