# IPD: Make aw find read each matched record once instead of rescanning the whole plans and research trees

- Date: 2026-09-25
- Kind: child
- Concern: `aw find plans <selector>` (and `aw find research <selector>`) open every record in the tree twice: once in the resolver's bounded header read and again in a full-tree display rescan, costing about 130ms of a user-visible ~600ms command.
- Scope: Replace the whole-tree `plans_index.scan_plans` / `research_index._scan_docs` call on the SELECTOR branch of `cli._find_type_records` with a per-path entry builder applied only to the resolver's matched paths; the no-selector branch, the matching semantics, and the displayed output stay byte-identical. INCLUDES preserving three behaviors the whole-tree scan currently supplies as side effects and a per-path builder can silently lose: the once-per-scan `artifact_core.get_ignored_dirs` result (a `git ls-files` SUBPROCESS, measured 2.7ms, which must not be re-run per matched path, F-6); the research scan's SKIP of a doc whose name or frontmatter does not parse, which today makes two resolver-matchable files display as "no matching research" (F-7); and `scan_plans`'s unguarded `read_text`, which a per-path builder must not turn into a new exception path (F-8).
- Scope-Paths: agent_workflows/cli.py, agent_workflows/plans_index.py, agent_workflows/research_index.py, agent_workflows/selectors.py, tests/test_find_single_read.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 59t9x5
- Blocks-Release: next
- Set: findonce
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: qfpnrm

## Workflow history
- 2026-09-26 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: qfpnrm verified (set findonce, attempt 1).
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 reviewed (aw set): status set to reviewed

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-701..PR-708, all FIXED, no deferrals. EVERY MEASUREMENT IN THIS PLAN REPRODUCES, which is unusual and worth recording: at review's HEAD `find plans <id6>` opened 1555 files for 777 unique plans with all 777 opened twice, `find plans` (no selector) opened 777 with zero doubles, `find research <id6>` 249/124/124, `find specs` and `find backlog` one double each; the warm in-process split measured `scan_plans` 128.0ms and `resolve` 91.6ms of 323.4ms (plan: 129.6/89.3/316.3), and the cold subprocess best-of-7 was 0.58s against a 0.26s `--version` floor (plan: 0.61s/0.35s). THE MATERIAL FINDINGS ARE THREE BEHAVIORS THE WHOLE-TREE SCAN SUPPLIES THAT A PER-PATH BUILDER LOSES. (a) `scan_plans`/`_scan_docs` each call `artifact_core.get_ignored_dirs` ONCE per scan and it spawns a `git ls-files` subprocess (2.7ms measured); a per-path `plan_entry` computing it internally would spawn one per matched path and could make a multi-match query SLOWER, so the ignored set must be hoisted and passed in (PR-701). (b) `_scan_docs` SKIPS a doc whose filename or frontmatter does not parse, and the resolver does not: measured live, `aw find research template` resolves to two real files and prints "no matching research", so `_doc_entry` must return None for exactly those and E-02 must pin that output (PR-702). (c) `scan_plans` calls `read_text` with NO error handling while the resolver's filename rules deliberately match unreadable files, so on the selector path an unreadable matched plan becomes a NEW crash (PR-703). Also: the sort-order caution is CORRECT but its consequence was overstated, because `pi.query` re-sorts whenever any filter flag is present (PR-704); E-01/E-05's absolute timings are live-artifact measurements needing re-derivation (PR-705); E-01's corpus names selectors that may match nothing (PR-706); the two named old test files are already absent so V-03's `test_plans_index.py` is the only pre-existing guard (PR-707); and the gate was missing most of its required elements (PR-708).
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 59t9x5; re-measured with an audit hook at HEAD: 1508 record opens for 754 plans (every one twice) on `find plans <id6>`, scan_plans 129.6ms of a 316.3ms warm in-process run, 0.61s best cold subprocess.

## Goal

Remove the redundant second read of every record that `aw find <type> <selector>` performs for the `plans` and `research` types, so the command opens each record once plus each MATCHED record once, and drops the ~130ms display rescan, without changing a single byte of output or which records match.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: baseline and guard

- [x] E-01 Capture the BEFORE baseline, before touching code: under `/tmp/opencode/findonce-baseline/`, save `python3 -m agent_workflows find <type> <sel>` stdout for a fixed selector corpus, plus the audit-hook open counter (`sys.addaudithook` counting `open` events on `.aw/records/**.md`) on `find plans <id6>` and `find research <id6>`, and the best-of-5 in-process timer wrapping `plans_index.scan_plans` and `selectors.resolve`.
  BUILD THE CORPUS BY VERIFYING EACH SELECTOR MATCHES SOMETHING, and do not copy the authored list blind. The authored corpus was `plans wqq8ua`, `plans wtiso`, `plans stopladder`, `plans executed`, `plans ctrl`, `plans` (no selector), `research <id6>`, `research` (no selector), `specs c4gd2h`, `backlog 59t9x5`. These are LIVE selectors over a tree that moves: a token that matches nothing yields an empty-result file, and an empty file diffs equal to an empty file, so such an entry silently contributes nothing to E-05's byte-diff while looking like coverage. For each token, first confirm it returns at least one row; replace any that does not with one that does, and RECORD the substitution. The corpus MUST retain, whatever the tokens end up being: at least one single-match id6 selector, at least one MULTI-match selector (a setid), at least one selector with an explicit filter flag (so `pi.query`'s re-sort path is covered, F-9), the no-selector arm for `plans` and for `research`, and at least one generic-branch type (`specs` or `backlog`) as a control that must not change. ALSO capture `python3 -m agent_workflows find research template` (or whatever token resolves to a name/frontmatter-unparseable research doc in the executing tree, see F-7): measured at review it resolves to two real files and prints "no matching research", and that counter-intuitive output is the one E-04 is most likely to change by accident.
  - Depends on: none
  - Expected outcome: one stdout file per corpus entry plus a text file with the open counts and timings; the plans open count is about twice the plan count and the no-selector count is about once. Record the numbers OBSERVED; see V-01 on why they are not compared to this plan's authored figures.
  - Execution state: performed

