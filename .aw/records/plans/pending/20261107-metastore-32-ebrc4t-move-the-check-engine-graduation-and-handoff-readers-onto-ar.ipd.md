# IPD: Move the check_engine graduation and handoff readers onto artifact_meta and unify the record skip list

- Date: 2026-11-07
- Kind: child
- Concern: Split from `ffceq0` (Task group 3) under the maintainer's step-complexity rule. This part takes the graduation and handoff subset of the `ffceq0` E-07 site list (19 site lines in 6 functions) and `ffceq0` E-08, the one record skip list (4.4 last bullet), which must follow every check_engine move.
- Scope: FINISHING PART after the round-3 split (2026-11-09, research `nj8zdp` guidance). E-01 and E-02 (the `check_engine` graduation and handoff readers) moved to `dbq57g` (Order 143); the `layout` constants and the `check_engine`, `selectors`, `artifact_refs` and `artifact_core` share of E-03 moved to `i16on1` (Order 144). This plan keeps the rest of E-03 (`ffceq0` E-08): point the inline skip-name copies in `specs`, `releases` and `ipd_lint` at the `layout` constants, and check that one definition remains. EXCLUDES: the other check_engine subsets (Orders 29 to 31) and git-content readers (`t4gl15` family).
- Scope-Paths: agent_workflows/specs.py, agent_workflows/releases.py, agent_workflows/ipd_lint.py, .aw/records/plans/pending/20261107-metastore-32-ebrc4t-move-the-check-engine-graduation-and-handoff-readers-onto-ar.ipd.md
- Item-Dependencies: executed:g5hpbb, executed:tve77h, executed:xexn45, executed:w1cs3p, executed:na188y, executed:i3b5zu, executed:dbq57g, executed:i16on1
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 32
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ebrc4t

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): round-3 split per research nj8zdp; items E-01, E-02 moved to dbq57g; E-03 (constants and the check_engine, selectors, artifact_refs, artifact_core subset) moved to i16on1.
- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from ffceq0 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).
- 2026-11-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

After `dbq57g` moves the graduation and handoff readers and `i16on1` adds the `layout` constants, the last three skip-name copies (`specs`, `releases`, `ipd_lint`) use them, so exactly one skip list remains and no `meta/*.jsonl` file is walked as a record.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Every E-item that moves a reader follows one rule, so a reviewer can check each the same way: (1) BEFORE the edit, add or extend a behavioral test in the named module that pins the reader's CURRENT observable behavior on a `tmp_path` fixture repository (the "prior behavior" column of the reader ledger in `## Findings`), and run it green against the unmodified code; (2) change the reader to call `artifact_meta`; (3) run the same test unchanged. A test that has to change in step 3 is a behavior change and must be one of the decisions listed in the ledger (D-1 to D-5), never a silent one. For every existing module named as a baseline, save the per-test outcome list under the gitignored `.aw/state/ffceq0/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/ffceq0/<E>-before.txt`) before the move and the same command into `<E>-after.txt` after it; `diff` of the two prints nothing except lines a named decision explains. Every saved baseline (command output, JSON, rule counts) also goes under `.aw/state/ffceq0/`, never `/tmp`, so it survives a lane integration. A count measured at authoring (for example the 1,635 executed plans of F-03) is context, never the bar: each expected outcome compares a before and after value re-derived on the same tree. New test modules set `pytestmark = pytest.mark.core`, call real functions or the real `aw` CLI, and never read production source.

The baseline directory stays `.aw/state/ffceq0/`, not this plan's own id6, because the split parent `ffceq0` keeps the final cache-parity, residual-audit and finishing items that compare against these saved files. Commit through `aw commit ebrc4t -- <each changed path>`, one commit per task group allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push.

### Task group 1: the shared skip list, remaining modules

Round-3 note (2026-11-09): E-01 and E-02 moved to `dbq57g`, and the first part of E-03 moved to `i16on1`; both are `- Item-Dependencies:` edges, so E-03's former `Depends on: E-02` is carried by them.

