# IPD: Delete the selectors record text readers and rebind the runner re-exports

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` C5 allows exactly one metadata reader (`artifact_meta`). Part 15 of the round-3 split of `k6jd6l` (Order 43, research `nj8zdp` guidance): delete the `selectors` public text readers `read_front_matter_id`, `read_front_matter_status` and `read_front_matter_blocks_release` and the module patterns `selectors._ID_RE`, `_STATUS_RE` and `_SET_RE`. The `oc_runipd`/`agy_runipd` `_read_id` re-exports, pinned by `tests/test_runner_shared.py::CrossHostReadIdReExportTests` (loose `-  `/`-\t` spelling), are rebound first. Measured at `f83159217`: test callers `tests/test_front_matter_loose_whitespace.py` (3), `tests/test_history_order.py` (1), `tests/test_fixfirst_end_to_end.py` (1), `tests/test_blocks_release_reader_bounding.py` (5); `artifact_meta.append_legacy` calls `_sel.read_front_matter_id` (1).
- Scope: The `selectors` reader part of `k6jd6l` E-11 subset 1. Production callers in `runner_shared`, `releases`, `status_set`, `ipd_lint` and `attention` are moved by `ffceq0` and `t4gl15` (dependencies); any that Order 280's F-25 still lists live is handled here with `--scope-reason`. EXCLUDES `selectors.metadata_region` (Orders 293 and 296), the `plans` and `prompts` readers (Orders 295, 296).
- Scope-Paths: agent_workflows/selectors.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/artifact_meta.py, tests/test_front_matter_loose_whitespace.py, tests/test_history_order.py, tests/test_fixfirst_end_to_end.py, tests/test_blocks_release_reader_bounding.py, .aw/records/plans/pending/20261109-metastore-294-8ysz6b-delete-the-selectors-record-text-readers-and-rebind-the-runn.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:71ewpn, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:t4gl15
- Status: approved
- Readiness: go-pending-approval
- Review-Depth: standard
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 294
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8ysz6b
- Approval: 2026-11-16, recorded via aw ipd set: status set to approved

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-16 approved (aw set): status set to approved

- 2026-11-14 reviewed (antigravity/gemini-3.8-flash): /plan-review (antigravity/gemini-3.8-flash): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004.
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from k6jd6l (round 3, research nj8zdp guidance).

## Goal

`selectors` defines no `read_front_matter_*` reader and no `_ID_RE`, `_STATUS_RE` or `_SET_RE`, and `CrossHostReadIdReExportTests` passes unchanged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Carried from `k6jd6l` E-11: "The public `selectors.read_front_matter_*` callers that remain after `ffceq0` and `t4gl15` include the `oc_runipd`/`agy_runipd` `_read_id` re-exports ...; rebind the re-export to `artifact_meta.read_text`'s loose `id` value (`ffceq0` D-2, `t4gl15` D-4) so that test passes unchanged." Save the before-list of `tests/test_runner_shared.py`, `tests/test_front_matter_loose_whitespace.py`, `tests/test_history_order.py`, `tests/test_fixfirst_end_to_end.py` and `tests/test_blocks_release_reader_bounding.py` to `.aw/state/9o83cr/E-11b-before.txt` before E-01 (ensure `.aw/state/9o83cr/` exists via `mkdir -p .aw/state/9o83cr/`).

PIN RULE (carried from `9o83cr`): before an edit that deletes or retargets, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > <before-file>`); after it, run the same command into the matching after-file. A retargeted test keeps every input case, so the after-list may rename a test but not drop a case; the evidence pastes both lists and maps each removed name to its successor.

### Task group 1: rebind, retarget tests, delete

- [x] E-01 Before the first edit, ensure `.aw/state/9o83cr/` exists (`mkdir -p .aw/state/9o83cr/`) and save the baseline test PIN list to `.aw/state/9o83cr/E-11b-before.txt`. Rebind `oc_runipd._read_id` and `agy_runipd._read_id` to a function returning `artifact_meta.read_text(text).fields`' loose `id` value (`ffceq0` D-2, `t4gl15` D-4), and change `artifact_meta.append_legacy`'s `_sel.read_front_matter_id` call to the same local reader.
  - Depends on: none
  - Expected outcome: no module imports `read_front_matter_id` for the re-export; `CrossHostReadIdReExportTests` passes unchanged.
  - Execution state: performed