- [x] E-02 Add `tests/test_find_single_read.py` with a tmp-repo fixture of about 6 plans (two sharing a Set, one executed, one in an `executed/YYYYMM/` shard, one whose `- Status:` has trailing prose so `plans_index._META_RE["Status"]` and `selectors._STATUS_RE` disagree) and 4 research docs (three well-formed, plus ONE whose filename does not parse under `research_contract.parse_name` or whose frontmatter is missing). Tests: (a) `find plans <id6>` opens each plan file at most twice and NON-matched plan files exactly once (audit hook counting per path), (b) the same for `find research <id6>`, (c) `find plans <setid>` output lines equal the lines produced by filtering a full `scan_plans` by the matched paths (the old algorithm, computed inside the test as the oracle), including ordering and the shard's disposition, (d) the Status-disagreement record still MATCHES per the resolver and DISPLAYS the whole-file `plans_index` status.
  ADD (e), THE UNPARSEABLE-RESEARCH-DOC CASE, which is the regression most likely to slip through: assert that a selector resolving to the unparseable doc produces the SAME output after the change as before, namely NO row for it. Measured at review on the live tree: `aw find research template` resolves to `conformance-results-template.md` and `20260712-0156-14-chatgpt-modular-report-template.md` (`selectors.resolve` returns both, kind `substring`) and prints `no matching research`, because `_scan_docs` `continue`s past a doc whose name or frontmatter does not parse and so yields no entry for it. The resolver and the display layer genuinely disagree about which files exist, and the display layer wins (F-7). A per-path `_doc_entry` that returns an entry for such a doc would ADD rows that `find` has never printed.
  ADD (f), THE UNREADABLE-FILE CASE: make one matched plan unreadable (chmod 0, skipped on a platform where that does not deny root) and assert `find plans <selector-matching-it-by-filename>` behaves identically before and after. The resolver's filename rules use `selectors._iter_paths`, whose docstring states "a filename match no longer depends on the body being readable", while `scan_plans` calls `p.read_text(encoding="utf-8")` with NO try/except - today that path is never reached on the selector branch because the whole-tree scan already ran (and would have raised for the whole command), so moving the read onto matched paths only changes WHEN it raises (F-8). Pin whichever behavior HEAD has and require E-04 to preserve it.
  - Depends on: E-01
  - Expected outcome: tests (a) and (b) FAIL at HEAD (non-matched files opened twice); (c), (d), (e) and (f) pass at HEAD, pinning current behavior.
  - Execution state: performed

### Task group 2: the fix

- [x] E-03 In `plans_index`, extract the per-file body of `scan_plans` into `plan_entry(plans_dir: Path, p: Path, *, ignored_dirs: set[str]) -> Optional[Tuple[PlanEntry, List[_core.Drift]]]` returning None for a path `scan_plans` would skip (`_EXCLUDE_NAMES`, `_core.is_ignored_path`, or not under `plans_dir`); make `scan_plans` a loop over it. Do the same in `research_index`: `_doc_entry(research_root, p, *, ignored_dirs)` extracted from `_scan_docs`, preserving every skip and drift branch (non-conformant name, missing/invalid frontmatter).
  `ignored_dirs` IS A REQUIRED PARAMETER, NOT COMPUTED INSIDE, and this is the item's one real design constraint (F-6). Both scans call `_core.get_ignored_dirs(<root>)` ONCE before the loop, and that function SPAWNS A SUBPROCESS (`git ls-files --others --ignored --exclude-standard --directory -z`), measured 2.7ms best / 3.4ms median at review. A `plan_entry` that resolved the ignored set itself would spawn one subprocess per matched path, so a setid selector matching 30 plans would pay ~80ms of new subprocess cost to save a ~130ms scan - turning a clear win into a wash, and making a multi-match query on a large Set potentially SLOWER than today. Keyword-only and no default, so a caller cannot silently skip it and get a wrong skip decision. The caller (E-04) computes it once per `find` invocation.
  Also preserve, exactly: `scan_plans`'s disposition derivation (first path component under `plans_dir`, so a `<disposition>/YYYYMM/` shard keeps its TOP-LEVEL disposition), both plan drift branches (`id-missing`, `id-invalid`), and the `read_text` call's error posture UNCHANGED (see F-8 and E-02(f); do not add a try/except in this item, which would be a behavior change disguised as a refactor).
  - Depends on: E-02
  - Expected outcome: pure refactor; `tests/test_plans_index.py` and E-02's tests unchanged in result. `scan_plans` still makes exactly ONE `get_ignored_dirs` call per invocation.
  - Execution state: performed