- [ ] E-03 (remaining subset of the original; the constants and the `check_engine`, `selectors`, `artifact_refs` and `artifact_core` share are done by `i16on1`) Replace the remaining record skip-name copies with the ONE list `layout.RECORD_SCAN_SKIP_NAMES` and the ONE excluded records subdirectory constant `layout.RECORD_SCAN_EXCLUDED_DIRS` (both added by `i16on1`): the inline sets with the same three names in `specs` (`skip_names` in `specs._spec_files`), `releases` (the record walkers `count_blocks_release_sentinel`, `check_blocks_release`, `check_from_backlog`) and `ipd_lint` (`_NON_IPD_BASENAMES` and the inline tuple in `_default_pending_files`). Those record walkers consult both constants. So a `meta/*.jsonl` log is never walked as a record.
  - Depends on: none
  - Expected outcome: the `i16on1` fixture tests still pass; `rg -n "_SKIP_NAMES\s*=|_NON_IPD_BASENAMES\s*=|skip_names\s*=" agent_workflows` lists only `layout.py` and the three `_SKIP_NAMES` alias lines of `i16on1`; `tests/test_artifact_refs_rewrite.py` passes unchanged.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

Carried verbatim from `ffceq0` Step 0; where a line says "this plan" it means the split parent `ffceq0`.

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `artifact_meta.history(id6)`, `artifact_meta.query(...)` with typed filters (type, status, Set, order, `depends_on`, `latest_gate_review_of`, `path`) and an `incomplete` list, `artifact_meta.resolve(path_or_id6)`, `artifact_meta.read_at(id6, rev)` (Order 09 only), `artifact_meta.repair(id6, *, confirm=None)`, and the `artifacts.short_description` column. The legacy loader stores a multi-word `- Status:` raw value in a legacy-only column and sets `artifacts.status` only for a single token (tve77h OQ-03, which names this plan as the carrier of the reader decision).
- One status normalizer already exists: `plans.normalize_status` maps `EXECUTED`/`DONE` to `executed` and any other unrecognized token to `plans.LEGACY_GROUP` (`legacy/unknown`); `plans.read_status` applies it to the FIRST token of the whole-file `- Status:` line. `attention._plans_record` and `ipd_lint.lint_text` (M105) already use it.
- `selectors.metadata_region` is the shared region bound (the bullet block before the first `##`, or the YAML fence). The PARITY CONSTRAINT comment above `selectors._STATUS_RE` records the 24-plan disagreement and forbids changing it without "owning that contract change", which D-1 does here.
- Shared history rules: `attention_contract.history_block`, `attention_contract.newest_history_record`, `attention_contract.last_history_at`.
- `aw find` for plans uses `plans_index.plan_entry` and `plans_index.query` for display rows and `selectors.resolve` (through `cli._resolve_selectors_with_kinds`) for selector hits; `aw ipd board` is `cli._run_plans` over `plans.scan`.
- New CLI leaves are declared in `command_surface` (`CommandDeclaration`) and covered by `tests/conformance_matrix.py`. Order 03 (`1ajqaa`) creates `agent_workflows/meta_cli.py` for `aw show --history`, so this plan adds `check meta` and `meta repair` to that module.
- Traversal exclusions live in `layout.TRAVERSAL_EXCLUSIONS` (consumed by `selectors`); `_SKIP_NAMES` is defined separately in `check_engine`, `selectors` and `artifact_refs`.
- Core tier: modules set `pytestmark = pytest.mark.core`; the bare gate is `python3 -m pytest` (30 s budget).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).


## Findings

Carried from `ffceq0` `## Findings` (measured 2026-11-02 at `0cbfcc706`), the rows this part relies on:

