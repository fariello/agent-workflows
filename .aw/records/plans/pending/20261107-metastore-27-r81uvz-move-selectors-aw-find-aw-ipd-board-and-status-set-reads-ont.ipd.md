# IPD: Move selectors, aw find, aw ipd board and status_set reads onto artifact_meta

- Date: 2026-11-07
- Kind: child
- Concern: Split from `ffceq0` (Task group 1) under the maintainer's step-complexity rule. Spec `4sd62s` C5 and C5a require that every metadata read goes through `artifact_meta`; `selectors` holds 7 `^-` metadata regular expressions and the selector status reader disagrees with the `plans_index` filter on 24 plans, so `aw find plans executed` and `aw find plans --status executed` list different sets (F-03, F-04).
- Scope: Pin then move the `selectors` reads and the `aw find`, `aw search` and `aw ipd board` paths in `cli` onto `artifact_meta`, add `artifact_meta.read_text` (OQ-03 of `ffceq0`) with its spec 4.3 entry, and apply decisions D-1 and D-2 (`ffceq0` E-01, E-02, E-03 carried unchanged). EXCLUDES: `attention` (Order 28 `dqutt8`), `check_engine` (Orders 29 to 32), `ipd_lint`, `status_set`, the meta commands and the cache-parity test (all kept in `ffceq0`).
- Scope-Paths: agent_workflows/selectors.py, agent_workflows/artifact_meta.py, agent_workflows/cli.py, agent_workflows/plans.py, tests/test_readers_selectors_find.py, tests/test_artifact_meta_legacy.py, tests/test_find_single_read.py, tests/test_front_matter_loose_whitespace.py, agent_workflows/status_set.py, tests/test_artifact_meta_loader_parity.py, .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md
- Item-Dependencies: executed:g5hpbb, executed:tve77h, executed:xexn45
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 27
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: r81uvz

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from ffceq0 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).
- 2026-11-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The `status_set` inventory and transition readers answer from the same cache, and the `selectors` readers and the `aw find`/`aw search`/`aw ipd board` paths answer from the `artifact_meta` cache, `artifact_meta.read_text` exists for in-memory text, and both `aw find` status paths give one answer, the one decision D-1 records.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Every E-item that moves a reader follows one rule, so a reviewer can check each the same way: (1) BEFORE the edit, add or extend a behavioral test in the named module that pins the reader's CURRENT observable behavior on a `tmp_path` fixture repository (the "prior behavior" column of the reader ledger in `## Findings`), and run it green against the unmodified code; (2) change the reader to call `artifact_meta`; (3) run the same test unchanged. A test that has to change in step 3 is a behavior change and must be one of the decisions listed in the ledger (D-1 to D-5), never a silent one. For every existing module named as a baseline, save the per-test outcome list under the gitignored `.aw/state/ffceq0/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/ffceq0/<E>-before.txt`) before the move and the same command into `<E>-after.txt` after it; `diff` of the two prints nothing except lines a named decision explains. Every saved baseline (command output, JSON, rule counts) also goes under `.aw/state/ffceq0/`, never `/tmp`, so it survives a lane integration. A count measured at authoring (for example the 1,635 executed plans of F-03) is context, never the bar: each expected outcome compares a before and after value re-derived on the same tree. New test modules set `pytestmark = pytest.mark.core`, call real functions or the real `aw` CLI, and never read production source.

The baseline directory stays `.aw/state/ffceq0/`, not this plan's own id6, because the split parent `ffceq0` keeps the final cache-parity, residual-audit and finishing items that compare against these saved files. Commit through `aw commit r81uvz -- <each changed path>`, one commit per task group allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push.

### Task group 1: selectors, aw find, the status-disagreement decision and the status_set reads