- [x] E-02 Retarget `tests/test_front_matter_loose_whitespace.py`, `tests/test_history_order.py` and `tests/test_fixfirst_end_to_end.py` from `selectors.read_front_matter_id`/`read_front_matter_status` to `artifact_meta.read_text`, keeping every case.
  - Depends on: E-01
  - Expected outcome: none of the three calls a `read_front_matter_*` reader.
  - Execution state: performed

- [x] E-03 Retarget `tests/test_blocks_release_reader_bounding.py` from `selectors.read_front_matter_blocks_release` to `artifact_meta.read_text(...).fields`, keeping every case.
  - Depends on: E-02
  - Expected outcome: the module calls no `read_front_matter_*` reader.
  - Execution state: performed

- [x] E-04 Delete `selectors.read_front_matter_id`, `read_front_matter_status` and `read_front_matter_blocks_release` with their private patterns.
  - Depends on: E-03
  - Expected outcome: `rg -n "read_front_matter_(id|status|blocks_release)" agent_workflows tools tests` prints only comment lines.
  - Execution state: performed

- [x] E-05 Delete `selectors._ID_RE`, `_STATUS_RE` and `_SET_RE` (their readers `selectors._read_id`, `_read_status`, `_read_setid` read through `artifact_meta` since Order 142, `cdglt1`); save the after-list; commit through `aw commit 8ysz6b -- <paths>`.
  - Depends on: E-04
  - Expected outcome: the three patterns are gone; no pinned case is dropped.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `selectors.read_front_matter_id` and `read_front_matter_status` are the loose-spelling readers (`^-\s*Id:`); `CrossHostReadIdReExportTests` pins that behavior.