- [x] E-04 In `cli._find_type_records`, on the `plans` branch move `pi.scan_plans(plans_dir)` INTO the `else:` (no-selector) arm; on the selector arm compute `ignored_dirs = _core.get_ignored_dirs(plans_dir)` ONCE, build `results` from `pi.plan_entry(plans_dir, p, ignored_dirs=ignored_dirs)` for each resolved matched path, drop Nones, and sort by the same key `scan_plans` iterates in (`sorted` over `Path` objects relative to `plans_dir`, NOT the string sort `_resolve_selectors_with_kinds` returns), then apply the existing `pi.query` filter unchanged. Mirror this on the `research` branch with `ri._doc_entry`. Leave the display loop, `highlight_tokens`, and the `paw8so` comment block intact; update the `selectors.py` "WHERE THE REAL COST IS" note to say the double read was removed by `qfpnrm`.
  THE `Path`-VERSUS-`str` SORT DISTINCTION IS REAL BUT ITS BLAST RADIUS IS NARROWER THAN THIS ITEM IMPLIED, and both halves matter so the executor neither skips it nor over-trusts it. It is real: measured on Python 3.14, `sorted(Path)` and `sorted(str)` genuinely differ (`Path("a/b.md") < Path("a-b/c.md")` is True while the string comparison is False), because `/` sorts below `-`, `.` and `_`. It currently has NO observable effect, for two independent reasons measured at review: (1) the live plans tree is FLAT (no `<disposition>/YYYYMM/` shard exists yet; `find .aw/records/plans -mindepth 2 -type d` is empty), and over the real 777 paths the two orders are IDENTICAL; (2) `pi.query` ends with `sorted(out, key=lambda e: (e.set_id or "", e.order or 0, e.path))`, so ANY query carrying an explicit `--id`/`--set`/`--status`/`--disposition` flag re-sorts and the input order is discarded entirely (`ri.query` likewise sorts by `(set_id, order, id6)`). The order therefore shows ONLY on a selector query with NO filter flag, over a tree containing a shard. Use the `Path` sort anyway - it is what `scan_plans` does, it costs nothing, and the shard case is the one `aw archive plans` is designed to create - but do not report the fix as closing an observable bug, and do not let E-02(c) pass merely because today's flat tree makes both orders agree (construct the shard in the fixture, which E-02 already requires).
  - Depends on: E-03
  - Expected outcome: E-02 (a)-(f) pass; each non-matched record is opened once; `get_ignored_dirs` is called at most once per `find` invocation on the selector path.
  - Execution state: performed

### Task group 3: prove it

- [x] E-05 Re-run E-01's selector corpus into `/tmp/opencode/findonce-after/` and `diff -r` against the baseline; re-run the open counter and the in-process timer on the same commands. Re-run on the SAME working tree as E-01, with no intervening commit that adds or removes a record, or the byte-diff compares two different corpora and a spurious difference reads as a regression. Also assert the SUBPROCESS count did not grow: count `git ls-files` invocations (an audit hook on `subprocess.Popen`, or wrap `artifact_core.get_ignored_dirs`) and show it is the same before and after for a MULTI-match selector, which is the F-6 regression a wall-clock number on a single-match selector would hide.
  - Depends on: E-04
  - Expected outcome: empty diff; plans opens about N_plans + matched (not 2 x N_plans); in-process time drops by roughly the old `scan_plans` share; `get_ignored_dirs` call count unchanged.
  - Execution state: performed

- [x] E-06 Prove the OPPOSITE direction on the no-selector arm, which this plan deliberately does not change: re-run the open counter on `find plans` and `find research` with NO selector and show the count is UNCHANGED from E-01 (one open per record, no doubles). E-04 edits the branch structure around that arm, so a mistake there is as likely as one on the selector arm and nothing else in the plan would catch it.
  - Depends on: E-04
  - Expected outcome: no-selector open counts equal E-01's exactly, with zero records opened twice.
  - Execution state: performed

- [x] E-07 Run `ruff check` and `ruff format --check` on `agent_workflows/cli.py`, `agent_workflows/plans_index.py`, `agent_workflows/research_index.py` and `agent_workflows/selectors.py`. Separate from the suite because `ruff` is a fail-closed pre-commit hook here, so a finding makes the COMMIT fail rather than a test, and discovering that after the suite wastes a round trip.
  - Depends on: E-04
  - Expected outcome: no findings on the four files.
  - Execution state: performed

- [x] E-08 Run the bare suite `python3 -m pytest`.
  - Depends on: E-05, E-06, E-07
  - Expected outcome: all pass.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `aw find` returns ARTIFACTS, not references (`selectors.py` header note, plan `826o13` E-01); `_PRECEDENCE` is frozen semantics. This plan does not touch `selectors.resolve`.
- `plans_index` (display, whole file, `(.+?)` Status) and `selectors` (matching, bounded header, `(\S+)` Status) DELIBERATELY disagree; the `paw8so` comment in `_find_type_records` states the whole-file display answer is authoritative. Keeping both readers, each for its current role, preserves that.
- The old find tests (`tests/test_cli_find.py`, `tests/test_selector_zero_open.py`) were removed by `19313eed` ("trim test suite"), so this plan adds a new focused file rather than extending them. CONFIRMED ABSENT at review, which means `tests/test_plans_index.py` is the ONLY pre-existing guard over `scan_plans` and there is no pre-existing guard at all over `_find_type_records` or `research_index._scan_docs`; E-02 is therefore the whole safety net for this change, not a supplement to one.
- `artifact_core.get_ignored_dirs` SPAWNS A SUBPROCESS (`git ls-files ...`), measured 2.7ms. Both tree scans call it once before their loop. Any per-path extraction must take the result as a parameter.
- `plans_index.query` re-sorts its output by `(set_id, order, path)` and `research_index.query` by `(set_id, order, id6)`, so the order in which entries are BUILT is observable only when no filter flag is supplied.
- The resolver and the display layer disagree about which files EXIST for research: `selectors._iter_paths` yields every non-index `.md`, while `research_index._scan_docs` skips a doc whose name or frontmatter does not parse. Measured live: two such docs exist, and `aw find research template` matches both and prints "no matching research". The display layer wins, and that is the behavior to preserve.
- `selectors._iter_paths`'s docstring records that "a filename match no longer depends on the body being readable", while `scan_plans` calls `read_text` with no guard. The two are reconciled today only because the whole-tree scan runs first.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone.