- [ ] E-01 Pin the current `aw find` and `selectors` behavior in `tests/test_readers_selectors_find.py` before any change: id6, Set, status, stem and substring selector matching per type; `aw find plans <id6>` and `--status`/`--status-not`/`--set`/`--id` filters; `aw find research` and `aw find prompts` rows (prompt id and Set from the `aw-prompt` comment, then the filename slot); `selectors.read_front_matter_id`, `read_front_matter_status`, `read_front_matter_blocks_release` and `declared_id6` on loose-whitespace (`-  `, `-\t`) and quoted-example fixtures; `aw find` exit code 2 for a selector that matches nothing (4.4a row `zyj8io`); and the fixture form of the 24-plan disagreement (one plan with `- Status: EXECUTED (approved ...)` in `executed/`). Also run the existing `tests/test_find_filters.py` (4.4a row `wja06w`), `tests/test_find_single_read.py`, `tests/test_selector_two_dialect_readers.py`, `tests/test_front_matter_loose_whitespace.py` and `tests/test_selector_resolver_matrix.py` green. Before any code edit, save these checkout baselines under `.aw/state/ffceq0/`: the sorted path lists of `aw find plans executed --paths` (`find-executed-sel-before.txt`) and `aw find plans --status executed --paths` (`find-executed-flt-before.txt`); `aw find <type> --agent` for every type (`find-<type>-before.jsonl`); `aw ipd board --json` (`board-before.json`, whose `plans-board` evidence carries `count`); and `aw attention --all --format json` (`att-before.json`, used by E-05).
  - Depends on: none
  - Expected outcome: the new module passes on the unmodified code; the outcome list of the five existing modules and every checkout baseline above is saved.
  - Execution state: pending

- [ ] E-02 Move `selectors` reads onto `artifact_meta`: `_read_id`, `_read_status`, `_read_setid`, `_read_yaml_scalar`, `read_front_matter_id`, `read_front_matter_status`, `read_front_matter_blocks_release`, `declared_id6`, `declares_id6`, `id6_ownership` and the `resolve` selector kinds `MATCH_ID6`/`MATCH_SETID`/`MATCH_STATUS` answer from `artifact_meta.resolve`/`artifact_meta.read`/`artifact_meta.query`; filename-only kinds (`MATCH_STEM`, `MATCH_SUBSTRING`, `MATCH_PATH`) keep reading no file content. The public `read_front_matter_*(text)` functions keep their text signature for Order 09's callers in this phase and answer through the one additive interface function this plan adds, `artifact_meta.read_text(text, *, record_type=None) -> State` (OQ-03), so no `^-` metadata regex remains in `selectors`. `read_text` returns a `State` that carries BOTH the strict-grammar fields (what `read`/`query` see) and, for `id`, `status` and `blocks_release`, the value the loose `^-[ \t]*` bullet spelling would give (D-2); the public `read_front_matter_*` readers answer from the loose value and the internal `_read_*` readers and the cache answer from the strict value. Add `read_text` to the function list of spec `4sd62s` 4.3 (OQ-03; a `note` through `aw specs note`, then the text edit). Add `read_text` and its tests in `tests/test_artifact_meta_legacy.py`: a strict, a two-space, a tab, a YAML-only research and a multi-word-status fixture each give the expected strict and loose values. Apply decision D-1 (status) and D-2 (whitespace). Other modules that import `selectors` private readers (`partition._read_setid`, `runner_shared` `_read_id`) keep working because the private names keep their signatures and answers in this phase; Order 09 or Order 11 retires them.
  - Depends on: E-01
  - Expected outcome: `rg -n "re\.(compile|search|match)\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/selectors.py` prints nothing; `tests/test_artifact_meta_legacy.py -k read_text` passes; the E-01 module and the five existing modules pass with an outcome-list diff that is empty except the assertions that D-1 names.
  - Execution state: pending

