# IPD: Run the uncited-file audit and record each file's verdict and derived property in a findings doc

- Date: 2026-10-11
- Kind: child
- Concern: Orders 01, 02 and 04 build the instruments; nothing yet RUNS them over the real population or records the answer. Backlog `e486tz` asks for the audit itself, and an audit whose results live in scrollback is not reproducible or reviewable. The population at authoring HEAD `fca848304` is 209 uncited deleted files holding 3,585 removed functions (`python3 tools/lost_guard_census.py --summary`), 102,815 lines of test source, so the classification must be mechanical first and human-judged only where the data cannot decide.
- Scope: IN: run `lost_guard_census.py --uncited --format json 19313eed` (Order 01), `deleted_test_replay.py --from-json` over that inventory (Order 02), and `replay_coverage_diff.py baseline` plus `diff --from-json` (Order 04); assign every file exactly one verdict from the closed set below by the precedence rule in E-03; write the inventory, verdicts, per-file touched-function data and every command with its pasted summary into ONE research findings doc created with `aw research new --kind findings`; refresh the (gitignored, local) research index. Verdicts: `recreated` (path exists at HEAD; compare test names, record overlap), `subject-retired` (an import failure on an `agent_workflows` module or symbol absent everywhere at HEAD), `api-moved` (an import failure on an `agent_workflows` symbol that exists elsewhere at HEAD; name where), `replay-env-limited` (a failure caused by the replay environment, not the product, including an import of a `tests.*` helper that the same trim deleted, a `no-tests` or `error` replay verdict, or a fixture absent at HEAD; name the cause), `fail-investigate` (at least one product-caused failure, i.e. a failing test whose message is not an import or environment failure, or an unexplained `timeout`; list failing nodeids), `pass-exclusive` (the tests that ran without an import or environment failure pass, and the replay touches at least one function with non-empty `exclusive_lines`), `pass-shared` (as `pass-exclusive`, but every touched function is fully shared), `no-product-reach` (touches no `agent_workflows` function; record what it does exercise). OUT: deriving properties (Order 06), mutation (Order 07), filing items (Order 08), editing any test or production file.
- Scope-Paths: .aw/records/research/
- Item-Dependencies: executed:1ub8ex, executed:nzzu8n, executed:sk2rbf
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 5
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8d0qsg