## Findings

Measured 2026-09-25 in the worktree at HEAD of `feat/graduate-batch3`, warm:

| Command | Record opens | Unique | Opened >= 2x | Note |
|---|---|---|---|---|
| `find plans 4awwg4` | 1508 | 754 | 754 | every plan twice |
| `find plans wqq8ua` | 1509 | 754 | 754 | |
| `find plans` (no selector) | 754 | 754 | 0 | only `scan_plans` runs |
| `find research 4awwg4` | 248 | 124 | 124 | same defect on research |
| `find specs 4awwg4` | 37 | 37 | 0 | generic branch reads matched only |
| `find backlog 4awwg4` | 606 | 604 | 1 | generic branch fine |

- BEFORE (the number V-05 compares against): `find plans wqq8ua` best-of-5 in-process 316.3ms, of which `plans_index.scan_plans` 129.6ms and `selectors.resolve` 89.3ms; cold subprocess best of 7 0.61s (median 0.66s); `aw --version` floor 0.35s.
- Cause: `_find_type_records` calls `pi.scan_plans(plans_dir)` (whole-tree `read_text`) BEFORE branching on `selectors_list`, then keeps only entries whose path is in the resolver's matched set. The research branch does the same with `ri._scan_docs`. The generic branch already reads only `matched_paths`, which is the shape this plan adopts.
- The backlog's caution that unifying the two readers changes matching is honored by NOT unifying them: matching stays in `resolve`, display fields still come from the whole-file `plans_index` parse, just for matched files only.

RE-MEASURED AT REVIEW on the live tree (777 plans, 124 research docs), every authored figure reproducing within tree growth:

| Command | Record opens | Unique | Opened >= 2x |
|---|---|---|---|
| `find plans <id6>` | 1555 | 777 | 777 |
| `find plans` (no selector) | 777 | 777 | 0 |
| `find research <id6>` | 249 | 124 | 124 |
| `find research` (no selector) | 124 | 124 | 0 |
| `find specs <id6>` | 39 | 37 | 1 |
| `find backlog <id6>` | 609 | 607 | 1 |

Warm in-process best-of-5 for `find plans <id6>`: total 323.4ms, `plans_index.scan_plans` 128.0ms, `selectors.resolve` 91.6ms (authored: 316.3 / 129.6 / 89.3). Cold subprocess best-of-7 0.58s, median 0.61s, against a `--version` floor of best 0.26s / median 0.27s (authored: 0.61s / 0.66s / 0.35s). So the ~130ms claim and the "every record twice" claim both hold, and the share of the user-visible command is real.

| Id | Severity | Evidence | Finding |
|---|---|---|---|
| F-6 | HIGH (added at review) | `plans_index.scan_plans` and `research_index._scan_docs` each call `_core.get_ignored_dirs(<root>)` ONCE before their loop; that function runs `subprocess.run(["git","ls-files","--others","--ignored","--exclude-standard","--directory","-z"], ...)`; measured best 2.7ms / median 3.4ms on this tree | A PER-PATH ENTRY BUILDER THAT RESOLVES THE IGNORED SET ITSELF SPAWNS ONE SUBPROCESS PER MATCHED PATH, which can make a multi-match selector SLOWER than the whole-tree scan it replaces: ~30 matched plans would cost ~80ms of new subprocess time to save a ~130ms scan. E-03 as authored gave `plan_entry` the signature `(plans_dir, p)` with no way to pass the set, which invites exactly that. The ignored set must be hoisted to the caller and injected. |
| F-7 | HIGH (added at review) | `research_index._scan_docs` `continue`s for a doc whose `parse_name` fails or whose `parse_frontmatter` returns None; measured: `_scan_docs` yields 122 entries for 124 non-index `.md` files, the two without entries being `conformance-results-template.md` and `20260712-0156-14-chatgpt-modular-report-template.md`; `selectors._iter_files` yields all 124; `selectors.resolve(root,"research","template",...)` returns BOTH files with kind `substring`; `python3 -m agent_workflows find research template` prints `no matching research` | THE RESOLVER MATCHES TWO RESEARCH FILES THE DISPLAY LAYER CANNOT RENDER, and the current output for them is NO ROWS. A per-path `_doc_entry` that returns an entry for an unparseable doc would ADD rows `find` has never printed, which is an output change on a plan whose whole premise is byte-identical output - and it would be invisible to any test that only uses well-formed fixtures. `_doc_entry` must return None for exactly the cases `_scan_docs` skips, and E-02 must pin the counter-intuitive "matches but prints nothing" output. |
| F-8 | MEDIUM (added at review) | `scan_plans`: `text = p.read_text(encoding="utf-8")` with no try/except; `selectors._iter_paths` docstring: "a filename match no longer depends on whether the body happens to be readable"; `selectors._iter_files` skips a file whose header cannot be read, and the `path`/`stem`/`substring` rules deliberately use `_iter_paths` instead | MOVING THE READ ONTO MATCHED PATHS CHANGES WHEN AN UNREADABLE FILE RAISES. Today an unreadable plan makes the whole-tree scan raise for EVERY `find plans` command; after the change it raises only when that file is MATCHED, and a filename rule can match it precisely because filename matching does not require a readable body. Whichever behavior is chosen, it is a change in a failure path that no test covers, so E-02(f) pins HEAD's behavior and E-03 is forbidden from "improving" it silently. |
| F-9 | LOW (added at review) | `plans_index.query` ends `return sorted(out, key=lambda e: (e.set_id or "", e.order or 0, e.path))`; `research_index.query` ends `sorted(out, key=lambda e: (e.set_id, e.order, e.id6))`; measured on Python 3.14, `Path("a/b.md") < Path("a-b/c.md")` is True while `"a/b.md" < "a-b/c.md"` is False; over the real 777 plan paths the two sorts are IDENTICAL, and `find .aw/records/plans -mindepth 2 -type d` finds no shard | E-04'S SORT-ORDER CAUTION IS CORRECT AND ITS CONSEQUENCE WAS OVERSTATED. The `Path`/`str` sorts really do differ (`/` sorts below `-`, `.`, `_`), but the order is observable only for a selector query with NO filter flag over a tree containing a `<disposition>/YYYYMM/` shard: any explicit `--id`/`--set`/`--status`/`--disposition` re-sorts in `query`, and no shard exists yet. Using the `Path` sort is still right (it is what `scan_plans` does, and `aw archive plans` creates shards), but E-02(c)'s fixture must CONTAIN a shard or the test passes vacuously on a flat tree, and the fix must not be reported as closing an observable bug. |
| F-10 | LOW (added at review) | `tests/test_cli_find.py` and `tests/test_selector_zero_open.py` both absent (confirmed by `ls`); no test file in `tests/` matches `find` or `selector` | E-02 IS THE ENTIRE SAFETY NET, not a supplement to one. `tests/test_plans_index.py` guards `scan_plans` alone; nothing guards `cli._find_type_records` or `research_index._scan_docs`. So a behavior change E-02 does not pin will be caught by nothing, which is why the review added cases (e) and (f) and why E-06 pins the untouched no-selector arm. |
| F-11 | LOW (added at review) | The plans corpus grew from 754 (authoring) to 777 (review) and the research corpus stands at 124; E-01's authored corpus names live tokens (`wqq8ua`, `wtiso`, `stopladder`, `executed`, `ctrl`, `c4gd2h`, `59t9x5`) with no check that each matches; an empty result file diffs equal to an empty result file | E-01'S BASELINE CORPUS AND ABSOLUTE FIGURES ARE LIVE-ARTIFACT MEASUREMENTS TREATED AS FIXED. Two consequences. First, a selector that matches nothing in the executing tree produces an empty baseline AND an empty after-file, so E-05's byte-diff passes for it while testing nothing - coverage that looks present and is not. Second, "plans open count equals twice the plan count" and V-05's literal BEFORE values (1509 opens, 316.3ms, 0.61s) will not reproduce exactly, so a literal comparison fails on a correct run. Both are fixed by verifying each selector matches, and by stating the pass condition as the SHAPE and the DELTA against E-01's own freshly recorded baseline. |

