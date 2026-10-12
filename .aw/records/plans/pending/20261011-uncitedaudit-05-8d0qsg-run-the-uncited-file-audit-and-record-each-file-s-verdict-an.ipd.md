# IPD: Run the uncited-file audit and record each file's verdict and derived property in a findings doc

- Date: 2026-10-11
- Kind: child
- Concern: Orders 01, 02 and 04 build the instruments; nothing yet RUNS them over the real population or records the answer. Backlog `e486tz` asks for the audit itself, and an audit whose results live in scrollback is not reproducible or reviewable. The population at authoring HEAD `fca848304` is 209 uncited deleted files holding 3,585 removed functions (`python3 tools/lost_guard_census.py --summary`), 102,815 lines of test source, so the classification must be mechanical first and human-judged only where the data cannot decide.
- Scope: IN: run `lost_guard_census.py --uncited --format json 19313eed` (Order 01), `deleted_test_replay.py --from-json` over that inventory (Order 02), and `replay_coverage_diff.py baseline` plus `diff --from-json` (Order 04); assign every file exactly one verdict from the closed set below; write the inventory, verdicts, per-file touched-function data and every command with its pasted summary into ONE research findings doc created with `aw research new --kind findings`; refresh the research index. Verdicts: `recreated` (path exists at HEAD; compare test names, record overlap), `subject-retired` (replay `error-import` on an `agent_workflows` module absent at HEAD), `api-moved` (replay `error-import` on a symbol that exists elsewhere at HEAD; name where), `replay-env-limited` (collect error or fixture failure caused by the replay environment, not the product; name the cause), `fail-investigate` (replay `fail` with product-caused assertion failures; list failing nodeids), `pass-exclusive` (replay passes and touches at least one function with non-empty `exclusive_lines`), `pass-shared` (replay passes and every touched function is fully shared), `no-product-reach` (touches no `agent_workflows` function; record what it does exercise). OUT: deriving properties (Order 06), mutation (Order 07), filing items (Order 08), editing any test or production file.
- Scope-Paths: .aw/records/research/
- Item-Dependencies: executed:1ub8ex, executed:nzzu8n, executed:sk2rbf
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 5
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8d0qsg

## Workflow history

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Produce a committed, re-derivable findings doc assigning every uncited trim-deleted test file one evidence-backed verdict, so later orders work from a fixed, reviewable list.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Measure

- [ ] E-01 Create the findings doc: `aw research new --kind findings --slug uncited-trim-audit --set uncitedaudit --summary "Per-file verdicts for the uncited 19313eed-deleted test files" --apply` (if the tool refuses the setid, use the setid it suggests and record that), then record HEAD sha, the inventory command and its totals line, and the population counts (files, functions) in a `## Inventory` section. All tool output (JSON) goes under a temp dir; only summaries and tables go into the doc.
  - Depends on: none
  - Expected outcome: one new `*.findings.md` under `.aw/records/research/` with HEAD and inventory totals equal to `--summary`'s uncited line.
  - Execution state: pending

- [ ] E-02 Run the replay over the inventory (`python3 tools/deleted_test_replay.py 19313eed --from-json <inv.json> --format json > <tmp>/replay.json`) and the coverage pair (`python3 tools/replay_coverage_diff.py baseline --out <tmp>/base` then `diff 19313eed --from-json <inv.json> --baseline <tmp>/base --format json > <tmp>/diff.json`). Record each command, wall time and summary counts per replay verdict in a `## Measurements` section. Verify `git status --short` outside `.aw/records/research/` is unchanged.
  - Depends on: E-01
  - Expected outcome: replay and diff JSON cover every inventory path (counts equal); measurement summary recorded.
  - Execution state: pending

### Task group 2: Classify and record