## Workflow history
- 2026-10-14 executed (aw agy run model=Gemini-4-Argon-High): aw agy run self-finalize: 8d0qsg verified (set uncitedaudit, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007. Reviewed at HEAD 550035bde. E-03 gets ordered verdict rules that read failing-test import messages (function-local imports report fail, demonstrated) and route trim-deleted tests.* helpers to replay-env-limited; index is gitignored so only the doc is committed; one-HEAD pinning and replay.json authority; V-items demand path-set and function-sum reconciliation; gate itemized. Record: .aw/records/reviews/20261011-uncitedaudit-05-8d0qsg-run-the-uncited-file-audit-and-record-each-file-s-verdict-an.review.md.

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Produce a committed, re-derivable findings doc assigning every uncited trim-deleted test file one evidence-backed verdict, so later orders work from a fixed, reviewable list.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Measure

- [x] E-01 First capture the execution-start state outside the repo: `git rev-parse HEAD`, `git status --short`, and `git worktree list` (E-02 compares against these). Create the findings doc: `aw research new --kind findings --slug uncited-trim-audit --set uncitedaudit --summary "Per-file verdicts for the uncited 19313eed-deleted test files" --apply` (the dry run accepted `--set uncitedaudit` at review; if the tool now refuses it, use the setid it suggests and record that). Run `python3 tools/lost_guard_census.py --uncited --format json 19313eed > <tmp>/inv.json` and `python3 tools/lost_guard_census.py --summary 19313eed`, then record the HEAD sha, the doc's id6 (Order 06 locates the doc by it), both commands, the `--summary` "Uncited deleted files" line, and the inventory's file count and `removed_funcs` sum in a `## Inventory` section. All tool output (JSON) goes under a temp dir outside the repo; only summaries and tables go into the doc.
  - Depends on: none
  - Expected outcome: one new `*.findings.md` under `.aw/records/research/` whose `## Inventory` records HEAD and inventory totals equal to `--summary`'s uncited line on the same HEAD (re-derived at execution; 209 / 3,585 is authoring context, not the bar).
  - Execution state: performed

- [x] E-02 Run the replay over the inventory (`python3 tools/deleted_test_replay.py 19313eed --from-json <inv.json> --format json > <tmp>/replay.json`) and the coverage pair (`python3 tools/replay_coverage_diff.py baseline --out <tmp>/base` then `diff 19313eed --from-json <inv.json> --baseline <tmp>/base --format json > <tmp>/diff.json`). Run all three on the HEAD E-01 recorded and make no commit between them: `diff` refuses a `baseline.json` whose `head` differs from `HEAD` (`sk2rbf` E-04), and line numbers are only comparable on one tree. Record each command, wall time and summary counts per replay verdict in a `## Measurements` section, plus the number of paths whose `diff.json` `verdict` differs from `replay.json`'s (the coverage run replays each file a second time; `replay.json` is authoritative for E-03, and any mismatch is listed by path). Verify `git status --short` outside `.aw/records/research/` and `git worktree list` both equal E-01's captures.
  - Depends on: E-01
  - Expected outcome: `replay.json` and `diff.json` each hold exactly one entry per inventory path (same path set); measurement summary recorded; status and worktree list unchanged.
  - Execution state: performed

### Task group 2: Classify and record

- [x] E-03 Assign each file one verdict from the Scope's closed set by the FIRST rule that matches, in this order, so no file can satisfy two:
  1. `recreated_at_head` true in the inventory -> `recreated` (replay still runs and its data is recorded; `overwrote_head_path` is true for these).
  2. A FILE-WIDE import failure: replay `error-import`, or replay `fail` where NO test passed and every failing test's junit message contains `ModuleNotFoundError` or `ImportError`. Classify by the missing name: a `tests.*` module that the same trim deleted (e.g. `tests.test_run_analytics_export`) -> `replay-env-limited`; an `agent_workflows` module in the inventory's `missing_imports`, or a symbol with no definition at HEAD (`git grep -nwE "^\s*(def|class) <name>" HEAD -- agent_workflows` empty) -> `subject-retired`; a symbol defined elsewhere at HEAD -> `api-moved` (name the new location). A PARTIAL import failure (some tests pass) does not match here: a function-local import fails at RUN time, so the file reports `fail`, not `error-import` (demonstrated at review on `tests/test_wtiso_taxonomy_freeze.py`: 2 failed / 5 passed, both messages `ImportError: cannot import name 'wtiso_gate' from 'agent_workflows'`). Treat its import-failing tests as explained, list them with their missing name in the row's reason, and classify the file by rules 4 and 5 over its other tests, so its passing tests' exclusive reach is not discarded.
  3. Replay `no-tests`, `error`, or `error-collect` not caused by the product -> `replay-env-limited` with the cause.
  4. Any failing test not explained by rule 2, `error-collect` with a product cause, or `timeout` -> `fail-investigate` (list failing nodeids and the first assertion line of each, up to 5).
  5. Otherwise (every test not explained by rule 2 passes): no touched `agent_workflows` function in `diff.json` -> `no-product-reach`; any touched function with non-empty `exclusive_lines` -> `pass-exclusive`; else `pass-shared`.
  Rules 1 and 5 are mechanical; rules 2 to 4 cite the deciding message. Write a `## Verdicts` table with one row per file: path, removed funcs, pin funcs, replay verdict, audit verdict, touched functions with exclusive line counts (top 5 by exclusive lines), the rule number that decided it, and a one-line reason for every judged (rule 2 to 4) verdict. Add a `## Verdict totals` table (files and `removed_funcs` per verdict) whose file total equals the inventory count and whose function total equals the inventory's `removed_funcs` sum.
  - Depends on: E-02
  - Expected outcome: every inventory path appears exactly once; totals reconcile; no verdict outside the closed set.
  - Execution state: performed

- [x] E-04 Write a `## Candidates for Order 06` section listing every `pass-exclusive` and `fail-investigate` file and, for each, the production functions with exclusive reach (for `pass-exclusive`) or the failing nodeids (for `fail-investigate`), grouped by production function key `agent_workflows/<module>.py::<qualname>` with the deleted files that reach it and each file's exclusive line count for it. Reach is per FILE: `diff.json` does not attribute lines to individual deleted tests, so name the file's tests only where a failing nodeid or the file's single test identifies them; Order 06 reads the test bodies itself (`anzu8q` Scope). Then run `aw research index` (it regenerates the GITIGNORED `INDEX.json`/`INDEX.md`, `.aw/.gitignore:50-51`, so nothing of it is committed) and commit ONLY the findings doc via `aw commit <this plan> -- <findings doc path>`.
  - Depends on: E-03
  - Expected outcome: grouped candidate list present; `aw research find --id <doc id6>` resolves the doc; `aw research index --check` reports no diagnostic naming the new doc (its pre-existing corpus diagnostics, which fail the exit code at review HEAD, are out of scope); one path-scoped commit containing only the doc.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Durable research the Set relies on goes to `.aw/records/research/` through `aw research new` / `aw research index`, never hand-named (`AGENTS.md` "Durable reference and walkthroughs documentation").
- The census's counts drift as comments change, so the doc records the HEAD it measured (`tools/lost_guard_census.py` docstring "THE REACH BOUND"; plan `oyh28b` V-01 recorded 211 at its HEAD vs 209 now).
- No test or production file is edited in an audit step (`oyh28b` approval gate "This plan produces a REPORT and FILED ITEMS, not fixes").

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Population at authoring: 209 files / 3,585 functions. | `python3 tools/lost_guard_census.py --summary` at `fca848304`. |
| F-02 | 4 files are recreated at HEAD; 3 import the vanished `wtiso_gate` (1 imports nothing else from `agent_workflows`); 13 import no `agent_workflows` module under `1ub8ex`'s pinned `ast.walk` rule. | `1ub8ex` Concern, F-03, F-04 (corrected from 16 at that plan's review). These seed `recreated`, `subject-retired` and likely `no-product-reach`. |
| F-05 | A function-local import of a vanished module fails at RUN time, so the replay reports `fail`, not `error-import`, and the file's other tests still pass. | Review replay of `tests/test_wtiso_taxonomy_freeze.py` in a detached worktree of `550035bde` with `nzzu8n`'s pytest flags: `2 failed, 5 passed`; both junit messages `ImportError: cannot import name 'wtiso_gate' from 'agent_workflows'` (the import is at blob line 254, inside a test). Hence E-03 rule 2 reads failing-test messages, not only the replay verdict. |
| F-06 | Uncited files also import `tests.*` helpers the same trim deleted, which is an environment cause, not a product one. | Review `ast.walk` over the 209 blobs: `tests.test_run_analytics_export` (2 files, itself an uncited deleted file), `tests.fixtures.run_analytics` (1), `tests` / `tests.fixtures` (3 each) absent as modules at HEAD; `tests.support` (46) present. |
| F-07 | The research index is gitignored and `aw research index --check` already exits 1 at review HEAD on pre-existing corpus diagnostics. | `.aw/.gitignore:50-51` (`records/research/INDEX.json`, `INDEX.md`); `.aw/records/research/README.md` "The index"; `aw research index` at `550035bde` exits 1 on `20261001-4xtpvg-00-7so8uz-...assessment.md: frontmatter-invalid` (owned by pending plan `kdje34`), plus 278 `stale-state-to-promote` / `adopted-without-consumer` lines. |
| F-03 | The largest cluster is the `run_*` / `runner*` / `rununify*` files: 34 files, 993 functions, 27,316 lines. | Authoring probe grouping uncited paths by prefix. |
| F-04 | Pin functions are 31 of 3,585 (0 all-pin files, 19 mixed), so pin retirement explains almost none of the population. | `1ub8ex` F-05. |