## Proposed changes (ordered, validatable)

1. Baseline outputs, opens, and timings, over a corpus each of whose selectors is VERIFIED to match something (E-01).
2. Regression tests pinning open counts, output equivalence, the unparseable-research-doc output and the unreadable-file posture (E-02).
3. Per-file entry builders in `plans_index` and `research_index`, taking the ignored set as a required parameter (E-03).
4. Selector branch uses them on matched paths only, with the ignored set computed once, sorted in `scan_plans` order (E-04).
5. Byte-diff and re-measure including the subprocess count (E-05), pin the untouched no-selector arm (E-06), `ruff` (E-07), full suite (E-08).

## Deferred / out of scope (with reason)

- Interpreter start plus `import agent_workflows.cli` (the ~0.35s `--version` floor) dominates the remaining cost and is a separate concern.
  - Carrier-Declined: not a double read; the backlog explicitly says this item cannot take `find` below that floor, and no measured defect is filed for it here.
- Correcting stale `wtiso` counts in older records.
  - Carrier: kx9md1

## Scope check

- Over-scope: none; specs/backlog/other generic types are already single-read and untouched (re-measured at review: one extra open each, which is the intended single display read of the matched file, see OQ-01).
- Under-scope: the `research` branch has the identical defect (249 opens / 124 docs at review) and is included, since leaving it would leave the same bug live under the same gate. Three further under-scope gaps were found at review and are now IN scope rather than deferred, because each is a way this plan could change output or performance silently: the injected ignored set (F-6), the unparseable-research-doc output (F-7), and the unreadable-file read posture (F-8). E-06 additionally pins the no-selector arm, which E-04 restructures around but does not intend to change.

## Required tests / validation

New `tests/test_find_single_read.py` (E-02) with open-count assertions that fail at HEAD, output-equivalence oracle tests over a fixture that CONTAINS a `<disposition>/YYYYMM/` shard (or E-02(c) passes vacuously, F-9), the unparseable-research-doc case (e) and the unreadable-file case (f); the live-corpus byte diff (E-05) including a `get_ignored_dirs` call-count comparison on a MULTI-match selector; the no-selector arm re-measure (E-06); `ruff` on the four edited modules (E-07); and the bare suite (E-08). Note E-02 is the only test coverage this surface has (F-10).

## Spec / documentation sync

No spec governs `find`'s read strategy; output is unchanged. Only the in-code note in `selectors.py` ("WHERE THE REAL COST IS") is updated so it stops pointing at a fixed defect. N/A for user docs.

## Open questions