- [ ] E-03 Move the `aw find` and `aw search` paths in `cli` onto `artifact_meta.query`: `_find_type_records` (plans, research, prompts, specs, backlog, releases branches), `_find_prompt_id6`, `_find_prompt_setid`, `_run_search._artifact_status`, and `_run_plans` (`aw ipd board` through `plans.scan`/`plans.read_status`). `plans.read_status` and `plans.scan` keep their signatures and return the same canonical readiness value (`plans.normalize_status`), now computed from the cached raw status. `aw find` shows `artifacts.short_description` when present and the current `detail` otherwise (AC-36 case 2 owner side).
  - Depends on: E-02
  - Expected outcome: E-01 passes; `aw find plans executed --paths` and `aw find plans --status executed --paths` list the same sorted paths, and that list equals the E-01 `find-executed-flt-before.txt` list (D-1: the selector path gains exactly the multi-word and upper-case records and the filter path loses none); `aw find plans zzzzzz` exits 2; the `count` of `aw ipd board --json` equals the E-01 `board-before.json` count; for every type, `aw find <type> --agent` item records equal the E-01 baseline except the `status` values D-1 names.
  - Execution state: pending

- [ ] E-04 Change `status_set.read_artifact_record` and `inventory_all_artifacts` to take `id6`, `status`, `set_id` and `record_type` from `artifact_meta.resolve`/`artifact_meta.read`/`artifact_meta.query` (type detection by path stays, since it reads no file content); `ArtifactRecord.raw_text` stays as the body text for body-prose consumers (open-question gates, N3); delete `_ID_RE`, `_STATUS_RE`, `_SET_RE` and the two inline YAML regexes. First dump today's inventory as sorted JSON (`path`, `record_type`, `id6`, `set_id`, `status`) to `.aw/state/ffceq0/inventory-before.json`, then dump it again after the change to `inventory-after.json`.
  - Depends on: E-03
  - Expected outcome: the before and after inventory dumps are identical EXCEPT the D-6 records (no in-file `- Set:` bullet), which gain their filename Set and nothing else; `tests/test_status_set_metadata_region.py` and `tests/test_selector_resolver_matrix.py` pass unchanged.
  - Execution state: pending

- [ ] E-05 Change the remaining `status_set` metadata reads to cached fields: `_format_status_transition_line` (priority, blocks_release, gate kind and ref), `plan_priority_work_kind_problems` (priority and work kind; same `ipd_schema.parse_plan_priority`/`parse_plan_work_kind` judgement), `read_item_dependencies_value` (raw `item_dependencies` declaration), and the backlog gate-default inputs in `_prepare_status_change` (`work_kind`, `blocks_release`, the release exemption pair; today `backlog.parse_item` and `selectors.read_front_matter_blocks_release` on in-memory text). `_format_status_transition_line(rec, dest_path, norm_stat, term, ...)` KEEPS its `ArtifactRecord` signature (it reads the cached fields for `rec` internally), because `tests/test_blocks_release_reader_bounding.py` calls it directly and must pass unchanged; only the text-taking `plan_priority_work_kind_problems` and `read_item_dependencies_value`, whose only callers are inside `status_set.py`, change to take a `State`.
  - Depends on: E-04
  - Expected outcome: `rg -n "re\.(compile|match|search|finditer|split)" agent_workflows/status_set.py` lists only non-metadata patterns (none of `Id`, `Status`, `Set`, `Priority`, `Gate-`, `Kind`, `Work-Kind`, `Approval`, `Readiness`, `Workflow history`); the R-row baseline tests of `2xwb9b` pass.
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
| F-03 | `aw find plans executed` lists 1,610 paths; `aw find plans --status executed` lists 1,635. The 25 extra: 24 multi-word `- Status:` plans in `executed/` (`EXECUTED 2026-07-0x ...` 13, `DONE (...)` 7, `EXECUTED (approved ...)` 4) plus `vfa1tl`, whose single token is upper-case `EXECUTED` | The selector path (`selectors._read_status`, exact token) and the filter path (`plans_index.query`, status OR disposition) answer the same question differently. |
| F-04 | Python check over all tracked plans: `selectors._read_status` and `plans_index.plan_entry(...).status` disagree on exactly 24 plans; for all 24, `plans.normalize_status(<whole line>)` is `legacy/unknown`, `plans.read_status` (first token) is `executed`, and `aw attention` reports `native_status: executed` | Three answers exist: none (selectors), the prose line (plans_index), `executed` (plans, attention). D-1 picks one. |
| F-05 | `selectors._read_status` (strict `^- `, YAML fallback) and `selectors.read_front_matter_status` (loose `^-\s*`, no YAML) disagree on 157 records, ALL research files with YAML status. No tracked record uses `-  ` or `-\t` before a metadata field (0 matches) | The whitespace difference has no corpus effect; the YAML difference is real, and D-2 keeps each caller's answer. |
| F-11 | `aw find plans zzzzzz` exits 2 today (4.4a `zyj8io`) | Pinned by E-01, re-checked after E-03. |