## Proposed changes (ordered, validatable)

1. Findings doc with inventory (E-01).
2. Replay and coverage measurements (E-02).
3. Per-file verdicts and totals (E-03).
4. Grouped candidate list, local index refresh, commit of the doc only (E-04).

## Deferred / out of scope (with reason)

- Property derivation for candidates: Order 06 (`anzu8q`).
  - Carrier: anzu8q
- Mutation proofs: Order 07 (`rq3q7v`).
  - Carrier: rq3q7v
- Filing items for `fail-investigate` regressions and unguarded properties: Order 08 (`xmr5qj`).
  - Carrier: xmr5qj
- The 89 CITED deleted files: already covered by the census's citation axes and the items plan `oyh28b` filed.
  - Carrier-Evidence: .aw/records/plans/executed/20260930-xvp5vx-01-oyh28b-build-a-reproducible-lost-guard-census-over-the-two-suite-tr.ipd.md

## Scope check

- Over-scope: none.
- Under-scope: none known; if the coverage baseline cannot trace xdist workers, Order 04's serial fallback costs more wall time but not scope. Each file is replayed twice (plain and under coverage); `nzzu8n`'s 300 s default per-file timeout bounds a hung file, and a `timeout` is classified by E-03 rule 4.

## Required tests / validation

- `aw research find --id <doc id6>` resolves the doc after E-04, and `aw research index --check` names no diagnostic against it.
- Verdict totals reconcile with the inventory file count and `removed_funcs` sum.
- `git status --short` shows only the new findings doc before commit, and `git worktree list` equals the execution-start capture.

## Spec / documentation sync

N/A: the deliverable is a research record; no spec or user-facing doc describes this audit.

## Open questions

