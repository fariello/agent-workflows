# IPD: Re-measure HEAD reach for the 319 budget-exhausted keys and build the probe queue

- Date: 2026-10-17
- Kind: child
- Concern: Backlog `lrnh5f` carries 319 production keys whose final verdict in `b1mx2w` `## Rollup mutation results` is `budget-exhausted`: Order 05 `rf1xxr` of Set `trimcarry` stopped starting probes once cumulative wall time reached its 10,800s cap (10833.66s, `b1mx2w` `## Rollup mutation totals`). Their reach classes were measured at HEAD `86f0d88d` (`b1mx2w` `## Key reach`), and HEAD has moved: `git diff --stat 86f0d88d 476c7b7bd -- agent_workflows` reports 25 production files changed, and 79 of the 319 keys live in those files, so the old reach is stale for a quarter of the queue. The old probe also used whole surviving test FILES as the selection, which is what exhausted the budget: the 292 `reached` keys' file selections total 104,864 collected tests, while the contexts that actually reach them total 25,601 (`b1mx2w` `## All Candidate Production Keys` `Surviving Contexts`).
- Scope: IN: create the Set `trimprobe` findings doc; run one full `tests/` coverage baseline at HEAD; for each of the 319 keys record its reach class, a valid mutation operator, its reaching test node ids count, its surviving test files, an estimated probe cost, and its assigned partition (Order 02, Order 03, Order 04, or a no-probe final verdict); commit the doc. OUT: any mutation probe (Orders 02 to 04); filing (Order 05); any code or test edit.
- Scope-Paths: .aw/records/research/*-trimprobe-01-*.findings.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: lrnh5f
- Set: trimprobe
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: g00ljy

## Workflow history

- 2026-10-17 to-review (opencode): authored review-ready child of Set `trimprobe` graduating backlog `lrnh5f`.
- 2026-10-17 draft (opencode): created.

## Goal

A committed, HEAD-current probe queue for all 319 keys, partitioned so each probe plan fits under its own 10,800s cap, so no key ends `budget-exhausted` for lack of planning a second time.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Inputs and baseline

- [ ] E-01 Create the doc with `aw research new --kind findings --set trimprobe --order 1 --slug budget-probe --summary "HEAD reach, probe queue and mutation verdicts for the 319 lrnh5f budget-exhausted keys" --apply`. Write `## Inputs`: `git rev-parse HEAD`; the key list extracted from `b1mx2w` `## Rollup mutation results` as every row whose `Final verdict` cell is `budget-exhausted` (count MUST be 319), with each row's `Operator` cell; the distinct module count of those keys (measured at authoring as 79 modules, not the 54 the backlog body states; record the measured value and the discrepancy); and paste `git diff --stat 86f0d88d HEAD -- agent_workflows tests | tail -1`. Save the extracted key list as `.aw/state/trimprobe-g00ljy/keys.tsv` (gitignored scratch).
  - Depends on: none
  - Expected outcome: the doc exists with `## Inputs`; the extracted count is 319.
  - Execution state: pending

- [ ] E-02 Run `python3 tools/replay_coverage_diff.py baseline --out .aw/state/trimprobe-g00ljy/base -- tests/` and paste its full stdout (`head`, `xdist`, `functions`, `subprocess_only`, `wall_s`) under `## Baseline`. Confirm its `head` equals the E-01 HEAD. Then run `python3 -m pytest -o addopts= -q --collect-only -p no:randomly -m "not slow and not livecorpus" tests/ > .aw/state/trimprobe-g00ljy/collect.txt` and paste its final summary line; this one collection maps each reaching test function to its collected item count (parametrized instances included).
  - Depends on: E-01
  - Expected outcome: `baseline.json` and `collect.txt` exist under `.aw/state/trimprobe-g00ljy/`; heads match.
  - Execution state: pending

### Task group 2: Classification and partition

- [ ] E-03 With a scratch script under `.aw/state/trimprobe-g00ljy/` (paste its source under `## Method`), classify every key in this order: `key-gone` when `tools.replay_coverage_diff.extract_functions` finds no span for the qualname in the HEAD module (final verdict, no probe); OPERATOR CHECK: when `tools.mutation_probe.apply_operator(<HEAD source>, <qualname>, <operator>)` returns `None`, replace the operator with the first entry of `tools.mutation_probe.OPERATORS` it accepts and record both, and if none is accepted the key is final `unprovable` with reason `no applicable operator`; `unguarded-unreached` when the key is absent from `baseline.json` (final verdict; Reason cell "unreached by the non-slow selection at <E-01 HEAD>", since `slow`/`livecorpus` are excluded, `8dyt88` `## Method`); `subprocess-only` when `subprocess_only` is true (partition `P4`); otherwise `reached`. For every key record its CONTROL FILE as below. For each `reached` key derive its NODE-ID selection by mapping every context (`tests.<module>[.<Class>].<test>`) to `tests/<module>.py[::<Class>]::<test>` with the longest-existing-file-prefix rule of `tools.mutation_probe._node_id_to_selector`, its collected item count `N` from `collect.txt`, its surviving test files, its CONTROL FILE (the deleted file with the most exclusive lines in the key's `hpjj44` `## Derived properties` `Reaching Test Files` cell, read with `git show 19313eed^:<path>` to confirm it exists there; `none` when no row or no such blob), and `est_s = 10 + 0.48 * N` (calibration at authoring HEAD `476c7b7bd`, `-n 6`: a 60-test selection probed in 24.92s and a 963-test selection in 459.68s, Findings F-03). Sort `reached` keys by `(N, key)` ascending and assign `P2` while the cumulative `est_s` is at most 7,200s and `P3` for the rest.
  - Depends on: E-02
  - Expected outcome: every key has exactly one of `key-gone`, `unprovable`, `unguarded-unreached`, `P2`, `P3`, `P4`.
  - Execution state: pending

- [ ] E-04 Write `## Probe queue`: one row per key with columns `Key`, `Operator`, `Operator note`, `Reach class`, `N`, `est_s`, `Surviving test files`, `Control file`, `Partition or final verdict`, in partition order then queue order, plus a summary table of counts per partition and per final verdict that sums to 319 and the summed `est_s` of `P2` and `P3`. The node-id selections are NOT committed (they are re-derived by Orders 02 and 03 at their own HEAD); the surviving files and control files ARE committed because Orders 02 to 04 need them in an isolated worktree (the file-level fallback and the positive control). Run `aw research index`, then commit only the doc with `aw commit <this plan> -- <doc path>`.
  - Depends on: E-03
  - Expected outcome: the table has 319 rows; counts sum to 319; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Research docs are created and indexed only through `aw research new` / `aw research index` (`AGENTS.md` "Durable reference and walkthroughs documentation"); a records artifact whose final name is minted at execution is declared in Scope-Paths by glob (`.aw/records/plans/README.md` "Declaring records in Scope-Paths"), as executed `8dyt88` and `rf1xxr` did.
- `.aw/state/` is gitignored and NOT shared between isolated lane worktrees (`rf1xxr` E-01), so anything a later child needs must be committed in the doc or re-derived in that child's own turn.
- The reach and mutation tooling is `tools/replay_coverage_diff.py` (`baseline` subcommand; coverage `dynamic_context = test_function`, `patch = subprocess`) and `tools/mutation_probe.py` (`apply_operator`, `OPERATORS`, `probe`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Rollup mutation results`, rows with `Final verdict` `budget-exhausted`, parsed at authoring | 319 rows; reach classes 292 `reached`, 25 `subprocess-only`, 2 `unreached` (`render_stream.py::_status_glyph_char`, `render_stream.py::Palette.status`); operators 278 `return-none`, 29 `raise`, 8 `negate-return`, 4 `return-false`; 79 distinct modules. |
| F-02 | `git diff --name-only 86f0d88d 476c7b7bd -- agent_workflows` | 25 production files changed; 79 of the 319 keys are in them, so their `86f0d88d` reach is stale. 21 test files were added in the same range (e.g. `tests/test_core_module_coverage.py`). |
| F-03 | Authoring calibration at HEAD `476c7b7bd` (scratch, nothing committed): `python3 tools/mutation_probe.py agent_workflows/comms.py::validate_ack --op return-none --format json -- -m "not slow and not livecorpus" <3 files>` and the same for `agent_workflows/ipd_schema.py::_parse_item_dependency_edge` with `-n 6` and its 29 surviving files | `killed`, 5 newly failing, `wall_s` 24.92 (60 collected tests); `killed`, 118 newly failing, `wall_s` 459.68 (963 collected tests). Both reported `checkout_status_changed: []`. |
| F-04 | Same key passed as `-- -n 6 -m ... @<argfile>` | `survived`, `wall_s` 5.77: an argfile selection silently ran almost nothing and yielded a FALSE `survived`. Selections must be passed as explicit arguments and preflighted for their collected count (Orders 02 to 04). |
| F-05 | One `--collect-only` over the union of the 292 reached keys' 427 surviving files | `8125/8149 tests collected (24 deselected) in 40.41s`; summed per-key file selections are 104,864 items, versus 25,601 reaching contexts in `b1mx2w`. At `0.48 s/item` the file-level plan costs about 50,000s and the node-id plan about 15,000s, so narrowing to reaching node ids is what makes the queue fit two capped plans. |

## Proposed changes (ordered, validatable)

1. E-01 creates the doc and pins the 319-key input.
2. E-02 records a HEAD baseline and one collection.
3. E-03 classifies, fixes operators and partitions.
4. E-04 writes and commits the queue.

## Deferred / out of scope (with reason)

- Mutation probing of `P2`, `P3`, `P4`: Orders 02 (`lictgf`), 03 (`f4pbs5`), 04 (`pr6lo9`).
  - Carrier: lictgf, f4pbs5, pr6lo9
- Filing restore items and reconciling the 319: Order 05 (`b83dpg`).
  - Carrier: b83dpg

## Scope check

- Over-scope: none. One records doc; scratch data stays under gitignored `.aw/state/`.
- Under-scope: none. Every one of the 319 keys receives a partition or a final verdict in E-03.

## Required tests / validation

- The E-01 extraction count equals 319 and the E-04 summary counts sum to 319.
- The E-02 baseline `head` equals `git rev-parse HEAD`.
- `git status --short` after the commit shows no tracked change outside the doc.

## Spec / documentation sync

N/A: a measurement record only; no behavior, CLI surface or spec-described contract changes, and no `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Probe at file level as `rf1xxr` did, or narrow to reaching node ids?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: narrow to reaching node ids (F-05): file level is about 50,000s, more than four capped plans. Narrowing can miss a test that reaches the key only through a subprocess (coverage records no context for those, `tools.replay_coverage_diff._function_coverage` sets `subprocess_only` from empty contexts), so Orders 02 and 03 re-run any narrowed `survived` at file level before concluding.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `aw research new` output naming the created path; paste the extraction command and its printed count `319`; paste the measured module count and the `git diff --stat` tail line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the full `replay_coverage_diff.py baseline` stdout and `git rev-parse HEAD` showing equal heads; paste the `--collect-only` summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the classification script's printed counts per class and partition (summing to 319), the list of keys whose operator was replaced (or `none`), and the cumulative `est_s` at the `P2`/`P3` boundary showing `P2` at most 7,200s.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `rg -c '^\| \`agent_workflows/' <doc>` scoped to `## Probe queue` showing 319; paste the summary table; paste the `aw commit` output and `git show --stat HEAD` listing only the doc.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Scope fence: `- Scope-Paths:` declares only this Set's order-01 findings doc; scratch data lives under the gitignored `.aw/state/trimprobe-g00ljy/`; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. No code or test edits. Paste the ACTUAL output of every command whose numbers enter the doc; never record a number you did not measure. Commit only the doc through `aw commit <plan> -- <doc path>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, finalize through `aw ipd finalize` (under a runner, the runner finalizes).