Step-complexity measurement for this part (2026-11-07, at the worktree HEAD of the split; the rule is that no E-item hides more than about 25 units of work):

- E-01 (pin): 1 new test module, 5 existing modules run as the baseline (`test_find_filters` 18 tests, `test_find_single_read` 6, `test_selector_two_dialect_readers` 11, `test_front_matter_loose_whitespace` 4, `test_selector_resolver_matrix` 21; counted with `rg -c '^\s*def test_' tests/<module>.py`), 13 checkout baselines (two path lists, nine `find-<type>` dumps, board, attention). About 19 units.
- E-02 (move `selectors`): `rg -c 're\.(compile|search|match)\(\s*r?"(\(\?m\))?\^-' agent_workflows/selectors.py` = 7 (six metadata literals plus the `_YAML_FENCE_CLOSE_RE` fence literal, which is not a metadata bullet); 11 named readers and 3 selector kinds; 1 new interface function with 5 fixture tests; 1 spec edit. About 25 units.
- E-03 (move `cli` find/search/board): 5 functions in `cli` (`_find_type_records` over 6 type branches, `_find_prompt_id6`, `_find_prompt_setid`, `_run_search._artifact_status` with its 1 `^-` literal, `_run_plans`), `plans.read_status`/`plans.scan` with 3 `^-` literals (`rg -c` on `agent_workflows/plans.py`). About 15 units.
- E-04 (`status_set` inventory, `ffceq0` E-15): `rg -n 're\.(compile|search|match|finditer|split)\(' agent_workflows/status_set.py` lists `_ID_RE`, `_STATUS_RE`, `_SET_RE` and the two inline YAML regexes inside `read_artifact_record` (5 deletions), 2 functions changed (`read_artifact_record`, `inventory_all_artifacts`), 2 inventory dumps, 2 test modules run unchanged (`test_status_set_metadata_region` 3 tests, `test_selector_resolver_matrix` 21). About 11 units.
- E-05 (remaining `status_set` reads, `ffceq0` E-16): 4 readers (`_format_status_transition_line` with 3 inline `^-` searches, `plan_priority_work_kind_problems` with 2 regex uses, `read_item_dependencies_value`, the gate-default inputs in `_prepare_status_change`), callers counted with `rg -c '<name>\(' agent_workflows tests` (the two text-taking functions have only their 2 in-module call sites each; `_format_status_transition_line` has 2 test call sites in `tests/test_blocks_release_reader_bounding.py`, which must pass unchanged), 3 test modules run. About 14 units.

READER LEDGER rows this part moves (copied from `ffceq0`; the full ledger stays in `ffceq0`):