- The `artifact_meta` interface (names from `tve77h`, `ffceq0`, `xexn45`): `read(id6) -> State`, `history(id6)`, `read_at(id6, rev)`, `read_text(text, *, record_type=None) -> State`, `append(id6, events, *, expect_seq)` with `dry_run`, the phase-B legacy writer (`append_legacy`, `render_legacy`), and the legacy loader (`load_legacy_artifact`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `f83159217` with `rg -n "read_front_matter_(id|status|blocks_release)" agent_workflows tests`: see the Concern; production callers in `runner_shared` (11), `releases` (3), `status_set` (3), `ipd_lint` (1), `attention` (1) are in the Scope-Paths of `ffceq0` or `t4gl15` and expected moved.

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    E01["E-01: Save Baseline PIN List & Rebind<br/>oc_runipd / agy_runipd _read_id"] --> E02["E-02: Retarget<br/>test_front_matter_loose_whitespace,<br/>test_history_order & test_fixfirst_end_to_end"]
    E02 --> E03["E-03: Retarget<br/>test_blocks_release_reader_bounding"]
    E03 --> E04["E-04: Delete selectors<br/>read_front_matter_* Readers"]
    E04 --> E05["E-05: Delete selectors<br/>_ID_RE, _STATUS_RE, _SET_RE & Commit"]
```

1. Rebind the re-exports (E-01).
2. Retarget three tests (E-02).
3. Retarget the blocks-release test (E-03).
4. Delete the readers (E-04).
5. Delete the patterns and commit (E-05).

## Deferred / out of scope (with reason)

- `selectors.metadata_region` and the `plans` readers.
  - Carrier: hrbbhy
- The `prompts` readers.
  - Carrier: iup4lp

## Scope check

- Over-scope: none.
- Under-scope: If Order 280's F-25 lists a live production caller of a deleted reader, retarget it here and justify the path at finalize (`--scope-reason`). Size: 5 E-items, 8 work Scope-Paths.

## Required tests / validation

The five PIN modules above.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.3 and section 7 step 7. CONTRIBUTES to AC-1 (owned by `9o83cr`).

## Open questions

### OQ-01: What if `selectors._read_id` still uses `_ID_RE`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Then Order 142 did not finish; stop and report rather than deleting the pattern. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `rg -n "read_front_matter_id" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py agent_workflows/artifact_meta.py` printing nothing and `python3 -m pytest -o addopts="" -v tests/test_runner_shared.py -k CrossHostReadIdReExport` with every test PASSED and `git diff --stat tests/test_runner_shared.py` empty.
  - Observed evidence: (attempt 1 commit `b7644bfc1` on lane `aw/lane/8ysz6b`, brought forward unchanged in attempt 2 as commit `315bb34b0`; every command below re-run in attempt 2 with identical output) Both hosts bind `_read_id` to the new `artifact_meta.read_loose_id(text)` (= `read_text(metadata_region(text)).loose_id`, byte-identical behavior to the deleted reader; measured over all 5129 `.aw/records/**/*.md` with 0 divergences before deletion), and `artifact_meta.write_legacy`'s sidecar fallback calls the same function.
    ```
    $ rg -n "read_front_matter_id" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py agent_workflows/artifact_meta.py; echo "rg exit=$?"
    rg exit=1
    $ python3 -m pytest -o addopts="" -v -n 0 tests/test_runner_shared.py -k CrossHostReadIdReExport
    tests/test_runner_shared.py::CrossHostReadIdReExportTests::test_cross_host_read_id_permissive_reader_reexport PASSED [100%]
    ====================== 1 passed, 142 deselected in 0.28s =======================
    $ git diff --stat tests/test_runner_shared.py
    (empty)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `rg -n "read_front_matter_" tests/test_front_matter_loose_whitespace.py tests/test_history_order.py tests/test_fixfirst_end_to_end.py` printing nothing and each module's before/after per-test lines.
  - Observed evidence:
    ```
    $ rg -n "read_front_matter_" tests/test_front_matter_loose_whitespace.py tests/test_history_order.py tests/test_fixfirst_end_to_end.py; echo "rg exit=$?"
    rg exit=1
    ```
    Per-module counts in `.aw/state/9o83cr/E-11b-{before,after}.txt` (all PASSED, identical names): `test_front_matter_loose_whitespace` before=4 after=4; `test_history_order` before=7 after=7; `test_fixfirst_end_to_end` before=35 after=35. The diff (V-05) shows no line for any of these three modules, so every case survives under its original name.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `rg -n "read_front_matter_" tests/test_blocks_release_reader_bounding.py` printing nothing and its before/after per-test lines.
  - Observed evidence:
    ```
    $ rg -n "read_front_matter_" tests/test_blocks_release_reader_bounding.py; echo "rg exit=$?"
    rg exit=1
    ```
    `test_blocks_release_reader_bounding` before=9 after=9, all PASSED. One rename, same four input cases (`text_fm`, `text_body`, `text_yaml`, `text_trailing`): `test_read_front_matter_blocks_release_cases` -> `test_loose_blocks_release_cases` (now through `artifact_meta.read_loose_blocks_release`).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste that `rg` output (empty, or each line a quoted comment).
  - Observed evidence:
    ```
    $ rg -n "read_front_matter_(id|status|blocks_release)" agent_workflows tools tests
    agent_workflows/check_engine.py:2087:# documented at `selectors.read_front_matter_id` happened before.
    agent_workflows/selectors.py:473:# The PUBLIC loose-whitespace readers that used to live here (`read_front_matter_id`, `_status`,
    agent_workflows/runner_shared.py:55899:        # the former `selectors.read_front_matter_status` (now `artifact_meta.read_loose_status`) is the shared PERMISSIVE reader, and
    tests/test_runner_shared.py:209:    """s4jctz / h0zk2g E-03: both hosts expose `_read_id` bound to permissive `read_front_matter_id`."""
    tests/test_ipdrunner_runagy_shim.py:329:        # status reading is owned by selectors.read_front_matter_status and tested in tests/.
    ```
    Every line is a comment or docstring. `tests/test_runner_shared.py:209` is a docstring left as is because V-01 requires that file unchanged. Live callers outside the fence that would have broken on deletion were retargeted with `--scope-reason` (`releases` 3, `runner_shared` 2, `review_basis` 3, `tests/test_readers_selectors_find.py` 9, `tests/test_artifact_meta_legacy_writer.py` 1); their pin list (190 cases, 9 modules) was identical before and after in attempt 1 (`.aw/state/8ysz6b/extra-{before,after}.txt`, `diff` exit 0); in attempt 2 those modules all pass inside the full `aw suite` run cited in V-05.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `rg -n "^_(ID|STATUS|SET)_RE =" agent_workflows/selectors.py` printing nothing, `diff .aw/state/9o83cr/E-11b-before.txt .aw/state/9o83cr/E-11b-after.txt` with no FAILED or ERROR line, and `git show --stat` of the `aw commit 8ysz6b` commit.
  - Observed evidence: The three patterns were already absent at the starting HEAD `9cfa6aa23` (removed by `cdglt1`, commit `36012ee0d`; `selectors._read_id`/`_read_status`/`_read_setid` read through `artifact_meta`, so OQ-01's stop condition does not apply). This run removed the stale comment references to them.
    ```
    $ rg -n "^_(ID|STATUS|SET)_RE =" agent_workflows/selectors.py; echo "rg exit=$?"
    rg exit=1
    $ diff .aw/state/9o83cr/E-11b-before.txt .aw/state/9o83cr/E-11b-after.txt
    3a4
    > PASSED tests/test_blocks_release_reader_bounding.py::TestBlocksReleaseReaderBounding::test_loose_blocks_release_cases
    5d5
    < PASSED tests/test_blocks_release_reader_bounding.py::TestBlocksReleaseReaderBounding::test_read_front_matter_blocks_release_cases
    $ grep -cE "^(FAILED|ERROR)" .aw/state/9o83cr/E-11b-after.txt
    0
    $ git show --stat 315bb34b0
    commit 315bb34b0e4586d7c8fb26ab6328d51b48f340ca
        metastore 294 (8ysz6b): delete selectors read_front_matter_* readers; rebind host _read_id to artifact_meta.read_loose_id (brought forward from lane aw/lane/8ysz6b b7644bfc1)
     agent_workflows/agy_runipd.py                |  18 ++---
     agent_workflows/artifact_meta.py             |  31 +++++++-
     agent_workflows/oc_runipd.py                 |  12 +--
     agent_workflows/releases.py                  |  13 +++-
     agent_workflows/review_basis.py              |  10 +--
     agent_workflows/runner_shared.py             |  12 +--
     agent_workflows/selectors.py                 | 105 ++++-----------------------
     tests/test_artifact_meta_legacy_writer.py    |   2 +-
     tests/test_blocks_release_reader_bounding.py |  20 +++--
     tests/test_fixfirst_end_to_end.py            |   3 +-
     tests/test_front_matter_loose_whitespace.py  |  21 ++++--
     tests/test_history_order.py                  |   4 +-
     tests/test_readers_selectors_find.py         |  20 ++---
     13 files changed, 118 insertions(+), 153 deletions(-)
    ```
    Both lists hold 198 lines; the only difference is the V-03 rename. Attempt 2 regenerated both lists (the before-list from a `git archive` of starting HEAD `ee436f6e3`, the after-list from the working tree; 198 lines each, 0 FAILED/ERROR) with the same diff shown. Full core suite (`aw suite`, attempt 2, after commit `315bb34b0`): `2889 passed, 1 skipped, 11 warnings in 117.21s (0:01:57)`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Pin-first where an item deletes or retargets. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Safety stop: if prerequisite metastore symbols from `59aiyh`, `71ewpn`, `ffceq0`, or `t4gl15` are absent upon starting, stop and report rather than creating conflicting implementations. Honesty rule: paste the ACTUAL output; never claim a result you did not run. Commits: only through `aw commit 8ysz6b -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through finalize; when `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 8ysz6b` itself; never a hand `git mv` to `executed/`.