### OQ-01: Must every `fail-investigate` file be root-caused here?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Here it is enough to separate product-caused failures from replay-environment failures with a one-line reason; deciding "regression vs intended change" is Order 06's derivation, which reads the history for each.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `aw research new` output naming the created path and id6; the pasted `## Inventory` section showing HEAD; and pasted output of `python3 -c 'import json; r=json.load(open("<tmp>/inv.json")); print(len(r), sum(x["removed_funcs"] for x in r))'` beside a pasted `--summary 19313eed` "Uncited deleted files" line from the same HEAD, with equal file and function counts (re-derived now, not compared to 209 / 3,585).
  - Observed evidence:
    - `aw research new --kind findings --slug uncited-trim-audit --set uncitedaudit --summary "Per-file verdicts for the uncited 19313eed-deleted test files" --apply`:
      `create       .aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md`
    - Pasted `## Inventory` section from `.aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md`:
      - Measured `HEAD`: `21b8df8a981b409125f4edd78f15348de02e1875`
      - Findings document `id6`: `hpjj44` (`.aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md`)
      - Commands run: `python3 tools/lost_guard_census.py --uncited --format json 19313eed > <tmp>/inv.json` and `python3 tools/lost_guard_census.py --summary 19313eed`
      - `--summary 19313eed` uncited line: `Uncited deleted files: 208 files holding 3573 removed functions`
      - Inventory JSON one-liner (`python3 -c 'import json; r=json.load(open("<tmp>/inv.json")); print(len(r), sum(x["removed_funcs"] for x in r))'`): `208 3573` (`3542` `behavioral_funcs`, `31` `pin_funcs` across `19` mixed files, `0` all-pin files), matching the `--summary 19313eed` uncited line (`208` files / `3573` removed functions).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted output of a `python3 -c` one-liner printing, for `replay.json` and `diff.json`, the entry count and whether the set of `path` values equals the inventory's, plus `replay.json`'s count per `verdict` and the replay-vs-diff verdict mismatch count; pasted `head` from `baseline.json` equal to E-01's recorded HEAD; pasted `git status --short` and `git worktree list` equal to E-01's captures apart from the new findings doc.
  - Observed evidence:
    - `python3 -c` one-liner over `inv.json`, `replay.json`, `diff.json`, and `baseline.json`:
      `replay_entries: 208 paths_equal_inv: True`
      `diff_entries: 208 paths_equal_inv: True`
      `replay_verdict_counts: {'error-collect': 1, 'error-import': 2, 'fail': 86, 'pass': 118, 'timeout': 1}`
      `diff_verdict_counts: {'error-collect': 1, 'error-import': 2, 'fail': 87, 'pass': 117, 'timeout': 1}`
      `verdict_mismatch_count: 1`
      `  mismatch: ('tests/test_doctor_and_marker.py', 'pass', 'fail')`
      `baseline_head: 21b8df8a981b409125f4edd78f15348de02e1875` (equal to E-01's recorded `HEAD` `21b8df8a981b409125f4edd78f15348de02e1875`)
    - `git status --short` before commit: `?? .aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md` (empty outside `.aw/records/research/`, matching E-01's empty `git status --short`).
    - `git worktree list`: zero `/tmp/deleted_test_replay_*` worktrees remain; lane `<repo-root>/.aw/worktrees/8d0qsg 21b8df8a9 [aw/lane/8d0qsg]` is unchanged from E-01 (unrelated `.aw/worktrees/*` lanes were pruned by concurrent runner activity in the shared repository during the run).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `## Verdict totals` table whose file sum equals the inventory count and function sum equals the inventory `removed_funcs` sum; pasted output of a `python3 -c` check over the doc's `## Verdicts` table showing every inventory path exactly once and no verdict outside the closed set; and three spot-checked judged rows (one each of `fail-investigate`, `replay-env-limited`, `api-moved` or `subject-retired` where present) with the junit message or `error_line` that supports each, including `tests/test_wtiso_taxonomy_freeze.py`'s row if it is still in the inventory.
  - Observed evidence:
    - Pasted `## Verdict totals` table from `.aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md`:
      - `recreated`: 4 files, 154 removed funcs
      - `subject-retired`: 2 files, 31 removed funcs
      - `api-moved`: 0 files, 0 removed funcs
      - `replay-env-limited`: 1 file, 84 removed funcs
      - `fail-investigate`: 80 files, 1413 removed funcs
      - `pass-exclusive`: 95 files, 1694 removed funcs
      - `pass-shared`: 17 files, 111 removed funcs
      - `no-product-reach`: 9 files, 86 removed funcs
      - **Total**: **208** files, **3573** removed funcs (reconciles with `inv.json`: `208` files / `3573` `removed_funcs`).
    - `python3 -c` check over `## Verdicts`:
      `rows: 208 unique_paths: 208 equals_inv_set: True exact_once: True func_sum: 3573 bad_verdicts: []`
    - Spot-checked rows and `tests/test_wtiso_taxonomy_freeze.py`:
      - `subject-retired`: `| tests/test_containment_predicates.py | 19 | 1 | error-import | subject-retired | 0 exclusive (36 shared) | 2 | File-wide import of retired agent_workflows.wtiso_gate (absent at HEAD): ImportError: cannot import name 'wtiso_gate' from 'agent_workflows' (<worktree>/agent_workflows/__init__.py) |`
      - `replay-env-limited`: `| tests/test_run_evidence_completion.py | 84 | 0 | error-collect | replay-env-limited | 0 exclusive (16 shared) | 3 | error-collect (StopIteration): module-level rglob('20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md') at line 1019 fails because spec was renamed to 20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md at HEAD |`
      - `fail-investigate`: `| tests/test_wtiso_adversarial.py | 9 | 0 | fail | fail-investigate | agent_workflows/cli.py::cmd_ipd (2) | 4 | 3 partial import failure(s) on agent_workflows.wtiso_gate (tests.test_wtiso_adversarial.FakeShellGitRefusalTests::test_fake_shell_refuses_mutating_git_in_shared_checkout, tests.test_wtiso_adversarial.GitCommitTrailerRejectionTests::test_missing_or_mismatched_aw_lane_trailer_is_rejected, tests.test_wtiso_adversarial.RelativePathClimbTests::test_relative_path_climbing_out_of_worktree_is_refused: ImportError: cannot import name 'wtiso_gate' from 'agent_workflows' (<worktree>/agent_workflows/__init__.py)); plus 1 unexplained failure(s): tests.test_wtiso_adversarial.NestedPermissionDeadlockTests::test_nested_permission_only_stall_watchdog_now (AssertionError: 1800.0 != 600.0) |`
      - `tests/test_wtiso_taxonomy_freeze.py` (partial import failure explained by rule 2, remaining 5 passing tests classified by rule 5): `| tests/test_wtiso_taxonomy_freeze.py | 7 | 0 | fail | pass-shared | 0 exclusive (9 shared) | 5 | Explained by rule 2 (2 partial import failure(s) on agent_workflows.wtiso_gate (tests.test_wtiso_taxonomy_freeze.GateLibraryTests::test_gate_library_is_single_import_surface, tests.test_wtiso_taxonomy_freeze.GateLibraryTests::test_gate_predicates_refuse_rather_than_silently_allow: ImportError: cannot import name 'wtiso_gate' from 'agent_workflows' (<worktree>/agent_workflows/__init__.py))); remaining 5 passing test(s) classified by rule 5: All 9 touched agent_workflows function(s) have 0 exclusive lines (fully shared with baseline) |`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted `aw research find --id <doc id6>` output resolving the doc; pasted `aw research index --check 2>&1 | grep <doc id6>` output (empty, or only lines the executor explains); pasted `aw commit` output; and `git show --stat HEAD` listing only the findings doc.
  - Observed evidence:
    - `aw research find --id hpjj44`:
      `hpjj44	todo	20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md	Per-file verdicts for the uncited 19313eed-deleted test files`
    - `aw research index --check 2>&1 | grep hpjj44`: empty (0 diagnostics against `hpjj44`).
    - `aw commit 8d0qsg -- .aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md`:
      `aw commit: committed 1 path(s): e085efabd02973c15ef0c85779ae8497372724a0`
    - `git show --stat --oneline e085efabd02973c15ef0c85779ae8497372724a0`:
      `e085efabd work(8d0qsg): Run the uncited-file audit and record each file's verdict and derived property in a findings doc`
      ` ...daudit-01-hpjj44-uncited-trim-audit.findings.md | 1262 ++++++++++++++++++++`
      ` 1 file changed, 1262 insertions(+)`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT: this plan edits no code or tests; it writes one findings doc (the research index it regenerates is gitignored and is not committed) and commits only that doc through `aw commit <plan> -- <findings doc path>`, never `git add -A`, never push. Scope fence: `- Scope-Paths:` declares `.aw/records/research/`; an edit outside it is justified at finalize, not avoided by stopping. Paste the ACTUAL output of every command whose numbers enter the doc or a V-item; never report a count you did not run. Every number in the doc must come from a pasted command run at the recorded HEAD. Under a runner, the runner finalizes; by hand, use `aw ipd finalize`.