| Reader | Prior behavior | Pinning test | After |
|---|---|---|---|
| `selectors._read_status`, `resolve` `MATCH_STATUS` | exact single token of the region `- Status:`; YAML `status:` for research; none for multi-word | E-01 module; `tests/test_selector_two_dialect_readers.py`; `tests/test_front_matter_loose_whitespace.py::test_single_token_status_contract_survives` | D-1: canonical status from the cache; multi-word executed plans match `executed` |
| `selectors.read_front_matter_id`/`_status`/`_blocks_release` | loose `^-\s*` bullet only, region-bounded, no YAML | `tests/test_front_matter_loose_whitespace.py`, `tests/test_blocks_release_reader_bounding.py` | D-2: same answers |
| `selectors.declared_id6`, `id6_ownership` | whole-file id read for the ownership verdict | `tests/test_plans_rename_selectors.py`, E-01 | cached `id` |
| `plans_index.plan_entry` status in `aw find plans` JSON | whole prose line | `tests/test_find_single_read.py::test_d_status_disagreement_record_matches_and_preserves_plans_index_status` | D-1: canonical value (the printed row already shows the disposition first, `e.disposition or e.status`, so it does not change) |
| `plans.read_status`, `plans.scan` (`aw ipd board`, attention, M105) | first token of whole-file line, normalized | `tests/test_plan_status.py`, `tests/test_plans_board.py` | same normalized value from the cached raw status |
| `cli._find_prompt_id6`/`_find_prompt_setid` | `aw-prompt` comment first, then guarded filename slot | `tests/test_find_prompts_lane_status.py`, E-01 | cached `id`/`set` (the legacy loader applies the same order) |
| `cli._run_search._artifact_status` | loose `^-\s*Status:` over the whole file | `tests/test_cli_search.py` | cached status |

DECISIONS that govern this part's reader moves (copied verbatim from `ffceq0`, which keeps the full D-1..D-6 table; a test that changes after a move must be one of these, never a silent change):

- D-1 (status of the 24 multi-word plans; F-03, F-04). KEPT: the canonical normalized status that `aw attention`, `aw ipd board` and `ipd_lint` already report (`executed` for `EXECUTED ...` and `DONE ...`, `legacy/unknown` for any other unrecognized token). For PLAN records only, both `aw find` paths match `plans.normalize_status` of the FIRST token of the cached raw value (the `plans.read_status` rule). Every other type keeps today's exact single-token match on the raw value, because `plans.normalize_status` knows only the plan vocabulary and maps `open`, `implemented`, `active` and `planned` to `legacy/unknown` (measured at review: `aw find backlog open` lists 27 rows and `aw find specs implemented` 22 today, and both must stay unchanged). The rule lives in `selectors`' `MATCH_STATUS` branch, so every `selectors.resolve` caller that allows `MATCH_STATUS` sees it; E-01 pins one non-find caller (`tests/test_selector_resolver_matrix.py`) so the change to those callers is observed, not assumed. WHAT EACH CONSUMER LOSES OR GAINS: `aw find plans executed` (selector path) GAINS the 24 plans plus `vfa1tl` and agrees with `--status executed` (1,635 rows at authoring); `aw find plans EXECUTED` stops matching `vfa1tl` by exact case (its only match today); the `aw find` JSON `status` of those 24 changes from the prose line to `executed` (the prose stays in the raw legacy column and in the file); the test edits are the expected value in `tests/test_find_single_read.py::test_d_status_disagreement_record_matches_and_preserves_plans_index_status` (only if its `plans_index` assertion reads through the moved path; Order 09 owns `plans_index`) and the `_read_status(multi)` assertion in `tests/test_front_matter_loose_whitespace.py::test_single_token_status_contract_survives`, whose `read_front_matter_status(multi)` and `parse_plan_file` assertions stay unchanged (D-2; the runner is Order 09's). Reason: one reader, one answer (4.3), and it is the answer three surfaces already give. The migration (Order 04) normalizes these terminal records at the cutover.
- D-2 (whitespace and YAML; F-05). KEPT: each caller's current answer. The cache holds research YAML status, so `_read_status`/`MATCH_STATUS` keep matching research by it, while the public `read_front_matter_status` keeps returning None for a YAML-only record (Order 09's runner callers read plans, which use bullets). Whitespace keeps each caller's current answer too: the legacy loader parses "one strict `- Field: value` grammar" (`tve77h` E-11), which matches the strict internal readers (`_read_id`/`_read_status` reject `-  ` and `-\t`, pinned by `tests/test_front_matter_loose_whitespace.py::test_internal_readers_stay_strict`), while the public `read_front_matter_*` readers keep accepting `-  ` and `-\t` (pinned by `test_public_readers_tolerate_loose_leading_whitespace`) through the loose values that `read_text` also returns (E-02). Today 0 tracked records use the loose spelling (F-05), so the cache and the public readers agree on the whole corpus; Order 11 retires the loose values with the public readers.
- D-6 (records with no in-file `- Set:` bullet; added 2026-11-07, maintainer decision recorded on backlog `suth7l`). KEPT: the cache's filename-derived Set. `status_set`'s reader returns no Set for these records (242 on this repository on 2026-11-07: 164 research, 30 prompts, 23 specs, 14 plans, 8 walkthroughs, 3 roadmaps), while the cache takes it from the filename, which spec `4sd62s` C1/C10 make the checked mirror of `set` and 5.2 step 3 already uses as the default. What a consumer loses: nothing; what changes: `aw set <setid>` and `aw find <setid>` also match those records once E-15 lands. Pinned by `tests/test_artifact_meta_loader_parity.py::test_cache_agrees_with_status_set_reader_on_every_fixture_record`.

