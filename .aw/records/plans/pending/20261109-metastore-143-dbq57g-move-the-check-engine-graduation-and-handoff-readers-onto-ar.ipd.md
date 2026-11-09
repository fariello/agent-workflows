# IPD: Move the check_engine graduation and handoff readers onto artifact_meta

- Date: 2026-11-09
- Kind: child
- Concern: Split from `ebrc4t` (Order 32) in round 3 of the metastore re-split, per research `nj8zdp` guidance (at most 8 work Scope-Paths per plan): `ebrc4t` declared 11 work Scope-Paths, because it combined the graduation and handoff subset of the `ffceq0` E-07 site list (19 site lines in 6 functions of `check_engine`) with the skip-list change across seven modules. This part takes the `check_engine` subset.
- Scope: Pin then move the graduation and handoff readers of `check_engine` (`build_graduation_reverse_index`, `graduation_cluster` through it, `evaluate_handoff_ready`, `check_graduation_incomplete`, `graduated_closable_warnings` and their history-date readers) onto `artifact_meta` (`ebrc4t` E-01 and E-02, carried unchanged). EXCLUDES: the record skip list (`i16on1`, Order 144, then `ebrc4t`), the other check_engine subsets (Orders 29 to 31), and git-content readers (`t4gl15` family).
- Scope-Paths: agent_workflows/check_engine.py, tests/test_readers_check_engine.py, tests/test_graduation_forward_links.py, tests/test_handoff_ready_gate.py, .aw/records/plans/pending/20261109-metastore-143-dbq57g-move-the-check-engine-graduation-and-handoff-readers-onto-ar.ipd.md
- Item-Dependencies: executed:g5hpbb, executed:tve77h, executed:xexn45, executed:w1cs3p, executed:na188y, executed:i3b5zu
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 143
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: dbq57g

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from ebrc4t (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The `check_engine` graduation and handoff rules read cached fields and report the same rule ids on this checkout as before.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Every E-item that moves a reader follows one rule, so a reviewer can check each the same way: (1) BEFORE the edit, add or extend a behavioral test in the named module that pins the reader's CURRENT observable behavior on a `tmp_path` fixture repository (the "prior behavior" column of the reader ledger in `## Findings`), and run it green against the unmodified code; (2) change the reader to call `artifact_meta`; (3) run the same test unchanged. A test that has to change in step 3 is a behavior change and must be one of the decisions copied below (D-1, D-4, D-6), never a silent one. For every existing module named as a baseline, save the per-test outcome list under the gitignored `.aw/state/ffceq0/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/ffceq0/<E>-before.txt`) before the move and the same command into `<E>-after.txt` after it; `diff` of the two prints nothing except lines a named decision explains. Every saved baseline also goes under `.aw/state/ffceq0/`, never `/tmp`. A count measured at authoring is context, never the bar. New test modules set `pytestmark = pytest.mark.core`, call real functions or the real `aw` CLI, and never read production source. The file names keep the `ebrc4t` suffix `-32` (`E-06-before-32.txt`, `check-before-32.txt`) so the split parent `ffceq0` finds them.

Commit through `aw commit dbq57g -- <each changed path>`, one commit per item allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push.

### Task group 1: check_engine graduation and handoff readers

- [ ] E-01 (carried from `ebrc4t` E-01) Pin the current behavior of THIS PART'S SUBSET of the `check_engine` working-tree readers (the original `ffceq0` E-06 list, partitioned across Orders 29 to 32) in `tests/test_readers_check_engine.py`: `build_graduation_reverse_index` and `graduation_cluster` (declarations alone, origin links alone, both; 4.4a row `pw2ln3`), `evaluate_handoff_ready`, `check_graduation_incomplete` (with `_item_graduated_date` and `_spec_implementing_date`) and `graduated_closable_warnings`, each on a `tmp_path` fixture through `aw check <type> --agent`. Run `tests/test_graduation_forward_links.py` and `tests/test_handoff_ready_gate.py` green as the baseline.
  - Depends on: none
  - Expected outcome: the new module passes on the unmodified code; the baseline outcome list is saved, and the sorted rule-id counts of `aw check all --agent` (one `rule` per diagnostic) are saved to `.aw/state/ffceq0/check-before.txt` if that file does not yet exist (the first check_engine part to run writes it; later parts keep it, because it is the parent's final comparison bar) and, always, to this part's own `.aw/state/ffceq0/check-before-32.txt`.
  - Execution state: pending

- [ ] E-02 (carried from `ebrc4t` E-02) Move the `check_engine` working-tree metadata readers onto `artifact_meta`: THIS PART'S SUBSET of the `ffceq0` E-07 site list (partitioned across Orders 29 to 32), namely every working-tree metadata read inside these functions, with its measured site-line count: `build_graduation_reverse_index` (5), `evaluate_handoff_ready` (6, working-tree reads only), `_item_graduated_date` (1), `_spec_implementing_date` (1), `check_graduation_incomplete` (4), `graduated_closable_warnings` (2); 19 site lines. In each function the reads to replace are the calls of `_read_declared_id`, `_read_item_id`, `_read_plan_status`, `_read_blocks_release`, `_parse_setid` and `_metadata_status`/`_status_meta` on working-tree text, the `_ITEM_*`/`_META_*`/`_PLAN_STATUS_RE`/`_ITEM_DEPENDENCIES_RE`/`_DATE_LINE_RE`/`_REVIEW_SUBJECT_TYPE_RE`/`_FROM_SPEC_LINE_RE`/`_CARRIER_DATE_RE` users, the inline `^- Kind:`/`^- Status:`/`^- Set:`/`^- Date:`/`^- Id:` searches, `backlog.parse_item` uses, the `prompts_index._parse_metadata_comment` use, and the `history_block`/`last_history_at` uses, all through `artifact_meta.read`/`query`/`history`. `_metadata_status(text)` keeps its text signature ONLY for the git-content callers that Order 09 moves to `read_at`; every working-tree call site passes through `artifact_meta.read` instead. Body-prose bullets kept by N3 (`_TARGET_BULLET_RE` over `Concern`/`Scope`/`Scope-Paths` body scanning for citations, open-question `Carrier*` rows) are NOT metadata reads and stay; each is listed in the `ffceq0` E-14 exclusion list.
  - Depends on: E-01
  - Expected outcome: E-01 and its baseline modules pass unchanged; `aw check all --agent` on this checkout reports the same rule-id multiset as `.aw/state/ffceq0/check-before-32.txt` (pasted sorted counts, empty diff), with any difference explained by a plan or record that changed between the two runs.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

Carried from `ebrc4t` (and through it `ffceq0`) Step 0:

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `artifact_meta.history(id6)`, `artifact_meta.query(...)` with typed filters and an `incomplete` list, `artifact_meta.resolve(path_or_id6)`.
- Shared history rules: `attention_contract.history_block`, `attention_contract.newest_history_record`, `attention_contract.last_history_at`.
- Core tier: modules set `pytestmark = pytest.mark.core`; the bare gate is `python3 -m pytest` (30 s budget).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never a bare line number (advisory `IPD-C801`).

## Findings

Carried from `ebrc4t` (measured 2026-11-07 at the round-1 split):

- Measured with an `ast` walk of `agent_workflows/check_engine.py` over every top-level function, counting non-comment lines that call a metadata reader or use a metadata regular expression (the list is in E-02). The whole working-tree population is 93 site lines in 50 functions, which `ffceq0` E-07 moved as one item; it is partitioned across Orders 29 to 32 by function, and the four subsets together equal it. This part's subset is the 19 site lines in 6 functions named in E-02.
- Sites inside the git-content readers (`_status_meta`, `_check_untooled_plan_transition`, `check_staged_illegal_backlog_transition`, `_lane_carrier_is_executed`, and every site within four lines after a `_blob_text` call) belong to the `t4gl15` family and are not counted.
- E-01 (pin): about 7 reader fixtures plus 2 baseline modules (`test_graduation_forward_links` 9 tests, `test_handoff_ready_gate` 16). E-02 (move): 19 site lines in 6 functions. Round 3: measured with `ipd_schema.count_named_units`, each item names at most 3 distinct units; 3 work Scope-Paths.

| Id | Evidence | Finding |
|---|---|---|
| F-08 | `history_block(` call sites: `attention` 6, `check_engine` 3; `last_history_at(` and `history_block(` together 10 sites in `attention` and `check_engine` | All history reads in this plan's module go through `artifact_meta.history`. |

READER LEDGER rows this part moves (copied from `ffceq0`):

| Reader | Prior behavior | Pinning test | After |
|---|---|---|---|
| `check_engine` identity, status, Set, Item-Dependencies and From-* readers | region-bounded `^- ` bullets with mixed whitespace rules | E-01 module and its baseline modules | cached fields; identical rule ids on this checkout |
| `check_engine.build_graduation_reverse_index`, `graduation_cluster` | declarations and reverse links read separately | `tests/test_graduation_forward_links.py`, `tests/test_from_backlog_cardinality.py` | `lineage` and `graduation_targets` rows, still distinct (4.4a `pw2ln3`) |

DECISIONS that govern this part's reader moves (copied verbatim from `ffceq0`, which keeps the full D-1..D-6 table):

- D-1 (status of the 24 multi-word plans; F-03, F-04). KEPT: the canonical normalized status that `aw attention`, `aw ipd board` and `ipd_lint` already report (`executed` for `EXECUTED ...` and `DONE ...`, `legacy/unknown` for any other unrecognized token). For PLAN records only, both `aw find` paths match `plans.normalize_status` of the FIRST token of the cached raw value (the `plans.read_status` rule). Every other type keeps today's exact single-token match on the raw value, because `plans.normalize_status` knows only the plan vocabulary and maps `open`, `implemented`, `active` and `planned` to `legacy/unknown`. Reason: one reader, one answer (4.3), and it is the answer three surfaces already give. (Full consumer-by-consumer text in `ffceq0`.)
- D-4 (status bullet outside the metadata region; F-06). KEPT: region-bounded reading. The 4 records are 3 reviews and 1 walkthrough, which have no lifecycle status, so no plan-status consumer changes.
- D-6 (records with no in-file `- Set:` bullet; added 2026-11-07, maintainer decision recorded on backlog `suth7l`). KEPT: the cache's filename-derived Set. `status_set`'s reader returns no Set for these records (242 on this repository on 2026-11-07), while the cache takes it from the filename, which spec `4sd62s` C1/C10 make the checked mirror of `set`. What a consumer loses: nothing. Pinned by `tests/test_artifact_meta_loader_parity.py::test_cache_agrees_with_status_set_reader_on_every_fixture_record`.

## Proposed changes (ordered, validatable)

1. Pin then move this subset of the `check_engine` working-tree readers (E-01, E-02).

## Deferred / out of scope (with reason)

- The one record skip list (`ebrc4t` E-03).
  - Carrier: i16on1
- The git-content readers of `check_engine` (`_blob_text`/`_status_meta` callers).
  - Carrier: t4gl15

## Scope check

- Over-scope: none. Only `check_engine.py` and the shared pin module change; the pin module gains one test class for this part, so the check_engine parts never edit the same test.
- Under-scope: none known. This part carries `ebrc4t` E-01 and E-02 unchanged.

## Required tests / validation

`tests/test_readers_check_engine.py` (core, `tmp_path` fixtures through `aw check <type> --agent`); this part adds only its own test class, named after Order 32. The baseline modules named in E-01 run before and after the move. Commands: the named modules, the bare core gate `python3 -m pytest`, `aw sanitize --agent`.

## Spec / documentation sync

N/A: no spec text changes; implements `4sd62s` section 7 step 5 for this subset of `check_engine`.

## Open questions

### OQ-01: Why does this part wait for Orders 29 to 31?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The round-3 rules give each new part the original plan's own dependencies; `ebrc4t` depended on the other three check_engine parts because the skip-list item had to follow every check_engine move. The edge also keeps the four check_engine parts from editing `check_engine.py` at the same time. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff --stat agent_workflows/check_engine.py` empty, then `python3 -m pytest -o addopts="" -v tests/test_readers_check_engine.py` all PASSED (one test per reader listed in E-01), and `wc -l` of the baseline modules' saved outcome list `.aw/state/ffceq0/E-06-before-32.txt`; also paste the sorted rule-id counts saved to `.aw/state/ffceq0/check-before-32.txt` (and `ls -l .aw/state/ffceq0/check-before.txt` showing the shared bar exists).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `diff .aw/state/ffceq0/E-06-before-32.txt .aw/state/ffceq0/E-07-after-32.txt` printing nothing (outcome lists of `tests/test_graduation_forward_links.py` and `tests/test_handoff_ready_gate.py`), and `aw check all --agent` sorted rule-id counts with `diff .aw/state/ffceq0/check-before-32.txt -` printing nothing (or each difference traced to a record changed between the runs).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every `- Item-Dependencies:` edge is executed. Every reader move is pin-first, and a test edited after a move must be one that the copied decisions name.

Honesty rule: run the named modules and `python3 -m pytest` (core gate) and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit dbq57g -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