### OQ-01: Should the backlog `find` path also be checked for the one doubly-opened record?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: measured 606 opens / 604 unique on `find backlog`; one extra open is not a perceptible cost and comes from the generic branch's `read_text` of a matched file, which is the intended single display read. No action.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: `ls /tmp/opencode/findonce-baseline/` listing one file per corpus entry; the corpus itself written out with, for EACH selector, proof it matched at least one row (a row count), plus a note of any authored token that was substituted and why (F-11); the pasted counter lines showing `opens=` about 2 x `unique=` for the plans and research selector commands and about 1 x for the no-selector commands; and the pasted `scan_plans=` / `resolve=` timing line. RECORD THE NUMBERS OBSERVED AND DO NOT COMPARE THEM TO THIS PLAN'S AUTHORED FIGURES as a pass condition: the corpus size is a live population that grew between authoring (754 plans) and review (777), so the absolute opens and milliseconds will differ again. The pass condition is the SHAPE - selector commands open each record about twice, no-selector commands about once - never a literal count.
  - Observed evidence: Verified baseline corpus of 12 items captured in /tmp/opencode/findonce-baseline/, row counts verified, opens=2x unique for selectors (1649/824 plans, 249/124 research), opens=1x unique for no-selector (824/824 plans, 124/124 research), cold subprocess 0.581s. Detail:
    `ls /tmp/opencode/findonce-baseline/`:
    01-plans-wqq8ua.txt
    02-plans-wtiso.txt
    03-plans-stopladder.txt
    04-plans-executed.txt
    05-plans-ctrl.txt
    06-plans-no-selector.txt
    07-plans-wqq8ua-filter-set.txt
    08-research-jd8qhs.txt
    09-research-no-selector.txt
    10-research-template.txt
    11-specs-c4gd2h.txt
    12-backlog-59t9x5.txt
    counts-and-timings.txt

    Corpus verification and row counts (substituted `research jd8qhs` for placeholder `research <id6>` because `jd8qhs` is a live research doc returning 1 row):
      01-plans-wqq8ua.txt: aw find plans wqq8ua -> 1 lines
      02-plans-wtiso.txt: aw find plans wtiso -> 8 lines
      03-plans-stopladder.txt: aw find plans stopladder -> 5 lines
      04-plans-executed.txt: aw find plans executed -> 706 lines
      05-plans-ctrl.txt: aw find plans ctrl -> 3 lines
      06-plans-no-selector.txt: aw find plans -> 824 lines
      07-plans-wqq8ua-filter-set.txt: aw find plans wqq8ua --set wtiso -> 5 lines
      08-research-jd8qhs.txt: aw find research jd8qhs -> 1 lines
      09-research-no-selector.txt: aw find research -> 122 lines
      10-research-template.txt: aw find research template -> 5 lines
      11-specs-c4gd2h.txt: aw find specs c4gd2h -> 1 lines
      12-backlog-59t9x5.txt: aw find backlog 59t9x5 -> 1 lines

    Open counters:
      find plans wqq8ua: opens=1649 unique=824 opened>=2x=824
      find plans (no selector): opens=824 unique=824 opened>=2x=0
      find research jd8qhs: opens=249 unique=124 opened>=2x=124
      find research (no selector): opens=124 unique=124 opened>=2x=0

    Timings:
      scan_plans min=132.1ms, resolve min=89.0ms
      cold subprocess best-of-7 find plans wqq8ua: 0.581s
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" tests/test_find_single_read.py` run BEFORE E-03/E-04 showing tests (a) and (b) FAILED with an open count of 2 for a non-matched file, and (c), (d), (e) and (f) passed. For (c), additionally paste evidence that the fixture's shard actually exists (the fixture's own file listing showing a path under `executed/<YYYYMM>/`), because on a flat fixture the `Path`/`str` sort orders coincide and (c) passes without testing the ordering it exists to test (F-9). For (e), paste the asserted output showing NO row for the unparseable research doc, since "prints nothing" is the behavior being pinned and an empty assertion would look the same as a missing one.
  - Observed evidence: Ran `python3 -m pytest -o addopts="" tests/test_find_single_read.py` BEFORE E-03/E-04: tests (a) and (b) failed with open count 2 for non-matched files; (c)-(f) passed. Shard existence verified at `executed/202608/20260815-sharded-01-pln004-plan-four.ipd.md`. Output for (e) verified returning empty lines/paths and kind="substring". Detail:
    BEFORE run of `python3 -m pytest -o addopts="" tests/test_find_single_read.py`:
    ```
    FAILED tests/test_find_single_read.py::test_a_find_plans_single_read_non_matched - AssertionError: Non-matched plan 20260920-otherset-01-pln003-plan-three.ipd.md opened 2 times (expected 1)
    FAILED tests/test_find_single_read.py::test_b_find_research_single_read_non_matched - AssertionError: Non-matched research doc 20260920-othertopic-01-res003-third-research.findings.md opened 2 times (expected 1)
    ========================= 2 failed, 4 passed in 0.33s ==========================
    ```
    Fixture shard existence proof for (c):
    `shard_file = plans_dir / "executed" / "202608" / "20260815-sharded-01-pln004-plan-four.ipd.md"`
    `assert shard_file.is_file()` -> True, path under `executed/202608/`.
    Asserted output for (e):
    `lines, paths, matches = cli._find_type_records(tmp_repo, "research", ["template"], args, term)`
    `assert lines == []`
    `assert paths == []`
    `assert len(matches) == 1 and matches[0].kind == "substring"`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_plans_index.py tests/test_find_single_read.py` summary after E-03 alone, with the same pass/fail split as V-02 (refactor changes nothing), and `git diff --stat` showing only `plans_index.py` and `research_index.py` changed by this item. ALSO paste the two new signatures showing `ignored_dirs` is keyword-only with NO default (F-6), and evidence that `scan_plans` still calls `get_ignored_dirs` exactly ONCE per invocation (wrap or count it), which is the property the extraction is most likely to break.
  - Observed evidence: Ran `python3 -m pytest -o addopts="" tests/test_plans_index.py tests/test_find_single_read.py` after E-03: 2 failed, 22 passed. `git diff --stat` showed only plans_index.py and research_index.py modified. Signatures verified keyword-only `ignored_dirs` with no default. get_ignored_dirs called exactly 1 time per invocation. Detail:
    `python3 -m pytest -o addopts="" tests/test_plans_index.py tests/test_find_single_read.py`:
    ```
    tests/test_plans_index.py ..................                             [ 75%]
    tests/test_find_single_read.py F....F                                    [100%]
    ========================= 2 failed, 22 passed in 0.38s =========================
    ```
    `git diff --stat`:
    ```
     agent_workflows/plans_index.py    |  83 ++++++++++------
     agent_workflows/research_index.py | 196 +++++++++++++++++++++-----------------
     2 files changed, 162 insertions(+), 117 deletions(-)
    ```
    Signatures:
    `plan_entry signature: (plans_dir: 'Path', p: 'Path', *, ignored_dirs: 'set[str]') -> 'Optional[Tuple[PlanEntry, List[_core.Drift]]]'`
    `plan_entry ignored_dirs kind: KEYWORD_ONLY default: <class 'inspect._empty'>`
    `_doc_entry signature: (research_root: 'Path', p: 'Path', *, ignored_dirs: 'set[str]') -> 'Tuple[Optional[DocEntry], List[Drift]]'`
    `_doc_entry ignored_dirs kind: KEYWORD_ONLY default: <class 'inspect._empty'>`

    get_ignored_dirs call counts:
    `scan_plans scanned 824 plans; get_ignored_dirs calls = 1`
    `_scan_docs scanned 122 docs; get_ignored_dirs calls = 1`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_find_single_read.py` showing all tests passed, and `grep -n "scan_plans(plans_dir)" agent_workflows/cli.py` showing the call only inside the no-selector arm. ALSO paste the same for `_scan_docs(research_root)` on the research branch, which the authored item did not require and which is the identical edit.
  - Observed evidence: Ran `python3 -m pytest -o addopts="" tests/test_find_single_read.py`: 6 passed in 0.34s. Grep confirmed `scan_plans(plans_dir)` and `_scan_docs(research_root)` only called inside no-selector arm in cli.py. Detail:
    `python3 -m pytest -o addopts="" tests/test_find_single_read.py`:
    ```
    tests/test_find_single_read.py ......                                    [100%]
    ============================== 6 passed in 0.34s ===============================
    ```
    `grep -n "scan_plans(plans_dir)" agent_workflows/cli.py`:
    `10822:            entries, _drift = pi.scan_plans(plans_dir)`
    `grep -n "_scan_docs(research_root)" agent_workflows/cli.py`:
    `10895:            entries, _drift = ri._scan_docs(research_root)`
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted EMPTY output of `diff -r /tmp/opencode/findonce-baseline /tmp/opencode/findonce-after`, plus a statement that no record was added or removed between the two runs (e.g. `git status --porcelain` on `.aw/records/` unchanged), since a moved corpus makes the diff meaningless in either direction. Pasted AFTER counter lines for the plans and research selector commands showing `opens=` at most `unique=` plus the matched count, each stated BESIDE its own E-01 BEFORE value rather than against this plan's authored numbers. Pasted AFTER in-process timing line showing no `scan_plans` time on the selector path and a total reduced by roughly that amount, again against E-01's own baseline. A best-of-7 cold subprocess time for the same command beside E-01's. AND the `get_ignored_dirs` call count before and after for a MULTI-match selector, equal (F-6): a single-match timing cannot detect the per-path subprocess regression.
  - Observed evidence: `diff -r -x counts-and-timings.txt /tmp/opencode/findonce-baseline /tmp/opencode/findonce-after` output is empty (0 diffs). Records tree unchanged. After open counters dropped to 1 open per non-matched record. Timings improved: selector branch min 93.2ms vs 221.1ms, cold subprocess 0.409s vs 0.581s. Multi-match selector `find plans wtiso` get_ignored_dirs calls remained exactly 1. Detail:
    `diff -r -x counts-and-timings.txt /tmp/opencode/findonce-baseline /tmp/opencode/findonce-after` output:
    (empty, exit code 0)
    `git status --porcelain .aw/records/`:
    (empty, unchanged)

    Open counters (AFTER beside BEFORE):
    find plans wqq8ua:
      BEFORE: opens=1649 unique=824 opened>=2x=824
      AFTER:  opens=826 unique=824 opened>=2x=1  (824 unique + 1 matched + 1 header = 826 opens, exactly 1 opened twice)
    find research jd8qhs:
      BEFORE: opens=249 unique=124 opened>=2x=124
      AFTER:  opens=126 unique=124 opened>=2x=1  (124 unique + 1 matched + 1 header = 126 opens, exactly 1 opened twice)

    Timings (AFTER beside BEFORE):
      BEFORE: scan_plans min=132.1ms, resolve min=89.0ms (total ~221.1ms)
      AFTER:  selector branch (resolve + plan_entry) min=93.2ms (scan_plans omitted on selector path, saving ~128ms)
      BEFORE cold subprocess best-of-7 find plans wqq8ua: 0.581s
      AFTER  cold subprocess best-of-7 find plans wqq8ua: 0.409s (saving 0.172s)

    get_ignored_dirs calls on multi-match selector `find plans wtiso`:
      BEFORE: 1
      AFTER:  1
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: pasted counter lines for `find plans` and `find research` with no selector, AFTER the change, showing counts equal to E-01's no-selector baselines with `opened>=2x=0`.
  - Observed evidence: Verified no-selector open counters AFTER: find plans opens=824, unique=824, opened>=2x=0; find research opens=124, unique=124, opened>=2x=0, exactly matching E-01 baseline. Detail:
    No-selector open counters AFTER (equal to E-01 baselines):
      find plans (no selector): opens=824 unique=824 opened>=2x=0
      find research (no selector): opens=124 unique=124 opened>=2x=0
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: pasted `ruff check` and `ruff format --check` output for `agent_workflows/cli.py`, `agent_workflows/plans_index.py`, `agent_workflows/research_index.py` and `agent_workflows/selectors.py`, showing no findings.
  - Observed evidence: Pre-commit and ruff check / ruff format --check passed cleanly on agent_workflows/cli.py, plans_index.py, research_index.py, and selectors.py. Detail:
    `ruff check agent_workflows/cli.py agent_workflows/plans_index.py agent_workflows/research_index.py agent_workflows/selectors.py`:
    ```
    All checks passed!
    ```
    `ruff format --check agent_workflows/cli.py agent_workflows/plans_index.py agent_workflows/research_index.py agent_workflows/selectors.py`:
    ```
    4 files already formatted
    ```
    Also verified via pre-commit:
    `pre-commit run ruff --files agent_workflows/cli.py agent_workflows/plans_index.py agent_workflows/research_index.py agent_workflows/selectors.py` -> Passed
    `pre-commit run ruff-format --files agent_workflows/cli.py agent_workflows/plans_index.py agent_workflows/research_index.py agent_workflows/selectors.py` -> Passed
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: the pasted final summary line of bare `python3 -m pytest` showing `N passed` and no failures.
  - Observed evidence: Ran bare `python3 -m pytest`: 2391 passed, 1 skipped, 3 warnings in 38.69s. Detail:
    `python3 -m pytest`:
    ```
    2391 passed, 1 skipped, 3 warnings in 38.69s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A performance fix to `aw find` with a byte-identical-output promise. `aw find plans <selector>` and `aw find research <selector>` currently open every record in the tree TWICE (re-measured at review: 1555 opens for 777 plans, all 777 doubled), because the display layer rescans the whole tree after the resolver has already read every header. The fix reads only the MATCHED records for display, removing about 128ms of a user-visible ~320ms warm command and about the same share of a 0.58s cold one. The plan is `Work-Kind: bug` with `Blocks-Release: next` because the repository's perceptibility test treats a measured, user-waited-on inefficiency as a defect, and the measurement is recorded rather than asserted. THE RISK IS ENTIRELY IN OUTPUT EQUIVALENCE, not in the speedup, and review found three specific ways it could break silently: a per-path builder that re-runs `get_ignored_dirs` would spawn a `git ls-files` subprocess per matched path and could make a multi-match query slower (F-6); a per-path research builder that renders a doc whose name or frontmatter does not parse would ADD rows that `find` has never printed, since two such docs exist and `aw find research template` currently matches both and prints "no matching research" (F-7); and moving `read_text` onto matched paths changes when an unreadable file raises (F-8). Each is now an explicit constraint with a pinning test. There is no pre-existing test over `cli._find_type_records` or `research_index._scan_docs`, so E-02 is the whole safety net (F-10).

SCOPE FENCE, stated as a DECLARATION for reconciliation, not as a stop directive. `agent_workflows/plans_index.py`: extract `plan_entry` and make `scan_plans` loop over it. `agent_workflows/research_index.py`: the same for `_doc_entry`/`_scan_docs`. `agent_workflows/cli.py`: only the `plans` and `research` branches of `_find_type_records`, moving the tree scan into the no-selector arm and building matched-path entries on the selector arm. `agent_workflows/selectors.py`: the "WHERE THE REAL COST IS" comment only. `tests/test_find_single_read.py` is new. EXPLICITLY NOT IN SCOPE: `selectors.resolve`, `_PRECEDENCE`, `_iter_files`/`_iter_paths` and every matching rule; the `plans_index`/`selectors` Status-regex disagreement, which is preserved deliberately and not unified; the generic branch for `specs`/`backlog`/other types, already single-read; `pi.query`/`ri.query` and their sort keys; the display loop, `highlight_tokens` and the `paw8so` comment block; and the interpreter-start floor (Deferred). An out-of-scope edit is to be MADE and then JUSTIFIED through `aw ipd finalize --scope-reason`, never silently.

HARD MUST: paste the ACTUAL output for every `V-*`. Never claim a command passed without running it. Four claims here are specifically easy to certify falsely and are named for that reason: E-01's corpus (a selector matching nothing produces an empty file that diffs clean against an empty file, so prove each matched something); E-02(c)'s ordering (a flat fixture makes both sort orders coincide, so prove the shard exists); E-05's byte-diff (a corpus that moved between runs makes the diff meaningless, so prove the tree did not change); and E-05's subprocess count (a single-match timing cannot see the per-path `git ls-files` regression, so count it on a multi-match selector). Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

STOP AND REPORT, for a genuinely unsafe condition only: if `_doc_entry` cannot be made to skip exactly the docs `_scan_docs` skips without duplicating frontmatter-parsing logic, since that would mean the extraction changes which records exist; or if the byte-diff shows a difference that is NOT explained by a corpus change, which means output equivalence failed and the premise of the plan is broken.

This plan is `reviewed` (review complete; NOT approved) and requires explicit human approval before execution. The executor commits only the `- Scope-Paths:` files via `aw commit qfpnrm -- <paths>`, never `git add -A`, and never pushes. LIFECYCLE TRANSITION: the plan reaches `executed/` only after every `V-*` carries concrete observed evidence and `aw ipd lint --phase pre-transition` conforms. Under `aw oc run` / `aw agy run` the RUNNER owns that transition and the executor must not hand-roll it; run by hand, the executor completes it with `aw ipd finalize` (never a hand-rolled `git mv`). Source item `59t9x5` is already `graduated` and carries `- Blocks-Release: next`, which this plan inherits, so that gate is discharged by this plan reaching `executed` rather than by editing the item.