## Proposed changes (ordered, validatable)

1. Pin then move `selectors` and the `aw find`/`aw search`/`aw ipd board` paths, applying D-1 and D-2 (E-01 to E-03).
2. Move the `status_set` inventory and transition reads, applying D-6 (E-04, E-05; `ffceq0` E-15, E-16, re-scoped there from `2xwb9b` by the maintainer on 2026-11-07, run `run-20261107T082247Z-2899457`, question `02-2xwb9b-a2-sequence-loader-fix`, answer C).

## Deferred / out of scope (with reason)

- `attention` reads (`ffceq0` E-04, E-05). Moved to dqutt8 (split 2026-11-07 per maintainer step-complexity rule).
  - Carrier: dqutt8
- `check_engine` working-tree readers (`ffceq0` E-06, E-07) and the skip list (E-08). Moved to w1cs3p, na188y, i3b5zu and ebrc4t (split 2026-11-07 per maintainer step-complexity rule).
  - Carrier: w1cs3p
- `ipd_lint` reads (`ffceq0` E-09). Moved to dqutt8 (split 2026-11-07 per maintainer step-complexity rule).
  - Carrier: dqutt8
- `aw check meta`, `aw meta repair`, cache parity, offline proof and the residual audit: kept in the split parent.
  - Carrier: ffceq0
- Deleting `selectors._STATUS_RE` and every other leftover parser.
  - Carrier: 9o83cr

## Scope check

- Over-scope: none. `artifact_meta.py` changes only to add `artifact_meta.read_text` (OQ-03 of `ffceq0`); `tests/test_artifact_meta_legacy.py` gains only the `read_text` tests; the spec changes only by the OQ-03 function-list entry; `tests/test_find_single_read.py` and `tests/test_front_matter_loose_whitespace.py` change only in the assertions D-1 names.
- Under-scope: none known. This part carries E-01, E-02, E-03, E-15 and E-16 of `ffceq0` unchanged except where its site list is partitioned, as named in each item.

## Required tests / validation

New core module `tests/test_readers_selectors_find.py` (`tmp_path` fixtures, real functions or the `aw` CLI, no production-source reads). The existing modules named in E-01, E-04 and E-05 run before and after each move, plus `tests/test_find_prompts_lane_status.py` and `tests/test_cli_search.py` for E-03. Acceptance-criteria rows carried from `ffceq0`: AC-21 rows `wja06w` and `zyj8io` (pasted runs; AC-21 is owned by `xexn45`).

Commands: the named modules, the bare core gate `python3 -m pytest`, `aw check`, `aw sanitize --agent`. The thorough tier `make test-all` runs once, in `ffceq0`'s final item.

## Spec / documentation sync