| Id | Evidence | Finding |
|---|---|---|
| F-02 | Reader modules by owner (writers are Orders 06/07). THIS PLAN: `selectors` (7 regex sites), `cli` find/search/board paths (`_find_type_records`, `_find_prompt_id6`, `_find_prompt_setid`, `_run_search`, `_run_plans`), `attention` (10), `attention_contract` (history readers), `plans` (3), `check_engine` working-tree readers (30 sites in the module; its 12 `_blob_text` git call sites go to Order 09), `ipd_lint` (5), `ipd_schema.parse_metadata_block` (via its caller), `artifact_refs._SKIP_NAMES`. ORDER 09: `runner_shared` (20), `oc_runipd`, `agy_runipd`, the four hooks, `check_engine` git readers, `plan_readiness.review_staleness_index`, `ipd_lifecycle._release_own_plan_edit_before_landing`, `status_set._prepare_status_change` HEAD read, `plans_index` (6), `plans_archive` (5), `plans_refs` read side, `research_index` (2), `research_archive`, `prompts_index`, `artifact_audit` (1), `review_findings` (1), `review_sequence` (2), `review_tier`, `review_rereview`, `orchestrator_readiness` (1), `production_checks` (5), `work_cmd` (2), `artifact_adopt` (1), `ipd_set_plan`, `completion` | 9 reader modules here, 27 in Order 09; with the writer modules of Orders 06/07 they cover the 59. Comment-only mentions (`term`, `config`, `lifecycle_style`, `command_surface`, docstrings in `agy_runipd`) are not readers. |
| F-06 | 4 records have a `- Status:` bullet only OUTSIDE the metadata region (3 reviews, 1 walkthrough quoting `- Status: approved <- unchanged`); `plans.read_status` (whole file) reads them, the region readers do not | No plan is affected (D-4). |
| F-08 | `history_block(` call sites: `attention` 6, `check_engine` 3; `last_history_at(` and `history_block(` together 10 sites in `attention` and `check_engine` | All history reads in this plan's modules go through `artifact_meta.history`. |
| F-09 | `_SKIP_NAMES = {"README.md", "INDEX.md", "STATUS.md"}` is defined identically in `check_engine`, `selectors` and `artifact_refs`; `layout.TRAVERSAL_EXCLUSIONS` holds 7 directory names | 4.4 asks for one list; E-08 places it in `layout`. |

Step-complexity measurement for this part (2026-11-07, at the worktree HEAD of the split; the rule is that no E-item hides more than about 25 units of work):

- Measured with an `ast` walk of `agent_workflows/check_engine.py` over every top-level function, counting non-comment lines that call a metadata reader (`_read_declared_id(`, `_read_item_id(`, `_read_plan_status(`, `_read_blocks_release(`, `_parse_setid(`, `_identity_metadata_region(`, `_metadata_status(`, `_status_meta(`, `backlog.parse_item(`, `_parse_metadata_comment(`, `history_block(`, `last_history_at(`) or use a metadata regular expression (`_ITEM_*_RE`, `_META_*_RE`, `_PLAN_STATUS_RE`, `_ITEM_DEPENDENCIES_RE`, `_DATE_LINE_RE`, `_REVIEW_SUBJECT_TYPE_RE`, `_FROM_SPEC_LINE_RE`, `_CARRIER_DATE_RE`, `_ID_LINE_RE`, `_SET_LINE_RE`, `_IDENT_*_RE`, `_STATUS_META_RE`, or an inline `^-` literal). The whole working-tree population is 93 site lines in 50 functions, which `ffceq0` E-07 moved as one item; it is partitioned across Orders 29 to 32 by function, and the four subsets together equal it (no function unassigned).
- Sites inside the git-content readers (`_status_meta`, `_check_untooled_plan_transition`, `check_staged_illegal_backlog_transition`, `_lane_carrier_is_executed`, and every site within four lines after a `_blob_text` call) are Order 09 `t4gl15`'s and are not counted. The reader definitions themselves (`_read_declared_id`, `_read_item_id`, `_read_plan_status`, `_read_blocks_release`, `_parse_setid`, `_identity_metadata_region`, `_metadata_status`) keep their text signatures for the git-content callers in this phase and are not moved by any part.
- E-01 and E-02 (pin and move, about 10 and 19 units) moved to `dbq57g` in round 3.
- E-03 (skip list, `ffceq0` E-08): `rg -n '_SKIP_NAMES|_NON_IPD_BASENAMES|skip_names|"README.md", "INDEX.md"' agent_workflows` gives 3 `_SKIP_NAMES` definitions (`check_engine`, `selectors`, `artifact_refs`), 1 `skip_names` set (`specs._spec_files`), 3 inline tuples in `releases` (`count_blocks_release_sentinel`, `check_blocks_release`, `check_from_backlog`), `ipd_lint._NON_IPD_BASENAMES` plus 1 inline tuple (`_default_pending_files`); 9 walker uses (`check_engine` 3, `selectors` 3, `artifact_refs` 1, `specs` 1, `ipd_lint` 2), 2 new constants, `artifact_core.iter_scan_files`, 1 fixture test and 1 rewrite test. About 22 units, of which round 3 moved the `layout`, `check_engine`, `selectors`, `artifact_refs` and `artifact_core` share to `i16on1`; the `specs`, `releases` and `ipd_lint` share (3 modules, 3 walker uses) stays here. Two more consumers import `check_engine._SKIP_NAMES` / `selectors._SKIP_NAMES` (`runner_shared`, `status_set`); they keep working because the old names stay as aliases of the `layout` constant until Order 11 (`9o83cr`) deletes them, and they are not edited here.

