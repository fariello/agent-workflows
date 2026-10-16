# IPD: Re-measure surviving reach for every rollup key and pass-shared file at HEAD

- Date: 2026-10-16
- Kind: child
- Concern: Rollup backlog `9qvfie` outcome 2 is 764 `triaged-not-mutated` items: 747 production keys (38 `budget-exhausted` + 709 `cost-cap`, including the 3 `property-unidentifiable` keys) and 17 `pass-shared` test files (findings `hpjj44` `## Triaged not mutated`; reconciliation (d)). Their reach numbers were measured at HEAD `3ae697cff` (`## Reach at derivation`), before the routine gate was narrowed (`ad9213cc6`, 2026-10-15) and before Orders 01 and 02 of this Set restore two modules. At derivation, of the 747 keys 459 had ZERO surviving test contexts, 25 were reached only by subprocess, and 263 had at least one surviving context (authoring computation over `## Reach at derivation` joined with `## Triaged not mutated`). Nothing can be decided about them until reach is re-measured at one HEAD.
- Scope: IN: create the Set's findings doc; record a fresh surviving-suite coverage baseline over the FULL `tests/` tree with `tools/replay_coverage_diff.py baseline`; for each of the 747 keys record existence at HEAD and its reach class (`key-gone` / `unreached` / `subprocess-only` / `reached`) with its surviving contexts; re-diff the 17 `pass-shared` files and the 4 recreated files with `tools/replay_coverage_diff.py diff` against that baseline; write the per-key and per-file tables. OUT: mutation probing (Order 05 `rf1xxr`); classifying the missing recreated names (Order 04 `we3kkb`); filing (Order 06 `z2xs98`); any code or test edit.
- Scope-Paths: .aw/records/research/*-trimcarry-01-*.findings.md
- Item-Dependencies: executed:24h56i, executed:x9z0ve
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 9qvfie
- Set: trimcarry
- Order: 3
- Highest E allocated: 04
- Author: opencode
- Id: 8dyt88
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set trimcarry graduating backlog 9qvfie.

## Goal

Turn the 764-item triaged tail into a measured, single-HEAD classification, so every key and file has a reach class that decides whether it is probed, retired, or filed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Findings doc and inputs

- [ ] E-01 Create the doc with `aw research new --kind findings --set trimcarry --order 1 --slug rollup-reach --summary "Reach, mutation and disposition for the 9qvfie rollup outcomes" --apply`. Extract the two input lists from findings `hpjj44` `## Triaged not mutated` into gitignored scratch files under `.aw/state/trimcarry-8dyt88/` (`keys.txt`: every row whose Item Type is `production-key`, expect 747; `files.txt`: every `test-file` row, expect 17). Write `## Inputs` in the new doc: measured HEAD (`git rev-parse HEAD`), both counts, the extraction command, and the note that the backlog body's list of 17 `pass-shared` names differs from `hpjj44` (12 of the backlog's names, for example `tests/test_cli_commands.py`, never existed in git history: `git log --all -- tests/<name>` is empty) so `hpjj44` `## Triaged not mutated` is authoritative, as the backlog item itself says ("details in hpjj44 ## Triaged not mutated").
  - Depends on: none
  - Expected outcome: doc exists with `## Inputs`; counts 747 and 17.
  - Execution state: pending

### Task group 2: Baseline and key classification

- [ ] E-02 Run `python3 tools/replay_coverage_diff.py baseline --out .aw/state/trimcarry-8dyt88/base -- tests/` (the trailing `tests/` is REQUIRED: `pyproject.toml` `testpaths` now selects only a core list, so a bare baseline would measure a fraction of the suite; the tool already adds `-m "not slow and not livecorpus"` in `_build_pytest_cmd`). Paste its printed summary (`head`, `xdist`, `functions`, `subprocess_only`, `wall_s`) into `## Baseline`. Confirm the baseline `head` equals HEAD and that `tests/test_benchmark_runners_reports.py` and `tests/test_run_evidence_completion.py` (Orders 01, 02) are present at HEAD.
  - Depends on: E-01
  - Expected outcome: `baseline.json` at HEAD over the full non-slow suite; summary pasted.
  - Execution state: pending

- [ ] E-03 For each key in `keys.txt` decide: `key-gone` when the function no longer exists in the module at HEAD (use `tools/replay_coverage_diff.py` `extract_functions` on the HEAD file, or the file is absent); otherwise from `baseline.json` `functions[key]`: absent -> `unreached`; `subprocess_only: true` -> `subprocess-only`; else `reached` with the context count. Write `## Key reach` as a table (`Key`, `hpjj44 reason` (`budget-exhausted`/`cost-cap`), `hpjj44 exclusive lines`, `Reach class`, `Surviving contexts` count, and EVERY distinct surviving test FILE the contexts belong to (derived from the FIRST TWO dot-segments of the context name, `tests.<module>[.<Class>].<test>` -> `tests/<module>.py`, confirming each derived path exists at HEAD; count and list any context that does not start with `tests.` or maps to no file instead of dropping it), which Order 05 (`rf1xxr`) uses as its narrowed probe selection) plus a counts table per class that sums to 747, and a per-module count table (module, keys, unreached) for Order 06's grouping. Keep the scratch script under `.aw/state/trimcarry-8dyt88/` and paste its source in the doc's `## Method`. `## Method` MUST also state the selection limit: the baseline excludes `slow` and `livecorpus` tests (`_build_pytest_cmd`), so `unreached` means "unreached by the routine non-slow selection", not "unreached by any test", and Orders 05 and 06 read it that way.
  - Depends on: E-02
  - Expected outcome: 747 rows; class counts sum to 747.
  - Execution state: pending

### Task group 3: Pass-shared and recreated re-diff, and commit

- [ ] E-04 Before committing anything (the diff refuses a baseline whose `head` is not HEAD), run `python3 tools/replay_coverage_diff.py diff 19313eed <the 17 pass-shared paths> tests/test_lane_input_manifest.py tests/test_release_readiness.py tests/test_run_analytics_cli.py tests/test_run_summary_table.py --baseline .aw/state/trimcarry-8dyt88/base --format json > .aw/state/trimcarry-8dyt88/rediff.json`. Write `## Pass-shared re-diff` with one row per pass-shared file: replay verdict, exclusive line total, shared line total, and every function with exclusive lines > 0; classify by the FIRST rule that applies: replay verdict not `pass`/`fail`, or `tests_count` 0 -> `replay-unverified` (the replay did not run the deleted tests, so 0 exclusive lines proves nothing; `deleted_test_replay.py` verdicts `error`, `error-import`, `error-collect`, `no-tests`, `timeout`); > 0 exclusive lines -> `exclusive-now`; else `shared-confirmed`. State in the section that Order 06 (`z2xs98`) must carry a `replay-unverified` file as a gap exactly like `exclusive-now`. Write `## Recreated re-diff` with, for each of the 4 recreated files, its replay verdict and every function with exclusive lines > 0 (key and count): the HEAD file already covers the names it kept, so those exclusive lines are reached only by the deleted-and-not-recreated tests, which is the input Order 04 (`we3kkb`) needs. Run `aw research index`, then commit only the doc: `aw commit <this plan> -- <doc path>`.
  - Depends on: E-03
  - Expected outcome: 17 pass-shared rows (each `shared-confirmed`, `exclusive-now` or `replay-unverified`) and 4 recreated rows; one path-scoped commit of the doc.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Research docs are created with `aw research new`, never hand-named; `aw research index` regenerates a GITIGNORED manifest (`.aw/.gitignore` `records/research/INDEX.json`), so only the doc is committed (precedent: executed `rq3q7v` E-03).
- `tools/replay_coverage_diff.py` keys functions as `agent_workflows/<m>.py::<qualname>` (`_collect_function_coverage`) and records `contexts` per function from `dynamic_context = test_function` (`_make_rc_content`); `subprocess_only` means lines hit with no test context. `diff` refuses a baseline whose `head` differs from HEAD (`run_diff`: "baseline head ... differs from current HEAD").
- The baseline tool forces `-m "not slow and not livecorpus"`; pass `tests/` explicitly because `testpaths` is a core list since `ad9213cc6`. Verified at authoring: `python3 tools/replay_coverage_diff.py baseline --out <scratch> -- tests/test_scope_match.py -p no:xdist` -> `functions: 94`, contexts like `tests.test_scope_match.ScopeMatchUnitTests.test_pathological_glob_avoids_exponential_time`.
- Scope-Paths for a records artifact whose final name is minted at execution uses a glob (`.aw/records/plans/README.md` "Declaring records in Scope-Paths"); `ipd_lifecycle._scope_match` matches `*` within one segment.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | 747 production keys and 17 test files are triaged-not-mutated. | `hpjj44` `## Triaged not mutated`: authoring count of `production-key` rows 747 (709 `cost-cap` + 38 `budget-exhausted`) and 17 `test-file` rows. |
| F2 | At derivation HEAD `3ae697cff`, 459 keys had 0 surviving contexts, 25 were subprocess-only, 263 were reached. | Authoring join of `## Reach at derivation` with the 747 keys (scratch, deleted). |
| F3 | The backlog body's 17 `pass-shared` names are not the findings doc's; 12 never existed. | `git log --all --oneline -- tests/test_cli_commands.py` (and 11 others) empty; `hpjj44` lists e.g. `tests/test_color_output.py`, `tests/test_dir_readmes.py`. |
| F4 | The derivation baseline predates the `testpaths` narrowing, so a re-measure must name `tests/`. | `git show 3ae697cff:pyproject.toml` -> `testpaths = ["tests"]`; HEAD `testpaths` lists 19 core modules. |
| F5 | Review checks at HEAD `a85608c0f`: `aw research new --kind findings --set trimcarry --order 1 --slug rollup-reach` (dry run) would write `.aw/records/research/20261016-trimcarry-01-<id6>-rollup-reach.findings.md`, which `ipd_lifecycle._scope_match` accepts against the Scope-Paths glob (`True`); `tools/replay_coverage_diff.py baseline --out <scratch> -- tests/test_agent_aw_home_containment.py -p no:xdist` printed `head`, `xdist`, `functions: 221`, `subprocess_only: 41`, `wall_s: 14.08`, contexts `tests.test_agent_aw_home_containment.test_...` (module-level form, two segments before the test name); `run_diff` records `verdict` and `tests_count` per file, and `deleted_test_replay.replay_file` yields `error`/`error-import`/`error-collect`/`no-tests`/`timeout` besides `pass`/`fail`; `tests/*.py` carry 26 `mark.slow` and 18 `mark.livecorpus` uses. | Review lane (scratch deleted). |

## Proposed changes (ordered, validatable)

1. Create the doc and extract inputs (E-01).
2. Full-suite baseline at HEAD (E-02).
3. Classify the 747 keys (E-03).
4. Re-diff the 17 pass-shared and 4 recreated files, index, commit (E-04).

## Deferred / out of scope (with reason)

- Mutation probing reached keys: Order 05.
  - Carrier: rf1xxr
- Classifying the missing recreated test names: Order 04.
  - Carrier: we3kkb
- Filing unreached keys and exclusive-now files: Order 06.
  - Carrier: z2xs98

## Scope check

- Over-scope: none.
- Under-scope: none; every one of the 764 items gets a class, and the 4 recreated files get the exclusive-reach input Order 04 needs.

## Required tests / validation

No tests are authored. The measurement's validity is checked by V-02..V-04 (baseline head equals HEAD, class counts sum to 747, 17 re-diff rows).

## Spec / documentation sync

N/A: produces a research record only; no spec or user-facing documentation changes.

## Open questions

### OQ-01: Is shared reach enough to retire a pass-shared file?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: This plan only MEASURES (`shared-confirmed` vs `exclusive-now`). The disposition is Order 06's: an `exclusive-now` file is filed; a `shared-confirmed` file is recorded as declined with the reason that every line it reaches is reached by a surviving test, the same partition rule `hpjj44` used to put it in `pass-shared`. Order 06 flags that decision for human review in its findings section.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `aw research new ... --apply` output with the doc path; pasted `wc -l` of `keys.txt` (747) and `files.txt` (17); the `## Inputs` section as committed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted baseline summary from `tools/replay_coverage_diff.py` `run_baseline` with `head` equal to pasted `git rev-parse HEAD`; pasted `ls tests/test_benchmark_runners_reports.py tests/test_run_evidence_completion.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted per-class counts table summing to 747 (sum shown); pasted output of a `python3 -c` check that every key in `keys.txt` appears exactly once in `## Key reach`; one sample row per non-empty class, cross-checked with a pasted lookup: `baseline.json` `functions[key]` for `reached`/`subprocess-only`/`unreached` (absent for the last), and `extract_functions` on the HEAD file (or the file's absence) for `key-gone`; pasted count of contexts that did not map to a test file (expected 0) and the `## Method` selection-limit sentence.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `## Pass-shared re-diff` table (17 rows, each row's class consistent with its pasted replay verdict, `tests_count` and exclusive total from `rediff.json`) and `## Recreated re-diff` table (4 files); pasted `aw research find --id <doc id6>`; pasted `aw commit` output and `git show --stat HEAD` listing only the doc; `git worktree list` before and after showing no leftover replay worktree.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Prerequisite: Orders 01 (`24h56i`) and 02 (`x9z0ve`) are `executed`, so the baseline includes their restored modules. Scope fence: `- Scope-Paths:` declares only this Set's order-01 findings doc; scratch data lives under the gitignored `.aw/state/`; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. No code or test edits. Paste the ACTUAL output of every command whose numbers enter the doc; never record a number you did not measure. Commit only the doc through `aw commit <plan> -- <doc path>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, finalize through `aw ipd finalize` (under a runner, the runner finalizes).