ONE spec amendment, carried from `ffceq0` OQ-03: `4sd62s` 4.3 gains `read_text(text, *, record_type=None) -> State` in its function list, with one sentence stating that it runs the same loader as `read_at`, caches nothing, and exists for in-memory text in phase B. Reason: the function list is the C5 contract, and without the entry the public `selectors.read_front_matter_*(text)` readers would need either a second grammar or a function the spec does not name. The `CHANGELOG.md` line for the D-1 matching change is written by `ffceq0`'s final item.

## Open questions

### OQ-01: Does this part fit the step-complexity limits?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes. 5 E-items, 11 Scope-Paths entries, measured at about 19, 25, 15, 11 and 14 units (see `## Findings`). E-02 sits at the limit because it also adds `read_text`; splitting `read_text` out would leave E-02 unable to remove the public readers' regular expressions, so it stays one item. E-04 and E-05 sit here, not in a separate plan, because `status_set` reads through the same `selectors` readers E-02 moves and E-04 depends on E-03 in the original. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git stash list` showing no stash and `git diff --stat agent_workflows/` empty (proving the code is unmodified), then `python3 -m pytest -o addopts="" -v tests/test_readers_selectors_find.py` with every test PASSED, including named tests for the multi-word `EXECUTED (approved ...)` fixture, loose-whitespace fixtures and the zero-match exit code 2; then `wc -l` of `.aw/state/ffceq0/E-01-before.txt` (the five existing modules' outcome list) and `ls -l .aw/state/ffceq0/` showing the E-01 checkout baselines (`find-executed-sel-before.txt`, `find-executed-flt-before.txt`, `find-<type>-before.jsonl`, `board-before.json`, `att-before.json`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the empty output of `rg -n "re\.(compile|search|match)\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/selectors.py`; the E-01 module re-run all PASSED; `diff .aw/state/ffceq0/E-01-before.txt .aw/state/ffceq0/E-02-after.txt` printing nothing or only the lines D-1 names; `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_legacy.py -k read_text` with the strict, two-space, tab, YAML-only and multi-word cases PASSED; and `git diff tests/` showing that the only changed existing assertions are the ones D-1 names.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw find plans executed --paths | sort | diff - <(aw find plans --status executed --paths | sort)` printing nothing, `diff` of that list against `.aw/state/ffceq0/find-executed-flt-before.txt` printing nothing, the line counts of the selector list before (`find-executed-sel-before.txt`) and after, `aw find backlog open --paths | wc -l` and `aw find specs implemented --paths | wc -l` equal to their E-01 values, `aw find plans zzzzzz; echo $?` printing 2, the `aw ipd board --json` `count` before and after (equal), the per-type `diff` of `aw find <type> --agent` item records against the E-01 baselines (differences only in D-1 `status` values), and `python3 -m pytest -o addopts="" -v tests/test_readers_selectors_find.py tests/test_find_prompts_lane_status.py tests/test_cli_search.py` all PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `diff .aw/state/ffceq0/inventory-before.json .aw/state/ffceq0/inventory-after.json` showing ONLY D-6 records (each line a `set_id` going from `null` to its filename Set, every other field equal), with the count of differing records, and the summary line of `python3 -m pytest -o addopts="" tests/test_status_set_metadata_region.py tests/test_selector_resolver_matrix.py tests/test_check_engine_metadata_region.py` with 0 failed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the output of `rg -n "re\.(compile|match|search|finditer|split)" agent_workflows/status_set.py` (no line names a metadata field) and the summary line of `python3 -m pytest -o addopts="" tests/test_blocks_release_reader_bounding.py tests/test_status_set.py -k "priority or bidirectional or deps" tests/test_status_set_descriptive_safety.py` with 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every `- Item-Dependencies:` edge is executed. Every reader move is pin-first: the baseline runs green on the unmodified code before the matching move, and a test edited after a move must be one that the copied decisions name.

Honesty rule: run the named modules and `python3 -m pytest` (core gate) and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit r81uvz -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