READER LEDGER rows this part moves (copied from `ffceq0`; the full ledger stays in `ffceq0`):

| Reader | Prior behavior | Pinning test | After |
|---|---|---|---|
| `check_engine` identity, status, Set, Item-Dependencies and From-* readers | region-bounded `^- ` bullets with mixed whitespace rules | E-06 module and its nine baseline modules | cached fields; identical rule ids on this checkout |
| `check_engine.build_graduation_reverse_index`, `graduation_cluster` | declarations and reverse links read separately | `tests/test_graduation_forward_links.py`, `tests/test_from_backlog_cardinality.py` | `lineage` and `graduation_targets` rows, still distinct (4.4a `pw2ln3`) |

DECISIONS that govern this part's reader moves (copied verbatim from `ffceq0`, which keeps the full D-1..D-6 table; a test that changes after a move must be one of these, never a silent change):

- D-1 (status of the 24 multi-word plans; F-03, F-04). KEPT: the canonical normalized status that `aw attention`, `aw ipd board` and `ipd_lint` already report (`executed` for `EXECUTED ...` and `DONE ...`, `legacy/unknown` for any other unrecognized token). For PLAN records only, both `aw find` paths match `plans.normalize_status` of the FIRST token of the cached raw value (the `plans.read_status` rule). Every other type keeps today's exact single-token match on the raw value, because `plans.normalize_status` knows only the plan vocabulary and maps `open`, `implemented`, `active` and `planned` to `legacy/unknown` (measured at review: `aw find backlog open` lists 27 rows and `aw find specs implemented` 22 today, and both must stay unchanged). The rule lives in `selectors`' `MATCH_STATUS` branch, so every `selectors.resolve` caller that allows `MATCH_STATUS` sees it; E-01 pins one non-find caller (`tests/test_selector_resolver_matrix.py`) so the change to those callers is observed, not assumed. WHAT EACH CONSUMER LOSES OR GAINS: `aw find plans executed` (selector path) GAINS the 24 plans plus `vfa1tl` and agrees with `--status executed` (1,635 rows at authoring); `aw find plans EXECUTED` stops matching `vfa1tl` by exact case (its only match today); the `aw find` JSON `status` of those 24 changes from the prose line to `executed` (the prose stays in the raw legacy column and in the file); the test edits are the expected value in `tests/test_find_single_read.py::test_d_status_disagreement_record_matches_and_preserves_plans_index_status` (only if its `plans_index` assertion reads through the moved path; Order 09 owns `plans_index`) and the `_read_status(multi)` assertion in `tests/test_front_matter_loose_whitespace.py::test_single_token_status_contract_survives`, whose `read_front_matter_status(multi)` and `parse_plan_file` assertions stay unchanged (D-2; the runner is Order 09's). Reason: one reader, one answer (4.3), and it is the answer three surfaces already give. The migration (Order 04) normalizes these terminal records at the cutover.
- D-4 (status bullet outside the metadata region; F-06). KEPT: region-bounded reading. The 4 records are 3 reviews and 1 walkthrough, which have no lifecycle status, so no plan-status consumer changes.
- D-5 (where the skip list applies; E-08). KEPT: record walkers skip `README.md`, `INDEX.md` and `STATUS.md` exactly as today; citation scans through `artifact_core.iter_scan_files` keep reading `README.md` (0u0ako). ADDED: every walker skips `records/meta/`. No record row changes today, because no `meta/` directory exists before the cutover.
- D-6 (records with no in-file `- Set:` bullet; added 2026-11-07, maintainer decision recorded on backlog `suth7l`). KEPT: the cache's filename-derived Set. `status_set`'s reader returns no Set for these records (242 on this repository on 2026-11-07: 164 research, 30 prompts, 23 specs, 14 plans, 8 walkthroughs, 3 roadmaps), while the cache takes it from the filename, which spec `4sd62s` C1/C10 make the checked mirror of `set` and 5.2 step 3 already uses as the default. What a consumer loses: nothing; what changes: `aw set <setid>` and `aw find <setid>` also match those records once E-15 lands. Pinned by `tests/test_artifact_meta_loader_parity.py::test_cache_agrees_with_status_set_reader_on_every_fixture_record`.

## Proposed changes (ordered, validatable)

1. Point the remaining skip-name copies at the `layout` constants (E-03).

## Deferred / out of scope (with reason)

- E-01, E-02 (the graduation and handoff readers of `check_engine`). Moved to dbq57g (round-3 split 2026-11-09 per research nj8zdp guidance).
  - Carrier: dbq57g
- E-03, the `layout` constants and the `check_engine`, `selectors`, `artifact_refs` and `artifact_core` subset with its `meta_dir` fixture test. Moved to i16on1 (round-3 split 2026-11-09 per research nj8zdp guidance).
  - Carrier: i16on1
- The git-content readers of `check_engine` (`_blob_text`/`_status_meta` callers).
  - Carrier: t4gl15
- The other check_engine site subsets of `ffceq0` E-06/E-07 (split 2026-11-07 per maintainer step-complexity rule): see Orders 29 (w1cs3p), 30 (na188y), 31 (i3b5zu) and 32 (ebrc4t).
  - Carrier: ffceq0
- Retiring the `_SKIP_NAMES` aliases that `runner_shared` and `status_set` still import.
  - Carrier: 9o83cr

## Scope check

- Over-scope: none. `specs.py`, `releases.py` and `ipd_lint.py` change only to consult the `layout` constants (E-03).
- Under-scope: none known. After round 3 this part carries only the `specs`, `releases` and `ipd_lint` subset of E-08 of `ffceq0`; `dbq57g` and `i16on1` carry the rest, and together they equal the original lists.

## Required tests / validation

No new test. E-03 re-runs the `meta_dir` fixture test that `i16on1` added to `tests/test_readers_check_engine.py`, plus `tests/test_artifact_refs_rewrite.py`, `tests/test_specs_recursive_read.py`, `tests/test_releases.py` and `tests/test_ipd_lint.py` unchanged.

Commands: the named modules, the bare core gate `python3 -m pytest`, `aw check`, `aw sanitize --agent`. The thorough tier `make test-all` runs once, in `ffceq0`'s final item.

## Spec / documentation sync

N/A: no spec text changes; implements `4sd62s` 4.4 last bullet (one exclusion list) for `specs`, `releases` and `ipd_lint`.

## Open questions

### OQ-01: Does this part fit the step-complexity limits?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Round 3 (2026-11-09): 1 E-item, 3 work Scope-Paths. It still depends on Orders 29 to 31 (and now on `dbq57g` and `i16on1`) because the skip-list item must follow every check_engine move, as `ffceq0` E-08 followed E-07. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n "_SKIP_NAMES\s*=|_NON_IPD_BASENAMES\s*=|skip_names\s*=|RECORD_SCAN_SKIP_NAMES\s*=|RECORD_SCAN_EXCLUDED_DIRS\s*=" agent_workflows` listing only `agent_workflows/layout.py` and the three `_SKIP_NAMES` alias lines of `i16on1`, with no line in `specs.py`, `releases.py` or `ipd_lint.py`; `python3 -m pytest -o addopts="" -v tests/test_readers_check_engine.py -k meta_dir` PASSED; and the summary lines of `python3 -m pytest -o addopts="" tests/test_artifact_refs_rewrite.py`, `tests/test_specs_recursive_read.py`, `tests/test_releases.py` and `tests/test_ipd_lint.py`, each named with 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every `- Item-Dependencies:` edge is executed. Every reader move is pin-first: the baseline runs green on the unmodified code before the matching move, and a test edited after a move must be one that the copied decisions name.

Honesty rule: run the named modules and `python3 -m pytest` (core gate) and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit ebrc4t -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