- [ ] E-03 Assign each file one verdict from the Scope's closed set, mechanically where the data decides (`error-import` plus module absence -> `subject-retired`; pass plus exclusive lines -> `pass-exclusive`; pass plus all shared -> `pass-shared`; no touched functions -> `no-product-reach`) and by reading the failure output where it does not (`fail` and `error-collect` -> `fail-investigate` vs `replay-env-limited`; `error-import` of a symbol -> `api-moved` vs `subject-retired`, decided by searching HEAD for the symbol name with `grep -rn "def <name>\|class <name>" agent_workflows`). Write a `## Verdicts` table with one row per file: path, removed funcs, pin funcs, replay verdict, audit verdict, touched functions with exclusive line counts (top 5 by exclusive lines), and a one-line reason for every judged (non-mechanical) verdict. Add a `## Verdict totals` table (files and functions per verdict) whose file total equals the inventory count.
  - Depends on: E-02
  - Expected outcome: every inventory path appears exactly once; totals reconcile; no verdict outside the closed set.
  - Execution state: pending

- [ ] E-04 Write a `## Candidates for Order 06` section listing every `pass-exclusive` and `fail-investigate` file and, for each, the production functions with exclusive reach (for `pass-exclusive`) or the failing nodeids (for `fail-investigate`), grouped by production function key `agent_workflows/<module>.py::<qualname>` with the deleted files and test names that reach it; then run `aw research index` and commit the doc and index via `aw commit <this plan> -- .aw/records/research/`.
  - Depends on: E-03
  - Expected outcome: grouped candidate list present; `aw research index --check` conforms; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Durable research the Set relies on goes to `.aw/records/research/` through `aw research new` / `aw research index`, never hand-named (`AGENTS.md` "Durable reference and walkthroughs documentation").
- The census's counts drift as comments change, so the doc records the HEAD it measured (`tools/lost_guard_census.py` docstring "THE REACH BOUND"; plan `oyh28b` V-01 recorded 211 at its HEAD vs 209 now).
- No test or production file is edited in an audit step (`oyh28b` approval gate "This plan produces a REPORT and FILED ITEMS, not fixes").

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Population at authoring: 209 files / 3,585 functions. | `python3 tools/lost_guard_census.py --summary` at `fca848304`. |
| F-02 | 4 files are recreated at HEAD, 1 imports only a vanished module, 16 import no `agent_workflows` symbol. | `1ub8ex` F-03, F-04. These seed `recreated`, `subject-retired` and likely `no-product-reach`. |
| F-03 | The largest cluster is the `run_*` / `runner*` / `rununify*` files: 34 files, 993 functions, 27,316 lines. | Authoring probe grouping uncited paths by prefix. |
| F-04 | Pin functions are 31 of 3,585 (0 all-pin files, 19 mixed), so pin retirement explains almost none of the population. | `1ub8ex` F-05. |

## Proposed changes (ordered, validatable)

1. Findings doc with inventory (E-01).
2. Replay and coverage measurements (E-02).
3. Per-file verdicts and totals (E-03).
4. Grouped candidate list, index refresh, commit (E-04).

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
- Under-scope: none known; if the coverage baseline cannot trace xdist workers, Order 04's serial fallback costs more wall time but not scope.

## Required tests / validation

- `aw research index --check` conforms after E-04.
- Verdict totals reconcile with the inventory count.
- `git status --short` shows only `.aw/records/research/` changes before commit.

## Spec / documentation sync

N/A: the deliverable is a research record; no spec or user-facing doc describes this audit.

## Open questions

### OQ-01: Must every `fail-investigate` file be root-caused here?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Here it is enough to separate product-caused failures from replay-environment failures with a one-line reason; deciding "regression vs intended change" is Order 06's derivation, which reads the history for each.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `aw research new` output naming the created path, and the pasted `## Inventory` section showing HEAD and totals equal to a pasted `--summary` uncited line from the same HEAD.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted per-verdict counts from `replay.json` and the count of entries in `diff.json`, both equal to the inventory count; pasted `git status --short` showing no change outside `.aw/records/research/`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `## Verdict totals` table whose file sum equals the inventory count, and three spot-checked judged rows (one each of `fail-investigate`, `replay-env-limited`, `api-moved` or `subject-retired` where present) with the replay error line that supports each.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `aw research index --check` output, pasted `aw commit` output, and `git show --stat HEAD` listing only `.aw/records/research/` paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT: this plan edits no code or tests; it writes one findings doc plus the research index and commits them through `aw commit <plan> -- .aw/records/research/`, never `git add -A`, never push. Every number in the doc must come from a pasted command run at the recorded HEAD. Under a runner, the runner finalizes; by hand, use `aw ipd finalize`.
